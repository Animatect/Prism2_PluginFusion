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
import math
import ctypes
import glob
import shutil

import BlackmagicFusion as bmd

package_path = os.path.join(os.path.dirname(__file__), 'thirdparty')
sys.path.append(package_path)

import pygetwindow as gw

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

import pyautogui
import pyperclip
from PrismUtils.Decorators import err_catcher as err_catcher



class Prism_Fusion_Functions(object):
	def __init__(self, core, plugin):
		self.core = core
		self.plugin = plugin
		self.fusion = bmd.scriptapp("Fusion")
		self.comp = None # This comp is used by the state Manager to avoid overriding the state data on wrong comps
		self.monkeypatchedsm = None # Reference to the state manager to be used on the monkeypatched functions.
		self.monkeypatchedimportstate = None # Reference to the importState to be used on the monkeypatched functions.
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
		self.core.registerCallback(
			"getIconPathForFileType", self.getIconPathForFileType, plugin=self
		)
		
		self.importHandlers = {
			".abc": {"importFunction": self.importAlembic},
			".fbx": {"importFunction": self.importFBX},
			".bcam":{"importFunction": self.importBlenderCam},
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
	

    #   Adds custom icon for Fusion auto-backup files
	@err_catcher(name=__name__)
	def getIconPathForFileType(self, extension):
		if extension == ".autocomp":
			icon = os.path.join(self.pluginDirectory, "UserInterfaces", "Fusion-Autosave.ico")
			return icon

		return None
	

	@err_catcher(name=__name__)
	def sceneOpen(self, origin):
		# if self.core.shouldAutosaveTimerRun():
		# 	origin.startAutosaveTimer()
		pass


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
			"Comp"]["FrameFormat"]["Width"]
		height = self.fusion.GetCurrentComp().GetPrefs()[
			"Comp"]["FrameFormat"]["Height"]
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
		currVer = self.fusion.Version
		#	This is a workaround since as of now Deadline does not support Fusion 19
		if currVer > 18:
			currVer = 18
		return currVer


	@err_catcher(name=__name__)
	def openScene(self, origin, filepath, force=False):
		if os.path.splitext(filepath)[1] not in self.sceneFormats:
			return False

		try:
			self.fusion.LoadComp(filepath)
		except:
			pass

		return True
	

	################################################
	#                                              #
	#                 THUMBNAIL                    #
	#                                              #
	################################################

	@err_catcher(name=__name__)
	def captureViewportThumbnail(self):
		#   Make temp dir and file
		tempDir = os.path.join(self.pluginDirectory, "Temp")
		if not os.path.exists(tempDir):
			os.mkdir(tempDir)
		thumbPath = os.path.join(tempDir, "FusionThumb.jpg")
		thumbName = os.path.basename(thumbPath).split('.')[0]

		#   Get Fusion API stuff
		comp = self.fusion.GetCurrentComp()
		flow = comp.CurrentFrame.FlowView

		comp.Lock()
		comp.StartUndo()

		thumbSaver = None
		origSaverList = {}

		#   Get tool through logic (Selected or Saver or last)
		thumbTool = self.findThumbnailTool(comp)

		if thumbTool:
			#   Save pass-through state of all savers
			origSaverList = self.origSaverStates("save", comp, origSaverList)

			# Add a Saver tool to the composition
			thumbSaver = comp.AddTool("Saver", -32768, -32768, 1)

			# Connect the Saver tool to the currently selected tool
			thumbSaver.Input = thumbTool

			# Set the path for the Saver tool
			thumbSaver.Clip = os.path.join(tempDir, thumbName + ".jpg")

			#   Get current frame number
			currFrame = comp.CurrentTime

			origStartFrame = comp.GetAttrs("COMPN_RenderStart")
			origEndFrame = comp.GetAttrs("COMPN_RenderEnd")

			# Temporarily set the render range to the current frame
			comp.SetAttrs({'COMPN_RenderStart' : currFrame})
			comp.SetAttrs({'COMPN_RenderEnd' : currFrame})

			# Render the current frame
			comp.Render()  # Trigger the render

			# Restore the original render range
			comp.SetAttrs({'COMPN_RenderStart' : origStartFrame})
			comp.SetAttrs({'COMPN_RenderEnd' : origEndFrame})

		#   Deals with the frame number suffix added by Fusion rener
		pattern = os.path.join(tempDir, thumbName + "*.jpg")
		renderedThumbs = glob.glob(pattern)

		if renderedThumbs:
			renderedThumb = renderedThumbs[0]  # Assuming only one matching file
			os.rename(renderedThumb, thumbPath)

		comp.EndUndo()
		comp.Undo()

		if thumbSaver:
			try:
				thumbSaver.Delete()
			except:
				pass

		#   Restore pass-through state of orig savers
		self.origSaverStates("load", comp, origSaverList)

		comp.Unlock()

		#   Get pixmap from Prism
		pm = self.core.media.getPixmapFromPath(thumbPath)

		#   Delete temp dir
		if os.path.exists(tempDir):
			shutil.rmtree(tempDir)

		return pm


	# Handle Savers pass-through state for thumb capture
	@err_catcher(name=__name__)
	def origSaverStates(self, mode, comp, origSaverList):
		saverList = self.getSaverList(comp)
		for tool in saverList:
			toolName = tool.GetAttrs()["TOOLS_Name"]
			if mode == "save":
				# Save the current pass-through state
				origSaverList[toolName] = tool.GetAttrs()["TOOLB_PassThrough"]
				# Set the tool to pass-through
				tool.SetAttrs({"TOOLB_PassThrough": True})
			elif mode == "load":
				# Restore the original pass-through state
				if toolName in origSaverList:
					tool.SetAttrs({"TOOLB_PassThrough": origSaverList[toolName]})

		return origSaverList


	# Get list of all Savers
	@err_catcher(name=__name__)
	def getSaverList(self, comp):

		saverList = []
		for tool in comp.GetToolList(False).values():
			if self.isSaver(tool):
				saverList.append(tool)

		return saverList
	

	#   Finds the tool to use for the thumbnail in priority
	@err_catcher(name=__name__)
	def findThumbnailTool(self, comp):
		# 1. Check the selected tool
		currTool = comp.ActiveTool
		if currTool:
			return currTool

		# 2. Check for any saver that is not pass-through
		for tool in comp.GetToolList(False).values():
			if self.isSaver(tool) and not self.isPassThrough(tool):
				return tool

		# 3. Check for any saver, even if pass-through
		for tool in comp.GetToolList(False).values():
			if self.isSaver(tool):
				return tool

		# 4. Fallback to the final tool in the flow
		return self.getLastTool(comp) or None


	#   Checks if tool is a Saver, or custom Saver type
	@err_catcher(name=__name__)
	def isSaver(self, tool):
		# Check if tool is valid
		if not tool:
			return False
		# Check if tool name is 'Saver' (should work if node is renamed)
		if tool.GetAttrs({"TOOLS_Name"})["TOOLS_RegID"] == "Saver":
			return True

		return False


	# Checks if tool is set to pass-through mode
	@err_catcher(name=__name__)
	def isPassThrough(self, tool):
		return tool and tool.GetAttrs({"TOOLS_Name"})["TOOLB_PassThrough"]


	#   Tries to find last tool in the flow
	@err_catcher(name=__name__)
	def getLastTool(self, comp):
		try:
			for tool in comp.GetToolList(False).values():
				if not self.hasConnectedOutputs(tool):
					return tool
		except:
			return None


	#   Finds if tool has any outputs connected
	@err_catcher(name=__name__)
	def hasConnectedOutputs(self, tool):
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
	

	################################################
	#                                              #
	#                 STATE MANAGER                #
	#                                              #
	################################################

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
	

	@err_catcher(name=__name__)												#	TODO
	def getCamName(self, origin, handle):
		if handle == "Current View":
			return handle

		return str(nodes[0])
	

	@err_catcher(name=__name__)												#	TODO
	def selectCam(self, origin):
		if self.isNodeValid(origin, origin.curCam):
			select(origin.curCam)


	@err_catcher(name=__name__)
	def sm_export_startup(self, origin):
		pass

		@err_catcher(name=__name__)
		def sm_export_setTaskText(self, origin, prevTaskName, newTaskName):
			origin.l_taskName.setText(newTaskName)


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
	def getNodePassthrough(self, nodename):
		node = self.get_rendernode(nodename)
		return not node.GetAttrs("TOOLB_PassThrough")
	

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
		if self.sm_checkCorrectComp(comp):
			if not self.rendernode_exists(nodename):
				comp.Lock()
				sv = comp.Saver()
				comp.Unlock()
				sv.SetAttrs({'TOOLS_Name' : nodename})
				if not self.posRelativeToNode(sv):
					#Move Render Node to the Right of the scene	
					self.setNodePosition(sv, find_min=False, x_offset=10, ignore_node_type="Saver")
					self.stackNodesByType(sv)
			return sv


	@err_catcher(name=__name__)
	def sm_render_preSubmit(self, origin, rSettings):
		pass


	###############################
	#	REPLACE PATHS FOR SUBMIT  #
	###############################
	@err_catcher(name=__name__)
	def getReplacedPaths(self, comp, filepath):
		pathmaps = comp.GetCompPathMap(False, False)
		pathexists = False
		isnetworkpath = False
		for k in pathmaps.keys():
			if k in filepath:
				index = filepath.find(k)

				if index != -1:  # Check if substring exists
					# Replace "brown" with "red"
					new_path = filepath[:index] + pathmaps[k] + "/" + filepath[index + len(k):]
					formatted_path = os.path.normpath(new_path)
					# Check if the formatted path exists
					if os.path.exists(formatted_path):
						pathexists = True
					# Check if path is local
					drive_letter, _  = os.path.splitdrive(formatted_path)
					drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive_letter)
					isnetworkpath = drive_type == 4 or formatted_path.startswith("\\\\")

					return {"path":formatted_path, "valid":pathexists, "net":isnetworkpath}
		
		return {"path":None, "valid":pathexists, "net":isnetworkpath}
	

	@err_catcher(name=__name__)
	def replacePathMapsLUTFiles(self, comp):
		oldcopy = pyperclip.paste()
		# Input text		
		all_OCIO_FT = comp.GetToolList(False, "OCIOFileTransform").values()
		all_FileLUT = comp.GetToolList(False, "FileLUT").values()
		luttools = list(all_OCIO_FT) + list(all_FileLUT)

		for tool in luttools:
			comp.Copy(tool)
			text = pyperclip.paste()
			# Define regular expression pattern to match the desired substring
			pattern = r'LUTFile = Input { Value = "(.*?)"'

			# Search for the pattern in the text
			match = re.search(pattern, text)

			# If a match is found, extract the substring after "Value ="
			if match:
				filepath = match.group(1)
				pathinfo = self.getReplacedPaths(comp, filepath)
				newpath = pathinfo["path"]
				if newpath:
					tool.LUTFile = newpath
			else:
				print("Pattern not found in the text.")
		pyperclip.copy(oldcopy)


	@err_catcher(name=__name__)
	def replacePathMapsOCIOCS(self, comp):
		oldcopy = pyperclip.paste()
		# Input text
		all_OCIO_CS = comp.GetToolList(False, "OCIOColorSpace").values()

		for tool in all_OCIO_CS:
			comp.Copy(tool)
			text = pyperclip.paste()
			# Define regular expression pattern to match the desired substring
			pattern = r'OCIOConfig\s*=\s*Input\s*{\s*Value\s*=\s*"([^"]+)"'

			# Search for the pattern in the text
			match = re.search(pattern, text)

			# If a match is found, extract the substring after "Value ="
			if match:
				filepath = match.group(1)
				pathinfo = self.getReplacedPaths(comp, filepath)
				newpath = pathinfo["path"]
				if newpath:
					tool.OCIOConfig = newpath
			else:
				print("Pattern not found in the text.")
		pyperclip.copy(oldcopy)
	

	def replacePathMapsFBX(self, comp):
		oldcopy = pyperclip.paste()
		# Input text
		all_fbx  = comp.GetToolList(False, "SurfaceFBXMesh").values()

		for tool in all_fbx:
			comp.Copy(tool)
			text = pyperclip.paste()
			# Define regular expression pattern to match the desired substring
			pattern = r'ImportFile = Input { Value = "(.*?)", },'

			# Search for the pattern in the text
			match = re.search(pattern, text)
			# print(match)

			# If a match is found, extract the substring after "Value ="
			if match:
				filepath = match.group(1)
				pathinfo = self.getReplacedPaths(comp, filepath)
				newpath = pathinfo["path"]
				tool.ImportFile = newpath
			else:
				print("Pattern not found in the text.")
		pyperclip.copy(oldcopy)


	def replacePathMapsABC(self, comp):
		pathdata = []
		oldcopy = pyperclip.paste()
		# Input text
		all_alembic  = comp.GetToolList(False, "SurfaceAlembicMesh").values()

		for tool in all_alembic:
			comp.Copy(tool)
			text = pyperclip.paste()
			# Define regular expression pattern to match the desired substring
			pattern = r'Filename = Input { Value = "(.*?)", },'

			# Search for the pattern in the text
			match = re.search(pattern, text)

			# If a match is found, extract the substring after "Value ="
			if match:
				filepath = match.group(1)
				pathinfo = self.getReplacedPaths(comp, filepath)
				newpath = pathinfo["path"]
				if newpath:
					tool.Filename = newpath
					pathdata.append({"node": tool.Name, "path":pathinfo["path"], "valid":pathinfo["valid"], "net":pathinfo["net"]})
			
		pyperclip.copy(oldcopy)
		return pathdata
	

	@err_catcher(name=__name__)
	def replacePathMapsbyPattern(self, comp, tool_list, regexpattern, pathInput):
		pathdata = []
		oldcopy = pyperclip.paste()

		for tool in tool_list:
			comp.Copy(tool)
			text = pyperclip.paste()
			# Define regular expression pattern to match the desired substring
			pattern = regexpattern
			# Search for the pattern in the text
			match = re.search(pattern, text)

			# If a match is found, extract the substring after "Value ="
			if match:
				filepath = match.group(1)
				pathinfo = self.getReplacedPaths(comp, filepath)
				newpath = pathinfo["path"]
				if newpath:
					setattr(tool, pathInput, newpath)
					pathdata.append({"node": tool.Name, "path":pathinfo["path"], "valid":pathinfo["valid"], "net":pathinfo["net"]})
			
		pyperclip.copy(oldcopy)
		return pathdata
	

	@err_catcher(name=__name__)
	def replacePathMapsIOtools(self, comp):
		pathdata = []
		all_loader = comp.GetToolList(False, "Loader").values()
		all_saver  = comp.GetToolList(False, "Saver").values()
		iotools = list(all_loader) + list(all_saver)
		comp.Lock()
		for tool in iotools:
			filepath = tool.GetAttrs("TOOLST_Clip_Name")[1]
			pathinfo = self.getReplacedPaths(comp, filepath)
			newpath = pathinfo["path"]
			if newpath:
				tool.Clip = newpath			
				pathdata.append({"node": tool.Name, "path":pathinfo["path"], "valid":pathinfo["valid"], "net":pathinfo["net"]})

		comp.Unlock()
		return pathdata


	###############################
	#		 RENDERING  		  #
	###############################

	@err_catcher(name=__name__)
	def sm_render_CheckSubmittedPaths(self):
		comp = self.fusion.GetCurrentComp()
		allpathdata = []

		# get Paths
		allpathdata += self.replacePathMapsIOtools(comp)
		# self.replacePathMapsABC(comp)
		# self.replacePathMapsFBX(comp)
		# self.replacePathMapsOCIOCS(comp)
		# self.replacePathMapsLUTFiles(comp)
		all_alembic  = comp.GetToolList(False, "SurfaceAlembicMesh").values()
		allpathdata += self.replacePathMapsbyPattern(
			comp, all_alembic, r'Filename = Input { Value = "(.*?)", },', "Filename"
			)
		
		all_fbx  = comp.GetToolList(False, "SurfaceFBXMesh").values()
		allpathdata += self.replacePathMapsbyPattern(
			comp, all_fbx, r'ImportFile = Input { Value = "(.*?)", },', "ImportFile"
			)
		
		all_OCIO_CS = comp.GetToolList(False, "OCIOColorSpace").values()
		allpathdata += self.replacePathMapsbyPattern(
			comp, all_OCIO_CS, r'OCIOConfig\s*=\s*Input\s*{\s*Value\s*=\s*"([^"]+)"', "OCIOConfig"
			)
		
		all_OCIO_FT = comp.GetToolList(False, "OCIOFileTransform").values()
		all_FileLUT = comp.GetToolList(False, "FileLUT").values()
		luttools = list(all_OCIO_FT) + list(all_FileLUT)
		allpathdata += self.replacePathMapsbyPattern(
			comp, luttools, r'LUTFile = Input { Value = "(.*?)"', "LUTFile"
			)
		
		for pathdata in allpathdata:
			if not pathdata["valid"]:
				print("path: ", pathdata["path"], " in ", pathdata["node"], "does not exists")
			if not pathdata["net"]:
				print("path: ", pathdata["path"], " in ", pathdata["node"], "Is not a NET Path")
			print("path: ", pathdata["path"], " in ", pathdata["node"], "was processed")


	@err_catcher(name=__name__)
	def configureRenderNode(self, nodeName, outputPath, fuseName=None):
		comp = self.fusion.GetCurrentComp()		
		if self.sm_checkCorrectComp(comp):
			sv = self.get_rendernode(nodeName)
			if sv:
				sv.Clip = outputPath
				if fuseName:
					sv["OutputFormat"] = fuseName

				if sv.Input.GetConnectedOutput():
					sv.Clip = outputPath
				else:
					return "Error (Render Node is not connected)"
			else:
				return "Error (Render Node does not exist)"


	#	Configures name to conform with Fusion Restrictions
	@err_catcher(name=__name__)
	def getFusLegalName(self, origName, check=False):
		"""
			Fusion has strict naming for nodes.  You can only use:
			- Alphanumeric characters:  a-z, A-Z, 0-9,
			- Do not use any spaces,
			- Do not use special charactors,
			- Node name cannot start with a number.
		"""

		# Check if the name starts with a number
		if origName[0].isdigit():
			if check:
				return False, "Name cannot start with a number."
			
			return "Error: Name cannot start with a number."

		# Check if the name contains only allowed characters
		if not re.match(r'^[A-Za-z0-9_\- .]*$', origName):
			if check:
				return False, "Name contains invalid characters."
			
			return "Error: Name contains invalid characters."

		newName = origName.replace(' ', '_')
		newName = newName.replace('.', '_')
		newName = newName.replace('-', '_')

		if check:
			return True, ""
		
		return newName


	#	Returns Fusion-legal Saver name base on State name
	@err_catcher(name=__name__)
	def getRendernodeName(self, stateName):
		legalName = self.getFusLegalName(stateName)
		nodeName = f"PrSAVER_{legalName}"

		return nodeName
	

	#	Gets individual State data from the comp state data based on the Saver name
	@err_catcher(name=__name__)
	def getMatchingStateData(self, nodeName):
		stateDataRaw = json.loads(self.sm_readStates(self))

		# Iterate through the states to find the matching state dictionary
		stateDetails = None
		for stateData in stateDataRaw["states"]:
			if stateData.get("rendernode") == nodeName:
				stateDetails = stateData
				return stateDetails

		self.core.popup(f"No state details for:  {nodeName}")                           #    TODO - ERROR HANDLING


	#	Renders individual State Saver locally
	@err_catcher(name=__name__)
	def sm_render_startLocalRender(self, origin, outputPathOnly, outputName, rSettings):
		comp = self.fusion.GetCurrentComp()		
		if self.sm_checkCorrectComp(comp):
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
			
			# Are we just setting the path and version into the render nodes or are we executing a local render?
			if outputPathOnly:
				return "Result=Success"

			else:				
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
	def isUsingMasterVersion(self):
		useMaster = self.core.mediaProducts.getUseMaster()
		if not useMaster:
			return False

		try:
			masterAction = self.cb_master.currentText()
			if masterAction == "Don't update master":
				return False
		except:
			pass

		return True


	@err_catcher(name=__name__)
	def handleMasterVersion(self, outputName, masterAction=None):
		if not self.isUsingMasterVersion():
			return

		if not masterAction:
			masterAction = self.cb_master.currentText()

		if masterAction in ("Set as master", "Force Set as Master"):
			self.core.mediaProducts.updateMasterVersion(outputName, mediaType="2drenders")
		elif masterAction in ("Add to master", "Force Add to Master"):
			self.core.mediaProducts.addToMasterVersion(outputName, mediaType="2drenders")


	#	Makes dict for later use in updating Master ver
	@err_catcher(name=__name__)
	def saveMasterData(self, rSettings, stateData, outputPath):
		if rSettings["masterOvr"]:
			stateMasterData = [stateData["taskname"], rSettings["handleMaster"], outputPath]
		else:
			stateMasterData = [stateData["taskname"], stateData["masterVersion"], outputPath]

		self.masterData.append(stateMasterData)


	#	Executes update Master for each state in dict
	@err_catcher(name=__name__)
	def executeMaster(self):
		for state in self.masterData:
			self.handleMasterVersion(state[2], state[1])


	#	Saves original comp settings
	@err_catcher(name=__name__)
	def saveOrigCompSettings(self, comp):
		cData = {}

		cData["orig_frameRange"] = self.getFrameRange(self)
		cData["orig_currentFrame"] = comp.CurrentTime
		cData["orig_rezX"], cData["orig_rezY"] = self.getResolution()
		cData["orig_HQ"] = comp.GetAttrs()["COMPB_HiQ"]
		cData["orig_MB"] = comp.GetAttrs()["COMPB_MotionBlur"]
		cData["orig_Proxy"] = comp.GetAttrs()["COMPB_Proxy"]

		return cData
	

	#	Resets original comp settings
	@err_catcher(name=__name__)
	def loadOrigCompSettings(self, comp, cData):
		origFrameStart, origFrameEnd = cData["orig_frameRange"]
		self.setFrameRange(self, origFrameStart, origFrameEnd)
		comp.CurrentTime = cData["orig_currentFrame"]
		self.setResolution(cData["orig_rezX"], cData["orig_rezY"])
		comp.SetAttrs({"COMPB_HiQ": cData["orig_HQ"]})
		comp.SetAttrs({"COMPB_MotionBlur": cData["orig_MB"]})
		comp.SetAttrs({"COMPB_Proxy": cData["orig_Proxy"]})


	#	Changes comp settings based on RenderGroup overrides if applicable
	@err_catcher(name=__name__)
	def setCompOverrides(self, comp, rSettings):
		if "frameOvr" in rSettings and rSettings["frameOvr"]:
			self.setFrameRange(self, rSettings["frame_start"], rSettings["frame_end"])

		if "scalingOvr" in rSettings and rSettings["scalingOvr"]:
			render_Scale = rSettings["render_Scale"]
			orig_rezX, orig_rezY = self.getResolution()
			renderRezX = orig_rezX * render_Scale
			renderRezY = orig_rezY * render_Scale
			self.setResolution(renderRezX, renderRezY)

		if "hiQualOvr" in rSettings and rSettings["hiQualOvr"]:
			tempHQ = rSettings["render_HQ"]
			if tempHQ == "Force HiQ":
				comp.SetAttrs({"COMPB_HiQ": True})
			if tempHQ == "Force LowQ":
				comp.SetAttrs({"COMPB_HiQ": False})

		if "blurOvr" in rSettings and rSettings["blurOvr"]:
			tempBlur = rSettings["render_Blur"]
			if tempBlur == "Force Use MB":
				comp.SetAttrs({"COMPB_MotionBlur": True})
			if tempBlur == "Force No MB":
				comp.SetAttrs({"COMPB_MotionBlur": False})
				
		if "proxyOvr" in rSettings and rSettings["proxyOvr"]:
			tempProxy = rSettings["render_Proxy"]
			if tempProxy == "Force Proxies Off":
				comp.SetAttrs({"COMPB_Proxy": True})
			if tempProxy == "Force Proxies On":
				comp.SetAttrs({"COMPB_Proxy": False})


	#	Adds a Scale node if the Scale override is used by the RenderGroup
	@err_catcher(name=__name__)
	def addScaleNode(self, comp, nodeName, scale):
		try:
			sv = self.get_rendernode(nodeName)
			if sv:
				#	Add a Scale tool
				scaleTool = comp.AddTool("Scale")
				#	Add tool to temp list for later deletion
				self.tempScaleTools.append(scaleTool)
				#	Set scale value
				scaleTool.SetInput("XSize", scale)

				# Get the output of the Scale tool
				scaleOutput = scaleTool.FindMainOutput(1)

				# Rewire the connections
				prev_input = sv.FindMainInput(1).GetConnectedOutput()  # Get the input connected to Saver

				if prev_input:
					scaleTool.FindMainInput(1).ConnectTo(prev_input)  # Connect the previous input to Scale
					sv.FindMainInput(1).ConnectTo(scaleOutput)  # Connect Scale to this specific Saver
				else:
					print(f"No input found connected to {sv.Name}.")
		
		except Exception as e:
			print(f"Error adding Scale node: {e}")


	#	Deletes the temp Scale nodes
	@err_catcher(name=__name__)
	def deleteTempScaleTools(self):
		for tool in self.tempScaleTools:
			try:
				tool.Delete()
			except:
				print(f"Unable to delete temporary Scale tool {tool}")


	#	Configures all the settings and paths for each state of the RenderGroup
	@err_catcher(name=__name__)
	def configureRenderComp(self, origin, comp, rSettings):
		self.origSaverList = {}
		self.masterData = []
		self.tempScaleTools = []

		#	Capture orignal Comp settings for restore after render
		self.origCompSettings = self.saveOrigCompSettings(comp)

		#	Get ImageRender states to be rendered with the group
		renderStates = rSettings["groupRenderStates"]

		#   Save pass-through state of all savers
		self.origSaverList = self.origSaverStates("save", comp, self.origSaverList)

		#	Configure Comp with overrides from RenderGroup
		self.setCompOverrides(comp, rSettings)

		for state in renderStates:
			#	Get Saver name for State
			nodeName = self.getRendernodeName(state)
			self.setNodePassthrough(nodeName, passThrough=False)

			#	Add Scale tool if scale override
			if "scalingOvr" in rSettings and rSettings["scalingOvr"]:
				self.addScaleNode(comp, nodeName, rSettings["render_Scale"])

			context = rSettings["context"]

			#	Set frame padding format for Fusion
			framePadding = "0" * self.core.framePadding
			context["frame"] = framePadding

			#	Get State data from Comp
			stateData = self.getMatchingStateData(nodeName)

			#	If Render as Previous Version enabled
			if rSettings["renderAsPrevVer"]:
				#	Get project basepath from core
				basePath = self.core.paths.getRenderProductBasePaths()[stateData["curoutputpath"]]

				#	 Add info to context
				stateData["mediaType"] = "2drenders"
				stateData["project_path"] = basePath
				stateData["identifier"] = stateData["taskname"]
				context["mediaType"] = "2drenders"
				#	Get highest existing render version to use for render
				self.useVersion = self.core.mediaProducts.getHighestMediaVersion(context, getExisting=True)

			#	If Render as Previous Version not enabled
			else:
				self.useVersion = None

			#	 Handle Location override
			if rSettings["locationOvr"]:
				renderLoc = rSettings["render_Loc"]
			else:
				renderLoc = stateData["curoutputpath"]

			#	Get new render path from Core for each Saver
			outputPathData = self.core.mediaProducts.generateMediaProductPath(
				entity=context,
				task=stateData["taskname"],
				extension=stateData["outputFormat"],
				framePadding=framePadding,
				comment=origin.stateManager.publishComment,
				version=self.useVersion if self.useVersion != "next" else None,
				location=renderLoc,
				singleFrame=False,
				returnDetails=True,
				mediaType="2drenders"
				)

			#	Get version filepath for Saver
			self.outputPath = outputPathData["path"]
			#	Configure Saver with new filepath
			self.configureRenderNode(nodeName, self.outputPath, fuseName=None)

			#	Setup master version execution
			self.saveMasterData(rSettings, stateData, self.outputPath)


			####	TODO  ADD VERSIONINFO CREATION	####


	#	Executes a GroupRender on the local machine that allows multiple Savers to render simultaneously
	@err_catcher(name=__name__)
	def sm_render_startLocalGroupRender(self, origin, rSettings):
		comp = self.fusion.GetCurrentComp()

		#	Return if the Comps do not match
		if not self.sm_checkCorrectComp(comp):
			return False

		comp.Lock()

		#	Setup comp settings and filepaths for render
		self.configureRenderComp(origin, comp, rSettings)

		#	Render of course . . . 
		comp.Render({"Wait": True})

		#	Remove any temp Scale nodes
		self.deleteTempScaleTools()

		#	Reset Comp settings to Original
		self.loadOrigCompSettings(comp, self.origCompSettings)

		#	Reconfigure pass-through of Savers
		self.origSaverStates("load", comp, self.origSaverList)

		comp.Unlock()

		#	Execute master version if applicable
		self.executeMaster()

		###		TODO	ADD POST RENDER CALLBACK	####

		#	TODO LOOK AT VERSIONINFO FILE GENERATION

		return "Result=Success"


	#	Generates a temp file and dir for farm submission
	@err_catcher(name=__name__)
	def getFarmTempFilepath(self, origFilepath):
		dirPath, fileName = os.path.split(origFilepath)
		baseName, ext = os.path.splitext(fileName)

		# Modify the basename by adding "--TEMP"
		new_baseName = f"{baseName}--TEMP_FARM_FILE{ext}"

		# Add the "TEMP" child directory to the path
		new_dirPath = os.path.join(dirPath, "TEMP_FARM")
		if not os.path.exists(new_dirPath):
			os.mkdir(new_dirPath)

		# Combine the new directory path with the modified filename
		new_filePath = os.path.join(new_dirPath, new_baseName)

		return new_filePath, new_dirPath
	

	@err_catcher(name=__name__)
	def setupFarmDetails(self, origin, rSettings):
		#	Edit various details for farm submission
		context = rSettings["context"]
		details = context.copy()
		
		if "filename" in details:
			del details["filename"]
		if "extension" in details:
			del details["extension"]

		details["version"] = self.useVersion
		details["sourceScene"] = self.tempFilePath
		details["identifier"] = rSettings["groupName"]
		details["comment"] = self.monkeypatchedsm.publishComment

		sceneDescription = None
		self.className = "RenderGroup"

		return details


	#	Submits the temp comp file to the Farm plugin for rendering
	@err_catcher(name=__name__)
	def sm_render_startFarmGroupRender(self, origin, farmPlugin, rSettings):
		comp = self.fusion.GetCurrentComp()

		#	Return if the Comps do not match
		if not self.sm_checkCorrectComp(comp):
			return False
		
		comp.Lock()

		#	Setup comp settings and filepaths for render
		self.configureRenderComp(origin, comp, rSettings)

		#	Gets current filename
		currFile = self.core.getCurrentFileName()
		#	Gets temp filename
		self.tempFilePath, tempDir = self.getFarmTempFilepath(currFile)
		#	Saves to temp comp
		saveTempResult = comp.Save(self.tempFilePath)				#	TODO HANDLE SAVE ERROR

		farmDetails = self.setupFarmDetails(origin, rSettings)

		#	Submits to farm plugin
		result = farmPlugin.sm_render_submitJob(
			origin,
			self.outputPath,
			None,
			handleMaster=False,					#	TESTING			TODO FINISH
			# handleMaster=handleMaster,		#	TODO FARM HANDLEMASTER
			details=farmDetails,
			sceneDescription=False
			)
		

		updateMaster = False						#	TODO


		# if result == "publish paused":
		# 	return
		# else:
		# 	if updateMaster:
		# 		self.handleMasterVersion(outputName)

		# 	kwargs = {
		# 		"state": self,
		# 		"scenefile": fileName,
		# 		"settings": rSettings,
		# 		"result": result,
		# 	}

		# 	self.core.callback("postRender", **kwargs)

		# 	if "Result=Success" in result:
		# 		return [self.state.text(0) + " - success"]
		# 	else:
		# 		erStr = "%s ERROR - sm_default_imageRenderPublish %s:\n%s" % (
		# 			time.strftime("%d/%m/%y %X"),
		# 			self.core.version,
		# 			result,
		# 		)
		# 		if not result.startswith("Execute Canceled: "):
		# 			if result == "unknown error (files do not exist)":
		# 				QMessageBox.warning(
		# 					self.core.messageParent,
		# 					"Warning",
		# 					"No files were created during the rendering. If you think this is a Prism bug please report it in the forum:\nwww.prism-pipeline.com/forum/\nor write a mail to contact@prism-pipeline.com",
		# 				)
		# 			else:
		# 				self.core.writeErrorLog(erStr)
		# 		return [self.state.text(0) + " - error - " + result]


		#	Deletes temp comp file
		try:
			shutil.rmtree(tempDir)
		except:
			self.core.popup(f"Unable to remove temp directory:  {tempDir}")                                      #    TESTING	TODO  Handle error

		#	Remove any temp Scale nodes
		self.deleteTempScaleTools()

		#	Reset Comp settings to Original
		self.loadOrigCompSettings(comp, self.origCompSettings)

		#	Reconfigure pass-through of Savers
		self.origSaverStates("load", comp, self.origSaverList)

		#	Save the original settings to original file
		comp.Save(currFile)

		comp.Unlock()

		# #	Execute master version if applicable									#	TODO
		# self.executeMaster()

		###		TODO	ADD POST RENDER CALLBACK	####


		return "Result=Success"


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
		dlParams["pluginInfos"]["Version"] = str(math.floor(self.getAppVersion(origin)))
		dlParams["pluginInfos"]["OutputFile"] = dlParams["jobInfos"]["OutputFilename0"]

		#	Uses StateManager comment for Farm comment
		try:
			dlParams["jobInfos"]["Comment"] = self.monkeypatchedsm.publishComment
		except:
			dlParams["jobInfos"]["Comment"] = "Prism-Submission-Fusion_ImageRender"


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
	def deleteNodes(self, origin, handles, num=0):
		comp = self.fusion.GetCurrentComp()	
		for i in handles:	
			if self.sm_checkCorrectComp(comp):
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
	def importImages(self, mediaBrowser):
		if mediaBrowser.origin.getCurrentAOV():
			fString = "Please select an import option:"
			buttons = ["Current AOV", "All AOVs", "Update Selected", "Cancel"]
			result = self.core.popupQuestion(fString, buttons=buttons, icon=QMessageBox.NoIcon)
		else:
			result = "Current AOV"

		if result == "Current AOV":
			self.fusionImportSource(mediaBrowser)
		elif result == "All AOVs":
			self.fusionImportPasses(mediaBrowser)
		elif result == "Update Selected":
			self.fusionUpdateSelectedPasses(mediaBrowser)
		else:
			return


	@err_catcher(name=__name__)
	def fusionImportSource(self, mediaBrowser):
		comp = self.fusion.GetCurrentComp()
		flow = comp.CurrentFrame.FlowView

		# refNode = comp.ActiveTool # None if no active tool
		leftmostNode = self.find_leftmost_lower_node(0.5)

		# deselect all nodes
		flow.Select()

		sourceData = mediaBrowser.compGetImportSource()
		imageData = self.getImageData(comp, sourceData)
		if imageData:
			updatehandle:list = [] # Required to return data on the updated nodes.
			node = self.processImageImport(imageData, updatehandle=updatehandle, refNode=leftmostNode)
			
			if leftmostNode:
				self.sort_loaders(leftmostNode, reconnectIn=True)

			# deselect all nodes
			flow.Select()
			self.getUpdatedNodesFeedback(updatehandle)


	@err_catcher(name=__name__)
	def fusionImportPasses(self, mediaBrowser):
		comp = self.fusion.GetCurrentComp()
		flow = comp.CurrentFrame.FlowView

		fString = "Some EXRs seem to have multiple channels:\n" + "Do you want to split the EXR channels into individual nodes?"
		splithandle = {'splitchosen': False, 'splitfirstasked': True, 'fstring': fString}
		updatehandle:list = [] #List of updated nodes

		# deselect all nodes
		flow.Select()

		# Get the leftmost position.
		# Also get Lower Position and check if it is within the x threshold to be still on the leftmost.
		# Update the position with every new node as the new pos.
		leftmostNode = self.find_leftmost_lower_node(0.5)

		dataSources = mediaBrowser.compGetImportPasses()
		for sourceData in dataSources:
			imageData = self.getPassData(comp, sourceData)
			# Return the last processed node.
			leftmostNode = self.processImageImport(imageData, splithandle=splithandle, updatehandle=updatehandle, refNode=leftmostNode)

		self.sort_loaders(leftmostNode, reconnectIn=True)

		# deselect all nodes
		flow.Select()
		self.getUpdatedNodesFeedback(updatehandle)		


	@err_catcher(name=__name__)
	def getUpdatedNodesFeedback(self, updatehandle):
		comp = self.fusion.GetCurrentComp()
		flow = comp.CurrentFrame.FlowView
		if len(updatehandle) > 0:
			
			message = "The following nodes were updated:\n\n"
			for handle in updatehandle:
				if ".#nochange#." in handle:
					message += handle.split(":")[0] + ": Version didn't change\n" 
				else:
					message += f"{handle}\n"
				flow.Select(comp.FindTool(handle.split(":")[0]), True)
			# Display List of updated nodes.
			self.createInformationDialog("Updated Nodes", message)


	@err_catcher(name=__name__)
	def createInformationDialog(self, title, message):
		msg = QMessageBox(QMessageBox.Question, title, message)
		msg.addButton("Ok", QMessageBox.YesRole)
		msg.setParent(self.core.messageParent, Qt.Window)
		msg.exec_()


	@err_catcher(name=__name__)
	def split_loader_name(self, name):
		prefix = name.rsplit('_', 1)[0]  # everything to the left of the last "_"
		suffix = name.rsplit('_', 1)[-1]  # everything to the right of the last "_"
		return prefix, suffix


	@err_catcher(name=__name__)
	def sort_loaders(self, posRefNode, reconnectIn=True):
		comp = self.fusion.GetCurrentComp()
		flow = comp.CurrentFrame.FlowView
		comp.Lock()
		#Get the leftmost loader within a threshold.
		leftmostpos = flow.GetPosTable(posRefNode)[1]
		thresh = 100
		loaders = [l for l in comp.GetToolList(False, "Loader").values() if abs(flow.GetPosTable(l)[1] - leftmostpos)<=thresh]
		loaderstop2bot = sorted(loaders, key=lambda ld: flow.GetPosTable(ld)[2])
		layers = set([self.split_loader_name(ly.Name)[0] for ly in loaders])
		sortedloaders = []
		for ly in sorted(list(layers)):
			lyloaders = [l for l in loaders if self.split_loader_name(l.Name)[0] == ly]
			sorted_loader_names = sorted(lyloaders, key=lambda ld: ld.Name.lower())
			sortedloaders += sorted_loader_names

		# Sorting the loader names
		lastloaderlyr = self.split_loader_name(sortedloaders[0].Name)[0]
		newx = flow.GetPosTable(loaderstop2bot[0])[1]
		newy = flow.GetPosTable(loaderstop2bot[0])[2]
		for l in sortedloaders:
			# we reconnect to solve an issue that creates "Ghost" connections un til comp is reoppened.
			innode =  comp.FindTool(l.Name+"_IN")
			outnode = comp.FindTool(l.Name+"_OUT")
			if innode and reconnectIn:
				innode.ConnectInput('Input', l)
			lyrnm = self.split_loader_name(l.Name)[0]
			if lyrnm != lastloaderlyr:
				newy+=1
			flow.SetPos(l, newx, newy)
			if innode:
				flow.SetPos(innode, newx+2, newy)
			if outnode:
				flow.SetPos(outnode, newx+3, newy)
			newy+=1
			lastloaderlyr = lyrnm
		comp.Unlock()


	@err_catcher(name=__name__)
	def fusionUpdateSelectedPasses(self, mediaBrowser):
		comp = self.fusion.GetCurrentComp()
		flow = comp.CurrentFrame.FlowView
	
		# from selection grab only loaders
		loaders = comp.GetToolList(True, "Loader").values()
		
		if not loaders:
			return

		# deselect all nodes
		flow.Select()

		dataSources = mediaBrowser.compGetImportPasses()
		updatehandle = []
		for sourceData in dataSources:
			imageData = self.getPassData(comp, sourceData)
			updatedloader, prevVersion =  self.updateLoaders(loaders, imageData['filePath'], imageData['firstFrame'], imageData['lastFrame'])
			if updatedloader:
				# Set up update feedback Dialog message
				version1 = prevVersion
				version2 = self.extract_version(updatedloader.GetAttrs('TOOLST_Clip_Name')[1])
				nodemessage = f"{updatedloader.Name}: v {str(version1)} -> v {str(version2)}"
				updatehandle.append(nodemessage)
		
		self.getUpdatedNodesFeedback(updatehandle)


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
			return self.getPassData(comp, sourceData[0], allAOVs=False)

		msgStr = "No image sequence was loaded."
		QMessageBox.warning(self.core.messageParent, "Prism Integration", msgStr)
		return None
	

	@err_catcher(name=__name__)
	def getPassData(self, comp, sourceData, allAOVs=True):
		curfr = int(comp.CurrentTime)
		if allAOVs:
			filePath = sourceData[0].replace(".####", "")
		else:
			filePath = sourceData[0].replace("####", f"{curfr:0{4}}")
		firstFrame = sourceData[1]
		lastFrame = sourceData[2]			
		aovNm = os.path.dirname(filePath).split("/")[-1]
    
		return self.returnImageDataDict(filePath, firstFrame, lastFrame, aovNm)
	

	@err_catcher(name=__name__)
	def updateLoaders(self, Loaderstocheck, filePath, firstFrame, lastFrame):
		for loader in Loaderstocheck:
			loaderClipPath = loader.Clip[0]
			if filePath == loaderClipPath:
				return loader, ".#nochange#."
			
			if self.are_paths_equal_except_version(loaderClipPath, filePath):
				version1 = self.extract_version(loaderClipPath)
				version2 = self.extract_version(filePath)

				self.reloadLoader(loader, filePath, firstFrame, lastFrame)
				if not version1 == version2:
					return loader, version1
			
		return None, ""
	

	@err_catcher(name=__name__)
	def processImageImport(self, imageData, splithandle=None, updatehandle:list=[], refNode=None):
		# Do in this function the actual importing or update of the image.		
		comp = self.fusion.GetCurrentComp()
		flow = comp.CurrentFrame.FlowView

		filePath = imageData['filePath']
		firstFrame = imageData['firstFrame']
		lastFrame = imageData['lastFrame']		
		aovNm = imageData['aovNm']
		
		extension = os.path.splitext(filePath)[1]
		# Check if path without version exists in a loader and if so generate a popup to update with new version.
		allLoaders = comp.GetToolList(False, "Loader").values()
		updatedloader, prevVersion = self.updateLoaders(allLoaders, filePath, firstFrame, lastFrame)
		# If an updated node was produced.
		if updatedloader:
			# Update Multilayer.
			if extension == ".exr":
				# check for multichannels to update all plitted nodes.
				extraloader = updatedloader
				checkedloaders:list = [updatedloader.Name]
				if len(self.get_loader_channels(updatedloader)) > 0:
					while  extraloader:
						allremainingLoaders = [t for t in allLoaders if not t.Name in checkedloaders]
						extraloader, extraversion = self.updateLoaders(allremainingLoaders, filePath, firstFrame, lastFrame)
						if extraloader:
							checkedloaders.append(extraloader.Name)

			# Set up update feedback Dialog message
			version1 = prevVersion
			version2 = self.extract_version(updatedloader.GetAttrs('TOOLST_Clip_Name')[1])
			nodemessage = f"{updatedloader.Name}: v {str(version1)} -> v {str(version2)}"
			updatehandle.append(nodemessage)

			return updatedloader

		# if paths were not updated then we create new nodes.
		comp.Lock()
		node = comp.AddTool("Loader")
		self.reloadLoader(node, filePath, firstFrame, lastFrame)
		node.SetAttrs({"TOOLS_Name": aovNm})
		if refNode:
			if refNode.GetAttrs('TOOLS_RegID') =='Loader':
				self.setNodePosition(node, x_offset = 0, y_offset = 1, refNode=refNode)
			else:
				self.setNodePosition(node, x_offset = -5, y_offset = 0, refNode=refNode)
		else:
			self.setNodePosition(node, x_offset = 0, y_offset = 0, refNode=None)
		
		comp.Unlock()
		
		# IF IS EXR
		if extension == ".exr":
			# check for multichannels
			channels = self.get_loader_channels(node)
			if len(channels) > 0:
				buttons = ["Yes", "No"]
				# if we need to manage the split dialog from outside and this is the first time the question is asked.
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
					loaders_list = self.process_multichannel(node)
					if len(loaders_list)>0:
						return loaders_list[-1]
 
				elif splithandle:
					splithandle['splitchosen'] = False

		# create wireless
		self.createWireless(node)
		flow.Select(node, True)
		
		return node
	

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
	def find_leftmost_lower_node(self, threshold):
		comp = self.fusion.GetCurrentComp()
		flow = comp.CurrentFrame.FlowView

		nodes = [t for t in comp.GetToolList(False).values() if flow.GetPosTable(t) and not t.GetAttrs('TOOLS_RegID')=='Underlay']
		if len(nodes) == 0:
			return None

		leftmost = min(nodes, key=lambda p: flow.GetPosTable(p)[1])
		downmost = max(nodes, key=lambda p: flow.GetPosTable(p)[2])

		if abs(flow.GetPosTable(downmost)[1] - flow.GetPosTable(leftmost)[1]) <= threshold:
			return downmost
		else:
			return leftmost
		

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
		flow = comp.CurrentFrame.FlowView
		loader_channels = self.get_loader_channels(tool)
		channel_data = self.get_channel_data(loader_channels)
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
			ldr.SetAttrs({'TOOLB_NameSet': True, 'TOOLS_Name': tool.Name.rsplit('_', 1)[0] + "_" + prefix})# rsplit splits from the right using in this case the first ocurrence.
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

		if len(loaders_list)>0:
			tool.Delete()
		
		comp.Unlock()
		comp.EndUndo()
		
		return loaders_list


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
	def getPythonLocation(self)-> str:
		ospath = os.path.dirname(os.__file__)
		path_components = os.path.split(ospath)
		new_path = os.path.join(*path_components[:-1])
		python_location = os.path.join(new_path, "python.exe")
		# Construct the command as a list
		return python_location


	@err_catcher(name=__name__)
	def create_and_run_bat(self):
		import subprocess
		home_dir = os.path.expanduser("~")
		bat_file_path = os.path.join(home_dir, "tmpcmdwin.bat")
		python_path = self.getPythonLocation()
		package_path = os.path.join(os.path.dirname(__file__), 'thirdparty')

		# Check if the batch file already exists
		if os.path.exists(bat_file_path):
			os.remove(bat_file_path)

		bat_content = f"""@echo off
	echo Running Python commands...
	"{python_path}" -c "import sys; sys.path.append(r'{package_path}'); import pygetwindow as gw; gw.getWindowsWithTitle('Fusion Studio - [')[0].activate()"
	@REM pause
	exit
	"""

		# Create the batch file
		with open(bat_file_path, 'w') as bat_file:
			bat_file.write(bat_content)

		return bat_file_path


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
			# script_dir = os.path.dirname(os.path.abspath(__file__))
			batch_file = self.create_and_run_bat()#os.path.join(script_dir, "cmdwin.bat")
			cmdwin = subprocess.Popen(["cmd", "/c", "start", batch_file], shell=True)
			time.sleep(1)
			# Delete the batch file
			os.remove(batch_file)
			
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
	def importBlenderCam(self, importPath, origin):
		from MH_BlenderCam_Fusion_Importer import BlenderCameraImporter
		BcamImporter = BlenderCameraImporter()
		return BcamImporter.import_blender_camera(importPath)


	@err_catcher(name=__name__)
	def sm_import_disableObjectTracking(self, origin):
		self.deleteNodes(origin, [origin.setName])


	#Main Import function
	@err_catcher(name=__name__)
	def sm_import_importToApp(self, origin, doImport, update, impFileName):
		# Check if a .bcam file exists, if so, prefer it over the abc, this means a Mh blender camera.
		root, _ = os.path.splitext(impFileName)
		isbcam = False
		new_file_path = os.path.normpath(root + '.bcam')
		if os.path.exists(new_file_path):
			isbcam = True
			impFileName = new_file_path
		
		comp = self.fusion.GetCurrentComp()
		flow = comp.CurrentFrame.FlowView
		fileName = os.path.splitext(os.path.basename(impFileName))
		origin.setName = ""
		result = False
		# Check that we are not importing in a comp different than the one we started the stateManager from
		if self.sm_checkCorrectComp(comp):
			#try to get an active tool to set a ref position
			activetool = None
			try:
				activetool = comp.ActiveTool()
			except:
				pass
			if activetool and not activetool.GetAttrs("TOOLS_RegID") =="BezierSpline":
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
				if isbcam:
					importedNodes = []
					importedNodes.append(self.getNode(newNodes[0]))
					origin.setName = "Import_" + fileName[0]			
					origin.nodes = importedNodes
				else:
					refPosNode, positionedNodes = self.ReplaceBeforeImport(origin, newNodes)
					self.cleanbeforeImport(origin)
					if refPosNode:
						atx, aty = flow.GetPosTable(refPosNode).values()
			
					importedTools = comp.GetToolList(True).values()
					#Set the position of the imported nodes relative to the previously active tool or last click in compView
					impnodes = [n for n in importedTools]
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

				#Deselect All
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

			# If there is a previous version of the same node.
			if oldnode:
				# idx = 1
				# check if it has valid inputs that are not part of previous import
				for input in oldnode.GetInputList().values():
					# idx+=1
					connectedOutput = input.GetConnectedOutput()
					if connectedOutput:
						inputName = input.Name
						connectedtool = connectedOutput.GetTool()
						# Avoid Feyframe nodes
						if not connectedtool.GetAttrs("TOOLS_RegID") =="BezierSpline" and not newnode.GetAttrs("TOOLS_RegID") == "Merge3D":
							# check to avoid a connection that breaks the incoming hierarchy.
							if not connectedtool.Name in nodenames:
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
		comp = self.fusion.GetCurrentComp()
		if self.sm_checkCorrectComp(comp):
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
		# return -32768, -32768


	@err_catcher(name=__name__)
	def find_extreme_loader(self):
		# Get the current composition
		comp = self.fusion.GetCurrentComp()
		flow = comp.CurrentFrame.FlowView()

		# Initialize variables to track the leftmost lower Loader node
		leftmost_lower_loader = None
		min_x = -float('inf')
		min_y = float('inf')

		# Iterate through all tools in the composition
		for tool in comp.GetToolList().values():
			# Check if the tool is of type "Loader"
			if tool.GetAttrs()['TOOLS_RegID'] == 'Loader':
				# Get the position of the Loader node
				position = flow.GetPosTable(tool)
				
				if position:
					x, y = position[1], position[2]
					# Check if this Loader node is the leftmost lower node
					if (y < min_y) or (y == min_y and x < min_x):
						min_x = x
						min_y = y
						leftmost_lower_loader = tool

		# Output the leftmost lower Loader node
		return leftmost_lower_loader


	@err_catcher(name=__name__)
	def find_extreme_position(self, thisnode=None, ignore_node_type=None, find_min=True):
		comp = self.fusion.GetCurrentComp()
		flow = comp.CurrentFrame.FlowView

		if find_min:
			thresh_x_position, thresh_y_position = float('inf'), float('inf')
		else: 
			thresh_x_position, thresh_y_position = -float('inf'), float('inf')

		extreme_node = None

		all_nodes = comp.GetToolList(False).values()

		for node in all_nodes:
			if thisnode and node.Name == thisnode.Name:
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
	def setNodePosition(self, node, find_min=True, x_offset=-2, y_offset=0, ignore_node_type=None, refNode=None):
		# Get the active composition
		comp = self.fusion.GetCurrentComp()
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
			self.set_node_position(flow, node, thresh_x_position + x_offset, thresh_y_position + y_offset)
		else:
			flow.Select()
			x,y = self.find_LastClickPosition()
			flow.SetPos(node, x, y)


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
	def sm_checkCorrectComp(self, comp, displaypopup=True):
		if self.comp:
			try:
				if self.comp.GetAttrs("COMPS_Name") == comp.GetAttrs("COMPS_Name"):
					return True
				else:
					raise Exception
			except:
				if displaypopup:
					self.core.popup("""The State Manager was originally opened in another comp.\n 
					It will now close and open again to avoid corrupting this comp's state data.""")
					self.core.closeSM(restart=True)
				return False
			
		return True
	
	
	@err_catcher(name=__name__)
	def sm_getExternalFiles(self, origin):
		extFiles = []
		return [extFiles, []]
	

	@err_catcher(name=__name__)
	def setDefaultState(self):
		comp = self.fusion.GetCurrentComp()
		if self.sm_checkCorrectComp(comp):
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
		if self.sm_checkCorrectComp(comp):
			comp.SetData("prismstates", buf + "_..._")


	@err_catcher(name=__name__)
	def sm_saveImports(self, origin, importPaths):
		comp = self.fusion.CurrentComp
		if self.sm_checkCorrectComp(comp):
			prismdata = comp.GetData("prismstates")
			prismdata += importPaths.replace("\\\\", "\\")
			comp.SetData("prismstates", prismdata)


	@err_catcher(name=__name__)
	def sm_readStates(self, origin):
		comp = self.fusion.CurrentComp
		if self.sm_checkCorrectComp(comp):
			prismdata = comp.GetData("prismstates")
			return prismdata.split("_..._")[0]


	@err_catcher(name=__name__)
	def sm_deleteStates(self, origin):
		comp = self.fusion.CurrentComp
		if self.sm_checkCorrectComp(comp):
			comp.SetData("prismstates","")


	@err_catcher(name=__name__)
	def getImportPaths(self, origin):
		comp = self.fusion.CurrentComp
		if self.sm_checkCorrectComp(comp):
			prismdata = comp.GetData("prismstates")
			return prismdata.split("_..._")[1]


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
		try:
			self.popup.close()
		except:
			pass


	def onProjectBrowserClose(self, origin):
		self.pbUI = None


	@err_catcher(name=__name__)
	def onProjectBrowserCalled(self, popup=None):
		#Feedback in case it takes time to open
		try:
			self.popup.close()
		except:
			pass
		if popup:
			self.popup = popup


	@err_catcher(name=__name__)
	def onStateManagerCalled(self, popup=None):
		#Feedback in case it takes time to open
		comp = self.fusion.GetCurrentComp()
		self.sm_checkCorrectComp(comp, displaypopup=False)
		#Set the comp used when sm was oppened for reference when saving states.
		self.comp = comp	
		try:
			self.popup.close()
		except:
			pass
		if popup:
			self.popup = popup


	@err_catcher(name=__name__)
	def onStateManagerOpen(self, origin):
		#Remove Export and Playblast buttons and states
		origin.b_createExport.deleteLater()
		origin.b_createPlayblast.deleteLater()

		# Create a new button
		origin.b_renderGroup = QPushButton(origin.w_CreateExports)
		origin.b_renderGroup.setObjectName("b_renderGroup")
		origin.b_renderGroup.setText("RenderGroup")

		# Set the size policy to expanding to make it wider
		origin.b_renderGroup.setMaximumSize(QSize(150, 16777215))
		sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
		origin.b_renderGroup.setSizePolicy(sizePolicy)

		# Insert the new button before b_showExportStates
		index = origin.horizontalLayout_4.indexOf(origin.b_showExportStates)
		origin.horizontalLayout_4.insertWidget(index - 1, origin.b_renderGroup)

		origin.b_renderGroup.clicked.connect(lambda: self.addRenderGroup(origin))

		# origin.createState(appStates["stateType"], parent=parent, setActive=True, **appStates.get("kwargs", {}))

		sm = self.core.getStateManager()
		removestates = ['Code', 'Export', 'Playblast']
		for state in removestates:
			if state in sm.stateTypes.keys():
				del sm.stateTypes[state]

		comp = self.fusion.GetCurrentComp()
		
		#Set the comp used when sm was opened for reference when saving states.
		self.comp = comp
		#Set State Manager Data on first open.
		if comp.GetData("prismstates") is None:
			self.setDefaultState()

		self.monkeypatchedsm = origin
		self.core.plugins.monkeyPatch(origin.rclTree, self.rclTree, self, force=True)

		#origin.gb_import.setStyleSheet("margin-top: 20px;")


	@err_catcher(name=__name__)
	def onStateManagerShow(self, origin):
		self.smUI = origin

		##	Resizes the StateManager Window
		# 	Check if SM has a resize method and resize it
		if hasattr(self.smUI, 'resize'):
			self.smUI.resize(800, self.smUI.size().height())

		#	Check if SM has a splitter resize method
		if hasattr(self.smUI, 'splitter') and hasattr(self.smUI.splitter, 'setSizes'):
			# Splitter position
			splitterPos = 350

			# 	Calculate the sizes for the splitter
			height = self.smUI.splitter.size().height()
			LeftSize = splitterPos
			RightSize = height - splitterPos

			# 	Set the sizes of the splitter areas
			self.smUI.splitter.setSizes([LeftSize, RightSize])

		try:
			self.popup.close()
		except:
			pass


	@err_catcher(name=__name__)
	def onStateManagerClose(self, origin):
		self.smUI = None


	@err_catcher(name=__name__)
	def onStateCreated(self, origin, state, stateData):
		if state.className in ["ImageRender", "Playblast"]:
			state.b_resPresets.setStyleSheet("padding-left: 1px;padding-right: 1px;")

		if state.className == "Folder":
			origin.tw_export.itemChanged.connect(self.sm_onfolderToggle)


	@err_catcher(name=__name__)
	def sm_onfolderToggle(self, item, column):
		# item is the same as a state.
		if item.ui.className == "Folder":
			for i in range(item.childCount()):
				curState = item.child(i)
				if item.checkState(0) == Qt.Checked:
					curState.setCheckState(0, Qt.Checked)
				else:
					curState.setCheckState(0, Qt.Unchecked)


	@err_catcher(name=__name__)
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
		# elif stateui.className == "ImportFile":
			

	@err_catcher(name=__name__)
	def addRenderGroup(self, origin):
		origin.createState("RenderGroup")


			
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
			rcmenu = QMenu(sm)

            # we check if the rclick is over a state
			idx = sm.activeList.indexAt(pos)
			parentState = sm.activeList.itemFromIndex(idx)
			if parentState:
				sm.rClickedItem = parentState

				if parentState.ui.className == "ImportFile":
					self.monkeypatchedimportstate = parentState.ui
					self.core.plugins.monkeyPatch(parentState.ui.preDelete, self.preDelete, self, force=True)

				#From here the only line that changes is the commented one in "render" state.
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

				# Check if it is Image Render #
				if parentState.ui.className != "ImageRender":
					menuExecuteV.setEnabled(False)
				###############################

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


	@err_catcher(name=__name__)
	def preDelete(
		self,
		item=None,
		baseText="Do you also want to delete the connected objects?\n\n",
	):
		state = self.monkeypatchedimportstate
		if len(state.nodes) <= 0 or state.stateMode == "ApplyCache":
			return
		message = baseText
		validNodes = [
			x for x in state.nodes if self.core.appPlugin.isNodeValid(state, x)
		]
		if validNodes:
			for idx, val in enumerate(validNodes):
				if idx > 5:
					message += "..."
					break
				else:
					message += self.core.appPlugin.getNodeName(state, val) + "\n"

			if not self.core.uiAvailable:
				action = 0
				print("delete objects:\n\n%s" % message)
			else:
				msg = QMessageBox(
					QMessageBox.Question, "Delete state", message, QMessageBox.No
				)
				msg.addButton("Yes", QMessageBox.YesRole)
				msg.setParent(self.core.messageParent, Qt.Window)
				action = msg.exec_()
				clicked_button = msg.clickedButton()
				result = clicked_button.text()
			# if action == 2:
			if result == "Yes":
				self.core.appPlugin.deleteNodes(state, validNodes)
