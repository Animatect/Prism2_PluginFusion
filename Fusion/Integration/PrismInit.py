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

	# pcore = PrismCore.PrismCore(app="Fusion")#, prismArgs=["noProjectBrowser"])
	pcore = PrismCore.PrismCore(app="Fusion", prismArgs=["noProjectBrowser"])

	# pcore.setActiveStyleSheet("Fusion")

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