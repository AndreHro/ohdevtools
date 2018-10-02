""" Interface to AWS S3 storage"""
import os
import sys

try:
    import boto3
except:
    print('\nAWS fetch requires boto3 module')
    print("Please install this using 'pip install boto3'\n")
else:
    # create AWS credentials file (if not already present)
    home = None
    if 'HOMEPATH' in os.environ and 'HOMEDRIVE' in os.environ:
        home = os.path.join(os.environ['HOMEDRIVE'], os.environ['HOMEPATH'])
    elif 'HOME' in os.environ:
        home = os.environ['HOME']
    if home:
        awsCreds = os.path.join(home, '.aws', 'credentials')
        if not os.path.exists(awsCreds):
            if sys.version_info[0] == 2:
                from urllib2 import urlopen
            else:
                from urllib.request import urlopen
            try:
                os.mkdir(os.path.join(home, '.aws'))
            except:
                pass
            try:
                credsFile = urlopen('http://core.linn.co.uk/aws-credentials' )
                creds = credsFile.read()
                with open(awsCreds, 'wt') as f:
                    f.write(creds)
            except:
                pass


def copy(aSrc, aDst):
    """Copy objects to/from AWS. AWS uri in form s3://<bucket>/<key>"""
    resource = boto3.resource('s3')
    if 's3://' in aSrc:
        bucket = resource.Bucket(aSrc.split('/')[2])
        obj = bucket.Object('/'.join(aSrc.split('/')[3:]))
        with open(aDst, 'wb') as data:
            obj.download_fileobj(data)
    elif 's3://' in aDst:
        bucket = resource.Bucket(aDst.split('/')[2])
        with open( aSrc, 'rb' ) as data:
            ext = aSrc.split(".")[-1]
            if ext in  ["txt", "json", "xml"]:
                bucket.upload_fileobj(data, '/'.join(aDst.split('/')[3:]), ExtraArgs={'ContentType': 'text/plain'})
            else:
                bucket.upload_fileobj(data, '/'.join(aDst.split('/')[3:]))


def ls(aUri):
    """Return directory listing of contents of specified URI"""
    entries = []
    fields = aUri.split('/')
    bucket = fields[2]
    prefix = '/'.join(fields[3:])
    if prefix[-1] != '/':
        prefix += '/'
    client = boto3.client('s3')
    objects = client.list_objects_v2(Bucket=bucket, Delimiter='/', Prefix=prefix)
    if 'CommonPrefixes' in objects:
        for item in objects['CommonPrefixes']:
            entries.append(item['Prefix'])
    if 'Contents' in objects:
        for item in objects['Contents']:
            entries.append(item['Key'])
    return entries

def delete(aBucket, aKey):
    if aKey != None and len(aKey) > 0:
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(aBucket)
        # this allows a single file to be deleted or an entire directory, so be careful!
        bucket.objects.filter(Prefix=aKey).delete()
