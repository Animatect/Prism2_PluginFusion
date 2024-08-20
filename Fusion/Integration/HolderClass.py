
# import platform
# import subprocess
import sys
import os
import time
from datetime import datetime
import PrismInit
import openPrismWindows as opw
import BlackmagicFusion as bmd

import manageprismpaths

from qtpy import QtCore, QtGui, QtWidgets


class PrismHolderClass(object):
	def __init__(self, UIManager, fusion):
		self.fusion = fusion

		self.ui = UIManager
		self.disp = bmd.UIDispatcher(self.ui)
		self.pcore = None

		# Set Global Variable
		self.bootstrapPrism()
				

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

		# Add your GUI element based event Handlers here:
		self.dlg.On.Bootstrap.Clicked = self.bootstrapPrism
		self.dlg.On.rcip.Clicked = self.runCodeInProcess
		self.dlg.On.btn_lockFile.Clicked = self.on_btn_lockFile
		# Prism UI Functions
		self.dlg.On.btn_projectbrowser.Clicked = self.on_btn_projectbrowser_clicked
		self.dlg.On.btn_saveversion.Clicked = self.on_btn_saveversion_clicked
		self.dlg.On.btn_savecomment.Clicked = self.on_btn_savecomment_clicked
		self.dlg.On.btn_statemanager.Clicked = self.on_btn_statemanager_clicked
		self.dlg.On.btn_prismsettings.Clicked = self.on_btn_prismsettings_clicked

		# self.dlg.Show()
		self.disp.RunLoop()
		self.dlg.Hide()

	# The window was closed
	def _func(self, ev):
		self.disp.ExitLoop()

	def bootstrapPrism(self, ev=None):
		global global_Prism # Declare global_var as global
		global_Prism = prismStateHolderClass()
	
	def runCodeInProcess(self, ev=None):
		global_Prism.runCodeInProcess()

	def on_btn_lockFile(self, ev=None):
		global_Prism.lockFile()
	
	# Add your GUI element based event functions here: ev is the event object
	def on_btn_projectbrowser_clicked(self, ev):
		if global_Prism.pcore.getPlugin("Fusion").pbUI:
			print("alreadyOppened")
		else:
			opw.openProjectBrowser(global_Prism.pcore)

	def on_btn_saveversion_clicked(self, ev):
		opw.runPrismSaveScene(global_Prism.pcore)

	def on_btn_savecomment_clicked(self, ev):
		opw.openPrismSaveWithComment(global_Prism.pcore)

	def on_btn_statemanager_clicked(self, ev):
		if global_Prism.pcore.getPlugin("Fusion").smUI:
			print("alreadyOppened")
		else:
			opw.openPrismStateManager(global_Prism.pcore)

	def on_btn_prismsettings_clicked(self, ev):
		opw.openPrismSettings(global_Prism.pcore)



class prismStateHolderClass(object):
	def __init__(self) -> None:
		self.pcore = None
		self.saveUI = None
		self.smUI = None
		self.pbUI = None
		self.prefUI = None
		self.fusion = bmd.scriptapp("Fusion")

		self.createPcore()
	
	def createPcore(self):		
		qapp = QtWidgets.QApplication.instance()
		if qapp == None:
			qapp = QtWidgets.QApplication(sys.argv)
		popup = opw.popupNoButton("Starting Prism", qapp)
		pcore = PrismInit.prismInit()
		pcore.setActiveStyleSheet("Fusion")

	# 	# It's easier to just manage the lockfiles ourselves via a loop running the PrismLoop.py process.
	# 	self.fusion.SetData("PrismLocked", pcore.getLockScenefilesEnabled())
	# 	#
	
	# 	current_time = datetime.now()
	# 	date_time_str = self.fusion.GetData("PrismLoopTime")
	# 	if date_time_str:
	# 		previous_time = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S")
	# 	else: # First time to set it.
	# 		self.fusion.SetData("PrismLoopTime", current_time.strftime("%Y-%m-%d %H:%M:%S"))
	# 		previous_time = datetime(1, 1, 1)
	# 	print("date_time_str: ", date_time_str)
	# 	# Calculate the elapsed time
	# 	elapsed_time = current_time - previous_time
	# 	seconds_passed = elapsed_time.total_seconds()

	# 	if seconds_passed > 15:
	# 		# Get the path to the timer script
	# 		worker_script = os.path.join(self.get_script_dir(), 'PrismLoop.py')
	# 		self.fusion.RunScript(worker_script)

		popup.close()
		self.checkForSanityMessage(qapp)
		# Assign
		self.pcore = pcore

	def get_script_dir(self):
		# Try to determine the script's directory
		if hasattr(sys, 'frozen'):  # PyInstaller
			script_dir = os.path.dirname(sys.executable)
		else:
			script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
		return script_dir

	# Make a test to see if windows are open.
	def checkForSanityMessage(self,qapp):
		appexists = False
		if qapp is not None:
			for widget in qapp.topLevelWidgets():
				if isinstance(widget, QtWidgets.QMessageBox):
					appexists = True
					# print(widget)
					# widget.close()
			if appexists:
				qapp.exec_()
	
	# Handle Locking.
	def lockFile(self):
		print("locking")
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
		print("Object Exists")
		fusion = bmd.scriptapp("Fusion")
		comp = fusion.GetCurrentComp()
		command = comp.GetData("cmd") # set the data in a variable from a diferent process comp.SetData("cmd", "print(global_Prism)")
		# Command to run
		code_string = command
		exec(code_string)

		print("finish")

