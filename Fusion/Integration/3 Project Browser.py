from CallButtons import CallButton
from ResetPrism import launch_prismFusion_menu
if __name__ == "__main__":
    #uimanager = fu.UIManager
    try:
        CallButton('btn_projectbrowser')
    except:
        launch_prismFusion_menu()
        CallButton('btn_projectbrowser')