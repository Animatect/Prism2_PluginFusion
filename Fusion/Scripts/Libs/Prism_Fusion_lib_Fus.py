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

        if "mediaId" in toolData:
            tool.SetData('Prism_MediaID', toolData['mediaId'])

        if "aov" in toolData:
            tool.SetData('Prism_AOV', toolData['aov'])

        if "currChannel" in toolData:
            tool.SetData('Prism_Channel', toolData['currChannel'])

        if "version" in toolData:
            tool.SetData('Prism_Version', toolData['version'])

        if "mediaType" in toolData:
            tool.SetData('Prism_MediaType', toolData['mediaType'])

        if "filepath" in toolData:
            tool.Clip = toolData['filepath']

        if "fuseFormat" in toolData:
            tool["OutputFormat"] = toolData['fuseFormat']

        if "frame_start" in toolData:
            tool.GlobalIn[0] = toolData["frame_start"]
            tool.GlobalOut[0] = toolData["frame_end"]

            tool.ClipTimeStart = 0
            tool.ClipTimeEnd = toolData["frame_end"] - toolData["frame_start"]
            tool.HoldLastFrame = 0


        #   TODO    TRYING TO HAVE NODE SHOW NAME NOT CLIP PATH
        tool.SetAttrs({'TOOLS_NameSet': True})

        return tool
    
    except:
        logger.warning(f"ERROR: Failed to add {toolType} to Comp")
        return None
    

@err_catcher(name=__name__)
def updateTool(tool:Tool, toolData:dict, xPos=-32768, yPos=-32768, autoConnect=1) -> Tool:          #   TODO IS THIS NEEDED OR USE ADDTOOL?
    try:
        if "toolName" in toolData:
            tool.SetAttrs({'TOOLS_Name' : toolData['toolName']})
        if "nodeName" in toolData:
            tool.SetAttrs({'TOOLS_Name' : toolData['nodeName']})

        # if "toolUID" in toolData:
        #     tool.SetData('Prism_UUID', toolData['toolUID'])
        # if "nodeUID" in toolData:
        #     tool.SetData('Prism_UUID', toolData['nodeUID'])

        # if "mediaId" in toolData:
        #     tool.SetData('Prism_MediaID', toolData['mediaId'])

        # if "aov" in toolData:
        #     tool.SetData('Prism_AOV', toolData['aov'])

        if "version" in toolData:
            tool.SetData('Prism_Version', toolData['version'])

        # if "mediaType" in toolData:
        #     tool.SetData('Prism_MediaType', toolData['mediaType'])

        if "filepath" in toolData:
            tool.Clip = toolData['filepath']

        # if "fuseFormat" in toolData:
        #     tool["OutputFormat"] = toolData['fuseFormat']

        if "frame_start" in toolData:
            tool.GlobalIn[0] = toolData["frame_start"]
            tool.GlobalOut[0] = toolData["frame_end"]

            tool.ClipTimeStart = 0
            tool.ClipTimeEnd = toolData["frame_end"] - toolData["frame_start"]
            tool.HoldLastFrame = 0


        #   TODO    TRYING TO HAVE NODE SHOW NAME NOT CLIP PATH
        tool.SetAttrs({'TOOLS_NameSet': True})

        return tool
    
    except:
        logger.warning(f"ERROR: Failed to update {tool} in Comp")
        return None


@err_catcher(name=__name__)
def getNodeType(tool:Tool) -> str:
    try:
        return tool.GetAttrs("TOOLS_RegID")
    except:
        logger.warning("ERROR: Cannot retrieve node type")
        return None


@err_catcher(name=__name__)
def getAllToolsByType(comp, type:str) -> list:
    try:
        toolList = []
        for tool in comp.GetToolList(False).values():
            if getNodeType(tool) == type:
                toolList.append(tool)

        return toolList
    except:
        logger.warning(f"ERROR: Unable to get all {type} tools from the Comp")
        return None
    

@err_catcher(name=__name__)
def getSelectedTools(comp, type:str) -> list:
    try:
        toolList = []
        for tool in comp.GetToolList(True).values():
            if getNodeType(tool) == type:
                toolList.append(tool)

        return toolList
    
    except:
        logger.warning(f"ERROR: Unable to get all {type} tools from the Comp")
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
def setNodeToLeft(comp, tool, refNode=None, x_offset:int=0, y_offset:int=1):
    if refNode:
        if getNodeType(refNode) == "Loader":
            setNodePosition(comp, tool, x_offset = 0, y_offset = 1, refNode=refNode)
        else:
            setNodePosition(comp, tool, x_offset = -5, y_offset = 0, refNode=refNode)
    else:
        setNodePosition(comp, tool, x_offset = 0, y_offset = 0, refNode=refNode)


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


@err_catcher(name=__name__)
def findLeftmostLowerNode(comp, threshold:int=0.5) -> Tool:
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
def sortingEnabled(comp, save:bool=False, checked:bool=None) -> bool:
    if save:
        try:
            comp.SetData("isPrismImportChbxCheck", checked)
            return True
        except:
            logger.warning("ERROR:  Unable to save Sorting Checkbox state")
            return False

    try:
        return bool(comp.GetData("isPrismImportChbxCheck", default=False))
    except:
        logger.warning("ERROR:  Unable to get Sorting Checkbox state")
        return False
    

@err_catcher(name=__name__)
def getLoaderChannels(tool) -> list:
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

                # Add full channel name to assigned channels of current prefix              #   TODO Look into this
                channels.append(channelName)

        return channelData
    
    except:
        logger.warning("ERROR: Failed to get channel data")
        return None
    

@err_catcher(name=__name__)														#	TODO
def sortLoaders(comp, posRefNode:Tool, reconnectIn:bool=True, sortnodes:bool=True):
    flow = comp.CurrentFrame.FlowView

    # comp.Lock()

    #Get the leftmost loader within a threshold.
    leftmostpos = flow.GetPosTable(posRefNode)[1]
    bottommostpos = flow.GetPosTable(posRefNode)[2]
    thresh = 100

    # We get only the loaders within a threshold from the leftmost and who were created by prism.
    try:
        loaders = [l for l in comp.GetToolList(False, "Loader").values() if abs(flow.GetPosTable(l)[1] - leftmostpos)<=thresh and l.GetData("Prism_UUID")]
        loaderstop2bot = sorted(loaders, key=lambda ld: flow.GetPosTable(ld)[2])
        layers = set([splitLoaderName(ly.Name)[0] for ly in loaders])
    except:
        logger.warning("ERROR: Cannot sort loaders - unable to resolve threshold in the flow")
        return

    sortedloaders = []
    for ly in sorted(list(layers)):
        lyloaders = [l for l in loaders if splitLoaderName(l.Name)[0] == ly]
        sorted_loader_names = sorted(lyloaders, key=lambda ld: ld.Name.lower())
        sortedloaders += sorted_loader_names
    # if refNode is not part of nodes to sort we move the nodes down so they don't overlap it.
    refInNodes = any(ldr.Name == posRefNode.Name for ldr in sortedloaders)

    # Sorting the loader names
    if len(sortedloaders) > 0:
        lastloaderlyr = splitLoaderName(sortedloaders[0].Name)[0]
        try:
            if sortnodes:
                newx = leftmostpos#flow.GetPosTable(loaderstop2bot[0])[1]
                newy = flow.GetPosTable(loaderstop2bot[0])[2]
                if not refInNodes:
                    newy = bottommostpos + 1.5
                
                for l in sortedloaders:
                    # we reconnect to solve an issue that creates "Ghost" connections until comp is reoppened.
                    innode =  comp.FindTool(l.Name+"_IN")
                    outnode = comp.FindTool(l.Name+"_OUT")
                    if innode and reconnectIn:
                        innode.ConnectInput('Input', l)
                    lyrnm = splitLoaderName(l.Name)[0]
                    # we make sure we have at least an innode for this loader created by prism.
                    if innode and innode.GetData("isprismnode"):
                        if lyrnm != lastloaderlyr:
                            newy+=1
                        flow.SetPos(l, newx, newy)
                        flow.SetPos(innode, newx+2, newy)
                        if outnode:
                            flow.SetPos(outnode, newx+3, newy)
                    newy+=1
                    lastloaderlyr = lyrnm

                logger.debug("Sorted Nodes")

        except:
            logger.warning("ERROR: Failed to sort nodes")

    # comp.Unlock()


@err_catcher(name=__name__)
def splitLoaderName(name:str) -> list:
    try:
        prefix = name.rsplit('_', 1)[0]  # everything to the left of the last "_"
        suffix = name.rsplit('_', 1)[-1]  # everything to the right of the last "_"
        return prefix, suffix
    
    except:
        logger.warning(f"ERROR: Unable to split loader name {name}")









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