# Copyright (c) 2023 GregValiant (Greg Foresi)
#   This is a collection of several small Post Processors that I have found useful or that have been requested here and there:
#     1) Remove Comments - Remove semi-colons and everything to the right of a semi-colon.  There are options.  (Thanks to @Torgeir)
#     2) Renumber Layers - For One-At-A-Time prints renumbering to "all at once" style can provide additional options for PauseAtHeight and Filament Change.
#     3) Add Extruder End code - A bug fix - this adds any 'Extruder End Gcode' of the last extruder used to the end of the file.
#     4) Add Data Headers - A debugging utility, it adds comments between the data sections
#     5) Lift Head Parking - adds a park move to the "Lift Head" cooling option for small layers.  The move is to just off the print.  It returns to the print after the G4 dwell is complete.
#     6) Change Printer Settings - Max Feedrate, Max Accel, Home Offsets, Steps/mm.  (There is no Max for Jerk)
#     7) Very Cool FanPath - Raise 1mm and follow a zigzag path across the print with just the Layer Cooling Fan running.
#     8) Disable ABL for small models.  The user defines 'small' and models that fall below that area on the build plate cause G29 and M420 to be commented out of the StartUp Gcode.  There is also a 'minimum time' option.
#     9) Gcode Line Numbering - Numbers the lines in the gcode.  A prefix is an option.  (authored by: Slashee the Cow)
#     10) Debug Gcode File - A debug tool that removes all the extrusions and heating lines from a range of layers or the whole file.  The result is a 'Movement Only' file so users can check a toolpath.  There is an option to leave the Hot End heating commands or comment them out.
#     11) One-at-a-Time Final Z - A bug fix that adds a move up to the transit (print MAXZ) height before the ending Gcode.  Prevents a crash if the last print is shorter than others.
#     12) One-at-a-Time Adjust Print Temperatures - Enter a list of temperatures and each succesive model will print at the assigned temperature.
#     13) Enable Speed Enforcement - If Flow Rate Compensation alters some print speeds to very high values this script will reset them to the speeds in the Cura settings.  The speeds are checked per feature and per extruder.  Speeds might be lowered, never raised.
#     14) Add line numbers for each layer - Debugging tool that addes a layer line number as a comment.
#     15) Kill Wipe at layer - Negates the wipe move for 'Outer-Wall, Infill, or Both' within a layer range.
#     26) 2X Print Temperatures (must be enabled in this script) - This is a High Temperature Override for Cura's 365° limit. This works but is disabled here for safety reasons.  If you enable it:  Set the Cura print temperatures to 1/2 of the required temperature and this script will go through and double them in the gcode.  When printing a material like PEEK you can set the temperature in Cura to 210 and the gcode will be changed to 420.
#     17) Move the Tool Changes - "Enable Prime Tower" must be checked for this to run.  Cura adds tool changes just prior to the nozzle moving to the prime tower.  This script moves the tool change to just past the move to the prime tower so the change occurs above the prime tower rather than above the model.
#     18) Change a dual extruder print into a single extruder print to check motion.  All the T0 and T1 lines are commented out and 1 or 2 beeps inserted instead.  Tool numbers are moved to the end of M104 lines and all M109 lines are converted to M104 so there is no waiting.  When coupled with "create a debug file" all extrusions are eliminated as well just leaving the print and prime tower motion.  You may leave the heating commands to see what effect the M109 lines might have.

from ..Script import Script
from UM.Application import Application
from UM.Message import Message
import re
import os

class LittleUtilities_v15(Script):

    def initialize(self) -> None:
        super().initialize()
        # Get the Max Feedrate and Max Accel from Cura Printer Settings (may be different than what the printer has)
        curaApp = Application.getInstance().getGlobalContainerStack()
        extruder = Application.getInstance().getGlobalContainerStack().extruderList
        self._instance.setProperty("change_feedrate_x", "value", curaApp.getProperty("machine_max_feedrate_x", "value"))
        self._instance.setProperty("change_feedrate_y", "value", curaApp.getProperty("machine_max_feedrate_y", "value"))
        self._instance.setProperty("change_feedrate_z", "value", curaApp.getProperty("machine_max_feedrate_z", "value"))
        self._instance.setProperty("change_feedrate_e", "value", curaApp.getProperty("machine_max_feedrate_e", "value"))
        self._instance.setProperty("change_accel_x", "value", curaApp.getProperty("machine_max_acceleration_x", "value"))
        self._instance.setProperty("change_accel_y", "value", curaApp.getProperty("machine_max_acceleration_y", "default_value"))
        self._instance.setProperty("change_steps_x", "value", str(extruder[0].getProperty("machine_steps_per_mm_x", "value")))
        self._instance.setProperty("change_steps_y", "value", str(extruder[0].getProperty("machine_steps_per_mm_y", "value")))
        self._instance.setProperty("change_steps_z", "value", str(extruder[0].getProperty("machine_steps_per_mm_z", "value")))
        self._instance.setProperty("change_steps_e", "value", str(extruder[0].getProperty("machine_steps_per_mm_e", "value")))
        self._instance.setProperty("very_cool_feed", "value", str(round(int(extruder[0].getProperty("speed_print", "value"))/2,0)))
        self._purge_end_loc = None
        self._instance.setProperty("adjust_e_loc_to", "value", round(float(extruder[0].getProperty("retraction_amount", "value")) * -1), 1)

        machine_extruder_count = int(curaApp.getProperty("machine_extruder_count", "value"))
        if machine_extruder_count > 1:
            self._instance.setProperty("temp_override_extruder_check", "value", True)
        else:
            self._instance.setProperty("temp_override_extruder_check", "value", False)

    def getSettingDataString(self):
        return """{
            "name": "Little Utilities v15",
            "key": "LittleUtilities_v15",
            "metadata": {},
            "version": 2,
            "settings":
            {                
                "enable_little_utilities":
                {
                    "label": "Enable the scripts",
                    "description": "Check the box to enable the scripts.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": true
                },
                "move_tool_changes":
                {
                    "label": "Move IDEX Tool Changes",
                    "description": "Move the tool changes from above the 'travel-to-Prime-Tower' moves to below those moves so the tool change occurs over the Prime Tower.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "enable_little_utilities"
                },
                "remove_comments":
                {
                    "label": "Remove Comments",
                    "description": "Removes all semi-colons and any text to the right of the semi-colon.  It isn't possible to anticipate the order these scripts should run.  In particular if you find that 'Remove Comments' should run last then add another instance of 'Little Utilities' and enable 'Remove Comments' in that instance to ensure it runs last.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "enable_little_utilities"
                },
                "remove_comments_inc_opening":
                {
                    "label": "    Include opening paragraph:",
                    "description": "The opening generally consists of comments only and includes from 'Flavor' to 'MAXZ'.  (The 'POSTPROCESSED' line is added after the scripts have all run.)",
                    "type": "bool",
                    "default_value": true,
                    "enabled": "remove_comments and enable_little_utilities"
                },
                "remove_comments_inc_startup":
                {
                    "label": "    Include StartUp Gcode:",
                    "description": "The StartUp section is from 'generated with...' to ';LAYER_COUNT:'.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": "remove_comments and enable_little_utilities"
                },
                "remove_comments_leave_layer_lines":
                {
                    "label": "    Remove ';LAYER:' lines:",
                    "description": "If unchecked then the ';LAYER:' lines will be left in.  That makes searching the gcode easier.  Post processors that run after this one may require the Layer lines.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "remove_comments and enable_little_utilities"
                },
                "remove_comments_inc_ending":
                {
                    "label": "    Include Ending Gcode:",
                    "description": "The Ending Gcode may have comments.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "remove_comments and enable_little_utilities"
                },
                "bug_fixes":
                {
                    "label": "Cura bug fix scripts",
                    "description": "These are scripts that fix noticed problems with Cura.",
                    "type": "bool",
                    "default_value": false,
                    "enabled":  "enable_little_utilities"
                },
                "add_extruder_end":
                {
                    "label": "    Add 'Ending Gcode' for final extruder",
                    "description": "Adds the Ending Gcode of the last extruder used in the print prior to the regular Ending Gcode.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "bug_fixes and enable_little_utilities"
                },
                "final_z":
                {
                    "label": "    One-at-a-Time Final Z",
                    "description": "Adds a Z-lift move up to the 'Transit Height' right after the last model finishes printing.  Prevents the nozzle crashing into taller prints.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "bug_fixes and enable_little_utilities"
                },
                "lift_head_park":
                {
                    "label": "Lift Head Parking",
                    "description": "For small layers - this adds a move off the print (to the skirt/brim area) so the nozzle doesn't ooze on the print.",
                    "type": "bool",
                    "default_value": false,
                    "enabled":  "enable_little_utilities"
                },
                "very_cool":
                {
                    "label": "Very Cool Fanpath",
                    "description": "Creates a fanpath that runs up and back 1mm above the print with the fan running to give extra cooling.  Helps lower the amount of sticking to support-interfaces.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "enable_little_utilities"
                },
                "very_cool_layer":
                {
                    "label": "    End of which layer(s)?",
                    "description": "Pick the layer(s) from the Cura preview.  The printhead will move in the 'Y' in a grid toolpath 1.0mm above the current Z (no extrusions) with the Layer Cooling Fan speed at the percent you enter here.  The 'X' index is 10mm.  For multiple layers delimit with a comma (',') and delimit ranges of layers with a dash ('-') do not add spaces.  Ex: 5,6,12-25,30,45-55 or 200-225.",
                    "type": "str",
                    "default_value": "1-227",
                    "unit": "Lay num  ",
                    "enabled": "very_cool and enable_little_utilities"
                },
                "very_cool_feed":
                {
                    "label": "    FanPath Speed mm/sec",
                    "description": "The Speed to run the printhead along the cooling fan path.",
                    "type": "int",
                    "default_value": 50,
                    "minimum_value": 7,
                    "minimum_value_warning": 10,
                    "maximum_value": 400,
                    "unit": "mm/sec  ",
                    "enabled": "very_cool and enable_little_utilities"
                },
                "very_cool_fan":
                {
                    "label": "    FanPath Cooling Fan %",
                    "description": "The % of the Fan Speed to apply to the cooling runs.",
                    "type": "int",
                    "default_value": 100,
                    "minimum_value": 25,
                    "maximum_value": 100,
                    "unit": "%  ",
                    "enabled": "very_cool and enable_little_utilities"
                },
                "very_cool_index_dist":
                {
                    "label": "    Index distance",
                    "description": "The distance to move the head between each pass across the print.",
                    "type": "int",
                    "default_value": 25,
                    "minimum_value": 5,
                    "maximum_value": 50,
                    "unit": "mm  ",
                    "enabled": "very_cool and enable_little_utilities"
                },
                "very_cool_y_index":
                {
                    "label": "    Add Y indexed path",
                    "description": "The toolpath is an X zigzag. Enabling the Y will create a grid toolpath. That doubles the cooling effect and takes twice as long.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "very_cool and enable_little_utilities"
                },
                "renum_or_revert":
                {
                    "label": "Renumber Layers",
                    "description": "Renumbers a One-at-a-Time file to All-at-Once numbering.  This allows different uses for Pause at Height and Filament Change.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "enable_little_utilities"
                },
                "renum_layers":
                {
                    "label": "    Renumber or UN-Renumber:",
                    "description": "For use with One-At-A-Time prints.  Re-numbering the layer from 0 to Top Layer will cause Pause At Height or Filament Change to act differently.  After re-numbering you might wish to set it back to affect any additional following post-processors.",
                    "type": "enum",
                    "options": {
                        "renum": "Renumber>AllAtOnce",
                        "un_renum": "Revert>OneAtATime"},
                    "default_value": "renum",
                    "enabled": "renum_or_revert and enable_little_utilities"
                },
                "change_printer_settings":
                {
                    "label": "Change Printer Settings",
                    "description": "Add gcode commands to a file to change the internal printer settings.  NOTE: Changes remain in effect until printer power-off (they do not reset at the end of the print).  The changes will become the new printer defaults if you elect to save with M500 (firmware dependent).",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "enable_little_utilities"
                },
                "change_feedrate":
                {
                    "label": "    Change Printer Max Speeds",
                    "description": "Change the max feedrate for any axes. Blank entries mean No Change.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "change_printer_settings and enable_little_utilities"
                },
                "change_feedrate_x":
                {
                    "label": "        Max X Feedrate",
                    "description": "Change the Max X feedrate.",
                    "type": "str",
                    "default_value": "",
                    "unit": "mm/sec  ",
                    "enabled": "change_printer_settings and change_feedrate and enable_little_utilities"
                },
                "change_feedrate_y":
                {
                    "label": "        Max Y Feedrate",
                    "description": "Change the Max Y feedrate.",
                    "type": "str",
                    "default_value": "",
                    "unit": "mm/sec  ",
                    "enabled": "change_printer_settings and change_feedrate and enable_little_utilities"
                },
                "change_feedrate_z":
                {
                    "label": "        Max Z Feedrate",
                    "description": "Change the Max Z feedrate.",
                    "type": "str",
                    "default_value": "",
                    "unit": "mm/sec  ",
                    "enabled": "change_printer_settings and change_feedrate and enable_little_utilities"
                },
                "change_feedrate_e":
                {
                    "label": "        Max E Feedrate",
                    "description": "Change the Max E feedrate.",
                    "type": "str",
                    "default_value": "",
                    "unit": "mm/sec  ",
                    "enabled": "change_printer_settings and change_feedrate and enable_little_utilities"
                },
                "change_xYaccel":
                {
                    "label": "    Change Max X-Y Acceleration",
                    "description": "Change the Max Accel for the X and/or Y axes. They can be unequal.  Blank entries mean No Change.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "change_printer_settings and enable_little_utilities"
                },
                "change_accel_x":
                {
                    "label": "        Max X Acceleration",
                    "description": "Change the Max X Acceleration.",
                    "type": "str",
                    "default_value": "",
                    "unit": "mm/sec²  ",
                    "enabled": "change_printer_settings and change_xYaccel and enable_little_utilities"
                },
                "change_accel_y":
                {
                    "label": "        Max Y Acceleration",
                    "description": "Change the Max Y Acceleration.",
                    "type": "str",
                    "default_value": "",
                    "unit": "mm/sec²  ",
                    "enabled": "change_printer_settings and change_xYaccel and enable_little_utilities"
                },
                "change_home_offset":
                {
                    "label": "    Change Home Offsets",
                    "description": "Change the Home Offsets. Blank entries mean No Change.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "change_printer_settings and enable_little_utilities"
                },
                "change_home_x":
                {
                    "label": "        Home Offset X",
                    "description": "Change the X home offset.",
                    "type": "str",
                    "default_value": "",
                    "enabled": "change_printer_settings and change_home_offset and enable_little_utilities"
                },
                "change_home_y":
                {
                    "label": "        Home Offset Y",
                    "description": "Change the Y home offset.",
                    "type": "str",
                    "default_value": "",
                    "enabled": "change_printer_settings and change_home_offset and enable_little_utilities"
                },
                "change_home_z":
                {
                    "label": "        Home Offset Z",
                    "description": "Change the Z home offset.",
                    "type": "str",
                    "default_value": "",
                    "enabled": "change_printer_settings and change_home_offset and enable_little_utilities"
                },
                "change_steps":
                {
                    "label": "    Change Steps/MM",
                    "description": "Change the Steps/MM for the XYZE axes. Blank entries mean No Change.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "change_printer_settings and enable_little_utilities"
                },
                "change_steps_x":
                {
                    "label": "        X Steps/MM",
                    "description": "Change the X Steps.",
                    "type": "str",
                    "default_value": "",
                    "unit": "steps/mm  ",
                    "enabled": "change_printer_settings and change_steps and enable_little_utilities"
                },
                "change_steps_y":
                {
                    "label": "        Y Steps/MM",
                    "description": "Change the Y Steps.",
                    "type": "str",
                    "default_value": "",
                    "unit": "steps/mm  ",
                    "enabled": "change_printer_settings and change_steps and enable_little_utilities"
                },
                "change_steps_z":
                {
                    "label": "        Z Steps/MM",
                    "description": "Change the Z Steps.",
                    "type": "str",
                    "default_value": "",
                    "unit": "steps/mm  ",
                    "enabled": "change_printer_settings and change_steps and enable_little_utilities"
                },
                "change_steps_e":
                {
                    "label": "        E Steps/MM",
                    "description": "Change the E Steps.",
                    "type": "str",
                    "default_value": "",
                    "unit": "steps/mm  ",
                    "enabled": "change_printer_settings and change_steps and enable_little_utilities"
                },
                "change_save_changes":
                {
                    "label": "    Save all changes (M500)",
                    "description": "Save the changes to the printer EEPROM or memory. If you don't save then any changes will expire when the printer is turned off.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "change_printer_settings and (change_home_offset or change_xYaccel or change_feedrate or change_steps) and enable_little_utilities"
                },
                "debugging_tools":
                {
                    "label": "Enable Debugging Tools",
                    "description": "Debug specific scripts.",
                    "type": "bool",
                    "default_value": false,
                    "enabled":  "enable_little_utilities"
                },
                "add_data_headers":
                {
                    "label": "    Add Data[?] headers",
                    "description": "A debugging tool.  Adds comment lines '>>>End of Data[xxx]<<<' to the end of each item in the Data List.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "debugging_tools and enable_little_utilities"
                },
                "add_data_headers_at_start":
                {
                    "label": "        At section start",
                    "description": "When checked the lines will be added to the beginning of a data section.  When un-checked they will be at the end.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": "add_data_headers and debugging_tools and enable_little_utilities"
                },
                "dual_ext_to_single":
                {
                    "label": "    Dual extruder to single extr",
                    "description": "Turns a dual extruder project into a single extruder file by commenting out the tool changes and adding beeps instead.  At tool change there is a single beep for T0 and a double beep for T1.  Tool numbers in heating commands are moved to the end as a comment.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "debugging_tools and enable_little_utilities"
                },
                "dual_convert_M109":
                {
                    "label": "        Convert M109 to M104",
                    "description": "Checking this will convert all temperature lines from 'M109' to 'M104'.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "debugging_tools and dual_ext_to_single and enable_little_utilities"
                },
                "debug_file":
                {
                    "label": "    Create a debugging file",
                    "description": "Removes all M commands and extrusions from the layer range specified.  All other layers are deleted.  This allows you to air-print parts of a file to check the motion.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "debugging_tools and enable_little_utilities"
                },
                "debug_autohome_cmd":
                {
                    "label": "        Your Auto-Home cmd",
                    "description": "Usually G28 but can be different.  Add parameters if required.",
                    "type": "str",
                    "default_value": "G28",
                    "enabled": "debug_file and debugging_tools and enable_little_utilities"
                },
                "debug_start_layer":
                {
                    "label": "        Start Layer Debug File",
                    "description": "The first layer to remove the extrusions from.  Prior Layers will be deleted",
                    "type": "int",
                    "default_value": "1",
                    "enabled": "debug_file and debugging_tools and enable_little_utilities"
                },
                "debug_end_layer":
                {
                    "label": "        End Layer Debug File",
                    "description": "The last layer to have extrusions removed.  Layers after this one will be deleted.  Enter '-1' for the top layer.",
                    "type": "int",
                    "default_value": 25,
                    "enabled": "debug_file and debugging_tools and enable_little_utilities"
                },
                "debug_leave_temperature_lines":
                {
                    "label": "        Leave HE temperature lines",
                    "description": "All temperature lines are commented out by default.  Checking this will leave the Hot End temperature lines active and the hot end will heat.  Any M140 and M190 bed temperature lines will still be commented out.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "debugging_tools and debug_file and enable_little_utilities"
                },
                "data_num_and_line_nums":
                {
                    "label": "    Add data[item] and line nums",
                    "description": "Another debug utility that will add ' ;Data: num, Line: lnum' to each line in the file",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "debugging_tools and enable_little_utilities"
                },
                "line_numbers":
                {
                    "label": "Add line numbers to the gcode",
                    "description": "Numbers the lines.  Some firmware requires line numbers.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "enable_little_utilities"
                },
                "add_line_nr_sentence_number_prefix":
                {
                    "label": "    Sentence number prefix",
                    "description": "This will appear before the line number in the g-code",
                    "type": "str",
                    "default_value": "",
                    "enabled": "line_numbers and enable_little_utilities"
                },
                "add_line_nr_starting_number":
                {
                    "label": "    Starting Number",
                    "description": "The number used for the first line.",
                    "type": "int",
                    "default_value": "1",
                    "enabled": "line_numbers and enable_little_utilities"
                },
                "add_line_nr_skip_comments":
                {
                    "label": "    Skip Comments",
                    "description": "When 'True' any line that starts with a semi-colon will be ignored during the numbering.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "line_numbers and enable_little_utilities"
                },
                "disable_abl":
                {
                    "label": "Disable ABL for Small Models",
                    "description": "When a model takes up less space, or is shorter time than entered below, any G29 and M420 lines in the startup will be disabled.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "enable_little_utilities"
                },
                "disable_abl_footprint":
                {
                    "label": "    By footprint",
                    "description": "When a model takes up less space than entered below, any G29 and M420 lines in the startup will be disabled.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "disable_abl and enable_little_utilities"
                },
                "disable_abl_min_footprint":
                {
                    "label": "        Min. Footprint for ABL",
                    "description": "FOR SINGLE MODELS ONLY - this disables the StartUp ABL commands for small prints.  Enter the minimum size of the print in square mm's (any skirt/brim/raft will be ignored).  Models that take up less space than this will NOT USE the ABL.  (If there is more than a single print on the build plate Cura adds the areas together so this would include all models.)",
                    "type": "int",
                    "default_value": 900,
                    "minimum_value": 4,
                    "unit": "mm²    ",
                    "enabled": "disable_abl and disable_abl_footprint and enable_little_utilities"
                },
                "disable_abl_time":
                {
                    "label": "    By print time",
                    "description": "When a model takes less time to print than entered below, any G29 and M420 lines in the startup will be disabled.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "disable_abl and enable_little_utilities"
                },
                "disable_abl_min_time":
                {
                    "label": "        Min. time for ABL",
                    "description": "This disables the StartUp ABL commands for short duration prints.  Enter the minimum time for ABL in minutes.  Models that take less time than this will NOT USE the ABL.",
                    "type": "int",
                    "default_value": 20,
                    "minimum_value": 4,
                    "unit": "minutes    ",
                    "enabled": "disable_abl and disable_abl_time and enable_little_utilities"
                },
                "adjust_temps":
                {
                    "label": "Adjust per model temperature",
                    "description": "Adjust the temperatures for each model in a 'One-at-a-Time' project.",
                    "type": "bool",
                    "default_value": false,
                    "enabled":  "enable_little_utilities"
                },
                "temperature_list":
                {
                    "label": "    Temperature List",
                    "description": "Enter the temperatures to assign to each model in the order you want them assigned (delimit with a comma - spaces are not allowed).  There should be one temperature assigned for each model on the build plate.  If there are less Temperatures than Number-of-Models the additional models will be set to 'Print Temperature'.  If you have the 'Initial Print Temperature' set differently than the 'Print Temperature' then the temperature changes will be made at LAYER:1 and all Initial Print Temperatures will be respected.",
                    "type": "str",
                    "unit": "°C  ",
                    "default_value": "210,215,220",
                    "enabled": "adjust_temps and enable_little_utilities"
                },
                "speed_limit_enable":
                {
                    "label": "Enable Speed Enforcement",
                    "description": "Whether to enforce the speeds in Cura if they have been effected by 'Flow Compensation'.  Speeds that are above the Cura settings will be adjusted down to the setting value.  Speeds that are slower than the setting are not affected.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "enable_little_utilities"
                },
                "speeds_to_check":
                {
                    "label": "    Enforce Speed Limits",
                    "description": "Print speeds, travel speeds, or both.  The speeds are checked per feature and per extruder.",
                    "type": "enum",
                    "options": {
                        "print_speeds": "Print Speeds",
                        "travel_speeds": "Travel Speeds",
                        "all_speeds": "Both"},
                    "default_value": "all_speeds",
                    "enabled": "speed_limit_enable and enable_little_utilities"
                },
                "kill_wipe":
                {
                    "label": "Kill wiping at layer",
                    "description": "This will comment out the first move after the last extrusion at the end of: TYPE:OUTER-WALL or TYPE:FILL or BOTH.  Only extruder 1 is checked to see if Wipe is enabled.  There can be issues if Wipe is enabled for some extruders and not for others.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": false
                },
                "wipe_to_kill":
                {
                    "label": "    Which Wipe Features?",
                    "description": "Make a selection.",
                    "type": "enum",
                    "options": {
                        "outer_wall_wipe": "Outer Wall",
                        "infill_wipe": "Infill",
                        "both_wipe": "Both"},
                    "default_value": "outer_wall_wipe",
                    "enabled": "kill_wipe and enable_little_utilities"
                },
                "kill_wipe_from":
                {
                    "label": "    Wipe kill Start Layer",
                    "description": "The first layer to kill wiping.  Use the Cura preview numbers.",
                    "type": "int",
                    "default_value": 25,
                    "minimum_value": 1,
                    "enabled": "kill_wipe and enable_little_utilities"
                },
                "kill_wipe_to":
                {
                    "label": "    Wipe kill End Layer",
                    "description": "The last layer to end wiping.  Use the Cura preview numbers or '-1' for the end layer.",
                    "type": "int",
                    "default_value": -1,
                    "enabled": "kill_wipe and enable_little_utilities"
                },
                "temp_override_enable":
                {
                    "label": "2X Print Temperatures",
                    "description": "This provides an override to the 365° hot end temperature limit in Cura.  This script will DOUBLE the Cura temperature settings within the gcode.  EX: A print temperature of 225° in Cura will become 450° in the gcode.  For single extruder printers, all the hot end temperatures will be affected.  For multi-extruder printers, you may select to change the temperatures of 'T0', 'T1', or 'Both'.  Printers with mixing hot ends ('extruders share heater' and 'extruders share nozzle') and printers with more than 2 extruders are not supported.  This script allows print temperatures in the gcode for materials like PEEK.  The printer must be capable of handling such high temperatures.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": false
                },
                "temp_override_extruder_select":
                {
                    "label": "Which extruders should be changed",
                    "description": "Select the Tool that will have DOUBLE temperatures.",
                    "type": "enum",
                    "options": {
                        "t0_only": "T0 only",
                        "t1_only": "T1 only",
                        "both_extruders": "Both T0 and T1"
                        },
                    "default_value": "t0_only",
                    "enabled": "temp_override_enable and temp_override_extruder_check and enable_little_utilities"
                },
                "temp_override_extruder_check":
                {
                    "label": "Hidden setting",
                    "description": "This setting remains hidden.  It enables the 'temp_override_extruder_select' option if the extruder count is 2.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": false
                }
            }
        }"""

    def execute(self, data):
        if  self.getSettingValueByKey("bug_fixes") and self.getSettingValueByKey("add_extruder_end"):
            self._add_extruder_end(data)
        if self.getSettingValueByKey("bug_fixes") and self.getSettingValueByKey("final_z"):
            self._final_z(data)
        if self.getSettingValueByKey("move_tool_changes"):
            self._move_tool_changes(data)
        if self.getSettingValueByKey("dual_ext_to_single"):
            self._dual_ext_to_single(data)
        if self.getSettingValueByKey("renum_or_revert"):
            self._renumber_layers(data)
        if self.getSettingValueByKey("add_data_headers") and self.getSettingValueByKey("debugging_tools"):
            self._add_data_header(data)
        if self.getSettingValueByKey("remove_comments"):
            self._remove_comments(data)
        if self.getSettingValueByKey("lift_head_park"):
            self._lift_head_park(data)
        if self.getSettingValueByKey("change_printer_settings"):
            self._change_printer_settings(data)
        if self.getSettingValueByKey("very_cool"):
            self._very_cool(data)
        if self.getSettingValueByKey("disable_abl"):
            self._disable_abl(data)
        if self.getSettingValueByKey("line_numbers"):
            self._line_numbering(data)
        if self.getSettingValueByKey("debug_file") and self.getSettingValueByKey("debugging_tools"):
            self._practice_file(data)
        if self.getSettingValueByKey("adjust_temps"):
            self._adjust_temps_per_model(data)
        if self.getSettingValueByKey("speed_limit_enable"):
            self._speed_limits(data)
        if self.getSettingValueByKey("kill_wipe"):
            self._kill_wipes(data)
        if self.getSettingValueByKey("data_num_and_line_nums") and self.getSettingValueByKey("debugging_tools"):
            self._data_num_and_line_nums(data)
        if self.getSettingValueByKey("temp_override_enable"):
            data = self._print_temp_change(data)
        data[1] = self.format_string(data[1])
        data[len(data) - 1] = self.format_string(data[len(data) - 1])
        return data

    # Add Extruder Ending Gcode-------------------------------------------
    def _add_extruder_end(self, data:str)->str:
        t_nr = 0
        try:
            for num in range(1,len(data)-2):
                lines = data[num].split("\n")
                for line in lines:
                    if re.match("T(\d*)",line):
                        t_nr = self.getValue(line, "T")
            end_gcode = Application.getInstance().getGlobalContainerStack().extruderList[t_nr].getProperty("machine_extruder_end_code","value")
        except:
            end_gcode = Application.getInstance().getGlobalContainerStack().extruderList[0].getProperty("machine_extruder_end_code","value")
        if end_gcode != "":
            data[len(data)-2] += end_gcode + "\n"
        return

    # Add data headers to the end of each data section.  Add 'Total Cmd Lines' to data[0]
    def _add_data_header(self, data:str)->str:
        in_front = bool(self.getSettingValueByKey("add_data_headers_at_start"))
        tot_lines = 2
        comments = 0
        for num in range(0,len(data)):
            tot_lines += data[num].count("\n")
            comments += data[num].count(";")
        tot_lines -= comments
        ## Add a couple of statistics to the beginning of the file
        data[0] += ";  There are " + "{:,.0f}".format(tot_lines) + " command Lines and " + "{:,.0f}".format(comments) + " comment lines in this file\n"
        if in_front:
            for num in range(0,len(data)-1):
                data[num] = ";" + str(">" * 33) + "Start of DATA[" + str(num) + "]" + str("<" * 33) + "\n" + data[num]
            data[len(data)-1] = ";" + str(">" * 33) + "Start of DATA[" + str(num+1) + "]" + str("<" * 33) + "\n" + data[len(data)-1]
        else:
            for num in range(0,len(data)-1):
                data[num] += ";" + str(">" * 33) + "End of DATA[" + str(num) + "]" + str("<" * 33) + "\n"
            data[len(data)-1] += ";" + str(">" * 33) + "End of DATA[" + str(num+1) + "]" + str("<" * 33) + "\n"
        return

    # Remove Comments----------------------------------------------------------
    def _remove_comments(self, data:str)->str:
        me_opening = bool(self.getSettingValueByKey("remove_comments_inc_opening"))
        me_startup = bool(self.getSettingValueByKey("remove_comments_inc_startup"))
        me_ending = bool(self.getSettingValueByKey("remove_comments_inc_ending"))
        me_layerlines = bool(self.getSettingValueByKey("remove_comments_leave_layer_lines"))

        # Start with the opening data paragraph if enabled
        if me_opening:
            layer = data[0]
            lines = layer.split("\n")
            modified_data = ""
            for line in lines:
                if line.startswith(";"):
                    line = ""
                    continue
                if ";" in line:
                    line = line.split(";")[0]
                modified_data += line + "\n"
            data[0] = modified_data[0:-1]

        # the StartUp Gcode section if enabled
        if me_startup:
            layer = data[1]
            lines = layer.split("\n")
            modified_data = ""
            for line in lines:
                if line.startswith(";"):
                    line = ""
                    continue
                if ";" in line:
                    line = line.split(";")[0]
                modified_data += line + "\n"
            data[1] = modified_data[0:-1]
        stop_at = len(data)
        if me_ending:
            stop_at = len(data)
        else:
            stop_at = len(data)-1

        # Remove comments from the Layers and (if enabled) from the Ending Gcode
        for num in range(2,stop_at,1):
            layer = data[num]
            lines = layer.split("\n")
            modified_data = ""
            for line in lines:
                # Leave the Layer Lines unless removal is enabled
                if line.startswith(";LAYER:") and not me_layerlines:
                    modified_data += line + "\n"
                    continue
                if line.startswith(";"):
                    line = ""
                    continue
                if ";" in line:
                    line = line.split(";")[0]
                modified_data += line + "\n"
            data[num] = modified_data[0:-1]
        return

    # Renumber Layers----------------------------------------------------------
    def _renumber_layers(self, data:str)->str:
        renum_layers = str(self.getSettingValueByKey("renum_layers"))
        one_at_a_time = Application.getInstance().getGlobalContainerStack().getProperty("print_sequence", "value")

        # If the project was sliced 'All at Once' then exit
        if one_at_a_time == "all_at_once":
            data[0] += ";  [Little Utilities] (Renumber Layers did not run because the Print Sequence is All-At-Once)\n"
            Message(title = "[Little Utilities] Renumber Layers", text = "Did not run because the Print Sequence is All-At-Once.").show()
            return data

        # Count the layers because "LAYER_COUNT" can be theoretical
        #raft_lay_count = 0
        #lay_count = 0
        layer0_index = 2
        for num in range(1,len(data)-1,1):
            layer = data[num]
            if ";LAYER:0" in layer:
                layer0_index = num
                break

        # Concantenate the data list items that were added to the beginning of each separate model
        for num in range(layer0_index,len(data) - 2,1):
            if num + 1 == len(data) - 2: break # Avoid concantenating the Ending Gcode
            try:
                while not ";LAYER:" in data[num + 1]:
                    data[num] += str(data[num + 1]) + "\n"
                    data.pop(num + 1)
            except:
                continue

        # Renumber the layers
        if renum_layers == "renum":
            lay_num = 0
            for num in range(layer0_index,len(data),1):
                layer = data[num]
                if layer.startswith(";LAYER:") and not layer.startswith(";LAYER:-"):
                    temp = layer.split("\n")
                    data[num] = layer.replace(temp[0],";LAYER:" + str(lay_num))
                    lay_num += 1
            layer = data[layer0_index - 1]

        # Revert the numbering to OneAtATime if enabled
        elif renum_layers == "un_renum":
            lay_num = 0
            for num in range(layer0_index,len(data),1):
                layer = data[num]
                if layer.startswith(";LAYER:") and not layer.startswith(";LAYER:-"):
                    temp = layer.split("\n")
                    data[num] = layer.replace(temp[0],";LAYER:" + str(lay_num))
                    lay_num += 1
                if ";LAYER_COUNT:" in layer:
                    lay_num = 0
            layer = data[layer0_index - 1]

        # Move the 'Time_elapsed' and 'Layer_Count' lines to the end of their data sections in case of a following PauseAtHeight
        modified_data = ""
        for num in range(2,len(data)-2,1):
            layer = data[num]
            lines = layer.split("\n")
            modified_data = ""
            time_line = ""
            for line in lines:
                if line.startswith(";TIME_ELAPSED:") or line.startswith(";LAYER_COUNT:"):
                    time_line += line + "\n"
                    line = ""
                if line != "":
                    modified_data += line + "\n"
            data[num] = modified_data + time_line

        # If re-numbering then change each LAYER_COUNT line to reflect the new total layers
        if renum_layers == "renum":
            for num in range(1,len(data)-1,1):
                layer = data[num]
                data[num] = re.sub(";LAYER_COUNT:(\d*)",";LAYER_COUNT:" + str(len(data) - 3),layer)

        # If reverting to one-at-a-time then change the LAYER_COUNT back to per model
        elif renum_layers == "un_renum":
            model_lay_count = 0
            for num in range(len(data)-1,1,-1):
                if ";LAYER:" in data[num]:
                    model_lay_count += 1
                if ";LAYER:0" in data[num]:
                    data[num-1] = re.sub(";LAYER_COUNT:(\d*)",";LAYER_COUNT:" + str(model_lay_count), data[num-1])
                    model_lay_count = 0
        return

    # Lift Head Parking--------------------------------------------------------
    def _lift_head_park(self, data:str)->str:
        extruder = Application.getInstance().getGlobalContainerStack().extruderList
        # Send a message and exit if Lift Head is not enabled
        if not bool(extruder[0].getProperty("cool_lift_head", "value")):
            Message(title = "[Little Utilities] LiftHead Parking", text = "Did not run because 'Lift Head' is not enabled.").show()
            return data
        travel_speed = int(extruder[0].getProperty("speed_travel", "value"))*60

        # Get the footprint size of the print on the build plate
        lines = data[0].split("\n")
        for line in lines:
            if line.startswith(";MINX:") or line.startswith(";PRINT.SIZE.MIN.X:"):
                x_min = float(line.split(":")[1])
            if line.startswith(";MINY:") or line.startswith(";PRINT.SIZE.MIN.Y:"):
                y_min = float(line.split(":")[1])
            if line.startswith(";MAXX:") or line.startswith(";PRINT.SIZE.MAX.X:"):
                x_max = float(line.split(":")[1])
            if line.startswith(";MAXY:") or line.startswith(";PRINT.SIZE.MAX.Y:"):
                y_max = float(line.split(":")[1])

        # Get the XY origin of the print
        mesh_x_origin = round(x_max - ((x_max - x_min)/2),2)
        mesh_y_origin = round(y_max - ((y_max - y_min)/2),2)

        # Find the lines that start with "Small layer"
        for lay_num in range(2, len(data)-1,1):
            layer = data[lay_num]
            lines = layer.split("\n")
            for index, line in enumerate(lines):
                if not line.startswith(";Small layer"):
                    continue
                else:
                # Get the "Return to" location and calculate the shortest move off the print
                    x_park = 0
                    y_park = 0
                    for xy_index in range(index-1, 0,-1):
                        if " X" in lines[xy_index] and " Y" in lines[xy_index]:
                            x_loc = self.getValue(lines[xy_index], "X")
                            y_loc = self.getValue(lines[xy_index], "Y")
                            if x_loc <= mesh_x_origin:
                                x_park = x_min
                                x_delta = x_loc - x_min
                            elif x_loc > mesh_x_origin:
                                x_park = x_max
                                x_delta = x_max - x_loc
                            if y_loc <= mesh_y_origin:
                                y_park = y_min
                                y_delta = y_loc - y_min
                            elif y_loc > mesh_y_origin:
                                y_park = y_max
                                y_delta = y_max - y_loc
                            break
                    if float(x_delta) >= float(y_delta):
                        park_line = f"G0 F{travel_speed} Y{y_park}"
                    else:
                        park_line = f"G0 F{travel_speed} X{x_park}"

                    # Insert the move and return lines
                    if self.getValue(lines[index+1], "E") is not None:
                        lines.insert(index + 3, park_line)
                        lines.insert(index + 5, f"G0 F{travel_speed} X{x_loc} Y{y_loc}")
                    else:
                        lines.insert(index + 2, park_line)
                        lines.insert(index + 4, f"G0 F{travel_speed} X{x_loc} Y{y_loc}")
                    break
            data[lay_num] = "\n".join(lines)
        return

    # Change printer settings--------------------------------------------------
    def _change_printer_settings(self, data:str)->str:
        change_feed_string = ";-------------------------------Change Printer Settings\n"
        change_accel_string = ""
        change_home_string = ""
        change_steps_string = ""
        save_string = ""

        # If there are Feed Rate changes
        if bool(self.getSettingValueByKey("change_feedrate")):
            x_feedrate = str(self.getSettingValueByKey("change_feedrate_x"))
            y_feedrate = str(self.getSettingValueByKey("change_feedrate_y"))
            z_feedrate = str(self.getSettingValueByKey("change_feedrate_z"))
            e_feedrate = str(self.getSettingValueByKey("change_feedrate_e"))
            if x_feedrate != "" or y_feedrate != "" or z_feedrate != "" or e_feedrate != "":
                change_feed_string += "M203"
                if x_feedrate != "":
                    change_feed_string += f" X{x_feedrate}"
                if y_feedrate != "":
                    change_feed_string += f" Y{y_feedrate}"
                if z_feedrate != "":
                    change_feed_string += f" Z{z_feedrate}"
                if e_feedrate != "":
                    change_feed_string += f" E{e_feedrate}"
                change_feed_string += " ;Change Max Feed Rate\n"

        # If there are Accel changes
        if bool(self.getSettingValueByKey("change_xYaccel")):
            x_accel = str(self.getSettingValueByKey("change_accel_x"))
            y_accel = str(self.getSettingValueByKey("change_accel_y"))
            if x_accel != "" or y_accel != "":
                change_accel_string += "M201"
                if x_accel != "":
                    change_accel_string += f" X{x_accel}"
                if y_accel != "":
                    change_accel_string += f" Y{y_accel}"
                change_accel_string += " ;Change Max Accel\n"

        # If there are Home Offset changes
        if bool(self.getSettingValueByKey("change_home_offset")):
            x_home = str(self.getSettingValueByKey("change_home_x"))
            y_home = str(self.getSettingValueByKey("change_home_y"))
            z_home = str(self.getSettingValueByKey("change_home_z"))
            if x_home != "" or y_home != "" or z_home != "":
                change_home_string += "M206"
                if x_home != "":
                    change_home_string += f" X{x_home}"
                if y_home != "":
                    change_home_string += f" Y{y_home}"
                if z_home != "":
                    change_home_string += f" Z{z_home}"
                change_home_string += " ;Change Home Offset\n"

        # If there are Steps/MM changes
        if bool(self.getSettingValueByKey("change_steps")):
            x_steps = str(self.getSettingValueByKey("change_steps_x"))
            y_steps = str(self.getSettingValueByKey("change_steps_y"))
            z_steps = str(self.getSettingValueByKey("change_steps_z"))
            e_steps = str(self.getSettingValueByKey("change_steps_e"))
            if x_steps != "" or y_steps != "" or z_steps != "" or e_steps != "":
                change_steps_string += "M92"
                if x_steps != "":
                    change_steps_string += f" X{x_steps}"
                if y_steps != "":
                    change_steps_string += f" Y{y_steps}"
                if z_steps != "":
                    change_steps_string += f" Z{z_steps}"
                if e_steps != "":
                    change_steps_string += f" E{e_steps}"
                change_steps_string += " ;Change Steps/MM\n"

        # Allow the user to save the changes to the printer and alter Cura Printer Settings
        if bool(self.getSettingValueByKey("change_save_changes")) and (bool(self.getSettingValueByKey("change_home_offset")) or bool(self.getSettingValueByKey("change_xYaccel")) or bool(self.getSettingValueByKey("change_feedrate")) or bool(self.getSettingValueByKey("change_steps"))):
            save_string = "M500 ;Save changes to printer\nG4 P500 ;Pause for save\n"
            if bool(self.getSettingValueByKey("change_xYaccel")):
                if x_accel != "":
                    Application.getInstance().getGlobalContainerStack().setProperty("machine_max_acceleration_x", "value", int(x_accel))
                if y_accel != "":
                    Application.getInstance().getGlobalContainerStack().setProperty("machine_max_acceleration_y", "value", int(y_accel))
            if bool(self.getSettingValueByKey("change_feedrate")):
                if x_feedrate != "":
                    Application.getInstance().getGlobalContainerStack().setProperty("machine_max_feedrate_x", "value", int(x_feedrate))
                if y_feedrate != "":
                    Application.getInstance().getGlobalContainerStack().setProperty("machine_max_feedrate_y", "value", int(y_feedrate))
                if z_feedrate != "":
                    Application.getInstance().getGlobalContainerStack().setProperty("machine_max_feedrate_z", "value", int(z_feedrate))
                if e_feedrate != "":
                    Application.getInstance().getGlobalContainerStack().setProperty("machine_max_feedrate_e", "value", int(e_feedrate))
            if bool(self.getSettingValueByKey("change_steps")):
                curaApp = Application.getInstance().getGlobalContainerStack()
                extruder = curaApp.extruderList
                if x_steps != "":
                    curaApp.setProperty("machine_steps_per_mm_x", "value", x_steps)
                    extruder[0].setProperty("machine_steps_per_mm_x", "value", x_steps)
                if y_steps != "":
                    curaApp.setProperty("machine_steps_per_mm_y", "value", y_steps)
                    extruder[0].setProperty("machine_steps_per_mm_y", "value", y_steps)
                if z_steps != "":
                    curaApp.setProperty("machine_steps_per_mm_z", "value", z_steps)
                    extruder[0].setProperty("machine_steps_per_mm_z", "value", z_steps)
                if e_steps != "":
                    curaApp.setProperty("machine_steps_per_mm_e", "value", e_steps)
                    extruder[0].setProperty("machine_steps_per_mm_e", "value", e_steps)

        # Add the changes to the gcode at the end of the StartUp Gcode
        data[1] += change_feed_string + change_accel_string + change_home_string + change_steps_string + save_string + ";-------------------------------End of Changes\n"
        data[1] = data[1][0:-1]
        lines = data[1].split("\n")

        # Reformat data[1] so ";LAYER_COUNT:xxx" is the last line
        for index, line in enumerate(lines):
            if line.startswith(";LAYER_COUNT"):
                layer_count = line
                lines.remove(layer_count)
                lines.append(layer_count)
                data[1] = "\n".join(lines) + "\n"
        return

    # Very_cool cooling--------------------------------------------------------
    def _very_cool(self, data:str)->str:
        all_layers = self.getSettingValueByKey("very_cool_layer")
        add_layers = ""
        numstart = 0
        numend = 0
        very_cool_layers = []
        # The layers can be individual entries or ranges.  This figures that out and adds all the named layers to 'very_cool_layers'
        if "," in all_layers:
            new_layers = all_layers.split(",")
            for index, n in enumerate(new_layers):
                if "-" in str(n):
                    numstart = str(n.split("-")[0])
                    numend = str(n.split("-")[1])
                    for m in range(int(numend),int(numstart)-1,-1):
                        new_layers.insert(index+1,m)
                    new_layers.pop(index)
            very_cool_layers = new_layers
        elif not "," in all_layers and "-" in all_layers:
            new_layers = []
            numstart = str(all_layers.split("-")[0])
            numend = str(all_layers.split("-")[1])
            for m in range(int(numstart),int(numend)+1,1):
                new_layers.append(m)
            very_cool_layers = new_layers
        else:
            very_cool_layers.append(all_layers)

        # Get the rest of the information that is required
        very_cool_y_index = bool(self.getSettingValueByKey("very_cool_y_index"))
        very_cool_index_dist = int(self.getSettingValueByKey("very_cool_index_dist"))
        extruder = Application.getInstance().getGlobalContainerStack().extruderList
        travel_speed = str(int(extruder[0].getProperty("speed_travel", "value"))*60)
        zhop_speed = str(int(extruder[0].getProperty("speed_z_hop", "value"))*60)
        retr_enabled = bool(extruder[0].getProperty("retraction_enable", "value"))
        retr_dist = str(extruder[0].getProperty("retraction_amount", "value"))
        retr_speed = str(extruder[0].getProperty("retraction_speed", "value")*60)
        bed_width = int(Application.getInstance().getGlobalContainerStack().getProperty("machine_width", "value"))
        bed_depth = int(Application.getInstance().getGlobalContainerStack().getProperty("machine_depth", "value"))
        fan_percent = self.getSettingValueByKey("very_cool_fan") /100
        fan_speed = 0
        # Check if the fan scale is RepRap 0-1
        fan_scale = bool(extruder[0].getProperty("machine_scale_fan_speed_zero_to_one", "value"))
        if not fan_scale:
            very_cool_fan_speed = round(255 * fan_percent)
        else:
            very_cool_fan_speed = round(fan_percent,1)

        # Get the travel speed percentage
        travel_rate = int(self.getSettingValueByKey("very_cool_feed")) * 60
        lines = data[0].split("\n")

        # The Mins and Maxes become the frame for the cooling movement grid
        for line in lines:
            if line.startswith(";MINX:") or line.startswith(";PRINT.SIZE.MIN.X:"):
                min_x = line.split(":")[1]
            if line.startswith(";MINY:") or line.startswith(";PRINT.SIZE.MIN.Y:"):
                min_y = line.split(":")[1]
            if line.startswith(";MAXX:") or line.startswith(";PRINT.SIZE.MAX.X:"):
                max_x = line.split(":")[1]
            if line.startswith(";MAXY:") or line.startswith(";PRINT.SIZE.MAX.Y:"):
                max_y = line.split(":")[1]

        # Track the fan speed
        for lay in very_cool_layers:
            cur_layer = int(lay)-1
            for num in range(2,len(data)-2,1):
                layer = data[num]
                if "M106 S" in layer:
                    rev_lines = layer.split("\n")
                    rev_lines.reverse()
                    for line in rev_lines:
                        if line.startswith("M106"):
                            fan_speed = str(self.getValue(line, "S"))
                            break
                        if line.startswith("M107"):
                            fan_speed = 0
                            break

                # Get the return-to X Y
                if ";LAYER:" + str(cur_layer) + "\n" in layer:
                    prev_layer = data[num].split("\n")
                    prev_layer.reverse()
                    for prev_line in prev_layer:
                        if " X" in prev_line and " Y" in prev_line:
                            ret_x = self.getValue(prev_line, "X")
                            ret_y = self.getValue(prev_line, "Y")
                            break

                    # Check for a retraction
                    for prev_line in prev_layer:
                        if " E" in prev_line:
                            ret_e = self.getValue(prev_line, "E")
                            my_match = re.search(" F(\d*) E[-(\d.*)]", prev_line)
                            if my_match is not None:
                                retracted = True
                            else:
                                retracted = False
                            break

                    # Final Z of the layer
                    for prev_line in prev_layer:
                        if " Z" in prev_line:
                            ret_z = self.getValue(prev_line, "Z")
                            lift_z = round(ret_z + 1,2)
                            break

                    # Put the travel string together
                    lines = []
                    lines.append(";TYPE:CUSTOM [Little Utilities] Very Cool FanPath")
                    lines.append(f"G0 F{zhop_speed} Z{lift_z}")
                    if not retracted and retr_enabled:
                        lines.append(f"G1 F{retr_speed} E{round(ret_e - float(retr_dist),5)}")
                    lines.append(f"M106 S{very_cool_fan_speed}")
                    x_index = float(min_x)
                    lines.append(f"G0 F{travel_rate} X{min_x} Y{min_y}")
                    while x_index < float(max_x):
                        lines.append(f"G0 X{round(x_index,2)} Y{max_y}")
                        if x_index + very_cool_index_dist > bed_width:
                            break
                        lines.append(f"G0 X{round(x_index + very_cool_index_dist,2)} Y{max_y}")
                        lines.append(f"G0 X{round(x_index + very_cool_index_dist,2)} Y{min_y}")
                        # Break out of the loop if the move will be beyond the bed width
                        if x_index + very_cool_index_dist * 2 > bed_width:
                            break
                        lines.append(f"G0 X{round(x_index + very_cool_index_dist * 2,2)} Y{min_y}")
                        x_index = x_index + very_cool_index_dist * 2
                    if very_cool_y_index:
                        y_index = float(min_y)
                        while y_index < float(max_y):
                            lines.append(f"G0 X{max_x} Y{round(y_index,2)}")
                            if y_index + very_cool_index_dist > bed_depth:
                                break
                            lines.append(f"G0 X{max_x} Y{round(y_index + very_cool_index_dist,2)}")
                            lines.append(f"G0 X{min_x} Y{round(y_index + very_cool_index_dist,2)}")
                            # Break out of the loop if the move will be beyond the bed width
                            if y_index + very_cool_index_dist * 2 > bed_depth:
                                break
                            lines.append(f"G0 X{min_x} Y{round(y_index + very_cool_index_dist * 2,2)}")
                            y_index = y_index + very_cool_index_dist * 2
                    lines.append(f"M106 S{fan_speed}")
                    lines.append(f"G0 F{travel_speed} X{ret_x} Y{ret_y}")
                    lines.append(f"G0 F{zhop_speed} Z{ret_z}")
                    if not retracted and retr_enabled:
                        lines.append(f"G1 F{retr_speed} E{ret_e}")
                    lines.append(f"G0 F{travel_speed} ;CUSTOM END")
                    fan_layer = "\n".join(lines)
                    time_line = re.search(";TIME_ELAPSED:(\d.*)", data[num])
                    data[num] = re.sub(";TIME_ELAPSED:(\d.*)", fan_layer  + "\n" + time_line[0], data[num])
        return

    # Disable ABL for small prints
    def _disable_abl(self, data:str)->str:
        disable_abl_footprint = bool(self.getSettingValueByKey("disable_abl_footprint"))
        disable_abl_time = bool(self.getSettingValueByKey("disable_abl_time"))
        if disable_abl_footprint:
            min_footprint = int(self.getSettingValueByKey("disable_abl_min_footprint"))
        else:
            min_footprint = 999999999
        if disable_abl_time:
            min_print_time = int(self.getSettingValueByKey("disable_abl_min_time")) * 60
        else:
            min_print_time = 999999999
        curaApp = Application.getInstance().getGlobalContainerStack()
        extruder = curaApp.extruderList
        adhesion_extruder_nr = int(curaApp.getProperty("adhesion_extruder_nr", "value"))
        if adhesion_extruder_nr == -1: adhesion_extruder_nr = 0
        adhesion_type = str(curaApp.getProperty("adhesion_type", "value"))
        skirt_gap = int(extruder[adhesion_extruder_nr].getProperty("skirt_gap", "value")) * 2
        skirt_line_count = int(extruder[adhesion_extruder_nr].getProperty("skirt_line_count", "value"))
        brim_width = int(extruder[adhesion_extruder_nr].getProperty("brim_width", "value")) * 2
        raft_margin = int(extruder[adhesion_extruder_nr].getProperty("raft_margin", "value")) * 2
        adhesion_line_width = float(extruder[adhesion_extruder_nr].getProperty("skirt_brim_line_width", "value"))
        raft_base_line_width = float(extruder[adhesion_extruder_nr].getProperty("raft_base_line_width", "value"))
        # Calculate the skirt/brim/raft width to subtract from the footprint
        if adhesion_type == "brim":
            subtract_dim = brim_width - adhesion_line_width * 2
        elif adhesion_type == "skirt":
            if skirt_line_count > 0:
                subtract_dim = skirt_gap + (adhesion_line_width * (skirt_line_count - .5) * 2)
            else:
                subtract_dim = 0.0
        elif adhesion_type == "raft":
            subtract_dim = raft_margin - raft_base_line_width
        else:
            subtract_dim = adhesion_line_width * -1
        # Get the size of the footprint on the build plate
        layer = data[0]
        lines = layer.split("\n")
        for line in lines:
            if line.startswith(";TIME:"):
                print_time = int(line.split(":")[1])
            if line.startswith(";MINX:") or line.startswith(";PRINT.SIZE.MIN.X:"):
                min_x = float(line.split(":")[1])
            if line.startswith(";MINY:") or line.startswith(";PRINT.SIZE.MIN.Y:"):
                min_y = float(line.split(":")[1])
            if line.startswith(";MAXX:") or line.startswith(";PRINT.SIZE.MAX.X:"):
                max_x = float(line.split(":")[1])
            if line.startswith(";MAXY:") or line.startswith(";PRINT.SIZE.MAX.Y:"):
                max_y = float(line.split(":")[1])
        # Determine the actual area of the model
        x_dim = max_x - min_x - subtract_dim
        y_dim = max_y - min_y - subtract_dim
        print_area = round(x_dim * y_dim, 2)
        # If no minimums are set then return with a message
        if not disable_abl_footprint and not disable_abl_time:
            Message(title = "[Little Utilities] ABL is ENABLED", text = "No minimums were set so ABL IS ENABLED.").show()
            return
        # Should ABL be disabled?
        please_disable_abl = False
        if disable_abl_footprint and print_area < min_footprint:
            please_disable_abl = True
        if disable_abl_time and print_time < min_print_time:
            please_disable_abl = True
        # If ABL will not be disabled then return with just a message
        if not please_disable_abl:
            Message(title = "[Little Utilities] ABL is ENABLED", text = "The print is either large or of long duration so ABL IS ENABLED.").show()
            return
        # If ABL will be disabled then comment out the G29 and M420 and display a message
        else:
            lines = data[1].split("\n")
            for index, line in enumerate(lines):
                if line.startswith("G29") or line.startswith("M420"):
                    lines[index] = ";" + line + " Disabled by Little Utilities"
            data[1] = "\n".join(lines)
            Message(title = "[Little Utilities] ABL is DISABLED", text = "The print is either small or of short duration so ABL IS DISABLED for this print.").show()
        return

    # Line Numbering-----------------------------------------------------------
    def _line_numbering(self, data:str)->str:
        prefix = self.getSettingValueByKey("add_line_nr_sentence_number_prefix")
        line_number = int(self.getSettingValueByKey("add_line_nr_starting_number"))
        skip_comments = bool(self.getSettingValueByKey("add_line_nr_skip_comments"))
        for layer_index, layer in enumerate(data):
            lines = layer.split("\n")
            for line_index, line in enumerate(lines):
                if skip_comments:
                    if not line.startswith(";") and line != "":
                        lines[line_index] = f"{prefix}{line_number} {line}"
                        line_number += 1
                elif not skip_comments and line != "":
                        lines[line_index] = f"{prefix}{line_number} {line}"
                        line_number += 1
            data[layer_index] = "\n".join(lines)
        return

    # Debug Practice File with no extrusions or heating -----------------------
    def _practice_file(self, data:str)->str:
        curaApp = Application.getInstance().getGlobalContainerStack()
        start_layer = int(self.getSettingValueByKey("debug_start_layer")) - 1
        end_layer = int(self.getSettingValueByKey("debug_end_layer"))
        debug_autohome_cmd = str(self.getSettingValueByKey("debug_autohome_cmd")).upper()
        debug_leave_temperature_lines = bool(self.getSettingValueByKey("debug_leave_temperature_lines"))
        print_sequence = str(curaApp.getProperty("print_sequence", "value"))
        layer_height = curaApp.getProperty("layer_height", "value")
        layer_height_0 = curaApp.getProperty("layer_height_0", "value")
        # Get the Initial Z
        for index, layer in enumerate(data):
            if ";LAYER:" + str(start_layer) + "\n" in layer:
                practice_start = index
                break
        for index, layer in enumerate(data):
            if end_layer != -1:
                if ";LAYER:" + str(end_layer) + "\n" in layer:
                    practice_end = index
                    break
            elif end_layer == -1:
                if ";LAYER:" in layer:
                    practice_end = index + 1

        if practice_end < practice_start:
            practice_end = practice_start + 1
        lines = data[practice_start - 1 ].split("\n")
        lines.reverse()
        resume_z = 0
        for line in lines:
            if " Z" in line:
                resume_z = self.getValue(line, "Z")
                break
        if resume_z <= 0:
            resume_z = layer_height_0 + (start_layer * layer_height)
        # Remove all the gcode from the layers before the start layer.  Leave the "LAYER: lines
        for num in range(1,practice_start,1):
            data[num] = data[num].split("\n")[0] + "\n"
        # Remove all the gcode from the layers after the end layer.  Leave the "LAYER:" lines
        for num in range(practice_end, len(data),1):
            data[num] = data[num].split("\n")[0] + "\n"
        # Insert a AutoHome and initial Z move to the first remaining layer
        data[practice_start] = debug_autohome_cmd + "\nG1 Z" + str(resume_z) + "\n" + data[practice_start]
        # Remove all extrusions and all the heating lines
        for num in range(1,len(data),1):
            layer = data[num]
            data[num] = re.sub(" E([-+]?[0-9]*\.[0-9]*)", "", data[num])
            if not debug_leave_temperature_lines:
                data[num] = re.sub("M104", ";M104", data[num])
                data[num] = re.sub("M109", ";M109", data[num])
            data[num] = re.sub("M140", ";M140", data[num])
            data[num] = re.sub("M190", ";M190", data[num])
        # Insert a parking move at the end of the last remaining layer
        data[practice_end] += "G1 X0 Y0\nM104 S0\nM140 S0\nM118 END OF GCODE\n"
        return

    # One-at-a-Time Final Z move (to clear the tops of taller prints)----------
    def _final_z(self, data:str)->str:
        transit_hgt = 0
        z_up = 0
        print_sequence = str(Application.getInstance().getGlobalContainerStack().getProperty("print_sequence", "value"))
        if print_sequence == "all_at_once":
            z_up = 5
        machine_height = int(Application.getInstance().getGlobalContainerStack().getProperty("machine_height", "value"))
        speed_z = int(Application.getInstance().getGlobalContainerStack().getProperty("machine_max_feedrate_z", "value")) * 60
        if speed_z > 2700:
            speed_z = 2700
        lines = data[0].split("\n")
        for line in lines:
            if "MAXZ:" in line or "MAX.Z:" in line:
                transit_hgt = round(float(line.split(":")[1]) + z_up, 2)
                if transit_hgt > machine_height:
                    transit_height = machine_height
                    break
        data[len(data)-1] = f"G0 F{speed_z} Z{transit_hgt} ; {print_sequence} final Z move\n" + data[len(data)-1]
        return

    # One-at-a-Time Adjust the print temperature on a per model basis----------
    def _adjust_temps_per_model(self, data:str)->str:
        print_sequence = str(Application.getInstance().getGlobalContainerStack().getProperty("print_sequence", "value"))
        if print_sequence == "all_at_once":
            Message(title = "[Little Utilities - Adjust Temps]", text = "This script is for One-At-A-Time projects only.  The script will exit.").show()
            return
        extruder = Application.getInstance().getGlobalContainerStack().extruderList
        print_temperature = int(extruder[0].getProperty("material_print_temperature", "value"))
        initial_print_temperature = int(extruder[0].getProperty("material_print_temperature_layer_0", "value"))
        # If the initial print temperature is different than the print temperature make the insertion at the LAYER:1's
        if print_temperature != initial_print_temperature:
            insert_at_layer = "1"
        else:
            insert_at_layer = "0"
        # Get the temperatures
        temperatures = str(self.getSettingValueByKey("temperature_list")) #Example for six models: 200,205,210,215,220,225
        temperature_list = temperatures.split(",")
        counter = 0
        # Make a list to hold the model names
        model_list = []
        # In case of list length discrepancies
        model_count_err = False
        for num in range(2,len(data)-1):
            if ";LAYER:" + insert_at_layer + "\n" in data[num]:
                lines = data[num].split("\n")
                # Get the model name and add it to the model list
                for line in lines:
                    if line.startswith(";MESH:") and not "NONMESH" in line:
                        model_name = line.split(":")[1]
                        if not model_name.endswith(")"):
                            model_name = model_name + "(0)"
                        model_list.append(model_name) # Cut off the ';MESH:' part of the line
                # Comment out the temperature line that Cura inserts at the end of layer 0
                if num > 2:
                    data[num - 1] = re.sub("M109", ";M109", data[num - 1])
                # if there is an M104 line mid-layer then replace it with the proper temperature
                if "M104" in data[num]:
                    data[num] = re.sub("M104 S(\d*)\n", "M104 S" + str(temperature_list[counter]) + " ; maintain temperature for " + model_list[len(model_list) - 1] + "\n", data[num])
                if insert_at_layer == "1":
                    if "M104" in data[num - 1]:
                        data[num - 1] = re.sub("M104 S", ";M104 S", data[num - 1])
                # If the Init Layer Temp is different then change the 'M109 S' to 'M109 R' in case the init temperature is lower than the new temperature.
                if insert_at_layer == "1":
                    data[num - 2] = re.sub("M109 S", "M109 R", data[num - 2])
                insert_pt = re.search(";LAYER_COUNT:", data[num - 1])
                # Pad the temperature list if it is shorter than the model list.  Throw an error so the user is informed.
                if len(temperature_list) < len(model_list):
                    model_count_err = True
                    temperature_list.append(print_temperature)
                # Add the new temperature line to the end of the previous layer
                if insert_pt is not None: # Insert the temperature line in the previous layer right above Layer_Count
                    data[num - 1] = data[num - 1][0:insert_pt.span()[0]] + "M109 R" + str(temperature_list[counter]) + " ;adjust temperature for " + model_list[len(model_list) - 1] + "\n" + data[num - 1][insert_pt.span()[0]:]
                else:
                    data[num - 1] += "M109 R" + str(temperature_list[counter]) + " ;temp change\n"
                counter += 1
        if model_count_err:
            Message(title = "[Little Utilities - Adjust Temps]", text = "The 'Temperature List' doesn't contain temperatures for all the models.  Extra models were set to 'Print Temperature'.").show()
        # Add these items to the end of the opening paragraph of the gcode
        data[0] += "; Print Order          Model Name                  Temperature\n"
        # Add these items to the message
        message_string = ";_Print Order________Model Name______________Temperature\n"
        # Put together the messages that will show when the file is saved.
        try:
            for num in range(0,len(model_list) + 1):
                space_num = " " * (40 - len(model_list[num])) # Adjust the spacing so it looks good
                data[0] += ";      " + str(num + 1) + "       " + model_list[num] + space_num + str(temperature_list[num]) + "\n"
                dash_num = "_" * (37 - len(model_list[num])) # Adjust the spacing so it looks good
                message_string += ";_____" + str(num + 1) + "_______" + model_list[num] + dash_num + str(temperature_list[num]) + "\n"
        except:
            pass
        message_string = message_string[0:-1] # Remove the last newline
        Message(title = "[Little Utilities - Adjust Temps]", text = message_string).show()
        return

    # Enforce the Print and/or Travel speeds that might have been affected by Cura Flow Compensation.  Speeds higher than the settings will be lowered to the setting speed.  This works per feature and per extruder.
    def _speed_limits(self, data:str)->str:
        curaApp = Application.getInstance().getGlobalContainerStack()
        extruder = curaApp.extruderList
        print_speed = int(extruder[0].getProperty("speed_print", "value")) * 60
        initial_print_speed = int(extruder[0].getProperty("speed_print_layer_0", "value")) * 60
        travel_speed = int(extruder[0].getProperty("speed_travel", "value")) * 60
        initial_travel_speed = int(extruder[0].getProperty("speed_travel_layer_0", "value")) * 60
        speed_slowdown_layers = int(curaApp.getProperty("speed_slowdown_layers", "value"))
        extruder_count = curaApp.getProperty("machine_extruder_count", "value")
        extruder_speed_list = []
        extruder_speed = []
        cur_extruder = 0
        new_speed = print_speed
        if extruder_count > 1:
            for num in range(0, 10, 1):
                lines = data[num].split("\n")
                for line in lines:
                    if ";LAYER:0" in line:
                        break
                    if line.startswith("T"):
                        cur_extruder = self.getValue(line, "T")
        for num in range(0, extruder_count):
            extruder_speed.append(extruder[num].getProperty("speed_print", "value") * 60)
            extruder_speed.append(extruder[num].getProperty("skirt_brim_speed", "value") * 60)
            extruder_speed.append(extruder[num].getProperty("speed_wall_x", "value") * 60)
            extruder_speed.append(extruder[num].getProperty("speed_wall_0", "value") * 60)
            extruder_speed.append(extruder[num].getProperty("speed_infill", "value") * 60)
            extruder_speed.append(extruder[num].getProperty("speed_topbottom", "value") * 60)
            extruder_speed.append(extruder[num].getProperty("speed_support", "value") * 60)
            extruder_speed.append(extruder[num].getProperty("speed_support_interface", "value") * 60)
            extruder_speed.append(extruder[num].getProperty("speed_prime_tower", "value") * 60)
            extruder_speed.append(extruder[num].getProperty("bridge_skin_speed", "value") * 60)
            extruder_speed_list.append(extruder_speed)
            extruder_speed = []

        # This list is used from layer 1 up.
        feature_name_list = ["PRINT_SPEED", ";TYPE:SKIRT", ";TYPE:WALL-INNER", ";TYPE:WALL-OUTER", ";TYPE:FILL", ";TYPE:SKIN", ";TYPE:SUPPORT", ";TYPE:SUPPORT-INTERFACE", ";TYPE:PRIME-TOWER", ";BRIDGE"]
        theindex = 0
        if speed_slowdown_layers == 0:
            initial_print_speed = print_speed
            initial_travel_speed = travel_speed
        speeds_to_check = self.getSettingValueByKey("speeds_to_check")
        for index, layer in enumerate(data):
            if ";LAYER:0" in data[index]:
                start_at = index + 1
                lines = data[index].split("\n")
                for l_index, line in enumerate(lines):
                    # Track the tool number
                    if line.startswith("T"):
                        cur_extruder = self.getValue(line, "T")
                        continue
                    # Check the initial layer printing speeds
                    if speeds_to_check != "travel_speeds":
                        if self.getValue(line, "G") in (1,2,3):
                            if " F" in line:
                                cur_speed = self.getValue(line, "F")
                                if cur_speed > initial_print_speed:
                                    lines[l_index] = re.sub("F((\d+(\.\d*)?)|(\.\d+)$)", "F" + str(round(initial_print_speed)), lines[l_index]) + " ; Speed was " + "/" + str(round(cur_speed / 60))
                    # Check the initial layer travel speeds
                    if speeds_to_check != "print_speeds":
                        if self.getValue(line, "G") == 0:
                            if " F" in line:
                                cur_speed = self.getValue(line, "F")
                                if cur_speed > initial_travel_speed:
                                    lines[l_index] = re.sub("F((\d+(\.\d*)?)|(\.\d+)$)", "F" + str(round(initial_travel_speed)), lines[l_index]) + " ; Speed was " + "/" + str(round(cur_speed / 60))
                data[index] = "\n".join(lines)
                break
            if not ";LAYER:0" in data[index]:
                continue
        # Layers above layer:0
        for num in range(start_at, len(data) - 1, 1):
            layer = data[num].split("\n")
            for l_index, line in enumerate(layer):
                # Track the tool number
                if line.startswith("T"):
                    cur_extruder = self.getValue(line, "T")
                    continue
                # Find the correct By Feature speed
                if line.startswith(";TYPE:"):
                    try:
                        theindex = feature_name_list.index(line)
                    except ValueError:
                        theindex = 0
                    new_speed = extruder_speed_list[cur_extruder][theindex]
                # Check the printing speeds
                if speeds_to_check != "travel_speeds":
                    if self.getValue(line, "G") in (1,2,3):
                        if " F" in line:
                            cur_speed = self.getValue(line, "F")
                            if cur_speed > new_speed:
                                layer[l_index] = re.sub("F((\d+(\.\d*)?)|(\.\d+)$)", "F" + str(round(new_speed)), layer[l_index]) + " ; Speed was " + str(round(cur_speed)) + "/" + str(round(cur_speed / 60))
                # Check the travel speeds
                if speeds_to_check != "print_speeds":
                    if self.getValue(line, "G") == 0:
                        if " F" in line:
                            cur_speed = self.getValue(line, "F")
                            if cur_speed > travel_speed:
                                layer[l_index] = re.sub("F((\d+(\.\d*)?)|(\.\d+)$)", "F" + str(round(travel_speed)), layer[l_index]) + " ; Speed was " + str(round(cur_speed)) + "/" + str(round(cur_speed / 60))
            data[num] = "\n".join(layer)
        return

    # Debug - add data item and line number within each data item--------------
    def _data_num_and_line_nums(self, data:str)->str:
        for layer_index, layer in enumerate(data):
            lines = layer.split("\n")[:-1]
            new_lines = []
            for line_number, line in enumerate(lines):
                if line_number == 0: line_number = str(line_number) + "000000000000"
                new_lines.append(f"{line.ljust(55)}; DATA [{layer_index}], LINE {line_number}")
            data[layer_index] = "\n".join(new_lines) + "\n"
        return

    # Comment out the Wiping movement line after Infill, Outer Wall, or Both
    def _kill_wipes(self, data: str) -> str:
        curaApp = Application.getInstance().getGlobalContainerStack()
        extruder = curaApp.extruderList
        # Deterimine if wiping is enabled.  Don't bother going through the code if it is not.
        if float(extruder[0].getProperty("wall_0_wipe_dist", "value")) > 0.0:
            ow_wipe_enabled = True
        else:
            ow_wipe_enabled = False
        if float(extruder[0].getProperty("infill_wipe_dist", "value")) > 0.0:
            infill_wipe_enabled = True
        else:
            infill_wipe_enabled = False
        start_layer = self.getSettingValueByKey("kill_wipe_from") - 1
        end_layer = self.getSettingValueByKey("kill_wipe_to")
        # Get the indexes of the Start and End layers
        if end_layer == -1 or end_layer <= start_layer:
            end_index = len(data) - 1
        else:
            end_layer = end_layer - 1
        wipe_to_kill = self.getSettingValueByKey("wipe_to_kill")
        for num in range(2, len(data) - 1):
            layer = data[num]
            if ";LAYER:" + str(start_layer) + "\n" in layer:
                start_index = num
                break
        if end_layer != -1:
            end_layer
            for num in range(start_index, len(data) - 1):
                layer = data[num]
                if ";LAYER:" + str(end_layer) + "\n" in layer:
                    end_index = num
                    break
        elif end_layer == -1:
            end_index = len(data) - 1

        # Message the user if they selected an option that isn't relevant
        if wipe_to_kill in ["infill_wipe", "both_wipe"] and not infill_wipe_enabled:
            data[0] += ";  [Little Utilities] Infill Wipe Distance is 0.0 so no changes were made to Infill.\n"
            Message(title = "[Little Utilities] Kill Wipe - Infill", text = "Did not run because the Infill Wipe Distance is 0.0.").show()

        if wipe_to_kill in ["outer_wall_wipe", "both_wipe"] and not ow_wipe_enabled:
            data[0] += ";  [Little Utilities] Outer Wall Wipe Distance is 0.0 so no changes were made to Outer Wall.\n"
            Message(title = "[Little Utilities] Kill Wipe - Outer Wall", text = "Did not run because the Outer Wall Wipe Distance is 0.0.").show()

        # If 'outer-wall' or 'both' are selected check for outer-wall wipes
        if wipe_to_kill != "infill_wipe" and ow_wipe_enabled:
            for num in range(start_index, end_index, 1):
                layer = data[num]
                nailed_it = False
                if ";TYPE:WALL-OUTER" in layer:
                    lines = layer.split("\n")
                    for l_num, line in enumerate(lines):
                        if not ";TYPE:WALL-OUTER" in line:
                            continue
                        else:
                            # If Type:outer-wall then go down to the first ';' and work back up to the last extrusion.
                            for semi_num in range(l_num + 1, len(lines)-1):
                                if lines[semi_num].startswith(";"):
                                    for c_num in range(semi_num-1, l_num, -1):
                                        if re.match("G1 X(\d.*) Y(\d.*) E(\d.*)", lines[c_num]) is not None:
                                            set_speed = ""
                                            # If the line being commented has an F parameter grab it and insert it for following moves.
                                            if " F" in lines[c_num + 1]:
                                                f_val = self.getValue(lines[c_num + 1], "F")
                                                set_speed = "\nG0 F" + str(f_val)
                                            lines[c_num + 1] = ";" + lines[c_num + 1] + set_speed
                                            nailed_it = True
                                            break
                                # Exit this for loop and continue checking the layer for additional Outer-Wall sections
                                if nailed_it:
                                    nailed_it = False
                                    break
                data[num] = "\n".join(lines)
        # If 'Infill' or 'Both' are selected check for Infill wipes
        if wipe_to_kill != "outer_wall_wipe" and infill_wipe_enabled:
            for num in range(start_index, end_index, 1):
                layer = data[num]
                nailed_it = False
                if ";TYPE:FILL" in layer:
                    lines = layer.split("\n")
                    for l_num, line in enumerate(lines):
                        if not ";TYPE:FILL" in line:
                            continue
                        else:
                            # If Type:Fill then go down to the first ';' and work back up to the last extrusion.
                            for semi_num in range(l_num + 1, len(lines)-1):
                                if lines[semi_num].startswith(";"):
                                    for c_num in range(semi_num-1, l_num, -1):
                                        if re.match("G1 X(\d.*) Y(\d.*) E(\d.*)", lines[c_num]) is not None:
                                            set_speed = ""
                                            # I the line being commented has an F parameter grab it and insert it for following moves.
                                            if " F" in lines[c_num + 1]:
                                                f_val = self.getValue(lines[c_num + 1], "F")
                                                set_speed = "\nG0 F" + str(f_val)
                                            lines[c_num + 1] = ";" + lines[c_num + 1] + set_speed
                                            nailed_it = True
                                            break
                                # Exit this for loop and continue checking the layer for additional Infill sections
                                if nailed_it:
                                    nailed_it = False
                                    break
                data[num] = "\n".join(lines)
        return

    # Format the startup and ending gcodes so they look nice.  This will move any comments so they line up
    def format_string(self, any_gcode_str: str):
        # Format the purge or travel-to-start strings.  No reason they shouldn't look nice.
        temp_lines = any_gcode_str.split("\n")
        gap_len = 0
        for temp_line in temp_lines:
            if ";" in temp_line and not temp_line.startswith(";"):
                if gap_len - len(temp_line.split(";")[0]) + 1 < 0:
                    gap_len = len(temp_line.split(";")[0]) + 1
        if gap_len < 30: gap_len = 30
        for temp_index, temp_line in enumerate(temp_lines):
            if ";" in temp_line and not temp_line.startswith(";"):
                temp_lines[temp_index] = temp_line.replace(temp_line.split(";")[0], temp_line.split(";")[0] + str(" " * (gap_len - 1 - len(temp_line.split(";")[0]))),1)
        any_gcode_str = "\n".join(temp_lines)
        return any_gcode_str

    def _print_temp_change(self, alt_data: str):
        # Exit if the script is not enabled
        if not bool(self.getSettingValueByKey("temp_override_enable")):
            return alt_data
        curaApp = Application.getInstance().getGlobalContainerStack()
        machine_extruder_count = int(curaApp.getProperty("machine_extruder_count", "value"))
        machine_extruders_enabled_count = int(curaApp.getProperty("extruders_enabled_count", "value"))
        # Exit if the printer has more than 2 extruders
        if machine_extruder_count > 2:
            Message(title = "[Little Utilities]", text = "Max Temperature Override - Did not run because the Extruder Count > 2").show()
            return alt_data
        # Exit if the printer has a mixing hot end
        shared_heater = bool(curaApp.getProperty("machine_extruders_share_heater", "value"))
        shared_nozzle = bool(curaApp.getProperty("machine_extruders_share_nozzle", "value"))
        if shared_heater or shared_nozzle:
            Message(title = "[Little Utilities]", text = "Max Temperature Override - Did not run because it is not compatible with mixing hot ends.").show()
            return alt_data

        # If only one extruder is enabled then treat it as a single extruder printer and change all the temperatures
        if machine_extruders_enabled_count == 1:
            machine_extruder_count = 1

        # The Tool to be adjusted deterimines which function to go through
        which_tool = "0"
        if machine_extruder_count == 2:
            if self.getSettingValueByKey("temp_override_extruder_select") == "t1_only":
                which_tool = "1"
            elif self.getSettingValueByKey("temp_override_extruder_select") == "both_extruders":
                which_tool = "Both"
        if machine_extruder_count == 1 or (machine_extruder_count == 2 and which_tool == "Both"):
            alt_data = self._all_changes(alt_data)
            return alt_data
        elif machine_extruder_count == 2 and which_tool != "Both":
            alt_data = self._tool_changes(alt_data, which_tool)
            return alt_data

    # Go though this if all the temperatures are being changed
    def _all_changes(self, alt_data: str) -> str:
        max_temp = 0
        new_temp = 0
        for num in range(1, len(alt_data)-1):
            if "M104" in alt_data[num] or "M109" in alt_data[num]:
                lines = alt_data[num].split("\n")
                for index, line in enumerate(lines):
                    if line.startswith("M104 S") or line.startswith("M109 S") or line.startswith("M104 T") or line.startswith("M109 T"):
                        cur_temp = int(self.getValue(line, "S"))
                        new_temp = cur_temp * 2
                        lines[index] = line.replace("S" + str(cur_temp), "S" + str(new_temp), 1)
                    if line.startswith("M109 R"):
                        cur_temp = int(self.getValue(line, "R"))
                        new_temp = cur_temp * 2
                        lines[index] = line.replace("R" + str(cur_temp), "R" + str(new_temp), 1)
                # Track the highest temperture so the user can be informed via a message
                if new_temp > max_temp:
                    max_temp = new_temp
                alt_data[num] = "\n".join(lines)
        alt_data[1] = ";  [Little Utilities] The print temperatures have been doubled.  The new temperatures are as high as " + str(max_temp) + "°.\n" + alt_data[1]
        msg_text = "The post processor 'Little Utilities | Max Temp Override' is enabled. All the temperatures in the Cura settings have been doubled in the Gcode.  The new print temperatures are as high as " + str(max_temp) + "°.  Your printer and the material must be capable of handling the high temperatures.  It is up to the user to determine the suitablility of High Temperature Overrides."
        Message(title = "HIGH TEMP PRINT WARNING", text = msg_text).show()
        return alt_data

    # Go though this one if the temperature changes are for a specific extruder only
    def _tool_changes(self, alt_data: str, tool_num: str) -> str:
        active_tool = "0"
        max_temp = 0
        new_temp = 0
        for num in range(1, len(alt_data)-1):
            lines = alt_data[num].split("\n")
            # Track the active tool number
            for index, line in enumerate(lines):
                if line.startswith("T0"):
                    active_tool = "0"
                elif line.startswith("T1"):
                    active_tool = "1"
                # Change the M104 and M109 lines of the active tool when it is equal to tool_num
                if tool_num == active_tool:
                    if line.startswith("M104 S") or line.startswith("M109 S"):
                        cur_temp = int(self.getValue(line, "S"))
                        new_temp = cur_temp * 2
                        lines[index] = line.replace("S" + str(cur_temp), "S" + str(new_temp), 1)
                    if line.startswith("M109 R"):
                        cur_temp = int(self.getValue(line, "R"))
                        new_temp = cur_temp * 2
                        lines[index] = line.replace("R" + str(cur_temp), "R" + str(new_temp), 1)
                # Change the heat up and cool down lines when the tool_num is inactive
                else:
                    if line.startswith("M104 T" + tool_num) or line.startswith("M109 T" + tool_num):
                        cur_temp = int(self.getValue(line, "S"))
                        new_temp = cur_temp * 2
                        lines[index] = line.replace("S" + str(cur_temp), "S" + str(new_temp), 1)
                # Cura doesn't add 'M109 T R' lines for the inactive tool so that situation is ignored
                # Track the highest temperture so the user can be informed via a message
                if new_temp > max_temp:
                    max_temp = new_temp
                alt_data[num] = "\n".join(lines)
        alt_data[1] = ";  [Little Utilities] The print temperatures for Tool 'T" + tool_num + "' have been doubled.  The new print temperatures are as high as " + str(max_temp) + "°.\n" + alt_data[1]
        msg_text = "The post processor 'Little Utilities | Max Temperature Override' is enabled. All the temperatures in the Cura settings for Tool 'T" + tool_num + "' have been doubled in the Gcode.  The new print temperatures are as high as " + str(max_temp) + "°.  Your printer and the material must be capable of handling the high temperatures.  It is up to the user to determine the suitablility of High Temperature Overrides."
        Message(title = "HIGH TEMP PRINT WARNING", text = msg_text).show()
        return

    def _move_tool_changes(self, alt_data: str) -> str:
        curaApp = Application.getInstance().getGlobalContainerStack()
        if not bool(curaApp.getProperty("prime_tower_enable", "value")):
            Message(title = "[Little Utilities]", text = "Move Tool Changes ... Did not run because 'Prime Tower' is not enabled.").show()
            return alt_data
        machine_extruder_count = int(curaApp.getProperty("machine_extruder_count", "value"))
        if machine_extruder_count < 2:
            return alt_data
        start_index = 2
        for num in range(2, len(alt_data) - 1):
            if ";LAYER:0" in alt_data[num]:
                start_index = num + 1
                break
        pull_lines = ""
        extruder = curaApp.extruderList
        prime_rad = curaApp.getProperty("prime_tower_size", "value") * 0.5
        prime_x = curaApp.getProperty("prime_tower_position_x", "value") - prime_rad
        prime_y = curaApp.getProperty("prime_tower_position_y", "value") + prime_rad
        layer_z = curaApp.getProperty("layer_height", "value")
        prime_feed = curaApp.getProperty("speed_prime_tower", "value") * 60
        if extruder[0].getProperty("retraction_hop_after_extruder_switch", "value"):
            paste_line = 1
        else:
            paste_line = 0
        for num in range(start_index, len(alt_data)-1):
            if not ";TYPE:PRIME-TOWER" in alt_data[num]:
                continue
            lines = alt_data[num].split("\n")
            modified_data = ""
            for index, line in enumerate(lines):
                if line.startswith("M135") or line.startswith("T"):
                    pull_lines = ""
                    p_index = index
                    pull_lines = f"\nG1 F{prime_feed} X{prime_x} Y{prime_y}"
                    # Pull out the lines before the travel moves to the prime tower
                    while not lines[p_index].startswith(";") and not " Z" in lines[p_index]:
                        pull_lines += "\n" + lines[p_index]
                        lines.pop(p_index)
                    if lines[p_index].startswith("G0 F") and " Z" in lines[p_index]:
                        modified_data += lines[p_index] + "\n"
                        continue
                    # For situations where there is no MESH:NONMESH line
                    if lines[p_index].startswith(";TYPE:") and pull_lines != "":
                        lines[p_index] += pull_lines
                        modified_data += lines[p_index] + "\n"
                    continue
                # Add the pulled lines back in after travel to the prime tower
                if line.startswith(";TYPE:PRIME-TOWER") and pull_lines != "":
                    lines[index + paste_line] += pull_lines
                    pull_lines = ""
                modified_data += lines[index] + "\n"
            alt_data[num] = modified_data[:-1]
        return alt_data

    def _dual_ext_to_single(self, data: str) -> str:
        convert_m109 = self.getSettingValueByKey("dual_convert_M109")
        for num in range(2, len(data)-1):
            lines = data[num].split("\n")
            for index, line in enumerate(lines):
                if line.startswith("T0"):
                    lines[index] = "M117 Tool T0\nM118 Tool T0\n;T0\nM300 P150"
                if line.startswith("T1"):
                    lines[index] = "M117 Tool T1\nM118 Tool T1\n;T1\nM300 P150\nG4 P300\nM300 P150"
                if line.startswith("M104") or line.startswith("M109"):
                    if convert_m109:
                        lines[index] = re.sub("M109", "M104", line)
                    if "T" in line:
                        tool_num = self.getValue(line, "T")
                        lines[index] = re.sub(" T(\d)", "", line) + " ;T" + str(tool_num)
            data[num] = "\n".join(lines)
        return