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


import os
import sys
import json
import platform
import re
import math
import glob
import shutil
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
import Libs.Prism_Fusion_lib_Helper as Helper
import Libs.Prism_Fusion_lib_Fus as Fus
import Libs.Prism_Fusion_lib_CompDb as CompDb
import Libs.Prism_Fusion_lib_3d as Fus3d

logger = logging.getLogger(__name__)



class Prism_Fusion_Functions(object):
	def __init__(self, core, plugin):
		self.core = core
		self.plugin = plugin
		self.fusion = bmd.scriptapp("Fusion")
		self.comp = None # This comp is used by the stateManager to avoid overriding the state data on wrong comps

		self.MP_stateManager = None # Reference to the stateManager to be used on the monkeypatched functions.
		self.MP_mediaBrowser = None # Reference to the mediaBrowser to be used on the monkeypatched functions.
		self.MP_mediaPlayer = None # Reference to the mediaPlayer to be used on the monkeypatched functions.
		# self.MP_importState = None # Reference to the importState to be used on the monkeypatched functions.

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
						("getIconPathForFileType", self.getIconPathForFileType),
						("openPBListContextMenu", self.openPBListContextMenu),
						("onMediaBrowserOpen", self.onMediaBrowserOpen),
				]

			# Iterate through the list to register callbacks
			for callback_name, method in callbacks:
				self.core.registerCallback(callback_name, method, plugin=self.plugin)

			logger.debug("Registered callbacks")

		except Exception as e:
			logger.warning(f"ERROR: Failed to register callbacks:\n{e}")
		
		self.importHandlers = {
			".abc": {"importFunction": self.import3dObject},
			".fbx": {"importFunction": self.import3dObject},
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
		
		#	Gets task color settings from the DCC settings
		self.taskColorMode = self.core.getConfig("Fusion", "taskColorMode")
		self.colorBrightness = self.core.getConfig("Fusion", "colorBrightness")
		
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
	def createUUID(self, simple=False, length=8):
		return CompDb.createUUID(simple=False, length=8)


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
	def getFusLegalName(self, origName, check=False):
		return Helper.getFusLegalName(origName, check=check)


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
		comp = self.getCurrentComp()
		comp.Lock()
		self.wrapped_CaptureViewportThumbnail(comp)
		comp.Unlock()


	@err_catcher(name=__name__)
	def wrapped_CaptureViewportThumbnail(self, comp):
		#   Make temp dir and file
		tempDir = os.path.join(self.pluginDirectory, "Temp")
		if not os.path.exists(tempDir):
			os.mkdir(tempDir)
		thumbPath = os.path.join(tempDir, "FusionThumb.jpg")
		thumbName = os.path.basename(thumbPath).split('.')[0]

		#   Get Fusion API stuff
		if not comp:
			comp = self.getCurrentComp()

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

		if thumbSaver:
			try:
				thumbSaver.Delete()
			except:
				pass

		#   Restore pass-through state of orig savers
		self.origSaverStates("load", comp, origSaverList)

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
		# saverList = self.getSaverList(comp)
		saverList = Fus.getAllToolsByType(comp, "Saver")
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
			if Fus.getNodeType(tool) == "Saver":
				return True
			else:
				return False
		except:
			return False
	

	#	Returns Fusion-legal Saver name base on State name
	@err_catcher(name=__name__)
	def getRendernodeName(self, stateName):
		legalName = Helper.getFusLegalName(stateName)
		nodeName = f"PrSAVER_{legalName}"

		return nodeName
	
	
	#	Creates Saver with UUID associated with ImageRender state
	@err_catcher(name=__name__)
	def createRendernode(self, nodeUID, nodeData):
		comp = self.getCurrentComp()
		comp.Lock()
		comp.StartUndo("Create Render Node")

		self.wrapped_createRendernode(nodeUID, nodeData, comp=comp)

		comp.EndUndo()
		comp.Unlock()		
	

	@err_catcher(name=__name__)
	def wrapped_createRendernode(self, nodeUID, nodeData, comp):
		if not comp:
			comp = self.getCurrentComp()
		if self.sm_checkCorrectComp(comp):
			if not CompDb.nodeExists(comp, nodeUID):

				#	Add Saver to Comp
				sv = Fus.addTool(comp, "Saver", nodeData)

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
		comp.Lock()
		comp.StartUndo("Update Render Node")

		self.wrapped_updateRendernode(nodeUID, nodeData, comp)	

		comp.EndUndo()
		comp.Unlock()


	@err_catcher(name=__name__)
	def wrapped_updateRendernode(self, nodeUID, nodeData, comp):
		if self.sm_checkCorrectComp(comp):
			sv = CompDb.getNodeByUID(comp, nodeUID)

			if sv:
				#	Update Saver Info
				Fus.updateTool(sv, nodeData)

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
	#                 IMPORTIMAGES                 #
	#                                              #
	################################################

	@err_catcher(name=__name__)
	def importImages(self, mediaBrowser):
		comp = self.getCurrentComp()
		comp.Lock()
		comp.StartUndo("Import Media")

		self.wrapped_ImportImages(mediaBrowser, comp)

		comp.EndUndo()
		comp.Unlock()


	@err_catcher(name=__name__)
	def wrapped_ImportImages(self, mediaBrowser, comp):
		try:
			#	This is to cover that Prism's MediaBrowser.py call to this importImages passes
			# 	the mediaPlayer object under the name mediaBrowser 
			self.MP_mediaPlayer = mediaPlayer = mediaBrowser

			self.core.plugins.monkeyPatch(mediaBrowser.compGetImportSource, self.compGetImportSource, self, force=True)
			self.core.plugins.monkeyPatch(mediaBrowser.compGetImportPasses, self.compGetImportPasses, self, force=True)
			logger.debug("Patched functions in 'importImages()'")

		except Exception as e:
			logger.warning(f"ERROR: Unable to load patched functions:\n{e}")
		
		if not comp:
			comp = self.getCurrentComp()
		
		try:
			#	Get Identifier Context Data
			contextRaw = mediaPlayer.getSelectedContexts()

			#	Seems sometimes context comes as a list
			if isinstance(contextRaw, list):
				context = contextRaw[0] if len(contextRaw) > 0 else None
			else:
				context = contextRaw

			#	Get AOV Contexts - empty list if 2drender
			version = self.core.pb.mediaBrowser.getCurrentVersion()
			aovDict = self.core.mediaProducts.getAOVsFromVersion(version)

		except Exception as e:
			logger.warning(f"ERROR:  Import Failed - Unable to get image context data:\n{e}.")
			self.core.popup(f"ERROR:  Import Failed - Unable to get image context data:\n{e}.")
			return

		try:
			#	Get sourceData based on mediaType - used to get framerange
			if "aov" in context:
				sourceData = mediaPlayer.compGetImportPasses()
			else:
				sourceData = mediaPlayer.compGetImportSource()


		###		TODO	Framerange in sourceData does not seem to update until Prism instance restarts		TODO
						#	This means the framerange will not update using Update Images
						#	Needs furter investigation

		except Exception as e:
			logger.warning(f"ERROR:  Import Failed - Unable to get image source data:\n{e}.")
			self.core.popup(f"ERROR:  Import Failed - Unable to get image source data:\n{e}.")
			return

		#	Function to aggregate data into importData
		importData = Helper.makeImportData(self, context, aovDict, sourceData)

		if not importData:
			logger.warning(f"ERROR:  Import Failed - Unable to make import data:\n{e}.")
			self.core.popup(f"ERROR:  Import Failed - Unable to make import data:\n{e}.")
			return

		#	Get "Sorting" checkbox state	
		sorting = Fus.sortingEnabled(comp)

		# Setup Dialog
		fString = "Please select an import option:"	

		#	Checks for AOVs or Channels
		hasAovs = bool(importData.get("aov") and len(importData.get("aovs", [])) > 1)
		hasChannels = bool(importData.get("channel") and len(importData.get("channels", [])) > 1)

		#	Adds buttons
		if hasAovs:
			buttons = ["Current AOV", "All AOVs"]
		else:
			buttons = ["Import Media"]

		if hasAovs or hasChannels:
			buttons.append("Update Selected")
		else:
			buttons.append("Update Version")

		buttons.append("Cancel")
			
		#	Execute question popup
		importType, checkbox_checked = self.importPopup(fString, buttons=buttons, icon=QMessageBox.NoIcon, checked=sorting)

		#	Save "Sorting" checkbox state
		if checkbox_checked is not None:
			Fus.sortingEnabled(comp, save=True, checked=checkbox_checked)

		#	Call the import with options and passing the data
		if importType in ["Import Media", "Current AOV", "All AOVs"]:
			#	Get any UIDs for the Identifier
			uids = CompDb.getUIDsFromImportData(comp, "import2d", importData)

			#	If there are already UIDs in the comp
			if uids and len(uids) > 0:
				self.importExisting(comp, uids, importData, importType, checkbox_checked)

			#	Import the image(s)
			else:
				self.configureImport(comp, importData, importType, sortnodes=not checkbox_checked)

		#	Update Option
		elif importType in ["Update Selected", "Update Version"]:
			#	Call the update
			self.updateImport(comp, importType, importData)

		#	Cancel Option
		else:
			logger.debug("Import Canceled")
			return
		

	@err_catcher(name=__name__)
	def importExisting(self, comp, uids, importData, importType, checkbox_checked):
		#	Get node info
		versions = []
		for uid in uids:
			tData = CompDb. getNodeInfo(comp, "import2d", uid)
			identifier = tData["mediaId"]
			versions.append(tData["version"])
		
		#	Takes the brackets out if there is only one item
		if len(versions) == 1:
			versions = versions[0]

		#	Popup question
		fString = (f"There is already ({versions}) of ({identifier}) the Comp:\n\n"
					"Would you like to:\n" 
					"       Update the version\n"
					"           or\n"
					"       Import this version?")
		buttons = ["Update", "Import", "Cancel"]

		result = self.core.popupQuestion(fString, buttons=buttons, icon=QMessageBox.NoIcon)

		#	Re-configure import type for update
		if result == "Update":
			if importType == "Import Media":
				importType = "Update Version"
			elif importType == "Current AOV":
				importType = "Update Current"
			elif importType == "All AOVs":
				importType = "Update All"
				
			#	Call update function
			self.updateImport(comp, importType, importData)

		#	Import as normal
		elif result == "Import":
			self.configureImport(comp, importData, importType, sortnodes=not checkbox_checked)

		else:
			logger.debug("Import Canceled")
			return


	@err_catcher(name=__name__)
	def configureImport(self, comp, importData, importType, sortnodes=True):
		flow = comp.CurrentFrame.FlowView

		#	Finds the left edge of the flow-nodes
		refNode = None
		leftmostNode = Fus.findLeftmostLowerNode(comp, 0.5)
		if sortnodes:
			if leftmostNode:
				refNode = leftmostNode

		importList = []

		try:
			#	For Current AOV
			if importType == "Current AOV":
				for importItem in importData["files"]:
					if importItem["aov"] == importData["aov"]:
						importList.append(importItem)
						break

			#	For all AOVs or single item
			else:
				for importItem in importData["files"]:
					importList.append(importItem)

		except Exception as e:
			logger.warning(f"ERROR: Unable to generate import item list:\n{e}")
			self.core.popup(f"ERROR: Unable to generate import item list:\n{e}")
			return

		try:

			#	For each import item
			for importItem in importList:

				# Deselect all nodes
				flow.Select()

				#	Make UUID
				toolUID = CompDb.createUUID()

				#	Make dict
				toolData = {"nodeName": Helper.makeLdrName(importItem),
							"version": importData["version"],
							"toolUID": toolUID,
							"mediaId": importData["identifier"],
							"displayName": importData["displayName"],
							"mediaType": importData["mediaType"],
							"aov": importItem.get("aov", ""),
							"filepath": importItem["basefile"],
							"extension": importData["extension"],
							"fuseFormat": self.getFuseFormat(importData["extension"]),
							"frame_start": importItem["frame_start"],
							"frame_end": importItem["frame_end"]
							}

				try:
					#	Get channels from image file
					channels = self.core.media.getLayersFromFile(importItem["basefile"])
				except:
					logger.warning("ERROR:  Unable to resolve image file channels")
					return

				#	If no channels or single channel call addSingle
				if len(channels) <= 1:
					leftmostNode = self.addSingleChannel(comp, toolUID, toolData, refNode, sortnodes)

				#	If multiple channels exists display popup to split
				else:
					fString = "This EXR seems to have multiple channels:\n" + "Do you want to split the EXR channels into individual nodes?"
					buttons = ["Yes", "No"]
					result = self.core.popupQuestion(fString, buttons=buttons, icon=QMessageBox.NoIcon)

					if result == "Yes":
						#	Call Multi-channel function for all channels
						leftmostNode = self.addMultiChannel(comp, toolData, channels, sortnodes=sortnodes)

					if result == "No":
						#	Get current viewed channel
						currChannel = importData["channel"]
						#	Call Multi-channel function for current channel
						leftmostNode = self.addMultiChannel(comp, toolData, channels, currChannel, sortnodes=sortnodes)


			#	Return if add image returns None
			if not leftmostNode:
				return

			Fus.sortLoaders(comp, leftmostNode, reconnectIn=True, sortnodes=sortnodes)


			logger.debug(f"Imported  {importData['identifier']}")

		except Exception as e:
			logger.warning(f"ERROR:  Unable to import Images:\n{e}")
			self.core.popup(f"ERROR:  Unable to import Images:\n{e}")


	@err_catcher(name=__name__)
	def addSingleChannel(self, comp, toolUID, toolData, refNode, sortnodes=True):
		flow = comp.CurrentFrame.FlowView

		#	Finds the left edge of the flow-nodes
		refNode = None
		leftmostNode = Fus.findLeftmostLowerNode(comp, 0.5)
		if sortnodes:
			if leftmostNode:
				refNode = leftmostNode

		try:
			#	Add and configure Loader
			ldr = Fus.addTool(comp, "Loader", toolData)
		
			if not ldr:
				self.core.popup(f"ERROR: Unable to add Loader to Comp")
				return

			#	Add mode to Comp Database
			CompDb.addNodeToDB(comp, "import2d", toolUID, toolData)
		except:
			logger.warning(f"ERROR: Unable to Import Single Channel")
			return None

		#	Deselect all
		flow.Select()

		# #	If sorting is enabled
		if sortnodes:
			if not leftmostNode:
				leftmostNode = ldr

		Fus.setNodeToLeft(comp, ldr, refNode)

		# #	If sorting is enabled
		if sortnodes:
			self.createWireless(toolUID)
			
		return ldr


	@err_catcher(name=__name__)
	def addMultiChannel(self, comp, toolData, channels, currChannel=None, sortnodes=True):
		flow = comp.CurrentFrame.FlowView

		#	Finds the left edge of the flow-nodes
		refNode = None
		leftmostNode = Fus.findLeftmostLowerNode(comp, 0.5)
		if sortnodes:
			if leftmostNode:
				refNode = leftmostNode

		#	If not splitting, use currently viewed channel
		if currChannel:
			channelList = [currChannel]
		#	Use all channels
		else:
			channelList = channels

		for channel in channelList:
			#	Deselect all
			flow.Select()

			#	Make copy to edit for each channel
			toolData_copy = toolData.copy()

			toolUID = CompDb.createUUID()

			#	Edit dict copy
			toolData_copy["toolUID"] = toolUID
			toolData_copy["channel"] = channel
			toolData_copy["nodeName"] = Helper.makeLdrName(toolData_copy)
			
			#	Add Loader with config data
			ldr = Fus.addTool(comp, "Loader", toolData_copy)

			#	Add node to Comp Database
			CompDb.addNodeToDB(comp, "import2d", toolUID, toolData_copy)

			try:
				#	Get available channels from Loader
				loaderChannels = Fus.getLoaderChannels(ldr)
				channelData = Fus.getChannelData(loaderChannels)
			except Exception as e:
				logger.warning(f"ERROR: Unable to get channels from Loader:\n{e}")
				return None

			#	Get the channel list for the channel being processed
			channelDict = channelData[channel]

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


			# Check if contains only a Z-channel (for Depth, Mist, etc)
			try:
				z_channel = None
				for channel_str in channelDict:
					if re.search(r'\.z$', channel_str.lower()):
						z_channel = channel_str

				#	Assign the Z-channel to the R, G, B, and Z
				if z_channel and len(channelDict) == 1:
					ldr.Clip1.OpenEXRFormat.RedName = z_channel
					ldr.Clip1.OpenEXRFormat.GreenName = z_channel
					ldr.Clip1.OpenEXRFormat.BlueName = z_channel
					ldr.Clip1.OpenEXRFormat.ZName = z_channel
			except:
				logger.warning("ERROR: Unable to assign image Z-channel to Loader")
				return None

			else:
				try:
					#	Match the attrs based on the dict						#	TODO make sure this works for all DCC channel types
					for channel_str in channelDict:
						match = re.search(r'\.([a-z])$', channel_str.lower())

						if match:
							suffix = match.group(1)
							attribute = channel_attributes.get(suffix)

							#	Configure Loader channels based on dict
							if attribute:
								setattr(ldr.Clip1.OpenEXRFormat, attribute, channel_str)
				except:
					logger.warning("ERROR: Unable to assign image channels to Loader")
					return None

			#	Deselect all
			flow.Select()

			#	If sorting is enabled
			if sortnodes:
				if not leftmostNode:
					leftmostNode = ldr

			Fus.setNodeToLeft(comp, ldr, refNode)

			#	If sorting is enabled
			if sortnodes:
				self.createWireless(toolUID)

		return ldr
			

	@err_catcher(name=__name__)
	def updateImport(self, comp, importType, importData):
		#	Just pass the import list as it should just be one file
		if importType == "Update Version":
			selUIDs = CompDb.getUIDsFromImportData(comp, "import2d", importData)

		#	Handle selected updates
		elif importType == "Update Selected":
			#	Get selected Loaders
			selTools = Fus.getSelectedTools(comp, "Loader")
			if len(selTools) < 1:
				logger.debug("No Loaders selected in the Comp")
				self.core.popup("No Loaders selected in the Comp")
				return
						
			#	Convert selected Tools list to UUID's
			selUIDs_all = []
			for tool in selTools:
				selUIDs_all.append(CompDb.getNodeUidFromTool(tool))

			#	Get selected Media Identifier
			selMediaId = importData["identifier"]
			selUIDs = []
			#	Iterate through UIDS and match only ones for Media ID
			for uid in selUIDs_all:
				tdata = CompDb.getNodeInfo(comp, "import2d", uid)
				if tdata["mediaId"] == selMediaId:
					selUIDs.append(uid)

		#	Update all MediaId Loaders (from Import button)
		elif importType == "Update All":
			#	Remove keys to force all Loaders
			if "aov" in importData:
				del importData["aov"]
			if "channel" in importData:
				del importData["channel"]
			
			selUIDs = CompDb.getUIDsFromImportData(comp, "import2d", importData)

		#	Update the current AOV/pass (from Import button)
		elif importType == "Update Current":
			selUIDs = CompDb.getUIDsFromImportData(comp, "import2d", importData)

		#	Get file list from importData
		fileList = importData["files"]

		#	If there are no nodes for the Media ID in the comp
		if not selUIDs or len(selUIDs) < 1:
			logger.warning(f"ERROR: There are no Loaders for ({importData['identifier']}) in the Comp")
			self.core.popup(f"There are no Loaders for ({importData['identifier']}) in the Comp")
			return False
		
		updateMsgList = []
	
		#	Iterate through update items
		for uid in selUIDs:
			try:
				#	Get original node data from database
				origNodeData = CompDb.getNodeInfo(comp, "import2d", uid)

				#	Get matching file data from file list based on AOV
				updateFileData = Helper.getFileDataFromAOV(fileList, origNodeData["aov"])

				#	Skip to next item if no result
				if not updateFileData:
					continue
				
				#	Make copy of original data
				updateData = origNodeData.copy()
				#	Update data with new values
				updateData["version"] = updateFileData["version"]
				updateData["filepath"] = updateFileData["basefile"]
				updateData["frame_start"] = updateFileData["frame_start"]
				updateData["frame_end"] = updateFileData["frame_end"]

				#	Compare versions and get result and result string
				compareRes, compareMsg = CompDb.compareVersions(origNodeData, updateData)

				#	Add message to message list
				updateMsgList.append(compareMsg)

				#	If there was a match to the database
				if compareRes:
					#	Make dict
					toolData = {"nodeName": Helper.makeLdrName(updateData),
								"version": updateData["version"],
								"filepath": updateData["filepath"],
								"frame_start": updateData["frame_start"],
								"frame_end": updateData["frame_end"]
								}

					#	Get original Loader
					ldr = CompDb.getNodeByUID(comp, uid)
					#	Update Loader config
					Fus.updateTool(ldr, toolData)
					#	Update Database record
					CompDb.updateNodeInfo(comp, "import2d", uid, toolData)
					
			except Exception as e:
				logger.warning(f"ERROR: Unable to update {importData['identifier']}")
				return

		#	Show update feedback
		if len(updateMsgList) == 0:
			formattedMsg = [["", f"No Selected Loaders for '{importData['identifier']}'"]]
		else:
			#	Sort message items
			formattedMsg = sorted(updateMsgList)

		#	Show popup
		self.updateMsgPopup(formattedMsg)


	@err_catcher(name=__name__)
	def createWireless(self, nodeUID):							#	TODO  Look into adding wireless with "addTool"
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
				node.SetData("isprismnode", True)	#	TODO

			ad.ConnectInput('Input', tool)

			#	Set UUID's to Wireless Nodes
			wirelessInUID = CompDb.createUUID()
			ad.SetData('Prism_UUID', wirelessInUID)
			wirelessOutUID = CompDb.createUUID()
			wl.SetData('Prism_UUID', wirelessOutUID)

			#	Add Wireless Nodes to Comp Database
			nodeData = CompDb.getNodeInfo(comp, "import2d", nodeUID)
			nodeData["connectedNodes"] = [wirelessInUID, wirelessOutUID]
			CompDb.updateNodeInfo(comp, "import2d", nodeUID, nodeData)

			#	Select the wireless out
			flow.Select()
			comp.SetActiveTool(wl)

			logger.debug(f"Created Wireless nodes for: {tool.Name}")

		except Exception as e:
			logger.warning(f"ERROR:  Could not add wireless nodes:\n{e}")





	################################################
	#                                              #
	#                   IMPORT3D                   #
	#                                              #
	################################################


	#	Imports or updates USD scene or object
	@err_catcher(name=__name__)
	def importUSD(self, origin, UUID, nodeData, update=False):
		comp = self.getCurrentComp()
		comp.Lock()
		comp.StartUndo("Import USD")

		result = self.wrapped_importUSD(origin, UUID, nodeData, update)

		comp.EndUndo()
		comp.Unlock()

		return result


	#	Imports or updates USD scene or object
	@err_catcher(name=__name__)
	def wrapped_importUSD(self, origin, UUID, nodeData, update=False):
		comp = self.getCurrentComp()
		importRes = False

		#	Add new uLoader
		if not update:
			try:
				#	Add tool
				uLdr = Fus.addTool(comp, "uLoader", nodeData)

				logger.debug(f"Imported USD object: {nodeData['product']}")

			except Exception as e:
				logger.warning(f"ERROR: Unable to import USD object:\n{e}")
				return {"result": False, "doImport": False}
			
			if uLdr:
				#	Add to Comp Database
				addResult = CompDb.addNodeToDB(comp, "import3d", UUID, nodeData)
				importRes = True
		
		#	Update uLoader
		else:
			try:
				#	Get tool
				tool = CompDb.getNodeByUID(comp, UUID)
				#	 Update tool data
				uLdr = Fus.updateTool(tool, nodeData)

				logger.debug(f"Updated uLoader: {nodeData['nodeName']}")
				importRes = True

			except Exception as e:
				logger.warning(f"ERROR: Failed to update uLoader:\n{e}")

			if uLdr:
				#	Update Comp DB record
				CompDb.updateNodeInfo(comp, "import3d", UUID, nodeData)
				importRes = True


		return {"result": importRes, "doImport": importRes}
	

	#	Creates simple USD scene - adds uMerge and uRender to uLoader
	@err_catcher(name=__name__)
	def createUsdScene(self, origin, UUID):
		comp = self.getCurrentComp()
		comp.Lock()
		comp.StartUndo("Create USD Scene")

		self.wrapped_createUsdScene(origin, UUID, comp)

		comp.EndUndo()
		comp.Unlock()


	@err_catcher(name=__name__)
	def wrapped_createUsdScene(self, origin, UUID, comp):
		try:
			Fus3d.createUsdScene(self, origin, UUID)
			logger.debug(f"Created USD Scene for {UUID}")

		except Exception as e:
			logger.warning(f"ERROR: Unable to create USD scene:\n{e}")


	#	Imports .fbx or .abc object into Comp	
	@err_catcher(name=__name__)
	def import3dObject(self, origin, UUID, nodeData, update=False):
		comp = self.getCurrentComp()
		comp.Lock()
		comp.StartUndo("Import 3D Object")	

		result = self.wrapped_import3dObject(origin, UUID, nodeData, comp=comp, update=update)

		comp.EndUndo()
		comp.Unlock()

		return result


	@err_catcher(name=__name__)
	def wrapped_import3dObject(self, origin, UUID, nodeData, comp, update=False):
		importRes = False

		format = nodeData["format"]

		#	Add new 3d Loader
		if not update:
			try:
				#	Add tooltype based on format
				if format == ".fbx":
					ldr3d = Fus.addTool(comp, "SurfaceFBXMesh", nodeData)

				elif format == ".abc":
					ldr3d = Fus.addTool(comp, "SurfaceAlembicMesh", nodeData)
				
				else:
					logger.warning(f"ERROR:  Format not supported: {format}")

				logger.debug(f"Imported 3d object: {nodeData['product']}")

			except Exception as e:
				logger.warning(f"ERROR: Unable to import 3d object:\n{e}")
				return {"result": False, "doImport": False}
			
			if ldr3d:
				#	Add to Comp Database
				addResult = CompDb.addNodeToDB(comp, "import3d", UUID, nodeData)
				importRes = True
		
		#	Update 3d Loader
		else:
			try:
				#	Get tool
				tool = CompDb.getNodeByUID(comp, UUID)
				#	 Update tool data
				ldr3d = Fus.updateTool(tool, nodeData)

				logger.debug(f"Updated Loader3d: {nodeData['nodeName']}")
				importRes = True

			except Exception as e:
				logger.warning(f"ERROR: Failed to update Loader3d:\n{e}")

			if ldr3d:
				#	Update Comp DB record
				CompDb.updateNodeInfo(comp, "import3d", UUID, nodeData)
				importRes = True


		return {"result": importRes, "doImport": importRes}


	#	Creates simple 3d scene - adds merge3d and render3d
	@err_catcher(name=__name__)
	def create3dScene(self, origin, UUID):
		comp = self.getCurrentComp()
		comp.Lock()
		comp.StartUndo("Create 3D Scene")	

		self.wrapped_create3dScene(origin, UUID)

		comp.EndUndo()
		comp.Unlock()

	
	#	Creates simple 3d scene - adds merge3d and render3d
	@err_catcher(name=__name__)
	def wrapped_create3dScene(self, origin, UUID):
		try:
			Fus3d.create3dScene(self, origin, UUID)
			logger.debug(f"Created 3d Scene for {UUID}")

		except Exception as e:
			logger.warning(f"ERROR: Unable to create 3d scene:\n{e}")
	

	@err_catcher(name=__name__)
	def importBlenderCam(self, origin, importPath, UUID, nodeName, version, update=False):
		# return Fus3d.importFBX(self, origin, importPath, UUID, nodeName, version, update=False)
		pass




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
	# 	for tool in iotools:
	# 		filepath = tool.GetAttrs("TOOLST_Clip_Name")[1]
	# 		pathinfo = self.getReplacedPaths(comp, filepath)
	# 		newpath = pathinfo["path"]
	# 		if newpath:
	# 			tool.Clip = newpath			
	# 			pathdata.append({"node": tool.Name, "path":pathinfo["path"], "valid":pathinfo["valid"], "net":pathinfo["net"]})

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

			stateData["comment"] = self.MP_stateManager.publishComment
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
		comp.Lock()

		result = self.wrapped_render_startLocalGroupRender(origin, rSettings, comp)

		comp.Unlock()

		return result


	@err_catcher(name=__name__)
	def wrapped_render_startLocalGroupRender(self, origin, rSettings, comp):
		#	Return if the Comps do not match
		if not self.sm_checkCorrectComp(comp):
			return False

		try:

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
			pass

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

		details["version"] = CompDb.createUUID(simple=True)
		details["sourceScene"] = self.tempFilePath
		details["identifier"] = rSettings["groupName"]
		details["comment"] = self.MP_stateManager.publishComment

		self.className = "RenderGroup"

		return details


	#	Submits the temp comp file to the Farm plugin for rendering
	@err_catcher(name=__name__)
	def sm_render_startFarmGroupRender(self, origin, farmPlugin, rSettings):
		comp = self.getCurrentComp()
		comp.Lock()

		result = self.wrapped_render_startFarmGroupRender(origin, farmPlugin, rSettings, comp)		

		comp.Unlock()

		return result


	@err_catcher(name=__name__)
	def wrapped_render_startFarmGroupRender(self, origin, farmPlugin, rSettings, comp):
		#	Makes global for later use in versioninfo creation and master update
		self.rSettings = rSettings

		#	Return if the Comps do not match
		if not self.sm_checkCorrectComp(comp):
			return False
		
		try:

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
			dlParams["jobInfos"]["Comment"] = self.MP_stateManager.publishComment
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
	

	#	Creates colored icons for rcl task color menu
	@err_catcher(name=__name__)
	def create_color_icon(self, color, diameter=8):
		try:
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
		except:
			logger.warning("ERROR: Unable to create task color icon")
			return None
	

	#	Selects desired tools in Comp
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


	#	Colors tools in Comp based on Color mode in DCC settings
	@err_catcher(name=__name__)
	def colorTaskNodes(self, nodeUIDs, color, item, category):
		comp = self.getCurrentComp()

		#	Colors the Loaders and wireless nodes
		if self.taskColorMode == "All Nodes":
			toolsToColorUID = CompDb.getAllConnectedNodes(comp, nodeUIDs)

		#	Only colors the Loader nodes
		elif self.taskColorMode == "Loader Nodes":
        #   Handle single or multiple nodeUIDs
			toolsToColorUID = nodeUIDs if isinstance(nodeUIDs, list) else [nodeUIDs]

		#	Coloring is disabled
		else:
			return
		
		#	Color the Project Browser Task
		self.colorItem(item, color)
		CompDb.addPrismDbIdentifier(comp, category, item.text(0), color)
		
		if not toolsToColorUID:
			logger.debug("There are not Loaders associated with this task.")
			self.core.popup("There are no loaders for this task.", severity="info")
			return
				
		#	If the RGB is the Clear Color code
		if color['R'] == 0.000011 and color['G'] == 0.000011 and color['B'] == 0.000011:
			for toolUID in toolsToColorUID:
				try:
					tool = CompDb.getNodeByUID(comp, toolUID)
					if tool:
						tool.TileColor = None
				except:
					logger.warning(f"ERROR: Unable to clear the color of the Loader: {toolUID}.")

		#	Set the color for each tool
		else:
			for toolUID in toolsToColorUID:
				try:
					if CompDb.nodeExists(comp, toolUID):
						tool = CompDb.getNodeByUID(comp, toolUID)
						if tool:
							tool.TileColor = color
							logger.debug(f"Set color of tool: {CompDb.getNodeNameByUID(comp, toolUID)}")
				except:
					logger.warning(f"ERROR: Cannot set color of tool: {toolUID}")



	#	Colors Media Task based on Color mode in DCC settings
	@err_catcher(name=__name__)
	def colorItem(self, item, color):
		#	Check if R, G, and B are all 0.000011 to clear the color
		if color['R'] == 0.000011 and color['G'] == 0.000011 and color['B'] == 0.000011:
			item.setBackground(0, QBrush())
			item.setForeground(0, QBrush())
			return
		
		#	Convert brightness percent (e.g., "75%") to an integer alpha value (0–255)
		try:
			percentage = int(self.colorBrightness.strip('%'))
			alpha = int((percentage / 100) * 255)
		except ValueError:
			alpha = 75  # Default alpha if conversion fails

		qcolor = QColor.fromRgbF(color['R'], color['G'], color['B'])

		#	Adding Alpha to mute task coloring
		qcolor.setAlpha(alpha)

		item.setBackground(0, qcolor)
		item.setForeground(0, QColor(230, 230, 230))

		#	If brightness is high, use luminance checker
		if alpha > 124:
			if Helper.isBgBright(color):
				item.setForeground(0, QColor(30, 30, 30))



	################################################
	#                                              #
	#        	       CALLBACKS                   #
	#                                              #
	################################################
	

	@err_catcher(name=__name__)
	def onMediaBrowserTaskUpdate(self, origin):
		#	If DCC 'Task Node Coloring' is disabled
		if self.taskColorMode == "Disabled":
			return
		
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
		#	If DCC 'Task Node Coloring' is disabled
		if self.taskColorMode == "Disabled":
			return
		
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


	#	This is to be able to call task coloring
	@err_catcher(name=__name__)
	def onMediaBrowserOpen(self, origin):
		self.MP_mediaBrowser = origin
		self.core.plugins.monkeyPatch(origin.updateTasks, self.updateTasks, self, force=True)


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
		origin.b_importImage.clicked.connect(lambda: self.addImportState(origin, "Import2d"))

		#	Create Import 3d buton
		origin.b_import3d = QPushButton(origin.w_CreateImports)
		origin.b_import3d.setObjectName("b_import3d")
		origin.b_import3d.setText("Import 3d")
		#	Add to the 2nd position of the layout
		origin.horizontalLayout_3.insertWidget(1, origin.b_import3d)
		#	Add connection to button
		origin.b_import3d.clicked.connect(lambda: self.addImportState(origin, "Import3d"))

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

		self.MP_stateManager = origin
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
			

	#	This is called from the import buttons in the SM (Import Image and Import 3D)
	@err_catcher(name=__name__)
	def addImportState(self, origin, stateType, filepath=None):				#	TODO IMPLEMENT ADDING IMAGE IMPORT STATE TO SM WITH FILEPATH
		importStates = []

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
			importStates += getattr(origin.stateTypes[state], "stateCategories", {}).get(stateType, [])

		if len(importStates) == 1:
			origin.createState(importStates[0]["stateType"], parent=parent, setActive=True)
		else:
			menu = QMenu(origin)
			for importState in importStates:
				actSet = QAction(importState["label"], origin)
				actSet.triggered.connect(lambda x=None,
							st=importState: origin.createState(st["stateType"],
							parent=parent,
							setActive=True,
							**st.get("kwargs",{}))
					)



				menu.addAction(actSet)

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
	def importPopup(self, text, title=None, buttons=None, icon=None, parent=None, checked=False):
		title = title or "Prism"
		buttons = buttons or ["Yes", "No"]
		parent = parent or getattr(self.core, "messageParent", None)

		dialog = ImageImportDialogue(text, title, buttons, parent)
		dialog.checkbox.setChecked(checked)
		result = dialog.exec_()

		# Check if dialog was accepted or rejected
		if result == QDialog.Accepted:
			# Return the clicked button text and the checkbox state
			return dialog.clicked_button_text, dialog.checkbox_checked
		else:
			# Handle the "X" case: Return None or default values
			return None, dialog.checkbox.isChecked()
		

	@err_catcher(name=__name__)
	def updateMsgPopup(self, updateMsgList, parent=None):
		parent = parent or getattr(self.core, "messageParent", None)

		dialog = UpdateDialog(updateMsgList, parent)
		dialog.exec_()


		
	################################################
	#                                              #
	#        	 MONKEYPATCHED FUNCTIONS           #
	#                                              #
	################################################

	#Right click menu from nodes on state manager to get previous versions.
	@err_catcher(name=__name__)
	def rclTree(self, pos, activeList):
		logger.debug("Loading patched function: 'rclTree'")

		sm = self.MP_stateManager
		if sm:			
			rcmenu = QMenu(sm)

            # we check if the rclick is over a state
			idx = sm.activeList.indexAt(pos)
			parentState = sm.activeList.itemFromIndex(idx)
			if parentState:
				sm.rClickedItem = parentState

				# if parentState.ui.className == "ImportFile":
				# 	self.MP_importState = parentState.ui
				# 	self.core.plugins.monkeyPatch(parentState.ui.preDelete, self.preDelete, self, force=True)

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


	# @err_catcher(name=__name__)
	# def preDelete(
	# 	self,
	# 	item=None,
	# 	baseText="Do you also want to delete the connected objects?\n\n",
	# 	):
		
	# 	logger.debug("Loading patched function: 'preDelete'")

	# 	state = self.MP_importState
	# 	if len(state.nodes) <= 0 or state.stateMode == "ApplyCache":
	# 		return
	# 	message = baseText
	# 	validNodes = [
	# 		x for x in state.nodes if self.core.appPlugin.isNodeValid(state, x)
	# 	]
	# 	if validNodes:
	# 		for idx, val in enumerate(validNodes):
	# 			if idx > 5:
	# 				message += "..."
	# 				break
	# 			else:
	# 				message += self.core.appPlugin.getObjectNodeNameByTool(state, val) + "\n"

	# 		if not self.core.uiAvailable:
	# 			action = 0
	# 			print("delete objects:\n\n%s" % message)											#	TODO
	# 		else:
	# 			msg = QMessageBox(
	# 				QMessageBox.Question, "Delete state", message, QMessageBox.No
	# 			)
	# 			msg.addButton("Yes", QMessageBox.YesRole)
	# 			msg.setParent(self.core.messageParent, Qt.Window)
	# 			action = msg.exec_()
	# 			clicked_button = msg.clickedButton()
	# 			result = clicked_button.text()
	# 		# if action == 2:
	# 		if result == "Yes":
	# 			self.core.appPlugin.deleteNodes(state, validNodes)


	#	These two functions edited take into account the dynamic padding,
	# 	and to use the patched Media Player.
	@err_catcher(name=__name__)
	def compGetImportSource(self):
		logger.debug("Loading patched function: 'compGetImportSource'")

		mediaPlayer = self.MP_mediaPlayer 		#	added this is refered as self in the original.

		sourceFolder = os.path.dirname(mediaPlayer.seq[0]).replace("\\", "/") #
		sources = self.core.media.getImgSources(sourceFolder)
		sourceData = []

		framepadding = self.core.framePadding 			#	added
		for curSourcePath in sources:
			if "#" * framepadding in curSourcePath: 	#	changed
				if mediaPlayer.pstart == "?" or mediaPlayer.pend == "?": #
					firstFrame = None
					lastFrame = None
				else:
					firstFrame = mediaPlayer.pstart 	#	changed
					lastFrame = mediaPlayer.pend 		#	changed

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

		mediaPlayer = self.MP_mediaPlayer 			#	added this is refered as self in the original.

		framepadding = self.core.framePadding 		# 	added
		sourceFolder = os.path.dirname(
			os.path.dirname(mediaPlayer.seq[0])		#	changed
		).replace("\\", "/")

		if "\\2dRender\\" in mediaPlayer.seq[0]:	#	added check if the mediaType is 2d #added
			sourceFolder = os.path.dirname(mediaPlayer.seq[0]).replace("\\", "/")

		passes = [
			x
			for x in os.listdir(sourceFolder)
			if x[-5:] not in ["(mp4)", "(jpg)", "(png)"]
			and not x.startswith("_")  				#	added exclude folders starting with "_" like _thumbs
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
				and mediaPlayer.pstart 					#	changed
				and mediaPlayer.pend 					#	changed
				and mediaPlayer.pstart != "?" 			#	changed
				and mediaPlayer.pend != "?" 			#	changed
			):
				firstFrame = mediaPlayer.pstart 		#	changed
				lastFrame = mediaPlayer.pend 			#	changed

				curPassName = imgs[0].split(".")[0]
				increment = "#" * framepadding 			#	changed
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


	#	This intercepts the mediaBrowser object and adds a custom internal callback
	@err_catcher(name=__name__)
	def updateTasks(self, *args, **kwargs):
		logger.debug("Loading patched function: 'mediaBrowser.updateTasks'")

		mediabrowser = self.MP_mediaBrowser

		self.core.plugins.callUnpatchedFunction(mediabrowser.updateTasks, *args, **kwargs)
		self.onMediaBrowserTaskUpdate(mediabrowser)



###########################################
#                                         #
################# CLASSES #################
#                                         #
###########################################	

#	Popup for import options
class ImageImportDialogue(QDialog):
	def __init__(self, text, title, buttons, parent=None, checked=False):
		super().__init__(parent)

		self.setWindowTitle(title)
		self.checkbox_checked = False
		self.clicked_button_text = None

		# Set up the layout
		layout = QVBoxLayout(self)

		# Add the main message text
		label = QLabel(text)
		layout.addWidget(label)

		# Add the checkbox
		self.checkbox = QCheckBox("Import Without Wireless/Sorting")
		self.checkbox.setToolTip("If this option is selected, Nodes will be added on last clicked position\n"
						   		 "and will not be taken into account when sorting.\n\n"
						   		 "They also will not be integrated into a wireless workflow.")
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


#	Popup for update message
class UpdateDialog(QDialog):
    def __init__(self, updateMsgList, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Update Information")

        layout = QVBoxLayout()

        #	Add the "Updates" header at the top
        header_label = QLabel("Updates:")
        header_font = QFont()
        header_font.setBold(True)
        header_label.setFont(header_font)
        layout.addWidget(header_label)

        #	Create the table
        self.table = QTableWidget()
        self.table.setRowCount(len(updateMsgList))
        self.table.setColumnCount(2)

        #	Hide table lines and numbers
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setVisible(False)
        self.table.setShowGrid(False)

        #	Reduce the space between cells
        self.table.setContentsMargins(0, 0, 0, 0)
        self.table.setStyleSheet("QTableWidget::item { padding: 0px; }")

        #	Get the width of the longest text in the first column
        font_metrics = QFontMetrics(self.font())
        maxWidth_firstCol = 0
        maxWidth_secondCol = 0

        for rowData in updateMsgList:
            #	First column
            textFirst = str(rowData[0])
            textWidth_first = font_metrics.horizontalAdvance(textFirst)
            if textWidth_first > maxWidth_firstCol:
                maxWidth_firstCol = textWidth_first

            #	Second column
            textSecond = str(rowData[1])
            textWidth_second = font_metrics.horizontalAdvance(textSecond)
            if textWidth_second > maxWidth_secondCol:
                maxWidth_secondCol = textWidth_second

        #	Add margin for both columns
        firstColumn_width = maxWidth_firstCol + 20
        secondColumn_width = maxWidth_secondCol + 20

        #	Populate the table with data
        for rowIndex, rowData in enumerate(updateMsgList):
            for colIndex, cellData in enumerate(rowData):
                item = QTableWidgetItem(str(cellData))
                item.setFlags(Qt.NoItemFlags)
                self.table.setItem(rowIndex, colIndex, item)

        #	Set column widths
        self.table.setColumnWidth(0, firstColumn_width)
        self.table.setColumnWidth(1, secondColumn_width)

        #	Last column stretches
        self.table.horizontalHeader().setStretchLastSection(False)

        #	Add the table
        layout.addWidget(self.table)

        # Add a close button
        b_close = QPushButton("Close")
        b_close.clicked.connect(self.close)
        layout.addWidget(b_close)

        # Set the dialog layout
        self.setLayout(layout)

        # Adjust the window width to match the table content
        totalTable_width = firstColumn_width + secondColumn_width + 50
        self.resize(totalTable_width, self.table.verticalHeader().length() + 100)
