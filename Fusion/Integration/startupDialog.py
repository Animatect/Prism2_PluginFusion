import os
import sys
import time
import tkinter as tk

def makeStartupDialog():
    ui = fu.UIManager
    disp = bmd.UIDispatcher(ui)

    root = tk.Tk()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    center_x = screen_width // 2
    center_y = screen_height // 2
    width = 250

    dlg = disp.AddWindow({'WindowTitle': 'Start Prism', 'ID': 'prismstart', 'Geometry': [center_x-(width*0.5), center_y, 250, 80], 'Spacing': 0,},[
        ui.VGroup({'Spacing': 0,},[
            ui.Label({
                "ID": "Label", 
                "Text": "Start Prism !\n",
				"Alignment":{
					"AlignHCenter":True,
					"AlignVCenter":True,
				},
				"WordWrap":True,
            }),
            # Add your GUI elements here:
            ui.HGroup({},[
                # Add foru buttons that have an icon resource attached and no border shading
                ui.Button({
                    'ID': 'B',
                    'Text': 'Start Prism',
                    # 'MinimumSize': [64, 64],
				    # 'Flat': True,
                }),
            ]),
        ]),
    ])

    itm = dlg.GetItems()

    # The window was closed
    def prismstartclose(ev):
        disp.ExitLoop()
    dlg.On.prismstart.Close = prismstartclose


    # Add your GUI element based event functions here:
    def bclick(ev):
        script_path = os.path.join(get_script_dir(), "ResetPrism.py")
        fusion.RunScript(script_path)
        disp.ExitLoop()
    dlg.On.B.Clicked = bclick

    dlg.Show()
    disp.RunLoop()
    dlg.Hide()


def makeEmptyDialog():
    script_path = os.path.join(get_script_dir(), "emptydialog.py")
    fusion.RunScript(script_path)

def get_script_dir():
	# Try to determine the script's directory
	if hasattr(sys, 'frozen'):  # PyInstaller
		script_dir = os.path.dirname(sys.executable)
	else:
		script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
	return script_dir

def checkEmptyDialog():
    uimanager = fu.UIManager
    holders = uimanager.FindWindows("startedprismsession")
    holder = None
    if len(holders) > 0:
        return True
    else:
        return False

if __name__ == "__main__":
    if fusion.GetData('Prism.Startup') or fusion.GetData('Prism.Startup') == None:
        fusion.SetData('Prism.Startup', False)
        time.sleep(1)
        fusion.SetData('Prism.Startup', True)
        if not checkEmptyDialog():
            makeEmptyDialog()
            makeStartupDialog()