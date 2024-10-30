# GregValiant (Greg Foresi) July of 2024
# Insert Z-hops for travel moves regardless of retraction.  The 'Layer Range', 'Minimum Travel Distance' and the 'Hop-Height' are user defined.
# This script is compatible with Z-hops enabled in Cura.  If Z-hops are enabled: There will occasionally be a hop on top of a hop, but the 'resume Z height' will be correct.
# It is not necessary to have "retractions" enabled.
# This script does NOT add any retractions.
#
# Note:
#   This script is NOT compatible with "One at a Time" mode.
#   For multi-extruder machines the same settings (Extruder #1) are used for all extruders.
#   This is a slow running post processor as it must check the cummulative distances of all travel moves (G0 moves) in the range of layers.

from UM.Application import Application
from ..Script import Script
import re
from UM.Message import Message
import math

class ZhopOnTravel(Script):

    def getSettingDataString(self):
        return """{
            "name": "Z-Hops for Travel (No Retract)",
            "key": "ZhopOnTravel",
            "metadata": {},
            "version": 2,
            "settings": {
                "zhop_travel_enabled": {
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
                    "enabled": "zhop_travel_enabled"
                },
                "end_layer": {
                    "label": "End Layer",
                    "description": "Enter '-1' to indicate the top layer, or enter a specific Layer number from the Cura preview.  The changes will end at the end of this layer.",
                    "unit": "Lay# ",
                    "type": "int",
                    "default_value": -1,
                    "minimum_value": "-1",
                    "enabled": "zhop_travel_enabled"
                },
                "hop_height": {
                    "label": "Z-Hop Height",
                    "description": "I refuse to provide a description for this.",
                    "unit": "mm  ",
                    "type": "float",
                    "default_value": 0.5,
                    "minimum_value": "0",
                    "maximum_value_warning": 5,
                    "enabled": "zhop_travel_enabled"
                },
                "min_travel_dist": {
                    "label": "Minimum Travel Distance",
                    "description": "Travel distances longer than this will cause a Z-Hop to occur.  This distance should be at least a bit longer than your 'Retraction Minimum Travel' to insure that there is a retraction before the travel move and subsequent Z-hop.",
                    "unit": "mm  ",
                    "type": "int",
                    "default_value": 10,
                    "minimum_value": "1",
                    "maximum_value": "200",
                    "enabled": "zhop_travel_enabled"
                }
            }
        }"""

    def execute(self, data):
        # Exit if the script isn't enabled
        if not bool(self.getSettingValueByKey("zhop_travel_enabled")):
            return data
        mycura = Application.getInstance().getGlobalContainerStack()
        # Exit if the Print Sequence is One-at-a-Time
        if mycura.getProperty("print_sequence", "value") == "one_at_a_time":
            Message(title = "[ZHop On Travel]", text = "Is not compatible with 'One at a Time' print sequence.").show()
            data[0] += ";  [ZHop On Travel] did not run because One at a Time is enabled"
            return data
        # Define some variables
        extruder = mycura.extruderList
        speed_zhop = extruder[0].getProperty("speed_z_hop", "value") * 60
        speed_travel = extruder[0].getProperty("speed_travel", "value") * 60
        retraction_enabled = extruder[0].getProperty("retraction_enable", "value")
        init_layer_height = float(mycura.getProperty("layer_height_0", "value"))
        min_travel_dist = self.getSettingValueByKey("min_travel_dist")
        hop_height = round(self.getSettingValueByKey("hop_height"),2)
        start_layer = self.getSettingValueByKey("start_layer")
        end_layer = self.getSettingValueByKey("end_layer")
        # Get the indexes for the start and end layers
        start_index = 2
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
        cur_z = init_layer_height
        # Track the Z up to the starting point
        for num in range(1, start_index):
            lines = data[num].splitlines()
            for line in lines:
                if " Z" in line and self.getValue(line, "Z") is not None:
                    cur_z = self.getValue(line, "Z")
        cur_x = 0.0
        cur_y = 0.0
        prev_x = 0.0
        prev_y = 0.0
        hop_start = 0
        hop_end = 0
        cmd_list = ["G0 ", "G1 ", "G2 ", "G3 "]
        # Make the insertions
        for num in range(start_index, end_index + 1):
            lines = data[num].splitlines()
            for index, line in enumerate(lines):
                # Get the XYZ values from movement commands
                if line[0:3] in cmd_list:
                    if " X" in line and self.getValue(line, "X") is not None:
                        prev_x = cur_x
                        cur_x = self.getValue(line, "X")
                    if " Y" in line and self.getValue(line, "Y") is not None:
                        prev_y = cur_y
                        cur_y = self.getValue(line, "Y")
                    if " Z" in line and self.getValue(line, "Z") is not None:
                        cur_z = self.getValue(line, "Z")
                # All travel moves are checked for their length
                if line.startswith("G0 ") and hop_start == 0:
                    hop_indexes = self._total_travel_length(index, lines, cur_x, cur_y, prev_x, prev_y)
                    hop_start = int(hop_indexes[0])
                    hop_end = int(hop_indexes[1])
                    if hop_start > 0:
                        # For any lines that are XYZ moves right before layer change
                        if lines[index] .startswith("G0") and " Z" in line:
                            lines[index] = lines[index].replace("Z" + str(cur_z), "Z" + str(cur_z + hop_height))
                        # Format the line
                        zhop_line = f"G0 F{speed_zhop} Z{cur_z + hop_height}"
                        zhop_line = zhop_line + str(" " * (30 - len(zhop_line))) + " ; ZhopOnTravel Up\n"
                        # If there is no 'F' in the next line then add one at the Travel Speed so the z-hop speed doesn't carry over
                        if not " F" in lines[index] and lines[index].startswith("G0"):
                            lines[index] = lines[index].replace("G0", f"G0 F{speed_travel}")                            
                        lines[index] = zhop_line + lines[index]
                # Make the 'Zhop down' insertion at the correct index location (or as soon as practicable after it) and format it
                if hop_end > 0 and index >= hop_end:
                    zhop_line = f"G0 F{speed_zhop} Z{cur_z}"
                    zhop_line = zhop_line + str(" " * (30 - len(zhop_line))) + " ; ZhopOnTravel Down\n"
                    # If there is no 'F' in the next line then add one to reinstate the Travel Speed (so the z-hop speed doesn't carry over through the travel moves)
                    if not " F" in lines[index] and lines[index].startswith("G0"):
                        lines[index] = lines[index].replace("G0", f"G0 F{speed_travel}")             
                    lines[index] = zhop_line + lines[index]
                    hop_end = 0
                    hop_start = 0
            data[num] = "\n".join(lines) + "\n"
        # Message to the user informing them of the number of Z-hops added
        hop_cnt = 0
        try:
            for num in range(start_index, end_index + 1):
                hop_cnt += data[num].count("ZhopOnTravel Up")
            Message(title = "[Z-hop On Travel]", text = str(hop_cnt) + " Z-Hops were added to the file").show()
        except:
            pass
        return data

    def _total_travel_length(self, l_index: int, lines: str, cur_x: float, cur_y: float, prev_x: float, prev_y: float) -> float:
        g_num = l_index
        travel_total = 0.0
        # Total the lengths of each move and compare them to the Minimum Distance for a Z-hop to occur
        while lines[g_num].startswith("G0 "):
            travel_total += self._get_distance(cur_x, cur_y, prev_x, prev_y)
            prev_x = cur_x
            if self.getValue(lines[g_num], "X") is not None:
                cur_x = self.getValue(lines[g_num], "X")
            prev_y = cur_y
            if self.getValue(lines[g_num], "Y") is not None:
                cur_y = self.getValue(lines[g_num], "Y")
            g_num += 1
            if g_num == len(lines):
                break
        if travel_total > self.getSettingValueByKey("min_travel_dist"):
            return l_index, g_num
        else:
            return 0, 0

    def _get_distance(self, cur_x: float, cur_y: float, prev_x: float, prev_y: float) -> float:
        try:
            dist = math.sqrt((prev_x - cur_x)**2 + (prev_y - cur_y)**2)
        except:
            return 0
        return dist
