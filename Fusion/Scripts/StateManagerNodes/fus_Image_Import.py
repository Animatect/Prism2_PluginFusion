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

#   Global Colors
COLOR_GREEN = QColor(0, 130, 0)
COLOR_ORANGE = QColor(200, 100, 0)
COLOR_RED = QColor(130, 0, 0)
COLOR_BLACK = QColor(0, 0, 0, 0)

#   Color names for beauty/color pass
COLORNAMES = ["color", 
              "beauty",
              "combined",
              "diffuse",
              "diffcolor",
              "diffusecolor"]

#   Width of State Thumbnail
STATE_THUMB_WIDTH = 270               #   TODO HARDCODED with width for initil size issue.

#   Icon to be used for State
scriptDir = os.path.dirname(os.path.dirname(__file__))
STATE_ICON = os.path.join(scriptDir, "Icons", "Image.png")

#   Qt Item data naming
ITEM_ROLE_DATA = Qt.UserRole + 1
ITEM_ROLE_COLOR = Qt.UserRole + 2
ITEM_ROLE_CHECKBOX = Qt.UserRole + 3


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

    ####   Do one of the following:     ####
        
        ##   1. Load State from Comp Data
        if stateData is not None:
            self.loadData(stateData)

            logger.debug("Loaded State from saved data")                    #   TODO


        ##   2. If passed from FusFuncts. Receive importData via "settings" kwarg
        elif settings:
            self.loadData(settings)

            logger.debug("Loaded State from data passed from ProjectBrowser Import")        #   TODO

        ##   3. Opens Media Popup to select import
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
                logger.debug("Media Import cancelled")
                return False
            
            if requestResult == "Empty":
                return False
            
            if not requestResult:
                logger.warning("ERROR: Unable to Import Image from MediaBrowser.")
                self.core.popup("Unable to Import Image from MediaBrowser.")
                return False
        
        ##   4. If error
        else:
            logger.warning("ERROR: Unable to Import Image.")
            self.core.popup("Unable to Import Image.")
            return False

        getattr(self.core.appPlugin, "sm_import_startup", lambda x: None)(self)

        self.connectEvents()
        self.nameChanged()
        self.updateUi()

        self.updateAovChnlTree()
        self.createStateThumbnail()
        self.createAovThumbs()


    @err_catcher(name=__name__)
    def connectEvents(self):
        self.e_name.textChanged.connect(self.nameChanged)
        self.e_name.editingFinished.connect(self.stateManager.saveStatesToScene)
        self.cb_taskColor.currentIndexChanged.connect(lambda: self.setToolColor(self.cb_taskColor.currentText()))
        self.b_focusView.clicked.connect(self.focusView)
        self.b_selectTools.clicked.connect(self.selectTools)
        self.lw_objects.itemPressed.connect(self.onAovItemClicked)                              #   When AOV item clicked
        self.b_browse.clicked.connect(self.browse)                                              #   Select Version Button
        self.b_browse.customContextMenuRequested.connect(self.openFolder)                       #   RCL Select Version Button
        self.b_importLatest.clicked.connect(lambda: self.importLatest(selectedStates=False))    #   Import Latest Button
        self.chb_autoUpdate.stateChanged.connect(self.autoUpdateChanged)                        #   Latest Checkbox
        self.b_importAll.clicked.connect(lambda: self.importAll(refreshUi=True))
        self.b_importSel.clicked.connect(self.importSelected)
        self.b_import.clicked.connect(self.imageImport)                                         #   Re-Import Button        TODO


    #########################
    #                       #
    #       Wrapped         #
    #   Prism Functions     #
    #                       #
    #########################

    @err_catcher(name=__name__)
    def getVersionInfoPath(self, cachePath):
        return self.core.getVersioninfoPath(
            self.core.mediaProducts.getMediaVersionInfoPathFromFilepath(cachePath)
            )
    
    @err_catcher(name=__name__)
    def getMasterVersionLabel(self, filepath):
        return self.core.mediaProducts.getMasterVersionLabel(filepath)
    
    @err_catcher(name=__name__)
    def getLatestVersion(self, context, includeMaster):
        mediaProducts = self.fuseFuncts.core.mediaProducts
        return mediaProducts.getLatestVersionFromIdentifier(context, includeMaster=includeMaster)
    
    @err_catcher(name=__name__)
    def getPixmapFromExrPath(self, filePath, width, height, channel, allowThumb):
        pxmap = self.core.media.getPixmapFromExrPath(filePath, width=width, height=height, channel=channel, allowThumb=allowThumb)
        return pxmap

    @err_catcher(name=__name__)
    def getPixmapFromPath(self, filePath, width, height):
        pxmap = self.core.media.getPixmapFromPath(filePath, width=width, height=height)
        return pxmap
    
    @err_catcher(name=__name__)
    def getCurrentVersion(self):
        self.mediaBrowser = self.mediaChooser.w_browser
        self.mediaPlayer = self.mediaBrowser.w_preview.mediaPlayer
        return self.mediaBrowser.getCurrentVersion()
    
    @err_catcher(name=__name__)
    def getAOVsFromVersion(self, version):
        return self.core.mediaProducts.getAOVsFromVersion(version)
    
    @err_catcher(name=__name__)
    def compGetImportPasses(self):
        self.mediaBrowser = self.mediaChooser.w_browser
        self.mediaPlayer = self.mediaBrowser.w_preview.mediaPlayer
        return self.mediaPlayer.compGetImportPasses()
    
    @err_catcher(name=__name__)
    def compGetImportSource(self):
        self.mediaBrowser = self.mediaChooser.w_browser
        self.mediaPlayer = self.mediaBrowser.w_preview.mediaPlayer
        return self.mediaPlayer.compGetImportSource()
    
    @err_catcher(name=__name__)
    def getFilesFromContext(self, aovItem):
        return self.fuseFuncts.core.mediaProducts.getFilesFromContext(aovItem)
    
    @err_catcher(name=__name__)
    def getLayersFromFile(self, filepath):
        return self.fuseFuncts.core.media.getLayersFromFile(filepath)

    @err_catcher(name=__name__)
    def getVideoDuration(self, filepath):
        return self.fuseFuncts.core.media.getVideoDuration(filepath)


    #########################
    #                       #
    #         STATE         #
    #                       #
    #########################


    @err_catcher(name=__name__)
    def setStateMode(self, stateMode):
        self.stateMode = stateMode
        self.l_class.setText(stateMode)


    @err_catcher(name=__name__)
    def nameChanged(self, text=None):                                   #   TODO -- Cleanup
        name = self.e_name.text()

        if text:
            name = text

        else:
            try:
                name = f"{self.identifier}__{self.version}"

            except Exception as e:                                          #   TODO
                name = text

        #   Set the name for the State list
        self.state.setText(0, name)
        #   Add icon to State name
        self.state.setIcon(0, QIcon(STATE_ICON))


    @err_catcher(name=__name__)
    def browse(self, refreshUi=True):                               #   TODO
        self.callMediaWindow()

        if refreshUi:
            self.updateUi()
            self.updateAovChnlTree()
            self.createAovThumbs()


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
        # self.updateUi()
        self.stateManager.saveStatesToScene()


    @err_catcher(name=__name__)
    def autoUpdateChanged(self, checked):
        self.w_importLatest.setVisible(not checked)

        if checked:
            curVersion, latestVersion = self.checkLatestVersion()
            if self.chb_autoUpdate.isChecked():
                if curVersion.get("version") and latestVersion.get("version") and curVersion["version"] != latestVersion["version"]:
                    self.importLatest(refreshUi=True, selectedStates=False)

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
        versionInfoPath = self.getVersionInfoPath(cachePath)

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
   
    
    #########################
    #                       #
    #          UI           #
    #                       #
    #########################


    @err_catcher(name=__name__)
    def callMediaWindow(self):
        self.selMediaContext = None
            
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
            result = self.makeImportData(self.selMediaContext)

        if clicked == "identifier":
            result = self.importLatest(refreshUi=False, selectedStates=False, setChecked=True)
        
        if not result:
            return False
        if result == "Empty":
            return result
        else:
            return True
        

    @err_catcher(name=__name__)
    def updateUi(self):
        versions = self.checkLatestVersion()
        if versions:
            curVersion, latestVersion = versions
        else:
            curVersion = latestVersion = ""

        if curVersion.get("version") == "master":
            filepath = self.getImportPath()
            curVersionName = self.getMasterVersionLabel(filepath)
        else:
            curVersionName = curVersion.get("version")

        if latestVersion.get("version") == "master":
            filepath = latestVersion["path"]
            latestVersionName = self.getMasterVersionLabel(filepath)
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

        getattr(self.core.appPlugin, "sm_import_updateUi", lambda x: None)(self)


    @err_catcher(name=__name__)                             #   TODO - Add functionality to color based on AOV status
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


    #   Add color items to the combobox
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


    #   Populates the AOV tree and adds file data to each item
    @err_catcher(name=__name__)
    def updateAovChnlTree(self):
        #   Setup UI
        self.lw_objects.setHeaderHidden(True)
        self.lw_objects.setMinimumHeight(350)

        #   Clear the list
        self.lw_objects.clear()
        #   Initialize the status icon
        self.lw_objects.setItemDelegate(statusColorDelegate(self.lw_objects))
        
        # Create a root item
        root_item = QTreeWidgetItem(self.lw_objects)
        root_item.setText(0, f"{self.identifier}_{self.version}")
        root_item.setExpanded(True)  # Expand the root item

        #   Add checkbox actions to item
        self.setupAovActions(root_item)

        # Dictionary to store file data
        basefile_dict = {}

        #   To capture if there are AOVs
        hasAOVs = False

        # Organize files by basefile
        for fileData in self.importData["files"]:
            basefile = fileData["basefile"]
            aov = fileData.get("aov", None)
            channel = fileData["channel"]
            frameRange = f"{fileData['frame_start']} - {fileData['frame_end']}"

            if basefile not in basefile_dict:
                basefile_dict[basefile] = {"aov_items": {}, "channels": [], "frameRange": frameRange}
            
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
                #   Set if has AOVs
                hasAOVs = True
                #   Itterate through each AOV
                for aov, channels in data["aov_items"].items():
                    aov_item = QTreeWidgetItem(root_item)
                    aov_item.setText(0, f"{aov}    (aov)    ({data['frameRange']})")
                    aov_item.setExpanded(True)

                    #   Add checkbox actions to item
                    self.setupAovActions(aov_item)

                    for channel in channels:
                        channel_item = QTreeWidgetItem(aov_item)
                        channel_item.setText(0, f"{channel}    (channel)")
                        channel_item.setExpanded(True)

                        # Find the corresponding fileData for this channel
                        correct_fileData = next(
                            (f for f in self.importData["files"]
                            if f["basefile"] == basefile and f.get("aov") == aov and f["channel"] == channel),
                            None
                        )

                        if correct_fileData:
                            #   Store fileData in tree item
                            channel_item.setData(0, ITEM_ROLE_DATA, correct_fileData)

                        #   Add checkbox actions to item
                        self.setupAovActions(channel_item)

            # If no AOVs, list channels directly under the root
            for channel in data["channels"]:
                channel_item = QTreeWidgetItem(root_item)
                channel_item.setText(0, f"{channel}    (channel)")
                channel_item.setExpanded(True)

                # Find the corresponding fileData for this channel
                correct_fileData = next(
                    (f for f in self.importData["files"]
                    if f["basefile"] == basefile and f["channel"] == channel),
                    None
                )

                if correct_fileData:
                    #   Store fileData in tree item
                    channel_item.setData(0, ITEM_ROLE_DATA, correct_fileData)

                #   Add checkbox actions to item
                self.setupAovActions(channel_item)

        #   If there are no AOVs, add framerange under the MediaID
        if not hasAOVs:
            root_item.setText(0, f"{self.identifier}_{self.version}    ({data['frameRange']})")

        self.updateAovStatus()


    #   Sets item checkbox and saves it to the item data                    #   TODO add code to save it to importData
    @err_catcher(name=__name__)
    def setCheckbox(self, item, checked):
        #   If passed a bool, convert to Qt.Checked type
        if isinstance(checked, bool):
            if checked:
                checked = Qt.Checked
            else:
                checked = Qt.Unchecked
        #   Set the checkbox
        item.setCheckState(0, checked)
        #   Save to item's data
        item.setData(0, ITEM_ROLE_CHECKBOX, checked)


    #   Adds checkbox and checkbox selection behaviour
    @err_catcher(name=__name__)
    def setupAovActions(self, item):
        # Make item checkable
        item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)

        # Check if there's a saved state for the checkbox
        if item.data(0, ITEM_ROLE_CHECKBOX) is not None:
            checked = item.data(0, ITEM_ROLE_CHECKBOX)
            self.setCheckbox(item, checked)
        else:
            item.setCheckState(0, Qt.Unchecked)
            self.setCheckbox(item, checked=False)


    #   Adds checkbox selection behaviours
    @err_catcher(name=__name__)
    def onAovItemClicked(self, item, column):
        if item.flags() & Qt.ItemIsUserCheckable:
            #   Get current checked state
            current_checked = item.checkState(0)
            #   Reverse the checked state
            new_checked = Qt.Unchecked if current_checked == Qt.Checked else Qt.Checked
            #   Set the checkbox with new state
            self.setCheckbox(item, new_checked)
            #   Sets tree checkboxes based on selection
            self.onCheckboxStateChanged(item, column)

        #   Call the AOV coloring after toggling
        self.updateAovStatus()
 

    #   Handles checkbox selection of the children and parents
    @err_catcher(name=__name__)
    def onCheckboxStateChanged(self, item, column):
        checked = item.checkState(0)
        item.setData(0, ITEM_ROLE_CHECKBOX, checked)

        # Temporarily block signals to avoid recursion
        self.lw_objects.blockSignals(True)

        # Recursively apply the state to all child items
        self._toggleCheckboxes(item, checked)

        # Update the parent check state
        self._updateParentCheckbox(item)

        # Re-enable signals
        self.lw_objects.blockSignals(False)


    @err_catcher(name=__name__)
    def _toggleCheckboxes(self, item, checked):
        for row in range(item.childCount()):
            child_item = item.child(row)
            self.setCheckbox(child_item, checked)

            # Recurse into the child's children
            self._toggleCheckboxes(child_item, checked)


    @err_catcher(name=__name__)
    def _updateParentCheckbox(self, item):
        parent = item.parent()
        #   Stop at the root parent
        if not parent:
            return

        #   Find which children items are checked
        all_checked = all(parent.child(i).checkState(0) == Qt.Checked for i in range(parent.childCount()))
        any_checked = any(parent.child(i).checkState(0) == Qt.Checked for i in range(parent.childCount()))
        any_unchecked = any(parent.child(i).checkState(0) == Qt.Unchecked for i in range(parent.childCount()))
        any_partially_checked = any(parent.child(i).checkState(0) == Qt.PartiallyChecked for i in range(parent.childCount()))

        #   Set parent's checkbox based on its children
        if all_checked:
            checked = Qt.Checked
        elif any_partially_checked:
            checked = Qt.PartiallyChecked
        elif any_checked and any_unchecked:
            checked = Qt.PartiallyChecked
        else:
            checked = Qt.Unchecked

        self.setCheckbox(parent, checked)

        # Stop at the root parent
        if parent.parent():
            self._updateParentCheckbox(parent)


    @err_catcher(name=__name__)
    def updateAovStatus(self):
        stateUIDs = self.fuseFuncts.getUIDsFromStateUIDs("import2d", self.stateUID, includeConn=False)

        # Get child AOV items
        aovItems = self.getAovItems(self.lw_objects)

        for item in aovItems:
            #   Removes and then skips unchecked items
            if item.checkState(0) != Qt.Checked:
                item.setData(0, ITEM_ROLE_COLOR, None)
                continue

            id_match = False
            ver_match = False

            itemData = item.data(0, ITEM_ROLE_DATA)
            if not itemData:
                continue  

            # Extract necessary values from itemData
            item_mediaId = itemData.get("identifier")
            item_aov = itemData.get("aov")
            item_channel = itemData.get("channel")
            item_version = itemData.get("version")

            # Check each stateUID
            for uid in stateUIDs:
                if not self.fuseFuncts.nodeExists(uid):
                    continue

                uidData = self.fuseFuncts.getNodeInfo("import2d", uid)
                if not uidData:  
                    continue  

                mediaId = uidData.get("mediaId")
                aov = uidData.get("aov")
                channel = uidData.get("channel")
                version = uidData.get("version")

                # Check if all required fields match
                if (
                    mediaId == item_mediaId and 
                    (aov is None or aov == item_aov) and
                    (channel is None or channel == item_channel)
                ):
                    id_match = True

                    if version == item_version:
                        ver_match = True
                        break

            # Assign color based on match status
            if ver_match:
                color = COLOR_GREEN
            elif id_match:
                color = COLOR_ORANGE
            else:
                color = COLOR_RED

            item.setData(0, ITEM_ROLE_COLOR, color)



    #########################
    #                       #
    #       Thumbnails      #
    #                       #
    #########################

    #   Get PixMap from Filepath or Fallback image
    @err_catcher(name=__name__)
    def getPixMap(self, filePath, width=None, height=None, channel=None, allowThumb=True):
        fallbackPmap = self.core.media.getFallbackPixmap()

        try:
            if os.path.exists(filePath):
                ext = os.path.splitext(filePath)[1]

                if ext.lower() == ".exr":
                    pixMap = self.getPixmapFromExrPath(filePath, width=width, height=height, channel=channel, allowThumb=allowThumb)
                else:
                    pixMap = self.getPixmapFromPath(filePath, width=width, height=height)

            else:
                logger.warning("ERROR:  Unable to create pixmap - filepath does not exist")
                raise Exception
        except:
            logger.warning("ERROR:  Unable to create thumbnail from filepath.  Using fallback.")
            pixMap = fallbackPmap

        return pixMap
    

    #   Gets Prism fallback image and scales pixmap
    @err_catcher(name=__name__)
    def getFallbackThumb(self, width):
        try:
            fallbackPixMap = self.core.media.getFallbackPixmap()
        except:
            logger.warning("ERROR:  Unable to get Prism Fallback Thumbnail")
            return ""

        try:
            # Maintain aspect ratio: Calculate new height
            aspectRatio = fallbackPixMap.height() / fallbackPixMap.width()
            new_height = int(width * aspectRatio)

            # Scale the pixmap to fill the QLabel's width while maintaining aspect ratio
            scaledPixmap = fallbackPixMap.scaled(STATE_THUMB_WIDTH, new_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)

            logger.debug("Created scaled fallback thumbnail")
            return scaledPixmap, width, new_height
        
        except:
            logger.warning("ERROR:  Unable to create Fallback Thumbnail")
            return fallbackPixMap, width, width

    
    #   Creates State Thumbnail using threading
    @err_catcher(name=__name__)
    def createStateThumbnail(self):
        if not hasattr(self, 'l_thumb'):
            logger.warning("ERROR: QLabel 'l_thumb' not found in UI")
            return
        
        #   Get temp fallback thumbnail pixmap
        temp_pixmap, temp_width, temp_height = self.getFallbackThumb(STATE_THUMB_WIDTH)

        try:
            # Apply the scaled pixmap
            self.l_thumb.setPixmap(temp_pixmap)
            self.l_thumb.adjustSize()

            self.l_thumb.setFixedHeight(temp_height)
            self.l_thumb.setFixedWidth(temp_width)
            self.l_thumb.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            # Add a border
            self.l_thumb.setStyleSheet("border: 1px solid gray;")
        except:
            logger.warning("ERROR:  Unable to set State Thumbnail")
            return

        #   Get state thumb width constant
        thumb_width = STATE_THUMB_WIDTH

        try:
            #   Get child AOV items
            aovItems = self.getAovItems(self.lw_objects)

            #   Default to use Prism thumbnails
            beautyFilepath = None
            channel = None
            allowThumb = True

            #   Try and find beauty/color AOV
            for item in aovItems:
                itemData = item.data(0, ITEM_ROLE_DATA)
                
                if itemData.get("aov") and itemData["aov"].lower() in COLORNAMES:
                    beautyFilepath = itemData["basefile"]

                    #   If user selected "All" in DCC settings use original image
                    if self.fuseFuncts.useAovThumbs == "All":
                        channel = itemData["channel"]
                        allowThumb = False

                    break

            if not beautyFilepath:
            # If no AOV match, try and find beauty/color channel
                for item in aovItems:
                    itemData = item.data(0, ITEM_ROLE_DATA)
                    if any(color in itemData.get("channel", "").lower() for color in COLORNAMES):
                        beautyFilepath = itemData["basefile"]
                        
                        #   If user selected "All" in DCC settings use original image
                        if self.fuseFuncts.useAovThumbs == "All":
                            channel = itemData["channel"]
                            allowThumb = False

                        break

            # If still no match, use the first available file
            if not beautyFilepath:
                beautyFilepath = self.importData["files"][0]["basefile"]

        except:
            logger.warning("ERROR:  Unable to set State Thumbnail")
            return

        # Create thumb thread
        self.createThumb_thread = ThumbnailThread(self.l_thumb, beautyFilepath, thumb_width, temp_height, channel, allowThumb, self.getPixMap)
        # Connect the signal to update the QLabel when the thumbnail is ready
        self.createThumb_thread.thumbnail_ready.connect(self.updateThumbnail)
        # Start the thread
        self.createThumb_thread.start()


    #   Generates pixmap for each AOV item with threading
    @err_catcher(name=__name__)
    def createAovThumbs(self):
        if self.fuseFuncts.useAovThumbs == "Disabled":
            return

        #   Get all child items form AOV list
        imageItems = self.getAovItems(self.lw_objects)
        #   Store list of active threads
        self.thumb_threads = []

        for item in imageItems:
            #   Get data from item
            itemData = item.data(0, ITEM_ROLE_DATA)
            #   Skip item if no data
            if not itemData:
                continue

            #   Get data items
            origFilePath = itemData.get("basefile")
            channel = itemData.get("channel")

            #   Get source file for thumb generation
            try:
                #   Use Prism thumbnail
                if self.core.media.getUseThumbnailForFile(origFilePath):
                    thumbPath = self.core.media.getThumbnailPath(origFilePath)
                else:
                    raise FileNotFoundError("Thumbnail not available")
            except FileNotFoundError:
                #   Use original thumbnail
                thumbPath = origFilePath

            #   Get width based on DCC settings
            width = self.aovThumbWidth

            # Load the original image to get its size
            orig_pixmap = QPixmap(thumbPath)
            if orig_pixmap.isNull():
                continue

            #   Get sizes
            orig_width = orig_pixmap.width()
            orig_height = orig_pixmap.height()
            height = int((width / orig_width) * orig_height) if orig_width else width

            #   Default to using Prism thumbnail
            path = thumbPath
            allowThumb = True

            #   If user selects All in DCC settings, use original image
            if self.fuseFuncts.useAovThumbs == "All":
                if channel and channel.lower() not in COLORNAMES:
                    path = origFilePath
                    allowThumb = False

            # Create thumbnail thread
            thumb_thread = ThumbnailThread(item, path, width, height, channel, allowThumb, self.getPixMap)
            #   Store thread
            self.thumb_threads.append(thumb_thread)
            #   Connect thread finish
            thumb_thread.thumbnail_ready.connect(self.setThumbToolTip)
            #   Launch thread
            thumb_thread.start()


    #   Get list of child items
    @err_catcher(name=__name__)
    def getAovItems(self, treeWidget):
        imageItems = []

        def traverse(item):
            if item.childCount() == 0:
                imageItems.append(item)
            else:
                for i in range(item.childCount()):
                    traverse(item.child(i))

        # Iterate over top-level items
        for i in range(treeWidget.topLevelItemCount()):
            traverse(treeWidget.topLevelItem(i))

        return imageItems
    

    #   Create html pixmap for AOV items
    @err_catcher(name=__name__)
    def setThumbToolTip(self, item, pixMap, new_height, new_width):
        try:
            # Convert QPixmap to Base64
            byte_array = QByteArray()
            buffer = QBuffer(byte_array)
            buffer.open(QIODevice.WriteOnly)
            pixMap.save(buffer, "PNG")

            base64_data = byte_array.toBase64().data().decode()
            thumbTip = f'<img src="data:image/png;base64,{base64_data}" width="{new_width}"/>'

            #   Set Tool Tip
            item.setToolTip(0, thumbTip)
        except:
            logger.warning("ERROR:  Unable to set AOV thumb tooltip")


    #   Replace placeholder thumb with generated pixmap
    @err_catcher(name=__name__)
    def updateThumbnail(self, item, pixMap, new_height, new_width):
        # This will be called when the thumbnail is ready in the thread
        try:
            # Update QLabel with new pixmap and size
            item.setPixmap(pixMap)
            item.setFixedHeight(new_height)
            item.setFixedWidth(new_width)

            # Adjust the size to the pixmap
            item.adjustSize()
        except:
            logger.warning("ERROR:  Unable to set State thumbnail")




    #########################
    #                       #
    #         DATA          #
    #                       #
    #########################


    @err_catcher(name=__name__)
    def makeImportData(self, context):
        self.context = context

        # version = self.mediaBrowser.getCurrentVersion()
        version = self.getCurrentVersion()

        if not version:
            logger.warning(f"ERROR: There are no Versions for this Media Identifier")
            self.core.popup("There are no Versions for this Media Identifier")
            return "Empty"

        #   Get data from various sources
        aovDict = self.getAOVsFromVersion(version)

        #	Get sourceData based on passes - used to get framerange
        if len(aovDict) > 1:
            sourceData = self.compGetImportPasses() #   has AOV's
        else:
            sourceData = self.compGetImportSource() #   no AOV's

        mediaType = context["mediaType"]

        try:
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
            
            #	Add additional items if they exist
            for key in ["asset", "sequence", "shot"]:
                if key in context:
                    importData[key] = context[key]
            
        except Exception as e:
            logger.warning(f"ERROR: Unable to make base importData dict: {e}")
            return {}

        files = []

        #   If there are Prism AOV's (for example not for 2d Renders)
        hasAOVs = bool(aovDict)

        # If AOVs exist, use aovDict and sourceData, otherwise use Context
        dataPairs = zip(aovDict, sourceData) if hasAOVs else [(context, sourceData[0])]

        for aovItem, sourceItem in dataPairs:
            if hasAOVs:
                aovItem["mediaType"] = mediaType
                filesList = self.getFilesFromContext(aovItem)
                aov = aovItem["aov"]
            else:
                filesList = self.getFilesFromContext(context)
                aov = None

            basefile = filesList[0]

            # Get file extension
            extension = self.getImageExtension(context, basefile)

            # Get frame start and end
            frame_start, frame_end = self.getFramesFromSourceData(extension, sourceItem, basefile)

            # Get channels list
            channels = self.getLayersFromFile(basefile)

            if len(channels) == 0:
                channels = ["Color"]

            for channel in channels:
                # Create file dictionary
                fileDict = {
                    "basefile": basefile,
                    "identifier": context["identifier"],
                    "channel": channel,
                    "version": context["version"],
                    "frame_start": frame_start,
                    "frame_end": frame_end,
                    "stateUID": self.stateUID
                }

                # Add additional AOV-specific fields if applicable
                if hasAOVs:
                    fileDict.update({"aov": aov})

                # Append to files list
                files.append(fileDict)

        # Add the files to the importData
        importData["files"] = files

        #   Add additional data if exist
        importData["extension"] = extension

        if importData["mediaType"] in ["3drenders", "external"]:
            try:
                importData["aovs"] = self.getAovNamesFromAovDict(aovDict)
            except Exception as e:
                logger.warning(f"ERROR: Unable to get AOV names list: {e}")

        try:
            if "channel" in context:
                importData["channel"] = context["channel"]

            channels = self.getLayersFromFile(basefile)
            importData["channels"] = channels

        except Exception as e:
            logger.warning(f"ERROR: Unable to add channel data to importData: {e}")

        if "versionPaths" in context:
            importData["versionPaths"] = context["versionPaths"]

        if "redirect" in context:
            importData["redirect"] = context["redirect"]

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
    

    @err_catcher(name=__name__)
    def getAovNamesFromAovDict(self, aovDict:list) -> list:
        try:
            aovNames = []
            for aovItem in aovDict:
                aovNames.append(aovItem["aov"])
            return aovNames
        except:
            logger.warning(f"ERROR:  Unable to get AOV names from : {aovDict}")
            return None


    @err_catcher(name=__name__)                         #   TODO NEEDED???
    def setSelectedMedia(self, selResult):
        self.selResult = selResult  # Save the selected media


    @err_catcher(name=__name__)
    def getImageExtension(self, context, basefile):
        #   Get file extension
        if "extension" in context:
            extension = context["extension"]
        else:
            _, extension = os.path.splitext(basefile)

        return extension
    

    @err_catcher(name=__name__)
    def getFramesFromSourceData(self, extension, sourceItem, basefile):
        #   Use framerange from sourceData if it exists (sequences)
        if type(sourceItem[1]) == int:
            frame_start = sourceItem[1]
            frame_end = sourceItem[2]

        #   Use video duration for video formats
        elif extension.lower() in self.fuseFuncts.core.media.videoFormats:
            duration = self.getVideoDuration(basefile)
            frame_start = 1
            frame_end = duration

        #   For Stills Images
        else:
            frame_start = 1
            frame_end = 1

        return frame_start, frame_end


    @err_catcher(name=__name__)
    def loadData(self, data):
        if "statename" in data:
            self.e_name.setText(data["statename"])
        if "statemode" in data:
            self.setStateMode(data["statemode"])
        if "stateUID" in data:
            self.stateUID = data["stateUID"]
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
        if "importData" in data:
            self.importData = data["importData"]
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
            self.files = data["files"]

        if "filepath" in data:
            data["filepath"] = getattr(
                self.core.appPlugin, "sm_import_fixImportPath", lambda x: x
            )(data["filepath"])
            self.setImportPath(data["filepath"])

        self.core.callback("onStateSettingsLoaded", self, data)


    #########################
    #                       #
    #       UTILITIES       #
    #                       #
    #########################


    #   Colors State Tools in the Comp
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



    #########################
    #                       #
    #       IMPORTING       #
    #                       #
    #########################


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
    def importAll(self, refreshUi=False, setChecked=False):

        self.imageImport(self.importData)

        # refreshUi = True                        #   TESTING

        if refreshUi:
            self.updateUi()
            self.updateAovChnlTree()
            self.createAovThumbs()

        if setChecked:
            #   Get all child items form AOV list
            aovItems = self.getAovItems(self.lw_objects)

            self.core.popup(f"aovItems:  {aovItems}")                                      #    TESTING

            for item in aovItems:
                self.setCheckbox(item, checked=True)




    @err_catcher(name=__name__)
    def importAllFromIdent(self, refreshUi=False, setChecked=False):

        self.imageImport(self.importData)

        # refreshUi = True                        #   TESTING

        if refreshUi:
            self.updateUi()
            self.updateAovChnlTree()
            self.createAovThumbs()

        if setChecked:
            #   Get all child items form AOV list
            aovItems = self.getAovItems(self.lw_objects)

            self.core.popup(f"aovItems:  {aovItems}")                                      #    TESTING

            for item in aovItems:
                self.setCheckbox(item, checked=True)




    @err_catcher(name=__name__)
    def importSelected(self, refreshUi=True):
        importData = self.importData.copy()

        selected_info = []

        def collectCheckedItems(item):
            if item.childCount() == 0 and item.checkState(0) == Qt.Checked:
                file_data = item.data(0, ITEM_ROLE_DATA)
                if file_data:
                    selected_info.append(file_data)

            for i in range(item.childCount()):
                collectCheckedItems(item.child(i))

        # Start from the root item
        root = self.lw_objects.invisibleRootItem()
        for i in range(root.childCount()):
            collectCheckedItems(root.child(i))

        if selected_info:
            importData["files"] = selected_info
        else:
            self.core.popup("No items selected.")
            return False

        self.imageImport(importData)

        if refreshUi:
            self.updateUi()
            self.updateAovChnlTree()
            self.createAovThumbs()


    @err_catcher(name=__name__)
    def checkLatestVersion(self):
        path = self.getImportPath()
        curVerData = {"version": self.importData["version"], "path": path}

        latestVerDict = self.getLatestVersion(self.importData, includeMaster=True)

        lastestVerName = latestVerDict["version"]
        lastestVerPath = latestVerDict["path"]

        if latestVerDict:
            latestVersionData = {"version": lastestVerName, "path": lastestVerPath}
        else:
            latestVersionData = {}

        return curVerData, latestVersionData
    

    @err_catcher(name=__name__)
    def importLatest(self, refreshUi=True, selectedStates=True, setChecked=False):
        highestVer = self.getLatestVersion(self.selMediaContext, includeMaster=True)

        result = self.makeImportData(highestVer)

        if not result:
            return False
        
        if result == "Empty":
            return result
        
        if not selectedStates:
            self.importAll(setChecked=setChecked)

            # self.importAll(refreshUi=True)

        if refreshUi:
            self.updateUi()
            self.updateAovChnlTree()
            self.createAovThumbs()

        return True



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
            "stateUID": self.stateUID,
            "filepath": self.getImportPath(),
            "autoUpdate": str(self.chb_autoUpdate.isChecked()),
            "taskname": self.taskName,
            "setname": self.setName,
            "taskColor": self.cb_taskColor.currentText(),
            "importData": self.importData,
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



    #########################
    #                       #
    #        CLASSES        #
    #                       #
    #########################


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
        self.w_browser.tw_identifier.itemDoubleClicked.connect(self.ident_dblClk)
        self.w_browser.lw_version.itemDoubleClicked.disconnect()
        self.w_browser.lw_version.itemDoubleClicked.connect(self.ver_dblClk)

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
    def ident_dblClk(self, item, column):
        selResult = ["identifier", item.data(0, Qt.UserRole)]

        self.mediaSelected.emit(selResult)
        self.accept() 


    @err_catcher(name=__name__)
    def ver_dblClk(self, item):
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
            
            selResult = ["version", data]

            self.mediaSelected.emit(selResult)
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
        color = index.data(ITEM_ROLE_COLOR)

        if color:
            # Ensure the color is a QColor object
            if isinstance(color, QColor):
                brush_color = color
            else:
                brush_color = QColor(color)  # Convert to QColor if not already

            rect = QRect(option.rect)
            # Position on the right
            rect.setLeft(option.rect.right() - 14)  
            # Set width of the color box
            rect.setWidth(10)

            painter.fillRect(rect, QBrush(brush_color))



#   Generates thumbnails in separate threads
class ThumbnailThread(QThread):
    thumbnail_ready = Signal(QWidget, QPixmap, int, int)

    def __init__(self, item, filepath, width, height, channel, allowThumb, funct_getPixMap):
        super().__init__()
        self.item = item
        self.filepath = filepath
        self.width = width
        self.height = height
        self.channel = channel
        self.allowThumb = allowThumb
        self.getPixMap = funct_getPixMap

    def run(self):
        # Get PixMap
        pixMap = self.getPixMap(self.filepath, self.width, self.height, self.channel, self.allowThumb)

        # Maintain aspect ratio: Calculate new height
        aspectRatio = pixMap.height() / pixMap.width()
        new_height = int(self.width * aspectRatio)

        # Scale the pixmap to fill the QLabel's width while maintaining aspect ratio
        scaledPixmap = pixMap.scaled(self.width, new_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        # Emit signal to update the UI with the pixmap
        self.thumbnail_ready.emit(self.item, scaledPixmap, new_height, self.width)
