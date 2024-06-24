# Copyright (c) 2023 GregValiant (Greg Foresi)
#    This script is for Flash Forge IDEX printers that use the 'M104 S T' syntax.  It will convert the Cura M104 and M109 lines from 'M104 T S' syntax.  It also tracks the Tool Number through the gcode and adds the active tool number to all M104 and M109 lines.

from ..Script import Script
from UM.Application import Application
from UM.Message import Message
import re
import os

class FlashForge_IDEX_TempTools(Script):

    def initialize(self) -> None:
        super().initialize()

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
                }
            }
        }"""

    def execute(self, data):
        # Exit if the script is not enabled
        if not self.getSettingValueByKey("enable_add_tool_nums"):
            return data
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
            data[num] = "\n".join(lines)
        return data
