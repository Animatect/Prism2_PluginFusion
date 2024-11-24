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
	

import os
import re
from typing import Union, Dict, Any
import logging

from PrismUtils.Decorators import err_catcher as err_catcher

logger = logging.getLogger(__name__)


#   For Python Type Hints
FusionComp = Dict
Tool = Any
ToolOption = Any
Color = int
UUID = str
Toolname = str


#   Creates Default Database
@err_catcher(name=__name__)
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
@err_catcher(name=__name__)
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


@err_catcher(name=__name__)
def makeLdrName(importData:dict) -> str:
    #	Sets up the name based on avail data
    try:
        ldrName = importData.get('identifier') or importData.get("mediaId")

        if "aov" in importData:
            ldrName = ldrName + f"_{importData['aov']}"

        if "currChannel" in importData:
            ldrName = ldrName + f"_{importData['currChannel']}"
   
        ldrName = ldrName + f"_{importData['version']}"
        
        return ldrName
    
    except Exception as e:
        logger.warning(f"ERROR: Unable to make Loader name from Import Data:\n{e}")
        return None


@err_catcher(name=__name__)
def makeImportData(plugin, context:dict, aovDict:dict, sourceData:dict) -> dict:
    #   Get mediaType from Context
    mediaType = context["mediaType"]

    try:
        #   Make base dict
        importData = {"identifier": context["identifier"],
                    "displayName": context["displayName"],
                    "mediaType": mediaType,
                    "itemType": context["itemType"],
                    "locations": context["locations"],
                    "path": context["path"],
                    "extension": "",
                    "version": context["version"],
                    "currentAov": "",
                    "aovs": [],
                    "currChannel": "",
                    "channels": []
                    }
        
    except Exception as e:
        logger.warning(f"ERROR: Unable to make base importData dict: {e}")
        return {}
    
    #   Add AOV if it exists
    if "aov" in context:
        importData["currentAov"] = context["aov"]

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

                #   Use framerange from sourceData if it exists (sequences)
                if type(sourceItem[1]) == int:
                    frame_start = sourceItem[1]
                    frame_end = sourceItem[2]

                #   Use video duration for video formats
                else:
                    duration = plugin.core.media.getVideoDuration(basefile)
                    frame_start = 1
                    frame_end = duration

                #   Make dict for each AOV
                fileDict = {
                    "basefile": basefile,
                    "identifier": context["identifier"],
                    "aov": aovItem["aov"],
                    "version": context["version"],
                    "frame_start": frame_start,
                    "frame_end": frame_end,
                }

                #   Add dict to files list
                files.append(fileDict)

        except Exception as e:
            logger.warning(f"ERROR: Unable to generate file list for {mediaType}:\n{e}")
            return {}

    #   For "2drenders:
    else:
        try:
            sourceData = sourceData[0]
            
            #   Get file list and get first file
            filesList = plugin.core.mediaProducts.getFilesFromContext(context)
            basefile = filesList[0]

            #   Use framerange from sourceData if it exists (sequences)
            if type(sourceData[1]) == int:
                frame_start = sourceData[1]
                frame_end = sourceData[2]

            #   Use video duration for vieo formats
            else:
                duration = plugin.core.media.getVideoDuration(basefile)
                frame_start = 1
                frame_end = duration

            #   Make dict for each AOV
            fileDict = {
                "basefile": basefile,
                "identifier": context["identifier"],
                "version": context["version"],
                "frame_start": frame_start,
                "frame_end": frame_end,
            }

            files.append(fileDict)

        except Exception as e:
            logger.warning(f"ERROR: Unable to generate file list for {mediaType}:\n{e}")
            return {}

    # Add the files to the importData
    importData["files"] = files

    #   Add additional data if exist
    try:
        if "channel" in context:
            importData["currChannel"] = context["channel"]

        channels = plugin.core.media.getLayersFromFile(basefile)
        importData["channels"] = channels

    except Exception as e:
        logger.warning(f"ERROR: Unable to add channel data to importData: {e}")

    try:
        if "extension" in context:
            importData["extension"] = context["extension"]
        else:
            _, extension = os.path.splitext(files[0]["basefile"])
            importData["extension"] = extension
    except Exception as e:
        logger.warning(f"ERROR: Unable to add extention to importData: {e}")

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



