# GregValiant

This Plugin is new in March of 2024.

This plugin adds a setting named "Little Utilities" to the Experimental settings in the Custom print setup of Cura. It enables several post-processing scripts.

The Little Utilities settings can be found in the Custom print setup by using the Search field on top of the settings. If you want to make the setting permanently visible in the sidebar, right click and select "Keep this setting visible".

***WARNING***
Some of the scripts are not compatible with each other or with other scripts.  If you "Remove Comments" and opt to remove "Layer Number" lines, then a post processor like "pause at height" will not work.  The user must check the gcode for unwanted side effects.

## Options

        Remove Comments:
			Include opening paragraph:  Whether to include from ";FLAVOR:xxxx" to ";TARGET_MACHINE.NAME"
			Include StartUp Gcode:  Whether to include the Startup gcode of the printer.
			Remove Layer Lines:  Whether to remove the layer lines from the gcode.  This can impact other post processors if this is done before they run.
			Indlude Enting Gcode:  Whether to include the Ending gcode of the printer.
		Add Last Extruder Ending Gcode:  A bug fix to add any Extruder Ending Gcode of the last extruder to the end of the last layer of the gcode.
		Lift Head Parking:  Used in conjunction with "Cooling / Lift Head" this adds a move away from the print (to the skirt/brim area) to eliminate oozing on the print.
		Very Cool Fanpath:  Adds a zigzag movement 1mm above the print to cool a layer.
			End of which Layers: Enter layer number(s).  Delimit single layers with a comma (Ex: 13,45,60).  Delimit ranges of layers with a dash (Ex: 20-23).
								 (The layer numbers may be mixed (Ex: 1,4,8-10,113).  Spaces are not allowed.)
			FanPath Travel Speed:  The speed that the print head will move along the grid.  Units are mm/sec.
			FanPath Cooling Fan %:  The fan speed.
			Index distance:  The distance to move the print head before each pass across the print.
			Add Y indexed path:  The normal zigzag path is doubled to be a grid path.
		Change Printer Settings:  Change the firmware settings in the printer.  This is firmware dependent.
			Change Printer Max Speeds: Adjusts the speeds with M203.
				Max X
				Max Y
				Max Z
				Max E
			Change Max XY accel:  Adjusts the accel with M201
				Max X Accel
				Max Y Accel
			Change Home Offsets:  Adjusts with M206
				Home Offset X
				Home Offset Y
				Home Offset Z
			Change Steps/mm:  Adjusts with M92
				X steps/mm
				Y steps/mm
				Z steps/mm
				E steps/mm
			Save all settings:  Saves the settings within the printer using M500.
								If the settings are not saved then any changes will revert to the previous defaults when the printer is powered off.
		Enable Debugging Tools:
			Add Data Headers:  Within Cura the data is kept in a Python list.  This tool will add comments between the data items.
			Create a debugging file:  This will remove all heating and extrusions from a file.  It leaves just the X, Y, Z movements in the user specified range of layers.
		Add Line Numbers to the Gcode:  Some specialty printers want the lines in the file numbered.
			Character Prefix:  You may enter a character that will precede the line number.
			Starting Number:  Generally 1 or 0 but can be something else.
			Skip Comments:  Whether to skip over lines that start with a semi-colon.
		Disable ABL for small models:  Will comment out G29 and M420 lines in the StartUp Gcode if the models size falls below a certain size or print time.
			By footprint:  The minimum size of the print in mm².  Prints small than this will not use ABL.
			By print time:  The minimum print time of the model.  Print times below this will not use ABL.
		One-at-a-Time Final Z:  A bug fix.  It is possible that if a short model is printed last in One-at-a-Time mode the the final travel move could cause the
								nozzle to crash into a previous taller print.  This adds a single Z move line to the "transit height" just before the Ending Gcode.
		Adjust per model temperature:  Also for One-at-a-Time mode, this will adjust the temperature for each model.
			Temperature list:  A list of the temperature to use (Ex: 205,210,1215).  The temperatures are distributed in the gcode in the print order, not by model name.
		Enable Speed Enforcement:  A bug fix for the wild speeds that have crept into Cura gcodes.
			Enforce Speed Limits for:  The options are Print, Travel, Both.  Speeds that are found to be above the Print and Travel speeds are adjusted down.
										
		
			
			
			
			
        
