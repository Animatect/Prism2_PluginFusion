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
	

from PrismUtils.Decorators import err_catcher as err_catcher


@err_catcher(name=__name__)
def importUSD(plugin, origin, importPath, UUID, nodeName, version):
    comp = plugin.getCurrentComp()

    comp.Lock()

    #	Add uLoader node
    usdTool = comp.AddTool("uLoader")

    #	Set import file path
    usdTool["Filename"] = importPath

    #	Set node name
    usdTool.SetAttrs({"TOOLS_Name": nodeName})

    #	Add custom UUID
    usdTool.SetData('Prism_UUID', UUID)

    comp.Unlock()

    return {"result": True, "doImport": True}


@err_catcher(name=__name__)
def updateUSD(plugin, origin, importPath, UUID, nodeName, version):
    comp = plugin.getCurrentComp()

    comp.Lock()

    #	Get uLoader node
    usdTool = plugin.getNodeByUID(UUID)

    #	Set import file path
    usdTool["Filename"] = importPath

    #	Set node name
    usdTool.SetAttrs({"TOOLS_Name": nodeName})

    comp.Unlock()

    return {"result": True, "doImport": True}



@err_catcher(name=__name__)
def importFBX(plugin, origin, importPath, UUID, nodeName, version, update=False):
    comp = plugin.getCurrentComp()

    comp.Lock()

    #	Add FBX Mesh node
    fbxTool = comp.AddTool("SurfaceFBXMesh")

    #	Set import mesh file path
    fbxTool["ImportFile"] = importPath

    #	Set node name
    fbxTool.SetAttrs({"TOOLS_Name": nodeName})

    #	Add custom UUID
    fbxTool.SetData('Prism_UUID', UUID)

    comp.Unlock()

    return {"result": True, "doImport": True}