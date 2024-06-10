from CallButtons import CallButton
from ResetPrism import launch_prismFusion_menu
from PrismInit import checkThirdParty
import openPrismWindows
if __name__ == "__main__":
    checkThirdParty()
    try:
        CallButton('btn_projectbrowser')
    except:
        openPrismWindows.openPrismSettings()