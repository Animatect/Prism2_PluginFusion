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

class Ui_wg_USD_Material(object):
    def setupUi(self, wg_USD_Material):
        if not wg_USD_Material.objectName():
            wg_USD_Material.setObjectName(u"wg_USD_Material")
        wg_USD_Material.resize(340, 795)
        self.verticalLayout = QVBoxLayout(wg_USD_Material)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.f_name = QWidget(wg_USD_Material)
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

        self.gb_import = QGroupBox(wg_USD_Material)
        self.gb_import.setObjectName(u"gb_import")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.gb_import.sizePolicy().hasHeightForWidth())
        self.gb_import.setSizePolicy(sizePolicy)
        self.verticalLayout_2 = QVBoxLayout(self.gb_import)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.groupBox = QGroupBox(self.gb_import)
        self.groupBox.setObjectName(u"groupBox")
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy1)
        self.verticalLayout_3 = QVBoxLayout(self.groupBox)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.w_browse = QWidget(self.groupBox)
        self.w_browse.setObjectName(u"w_browse")
        self.horizontalLayout_7 = QHBoxLayout(self.w_browse)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalLayout_7.setContentsMargins(9, 0, 9, 0)
        self.b_browse = QPushButton(self.w_browse)
        self.b_browse.setObjectName(u"b_browse")
        self.b_browse.setFocusPolicy(Qt.NoFocus)
        self.b_browse.setContextMenuPolicy(Qt.NoContextMenu)

        self.horizontalLayout_7.addWidget(self.b_browse)

        self.b_explorer = QPushButton(self.w_browse)
        self.b_explorer.setObjectName(u"b_explorer")
        self.b_explorer.setMinimumSize(QSize(0, 0))
        self.b_explorer.setMaximumSize(QSize(99999, 16777215))
        self.b_explorer.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout_7.addWidget(self.b_explorer)


        self.verticalLayout_3.addWidget(self.w_browse)

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
        self.verticalLayout_7 = QVBoxLayout(self.gb_options)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.f_focusView = QHBoxLayout()
        self.f_focusView.setObjectName(u"f_focusView")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.f_focusView.addItem(self.horizontalSpacer)

        self.b_focusView = QPushButton(self.gb_options)
        self.b_focusView.setObjectName(u"b_focusView")

        self.f_focusView.addWidget(self.b_focusView)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.f_focusView.addItem(self.horizontalSpacer_2)


        self.verticalLayout_7.addLayout(self.f_focusView)


        self.verticalLayout_2.addWidget(self.gb_options)

        self.gb_matX = QGroupBox(self.gb_import)
        self.gb_matX.setObjectName(u"gb_matX")
        self.verticalLayout_5 = QVBoxLayout(self.gb_matX)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.lo_matX = QHBoxLayout()
        self.lo_matX.setObjectName(u"lo_matX")
        self.e_matxFile = QLineEdit(self.gb_matX)
        self.e_matxFile.setObjectName(u"e_matxFile")
        self.e_matxFile.setAcceptDrops(False)
        self.e_matxFile.setReadOnly(True)

        self.lo_matX.addWidget(self.e_matxFile)


        self.verticalLayout_5.addLayout(self.lo_matX)


        self.verticalLayout_2.addWidget(self.gb_matX)

        self.gb_textures = QGroupBox(self.gb_import)
        self.gb_textures.setObjectName(u"gb_textures")
        self.gb_textures.setEnabled(True)
        sizePolicy.setHeightForWidth(self.gb_textures.sizePolicy().hasHeightForWidth())
        self.gb_textures.setSizePolicy(sizePolicy)
        self.verticalLayout_6 = QVBoxLayout(self.gb_textures)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.tw_textureFiles = QTableWidget(self.gb_textures)
        if (self.tw_textureFiles.columnCount() < 3):
            self.tw_textureFiles.setColumnCount(3)
        self.tw_textureFiles.setObjectName(u"tw_textureFiles")
        sizePolicy2 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.tw_textureFiles.sizePolicy().hasHeightForWidth())
        self.tw_textureFiles.setSizePolicy(sizePolicy2)
        self.tw_textureFiles.setMinimumSize(QSize(0, 400))
        self.tw_textureFiles.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.tw_textureFiles.setShowGrid(False)
        self.tw_textureFiles.setColumnCount(3)

        self.verticalLayout_6.addWidget(self.tw_textureFiles)

        self.b_createShader = QPushButton(self.gb_textures)
        self.b_createShader.setObjectName(u"b_createShader")
        self.b_createShader.setFocusPolicy(Qt.NoFocus)

        self.verticalLayout_6.addWidget(self.b_createShader)


        self.verticalLayout_2.addWidget(self.gb_textures)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)


        self.verticalLayout.addWidget(self.gb_import)


        self.retranslateUi(wg_USD_Material)

        QMetaObject.connectSlotsByName(wg_USD_Material)
    # setupUi

    def retranslateUi(self, wg_USD_Material):
        wg_USD_Material.setWindowTitle(QCoreApplication.translate("wg_USD_Material", u"USD_Material", None))
        self.l_name.setText(QCoreApplication.translate("wg_USD_Material", u"State name:", None))
        self.l_class.setText(QCoreApplication.translate("wg_USD_Material", u"USD Material", None))
        self.gb_import.setTitle(QCoreApplication.translate("wg_USD_Material", u"Import", None))
        self.groupBox.setTitle(QCoreApplication.translate("wg_USD_Material", u"Texture Files", None))
        self.b_browse.setText(QCoreApplication.translate("wg_USD_Material", u"Browse", None))
        self.b_explorer.setText(QCoreApplication.translate("wg_USD_Material", u"Open Explorer", None))
        self.b_import.setText(QCoreApplication.translate("wg_USD_Material", u"Re-Import", None))
        self.gb_options.setTitle("")
        self.b_focusView.setText(QCoreApplication.translate("wg_USD_Material", u"Focus View", None))
        self.gb_matX.setTitle(QCoreApplication.translate("wg_USD_Material", u"MaterialX", None))
        self.gb_textures.setTitle(QCoreApplication.translate("wg_USD_Material", u"Textures", None))
        self.b_createShader.setText(QCoreApplication.translate("wg_USD_Material", u"Create Material", None))
    # retranslateUi

