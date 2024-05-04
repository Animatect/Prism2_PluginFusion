import BlackmagicFusion as bmd
from ResetPrism import launch_prismFusion_menu
def CallButton(clickedBtn):
    uimanager = bmd.scriptapp("Fusion").UIManager
    holders = uimanager.FindWindows("PrismHolder")
    holder = None
    if len(holders) > 0:
        holder = holders[len(holders)]
    else:
        launch_prismFusion_menu()
        holder = holders[len(holders)]
    # buttons = [
    #     "btn_projectbrowser",
    #     "btn_savecomment",
    #     "btn_statemanager",
    #     "btn_prismsettings"
    # ]
    # for btn in buttons:
    #     holder.GetItems()[btn].SetEnabled(False)

    # holder.GetItems()[clickedBtn].SetEnabled(True)
    holder.GetItems()[clickedBtn].Click()

    # for btn in buttons:
    #     holder.GetItems()[btn].SetEnabled(True)