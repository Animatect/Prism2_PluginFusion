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
import subprocess


def environment(module, nolocation=False):
	ospath = os.path.dirname(os.__file__)
	path_components = os.path.split(ospath)
	new_path = os.path.join(*path_components[:-1])
	python_location = os.path.join(new_path, "python.exe")
	# Construct the command as a list
	command = [python_location, "-m", "pip", "install", module]
	if nolocation:
		command = ["python", "-m", "pip", "install", module]

	# Run the command and capture the output
	try:
		result = subprocess.run(command, check=True, capture_output=True, text=True)
		print("Command output:", result.stdout)
	except subprocess.CalledProcessError as e:
		print("Error occurred:", e)
		print("Command output (if available):", e.stdout)

def installThirdParty():
	try:
		environment("PySide6")
		environment("qtpy")
	except:
		environment("PySide2")
	# environment("pyautogui")
	# environment("pyperclip")
	# environment("psutil")
	# environment("plyer")
	# environment("pygetwindow", nolocation=True)

if __name__ == "__main__":
	installThirdParty()