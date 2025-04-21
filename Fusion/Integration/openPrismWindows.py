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


import sys
import os
import PrismInit

import ManagePrismPaths							#	USED ?

from qtpy import QtCore, QtGui, QtWidgets


def openProjectBrowser(globalpcore=None):
	if not globalpcore:
		qapp = QtWidgets.QApplication.instance()
		if qapp == None:
			qapp = QtWidgets.QApplication(sys.argv)
		popup = popupNoButton("Opening Project Browser, Please wait", qapp)

		pcore = PrismInit.prismInit()

		pcore.callback(name="onProjectBrowserCalled", args=[popup])

		pcore.projectBrowser()
		# del pcore		
		qapp.exec_()
	else:
		qapp = QtWidgets.QApplication.instance()
		if qapp == None:
			qapp = QtWidgets.QApplication(sys.argv)

		if globalpcore:
			launchProjectBrowser(qapp=qapp, globalpcore=globalpcore)
		else:
			popupError()


def runPrismSaveScene(globalpcore=None):
	if not globalpcore:
		qapp = QtWidgets.QApplication.instance()
		if qapp == None:
			qapp = QtWidgets.QApplication(sys.argv)

		pcore = PrismInit.prismInit()
		pcore.saveScene()
		del pcore		
		qapp.exec_()
	else:
		qapp = QtWidgets.QApplication.instance()
		if qapp == None:
			qapp = QtWidgets.QApplication(sys.argv)
		
		if globalpcore:
			pcore = globalpcore
			if pcore.fileInPipeline():
				pcore.saveScene()		
				# qapp.exec_()
			else:
				msg = "File is not in project."
				pcore.popup(msg)
				launchProjectBrowser(qapp=qapp, globalpcore=globalpcore)
		else:
			popupError()


def openPrismSaveWithComment(globalpcore=None):
	if not globalpcore:
		qapp = QtWidgets.QApplication.instance()
		if qapp == None:
			qapp = QtWidgets.QApplication(sys.argv)
		pcore = PrismInit.prismInit()
		pcore.saveWithComment()
		del pcore	
		qapp.exec_()
	else:
		print("[Prism] Globalpcore does not exist")
		qapp = QtWidgets.QApplication.instance()
		if qapp == None:
			qapp = QtWidgets.QApplication(sys.argv)
		
		if globalpcore:
			pcore = globalpcore
			if pcore.fileInPipeline():
				pcore.saveWithComment()		
				qapp.exec_()
			else:
				msg = "File is not in project."
				pcore.popup(msg)

				launchProjectBrowser(qapp=qapp, globalpcore=globalpcore)
		else:
			popupError()

def openPrismStateManager(globalpcore=None):
	if not globalpcore:
		print("[Prism] StateManager: No GlobalPcore")
		qapp = QtWidgets.QApplication.instance()
		if qapp == None:
			qapp = QtWidgets.QApplication(sys.argv)
		popup = popupNoButton("Opening State Manager, Please wait", qapp)

		pcore = PrismInit.prismInit()
		pcore.callback(name="onStateManagerCalled", args=[popup])
		
		pcore.stateManager()
		# del pcore		
		qapp.exec_()
	else:
		qapp = QtWidgets.QApplication.instance()
		if qapp == None:
			qapp = QtWidgets.QApplication(sys.argv)

		
		popup = popupNoButton("Opening State Manager, Please wait", qapp)
		
		if globalpcore:
			pcore = globalpcore
			pcore.callback(name="onStateManagerCalled", args=[popup])
			#
			pcore.stateManager()
			#
			qapp.exec_()
		else:
			popupError()


def openPrismSettings(globalpcore=None):
	if not globalpcore:
		print("[Prism] ProjectBrowser no GlobalPcore")
		qapp = QtWidgets.QApplication.instance()
		if qapp == None:
			qapp = QtWidgets.QApplication(sys.argv)

		pcore = PrismInit.prismInit()
		pcore.prismSettings()
		del pcore
		
		qapp.exec_()
	else:
		qapp = QtWidgets.QApplication.instance()
		if qapp == None:
			qapp = QtWidgets.QApplication(sys.argv)

		if globalpcore:
			pcore = globalpcore
			#
			pcore.prismSettings()
			#
			qapp.exec_()
		else:
			popupError()

def launchProjectBrowser(qapp=None, globalpcore=None):
	if qapp and globalpcore:
		popup = popupNoButton("Opening Project Browser, Please wait", qapp)
		pcore = globalpcore
		pcore.callback(name="onProjectBrowserCalled", args=[popup])
		#
		pcore.projectBrowser()
		#
		qapp.exec_()


def popupError():
	error_box = QtWidgets.QMessageBox()
	# Set the text and title of the error box
	error_box.setText("Prism isn't properly started!\nPlease Reset Prism from the button in the Prism Menu.")
	error_box.setWindowTitle("Error")

	# Set the icon to a critical error icon
	error_box.setIcon(QtWidgets.QMessageBox.Critical)
	error_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
	error_box.setDefaultButton(QtWidgets.QMessageBox.Ok)

	error_box.setStyleSheet("QMessageBox { background-color: #31363b; color: white; }")


	# Execute the error box
	error_box.exec_()


def popupNoButton(
	text,
	qapp,
	title=None,
	icon=None,
	show=True,
	centered=False,
	large=False
):
	text = str(text)
	title = str(title or "Prism")
	current_directory = os.path.dirname(os.path.abspath(__file__))
	icon = QtGui.QIcon(os.path.join(current_directory, "Fusion.ico"))
	label = QtWidgets.QLabel(text)
	icon_label = QtWidgets.QLabel(text)

	label.setStyleSheet("color: white")

	if centered:
		label.setAlignment(QtCore.Qt.AlignCenter)
	if large:
		label.setStyleSheet("color: white; font-size: 15px")


	msg = QtWidgets.QDialog()
	msg.setWindowTitle(title)
	msg.setWindowIcon(icon)

	# Set up layout
	layout = QtWidgets.QVBoxLayout()
	layout.addStretch()
	layout.addWidget(label)
	layout.addStretch()
	msg.setLayout(layout)


	msg.setMinimumWidth(200)
	msg.setMinimumHeight(50)
	msg.setStyleSheet("background-color: #31363b;")

	msg.setModal(False)

	msg.setWindowFlags(msg.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
	if show:
		msg.show()
		qapp.processEvents()

	return msg