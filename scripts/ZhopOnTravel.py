# GregValiant (Greg Foresi) July of 2024
# Insert Z-hops for travel moves regardless of retraction.  The 'Layer Range' (or Layer List), 'Minimum Travel Distance' and the 'Hop-Height' are user defined.
# This script is compatible with Z-hops enabled in Cura.  If Z-hops are enabled: There will occasionally be a hop on top of a hop, but the 'resume Z height' will be correct.
# It is not necessary to have "retractions" enabled.  If retractions are disabled in Cura you may elect to have this script add retractions.  The Cura retraction distance and speeds are used.
# The retraction settings for a multi-extruder printer are always taken from Extruder 1.
#
# Compatibility:
# The script is compatible with:  Relative Extrusion, Firmware Retraction, and Extra Prime Amount > 0.
#
# Incompatibility:
#   This script is NOT compatible with "One at a Time" mode.
#
# Please note:
#   This is a slow running post processor as it must check the cummulative distances of all travel moves (G0 moves) in the range of layers.

from UM.Application import Application
from ..Script import Script
import re
from UM.Message import Message
import math

class ZhopOnTravel(Script):

    def getSettingDataString(self):
        return """{
            "name": "Z-Hops for Travel Moves",
            "key": "ZhopOnTravel",
            "metadata": {},
            "version": 2,
            "settings": {
                "zhop_travel_enabled": {
                    "label": "Enable script",
                    "description": "Enables the script so it will run.  NOTE:  This script is slow running because it must check the length of all travel moves in your layer range.  Large prints may take more than 45 seconds to process.  You can search the Gcode for 'Hop up' to locate lines that were added.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": true
                },
                "list_or_range":
                {
                    "label": "Layer List or Range",
                    "description": "Using a list allows you to call out one or more individual layers delimited by commas (Ex: 23,29,35).  A layer range has a start layer and an end layer.",
                    "type": "enum",
                    "options": {
                        "range_of_layers": "Range of Layers",
                        "list_of_layers": "Layer List" },
                    "default_value": "range_of_layers"
                },
                "layers_of_interest":
                {
                    "label": "List of Layers",
                    "description": "Use the Cura preview layer numbers.  Enter 'individual layer' numbers delimited by commas.  Spaces are not allowed.",
                    "type": "str",
                    "default_value": "10,28,31,54",
                    "enabled": "zhop_travel_enabled and list_or_range == 'list_of_layers'"
                },
                "start_layer": {
                    "label": "Start Layer",
                    "description": "Layer number to start the changes at.  Use the Cura preview layer numbers.  The changes will start at the start of the layer.",
                    "unit": "Lay# ",
                    "type": "int",
                    "default_value": 1,
                    "minimum_value": "1",
                    "enabled": "zhop_travel_enabled and list_or_range == 'range_of_layers'"
                },
                "end_layer": {
                    "label": "End Layer",
                    "description": "Enter '-1' to indicate the top layer, or enter a specific Layer number from the Cura preview.  The changes will end at the end of this layer.",
                    "unit": "Lay# ",
                    "type": "int",
                    "default_value": -1,
                    "minimum_value": "-1",
                    "enabled": "zhop_travel_enabled and list_or_range == 'range_of_layers'"
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
                    "description": "Travel distances longer than this will cause a Z-Hop to occur.",
                    "unit": "mm  ",
                    "type": "int",
                    "default_value": 10,
                    "minimum_value": "1",
                    "maximum_value": "200",
                    "enabled": "zhop_travel_enabled"
                },
                "add_retract": {
                    "label": "Add retraction when necessary",
                    "description": "Depending on your travel settings there may not be a retraction prior to a travel move.  When enabled, if there is no retraction prior to an added z-hop, this setting will add a retraction before the Z-hop, and a prime after returning to the working layer height.  If retractions are disabled in Cura this setting is still available and will add retractions based on the Cura settings for Retraction Amount and Retract and Prime Speeds.  All retraction settings are from the settings for 'Extruder 1' regardless of the number of extruders.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "zhop_travel_enabled"
                }
            }
        }"""

    def execute(self, data):
        # Exit if the script isn't enabled
        if not bool(self.getSettingValueByKey("zhop_travel_enabled")):
            return data
        curaApp = Application.getInstance().getGlobalContainerStack()
        # Exit if the Print Sequence is One-at-a-Time
        if curaApp.getProperty("print_sequence", "value") == "one_at_a_time":
            Message(title = "[ZHop On Travel]", text = "Is not compatible with 'One at a Time' print sequence.").show()
            data[0] += ";  [ZHop On Travel] did not run because One at a Time is enabled"
            return data

        # Define some variables
        extruder = curaApp.extruderList
        speed_zhop = extruder[0].getProperty("speed_z_hop", "value") * 60
        speed_travel = extruder[0].getProperty("speed_travel", "value") * 60
        retraction_enabled = extruder[0].getProperty("retraction_enable", "value")
        extra_prime_vol = extruder[0].getProperty("retraction_extra_prime_amount", "value")
        retraction_amount = extruder[0].getProperty("retraction_amount", "value")
        retract_speed = int(extruder[0].getProperty("retraction_retract_speed", "value")) * 60
        prime_speed = int(extruder[0].getProperty("retraction_prime_speed", "value")) * 60
        firmware_retract = curaApp.getProperty("machine_firmware_retract", "value")
        relative_extrusion = curaApp.getProperty("relative_extrusion", "value")
        self._cur_z = float(curaApp.getProperty("layer_height_0", "value"))
        filament_dia = extruder[0].getProperty("material_diameter", "value")
        extra_prime_dist = extra_prime_vol / (math.pi * (filament_dia / 2)**2)
        self._add_retract = self.getSettingValueByKey("add_retract")
        min_travel_dist = self.getSettingValueByKey("min_travel_dist")
        hop_height = round(self.getSettingValueByKey("hop_height"),2)
        list_or_range = self.getSettingValueByKey("list_or_range")
        layer_list = []
        index_list = []

        if list_or_range == "list_of_layers":
            layer_string = self.getSettingValueByKey("layers_of_interest")
            layer_list = layer_string.split(",")
            for layer in layer_list:
                for num in range(2, len(data) - 1):
                    if ";LAYER:" + str(int(layer) - 1) + "\n" in data[num]:
                        index_list.append(num)
            start_index = index_list[0]
            end_index = index_list[len(index_list) - 1]

        elif list_or_range == "range_of_layers":
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
                    if ";LAYER:" + str(end_layer) + "\n" in data[num]:
                        end_layer = data[num].splitlines()[0].split(":")[1]
                        end_index = num
                        break
            for num in range(start_index, end_index):
                index_list.append(num)

        # Track the Z up to the starting point
        for num in range(1, start_index):
            lines = data[num].splitlines()
            for line in lines:
                if " Z" in line and self.getValue(line, "Z") is not None:
                    self._cur_z = self.getValue(line, "Z")

        # Use 'start_here' to avoid a zhop on the first move of the initial layer because a double-retraction may occur.
        if start_index == 2:
            start_here = False
        else:
            start_here = True

        # Initialize variables
        self._is_retracted = False
        hop_up_lines = ""
        hop_down_lines = ""
        hop_start = 0
        hop_end = 0
        self._cur_x = 0.0
        self._cur_y = 0.0
        self._prev_x = 0.0
        self._prev_y = 0.0
        self._cur_e = 0.0
        self._prev_e = 0.0
        cmd_list = ["G0 ", "G1 ", "G2 ", "G3 "]
        self.reset_type = 0

        # Keep track of the axes locations if the start layer > layer:0
        if start_index > 2:
            self._track_all_axes(data, cmd_list, start_index, relative_extrusion)

        # Make the insertions
        for num in index_list: #for num in range(start_index, end_index + 1):
            lines = data[num].splitlines()
            for index, line in enumerate(lines):
                if num == 2:
                    if line.startswith(";TYPE"):
                        start_here = True
                    if not start_here:
                        continue
                if line.startswith("G92") and " E" in line:
                    self._cur_e = self.getValue(line, "E")
                    self._prev_e = self._cur_e
                    continue
                # Get the XYZ values from movement commands
                if line[0:3] in cmd_list:
                    if " X" in line and self.getValue(line, "X") is not None:
                        self._prev_x = self._cur_x
                        self._cur_x = self.getValue(line, "X")
                    if " Y" in line and self.getValue(line, "Y") is not None:
                        self._prev_y = self._cur_y
                        self._cur_y = self.getValue(line, "Y")
                    if " Z" in line and self.getValue(line, "Z") is not None:
                        self._cur_z = self.getValue(line, "Z")

                # Check whether retractions have occured
                if line[0:3] in ["G1 ", "G2 ", "G3 "] and "X" in line and "Y" in line and "E" in line:
                    self._is_retracted = False
                    self._cur_e = self.getValue(line, "E")
                elif (line.startswith("G1") and "F" in line and "E" in line and not "X" in line or not "Y" in line) or "G10" in line:
                    if self.getValue(line, "E") is not None:
                        self._cur_e = self.getValue(line, "E")
                    if not relative_extrusion:
                        if self._cur_e < self._prev_e or "G10" in line:
                            self._is_retracted = True
                    elif relative_extrusion:
                        if self._cur_e < 0 or "G10" in line:
                            self._is_retracted = True
                if line.startswith(";TYPE"):
                    start_here = True
                if not start_here:
                    continue

                # All travels are checked for their cumulative length
                if line.startswith("G0 ") and hop_start == 0:
                    hop_indexes = self._total_travel_length(index, lines)
                    hop_start = int(hop_indexes[0])
                    hop_end = int(hop_indexes[1])
                    if hop_start > 0:
                        # For any lines that are XYZ moves right before layer change
                        if " Z" in line:
                            lines[index] = lines[index].replace("Z" + str(self._cur_z), "Z" + str(self._cur_z + hop_height))
                        # If there is no 'F' in the next line then add one at the Travel Speed so the z-hop speed doesn't carry over
                        if not " F" in lines[index] and lines[index].startswith("G0"):
                            lines[index] = lines[index].replace("G0", f"G0 F{speed_travel}")
                        if "X" in lines[index - 1] and "Y" in lines[index - 1] and "E" in lines[index - 1]:
                            self._is_retracted = False
                        hop_up_lines = self.get_hop_up_lines(retraction_amount, speed_zhop, retract_speed, prime_speed, extra_prime_dist, firmware_retract, relative_extrusion, hop_height)
                        lines[index] = hop_up_lines + lines[index]

                # Make the 'Zhop down' insertion at the correct index location (or as soon as practicable after it)
                if hop_end > 0 and index >= hop_end:
                    # If there is no 'F' in the next line then add one to reinstate the Travel Speed (so the z-hop speed doesn't carry over through the travel moves)
                    if not " F" in lines[index] and lines[index].startswith("G0"):
                        lines[index] = lines[index].replace("G0", f"G0 F{speed_travel}")
                    hop_down_lines = self.get_hop_down_lines(retraction_amount, speed_zhop, retract_speed, prime_speed, extra_prime_dist, firmware_retract, relative_extrusion, hop_height, lines[index])
                    lines[index] = hop_down_lines + lines[index]
                    self._is_retracted = False
                    hop_end = 0
                    hop_start = 0
                    hop_down = ""
                if line.startswith(";"):
                    continue
                self._prev_e = self._cur_e
            data[num] = "\n".join(lines) + "\n"

        # Message to the user informing them of the number of Z-hops added
        hop_cnt = 0
        retract_cnt = 0
        try:
            for num in range(start_index, end_index + 1):
                hop_cnt += data[num].count("; Hop Up")
                retract_cnt += data[num].count("; Retract")
            msg_txt = str(hop_cnt) + " Z-Hops were added to the file\n"
            if self._add_retract:
                msg_txt += str(retract_cnt) + " Retracts and unretracts were added to the file"
            Message(title = "[Z-hop On Travel]", text = msg_txt).show()
        except:
            pass
        return data

    def _total_travel_length(self, l_index: int, lines: str) -> float:
        g_num = l_index
        travel_total = 0.0
        # Total the lengths of each move and compare them to the Minimum Distance for a Z-hop to occur
        while lines[g_num].startswith("G0 "):
            travel_total += self._get_distance()
            self._prev_x = self._cur_x
            if self.getValue(lines[g_num], "X") is not None:
                self._cur_x = self.getValue(lines[g_num], "X")
            self._prev_y = self._cur_y
            if self.getValue(lines[g_num], "Y") is not None:
                self._cur_y = self.getValue(lines[g_num], "Y")
            g_num += 1
            if g_num == len(lines):
                break
        if travel_total > self.getSettingValueByKey("min_travel_dist"):
            return l_index, g_num
        else:
            return 0, 0

    # Get the distance between the last XY location and the current XY location
    def _get_distance(self) -> float:
        try:
            dist = math.sqrt((self._prev_x - self._cur_x)**2 + (self._prev_y - self._cur_y)**2)
        except:
            return 0
        return dist

    # The retraction figure outer.
    def get_hop_up_lines(self, retraction_amount: float, speed_zhop: str, retract_speed: str, prime_speed: str, extra_prime_dist: float, firmware_retract: bool, relative_extrusion: bool, hop_height: str) -> str:
        hop_retraction = not self._is_retracted
        if not self._add_retract:
            hop_retraction = False
        reset_type = 0 # no other options
        if hop_retraction:
            reset_type += 1
        if firmware_retract and hop_retraction:
            reset_type += 2
        if relative_extrusion and hop_retraction:
            reset_type += 4
        if extra_prime_dist > 0 and hop_retraction:
            reset_type += 8
        up_lines = f"G0 F{speed_zhop} Z{round(self._cur_z + hop_height,2)} ; Hop Up"
        if reset_type in [1, 9] and hop_retraction: # add retract only when necessary
            up_lines = f"G1 F{retract_speed} E{round(self._cur_e - retraction_amount, 5)} ; Retract\n" + up_lines
            self._cur_e = round(self._cur_e - retraction_amount, 5)
        if reset_type in [3, 7] and hop_retraction: # add retract and firmware retract
            up_lines = "G10 ; Retract\n" + up_lines
        if reset_type in [5, 13] and hop_retraction: # add retract and relative extrusion
            up_lines = f"G1 F{retract_speed} E-{retraction_amount} ; Retract\n" + up_lines
            self._cur_e = 0
        if reset_type in [11, 15] and hop_retraction: # add retract, firmware retraction, extra prime
            up_lines = "G10 ; Retract\n" + up_lines

        # Format the added lines for readability
        if "\n" in up_lines: # for lines that include a retraction
            lines = up_lines.split("\n")
            for index, line in enumerate(lines):
                front_txt = lines[index].split(";")[0]
                back_txt = lines[index].split(";")[1]
                lines[index] = front_txt + str(" " * (40 - len(front_txt))) +";" +  back_txt
            up_lines = "\n".join(lines) + "\n"
        else: # for lines without a retraction
            front_txt = up_lines.split(";")[0]
            back_txt = up_lines.split(";")[1]
            up_lines = front_txt + str(" " * (40 - len(front_txt))) +";" +  back_txt + "\n"
        return up_lines

    # The Zhop down may require different kinds of primes depending on the Cura settings.
    def get_hop_down_lines(self, retraction_amount: float, speed_zhop: str, retract_speed: str, prime_speed: str, extra_prime_dist: str, firmware_retract: bool, relative_extrusion: bool, hop_height: str, next_line: str) -> str:
        hop_retraction = not self._is_retracted
        if not self._add_retract:
            hop_retraction = False
        # Base the prime on the combination of Cura settings
        reset_type = 0
        if hop_retraction:
            reset_type += 1
        if firmware_retract and hop_retraction:
            reset_type += 2
        if relative_extrusion and hop_retraction:
            reset_type += 4
        if extra_prime_dist > 0.0 and hop_retraction:
            reset_type += 8
        dn_lines = f"G0 F{speed_zhop} Z{self._cur_z} ; Hop Down"
        # Format the line and return if the retraction option is unchecked
        if "G11" in next_line or re.search("G1 F(\d+\.\d+|\d+) E(-?\d+\.\d+|-?\d+)", next_line) is not None and reset_type == 0:
            front_txt = dn_lines.split(";")[0]
            back_txt = dn_lines.split(";")[1]
            dn_lines = front_txt + str(" " * (40 - len(front_txt))) +";" +  back_txt + "\n"
            self._is_retracted = False
            return dn_lines
        # If the retraction option is checked then determine the required unretract code for the particular combination of Cura settings.
        # Add retract 1
        if reset_type == 1 and hop_retraction:
            dn_lines += f"\nG1 F{prime_speed} E{self._prev_e + retraction_amount} ; Unretract"
        # Add retract 1 + firmware retract 2
        if reset_type == 3 and hop_retraction:
            dn_lines += "\nG11 ; UnRetract"
        # Add retract 1 + relative extrusion 4
        if reset_type == 5 and hop_retraction:
            dn_lines += f"\nG1 F{prime_speed} E{retraction_amount} ; UnRetract"
        # Add retract 1 + firmware retraction 2 + relative extrusion 4
        if reset_type == 7 and hop_retraction:
            dn_lines += f"\nG11 ; Unretract"
        # Add retract 1 + extra prime 8
        if reset_type == 9 and hop_retraction:
            dn_lines += f"\nG92 E{round(self._prev_e - extra_prime_dist,5)} ; Extra prime adjustment"
            dn_lines += f"\nG1 F{prime_speed} E{round(self._prev_e + retraction_amount, 5)} ; UnRetract"
            self._cur_e = round(self._prev_e + retraction_amount, 5)
        # Add retract 1 + firmware retraction 2 + extra prime 8
        if reset_type == 11 and hop_retraction:
            dn_lines += "\nG11 ; UnRetract"
            dn_lines += "\nM83 ; Relative extrusion"
            dn_lines += f"\nG1 F{prime_speed} E{round(extra_prime_dist, 5)} ; Extra prime"
            if not relative_extrusion:
                dn_lines += "\nM82 ; Absolute extrusion"
        # Add retract 1 + relative extrusion 4 + extra prime 8
        if reset_type == 13 and hop_retraction:
            dn_lines += f"\nG1 F{prime_speed} E{round(retraction_amount + extra_prime_dist, 5)} ; Unretract with extra prime"
        # Add retract 1 + firmware retraction 2 + relative extrusion 4 + extra prime 8
        if reset_type == 15 and hop_retraction:
            dn_lines += "\nG11 ; UnRetract"
            dn_lines += f"\nG1 F{prime_speed} E{round(extra_prime_dist, 5)} ; Extra prime"

        # Format the added lines for readability
        if "\n" in dn_lines: # for lines with primes
            lines = dn_lines.split("\n")
            for index, line in enumerate(lines):
                front_txt = lines[index].split(";")[0]
                back_txt = lines[index].split(";")[1]
                lines[index] = front_txt + str(" " * (40 - len(front_txt))) +";" +  back_txt
            dn_lines = "\n".join(lines) + "\n"
        else: # for lines with no prime
            front_txt = dn_lines.split(";")[0]
            back_txt = dn_lines.split(";")[1]
            dn_lines = front_txt + str(" " * (40 - len(front_txt))) +";" +  back_txt + "\n"
        self._is_retracted = False
        return dn_lines

    def _track_all_axes(self, data: str, cmd_list: int, start_index: int, relative_extrusion: bool) -> str:
        for num in range(2, start_index - 1):
            lines = data[num].split("\n")
            for line in lines:
                # Get the XYZ values from movement commands
                if line[0:3] in cmd_list:
                    if " X" in line and self.getValue(line, "X") is not None:
                        self._prev_x = self._cur_x
                        self._cur_x = self.getValue(line, "X")
                    if " Y" in line and self.getValue(line, "Y") is not None:
                        self._prev_y = self._cur_y
                        self._cur_y = self.getValue(line, "Y")
                    if " Z" in line and self.getValue(line, "Z") is not None:
                        self._cur_z = self.getValue(line, "Z")

                # Check whether retractions have occured
                if re.search("G1 X(-?\d+\.\d+|-?\d+) Y(-?\d+\.\d+|-?\d+) E(-?\d+\.\d+|-?\d+)", line) is not None or re.search("G1 F(\d+\.\d+|\d+) X(-?\d+\.\d+|-?\d+) Y(-?\d+\.\d+|-?\d+) E(-?\d+\.\d+|-?\d+)", line) is not None: # G1 X117.3 Y134.268 E1633.06469
                    self._is_retracted = False
                    self._cur_e = self.getValue(line, "E")
                elif re.search("F(\d*\d.*) E(-?\d*\d.*)", line) is not None or "G10" in line:
                    if self.getValue(line, "E") is not None:
                        self._cur_e = self.getValue(line, "E")
                    if not relative_extrusion:
                        if self._cur_e < self._prev_e or "G10" in line:
                            self._is_retracted = True
                    elif relative_extrusion:
                        if self._cur_e < 0 or "G10" in line:
                            self._is_retracted = True
        self._prev_e = self._cur_e
        return
