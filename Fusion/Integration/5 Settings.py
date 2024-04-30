# from openPrismWindows import openPrismSettings
if __name__ == "__main__":
    # openPrismSettings()
    uimanager = fu.UIManager
    holders = uimanager.FindWindows("PrismHolder")
    holder = holders[len(holders)]

    holder.GetItems()['btn_prismsettings'].Click()