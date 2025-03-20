# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'fus_Image_Import.ui'
##
## Created by: Qt User Interface Compiler version 6.7.2
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
        wg_Image_Import.resize(441, 789)
        self.verticalLayout = QVBoxLayout(wg_Image_Import)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.l_class = QLabel(wg_Image_Import)
        self.l_class.setObjectName(u"l_class")
        font = QFont()
        font.setBold(True)
        self.l_class.setFont(font)

        self.horizontalLayout.addWidget(self.l_class)

        self.e_name = QLineEdit(wg_Image_Import)
        self.e_name.setObjectName(u"e_name")
        self.e_name.setMinimumSize(QSize(0, 0))
        self.e_name.setMaximumSize(QSize(9999, 16777215))

        self.horizontalLayout.addWidget(self.e_name)

        self.l_name = QLabel(wg_Image_Import)
        self.l_name.setObjectName(u"l_name")

        self.horizontalLayout.addWidget(self.l_name)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.f_name = QWidget(wg_Image_Import)
        self.f_name.setObjectName(u"f_name")
        self.horizontalLayout_2 = QHBoxLayout(self.f_name)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(9, 0, 18, 0)
        self.l_thumb = QLabel(self.f_name)
        self.l_thumb.setObjectName(u"l_thumb")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.l_thumb.sizePolicy().hasHeightForWidth())
        self.l_thumb.setSizePolicy(sizePolicy)
        self.l_thumb.setMinimumSize(QSize(0, 0))

        self.horizontalLayout_2.addWidget(self.l_thumb)

        self.lo_options = QVBoxLayout()
        self.lo_options.setObjectName(u"lo_options")
        self.cb_taskColor = QComboBox(self.f_name)
        self.cb_taskColor.setObjectName(u"cb_taskColor")

        self.lo_options.addWidget(self.cb_taskColor)

        self.b_focusView = QPushButton(self.f_name)
        self.b_focusView.setObjectName(u"b_focusView")

        self.lo_options.addWidget(self.b_focusView)

        self.b_selectTools = QPushButton(self.f_name)
        self.b_selectTools.setObjectName(u"b_selectTools")

        self.lo_options.addWidget(self.b_selectTools)


        self.horizontalLayout_2.addLayout(self.lo_options)


        self.verticalLayout.addWidget(self.f_name)

        self.gb_import = QGroupBox(wg_Image_Import)
        self.gb_import.setObjectName(u"gb_import")
        self.verticalLayout_2 = QVBoxLayout(self.gb_import)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.gb_version = QGroupBox(self.gb_import)
        self.gb_version.setObjectName(u"gb_version")
        self.verticalLayout_3 = QVBoxLayout(self.gb_version)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.w_currentVersion = QWidget(self.gb_version)
        self.w_currentVersion.setObjectName(u"w_currentVersion")
        self.horizontalLayout_5 = QHBoxLayout(self.w_currentVersion)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(9, 0, 9, 0)
        self.l_text_Current = QLabel(self.w_currentVersion)
        self.l_text_Current.setObjectName(u"l_text_Current")

        self.horizontalLayout_5.addWidget(self.l_text_Current)

        self.l_curVersion = QLabel(self.w_currentVersion)
        self.l_curVersion.setObjectName(u"l_curVersion")

        self.horizontalLayout_5.addWidget(self.l_curVersion)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.horizontalLayout_5.addItem(self.horizontalSpacer)

        self.label_6 = QLabel(self.w_currentVersion)
        self.label_6.setObjectName(u"label_6")

        self.horizontalLayout_5.addWidget(self.label_6)

        self.l_latestVersion = QLabel(self.w_currentVersion)
        self.l_latestVersion.setObjectName(u"l_latestVersion")

        self.horizontalLayout_5.addWidget(self.l_latestVersion)


        self.verticalLayout_3.addWidget(self.w_currentVersion)

        self.w_autoUpdate = QWidget(self.gb_version)
        self.w_autoUpdate.setObjectName(u"w_autoUpdate")
        self.horizontalLayout_14 = QHBoxLayout(self.w_autoUpdate)
        self.horizontalLayout_14.setObjectName(u"horizontalLayout_14")
        self.horizontalLayout_14.setContentsMargins(9, 0, 9, 0)
        self.l_autoUpdate = QLabel(self.w_autoUpdate)
        self.l_autoUpdate.setObjectName(u"l_autoUpdate")

        self.horizontalLayout_14.addWidget(self.l_autoUpdate)

        self.horizontalSpacer_10 = QSpacerItem(40, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.horizontalLayout_14.addItem(self.horizontalSpacer_10)

        self.chb_autoUpdate = QCheckBox(self.w_autoUpdate)
        self.chb_autoUpdate.setObjectName(u"chb_autoUpdate")
        self.chb_autoUpdate.setChecked(False)

        self.horizontalLayout_14.addWidget(self.chb_autoUpdate)


        self.verticalLayout_3.addWidget(self.w_autoUpdate)

        self.w_importLatest = QWidget(self.gb_version)
        self.w_importLatest.setObjectName(u"w_importLatest")
        self.horizontalLayout_7 = QHBoxLayout(self.w_importLatest)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalLayout_7.setContentsMargins(9, 0, 9, 0)
        self.b_browse = QPushButton(self.w_importLatest)
        self.b_browse.setObjectName(u"b_browse")
        self.b_browse.setFocusPolicy(Qt.NoFocus)
        self.b_browse.setContextMenuPolicy(Qt.NoContextMenu)

        self.horizontalLayout_7.addWidget(self.b_browse)

        self.b_importLatest = QPushButton(self.w_importLatest)
        self.b_importLatest.setObjectName(u"b_importLatest")
        self.b_importLatest.setMinimumSize(QSize(0, 0))
        self.b_importLatest.setMaximumSize(QSize(99999, 16777215))
        self.b_importLatest.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout_7.addWidget(self.b_importLatest)


        self.verticalLayout_3.addWidget(self.w_importLatest)


        self.verticalLayout_2.addWidget(self.gb_version)

        self.gb_options = QGroupBox(self.gb_import)
        self.gb_options.setObjectName(u"gb_options")
        self.verticalLayout_6 = QVBoxLayout(self.gb_options)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.lo_importButtons = QHBoxLayout()
        self.lo_importButtons.setObjectName(u"lo_importButtons")
        self.b_importAll = QPushButton(self.gb_options)
        self.b_importAll.setObjectName(u"b_importAll")

        self.lo_importButtons.addWidget(self.b_importAll)

        self.b_importSel = QPushButton(self.gb_options)
        self.b_importSel.setObjectName(u"b_importSel")

        self.lo_importButtons.addWidget(self.b_importSel)

        self.b_refresh = QPushButton(self.gb_options)
        self.b_refresh.setObjectName(u"b_refresh")
        self.b_refresh.setFocusPolicy(Qt.NoFocus)

        self.lo_importButtons.addWidget(self.b_refresh)


        self.verticalLayout_6.addLayout(self.lo_importButtons)


        self.verticalLayout_2.addWidget(self.gb_options)

        self.gb_channels = QGroupBox(self.gb_import)
        self.gb_channels.setObjectName(u"gb_channels")
        self.verticalLayout_4 = QVBoxLayout(self.gb_channels)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(9, 9, 9, 9)
        self.lw_objects = QTreeWidget(self.gb_channels)
        __qtreewidgetitem = QTreeWidgetItem()
        __qtreewidgetitem.setText(0, u"1");
        self.lw_objects.setHeaderItem(__qtreewidgetitem)
        self.lw_objects.setObjectName(u"lw_objects")
        self.lw_objects.setSelectionMode(QAbstractItemView.NoSelection)
        self.lw_objects.setVerticalScrollMode(QAbstractItemView.ScrollPerItem)
        self.lw_objects.setHorizontalScrollMode(QAbstractItemView.ScrollPerItem)

        self.verticalLayout_4.addWidget(self.lw_objects)


        self.verticalLayout_2.addWidget(self.gb_channels)


        self.verticalLayout.addWidget(self.gb_import)

        QWidget.setTabOrder(self.chb_autoUpdate, self.lw_objects)

        self.retranslateUi(wg_Image_Import)

        QMetaObject.connectSlotsByName(wg_Image_Import)
    # setupUi

    def retranslateUi(self, wg_Image_Import):
        wg_Image_Import.setWindowTitle(QCoreApplication.translate("wg_Image_Import", u"ImportFile", None))
        self.l_class.setText(QCoreApplication.translate("wg_Image_Import", u"Import Images", None))
        self.l_name.setText(QCoreApplication.translate("wg_Image_Import", u"State name:", None))
        self.l_thumb.setText(QCoreApplication.translate("wg_Image_Import", u"Thumbnail", None))
        self.b_focusView.setText(QCoreApplication.translate("wg_Image_Import", u"Focus View", None))
        self.b_selectTools.setText(QCoreApplication.translate("wg_Image_Import", u"Select Tools", None))
        self.gb_import.setTitle("")
        self.gb_version.setTitle(QCoreApplication.translate("wg_Image_Import", u"Version", None))
        self.l_text_Current.setText(QCoreApplication.translate("wg_Image_Import", u"Current:     ", None))
        self.l_curVersion.setText(QCoreApplication.translate("wg_Image_Import", u"-", None))
        self.label_6.setText(QCoreApplication.translate("wg_Image_Import", u"Latest:     ", None))
        self.l_latestVersion.setText(QCoreApplication.translate("wg_Image_Import", u"-", None))
        self.l_autoUpdate.setText(QCoreApplication.translate("wg_Image_Import", u"Auto load latest version:", None))
        self.chb_autoUpdate.setText("")
        self.b_browse.setText(QCoreApplication.translate("wg_Image_Import", u"Select Version", None))
        self.b_importLatest.setText(QCoreApplication.translate("wg_Image_Import", u"Import latest Version", None))
        self.gb_options.setTitle(QCoreApplication.translate("wg_Image_Import", u"Import", None))
        self.b_importAll.setText(QCoreApplication.translate("wg_Image_Import", u"Import All", None))
        self.b_importSel.setText(QCoreApplication.translate("wg_Image_Import", u"Import Selected", None))
        self.b_refresh.setText(QCoreApplication.translate("wg_Image_Import", u"Refresh", None))
        self.gb_channels.setTitle(QCoreApplication.translate("wg_Image_Import", u"Image AOV / Channels", None))
    # retranslateUi

