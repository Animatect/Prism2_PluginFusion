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
	

import os
import logging

from PrismUtils.Decorators import err_catcher as err_catcher

logger = logging.getLogger(__name__)


#	Returns the filename of the current comp
@err_catcher(name=__name__)
def getCurrentFileName(comp, origin=None, path=True):
    try:
        if comp is None:
            currentFileName = ""
        else:
            currentFileName = comp.GetAttrs()["COMPS_FileName"]

        return currentFileName
    
    except Exception as e:
        logger.warning(f"ERROR: Failed to get current filename:\n{e}")


@err_catcher(name=__name__)
def openScene(fusion, sceneFormats, filepath, force=False):
    if os.path.splitext(filepath)[1] not in sceneFormats:
        return False

    try:
        fusion.LoadComp(filepath)
        logger.debug(f"Loaded scenefile: {filepath}")
    except:
        logger.warning("ERROR: Failed to load Comp")

    return True


@err_catcher(name=__name__)
def saveScene(comp, filepath, details={}):
    try:
        #Save function returns True on success, False on failure
        result = comp.Save(filepath)
        if result:
            logger.debug(f"Saved file to {filepath}")
            return True
        else:
            raise Exception
    except:
        logger.warning(f"ERROR: Failed to save {filepath}")
        return False
    

@err_catcher(name=__name__)
def getFrameRange(comp):
    try:
        startframe = comp.GetAttrs()["COMPN_GlobalStart"]
        endframe = comp.GetAttrs()["COMPN_GlobalEnd"]
        return [startframe, endframe]
    except:
        logger.warning("ERROR: Failed to get current frame range")
        return [None, None]
    

#	Sets the supplied framerange to the comp
@err_catcher(name=__name__)
def setFrameRange(comp, startFrame, endFrame):
    comp.Lock()
    try:
        comp.SetAttrs(
            {
                "COMPN_GlobalStart": startFrame,
                "COMPN_RenderStart": startFrame,
                "COMPN_GlobalEnd": endFrame,
                "COMPN_RenderEnd": endFrame
            }
        )
        comp.SetPrefs(
            {
                "Comp.Unsorted.GlobalStart": startFrame,
                "Comp.Unsorted.GlobalEnd": endFrame,
            }
        )
    except Exception as e:
        logger.warning(f"ERROR: Could not set framerange in the comp:\n{e}")

    comp.Unlock()


@err_catcher(name=__name__)
def getFPS(comp):
    try:
        return comp.GetPrefs()["Comp"]["FrameFormat"]["Rate"]
    except Exception as e:
        logger.warning(f"ERROR: Failed to get the fps from comp:\n{e}")
        return None
    


@err_catcher(name=__name__)
def setFPS(comp, fps):
    try:
        return comp.SetPrefs({"Comp.FrameFormat.Rate": fps})
    except:
        logger.warning(f"ERROR: Failed to set the fps to the comp")



@err_catcher(name=__name__)
def getResolution(comp):
    try:
        width = comp.GetPrefs()[
            "Comp"]["FrameFormat"]["Width"]
        height = comp.GetPrefs()[
            "Comp"]["FrameFormat"]["Height"]
        
        return [width, height]
    
    except Exception as e:
        logger.warning(f"ERROR: Failed to get the current resolution from the comp:\n{e}")
        return [None, None]
    

@err_catcher(name=__name__)
def setResolution(comp, width=None, height=None):
    try:
        comp.SetPrefs(
            {
                "Comp.FrameFormat.Width": width,
                "Comp.FrameFormat.Height": height,
            }
        )
    except Exception as e:
        logger.warning(f"ERROR: Failed to set the resolution to the comp:\n{e}")


@err_catcher(name=__name__)
def getCurrentFrame(comp):
    try:
        return comp.CurrentTime
    
    except:
        logger.warning(f"ERROR: Failed to get current frame from Comp")
        return None


@err_catcher(name=__name__)
def addTool(comp, toolType, toolName=None, xPos=-32768, yPos=-32768, autoConnect=1):
    try:
        return comp.AddTool(toolType, xPos, yPos, autoConnect)
    
    except:
        logger.warning(f"ERROR: Failed to add {toolType} to Comp")
        return None


