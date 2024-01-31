import os
import sys


prismRoot = os.getenv("PRISM_ROOT")
if not prismRoot:
	prismRoot = "C:/Program Files/Prism2"#"C:/GitHub/Prism/Prism"

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

import PrismCore

pcore = PrismCore.PrismCore(app="Fusion")# ,prismArgs=["noUI"])

#print(pcore.appPlugin.sceneFormats)
fileName = pcore.getCurrentFileName()
context = pcore.getScenefileData(fileName)
print(f"filename: {fileName}, \n context: {context}")
##print(pcore.sm.stateTypes.keys())