# Copyright (c) 2023 GregValiant (Greg Foresi)
#    This script is for Flash Forge IDEX printers that use the 'M104 S T' syntax.
#    - The Cura M104 and M109 lines will convert from 'M104/9 T S' syntax to 'M104/9 S T' syntax.
#    - The Tool Number is tracked through the gcode and the active tool number is added to all M104 and M109 lines.
#    - Cura ':TYPE:" lines will be changed to ";structure:" lines.
#    - Selecting the Print Mode (Normal, Duplicate, Mirror) will add relevant commands.

from ..Script import Script
from UM.Application import Application
from UM.Message import Message
import re
import os

class FlashForge_IDEX_TempTools(Script):

    def initialize(self) -> None:
        super().initialize()
        msg_txt = "    NOTE: The model must be located at the exact mid-point of the build plate.\n  If it is a single extruder print then the un-used extruder must be disabled.  Mirror and Duplicate modes assume that both extruders are used.\nIn 'Normal' mode the model cannot exceed X300 Y250.  In 'Mirror' or 'Duplicate' mode the model may not exceed X133 Y250."
        Message(title = "[Flash Forge IDEX Model Placement]", text = msg_txt).show()

    def getSettingDataString(self):
        return """{
            "name": "Flash Forge IDEX Tool Temp Conversion",
            "key": "FlashForge_IDEX_TempTools",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "enable_add_tool_nums":
                {
                    "label": "Enable FF IDEX Tool Nums",
                    "description": "This script changes the M104/M109 lines from the CUra syntax 'M104 T# S210' to 'M104 S210 T#' syntax.  It will also add the number of the active tool to any M104/M109 line that doesn't have one.  Ex: 'M109 S210' will become 'M109 S210 T#'",
                    "type": "bool",
                    "default_value": true,
                    "enabled": true
                },
                "print_mode":
                {
                    "label": "Print Mode",
                    "description": "Normal, Duplicate, or Mirror",
                    "type": "enum",
                    "options": {
                        "mode_normal": "Normal",
                        "mode_duplicate": "Duplicate",
                        "mode_mirror": "Mirror"
                        },
                    "default_value": "mode_normal",
                    "enabled": "enable_add_tool_nums"
                }
            }
        }"""

    def execute(self, data):
        # Exit if the script is not enabled
        if not self.getSettingValueByKey("enable_add_tool_nums"):
            return data
        mycura = Application.getInstance().getGlobalContainerStack()
        extruder = mycura.extruderList
        # Exit if the printer is a single extruder printer
        if int(mycura.getProperty("machine_extruder_count", "value")) == 1:
            Message(title = "[Flash Forge IDEX Temp Tools]", text = "The script only works on dual extruder printers.  The script exited without running").show()
            return data
        if extruder[0].isEnabled:
            t0_enabled = True
        else:
            t0_enabled = False
        if extruder[1].isEnabled:
            t1_enabled = True
        else:
            t1_enabled = False
        t0_material = str(extruder[0].material.getMetaDataEntry("material", ""))
        t0_temp = str(extruder[0].getProperty("material_print_temperature", "value"))
        t1_material = str(extruder[1].material.getMetaDataEntry("material", ""))
        t1_temp = str(extruder[1].getProperty("material_print_temperature", "value"))
        bed_temp = str(mycura.getProperty("material_bed_temperature", "value"))
        layer_height = str(mycura.getProperty("layer_height", "value"))
        insert_str = ";machine_type: Creator 3\n;right_extruder_material: " + t0_material + "\n;right_extruder_material_density: 1.24\n;left_extruder_material: " + t1_material + "\n;left_extruder_material_density: 1.24\n;filament_diameter0: 1.75\n;right_extruder_temperature: " + t0_temp + "\n;filament_diameter1: 1.75\n;left_extruder_temperature: " + t1_temp + "\n;platform_temperature: " + bed_temp + "\n"
        print_mode = self.getSettingValueByKey("print_mode")
        active_extruder = "0"
        if print_mode == "mode_normal":
            if t1_enabled and not t0_enabled:
                active_extruder = "1"
        location_str = ";start gcode\nM118 X31.60 Y69.10 Z26.65"
        if t0_enabled:
            location_str += " T0"
        if t1_enabled and print_mode in ["mode_mirror", "mode_duplicate"]:
            location_str += " T1"
        if print_mode == "mode_mirror":
            location_str += " D1"
        elif print_mode == "mode_duplicate":
            location_str += " D2"
        location_str += " ; " + print_mode
        if print_mode == "mode_mirror":
            location_str += "\nM7 T0\nM6 T0\nM6 T1\nM651 S255\nM109 T1"
        elif print_mode == "mode_duplicate":
            location_str += "\nM7 T0\nM6 T0\nM6 T1\nM651 S255\nM109 T2"
        elif print_mode == "mode_normal":
            location_str += "\nM7 T0\nM6 T0\nM651 S255\nM108 T" + str(active_extruder)           
        opening_paragraph = data[1].split("\n")
        opening_paragraph.insert(1, insert_str + location_str)
        data[1] = "\n".join(opening_paragraph)

        active_tool = "0"
        # Go through the StartUp Gcode section and track the active tool.  No changes are made to the StartUp Section.  It is assumed that the StartUp Gcode is correct and works.
        lines = data[1].split("\n")
        for line in lines:
            if line.startswith("T"):
                active_tool = self.getValue(line, "T")
        # Go through all the layers and make the changes.
        for num in range(2, len(data)-1):
            lines = data[num].split("\n")
            for index, line in enumerate(lines):
                if line.startswith("T"):
                    active_tool = str(self.getValue(line, "T"))
                if line[0:4] in ["M104","M109"]:
                    if "T" in line:
                        g_cmd = self.getValue(line, "M")
                        tool_num = self.getValue(line, "T")
                        temp = self.getValue(line, "S")
                        lines[index] = f"M{g_cmd} S{temp} T{tool_num}"
                    if not "T" in line:
                        lines[index] = line + " T" + str(active_tool)
                # Move any F parameters to the end of the line
                if " F" in line:
                    f_val = self.getValue(line, "F")
                    lines[index] = lines[index].replace(" F" + str(f_val), "") + " F" + str(f_val)
                # Flash print doens't use G0 so change them all to G1
                if line.startswith("G0"):
                    lines[index] = lines[index].replace("G0", "G1")
                # Change the Cura "TYPE:" lines to "structure:" lines
                if "TYPE:WALL-OUTER" in line:
                    lines[index] = lines[index].replace("TYPE:WALL-OUTER", "structure:shell-outer")
                if "TYPE:WALL-INNER" in line:
                    lines[index] = lines[index].replace("TYPE:WALL-INNER", "structure:shell-inner")
                if "TYPE:FILL" in line:
                    lines[index] = lines[index].replace("TYPE:FILL", "structure:infill-sparse")
                if "TYPE:SKIN" in line:
                    lines[index] = lines[index].replace("TYPE:SKIN", "structure:infill-solid")
                if "TYPE:SKIRT" in line:
                    lines[index] = lines[index].replace("TYPE:SKIRT", "structure:pre-extrude\n;raft")
                if "TYPE:RAFT" in line:
                    lines[index] = lines[index].replace("TYPE:RAFT", "structure:raft")
                if "TYPE:BRIM" in line:
                    lines[index] = lines[index].replace("TYPE:BRIM", "structure:brim")
                if "TYPE:SUPPORT" in line:
                    lines[index] = lines[index].replace("TYPE:SUPPORT", "structure:support ;")
            data[num] = "\n".join(lines)
        return data