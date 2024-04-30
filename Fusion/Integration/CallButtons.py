import BlackmagicFusion as bmd

def CallButton(clickedBtn):
    uimanager = bmd.scriptapp("Fusion").UIManager
    holders = uimanager.FindWindows("PrismHolder")
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