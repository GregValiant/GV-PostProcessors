# Copyright (c) 2025 GregValiant (Greg Foresi)
#  Suitable to Prusa, Orca, and Bambu slicers
#  Depending on the chosen options, this script can:
#    <retract> <Lift the nozzle> <park park the head> <pause> <take a image> <pause> <move back> <lower the nozzle> <unretract>.

import sys
import os

# Get the file from the slicer and read it in
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
    input("'Time Lapse Camera' requires that 'Add Layer Numbers' runs before it.  The script will exit.")
    exit(0)
    
# Let the user decide to run the script or exit without running.
try:
    response = input("\nGreg Valiants      [Time Lapse Camera]\nfor Prusa/Orca has started.  This will insert camera trigger commands every so-many layers.  Head park and retractions are options.\nDo you wish to Continue?\n <y> Yes\n <n> No\n").lower()
except:
    response = "n"
if response not in ["y", "n"]:
    fail_response = input("The response was other than 'y' or 'n'.  The script will exit.")
    exit(0)
if response == "n":
    exit(0)

# Insert the post-processor name
by_line = ";     Post Processed by Greg Valiant's [Time Lapse Camera] for Prusa/Orca/Bambu\n"
for index, line in enumerate(lines):
    if "; HEADER_BLOCK_END" in line or "; external perimeters extrusion width =" in line:
        lines.insert(index, by_line)
        break

# Get some settings
slicer_name = ""
for line in lines:
    if "Prusa" in line:
        slicer_name = "Prusa"
    if "Orca" in line:
        slicer_name = "Orca"
    if "BambuStudio" in line:
        slicer_name = "Bambu"
    if slicer_name != "":
        break
        
for index, line in enumerate(lines):
    if "; use_relative_e_distances" in line:
        relative_extrusion_str = line.split("= ")[1]
        if relative_extrusion_str == "0":
            relative_extrusion = False
        else:
            relative_extrusion = True
            
    if "; use_firmware_retraction" in line:
        firmware_retract_str = int(line.split("= ")[1])
        if firmware_retract_str == 0:
            firmware_retract = False
        elif firmware_retract_str == 1:
            firmware_retract = True
            
    if "; travel_speed =" in line:
        travel_speed = int(line.split("= ")[1]) * 60
      
    if "; retract_speed" in line or "; retraction_speed =" in line:
        retract_speed = int(line.split("= ")[1]) * 60
        
    if "; deretract_speed" in line or "; deretraction_speed =" in line:
        prime_speed = int(line.split("= ")[1]) * 60
        
    if "; retract_length =" in line or "; retraction_length =" in line or "; filament_retract_length =" in line:
        retract_length_str = line.split("= ")[1][:-1]
            retract_length_list = retract_length_str.split(",")
            if retract_length_list[0] != "nil":
                retract_length_ext_0 = round(float(retract_length_list[0]), 2)
                retract_enabled_ext_0 = True
            else:
                retract_length_ext_0 = 0.0
                retract_enabled_ext_0 = False
            retract_length_ext_1 = 0.0
            if len(retract_length_list) > 1:
                if retract_length_list[1] != "nil":
                    retract_length_ext_1 = round(float(retract_length_list[1]), 2)
                    retract_enabled_ext_1 = True
                else:
                    retract_length_ext_1 = 0.0
                    retract_enabled_ext_1 = False

    if "; bed_shape =" in line or "; printable_area =" in line:
        bed_shape = line.split("= ")[1]
        bed_min_x = bed_shape.split(",")[0].split("x")[0]
        bed_max_x = bed_shape.split(",")[2].split("x")[0]
        bed_min_y = bed_shape.split(",")[0].split("x")[1]
        bed_max_y = bed_shape.split(",")[2].split("x")[1]
if retract_dist > 0:
    retract_enabled = True
else:
    retract_enabled = False

# Get settings from the user
response = "r"
while response == "r":
    try:
        trigger_command = input("Enter the 'Trigger Commmand' you want to use.  This is often M240.\n").upper()
    except:
        trigger_command = "None"
    try:
        insert_frequency = int(input("How often should the 'Trigger Commmand' be inserted.\n 1) Every Layer\n 2) Every 2nd layer\n 3) Every 3rd layer\n etc, etc, etc.\n"))
    except:
        insert_frequency = 1
    try:
        anti_shake_wait = int(input("How long to wait for the printer frame to settle down before taking the image.  (Units is 'micro-seconds' so 500 is 1/2 second.)\n"))
    except:
        anti_shake_wait = 0
    try:
        pause_length = int(input("How long to wait after taking the image.  (Units is 'micro-seconds'.)\n"))
    except:
        pause_length = 0
    try:
        park_print_head_str = input("Do you want to park the print head?\n <y< Yes\n <n> No\n").lower()
        if park_print_head_str == "y":
            park_print_head = True
        else:
            park_print_head = False
    except:
        park_print_head = True
    try:
        if park_print_head:
            x_park = int(input(f"Park head 'X'. (min: {bed_min_x} to max: {bed_max_x}) <enter>\n"))
            y_park = int(input(f"Park head 'Y'. (min: {bed_min_y} to max: {bed_max_y}) <enter>\n"))
            if x_park < int(bed_min_x):
                x_park = int(bed_min_x)
            if x_park > int(bed_max_x):
                x_park = int(bed_max_x)
            if y_park < int(bed_min_y):
                y_park = int(bed_min_y)
            if y_park > int(bed_max_y):
                y_park = int(bed_max_y)
    except:
        x_park = 0
        y_park = 0
    try:
        retract_str = input("Add a retraction when necessary?\n (The only time this might be <n> is if Retraction is not enabled.)\n <y> Yes\n <n> No\n").lower()
        if retract_str == "y":
            retract = True
        else:
            retract = False
    except:
        retract = True
    try:
        zhop = int(input("Z-hop distance before parking the head.\n"))
        if zhop < 0: zhop = 0
    except:
        zhop = 0
    try:
        ensure_final_image_str = input("Insure a final image?\n (Since you can choose not to take an image on every layer, there might not be an end-of-print image.  Choosing <y> here will insure that one is taken when the print ends regardless of the 'Frequency'.)\n <y> Yes\n <n> No\n").lower()
        if ensure_final_image_str == "y":
            ensure_final_image = True
        else:
            ensure_final_image = False
    except:
        ensure_final_image = True

# Review the user settings
    input_str = "\nReview your camera settings:\n\n"
    input_str += f"Trigger Command............. {trigger_command}\n"
    input_str += f"Insert Frequency............ {insert_frequency}\n"
    input_str += f"Anti-Shake-Wait............. {anti_shake_wait}\n"
    input_str += f"Pause after image........... {pause_length}\n"
    input_str += f"Park Print Head............. {park_print_head}\n"
    if park_print_head:
        input_str += f"  Park Head X............... {x_park}\n"
        input_str += f"  Park Head Y............... {y_park}\n"
    input_str += f"Retract when necessary...... {retract}\n"
    input_str += f"Z-hop before parking........ {zhop}\n"
    input_str += f"Insure final Image.......... {ensure_final_image}\n"

    try:
        response = input(input_str + "\n <y> Continue\n <r> Redo\n <x> Quit\n").lower()
        if response not in ["y", "r", "x"]:
            fail_response = input("The response must be either 'y', 'r', or 'x'.  You must input the settings again.")
            response = "r"
    except:
        response = "x"
    if response == "x":
        exit(0)

# Put together a list of the layer changes
data_list = [0]
for index, line in enumerate(lines):
    if ";TYPE:Custom" in line or "; CHANGE_LAYER" in line:
        data_list.append(index)
        break

for num in range(data_list[1], len(lines) - 1):
    if ";Layer:" in lines[num]:
        data_list.append(num + 1)
        break

layers_index = data_list[2] + 1
for num in range(layers_index, len(lines) - 1):
    if ";Layer:" in lines[num]:
        data_list.append(num + 1)
        continue
    elif ";END gcode" in lines[num]:
        data_list.append(num + 1)
        continue
    elif "M84" in lines[num]:
        data_list.append(num + 2)
        break

# Initialize some variables
speed_z = 1200
if relative_extrusion:
    rel_cmd = 83
else:
    rel_cmd = 82
last_x = 0
last_y = 0
last_z = 0
last_e = 0
prev_e = 0
is_retracted = False

# Put the insertion sub-string together
gcode_to_append = ""
if park_print_head:
    gcode_to_append += f"G0 F{travel_speed} X{x_park} Y{y_park} ;Park print head\n"
gcode_to_append += "M400 ;Wait for moves to finish\n"
if anti_shake_wait > 0:
    gcode_to_append += f"G4 P{anti_shake_wait} ;Wait for printer to settle down\n"
gcode_to_append += trigger_command + " ;Snap the Image\n"
if pause_length > 0:
    gcode_to_append += f"G4 P{pause_length} ;Wait for camera to finish\n"

# Use the insert_frequency to index through the layers
current_lines_index = 2
while current_lines_index < len(data_list) - 2:
    for num in range(data_list[current_lines_index], data_list[current_lines_index + 1]):
        if lines[num].startswith("G1"):
            temp = lines[num].split(" ")
            for param in temp:
                if param.startswith("X"):
                    last_x = float(param[1:])
                elif param.startswith("Y"):
                    last_y = float(param[1:])
                elif param.startswith("E"):
                    last_e = float(param[1:])
                elif param.startswith("Z"):
                    last_z = float(param[1:])

            #Track the E location so that if there is already a retraction we don't double dip.
            if rel_cmd == 82:
                if " E" in lines[num]:
                    if float(last_e) < float(prev_e):
                        is_retracted = True
                    else:
                        is_retracted = False
                    prev_e = last_e
            elif rel_cmd == 83:
                if " E" in lines[num]:
                    if float(last_e) < 0:
                        is_retracted = True
                    else:
                        is_retracted = False
                    prev_e = 0
        # Retractions
        if firmware_retract and lines[num][0:3] in {"G10", "G11"}:
            if lines[num][1:3] == "10":
                is_retracted = True
                last_e = float(prev_e) - float(retract_dist)
            if lines[num][1:3] == "11":
                is_retracted = False
                last_e = float(prev_e) + float(retract_dist)
            if rel_cmd == 82:
                prev_e = last_e
            else:
                prev_e = 0

    # Put the main insertion string together
    camera_code = ";TYPE:CUSTOM-----------------TimeLapse Begin\n"
    if retract and not is_retracted and retract_enabled:
        camera_code += "M83 ;Extrude Relative\n"
        if not firmware_retract:
            camera_code += f"G1 F{retract_speed} E-{retract_dist} ;Retract filament\n"
        else:
            camera_code += "G10 ;Retract filament\n"
    if zhop != 0:
        camera_code += f"G1 F{speed_z} Z{round(last_z + zhop,2)} ;Move up\n"
    camera_code += gcode_to_append
    camera_code += f"G1 F{travel_speed} X{last_x} Y{last_y} ;Restore XY position\n"
    if zhop != 0:
        camera_code += f"G1 F{speed_z} Z{last_z} ;Restore Z position\n"
    if retract and not is_retracted and retract_enabled:
        if not firmware_retract:
            camera_code += f"G1 F{retract_speed} E{retract_dist} ;Un-Retract filament\n"
        else:
            camera_code += "G11 ;Un-Retract filament\n"
        camera_code += f"M{rel_cmd} ;Extrusion Mode\n"
    camera_code += f";{'-' * 28}TimeLapse End\n"
    
    # Format the camera code to be inserted
    temp_lines = camera_code.split("\n")
    for temp_index, temp_line in enumerate(temp_lines):
        if ";" in temp_line and not temp_line.startswith(";"):
            temp_lines[temp_index] = temp_line.replace(temp_line.split(";")[0], temp_line.split(";")[0] + str(" " * (29 - len(temp_line.split(";")[0]))),1)
    temp_lines = "\n".join(temp_lines)
    
    # Insert the camera code string
    lines.insert(data_list[current_lines_index + 1] - 2, temp_lines)
    
    # Index the data_list to account for the insertion so the next one goes in the proper location in the gcode.
    for dnum, lnum in enumerate(data_list):
        data_list[dnum] += 1
    current_lines_index += insert_frequency
    
# Final image if there was no camera shot at the end of the last layer.
need_final = True
for line in lines[data_list[len(data_list) - 3]:data_list[len(data_list) - 1]]:
    if "TimeLapse" in line:
        need_final = False
        break
if ensure_final_image and need_final:
    last_image_str = ";TYPE:CUSTOM-----------------TimeLapse Final Image\n"
    last_image_str += "M83                          ;Relative Extrusion\n"
    last_image_str += "G91                          ;Relative Movement\n"
    last_image_str += f"G1 F{retract_speed} E-{retract_dist}               ;Retract\n"
    last_image_str += "G1 F1200 Z1                  ;Move up\n"
    last_image_str += f"G1 F{travel_speed} X0 Y{int(bed_max_y)-3}             ;Park Head\n"
    last_image_str += "M400                         ;Wait for moves to finish\n"
    last_image_str += trigger_command + "                         ;Snap the final Image\n"
    if pause_length > 0:
        last_image_str += f"G4 P{pause_length}                      ;Wait for camera to finish\n"
    last_image_str += "G90                          ;Absolute Movement\n"
    if rel_cmd == 82:
        last_image_str += "M82                          ;Absolute Extrusion\n"
    last_image_str += ";----------------------------TimeLapse End\n"    
    lines.insert(data_list[len(data_list)-2] - 1, last_image_str)

# Send the file back to the slicer as it was received, with each line a separate item in the lines list
for index, line in enumerate(lines):
    if "\n" in line[0:-1]:
        lines[index] = line[:-1]
        temp = lines.pop(index)
        temp1 = temp.split("\n")
        temp1.reverse()
        for n_line in temp1:
            lines.insert(index, n_line + "\n")

# Write the new file
dest_file = open(sourceFile, "w+")
for line in lines:
    dest_file.write(line)
dest_file.close()
final_file.close()