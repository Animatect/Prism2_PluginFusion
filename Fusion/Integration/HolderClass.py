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


import sys
import os

import PrismInit
import openPrismWindows as opw
import BlackmagicFusion as bmd


from qtpy import QtWidgets


class PrismHolderClass(object):
	def __init__(self, UIManager, fusion):
		self.fusion = fusion

		self.ui = UIManager
		self.disp = bmd.UIDispatcher(self.ui)
		self.pcore = None

		self.dlg = self.disp.AddWindow(
			{ "WindowTitle": "PrismHolder", 
			"ID": "PrismHolder", 
			"Geometry": [ 300, 100, 200, 250 ], },#xpos,ypos,width,height
			
			[
				self.ui.VGroup(
				{ "Spacing": 5, },
				[
					self.ui.Label({ 
						"ID": "PrismLabel", 
						"Text": "Prism Fusion Menu",
						'Alignment': {'AlignHCenter': True, 'AlignVCenter': True},
					}),
					#
					self.ui.HGroup({},[
					# Add foru buttons that have an icon resource attached and no border shading
					self.ui.Button({
						'ID': 'Bootstrap',
						'Text': 'BootstrapPrism',
						}),
					self.ui.Button({
						'ID': 'rcip',
						'Text': 'runCodeInProcess',
						}),
					self.ui.Button({
						'ID': 'btn_lockFile',
						'Text': 'LockFile',
						}),
					]),
					#
					self.ui.VGap,
					#
					self.ui.Button({
						"ID": "btn_projectbrowser",
						"Text": "Project Browser",
					}),
					#
					self.ui.VGap,
					#
					self.ui.VGroup([
					#
						self.ui.Button({
							"ID": "btn_saveversion",
							"Text": "Save Version", 
						}),
						self.ui.Button({
							"ID": "btn_savecomment",
							"Text": "Save Comment",
						}),
					]),#grpend
					self.ui.VGap,
					#
					self.ui.VGroup([
					#
						self.ui.Button({
							"ID": "btn_statemanager",
							"Text": "State Manager",
						}),
						self.ui.Button({
							"ID": "btn_prismsettings",
							"Text": "Prism Settings",
						}),
					]),#grpend
				]),
			]
			)

		self.itm = self.dlg.GetItems()
		self.dlg.On.PrismHolder.Close = self._func

		# Add Buttons:
		self.dlg.On.Bootstrap.Clicked = self.bootstrapPrism
		self.dlg.On.rcip.Clicked = self.runCodeInProcess
		self.dlg.On.btn_lockFile.Clicked = self.on_btn_lockFile
		# Prism UI Functions
		self.dlg.On.btn_projectbrowser.Clicked = self.on_btn_projectBrowser_clicked
		self.dlg.On.btn_saveversion.Clicked = self.on_btn_saveVersion_clicked
		self.dlg.On.btn_savecomment.Clicked = self.on_btn_saveComment_clicked
		self.dlg.On.btn_statemanager.Clicked = self.on_btn_stateManager_clicked
		self.dlg.On.btn_prismsettings.Clicked = self.on_btn_prismSettings_clicked

		# Set Global Variable
		self.bootstrapPrism()


		# # # # # # # # # # # # #
		#	Hides or Shows the Hidden Menu Window
		# self.dlg.Show()
		self.disp.RunLoop()
		self.dlg.Hide()
		# # # # # # # # # # # # #


	# The window was closed
	def _func(self, ev):
		self.disp.ExitLoop()


	def bootstrapPrism(self, ev=None):
		global global_Prism
		global_Prism = prismStateHolderClass()

	
	def runCodeInProcess(self, ev=None):
		global_Prism.runCodeInProcess()


	def on_btn_lockFile(self, ev=None):
		global_Prism.lockFile()

	
	# Add your GUI element based event functions here: ev is the event object
	def on_btn_projectBrowser_clicked(self, ev):
		if global_Prism.pcore.getPlugin("Fusion").pbUI:
			print("[Prism] Project Browser is already opened")
		else:
			print("[Prism]  Opening Project Browser")
			opw.openProjectBrowser(global_Prism.pcore)


	def on_btn_saveVersion_clicked(self, ev):
		print("[Prism]  Saving Version")
		opw.runPrismSaveScene(global_Prism.pcore)


	def on_btn_saveComment_clicked(self, ev):
		print("[Prism]  Opening Save Dialog")
		opw.openPrismSaveWithComment(global_Prism.pcore)


	def on_btn_stateManager_clicked(self, ev):
		if global_Prism.pcore.getPlugin("Fusion").smUI:
			print("[Prism] State Manager is already opened")
		else:
			print("[Prism]  Opening State Manager")
			opw.openPrismStateManager(global_Prism.pcore)


	def on_btn_prismSettings_clicked(self, ev):
		print("[Prism]  Opening Settings")
		opw.openPrismSettings(global_Prism.pcore)



class prismStateHolderClass(object):
	def __init__(self) -> None:
		self.pcore = None
		self.saveUI = None
		self.smUI = None
		self.pbUI = None
		self.prefUI = None
		self.fusion = bmd.scriptapp("Fusion")

		self.handledSanityPopups = set()

		self.createPcore()

	
	def createPcore(self):		
		print("[Prism] Creating Global Prism Instance")

		#	Check if Prism already exists
		qapp = QtWidgets.QApplication.instance()
		if qapp is None:
			qapp = QtWidgets.QApplication(sys.argv)

		#	Show Starting popup
		popup = opw.popupNoButton("Starting Prism", qapp, centered=True, large=True)

		#	Create Prism Core from Lib function
		pcore = PrismInit.prismInit()

		#	Close the Starting popup
		popup.close()

		if not pcore:
			print("[PRISM ERROR] Unable to create Prism Core.  Please contact the developers.")
			return None

		# Assign pcore
		self.pcore = pcore

#	THIS IS MAYBE WHERE THE EXTRA SANITY CHECKS ARE COMING FROM	
#	THIS SEEMS TO BE WORKING NOW
#	vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv

		# if pcore.pb:														#	NEEDED ????

		# 	print("*** Starting QApplication event loop")					#	TESTING
		# 	qapp.exec_()
		# 	print("*** Exiting QApplication event loop")					#	TESTING

		# else:

		self.checkForSanityPopups(qapp)


	#	Handles the Sanity popups
	def checkForSanityPopups(self, qapp):
		#	Closes all Sanity Popups
		self.closeExistingPopups(qapp)

		#	Itterates through all the existing popups
		if qapp is not None:
			for widget in qapp.topLevelWidgets():
				#	Adds all the QMessage popups to Set once
				if isinstance(widget, QtWidgets.QMessageBox) and widget not in self.handledSanityPopups:
					self.handledSanityPopups.add(widget)
					#	Executes the popups in the Set (Only shows each one once)
					widget.exec_()

	#	Closes all Sanity popups
	def closeExistingPopups(self, qapp):
		if qapp is not None:
			for widget in qapp.topLevelWidgets():
				if isinstance(widget, QtWidgets.QMessageBox):
					widget.close()

#	^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^



	def get_scriptDir(self):
		# Try to determine the script's directory
		if hasattr(sys, 'frozen'):  # PyInstaller
			script_dir = os.path.dirname(sys.executable)
		else:
			script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
		return script_dir
	

	# Handle Locking.
	def lockFile(self):
		print("[Prism] Locking File")
		if self.pcore.getLockScenefilesEnabled():
			if not self.pcore.users.ensureUser():
				return False
			filepaths = list(self.fusion.GetData("NewComps").values())
			for filepath in filepaths:
				os.path.normpath(filepath)
				if not self.pcore.fileInPipeline(filepath=filepath):
					return False
				self.pcore.lockScenefile(filepath)


	# Debug Functions.
	def runCodeInProcess(self):
		print("[Prism] Object Exists")
		fusion = bmd.scriptapp("Fusion")
		comp = fusion.GetCurrentComp()
		command = comp.GetData("cmd") # set the data in a variable from a diferent process comp.SetData("cmd", "print(global_Prism)")
		# Command to run
		code_string = command
		exec(code_string)
