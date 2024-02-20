import os
import sys

if False:
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


# from C:\ProgramData\Blackmagic Design\Fusion\Reactor\Deploy\Scripts\Comp\AttributeSpreadsheet
# comp = fusion.GetCurrentComp()
# at = comp.ActiveTool()
# for fusion_input in at.GetInputList().values():
#     print(fusion_input.GetAttrs('INPS_ID'))
	
	#To get all the attributes uncomment the following:
	#print('##############################################')
	# for atr in fusion_input.GetAttrs():
	#     print(atr)
	
import re

def extract_version(filepath):
	# Extract the version information using a regular expression
	match = re.search(r"v(\d{4})", filepath)
	print(f"match: {match}")
	if match:
		return int(match.group(1))
	else:
		return None

def are_paths_equal_except_version(path1, path2):
	# Extract version information from both paths
	version1 = extract_version(path1)
	version2 = extract_version(path2)

	# If either version is not present, or they are different, return False
	if version1 is None or version2 is None or version1 != version2:
		return False

	# Remove the version part from the paths for exact match comparison
	path1_without_version = re.sub(r"v\d{4}", "", path1)
	path2_without_version = re.sub(r"v\d{4}", "", path2)
	print(f"path1_without_version: {path1_without_version}")
	print(f"path2_without_version: {path2_without_version}")
	# Check if the non-version parts are an exact match
	if path1_without_version == path2_without_version:
		# Versions are the same, and non-version parts are an exact match
		return True
	else:
		# Versions are the same, but non-version parts are different
		return False

# Example usage
current_filepath = "C:/tmp/tstpry/03_Production/Shots/sq_01/sh_01/Renders/3dRender/Layout/v0001/beauty/sq_01-sh_01_Layout_v0001_beauty.0100.exr"
other_filepath = "C:/tmp/tstpry/03_Production/Shots/sq_01/sh_01/Renders/3dRender/Layout/v0001/beauty/sq_01-sh_01_Layout_v0001_beauty.0200.exr"

if are_paths_equal_except_version(current_filepath, other_filepath):
	print("The other file is the same version and has the same non-version parts.")
else:
	print("The other file is different.")