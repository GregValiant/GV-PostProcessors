# GregValiant's PostProcessors for PrusaSlicer, OrcaSlicer, Bambu Studio, and Creality Print

PLEASE NOTE:  
- These post-processors are "python scripts" and Python must be installed on your computer. 
- "GregValiants_AddLayerNumbers" must be run first in order for the other scripts to work (they will search for Layer Numbers).  

All the slicers require that the post processors are entered into the "Others | Output Options | Post-processing scripts" text box in this form...  
"C:\Users\grego\AppData\Local\Programs\Python\Python313\python.exe" "C:\Users\grego\Documents\PrusaScripts\GregValiants_AddLayerNumbers.py";  
The quotation marks are necessary on my installation of Windows 10 Pro.  For Linux or Mac you will need to adjust as needed.  

The first part of the line is the path and file name for "python.exe" (on your computer) followed by a single "space".  
The second part is the path and file name of the post-processor followed by a semi-colon.  
Each post-processor requires the same form and must be on separate lines in the text box.  
For multiple post-processors the "Post-processing scripts" textbox would look something like this...  

*<path\python.exe><1space><path\post-processor file name><;>*  
Github is shortening this but each "path + post processor" should be on a single line.  (It will look odd in the short textboxes of Orca and Bambu.)  
"C:\Users\PathToPython\Python313\python.exe" "C:\Users\grego\Documents\PrusaScripts\GregValiants_AddLayerNumbers.py";  
"C:\Users\PathToPython\Python313\python.exe" "C:\Users\grego\Documents\PrusaScripts\GregValiants_SearchAndReplace.py";  
"C:\Users\PathToPython\Python313\python.exe" "C:\Users\grego\Documents\PrusaScripts\GregValiants_AdvancedFanControl.py";  

*I keep a simple text file with the above lines in it.  When I need to use a script, I open that file and copy the line and paste it into the post-processor box of the slicer.*  

As each post-processor runs it will open a command window and you will be asked for your input.  The scripts attempt to catch typos, but you need to be careful.  

Slic3R based script changes:  
2/25/2025  Added the Display Layer and ET script.  
3/1/2025   Added Pause at Layer.  
3/4/2025   Added Insert at Layer Change  
3/12 and 3/13/2025  Adjusted scripts to utilize variables from the slicers (instead of parsing the gcode).  Improved performance.  
3/13/2025  Change the layer_change insertion from ";Layer:" to ";Layer#:" to avoid conflicts with the slicer layer_change_gcode.  
3/16/2025   DisplayInfoAndET  Revised the calculation of the remaining time.  
3/18/2025   Added support for Creality Print.  

-----------------------------------------------------------------------------  
**Add Layer Numbers:**  
2/14/2025  My test model is 50mm tall.  When I slice at 0.2 layer height and 0.2 initial layer height and with "Generate Support Material" turned off, it is 250 layers.  That's what I expect and what "Add Layer Numbers" comes up with.  If I turn "Generate Support Material" on - it is 470 layers in Prusa, 379 layers in Orca, and 350 layers in Bambu.  Go figure.  The script will make the adjustment when supports are enabled or disabled.  The layer numbering in the gcode will match the slicer preview.  
The script will go through the gcode and look for ";LAYER_CHANGE" ("; CHANGE_LAYER" in Bambu) and add a line below that ";Layer:XX".  
The layer numbers will match the preview.  ";Layer:1" might be the first layer of the model, or might be the first layer of a raft with the model up higher.  
*Please NOTE:* If your 'Before_Layer_Change' Gcode has ';Layer{layer_num+1}' or something similar, you should remove it or you will end up with double ";layer:X" lines.  The slicer adds it's line after the first layer and the text can be altered by a user so it can't be counted on.
*All of my other scripts require that 'Add Layer Numbers' runs first.*  It must only be run once.  

**Search and Replace**  
Requires "Add Layer Numbers" to run before it.
The review will include the settings:  
- *Search String......................: YourString* >>> Enter the string to search for.  This can be a simple string like ";LAYER_CHANGE" or can be a regular expression like  ";Layer:(\d+)\n"  
- *Replace With.......................: M999* >>> This is the text that will replace the search string.  For a Regular Expression replacement it could be ";LAYER:\1\nM999" which would remember the layer number in the Regex search example.  
- *Is Regex?..........................: False* >>> Whether the search string should be considered a "Regular Expression".  
- *Enable a Layer Range Search?.......: True* >>> It isn't necessary to search the entire gcode.  The search can be limited to a range of layers.  If you do enable a layer range then you get to pick the start and end layers.  
- *Start Layer....................: 25* >>> the search will commence at the beginning of the Start Layer.  
- *End Layer......................: 50* >>> the search will continue through to the end of the End Layer.  
- *Replace the First Instance only?...: False* >>> You can opt to change only the first instance of the Search String rather than all of the occurences.  
- *Ignore Startup G-Code?.............: True* >>> When set to 'True' the StartUp will not be included in the Search and Replace.  
- *Ignore Ending G-Code?..............: True* >>> When set to 'True' the Ending Gcode will not be included in the Search and Replace.  (If you define a 'Layer Range' then the StartUp and Endings are always excluded.)  

* <Continue?(y)  Redo(r)  Quit(x)* >>> selecting "r" will allow you to go back and make changes to your settings.  
 
**Advanced Fan Control**  
Requires "Add Layer Numbers" to run before it.
For multi-extruders two fan circuits are supported.
The two main options are "By Feature" (works well for large models) and "By Layer".
The first option is "Fan speed by PWM or by RepRap scale 0-1".  Most printers use PWM.
*By Layer*
Enter the layer numbers and corresponding fan speeds as "5/35" where 5 would be the layer number and 35 would be the fan percentage.  Multiple layers and speeds may be entered by delimiting with a comma.  For example:  5/35,20/100,35/50,75/100 would bounce the fan speed from 35% to 100% to 50% to 75% at the various layers.  This works well with smaller models as the fans don't react instanteously.
*By Feature*
Allows you to set fan speeds starting at a layer of your choice, and continuing to a layer of your choice.  Each defined "TYPE" in the gcode can have a different fan speed.
The top of a raft can be cooled and then the fan will shut off when the top surface of the raft finished.
If your fan control ends before the top layer of the print, you can select the "final fan speed" that will carry through to the end of the print.

This example of the settings is from "By Feature"

Review your fan settings:  

"Fan Scale (PMW 0 to 255 or RepRap 0 to 1)"  
"Start Layer"  
"End Layer"  
"alias_bed_adhesion_skirt"  
"alias_bed_adhesion_brim"  
"alias_wall_outer"  
"alias_wall_inner"  
"alias_top_skin"  
"alias_mid_skin"  
"alias_btm_skin"  
"alias_bridge"  
"alias_internal_bridge"  
"alias_overhang_wall"  
"alias_infill"  
"alias_support"  
"alias_support_interface"  
"Final Fan speed"  
"Bambu Auxiliary Fan"  
"Bambu Chamber Fan"  
 <Continue(y,n) or Redo(r)>  
 
Entering an "r" will allow you to go back through and change things.  
The script makes no attempt to determine specific printer models but the Aux Fan and Chamber fan are available in Bambu Studio.
 
 **Time Lapse Camera**  
 This requires 'Add Layer Numbers' to run first.
 The script will add camera trigger commands at the ends of layers.  The setting options are.  

Trigger Command............. (often M240)  
Insert Frequency............ (how often to insert the command.  Every layer, every 3rd, every 19th, whatever)  
Anti-Shake-Wait............. (in milleseconds - how long to wait (at the park position) for the printer frame to become still)  
Pause after image........... (in milleseconds - how long to wait after the camera takes the image)  
Park Print Head............. (whether to park the print head or not)  
  Park Head X............... (the 'x' location to park the head)  
  Park Head Y............... (the 'y' location to park the head)  
Retract when necessary...... (add a retraction and prime if there wasn't one before parking the head.)  
Z-hop before parking........ (the height to move the nozzle up from the print before parking)  
Insure final Image.......... (if the insertion frequency was such that there was no image taken at the end of the last layer - this will do that)  

**Insert at Layer Change**  
This requires 'Add Layer Numbers' to run first.  
 The script will search the gcode complete, or a range of layers, and add gcode commands at layer changes replacements.  
 The setting options are.  
  'Insertion Frequency'  You may insert the commands every so many layers.  Entering a '0' will make a single insertion at a specific layer.
  'Start Layer' The layer to start the insertions at
  'End Layer' The last layer for insertions
  if Insertion Frequency is 0:
  'Single Insertion Layer Number' The layer to put a single instance of the insert code
  'Gcode to Add' The commands to insert.  Delimit multiple commands with commas.  EX: G92 E0,M221 S100,M117 GoodBye.  
 
 **Display Layer and ET**  
Requires "Add Layer Numbers" to run before it.
This uses M117 to send a message to the LCD in the form ' 1/250 | ET 3h45m '.  M118's are also added to send the same string to a print server (for example Octoprint).
An option is to add M73 with % complete, and Time remaining as ' M73  R322 P0 '.  M75 is added to the start of the file, and M77 is added to the end of the file. Bambu Studio appears to add the M73 lines by default.

**Pause at Layer**  
Much like the Pause at Height in Cura, it asks several questions so the pause and return can be set up.  The settings include 10 pause options including M600.
Users won't be asked for all of these, but a lot of these.

Pause Layer(s).............. Can be multiple layers (delimited by commas) as long as they use the same basic settings (park position, retract amount, etc.) Ex:  125,333,412  
Message(s) M117 and M118.... Messages to send to the LCD and a print server like Octoprint.  For different message for each pause delimit with commas. Ex: green,red,blue  
Pause Method................ The pause command.  There are 11 options from Marlin M0, M25, Klipper PAUSE, G4, etc.  
  if pause_method == "G4":  
    G4 Dwell Time............... The dwell entered as minutes\n"  
  if pause_method == "M600"  
	All parameters for M600 (B, L, U, R, X, Y, Z, etc.)  
Reason for Pause............ Either 'Filament Change' or 'All Others' (for inserting nuts or magnets).  
Unload Amount............... The amount of filament to back out of the extruder for filament changes  
Enable Quick Purge.......... Extrude some material before unloading.  This helps keep the filament from getting stuck in the hot end.  
Reload Amount............... The amount of filament to extrude to get the end back to the nozzle.  
Unload and Reload Speed..... The E-speed for loading and unloading.  Generally, the machine max E speed.  
Purge Amount................ The amount of filament to purge when changing color.  
Extra Prime Amount.......... When the reason is All Others, this allows a make up extrustion to account for oozing during the pause  
Keep Steppers Alive......... Whether to allow the steppers to possibly disable.  
Disarm Timout............... The amount of time from the last movement, to the steppers disabling.  
Park the Print Head......... Whether to park the print head during the pause  
Park Head X................. The X parking location  
Park Head Y................. The Y parking location  
Z-hop for Parking........... The height to lift the nozzle over the print before parking  
Standby Temperature......... The temperature to sit at while waiting to resume the print  
Resume Print Temperature Cmd Either M104 or M109.  
Resume Temperature.......... The temperature that the print will resume at  
Custom Gcode Before Pause... Gcode commands to add before the pause  
Beep at Pause............... Whether to beep at pause  
Custom Gcode After Pause.... Gcode commands to add after the pause  
Redo Previous Layer......... Whether to go over the previous layer again.  
Redo Layer Flow Rate........ Flow % for the 'redo layer'  

Some of the commands are options, but there can be a lot of questions to answer.  There is a checklist before continuing and that allows you to go back and make changes to your settings, or to simply exit.  


