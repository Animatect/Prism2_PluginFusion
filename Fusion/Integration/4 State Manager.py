# from openPrismWindows import openPrismStateManager
if __name__ == "__main__":
    # openPrismStateManager()
    uimanager = fu.UIManager
    holders = uimanager.FindWindows("PrismHolder")
    holder = holders[len(holders)]

    holder.GetItems()['btn_statemanager'].Click()