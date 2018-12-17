#!/usr/bin/env python
import json
import os
import subprocess
import sys
import time
import zipfile
import argparse
import random
import socket
from collections import OrderedDict
import Common
import time
import shutil

kDateTime         = time.strftime( '%d %b %Y %H:%M:%S', time.localtime() )
kPcasLookupTable  = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'product_info.json')
kPcasTableName    = 'PcasInfo'
# keys from PcasInfo
kDescKey = "description"
kVerKey = "lateststable"
kTargetKey = "legacytarget"
kNameKey = "name"
kPlatKey = "platform"
kRenewNameKey = "renewname"
kRenewUrlKey = "renewurl"
kUrlKey = "url"
kVolkano1Key = "volkano1"
kVolkano1SourcesKey = "v1sources"
kSourceMapRcaFirst = "rcafirst"
kVarsKey = "variants"
kPcasInfoKeys = [kDescKey, kVerKey, kTargetKey, kNameKey, kPlatKey, kRenewNameKey, kRenewUrlKey, kUrlKey, kVolkano1Key, kVolkano1SourcesKey, kSourceMapRcaFirst]

kTargetTableName  = 'Target2Pcas'
kLegalObj         = 'legal'
kReleaseNotesObj  = 'releasenotes'
kReleaseInfoV1Obj = 'releaseinfoV1'
kStableInfoObj    = 'stablereleases'
kLatestInfoObj    = 'latestreleases'

def GetPcas( aProductName ):
    pcas = ""
    jsonObjs = Common.GetJsonObjects( kPcasLookupTable )
    pcasList = GetPcasList( aProductName )
    for entry in pcasList:
        pcas = entry
        break # not sure if/how to handle multiple entries
    return pcas

def GetPcasList( aProductName ):
    pcas = ""
    jsonObjs = Common.GetJsonObjects( kPcasLookupTable )
    pcasList = []
    try:
         pcasList = jsonObjs[kTargetTableName][aProductName]
    except KeyError:
         pcasList = jsonObjs[kTargetTableName][aProductName.replace( "Mk1", "" )]
    return pcasList

def GetOutputNames( aTarget ):
    names = []
    try:
        jsonObjs = Common.GetJsonObjects( kPcasLookupTable )
        for pcas in jsonObjs[kTargetTableName][aTarget]:
            names.append( 'Fw' + pcas )
    except:
        names = [aTarget]
    return names

def GetNewVariant( aOldVariant ):
    old = aOldVariant
    prefix = ""
    if old.startswith( Common.kProductSuppressedString ):
        old = old.split('_')[1]
        prefix = Common.kProductSuppressedString + '_'

    if not old.startswith('Fw'):
        releaseVariantNew = "%sFw%s" % ( prefix, GetPcas( old ) )
    else:
        releaseVariantNew = aOldVariant
    return releaseVariantNew

def GetTarget( aPcas ):
    name = ""
    pcasStr = str(aPcas)
    pcasNum = pcasStr.lower().replace("pcas", "").replace("fw", "")
    jsonObjs = Common.GetJsonObjects( kPcasLookupTable )
    pcasTable = jsonObjs[kTargetTableName]
    for target, pcasList in pcasTable.iteritems():
        for entry in pcasList:
            if pcasNum == entry:
                name = target
                break # not sure if/how to handle multiple entries
    return name

def GetLegal():
    jsonObjs = Common.GetJsonObjects( kPcasLookupTable )
    return jsonObjs[kLegalObj]

def GetReleaseNotes(aReleaseType='stable'):
    relType = None
    if 'dev' in aReleaseType.lower():
        relType = 'dev'
    elif 'beta' in aReleaseType.lower():
        relType = 'beta'
    else:
        relType = 'stable'
    jsonObjs = Common.GetJsonObjects( kPcasLookupTable )
    return jsonObjs[kReleaseNotesObj][relType]

def GetReleaseNotesBeta():
    return GetReleaseNotes('beta')

def GetReleaseNotesDev():
    return GetReleaseNotes('dev')

def GetV1DownloadUrlBase():
    jsonObjs = Common.GetJsonObjects( kPcasLookupTable )
    return jsonObjs[kReleaseInfoV1Obj]["downloadurlbase"]

def GetV1DownloadBetaDir():
    jsonObjs = Common.GetJsonObjects( kPcasLookupTable )
    return jsonObjs[kReleaseInfoV1Obj]["downloadbetadir"]

def GetV1DownloadDevelopmentDir():
    jsonObjs = Common.GetJsonObjects( kPcasLookupTable )
    return jsonObjs[kReleaseInfoV1Obj]["downloaddevdir"]

def GetV1DownloadStableDir():
    jsonObjs = Common.GetJsonObjects( kPcasLookupTable )
    return jsonObjs[kReleaseInfoV1Obj]["downloadstabledir"]

def GetV1DownloadNightlyDir():
    jsonObjs = Common.GetJsonObjects( kPcasLookupTable )
    return jsonObjs[kReleaseInfoV1Obj]["downloadnightlydir"]

def GetV1MinKonfigVersion():
    jsonObjs = Common.GetJsonObjects( kPcasLookupTable )
    return jsonObjs[kReleaseInfoV1Obj]["minkonfigversion"]

def GetV1ExaktLinkVersion():
    jsonObjs = Common.GetJsonObjects( kPcasLookupTable )
    return jsonObjs[kReleaseInfoV1Obj]["exaktlink"]

def GetLatestReleaseInfo(aPlatform, aReleaseType):
    jsonObjs = Common.GetJsonObjects( kPcasLookupTable )
    if jsonObjs[kLatestInfoObj][aPlatform] != None:
        return jsonObjs[kLatestInfoObj][aPlatform][aReleaseType]
    else:
        return None

def GetStableReleaseVersions(aPlatform):
    jsonObjs = Common.GetJsonObjects( kPcasLookupTable )
    return list(jsonObjs[kStableInfoObj][aPlatform].keys())

def GetStableReleaseInfo(aVersion):
    jsonObjs = Common.GetJsonObjects( kPcasLookupTable )
    if jsonObjs[kStableInfoObj]['core1'].has_key(aVersion):
        return jsonObjs[kStableInfoObj]['core1'][aVersion]
    elif jsonObjs[kStableInfoObj]['core4'].has_key(aVersion):
        return jsonObjs[kStableInfoObj]['core4'][aVersion]

    print "WARNING: could night find stable release info for: " + aVersion
    raise ValueError("MissingInfo")

def GetPlatform( aPcas ):
    try:
        p,d = GetPlatformAndDescription( aPcas )
        return p
    except:
        return None

def GetDescription( aPcas ):
    try:
        p,d = GetPlatformAndDescription( aPcas )
        return d
    except:
        return None

def GetPlatformAndDescription( aPcas ):
    pcasStr = str(aPcas)
    pcasNum = pcasStr.lower().replace("pcas", "").replace("fw", "")
    jsonObjs = Common.GetJsonObjects( kPcasLookupTable )
    if jsonObjs[kPcasTableName].has_key( pcasNum ):
        pcasInfo = jsonObjs[kPcasTableName]
        return pcasInfo[pcasNum]["platform"], pcasInfo[pcasNum]["description"]
    else:
        for pcasinfo in jsonObjs[kPcasTableName].itervalues():
            if pcasinfo.has_key( "variants" ):
                for pcas, variantInfo in pcasinfo["variants"].iteritems():
                    if pcas == pcasNum:
                        return pcasinfo["platform"], variantInfo
    #print "WARNING: could night find platform/description for: " + pcasStr
    raise ValueError("MissingInfo")

def GetLatestStableRelease( aPcas ):
    pcasStr = str(aPcas)
    pcasNum = pcasStr.lower().replace("pcas", "").replace("fw", "")
    jsonObjs = Common.GetJsonObjects( kPcasLookupTable )
    if jsonObjs[kPcasTableName].has_key( pcasNum ):
        pcasInfo = jsonObjs[kPcasTableName]
        return pcasInfo[pcasNum]["lateststable"]
    else:
        for pcasinfo in jsonObjs[kPcasTableName].itervalues():
            if pcasinfo.has_key( "variants" ):
                for pcas, variantInfo in pcasinfo["variants"].iteritems():
                    if pcas == pcasNum:
                        return pcasinfo["lateststable"]
    print "WARNING: could night find latest stable release for: " + pcasStr
    raise ValueError("MissingInfo")

def GetTargets( aPlatform, aType='pcas', aIncRenew=False ):
    # aPlatform = 'core1' or 'core4'
    # aType = 'target', 'pcas', 'fw'
    devList = []
    prefix = "Fw" if aType == 'fw' else ""
    jsonObjs = Common.GetJsonObjects( kPcasLookupTable )
    for pcas, pcasinfo in jsonObjs[kPcasTableName].iteritems():
        if pcasinfo["platform"] == aPlatform:
            if aType == 'target':
                devList.append( pcasinfo["legacytarget"] )
            else:
                devList.append( prefix + pcas )
                if pcasinfo.has_key( "variants" ):
                    varList = pcasinfo["variants"]
                    for var, varinfo in varList.iteritems():
                        if var != "826": # don't include renew devices
                            devList.append( prefix + var )
                            if "826" in varList and aIncRenew:
                                devList.append( prefix + var + "_826" )
                        elif aIncRenew:
                            devList.append( prefix + pcas + "_826" )
    #print "%s targets (%d): %s" % ( aPlatform, len(devList), devList )
    return devList

def DeviceTypeCount( aPlatform, aDevList ):
    count = 0
    if len(aDevList) > 0:
        # determine list type by first entry
        listType = GetTargetType( aDevList[0] )
        targets = GetTargets( aPlatform, listType )
        for dev in aDevList:
            if str(dev) in targets:
                count += 1
    return count

def GetTargetType( aTarget ):
    listType = 'target'
    if isinstance( aTarget, int ) or aTarget.isdigit(): 
        listType = 'pcas'
    elif 'fw' in aTarget.lower():
        listType = 'fw'
    return listType

def GetFirmwareVariant( aPcas ):
    pcasStr = str(aPcas)
    pcasNum = pcasStr.lower().replace("pcas", "").replace("fw", "")
    platform =  GetPlatform( pcasNum )
    if platform == "core1":
        fwVar = "Fw%s" % pcasNum
    elif platform == "core4":
        fwVar = "%s" % pcasNum
    else:
        raise ValueError("PcasInvalid")
    return fwVar

def GetAllTargets():
    # returns a full integer list of pcas targets available, sorted by pcas number
    core1 = GetTargets( "core1" )
    core4 = GetTargets( "core4" )
    allDevs = core1 + core4
    return sorted(allDevs, key=int)

def GetCore1Targets():
    # returns a full integer list of pcas targets available, sorted by pcas number
    core1 = GetTargets( "core1" )
    return sorted(core1, key=int)

def GetCore1TargetsIncRenew():
    # returns a full integer list of pcas targets available, sorted by pcas number
    core1 = GetTargets( "core1", "pcas", True )
    core1.sort(key=lambda e: int(e.split('_')[0]))
    return core1

def HasRenew( aPcas ):
    pcasStr = str(aPcas)
    pcasNum = pcasStr.lower().replace("pcas", "").replace("fw", "")
    core1 = GetTargets( "core1", "pcas", True )
    return (pcasNum + "_826") in core1

def GetRenewName( aPcas ):
    pcasStr = str(aPcas)
    pcasNum = pcasStr.lower().replace("pcas", "").replace("fw", "")
    jsonObjs = Common.GetJsonObjects( kPcasLookupTable )
    if jsonObjs[kPcasTableName].has_key( pcasNum ):
        pcasInfo = jsonObjs[kPcasTableName]
        return pcasInfo[pcasNum]["renewname"]
    else:
        for pcasinfo in jsonObjs[kPcasTableName].itervalues():
            if pcasinfo.has_key( "variants" ):
                for pcas, variantInfo in pcasinfo["variants"].iteritems():
                    if pcas == pcasNum:
                        return pcasinfo["renewname"]

def GetCore4Targets():
    # returns a full integer list of pcas targets available, sorted by pcas number
    core4 = GetTargets( "core4" )
    return sorted(core4, key=int)


def Core1Count( aDevList ):
    return DeviceTypeCount( 'core1', aDevList )

def Core4Count( aDevList ):
    return DeviceTypeCount( 'core4', aDevList )

def IncludesAllCore1Devices( aDevList ):
    devCount = Core1Count( aDevList )
    core1 = GetCore1Targets()
    return devCount == len(core1)

def IncludesAllCore4Devices( aDevList ):
    devCount = Core4Count( aDevList )
    core4 = GetCore4Targets()
    return devCount == len(core4)

def GetLatestVersionsCore1( ):
    return GetLatestVersions( 'core1' )

def GetLatestVersionsCore4( ):
    return GetLatestVersions( 'core4' )

def GetLatestVersions( aPlatform ):
    beta = None
    stable = None

    rlsInfo = GetLatestReleaseInfo(aPlatform, 'stable')
    if rlsInfo != None:
        stable = rlsInfo["version"]
    else:
        Common.Info( '[FAIL]    No valid stable release version found for %s' % ( aPlatform ) )
        sys.exit(2)
    
    rlsInfo = GetLatestReleaseInfo(aPlatform, 'beta')
    if rlsInfo != None:
        # if beta is identical to stable, don't report it
        beta = rlsInfo["version"] if rlsInfo["version"] != stable else None
    else:
        Common.Info( '[WARNING]    No valid beta release version found for %s' % ( aPlatform ) )

    rlsList = GetStableReleaseVersions(aPlatform)

    print( "Latest device versions for %s: %s (beta), %s (stable)" % ( aPlatform, beta, stable ) )
    print( "Stable release version list for %s: %s" % ( aPlatform, rlsList ) )
    return { 'beta': beta, 'stable': stable, 'releaseList': rlsList }

def SuppressioStringForJenkins():
    kJenkinsSuppressionParam = "____EnableSuppression____"
    core1list = []
    core4list = []
    alllist =   []
    
    for pcas in GetCore1Targets():
        core1list.append( "\"%s (Pcas %s: %s):selected\"" % (GetTarget(pcas), str(pcas), GetDescription(pcas).replace(",","-")) )

    for pcas in GetCore4Targets():
        core4list.append( "\"%s (Pcas %s: %s):selected\"" % (GetTarget(pcas), str(pcas), GetDescription(pcas).replace(",","-")) )

    for pcas in GetAllTargets():
        alllist.append( "\"%s (Pcas %s: %s):selected\"" % (GetTarget(pcas), str(pcas), GetDescription(pcas).replace(",","-")) )

    # lists are sorted by pcas, this will re-sort by target name instead
    core1  = ",".join(sorted(core1list, key=str))
    core4  = ",".join(sorted(core4list, key=str))
    alldev = ",".join(sorted(alllist, key=str))

    groovyScript = """
        if ({0}.equals(\"None\")) {{
            return []
        }} else if ({0}.equals(\"Core1\")) {{
            return [
                {1}
            ]
        }} else if ({0}.equals(\"Core4\")) {{
            return [
                {2}
            ]
        }} else if ({0}.equals(\"All\")) {{
            return [
                {3}
            ]
        }} else {{
            return [\"Unknown Product Group: \" + {0}]
        }}
    """.format( kJenkinsSuppressionParam, core1, core4, alldev  )

    return groovyScript

def CreateV1Feed(aFile, aVersion, aDownloadSubDir, aSuppressionList, aMinKonfigVersion=None, aExaktLink=None):
    def GetFeedSectionProducts():
        pcasListJson = []
        for item in GetCore1TargetsIncRenew():
            pcas = str(item)
            entry = {}
            if "_" in pcas:
                # handle renew variants differently
                pcasGroup = pcas.split("_")
                entry["pcas"] = pcasGroup
                pcas = pcasGroup[0]
            else: 
                entry["pcas"] = [pcas]
            entry["variantid"] = GetTarget(pcas)
            pcasListJson.append( entry )
        return pcasListJson

    def GetFeedSectionProductsV2():
        pcasListJson = []
        jsonObjs = Common.GetJsonObjects( kPcasLookupTable )
        for pcas, pcasinfo in jsonObjs[kPcasTableName].iteritems():
            if pcasinfo["platform"] == "core1":
                entry = {}
                entry["variantid"] = pcasinfo["legacytarget"]
                pcasList = []
                pcasList.append(pcas)
                if pcasinfo.has_key( "variants" ):
                    varList = pcasinfo["variants"]
                    for var, varinfo in varList.iteritems():
                        if var != "826": # don't include renew devices
                            pcasList.append( var )
                entry["pcas"] = pcasList
                pcasListJson.append( entry )
        pcasListJson.sort(key=lambda e: int(e["pcas"][0]))
        return pcasListJson

    def GetFeedSectionLatestStable():
        rlsInfo = GetLatestReleaseInfo('core1', 'stable')
        section = GetFeedSectionReleases(rlsInfo['date'], rlsInfo['version'], GetV1DownloadStableDir(), rlsInfo['suppress'], rlsInfo['minkonfigversion'], rlsInfo['exaktlink'])
        return section

    def GetFeedSectionReleases(aDateTime, aVersion, aDownloadSubDir, aSuppressionList, aMinKonfigVersion=None, aExaktLink=None):
        quality = "release"
        uriHasVersionDir = False
        if 'beta' in aDownloadSubDir.lower() or 'dev' in aDownloadSubDir.lower():
            quality = "beta"
            uriHasVersionDir = True
        elif 'nightly' in aDownloadSubDir.lower():
            quality = "nightly"
            uriHasVersionDir = True

        relListJson = []
        for item in GetTargets( "core1" ):
            pcas = str(item)
            var = "Fw%s" % pcas
            legalInfo = GetLegal()
            minkonver = GetV1MinKonfigVersion() if aMinKonfigVersion is None else aMinKonfigVersion
            exaktlnk = GetV1ExaktLinkVersion() if aExaktLink is None else aExaktLink
            date = aDateTime
            version = aVersion

            if aSuppressionList != None and var in aSuppressionList:
                if quality == "release":
                    version = GetLatestStableRelease(item)
                    rlsInfo = GetStableReleaseInfo(version)
                    date = rlsInfo['date']
                    minkonver = rlsInfo['minkonfigversion']
                    exaktlnk = rlsInfo['exaktlink']
                else:
                    continue # skip suppressed entries for non-stable feed info

            rel = {
                "date": "%s" % date,
                "exaktlink": "%s" % exaktlnk,
                "licenseurl": "%s" % legalInfo["licenseurl"],
                "minkonfigversion": "%s" % minkonver,
                "privacyuri": "%s" % legalInfo["privacyuri"],
                "privacyurl": "%s" % legalInfo["privacyurl"],
                "privacyversion": legalInfo["privacyversion"],
                "quality": "%s" % quality,
                "releasenotesuri": "%s" % GetReleaseNotes(aDownloadSubDir),
                "uri": "{0}/{1}{2}/{3}_{4}.zip".format( GetV1DownloadUrlBase(), aDownloadSubDir, "/" + version if uriHasVersionDir else "", var, version ),
                "variantids": [
                    "%s" % var
                ],
                "version": "%s" % version
            }
            relListJson.append( rel )
        relListJson.sort(key=lambda e: int(e["variantids"][0].replace("Fw", "")))
        return relListJson

    feed = {}

    # pcas lookup table and release info
    feed["products"] = GetFeedSectionProducts()
    feed["productsV2"] = GetFeedSectionProductsV2()


    relListJson = []
    if 'dev' in aDownloadSubDir.lower() or 'beta' in aDownloadSubDir.lower():
        relListJson += GetFeedSectionLatestStable() # beta and dev carry latest stable as well for reverting back
    relListJson += GetFeedSectionReleases(kDateTime, aVersion, aDownloadSubDir, aSuppressionList) # info for this release
    feed["releases"] = relListJson

    Common.CreateJsonFile( feed, aFile )

def CreateV1DevelopmentFeed(aFile, aVersion, aSuppressionList):
    CreateV1Feed(aFile, aVersion, GetV1DownloadDevelopmentDir(), aSuppressionList)
    UpdateLatestReleaseInfoCore1('dev', aVersion, aSuppressionList)

def CreateV1BetaFeed(aFile, aVersion, aSuppressionList):
    CreateV1Feed(aFile, aVersion, GetV1DownloadBetaDir(), aSuppressionList)
    UpdateLatestReleaseInfoCore1('beta', aVersion, aSuppressionList)

def CreateV1NightlyFeed(aFile, aVersion):
    CreateV1Feed(aFile, aVersion, GetV1DownloadNightlyDir(), None)
    UpdateLatestReleaseInfoCore1('nightly', aVersion, None)

def CreateV1ReleaseFeed(aFile, aVersion, aIsPromotionFromDev):
    rlsInfo = None
    if aIsPromotionFromDev:
        rlsInfo = GetLatestReleaseInfo('core1', 'dev')
    else:
        rlsInfo = GetLatestReleaseInfo('core1', 'beta')
    if rlsInfo == None or rlsInfo['version'] == aVersion:
        return False
    
    CreateV1Feed(aFile, aVersion, GetV1DownloadStableDir(), rlsInfo['suppress'], rlsInfo['minkonfigversion'], rlsInfo['exaktlink'])
    UpdateLatestReleaseInfoCore1('stable', aVersion, rlsInfo['suppress'], rlsInfo['minkonfigversion'], rlsInfo['exaktlink'])
    return True

def UpdateLatestReleaseInfoCore1(aReleaseType, aVersion, aSuppressionList, aMinKonfigVersion=None, aExaktLink=None):
    UpdateLatestReleaseInfo('core1', aReleaseType, aVersion, aSuppressionList, aMinKonfigVersion, aExaktLink)

def UpdateLatestReleaseInfoCore4(aReleaseType, aVersion, aSuppressionList):
    UpdateLatestReleaseInfo('core4', aReleaseType, aVersion, aSuppressionList)

def UpdateLatestReleaseInfo(aPlatform, aReleaseType, aVersion, aSuppressionList, aMinKonfigVersion=None, aExaktLink=None):
    relType = 'stable'
    if 'dev' in aReleaseType.lower():
        relType = 'dev'
    elif 'beta' in aReleaseType.lower():
        relType = 'beta'
    elif 'night' in aReleaseType.lower():
        relType = 'nightly'

    jsonObjs = Common.GetJsonObjects( kPcasLookupTable )
    relObj = jsonObjs[kLatestInfoObj][aPlatform][relType]
    relObj['version'] = aVersion
    relObj['date'] = kDateTime
    relObj['suppress'] = aSuppressionList
    mk = GetV1MinKonfigVersion() if aMinKonfigVersion == None else aMinKonfigVersion
    relObj['minkonfigversion'] = mk
    el = GetV1ExaktLinkVersion() if aExaktLink == None else aExaktLink
    relObj['exaktlink'] = el

    if relType == 'stable':
        # set dev and beta to none on stable release
        jsonObjs[kLatestInfoObj][aPlatform]['dev'] = None
        jsonObjs[kLatestInfoObj][aPlatform]['beta'] = None
        # append this release to 'stablereleases'
        jsonObjs[kStableInfoObj][aPlatform][aVersion] = {'date': kDateTime, 'exaktlink': el, 'minkonfigversion': mk }
        # update 'lateststable' per pcas entry
        pcasOnlySuppressionList = [] if aSuppressionList == None else [s.replace("Fw", "") for s in aSuppressionList]
        for pcas, pcasinfo in jsonObjs[kPcasTableName].iteritems():
            if pcas not in pcasOnlySuppressionList:
                pcasinfo['lateststable'] = aVersion

    Common.CreateJsonFile( jsonObjs, kPcasLookupTable )

def CommitAndPushReleaseInfo( aVersion, aDryRun ):
    Common.CommitAndPushFiles( Common.kOhDevToolsRepo, [kPcasLookupTable], "Upated product info for release %s" % aVersion, aDryRun )
    # also publish to cloud location

def CreateCppPcasInfo( aFilePath=None ):
    jsonObjs = Common.GetJsonObjects( kPcasLookupTable )
    kKeyFirmwareVariant = "fwvar"
    cpp = """#pragma once

#include <OpenHome/OhNetTypes.h>
#include <OpenHome/Private/Standard.h>
#include <map>
#include <string>

EXCEPTION(PcasNotFound);

using namespace OpenHome;

namespace Linn
{
namespace Target
{
    typedef std::map<std::string, std::string> PcasData;
    typedef std::map<TUint, PcasData> PcasDict;\n
"""
    cpp += "    static const TChar* kKeyPcasDescription = \"%s\";\n" % kDescKey
    cpp += "    static const TChar* kKeyPcasLatestStable = \"%s\";\n" % kVerKey
    cpp += "    static const TChar* kKeyPcasLegacyTarget = \"%s\";\n" % kTargetKey
    cpp += "    static const TChar* kKeyPcasName = \"%s\";\n" % kNameKey
    cpp += "    static const TChar* kKeyPcasPlatform = \"%s\";\n" % kPlatKey
    cpp += "    static const TChar* kKeyPcasRenewName = \"%s\";\n" % kRenewNameKey
    cpp += "    static const TChar* kKeyPcasRenewUrl = \"%s\";\n" % kRenewUrlKey
    cpp += "    static const TChar* kKeyPcasUrl = \"%s\";\n" % kUrlKey
    cpp += "    static const TChar* kKeyPcasVolkano1 = \"%s\";\n" % kVolkano1Key
    cpp += "    static const TChar* kKeyPcasVolkano1Sources = \"%s\";\n" % kVolkano1SourcesKey
    cpp += "    static const TChar* kKeyPcasSourceMapRcaFirst = \"%s\";\n" % kSourceMapRcaFirst
    cpp += "    static const TChar* kKeyPcasFirmwareVariant = \"%s\";\n" % kKeyFirmwareVariant

    cpp += """
    static const PcasDict kPcasDict = {
"""
    for pcas, pcasinfo in jsonObjs[kPcasTableName].iteritems():
        pcasNum = int(pcas)
        varList = [pcasNum]
        descList = {pcasNum:pcasinfo[kDescKey]}
        if kVarsKey in pcasinfo:
            for varpcas, vardesc in pcasinfo[kVarsKey].iteritems():
                varNum = int(varpcas)
                if varNum != 826:
                    varList.append( varNum )
                    descList[varNum] = vardesc
        for var in varList:
            cpp += "        { %d, {" % var
            for key in kPcasInfoKeys:
                if key in pcasinfo:
                    val = pcasinfo[key] if key != kDescKey else descList[var]
                    cpp += "{\"%s\", \"%s\"}, " % (key, val)
            cpp += "{\"%s\", \"%s\"}" % (kKeyFirmwareVariant, GetFirmwareVariant(var))
            cpp += "} },\n"
    
    cpp += """
    };

    class PcasInfo
    {
    public:
        static const TChar* GetModelName(TUint aPcas, TBool aIsRenew)
        {
            if (aIsRenew) {
                return Get(kKeyPcasRenewName, aPcas);
            }
            else {
                return Get(kKeyPcasName, aPcas);
            }
        }

        static const TChar* GetUrl(TUint aPcas, TBool aIsRenew)
        {
            if (aIsRenew) {
                return Get(kKeyPcasRenewUrl, aPcas);
            }
            else {
                return Get(kKeyPcasUrl, aPcas);
            }
        }

        static const TChar* GetDescription(TUint aPcas)
        {
            return Get(kKeyPcasDescription, aPcas);
        }

        static const TChar* GetLegacyVariantStr(TUint aPcas)
        {
            return Get(kKeyPcasLegacyTarget, aPcas);
        }

        static const TChar* GetFirmwareVariant(TUint aPcas)
        {
            return Get(kKeyPcasFirmwareVariant, aPcas);
        }

        static const TChar* GetLatestStableSoftwareVersion(TUint aPcas)
        {
            return Get(kKeyPcasLatestStable, aPcas);
        }

        static TBool IsCore1(TUint aPcas)
        {
            return  strcmp(Get(kKeyPcasPlatform, aPcas), "core1") == 0;
        }

        static TBool IsCore4(TUint aPcas)
        {
            return  strcmp(Get(kKeyPcasPlatform, aPcas), "core4") == 0;
        }

        static TBool IsVolkano1(TUint aPcas)
        {
            return  strcmp(Get(kKeyPcasVolkano1, aPcas), "True") == 0;
        }

        static TUint Volkano1Sources(TUint aPcas)
        {
            if (IsVolkano1(aPcas)) {
                return GetNum(kKeyPcasVolkano1Sources, aPcas);
            }
            else {
                return 0;
            }
        }

        static TBool SourceMapRcaFirst(TUint aPcas)
        {
            TBool rcaFirst = false;
            try {
                rcaFirst = strcmp(Get(kKeyPcasSourceMapRcaFirst, aPcas), "True") == 0;
            }
            catch (const std::out_of_range&) { }
            return rcaFirst;
        }

        static const TChar* Get(const TChar* aKey, TUint aPcas)
        {
            std::string key = aKey;
            for (auto& x: kPcasDict) {
                if (x.first == aPcas) {
                    return x.second.at(key).c_str();
                }
            }
            THROW(PcasNotFound);
        }

        static const TUint GetNum(const TChar* aKey, TUint aPcas)
        {
            return TUint(atoi(Get(aKey, aPcas)));
        }
    };
} // namespace Target
} // namespace Linn
"""

    if aFilePath != None:
        Common.CreateTextFile( cpp, os.path.join( aFilePath, "PcasInfo.h" ) )
    else:    
        print cpp
    return cpp

def TargetToPcasFileConversion( aFilePath ):
    # filter out renew files
    for f in os.listdir( aFilePath ):
        fullPath = os.path.join( aFilePath, f )
        if os.path.isfile( fullPath ):
            fname = f.lower()
            if "renew" in fname:
                if "akurate" in fname:
                    if "dsm" in fname:
                        adsmRenewFile = fullPath
                    elif "ds" in fname:
                        adsRenewFile = fullPath
                elif "klimax" in fname:
                    if "dsm" in fname:
                        kdsmRenewFile = fullPath
                    elif "ds" in fname:
                        kdsRenewFile = fullPath

    for f in os.listdir( aFilePath ):
        fullPath = os.path.join( aFilePath, f )
        if os.path.isfile( fullPath ):
            [name, ext] = os.path.basename( fullPath ).split('.')
            pcasList = []
            try:
                pcasList = GetPcasList( name )
            except:
                if "renew" not in f.lower():
                    print "SKIP %s" %  fullPath
                continue

            for entry in pcasList:
                newFile = os.path.join( aFilePath, GetFirmwareVariant( entry ) + "." + ext )
                print "COPY %s to %s" % ( fullPath, newFile )
                shutil.copy2( fullPath, newFile )
                if HasRenew( entry ):
                    newFile = os.path.join( aFilePath, GetFirmwareVariant( entry ) + "Renew." + ext )
                    renewName = GetRenewName( entry ).lower()
                    srcFile = None
                    if "akurate" in renewName:
                        if "dsm" in renewName:
                            srcFile = adsmRenewFile
                        elif "ds" in renewName:
                            srcFile = adsRenewFile
                    elif "klimax" in renewName:
                        if "dsm" in renewName:
                            srcFile = kdsmRenewFile
                        elif "ds" in renewName:
                            srcFile = kdsRenewFile
                    print "COPY %s to %s" % ( srcFile, newFile )
                    shutil.copy2( srcFile, newFile )
            os.remove( fullPath )
    
    # delete unused renew files
    os.remove( adsmRenewFile )
    os.remove( adsRenewFile )
    os.remove( kdsmRenewFile )
    os.remove( kdsRenewFile )

#print SuppressioStringForJenkins()
#CreateV1DevelopmentFeed("tempV1devFeed.json", "4.66.250", ["Fw913", "Fw1015"])
#CreateV1ReleaseFeed("tempV1stableFeed.json", "4.66.255", False)
#CreateV1NightlyFeed("tempV1nightlyFeed.json", "4.0.699")
#CreateV1BetaFeed("tempV1betaFeed.json", "4.66.259", ["Fw913", "Fw1015"])
#CommitAndPushReleaseInfo( "1.2.3", True )
#CreateCppPcasInfo(".")
#TargetToPcasFileConversion("T:\\volkano2\\product\\Linn\\res\\icons")

#for f in os.listdir( "T:\\volkano2\\product\\Linn\\res\\icons" ):
#    print "  <entry    type=\"file\"   key=\"res/icons/{0}\">res/icons/{0}</entry>".format( f )