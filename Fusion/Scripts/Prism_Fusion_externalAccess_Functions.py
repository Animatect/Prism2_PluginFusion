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
import platform
import logging

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

from PrismUtils.Decorators import err_catcher_plugin as err_catcher

logger = logging.getLogger(__name__)


class Prism_Fusion_externalAccess_Functions(object):
	def __init__(self, core, plugin):
		self.core = core
		self.plugin = plugin

		#	Register callbacks
		try:
			self.core.registerCallback(
				"userSettings_saveSettings",
				self.userSettings_saveSettings,
				plugin=self.plugin,
			)
			self.core.registerCallback(
				"userSettings_loadSettings",
				self.userSettings_loadSettings,
				plugin=self.plugin,
			)
			self.core.registerCallback(
				"getPresetScenes", 
				self.getPresetScenes, 
				plugin=self.plugin
			)
			ssheetPath = os.path.join(
				self.pluginDirectory,
				"UserInterfaces",
				"FusionStyleSheet"
			)
			self.core.registerCallback(
				"getIconPathForFileType", self.getIconPathForFileType, plugin=self
				)
			logger.debug("Registered callbacks")

		except Exception as e:
			logger.warning(f"ERROR: Registering callbacks failed:\n {e}")
		
		self.core.registerStyleSheet(ssheetPath)
		

	@err_catcher(name=__name__)
	def userSettings_loadUI(self, origin, tab):
		#	Group box for the Prism options
		origin.gb_prismFusionOptions = QGroupBox()
		lo_prismFusionOptions = QVBoxLayout()
		origin.gb_prismFusionOptions.setLayout(lo_prismFusionOptions)

		#	Start mode layout
		lo_prismStartMode = QHBoxLayout()
		origin.l_prismStartMode = QLabel("Prism Start Mode:       ")
		origin.cb_prismStartMode = QComboBox()
		
		#	Add options to the combo box
		origin.cb_prismStartMode.addItems(["automatic", "prompt", "manual"])
		origin.cb_prismStartMode.setCurrentIndex(1)
		
		#	Add label and combo box to the horizontal layout
		lo_prismStartMode.addWidget(origin.l_prismStartMode)
		lo_prismStartMode.addWidget(origin.cb_prismStartMode)
		
		#	Add spacer on the right side
		spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
		lo_prismStartMode.addItem(spacer)
		
		#	Add start layout to the groupbox
		lo_prismFusionOptions.addLayout(lo_prismStartMode)
		
		#	Add a small vert spacer between the combo box layout and checkbox layout
		vertSpacer = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed)
		lo_prismFusionOptions.addItem(vertSpacer)
		
		#	Create a horz layout for the Dev Menu
		lo_installDevTools = QHBoxLayout()
		origin.l_installDevTools = QLabel("Install Prism Developer Menu With Plugin:")
		origin.chk_installDevTools = QCheckBox()
		
		#	Add label and checkbox to the horz layout
		lo_installDevTools.addWidget(origin.l_installDevTools)
		lo_installDevTools.addWidget(origin.chk_installDevTools)

		#	Add spacer on the right side
		spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
		lo_installDevTools.addItem(spacer)
		
		#	Add the Dev menu layout to the group box layout
		lo_prismFusionOptions.addLayout(lo_installDevTools)
		
		#	Add the Prism Fusion Options group box to the tab layout
		tab.layout().addWidget(origin.gb_prismFusionOptions)

		#	ToolTips
		tip = ("Prism launch behaviour when Fusion opens:\n\n"
		 		"   Automatic:   Prism starts whenever Fusion is opened.\n"
				"   Prompt:       A popup will be displayed to start Prism when Fusion is opened.\n"
				"   Manual:       Prism is started using the 'RESET PRISM' menu item in the Prism menu of Fusion.")
		origin.l_prismStartMode.setToolTip(tip)
		origin.cb_prismStartMode.setToolTip(tip)

		tip = "Install Prism Development menu to Fusion when adding the integration."
		origin.l_installDevTools.setToolTip(tip)
		origin.chk_installDevTools.setToolTip(tip)


		# origin.gb_bldAutoSave = QGroupBox("Auto save renderings")
		# lo_bldAutoSave = QVBoxLayout()
		# origin.gb_bldAutoSave.setLayout(lo_bldAutoSave)
		# origin.gb_bldAutoSave.setCheckable(True)
		# origin.gb_bldAutoSave.setChecked(False)

		# origin.chb_bldRperProject = QCheckBox("use path only for current project")

		# w_bldAutoSavePath = QWidget()
		# lo_bldAutoSavePath = QHBoxLayout()
		# origin.le_bldAutoSavePath = QLineEdit()
		# b_bldAutoSavePath = QPushButton("...")

		# lo_bldAutoSavePath.setContentsMargins(0, 0, 0, 0)
		# b_bldAutoSavePath.setMinimumSize(40, 0)
		# b_bldAutoSavePath.setMaximumSize(40, 1000)
		# b_bldAutoSavePath.setFocusPolicy(Qt.NoFocus)
		# b_bldAutoSavePath.setContextMenuPolicy(Qt.CustomContextMenu)
		# w_bldAutoSavePath.setLayout(lo_bldAutoSavePath)
		# lo_bldAutoSavePath.addWidget(origin.le_bldAutoSavePath)
		# lo_bldAutoSavePath.addWidget(b_bldAutoSavePath)

		# lo_bldAutoSave.addWidget(origin.chb_bldRperProject)
		# lo_bldAutoSave.addWidget(w_bldAutoSavePath)
		# tab.layout().addWidget(origin.gb_bldAutoSave)

		# if hasattr(self.core, "projectPath") and self.core.projectPath is not None:
		# 	origin.le_bldAutoSavePath.setText(self.core.projectPath)

		# b_bldAutoSavePath.clicked.connect(
		# 	lambda: origin.browse(
		# 		windowTitle="Select render save path", uiEdit=origin.le_bldAutoSavePath
		# 	)
		# )
		# b_bldAutoSavePath.customContextMenuRequested.connect(
		# 	lambda: self.core.openFolder(origin.le_bldAutoSavePath.text())
		# )
	
	@err_catcher(name=__name__)
	def userSettings_saveSettings(self, origin, settings):
		try:
			if "Fusion" not in settings:
				settings["Fusion"] = {}

			bsPath = self.core.fixPath(origin.le_bldAutoSavePath.text())
			if not bsPath.endswith(os.sep):
				bsPath += os.sep

			if origin.chb_bldRperProject.isChecked():
				if os.path.exists(self.core.prismIni):
					k = "autosavepath_%s" % self.core.projectName
					settings["Fusion"][k] = bsPath
			else:
				settings["Fusion"]["autosavepath"] = bsPath

			settings["Fusion"]["autosaverender"] = origin.gb_bldAutoSave.isChecked()
			settings["Fusion"]["autosaveperproject"] = origin.chb_bldRperProject.isChecked()

			#	Saves Prism Start Mode option
			settings["Fusion"]["prismStartMode"] = origin.cb_prismStartMode.currentText()
			self.setStartmodeConfig(origin.cb_prismStartMode.currentText())


		except Exception as e:
			logger.warning(f"ERROR: Could not save user settings:\n{e}")


	@err_catcher(name=__name__)
	def userSettings_loadSettings(self, origin, settings):
		try:
			if "Fusion" in settings:
				if "autosaverender" in settings["Fusion"]:
					origin.gb_bldAutoSave.setChecked(settings["Fusion"]["autosaverender"])

				if "autosaveperproject" in settings["Fusion"]:
					origin.chb_bldRperProject.setChecked(
						settings["Fusion"]["autosaveperproject"]
					)

				pData = "autosavepath_%s" % getattr(self.core, "projectName", "")
				if pData in settings["Fusion"]:
					if origin.chb_bldRperProject.isChecked():
						origin.le_bldAutoSavePath.setText(settings["Fusion"][pData])

				if "autosavepath" in settings["Fusion"]:
					if not origin.chb_bldRperProject.isChecked():
						origin.le_bldAutoSavePath.setText(
							settings["Fusion"]["autosavepath"]
						)
				
				#	Loads Fusion start mode  setting from Prism Config file if exists
				if "prismStartMode" in settings["Fusion"]:
					idx = origin.cb_prismStartMode.findText(settings["Fusion"]["prismStartMode"])
					if idx != -1:
						origin.cb_prismStartMode.setCurrentIndex(idx)
				#	Defaults to Prompt mode
				else:
					origin.cb_prismStartMode.setCurrentIndex(1)

		except Exception as e:
			logger.warning(f"ERROR: Failed to load user settings:\n{e}")


	@err_catcher(name=__name__)
	def getPresetScenes(self, presetScenes):
		try:
			presetDir = os.path.join(self.pluginDirectory, "Presets")
			scenes = self.core.entities.getPresetScenesFromFolder(presetDir)
			presetScenes += scenes

		except Exception as e:
			logger.warning(f"ERROR: Failed to load scene presets:\n{e}")

		
	@err_catcher(name=__name__)
	def getAutobackPath(self, origin):
		autobackpath = ""
		if platform.system() == "Windows":
			autobackpath = os.path.join(
				self.core.getWindowsDocumentsPath(), "Fusion"
			)

		fileStr = "Fusion Scene File ("
		for i in self.sceneFormats:
			fileStr += "*%s " % i

		fileStr += ")"

		return autobackpath, fileStr
	

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
	def copySceneFile(self, origin, origFile, targetPath, mode="copy"):
		pass


	# Saves the Start mode to the Scripts config file
	@err_catcher(name=__name__)
	def setStartmodeConfig(self, mode):
		# Gets user preferences dir (usually My Documents in Windows)
		prefDir = self.core.getUserPrefDir()
		# Gets the Prism InstallLocations file
		self.installLocPath = os.path.join(prefDir, "InstallLocations" + self.core.configs.preferredExtension)
		# Returns the DCC integrations
		integrations = self.core.readYaml(path=self.installLocPath) or {}

		# Retrieve Fusion paths, or return if Fusion integration is missing or empty
		fusionPaths = integrations.get("Fusion")
		if not fusionPaths:
			logger.warning("ERROR: It does not appear that an integration for Fusion has been added yet.")
			return

		# Iterate over each Fusion path and save the config file
		for fusionPath in fusionPaths:
			# Define the PrismAutostart.config filepath
			scriptPath = os.path.join(fusionPath, "Scripts")
			saveConfigPath = os.path.join(scriptPath, "PrismAutostart.config")

			# Check if the Scripts directory exists, else log an error and skip to the next path
			if not os.path.exists(scriptPath):
				logger.warning(f"ERROR: Unable to find Scripts directory at {scriptPath}")
				continue

			# Attempt to write the mode to the config file
			try:
				with open(saveConfigPath, "w") as configFile:
					configFile.write(f"autoStart: {mode}")
				logger.debug(f"Successfully saved mode '{mode}' to {saveConfigPath}")
			except Exception as e:
				logger.warning(f"ERROR: Failed to write to config file at {saveConfigPath}: {e}")
