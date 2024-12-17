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
import time


packagePath = os.path.normpath(THIRDPARTY)
sys.path.append(packagePath)

import psutil


def launch_prismFusion_menu():
	print("[Prism] Launching Prism Core")
	
	# Make Sure the script runs only once at startup.
	if not is_process_running("FusionRenderNode.exe"):
		scriptPath = os.path.join(get_script_dir(), "CreateHolder.py")
		fusion.RunScript(scriptPath)

	else:
		fusion_popup("RenderNode Running", "Render Node is Running\nplease Close it and Reset Prism from the menu.")


def get_script_dir():
	# Try to determine the script's directory
	if hasattr(sys, 'frozen'):
		script_dir = os.path.dirname(sys.executable)
	else:
		script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
	return script_dir
	

def is_process_running(process_name):
	"""Check if there is any running process that contains the given name."""
	for proc in psutil.process_iter(['pid', 'name']):
		try:
			if process_name.lower() in proc.info['name'].lower():
				print(f"[Prism] The process '{process_name}' is running.")
				return True
		except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
			pass
	print(f"[Prism] The process '{process_name}' is not running.")
	return False


def fusion_popup(windowtitle, label):
	ui = fu.UIManager
	disp = bmd.UIDispatcher(ui)

	dlg = disp.AddWindow({'WindowTitle': windowtitle, 'ID': 'fuspopup', 'Geometry': [100, 100, 300, 90], 'Spacing': 0,},[
		ui.VGroup({'Spacing': 10,},[
			# Add your GUI elements here:
			ui.HGroup({'Spacing': 0,},[
				ui.Label({
					"ID": "Label",
					"Text": label,
					"Alignment":{
						"AlignHCenter": True,
						"AlignTop": True,
					},                    
				}),
			]),
			ui.HGroup({'Spacing': 0,},[
				ui.Button({'Spacing': 0,
					'ID': 'B',
					'Text': 'Close',
					"Weight": 0.5,
				}),
			]),
		]),
	])

	itm = dlg.GetItems()

	# The window was closed
	def _func(ev):
		disp.ExitLoop()
	dlg.On.fuspopup.Close = _func

	# Add your GUI element based event functions here:
	def _func(ev):
		# print('Button Clicked')
		disp.ExitLoop()
	dlg.On.B.Clicked = _func

	dlg.Show()
	disp.RunLoop()
	dlg.Hide()



if __name__ == "__main__":
	launch_prismFusion_menu()