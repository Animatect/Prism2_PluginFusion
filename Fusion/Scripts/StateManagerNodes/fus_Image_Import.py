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
        node=None,
        importPath=None,
        stateData=None,
        openProductsBrowser=True,                                               #   TODO  ???
        settings=None,
    ):
        self.state = state
        self.stateMode = "Image_Import"

        self.core = core
        self.stateManager = stateManager
        self.taskName = ""
        self.setName = ""

        self.fuseFuncts = self.core.appPlugin                           #   TODO - change references to this in the code

        stateNameTemplate = "{entity}_{version}"
        self.stateNameTemplate = self.core.getConfig(
            "globals",
            "defaultImportStateName",
            configPath=self.core.prismIni,
        ) or stateNameTemplate
        self.e_name.setText(self.stateNameTemplate)
        self.l_name.setVisible(False)
        self.e_name.setVisible(False)

        self.nodes = []
        self.nodeNames = []

        # self.f_abcPath.setVisible(False)
        # self.f_keepRefEdits.setVisible(False)

        self.oldPalette = self.b_importLatest.palette()
        self.updatePalette = QPalette()
        self.updatePalette.setColor(QPalette.Button, QColor(200, 100, 0))
        self.updatePalette.setColor(QPalette.ButtonText, QColor(255, 255, 255))

        self.populateTaskColorCombo()

        createEmptyState = (
            QApplication.keyboardModifiers() == Qt.ControlModifier
            or not self.core.uiAvailable
            ) or not openProductsBrowser                                                    #   TODO


        if stateData is not None:
            self.loadData(stateData)

        else:
            if settings:
                #   Receive importData via "settings" kwarg
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

        if (
            importPath is None
            and stateData is None
            and not createEmptyState
            and not self.stateManager.standalone
            ):
            importPaths = self.requestImportPaths()
            if importPaths:
                importPath = importPaths[-1]
                if len(importPaths) > 1:                                          #   TESTING
                    for importPath in importPaths[:-1]:
                        stateManager.importFile(importPath)

        if importPath:
            self.setImportPath(importPath)
            result = self.importImage(settings=settings)

            if not result:
                return False
            
        elif (
            stateData is None
            and not createEmptyState
            and not self.stateManager.standalone
            ):
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
    def requestImportPaths(self):
        # try:

            #   TEMP BYPASS OF STATE MANAGER    #
        #     fString = ("Please use the Project Browser to Import Images.\n\n"
        #             "Open Project Browser?")

        #     result = self.core.popupQuestion(
        #         fString,
        #         title="Import Images",
        #         buttons=["Open", "Cancel"],
        #         icon=QMessageBox.Warning,
        #         )

        #     #   Cancels Adding the State
        #     if result == "Cancel":
        #         return False


        #     #	Opens Project Browser
        #     logger.debug("Opening Project Browser")

        #     self.core.projectBrowser()
        #     #	Switch to Media Tab
        #     if self.core.pb:
        #         self.core.pb.showTab("Media")
        # except:
        #     logger.warning("ERROR: Unable to Open Project Browser.")





        #	Opens Project Browser
        logger.debug("Opening Project Browser")

        self.core.projectBrowser()
        #	Switch to Media Tab
        if self.core.pb:
            self.core.pb.showTab("Media")


        # result = self.core.callback("requestImportPath", self)
        # for res in result:
        #     if isinstance(res, dict) and res.get("importPaths") is not None:

        #         # self.core.popup(f"res:  {res}")                             #   TESTING

        #         return res["importPaths"]

        # import MediaBrowser
        # ts = MediaBrowser.MediaBrowser(core=self.core, importState=self)
        # self.core.parentWindow(ts)
        # ts.exec_()
        # importPath = [ts.mediaPath]

        # self.core.popup(f"importPath:  {importPath}")                             #   TESTING


        # return importPath


    @err_catcher(name=__name__)
    def loadData(self, data):
        if "statename" in data:
            self.e_name.setText(data["statename"])
        if "statemode" in data:
            self.setStateMode(data["statemode"])
        if "taskname" in data:
            self.taskName = data["taskname"]
        if "nodenames" in data:
            self.nodeNames = eval(data["nodenames"])
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
        self.b_browse.clicked.connect(self.browse)
        self.b_browse.customContextMenuRequested.connect(self.openFolder)
        self.b_import.clicked.connect(self.importImage)
        self.b_importLatest.clicked.connect(self.importLatest)
        self.chb_autoUpdate.stateChanged.connect(self.autoUpdateChanged)
        self.cb_taskColor.currentIndexChanged.connect(lambda: self.setTaskColor(self.cb_taskColor.currentText()))


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
    def getSortKey(self):
        cacheData = self.core.paths.getCachePathData(self.getImportPath())
        return cacheData.get("product")
    

    @err_catcher(name=__name__)
    def browse(self):
        # import ProductBrowser

        # ts = ProductBrowser.ProductBrowser(core=self.core, importState=self)
        # self.core.parentWindow(ts)
        # ts.exec_()
        # importPath = ts.productPath

        # if importPath:
        #     result = self.importImage(update=True, path=importPath)
        #     if result:
        #         self.setImportPath(importPath)
        #     self.updateUi()

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
    def isShotCam(self, path=None):
        if not path:
            path = self.getImportPath()
        return path.endswith(".abc") and "/_ShotCam/" in path

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

        if not hasattr(self.core.appPlugin, "sm_import_importToApp"):
            self.core.popup("Import into %s is not supported." % self.core.appPlugin.pluginName)
            return

        result = self.runSanityChecks(impFileName)
        if not result:
            return

        cacheData = self.core.paths.getCachePathData(impFileName)
        self.taskName = cacheData.get("task")
        doImport = True


        # temporary workaround until all plugin handle the settings argument
        if self.core.appPlugin.pluginName == "Maya":
            importResult = self.core.appPlugin.sm_import_importToApp(
                self, doImport=doImport, update=update, impFileName=impFileName, settings=settings
            )
        else:
            importResult = self.core.appPlugin.sm_import_importToApp(
                self, doImport=doImport, update=update, impFileName=impFileName
            )

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

            if not result:
                msgStr = "Import failed: %s" % impFileName
                self.core.popup(msgStr, title="ImportFile")

        kwargs = {
            "state": self,
            "scenefile": fileName,
            "importfile": impFileName,
            "importedObjects": self.nodeNames,
        }
        self.core.callback("postImport", **kwargs)
        self.setImportPath(impFileName)
        self.stateManager.saveImports()
        self.updateUi()
        self.stateManager.saveStatesToScene()

        return result

    @err_catcher(name=__name__)
    def importLatest(self, refreshUi=True, selectedStates=True):
        if refreshUi:
            self.updateUi()

        path = self.getImportPath()

        latestVerDict = self.core.mediaProducts.getLatestVersionFromFilepath(path, includeMaster=True)

        # self.core.popup(f"latestVerDict:  {latestVerDict}")               #   TESTING

        files = self.core.mediaProducts.getFilesFromContext(latestVerDict)

        # self.core.popup(f"files:  {files}")               #   TESTING


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
        # latestVerDict = self.core.mediaProducts.getLatestVersionFromIdentifier(self.importData, includeMaster=True)

        # latestVerDict = self.core.mediaProducts.getVersionsFromContext(self.importData)


        lastestVerName = latestVerDict["version"]
        lastestVerPath = latestVerDict["path"]

        if latestVerDict:
            latestVersionData = {"version": lastestVerName, "path": lastestVerPath}
        else:
            latestVersionData = {}

        return curVerData, latestVersionData
    

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
                elif self.nodes:
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
        for file_data in self.files:
            aov = file_data["aov"]

            # self.core.popup(f"aov:  {aov}")                                      #    TESTING

            # Get the channels from the file using the provided method
            try:
                channels = self.core.media.getLayersFromFile(file_data["basefile"])
                # self.core.popup(f"channels:  {channels}")                                      #    TESTING

                if len(channels) < 1:
                    raise Exception
                
            except Exception as e:
                # Handle exceptions (e.g., invalid file) gracefully
                channels = ["Unknown Channel"]
                print(f"Error getting channels for file {file_data['basefile']}: {e}")

            # Check if this AOV already exists in the tree
            if aov not in aov_items:
                # Create a new item for the AOV
                aov_item = QTreeWidgetItem(root_item)
                aov_item.setText(0, aov)
                aov_items[aov] = aov_item
            else:
                # Reuse the existing AOV item
                aov_item = aov_items[aov]

            # Add channels as children of the AOV
            for channel in channels:
                channel_item = QTreeWidgetItem(aov_item)
                channel_item.setText(0, channel)

                # Optionally style the channel item, e.g., based on frame range
                frame_start = file_data["frame_start"]
                frame_end = file_data["frame_end"]
                if frame_start > frame_end:  # Example validation logic
                    channel_item.setBackground(0, QBrush(QColor("red")))

        # Optionally expand all AOV items
        for aov_item in aov_items.values():
            aov_item.setExpanded(True)



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


    # @err_catcher(name=__name__)
    def setTaskColor(self, color):                                              #   TODO

        self.core.popup(f"color:  {color}")                                      #    TESTING



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
        if len(self.nodes) > 0 and self.stateMode != "ApplyCache":
            message = baseText
            validNodes = [
                x for x in self.nodes if self.core.appPlugin.isNodeValid(self, x)
            ]
            if len(validNodes) > 0:
                for idx, val in enumerate(validNodes):
                    if idx > 5:
                        message += "..."
                        break
                    else:
                        message += self.core.appPlugin.getNodeName(self, val) + "\n"

                if not self.core.uiAvailable:
                    action = "Yes"
                    print("delete objects:\n\n%s" % message)
                else:
                    action = self.core.popupQuestion(message, title="Delete State", parent=self.stateManager)

                if action == "Yes":
                    self.core.appPlugin.deleteNodes(self, validNodes)

        getattr(self.core.appPlugin, "sm_import_preDelete", lambda x: None)(self)

    @err_catcher(name=__name__)
    def getStateProps(self):


        return {
            "statename": self.e_name.text(),
            "statemode": self.stateMode,
            "filepath": self.getImportPath(),
            "autoUpdate": str(self.chb_autoUpdate.isChecked()),
            "taskname": self.taskName,
            "nodenames": str(self.nodeNames),
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

