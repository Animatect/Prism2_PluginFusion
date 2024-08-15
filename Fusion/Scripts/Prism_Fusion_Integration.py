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
# Copyright (C) 2016-2020 Richard Frangenberg
#
# Licensed under GNU GPL-3.0-or-later
#
# This file is part of Prism.
#
# Prism is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Prism is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Prism.  If not, see <https://www.gnu.org/licenses/>.

import os
import sys
import platform
import shutil

try:
	from PySide6.QtCore import *
	from PySide6.QtGui import *
	from PySide6.QtWidgets import *
except:
	from PySide2.QtCore import *
	from PySide2.QtGui import *
	from PySide2.QtWidgets import *

from PrismUtils.Decorators import err_catcher_plugin as err_catcher


class Prism_Fusion_Integration(object):
	def __init__(self, core, plugin):
		self.core = core
		self.plugin = plugin
		self.scripts = [
				"Menu_SaveVersion.py",
				"Menu_SaveComment.py",
				"Menu_OpenProjectBrowser.py",
				"Menu_OpenStateManager.py",
				"Menu_OpenSettings.py",
				"openPrismWindows.py",
				"PrismInit.py",
				"InstallThirdParty.py",
				"LoaderFromSaver.lua",
				"Fusion.ico",
				"ResetPrism.py",
				"HolderClass.py",
				"CallButtons.py",
				"CreateHolder.py",
				"manageprismpaths.py",
				"BlenderOCIOmanager.py",
				"startupDialog.py",
				"emptydialog.py",
			]
		self.devscripts = [
				"pdmExecuteCode.py",
				"sandbox1.py",
		]
		self.configs = [
			"PrismMenu.fu",
			# "PrismEvents.fu",
		]
		self.devconfigs = [
			"PrismDevMenu.fu",
		]
		
		if platform.system() == "Windows":
			self.examplePath = os.path.join(
				os.environ["appdata"], "Blackmagic Design", "Fusion"
			)
		elif platform.system() == "Linux":
			userName = (
				os.environ["SUDO_USER"]
				if "SUDO_USER" in os.environ
				else os.environ["USER"]
			)
			self.examplePath = "/home/%s/.fusion/BlackmagicDesign/Fusion" % userName
		elif platform.system() == "Darwin":
			userName = (
				os.environ["SUDO_USER"]
				if "SUDO_USER" in os.environ
				else os.environ["USER"]
			)
			self.examplePath = (
				"/Users/%s/Library/Application Support/Blackmagic Design/Fusion"
				% userName
			)

	@err_catcher(name=__name__)
	def getExecutable(self):
		execPath = ""
		if platform.system() == "Windows":
			execPath = "C:\\Program Files\\Blackmagic Design\\Fusion 9\\Fusion.exe"

		return execPath

	def addIntegration(self, installPath):
		scripts = self.scripts.copy()
		configs = self.configs.copy()
		# Check if we are installing devtools.
		if self.core.ps:
			userSettingDialog = self.core.ps.findChild(QWidget, "dlg_UserSettings")
			if userSettingDialog:
				if hasattr(userSettingDialog, 'gb_bldInstallDevTools'):
					gb_bldInstallDevTools = getattr(userSettingDialog, 'gb_bldInstallDevTools')
					# self.core.popup(str(gb_bldInstallDevTools.isChecked()))
					if gb_bldInstallDevTools.isChecked():
						scripts.extend(self.devscripts)
						configs.extend(self.devconfigs)
		try:
			if not os.path.exists(installPath):
				QMessageBox.warning(
					self.core.messageParent,
					"Prism Integration",
					"Invalid Fusion path: %s.\nThe path doesn't exist." % installPath,
					QMessageBox.Ok,
				)
				return False

			integrationBase = os.path.join(
				os.path.dirname(os.path.dirname(__file__)), "Integration"
			)
			addedFiles = []

			# "PrismMenu.fu" add a Prism menu, but leads to freezes
			for i in configs:
				origFile = os.path.join(integrationBase, i)
				targetFile = os.path.join(installPath, "Config", i)

				if not os.path.exists(os.path.dirname(targetFile)):
					os.makedirs(os.path.dirname(targetFile))
					addedFiles.append(os.path.dirname(targetFile))

				if os.path.exists(targetFile):
					os.remove(targetFile)

				shutil.copy2(origFile, targetFile)
				addedFiles.append(targetFile)

				with open(targetFile, "r") as init:
					initStr = init.read()
					initStr = initStr.replace(
						"PRISMROOT", '"%s"' % self.core.prismRoot.replace(
							"\\", "/")
					)

				with open(targetFile, "w") as init:
					init.write(initStr)
			
			# .scriptlib Files
			for i in ["PrismInit.scriptlib"]:
				origFile = os.path.join(integrationBase, i)
				targetFile = os.path.join(installPath, "Scripts", i)

				if not os.path.exists(os.path.dirname(targetFile)):
					os.makedirs(os.path.dirname(targetFile))
					addedFiles.append(os.path.dirname(targetFile))

				if os.path.exists(targetFile):
					os.remove(targetFile)

				shutil.copy2(origFile, targetFile)
				addedFiles.append(targetFile)

				with open(targetFile, "r") as init:
					initStr = init.read()

				with open(targetFile, "w") as init:
					initStr = initStr.replace(
						"PRISMROOT", '"%s"' % self.core.prismRoot.replace(
							"\\", "/")
					)
					init.write(initStr)

			for i in scripts:
				file_name, file_extension = os.path.splitext(i)
				origFile = os.path.join(integrationBase, i)
				targetFile = os.path.join(installPath, "Scripts", "Prism", i)

				if not os.path.exists(os.path.dirname(targetFile)):
					os.makedirs(os.path.dirname(targetFile))
					addedFiles.append(os.path.dirname(targetFile))

				if os.path.exists(targetFile):
					os.remove(targetFile)

				shutil.copy2(origFile, targetFile)
				addedFiles.append(targetFile)

				# Do not try to read/write an icon file
				if not file_extension == ".ico":
        
					with open(targetFile, "r") as init:
						initStr = init.read()

					with open(targetFile, "w") as init:
						initStr = initStr.replace(
							"PRISMROOT", '"%s"' % self.core.prismRoot.replace(
								"\\", "/")
						)
						# get path to third party scripts
						initStr = initStr.replace(
							"THIRDPARTY", '"%s"' % os.path.join(os.path.dirname(__file__), 'thirdparty').replace(
								'\\', '/')
						)
						init.write(initStr)

			# for i in ["WritePrism.setting"]:
			#     origFile = os.path.join(integrationBase, i)
			#     targetFile = os.path.join(installPath, "Macros", i)

			#     if not os.path.exists(os.path.dirname(targetFile)):
			#         os.makedirs(os.path.dirname(targetFile))
			#         addedFiles.append(os.path.dirname(targetFile))

			#     if os.path.exists(targetFile):
			#         os.remove(targetFile)

			#     shutil.copy2(origFile, targetFile)
			#     addedFiles.append(targetFile)

			#     with open(targetFile, "r") as init:
			#         initStr = init.read()

			#     with open(targetFile, "w") as init:
			#         initStr = initStr.replace(
			#             "PRISMROOT", '"%s"' % self.core.prismRoot.replace(
			#                 "\\", "/")
			#         )
			#         init.write(initStr)

			if platform.system() in ["Linux", "Darwin"]:
				for i in addedFiles:
					os.chmod(i, 0o777)

			return True

		except Exception as e:
			exc_type, exc_obj, exc_tb = sys.exc_info()

			msgStr = (
				"Errors occurred during the installation of the Fusion integration.\nThe installation is possibly incomplete.\n\n%s\n%s\n%s"
				% (str(e), exc_type, exc_tb.tb_lineno)
			)
			msgStr += "\n\nRunning this application as administrator could solve this problem eventually."

			QMessageBox.warning(self.core.messageParent,
								"Prism Integration", msgStr)
			return False

	def removeIntegration(self, installPath):
		try:
			pFiles = []
			for i in self.configs:
				pFiles.append(
					os.path.join(installPath, "Config", i)
				)
			for i in self.devconfigs:
				pFiles.append(
					os.path.join(installPath, "Config", i)
				)
			
			pFiles.append(os.path.join(installPath, "Scripts", "PrismInit.scriptlib"))

			for file in self.scripts:
				pFiles.append(
					os.path.join(
						installPath, "Scripts", "Prism", file
					)
				)
			for file in self.devscripts:
				pFiles.append(
					os.path.join(
						installPath, "Scripts", "Prism", file
					)
				)

			for i in pFiles:
				if os.path.exists(i):
					os.remove(i)

			pfolder = os.path.join(installPath, "Scripts", "Prism")
			if not os.listdir(pfolder):
				os.rmdir(pfolder)

			return True

		except Exception as e:
			exc_type, exc_obj, exc_tb = sys.exc_info()

			msgStr = (
				"Errors occurred during the removal of the Fusion integration.\n\n%s\n%s\n%s"
				% (str(e), exc_type, exc_tb.tb_lineno)
			)
			msgStr += "\n\nRunning this application as administrator could solve this problem eventually."

			QMessageBox.warning(self.core.messageParent,
								"Prism Integration", msgStr)
			return False

	def updateInstallerUI(self, userFolders, pItem):
		try:
			pluginItem = QTreeWidgetItem([self.plugin.pluginName])
			pItem.addChild(pluginItem)

			pluginPath = self.examplePath

			if pluginPath != None and os.path.exists(pluginPath):
				pluginItem.setCheckState(0, Qt.Checked)
				pluginItem.setText(1, pluginPath)
				pluginItem.setToolTip(0, pluginPath)
			else:
				pluginItem.setCheckState(0, Qt.Unchecked)
				pluginItem.setText(1, "< doubleclick to browse path >")
		except Exception as e:
			exc_type, exc_obj, exc_tb = sys.exc_info()
			msg = QMessageBox.warning(
				self.core.messageParent,
				"Prism Installation",
				"Errors occurred during the installation.\n The installation is possibly incomplete.\n\n%s\n%s\n%s\n%s"
				% (__file__, str(e), exc_type, exc_tb.tb_lineno),
			)
			return False

	def installerExecute(self, fusionItem, result):
		try:
			installLocs = []

			if fusionItem.checkState(0) == Qt.Checked and os.path.exists(
				fusionItem.text(1)
			):
				result["Fusion integration"] = self.core.integration.addIntegration(
					self.plugin.pluginName, path=fusionItem.text(1), quiet=True)
				if result["Fusion integration"]:
					installLocs.append(fusionItem.text(1))

			return installLocs
		except Exception as e:
			exc_type, exc_obj, exc_tb = sys.exc_info()
			msg = QMessageBox.warning(
				self.core.messageParent,
				"Prism Installation",
				"Errors occurred during the installation.\n The installation is possibly incomplete.\n\n%s\n%s\n%s\n%s"
				% (__file__, str(e), exc_type, exc_tb.tb_lineno),
			)
			return False
