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


ui = fu.UIManager
disp = bmd.UIDispatcher(ui)

dlg = disp.AddWindow({'WindowTitle': 'SessionStarted', 'ID': 'startedprismsession', 'Geometry': [100, 100, 200, 50], 'Spacing': 0,},[
    ui.VGroup({'Spacing': 0,},[
    # Add your GUI elements here:
    ui.HGroup({},[
    ui.Label({"ID": "Label", "Text": "Empty",}),
        ]),
    ]),
])
# def _func(ev):
#     disp.ExitLoop()
# dlg.On.startedprismsession.Close = _func

# dlg.Show()
disp.RunLoop()
dlg.Hide()