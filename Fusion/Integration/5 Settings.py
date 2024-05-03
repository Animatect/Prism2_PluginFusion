from CallButtons import CallButton
from ResetPrism import launch_prismFusion_menu
if __name__ == "__main__":
    try:
        CallButton('btn_prismsettings')
    except:
        launch_prismFusion_menu()
        CallButton('btn_prismsettings')