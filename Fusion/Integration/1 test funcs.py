import os
import sys
import re





def get_loader_channels(tool):
	# Get all loader channels and filter out the ones to skip
	skip = {
		"r", 
		"red", 
		"g", 
		"green", 
		"b", 
		"blue", 
		"a", 
		"alpha",
		"SomethingThatWontMatchHopefully"
	}
	source_channels = tool.Clip1.OpenEXRFormat.RedName.GetAttrs("INPIDT_ComboControl_ID")
	all_channels = []

	for channel_name in source_channels.values():
		if channel_name not in skip:
			all_channels.append(channel_name)

	# Sort the channel list
	sorted_channels = sorted(all_channels)

	return sorted_channels

def get_channel_data(loader_channels):
	channel_data = {}

	for channel_name in loader_channels:
		# Get prefix and channel from full channel name using regex
		match = re.match(r"(.+)\.(.+)", channel_name)
		if match:
			prefix, channel = match.groups()

			# Use setdefault to initialize channels if prefix is encountered for the first time
			channels = channel_data.setdefault(prefix, [])

			# Add full channel name to assigned channels of current prefix
			channels.append(channel_name)

	return channel_data

def GetLoaderClip(tool):
	loader_clip = tool.Clip[fusion.TIME_UNDEFINED]
	if loader_clip:        
		return loader_clip
	
	print("Loader contains no clips to explore")
	return 

def move_loaders(org_x_pos, org_y_pos, loaders):
	comp = fusion.GetCurrentComp()
	flow = comp.CurrentFrame.FlowView
	y_pos_add = 1

	for count, ldr in enumerate(loaders, start=0):
		flow.SetPos(ldr, org_x_pos, org_y_pos + y_pos_add * count)

def process_multichannel(tool):
	comp = fusion.GetCurrentComp()
	loader_channels = get_loader_channels(tool)
	channel_data = get_channel_data(loader_channels)
	flow = comp.CurrentFrame.FlowView
	x_pos, y_pos = flow.GetPosTable(tool).values()

	loaders_list = []

	comp.StartUndo()
	comp.Lock()

	# Invalid names mapping
	invalid_names = {
		'RedName': 'CHANNEL_NO_MATCH',
		'GreenName': 'CHANNEL_NO_MATCH',
		'BlueName': 'CHANNEL_NO_MATCH',
		'AlphaName': 'CHANNEL_NO_MATCH',
		'XName': 'CHANNEL_NO_MATCH',
		'YName': 'CHANNEL_NO_MATCH',
		'ZName': 'CHANNEL_NO_MATCH',
	}

	# Update the loader node channel settings
	for prefix, channels in channel_data.items():
		ldr = comp.Loader({'Clip': GetLoaderClip(tool)})

		# Replace invalid EXR channel names with placeholders
		ldr.SetAttrs({'TOOLB_NameSet': True, 'TOOLS_Name': prefix})
		for name, placeholder in invalid_names.items():
			setattr(ldr.Clip1.OpenEXRFormat, name, placeholder)

		# Refresh the OpenEXRFormat setting using real channel name data in a 2nd stage
		for channel_name in channels:
			channel = re.search(r"\.([^.]+)$", channel_name).group(1).lower()

			# Dictionary to map channel types to attribute names
			channel_attributes = {
				'r': 'RedName', 'red': 'RedName',
				'g': 'GreenName', 'green': 'GreenName',
				'b': 'BlueName', 'blue': 'BlueName',
				'a': 'AlphaName', 'alpha': 'AlphaName',
				'x': 'RedName',
				'y': 'GreenName',
				'z': 'BlueName',
			}

			# Handle channels using the mapping
			if channel in channel_attributes:
				setattr(ldr.Clip1.OpenEXRFormat, channel_attributes[channel], channel_name)

			# Handle C4D style channels
			else:
				my_table_of_phrases = re.split(r'\.', channel_name)
				last_item = my_table_of_phrases[-1]

				if last_item in channel_attributes:
					setattr(ldr.Clip1.OpenEXRFormat, channel_attributes[last_item], channel_name)

		loaders_list.append(ldr)

	move_loaders(x_pos, y_pos, loaders_list)

	tool.Delete()
	comp.Unlock()
	comp.EndUndo()
	# comp.SetActiveTool(tool)

if __name__ == "__main__":
	ld = comp.beauty
	# lc = get_loader_channels(ld)
	# print(lc)
	# print("#########")
	# cd = get_channel_data(lc)
	process_multichannel(ld)
	

