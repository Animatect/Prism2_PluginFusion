import sys
import os
import PrismInit

import manageprismpaths

# from qtpy import QtCore, QtGui, QtWidgets
from PySide6 import QtCore, QtGui, QtWidgets


def openProjectBrowser(globalpcore=None):
	if not globalpcore:
		qapp = QtWidgets.QApplication.instance()
		if qapp == None:
			qapp = QtWidgets.QApplication(sys.argv)
		popup = popupNoButton("Openning Project Browser, Please wait", qapp)

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
				qapp.exec_()
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
		print("globalpcore")
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
		print("StateManager no GlobalPcore")
		qapp = QtWidgets.QApplication.instance()
		if qapp == None:
			qapp = QtWidgets.QApplication(sys.argv)
		popup = popupNoButton("Openning State Manager, Please wait", qapp)

		pcore = PrismInit.prismInit()
		pcore.callback(name="onStateManagerCalled", args=[popup])
		
		pcore.stateManager()
		# del pcore		
		qapp.exec_()
	else:
		qapp = QtWidgets.QApplication.instance()
		if qapp == None:
			qapp = QtWidgets.QApplication(sys.argv)

		
		popup = popupNoButton("Openning State Manager, Please wait", qapp)
		
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
		print("ProjectBrowser no GlobalPcore")
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
		popup = popupNoButton("Openning Project Browser, Please wait", qapp)
		pcore = globalpcore
		pcore.callback(name="onProjectBrowserCalled", args=[popup])
		#
		pcore.projectBrowser()
		#
		qapp.exec_()


def popupError():
	error_box = QtWidgets.QMessageBox()
	# Set the text and title of the error box
	error_box.setText("Prism isn't propperly started!\nPlease Reset Prism from the button in the Prism Menu.")
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
):
	text = str(text)
	title = str(title or "Prism")
	current_directory = os.path.dirname(os.path.abspath(__file__))
	icon = QtGui.QIcon(os.path.join(current_directory, "Fusion.ico"))
	label = QtWidgets.QLabel(text)
	icon_label = QtWidgets.QLabel(text)

	msg = QtWidgets.QDialog()
	msg.setWindowTitle(title)
	msg.setWindowIcon(icon)

	# Set up layout
	layout = QtWidgets.QVBoxLayout()
	layout.addWidget(label)
	msg.setLayout(layout)

	label.setStyleSheet("color: white;")
	msg.setMinimumWidth(200)
	msg.setMinimumHeight(50)
	msg.setStyleSheet("background-color: #31363b;")

	msg.setModal(False)
	if show:
		msg.show()
		qapp.processEvents()

	return msg