# from openPrismWindows import openProjectBrowser
if __name__ == "__main__":
    # openProjectBrowser()
    uimanager = fu.UIManager
    holders = uimanager.FindWindows("PrismHolder")
    holder = holders[len(holders)]

    holder.GetItems()['btn_projectbrowser'].Click()