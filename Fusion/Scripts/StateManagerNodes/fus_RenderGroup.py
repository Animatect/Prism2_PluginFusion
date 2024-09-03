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
import sys
import time
import platform
import re

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

from PrismUtils.Decorators import err_catcher


class RenderGroupClass(object):
	className = "RenderGroup"
	listType = "Export"
	stateCategories = {"RenderGroup": [{"label": className, "stateType": className}]}

	@err_catcher(name=__name__)
	def setup(self, state, core, stateManager, node=None, stateData=None):
		self.state = state
		self.core = core
		self.stateManager = stateManager
		self.fusionFuncs = self.core.appPlugin
		self.canSetVersion = True
		self.customContext = None
		self.allowCustomContext = False
		self.mediaType = "2drenders"
		self.cb_context.addItems(["From scenefile", "Custom"])
		
		self.treeWidget = self.stateManager.tw_export
		self.itemNames = self.getItemNames()

		self.renderingStarted = False
		self.cleanOutputdir = True

		self.e_name.setVisible(True)

		self.populateCombos()

		getattr(self.fusionFuncs, "sm_render_startup", lambda x: None)(self)

		self.tasknameRequired = True

#		self.oldPalette = self.b_changeTask.palette()
		self.warnPalette = QPalette()
		self.warnPalette.setColor(QPalette.Button, QColor(200, 0, 0))
		self.warnPalette.setColor(QPalette.ButtonText, QColor(255, 255, 255))

		self.setTaskWarn(True)
		self.nameChanged(state.text(0))

		#	Render Farm
		self.gb_submit.setChecked(False)
		self.cb_manager.addItems([p.pluginName for p in self.core.plugins.getRenderfarmPlugins()])
		self.core.callback("onStateStartup", self)

		self.gb_submit.setVisible(True)
		if self.cb_manager.count() == 0:
			self.gb_submit.setVisible(False)

		self.managerChanged(True)
		

		#	Load Existing State Data
		if stateData is not None:
			self.loadData(stateData)

		#	Set Defaults for New State	
		else:
			context = self.getCurrentContext()
			if context.get("type") == "asset":
				self.setRangeType("Single Frame")
			elif context.get("type") == "shot":
				self.setRangeType("Shot")
			elif self.stateManager.standalone:
				self.setRangeType("Custom")
			else:
				self.setRangeType("Scene")

			start, end = self.getFrameRange("Scene")
			if start is not None:
				self.sp_rangeStart.setValue(start)

			if end is not None:
				self.sp_rangeEnd.setValue(end)

			if context.get("task"):
				self.setTaskname(context.get("task"))
				self.e_name.setText(context.get("task"))

			self.chb_overrideFrameRange.setChecked(False)										#	TODO SET DEFAULTS

			# self.setUniqueName(self.className + " - Compositing")
#			self.chb_upVersion.setChecked(True)


		self.connectEvents()
		self.setToolTips()
		self.refreshSubmitUi()
		self.updateUi()


	@err_catcher(name=__name__)
	def populateCombos(self):															#	TODO	ADD SAVE FOR ADDTL OPTIONS

		#	Frame Range
		self.rangeTypes = [
			"Scene",
			"Shot",
			"Single Frame",
			"Custom",
			"Expression",
		]
		self.cb_rangeType.addItems(self.rangeTypes)
		for idx, rtype in enumerate(self.rangeTypes):
			self.cb_rangeType.setItemData(
				idx, self.stateManager.getFrameRangeTypeToolTip(rtype), Qt.ToolTipRole
			)

		#	Handle Master
		masterItems = ["Force Set as Master", "Force Add to master", "Force Don't update master"]
		self.cb_master.addItems(masterItems)

		self.product_paths = self.core.paths.getRenderProductBasePaths()
		self.cb_outPath.addItems(list(self.product_paths.keys()))
		if len(self.product_paths) < 2:
			self.useLocation = False
			self.w_renderLocation.setHidden(True)
		else:
			self.useLocation = True

		#	Render Scaling
		renderScalings = [
			"25",
			"50",
			"75",
			"100",
			"125",
			"150",
			"200"
			]

		self.cb_renderScaling.addItems(renderScalings)
		tempIdx = self.cb_renderScaling.findText("100")
		self.cb_renderScaling.setCurrentIndex(tempIdx)

		qualOptions = ["Use Scene", "Force HiQ", "Force LowQ"]
		self.cb_renderQuality.addItems(qualOptions)

		motionBlurOptions = ["Use Scene", "Force Use MB", "Force No MB"]
		self.cb_renderMB.addItems(motionBlurOptions)

		proxyOptions = ["Use Scene", "Force Proxies Off", "Force Proxies On"]
		self.cb_renderProxy.addItems(proxyOptions)


	@err_catcher(name=__name__)
	def setToolTips(self):															#	TODO	ADD TOOLTIPS

		tip = "Name of RenderGroup.\nThis does not affect the render filenaming"
		self.l_class.setToolTip(tip)
		self.e_name.setToolTip(tip)

		tip = "These options will override the options in each State rendered with this RenderGroup."
		self.gb_RenderGroup.setToolTip(tip)

		tip = "Override Framerange."
		self.chb_overrideFrameRange.setToolTip(tip)
		self.label_3.setToolTip(tip)

		tip = "Override Master Version setting."
		self.chb_overrideMaster.setToolTip(tip)
		self.l_master.setToolTip(tip)
		self.cb_master.setToolTip(tip)

		tip = "Override Render Location setting."
		self.chb_overrideLocation.setToolTip(tip)
		self.l_location.setToolTip(tip)
		self.cb_outPath.setToolTip(tip)

		tip = "Scale Render Resolution of Comp."
		self.chb_overrideScaling.setToolTip(tip)
		self.l_renderScaling.setToolTip(tip)
		self.cb_renderScaling.setToolTip(tip)

		tip = "Override HiQ (High Quality) setting of Comp."
		self.chb_overrideQuality.setToolTip(tip)
		self.l_renderQuality.setToolTip(tip)
		self.cb_renderQuality.setToolTip(tip)

		tip = "Override MB (Motion Blur) setting of Comp."
		self.chb_overrideRenderMB.setToolTip(tip)
		self.l_renderMB.setToolTip(tip)
		self.cb_renderMB.setToolTip(tip)

		tip = "Override Prx (Proxy) setting of Comp."
		self.chb_overrideProxy.setToolTip(tip)
		self.l_renderProxy.setToolTip(tip)
		self.cb_renderProxy.setToolTip(tip)

		self.w_frameExpression.setToolTip(
			self.stateManager.getFrameRangeTypeToolTip("ExpressionField")
			)


	@err_catcher(name=__name__)
	def loadData(self, data):
		if "contextType" in data:
			self.setContextType(data["contextType"])
		if "customContext" in data:
			self.customContext = data["customContext"]
		if "taskname" in data:
			self.setTaskname(data["taskname"])

		self.updateUi()

		if "stateName" in data:
			self.e_name.setText(data["stateName"])
		# elif "statename" in data:
		# 	self.e_name.setText(data["statename"] + " - {identifier}")

		if "overrideFrameRange" in data:
			self.chb_overrideFrameRange.setChecked(data["overrideFrameRange"])
		if "overrideMaster" in data:
			self.chb_overrideMaster.setChecked(data["overrideMaster"])
		if "ovrMasterOption" in data:
			idx = self.cb_master.findText(data["ovrMasterOption"])
			if idx != -1:
				self.cb_master.setCurrentIndex(idx)
		if "overrideLocation" in data:
			self.chb_overrideLocation.setChecked(data["overrideLocation"])
		if "ovrLocOption" in data:
			idx = self.cb_outPath.findText(data["ovrLocOption"])
			if idx != -1:
				self.cb_outPath.setCurrentIndex(idx)
		if "overrideScaling" in data:
			self.chb_overrideScaling.setChecked(data["overrideScaling"])
		if "ovrScaleOption" in data:
			idx = self.cb_renderScaling.findText(data["ovrScaleOption"])
			if idx != -1:
				self.cb_renderScaling.setCurrentIndex(idx)
		if "overrideHiQ" in data:
			self.chb_overrideQuality.setChecked(data["overrideHiQ"])
		if "ovrHiQOption" in data:
			idx = self.cb_renderQuality.findText(data["ovrHiQOption"])
			if idx != -1:
				self.cb_renderQuality.setCurrentIndex(idx)
		if "overrideMB" in data:
			self.chb_overrideRenderMB.setChecked(data["overrideMB"])
		if "ovrMBOption" in data:
			idx = self.cb_renderMB.findText(data["ovrMBOption"])
			if idx != -1:
				self.cb_renderMB.setCurrentIndex(idx)
		if "overrideProxy" in data:
			self.chb_overrideProxy.setChecked(data["overrideProxy"])
		if "ovrProxyOption" in data:
			idx = self.cb_renderProxy.findText(data["ovrProxyOption"])
			if idx != -1:
				self.cb_renderProxy.setCurrentIndex(idx)
		if "rangeType" in data:
			idx = self.cb_rangeType.findText(data["rangeType"])
			if idx != -1:
				self.cb_rangeType.setCurrentIndex(idx)
				self.updateRange()
		if "startframe" in data:
			self.sp_rangeStart.setValue(int(data["startframe"]))
		if "endframe" in data:
			self.sp_rangeEnd.setValue(int(data["endframe"]))
		if "frameExpression" in data:
			self.le_frameExpression.setText(data["frameExpression"])
		if "curoutputpath" in data:
			idx = self.cb_outPath.findText(data["curoutputpath"])
			if idx != -1:
				self.cb_outPath.setCurrentIndex(idx)

		if "renderStates" in data:
			# Clear any existing items in the list
			self.tw_renderStates.clear()
			# Populate State List
			for state in data["renderStates"]:
				self.tw_renderStates.addItem(state)

		if "submitrender" in data:
			self.gb_submit.setChecked(eval(data["submitrender"]))
		if "rjmanager" in data:
			idx = self.cb_manager.findText(data["rjmanager"])
			if idx != -1:
				self.cb_manager.setCurrentIndex(idx)
			self.managerChanged(True)
		if "rjprio" in data:
			self.sp_rjPrio.setValue(int(data["rjprio"]))
		if "rjframespertask" in data:
			self.sp_rjFramesPerTask.setValue(int(data["rjframespertask"]))
		if "rjtimeout" in data:
			self.sp_rjTimeout.setValue(int(data["rjtimeout"]))
		if "rjsuspended" in data:
			self.chb_rjSuspended.setChecked(eval(data["rjsuspended"]))
		if "osdependencies" in data:
			self.chb_osDependencies.setChecked(eval(data["osdependencies"]))
		if "osupload" in data:
			self.chb_osUpload.setChecked(eval(data["osupload"]))
		if "ospassets" in data:
			self.chb_osPAssets.setChecked(eval(data["ospassets"]))
		if "osslaves" in data:
			self.e_osSlaves.setText(data["osslaves"])
		if "dlconcurrent" in data:
			self.sp_dlConcurrentTasks.setValue(int(data["dlconcurrent"]))
		if "dlgpupt" in data:
			self.sp_dlGPUpt.setValue(int(data["dlgpupt"]))
			self.gpuPtChanged()
		if "dlgpudevices" in data:
			self.le_dlGPUdevices.setText(data["dlgpudevices"])
			self.gpuDevicesChanged()
		# if "lastexportpath" in data:
		# 	lePath = self.core.fixPath(data["lastexportpath"])
		# 	self.l_pathLast.setText(lePath)
		# 	self.l_pathLast.setToolTip(lePath)
		if "stateenabled" in data:
			if type(data["stateenabled"]) == int:
				self.state.setCheckState(
					0, Qt.CheckState(data["stateenabled"]),
				)
		# if "stateenabled" in data:
		# 	self.chb_upVersion.setChecked(eval(data["upversion"]))

		# Item Color #
		self.state.setBackground(0, QColor("#429933"))

		self.core.callback("onStateSettingsLoaded", self, data)


	@err_catcher(name=__name__)
	def connectEvents(self):
		self.e_name.textChanged.connect(self.nameChanged)
		self.e_name.editingFinished.connect(self.stateManager.saveStatesToScene)

		self.chb_overrideFrameRange.toggled.connect(lambda: self.updateUi())
		self.chb_overrideMaster.toggled.connect(lambda: self.updateUi())
		self.chb_overrideLocation.toggled.connect(lambda: self.updateUi())
		self.chb_overrideScaling.toggled.connect(lambda: self.updateUi())
		self.chb_overrideQuality.toggled.connect(lambda: self.updateUi())
		self.chb_overrideRenderMB.toggled.connect(lambda: self.updateUi())
		self.chb_overrideProxy.toggled.connect(lambda: self.updateUi())
		self.cb_rangeType.activated.connect(self.rangeTypeChanged)
		self.sp_rangeStart.editingFinished.connect(self.startChanged)
		self.sp_rangeEnd.editingFinished.connect(self.endChanged)
		self.le_frameExpression.textChanged.connect(self.frameExpressionChanged)
		self.le_frameExpression.editingFinished.connect(
			self.stateManager.saveStatesToScene
			)
		self.le_frameExpression.setMouseTracking(True)
		self.le_frameExpression.origMoveEvent = self.le_frameExpression.mouseMoveEvent
		self.le_frameExpression.mouseMoveEvent = self.exprMoveEvent
		self.le_frameExpression.leaveEvent = self.exprLeaveEvent
		self.le_frameExpression.focusOutEvent = self.exprFocusOutEvent

		self.cb_master.activated.connect(self.stateManager.saveStatesToScene)
		self.cb_outPath.activated.connect(self.stateManager.saveStatesToScene)

		self.b_addRenderState.clicked.connect(self.addRenderState)
		self.gb_submit.toggled.connect(self.rjToggled)
		self.cb_manager.activated.connect(self.managerChanged)
		self.sp_rjPrio.editingFinished.connect(self.stateManager.saveStatesToScene)
		self.sp_rjFramesPerTask.editingFinished.connect(
			self.stateManager.saveStatesToScene
			)
		self.sp_rjTimeout.editingFinished.connect(self.stateManager.saveStatesToScene)
		self.chb_rjSuspended.stateChanged.connect(self.stateManager.saveStatesToScene)
		self.chb_osDependencies.stateChanged.connect(
			self.stateManager.saveStatesToScene
			)
		self.chb_osUpload.stateChanged.connect(self.stateManager.saveStatesToScene)
		self.chb_osPAssets.stateChanged.connect(self.stateManager.saveStatesToScene)
		self.e_osSlaves.editingFinished.connect(self.stateManager.saveStatesToScene)
		self.b_osSlaves.clicked.connect(self.openSlaves)
		self.sp_dlConcurrentTasks.editingFinished.connect(
			self.stateManager.saveStatesToScene
			)
		self.sp_dlGPUpt.editingFinished.connect(self.gpuPtChanged)
		self.le_dlGPUdevices.editingFinished.connect(self.gpuDevicesChanged)

		#	Adds RCL menu to RenderStates list
		self.tw_renderStates.setContextMenuPolicy(Qt.CustomContextMenu)
		self.tw_renderStates.customContextMenuRequested.connect(self.renderStatesRclMenu)



		# self.treeWidget.itemSelectionChanged.connect(self.onTreeItemSelectionChanged)
		# self.chb_upVersion.stateChanged.connect(self.stateManager.saveStatesToScene)					#	TODO	LOOK AT SUBMIT LAST VERSION




	# @err_catcher(name=__name__)															#	TODO	NEEDED??
	# def selectContextClicked(self, state=None):
	# 	self.dlg_entity = self.stateManager.entityDlg(self)
	# 	data = self.getCurrentContext()
	# 	self.dlg_entity.w_entities.navigate(data)
	# 	self.dlg_entity.entitySelected.connect(lambda x: self.setCustomContext(x))
	# 	self.dlg_entity.show()

	# @err_catcher(name=__name__)															#	TODO	NEEDED??
	# def setCustomContext(self, context):
	# 	self.customContext = context
	# 	self.refreshContext()
	# 	self.stateManager.saveStatesToScene()

	# @err_catcher(name=__name__)															#	TODO	NEEDED??
	# def onContextTypeChanged(self, state):
	# 	self.refreshContext()
	# 	self.stateManager.saveStatesToScene()

	@err_catcher(name=__name__)
	def rangeTypeChanged(self, state):
		self.updateUi()
		self.stateManager.saveStatesToScene()

	@err_catcher(name=__name__)
	def startChanged(self):
		if self.sp_rangeStart.value() > self.sp_rangeEnd.value():
			self.sp_rangeEnd.setValue(self.sp_rangeStart.value())

		self.stateManager.saveStatesToScene()

	@err_catcher(name=__name__)
	def endChanged(self):
		if self.sp_rangeEnd.value() < self.sp_rangeStart.value():
			self.sp_rangeStart.setValue(self.sp_rangeEnd.value())

		self.stateManager.saveStatesToScene()

	@err_catcher(name=__name__)
	def frameExpressionChanged(self, text=None):
		if not hasattr(self, "expressionWinLabel"):
			return

		frames = self.core.resolveFrameExpression(self.le_frameExpression.text())
		if len(frames) > 1000:
			frames = frames[:1000]
			frames.append("...")

		for idx in range(int(len(frames) / 30.0)):
			frames.insert((idx+1)*30, "\n")

		frameStr = ",".join([str(x) for x in frames]) or "invalid expression"
		self.expressionWinLabel.setText(frameStr)
		self.expressionWin.resize(1, 1)

	@err_catcher(name=__name__)
	def exprMoveEvent(self, event):
		self.showExpressionWin(event)
		if hasattr(self, "expressionWin") and self.expressionWin.isVisible():
			self.expressionWin.move(
				QCursor.pos().x() + 20, QCursor.pos().y() - self.expressionWin.height()
			)
		self.le_frameExpression.origMoveEvent(event)

	@err_catcher(name=__name__)
	def showExpressionWin(self, event):
		if not hasattr(self, "expressionWin") or not self.expressionWin.isVisible():
			if hasattr(self, "expressionWin"):
				self.expressionWin.close()

			self.expressionWin = QFrame()
			ss = getattr(self.fusionFuncs, "getFrameStyleSheet", lambda x: "")(self)
			self.expressionWin.setStyleSheet(
				ss + """ .QFrame{ border: 2px solid rgb(100,100,100);} """
			)

			self.core.parentWindow(self.expressionWin)
			winwidth = 10
			winheight = 10
			VBox = QVBoxLayout()
			frames = self.core.resolveFrameExpression(self.le_frameExpression.text())
			if len(frames) > 1000:
				frames = frames[:1000]
				frames.append("...")

			for idx in range(int(len(frames) / 30.0)):
				frames.insert((idx+1)*30, "\n")

			frameStr = ",".join([str(x) for x in frames]) or "invalid expression"
			self.expressionWinLabel = QLabel(frameStr)
			VBox.addWidget(self.expressionWinLabel)
			self.expressionWin.setLayout(VBox)
			self.expressionWin.setWindowFlags(
				Qt.FramelessWindowHint  # hides the window controls
				| Qt.WindowStaysOnTopHint  # forces window to top... maybe
				| Qt.SplashScreen  # this one hides it from the task bar!
			)

			self.expressionWin.setGeometry(0, 0, winwidth, winheight)
			self.expressionWin.move(QCursor.pos().x() + 20, QCursor.pos().y())
			self.expressionWin.setAttribute(Qt.WA_ShowWithoutActivating)
			self.expressionWin.show()

	@err_catcher(name=__name__)
	def exprLeaveEvent(self, event):
		if hasattr(self, "expressionWin") and self.expressionWin.isVisible():
			self.expressionWin.close()

	@err_catcher(name=__name__)
	def exprFocusOutEvent(self, event):
		if hasattr(self, "expressionWin") and self.expressionWin.isVisible():
			self.expressionWin.close()

	@err_catcher(name=__name__)
	def nameChanged(self, text):
		text = self.e_name.text()
		context = {}
		context["identifier"] = self.getTaskname() or "None"
		num = 0
		try:
			if "{#}" in text:
				while True:
					context["#"] = num or ""
					name = text.format(**context)
					for state in self.stateManager.states:
						if state.ui.listType != "Export":
							continue

						if state is self.state:
							continue

						if state.text(0) == name:
							num += 1
							break
					else:
						break
			else:
				name = text.format(**context)
		except Exception:
			name = text
		name = "RENDERGROUP - " + name

		if self.state.text(0).endswith(" - disabled"):
			name += " - disabled"

		self.state.setText(0, name)


	# @err_catcher(name=__name__)															#	TODO	NEEDED??
	# def getFormat(self):
	# 	self.cb_format.currentText()

	# @err_catcher(name=__name__)															#	TODO	NEEDED??
	# def setFormat(self, fmt):
	# 	idx = self.cb_format.findText(fmt)
	# 	if idx != -1:
	# 		self.cb_format.setCurrentIndex(idx)
	# 		self.stateManager.saveStatesToScene()
	# 		return True

	# 	return False

	@err_catcher(name=__name__)
	def getContextType(self):
		contextType = self.cb_context.currentText()
		return contextType

	@err_catcher(name=__name__)
	def setContextType(self, contextType):
		idx = self.cb_context.findText(contextType)
		if idx != -1:
			self.cb_context.setCurrentIndex(idx)
			self.refreshContext()
			return True

		return False

	@err_catcher(name=__name__)															#	TODO	NEEDED??
	def getTaskname(self):
		# taskName = self.l_taskName.text()
		# return taskName
		pass


	@err_catcher(name=__name__)															#	TODO	NEEDED??
	def setTaskname(self, taskname):
		# self.l_taskName.setText(taskname)
		# self.setTaskWarn(not bool(taskname))
		# self.updateUi()

		pass


	# @err_catcher(name=__name__)															#	TODO	NEEDED??
	# def getSortKey(self):
	# 	return self.getTaskname()


	@err_catcher(name=__name__)
	def changeTask(self):
		from PrismUtils import PrismWidgets
		#	Sets up popup window
		self.nameWin = PrismWidgets.CreateItem(
			startText=self.getTaskname(),
			showTasks=True,
			taskType="2d",
			core=self.core,
			)

		self.core.parentWindow(self.nameWin)
		self.nameWin.setWindowTitle("Change Identifier")
		self.nameWin.l_item.setText("Identifier:")
		self.nameWin.buttonBox.buttons()[0].setText("Ok")
		self.nameWin.e_item.selectAll()
		result = self.nameWin.exec_()

		if result == 1:
			#	Checks if entered name is Fusion legal
			isLegal, errorStr = self.getFusLegalName(self.nameWin.e_item.text(), check=True)
			if not isLegal:
				self.core.popup(errorStr)
				return

			self.setTaskname(self.nameWin.e_item.text())
			self.nameChanged(self.e_name.text())
			self.stateManager.saveStatesToScene()
			
			# self.stateManager.tw_export.itemChanged.connect(self.sm_handle_item_changed)		#	TODO	THIS IS IN ImageRender
																								#			BUT NOT HERE.  IS THAT CORRECT?


	# #	Fusion has strict naming for nodes.  You can only use:															#	TODO	NEEDED??
	# #	Alphanumeric characters:  a-z, A-Z, 0-9,
	# #	Do not use any spaces,
	# #	Do not use special charactors,
	# #	Node name cannot start with a number.
	# @err_catcher(name=__name__)
	# def getFusLegalName(self, origName, check=False):						#	ADDED
	# 	# Check if the name starts with a number
	# 	if origName[0].isdigit():
	# 		if check:
	# 			return False, "Name cannot start with a number."
			
	# 		return "Error: Name cannot start with a number."

	# 	# Check if the name contains only allowed characters
	# 	if not re.match(r'^[A-Za-z0-9_\- .]*$', origName):
	# 		if check:
	# 			return False, "Name contains invalid characters."
			
	# 		return "Error: Name contains invalid characters."

	# 	newName = origName.replace(' ', '_')									#	EDITED
	# 	newName = newName.replace('.', '_')
	# 	newName = newName.replace('-', '_')

	# 	if check:
	# 		return True, ""
		
	# 	return newName


	@err_catcher(name=__name__)
	def changeTaskAuto(self, identifier):
		self.setTaskname(identifier)
		self.nameChanged(identifier)
		self.stateManager.saveStatesToScene()


	#################################
	#								#	
	####### RENDER NODE STUFF #######
	#								#
	#################################
	@err_catcher(name=__name__)
	def getItemNamesRecursive(self, item, itemNames):
		# Add the name of the current item
		name = item.text(0)
		itemNames.add(name)

		# Recursively process child items
		for i in range(item.childCount()):
			child_item = item.child(i)
			self.getItemNamesRecursive(child_item, itemNames)

	@err_catcher(name=__name__)
	def getItemNames(self):
		itemNames = set()

		# Iterate through the top-level items in the QTreeWidget
		for i in range(self.treeWidget.topLevelItemCount()):
			top_level_item = self.treeWidget.topLevelItem(i)
			self.getItemNamesRecursive(top_level_item, itemNames)

		return itemNames 
	


	@err_catcher(name=__name__)
	def getRangeType(self):
		return self.cb_rangeType.currentText()

	@err_catcher(name=__name__)
	def setRangeType(self, rangeType):
		idx = self.cb_rangeType.findText(rangeType)
		if idx != -1:
			self.cb_rangeType.setCurrentIndex(idx)
			self.updateRange()
			return True

		return False

	# @err_catcher(name=__name__)
	# def getResolution(self, resolution):															#	TODO	NEEDED??
	# 	res = None
	# 	if resolution == "Get from rendersettings":
	# 		if hasattr(self.fusionFuncs, "getResolution"):
	# 			res = self.fusionFuncs.getResolution()
	# 		else:
	# 			res = [1920, 1080]
	# 	elif resolution.startswith("Project ("):
	# 		res = resolution[9:-1].split("x")
	# 		res = [int(r) for r in res]
	# 	else:
	# 		try:
	# 			pwidth = int(resolution.split("x")[0])
	# 			pheight = int(resolution.split("x")[1])
	# 			res = [pwidth, pheight]
	# 		except:
	# 			res = getattr(
	# 				self.fusionFuncs, "evaluateResolution", lambda x: None
	# 			)(resolution)

	# 	return res

	@err_catcher(name=__name__)
	def getMasterVersion(self):
		return self.cb_master.currentText()

	@err_catcher(name=__name__)
	def setMasterVersion(self, master):
		idx = self.cb_master.findText(master)
		if idx != -1:
			self.cb_master.setCurrentIndex(idx)
			self.stateManager.saveStatesToScene()
			return True

		return False

	@err_catcher(name=__name__)
	def getLocation(self):
		return self.cb_outPath.currentText()

	@err_catcher(name=__name__)
	def setLocation(self, location):
		idx = self.cb_outPath.findText(location)
		if idx != -1:
			self.cb_outPath.setCurrentIndex(idx)
			self.stateManager.saveStatesToScene()
			return True

		return False


	@err_catcher(name=__name__)
	def renderStatesRclMenu(self, pos):
		# Find the item at the clicked position
		clickedItem = self.tw_renderStates.itemAt(pos)
		
		# Create the rcl menu
		menu = QMenu(self.tw_renderStates)
		
		# If clicked on a State
		if clickedItem:
			removeAct = QAction("Remove State", self.tw_renderStates)
			menu.addAction(removeAct)
			removeAct.triggered.connect(lambda: self.removeState(clickedItem))
		#	If clicked on empty area of list
		else:
			removeAllAct = QAction("Remove All States", self.tw_renderStates)
			menu.addAction(removeAllAct)
			removeAllAct.triggered.connect(self.removeAllStates)
		
		# Show the menu at the cursor position
		menu.exec_(self.tw_renderStates.viewport().mapToGlobal(pos))


	@err_catcher(name=__name__)
	def removeState(self, item):
		#	Removes item from list
		row = self.tw_renderStates.row(item)
		self.tw_renderStates.takeItem(row)
		self.stateManager.saveStatesToScene()


	@err_catcher(name=__name__)
	def removeAllStates(self):
		#	Clears list
		self.tw_renderStates.clear()
		self.stateManager.saveStatesToScene()



	@err_catcher(name=__name__)
	def addRenderState(self):
		import ItemList

		allStates = self.getItemNames()
		renderStates = [state for state in allStates if state.startswith("ImageRender")]

		self.selStatesUI = ItemList.ItemList(core=self.core)
		self.selStatesUI.setWindowTitle("Select Render States")
		self.core.parentWindow(self.selStatesUI)
		self.selStatesUI.tw_steps.doubleClicked.connect(self.selStatesUI.accept)
		self.selStatesUI.tw_steps.horizontalHeaderItem(0).setText("Name")
		self.selStatesUI.tw_steps.setColumnHidden(1, True)
		for i in sorted(renderStates, key=lambda s: s.lower()):
			rc = self.selStatesUI.tw_steps.rowCount()
			self.selStatesUI.tw_steps.insertRow(rc)
			item1 = QTableWidgetItem(i)
			self.selStatesUI.tw_steps.setItem(rc, 0, item1)

		result = self.selStatesUI.exec_()

		if result != 1:
			return False
		
		# Clear existing items
		self.tw_renderStates.clear()

		# Add selected items to the States list
		for i in self.selStatesUI.tw_steps.selectedItems():
			if i.column() == 0:  # Ensure we are working with the correct column
				list_item = QListWidgetItem(i.text())  # Create a list widget item with the selected text
				self.tw_renderStates.addItem(list_item)  # Add the item

		self.updateUi()
		self.stateManager.saveStatesToScene()




	@err_catcher(name=__name__)
	def updateUi(self):
		self.w_context.setHidden(not self.allowCustomContext)
		self.refreshContext()

		if not self.core.mediaProducts.getUseMaster():
			self.w_master.setVisible(False)
		else:
			self.updateMasterOvr()

		self.refreshSubmitUi()
		self.nameChanged(self.e_name.text())

		self.updateRange()
		self.updateLocationOvr()
		self.updateScalingOvr()
		self.updateHiQOvr()
		self.updateMbOvr()
		self.updateProxyOvr()

		self.stateManager.saveStatesToScene()

		return True
	

	@err_catcher(name=__name__)
	def refreshContext(self):
		context = self.getCurrentContext()
		contextStr = self.getContextStrFromEntity(context)
		self.l_context.setText(contextStr)

	@err_catcher(name=__name__)
	def getCurrentContext(self):
		context = None
		if self.allowCustomContext:
			ctype = self.getContextType()
			if ctype == "Custom":
				context = self.customContext

		if not context:
			fileName = self.core.getCurrentFileName()
			context = self.core.getScenefileData(fileName)
		
		if "username" in context:
			del context["username"]

		if "user" in context:
			del context["user"]

		return context

	@err_catcher(name=__name__)
	def refreshSubmitUi(self):
		if not self.gb_submit.isHidden():
			if not self.gb_submit.isCheckable():
				return

			submitChecked = self.gb_submit.isChecked()
			for idx in reversed(range(self.gb_submit.layout().count())):
				self.gb_submit.layout().itemAt(idx).widget().setHidden(not submitChecked)

			if submitChecked:
				self.core.plugins.getRenderfarmPlugin(self.cb_manager.currentText()).sm_render_updateUI(self)
		

	@err_catcher(name=__name__)
	def updateFrameRangeOvr(self):
		isEnabled = self.chb_overrideFrameRange.isChecked()

		# UI elements to update
		uiElements = [
			self.cb_rangeType,
			self.w_frameRangeValues,
			self.w_frameExpression
		]
		
		# Iterate over each UI element and set its hidden state
		for element in uiElements:
			element.setHidden(not isEnabled)


	@err_catcher(name=__name__)
	def updateMasterOvr(self):
		isEnabled = self.chb_overrideMaster.isChecked()

		# UI elements to update
		uiElements = [
			self.cb_master
		]
		
		# Iterate over each UI element and set its hidden state
		for element in uiElements:
			element.setHidden(not isEnabled)


	@err_catcher(name=__name__)
	def updateLocationOvr(self):
		isEnabled = self.chb_overrideLocation.isChecked()

		if self.useLocation:
			# UI elements to update
			uiElements = [
				self.cb_outPath
			]
			
			# Iterate over each UI element and set its hidden state
			for element in uiElements:
				element.setHidden(not isEnabled)


	@err_catcher(name=__name__)
	def updateScalingOvr(self):
		isEnabled = self.chb_overrideScaling.isChecked()

		# UI elements to update
		uiElements = [
			self.cb_renderScaling
		]
		
		# Iterate over each UI element and set its hidden state
		for element in uiElements:
			element.setHidden(not isEnabled)


	@err_catcher(name=__name__)
	def updateHiQOvr(self):
		isEnabled = self.chb_overrideQuality.isChecked()

		# UI elements to update
		uiElements = [
			self.cb_renderQuality
		]
		
		# Iterate over each UI element and set its hidden state
		for element in uiElements:
			element.setHidden(not isEnabled)


	@err_catcher(name=__name__)
	def updateMbOvr(self):
		isEnabled = self.chb_overrideRenderMB.isChecked()

		# UI elements to update
		uiElements = [
			self.cb_renderMB
		]
		
		# Iterate over each UI element and set its hidden state
		for element in uiElements:
			element.setHidden(not isEnabled)


	@err_catcher(name=__name__)
	def updateProxyOvr(self):
		isEnabled = self.chb_overrideProxy.isChecked()

		# UI elements to update
		uiElements = [
			self.cb_renderProxy
		]
		
		# Iterate over each UI element and set its hidden state
		for element in uiElements:
			element.setHidden(not isEnabled)


	@err_catcher(name=__name__)
	def updateRange(self):
		rangeType = self.cb_rangeType.currentText()
		isCustom = rangeType == "Custom"
		isExp = rangeType == "Expression"
		self.l_rangeStart.setVisible(not isCustom and not isExp)
		self.l_rangeEnd.setVisible(not isCustom and not isExp)
		self.sp_rangeStart.setVisible(isCustom)
		self.sp_rangeEnd.setVisible(isCustom)
		self.w_frameRangeValues.setVisible(not isExp)
		self.w_frameExpression.setVisible(isExp)

		if not isCustom and not isExp:
			frange = self.getFrameRange(rangeType=rangeType)
			start = str(int(frange[0])) if frange[0] is not None else "-"
			end = str(int(frange[1])) if frange[1] is not None else "-"
			self.l_rangeStart.setText(start)
			self.l_rangeEnd.setText(end)

		self.updateFrameRangeOvr()


	@err_catcher(name=__name__)
	def getFrameRange(self, rangeType):
		startFrame = None
		endFrame = None
		if rangeType == "Scene":
			if hasattr(self.fusionFuncs, "getFrameRange"):
				startFrame, endFrame = self.fusionFuncs.getFrameRange(self)
				startFrame = int(startFrame)
				endFrame = int(endFrame)
			else:
				startFrame = 1001
				endFrame = 1100
		elif rangeType == "Shot":
			context = self.getCurrentContext()
			if context.get("type") == "shot" and "sequence" in context:
				frange = self.core.entities.getShotRange(context)
				if frange:
					startFrame, endFrame = frange
		elif rangeType == "Single Frame":
			if hasattr(self.fusionFuncs, "getCurrentFrame"):
				startFrame = int(self.fusionFuncs.getCurrentFrame())
			else:
				startFrame = 1001
		elif rangeType == "Custom":
			startFrame = self.sp_rangeStart.value()
			endFrame = self.sp_rangeEnd.value()
		elif rangeType == "Expression":
			return self.core.resolveFrameExpression(self.le_frameExpression.text())

		if startFrame == "":
			startFrame = None

		if endFrame == "":
			endFrame = None

		if startFrame is not None:
			startFrame = int(startFrame)

		if endFrame is not None:
			endFrame = int(endFrame)

		return startFrame, endFrame

	@err_catcher(name=__name__)
	def openSlaves(self):
		if eval(os.getenv("PRISM_DEBUG", "False")):
			try:
				del sys.modules["SlaveAssignment"]
			except:
				pass

		import SlaveAssignment

		self.sa = SlaveAssignment.SlaveAssignment(
			core=self.core, curSlaves=self.e_osSlaves.text()
		)
		result = self.sa.exec_()

		if result == 1:
			selSlaves = ""
			if self.sa.rb_exclude.isChecked():
				selSlaves = "exclude "
			if self.sa.rb_all.isChecked():
				selSlaves += "All"
			elif self.sa.rb_group.isChecked():
				selSlaves += "groups: "
				for i in self.sa.activeGroups:
					selSlaves += i + ", "

				if selSlaves.endswith(", "):
					selSlaves = selSlaves[:-2]

			elif self.sa.rb_custom.isChecked():
				slavesList = [x.text() for x in self.sa.lw_slaves.selectedItems()]
				for i in slavesList:
					selSlaves += i + ", "

				if selSlaves.endswith(", "):
					selSlaves = selSlaves[:-2]

			self.e_osSlaves.setText(selSlaves)
			self.stateManager.saveStatesToScene()

	@err_catcher(name=__name__)
	def gpuPtChanged(self):
		self.w_dlGPUdevices.setEnabled(self.sp_dlGPUpt.value() == 0)
		self.stateManager.saveStatesToScene()

	@err_catcher(name=__name__)
	def gpuDevicesChanged(self):
		self.w_dlGPUpt.setEnabled(self.le_dlGPUdevices.text() == "")
		self.stateManager.saveStatesToScene()

	# @err_catcher(name=__name__)
	# def showPasses(self):															#	TODO	NEEDED??
	# 	steps = getattr(
	# 		self.fusionFuncs, "sm_render_getRenderPasses", lambda x: None
	# 	)(self)

	# 	if steps is None or len(steps) == 0:
	# 		return False

	# 	if self.core.isStr(steps):
	# 		steps = eval(steps)

	# 	if eval(os.getenv("PRISM_DEBUG", "False")):
	# 		try:
	# 			del sys.modules["ItemList"]
	# 		except:
	# 			pass

	# 	import ItemList

	# 	self.il = ItemList.ItemList(core=self.core)
	# 	self.il.setWindowTitle("Select Passes")
	# 	self.core.parentWindow(self.il)
	# 	self.il.tw_steps.doubleClicked.connect(self.il.accept)
	# 	self.il.tw_steps.horizontalHeaderItem(0).setText("Name")
	# 	self.il.tw_steps.setColumnHidden(1, True)
	# 	for i in sorted(steps, key=lambda s: s.lower()):
	# 		rc = self.il.tw_steps.rowCount()
	# 		self.il.tw_steps.insertRow(rc)
	# 		item1 = QTableWidgetItem(i)
	# 		self.il.tw_steps.setItem(rc, 0, item1)

	# 	result = self.il.exec_()

	# 	if result != 1:
	# 		return False

	# 	for i in self.il.tw_steps.selectedItems():
	# 		if i.column() == 0:
	# 			self.fusionFuncs.sm_render_addRenderPass(
	# 				self, passName=i.text(), steps=steps
	# 			)

	# 	self.updateUi()
	# 	self.stateManager.saveStatesToScene()

	# @err_catcher(name=__name__)
	# def rclickPasses(self, pos):
	# 	if self.lw_passes.currentItem() is None or not getattr(
	# 		self.fusionFuncs, "canDeleteRenderPasses", True
	# 	):
	# 		return

	# 	rcmenu = QMenu()

	# 	delAct = QAction("Delete", self)
	# 	delAct.triggered.connect(self.deleteAOVs)
	# 	rcmenu.addAction(delAct)

	# 	rcmenu.exec_(QCursor.pos())

	# @err_catcher(name=__name__)
	# def deleteAOVs(self):
	# 	items = self.lw_passes.selectedItems()
	# 	for i in items:
	# 		self.fusionFuncs.removeAOV(i.text())
	# 	self.updateUi()

	@err_catcher(name=__name__)
	def rjToggled(self, checked):
		self.refreshSubmitUi()
		self.stateManager.saveStatesToScene()

	@err_catcher(name=__name__)
	def managerChanged(self, text=None):
		plugin = self.core.plugins.getRenderfarmPlugin(self.cb_manager.currentText())
		if plugin:
			plugin.sm_render_managerChanged(self)

		self.stateManager.saveStatesToScene()

	@err_catcher(name=__name__)
	def getContextStrFromEntity(self, entity):
		if not entity:
			return ""

		entityType = entity.get("type", "")
		if entityType == "asset":
			entityName = entity.get("asset_path").replace("\\", "/")
		elif entityType == "shot":
			entityName = self.core.entities.getShotName(entity)
		else:
			return ""

		context = "%s - %s" % (entityType.capitalize(), entityName)
		return context

	@err_catcher(name=__name__)
	def preExecuteState(self):
		warnings = []

		self.updateUi()

		# if self.tasknameRequired and not self.getTaskname():						#	TODO Change to looking at States from list
		# 	warnings.append(["No identifier is given.", "", 3])

		#	TODO	Get StateNames from list

		#	TODO	Get Saver from each State

		#	TODO	Save current context

		#	TODO	Config Savers based on selected States
			#	Config Savers mute state (unmute all in list, and mute all not in list)	
			# 	Update selected Savers versions / names
			#	

		#	TODO 	apply all overrides to context

		#	TODO	Maybe save .comp to temp file

		#	TODO	Render comp

		#	TODO 	Return comp to original state.


		rangeType = self.cb_rangeType.currentText()
		frames = self.getFrameRange(rangeType)
		if rangeType != "Expression":
			frames = frames[0]

		if frames is None or frames == []:
			warnings.append(["Framerange is invalid.", "", 3])

		if not self.gb_submit.isHidden() and self.gb_submit.isChecked():
			plugin = self.core.plugins.getRenderfarmPlugin(self.cb_manager.currentText())
			warnings += plugin.sm_render_preExecute(self)

		warnings += self.fusionFuncs.sm_render_preExecute(self)

		return [self.state.text(0), warnings]

	#################################################
	@err_catcher(name=__name__)
	def submitCheckPaths(self):
		self.fusionFuncs.sm_render_CheckSubmittedPaths()

	@err_catcher(name=__name__)
	def setFarmedRange(self, startFrame, endFrame):
		self.fusionFuncs.setFrameRange(self, startFrame, endFrame)

	# @err_catcher(name=__name__)																#	TODO	NEEDED??
	# def upSubmittedSaversVersions(self, parent):
	# 	# Before Submitting, change version of elegible Savers.
	# 	sm = parent
	# 	fileName = self.core.getCurrentFileName()
	# 	context = self.getCurrentContext()
	# 	for state in sm.states:
	# 		stateui = state.ui
	# 		if stateui.className == "ImageRender":
	# 			if not stateui.b_setRendernode.text() == "SetRenderNode" and state.checkState(0) == Qt.Checked:
	# 				#Get Output, Update UI and set infoFile.				
	# 				stateui.executeState(parent=parent, outOnly=True)


	# @err_catcher(name=__name__)															#	TODO	NEEDED??
	# def getOutputName(self, useVersion="next", stateui = None):
	# 	if stateui == None:
	# 		stateui = self
	# 	if stateui.tasknameRequired and not stateui.getTaskname():
	# 		return

	# 	task = stateui.getTaskname()
	# 	extension = stateui.cb_format.currentText()
	# 	context = stateui.getCurrentContext()
	# 	framePadding = ""

	# 	if "type" not in context:
	# 		return

	# 	singleFrame = stateui.cb_rangeType.currentText() == "Single Frame"
	# 	location = stateui.cb_outPath.currentText()
	# 	outputPathData = stateui.core.mediaProducts.generateMediaProductPath(
	# 		entity=context,
	# 		task=task,
	# 		extension=extension,
	# 		framePadding=framePadding,
	# 		comment=self.stateManager.publishComment,
	# 		version=useVersion if useVersion != "next" else None,
	# 		location=location,
	# 		singleFrame=singleFrame,
	# 		returnDetails=True,
	# 		mediaType=self.mediaType,
	# 	)

	# 	outputFolder = os.path.dirname(outputPathData["path"])
	# 	hVersion = outputPathData["version"]

	# 	return outputPathData["path"], outputFolder, hVersion


	# @err_catcher(name=__name__)
	# def configureRenderNode(self, nodeName, useVersion="next", stateUI=None):															#	TODO	NEEDED??
	# 	if stateUI is None:
	# 		stateUI = self
	# 	if stateUI.tasknameRequired and not stateUI.getTaskname():
	# 		return

	# 	outputName, _, _ = self.getOutputName(useVersion=useVersion)

	# 	extension = stateUI.cb_format.currentText()
	# 	fuseName = None

	# 	try:
	# 		for fmt in self.outputFormats:
	# 			if fmt["extension"] == extension.lower():
	# 				fuseName = fmt["fuseName"]
	# 				break

	# 		self.fusionFuncs.configureRenderNode(nodeName, outputName, fuseName)
	# 		self.stateManager.saveStatesToScene()

	# 	except:
	# 		print("ERROR: Unable to config Saver")


	@err_catcher(name=__name__)
	def executeState(self, parent, useVersion="next", outOnly=False):
		# if render manager plugins were detected.
		if self.cb_manager.count() > 0:
			hasRenderManger = True

		sumbitToFarm = self.gb_submit.isChecked()

		if sumbitToFarm and not hasRenderManger:
			return [self.state.text(0) + " - error - There are no Render Manager plugins installed"]

		if not sumbitToFarm:



			result = self.fusionFuncs.sm_render_startLocalGroupRender(self, outputPathOnly=False, outputName="", rSettings="")

			
		# rangeType = self.cb_rangeType.currentText()
		# frames = self.getFrameRange(rangeType)
		# if rangeType != "Expression":
		# 	startFrame = frames[0]
		# 	endFrame = frames[1]
		# else:
		# 	startFrame = None
		# 	endFrame = None

		# if frames is None or frames == [] or frames[0] is None:
		# 	return [self.state.text(0) + ": error - Framerange is invalid"]

		# if rangeType == "Single Frame":
		# 	endFrame = startFrame

		# updateMaster = True
		# fileName = self.core.getCurrentFileName()
		# context = self.getCurrentContext()
		# # if not self.renderingStarted:
		# # if self.tasknameRequired and not self.getTaskname():										#	TODO  Look at States from list
		# # 	return [
		# # 		self.state.text(0)
		# # 		+ ": error - no identifier is given. Skipped the activation of this state."
		# # 	]
		
		# outputName, outputPath, hVersion = self.getOutputName(useVersion=useVersion)

		# outLength = len(outputPath)
		# if platform.system() == "Windows" and os.getenv("PRISM_IGNORE_PATH_LENGTH") != "1" and outLength > 255:
		# 	return [
		# 		self.state.text(0)
		# 		+ " - error - The outputpath is longer than 255 characters (%s), which is not supported on Windows. Please shorten the outputpath by changing the comment, taskname or projectpath."
		# 		% outLength
		# 	]

		# if not os.path.exists(os.path.dirname(outputPath)):
		# 	os.makedirs(os.path.dirname(outputPath))

		# details = context.copy()
		# if "filename" in details:
		# 	del details["filename"]

		# if "extension" in details:
		# 	del details["extension"]

		# details["version"] = hVersion
		# details["sourceScene"] = fileName
		# details["identifier"] = self.getTaskname()
		# details["comment"] = self.stateManager.publishComment

		# if self.mediaType == "2drenders":
		# 	infopath = os.path.dirname(outputPath)
		# else:
		# 	infopath = outputPath

		# self.core.saveVersionInfo(
		# 	filepath=infopath, details=details
		# )

		# self.l_pathLast.setText(outputName)
		# self.l_pathLast.setToolTip(outputName)
		# self.stateManager.saveStatesToScene()

		# rSettings = {
		# 	"outputName": outputName,
		# 	"startFrame": startFrame,
		# 	"endFrame": endFrame,
		# 	"frames": frames,
		# 	"rangeType": rangeType,
		# }


		# self.fusionFuncs.sm_render_preSubmit(self, rSettings)

		# kwargs = {
		# 	"state": self,
		# 	"scenefile": fileName,
		# 	"settings": rSettings,
		# }

		# result = self.core.callback("preRender", **kwargs)
		# for res in result:
		# 	if isinstance(res, dict) and res.get("cancel", False):
		# 		return [
		# 			self.state.text(0)
		# 			+ " - error - %s" % res.get("details", "preRender hook returned False")
		# 		]

		# if not os.path.exists(os.path.dirname(rSettings["outputName"])):
		# 	os.makedirs(os.path.dirname(rSettings["outputName"]))

		# ### SUBMIT TO FARM ###

		# # self.core.saveScene(versionUp=False, prismReq=False)				#	DO WE WANT THIS HARDCODED or USE SM PREF
		# # # If Render on the farm is selected
		# # if not self.gb_submit.isHidden():
		# # 	# get the Frame Range.
		# # 	self.setFarmedRange(startFrame, endFrame)
		# # 	# get new versions for all savers.
		# # 	# if self.chb_upVersion.isChecked():
		# # 	# 	self.upSubmittedSaversVersions(self.stateManager)

		# # 	if 0 == 1:
		# # 		pass												#	TODO ???

		# # 	else:
		# # 		msg = ('Are you sure you want to execute this state as a previous version?\nThis may overwrite existing files.')
		# # 		executeprev = self.core.popupQuestion(
		# # 			msg,
		# # 			title="Warning",
		# # 			buttons=["Continue", "Cancel"],
		# # 			icon=QMessageBox.Warning,
		# # 			escapeButton="Cancel",
		# # 		)
		# # 		if executeprev == "Cancel":
		# # 			return [self.state.text(0) + " - Canceled"]
		# # 	# check paths and resolve path mappings.
		# # 	self.submitCheckPaths()
		# # 	# 
		# # 	handleMaster = "media" if self.isUsingMasterVersion() else False
		# # 	plugin = self.core.plugins.getRenderfarmPlugin(self.cb_manager.currentText())
			
		# # 	sceneDescription = None

		# # 	result = plugin.sm_render_submitJob(
		# # 		self,
		# # 		rSettings["outputName"],
		# # 		parent,
		# # 		handleMaster=handleMaster,
		# # 		details=details,
		# # 		sceneDescription=sceneDescription
		# # 	)
			

		# # 	updateMaster = False
		# # 	# Render Locally
		# # 	# else:
		# # 	# 	result = self.fusionFuncs.sm_render_startLocalRender(
		# # 	# 		self, outOnly, rSettings["outputName"], rSettings
		# # 	# 	)
		# # 	# result = self.fusionFuncs.sm_render_startLocalRender(
		# # 	# 	self, outOnly, rSettings["outputName"], rSettings
		# # 	# )
		# # # else:
		# # # 	rSettings = self.LastRSettings
		# # # 	result = self.fusionFuncs.sm_render_startLocalRender(
		# # # 		self, outOnly, rSettings["outputName"], rSettings
		# # # 	)
		# # # 	outputName = rSettings["outputName"]

		# # if not self.renderingStarted:
		# # 	self.fusionFuncs.sm_render_undoRenderSettings(self, rSettings)

		# # if result == "publish paused":
		# # 	return
		# # else:
		# # 	if updateMaster:
		# # 		self.handleMasterVersion(outputName)

		# # 	kwargs = {
		# # 		"state": self,
		# # 		"scenefile": fileName,
		# # 		"settings": rSettings,
		# # 		"result": result,
		# # 	}

		# # 	self.core.callback("postRender", **kwargs)

		# # 	if "Result=Success" in result:
		# # 		return [self.state.text(0) + " - success"]
		# # 	else:
		# # 		erStr = "%s ERROR - sm_default_imageRenderPublish %s:\n%s" % (
		# # 			time.strftime("%d/%m/%y %X"),
		# # 			self.core.version,
		# # 			result,
		# # 		)
		# # 		if not result.startswith("Execute Canceled: "):
		# # 			if result == "unknown error (files do not exist)":
		# # 				QMessageBox.warning(
		# # 					self.core.messageParent,
		# # 					"Warning",
		# # 					"No files were created during the rendering. If you think this is a Prism bug please report it in the forum:\nwww.prism-pipeline.com/forum/\nor write a mail to contact@prism-pipeline.com",
		# # 				)
		# # 			else:
		# # 				self.core.writeErrorLog(erStr)
		# # 		return [self.state.text(0) + " - error - " + result]



	@err_catcher(name=__name__)
	def isUsingMasterVersion(self):
		useMaster = self.core.mediaProducts.getUseMaster()
		if not useMaster:
			return False

		masterAction = self.cb_master.currentText()
		if masterAction == "Don't update master":
			return False

		return True

	@err_catcher(name=__name__)
	def handleMasterVersion(self, outputName):
		if not self.isUsingMasterVersion():
			return

		masterAction = self.cb_master.currentText()
		if masterAction == "Set as master":
			self.core.mediaProducts.updateMasterVersion(outputName, mediaType="2drenders")
		elif masterAction == "Add to master":
			self.core.mediaProducts.addToMasterVersion(outputName, mediaType="2drenders")

	@err_catcher(name=__name__)
	def setTaskWarn(self, warn):
		# useSS = getattr(self.fusionFuncs, "colorButtonWithStyleSheet", False)
		# if warn:
		# 	if useSS:
		# 		self.b_changeTask.setStyleSheet(
		# 			"QPushButton { background-color: rgb(200,0,0); }"
		# 		)
		# 	else:
		# 		self.b_changeTask.setPalette(self.warnPalette)
		# else:
		# 	if useSS:
		# 		self.b_changeTask.setStyleSheet("")
		# 	else:
		# 		self.b_changeTask.setPalette(self.oldPalette)

		pass


	#This function is used to get the settings that are going to be saved to the state file.
	@err_catcher(name=__name__)
	def getStateProps(self):
		stateProps = {
			"stateName": self.e_name.text(),
			"contextType": self.getContextType(),
			"customContext": self.customContext,
			"taskname": self.getTaskname(),

			"overrideFrameRange": self.chb_overrideFrameRange.isChecked(),
			"rangeType": str(self.cb_rangeType.currentText()),
			"startframe": self.sp_rangeStart.value(),
			"endframe": self.sp_rangeEnd.value(),
			"frameExpression": self.le_frameExpression.text(),

			"overrideMaster": self.chb_overrideMaster.isChecked(),
			"ovrMasterOption": self.cb_master.currentText(),

			"overrideLocation": self.chb_overrideLocation.isChecked(),
			"ovrLocOption": self.cb_outPath.currentText(),

			"overrideScaling": self.chb_overrideScaling.isChecked(),
			"ovrScaleOption": self.cb_renderScaling.currentText(),

			"overrideHiQ": self.chb_overrideQuality.isChecked(),
			"ovrHiQOption": self.cb_renderQuality.currentText(),

			"overrideMB": self.chb_overrideRenderMB.isChecked(),
			"ovrMBOption": self.cb_renderMB.currentText(),

			"overrideProxy": self.chb_overrideProxy.isChecked(),
			"ovrProxyOption": self.cb_renderProxy.currentText(),

			"curoutputpath": self.cb_outPath.currentText(),
			"submitrender": str(self.gb_submit.isChecked()),
			"rjmanager": str(self.cb_manager.currentText()),
			"rjprio": self.sp_rjPrio.value(),
			"rjframespertask": self.sp_rjFramesPerTask.value(),
			"rjtimeout": self.sp_rjTimeout.value(),
			"rjsuspended": str(self.chb_rjSuspended.isChecked()),
			"osdependencies": str(self.chb_osDependencies.isChecked()),
			"osupload": str(self.chb_osUpload.isChecked()),
			"ospassets": str(self.chb_osPAssets.isChecked()),
			"osslaves": self.e_osSlaves.text(),
			"dlconcurrent": self.sp_dlConcurrentTasks.value(),
			"dlgpupt": self.sp_dlGPUpt.value(),
			"dlgpudevices": self.le_dlGPUdevices.text(),
			"stateenabled": str(self.state.checkState(0)),
			# "upversion": str(self.chb_upVersion.isChecked()),
        	"renderStates": [self.tw_renderStates.item(i).text() for i in range(self.tw_renderStates.count())]
		}
		self.core.callback("onStateGetSettings", self, stateProps)
		return stateProps