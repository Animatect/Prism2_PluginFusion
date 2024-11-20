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
def getFrameRange(comp) -> list[int, int]:
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
    comp.Lock()
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

    comp.Unlock()


@err_catcher(name=__name__)
def getRenderRange(comp) -> list[int, int]:
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
    comp.Lock()

    try:
        comp.SetAttrs(
            {
                "COMPN_RenderStart": startFrame,
                "COMPN_RenderEnd": endFrame
            }
        )

    except Exception as e:
        logger.warning(f"ERROR: Could not set framerange in the comp:\n{e}")

    comp.Unlock()


@err_catcher(name=__name__)
def getFPS(comp) -> int:
    try:
        return comp.GetPrefs()["Comp"]["FrameFormat"]["Rate"]
    except Exception as e:
        logger.warning(f"ERROR: Failed to get the fps from comp:\n{e}")
        return None
    


@err_catcher(name=__name__)
def setFPS(comp, fps:int):
    try:
        return comp.SetPrefs({"Comp.FrameFormat.Rate": fps})
    except:
        logger.warning(f"ERROR: Failed to set the fps to the comp")



@err_catcher(name=__name__)
def getResolution(comp) -> list[int, int]:
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


@err_catcher(name=__name__)
def addTool(comp, toolType:str, toolData:dict={}, xPos=-32768, yPos=-32768, autoConnect=1) -> Tool:
    try:
        tool = comp.AddTool(toolType, xPos, yPos, autoConnect)

        if "toolName" in toolData:
            tool.SetAttrs({'TOOLS_Name' : toolData['toolName']})
        if "nodeName" in toolData:
            tool.SetAttrs({'TOOLS_Name' : toolData['nodeName']})

        if "toolUID" in toolData:
            tool.SetData('Prism_UUID', toolData['toolUID'])
        if "nodeUID" in toolData:
            tool.SetData('Prism_UUID', toolData['nodeUID'])

        if "filepath" in toolData:
            tool.Clip = toolData['filepath']

        if "fuseFormat" in toolData:
            tool["OutputFormat"] = toolData['fuseFormat']

        return tool
    
    except:
        logger.warning(f"ERROR: Failed to add {toolType} to Comp")
        return None
    

@err_catcher(name=__name__)
def updateTool(tool:Tool, toolData:dict, xPos=-32768, yPos=-32768, autoConnect=1) -> Tool:
    try:
        if "toolName" in toolData:
            tool.SetAttrs({'TOOLS_Name' : toolData['toolName']})
        if "nodeName" in toolData:
            tool.SetAttrs({'TOOLS_Name' : toolData['nodeName']})

        if "toolUID" in toolData:
            tool.SetData('Prism_UUID', toolData['toolUID'])

        if "filepath" in toolData:
            tool.Clip = toolData['filepath']

        if "fuseFormat" in toolData:
            tool["OutputFormat"] = toolData['fuseFormat']

        logger.debug(f"Updated tool: {tool}")

        return tool
    
    except:
        logger.warning(f"ERROR: Failed to update {tool} in Comp")
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


#   Finds if tool has an input connected
@err_catcher(name=__name__)
def connectTools(toolFrom, toolTo):
    try:
        toolTo.FindMainInput(1).ConnectTo(toolFrom)
    except:
        logger.warning(f"ERROR: Could not connect {toolFrom} into {toolTo}")


#   Finds if tool has an input connected
@err_catcher(name=__name__)
def getToolOutput(tool) -> ToolOption:
    try:
        return tool.FindMainOutput(1)
    except:
        logger.warning(f"ERROR: Could not get tool output for {tool}")
        return None


#   Finds if tool has an input connected
@err_catcher(name=__name__)
def getToolBefore(tool) -> Tool:
    try:
        return tool.FindMainInput(1).GetConnectedOutput()
    except:
        logger.warning(f"ERROR: Could not get the tool connected to {tool}")
        return None



#   The name of this function comes for its initial use to position
#   the "state manager node" that what used before using SetData.
@err_catcher(name=__name__)
def setNodePosition(comp, node, find_min=True, x_offset=-2, y_offset=0, ignore_node_type:str=None, refNode:Tool=None):
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
        set_node_position(flow, node, thresh_x_position + x_offset, thresh_y_position + y_offset)
    else:
        flow.Select()
        x,y = find_LastClickPosition(comp)
        flow.SetPos(node, x, y)


@err_catcher(name=__name__)
def set_node_position(flow, smnode:Tool, x:int, y:int):
    flow.SetPos(smnode, x, y)


@err_catcher(name=__name__)
def matchNodePos(comp, nodeTomove:Tool, nodeInPos:Tool):
    flow = comp.CurrentFrame.FlowView
    x,y = flow.GetPosTable(nodeInPos).values()
    set_node_position(flow, nodeTomove, x, y)


#Get last click on comp view.
@err_catcher(name=__name__)
def find_LastClickPosition(comp) -> list[int, int]:
    flow = comp.CurrentFrame.FlowView
    posNode = comp.AddToolAction("Background")
    x,y = flow.GetPosTable(posNode).values()
    posNode.Delete()

    return x,y
    # return -32768, -32768


@err_catcher(name=__name__)
def posRelativeToNode(comp, node, xoffset=3) -> bool:
    flow = comp.CurrentFrame.FlowView
    #check if there is selection
    if len(comp.GetToolList(True).values()) > 0:
        try:
            activeNode = comp.ActiveTool()
        except:
            activeNode = comp.GetToolList(True)[1]
        if not activeNode.Name == node.Name:
            postable = flow.GetPosTable(activeNode)
            if postable:
                x, y = postable.values()
                flow.SetPos(node, x + xoffset, y)
                try:
                    node.ConnectInput('Input', activeNode)
                except:
                    pass
                return True

    return False


#	Arranges nodes in a vertcal stack
@err_catcher(name=__name__)
def stackNodesByType(comp, nodetostack:Tool, yoffset=3, tooltype:str="Saver"):
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


# @err_catcher(name=__name__)                           #   USED???
# def find_extreme_loader(comp):
#     flow = comp.CurrentFrame.FlowView()

#     # Initialize variables to track the leftmost lower Loader node
#     leftmost_lower_loader = None
#     min_x = -float('inf')
#     min_y = float('inf')

#     # Iterate through all tools in the composition
#     for tool in comp.GetToolList().values():
#         # Check if the tool is of type "Loader"
#         if tool.GetAttrs()['TOOLS_RegID'] == 'Loader':
#             # Get the position of the Loader node
#             position = flow.GetPosTable(tool)
            
#             if position:
#                 x, y = position[1], position[2]
#                 # Check if this Loader node is the leftmost lower node
#                 if (y < min_y) or (y == min_y and x < min_x):
#                     min_x = x
#                     min_y = y
#                     leftmost_lower_loader = tool

#     # Output the leftmost lower Loader node
#     return leftmost_lower_loader



# @err_catcher(name=__name__)                                   #   USED ????
# def find_extreme_position(comp, thisnode=None, ignore_node_type=None, find_min=True):
#     flow = comp.CurrentFrame.FlowView

#     if find_min:
#         thresh_x_position, thresh_y_position = float('inf'), float('inf')
#     else: 
#         thresh_x_position, thresh_y_position = -float('inf'), float('inf')

#     extreme_node = None

#     all_nodes = comp.GetToolList(False).values()

#     for node in all_nodes:
#         if thisnode and node.Name == thisnode.Name:
#             continue

#         if ignore_node_type and node.GetAttrs("TOOLS_RegID") == ignore_node_type:
#             continue

#         postable = flow.GetPosTable(node)
#         x, y = postable.values() if postable else (thresh_x_position, thresh_y_position)

#         x_thresh = x < thresh_x_position if find_min else x > thresh_x_position
#         y_thresh = y < thresh_y_position

#         if x_thresh:
#             thresh_x_position = x
#             extreme_node = node

#         if y_thresh:
#             thresh_y_position = y

#     return extreme_node, thresh_x_position, thresh_y_position