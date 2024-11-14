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
	


import json
import logging

from PrismUtils.Decorators import err_catcher as err_catcher

logger = logging.getLogger(__name__)


@err_catcher(name=__name__)
def createDefaultPrismFileDb(comp):
    #   This template needs to have the required keys.
    #   Add additional keys as needed.
    defaultDb = {
        "fileValues": {
            "identifiersColors": {
                "asset": {},
                "shot": {}
            }
        },
        "nodes": {
            "import3d": {},
            "importImage": {}
        }
    }

    try:
        logger.debug("Creating default Prism Comp Database")
        cpData_str = json.dumps(defaultDb)
        comp.SetData("PrismDB", cpData_str)
        return defaultDb
    except:
        logger.warning("ERROR: Unable to create default Prism Comp Database")
        return None


@err_catcher(name=__name__)
def loadPrismFileDb(comp):
    try:
        cpData_str = comp.GetData("PrismDB")
    except:
        logger.warning("ERROR: Unable to get Prism Comp Database from the Comp")

    if cpData_str:
        cpData = json.loads(cpData_str)
        logger.debug("Loaded Prism Comp Database")
    else:
        cpData = createDefaultPrismFileDb(comp)

    return cpData


@err_catcher(name=__name__)
def savePrismFileDb(comp, cpData):
    try:
        cpData_str =  json.dumps(cpData, indent=4)
        comp.SetData("PrismDB", cpData_str)
        logger.debug("Saved Prism Comp Database to Comp")
    except:
        logger.warning("ERROR: Failed to save Prism Comp Database to Comp")


@err_catcher(name=__name__)
def addPrismDbIdentifier(comp, category, name, color):
    cpData = loadPrismFileDb(comp)
    try:
        if category in ["asset", "shot"]:
            cpData["fileValues"]["identifiersColors"][category][name] = color
            savePrismFileDb(comp, cpData)
            logger.debug(f"Added {category}{name} to Prism Comp Database")
    except:
        logger.warning("ERROR:  Unable to add Identifier")



@err_catcher(name=__name__)
def addPrismDbNodeInfo(comp, type, UUID, nodeData):
    cpData = loadPrismFileDb(comp)

    try:
        cpData["nodes"][type][UUID] = nodeData
        savePrismFileDb(comp, cpData)
        logger.debug(f"Added {nodeData['nodeName']} to the Comp Database")
        return True
    except:
        logger.warning("ERROR:  Failed to add the Naode Data to the Comp Database")
        return False



@err_catcher(name=__name__)
def updatePrismDbNodeInfo(comp, type, UUID, nodeData):
    cpData = loadPrismFileDb(comp)

    try:
        if UUID in cpData["nodes"][type]:
            cpData["nodes"][type][UUID].update(nodeData)
            logger.debug(f"Updated {nodeData['nodeName']} data.")
            savePrismFileDb(comp, cpData)
            return True
        else:
            logger.debug(f"The is no data for node: {UUID}")
            return False
    except:
        logger.warning("ERROR: Failed to update Node Data")
        return False


@err_catcher(name=__name__)
def removePrismDbNodeInfo(comp, type, UUID):
    cpData = loadPrismFileDb(comp)

    try:
        if UUID in cpData["nodes"][type]:
            del cpData["nodes"][type][UUID]
            logger.debug(f"Removed {UUID} from the Comp Database")
            savePrismFileDb(comp, cpData)
        else:
            logger.debug(f"{UUID} does not exist in the Comp Database")
            
    except:
        logger.warning(f"ERROR: Unable to remove {UUID} from the Comp Database")


    

@err_catcher(name=__name__)
def getPrismDbIdentifierColor(comp, category, name):
    try:
        logger.debug(f"Getting Identifier Color for {name}")
        cpData = loadPrismFileDb(comp)
        if category in cpData["fileValues"]["identifiersColors"]:
            if name in cpData["fileValues"]["identifiersColors"][category]:
                color = cpData["fileValues"]["identifiersColors"][category][name]
                logger.debug(f"{color} found for {name}")
                return color
        
        logger.debug(f"No color associated with {name}")
        return None
    except:
        logger.warning("ERROR:  Unable to get Identifier Color")

