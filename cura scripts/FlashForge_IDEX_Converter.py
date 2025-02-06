# Copyright (c) 2023 GregValiant (Greg Foresi)
#    This script is for Flash Forge IDEX printers like the Creator Pro 2 and Creator 3 Pro.  The intent is to convert a Cura slice into a gcode suitable for a Flash Forge printer.
#    - The Cura M104 and M109 lines will convert from 'M104/9 T S' syntax to 'M104/9 S T' syntax.
#    - The Tool Number is tracked through the gcode and the active tool number is added to all M104 and M109 lines.
#    - The fan lines are changed from 'M106 P' to M106 T'
#    - Cura ':TYPE:" lines will be changed to ";structure:" lines.  The gcode should preview correctly in Flash Print
#    - Selecting the Print Mode (Normal, Duplicate, Mirror) will add relevant commands to the beginning of the file so the printer can adjust it's mode.
#    - [Model Size XY] Normal: X_width up to build plate width.  Y depth up to build plate depth.
#                      Duplicate and Mirror: the X_width limit about 45% of the width of the build plate.  Y depth up to build plate depth.
#                      The gcode should be previewed in FLash Print to insure that the print will fit the bed.
#    - [Model Placement]  The model must be at the 'X' midpoint of the Cura build plate.  If you have multiple models they must all be at the 'X' midpoint.
#    - Duplicate and Mirror -
#          All models on the build plate should be set to the same extruder
#          If the StartUp Gcode Hot End temperatures are not configured correctly - odd things can happen.  Check the Flash Print preview.


from ..Script import Script
from UM.Application import Application
from UM.Message import Message
import re

class FlashForge_IDEX_Converter(Script):

    def initialize(self) -> None:
        super().initialize()
        msg_txt = "    NOTE: The model must be located at the 'X' mid-point of the build plate.\n    If it is a single extruder print then the un-used extruder should be disabled.\nIn 'Normal' mode the model cannot exceed the build plate 'machine_width'.\nIn 'Mirror' or 'Duplicate' mode the model may not exceed about 45% of the 'machine_width'.  Check the gcode preview in Flash Print to ensure the print will fit on the build plate.\n\nNOTE:  'Flash Forge IDEX Converter' should be last in the post-processor list."
        Message(title = "[Flash Forge IDEX Model Placement]", text = msg_txt).show()

    def getSettingDataString(self):
        return """{
            "name": "Flash Forge IDEX Converter Beta",
            "key": "FlashForge_IDEX_Converter",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "enable_flash_forge_IDEX_converter":
                {
                    "label": "Enable FF IDEX Conversion",
                    "description": "This script will convert a slice from a normal Cura slice to a 'Normal', 'Duplicate', or 'Mirror' mode print for the Flash Forge printer.  The printer in Cura must be configured as an 'Origin at Center' machine.  Max Model Size Normal: X300 Y240.  Max Model Size Duplicate or Mirror: X133 Y240.  Multiple models are allowed but all X locations must be '0'.",
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
                    "enabled": "enable_flash_forge_IDEX_converter"
                }
            }
        }"""

    def execute(self, data):
        # Exit if the script is not enabled
        if not self.getSettingValueByKey("enable_flash_forge_IDEX_converter"):
            return data
        mycura = Application.getInstance().getGlobalContainerStack()
        extruder = mycura.extruderList
        machine_width = int(mycura.getProperty("machine_width", "value"))
        print_mode = self.getSettingValueByKey("print_mode")
        cura_start = data[0].split("\n")
        for line in cura_start:
            if "MINX:" in line or "MIN.X:" in line:
                min_x = abs(float(line.split(":")[1]))
            if "MAXX:" in line or "MAX.X" in line:
                max_x = abs(float(line.split(":")[1]))
        x_size = max_x + min_x
        if print_mode != "mode_normal" and x_size > .45 * machine_width or print_mode == "mode_normal" and x_size > machine_width:
            msgtext = "The X footprint of the 'model+skirt/brim/raft+supports' is " + str(x_size) + "mm.\nYou must view the gcode file in the Flash Print preview to ensure the print will fit the build plate of the printer."
            Message(title = "[FlashForge Max Footprint]", text = msgtext).show()
        # Exit if the printer is a single extruder printer
        if int(mycura.getProperty("machine_extruder_count", "value")) == 1:
            #Message(title = "[Flash Forge IDEX Temp Tools]", text = "The script only works on dual extruder printers.  The script exited without running").show()
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
        # Put together the opening conversion string
        insert_str = ";----- Flash Forge IDEX Converter Start"
        insert_str += "\n;machine_type: Flash Forge Creator 2/3 Pro\n;right_extruder_material: " + t0_material + "\n;right_extruder_material_density: 1.24\n;left_extruder_material: " + t1_material + "\n;left_extruder_material_density: 1.24\n;filament_diameter0: 1.75\n;right_extruder_temperature: " + t0_temp + "\n;filament_diameter1: 1.75\n;left_extruder_temperature: " + t1_temp + "\n;platform_temperature: " + bed_temp + "\n"
        location_str = ";start gcode\nM118 X31.60 Y69.10 Z26.65"
        location_str += " T0"
        if print_mode in ["mode_mirror", "mode_duplicate"]:
            location_str += " T1"
        if print_mode == "mode_mirror":
            location_str += " D1"
        elif print_mode == "mode_duplicate":
            location_str += " D2"
        location_str += " ; " + print_mode
        if print_mode == "mode_mirror":
            location_str += "\nM7 T0\nM6 T0\nM6 T1\nM651 S255\nM109 T1"
        elif print_mode == "mode_duplicate":
            location_str += "\nM7 T0\nM6 T0\nM6 T1\nM651 S255\nM109 T0"            
        elif print_mode == "mode_normal":
            location_str += "\nM7 T0\nM6 T0"
            location_str += "\nM651 S255\nM108 T0"            
        location_str += "\n;extrude_ratio:1\n;----- End of Flash Forge Start"
        # Insert the string at the G92 E0 closest to the start of the initial layer
        opening_paragraph = data[1].split("\n")
        for num in range(len(opening_paragraph) - 1, 0, -1):
            if "G92 E0" in opening_paragraph[num]:
                opening_paragraph.insert(num + 1, insert_str + location_str)
                break
        data[1] = "\n".join(opening_paragraph)

        active_tool = "0"
        # Go through the StartUp Gcode section and track the active tool.  It is assumed that the StartUp Gcode is correct and works.  If there is an M106 or M107 it will be changed.
        lines = data[1].split("\n")
        for index, line in enumerate(lines):
            if line.startswith("T"):
                active_tool = self.getValue(line, "T")
            if line.startswith("M106 S"):
                fan_speed = self.getValue(line, "S")
                lines[index] = f"M106 S{fan_speed} T0\nM106 S{fan_speed} T1"
            if line.startswith("M107"):
                lines[index] = "M107 T0\nM107 T1"
        data[1] = "\n".join(lines)

        # Go through all the layers and make the changes.
        for num in range(2, len(data)-1):
            lines = data[num].split("\n")
            for index, line in enumerate(lines):
                if line.startswith("T"):
                    active_tool = str(self.getValue(line, "T"))
                    continue
                
                # Rearrange the tool numbers in the temperature lines.  Add the tool number if it isn't there.
                if line[0:4] in ["M104","M109"]:
                    if " T" in line and not ";" in line:
                        g_cmd = self.getValue(line, "M")
                        tool_num = self.getValue(line, "T")
                        temp = self.getValue(line, "S")
                        lines[index] = f"M{g_cmd} S{temp} T{tool_num}"
                    if not " T" in line and not ";" in line:
                        lines[index] = line + " T" + str(active_tool)
                    if " T" in line and ";" in line:
                        g_cmd = self.getValue(line, "M")
                        tool_num = self.getValue(line, "T")
                        temp = self.getValue(line, "S")
                        c_comment = self._get_comment
                        lines[index] = f"M{g_cmd} S{temp} T{tool_num} {c_comment}"
                    # If there is a comment at the end of the line it needs to be handled differently
                    elif not "T" in line and ";" in line:
                        frt_part = line.split(";")[0].rstrip()
                        frt_part = frt_part + " T" + str(active_tool)
                        c_comment = self._get_comment(line)
                        lines[index] = frt_part + c_comment
                
                # Move any F parameters to the end of the line
                if " F" in line and self.getValue(line, "F") is not None:
                    f_val = self.getValue(line, "F")
                    if not ";" in line:
                        lines[index] = lines[index].replace(" F" + str(f_val), "") + " F" + str(f_val)
                    # If there is a comment at the end of the line it needs to be handled differently
                    else:
                        frt_part = line.split(";")[0].rstrip()
                        c_comment = self._get_comment(line)
                        frt_part = frt_part.replace(" F" + str(f_val), "") + " F" + str(f_val)
                        lines[index] = frt_part + c_comment
                
                # Make adjustments to the fan lines
                if line.startswith("M107"):
                    lines[index] = "M106 S0 T0\nM106 S0 T1"
                    continue
                if line.startswith("M106"):
                    fan_speed = self.getValue(line, "S")
                    lines[index] = "M106 S" + str(fan_speed) + " T0"
                    if print_mode != "mode_normal":
                        lines[index] += "\nM106 S" + str(fan_speed) + " T1"
                    continue
                # Flash print doens't use G0 so change them all to G1
                if line.startswith("G0"):
                    lines[index] = lines[index].replace("G0", "G1")
                    continue
                
                # Changing the "TYPE" lines to "structure" lines allows the preview to show correctly in Flash Print
                if "TYPE:WALL-OUTER" in line:
                    lines[index] = lines[index].replace("TYPE:WALL-OUTER", "structure:shell-outer")
                    continue
                if "TYPE:WALL-INNER" in line:
                    lines[index] = lines[index].replace("TYPE:WALL-INNER", "structure:shell-inner")
                    continue
                if "TYPE:FILL" in line:
                    lines[index] = lines[index].replace("TYPE:FILL", "structure:infill-sparse")
                    continue
                if "TYPE:SKIN" in line:
                    lines[index] = lines[index].replace("TYPE:SKIN", "structure:infill-solid")
                    continue
                if "TYPE:SKIRT" in line:
                    lines[index] = lines[index].replace("TYPE:SKIRT", "structure:pre-extrude\n;raft")
                    continue
                if "TYPE:RAFT" in line:
                    lines[index] = lines[index].replace("TYPE:RAFT", "structure:raft")
                    continue
                if "TYPE:BRIM" in line:
                    lines[index] = lines[index].replace("TYPE:BRIM", "structure:brim")
                    continue
                if "TYPE:SUPPORT-INTERFACE" in line:
                    lines[index] = ";support-start\n;structure:line-support-solid\n" + line
                    new_index = index + 1
                    for nr in range(new_index, len(lines) - 1):
                        if lines[nr].startswith(";"):
                            lines[nr] = ";support-end\n" + lines[nr]
                            break
                    continue
                if "TYPE:SUPPORT" in line:
                    lines[index] = ";support-start\n;structure:line-support-sparse\n" + line
                    new_index = index + 1
                    for nr in range(new_index, len(lines) - 1):
                        if lines[nr].startswith(";"):
                            lines[nr] = ";support-end\n" + lines[nr]
                            break
                    continue
                if "TYPE:CUSTOM" in line:
                    lines[index] = lines[index] = ";structure:custom" + lines[index]
                    continue
            data[num] = "\n".join(lines)
        
        # This final section adds the ';layer:x.xx' lines that indicate the layer height to the Flash Print Gcode pre-viewer.
        # Both Adaptive Layers and Z-hops must be considered.
        cur_z = float(mycura.getProperty("layer_height_0", "value"))
        z_hop_enabled = bool(extruder[0].getProperty("retraction_hop_enabled", "value"))
        layer_hgt = cur_z
        working_z = cur_z
        prev_z = 0.0
        hop_up = False
        if not z_hop_enabled:
            for num in range(2, len(data) - 1):
                # For one-at-a-time items in the data[list] that are not layers.
                if re.search(";LAYER:", data[num]) is None:
                    continue
                lines = data[num].split("\n")
                for index, line in enumerate(lines):
                    if " Z" in line and self.getValue(line, "Z") is not None:
                        cur_z = float(self.getValue(line, "Z"))
                        layer_hgt = round(cur_z - prev_z, 2)
                        # This is required for pause code that can produce large Z moves or relative moves.
                        if layer_hgt < 0: layer_hgt = layer_height
                        prev_z = cur_z
                    if line.startswith(";LAYER:"):
                        lines[index] = line + "\n;layer:" + str(layer_hgt)
                data[num] = "\n".join(lines)
                
        elif z_hop_enabled:
            l_index = 0
            for num in range(1, len(data) - 1):
                # For one-at-a-time items in the data[list] that are not layers.
                if re.search(";LAYER:", data[num]) is None:
                    continue
                lines = data[num].split("\n")
                for index, line in enumerate(lines):
                    # In case another post processor added lines before the LAYER line.
                    if re.search(";LAYER:", line) is not None:
                        l_index = index
                        # Track the Z so the actual layer height can be calculated
                    if re.search("G1 Z(\d.*) F(\d.*)", line) is not None:
                        cur_z = self.getValue(line, "Z")
                        continue
                    if line.startswith("G1") and " X" in line and " Y" in line and " Z" in line:
                        cur_z = self.getValue(line, "Z")
                        continue
                    if line.startswith("G1") and " X" in line and " Y" in line and " E" in line:   
                        if "\n" not in lines[l_index]:                     
                            layer_hgt = round(cur_z - prev_z, 2)
                            lines[l_index] = lines[l_index] + "\n;layer:" + str(layer_hgt)
                            prev_z = cur_z
                data[num] = "\n".join(lines)
        return data

    def _get_comment(self, c_line: str) -> str:
        frt_part = c_line.split(";")[0]
        frt_len = len(frt_part)
        frt_part = frt_part.rstrip()
        frt_2_len = len(frt_part)
        spaces = frt_len - frt_2_len
        c_comment = (" " * spaces) + ";" + c_line.split(";")[1]
        return c_comment

