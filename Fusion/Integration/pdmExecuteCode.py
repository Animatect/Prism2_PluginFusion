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

## This file is for developers and allows execution of code in the context of an existing prism core.                   ##
## It uses Fusion Data Attributes to set the command to be retrieved from the Holder Class which executes the command.  ##


import BlackmagicFusion as bmd
ui = fu.UIManager
disp = bmd.UIDispatcher(ui)
comp = fusion.GetCurrentComp()
codedata = comp.GetData("cmd")

examplecode = """
qapp = QtWidgets.QApplication.instance()
if qapp == None:
    print("wasnone")
    qapp = QtWidgets.QApplication(sys.argv)
pcore = global_Prism.pcore
pcore.stateManager()

sm = pcore.sm
print("nm is SetRenderNode: ", sm.states[0].ui.b_setRendernode.text() == "SetRenderNode")
print("frRg: ", sm.states[0].ui.getFrameRange("Scene"))

qapp.exec_()
"""
if codedata and codedata != "":
    examplecode = codedata

dlg = disp.AddWindow({ "WindowTitle": "Run Code with global Prism Core", "ID": "RunCode", "Geometry": [100, 100, 600, 800], "Spacing": 10, "Margin": 10,},[
	ui.VGroup({ "ID": "root",},[
		# Add your GUI elements here:
        ui.HGroup({
            "Weight":1,},[
		ui.TextEdit({ 
			"ID": "MyTxt",
			"Text": examplecode,
			"PlaceholderText": "Maintain this window open to keep executing code",
			"Lexer": "fusion",
            "MinimumSize":{500, 750},
		}),
        ]),
        ui.HGroup({
            "Weight":0,},[
        ui.Button({
            'ID': 'run',
            'Text': 'Run Code',
        }),
        ui.Button({
            'ID': 'clearcode',
            'Text': 'Clear Code',
        }),
        ]),
]),
])

itm = dlg.GetItems()

# The window was closed
def _func(ev):
	disp.ExitLoop()
dlg.On.RunCode.Close = _func

# Add your GUI element based event functions here:

# def _func(ev):
# 	print(itm['MyTxt'].PlainText)
# dlg.On.MyTxt.TextChanged = _func

def executeCode(ev):
    data = itm['MyTxt'].PlainText
    comp = fusion.GetCurrentComp()
    comp.SetData("cmd", data)
    uimanager = bmd.scriptapp("Fusion").UIManager
    holders = uimanager.FindWindows("PrismHolder")
    holder = holders[len(holders)]
    holder.GetItems()["rcip"].Click()
dlg.On.run.Clicked = executeCode

def clearcode(ev):
    data = itm['MyTxt'].PlainText
    comp = fusion.GetCurrentComp()
    comp.SetData("cmd", "")
    itm['MyTxt'].PlainText = ""
dlg.On.clearcode.Clicked = clearcode

dlg.Show()
disp.RunLoop()
dlg.Hide()
