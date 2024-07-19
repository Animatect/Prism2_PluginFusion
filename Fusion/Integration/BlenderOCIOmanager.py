import os

def get_installed_blender_versions(blender_directory):
	versions = []

	if os.path.exists(blender_directory):
		for item in os.listdir(blender_directory):
			item_path = os.path.join(blender_directory, item)
			if os.path.isdir(item_path):
				versions.append(item)
	
	if len(versions)==0:
		versions.append("No Blender Versions found")

	return versions

def find_LastClickPosition():
	comp = fusion.GetCurrentComp()
	flow = comp.CurrentFrame.FlowView
	posNode = comp.AddToolAction("Background")
	x,y = flow.GetPosTable(posNode).values()
	posNode.Delete()

	return x,y

## UI ##

ui = fu.UIManager
disp = bmd.UIDispatcher(ui)
blender_directory = "C:\\Program Files\\Blender Foundation"

dlg = disp.AddWindow({"WindowTitle": "Blender OCIO MAnager", "ID": "BlenderOCIO", "Geometry": [100, 100, 300, 70], "Spacing": 10,},[
	ui.VGroup({"ID": "root",},[
		# Add your GUI elements here:
		ui.ComboBox({
				"ID": "MyCombo", 
				"Text": "Blender Versions"
			}),
		ui.Button({
				'ID': 'B',
				'Text': 'Create OCIO Node',
			}),
	]),
])

itm = dlg.GetItems()

# The window was closed
def _func(ev):
	disp.ExitLoop()
dlg.On.BlenderOCIO.Close = _func

# Add your GUI element based event functions here:

def indexchanged(ev):
	# if itm['MyCombo'].CurrentIndex == 0:
	pass

def createClicked(ev):
	comp = fusion.GetCurrentComp()
	flow = comp.CurrentFrame.FlowView
	blenderversion = itm['MyCombo'].CurrentText.split(" ")[1]
	ociopath = os.path.join(blender_directory, itm['MyCombo'].CurrentText, blenderversion,"datafiles","colormanagement","config.ocio")
	if os.path.isfile(ociopath):
		x,y = find_LastClickPosition()
		flow.Select()
		node = comp.AddTool("OCIOColorSpace",x,y)
		node.SetAttrs({'TOOLS_Name':f'Blender_OCIO_{blenderversion}_'})
		flow.Select(node, True)
		nodename = node.GetAttrs('TOOLS_Name')
		comp.Copy(node)
		buffer = fusion.GetClipboard()
		newdata = {'OCIOConfig': {
					'__ctor': 'Input',
					'__flags': 1048832,
					'Value': ociopath
				}}
		buffer['Tools'][nodename]['Inputs'].update(newdata)
		node.Delete()
		comp.Paste(buffer)
		node = comp.ActiveTool
		flow.SetPos(node, x, y)
	else:
		print("File does not exists")

dlg.On.B.Clicked = createClicked
dlg.On.MyCombo.CurrentIndexChanged = indexchanged

# Add the items to the ComboBox menu
for version in get_installed_blender_versions(blender_directory):
	itm['MyCombo'].AddItem(version)



dlg.Show()
disp.RunLoop()
dlg.Hide()