# -*- coding: utf-8 -*-
#
####################################################
#
# PRISM - Pipeline for animation and VFX projects
#
# www.prism-pipeline.com
#
# contact: contact@prism-pipeline.com
#
####################################################
#
#
# Copyright (C) 2016-2023 Richard Frangenberg
# Copyright (C) 2023 Prism Software GmbH
#
# Licensed under GNU LGPL-3.0-or-later
#
# This file is part of Prism.
#
# Prism is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Prism is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Prism.  If not, see <https://www.gnu.org/licenses/>.
###########################################################################
#
#                BMD Fusion Studio Integration for Prism2
#
#             https://github.com/Animatect/Prism2_PluginFusion
#
#                           Esteban Covo
#                     e.covo@magichammer.com.mx
#                     https://magichammer.com.mx
#
#                           Joshua Breckeen
#                              Alta Arts
#                          josh@alta-arts.com
#
###########################################################################


##  THIS IS A LIBRARY FOR HELPER FUNCTIONS FOR THE FUSION PRISM PLUGIN  ##
	

import os
import re
from typing import Union, Dict, Tuple, Any
import logging
from datetime import datetime
import uuid
import hashlib

from PrismUtils.Decorators import err_catcher as err_catcher

#   For Python Type Hints
FusionComp = Dict
Tool = Any
ToolOption = Any
Color = int
UUID = str
Toolname = str

logger = logging.getLogger(__name__)


#	Creates UUID

def createUUID(simple:bool=False, length:int=8) -> str:
    #	Creates simple Date/Time UID
    if simple:
        # Get the current date and time
        now = datetime.now()
        # Format as MMDDHHMM
        uid = now.strftime("%m%d%H%M")

        logger.debug(f"Created Simple UID: {uid}")
    
        return uid
    
    # Generate a 8 charactor UUID string
    else:
        uid = uuid.uuid4()
        # Create a SHA-256 hash of the UUID
        hashObject = hashlib.sha256(uid.bytes)
        # Convert the hash to a hex string and truncate it to the desired length
        shortUID = hashObject.hexdigest()[:length]

        logger.debug(f"Created UID: {shortUID}")

        return shortUID



#   Gets list of AOV's from Prism

def getAovNamesFromAovDict(aovDict:list) -> list:
    try:
        aovNames = []
        for aovItem in aovDict:
            aovNames.append(aovItem["aov"])
        return aovNames
    except:
        logger.warning(f"ERROR:  Unable to get AOV names from : {aovDict}")
        return None
		


#	Configures name to conform with Fusion Restrictions

def getFusLegalName(origName:str, check:bool=False) -> str:			#	TODO  Restructure and logging
    """
        Fusion has strict naming for nodes.  You can only use:
        - Alphanumeric characters:  a-z, A-Z, 0-9,
        - Do not use any spaces,
        - Do not use special charactors,
        - Node name cannot start with a number.
    """

    # Check if the name starts with a number
    if origName[0].isdigit():
        if check:
            return False, "Name cannot start with a number."
        
        return "Error: Name cannot start with a number."

    # Check if the name contains only allowed characters
    if not re.match(r'^[A-Za-z0-9_\- .]*$', origName):
        if check:
            return False, "Name contains invalid characters."
        
        return "Error: Name contains invalid characters."

    newName = origName.replace(' ', '_')
    newName = newName.replace('.', '_')
    newName = newName.replace('-', '_')

    if check:
        logger.debug(f"Name is Fusion-legal: {newName}")
        return True, ""
            
    return newName


#   Makes import data dict from various Prism data sources

def makeImportData(plugin, context:dict, aovDict:dict, sourceData:dict) -> dict:
    #   Get mediaType from Context
    mediaType = context["mediaType"]

    try:
        #   Make base dict
        importData = {"identifier": context["identifier"],
                    "displayName": context["displayName"],
                    "mediaType": mediaType,
                    "locations": context["locations"],
                    "path": context["path"],
                    "extension": "",
                    "version": context["version"],
                    "aov": "",
                    "aovs": [],
                    "channel": "",
                    "channels": []
                    }
        
    except Exception as e:
        logger.warning(f"ERROR: Unable to make base importData dict: {e}")
        return {}
    
    #   Combines the two different keys from Assets (type) or Shots (itemType)
    for key in ["itemType", "type"]:
        if key in context:
            importData["itemType"] = context[key]

    #   Add additiona items if they exist
    for key in ["aov", "sequence", "shot", "asset"]:
        if key in context:
            importData[key] = context[key]

    files = []

    #   For "3drenders" and "external media"
    if mediaType in ["3drenders", "externalMedia"]:
        try:
            #   Iterate through both dicts to extract needed data
            for aovItem, sourceItem in zip(aovDict, sourceData):
                #   Add mediaType to each aovItem
                aovItem["mediaType"] = mediaType
                #   Get file list for each aov, and get first file
                filesList = plugin.core.mediaProducts.getFilesFromContext(aovItem)
                basefile = filesList[0]

                #   Get file extension
                if "extension" in context:
                    extension = context["extension"]
                else:
                    _, extension = os.path.splitext(basefile)

                #   Use framerange from sourceData if it exists (sequences)
                if type(sourceItem[1]) == int:
                    frame_start = sourceItem[1]
                    frame_end = sourceItem[2]

                #   Use video duration for video formats
                elif extension in plugin.core.media.videoFormats:
                        duration = plugin.core.media.getVideoDuration(basefile)
                        frame_start = 1
                        frame_end = duration

                #   For Stills Images
                else:
                    frame_start = 1
                    frame_end = 1

                #   Make dict for each AOV
                fileDict = {
                    "basefile": basefile,
                    "identifier": context["identifier"],
                    "aov": aovItem["aov"],
                    "version": context["version"],
                    "frame_start": frame_start,
                    "frame_end": frame_end,
                }

                if "channel" in context:
                    fileDict["channel"] = context["channel"]

                #   Add dict to files list
                files.append(fileDict)

        except Exception as e:
            logger.warning(f"ERROR: Unable to generate file list for {mediaType}:\n{e}")
            return None

    #   For "2drenders:
    else:
        try:
            sourceData = sourceData[0]
            
            #   Get file list and get first file
            filesList = plugin.core.mediaProducts.getFilesFromContext(context)
            basefile = filesList[0]

            #   Get file extension
            if "extension" in context:
                extension = context["extension"]
            else:
                _, extension = os.path.splitext(basefile)

            #   Use framerange from sourceData if it exists (sequences)
            if type(sourceData[1]) == int:
                frame_start = sourceData[1]
                frame_end = sourceData[2]

            #   Use video duration for video formats
            elif extension in plugin.core.media.videoFormats:
                    duration = plugin.core.media.getVideoDuration(basefile)
                    frame_start = 1
                    frame_end = duration

            #   For Stills Images
            else:
                frame_start = 1
                frame_end = 1

            #   Make dict for each AOV
            fileDict = {
                "basefile": basefile,
                "identifier": context["identifier"],
                "version": context["version"],
                "frame_start": frame_start,
                "frame_end": frame_end,
            }

            if "channel" in context:
                fileDict["channel"] = context["channel"]

            files.append(fileDict)

        except Exception as e:
            logger.warning(f"ERROR: Unable to generate file list for {mediaType}:\n{e}")
            return None

    # Add the files to the importData
    importData["files"] = files

    #   Add additional data if exist
    importData["extension"] = extension

    try:
        channels = plugin.core.media.getLayersFromFile(basefile)
        importData["channels"] = channels

    except Exception as e:
        logger.warning(f"ERROR: Unable to add channel data to importData: {e}")

    if "versionPaths" in context:
        importData["versionPaths"] = context["versionPaths"]

    if "redirect" in context:
        importData["redirect"] = context["redirect"]

    if importData["mediaType"] in ["3drenders", "external"]:
        try:
            importData["aovs"] = getAovNamesFromAovDict(aovDict)
        except Exception as e:
            logger.warning(f"ERROR: Unable to get AOV names list: {e}")

    return importData


#   Return File data based on desired AOV

def getFileDataFromAOV(fileList:list, aov:str) -> dict:
    #   If list is one item, jut return the item
    if len(fileList) == 1:
        return fileList[0]
    
    #   Iterate through list to find matching AOV
    for fileData in fileList:
        if "aov" in fileData:
            if fileData["aov"] == aov:
                return fileData
            
    return None


def compareVersions(origVerRecord:dict, updateVerRecord:dict) -> Tuple[bool, str]:
    try:
        #   Get original version
        origVer_str = origVerRecord["version"]
        # Convert to Int
        origVer_match = re.search(r'\d+', origVer_str)
        origVer_int = int(origVer_match.group()) if origVer_match else 0

        #   Get updated version
        updateVer_str = updateVerRecord["version"]
        # Convert to Int
        updateVer_match = re.search(r'\d+', updateVer_str)
        updateVer_int = int(updateVer_match.group()) if updateVer_match else 0

        #   Get frame ranges
        origFrameStart_int = int(origVerRecord['frame_start'])
        origFrameEnd_int = int(origVerRecord['frame_end'])
        origFramerange = f"{origFrameStart_int} - {origFrameEnd_int}"
        updateFramerange = f"{updateVerRecord['frame_start']} - {updateVerRecord['frame_end']}"

        #   Make name for update popup
        compareName = origVerRecord.get("mediaId")
        if "aov" in origVerRecord:
            compareName = compareName + f"_{origVerRecord['aov']}"
        if "channel" in origVerRecord:
            compareName = compareName + f"_{origVerRecord['channel']}"
   
        ## Compare versions - return a list with two items:
            #   a bool showing if there was an update
            #   a message as a list with two items:
                #   the name of the media being compared
                #   the result of the comparison

        #   If versions are the same
        if origVer_int == updateVer_int:
            
            #   If frame ranges are the same
            if origFramerange == updateFramerange:
                return [False, [f"{compareName}:", "  No Changes"]]

            #   If frame ranges different
            else:
                return [True, [f"{compareName}:", f"updated {origVer_str} frameRange ({origFramerange}-{updateFramerange})"]]

        #   Versions are different
        else:
            return [True, [f"{compareName}:", f"{origVer_str} ({origFramerange})  -->  {updateVer_str} ({updateFramerange})"]]

    except Exception as e:
        logger.warning(f"ERROR: Unable to make version update message - {e}")
        return [False, "ERROR"]


#	Returns an average luminance value
def calculateLuminance(color:dict) -> float:
    try:
        r,g,b = color['R'], color['G'], color['B']
        # No need for normalization if RGB values are already in [0, 1]
        luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
        return luminance
    except:
        logger.warning("ERROR:  Unable to calculate luminance")
        return 0.4
    

#	Determines if color is bighter than threshold

def isBgBright(color:dict, threshold=0.5) -> bool:
    luminance = calculateLuminance(color)
    return luminance > threshold