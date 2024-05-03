from CallButtons import CallButton
from ResetPrism import launch_prismFusion_menu
if __name__ == "__main__":
    try:
        CallButton('btn_statemanager')
    except:
        launch_prismFusion_menu()
        CallButton('btn_statemanager')