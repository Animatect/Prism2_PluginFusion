###### VIEW FOCUS ######

# 
def calcNewPosition(toolX, toolY):
    deltax = toolX - (-0.5)
    deltay = toolY - (-0.5)
    # the ratio is the ammount the viewer moves to center the node for each 0.5 units
    xscaled_delta = deltax * (55/0.5)
    yscaled_delta = deltay * (16.5/0.5)

    return xscaled_delta, yscaled_delta

# 
def focusOnTool(comp, tool, scalefactor = 0.5):
    flow = comp.CurrentFrame.FlowView

    # tool = comp.Background1
    Xpos, Ypos = flow.GetPosTable(tool).values()
    x, y = calcNewPosition(Xpos, Ypos)

    new_bookmark:dict = {'__flags': 1048832, 
                    'Offset': {'__flags': 256, 1.0: x, 2.0: y}, 
                    'Name': 'prismRefocus', 
                    'Scale': scalefactor}
    
    bookmarks = flow.GetBookmarkList()
    if bookmarks:
        next_key = max(bookmarks.keys()) + 1.0
        bookmarks[next_key] = new_bookmark
    else:
        bookmarks = {}
        bookmarks[1] = new_bookmark

    flow.SetBookmarkList(bookmarks)
    flow.GoToBookmark('prismRefocus')

    # flow.DeleteBookmark('prismRefocus')
    last_item = bookmarks.popitem()
    flow.SetBookmarkList(bookmarks)

########################

def sm_view_FocusStateTool():
    comp = fusion.CurrentComp
    focustool = comp.ActiveTool

    if focustool:
        focusOnTool(comp, focustool)
    else:
        pass

if __name__ == "__main__":
    sm_view_FocusStateTool()