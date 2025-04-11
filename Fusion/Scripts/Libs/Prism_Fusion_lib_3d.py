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


##  THIS IS A LIBRARY FOR 3D FUNCTIONS FOR THE FUSION PRISM PLUGIN  ##
	
import pyautogui
import time
import tkinter as tk
import logging
# import os
# import pyperclip

import Libs.Prism_Fusion_lib_Fus as Fus
import Libs.Prism_Fusion_lib_Helper as Helper

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



def createUsdScene(plugin, origin, UUID):

    comp = plugin.getCurrentComp()
    flow = comp.CurrentFrame.FlowView

    #	Get uLoader node
    usdTool = Fus.getToolByUID(comp, UUID)

    # Add uMerge and uRender nodes
    uMerge = comp.AddTool("uMerge")
    uRender = comp.AddTool("uRenderer")

    # Connect Nodes
    uMerge.ConnectInput("SceneInput1", usdTool)
    uRender.ConnectInput("SceneInput", uMerge)

    #   Get position of the uLoader
    usdTool_x, usdTool_y = flow.GetPosTable(usdTool).values()

    #   Set positions relative to uLoader
    flow.SetPos(uMerge, usdTool_x + 2, usdTool_y)
    flow.SetPos(uRender, usdTool_x + 4, usdTool_y)


def create3dScene(plugin, origin, UUID):

    comp = plugin.getCurrentComp()
    flow = comp.CurrentFrame.FlowView


    #	Get uLoader node
    fbxTool = Fus.getToolByUID(comp, UUID)

    # Add uMerge and uRender nodes
    merge3d = comp.AddTool("Merge3D")
    render3d = comp.AddTool("Renderer3D")

    # Connect Nodes
    merge3d.ConnectInput("SceneInput1", fbxTool)
    render3d.ConnectInput("SceneInput", merge3d)

    #   Get position of the uLoader
    fbxTool_x, fbxTool_y = flow.GetPosTable(fbxTool).values()

    #   Set positions relative to uLoader
    flow.SetPos(merge3d, fbxTool_x + 2, fbxTool_y)
    flow.SetPos(render3d, fbxTool_x + 4, fbxTool_y)


abc_options = {
    "Points": True,
    "Transforms": True,
    "Hierarchy": False,
    "Lights": True,
    "Normals": True,
    "Meshes": True,
    "UVs": True,
    "Cameras": True,
    "InvCameras": True
    # "SamplingRate": 24
}


def focusFusionDialog(fusion:Fusion_, msg:str)->int:
    ui = fusion.UIManager
    disp = bmd.UIDispatcher(ui)

    spinner_value = 0  # Variable to store the spinner value

    tkinter = tk.Tk()
    screen_width = tkinter.winfo_screenwidth()
    screen_height = tkinter.winfo_screenheight()

    center_x = screen_width // 2
    center_y = screen_height // 2
    width = 500

    dlg = disp.AddWindow({
        'WindowTitle': 'Legacy 3D Focus Window', 
        'ID': 'Legacy3DWin', 
        'Geometry': [center_x-(width*0.5), center_y, width, 170], 
        'Spacing': 0,},[
        
        ui.VGroup({
            'Spacing': 0,
            'MinimumSize': [400, 150]
            },[
            ui.Label({
                "ID": "Label", 
                "Text": f"\n {msg} !\n",
				"Alignment":{
					"AlignHCenter":True,
					"AlignVCenter":True,
				},
				"WordWrap":True,
            }),
            # Add your GUI elements here:
            ui.HGroup({},[
                ui.HGap(1, 1),  # Spacer to push the button to the center horizontally
                ui.VGroup({},[
                    ui.HGroup({'Spacing': 5}, [
                            ui.Label({
                                'Text': 'Timeout: ',
                                'ToolTip': 'The amount of time in seconds the import should wait before failing.'}),
                            ui.SpinBox({'ID': 'Spinner', 'Value': 60, 'Minimum': 0, 'Maximum': 60,'FixedSize': [50, 20],}),
                            ui.Label({'Text': 'secs'}),
                        ]),
                    ui.Button({
                        'ID': 'B',
                        'Text': 'START IMPORT',
                        'FixedSize': [200, 20], # Width x Height in pixels
                    }),
                ]),
                ui.HGap(1, 1),  # Spacer to push the button to the center horizontally
            ]),
        ]),
    ])

    itm = dlg.GetItems()

    # The window was closed
    def _func(ev):
        nonlocal spinner_value
        spinner_value = -1
        disp.ExitLoop()
    dlg.On.Legacy3DWin.Close = _func

    # Add your GUI element based event functions here:
    def _func(ev):
        nonlocal spinner_value
        spinner_value = itm['Spinner'].Value  # Retrieve the spinner value
        disp.ExitLoop()
    dlg.On.B.Clicked = _func

    dlg.Show()
    disp.RunLoop()
    dlg.Hide()

    return spinner_value


def doUiImport(fusion:Fusion_, formatCall:str, interval:float, filepath:str, timeoutsecs:int):
    comp:Composition_ = fusion.GetCurrentComp()
    #Call the dialog
    fusion.QueueAction("Utility_Show", {"id":formatCall})
    time.sleep(interval)
    pyautogui.typewrite(filepath)
    time.sleep(interval)
    pyautogui.press("enter")
    time.sleep(interval)
    pyautogui.press("enter")
    time.sleep(interval)
    
    # Wait until file is imported
    elapsedtime = 0
    while len(comp.GetToolList(True))<0 and elapsedtime < timeoutsecs:
        loopinterval:float = 0.1
        elapsedtime += loopinterval
        time.sleep(loopinterval)
    if len(comp.GetToolList(True)) > 0:
        return True
    else:
        return False
    

def importFormatByUI(fusion:Fusion_, origin:Legacy3D_ImportClass, formatCall:str, filepath:str, global_scale:float, options:dict = None, interval:float = 0.5):
    origin.stateManager.showMinimized()
    comp:Composition_ = fusion.GetCurrentComp()
    flow:FlowView_ = comp.CurrentFrame.FlowView
    flow.Select(None)

    #Set preferences for the alembic import dialog
    if formatCall == "AbcImport" and isinstance(options, dict):
        current = fusion.GetPrefs("Global.Alembic.Import")
        new = current.copy()
        for key, value in options.items():
            if key in current:
                new[key] = value
            else:
                print("Invalid option %s:" % key)
        fusion.SetPrefs("Global.Alembic.Import", new)
    
    #Warning
    fString = "Importing this 3Dformat requires UI automation.\n\nPLEASE DO NOT USE THE MOUSE AFTER CLOSING THIS DIALOG UNTIL IMPORT IS DONE"
    #   Create a dialog to focus the fusion window and retrieves info from it.
    timeoutSecs:int = focusFusionDialog(fusion, fString)
    imported:bool = False

    if timeoutSecs > 0:
        imported = doUiImport(fusion, formatCall, interval, filepath, timeoutSecs)
    

    return imported


def importLegacyAbc(importPath:str, fusion:Fusion_, origin:Legacy3D_ImportClass)->bool:
    return importFormatByUI(
                            fusion=fusion, 
                            origin=origin, 
                            formatCall="AbcImport", 
                            filepath=importPath, 
                            global_scale=100, 
                            options=abc_options
                        )


def importLegacyFbx(importPath:str, fusion:Fusion_, origin:Legacy3D_ImportClass)->bool:
    return importFormatByUI(
                            fusion=fusion, 
                            origin=origin,  
                            formatCall="FBXImport", 
                            filepath=importPath,
                            global_scale=100
                        )


def createLegacy3DScene(origin:Legacy3D_ImportClass, comp:Composition_, flow:FlowView_, filename:str, toolData:dict, stateUUID:str, initcoords:tuple=tuple((0,0)))->bool:
    #   check if there was a merge3D in the import and where was it connected to
    importedTools:list[Tool_] = comp.GetToolList(True).values()
    isUpdate:bool = False
    positionedNodes:list[str] = []
    unsuccesfulConnections:list[str] = []
    # aggregateData = CompDb.loadPrismFileDb(comp)

    product = toolData["product"]
    version = toolData["version"]

    atx:float = initcoords[0] 
    aty:float = initcoords[1]

    #Set the position of the imported nodes relative to the previously active tool or last click in compView
    impnodes = [n for n in importedTools]
    if len(impnodes) > 0:
        # Find the rightmost tool
        rightmost_tool:Tool_ = impnodes[0]
        rightmost_x = flow.GetPosTable(rightmost_tool)[1]
        
        for tool in impnodes:
            tool_x = flow.GetPosTable(tool)[1]
            if tool_x > rightmost_x:
                rightmost_x = tool_x
                rightmost_tool = tool

        firstnode:Tool_ = rightmost_tool  # Use the rightmost tool as the reference
        firstnode.SetAttrs({'TOOLS_Name' : f"ROOT_{product}"})
        fstnx, fstny = flow.GetPosTable(firstnode).values()

        
        newNodes:list[str] = [n.Name for n in importedTools]

        flow.GoToBookmark('3dImportBM')
        isUpdate, positionedNodes, unsuccesfulConnections = ReplaceBeforeImport(origin, comp, stateUUID, importedTools, firstnode)
        cleanbeforeImport(origin, stateUUID)

        # Reassign the State ID as the entry point node ID
        # This Has to be done after cleaning the scene so in case of update the old firstnode (which shares UID) is gone.
        firstnode.SetData("Prism_UUID", stateUUID)

        if isUpdate and len(positionedNodes)>0:
            atx, aty = flow.GetPosTable(firstnode).values()


        for tool in impnodes:
            thisToolData:dict = toolData.copy()
            # Give a UUID to every imported node 
            toolUID = Helper.createUUID()
            if tool.GetData("Prism_UUID"):
                toolUID = tool.GetData("Prism_UUID")
            else:
                tool.SetData("Prism_UUID", toolUID)
            thisToolData["nodeName"] = tool.Name
            thisToolData["toolOrigName"] = tool.Name
            thisToolData["toolUID"] = toolUID
            thisToolData["stateUID"] = stateUUID
            thisToolData["tooltype"] = tool.GetAttrs('TOOLS_RegID')
            thisToolData["entryNode"] = {firstnode.Name : firstnode.GetData("Prism_UUID")}
            
            inputTools:list = [inpt.GetConnectedOutput().GetTool() for inpt in tool.GetInputList().values() if inpt.GetConnectedOutput()]
            if len(inputTools)>0:
                connectedNodesDict:dict= {}
                for t in inputTools:
                    # print(f"Connected node name: {t.GetAttrs('TOOLS_Name')}")
                    tUID = Helper.createUUID()
                    if t.GetData("Prism_UUID"):
                        tUID = t.GetData("Prism_UUID")
                    else:
                        t.SetData("Prism_UUID", tUID)
                    # print(f"{tool.Name} connections: {t.Name}")
                    connectedNodesDict[t.GetAttrs('TOOLS_Name')]=tUID
                
                thisToolData["connectedNodes"] = connectedNodesDict
            Fus.addToolData(tool, thisToolData)
            if not tool.Name in positionedNodes:
                x,y  = flow.GetPosTable(tool).values()
                newx = x+(atx-fstnx)
                newy = y+(aty-fstny)
                flow.SetPos(tool, newx-1, newy)

    ##########
   
    for t in importedTools:
        newName:str =  f"{t.GetAttrs('TOOLS_Name')}_{toolData.get('product')}_{version}"
        t.SetAttrs({'TOOLS_Name' : newName})

    origin.setName = "Import_" + toolData.get("product")
    
    # Re-center view on the creation coordinates.
    flow.GoToBookmark('3dImportBM')
    # flow.DeleteBookmark('3dImportBM')
    bookmarks = flow.GetBookmarkList()
    last_item = bookmarks.popitem()
    flow.SetBookmarkList(bookmarks)

    #   Deselect All
    flow.Select()

    # Reselect.
    objs:list[Tool_] = []

    #REPLACEMENT UP#
    stateTools:list[Tool_] = getToolsFromNodeList(comp, getStateNodesList(comp, stateUUID))
    for tool in stateTools:
        objs.append(tool)

    #   Select nodes in comp
    for o in objs:
        flow.Select(o)

    #Set result to True if we have nodes
    result:bool = len(importedTools) > 0

    if isUpdate and len(unsuccesfulConnections)>0:
        msg:str = "The Following connections were unsuccessful: \n"
        for connection in unsuccesfulConnections:
            msg += "\n" + connection

        msg += "\n if possible reconnect manually."
        origin.core.popup(msg, severity="info")

    return result


def getNode(obj:str|dict|Tool_)->dict:
    if type(obj) == str:
        node = {"name": obj}
    elif type(obj) == dict:
        node = {"name": obj["name"]}
    else:
        node = {"name": obj.Name}
    return node


def selectNodes(origin:Legacy3D_ImportClass):
    if origin.lw_objects.selectedItems() != []:
        nodes:list[dict] = []
        for i in origin.lw_objects.selectedItems():
            node = origin.nodes[origin.lw_objects.row(i)]
            if isNodeValid(origin, node):
                nodes.append(node)
        # select(nodes)


def isNodeValid(origin, handle):
    return True


def getObject(comp:Composition_, node:str|dict)->Tool_:
    if type(node) == str:
        node = getNode(node)

    return comp.FindTool(node["name"])


def applyProductSufix(originalName:str, origin:Legacy3D_ImportClass)->str:
    newName:str = originalName + "_" + origin.importPath.split("_")[-2]
    return newName


def cleanbeforeImport(origin:Legacy3D_ImportClass, stateUID:str):
    # if origin.nodes == []:
    #     return
    # nodes:list[dict] = []
    # for o in origin.nodes:
    #     nodes.append(getNode(o))

    origin.core.appPlugin.deleteNodes(stateUID)
    origin.nodes = []


def deleteTools(comp:Composition_, stateUID:str):
    # aggregateData = CompDb.loadPrismFileDb(comp)
    stateTools:list[Tool_] = getToolsFromNodeList(comp, getStateNodesList(comp, stateUID))
    for tool in stateTools:
        try:
            tool.Delete()
            if tool.GetData("Prism_UUID"):
                pass
                # CompDb.removeNodeFromDB(comp, "import3d", tool.GetData("Prism_UUID"), saveDB=False, aggregateData=aggregateData)

        except:
            logger.debug("Could not delete the tool.")
    

# def getNodeStateTypes(comp:Composition_) -> list:
#     # cpData = CompDb.loadPrismFileDb(comp)
#     stateTypes:list = []
#     for n in cpData["nodes"]:
#         stateTypes.append(n)

#     return stateTypes


def getAllNodes(comp:Composition_) -> dict:
    # cpData = CompDb.loadPrismFileDb(comp)
    # stateTypes:list[str] = getNodeStateTypes(comp)
    nodes:dict = {
        l.GetData("Prism_UUID") : l for l in comp.GetToolList(False, "Loader").values()
            if (
                l.GetData("Prism_UUID") and
                isinstance(l.GetData('Prism_ToolData'), dict) and
                l.GetData('Prism_ToolData').get("stateUID")
            )
    }
    
    return nodes


def getStateNodesList(comp:Composition_, stuid:str) -> list[str]:
    # Get a list of the state nodes UIDS
    toolls:list[str] = [
        l.GetData("Prism_UUID") for l in comp.GetToolList(False, "Loader").values()
        if (
            l.GetData("Prism_UUID")
            and l.GetData('Prism_ToolData').get("stateUID") == stuid
        )
    ]
    
    return toolls


def getStateNodesOrigNameList(comp:Composition_, nodeUIDlist:list[str]) -> list[str]:
    nodes:dict = getAllNodes(comp)
    nodeNmLs:list[str] = []

    for nodeuid in nodeUIDlist:
        node:Tool_ = nodes.get(nodeuid)
        nodeData:dict = node.GetData('Prism_ToolData')
        if nodeData:
            toolorignm:str = nodeData.get("toolOrigName")
            if toolorignm:
                nodeNmLs.append(toolorignm)
    
    return nodeNmLs


def getToolsFromNodeList(comp:Composition_, nodeUIDlist:list[str]) -> list[Tool_]:
    nodes:dict = getAllNodes(comp)
    tools:list[Tool_] = []

    for nodeuid in nodeUIDlist:
        if (tool := nodes.get(nodeuid)):
            tools.append(tool)

    return tools


def ReplaceBeforeImport(origin:Legacy3D_ImportClass, comp:Composition_, stateUID:str, newtools:list[Tool_], sceneTool:Tool_)->tuple[bool, list[str], list[str]]:
    alldbnodes:dict = getAllNodes(comp)
    statenodesuids:list[str] = getStateNodesList(comp, stateUID)
    stateNodesNames:list[str] = getStateNodesOrigNameList(comp, statenodesuids)
    stateTools:list[Tool_] = getToolsFromNodeList(comp, statenodesuids)
    oldSceneTool:Tool_|None = None
    positionednodes:list[str] = []
    unsuccesfulconnections:list[str] = []

    if len(stateTools) < 1:
        return False, [], []
    
    if (oldSceneTool := alldbnodes.get(stateUID)):
        pass # using the walrus operator to assign the variable that would have been assigned inside the block
    else:
        return False, [], []
    
    # Match new to old tools.
    for newtool in newtools:
        toolType:str  = newtool.GetAttrs("TOOLS_RegID")
        if newtool == sceneTool or toolType == "Merge3D":
            continue

        oldtool:Tool_ = None
        if newtool.Name in stateNodesNames:
            for nodeuid in statenodesuids:
                node:Tool_ = alldbnodes.get(nodeuid)
                node_data:dict = node.GetData('Prism_ToolData') if node else None
                if node_data:
                    if newtool.Name == node_data.get("toolOrigName") and toolType == node_data.get("tooltype"):
                        for t in stateTools:
                            if t.GetData('Prism_UUID') == nodeuid:
                                oldtool = t
                                break
        

        # If there is a previous version of the same node.
        if oldtool:
            # check if it has valid inputs that are not part of previous import
            connectedInputList:list = [inpt for inpt in oldtool.GetInputList().values() if inpt.GetConnectedOutput()]
            for inpt in connectedInputList:
                input:Input_ = inpt
                connectedOutput:Output_ = input.GetConnectedOutput()
                inputName:str = input.Name
                connectedtool:Tool_ = connectedOutput.GetTool()
                # Avoid Keyframe nodes
                if not connectedtool.GetAttrs("TOOLS_RegID") =="BezierSpline":
                    # check to avoid a connection that breaks the incoming hierarchy that we are not reconnecting nodes that belong to the orig scene.
                    if not connectedtool.GetData('Prism_UUID') or not connectedtool.GetData('Prism_UUID') in statenodesuids:
                        # Merge is only supported for the Scene node.                        
                        connectionsuccess:bool = newtool.ConnectInput(inputName, connectedtool)
                        if not connectionsuccess and " " in inputName:
                            fixedName:str = inputName.replace(" ", ".") # some inputs convert "." to " "
                            try:
                                connectionsuccess = newtool.ConnectInput(fixedName, connectedtool)
                            except Exception as e:
                                logger.warning(e)
                        
                        if not connectionsuccess:
                            connectionstring:str = f"{connectedtool.Name} --> {newtool.Name}.{inputName}"
                            unsuccesfulconnections.append(connectionstring)
                            
            Fus.matchToolPos(comp, newtool, oldtool)
            positionednodes.append(newtool.Name)
        
    # Reconnect the 3D Scene.    
    if sceneTool.GetAttrs("TOOLS_RegID") == "Merge3D":
        if oldSceneTool.GetAttrs("TOOLS_RegID") == "Merge3D":
            mergednodes:list[Tool_] = []
            sceneinputs:list[Input_] = [input for input in oldSceneTool.GetInputList().values() if "SceneInput" in input.Name and input.GetConnectedOutput()]
            for input in sceneinputs:
                connectedOutput:Output_ = input.GetConnectedOutput()
                connectedtool:Tool_ = connectedOutput.GetTool()
                if not connectedtool.GetData('Prism_UUID') or not connectedtool.GetData('Prism_UUID') in statenodesuids:
                    mergednodes.append(connectedtool)
            if sceneTool.GetAttrs("TOOLS_RegID") == "Merge3D" and len(mergednodes) > 0:
                for mergednode in mergednodes:
                    # get empty inputs
                    newsceneinputs:list = [input for input in sceneTool.GetInputList().values() if "SceneInput" in input.Name and not input.GetConnectedOutput()]
                    # get the first of availible inputs.
                    input = newsceneinputs[0]
                    try:
                        sceneTool.ConnectInput(input.Name, mergednode)
                    except Exception as e:
                        logger.warning(e)
                    comp.UpdateViews()

    #   Gets to output tool and connection
    outConnections = oldSceneTool.GetOutputList()[1].GetConnectedInputs()

    for input in outConnections.values():
        inputName:str = input.Name
        connectedTool = input.GetTool()

        #   Connect if the tool exists
        if connectedTool:
            connectedTool.ConnectInput(inputName, sceneTool)
        ##  If the Root tool was being viewed in the viewer, it will not re-display it there.

    # Match positions.
    Fus.matchToolPos(comp, sceneTool, oldSceneTool)
    positionednodes.append(sceneTool.Name)
        
    return True, positionednodes, unsuccesfulconnections




# 
# def sm_import_updateObjects(self, origin):
#     pass


# 
# def sm_import_removeNameSpaces(self, origin):
#     pass


#############   ORIGINAL CODE   ###########




# 
# def getPythonLocation(self)-> str:
#     ospath = os.path.dirname(os.__file__)
#     path_components = os.path.split(ospath)
#     new_path = os.path.join(*path_components[:-1])
#     python_location = os.path.join(new_path, "python.exe")
#     # Construct the command as a list
#     return python_location


# 
# def create_and_run_bat(self):
#     import subprocess
#     home_dir = os.path.expanduser("~")
#     bat_file_path = os.path.join(home_dir, "tmpcmdwin.bat")
#     python_path = self.getPythonLocation()
#     package_path = os.path.join(os.path.dirname(__file__), 'thirdparty')

#     # Check if the batch file already exists
#     if os.path.exists(bat_file_path):
#         os.remove(bat_file_path)

#     bat_content = f"""@echo off
# echo Running Python commands...
# "{python_path}" -c "import sys; sys.path.append(r'{package_path}'); import pygetwindow as gw; gw.getWindowsWithTitle('Fusion Studio - [')[0].activate()"
# @REM pause
# exit
# """

#     # Create the batch file
#     with open(bat_file_path, 'w') as bat_file:
#         bat_file.write(bat_content)

#     return bat_file_path


# 
# def focus_fusion_window(self):
#     import subprocess
#     # Get all windows
#     windows = gw.getAllTitles()

#     # Define the pattern using a regular expression
#     pattern = r'^Fusion Studio - '
#     window_title = "Fusion Studio - ["

#     # Filter windows based on the pattern
#     matching_windows = [window for window in windows if re.match(pattern, window)]
#     # Focus on the first matching window
#     if matching_windows:
#         # script_dir = os.path.dirname(os.path.abspath(__file__))
#         batch_file = self.create_and_run_bat()#os.path.join(script_dir, "cmdwin.bat")
#         cmdwin = subprocess.Popen(["cmd", "/c", "start", batch_file], shell=True)
#         time.sleep(1)
#         # Delete the batch file
#         os.remove(batch_file)
        
#         if not len(matching_windows)>1:	
#             matching_window = gw.getWindowsWithTitle(window_title)[0]
#             # print("matching_window: ", matching_window.title)
#             # matching_window.activate()
#             # time.sleep(1)
#             # print("active: ", matching_window.isActive)
#             if matching_window.isActive:
#                 return True
#             else:
#                 msg = f"Window with title '{window_title}' is not active.\nTry again leaving the cursor over the Fusion Window."
#                 self.popup = self.core.popup(msg)
#                 return False
#         else:
#             msg = f"There is more than one Window with title '{window_title}' open\nplease close one."
#             self.core.popup(msg)
#             return False

#     else:
#         msg = f"Window with title '{window_title}' not found."
#         self.core.popup(msg)
#         return False



# 
# def importBlenderCam(self, importPath, origin):
#     from MH_BlenderCam_Fusion_Importer import BlenderCameraImporter
#     BcamImporter = BlenderCameraImporter()
#     return BcamImporter.import_blender_camera(importPath)


# 
# def sm_import_disableObjectTracking(self, origin):
#     self.deleteNodes(origin, [origin.setName])


# # #Main Import function
# 
# def sm_import_importToApp(self, origin, doImport, update, impFileName):


#     #	BlenderCam Check
#     root, _ = os.path.splitext(impFileName)
#     isbcam = False
#     new_file_path = os.path.normpath(root + '.bcam')
#     if os.path.exists(new_file_path):
#         isbcam = True
#         impFileName = new_file_path
    



#     comp = self.getCurrentComp()
#     flow = comp.CurrentFrame.FlowView
#     fileName = os.path.splitext(os.path.basename(impFileName))
#     origin.setName = ""
#     result = False


#     # Check that we are not importing in a comp different than the one we started the stateManager from
#     if not self.sm_checkCorrectComp(comp):
#         return

#     #try to get an active tool to set a ref position
#     activetool = None
#     try:
#         activetool = comp.ActiveTool()
#     except:
#         pass
#     if activetool and not activetool.GetAttrs("TOOLS_RegID") =="BezierSpline":
#         atx, aty = flow.GetPosTable(activetool).values()
#     else:
#         atx, aty = self.find_LastClickPosition()
    
#     #	Get Extension
#     ext = fileName[1].lower()

#     #	Check if Image Format is supported
#     if ext not in self.importHandlers:
#         self.core.popup(f"Import format '{ext}' is not supported")
#         logger.warning(f"Import format '{ext}' is not supported")
#         return {"result": False, "doImport": doImport}

#     else:
#         # Do the importing
#         result = self.importHandlers[ext]["importFunction"](impFileName, origin)

#     # After import update the stateManager interface
#     if result:
#         #check if there was a merge3D in the import and where was it connected to
#         newNodes = [n.Name for n in comp.GetToolList(True).values()]
#         if isbcam:
#             importedNodes = []
#             importedNodes.append(self.getNode(newNodes[0]))
#             origin.setName = "Import_" + fileName[0]			
#             origin.nodes = importedNodes
#         else:
#             refPosNode, positionedNodes = self.ReplaceBeforeImport(origin, newNodes)
#             self.cleanbeforeImport(origin)
#             if refPosNode:
#                 atx, aty = flow.GetPosTable(refPosNode).values()
    
#             importedTools = comp.GetToolList(True).values()
#             #Set the position of the imported nodes relative to the previously active tool or last click in compView
#             impnodes = [n for n in importedTools]
#             if len(impnodes) > 0:

#                 firstnode = impnodes[0]
#                 fstnx, fstny = flow.GetPosTable(firstnode).values()

#                 for n in impnodes:
#                     if not n.Name in positionedNodes:
#                         x,y  = flow.GetPosTable(n).values()

#                         offset = [x-fstnx,y-fstny]
#                         newx = x+(atx-x)+offset[0]
#                         newy = y+(aty-y)+offset[1]
#                         flow.SetPos(n, newx-1, newy)

#             ##########

#             importedNodes = []
#             for i in newNodes:
#                 # Append sufix to objNames to identify product with unique Name
#                 node = self.getObject(i)
#                 newName = self.applyProductSufix(i, origin)
#                 node.SetAttrs({"TOOLS_Name":newName, "TOOLB_NameSet": True})
#                 importedNodes.append(self.getNode(newName))

#             origin.setName = "Import_" + fileName[0]			
#             origin.nodes = importedNodes

#         #Deselect All
#         flow.Select()

#         objs = [self.getObject(x) for x in importedNodes]
        
#         #select nodes in comp
#         for o in objs:
#             flow.Select(o)

#         #Set result to True if we have nodes
#         result = len(importedNodes) > 0

#     return {"result": result, "doImport": doImport}