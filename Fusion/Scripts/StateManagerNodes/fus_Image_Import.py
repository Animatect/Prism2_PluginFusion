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
import logging

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

from PrismUtils.Decorators import err_catcher

logger = logging.getLogger(__name__)


COLOR_GREEN = QColor(0, 130, 0)
COLOR_ORANGE = QColor(200, 100, 0)
COLOR_RED = QColor(130, 0, 0)
COLOR_BLACK = QColor(0, 0, 0, 0)

COLORNAMES = ["rgb",
              "rgba",
              "color", 
              "beauty",
              "combined",
              "diffuse",
              "diffcolor",
              "diffusecolor"]



class Image_ImportClass(object):
    className = "Image_Import"
    listType = "Import"
    stateCategories = {"Import2d": [{"label": className, "stateType": className}]}


    @err_catcher(name=__name__)
    def setup(
        self,
        state,
        core,
        stateManager,
        importPath=None,
        stateData=None,
        settings=None,
    ):
        self.state = state
        self.stateMode = "Image_Import"

        self.core = core
        self.stateManager = stateManager

        self.taskName = ""
        self.setName = ""

        self.fuseFuncts = self.core.appPlugin

        self.mediaChooser = ReadMediaDialog(self, self.core)

        self.taskColorMode = self.fuseFuncts.taskColorMode
        if self.taskColorMode == "Disabled":
            self.cb_taskColor.setVisible(False)
        else:
            self.cb_taskColor.setVisible(True)
            self.populateTaskColorCombo()

        self.aovThumbWidth = self.fuseFuncts.aovThumbWidth

        self.selMediaContext = None

        stateNameTemplate = "{entity}_{version}"
        self.stateNameTemplate = self.core.getConfig(
            "globals",
            "defaultImportStateName",
            configPath=self.core.prismIni,
        ) or stateNameTemplate

        self.e_name.setText(self.stateNameTemplate)
        
        #   Hide unused UI elements
        self.l_name.setVisible(False)
        self.e_name.setVisible(False)
        self.l_class.setVisible(False)

        self.oldPalette = self.b_importLatest.palette()
        self.updatePalette = QPalette()
        self.updatePalette.setColor(QPalette.Button, QColor(200, 100, 0))
        self.updatePalette.setColor(QPalette.ButtonText, QColor(255, 255, 255))

        createEmptyState = (
            QApplication.keyboardModifiers() == Qt.ControlModifier
            or not self.core.uiAvailable
            )

    ##   Do one of the following:
        
        #   1. Load State from Comp Data
        if stateData is not None:
            self.loadData(stateData)

            logger.debug("Loaded State from saved data")                    #   TODO


        #   2. If passed from FusFuncts. Receive importData via "settings" kwarg
        elif settings:
            self.identifier = settings.get("identifier", None)
            self.mediaType = settings.get("mediaType", None)
            self.itemType = settings.get("itemType", None)
            self.extension = settings.get("extension", None)
            self.version = settings.get("version", None)
            self.aov = settings.get("aov", "")
            self.aovs = settings.get("aovs", "")
            self.channel = settings.get("channel", "")
            self.channels = settings.get("channels", "")
            self.files = settings.get("files", None)

            logger.debug("Loaded State from data passed from ProjectBrowser Import")        #   TODO

        #   3. Opens Media Popup to select import
        elif (
            importPath is None
            and stateData is None
            and not createEmptyState
            and not self.stateManager.standalone
            ):
            #   Make new UID for State
            self.stateUID = self.fuseFuncts.createUUID()
            #   Open MediaChooser to get import
            requestResult = self.callMediaWindow()
            
            if requestResult == "Cancelled":
                logger.debug("Medi Import cancelled")
                return False
            
            if not requestResult:
                logger.warning("Unable to Import Image from MediaBrowser.")             #   TODO
                self.core.popup("Unable to Import Image from MediaBrowser.")            #    TESTING
                return False
        
        #   4. If error
        else:
            logger.warning("Unable to Import Image.")                               #   TODO
            self.core.popup("Unable to Import Image.")                                      #    TESTING
            return False

        getattr(self.core.appPlugin, "sm_import_startup", lambda x: None)(self)

        self.connectEvents()
        self.nameChanged()
        self.updateUi()


    @err_catcher(name=__name__)
    def setStateMode(self, stateMode):
        self.stateMode = stateMode
        self.l_class.setText(stateMode)


    @err_catcher(name=__name__)
    def callMediaWindow(self):
        self.selMediaContext = None
        
        # if hasattr(self, "mediaChooser"):                     #   NEEDED ???
        #     self.mediaChooser.close()
            
        self.mediaBrowser = self.mediaChooser.w_browser
        self.mediaPlayer = self.mediaBrowser.w_preview.mediaPlayer
        self.mediaChooser.mediaSelected.connect(lambda selResult: self.setSelectedMedia(selResult))

        result = self.mediaChooser.exec_()

        if result == QDialog.Rejected:
            return "Cancelled"
        
        if not self.selResult:
            return False

        clicked = self.selResult[0]
        self.selMediaContext = self.selResult[1]

        if clicked == "version":
            self.makeImportData(self.selMediaContext)

        if clicked == "identifier":
            self.importLatest(selectedStates=False)

        return True
    

    @err_catcher(name=__name__)                         #   TODO Simplify
    def setSelectedMedia(self, selResult):
        self.selResult = selResult  # Save the selected media



    @err_catcher(name=__name__)
    def makeImportData(self, context):
        self.context = context
        version = self.mediaBrowser.getCurrentVersion()

        if not version:
            logger.warning(f"ERROR: There are no Versions for this Media Identifier")
            self.core.popup("There are no Versions for this Media Identifier")
            return False

        #   Get data from various sources
        aovDict = self.core.mediaProducts.getAOVsFromVersion(version)

        #	Get sourceData based on passes - used to get framerange
        if len(aovDict) > 1:
            sourceData = self.mediaPlayer.compGetImportPasses() #   has AOV's
        else:
            sourceData = self.mediaPlayer.compGetImportSource() #   no AOV's

        mediaType = context["mediaType"]

        # try:
        #   Make base dict
        importData = {"stateUID": self.stateUID,
                    "identifier": context["identifier"],
                    "displayName": context["displayName"],
                    "mediaType": mediaType,
                    "itemType": context["itemType"],
                    "locations": context["locations"],
                    "path": context["path"],
                    "extension": "",
                    "version": context["version"],
                    "aovs": [],
                    "channels": []
                    }
            
        # except Exception as e:
        #     logger.warning(f"ERROR: Unable to make base importData dict: {e}")
        #     return {}

        files = []

        #   If there are Prism AOV's (for example not for 2d Renders)
        if len(aovDict) > 0:

            # try:                                  #   TODO

            #   Iterate through both dicts to extract needed data
            for aovItem, sourceItem in zip(aovDict, sourceData):
                #   Add mediaType to each aovItem
                aovItem["mediaType"] = mediaType
                # aov = aovItem["aov"]
                #   Get file list for each aov, and get first file
                filesList = self.fuseFuncts.core.mediaProducts.getFilesFromContext(aovItem)
                basefile = filesList[0]

                #   Get file extension
                if "extension" in context:
                    extension = context["extension"]
                else:
                    _, extension = os.path.splitext(basefile)

                #   Use framerange from sourceData if it exists (sequences)
                if type(sourceItem[1]) == int:
                    frame_start = sourceItem[1]
                    frame_end = sourceItem[2]

                #   Use video duration for video formats
                elif extension in self.fuseFuncts.core.media.videoFormats:
                        duration = self.fuseFuncts.core.media.getVideoDuration(basefile)
                        frame_start = 1
                        frame_end = duration

                #   For Stills Images
                else:
                    frame_start = 1
                    frame_end = 1

                channels = self.fuseFuncts.core.media.getLayersFromFile(basefile)

                if len(channels) == 0:
                    channels = ["Color"]

                for channel in channels:

                    #   Make dict for each Channel
                    fileDict = {
                        "stateUID": self.stateUID,
                        "basefile": basefile,
                        "identifier": context["identifier"],
                        "aov": aovItem["aov"],
                        "channel": channel,
                        "version": context["version"],
                        "frame_start": frame_start,
                        "frame_end": frame_end,
                    }

                    #   Add dict to files list
                    files.append(fileDict)



            # except Exception as e:
            #     logger.warning(f"ERROR: Unable to generate file list for {mediaType}:\n{e}")
            #     return None



        #   For no AOV's (for example 2drenders)
        else:
            # try:                          #   TODO

            sourceData = sourceData[0]
            
            #   Get file list and get first file
            filesList = self.fuseFuncts.core.mediaProducts.getFilesFromContext(context)
            basefile = filesList[0]

            #   Get file extension
            if "extension" in context:
                extension = context["extension"]
            else:
                _, extension = os.path.splitext(basefile)

            #   Use framerange from sourceData if it exists (sequences)
            if type(sourceData[1]) == int:
                frame_start = sourceData[1]
                frame_end = sourceData[2]

            #   Use video duration for video formats
            elif extension in self.fuseFuncts.core.media.videoFormats:
                    duration = self.fuseFuncts.core.media.getVideoDuration(basefile)
                    frame_start = 1
                    frame_end = duration

            #   For Stills Images
            else:
                frame_start = 1
                frame_end = 1

            channels = self.fuseFuncts.core.media.getLayersFromFile(basefile)

            if len(channels) == 0:
                channels = ["Color"]

            for channel in channels:
                #   Make dict for each Channel
                fileDict = {
                    "basefile": basefile,
                    "identifier": context["identifier"],
                    "channel": channel,
                    "version": context["version"],
                    "frame_start": frame_start,
                    "frame_end": frame_end,
                }

                #   Add dict to files list
                files.append(fileDict)


            # except Exception as e:
            #     logger.warning(f"ERROR: Unable to generate file list for {mediaType}:\n{e}")
            #     return None

        # Add the files to the importData
        importData["files"] = files

        #   Add additional data if exist
        importData["extension"] = extension

        try:
            if "channel" in context:
                importData["channel"] = context["channel"]

            channels = self.fuseFuncts.core.media.getLayersFromFile(basefile)
            importData["channels"] = channels

        except Exception as e:
            logger.warning(f"ERROR: Unable to add channel data to importData: {e}")

        if "versionPaths" in context:
            importData["versionPaths"] = context["versionPaths"]

        if "redirect" in context:
            importData["redirect"] = context["redirect"]

        if importData["mediaType"] in ["3drenders", "external"]:
            try:
                importData["aovs"] = self.getAovNamesFromAovDict(aovDict)
            except Exception as e:
                logger.warning(f"ERROR: Unable to get AOV names list: {e}")

        files = importData["files"]

        self.importData = importData

        self.identifier = importData.get("identifier", None)
        self.mediaType = importData.get("mediaType", None)
        self.itemType = importData.get("itemType", None)
        self.extension = importData.get("extension", None)
        self.version = importData.get("version", None)
        self.aov = importData.get("aov", "")
        self.aovs = importData.get("aovs", "")
        self.channel = importData.get("channel", "")
        self.channels = importData.get("channels", "")
        self.files = importData.get("files", None)

        self.setImportPath(self.files[0]["basefile"])

        return True


    def getAovNamesFromAovDict(self, aovDict:list) -> list:
        try:
            aovNames = []
            for aovItem in aovDict:
                aovNames.append(aovItem["aov"])
            return aovNames
        except:
            logger.warning(f"ERROR:  Unable to get AOV names from : {aovDict}")
            return None



    @err_catcher(name=__name__)
    def loadData(self, data):
        if "statename" in data:
            self.e_name.setText(data["statename"])
        if "statemode" in data:
            self.setStateMode(data["statemode"])
        if "taskname" in data:
            self.taskName = data["taskname"]
        if "setname" in data:
            self.setName = data["setname"]
        if "autoUpdate" in data:
            self.chb_autoUpdate.setChecked(eval(data["autoUpdate"]))
        if "taskColor" in data:
            idx = self.cb_taskColor.findText(data["taskColor"])
            if idx != -1:
                self.cb_taskColor.setCurrentIndex(idx)
        if "identifier" in data:
            self.identifier = data["identifier"]
        if "mediaType" in data:
            self.mediaType = data["mediaType"]
        if "itemType" in data:
            self.itemType = data["itemType"]
        if "extension" in data:
            self.extension = data["extension"]
        if "version" in data:
            self.version = data["version"]
        if "aov" in data:
            self.aov = data["aov"]
        if "aovs" in data:
            self.aovs = data["aovs"]
        if "channel" in data:
            self.channel = data["channel"]
        if "channels" in data:
            self.channels = data["channels"]
        if "files" in data:
            self.channels = data["files"]

        if "filepath" in data:
            data["filepath"] = getattr(
                self.core.appPlugin, "sm_import_fixImportPath", lambda x: x
            )(data["filepath"])
            self.setImportPath(data["filepath"])

        self.core.callback("onStateSettingsLoaded", self, data)


    @err_catcher(name=__name__)
    def connectEvents(self):
        self.e_name.textChanged.connect(self.nameChanged)
        self.e_name.editingFinished.connect(self.stateManager.saveStatesToScene)
        self.cb_taskColor.currentIndexChanged.connect(lambda: self.setToolColor(self.cb_taskColor.currentText()))
        self.b_focusView.clicked.connect(self.focusView)
        self.b_selectTools.clicked.connect(self.selectTools)

        self.b_browse.clicked.connect(self.browse)                          #   Select Version Button
        self.b_browse.customContextMenuRequested.connect(self.openFolder)   #   RCL Select Version Button
        self.b_importLatest.clicked.connect(self.importLatest)              #   Import Latest Button
        self.chb_autoUpdate.stateChanged.connect(self.autoUpdateChanged)    #   Latest Checkbox
        self.b_importAll.clicked.connect(self.importAll)
        self.b_importSel.clicked.connect(self.importSelected)
        self.b_import.clicked.connect(self.imageImport)                     #   Re-Import Button        TODO


    @err_catcher(name=__name__)
    def nameChanged(self, text=None):
        name = self.e_name.text()

        if text:
            name = text

        else:
            try:
                # importPath = self.getImportPath()
                # fileData = self.core.mediaProducts.getDataFromFilepath(importPath)
                name = f"{self.identifier}__{self.version}"

            except Exception as e:                                          #   TODO
                name = text

        self.state.setText(0, name)

    

    @err_catcher(name=__name__)
    def browse(self):                               #   TODO
        # self.core.projectBrowser()
        # #	Switch to Media Tab
        # if self.core.pb:
        #     self.core.pb.showTab("Media")

        self.callMediaWindow()


    @err_catcher(name=__name__)                     #   TODO
    def openFolder(self, pos):
        path = self.getImportPath()
        if os.path.isfile(path):
            path = os.path.dirname(path)

        self.core.openFolder(path)


    @err_catcher(name=__name__)                     #   Look at this
    def getImportPath(self):
        path = getattr(self, "importPath", "")
        if path:
            path = os.path.normpath(path)

        return path


    @err_catcher(name=__name__)
    def setImportPath(self, path):                  #   Look at this
        self.importPath = path
        self.w_currentVersion.setToolTip(path)
        self.stateManager.saveImports()
        self.updateUi()
        self.stateManager.saveStatesToScene()


    @err_catcher(name=__name__)
    def autoUpdateChanged(self, checked):
        self.w_latestVersion.setVisible(not checked)
        self.w_importLatest.setVisible(not checked)

        if checked:
            curVersion, latestVersion = self.checkLatestVersion()
            if self.chb_autoUpdate.isChecked():
                if curVersion.get("version") and latestVersion.get("version") and curVersion["version"] != latestVersion["version"]:
                    self.importLatest()

        self.stateManager.saveStatesToScene()


    @err_catcher(name=__name__)
    def runSanityChecks(self, cachePath):
        result = True

        if getattr(self.core.appPlugin, "hasFrameRange", True):
            result = self.checkFrameRange(cachePath)

        if not result:
            return False

        return True


    @err_catcher(name=__name__)
    def checkFrameRange(self, cachePath):
        versionInfoPath = self.core.getVersioninfoPath(
            self.core.mediaProducts.getMediaVersionInfoPathFromFilepath(cachePath)
        )

        impFPS = self.core.getConfig("fps", configPath=versionInfoPath)
        curFPS = self.core.getFPS()
        if not impFPS or not curFPS or impFPS == curFPS:
            return True

        fString = (
            "The FPS of the import doesn't match the FPS of the current scene:\n\nCurrent scene FPS:\t%s\nImport FPS:\t\t%s"
            % (curFPS, impFPS)
        )

        result = self.core.popupQuestion(
            fString,
            title="FPS mismatch",
            buttons=["Continue", "Cancel"],
            icon=QMessageBox.Warning,
        )

        if result == "Cancel":
            return False

        return True
    

    @err_catcher(name=__name__)
    def imageImport(self, importData, update=False, path=None, settings=None):                              #   TODO
        result = True
        if self.stateManager.standalone:
            return result

        fileName = self.core.getCurrentFileName()
        impFileName = path or self.getImportPath()
        impFileName = os.path.normpath(impFileName)

        kwargs = {
            "state": self,
            "scenefile": fileName,
            "importfile": impFileName,
        }
        result = self.core.callback("preImport", **kwargs)
        for res in result:
            if isinstance(res, dict) and res.get("cancel", False):
                return

            if res and "importfile" in res:
                impFileName = res["importfile"]
                if not impFileName:
                    return

        if not impFileName:
            self.core.popup("Invalid importpath:\n\n%s" % impFileName)
            return

        result = self.runSanityChecks(impFileName)
        if not result:
            return

        doImport = True

        # resStr = ""
        # for item in importData["files"]:
        #     resStr += f"{item}\n\n"

        # self.core.popup(f"resStr:  {resStr}")                   #   TESTING


        #   Execute import
        importResult = self.fuseFuncts.imageImport(self, importData)

        if not importResult:
            result = None
            doImport = False
        else:
            result = importResult["result"]
            doImport = importResult["doImport"]
            if result and "mode" in importResult:
                self.setStateMode(importResult["mode"])

        if doImport:
            if result == "canceled":
                return

        kwargs = {
            "state": self,
            "scenefile": fileName,
            "importfile": impFileName,
        }
        self.core.callback("postImport", **kwargs)

        # self.setImportPath(impFileName)
        self.stateManager.saveImports()
        self.updateUi()
        self.stateManager.saveStatesToScene()

        result = True

        return result


    @err_catcher(name=__name__)
    def importLatest(self, refreshUi=True, selectedStates=True):
        mediaProducts = self.fuseFuncts.core.mediaProducts
        # itemData = item.data(0, Qt.UserRole)
        # currIdent = itemData["identifier"]

        # currIdent = self.importData["identifier"]

        highestVer = mediaProducts.getLatestVersionFromIdentifier(self.selMediaContext, includeMaster=True)

        # self.selMediaContext = highestVer

        result = self.makeImportData(highestVer)

        # self.updateUi()

        if not result:
            return False
        
        if not selectedStates:
            self.importAll()

        return True
            

        # highestVer = mediaProducts.getHighestMediaVersion(itemData, getExisting=True, ignoreEmpty=False, ignoreFolder=False)



        # if refreshUi:
        #     self.updateUi()

        # path = self.getImportPath()

        # latestVerDict = self.core.mediaProducts.getLatestVersionFromFilepath(path, includeMaster=True)
        # files = self.core.mediaProducts.getFilesFromContext(latestVerDict)

        # lastestVerPath = files[0]

        # if not lastestVerPath:
        #     if not self.chb_autoUpdate.isChecked():
        #         self.core.popup("Couldn't get latest version.")
        #     return

        # prevState = self.stateManager.applyChangesToSelection
        # self.stateManager.applyChangesToSelection = False

        # self.setImportPath(lastestVerPath)
        # # self.imageImport(update=True)
        # if selectedStates:
        #     selStates = self.stateManager.getSelectedStates()
        #     for state in selStates:
        #         if state.__hash__() == self.state.__hash__():
        #             continue

        #         if hasattr(state.ui, "importLatest"):
        #             state.ui.importLatest(refreshUi=refreshUi, selectedStates=False)

        # self.stateManager.applyChangesToSelection = prevState


    @err_catcher(name=__name__)
    def checkLatestVersion(self):
        path = self.getImportPath()
        curVerData = {"version": self.context["version"], "path": path}

        latestVerDict = self.core.mediaProducts.getLatestVersionFromIdentifier(self.context, includeMaster=True)
        lastestVerName = latestVerDict["version"]
        lastestVerPath = latestVerDict["path"]

        if latestVerDict:
            latestVersionData = {"version": lastestVerName, "path": lastestVerPath}
        else:
            latestVersionData = {}

        return curVerData, latestVersionData
    

    @err_catcher(name=__name__)
    def importAll(self):
        self.imageImport(self.importData)


    @err_catcher(name=__name__)
    def importSelected(self):
        importData = self.importData.copy()

        #   Get slected items
        selItems = self.lw_objects.selectedItems()

        if selItems:
            selected_info = []
            for item in selItems:
                #   Only get children
                if item.childCount() == 0:
                    #   Get stored item data
                    file_data = item.data(0, Qt.UserRole)
                    selected_info.append(file_data)

            if selected_info:
                importData["files"] = selected_info

        else:
            self.core.popup("No items selected.")
            return False

        self.imageImport(importData)


    @err_catcher(name=__name__)
    def setStateColor(self, status):
        if status == "ok":
            statusColor = COLOR_GREEN
        elif status == "warning":
            statusColor = COLOR_ORANGE
        elif status == "error":
            statusColor = COLOR_RED
        else:
            statusColor = COLOR_BLACK

        self.statusColor = statusColor
        self.stateManager.tw_import.repaint()


    @err_catcher(name=__name__)
    def updateUi(self):
        versions = self.checkLatestVersion()
        if versions:
            curVersion, latestVersion = versions
        else:
            curVersion = latestVersion = ""

        if curVersion.get("version") == "master":
            filepath = self.getImportPath()
            curVersionName = self.core.mediaProducts.getMasterVersionLabel(filepath)
        else:
            curVersionName = curVersion.get("version")

        if latestVersion.get("version") == "master":
            filepath = latestVersion["path"]
            latestVersionName = self.core.mediaProducts.getMasterVersionLabel(filepath)
        else:
            latestVersionName = latestVersion.get("version")

        self.l_curVersion.setText(curVersionName or "-")
        self.l_latestVersion.setText(latestVersionName or "-")

        status = "error"
        if self.chb_autoUpdate.isChecked():
            if curVersionName and latestVersionName and curVersionName != latestVersionName:
                self.importLatest(refreshUi=False)

            if latestVersionName:
                status = "ok"
        else:
            useSS = getattr(self.core.appPlugin, "colorButtonWithStyleSheet", False)
            if (
                curVersionName
                and latestVersionName
                and curVersionName != latestVersionName
                and not curVersionName.startswith("master")
            ):
                status = "warning"
                if useSS:
                    self.b_importLatest.setStyleSheet(
                        "QPushButton { background-color: rgb(200,100,0); }"
                    )
                else:
                    self.b_importLatest.setPalette(self.updatePalette)
            else:
                if curVersionName and latestVersionName:
                    status = "ok"

                if useSS:
                    self.b_importLatest.setStyleSheet("")
                    self.b_importLatest.setStyleSheet(
                        "QPushButton { background-color: rgb(0,100,0); }"
                        )
                else:
                    # self.b_importLatest.setPalette(self.oldPalette)
                    self.b_importLatest.setStyleSheet(
                        "QPushButton { background-color: rgb(0,100,0); }"
                        )


        self.nameChanged()
        self.setStateColor(status)
        self.updateAovChnlTree()
        self.createStateThumb()


        getattr(self.core.appPlugin, "sm_import_updateUi", lambda x: None)(self)


    #   Populates the AOV tree and adds file data to each item
    @err_catcher(name=__name__)
    def updateAovChnlTree(self):
        #   Setup UI
        self.lw_objects.setHeaderHidden(True)
        self.lw_objects.setMinimumHeight(350)
        self.lw_objects.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.lw_objects.setSelectionBehavior(QAbstractItemView.SelectRows)

        #   Clear the list
        self.lw_objects.clear()
        #   Initialize the status icon
        self.lw_objects.setItemDelegate(statusColorDelegate(self.lw_objects))
        
        # Create a root item
        root_item = QTreeWidgetItem(self.lw_objects)
        root_item.setText(0, f"{self.identifier}_{self.version}")
        root_item.setExpanded(True)  # Expand the root item

        # Dictionary to store file data
        basefile_dict = {}

        # Organize files by basefile
        for file_data in self.importData["files"]:
            basefile = file_data["basefile"]
            aov = file_data.get("aov", None)
            channel = file_data["channel"]

            if basefile not in basefile_dict:
                basefile_dict[basefile] = {"aov_items": {}, "channels": []}
            
            if aov:
                if aov not in basefile_dict[basefile]["aov_items"]:
                    basefile_dict[basefile]["aov_items"][aov] = []
                basefile_dict[basefile]["aov_items"][aov].append(channel)
            else:
                basefile_dict[basefile]["channels"].append(channel)

        # Populate tree with grouped data
        for basefile, data in basefile_dict.items():
            # Add AOVs if they exist
            if data["aov_items"]:
                for aov, channels in data["aov_items"].items():
                    aov_item = QTreeWidgetItem(root_item)
                    aov_item.setText(0, f"{aov}    (aov)")
                    aov_item.setExpanded(True)  # Expand AOV item

                    for channel in channels:
                        channel_item = QTreeWidgetItem(aov_item)
                        channel_item.setText(0, f"{channel}    (channel)")
                        channel_item.setExpanded(True)  # Expand channel item

                        # Find the corresponding file_data for this channel
                        correct_file_data = next(
                            (f for f in self.importData["files"]
                            if f["basefile"] == basefile and f.get("aov") == aov and f["channel"] == channel),
                            None
                        )

                        if correct_file_data:
                            #   Store file_data in tree item
                            channel_item.setData(0, Qt.UserRole, correct_file_data)

                            #   If AOV Thumbs are Enabled in Settings
                            if self.fuseFuncts.useAovThumbs == "Enabled":
                                #   Get Thumb PixMap HTML object
                                thumbTip = self.getThumbToolTip(correct_file_data["basefile"], channel=channel)
                                #   Set Tool Tip
                                channel_item.setToolTip(0, thumbTip)  # Set HTML tooltip

            # If no AOVs, list channels directly under the root
            for channel in data["channels"]:
                channel_item = QTreeWidgetItem(root_item)
                channel_item.setText(0, f"{channel}    (channel)")
                channel_item.setExpanded(True)  # Expand channel item

                # Find the corresponding file_data for this channel
                correct_file_data = next(
                    (f for f in self.importData["files"]
                    if f["basefile"] == basefile and f["channel"] == channel),
                    None
                )

                if correct_file_data:
                    #   Store file_data in tree item
                    channel_item.setData(0, Qt.UserRole, correct_file_data)

                    #   If AOV Thumbs are Enabled in Settings
                    if self.fuseFuncts.useAovThumbs == "Enabled":
                        #   Get Thumb PixMap HTML object
                        thumbTip = self.getThumbToolTip(correct_file_data["basefile"], channel=channel)
                        #   Set Tool Tip
                        channel_item.setToolTip(0, thumbTip)  # Set HTML tooltip

        self.lw_objects.itemSelectionChanged.connect(self.selectChildren)


    #   Ensure all children of a selected item are also selected.
    @err_catcher(name=__name__)
    def selectChildren(self):
        for item in self.lw_objects.selectedItems():
            self._selectAllChildren(item)


    #   Recursively select all child items.
    @err_catcher(name=__name__)
    def _selectAllChildren(self, item):
        for i in range(item.childCount()):
            child = item.child(i)
            child.setSelected(True)
            self._selectAllChildren(child)


    #   Get PixMap from Filepath or Fallback image
    @err_catcher(name=__name__)
    def getPixMap(self, filePath, width=None, height=None, channel=None):
        fallbackPmap = self.core.media.getFallbackPixmap()

        try:
            if os.path.exists(filePath):
                ext = os.path.splitext(filePath)[1]
                if ext.lower() == ".exr":
                    pixMap = self.core.media.getPixmapFromExrPath(filePath, width=width, height=height, channel=channel)
                else:
                    pixMap = self.core.media.getPixmapFromPath(filePath, width=width, height=height)
            else:
                raise Exception
        except:
            pixMap = fallbackPmap

        return pixMap
    

    @err_catcher(name=__name__)
    def createStateThumb(self):
        if not hasattr(self, 'l_thumb'):
            logger.warning("ERROR: QLabel 'l_thumb' not found in UI")
            return

        #   Get file to use for thumb
        for fileData in self.importData["files"]:
            #   Try and find Color Pass
            if "aov" in fileData and fileData["aov"].lower() in COLORNAMES:
                basefile = fileData["basefile"]
                break

            #   Use first Pass
            else:
                fileData = self.importData["files"][0]
                basefile = fileData["basefile"]

        #   Get PixMap
        pixMap = self.getPixMap(basefile)
        self.l_thumb.setPixmap(pixMap)

        label_width = 270               #   TODO HARDCODED with width for initil size issue.

        # Maintain aspect ratio: Calculate new height
        aspectRatio = pixMap.height() / pixMap.width()
        new_height = int(label_width * aspectRatio)

        # Scale the pixmap to fill the QLabel's width while maintaining aspect ratio
        scaledPixmap = pixMap.scaled(label_width, new_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        # Apply the scaled pixmap
        self.l_thumb.setPixmap(scaledPixmap)
        self.l_thumb.adjustSize()

        self.l_thumb.setFixedHeight(new_height)
        self.l_thumb.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # Add a border
        self.l_thumb.setStyleSheet("border: 1px solid gray;")


    @err_catcher(name=__name__)
    def getThumbToolTip(self, filePath, channel):
        try:
            if self.core.media.getUseThumbnailForFile(filePath):
                path = self.core.media.getThumbnailPath(filePath)
            else:
                raise Exception
        except:
            path = filePath

        width = self.aovThumbWidth

        # Load the original image to get its size
        orig_pixmap = QPixmap(path)
        if orig_pixmap.isNull():
            return ""

        orig_width = orig_pixmap.width()
        orig_height = orig_pixmap.height()

        # Calculate height while maintaining aspect ratio
        height = int((width / orig_width) * orig_height) if orig_width else width

        pixMap = self.getPixMap(path, width, height, channel)

        # Convert QPixmap to Base64
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QIODevice.WriteOnly)
        pixMap.save(buffer, "PNG")

        base64_data = byte_array.toBase64().data().decode()
        thumbTip = f'<img src="data:image/png;base64,{base64_data}" width="{width}"/>'

        return thumbTip


    @err_catcher(name=__name__)
    def populateTaskColorCombo(self):
        #   Clear existing items
        self.cb_taskColor.clear()

        # Loop through color dictionary and add items with icons
        for key in self.fuseFuncts.fusionToolsColorsDict.keys():
            name = key
            color = self.fuseFuncts.fusionToolsColorsDict[key]

            # Create a QColor from the RGB values
            qcolor = QColor.fromRgbF(color['R'], color['G'], color['B'])

            # Create icon with the color
            icon = self.fuseFuncts.create_color_icon(qcolor)
            self.cb_taskColor.addItem(QIcon(icon), name)


    @err_catcher(name=__name__)
    def setToolColor(self, color):
        #   Get all Tool UIDs for the State
        uids = self.fuseFuncts.getUIDsFromStateUIDs("import2d", self.stateUID)

        # Colors the Loaders and wireless nodes
        if self.taskColorMode == "All Nodes":
            toolsToColorUID = uids

		#	Only colors the Loader nodes
        elif self.taskColorMode == "Loader Nodes":
            toolsToColorUID = []
            for uid in uids:
                tool = self.fuseFuncts.getNodeByUID(uid)
                if tool.ID == "Loader":
                    toolsToColorUID.append(uid)
        else:
            logger.debug("Tool Coloring is Disabled")
            return

        #   Get rgb color from dict
        colorRGB = self.fuseFuncts.fusionToolsColorsDict[color]
        #   Color tool
        self.fuseFuncts.colorTools(toolsToColorUID, "import2d", colorRGB, category="import2d")

        self.stateManager.saveImports()
        self.stateManager.saveStatesToScene()


    #   Centers Flow View on Tool
    @err_catcher(name=__name__)
    def focusView(self):
        #   Get all Tool UIDs for the State
        uids = self.fuseFuncts.getUIDsFromStateUIDs("import2d", self.stateUID)
        for uid in uids:
            #   Focus on the main Tool
            nData = self.fuseFuncts.getNodeInfo("import2d", uid)
            if nData["version"]:
                self.fuseFuncts.sm_view_FocusStateTool(uid)
                return


    #   Selects all Tools of the State
    @err_catcher(name=__name__)
    def selectTools(self):
        #   Get Fusion objects
        comp = self.fuseFuncts.getCurrentComp()
        flow = comp.CurrentFrame.FlowView
        #   All State Tool UIDS
        uids = self.fuseFuncts.getUIDsFromStateUIDs("import2d", self.stateUID)

        #   Select each Tool
        for uid in uids:
            tool = self.fuseFuncts.getNodeByUID(uid)
            flow.Select(tool)


    @err_catcher(name=__name__)
    def preDelete(self, item):
        if not self.core.uiAvailable:
            action = "Yes"
        else:
            action = "No"

        #   Get all Tool UIDs for the State
        uids = self.fuseFuncts.getUIDsFromStateUIDs("import2d", self.stateUID)
            
        if len(uids) > 0:
            text = "Do you want to Delete the Associated Loader(s)?"
            action = self.core.popupQuestion(text, title="Delete State", parent=self.stateManager)

        if action == "Yes":
            #   Delete each tool
            for uid in uids:
                self.fuseFuncts.deleteNode("import2d", uid, delAction=True)

            # self.core.appPlugin.deleteNodes(self)
                

    @err_catcher(name=__name__)
    def getStateProps(self):
        return {
            "statename": self.e_name.text(),
            "statemode": self.stateMode,
            "filepath": self.getImportPath(),
            "autoUpdate": str(self.chb_autoUpdate.isChecked()),
            "taskname": self.taskName,
            "setname": self.setName,
            "taskColor": self.cb_taskColor.currentText(),

            "identifier": self.identifier,
            "mediaType": self.mediaType,
            "itemType": self.itemType,
            "extension": self.extension,
            "version": self.version,
            "aov": self.aov,
            "aovs": self.aovs,
            "channel": self.channel,
            "channels": self.channels,
            "files": self.files
        }


class ReadMediaDialog(QDialog):

    mediaSelected = Signal(object)

    def __init__(self, state, core):
        super(ReadMediaDialog, self).__init__()
        self.state = state
        self.core = core

        self.isValid = False
        self.setupUi()


    @err_catcher(name=__name__)
    def setupUi(self):
        filepath = self.core.getCurrentFileName()
        # entity = self.core.getScenefileData(filepath)
        
        title = "Select Media"
        self.setWindowTitle(title)
        self.core.parentWindow(self)

        import MediaBrowser
        self.w_browser = MediaBrowser.MediaBrowser(core=self.core)
        self.w_browser.headerHeightSet = True

        ##   Disconnect native function of showing versionInfo, and connect to import the version
        #   This is disabled unless the main code gets something connected to the ID table list widget
        # self.w_browser.tw_identifier.itemDoubleClicked.disconnect()
        self.w_browser.tw_identifier.itemDoubleClicked.connect(self.identDblClicked)
        self.w_browser.lw_version.itemDoubleClicked.disconnect()
        self.w_browser.lw_version.itemDoubleClicked.connect(self.verDblClicked)

        self.lo_main = QVBoxLayout()
        self.setLayout(self.lo_main)

        self.bb_main = QDialogButtonBox()
        self.bb_main.addButton("Import Selected", QDialogButtonBox.AcceptRole)
        self.bb_main.addButton("Import Custom", QDialogButtonBox.AcceptRole)
        self.bb_main.addButton("Open Project Browser", QDialogButtonBox.AcceptRole)
        self.bb_main.addButton("Cancel", QDialogButtonBox.RejectRole)

        self.bb_main.clicked.connect(self.buttonClicked)

        self.lo_main.addWidget(self.w_browser)
        self.lo_main.addWidget(self.bb_main)

        # self.w_browser.navigate([entity])


    @err_catcher(name=__name__)
    def identDblClicked(self, item, column):
        selResult = ["identifier", item.data(0, Qt.UserRole)]

        self.mediaSelected.emit(selResult)
        self.accept() 


    @err_catcher(name=__name__)
    def verDblClicked(self, item):
        data = self.w_browser.getCurrentSource()

        if not data:
            data = self.w_browser.getCurrentAOV()
            if not data:
                data = self.w_browser.getCurrentVersion()
                if not data:
                    data = self.w_browser.getCurrentIdentifier()

        if not data:
            msg = "Invalid version selected."
            self.core.popup(msg, parent=self)
            return
        
        selResult = ["version", data]

        self.mediaSelected.emit(selResult)
        self.accept()  


    @err_catcher(name=__name__)
    def buttonClicked(self, button):
        if button == "select" or button.text() == "Import Selected":
            data = self.w_browser.getCurrentSource()
            if not data:
                data = self.w_browser.getCurrentAOV()
                if not data:
                    data = self.w_browser.getCurrentVersion()
                    if not data:
                        data = self.w_browser.getCurrentIdentifier()

            if not data:
                msg = "Invalid version selected."
                self.core.popup(msg, parent=self)
                return

            self.mediaSelected.emit(data)
            self.accept()

        elif button.text() == "Import Custom":
            self.core.popup("Not Yet Implemented")                                      #    TESTING
    
        elif button.text() == "Open Project Browser":                                   #   TODO
            self.reject()
            self.openProjectBrowser()

        elif button.text() == "Cancel":
            self.reject()  # Close the dialog with no selection

        else:
            self.reject()  # Close the dialog with no selection


    @err_catcher(name=__name__)
    def openProjectBrowser(self):
        self.core.projectBrowser()
        if self.core.pb:
            self.core.pb.showTab("Libraries")


#   For the AOV list colored icons
class statusColorDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        # Call the default painting method
        super().paint(painter, option, index)

        # Get the color from the item’s data
        color = index.data(32)      #   TODO

        if color:
            rect = QRect(option.rect)
            #   Position on the right
            rect.setLeft(option.rect.right() - 14)  
            #   Set width of the color box
            rect.setWidth(10)

            painter.fillRect(rect, QBrush(QColor(color)))