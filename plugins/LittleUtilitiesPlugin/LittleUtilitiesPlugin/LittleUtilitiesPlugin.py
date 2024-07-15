#------------------------------------------------------------------------------------------------------------------------------------
# Initial Copyright(c) 2024 Greg Foresi (GregValiant)
#
# Little Utilities is released under the terms of the AGPLv3 or higher.
#
# Description:  A collection of scripts that can be useful in certain situations.
#
#------------------------------------------------------------------------------------------------------------------------------------
#     1) Remove Comments - Remove semi-colons and everything to the right of a semi-colon.  There are options.  (Thanks to @Torgeir)
#     2) Add Extruder End code - A bug fix - this adds any 'Extruder End Gcode' of the last extruder used to the end of the file.
#     4) Add Data Headers - A debugging utility, it adds comments between the data sections
#     5) Lift Head Parking - adds a park move to the "Lift Head" cooling option for small layers.  The move is to just off the print.  It returns to the print after the G4 dwell is complete.
#     6) Change Printer Settings - Max Feedrate, Max Accel, Home Offsets, Steps/mm.  (There is no Max for Jerk)
#     7) Very Cool FanPath - Raise 1mm and follow a zigzag path across the print with just the Layer Cooling Fan running.
#     8) Disable ABL for small models.  The user defines 'small' and models that fall below that area on the build plate cause G29 and M420 to be commented out of the StartUp Gcode.  There is also a 'minimum time' option.
#     9) Gcode Line Numbering - Numbers the lines in the gcode.  A prefix is an option.  (authored by: Slashee the Cow)
#     10) Debug Gcode File - A debug tool that removes all the extrusions and heating lines from a range of layers or the whole file.  The result is a 'Movement Only' file so users can check a toolpath.
#     11) One-at-a-Time Final Z - A bug fix that adds a move up to the transit (print MAXZ) height before the ending Gcode.  Prevents a crash if the last print is shorter than others.
#     12) Adjust Temperatures One-at-a-Time - Enter a list of temperatures and each succesive model will print at the assigned temperature.
#     13) Enable Speed Enforcement - If Flow Rate Compensation alters some print speeds to very high values this script will reset them to the speeds in the Cura settings.  The speeds are checked per feature and per extruder.  Speeds might be lowered, never raised.
#
#------------------------------------------------------------------------------------------------------------------------------------

import re
from collections import OrderedDict
from UM.Message import Message
from UM.Extension import Extension
from UM.Application import Application
from UM.Settings.SettingDefinition import SettingDefinition
from UM.Settings.DefinitionContainer import DefinitionContainer
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Logger import Logger

class LittleUtilitiesPlugin(Extension):
    def __init__(self):
        super().__init__()

        self._application = Application.getInstance()
        self._i18n_catalog = None

        self._settings_dict = OrderedDict()
        self._settings_dict["little_utilities_enable"] = {
            "label": "Enable Little Utilities",
            "description": "Make the Utilities available for use.",
            "type": "bool",
            "default_value": False,
            "settable_per_mesh": False,
            "settable_per_extruder": False,
            "settable_per_meshgroup": False,
            "enabled": True
        }
        self._settings_dict["remove_comments"] = {
            "label": "    Remove Comments",
            "description": "Removes all semi-colons and any text to the right of the semi-colon.",
            "type": "bool",
            "default_value": False,
            "enabled": "little_utilities_enable"
        }
        self._settings_dict["remove_comments_inc_opening"] = {
            "label": "        Include opening paragraph:",
            "description": "The opening generally consists of comments only and includes from 'Flavor' to 'MAXZ'.  (The 'POSTPROCESSED' line is added after the scripts have all run.)",
            "type": "bool",
            "default_value": True,
            "enabled": "remove_comments and little_utilities_enable"
        }
        self._settings_dict["remove_comments_inc_startup"] = {
            "label": "        Include StartUp Gcode:",
            "description": "The StartUp section is from 'generated with...' to ';LAYER_COUNT:'.",
            "type": "bool",
            "default_value": True,
            "enabled": "remove_comments and little_utilities_enable"
        }
        self._settings_dict["remove_comments_leave_layer_lines"] = {
            "label": "        Remove ';LAYER:' lines:",
            "description": "If unchecked then the ';LAYER:' lines will be left in.  That makes searching the gcode easier.  Post processors that run after this one may require the Layer lines.",
            "type": "bool",
            "default_value": False,
            "enabled": "remove_comments and little_utilities_enable"
        }
        self._settings_dict["remove_comments_inc_ending"] = {
            "label": "        Include Ending Gcode:",
            "description": "The Ending Gcode may have comments.",
            "type": "bool",
            "default_value": False,
            "enabled": "remove_comments and little_utilities_enable"
        }
        self._settings_dict["add_extruder_end"] = {
            "label": "    Add Last Extruder Ending Gcode",
            "description": "Adds the Ending Gcode of the last extruder used in the print prior to the regular Ending Gcode.",
            "type": "bool",
            "default_value": False,
            "enabled": "little_utilities_enable"
        }
        self._settings_dict["lift_head_park"] = {
            "label": "    Lift Head Parking",
            "description": "For small layers - this adds a move off the print (to the skirt/brim area) so the nozzle doesn't ooze on the print.",
            "type": "bool",
            "default_value": False,
            "enabled": "little_utilities_enable"
        }
        self._settings_dict["very_cool_enable"] = {
            "label": "    Very Cool Fanpath",
            "description": "Creates a fanpath that runs up and back 1mm above the print with the fan running to give extra cooling.  Helps lower the amount of sticking to support-interfaces.",
            "type": "bool",
            "default_value": False,
            "enabled": "little_utilities_enable"
        }
        self._settings_dict["very_cool_layer"] = {
            "label": "        End of which layer(s)?",
            "description": "Pick the layer(s) from the Cura preview.  The printhead will move in the 'Y' in a grid toolpath 1.0mm above the current Z (no extrusions) with the Layer Cooling Fan speed at the percent you enter here.  The 'X' index is 10mm.  For multiple layers delimit with a comma (',') and delimit ranges of layers with a dash ('-') do not add spaces.  Ex: 5,6,12-25,30,45-55 or 200-225.",
            "type": "str",
            "default_value": "1-227",
            "unit": "Lay num  ",
            "enabled": "very_cool_enable and little_utilities_enable"
        }
        self._settings_dict["very_cool_feed"] = {
            "label": "        FanPath Speed mm/sec",
            "description": "The Speed to run the printhead along the cooling fan path.",
            "type": "int",
            "default_value": 50,
            "minimum_value": 7,
            "minimum_value_warning": 10,
            "maximum_value": 400,
            "unit": "mm/sec  ",
            "enabled": "very_cool_enable and little_utilities_enable"
        }
        self._settings_dict["very_cool_fan"] = {
            "label": "        FanPath Cooling Fan %",
            "description": "The % of the Fan Speed to apply to the cooling runs.",
            "type": "int",
            "default_value": 100,
            "minimum_value": 25,
            "maximum_value": 100,
            "unit": "%  ",
            "enabled": "very_cool_enable and little_utilities_enable"
        }
        self._settings_dict["very_cool_index_dist"] = {
            "label": "        Index distance",
            "description": "The distance to move the head between each pass across the print.",
            "type": "int",
            "default_value": 25,
            "minimum_value": 5,
            "maximum_value": 50,
            "unit": "mm  ",
            "enabled": "very_cool_enable and little_utilities_enable"
        }
        self._settings_dict["very_cool_y_index"] = {
            "label": "        Add Y indexed path",
            "description": "The toolpath is an X zigzag. Enabling the Y will create a grid toolpath. That doubles the cooling effect and takes twice as long.",
            "type": "bool",
            "default_value": False,
            "enabled": "very_cool_enable and little_utilities_enable"
        }
        self._settings_dict["change_printer_settings"] = {
            "label": "    Change Printer Settings",
            "description": "Add gcode commands to a file to change the internal printer settings.",
            "type": "bool",
            "default_value": False,
            "enabled": "little_utilities_enable"
        }
        self._settings_dict["change_feedrate"] = {
            "label": "        Change Printer Max Speeds",
            "description": "Change the max feedrate for any axes. Blank entries mean No Change.",
            "type": "bool",
            "default_value": False,
            "enabled": "change_printer_settings and little_utilities_enable"
        }
        self._settings_dict["change_feedrate_x"] = {
            "label": "            Max X Feedrate",
            "description": "Change the Max X feedrate.",
            "type": "str",
            "default_value": "",
            "unit": "mm/sec  ",
            "enabled": "change_printer_settings and change_feedrate and little_utilities_enable"
        }
        self._settings_dict["change_feedrate_y"] = {
            "label": "            Max Y Feedrate",
            "description": "Change the Max Y feedrate.",
            "type": "str",
            "default_value": "",
            "unit": "mm/sec  ",
            "enabled": "change_printer_settings and change_feedrate and little_utilities_enable"
        }
        self._settings_dict["change_feedrate_z"] = {
            "label": "            Max Z Feedrate",
            "description": "Change the Max Z feedrate.",
            "type": "str",
            "default_value": "",
            "unit": "mm/sec  ",
            "enabled": "change_printer_settings and change_feedrate and little_utilities_enable"
        }
        self._settings_dict["change_feedrate_e"] = {
            "label": "            Max E Feedrate",
            "description": "Change the Max E feedrate.",
            "type": "str",
            "default_value": "",
            "unit": "mm/sec  ",
            "enabled": "change_printer_settings and change_feedrate and little_utilities_enable"
        }
        self._settings_dict["change_xy_accel"] = {
            "label": "        Change Max X-Y Acceleration",
            "description": "Change the Max Accel for the X and/or Y axes. They can be unequal.  Blank entries mean No Change.",
            "type": "bool",
            "default_value": False,
            "enabled": "change_printer_settings and little_utilities_enable"
        }
        self._settings_dict["change_accel_x"] = {
            "label": "            Max X Acceleration",
            "description": "Change the Max X Acceleration.",
            "type": "str",
            "default_value": "",
            "unit": "mm/sec²  ",
            "enabled": "change_printer_settings and change_xYaccel and little_utilities_enable"
        }
        self._settings_dict["change_accel_y"] = {
            "label": "            Max Y Acceleration",
            "description": "Change the Max Y Acceleration.",
            "type": "str",
            "default_value": "",
            "unit": "mm/sec²  ",
            "enabled": "change_printer_settings and change_xYaccel and little_utilities_enable"
        }
        self._settings_dict["change_home_offset"] = {
            "label": "        Change Home Offsets",
            "description": "Change the Home Offsets. Blank entries mean No Change.",
            "type": "bool",
            "default_value": False,
            "enabled": "change_printer_settings and little_utilities_enable"
        }
        self._settings_dict["change_home_x"] = {
            "label": "            Home Offset X",
            "description": "Change the X home offset.",
            "type": "str",
            "default_value": "",
            "enabled": "change_printer_settings and change_home_offset and little_utilities_enable"
        }
        self._settings_dict["change_home_y"] = {
            "label": "            Home Offset Y",
            "description": "Change the Y home offset.",
            "type": "str",
            "default_value": "",
            "enabled": "change_printer_settings and change_home_offset and little_utilities_enable"
        }
        self._settings_dict["change_home_z"] = {
            "label": "            Home Offset Z",
            "description": "Change the Z home offset.",
            "type": "str",
            "default_value": "",
            "enabled": "change_printer_settings and change_home_offset and little_utilities_enable"
        }
        self._settings_dict["change_steps"] = {
            "label": "        Change Steps/MM",
            "description": "Change the Steps/MM for the XYZE axes. Blank entries mean No Change.",
            "type": "bool",
            "default_value": False,
            "enabled": "change_printer_settings and little_utilities_enable"
        }
        self._settings_dict["change_steps_x"] = {
            "label": "            X Steps/MM",
            "description": "Change the X Steps.",
            "type": "str",
            "default_value": "200",
            "unit": "steps/mm  ",
            "enabled": "change_printer_settings and change_steps and little_utilities_enable"
        }
        self._settings_dict["change_steps_y"] = {
            "label": "            Y Steps/MM",
            "description": "Change the Y Steps.",
            "type": "float",
            "unit": "steps/mm  ",
            "enabled": "change_printer_settings and change_steps and little_utilities_enable"
        }
        self._settings_dict["change_steps_z"] = {
            "label": "            Z Steps/MM",
            "description": "Change the Z Steps.",
            "type": "float",
            "unit": "steps/mm  ",
            "enabled": "change_printer_settings and change_steps and little_utilities_enable"
        }
        self._settings_dict["change_steps_e"] = {
            "label": "            E Steps/MM",
            "description": "Change the E Steps.",
            "type": "float",
            "unit": "steps/mm  ",
            "enabled": "change_printer_settings and change_steps and little_utilities_enable"
        }
        self._settings_dict["change_save_changes"] = {
            "label": "        Save changes (M500)",
            "description": "Save the changes to the printer EEPROM or memory. If you don't save then any changes will expire when the printer is turned off.",
            "type": "bool",
            "default_value": False,
            "enabled": "little_utilities_enable and change_printer_settings and (change_home_offset or change_xYaccel or change_feedrate or change_steps)"
        }
        self._settings_dict["debugging_tools"] = {
            "label": "    Enable Debugging Tools",
            "description": "Debug specific scripts.",
            "type": "bool",
            "default_value": False,
            "enabled": "little_utilities_enable"
        }
        self._settings_dict["add_data_headers"] = {
            "label": "        Add Data[?] headers",
            "description": "A debugging tool.  Adds comment lines '>>>End of Data[xxx]<<<' to the end of each item in the Data List.",
            "type": "bool",
            "default_value": False,
            "enabled": "debugging_tools and little_utilities_enable"
        }
        self._settings_dict["add_data_headers_at_start"] = {
            "label": "            At section start",
            "description": "When checked the lines will be added to the beginning of a data section.  When un-checked they will be at the end.",
            "type": "bool",
            "default_value": True,
            "enabled": "add_data_headers and debugging_tools and little_utilities_enable"
        }
        self._settings_dict["debug_file"] = {
            "label": "        Create a debugging file",
            "description": "Removes all M commands and extrusions from the layer range specified.  All other layers are deleted.",
            "type": "bool",
            "default_value": False,
            "enabled": "debugging_tools and little_utilities_enable"
        }
        self._settings_dict["debug_autohome_cmd"] = {
            "label": "            Your Auto-Home cmd",
            "description": "Usually G28 but can be different.  Add parameters if required.",
            "type": "str",
            "default_value": "G28",
            "enabled": "debug_file and debugging_tools and little_utilities_enable"
        }
        self._settings_dict["debug_start_layer"] = {
            "label": "            Start Layer Debug File",
            "description": "Use the Cura preview layer numbers.  This is the first layer to remove the extrusions from.  Earlier Layers will be deleted",
            "type": "int",
            "default_value": 12,
            "minimum_value": 1,
            "enabled": "debug_file and debugging_tools and little_utilities_enable"
        }
        self._settings_dict["debug_end_layer"] = {
            "label": "        End Layer Debug File",
            "description": "Use -1 to indicate the top layer.  Use the Cura preview numbers to indicate a layer below the top.  This is the last layer that will have the extrusions removed.  All layers above this one will be deleted.",
            "type": "int",
            "default_value": -1,
            "enabled": "debug_file and debugging_tools and little_utilities_enable"
        }
        self._settings_dict["data_num_and_line_nums"] = {
            "label": "        Add data[item#] and line[line#]",
            "description": "Adds a numbering comment to each line in the file as ' ;Data: num, Line: num'",
            "type": "bool",
            "default_value": False,
            "enabled": "debugging_tools and little_utilities_enable"
        }
        self._settings_dict["line_numbers"] = {
            "label": "    Add line numbers to the gcode",
            "description": "Numbers the lines.  Some firmware requires line numbers.",
            "type": "bool",
            "default_value": False,
            "enabled": "debugging_tools and little_utilities_enable"
        }
        self._settings_dict["add_line_nr_sentence_number_prefix"] = {
            "label": "        Line number prefix",
            "description": "This will appear before the line number in the g-code",
            "type": "str",
            "default_value": "",
            "enabled": "line_numbers and debugging_tools and little_utilities_enable"
        }
        self._settings_dict["add_line_nr_starting_number"] = {
            "label": "        Starting Number",
            "description": "The number used for the first line.",
            "type": "int",
            "default_value": "1",
            "enabled": "line_numbers and debugging_tools and little_utilities_enable"
        }
        self._settings_dict["add_line_nr_skip_comments"] = {
            "label": "        Skip Comments",
            "description": "When 'True' any line that starts with a semi-colon will be ignored during the numbering.",
            "type": "bool",
            "default_value": False,
            "enabled": "line_numbers and debugging_tools and little_utilities_enable"
        }
        self._settings_dict["disable_abl"] = {
            "label": "    Disable ABL for Small Models",
            "description": "When a model takes up less space, or is shorter time than entered below, any G29 and M420 lines in the startup will be disabled.",
            "type": "bool",
            "default_value": False,
            "enabled": "little_utilities_enable"
        }
        self._settings_dict["disable_abl_footprint"] = {
            "label": "        By footprint",
            "description": "When a model takes up less space than entered below, any G29 and M420 lines in the startup will be disabled.",
            "type": "bool",
            "default_value": False,
            "enabled": "disable_abl and little_utilities_enable"
        }
        self._settings_dict["disable_abl_min_footprint"] = {
            "label": "            Min. Footprint for ABL",
            "description": "FOR SINGLE MODELS ONLY - this disables the StartUp ABL commands for small prints.  Enter the minimum size of the print in square mm's (any skirt/brim/raft will be ignored).  Models that take up less space than this will NOT USE the ABL.  (If there is more than a single print on the build plate Cura adds the areas together so this would include all models.)",
            "type": "int",
            "default_value": 900,
            "minimum_value": 4,
            "unit": "mm²    ",
            "enabled": "disable_abl and disable_abl_footprint and little_utilities_enable"
        }
        self._settings_dict["disable_abl_time"] = {
            "label": "        By print time",
            "description": "When a model takes less time to print than entered below, any G29 and M420 lines in the startup will be disabled.",
            "type": "bool",
            "default_value": False,
            "enabled": "disable_abl and little_utilities_enable"
        }
        self._settings_dict["disable_abl_min_time"] = {
            "label": "            Min. time for ABL",
            "description": "This disables the StartUp ABL commands for short duration prints.  Enter the minimum time for ABL in minutes.  Models that take less time than this will NOT USE the ABL.",
            "type": "int",
            "default_value": 20,
            "minimum_value": 4,
            "unit": "minutes    ",
            "enabled": "disable_abl and disable_abl_time and little_utilities_enable"
        }
        self._settings_dict["final_z"] = {
            "label": "    One-at-a-Time Final Z",
            "description": "Adds a Z-lift move to the 'Transit' height right after the last model finishes printing.  Prevents the nozzle crashing into taller prints.",
            "type": "bool",
            "default_value": False,
            "enabled": "little_utilities_enable"
        }
        self._settings_dict["adjust_temps"] = {
            "label": "    Adjust per model temperature",
            "description": "Adjust the temperatures for each model in a 'One-at-a-Time' project.",
            "type": "bool",
            "default_value": False,
            "enabled": "little_utilities_enable"
        }
        self._settings_dict["temperature_list"] = {
            "label": "        Temperature List",
            "description": "Enter the temperatures to assign to each model in the order you want them assigned (delimit with a comma - spaces are not allowed).  There should be one temperature assigned for each model on the build plate.  If there are less Temperatures than Number-of-Models the additional models will be set to 'Print Temperature'.  If you have the 'Initial Print Temperature' set differently than the 'Print Temperature' then the temperature changes will be made at LAYER:1 and all Initial Print Temperatures will be respected.",
            "type": "str",
            "unit": "°C  ",
            "default_value": "210,215,220",
            "enabled": "adjust_temps and little_utilities_enable"
        }
        self._settings_dict["speed_limit_enable"] = {
            "label": "    Enable Speed Enforcement",
            "description": "Whether to enforce the speeds in Cura if they have been effected by 'Flow Compensation'.",
            "type": "bool",
            "default_value": False,
            "enabled": "little_utilities_enable"
        }
        self._settings_dict["speeds_to_check"] = {
            "label": "    Enforce Speed Limits",
            "description": "Print speeds, travel speeds, or both.  The speeds are checked per feature and per extruder.",
            "type": "enum",
            "options": {
                "print_speeds": "Print Speeds",
                "travel_speeds": "Travel Speeds",
                "all_speeds": "Both"},
            "default_value": "all_speeds",
            "enabled": "speed_limit_enable and little_utilities_enable"
        }
        self._settings_dict["speeds_to_check"] = {
            "label": "        Enforce Speed Limits",
            "description": "Print speeds, travel speeds, or both.  The speeds are checked per feature and per extruder.",
            "type": "enum",
            "options": {
                "print_speeds": "Print Speeds",
                "travel_speeds": "Travel Speeds",
                "all_speeds": "Both"},
            "default_value": "all_speeds",
            "enabled": "speed_limit_enable and little_utilities_enable"
        }

        ContainerRegistry.getInstance().containerLoadComplete.connect(self._onContainerLoadComplete)

        self._application.getOutputDeviceManager().writeStarted.connect(self._distribute_scripts)


    def _onContainerLoadComplete(self, container_id):
        if not ContainerRegistry.getInstance().isLoaded(container_id):
            # skip containers that could not be loaded, or subsequent findContainers() will cause an infinite loop
            return

        try:
            container = ContainerRegistry.getInstance().findContainers(id = container_id)[0]

        except IndexError:
            # the container no longer exists
            return

        if not isinstance(container, DefinitionContainer):
            # skip containers that are not definitions
            return

        LittleUtilities_category = container.findDefinitions(key="experimental")

        little_utilities_enable = container.findDefinitions(key=list(self._settings_dict.keys())[0])
        remove_comments = container.findDefinitions(key=list(self._settings_dict.keys())[1])
        remove_comments_inc_opening = container.findDefinitions(key=list(self._settings_dict.keys())[2])
        remove_comments_inc_startup = container.findDefinitions(key=list(self._settings_dict.keys())[3])
        remove_comments_leave_layer_lines = container.findDefinitions(key=list(self._settings_dict.keys())[4])
        remove_comments_inc_ending = container.findDefinitions(key=list(self._settings_dict.keys())[5])
        add_extruder_end = container.findDefinitions(key=list(self._settings_dict.keys())[6])
        lift_head_park = container.findDefinitions(key=list(self._settings_dict.keys())[7])

        very_cool_enable = container.findDefinitions(key=list(self._settings_dict.keys())[8])
        very_cool_layer = container.findDefinitions(key=list(self._settings_dict.keys())[9])
        very_cool_feed = container.findDefinitions(key=list(self._settings_dict.keys())[10])
        very_cool_fan = container.findDefinitions(key=list(self._settings_dict.keys())[11])
        very_cool_index_dist = container.findDefinitions(key=list(self._settings_dict.keys())[12])
        very_cool_y_index = container.findDefinitions(key=list(self._settings_dict.keys())[13])

        change_printer_settings = container.findDefinitions(key=list(self._settings_dict.keys())[14])
        change_feedrate = container.findDefinitions(key=list(self._settings_dict.keys())[15])
        change_feedrate_x = container.findDefinitions(key=list(self._settings_dict.keys())[16])
        change_feedrate_y = container.findDefinitions(key=list(self._settings_dict.keys())[17])
        change_feedrate_z = container.findDefinitions(key=list(self._settings_dict.keys())[18])
        change_feedrate_e = container.findDefinitions(key=list(self._settings_dict.keys())[19])
        change_xy_accel = container.findDefinitions(key=list(self._settings_dict.keys())[20])
        change_accel_x = container.findDefinitions(key=list(self._settings_dict.keys())[21])
        change_accel_y = container.findDefinitions(key=list(self._settings_dict.keys())[22])
        change_home_offset = container.findDefinitions(key=list(self._settings_dict.keys())[23])
        change_home_x = container.findDefinitions(key=list(self._settings_dict.keys())[24])
        change_home_y = container.findDefinitions(key=list(self._settings_dict.keys())[25])
        change_home_z = container.findDefinitions(key=list(self._settings_dict.keys())[26])
        change_steps = container.findDefinitions(key=list(self._settings_dict.keys())[27])
        change_steps_x = container.findDefinitions(key=list(self._settings_dict.keys())[28])
        change_steps_y = container.findDefinitions(key=list(self._settings_dict.keys())[29])
        change_steps_z = container.findDefinitions(key=list(self._settings_dict.keys())[30])
        change_steps_e = container.findDefinitions(key=list(self._settings_dict.keys())[31])
        change_save_changes = container.findDefinitions(key=list(self._settings_dict.keys())[32])

        debugging_tools = container.findDefinitions(key=list(self._settings_dict.keys())[33])
        add_data_headers = container.findDefinitions(key=list(self._settings_dict.keys())[34])
        add_data_headers_at_start = container.findDefinitions(key=list(self._settings_dict.keys())[35])

        debug_file = container.findDefinitions(key=list(self._settings_dict.keys())[36])
        debug_autohome_cmd = container.findDefinitions(key=list(self._settings_dict.keys())[37])
        debug_start_layer = container.findDefinitions(key=list(self._settings_dict.keys())[38])
        debug_end_layer = container.findDefinitions(key=list(self._settings_dict.keys())[39])

        data_num_and_line_nums = container.findDefinitions(key=list(self._settings_dict.keys())[40])

        line_numbers = container.findDefinitions(key=list(self._settings_dict.keys())[41])
        add_line_nr_sentence_number_prefix = container.findDefinitions(key=list(self._settings_dict.keys())[42])
        add_line_nr_starting_number = container.findDefinitions(key=list(self._settings_dict.keys())[43])
        add_line_nr_skip_comments = container.findDefinitions(key=list(self._settings_dict.keys())[44])

        disable_abl = container.findDefinitions(key=list(self._settings_dict.keys())[45])
        disable_abl_footprint = container.findDefinitions(key=list(self._settings_dict.keys())[46])
        disable_abl_min_footprint = container.findDefinitions(key=list(self._settings_dict.keys())[47])
        disable_abl_time = container.findDefinitions(key=list(self._settings_dict.keys())[48])
        disable_abl_min_time = container.findDefinitions(key=list(self._settings_dict.keys())[49])

        final_z = container.findDefinitions(key=list(self._settings_dict.keys())[50])

        adjust_temps = container.findDefinitions(key=list(self._settings_dict.keys())[51])
        temperature_list = container.findDefinitions(key=list(self._settings_dict.keys())[52])

        speed_limit_enable = container.findDefinitions(key=list(self._settings_dict.keys())[53])
        speeds_to_check = container.findDefinitions(key=list(self._settings_dict.keys())[54])

        if LittleUtilities_category:
            LittleUtilities_category = LittleUtilities_category[0]
            for setting_key, setting_dict in self._settings_dict.items():
                definition = SettingDefinition(setting_key, container, LittleUtilities_category, self._i18n_catalog)
                definition.deserialize(setting_dict)
                # add the setting to the already existing platform adhesion setting definition
                LittleUtilities_category._children.append(definition)
                container._definition_cache[setting_key] = definition
                container._updateRelations(definition)


            extruder = Application.getInstance().getGlobalContainerStack().extruderList
            mycura = Application.getInstance().getGlobalContainerStack()
            max_feedrate_x = str(mycura.getProperty("machine_max_feedrate_x", "value"))
            max_feedrate_y = str(mycura.getProperty("machine_max_feedrate_y", "value"))
            max_feedrate_z = str(mycura.getProperty("machine_max_feedrate_z", "value"))
            max_feedrate_e = str(mycura.getProperty("machine_max_feedrate_e", "value"))
            extruder[0].setProperty("change_feedrate_x", "value", str(max_feedrate_x))
            extruder[0].setProperty("change_feedrate_y", "value", str(max_feedrate_y))
            extruder[0].setProperty("change_feedrate_z", "value", str(max_feedrate_z))
            extruder[0].setProperty("change_feedrate_e", "value", str(max_feedrate_e))
                
            steps_per_mm_x = extruder[0].getProperty("machine_steps_per_mm_x", "value")
            steps_per_mm_y = extruder[0].getProperty("machine_steps_per_mm_y", "value")
            steps_per_mm_z = extruder[0].getProperty("machine_steps_per_mm_z", "value")
            steps_per_mm_e = extruder[0].getProperty("machine_steps_per_mm_e", "value")
            extruder[0].setProperty("change_steps_x", "value", str(steps_per_mm_x))
            extruder[0].setProperty("change_steps_y", "value", str(steps_per_mm_y))
            extruder[0].setProperty("change_steps_z", "value", str(steps_per_mm_z))
            extruder[0].setProperty("change_steps_e", "value", str(steps_per_mm_e))

    def _distribute_scripts(self, output_device):
        scene = self._application.getController().getScene()
        global_container_stack = self._application.getGlobalContainerStack()
        if not global_container_stack:
            return
        extruder = global_container_stack.extruderList
        # Check the extruder count to see if more than one is enabled and if that one is T0.
        little_utilities_enable = extruder[0].getProperty("little_utilities_enable", "value")
        # get settings from Cura
        remove_comments = extruder[0].getProperty("remove_comments", "value")
        remove_comments_inc_opening = extruder[0].getProperty("remove_comments_inc_opening", "value")
        remove_comments_inc_startup = extruder[0].getProperty("remove_comments_inc_startup", "value")
        remove_comments_leave_layer_lines = extruder[0].getProperty("remove_comments_leave_layer_lines", "value")
        remove_comments_inc_ending = extruder[0].getProperty("remove_comments_inc_ending", "value")
        add_extruder_end = extruder[0].getProperty("add_extruder_end", "value")

        debugging_tools = extruder[0].getProperty("debugging_tools", "value")
        add_data_headers = extruder[0].getProperty("add_data_headers", "value")
        lift_head_park = extruder[0].getProperty("lift_head_park", "value")

        very_cool_enable = extruder[0].getProperty("very_cool_enable", "value")

        interface_temp = extruder[0].getProperty("interface_temp", "value")
        interface_flow = extruder[0].getProperty("interface_flow", "value")
        unload_dist = extruder[0].getProperty("unload_dist", "value")
        load_dist = extruder[0].getProperty("load_dist", "value")
        enable_purge = extruder[0].getProperty("enable_purge", "value")
        purge_amt_model = extruder[0].getProperty("purge_amt_model", "value")
        purge_amt_interface = extruder[0].getProperty("purge_amt_interface", "value")
        park_head = extruder[0].getProperty("park_head", "value")
        park_x = extruder[0].getProperty("park_x", "value")
        park_y = extruder[0].getProperty("park_y", "value")
        m300_add = extruder[0].getProperty("m300_add", "value")
        m118_add = extruder[0].getProperty("m118_add", "value")

        global_container_stack = self._application.getGlobalContainerStack()
        extruder = global_container_stack.extruderList

        if not little_utilities_enable:
            return

        gcode_dict = getattr(scene, "gcode_dict", {})
        if not gcode_dict: # this also checks for an empty dict
            Logger.log("w", "Scene has no gcode to process")
            return

        dict_changed = False

        for plate_id in gcode_dict:
            data = gcode_dict[plate_id]
            if len(data) < 2:
                Logger.log("w", "G-Code %s does not contain any layers", plate_id)
                continue

            if ";  [Little Utilities] plugin is enabled\n" not in data[0] and little_utilities_enable:
                if add_extruder_end:
                    self._add_extruder_end(data, extruder)
                if lift_head_park:
                    self._lift_head_park(data, extruder)
                if very_cool_enable:
                    self._very_cool(data, extruder)
                if remove_comments:
                    self._remove_comments(data, extruder)
                if  debugging_tools and add_data_headers:
                    self._add_data_header(data, extruder)
                data[0] += ";  [Little Utilities] plugin is enabled\n"
                gcode_dict[plate_id] = data
                dict_changed = True
            else:
                Logger.log("d", "G-Code %s has already been processed", plate_id)
                continue
        if dict_changed:
            setattr(scene, "gcode_dict", gcode_dict)

    # Add Extruder Ending Gcode-------------------------------------------
    def _add_extruder_end(self, data:str, extruder: int)->str:
        t_nr = 0
        try:
            for num in range(1,len(data)-2):
                lines = data[num].split("\n")
                for line in lines:
                    if re.match("T(\d*)",line):
                        t_nr = self.getValue(line, "T")
            extruder_end_gcode = Application.getInstance().getGlobalContainerStack().extruderList[t_nr].getProperty("machine_extruder_end_code","value")
        except:
            extruder_end_gcode = Application.getInstance().getGlobalContainerStack().extruderList[0].getProperty("machine_extruder_end_code","value")
        if extruder_end_gcode != "":
            data[len(data)-2] += extruder_end_gcode + "\n"
        return

    # Add Data Headers-------------------------------------------
    def _add_data_header(self, data: str, extruder: int)->str:
        global_container_stack = self._application.getGlobalContainerStack()
        extruder = global_container_stack.extruderList
        in_front = bool(extruder[0].getProperty("add_data_headers_at_start", "value"))
        tot_lines = 2
        comments = 0
        for num in range(0,len(data)):
            tot_lines += data[num].count("\n")
            comments += data[num].count(";")
        tot_lines -= comments
        # Add a couple of statistics to the beginning of the file
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

    def _remove_comments(self, data:str, extruder: int)->str:
        me_opening = bool(extruder[0].getProperty("remove_comments_inc_opening", "value"))
        me_startup = bool(extruder[0].getProperty("remove_comments_inc_startup", "value"))
        me_ending = bool(extruder[0].getProperty("remove_comments_inc_ending", "value"))
        me_layerlines = bool(extruder[0].getProperty("remove_comments_leave_layer_lines", "value"))

        # Start with the opening data paragraph if enabled
        if me_opening:
            layer = data[0]
            lines = layer.split("\n")
            modified_data = ""
            for line in lines:
                if line == "":
                    continue
                if line.startswith(";"):
                    line = ""
                    continue
                if ";" in line:
                    line = line.split(";")[0]
                modified_data += line + "\n"
            data[0] = modified_data#[0:-1]

        # the StartUp Gcode section if enabled
        if me_startup:
            layer = data[1]
            lines = layer.split("\n")
            modified_data = ""
            for line in lines:
                if line == "":
                    continue
                if line.startswith(";"):
                    line = ""
                    continue
                if ";" in line:
                    line = line.split(";")[0]
                modified_data += line + "\n"
            data[1] = modified_data#[0:-1]
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
                if line == "":
                    continue
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
            data[num] = modified_data#[0:-1]
        return

    # Lift Head Parking--------------------------------------------------------
    def _lift_head_park(self, data:str, extruder: int)->str:
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

    # Very_cool cooling--------------------------------------------------------
    def _very_cool(self, data:str, extruder:int)->str:

        all_layers = extruder[0].getProperty("very_cool_layer", "value")
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
        very_cool_y_index = bool(extruder[0].getProperty("very_cool_y_index", "value"))
        very_cool_index_dist = int(extruder[0].getProperty("very_cool_index_dist", "value"))
        travel_speed = str(int(extruder[0].getProperty("speed_travel", "value"))*60)
        zhop_speed = str(int(extruder[0].getProperty("speed_z_hop", "value"))*60)
        retr_enabled = bool(extruder[0].getProperty("retraction_enable", "value"))
        retr_dist = str(extruder[0].getProperty("retraction_amount", "value"))
        retr_speed = str(extruder[0].getProperty("retraction_speed", "value")*60)
        bed_width = int(Application.getInstance().getGlobalContainerStack().getProperty("machine_width", "value"))
        bed_depth = int(Application.getInstance().getGlobalContainerStack().getProperty("machine_depth", "value"))
        fan_percent = extruder[0].getProperty("very_cool_fan", "value") /100
        fan_speed = 0
        # Check if the fan scale is RepRap 0-1
        fan_scale = bool(extruder[0].getProperty("machine_scale_fan_speed_zero_to_one", "value"))
        if not fan_scale:
            very_cool_fan_speed = round(255 * fan_percent)
        else:
            very_cool_fan_speed = round(fan_percent,1)

        # Get the travel speed percentage
        travel_rate = int(extruder[0].getProperty("very_cool_feed", "value")) * 60
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
                    lines.append(f"M106 S{very_cool_fan_speed} ; Fan Speed - Very Cool Fanpath")
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
                    lines.append(f"M106 S{fan_speed} ; Previous Fan Speed")
                    lines.append(f"G0 F{travel_speed} X{ret_x} Y{ret_y}")
                    lines.append(f"G0 F{zhop_speed} Z{ret_z}")
                    if not retracted and retr_enabled:
                        lines.append(f"G1 F{retr_speed} E{ret_e}")
                    lines.append(f"G0 F{travel_speed} ;CUSTOM END")
                    fan_layer = "\n".join(lines)
                    time_line = re.search(";TIME_ELAPSED:(\d.*)", data[num])
                    data[num] = re.sub(";TIME_ELAPSED:(\d.*)", fan_layer  + "\n" + time_line[0], data[num])
        return

    def _change_printer_settings(self, data:str, extruder:int)->str:
        change_feed_string = ";  Change Printer Settings\n"
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
                mycura = Application.getInstance().getGlobalContainerStack()
                extruder = mycura.extruderList
                if x_steps != "":
                    mycura.setProperty("machine_steps_per_mm_x", "value", x_steps)
                    extruder[0].setProperty("machine_steps_per_mm_x", "value", x_steps)
                if y_steps != "":
                    mycura.setProperty("machine_steps_per_mm_y", "value", y_steps)
                    extruder[0].setProperty("machine_steps_per_mm_y", "value", y_steps)
                if z_steps != "":
                    mycura.setProperty("machine_steps_per_mm_z", "value", z_steps)
                    extruder[0].setProperty("machine_steps_per_mm_z", "value", z_steps)
                if e_steps != "":
                    mycura.setProperty("machine_steps_per_mm_e", "value", e_steps)
                    extruder[0].setProperty("machine_steps_per_mm_e", "value", e_steps)

        # Add the changes to the gcode at the end of the StartUp Gcode
        data[1] += change_feed_string + change_accel_string + change_home_string + change_steps_string + save_string + ";  End of Changes\n"
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

    def getValue(self, line: str, param: str)->str:
        try:
            the_num = line.split(param)[1]
            if " " in the_num:
                the_num = the_num.split(" ")[0]
            return float(the_num)
        except:
            return None