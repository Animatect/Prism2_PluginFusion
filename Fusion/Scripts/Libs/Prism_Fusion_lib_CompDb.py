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


##  THIS IS A LIBRARY FOR DATABASE FUNCTIONS FOR THE FUSION PRISM PLUGIN  ##
	


import json
import re
import uuid
import hashlib
from datetime import datetime
from typing import TYPE_CHECKING, Union, Dict, Tuple, Any
import logging

from . import Prism_Fusion_lib_3d as Fus3D 

from PrismUtils.Decorators import err_catcher as err_catcher

from typing import TYPE_CHECKING, Any, Literal
if TYPE_CHECKING:
    from StateManagerNodes.fus_Legacy3D_Import import Legacy3D_ImportClass
else:
    Tool_ = Any
    Composition_ = Any
    FlowView_ = Any
    Fusion_ = Any
    Legacy3D_ImportClass = Any
    Input_ = Any
    Output_ = Any

logger = logging.getLogger(__name__)


####################################################################################
####   THIS IS A TEMPLATE FOR THE PRISM DATABASE STRUCTURE SAVED IN THE COMP    ####

#   DataBase Structure:                                 ####   TODO - MAKE SURE IT IS ACCURATE     ####
#
#   Root(
#        "comp": {
#           "mediaIdColors": {
#               "asset": {},
#               "shot": {
#               "MEDIA IDENTIFIER": {           (  string  )
#                   "R": 1.0,                   (  int  )
#                   "G": 0.6588235294117647,    (  int  )
#                   "B": 0.2                    (  int  )
#                   }
#               }
#           },
#           "sortingDisabled": bool
#       },
#       "nodes"{
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
#                        "3dFilepath": string
#                        "product": string
#                        "format": string
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

####################################################################################


#   For Python Type Hints
Tool = Any
Color = int
UUID = str
Toolname = str


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


#   Creates Default Database

def createDefaultPrismFileDb(comp) -> dict:
    #   This template needs to have the required keys.
    #   Add additional keys as needed.
    defaultDb = {
        "comp": {
            "mediaIdColors": {
                "asset": {},
                "shot": {}
            },
            "sortingDisabled": False
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

def savePrismFileDb(comp, cpData_orig:dict):

    #   Clean DB dict before saving
    cpData_cleaned = cleanPrismFileDb(comp, cpData_orig)

    #   Only use cleaned if it is not None
    if cpData_cleaned:
        cpData = cpData_cleaned
    else:
        cpData = cpData_orig

    try:
        cpData_str =  json.dumps(cpData)#, indent=4)
        comp.SetData("PrismDB", cpData_str)
        logger.debug("Saved Prism Comp Database to Comp")

        # print(f"\n***  Prism Database:\n{print(comp.GetData('PrismDB'))}\n")                            #   TESTING

    except:
        logger.warning("ERROR: Failed to save Prism Comp Database to Comp")


#   Removes DB records if the node does not exist in Comp

def cleanPrismFileDb(comp, cpData_orig:dict) -> dict:
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


#   Adds DB records if the node does not exist in the DB but does exist in the comp.

def updatePrismFileDB(comp:Composition_):
    # be sure to add the nodetype/category to the database and the data in the Fus library function (where it goes in the DB). 
    flow:FlowView_ = comp.CurrentFrame.FlowView    
    # get all nodes in the comp that have a Prism UUID
    prismTools:list[Tool_] = [t for t in comp.GetToolList().values() if t.GetData("Prism_UUID")]
    # get all nodes in the database as a collection.
    alldbnodes:dict = Fus3D.getAllNodes(comp)
    # check if the nodes that have a UUID exist in the database nodes collection.
    for tool in prismTools:
        tooluid:str|None = tool.GetData("Prism_UUID")
        if not tooluid in alldbnodes:
        # if a node is not in the db check if has dbData property/data
            dbData:dict = tool.GetData("Prism_ToolData")
            if dbData:
                listType:str|None = tool.GetData("Prism_ToolData").get("listType")
                if listType:
                # add the node to the database records
                    addNodeToDB(comp, listType, tooluid, tool.GetData("Prism_ToolData"))
                    # TODO Alternatively add a State...


def addPrismDbIdentifier(comp, category:str, name:str, color:int):
    cpData = loadPrismFileDb(comp)
    try:
        if category in ["asset", "shot"]:
            cpData["comp"]["mediaIdColors"][category][name] = color
            savePrismFileDb(comp, cpData)
            logger.debug(f"Added {category}{name} to Prism Comp Database")
    except:
        logger.warning("ERROR:  Unable to add Identifier")


#   Returns the Color of a Given Identifier

def getPrismDbIdentifierColor(comp, category:str, name:str) -> Union[Color, None]:
    try:
        logger.debug(f"Getting Identifier Color for {name}")
        cpData = loadPrismFileDb(comp)
        if category in cpData["comp"]["mediaIdColors"]:
            if name in cpData["comp"]["mediaIdColors"][category]:
                color = cpData["comp"]["mediaIdColors"][category][name]
                logger.debug(f"{color} found for {name}")
                return color
        
        logger.debug(f"No color associated with {name}")
        return None
    except:
        logger.warning("ERROR:  Unable to get Identifier Color")


#   Sets/Gets the checkbox state of the dialog as part of the comp data.

def sortingEnabled(comp, save:bool=False, checked:bool=None) -> bool:
    cpData = loadPrismFileDb(comp)

    if save:
        try:
            cpData["comp"]["sortingDisabled"] = checked
            savePrismFileDb(comp, cpData)
            return True
        except:
            logger.warning("ERROR:  Unable to save Sorting Disabled state")
            return False

    try:
        return cpData["comp"]["sortingDisabled"]
    except:
        logger.warning("ERROR:  Unable to get Sorting Disabled state")
        return False
    

#   Adds new Node to the DB

def addNodeToDB(comp, listType:str, UUID:str, nodeData:dict, saveDB:bool=True, aggregateData:dict=None) -> bool:
    cpData = loadPrismFileDb(comp)
    if not saveDB and aggregateData:
        cpData = aggregateData.copy()

    #   Remove the UID from the data since it is the main key
    for key in ["nodeUID", "toolUID"]:
        if key in nodeData:
            del nodeData[key]

    try:
        #   Checks is there is already an item in the DB
        matchingUID = checkRecordInDb(comp, listType, UUID, nodeData)
        if matchingUID:
            #   Removes the original record and reloads the DB
            removeNodeFromDB(comp, listType, matchingUID)
            cpData = loadPrismFileDb(comp)

        #   Adds the record to the Database
        cpData["nodes"][listType][UUID] = nodeData
        if saveDB:
            savePrismFileDb(comp, cpData)
        else:
            aggregateData = cpData

        if "nodeName" in nodeData:                                                  #   TODO Deal with toolName vs nodeName
            logger.debug(f"Added {nodeData['nodeName']} to the Comp Database")
        elif "toolName" in nodeData:
            logger.debug(f"Added {nodeData['toolName']} to the Comp Database")
        else:
            logger.debug(f"Added {UUID} to the Comp Database")

        return True

    except Exception as e:
        logger.warning(f"ERROR:  Failed to add the Node Data to the Comp Database\n{e}")
        return False
    

#   Checks is there is already a record in the Database
#   This is to cover if a node was added, then deleted in Fusion, and added again.

def checkRecordInDb(comp, listType:str, UUID:str, nodeData:dict) -> Union[UUID | bool]:
    cpData = loadPrismFileDb(comp)

    try:
        #   Get the database branch for the specified listType
        typeBranch = cpData["nodes"].get(listType, {})

        #   Items to compare in the records
        checkItems = ["nodeName", "groupName", "shaderName", "version", "filepath", "format", "mediaId", "displayName", "tooltype"]

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

def removeNodeFromDB(comp, listType:str, UUID:str, saveDB:bool=True, aggregateData:dict=None):
    cpData = loadPrismFileDb(comp)
    if not saveDB and aggregateData:
        cpData = aggregateData.copy()

    try:
        if UUID in cpData["nodes"][listType]:
            del cpData["nodes"][listType][UUID]
            logger.debug(f"Removed {UUID} from the Comp Database")
            if saveDB:
                savePrismFileDb(comp, cpData)
            else:
                aggregateData = cpData
        else:
            logger.debug(f"{UUID} does not exist in the Comp Database")
            
    except:
        logger.warning(f"ERROR: Unable to remove {UUID} from the Comp Database")


#   Gets the database record for a given importData dict

def getUIDsFromImportData(comp, listType:str, importData:dict) -> dict:
    cpData = loadPrismFileDb(comp)

    if not cpData:
        return None
    
    uids = []
    
    try:
        #   Get the requested node listType
        nodes = cpData.get("nodes", {}).get(listType, {})
        if not nodes:
            if listType in ["import2d", "import3d"]:
                logger.debug(f"No records exist in the {listType} database")
            else:
                logger.warning(f"ERROR: Node type '{listType}' not found in the database.")
            return []
        
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
        logger.warning(f"No nodes found with mediaId '{import_mediaId}' in type '{listType}'.")
        return []


#   Gets the database record for a given Identifier

def getDbRecordFromMediaId(comp, listType:str, mediaId:str) -> dict:
    cpData = loadPrismFileDb(comp)

    if not cpData:
        return None
    
    #   Get the requested node listType
    nodes = cpData.get("nodes", {}).get(listType, {})
    if not nodes:
        logger.warning(f"ERROR: Node type '{listType}' not found in the database.")
        return None
    
    #   Search for a node matching the given mediaId
    for uuid, node_data in nodes.items():
        if node_data.get("mediaId") == mediaId:
            exists = nodeExists(comp, uuid)
            if exists:
                return [uuid, exists, node_data]
                
    logger.warning(f"ERROR: No node found with mediaId '{mediaId}' in type '{listType}'.")
    return None


#   Updates the Node's Data in the DB

def updateNodeInfo(comp, listType:str, UUID:str, nodeData:dict) -> bool:
    cpData = loadPrismFileDb(comp)

    #   Remove the UID from the data since it is the main key
    nodeDataCopy = nodeData.copy()
    for key in ["nodeUID", "toolUID"]:
        if key in nodeDataCopy:
            del nodeDataCopy[key]

    try:
        #   Updates existing keys as needed
        if UUID in cpData["nodes"][listType]:
            cpData["nodes"][listType][UUID].update(nodeDataCopy)

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
        

#   Return a list of MediaIds for a given type

def getMediaIDsForType(comp, listType:str) -> list[str]:
    #   Get database data
    cpData = loadPrismFileDb(comp)

    mediaIDs = set()

    try:
        # Check if the listType exists in the comp
        if listType in cpData["nodes"]:
            # Loop through the UUIDs under the specified listType
            for uuid in cpData["nodes"][listType]:
                #   Get Media ID
                id = cpData["nodes"][listType][uuid]["mediaId"]
                mediaIDs.add(id)
        
            logger.debug("Constructed list of MediaID's")
            return sorted(mediaIDs)
    
    except Exception as e:
        logger.warning(f"ERROR: Unable to get list of MediaID's from database:\n{e}")


#   Return the Node Data for a given Node

def getNodeInfo(comp, listType:str, UUID:str) -> dict:
    cpData = loadPrismFileDb(comp)

    try:
        if UUID in cpData["nodes"][listType]:
            return cpData["nodes"][listType][UUID]
        else:
            logger.debug(f"The is no data for node: {UUID}")
            return False
    except:
        logger.warning("ERROR: Failed to read Node Data")
        return False


#   Returns list of import files based on selected tools

def getFilesFromSelTools(comp, importData:dict, selUIDs:list) -> list[str]:
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


#	Checks if a matching tool exists in the comp

def nodeExists(comp, nodeUID:str) -> bool:
    if getNodeByUID(comp, nodeUID):
        return True
    return False


#   Returns tool based on UID

def getNodeByUID(comp, nodeUID:str) -> Union[Tool, None]:
    try:
        #   Gets all tools
        tools = comp.GetToolList(False)

        for tool_name, tool in tools.items():
            toolUID = tool.GetData('Prism_UUID')

            if toolUID == nodeUID:
                return tool
            
        return None
    
    except:
        logger.warning(f"ERROR: Finding tool by UID failed.")
        return None


#   Returns tool name based on UID

def getNodeNameByUID(comp, nodeUID:str) -> Toolname:
    tool = getNodeByUID(comp, nodeUID)
    toolName = getNodeNameByTool(tool)

    return toolName


#   Returns tool name for tool

def getNodeNameByTool(tool:Tool) -> Toolname:
    try:
        toolName = tool.GetAttrs()["TOOLS_Name"]
        return toolName
    except:
        logger.warning(f"ERROR: Cannot get name for {tool}")
        return None
    

#   Returns tool's UID

def getNodeUidFromTool(tool) -> str:
    try:
        nodeUID = tool.GetData('Prism_UUID')
        return nodeUID
    except:
        logger.warning(f"ERROR: Cannot get UUID for {tool}")
        return None


#   Returns tool UID based on Identifier

def getNodeUidFromMediaId(comp, listType:str, mediaId:str) -> Union[str | list | None]:
    cpData = loadPrismFileDb(comp)

    matchingNodes = []

    try:
        #   Iterate through nodes of the given listType
        for uuid, nodeData in cpData["nodes"].get(listType, {}).items():
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

def getNodeUidFromMediaDisplayname(comp, listType:str, mediaId:str) -> Union[UUID | None]:
    cpData = loadPrismFileDb(comp)

    mediaIdUids = []

    try:
        # Iterate through nodes of the given listType
        for uuid, nodeData in cpData["nodes"].get(listType, {}).items():
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

def getConnectedNodes(comp, listType:str, UUID:str) -> Union[list | None]:
    cpData = loadPrismFileDb(comp)

    try:
        if UUID in cpData["nodes"][listType]:
            nodeData = cpData["nodes"][listType][UUID]
            if "connectedNodes" not in nodeData:
                return []
            
            else:
                connectedNodes = nodeData["connectedNodes"]

            #   If connected nodes is a dict with names
            if isinstance(connectedNodes, dict):
                connUIDs = []
                for name, uid in connectedNodes.items():
                    connUIDs.append(uid)

                return connUIDs
            #   If connected nodes is just a list of UIDs
            else:
                return connectedNodes

        else:
            logger.debug(f"{UUID} does not exist in the Comp Database")
            return None
    except:
        logger.warning(f"ERROR: Unable to get connected nodes for {UUID}")
        return None
    

#	Gets either single UID or List of UID's
#	and returns the original and all connected UUID's

def getAllConnectedNodes(comp, listType:str, nodeUIDs:Union[list|str]) -> list[Tool]:
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
            connectedNodes = getConnectedNodes(comp, listType, mainToolUID)
            for connNodeUID in connectedNodes:
                allToolUIDs.append(connNodeUID)
        
        logger.debug(f"Getting all connected nodes for {nodeUIDs}")
        return allToolUIDs   

    except:
        logger.warning("ERROR: Unable to get all connected nodes")
        return None 


# Checks if tool is set to pass-through mode

def isPassThrough(comp, nodeUID:str=None, node:str=None) -> bool:
    if nodeUID:
        node = getNodeByUID(comp, nodeUID)

    return node and node.GetAttrs({"TOOLS_Name"})["TOOLB_PassThrough"]


#	Sets the Fusion node's passthrough

def setPassThrough(comp, nodeUID:str=None, node:str=None, passThrough=False):
    if nodeUID:
        node = getNodeByUID(comp, nodeUID)
    node.SetAttrs({"TOOLB_PassThrough": passThrough})


#   Reloads the Loaders and sets the clip start/end/length

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



def sm_saveStates(comp, buf:str):
    try:
        comp.SetData("prismStates", buf + "_..._")
        logger.debug(f"Saved the state data to the comp.")
    except:
        logger.warning(f"ERROR: Unable to save State Data to comp: {comp}")



def sm_saveImports(comp, importPaths:str):
    prismdata = comp.GetData("prismStates")
    prismdata += importPaths.replace("\\\\", "\\")
    comp.SetData("prismStates", prismdata)



def sm_readStates(comp) -> str:
    try:
        prismdata = comp.GetData("prismStates")
        if not prismdata:
            logger.debug("Prism State Data does not exist.")
        else:
            return prismdata.split("_..._")[0]
    except:
        logger.warning(f"ERROR:  Unable to read State Data from comp: {comp}")
        logger.warning(f"ERROR:  Resetting Prism State Data")
        setDefaultState()


#	Gets called from SM to remove all States

def sm_deleteStates(comp):
    #	Sets the states datablock to empty default state
    setDefaultState()



def getImportPaths(comp) -> str:
    prismdata = comp.GetData("prismStates")
    return prismdata.split("_..._")[1]
