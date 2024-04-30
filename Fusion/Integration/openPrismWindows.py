import sys
import os
import PrismInit
from PySide2 import QtCore, QtGui, QtWidgets

def openProjectBrowser(globalpcore):
	qapp = QtWidgets.QApplication.instance()
	if qapp == None:
		print("wasnonepbr")
		qapp = QtWidgets.QApplication(sys.argv)

	popup = popupNoButton("Openning Project Browser, Please wait", qapp)

	if globalpcore:
		print("pcore existed")
		pcore = globalpcore
	else:
		print("pcore NOT existed")
		pcore = PrismInit.prismInit()

	pcore.callback(name="onProjectBrowserCalled", args=[popup])
	#
	pcore.projectBrowser()
	#
	qapp.exec_()

def runPrismSaveScene(globalpcore):
	qapp = QtWidgets.QApplication.instance()
	if qapp == None:
		qapp = QtWidgets.QApplication(sys.argv)

	if globalpcore:
		print("pcore existed")
		pcore = globalpcore
	else:
		print("pcore NOT existed")
		pcore = PrismInit.prismInit()
	#
	pcore.saveScene()
	#
	qapp.exec_()

def openPrismSaveWithComment(globalpcore):
	qapp = QtWidgets.QApplication.instance()
	if qapp == None:
		qapp = QtWidgets.QApplication(sys.argv)

	if globalpcore:
		print("pcore existed")
		pcore = globalpcore
	else:
		print("pcore NOT existed")
		pcore = PrismInit.prismInit()
	#
	try:
		pcore.saveWithComment()
	except:
		print("problemas")
	#
	qapp.exec_()

def openPrismStateManager(globalpcore):
	qapp = QtWidgets.QApplication.instance()
	if qapp == None:
		print("wasnone")
		qapp = QtWidgets.QApplication(sys.argv)

	
	popup = popupNoButton("Openning State Manager, Please wait", qapp)
	
	if globalpcore:
		print("pcore existed")
		pcore = globalpcore
	else:
		print("pcore NOT existed")
		pcore = PrismInit.prismInit()

	pcore.callback(name="onStateManagerCalled", args=[popup])
	#
	pcore.stateManager()
	#
	qapp.exec_()

def openPrismSettings(globalpcore):
	qapp = QtWidgets.QApplication.instance()
	if qapp == None:
		qapp = QtWidgets.QApplication(sys.argv)

	if globalpcore:
		print("pcore existed")
		pcore = globalpcore
	else:
		print("pcore NOT existed")
		pcore = PrismInit.prismInit()
	#
	pcore.prismSettings()
	#
	qapp.exec_()


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