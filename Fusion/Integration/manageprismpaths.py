import os
import sys
import platform

startEnv = os.environ.copy()

# check if python 2 or python 3 is used
# if sys.version[0] == "3":
#     pVersion = 3
#     if sys.version[2] == "7":
#         pyLibs = "Python37"
#     elif sys.version[2] == "9":
#         pyLibs = "Python39"
#     else:
#         pyLibs = "Python310"
# else:
#     pVersion = 2
#     pyLibs = "Python27"
#Commented code is left in case python 3 versions are needed at some point.
pyLibs = "Python3"

prismRoot = PRISMROOT
prismLibs = os.getenv("PRISM_LIBS")

if not prismLibs:
    prismLibs = prismRoot

if not os.path.exists(os.path.join(prismLibs, "PythonLibs")) and os.getenv("PRISM_NO_LIBS") != "1":
    raise Exception('Prism: Couldn\'t find libraries. Set "PRISM_LIBS" to fix this.')

scriptPath = os.path.join(prismRoot, "Scripts")
if scriptPath not in sys.path:
    sys.path.append(scriptPath)

pyLibPath = os.path.join(prismLibs, "PythonLibs", pyLibs)
cpLibs = os.path.join(prismLibs, "PythonLibs", "CrossPlatform")

if cpLibs not in sys.path:
    sys.path.append(cpLibs)

if pyLibPath not in sys.path:
    sys.path.append(pyLibPath)

if sys.version[0] == "3":
    py3LibPath = os.path.join(prismLibs, "PythonLibs", "Python3")
    if py3LibPath not in sys.path:
        sys.path.append(py3LibPath)

    pySidePath = os.path.normpath(os.path.join(py3LibPath, "PySide"))
    if pySidePath not in sys.path:
        sys.path.append(pySidePath)

    if platform.system() == "Windows":
        sys.path.insert(0, os.path.join(py3LibPath, "win32"))
        sys.path.insert(0, os.path.join(py3LibPath, "win32", "lib"))
        pywinpath = os.path.join(prismLibs, "PythonLibs", pyLibs, "pywin32_system32")
        sys.path.insert(0, pywinpath)
        os.environ["PATH"] = pywinpath + os.pathsep + os.environ["PATH"]
        if hasattr(os, "add_dll_directory") and os.path.exists(pywinpath):
            os.add_dll_directory(pywinpath)
