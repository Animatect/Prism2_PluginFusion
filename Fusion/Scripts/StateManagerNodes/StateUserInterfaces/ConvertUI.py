
import subprocess
import os
import time

def replace_pyside6_with_qtpy(file_path):
	if not os.path.exists(file_path):
		print(f"File not found: {file_path}")
		return
	
	try:
		# Step 1: Read the content of the file
		with open(file_path, 'r') as file:
			content = file.read()
		
		# Step 2: Replace 'PySide6' with 'qtpy'
		modified_content = content.replace('PySide6', 'qtpy')
		
		# Step 3: Write the modified content back to the file
		with open(file_path, 'w') as file:
			file.write(modified_content)
		
		print(f"Successfully replaced 'PySide6' with 'qtpy' in {file_path}")
	except Exception as e:
		print(f"An error occurred: {e}")


def convert_ui_to_py(ui_file):
	base_name, _ = os.path.splitext(ui_file)
	py_file = f"{base_name}_ui.py"
	subprocess.run(["pyside6-uic", "--star-imports",  ui_file, "-o", py_file])
	return py_file

if __name__ == "__main__":
	fnames = ["fus_ImageRender", "fus_NetRender"]
	for fname in fnames:
		# Get the path of the current script
		script_path = os.path.abspath(__file__)
		# Construct the path to the .ui file (assuming it's in the same directory)
		ui_file_path = os.path.join(os.path.dirname(script_path), fname + ".ui")
		# Convert the .ui file to .py and get the output .py file path
		output_py_path = convert_ui_to_py(ui_file_path)
	
		print(f"Converted .ui file to .py: {output_py_path}")

		
		# Example usage
		timmer = 0
		file_path = os.path.join(os.path.dirname(script_path), f"{fname}_ui.py")  # Replace with the path to your .py file
		print("filepath: ", file_path)
		while timmer < 2:
			time.sleep(1)
			timmer += 1
			print(timmer)
		replace_pyside6_with_qtpy(file_path)