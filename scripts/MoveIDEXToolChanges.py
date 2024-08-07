# Copyright (c) August 2024 GregValiant (Greg Foresi)
#
#  Prime Tower must be enabled.
# The printer must be a multiple extruder machine.

from ..Script import Script
from UM.Application import Application
from UM.Message import Message

class MoveIDEXToolChanges(Script):

    def getSettingDataString(self):
        return """{
            "name": "Move IDEX Tool Changes to Prime Tower",
            "key": "MoveIDEXToolChanges",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "move_tool_changes":
                {
                    "label": "Move Tool Changes",
                    "description": "Move the tool changes from above the print, to above the Prime Tower.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": true
                }
            }
        }"""

    def execute(self, data):
        if not bool(Application.getInstance().getGlobalContainerStack().getProperty("prime_tower_enable", "value")):
            Message(title = "[Move Tool Changes]", text = "Did not run because 'Prime Tower' is not enabled.").show()
            return data
        machine_extruder_count = int(Application.getInstance().getGlobalContainerStack().getProperty("machine_extruder_count", "value"))
        if machine_extruder_count < 2:
            return data
        start_index = 2
        for num in range(2, len(data) - 1):
            if ";LAYER:0" in data[num]:
                start_index = num + 1
                break
        pull_lines = ""
        if self.getSettingValueByKey("move_tool_changes"):
            for num in range(start_index, len(data)-1):
                if not ";TYPE:PRIME-TOWER" in data[num]:
                    continue
                lines = data[num].split("\n")
                modified_data = ""
                for index, line in enumerate(lines):
                    if line.startswith("M135") or line.startswith("T"):
                        pull_lines = ""
                        p_index = index
                        # Pull out the lines before the travel moves to the prime tower
                        while not lines[p_index].startswith(";") and not " Z" in lines[p_index]:
                            pull_lines += "\n" + lines[p_index]
                            lines.pop(p_index)
                        if lines[p_index].startswith("G0 F") and " Z" in lines[p_index]:
                            modified_data += lines[p_index] + "\n"
                            continue
                    # For situations where there is no MESH:NONMESH line
                        if lines[p_index].startswith(";TYPE:") and pull_lines != "":
                            lines[p_index] += pull_lines
                            modified_data += lines[p_index] + "\n"
                        continue
                    # Add the pulled_lines back in after TYPE:PRIME-TOWER
                    if line.startswith(";TYPE:PRIME-TOWER") and pull_lines != "":
                        lines[index] += pull_lines
                        pull_lines = ""
                    modified_data += lines[index] + "\n"
                data[num] = modified_data[:-1]
        return data