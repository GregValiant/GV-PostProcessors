# Copyright (c) 2023 Ultimaker B.V.
# The PostProcessingPlugin is released under the terms of the LGPLv3 or higher.

# Modification 06.09.2020
# add checkbox, now you can choose and use configuration from the firmware itself.
# Altered by GregValiant (Greg Foresi) 5-30-2023
#   Moved the FilamentChange code below the ";LAYER:" line

from typing import List
from ..Script import Script
import re

from UM.Application import Application #To get the current printer's settings.

class FilamentChange(Script):

    _gcode_flavor = str(Application.getInstance().getGlobalContainerStack().getProperty("machine_gcode_flavor", "value"))

    def getSettingDataString(self):
        return """{
            "name": "Filament Change",
            "key": "FilamentChange",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "enable_filament_change":
                {
                    "label": "Enable Filament Change",
                    "description": "Uncheck to temporarily disable this feature.",
                    "type": "bool",
                    "default_value": true
                },
                "layer_number":
                {
                    "label": "Layer",
                    "description": "The layer numbers for filament changes. Use the layer numbers from the Cura preview.  The filament change will occur at the START of the layers.  You may specify multiple filament changes by delimitint the layer numbers with a comma (Ex: 5,18,25).",
                    "unit": "",
                    "type": "str",
                    "default_value": "10",
                    "enabled": "enable_filament_change"
                },
                "firmware_config":
                {
                    "label": "Configure M600 or use existing",
                    "description": "Use the settings currently in your firmware, or customise the parameters of the filament change here.  Not all firmware flavors accept all parameters.  You will need to experiment on which ones will be OK with the printer.",
                    "type": "enum",
                    "options":
                        {
                        "manual": "Configure M600",
                        "automatic": "Use Default Settings"
                        },
                    "default_value": "manual",
                    "enabled": "enable_filament_change"
                },
                "beep_count":
                {
                    "label": "    B) Beeps at pause",
                    "description": "The number of beeps that will sound at the filament change.",
                    "type": "int",
                    "default_value": 1,
                    "enabled": "enable_filament_change and firmware_config == 'manual'"
                },
                "retract_amount":
                {
                    "label": "    E) Retraction before park",
                    "description": "Initial filament retraction distance. The filament will be retracted with this amount before moving the nozzle away from the ongoing print.",
                    "unit": "mm  ",
                    "type": "float",
                    "default_value": 6.5,
                    "enabled": "enable_filament_change and firmware_config == 'manual'"
                },
                "unload_amount":
                {
                    "label": "    U) Unload Amount",
                    "description": "This is the unload amount.  Bowden printers will take a large number.  In the gcode the amount will be broken into 150mm chunks to avoid firmware 'over-long extrusion' warnings.",
                    "unit": "mm  ",
                    "type": "int",
                    "default_value": 400,
                    "enabled": "enable_filament_change and firmware_config == 'manual' and machine_gcode_flavor != 'RepRap (RepRap)'"
                },
                "unload_amount_reprap":
                {
                    "label": "    L) Unload Amount RepRap",
                    "description": "RepRap uses 'L' parameter for unload and others use 'U' for unload.  Bowden printers will take a large number.  In the gcode the amount will be broken into 150mm chunks to avoid firmware 'over-long extrusion' warnings.",
                    "unit": "mm  ",
                    "type": "int",
                    "default_value": 400,
                    "enabled": "enable_filament_change and firmware_config == 'manual' and machine_gcode_flavor == 'RepRap (RepRap)'"
                },
                "reload_amount":
                {
                    "label": "    L) Reload Amount",
                    "description": "For all firmware except RepRap this will be the 'U' parameterand is the unload amount.  Bowden printers will take a large number.",
                    "unit": "mm  ",
                    "type": "float",
                    "default_value": 300.0,
                    "enabled": "enable_filament_change and firmware_config == 'manual' and machine_gcode_flavor != 'RepRap (RepRap)'"
                },
                "resume_temperature":
                {
                    "label": "    R) Resume Temperature",
                    "description": "This will usually be the printing temperature of the new material.",
                    "unit": "degrees  ",
                    "type": "int",
                    "default_value": 210,
                    "enabled": "enable_filament_change and firmware_config == 'manual'"
                },
                "tool_number":
                {
                    "label": "    T) Tool Number",
                    "description": "For single extruder machines this will always be '0'.  For multi-extruder machines you can specify which extruder will be affected.  The extruder must be at print temperature.  That can be handled with 'Gcode Before' and reset with 'Gcode After'. To disable - leave the setting blank.",
                    "type": "str",
                    "default_value": "0",
                    "enabled": "enable_filament_change and firmware_config == 'manual'"
                },
                "x_position":
                {
                    "label": "    X) Park Location",
                    "description": "Extruder X position. The print head will move here for filament change.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 0.0,
                    "enabled": "enable_filament_change and firmware_config == 'manual'"
                },
                "y_position":
                {
                    "label": "    Y) Park Location",
                    "description": "Extruder Y position. The print head will move here for filament change.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 0.0,
                    "enabled": "enable_filament_change and firmware_config == 'manual'"
                },
                "z_position":
                {
                    "label": "    Z) move (relative)",
                    "description": "Move the print head this much above the print for the filament change.",
                    "unit": "mm  ",
                    "type": "float",
                    "default_value": 2.0,
                    "minimum_value": 0,
                    "enabled": "enable_filament_change and firmware_config == 'manual'"
                },
                "machine_gcode_flavor":
                {
                    "label": "G-code flavor",
                    "description": "The type of g-code to be generated. This setting is controlled by the script and will not be visible.",
                    "type": "enum",
                    "options":
                    {
                        "RepRap (Marlin/Sprinter)": "Marlin",
                        "RepRap (Volumetric)": "Marlin (Volumetric)",
                        "RepRap (RepRap)": "RepRap",
                        "UltiGCode": "Ultimaker 2",
                        "Griffin": "Griffin",
                        "Makerbot": "Makerbot",
                        "BFB": "Bits from Bytes",
                        "MACH3": "Mach3",
                        "Repetier": "Repetier"
                    },
                    "default_value": "RepRap (Marlin/Sprinter)",
                    "enabled": false
                },
                "enable_before_macro":
                {
                    "label": "Enable G-code Before",
                    "description": "Use this to insert a custom G-code macro before the filament change happens",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "enable_filament_change"
                },
                "before_macro":
                {
                    "label": "G-code Before",
                    "description": "Any custom G-code to run before the filament change happens.  Ex: M300 S400 P1000 for a beep.  For Multi-Line insertions de-limit with a comma.",
                    "unit": "",
                    "type": "str",
                    "default_value": "",
                    "enabled": "enable_filament_change and enable_before_macro"
                },
                "enable_after_macro":
                {
                    "label": "Enable G-code After",
                    "description": "Use this to insert a custom G-code macro after the filament change",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "enable_filament_change"
                },
                "after_macro":
                {
                    "label": "G-code After",
                    "description": "Any custom G-code to run after the filament has been changed.  For Multi-Line insertions de-limit with a comma.",
                    "unit": "",
                    "type": "str",
                    "default_value": "",
                    "enabled": "enable_filament_change and enable_after_macro"
                }
            }
        }"""

    ##  Copy machine name and gcode flavor from global stack so we can use their value in the script stack
    def initialize(self) -> None:
        super().initialize()
        mycura = Application.getInstance().getGlobalContainerStack()
        extruder = mycura.extruderList
        if mycura is None or self._instance is None:
            return

        for key in ["machine_gcode_flavor"]:
            self._instance.setProperty(key, "value", mycura.getProperty("machine_gcode_flavor", "value"))
        self._gcode_flavor = self.getSettingValueByKey("machine_gcode_flavor")
        self._instance.setProperty("initial_retract", "value", extruder[0].getProperty("retraction_amount", "value"))
        self._instance.setProperty("resume_temperature", "value", extruder[0].getProperty("material_print_temperature", "value"))

    def execute(self, data: List[str]):
        enable_filament_change = self.getSettingValueByKey("enable_filament_change")
        if not enable_filament_change:
            data[0] += ";  Filament Change (disabled by user)" + "\n"
            return data
        layer_nums = self.getSettingValueByKey("layer_number")
        b_beeps = self.getSettingValueByKey("beep_count")
        e_retract_amount = self.getSettingValueByKey("retract_amount")
        u_unload_amount = self.getSettingValueByKey("unload_amount")
        lu_unload_amount_reprap = 0
        if self._gcode_flavor == "RepRap (RepRap)":
            lu_unload_amount_reprap = self.getSettingValueByKey("unload_amount_reprap")
        l_reload_amount = self.getSettingValueByKey("reload_amount")
        r_resume_temperature = self.getSettingValueByKey("resume_temperature")
        t_tool_number = self.getSettingValueByKey("tool_number")
        x_pos = self.getSettingValueByKey("x_position")
        y_pos = self.getSettingValueByKey("y_position")
        z_pos = self.getSettingValueByKey("z_position")
        firmware_config = self.getSettingValueByKey("firmware_config")
        enable_before_macro = self.getSettingValueByKey("enable_before_macro")
        before_macro = self.getSettingValueByKey("before_macro")
        if "," in before_macro:
            before_macro = re.sub(",","\n",before_macro)
        enable_after_macro = self.getSettingValueByKey("enable_after_macro")
        after_macro = self.getSettingValueByKey("after_macro")
        if "," in after_macro:
            after_macro = re.sub(",","\n",after_macro)

        color_change = ";-----Start of Filament Change\n"
        m600_line = "M600"
        if enable_before_macro and before_macro != "":
            color_change = color_change + before_macro + "\n"

        if firmware_config == "manual":
            if b_beeps > 0:
                m600_line += f" B{b_beeps}"
            if e_retract_amount is not None and e_retract_amount != 0.0:
                m600_line += f" E{e_retract_amount}"
            if u_unload_amount != 0 and self._gcode_flavor != "RepRap (RepRap)":
                m600_line += f" U{u_unload_amount}"
            # Reprap uses 'L'for unload and Marlin uses 'U' for unload
            if l_reload_amount != 0 and self._gcode_flavor != "RepRap (RepRap)":
                m600_line += f" L{l_reload_amount}"
            if lu_unload_amount_reprap != 0 and self._gcode_flavor == "RepRap (RepRap)":
                m600_line += f" L{lu_unload_amount_reprap}"
            if r_resume_temperature != 0:
                m600_line += f" R{r_resume_temperature}"
            if t_tool_number != "":
                m600_line += f" T{t_tool_number}"
            if x_pos is not None:
                m600_line += f" X{x_pos}"
            if y_pos is not None:
                m600_line += f" Y{y_pos}"
            if z_pos is not None and z_pos > 0.:
                m600_line += f" Z{z_pos}"
        color_change += m600_line
        if enable_after_macro and after_macro != "":
            color_change += "\n" + after_macro
        color_change += "\n;-----End of Filament Change\n"
        layer_targets = layer_nums.split(",")
        if len(layer_targets) > 0:
            for layer_num in layer_targets:
                layer_num = int(layer_num) - 1
                for num in range(2,len(data)-1):
                    if ";LAYER:" + str(layer_num) + "\n" in data[num]:
                        data[num] = data[num].replace(";LAYER:" + str(layer_num) + "\n", ";LAYER:" + str(layer_num) + "\n" + color_change)
                        break
        return data