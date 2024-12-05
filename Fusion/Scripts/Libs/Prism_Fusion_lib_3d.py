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
	

from PrismUtils.Decorators import err_catcher as err_catcher



@err_catcher(name=__name__)
def createUsdScene(plugin, origin, UUID):

    comp = plugin.getCurrentComp()
    flow = comp.CurrentFrame.FlowView

    comp.Lock()

    #	Get uLoader node
    usdTool = plugin.getNodeByUID(UUID)

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

    comp.Unlock()


@err_catcher(name=__name__)
def create3dScene(plugin, origin, UUID):

    comp = plugin.getCurrentComp()
    flow = comp.CurrentFrame.FlowView

    comp.Lock()

    #	Get uLoader node
    fbxTool = plugin.getNodeByUID(UUID)

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

    comp.Unlock()





#############   ORIGINAL CODE   ###########



# abc_options = {
#     "Points": True,
#     "Transforms": True,
#     "Hierarchy": False,
#     "Lights": True,
#     "Normals": True,
#     "Meshes": True,
#     "UVs": True,
#     "Cameras": True,
#     "InvCameras": True
#     # "SamplingRate": 24
# }

# @err_catcher(name=__name__)
# def getPythonLocation(self)-> str:
#     ospath = os.path.dirname(os.__file__)
#     path_components = os.path.split(ospath)
#     new_path = os.path.join(*path_components[:-1])
#     python_location = os.path.join(new_path, "python.exe")
#     # Construct the command as a list
#     return python_location


# @err_catcher(name=__name__)
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


# @err_catcher(name=__name__)
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
    

# @err_catcher(name=__name__)
# def doUiImport(self, fusion, formatCall, interval, filepath):
#     if self.focus_fusion_window():
#         comp = fusion.GetCurrentComp()
#         #Call the dialog
#         fusion.QueueAction("Utility_Show", {"id":formatCall})
#         time.sleep(interval)
#         pyautogui.typewrite(filepath)
#         time.sleep(interval)
#         pyautogui.press("enter")
#         pyautogui.press("enter")
        
#         # Wait until file is imported
#         elapsedtime = 0
#         while len(comp.GetToolList(True))<0 and elapsedtime < 20:
#             loopinterval = 0.1
#             elapsedtime += loopinterval
#             time.sleep(loopinterval)
#         if len(comp.GetToolList(True)) > 0:
#             return True
#         else:
#             return False
#     else:
#         return False

    
# @err_catcher(name=__name__)
# def importFormatByUI(self, origin, formatCall, filepath, global_scale, options = None, interval = 0.05):
#     origin.stateManager.showMinimized()

#     fusion = self.fusion
#     comp = fusion.GetCurrentComp()
#     #comp.Lock()
#     flow = comp.CurrentFrame.FlowView
#     flow.Select(None)

#     if not os.path.exists(filepath):
#         QMessageBox.warning(
#             self.core.messageParent, "Warning", "File %s does not exists" % filepath
#         )

#     #Set preferences for the alembic import dialog
#     if formatCall == "AbcImport" and isinstance(options, dict):
#         current = fusion.GetPrefs("Global.Alembic.Import")
#         new = current.copy()
#         for key, value in options.items():
#             if key in current:
#                 new[key] = value
#             else:
#                 print("Invalid option %s:" % key)
#         fusion.SetPrefs("Global.Alembic.Import", new)
    
#     #Warning
#     fString = "Importing this 3Dformat requires UI automation.\n\nPLEASE DO NOT USE THE MOUSE AFTER CLOSING THIS DIALOG UNTIL IMPORT IS DONE"
#     buttons = ["Continue"]
#     result = self.core.popupQuestion(fString, buttons=buttons, icon=QMessageBox.NoIcon)

#     imported = False
#     if result == "Save":
#         filepath = self.getCurrentFileName()
#         didSave = False
#         if not filepath == "":
#             if self.core.fileInPipeline():
#                 didSave = self.core.saveScene(versionUp=False)
#             else:
#                 didSave = self.saveScene(filepath)
#             if not didSave == False:
#                 imported = self.doUiImport(fusion, formatCall, interval, filepath)
#         else:
#             self.core.popup("Scene can't be saved, save a version first")

#     elif result == "Save new version":
#         if self.core.fileInPipeline():
#             self.core.saveScene()
#             imported = self.doUiImport(fusion, formatCall, interval, filepath)

#     elif result == "Continue":
#         imported = self.doUiImport(fusion, formatCall, interval, filepath)

#     else:
#         imported = False

#     imported = self.doUiImport(fusion, formatCall, interval, filepath)
#     origin.stateManager.showNormal()

#     return imported


# @err_catcher(name=__name__)
# def importAlembic(self, importPath, origin):
#     return self.importFormatByUI(origin=origin, formatCall="AbcImport", filepath=importPath, global_scale=100, options=self.abc_options)




# @err_catcher(name=__name__)
# def importUSD(self, origin, importPath, UUID, nodeName, version, update=False):
#     comp = self.getCurrentComp()
#     comp.Lock()
#     #	Add uLoader node
#     usdTool = comp.AddTool("uLoader")
#     #	Set import file path
#     usdTool["Filename"] = importPath
#     #	Set node name
#     usdTool.SetAttrs({"TOOLS_Name": nodeName})
#     #	Add custom UUID
#     usdTool.SetData('PrImportUID', UUID)
#     comp.Unlock()
#     return {"result": True, "doImport": True}






# @err_catcher(name=__name__)
# def importFBX(self, importPath, origin):
#     comp = self.getCurrentComp()
#     comp.Lock()
#     #	Add FBX Mesh node
#     fbxTool = comp.AddTool("SurfaceFBXMesh")
#     #	Set import mesh file path
#     fbxTool["ImportFile"] = importPath
#     #	Get versionInfo data
#     versionInfoData = self.core.products.getProductDataFromFilepath(importPath)
#     productName = versionInfoData["product"]
#     productVersion = versionInfoData["version"]
#     #	Set node name
#     toolName = f"{productName}_{productVersion}"
#     fbxTool.SetAttrs({"TOOLS_Name": toolName})
#     #	Add custom UUID
#     fbxTool.SetData('PrImportUID', self.createUUID())
#     comp.Unlock()
#     return {"result": True, "doImport": True}
#     return self.importFormatByUI(origin = origin, formatCall="FBXImport", filepath=importPath, global_scale=100)


# @err_catcher(name=__name__)
# def importBlenderCam(self, importPath, origin):
#     from MH_BlenderCam_Fusion_Importer import BlenderCameraImporter
#     BcamImporter = BlenderCameraImporter()
#     return BcamImporter.import_blender_camera(importPath)


# @err_catcher(name=__name__)
# def sm_import_disableObjectTracking(self, origin):
#     self.deleteNodes(origin, [origin.setName])


# # #Main Import function
# @err_catcher(name=__name__)
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
#                 comp.Lock()

#                 fisrtnode = impnodes[0]
#                 fstnx, fstny = flow.GetPosTable(fisrtnode).values()

#                 for n in impnodes:
#                     if not n.Name in positionedNodes:
#                         x,y  = flow.GetPosTable(n).values()

#                         offset = [x-fstnx,y-fstny]
#                         newx = x+(atx-x)+offset[0]
#                         newy = y+(aty-y)+offset[1]
#                         flow.SetPos(n, newx-1, newy)

#                 comp.Unlock()
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


# @err_catcher(name=__name__)
# def getNode(self, obj):
#     if type(obj) == str:
#         node = {"name": obj}
#     elif type(obj) == dict:
#         node = {"name": obj["name"]}
#     else:
#         node = {"name": obj.Name}
#     return node


# @err_catcher(name=__name__)
# def selectNodes(self, origin):
#     if origin.lw_objects.selectedItems() != []:
#         nodes = []
#         for i in origin.lw_objects.selectedItems():
#             node = origin.nodes[origin.lw_objects.row(i)]
#             if self.isNodeValid(origin, node):
#                 nodes.append(node)
#         # select(nodes)
                

# @err_catcher(name=__name__)
# def isNodeValid(self, origin, handle):
#     return True
    

# @err_catcher(name=__name__)
# def getObjectNodeNameByTool(self, origin, node):
#     if self.isNodeValid(origin, node):
#         try:
#             return node["name"]
#         except:
#             QMessageBox.warning(
#                 self.core.messageParent, "Warning", "Cannot get name from %s" % node
#             )
#             return node
#     else:
#         return "invalid"


# @err_catcher(name=__name__)
# def getObject(self, node):
#     comp = self.getCurrentComp()
#     if type(node) == str:
#         node = self.getNode(node)

#     return comp.FindTool(node["name"])


# @err_catcher(name=__name__)
# def applyProductSufix(self, originalName, origin):
#     newName = originalName + "_" + origin.importPath.split("_")[-2]
#     return newName


# @err_catcher(name=__name__)
# def cleanbeforeImport(self, origin):
#     if origin.nodes == []:
#         return
#     nodes = []
#     for o in origin.nodes:
#         nodes.append(self.getNode(o))

#     self.deleteNodes(origin, nodes)
#     origin.nodes = []


# @err_catcher(name=__name__)
# def ReplaceBeforeImport(self, origin, newnodes):
#     comp = self.getCurrentComp()
#     if origin.nodes == []:
#         return None, []
#     nodes = []
#     nodenames =[]
#     outputnodes = []
#     positionednodes = []
#     sceneNode = None
    
#     # We are going to collect the existing nodes and check if there is a merge3D or transform3D node that represents the entry of the scene.
#     for o in origin.nodes:
#         hasmerge = False
#         node = comp.FindTool(o["name"])
#         if node:
#             # Store Scene Node Connections
#             nodeID  = node.GetAttrs("TOOLS_RegID")
#             ismerge = nodeID == "Merge3D"
#             # We try to account for Transform3D nodes that are not standarly Named.
#             istrans3D = nodeID == "Transform3D" and "Transform3D" in node.Name
#             # If there is no merge there should be a transform3D but if there is merge transform3D is out.
#             if ismerge or istrans3D:
#                 if ismerge:
#                     hasmerge = True
#                 if ismerge or not hasmerge:
#                     outputnodes = [] # clean this variable in case there was an unaccounted node
#                     sceneNode = node
#                     connectedinputs = node.output.GetConnectedInputs()
#                     if len(connectedinputs)>0:
#                         for v in connectedinputs.values():
#                             connectedNode = {"node":v.GetTool().Name,"input":v.Name}
#                             outputnodes.append(connectedNode)
#             nodenames.append(node.Name)
#             nodes.append(node)
#     for o in newnodes:
#         newnode = comp.FindTool(o)
#         # Reconnect the scene node
#         if sceneNode:
#             nodeID = newnode.GetAttrs("TOOLS_RegID")
#             sceneNID = sceneNode.GetAttrs("TOOLS_RegID")
#             if nodeID == sceneNID:

#                 # We try to account for Transform3D nodes that are not standarly Named.
#                 proceed = True
#                 if nodeID == "Transform3D" and not "Transform3D" in newnode.Name:
#                     proceed = False
                
#                 if proceed and len(outputnodes) > 0:
#                     for outn in outputnodes:
#                         tool = comp.FindTool(outn["node"])
#                         tool.ConnectInput(outn["input"], newnode)
#         # Match old to new
#         oldnodename = self.applyProductSufix(o, origin)
#         oldnode = comp.FindTool(oldnodename)

#         # If there is a previous version of the same node.
#         if oldnode:
#             # idx = 1
#             # check if it has valid inputs that are not part of previous import
#             for input in oldnode.GetInputList().values():
#                 # idx+=1
#                 connectedOutput = input.GetConnectedOutput()
#                 if connectedOutput:
#                     inputName = input.Name
#                     connectedtool = connectedOutput.GetTool()
#                     # Avoid Feyframe nodes
#                     if not connectedtool.GetAttrs("TOOLS_RegID") =="BezierSpline" and not newnode.GetAttrs("TOOLS_RegID") == "Merge3D":
#                         # check to avoid a connection that breaks the incoming hierarchy.
#                         if not connectedtool.Name in nodenames:
#                             newnode.ConnectInput(inputName, connectedtool)
#             # Reconnect the 3D Scene.
#             if sceneNode:
#                 if sceneNode.GetAttrs("TOOLS_RegID") == "Merge3D":
#                     if oldnode.GetAttrs("TOOLS_RegID") == "Merge3D":
#                         mergednodes = []
#                         sceneinputs = [input for input in oldnode.GetInputList().values() if "SceneInput" in input.Name]
#                         # newsceneinputs = [input for input in newnode.GetInputList().values() if "SceneInput" in input.Name]
#                         for input in sceneinputs:
#                             connectedOutput = input.GetConnectedOutput()
#                             if connectedOutput:
#                                 connectedtool = connectedOutput.GetTool()
#                                 if not connectedtool.Name in nodenames:
#                                     mergednodes.append(connectedtool)
#                         if newnode.GetAttrs("TOOLS_RegID") == "Merge3D" and len(mergednodes) > 0:
#                             newsceneinputs = [input for input in newnode.GetInputList().values() if "SceneInput" in input.Name]
#                             for mergednode in mergednodes:
#                                 for input in newsceneinputs:
#                                     connectedOutput = input.GetConnectedOutput()
#                                     if not connectedOutput:
#                                         newnode.ConnectInput(input.Name, mergednode)
#             # Match position.
#             self.matchNodePos(newnode, oldnode)
#             positionednodes.append(newnode.Name)
        
#     # Return position
#     if sceneNode:
#         return sceneNode, positionednodes
    
#     return None, positionednodes


# @err_catcher(name=__name__)
# def sm_import_updateObjects(self, origin):
#     pass


# @err_catcher(name=__name__)
# def sm_import_removeNameSpaces(self, origin):
#     pass
