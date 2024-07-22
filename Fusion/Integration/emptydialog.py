ui = fu.UIManager
disp = bmd.UIDispatcher(ui)

dlg = disp.AddWindow({'WindowTitle': 'SessionStarted', 'ID': 'startedprismsession', 'Geometry': [100, 100, 200, 50], 'Spacing': 0,},[
    ui.VGroup({'Spacing': 0,},[
    # Add your GUI elements here:
    ui.HGroup({},[
    ui.Label({"ID": "Label", "Text": "Empty",}),
        ]),
    ]),
])
# def _func(ev):
#     disp.ExitLoop()
# dlg.On.startedprismsession.Close = _func

# dlg.Show()
disp.RunLoop()
dlg.Hide()