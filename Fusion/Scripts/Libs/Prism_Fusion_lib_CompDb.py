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
	


import json
import re
import uuid
import hashlib
from datetime import datetime
from typing import Union, Dict, Tuple, Any
import logging

from PrismUtils.Decorators import err_catcher as err_catcher

logger = logging.getLogger(__name__)


### THIS IS A LIBRARY FOR THE PRISM DATABASE SAVED TO THE COMP  ###


#   LETS KEEP THIS STRUCTURE UPDATED WITH CHANGES

#   DataBase Structure:                                 #   TODO - MAKE SURE IT IS ACCURATE
#
#   Root(
#       "nodes"(
#           "import2d" (
#               UUID: {
#                   NodeData: {
#                        "nodeName": string       (  {mediaId}_{aov}_{channel}_{version}  )
#                        "version": string        (  v001  )
#                        "mediaId": string        (  IdentifierName  )
#                        "displayName": string    (  IdentifierName (2d)  )
#                        "mediaType": string      (  2drenders, 3drenders, externalMedia  )
#                        "AOV": string            (  RGB, AO, Beauty  )
#                        "filepath": string       (  full path of first file in seq  )
#                        "extension": string      (  .exr, .mov  )
#                        "fuseFormat": string     (  OpenEXRFormat  )
#                        "frame_start": int       (  1  )
#                        "frame_end": int         (  100  )
#                        "connectedNodes": list   (  a43dg4th, 4jt86d5e  )
#                        }
#                     }
#                  }
#           "import3d" (
#               UUID: {
#                   NodeData: {
#                        "nodeName": string
#                        "version": string
#                        "filepath": string
#                        "format": string
#                        "product": string
#                        "connectedNodes": list
#                        }
#                     }
#                  }
#           "render2d" (
#               UUID: {
#                   NodeData: {
#                        "nodeName": string
#                        "version": string
#                        "filepath": string
#                        "format": string
#                        }
#                     }
#                  }
#           "export3d" (
#               UUID: {
#                   NodeData: {
#                        "nodeName": string
#                        "version": string
#                        "filepath": string
#                        "format": string
#                        }
#                     }
#                  }



#   For Python Type Hints
Tool = Any
Color = int
UUID = str
Toolname = str


#	Creates UUID
@err_catcher(name=__name__)
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


#   Creates Default Database
@err_catcher(name=__name__)
def createDefaultPrismFileDb(comp) -> dict:
    #   This template needs to have the required keys.
    #   Add additional keys as needed.
    defaultDb = {
        "fileValues": {
            "identifiersColors": {
                "asset": {},
                "shot": {}
            }
        },
        "nodes": {
            "import3d": {},
            "import2d": {},
            "render2d": {},
            "export3d": {}
        }
    }

    try:
        logger.debug("Creating default Prism Comp Database")
        cpData_str = json.dumps(defaultDb)
        comp.SetData("PrismDB", cpData_str)
        return defaultDb
    except:
        logger.warning("ERROR: Unable to create default Prism Comp Database")
        return None


#   Returns the Database Dict
@err_catcher(name=__name__)
def loadPrismFileDb(comp) -> dict:
    try:
        cpData_str = comp.GetData("PrismDB")
    except:
        logger.warning("ERROR: Unable to get Prism Comp Database from the Comp")

    if cpData_str:
        cpData = json.loads(cpData_str)
        logger.debug("Loaded Prism Comp Database")
    else:
        cpData = createDefaultPrismFileDb(comp)

    return cpData


#   Saves the Database Dict
@err_catcher(name=__name__)
def savePrismFileDb(comp, cpData_orig:dict):

    #   Clean DB dict before saving
    cpData_cleaned = cleanPrismFileDb(comp, cpData_orig)

    #   Only use cleaned if it is not None
    if cpData_cleaned:
        cpData = cpData_cleaned
    else:
        cpData = cpData_orig

    try:
        cpData_str =  json.dumps(cpData, indent=4)
        comp.SetData("PrismDB", cpData_str)
        logger.debug("Saved Prism Comp Database to Comp")

        print(f"\n***  Prism Database:\n{print(comp.GetData('PrismDB'))}\n")                            #   TESTING

    except:
        logger.warning("ERROR: Failed to save Prism Comp Database to Comp")


#   Removes DB records if the node does not exist in Comp
@err_catcher(name=__name__)
def cleanPrismFileDb(comp, cpData_orig:dict) ->dict:
    try:
        cpData_cleaned = cpData_orig.copy()

        # Iterate through all subcategories under the "nodes" key
        for subcategory, nodes in cpData_cleaned["nodes"].items():
            # Collect UIDs to remove if they do not exist in the composition
            uids_to_remove = [
                node_uid for node_uid in nodes
                if not nodeExists(comp, node_uid)
                ]

            # Remove the invalid UIDs from the current subcategory
            for uid in uids_to_remove:
                logger.debug(f"Cleaned {uid} record from Database")
                del nodes[uid]

        return cpData_cleaned
        
    except Exception as e:
        logger.warning(f"ERROR: Failed to Clean Prism Comp Database:\n{e}")
        return None


#   Adds a new Media Identifier to the DB
@err_catcher(name=__name__)
def addPrismDbIdentifier(comp, category:str, name:str, color:int):
    cpData = loadPrismFileDb(comp)
    try:
        if category in ["asset", "shot"]:
            cpData["fileValues"]["identifiersColors"][category][name] = color
            savePrismFileDb(comp, cpData)
            logger.debug(f"Added {category}{name} to Prism Comp Database")
    except:
        logger.warning("ERROR:  Unable to add Identifier")


#   Returns the Color of a Given Identifier
@err_catcher(name=__name__)
def getPrismDbIdentifierColor(comp, category:str, name:str) -> Union[Color, None]:
    try:
        logger.debug(f"Getting Identifier Color for {name}")
        cpData = loadPrismFileDb(comp)
        if category in cpData["fileValues"]["identifiersColors"]:
            if name in cpData["fileValues"]["identifiersColors"][category]:
                color = cpData["fileValues"]["identifiersColors"][category][name]
                logger.debug(f"{color} found for {name}")
                return color
        
        logger.debug(f"No color associated with {name}")
        return None
    except:
        logger.warning("ERROR:  Unable to get Identifier Color")


#   Adds new Node to the DB
@err_catcher(name=__name__)
def addNodeToDB(comp, type:str, UUID:str, nodeData:dict) -> bool:
    cpData = loadPrismFileDb(comp)

    #   Remove the UID from the data since it is the main key
    for key in ["nodeUID", "toolUID"]:
        if key in nodeData:
            del nodeData[key]

    try:
        #   Checks is there is already an item in the DB
        matchingUID = checkRecordInDb(comp, type, UUID, nodeData)
        if matchingUID:
            #   Removes the original record and reloads the DB
            removeNodeFromDB(comp, type, matchingUID)
            cpData = loadPrismFileDb(comp)

        #   Adds the record to the Database
        cpData["nodes"][type][UUID] = nodeData
        savePrismFileDb(comp, cpData)
        logger.debug(f"Added {nodeData['nodeName']} to the Comp Database")
        return True

    except Exception as e:
        logger.warning(f"ERROR:  Failed to add the Node Data to the Comp Database\n{e}")
        return False
    

#   Checks is there is already a record in the Database
#   This is to cover if a node was added, then deleted in Fusion, and added again.
@err_catcher(name=__name__)
def checkRecordInDb(comp, type:str, UUID:str, nodeData:dict) -> Union[UUID | bool]:
    cpData = loadPrismFileDb(comp)

    try:
        #   Get the database branch for the specified type
        typeBranch = cpData["nodes"].get(type, {})

        #   Items to compare in the records
        checkItems = ["nodeName", "version", "filepath", "format", "mediaId", "displayName"]

        for recordUUID, recordData in typeBranch.items():
            #   Skip if the record does not have a "NodeData" structure
            if not isinstance(recordData, dict):
                continue

            # Check if all checkItems match
            match = True
            for item in checkItems:
                if item in nodeData and item in recordData:
                    if nodeData[item] != recordData[item]:
                        logger.debug(f"Mismatch found for {item} in record {recordUUID}: "
                                     f"{nodeData[item]} != {recordData[item]}")
                        match = False
                        break
                elif item in nodeData or item in recordData:
                    #   Key exists in one but not the other
                    logger.debug(f"Key {item} is missing in either nodeData or record {recordUUID}")
                    match = False
                    break

            #   If all checkItems match,
            if match:
                logger.debug(f"Matching record found for node: {recordUUID}")
                return recordUUID

        #   No matching record found
        logger.debug(f"No record found for node: {UUID}")
        return False

    except Exception as e:
        logger.warning(f"ERROR: Failed to check record in database: {e}")
        return False


#   Removes a Node from the DB
@err_catcher(name=__name__)
def removeNodeFromDB(comp, type:str, UUID:str):
    cpData = loadPrismFileDb(comp)

    try:
        if UUID in cpData["nodes"][type]:
            del cpData["nodes"][type][UUID]
            logger.debug(f"Removed {UUID} from the Comp Database")
            savePrismFileDb(comp, cpData)
        else:
            logger.debug(f"{UUID} does not exist in the Comp Database")
            
    except:
        logger.warning(f"ERROR: Unable to remove {UUID} from the Comp Database")


#   Gets the database record for a given importData dict
@err_catcher(name=__name__)
def getUIDsFromImportData(comp, type:str, importData:dict) -> dict:
    cpData = loadPrismFileDb(comp)

    if not cpData:
        return None
    
    uids = []
    
    try:
        #   Get the requested node type
        nodes = cpData.get("nodes", {}).get(type, {})
        if not nodes:
            logger.warning(f"ERROR: Node type '{type}' not found in the database.")
            return None
        
        #   Extract fields from importData
        import_mediaId = importData.get("identifier")
        import_mediaType = importData.get("mediaType")
        import_aov = importData.get("aov")
        import_channel = importData.get("channel")

        # Search for a record matching all the available items
        for uuid, node_data in nodes.items():
            match = True

            if node_data.get("mediaId") != import_mediaId:
                match = False
            
            if node_data.get("mediaType") != import_mediaType:
                match = False

            # Check aov if it exists in both the database and importData
            if "aov" in node_data and import_aov is not None and import_aov != "":
                if node_data.get("aov") != import_aov:
                    match = False

            if match:
                # If all checks pass, return the match
                if nodeExists(comp, uuid):
                    uids.append(uuid)

        return uids
    
    except:
        logger.warning(f"No nodes found with mediaId '{import_mediaId}' in type '{type}'.")
        return None


#   Gets the database record for a given Identifier
@err_catcher(name=__name__)
def getDbRecordFromMediaId(comp, type:str, mediaId:str) -> dict:
    cpData = loadPrismFileDb(comp)

    if not cpData:
        return None
    
    #   Get the requested node type
    nodes = cpData.get("nodes", {}).get(type, {})
    if not nodes:
        logger.warning(f"ERROR: Node type '{type}' not found in the database.")
        return None
    
    #   Search for a node matching the given mediaId
    for uuid, node_data in nodes.items():
        if node_data.get("mediaId") == mediaId:
            exists = nodeExists(comp, uuid)
            if exists:
                return [uuid, exists, node_data]
                
    logger.warning(f"ERROR: No node found with mediaId '{mediaId}' in type '{type}'.")
    return None


#   Updates the Node's Data in the DB
@err_catcher(name=__name__)
def updateNodeInfo(comp, type:str, UUID:str, nodeData:dict) -> bool:
    cpData = loadPrismFileDb(comp)

    #   Remove the UID from the data since it is the main key
    nodeDataCopy = nodeData.copy()
    for key in ["nodeUID", "toolUID"]:
        if key in nodeDataCopy:
            del nodeDataCopy[key]

    try:
        #   Updates existing keys as needed
        if UUID in cpData["nodes"][type]:
            cpData["nodes"][type][UUID].update(nodeDataCopy)

            if "nodeName" in nodeDataCopy:
                logger.debug(f"Updated {nodeDataCopy['nodeName']} data.")
            else:
                logger.debug(f"Updated {UUID} data.")
            
            savePrismFileDb(comp, cpData)
            return True
        
        else:
            logger.debug(f"The is no data for node: {UUID}")
            return False
    except Exception as e:
        logger.warning(f"ERROR: Failed to update Node Data for {UUID}\n{e}")
        return False
        

#   Return the Node Data for a given Node
@err_catcher(name=__name__)
def getNodeInfo(comp, type:str, UUID:str) -> dict:
    cpData = loadPrismFileDb(comp)

    try:
        if UUID in cpData["nodes"][type]:
            return cpData["nodes"][type][UUID]
        else:
            logger.debug(f"The is no data for node: {UUID}")
            return False
    except:
        logger.warning("ERROR: Failed to read Node Data")
        return False


#   Returns list of import files based on selected tools
@err_catcher(name=__name__)
def getFilesFromSelTools(comp, importData:dict, selUIDs:list) -> list:
    selItems = []
    #   Get files list
    importFileList = importData["files"]

    for importFile in importFileList:
        #   Make copy to edit
        importFileData = importData.copy()

        #   Add items to copy
        importFileData["aov"] = importFile["aov"]

        if "channel" in importData:
            importFileData["channel"] = importData["channel"]

        importFileData["files"] = [importFile]

        #   Get associated UIDs for each file in list
        uids = getUIDsFromImportData(comp, "import2d", importFileData)

        #   Filter files by selected UIDs
        for uid in uids:
            if uid in selUIDs:
                selItems.append(importFile)

    return selItems


#   Compares two version data dicts and returns result and message
@err_catcher(name=__name__)
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
        origFramerange = f"{origVerRecord['frame_start']} - {origVerRecord['frame_end']}"
        updateFramerange = f"{updateVerRecord['frame_start']} - {updateVerRecord['frame_end']}"

        #   Make name for update popup
        compareName = origVerRecord.get("mediaId")
        if "aov" in origVerRecord:
            compareName = compareName + f"_{origVerRecord['aov']}"
        if "channel" in origVerRecord:
            compareName = compareName + f"_{origVerRecord['channel']}"
   
        ## Compare versions

        #   If versions are the same
        if origVer_int == updateVer_int:
            #   If frame ranges are the same
            if origFramerange == updateFramerange:
                return [False, f"{compareName}:   No Changes"]
            
            #   If frame ranges different
            else:
                return [True, f"{compareName}:   updated {origVer_str} FrameRange ({origFramerange}-{updateFramerange})"]
            
        #   Versions are different
        else:
            return [True, f"{compareName}:   {origVer_str} ({origFramerange})  -->  {updateVer_str} ({updateFramerange})"]
    
    except Exception as e:
        logger.warning(f"ERROR: Unable to make version update message - {e}")
        return [False, "ERROR"]


#	Checks if a matching tool exists in the comp
@err_catcher(name=__name__)
def nodeExists(comp, nodeUID:str) -> bool:
    if getNodeByUID(comp, nodeUID):
        return True
    return False


#   Returns tool based on UID
@err_catcher(name=__name__)
def getNodeByUID(comp, nodeUID:str) -> Union[Tool, None]:
    try:
        #   Gets all tools
        tools = comp.GetToolList(False)

        for tool_name, tool in tools.items():
            toolUID = tool.GetData('Prism_UUID')

            if toolUID == nodeUID:
                return tool
            
        raise Exception
    
    except:
        logger.warning(f"ERROR: No node found for {nodeUID}")
        return None


#   Returns tool name based on UID
@err_catcher(name=__name__)
def getNodeNameByUID(comp, nodeUID:str) -> Toolname:
    tool = getNodeByUID(comp, nodeUID)
    toolName = getNodeNameByTool(tool)

    return toolName


#   Returns tool name for tool
@err_catcher(name=__name__)
def getNodeNameByTool(tool:Tool) -> Toolname:
    try:
        toolName = tool.GetAttrs()["TOOLS_Name"]
        return toolName
    except:
        logger.warning(f"ERROR: Cannot get name for {tool}")
        return None
    

#   Returns tool's UID
@err_catcher(name=__name__)
def getNodeUidFromTool(tool) -> str:
    try:
        nodeUID = tool.GetData('Prism_UUID')
        return nodeUID
    except:
        logger.warning(f"ERROR: Cannot get UUID for {tool}")
        return None


#   Returns tool UID based on Identifier
@err_catcher(name=__name__)
def getNodeUidFromMediaId(comp, type:str, mediaId:str) -> Union[str | list | None]:
    cpData = loadPrismFileDb(comp)

    matchingNodes = []

    try:
        #   Iterate through nodes of the given type
        for uuid, nodeData in cpData["nodes"].get(type, {}).items():
            if nodeData.get("mediaId") == mediaId:
                matchingNodes.append(uuid)
        
        #   Return None if no matching mediaId is found
        if len(matchingNodes) == 0:
            return None
        
        #   Return string if there is only one node
        elif len(matchingNodes) == 1:
            return matchingNodes[0]
        
        #   Return List if there are multiple
        else:
            return matchingNodes
    except:
        logger.warning("ERROR: Uanble to get UUID from Media Identifier.")
        return None
    

#   Returns tool UID based on Identifier display name
@err_catcher(name=__name__)
def getNodeUidFromMediaDisplayname(comp, type:str, mediaId:str) -> Union[UUID | None]:
    cpData = loadPrismFileDb(comp)

    mediaIdUids = []

    try:
        # Iterate through nodes of the given type
        for uuid, nodeData in cpData["nodes"].get(type, {}).items():
            if nodeData.get("displayName") == mediaId:
                mediaIdUids.append(uuid)
        
        if len(mediaIdUids) == 0:
            return None
        
        elif len(mediaIdUids) == 1:
            return mediaIdUids[0]
        
        else:
            return mediaIdUids
    
    except:
        # Return None if no matching mediaId is found
        return None


#   Returns the Connected Nodes for a given Node
@err_catcher(name=__name__)
def getConnectedNodes(comp, type:str, UUID:str) -> Union[list | None]:
    cpData = loadPrismFileDb(comp)

    try:
        if UUID in cpData["nodes"][type]:
            nodeData = cpData["nodes"][type][UUID]
            return nodeData["connectedNodes"]
        else:
            logger.debug(f"{UUID} does not exist in the Comp Database")
            return None
    except:
        logger.warning(f"ERROR: Unable to get connected nodes for {UUID}")
        return None
    

#	Gets either single UID or List of UID's
#	and returns the original and all connected UUID's
@err_catcher(name=__name__)
def getAllConnectedNodes(comp, nodeUIDs:Union[list|str]) -> list:
    mainToolsUIDs = []
    allToolUIDs = []

    try:
        #   Handle single or multiple nodeUIDs
        mainToolsUIDs = nodeUIDs if isinstance(nodeUIDs, list) else [nodeUIDs]

        #	Check if there are any Loaders for this Task
        if len(mainToolsUIDs) == 0:
            raise Exception

        for mainToolUID in mainToolsUIDs:
            allToolUIDs.append(mainToolUID)
            #	Get connected  nodes from the Comp Database
            connectedNodes = getConnectedNodes(comp, "import2d", mainToolUID)
            for connNodeUID in connectedNodes:
                allToolUIDs.append(connNodeUID)
        
        logger.debug(f"Getting all connected nodes for {nodeUIDs}")
        return allToolUIDs   

    except:
        logger.warning("ERROR: Unable to get all connected nodes")
        return None 


# Checks if tool is set to pass-through mode
@err_catcher(name=__name__)
def isPassThrough(comp, nodeUID:str=None, node:str=None) -> bool:
    if nodeUID:
        node = getNodeByUID(comp, nodeUID)

    return node and node.GetAttrs({"TOOLS_Name"})["TOOLB_PassThrough"]


#	Sets the Fusion node's passthrough
@err_catcher(name=__name__)
def setPassThrough(comp, nodeUID:str=None, node:str=None, passThrough=False):
    if nodeUID:
        node = getNodeByUID(comp, nodeUID)
    node.SetAttrs({"TOOLB_PassThrough": passThrough})


#   Reloads the Loaders and sets the clip start/end/length
@err_catcher(name=__name__)
def reloadLoader(fusion, comp, node, filePath=None, firstframe=None, lastframe=None):
    try:
        if filePath:
            # Rename the clipname to force reload duration
            node.Clip[fusion.TIME_UNDEFINED] = filePath

        # If first frame is None, it is probably not a sequence.
        if firstframe:
            node.GlobalOut[0] = lastframe
            node.GlobalIn[0] = firstframe

            # Trim
            node.ClipTimeStart = 0
            node.ClipTimeEnd = lastframe - firstframe
            node.HoldLastFrame = 0

        # Clips Reload
        setPassThrough(comp, node=node, passThrough=True)
        setPassThrough(comp, node=node, passThrough=False)

        logger.debug(f"Reloaded Loader: {filePath}")

    except:
        logger.warning(f"ERROR: Failed to reload Loader: {filePath}")



################################
###        STATE DATA        ###

@err_catcher(name=__name__)
def setDefaultState(comp):
    defaultState = """{
    "states": [
        {
            "statename": "publish",
            "comment": "",
            "description": ""
        }
    ]
}_..._
"""
    try:
        comp.SetData("prismStates", defaultState)
        logger.debug("Saved the empty state data to the comp")
    except:
        logger.warning(f"ERROR: Unable to save default State Data to comp: {comp}")


@err_catcher(name=__name__)
def sm_saveStates(comp, buf:str):
    try:
        comp.SetData("prismStates", buf + "_..._")
        logger.debug(f"Saved the state data to the comp.")
    except:
        logger.warning(f"ERROR: Unable to save State Data to comp: {comp}")


@err_catcher(name=__name__)
def sm_saveImports(comp, importPaths:str):
    prismdata = comp.GetData("prismStates")
    prismdata += importPaths.replace("\\\\", "\\")
    comp.SetData("prismStates", prismdata)


@err_catcher(name=__name__)
def sm_readStates(comp) -> str:
    try:
        prismdata = comp.GetData("prismStates")
        return prismdata.split("_..._")[0]
    except:
        logger.warning(f"ERROR:  Unable to read State Data from comp: {comp}")
        return 


#	Gets called from SM to remove all States
@err_catcher(name=__name__)
def sm_deleteStates(comp):
    #	Sets the states datablock to empty default state
    setDefaultState()


@err_catcher(name=__name__)
def getImportPaths(comp) -> str:
    prismdata = comp.GetData("prismStates")
    return prismdata.split("_..._")[1]
