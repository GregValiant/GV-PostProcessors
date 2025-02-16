# GregValiant's PostProcessors for PrusaSlicer, OrcaSlicer, and Bambu Studio

As I work on these I update the Git page.  The versions here should work as intended.  Since I am a one-man-band there may be bugs that I did not catch.  Let me know if there are issues with the post processors.

PLEASE NOTE:
- These post-processors are "python scripts" and Python must be installed on your computer. 
- "GregValiants_AddLayerNumbers" must be run first in order for the other scripts to work (they will search for Layer Numbers).

In all three slicers, the post processors need to be entered into the "Output Options" "Post-processing scripts" text box in this manner...
"C:\Users\grego\AppData\Local\Programs\Python\Python313\python.exe" "C:\Users\grego\Documents\PrusaScripts\GregValiants_AddLayerNumbers.py";
The quotation marks are necessary on my installtion of Windows 10 Pro.
The first part of the line is the path and file name for "python.exe" (on your computer) followed by a single "space".
The second part is the path and file name of the post-processor followed by a semi-colon.
Each post-processor requires the same form and must be separate.
For multiple post-processors the "Post-processing scripts" textbox would look something like this...

<path\python.exe><1space><path\post-processor file name><;>
Github is shortening this but each "path + post processor" should be on a single line.
"C:\Users\grego\AppData\Local\Programs\Python\Python313\python.exe" "C:\Users\grego\Documents\PrusaScripts\GregValiants_AddLayerNumbers.py";  
"C:\Users\grego\AppData\Local\Programs\Python\Python313\python.exe" "C:\Users\grego\Documents\PrusaScripts\GregValiants_SearchAndReplace.py";  
"C:\Users\grego\AppData\Local\Programs\Python\Python313\python.exe" "C:\Users\grego\Documents\PrusaScripts\GregValiants_AdvancedFanControl.py";  

As each post-processor runs it will open a command window and you will be asked for your input.  The scripts attempt to catch typos, but you need to be careful.

-----------------------------------------------------------------------------
**Add Layer Numbers:**
2/14/2025  My test model is 50mm tall.  When I slice at 0.2 layer height and 0.2 initial layer height and with "Generate Support Material" turned off, it is 250 layers.  That's what I expect and what "Add Layer Numbers" comes up with.  If I turn "Generate Support Material" on - it is 470 layers in Prusa, 379 layers in Orca, and 350 layers in Bambu.  Go figure.  The script will make the adjustment when supports are enabled or disabled.  The layer numbering in the gcode will match the slicer preview.
The script will go through the gcode and look for ";LAYER_CHANGE" ("; CHANGE_LAYER" in Bambu) and add a line below that ";Layer:XX".  
The layer numbers will match the preview.  ";Layer:1" might be the first layer of the model, or might be the first layer of a raft with the model up higher.
Any followup scripts that run will likely require that 'Add Layer Numbers' runs first.  It must only be run once.  

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
Currently this is set up for single fans.  If there is interest, additional fan circuits could be added.  That is a PITA.
The two main options are "By Feature" (works well for large models) and "By Layer".
The first option is "Fan speed by PWM or by RepRap scale 0-1".  Most printers us PWM.
*By Layer*
Enter the layer numbers and corresponding fan speeds as "5/35" where 5 would be the layer number and 35 would be the fan percentage.  Multiple layers and speeds may be entered by delimiting with a comma.  For example:  5/35,20/100,35/50,75/100 would bounce the fan speed from 35% to 100% to 50% to 75% at the various layers.  This works well with smaller models as the fans don't react instanteously.
*By Feature*
Allows you to set fan speeds starting at a layer of your choice, and continuing to a layer of your choice.  Each defined "TYPE" in the gcode can have a different fan speed.
The top of a raft can be cooled and then the fan will shut off when the top surface of the raft finished.
The fan can be shut off for "wipes" but doing so will add a _LOT_ of lines to the gcode file.
If your fan control ends before the top layer of the print, you can select the "final fan speed" that will carry through to the end.

This settings example is from "By Feature"

Review your fan settings:  

Use normal PWM fan scale (0 to 255)  
Start Layer (model starts on ';Layer:1' in the Gcode): 5  
End Layer in the Gcode...............................: 32  
TYPE:External Perimeter..............................: 100%  
TYPE:Perimeter.......................................: 35%  
TYPE:Top solid infill................................: 50%  
TYPE:Solid infill....................................: 35%  
TYPE:Bridge infill...................................: 100%  
TYPE:Internal infill.................................: 50%  
TYPE:Skirt/Brim......................................: 0%  
TYPE:Support.........................................: 35%  
TYPE:Support interface...............................: 100%  
Fan off during travel................................: False  
Final Fan speed (above the End Layer)................: 75%  
Top-of-Raft fan speed................................: 80%  
 <Continue(y,n) or Redo(r)>  
 
 Entering an "r" will allow you to go back through and change things.
 There are additional settings for Bambu printers that will allow control of the Aux and Chamber fans.  The settings will come up whether those fans exist on the printer or not.  The script makes no attempt to determine specific printer models.
 
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

**Search and Replace**
This requires 'Add Layer Numbers' to run first.
 The script will search the gcode complete, or a range of layers, and make replacements.  Regular Expressions are an option as is ignoring the StartUp and Ending gcodes.  
 The setting options are. 
 
Review your Search and Replace settings  

Search String......................: (the string you want to search for.)  
Replace With.......................: (the replacement string.  If your search string ends with a '\n' then the replacement string should end with a \n.)  
Is Regex?..........................: (will treat the search string as a regular expression Ex: ;Layer:(\d+) )  
Enable a Layer Range Search?.......: (you can limit the search to a range of layers.  If the Start and End numbers are the same, then just that layer would be searched.)  
  Start Layer......................: (the starting layer)  
  End Layer........................: (the ending layer)  
Replace the First Instance only?...: (you might only need to replace a single instance rather than everything in the file)  
Ignore Startup G-Code?.............: (leave the startup out)  
Ignore Ending G-Code?..............: (leave the ending out)  
 <Continue?(y)  Redo(r)  Quit(x)\n"  