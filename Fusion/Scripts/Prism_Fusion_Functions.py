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
import re
import pygetwindow as gw
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
		self.monkeypatchedsm = None # Reference to the state manager to be used on the monkeypatched functions.
		self.popup = None # Reference of popUp dialog that shows before openning a window when it takes some time.

		self.listener = None
		
		self.saveUI = None
		self.smUI = None
		self.pbUI = None
		self.prefUI = None

		self.core.registerCallback(
			"onUserSettingsOpen", self.onUserSettingsOpen, plugin=self.plugin
		)
		self.core.registerCallback(
			"onProjectBrowserStartup", self.onProjectBrowserStartup, plugin=self.plugin
		)
		self.core.registerCallback(
			"onProjectBrowserClose", self.onProjectBrowserClose, plugin=self.plugin
		)		
		self.core.registerCallback(
			"onProjectBrowserShow", self.onProjectBrowserShow, plugin=self.plugin
		)
		self.core.registerCallback(
			"onProjectBrowserCalled", self.onProjectBrowserCalled, plugin=self.plugin
		)
		self.core.registerCallback(
			"onStateManagerCalled", self.onStateManagerCalled, plugin=self.plugin
		)
		self.core.registerCallback(
			"onStateManagerOpen", self.onStateManagerOpen, plugin=self.plugin
		)
		self.core.registerCallback(
			"onStateManagerClose", self.onStateManagerClose, plugin=self.plugin
		)
		self.core.registerCallback(
			"onStateManagerShow", self.onStateManagerShow, plugin=self.plugin
		)
		self.core.registerCallback(
			"onStateCreated", self.onStateCreated, plugin=self.plugin
		)
		self.core.registerCallback(
			"onStateDeleted", self.onStateDeleted, plugin=self.plugin
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
	def getCurrentFileName(self, origin=None, path=True):
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

	# @err_catcher(name=__name__)
	# def updateReadNodes(self):
	# 	updatedNodes = []

	# 	selNodes = self.fusion.GetCurrentComp().GetToolList(True, "Loader")
	# 	if len(selNodes) == 0:
	# 		selNodes = self.fusion.GetCurrentComp().GetToolList(False, "Loader")

	# 	if len(selNodes):
	# 		comp = self.fusion.GetCurrentComp()
	# 		comp.StartUndo("Updating loaders")
	# 		for k in selNodes:
	# 			i = selNodes[k]
	# 			curPath = comp.MapPath(i.GetAttrs()["TOOLST_Clip_Name"][1])

	# 			newPath = self.core.getLatestCompositingVersion(curPath)

	# 			if os.path.exists(os.path.dirname(newPath)) and not curPath.startswith(
	# 				os.path.dirname(newPath)
	# 			):
	# 				firstFrame = i.GetInput("GlobalIn")
	# 				lastFrame = i.GetInput("GlobalOut")

	# 				i.Clip = newPath

	# 				i.GlobalOut = lastFrame
	# 				i.GlobalIn = firstFrame
	# 				i.ClipTimeStart = 0
	# 				i.ClipTimeEnd = lastFrame - firstFrame
	# 				i.HoldLastFrame = 0

	# 				updatedNodes.append(i)
	# 		comp.EndUndo(True)

	# 	if len(updatedNodes) == 0:
	# 		QMessageBox.information(
	# 			self.core.messageParent, "Information", "No nodes were updated"
	# 		)
	# 	else:
	# 		mStr = "%s nodes were updated:\n\n" % len(updatedNodes)
	# 		for i in updatedNodes:
	# 			mStr += i.GetAttrs()["TOOLS_Name"] + "\n"

	# 		QMessageBox.information(
	# 			self.core.messageParent, "Information", mStr)

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
	def setNodePassthrough(self, nodename, passThrough):
		node = self.get_rendernode(nodename)
		node.SetAttrs({"TOOLB_PassThrough": passThrough})

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
				self.setSmNodePosition(sv, find_min=False, x_offset=10, ignore_node_type="Saver")
				self.stackNodesByType(sv)
		return sv

	@err_catcher(name=__name__)
	def sm_render_preSubmit(self, origin, rSettings):
		pass

	#Function called from MediaProducts.py to fix the output path for Fusion.
	@err_catcher(name=__name__)
	def sm_render_fixOutputPath(self, origin, path, singleFrame=False):
		directory, filename = os.path.split(path)
		name, extension = os.path.splitext(filename)
		new_filename = f"{name}_.{extension}"
		newPath = os.path.join(directory, new_filename)
		return newPath

	@err_catcher(name=__name__)
	def sm_render_startLocalRender(self, origin, outputPathOnly, outputName, rSettings):
		print(rSettings)
		comp = self.fusion.GetCurrentComp()

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
		
		# Are we just stiing the path and version into the render nodes or are we executing a local render?
		if outputPathOnly:

			return "Result=Success"

		else:
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
		dlParams["jobInfoFile"] = os.path.join(
			homeDir, "temp", "fusion_submit_info.job"
		)
		dlParams["pluginInfoFile"] = os.path.join(
			homeDir, "temp", "fusion_plugin_info.job"
		)

		dlParams["jobInfos"]["Plugin"] = "Fusion"
		dlParams["jobInfos"]["Comment"] = "Prism-Submission-Fusion_ImageRender"
		dlParams["pluginInfos"]["OutputFile"] = dlParams["jobInfos"]["OutputFilename0"]

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
		# print(f'origin: {origin}\norigin.origin: {origin.origin}')
		# for aov in origin.origin.getCurrentAOV():
		# 	val = origin.origin.getCurrentAOV()[aov]
		# 	print(f'{aov} : {val}')

		if origin.origin.getCurrentAOV():
			fString = "Please select an import option:"
			buttons = ["Current AOV", "All AOVs", "Update Selected"]
			result = self.core.popupQuestion(fString, buttons=buttons, icon=QMessageBox.NoIcon)
		else:
			result = "Current AOV"

		if result == "Current AOV":
			self.fusionImportSource(origin)
		elif result == "All AOVs":
			self.fusionImportPasses(origin)
		elif result == "Update Selected":
			self.fusionUpdateSelectedPasses(origin)
		else:
			return

	@err_catcher(name=__name__)
	def fusionImportSource(self, origin):
		comp = self.fusion.GetCurrentComp()
		flow = comp.CurrentFrame.FlowView

		# deselect all nodes
		flow.Select()

		sourceData = origin.compGetImportSource()
		imageData = self.getImageData(comp, sourceData)
		if imageData:
			self.processImageImport(comp, flow, imageData)

	@err_catcher(name=__name__)
	def fusionImportPasses(self, origin):
		comp = self.fusion.GetCurrentComp()
		flow = comp.CurrentFrame.FlowView

		fString = "Some EXRs seem to have multiple channels:\n" + "Do you want to split the EXR channels into individual nodes?"
		splithandle = {'splitchosen': False, 'splitfirstasked': True, 'fstring': fString}
		updatehandle = {'updatednodes': [], 'updatelog': []}

		# deselect all nodes
		flow.Select()

		dataSources = origin.compGetImportPasses()
		for sourceData in dataSources:
			imageData = self.getPassData(comp, sourceData)
			self.processImageImport(comp, flow, imageData, splithandle=splithandle, updatehandle=updatehandle)

		if len(updatehandle["updatelog"]) > 0:
			fString = "The following nodes were updated:\n"
			updatedNodes = updatehandle["updatelog"]
			for node in updatedNodes:
				if node['oldv'] != node['newv']:
					fString += f"{node['name']}: v {node['oldv']} -> v {node['newv']}\n"
					nodeToSelect = comp.FindTool(node['name'])
					flow.Select(nodeToSelect, True)
			self.core.popupQuestion(fString, buttons=['ok'], icon=QMessageBox.NoIcon)
			return

	@err_catcher(name=__name__)
	def fusionUpdateSelectedPasses(self, origin):
		comp = self.fusion.GetCurrentComp()
		flow = comp.CurrentFrame.FlowView
	
		# from selection grab only loaders
		loaders = comp.GetToolList(True, "Loader").values()
		
		if not loaders:
			return

		# deselect all nodes
		flow.Select()

		dataSources = origin.compGetImportPasses()
		updatelog = []
		for sourceData in dataSources:
			imageData = self.getPassData(comp, sourceData)
			updatedPaths, updatedNodes = self.updateLoaders(loaders, imageData['filePath'], imageData['firstFrame'], imageData['lastFrame'])
			if updatedPaths:
				for node in updatedNodes:
					updatelog.append(node)
				continue
		
		wasVersionChanged = False
		if len(updatelog) > 0:
			fString = "The following nodes were updated:\n"
			allUpdatedNodes = updatelog
			for node in allUpdatedNodes:
				if node['oldv'] != node['newv']:
					wasVersionChanged = True
					fString += f"{node['name']}: v {node['oldv']} -> v {node['newv']}\n"
					nodeToSelect = comp.FindTool(node['name'])
					flow.Select(nodeToSelect, True)
			if wasVersionChanged:
				self.core.popupQuestion(fString, buttons=['ok'], icon=QMessageBox.NoIcon)
			else:
				self.core.popupQuestion("Nodes were updated but no version was changed", buttons=['ok'], icon=QMessageBox.NoIcon)
			return
		else:
			self.core.popupQuestion("Nothing was updated", buttons=['ok'], icon=QMessageBox.NoIcon)

	@err_catcher(name=__name__)
	def returnImageDataDict(self, filePath, firstFrame, lastFrame, aovNm):
		return {
		'filePath': filePath, 
		'firstFrame': firstFrame, 
		'lastFrame': lastFrame, 
		'aovNm': aovNm
		}


	@err_catcher(name=__name__)
	def getImageData(self, comp, sourceData):
		curfr = int(comp.CurrentTime)	
		# check if the source data is interpreting the image sequence as individual images.
		image_strings = [item[0] for item in sourceData if isinstance(item[0], str)]
		if len(image_strings) > 1:
			imagepath = self.is_image_sequence(image_strings)
			if imagepath:
				filePath = imagepath.replace("####", f"{curfr:0{4}}")
				firstFrame = 1
				lastFrame = len(image_strings)	
				aovNm = 'PrismLoader'

				return self.returnImageDataDict(filePath, firstFrame, lastFrame, aovNm)
		else:
			# Break the meaningless 1 item nested array.
			return self.getPassData(comp, sourceData[0])

		msgStr = "No image sequence was loaded."
		QMessageBox.warning(self.core.messageParent, "Prism Integration", msgStr)
		return None

	@err_catcher(name=__name__)
	def getPassData(self, comp, sourceData):
		curfr = int(comp.CurrentTime)
		
		filePath = sourceData[0].replace("####", f"{curfr:0{4}}")
		firstFrame = sourceData[1]
		lastFrame = sourceData[2]			
		aovNm = os.path.dirname(filePath).split("/")[-1]
    
		return self.returnImageDataDict(filePath, firstFrame, lastFrame, aovNm)

	@err_catcher(name=__name__)
	def updateLoaders(self, Loaders, filePath, firstFrame, lastFrame):
		updatedNodes = []
		areUpdatedPaths = False
		for loader in Loaders:
			loaderClipPath = loader.Clip[0]
			if self.are_paths_equal_except_version(loaderClipPath, filePath):
				version1 = self.extract_version(loaderClipPath)
				version2 = self.extract_version(filePath)
				areUpdatedPaths = True

				self.reloadLoader(loader, filePath, firstFrame, lastFrame)
				updatedNodes.append({'name':loader.Name, 'oldv': str(version1), 'newv': str(version2)})

		return areUpdatedPaths, updatedNodes

	@err_catcher(name=__name__)
	def processImageImport(self, comp, flow, imageData, splithandle=None, updatehandle=None):
		# Do in this function the actual importing or update of the image.

		filePath = imageData['filePath']
		firstFrame = imageData['firstFrame']
		lastFrame = imageData['lastFrame']
		aovNm = imageData['aovNm']
		
		# Check if path without version exists in a loader and if so generate a popup to update with new version.
		allLoaders = comp.GetToolList(False, "Loader").values()
		areUpdatedPaths, updatedNodes = self.updateLoaders(allLoaders, filePath, firstFrame, lastFrame)
		
		# if paths were updated then we return, else we follow to create new nodes.
		if areUpdatedPaths:
			# if we are running the function on multiple AOVs:
			if updatehandle:
				for node in updatedNodes:
					updatehandle['updatelog'].append(node)
				return

			# if we are running the function on a single AOV:
			else:
				fString = "The following nodes were updated:\n"
				for node in updatedNodes:
					if node['oldv'] != node['newv']:
						fString += f"{node['name']}: v {node['oldv']} -> v {node['newv']}\n"
						nodeToSelect = comp.FindTool(node['name'])
						flow.Select(nodeToSelect, True)
				self.core.popupQuestion(fString, buttons=['ok'], icon=QMessageBox.NoIcon)
				return


		# if paths were not updated then we create new nodes.
		comp.Lock()
		node = comp.AddTool("Loader")
		self.reloadLoader(node, filePath, firstFrame, lastFrame)
		node.SetAttrs({"TOOLS_Name": aovNm})
		self.setSmNodePosition(node, x_offset = -5, y_offset = 0)
		comp.Unlock()

		# check if the leftmost node is a Loader to put the nodes below.
		validtools = [t for t in comp.GetToolList(False).values() if flow.GetPosTable(t) and not t.Name == node.Name and not t.Name == 'DO_NOT_DELETE_PrismSM']
		leftmostNode = self.find_leftmost_lower_node(flow, validtools, 0)
		
		if len(comp.GetToolList()) == 1:
			x_pos, y_pos = self.find_LastClickPosition()
			flow.SetPos(node, x_pos, y_pos + 1.5)

		elif leftmostNode.GetAttrs("TOOLS_RegID") == "Loader":
			loaders = [l for l in comp.GetToolList(False, "Loader").values() if not l.Name == node.Name]	
			leftmostLoader = self.find_leftmost_lower_node(flow, loaders, 2.5)
			x_pos, y_pos = flow.GetPosTable(leftmostLoader).values()
			flow.SetPos(node, x_pos, y_pos + 1.5)
		
		# IF IS EXR
		extension = os.path.splitext(filePath)[1]
		if extension == ".exr":
			# check for multichannels
			channels = self.get_loader_channels(node)
			# print("channels: ", channels)
			if len(channels) > 0:
				buttons = ["Yes", "No"]
				# if we need to manage the plit dialog from outside and this is the first time the question is asked.
				if splithandle and splithandle['splitfirstasked']:
					splithandle['splitfirstasked'] = False
					fString = splithandle['fstring']
					result = self.core.popupQuestion(fString, buttons=buttons, icon=QMessageBox.NoIcon)

				elif splithandle and splithandle['splitchosen']:
					result = "Yes"
				elif splithandle and not splithandle['splitchosen']:
					result = "No"

				else:
					fString = "This EXR seems to have multiple channels:\n" + "Do you want to split the EXR channels into individual nodes?"
					result = self.core.popupQuestion(fString, buttons=buttons, icon=QMessageBox.NoIcon)

				if result == "Yes":
					if splithandle:
						splithandle['splitchosen'] = True
					self.process_multichannel(node)
					return
 
				elif splithandle:
					splithandle['splitchosen'] = False

		# create wireless
		self.createWireless(node)
		flow.Select(node, True)
		
		return

	@err_catcher(name=__name__)
	def createWireless(self, tool):
		wirelessCopy = """{
	Tools = ordered() {
		neverreferencednameonwirelesslink = Fuse.Wireless {
			NameSet = true,
			Inputs = {
				Input = Input {
					SourceOp = "neverreferencednameonautodomain",
					Source = "Output",
				},
			},
			ViewInfo = OperatorInfo { Pos = { -433.307, 3.35109 } },
			Colors = { TileColor = { R = 0.92156862745098, G = 0.431372549019608, B = 0 }, }
		},
		neverreferencednameonautodomain = AutoDomain {
			CtrlWZoom = false,
			NameSet = true,
			ViewInfo = OperatorInfo { Pos = { -561.973, 0.926849 } },
			Colors = { TileColor = { R = 0.92156862745098, G = 0.431372549019608, B = 0 }, }
		}
	}
}"""
		comp = self.fusion.GetCurrentComp()
		flow = comp.CurrentFrame.FlowView
		# ad = comp.AutoDomain()

		pyperclip.copy(wirelessCopy)
		comp.Paste(wirelessCopy)
		ad = comp.FindTool("neverreferencednameonautodomain")
		ad.SetAttrs({'TOOLS_Name': tool.Name + '_IN'})
		wl = comp.FindTool("neverreferencednameonwirelesslink")
		wl.SetAttrs({'TOOLS_Name': tool.Name + '_OUT'})
		x_pos, y_pos = flow.GetPosTable(tool).values()

		nodes = [ad, wl]
		for i, node in enumerate(nodes, start=1):
			offset = 1.5 if i == 1 else 1.3
			flow.SetPos(node, x_pos + offset*i, y_pos)

		ad.ConnectInput('Input', tool)


	@err_catcher(name=__name__)
	def find_leftmost_lower_node(self, flow, nodes, threshold):
		leftmost_node = None
		downmost_node = None
		min_x_position = float('inf')
		max_y_position = -float('inf')
		downmost_node_x = float('inf')
		for n in nodes:
			x, y = flow.GetPosTable(n).values()
			if x < min_x_position or leftmost_node is None:
				leftmost_node = (n)
				min_x_position = x
			if y > max_y_position or downmost_node is None:
				downmost_node = (n)
				max_y_position = y
				downmost_node_x = x

		if abs(downmost_node_x - min_x_position) < threshold:
			return downmost_node

		return leftmost_node

	@err_catcher(name=__name__)
	def extract_version(self, filepath):
		# Extract the version information using a regular expression
		match = re.search(r"v(\d{4})", filepath)
		if match:
			return int(match.group(1))
		else:
			return None

	@err_catcher(name=__name__)
	def are_paths_equal_except_version(self, path1, path2):
		# Remove the version part from the paths for exact match comparison
		path1_without_version = re.sub(r"v\d{4}", "", path1)
		path2_without_version = re.sub(r"v\d{4}", "", path2)
		# Check if the non-version parts are an exact match
		if path1_without_version == path2_without_version:
			# Versions are the same, and non-version parts are an exact match
			return True
		else:
			# Versions are the same, but non-version parts are different
			return False


	# EXR CHANNEL MANAGEMENT #
	@err_catcher(name=__name__)
	def get_pattern_prefix(self, string):
		pattern = re.compile(r'^(.+)v\d{4}\.exr$')
		match = pattern.match(string)
		return match.group(1) if match else None

	@err_catcher(name=__name__)
	def is_image_sequence(self, strings):
		first_image_prefix = self.get_pattern_prefix(strings[0])
		if all(self.get_pattern_prefix(item) == first_image_prefix for item in strings):
			return strings[0]
		else:
			return None

	@err_catcher(name=__name__)
	def get_loader_channels(self, tool):
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
		source_channels = tool.Clip1.OpenEXRFormat.RedName.GetAttrs("INPIDT_ComboControl_ID")
		all_channels = []
		# print(source_channels)
		for channel_name in source_channels.values():
			if channel_name.lower() not in skip:
				all_channels.append(channel_name)

		# Sort the channel list
		sorted_channels = sorted(all_channels)

		return sorted_channels

	@err_catcher(name=__name__)
	def get_channel_data(self,loader_channels):
		channel_data = {}

		for channel_name in loader_channels:
			# Get prefix and channel from full channel name using regex
			match = re.match(r"(.+)\.(.+)", channel_name)
			if match:
				prefix, channel = match.groups()

				# Use setdefault to initialize channels if prefix is encountered for the first time
				channels = channel_data.setdefault(prefix, [])

				# Add full channel name to assigned channels of current prefix
				channels.append(channel_name)

		return channel_data

	@err_catcher(name=__name__)
	def GetLoaderClip(self, tool):
		loader_clip = tool.Clip[self.fusion.TIME_UNDEFINED]
		if loader_clip:        
			return loader_clip
		
		print("Loader contains no clips to explore")
		return 

	@err_catcher(name=__name__)
	def move_loaders(self,org_x_pos, org_y_pos, loaders):
		comp = self.fusion.GetCurrentComp()
		flow = comp.CurrentFrame.FlowView
		y_pos_add = 1

		for count, ldr in enumerate(loaders, start=0):
			flow.SetPos(ldr, org_x_pos, org_y_pos + y_pos_add * count)

	@err_catcher(name=__name__)
	def process_multichannel(self, tool):
		comp = self.fusion.GetCurrentComp()
		loader_channels = self.get_loader_channels(tool)
		channel_data = self.get_channel_data(loader_channels)
		flow = comp.CurrentFrame.FlowView
		x_pos, y_pos = flow.GetPosTable(tool).values()

		loaders_list = []

		comp.StartUndo()
		comp.Lock()

		# Invalid names mapping
		invalid_names = {
			'RedName': 'CHANNEL_NO_MATCH',
			'GreenName': 'CHANNEL_NO_MATCH',
			'BlueName': 'CHANNEL_NO_MATCH',
			'AlphaName': 'CHANNEL_NO_MATCH',
			'XName': 'CHANNEL_NO_MATCH',
			'YName': 'CHANNEL_NO_MATCH',
			'ZName': 'CHANNEL_NO_MATCH',
		}

		# Update the loader node channel settings
		for prefix, channels in channel_data.items():
			ldr = comp.Loader({'Clip': self.GetLoaderClip(tool)})

			# Replace invalid EXR channel names with placeholders
			ldr.SetAttrs({'TOOLB_NameSet': True, 'TOOLS_Name': prefix})
			for name, placeholder in invalid_names.items():
				setattr(ldr.Clip1.OpenEXRFormat, name, placeholder)

			# Refresh the OpenEXRFormat setting using real channel name data in a 2nd stage
			for channel_name in channels:
				channel = re.search(r"\.([^.]+)$", channel_name).group(1).lower()

				# Dictionary to map channel types to attribute names
				channel_attributes = {
					'r': 'RedName', 'red': 'RedName',
					'g': 'GreenName', 'green': 'GreenName',
					'b': 'BlueName', 'blue': 'BlueName',
					'a': 'AlphaName', 'alpha': 'AlphaName',
					'x': 'RedName',
					'y': 'GreenName',
					'z': 'BlueName',
				}

				# Handle channels using the mapping
				if channel in channel_attributes:
					setattr(ldr.Clip1.OpenEXRFormat, channel_attributes[channel], channel_name)

				# Handle C4D style channels
				else:
					my_table_of_phrases = re.split(r'\.', channel_name)
					last_item = my_table_of_phrases[-1]

					if last_item in channel_attributes:
						setattr(ldr.Clip1.OpenEXRFormat, channel_attributes[last_item], channel_name)

			loaders_list.append(ldr)

		self.move_loaders(x_pos, y_pos, loaders_list)
		# create IN and OUT nodes.
		for node in loaders_list:
			self.createWireless(node)
			flow.Select(node, True)

		tool.Delete()
		comp.Unlock()
		comp.EndUndo()



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
	def focus_fusion_window(self):
		import subprocess
		# Get all windows
		windows = gw.getAllTitles()

		# Define the pattern using a regular expression
		pattern = r'^Fusion Studio - '
		window_title = "Fusion Studio - ["

		# Filter windows based on the pattern
		matching_windows = [window for window in windows if re.match(pattern, window)]
		# Focus on the first matching window
		if matching_windows:
			script_dir = os.path.dirname(os.path.abspath(__file__))
			batch_file = os.path.join(script_dir, "cmdwin.bat")
			cmdwin = subprocess.Popen(["cmd", "/c", "start", batch_file], shell=True)
			time.sleep(1)	
			
			if not len(matching_windows)>1:	
				matching_window = gw.getWindowsWithTitle(window_title)[0]
				# print("matching_window: ", matching_window.title)
				# matching_window.activate()
				# time.sleep(1)
				# print("active: ", matching_window.isActive)
				if matching_window.isActive:
					return True
				else:
					msg = f"Window with title '{window_title}' is not active.\nTry again leaving the cursor over the Fusion Window."
					self.popup = self.core.popup(msg)
					return False
			else:
				msg = f"There is more than one Window with title '{window_title}' open\nplease close one."
				self.core.popup(msg)
				return False

		else:
			msg = f"Window with title '{window_title}' not found."
			self.core.popup(msg)
			return False
		
		 

	@err_catcher(name=__name__)
	def doUiImport(self, fusion, formatCall, interval, filepath):
		if self.focus_fusion_window():
			comp = fusion.GetCurrentComp()
			#Call the dialog
			fusion.QueueAction("Utility_Show", {"id":formatCall})
			time.sleep(interval)
			pyautogui.typewrite(filepath)
			time.sleep(interval)
			pyautogui.press("enter")
			pyautogui.press("enter")
			
			
			# Wait until file is imported
			elapsedtime = 0
			while len(comp.GetToolList(True))<0 and elapsedtime < 20:
				loopinterval = 0.1
				elapsedtime += loopinterval
				time.sleep(loopinterval)
			if len(comp.GetToolList(True)) > 0:
				return True
			else:
				return False
		else:
			return False


		
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
		
		#Warning
		fString = "Importing this 3Dformat requires UI automation.\n\nPLEASE DO NOT USE THE MOUSE AFTER CLOSING THIS DIALOG UNTIL IMPORT IS DONE"
		buttons = ["Continue"]
		result = self.core.popupQuestion(fString, buttons=buttons, icon=QMessageBox.NoIcon)

		imported = False
		# if result == "Save":
		# 	filepath = self.getCurrentFileName()
		# 	didSave = False
		# 	if not filepath == "":
		# 		if self.core.fileInPipeline():
		# 			didSave = self.core.saveScene(versionUp=False)
		# 		else:
		# 			didSave = self.saveScene(filepath)
		# 		if not didSave == False:
		# 			imported = self.doUiImport(fusion, formatCall, interval, filepath)
		# 	else:
		# 		self.core.popup("Scene can't be saved, save a version first")

		# elif result == "Save new version":
		# 	if self.core.fileInPipeline():
		# 		self.core.saveScene()
		# 		imported = self.doUiImport(fusion, formatCall, interval, filepath)

		# elif result == "Continue":
		# 	imported = self.doUiImport(fusion, formatCall, interval, filepath)

		# else:
		# 	imported = False
  
		imported = self.doUiImport(fusion, formatCall, interval, filepath)
		origin.stateManager.showNormal()

		return imported
		



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
		if activetool:
			atx, aty = flow.GetPosTable(activetool).values()
		else:
			atx, aty = self.find_LastClickPosition()
			
		
		#get Extension
		ext = fileName[1].lower()

		#if extension is supported
		if ext in self.importHandlers:
			# Do the importing
			result = self.importHandlers[ext]["importFunction"](impFileName, origin)
		else:
			self.core.popup("Format is not supported.")
			return {"result": False, "doImport": doImport}

		#After import update the stateManager interface
		if result:
			#check if there was a merge3D in the import and where was it connected to
			newNodes = [n.Name for n in comp.GetToolList(True).values()]
			refPosNode, positionedNodes = self.ReplaceBeforeImport(origin, newNodes)
			self.cleanbeforeImport(origin)
			if refPosNode:
				atx, aty = flow.GetPosTable(refPosNode).values()
	
			importedTools = comp.GetToolList(True).values()
			#Set the position of the imported nodes relative to the previously active tool or last click in compView
			impnodes = [n for n in importedTools]
			#print(impnodes)
			if len(impnodes) > 0:
				comp.Lock()

				fisrtnode = impnodes[0]
				fstnx, fstny = flow.GetPosTable(fisrtnode).values()

				for n in impnodes:
					if not n.Name in positionedNodes:
						x,y  = flow.GetPosTable(n).values()

						offset = [x-fstnx,y-fstny]
						newx = x+(atx-x)+offset[0]
						newy = y+(aty-y)+offset[1]
						flow.SetPos(n, newx-1, newy)

				comp.Unlock()
			##########


			importedNodes = []
			for i in newNodes:
				# Append sufix to objNames to identify product with unique Name
				node = self.getObject(i)
				newName = self.apllyProductSufix(i, origin)
				node.SetAttrs({"TOOLS_Name":newName, "TOOLB_NameSet": True})
				importedNodes.append(self.getNode(newName))

			origin.setName = "Import_" + fileName[0]			
			origin.nodes = importedNodes

			# print(
			# 	"the origin is:", origin, "\n",
			# 	"State: ", origin.state,"\n",
			# 	"Name: ", origin.importPath.split("_")[-2], "\n",
			# 	"Nodes: ", origin.nodeNames, "\n",
			# 	"importPath:", origin.importPath, "\n",
			# 	)
			
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

	@err_catcher(name=__name__)
	def apllyProductSufix(self, originalName, origin):
		newName = originalName + "_" + origin.importPath.split("_")[-2]
		return newName

	@err_catcher(name=__name__)
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
	def ReplaceBeforeImport(self, origin, newnodes):
		comp = self.fusion.GetCurrentComp()
		if origin.nodes == []:
			return None, []
		nodes = []
		nodenames =[]
		outputnodes = []
		positionednodes = []
		sceneNode = None
		
		# We are going to collect the existing nodes and check if there is a merge3D or transform3D node that represents the entry of the scene.
		for o in origin.nodes:
			hasmerge = False
			node = comp.FindTool(o["name"])
			if node:
				# Store Scene Node Connections
				nodeID  = node.GetAttrs("TOOLS_RegID")
				ismerge = nodeID == "Merge3D"
				# We try to account for Transform3D nodes that are not standarly Named.
				istrans3D = nodeID == "Transform3D" and "Transform3D" in node.Name
				# If there is no merge there should be a transform3D but if there is merge transform3D is out.
				if ismerge or istrans3D:
					if ismerge:
						hasmerge = True
					if ismerge or not hasmerge:
						outputnodes = [] # clean this variable in case there was an unaccounted node
						sceneNode = node
						connectedinputs = node.output.GetConnectedInputs()
						if len(connectedinputs)>0:
							for v in connectedinputs.values():
								connectedNode = {"node":v.GetTool().Name,"input":v.Name}
								outputnodes.append(connectedNode)
				nodenames.append(node.Name)
				nodes.append(node)
		for o in newnodes:
			newnode = comp.FindTool(o)
			# Reconnect the scene node
			if sceneNode:
				nodeID = newnode.GetAttrs("TOOLS_RegID")
				sceneNID = sceneNode.GetAttrs("TOOLS_RegID")
				if nodeID == sceneNID:

					# We try to account for Transform3D nodes that are not standarly Named.
					proceed = True
					if nodeID == "Transform3D" and not "Transform3D" in newnode.Name:
						proceed = False
					
					if proceed and len(outputnodes) > 0:
						for outn in outputnodes:
							tool = comp.FindTool(outn["node"])
							tool.ConnectInput(outn["input"], newnode)
			# Match old to new
			oldnodename = self.apllyProductSufix(o, origin)
			oldnode = comp.FindTool(oldnodename)

			# print("oldnode: ", oldnode.Name)
			# If there is a previous version of the same node.
			if oldnode:
				# idx = 1
				# check if it has valid inputs that are not part of previous import
				for input in oldnode.GetInputList().values():
					# print(input.Name, idx)
					# idx+=1
					connectedOutput = input.GetConnectedOutput()
					if connectedOutput:
						inputName = input.Name
						connectedtool = connectedOutput.GetTool()
						# Avoid Feyframe nodes
						if not connectedtool.GetAttrs("TOOLS_RegID") =="BezierSpline" and not newnode.GetAttrs("TOOLS_RegID") == "Merge3D":
							# check to avoid a connection that breaks the incoming hierarchy.
							if not connectedtool.Name in nodenames:
								# print("input: ", inputName, " -> ctool: ", connectedtool.Name, " NewNode: ", newnode.Name)
								newnode.ConnectInput(inputName, connectedtool)
				# Reconnect the 3D Scene.
				if sceneNode:
					if sceneNode.GetAttrs("TOOLS_RegID") == "Merge3D":
						if oldnode.GetAttrs("TOOLS_RegID") == "Merge3D":
							mergednodes = []
							sceneinputs = [input for input in oldnode.GetInputList().values() if "SceneInput" in input.Name]
							# newsceneinputs = [input for input in newnode.GetInputList().values() if "SceneInput" in input.Name]
							for input in sceneinputs:
								connectedOutput = input.GetConnectedOutput()
								if connectedOutput:
									connectedtool = connectedOutput.GetTool()
									if not connectedtool.Name in nodenames:
										mergednodes.append(connectedtool)
							if newnode.GetAttrs("TOOLS_RegID") == "Merge3D" and len(mergednodes) > 0:
								newsceneinputs = [input for input in newnode.GetInputList().values() if "SceneInput" in input.Name]
								for mergednode in mergednodes:
									for input in newsceneinputs:
										connectedOutput = input.GetConnectedOutput()
										if not connectedOutput:
											newnode.ConnectInput(input.Name, mergednode)
				# Match position.
				self.matchNodePos(newnode, oldnode)
				positionednodes.append(newnode.Name)
			
		# Return position
		if sceneNode:
			return sceneNode, positionednodes
		
		return None, positionednodes


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
	#        	    NODE POSITIONING               #
	#                                              #
	################################################

	#Get last click on comp view.
	@err_catcher(name=__name__)
	def find_LastClickPosition(self):
		comp = self.fusion.GetCurrentComp()
		flow = comp.CurrentFrame.FlowView
		posNode = comp.AddToolAction("Background")
		x,y = flow.GetPosTable(posNode).values()
		posNode.Delete()

		return x,y

	@err_catcher(name=__name__)
	def find_extreme_position(self, flow, thisnode=None, all_nodes=[], ignore_node_type=None, find_min=True):
		if find_min:
			thresh_x_position, thresh_y_position = float('inf'), float('inf')
		else: 
			thresh_x_position, thresh_y_position = -float('inf'), float('inf')

		extreme_node = None

		for node in all_nodes:
			if thisnode and node.Name == thisnode.Name or node.Name == 'DO_NOT_DELETE_PrismSM':
				continue

			if ignore_node_type and node.GetAttrs("TOOLS_RegID") == ignore_node_type:
				continue

			postable = flow.GetPosTable(node)
			x, y = postable.values() if postable else (thresh_x_position, thresh_y_position)

			x_thresh = x < thresh_x_position if find_min else x > thresh_x_position
			y_thresh = y < thresh_y_position

			if x_thresh:
				thresh_x_position = x
				extreme_node = node

			if y_thresh:
				thresh_y_position = y

		return extreme_node, thresh_x_position, thresh_y_position

	@err_catcher(name=__name__)
	def set_node_position(self, flow, smnode, x, y):
		flow.SetPos(smnode, x, y)

	@err_catcher(name=__name__)
	def matchNodePos(self, nodeTomove, nodeInPos):
		comp = self.fusion.GetCurrentComp()
		flow = comp.CurrentFrame.FlowView
		x,y = flow.GetPosTable(nodeInPos).values()
		self.set_node_position(flow, nodeTomove, x, y)

	#The name of this function comes for its initial use to position the "state manager node" that what used before using SetData.
	@err_catcher(name=__name__)
	def setSmNodePosition(self, smnode, find_min=True, x_offset=-2, y_offset=0, ignore_node_type=None):
		# Get the active composition
		comp = self.fusion.GetCurrentComp()
		flow = comp.CurrentFrame.FlowView

		if not comp:
			# No active composition
			return

		# Get all nodes in the composition
		all_nodes = comp.GetToolList(False).values()

		if not all_nodes:
			flow.SetPos(smnode, 0, 0)
			return

		xmost_node, thresh_x_position, thresh_y_position = self.find_extreme_position(flow, smnode, all_nodes, ignore_node_type, find_min)

		if xmost_node:
			self.set_node_position(flow, smnode, thresh_x_position + x_offset, thresh_y_position + y_offset)
		else:
			flow.SetPos(smnode, 0, 0)

	@err_catcher(name=__name__)
	def posRelativeToNode(self, node, xoffset=3):
		comp = self.fusion.GetCurrentComp()
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

	################################################
	#                                              #
	#        	  STATE MANAGER STUFF              #
	#                                              #
	################################################

	@err_catcher(name=__name__)
	def sm_getExternalFiles(self, origin):
		extFiles = []
		return [extFiles, []]

# 	@err_catcher(name=__name__)
# 	def makeFusionStatesNode(self):
# 		comp = self.fusion.GetCurrentComp()
# 		clip = """{
# 	Tools = ordered() {
# 		DO_NOT_DELETE_PrismSM = Note {
# 			Locked = true,
# 			CtrlWZoom = false,
# 			NameSet = true,
# 			Inputs = {
# 				Comments = Input { Value = "{\\n    \\"states\\": [\\n        {\\n            \\"statename\\": \\"publish\\",\\n            \\"comment\\": \\"\\",\\n            \\"description\\": \\"\\"\\n        }\\n    ]\\n}_..._", }
# 			},
# 			ViewInfo = StickyNoteInfo {
# 				Pos = { 388.667, 1.30299 },
# 				Flags = {
# 					Expanded = true
# 				},
# 				Size = { 86, 16.3636 }
# 			},
# 			Colors = { TileColor = { R = 0.0, G = 0.0, B = 1.0 }, }
# 		}
# 	},
# 	ActiveTool = "DO_NOT_DELETE_PrismSM"
# }"""

# 		pyperclip.copy(clip)
# 		comp.Paste(clip)
	
# 	@err_catcher(name=__name__)
# 	def getFusionStatesNode(self):
# 		comp = self.fusion.CurrentComp
# 		smnode = comp.FindTool("DO_NOT_DELETE_PrismSM")
# 		if smnode == None:
# 			self.makeFusionStatesNode()
# 			smnode = comp.ActiveTool
# 			self.setSmNodePosition(smnode, x_offset=-10,y_offset=-3)

# 		return smnode

	@err_catcher(name=__name__)
	def setDefaultState(self):
		comp = self.fusion.CurrentComp
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
		comp.SetData("prismstates",defaultState)

	@err_catcher(name=__name__)
	def sm_saveStates(self, origin, buf):
		comp = self.fusion.CurrentComp
		comp.SetData("prismstates", buf + "_..._")
		# prismstates = self.getFusionStatesNode()
		# prismstates.Comments = buf + "_..._"

	@err_catcher(name=__name__)
	def sm_saveImports(self, origin, importPaths):
		comp = self.fusion.CurrentComp
		prismdata = comp.GetData("prismstates")
		prismdata += importPaths.replace("\\\\", "\\")
		comp.SetData("prismstates", prismdata)
		# prismstates = self.getFusionStatesNode()
		# prismstates.Comments[0] += importPaths.replace("\\\\", "\\")

	@err_catcher(name=__name__)
	def sm_readStates(self, origin):
		comp = self.fusion.CurrentComp
		prismdata = comp.GetData("prismstates")
		return prismdata.split("_..._")[0]
		# prismstates = self.getFusionStatesNode()
		# return prismstates.Comments[0].split("_..._")[0]

	@err_catcher(name=__name__)
	def sm_deleteStates(self, origin):
		comp = self.fusion.CurrentComp
		comp.SetData("prismstates","")
		# prismstates = self.getFusionStatesNode()
		# prismstates.Comments = ""

	@err_catcher(name=__name__)
	def getImportPaths(self, origin):
		comp = self.fusion.CurrentComp
		prismdata = comp.GetData("prismstates")
		return prismdata.split("_..._")[1]
		# prismstates = self.getFusionStatesNode()
		# return prismstates.Comments[0].split("_..._")[1]

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
		self.pbUI = origin
	

	@err_catcher(name=__name__)
	def onProjectBrowserShow(self, origin):
		self.popup.close()

	def onProjectBrowserClose(self, origin):
		self.pbUI = None

	@err_catcher(name=__name__)
	def onProjectBrowserCalled(self, popup):
		#Feedback in case it takes time to open
		try:
			self.popup.close()
		except:
			pass
		self.popup = popup

	@err_catcher(name=__name__)
	def onStateManagerCalled(self, popup):		
		#Feedback in case it takes time to open
		try:
			self.popup.close()
		except:
			pass
		self.popup = popup
		
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

		#Set State Manager Data on first open.
		comp = self.fusion.CurrentComp
		if comp.GetData("prismstates") == None:
			self.setDefaultState()

		self.monkeypatchedsm = origin
		self.core.plugins.monkeyPatch(origin.rclTree, self.rclTree, self, force=True)
		#origin.gb_import.setStyleSheet("margin-top: 20px;")

	@err_catcher(name=__name__)
	def onStateManagerShow(self, origin):
		self.smUI = origin
		self.popup.close()

	@err_catcher(name=__name__)
	def onStateManagerClose(self, origin):
		self.smUI = None
		
	@err_catcher(name=__name__)
	def onStateCreated(self, origin, state, stateData):
		if state.className == "ImageRender":
			state.b_resPresets.setStyleSheet("padding-left: 1px;padding-right: 1px;")

		elif state.className == "Playblast":
			state.b_resPresets.setStyleSheet("padding-left: 1px;padding-right: 1px;")

	def onStateDeleted(self, origin, stateui):
		comp = self.fusion.GetCurrentComp()
		if stateui.className == "ImageRender":
			node = comp.FindTool(stateui.b_setRendernode.text())
			if node:
				fString = "Do you want to also delete the Saver node\nassociated with this render:"
				buttons = ["Yes", "No"]
				result = self.core.popupQuestion(fString, buttons=buttons, icon=QMessageBox.NoIcon)
				if result == "Yes":
					node.Delete()

			
	################################################
	#                                              #
	#        	 MONKEYPATCHED FUNCTIONS           #
	#                                              #
	################################################

	#Right click menu from nodes on state manager to get previous versions.
	@err_catcher(name=__name__)
	def rclTree(self, pos, activeList):
		sm = self.monkeypatchedsm
		if sm:
			#From here the only line that changes is the commented one in "render" state.
			rcmenu = QMenu(sm)
			idx = sm.activeList.indexAt(pos)
			parentState = sm.activeList.itemFromIndex(idx)
			sm.rClickedItem = parentState

			actExecute = QAction("Execute", sm)
			actExecute.triggered.connect(lambda: sm.publish(executeState=True))

			menuExecuteV = QMenu("Execute as previous version", sm)

			actSort = None
			selItems = sm.getSelectedStates()
			if len(selItems) > 1:
				parents = []
				for item in selItems:
					if item.parent() not in parents:
						parents.append(item.parent())

				if len(parents) == 1:
					actSort = QAction("Sort", sm)
					actSort.triggered.connect(lambda: sm.sortStates(selItems))

			actCopy = QAction("Copy", sm)
			actCopy.triggered.connect(sm.copyState)

			actPaste = QAction("Paste", sm)
			actPaste.triggered.connect(sm.pasteStates)

			actRename = QAction("Rename", sm)
			actRename.triggered.connect(sm.renameState)

			actDel = QAction("Delete", sm)
			actDel.triggered.connect(sm.deleteState)

			if parentState is None:
				print("no parentstate")
				actCopy.setEnabled(False)
				actRename.setEnabled(False)
				actDel.setEnabled(False)
				actExecute.setEnabled(False)
				menuExecuteV.setEnabled(False)
			elif hasattr(parentState.ui, "l_pathLast"):
				outPath = parentState.ui.getOutputName()
				if not outPath or not outPath[0]:
					menuExecuteV.setEnabled(False)
				else:
					outPath = outPath[0]
					if "render" in parentState.ui.className.lower():
						# GET PATHS FROM VERSIONS IN 2DRENDERS FOLDER
						existingVersions = sm.core.mediaProducts.getVersionsFromSameVersionStack(
							outPath, mediaType="2drenders"
						)
					elif "playblast" in parentState.ui.className.lower():
						existingVersions = sm.core.mediaProducts.getVersionsFromSameVersionStack(
							outPath, mediaType="playblasts"
						)
					else:
						existingVersions = sm.core.products.getVersionsFromSameVersionStack(
							outPath
						)
					for version in sorted(
						existingVersions, key=lambda x: x["version"], reverse=True
					):
						name = version["version"]
						actV = QAction(name, sm)
						actV.triggered.connect(
							lambda y=None, v=version["version"]: sm.publish(
								executeState=True, useVersion=v
							)
						)
						menuExecuteV.addAction(actV)

			if menuExecuteV.isEmpty():
				menuExecuteV.setEnabled(False)

			if parentState is None or parentState.ui.className == "Folder":
				createMenu = sm.getStateMenu(parentState=parentState)
				rcmenu.addMenu(createMenu)

			if sm.activeList == sm.tw_export:
				if not sm.standalone:
					rcmenu.addAction(actExecute)
					rcmenu.addMenu(menuExecuteV)

			if actSort:
				rcmenu.addAction(actSort)

			rcmenu.addAction(actCopy)
			rcmenu.addAction(actPaste)
			rcmenu.addAction(actRename)
			rcmenu.addAction(actDel)

			rcmenu.exec_(sm.activeList.mapToGlobal(pos))