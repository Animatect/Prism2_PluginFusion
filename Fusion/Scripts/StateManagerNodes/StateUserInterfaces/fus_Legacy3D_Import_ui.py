# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'fus_Legacy3D_Import.ui'
##
## Created by: Qt User Interface Compiler version 6.8.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from qtpy.QtCore import *  # type: ignore
from qtpy.QtGui import *  # type: ignore
from qtpy.QtWidgets import *  # type: ignore

class Ui_wg_Legacy3D_Import(object):
    def setupUi(self, wg_Legacy3D_Import):
        if not wg_Legacy3D_Import.objectName():
            wg_Legacy3D_Import.setObjectName(u"wg_Legacy3D_Import")
        wg_Legacy3D_Import.resize(423, 668)
        self.verticalLayout = QVBoxLayout(wg_Legacy3D_Import)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.f_name = QWidget(wg_Legacy3D_Import)
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

        self.cb_taskColor = QComboBox(self.f_name)
        self.cb_taskColor.setObjectName(u"cb_taskColor")

        self.horizontalLayout_2.addWidget(self.cb_taskColor)


        self.verticalLayout.addWidget(self.f_name)

        self.gb_import = QGroupBox(wg_Legacy3D_Import)
        self.gb_import.setObjectName(u"gb_import")
        self.verticalLayout_2 = QVBoxLayout(self.gb_import)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(-1, 0, -1, 9)
        self.gb_version = QGroupBox(self.gb_import)
        self.gb_version.setObjectName(u"gb_version")
        self.verticalLayout_3 = QVBoxLayout(self.gb_version)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(-1, 6, -1, 9)
        self.w_currentVersion = QWidget(self.gb_version)
        self.w_currentVersion.setObjectName(u"w_currentVersion")
        self.horizontalLayout_5 = QHBoxLayout(self.w_currentVersion)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(9, 0, 9, 0)
        self.label_3 = QLabel(self.w_currentVersion)
        self.label_3.setObjectName(u"label_3")

        self.horizontalLayout_5.addWidget(self.label_3)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.horizontalLayout_5.addItem(self.horizontalSpacer)

        self.l_curVersion = QLabel(self.w_currentVersion)
        self.l_curVersion.setObjectName(u"l_curVersion")

        self.horizontalLayout_5.addWidget(self.l_curVersion)


        self.verticalLayout_3.addWidget(self.w_currentVersion)

        self.w_latestVersion = QWidget(self.gb_version)
        self.w_latestVersion.setObjectName(u"w_latestVersion")
        self.horizontalLayout_6 = QHBoxLayout(self.w_latestVersion)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(9, 0, 9, 0)
        self.label_6 = QLabel(self.w_latestVersion)
        self.label_6.setObjectName(u"label_6")

        self.horizontalLayout_6.addWidget(self.label_6)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_2)

        self.l_latestVersion = QLabel(self.w_latestVersion)
        self.l_latestVersion.setObjectName(u"l_latestVersion")

        self.horizontalLayout_6.addWidget(self.l_latestVersion)


        self.verticalLayout_3.addWidget(self.w_latestVersion)

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
        self.b_importLatest = QPushButton(self.w_importLatest)
        self.b_importLatest.setObjectName(u"b_importLatest")
        self.b_importLatest.setMinimumSize(QSize(0, 0))
        self.b_importLatest.setMaximumSize(QSize(99999, 16777215))
        self.b_importLatest.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout_7.addWidget(self.b_importLatest)

        self.b_browse = QPushButton(self.w_importLatest)
        self.b_browse.setObjectName(u"b_browse")
        self.b_browse.setFocusPolicy(Qt.NoFocus)
        self.b_browse.setContextMenuPolicy(Qt.NoContextMenu)

        self.horizontalLayout_7.addWidget(self.b_browse)


        self.verticalLayout_3.addWidget(self.w_importLatest)

        self.widget = QWidget(self.gb_version)
        self.widget.setObjectName(u"widget")
        self.horizontalLayout = QHBoxLayout(self.widget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(-1, 0, -1, 0)
        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_6)

        self.b_import = QPushButton(self.widget)
        self.b_import.setObjectName(u"b_import")
        self.b_import.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout.addWidget(self.b_import)

        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_5)


        self.verticalLayout_3.addWidget(self.widget)

        self.label = QLabel(self.gb_version)
        self.label.setObjectName(u"label")
        self.label.setWordWrap(True)

        self.verticalLayout_3.addWidget(self.label)


        self.verticalLayout_2.addWidget(self.gb_version)

        self.gb_options = QGroupBox(self.gb_import)
        self.gb_options.setObjectName(u"gb_options")
        self.verticalLayout_4 = QVBoxLayout(self.gb_options)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.f_viewFocus = QWidget(self.gb_options)
        self.f_viewFocus.setObjectName(u"f_viewFocus")
        self.horizontalLayout_11 = QHBoxLayout(self.f_viewFocus)
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.horizontalLayout_11.setContentsMargins(9, 0, 9, 0)
        self.horizontalSpacer_7 = QSpacerItem(40, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.horizontalLayout_11.addItem(self.horizontalSpacer_7)

        self.b_focusView = QPushButton(self.f_viewFocus)
        self.b_focusView.setObjectName(u"b_focusView")

        self.horizontalLayout_11.addWidget(self.b_focusView)

        self.horizontalSpacer_8 = QSpacerItem(40, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.horizontalLayout_11.addItem(self.horizontalSpacer_8)


        self.verticalLayout_4.addWidget(self.f_viewFocus)

        self.f_3DScene = QWidget(self.gb_options)
        self.f_3DScene.setObjectName(u"f_3DScene")
        self.horizontalLayout_10 = QHBoxLayout(self.f_3DScene)
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.horizontalLayout_10.setContentsMargins(9, 0, 9, 0)
        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.horizontalLayout_10.addItem(self.horizontalSpacer_3)

        self.b_createRenderNode = QPushButton(self.f_3DScene)
        self.b_createRenderNode.setObjectName(u"b_createRenderNode")

        self.horizontalLayout_10.addWidget(self.b_createRenderNode)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.horizontalLayout_10.addItem(self.horizontalSpacer_4)


        self.verticalLayout_4.addWidget(self.f_3DScene)


        self.verticalLayout_2.addWidget(self.gb_options)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)


        self.verticalLayout.addWidget(self.gb_import)

        QWidget.setTabOrder(self.e_name, self.chb_autoUpdate)

        self.retranslateUi(wg_Legacy3D_Import)

        QMetaObject.connectSlotsByName(wg_Legacy3D_Import)
    # setupUi

    def retranslateUi(self, wg_Legacy3D_Import):
        wg_Legacy3D_Import.setWindowTitle(QCoreApplication.translate("wg_Legacy3D_Import", u"ImportFile", None))
        self.l_name.setText(QCoreApplication.translate("wg_Legacy3D_Import", u"State name:", None))
        self.l_class.setText(QCoreApplication.translate("wg_Legacy3D_Import", u"Legacy3D_Import", None))
        self.gb_import.setTitle("")
        self.gb_version.setTitle(QCoreApplication.translate("wg_Legacy3D_Import", u"Version", None))
        self.label_3.setText(QCoreApplication.translate("wg_Legacy3D_Import", u"Current Version:", None))
        self.l_curVersion.setText(QCoreApplication.translate("wg_Legacy3D_Import", u"-", None))
        self.label_6.setText(QCoreApplication.translate("wg_Legacy3D_Import", u"Latest Version:", None))
        self.l_latestVersion.setText(QCoreApplication.translate("wg_Legacy3D_Import", u"-", None))
        self.l_autoUpdate.setText(QCoreApplication.translate("wg_Legacy3D_Import", u"Auto load latest version:", None))
        self.chb_autoUpdate.setText("")
        self.b_importLatest.setText(QCoreApplication.translate("wg_Legacy3D_Import", u"Import latest Version", None))
        self.b_browse.setText(QCoreApplication.translate("wg_Legacy3D_Import", u"Browse Version", None))
        self.b_import.setText(QCoreApplication.translate("wg_Legacy3D_Import", u"Re-Import", None))
        self.label.setText(QCoreApplication.translate("wg_Legacy3D_Import", u"<html><head/><body><p align=\"center\">Be mindful of the re-connect limitations:  Merge3D nodes that are not the Root node cannot be processed so avoid connecting anything new to them.  Use for this purpose the Root node or use the create Render Node button to create a Merge Node.</p></body></html>", None))
        self.gb_options.setTitle(QCoreApplication.translate("wg_Legacy3D_Import", u"Options", None))
        self.b_focusView.setText(QCoreApplication.translate("wg_Legacy3D_Import", u"Focus View on State Node", None))
        self.b_createRenderNode.setText(QCoreApplication.translate("wg_Legacy3D_Import", u"Create Render Node", None))
    # retranslateUi

