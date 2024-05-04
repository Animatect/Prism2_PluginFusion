# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'fus_ImageRender.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_wg_ImageRender(object):
    def setupUi(self, wg_ImageRender):
        if not wg_ImageRender.objectName():
            wg_ImageRender.setObjectName(u"wg_ImageRender")
        wg_ImageRender.resize(497, 937)
        self.verticalLayout = QVBoxLayout(wg_ImageRender)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.f_name = QWidget(wg_ImageRender)
        self.f_name.setObjectName(u"f_name")
        self.horizontalLayout_4 = QHBoxLayout(self.f_name)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(9, 0, 18, 0)
        self.l_name = QLabel(self.f_name)
        self.l_name.setObjectName(u"l_name")

        self.horizontalLayout_4.addWidget(self.l_name)

        self.e_name = QLineEdit(self.f_name)
        self.e_name.setObjectName(u"e_name")

        self.horizontalLayout_4.addWidget(self.e_name)

        self.l_class = QLabel(self.f_name)
        self.l_class.setObjectName(u"l_class")
        font = QFont()
        font.setBold(True)
        font.setWeight(75)
        self.l_class.setFont(font)

        self.horizontalLayout_4.addWidget(self.l_class)


        self.verticalLayout.addWidget(self.f_name)

        self.gb_imageRender = QGroupBox(wg_ImageRender)
        self.gb_imageRender.setObjectName(u"gb_imageRender")
        self.gridLayout_2 = QGridLayout(self.gb_imageRender)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.w_context = QWidget(self.gb_imageRender)
        self.w_context.setObjectName(u"w_context")
        self.horizontalLayout_11 = QHBoxLayout(self.w_context)
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.horizontalLayout_11.setContentsMargins(9, 0, 9, 0)
        self.label_7 = QLabel(self.w_context)
        self.label_7.setObjectName(u"label_7")

        self.horizontalLayout_11.addWidget(self.label_7)

        self.horizontalSpacer_5 = QSpacerItem(37, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_11.addItem(self.horizontalSpacer_5)

        self.l_context = QLabel(self.w_context)
        self.l_context.setObjectName(u"l_context")

        self.horizontalLayout_11.addWidget(self.l_context)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_11.addItem(self.horizontalSpacer_3)

        self.b_context = QPushButton(self.w_context)
        self.b_context.setObjectName(u"b_context")

        self.horizontalLayout_11.addWidget(self.b_context)

        self.cb_context = QComboBox(self.w_context)
        self.cb_context.setObjectName(u"cb_context")

        self.horizontalLayout_11.addWidget(self.cb_context)


        self.gridLayout_2.addWidget(self.w_context, 0, 0, 1, 1)

        self.f_taskname = QWidget(self.gb_imageRender)
        self.f_taskname.setObjectName(u"f_taskname")
        self.horizontalLayout_10 = QHBoxLayout(self.f_taskname)
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.horizontalLayout_10.setContentsMargins(9, 0, 9, 0)
        self.label_2 = QLabel(self.f_taskname)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout_10.addWidget(self.label_2)

        self.l_taskName = QLabel(self.f_taskname)
        self.l_taskName.setObjectName(u"l_taskName")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.l_taskName.sizePolicy().hasHeightForWidth())
        self.l_taskName.setSizePolicy(sizePolicy)
        self.l_taskName.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_10.addWidget(self.l_taskName)

        self.b_changeTask = QPushButton(self.f_taskname)
        self.b_changeTask.setObjectName(u"b_changeTask")
        self.b_changeTask.setEnabled(True)
        self.b_changeTask.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout_10.addWidget(self.b_changeTask)


        self.gridLayout_2.addWidget(self.f_taskname, 1, 0, 1, 1)

        self.f_range = QWidget(self.gb_imageRender)
        self.f_range.setObjectName(u"f_range")
        self.horizontalLayout = QHBoxLayout(self.f_range)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(9, 0, 9, 0)
        self.label_3 = QLabel(self.f_range)
        self.label_3.setObjectName(u"label_3")

        self.horizontalLayout.addWidget(self.label_3)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)

        self.cb_rangeType = QComboBox(self.f_range)
        self.cb_rangeType.setObjectName(u"cb_rangeType")
        self.cb_rangeType.setMinimumSize(QSize(150, 0))

        self.horizontalLayout.addWidget(self.cb_rangeType)


        self.gridLayout_2.addWidget(self.f_range, 2, 0, 1, 1)

        self.w_frameRangeValues = QWidget(self.gb_imageRender)
        self.w_frameRangeValues.setObjectName(u"w_frameRangeValues")
        self.gridLayout = QGridLayout(self.w_frameRangeValues)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(9, 0, 9, 0)
        self.l_rangeEnd = QLabel(self.w_frameRangeValues)
        self.l_rangeEnd.setObjectName(u"l_rangeEnd")
        self.l_rangeEnd.setMinimumSize(QSize(30, 0))
        self.l_rangeEnd.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.l_rangeEnd, 1, 5, 1, 1)

        self.sp_rangeEnd = QSpinBox(self.w_frameRangeValues)
        self.sp_rangeEnd.setObjectName(u"sp_rangeEnd")
        self.sp_rangeEnd.setMaximumSize(QSize(55, 16777215))
        self.sp_rangeEnd.setMaximum(99999)
        self.sp_rangeEnd.setValue(1100)

        self.gridLayout.addWidget(self.sp_rangeEnd, 1, 6, 1, 1)

        self.sp_rangeStart = QSpinBox(self.w_frameRangeValues)
        self.sp_rangeStart.setObjectName(u"sp_rangeStart")
        self.sp_rangeStart.setMaximumSize(QSize(55, 16777215))
        self.sp_rangeStart.setMaximum(99999)
        self.sp_rangeStart.setValue(1001)

        self.gridLayout.addWidget(self.sp_rangeStart, 0, 6, 1, 1)

        self.l_rangeStart = QLabel(self.w_frameRangeValues)
        self.l_rangeStart.setObjectName(u"l_rangeStart")
        self.l_rangeStart.setMinimumSize(QSize(30, 0))
        self.l_rangeStart.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.l_rangeStart, 0, 5, 1, 1)

        self.l_rangeStartInfo = QLabel(self.w_frameRangeValues)
        self.l_rangeStartInfo.setObjectName(u"l_rangeStartInfo")

        self.gridLayout.addWidget(self.l_rangeStartInfo, 0, 0, 1, 1)

        self.horizontalSpacer_13 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer_13, 0, 4, 1, 1)

        self.l_rangeEndInfo = QLabel(self.w_frameRangeValues)
        self.l_rangeEndInfo.setObjectName(u"l_rangeEndInfo")

        self.gridLayout.addWidget(self.l_rangeEndInfo, 1, 0, 1, 1)


        self.gridLayout_2.addWidget(self.w_frameRangeValues, 3, 0, 1, 1)

        self.w_frameExpression = QWidget(self.gb_imageRender)
        self.w_frameExpression.setObjectName(u"w_frameExpression")
        self.horizontalLayout_15 = QHBoxLayout(self.w_frameExpression)
        self.horizontalLayout_15.setSpacing(6)
        self.horizontalLayout_15.setObjectName(u"horizontalLayout_15")
        self.horizontalLayout_15.setContentsMargins(9, 0, 9, 0)
        self.l_frameExpression = QLabel(self.w_frameExpression)
        self.l_frameExpression.setObjectName(u"l_frameExpression")

        self.horizontalLayout_15.addWidget(self.l_frameExpression)

        self.horizontalSpacer_14 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_15.addItem(self.horizontalSpacer_14)

        self.le_frameExpression = QLineEdit(self.w_frameExpression)
        self.le_frameExpression.setObjectName(u"le_frameExpression")
        self.le_frameExpression.setMinimumSize(QSize(150, 0))

        self.horizontalLayout_15.addWidget(self.le_frameExpression)


        self.gridLayout_2.addWidget(self.w_frameExpression, 4, 0, 1, 1)

        self.f_cam = QWidget(self.gb_imageRender)
        self.f_cam.setObjectName(u"f_cam")
        self.horizontalLayout_2 = QHBoxLayout(self.f_cam)
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(9, 0, 9, 0)

        self.gridLayout_2.addWidget(self.f_cam, 5, 0, 1, 1)

        self.f_resolution = QWidget(self.gb_imageRender)
        self.f_resolution.setObjectName(u"f_resolution")
        self.horizontalLayout_9 = QHBoxLayout(self.f_resolution)
        self.horizontalLayout_9.setSpacing(6)
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.horizontalLayout_9.setContentsMargins(9, 0, 9, 0)
        self.label_4 = QLabel(self.f_resolution)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setEnabled(True)

        self.horizontalLayout_9.addWidget(self.label_4)

        self.horizontalSpacer_9 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_9.addItem(self.horizontalSpacer_9)

        self.chb_resOverride = QCheckBox(self.f_resolution)
        self.chb_resOverride.setObjectName(u"chb_resOverride")

        self.horizontalLayout_9.addWidget(self.chb_resOverride)

        self.sp_resWidth = QSpinBox(self.f_resolution)
        self.sp_resWidth.setObjectName(u"sp_resWidth")
        self.sp_resWidth.setEnabled(False)
        self.sp_resWidth.setMinimum(1)
        self.sp_resWidth.setMaximum(99999)
        self.sp_resWidth.setValue(1280)

        self.horizontalLayout_9.addWidget(self.sp_resWidth)

        self.sp_resHeight = QSpinBox(self.f_resolution)
        self.sp_resHeight.setObjectName(u"sp_resHeight")
        self.sp_resHeight.setEnabled(False)
        self.sp_resHeight.setMinimum(1)
        self.sp_resHeight.setMaximum(99999)
        self.sp_resHeight.setValue(720)

        self.horizontalLayout_9.addWidget(self.sp_resHeight)

        self.b_resPresets = QPushButton(self.f_resolution)
        self.b_resPresets.setObjectName(u"b_resPresets")
        self.b_resPresets.setEnabled(False)
        self.b_resPresets.setMinimumSize(QSize(23, 23))
        self.b_resPresets.setMaximumSize(QSize(23, 23))
        self.b_resPresets.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout_9.addWidget(self.b_resPresets)


        self.gridLayout_2.addWidget(self.f_resolution, 6, 0, 1, 1)

        self.w_renderPreset = QWidget(self.gb_imageRender)
        self.w_renderPreset.setObjectName(u"w_renderPreset")
        self.horizontalLayout_14 = QHBoxLayout(self.w_renderPreset)
        self.horizontalLayout_14.setObjectName(u"horizontalLayout_14")
        self.horizontalLayout_14.setContentsMargins(-1, 0, -1, 0)
        self.l_renderPreset = QLabel(self.w_renderPreset)
        self.l_renderPreset.setObjectName(u"l_renderPreset")

        self.horizontalLayout_14.addWidget(self.l_renderPreset)

        self.horizontalSpacer_7 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_14.addItem(self.horizontalSpacer_7)

        self.chb_renderPreset = QCheckBox(self.w_renderPreset)
        self.chb_renderPreset.setObjectName(u"chb_renderPreset")

        self.horizontalLayout_14.addWidget(self.chb_renderPreset)

        self.cb_renderPreset = QComboBox(self.w_renderPreset)
        self.cb_renderPreset.setObjectName(u"cb_renderPreset")
        self.cb_renderPreset.setEnabled(False)
        self.cb_renderPreset.setMinimumSize(QSize(150, 0))

        self.horizontalLayout_14.addWidget(self.cb_renderPreset)


        self.gridLayout_2.addWidget(self.w_renderPreset, 7, 0, 1, 1)

        self.w_master = QWidget(self.gb_imageRender)
        self.w_master.setObjectName(u"w_master")
        self.horizontalLayout_17 = QHBoxLayout(self.w_master)
        self.horizontalLayout_17.setSpacing(0)
        self.horizontalLayout_17.setObjectName(u"horizontalLayout_17")
        self.horizontalLayout_17.setContentsMargins(9, 0, 9, 0)
        self.l_outPath_2 = QLabel(self.w_master)
        self.l_outPath_2.setObjectName(u"l_outPath_2")

        self.horizontalLayout_17.addWidget(self.l_outPath_2)

        self.horizontalSpacer_28 = QSpacerItem(113, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_17.addItem(self.horizontalSpacer_28)

        self.cb_master = QComboBox(self.w_master)
        self.cb_master.setObjectName(u"cb_master")
        self.cb_master.setMinimumSize(QSize(150, 0))

        self.horizontalLayout_17.addWidget(self.cb_master)


        self.gridLayout_2.addWidget(self.w_master, 8, 0, 1, 1)

        self.w_outPath = QWidget(self.gb_imageRender)
        self.w_outPath.setObjectName(u"w_outPath")
        self.horizontalLayout_16 = QHBoxLayout(self.w_outPath)
        self.horizontalLayout_16.setSpacing(0)
        self.horizontalLayout_16.setObjectName(u"horizontalLayout_16")
        self.horizontalLayout_16.setContentsMargins(9, 0, 9, 0)
        self.l_outPath = QLabel(self.w_outPath)
        self.l_outPath.setObjectName(u"l_outPath")

        self.horizontalLayout_16.addWidget(self.l_outPath)

        self.horizontalSpacer_27 = QSpacerItem(113, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_16.addItem(self.horizontalSpacer_27)

        self.cb_outPath = QComboBox(self.w_outPath)
        self.cb_outPath.setObjectName(u"cb_outPath")
        self.cb_outPath.setMinimumSize(QSize(150, 0))

        self.horizontalLayout_16.addWidget(self.cb_outPath)


        self.gridLayout_2.addWidget(self.w_outPath, 9, 0, 1, 1)

        self.f_renderLayer = QWidget(self.gb_imageRender)
        self.f_renderLayer.setObjectName(u"f_renderLayer")
        self.horizontalLayout_5 = QHBoxLayout(self.f_renderLayer)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(9, 0, 9, 0)
        self.label_5 = QLabel(self.f_renderLayer)
        self.label_5.setObjectName(u"label_5")

        self.horizontalLayout_5.addWidget(self.label_5)

        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_6)

        self.cb_renderLayer = QComboBox(self.f_renderLayer)
        self.cb_renderLayer.setObjectName(u"cb_renderLayer")
        self.cb_renderLayer.setEnabled(True)
        self.cb_renderLayer.setMinimumSize(QSize(150, 0))

        self.horizontalLayout_5.addWidget(self.cb_renderLayer)


        self.gridLayout_2.addWidget(self.f_renderLayer, 10, 0, 1, 1)

        self.w_format = QWidget(self.gb_imageRender)
        self.w_format.setObjectName(u"w_format")
        self.horizontalLayout_6 = QHBoxLayout(self.w_format)
        self.horizontalLayout_6.setSpacing(0)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(9, 0, 9, 0)
        self.label_6 = QLabel(self.w_format)
        self.label_6.setObjectName(u"label_6")

        self.horizontalLayout_6.addWidget(self.label_6)

        self.horizontalSpacer_12 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_12)

        self.cb_format = QComboBox(self.w_format)
        self.cb_format.setObjectName(u"cb_format")
        self.cb_format.setMinimumSize(QSize(150, 0))

        self.horizontalLayout_6.addWidget(self.cb_format)


        self.gridLayout_2.addWidget(self.w_format, 11, 0, 1, 1)

        self.f_rendernode = QWidget(self.gb_imageRender)
        self.f_rendernode.setObjectName(u"f_rendernode")
        self.f_rendernode.setEnabled(True)
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.f_rendernode.sizePolicy().hasHeightForWidth())
        self.f_rendernode.setSizePolicy(sizePolicy1)
        self.f_rendernode.setBaseSize(QSize(0, 0))
        self.horizontalLayout_20 = QHBoxLayout(self.f_rendernode)
        self.horizontalLayout_20.setObjectName(u"horizontalLayout_20")
        self.horizontalLayout_20.setContentsMargins(9, 0, 9, 0)
        self.label_10 = QLabel(self.f_rendernode)
        self.label_10.setObjectName(u"label_10")

        self.horizontalLayout_20.addWidget(self.label_10)

        self.verticalGroupBox = QGroupBox(self.f_rendernode)
        self.verticalGroupBox.setObjectName(u"verticalGroupBox")
        self.verticalLayout_2 = QVBoxLayout(self.verticalGroupBox)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.verticalLayout_2.addItem(self.horizontalSpacer)


        self.horizontalLayout_20.addWidget(self.verticalGroupBox)

        self.b_setRendernode = QPushButton(self.f_rendernode)
        self.b_setRendernode.setObjectName(u"b_setRendernode")
        self.b_setRendernode.setEnabled(True)
        sizePolicy2 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.b_setRendernode.sizePolicy().hasHeightForWidth())
        self.b_setRendernode.setSizePolicy(sizePolicy2)
        self.b_setRendernode.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout_20.addWidget(self.b_setRendernode)

        self.chb_passthrough = QCheckBox(self.f_rendernode)
        self.chb_passthrough.setObjectName(u"chb_passthrough")
        self.chb_passthrough.setChecked(True)
        self.chb_passthrough.setTristate(False)

        self.horizontalLayout_20.addWidget(self.chb_passthrough)


        self.gridLayout_2.addWidget(self.f_rendernode, 12, 0, 1, 1)

        self.f_setOutputOnly = QWidget(self.gb_imageRender)
        self.f_setOutputOnly.setObjectName(u"f_setOutputOnly")
        self.horizontalLayout_12 = QHBoxLayout(self.f_setOutputOnly)
        self.horizontalLayout_12.setSpacing(6)
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.horizontalLayout_12.setContentsMargins(9, 0, 9, 0)
        self.label_9 = QLabel(self.f_setOutputOnly)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setEnabled(True)

        self.horizontalLayout_12.addWidget(self.label_9)

        self.horizontalSpacer_10 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_12.addItem(self.horizontalSpacer_10)

        self.chb_outOnly = QCheckBox(self.f_setOutputOnly)
        self.chb_outOnly.setObjectName(u"chb_outOnly")

        self.horizontalLayout_12.addWidget(self.chb_outOnly)


        self.gridLayout_2.addWidget(self.f_setOutputOnly, 13, 0, 1, 1)


        self.verticalLayout.addWidget(self.gb_imageRender)

        self.gb_submit = QGroupBox(wg_ImageRender)
        self.gb_submit.setObjectName(u"gb_submit")
        self.gb_submit.setCheckable(True)
        self.gb_submit.setChecked(True)
        self.verticalLayout_8 = QVBoxLayout(self.gb_submit)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.verticalLayout_8.setContentsMargins(-1, 15, -1, -1)
        self.f_manager = QWidget(self.gb_submit)
        self.f_manager.setObjectName(u"f_manager")
        self.horizontalLayout_13 = QHBoxLayout(self.f_manager)
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.horizontalLayout_13.setContentsMargins(9, 0, 9, 0)
        self.l_manager = QLabel(self.f_manager)
        self.l_manager.setObjectName(u"l_manager")

        self.horizontalLayout_13.addWidget(self.l_manager)

        self.horizontalSpacer_19 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_13.addItem(self.horizontalSpacer_19)

        self.cb_manager = QComboBox(self.f_manager)
        self.cb_manager.setObjectName(u"cb_manager")
        self.cb_manager.setMinimumSize(QSize(150, 0))

        self.horizontalLayout_13.addWidget(self.cb_manager)


        self.verticalLayout_8.addWidget(self.f_manager)

        self.f_rjPrio = QWidget(self.gb_submit)
        self.f_rjPrio.setObjectName(u"f_rjPrio")
        self.horizontalLayout_21 = QHBoxLayout(self.f_rjPrio)
        self.horizontalLayout_21.setObjectName(u"horizontalLayout_21")
        self.horizontalLayout_21.setContentsMargins(9, 0, 9, 0)
        self.l_rjPrio = QLabel(self.f_rjPrio)
        self.l_rjPrio.setObjectName(u"l_rjPrio")

        self.horizontalLayout_21.addWidget(self.l_rjPrio)

        self.horizontalSpacer_16 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_21.addItem(self.horizontalSpacer_16)

        self.sp_rjPrio = QSpinBox(self.f_rjPrio)
        self.sp_rjPrio.setObjectName(u"sp_rjPrio")
        self.sp_rjPrio.setMaximum(100)
        self.sp_rjPrio.setValue(50)

        self.horizontalLayout_21.addWidget(self.sp_rjPrio)


        self.verticalLayout_8.addWidget(self.f_rjPrio)

        self.f_rjWidgetsPerTask = QWidget(self.gb_submit)
        self.f_rjWidgetsPerTask.setObjectName(u"f_rjWidgetsPerTask")
        self.horizontalLayout_22 = QHBoxLayout(self.f_rjWidgetsPerTask)
        self.horizontalLayout_22.setObjectName(u"horizontalLayout_22")
        self.horizontalLayout_22.setContentsMargins(9, 0, 9, 0)
        self.label_15 = QLabel(self.f_rjWidgetsPerTask)
        self.label_15.setObjectName(u"label_15")

        self.horizontalLayout_22.addWidget(self.label_15)

        self.horizontalSpacer_17 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_22.addItem(self.horizontalSpacer_17)

        self.sp_rjFramesPerTask = QSpinBox(self.f_rjWidgetsPerTask)
        self.sp_rjFramesPerTask.setObjectName(u"sp_rjFramesPerTask")
        self.sp_rjFramesPerTask.setMaximum(9999)
        self.sp_rjFramesPerTask.setValue(5)

        self.horizontalLayout_22.addWidget(self.sp_rjFramesPerTask)


        self.verticalLayout_8.addWidget(self.f_rjWidgetsPerTask)

        self.f_rjTimeout = QWidget(self.gb_submit)
        self.f_rjTimeout.setObjectName(u"f_rjTimeout")
        self.horizontalLayout_28 = QHBoxLayout(self.f_rjTimeout)
        self.horizontalLayout_28.setObjectName(u"horizontalLayout_28")
        self.horizontalLayout_28.setContentsMargins(9, 0, 9, 0)
        self.l_rjTimeout = QLabel(self.f_rjTimeout)
        self.l_rjTimeout.setObjectName(u"l_rjTimeout")

        self.horizontalLayout_28.addWidget(self.l_rjTimeout)

        self.horizontalSpacer_23 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_28.addItem(self.horizontalSpacer_23)

        self.sp_rjTimeout = QSpinBox(self.f_rjTimeout)
        self.sp_rjTimeout.setObjectName(u"sp_rjTimeout")
        self.sp_rjTimeout.setMinimum(1)
        self.sp_rjTimeout.setMaximum(9999)
        self.sp_rjTimeout.setValue(180)

        self.horizontalLayout_28.addWidget(self.sp_rjTimeout)


        self.verticalLayout_8.addWidget(self.f_rjTimeout)

        self.f_rjSuspended = QWidget(self.gb_submit)
        self.f_rjSuspended.setObjectName(u"f_rjSuspended")
        self.horizontalLayout_26 = QHBoxLayout(self.f_rjSuspended)
        self.horizontalLayout_26.setObjectName(u"horizontalLayout_26")
        self.horizontalLayout_26.setContentsMargins(9, 0, 9, 0)
        self.label_18 = QLabel(self.f_rjSuspended)
        self.label_18.setObjectName(u"label_18")

        self.horizontalLayout_26.addWidget(self.label_18)

        self.horizontalSpacer_20 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_26.addItem(self.horizontalSpacer_20)

        self.chb_rjSuspended = QCheckBox(self.f_rjSuspended)
        self.chb_rjSuspended.setObjectName(u"chb_rjSuspended")
        self.chb_rjSuspended.setChecked(False)

        self.horizontalLayout_26.addWidget(self.chb_rjSuspended)


        self.verticalLayout_8.addWidget(self.f_rjSuspended)

        self.f_osDependencies = QWidget(self.gb_submit)
        self.f_osDependencies.setObjectName(u"f_osDependencies")
        self.horizontalLayout_27 = QHBoxLayout(self.f_osDependencies)
        self.horizontalLayout_27.setObjectName(u"horizontalLayout_27")
        self.horizontalLayout_27.setContentsMargins(9, 0, 9, 0)
        self.label_19 = QLabel(self.f_osDependencies)
        self.label_19.setObjectName(u"label_19")

        self.horizontalLayout_27.addWidget(self.label_19)

        self.horizontalSpacer_22 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_27.addItem(self.horizontalSpacer_22)

        self.chb_osDependencies = QCheckBox(self.f_osDependencies)
        self.chb_osDependencies.setObjectName(u"chb_osDependencies")
        self.chb_osDependencies.setChecked(True)

        self.horizontalLayout_27.addWidget(self.chb_osDependencies)


        self.verticalLayout_8.addWidget(self.f_osDependencies)

        self.f_osUpload = QWidget(self.gb_submit)
        self.f_osUpload.setObjectName(u"f_osUpload")
        self.horizontalLayout_23 = QHBoxLayout(self.f_osUpload)
        self.horizontalLayout_23.setObjectName(u"horizontalLayout_23")
        self.horizontalLayout_23.setContentsMargins(-1, 0, -1, 0)
        self.label_16 = QLabel(self.f_osUpload)
        self.label_16.setObjectName(u"label_16")

        self.horizontalLayout_23.addWidget(self.label_16)

        self.horizontalSpacer_18 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_23.addItem(self.horizontalSpacer_18)

        self.chb_osUpload = QCheckBox(self.f_osUpload)
        self.chb_osUpload.setObjectName(u"chb_osUpload")
        self.chb_osUpload.setChecked(True)

        self.horizontalLayout_23.addWidget(self.chb_osUpload)


        self.verticalLayout_8.addWidget(self.f_osUpload)

        self.f_osPAssets = QWidget(self.gb_submit)
        self.f_osPAssets.setObjectName(u"f_osPAssets")
        self.horizontalLayout_24 = QHBoxLayout(self.f_osPAssets)
        self.horizontalLayout_24.setObjectName(u"horizontalLayout_24")
        self.horizontalLayout_24.setContentsMargins(-1, 0, -1, 0)
        self.label_17 = QLabel(self.f_osPAssets)
        self.label_17.setObjectName(u"label_17")

        self.horizontalLayout_24.addWidget(self.label_17)

        self.horizontalSpacer_21 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_24.addItem(self.horizontalSpacer_21)

        self.chb_osPAssets = QCheckBox(self.f_osPAssets)
        self.chb_osPAssets.setObjectName(u"chb_osPAssets")
        self.chb_osPAssets.setChecked(True)

        self.horizontalLayout_24.addWidget(self.chb_osPAssets)


        self.verticalLayout_8.addWidget(self.f_osPAssets)

        self.gb_osSlaves = QGroupBox(self.gb_submit)
        self.gb_osSlaves.setObjectName(u"gb_osSlaves")
        self.horizontalLayout_25 = QHBoxLayout(self.gb_osSlaves)
        self.horizontalLayout_25.setObjectName(u"horizontalLayout_25")
        self.horizontalLayout_25.setContentsMargins(9, 3, 9, 3)
        self.e_osSlaves = QLineEdit(self.gb_osSlaves)
        self.e_osSlaves.setObjectName(u"e_osSlaves")

        self.horizontalLayout_25.addWidget(self.e_osSlaves)

        self.b_osSlaves = QPushButton(self.gb_osSlaves)
        self.b_osSlaves.setObjectName(u"b_osSlaves")
        self.b_osSlaves.setMaximumSize(QSize(25, 16777215))
        self.b_osSlaves.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout_25.addWidget(self.b_osSlaves)


        self.verticalLayout_8.addWidget(self.gb_osSlaves)

        self.w_dlConcurrentTasks = QWidget(self.gb_submit)
        self.w_dlConcurrentTasks.setObjectName(u"w_dlConcurrentTasks")
        self.horizontalLayout_29 = QHBoxLayout(self.w_dlConcurrentTasks)
        self.horizontalLayout_29.setObjectName(u"horizontalLayout_29")
        self.horizontalLayout_29.setContentsMargins(9, 0, 9, 0)
        self.l_dlConcurrentTasks = QLabel(self.w_dlConcurrentTasks)
        self.l_dlConcurrentTasks.setObjectName(u"l_dlConcurrentTasks")

        self.horizontalLayout_29.addWidget(self.l_dlConcurrentTasks)

        self.horizontalSpacer_24 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_29.addItem(self.horizontalSpacer_24)

        self.sp_dlConcurrentTasks = QSpinBox(self.w_dlConcurrentTasks)
        self.sp_dlConcurrentTasks.setObjectName(u"sp_dlConcurrentTasks")
        self.sp_dlConcurrentTasks.setMinimum(1)
        self.sp_dlConcurrentTasks.setMaximum(99)
        self.sp_dlConcurrentTasks.setValue(1)

        self.horizontalLayout_29.addWidget(self.sp_dlConcurrentTasks)


        self.verticalLayout_8.addWidget(self.w_dlConcurrentTasks)

        self.w_dlGPUpt = QWidget(self.gb_submit)
        self.w_dlGPUpt.setObjectName(u"w_dlGPUpt")
        self.horizontalLayout_30 = QHBoxLayout(self.w_dlGPUpt)
        self.horizontalLayout_30.setObjectName(u"horizontalLayout_30")
        self.horizontalLayout_30.setContentsMargins(9, 0, 9, 0)
        self.l_dlGPUpt = QLabel(self.w_dlGPUpt)
        self.l_dlGPUpt.setObjectName(u"l_dlGPUpt")

        self.horizontalLayout_30.addWidget(self.l_dlGPUpt)

        self.horizontalSpacer_25 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_30.addItem(self.horizontalSpacer_25)

        self.sp_dlGPUpt = QSpinBox(self.w_dlGPUpt)
        self.sp_dlGPUpt.setObjectName(u"sp_dlGPUpt")
        self.sp_dlGPUpt.setMinimum(0)
        self.sp_dlGPUpt.setMaximum(99)
        self.sp_dlGPUpt.setValue(0)

        self.horizontalLayout_30.addWidget(self.sp_dlGPUpt)


        self.verticalLayout_8.addWidget(self.w_dlGPUpt)

        self.w_dlGPUdevices = QWidget(self.gb_submit)
        self.w_dlGPUdevices.setObjectName(u"w_dlGPUdevices")
        self.horizontalLayout_31 = QHBoxLayout(self.w_dlGPUdevices)
        self.horizontalLayout_31.setObjectName(u"horizontalLayout_31")
        self.horizontalLayout_31.setContentsMargins(9, 0, 9, 0)
        self.l_dlGPUdevices = QLabel(self.w_dlGPUdevices)
        self.l_dlGPUdevices.setObjectName(u"l_dlGPUdevices")

        self.horizontalLayout_31.addWidget(self.l_dlGPUdevices)

        self.horizontalSpacer_26 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_31.addItem(self.horizontalSpacer_26)

        self.le_dlGPUdevices = QLineEdit(self.w_dlGPUdevices)
        self.le_dlGPUdevices.setObjectName(u"le_dlGPUdevices")
        self.le_dlGPUdevices.setMinimumSize(QSize(150, 0))

        self.horizontalLayout_31.addWidget(self.le_dlGPUdevices)


        self.verticalLayout_8.addWidget(self.w_dlGPUdevices)


        self.verticalLayout.addWidget(self.gb_submit)

        self.gb_previous = QGroupBox(wg_ImageRender)
        self.gb_previous.setObjectName(u"gb_previous")
        self.gb_previous.setCheckable(False)
        self.gb_previous.setChecked(False)
        self.horizontalLayout_18 = QHBoxLayout(self.gb_previous)
        self.horizontalLayout_18.setObjectName(u"horizontalLayout_18")
        self.horizontalLayout_18.setContentsMargins(9, 9, 9, 9)
        self.scrollArea = QScrollArea(self.gb_previous)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 446, 69))
        self.verticalLayout_3 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.l_pathLast = QLabel(self.scrollAreaWidgetContents)
        self.l_pathLast.setObjectName(u"l_pathLast")

        self.verticalLayout_3.addWidget(self.l_pathLast)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.horizontalLayout_18.addWidget(self.scrollArea)

        self.b_pathLast = QToolButton(self.gb_previous)
        self.b_pathLast.setObjectName(u"b_pathLast")
        self.b_pathLast.setEnabled(True)
        self.b_pathLast.setArrowType(Qt.DownArrow)

        self.horizontalLayout_18.addWidget(self.b_pathLast)


        self.verticalLayout.addWidget(self.gb_previous)

        QWidget.setTabOrder(self.e_name, self.b_context)
        QWidget.setTabOrder(self.b_context, self.cb_context)
        QWidget.setTabOrder(self.cb_context, self.cb_rangeType)
        QWidget.setTabOrder(self.cb_rangeType, self.sp_rangeStart)
        QWidget.setTabOrder(self.sp_rangeStart, self.sp_rangeEnd)
        QWidget.setTabOrder(self.sp_rangeEnd, self.le_frameExpression)
        QWidget.setTabOrder(self.le_frameExpression, self.chb_resOverride)
        QWidget.setTabOrder(self.chb_resOverride, self.sp_resWidth)
        QWidget.setTabOrder(self.sp_resWidth, self.sp_resHeight)
        QWidget.setTabOrder(self.sp_resHeight, self.chb_renderPreset)
        QWidget.setTabOrder(self.chb_renderPreset, self.cb_renderPreset)
        QWidget.setTabOrder(self.cb_renderPreset, self.cb_master)
        QWidget.setTabOrder(self.cb_master, self.cb_outPath)
        QWidget.setTabOrder(self.cb_outPath, self.cb_renderLayer)
        QWidget.setTabOrder(self.cb_renderLayer, self.cb_format)
        QWidget.setTabOrder(self.cb_format, self.scrollArea)
        QWidget.setTabOrder(self.scrollArea, self.b_pathLast)

        self.retranslateUi(wg_ImageRender)

        QMetaObject.connectSlotsByName(wg_ImageRender)
    # setupUi

    def retranslateUi(self, wg_ImageRender):
        wg_ImageRender.setWindowTitle(QCoreApplication.translate("wg_ImageRender", u"Image Render", None))
        self.l_name.setText(QCoreApplication.translate("wg_ImageRender", u"Name:", None))
        self.l_class.setText(QCoreApplication.translate("wg_ImageRender", u"ImageRender", None))
        self.gb_imageRender.setTitle(QCoreApplication.translate("wg_ImageRender", u"General", None))
        self.label_7.setText(QCoreApplication.translate("wg_ImageRender", u"Context:", None))
        self.l_context.setText("")
        self.b_context.setText(QCoreApplication.translate("wg_ImageRender", u"Select", None))
        self.label_2.setText(QCoreApplication.translate("wg_ImageRender", u"Identifier:", None))
        self.l_taskName.setText("")
        self.b_changeTask.setText(QCoreApplication.translate("wg_ImageRender", u"change", None))
        self.label_3.setText(QCoreApplication.translate("wg_ImageRender", u"Framerange:", None))
        self.l_rangeEnd.setText(QCoreApplication.translate("wg_ImageRender", u"1100", None))
        self.l_rangeStart.setText(QCoreApplication.translate("wg_ImageRender", u"1001", None))
        self.l_rangeStartInfo.setText(QCoreApplication.translate("wg_ImageRender", u"Start:", None))
        self.l_rangeEndInfo.setText(QCoreApplication.translate("wg_ImageRender", u"End:", None))
        self.l_frameExpression.setText(QCoreApplication.translate("wg_ImageRender", u"Frame expression:", None))
        self.label_4.setText(QCoreApplication.translate("wg_ImageRender", u"Resolution override:", None))
        self.chb_resOverride.setText("")
        self.b_resPresets.setText(QCoreApplication.translate("wg_ImageRender", u"\u25bc", None))
        self.l_renderPreset.setText(QCoreApplication.translate("wg_ImageRender", u"Rendersettings preset:", None))
        self.chb_renderPreset.setText("")
        self.l_outPath_2.setText(QCoreApplication.translate("wg_ImageRender", u"Master Version:", None))
        self.l_outPath.setText(QCoreApplication.translate("wg_ImageRender", u"Location:", None))
        self.label_5.setText(QCoreApplication.translate("wg_ImageRender", u"Render layer:", None))
        self.label_6.setText(QCoreApplication.translate("wg_ImageRender", u"Format:", None))
        self.label_10.setText(QCoreApplication.translate("wg_ImageRender", u"RenderNode:", None))
#if QT_CONFIG(tooltip)
        self.b_setRendernode.setToolTip(QCoreApplication.translate("wg_ImageRender", u"Set RenderNode by name or create a new one", None))
#endif // QT_CONFIG(tooltip)
        self.b_setRendernode.setText(QCoreApplication.translate("wg_ImageRender", u"SetRenderNode", None))
#if QT_CONFIG(tooltip)
        self.chb_passthrough.setToolTip(QCoreApplication.translate("wg_ImageRender", u"Enables or disables the render node.", None))
#endif // QT_CONFIG(tooltip)
        self.chb_passthrough.setText(QCoreApplication.translate("wg_ImageRender", u"Active", None))
#if QT_CONFIG(tooltip)
        self.f_setOutputOnly.setToolTip(QCoreApplication.translate("wg_ImageRender", u"If this checkbox is selected, executing the state won't render the node, instead it will set the correct name and version, it will also create the appropiate folders and set the path to it for easy access in the state's UI", None))
#endif // QT_CONFIG(tooltip)
        self.label_9.setText(QCoreApplication.translate("wg_ImageRender", u"Set Output only:", None))
        self.chb_outOnly.setText("")
        self.gb_submit.setTitle(QCoreApplication.translate("wg_ImageRender", u"Submit Render Job", None))
        self.l_manager.setText(QCoreApplication.translate("wg_ImageRender", u"Manager:", None))
        self.l_rjPrio.setText(QCoreApplication.translate("wg_ImageRender", u"Priority:", None))
        self.label_15.setText(QCoreApplication.translate("wg_ImageRender", u"Frames per Task:", None))
        self.l_rjTimeout.setText(QCoreApplication.translate("wg_ImageRender", u"Task Timeout (min)", None))
        self.label_18.setText(QCoreApplication.translate("wg_ImageRender", u"Submit suspended:", None))
        self.chb_rjSuspended.setText("")
        self.label_19.setText(QCoreApplication.translate("wg_ImageRender", u"Submit dependent files:", None))
        self.chb_osDependencies.setText("")
        self.label_16.setText(QCoreApplication.translate("wg_ImageRender", u"Upload output:", None))
        self.chb_osUpload.setText("")
        self.label_17.setText(QCoreApplication.translate("wg_ImageRender", u"Use Project Assets", None))
        self.chb_osPAssets.setText("")
        self.gb_osSlaves.setTitle(QCoreApplication.translate("wg_ImageRender", u"Assign to slaves:", None))
        self.b_osSlaves.setText(QCoreApplication.translate("wg_ImageRender", u"...", None))
        self.l_dlConcurrentTasks.setText(QCoreApplication.translate("wg_ImageRender", u"Concurrent Tasks:", None))
        self.l_dlGPUpt.setText(QCoreApplication.translate("wg_ImageRender", u"GPUs Per Task:", None))
        self.l_dlGPUdevices.setText(QCoreApplication.translate("wg_ImageRender", u"Select GPU Devices:", None))
        self.le_dlGPUdevices.setPlaceholderText(QCoreApplication.translate("wg_ImageRender", u"Enter Valid GPU Device Id(s)", None))
        self.gb_previous.setTitle(QCoreApplication.translate("wg_ImageRender", u"Previous render", None))
        self.l_pathLast.setText(QCoreApplication.translate("wg_ImageRender", u"None", None))
        self.b_pathLast.setText(QCoreApplication.translate("wg_ImageRender", u"...", None))
    # retranslateUi

