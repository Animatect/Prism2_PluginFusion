
import subprocess
import os

def convert_ui_to_py(ui_file):
	base_name, _ = os.path.splitext(ui_file)
	py_file = f"{base_name}_ui.py"
	subprocess.run(["pyside2-uic", ui_file, "-o", py_file])
	return py_file

if __name__ == "__main__":    
	fname = "fus_ImageRender"
	# Get the path of the current script
	script_path = os.path.abspath(__file__)
	# Construct the path to the .ui file (assuming it's in the same directory)
	ui_file_path = os.path.join(os.path.dirname(script_path), fname + ".ui")
	# Convert the .ui file to .py and get the output .py file path
	output_py_path = convert_ui_to_py(ui_file_path)
 
	print(f"Converted .ui file to .py: {output_py_path}")