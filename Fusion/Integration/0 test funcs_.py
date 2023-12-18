import os
import sys


prismRoot = os.getenv("PRISM_ROOT")
if not prismRoot:
	prismRoot = "C:/GitHub/Prism/Prism"

scriptDir = os.path.join(prismRoot, "Scripts")
pysideDir = os.path.join(prismRoot, "PythonLibs", "Python3", "PySide")
sys.path.append(pysideDir)

if scriptDir not in sys.path:
	sys.path.append(scriptDir)

if pysideDir not in sys.path:
	sys.path.append(pysideDir)

# from PySide2.QtCore import *
# from PySide2.QtGui import *
# from PySide2.QtWidgets import *

from PySide2 import QtCore, QtGui, QtWidgets

#It is necessary to make a QApplication instance before importing PrismCore
qapp = QtWidgets.QApplication.instance()
if qapp == None:
	qapp = QtWidgets.QApplication(sys.argv)
def prismInit():	

	import PrismCore

	pcore = PrismCore.PrismCore(app="Fusion")# ,prismArgs=["noUI"])
	
	return pcore

	#pcore = prismInit()rt
	#print(pcore.version)
	print("hola")
"""
pcore.appPlugin.tst()
print(pcore.appPlugin.sceneFormats)

def fusiontst(self):
	currentFileName = self.fusion.GetCurrentComp().GetAttrs()["COMPS_FileName"]
	print(currentFileName.split("\\")[-1])
	
fusiontst(self)"""

import os
import sys

#from qtpy import QtWidgets, QtCore, QtGui


MENU_LABEL = "Prism"


self = sys.modules[__name__]
self.menu = None



def launch_prismFusion_menu():
	#app = QtWidgets.QApplication(sys.argv)
	pcore = prismInit()
	pcore.setActiveStyleSheet("Fusion")

	


	
#launch_prismFusion_menu()
import pyautogui
import time
import pyperclip

fusion = self.fusion
comp = fusion.CurrentComp

abc_options = {
		"Points": True,
		"Transforms": True,
		"Hierarchy": False,
		"Lights": True,
		"Normals": True,
		"Meshes": True,
		"UVs": True,
		"Cameras": True,
		"InvCameras": True
		# "SamplingRate": 24
	}

def creaeteNote():
	clip = """{
	Tools = ordered() {
		DO_NOT_DELETE_PrismSM = Note {
			CtrlWZoom = false,
			NameSet = true,
			Inputs = {
				Comments = Input { Value = "Hola de nuevo", }
			},
			ViewInfo = StickyNoteInfo {
				Pos = { 388.667, 1.30299 },
				Flags = {
					Expanded = true
				},
				Size = { 86, 16.3636 }
			},
			Colors = { TileColor = { R = 0.0, G = 0.0, B = 1.0 }, }
		}
	},
	ActiveTool = "DO_NOT_DELETE_PrismSM"
}"""
	pyperclip.copy(clip)
	comp.Paste(clip)
	print(clip)

if __name__ == "__main__":
	creaeteNote()