# Copyright (c) 2025 GregValiant (Greg Foresi)
#  Suitable to Prusa, Orca, and Bambu slicers
#    Add fan speed changes 'By Layer' or 'By Feature'
#    Supports dual extruders with dual fans
#    Bambu printers can optionally also control the Auxiliary and Chamber fans P2 and P3.

import sys
import os

sourceFile = sys.argv[1]
final_file = open(sourceFile, "r")
lines = final_file.readlines()

# If Add Layer Numbers didn't run first then exit
layer_numbers_added = False
for line in lines:
    if "[Add Layer Numbers]" in line:
        layer_numbers_added = True
        break
if not layer_numbers_added:
    input("'Advance Fan Control' requires that 'Add Layer Numbers' runs before it.  The script will exit.")
    exit(0)

control_p2_p3 = None
p2_fan_list = []
p3_fan_list = []
slicer_name = None
draft_shield = None
fan_speed_is_pwm = None
extruder_count = None
layer_count = None

def main(lines):
    response = "q"
    while not response in ["y", "n"]:
        response = input("\nGreg Valiants      [Advanced Fan Control]\nfor Prusa/Orca/Bambu has started.\n Note: You may run multiple instances of this script.  Example: The first might be for 'By Layer' up to layer 250 and then a second instance can be 'By Feature' and start at layer 250.\n Do you wish to continue?\n <y> Yes\n <n> No\n").lower()
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
    layer_count = my_settings[5]
    nozzle_size_0 = my_settings[6]
    nozzle_size_1 = my_settings[7]
    extruder_count = my_settings[8]
    fan_mode = my_settings[9]
    fan_speed_is_pwm = my_settings[10]
    slicer_name = get_slicer_settings(lines)[7]
    # If removing the existing fan lines
    if remove_m106:
        lines = remove_fan_lines(slicer_name)
    # Get the auxiliary and chamber fan info from Bambu
    if slicer_name == "Bambu":
        control_p2_p3_str = "r"
        while control_p2_p3_str == "r":
            control_p2_p3_str = input("\nDo you want to control the Aux and Chamber fans from Bambu Studio, or from here?\n <y> Yes, Control here\n <n> Control in Bambu\n")
            if control_p2_p3_str not in ["y", "n"]:
                response = input("Invalid response.  Must be 'y' or 'n'")
                control_p2_p3_str = "r"
                continue
        if control_p2_p3_str == "y":
            control_p2_p3 = True
            bambu_aux_fans = bambu_extra_fans()
            p2_fan_list = bambu_aux_fans[0]
            p3_fan_list = bambu_aux_fans[1]
        else:
            control_p2_p3 = False
            p2_fan_list = []
            p3_fan_list = []
    else:
        control_p2_p3 = False
        p2_fan_list = []
        p3_fan_list = []

    # The 4 options: Single Extruder By Layer, Singler extruder By Feature, Dual Extruder By Layer, Dual Extruder By Feature
    if fan_mode == 1:
        # Get the By Feature settings
        feature_settings = getSettings_ByFeature(fan_speed_is_pwm, layer_count, extruder_count, fan_0, fan_1, raft_layers, slicer_name, p2_fan_list, p3_fan_list)
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

        fan_layer_list = getSettings_ByLayer(fan_speed_is_pwm)
        if extruder_count == 1:
            # Single extruder by layer
            lines = single_extruder_ByLayer(fan_layer_list, fan_0)
        elif extruder_count > 1:
            # Dual extruder by layer
            lines = dual_extruder_ByLayer(fan_layer_list, fan_0, fan_1)

    # Make sure the fan is off at the start and end of the print.
    if slicer_name == "Bambu":
        lines = insert_aux_and_chamber_fans(p2_fan_list, p3_fan_list)
    if remove_m106:
        add_m106_S0_lines = add_starting_ending_fan(extruder_count, fan_0, fan_1, slicer_name, control_p2_p3)

    # Insert the by line
    if fan_mode == 1:
        by_line = ";     Post Processed by Greg Valiant's [Advanced Fan Control 'By Feature'] for Prusa/Orca/Bambu\n"
    else:
        by_line = ";     Post Processed by Greg Valiant's [Advanced Fan Control 'By Layer'] for Prusa/Orca/Bambu\n"
    for index, line in enumerate(lines):
        if "; HEADER_BLOCK_END" in line or "; external perimeters extrusion width =" in line:
            lines.insert(index, by_line)
            break

    # Send the file back to the slicer as it was received, with each line a separate item in the lines list
    for index, line in enumerate(lines):
        if "\n" in line[0:-1]:
            lines[index] = line[:-1]
            temp = lines.pop(index)
            temp1 = temp.split("\n")
            temp1.reverse()
            for n_line in temp1:
                lines.insert(index, n_line + "\n")

    # Write the file
    dest_file = open(sourceFile, "w")
    for line in lines:
        dest_file.write(line)
    dest_file.close()
    final_file.close()

def getSettings_ByLayer(fan_speed_is_pwm):
    fan_layers = "r"
    fan_layer_list = []
    while fan_layers == "r":
        fan_layers = input("\nThese settings are for the layer cooling fan.\nEnter layers and Fan speeds% as 'layer#/speed%'. For multiple changes delimit the settings with commas. The layer numbers must be in 'Ascending' order.\n (EX: 5/35,25/100,35/0)\n Layer/Speed: ")
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

    # Convert the percentages into PWM or 0to1 as required
    fan_layer_list = fan_layers.split(",")
    for index, fan in enumerate(fan_layer_list):
        if not fan_speed_is_pwm:
            fan_layer_list[index] = fan_layer_list[index].split("/")[0] + "/" + str(round(int(fan_layer_list[index].split("/")[1]) * .01, 2))
        else:
            fan_layer_list[index] = fan_layer_list[index].split("/")[0] + "/" + str(round(int(fan_layer_list[index].split("/")[1]) * 2.55))
    return fan_layer_list


def getSettings_ByFeature(fan_speed_is_pwm, layer_count, extruder_count, fan_0, fan_1, raft_layers, slicer_name, p2_fan_list, p3_fan_list):
    setting_review = "r"
    while setting_review == "r":
        # Get the fan settings for each feature
        start_layer = "a"
        while start_layer == "a":
            try:
                print("\nThe next settings are for 'By Feature'\n")
                start_layer = int(input("\n'Start Layer'\n Enter the start layer for Fan Control.  Use the preview numbers.\n Start Layer:"))
            except:
                print("The Start Layer must be an integer > 0.  Try again.")
                start_layer = "a"
                continue

        end_layer = "z"
        while end_layer == "z":
            try:
                end_layer = int(input(f"\n'End Layer'\n Enter the ending layer number.  Fan Control will continue to the end of this layer.  Use the layer numbers from the preview\n (top layer is: {layer_count}).\n End Layer:"))
                if end_layer > layer_count:
                    print(f"The end layer must be an integer less than {layer_count}.  Try again.\n")
                    end_layer = "z"
                    continue

            except:
                print(f"The end layer must be an integer less than {layer_count}.  Try again.\n")
                end_layer = "z"
                continue
        feature_names = getAliases(slicer_name)
        alias_bed_adhesion_skirt = feature_names[0]
        alias_bed_adhesion_brim = feature_names[1]
        alias_supt = feature_names[2]
        alias_supt_inter = feature_names[3]
        alias_wall_outer = feature_names[4]
        alias_wall_inner = feature_names[5]
        alias_infill = feature_names[6]
        alias_top_skin = feature_names[7]
        alias_mid_skin = feature_names[8]
        alias_btm_skin = feature_names[9]
        alias_overhang_wall = feature_names[10]
        alias_bridge = feature_names[11]
        alias_internal_bridge = feature_names[12]

        type_skirt = fan_speed_feature_type(f"\n'{alias_bed_adhesion_skirt}'\n Enter the Fan speed (0% to 100%) for the skirt/draft shield (in PrusaSlicer this includes the Brim).\n If your StartLayer is above Layer:1 this would only effect a draft shield.\n")
        if slicer_name == "Orca":
            type_brim = fan_speed_feature_type("\n'TYPE:Brim'\n Enter the Fan speed (0% to 100%) for the Brim.\n")
        else:
            type_brim = type_skirt
            
        type_support = fan_speed_feature_type(f"\n'{alias_supt}'\n Enter the Fan speed (0% to 100%) for the support structure.\n")
        type_support_interface = fan_speed_feature_type(f"\n'{alias_supt_inter}'\n Enter the Fan speed (0% to 100%) for the support interface.\n")
        type_wall_outer = fan_speed_feature_type(f"\n'{alias_wall_outer}'\n Enter the Fan speed (0% to 100%) for the outer walls.\n")
        type_wall_inner = fan_speed_feature_type(f"\n'{alias_wall_inner}'\n Enter the Fan speed (0% to 100%) for the inner walls.\n")
        type_infill = fan_speed_feature_type(f"\n'{alias_infill}'\n Enter the Fan speed (0% to 100%) for the infill.\n")
        type_top_skin = fan_speed_feature_type(f"\n'{alias_top_skin}'\n Enter the Fan speed (0% to 100%) for the top skins.\n")
        type_mid_skin = fan_speed_feature_type(f"\n'{alias_mid_skin}'\n Enter the Fan speed (0% to 100%) for the internal skins.\n")
        if slicer_name == "Orca":
            type_btm_skin = fan_speed_feature_type(f"\n'TYPE:Bottom surface'\n Enter the Fan speed (0% to 100%) for the bottom skins.\n")
        else:
            type_btm_skin = type_mid_skin

        type_overhang_wall = fan_speed_feature_type(f"\n'{alias_overhang_wall}'\n Enter the Fan speed (0% to 100%) for the walls around overhangs.\n")
        type_bridge = fan_speed_feature_type(f"\n'{alias_bridge}'\n Enter the Fan speed (0% to 100%) for the outer bridging.\n")
        if slicer_name == "Orca":
            type_internal_bridge = fan_speed_feature_type("\n'TYPE:Internal Bridge'\n Enter the Fan speed (0% to 100%) for the internal bridging.\n")
        elif slicer_name == "Prusa":
            type_internal_bridge = type_bridge
        elif slicer_name == "Bambu":
            type_internal_bridge = type_btm_skin

        if end_layer < layer_count:
            final_fan_speed = fan_speed_feature_type("\n'Final Fan Speed'\n Your end layer is lower than the print top layer.  Enter the fan speed to use from the End layer to the end of the print.\n Enter the Fan speed (0% to 100%) for the Final Fan Speed.\n")
        else:
            final_fan_speed = 0

        # If there is a draft shield it is subject to the Skirt settings
        draft_shield = get_slicer_settings(lines)[6]
        # Review the 'By Feature' settings
        input_str = "\nReview your Custom Fan settings:\n\n"
        final_review = "z"
        while final_review == "z":
            if fan_speed_is_pwm:
                input_str += "Fan Scale is (0 to 255)\n"
            else:
                input_str += "Fan Scale is (0 to 1)\n"
            input_str += f"Start Layer (model starts on 'Layer:{1 + raft_layers}' in the Gcode) = {start_layer}\n"
            input_str += f"End Layer (top layer is {layer_count}) = {end_layer}\n"
            if start_layer == 1 or draft_shield:
                input_str += f"{alias_bed_adhesion_skirt[:-1]} = {round(type_skirt / 2.55)}%\n"
                if slicer_name == "Orca":
                    input_str += f"{alias_bed_adhesion_brim[:-1]} = {round(type_brim / 2.55)}%\n"
            input_str += f"{alias_wall_outer[:-1]} = {round(type_wall_outer / 2.55)}%\n"
            input_str += f"{alias_wall_inner[:-1]} = {round(type_wall_inner / 2.55)}%\n"
            input_str += f"{alias_top_skin[:-1]} = {round(type_top_skin / 2.55)}%\n"
            input_str += f"{alias_mid_skin[:-1]} = {round(type_mid_skin / 2.55)}%\n"
            if slicer_name == "Orca":
                input_str += f"{alias_btm_skin[:-1]} = {round(type_btm_skin / 2.55)}%\n"
            input_str += f"{alias_bridge[:-1]} = {round(type_bridge / 2.55)}%\n"
            if slicer_name == "Orca":
                input_str += f"{alias_internal_bridge[:-1]} = {round(type_internal_bridge / 2.55)}%\n"
            input_str += f"{alias_overhang_wall[:-1]} = {round(type_overhang_wall / 2.55)}%\n"
            input_str += f"{alias_infill[:-1]} = {round(type_infill / 2.55)}%\n"
            input_str += f"{alias_supt[:-1]} = {round(type_support / 2.55)}%\n"
            input_str += f"{alias_supt_inter[:-1]} = {round(type_support_interface / 2.55)}%\n"
            if end_layer < layer_count:
                input_str += f"; Final Fan speed = {round(final_fan_speed / 2.55)}%\n"
            if slicer_name == "Bambu":
                input_str += f"; Auxiliary Fan Layer/Speed = {p2_fan_list}\n"
                input_str += f"; Chamber Fan Layer/Speed = {p3_fan_list}\n"
            input_str = format_string(input_str)
            setting_review = input(input_str + "\n <y> Continue\n <r> Redo settings\n <x> Quit\n").lower()
            if setting_review not in ["y", "r", "x"]:
                print("Invalid response.  Response must be 'y', 'r', or 'x'.  Try again.\n")
                final_review = "z"
                continue
            else:
                final_review = "c"
            if setting_review == "x":
                response = input("Your response was 'x'.  The script will exit with no fan changes. <Enter>.")
                exit(0)

    feature_type_list = [
        alias_wall_outer,
        alias_wall_inner,
        alias_top_skin,
        alias_mid_skin,
        alias_btm_skin,
        alias_bridge,
        alias_internal_bridge,
        alias_overhang_wall,
        alias_infill,
        alias_bed_adhesion_skirt,
        alias_bed_adhesion_brim,
        alias_supt,
        alias_supt_inter]
    if fan_speed_is_pwm:
        feature_speed_list = [
            round(type_wall_outer),
            round(type_wall_inner),
            round(type_top_skin),
            round(type_mid_skin),
            round(type_btm_skin),
            round(type_bridge),
            round(type_internal_bridge),
            round(type_overhang_wall),
            round(type_infill),
            round(type_skirt),
            round(type_brim),
            round(type_support),
            round(type_support_interface),
            round(final_fan_speed)]

    else:
        feature_speed_list = [
            round(type_wall_outer / 255, 2),
            round(type_wall_inner / 255, 2),
            round(type_top_skin / 255, 2),
            round(type_mid_skin / 255, 2),
            round(type_btm_skin / 255, 2),
            round(type_bridge / 255, 2),
            round(type_internal_bridge / 255,2),
            round(type_overhang_wall / 255, 2),
            round(type_infill / 255, 2),
            round(type_skirt / 255, 2),
            round(type_brim / 255, 2),
            round(type_support / 255, 2),
            round(type_support_interface / 255, 2),
            round(final_fan_speed / 255, 2)]
    return feature_type_list, feature_speed_list, start_layer, end_layer

def single_extruder_ByLayer(fan_layer_list, fan_0):
    for index, line in enumerate(lines):
        if line == ";Layer#:1\n":
            start_index = index
            break
    for l_index in range(start_index,len(lines) - 1):
        if ";Layer#:" in lines[l_index]:
            layer_number = str(lines[l_index].split(":")[1][:-1])
            # If there is a match for the current layer number make the insertion
            for fan_change in fan_layer_list:
                fan_split = fan_change.split("/")
                layer_nr = int(fan_split[0])
                if layer_number == str(layer_nr):
                    lines[l_index] += f"M106 S{fan_split[1]} {fan_0}\n"
    return lines

def dual_extruder_ByLayer(fan_layer_list, fan_0, fan_1):
    active_tool = "T0"
    active_fan = fan_0
    off_fan = fan_1
    cur_fan_speed = 0
    start_layer = fan_layer_list[0].split("/")[0]
    for layer_speed in fan_layer_list:
        layer = layer_speed.split("/")[0]
        speed = layer_speed.split("/")[1]
        for index, line in enumerate(lines):
            # Insert a place holder
            if ";Layer#:" + layer.split("/")[0] in line:
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
        # Replace the place holder with a fan line
        if line.startswith("M999"):
            cur_speed = int(line.split("S")[1][:-1])
            lines[index] = f"M106 S{cur_speed} {active_fan}\n"
            speed_change_started = True
    return lines

def single_extruder_ByFeature(feature_type_list, feature_speed_list, start_layer, end_layer, fan_0):
    end_index = None
    for index, line in enumerate(lines):
        if line == f";Layer#:{start_layer}\n":
            start_index = index
        if line == f";Layer#:{int(end_layer) + 1}\n":
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
    end_index = None
    for index, line in enumerate(lines):
        if line == f";Layer#:{start_layer}\n":
            start_index = index
        if line == f";Layer#:{int(end_layer) + 1}\n":
            end_index = index
        if "; EXECUTABLE_BLOCK_END" in line or "M84" in line:
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
                    if slicer_name != "Bambu":
                        lines[num] = f"M106 S0 {fan_1}\n{lines[num]}M106 S{cur_speed} {fan_0}\n"
                    else:
                        lines[num] = f"M106 {fan_1} S0\n{lines[num]}M106 {fan_0} S{cur_speed}\n"
                if line.startswith("T1"):
                    if slicer_name != "Bambu":
                        lines[num] = f"M106 S0 {fan_0}\n{lines[num]}M106 S{cur_speed} {fan_1}\n"
                    else:
                        lines[num] = f"M106 {fan_0} S0\n{lines[num]}M106 {fan_1} S{cur_speed}\n"
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

def add_starting_ending_fan(extruder_count, fan_0, fan_1, slicer_name, control_p2_p3):
    start_index = None
    for index, line in enumerate(lines):
        if line == ";Layer#:1\n":
            start_index = index
            fan_off_line = f"M106 S0 {fan_0}"
            if extruder_count > 1:
                fan_off_line += f"\nM106 S0 {fan_1}"
            fan_off_line += f"\n{lines[index - 1]}"
            lines[index - 1] = fan_off_line
        if line.startswith("M140 S0") and start_index != None:
            if slicer_name != "Bambu":
                fan_off_line = f"M106 S0 {fan_0}"
                if extruder_count > 1:
                    fan_off_line += f"\nM106 S0 {fan_1}"
            elif slicer_name == "Bambu":
                fan_off_line = f"M106 {fan_0} S0"
                if extruder_count > 1:
                    fan_off_line += f"\nM106 {fan_1} S0"
                if control_p2_p3:
                    fan_off_line += f"\nM106 P2 S0\nM106 P3 S0"
            fan_off_line += f"\n{lines[index]}"
            lines[index] = fan_off_line
    return

# Get the slicer settings from the gcode
def get_slicer_settings(lines: str) -> str:
    raft_layers = 0
    layer_count = 0
    slicer_name = ""
    for line in lines:
        if "; generated by OrcaSlicer" in line:
            slicer_name = "Orca"
        if "; generated by PrusaSlicer" in line:
            slicer_name = "Prusa"
        if "; BambuStudio" in line:
            slicer_name = "Bambu"
        if slicer_name != "":
            break
    for line in lines:
        if ";Layer#:" in line:
            layer_count += 1
        
    raft_layers = int(os.environ["SLIC3R_RAFT_LAYERS"])
    nozzle_size_0 = float(os.environ["SLIC3R_NOZZLE_DIAMETER"].split(",")[0])
    nozzle_size_1 = 0.0
    if "," in os.environ["SLIC3R_NOZZLE_DIAMETER"]:
        nozzle_size_1 = float(os.environ["SLIC3R_NOZZLE_DIAMETER"].split(",")[1])    
    extruder_count = len(os.environ["SLIC3R_NOZZLE_DIAMETER"].split(","))    
    draft_shield = False if str(os.environ["SLIC3R_DRAFT_SHIELD"]) == 'disabled' else True
    raft_cooling_speed = 0
    
    return raft_layers, raft_cooling_speed, layer_count, nozzle_size_0, nozzle_size_1, extruder_count, draft_shield, slicer_name

# Get user settings
def get_post_settings() -> str:
    # Get the layer count and number of raft layers
    slicer_settings = get_slicer_settings(lines)
    raft_layers = slicer_settings[0]
    raft_cooling_speed = slicer_settings[1]
    layer_count = slicer_settings[2]
    nozzle_size_0 = slicer_settings[3]
    nozzle_size_1 = slicer_settings[4]
    extruder_count = slicer_settings[5]
    draft_shield = slicer_settings[6]

    response = "99"
    while response == "99":
        # Should previous M106 lines be removed?  Not doing so will allow changes made by previous instances of AdvancedFanControl to remain in the gcode.
        fan_speed_is_pwm = "99"
        while fan_speed_is_pwm not in [True, False]:
            fan_speed_is_pwm_str = input("\n'Fan Speed Scale'\n This is firmware dependent.  Marlin based firmware will use 'PWM' (0 to 255).  Some RepRap firmware might use '0 to 1'\n Either way, you will enter the fan speeds as a % with 0 being off, and 100 being full speed.\n <1> Normal PWM\n <2> RepRap 0 to 1\n")
            if fan_speed_is_pwm_str not in ['1', '2']:
                print("Invalid entry.  Must be '1' for PWM scale, or '2' for 0 to 1 scale\n")
                fan_speed_is_pwm_str = "99"
                continue
            if fan_speed_is_pwm_str == "1":
                fan_speed_is_pwm = True
            else:
                fan_speed_is_pwm = False

        fan_0 = "101"
        while not fan_0.startswith("P") and not fan_0 == "":
            try:
                fan_0 = int(input("\n'Fan Circuit Number Extruder 1 (T0)'\n The Layer Cooling Fan circuit number of the primary extruder (T0).\n (This is usually '0' but might be different for your machine.)\n T0 Fan #: "))
            except:
                print("Input error.  Must be an integer from 0 to 99")
                fan_0 = "101"
                continue
            if extruder_count > 1:
                fan_1 = int(input("\n'Fan Circuit Number Extruder 2 (T1)'\n The Layer Cooling Fan circuit number of the second extruder (T1)?\n (This is often the same as the primary extruder but can be different on some IDEX and other printers.)\n T1 Fan #: "))

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
                remove_m106 = input("\n'Remove existing M106 lines'\n If you intend to run more than one instance of this post-processor, the first instance should remove the M106 and M107 lines and succeeding instances should not.  (NOTE: M106/M107 Removal starts at the first layer regardless of your 'Start Layer'.)\n <y> Yes, Remove M106/M107\n <n> No, leave them be\n").lower()
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
                    fan_mode = int(input("\n'Fan Control by Layer or by Feature'\n 'By Feature' is good for large or slow prints.  (If the print is quick the fan ddoesn't really get a chance to settle at the speed setting.)\n <1> 'By Feature'\n <2> 'By Layer'\n"))
                except:
                    print("Input error.  Must be a 1 or a 2.")
                    fan_mode = ""
                    continue
            # Review the user settings
            input_str = "\nReview your settings to this point:\n\n"
            input_str += f"Fan Speed Scale 0 to 1.......... {str(fan_speed_is_pwm)}\n"
            input_str += f"Extruder 1 (T0) Cooling Fan Nr.. {fan_0 if fan_0 != "" else "0"}\n"
            if extruder_count > 1:
                input_str += f"Extruder 2 (T1) Cooling Fan Nr.. {fan_1 if fan_1 != "" else "0"}\n"
            input_str += f"Remove existing fan lines....... {remove_m106}\n"
            input_str += f"By Feature or By Layer.......... {'By Feature' if fan_mode == 1 else 'By Layer'}"
            input_str += "\n Does that look good?\n"
            response = input(input_str + "\n 'y' Continue\n 'n' Redo Settings\n")
            if response not in ['y', 'n']:
                print(response)
                print("Invalid response.  Try again. <Enter>")
                response = "99"
                continue
            if response == 'n':
                response = "99"
    return remove_m106, fan_0, fan_1, raft_layers, raft_cooling_speed, layer_count, nozzle_size_0, nozzle_size_1, extruder_count, fan_mode, fan_speed_is_pwm

def remove_fan_lines(slicer_name) -> str:
    # Remove the M106 and M107 lines if requested.
    if slicer_name == "Bambu":
        chg_line = "; CHANGE_LAYER"
    else:
        chg_line = ";LAYER_CHANGE"
    for index, line in enumerate(lines):
        if chg_line in line:
            start_here = index
            break
    for index, line in enumerate(lines):
        if index <= start_here:
            continue
        if slicer_name != "Bambu":
            if "M106" in line or "M107" in line:
                lines[index] = ""
        elif slicer_name == "Bambu":
            if control_p2_p3:
                if "M106" in line:
                    lines[index] = ""
            elif not control_p2_p3:
                if "M106" in line and not "P3" in line and not "P2" in line:
                    lines[index] = ""
    return lines

def getAliases(slicer_name):
    if slicer_name == "Prusa":
        alias_bed_adhesion_skirt = ";TYPE:Skirt/Brim\n"
        alias_bed_adhesion_brim = ";Not in Prusa"
        alias_supt = ";TYPE:Support material\n"
        alias_supt_inter = ";TYPE:Support material interface\n"
        alias_wall_outer = ";TYPE:External perimeter\n"
        alias_wall_inner = ";TYPE:Perimeter\n"
        alias_infill = ";TYPE:Internal infill\n"
        alias_top_skin = ";TYPE:Top solid infill\n"
        alias_mid_skin = ";TYPE:Solid infill\n"
        alias_btm_skin = ";TYPE:Solid infill\n"
        alias_overhang_wall = ";TYPE:Overhang perimeter\n"
        alias_bridge = ";TYPE:Bridge infill\n"
        alias_internal_bridge = ";Not in Prusa"

    elif slicer_name == "Orca":
        alias_bed_adhesion_skirt = ";TYPE:Skirt\n"
        alias_bed_adhesion_brim = ";TYPE:brim\n"
        alias_supt = ";TYPE:Support\n"
        alias_supt_inter = ";TYPE:Support interface\n"
        alias_wall_outer = ";TYPE:Outer wall\n"
        alias_wall_inner = ";TYPE:Inner wall\n"
        alias_infill = ";TYPE:Sparse infill\n"
        alias_top_skin = ";TYPE:Top surface\n"
        alias_mid_skin = ";TYPE:Internal solid infill\n"
        alias_btm_skin = ";TYPE:Bottom surface\n"
        alias_overhang_wall = ";TYPE:Overhang wall\n"
        alias_bridge = ";TYPE:Bridge\n"
        alias_internal_bridge = ";TYPE:Internal Bridge\n"

    elif slicer_name == "Bambu":
        alias_bed_adhesion_skirt = "; FEATURE: Skirt\n"
        alias_bed_adhesion_brim = "; FEATURE: Brim\n"
        alias_supt = "; FEATURE: Support\n"
        alias_supt_inter = "; FEATURE: Support interface\n"
        alias_wall_outer = "; FEATURE: Outer wall\n"
        alias_wall_inner = "; FEATURE: Inner wall\n"
        alias_infill = "; FEATURE: Sparse infill\n"
        alias_top_skin = "; FEATURE: Top surface\n"
        alias_mid_skin = "; FEATURE: Internal solid infill\n"
        alias_btm_skin = "; FEATURE: Bottom surface\n"
        alias_overhang_wall = "; FEATURE: Overhang wall\n"
        alias_bridge = "; FEATURE: Bridge\n"
        alias_internal_bridge = "Not in Bambu"
    return [alias_bed_adhesion_skirt, alias_bed_adhesion_brim, alias_supt, alias_supt_inter, alias_wall_outer, alias_wall_inner, alias_infill, alias_top_skin, alias_mid_skin, alias_btm_skin, alias_overhang_wall, alias_bridge, alias_internal_bridge]

def format_string(input_str):
    temp_lines = input_str.split("\n")
    gap_len = 0
    for temp_line in temp_lines:
        if "=" in temp_line:
            if gap_len - len(temp_line.split("=")[0]) + 1 < 0:
                gap_len = len(temp_line.split("=")[0]) + 1
    if gap_len < 30: gap_len = 30
    for temp_index, temp_line in enumerate(temp_lines):
        if "=" in temp_line:
            temp_lines[temp_index] = temp_line.replace(temp_line.split("=")[0], temp_line.split("=")[0] + str(
                "." * (gap_len - len(temp_line.split("=")[0]))), 1)
    input_str = "\n".join(temp_lines)
    return input_str

def bambu_extra_fans():
    response = input("The next settings are for the Auxiliary Fan (and the Chamber fan if it is supported).\n <enter>\n\n")
    bambu_p2_str = "r"
    p2_fan_list = []
    while bambu_p2_str == "r":
        bambu_p2_str = input("\n'Auxiliary Fan (P2)'\n Will the auxiliary fan be used?\n <y> Yes\n <n> No\n")
        if bambu_p2_str not in ["y", "n"]:
            bambu_p2_str = "r"
            print("Invalid response.  Must be 'y' or 'n'.\n")
            continue
        elif bambu_p2_str == "y":
            p2_layer_str = input("\nEnter the layers and fan speed percentages for the Auxiliary Fan as 'Layer#/Fan%'.  Delimit multiple ranges with commas.\n (Ex: 1/50,75/100,150/0)\n")
        if "," in p2_layer_str:
            new_layer_list = p2_layer_str.split(",")
            for fan_cmd in new_layer_list:
                p2_fan_list.append(fan_cmd)
        else:
            p2_fan_list.append(p2_layer_str)
        # Check for input errors
        err_code = 0
        for fan in p2_fan_list:
            if "/" not in fan or "." in p2_layer_str:
                err_code = 1
                p2_layer_str = "r"
                P2_fan_list = []
        if err_code > 0:
            print("There is an error in the fan list.  Each fan speed indicator must be entered as 'lay#/speed%'.  If more than one - they are separated by commas.\n Try again...")
            p2_layer_str = "r"
            continue

    chamber_temp_control_fan = False
    for line in lines:
        if "; support_chamber_temp_control =" in line:
            chamber_temp_control_fan = bool(int(line.split("= ")[1]))

    p3_fan_list = []
    if chamber_temp_control_fan:
        bambu_chamber_fan_str = "r"
        while bambu_chamber_fan_str == "r":
            bambu_chamber_fan_str = input("\n'Chamber Fan (P3)'\n Will the Chamber fan be used? <y> or <n>\n")
            if bambu_chamber_fan_str not in ["y", "n"]:
                bambu_chamber_fan_str = "r"
                print("Invalid response.  Must be 'y' or 'n'.\n")
                continue
            elif bambu_chamber_fan_str == "y":
                p3_layer_str = input("\nEnter the layers and fan speed percentages for the Chamber Fan as 'Layer#/Fan%'.\n  Delimit multiple ranges with commas.\n (Ex: 1/50,75/100,150/0)\n")
                if "," in p3_layer_str:
                    new_layer_list = p3_layer_str.split(",")
                    for fan_cmd in new_layer_list:
                        p3_fan_list.append(fan_cmd)
                else:
                    p3_fan_list.append(p3_layer_str)
            # Check for input errors
            err_code = 0
            for fan in p3_fan_list:
                if "/" not in fan or "." in p3_layer_str:
                    err_code = 1
                    p3_layer_str = "r"
                    p3_fan_list = []
            if err_code > 0:
                print("There is an error in the chamber fan list.  Each fan speed indicator must be entered as 'lay#/speed%'.  If more than one - they are separated by commas.\n Try again...")
                p3_layer_str = "r"
                continue

    if p2_fan_list == []:
        p2_fan_list = ["0/0"]
    else:
        for index, fan in enumerate(p2_fan_list):
            if not fan_speed_is_pwm:
                p2_fan_list[index] = p2_fan_list[index].split("/")[0] + "/" + str(round(int(p2_fan_list[index].split("/")[1]) * .01, 2))
            else:
                p2_fan_list[index] = p2_fan_list[index].split("/")[0] + "/" + str(round(int(p2_fan_list[index].split("/")[1]) * 2.55))

    if p3_fan_list == []:
        p3_fan_ist = ["0/0"]
    else:
        for index, fan in enumerate(p3_fan_list):
            if not fan_speed_is_pwm:
                p3_fan_list[index] = p3_fan_list[index].split("/")[0] + "/" + str(round(int(p3_fan_list[index].split("/")[1]) * .01, 2))
            else:
                p3_fan_list[index] = p3_fan_list[index].split("/")[0] + "/" + str(round(int(p3_fan_list[index].split("/")[1]) * 2.55))

    return p2_fan_list, p3_fan_list

def insert_aux_and_chamber_fans(p2_fan_list, p3_fan_list):
    for index, line in enumerate(lines):
        if line == ";Layer#:1\n":
            start_index = index
            break
    for l_index in range(start_index,len(lines) - 1):
        if ";Layer#:" in lines[l_index]:
            layer_number = str(lines[l_index].split(":")[1][:-1])
            # This is necessary when layer lines coincide
            if "\n" in layer_number:
                layer_number = layer_number.split("\n")[0]
            # If there is a match for the current layer number make the insertion
            for p2_change in p2_fan_list:
                fan_split = p2_change.split("/")
                layer_nr = int(fan_split[0])
                if int(layer_number) == layer_nr:
                    lines[l_index] += f"M106 P2 S{fan_split[1]} \n"

    for index, line in enumerate(lines):
        if line == ";Layer#:1\n":
            start_index = index
            break
    for l_index in range(start_index,len(lines) - 1):
        if ";Layer#:" in lines[l_index]:
            layer_number = str(lines[l_index].split(":")[1][:-1])
            # If there is a match for the current layer number make the insertion
            for p3_change in p3_fan_list:
                fan_split = p3_change.split("/")
                layer_nr = int(fan_split[0])
                if layer_number == str(layer_nr):
                    lines[l_index] += f"M106 P3 S{fan_split[1]}\n"
    return lines

if __name__ == "__main__":
    main(lines)