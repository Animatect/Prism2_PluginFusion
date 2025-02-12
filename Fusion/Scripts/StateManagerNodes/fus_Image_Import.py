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

        # self.mediaChooser = None

        self.taskName = ""
        self.setName = ""

        self.fuseFuncts = self.core.appPlugin

        stateNameTemplate = "{entity}_{version}"
        self.stateNameTemplate = self.core.getConfig(
            "globals",
            "defaultImportStateName",
            configPath=self.core.prismIni,
        ) or stateNameTemplate
        self.e_name.setText(self.stateNameTemplate)
        self.l_name.setVisible(False)
        self.e_name.setVisible(False)
        self.l_class.setVisible(False)

        self.oldPalette = self.b_importLatest.palette()
        self.updatePalette = QPalette()
        self.updatePalette.setColor(QPalette.Button, QColor(200, 100, 0))
        self.updatePalette.setColor(QPalette.ButtonText, QColor(255, 255, 255))

        self.populateTaskColorCombo()

        createEmptyState = (
            QApplication.keyboardModifiers() == Qt.ControlModifier
            or not self.core.uiAvailable
            )

    #   Do one of the following:

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

            logger.debug("Loaded State from data passed from ProjectBrowser Import")                #   TODO

        #   3. Opens Media Popup to select import
        elif (
            importPath is None
            and stateData is None
            and not createEmptyState
            and not self.stateManager.standalone
            ):
            requestResult = self.callMediaWindow()
            # requestResult = self.requestImportPaths()
            

            if not requestResult:
                logger.warning("Unable to Import Image from MediaBrowser.")                         #   TODO
                self.core.popup("Unable to Import Image from MediaBrowser.")                                      #    TESTING
                return False
            
        else:
            # (
            # stateData is None
            # and not createEmptyState
            # and not self.stateManager.standalone
            # ):
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
        self.selectedMedia = None
        
        if hasattr(self, "mediaChooser"):
            self.mediaChooser.close()
            
        self.mediaChooser = ReadMediaDialog(self, self.core)
        self.mediaChooser.mediaSelected.connect(lambda data: self.setSelectedMedia(data))

        self.mediaBrowser = self.mediaChooser.w_browser
        self.mediaPlayer = self.mediaBrowser.w_preview.mediaPlayer

        self.mediaChooser.exec_()

        # self.core.projectBrowser()
        # #	Switch to Media Tab
        # if self.core.pb:
        #     self.core.pb.showTab("Media")

        #     self.mediaBrowser = self.core.pb.mediaBrowser
        #     self.mediaBrowser.lw_version.itemDoubleClicked.disconnect()
        #     self.mediaBrowser.lw_version.itemDoubleClicked.connect(self.itemDoubleClicked)

        #     self.mediaPlayer = self.mediaBrowser.w_preview.mediaPlayer

        if not self.selectedMedia:
            self.core.popup("NOTHING SELECTED")                                      #    TESTING
            return False


        self.makeImportData()


        return True
    



    @err_catcher(name=__name__)                         #   TODO Simplify
    def setSelectedMedia(self, data):
        self.selectedMedia = data  # Save the selected media



    @err_catcher(name=__name__)
    def makeImportData(self):

        context = self.selectedMedia


        print("\n\n*** CONTEXT  ****\n")
        for key in sorted(context.keys()):
            print(f"{key}: {context[key]}")

        self.core.popup(f"context:  {context}")                                      #    TESTING

        mediaType = context["mediaType"]

        version = self.mediaBrowser.getCurrentVersion()

        print("\n\n*** VERSION  ****\n")
        for key in sorted(version.keys()):
            print(f"{key}: {version[key]}")

        self.core.popup(f"version:  {version}")                                      #    TESTING

        aovDict = self.core.mediaProducts.getAOVsFromVersion(version)

        print("\n\n*** AOV DICT  ****\n")
        for item in aovDict:
            print("\n*******  AOV *****")
            for key in sorted(item.keys()):
                print(f"{key}: {item[key]}")

        self.core.popup(f"aovDict:  {aovDict}")                                      #    TESTING

        #	Get sourceData based on mediaType - used to get framerange
        if "aov" in context:
            sourceData = self.mediaPlayer.compGetImportPasses()
        else:
            sourceData = self.mediaPlayer.compGetImportSource()


        try:
            #   Make base dict
            importData = {"identifier": context["identifier"],
                        "displayName": context["displayName"],
                        "mediaType": mediaType,
                        "itemType": context["itemType"],
                        "locations": context["locations"],
                        "path": context["path"],
                        "extension": "",
                        "version": context["version"],
                        "aov": "",
                        "aovs": [],
                        "channel": "",
                        "channels": []
                        }
            
        except Exception as e:
            logger.warning(f"ERROR: Unable to make base importData dict: {e}")
            return {}
        
        #   Add AOV if it exists
        if "aov" in context:
            importData["aov"] = context["aov"]

        files = []

        #   For "3drenders" and "external media"
        if mediaType in ["3drenders", "externalMedia"]:
            try:
                #   Iterate through both dicts to extract needed data
                for aovItem, sourceItem in zip(aovDict, sourceData):
                    #   Add mediaType to each aovItem
                    aovItem["mediaType"] = mediaType
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

                    #   Make dict for each AOV
                    fileDict = {
                        "basefile": basefile,
                        "identifier": context["identifier"],
                        "aov": aovItem["aov"],
                        "version": context["version"],
                        "frame_start": frame_start,
                        "frame_end": frame_end,
                    }

                    #   Add dict to files list
                    files.append(fileDict)

            except Exception as e:
                logger.warning(f"ERROR: Unable to generate file list for {mediaType}:\n{e}")
                return None

        #   For "2drenders:
        else:
            try:
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

                #   Make dict for each AOV
                fileDict = {
                    "basefile": basefile,
                    "identifier": context["identifier"],
                    "version": context["version"],
                    "frame_start": frame_start,
                    "frame_end": frame_end,
                }

                files.append(fileDict)

            except Exception as e:
                logger.warning(f"ERROR: Unable to generate file list for {mediaType}:\n{e}")
                return None

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


        # print("\n\n*** IMPORT DATA\n\n")
        # for key, value in importData.items():
            # print(f"{key}:  {value}")
        # print("**********************\n\n")

        files = importData["files"]
        # print("*** FILES\n\n")
        # print(files)
        # # print("****************")
        # for file in files:
        #     print("*** FILE")
        #     # print(file)
        #     # print("*******")
        #     for key, value in file.items():
        #         print(f"{key}:  {value}")
        # print("**********")

        self.importData = importData                                        #   TESTING

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
        self.cb_taskColor.currentIndexChanged.connect(lambda: self.setTaskColor(self.cb_taskColor.currentText()))
        self.b_browse.clicked.connect(self.browse)  #   Select Version Button
        self.b_browse.customContextMenuRequested.connect(self.openFolder)   #   RCL Select Version Button
        self.b_importLatest.clicked.connect(self.importLatest)  #   Import Latest Button
        self.chb_autoUpdate.stateChanged.connect(self.autoUpdateChanged)    #   Latest Checkbox
        self.b_importAll.clicked.connect(self.importAll)
        self.b_importSel.clicked.connect(self.importSelected)
        self.b_import.clicked.connect(self.importImage)     #   Re-Import Button
        self.b_selectAll.clicked.connect(self.selectAllAovs)


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
    def browse(self):

        self.core.projectBrowser()
        #	Switch to Media Tab
        if self.core.pb:
            self.core.pb.showTab("Media")


    @err_catcher(name=__name__)
    def openFolder(self, pos):
        path = self.getImportPath()
        if os.path.isfile(path):
            path = os.path.dirname(path)

        self.core.openFolder(path)


    @err_catcher(name=__name__)
    def getImportPath(self):
        path = getattr(self, "importPath", "")
        if path:
            path = os.path.normpath(path)

        return path


    @err_catcher(name=__name__)
    def setImportPath(self, path):
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
    def importImage(self, update=False, path=None, settings=None):                              #   TODO
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

        # if not hasattr(self.core.appPlugin, "sm_import_importToApp"):
        #     self.core.popup("Import into %s is not supported." % self.core.appPlugin.pluginName)
        #     return

        result = self.runSanityChecks(impFileName)
        if not result:
            return

        doImport = True


        # importResult = self.core.appPlugin.sm_import_importToApp(
        #         self, doImport=doImport, update=update, impFileName=impFileName, settings=settings
        #         )

        # if not importResult:
        #     result = None
        #     doImport = False
        # else:
        #     result = importResult["result"]
        #     doImport = importResult["doImport"]
        #     if result and "mode" in importResult:
        #         self.setStateMode(importResult["mode"])

        # if doImport:
        #     if result == "canceled":
        #         return

            # self.nodeNames = [
            #     self.core.appPlugin.getNodeName(self, x) for x in self.nodes
            # ]
            # illegalNodes = self.core.checkIllegalCharacters(self.nodeNames)
            # if len(illegalNodes) > 0:
            #     msgStr = "Objects with non-ascii characters were imported. Prism supports only the first 128 characters in the ascii table. Please rename the following objects as they will cause errors with Prism:\n\n"
            #     for i in illegalNodes:
            #         msgStr += i + "\n"
            #     self.core.popup(msgStr)

            # if self.chb_autoNameSpaces.isChecked():
            #     self.core.appPlugin.sm_import_removeNameSpaces(self)

            # if not result:
            #     msgStr = "Import failed: %s" % impFileName
            #     self.core.popup(msgStr, title="ImportFile")

        kwargs = {
            "state": self,
            "scenefile": fileName,
            "importfile": impFileName,
        }
        self.core.callback("postImport", **kwargs)
        self.setImportPath(impFileName)
        self.stateManager.saveImports()
        self.updateUi()
        self.stateManager.saveStatesToScene()

        result = True

        return result


    @err_catcher(name=__name__)
    def importLatest(self, refreshUi=True, selectedStates=True):
        if refreshUi:
            self.updateUi()

        path = self.getImportPath()

        latestVerDict = self.core.mediaProducts.getLatestVersionFromFilepath(path, includeMaster=True)
        files = self.core.mediaProducts.getFilesFromContext(latestVerDict)

        lastestVerPath = files[0]

        if not lastestVerPath:
            if not self.chb_autoUpdate.isChecked():
                self.core.popup("Couldn't get latest version.")
            return

        prevState = self.stateManager.applyChangesToSelection
        self.stateManager.applyChangesToSelection = False

        self.setImportPath(lastestVerPath)
        # self.importImage(update=True)
        if selectedStates:
            selStates = self.stateManager.getSelectedStates()
            for state in selStates:
                if state.__hash__() == self.state.__hash__():
                    continue

                if hasattr(state.ui, "importLatest"):
                    state.ui.importLatest(refreshUi=refreshUi, selectedStates=False)

        self.stateManager.applyChangesToSelection = prevState


    @err_catcher(name=__name__)
    def checkLatestVersion(self):
        path = self.getImportPath()

        curVerName = self.core.mediaProducts.getVersionFromFilepath(path) or ""
        # getVersionFromFilepath

        curVerData = {"version": curVerName, "path": path}

        latestVerDict = self.core.mediaProducts.getLatestVersionFromFilepath(path, includeMaster=True)
        if not latestVerDict:
            latestVerDict = self.core.mediaProducts.getLatestVersionFromIdentifier(self.importData, includeMaster=True)
            if not latestVerDict:
                latestVerDict = self.core.mediaProducts.getVersionsFromContext(self.importData)

        lastestVerName = latestVerDict["version"]
        lastestVerPath = latestVerDict["path"]

        if latestVerDict:
            latestVersionData = {"version": lastestVerName, "path": lastestVerPath}
        else:
            latestVersionData = {}

        return curVerData, latestVersionData
    

    @err_catcher(name=__name__)
    def importAll(self):
        self.core.popup("IMPORT ALL BUTTON")                                      #    TESTING


    @err_catcher(name=__name__)
    def importSelected(self):
        self.core.popup("IMPORT SELECTED BUTTON")                                      #    TESTING


    @err_catcher(name=__name__)
    def setStateColor(self, status):
        if status == "ok":
            statusColor = QColor(0, 130, 0)
        elif status == "warning":
            statusColor = QColor(200, 100, 0)
        elif status == "error":
            statusColor = QColor(130, 0, 0)
        else:
            statusColor = QColor(0, 0, 0, 0)

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

        # isCache = self.stateMode == "ApplyCache"
        # self.f_nameSpaces.setVisible(not isCache)

        self.nameChanged()
        self.setStateColor(status)

        self.updateAovChnlTree()

        self.createStateThumb()

        getattr(self.core.appPlugin, "sm_import_updateUi", lambda x: None)(self)


    @err_catcher(name=__name__)
    def updateAovChnlTree(self):

        # self.core.popup(f"self.importData: {self.importData}")                                      #    TESTING
        # print(f"self.importData:\n\n{self.importData}")                                      #    TESTING

        # files = self.importData["files"]

        # self.core.popup(f"identifier: {identifier}\n"
        #                 f"aov: {aov}\n"
        #                 f"aovs: {aovs}\n"
        #                 f"channel: {channel}\n"
        #                 f"channels: {channels}")                                      #    TESTING
        

        self.lw_objects.setHeaderHidden(True)
        self.lw_objects.setMinimumHeight(350)  # Set the minimum height to 300 pixels
        self.lw_objects.clear()

        # Create a root item for the identifier
        root_item = QTreeWidgetItem(self.lw_objects)
        root_item.setText(0, f"{self.identifier}_{self.version}")
        root_item.setExpanded(True)  # Optional: expand the root item by default

        # Dictionary to store AOV nodes for grouping channels
        aov_items = {}

        # Iterate through the files and organize AOVs and channels
        for file_data in self.importData["files"]:
            aov = file_data.get("aov", None)
            if aov:
                aov = file_data["aov"]

            # Get the channels from the file using the provided method
            try:
                channels = self.core.media.getLayersFromFile(file_data["basefile"])

                if len(channels) < 1:
                    raise Exception
                
            except Exception as e:
                # Handle exceptions (e.g., invalid file) gracefully
                channels = ["Unknown Channel"]
                print(f"Error getting channels for file {file_data['basefile']}: {e}")

            if aov:
                # Check if this AOV already exists in the tree
                if aov not in aov_items:
                    # Create a new item for the AOV
                    aov_item = QTreeWidgetItem(root_item)
                    aovText = f"{aov}    (aov)"
                    aov_item.setText(0, aovText)
                    aov_items[aov] = aov_item
                else:
                    # Reuse the existing AOV item
                    aov_item = aov_items[aov]

            # Add channels as children of the AOV
            for channel in channels:
                channel_item = QTreeWidgetItem(aov_item)
                channelText = f"{channel}    (channel)"
                channel_item.setText(0, channelText)

                # Optionally style the channel item, e.g., based on frame range
                frame_start = file_data["frame_start"]
                frame_end = file_data["frame_end"]
                if frame_start > frame_end:  # Example validation logic
                    channel_item.setBackground(0, QBrush(QColor("red")))

        # Optionally expand all AOV items
        for aov_item in aov_items.values():
            aov_item.setExpanded(True)

            
    @err_catcher(name=__name__)
    def createStateThumb(self):
        if not hasattr(self, 'l_thumb'):
            logger.warning("ERROR: QLabel 'l_thumb' not found in UI")
            return

        fallbackPmap = self.core.media.getFallbackPixmap()

        fileData = self.importData["files"][0]
        basefile = fileData["basefile"]

        try:
            if os.path.exists(basefile):
                pixMap = self.core.media.getPixmapFromPath(basefile)

            else:
                raise Exception
            
        except:
            pixMap = fallbackPmap

        # Get the QLabel's current width (stretched)
        label_width = self.l_thumb.width()

        # Maintain aspect ratio: Calculate new height
        aspectRatio = pixMap.height() / pixMap.width()
        new_height = int(label_width * aspectRatio)

        # Scale the pixmap to fill the QLabel's width while maintaining aspect ratio
        scaledPixmap = pixMap.scaled(label_width, new_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        # Apply the scaled pixmap
        self.l_thumb.setPixmap(scaledPixmap)

        # Update QLabel height dynamically
        self.l_thumb.setFixedHeight(new_height)

        # Ensure QLabel stretches horizontally but keeps a fixed height
        self.l_thumb.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Optional: Add a border for visibility
        self.l_thumb.setStyleSheet("border: 1px solid gray;")


    @err_catcher(name=__name__)
    def populateTaskColorCombo(self):
        # Assuming self.cb_taskColor is your QComboBox
        self.cb_taskColor.clear()  # Clear existing items

        # Loop through your color dictionary and add items with icons
        for key in self.fuseFuncts.fusionToolsColorsDict.keys():
            name = key
            color = self.fuseFuncts.fusionToolsColorsDict[key]

            # Create a QColor from the RGB values
            qcolor = QColor.fromRgbF(color['R'], color['G'], color['B'])

            # Create a QIcon with the color (you can create an icon using a colored rectangle or image)
            icon = self.fuseFuncts.create_color_icon(qcolor)

            # Add the item to the QComboBox with the icon and text
            self.cb_taskColor.addItem(QIcon(icon), name)

            # Optionally, you can connect a lambda function to handle item selection (if needed)
            # For example, you can use the currentIndexChanged signal of the QComboBox:
            self.cb_taskColor.currentIndexChanged.connect(
                lambda index, color=color: self.handleColorSelection(index, color)
            )

        # Optionally, set the size of the icons in the combobox
        self.cb_taskColor.setIconSize(QSize(24, 24))


    @err_catcher(name=__name__)
    def setTaskColor(self, color):                                              #   TODO

        self.core.popup(f"color:  {color}")                                      #    TESTING


    @err_catcher(name=__name__)
    def selectAllAovs(self):
        self.lw_objects.selectAll()


    # @err_catcher(name=__name__)
    # def updateTrackObjects(self, state):
    #     if not state:
    #         if len(self.nodes) > 0:
    #             msg = QMessageBox(
    #                 QMessageBox.Question,
    #                 "Track objects",
    #                 "When you disable object tracking Prism won't be able to delete or replace the imported objects at a later point in time. You cannot undo this action. Are you sure you want to disable object tracking?",
    #                 QMessageBox.Cancel,
    #             )
    #             msg.addButton("Continue", QMessageBox.YesRole)
    #             msg.setParent(self.core.messageParent, Qt.Window)
    #             action = msg.exec_()

    #             if action != 0:
    #                 self.chb_trackObjects.setChecked(True)
    #                 return

    #         self.nodes = []
    #         getattr(
    #             self.core.appPlugin, "sm_import_disableObjectTracking", lambda x: None
    #         )(self)

    #     self.updateUi()
    #     self.stateManager.saveStatesToScene()


    @err_catcher(name=__name__)
    def preDelete(
        self,
        item=None,
        baseText="Do you also want to delete the connected objects?\n\n",
    ):
        if not self.core.uiAvailable:
            action = "Yes"
            print("delete objects:\n\n%s" % baseText)
        else:
            action = self.core.popupQuestion(baseText, title="Delete State", parent=self.stateManager)

        if action == "Yes":
            self.core.appPlugin.deleteNodes(self)

        getattr(self.core.appPlugin, "sm_import_preDelete", lambda x: None)(self)


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
        entity = self.core.getScenefileData(filepath)
        
        title = "Select Media"
        self.setWindowTitle(title)
        self.core.parentWindow(self)

        import MediaBrowser
        self.w_browser = MediaBrowser.MediaBrowser(core=self.core)
        self.w_browser.headerHeightSet = True

        ##   Disconnect native function of showing versionInfo, and connect to import the version
        
        #   This is disabled unless the main code gets something connected to the ID table widget
        # self.w_browser.tw_identifier.itemDoubleClicked.disconnect()

        self.w_browser.tw_identifier.itemDoubleClicked.connect(self.idDoubleClicked)
        self.w_browser.lw_version.itemDoubleClicked.disconnect()
        self.w_browser.lw_version.itemDoubleClicked.connect(self.verDoubleClicked)

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

        self.w_browser.navigate([entity])


    @err_catcher(name=__name__)
    def idDoubleClicked(self):

        
        self.buttonClicked("select")


    @err_catcher(name=__name__)
    def verDoubleClicked(self, item):
        self.getVerData()


    @err_catcher(name=__name__)
    def getVerData(self):
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