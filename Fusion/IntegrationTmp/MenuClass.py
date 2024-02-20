
import platform
import sys
import BlackmagicFusion as bmd

class PrismFusionMenu(object):
	def __init__(self, UIManager, fusion):
		self.fusion = fusion

		self.ui = UIManager
		self.disp = bmd.UIDispatcher(self.ui)

		#Check if window is open
		prevwin = self.ui.FindWindows("PrismWin")
		if prevwin:
			for prm in prevwin.values():
				prm.Hide()
				self.disp.ExitLoop()

		self.dlg = self.disp.AddWindow(
			{ "WindowTitle": "Prism Menu", 
			"ID": "PrismWin", 
			"Geometry": [ 300, 100, 200, 250 ], },#xpos,ypos,width,height
			
			[
				self.ui.VGroup(
				{ "Spacing": 5, },
				[
					# Add your GUI elements here:
					self.ui.Label({ 
						"ID": "PrismLabel", 
						"Text": "Prism Fusion Menu",
						'Alignment': {'AlignHCenter': True, 'AlignVCenter': True},
					}),
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
		self.dlg.On.PrismWin.Close = self._func

		# Add your GUI element based event Handlers here:
		self.dlg.On.btn_projectbrowser.Clicked = self.on_btn_projectbrowser_clicked
		self.dlg.On.btn_saveversion.Clicked = self.on_btn_saveversion_clicked
		self.dlg.On.btn_savecomment.Clicked = self.on_btn_savecomment_clicked
		self.dlg.On.btn_statemanager.Clicked = self.on_btn_statemanager_clicked
		self.dlg.On.btn_prismsettings.Clicked = self.on_btn_prismsettings_clicked

		self.dlg.Show()
		self.disp.RunLoop()
		self.dlg.Hide()

	# The window was closed
	def _func(self, ev):
		self.disp.ExitLoop()

	# Add your GUI element based event functions here: ev is the event object
	def on_btn_projectbrowser_clicked(self, ev):
		from openPrismWindows import openProjectBrowser
		openProjectBrowser()

	def on_btn_saveversion_clicked(self, ev):
		from openPrismWindows import runPrismSaveScene
		runPrismSaveScene()

	def on_btn_savecomment_clicked(self, ev):
		from openPrismWindows import openPrismSaveWithComment
		openPrismSaveWithComment()

	def on_btn_statemanager_clicked(self, ev):
		from openPrismWindows import openPrismStateManager
		openPrismStateManager()

	def on_btn_prismsettings_clicked(self, ev):
		from openPrismWindows import openPrismSettings
		openPrismSettings()

	