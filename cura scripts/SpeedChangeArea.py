# Copyright (c) 2023 UltiMaker
#  Designed by GregValiant (Greg Foresi) 6-1-2023
#  Add temperature changes and/or Park and Wait for Bridges.
#  Adjusts the total print ";TIME:" and layer ";TIME_ELAPSED:" if M109 is used.

from ..Script import Script
import re
from UM.Application import Application
from UM.Message import Message
from typing import List, Tuple

class SpeedChangeInArea(Script):

    def initialize(self) -> None:
        super().initialize()
        self.curaApp = Application.getInstance().getGlobalContainerStack()
        self.machine_width = self.curaApp.getProperty("machine_width", "value")
        self.machine_depth = self.curaApp.getProperty("machine_depth", "value")
        self.machine_height = self.curaApp.getProperty("machine_height", "value")
        self.origin_at_center = False if self.curaApp.getProperty("print_sequence", "value") == "all_at_once" else True
        self.machine_z_min = 0.00
        self.machine_z_max = round(self.machine_height, 2)
        if self.origin_at_center:
            self.machine_x_min = -(round(self.machine_width / 2, 2))
            self.machine_x_max = round(self.machine_width / 2, 2)
            self.machine_y_min = -(round(self.machine_depth / 2, 2))
            self.machine_y_max = round(self.machine_depth / 2, 2)
        else:
            self.machine_x_min = 0.00
            self.machine_x_max = self.machine_width
            self.machine_y_min = 0.00
            self.machine_y_max = self.machine_depth

    def getSettingDataString(self) -> str:
        return """{
            "name": "Speed Change in an Area",
            "key": "SpeedChangeInArea",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "speed_percent":
                {
                    "label": "Print Speed Adjustment %",
                    "description": "Adjust print speed to this value in the ranges described below.",
                    "type": "int",
                    "unit": "% ",
                    "default_value": 100,
                    "enabled": true
                },
                "enable_x_range":
                {
                    "label": "Enable 'X' range",
                    "description": "Enable a range in the 'X' to change speeds.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": true
                },
                "x_min_cutoff":
                {
                    "label": "    'X' Minimum cutoff",
                    "description": "At an 'X' above this; the speed will be altered.",
                    "type": "int",
                    "default_value": 0,
                    "minimum_value": "self.machine_x_min",
                    "maximum_value": "self.machine_x_max",
                    "enabled": "enable_x_range"
                },
                "x_max_cutoff":
                {
                    "label": "    'X' Maximum cutoff",
                    "description": "At an 'X' below this; the speed will be altered.",
                    "type": "int",
                    "default_value": 220,
                    "minimum_value": "self.machine_x_min",
                    "maximum_value": "self.machine_x_max",
                    "enabled": "enable_x_range"
                },
                "enable_y_range":
                {
                    "label": "Enable 'Y' range",
                    "description": "Enable a range in the 'Y' to change speeds.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": true
                },
                "y_min_cutoff":
                {
                    "label": "    'Y' Minimum cutoff",
                    "description": "At a 'Y' above this; the speed will be altered.",
                    "type": "int",
                    "default_value": 0,
                    "minimum_value": "self.machine_y_min",
                    "maximum_value": "self.machine_y_max",
                    "enabled": "enable_y_range"
                },
                "y_max_cutoff":
                {
                    "label": "    'Y' Maximum cutoff",
                    "description": "At a 'Y' below this; the speed will be altered.",
                    "type": "int",
                    "default_value": 230,
                    "minimum_value": "self.machine_y_min",
                    "maximum_value": "self.machine_y_max",
                    "enabled": "enable_y_range"
                },
                "enable_z_range":
                {
                    "label": "Enable 'Z' range",
                    "description": "Enable a range in the 'Z' to change speeds.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": true
                },
                "z_min_cutoff":
                {
                    "label": "    'Z' Minimum cutoff",
                    "description": "At a 'Z' above this; the speed will be altered.",
                    "type": "int",
                    "default_value": 0,
                    "minimum_value": 0,
                    "maximum_value": 250,
                    "enabled": "enable_z_range"
                },
                "z_max_cutoff":
                {
                    "label": "    'Z' Maximum cutoff",
                    "description": "At a 'Z' below this; the speed will be altered.",
                    "type": "int",
                    "default_value": 230,
                    "minimum_value": 0,
                    "maximum_value": 250,
                    "enabled": "enable_z_range"
                }
            }
        }"""

    def execute(self, data: List[str]) -> List[str]:
        speed_percent = self.getSettingValueByKey("speed_percent") / 100
        x_cur = 0.0; x_prev = 0.0; valid_x = False
        if self.getSettingValueByKey("enable_x_range"):
            x_min = self.getSettingValueByKey("x_min_cutoff")
            x_max = self.getSettingValueByKey("x_max_cutoff")
        else:
            x_min = self.machine_x_min
            x_max = self.machine_x_max
        y_cur = 0.0; y_prev = 0.0; valid_y = False
        if self.getSettingValueByKey("enable_y_range"):
            y_min = self.getSettingValueByKey("y_min_cutoff")
            y_max = self.getSettingValueByKey("y_max_cutoff")
        else:
            y_min = self.machine_y_min
            y_max = self.machine_y_max
        z_cur = 0.0; z_prev = 0.0; valid_z = False
        if self.getSettingValueByKey("enable_z_range"):
            z_min = self.getSettingValueByKey("z_min_cutoff")
            z_max = self.getSettingValueByKey("z_max_cutoff")
        else:
            z_min = self.machine_z_min
            z_max = self.machine_z_max

        f_cur = 0.0
        move_cmd = ["G0 ", "G1 ", "G2 ", "G3 "]
        for index, layer in enumerate(data):
            lines = layer.split("\n")
            for l_index, line in enumerate(lines):
                if line[:3] in move_cmd:
                    if " F" in line:
                        f_cur = self.getValue(line, "F")
                    if " X" in line:
                        x_cur = self.getValue(line, "X")
                    if " Y" in line:
                        y_cur = self.getValue(line, "Y")
                    if " Z" in line:
                        z_cur = self.getValue(line, "Z")
                if x_min < x_cur < x_max or x_min < x_prev < x_max:
                    valid_x = True
                else:
                    valid_x = False
                if y_min < y_cur < y_max or y_min < y_prev < y_max:
                    valid_y = True
                else:
                    valid_y = False
                if z_min < z_cur < z_max:
                    valid_z = True
                else:
                    valid_z = False
                
                if valid_x and valid_y and valid_z:
                    if line.startswith("G1 ") and " F" in line:
                        lines[l_index] = re.sub(f"F{f_cur}", f"F{round(f_cur*speed_percent)} ", line)
                    elif line.startswith("G1") and not " F" in line and (" X" in line or " Y" in line):
                        lines[l_index] = re.sub("G1 ", f"G1 F{round(f_cur*speed_percent)} ", line)
                else:
                    lines[l_index] = re.sub("G1 ", f"G1 F{round(f_cur)} ", line)                
                x_prev = x_cur
                y_prev = y_cur
                z_prev = z_cur
            data[index] = "\n".join(lines)
        return data