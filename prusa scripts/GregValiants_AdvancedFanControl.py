# By GregValiant
# This PrusaSlicer/Orca script will:
#    Add fan speed changes 'By Layer' or 'By Feature'

import sys
import os

sourceFile = sys.argv[1]
final_file = open(sourceFile, "r")
lines = final_file.readlines()

def __init__(self, lines, fan_speed_0_to_1, extruder_count, total_layer_count, draft_shield) -> None:
    self.get_prusa_settings()
    self.get_post_settings()
    self.remove_fan_lines()
    self.add_starting_ending_fan()
    self.fan_speed_feature_type()
    self.single_extruder_ByLayer()
    self.dual_extruder_ByLayer()
    self.single_extruder_ByFeature()
    self.dual_extruder_ByFeature()
    self.getSettings_ByFeature()
    self.getSettings_ByLayer()
    lines = final_file.readlines()
    fan_speed_0_to_1
    extruder_count
    total_layer_count
    draft_shield

def main():
    response = "q"
    while not response in ["y", "n"]:
        response = input("\nGreg Valiants [Advanced Fan Control]\nfor Prusa/Orca has started.\n Note: You may run multiple instances of this script.  The first might be for 'By Layer' up to layer 250 and then a second instance can be 'By Feature' and start at layer 250.\n Do you wish to continue?  (y) or (n).\n").lower()
        if response not in ["y", "n"]:
            print("Invalid Response.  Must be 'y' or 'n'.")
            continue
        if response == "n":
            print("Exiting")
            final_file.close()
            exit(0)

    # Get the preliminary settings from both the gcode and the user
    my_settings = get_post_settings()
    remove_m106 = bool(my_settings[0])
    fan_0 = my_settings[1]
    fan_1 = my_settings[2]
    raft_layers = my_settings[3]
    raft_cooling_speed = my_settings[4]
    total_layer_count = my_settings[5]
    nozzle_size_0 = my_settings[6]
    nozzle_size_1 = my_settings[7]
    extruder_count = my_settings[8]
    fan_mode = my_settings[9]
    fan_speed_0_to_1 = my_settings[10]

    # If removing the existing fan lines
    if remove_m106:
        lines = remove_fan_lines()

    # The 4 options: Single Extruder By Layer, Singler extruder By Feature, Dual Extruder By Layer, Dual Extruder By Feature
    if fan_mode == 1:
        # Get the By Feature settings
        feature_settings = getSettings_ByFeature(fan_speed_0_to_1, total_layer_count, extruder_count, fan_0, fan_1, raft_layers)
        feature_type_list = feature_settings[0]
        feature_speed_list = feature_settings[1]
        start_layer = feature_settings[2]
        end_layer = feature_settings[3]
        if extruder_count == 1:
            # Single extruder by feature
            lines = single_extruder_ByFeature(feature_type_list, feature_speed_list, start_layer, end_layer, fan_0)
        elif extruder_count > 1:
            # Dual extruder by feature
            lines = dual_extruder_ByFeature(feature_type_list, feature_speed_list, start_layer, end_layer, fan_0, fan_1)
    elif fan_mode == 2:
        fan_layer_list = getSettings_ByLayer(fan_speed_0_to_1)
        if extruder_count == 1:
            # Single extruder by layer
            lines = single_extruder_ByLayer(fan_layer_list, fan_0)
        elif extruder_count > 1:
            # Dual extruder by layer
            lines = dual_extruder_ByLayer(fan_layer_list, fan_0, fan_1)

    # Make sure the fan is off at the start and end of the print.
    if remove_m106:
        add_m106_S0_lines = add_starting_ending_fan(extruder_count, fan_0, fan_1)

    # Send the file back to Prusa/Orca
    dest_file = open(sourceFile, "w")
    for line in lines:
        dest_file.write(line)
    dest_file.close()
    final_file.close()

def getSettings_ByLayer(fan_speed_0_to_1):
    fan_layers = "r"
    fan_layer_list = []
    while fan_layers == "r":
        fan_layers = input("Enter layers and Fan speeds% as 'layer#/speed%'. For multiple changes delimit the settings with commas. The layer numbers must be in 'Ascending' order.\n (EX: 5/35,25/100,35/0)\n")
        if "," in fan_layers:
            new_layer_list = fan_layers.split(",")
            for fan_cmd in new_layer_list:
                fan_layer_list.append(fan_cmd)
        else:
            fan_layer_list.append(fan_layers)
        # Check for input errors
        err_code = 0
        for fan in fan_layer_list:
            if "/" not in fan or "." in fan_layers:
                err_code = 1
                fan_layers = "r"
                fan_layer_list = []
        if err_code > 0:
            print("There is an error in the fan list.  Each fan speed indicator must be entered as 'lay/speed%'.  If more than one they are separated by commas.\n Try again...")
            fan_layers = "r"
            continue

    # Add the layer list to the gcode as a record of the settings
    lines.insert(2, f";\n;     Fan Changes (LAY / %): {fan_layers}\n")
    # Convert the percentages into PWM or 0to1 as required
    fan_layer_list = fan_layers.split(",")
    for index, fan in enumerate(fan_layer_list):
        if fan_speed_0_to_1:
            fan_layer_list[index] = fan_layer_list[index].split("/")[0] + "/" + str(round(int(fan_layer_list[index].split("/")[1]) * .01, 2))
        else:
            fan_layer_list[index] = fan_layer_list[index].split("/")[0] + "/" + str(round(int(fan_layer_list[index].split("/")[1]) * 2.55))
    return fan_layer_list


def getSettings_ByFeature(fan_speed_0_to_1, total_layer_count, extruder_count, fan_0, fan_1, raft_layers):
    setting_review = "r"
    while setting_review == "r":
        # Get the fan settings for each feature
        start_layer = "a"
        while start_layer == "a":
            try:
                start_layer = int(input("'Start Layer'\n Enter the start layer for Fan Control.  Use the preview numbers.\n"))
            except:
                print("The Start Layer must be an integer > 0.  Try again.")
                start_layer = "a"
                continue

        end_layer = "z"
        while end_layer == "z":
            try:
                end_layer = int(input(f"'End Layer'\n Enter the ending layer number.  Fan Control will continue to the end of this layer.  Use the layer numbers from the preview\n (top layer is: {total_layer_count}).\n"))
                if end_layer > total_layer_count:
                    print(f"The end layer must be an integer less than {total_layer_count}.  Try again.\n")
                    end_layer = "z"
                    continue

            except:
                print(f"The end layer must be an integer less than {total_layer_count}.  Try again.\n")
                end_layer = "z"
                continue

        type_external_perimeter = fan_speed_feature_type("\n'TYPE:External perimeter'\n Enter the Fan speed (0% to 100%) for the outer walls.\n")
        type_perimeter = fan_speed_feature_type("\nTYPE:Perimeter'\n Enter the Fan speed (0% to 100%) for the inner walls.\n")
        type_top_solid_infill = fan_speed_feature_type("\n'TYPE:Top solid infill'\n Enter the Fan speed (0% to 100%) for the top skins.\n")
        type_solid_infill = fan_speed_feature_type("\n'TYPE:Solid infill'\n Enter the Fan speed (0% to 100%) for the bottom and mid skins.\n")
        type_bridge_infill = fan_speed_feature_type("\n'TYPE:Bridge infill'\n Enter the Fan speed (0% to 100%) for the first skins over support.\n")
        type_overhang_perimeter = fan_speed_feature_type("\n'TYPE:Overhang perimeter'\n Enter the Fan speed (0% to 100%) for the walls around overhangs.\n")
        type_internal_infill = fan_speed_feature_type("\n'TYPE:Internal infill'\n Enter the Fan speed (0% to 100%) for the bottom skins.\n")
        type_skirt_brim = fan_speed_feature_type("\n'TYPE:Skirt'\n Enter the Fan speed (0% to 100%) for the skirt/brim/draft shield.\n If your StartLayer is above Layer:1 this would only effect a draft shield.\n")
        type_support = fan_speed_feature_type("\n'TYPE:Support material'\n Enter the Fan speed (0% to 100%) for the support structure.\n")
        type_support_interface = fan_speed_feature_type("\n'TYPE:Support material interface'\n Enter the Fan speed (0% to 100%) for the support interface.\n")
        if end_layer < total_layer_count:
            final_fan_speed = fan_speed_feature_type("\n'Final Fan Speed'\n Your end layer is lower than the print top layer.  Enter the fan speed to use from the End layer to the end of the print.\n Enter the Fan speed (0% to 100%) for the Final Fan Speed.\n")
        else:
            final_fan_speed = 0

        draft_shield = get_prusa_settings(lines)[6]
        input_str = "\nReview your Custom Fan settings:\n\n"
        final_review = "z"
        while final_review == "z":
            if not fan_speed_0_to_1:
                input_str += "Use normal PWM fan scale (0 to 255)\n"
            else:
                input_str += "Use RepRap fan scale (0 to 1)\n"
            input_str += f"Start Layer (model starts on ';Layer:{1 + raft_layers}' in the Gcode): {start_layer}\n"
            input_str += "End Layer in the Gcode...............................: " + str(end_layer) + "\n"
            input_str += "TYPE:External Perimeter..............................: " + str(round(type_external_perimeter / 2.55)) + "%\n"
            input_str += "TYPE:Perimeter.......................................: " + str(round(type_perimeter / 2.55)) + "%\n"
            input_str += "TYPE:Top solid infill................................: " + str(round(type_top_solid_infill / 2.55)) + "%\n"
            input_str += "TYPE:Solid infill....................................: " + str(round(type_solid_infill / 2.55)) + "%\n"
            input_str += "TYPE:Bridge infill...................................: " + str(round(type_bridge_infill / 2.55)) + "%\n"
            input_str += "Type:Overhang perimeter..............................; " + str(round(type_overhang_perimeter / 2.55)) + "%\n"
            input_str += "TYPE:Internal infill.................................: " + str(round(type_internal_infill / 2.55)) + "%\n"
            if start_layer == 1 or draft_shield:
                input_str += "TYPE:Skirt/Brim/Draft Shield.........................: " + str(round(type_skirt_brim / 2.55)) + "%\n"
            input_str += "TYPE:Support.........................................: " + str(round(type_support / 2.55)) + "%\n"
            input_str += "TYPE:Support interface...............................: " + str(round(type_support_interface / 2.55)) + "%\n"
            if end_layer < total_layer_count:
                input_str += "Final Fan speed......................................: " + str(round(final_fan_speed / 2.55)) + "%\n"
            setting_review = input(input_str + "\n<Continue(y)  Redo(r)  Quit(x)> ").lower()
            if setting_review not in ["y", "r", "x"]:
                print("Response must be 'y', 'r', or 'x'.  Try again.\n")
                final_review = "z"
                continue
            else:
                final_review = "c"
            if setting_review == "x":
                response = input("Your response was 'x'.  The script will exit with no fan changes. <Enter>.")
                exit(0)

    feature_type_list = [
        ";TYPE:External perimeter\n",
        ";TYPE:Perimeter\n",
        ";TYPE:Top solid infill\n",
        ";TYPE:Solid infill\n",
        ";TYPE:Bridge infill\n",
        ";TYPE:Overhang perimeter\n",
        ";TYPE:Internal infill\n",
        ";TYPE:Skirt/Brim\n",
        ";TYPE:Support material\n",
        ";TYPE:Support material interface\n"]
    if not fan_speed_0_to_1:
        feature_speed_list = [
            round(type_external_perimeter),
            round(type_perimeter),
            round(type_top_solid_infill),
            round(type_solid_infill),
            round(type_bridge_infill),
            round(type_overhang_perimeter),
            round(type_internal_infill),
            round(type_skirt_brim),
            round(type_support),
            round(type_support_interface),
            round(final_fan_speed)]
    else:
        feature_speed_list = [
            round(type_external_perimeter / 255, 2),
            round(type_perimeter / 255, 2),
            round(type_top_solid_infill / 255, 2),
            round(type_solid_infill / 255, 2),
            round(type_bridge_infill / 255, 2),
            round(type_overhang_perimeter / 255, 2),
            round(type_internal_infill / 255, 2),
            round(type_skirt_brim / 255, 2),
            round(type_support / 255, 2),
            round(type_support_interface / 255, 2),
            round(final_fan_speed / 255, 2)]
    return feature_type_list, feature_speed_list, start_layer, end_layer

def single_extruder_ByLayer(fan_layer_list, fan_0):
    lines.insert(1, "\n;   Post Processed by Greg Valiant's [Advanced Fan Control 'By Layer'] for Prusa/Orca\n")
    for index, line in enumerate(lines):
        if line == ";Layer:1\n":
            start_index = index
            break
    for l_index in range(start_index,len(lines) - 1):
        if ";Layer:" in lines[l_index]:
            layer_number = str(lines[l_index].split(":")[1][:-1])
            # If there is a match for the current layer number make the insertion
            for fan_change in fan_layer_list:
                fan_split = fan_change.split("/")
                layer_nr = int(fan_split[0])
                if layer_number == str(layer_nr):
                    lines[l_index] += f"M106 S{fan_split[1]} {fan_0}\n"
    return lines

def dual_extruder_ByLayer(fan_layer_list, fan_0, fan_1):
    lines.insert(1, "\n;   Post Processed by Greg Valiant's [Advanced Fan Control 'By Layer'] for Prusa/Orca\n")
    active_tool = "T0"
    active_fan = fan_0
    off_fan = fan_1
    cur_fan_speed = 0
    start_layer = fan_layer_list[0].split("/")[0]
    for layer_speed in fan_layer_list:
        layer = layer_speed.split("/")[0]
        speed = layer_speed.split("/")[1]
        for index, line in enumerate(lines):
            if ";Layer:" + layer.split("/")[0] in line:
                lines.insert(index, f"M999 S{speed}\n")
                break
    speed_change_started = False
    for index, line in enumerate(lines):
        if line.startswith("T0") or line.startswith("T1"):
            if line.startswith("T0"):
                active_fan = fan_0
                off_fan = fan_1
            elif line.startswith("T1"):
                active_fan = fan_1
                off_fan = fan_0
            if speed_change_started:
                lines[index] = f"M106 S0 {off_fan}\n{line}M106 S{cur_speed} {active_fan}\n"
        if line.startswith("M999"):
            cur_speed = int(line.split("S")[1][:-1])
            lines[index] = f"M106 S{cur_speed} {active_fan}\n"
            speed_change_started = True
    return lines

def single_extruder_ByFeature(feature_type_list, feature_speed_list, start_layer, end_layer, fan_0):
    lines.insert(1, "\n;   Post Processed by Greg Valiant's [Advanced Fan Control 'By Feature'] for Prusa/Orca\n")
    end_index = None
    for index, line in enumerate(lines):
        if line == f";Layer:{start_layer}\n":
            start_index = index
        if line == f";Layer:{int(end_layer) + 1}\n":
            end_index = index
        if "end gcode" in line:
            last_index = index
    if end_index == None:
        end_index = last_index
    for num in range(start_index, end_index):
        if lines[num] in feature_type_list:
            cur_index = feature_type_list.index(lines[num])
            cur_speed = feature_speed_list[cur_index]
            lines[num] += f"M106 S{cur_speed} {fan_0}\n"
    if end_index != last_index:
        lines[end_index] += f"M106 S{feature_speed_list[10]} {fan_0}\n"
    return lines

def dual_extruder_ByFeature(feature_type_list, feature_speed_list, start_layer, end_layer, fan_0, fan_1):
    lines.insert(1, "\n;   Post Processed by Greg Valiant's [Advanced Fan Control 'By Feature'] for Prusa/Orca\n")
    end_index = None
    for index, line in enumerate(lines):
        if line == f";Layer:{start_layer}\n":
            start_index = index
        if line == f";Layer:{int(end_layer) + 1}\n":
            end_index = index
        if "end gcode" in line:
            last_index = index
    if end_index == None:
        end_index = last_index
    # Track the tool number
    active_tool = "T0"
    active_fan = fan_0
    off_tool = "T1"
    off_fan = fan_1
    cur_speed = 0
    for num in range(0, start_index):
        if line.startswith("T0"):
            active_fan = fan_0
        elif line.startswith("T1"):
            active_fan = fan_1
    for num in range(start_index, end_index):
        if lines[num] in feature_type_list:
            cur_index = feature_type_list.index(lines[num])
            cur_speed = feature_speed_list[cur_index]
            lines[num] += f"M106 S{cur_speed} {active_fan}\n"
        if fan_0 != fan_1:
            if lines[num].startswith("T0"):
                lines[num] = f"M106 S0 {fan_1}\n{lines[num]}M106 S{cur_speed} {fan_0}\n"
                active_fan = fan_0
            if lines[num].startswith("T1"):
                lines[num] = f"M106 S0 {fan_0}\n{lines[num]}M106 S{cur_speed} {fan_1}\n"
                active_fan = fan_1
    if end_index != last_index:
        final_speed = feature_speed_list[10]
        lines[end_index] += f"M106 S{final_speed} {active_fan}\n"
        for num in range(end_index, last_index):
            if fan_0 != fan_1:
                if line.startswith("T0"):
                    lines[num] = f"M106 S0 {fan_1}\n{lines[num]}M106 S{cur_speed} {fan_0}\n"
                if line.startswith("T1"):
                    lines[num] = f"M106 S0 {fan_0}\n{lines[num]}M106 S{cur_speed} {fan_1}\n"
    return lines

def fan_speed_feature_type(feature_text):
    feature_type = -1
    while feature_type == -1:
        try:
            feature_type = int(input(f"{feature_text}")) * 2.55
            if feature_type < 0 or feature_type > 255:
                feature_type = -1
                print("The fan speed must be an integer between 0 and 100.  Try again.")
                continue
        except:
            print("There was an error in the input.  Try again.")
            feature_type = -1
            continue
    return feature_type

def add_starting_ending_fan(extruder_count, fan_0, fan_1):
    start_index = None
    for index, line in enumerate(lines):
        if line == ";Layer:1\n":
            start_index = index
            fan_off_line = f"M106 S0 {fan_0}"
            if extruder_count > 1:
                fan_off_line += f"\nM106 S0 {fan_1}"
            fan_off_line += f"\n{lines[index - 1]}\n"
            lines[index - 1] = fan_off_line
        if line.startswith("M140 S0") and start_index != None:
            fan_off_line = f"M106 S0 {fan_0}"
            if extruder_count > 1:
                fan_off_line += f"\nM106 S0 {fan_1}"
            fan_off_line += f"\n{lines[index]}"
            lines[index] = fan_off_line
    return

# Get the settings from Prusa
def get_prusa_settings(lines: str) -> str:
    raft_layers = 0
    total_layer_count = 0
    for line in lines:
        if ";Layer:" in line:
            total_layer_count += 1
        if "; raft_layers =" in line:
            raft_layers = int(line.split("= ")[1])
        if "; nozzle_diameter =" in line:
            nozzle_size_str = line.split("= ")[1]
            nozzle_size_list = nozzle_size_str.split(",")
            nozzle_size_0 = float(nozzle_size_list[0])
            if len(nozzle_size_list) > 1:
                nozzle_size_1 = float(nozzle_size_list[1])
            else:
                nozzle_size_1 = None

            extruder_count = len(nozzle_size_list)
        if "; draft_shield =" in line:
            if "disabled" in line:
                draft_shield = False
            else:
                draft_shield = True

    raft_cooling_speed = 0
    return raft_layers, raft_cooling_speed, total_layer_count, nozzle_size_0, nozzle_size_1, extruder_count, draft_shield

# Get user settings
def get_post_settings() -> str:
    # Get the layer count and number of raft layers
    prusa_settings = get_prusa_settings(lines)
    raft_layers = prusa_settings[0] #  raft_layers, raft_cooling_speed, total_layer_count, nozzle_size_0, nozzle_size_1, extruder_count, draft_shield
    raft_cooling_speed = prusa_settings[1]
    total_layer_count = prusa_settings[2]
    nozzle_size_0 = prusa_settings[3]
    nozzle_size_1 = prusa_settings[4]
    extruder_count = prusa_settings[5]
    draft_shield = prusa_settings[6]

    response = "99"
    while response == "99":
        # Should previous M106 lines be removed?  Not doing so will allow changes made by previous instances of PrusaFanControl to remain in the gcode.
        fan_speed_0_to_1 = "99"
        while fan_speed_0_to_1 not in [True, False]:
            fan_speed_0_to_1_str = input("'Fan Speed Scale'\n Should Fan Speeds be normal PWM (0 to 255) or RepRap (0 to 1)?\n Enter <1> for PWM or <2> for RepRap 0 to 1\n")
            if fan_speed_0_to_1_str not in ['1', '2']:
                print("Invalid entry.  Must be '1' for PWM scale, or '2' for 0 to 1 scale\n")
                fan_speed_0_to_1_str = "99"
                continue
            if fan_speed_0_to_1_str == "2":
                fan_speed_0_to_1 = True
            else:
                fan_speed_0_to_1 = False

        fan_0 = "101"
        while not fan_0.startswith("P") and not fan_0 == "":
            try:
                fan_0 = int(input("'Fan Circuit Number Extruder 1 (T0)'\n Of the Layer Cooling Fan of the primary extruder (T0).\n (This is usually '0' but might be different for your machine.) <enter>\n"))
            except:
                print("Input error.  Must be an integer from 0 to 99")
                fan_0 = "101"
                continue
            if extruder_count > 1:
                fan_1 = int(input("'Fan Circuit Number Extruder 2 (T1)'\n of the Layer Cooling Fan of the second extruder (T1)?\n (This is often the same as the primary extruder but can be different on some IDEX and other printers.) <enter>\n"))

            else:
                fan_1 = ""
            if not fan_0 >= 0 and fan_0 <= 99:
                print("Invalid response.  Try again.")
                continue
            fan_0 = str(fan_0)
            if extruder_count >1:
                fan_1 = str(fan_1)
            if extruder_count == 1 and fan_0 == "0":
                fan_0 = ""
            elif extruder_count == 1 and fan_0 != "0":
                fan_0 = "P" + fan_0
            elif extruder_count > 1:
                if fan_0 == fan_1:
                    fan_0 = ""
                    fan_1 = ""
                else:
                    fan_0 = "P" + str(fan_0)
                    fan_1 = "P" + str(fan_1)

        remove_m106 = "r"
        while not remove_m106 in [True, False]:
            try:
                remove_m106 = input("'Remove existing M106 lines'\n If you intend to run more than one instance of this post-processor, the first instance should remove the M106 and M107 lines and succeeding instances should not.  (NOTE: M106/M107 Removal starts at the first layer regardless of your 'Start Layer'.)\n Enter <y> for Remove or <n> for Leave them alone\n").lower()
                if remove_m106 not in ["y", "n"]:
                    print("Invalid response.  Must be 'y' or 'n'.")
                    continue
                if remove_m106 == "y":
                    remove_m106 = True
                else:
                    remove_m106 = False
            except:
                print("Invalid response.  Must be y or n.")
                remove_m106 = "r"

            fan_mode = ""
            while fan_mode not in [1, 2]:
                try:
                    fan_mode = int(input("'Fan Control'\n Enter <1> for 'By Feature' or <2> for 'By Layer'\n 'By Feature' works better for long prints because the fan takes a bit to react to a command and spin up, or wind down to speed.\n"))
                except:
                    print("Input error.  Must be a 1 or a 2.")
                    fan_mode = ""
                    continue
            # Review the user settings
            input_str = "\nReview your settings to this point:\n\n"
            input_str += f"Fan Speed Scale 0 to 1.......... {str(fan_speed_0_to_1)}\n"
            input_str += f"Extruder 1 (T0) Cooling Fan Nr.. {fan_0 if fan_0 != "" else "0"}\n"
            if extruder_count > 1:
                input_str += f"Extruder 2 (T1) Cooling Fan Nr.. {fan_1 if fan_1 != "" else "0"}\n"
            input_str += f"Remove existing fan lines....... {remove_m106}\n"
            input_str += f"By Feature or By Layer.......... {'By Feature' if fan_mode == 1 else 'By Layer'}"
            response = input(input_str + "\n\n Enter 'y' to continue or 'n' to try again\n")
            if response not in ['y', 'n']:
                print("Invalid response.  Try again. <Enter>")
                response = "99"
                continue
            if response == 'n':
                response = "99"
    return remove_m106, fan_0, fan_1, raft_layers, raft_cooling_speed, total_layer_count, nozzle_size_0, nozzle_size_1, extruder_count, fan_mode, fan_speed_0_to_1

def remove_fan_lines() -> str:
    # Remove the M106 and M107 lines if requested.
    for index, line in enumerate(lines):
        if "LAYER_CHANGE" in line:
            start_here = index
            break
    for index, line in enumerate(lines):
        if index <= start_here:
            continue
        if "M106" in line or "M107" in line:
            lines[index] = ""
    return lines

if __name__ == "__main__":
    main()