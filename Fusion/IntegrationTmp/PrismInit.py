import os
import sys


def prismInit():
	prismRoot = getPrismRoot()

	scriptDir = os.path.join(prismRoot, "Scripts")
	pysideDir = os.path.join(prismRoot, "PythonLibs", "Python3", "PySide")
	sys.path.append(pysideDir)

	if scriptDir not in sys.path:
		sys.path.append(scriptDir)

	if pysideDir not in sys.path:
		sys.path.append(pysideDir)

	import PrismCore

	pcore = PrismCore.PrismCore(app="Fusion", prismArgs=["noProjectBrowser"])

	pcore.setActiveStyleSheet("Fusion")
	#Because Fusion Importing of 3D using code is basically a hack, we need to make sure as much as we can that the fusion window is in focus
	#this means limiting the amount of qt windows we manage on top.
	if pcore.pb:
		pcore.pb.close()

	return pcore

def getPrismRoot():
	prismRoot = os.getenv("PRISM_ROOT")
	if not prismRoot:
		path1 = os.path.normpath("C:/Program Files/Prism2")
		path2 = os.path.normpath("C:/GitHub/Prism/Prism")
		prismRoot = path1 if os.path.exists(path1) else path2
	return prismRoot

def getIconPath():
	return os.path.join(getPrismRoot(), "Scripts", "UserInterfacesPrism", "p_tray.png")
