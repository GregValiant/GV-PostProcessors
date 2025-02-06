# GregValiant's PostProcessors and Plugins for Cura
 PostProcessing Scripts for Cura

As I work on these I update the Git page.  The versions here should work as intended and they are not Cura "version specific".  My own Cura installations go from UM 4.13.1 to current and Smart Avionics 4.20.x fork and I test on those.  They are likely to be acceptable to Creality and other Cura forks but I don't debug with those.  Since I am a one-man-band there may be bugs that I did not catch.  Let me know if there are issues with the post processors.

Known Issues:

MultiExtruderColorMix:
    I don't own a multi-extruder machine so this script might not work as expected.  I could use feedback on this one.

Filament Change:.
    I added all the possible parameters as listed on MarlinFW.org.  The parameters must be supported in the firmware.  If they are not then the parameter is likely to be ignored, but it is possible that an invalid parameter will keep the command from being executed by the printer.

Flash Forge IDEX Tool Temps:
    This started out as a simple attempt to change the syntax of the Cura Gcode to be acceptable to the Flash Forge IDEX printers.  It ended up being a pretty full-fledged translator and allows the user to select the mode "Normal, Duplicate, or Mirror" in the post processor settings and when the file is saved the gcode is translated and some lines added so the Flash Forge printer will print it as it should.  Just because the Cura gcode opened in FlashPrint seems to be correct doesn't mean that it will print correctly.  This is another one that I need feedback on.

Marlin to FlashForge Converter (for single extruder printers):
	Please note that some testing on a Creator 2 has shown that the script is not working as expected.  The print refuses to start.
	Goes through the gcode and makes changes like changing the "TYPE" lines to ";structure:" lines are used by FlashPrint.  It also adds tool numbers to fan lines, changes the G0 commands to G1 commands, and translates things like Cura's heating lines and Build Volume Fan lines.  The script is compatible with the FlashFinder plugins from the MarketPlace.

-----------------------------------------------------------------------------
Latest Changes:
2/01/2025:  Added the post processors for Prusa/Orca

1/25/2025: Little Utilities update:
	Added 'Initial Layer Walls Z Height' adjustment.  The layer height of the initial layer Inner and Outer walls can be adjusted separate from other features.  The second layer has the Wall Flow Rate adjusted to account for the higher layer heights.

AnnealingCoolDown now has a "Filament Drying" function.  It will create a gcode file with just the commands needed to Auto-Home, park the head, heat the build plate to a temperature of your choice.  The bed will stay at that temperature for the specified period of time and then shut off.

AddCuraSettings is updated to the settings in Cura 5.9.0 stable release.

ZhopOnTravel can now add retractions when they are necessary.

MaxVolumetricSpeed (Max E Speed by Flow Rate) is new and there is a pull request in for it.
    Also added the same function as a Plugin.  The settings appear at the top of the "Speed Settings" in Cura.

PurgeLinesAndUnload - found a couple of bugs (typos) and added support for machines with disallowed areas.  Added moves when a multi-extruder printer travels to the purge tower at the beginning of a print.

-----------------------------------------------------------------------------
Here is a list of the post-processors and a brief description of what they do.
Most of these provide tweaks to a gcode.  Some are my own ideas and others are ideas from posters on various forums.  Then it becomes "I wonder if I can do that...".

**AAA Post Process ReadMe:**
	When loaded into Cura it will immedeately open the PDF file of the same name.  The PDF has descriptions of all the Cura post processors.  Maintaining it is difficult but I do update it from time to time.  There doesn't seem to be mistakes in it, but there might be new post-processors missing.  This requires both the ".py" file and the ".pdf" file.

**AddCoolingProfile:**
	This one is now included with Cura.  If gives fine control over the layer cooling fan(s) either "By Layer" or "By Feature".

**AddCuraSettings:**
	Adds a list of over 600 Cura settings to the end of the gcode file.  The exact number depends on the number of extruders, whether certain settings are checked, etc.  It was turned down by the Cura team as being too difficult to maintain.  I see their point, but it is useful to have sometimes none the less.  The current version has been updtated to Cura 5.9.0.

**AlterZHops:**
	This allows the Z-hop height to be altered for ranges of layers.  Setting the new hop height to "0" effectively turns it off although the lines are not removed from the gcode.

**AnnealingOrDrying:**
	Allows "End-of-print" control of the bed (and chamber) temperatures.  The bed temperature can be adjusted and the "cool down" can be stretched out to "anneal" a print.  The print head can be parked out of the way so a cover can be placed over the print.
	A second option allows you to use the build plate heater to dry filament.  You need to slice a model but there won't be a print in the gcode file.  Just a short script to move the print head up out of the way, and heat the bed for however long you need.

**BridgeTemperatureAdjustment:**
	Allows a temperature change for bridging and then returns the temperature to the normal print temperature when the bridge is finished.

**CuraPrependBugFix:**
	This is specifically for Cura 5.7.2 and removes the temperature prepend lines that are being erroneously entered before the StartUp Gcode.

**DiscoverSettings:**
    NOTE:  This does not generate a gcode file.
	Goes through "fdmprinter.def.json" and retrieves all the settings and pastes them into the gcode file.  If a comparison between two Cura versions is being made then it lists all the settings in each version and reports the differences between the two versions.  This is what I use to update "AddCuraSettings".

**DisplayInfoOnLCD and DisplayInfoOnLCD_GV:**
	Now included in Cura, it adds some info to the LCD and can bounce that information back to a print server like OctoPrint or PrintRun.  The version with the GV extension has some minor changes in it that differ from the Cura version.

**EmulateMultiExtruder:**
	This allows a user to slice a file with a dual extruder printer active and then exchange the Tool Changes for PauseAtLayer and print the gcode on a single extruder printer.  The user becomes the tool changer.  This can get very old very fast but occasionally it's handy to have.

**FilamentChange:**
	This is a re-write of the Cura version.  It may get accepted into Cura.  I've added all the possible parameters and some firmware may not like that.

**FlashForge_IDEX_TempTools:**
	Allows users to pick the print mode and to convert a Cura Gcode to a FlashPrint gcode.  This is a work in process.

**HighTempPrinting:**
	A workaround for the Cura 365° temperature limit of the hot end.  When printing a material like PEEK the user enters 1/2 print temperature values and the post-processor will double them in the gcode.

**InsertAtLayerChange:**
	A re-write with added options such as "Frequency" of the insertion.

**LimitXYAccelJerk:**
	For bed slinger printers, the accel can be changed at a layer, or gradually changed across a range of layers.  It can keep jerky motion of tall prints from breaking the print loose from the bed.

**LittleUtilities_v17:**
	A collection of 17 post processors ranging from "Remove Comments" (usefull for UM2 printers) to creating debugging gcode files with no extrusions.  There are some script debugging tools as well.  The 'v' number indicates how many scripts are included rather than the version number.

**MultiExtruderColorMix:**
	A work in process.  This is intended to allow graduated mixing for printers with mixing hot ends.  The Marlin side is well along.  The RepRap side is just started.

**PauseAtLayer:**
	My re-work of PauseAtHeight.  Allows for unloading, purging, and re-loading and other new options.  There is an option to add pauses to all the models in a "One at a Time" project.  I threw out the "By Height" option as it didn't work well with Adaptive Layers or Z-hops.

**PurgeLinesAndUnload:**
	'Adds purge lines' to the gcode.  The lines can be at the top, bottom, left, or right and either full length or half length.  Rectangular, elliptical and Origin at Center are supported.  If you have purge lines in your startup gcode you need to remove them as this post processor makes them redundant (although it will try to find them in the startup and comment them out).
	Other settings are:
	'Adjust the E location' prior to the start of the print.  The filament start of the skirt/brim can be dialed in.
	'Circle around to start'.  Adds orthogonal travel moves around the build plate periphery to the layer start point to keep strings from crossing where the print will be.  A change in Cura for multi-extruder printers is to add a move to the prime tower location before the print starts.  I need to think about that because it affects the pre-print movements of this script.
	'Unload FIlament' will unload the filament from the extruder at the end of a print.
	For multi-extruder printers:  If the definition file includes a 'Move to Prime Tower" before the start of the first layer then the script will add an orthogonal move to the nearest edge so the nozzle does not cross the print area.  This is not an option, but something that always runs.

**Raise3DIDEX:**
	Does for the Raise3D IDEX machines what the other post does for the Flash Forge IDEX machines.

**RetractContinue:**
	A re-work to allow the script to work with z-hops and relative extrusion.

**SearchAndReplace:**
	Another re-write with new options including "First Instance Only" and ranges of layers.

**SuptIntMaterialChange:**
	This one is really cool.  With the air-gap over the support-interface (or raft) at "0" the user can select the layers to insert filament changes just for the Support-Interface.  After the interface is printed there is another pause to change back to the original material.  (Using PETG for the interface of a PLA print, or vice-versa, works well.)  This allows for excellent release of the support from the model and excellent finishes on the support side of the "first layer over support".  The downside is that as good as it is with large flats, it's value decreases as the number of pauses required grows which makes it annoying for things like the support in large horizontal holes.  But if you have a box top and it needs to be printed right-side-up, this is really good.

**TimeLapse:**
	A re-write that has been submitted to UM.  It includes additional options like "Frequency" of the insertion.

**Zhop On Travel:**
	Adds Z-hops to a file within a range of layers based on the length of a travel move.  The hop height and minimum travel are user defined.  This is not dependent on retractions and is compatible with Z-Hops enabled in Cura.  It is not compatible with One-at-a-Time mode.
	Retractions have been added and occur if there isn't already one in place when the new Zhop's are added.
	This is compatible with firmware retraction, relative extrusion, and extra prime amount.  You can leave "z-hop on retraction" disabled in Cura and use this script to hop for just a couple of layers when necessary.

**Max E Speed and Jerk Decoupler**
	Goes through the Gcode and at every retraction/prime it changes the Max E Speed with M203.  Before the retraction/prime the speed is increased so retraction/prime is at the set speed.  After the retract/prime event; the speed is reduced so that flow increases in the gcode will not under-extrude.  The script works with Absolute Extrusion, Relative Extrusion, Firmware Retraction, Marlin and RepRap, and allows for separate settings for dual extruders.
	Jerk settings are included for the extruder(s).

-----------------------------------------------------------------------------
Plugin Extensions for Cura:

**SovolSV04_IDEX:**
	This is intended to compliment the Sovol SV04 in Cura.  The commands are available in the "Dual Extruder" section of the Cura settings.
	When it is installed and in "Auto_Mode" it will check the printer name and make an adjustment to 'Copy', 'Dual', 'Mirror', 'Single01', or Single02 mode.  In Dual Mode there are options for single use 'StartUp' and 'Ending' macros.

**FlashForge_IDEX_Plugin:**
	Same as the post-processor but as a plugin/extension

**Support Interface Material Change:**
	This is the same as the post-processor.  It is available in the normal Cura 'Support' settings under 'Enable Support Interface'

**Max E Speed and Jerk Decoupler:**
	See the post processor above.

-----------------------------------------------------------------------------

