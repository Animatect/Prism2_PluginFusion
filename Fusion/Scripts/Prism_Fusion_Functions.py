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

#	Import Prism Fusion Libraries
import Libs.Prism_Fusion_lib_Fus as Fus
import Libs.Prism_Fusion_lib_CompDb as CompDb
import Libs.Prism_Fusion_lib_3d as Fus3d

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
			callbacks = [
						("onUserSettingsOpen", self.onUserSettingsOpen),
						("onProjectBrowserStartup", self.onProjectBrowserStartup),
						("onProjectBrowserClose", self.onProjectBrowserClose),
						("onProjectBrowserShow", self.onProjectBrowserShow),
						("onProjectBrowserCalled", self.onProjectBrowserCalled),
						("onStateManagerCalled", self.onStateManagerCalled),
						("onStateManagerOpen", self.onStateManagerOpen),
						("onStateManagerClose", self.onStateManagerClose),
						("onStateManagerShow", self.onStateManagerShow),
						("onStateCreated", self.onStateCreated),
						# ("onStateDeleted", self.onStateDeleted),
						("getIconPathForFileType", self.getIconPathForFileType),
						("openPBListContextMenu", self.openPBListContextMenu),
						("onMediaBrowserTaskUpdate", self.onMediaBrowserTaskUpdate),
				]

			# Iterate through the list to register callbacks
			for callback_name, method in callbacks:
				self.core.registerCallback(callback_name, method, plugin=self.plugin)

			logger.debug("Registered callbacks")

		except Exception as e:
			logger.warning(f"ERROR: Failed to register callbacks:\n{e}")
		
		self.importHandlers = {
			".abc": {"importFunction": self.importABC},
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

		self.fusionToolsColorsDict = {
			'Clear Color': {'R': 0.000011, 'G': 0.000011, 'B': 0.000011 },
			'Orange': {'R': 0.9215686274509803, 'G': 0.43137254901960786, 'B': 0.0 },
			'Apricot': {'R': 1.0, 'G': 0.6588235294117647, 'B': 0.2 },
			'Yellow': {'R': 0.8862745098039215, 'G': 0.6627450980392157, 'B': 0.10980392156862745},
			'Lime': {'R': 0.6235294117647059, 'G': 0.7764705882352941, 'B': 0.08235294117647059},
			'Olive': {'R': 0.37254901960784315, 'G': 0.6, 'B': 0.12549019607843137},
			'Green': {'R': 0.26666666666666666, 'G': 0.5607843137254902, 'B': 0.396078431372549},
			'Teal': {'R': 0.0, 'G': 0.596078431372549, 'B': 0.6},
			'Navy': {'R': 0.08235294117647059, 'G': 0.3843137254901961, 'B': 0.5176470588235295},
			'Blue': {'R': 0.4745098039215686, 'G': 0.6588235294117647, 'B': 0.8156862745098039},
			'Purple': {'R': 0.6, 'G': 0.45098039215686275, 'B': 0.6274509803921569},
			'Violet': {'R': 0.5843137254901961, 'G': 0.29411764705882354, 'B': 0.803921568627451},
			'Pink': {'R': 0.9137254901960784, 'G': 0.5490196078431373, 'B': 0.7098039215686275},
			'Tan': {'R': 0.7254901960784313, 'G': 0.6901960784313725, 'B': 0.592156862745098},
			'Beige': {'R': 0.7764705882352941, 'G': 0.6274509803921569, 'B': 0.4666666666666667},
			'Brown': {'R': 0.6, 'G': 0.4, 'B': 0.0},
			'Chocolate': {'R': 0.5490196078431373, 'G': 0.35294117647058826, 'B': 0.24705882352941178}
		}

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



	##########################################################
	##														##
	##	 Wrappers for External calls to Library Functions	##
	##														##
	##########################################################

	#	Returns the filename of the current comp
	@err_catcher(name=__name__)
	def getCurrentFileName(self, origin=None, path=True):
		curComp = self.getCurrentComp()
		return Fus.getCurrentFileName(curComp)
		

	@err_catcher(name=__name__)
	def openScene(self, origin, filepath, force=False):
		return Fus.openScene(self.fusion, self.sceneFormats, filepath, force=force)
	

	@err_catcher(name=__name__)
	def saveScene(self, origin, filepath, details={}):
		curComp = self.getCurrentComp()
		return Fus.saveScene(curComp, filepath, details)
	

	@err_catcher(name=__name__)
	def getFrameRange(self, origin):
		curComp = self.getCurrentComp()
		return Fus.getFrameRange(curComp)


	@err_catcher(name=__name__)
	def setFrameRange(self, origin, startFrame, endFrame):
		comp = self.getCurrentComp()
		Fus.setFrameRange(comp, startFrame, endFrame)

	@err_catcher(name=__name__)
	def getFPS(self, origin):
		comp = self.getCurrentComp()
		return Fus.getFPS(comp)
	

	@err_catcher(name=__name__)
	def setFPS(self, origin, fps):
		comp = self.getCurrentComp()
		Fus.setFPS(comp, fps)


	@err_catcher(name=__name__)
	def getResolution(self):
		comp = self.getCurrentComp()
		return Fus.getResolution(comp)


	@err_catcher(name=__name__)
	def setResolution(self, width=None, height=None):
		comp = self.getCurrentComp()
		Fus.setResolution(comp, width, height)

	@err_catcher(name=__name__)
	def nodeExists(self, nodeUID):
		comp = self.getCurrentComp()
		return CompDb.nodeExists(comp, nodeUID)
	

	@err_catcher(name=__name__)
	def getNodeByUID(self, nodeUID):
		comp = self.getCurrentComp()
		return CompDb.getNodeByUID(comp, nodeUID)
	

	@err_catcher(name=__name__)
	def getNodeNameByUID(self, nodeUID):
		comp = self.getCurrentComp()
		return CompDb.getNodeNameByUID(comp, nodeUID)
	

	@err_catcher(name=__name__)
	def isPassThrough(self, nodeUID):
		comp = self.getCurrentComp()
		return CompDb.isPassThrough(comp, nodeUID)


	@err_catcher(name=__name__)
	def setPassThrough(self, nodeUID=None, node=None, passThrough=False):
		comp = self.getCurrentComp()
		CompDb.setPassThrough(comp, nodeUID=nodeUID, node=node, passThrough=passThrough)


	@err_catcher(name=__name__)
	def setDefaultState(self):
		comp = self.getCurrentComp()
		if self.sm_checkCorrectComp(comp):
			CompDb.setDefaultState(comp)


	@err_catcher(name=__name__)
	def sm_saveStates(self, origin, buf):
		comp = self.getCurrentComp()
		if self.sm_checkCorrectComp(comp):
			CompDb.sm_saveStates(comp, buf)


	@err_catcher(name=__name__)
	def sm_saveImports(self, origin, importPaths):
		comp = self.getCurrentComp()
		if self.sm_checkCorrectComp(comp):
			CompDb.sm_saveImports(comp, importPaths)


	@err_catcher(name=__name__)
	def sm_readStates(self, origin):
		comp = self.getCurrentComp()
		if self.sm_checkCorrectComp(comp):
			return CompDb.sm_readStates(comp)


	#	Gets called from SM to remove all States
	@err_catcher(name=__name__)
	def sm_deleteStates(self, origin):
		comp = self.getCurrentComp()
		if self.sm_checkCorrectComp(comp):
			#	Sets the states datablock to empty default state
			CompDb.setDefaultState(comp)
			self.core.popup("All States have been removed.\n"
							"You may have to remove associated Loaders and Savers\n"
							"from the comp manually.")


	@err_catcher(name=__name__)
	def getImportPaths(self, origin):
		comp = self.getCurrentComp()
		if self.sm_checkCorrectComp(comp):
			return CompDb.getImportPaths(comp)


#########################################
		

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
	def getSceneExtension(self, origin):
		return self.sceneFormats[0]
		

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


	#	Creates UUID													#	ADD TO CompDB
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
		

	@err_catcher(name=__name__)
	def getAppVersion(self, origin):
		try:
			return self.fusion.Version
		except:
			return None
		
		
	@err_catcher(name=__name__)
	def getFuseFormat(self, extension):
		for fmt in self.outputFormats:
			if fmt["extension"] == extension.lower():
				fuseFormat = fmt["fuseName"]
				return fuseFormat


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
				thumbSaver = Fus.addTool(comp, "Saver")

				# Connect the Saver tool to the currently selected tool
				thumbSaver.Input = thumbTool

				# Set the path for the Saver tool
				thumbSaver.Clip = os.path.join(tempDir, thumbName + ".jpg")

				#   Get current frame number
				currFrame = Fus.getCurrentFrame(comp)

				#	Get Comps render range
				origStartFrame, origEndFrame = Fus.getRenderRange(comp)

				# Temporarily set the render range to the current frame
				Fus.setRenderRange(comp, currFrame, currFrame)

				# Render the current frame
				comp.Render()

				# Restore the original render range
				Fus.setRenderRange(comp, origStartFrame, origEndFrame)

			#   Deals with the frame number suffix added by Fusion rener
			pattern = os.path.join(tempDir, thumbName + "*.jpg")
			renderedThumbs = glob.glob(pattern)

			if renderedThumbs:
				renderedThumb = renderedThumbs[0]  # Assuming only one matching file
				os.rename(renderedThumb, thumbPath)
				logger.debug(f"Created Thumbnail from: {CompDb.getNodeNameByTool(thumbTool)}")
			
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
			toolName = CompDb.getNodeNameByTool(tool)

			if mode == "save":
				# Save the current pass-through state
				origSaverList[toolName] = CompDb.isPassThrough(comp, node=tool)
				CompDb.setPassThrough(comp, node=tool, passThrough=True)
			elif mode == "load":
				# Restore the original pass-through state
				if toolName in origSaverList:
					CompDb.setPassThrough(comp, node=tool, passThrough=origSaverList[toolName])

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
			if self.isSaver(tool) and not CompDb.isPassThrough(comp, node=tool):
				return tool

		# 3. Check for any saver, even if pass-through
		for tool in comp.GetToolList(False).values():
			if self.isSaver(tool):
				return tool

		# 4. Fallback to the final tool in the flow
		return Fus.getLastTool(comp) or None



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
			if CompDb.getNodeType(tool) == "Saver":
				return True
			else:
				return False
		except:
			return False
	

	#	Returns Fusion-legal Saver name base on State name
	@err_catcher(name=__name__)
	def getRendernodeName(self, stateName):
		legalName = self.getFusLegalName(stateName)
		nodeName = f"PrSAVER_{legalName}"

		return nodeName
	
	
	#	Creates Saver with UUID associated with ImageRender state
	@err_catcher(name=__name__)
	def createRendernode(self, nodeUID, nodeData):
		comp = self.getCurrentComp()
		if self.sm_checkCorrectComp(comp):
			if not CompDb.nodeExists(comp, nodeUID):
				comp.Lock()

				#	Add Saver to Comp
				sv = Fus.addTool(comp, "Saver", nodeData)

				comp.Unlock()

				#	Add node to Comp Database
				CompDb.addNodeToDB(comp, "render2d", nodeUID, nodeData)

				#	Position Saver
				if not Fus.posRelativeToNode(comp, sv):
					try:
						#Move Render Node to the Right of the scene	
						Fus.setNodePosition(comp, sv, find_min=False, x_offset=10, ignore_node_type="Saver")
						Fus.stackNodesByType(comp, sv)
					except:
						logger.debug(f"ERROR: Not able to position {nodeData['nodeName']}")

			if sv:
				logger.debug(f"Saver created for: {nodeData['nodeName']} - {nodeUID}")
				return sv
			else:
				logger.warning(f"ERROR: Unable to create Saver for {nodeData['nodeName']}")
				return False


	#	Updates Saver node name
	@err_catcher(name=__name__)
	def updateRendernode(self, nodeUID, nodeData):
		comp = self.getCurrentComp()
		if self.sm_checkCorrectComp(comp):
			sv = CompDb.getNodeByUID(comp, nodeUID)

			if sv:
				comp.Lock()
				#	Update Saver Info
				Fus.updateTool(sv, nodeData)
				comp.Unlock()

				#	Update Node in Comp Database
				CompDb.updateNodeInfo(comp, "render2d", nodeUID, nodeData)

				logger.debug(f"Saver updated: {nodeData['nodeName']}")
			else:
				logger.warning(f"ERROR: Not able to update: {nodeData['nodeName']}")

			return sv
		

	#	Configures Saver filepath and image format
	@err_catcher(name=__name__)
	def configureRenderNode(self, nodeUID, nodeData):
		comp = self.getCurrentComp()
		if self.sm_checkCorrectComp(comp):
			sv = CompDb.getNodeByUID(comp, nodeUID)
			if sv:
				#	Update Saver
				Fus.updateTool(sv, nodeData)
				#	Update Comp Database
				CompDb.updateNodeInfo(comp, "render2d", nodeUID, nodeData)

				#	Check if Saver is connected to something
				if Fus.hasConnectedInput(sv):
					if "nodeName" in nodeData:
						logger.debug(f"Configured Saver: {nodeData['nodeName']}")
					else:
						logger.debug(f"Configured Saver: {nodeUID}")


				else:
					logger.debug(f"ERROR: Render Node is not connected: {nodeUID}")
			else:
				logger.warning(f"ERROR: Render Node does not exist: {nodeUID}")


	#	Removes Node from Comp
	@err_catcher(name=__name__)
	def deleteNode(self, type, nodeUID, delAction):
		comp = self.getCurrentComp()
		if self.sm_checkCorrectComp(comp):
			if delAction and CompDb.nodeExists(comp, nodeUID):
				#	Delete the Tool from the Comp
				try:
					tool = CompDb.getNodeByUID(comp, nodeUID)
					toolName = CompDb.getNodeNameByUID(comp, nodeUID)

					tool.Delete()
					logger.debug(f"Removed tool '{toolName}")

				except:
					logger.warning(f"ERROR:  Unable to remove tool from Comp: {nodeUID}")

			#	Remove the Tool from the Comp Database
			CompDb.removeNodeFromDB(comp, type, nodeUID)
	

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
	# @err_catcher(name=__name__)
	# def stackNodesByType(self, nodetostack, yoffset=3, tooltype="Saver"):
	# 	comp = self.getCurrentComp()
	# 	flow = comp.CurrentFrame.FlowView

	# 	origx, origy = flow.GetPosTable(nodetostack).values()

	# 	toollist = comp.GetToolList().values()
		
	# 	thresh_y_position = -float('inf')
	# 	upmost_node = None		

	# 	# Find the upmost node
	# 	for node in toollist:
	# 		try:
	# 			if node.Name == nodetostack.Name:
	# 					continue
				
	# 			if node.GetAttrs("TOOLS_RegID") == tooltype:
	# 				postable = flow.GetPosTable(node)
	# 				y = thresh_y_position
	# 				#check if node has a postable.
	# 				if postable:
	# 					# Get the node's position
	# 					x,y = postable.values()

	# 					if y > thresh_y_position:
	# 						thresh_y_position = y
	# 						upmost_node = node
	# 		except Exception as e:
	# 			logger.warning(f"ERROR: Unable to stack nodes:\n{e}")

	# 	if upmost_node:
	# 		#set pos to the leftmost or rightmost node
	# 		flow.SetPos(nodetostack, origx, thresh_y_position + yoffset)



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
		comp = self.getCurrentComp()
		stateDataRaw = json.loads(self.sm_readStates(self))

		# Iterate through the states to find the matching state dictionary
		stateDetails = None
		for stateData in stateDataRaw["states"]:
			if stateData.get("nodeUID") == nodeUID:
				stateDetails = stateData
				logger.debug(f"State data found for: {CompDb.getNodeNameByUID(comp, nodeUID)}")
				return stateDetails

		logging.warning(f"ERROR: No state details for:  {nodeUID}")
		return None


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
				scaleTool = Fus.addTool(comp, "Scale", autoConnect=0)
				#	Add tool to temp list for later deletion
				self.tempScaleTools.append(scaleTool)
				#	Set Scale Sizing
				scaleTool.SetInput("XSize", scaleOvrCode)

				# Rewire the connections
				prev_input = Fus.getToolBefore(sv)
				if prev_input:
					Fus.connectTools(prev_input, scaleTool)
					Fus.connectTools(scaleTool, sv)
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
			nodeName = CompDb.getNodeNameByUID(comp, nodeUID)

			#	Exits if unable to get state data
			if not stateData:
				logger.warning(f"ERROR: Unable to configure RenderComp for {nodeName}")

			sv = CompDb.getNodeByUID(comp, nodeUID)
			CompDb.setPassThrough(comp, nodeUID=nodeUID, passThrough=False)

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

			#	Configure Saver with new filepath						#	TODO
			nodeData = {"nodeName": nodeName,
						"filepath": self.outputPath,
			   			"format": extension,
						"fuseFormat": self.getFuseFormat(extension)}

			self.configureRenderNode(nodeUID, nodeData)

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

			nodeUID = rSettings["nodeUID"]

			sv = CompDb.getNodeByUID(comp, nodeUID)

			if sv:
				nodeData = {"filepath": outputName,
							"version": rSettings["version"],
			   				"format": rSettings["format"],
							"fuseFormat": rSettings["fuseFormat"]
							}
				
				self.configureRenderNode(nodeUID, nodeData)
				# sv.Clip = outputName

				if not Fus.hasConnectedInput(sv):
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
	def reloadLoader(self, comp, node, filePath, firstframe, lastframe):
		if CompDb.getNodeType(node) == 'Loader':
			try:
				node = node
				loaderPath = filePath
				loaderName = CompDb.getNodeNameByTool(node)

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
				CompDb.setPassThrough(comp, node=node, passThrough=True)
				CompDb.setPassThrough(comp, node=node, passThrough=False)

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
		
		#	Get Identifier Context Data - contains:
			#	aov: current aov
			#	displayName: adds the 2d or exteral to the name
			#	extension
			#	identifier
			#	itemType: shot or asset
			#	locations
			#	mediaType: 3drenders, 2drenders, externalMedia
			#	path: dir containing media. is aov dir if aov, ver number if no aov
			#	version
		contextRaw = mediaBrowser.getCurRenders()
		if isinstance(contextRaw, list):
			context = contextRaw[0] if len(contextRaw) > 0 else None
		else:
			context = contextRaw

		# self.core.popup(f"context:  {context}")                                      #    TESTING

		# Check if file is Linked
		path = context["path"]
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
		source = context["source"]
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
			self.fusionImportSource(mediaBrowser, context, sortnodes=not checkbox_checked)

		elif result == "All AOVs":
			self.fusionImportPasses(mediaBrowser, context, dataSources, sortnodes=not checkbox_checked)

		elif result == "Update Selected":
			self.fusionUpdateSelectedPasses(mediaBrowser, context, sortnodes=not checkbox_checked)
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
	def fusionImportSource(self, mediaBrowser, context, sortnodes=True):
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
			refNode = None
			updatehandle:list = [] # Required to return data on the updated nodes.
			
			if sortnodes:
				refNode = leftmostNode
				
			try:
				node = self.processImageImport(
								imageData,
								context, 
								updatehandle=updatehandle,
								refNode=refNode,
								createwireless=sortnodes
								)
			except:
				logger.warning("ERROR: Unable to process import images")
				return

			if sortnodes:
				if not leftmostNode:
					leftmostNode = node

				self.sort_loaders(leftmostNode, reconnectIn=True, sortnodes=sortnodes)
					
			# deselect all nodes
			flow.Select()
			self.getUpdatedNodesFeedback(updatehandle)

			logger.debug(f"Imported image: {imageData['filePath']}")


	@err_catcher(name=__name__)
	def fusionImportPasses(self, mediaBrowser, context, dataSources, sortnodes=True):
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
									context,
									splithandle=splithandle,
									updatehandle=updatehandle,
									refNode=leftmostNode,
									createwireless=sortnodes,
									processmultilayerexr=False
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
	def getUpdatedNodesFeedback(self, updatehandle, calledfromupdate=False):
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
		else:
			if calledfromupdate:
				logger.debug("Showing no updated nodes popup")
				self.core.popup("No nodes were updated.", severity="info")



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
	def fusionUpdateSelectedPasses(self, mediaBrowser, context, sortnodes=True):
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
													comp,
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
														comp,
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

					self.getUpdatedNodesFeedback(updatehandle, calledfromupdate=True)
					return
	
		self.getUpdatedNodesFeedback(updatehandle, calledfromupdate=True)
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
	def updateLoaders(self, comp, Loaderstocheck, filePath, firstFrame, lastFrame, isSequence=False, exrlayers=[]):
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

					self.reloadLoader(comp, loader, filePath, firstFrame, lastFrame)
					if not version1 == version2:
						return loader, version1
				
			return None, ""
		
		except:
			logger.warning("ERROR: Failed to update loaders")
			return None
	

	@err_catcher(name=__name__)
	def processImageImport(self, imageData, context, splithandle=None, updatehandle:list=[], refNode=None, createwireless=True, processmultilayerexr=True):
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
			updatedloader, prevVersion = self.updateLoaders(comp, allLoaders, filePath, firstFrame, lastFrame, isSequence)
		except:
			updatedloader = prevVersion = None

		# If an updated node was produced.
		if updatedloader:
			try:
				# Update Multilayer.
				if extension == ".exr":
					# check for multichannels to update all splitted nodes.
					extraloader = updatedloader
					checkedloaders:list = [updatedloader.Name]
					if len(self.get_loader_channels(updatedloader)) > 0:
						while  extraloader:
							allremainingLoaders = [t for t in allLoaders if not t.Name in checkedloaders]
							extraloader, extraversion = self.updateLoaders(comp, allremainingLoaders, filePath, firstFrame, lastFrame, isSequence)
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
			self.reloadLoader(comp, node, filePath, firstFrame, lastFrame)
			nodeName = layerNm + "_" + aovNm
			node.SetAttrs({"TOOLS_Name": nodeName})

			if refNode:
				if refNode.GetAttrs('TOOLS_RegID') =='Loader':
					Fus.setNodePosition(comp, node, x_offset = 0, y_offset = 1, refNode=refNode)
				else:
					Fus.setNodePosition(comp, node, x_offset = -5, y_offset = 0, refNode=refNode)
			else:
				Fus.setNodePosition(comp, node, x_offset = 0, y_offset = 0, refNode=None)

			comp.Unlock()

		except:
			logger.warning("ERROR: Failed to create loader node.")
			comp.Unlock()
			return
		
		# IF IS EXR
		if extension == ".exr" and processmultilayerexr:
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
						loaders_list = self.process_multichannel(context, node, createwireless=createwireless)
						if len(loaders_list)>0:
							leftMostNode = CompDb.getNodeByUID(comp, loaders_list[-1])
							return leftMostNode
	
					elif splithandle:
						splithandle['splitchosen'] = False
			except:
				logger.warning("ERROR: Failed to process Multilayer EXR")
				return None

		#	Add UUID to Loader
		nodeUID = self.createUUID()
		node.SetData('Prism_UUID', nodeUID)


		#	Add Node Data to Comp Database
		version = version2 if 'version2' in locals() else prevVersion

		nodeData = {"nodeName": nodeName,
					"version": context["version"],
					"filepath": filePath,
					"format": extension,
					"mediaId": context["identifier"],
					"displayName": context["displayName"],
					"connectedNodes": ""}

		CompDb.addNodeToDB(comp, "import2d", nodeUID, nodeData)

		# create wireless
		if createwireless:
			self.createWireless(nodeUID)

		flow.Select(node, True)
		
		return node
	

	@err_catcher(name=__name__)
	def createWireless(self, nodeUID):
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
		tool = CompDb.getNodeByUID(comp, nodeUID)

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

			#	Set UUID's to Wireless Nodes
			wirelessInUID = self.createUUID()
			ad.SetData('Prism_UUID', wirelessInUID)
			wirelessOutUID = self.createUUID()
			wl.SetData('Prism_UUID', wirelessOutUID)

			#	Add Wireless Nodes to Comp Database
			nodeData = CompDb.getNodeInfo(comp, "import2d", nodeUID)
			nodeData["connectedNodes"] = [wirelessInUID, wirelessOutUID]
			CompDb.updateNodeInfo(comp, "import2d", nodeUID, nodeData)

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
		version_pattern = rf"v(\d{{{padding}}})"  # Using f-string for dynamic regex pattern
		master_pattern  = r"(?:\\|\/|_)master(?:\\|\/|_|$)"  # Matches "\master\", "/master/", "_master"
		match = re.search(version_pattern, filepath)

		if match:
			return int(match.group(1))
		
		# Check the full path for any "\master\" or "_master" pattern if no version was found
		master_match = re.search(master_pattern, filepath, re.IGNORECASE)
		if master_match:
			return "master"
		else:
			logger.warning(f"ERROR: Failed to extract version from filepath: {filepath}")
			return None
		

	@err_catcher(name=__name__)
	def are_paths_equal_except_version(self, path1, path2, isSequence):	
		try:
			# Remove the version part from the paths for exact match comparison
			padding = self.core.versionPadding
			version_pattern = rf"v\d{{{padding}}}"
			master_dir_pattern = r'(?<=/|\\)master(?=/|\\)'
			master_file_pattern = r'_master(?=\.)'
			path1_without_version = re.sub(version_pattern, "", path1)
			path2_without_version = re.sub(version_pattern, "", path2)
			path1_version = self.extract_version(path1)
			path2_version = self.extract_version(path2)
			if path1_version and path1_version == "master":
				path1_without_version = re.sub(master_dir_pattern, '', path1)  # Remove "master" from directory path
				path1_without_version = re.sub(master_file_pattern, '_', path1_without_version)  # Remove "master" from filename
			if path2_version and path2_version == "master":
				path2_without_version = re.sub(master_dir_pattern, '', path2)  # Remove "master" from directory path
				path2_without_version = re.sub(master_file_pattern, '_', path2_without_version)  # Remove "master" from filename
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

			for count, nodeUID in enumerate(loaders, start=0):
				ldr = CompDb.getNodeByUID(comp, nodeUID)
				flow.SetPos(ldr, org_x_pos, org_y_pos + y_pos_add * count)
		except:
			logger.warning("ERROR: Failed to move loaders")


	@err_catcher(name=__name__)
	def process_multichannel(self, context, tool, createwireless=True):
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



				#	Add UUID to Loader
				nodeUID = self.createUUID()
				ldr.SetData('Prism_UUID', nodeUID)



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

				loaders_list.append(nodeUID)
			except:
				logger.warning("ERROR: Failed to process multichannel EXR - failed to assign channels")
				return

		self.move_loaders(x_pos, y_pos, loaders_list)

		# create IN and OUT nodes.
		for nodeUID in loaders_list:


			# #	Add Node Data to Comp Database
			# version = version2 if 'version2' in locals() else prevVersion

			nodeData = {#"nodeName": nodeName,
						"version": context["version"],
						"filepath": context["path"],
						"format": context["extension"],
						"mediaId": context["identifier"],
						"displayName": context["displayName"],
						"connectedNodes": ""}

			CompDb.addNodeToDB(comp, "import2d", nodeUID, nodeData)

			# create wireless
			if createwireless:
				self.createWireless(nodeUID)


			flow.Select(CompDb.getNodeByUID(comp, nodeUID), True)

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


	#	TODO LOOK AT COMBINING THESE CALLS

	@err_catcher(name=__name__)
	def importUSD(self, origin, UUID, nodeData, update=False):				#	TODO HANDLE ERRORS
		comp = self.getCurrentComp()
	
		if not update:
			addResult = CompDb.addNodeToDB(comp, "import3d", UUID, nodeData)
			result = Fus3d.importUSD(self, origin, UUID, nodeData)
		
		else:
			CompDb.updateNodeInfo(comp, "import3d", UUID, nodeData)
			result = Fus3d.updateUSD(self, origin, UUID, nodeData)

		return result
	

	@err_catcher(name=__name__)
	def createUsdScene(self, origin, UUID):
		Fus3d.createUsdScene(self, origin, UUID)


	@err_catcher(name=__name__)
	def importFBX(self, origin, UUID, nodeData, update=False):				#	TODO HANDLE ERRORS
		comp = self.getCurrentComp()
	
		if not update:
			addResult = CompDb.addNodeToDB(comp, "import3d", UUID, nodeData)
			result = Fus3d.importFBX(self, origin, UUID, nodeData)
		
		else:
			CompDb.updateNodeInfo(comp, "import3d", UUID, nodeData)
			result = Fus3d.updateFBX(self, origin, UUID, nodeData)

		return result

	
	@err_catcher(name=__name__)
	def createFbxScene(self, origin, UUID):
		Fus3d.createFbxScene(self, origin, UUID)
	

	@err_catcher(name=__name__)
	def importABC(self, origin, UUID, nodeData, update=False):				#	TODO HANDLE ERRORS
		comp = self.getCurrentComp()
	
		if not update:
			addResult = CompDb.addNodeToDB(comp, "import3d", UUID, nodeData)
			result = Fus3d.importABC(self, origin, UUID, nodeData)
		
		else:
			CompDb.updateNodeInfo(comp, "import3d", UUID, nodeData)
			result = Fus3d.updateABC(self, origin, UUID, nodeData)

		return result
		return result
	
	
	@err_catcher(name=__name__)
	def createAbcScene(self, origin, UUID):
		Fus3d.createAbcScene(self, origin, UUID)


	@err_catcher(name=__name__)
	def importBlenderCam(self, origin, importPath, UUID, nodeName, version, update=False):
		# return Fus3d.importFBX(self, origin, importPath, UUID, nodeName, version, update=False)
		pass






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
	#              MEDIA BROWSER MENU              #
	#                                              #
	################################################
	
	@err_catcher(name=__name__)
	def calculate_luminance(self, color:dict):
		r,g,b = color['R'], color['G'], color['B']
		# No need for normalization if RGB values are already in [0, 1]
		luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
		return luminance

	@err_catcher(name=__name__)
	def is_background_bright(self, color:dict, threshold=0.5):
		luminance = self.calculate_luminance(color)
		return luminance > threshold

	@err_catcher(name=__name__)
	def create_color_icon(self, color, diameter=8):
		# Create a QPixmap to draw the circle
		pixmap = QPixmap(diameter, diameter)
		pixmap.fill(QColor("transparent"))  # Transparent background
		
		# Draw the circle
		painter = QPainter(pixmap)
		painter.setRenderHint(QPainter.Antialiasing)
		painter.setBrush(color)
		painter.setPen(QColor("transparent"))  # No border
		painter.drawEllipse(0, 0, diameter, diameter)
		painter.end()
		
		return pixmap
	

	@err_catcher(name=__name__)
	def selecttasknodes(self, nodeUIDs):
		comp = self.getCurrentComp()
		flow = comp.CurrentFrame.FlowView
		# deselect all nodes
		flow.Select()

		toolsToSelectUID = CompDb.getAllConnectedNodes(comp, nodeUIDs)
		
		if not toolsToSelectUID:
			logger.debug("There are not Loaders associated with this task.")
			self.core.popup("There are no loaders for this task.", severity="info")
			return
				
		#	Set the color for each tool
		for toolUID in toolsToSelectUID:
			try:
				if CompDb.nodeExists(comp, toolUID):
					tool = CompDb.getNodeByUID(comp, toolUID)
					flow.Select(tool, True)
			except:
				pass


	@err_catcher(name=__name__)
	def colorTaskNodes(self, nodeUIDs, color, item, category):
		comp = self.getCurrentComp()

		toolsToColorUID = CompDb.getAllConnectedNodes(comp, nodeUIDs)
		
		if not toolsToColorUID:
			logger.debug("There are not Loaders associated with this task.")
			self.core.popup("There are no loaders for this task.", severity="info")
			return
				
		#	If the RGB is the Clear Color code
		if color['R'] == 0.000011 and color['G'] == 0.000011 and color['B'] == 0.000011:
			for toolUID in toolsToColorUID:
				tool = CompDb.getNodeByUID(comp, toolUID)
				tool.TileColor = None

		#	Set the color for each tool
		else:
			for toolUID in toolsToColorUID:
				try:
					if CompDb.nodeExists(comp, toolUID):
						tool = CompDb.getNodeByUID(comp, toolUID)
						tool.TileColor = color
						logger.debug(f"Set color of tool: {CompDb.getNodeNameByUID(comp, toolUID)}")
				except:
					logger.debug(f"Cannot set color of tool: {toolUID}")

		#	Color the Project Browser Task
		self.colorItem(item, color)
		CompDb.addPrismDbIdentifier(comp, category, item.text(0), color)


	@err_catcher(name=__name__)
	def colorItem(self, item, color):
		#	Check if R, G, and B are all 0.000011 to clear the color
		if color['R'] == 0.000011 and color['G'] == 0.000011 and color['B'] == 0.000011:
			item.setBackground(0, QBrush())
			item.setForeground(0, QBrush())
			return

		qcolor = QColor.fromRgbF(color['R'], color['G'], color['B'])
		item.setBackground(0, qcolor)
		item.setForeground(0, QColor(230, 230, 230))
		if self.is_background_bright(color):
			item.setForeground(0, QColor(30, 30, 30))



	################################################
	#                                              #
	#        	       CALLBACKS                   #
	#                                              #
	################################################
	

	@err_catcher(name=__name__)
	def onMediaBrowserTaskUpdate(self, origin, curTask):
		comp = self.getCurrentComp()
		lw = origin.tw_identifier #listwidget
		entity = origin.getCurrentEntity()
		if lw == origin.tw_identifier:
			category = entity.get("type")
			if category in ["asset", "shot"]:
				for i in range(lw.topLevelItemCount()):
					item = lw.topLevelItem(i)
					color = CompDb.getPrismDbIdentifierColor(comp, category, item.text(0))
					if color:
						self.colorItem(item, color)



	@err_catcher(name=__name__)
	def openPBListContextMenu(self, origin, rcmenu, lw, item, path):
		entity = origin.getCurrentEntity()
		if lw == origin.tw_identifier:
			category = entity.get("type")
			if category in ["asset", "shot"]:
				comp = self.getCurrentComp()

				#	Get Display Name from Item
				displayName = item.text(0)

				#	Get NodeUID based on Media Identifier
				mediaNodeUIDs = CompDb.getNodeUidFromMediaDisplayname(comp, "import2d", displayName)

				#	Setup rcl "Select Nodes" items
				depAct = QAction("Select Task Nodes....", origin)
				depAct.triggered.connect(lambda: self.selecttasknodes(mediaNodeUIDs))
				rcmenu.addAction(depAct)

				#	Setup rcl "Color Nodes" items
				menuSelTaskC = QMenu("Select Task Color", origin)
				menuSelTaskC.setStyleSheet("""
					QMenu::item {
						padding-left: 5px;  /* Reduce left padding of item text */
						padding-right: 5px; /* Optional, adjust to control space around icon */
					}
					QMenu::icon {
						margin-right: -5px; /* Bring icon closer to text */
					}
				""")
				for key in self.fusionToolsColorsDict.keys():
					name = key
					color = self.fusionToolsColorsDict[key]

					qcolor = QColor.fromRgbF(color['R'], color['G'], color['B'])
					depAct = QAction(name, origin)

					# we can pass name as a default argument in the lambda to "freeze" its value for each iteration
					# even if the action isn't checkable, the triggered signal passes checked as an argument by default.
					depAct.triggered.connect(lambda checked=False, color=color: self.colorTaskNodes(mediaNodeUIDs, color, item, category))
					icon = self.create_color_icon(qcolor)
					depAct.setIcon(icon)
					menuSelTaskC.addAction(depAct)

				rcmenu.addMenu(menuSelTaskC)


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
		origin.b_createImport.deleteLater()
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
		origin.b_import3d = QPushButton(origin.w_CreateImports)
		origin.b_import3d.setObjectName("b_import3d")
		origin.b_import3d.setText("Import 3d")
		#	Add to the 2nd position of the layout
		origin.horizontalLayout_3.insertWidget(1, origin.b_import3d)
		#	Add connection to button
		origin.b_import3d.clicked.connect(lambda: self.addImport3dState(origin))

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
		if CompDb.sm_readStates(comp) is None:
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

		##	Resize Main Vert Splitter
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


	# @err_catcher(name=__name__)
	# def onStateDeleted(self, origin, stateui):
	# 	comp = self.getCurrentComp()
	# 	if stateui.className == "ImageRender":
	# 		try:
	# 			node = CompDb.get
	# 			node = comp.FindTool(stateui.b_setRendernode.text())
	# 			if node:
	# 				fString = "Do you want to also delete the Saver node\nassociated with this render:"
	# 				buttons = ["Yes", "No"]
	# 				result = self.core.popupQuestion(fString, buttons=buttons, icon=QMessageBox.NoIcon)
	# 				if result == "Yes":
	# 					node.Delete()
	# 					CompDb.removeNodeFromDB(comp, "render2d", )
	# 		except:
	# 			logger.warning(f"ERROR: Unable to remove Saver: {node.Name}")
	# 	# elif stateui.className == "ImportFile":
			

	#	This is for the Import Image button on SM.
	#	Presently just redirects to Project Browser
	@err_catcher(name=__name__)
	def addImportImageState(self, origin):					#	TODO - Add importing through SM functionality.
		title = "Import Image"
		msg = ("Importing Images through the State Manager is not yet supported.\n\n"
				"Please import through the Project Browser Media tab")
		buttons = ["Open Project Browser", "Cancel"]

		#	Execute popup Question
		result = self.core.popupQuestion(msg, buttons=buttons, title=title, icon=QMessageBox.Warning)

		if result == "Open Project Browser":
			#	Opens Project Browser
			try:
				logger.debug("Opening Project Browser")
				origin.core.projectBrowser()
				origin.close()
				#	Switch to Media Tab
				if origin.core.pb:
					origin.core.pb.showTab("Media")
			except:
				logger.warning("ERROR: Unable to Open Project Browser.")



	@err_catcher(name=__name__)
	def addImport3dState(self, origin):
		stateType = "Import"
		import3dStates = []

		curSel = origin.getCurrentItem(origin.activeList)
		if (origin.activeList == origin.tw_import
			and curSel is not None
			and curSel.ui.className == "Folder"
			):
			parent = curSel
		else:
			parent = None

		states = origin.stateTypes
		for state in states:
			import3dStates += getattr(origin.stateTypes[state], "stateCategories", {}).get(stateType, [])

		if len(import3dStates) == 1:
			origin.createState(import3dStates[0]["stateType"], parent=parent, setActive=True)
		else:
			menu = QMenu(origin)
			for importState in import3dStates:
				actSet = QAction(importState["label"], origin)
				actSet.triggered.connect(lambda x=None,
							st=importState: origin.createState(st["stateType"],
							parent=parent,
							setActive=True,
							**st.get("kwargs",{}))
					)
				menu.addAction(actSet)

			# getattr(self.core.appPlugin, "sm_openStateFromNode", lambda x, y, stateType: None)(			#	NOT USED???
			# 	self, menu, stateType=stateType
			# 	)

			if not menu.isEmpty():
				menu.exec_(QCursor.pos())

		origin.activeList.setFocus()


		




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
			print("sd: ", sourceData)

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

	# @err_catcher(name=__name__)
	# def updateTasks(self, *args, **kwargs):
	# 	logger.debug("Loading patched function: 'mediaBrowser.updateTasks'")
	# 	mediabrowser = self.monkeypatchedmediabrowser#self.core.pb.mediaBrowser
	# 	self.core.plugins.callUnpatchedFunction(mediabrowser.updateTasks, *args, **kwargs)
	# 	self.onMediaBrowserTaskUpdate(mediabrowser)


###########################################
#                                         #
################# CLASSES #################
#                                         #
###########################################	

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
