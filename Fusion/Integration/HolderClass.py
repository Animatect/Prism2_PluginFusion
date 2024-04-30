
import platform
import sys
import openPrismWindows
import PrismInit
import subprocess
import openPrismWindows as opw
import BlackmagicFusion as bmd

from PySide2 import QtCore, QtGui, QtWidgets

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

		self.createPcore()
	
	def createPcore(self):
		qapp = QtWidgets.QApplication.instance()
		if qapp == None:
			qapp = QtWidgets.QApplication(sys.argv)
		popup = opw.popupNoButton("Setting Up Prims Project Manager", qapp)
		pcore = PrismInit.prismInit()
		pcore.setActiveStyleSheet("Fusion")
		popup.close()
		# Assign
		self.pcore = pcore

	def runCodeInProcess(self):
		print("Object Exists")
		fusion = bmd.scriptapp("Fusion")
		comp = fusion.GetCurrentComp()
		command = comp.GetData("cmd") # set the data in a variable from a diferent process comp.SetData("cmd", "print(global_Prism)")
		# Command to run
		code_string = command
		exec(code_string)

		print("finish")