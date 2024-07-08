@echo off
echo Running Python commands...
python -c "import pygetwindow as gw; gw.getWindowsWithTitle('Fusion Studio - [')[0].activate()"
@REM pause
exit
