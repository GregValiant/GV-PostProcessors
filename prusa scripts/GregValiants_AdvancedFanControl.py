# By GregValiant
# This PrusaSlicer/Orca script will:
#    Add fan speed changes 'By Layer' or 'By Feature'

import sys
import re
import os

sourceFile = sys.argv[1]
final_file = open(sourceFile, "r")
lines = final_file.readlines()
try:
    response = input("Greg Valiants [Advanced Fan Control] for Prusa/Orca has started.\nDo you wish to continue? (y,n).\n").lower()
except:
    response = "n"
if response == "n":
    exit(0)

# Get the layer count and number of raft layers
raft_layers = 0
total_layer_count = 0
for line in lines:
    if ";LAYER_CHANGE" in line:
        total_layer_count += 1
    if "; raft_layers =" in line:
        raft_layers = int(line.split("= ")[1])
raft_cooling_speed = 0

# Should previous M106 lines be removed?  Not doing so will allow changes made by previous instances of PrusaFanControl to remain in the gcode.
try:
    fan_speed_0_to_1_str = input("Should Fan Speeds be normal PWM (0 to 255) or RepRap (0 to 1)? <p,r>\n")
    if fan_speed_0_to_1_str == "r":
        fan_speed_0_to_1 = True
    else:
        fan_speed_0_to_1 = False
except:
    fan_speed_0_to_1 = False
try:
    remove_m106 = input("Should the existing M106 lines be removed?\nIf you intend to run more than one instance of this post-processor, the first instance should remove the M106 and M107 lines and succeeding instances should not.  (NOTE: M106/M107 Removal starts at the first layer regardless of your 'Start Layer'.)\nDo you want to remove the existing fan lines so they don't interfere?(y/n)\n").lower()
except:
    remove_m106 = "n"
# Remove the M106 and M107 lines if requested.
if remove_m106 == "y":
    for index, line in enumerate(lines):
        if "LAYER_CHANGE" in line:
            start_here = index
            break
    for index, line in enumerate(lines):
        if index <= start_here:
            continue
        if "M106" in line or "M107" in line:
                lines[index] = ""
try:
    by_layer = input("By Feature(f) or By Layer(l).\n").lower()
except:
    by_layer = "l"
if by_layer == "":
    response = input("Invalid response.  The script will exit with no fan changes. <Enter>")
    exit(0)

# BY LAYER
if by_layer == "l":
    # Add the post processor name to the gcode
    lines.insert(1, ";\n;   Post Processed by GregValiant [Advanced Fan Control By Layer] for Prusa/Orca")
    fan_layer_list = []
    fan_layers = ""
    try:
        fan_layers = input("Enter layers and Fan speeds as 'layer/speed'. For multiple changes delimit the settings with commas.\nWhat are the change layers and fan speed %(s) (EX: 5/35,25/100,35/0)\n")
    except:
        print("There appears to be an error in the 'layer / Speed' input.  All settings will be '0/0'.")
        fan_layers = "0/0"
    # Add the layer list to the gcode as a record of the settings
    lines.insert(2, ";\n;     Fan Changes (LAY / %): " + str(fan_layers))

    # Convert the fan_layers to a list
    if "," in fan_layers:
        new_layer_list = fan_layers.split(",")
        for fan_cmd in new_layer_list:
            fan_layer_list.append(fan_cmd)
    else:
        fan_layer_list.append(fan_layers)

    # Go through the file and make the changes
    for fan_change in fan_layer_list:
        fan_split = fan_change.split("/")
        layer_nr = int(fan_split[0])
        if not fan_speed_0_to_1:
            fan_speed = round(int(fan_split[1]) * 2.55)
        else:
            fan_speed = round(int(fan_split[1]) * 0.01,2)
        for index, line in enumerate(lines):
            if line == ";Layer:" + str(layer_nr) + "\n":
                lines[index] += "M106 S" + str(fan_speed) + "\n"

else:
    # Add the post processor name to the gcode
    lines.insert(1, ";\n;   Post Processed by GregValiant [Advanced Fan Control By Feature] for Prusa/Orca")
    setting_review = "r"
    while setting_review == "r":
        # Get the fan settings for each feature
        try:
            start_layer = int(input("Enter the starting layer.  Use the preview numbers.\n"))
            if start_layer < 1: start_layer = 1
        except:
            start_layer = 1
        try:
            end_layer = int(input(f"Enter the ending layer number.  Fan control will continue to the end of this layer.  Use the layer numbers from the preview (top layer is: {total_layer_count}).\n"))
            if end_layer > total_layer_count or end_layer == 0: end_layer = total_layer_count
        except:
            end_layer = total_layer_count
        try:
            type_external_perimeter = int(input("\nEnter the Fan speed (0% to 100%) for each feature as they come up.\n\nTYPE:External Perimeter (outer walls)\n")) * 2.55
        except:
            type_external_perimeter = 0
        try:
            type_perimeter = int(input("TYPE:Perimeter (inner walls)\n")) * 2.55
        except:
            type_perimeter = 0
        try:
            type_top_solid_infill = int(input("TYPE:Top solid infill (very top skins)\n")) * 2.55
        except:
            type_top_solid_infill = 0
        try:
            type_solid_infill = int(input("TYPE:Solid infill (bottom and middle skins)\n")) * 2.55
        except:
            type_solid_infill = 0
        try:
            type_bridge_infill = int(input("TYPE:Bridge infill (first skin over infill and bridges)\n")) * 2.55
        except:
            type_bridge_infill = 0
        try:
            type_internal_infill = int(input("TYPE:Internal infill (infill)\n")) * 2.55
        except:
            type_internal_infill = 0
        try:
            type_skirt_brim = 0
            if start_layer == 1:
                type_skirt_brim = int(input("TYPE:Skirt/Brim (bed adhesion) and Draft Shield\n")) * 2.55
        except:
            type_skirt_brim = 0
        try:
            type_support = int(input("TYPE:Support (support structure)\n")) * 2.55
        except:
            type_support = 0
        try:
            type_support_interface = int(input("TYPE:Support interface (support interface)\n")) * 2.55
        except:
            type_support_interface = 0
        try:
            type_travel_fan_speed = input("Fan off during travel (WIPE) moves?\n   NOTE: turning off the fan during wipes will add A LOT of lines to the gcode.(y,n)\n").lower()
        except:
            type_travel_fan_speed = "n"
        if raft_layers > 0:
            try:
                raft_cooling_speed = int(input("You have a Raft enabled.  You can cool the top layer of the raft independent of your Start Layer.\nIf you wish to cool the top layer of the Raft enter the fan speed to use, or enter 0 to disable.\n")) * 2.55
            except:
                raft_cooling_speed = 0

        fan_off_for_travel = False
        if type_travel_fan_speed == "y":
            fan_off_for_travel = True
        final_fan_speed = 0
        if end_layer < total_layer_count:
            try:
                final_fan_speed = round(int(input(f"Enter the 'Final Fan Speed' for layers from your End Layer ({end_layer}) to the end of the print.\n")) * 2.55)
            except:
                fan_off_for_travel = False
        
        input_str = "\nReview your fan settings:\n\n"
        try:
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
            input_str += "TYPE:Internal infill.................................: " + str(round(type_internal_infill / 2.55)) + "%\n"
            if start_layer == 1:
                input_str += "TYPE:Skirt/Brim......................................: " + str(round(type_skirt_brim / 2.55)) + "%\n"
            input_str += "TYPE:Support.........................................: " + str(round(type_support / 2.55)) + "%\n"
            input_str += "TYPE:Support interface...............................: " + str(round(type_support_interface / 2.55)) + "%\n"
            input_str += "Fan off during travel................................: " + str(fan_off_for_travel) + "\n"
            if end_layer < total_layer_count:
                input_str += "Final Fan speed (above the End Layer)................: " + str(round(final_fan_speed / 2.55)) + "%\n"
            if raft_layers > 0:
                input_str += "Top-of-Raft fan speed................................: " + str(round(raft_cooling_speed / 2.55)) + "%\n"
            setting_review = input(input_str + "\n<Continue(y,n) or Redo(r)> ").lower()
        except:            
            setting_review = "n"
        if setting_review == "n":
            response = input("Your response was 'n'.  The script will exit with no fan changes. <Enter>.")
            exit(0)

    if raft_layers > 0 and raft_cooling_speed > 0:
        for index, line in enumerate(lines):
            if ";Layer:" + str(raft_layers) in line:
                lines.insert(index + 1, "M106 S" + str(round(raft_cooling_speed)) + "\n")
                start_here = index + 1
                while not ";LAYER_CHANGE" in lines[start_here]:
                    start_here += 1
                lines.insert(start_here, "M106 S0\n")
                break
        
    feature_type_list = [
        ";TYPE:External perimeter\n",
        ";TYPE:Perimeter\n",
        ";TYPE:Top solid infill\n",
        ";TYPE:Solid infill\n",
        ";TYPE:Bridge infill\n",
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
            round(type_internal_infill),
            round(type_skirt_brim),
            round(type_support),
            round(type_support_interface)]
    else:
        feature_speed_list = [
            round(type_external_perimeter / 255, 2),
            round(type_perimeter / 255, 2),
            round(type_top_solid_infill / 255, 2),
            round(type_solid_infill / 255, 2),
            round(type_bridge_infill / 255, 2),
            round(type_internal_infill / 255, 2),
            round(type_skirt_brim / 255, 2),
            round(type_support / 255, 2),
            round(type_support_interface / 255, 2)]
    # Go through the file and make the changes
    prev_fan_speed = 0
    run_script = False
    for index, line in enumerate(lines):
        if line == ";Layer:" + str(start_layer) + "\n":
            run_script = True
        if not run_script:
            continue
        if line in feature_type_list:
            position = feature_type_list.index(line)
            lines[index] += "M106 S" + str(feature_speed_list[position]) + "\n"
            prev_fan_speed = feature_speed_list[position]
        if fan_off_for_travel:
            if ";WIPE_START" in line:
                lines[index] += "M106 S0\n"
            elif ";WIPE_END" in line:
                lines[index] += f"M106 S{prev_fan_speed}\n"
        if line == ";Layer:" + str(end_layer + 1) + "\n":
            run_script = False
            break
    if end_layer < total_layer_count:
        for index, line in enumerate(lines):
            if line == ";Layer:" + str(end_layer + 1) + "\n":
                lines[index] += "M106 S" + str(final_fan_speed) + "\n"
                break

# If the M106 lines were removed then start with the fan off, and turn it off at the end.
if remove_m106 == "y":
    for index, line in enumerate(lines):
        if ";Layer:" in line:
            lines[index] = "M106 S0 ; Start with the fan off\n" + lines[index]
            break
    for index, line in enumerate(lines):
        if index < start_here:
            continue
        if "M140 S0" in line:
            lines[index] = "M106 S0 ; turn off fan\n" + lines[index]
            break

# Write the new file
dest_file = open(sourceFile, "w+")
for line in lines:
    dest_file.write(line)
dest_file.close()
final_file.close()