import os
import sys
import platform
import PrismInit
from PySide2 import QtCore, QtGui, QtWidgets

class PrismFusionMenu(QtWidgets.QWidget):
	def __init__(self, pcore, *args, **kwargs):
		#initialize parent class
		super(PrismFusionMenu, self).__init__(*args, **kwargs)
		#set prismcore
		self.pcore = pcore
		self.menuLabel = "Prism"
		self.setObjectName(self.menuLabel)

		icon_path = PrismInit.getIconPath()
		icon = QtGui.QIcon(icon_path)
		self.setWindowIcon(icon)

		# Set the initial width of the window
		self.resize(200, 0)

		self.setWindowFlags(
			QtCore.Qt.Window
			| QtCore.Qt.CustomizeWindowHint
			| QtCore.Qt.WindowTitleHint
			| QtCore.Qt.WindowMinimizeButtonHint
			| QtCore.Qt.WindowCloseButtonHint
			| QtCore.Qt.WindowStaysOnTopHint
		)
		self.render_mode_widget = None
		self.setWindowTitle(self.menuLabel)

		asset_label = QtWidgets.QLabel("Prism Fusion", self)
		asset_label.setAlignment(QtCore.Qt.AlignHCenter)

		ProjectBrowser_btn = QtWidgets.QPushButton("Project Browser", self)
		SaveVersion_btn = QtWidgets.QPushButton("Save Version", self)
		SaveComment_btn = QtWidgets.QPushButton("Save Comment", self)
		StateManager_btn = QtWidgets.QPushButton("State Manager", self)
		PrismSettings_btn = QtWidgets.QPushButton("Prism Settings", self)
		

		layout = QtWidgets.QVBoxLayout(self)
		layout.setContentsMargins(10, 20, 10, 20)

		layout.addWidget(asset_label)

		layout.addSpacing(20)

		layout.addWidget(ProjectBrowser_btn)

		layout.addSpacing(20)

		layout.addWidget(SaveVersion_btn)
		layout.addWidget(SaveComment_btn)

		layout.addSpacing(20)

		layout.addWidget(StateManager_btn)
		layout.addWidget(PrismSettings_btn)

		self.setLayout(layout)

		# Store reference so we can update the label
		self.asset_label = asset_label

		ProjectBrowser_btn.clicked.connect(self.on_ProjectBrowser_clicked)
		SaveVersion_btn.clicked.connect(self.on_SaveVersion_clicked)
		SaveComment_btn.clicked.connect(self.on_SaveComment_clicked)
		StateManager_btn.clicked.connect(self.on_StateManager_clicked)
		PrismSettings_btn.clicked.connect(self.on_PrismSettings_clicked)

	def on_ProjectBrowser_clicked(self):
		if platform.system() == "Linux":
			self.pcore.projectBrowser()
			qApp.exec_()
		else:
			self.pcore.projectBrowser()

		return {"FINISHED"}

	def on_SaveVersion_clicked(self):
		self.pcore.saveScene()

	
	def on_SaveComment_clicked(self):
		self.pcore.saveWithComment()

	def on_StateManager_clicked(self):
		self.pcore.stateManager()

	def on_PrismSettings_clicked(self):
		self.pcore.prismSettings()


def launch_prismFusion_menu():
	#It is necessary to make or fetch a QApplication instance before importing PrismCore
	qapp = QtWidgets.QApplication.instance()
	if qapp == None:
		qapp = QtWidgets.QApplication(sys.argv)

	pcore = PrismInit.prismInit()
	pcore.setActiveStyleSheet("Fusion")
	
	splitprefspath = pcore.getUserPrefConfigPath().split("\\")
	splitprefspath[-1] = "PrismFusionMenu.lock"
	lock_file_path = "\\".join(splitprefspath)
	#print(lock_file_path)

	# Check if the lock file already exists
	if os.path.exists(lock_file_path):
		print("Another instance is already running.")
		sys.exit(0)

	try:
		# Try to open the lock file for writing
		with open(lock_file_path, "w") as lock_file:
			pass  # Just open and immediately close the file		

		pf_menu = PrismFusionMenu(pcore)
		pf_menu.show()

		result = qapp.exec_()
		print("Shutting down..")

		# Close and delete the lock file when done
		lock_file.close()
		os.remove(lock_file_path)

		sys.exit(result)

	except IOError:
		print("Error creating the lock file.")
		sys.exit(1)


if __name__ == "__main__":
	launch_prismFusion_menu()
