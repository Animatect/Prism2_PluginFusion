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
import sys

# Add parent directories to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.dirname(current_dir)  # Scripts directory
sys.path.append(scripts_dir)

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

from PrismUtils.Decorators import err_catcher

logger = logging.getLogger(__name__)



class Legacy3D_ImportClass(object):
    className = "Legacy3D_Import"
    listType = "Import"
    stateCategories = {"Import3d": [{"label": className, "stateType": className}]}

    @err_catcher(name=__name__)
    def setup(
        self,
        state,
        core,
        stateManager,
        node=None,
        importPath=None,
        stateData=None,
        openProductsBrowser=True,
        settings=None,
    ):
        
        self.state = state
        self.stateMode = "Legacy3D_Import"                          #   TODO  Handle setting stateMode for the UI label.

        self.core = core
        self.stateManager = stateManager
        self.fuseFuncts = self.core.appPlugin
        self.stateUID = None

        self.supportedFormats = [".abc", ".fbx"]

        self.taskName = ""
        self.setName = ""

        stateNameTemplate = "{entity}_{product}_{version}"
        self.stateNameTemplate = self.core.getConfig(
            "globals",
            "defaultImportStateName",
            configPath=self.core.prismIni,
        ) or stateNameTemplate
        self.e_name.setText(self.stateNameTemplate)
        self.l_name.setVisible(False)
        self.e_name.setVisible(False)

        self.oldPalette = self.b_importLatest.palette()
        self.updatePalette = QPalette()
        self.updatePalette.setColor(QPalette.Button, QColor(200, 100, 0))
        self.updatePalette.setColor(QPalette.ButtonText, QColor(255, 255, 255))

        #	Gets task color settings from the DCC settings
        self.taskColorMode = self.core.getConfig("Fusion", "taskColorMode")
        if self.taskColorMode == "Disabled":
            self.gb_taskColor.setHidden(True)
        else:
            self.gb_taskColor.setHidden(False)
            self.populateTaskColorCombo()

        createEmptyState = (
            QApplication.keyboardModifiers() == Qt.ControlModifier
            or not self.core.uiAvailable
        ) or not openProductsBrowser

        if (
            importPath is None
            and stateData is None
            and not createEmptyState
            and not self.stateManager.standalone
        ):
            importPaths = self.requestImportPaths()
            if importPaths:
                importPath = importPaths[-1]
                if len(importPaths) > 1:
                    for importPath in importPaths[:-1]:
                        stateManager.importFile(importPath)

        if importPath:
            _, extension = os.path.splitext(importPath)

            if extension.lower() not in self.supportedFormats:
                self.core.popup(f"{extension.upper()} is not supported with this Import State")
                return False

            self.setImportPath(importPath)
            result = self.importObject(settings=settings)

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

        if stateData is not None:
            self.loadData(stateData)

        tip = ("Create a simple Render Node.\n\n"
               "This will attach a render node to the entry point of the imported scene")
        self.b_createRenderNode.setToolTip(tip)

        self.nameChanged()
        self.updateUi()


    @err_catcher(name=__name__)
    def setStateMode(self, stateMode):
        self.stateMode = stateMode
        self.l_class.setText(stateMode)


    @err_catcher(name=__name__)
    def requestImportPaths(self):
        #   Calls the Prism Library window as per Prism settings from callback in Librries plugin

        # DISABLED - So will always open ProjectBrowser->Products tab
        #   vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
        # # result = self.core.callback("requestImportPath", self.stateManager)     #   TODO This causes issue on one machine when opening SM after import
        # result = self.core.callback("requestImportPath", self)     #   TODO This works but window behind SM.

        # #   If user selects from Library, returns file path
        # for res in result:
        #     if isinstance(res, dict) and res.get("importPaths") is not None:
        #         return res["importPaths"]

        #   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

        #   Calls Product Browser
        import ProductBrowser
        ts = ProductBrowser.ProductBrowser(core=self.core, importState=self)
        self.core.parentWindow(ts)
        ts.exec_()
        #   If user selects from Library, returns file path
        importPath = [ts.productPath]
        return importPath


    @err_catcher(name=__name__)
    def loadData(self, data):
        if "statename" in data:
            self.e_name.setText(data["statename"])
        if "stateUID" in data:
            self.stateUID = data["stateUID"]
        if "statemode" in data:
            self.setStateMode(data["statemode"])
        if "taskColor" in data:
            idx = self.cb_taskColor.findText(data["taskColor"])
            if idx != -1:
                self.cb_taskColor.setCurrentIndex(idx)
        if "filepath" in data:
            data["filepath"] = getattr(
                self.core.appPlugin, "sm_import_fixImportPath", lambda x: x
            )(data["filepath"])
            self.setImportPath(data["filepath"])
        if "taskname" in data:
            self.taskName = data["taskname"]
        if "setname" in data:
            self.setName = data["setname"]
        if "autoUpdate" in data:
            self.chb_autoUpdate.setChecked(eval(data["autoUpdate"]))

        self.core.callback("onStateSettingsLoaded", self, data)


    @err_catcher(name=__name__)
    def connectEvents(self):
        self.e_name.textChanged.connect(self.nameChanged)
        self.e_name.editingFinished.connect(self.stateManager.saveStatesToScene)
        #   This is the "Browse" button
        self.b_browse.clicked.connect(self.browse)
        self.b_browse.customContextMenuRequested.connect(self.openFolder)
        #   This is the "Re-Import" button
        self.b_import.clicked.connect(lambda: self.importObject(update=True))
        self.b_importLatest.clicked.connect(self.importLatest)
        self.chb_autoUpdate.stateChanged.connect(self.autoUpdateChanged)
        self.b_createRenderNode.clicked.connect(self.createRenderNode)
        self.cb_taskColor.currentIndexChanged.connect(lambda: self.setTaskColor(self.cb_taskColor.currentText()))


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
    def setTaskColor(self, color):
        #   Get rgb color from dict
        colorRGB = self.fuseFuncts.fusionToolsColorsDict[color]
        #   Color tool
        self.fuseFuncts.colorLegacy3DTaskNodes(self.stateUID, colorRGB)

        self.stateManager.saveImports()
        self.stateManager.saveStatesToScene()


    @err_catcher(name=__name__)
    def nameChanged(self, text=None):
        text = self.e_name.text()
        cacheData = self.core.paths.getCachePathData(self.getImportPath())
        if cacheData.get("type") == "asset":
            cacheData["entity"] = os.path.basename(cacheData.get("asset_path", ""))
        elif cacheData.get("type") == "shot":
            shotName = self.core.entities.getShotName(cacheData)
            if shotName:
                cacheData["entity"] = shotName

        num = 0

        try:
            if "{#}" in text:
                while True:
                    cacheData["#"] = num or ""
                    name = text.format(**cacheData)
                    for state in self.stateManager.states:
                        if state.ui.listType != "Import":
                            continue

                        if state is self.state:
                            continue

                        if state.text(0) == name:
                            num += 1
                            break
                    else:
                        break
            else:
                name = text.format(**cacheData)

        except Exception as e:
            name = text

        self.state.setText(0, name)

        self.stateManager.saveImports()
        self.stateManager.saveStatesToScene()


    @err_catcher(name=__name__)
    def getSortKey(self):
        cacheData = self.core.paths.getCachePathData(self.getImportPath())
        return cacheData.get("product")


    @err_catcher(name=__name__)
    def browse(self):
        import ProductBrowser

        ts = ProductBrowser.ProductBrowser(core=self.core, importState=self)
        self.core.parentWindow(ts)
        ts.exec_()
        importPath = ts.productPath

        if importPath:
            result = self.importObject(update=True, path=importPath)
            if result:
                self.setImportPath(importPath)
            self.updateUi()


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

        self.stateManager.saveImports()
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
            self.core.products.getVersionInfoPathFromProductFilepath(cachePath)
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
    def importObject(self, update=False, path=None, settings=None):

        if not update:
            self.stateUID = self.fuseFuncts.createUUID()

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

        cacheData = self.core.paths.getCachePathData(impFileName)

        self.taskName = cacheData.get("task")
        doImport = True
        
		#	Set node name
        productName = cacheData["product"]
        productVersion = cacheData["version"]
        nodeName = f"{productName}_{productVersion}"

        nodeData = {"nodeName": nodeName,
                    "nodeUID": self.stateUID,
                    "version": productVersion,
                    "Filepath": impFileName,
                    "product": productName,
                    "format": "abc"}

        #   Call import function
        importResult = self.core.appPlugin.importLegacy3D(self,
                                                UUID=self.stateUID,
                                                nodeData=nodeData,
                                                update=update)

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

            if not result:
                msgStr = "Import failed: %s" % impFileName
                self.core.popup(msgStr, title="ImportFile")

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

        return result


    @err_catcher(name=__name__)
    def importLatest(self, refreshUi=True, selectedStates=True):
        if refreshUi:
            self.updateUi()

        latestVersion = self.core.products.getLatestVersionFromPath(
            self.getImportPath()
        )
        filepath = self.core.products.getPreferredFileFromVersion(latestVersion)
        if not filepath:
            if not self.chb_autoUpdate.isChecked():
                self.core.popup("Couldn't get latest version.")
            return

        prevState = self.stateManager.applyChangesToSelection
        self.stateManager.applyChangesToSelection = False
        self.setImportPath(filepath)
        self.importObject(update=True)
        if selectedStates:
            selStates = self.stateManager.getSelectedStates()
            for state in selStates:
                if state.__hash__() == self.state.__hash__():
                    continue

                if hasattr(state.ui, "importLatest"):
                    state.ui.importLatest(refreshUi=refreshUi, selectedStates=False)

        self.stateManager.applyChangesToSelection = prevState

        self.stateManager.saveImports()
        self.stateManager.saveStatesToScene()


    @err_catcher(name=__name__)
    def checkLatestVersion(self):
        path = self.getImportPath()
        curVersionName = self.core.products.getVersionFromFilepath(path) or ""
        curVersionData = {"version": curVersionName, "path": path}
        latestVersion = self.core.products.getLatestVersionFromPath(path)
        if latestVersion:
            latestVersionData = {"version": latestVersion["version"], "path": latestVersion["path"]}
        else:
            latestVersionData = {}

        return curVersionData, latestVersionData
    

    #   Creates simple USD Scene with uMerge and URenderer
    @err_catcher(name=__name__)
    def createRenderNode(self):
        # if self.stateManager.standalone:
        #     return
        
        # UUID = self.stateUID
        
        # result = self.fuseFuncts.createUsdScene(self, UUID)
        print("clicked")


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
            curVersionName = self.core.products.getMasterVersionLabel(filepath)
        else:
            curVersionName = curVersion.get("version")

        if latestVersion.get("version") == "master":
            filepath = latestVersion["path"]
            latestVersionName = self.core.products.getMasterVersionLabel(filepath)
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

                #   Color green if is latest version
                if useSS:
                    self.b_importLatest.setStyleSheet(
                        "QPushButton { background-color: rgb(0,130,0); }"
                    )
                else:
                    self.b_importLatest.setPalette(self.oldPalette)

        self.nameChanged()
        self.setStateColor(status)
        getattr(self.core.appPlugin, "sm_import_updateUi", lambda x: None)(self)


    @err_catcher(name=__name__)
    def preDelete(self, item=None):
        try:
            message = "Do you also want to delete the connected objects?\n\n"
            if not self.core.uiAvailable:
                action = "Yes"
                print("delete objects:\n\n%s" % message)
            else:
                action = self.core.popupQuestion(message, title="Delete State", parent=self.stateManager)

            if action == "Yes":
                self.core.appPlugin.deleteNodes(self.stateUID)

            getattr(self.core.appPlugin, "sm_import_preDelete", lambda x: None)(self)
        except:
            logger.warning("ERROR: Unable to remove Lgacy3D scene completely from Comp")


    @err_catcher(name=__name__)
    def getStateProps(self):
        return {
            "statename": self.e_name.text(),
            "stateUID": self.stateUID,
            "statemode": self.stateMode,
            "taskColor": self.cb_taskColor.currentText(),
            "filepath": self.getImportPath(),
            "autoUpdate": str(self.chb_autoUpdate.isChecked()),
            "taskname": self.taskName,
            "setname": self.setName,
        }
