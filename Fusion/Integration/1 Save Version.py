# from openPrismWindows import runPrismSaveScene
if __name__ == "__main__":
    # runPrismSaveScene()
    uimanager = fu.UIManager
    holders = uimanager.FindWindows("PrismHolder")
    holder = holders[len(holders)]

    holder.GetItems()['btn_saveversion'].Click()