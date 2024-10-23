# **BMD Fusion Studio Integration for Prism Pipeline 2**
A Fusion Studio integration to be used with version 2 of Prism Pipeline 

Prism automates and simplifies the workflow of animation and VFX projects.

You can find more information on the website:

https://prism-pipeline.com/


## **Notes**

- This intergration has been tested with Fusion Studio versions 18 and 19.
- This integration does not work with Resolve Fusion, thought it is planned for the future.
- To aid is use, tooltips are provided throughout.
<br/><br/>

## **Installation**

This plugin is for Windows only, as Prism2 only supports Windows at this time.

TODO:  You can either download the latest stable release version from: [Latest Release](https://github.com/Animatect/Prism2_PluginFusion/releases/latest)

TODO:  or download the current code zipfile from the green "Code" button above or on [Github](https://Animatect/Prism2_PluginFusion)

Copy the directory named "Fusion" to a directory of your choice, or a Prism2 plugin directory.

It is suggested to have the Fusion plugin with the other DCC plugins in: *{drive}\ProgramData\Prism2\plugins*

Prism's default plugin directories are: *{installation path}\Plugins\Apps* and *{installation Path}\Plugins\Custom*.

You can add the additional plugin search paths in Prism2 settings.  Go to Settings->Plugins and click the gear icon.  This opens a dialogue and you may add additional search paths at the bottom.

Once added, select the "Add existing plugin" (plus icon) and navigate to where you saved the Fusion folder.

![Adding Plugin](https://github.com/user-attachments/assets/59a083a6-88e0-439e-a228-51112e509b76)

<br/>

![Plugin Folder](https://github.com/user-attachments/assets/3858e04c-60e1-454c-91b1-7ba945d3d005)


Afterwards, you can select the Plugin autoload as desired:

![Autoload](https://github.com/user-attachments/assets/f254c8e9-9ff9-40ca-95f7-4a2fdb20946a)

To add the integration, go to the "DCC Apps" -> "Fusion" tab.  Then click the "add" button and navigate to the folder containing Fusion's "Scripts" directory - this is usually at "../AppData/Roaming/Blackmagic Design/Fusion".  If there is more than one version of Fusion installed, it is advisable to set the executable in the "Override" box in the DCC settings.

![Add DCC apps](https://github.com/user-attachments/assets/8d4d16ac-38d9-4849-ba8d-d9be7a077fca)

<br/>

## **Usage**

### **Menu**
Prism functions are accessed through the Prism menu in the top bar of Gimp's UI.  The communication server must be started before Prism functions may be executed.  This opens a socket port between Prism and the Gimp integration only, and there is no data communicated outside the local computer.  You can change the port number in Settings->DCCs->Gimp if needed.

![Prism Menu](https://github.com/AltaArts/Gimp_Integration--Prism-Plugin/assets/86539171/46afa882-72d0-4153-b7bf-ae9cac63ebfc)

<br/>

### **Messages / Logging**

Messages can be displayed several ways, with several levels of detail.  Gimp displays messages through the status bar at the bottom, and the "Error Console".

![Gimp Error Console](https://github.com/AltaArts/Gimp_Integration--Prism-Plugin/assets/86539171/67df98e5-ae36-4a11-a60d-dbd3bbfdb3c5)

There are three level of message display, but all messages will always be saved in the log.  With "Log Only", no messages will be displayed in the Gimp UI.  "Minimal" will display some messages that may be useful to the user such as "Starting Server".  "All" will display all messages in the UI. 

![Log Menu](https://github.com/AltaArts/Gimp_Integration--Prism-Plugin/assets/86539171/f0de1aef-72b2-4b4c-bc5f-495414f321a6)

Keep in mind that having "All" messages displayed will show many messages and slightly slow the interface, thus it is suggested to have the message level at "Minimal".  If the Error Console is docked in a widow with other tabs, new messages will move the focus to the Error Console so it is suggested to have the Error Console docked into its own window.

![Suggested UI](https://github.com/AltaArts/Gimp_Integration--Prism-Plugin/assets/86539171/30882315-8770-4f04-a863-afea2f504e82)



The Gimp log may be viewed by opening the directory with the "open Log" button in Settings->DCCs->Gimp.  The log will update until it reaches the max size limit set in settings, and then will be renamed to "_OLD" with a maximum of those two files.  By default, the logs are saved in the Gimp plugin directory and you can change the save location in the settings.
<br/><br/>

### **Exporting**

To export (save) images we use the StateManager via a custom Gimp_Render state.  Various output image formats are supported, with more being added.  The current image's details will be displayed along with format-specific settings for each state.  A user has the option to scale the resulting image, or change the color mode and bit depth of the resulting export.  These changes will not alter the scenefile.

![Gimp Render](https://github.com/AltaArts/Gimp_Integration--Prism-Plugin/assets/86539171/5d989db8-205d-4484-b5e6-d64528bad250)

If the lowest layer of the scenefile image has an alpha channel, and the export format is not an alpha format (not RGBA or GRAYA), then an option will be displayed to select the desired background to be used.

![AlphaFill](https://github.com/AltaArts/Gimp_Integration--Prism-Plugin/assets/86539171/fe812ace-7ff5-4862-9915-b5a6ef12ed3e)


A user may export to .psd using the StateManager.  By default the resulting .psd will be saved in the selected Identifier in Media tab.  There is also and option to export the .psd as a scenefile under the Scenefiles tab.

![SM psd](https://github.com/AltaArts/Gimp_Integration--Prism-Plugin/assets/86539171/08b12333-d439-4690-b0cc-1cc29c9a311d)

This will export the .psd next to the .xcf using the same version number and details.

![PSD Version](https://github.com/AltaArts/Gimp_Integration--Prism-Plugin/assets/86539171/185bc704-922c-41df-81e0-315f7da7ee2a)


<br/><br/>


## **Issues / Suggestions**

For any bug reports or suggestions, please add to the GitHub repo.
