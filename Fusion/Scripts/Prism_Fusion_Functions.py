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
import sys
import json
import platform
import time
import BlackmagicFusion as bmd

try:
	from PySide2.QtCore import *
	from PySide2.QtGui import *
	from PySide2.QtWidgets import *
except:
	from PySide.QtCore import *
	from PySide.QtGui import *

import pyautogui
import pyperclip
from PrismUtils.Decorators import err_catcher as err_catcher


class Prism_Fusion_Functions(object):
	def __init__(self, core, plugin):
		self.core = core
		self.plugin = plugin
		self.fusion = bmd.scriptapp("Fusion")

		self.core.registerCallback(
			"onUserSettingsOpen", self.onUserSettingsOpen, plugin=self.plugin
		)
		self.core.registerCallback(
			"onProjectBrowserStartup", self.onProjectBrowserStartup, plugin=self.plugin
		)
		self.core.registerCallback(
			"onStateManagerOpen", self.onStateManagerOpen, plugin=self.plugin
		)
		self.core.registerCallback(
			"onStateCreated", self.onStateCreated, plugin=self.plugin
		)

		self.importHandlers = {
			".abc": {"importFunction": self.importAlembic},
			".fbx": {"importFunction": self.importFBX},
		}

		# self.exportHandlers = {
		# 	".abc": {"exportFunction": self.exportAlembic},
		# 	".fbx": {"exportFunction": self.exportFBX},
		# 	".obj": {"exportFunction": self.exportObj},
		# 	".blend": {"exportFunction": self.exportBlend},
		# }

	@err_catcher(name=__name__)
	def startup(self, origin):
		# 	for obj in QApplication.topLevelWidgets():
		# 		if obj.objectName() == 'FusionWindow':
		# 			QtParent = obj
		# 			break
		# 	else:
		# 		return False
		if platform.system() == "Linux":
			origin.timer.stop()

			if "prism_project" in os.environ and os.path.exists(
				os.environ["prism_project"]
			):
				curPrj = os.environ["prism_project"]
			else:
				curPrj = self.core.getConfig("globals", "current project")

			if curPrj != "":
				self.core.changeProject(curPrj)
			return False

		
		self.core.setActiveStyleSheet("Fusion")
		appIcon = QIcon(
			os.path.join(self.core.prismRoot, "Scripts", "UserInterfacesPrism", "p_tray.png")
		)
		qapp = QApplication.instance()
		qapp.setWindowIcon(appIcon) 

		origin.messageParent = QWidget()
		# 	origin.messageParent.setParent(QtParent, Qt.Window)
		if self.core.useOnTop:
			origin.messageParent.setWindowFlags(
				origin.messageParent.windowFlags() ^ Qt.WindowStaysOnTopHint
			)

		origin.timer.stop()
		origin.startAutosaveTimer()


	@err_catcher(name=__name__)
	def autosaveEnabled(self, origin):
		# get autosave enabled
		return False

	@err_catcher(name=__name__)
	def sceneOpen(self, origin):
		if self.core.shouldAutosaveTimerRun():
			origin.startAutosaveTimer()

	@err_catcher(name=__name__)
	def getCurrentFileName(self, origin, path=True):
		curComp = self.fusion.GetCurrentComp()
		if curComp is None:
			currentFileName = ""
		else:
			currentFileName = self.fusion.GetCurrentComp().GetAttrs()["COMPS_FileName"]

		return currentFileName

	@err_catcher(name=__name__)
	def getSceneExtension(self, origin):
		return self.sceneFormats[0]

	@err_catcher(name=__name__)
	def saveScene(self, origin, filepath, details={}):
		try:
			#Save function returns True on success, False on failure
			return self.fusion.GetCurrentComp().Save(filepath)
		except:
			return False

	@err_catcher(name=__name__)
	def getImportPaths(self, origin):
		prismstates = self.getFusionStatesNode()
		return prismstates.Comments[0].split("_..._")[1]

	@err_catcher(name=__name__)
	def getFrameRange(self, origin):
		startframe = self.fusion.GetCurrentComp().GetAttrs()["COMPN_GlobalStart"]
		endframe = self.fusion.GetCurrentComp().GetAttrs()["COMPN_GlobalEnd"]

		return [startframe, endframe]

	@err_catcher(name=__name__)
	def setFrameRange(self, origin, startFrame, endFrame):
		comp = self.fusion.GetCurrentComp()
		comp.Lock()
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
		comp.Unlock()

	@err_catcher(name=__name__)
	def getFPS(self, origin):
		return self.fusion.GetCurrentComp().GetPrefs()["Comp"]["FrameFormat"]["Rate"]

	@err_catcher(name=__name__)
	def setFPS(self, origin, fps):
		return self.fusion.GetCurrentComp().SetPrefs({"Comp.FrameFormat.Rate": fps})

	@err_catcher(name=__name__)
	def getResolution(self):
		width = self.fusion.GetCurrentComp().GetPrefs()[
			"Comp"]["FrameFormat"]["Height"]
		height = self.fusion.GetCurrentComp().GetPrefs()[
			"Comp"]["FrameFormat"]["Width"]
		return [width, height]

	@err_catcher(name=__name__)
	def setResolution(self, width=None, height=None):
		self.fusion.GetCurrentComp().SetPrefs(
			{
				"Comp.FrameFormat.Width": width,
				"Comp.FrameFormat.Height": height,
			}
		)

	@err_catcher(name=__name__)
	def updateReadNodes(self):
		updatedNodes = []

		selNodes = self.fusion.GetCurrentComp().GetToolList(True, "Loader")
		if len(selNodes) == 0:
			selNodes = self.fusion.GetCurrentComp().GetToolList(False, "Loader")

		if len(selNodes):
			comp = self.fusion.GetCurrentComp()
			comp.StartUndo("Updating loaders")
			for k in selNodes:
				i = selNodes[k]
				curPath = comp.MapPath(i.GetAttrs()["TOOLST_Clip_Name"][1])

				newPath = self.core.getLatestCompositingVersion(curPath)

				if os.path.exists(os.path.dirname(newPath)) and not curPath.startswith(
					os.path.dirname(newPath)
				):
					firstFrame = i.GetInput("GlobalIn")
					lastFrame = i.GetInput("GlobalOut")

					i.Clip = newPath

					i.GlobalOut = lastFrame
					i.GlobalIn = firstFrame
					i.ClipTimeStart = 0
					i.ClipTimeEnd = lastFrame - firstFrame
					i.HoldLastFrame = 0

					updatedNodes.append(i)
			comp.EndUndo(True)

		if len(updatedNodes) == 0:
			QMessageBox.information(
				self.core.messageParent, "Information", "No nodes were updated"
			)
		else:
			mStr = "%s nodes were updated:\n\n" % len(updatedNodes)
			for i in updatedNodes:
				mStr += i.GetAttrs()["TOOLS_Name"] + "\n"

			QMessageBox.information(
				self.core.messageParent, "Information", mStr)

	@err_catcher(name=__name__)
	def getAppVersion(self, origin):
		return self.fusion.Version

	@err_catcher(name=__name__)
	def openScene(self, origin, filepath, force=False):
		if os.path.splitext(filepath)[1] not in self.sceneFormats:
			return False

		try:
			self.fusion.LoadComp(filepath)
		except:
			pass

		return True

	

	#STATE MANAGER
	@err_catcher(name=__name__)
	def sm_export_addObjects(self, origin, objects=None):
		if not objects:
			objects = []  # get selected objects from scene

		for i in objects:
			if not i in origin.nodes:
				origin.nodes.append(i)

		origin.updateUi()
		origin.stateManager.saveStatesToScene()

	@err_catcher(name=__name__)
	def getNodeName(self, origin, node):
		if self.isNodeValid(origin, node):
			try:
				return node["name"]
			except:
				QMessageBox.warning(
					self.core.messageParent, "Warning", "Cannot get name from %s" % node
				)
				return node
		else:
			return "invalid"

	@err_catcher(name=__name__)
	def selectNodes(self, origin):
		if origin.lw_objects.selectedItems() != []:
			nodes = []
			for i in origin.lw_objects.selectedItems():
				node = origin.nodes[origin.lw_objects.row(i)]
				if self.isNodeValid(origin, node):
					nodes.append(node)
			# select(nodes)

	@err_catcher(name=__name__)
	def isNodeValid(self, origin, handle):
		return True

	@err_catcher(name=__name__)
	def getCamNodes(self, origin, cur=False):
		sceneCams = []  # get cams from scene
		if cur:
			sceneCams = ["Current View"] + sceneCams

		return sceneCams

	@err_catcher(name=__name__)
	def getCamName(self, origin, handle):
		if handle == "Current View":
			return handle

		return str(nodes[0])

	@err_catcher(name=__name__)
	def selectCam(self, origin):
		if self.isNodeValid(origin, origin.curCam):
			select(origin.curCam)

	@err_catcher(name=__name__)
	def sm_export_startup(self, origin):
		pass

	# 	@err_catcher(name=__name__)
	# 	def sm_export_setTaskText(self, origin, prevTaskName, newTaskName):
	# 		origin.l_taskName.setText(newTaskName)

	@err_catcher(name=__name__)
	def sm_export_removeSetItem(self, origin, node):
		pass

	@err_catcher(name=__name__)
	def sm_export_clearSet(self, origin):
		pass

	@err_catcher(name=__name__)
	def sm_export_updateObjects(self, origin):
		pass

	@err_catcher(name=__name__)
	def sm_export_exportShotcam(self, origin, startFrame, endFrame, outputName):
		result = self.sm_export_exportAppObjects(
			origin,
			startFrame,
			endFrame,
			(outputName + ".abc"),
			nodes=[origin.curCam],
			expType=".abc",
		)
		result = self.sm_export_exportAppObjects(
			origin,
			startFrame,
			endFrame,
			(outputName + ".fbx"),
			nodes=[origin.curCam],
			expType=".fbx",
		)
		return result

	@err_catcher(name=__name__)
	def sm_export_exportAppObjects(
		self,
		origin,
		startFrame,
		endFrame,
		outputName,
		scaledExport=False,
		nodes=None,
		expType=None,
	):
		pass

	@err_catcher(name=__name__)
	def sm_export_preDelete(self, origin):
		pass

	@err_catcher(name=__name__)
	def sm_export_unColorObjList(self, origin):
		origin.lw_objects.setStyleSheet(
			"QListWidget { border: 3px solid rgb(50,50,50); }"
		)

	@err_catcher(name=__name__)
	def sm_export_typeChanged(self, origin, idx):
		pass

	@err_catcher(name=__name__)
	def sm_export_preExecute(self, origin, startFrame, endFrame):
		warnings = []

		return warnings

	@err_catcher(name=__name__)
	def sm_export_loadData(self, origin, data):
		pass

	@err_catcher(name=__name__)
	def sm_export_getStateProps(self, origin, stateProps):
		stateProps.update()

		return stateProps

	################################################
	#                                              #
	#                    RENDER                    #
	#                                              #
	################################################

	@err_catcher(name=__name__)
	def sm_render_startup(self, origin):
		pass

	@err_catcher(name=__name__)
	def sm_render_getRenderLayer(self, origin):
		rlayerNames = []

		return rlayerNames

	@err_catcher(name=__name__)
	def sm_render_refreshPasses(self, origin):
		pass

	@err_catcher(name=__name__)
	def sm_render_openPasses(self, origin, item=None):
		pass

	@err_catcher(name=__name__)
	def removeAOV(self, aovName):
		pass

	@err_catcher(name=__name__)
	def posRelativeToNode(self, node, xoffset=3):
		comp = self.fusion.GetCurrentComp()
		flow = comp.CurrentFrame.FlowView
		#check if there is selection
		if len(comp.GetToolList(True).values()) > 0:
			activeNode = comp.ActiveTool()
			if not activeNode.Name == node.Name:
				postable = flow.GetPosTable(activeNode)
				if postable:
					x, y = postable.values()
					flow.SetPos(node, x + xoffset, y)
					node.ConnectInput('Input', activeNode)
					return True

		return False

	@err_catcher(name=__name__)
	def stackNodesByType(self, nodetostack, yoffset=3, tooltype="Saver"):
		comp = self.fusion.GetCurrentComp()
		flow = comp.CurrentFrame.FlowView

		origx, origy = flow.GetPosTable(nodetostack).values()

		toollist = comp.GetToolList().values()
		
		thresh_y_position = -float('inf')
		upmost_node = None		

		# Find the upmost node
		for node in toollist:
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

		if upmost_node:
			#set pos to the leftmost or rightmost node
			flow.SetPos(nodetostack, origx, thresh_y_position + yoffset)

	@err_catcher(name=__name__)
	def rendernode_exists(self, nodename):
		comp = self.fusion.GetCurrentComp()
		sv = comp.FindTool(nodename)
		if sv is None:
			return False
		return True

	@err_catcher(name=__name__)
	def get_rendernode(self, nodename):
		comp = self.fusion.GetCurrentComp()
		return comp.FindTool(nodename)

	@err_catcher(name=__name__)
	def create_rendernode(self, nodename):
		comp = self.fusion.GetCurrentComp()
		if not self.rendernode_exists(nodename):
			comp.Lock()
			sv = comp.Saver()
			comp.Unlock()
			sv.SetAttrs({'TOOLS_Name' : nodename})
			if not self.posRelativeToNode(sv):
				#Move Render Node to the Right of the scene	
				self.setSmNodePosition(sv, min=False, xoffset=5, ignoreNodeType="Saver")
				self.stackNodesByType(sv)
		return sv

	@err_catcher(name=__name__)
	def sm_render_preSubmit(self, origin, rSettings):
		pass

	@err_catcher(name=__name__)
	def sm_render_startLocalRender(self, origin, outputName, rSettings):
		print(rSettings)
		comp = self.fusion.GetCurrentComp()
		outputName = rSettings["outputName"]
		sv = self.get_rendernode(origin.get_rendernode_name())
		#if sv is not None
		if sv:
			#if sv has input
			if sv.Input.GetConnectedOutput():
				sv.Clip = outputName
			else:
				return "Error (Render Node is not connected)"
		else:
			return "Error (Render Node does not exist)"
		
		frstart = rSettings["startFrame"]
		frend = rSettings["endFrame"]
		
		if origin.chb_resOverride.isChecked():
			wdt = origin.sp_resWidth.value()
			Hhgt = origin.sp_resHeight.value()
	
			comp.Render({'Tool': sv, 'Wait': True, 'FrameRange': f'{frstart}..{frend}','SizeType': -1, 'Width': wdt, 'Height': Hhgt})
		else:
			comp.Render({'Tool': sv, 'Wait': True, 'FrameRange': f'{frstart}..{frend}'})

		if len(os.listdir(os.path.dirname(outputName))) > 0:
			return "Result=Success"
		else:
			return "unknown error (files do not exist)"

	@err_catcher(name=__name__)
	def sm_render_undoRenderSettings(self, origin, rSettings):
		pass

	@err_catcher(name=__name__)
	def sm_render_getDeadlineParams(self, origin, dlParams, homeDir):
		pass

	@err_catcher(name=__name__)
	def getCurrentRenderer(self, origin):
		return "Renderer"

	@err_catcher(name=__name__)
	def getCurrentSceneFiles(self, origin):
		curFileName = self.core.getCurrentFileName()
		scenefiles = [curFileName]
		return scenefiles

	@err_catcher(name=__name__)
	def sm_render_getRenderPasses(self, origin):
		return []

	@err_catcher(name=__name__)
	def sm_render_addRenderPass(self, origin, passName, steps):
		pass

	@err_catcher(name=__name__)
	def sm_render_preExecute(self, origin):
		warnings = []

		return warnings

	@err_catcher(name=__name__)
	def getProgramVersion(self, origin):
		return "1.0"

	@err_catcher(name=__name__)
	def sm_render_getDeadlineSubmissionParams(self, origin, dlParams, jobOutputFile):
		dlParams["Build"] = dlParams["build"]
		dlParams["OutputFilePath"] = os.path.split(jobOutputFile)[0]
		dlParams["OutputFilePrefix"] = os.path.splitext(
			os.path.basename(jobOutputFile)
		)[0]
		dlParams["Renderer"] = self.getCurrentRenderer(origin)

		if origin.chb_resOverride.isChecked() and "resolution" in dlParams:
			resString = "Image"
			dlParams[resString + "Width"] = str(origin.sp_resWidth.value())
			dlParams[resString + "Height"] = str(origin.sp_resHeight.value())

		return dlParams

	@err_catcher(name=__name__)
	def deleteNodes(self, origin, handles, num=0):
		for i in handles:
			comp = self.fusion.CurrentComp
			toolnm = i["name"]
			tool = comp.FindTool(toolnm)
			if tool:
				tool.Delete()

	################################################
	#                                              #
	#                 IMPORTIMAGES                 #
	#                                              #
	################################################
	@err_catcher(name=__name__)
	def reloadLoader(self, node, filePath, firstframe, lastframe):
		if node.GetAttrs("TOOLS_RegID") == 'Loader':
			node = node
			loaderPath = filePath
			loaderName = node.GetAttrs("TOOLS_Name")

			# Rename the clipname to force reload duration
			node.Clip = loaderPath
			node.GlobalIn[0] = firstframe
			node.GlobalOut[0] = lastframe

			# ClipsReaload
			node.SetAttrs({"TOOLB_PassThrough": True})
			node.SetAttrs({"TOOLB_PassThrough": False})

	@err_catcher(name=__name__)
	def importImages(self, origin):
		print(f'origin: {origin}\norigin.origin: {origin.origin}')
		for aov in origin.origin.getCurrentAOV():
			val = origin.origin.getCurrentAOV()[aov]
			print(f'{aov} : {val}')

		if origin.origin.getCurrentAOV():
			fString = "Please select an import option:"
			buttons = ["Current AOV", "All AOVs", "Layout all AOVs"]
			result = self.core.popupQuestion(fString, buttons=buttons, icon=QMessageBox.NoIcon)
		else:
			result = "Current AOV"

		if result == "Current AOV":
			self.fusionImportSource(origin)
		elif result == "All AOVs":
			self.fusionImportPasses(origin)
		# elif result == "Layout all AOVs":
		# 	self.fusionLayout(origin)
		else:
			return
	@err_catcher(name=__name__)
	def fusionImportSource(self, origin):
		comp = self.fusion.GetCurrentComp()
		sourceData = origin.compGetImportSource()

		for i in sourceData:
			curfr = int(comp.CurrentTime)
			filePath = i[0].replace("####", f"{curfr:0{4}}")
			firstFrame = i[1]
			lastFrame = i[2]			
			aovNm = os.path.dirname(filePath).split("/")[-1]

			comp.Lock()
			node = comp.AddTool("Loader")
			self.reloadLoader(node, filePath, firstFrame, lastFrame)
			node.SetAttrs({"TOOLS_Name": aovNm})
			comp.Unlock()

	@err_catcher(name=__name__)
	def fusionImportPasses(self, origin):
		sourceData = origin.compGetImportPasses()
		#print(sourceData)
		# for i in sourceData:
		# 	filePath = i[0]
		# 	firstFrame = i[1]
		# 	lastFrame = i[2]

		# 	node = nuke.createNode(
		# 		"Read",
		# 		"file \"%s\"" % filePath,
		# 		False,
		# 	)
		# 	if firstFrame is not None:
		# 		node.knob("first").setValue(firstFrame)
		# 	if lastFrame is not None:
		# 		node.knob("last").setValue(lastFrame)

	@err_catcher(name=__name__)
	def nukeLayout(self, origin):
		msg = "This feature is disabled"
		self.core.popup(msg)
		return

	################################################
	#                                              #
	#                   IMPORT3D                   #
	#                                              #
	################################################
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

	@err_catcher(name=__name__)
	def importFormatByUI(self, origin, formatCall, filepath, global_scale, options = None, interval = 0.05):
		origin.stateManager.showMinimized()

		fusion = self.fusion
		comp = fusion.GetCurrentComp()
		#comp.Lock()
		flow = comp.CurrentFrame.FlowView
		flow.Select(None)

		if not os.path.exists(filepath):
			QMessageBox.warning(
				self.core.messageParent, "Warning", "File %s does not exists" % filepath
			)

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
		
		#Call the dialog
		fusion.QueueAction("Utility_Show", {"id":formatCall})
		time.sleep(interval)
		pyautogui.typewrite(filepath)
		time.sleep(interval)
		pyautogui.press("enter")
		pyautogui.press("enter")
		
		elapsedtime = 0
		#comp.Unlock()
		while len(comp.GetToolList(True))<0 and elapsedtime < 10:
			loopinterval = 0.1
			elapsedtime += loopinterval
			time.sleep(loopinterval)

		origin.stateManager.showNormal()

		if len(comp.GetToolList(True)) > 0:
			return True
		else:
			return False


	@err_catcher(name=__name__)
	def importAlembic(self, importPath, origin):
		return self.importFormatByUI(origin = origin, formatCall="AbcImport", filepath=importPath,global_scale=100, options = self.abc_options)

	@err_catcher(name=__name__)
	def importFBX(self, importPath, origin):
		return self.importFormatByUI(origin = origin, formatCall="FBXImport", filepath=importPath,global_scale=100)


	@err_catcher(name=__name__)
	def sm_import_disableObjectTracking(self, origin):
		self.deleteNodes(origin, [origin.setName])

	#Main Import function
	@err_catcher(name=__name__)
	def sm_import_importToApp(self, origin, doImport, update, impFileName):
		comp = self.fusion.GetCurrentComp()
		flow = comp.CurrentFrame.FlowView
		fileName = os.path.splitext(os.path.basename(impFileName))
		origin.setName = ""
		result = False
		#try to get an active tool to set a ref position
		activetool = None
		try:
			activetool = comp.ActiveTool()
		except:
			pass
		#if there is no active tool we use the note tool for the StateManager as a reference 
		if not activetool:
			activetool = self.getFusionStatesNode()
		
		#get Extension
		ext = fileName[1].lower()

		#if extension is supported
		if ext in self.importHandlers:
			self.cleanbeforeImport(origin)
			result = self.importHandlers[ext]["importFunction"](impFileName, origin)
		else:
			self.core.popup("Format is not supported.")
			return {"result": False, "doImport": doImport}

		#After import update the stateManager interface
		if result:
			#Set the position of the imported nodes relative to the previously active tool
			if activetool is not None:
				#print("locs")
				impnodes = [n for n in comp.GetToolList(True).values()]
				#print(impnodes)
				if len(impnodes) > 0:
					comp.Lock()

					fisrtnode = impnodes[0]
					fstnx, fstny = flow.GetPosTable(fisrtnode).values()

					for n in impnodes:
						#print("locs")
						atx, aty = flow.GetPosTable(activetool).values()
						x,y  = flow.GetPosTable(n).values()

						offset = [x-fstnx,y-fstny]
						newx = x+(atx-x)+offset[0]
						newy = y+(aty-y)+offset[1]
						flow.SetPos(n, newx-1, newy)

					comp.Unlock()
			##########

			newNodes = [n.Name for n in comp.GetToolList(True).values()]
			importedNodes = []
			for i in newNodes:
				#if i not in existingNodes:
				##...
				importedNodes.append(self.getNode(i))

			origin.setName = "Import_" + fileName[0]			
			origin.nodes = importedNodes
			#Deseleccionar todo
			flow.Select()

			objs = [self.getObject(x) for x in importedNodes]
			
			#select nodes in comp
			for o in objs:
				flow.Select(o)

			#Set result to True if we have nodes
			result = len(importedNodes) > 0

		return {"result": result, "doImport": doImport}


	@err_catcher(name=__name__)
	def getNode(self, obj):
		if type(obj) == str:
			node = {"name": obj}
		elif type(obj) == dict:
			node = {"name": obj["name"]}
		else:
			node = {"name": obj.Name}
		return node

	@err_catcher(name=__name__)
	def getObject(self, node):
		comp = self.fusion.GetCurrentComp()
		if type(node) == str:
			node = self.getNode(node)

		return comp.FindTool(node["name"])

	def cleanbeforeImport(self, origin):
		# print(f"origin setname: {origin.setName}")
		# print(f"origin nodes: {origin.nodes}")
		if origin.nodes == []:
			return
		nodes = []
		for o in origin.nodes:
			nodes.append(self.getNode(o))

		self.deleteNodes(origin, nodes)
		origin.nodes = []

	@err_catcher(name=__name__)
	def sm_import_updateObjects(self, origin):
		pass

	@err_catcher(name=__name__)
	def sm_import_removeNameSpaces(self, origin):
		print("removing namespaces")
		pass

	################################################
	#                                              #
	#                    PLAYBLAST                 #
	#                                              #
	################################################
	@err_catcher(name=__name__)
	def sm_playblast_startup(self, origin):
		frange = self.getFrameRange(origin)
		origin.sp_rangeStart.setValue(frange[0])
		origin.sp_rangeEnd.setValue(frange[1])

	@err_catcher(name=__name__)
	def sm_playblast_createPlayblast(self, origin, jobFrames, outputName):
		pass

	@err_catcher(name=__name__)
	def sm_playblast_preExecute(self, origin):
		warnings = []

		return warnings

	@err_catcher(name=__name__)
	def sm_playblast_execute(self, origin):
		pass

	@err_catcher(name=__name__)
	def sm_playblast_postExecute(self, origin):
		pass

	@err_catcher(name=__name__)
	def sm_createRenderPressed(self, origin):
		origin.createPressed("Render")

	################################################
	#                                              #
	#        	  STATE MANAGER STUFF              #
	#                                              #
	################################################

	@err_catcher(name=__name__)
	def sm_getExternalFiles(self, origin):
		extFiles = []
		return [extFiles, []]

	@err_catcher(name=__name__)
	def setSmNodePosition(self, smnode, min=True, xoffset=-2, ignoreNodeType=None):
		# Get the active composition
		comp = self.fusion.GetCurrentComp()
		flow = comp.CurrentFrame.FlowView

		if comp:
			# Get all nodes in the composition
			all_nodes = comp.GetToolList(False).values()

			if all_nodes:
				# Initialize variables to track the leftmost node
				xmost_node, upmost_node = None, None
				
				thresh_x_position, thresh_y_position = 0, 0
				if min:
					thresh_x_position, thresh_y_position = float('inf'), float('inf')  # Initialize with positive infinity
				else:
					thresh_x_position, thresh_y_position = -float('inf'), float('inf')  # Initialize with negative infinity

				# Iterate through all nodes
				for node in all_nodes:
					# Skip the SM node
					if node.Name == smnode.Name:
						continue

					# Skip nodes with the ignoreNodeType
					if ignoreNodeType:
							if node.GetAttrs("TOOLS_RegID") == ignoreNodeType:
								continue

					
					postable = flow.GetPosTable(node)
					x,y = thresh_x_position, thresh_y_position
					#check if node has a postable.
					if postable:
						# Get the node's position
						x,y = postable.values()
					
					# Check if the X-coordinate is smaller than the current minimum or larger than the current maximum
					xthresh, ythresh = False, False
     
					if min:
						xthresh = x < thresh_x_position
						ythresh = y < thresh_y_position
					else:
						xthresh = x > thresh_x_position
						ythresh = y < thresh_y_position

					if xthresh:
						thresh_x_position = x
						xmost_node = node

					if ythresh:
						thresh_y_position = y
						upmost_node = node

				if xmost_node:
					#set pos to the leftmost or rightmost node
					flow.SetPos(smnode, thresh_x_position + xoffset, thresh_y_position)
				else:
					flow.SetPos(smnode, 0, 0)
			else:
				flow.SetPos(smnode, 0, 0)
		else:
			print("No active composition.")

	@err_catcher(name=__name__)
	def makeFusionStatesNode(self):
		comp = self.fusion.GetCurrentComp()
		clip = """{
	Tools = ordered() {
		DO_NOT_DELETE_PrismSM = Note {
			Locked = true,
			CtrlWZoom = false,
			NameSet = true,
			Inputs = {
				Comments = Input { Value = "{\\n    \\"states\\": [\\n        {\\n            \\"statename\\": \\"publish\\",\\n            \\"comment\\": \\"\\",\\n            \\"description\\": \\"\\"\\n        }\\n    ]\\n}_..._", }
			},
			ViewInfo = StickyNoteInfo {
				Pos = { 388.667, 1.30299 },
				Flags = {
					Expanded = true
				},
				Size = { 86, 16.3636 }
			},
			Colors = { TileColor = { R = 0.0, G = 0.0, B = 1.0 }, }
		}
	},
	ActiveTool = "DO_NOT_DELETE_PrismSM"
}"""

		pyperclip.copy(clip)
		comp.Paste(clip)

	@err_catcher(name=__name__)
	def getFusionStatesNode(self):
		comp = self.fusion.CurrentComp
		smnode = comp.FindTool("DO_NOT_DELETE_PrismSM")
		if smnode == None:
			self.makeFusionStatesNode()
			smnode = comp.ActiveTool
			self.setSmNodePosition(smnode)

		return smnode

	@err_catcher(name=__name__)
	def sm_saveStates(self, origin, buf):
		prismstates = self.getFusionStatesNode()
		prismstates.Comments = buf + "_..._"

	@err_catcher(name=__name__)
	def sm_saveImports(self, origin, importPaths):
		prismstates = self.getFusionStatesNode()
		prismstates.Comments[0] += importPaths.replace("\\\\", "\\")

	@err_catcher(name=__name__)
	def sm_readStates(self, origin):
		prismstates = self.getFusionStatesNode()
		return prismstates.Comments[0].split("_..._")[0]

	@err_catcher(name=__name__)
	def sm_deleteStates(self, origin):
		prismstates = self.getFusionStatesNode()
		prismstates.Comments = ""


	################################################
	#                                              #
	#        	       CALLBACKS                   #
	#                                              #
	################################################

	@err_catcher(name=__name__)
	def onUserSettingsOpen(self, origin):
		pass

	@err_catcher(name=__name__)
	def onProjectBrowserStartup(self, origin):
		pass

	@err_catcher(name=__name__)
	def onStateManagerOpen(self, origin):
		#Remove Export and Playblast buttons and states
		origin.b_createExport.deleteLater()
		origin.b_createPlayblast.deleteLater()
		sm = self.core.getStateManager()
		removestates = ['Code', 'Export', 'Playblast']
		for state in removestates:
			if state in sm.stateTypes.keys():
				del sm.stateTypes[state]
	
		#origin.gb_import.setStyleSheet("margin-top: 20px;")

	@err_catcher(name=__name__)
	def onStateCreated(self, origin, state, stateData):
		if state.className == "ImageRender":
			state.b_resPresets.setStyleSheet("padding-left: 1px;padding-right: 1px;")
		elif state.className == "Playblast":
			state.b_resPresets.setStyleSheet("padding-left: 1px;padding-right: 1px;")