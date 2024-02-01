import sys
import PrismInit
from PySide2 import QtCore, QtGui, QtWidgets

def openProjectBrowser():
	qapp = QtWidgets.QApplication.instance()
	if qapp == None:
		qapp = QtWidgets.QApplication(sys.argv)

	pcore = PrismInit.prismInit()
	pcore.setActiveStyleSheet("Fusion")
	pcore.projectBrowser()

	qapp.exec_()

def runPrismSaveScene():
	qapp = QtWidgets.QApplication.instance()
	if qapp == None:
		qapp = QtWidgets.QApplication(sys.argv)

	pcore = PrismInit.prismInit()
	pcore.setActiveStyleSheet("Fusion")
	pcore.saveScene()

	qapp.exec_()

def openPrismSaveWithComment():
	qapp = QtWidgets.QApplication.instance()
	if qapp == None:
		qapp = QtWidgets.QApplication(sys.argv)

	pcore = PrismInit.prismInit()
	pcore.setActiveStyleSheet("Fusion")
	pcore.saveWithComment()

	qapp.exec_()

def openPrismStateManager():
	qapp = QtWidgets.QApplication.instance()
	if qapp == None:
		qapp = QtWidgets.QApplication(sys.argv)

	pcore = PrismInit.prismInit()
	pcore.setActiveStyleSheet("Fusion")
	pcore.stateManager()

	qapp.exec_()

def openPrismSettings():
	qapp = QtWidgets.QApplication.instance()
	if qapp == None:
		qapp = QtWidgets.QApplication(sys.argv)

	pcore = PrismInit.prismInit()
	pcore.setActiveStyleSheet("Fusion")
	pcore.prismSettings()

	qapp.exec_()