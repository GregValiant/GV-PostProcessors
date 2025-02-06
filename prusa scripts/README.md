# GV-PostProcessors

*PostProcessing Scripts for PrusaSlicer and OrcaSLicer*

As I work on these I update the Git page.  The versions here should work as intended.  Since I am a one-man-band there may be bugs that I did not catch.  Let me know if there are issues with the post processors.

PLEASE NOTE:
    These post-processors are "python scripts" and Python must be installed on your computer.
    "GregValiants_AddLayerNumbers" must be run first in order for the other scripts to work (they will search for Layer Numbers).


In both Prusa and Orca, the post processors need to be entered into the "Output Options" "Post-processing scripts" text box in this manner:
"C:\Users\grego\AppData\Local\Programs\Python\Python313\python.exe" "C:\Users\grego\Documents\Creality\PrusaScripts\GregValiants_AddLayerNumbers.py";
The quotation marks are necessary on my installtion of Windows 10 Pro.
The first part of the line is the path and file name for "python.exe" on your computer.
then a "space" character.
The second part is the path and file name of the post-processor followed by a semi-colon
Each post-processor requires the same form and must be separate.
For multiple post-processors the "Post-processing scripts" textbox would look something like this:
-------------
"C:\Users\grego\AppData\Local\Programs\Python\Python313\python.exe" "C:\Users\grego\Documents\Creality\PrusaScripts\GregValiants_AddLayerNumbers.py";
"C:\Users\grego\AppData\Local\Programs\Python\Python313\python.exe" "C:\Users\grego\Documents\Creality\PrusaScripts\GregValiants_SearchAndReplace.py";
"C:\Users\grego\AppData\Local\Programs\Python\Python313\python.exe" "C:\Users\grego\Documents\Creality\PrusaScripts\GregValiants_AdvancedFanControl.py";
-------------
As each post-processor runs it will open a command window and you will be asked to enter your options.  There will be a final listing of your inputs that will look something like this (Add Layer Numbers does not have a final review):

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
 
-----------------------------------------------------------------------------
**Add Layer Numbers:
Goes through the gcode and looks for ";LAYER_CHANGE" and adds a line below that ";Layer:XX".
The layer numbers will match the Prusa/Orca preview.  ";Layer:1" might be the first layer of the model, or might be the first layer of a raft with the model up higher.

**Search and Replace
The review will include the settings:
Search String......................: YourString >>> Enter the string to search for.  This can be a simple string like ";LAYER_CHANGE" or can be a regular expression like  ";Layer:(\d+)\n"
Replace With.......................: M999 >>> This is the text that will replace the search string.  For a Regular Expression replacement it could be ";LAYER:\1\nM999" which would remember the layer number in the Regex search example.
Is Regex?..........................: False >>> Whether the search string should be considered a "Regular Expression".
Enable a Layer Range Search?.......: True >>> It isn't necessary to search the entire gcode.  The search can be limited to a reange of layers.  If you do enable a layer range then you get to pick the start and end layers.
    Start Layer....................: 25 >>> the search will commence at the beginning of the Start Layer
    End Layer......................: 50 >>> the search will continue through to the end of the End Layer
Replace the First Instance only?...: False >>> You can opt to change only the first instance of the Search String rather than all of the occurences.
Ignore Startup G-Code?.............: True >>> When set to 'True' the StartUp will not be included in the Search and Replace.
Ignore Ending G-Code?..............: True >>> When set to 'True' the Ending Gcode will not be included in the Search and Replace
I you define a 'Layer Range' then the StartUp and Endings are always excluded.
 <Continue?(y)  Redo(r)  Quit(x) >>> selecting "r" will allow you to go back and make changes to your settings.
 
**Advanced Fan Control**
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

