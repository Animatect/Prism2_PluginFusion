import HolderClass

def launch_prismFusion_menu():
    uimanager = fu.UIManager
    holder = uimanager.FindWindow("PrismHolder")
    try:
        holder.Close()
    except:
        pass  
    holder = HolderClass.PrismHolderClass(fu.UIManager, fusion)
    print("prismHolder Exited")

if __name__ == "__main__":
    launch_prismFusion_menu()