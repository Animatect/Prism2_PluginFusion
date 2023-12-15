# -*- coding: utf8 -*-

import os
import subprocess


def environment(module):
	ospath = os.path.dirname(os.__file__)
	path_components = os.path.split(ospath)
	new_path = os.path.join(*path_components[:-1])
	python_location = os.path.join(new_path, "python.exe")
	# Construct the command as a list
	command = [python_location, "-m", "pip", "install", module]

	# Run the command and capture the output
	try:
		result = subprocess.run(command, check=True, capture_output=True, text=True)
		print("Command output:", result.stdout)
	except subprocess.CalledProcessError as e:
		print("Error occurred:", e)
		print("Command output (if available):", e.stdout)

if __name__ == "__main__":
	environment("pyautogui")
	environment("pyperclip")
