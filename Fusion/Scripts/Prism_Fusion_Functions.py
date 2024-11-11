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
import uuid
import hashlib
import logging
from datetime import datetime

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

logger = logging.getLogger(__name__)



class Prism_Fusion_Functions(object):
	def __init__(self, core, plugin):
		self.core = core
		self.plugin = plugin
		self.fusion = bmd.scriptapp("Fusion")
		self.comp = None # This comp is used by the state Manager to avoid overriding the state data on wrong comps
		self.monkeypatchedsm = None # Reference to the state manager to be used on the monkeypatched functions.
		self.monkeypatchedmediabrowser = None # Reference to the mediabrowser to be used on the monkeypatched functions.
		self.monkeypatchedimportstate = None # Reference to the importState to be used on the monkeypatched functions.
		self.popup = None # Reference of popUp dialog that shows before opening a window when it takes some time.

		self.listener = None
		
		self.saveUI = None
		self.smUI = None
		self.pbUI = None
		self.prefUI = None

		#	Register Callbacks
		try:
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
			logger.debug("Registered callbacks")

		except Exception as e:
			logger.warning(f"ERROR: Failed to register callbacks:\n{e}")
		
		self.importHandlers = {
			".abc": {"importFunction": self.importAlembic},
			".fbx": {"importFunction": self.importFBX},
			".bcam":{"importFunction": self.importBlenderCam},
			".usd":{"importFunction": self.importUSD},
			".usda":{"importFunction": self.importUSD},
			".usdc":{"importFunction": self.importUSD}
		}

		# self.exportHandlers = {
		# 	".abc": {"exportFunction": self.exportAlembic},
		# 	".fbx": {"exportFunction": self.exportFBX},
		# 	".obj": {"exportFunction": self.exportObj},
		# 	".blend": {"exportFunction": self.exportBlend},
		# }

		#	Format dict to differentiate still/movie types
		self.outputFormats = [
			{"extension": ".exr", "fuseName": "OpenEXRFormat", "type": "image"},
			{"extension": ".dpx", "fuseName": "DPXFormat", "type": "image"},
			{"extension": ".png", "fuseName": "PNGFormat", "type": "image"},
			{"extension": ".tif", "fuseName": "TiffFormat", "type": "image"},
			{"extension": ".jpg", "fuseName": "JpegFormat", "type": "image"},
			{"extension": ".mov", "fuseName": "QuickTimeMovies", "type": "video"},
			{"extension": ".mp4", "fuseName": "QuickTimeMovies", "type": "video"},
			{"extension": ".mxf", "fuseName": "MXFFormat", "type": "video"},
			{"extension": ".avi", "fuseName": "AVIFormat", "type": "video"}
		]
		#	ARCHIVED FORMATS FOR LATER USE - THESE ARE THE NAMES FUSION USES
			# "PIXFormat": "pix",             # Alias PIX
			# "IFFFormat": "iff",             # Amiga IFF
			# "CineonFormat": "cin",          # Kodak Cineon
			# "DPXFormat": "dpx",             # DPX
			# "FusePicFormat": "fusepic",     # Fuse Pic
			# "FlipbookFormat": "fb",         # Fusion Flipbooks
			# "RawFormat": "raw",             # Fusion RAW Image
			# "IFLFormat": "ifl",             # Image File List (Text File)
			# "IPLFormat": "ipl",             # IPL
			# "JpegFormat": "jpg",            # JPEG
			# "Jpeg2000Format": "jp2",        # JPEG2000
			# "MXFFormat": "mxf",             # MXF - Material Exchange Format
			# "OpenEXRFormat": "exr",         # OpenEXR
			# "PandoraFormat": "piyuv10",     # Pandora YUV
			# "PNGFormat": "png",             # PNG
			# "VPBFormat": "vpb",             # Quantel VPB
			# "QuickTimeMovies": "mov",       # QuickTime Movie
			# "HDRFormat": "hdr",             # Radiance
			# "SixRNFormat": "6RN",           # Rendition
			# "SGIFormat": "sgi",             # SGI
			# "PICFormat": "si",              # Softimage PIC
			# "SUNFormat": "RAS",             # SUN Raster
			# "TargaFormat": "tga",           # Targa
			# "TiffFormat": "tiff",           # TIFF
			# "rlaFormat": "rla",             # Wavefront RLA
			# "BMPFormat": "bmp",             # Windows BMP
			# "YUVFormat": "yuv",             # YUV



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
			logger.warning("ERROR: Linux is not supported at this time")
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
			if os.path.isfile(icon):
				return icon
			else:
				logger.warning("ERROR: Fusion auto-save icon not found")

		return None
	

	@err_catcher(name=__name__)
	def sceneOpen(self, origin):
		# if self.core.shouldAutosaveTimerRun():
		# 	origin.startAutosaveTimer()
		pass


	#	Returns Current Comp
	@err_catcher(name=__name__)
	def getCurrentComp(self):
		try:
			curComp = self.fusion.GetCurrentComp()
			# logger.debug(f"CurrentComp: {curComp.GetAttrs('COMPS_Name')}")
			return curComp
		except Exception as e:
			logger.warning(f"ERROR: Failed to resolve the current Fusion comp:\n{e}")
			return None
	

	#	Returns the filename of the current comp
	@err_catcher(name=__name__)
	def getCurrentFileName(self, origin=None, path=True):
		curComp = self.getCurrentComp()
		try:
			if curComp is None:
				currentFileName = ""
			else:
				currentFileName = self.getCurrentComp().GetAttrs()["COMPS_FileName"]
				# logger.debug(f"Current filename: {currentFileName}")

			return currentFileName
		
		except Exception as e:
			logger.warning(f"ERROR: Failed to get current filename:\n{e}")
	

	@err_catcher(name=__name__)
	def getSceneExtension(self, origin):
		return self.sceneFormats[0]
	

	@err_catcher(name=__name__)
	def saveScene(self, origin, filepath, details={}):
		try:
			#Save function returns True on success, False on failure
			result = self.getCurrentComp().Save(filepath)
			if result:
				logger.debug(f"Saved file to {filepath}")
				return True
			else:
				raise Exception
		except:
			logger.warning(f"ERROR: Failed to save {filepath}")
			return False
	

	@err_catcher(name=__name__)
	def getFrameRange(self, origin):
		try:
			startframe = self.getCurrentComp().GetAttrs()["COMPN_GlobalStart"]
			endframe = self.getCurrentComp().GetAttrs()["COMPN_GlobalEnd"]
			return [startframe, endframe]
		except:
			logger.warning("ERROR: Failed to get current frame range")
			return [None, None]
	

	#	Sets the supplied framerange to the comp
	@err_catcher(name=__name__)
	def setFrameRange(self, origin, startFrame, endFrame):
		comp = self.getCurrentComp()
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


	#	Returns the framerange key/value to be used in the render command
	@err_catcher(name=__name__)
	def getFrameRangeRenderCmd(self, comp, rSettings, group):
		renderCmd = {}

		try:
			#	ImageRender
			if not group:
				#	Range types other than expression
				if rSettings["rangeType"] != "Expression":
					renderCmd['Start'] = rSettings["startFrame"]
					renderCmd['End'] = rSettings["endFrame"]

				#	Range type is expression	
				else:
					renderCmd["FrameRange"] = ", ".join(str(i) for i in rSettings["frames"])

			#	RenderGroup
			else:
				#	If framerange override from group
				if "frameOvr" in rSettings and rSettings["frameOvr"]:
					#	If range type is not expression
					if rSettings["rangeType"] != "Expression":
						renderCmd['Start'] = int(rSettings["frame_start"])
						renderCmd['End'] = int(rSettings["frame_end"])

					#	If range type is expression	
					else:
						renderCmd["FrameRange"] = ", ".join(str(i) for i in rSettings["frames"])

				#	If no override uses comp range
				else:
					renderCmd['Start'], renderCmd['End'] = self.getFrameRange(self)

			return renderCmd
		
		except Exception as e:
			logger.warning(f"ERROR: Failed to construct framerange renderCmd:\n{e}")
			return ""


	@err_catcher(name=__name__)
	def getFPS(self, origin):
		try:
			return self.getCurrentComp().GetPrefs()["Comp"]["FrameFormat"]["Rate"]
		except Exception as e:
			logger.warning(f"ERROR: Failed to get the fps from comp:\n{e}")
			return None
	

	@err_catcher(name=__name__)
	def setFPS(self, origin, fps):
		try:
			return self.getCurrentComp().SetPrefs({"Comp.FrameFormat.Rate": fps})
		except:
			logger.warning(f"ERROR: Failed to set the fps to the comp:\n{e}")


	@err_catcher(name=__name__)
	def getResolution(self):
		try:
			width = self.getCurrentComp().GetPrefs()[
				"Comp"]["FrameFormat"]["Width"]
			height = self.getCurrentComp().GetPrefs()[
				"Comp"]["FrameFormat"]["Height"]
			return [width, height]
		
		except Exception as e:
			logger.warning(f"ERROR: Failed to get the current resolution from the comp:\n{e}")
			return [None, None]


	@err_catcher(name=__name__)
	def setResolution(self, width=None, height=None):
		try:
			self.getCurrentComp().SetPrefs(
				{
					"Comp.FrameFormat.Width": width,
					"Comp.FrameFormat.Height": height,
				}
			)
		except Exception as e:
			logger.warning(f"ERROR: Failed to set the resolution to the comp:\n{e}")


	#	Creates UUID
	@err_catcher(name=__name__)
	def createUUID(self, simple=False, length=8):
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


	# @err_catcher(name=__name__)
	# def updateReadNodes(self):
	# 	updatedNodes = []
	# 	comp = self.getCurrentComp()

	# 	selNodes = comp.GetToolList(True, "Loader")
	# 	if len(selNodes) == 0:
	# 		selNodes = comp.GetToolList(False, "Loader")

	# 	if len(selNodes):
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
		try:
			return self.fusion.Version
		except:
			return None


	@err_catcher(name=__name__)
	def openScene(self, origin, filepath, force=False):
		if os.path.splitext(filepath)[1] not in self.sceneFormats:
			return False

		try:
			self.fusion.LoadComp(filepath)
			logger.debug(f"Loaded scenefile: {filepath}")
		except:
			logger.warning("ERROR: Failed to load Comp")

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
		comp = self.getCurrentComp()
		flow = comp.CurrentFrame.FlowView

		comp.Lock()
		comp.StartUndo()
		try:
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
				comp.Render()

				# Restore the original render range
				comp.SetAttrs({'COMPN_RenderStart' : origStartFrame})
				comp.SetAttrs({'COMPN_RenderEnd' : origEndFrame})

			#   Deals with the frame number suffix added by Fusion rener
			pattern = os.path.join(tempDir, thumbName + "*.jpg")
			renderedThumbs = glob.glob(pattern)

			if renderedThumbs:
				renderedThumb = renderedThumbs[0]  # Assuming only one matching file
				os.rename(renderedThumb, thumbPath)
				logger.debug(f"Created Thumbnail from: {self.getNodeNameByTool(thumbTool)}")
			
		except Exception as e:
			logger.warning(f"ERROR: Filed to create thumbnail:\n{e}")

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
		if os.path.isfile(thumbPath):
			pm = self.core.media.getPixmapFromPath(thumbPath)
		else:
			pm = None

		#   Delete temp dir
		if os.path.exists(tempDir):
			shutil.rmtree(tempDir)

		return pm


	# Handle Savers pass-through state for thumb capture
	@err_catcher(name=__name__)
	def origSaverStates(self, mode, comp, origSaverList):
		saverList = self.getSaverList(comp)
		for tool in saverList:
			toolName = self.getNodeNameByTool(tool)

			if mode == "save":
				# Save the current pass-through state
				origSaverList[toolName] = self.isPassThrough(node=tool)
				self.setPassThrough(node=tool, passThrough=True)
			elif mode == "load":
				# Restore the original pass-through state
				if toolName in origSaverList:
					self.setPassThrough(node=tool, passThrough=origSaverList[toolName])

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
			if self.isSaver(tool) and not self.isPassThrough(node=tool):
				return tool

		# 3. Check for any saver, even if pass-through
		for tool in comp.GetToolList(False).values():
			if self.isSaver(tool):
				return tool

		# 4. Fallback to the final tool in the flow
		return self.getLastTool(comp) or None



	###############################################
	#											  #
	#					NODES					  #
	#											  #
	###############################################

	#   Checks if tool is a Saver, or custom Saver type
	@err_catcher(name=__name__)
	def isSaver(self, tool):
		# Check if tool is valid
		if not tool:
			return False
		try:
			# Check if tool name is 'Saver' (should work if node is renamed)
			if tool.GetAttrs({"TOOLS_Name"})["TOOLS_RegID"] == "Saver":
				return True
			else:
				return False
		except:
			return False
	

	#   Tries to find last tool in the flow
	@err_catcher(name=__name__)
	def getLastTool(self, comp):
		try:
			for tool in comp.GetToolList(False).values():
				if not self.hasConnectedOutputs(tool):
					return tool
			return None
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
	

	# Checks if tool is set to pass-through mode
	@err_catcher(name=__name__)
	def isPassThrough(self, nodeUID=None, node=None):
		if nodeUID:
			node = self.getNodeByUID(nodeUID)

		return node and node.GetAttrs({"TOOLS_Name"})["TOOLB_PassThrough"]


	#	Sets the Fusion node's passthrough
	@err_catcher(name=__name__)
	def setPassThrough(self, nodeUID=None, node=None, passThrough=False):
		if nodeUID:
			node = self.getNodeByUID(nodeUID)
		node.SetAttrs({"TOOLB_PassThrough": passThrough})


	#	Checks if a matching tool exists in the comp
	@err_catcher(name=__name__)
	def rendernodeExists(self, nodeUID):
		if self.getNodeByUID(nodeUID):
			return True
		
		return False
	
	#	
	@err_catcher(name=__name__)
	def getNodeType(self, tool):
		try:
			return tool.GetAttrs("TOOLS_RegID")
		except:
			logger.warning("ERROR: Cannot retrieve node type")
			return None
	

	@err_catcher(name=__name__)
	def getNodeByUID(self, nodeUID):
		comp = self.getCurrentComp()
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
	def getNodeNameByUID(self, nodeUID):
		tool = self.getNodeByUID(nodeUID)
		toolName = self.getNodeNameByTool(tool)

		return toolName
	
	
	@err_catcher(name=__name__)
	def getNodeNameByTool(self, tool):
		try:
			toolName = tool.GetAttrs()["TOOLS_Name"]
			return toolName
		except:
			logger.warning(f"ERROR: Cannot get name for {tool}")
			return None
	

	#	Returns Fusion-legal Saver name base on State name
	@err_catcher(name=__name__)
	def getRendernodeName(self, stateName):
		legalName = self.getFusLegalName(stateName)
		nodeName = f"PrSAVER_{legalName}"

		return nodeName
	
	
	#	Creates Saver with UUID associated with ImageRender state
	@err_catcher(name=__name__)
	def createRendernode(self, nodeName, nodeUID):
		comp = self.getCurrentComp()
		if self.sm_checkCorrectComp(comp):
			if not self.rendernodeExists(nodeUID):
				comp.Lock()
				sv = comp.Saver()
				sv.SetAttrs({'TOOLS_Name' : nodeName})
				sv.SetData('Prism_UUID', nodeUID)
				comp.Unlock()

				if not self.posRelativeToNode(sv):
					try:
						#Move Render Node to the Right of the scene	
						self.setNodePosition(sv, find_min=False, x_offset=10, ignore_node_type="Saver")
						self.stackNodesByType(sv)
					except:
						logger.debug(f"ERROR: Not able to position {nodeName}")

			if sv:
				logger.debug(f"Saver created for: {nodeName} - {nodeUID}")
				return sv
			else:
				logger.warning(f"ERROR: Unable to create Saver for {nodeName}")
				return False


	#	Updates Saver node name
	@err_catcher(name=__name__)
	def updateRendernode(self, nodeName, nodeUID):
		comp = self.getCurrentComp()
		if self.sm_checkCorrectComp(comp):
			sv = self.getNodeByUID(nodeUID)

			if sv:
				comp.Lock()
				sv.SetAttrs({'TOOLS_Name' : nodeName})
				comp.Unlock()

				logger.debug(f"Saver updated: {self.getNodeNameByUID(nodeUID)}")
			else:
				logger.warning(f"ERROR: Not able to update: {nodeName}")

			return sv
		

	#	Configures Saver filepath and image format
	@err_catcher(name=__name__)
	def configureRenderNode(self, nodeUID, outputPath, fuseName=None):
		comp = self.getCurrentComp()
		if self.sm_checkCorrectComp(comp):
			sv = self.getNodeByUID(nodeUID)
			if sv:
				sv.Clip = outputPath
				if fuseName:
					try:
						sv["OutputFormat"] = fuseName
					except:
						logger.warning(f"ERROR: Could not set node format to {fuseName}")

				if sv.Input.GetConnectedOutput():
					sv.Clip = outputPath
					logger.debug(f"Configured Saver: {self.getNodeNameByUID(nodeUID)}")

				else:
					logger.debug(f"ERROR: Render Node is not connected: {nodeUID}")
			else:
				logger.warning(f"ERROR: Render Node does not exist: {nodeUID}")
	

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
	def getCamNodes(self, origin, cur=False):
		sceneCams = []  # get cams from scene
		if cur:
			sceneCams = ["Current View"] + sceneCams

		return sceneCams
	

	@err_catcher(name=__name__)												#	TODO - USED?
	def getCamName(self, origin, handle):
		if handle == "Current View":
			return handle

		return str(nodes[0])
	

	@err_catcher(name=__name__)												#	TODO - USED?
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
	

	#	Arranges nodes in a vertcal stack
	@err_catcher(name=__name__)
	def stackNodesByType(self, nodetostack, yoffset=3, tooltype="Saver"):
		comp = self.getCurrentComp()
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



	# @err_catcher(name=__name__)
	# def refreshNodees(self):
	# 	comp = self.getCurrentComp()
	# 	# Iterate through all tools in the composition
	# 	tools = comp.GetToolList(False)

	# 	for tool_name, tool in tools.items():  # tool_name is the key, tool is the value
	# 		toolUID = tool.GetData('Prism_UUID')

    #     # Check if the tool has the attribute 'Prism_UUID' and if it matches the provided UID
	# 		if toolUID == nodeUID:
	# 			return tool
			
	# 	return None




	@err_catcher(name=__name__)
	def sm_render_preSubmit(self, origin, rSettings):
		pass


	###############################
	#	REPLACE PATHS FOR SUBMIT  #
	###############################
	# @err_catcher(name=__name__)
	# def getReplacedPaths(self, comp, filepath):
	# 	pathmaps = comp.GetCompPathMap(False, False)
	# 	pathexists = False
	# 	isnetworkpath = False
	# 	for k in pathmaps.keys():
	# 		if k in filepath:
	# 			index = filepath.find(k)

	# 			if index != -1:  # Check if substring exists
	# 				# Replace "brown" with "red"
	# 				new_path = filepath[:index] + pathmaps[k] + "/" + filepath[index + len(k):]
	# 				formatted_path = os.path.normpath(new_path)
	# 				# Check if the formatted path exists
	# 				if os.path.exists(formatted_path):
	# 					pathexists = True
	# 				# Check if path is local
	# 				drive_letter, _  = os.path.splitdrive(formatted_path)
	# 				drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive_letter)
	# 				isnetworkpath = drive_type == 4 or formatted_path.startswith("\\\\")

	# 				return {"path":formatted_path, "valid":pathexists, "net":isnetworkpath}
		
	# 	return {"path":None, "valid":pathexists, "net":isnetworkpath}
	

	# @err_catcher(name=__name__)
	# def replacePathMapsLUTFiles(self, comp):
	# 	oldcopy = pyperclip.paste()
	# 	# Input text		
	# 	all_OCIO_FT = comp.GetToolList(False, "OCIOFileTransform").values()
	# 	all_FileLUT = comp.GetToolList(False, "FileLUT").values()
	# 	luttools = list(all_OCIO_FT) + list(all_FileLUT)

	# 	for tool in luttools:
	# 		comp.Copy(tool)
	# 		text = pyperclip.paste()
	# 		# Define regular expression pattern to match the desired substring
	# 		pattern = r'LUTFile = Input { Value = "(.*?)"'

	# 		# Search for the pattern in the text
	# 		match = re.search(pattern, text)

	# 		# If a match is found, extract the substring after "Value ="
	# 		if match:
	# 			filepath = match.group(1)
	# 			pathinfo = self.getReplacedPaths(comp, filepath)
	# 			newpath = pathinfo["path"]
	# 			if newpath:
	# 				tool.LUTFile = newpath
	# 		else:
	# 			print("Pattern not found in the text.")
	# 	pyperclip.copy(oldcopy)


	# @err_catcher(name=__name__)
	# def replacePathMapsOCIOCS(self, comp):
	# 	oldcopy = pyperclip.paste()
	# 	# Input text
	# 	all_OCIO_CS = comp.GetToolList(False, "OCIOColorSpace").values()

	# 	for tool in all_OCIO_CS:
	# 		comp.Copy(tool)
	# 		text = pyperclip.paste()
	# 		# Define regular expression pattern to match the desired substring
	# 		pattern = r'OCIOConfig\s*=\s*Input\s*{\s*Value\s*=\s*"([^"]+)"'

	# 		# Search for the pattern in the text
	# 		match = re.search(pattern, text)

	# 		# If a match is found, extract the substring after "Value ="
	# 		if match:
	# 			filepath = match.group(1)
	# 			pathinfo = self.getReplacedPaths(comp, filepath)
	# 			newpath = pathinfo["path"]
	# 			if newpath:
	# 				tool.OCIOConfig = newpath
	# 		else:
	# 			print("Pattern not found in the text.")
	# 	pyperclip.copy(oldcopy)
	

	# def replacePathMapsFBX(self, comp):
	# 	oldcopy = pyperclip.paste()
	# 	# Input text
	# 	all_fbx  = comp.GetToolList(False, "SurfaceFBXMesh").values()

	# 	for tool in all_fbx:
	# 		comp.Copy(tool)
	# 		text = pyperclip.paste()
	# 		# Define regular expression pattern to match the desired substring
	# 		pattern = r'ImportFile = Input { Value = "(.*?)", },'

	# 		# Search for the pattern in the text
	# 		match = re.search(pattern, text)

	# 		# If a match is found, extract the substring after "Value ="
	# 		if match:
	# 			filepath = match.group(1)
	# 			pathinfo = self.getReplacedPaths(comp, filepath)
	# 			newpath = pathinfo["path"]
	# 			tool.ImportFile = newpath
	# 		else:
	# 			print("Pattern not found in the text.")
	# 	pyperclip.copy(oldcopy)


	# def replacePathMapsABC(self, comp):
	# 	pathdata = []
	# 	oldcopy = pyperclip.paste()
	# 	# Input text
	# 	all_alembic  = comp.GetToolList(False, "SurfaceAlembicMesh").values()

	# 	for tool in all_alembic:
	# 		comp.Copy(tool)
	# 		text = pyperclip.paste()
	# 		# Define regular expression pattern to match the desired substring
	# 		pattern = r'Filename = Input { Value = "(.*?)", },'

	# 		# Search for the pattern in the text
	# 		match = re.search(pattern, text)

	# 		# If a match is found, extract the substring after "Value ="
	# 		if match:
	# 			filepath = match.group(1)
	# 			pathinfo = self.getReplacedPaths(comp, filepath)
	# 			newpath = pathinfo["path"]
	# 			if newpath:
	# 				tool.Filename = newpath
	# 				pathdata.append({"node": tool.Name, "path":pathinfo["path"], "valid":pathinfo["valid"], "net":pathinfo["net"]})
			
	# 	pyperclip.copy(oldcopy)
	# 	return pathdata
	

	# @err_catcher(name=__name__)
	# def replacePathMapsbyPattern(self, comp, tool_list, regexpattern, pathInput):
	# 	pathdata = []
	# 	oldcopy = pyperclip.paste()

	# 	for tool in tool_list:
	# 		comp.Copy(tool)
	# 		text = pyperclip.paste()
	# 		# Define regular expression pattern to match the desired substring
	# 		pattern = regexpattern
	# 		# Search for the pattern in the text
	# 		match = re.search(pattern, text)

	# 		# If a match is found, extract the substring after "Value ="
	# 		if match:
	# 			filepath = match.group(1)
	# 			pathinfo = self.getReplacedPaths(comp, filepath)
	# 			newpath = pathinfo["path"]
	# 			if newpath:
	# 				setattr(tool, pathInput, newpath)
	# 				pathdata.append({"node": tool.Name, "path":pathinfo["path"], "valid":pathinfo["valid"], "net":pathinfo["net"]})
			
	# 	pyperclip.copy(oldcopy)
	# 	return pathdata
	

	# @err_catcher(name=__name__)
	# def replacePathMapsIOtools(self, comp):
	# 	pathdata = []
	# 	all_loader = comp.GetToolList(False, "Loader").values()
	# 	all_saver  = comp.GetToolList(False, "Saver").values()
	# 	iotools = list(all_loader) + list(all_saver)
	# 	comp.Lock()
	# 	for tool in iotools:
	# 		filepath = tool.GetAttrs("TOOLST_Clip_Name")[1]
	# 		pathinfo = self.getReplacedPaths(comp, filepath)
	# 		newpath = pathinfo["path"]
	# 		if newpath:
	# 			tool.Clip = newpath			
	# 			pathdata.append({"node": tool.Name, "path":pathinfo["path"], "valid":pathinfo["valid"], "net":pathinfo["net"]})

	# 	comp.Unlock()
	# 	return pathdata


	###############################
	#		 RENDERING  		  #
	###############################

	# @err_catcher(name=__name__)
	# def sm_render_CheckSubmittedPaths(self):
	# 	comp = self.getCurrentComp()
	# 	allpathdata = []

	# 	# get Paths
	# 	allpathdata += self.replacePathMapsIOtools(comp)
	# 	# self.replacePathMapsABC(comp)
	# 	# self.replacePathMapsFBX(comp)
	# 	# self.replacePathMapsOCIOCS(comp)
	# 	# self.replacePathMapsLUTFiles(comp)
	# 	all_alembic  = comp.GetToolList(False, "SurfaceAlembicMesh").values()
	# 	allpathdata += self.replacePathMapsbyPattern(
	# 		comp, all_alembic, r'Filename = Input { Value = "(.*?)", },', "Filename"
	# 		)
		
	# 	all_fbx  = comp.GetToolList(False, "SurfaceFBXMesh").values()
	# 	allpathdata += self.replacePathMapsbyPattern(
	# 		comp, all_fbx, r'ImportFile = Input { Value = "(.*?)", },', "ImportFile"
	# 		)
		
	# 	all_OCIO_CS = comp.GetToolList(False, "OCIOColorSpace").values()
	# 	allpathdata += self.replacePathMapsbyPattern(
	# 		comp, all_OCIO_CS, r'OCIOConfig\s*=\s*Input\s*{\s*Value\s*=\s*"([^"]+)"', "OCIOConfig"
	# 		)
		
	# 	all_OCIO_FT = comp.GetToolList(False, "OCIOFileTransform").values()
	# 	all_FileLUT = comp.GetToolList(False, "FileLUT").values()
	# 	luttools = list(all_OCIO_FT) + list(all_FileLUT)
	# 	allpathdata += self.replacePathMapsbyPattern(
	# 		comp, luttools, r'LUTFile = Input { Value = "(.*?)"', "LUTFile"
	# 		)
		
	# 	for pathdata in allpathdata:
	# 		if not pathdata["valid"]:
	# 			print("path: ", pathdata["path"], " in ", pathdata["node"], "does not exists")
	# 		if not pathdata["net"]:
	# 			print("path: ", pathdata["path"], " in ", pathdata["node"], "Is not a NET Path")
	# 		print("path: ", pathdata["path"], " in ", pathdata["node"], "was processed")


	#	Configures name to conform with Fusion Restrictions
	@err_catcher(name=__name__)
	def getFusLegalName(self, origName, check=False):					#	TODO  Restructure and logging
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
			logger.debug(f"Name is Fusion-legal: {newName}")
			return True, ""
				
		return newName


	#	Gets individual State data from the comp state data based on the UUID
	@err_catcher(name=__name__)
	def getMatchingStateDataFromUID(self, nodeUID):
		stateDataRaw = json.loads(self.sm_readStates(self))

		# Iterate through the states to find the matching state dictionary
		stateDetails = None
		for stateData in stateDataRaw["states"]:
			if stateData.get("nodeUID") == nodeUID:
				stateDetails = stateData
				logger.debug(f"State data found for: {self.getNodeNameByUID(nodeUID)}")
				return stateDetails

		logging.warning(f"ERROR: No state details for:  {nodeUID}")
		return None


	# #	Gets individual State data from the comp state data based on the Saver name
	# @err_catcher(name=__name__)
	# def getMatchingStateDataFromName(self, nodeUID):										#	TODO NOT USED
	# 	stateDataRaw = json.loads(self.sm_readStates(self))

	# 	# Iterate through the states to find the matching state dictionary
	# 	stateDetails = None
	# 	for stateData in stateDataRaw["states"]:
	# 		if stateData.get("rendernode") == nodeUID:
	# 			stateDetails = stateData
	# 			return stateDetails

	# 	logging.warning(f"No state details for:  {nodeUID}")


	@err_catcher(name=__name__)
	def isUsingMasterVersion(self):
		useMaster = self.core.mediaProducts.getUseMaster()
		if not useMaster:
			return False

		try:
			masterAction = self.cb_master.currentText()
			if masterAction == "Don't Update Master":
				return False
		except:
			logger.debug("ERROR: Unable to retrieve Master selection from UI")

		return True


	#	Executes local master update if required
	@err_catcher(name=__name__)
	def handleMasterVersion(self, outputName, masterAction=None):
		if not self.isUsingMasterVersion():
			return

		if not masterAction:
			masterAction = self.cb_master.currentText()

		if masterAction in ["Set as master", "Force Set as Master"]:
			try:
				self.core.mediaProducts.updateMasterVersion(outputName, mediaType="2drenders")
				logger.debug(f"Updated Master for: {outputName}")
			except Exception as e:
				logger.warning(f"ERROR: Unable to Set as Master:\n{e}")

		elif masterAction in ["Add to master", "Force Add to Master"]:
			try:
				self.core.mediaProducts.addToMasterVersion(outputName, mediaType="2drenders")
				logger.debug(f"Updated Master for: {outputName}")
			except Exception as e:
				logger.warning(f"ERROR: Unable to Add to Master:\n{e}")


	#	Makes dict for later use in updating Master ver
	@err_catcher(name=__name__)
	def saveMasterData(self, rSettings, stateData, outputPath):
		if rSettings["masterOvr"]:
			stateMasterData = [stateData["taskname"], rSettings["handleMaster"], outputPath]
		else:
			stateMasterData = [stateData["taskname"], stateData["masterVersion"], outputPath]

		if stateMasterData[1] in ["Set as master", "Add to master", "Force Set as Master", "Force Add to Master"]:
			self.masterData.append(stateMasterData)


	#	Executes update Master for each state in dict
	@err_catcher(name=__name__)
	def executeGroupMaster(self):
		try:
			for stateData in self.masterData:
				self.handleMasterVersion(stateData[2], stateData[1])
			return True
		except:
			return False


	#	Submits python job to Farm for Master Update
	@err_catcher(name=__name__)
	def submitFarmGroupMaster(self, origin, farmPlugin, result, details):
		#	Gets farm job info
		try:
			jobId = farmPlugin.getJobIdFromSubmitResult(result)
		except:
			logger.warning("ERROR: Unable to Submit Update Master to Farm")
			return False

		for stateData in self.masterData:
			updateMaster = False
			#	Appends job name
			jobName = stateData[0] + "_updateMaster"
			jobOutputFile = stateData[2].replace("\\", "/")
			jobData = origin.stateManager.submittedDlJobData[jobId]

			#	Generates code to be used in python job
			code = """
import sys

root = \"%s\"
sys.path.append(root + "/Scripts")

import PrismCore
pcore = PrismCore.create(prismArgs=["noUI", "loadProject"])
path = r\"%s\"
""" % (self.core.prismRoot, os.path.expandvars(jobOutputFile))

			#	Uses core methods for update mastr
			if stateData[1] in ["Set as master", "Force Set as Master"]:
				updateMaster = True
				code += "pcore.mediaProducts.updateMasterVersion(path, mediaType='2drenders')"

			#	Uses core methods for update mastr
			elif stateData[1] in ["Add to master", "Force Add to Master"]:
				updateMaster = True
				code += "pcore.mediaProducts.addToMasterVersion(path, mediaType='2drenders')"

			if jobId:
				masterDep = [jobId]
			else:
				masterDep = None

			prio = os.getenv("PRISM_DEADLINE_MASTER_UPDATE_PRIO")
			if prio:
				prio = int(prio)
			else:
				prio = 80

			#	Submits python job is applicable
			if updateMaster:
				try:
					farmPlugin.submitPythonJob(
						code=code,
						jobName=jobName,
						jobPrio=prio,
						jobPool=jobData["jobInfos"]["Pool"],
						jobSndPool=jobData["jobInfos"]["SecondaryPool"],
						jobGroup=jobData["jobInfos"]["Group"],
						jobTimeOut=jobData["jobInfos"]["TaskTimeoutMinutes"],
						jobMachineLimit=jobData["jobInfos"]["MachineLimit"],
						jobComment="Prism-Update_Master",
						jobBatchName=jobData["jobInfos"].get("BatchName"),
						frames="1",
						suspended=jobData["jobInfos"].get("InitialStatus") == "Suspended",
						jobDependencies=masterDep,
						state=origin,
						)
					
					logger.debug(f"Created Farm Master Update job for: {jobName}")
					
				except Exception as e:
					logger.warning(f"ERROR: Unable to Submit Update Master to Farm:\n{e}")
					return False
				
		return True
	

	#	Makes dict for later use in updating Master ver
	@err_catcher(name=__name__)
	def saveVersionList(self, outputPath, stateData):
		sData = outputPath, stateData
		self.versionData.append(sData)


	#	Executes versioninfo creation for each state in dict
	@err_catcher(name=__name__)
	def executeGroupVersioninfo(self):
		for state in self.versionData:
			try:
				filepath = state[0]
				stateData = state[1]

				self.core.saveVersionInfo(filepath, details=stateData)
				logger.debug(f"Created VersionInfo for: {filepath}")

			except:
				logger.warning(f"ERROR: Unable to generate VersionInfo file for: {filepath}")
				return False
			
		return True


	#	Saves original comp settings
	@err_catcher(name=__name__)
	def saveOrigCompSettings(self, comp):
		try:
			cData = {}
			cData["orig_frameRange"] = self.getFrameRange(self)
			cData["orig_currentFrame"] = comp.CurrentTime
			cData["orig_rezX"], cData["orig_rezY"] = self.getResolution()
			cData["orig_HQ"] = comp.GetAttrs()["COMPB_HiQ"]
			cData["orig_MB"] = comp.GetAttrs()["COMPB_MotionBlur"]
			cData["orig_Proxy"] = comp.GetAttrs()["COMPB_Proxy"]

			return cData
		
		except Exception as e:
			logger.warning(f"ERROR: Unable to save original Comp settings:\n{e}")
			return None
	

	#	Resets original comp settings
	@err_catcher(name=__name__)
	def loadOrigCompSettings(self, comp, cData):
		try:
			origFrameStart, origFrameEnd = cData["orig_frameRange"]
			self.setFrameRange(self, origFrameStart, origFrameEnd)
			comp.CurrentTime = cData["orig_currentFrame"]
			self.setResolution(cData["orig_rezX"], cData["orig_rezY"])
			comp.SetAttrs({"COMPB_HiQ": cData["orig_HQ"]})
			comp.SetAttrs({"COMPB_MotionBlur": cData["orig_MB"]})
			comp.SetAttrs({"COMPB_Proxy": cData["orig_Proxy"]})
		
		except Exception as e:
			logger.warning(f"ERROR: Unable to set original settings to Comp:\n{e}")


	#	Changes comp settings based on RenderGroup overrides if applicable
	@err_catcher(name=__name__)
	def setCompOverrides(self, comp, rSettings):
		if "frameOvr" in rSettings and rSettings["frameOvr"]:
			self.setFrameRange(self, rSettings["frame_start"], rSettings["frame_end"])

		#	Temp adjust comp rez if scale override is above 100%
		scaleOvrType, scaleOvrCode = self.getScaleOverride(rSettings)
		if scaleOvrType == "scale":
			orig_rezX, orig_rezY = self.getResolution()
			renderRezX = orig_rezX * scaleOvrCode
			renderRezY = orig_rezY * scaleOvrCode
			self.setResolution(renderRezX, renderRezY)


	#	Adds a Scale node if the Scale override is used by the RenderGroup
	@err_catcher(name=__name__)
	def addScaleNode(self, comp, sv, scaleOvrCode):
		try:
			if sv:
				#	Add a Scale tool
				scaleTool = comp.AddTool("Scale")
				#	Add tool to temp list for later deletion
				self.tempScaleTools.append(scaleTool)
				scaleTool.SetInput("XSize", scaleOvrCode)

				# Get the output of the Scale tool
				scaleOutput = scaleTool.FindMainOutput(1)

				# Rewire the connections
				prev_input = sv.FindMainInput(1).GetConnectedOutput()  # Get the input connected to Saver

				if prev_input:
					scaleTool.FindMainInput(1).ConnectTo(prev_input)  # Connect the previous input to Scale
					sv.FindMainInput(1).ConnectTo(scaleOutput)  # Connect Scale to this specific Saver
				else:
					logger.debug(f"No input found connected to {sv.Name}.")
		
		except Exception as e:
			logger.warning(f"ERROR: Could not add Scale node: {e}")


	#	Deletes the temp Scale nodes
	@err_catcher(name=__name__)
	def deleteTempScaleTools(self):
		for tool in self.tempScaleTools:
			try:
				tool.Delete()
			except:
				logger.warning(f"ERROR: Unable to delete temporary Scale tool {tool}")


	#	Configures all the settings and paths for each state of the RenderGroup
	@err_catcher(name=__name__)
	def configureRenderComp(self, origin, comp, rSettings):
		self.origSaverList = {}
		self.masterData = []
		self.versionData = []
		self.tempScaleTools = []

		context = rSettings["context"]
		
		#	Capture orignal Comp settings for restore after render
		self.origCompSettings = self.saveOrigCompSettings(comp)

		#	Get ImageRender states to be rendered with the group
		renderStates = rSettings["groupRenderStates"]

		#   Save pass-through state of all savers
		self.origSaverList = self.origSaverStates("save", comp, self.origSaverList)

		#	Configure Comp with overrides from RenderGroup
		self.setCompOverrides(comp, rSettings)

		for nodeUID in renderStates:
			#	Get State data from Comp
			stateData = self.getMatchingStateDataFromUID(nodeUID)

			#	Exits if unable to get state data
			if not stateData:
				nodeName = self.getNodeNameByUID(nodeUID)
				logger.warning(f"ERROR: Unable to configure RenderComp for {nodeName}")

			sv = self.getNodeByUID(nodeUID)
			self.setPassThrough(nodeUID=nodeUID, passThrough=False)

			#	Add Scale tool if scale override is above 100%
			scaleOvrType, scaleOvrCode = self.getScaleOverride(rSettings)
			if scaleOvrType == "scale":
				self.addScaleNode(comp, sv, scaleOvrCode)


			#	Set frame padding format for Fusion
			extension = stateData["outputFormat"]
			#	Gets list of ext types that are still image formats
			imageExts = [formatDict["extension"] for formatDict in self.outputFormats if formatDict["type"] == "image"]
			if extension in imageExts:
				#	Adds project padding to the name if it is a image sequence
				framePadding = "0" * self.core.framePadding
			else:
				#	Adds empty string if a movie format
				framePadding = ""

			context["frame"] = framePadding

			#	If Render as Previous Version enabled
			if rSettings["renderAsPrevVer"]:
				try:
					#	Get project basepath from core
					basePath = self.core.paths.getRenderProductBasePaths()[stateData["curoutputpath"]]

					#	 Add info to context
					stateData["mediaType"] = "2drenders"
					stateData["project_path"] = basePath
					stateData["identifier"] = stateData["taskname"]
					context["mediaType"] = "2drenders"
					#	Get highest existing render version to use for render
					self.useVersion = self.core.mediaProducts.getHighestMediaVersion(context, getExisting=True)
				except:
					self.useVersion = None

			#	If Render as Previous Version not enabled
			else:
				self.useVersion = None

			#	 Handle Location override
			if rSettings["locationOvr"]:
				renderLoc = rSettings["render_Loc"]
			else:
				renderLoc = stateData["curoutputpath"]

			try:
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
				
			except Exception as e:
				logger.warning(f"ERROR: Unable to get output filepath:\n{e}")
				return

			#	Get version filepath for Saver
			self.outputPath = outputPathData["path"]
			#	Configure Saver with new filepath
			self.configureRenderNode(nodeUID, self.outputPath, fuseName=None)

			stateData["comment"] = self.monkeypatchedsm.publishComment
			renderDir = os.path.dirname(self.outputPath)
			self.saveVersionList(renderDir, stateData)

			#	Setup master version execution
			self.saveMasterData(rSettings, stateData, self.outputPath)

		logger.debug(f"Configured Render settings for comp: {comp.GetAttrs()['COMPS_Name']}")


	@err_catcher(name=__name__)
	def getHiQualOverride(self, rSettings):
		if "hiQualOvr" in rSettings and rSettings["hiQualOvr"]:
			tempHQ = rSettings["render_HQ"]
			if tempHQ == "Force HiQ":
				hiQCmd = True
			if tempHQ == "Force LowQ":
				hiQCmd = False
		else:
			hiQCmd = None

		return hiQCmd
	
	
	@err_catcher(name=__name__)
	def getBlurOverride(self, rSettings):
		if "blurOvr" in rSettings and rSettings["blurOvr"]:
			tempBlur = rSettings["render_Blur"]
			if tempBlur == "Force Use MB":
				blurCmd = True
			if tempBlur == "Force No MB":
				blurCmd = False
		else:
			blurCmd = None

		return blurCmd
	
	
	#	Returns scale type and scale code if scale override
	@err_catcher(name=__name__)
	def getScaleOverride(self, rSettings):
		if not rSettings["scalingOvr"]:
			return None, None
		
		if rSettings["render_Scale"] in ["Force Proxies Off",
									   		"1/2 (proxy)",
											"1/3 (proxy)",
											"1/4 (proxy)"
											]:
	
			match rSettings["render_Scale"]:
				case "Force Proxies Off":
					scaleCmd = 1
				case "1/2 (proxy)":
					scaleCmd = 2
				case "1/3 (proxy)":
					scaleCmd = 3
				case "1/4 (proxy)":
					scaleCmd = 4

			return "proxy", scaleCmd
		
		elif rSettings["render_Scale"] in ["125 (scale)",
									 		"150 (scale)",
											"200 (scale)"
											]:
			
			match rSettings["render_Scale"]:
				case "125 (scale)":
					scale = 1.25
				case "150 (scale)":
					scale = 1.5
				case "200 (scale)":
					scale = 2

			return "scale", scale
		
		else:
			return None, None
		

	#	Generates render args dict from overrides
	@err_catcher(name=__name__)
	def makeRenderCmd(self, comp, rSettings, group=False):
		try:
			#	Gets appropriate framerange render command
			renderCmd = self.getFrameRangeRenderCmd(comp, rSettings, group)

			#	Uses Fusion proxy command for rez's less than 100%
			scaleOvrType, scaleOvrCode = self.getScaleOverride(rSettings)
			if scaleOvrType == "proxy":
				renderCmd['SizeType'] = scaleOvrCode

			#	Sets global comp HiQual setting
			hiQualOvr = self.getHiQualOverride(rSettings)
			if hiQualOvr is not None:
				renderCmd['HiQ'] = hiQualOvr

			#	Sets global comp MotionBlur setting
			blurOvr = self.getBlurOverride(rSettings)
			if blurOvr is not None:
				renderCmd['MotionBlur'] = blurOvr

			logger.debug(f"Generated Render command: {renderCmd}")
			return renderCmd
		
		except:
			return ""
	

	#	Renders individual State Saver locally
	@err_catcher(name=__name__)
	def sm_render_startLocalRender(self, origin, outputPathOnly, outputName, rSettings):
		comp = self.getCurrentComp()	
		if self.sm_checkCorrectComp(comp):
			self.tempScaleTools = []
			origCompSettings = self.saveOrigCompSettings(comp)

			sv = self.getNodeByUID(rSettings["nodeUID"])
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
				#	Add Scale tool if scale override is above 100%
				scaleOvrType, scaleOvrCode = self.getScaleOverride(rSettings)
				if scaleOvrType == "scale":
					self.addScaleNode(comp, sv, scaleOvrCode)

				#	Gets render args from override settings
				renderCmd = self.makeRenderCmd(comp, rSettings)

				#	Renders with override args
				comp.Render({**renderCmd, 'Tool': sv, "Wait": True})

				#	Remove any temp Scale nodes
				self.deleteTempScaleTools()

				#	Reset Comp settings to Original
				self.loadOrigCompSettings(comp, origCompSettings)

				if len(os.listdir(os.path.dirname(outputName))) > 0:
					return "Result=Success"
				else:
					return "unknown error (files do not exist)"
				

	#	Executes a GroupRender on the local machine that allows multiple Savers to render simultaneously
	@err_catcher(name=__name__)
	def sm_render_startLocalGroupRender(self, origin, rSettings):
		comp = self.getCurrentComp()

		#	Return if the Comps do not match
		if not self.sm_checkCorrectComp(comp):
			return False

		try:
			comp.Lock()

			#	Setup comp settings and filepaths for render
			self.configureRenderComp(origin, comp, rSettings)

			#	Gets render args from override settings
			renderCmd = self.makeRenderCmd(comp, rSettings, group=True)

			#	Renders with override args
			comp.Render({**renderCmd, "Wait": True})

			#	Remove any temp Scale nodes
			self.deleteTempScaleTools()

			#	Reset Comp settings to Original
			self.loadOrigCompSettings(comp, self.origCompSettings)

			#	Reconfigure pass-through of Savers
			self.origSaverStates("load", comp, self.origSaverList)

			renderResult = True

		except:
			renderResult = False
		finally:
			comp.Unlock()

		#	Create versionInfo file for each state
		versionResult = self.executeGroupVersioninfo()

		#	Execute master version if applicable
		masterResult = self.executeGroupMaster()

		#	Returns result string back to Core for UI
		#	Cannot figure out why there is a 'False' in the return string, but it is needed.
		if renderResult and versionResult and masterResult:
			logger.debug("Success: rendered Local GroupRender.")
			return "Result=Success"
		else:
			if not renderResult:
				logger.warning("Error (Local Group Render failed)")
				return "Error (Local Group Render failed)", False
			if not versionResult:
				logger.warning("Error (Failed to create versionInfo)")
				return "Error (Failed to create versionInfo)", False
			if not masterResult:
				logger.warning("Error (Failed to update Master)")
				return "Error (Failed to update Master)", False


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
	

	#	Edit various details for farm submission
	@err_catcher(name=__name__)
	def setupFarmDetails(self, origin, rSettings):
		context = rSettings["context"]
		details = context.copy()
		
		if "filename" in details:
			del details["filename"]
		if "extension" in details:
			del details["extension"]

		details["version"] = self.createUUID(simple=True)
		details["sourceScene"] = self.tempFilePath
		details["identifier"] = rSettings["groupName"]
		details["comment"] = self.monkeypatchedsm.publishComment

		self.className = "RenderGroup"

		return details


	#	Submits the temp comp file to the Farm plugin for rendering
	@err_catcher(name=__name__)
	def sm_render_startFarmGroupRender(self, origin, farmPlugin, rSettings):
		comp = self.getCurrentComp()

		#	Makes global for later use in versioninfo creation and master update
		self.rSettings = rSettings

		#	Return if the Comps do not match
		if not self.sm_checkCorrectComp(comp):
			return False
		
		try:
			comp.Lock()

			#	Setup comp settings and filepaths for render
			self.configureRenderComp(origin, comp, rSettings)

			#	Gets current filename
			currFile = self.core.getCurrentFileName()
			#	Gets temp filename
			self.tempFilePath, tempDir = self.getFarmTempFilepath(currFile)
			
			#	Saves to temp comp
			try:
				saveTempResult = comp.Save(self.tempFilePath)
				if saveTempResult:
					logger.debug(f"Saved temp Comp for Farm submission to:\n{self.tempFilePath}")
				else:
					raise Exception
			except:
				logger.warning(f"ERROR: Failed to save temp Comp for Farm submission:\n{self.tempFilePath}")
				comp.Unlock()
				return

			farmDetails = self.setupFarmDetails(origin, rSettings)

			#	Checks if there are states that use update Master
			if len(self.masterData) > 0:
				executeMaster = True
			else:
				executeMaster = False

			#	Submits to farm plugin
			submitResult = farmPlugin.sm_render_submitJob(
				origin,
				self.outputPath,
				None,
				handleMaster=False,
				details=farmDetails,
				useBatch=executeMaster,
				sceneDescription=False
				)
		except:
			submitResult = False
		
		#	Deletes temp comp file
		try:
			shutil.rmtree(tempDir)
		except:
			logger.warning(f"Unable to remove temp directory:  {tempDir}")

		#	Remove any temp Scale nodes
		self.deleteTempScaleTools()

		#	Reset Comp settings to Original
		self.loadOrigCompSettings(comp, self.origCompSettings)

		#	Reconfigure pass-through of Savers
		self.origSaverStates("load", comp, self.origSaverList)

		#	Save the original settings to original file
		comp.Save(currFile)

		comp.Unlock()

		#	Create versionInfo file for each state
		versionResult = self.executeGroupVersioninfo()

		#	Executes Farm update Master if applicable
		if submitResult and executeMaster:
			masterResult = self.submitFarmGroupMaster(origin, farmPlugin, submitResult, farmDetails)

		#	Returns result string back to Core for UI
		#	Cannot figure out why there is a 'False' in the return string, but it is needed.
		if executeMaster:
			if submitResult and versionResult and masterResult:
				logger.debug("Farm submission sucessful")
				return "Result=Success"
			else:
				if not submitResult:
					logger.warning("Error (Failed to submitGroup Render to Farm)")
					return "error (Failed to submitGroup Render to Farm)", False
				if not versionResult:
					logger.warning("Error (Failed to create versionInfo Farm job)")
					return "error (Failed to create versionInfo Farm job)", False
				if not masterResult:
					logger.warning("Error (Failed to update Master Farm job)")
					return "error (Failed to update Master Farm job)", False
		else:
			if submitResult and versionResult:
				logger.debug("Farm submission sucessful")
				return "Result=Success"
			else:
				if not submitResult:
					logger.warning("Error (Failed to submitGroup Render to Farm)")
					return "error (Failed to submitGroup Render to Farm)", False
				if not versionResult:
					logger.warning("Error (Failed to create versionInfo Farm job)")
					return "error (Failed to create versionInfo Farm job)", False



	#	NOT USED HERE
	@err_catcher(name=__name__)
	def sm_render_undoRenderSettings(self, origin, rSettings):
		pass


	#	Sets Deadline args that are called from Deadline plugin
	@err_catcher(name=__name__)
	def sm_render_getDeadlineParams(self, origin, dlParams, homeDir):
		#	Sets Deadling jobinfo arg file location
		dlParams["jobInfoFile"] = os.path.join(homeDir, "temp", "fusion_submit_info.job")

		dlParams["jobInfos"]["Plugin"] = "Fusion"

		#	Uses StateManager comment for Deadline comment
		try:
			dlParams["jobInfos"]["Comment"] = self.monkeypatchedsm.publishComment
		except:
			dlParams["jobInfos"]["Comment"] = "Prism-Submission-Fusion_ImageRender"

		#	Sets Deadling plugininfo arg file location
		dlParams["pluginInfoFile"] = os.path.join(homeDir, "temp", "fusion_plugin_info.job")

		dlParams["pluginInfos"]["Version"] = str(math.floor(self.getAppVersion(origin)))
		dlParams["pluginInfos"]["OutputFile"] = dlParams["jobInfos"]["OutputFilename0"]

		#	Uses Fusion proxy command for rez's less than 100%
		scaleOvrType, scaleOvrCode = self.getScaleOverride(self.rSettings)
		if scaleOvrType == "proxy":
			dlParams["pluginInfos"]["Proxy"] = scaleOvrCode

		hiQualOvr = self.getHiQualOverride(self.rSettings)
		if hiQualOvr is not None:
			dlParams["pluginInfos"]["HighQuality"] = hiQualOvr

		blurOvr = self.getBlurOverride(self.rSettings)
		if blurOvr is not None:
			dlParams["pluginInfos"]["MotionBlur"] = blurOvr


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
		comp = self.getCurrentComp()
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
		if self.getNodeType(node) == 'Loader':
			try:
				node = node
				loaderPath = filePath
				loaderName = self.getNodeNameByTool(node)

				# Rename the clipname to force reload duration
				node.Clip[self.fusion.TIME_UNDEFINED] = loaderPath

				# If first frame is None, it is probably not a sequence.
				if firstframe:
					node.GlobalOut[0] = lastframe
					node.GlobalIn[0] = firstframe

					# Trim
					node.ClipTimeStart = 0
					node.ClipTimeEnd = lastframe - firstframe
					node.HoldLastFrame = 0

				# Clips Reload
				self.setPassThrough(node=node, passThrough=True)
				self.setPassThrough(node=node, passThrough=False)

				logger.debug(f"Reloaded Loader: {filePath}")

			except:
				logger.warning(f"ERROR: Failed to reload Loader: {filePath}")


	@err_catcher(name=__name__)
	def importImages(self, mediaBrowser):
		#
		try:
			self.monkeypatchedmediabrowser = mediaBrowser
			self.core.plugins.monkeyPatch(mediaBrowser.compGetImportSource, self.compGetImportSource, self, force=True)
			self.core.plugins.monkeyPatch(mediaBrowser.compGetImportPasses, self.compGetImportPasses, self, force=True)
			logger.debug("Patched functions in 'importImages()'")

		except Exception as e:
			logger.warning(f"ERROR: Unable to load patched functions:\n{e}")

		comp = self.getCurrentComp()
		
		# Check if file is Linked
		contexts = mediaBrowser.getCurRenders()
		data = contexts[0]
		path = data["path"]
		isfile = os.path.isfile(os.path.join(path, "REDIRECT.txt"))
		if isfile:
			logger.debug("Importing of Linked Media is not supported")
			self.core.popup("Linked media is not supported at the momment.\nTry dragging the file directly from the project browser.")
			return
		
		# Setup Dialog
		fString = "Please select an import option:"
		try:
			checked = comp.GetData("isPrismImportChbxCheck")
		except:
			pass

		if not checked:
			checked = False		

		try:
			currentAOV = mediaBrowser.origin.getCurrentAOV()
		except:
			logger.warning("ERROR: Unable to get the current AOV name.")

		dataSources = None
		if currentAOV:
			dataSources = mediaBrowser.compGetImportPasses()
		
		# Check if media padding corresponds to the project:
		source = data["source"]
		if "#" in source:
			if not self.check_numpadding_matching(source):
				self.core.popup("The padding of the file you are trying to import\ndoes not seem to match the project padding.\nCheck the project preferences.")
				return

		if currentAOV and len(dataSources) > 1:
			buttons = ["Current AOV", "All AOVs", "Update Selected", "Cancel"]
			result, checkbox_checked = self.popupQuestion(fString, buttons=buttons, icon=QMessageBox.NoIcon, checked=checked)
		else:
			buttons = ["Import Media", "Update Selected", "Cancel"]
			result, checkbox_checked = self.popupQuestion(fString, buttons=buttons, icon=QMessageBox.NoIcon, checked=checked)

		comp.SetData("isPrismImportChbxCheck", checkbox_checked)

		if result == "Current AOV" or result == "Import Media":
			self.fusionImportSource(mediaBrowser, sortnodes=not checkbox_checked)

		elif result == "All AOVs":
			self.fusionImportPasses(mediaBrowser, dataSources, sortnodes=not checkbox_checked)

		elif result == "Update Selected":
			self.fusionUpdateSelectedPasses(mediaBrowser, sortnodes=not checkbox_checked)
		else:
			return

	@err_catcher(name=__name__)
	def check_numpadding_matching(self, filename):
		try:
			projectframepadding = self.core.framePadding
			# Regular expression to match the `.` followed by hashes `#` and ending in another `.` before extension
			pattern = r"\.(#+)\."

			# Search for the pattern in the filename
			match = re.search(pattern, filename)
			
			if match:
				# Count the number of `#` characters in the matched group
				padding_length = len(match.group(1))
				return padding_length == projectframepadding
			else:
				return False
		except:
			logger.warning(f"ERROR: Unable to check frame padding for {filename}")
			return False
		
		
	@err_catcher(name=__name__)
	def fusionImportSource(self, mediaBrowser, sortnodes=True):
		comp = self.getCurrentComp()
		flow = comp.CurrentFrame.FlowView

		# refNode = comp.ActiveTool # None if no active tool
		leftmostNode = self.find_leftmost_lower_node(0.5)

		# deselect all nodes
		flow.Select()

		try:
			sourceData = mediaBrowser.compGetImportSource()
		except:
			logger.warning("ERROR: Unable to get sourceData from the MediaBrowser")
			return

		imageData = self.getImageData(sourceData)
		if imageData:
			updatehandle:list = [] # Required to return data on the updated nodes.
			if sortnodes:
				try:
					node = self.processImageImport(
									imageData,
									updatehandle=updatehandle,
									refNode=leftmostNode,
									createwireless=sortnodes
									)
				except:
					logger.warning("ERROR: Unable to process import images")
			
				if not leftmostNode:
					leftmostNode = node
				self.sort_loaders(leftmostNode, reconnectIn=True, sortnodes=sortnodes)
					
			else:
				try:
					node = self.processImageImport(
									imageData,
									updatehandle=updatehandle,
									refNode=None,
									createwireless=sortnodes
									)
				except:
					logger.warning("ERROR: Unable to process import images")

			# deselect all nodes
			flow.Select()
			self.getUpdatedNodesFeedback(updatehandle)

			logger.debug(f"Imported image: {imageData['filePath']}")


	@err_catcher(name=__name__)
	def fusionImportPasses(self, mediaBrowser, dataSources, sortnodes=True):
		comp = self.getCurrentComp()
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

		# dataSources = mediaBrowser.compGetImportPasses()
		for sourceData in dataSources:
			try:
				imageData = self.getPassData(sourceData)
			except:
				logger.warning("ERROR: Unable to import passes - failed to get pass data")
				return
			
			# Return the last processed node.
			try:
				leftmostNode = self.processImageImport(
									imageData,
									splithandle=splithandle,
									updatehandle=updatehandle,
									refNode=leftmostNode,
									createwireless=sortnodes
									)
			except:
				logger.warning("ERROR: Unable to import passes")
				return
			
		self.sort_loaders(leftmostNode, reconnectIn=True, sortnodes=sortnodes)

		# deselect all nodes
		flow.Select()
		self.getUpdatedNodesFeedback(updatehandle)

		currIdentifier = self.core.pb.mediaBrowser.getCurrentIdentifier()
		logger.debug(f"Imported passes for: {currIdentifier['displayName']}")


	@err_catcher(name=__name__)
	def getUpdatedNodesFeedback(self, updatehandle):
		comp = self.getCurrentComp()
		flow = comp.CurrentFrame.FlowView

		if len(updatehandle) > 0:
			try:
				message = "The following nodes were updated:\n\n"
				for handle in updatehandle:
					if ".#nochange#." in handle:
						message += handle.split(":")[0] + ": Version didn't change\n" 
					else:
						message += f"{handle}\n"
					flow.Select(comp.FindTool(handle.split(":")[0]), True)

				# Display List of updated nodes.
				logger.debug("Showing version update popup")
				self.createInformationDialog("Updated Nodes", message)

			except:
				logger.warning("ERROR: Unable to display version update feedback")


	@err_catcher(name=__name__)
	def createInformationDialog(self, title, message):
		msg = QMessageBox(QMessageBox.Question, title, message)
		msg.addButton("Ok", QMessageBox.YesRole)
		msg.setParent(self.core.messageParent, Qt.Window)
		msg.exec_()


	@err_catcher(name=__name__)
	def split_loader_name(self, name):
		try:
			prefix = name.rsplit('_', 1)[0]  # everything to the left of the last "_"
			suffix = name.rsplit('_', 1)[-1]  # everything to the right of the last "_"
			return prefix, suffix
		except:
			logger.warning(f"ERROR: Unable to split loader name {name}")


	@err_catcher(name=__name__)
	def sort_loaders(self, posRefNode, reconnectIn=True, sortnodes=True):
		comp = self.getCurrentComp()
		flow = comp.CurrentFrame.FlowView

		comp.Lock()

		#Get the leftmost loader within a threshold.
		leftmostpos = flow.GetPosTable(posRefNode)[1]
		bottommostpos = flow.GetPosTable(posRefNode)[2]
		thresh = 100

		# We get only the loaders within a threshold from the leftmost and who were created by prism.
		try:
			loaders = [l for l in comp.GetToolList(False, "Loader").values() if abs(flow.GetPosTable(l)[1] - leftmostpos)<=thresh and l.GetData("isprismnode")]
			loaderstop2bot = sorted(loaders, key=lambda ld: flow.GetPosTable(ld)[2])
			layers = set([self.split_loader_name(ly.Name)[0] for ly in loaders])
		except:
			logger.warning("ERROR: Cannot sort loaders - unable to resolve threshold in the flow")
			return

		sortedloaders = []
		for ly in sorted(list(layers)):
			lyloaders = [l for l in loaders if self.split_loader_name(l.Name)[0] == ly]
			sorted_loader_names = sorted(lyloaders, key=lambda ld: ld.Name.lower())
			sortedloaders += sorted_loader_names
		# if refNode is not part of nodes to sort we move the nodes down so they don't overlap it.
		refInNodes = any(ldr.Name == posRefNode.Name for ldr in sortedloaders)

		# Sorting the loader names
		if len(sortedloaders) > 0:
			lastloaderlyr = self.split_loader_name(sortedloaders[0].Name)[0]
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
						lyrnm = self.split_loader_name(l.Name)[0]
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

		comp.Unlock()


	@err_catcher(name=__name__)
	def fusionUpdateSelectedPasses(self, mediaBrowser, sortnodes=True):
		comp = self.getCurrentComp()
		flow = comp.CurrentFrame.FlowView
	
		# from selection grab only loaders
		loaders = comp.GetToolList(True, "Loader").values()
		origloaders = loaders
		
		if not loaders:
			logger.warning("ERROR: Could not find any Loaders in the comp")
			return

		try:
			dataSources = mediaBrowser.compGetImportPasses()
			if len(dataSources) == 0:
				dataSources = mediaBrowser.compGetImportSource()
		except:
			logger.warning("ERROR: Unable to get data sources from the MediaBrowser")
			return

		updatehandle = []
		for sourceData in dataSources:
			imageData = self.getPassData(sourceData)
			updatedloader, prevVersion =  self.updateLoaders(
													loaders,
													imageData['filePath'],
													imageData['firstFrame'],
													imageData['lastFrame'],
													imageData['isSequence']
													)

			if updatedloader:
				try:
					# Set up update feedback Dialog message
					version1 = prevVersion
					version2 = self.extract_version(updatedloader.GetAttrs('TOOLST_Clip_Name')[1])
					nodemessage = f"{updatedloader.Name}: v {str(version1)} -> v {str(version2)}"
					updatehandle.append(nodemessage)
				except:
					logger.warning("ERROR: Unable to update passes - cannot compare versions")
					return

				# if multilayerEXR
				if updatedloader.GetData("prismmultchanlayer"):
					try:
						loader_channels = self.get_loader_channels(updatedloader)
						layernames = list(set(self.get_channel_data(loader_channels)))
						flow.Select(updatedloader, False)
						loaders = comp.GetToolList(True, "Loader").values()
					except:
						logger.warning("ERROR: Unable to update passes - cannot resolve exr channels")
						return
					
					for ly in layernames:
						# we try the same data for each channel just to make sure, since the Clip is the same we just have to iterate and remove whatever is found.
						try:
							updatedloader, prevVersion =  self.updateLoaders(
													   loaders,
													   imageData['filePath'],
													   imageData['firstFrame'],
													   imageData['lastFrame'],
													   imageData['isSequence'],
													   exrlayers=layernames
													   )
						except:
							logger.warning("ERROR: Unable to update passes - cannot compare versions")
							return
						
						if updatedloader:
							# Deselect updated one and try again.
							flow.Select(updatedloader,False)
							loaders = comp.GetToolList(True, "Loader").values()
							# Set up update feedback Dialog message
							version1 = prevVersion
							version2 = self.extract_version(updatedloader.GetAttrs('TOOLST_Clip_Name')[1])
							nodemessage = f"{updatedloader.Name}: v {str(version1)} -> v {str(version2)}"
							updatehandle.append(nodemessage)
						else:
							# if we didnt find another one then there is no point in keep looking
							break
					
						logger.debug(f"Updated Loader: {updatedloader.Name}")

					self.getUpdatedNodesFeedback(updatehandle)

		self.getUpdatedNodesFeedback(updatehandle)
		currIdentifier = self.core.pb.mediaBrowser.getCurrentIdentifier()
		logger.debug(f"Updated selected passes for: {currIdentifier['displayName']}")


	@err_catcher(name=__name__)
	def returnImageDataDict(self, filePath, firstFrame, lastFrame, aovNm, layerNm, isSequence):
		return {
		'filePath': filePath, 
		'firstFrame': firstFrame, 
		'lastFrame': lastFrame, 
		'aovNm': aovNm,
		'layerNm': layerNm,
		'isSequence': isSequence
		}


	@err_catcher(name=__name__)
	def getImageData(self, sourceData):
		curfr = self.get_current_frame()
		framepadding = self.core.framePadding
		padding_string = self.get_frame_padding_string()

		try:
			# Check if source data interprets the image sequence as individual images.
			image_strings = [item[0] for item in sourceData if isinstance(item[0], str)]

			if len(image_strings) > 1:
				imagepath = self.is_image_sequence(image_strings)

				if imagepath:
					filePath = self.format_file_path(imagepath["file_path"], curfr, framepadding, padding_string)
					firstFrame, lastFrame = imagepath["start_frame"], imagepath["end_frame"]
					aovNm, layerNm = 'PrismLoader', 'PrismMedia'

					logger.debug(f"Retrieved image data for image sequence: {filePath}")
					return self.returnImageDataDict(filePath, firstFrame, lastFrame, aovNm, layerNm, imagepath["is_sequence"])
			else:
				# Handle a single image by calling getPassData directly
				logger.debug(f"Retrieved image data for image: {sourceData[0]}")
				return self.getPassData(sourceData[0])
			
		except:
			logger.warning("ERROR: No image sequence was loaded.")
			QMessageBox.warning(self.core.messageParent, "Prism Integration", "No image sequence was loaded.")
			return None


	@err_catcher(name=__name__)
	def getPassData(self, sourceData):
		firstFrame, lastFrame = sourceData[1], sourceData[2]
		curfr = firstFrame #self.get_current_frame()
		framepadding = self.core.framePadding
		padding_string = self.get_frame_padding_string()

		numframepadsinpath = self.check_padding_in_filepath(sourceData[0])
		isSequence = numframepadsinpath > 0

		try:
			if isSequence:
				filePath = self.format_file_path_with_validation(sourceData[0], curfr, framepadding, padding_string, firstFrame)
			else:
				filePath = sourceData[0]
		except:
			logger.warning("ERROR: Failed to get pass data")
			return

		try:
			aovNm, layerNm = self.extract_aov_layer_names(filePath)
		except:
			logger.warning("ERROR: Failed to extract AOV Layer names")
			return

		logger.debug(f"Retrieved pass data for image: {aovNm}")
		return self.returnImageDataDict(filePath, firstFrame, lastFrame, aovNm, layerNm, isSequence)


	# Helper function to know if a path has padding and the padding length.
	@err_catcher(name=__name__)
	def check_padding_in_filepath(self,filepath):
		try:
			filepath = str(filepath)
			# Get the file extension
			_, file_extension = os.path.splitext(filepath)

			# Regular expression to match consecutive '#' characters before the extension
			pattern = rf"(#+)\{file_extension}$"
			match = re.search(pattern, filepath)

			if match:
				num_hashes = len(match.group(1))
				# File path has {num_hashes} consecutive '#' characters before the extension.
				return num_hashes
			else:
				# No consecutive '#' characters found before the extension.
				return 0
		except:
			logger.warning("ERROR:  Failed to check padding in filepath")
			return None
		

	# Helper function get frame number
	@err_catcher(name=__name__)
	def get_current_frame(self):
		comp = self.getCurrentComp()
		return int(comp.CurrentTime)


	# Helper function get frame padding string
	@err_catcher(name=__name__)
	def get_frame_padding_string(self):
		framepadding = self.core.framePadding
		padding_string = '#' * framepadding + '.'
		return str(padding_string)


	# Helper function to format file path with frame number
	@err_catcher(name=__name__)
	def format_file_path(self, path, frame, framepadding, padding_string):
		"""Format the file path to replace padding_string with the current frame."""
		try:
			return path.replace(padding_string, f"{frame:0{framepadding}}.")
		except:
			logger.warning("ERROR: Failed to format file path string")
			return ""


	# Helper function to handle padding string replacement based on file existence
	@err_catcher(name=__name__)
	def format_file_path_with_validation(self, path, frame, framepadding, padding_string, firstFrame):
		"""Format the file path by validating its existence."""
		try:
			if firstFrame:
				formatted_first_frame = f"{firstFrame:0{framepadding}}."
				modified_file_path = path.replace(padding_string, formatted_first_frame)

				if os.path.exists(modified_file_path):
					return path.replace(padding_string, f"{frame:0{framepadding}}.")
				else:
					return path.replace("." + padding_string, ".")
			else:
				return path
		except:
			logger.warning("ERROR: Failed to format file path with validation")
			return ""


	# Helper function to extract AOV and layer names
	@err_catcher(name=__name__)
	def extract_aov_layer_names(self, filePath):
		"""Extract the AOV and layer names from the file path."""
		try:
			parts = os.path.dirname(filePath).split("/")
			aovnm = parts[-1]
			wronglayerNms = ["2dRender","3dRender"]
			layerNm = parts[-3]
			if layerNm in wronglayerNms:
				layerNm = parts[-2]
			
			return aovnm, layerNm
		
		except:
			logger.warning("ERROR: Failed to extract AOV layer names")
			return None


	@err_catcher(name=__name__)
	def updateLoaders(self, Loaderstocheck, filePath, firstFrame, lastFrame, isSequence=False, exrlayers=[]):
		try:
			for loader in Loaderstocheck:
				loaderClipPath = loader.Clip[0]
				if filePath == loaderClipPath:
					return loader, ".#nochange#."
				
				if len(exrlayers) > 0:
					layer = loader.GetData("prismmultchanlayer")
					if layer: 
						if layer not in exrlayers:
							return loader, ".#nochange#."
				
				if self.are_paths_equal_except_version(loaderClipPath, filePath, isSequence):
					version1 = self.extract_version(loaderClipPath)
					version2 = self.extract_version(filePath)

					self.reloadLoader(loader, filePath, firstFrame, lastFrame)
					if not version1 == version2:
						return loader, version1
				
			return None, ""
		
		except:
			logger.warning("ERROR: Failed to update loaders")
			return None
	

	@err_catcher(name=__name__)
	def processImageImport(self, imageData, splithandle=None, updatehandle:list=[], refNode=None, createwireless=True):
		# Do in this function the actual importing or update of the image.		
		comp = self.getCurrentComp()
		flow = comp.CurrentFrame.FlowView

		filePath = imageData['filePath']
		firstFrame = imageData['firstFrame']
		lastFrame = imageData['lastFrame']
		aovNm = imageData['aovNm']
		layerNm = imageData['layerNm']
		isSequence = imageData['isSequence']
		
		extension = os.path.splitext(filePath)[1]
		# Check if path without version exists in a loader and if so generate a popup to update with new version.
		allLoaders = comp.GetToolList(False, "Loader").values()
		try:
			updatedloader, prevVersion = self.updateLoaders(allLoaders, filePath, firstFrame, lastFrame, isSequence)
		except:
			updatedloader = prevVersion = None

		# If an updated node was produced.
		if updatedloader:
			try:
				# Update Multilayer.
				if extension == ".exr":
					# check for multichannels to update all plitted nodes.
					extraloader = updatedloader
					checkedloaders:list = [updatedloader.Name]
					if len(self.get_loader_channels(updatedloader)) > 0:
						while  extraloader:
							allremainingLoaders = [t for t in allLoaders if not t.Name in checkedloaders]
							extraloader, extraversion = self.updateLoaders(allremainingLoaders, filePath, firstFrame, lastFrame, isSequence)
							if extraloader:
								checkedloaders.append(extraloader.Name)

				# Set up update feedback Dialog message
				version1 = prevVersion
				version2 = self.extract_version(updatedloader.GetAttrs('TOOLST_Clip_Name')[1])
				nodemessage = f"{updatedloader.Name}: v {str(version1)} -> v {str(version2)}"
				updatehandle.append(nodemessage)

				return updatedloader
			except:
				logger.warning("ERROR: Unable to process image import")
				return

		# if paths were not updated then we create new nodes.
		try:
			comp.Lock()
			node = comp.AddTool("Loader")
			# Set a Prism node identifier:
			if createwireless:
				node.SetData("isprismnode", True)
			self.reloadLoader(node, filePath, firstFrame, lastFrame)
			node.SetAttrs({"TOOLS_Name": layerNm + "_" + aovNm})
			if refNode:
				if refNode.GetAttrs('TOOLS_RegID') =='Loader':
					self.setNodePosition(node, x_offset = 0, y_offset = 1, refNode=refNode)
				else:
					self.setNodePosition(node, x_offset = -5, y_offset = 0, refNode=refNode)
			else:
				self.setNodePosition(node, x_offset = 0, y_offset = 0, refNode=None)

			comp.Unlock()

		except:
			logger.warning("ERROR: Failed to create loader node.")
			comp.Unlock()
			return
		
		# IF IS EXR
		if extension == ".exr":
			try:
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
						loaders_list = self.process_multichannel(node, createwireless=createwireless)
						if len(loaders_list)>0:
							return loaders_list[-1]
	
					elif splithandle:
						splithandle['splitchosen'] = False
			except:
				logger.warning("ERROR: Failed to process Multilayer EXR")
				return None

		# create wireless
		if createwireless:
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
		comp = self.getCurrentComp()
		flow = comp.CurrentFrame.FlowView
		# ad = comp.AutoDomain()

		try:
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
				# Set Prism node identifier.
				node.SetData("isprismnode", True)

			ad.ConnectInput('Input', tool)

			logger.debug(f"Created Wireless nodes for: {tool.Name}")

		except Exception as e:
			logger.warning(f"ERROR:  Could not add wireless nodes:\n{e}")


	@err_catcher(name=__name__)
	def find_leftmost_lower_node(self, threshold):
		comp = self.getCurrentComp()
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
	def extract_version(self, filepath):
		# Extract the version information using a regular expression
		padding = self.core.versionPadding
		pattern = rf"v(\d{{{padding}}})"  # Using f-string for dynamic regex pattern
		match = re.search(pattern, filepath)

		if match:
			return int(match.group(1))
		else:
			logger.warning(f"ERROR: Failed to extract version from filepath: {filepath}")
			return None
		

	@err_catcher(name=__name__)
	def are_paths_equal_except_version(self, path1, path2, isSequence):	
		try:
			# Remove the version part from the paths for exact match comparison
			padding = self.core.versionPadding
			version_pattern = rf"v\d{{{padding}}}"
			path1_without_version = re.sub(version_pattern, "", os.path.splitext(path1)[0])
			path2_without_version = re.sub(version_pattern, "", os.path.splitext(path2)[0])
			if isSequence:
				# Use regex to remove numbers before any file extension (can vary in length)
				path1_without_version = re.sub(r'(\d+)(\.\w+)$', r'\2', path1_without_version)
				path2_without_version = re.sub(r'(\d+)(\.\w+)$', r'\2', path2_without_version)
			# Check if the non-version parts are an exact match
			if path1_without_version == path2_without_version:
				# Versions are the same, and non-version parts are an exact match
				return True
			else:
				# Versions are the same, but non-version parts are different
				return False
			
		except:
			logger.warning("ERROR: Failed to compare versions")
			return False

	@err_catcher(name=__name__)
	def get_pattern_prefix(self, file_path):
		try:
			# Extract the file extension
			_, file_extension = os.path.splitext(file_path)
			padding = self.core.versionPadding

			# Regex pattern to capture the prefix and the frame number
			# Example: sq_030-sh_010_Compositing_v001.0001.exr
			regex_pattern = rf'^(.+)v\d{{{padding}}}\.(\d{{{padding}}}){re.escape(file_extension)}$'
			pattern = re.compile(regex_pattern)
			match = pattern.match(file_path)

			# Return the prefix and frame number if matched
			return (match.group(1), int(match.group(2))) if match else (None, None)
		
		except:
			logger.warning("ERROR: Failed to get pattern prefix")
			return None, None
		

	@err_catcher(name=__name__)
	def is_image_sequence(self, strings):
		try:
			# Get the prefix and frame number of the first file
			first_image_prefix, first_frame = self.get_pattern_prefix(strings[0])

			# Check if all files share the same prefix and find their frame numbers
			frame_numbers = []
			for item in strings:
				prefix, frame = self.get_pattern_prefix(item)
				if prefix != first_image_prefix or frame is None:
					return None  # Not an image sequence
				frame_numbers.append(frame)

			# Get the first and last frame numbers
			start_frame = min(frame_numbers)
			end_frame = max(frame_numbers)

			# Return the first file path (assumed as the main reference), and frame range details
			return {
				"file_path": strings[0],
				"start_frame": start_frame,
				"end_frame": end_frame,
				"is_sequence": True
				} if start_frame != end_frame else None
		except:
			logger.warning("ERROR: Failed to get is image sequence")
		

	# EXR CHANNEL MANAGEMENT #

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
		try:
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
		
		except:
			logger.warning("ERROR: Failed to get channel data")
			return None
	

	@err_catcher(name=__name__)
	def GetLoaderClip(self, tool):
		loader_clip = tool.Clip[self.fusion.TIME_UNDEFINED]
		if loader_clip:        
			return loader_clip
		
		logger.warning("EERROR: Loader contains no clips to explore")
	

	@err_catcher(name=__name__)
	def move_loaders(self,org_x_pos, org_y_pos, loaders):
		try:
			comp = self.getCurrentComp()
			flow = comp.CurrentFrame.FlowView
			y_pos_add = 1

			for count, ldr in enumerate(loaders, start=0):
				flow.SetPos(ldr, org_x_pos, org_y_pos + y_pos_add * count)
		except:
			logger.warning("ERROR: Failed to move loaders")


	@err_catcher(name=__name__)
	def process_multichannel(self, tool, createwireless=True):
		try:
			comp = self.getCurrentComp()
			flow = comp.CurrentFrame.FlowView
			loader_channels = self.get_loader_channels(tool)
			channel_data = self.get_channel_data(loader_channels)
			x_pos, y_pos = flow.GetPosTable(tool).values()
		except:
			logger.warning("ERROR: Failed to process multichannel EXR - could not get data")
			return

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

		# Update the loader node channel settings and create loaders
		# prefix is the name of the layer.
		for prefix, channels in channel_data.items():
			try:
				logger.debug(f"Splitting EXR Channel: {prefix}")

				ldr = comp.Loader({'Clip': self.GetLoaderClip(tool)})
				# Add Prism node identifier
				ldr.SetData("isprismnode", True)

				# Replace invalid EXR channel names with placeholders
				ldr.SetAttrs({'TOOLB_NameSet': True, 'TOOLS_Name': tool.Name.rsplit('_', 1)[0] + "_" + prefix})# rsplit splits from the right using in this case the first ocurrence.
				for name, placeholder in invalid_names.items():
					setattr(ldr.Clip1.OpenEXRFormat, name, placeholder)

				# Refresh the OpenEXRFormat setting using real channel name data in a 2nd stage
				for channel_name in channels:
					channel = re.search(r"\.([^.]+)$", channel_name).group(1).lower() # r, g, b, etc...
					
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
						logger.debug(f"Mapped {prefix} -- {channel_name}  to  {channel_attributes[channel]}")

					# Handle C4D style channels
					else:
						my_table_of_phrases = re.split(r'\.', channel_name)
						last_item = my_table_of_phrases[-1]

						if last_item in channel_attributes:
							setattr(ldr.Clip1.OpenEXRFormat, channel_attributes[last_item], channel_name)
					
					# Get an identifier for the layernm
					ldr.SetData("prismmultchanlayer", prefix)

				loaders_list.append(ldr)
			except:
				logger.warning("ERROR: Failed to process multichannel EXR - failed to assign channels")
				return

		self.move_loaders(x_pos, y_pos, loaders_list)

		# create IN and OUT nodes.
		for node in loaders_list:
			if createwireless:
				self.createWireless(node)
			flow.Select(node, True)

		if len(loaders_list)>0:
			tool.Delete()
		
		comp.Unlock()
		comp.EndUndo()

		logger.debug(f"Processed multichannel EXR: {tool.Name}")
		
		return loaders_list


	################################################
	#                                              #
	#                   IMPORT3D                   #
	#                                              #
	################################################

	# abc_options = {
	# 	"Points": True,
	# 	"Transforms": True,
	# 	"Hierarchy": False,
	# 	"Lights": True,
	# 	"Normals": True,
	# 	"Meshes": True,
	# 	"UVs": True,
	# 	"Cameras": True,
	# 	"InvCameras": True
	# 	# "SamplingRate": 24
	# }
	
	# @err_catcher(name=__name__)
	# def getPythonLocation(self)-> str:
	# 	ospath = os.path.dirname(os.__file__)
	# 	path_components = os.path.split(ospath)
	# 	new_path = os.path.join(*path_components[:-1])
	# 	python_location = os.path.join(new_path, "python.exe")
	# 	# Construct the command as a list
	# 	return python_location


	# @err_catcher(name=__name__)
	# def create_and_run_bat(self):
	# 	import subprocess
	# 	home_dir = os.path.expanduser("~")
	# 	bat_file_path = os.path.join(home_dir, "tmpcmdwin.bat")
	# 	python_path = self.getPythonLocation()
	# 	package_path = os.path.join(os.path.dirname(__file__), 'thirdparty')

	# 	# Check if the batch file already exists
	# 	if os.path.exists(bat_file_path):
	# 		os.remove(bat_file_path)

	# 	bat_content = f"""@echo off
	# echo Running Python commands...
	# "{python_path}" -c "import sys; sys.path.append(r'{package_path}'); import pygetwindow as gw; gw.getWindowsWithTitle('Fusion Studio - [')[0].activate()"
	# @REM pause
	# exit
	# """

	# 	# Create the batch file
	# 	with open(bat_file_path, 'w') as bat_file:
	# 		bat_file.write(bat_content)

	# 	return bat_file_path


	# @err_catcher(name=__name__)
	# def focus_fusion_window(self):
	# 	import subprocess
	# 	# Get all windows
	# 	windows = gw.getAllTitles()

	# 	self.core.popup(f"windows:  {windows}")                                      #    TESTING

	# 	# Define the pattern using a regular expression
	# 	pattern = r'^Fusion Studio - '
	# 	window_title = "Fusion Studio - ["

	# 	# Filter windows based on the pattern
	# 	matching_windows = [window for window in windows if re.match(pattern, window)]
	# 	# Focus on the first matching window
	# 	if matching_windows:
	# 		# script_dir = os.path.dirname(os.path.abspath(__file__))
	# 		batch_file = self.create_and_run_bat()#os.path.join(script_dir, "cmdwin.bat")
	# 		cmdwin = subprocess.Popen(["cmd", "/c", "start", batch_file], shell=True)
	# 		time.sleep(1)
	# 		# Delete the batch file
	# 		os.remove(batch_file)
			
	# 		if not len(matching_windows)>1:	
	# 			matching_window = gw.getWindowsWithTitle(window_title)[0]
	# 			# print("matching_window: ", matching_window.title)
	# 			# matching_window.activate()
	# 			# time.sleep(1)
	# 			# print("active: ", matching_window.isActive)
	# 			if matching_window.isActive:
	# 				return True
	# 			else:
	# 				msg = f"Window with title '{window_title}' is not active.\nTry again leaving the cursor over the Fusion Window."
	# 				self.popup = self.core.popup(msg)
	# 				return False
	# 		else:
	# 			msg = f"There is more than one Window with title '{window_title}' open\nplease close one."
	# 			self.core.popup(msg)
	# 			return False

	# 	else:
	# 		msg = f"Window with title '{window_title}' not found."
	# 		self.core.popup(msg)
	# 		return False
		

	# @err_catcher(name=__name__)
	# def doUiImport(self, fusion, formatCall, interval, filepath):
	# 	if self.focus_fusion_window():
	# 		comp = fusion.GetCurrentComp()
	# 		#Call the dialog
	# 		fusion.QueueAction("Utility_Show", {"id":formatCall})
	# 		time.sleep(interval)
	# 		pyautogui.typewrite(filepath)
	# 		time.sleep(interval)
	# 		pyautogui.press("enter")
	# 		pyautogui.press("enter")
			
	# 		# Wait until file is imported
	# 		elapsedtime = 0
	# 		while len(comp.GetToolList(True))<0 and elapsedtime < 20:
	# 			loopinterval = 0.1
	# 			elapsedtime += loopinterval
	# 			time.sleep(loopinterval)
	# 		if len(comp.GetToolList(True)) > 0:
	# 			return True
	# 		else:
	# 			return False
	# 	else:
	# 		return False

		
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
		
	# 	#Warning
	# 	fString = "Importing this 3Dformat requires UI automation.\n\nPLEASE DO NOT USE THE MOUSE AFTER CLOSING THIS DIALOG UNTIL IMPORT IS DONE"
	# 	buttons = ["Continue"]
	# 	result = self.core.popupQuestion(fString, buttons=buttons, icon=QMessageBox.NoIcon)

	# 	imported = False
	# 	# if result == "Save":
	# 	# 	filepath = self.getCurrentFileName()
	# 	# 	didSave = False
	# 	# 	if not filepath == "":
	# 	# 		if self.core.fileInPipeline():
	# 	# 			didSave = self.core.saveScene(versionUp=False)
	# 	# 		else:
	# 	# 			didSave = self.saveScene(filepath)
	# 	# 		if not didSave == False:
	# 	# 			imported = self.doUiImport(fusion, formatCall, interval, filepath)
	# 	# 	else:
	# 	# 		self.core.popup("Scene can't be saved, save a version first")

	# 	# elif result == "Save new version":
	# 	# 	if self.core.fileInPipeline():
	# 	# 		self.core.saveScene()
	# 	# 		imported = self.doUiImport(fusion, formatCall, interval, filepath)

	# 	# elif result == "Continue":
	# 	# 	imported = self.doUiImport(fusion, formatCall, interval, filepath)

	# 	# else:
	# 	# 	imported = False

	# 	imported = self.doUiImport(fusion, formatCall, interval, filepath)
	# 	origin.stateManager.showNormal()

	# 	return imported


	@err_catcher(name=__name__)
	def importAlembic(self, importPath, origin):




		return self.importFormatByUI(origin=origin, formatCall="AbcImport", filepath=importPath, global_scale=100, options=self.abc_options)
	



	@err_catcher(name=__name__)
	def importUSD(self, importPath, origin):
		comp = self.getCurrentComp()

		self.core.popup(f"importPath:  {importPath}")                                      #    TESTING

		comp.Lock()
		
		#	Add uLoader node
		usdTool = comp.AddTool("uLoader")

		#	Set import file path
		usdTool["Filename"] = importPath

		#	Get versionInfo data
		versionInfoData = self.core.products.getProductDataFromFilepath(importPath)
		productName = versionInfoData["product"]
		productVersion = versionInfoData["version"]

		#	Set node name
		toolName = f"{productName}_{productVersion}"
		usdTool.SetAttrs({"TOOLS_Name": toolName})

		#	Add custom UUID
		usdTool.SetData('PrImportUID', self.createUUID())



		comp.Unlock()





		return True





	@err_catcher(name=__name__)
	def importFBX(self, importPath, origin):

		comp = self.getCurrentComp()

		comp.Lock()

		#	Add FBX Mesh node
		fbxTool = comp.AddTool("SurfaceFBXMesh")

		#	Set import mesh file path
		fbxTool["ImportFile"] = importPath

		#	Get versionInfo data
		versionInfoData = self.core.products.getProductDataFromFilepath(importPath)
		productName = versionInfoData["product"]
		productVersion = versionInfoData["version"]

		#	Set node name
		toolName = f"{productName}_{productVersion}"
		fbxTool.SetAttrs({"TOOLS_Name": toolName})

		#	Add custom UUID
		fbxTool.SetData('PrImportUID', self.createUUID())




		comp.Unlock()

		return True









		# return self.importFormatByUI(origin = origin, formatCall="FBXImport", filepath=importPath, global_scale=100)
	

	@err_catcher(name=__name__)
	def importBlenderCam(self, importPath, origin):
		from MH_BlenderCam_Fusion_Importer import BlenderCameraImporter
		BcamImporter = BlenderCameraImporter()
		return BcamImporter.import_blender_camera(importPath)


	# @err_catcher(name=__name__)
	# def sm_import_disableObjectTracking(self, origin):
	# 	self.deleteNodes(origin, [origin.setName])


	# #Main Import function
	@err_catcher(name=__name__)
	def sm_import_importToApp(self, origin, doImport, update, impFileName):


		#	BlenderCam Check
		root, _ = os.path.splitext(impFileName)
		isbcam = False
		new_file_path = os.path.normpath(root + '.bcam')
		if os.path.exists(new_file_path):
			isbcam = True
			impFileName = new_file_path
		



		comp = self.getCurrentComp()
		flow = comp.CurrentFrame.FlowView
		fileName = os.path.splitext(os.path.basename(impFileName))
		origin.setName = ""
		result = False


		# Check that we are not importing in a comp different than the one we started the stateManager from
		if not self.sm_checkCorrectComp(comp):
			return

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
		
		#	Get Extension
		ext = fileName[1].lower()

		#	Check if Image Format is supported
		if ext not in self.importHandlers:
			self.core.popup(f"Import format '{ext}' is not supported")
			logger.warning(f"Import format '{ext}' is not supported")
			return {"result": False, "doImport": doImport}

		else:
			# Do the importing
			result = self.importHandlers[ext]["importFunction"](impFileName, origin)

			self.core.popup(f"result of import function: {result}")                                      #    TESTING



		#After import update the stateManager interface
		# if result:
		# 	#check if there was a merge3D in the import and where was it connected to
		# 	newNodes = [n.Name for n in comp.GetToolList(True).values()]
		# 	if isbcam:
		# 		importedNodes = []
		# 		importedNodes.append(self.getNode(newNodes[0]))
		# 		origin.setName = "Import_" + fileName[0]			
		# 		origin.nodes = importedNodes
		# 	else:
		# 		refPosNode, positionedNodes = self.ReplaceBeforeImport(origin, newNodes)
		# 		self.cleanbeforeImport(origin)
		# 		if refPosNode:
		# 			atx, aty = flow.GetPosTable(refPosNode).values()
		
		# 		importedTools = comp.GetToolList(True).values()
		# 		#Set the position of the imported nodes relative to the previously active tool or last click in compView
		# 		impnodes = [n for n in importedTools]
		# 		if len(impnodes) > 0:
		# 			comp.Lock()

		# 			fisrtnode = impnodes[0]
		# 			fstnx, fstny = flow.GetPosTable(fisrtnode).values()

		# 			for n in impnodes:
		# 				if not n.Name in positionedNodes:
		# 					x,y  = flow.GetPosTable(n).values()

		# 					offset = [x-fstnx,y-fstny]
		# 					newx = x+(atx-x)+offset[0]
		# 					newy = y+(aty-y)+offset[1]
		# 					flow.SetPos(n, newx-1, newy)

		# 			comp.Unlock()
		# 		##########

		# 		importedNodes = []
		# 		for i in newNodes:
		# 			# Append sufix to objNames to identify product with unique Name
		# 			node = self.getObject(i)
		# 			newName = self.applyProductSufix(i, origin)
		# 			node.SetAttrs({"TOOLS_Name":newName, "TOOLB_NameSet": True})
		# 			importedNodes.append(self.getNode(newName))

		# 		origin.setName = "Import_" + fileName[0]			
		# 		origin.nodes = importedNodes

		# 	#Deselect All
		# 	flow.Select()

		# 	objs = [self.getObject(x) for x in importedNodes]
			
		# 	#select nodes in comp
		# 	for o in objs:
		# 		flow.Select(o)

		# 	#Set result to True if we have nodes
		# 	result = len(importedNodes) > 0

		return {"result": result, "doImport": doImport}


	# @err_catcher(name=__name__)
	# def getNode(self, obj):
	# 	if type(obj) == str:
	# 		node = {"name": obj}
	# 	elif type(obj) == dict:
	# 		node = {"name": obj["name"]}
	# 	else:
	# 		node = {"name": obj.Name}
	# 	return node
	

	# @err_catcher(name=__name__)
	# def selectNodes(self, origin):
	# 	if origin.lw_objects.selectedItems() != []:
	# 		nodes = []
	# 		for i in origin.lw_objects.selectedItems():
	# 			node = origin.nodes[origin.lw_objects.row(i)]
	# 			if self.isNodeValid(origin, node):
	# 				nodes.append(node)
	# 		# select(nodes)
					

	# @err_catcher(name=__name__)
	# def isNodeValid(self, origin, handle):
	# 	return True
		

	# @err_catcher(name=__name__)
	# def getObjectNodeNameByTool(self, origin, node):
	# 	if self.isNodeValid(origin, node):
	# 		try:
	# 			return node["name"]
	# 		except:
	# 			QMessageBox.warning(
	# 				self.core.messageParent, "Warning", "Cannot get name from %s" % node
	# 			)
	# 			return node
	# 	else:
	# 		return "invalid"
	

	# @err_catcher(name=__name__)
	# def getObject(self, node):
	# 	comp = self.getCurrentComp()
	# 	if type(node) == str:
	# 		node = self.getNode(node)

	# 	return comp.FindTool(node["name"])
	

	# @err_catcher(name=__name__)
	# def applyProductSufix(self, originalName, origin):
	# 	newName = originalName + "_" + origin.importPath.split("_")[-2]
	# 	return newName
	

	# @err_catcher(name=__name__)
	# def cleanbeforeImport(self, origin):
	# 	if origin.nodes == []:
	# 		return
	# 	nodes = []
	# 	for o in origin.nodes:
	# 		nodes.append(self.getNode(o))

	# 	self.deleteNodes(origin, nodes)
	# 	origin.nodes = []


	# @err_catcher(name=__name__)
	# def ReplaceBeforeImport(self, origin, newnodes):
	# 	comp = self.getCurrentComp()
	# 	if origin.nodes == []:
	# 		return None, []
	# 	nodes = []
	# 	nodenames =[]
	# 	outputnodes = []
	# 	positionednodes = []
	# 	sceneNode = None
		
	# 	# We are going to collect the existing nodes and check if there is a merge3D or transform3D node that represents the entry of the scene.
	# 	for o in origin.nodes:
	# 		hasmerge = False
	# 		node = comp.FindTool(o["name"])
	# 		if node:
	# 			# Store Scene Node Connections
	# 			nodeID  = node.GetAttrs("TOOLS_RegID")
	# 			ismerge = nodeID == "Merge3D"
	# 			# We try to account for Transform3D nodes that are not standarly Named.
	# 			istrans3D = nodeID == "Transform3D" and "Transform3D" in node.Name
	# 			# If there is no merge there should be a transform3D but if there is merge transform3D is out.
	# 			if ismerge or istrans3D:
	# 				if ismerge:
	# 					hasmerge = True
	# 				if ismerge or not hasmerge:
	# 					outputnodes = [] # clean this variable in case there was an unaccounted node
	# 					sceneNode = node
	# 					connectedinputs = node.output.GetConnectedInputs()
	# 					if len(connectedinputs)>0:
	# 						for v in connectedinputs.values():
	# 							connectedNode = {"node":v.GetTool().Name,"input":v.Name}
	# 							outputnodes.append(connectedNode)
	# 			nodenames.append(node.Name)
	# 			nodes.append(node)
	# 	for o in newnodes:
	# 		newnode = comp.FindTool(o)
	# 		# Reconnect the scene node
	# 		if sceneNode:
	# 			nodeID = newnode.GetAttrs("TOOLS_RegID")
	# 			sceneNID = sceneNode.GetAttrs("TOOLS_RegID")
	# 			if nodeID == sceneNID:

	# 				# We try to account for Transform3D nodes that are not standarly Named.
	# 				proceed = True
	# 				if nodeID == "Transform3D" and not "Transform3D" in newnode.Name:
	# 					proceed = False
					
	# 				if proceed and len(outputnodes) > 0:
	# 					for outn in outputnodes:
	# 						tool = comp.FindTool(outn["node"])
	# 						tool.ConnectInput(outn["input"], newnode)
	# 		# Match old to new
	# 		oldnodename = self.applyProductSufix(o, origin)
	# 		oldnode = comp.FindTool(oldnodename)

	# 		# If there is a previous version of the same node.
	# 		if oldnode:
	# 			# idx = 1
	# 			# check if it has valid inputs that are not part of previous import
	# 			for input in oldnode.GetInputList().values():
	# 				# idx+=1
	# 				connectedOutput = input.GetConnectedOutput()
	# 				if connectedOutput:
	# 					inputName = input.Name
	# 					connectedtool = connectedOutput.GetTool()
	# 					# Avoid Feyframe nodes
	# 					if not connectedtool.GetAttrs("TOOLS_RegID") =="BezierSpline" and not newnode.GetAttrs("TOOLS_RegID") == "Merge3D":
	# 						# check to avoid a connection that breaks the incoming hierarchy.
	# 						if not connectedtool.Name in nodenames:
	# 							newnode.ConnectInput(inputName, connectedtool)
	# 			# Reconnect the 3D Scene.
	# 			if sceneNode:
	# 				if sceneNode.GetAttrs("TOOLS_RegID") == "Merge3D":
	# 					if oldnode.GetAttrs("TOOLS_RegID") == "Merge3D":
	# 						mergednodes = []
	# 						sceneinputs = [input for input in oldnode.GetInputList().values() if "SceneInput" in input.Name]
	# 						# newsceneinputs = [input for input in newnode.GetInputList().values() if "SceneInput" in input.Name]
	# 						for input in sceneinputs:
	# 							connectedOutput = input.GetConnectedOutput()
	# 							if connectedOutput:
	# 								connectedtool = connectedOutput.GetTool()
	# 								if not connectedtool.Name in nodenames:
	# 									mergednodes.append(connectedtool)
	# 						if newnode.GetAttrs("TOOLS_RegID") == "Merge3D" and len(mergednodes) > 0:
	# 							newsceneinputs = [input for input in newnode.GetInputList().values() if "SceneInput" in input.Name]
	# 							for mergednode in mergednodes:
	# 								for input in newsceneinputs:
	# 									connectedOutput = input.GetConnectedOutput()
	# 									if not connectedOutput:
	# 										newnode.ConnectInput(input.Name, mergednode)
	# 			# Match position.
	# 			self.matchNodePos(newnode, oldnode)
	# 			positionednodes.append(newnode.Name)
			
	# 	# Return position
	# 	if sceneNode:
	# 		return sceneNode, positionednodes
		
	# 	return None, positionednodes


	# @err_catcher(name=__name__)
	# def sm_import_updateObjects(self, origin):
	# 	pass


	# @err_catcher(name=__name__)
	# def sm_import_removeNameSpaces(self, origin):
	# 	pass


	################################################
	#                                              #
	#                    PLAYBLAST                 #
	#                                              #
	################################################						#	TODO - NEED PLAYBLAST?

	# @err_catcher(name=__name__)
	# def sm_playblast_startup(self, origin):		
	# 	frange = self.getFrameRange(origin)
	# 	origin.sp_rangeStart.setValue(frange[0])
	# 	origin.sp_rangeEnd.setValue(frange[1])


	# @err_catcher(name=__name__)
	# def sm_playblast_createPlayblast(self, origin, jobFrames, outputName):
	# 	pass


	# @err_catcher(name=__name__)
	# def sm_playblast_preExecute(self, origin):
	# 	warnings = []

	# 	return warnings


	# @err_catcher(name=__name__)
	# def sm_playblast_execute(self, origin):
	# 	pass


	# @err_catcher(name=__name__)
	# def sm_playblast_postExecute(self, origin):
	# 	pass


	# @err_catcher(name=__name__)
	# def sm_createRenderPressed(self, origin):
	# 	comp = self.getCurrentComp()
	# 	if self.sm_checkCorrectComp(comp):
	# 		origin.createPressed("Render")


	################################################
	#                                              #
	#        	    NODE POSITIONING               #
	#                                              #
	################################################

	#Get last click on comp view.
	@err_catcher(name=__name__)
	def find_LastClickPosition(self):
		comp = self.getCurrentComp()
		flow = comp.CurrentFrame.FlowView
		posNode = comp.AddToolAction("Background")
		x,y = flow.GetPosTable(posNode).values()
		posNode.Delete()

		return x,y
		# return -32768, -32768


	@err_catcher(name=__name__)
	def find_extreme_loader(self):
		# Get the current composition
		comp = self.getCurrentComp()
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
		comp = self.getCurrentComp()
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
		comp = self.getCurrentComp()
		flow = comp.CurrentFrame.FlowView
		x,y = flow.GetPosTable(nodeInPos).values()
		self.set_node_position(flow, nodeTomove, x, y)


	#The name of this function comes for its initial use to position the "state manager node" that what used before using SetData.
	@err_catcher(name=__name__)
	def setNodePosition(self, node, find_min=True, x_offset=-2, y_offset=0, ignore_node_type=None, refNode=None):
		# Get the active composition
		comp = self.getCurrentComp()
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
		comp = self.getCurrentComp()
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
				logger.warning("ERROR: The State Manager was originally opened in another comp.\n" 
								"It will now close and open again to avoid corrupting this comp's state data.")
				if displaypopup:
					self.core.popup("The State Manager was originally opened in another comp.\n"
									"It will now close and open again to avoid corrupting this comp's state data.")
					self.core.closeSM(restart=True)
				return False
			
		return True
	
	
	@err_catcher(name=__name__)
	def sm_getExternalFiles(self, origin):
		extFiles = []
		return [extFiles, []]
	

	@err_catcher(name=__name__)
	def setDefaultState(self):
		comp = self.getCurrentComp()
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
			try:
				comp.SetData("prismstates",defaultState)
				logger.debug("Saved the empty state data to the comp")
			except:
				logger.warning(f"ERROR: Unable to save default State Data to comp: {comp}")


	@err_catcher(name=__name__)
	def sm_saveStates(self, origin, buf):
		comp = self.getCurrentComp()
		if self.sm_checkCorrectComp(comp):
			try:
				comp.SetData("prismstates", buf + "_..._")
				logger.debug(f"Saved the state data to the comp.")
			except:
				logger.warning(f"ERROR: Unable to save State Data to comp: {comp}")


	@err_catcher(name=__name__)
	def sm_saveImports(self, origin, importPaths):
		comp = self.getCurrentComp()
		if self.sm_checkCorrectComp(comp):
			prismdata = comp.GetData("prismstates")
			prismdata += importPaths.replace("\\\\", "\\")
			comp.SetData("prismstates", prismdata)


	@err_catcher(name=__name__)
	def sm_readStates(self, origin):
		comp = self.getCurrentComp()
		if self.sm_checkCorrectComp(comp):
			try:
				prismdata = comp.GetData("prismstates")
				return prismdata.split("_..._")[0]
			except:
				logger.warning(f"ERROR:  Unable to read State Data from comp: {comp}")
				return 


	#	Gets called from SM to remove all States
	@err_catcher(name=__name__)
	def sm_deleteStates(self, origin):
		comp = self.getCurrentComp()
		if self.sm_checkCorrectComp(comp):
			#	Sets the states datablock to empty default state
			self.setDefaultState()
			self.core.popup("All States have been removed.\n"
							"You may have to remove associated Savers from the comp manually.")



	@err_catcher(name=__name__)
	def getImportPaths(self, origin):
		comp = self.getCurrentComp()
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
		origin.setWindowIcon(QIcon(self.prismAppIcon))


	@err_catcher(name=__name__)
	def onProjectBrowserStartup(self, origin):
		self.pbUI = origin
		origin.setWindowIcon(QIcon(self.prismAppIcon))
	

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
		comp = self.getCurrentComp()
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
		origin.setWindowIcon(QIcon(self.prismAppIcon))
		#	Remove Import buttons
		# origin.b_createImport.deleteLater()
		origin.b_shotCam.deleteLater()

		#	Remove Export and Playblast buttons
		origin.b_createExport.deleteLater()
		origin.b_createPlayblast.deleteLater()



		#	Create Import Image buton
		origin.b_importImage = QPushButton(origin.w_CreateImports)
		origin.b_importImage.setObjectName("b_importImage")
		origin.b_importImage.setText("Import Image")
		#	Add to the beginning of the layout
		origin.horizontalLayout_3.insertWidget(0, origin.b_importImage)
		#	Add connection to button
		origin.b_importImage.clicked.connect(lambda: self.addImportImageState(origin))

		#	Create Import 3d buton
		# origin.b_import3d = QPushButton(origin.w_CreateImports)
		# origin.b_import3d.setObjectName("b_import3d")
		# origin.b_import3d.setText("Import 3d")
		# #	Add to the 2nd position of the layout
		# origin.horizontalLayout_3.insertWidget(1, origin.b_import3d)
		# #	Add connection to button
		# origin.b_import3d.clicked.connect(lambda: self.addImport3dState(origin))


		# #	Change text of Import Button
		# origin.b_createImport.setText("Import 3d")
		# #	Remove native Prism connection from button
		# origin.b_createImport.clicked.disconnect()

		# Create a new button for RenderGroup
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

		#	Delete unused States
		sm = self.core.getStateManager()
		removestates = ['Code', 'Export', 'Playblast']
		for state in removestates:
			if state in sm.stateTypes.keys():
				try:
					del sm.stateTypes[state]
				except:
					logger.debug(f"Unable to remove default state: {state}")

		comp = self.getCurrentComp()
		
		#Set the comp used when sm was opened for reference when saving states.
		self.comp = comp
		#Set State Manager Data on first open.
		if comp.GetData("prismstates") is None:
			self.setDefaultState()

		self.monkeypatchedsm = origin
		try:
			self.core.plugins.monkeyPatch(origin.rclTree, self.rclTree, self, force=True)
			self.core.plugins.monkeyPatch(self.core.mediaProducts.getVersionStackContextFromPath,
								 			self.getVersionStackContextFromPath,
											self,
											force=True)
		except Exception as e:
			logger.warning(f"ERROR: Failed to load patched functions:\n{e}")

		#origin.gb_import.setStyleSheet("margin-top: 20px;")


	@err_catcher(name=__name__)
	def onStateManagerShow(self, origin):
		self.smUI = origin

		##	Resizes the StateManager Window
		# 	Check if SM has a resize method and resize it
		if hasattr(self.smUI, 'resize'):
			try:
				self.smUI.resize(800, self.smUI.size().height())
			except:
				pass

		#	Check if SM has a splitter resize method
		if hasattr(self.smUI, 'splitter') and hasattr(self.smUI.splitter, 'setSizes'):
			try:
				# Splitter position
				splitterPos = 350

				# 	Calculate the sizes for the splitter
				height = self.smUI.splitter.size().height()
				LeftSize = splitterPos
				RightSize = height - splitterPos

				# 	Set the sizes of the splitter areas
				self.smUI.splitter.setSizes([LeftSize, RightSize])
			except:
				pass

		try:
			self.popup.close()
		except:
			pass


	@err_catcher(name=__name__)
	def onStateManagerClose(self, origin):
		self.smUI = None


	@err_catcher(name=__name__)
	def onStateCreated(self, origin, state, stateData):
		# if state.className in ["ImageRender", "Playblast"]:								#	FROM REMOVING RENDER REZ PRESETS
		# 	state.b_resPresets.setStyleSheet("padding-left: 1px;padding-right: 1px;")

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
		comp = self.getCurrentComp()
		if stateui.className == "ImageRender":
			try:
				node = comp.FindTool(stateui.b_setRendernode.text())
				if node:
					fString = "Do you want to also delete the Saver node\nassociated with this render:"
					buttons = ["Yes", "No"]
					result = self.core.popupQuestion(fString, buttons=buttons, icon=QMessageBox.NoIcon)
					if result == "Yes":
						node.Delete()
			except:
				logger.warning(f"ERROR: Unable to remove Saver: {node.Name}")
		# elif stateui.className == "ImportFile":
			

	@err_catcher(name=__name__)
	def addImportImageState(self, origin):
		# origin.createState("RenderGroup")

		#	TODO  MAKE OPEN PROJECTBROWSER

		self.core.popup("Importing Images through the State Manager is not yet supported.\n\n"
				  		"Please import through the Project Browser Media tab")                        #    TODO Implement Image Import
		


	@err_catcher(name=__name__)
	def addImport3dState(self, origin):

		origin.createState("ImportFile", parent=self, setActive=True)					#	TODO - TEMP - This is the default action
		
		# states = origin.stateTypes

		# self.core.popup(f"import3dStates:  {states}")                                      #    TESTING

		# for state in states:
		# 	import3dStates += getattr(origin.stateTypes[state], "stateCategories", {}).get(stateType, [])


	@err_catcher(name=__name__)
	def addRenderGroup(self, origin):
		origin.createState("RenderGroup")



			


	##########################################
	#                                        #
	################# POPUPS #################
	#                                        #
	##########################################	
		
	@err_catcher(name=__name__)
	def popupQuestion(self, text, title=None, buttons=None, icon=None, parent=None, checked=False):
		title = title or "Prism"
		buttons = buttons or ["Yes", "No"]
		parent = parent or getattr(self.core, "messageParent", None)

		dialog = CustomMessageBox(text, title, buttons, parent)
		dialog.checkbox.setChecked(checked)
		dialog.exec_()

		# Return both the clicked button text and the checkbox state
		return dialog.clicked_button_text, dialog.checkbox_checked
		
	################################################
	#                                              #
	#        	 MONKEYPATCHED FUNCTIONS           #
	#                                              #
	################################################

	#Right click menu from nodes on state manager to get previous versions.
	@err_catcher(name=__name__)
	def rclTree(self, pos, activeList):
		logger.debug("Loading patched function: 'rclTree'")

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
	def getVersionStackContextFromPath(self, filepath, mediaType=None):
		logger.debug("Loading patched function: 'getVersionStackContextFromPath'")

		# context = self.core.paths.getRenderProductData(filepath)
		#The only modification was putting the mediaType as an argument for the context in the next line which replaces the previous one.
		context = self.core.paths.getRenderProductData(filepath, mediaType=mediaType)

		if mediaType:
			context["mediaType"] = mediaType

		if "asset" in context:
			context["asset"] = os.path.basename(context["asset_path"])

		if "version" in context:
			del context["version"]
		if "comment" in context:
			del context["comment"]
		if "user" in context:
			del context["user"]

		return context


	@err_catcher(name=__name__)
	def preDelete(
		self,
		item=None,
		baseText="Do you also want to delete the connected objects?\n\n",
	):
		
		logger.debug("Loading patched function: 'preDelete'")

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
					message += self.core.appPlugin.getObjectNodeNameByTool(state, val) + "\n"

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


	# These two functions should take into account the dynamic padding, that is the only modification, next to changing self to a reference to the mediabrowser.
	@err_catcher(name=__name__)
	def compGetImportSource(self):
		logger.debug("Loading patched function: 'compGetImportSource'")

		mediabrowser = self.monkeypatchedmediabrowser # added this is refered as self in the original.
		#
		sourceFolder = os.path.dirname(mediabrowser.seq[0]).replace("\\", "/") #
		sources = self.core.media.getImgSources(sourceFolder)
		sourceData = []

		framepadding = self.core.framePadding #added
		for curSourcePath in sources:
			if "#" * framepadding in curSourcePath: # changed
				if mediabrowser.pstart == "?" or mediabrowser.pend == "?": #
					firstFrame = None
					lastFrame = None
				else:
					firstFrame = mediabrowser.pstart #
					lastFrame = mediabrowser.pend #

				filePath = curSourcePath.replace("\\", "/")
			else:
				filePath = curSourcePath.replace("\\", "/")
				firstFrame = None
				lastFrame = None

			sourceData.append([filePath, firstFrame, lastFrame])

		return sourceData

	@err_catcher(name=__name__)
	def compGetImportPasses(self):
		logger.debug("Loading patched function: 'compGetImportPasses'")

		mediabrowser = self.monkeypatchedmediabrowser # added this is refered as self in the original.
		#
		framepadding = self.core.framePadding #added
		sourceFolder = os.path.dirname(
			os.path.dirname(mediabrowser.seq[0])
		).replace("\\", "/")
		# check if the mediaType is 2d #added
		if "\\2dRender\\" in mediabrowser.seq[0]:
			sourceFolder = os.path.dirname(mediabrowser.seq[0]).replace("\\", "/")
		passes = [
			x
			for x in os.listdir(sourceFolder)
			if x[-5:] not in ["(mp4)", "(jpg)", "(png)"]
			and not x.startswith("_")  # Exclude folders starting with "_" like _thumbs #added
			and os.path.isdir(os.path.join(sourceFolder, x))
		]
		sourceData = []

		for curPass in passes:
			curPassPath = os.path.join(sourceFolder, curPass)

			imgs = os.listdir(curPassPath)
			if len(imgs) == 0:
				continue

			if (
				len(imgs) > 1
				and mediabrowser.pstart #
				and mediabrowser.pend #
				and mediabrowser.pstart != "?" #
				and mediabrowser.pend != "?" #
			):
				firstFrame = mediabrowser.pstart #
				lastFrame = mediabrowser.pend #

				curPassName = imgs[0].split(".")[0]
				increment = "#" * framepadding # changed
				curPassFormat = imgs[0].split(".")[-1]

				filePath = os.path.join(
					sourceFolder,
					curPass,
					".".join([curPassName, increment, curPassFormat]),
				).replace("\\", "/")
			else:
				filePath = os.path.join(curPassPath, imgs[0]).replace("\\", "/")
				firstFrame = None
				lastFrame = None

			sourceData.append([filePath, firstFrame, lastFrame])

		return sourceData



class CustomMessageBox(QDialog):
	def __init__(self, text, title, buttons, parent=None, checked=False):
		super().__init__(parent)

		self.setWindowTitle(title)
		self.checkbox_checked = False

		# Set up the layout
		layout = QVBoxLayout(self)

		# Add the main message text
		label = QLabel(text)
		layout.addWidget(label)

		# Add the checkbox
		self.checkbox = QCheckBox("Import Without Wireless/Sorting")
		self.checkbox.setToolTip("If this option is selected, Nodes will be added on last clicked position and will not be taken into account when sorting.\nThey also will not be integrated into a wireless workflow.")
		layout.addWidget(self.checkbox)

		# Add the dialog buttons
		self.button_box = QDialogButtonBox()
		self.button_map = {}

		# Add buttons with ActionRole to the dialog
		for button_text in buttons:
			role = QDialogButtonBox.ActionRole
			button = self.button_box.addButton(button_text, role)
			self.button_map[button] = button_text  # Map buttons to their text

		# Connect button clicked signal to handler
		self.button_box.clicked.connect(self.handle_button_clicked)
		layout.addWidget(self.button_box)

		# Set dialog layout
		self.setLayout(layout)

	def set_checkbox_checked_state(self, checked):
		self.checkbox.setChecked(checked)

	def handle_button_clicked(self, button):
		self.checkbox_checked = self.checkbox.isChecked()
		self.clicked_button_text = self.button_map[button]
		self.accept()  # Close the dialog
