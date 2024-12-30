# GregValiant
#   This script is a redo of 'Change At Z'.
#     "By Height" is obsolete as ChangAtZ could be fooled by Adaptive Layers, Z-hops, and Scarf Seams.
#     The use of M220 to change speeds is obolete and the user can opt to change just the print speed or both print and travel speeds.  The gcode lines are changed to the new F values.
#     Output to LCD will add an M118 to output the message to a print server.
#     Allows the user to select a Range of layers rather than just 'Single Layer' or 'To the End'.
#     Added support for Relative Extrusion
#     Version number changed to 1.0.0

from UM.Application import Application
from ..Script import Script
import re
from UM.Message import Message
from UM.Logger import Logger

class ChangeAtLayer(Script):
    version = "1.0.0"

    def initialize(self) -> None:
        super().initialize()
        curaApp = Application.getInstance().getGlobalContainerStack()
        machine_extruder_count = int(curaApp.getProperty("machine_extruder_count", "value"))
        if machine_extruder_count == 1:
            self._instance.setProperty("multi_extruder", "value", False)
        else:
            self._instance.setProperty("multi_extruder", "value", True)
        machine_heated_build_volume = bool(curaApp.getProperty("machine_heated_build_volume", "value"))
        if machine_heated_build_volume:
            self._instance.setProperty("heated_build_volume", "value", True)
        else:
            self._instance.setProperty("heated_build_volume", "value", False)

    def getSettingDataString(self):
        return """{
            "name": "Change At Layer",
            "key": "ChangeAtLayer",
            "metadata": {},
            "version": 2,
            "settings": {
                "cal_enabled": {
                    "label": "Enable Change at Layer",
                    "description": "Enables the script so it will run.  You may have more than one instance of 'Change At Layer' in the list of post processors.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": true
                },
                "a_start_layer": {
                    "label": "Start Layer",
                    "description": "Layer number to start the changes at.  Use the Cura preview layer numbers.  The changes will start at the beginning of the layer.",
                    "unit": "",
                    "type": "int",
                    "default_value": 1,
                    "minimum_value": "-7",
                    "minimum_value_warning": "1",
                    "unit": "Layer #",
                    "enabled": "cal_enabled"
                },
                "a_end_layer": {
                    "label": "End Layer",
                    "description": "Use '-1' to indicate the end of the last layer.  The changes will end at the end of the indicated layer.  Use the Cura preview layer number.  If the 'Start Layer' is equal to the 'End Layer' then the changes only affect that single layer.",
                    "type": "int",
                    "default_value": -1,
                    "unit": "Layer #",
                    "enabled": "cal_enabled"
                },
                "b_change_speed": {
                    "label": "Change Speeds",
                    "description": "Check to enable a speed change for the Print Speeds.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "cal_enabled"
                },
                "b_change_printspeed": {
                    "label": "    Include Travel Speeds",
                    "description": "Check this box to change the Travel Speeds as well as the Print Speeds.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": "b_change_speed and cal_enabled"
                },
                "b_speed": {
                    "label": "    Speed %",
                    "description": "Speed factor as a percentage.  The chosen speeds will be altered by this much.",
                    "unit": "%  ",
                    "type": "int",
                    "default_value": 100,
                    "minimum_value": "10",
                    "minimum_value_warning": "50",
                    "maximum_value_warning": "200",
                    "enabled": "b_change_speed and cal_enabled"
                },
                "c_change_flowrate": {
                    "label": "Change Flow Rate",
                    "description": "Select to change the flow rate of all extrusions in the layer range.  This command uses M221 to set the flow percentage in the printer.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "cal_enabled"
                },
                "c_flowrate_t0": {
                    "label": "    Flow Rate % (T0)",
                    "description": "Enter the new Flow Rate Percentage.  For a multi-extruder printer this will apply to Extruder 1 (T0).",
                    "unit": "%  ",
                    "type": "int",
                    "default_value": 100,
                    "minimum_value": "25",
                    "minimum_value_warning": "50",
                    "maximum_value_warning": "150",
                    "maximum_value": "200",
                    "enabled": "c_change_flowrate and cal_enabled"
                },
                "multi_extruder": {
                    "label": "Hidden setting to enable 2nd extruder settings for multi-extruder printers.",
                    "description": "Enable T1 options.",
                    "type": "bool",
                    "value": false,
                    "default_value": false,
                    "enabled": false
                },
                "c_flowrate_t1": {
                    "label": "    Flow Rate % T1",
                    "description": "New Flow rate percentage for Extruder 2 (T1).",
                    "unit": "%  ",
                    "type": "int",
                    "default_value": 100,
                    "minimum_value": "1",
                    "minimum_value_warning": "10",
                    "maximum_value_warning": "200",
                    "enabled": "multi_extruder and c_change_flowrate and cal_enabled"
                },
                "d_change_bed_temp": {
                    "label": "Change Bed Temp",
                    "description": "Select if Bed Temperature is to be changed.  The bed temperature will revert at the End Layer.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "cal_enabled"
                },
                "d_bedTemp": {
                    "label": "    Bed Temp",
                    "description": "New Bed Temperature",
                    "unit": "°C  ",
                    "type": "int",
                    "default_value": 60,
                    "minimum_value": "0",
                    "minimum_value_warning": "30",
                    "maximum_value_warning": "120",
                    "enabled": "d_change_bed_temp and cal_enabled"
                },
                "heated_build_volume": {
                    "label": "Hidden setting",
                    "description": "This enables the build volume settings",
                    "type": "bool",
                    "default_value": false,
                    "enabled": false
                },
                "e_change_build_volume_temperature": {
                    "label": "Change Build Volume Temperature",
                    "description": "Select if Build Volume Temperature is to be changed",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "heated_build_volume and cal_enabled"
                },
                "e_build_volume_temperature": {
                    "label": "    Build Volume Temperature",
                    "description": "New Build Volume Temperature.  This will revert at the end of the End Layer.",
                    "unit": "°C  ",
                    "type": "int",
                    "default_value": 20,
                    "minimum_value": "0",
                    "minimum_value_warning": "15",
                    "maximum_value_warning": "50",
                    "enabled": "heated_build_volume and e_change_build_volume_temperature and cal_enabled"
                },
                "f_change_extruder_temperature": {
                    "label": "Change Print Temp",
                    "description": "Select if the Printing Temperature is to be changed",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "cal_enabled"
                },
                "f_extruder_temperature_t0": {
                    "label": "    Extruder 1 Temp (T0)",
                    "description": "New temperature for Extruder 1 (T0).",
                    "unit": "°C  ",
                    "type": "int",
                    "default_value": 190,
                    "minimum_value": "0",
                    "minimum_value_warning": "160",
                    "maximum_value_warning": "250",
                    "enabled": "f_change_extruder_temperature and cal_enabled"
                },
                "f_extruder_temperature_t1": {
                    "label": "    Extruder 2 Temp (T1)",
                    "description": "New temperature for Extruder 2 (T1).",
                    "unit": "°C  ",
                    "type": "int",
                    "default_value": 190,
                    "minimum_value": "0",
                    "minimum_value_warning": "160",
                    "maximum_value_warning": "250",
                    "enabled": "multi_extruder and f_change_extruder_temperature and cal_enabled"
                },
                "g_change_retract": {
                    "label": "Change Retraction Settings",
                    "description": "Indicates you would like to modify retraction properties.  If 'Firmware Retraction' is enabled then M207 and M208 lines are added.  Your firmware must understand those commands.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "cal_enabled and not multi_extruder"
                },
                "g_change_retract_speed": {
                    "label": "    Change Retract/Prime Speed",
                    "description": "Changes the retraction and prime speed.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "g_change_retract and cal_enabled and not multi_extruder"
                },
                "g_retract_speed": {
                    "label": "        Retract/Prime Speed",
                    "description": "New Retract Feed Rate (mm/s).  If 'Firmware Retraction' is used then M207 and M208 are used to change the retract and prime speeds and the distance.  NOTE: the same speed will be used for both retract and prime.",
                    "unit": "mm/s  ",
                    "type": "float",
                    "default_value": 40,
                    "minimum_value": "0",
                    "minimum_value_warning": "0",
                    "maximum_value_warning": "100",
                    "enabled": "g_change_retract and g_change_retract_speed and cal_enabled and not multi_extruder"
                },
                "g_change_retract_amount": {
                    "label": "    Change Retraction Amount",
                    "description": "Changes the retraction length during print",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "g_change_retract and cal_enabled and not multi_extruder"
                },
                "g_retract_amount": {
                    "label": "        Retract Amount",
                    "description": "New Retraction Distance (mm).  If firmware retraction is used then M207 and M208 are used to change the retract and prime amount.",
                    "unit": "mm  ",
                    "type": "float",
                    "default_value": 6.5,
                    "minimum_value": "0",
                    "minimum_value_warning": "0",
                    "maximum_value_warning": "20",
                    "enabled": "g_change_retract and g_change_retract_amount and cal_enabled and not multi_extruder"
                }
            }
        }"""

    def execute(self, data):
        # Exit if the script isn't enabled
        if not bool(self.getSettingValueByKey("cal_enabled")):
            data[0] += ";  [Change at Layer] is not enabled.\n"
            Logger.log("i", "[Change at Layer] is not enabled.")
            return data

        curaApp = Application.getInstance().getGlobalContainerStack()
        extruder = curaApp.extruderList
        firmware_retraction = bool(curaApp.getProperty("machine_firmware_retract", "value"))
        relative_extrusion = bool(curaApp.getProperty("relative_extrusion", "value"))
        self.extruder_count = curaApp.getProperty("machine_extruder_count", "value")
        self.heated_build_volume = curaApp.getProperty("machine_heated_build_volume", "value")
        start_layer = self.getSettingValueByKey("a_start_layer") - 1
        end_layer = self.getSettingValueByKey("a_end_layer")
        retract_enabled = bool(extruder[0].getProperty("retraction_enable", "value"))
        self.orig_bed_temp = curaApp.getProperty("material_bed_temperature", "value")
        self.orig_bv_temp = curaApp.getProperty("build_volume_temperature", "value")
        # Find the indexes of the Start and End layers
        start_index = None
        end_index = len(data) - 1
        for index, layer in enumerate(data):
            if ";LAYER:" + str(start_layer) + "\n" in layer:
                start_index = index
                break
        if end_layer == -1:
            if retract_enabled:
                end_index = len(data) - 2
            else:
                end_index = len(data) - 1
        else:
            end_layer -= 1
            for index, layer in enumerate(data):
                if ";LAYER:" + str(end_layer) + "\n" in layer:
                    end_index = index
                    break
        # Exit if the Start Layer wasn't found
        if start_index == None:
            Message(title = "[Change at Layer]", text = "The 'Start Layer' is beyond the top of the print.  The script did not run.").show()
            Logger.log("w", "[Change at Layer] The 'Start Layer' is beyond the top of the print.  The script did not run.")
            return data
        # Adjust the End Index if the End Index < Start Index or the script doesn't do anything
        if end_index < start_index:
            start_index = end_index
            Message(title = "[Change at Layer]", text = "Check the Gcode.  Your 'Start Layer' input is higher than the End Layer input.  The Start Layer has been adjusted to equal the End Layer.").show()
        self.start_index = start_index
        self.end_index = end_index

        # Run the selected procedures
        # Mapping settings to corresponding methods
        procedures = {
            "b_change_speed": self._change_speed,
            "c_change_flowrate": self._change_flow,
            "d_change_bed_temp": self._change_bed_temp,
            "e_change_build_volume_temperature": self._change_bv_temp,
            "f_change_extruder_temperature": self._change_hotend_temp,
            "g_change_retract": self._change_retract
        }
        # Run selected procedures
        for setting, method in procedures.items():
            if self.getSettingValueByKey(setting):
                method(data)
        data = self._format_lines(data)
        return data

# What to do about Rafts and one-at-a-time

    def _change_speed(self, data:str)->str:
        speed_x = self.getSettingValueByKey("b_speed")/100
        print_speed_only = not bool(self.getSettingValueByKey("b_change_printspeed"))
        for index, layer in enumerate(data):
            if index >= self.start_index and index <= self.end_index:
                lines = layer.splitlines()
                for l_index, line in enumerate(lines):
                    if " F" in line and " X" in line and " Y" in line and not " Z" in line:
                        f_value = self.getValue(line, "F")
                        if line.startswith(("G1", "G2", "G3")):
                            lines[l_index] = line.replace("F" + str(f_value), "F" + str(round(f_value * speed_x)))
                            lines[l_index] += f" ; Change_at_Layer: {round(speed_x * 100)}% Print Speed"
                            continue
                        if not print_speed_only and line.startswith("G0"):
                            lines[l_index] = line.replace("F" + str(f_value), "F" + str(round(f_value * speed_x)))
                            lines[l_index] += f" ; Change_at_Layer: {round(speed_x * 100)}% Travel Speed"
                data[index] = "\n".join(lines) + "\n"
        return data

    def _change_flow(self, data:str)->str:
        new_flowrate_0 = "M221 S" + str(self.getSettingValueByKey("c_flowrate_t0")) + " ; Change_at_Layer: Alter Flow Rate"
        reset_flowrate_0 = "M221 S100 ; Change_at_Layer: Reset Flow Rate"
        if self.extruder_count > 1:
            new_flowrate_1 = "M221 S" + str(self.getSettingValueByKey("c_flowrate_t1")) + " ; Change_at_Layer: Alter Flow Rate"
        else:
            new_flowrate_1 = ""
        # For single extruder
        if self.extruder_count == 1:
            lines = data[self.start_index].splitlines()
            lines[0] += new_flowrate_0
            data[self.start_index] = "\n".join(lines) + "\n"
            lines = data[self.end_index].splitlines()
            lines[len(lines) - 2] += reset_flowrate_0
            data[self.end_index] = "\n".join(lines) + "\n"
        # For dual-extruders
        elif self.extruder_count > 1:
            for index, layer in enumerate(data):
                if index < self.start_index:
                    continue
                else:
                    lines = layer.splitlines()
                    for l_index, line in enumerate(lines):
                        if line.startswith("T0"):
                            lines[l_index] = lines[l_index] + "\n" + new_flowrate_0
                            lines[l_index] += " ; Change_at_Layer: Alter Flow Rate"
                        if line.startswith("T1"):
                            lines[l_index] = lines[l_index] + "\n" + new_flowrate_1
                            lines[l_index] += " ; Change_at_Layer: Alter Flow Rate"
                    data[index] = "\n".join(lines) + "\n"
                    if index == self.end_index:
                        lines = data[index].splitlines()
                        lines[len(lines) - 2] += "\nM221 S100 ; Change_at_Layer: Reset Flow Rate"
                        data[index] = "\n".join(lines) + "\n"
                        break
                if index > self.end_index:
                    break
        return data

    def _change_bed_temp(self, data:str)->str:
        new_bed_temp = self.getSettingValueByKey("d_bedTemp")
        if self.start_index == 2:
            if "M140 S" in data[2]:
                data[2] = re.sub("M140 S", ";M140 S", data[2])
            if "M140 S" in data[3]:
                data[3] = re.sub("M140 S", ";M140 S", data[3])
        lines = data[self.start_index].splitlines()
        lines[0] += "\nM140 S" + str(new_bed_temp) + " ; Change_at_Layer: Change Bed Temperature"
        data[self.start_index] = "\n".join(lines) + "\n"
        lines = data[self.end_index].splitlines()
        lines[len(lines) - 2] += "\nM140 S" + str(self.orig_bed_temp) + " ; Change_at_Layer: Reset Bed Temperature"
        data[self.end_index] = "\n".join(lines) + "\n"
        return data

    def _change_bv_temp(self, data:str)->str:
        if not self.heated_build_volume:
            return data
        new_bv_temp = self.getSettingValueByKey("e_build_volume_temperature")
        lines = data[self.start_index].splitlines()
        lines[0] += "\nM141 S" + str(new_bv_temp) + " ; Change_at_Layer: Change Build Volume Temperature"
        data[self.start_index] = "\n".join(lines) + "\n"
        lines = data[self.end_index].splitlines()
        lines[len(lines) - 2] += "\nM141 S" + str(self.orig_bv_temp) + " ; Change_at_Layer: Reset Build Volume Temperature"
        data[self.end_index] = "\n".join(lines) + "\n"
        return data

    def _change_hotend_temp(self, data:str)->str:
        curaApp = Application.getInstance().getGlobalContainerStack()
        extruder = curaApp.extruderList
        new_hotend_temp_0 = self.getSettingValueByKey("f_extruder_temperature_t0")
        orig_hot_end_temp_0 = extruder[0].getProperty("material_print_temperature", "value")
        orig_standby_temp_0 = int(extruder[0].getProperty("material_standby_temperature", "value"))
        # Start with single extruder machines
        if self.extruder_count == 1:
            if self.start_index == 2:
                if "M104 S" in data[2]:
                    data[2] = re.sub("M104 S", ";M104 S", data[2])
                if "M104 S" in data[3]:
                    data[3] = re.sub("M104 S", ";M104 S", data[3])
            # Add the temperature change at the beginning of the start layer
            lines = data[self.start_index].splitlines()
            for index, line in enumerate(lines):
                lines[0] += "\n" + "M104 S" + str(new_hotend_temp_0) + " ; Change_at_Layer: Change Nozzle Temperature"
                data[self.start_index] = "\n".join(lines) + "\n"
                break
            # Revert the temperature to the Cura setting at the end of the end layer
            lines = data[self.end_index].splitlines()
            for index, line in enumerate(lines):
                lines[len(lines) - 2] += "\n" + "M104 S" + str(orig_hot_end_temp_0) + " ; Change_at_Layer: Reset Nozzle Temperature"
                data[self.end_index] = "\n".join(lines) + "\n"
                break
        # Multi-extruder machines
        elif self.extruder_count > 1:
            active_tool = "T0"
            new_hotend_temp_1 = self.getSettingValueByKey("f_extruder_temperature_t1")
            orig_hot_end_temp_1 = extruder[1].getProperty("material_print_temperature", "value")
            orig_standby_temp_1 = int(extruder[1].getProperty("material_standby_temperature", "value"))
            # Track the tool number
            for index, layer in enumerate(data):
                if index < self.start_index:
                    lines = layer.splitlines()
                    for line in lines:
                        if line.startswith("T0"):
                            active_tool = "T0"
                        if line.startswith("T1"):
                            active_tool = "T1"
                # At the start layer start making the changes
                elif index >= self.start_index:
                    lines = layer.splitlines()
                    for l_index, line in enumerate(lines):
                        # Continue to track the tool number
                        if line.startswith("T0"):
                            active_tool = "T0"
                        if line.startswith("T1"):
                            active_tool = "T1"
                        # Make the temperature changes to lines that are not standby temperature lines
                        if line.startswith(("M104", "M109")):
                            if "T0" in line:
                                temp = int(self.getValue(line, "S"))
                                if temp != orig_standby_temp_0 and temp != 0:
                                    lines[l_index] = line.replace("S" + str(temp), "S" + str(new_hotend_temp_0) + " ; Change_at_Layer: Alter temperature")
                            if "T1" in line:
                                temp = self.getValue(line, "S")
                                if temp != orig_standby_temp_1 and temp != 0:
                                    lines[l_index] = line.replace("S" + str(temp), "S" + str(new_hotend_temp_1) + " ; Change_at_Layer: Alter temperature")
                            if not "T0" in line and not "T1" in line:
                                if active_tool == "T0":
                                    temp = self.getValue(line, "S")
                                    if temp != orig_standby_temp_0 and temp != 0:
                                        lines[l_index] = line.replace("S" + str(temp), "S" + str(new_hotend_temp_0) + " ; Change_at_Layer: Alter temperature")
                                elif active_tool == "T1":
                                    temp = self.getValue(line, "S")
                                    if temp != orig_standby_temp_1 and temp != 0:
                                        lines[l_index] = line.replace("S" + str(temp), "S" + str(new_hotend_temp_1) + " ; Change_at_Layer: Alter temperature")
                    data[index] = "\n".join(lines) + "\n"
                if index == self.end_index:
                    lines = data[self.end_index].splitlines()
                    if active_tool == 0:
                        lines[len(lines) - 2] += "\nM104 T0 S" + str(orig_hot_end_temp_0) + " ; Original Temperature T0"
                    if active_tool == 1:
                        lines[len(lines) - 2] += "\nM104 T1 S" + str(orig_hot_end_temp_1) + " ; Original Temperature T1"
                    data[self.end_index] = "\n".join(lines) + "\n"
                    break
        return data

    def _change_retract(self, data:str)->str:
        curaApp = Application.getInstance().getGlobalContainerStack()
        extruder = curaApp.extruderList
        retract_enabled = extruder[0].getProperty("retraction_enable", "value")
        if not retract_enabled:
            return
        firmware_retraction = bool(curaApp.getProperty("machine_firmware_retract", "value"))
        relative_extrusion = bool(curaApp.getProperty("relative_extrusion", "value"))
        speed_retract_0 = int(extruder[0].getProperty("retraction_speed", "value") * 60)
        retract_amt_0 = extruder[0].getProperty("retraction_amount", "value")
        change_retract_amt = self.getSettingValueByKey("g_change_retract_amount")
        change_retract_speed = self.getSettingValueByKey("g_change_retract_speed")
        new_retract_speed = int(self.getSettingValueByKey("g_retract_speed") * 60)
        new_retract_amt = self.getSettingValueByKey("g_retract_amount")

        if firmware_retraction:
            lines = data[self.start_index].splitlines()
            firmware_start_str = "\nM207"
            if change_retract_speed:
                firmware_start_str += " F" + str(new_retract_speed)
            if change_retract_amt:
                firmware_start_str += " S" + str(new_retract_amt)
            firmware_start_str += f" ; Change_at_Layer: Alter Firmware Retract\nM208 S{new_retract_speed} ; Change_at_Layer: Alter Firmware Prime"
            lines[0] += firmware_start_str
            data[self.start_index] = "\n".join(lines) + "\n"
            lines = data[self.end_index].splitlines()
            firmware_reset = f"M207 F{speed_retract_0} S{retract_amt_0} ; Change_at_Layer: Reset Firmware Retract\nM208 S{speed_retract_0} ; Change_at_Layer: Reset Firmware Prime"
            if len(lines) < 2:
                lines.append(firmware_reset)
            else:
                lines[len(lines) - 1] += "\n" + firmware_reset
            data[self.end_index] = "\n".join(lines) + "\n"
            return data

        if not firmware_retraction:
            prev_e = 0
            cur_e = 0
            is_retracted = False
            for num in range(1, self.start_index - 1):
                lines = data[num].splitlines()
                for line in lines:
                    if " E" in line:
                        cur_e = self.getValue(line, "E")
                        prev_e = cur_e
            for num in range(self.start_index, self.end_index):
                lines = data[num].splitlines()
                for index, line in enumerate(lines):
                    if line == "G92 E0":
                        cur_e = 0
                        prev_e = 0
                        continue
                    if " E" in line and self.getValue(line, "E") is not None:
                        cur_e = self.getValue(line, "E")
                    if cur_e >= prev_e and " X" in line and " Y" in line:
                        prev_e = cur_e
                        is_retracted = False
                        continue
                    if " F" in line and " E" in line and not " X" in line and not " Z" in line:
                        cur_speed = self.getValue(line, "F")
                        if cur_e < prev_e:
                            is_retracted = True
                            new_e = prev_e - new_retract_amt
                            if not relative_extrusion:
                                if change_retract_amt:
                                    lines[index] = lines[index].replace("E" + str(cur_e), "E" + str(new_e))
                                    prev_e = new_e
                                if change_retract_speed:
                                    lines[index] = lines[index].replace("F" + str(cur_speed), "F" + str(new_retract_speed))
                            elif relative_extrusion:
                                if change_retract_amt:
                                    lines[index] = lines[index].replace("E" + str(cur_e), "E-" + str(new_retract_amt))
                                    prev_e = 0
                                if change_retract_speed:
                                    lines[index] = lines[index].replace("F" + str(cur_speed), "F" + str(new_retract_speed))
                            lines[index] += " ; Change_at_Layer: Alter retract"
                        else:
                            # Prime line
                            if change_retract_speed:
                                lines[index] = lines[index].replace("F" + str(cur_speed), "F" + str(new_retract_speed))
                                prev_e = cur_e
                            if relative_extrusion:
                                if change_retract_amt:
                                    lines[index] = lines[index].replace("E" + str(cur_e), "E" + str(new_retract_amt))
                                prev_e = 0
                            lines[index] += " ; Change_at_Layer: Alter retract"
                            is_retracted = False
                data[num] = "\n".join(lines) + "\n"
            # If the changes end before the last layer and the filament is retracted, then adjust the first prime of the next layer so it doesn't blob.
            if is_retracted and self.getSettingValueByKey("a_end_layer") != -1:
                layer = data[self.end_index]
                lines = layer.splitlines()
                for index, line in enumerate(lines):
                    if " X" in line and " Y" in line and " E" in line:
                        break
                    if " F" in line and " E" in line and not " X" in line and not " Z" in line:
                        cur_e = self.getValue(line, "E")
                        if not relative_extrusion:
                            new_e = prev_e + new_retract_amt
                            if change_retract_amt:
                                lines[index] = lines[index].replace("E" + str(cur_e), "E" + str(new_e)) + " ; Change_at_Layer: Alter retract"
                                break
                        elif relative_extrusion:
                            if change_retract_amt:
                                lines[index] = lines[index].replace("E" + str(cur_e), "E" + str(new_retract_amt)) + " ; Change_at_Layer: Alter retract"
                                break
                data[self.end_index] = "\n".join(lines) + "\n"
        return data

    def _format_lines(self, temp_data: str) -> str:
        for l_index, layer in enumerate(temp_data):
            lines = layer.split("\n")
            for index, line in enumerate(lines):
                if "; Change_at_Layer:" in line:
                    lines[index] = lines[index].split(";")[0] + ";" + ("-" * (40 - len(lines[index].split(";")[0]))) + lines[index].split(";")[1]
            temp_data[l_index] = "\n".join(lines)
        return temp_data