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
import sys
import time
import platform
import logging

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

from PrismUtils.Decorators import err_catcher

logger = logging.getLogger(__name__)



class ImageRenderClass(object):
	className = "ImageRender"
	listType = "Export"
	stateCategories = {"Render": [{"label": className, "stateType": className}]}

	@err_catcher(name=__name__)
	def setup(self, state, core, stateManager, node=None, stateData=None):
		self.state = state
		self.core = core
		self.stateManager = stateManager
		self.fusionFuncs = self.core.appPlugin
		self.canSetVersion = True
		self.customContext = None
		self.allowCustomContext = False
		self.cb_context.addItems(["From scenefile", "Custom"])

		self.treeWidget = self.stateManager.tw_export
		self.itemNames = self.getItemNames()

		self.renderingStarted = False
		self.cleanOutputdir = True

		self.e_name.setText(state.text(0) + " - {identifier}")

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
		self.w_frameExpression.setToolTip(
			self.stateManager.getFrameRangeTypeToolTip("ExpressionField")
		)

		#	Render Scaling
		renderScalings = [
			"Force Proxies Off",
			"1/4 (proxy)", 
			"1/3 (proxy)",
			"1/2 (proxy)",
			"100 (scale)",
			"125 (scale)",
			"150 (scale)",
			"200 (scale)"
			]

		self.cb_renderScaling.addItems(renderScalings)
		self.cb_renderScaling.setCurrentIndex(4)

		self.l_name.setVisible(False)
		self.e_name.setVisible(False)
		self.gb_submit.setChecked(False)
		self.f_renderLayer.setVisible(False)

		getattr(self.fusionFuncs, "sm_render_startup", lambda x: None)(self)

		masterItems = ["Set as master", "Add to master", "Don't update master"]
		self.cb_master.addItems(masterItems)
		self.product_paths = self.core.paths.getRenderProductBasePaths()
		self.cb_outPath.addItems(list(self.product_paths.keys()))
		if len(self.product_paths) < 2:
			self.w_outPath.setVisible(False)

		self.mediaType = "2drenders"
		self.tasknameRequired = True

		#	Gets formats dict from Prism_Fusion_Functions.py to differentiate still/movie types
		self.outputFormats = self.fusionFuncs.outputFormats
		self.cb_format.addItems([formatDict["extension"] for formatDict in self.outputFormats])

		self.connectEvents()

		self.oldPalette = self.b_changeTask.palette()
		self.warnPalette = QPalette()
		self.warnPalette.setColor(QPalette.Button, QColor(200, 0, 0))
		self.warnPalette.setColor(QPalette.ButtonText, QColor(255, 255, 255))

		self.setTaskWarn(True)
		self.nameChanged(state.text(0))

		self.cb_manager.addItems([p.pluginName for p in self.core.plugins.getRenderfarmPlugins()])
		self.core.callback("onStateStartup", self)

		#Disable Distributed rendering as it is handled by the NetRender state.
		self.gb_submit.setVisible(False)
		self.gb_submit.setChecked(False)

		self.managerChanged(True)

		#	Load State data from comp
		if stateData is not None:
			self.loadData(stateData)

		#	Load default State data
		else:
			try:
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

				self.chb_resOverride.setChecked(False)

				self.setUniqueName(f"{self.className} - {self.getTaskname()}")

				self.stateUID = self.fusionFuncs.createUUID()

				logger.debug("Loading State Defaults")

			except:
				logger.warning("ERROR: Failed to load State defaults")

			self.setRendernode()
			self.updateUi()

		self.onStateLoaded()


	@err_catcher(name=__name__)
	def loadData(self, data):
		try:
			if "nodeUID" in data:
				self.stateUID = data["nodeUID"]
			if "contextType" in data:
				self.setContextType(data["contextType"])
			if "customContext" in data:
				self.customContext = data["customContext"]
			if "taskname" in data:
				self.setTaskname(data["taskname"])

			self.updateUi()

			if "stateName" in data:
				self.e_name.setText(data["stateName"])
			elif "statename" in data:
				self.e_name.setText(data["statename"] + " - {identifier}")

			if "renderScaleOverride" in data:
				self.chb_resOverride.setChecked(data["renderScaleOverride"])
			if "currentRenderScale" in data:
				idx = self.cb_renderScaling.findText(data["currentRenderScale"])
				if idx != -1:
					self.cb_renderScaling.setCurrentIndex(idx)
					self.stateManager.saveStatesToScene()
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
			if "masterVersion" in data:
				idx = self.cb_master.findText(data["masterVersion"])
				if idx != -1:
					self.cb_master.setCurrentIndex(idx)
			if "curoutputpath" in data:
				idx = self.cb_outPath.findText(data["curoutputpath"])
				if idx != -1:
					self.cb_outPath.setCurrentIndex(idx)
			if "renderlayer" in data:
				idx = self.cb_renderLayer.findText(data["renderlayer"])
				if idx != -1:
					self.cb_renderLayer.setCurrentIndex(idx)
					self.stateManager.saveStatesToScene()
			if "outputFormat" in data:
				idx = self.cb_format.findText(data["outputFormat"])
				if idx != -1:
					self.cb_format.setCurrentIndex(idx)
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
			if "lastexportpath" in data:
				lePath = self.core.fixPath(data["lastexportpath"])
				self.l_pathLast.setText(lePath)
				self.l_pathLast.setToolTip(lePath)
			if "stateenabled" in data:
				if type(data["stateenabled"]) == int:
					self.state.setCheckState(
						0, Qt.CheckState(data["stateenabled"]),
					)
			if "rendernode" in data:
				self.setRendernode()
			
			if "outonly" in data: 
				self.chb_outOnly.setChecked(data["outonly"])
			
			logger.debug("Loaded State Data into UI")
		
		except:
			logger.warning("ERROR: Failed to load State Data into UI")


		self.core.callback("onStateSettingsLoaded", self, data)





		# Setup the enabled disabled checkboxes
		# nodename = self.getRendernodeName()
		# if self.fusionFuncs.rendernode_exists(nodename):
		# 	state = self.fusionFuncs.getNodePassthrough(nodename)
		# 	if state:
		# 		self.state.setCheckState(0, Qt.Checked)
		# 	else:
		# 		self.state.setCheckState(0, Qt.Unchecked)
				
		# self.stateManager.tw_export.itemChanged.connect(self.sm_handle_item_changed)

		# self.state.setBackground(0, QColor("#365e99"))



	@err_catcher(name=__name__)
	def onStateLoaded(self):
		if self.fusionFuncs.nodeExists(self.stateUID):
			passThrough = self.fusionFuncs.isPassThrough(nodeUID=self.stateUID)
			if passThrough:
				self.state.setCheckState(0, Qt.Unchecked)
			else:
				self.state.setCheckState(0, Qt.Checked)

		self.stateManager.tw_export.itemChanged.connect(self.sm_handle_item_changed)

		self.state.setBackground(0, QColor("#365e99"))

		self.stateManager.saveStatesToScene()

		stateName = self.fusionFuncs.getNodeNameByUID(self.stateUID)
		logger.debug(f"Loaded State: {stateName}")


	@err_catcher(name=__name__)
	def connectEvents(self):
		self.e_name.textChanged.connect(self.nameChanged)
		self.e_name.editingFinished.connect(self.stateManager.saveStatesToScene)
		self.cb_context.activated.connect(self.onContextTypeChanged)
		self.b_context.clicked.connect(self.selectContextClicked)
		self.b_changeTask.clicked.connect(self.changeTask)
		self.b_setRendernode.clicked.connect(self.on_b_setRendernode_clicked)
		self.chb_resOverride.toggled.connect(lambda: self.updateUi())
		self.cb_renderScaling.activated.connect(self.stateManager.saveStatesToScene)
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
		self.cb_renderLayer.activated.connect(self.stateManager.saveStatesToScene)
		self.cb_format.activated.connect(lambda: self.setRendernode())
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
		self.b_pathLast.clicked.connect(self.showLastPathMenu)
		self.chb_outOnly.stateChanged.connect(self.outOnlyChanged)
		# self.treeWidget.itemSelectionChanged.connect(self.onTreeItemSelectionChanged)

	@err_catcher(name=__name__)
	def generateUniqueName(self, base_name, names):
		try:
			unique_name = base_name
			counter = 1
			while unique_name in names:
				unique_name = f"{base_name}_{counter}"
				counter += 1
			names.add(unique_name)
			return unique_name
		except:
			logger.warning(f"ERROR: Failed to create unique name for {base_name}")
			return base_name


	@err_catcher(name=__name__)
	def setUniqueName(self, origName):
		name = origName
		names = self.itemNames
		uniqueName = self.generateUniqueName(name, names)
		self.itemNames.add(uniqueName)
		newtaskname = uniqueName.split(" - ")[-1]
		self.changeTaskAuto(newtaskname)


	@err_catcher(name=__name__)
	def showLastPathMenu(self, state=None):
		path = self.l_pathLast.text()
		if path == "None":
			return

		menu = QMenu(self)

		act_open = QAction("Play", self)
		act_open.triggered.connect(lambda: self.core.media.playMediaInExternalPlayer(path))
		menu.addAction(act_open)

		act_open = QAction("Open in Media Browser", self)
		act_open.triggered.connect(lambda: self.openInMediaBrowser(path))
		menu.addAction(act_open)

		act_open = QAction("Open in explorer", self)
		act_open.triggered.connect(lambda: self.core.openFolder(path))
		menu.addAction(act_open)

		act_copy = QAction("Copy", self)
		act_copy.triggered.connect(lambda: self.core.copyToClipboard(path, file=True))
		menu.addAction(act_copy)

		menu.exec_(QCursor.pos())

	@err_catcher(name=__name__)
	def openInMediaBrowser(self, path):
		self.core.projectBrowser()
		self.core.pb.showTab("Media")
		data = self.core.paths.getRenderProductData(path)
		self.core.pb.mediaBrowser.showRender(entity=data, identifier=data.get("identifier"), version=data.get("version"))

	@err_catcher(name=__name__)
	def selectContextClicked(self, state=None):
		self.dlg_entity = self.stateManager.entityDlg(self)
		data = self.getCurrentContext()
		self.dlg_entity.w_entities.navigate(data)
		self.dlg_entity.entitySelected.connect(lambda x: self.setCustomContext(x))
		self.dlg_entity.show()

	@err_catcher(name=__name__)
	def setCustomContext(self, context):
		self.customContext = context
		self.refreshContext()
		self.stateManager.saveStatesToScene()

	@err_catcher(name=__name__)
	def onContextTypeChanged(self, state):
		self.refreshContext()
		self.stateManager.saveStatesToScene()

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

	# @err_catcher(name=__name__)
	# def setCam(self, index):
	#     self.curCam = self.camlist[index]
	#     self.stateManager.saveStatesToScene()

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

		if self.state.text(0).endswith(" - disabled"):
			name += " - disabled"

		self.state.setText(0, name)

		self.statusColorNodeButton()

		self.stateManager.saveStatesToScene()



	@err_catcher(name=__name__)
	def getFormat(self):
		self.cb_format.currentText()

	@err_catcher(name=__name__)
	def setFormat(self, fmt):
		try:
			idx = self.cb_format.findText(fmt)
			if idx != -1:
				self.cb_format.setCurrentIndex(idx)
				self.stateManager.saveStatesToScene()
				return True
		except:
			logger.warning(f"ERROR: Unable to set format in the UI: {fmt}")

		return False

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

	@err_catcher(name=__name__)
	def getTaskname(self):
		taskName = self.l_taskName.text()
		return taskName

	@err_catcher(name=__name__)
	def setTaskname(self, taskname):
		self.l_taskName.setText(taskname)
		self.setTaskWarn(not bool(taskname))
		self.updateUi()

	@err_catcher(name=__name__)
	def getSortKey(self):
		return self.getTaskname()

	
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
			isLegal, errorStr = self.fusionFuncs.getFusLegalName(self.nameWin.e_item.text(), check=True)
			if not isLegal:
				self.core.popup(errorStr)
				return
			
			#	Gets user entered name
			enteredName = self.nameWin.e_item.text()
			#	Gets Fusion Legal name
			fusLegalName = self.fusionFuncs.getFusLegalName(enteredName)

			#	Compares the names
			if enteredName != fusLegalName:
				nameChangeString = ("The Fusion Saver name will be changed from:\n\n"
									f"       {enteredName}  to  {fusLegalName}     \n\n\n"
									"Accept the change?")

				#	Shows popup of the name change
				result = self.core.popupQuestion(nameChangeString, title="Name Changed")

				#	If it is not accepted it will not change the name
				if result != "Yes":
					return

			self.setTaskname(self.nameWin.e_item.text())
			self.nameChanged(self.e_name.text())
			self.stateManager.saveStatesToScene()
			
			self.stateManager.tw_export.itemChanged.connect(self.sm_handle_item_changed)


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
	
	# @err_catcher(name=__name__)
	# def onTreeItemSelectionChanged(self):
		# 	self.setTreeItemColor("selected")


	#	Checks if Comp is in Prism's project
	@err_catcher(name=__name__)
	def on_b_setRendernode_clicked(self):
		pcore = self.core
		curfile = pcore.getCurrentFileName()
		filepath = curfile.replace("\\", "/")

		#	Checks if comp exists on disk and in Prism
		if not filepath and not pcore.fileInPipeline(filepath, validateFilename=False):
			pcore.showFileNotInProjectWarning()
			return
				
		#	Sets the Saver
		self.setRendernode(create=True)


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

		try:
			# Iterate through the top-level items in the QTreeWidget
			for i in range(self.treeWidget.topLevelItemCount()):
				top_level_item = self.treeWidget.topLevelItem(i)
				self.getItemNamesRecursive(top_level_item, itemNames)

			return itemNames
		
		except:
			logger.warning("ERROR: Cannot get Item names")
			return None

	@err_catcher(name=__name__)
	def setTreeItemColor(self, status=None):
		if self.chb_outOnly.isChecked():
			background_color = QColor("#007ACC")
			# print(widgetItem.data(0, 1))
		else:
			background_color = None #QColor("#232629")
			# print(widgetItem.data(0, 1))

		self.state.setData(0, 1, background_color)


	@err_catcher(name=__name__)
	def outOnlyChanged(self, checked):
		if checked:
			self.f_setOutputOnly.setStyleSheet("background-color: #007ACC;")
		else:
			self.f_setOutputOnly.setStyleSheet("")

		self.setTreeItemColor()
		self.stateManager.saveStatesToScene()

	@err_catcher(name=__name__)
	def sm_handle_item_changed(self, item, column):
		# print("ch")
		if(item.ui.className == "ImageRender"):
			if item.text(column) == self.state.text(column):
				if item.checkState(0) == Qt.Checked:
					self.sm_ToggleNodeChanged(False)
				else:
					self.sm_ToggleNodeChanged(True)

	@err_catcher(name=__name__)
	def sm_ToggleNodeChanged(self, disabled)->None:
		# disabled = twitem.checkState(0) != Qt.Checked
		try:
			nodeUID = self.stateUID
			if self.fusionFuncs.nodeExists(nodeUID):
				self.fusionFuncs.setPassThrough(nodeUID=nodeUID, passThrough=disabled)
			else:
				self.setRendernode()
		except:
			stateName = self.fusionFuncs.getNodeNameByUID(nodeUID)
			logger.warning(f"ERROR: Unable to change the {stateName} Saver's passthrough.")

		# self.setTreeItemColor()
		self.stateManager.saveStatesToScene()


	@err_catcher(name=__name__)
	def getRendernodeName(self):
		try:
			identifier = self.getTaskname()

			if identifier != "":
				legalName = self.fusionFuncs.getFusLegalName(identifier)
				nodeName = f"PrSAVER_{legalName}"

				return nodeName
			
			else:
				return None
		
		except:
			return None
	

	#	Adds and configures RenderNode
	@err_catcher(name=__name__)
	def setRendernode(self, create=False):
		nodeName = self.getRendernodeName()
		nodeUID = self.stateUID

		#	If the Saver exists
		if self.fusionFuncs.nodeExists(nodeUID):
			self.b_setRendernode.setText(nodeName)

			#	Create Node Data
			nodeData = {"nodeName": nodeName,
			   			"format": self.cb_format.currentText()
				}
						   

			self.fusionFuncs.updateRendernode(nodeUID, nodeData)

		#	If it does not exist
		else:
			#	If Create then call createRendernode
			if create:

				#	Create Node Data
				nodeData = {
					"nodeName": nodeName,
					"nodeUID": nodeUID,
					"version": "",
					"filepath": "",
					"format": "",
					}

				try:
					result = self.fusionFuncs.createRendernode(nodeUID, nodeData)
					self.b_setRendernode.setText(nodeName)
				except:
					pass

			#	 If not create then just set text
			else:
				self.b_setRendernode.setText("SetRenderNode")


		self.configureRenderNode(nodeName)
		self.statusColorNodeButton()
		self.updateUi()
		self.setTreeItemColor()
		self.stateManager.saveStatesToScene()


	#	Checks the Saver's data and colors the button
	@err_catcher(name=__name__)
	def statusColorNodeButton(self):
		try:
			renderNodeName = self.getRendernodeName()

			#	Checks if Saver exists
			if self.fusionFuncs.nodeExists(self.stateUID):
				toolName = self.fusionFuncs.getNodeNameByUID(self.stateUID)
				#	Compares Identifier name to Saver name
				if toolName == renderNodeName:
					#	If they are the same then Green
					self.b_setRendernode.setStyleSheet("background-color: green; color: white;")
					logger.debug(f"Saver matches Identifier for {renderNodeName}")
					return True
				
				else:
					#	If different then Orange
					self.b_setRendernode.setStyleSheet("background-color: orange; color: white;")
					logger.debug(f"Saver name does not match Identifier {renderNodeName}")
					return "ERROR: Saver name does not match Indentifier"

			#	If the Saver does not exist	
			else:
				raise Exception

		except:
			#	If Saver does not exists or error then RED
			self.b_setRendernode.setStyleSheet("background-color: red; color: white;")
			logger.debug(f"Saver does not exist for:  {renderNodeName}")
			return "ERROR:  Saver does not exist"


	#	Sets image format and output path
	@err_catcher(name=__name__)
	def configureRenderNode(self, nodeName, useVersion="next", stateUI=None):
		if stateUI is None:
			stateUI = self
		if stateUI.tasknameRequired and not stateUI.getTaskname():
			return
		
		nodeUID = self.stateUID

		outputName, dir, version = self.getOutputName(useVersion=useVersion)

		if not outputName:
			return

		extension = stateUI.cb_format.currentText()
		fuseName = None

		try:
			nodeData = {
				"nodeName": nodeName,
				"version": version,
				"filepath": outputName,
				"format": extension,
				"fuseFormat": self.fusionFuncs.getFuseFormat(extension)
				}

			self.fusionFuncs.configureRenderNode(nodeUID, nodeData)
			self.stateManager.saveStatesToScene()

		except:
			nodeName = self.fusionFuncs.getNodeNameByUID(nodeUID)
			logger.warning(f"ERROR: Unable to config Saver {nodeName}")


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
	def updateUi(self):
		self.w_context.setHidden(not self.allowCustomContext)
		self.refreshContext()


		# update Cams																		#	TODO - NEEDED ???
		# self.cb_cam.clear()
		# self.camlist = camNames = []

		# if not self.stateManager.standalone:
		#     self.camlist = self.fusionFuncs.getCamNodes(self, cur=True)
		#     camNames = [self.fusionFuncs.getCamName(self, i) for i in self.camlist]

		# self.cb_cam.addItems(camNames)

		# if self.curCam in self.camlist:
		#     self.cb_cam.setCurrentIndex(self.camlist.index(self.curCam))
		# else:
		#     self.cb_cam.setCurrentIndex(0)
		#     if len(self.camlist) > 0:
		#         self.curCam = self.camlist[0]
		#     else:
		#         self.curCam = None

		#     self.stateManager.saveStatesToScene()

		self.updateRange()

		if not self.core.mediaProducts.getUseMaster():
			self.w_master.setVisible(False)

		self.cb_renderScaling.setEnabled(self.chb_resOverride.isChecked())

		# update Render Layer
		# curLayer = self.cb_renderLayer.currentText()
		# self.cb_renderLayer.clear()

		# layerList = getattr(
		# 	self.fusionFuncs, "sm_render_getRenderLayer", lambda x: []
		# )(self)

		# self.cb_renderLayer.addItems(layerList)

		# if curLayer in layerList:
		# 	self.cb_renderLayer.setCurrentIndex(layerList.index(curLayer))
		# else:
		# 	self.cb_renderLayer.setCurrentIndex(0)
		# 	self.stateManager.saveStatesToScene()

		# self.refreshSubmitUi()
		# getattr(self.fusionFuncs, "sm_render_refreshPasses", lambda x: None)(self)

		self.nameChanged(self.e_name.text())
  
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


	@err_catcher(name=__name__)
	def getFrameRange(self, rangeType):
		startFrame = None
		endFrame = None
		try:
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
				try:	
					comp = self.fusionFuncs.getCurrentComp()
					startFrame = comp.CurrentTime
				except:
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
		
		except:
			stateName = self.fusionFuncs.getNodeNameByUID(self.stateUID)
			logger.warning(f"ERROR: Unable to set range type {rangeType} for {stateName}")
	

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

	@err_catcher(name=__name__)
	def showPasses(self):
		steps = getattr(
			self.fusionFuncs, "sm_render_getRenderPasses", lambda x: None
		)(self)

		if steps is None or len(steps) == 0:
			return False

		if self.core.isStr(steps):
			steps = eval(steps)

		if eval(os.getenv("PRISM_DEBUG", "False")):
			try:
				del sys.modules["ItemList"]
			except:
				pass

		import ItemList

		self.il = ItemList.ItemList(core=self.core)
		self.il.setWindowTitle("Select Passes")
		self.core.parentWindow(self.il)
		self.il.tw_steps.doubleClicked.connect(self.il.accept)
		self.il.tw_steps.horizontalHeaderItem(0).setText("Name")
		self.il.tw_steps.setColumnHidden(1, True)
		for i in sorted(steps, key=lambda s: s.lower()):
			rc = self.il.tw_steps.rowCount()
			self.il.tw_steps.insertRow(rc)
			item1 = QTableWidgetItem(i)
			self.il.tw_steps.setItem(rc, 0, item1)

		result = self.il.exec_()

		if result != 1:
			return False

		for i in self.il.tw_steps.selectedItems():
			if i.column() == 0:
				self.fusionFuncs.sm_render_addRenderPass(
					self, passName=i.text(), steps=steps
				)

		self.updateUi()
		self.stateManager.saveStatesToScene()

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

		if self.tasknameRequired and not self.getTaskname():
			warnings.append(["No identifier is given.", "", 3])

		#	Checks for any node errors
		nodeStatus = self.statusColorNodeButton()
		if nodeStatus is not True:
			warnings.append([nodeStatus, "", 3])

		# if self.curCam is None or (									#	TODO - NEEDED ???
		#     self.curCam != "Current View"
		#     and not self.fusionFuncs.isNodeValid(self, self.curCam)
		# ):
		#     warnings.append(["No camera is selected.", "", 3])
		# elif self.curCam == "Current View":
		#     warnings.append(["No camera is selected.", "", 2])

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
	# @err_catcher(name=__name__)										#	TODO - NEEDED ???
	# def submitCheckPaths(self):
	# 	self.fusionFuncs.sm_render_CheckSubmittedPaths()

	# @err_catcher(name=__name__)
	# def setFarmedRange(self):
	# 	print("hay que poner el frame range para la farm")

	# @err_catcher(name=__name__)
	# def upSubmittedSaversVersions(self, parent):
	# 	# Before Submitting, change version of elegible Savers.
	# 	sm = parent
	# 	fileName = self.core.getCurrentFileName()
	# 	context = self.getCurrentContext()
	# 	for state in sm.states:
	# 		stateUI = state.ui
	# 		if stateUI.className == "ImageRender":
	# 			if not stateUI.b_setRendernode.text() == "SetRenderNode" and stateUI.chb_passthrough.isChecked():
	# 				#Get Output, Update UI and set infoFile.				
	# 				stateUI.executeState(parent=parent, outOnly=True)


	@err_catcher(name=__name__)
	def getOutputName(self, useVersion="next", stateUI=None):
		if stateUI == None:
			stateUI = self
		if stateUI.tasknameRequired and not stateUI.getTaskname():
			return

		context = stateUI.getCurrentContext()

		if "type" not in context:
			return
		
		task = stateUI.getTaskname()

		#	Gets extension
		extension = stateUI.cb_format.currentText()
		#	Gets list of ext types that are still image formats
		imageExts = [formatDict["extension"] for formatDict in self.outputFormats if formatDict["type"] == "image"]
		if extension in imageExts:
			#	Adds project padding to the name if it is a image sequence
			framePadding = "0" * self.core.framePadding
		else:
			#	Adds empty string if a movie format
			framePadding = ""

		location = stateUI.cb_outPath.currentText()

		try:
			outputPathData = stateUI.core.mediaProducts.generateMediaProductPath(
				entity=context,
				task=task,
				extension=extension,
				framePadding=framePadding,
				comment=self.stateManager.publishComment,
				version=useVersion if useVersion != "next" else None,
				location=location,
				singleFrame=False,
				returnDetails=True,
				mediaType=self.mediaType,
				)

			outputFolder = os.path.dirname(outputPathData["path"])
			hVersion = outputPathData["version"]

			return outputPathData["path"], outputFolder, hVersion
		
		except Exception as e:
			stateName = self.fusionFuncs.getNodeNameByUID(self.stateUID)
			logger.warning(f"ERROR: Unable to get render output name for {stateName}:\n{e}")
			return None, None, None


	@err_catcher(name=__name__)
	def executeState(self, parent, useVersion="next", outOnly=False):
		outOnly = outOnly or self.chb_outOnly.isChecked()

		rangeType = self.cb_rangeType.currentText()
		frames = self.getFrameRange(rangeType)

		if rangeType != "Expression":
			startFrame = frames[0]
			endFrame = frames[1]
		else:
			startFrame = None
			endFrame = None

		if frames is None or frames == [] or frames[0] is None:
			return [self.state.text(0) + " - error - Framerange is invalid"]

		if rangeType == "Single Frame":
			endFrame = startFrame

		updateMaster = True
		fileName = self.core.getCurrentFileName()
		context = self.getCurrentContext()

		if not self.renderingStarted:
			if self.tasknameRequired and not self.getTaskname():
				return [
					self.state.text(0)
					+ ": error - no identifier is given. Skipped the activation of this state."
				]

			# if self.curCam is None or (
			#     self.curCam != "Current View"
			#     and not self.fusionFuncs.isNodeValid(self, self.curCam)
			# ):
			#     return [
			#         self.state.text(0)
			#         + ": error - no camera is selected. Skipping activation of this state."
			#     ]

			outputName, outputPath, hVersion = self.getOutputName(useVersion=useVersion)

			if not outputName:
				return [self.state.text(0) + " - error - Unable to get render output path. Canceling publish. "]

			outLength = len(outputName)
			if platform.system() == "Windows" and os.getenv("PRISM_IGNORE_PATH_LENGTH") != "1" and outLength > 255:
				return [
					self.state.text(0)
					+ " - error - The outputpath is longer than 255 characters (%s), which is not supported on Windows. Please shorten the outputpath by changing the comment, taskname or projectpath."
					% outLength
				]

			if not os.path.exists(os.path.dirname(outputPath)):
				os.makedirs(os.path.dirname(outputPath))

			details = context.copy()
			if "filename" in details:
				del details["filename"]

			if "extension" in details:
				del details["extension"]

			details["version"] = hVersion
			details["sourceScene"] = fileName
			details["identifier"] = self.getTaskname()
			details["comment"] = self.stateManager.publishComment

			_, extension = os.path.splitext(outputName)
			fuseFormat = self.fusionFuncs.getFuseFormat(extension)

			if self.mediaType == "3drenders":
				infopath = os.path.dirname(outputPath)
			else:
				infopath = outputPath

			self.core.saveVersionInfo(
				filepath=infopath, details=details
			)

			self.l_pathLast.setText(outputName)
			self.l_pathLast.setToolTip(outputName)
			self.stateManager.saveStatesToScene()

			rSettings = {
				"outputName": outputName,
				"nodeUID": self.stateUID,
				"version": hVersion,
				"format": extension,
				"fuseFormat": fuseFormat,
				"startFrame": startFrame,
				"endFrame": endFrame,
				"frames": frames,
				"rangeType": rangeType,
			}

			rSettings["scalingOvr"] = self.chb_resOverride.isChecked()
			rSettings["render_Scale"] = self.cb_renderScaling.currentText()

			self.fusionFuncs.sm_render_preSubmit(self, rSettings)

			kwargs = {
				"state": self,
				"scenefile": fileName,
				"settings": rSettings,
			}

			result = self.core.callback("preRender", **kwargs)
			for res in result:
				if isinstance(res, dict) and res.get("cancel", False):
					return [
						self.state.text(0)
						+ " - error - %s" % res.get("details", "preRender hook returned False")
					]

			if not os.path.exists(os.path.dirname(rSettings["outputName"])):
				os.makedirs(os.path.dirname(rSettings["outputName"]))


			result = self.fusionFuncs.sm_render_startLocalRender(
					self, outOnly, rSettings["outputName"], rSettings
				)

		else:
			rSettings = self.LastRSettings
			result = self.fusionFuncs.sm_render_startLocalRender(
				self, outOnly, rSettings["outputName"], rSettings
			)
			outputName = rSettings["outputName"]

		if not self.renderingStarted:
			self.fusionFuncs.sm_render_undoRenderSettings(self, rSettings)

		if result == "publish paused":
			return [self.state.text(0) + " - publish paused"]
		else:
			if updateMaster:
				self.handleMasterVersion(outputName)

			kwargs = {
				"state": self,
				"scenefile": fileName,
				"settings": rSettings,
				"mediaType": "2drenders",
				"result": result,
			}

			self.core.callback("postRender", **kwargs)

			if "Result=Success" in result:
				return [self.state.text(0) + " - success"]
			else:
				erStr = "%s ERROR - sm_default_imageRenderPublish %s:\n%s" % (
					time.strftime("%d/%m/%y %X"),
					self.core.version,
					result,
				)
				if not result.startswith("Execute Canceled: "):
					if result == "unknown error (files do not exist)":
						QMessageBox.warning(
							self.core.messageParent,
							"Warning",
							"No files were created during the rendering. If you think this is a Prism bug please report it in the forum:\nwww.prism-pipeline.com/forum/\nor write a mail to contact@prism-pipeline.com",
						)
					else:
						self.core.writeErrorLog(erStr)
				return [self.state.text(0) + " - error - " + result]


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

		stateName = self.fusionFuncs.getNodeNameByUID(self.stateUID)

		masterAction = self.cb_master.currentText()
		if masterAction == "Set as master":
			try:
				self.core.mediaProducts.updateMasterVersion(outputName, mediaType="2drenders")
				logger.debug(f"Updated Master for: {stateName}")
			except Exception as e:
				logger.warning(f"ERROR: Unable to Set as Master for {stateName}:\n{e}")

		elif masterAction == "Add to master":
			try:
				self.core.mediaProducts.addToMasterVersion(outputName, mediaType="2drenders")
				logger.debug(f"Updated Master for: {stateName}")
			except Exception as e:
				logger.warning(f"ERROR: Unable to Add to Master for {stateName}:\n{e}")


	@err_catcher(name=__name__)
	def setTaskWarn(self, warn):
		try:
			useSS = getattr(self.fusionFuncs, "colorButtonWithStyleSheet", False)
			if warn:
				if useSS:
					self.b_changeTask.setStyleSheet(
						"QPushButton { background-color: rgb(200,0,0); }"
					)
				else:
					self.b_changeTask.setPalette(self.warnPalette)
			else:
				if useSS:
					self.b_changeTask.setStyleSheet("")
				else:
					self.b_changeTask.setPalette(self.oldPalette)
		except:
			logger.warning("ERROR: Unable to set Task Warning color.")

	#	Called Directly from StateManager
	@err_catcher(name=__name__)
	def preDelete(self, item=None):
		try:
			#   Defaults to Delete the Node
			delAction = "Yes"

			if not self.core.uiAvailable:
				logger.debug(f"Deleting node: {item}")

			else:
				nodeUID = self.stateUID
				nodeName = self.fusionFuncs.getNodeNameByUID(nodeUID)

				#   If the Loader exists, show popup question
				if nodeName:
					message = f"Would you like to also remove the associated Saver: {nodeName}?"
					buttons = ["Yes", "No"]
					buttonToBool = {"Yes": True, "No": False}

					response = self.core.popupQuestion(message, buttons=buttons, icon=QMessageBox.NoIcon)
					delAction = buttonToBool.get(response, False)
				
				self.fusionFuncs.deleteNode("render2d", nodeUID, delAction=delAction)

		except:
			logger.warning("ERROR: Unable to remove Saver from Comp")


	#This function is used to get the settings that are going to be saved to the state file.
	@err_catcher(name=__name__)
	def getStateProps(self):
		stateProps = {
			"stateName": self.e_name.text(),
			"nodeUID": self.stateUID, 
			"contextType": self.getContextType(),
			"customContext": self.customContext,
			"taskname": self.getTaskname(),
			"renderScaleOverride": self.chb_resOverride.isChecked(),
			"currentRenderScale": self.cb_renderScaling.currentText(),
			"rangeType": str(self.cb_rangeType.currentText()),
			"startframe": self.sp_rangeStart.value(),
			"endframe": self.sp_rangeEnd.value(),
			"frameExpression": self.le_frameExpression.text(),
			# "currentcam": str(self.curCam),
			# "resoverride": str(
			# 	[
			# 		self.chb_resOverride.isChecked(),
			# 		self.sp_resWidth.value(),
			# 		self.sp_resHeight.value(),
			# 	]
			# ),
			"masterVersion": self.cb_master.currentText(),
			"curoutputpath": self.cb_outPath.currentText(),
			"renderlayer": str(self.cb_renderLayer.currentText()),
			"outputFormat": str(self.cb_format.currentText()),
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
			"lastexportpath": self.l_pathLast.text().replace("\\", "/"),
			"stateenabled": str(self.state.checkState(0)),
			"rendernode": self.b_setRendernode.text(),
			"outonly": self.chb_outOnly.isChecked(),
		}
		self.core.callback("onStateGetSettings", self, stateProps)
		return stateProps
