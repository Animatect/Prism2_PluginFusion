# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'default_ImportFile.ui'
##
## Created by: Qt User Interface Compiler version 6.4.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from qtpy.QtCore import *  # type: ignore
from qtpy.QtGui import *  # type: ignore
from qtpy.QtWidgets import *  # type: ignore

class Ui_wg_Image_Import(object):
    def setupUi(self, wg_Image_Import):
        if not wg_Image_Import.objectName():
            wg_Image_Import.setObjectName(u"wg_Image_Import")
        wg_Image_Import.resize(340, 600)
        self.verticalLayout = QVBoxLayout(wg_Image_Import)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.f_name = QWidget(wg_Image_Import)
        self.f_name.setObjectName(u"f_name")
        self.horizontalLayout_2 = QHBoxLayout(self.f_name)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(9, 0, 18, 0)
        self.l_name = QLabel(self.f_name)
        self.l_name.setObjectName(u"l_name")

        self.horizontalLayout_2.addWidget(self.l_name)

        self.e_name = QLineEdit(self.f_name)
        self.e_name.setObjectName(u"e_name")
        self.e_name.setMinimumSize(QSize(0, 0))
        self.e_name.setMaximumSize(QSize(9999, 16777215))

        self.horizontalLayout_2.addWidget(self.e_name)

        self.l_class = QLabel(self.f_name)
        self.l_class.setObjectName(u"l_class")
        font = QFont()
        font.setBold(True)
        self.l_class.setFont(font)

        self.horizontalLayout_2.addWidget(self.l_class)


        self.verticalLayout.addWidget(self.f_name)

        self.gb_import = QGroupBox(wg_Image_Import)
        self.gb_import.setObjectName(u"gb_import")
        self.verticalLayout_2 = QVBoxLayout(self.gb_import)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.groupBox = QGroupBox(self.gb_import)
        self.groupBox.setObjectName(u"groupBox")
        self.verticalLayout_3 = QVBoxLayout(self.groupBox)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.w_currentVersion = QWidget(self.groupBox)
        self.w_currentVersion.setObjectName(u"w_currentVersion")
        self.horizontalLayout_5 = QHBoxLayout(self.w_currentVersion)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(9, 0, 9, 0)
        self.label_3 = QLabel(self.w_currentVersion)
        self.label_3.setObjectName(u"label_3")

        self.horizontalLayout_5.addWidget(self.label_3)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer)

        self.l_curVersion = QLabel(self.w_currentVersion)
        self.l_curVersion.setObjectName(u"l_curVersion")

        self.horizontalLayout_5.addWidget(self.l_curVersion)


        self.verticalLayout_3.addWidget(self.w_currentVersion)

        self.w_latestVersion = QWidget(self.groupBox)
        self.w_latestVersion.setObjectName(u"w_latestVersion")
        self.horizontalLayout_6 = QHBoxLayout(self.w_latestVersion)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(9, 0, 9, 0)
        self.label_6 = QLabel(self.w_latestVersion)
        self.label_6.setObjectName(u"label_6")

        self.horizontalLayout_6.addWidget(self.label_6)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_2)

        self.l_latestVersion = QLabel(self.w_latestVersion)
        self.l_latestVersion.setObjectName(u"l_latestVersion")

        self.horizontalLayout_6.addWidget(self.l_latestVersion)


        self.verticalLayout_3.addWidget(self.w_latestVersion)

        self.w_autoUpdate = QWidget(self.groupBox)
        self.w_autoUpdate.setObjectName(u"w_autoUpdate")
        self.horizontalLayout_14 = QHBoxLayout(self.w_autoUpdate)
        self.horizontalLayout_14.setObjectName(u"horizontalLayout_14")
        self.horizontalLayout_14.setContentsMargins(9, 0, 9, 0)
        self.l_autoUpdate = QLabel(self.w_autoUpdate)
        self.l_autoUpdate.setObjectName(u"l_autoUpdate")

        self.horizontalLayout_14.addWidget(self.l_autoUpdate)

        self.horizontalSpacer_10 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_14.addItem(self.horizontalSpacer_10)

        self.chb_autoUpdate = QCheckBox(self.w_autoUpdate)
        self.chb_autoUpdate.setObjectName(u"chb_autoUpdate")
        self.chb_autoUpdate.setChecked(False)

        self.horizontalLayout_14.addWidget(self.chb_autoUpdate)


        self.verticalLayout_3.addWidget(self.w_autoUpdate)

        self.w_importLatest = QWidget(self.groupBox)
        self.w_importLatest.setObjectName(u"w_importLatest")
        self.horizontalLayout_7 = QHBoxLayout(self.w_importLatest)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalLayout_7.setContentsMargins(9, 0, 9, 0)
        self.b_browse = QPushButton(self.w_importLatest)
        self.b_browse.setObjectName(u"b_browse")
        self.b_browse.setFocusPolicy(Qt.NoFocus)
        self.b_browse.setContextMenuPolicy(Qt.CustomContextMenu)

        self.horizontalLayout_7.addWidget(self.b_browse)

        self.b_importLatest = QPushButton(self.w_importLatest)
        self.b_importLatest.setObjectName(u"b_importLatest")
        self.b_importLatest.setMinimumSize(QSize(0, 0))
        self.b_importLatest.setMaximumSize(QSize(99999, 16777215))
        self.b_importLatest.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout_7.addWidget(self.b_importLatest)


        self.verticalLayout_3.addWidget(self.w_importLatest)

        self.widget = QWidget(self.groupBox)
        self.widget.setObjectName(u"widget")
        self.horizontalLayout = QHBoxLayout(self.widget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(-1, 0, -1, 0)
        self.b_import = QPushButton(self.widget)
        self.b_import.setObjectName(u"b_import")
        self.b_import.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout.addWidget(self.b_import)


        self.verticalLayout_3.addWidget(self.widget)


        self.verticalLayout_2.addWidget(self.groupBox)

        self.gb_options = QGroupBox(self.gb_import)
        self.gb_options.setObjectName(u"gb_options")
        self.verticalLayout_6 = QVBoxLayout(self.gb_options)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.f_keepRefEdits = QWidget(self.gb_options)
        self.f_keepRefEdits.setObjectName(u"f_keepRefEdits")
        self.horizontalLayout_10 = QHBoxLayout(self.f_keepRefEdits)
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.horizontalLayout_10.setContentsMargins(9, 0, 9, 0)
        self.chb_keepRefEdits = QCheckBox(self.f_keepRefEdits)
        self.chb_keepRefEdits.setObjectName(u"chb_keepRefEdits")
        self.chb_keepRefEdits.setChecked(True)

        self.horizontalLayout_10.addWidget(self.chb_keepRefEdits)


        self.verticalLayout_6.addWidget(self.f_keepRefEdits)

        self.f_nameSpaces = QWidget(self.gb_options)
        self.f_nameSpaces.setObjectName(u"f_nameSpaces")
        self.horizontalLayout_12 = QHBoxLayout(self.f_nameSpaces)
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.horizontalLayout_12.setContentsMargins(9, 0, 9, 0)

        self.verticalLayout_6.addWidget(self.f_nameSpaces)

        self.f_abcPath = QWidget(self.gb_options)
        self.f_abcPath.setObjectName(u"f_abcPath")
        self.horizontalLayout_11 = QHBoxLayout(self.f_abcPath)
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.horizontalLayout_11.setContentsMargins(9, 0, 9, 0)
        self.chb_abcPath = QCheckBox(self.f_abcPath)
        self.chb_abcPath.setObjectName(u"chb_abcPath")

        self.horizontalLayout_11.addWidget(self.chb_abcPath)


        self.verticalLayout_6.addWidget(self.f_abcPath)

        self.w_trackObjects = QWidget(self.gb_options)
        self.w_trackObjects.setObjectName(u"w_trackObjects")
        self.horizontalLayout_9 = QHBoxLayout(self.w_trackObjects)
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.horizontalLayout_9.setContentsMargins(9, 0, 9, 0)

        self.verticalLayout_6.addWidget(self.w_trackObjects)


        self.verticalLayout_2.addWidget(self.gb_options)

        self.gb_channels = QGroupBox(self.gb_import)
        self.gb_channels.setObjectName(u"gb_channels")
        self.verticalLayout_4 = QVBoxLayout(self.gb_channels)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(9, 9, 9, 9)
        self.lw_objects = QListWidget(self.gb_channels)
        self.lw_objects.setObjectName(u"lw_objects")
        self.lw_objects.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.lw_objects.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.lw_objects.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)

        self.verticalLayout_4.addWidget(self.lw_objects)

        self.b_selectAll = QPushButton(self.gb_channels)
        self.b_selectAll.setObjectName(u"b_selectAll")

        self.verticalLayout_4.addWidget(self.b_selectAll)


        self.verticalLayout_2.addWidget(self.gb_channels)


        self.verticalLayout.addWidget(self.gb_import)

        QWidget.setTabOrder(self.e_name, self.chb_autoUpdate)
        QWidget.setTabOrder(self.chb_autoUpdate, self.chb_keepRefEdits)
        QWidget.setTabOrder(self.chb_keepRefEdits, self.chb_abcPath)
        QWidget.setTabOrder(self.chb_abcPath, self.lw_objects)
        QWidget.setTabOrder(self.lw_objects, self.b_selectAll)

        self.retranslateUi(wg_Image_Import)

        QMetaObject.connectSlotsByName(wg_Image_Import)
    # setupUi

    def retranslateUi(self, wg_Image_Import):
        wg_Image_Import.setWindowTitle(QCoreApplication.translate("wg_Image_Import", u"ImportFile", None))
        self.l_name.setText(QCoreApplication.translate("wg_Image_Import", u"State name:", None))
        self.l_class.setText(QCoreApplication.translate("wg_Image_Import", u"ImportFile", None))
        self.gb_import.setTitle(QCoreApplication.translate("wg_Image_Import", u"Import", None))
        self.groupBox.setTitle(QCoreApplication.translate("wg_Image_Import", u"Version", None))
        self.label_3.setText(QCoreApplication.translate("wg_Image_Import", u"Current Version:", None))
        self.l_curVersion.setText(QCoreApplication.translate("wg_Image_Import", u"-", None))
        self.label_6.setText(QCoreApplication.translate("wg_Image_Import", u"Latest Version:", None))
        self.l_latestVersion.setText(QCoreApplication.translate("wg_Image_Import", u"-", None))
        self.l_autoUpdate.setText(QCoreApplication.translate("wg_Image_Import", u"Auto load latest version:", None))
        self.chb_autoUpdate.setText("")
        self.b_browse.setText(QCoreApplication.translate("wg_Image_Import", u"Browse", None))
        self.b_importLatest.setText(QCoreApplication.translate("wg_Image_Import", u"Import latest Version", None))
        self.b_import.setText(QCoreApplication.translate("wg_Image_Import", u"Re-Import", None))
        self.gb_options.setTitle(QCoreApplication.translate("wg_Image_Import", u"Options", None))
        self.chb_keepRefEdits.setText("")
        self.chb_abcPath.setText("")
        self.gb_channels.setTitle(QCoreApplication.translate("wg_Image_Import", u"Channels", None))
        self.b_selectAll.setText(QCoreApplication.translate("wg_Image_Import", u"Select all", None))
    # retranslateUi

