#------------------------------------------------------------------------------------------------------------------------------------
# Initial Copyright(c) 2024 Greg Foresi (GregValiant)
#
# Sovol SV04 IDEX Converter is released under the terms of the AGPLv3 or higher.
#
# Description:  Postprocessing script to convert adapt Cura Gcode to the Sovol SV03 IDEX machines.  The SV04 "Copy", "Dual", "Mirror", Single01", and "Single02" printers must be installed.
#    The settings will be available under "Dual Extrusion".
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

class SovolSV04_IDEX_Plugin(Extension):
    def __init__(self):
        super().__init__()

        self._application = Application.getInstance()

        self._i18n_catalog = None

        self._settings_dict = OrderedDict()
        self._settings_dict["sovolidexconverter_enable"] = {
            "label": "Enable Sovol IDEX",
            "description": "Check to enable the script",
            "type": "bool",
            "default_value": True,
            "enabled": True
        }
        self._settings_dict["print_mode"] = {
            "label": "    Select the print mode",
            "description": "'Auto Select' the plugin will select the mode based on the name of the printer.  NOTE:  'SV04' must be in the printer name and the 'mode' must be in the printer name ('Copy', 'Dual', 'Mirror', 'Single01', 'Single02').",
            "type": "enum",
            "options":
            {
                "mode_auto": "Auto Select",
                "mode_copy": "Copy",
                "mode_dual": "Dual",
                "mode_mirror": "Mirror",
                "mode_tool_01": "Single01",
                "mode_tool_02": "Single02"},
            "default_value": "mode_auto",
            "enabled": "sovolidexconverter_enable"
        }
        self._settings_dict["enable_t0_start"] = {
            "label": "    Enable T0 StartUp macro",
            "description": "Enable a Custom Gcode to run the first time that T0 is called.",
            "type": "bool",
            "default_value": False,
            "enabled": "sovolidexconverter_enable and print_mode == 'mode_dual'"
        }
        self._settings_dict["t0_initial_gcode"] = {
            "label": "    T0 'First Use' Commands",
            "description": "Enter gcode commands delimited by commas.",
            "type": "str",
            "default_value": "",
            "enabled": "sovolidexconverter_enable and enable_t0_start and print_mode == 'mode_dual'"
        }
        self._settings_dict["enable_t0_end"] = {
            "label": "    Enable T0 Ending macro",
            "description": "Enable a Custom Gcode to run the last time that T0 is called.",
            "type": "bool",
            "default_value": False,
            "enabled": "sovolidexconverter_enable and print_mode == 'mode_dual'"        
        }
        self._settings_dict["t0_end_gcode"] = {
            "label": "    T0 Last Use Commands",
            "description": "Enter gcode commands delimited by commas.",
            "type": "str",
            "default_value": "",
            "enabled": "sovolidexconverter_enable and enable_t0_end and print_mode == 'mode_dual'"
        }
        self._settings_dict["enable_t1_start"] = {
            "label": "    Enable T1 StartUp macro",
            "description": "Enable a Custom Gcode to run the first time that T1 is called.",
            "type": "bool",
            "default_value": False,
            "enabled": "sovolidexconverter_enable and print_mode == 'mode_dual'"
        }
        self._settings_dict["t1_initial_gcode"] = {
            "label": "    T1 First Use Commands",
            "description": "Enter gcode commands delimited by commas.  NO SPACES.",
            "type": "str",
            "default_value": "",
            "enabled": "sovolidexconverter_enable and enable_t1_start and print_mode == 'mode_dual'"
        }
        self._settings_dict["enable_t1_end"] = {
            "label": "    Enable T1 Ending macro",
            "description": "Enable a Custom Gcode to run the last time that T0 is called.",
            "type": "bool",
            "default_value": False,
            "enabled": "sovolidexconverter_enable and print_mode == 'mode_dual'"
        }
        self._settings_dict["t1_end_gcode"] = {
            "label": "    T1 Last Use Commands",
            "description": "Enter gcode commands delimited by commas.  NO SPACES.",
            "type": "str",
            "default_value": "",
            "enabled": "sovolidexconverter_enable and enable_t1_start and print_mode == 'mode_dual'"
        }

        ContainerRegistry.getInstance().containerLoadComplete.connect(self._onContainerLoadComplete)

        self._application.getOutputDeviceManager().writeStarted.connect(self._ParseGcode)


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

        dual_modes_category = container.findDefinitions(key="dual")

        sovolidexconverter_enable = container.findDefinitions(key=list(self._settings_dict.keys())[0])
        print_mode = container.findDefinitions(key=list(self._settings_dict.keys())[1])
        enable_t0_start = container.findDefinitions(key=list(self._settings_dict.keys())[2])
        t0_initial_gcode = container.findDefinitions(key=list(self._settings_dict.keys())[3])
        enable_t0_end = container.findDefinitions(key=list(self._settings_dict.keys())[4])
        t0_end_gcode = container.findDefinitions(key=list(self._settings_dict.keys())[5])
        enable_t1_start = container.findDefinitions(key=list(self._settings_dict.keys())[6])
        t1_initial_gcode = container.findDefinitions(key=list(self._settings_dict.keys())[7])
        enable_t1_end = container.findDefinitions(key=list(self._settings_dict.keys())[8])
        t1_end_gcode = container.findDefinitions(key=list(self._settings_dict.keys())[9])

        insert_at = 0
        if dual_modes_category:
            dual_modes_category = dual_modes_category[0]
            for setting_key, setting_dict in self._settings_dict.items():

                definition = SettingDefinition(setting_key, container, dual_modes_category, self._i18n_catalog)
                definition.deserialize(setting_dict)

                # add the setting to the top of the 'Dual' extrusion settings.
                dual_modes_category._children.insert(insert_at, definition)
                container._definition_cache[setting_key] = definition
                container._updateRelations(definition)
                insert_at += 1

    def _ParseGcode(self, output_device):
        scene = self._application.getController().getScene()

        global_container_stack = self._application.getGlobalContainerStack()
        if not global_container_stack:
            return
        extruder = global_container_stack.extruderList     

        # Exit if the script isn't enabled   
        sovolidexconverter_enable = extruder[0].getProperty("sovolidexconverter_enable", "value")
        if not sovolidexconverter_enable:
            Logger.log("i", "[Sovol SV04 IDEX Converter] Was not enabled.")
            return
        
        # get settings from Cura
        print_mode = extruder[0].getProperty("print_mode", "value")
        gcode_dict = getattr(scene, "gcode_dict", {})
        if not gcode_dict: # this also checks for an empty dict
            Logger.log("w", "Scene has no gcode to process")
            return

        mycura = Application.getInstance().getGlobalContainerStack()
        extruder = mycura.extruderList
        machine_name = mycura.getProperty("machine_name", "default_value")
        dict_changed = False
        for plate_id in gcode_dict:
            gcode_list = gcode_dict[plate_id]
            if len(gcode_list) < 2:
                Logger.log("w", "G-Code %s does not contain any layers", plate_id)
                continue
                
            # Skip to the end if the Gcode is being saved a second time with no changes to the settings.
            if ";  [Sovol SV04 IDEX Converter] plugin is enabled" not in gcode_list[0]:
                match print_mode:
                    case "mode_copy":
                        mode_str = "SV04 Copy Mode"
                        sv04_cmd = "M605 S2; Copy Mode"
                    case "mode_dual":
                        mode_str = "SV04 Dual Mode"
                        sv04_cmd = "M605 S0 ;Set printer to Dual Mode"
                    case "mode_mirror":
                        mode_str = "SV04 Mirror Mode"
                        sv04_cmd = "M605 S3 ;Set printer to Mirror Mode"
                    case "mode_tool_01":
                        mode_str = "SV04 Single Mode 01"
                        sv04_cmd = "M605 S0 ;Set printer to Single Mode 01"
                    case "mode_tool_02":
                        mode_str = "SV04 Single Mode 02"
                        sv04_cmd = "M605 S0 ;Set printer to Single Mode 02"
                        
                # If in 'Auto Select' mode the printer name determines the mode.
                if not "SV04" in machine_name and print_mode == "mode_auto":
                    Logger.log("i", "The printer name does not contain 'SV04'.  Auto-Mode cannot be used with this printer.")
                    Message(title = "[SovolSV04 IDEX Plugin]", text = "The active printer does not have 'SV04' in its name which 'Auto Mode' requires.  The SovolSV04_IDEX plugin must exit.").show()
                    return
                if print_mode == "mode_auto":
                    if "Copy" in machine_name:
                        print_mode = "mode_copy"                    
                        mode_str = "SV04 Copy Mode"
                        sv04_cmd = "M605 S2 ;Set printer to Copy Mode"
                    elif "Dual" in machine_name:
                        print_mode = "mode_dual"
                        mode_str = "SV04 Dual Mode"
                        sv04_cmd = "M605 S0 ;Set printer to Dual Mode"
                    elif "Mirror" in machine_name:
                        print_mode = "mode_mirror"
                        mode_str = "SV04 Mirror Mode"
                        sv04_cmd = "M605 S3 ;Set printer to Mirror Mode"
                    elif "Single01" in machine_name:
                        print_mode = "mode_tool_01"
                        mode_str = "SV04 Single Mode 01"
                        sv04_cmd = "M605 S0 ;Set printer to Single Mode 01"
                    elif "Single02" in machine_name:
                        print_mode = "mode_tool_02"
                        mode_str = "SV04 Single Mode 02"
                        sv04_cmd = "M605 S0 ;Set printer to Single Mode 02"
                    
                # Add the printer name so it is in the second line of the gcode ala Sovol Cura
                lines = gcode_list[0].split("\n")
                lines.insert(1, ";TARGET_MACHINE.NAME:" + mode_str)
                gcode_list[0] = "\n".join(lines)

                # Add the print mode before the StartUp Gcode
                opening = gcode_list[1].split("\n")
                opening.insert(1, sv04_cmd)
                gcode_list[1] = "\n".join(opening)

                # Add the correct tool number if in either Single Mode
                if mode_str in ["SV04 Single Mode 01", "SV04 Single Mode 02"]:
                    lines = gcode_list[1].split("\n")
                    for index, line in enumerate(lines):
                        if line.startswith("M82"):
                            lines[index] += "\n;" + mode_str
                            if mode_str in ["SV04 Single Mode 01", "SV04 Single Mode 02"]:
                                tool_num = str(int(mode_str[-1]) - 1)
                                lines[index] = "T" + tool_num + "\n" + line
                            break
                    gcode_list[1] = "\n".join(lines)

                # If in Dual mode then get any Start and End gcode macros for each tool
                if print_mode == "mode_dual":
                    start_gcode = gcode_list[1].split("\n")
                    initial_extruder_nr = 0
                    for index, line in enumerate(start_gcode):
                        if line.startswith("T1"):
                            initial_extruder_nr = 1
                            break
                        elif line.startswith("T0"):
                            initial_extruder_nr = 0
                            break
                    if initial_extruder_nr == 0:
                        alt_extruder_nr = 1
                    else:
                        alt_extruder_nr = 0
                        
                    # Check if the alternate extruder is used in the print
                    alt_extruder_used = False
                    for num in range(1, len(gcode_list) - 1):
                        if f"\nT{alt_extruder_nr}\n" in gcode_list[num]:
                            alt_extruder_used = True
                            break
                            
                    # Check if an extruder is disabled
                    enabled_list = list([mycura.isEnabled for mycura in mycura.extruderList])
                    if enabled_list[initial_extruder_nr]:
                        init_temp = round(extruder[initial_extruder_nr].getProperty("material_print_temperature_layer_0", "value"))
                        heat_first_line = f"M109 T{initial_extruder_nr} S{init_temp}                   ; Extruder #{initial_extruder_nr + 1} to Start-Out Temp"
                    else:
                        heat_first_line = f"M104 T{initial_extruder_nr} S0                     ; Extruder #{initial_extruder_nr + 1} is disabled or not used"
                    
                    # Set the temperature for the Initial Extruder
                    if enabled_list[alt_extruder_nr] and alt_extruder_used:
                        off_temp = round(extruder[alt_extruder_nr].getProperty("material_standby_temperature", "value"))
                        heat_second_line = f"M104 T{alt_extruder_nr} S{off_temp}                   ; Extruder #{alt_extruder_nr + 1} to Start-Out Temp"
                    else:
                        heat_second_line = f"M104 T{alt_extruder_nr} S0                     ; Extruder #{alt_extruder_nr + 1} is disabled or not used"
                    for index, line in enumerate(start_gcode):
                        if line.startswith("G92 E"):
                            start_gcode.insert(index, heat_first_line)
                            start_gcode.insert(index, heat_second_line)
                            break
                    gcode_list[1] = "\n".join(start_gcode)
                    
                    # Prepare the one-time startup and ending gcode macros
                    t0_initial_gcode = ""
                    t0_end_gcode = ""
                    t1_initial_gcode = ""
                    t1_end_gcode = ""
                    enable_t0_start = extruder[0].getProperty("enable_t0_start", "value")
                    if enable_t0_start:
                        t0_initial_gcode = extruder[0].getProperty("t0_initial_gcode", "value").upper()
                        t0_initial_gcode = "\n" + t0_initial_gcode.replace(",", "\n")
                    enable_t0_end = extruder[0].getProperty("enable_t0_end", "value")
                    if enable_t0_end:
                        t0_end_gcode = extruder[0].getProperty("t0_end_gcode", "value").upper()
                        t0_end_gcode = t0_end_gcode.replace(",", "\n") + "\n"
                    enable_t1_start = extruder[0].getProperty("enable_t1_start", "value")
                    if enable_t1_start:
                        t1_initial_gcode = extruder[0].getProperty("t1_initial_gcode", "value").upper()
                        t1_initial_gcode = "\n" + t1_initial_gcode.replace(",", "\n")
                    enable_t1_end = extruder[0].getProperty("enable_t1_end", "value")
                    if enable_t1_end:
                        t1_end_gcode = extruder[0].getProperty("t1_end_gcode", "value").upper()
                        t1_end_gcode = t1_end_gcode.replace(",", "\n") + "\n"
                    active_tool = "0"

                    # Track the tools to find the first use and last use
                    len_of_data = len(gcode_list)
                    first_t0_line = [len_of_data,0]
                    last_t0_line = [len_of_data,0]
                    first_t1_line = [len_of_data,0]
                    last_t1_line = [len_of_data,0]
                    t0_used = False
                    t1_used = False
                    for num in range(1, len(gcode_list) - 1):
                        lines = gcode_list[num].split("\n")
                        for index, line in enumerate(lines):
                            if line.startswith("T0"):
                                t0_used = True
                                last_t0_line = [num, index]
                                if first_t0_line == [len_of_data,0]:
                                    first_t0_line = [num, index]
                            if line.startswith("T1"):
                                t1_used = True
                                last_t1_line = [num, index]
                                if first_t1_line == [len_of_data,0]:
                                    first_t1_line = [num, index]

                    # Add any start or ending macro commands to the first and last use of the tool
                    if first_t0_line != [len_of_data ,0] and enable_t0_start:
                        lines = gcode_list[first_t0_line[0]].split("\n")
                        lines[first_t0_line[1]] += str(t0_initial_gcode)
                        gcode_list[first_t0_line[0]] = "\n".join(lines)
                    if first_t1_line != [len_of_data ,0] and enable_t1_start:
                        lines = gcode_list[first_t1_line[0]].split("\n")
                        lines[first_t1_line[1]] += str(t1_initial_gcode)
                        gcode_list[first_t1_line[0]] = "\n".join(lines)
                    
                    # If T0 is the last tool used add the macro code to the end of the last layer.
                    if last_t0_line[0] > last_t1_line[0]:                
                        if last_t0_line != [len_of_data ,0] and enable_t1_end:
                            lines = gcode_list[last_t0_line[0]].split("\n")
                            lines[last_t0_line[1]] = str(t1_end_gcode) + lines[last_t0_line[1]]
                            gcode_list[last_t0_line[0]] = "\n".join(lines)
                            for l_num in range(len(gcode_list) - 1, 0, -1):
                                if ";LAYER:" in gcode_list[l_num]:
                                    l_lines = gcode_list[l_num].split("\n")
                                    l_lines.insert(len(l_lines) - 2, t0_end_gcode[:-1])
                                    gcode_list[l_num] = "\n".join(l_lines)
                                    break
                    
                    # If T1 is the last tool used add the macro code to the end of the last layer.
                    elif last_t1_line[0] > last_t0_line[0]:
                        if last_t1_line != [len_of_data ,0] and enable_t0_end:
                            lines = gcode_list[last_t1_line[0]].split("\n")
                            lines[last_t1_line[1]] = str(t0_end_gcode) + lines[last_t1_line[1]]
                            gcode_list[last_t1_line[0]] = "\n".join(lines)
                            for l_num in range(len(gcode_ist) - 1, 0, -1):
                                if ";LAYER:" in gcode_list[l_num]:
                                    l_lines = gcode_list[l_num].split("\n")
                                    l_lines.insert(len(l_lines) - 2, t1_end_gcode[:-1])
                                    gcode_list[l_num] = "\n".join(l_lines)
                                    break
                    
                    # For prints that only use T0
                    if last_t1_line[0] == len(gcode_list) and t0_used:
                        for l_num in range(len(gcode_list) - 1, 0, -1):
                            if ";LAYER:" in gcode_list[l_num]:
                                l_lines = gcode_list[l_num].split("\n")
                                l_lines.insert(len(l_lines) - 2, t0_end_gcode[:-1])
                                gcode_list[l_num] = "\n".join(l_lines)
                                break
                    
                    # For prints that only use T1
                    if last_t0_line[0] == len(gcode_list) and t1_used:
                        for l_num in range(len(gcode_list) - 1, 0, -1):
                            if ";LAYER:" in gcode_list[l_num]:
                                l_lines = gcode_list[l_num].split("\n")
                                l_lines.insert(len(l_lines) - 2, t1_end_gcode[:-1])
                                gcode_list[l_num] = "\n".join(l_lines)
                                break
                    gcode_list[0] += ";  [Sovol SV04 IDEX Converter] plugin is enabled\n"
                    gcode_dict[plate_id] = gcode_list
                    dict_changed = True
                elif print_mode == "mode_copy" or print_mode == "mode_mirror":                    
                    start_gcode = gcode_list[1].split("\n")
                    start_temp = round(extruder[0].getProperty("material_print_temperature_layer_0", "value"))
                    heat_first_line = f"M109 S{start_temp}                   ; Both Extruders to Start-Out Temp"
                    for index, line in enumerate(start_gcode):
                        if line.startswith("G92 E"):
                            start_gcode.insert(index, heat_first_line)
                            break
                    gcode_list[1] = "\n".join(start_gcode)
                else:
                    Logger.log("d", "G-Code %s has already been processed", plate_id)
                    continue
        if dict_changed:
            setattr(scene, "gcode_dict", gcode_dict)
        return