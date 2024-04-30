# from openPrismWindows import openPrismSaveWithComment
if __name__ == "__main__":
    # openPrismSaveWithComment()
    uimanager = fu.UIManager
    holders = uimanager.FindWindows("PrismHolder")
    holder = holders[len(holders)]

    holder.GetItems()['btn_savecomment'].Click()