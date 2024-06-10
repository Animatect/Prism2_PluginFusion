import BlackmagicFusion as bmd
from ResetPrism import launch_prismFusion_menu
def CallButton(clickedBtn):
    uimanager = bmd.scriptapp("Fusion").UIManager
    holders = uimanager.FindWindows("PrismHolder")
    holder = None
    if len(holders) > 0:
        holder = holders[len(holders)]
        holder.GetItems()[clickedBtn].Click()
    else:
        print("no holder")