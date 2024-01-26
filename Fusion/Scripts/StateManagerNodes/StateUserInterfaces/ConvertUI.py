fname = "tst_ImageRender"
# fname = "tst_ImportFile"
# fname = "tst_Export"
# fname = "tst_InstallHDA"
# fname = "tst_SaveHDA"
# fname = "tst_Playblast"
# fname = "tst_Dependency"

code = """
import sys, pprint
sys.path.append("C:/Users/richa/Downloads/qtpy-tools-main/qtpy-tools-main")

fname = "%s"
from qtpyuic import compileUi
pyfile = open(fname + "_ui.py", "w")
compileUi(fname + ".ui", pyfile, False, 4, False)


pyfile.close()
print("done")
""" % fname

import subprocess
proc = subprocess.Popen(["python2", "-c", code])
result = proc.communicate()
print(result)