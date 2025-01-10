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


import BlackmagicFusion as bmd
from ResetPrism import launch_prismFusion_menu


def CallButton(clickedBtn):
    uimanager = bmd.scriptapp("Fusion").UIManager
    holders = uimanager.FindWindows("PrismHolder")
    holder = None
    
    if len(holders) > 0:
        holder = holders[len(holders)]
        holder.GetItems()[clickedBtn].Click()
    else:
        print("[Prism]  Prism is not running.  Please RESET PRISM.")
        makeMessageDialog("Prism is not running.\n\nPlease RESET PRISM from the Fusion Prism Menu.")



def makeMessageDialog(message):
    import tkinter as tk

    fusion = bmd.scriptapp("Fusion")
    ui = fusion.UIManager
    disp = bmd.UIDispatcher(ui)

    #   Window size
    windowWidth = 300  # Smaller width
    windowHeight = 150  # Smaller height

    #   tkinter to get screen size for centering
    root = tk.Tk()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    center_x = (screen_width - windowWidth) // 2
    center_y = (screen_height - windowHeight) // 2

    # Create the dialogue
    dlg = disp.AddWindow({'WindowTitle': 'PRISM', 'ID': 'messagebox', 'Geometry': [center_x, center_y, windowWidth, windowHeight], 'Spacing': 10}, [
        ui.VGroup({'Spacing': 5}, [
            ui.Label({
                "ID": "MessageLabel",
                "Text": message,
                "Alignment": {
                    "AlignHCenter": True,
                    "AlignVCenter": True,
                },
                "WordWrap": True,
            }),
            ui.HGroup({}, [
                ui.Button({
                    'ID': 'CloseButton',
                    'Text': 'Close',
                    'MinimumSize': [100, 30],
                    'Flat': True,
                }),
            ]),
        ]),
    ])

    # Event function when the button is clicked
    def closeDialog(ev):
        disp.ExitLoop()

    dlg.On.CloseButton.Clicked = closeDialog

    dlg.Show()
    disp.RunLoop()
    dlg.Hide()