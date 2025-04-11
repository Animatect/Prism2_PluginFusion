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
import time

import BlackmagicFusion as bmd


package_path = os.path.join(os.path.dirname(__file__), 'thirdparty')
sys.path.append(package_path)

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

import pyperclip

from PrismUtils.Decorators import err_catcher as err_catcher

from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from PrismCore import PrismCore
	from ProjectScripts.StateManager import StateManager
	from ProjectScripts.MediaBrowser import MediaBrowser, MediaPlayer
from StateManagerNodes.fus_Legacy3D_Import import Legacy3D_ImportClass
	
#	Import Prism Fusion Libraries
import Libs.Prism_Fusion_lib_Helper as Helper
import Libs.Prism_Fusion_lib_Fus as Fus
import Libs.Prism_Fusion_lib_3d as Fus3d

logger = logging.getLogger(__name__)



class Prism_Fusion_Functions(object):
	def __init__(self, core, plugin):
		self.core:PrismCore = core
		self.plugin = plugin
		self.fusion:Fusion_ = bmd.scriptapp("Fusion")
		self.comp:Composition_ = None # This comp is used by the stateManager to avoid overriding the state data on wrong comps
		
		self.MP_stateManager:StateManager = None # Reference to the stateManager to be used on the monkeypatched functions.

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
						("getIconPathForFileType", self.getIconPathForFileType)
				]

			# Iterate through the list to register callbacks
			for callback_name, method in callbacks:
				self.core.registerCallback(callback_name, method, plugin=self.plugin)

			logger.debug("Registered callbacks")

		except Exception as e:
			logger.warning(f"ERROR: Failed to register callbacks:\n{e}")
		
		self.legacyImportHandlers = {
			".abc": {"importFunction": self.importLegacyAbc},
			".fbx": {"importFunction": self.importLegacyFbx}
		}

		# self.exportHandlers = {
		# 	".abc": {"exportFunction": self.exportAlembic},
		# 	".fbx": {"exportFunction": self.exportFBX},
		# 	".obj": {"exportFunction": self.exportObj},
		# 	".blend": {"exportFunction": self.exportBlend},
		# }

		#	Format dict for Fusion naming and to differentiate still/movie types
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

		#	Dict for Fusion tool coloring (colors come from native Fusion)
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

		#	Conversion for PBR names to Fusion uShader inputs
		self.connectDict = {"ao": {"input": "occlusion", "colorspace": "linear"},
				 	   	    "color": {"input": "diffuseColor", "colorspace": "sRGB"},
				 	   		"metallic": {"input": "metallic", "colorspace": "linear"},
							"roughness": {"input": "roughness", "colorspace": "linear"},
							"normal": {"input": "normal", "colorspace": "linear"},
							"displace": {"input": "displacement", "colorspace": "linear"},
							"alpha": {"input": "opacity", "colorspace": "linear"},
							"alphaThreshold": {"input": "opacityThreshold", "colorspace": "linear"},
							"emit": {"input": "emissiveColor", "colorspace": "sRGB"},
							"clearcoat": {"input": "clearcoat", "colorspace": "linear"},
							"coatRough": {"input": "clearcoatRoughness", "colorspace": "linear"},
							"ior": {"input": "ior", "colorspace": "linear"},
							"specColor": {"input": "specColor", "colorspace": "sRGB"}
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
		
		#	Gets config settings from the DCC settings
		self.taskColorMode = self.core.getConfig("Fusion", "taskColorMode")
		self.useAovThumbs = self.core.getConfig("Fusion", "useAovThumbs")
		self.sortMode = self.core.getConfig("Fusion", "sorting")

		usePopup = self.core.getConfig("Fusion", "updatePopup")
		if usePopup == "Enabled":
			self.useUpdatePopup = True
		else:
			self.useUpdatePopup = False


		#	Sets the AOV thumb size based off user settings
		match self.core.getConfig("Fusion", "thumbsSize"):
			case "Small (300 px)":
				self.aovThumbWidth = 300
			case "Medium (600 px)":
				self.aovThumbWidth = 600
			case "Large (900 px)":
				self.aovThumbWidth = 900
			case _:
				self.aovThumbWidth = 500

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
	def setDefaultState(self):
		comp = self.getCurrentComp()
		if self.sm_checkCorrectComp(comp):
			Fus.setDefaultState(comp)


	@err_catcher(name=__name__)
	def sm_saveStates(self, origin, buf):
		comp = self.getCurrentComp()
		# The comp check for the imports should be done also in the  states operations.
		# here we just do a check,  by doing that we can check again in another function where we can actually interrupt the process
		# in the other functions if there is a problem but avoid corrupting the comp's states.
		if self.sm_checkCorrectComp(comp, displaypopup=False, deleteSM=False):
			Fus.sm_saveStates(comp, buf)


	@err_catcher(name=__name__)
	def sm_saveImports(self, origin, importPaths):
		comp = self.getCurrentComp()
		# The comp check for the imports should be done also in the import and delete functions for import states.
		# here we just do a check, but by doing it there we can actually interrupt the process.
		if self.sm_checkCorrectComp(comp, displaypopup=False, deleteSM=False):
			Fus.sm_saveImports(comp, importPaths)


	@err_catcher(name=__name__)
	def sm_readStates(self, origin):
		comp = self.getCurrentComp()
		if self.sm_checkCorrectComp(comp):
			return Fus.sm_readStates(comp)

	@err_catcher(name=__name__)
	def sm_createStatePressed(self, origin, stateType):
		comp = self.getCurrentComp()
		if self.sm_checkCorrectComp(comp):
			return []
		
		logger.warning(f"ERROR: Unable to to create state")
		return None


	#	Gets called from SM to remove all States
	@err_catcher(name=__name__)
	def sm_deleteStates(self, origin):
		comp = self.getCurrentComp()
		if self.sm_checkCorrectComp(comp):
			#	Sets the states datablock to empty default state
			Fus.setDefaultState(comp)
			self.core.popup("All States have been removed.\n"
							"You may have to remove associated Loaders and Savers\n"
							"from the comp manually.")


	@err_catcher(name=__name__)
	def getImportPaths(self, origin):
		comp = self.getCurrentComp()
		if self.sm_checkCorrectComp(comp):
			return Fus.getImportPaths(comp)


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
	

	#	Called from core.sceneOpen()
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
	def sm_import_startup(self, origin):
		pass


	@err_catcher(name=__name__)
	def sm_checkCorrectComp(self, comp, displaypopup:bool=True, deleteSM:bool=True):
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
				# deleteSM allows to use this function as a boolean check without deleting the StateManager.
				if deleteSM:
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
		thumb = self.wrapped_CaptureViewportThumbnail(comp)
		comp.Unlock()
		return thumb


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
				logger.debug(f"Created Thumbnail from: {Fus.getToolName(thumbTool)}")
			
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
			toolName = Fus.getToolName(tool)

			if mode == "save":
				# Save the current pass-through state
				origSaverList[toolName] = Fus.isPassThrough(comp, tool=tool)
				Fus.setPassThrough(comp, tool=tool, passThrough=True)
			elif mode == "load":
				# Restore the original pass-through state
				if toolName in origSaverList:
					Fus.setPassThrough(comp, tool=tool, passThrough=origSaverList[toolName])

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
			if self.isSaver(tool) and not Fus.isPassThrough(comp, tool=tool):
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
			if Fus.getToolType(tool) == "Saver":
				return True
			else:
				return False
		except:
			return False
	

	#	Returns Fusion-legal Saver name base on State name
	@err_catcher(name=__name__)
	def getRendernodeName(self, stateName):
		legalName = Helper.getFusLegalName(stateName)
		toolName = f"PrSAVER_{legalName}"

		return toolName
	
	
	#	Creates Saver with UUID associated with ImageRender state
	@err_catcher(name=__name__)
	def createRendernode(self, toolUID, toolData):
		comp = self.getCurrentComp()
		comp.Lock()
		comp.StartUndo("Create Render Node")

		self.wrapped_createRendernode(toolUID, toolData, comp=comp)

		comp.EndUndo()
		comp.Unlock()		
	

	@err_catcher(name=__name__)
	def wrapped_createRendernode(self, toolUID, toolData, comp):
		if not comp:
			comp = self.getCurrentComp()
		if self.sm_checkCorrectComp(comp):
			if not Fus.toolExists(comp, toolUID):
				#	Get selected Tool

				selTools = Fus.getSelectedTools(comp)

				#	Add Saver to Comp
				sv = Fus.addTool(comp, "Saver", toolData)

				#	Position Saver
				if selTools:
					try:
						#	Move Render Node to the Right of the scene	
						Fus.setToolPosRelative(comp, sv, selTools[0], 3)
						# Fus.stackToolsByType(comp, sv)
					except:
						logger.debug(f"ERROR: Not able to position {toolData['toolName']}")

			if sv:
				logger.debug(f"Saver created for: {toolData['toolName']} - {toolData}")
				return sv
			else:
				logger.warning(f"ERROR: Unable to create Saver for {toolData['toolName']}")
				return False


	#	Updates Saver tool name
	@err_catcher(name=__name__)
	def updateRendernode(self, toolUID, toolData):
		comp = self.getCurrentComp()
		comp.Lock()
		comp.StartUndo("Update Render Node")

		self.wrapped_updateRendernode(toolUID, toolData, comp)	

		comp.EndUndo()
		comp.Unlock()


	@err_catcher(name=__name__)
	def wrapped_updateRendernode(self, toolUID, toolData, comp):
		if self.sm_checkCorrectComp(comp):
			sv = Fus.getToolByUID(comp, toolUID)

			if sv:
				#	Update Saver Info
				Fus.configureTool(sv, toolData)
				logger.debug(f"Saver updated: {toolData['toolName']}")
			else:
				logger.warning(f"ERROR: Not able to update: {toolData['toolName']}")

			return sv
		

	#	Configures Saver filepath and image format
	@err_catcher(name=__name__)
	def configureRenderNode(self, toolUID, toolData):
		comp = self.getCurrentComp()
		if self.sm_checkCorrectComp(comp):
			sv = Fus.getToolByUID(comp, toolUID)
			if sv:
				#	Update Saver
				Fus.configureTool(sv, toolData)

				#	Check if Saver is connected to something
				if Fus.hasConnectedInput(sv):
					if "toolName" in toolUID:
						logger.debug(f"Configured Saver: {toolData['toolName']}")
					else:
						logger.debug(f"Configured Saver: {toolData}")


				else:
					logger.debug(f"ERROR: Render Node is not connected: {toolUID}")
			else:
				logger.warning(f"ERROR: Render Node does not exist: {toolUID}")


	#	Removes Node from Comp
	@err_catcher(name=__name__)
	def deleteNode(self, toolUID, delAction):
		comp = self.getCurrentComp()
		if self.sm_checkCorrectComp(comp):
			if delAction and Fus.toolExists(comp, toolUID):
				#	Delete the Tool from the Comp
				try:
					tool = Fus.getToolByUID(comp, toolUID)
					toolName = Fus.getToolName(tool)

					tool.Delete()
					logger.debug(f"Removed tool '{toolName}")

				except:
					logger.warning(f"ERROR:  Unable to remove tool from Comp: {toolUID}")

	


	################################################
	#                                              #
	#                 STATE MANAGER                #
	#                                              #
	################################################


	#	Gets called from StateManager to get Import State type							#	NEEDED???
	# @err_catcher(name=__name__)		
	# def sm_getImportHandlerType(self, extension):
	# 	return self.imageImportHandlers.get(extension.lower())


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
		if Fus3d.isNodeValid(origin, origin.curCam):
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


	#	TODO  TEMP

	# def makeImportData(self, context, aovDict, sourceData):
	# 	#	Function to aggregate data into importData
	# 	return Helper.makeImportData(self, context, aovDict, sourceData)



	@err_catcher(name=__name__)
	def imageImport(self, state, importData, sortMode):
		comp = self.getCurrentComp()
		comp.Lock()
		comp.StartUndo("Import Media")

		result = self.wrapped_ImageImport(comp, state, importData, sortMode)

		comp.EndUndo()
		comp.Unlock()

		return result


	#	Receives importData and adds the Loaders to the Comp
	@err_catcher(name=__name__)
	def wrapped_ImageImport(self, comp, state, importData, sortMode):
		"""
		Example importData:
			{
			'stateUID': '0b67a0f6',
			'identifier': 'SingleLyr-MultiAOV',
			'displayName': 'SingleLyr-MultiAOV',
			'mediaType': '3drenders',
			'itemType': 'shot',			(or 'asset')
			'asset': 'monkey',			(based on 'itemType')
			'sequence': '010_seq',		(based on 'itemType')
			'shot': '010_shot',			(based on 'itemType')
			'locations': {
						'global': 'N:\\...\\3dRender\\SingleLyr-MultiAOV\\v002'
						}, 
			'path': 'N:\\...\\3dRender\\SingleLyr-MultiAOV\\v002\\AO',
			'extension': '.exr',
			'version': 'v002',
			'aovs': ['AO', 'Beauty', 'DiffCol'],
			'channels': ['RGBA],
			'files': [
						{
							'basefile': 'N:\\...\\3dRender\\SingleLyr-MultiAOV\\v002\\AO\\010_MEDIA-010_MEDIA_SingleLyr-MultiAOV_v002_AO.0001.exr',
							'identifier': 'SingleLyr-MultiAOV',
							'aov': 'AO',
							'channel': 'RGBA',
							'version': 'v002',
							'frame_start': 1,
							'frame_end': 20
						},
						{
							'basefile': 'N:\\...\\3dRender\\SingleLyr-MultiAOV\\v002\\Beauty\\010_MEDIA-010_MEDIA_SingleLyr-MultiAOV_v002_Beauty.0001.exr',
							'identifier': 'SingleLyr-MultiAOV',
							'aov': 'Beauty',
							'channel': 'RGBA',
							'version': 'v002',
							'frame_start': 1,
							'frame_end': 20
						},
						{
							'basefile': 'N:\\...\\3dRender\\SingleLyr-MultiAOV\\v002\\DiffCol\\010_MEDIA-010_MEDIA_SingleLyr-MultiAOV_v002_DiffCol.0001.exr',
							'identifier': 'SingleLyr-MultiAOV',
							'aov': 'DiffCol',
							'channel': 'RGBA',
							'version': 'v002',
							'frame_start': 1,
							'frame_end': 20
						}
					]
			}
		
		"""

		flow = comp.CurrentFrame.FlowView

		#	Initilizes the Update Message stuff
		updated = False
		updateMsgList = []

		#	Setup Sorting/Wireless modes
		sortNodes = False
		addWireless = False
		if sortMode == "Sorting & Wireless":
			sortNodes = True
			addWireless = True
		elif sortMode == "Sorting Only":
			sortNodes = True

		refNode = None

		#	Finds the left edge of the flow-nodes
		if sortNodes:
			refNode = Fus.findLeftmostLowerTool(comp, 0.5)

		try:
				#	For each import item
			start = time.time()
			refX, refY = Fus.getToolPosition(comp, refNode)
			for importItem in importData["files"]:
				# Deselect all nodes
				flow.Select()

				#	Make base dict
				toolData = {"nodeName": Fus.makeLdrName(importItem, importData),
							"toolUID": importItem["fileUID"],
							"version": importData["version"],
							"stateUID": importData["stateUID"],
							"mediaId": importData["identifier"],
							"displayName": importData["displayName"],
							"mediaType": importData["mediaType"],
							"aov": importItem.get("aov", ""),
							"channel": importItem.get("channel", ""),
							"filepath": importItem["basefile"],
							"extension": importData["extension"],
							"fuseFormat": self.getFuseFormat(importData["extension"]),
							"frame_start": importItem["frame_start"],
							"frame_end": importItem["frame_end"],
							"listType": "import2d",
							}
					
				#	Add additional items if they exist
				for key in ["asset", "sequence", "shot", "itemType", "redirect"]:
					if key in importData:
						toolData[key] = importData[key]

				#	Get any Matching Tools already in the Comp
				orig_toolUID = Fus.getUIDsFromImportData(comp, importItem, "import2d")

				#	Add Loader and configure
				if len(orig_toolUID) == 0:
					#	Import the image
					leftmostNode = self.addImage(comp, toolData, sortNodes, addWireless, refX, refY)

					#	Return if failed
					if not leftmostNode:
						logger.warning(f"ERROR:  Unable to import Images:\n{e}")
						self.core.popup(f"ERROR:  Unable to import Images:\n{e}")
						return False
					
					

				#	Update loader if it already exists in the Comp
				else:
					updated = True
					doImport = True
					orig_toolUID = orig_toolUID[0]
					updateRes, compareMsg = self.updateImport(comp, orig_toolUID, toolData)

					updateMsgList.append(compareMsg)
			
			end1 = time.time()
			print(f"# tool Adding Execution time: {end1 - start:.4f} seconds")

			##########################
			# SORT ALL PRISM LOADERS #
			##########################
					
			#	If Not Sorting
			if not sortNodes:
				logger.debug(f"Imported  {importData['identifier']} without sorting")
				result = "Imported Image without Sorting"
				doImport = True

			#	If Sorting
			else:
				#	Sort and Arrange Loaders and Wireless tools
				self.sortLoaders(comp, currentStateID=importData["stateUID"])

				logger.debug(f"Imported  and sorted {importData['identifier']}")
				result = "Imported Image without Sorting"
				doImport = True

			end = time.time()
			print(f"Execution time: {end - start:.4f} seconds")
			if updated:
				return {"result": "updated", "updateMsgList": updateMsgList, "doImport": doImport}
			else:
				return {"result": result, "doImport": doImport}

		except Exception as e:
			logger.warning(f"ERROR:  Unable to import Images:\n{e}")
			self.core.popup(f"ERROR:  Unable to import Images:\n{e}")


	@err_catcher(name=__name__)
	def addImage(self, comp, toolData, sortNodes, addWireless, refX=0, refY=0):
		flow = comp.CurrentFrame.FlowView
		toolUID = toolData["toolUID"]
		
		try:
			if sortNodes:
				#	Add and configure Loader below so it will not mess up Flow
				ldr = Fus.addTool(comp, "Loader", toolData, xPos=refX , yPos=refY + 0.5)
			else:
				#	Add and configure Loader without positiong
				ldr = Fus.addTool(comp, "Loader", toolData)
		
			if not ldr:
				self.core.popup(f"ERROR: Unable to add Loader to Comp")
				return False

		except:
			logger.warning(f"ERROR: Unable to add Loader to Comp")
			return False

		# Deselect all
		flow.Select()

		if toolData["extension"] == ".exr":
			#	Handle Multi-part .exrs
			try:
				channel = toolData["channel"]

				#	Check if the file has parts
				if ldr.Clip1.OpenEXRFormat.Part:
					#	Get list of parts in file
					parts = ldr.Clip1.OpenEXRFormat.Part.GetAttrs('INPIDT_ComboControl_ID')
					#	Match and assign part
					if channel in parts.values():
						ldr.Clip1.OpenEXRFormat.Part = channel
			except:
				logger.warning(f"ERROR: Unable to assign multi-part .exr for ({channel})")

			try:		
				#	Get available channels from Loader
				loaderChannels = Fus.getLoaderChannels(ldr)
				channelData = Fus.getChannelData(loaderChannels)

				#	Get the channel list for the channel being processed
				if len(channelData) > 0:
					channelDict = channelData[toolData["channel"]]

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

					else:
						#	Match the attrs based on the dict
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
				return False

		#	If Add Wireless is enabled
		if addWireless:
			self.createWireless(toolUID)
			
		return ldr
			

	@err_catcher(name=__name__)
	def updateImport(self, comp, orig_toolUID, toolData):
		#	Get original node data from database
		origTool = Fus.getToolByUID(comp, orig_toolUID)
		origToolData = Fus.getToolData(origTool)
		
		#	Make copy of original data
		updateData = origToolData.copy()

		#	Update data with new values
		updateData["version"] = toolData["version"]
		updateData["filepath"] = toolData["filepath"]
		updateData["frame_start"] = toolData["frame_start"]
		updateData["frame_end"] = toolData["frame_end"]
		updateData["nodeName"] = Fus.makeLdrName(updateData, toolData)

		#	Get original Loader
		ldr = Fus.getToolByUID(comp, orig_toolUID)
		#	Update Loader config
		Fus.configureTool(ldr, updateData)

		#	Get version compare message
		compareRes, compareMsg = Helper.compareVersions(origToolData, toolData)

		return compareRes, compareMsg


	#	Creates and adds a Wireless set to the Loader
	#	This uses an AutoDomain tool for the "IN", and the Wireless for the "OUT"
	@err_catcher(name=__name__)
	def createWireless(self, toolUID):							#	TODO  Look into adding wireless with "addTool"
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

		#	Get Loader tool
		ldr = Fus.getToolByUID(comp, toolUID)

		#	Get Loader data
		ldrData = Fus.getToolData(ldr)

		#	Make base name
		baseName = Fus.makeWirelessName(ldrData)
		
		try:
			#	Copy and paste settings code into Comp
			pyperclip.copy(wirelessCopy)
			comp.Paste(wirelessCopy)

			#	Sets Wireless tools names
			wireless_IN = comp.FindTool("neverreferencednameonautodomain")
			wireless_IN_name = baseName + '_IN'
			wireless_IN.SetAttrs({'TOOLS_Name': wireless_IN_name})
			wireless_OUT = comp.FindTool("neverreferencednameonwirelesslink")
			wireless_OUT_name = baseName + '_OUT'
			wireless_OUT.SetAttrs({'TOOLS_Name': wireless_OUT_name})

			#	Temporarily Set Positions of Tools
			Fus.setToolPosRelative(comp, wireless_IN, ldr, 1.5)
			Fus.setToolPosRelative(comp, wireless_OUT, wireless_IN, 1.5)
			
			#	Connect _IN to Loader
			# wireless_IN.ConnectInput('Input', ldr)
			Fus.connectTools(ldr, wireless_IN)

			#	Get Loader's Original Data
			lData = Fus.getToolData(ldr)

			#	List of Keys that are not needed in the Wireless Tools
			keysToDelete = ["nodeName",
							"version",
							"filepath",
							"extension",
							"fuseFormat",
							"frame_start",
							"frame_end",
							"connectedNodes"]
			
			#	Make Generic Wireless Data using Loader Data deleting the keys
			wData = {key: value for key, value in lData.items() if key not in keysToDelete}

			#	Make Wireless_In data
			w_inData = wData.copy()
			#	Make Wireless_In UID and add to its Data
			wirelessInUID = Helper.createUUID()
			w_inData["toolUID"] = wirelessInUID
			w_inData["nodeName"] = wireless_IN_name
			#	Add Data to the Database
			Fus.configureTool(wireless_IN, w_inData)

			#	Make Wireless_Out data
			w_outData = wData.copy()
			#	Make Wireless_Out UID and add to its Data
			wirelessOutUID = Helper.createUUID()
			w_outData["toolUID"] = wirelessOutUID
			w_outData["nodeName"] = wireless_OUT_name
			#	Add Data to the Database
			Fus.configureTool(wireless_OUT, w_outData)

			#	Add Wireless Nodes to Loader's Data
			lData["connectedNodes"] = {"wireless_IN": wirelessInUID,
											"wireless_OUT": wirelessOutUID}
			Fus.configureTool(ldr, lData)

			#	Select the wireless out
			flow.Select()
			comp.SetActiveTool(wireless_OUT)

			logger.debug(f"Created Wireless nodes for: {ldr.Name}")

		except Exception as e:
			logger.warning(f"ERROR:  Could not add wireless nodes:\n{e}")

	@err_catcher(name=__name__)
	def get_all_items(self, tree_widget):
		def recurse_items(parent):
			items = []
			for i in range(parent.childCount()):
				child = parent.child(i)
				items.append(child)
				items.extend(recurse_items(child))
			return items

		all_items = []
		for i in range(tree_widget.topLevelItemCount()):
			top_item = tree_widget.topLevelItem(i)
			all_items.append(top_item)
			all_items.extend(recurse_items(top_item))
		return all_items

	@err_catcher(name=__name__)
	def getImageStatesIDs(self)->list:
		sm = self.MP_stateManager
		items = self.get_all_items(sm.tw_import)
		imageImports:list = []
		for item in items:
			if item.ui.className == "Image_Import":
				props = item.ui.getStateProps()
				taskName = props["displayName"]
				stateUID = item.ui.stateUID
				imageImports.append(stateUID)
		return imageImports
	
	@err_catcher(name=__name__)
	def selectAllStateLoaders(self):
		#   Get Fusion objects
		comp = self.getCurrentComp()
		flow = comp.CurrentFrame.FlowView
		#	All State iDs
		imagestateuids:list = self.getImageStatesIDs()
		allstatetools:list = []
		#   All State Tool UIDS
		for stateUID in imagestateuids:
			stateTools = Fus.getToolsFromStateUIDs(comp, stateUID)
			allstatetools += stateTools

		#   Select each Tool
		flow.Select()
		for tool in allstatetools:
			flow.Select(tool)

	#	Sort and arrange all Prism Loaders 
	@err_catcher(name=__name__)
	def sortLoaders(self, comp, currentStateID=None, getfeedback:bool=False, offset=1.5, flowThresh=100, toolThresh=3, horzGap=1.1, vertGap=1):
		flow = comp.CurrentFrame.FlowView
		print("sorting...")
		posRefNode = Fus.findLeftmostUpperTool(comp, toolType="Loader")
		if not posRefNode:
			return self.core.popup("Nothing to Sort", severity="info")
		
		stateuids:list = self.getImageStatesIDs()
		# In case the state object has not been created and can't be listed or queried.
		if currentStateID and not currentStateID in stateuids:
			stateuids.append(currentStateID)
		print("stateuids: ", stateuids)
		#   Get the left-most and bottom-most Loader within a threshold.
		leftmostpos, bottommostpos = Fus.getToolPosition(comp, posRefNode)

		#   We get only the loaders within a threshold from the leftmost and who were created by prism.
		try:
			start=time.time()
			loaders = [l for l in comp.GetToolList(False, "Loader").values()
					if (
						abs(Fus.getToolPosition(comp, l)[0] - leftmostpos) <= flowThresh
						and l.GetData("Prism_UUID")
						and l.GetData('Prism_ToolData')
						and l.GetData('Prism_ToolData').get("stateUID") in stateuids
						)
						]
			# We sort top to bottom to get the topmost position among these
			loaderstop2bot = sorted(loaders, key=lambda ld: Fus.getToolPosition(comp, ld)[1])
			end = time.time()
			print(f"# get and sort loaders Execution time: {end - start:.4f} seconds")
			
		except:
			logger.warning("ERROR: Cannot sort loaders - unable to resolve threshold in the flow")
			return

		#	Gets list of all Media Identifiers in the Comp Database
		start = time.time()

		# Create a mapping for UID priority
		uid_index = {uid: index for index, uid in enumerate(stateuids)}
		# Sort first by UID block using the index on the sorted function, then by name
		# Sort primarily by the UID order (using its numeric rank from uid_index) If multiple entries share the same UID, sort alphabetically by name
		sortedloaders = sorted(loaders, key=lambda ld: (uid_index[ld.GetData("Prism_ToolData").get("stateUID")], ld.Name.lower()))
					
		# if refNode is not part of nodes to sort we move the nodes down so they don't overlap it.
		refInNodes = any(ldr.Name == posRefNode.Name for ldr in sortedloaders)

		if len(sortedloaders) < 1:
			return
		# To check if a node is in a layer or if we've switched layers, we first store a refernce layer
		# update it and compare it in each iteration.
		lastLoaderLyr = sortedloaders[0].GetData("Prism_ToolData").get("mediaId")
		end = time.time()
		print(f"# get and sort MediaID Execution time: {end - start:.4f} seconds")

		try:
			start = time.time()
			new_X = leftmostpos
			new_Y = Fus.getToolPosition(comp, loaderstop2bot[0])[1]

			if not refInNodes:
				new_Y = bottommostpos + offset

			for ldr in sortedloaders:
				#   Get Loader data
				ldrData = Fus.getToolData(ldr)
				lyrNm = ldrData['mediaId']

				#	Gets the connected tools if any
				connectedTools = ldrData.get("connectedNodes", None)

				if connectedTools:
					# Gets the wireless nodes if available
					inNode = Fus.getToolByUID(comp, connectedTools.get("wireless_IN"))
					outNode = Fus.getToolByUID(comp, connectedTools.get("wireless_OUT"))
				else:
					inNode, outNode = None, None

				# Get input object connected to Loader
				nextToolInput = Fus.getInputsFromOutput(ldr)
				nextTool = nextToolInput[0].GetTool() if nextToolInput else None
				nextToolName = nextTool.Name if nextTool else None

				# Get Wireless_IN position before moving (only if inNode exists)
				inNodeOrigPos = Fus.getToolPosition(comp, inNode) if inNode else None

				# Adjust vertical position for the Loader
				if lyrNm != lastLoaderLyr:
					new_Y += vertGap

				# Set Loader position
				Fus.setToolPosition(flow, ldr, new_X, new_Y)

				# Only handle connections if there are connected tools
				if inNode and nextTool:
					if nextToolName != inNode.Name:
						# Connect Loader to nextTool
						Fus.connectTools(ldr, nextTool)
						# Position nextTool to the right of the Loader
						Fus.setToolPosRelative(comp, nextTool, ldr, horzGap)
						# Connect nextTool to _IN
						Fus.connectTools(nextTool, inNode)
						# Position Wireless_IN to the right of the Loader
						Fus.setToolPosRelative(comp, inNode, ldr, horzGap * 2)
					else:
						# Connect Loader to Wireless IN
						Fus.connectTools(ldr, inNode)
						# Position Wireless_IN to the right of the Loader
						Fus.setToolPosRelative(comp, inNode, ldr, horzGap * 2)

				if outNode and inNode:
					# If _OUT and _IN are within toolThresh, position _OUT
					if Fus.isToolNearTool(comp, outNode, refPos=inNodeOrigPos, thresh=toolThresh):
						Fus.setToolPosRelative(comp, outNode, inNode, horzGap)

				# Increment vertical position for next Loader
				new_Y += vertGap
				lastLoaderLyr = lyrNm
			
			end = time.time()
			print(f"# Tools Sorting Execution time: {end - start:.4f} seconds")
			logger.debug("Sorted Nodes")
			
			if getfeedback:
				self.core.popup("Sorted!", severity="info")
		

		except Exception as e:
			logger.warning(f"ERROR: Failed to sort nodes:\n{e}")



	################################################
	#                                              #
	#                   IMPORT3D                   #
	#                                              #
	################################################


	#	Imports or updates USD scene or object
	@err_catcher(name=__name__)
	def importUSD(self, origin, UUID, toolData, update=False):
		comp = self.getCurrentComp()
		flow:FlowView_ = comp.CurrentFrame.FlowView

		if self.sm_checkCorrectComp(comp):
			comp.Lock()
			comp.StartUndo("Import USD")

			flow.InsertBookmark("USD_Import")
			result = self.wrapped_importUSD(origin, UUID, toolData, update)

			
			bookmarks = flow.GetBookmarkList()
			last_item = bookmarks.popitem()
			flow.SetBookmarkList(bookmarks)
			
			comp.EndUndo()
			comp.Unlock()
		else:
			logger.warning(f"ERROR: Unable to import USD")
			return {"result": False, "doImport": False}

		return result
	
	
	#	Imports or updates USD scene or object
	@err_catcher(name=__name__)
	def wrapped_importUSD(self, origin, UUID, toolData, update=False):
		comp = self.getCurrentComp()
		importRes = False

		#	Add new uLoader if not update or if the Tool is not in the Comp
		if not update or not Fus.toolExists(comp, UUID):
			try:
				#	Add tool
				uLdr = Fus.addTool(comp, "uLoader", toolData)

				logger.debug(f"Imported USD object: {toolData['product']}")

			except Exception as e:
				logger.warning(f"ERROR: Unable to import USD object:\n{e}")
				return {"result": False, "doImport": False}
			
			if uLdr:
				importRes = True
		
		#	Update uLoader
		else:
			try:
				#	Get tool
				tool = Fus.getToolByUID(comp, UUID)
				#	 Update tool data
				uLdr = Fus.configureTool(tool, toolData)

				logger.debug(f"Updated uLoader: {toolData['nodeName']}")
				importRes = True

			except Exception as e:
				logger.warning(f"ERROR: Failed to update uLoader:\n{e}")

			if uLdr:
				importRes = True

		return {"result": importRes, "doImport": importRes}
	

	#	Creates simple USD scene - adds uMerge and uRender to uLoader
	@err_catcher(name=__name__)
	def createUsdScene(self, origin, UUID):
		comp = self.getCurrentComp()
		if self.sm_checkCorrectComp(comp):
			comp.Lock()
			comp.StartUndo("Create USD Scene")

			self.wrapped_createUsdScene(origin, UUID, comp)

			comp.EndUndo()
			comp.Unlock()
		else:
			logger.warning(f"ERROR: Unable to create USD scene")


	@err_catcher(name=__name__)
	def wrapped_createUsdScene(self, origin, UUID, comp):
		try:
			Fus3d.createUsdScene(self, origin, UUID)
			logger.debug(f"Created USD Scene for {UUID}")

		except Exception as e:
			logger.warning(f"ERROR: Unable to create USD scene:\n{e}")



	#	Creates group with uTextures and uShader
	@err_catcher(name=__name__)
	def createUsdMaterial(self, origin, UUID, texData, update=False):
		comp = self.getCurrentComp()
		flow:FlowView_ = comp.CurrentFrame.FlowView

		# comp.Lock()
		comp.StartUndo("Create USD Material")

		flow.InsertBookmark("USDmat_Import")
		result = self.wrapped_createUsdMaterial(origin, UUID, texData, update)

		comp.EndUndo()
		# comp.Unlock()

		return result


	#	Creates group with uTextures and uShader
	@err_catcher(name=__name__)
	def wrapped_createUsdMaterial(self, origin, UUID, texData, update):
		comp = self.getCurrentComp()
		flow = comp.CurrentFrame.FlowView

																		#	TODO add more connection types
																		#	TODO handle ARM type (AO, ROUGH, MET)
																		#	It seems Fusion cannot manipulate uTextures
		#	If Update, just toggle Tool bypass
		if update:
			try:
				tool = Fus.getToolByUID(comp, UUID)
				sData = Fus.getToolData(tool)
				groupUID = sData["connectedNodes"]["Group"]
				comp.Unlock()
				Fus.setPassThrough(comp, nodeUID=groupUID, passThrough=True)
				Fus.setPassThrough(comp, nodeUID=groupUID, passThrough=False)
				comp.Lock()

				return {"result": True, "doImport": True}
			except:
				logger.warning("ERROR: Failed to update USD Material")
				return {"result": False, "doImport": False}

		#	Add uShader
		try:
			#	Configure Data
			shdData = texData.copy()
			del shdData["texFiles"]
			shdData["toolName"] = f"{texData['toolName']}_uShader"
			shdData["shaderName"] = texData["shaderName"]
		
			#	Get Positions to not mess up flow
			lastClicked = Fus.findLastClickPosition(comp)
			leftTool = Fus.findLeftmostLowerTool(comp, threshold=10)
			left_x, left_y = Fus.getToolPosition(comp, leftTool)
			temp_x = left_x - 20
			temp_y = left_y - 20

			#	Add uShader tool
			uShader = Fus.addTool(comp, "uShader", shdData, temp_x, temp_y)
			logger.debug(f"Added uShader: {shdData['toolName']}")
		
		except Exception as e:
			logger.warning(f"ERROR: Unable to add uShader to Comp:\n{e}")
			comp.Unlock()
			return False

		#	Handle textures
		try:
			connectedTexs = {}
			for texture in texData["texFiles"]:
				#	Create UIDs for each texture
				toolUID = Helper.createUUID()
				#	Configure texture data
				texDict = {}
				texDict["toolUID"] = toolUID
				texDict["stateUID"] = texData["stateUID"]
				texDict["nodeName"] = f"{texData['toolName']}_{texture['map'].upper()}"
				texDict["shaderName"] = texData["shaderName"]
				texDict["texMap"] = texture["map"].upper()
				texDict["uTexFilepath"] = texture["path"]				

				#	Add uTexture
				uTexture = Fus.addTool(comp, "uTexture", texDict, temp_x, temp_y)

				if uTexture:
					#	Add to Connected Textures Dict
					connectedTexs[f"Tex_{texture['map'].upper()}"] = toolUID

		except Exception as e:
			logger.warning(f"ERROR: Unable to add uTextures to Comp:\n{e}")
			comp.Unlock()
			return False

		#	Add connected tools to uShader Data
		updateDict = {"connectedNodes": connectedTexs}
		Fus.updateToolData(uShader, updateDict)

		#	Get tool for each UID
		texTools = [tool for uid in connectedTexs.values() if (tool := Fus.getToolByUID(comp, uid))]
		#	Stack uTextures and get the average position
		xPos, yPos = Fus.stackToolsByList(comp, texTools, yoffset=0.6)
		#	Moves uShader to the right of the stack
		Fus.setToolPosition(flow, uShader, xPos+1, yPos)

		logger.debug("Added uTextures to Comp")
		
		#	Make texture connections
		for tool in texTools:
			try:
				#	Get tool data
				toolData = Fus.getToolData(tool)

				#	Get map type from data
				mapType = (toolData.get("texMap", None)).lower()
				#	Get uShader connection data from map type
				connectionData = self.connectDict.get(mapType, None)
				#	Extract input name and colorspace
				mapInput = connectionData.get("input", None)

				#	Connect the tool to the uShader using mapInput
				uShader[mapInput] = tool

				logger.debug(f"Connected {tool.Name} to uShader_{mapInput}")
				
			except:
				logger.warning(f"ERROR: Failed to connect {tool.Name} to uShader.")

		#	Make Group
		try:
			#	Make list of tools to add to group
			groupTools = texTools
			groupTools.append(uShader)
			#	Make group name
			groupName = texData['shaderName']

			#	Create group
			groupUID, newToolsUIDs = Fus.groupTools(comp,
										   			self,
													groupName,
													groupTools,
													outputTool=uShader,
													pos=lastClicked)
			

			#	Make Group Data
			groupData = {"groupName": texData['shaderName'],
						 "stateUID": texData["stateUID"],
						 "shaderName": texData["shaderName"],
						 "connectedNodes": newToolsUIDs}

			#	Get Group Tool
			groupTool = Fus.getToolByUID(comp, groupUID)


			#	Uodate Group and add to Database
			Fus.configureTool(groupTool, groupData)

			#	Add Group UID to uShader database record
			updateDict["connectedNodes"]["Group"] = groupUID
			Fus.updateToolData(uShader, updateDict)

			logger.debug(f"Created shader group: {groupName}")

		except Exception as e:
			logger.warning("ERROR: Failed to create group")
			comp.Unlock()

		#	Set the colorspace for textures
		#	(have to do it at the end since it gets reset in the group creation)
		if newToolsUIDs:
			for uid in newToolsUIDs:
				try:
				#	Get tool data
					tool = Fus.getToolByUID(comp, uid)
					toolData = Fus.getToolData(tool)

					#	Get map type from data
					mapType = toolData.get("Prism_TexMap", None)
					mapType = mapType.lower() if mapType is not None else None

					if mapType:
						#	Get colorspace from map type
						connectionData = self.connectDict.get(mapType, None)
						colorspace = connectionData.get("colorspace", None)

						#	Change to Fusion integer
						colorCode = 0
						if colorspace == "sRGB":
							colorCode = 1

						#	Set the tools colorspace
						tool["SourceColorSpace"] = colorCode

						logger.debug(f"Configured SourceColorSpace for {tool.Name}")

				except:
					logger.warning(f"ERROR: Not able to set Source ColorSpace for {tool.Name}.")
					comp.Unlock()


	#	Creates MaterialX tool
	@err_catcher(name=__name__)
	def createUsdMatX(self, origin, UUID, texData, update=False):
		comp = self.getCurrentComp()
		flow:FlowView_ = comp.CurrentFrame.FlowView

		comp.Lock()
		comp.StartUndo("Import USD MaterialX")	

		flow.InsertBookmark("USDmatX_Import")
		result = self.wrapped_createUsdMatX(origin, UUID, texData, update)

		comp.EndUndo()
		comp.Unlock()

		return result


	#	Creates MaterialX tool
	@err_catcher(name=__name__)
	def wrapped_createUsdMatX(self, origin, UUID, matXData, update):
		comp = self.getCurrentComp()
		result = False

		if not update:
			try:
				#	Add uMaterialX tool
				uMaterialX = Fus.addTool(comp, "uMaterialX", matXData)
			
				if uMaterialX:
					result = True
					logger.debug(f"Created MaterialX ({matXData['shaderName']})")
			except:
				logger.warning("ERROR:  Failed to create MaterialX material")

		else:
			try:
				tool = Fus.getToolByUID(comp, UUID)
				uMaterialX = Fus.configureTool(tool, matXData)

				if uMaterialX:
					result = True
					logger.debug(f"Updated MaterialX ({matXData['shaderName']})")
			except:
				logger.warning("ERROR: Failed to update MaterialX material")

		return {"result": result, "doImport": result}


	#	Imports .fbx or .abc object into Comp
	@err_catcher(name=__name__)
	def import3dObject(self, origin, UUID, toolData, update=False):
		comp = self.getCurrentComp()
		flow:FlowView_ = comp.CurrentFrame.FlowView

		if self.sm_checkCorrectComp(comp):
			comp.Lock()
			comp.StartUndo("Import 3D Object")

			flow.InsertBookmark("3dObject_Import")
			result = self.wrapped_import3dObject(origin, UUID, toolData, comp=comp, update=update)

			comp.EndUndo()
			comp.Unlock()
		else:
			logger.warning(f"ERROR: Unable to import 3d object")
			return {"result": False, "doImport": False}

		return result


	@err_catcher(name=__name__)
	def wrapped_import3dObject(self, origin, UUID, toolData, comp, update=False):
		importRes = False

		format = toolData["format"]

		#	Add new 3d Loader if not update or Tool is not in the Comp
		if not update or not Fus.toolExists(comp, UUID):
			try:
				#	Add tooltype based on format
				if format == ".fbx":
					toolType = "SurfaceFBXMesh"
				elif format == ".abc":
					toolType = "SurfaceAlembicMesh"
				else:
					logger.warning(f"ERROR:  Format not supported: {format}")
					self.core.popup(f"ERROR:  Format not supported: {format}")
					return False

				#	Add 3d Tool
				ldr3d = Fus.addTool(comp, toolType, toolData)

				logger.debug(f"Imported 3d object: {toolData['product']}")

			except Exception as e:
				logger.warning(f"ERROR: Unable to import 3d object:\n{e}")
				return {"result": False, "doImport": False}
			
			if ldr3d:
				importRes = True
		
		#	Update 3d Loader
		else:
			try:
				#	Get tool
				tool = Fus.getToolByUID(comp, UUID)
				#	 Update tool data
				ldr3d = Fus.configureTool(tool, toolData)

				logger.debug(f"Updated Loader3d: {toolData['nodeName']}")
				importRes = True

			except Exception as e:
				logger.warning(f"ERROR: Failed to update Loader3d:\n{e}")

			if ldr3d:
				importRes = True

		return {"result": importRes, "doImport": importRes}


	#	Creates simple 3d scene - adds merge3d and render3d
	@err_catcher(name=__name__)
	def create3dScene(self, origin, UUID):
		comp = self.getCurrentComp()
		if self.sm_checkCorrectComp(comp):
			comp.Lock()
			comp.StartUndo("Create 3D Scene")	

			self.wrapped_create3dScene(origin, UUID)

			comp.EndUndo()
			comp.Unlock()
		else:
			logger.warning(f"ERROR: Unable to create 3d scene")

	
	#	Creates simple 3d scene - adds merge3d and render3d
	@err_catcher(name=__name__)
	def wrapped_create3dScene(self, origin, UUID):		
		try:
			Fus3d.create3dScene(self, origin, UUID)
			logger.debug(f"Created 3d Scene for {UUID}")

		except Exception as e:
			logger.warning(f"ERROR: Unable to create 3d scene:\n{e}")
		

	#	Uses Fusion UI Menu to import FBX or ABC scene
	@err_catcher(name=__name__)
	def importLegacy3D(self, origin:Legacy3D_ImportClass, UUID, nodeData, update=False):
		comp:Composition_ = self.getCurrentComp()
		flow:FlowView_ = comp.CurrentFrame.FlowView

		# Check that we are not importing in a comp different than the one we started the stateManager from
		if self.sm_checkCorrectComp(comp):
			comp.Lock()
			comp.StartUndo("Import Legacy3D")

			flow.InsertBookmark("3dImportBM") # Save where the view is at the time of import.
			result:dict[str, bool] = self.wrapped_importLegacy3D(origin, UUID, nodeData, update)

			comp.EndUndo()
			comp.Unlock()
		else:
			logger.warning(f"ERROR: Unable to import 3D Scene")
			return {"result": False, "doImport": False}

		return result


	@err_catcher(name=__name__)
	def wrapped_importLegacy3D(self, origin:Legacy3D_ImportClass, UUID, nodeData, update=False, doImport=True):
		comp:Composition_ = self.getCurrentComp()
		flow:FlowView_ = comp.CurrentFrame.FlowView

		#	Add new 3D Scene
		try:
			#	Import file
			fileName:tuple[str, str] = os.path.splitext(os.path.basename(nodeData["Filepath"]))
			origin.setName = ""
			result:bool = False
			
			# check if there is an active tool or selection.
			# if not, get the last clicked pos.
			atx, aty = Fus.getRefPosition(comp, flow)

			#	Get Extension
			format:str = fileName[1].lower()
			nodeData["format"] = format
			if not os.path.exists(nodeData["Filepath"]):
				QMessageBox.warning(
					origin.core.messageParent, "Warning", "File %s does not exists" % nodeData["Filepath"]
				)
				return {"result": False, "doImport": False}
			else:
				pass
			
			#	Get Extension
			ext = fileName[1].lower()
			#	Check if Image Format is supported
			if ext not in self.legacyImportHandlers:
				self.core.popup(f"Import format '{ext}' is not supported")
				logger.warning(f"Import format '{ext}' is not supported")
				return {"result": False, "doImport": doImport}

			else:
				# Do the importing
				result = self.legacyImportHandlers[ext]["importFunction"](nodeData["Filepath"], origin)

			# After import update the stateManager interface
			if result:
				initcoords:tuple = (atx, aty)
				result = Fus3d.createLegacy3DScene(origin, comp, flow, fileName, nodeData, UUID, initcoords)
				
				logger.debug(f"Imported Legacy3D Scene: {nodeData['product']}")

			return {"result": result, "doImport": doImport}
		
		except Exception as e:
			logger.warning(f"ERROR: Unable to import Legacy3D Scene:\n{e}")
			return {"result": False, "doImport": False}


	@err_catcher(name=__name__)
	def importLegacyAbc(self, Filepath, origin):
		result = Fus3d.importLegacyAbc(Filepath, self.fusion, origin)
		return result


	@err_catcher(name=__name__)
	def importLegacyFbx(self, Filepath, origin):
		result = Fus3d.importLegacyFbx(Filepath, self.fusion, origin)
		return result



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
	def getMatchingStateDataFromUID(self, toolUID):
		comp = self.getCurrentComp()
		stateDataRaw = json.loads(self.sm_readStates(self))

		# Iterate through the states to find the matching state dictionary
		stateDetails = None
		for stateData in stateDataRaw["states"]:
			if stateData.get("toolUID") == toolUID:
				stateDetails = stateData
				logger.debug(f"State data found for: {Fus.getToolNameByUID(comp, toolUID)}")
				return stateDetails

		logging.warning(f"ERROR: No state details for:  {toolUID}")
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


	#	Adds a Scale tool if the Scale override is used by the RenderGroup
	@err_catcher(name=__name__)
	def addScaletool(self, comp, sv, scaleOvrCode):
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
			logger.warning(f"ERROR: Could not add Scale tool: {e}")


	#	Deletes the temp Scale tools
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

		for toolUID in renderStates:
			#	Get State data from Comp
			stateData = self.getMatchingStateDataFromUID(toolUID)
			toolName = Fus.getToolNameByUID(comp, toolUID)

			#	Exits if unable to get state data
			if not stateData:
				logger.warning(f"ERROR: Unable to configure RenderComp for {toolName}")

			sv = Fus.getToolByUID(comp, toolUID)
			Fus.setPassThrough(comp, toolUID=toolUID, passThrough=False)

			#	Add Scale tool if scale override is above 100%
			scaleOvrType, scaleOvrCode = self.getScaleOverride(rSettings)
			if scaleOvrType == "scale":
				self.addScaletool(comp, sv, scaleOvrCode)

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
			toolData = {"toolName": toolName,
						"filepath": self.outputPath,
			   			"format": extension,
						"fuseFormat": self.getFuseFormat(extension)}

			self.configureRenderNode(toolUID, toolData)

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

			toolUID = rSettings["toolUID"]

			sv = Fus.getToolByUID(comp, toolUID)

			if sv:
				toolData = {"filepath": outputName,
							"version": rSettings["version"],
			   				"format": rSettings["format"],
							"fuseFormat": rSettings["fuseFormat"]
							}
				
				self.configureRenderNode(toolUID, toolData)
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
					self.addScaletool(comp, sv, scaleOvrCode)

				#	Gets render args from override settings
				renderCmd = self.makeRenderCmd(comp, rSettings)

				#	Minimize the State Manager
				origin.stateManager.showMinimized()	

				#	Renders with override args
				comp.Render({**renderCmd, 'Tool': sv, "Wait": True})

				#	Remove any temp Scale tools
				self.deleteTempScaleTools()

				#	Reset Comp settings to Original
				self.loadOrigCompSettings(comp, origCompSettings)

				#	Un-Minimize the State Manager
				# self.stateManager.showNormal()	

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

			#	Minimize the State Manager
			origin.stateManager.showMinimized()	

			#	Renders with override args
			comp.Render({**renderCmd, "Wait": True})

			#	Remove any temp Scale tools
			self.deleteTempScaleTools()

			#	Reset Comp settings to Original
			self.loadOrigCompSettings(comp, self.origCompSettings)

			#	Reconfigure pass-through of Savers
			self.origSaverStates("load", comp, self.origSaverList)

			#	Un-Minimize the State Manager
			# self.stateManager.showNormal()	

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

		details["version"] = Helper.createUUID(simple=True)
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

		#	Remove any temp Scale tools
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
				

	@err_catcher(name=__name__)
	def create3DRenderNode(self, stateUID):
		comp:Composition_ = self.getCurrentComp()
		flow:FlowView_ = comp.CurrentFrame.FlowView
		try:
			scenetool = Fus.getToolByUID(comp, stateUID)
			if scenetool:
				x:float = 0.0
				y:float = 0.0
				x, y = flow.GetPosTable(scenetool).values()
				mrg:Tool_ = comp.AddTool("Merge3D", x, y)
				flow.SetPos(mrg, x+1.5, y)
				ren:Tool_ = comp.AddTool("Renderer3D", x, y)
				flow.SetPos(ren, x+3, y)

				if scenetool.Name.startswith("ROOT_"):
					product = scenetool.Name.split("ROOT_")[1]
					mrg.SetAttrs({'TOOLS_Name' : "3DSceneMerge_" + product})
					ren.SetAttrs({'TOOLS_Name' : "3DRender_" + product})
				
				mrg.ConnectInput("SceneInput1", scenetool)
				ren.ConnectInput("SceneInput", mrg)

				flow.Select()
				flow.Select(mrg)
				flow.Select(ren)
				Fus.focusOnTool(comp, mrg, 1.0)

		except Exception as e:
			logger.warning(f"Error: {e} (Failed to create 3DScene correctly)")


	@err_catcher(name=__name__)
	def sm_view_FocusStateTool(self, stateUID):
		comp:Composition_ = self.getCurrentComp()
		focustool = Fus.getToolByUID(comp, stateUID)

		if focustool:
			Fus.focusOnTool(comp, focustool)
		else:
			self.core.popup("No state tool was found",  severity="info")


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
	def sm_render_managerChanged(self, origin, isPandora):
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
	def deleteNodes(self, stateUID):
		comp:Composition_ = self.getCurrentComp()
		comp.StartUndo("delete Legacy3D Nodes")
		Fus3d.deleteTools(comp, stateUID)
		comp.EndUndo()



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
		flow:FlowView_ = comp.CurrentFrame.FlowView
		# deselect all nodes
		flow.Select()

		toolsToSelectUID = Fus.getConnectedNodes(comp, nodeUIDs)
		
		if not toolsToSelectUID:
			logger.debug("There are not Loaders associated with this task.")
			self.core.popup("There are no loaders for this task.", severity="info")
			return
				
		#	Select all tools
		for toolUID in toolsToSelectUID:
			try:
				if Fus.toolExists(comp, toolUID):
					tool = Fus.getToolByUID(comp, toolUID)
					flow.Select(tool, True)
			except:
				pass

	@err_catcher(name=__name__)
	def colorLegacy3DTaskNodes(self, stateUID, color):
		comp = self.getCurrentComp()
		# in Legacy3d we give an empty list to the parameter with the stateIdinside as only param.
		statenodesuids:list[str] = Fus3d.getStateNodesList(comp, stateUID)
		toolsToColor:list[Tool_] = Fus3d.getToolsFromNodeList(comp, statenodesuids)

		#	If the RGB is the Clear Color code
		for tool in toolsToColor:
			try:
				if color['R'] == 0.000011 and color['G'] == 0.000011 and color['B'] == 0.000011:
					tool.TileColor = None
				else:
					tool.TileColor = color
					logger.debug(f"Set color of tool: {tool.Name}")
			except:
				logger.warning(f"ERROR: Cannot set color of tool: {tool.Name}.")


	#	Colors tools in Comp
	@err_catcher(name=__name__)
	def colorTools(self, toolsToColor, color):
		comp = self.getCurrentComp()

		#	Handle if Passed Single Tool
		if not isinstance(toolsToColor, list):
			toolsToColor = [toolsToColor]

		for tool in toolsToColor:
			#	If the RGB is the Clear Color code
			if color['R'] == 0.000011 and color['G'] == 0.000011 and color['B'] == 0.000011:
				try:
					tool.TileColor = None
				except:
					logger.warning(f"ERROR: Unable to clear the color of the Loader: {tool}.")
			else:
				try:
					tool.TileColor = color
					logger.debug(f"Set color of tool: {tool}")
				except:
					logger.warning(f"ERROR: Cannot set color of tool: {tool}")




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
		origin.b_createImport.deleteLater()

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


		#Set the comp used when sm was opened for reference when saving states.
		comp = self.getCurrentComp()
		self.comp = comp

		#Set State Manager Data on first open.
		if Fus.sm_readStates(comp) is None:
			self.setDefaultState()

		self.MP_stateManager = origin

		
		# Add MenuItems
		origin.actionSortImageLoaders = QAction(origin)
		origin.actionSortImageLoaders.setObjectName(u"actionSortImageLoaders")
		origin.actionSortImageLoaders.setText(QCoreApplication.translate("mw_StateManager", u"Sort Image Loaders", None))
		origin.actionSortImageLoaders.triggered.connect(lambda: self.sortLoaders(comp, getfeedback=True))
		#.
		origin.actionSelectImageLoaders = QAction(origin)
		origin.actionSelectImageLoaders.setObjectName(u"actionSelectImageLoaders")
		origin.actionSelectImageLoaders.setText(QCoreApplication.translate("mw_StateManager", u"Select Image Loaders", None))
		origin.actionSelectImageLoaders.triggered.connect(self.selectAllStateLoaders)
		#.
		origin.menuAbout.addSeparator()
		origin.menuAbout.addAction(origin.actionSortImageLoaders)
		origin.menuAbout.addAction(origin.actionSelectImageLoaders)
		origin.menuAbout.addSeparator()
		##

		try:
			self.core.plugins.monkeyPatch(origin.rclTree, self.rclTree, self, force=True)
			self.core.plugins.monkeyPatch(self.core.mediaProducts.getVersionStackContextFromPath,
								 			self.getVersionStackContextFromPath,
											self,
											force=True)
			self.core.plugins.monkeyPatch(origin.shotCam, self.shotCam, self, force=True)
			self.core.plugins.monkeyPatch(origin.showStateMenu, self.showStateMenu, self, force=True)
			self.core.plugins.monkeyPatch(origin.pasteStates, self.pasteStates, self, force=True)
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
				self.smUI.resize(900, self.smUI.size().height())
				self.smUI.resize(800, self.smUI.size().width())
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
		

	#	This is called from the import buttons in the SM (Import Image and Import 3D) or called from outside code
	@err_catcher(name=__name__)
	def addImportState(self, origin, stateType, useUi=True, settings=None):
		"""
		for Image_Import settings could be a qt item data or Prism Identifier context, but must be a dict and contain:
		
		{'displayName',			(including '2d' or 'external' if applicable)
		'hierarchy',
		'identifier',
		'itemType',				('shot' or 'asset')
		'mediaType',			('3drenders' etc)
		'path',
		'project_name',
		'project_path',
		'sequence',				(if tiemType is 'shot')
		'shot',					(if tiemType is 'shot')
		'asset',				(if tiemType is 'asset')
		'type'					('shot' or 'asset')
		}
		
		"""


		comp = self.getCurrentComp()	
		if self.sm_checkCorrectComp(comp):
			#	Not for passed settings
			if useUi:
				importStates = []
				#	Gets selected item from the StateManager list - to allow for adding to folder
				curSel = origin.getCurrentItem(origin.activeList)
				if (origin.activeList == origin.tw_import
					and curSel is not None
					and curSel.ui.className == "Folder"
					):
					parent = curSel
				else:
					parent = None
				#	Get types of States available
				states = origin.stateTypes
				#	Gets all available State of a given type
				for state in states:
					importStates += getattr(origin.stateTypes[state], "stateCategories", {}).get(stateType, [])
				#	 If there is only one State, call it immediatly
				if len(importStates) == 1:
					origin.createState(importStates[0]["stateType"], parent=parent, setActive=True)
				#	If there is more than one, create a submenu for the States
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

			#	If passed settings just call the State directly ('Image_Import')
			else:
				origin.createState(stateType, parent=None, setActive=False, settings=settings)


	@err_catcher(name=__name__)
	def addRenderGroup(self, origin):
		comp = self.getCurrentComp()	
		if self.sm_checkCorrectComp(comp):
			origin.createState("RenderGroup")


	##########################################
	#                                        #
	################# POPUPS #################
	#                                        #
	##########################################	
		
	# @err_catcher(name=__name__)
	# def importPopup(self, text, title=None, buttons=None, icon=None, parent=None, checked=False):
	# 	title = title or "Prism"
	# 	buttons = buttons or ["Yes", "No"]
	# 	parent = parent or getattr(self.core, "messageParent", None)

	# 	dialog = ImageImportDialogue(text, title, buttons, parent)
	# 	dialog.checkbox.setChecked(checked)
	# 	result = dialog.exec_()

	# 	# Check if dialog was accepted or rejected
	# 	if result == QDialog.Accepted:
	# 		# Return the clicked button text and the checkbox state
	# 		return dialog.clicked_button_text, dialog.checkbox_checked
	# 	else:
	# 		# Handle the "X" case: Return None or default values
	# 		return None, dialog.checkbox.isChecked()
		

	# @err_catcher(name=__name__)
	# def updateMsgPopup(self, updateMsgList, parent=None):
	# 	parent = parent or getattr(self.core, "messageParent", None)

	# 	dialog = UpdateDialog(updateMsgList, parent)
	# 	dialog.exec_()


		
	################################################
	#                                              #
	#        	 MONKEYPATCHED FUNCTIONS           #
	#                                              #
	################################################

	#Right click menu from nodes on state manager to get previous versions.
	@err_catcher(name=__name__)
	def rclTree(self, pos, activeList):
		logger.debug("Loading patched function: 'rclTree'")
		if self.sm_checkCorrectComp(self.getCurrentComp()):
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
	def showStateMenu (self, listType=None, useSelection=False):
		logger.debug("Loading patched function: 'showStateMenu'")
		
		comp = self.getCurrentComp()
		if self.sm_checkCorrectComp(comp):
			sm = self.MP_stateManager			
			globalPos = QCursor.pos()
			parentState = None
			if useSelection:
				listWidget = sm.tw_import if listType == "Import" else sm.tw_export
				if listWidget == sm.activeList:
					parentState = sm.getCurrentItem(sm.activeList)
			else:
				pos = sm.activeList.mapFromGlobal(globalPos)
				idx = sm.activeList.indexAt(pos)
				parentState = sm.activeList.itemFromIndex(idx)

			if parentState and parentState.ui.className != "Folder":
				parentState = None

			menu = sm.getStateMenu(listType, parentState)
			menu.exec_(globalPos)
			# self.core.plugins.callUnpatchedFunction(sm.showStateMenu, listType=listType, useSelection=useSelection)

		else:
			logger.warning(f"ERROR: Unable to to create state")

	@err_catcher(name=__name__)
	def pasteStates(self):
		logger.debug("Loading patched function: 'showStateMenu'")
		
		comp = self.getCurrentComp()
		if self.sm_checkCorrectComp(comp):
			sm = self.MP_stateManager

			cb = QClipboard()
			try:
				rawText = cb.text("plain")[0]
			except:
				QMessageBox.warning(
					sm.core.messageParent,
					"Paste states",
					"No valid state data in clipboard.",
				)
				return

			sm.loadStates(rawText)

			sm.showState()
			sm.activeList.clearFocus()
			sm.activeList.setFocus()

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
	# @err_catcher(name=__name__)
	# def updateTasks(self, *args, **kwargs):
	# 	logger.debug("Loading patched function: 'mediaBrowser.updateTasks'")

	# 	mediabrowser = self.MP_mediaBrowser

	# 	self.core.plugins.callUnpatchedFunction(mediabrowser.updateTasks, *args, **kwargs)
	# 	self.onMediaBrowserTaskUpdate(mediabrowser)


	#	This imports shotcams as a legacy
	@err_catcher(name=__name__)
	def shotCam(self):
		logger.debug("Loading state manager patched function: 'shotCam'")
		if self.sm_checkCorrectComp(self.getCurrentComp()):
			sm = self.MP_stateManager

		sm.saveEnabled = False
		for i in sm.states:
			if i.ui.className == "Legacy3D_Import" and i.ui.taskName == "ShotCam":
				mCamState = i.ui
				camState = i

		if "mCamState" in locals():
			mCamState.importLatest()
			sm.selectState(camState)
		else:
			fileName = sm.core.getCurrentFileName()
			fnameData = sm.core.getScenefileData(fileName)
			if not (
				os.path.exists(fileName)
				and sm.core.fileInPipeline(fileName)
			):
				sm.core.showFileNotInProjectWarning(title="Warning")
				sm.saveEnabled = True
				return False

			if fnameData.get("type") != "shot":
				msgStr = "Shotcams are not supported for assets."
				sm.core.popup(msgStr)
				sm.saveEnabled = True
				return False

			if sm.core.getConfig("globals", "productTasks", config="project"):
				fnameData["department"] = os.getenv("PRISM_SHOTCAM_DEPARTMENT", "Layout")
				fnameData["task"] = os.getenv("PRISM_SHOTCAM_TASK", "Cameras")

			filepath = sm.core.products.getLatestVersionpathFromProduct(
				"_ShotCam", entity=fnameData
			)
			
			if not filepath:
				sm.core.popup("Could not find a shotcam for the current shot.")
				sm.saveEnabled = True
				return False

			sm.createState("Legacy3D_Import", importPath=filepath, setActive=True)

		sm.setListActive(sm.tw_import)
		sm.activateWindow()
		sm.activeList.setFocus()
		sm.saveEnabled = True
		sm.saveStatesToScene()




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


# #	Popup for update message
# class UpdateDialog(QDialog):
#     def __init__(self, updateMsgList, parent=None):
#         super().__init__(parent)
#         self.setWindowTitle("Update Information")

#         layout = QVBoxLayout()

#         #	Add the "Updates" header at the top
#         header_label = QLabel("Updates:")
#         header_font = QFont()
#         header_font.setBold(True)
#         header_label.setFont(header_font)
#         layout.addWidget(header_label)

#         #	Create the table
#         self.table = QTableWidget()
#         self.table.setRowCount(len(updateMsgList))
#         self.table.setColumnCount(2)

#         #	Hide table lines and numbers
#         self.table.verticalHeader().setVisible(False)
#         self.table.horizontalHeader().setVisible(False)
#         self.table.setShowGrid(False)

#         #	Reduce the space between cells
#         self.table.setContentsMargins(0, 0, 0, 0)
#         self.table.setStyleSheet("QTableWidget::item { padding: 0px; }")

#         #	Get the width of the longest text in the first column
#         font_metrics = QFontMetrics(self.font())
#         maxWidth_firstCol = 0
#         maxWidth_secondCol = 0

#         for rowData in updateMsgList:
#             #	First column
#             textFirst = str(rowData[0])
#             textWidth_first = font_metrics.horizontalAdvance(textFirst)
#             if textWidth_first > maxWidth_firstCol:
#                 maxWidth_firstCol = textWidth_first

#             #	Second column
#             textSecond = str(rowData[1])
#             textWidth_second = font_metrics.horizontalAdvance(textSecond)
#             if textWidth_second > maxWidth_secondCol:
#                 maxWidth_secondCol = textWidth_second

#         #	Add margin for both columns
#         firstColumn_width = maxWidth_firstCol + 20
#         secondColumn_width = maxWidth_secondCol + 20

#         #	Populate the table with data
#         for rowIndex, rowData in enumerate(updateMsgList):
#             for colIndex, cellData in enumerate(rowData):
#                 item = QTableWidgetItem(str(cellData))
#                 item.setFlags(Qt.NoItemFlags)
#                 self.table.setItem(rowIndex, colIndex, item)

#         #	Set column widths
#         self.table.setColumnWidth(0, firstColumn_width)
#         self.table.setColumnWidth(1, secondColumn_width)

#         #	Last column stretches
#         self.table.horizontalHeader().setStretchLastSection(False)

#         #	Add the table
#         layout.addWidget(self.table)

#         # Add a close button
#         b_close = QPushButton("Close")
#         b_close.clicked.connect(self.close)
#         layout.addWidget(b_close)

#         # Set the dialog layout
#         self.setLayout(layout)

#         # Adjust the window width to match the table content
#         totalTable_width = firstColumn_width + secondColumn_width + 50
#         self.resize(totalTable_width, self.table.verticalHeader().length() + 100)
