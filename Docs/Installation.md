
Copy the directory named "Fusion" to a directory of your choice, or a Prism2 plugin directory.

It is suggested to have the Fusion plugin with the other DCC plugins in: *{drive}\ProgramData\Prism2\plugins*

Prism's default plugin directories are: *{installation path}\Plugins\Apps* and *{installation Path}\Plugins\Custom*.

You can add the additional plugin search paths in Prism2 settings.  Go to Settings->Plugins and click the gear icon.  This opens a dialogue and you may add additional search paths at the bottom.

Once added, select the "Add existing plugin" (plus icon) and navigate to where you saved the Fusion folder.

![Adding Plugin](DocsImages/Adding_Plugin.png)

<br/>

![Plugin Folder](https://github.com/user-attachments/assets/3858e04c-60e1-454c-91b1-7ba945d3d005)


Afterwards, you can select the Plugin autoload as desired:

![Autoload](https://github.com/user-attachments/assets/f254c8e9-9ff9-40ca-95f7-4a2fdb20946a)

To add the integration, go to the "DCC Apps" -> "Fusion" tab.  Then click the "add" button and navigate to the folder containing Fusion's "Scripts" directory - this is usually at "../AppData/Roaming/Blackmagic Design/Fusion".  If there is more than one version of Fusion installed, it is advisable to set the executable in the "Override" box in the DCC settings.

![Add DCC apps](https://github.com/user-attachments/assets/8d4d16ac-38d9-4849-ba8d-d9be7a077fca)
