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

	return pcore

def getPrismRoot():
	prismRoot = os.getenv("PRISM_ROOT")
	if not prismRoot:
		prismRoot = PRISMROOT
	return prismRoot

def getIconPath():
	return os.path.join(getPrismRoot(), "Scripts", "UserInterfacesPrism", "p_tray.png")

def checkThirdParty():
	# import sys
	# if not sys.version_info.major == 3:
	# 	raise Exception("Fusion Plugin only works with python 3 up to 3.11")
	# 	#return
	# if sys.version_info.minor > 11:
	# 	raise Exception("Fusion Plugin only works with python 3.11 and lower")
		#return
	
	#Check for third party
	try:
		import qtpy
		# import pyautogui
		# import pyperclip
		# import psutil
		# import plyer
		pass
	except ImportError:
		import InstallThirdParty
		InstallThirdParty.installThirdParty()