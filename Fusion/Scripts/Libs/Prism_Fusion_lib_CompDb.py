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
from typing import Union, Dict, Any
import logging

from PrismUtils.Decorators import err_catcher as err_catcher

logger = logging.getLogger(__name__)


### THIS IS A LIBRARY FOR THE PRISM DATABASE SAVED TO THE COMP  ###


#   LETS KEEP THIS STRUCTURE UPDATED WITH CHANGES

#   DataBase Structure:
#
#   Root(
#       "nodes"(
#           "import2d" (
#               UUID: {
#                   NodeData: {
#                        "nodeName": string
#                        "verion": string
#                        "filepath": string
#                        "format": string
#                        "mediaId": string
#                        "displayName": string
#                        "connectedNodes": list
#                        }
#                     }
#                  }
#           "import3d" (
#               UUID: {
#                   NodeData: {
#                        "nodeName": string
#                        "verion": string
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
#                        "verion": string
#                        "filepath": string
#                        "format": string
#                        }
#                     }
#                  }
#           "export3d" (
#               UUID: {
#                   NodeData: {
#                        "nodeName": string
#                        "verion": string
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
def savePrismFileDb(comp, cpData:dict):
    try:
        cpData_str =  json.dumps(cpData, indent=4)
        comp.SetData("PrismDB", cpData_str)
        logger.debug("Saved Prism Comp Database to Comp")
    except:
        logger.warning("ERROR: Failed to save Prism Comp Database to Comp")


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

    except:
        logger.warning("ERROR:  Failed to add the Node Data to the Comp Database")
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


#   Updates the Node's Data in the DB
@err_catcher(name=__name__)
def updateNodeInfo(comp, type:str, UUID:str, nodeData:dict) -> bool:
    cpData = loadPrismFileDb(comp)

    try:
        if UUID in cpData["nodes"][type]:
            cpData["nodes"][type][UUID].update(nodeData)
            logger.debug(f"Updated {nodeData['nodeName']} data.")
            savePrismFileDb(comp, cpData)
            return True
        else:
            logger.debug(f"The is no data for node: {UUID}")
            return False
    except:
        logger.warning("ERROR: Failed to update Node Data")
        return False
        

#   Return the Node Data for a given Node
@err_catcher(name=__name__)
def getNodeInfo(comp, type:str, UUID:str) -> bool:
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


#	Checks if a matching tool exists in the comp
@err_catcher(name=__name__)
def nodeExists(comp, nodeUID:str) -> bool:
    if getNodeByUID(comp, nodeUID):
        return True
    return False


@err_catcher(name=__name__)
def getNodeByUID(comp, nodeUID:str) -> Union[Tool, None]:
    try:
        # Iterate through all tools in the composition
        tools = comp.GetToolList(False)

        for tool_name, tool in tools.items():  # tool_name is the key, tool is the value
            toolUID = tool.GetData('Prism_UUID')

        # Check if the tool has the attribute 'Prism_UUID' and if it matches the provided UID
            if toolUID == nodeUID:
                return tool
            
        raise Exception
    
    except:
        logger.warning(f"ERROR: No node found for {nodeUID}")
        return None


@err_catcher(name=__name__)
def getNodeNameByUID(comp, nodeUID:str) -> Toolname:
    tool = getNodeByUID(comp, nodeUID)
    toolName = getNodeNameByTool(tool)

    return toolName


@err_catcher(name=__name__)
def getNodeNameByTool(tool:Tool) -> Toolname:
    try:
        toolName = tool.GetAttrs()["TOOLS_Name"]
        return toolName
    except:
        logger.warning(f"ERROR: Cannot get name for {tool}")
        return None
    

#   Return the Node Data for a given Node
@err_catcher(name=__name__)
def getNodeUidFromMediaId(comp, type:str, mediaId:str) -> Union[str | list | None]:
    cpData = loadPrismFileDb(comp)

    matchingNodes = []

    try:
        # Iterate through nodes of the given type
        for uuid, nodeData in cpData["nodes"].get(type, {}).items():
            if nodeData.get("mediaId") == mediaId:
                matchingNodes.append(uuid)
        
        # Return None if no matching mediaId is found
        if len(matchingNodes) == 0:
            return None
        
        #   Return Int if there is only one node
        elif len(matchingNodes) == 1:
            return matchingNodes[0]
        
        #   Return List if there are multiple
        else:
            return matchingNodes
    except:
        logger.warning("ERROR: Uanble to get UUID from Media Identifier.")
        return None
    

#   Return the Node Data for a given Node
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
        if isinstance(nodeUIDs, list):
            for uid in nodeUIDs:
                mainToolsUIDs.append(uid)
        else:
            mainToolsUIDs.append(nodeUIDs)

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


@err_catcher(name=__name__)
def getNodeType(tool:Tool) -> str:
    try:
        return tool.GetAttrs("TOOLS_RegID")
    except:
        logger.warning("ERROR: Cannot retrieve node type")
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
