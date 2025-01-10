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


##  THIS IS A LIBRARY FOR FUSION COMP FUNCTIONS FOR THE FUSION PRISM PLUGIN  ##
	

import os
import re
from typing import Union, Dict, Tuple, Any
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


#	Returns the filename of the current comp
@err_catcher(name=__name__)
def getCurrentFileName(comp, origin=None, path=True) -> str:
    try:
        if comp is None:
            currentFileName = ""
        else:
            currentFileName = comp.GetAttrs()["COMPS_FileName"]

        return currentFileName
    
    except Exception as e:
        logger.warning(f"ERROR: Failed to get current filename:\n{e}")


@err_catcher(name=__name__)
def openScene(fusion, sceneFormats:list, filepath:str, force=False) -> bool:
    if os.path.splitext(filepath)[1] not in sceneFormats:
        return False

    try:
        fusion.LoadComp(filepath)
        logger.debug(f"Loaded scenefile: {filepath}")
    except:
        logger.warning("ERROR: Failed to load Comp")

    return True


@err_catcher(name=__name__)
def saveScene(comp, filepath:str, details={}) -> bool:
    try:
        #Save function returns True on success, False on failure
        result = comp.Save(filepath)
        if result:
            logger.debug(f"Saved file to {filepath}")
            return True
        else:
            raise Exception
    except:
        logger.warning(f"ERROR: Failed to save {filepath}")
        return False
    

@err_catcher(name=__name__)
def getFrameRange(comp) -> Tuple[int, int]:
    try:
        startframe = comp.GetAttrs()["COMPN_GlobalStart"]
        endframe = comp.GetAttrs()["COMPN_GlobalEnd"]
        return [startframe, endframe]
    except:
        logger.warning("ERROR: Failed to get current frame range")
        return [None, None]
    

#	Sets the supplied framerange to the comp
@err_catcher(name=__name__)
def setFrameRange(comp, startFrame:int, endFrame:int):
    try:
        comp.SetAttrs(
            {
                "COMPN_GlobalStart": startFrame,
                "COMPN_RenderStart": startFrame,
                "COMPN_GlobalEnd": endFrame,
                "COMPN_RenderEnd": endFrame
            }
        )
        comp.SetPrefs(
            {
                "Comp.Unsorted.GlobalStart": startFrame,
                "Comp.Unsorted.GlobalEnd": endFrame,
            }
        )
    except Exception as e:
        logger.warning(f"ERROR: Could not set framerange in the comp:\n{e}")



@err_catcher(name=__name__)
def getRenderRange(comp) -> Tuple[int, int]:
    try:
        startframe = comp.GetAttrs()["COMPN_RenderStart"]
        endframe = comp.GetAttrs()["COMPN_RenderEnd"]
        return [startframe, endframe]
    except:
        logger.warning("ERROR: Failed to get current render range")
        return [None, None]
    

#	Sets the supplied framerange to the comp
@err_catcher(name=__name__)
def setRenderRange(comp, startFrame:int, endFrame:int):
    try:
        comp.SetAttrs(
            {
                "COMPN_RenderStart": startFrame,
                "COMPN_RenderEnd": endFrame
            }
        )

    except Exception as e:
        logger.warning(f"ERROR: Could not set framerange in the comp:\n{e}")



@err_catcher(name=__name__)
def getFPS(comp) -> float:
    try:
        return comp.GetPrefs()["Comp"]["FrameFormat"]["Rate"]
    except Exception as e:
        logger.warning(f"ERROR: Failed to get the fps from comp:\n{e}")
        return None
    


@err_catcher(name=__name__)
def setFPS(comp, fps:float):
    try:
        return comp.SetPrefs({"Comp.FrameFormat.Rate": fps})
    except:
        logger.warning(f"ERROR: Failed to set the fps to the comp")



@err_catcher(name=__name__)
def getResolution(comp) -> Tuple[int, int]:
    try:
        width = comp.GetPrefs()[
            "Comp"]["FrameFormat"]["Width"]
        height = comp.GetPrefs()[
            "Comp"]["FrameFormat"]["Height"]
        
        return [width, height]
    
    except Exception as e:
        logger.warning(f"ERROR: Failed to get the current resolution from the comp:\n{e}")
        return [None, None]
    

@err_catcher(name=__name__)
def setResolution(comp, width:int=None, height:int=None):
    try:
        comp.SetPrefs(
            {
                "Comp.FrameFormat.Width": width,
                "Comp.FrameFormat.Height": height,
            }
        )
    except Exception as e:
        logger.warning(f"ERROR: Failed to set the resolution to the comp:\n{e}")


@err_catcher(name=__name__)
def getCurrentFrame(comp) -> int:
    try:
        return comp.CurrentTime
    
    except:
        logger.warning(f"ERROR: Failed to get current frame from Comp")
        return None


#   Adds tool of specified type and configures given data
@err_catcher(name=__name__)
def addTool(comp, toolType:str, toolData:dict={}, xPos:int=-32768, yPos:int=-32768, autoConnect=1) -> Tool:
    try:
        tool = comp.AddTool(toolType, xPos, yPos, autoConnect)

        if "toolName" in toolData:
            tool.SetAttrs({'TOOLS_Name' : toolData['toolName']})
        if "nodeName" in toolData:
            tool.SetAttrs({'TOOLS_Name' : toolData['nodeName']})

        if "groupName" in toolData:
            tool.SetData('Prism_Group', toolData['groupName'])

        if "toolUID" in toolData:
            tool.SetData('Prism_UUID', toolData['toolUID'])
        if "nodeUID" in toolData:
            tool.SetData('Prism_UUID', toolData['nodeUID'])

        if "mediaId" in toolData:
            tool.SetData('Prism_MediaID', toolData['mediaId'])

        if "product" in toolData:
            tool.SetData('Prism_Product', toolData['product'])

        if "format" in toolData:
            tool.SetData('Format', toolData['format'])

        if "aov" in toolData:
            tool.SetData('Prism_AOV', toolData['aov'])

        if "channel" in toolData:
            tool.SetData('Prism_Channel', toolData['channel'])

        if "shaderName" in toolData:
            tool.SetData('Prism_Shader', toolData['shaderName'])

        if "shaderType" in toolData:
            tool.SetData('Prism_ShaderType', toolData['shaderType'])

        if "texMap" in toolData:
            tool.SetData('Prism_TexMap', toolData['texMap'])
 
        if "version" in toolData:
            tool.SetData('Prism_Version', toolData['version'])

        if "mediaType" in toolData:
            tool.SetData('Prism_MediaType', toolData['mediaType'])

        if "connectedNodes" in toolData:
            tool.SetData('Prism_ConnectedNodes', toolData['connectedNodes'])

        if "filepath" in toolData:
            tool.Clip = toolData['filepath']

        if "usdFilepath" in toolData:
            tool["Filename"] = toolData['usdFilepath']

        if "uTexFilepath" in toolData:
            tool["Filename"] = toolData['uTexFilepath']

        if "matXfilePath" in toolData:
            tool["MaterialFile"] = toolData["matXfilePath"]

        if "3dFilepath" in toolData:
            if toolData["format"] == ".fbx":
                tool["ImportFile"] = toolData['3dFilepath']
            elif toolData["format"] == ".abc":
                tool["Filename"] = toolData['3dFilepath']

        if "fuseFormat" in toolData:
            tool["OutputFormat"] = toolData['fuseFormat']

        if "frame_start" in toolData:
            tool.GlobalIn[0] = toolData["frame_start"]
            tool.GlobalOut[0] = toolData["frame_end"]

            tool.ClipTimeStart = 0
            tool.ClipTimeEnd = toolData["frame_end"] - toolData["frame_start"]
            tool.HoldLastFrame = 0


        #   TODO    TRYING TO HAVE TOOL SHOW NAME NOT CLIP PATH
        # tool.SetAttrs({'TOOLS_NameSet': True})

        return tool
    
    except:
        logger.warning(f"ERROR: Failed to add {toolType} to Comp")
        return None
    

#   Updates tool config for given data
@err_catcher(name=__name__)
def updateTool(tool:Tool, toolData:dict, xPos:int=-32768, yPos:int=-32768, autoConnect=1) -> Tool:
    try:
        if "toolName" in toolData:
            tool.SetAttrs({'TOOLS_Name' : toolData['toolName']})
        if "nodeName" in toolData:
            tool.SetAttrs({'TOOLS_Name' : toolData['nodeName']})

        if "groupName" in toolData:
            tool.SetData('Prism_Group', toolData['groupName'])

        if "version" in toolData:
            tool.SetData('Prism_Version', toolData['version'])

        if "connectedNodes" in toolData:
            tool.SetData('Prism_ConnectedNodes', toolData['connectedNodes'])

        if "filepath" in toolData:
            tool.Clip = toolData['filepath']

        if "usdFilepath" in toolData:
            tool["Filename"] = toolData['usdFilepath']

        if "matXfilePath" in toolData:
            tool["MaterialFile"] = toolData["matXfilePath"]

        if "3dFilepath" in toolData:
            if toolData["format"] == ".fbx":
                tool["ImportFile"] = toolData['3dFilepath']
            elif toolData["format"] == ".abc":
                tool["Filename"] = toolData['3dFilepath']

        if "frame_start" in toolData:
            tool.GlobalIn[0] = toolData["frame_start"]
            tool.GlobalOut[0] = toolData["frame_end"]

            tool.ClipTimeStart = 0
            tool.ClipTimeEnd = toolData["frame_end"] - toolData["frame_start"]
            tool.HoldLastFrame = 0


        #   TODO    TRYING TO HAVE TOOL SHOW NAME NOT CLIP PATH
        # tool.SetAttrs({'TOOLS_NameSet': True})

        return tool
    
    except:
        logger.warning(f"ERROR: Failed to update {tool} in Comp")
        return None


#   Returns Prism Data contained in Tool
@err_catcher(name=__name__)
def getToolData(tool:Tool) -> dict:
    try:
        #   Get all the tool data
        allData = tool.GetData()

        # Extract only the keys starting with "Prism"
        prismKeys = {key: value for key, value in allData.items() if str(value).startswith("Prism")}

        prismData = {}

        #   Get key value pairs
        for key, value in prismKeys.items():
            data = tool.GetData(value)
            #   Add to dict
            prismData[value] = data

        return prismData

    except Exception as e:
        logger.warning(f"ERROR: Unable to get tool data from: {tool}\n{e}")
        return {}
    

#   Creates a group with given tools and returns the Group UID and new UIDs.
@err_catcher(name=__name__)
def groupTools(comp,
               origin,
               groupName:str,
               toolList:list,
               outputTool:Tool = None,
               inputTool:Tool = None,
               pos=None
               ) -> tuple[UUID, list[UUID]]:
    
    success = False
    toolUIDs = []
    toolsToCopy = dict()
    iOconnections = []

    try:
        for tool in toolList:
            #   Add UUID to list
            uid = getToolData(tool)["Prism_UUID"]
            toolUIDs.append(uid)

            #   Copys the settings code
            toolSettings = comp.CopySettings(tool)

            #   Gets the output socket object
            outputSocket = getToolOutputSocket(tool)

            inputNames = []
            #   Gets list of connected tools' input socket objects
            inputs = getInputsFromOutput(tool)
            
            for input in inputs:
                #   Get the tool of the socket and get its name
                parentTool = input.GetTool()
                parentToolName = parentTool.Name
                #   Gets the name of the input socket
                inputName = input.Name
                #   Makes a dict with the input names
                inputDict = {"inputToolName": parentToolName,
                             "inputName": inputName}

                #   Adds the input dict to the list
                inputNames.append(inputDict)

            #   Makes tool I/O dict
            toolIo = {"toolName": tool.Name,
                      "output": outputSocket.Name,
                      "inputs": inputNames}
            
            #   Adds it to the list
            iOconnections.append(toolIo)

            # Add the tool's settings to the all_tools dictionary
            toolsToCopy.update(toolSettings["Tools"])

        success = True
    
    except Exception as e:
        logger.warning(f"ERROR: Unable to copy tool settings:\n{e}")
        return False

    if success:
        #   Deletes the original tools
        for tool in toolList:
            tool.Delete()

    try:
        #   Create group settings code
        gt = {"Tools": {groupName: {"__ctor": "GroupOperator" }}}

        gt["Tools"][groupName]["ViewInfo"] = dict(__ctor="GroupInfo")
        gt["Tools"][groupName]["Inputs"] = dict()
        gt["Tools"][groupName]["Outputs"] = dict()

        #   Add the list of tools settings to the group
        gt["Tools"][groupName]["Tools"] = toolsToCopy

        #   Add an external input using the inputTool
        if inputTool:
            gt["Tools"][groupName]["Inputs"]["Input1"] = dict(
                __ctor="InstanceInput", SourceOp=inputTool.Name, Source="Input"
            )

        #   Add an external output using the outputTool
        if outputTool:
            gt["Tools"][groupName]["Outputs"]["Output1"] = dict(
                __ctor="InstanceOutput", SourceOp=outputTool.Name, Source="Output"
            )

        #   Paste the group settings code into the composition
        comp.Paste(gt)

        #   Reconnect the tools
        for toolDict in iOconnections:
            #   Get the pasted tool from the saved Tool Name
            tool = comp.FindTool(toolDict["toolName"])
            #   Get the new output socket object
            output = getToolOutputSocket(tool)

            #   Itterate throught the input list since there can be multiple tools connected
            for inputDict in toolDict["inputs"]:
                #   Get the pasted tool from the saved Tool Name
                inputTool = getToolByName(comp, inputDict["inputToolName"])
                #   Get the input socket object by matching saved name
                input = getMatchingInputSocket(inputTool, inputDict["inputName"])

                #   Connect the two tools via their sockets
                result = connectInputToOutput(input, output)

        if result:
            #   Add UUID to Group Tool
            groupUID = origin.createUUID()
            groupTool = getToolByName(comp, groupName)
            groupTool.SetData('Prism_UUID', groupUID)

            #   Sets Group Tool Position if passed
            if pos:
                flow = comp.CurrentFrame.FlowView
                setToolPosition(flow, groupTool, pos[0], pos[1])

            return groupUID, toolUIDs
        

    except Exception as e:
        logger.warning(f"ERROR: Failed to create group:\n{e}")
        return None


#   Returns tool that matches name
@err_catcher(name=__name__)
def getToolByName(comp, toolName:str) -> Tool:
    try:
        for tool in comp.GetToolList(False).values():
            if tool.Name == toolName:
                return tool
        logger.warning(f"ERROR: No tool found with the name: {toolName}")
        return None
    
    except Exception as e:
        logger.warning(f"ERROR: Uanble to match {toolName}:\n{e}")
        return None


#   Returns type of tool
@err_catcher(name=__name__)
def getToolType(tool:Tool) -> str:
    try:
        return tool.GetAttrs("TOOLS_RegID")
    except:
        logger.warning("ERROR: Cannot Retrieve Tool type")
        return None


#   Returns all tools of specified type
@err_catcher(name=__name__)
def getAllToolsByType(comp, toolType:str) -> list[Tool]:
    try:
        toolList = []
        for tool in comp.GetToolList(False).values():
            if getToolType(tool) == toolType:
                toolList.append(tool)

        return toolList
    except:
        logger.warning(f"ERROR: Unable to get all {toolType} tools from the Comp")
        return None
    

#   Returns tools selected in Comp with optional Tool Type
@err_catcher(name=__name__)
def getSelectedTools(comp, toolType:str=None) -> list[Tool]:
    try:
        toolList = []
        for tool in comp.GetToolList(True).values():
            if toolType:
                if getToolType(tool) == toolType:
                    toolList.append(tool)
            else:
                toolList.append(tool)

        return toolList
    
    except:
        logger.warning(f"ERROR: Unable to get all {toolType} tools from the Comp")
        return None


#   Tries to find last tool in the flow
@err_catcher(name=__name__)
def getLastTool(comp) -> Tool | None:
    try:
        for tool in comp.GetToolList(False).values():
            if not hasConnectedOutputs(tool):
                return tool
        return None
    except:
        return None
        
    
#   Finds if tool has any outputs connected
@err_catcher(name=__name__)
def hasConnectedOutputs(tool) -> bool:
    if not tool:
        return False

    outputList = tool.GetOutputList()
    for output in outputList.values():
        if output is not None and hasattr(output, 'GetConnectedInput'):
            # Check if the output has any connected inputs in other tools
            try:
                connection = output.GetConnectedInputs()
                if connection != {}:
                    return True
            except:
                return False

    return False    


#   Finds if tool has an input connected
@err_catcher(name=__name__)
def hasConnectedInput(tool) -> bool:
    if not tool:
        return False

    try:
        if tool.Input.GetConnectedOutput():
            logger.debug(f"{tool} has a connected input")
            return True
        else:
            logger.debug(f"{tool} has no connected input")
            return False
    except:
        logger.warning(f"ERROR: Unable to check inputs for {tool}")
        return False    


#   Connects two tools
@err_catcher(name=__name__)
def connectTools(toolFrom:Tool, toolTo:Tool) -> bool:
    try:
        #   Connect MainOutput to 1st MainInput (works for most situations)
        toolTo.FindMainInput(1).ConnectTo(toolFrom)
        return True
    
    except:
        logger.warning(f"ERROR: Could not connect {toolFrom} into {toolTo}")
        return False


#   Takes Fusion input and output objects and makes connection
@err_catcher(name=__name__)
def connectInputToOutput(input:ToolOption, output:ToolOption) -> bool:
    try:
        #   Connects input socket object to output socket object
        input.ConnectTo(output)
        return True
    
    except Exception as e:
        logger.warning(f"ERROR: Unable to make connections:\n{e}")
        return False


#   Returns output socket object
@err_catcher(name=__name__)
def getToolOutputSocket(tool) -> ToolOption:
    try:
        return tool.FindMainOutput(1)
    except:
        logger.warning(f"ERROR: Could not get tool output for {tool}")
        return None
    

#   Returns list of input sockets that are connected to the tool's output
@err_catcher(name=__name__)
def getInputsFromOutput(tool) -> list[ToolOption]:
    try:
        #   Gets the Fusion table of inputs
        inputsDict = tool.FindMainOutput(1).GetConnectedInputs()
        inputsList = []
        #   Itterates over ther table and extracts the objects
        for inputIdx, inputTool in inputsDict.items():
            if inputTool:
                inputsList.append(inputTool)
        
        return inputsList

    except:
        logger.warning(f"ERROR: Could not get tool's connected inputs to output for {tool}")
        return None


#   Returns matching input socket from Input name
@err_catcher(name=__name__)
def getMatchingInputSocket(tool, inputName:str) -> ToolOption:
    try:
        #   Gets the Fusion table of inputs
        inputs = tool.GetInputList()

        #   Itterates over ther table and extracts the objects
        for inputIdx, inputTool in inputs.items():
            if inputTool:
                #   Return input object if it matches the name
                if inputTool.Name == inputName:
                    return inputTool
                
        #   If no match
        logger.warning(f"ERROR: Unable to find matching input socket: {inputName}")
        return None
    except Exception as e:
        logger.warning(f"ERROR: Failed to match input socket {inputName}:\n{e}")
        return None


#   Finds if tool has an input connected
@err_catcher(name=__name__)
def getToolBefore(tool) -> Tool:
    try:
        return tool.FindMainInput(1).GetConnectedOutput()
    except:
        logger.warning(f"ERROR: Could not get the tool connected to {tool}")
        return None


#	Sets up the name based on avail data
@err_catcher(name=__name__)
def makeLdrName(importData:dict) -> str:
    try:
        ldrName = importData.get('identifier') or importData.get("mediaId")

        if "aov" in importData:
            ldrName = ldrName + f"_{importData['aov']}"

        if "channel" in importData:
            ldrName = ldrName + f"_{importData['channel']}"
   
        ldrName = ldrName + f"_{importData['version']}"
        
        return ldrName
    
    except Exception as e:
        logger.warning(f"ERROR: Unable to make Loader name from Import Data:\n{e}")
        return None
    

#	Sets up the name based on avail data
@err_catcher(name=__name__)
def makeWirelessName(importData:dict) -> str:
    try:
        wirelessName = (importData.get('identifier')
                        or importData.get("mediaId")
                        or importData.get("Prism_MediaID"))

        if "aov" in importData:
            wirelessName = wirelessName + f"_{importData['aov']}"
        elif "Prism_AOV" in importData:
            wirelessName = wirelessName + f"_{importData['Prism_AOV']}"

        if "channel" in importData:
            wirelessName = wirelessName + f"_{importData['channel']}"
        elif "Prism_Channel" in importData:
            wirelessName = wirelessName + f"_{importData['Prism_Channel']}"

        return wirelessName
    
    except Exception as e:
        logger.warning(f"ERROR: Unable to make Wireless base name from Import Data:\n{e}")
        return None
    

#   The name of this function comes for its initial use to position
#   the "state manager node" that what used before using SetData.
@err_catcher(name=__name__)
def setToolPosition(comp, node, find_min=True, x_offset=-2, y_offset=0, ignore_node_type:str=None, refNode:Tool=None):
    # Get the active composition
    flow = comp.CurrentFrame.FlowView

    if not comp:
        # No active composition
        return

    # Get all nodes in the composition
    all_nodes = comp.GetToolList(False).values()

    if not all_nodes:
        flow.SetPos(node, 0, 0)
        return

    # xmost_node, thresh_x_position, thresh_y_position = self.find_extreme_position(node, ignore_node_type, find_min)

    # if xmost_node:
    if refNode:
        thresh_x_position, thresh_y_position = postable = flow.GetPosTable(refNode).values()
        setToolPosition(flow, node, thresh_x_position + x_offset, thresh_y_position + y_offset)
    else:
        flow.Select()
        x,y = find_LastClickPosition(comp)
        flow.SetPos(node, x, y)


#   Returns Position of Tool
@err_catcher(name=__name__)
def getToolPosition(comp, tool:Tool) -> Tuple[float, float]:
    flow = comp.CurrentFrame.FlowView
    try:
        return list(flow.GetPosTable(tool).values())
    except:
        logger.warning(f"ERROR: Unable to get position of {tool}.")
        return 0, 0


#   Set Tool Position in Comp
@err_catcher(name=__name__)
def setToolPosition(flow, tool:Tool, x:float, y:float):
    try:
        flow.SetPos(tool, x, y)
    except:
        logger.warning(f"ERROR: Unable to set position of {tool}")


#   Sets Tool Position Relative to Another Tool
@err_catcher(name=__name__)
def setToolPosRelative(comp, tool, refTool, x_offset:float=1, y_offset:float=0):
    try:
        flow = comp.CurrentFrame.FlowView

        #   Get Position of Ref Tool
        x, y = getToolPosition(comp, refTool)

        #   Set Tool Position with Offset
        setToolPosition(flow, tool, x + x_offset, y + y_offset)
    except:
        logger.warning(f"ERROR: Unable to set {tool} position relative to {refTool}")


#   Set Tool Position Depending on Type
@err_catcher(name=__name__)
def setToolToLeft(comp, tool, refNode=None, x_offset:float=0, y_offset:float=1):
    try:
        if refNode:
            #   Checks if it is a Loader from Prism
            if getToolType(refNode) == "Loader" and getToolData(refNode) != {}:
                #   Set Under other Loaders
                setToolPosRelative(comp, tool, refNode, x_offset = 0, y_offset = 1)
            else:
                #   Set to the Left of Flow
                setToolPosRelative(comp, tool, refNode, x_offset = -8, y_offset = 0)
        else:
            #   Just put in position
            setToolPosition(comp, tool, x_offset = 0, y_offset = 0)
    except:
        logger.warning(f"ERROR: Unable to set {tool} to the left")


#   Checks if Tool is within a Threshold Distance of Another Tool OR Position
@err_catcher(name=__name__)
def isToolNearTool(comp, tool, refTool:Tool=None, refPos:Tuple[float, float]=None, thresh:float=3) -> bool:
    flow = comp.CurrentFrame.FlowView

    try:
        #   If given a ref Tool, get its position
        if refTool:
            refPos = getToolPosition(comp, refTool)

        #   Make sure the position is a dict for Fusion
        if not isinstance(refPos, list):
            logger.warning("ERROR: Unable to check tool proximity, incorrect reference position.")
            return True
        
        #   Get position of Tool
        toolPos = getToolPosition(comp, tool)

        #   Calculate distances
        distX = abs(toolPos[0] - refPos[0])
        distY = abs(toolPos[1] - refPos[1])

        #   If both X and Y are within Threshold
        if distX <= thresh and distY <= thresh:
            return True
        else:
            return False
    except:
        logger.warning("ERROR: Unable to check tool proximity.")
        return True


@err_catcher(name=__name__)
def matchToolPos(comp, nodeTomove:Tool, nodeInPos:Tool):
    flow = comp.CurrentFrame.FlowView
    x,y = getToolPosition(comp, nodeInPos)
    setToolPosition(flow, nodeTomove, x, y)


#Get last click on comp view.
@err_catcher(name=__name__)
def find_LastClickPosition(comp) -> Tuple[int, int]:
    flow = comp.CurrentFrame.FlowView
    posNode = comp.AddToolAction("Background")
    x,y = getToolPosition(comp, posNode)
    posNode.Delete()

    return x,y
    # return -32768, -32768


@err_catcher(name=__name__)
def posRelativeToTool(comp, tool, xoffset:float=3) -> bool:
    flow = comp.CurrentFrame.FlowView
    #check if there is selection
    if len(comp.GetToolList(True).values()) > 0:
        try:
            activeNode = comp.ActiveTool()
        except:
            activeNode = comp.GetToolList(True)[1]
        if not activeNode.Name == tool.Name:
            postable = flow.GetPosTable(activeNode)
            if postable:
                x, y = postable.values()
                flow.SetPos(tool, x + xoffset, y)
                try:
                    tool.ConnectInput('Input', activeNode)
                except:
                    pass
                return True

    return False


# Arranges nodes in a vertical stack
@err_catcher(name=__name__)
def stackToolsByList(comp, toolList: list[Tool], xoffset:float=0, yoffset:float=1):
    flow = comp.CurrentFrame.FlowView

    # Ensure there is at least one tool to stack
    if not toolList:
        return

    # Initialize variables to calculate the average position
    totalX, totalY = 0, 0

    # Get the position of the first tool
    refNode = toolList[0]
    refPos = flow.GetPosTable(refNode)
    x, y = refPos.values()

    # Iterate through the tools and set their positions
    for i, tool in enumerate(toolList):
        # Get the new Y position based on the offset
        if i == 0:  # The first tool doesn't move
            newX = x
            newY = y
        else:
            # For each other tools, stack vertically
            newX = x + xoffset
            newY = y + i * yoffset

        # Set the new position for each tool
        flow.SetPos(tool, newX, newY)

        # Add the position to the total
        totalX += newX
        totalY += newY

    # Calculate the average position
    avgX = totalX / len(toolList)
    avgY = totalY / len(toolList)

    return avgX, avgY


#	Arranges nodes in a vertcal stack
@err_catcher(name=__name__)
def stackToolsByType(comp, nodetostack:Tool, yoffset:float=3, tooltype:str="Saver"):
    flow = comp.CurrentFrame.FlowView

    origx, origy = flow.GetPosTable(nodetostack).values()

    toollist = comp.GetToolList().values()
    
    thresh_y_position = -float('inf')
    upmost_node = None		

    # Find the upmost node
    for node in toollist:
        try:
            if node.Name == nodetostack.Name:
                    continue
            
            if node.GetAttrs("TOOLS_RegID") == tooltype:
                postable = flow.GetPosTable(node)
                y = thresh_y_position
                #check if node has a postable.
                if postable:
                    # Get the node's position
                    x,y = postable.values()

                    if y > thresh_y_position:
                        thresh_y_position = y
                        upmost_node = node
        except Exception as e:
            logger.warning(f"ERROR: Unable to stack nodes:\n{e}")

    if upmost_node:
        #set pos to the leftmost or rightmost node
        flow.SetPos(nodetostack, origx, thresh_y_position + yoffset)


@err_catcher(name=__name__)
def findLeftmostLowerTool(comp, threshold:float=0.5) -> Tool:
    flow = comp.CurrentFrame.FlowView

    try:
        nodes = [t for t in comp.GetToolList(False).values() if flow.GetPosTable(t) and not t.GetAttrs('TOOLS_RegID')=='Underlay']
        if len(nodes) == 0:
            return None

        leftmost = min(nodes, key=lambda p: flow.GetPosTable(p)[1])
        downmost = max(nodes, key=lambda p: flow.GetPosTable(p)[2])

        if abs(flow.GetPosTable(downmost)[1] - flow.GetPosTable(leftmost)[1]) <= threshold:
            return downmost
        else:
            return leftmost
    except:
        logger.warning("ERROR: Failed to find leftmost lower node")
        return None


@err_catcher(name=__name__)
def getLoaderChannels(tool) -> list[str]:
    # Get all loader channels and filter out the ones to skip
    skip = {			
        "SomethingThatWontMatchHopefully".lower(),
        "r", 
        "red", 
        "g", 
        "green", 
        "b", 
        "blue", 
        "a", 
        "alpha",
        "rgb","rgb.r","rgb.g","rgb.b","rgb.a", # Mantra channels
    }
    sourceChannels = tool.Clip1.OpenEXRFormat.RedName.GetAttrs("INPIDT_ComboControl_ID")
    allChannels = []
    for channelName in sourceChannels.values():
        if channelName.lower() not in skip:
            allChannels.append(channelName)

    # Sort the channel list
    sortedChannels = sorted(allChannels)

    return sortedChannels


@err_catcher(name=__name__)
def getChannelData(loaderChannels:list) -> dict:
    try:
        channelData = {}

        for channelName in loaderChannels:
            # Get prefix and channel from full channel name using regex
            match = re.match(r"(.+)\.(.+)", channelName)
            if match:
                prefix, channel = match.groups()

                # Use setdefault to initialize channels if prefix is encountered for the first time
                channels = channelData.setdefault(prefix, [])

                # Add full channel name to assigned channels of current prefix
                channels.append(channelName)

        return channelData
    
    except:
        logger.warning("ERROR: Failed to get channel data")
        return None
    

