# Copyright (c) 2023 GregValiant (Greg Foresi)
#    This script is for Flash Forge printers like the Adventure 3.  The intent is to convert a Cura slice into a gcode suitable for a Flash Forge printer.


from ..Script import Script
from UM.Application import Application
from UM.Message import Message
import re

class FlashForgeA3Converter(Script):

    def initialize(self) -> None:
        super().initialize()
        msg_txt = "NOTE: This is a beta version and may not produce a gcode that is acceptable to Flash Forge firmware.  Please let me know if there are issues with it running, and/or the actual suitability of the post-processed Gcode."
        Message(title = "[Flash Forge Converter]", text = msg_txt).show()

    def getSettingDataString(self):
        return """{
            "name": "Flash Forge Adv3 Converter Beta",
            "key": "FlashForgeA3Converter",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "enable_flash_forge_Adv3_converter":
                {
                    "label": "Enable Adventure 3 Conversion",
                    "description": "This script (is supposed to) convert a Cura Gcode to a form acceptable to the Flash Forge printer.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": true
                }
            }
        }"""

    def execute(self, data):
        # Exit if the script is not enabled
        if not self.getSettingValueByKey("enable_flash_forge_Adv3_converter"):
            return data
        mycura = Application.getInstance().getGlobalContainerStack()
        extruder = mycura.extruderList
        machine_width = int(mycura.getProperty("machine_width", "value"))
        cura_start = data[0].split("\n")
        for line in cura_start:
            if "MINX:" in line or "MIN.X:" in line:
                min_x = abs(float(line.split(":")[1]))
            if "MAXX:" in line or "MAX.X" in line:
                max_x = abs(float(line.split(":")[1]))
        x_size = max_x + min_x
        
#-------------------------------------------------------------------------------------------------------------------------

        # Pull the virgin StartUp Gcode from Cura.  This will include the un-altered replacement patterns
        startup_gcode = mycura.getProperty("machine_start_gcode", "value")
        # Or get the startup section.  This is from the finished gcode and will have the replacements made
        startup_section = data[1]
        # The Extruder Start and Extruder End for each extruder along with the material of each extruder and the initial layer print temperature
        tool_0_start = extruder[0].getProperty("machine_extruder_start_code", "value")
        tool_0_ending = extruder[0].getProperty("machine_extruder_end_code", "value")
        tool_0_material = extruder[0].material.getMetaDataEntry("material", "")
        tool_0_init_temp = extruder[0].getProperty("material_print_temperature_layer_0", "value")
        
        # Break it into lines
        lines = startup_section.split("\n")
        # Add the tool number to hot end temperature lines
        for index, line in enumerate(lines):
            if line.startswith("M104") or line.startswith("M109"):
                lines[index] += " T0"
        data[1] = "\n".join(lines)
#-------------------------------------------------------------------------------------------------------------------------
        
        t0_material = str(extruder[0].material.getMetaDataEntry("material", ""))
        t0_temp = str(extruder[0].getProperty("material_print_temperature", "value"))
        bed_temp = str(mycura.getProperty("material_bed_temperature", "value"))
        layer_height = str(mycura.getProperty("layer_height", "value"))
        location_str = ";extrude_ratio:1"
        # Insert the string at the G92 E0 closest to the start of the initial layer
        opening_paragraph = data[1].split("\n")
        for num in range(len(opening_paragraph) - 1, 0, -1):
            if "G92 E0" in opening_paragraph[num]:
                opening_paragraph.insert(num + 1, location_str)
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
                lines[index] = f"M106 S{fan_speed} T0"
            if line.startswith("M107"):
                lines[index] = "M107 T0"
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
                    continue
                if " F" in line:
                    cur_feedrate = self.getValue(line, "F")
                # Flash print doens't use G0 so change them all to G1
                if line.startswith("G0"):
                    lines[index] = lines[index].replace("G0", "G1")
                    if not " F" in line:
                        lines[index] += f" F{cur_feedrate}"
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

