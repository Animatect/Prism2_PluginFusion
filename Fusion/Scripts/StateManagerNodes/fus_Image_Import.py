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
from sys import version

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

from typing import TYPE_CHECKING, Union, Dict, Any, Tuple
if TYPE_CHECKING:
    pass
else:
    Tool_ = Any
    Composition_ = Any
    FlowView_ = Any

#   For Python Type Hints
FusionComp = Dict
Tool = Any
ToolOption = Any
Color = int
UUID = str
Toolname = str
PixMap = Any

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

        #   Checks if the attr already exists and assigns if not
        self.core = getattr(self, "core", core)
        self.state = getattr(self, "state", state)
        self.stateManager = getattr(self, "stateManager", stateManager)
        self.fuseFuncts = getattr(self, "fuseFuncts", self.core.appPlugin)

        if not hasattr(self, "mediaChooser"):
            self.mediaChooser = ReadMediaDialog(self, self.core)
            
        self.stateMode = "Image_Import"
        self.taskName = ""
        self.setName = ""

        #   Gets color mode from DCC settings
        self.taskColorMode = self.fuseFuncts.taskColorMode
        if self.taskColorMode == "Disabled":
            self.cb_taskColor.setVisible(False)
        else:
            self.cb_taskColor.setVisible(True)
            self.populateTaskColorCombo()
        #   Get thumbnail size from DCC settings
        self.aovThumbWidth = self.fuseFuncts.aovThumbWidth
        #   Get sorting mode from DCC settings
        self.sortMode = self.fuseFuncts.sortMode
        #   Get use version update popup from DCC settings
        self.useUpdatePopup = self.fuseFuncts.useUpdatePopup

        #   State name stuff
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

        #   Sets colors
        self.oldPalette = self.b_importLatest.palette()
        self.updatePalette = QPalette()
        self.updatePalette.setColor(QPalette.Button, QColor(200, 100, 0))
        self.updatePalette.setColor(QPalette.ButtonText, QColor(255, 255, 255))

        font = self.l_curVersion.font()
        font.setBold(True)
        self.l_curVersion.setFont(font)

        font = self.l_latestVersion.font()
        font.setBold(True)
        self.l_latestVersion.setFont(font)

        # createEmptyState = (
        #     QApplication.keyboardModifiers() == Qt.ControlModifier
        #     or not self.core.uiAvailable
        #     )

    ####   Do one of the following:     ####

        ##   1. Load State from Comp Data
        if stateData is not None:
            self.loadData(stateData)
            logger.debug("Loaded State from saved data")                    #   TODO

            self.nameChanged()
            self.updateUi()
            self.updateAovChnlTree()
            self.createStateThumbnail()
            self.createAovThumbs()

        ##   2. If passed from FusFuncts. Receive importData via "settings" kwarg
        elif settings:
            #   Create State UUID
            self.stateUID = self.fuseFuncts.createUUID()
            #   Set intial importData to settings
            self.importData = settings
            #   Import the latest version
            self.importLatest(refreshUi=True, selectedStates=False, setChecked=True)

            logger.debug("Loaded State from data passed from ProjectBrowser Import")        #   TODO


        ##   3. Opens Media Popup to select import
        elif (
            importPath is None
            and stateData is None
            # and not createEmptyState
            and not settings
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
        
            self.nameChanged()
            self.updateUi()
            self.updateAovChnlTree()
            self.createStateThumbnail()
            self.createAovThumbs()


        ##   4. If error
        else:
            logger.warning("ERROR: Unable to Import Image.")
            self.core.popup("Unable to Import Image.")
            return False

        getattr(self.core.appPlugin, "sm_import_startup", lambda x: None)(self)

        self.connectEvents()
        self.setToolTips()

        self.stateManager.saveImports()
        self.stateManager.saveStatesToScene()


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
        self.b_importLatest.clicked.connect(lambda: self.importLatest(refreshUi=True, selectedStates=False, setChecked=True))    #   Import Latest Button
        self.chb_autoUpdate.stateChanged.connect(self.autoUpdateChanged)                        #   Latest Checkbox
        self.b_importAll.clicked.connect(lambda: self.importAll(refreshUi=True))
        self.b_importSel.clicked.connect(self.importSelected)
        self.b_refresh.clicked.connect(self.refresh)                                            #   Refresh Button        TODO


    #########################
    #                       #
    #       Wrapped         #
    #   Prism Functions     #
    #                       #
    #########################

    #   Returns the VersionInfo filepath
    @err_catcher(name=__name__)
    def getVersionInfoPath(self, cachePath:dict) -> str:
        return self.core.getVersioninfoPath(
            self.core.mediaProducts.getMediaVersionInfoPathFromFilepath(cachePath)
            )
    
    #   Returns the version label name from version filepath
    @err_catcher(name=__name__)
    def getMasterVersionLabel(self, filepath:str) -> str:
        return self.core.mediaProducts.getMasterVersionLabel(filepath)
    
    #   Returns highest version context from a given context
    @err_catcher(name=__name__)
    def getLatestVersion(self, context:dict, includeMaster:bool) -> dict:
        mediaProducts = self.fuseFuncts.core.mediaProducts
        return mediaProducts.getLatestVersionFromIdentifier(context, includeMaster=includeMaster)
    
    #   Returns a pixmap from an exr image filepath (can specify channel/aov)
    @err_catcher(name=__name__)
    def getPixmapFromExrPath(self, filePath:str, width:int, height:int, channel:str, allowThumb:bool) -> PixMap:
        pxmap = self.core.media.getPixmapFromExrPath(filePath, width=width, height=height, channel=channel, allowThumb=allowThumb)
        return pxmap

    #   Returns a pixmap from a generic media image filepath
    @err_catcher(name=__name__)
    def getPixmapFromPath(self, filePath:str, width:int, height:int) -> PixMap:
        pxmap = self.core.media.getPixmapFromPath(filePath, width=width, height=height)
        return pxmap
    
    #   Returns a context from the currently selected version
    @err_catcher(name=__name__)
    def getCurrentVersion(self) -> dict:
        self.mediaBrowser = self.mediaChooser.w_browser
        self.mediaPlayer = self.mediaBrowser.w_preview.mediaPlayer
        return self.mediaBrowser.getCurrentVersion()
    
    #   Returns a list of AOV dicts for a given context
    @err_catcher(name=__name__)
    def getAOVsFromVersion(self, version:dict) -> list:
        return self.core.mediaProducts.getAOVsFromVersion(version)
    
    #   Returns a list of all the image files for a given context
    @err_catcher(name=__name__)
    def getFilesFromContext(self, aovItem:dict) -> list:
        return self.fuseFuncts.core.mediaProducts.getFilesFromContext(aovItem)
    
    #   Returns a list of channels/AOVs for a given filepth
    @err_catcher(name=__name__)
    def getLayersFromFile(self, filepath:str) -> list:
        return self.fuseFuncts.core.media.getLayersFromFile(filepath)

    #   Returns the numver of frames for a given video filepath
    @err_catcher(name=__name__)
    def getVideoDuration(self, filepath:str) -> int:
        return self.fuseFuncts.core.media.getVideoDuration(filepath)


    #########################
    #                       #
    #         STATE         #
    #                       #
    #########################


    @err_catcher(name=__name__)                     #   NEEDED ???
    def setStateMode(self, stateMode):
        self.stateMode = stateMode
        self.l_class.setText(stateMode)


    #   Set State Name and Icon
    @err_catcher(name=__name__)
    def nameChanged(self, text=None):
        name = self.e_name.text()

        if text:
            name = text
        else:
            try:
                name = f"{self.importData['identifier']}__{self.importData['version']}"
            except Exception as e:                                          #   TODO
                name = text

        #   Set the name for the State list
        self.state.setText(0, name)
        #   Add icon to State name
        self.state.setIcon(0, QIcon(STATE_ICON))

        self.stateManager.saveImports()
        self.stateManager.saveStatesToScene()


    #   Opens Media Chooser to select version
    @err_catcher(name=__name__)
    def browse(self, refreshUi=True):
        #   Get the AOV items
        aovItems = self.getAllItems(useChecked=False, aovs=True)
        if aovItems:
            #   Get the MediaId of the first AOV item
            itemData = self.getItemData(aovItems[0])
            #   Call the MediaWindow with the MediaId
            self.callMediaWindow(itemData)

        else:
            #   Just call without a MediaId
            self.callMediaWindow()

        if refreshUi:
            self.updateUi()
            self.updateAovChnlTree()
            self.createAovThumbs()
            self.createStateThumbnail()


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
        self.l_text_Current.setToolTip(path)
        self.stateManager.saveImports()
        self.stateManager.saveStatesToScene()


    #   Updates the Auto-update UI
    @err_catcher(name=__name__)
    def autoUpdateChanged(self, checked):
        self.w_importLatest.setVisible(not checked)

        if checked:
            curVersion, latestVersion = self.checkLatestVersion()
            if self.chb_autoUpdate.isChecked():
                if curVersion.get("version") and latestVersion.get("version") and curVersion["version"] != latestVersion["version"]:
                    self.importLatest(refreshUi=False, selectedStates=False)

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
    def setToolTips(self):
        tip = ("Sets the color of the\n"
               "Tools in the Fusion Comp")
        self.cb_taskColor.setToolTip(tip)

        tip = ("Centers the view of the State tools\n"
               "in the Node Graph.")
        self.b_focusView.setToolTip(tip)

        tip = "Selects all the State tools in the Comp"
        self.b_selectTools.setToolTip(tip)

        tip = "Opens the Media Browser to select a specfic version"
        self.b_browse.setToolTip(tip)

        tip = ("Will import the latest version of the media.\n"
               "This includes all AOVs, layers, and channels")
        self.b_importLatest.setToolTip(tip)

        tip = ("Enables Auto-update function.\n\n"
               "This will automatically import/update to\n"
               "the most recent version of the media.")
        self.w_autoUpdate.setToolTip(tip)

        tip = ("Will import the currently viewed version of the media.\n"
               "This includes all AOVs, layers, and channels")
        self.b_importAll.setToolTip(tip)

        tip = ("Will import the currently selected AOVs, layers, and channels\n"
               "of the currently viewed version")
        self.b_importSel.setToolTip(tip)

        tip = ("Refreshes the UI\n"
               "Filepaths, version, thumbnails, statuses")
        self.b_refresh.setToolTip(tip)

        tip = ("AOV listing.\n\n"
               "This displays all the Media Identifier's AOVs,\n"
               "as well as layers, channels, and parts of\n"
               "EXRs.\n\n"
               "Checking an item allows for custom import with\n"
               "the Import Selected button.")
        self.lw_objects.setToolTip(tip)


    #   Opens the Custom MediaBrowser window to choose import
    @err_catcher(name=__name__)
    def callMediaWindow(self, itemData=None):
        #   Sets objects
        self.mediaBrowser = self.mediaChooser.w_browser
        self.mediaPlayer = self.mediaBrowser.w_preview.mediaPlayer

        #   If passed itemData, navigate to the Media Item
        if itemData:
            try:
                #   Navigate to the coorect tab/table
                self.mediaBrowser.navigateToEntity(itemData)
                #   Get the item title
                mediaId = (itemData.get("displayName")
                        or itemData.get("mediaId")
                        or itemData.get("identifier")
                        )

                #   Find and select the Identifier
                items = self.mediaBrowser.tw_identifier.findItems(mediaId, Qt.MatchFlag(Qt.MatchExactly & Qt.MatchCaseSensitive ^ Qt.MatchRecursive))
                if items:
                    self.mediaBrowser.tw_identifier.setCurrentItem(items[0])
            except:
                logger.debug("ERROR:  Unable to navigate to State's entity in the MediaBrowser")

        #   Connects clicked signal
        self.mediaChooser.mediaSelected.connect(lambda selResult: self.setSelectedMedia(selResult))
        #   Calls the MediaBrowser and receives result
        result = self.mediaChooser.exec_()

        #   If cancelled
        if result == QDialog.Rejected:
            return "Cancelled"
        
        #   If error
        if not self.selResult:
            return False

        #   Gets the result
        clicked = self.selResult[0]
        self.importData = self.selResult[1]

        #   Makes funct call based on what was clicked (Identifier or Version)
        if clicked == "version":
            currVersion = self.getCurrentVersion()
            result = self.makeImportData(currVersion)

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

        if not versions:
            logger.debug("Skipped setting Latest Version Status")
            return

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
                self.importLatest(refreshUi=False, selectedStates=False, setChecked=True)

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

        self.stateManager.saveImports()
        self.stateManager.saveStatesToScene()


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
        root_item.setText(0, f"{self.importData['identifier']}_{self.importData['version']}")
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
                            self.setItemData(channel_item, correct_fileData)

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
                    self.setItemData(channel_item, correct_fileData)


                #   Add checkbox actions to item
                self.setupAovActions(channel_item)

        #   If there are no AOVs, add framerange under the MediaID
        if not hasAOVs:
            root_item.setText(0, f"{self.importData['identifier']}_{self.importData['version']}    ({data['frameRange']})")

        self.updateAovStatus()


    #   Adds checkbox and checkbox selection behaviour
    @err_catcher(name=__name__)
    def setupAovActions(self, item):
        # Make item checkable
        item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)

        matchingData = self.getMatchingDataFromItem(item)
        if matchingData:
            checked = matchingData.get("stateChecked", None)
            if checked:
                self.setItemChecked(item, checked)
            else:
                self.setItemChecked(item, "unchecked")
        else:
            self.setItemChecked(item, "unchecked")

        self._updateParentCheckbox(item)


    #   Adds checkbox selection behaviours
    @err_catcher(name=__name__)
    def onAovItemClicked(self, item, column):
        if item.flags() & Qt.ItemIsUserCheckable:
            #   Get current checked state
            current_checked = self.getItemChecked(item)
            #   Reverse the checked state
            new_checked = "unchecked" if current_checked == "checked" else "checked"
            #   Set the checkbox with new state
            self.setItemChecked(item, new_checked)
            #   Sets tree checkboxes based on selection
            self.onCheckboxStateChanged(item, column)

        #   Call the AOV coloring after toggling
        self.updateAovStatus()

        self.stateManager.saveImports()
        self.stateManager.saveStatesToScene()
 

    #   Handles checkbox selection of the children and parents
    @err_catcher(name=__name__)
    def onCheckboxStateChanged(self, item, column):
        checked = self.getItemChecked(item)
        item.setData(0, ITEM_ROLE_CHECKBOX, checked)

        # Temporarily block signals to avoid recursion
        self.lw_objects.blockSignals(True)

        # Recursively apply the state to all child items
        self._toggleCheckbox(item, checked)

        # Update the parent check state
        self._updateParentCheckbox(item)

        # Re-enable signals
        self.lw_objects.blockSignals(False)


    @err_catcher(name=__name__)
    def _toggleCheckbox(self, item, checked):
        for row in range(item.childCount()):
            child_item = item.child(row)
            self.setItemChecked(child_item, checked)

            # Recurse into the child's children
            self._toggleCheckbox(child_item, checked)


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
        any_partially = any(parent.child(i).checkState(0) == Qt.PartiallyChecked for i in range(parent.childCount()))

        #   Set parent's checkbox based on its children
        if all_checked:
            checked = Qt.Checked
        elif any_partially:
            checked = Qt.PartiallyChecked
        elif any_checked and any_unchecked:
            checked = Qt.PartiallyChecked
        else:
            checked = Qt.Unchecked

        self.setItemChecked(parent, checked)

        # Stop at the root parent
        if parent.parent():
            self._updateParentCheckbox(parent)


    @err_catcher(name=__name__)
    def getAllItems(self, useChecked=False, aovs=False):
        items = []

        def _recursiveCollect(item):
            isLeaf = item.childCount() == 0
            if (not aovs or isLeaf) and (not useChecked or self.getItemChecked(item)=="checked"):
                items.append(item)
            for i in range(item.childCount()):
                _recursiveCollect(item.child(i))

        # Iterate through top-level items
        for i in range(self.lw_objects.topLevelItemCount()):
            _recursiveCollect(self.lw_objects.topLevelItem(i))

        return items


    @err_catcher(name=__name__)
    def updateAovStatus(self):
        stateUIDs = self.fuseFuncts.getUIDsFromStateUIDs("import2d", self.stateUID, includeConn=False)

        # Get child AOV items
        aovItems = self.getAllItems(aovs=True)

        for item in aovItems:
            #   Removes and then skips unchecked items
            if self.getItemChecked(item) != "checked":
                self.setItemStatusColor(item, None)
                continue

            id_match = False
            ver_match = False

            itemData = self.getItemData(item)
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

            self.setItemStatusColor(item, color)


    @err_catcher(name=__name__)
    def refreshTips(self):
        self.setStateThumbToolTip()

    
    @err_catcher(name=__name__)
    def setStateThumbToolTip(self):
        tip = f"State UUID: {self.stateUID}"
        self.l_thumb.setToolTip(tip)


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
            aovItems = self.getAllItems(aovs=True)

            #   Default to use Prism thumbnails
            beautyFilepath = None
            channel = None
            allowThumb = True

            #   Try and find beauty/color AOV
            for item in aovItems:
                itemData = self.getItemData(item)
                
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
                    itemData = self.getItemData(item)
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

        #   Store list of active threads
        self.thumb_threads = []

        #   Get all child items from AOV list
        imageItems = self.getAllItems(aovs=True)

        for item in imageItems:
            #   Get data from item
            itemData = self.getItemData(item)
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
    def loadData(self, data):
        self.importData = data

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
            checked = eval(data["autoUpdate"])
            self.chb_autoUpdate.setChecked(checked)
            self.autoUpdateChanged(checked)
        if "taskColor" in data:
            idx = self.cb_taskColor.findText(data["taskColor"])
            if idx != -1:
                self.cb_taskColor.setCurrentIndex(idx)
        if "filepath" in data:
            data["filepath"] = getattr(
                self.core.appPlugin, "sm_import_fixImportPath", lambda x: x
            )(data["filepath"])
            self.setImportPath(data["filepath"])

        self.core.callback("onStateSettingsLoaded", self, data)


    @err_catcher(name=__name__)
    def makeImportData(self, context):
        if not context:
            logger.warning(f"ERROR: There are no Versions for this Media Identifier")
            self.core.popup("There are no Versions for this Media Identifier")
            return "Empty"

        #   Get data from various sources
        aovDict = self.getAOVsFromVersion(context)
        
        #	Get sourceData based on passes - used to get framerange
        versionDir = context["path"]
        if len(aovDict) > 0:
            usePasses = True    #   Has AOVs
        else:
            usePasses = False   #   No AOVs
        sourceData = self.getImportSource(versionDir, usePasses)

        mediaType = context["mediaType"]

        try:
            #   Make base dict
            importData = context

            importData["stateUID"] = self.stateUID
            importData["aovs"] = []
            importData["channels"] = []

            if "itemType" not in context:
                if "asset" in context:
                    importData["itemType"] = "asset"
                elif "sequence" in context or "shot" in context:
                    importData["itemType"] = "shot"
            
        except Exception as e:
            logger.warning(f"ERROR: Unable to make base importData dict: {e}")
            return {}

        files = []

        #   If there are Prism AOV's (for example not for 2d Renders)
        hasAOVs = bool(aovDict)

        # If AOVs exist, use aovDict and sourceData, otherwise use importData
        dataPairs = zip(aovDict, sourceData) if hasAOVs else [(importData, sourceData[0])]

        for aovItem, sourceItem in dataPairs:
            if hasAOVs:
                aovItem["mediaType"] = mediaType
                filesList = self.getFilesFromContext(aovItem)
                aov = aovItem["aov"]
            else:
                filesList = self.getFilesFromContext(importData)
                aov = None

            basefile = filesList[0]

            # Get file extension
            extension = self.getImageExtension(importData, basefile)

            # Get channels list
            channels = self.getLayersFromFile(basefile)

            if len(channels) == 0:
                channels = ["Color"]

            for channel in channels:
                # Create file dictionary
                fileDict = importData.copy()
                #   Add additional items
                fileDict["basefile"] = basefile
                fileDict["channel"] = channel
                fileDict["frame_start"] = sourceItem[1]
                fileDict["frame_end"] = sourceItem[2]

                # Add additional AOV-specific fields if applicable
                if hasAOVs:
                    fileDict.update({"aov": aov})

                #   Create UUID for each basefile
                fileDict["fileUID"] = self.fuseFuncts.createUUID()

                # Append to files list
                files.append(fileDict)

        # Add the files to the importData
        importData["files"] = files
        self.setImportPath(files[0]["basefile"])

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

        #   Set global data object
        self.importData = importData

        return True
    

    #    Modified and combined version of Prism compGetImportSource() & compImportPasses()
    @err_catcher(name=__name__)
    def getImportSource(self, versionDir, usePasses):
        sourceData = []

        if usePasses:
            #   Get AOV directories from version directory
            sources = [
                x
                for x in os.listdir(versionDir)
                if x[-5:] not in ["(mp4)", "(jpg)", "(png)"]
                and os.path.isdir(os.path.join(versionDir, x))
            ]

        else:
            #   Get souce
            sources = self.core.media.getImgSources(versionDir, getFirstFile=True)

        for source in sources:
            #   Make sure sourceDir is a directory
            sourcePath = os.path.join(versionDir, source)
            if not os.path.isdir(sourcePath):
                sourceDir = os.path.dirname(sourcePath)
            else:
                sourceDir = sourcePath

            #   Get sequence Data
            seqName, seqFiles = self.getSequenceData(sourceDir)
            baseFile = seqFiles[0]
            extension = self.getImageExtension(basefile=baseFile)

            #   Handle images sequence
            if len(seqFiles) > 1 and extension not in self.core.media.videoFormats:
                    firstFrame, lastFrame = self.core.media.getFrameRangeFromSequence(seqFiles, baseFile=baseFile)
                    filePath = os.path.join(versionDir, seqName).replace("\\", "/")
            #   Handle video files
            elif extension in self.core.media.videoFormats:
                filePath = os.path.join(sourceDir, baseFile).replace("\\", "/")
                duration = self.getVideoDuration(filePath)
                firstFrame = 1
                lastFrame = duration
            #   Handle single image stills
            else:
                filePath = os.path.join(sourceDir, baseFile).replace("\\", "/")
                firstFrame = 1
                lastFrame = 1

            sourceData.append([filePath, firstFrame, lastFrame])

        return sourceData
    

    @err_catcher(name=__name__)
    def getSequenceData(self, sourceDir):
        #   Handle
        if self.getLinkedFilepath(sourceDir):
            files = self.getLinkedFilepath(sourceDir)

        else:
            files = os.listdir(sourceDir)

        #   Filter and get sequence Dict
        validFiles = self.core.media.filterValidMediaFiles(files)
        validFiles = sorted(validFiles, key=lambda x: x if "cryptomatte" not in os.path.basename(x) else "zzz" + x)

        seqDict = self.core.media.detectSequences(validFiles)
        seqName, seqFiles = next(iter(seqDict.items()))

        return seqName, seqFiles


    @err_catcher(name=__name__)
    def getLinkedFilepath(self, sourceDir):
        redirectFile = os.path.join(sourceDir, "REDIRECT.txt")
        if os.path.exists(redirectFile):
            with open(redirectFile, "r") as rdFile:
                files = [rdFile.read()]

            return files
        
        else:
            return None


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
    def setItemData(self, item, data):
        item.setData(0, ITEM_ROLE_DATA, data)


    @err_catcher(name=__name__)
    def getItemData(self, item):
        return item.data(0, ITEM_ROLE_DATA)
    

    #   Sets item checkbox and saves it to the item data
    @err_catcher(name=__name__)
    def setItemChecked(self, item, checked):
        if isinstance(checked, str):
            checked_str = checked
            checked_qt = self.strToQtChecked(checked)
        elif isinstance(checked, Qt.CheckState):
            checked_str = self.qtCheckedToStr(checked)
            checked_qt = checked
        else:
            checked_str = "unchecked"
            checked_qt = self.strToQtChecked("unchecked")

        #   Set the checkbox using Qt.checked
        item.setCheckState(0, checked_qt)
        #   Save to item's data as str
        item.setData(0, ITEM_ROLE_CHECKBOX, checked_str)

        #   Save checked to importData
        matching_fileData = self.getMatchingDataFromItem(item)
        if matching_fileData:
            matching_fileData["stateChecked"] = checked_str

        self.stateManager.saveImports()
        self.stateManager.saveStatesToScene()



    @err_catcher(name=__name__)
    def getItemChecked(self, item):
        checked_raw = item.data(0, ITEM_ROLE_CHECKBOX)
        if not checked_raw:
            return None
        
        if isinstance(checked_raw, str):
            checked_str = checked_raw
            checked_qt = self.strToQtChecked(checked_raw)
        elif isinstance(checked_raw, Qt.CheckState):
            checked_str = self.qtCheckedToStr(checked_raw)
            checked_qt = checked_raw
        else:
            return None

        return checked_str
    

    @err_catcher(name=__name__)
    def qtCheckedToStr(self, checked_qt):
        if isinstance(checked_qt, Qt.CheckState):
            if checked_qt == Qt.Checked:
                checked_str = "checked"
            elif checked_qt == Qt.Unchecked:
                checked_str = "unchecked"
            elif checked_qt == Qt.PartiallyChecked:
                checked_str = "partial"

            return checked_str
        else:
            logger.warning("ERROR:  'Checked' is not a Qt check object" )
            return "Unchecked"


    @err_catcher(name=__name__)
    def strToQtChecked(self, checked_str):
        if isinstance(checked_str, str):
            if checked_str == "checked":
                checked_qt = Qt.Checked
            elif checked_str == "unchecked":
                checked_qt = Qt.Unchecked
            elif checked_str == "partial":
                checked_qt = Qt.PartiallyChecked

            return checked_qt
        else:
            logger.warning("ERROR:  'Checked' is not a string.")
            return "UnChecked"


    @err_catcher(name=__name__)
    def setItemStatusColor(self, item, color):
        item.setData(0, ITEM_ROLE_COLOR, color)


    @err_catcher(name=__name__)
    def getItemStatusColor(self, item):
        return item.data(0, ITEM_ROLE_COLOR)
    

    @err_catcher(name=__name__)
    def getMatchingDataFromItem(self, item):
        itemData = self.getItemData(item)
        if not itemData:
            return None
        
        itemUID = itemData["fileUID"]

        fData = self.importData["files"]

        for fileData in fData:
            if fileData["fileUID"] == itemUID:
                return fileData
            
        else:
            return None


    @err_catcher(name=__name__)
    def getImageExtension(self, context=None, basefile=None):
        try:
            if context and "extension" in context:
                extension = context["extension"]
            elif basefile:
                _, extension = os.path.splitext(basefile)
            else:
                raise Exception
            
            return extension.lower()
            
        except:
            logger.warning("ERROR:  Unable to get Image Extension")
            return None



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
    def imageImport(self, importData, update=False, path=None, settings=None):
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

        #   Execute import
        importResult = self.fuseFuncts.imageImport(self, importData, self.sortMode)

        if not importResult:
            result = None
            doImport = False
        else:
            result = importResult["result"]
            doImport = importResult["doImport"]

        if doImport:
            if result == "canceled":
                return False

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

        #   Show version update popup if enabled
        if self.useUpdatePopup and result == "updated":
            updateMsgList = importResult["updateMsgList"]
            self.showUpdatePopup(updateMsgList)

        return doImport
    


    @err_catcher(name=__name__)
    def showUpdatePopup(self, updateMsgList, parent=None):
        parent = parent or getattr(self.core, "messageParent", None)

        dialog = UpdateDialog(updateMsgList, parent)
        dialog.exec_()



    @err_catcher(name=__name__)
    def importAll(self, refreshUi=False):
        #   Import all images
        self.imageImport(self.importData)

        if refreshUi:
            self.updateUi()
            self.updateAovChnlTree()
            self.createAovThumbs()
        else:
            self.updateAovChnlTree()

        #   Get all items in the AOV list
        allItems = self.getAllItems()

        #   Check all items
        for item in allItems:
            self.setItemChecked(item, "checked")

        #   Call the AOV coloring after toggling
        self.updateAovStatus()
        # self.createStateThumbnail()

        self.stateManager.saveImports()
        self.stateManager.saveStatesToScene()


    @err_catcher(name=__name__)
    def importSelected(self, refreshUi=True):
        importData = self.importData.copy()

        selItemData = []
        selItems = self.getAllItems(useChecked=True, aovs=True)
        if selItems:
            for item in selItems:
                iData = self.getItemData(item)
                if iData:
                    selItemData.append(iData)

            importData["files"] = selItemData

        else:
            self.core.popup("No items selected.")
            return False

        self.imageImport(importData)

        if refreshUi:
            self.updateUi()
            self.updateAovChnlTree()
            self.createAovThumbs()

        #   Call the AOV coloring after toggling
        self.updateAovStatus()

        self.stateManager.saveImports()
        self.stateManager.saveStatesToScene()


    @err_catcher(name=__name__)
    def checkLatestVersion(self):
        try:
            path = self.getImportPath()
            curVerData = {"version": self.importData["version"], "path": path}

            latestVerDict = self.getLatestVersion(self.importData, includeMaster=True)
            lastestVerName = latestVerDict["version"]
            lastestVerPath = latestVerDict["path"]

            if latestVerDict:
                latestVersionData = {"version": lastestVerName, "path": lastestVerPath}
            else:
                latestVersionData = {}
            
            #   Sets tooltips
            curVerPath = curVerData["path"]
            self.l_text_Current.setToolTip(curVerPath)
            self.l_curVersion.setToolTip(curVerPath)

            latestVerPath = latestVersionData["path"]
            self.l_text_Latest.setToolTip(latestVerPath)
            self.l_latestVersion.setToolTip(latestVerPath)

            return curVerData, latestVersionData
        
        except:
            logger.debug("ERROR:  Unable to get Latest Version.")
            return None
    

    @err_catcher(name=__name__)
    def importLatest(self, refreshUi=True, selectedStates=True, setChecked=False):

        importIdentifier = self.importData.copy()

        keys_to_remove = [
            'stateUID', 'locations', 'extension', 'version', 'aovs', 'channels', 
            'files', 'statename', 'statemode', 'filepath', 'autoUpdate', 'taskname', 'taskColor', 'aov', 'comment', 'date', 
            'source', 'user', 'username'
        ]
        
        # Remove unwanted keys to make Prism context
        for key in keys_to_remove:
            importIdentifier.pop(key, None)

        highestVer = self.getLatestVersion(importIdentifier, includeMaster=True)

        result = self.makeImportData(highestVer)

        if not result:
            return False
        
        if result == "Empty":
            return result
        
        if not selectedStates:
            self.importAll(refreshUi=False)

        if refreshUi:
            self.updateUi()
            self.updateAovChnlTree()
            self.createAovThumbs()
            self.createStateThumbnail()

        return True


    @err_catcher(name=__name__)
    def refresh(self):

        # self.importSelected()                 #   DO WE WANT TO ACTUALLY IMPORT OR JUST KEEP UI REFRESH
        self.updateUi()
        self.updateAovChnlTree()
        self.createAovThumbs()
        self.createStateThumbnail()

        self.refreshTips()



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
                

    @err_catcher(name=__name__)                                 #   TODO Make sure all info is in here (shot, asset, etc)
    def getStateProps(self):

        self.importData["statename"] = self.e_name.text()
        self.importData["statemode"] = self.stateMode
        self.importData["filepath"] = self.getImportPath()
        self.importData["autoUpdate"] = str(self.chb_autoUpdate.isChecked())
        self.importData["taskname"] = self.taskName
        self.importData["taskColor"] = self.cb_taskColor.currentText()


        return self.importData



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
        self.stateManager = self.state.stateManager
        self.fuseFuncts = self.state.fuseFuncts
        self.core = core

        self.isValid = False
        self.setupUi()


    @err_catcher(name=__name__)
    def setupUi(self):
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

        #   Disconnect native right-click-list and connect custom
        self.w_browser.tw_identifier.customContextMenuRequested.disconnect()
        self.w_browser.tw_identifier.customContextMenuRequested.connect(self.customRclList)

        #   Create main window
        self.lo_main = QVBoxLayout()
        self.setLayout(self.lo_main)

        #   Create bottom layout
        self.lo_bottom = QHBoxLayout()

        #   Add instructions label text to bottom
        instructionsText = ("      Double-click Identifier to Import Latest Version      --      "
                            "Double-click Version to Load Version into State     --     "
                            "Right-click Identifier to Import Multiple Items")
        l_instructions = QLabel(instructionsText)

        #   Add button box
        self.bb_main = QDialogButtonBox()
        self.bb_main.addButton("Import Selected", QDialogButtonBox.AcceptRole)
        ##  vvvvv    Disabled until functions added  vvvvvvvv    ##
        # self.bb_main.addButton("Import Custom", QDialogButtonBox.AcceptRole)
        # self.bb_main.addButton("Open Project Browser", QDialogButtonBox.AcceptRole)
        ##  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^   ##
        self.bb_main.addButton("Cancel", QDialogButtonBox.RejectRole)
        self.bb_main.clicked.connect(self.buttonClicked)

        # Add widgets to the bottom layout
        self.lo_bottom.addWidget(l_instructions)
        self.lo_bottom.addStretch()  # Expanding spacer
        self.lo_bottom.addWidget(self.bb_main)

        #   Add main Browser to window
        self.lo_main.addWidget(self.w_browser)
        # Add bottom layout to window
        self.lo_main.addLayout(self.lo_bottom)

        tip = ("Double-click Identifier to Load\n"
               "and Import the Latest Version.\n\n"
               "Right-click on multi-selected items\n"
               "to import the latest version of the multi-\n"
               "selected items.")
        self.w_browser.tw_identifier.setToolTip(tip)

        tip = ("Double-click Version to Load\n"
               "the Version into the State.")
        self.w_browser.lw_version.setToolTip(tip)

        tip = ("Single-selection:  load the selected version into the State.\n"
               "Multi-selection:  import the latest version of each Identifier")
        self.bb_main.setToolTip(tip)


    #   Handles clicked buttons
    @err_catcher(name=__name__)
    def buttonClicked(self, button):
        if button == "select" or button.text() == "Import Selected":
            self.handelImportButton()
        elif button.text() == "Import Custom":
            self.core.popup("Not Yet Implemented")                                      #    TESTING
        elif button.text() == "Open Project Browser":                                   #   TODO
            self.reject()
            self.openProjectBrowser()
        elif button.text() == "Cancel":
            self.reject()  # Close the dialog with no selection
        else:
            self.reject()  # Close the dialog with no selection


    #   Handles if the Import Selected buton clicked
    def handelImportButton(self):
        selectedItems = self.w_browser.tw_identifier.selectedItems()

        # if len(selectedItems) == 0:
        #     self.reject()

        if len(selectedItems) == 1:
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

        elif len(selectedItems) > 1:
            self.handleRclImport(selectedItems)


    #   Add custom RCL list to Identifier list
    @err_catcher(name=__name__)
    def customRclList(self, pos):
        selectedItems = self.w_browser.tw_identifier.selectedItems()

        rcmenu = QMenu(self)

        importAct = QAction("Import into Comp", self)
        importAct.triggered.connect(lambda: self.handleRclImport(selectedItems))
        rcmenu.addAction(importAct)

        rcmenu.exec_(self.w_browser.tw_identifier.mapToGlobal(pos))


    #   Handle import from custom RCL
    @err_catcher(name=__name__)
    def handleRclImport(self, selectedItems):
        #   Close Dialogue
        self.reject()

        #   If single item, import directly in this state
        if len(selectedItems) == 1:
            self.ident_dblClk(selectedItems[0])
        #   If multiple items, call the import through the main plugin
        elif len(selectedItems) > 1:
            for item in selectedItems:
                iData = item.data(0, Qt.UserRole)
                self.fuseFuncts.addImportState(self.stateManager, "Image_Import", useUi=False, settings=iData)
        else:
            logger.debug("No Media Items Selected")


    #   Sends data back to the main code to import the latest version
    @err_catcher(name=__name__)
    def ident_dblClk(self, item, column=None):
        selResult = ["identifier", item.data(0, Qt.UserRole)]

        self.mediaSelected.emit(selResult)
        self.accept() 


    #   Sends data back to main code to populate the version
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


#	Popup for update message
class UpdateDialog(QDialog):
    def __init__(self, updateMsgList, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Update Information")

        layout = QVBoxLayout()

        #	Add the "Updates" header at the top
        header_label = QLabel("Updates:")
        header_font = QFont()
        header_font.setBold(True)
        header_label.setFont(header_font)
        layout.addWidget(header_label)

        #	Create the table
        self.table = QTableWidget()
        self.table.setRowCount(len(updateMsgList))
        self.table.setColumnCount(2)

        #	Hide table lines and numbers
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setVisible(False)
        self.table.setShowGrid(False)

        #	Reduce the space between cells
        self.table.setContentsMargins(0, 0, 0, 0)
        self.table.setStyleSheet("QTableWidget::item { padding: 0px; }")

        #	Get the width of the longest text in the first column
        font_metrics = QFontMetrics(self.font())
        maxWidth_firstCol = 0
        maxWidth_secondCol = 0

        for rowData in updateMsgList:
            #	First column
            textFirst = str(rowData[0])
            textWidth_first = font_metrics.horizontalAdvance(textFirst)
            if textWidth_first > maxWidth_firstCol:
                maxWidth_firstCol = textWidth_first

            #	Second column
            textSecond = str(rowData[1])
            textWidth_second = font_metrics.horizontalAdvance(textSecond)
            if textWidth_second > maxWidth_secondCol:
                maxWidth_secondCol = textWidth_second

        #	Add margin for both columns
        firstColumn_width = maxWidth_firstCol + 20
        secondColumn_width = maxWidth_secondCol + 20

        #	Populate the table with data
        for rowIndex, rowData in enumerate(updateMsgList):
            for colIndex, cellData in enumerate(rowData):
                item = QTableWidgetItem(str(cellData))
                item.setFlags(Qt.NoItemFlags)
                self.table.setItem(rowIndex, colIndex, item)

        #	Set column widths
        self.table.setColumnWidth(0, firstColumn_width)
        self.table.setColumnWidth(1, secondColumn_width)

        #	Last column stretches
        self.table.horizontalHeader().setStretchLastSection(False)

        #	Add the table
        layout.addWidget(self.table)

        # Add a close button
        b_close = QPushButton("Close")
        b_close.clicked.connect(self.close)
        layout.addWidget(b_close)

        # Set the dialog layout
        self.setLayout(layout)

        # Adjust the window width to match the table content
        totalTable_width = firstColumn_width + secondColumn_width + 50
        self.resize(totalTable_width, self.table.verticalHeader().length() + 100)
