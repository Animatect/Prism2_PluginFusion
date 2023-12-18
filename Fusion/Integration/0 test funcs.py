# from ProjectBrowser import openProjectBrowser
# openProjectBrowser()

import os
import sys
import platform
import PrismInit
from PySide2 import QtCore, QtGui, QtWidgets

qapp = QtWidgets.QApplication.instance()
if qapp == None:
	qapp = QtWidgets.QApplication(sys.argv)

pcore = PrismInit.prismInit()
pcore.setActiveStyleSheet("Fusion")
#pcore.projectBrowser()
pcore.pb.close()
print(pcore.pb)

qapp.exec_()