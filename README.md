# Prism2_PluginFusion
 Fusion plugin for the Prism Pipeline Framework

# DESCRIPTION
This plugin adds prism functionality to bmd Fusion:
- Loader and version management.
- Products import and version management.
- Saver Management through the State Manager.
- Blender Camera import.
- Blender OCIO detection (as long as Blender is installed in degault location).
- Network render management.
- Unified Prism Core (Prism 1 plugin would make 1 core for each operation).
- Usual Prism functionality like scene version management, Project Browser, etc.

The plugin can be launched from the startup dialog, if this doesn´t work it can be launched from the prism menu using the *START PRISM* entry.
This plugin has been tested in very controlled environments, any bugs found please report them as an issue in this github page.


# REQUIREMENTS
This plugin has been tested with Fusion 18 but should work with any Fusion that runs python 3.9 or upwards and pyside6

# INSTALLATION
- Unzip and paste the Fusion folder (contains integration, presets, scripts, userinterfaces) in the location you want the plugin to be.
- Go to settings > Plugins and in the top-right corner there is a cogwheel icon that reads Manage plugins paths...
- in plugins paths press the + button and add the fusion folder, the new path must read something like C:\ProgramData\Prism2\Plugins\Fusion.
- Another way is to add the parent folder to Plugin search paths and let prism look for the plugin.
- Press ok and restart prism
- Go to settings DCC apps > Fusion tab and press the button that reads "add", press ok in the default location and that's it.