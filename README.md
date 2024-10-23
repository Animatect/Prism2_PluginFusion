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
Prism functions are accessed through the Prism menu in the top bar of Fusion Studio's UI.

TODO

TODO - NEW PIC AFTER MENU CLEANUP
![Prism Menu](https://github.com/user-attachments/assets/3e5fca21-8ca6-458c-a593-b0398d207930)


<br/>

### **Rendering**

Prism's State Manager is used for rendering images from Fusion into the Prism pipeline and functions similar to other DCC integrations.  The main render state is the ImageRender which allows the user to


### **Importing**




<br/><br/>


## **Issues / Suggestions**

For any bug reports or suggestions, please add to the GitHub repo I/ssues or Projects tabs.
