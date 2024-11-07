# **Importing**
Importing images into Fusion can be done utilizing the native method by drag/dropping of course.  But the Prism integration provides a better process utilizing the Project Browser.

To import into Fusion first launch the Project Browser from the Prism menu in Fusion, and right click on the image in the viewer.

![PB Rightclick](DocsImages/PB-Rightclick.png)

Depending on the type of image file (video file, image sequence, still image) various options will be displayed allowing the user to import as desired (see sections below).

### **Positioning:**
By default, the integrtion image import will try and position all Loaders to the left side of the Comp and stack them vertically to stay uncluttered (see "Import Without Wireless/Sorting" below to disable).

### **Import Without Wireless/Sorting:**
By default, this checkbox is unchecked and will provide additional automation to the import.  The automation will consist of positioning the Loader in a stack to the left side of the Flow in the Comp, and adds a set of Wireless nodes (In and Out) to the Loader.

By unchecking this checkbox will disable the auto positioning/stacking, and place the Loader into the Flow the native "Fusion" way.  This means if a node is selected, it will add the Loader and connect it to the selected node.  If no node is selected, the Loader will be added to the last clciked position in the Flow.

Also if the checkbox is checked, the auto Wireless nodes will not be added and the Loader will be added alone as a single node.


<br/>
TODO:

- All AOVs
- Current AOV
- Split EXR
- Updating
- Positioning
- Without Wireless/Sorting

<br/>

jump to:

[**Interface**](Interface.md)

[**Rendering**](Rendering.md)
