# Authored by: GregValiant (Greg Foresi) 6/24
# The temperatures in Cura must be set to 1/2 the required temperature of the material printing values.  This will affect:
#    - Print Temp
#    - Intial Layer Print Temp
#    - Initial Layer Print Temp
#    - Final Print Temp
#    - Small Layer Print Temp
#    - Standby Temp
#    - Default Print Temp
# Other affected settings (some may be hidden):
#    - Break Preparation Temperature
#    - Break Temperature
# This script will go through the gcode and double all the temperature values in M104 S, M109 S, and M109 R lines.
# Conventional dual extruder printers are supported and the user can select the tool to be affected.  Printers with mixing hot ends (shared heater and nozzle) are not supported.

from ..Script import Script
from UM.Application import Application
from UM.Message import Message

class HighTempPrinting(Script):

    def initialize(self) -> None:
        super().initialize()
        # Get the extruder count and enable the 'Extruder Select' option if it is a multi-extruder printer.
        mycura = Application.getInstance().getGlobalContainerStack()
        machine_extruder_count = int(mycura.getProperty("machine_extruder_count", "value"))

        if machine_extruder_count > 1:
            self._instance.setProperty("extruder_check", "value", True)
        else:
            self._instance.setProperty("extruder_check", "value", False)

    def getSettingDataString(self):
        return """{
            "name": "High Temperature Printing",
            "key": "HighTempPrinting",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "enable_temp_change":
                {
                    "label": "Enable 2X Hot End Temps",
                    "description": "When enabled for a single extruder printer, all the Hot End temperature values in the gcode will be doubled.  EX: 225° in Cura 'Printing Temperature' will become 450° in the gcode.  This is an override to the 365° limit in Cura.  For multi-extruder printers, you may select the extruder to alter the temperatures for.  Printers with mixing hot ends (extruders share heater and extruders share nozzle) are not supported.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": true
                },
                "extruder_select":
                {
                    "label": "Which extruders should be changed",
                    "description": "Select the Tool that will have double temperatures.",
                    "type": "enum",
                    "options": {
                        "t0_only": "T0 only",
                        "t1_only": "T1 only",
                        "both_extruders": "Both T0 and T1"
                        },
                    "default_value": "t0_only",
                    "enabled": "enable_temp_change and extruder_check"
                },
                "extruder_check":
                {
                    "label": "Hidden setting",
                    "description": "This setting remains hidden.  It enables the 'extruder_select' option if the extruder count is 2.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": false
                }
            }
        }"""

    def execute(self, data):
        # Exit if the script is not enabled
        if not bool(self.getSettingValueByKey("enable_temp_change")):
            return data
        mycura = Application.getInstance().getGlobalContainerStack()
        machine_extruder_count = int(mycura.getProperty("machine_extruder_count", "value"))
        machine_extruders_enabled_count = int(mycura.getProperty("extruders_enabled_count", "value"))
        # Exit if the printer has more than 2 extruders
        if machine_extruder_count > 2:
            Message(title = "[High Temperature Printing]", text = "Did not run because the Extruder Count > 2").show()
            return data
        # Exit if the printer has a mixing hot end
        shared_heater = bool(mycura.getProperty("machine_extruders_share_heater", "value"))
        shared_nozzle = bool(mycura.getProperty("machine_extruders_share_nozzle", "value"))
        if shared_heater or shared_nozzle:
            Message(title = "[High Temperature Printing]", text = "Did not run because it is not compatible with mixing hot ends.").show()
            return data

        # If only one extruder is enabled then treat it as a single extruder printer and change all the temperatures
        if machine_extruders_enabled_count == 1:
            machine_extruder_count = 1

        # The Tool to be adjusted deterimines which function to go through
        which_tool = "0"
        if machine_extruder_count == 2:
            if self.getSettingValueByKey("extruder_select") == "t1_only":
                which_tool = "1"
            elif self.getSettingValueByKey("extruder_select") == "both_extruders":
                which_tool = "Both"
        if machine_extruder_count == 1 or (machine_extruder_count == 2 and which_tool == "Both"):
            data = self._all_changes(data)
            return data
        elif machine_extruder_count == 2 and which_tool != "Both":
            data = self._tool_changes(data, which_tool)
            return data

    # Go though this if all the temperatures are being changed
    def _all_changes(self, alt_data: str) -> str:
        max_temp = 0
        new_temp = 0
        for num in range(1, len(alt_data)-1):
            if "M104" in alt_data[num] or "M109" in alt_data[num]:
                lines = alt_data[num].split("\n")
                for index, line in enumerate(lines):
                    if line.startswith("M104 S") or line.startswith("M109 S") or line.startswith("M104 T") or line.startswith("M109 T"):
                        cur_temp = int(self.getValue(line, "S"))
                        new_temp = cur_temp * 2
                        lines[index] = line.replace("S" + str(cur_temp), "S" + str(new_temp), 1)
                    if line.startswith("M109 R"):
                        cur_temp = int(self.getValue(line, "R"))
                        new_temp = cur_temp * 2
                        lines[index] = line.replace("R" + str(cur_temp), "R" + str(new_temp), 1)
                # Track the highest temperture so the user can be informed via a message
                if new_temp > max_temp:
                    max_temp = new_temp
                alt_data[num] = "\n".join(lines)
        alt_data[1] = ";  [HighTempPrinting] The print temperatures have been overridden by post processing.  The new print temperatures are as high as " + str(max_temp) + "°.\n" + alt_data[1]
        msg_text = "The post processor 'Cura High Temp Override' is enabled. All the temperatures in the Cura settings have been doubled in the Gcode.  The new print temperatures are as high as " + str(max_temp) + "°.  Your printer and the material must be capable of handling the high temperatures.  It is up to the user to determine the suitablility of High Temperature Printing."
        Message(title = "HIGH TEMP PRINT WARNING", text = msg_text).show()
        return alt_data

    # Go though this one if the temperature changes are for a specific extruder only
    def _tool_changes(self, alt_data: str, tool_num: str) -> str:
        active_tool = "0"
        max_temp = 0
        new_temp = 0
        for num in range(1, len(alt_data)-1):
            lines = alt_data[num].split("\n")
            # Track the active tool number
            for index, line in enumerate(lines):
                if line.startswith("T0"):
                    active_tool = "0"
                elif line.startswith("T1"):
                    active_tool = "1"
                # Change the M104 and M109 lines of the active tool when it is equal to tool_num
                if tool_num == active_tool:
                    if line.startswith("M104 S") or line.startswith("M109 S"):
                        cur_temp = int(self.getValue(line, "S"))
                        new_temp = cur_temp * 2
                        lines[index] = line.replace("S" + str(cur_temp), "S" + str(new_temp), 1)
                    if line.startswith("M109 R"):
                        cur_temp = int(self.getValue(line, "R"))
                        new_temp = cur_temp * 2
                        lines[index] = line.replace("R" + str(cur_temp), "R" + str(new_temp), 1)
                # Change the heat up and cool down lines when the tool_num is inactive
                else:
                    if line.startswith("M104 T" + tool_num) or line.startswith("M109 T" + tool_num):
                        cur_temp = int(self.getValue(line, "S"))
                        new_temp = cur_temp * 2
                        lines[index] = line.replace("S" + str(cur_temp), "S" + str(new_temp), 1)
                # Cura doesn't add 'M109 T R' lines for the inactive tool so that situation is ignored
                # Track the highest temperture so the user can be informed via a message
                if new_temp > max_temp:
                    max_temp = new_temp
                alt_data[num] = "\n".join(lines)
        alt_data[1] = ";  [HighTempPrinting] The print temperatures for Tool 'T" + tool_num + "' have been overridden by post processing.  The new print temperatures are as high as " + str(max_temp) + "°.\n" + alt_data[1]
        msg_text = "The post processor 'High Temperature Printing' is enabled. All the temperatures in the Cura settings for Tool 'T" + tool_num + "' have been doubled in the Gcode.  The new print temperatures are as high as " + str(max_temp) + "°.  Your printer and the material must be capable of handling the high temperatures.  It is up to the user to determine the suitablility of High Temperature Printing."
        Message(title = "HIGH TEMP PRINT WARNING", text = msg_text).show()
        return alt_data

