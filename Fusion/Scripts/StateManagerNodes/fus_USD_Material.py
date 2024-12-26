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
# import re
import logging

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

from PrismUtils.Decorators import err_catcher


logger = logging.getLogger(__name__)



class USD_MaterialClass(object):
    className = "USD_Material"
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
        self.stateMode = "USD_Material (empty)"

        self.core = core
        self.stateManager = stateManager
        self.fuseFuncts = self.core.appPlugin

        self.supportedFormats = [".mtlx", ".png", ".jpg", ".jpeg", ".exr", ".tga", ".tif", ".tiff"]               #   TODO - add file types

        self.texTypes = {"color": ["diffuse", "diff", "color", "base color", "basecolor", "albedo", "col", "base"],                                     #   TODO - add more types
                         "metallic": ["metallic", "metal", "metalness", "met", "mtl"],
                         "roughness": ["roughness", "rough", "rgh", "glossiness", "glossy", "gloss"],
                         "normal": ["normal", "norm", "nor", "nrm", "nml"],
                         "ao": ["ao", "ambient occlusion", "ambientocclusion", "occlusion", "cavity"],
                         "ARM": ["arm", "orm"],
                         "emit": ["emmision", "emit"],
                         "displace": ["displacement", "disp", "height", "bump", "bmp"],
                         "alpha": ["alpha", "opacity"],
                         "subsurface": ["sss", "subsurface", "ssscolor"],
                         "clearcoat": ["clearcoat", "coat"],
                         "coatRough": ["clearcoatRoughness, clearRough", "coarRoughness", "coatRough"]}

        self.textureFiles = []

        self.taskName = ""
        self.setName = ""

        self.l_name.setVisible(False)
        self.e_name.setVisible(False)

        # Set the header labels for the table
        self.tw_textureFiles.setHorizontalHeaderLabels(["Map", "File", "Path"])

        # Hide the "Path" column
        self.tw_textureFiles.setColumnHidden(2, True)

        # Make the "File" column stretch to the right edge
        header = self.tw_textureFiles.horizontalHeader()
        header.setStretchLastSection(True)

        # Hide the row numbers
        self.tw_textureFiles.verticalHeader().setVisible(False)

        # Set context menu policy for right-click actions
        self.tw_textureFiles.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tw_textureFiles.customContextMenuRequested.connect(self.showContextMenu)

        #   Initially hidee the Panels
        self.gb_matX.hide()
        self.gb_textures.hide()

        self.cb_taskColor.setFixedWidth(125)
        #	Gets task color settings from the DCC settings
        self.taskColorMode = self.core.getConfig("Fusion", "taskColorMode")
        if self.taskColorMode == "Disabled":
            self.cb_taskColor.hide()
        else:
            self.cb_taskColor.show()
            self.populateTaskColorCombo()

        if importPath:
            _, extension = os.path.splitext(importPath)

            if extension.lower() not in self.supportedFormats:
                self.core.popup(f"{extension.upper()} is not supported with this Import State")
                return False

            # self.setImportPath(importPath)
            # result = self.importObject(settings=settings)

        #     if not result:
        #         return False
        # # elif (
        #     stateData is None
        #     and not createEmptyState
        #     and not self.stateManager.standalone
        # ):
        #     return False

        getattr(self.core.appPlugin, "sm_import_startup", lambda x: None)(self)

        self.connectEvents()

        if stateData is not None:
            self.loadData(stateData)
        
        else:
            self.stateUID = self.fuseFuncts.createUUID()
            self.lastExplorerDir = self.findProjectTexDir()

            self.e_name.setText(self.stateMode)
            self.l_class.setText(self.stateMode)


        # tip = ("Create a simple Fusion USD scene.\n\n"                    #######   TODO TOOLTIPS
        #        "This will add and connect:\n"
        #        "A uMerge and a uRenderer")
        # self.b_createUsdScene.setToolTip(tip)

        self.nameChanged()
        self.updateUi()


    @err_catcher(name=__name__)
    def setStateMode(self, stateMode):
        self.stateMode = stateMode
        self.l_class.setText(stateMode)


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
        if "textureFiles" in data:
            self.textureFiles = data["textureFiles"]
        if "taskname" in data:
            self.taskName = data["taskname"]
        if "setname" in data:
            self.setName = data["setname"]
        if "lastExplorerDir" in data:
            self.lastExplorerDir = data["lastExplorerDir"]

        self.refreshTexList()

        self.core.callback("onStateSettingsLoaded", self, data)


    @err_catcher(name=__name__)
    def connectEvents(self):
        self.e_name.textChanged.connect(self.nameChanged)
        self.e_name.editingFinished.connect(self.stateManager.saveStatesToScene)
        #   This is the "Browse" button
        self.b_browse.clicked.connect(self.browse)
        self.b_browse.customContextMenuRequested.connect(self.openFolder)
        #   This is the "Re-Import" button
        # self.b_import.clicked.connect(lambda: self.importObject(update=True))                 #   TODO
        self.b_explorer.clicked.connect(self.openExplorer)
        self.b_createShader.clicked.connect(self.createUsdMaterial)
        self.tw_textureFiles.customContextMenuRequested.connect(self.showContextMenu)
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
        self.fuseFuncts.colorTaskNodes(self.stateUID, "import3d", colorRGB, category="import3d")

        self.stateManager.saveImports()
        self.stateManager.saveStatesToScene()


    @err_catcher(name=__name__)
    def updateUi(self):

        getattr(self.core.appPlugin, "sm_import_updateUi", lambda x: None)(self)
        

    @err_catcher(name=__name__)
    def nameChanged(self, text=None):
        if not text:
            name = self.e_name.text()
        else:
            name = f"USD_Mat ({text})"

        self.state.setText(0, name)

        self.stateManager.saveStatesToScene()
    

    #   Gets the Project Texture dir from pipeline config
    @err_catcher(name=__name__)
    def findProjectTexDir(self):
        #   Get current project
        if "prism_project" in os.environ and os.path.exists(os.environ["prism_project"]):
            curPrj = os.environ["prism_project"]
        else:
            curPrj = self.core.getConfig("globals", "current project")
        #   Get project Texture directory
        texDir = self.core.projects.getResolvedProjectStructurePath("textures")

        #   Return Dir
        if texDir:
            return texDir
        elif curPrj:
            return curPrj
        else:
            return None


    #   From Browser Button
    @err_catcher(name=__name__)
    def browse(self):
        #   Get import paths from Libraries window
        paths = self.launchLibBrowser()

        if not paths:
            return
        
        path = paths[0]
        ext = os.path.splitext(os.path.basename(path))[1]

        if ext not in self.supportedFormats:
            logger.warning(f"ERROR:  '{ext}' format is not supported.")
            self.core.popup(f"ERROR:  '{ext}' format is not supported.")
            return

        #   Handle MaterialX Import
        if len(paths) == 1 and ext.lower() == ".mtlx":
            self.importMatX(path)

        #   Handle Texture set
        else:
            self.importTextureSet(paths)


    #   Launch Libraries window and return selected Import Path(s)
    @err_catcher(name=__name__)
    def launchLibBrowser(self):
        try:
            #   Get Libraries Plugin
            libs = self.core.getPlugin("Libraries")
            if not libs:
                raise Exception
        except:
            logger.warning("ERROR:  Libraries Plugin not installed.  Use the 'Open Explorer' button to choose Texture Set.")
            self.core.popup("Libraries Plugin not installed.\n\n"
                           "Use the 'Open Explorer' button to choose Texture Set.")
            return None

        try:
            #   Call Libraries popup and return selected file path(s)
            paths = libs.getAssetImportPaths()

            if not paths:
                logger.debug("Texture selection canceled.")
                return None
            
            return paths
            
        except Exception as e:
            self.core.popup(f"ERROR: Failed  Texture Set: {e}")
            logger.warning(f"ERROR: selecting Texture Set: {e}")
            return None
        

    #   Opens File Explorer to pick texture files
    @err_catcher(name=__name__)
    def openExplorer(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        dialog = QFileDialog()

        #   Allow selecting files
        dialog.setFileMode(QFileDialog.ExistingFiles)
        dialog.setOption(QFileDialog.ShowDirsOnly, False)

        #   Set title
        dialog.setWindowTitle("Select Texture Files")

        #   Set the initial directory if lastExplorerDir is set
        if self.lastExplorerDir:
            dialog.setDirectory(self.lastExplorerDir)

        #   Open the dialog
        if dialog.exec_():
            #   Retrieve the selected items
            selectedItems = dialog.selectedFiles()
            textureFiles = selectedItems

            #   Update lastExplorerDir to the directory of the first selected item
            if selectedItems:
                firstItem = selectedItems[0]
                if os.path.isfile(firstItem):
                    self.lastExplorerDir = os.path.dirname(firstItem)
                elif os.path.isdir(firstItem):
                    self.lastExplorerDir = firstItem

                path = selectedItems[0]
                ext = os.path.splitext(os.path.basename(path))[1]

                if ext not in self.supportedFormats:
                    logger.warning(f"ERROR:  '{ext}' format is not supported.")
                    self.core.popup(f"ERROR:  '{ext}' format is not supported.")
                    return

                #   Handle MaterialX Import
                if len(selectedItems) == 1 and ext.lower() == ".mtlx":
                    self.importMatX(path)

                #   Handle Texture set
                else:
                    self.importTextureSet(selectedItems)


    @err_catcher(name=__name__)
    def importMatX(self, importPath, update=False):
        result = True

        if self.stateManager.standalone:
            return result

        #   Get current comp filename
        fileName = self.core.getCurrentFileName()

        doImport = True

        basename = os.path.basename(importPath)

        #   Configure UI
        self.setStateMode("MaterialX")
        self.gb_matX.show()
        self.e_matxFile.setText(basename)
        
        #   Make name without ext
        matXname = os.path.splitext(basename)[0]
        self.nameChanged(matXname)

        #   Make dict
        matxData = {"toolName": matXname,
                    "nodeUID": self.stateUID,
                    "shaderName": matXname,
                    "shaderType": "MaterialX",
                    "matXfilePath": importPath}
        
        #   Updates existing tool if it exists
        update = self.fuseFuncts.nodeExists(self.stateUID)

        #   Call fucntion to import
        importResult = self.fuseFuncts.createUsdMatX(self,
                                                     UUID=self.stateUID,
                                                     texData=matxData,
                                                     update=update)

        if not importResult:
            result = None
            doImport = False
        else:
            result = importResult["result"]
            doImport = importResult["doImport"]

        if doImport:
            if result == "canceled":
                return

        kwargs = {
            "state": self,
            "scenefile": fileName,
        }
        self.core.callback("postImport", **kwargs)
        self.stateManager.saveImports()
        self.updateUi()
        self.stateManager.saveStatesToScene()

        return result


    @err_catcher(name=__name__)
    def importTextureSet(self, textureFiles):
        #   Configure UI
        self.setStateMode("USD Material")
        self.gb_textures.show()

        if len(textureFiles) == 1:
            full_fileList = []

            #   Resolve Texture Set from selected file
            try:
                path = textureFiles[0]
                texDir = os.path.dirname(path)
                #   Loop through files to get full filepaths
                for file in os.listdir(texDir):
                    fullPath = os.path.join(texDir, file)
                    full_fileList.append(fullPath)

                #   Get matching texture set from file list
                texSet = self.getTextureSet(full_fileList, path)

                if not texSet:
                    raise Exception

            except Exception as e:
                logger.warning(f"ERROR: Failed to extract Texture Set from selected File: {e}")
                self.core.popup(f"Failed to extract Texture Set from selected File: {e}")
                return
        else:
            #   Pass selected files
            texSet = textureFiles
            baseNames = [os.path.splitext(os.path.basename(f))[0] for f in texSet]
            self.commonPrefix = self.findCommonPrefix(baseNames)

        #   Populate the list widget
        self.populateTextList(texSet)

        self.nameChanged(self.commonPrefix)


    @err_catcher(name=__name__)
    def getTextureSet(self, fileList, knownFilename):
        try:
            # Extract the dir and basename of the known file
            known_dir = os.path.dirname(knownFilename)
            known_base = os.path.splitext(os.path.basename(knownFilename))[0]

            # Find all files in the same directory as the known file
            relevant_files = [f for f in fileList if os.path.dirname(f) == known_dir]

            # Extract the "core name" of the known file (before any suffix or pass indicators)
            coreName = known_base.split('_')[0] + '_' + known_base.split('_')[1]

            # Filter files to match the exact core name prefix
            matchingFiles = [f for f in relevant_files if os.path.splitext(os.path.basename(f))[0].startswith(coreName)]

            return matchingFiles
        
        except:
            return None


    #   Match map type to texture files
    @err_catcher(name=__name__)
    def matchTexType(self, fileName, fileList):
        #   Get basename without extension
        baseName = os.path.splitext(fileName)[0]

        #   Get the common name in all texture files
        baseNames = [os.path.splitext(os.path.basename(f))[0] for f in fileList]
        commonPrefix = self.findCommonPrefix(baseNames)

        #   Extract the texture part by removing the common prefix
        texturePart = baseName[len(commonPrefix):].strip("_").lower()

        #   Get list of keywords sorted by length (longest first)
        sortedTexTypes = sorted(self.texTypes.items(),
                    key=lambda item: -max(len(keyword) for keyword in item[1]))

        #   Loop through the sorted dict and check keywords
        for texType, keywords in sortedTexTypes:
            for keyword in sorted(keywords, key=len, reverse=True):
                if keyword.lower() in texturePart:
                    return texType

        # If no match, return None
        return None


#   Returns string of the common part of names
    def findCommonPrefix(self, baseNameList):
        if not baseNameList:
            return ""
        
        # Start with the first file's base name
        commonPrefix = baseNameList[0]
        
        # Loop through each file and adjust the common prefix
        for baseName in baseNameList[1:]:
            i = 0
            while i < len(commonPrefix) and i < len(baseName) and commonPrefix[i] == baseName[i]:
                i += 1
            # Trim the common prefix
            commonPrefix = commonPrefix[:i]  
            if not commonPrefix:
                break

            self.commonPrefix = commonPrefix
                
        return commonPrefix


    #   RCL menu for texture file list
    @err_catcher(name=__name__)
    def showContextMenu(self, pos):
        # Create the context menu
        menu = QMenu(self.tw_textureFiles)

        if self.tw_textureFiles.rowCount() > 0:
            # If not on an item show the "Clear List" option
            if not self.tw_textureFiles.itemAt(pos):
                act_Clear = menu.addAction("Clear List")
                act_Clear.triggered.connect(self.clearTextureList)

            # If on an item show the "Remove Selected Items" option
            else:
                act_Remove = menu.addAction("Remove Selected Items")
                act_Remove.triggered.connect(self.removeSelectedItems)

        # Show the menu at the cursor's position
        menu.exec_(self.tw_textureFiles.mapToGlobal(pos))


    # Receive the texture list and populate the table
    @err_catcher(name=__name__)
    def populateTextList(self, textureFiles):
        # Clear the table
        self.tw_textureFiles.setRowCount(0)

        # Get the table's text color
        tableTextColor = self.tw_textureFiles.palette().color(QPalette.Text)

        # Loop through the texture files and add rows to the table
        for row, filePath in enumerate(textureFiles):
            if self.isSupportedFormat(filePath):
                fileName = os.path.basename(filePath)
                rowPosition = self.tw_textureFiles.rowCount()

                # Insert a new row
                self.tw_textureFiles.insertRow(rowPosition)

                # Attempt to match texType from the fileName
                matchedTexType = self.matchTexType(fileName, textureFiles)

                # Add Map column with a combo box
                mapComboBox = QComboBox()
                mapComboBox.currentIndexChanged.connect(lambda index, r=row: self.updateTexType(r))
                mapComboBox.addItem("NONE")
                for texType in self.texTypes.keys():
                    mapComboBox.addItem(texType.capitalize())
                if matchedTexType:
                    index = mapComboBox.findText(matchedTexType.capitalize())
                    if index != -1:
                        mapComboBox.setCurrentIndex(index)
                else:
                    mapComboBox.setCurrentIndex(0)

                # Apply the same text color as the table
                mapComboBox.setStyleSheet(f"QComboBox {{ color: {tableTextColor.name()}; }}")
                self.tw_textureFiles.setCellWidget(rowPosition, 0, mapComboBox)

                # Add File column with the file name
                fileItem = QTableWidgetItem(fileName)
                self.tw_textureFiles.setItem(rowPosition, 1, fileItem)

                # Add Path column with the full file path (hidden)
                pathItem = QTableWidgetItem(filePath)
                self.tw_textureFiles.setItem(rowPosition, 2, pathItem)

        self.saveTexList()


    @err_catcher(name=__name__)
    def refreshTexList(self):
        # Clear the table
        self.tw_textureFiles.setRowCount(0)

        # Force text color to white
        forcedTextColor = "#D0D0D0"

        # Loop through self.textureFiles and add rows to the table
        for row, texFile in enumerate(self.textureFiles):
            filePath = texFile.get("path", "")
            fileName = texFile.get("file", "")
            texType = texFile.get("map", "NONE")

            # Insert a new row
            rowPosition = self.tw_textureFiles.rowCount()
            self.tw_textureFiles.insertRow(rowPosition)

            # Add Map column with a combo box
            mapComboBox = QComboBox()
            mapComboBox.currentIndexChanged.connect(lambda index, r=row: self.updateTexType(r))
            mapComboBox.addItem("NONE")
            for texTypeKey in self.texTypes.keys():
                mapComboBox.addItem(texTypeKey.capitalize())
            if texType:
                index = mapComboBox.findText(texType.capitalize())
                if index != -1:
                    mapComboBox.setCurrentIndex(index)
            else:
                mapComboBox.setCurrentIndex(0)

            # Manually set combo box text color to white
            mapComboBox.setStyleSheet(f"QComboBox {{ color: {forcedTextColor}; }}")
            self.tw_textureFiles.setCellWidget(rowPosition, 0, mapComboBox)

            # Add File column with the file name
            fileItem = QTableWidgetItem(fileName)
            fileItem.setForeground(QBrush(QColor(forcedTextColor)))  # Set text to white
            self.tw_textureFiles.setItem(rowPosition, 1, fileItem)

            # Add Path column with the full file path (hidden)
            pathItem = QTableWidgetItem(filePath)
            pathItem.setForeground(QBrush(QColor(forcedTextColor)))  # Set text to white
            self.tw_textureFiles.setItem(rowPosition, 2, pathItem)

        # Optionally save the table state
        self.saveTexList()


    #   Clears all items from list
    @err_catcher(name=__name__)
    def clearTextureList(self):
        #   Clear the list widget
        self.tw_textureFiles.clearContents()
        #   Reset textureFiles
        self.textureFiles = []

        self.refreshTexList()


    #   Removes texture file from list
    @err_catcher(name=__name__)
    def removeSelectedItems(self):
        # Get the selected items (QTableWidgetItems)
        selItems = self.tw_textureFiles.selectedItems()

        # Remove items from the list and self.textureFiles
        rowsToRemove = set()
        for item in selItems:
            row = self.tw_textureFiles.row(item)
            rowsToRemove.add(row)

            # Retrieve the stored file path
            filePath = self.tw_textureFiles.item(row, 2).text()

            # Remove from the textureFiles list
            self.textureFiles = [data for data in self.textureFiles if data["path"] != filePath]

        # Remove rows from the table widget
        for row in sorted(rowsToRemove, reverse=True):
            self.tw_textureFiles.removeRow(row)

        self.refreshTexList()



    # Saves the table content to self.textureFiles
    @err_catcher(name=__name__)
    def saveTexList(self):
        self.textureFiles = []  # Clear the current list

        # Loop through the rows in the table
        for row in range(self.tw_textureFiles.rowCount()):
            # Get the combo box widget for the "Map" column
            mapComboBox = self.tw_textureFiles.cellWidget(row, 0)
            selectedTexType = mapComboBox.currentText() if mapComboBox else "NONE"

            # Get the file name from the "File" column
            fileItem = self.tw_textureFiles.item(row, 1)
            fileName = fileItem.text() if fileItem else ""

            # Get the file path from the "Path" column
            pathItem = self.tw_textureFiles.item(row, 2)
            filePath = pathItem.text() if pathItem else ""

            # Add the row's data to the textureFiles list
            textureFileData = {
                "map": selectedTexType,
                "file": fileName,
                "path": filePath,
            }
            self.textureFiles.append(textureFileData)

        self.stateManager.saveStatesToScene()



    #   Updates map in textureFiles
    @err_catcher(name=__name__)
    def updateTexType(self, row):
        # Get the combo box in the given row
        combo = self.tw_textureFiles.cellWidget(row, 0)
        if combo:
            selected_text = combo.currentText()
            self.textureFiles[row]['map'] = selected_text

        self.saveTexList()


    #   Checks if image format is supported
    @err_catcher(name=__name__)
    def isSupportedFormat(self, fileName):
        ext = os.path.splitext(fileName)[-1].lower()
        return ext in self.supportedFormats


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
        self.stateManager.saveImports()
        self.updateUi()
        self.stateManager.saveStatesToScene()


    #   Creates the material using textures
    @err_catcher(name=__name__)
    def createUsdMaterial(self, update=False, path=None, settings=None):
        result = True

        if self.stateManager.standalone:
            return result

        #   Get current comp filename
        fileName = self.core.getCurrentFileName()

        doImport = True

        #   Only send textures that have a mapping (not NONE)
        sendTexFiles = [item for item in self.textureFiles if item["map"] != "NONE"]
        
        #   Make dict
        texData = {"toolName": self.commonPrefix,
                   "shaderName": self.commonPrefix,
                   "shaderType": "uShader",
                   "nodeUID": self.stateUID,
                   "texFiles": sendTexFiles}

        #   Call fucntion to import
        importResult = self.fuseFuncts.createUsdMaterial(self,
                                                         UUID=self.stateUID,
                                                         texData=texData,
                                                         update=update)

        if not importResult:
            result = None
            doImport = False
        else:
            result = importResult["result"]
            doImport = importResult["doImport"]
            # if result and "mode" in importResult:
            #     self.setStateMode(importResult["mode"])

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

            # if not result:
            #     # msgStr = "Import failed: %s" % impFileName
            #     self.core.popup(msgStr, title="ImportFile")

        kwargs = {
            "state": self,
            "scenefile": fileName,
        }
        self.core.callback("postImport", **kwargs)
        self.stateManager.saveImports()
        self.updateUi()
        self.stateManager.saveStatesToScene()

        return result


    #   Called from StateManager when deleting state
    @err_catcher(name=__name__)
    def preDelete(self, item=None):
        try:
            #   Defaults to Delete the Node
            delAction = "Yes"

            if not self.core.uiAvailable:
                logger.debug(f"Deleting node: {item}")

            else:
                #   Get node data
                nodeUID = self.stateUID
                nodeName = self.fuseFuncts.getNodeNameByUID(nodeUID)
                nodeData = self.fuseFuncts.getNodeInfo("import3d", nodeUID)

                #   Get associated textures
                connectedTools = nodeData.get("connectedNodes", [])

                #   If the material tool exists, show popup question
                if nodeName:
                    message = f"Would you like to also remove the material ({nodeData['shaderName']}) from the Comp?"
                    buttons = ["Yes", "No"]
                    buttonToBool = {"Yes": True, "No": False}

                    response = self.core.popupQuestion(message, buttons=buttons, icon=QMessageBox.NoIcon)
                    delAction = buttonToBool.get(response, False)

                    if response == "Yes":
                        self.fuseFuncts.deleteNode("import3d", nodeUID, delAction=delAction)
                        #   Delete all the textures
                        for uid in connectedTools:
                            self.fuseFuncts.deleteNode("import3d", uid, delAction=delAction)

        except:
            logger.warning("ERROR: Unable to remove Material from Comp")


    @err_catcher(name=__name__)
    def getStateProps(self):
        return {
            "statename": self.e_name.text(),
            "stateUID": self.stateUID,
            "statemode": self.stateMode,
            "textureFiles": self.textureFiles,
            "taskname": self.taskName,
            "setname": self.setName,
            "lastExplorerDir": self.lastExplorerDir
        }
