# GregValiant (Greg Foresi) October of 2024
# Combine Z-hops with retractions and/or primes.  The 'Layer Range' is user defined.
#
# Note:
#   This script is NOT compatible with "One at a Time" mode.
#   For multi-extruder machines the same settings (Extruder #1) are used for all extruders.

from UM.Application import Application
from ..Script import Script
import re
from UM.Message import Message
import math

class CombineZhopsAndRetracts(Script):

    def getSettingDataString(self):
        return """{
            "name": "Combine Z-Hops and Retracts",
            "key": "CombineZhopsAndRetracts",
            "metadata": {},
            "version": 2,
            "settings": {
                "zhop_combine_enabled": {
                    "label": "Enable script",
                    "description": "Enables the script so it will run.  NOTE:  This script is slow running because it must check the length of all travel moves in your layer range.  Large prints may take more than 45 seconds to process.  NOTE: If running 'Purge Lines and Unload' that script should run after this one.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": true
                },
                "start_layer": {
                    "label": "Start Layer",
                    "description": "Layer number to start the changes at.  Use the Cura preview layer numbers.  The changes will start at the start of the layer.",
                    "unit": "Lay# ",
                    "type": "int",
                    "default_value": 1,
                    "minimum_value": "1",
                    "enabled": "zhop_combine_enabled"
                },
                "end_layer": {
                    "label": "End Layer",
                    "description": "Enter '-1' to indicate the top layer, or enter a specific Layer number from the Cura preview.  The changes will end at the end of this layer.",
                    "unit": "Lay# ",
                    "type": "int",
                    "default_value": -1,
                    "minimum_value": "-1",
                    "enabled": "zhop_combine_enabled"
                },
                "ret_combine": {
                    "label": "Retract Combine",
                    "description": "Check to combine retracts with their hops.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": "zhop_combine_enabled"
                },
                "prime_combine": {
                    "label": "Prime Combine",
                    "description": "Check to combine primes with their hops.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": "zhop_combine_enabled"
                }
            }
        }"""

    def execute(self, data):
        # Exit if the script isn't enabled
        if not bool(self.getSettingValueByKey("zhop_combine_enabled")):
            return data
        mycura = Application.getInstance().getGlobalContainerStack()
        # Exit if the Print Sequence is One-at-a-Time
        if mycura.getProperty("print_sequence", "value") == "one_at_a_time":
            Message(title = "[Combine Z-Hops and Retracts]", text = "Is not compatible with 'One at a Time' print sequence.").show()
            data[0] += ";  [Combine Z-Hops and Retracts] did not run because One at a Time is enabled"
            return data
        extruder = mycura.extruderList
        speed_zhop = extruder[0].getProperty("speed_z_hop", "value") * 60
        speed_travel = extruder[0].getProperty("speed_travel", "value") * 60
        retraction_enabled = extruder[0].getProperty("retraction_enable", "value")
        start_layer = self.getSettingValueByKey("start_layer")
        end_layer = self.getSettingValueByKey("end_layer")
        ret_combine = self.getSettingValueByKey("ret_combine")
        prime_combine = self.getSettingValueByKey("prime_combine")
        if not ret_combine and not prime_combine:
            Message(title = "[Combine Z-Hops and Retracts]", text = "Did not run because neither Retract Combine nor Prime Combine are checked.").show()
            return data
        # Get the indexes for the start and end layers
        for num in range(1, len(data) - 1):
            if ";LAYER:" + str(start_layer - 1) + "\n" in data[num]:
                start_index = num
                break
        if end_layer == -1:
            if retraction_enabled:
                end_index = len(data) - 3
            else:
                end_index = len(data) - 2
        elif end_layer != -1:
            for num in range(1, len(data) - 1):
                if ";LAYER:" + str(end_layer - 1) + "\n" in data[num]:
                    end_layer = data[num].splitlines()[0].split(":")[1]
                    end_index = num
                    break
        # Make the changes
        for num in range(start_index, end_index + 1):
            lines = data[num].splitlines()
            for index, line in enumerate(lines):
                # look for hop lines
                if re.search("G1 F(\d\d.) Z", line) is not None:
                    # for retraction
                    if re.search("G1 F(\d\d.*) E", lines[index-1]) is not None and ret_combine:
                        z_hgt = line.split("Z")[1]
                        lines[index-1] += " Z" + str(z_hgt) + "           ; Combine Retract"
                        lines.pop(index)
                        # for primes
                    if re.search("G1 F(\d\d.*) E", lines[index+1]) is not None and prime_combine:
                        z_hgt = line.split("Z")[1]
                        lines[index+1] += " Z" + str(z_hgt) + "           ; Combine Prime"
                        lines.pop(index)
            data[num] = "\n".join(lines)
        return data