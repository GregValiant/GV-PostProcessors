# Copyright (c) 2023 GregValiant (Greg Foresi)
#    This script is for Flash Forge printers like the Adventure 3.  The intent is to convert a Cura slice into a gcode suitable for a Flash Forge printer.
#    The script assumes that the StartUp Gcode is configured correctly and that M104\nM6 and M140/nM7 are used in the start-up as "wait" commands.

from ..Script import Script
from UM.Application import Application
from UM.Message import Message
import re

class MarlinToFlashForgeConverter(Script):

    def initialize(self) -> None:
        super().initialize()
        msg_txt = "NOTE:This script is not for use with multi-extruder printers.\n\nNOTE: This script is designed to produce a gcode that is acceptable to Flash Forge firmware and the Flash Print previewer.  Please let me know of any problems."
        Message(title = "[Marlin-to-FlashForge Converter (Beta)]", text = msg_txt).show()

    def getSettingDataString(self):
        return """{
            "name": "Marlin-to-FlashForge Converter One Extruder",
            "key": "MarlinToFlashForgeConverter",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "enable_marlin_to_flash_forge_converter":
                {
                    "label": "Enable 'Marlin-to-FlashForge' Converter",
                    "description": "This script (is supposed to) convert a Cura Marlin Gcode to a Flash Forge gcode.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": true
                }
            }
        }"""

    def execute(self, data):
        # Exit if the script is not enabled
        if not self.getSettingValueByKey("enable_marlin_to_flash_forge_converter"):
            return data
        curaApp = Application.getInstance().getGlobalContainerStack()
        extruder = curaApp.extruderList
        # Don't allow the script to run if the gcode has already been post-processed.
        if ";Flavor:FlashForge" in data[0]:
            return data
        cooling_fan_nr = extruder[0].getProperty("machine_extruder_cooling_fan_number", "value")
        bv_fan_nr = curaApp.getProperty("build_volume_fan_nr", "value")
        
#-------------------------------------------------------------------------------------------------------------------------
        # Change the G-Code flavor in line 1
        data[0] = "\n" + data[0]
        data[0] = re.sub("Marlin", "FlashForge", data[0])
        layer_height = str(curaApp.getProperty("layer_height", "value"))
        # Insert the 'extruder_ratio' string at the G92 E0 closest to the start of the initial layer
        opening_paragraph = data[1].split("\n")
        for index, line in enumerate(opening_paragraph):
            if "G92 E0" in line:
                opening_paragraph.insert(index + 1, ";extrude_ratio:1")
        data[1] = "\n".join(opening_paragraph)

        # Add the T number to any fan lines in the startup
        lines = data[1].split("\n")
        for index, line in enumerate(lines):
            if line.startswith("M106 S"):
                fan_speed = self.getValue(line, "S")
                lines[index] = f"M106 S{fan_speed} T0"
            if line.startswith("M107"):
                lines[index] = "M107 T0                      ; Fan off"
        data[1] = "\n".join(lines)

        # Go through all the layers and make the changes.
        for num in range(2, len(data)-1):
            lines = data[num].split("\n")
            for index, line in enumerate(lines):
                if line.startswith("T"):
                    active_tool = str(self.getValue(line, "T"))
                    lines[index] = f"M108 T{active_tool}"
                    continue

                # Rearrange the tool numbers in the temperature lines.  Add the tool number if it isn't there.
                if line.startswith("M104"):
                    # yes tool - no comment
                    if " T" in line and not ";" in line:
                        tool_num = self.getValue(line, "T")
                        temp = self.getValue(line, "S")
                        lines[index] = f"M104 S{temp} T{tool_num}"
                    # no tool - no comment
                    if not " T" in line and not ";" in line:
                        lines[index] = line + " T0"
                    # yes tool - yes comment
                    if " T" in line and ";" in line:
                        tool_num = self.getValue(line, "T")
                        temp = self.getValue(line, "S")
                        c_comment = self._get_comment(line)
                        lines[index] = f"M104 S{temp} T{tool_num}{c_comment[3:]}"
                    # no tool - yes comment
                    elif not "T" in line and ";" in line:
                        frt_part = line.split(";")[0].rstrip()
                        frt_part = frt_part + " T0"
                        c_comment = self._get_comment(line)
                        lines[index] = frt_part + c_comment[3:]
                    continue
                if line.startswith("M109"):
                    temp = self.getValue(line, line[5])
                    lines[index] = f"M104 S{temp} T0               ; Resume temperature\nM6                         ; Wait for hot end"
                    continue
                if line.startswith("M190"):
                    temp = self.getValue(line, "S")
                    lines[index] += f"M140 S{temp} T0\nM7"
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
                    lines[index] = "M107 T0"
                    continue
                if line.startswith("M106") and " P" in line:
                    fan_num = self.getValue(line, "P")
                    fan_speed = self.getValue(line, "S")
                    if fan_num != cooling_fan_nr:
                        if fan_speed > 0:
                            lines[index] = f"M651 S{fan_speed}"
                        else:
                            lines[index] = "M652"
                    else:
                        lines[index] = re.sub("P", "T", lines[index])
                        continue
                if line.startswith("M106") and not "P" in line:
                    fan_speed = self.getValue(line, "S")
                    lines[index] = f"M106 S{fan_speed} T0"
                    continue
                if " F" in line:
                    cur_feedrate = self.getValue(line, "F")
                # Change all G0 commands to G1's
                if line.startswith("G0"):
                    lines[index] = lines[index].replace("G0", "G1")
                    if not " F" in line:
                        lines[index] = lines[index].replace("G1", f"G1 F{cur_feedrate}")
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
                    lines[index] = ";support-start\n;structure:line-support-solid"
                    new_index = index + 1
                    for nr in range(new_index, len(lines) - 1):
                        if lines[nr].startswith(";"):
                            lines[nr] = ";support-end\n" + lines[nr]
                            break
                    continue
                if "TYPE:SUPPORT" in line:
                    lines[index] = ";support-start\n;structure:line-support-sparse"
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
        cur_z = float(curaApp.getProperty("layer_height_0", "value"))
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
                    # Track the Z so the actual layer height can be determined
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