"""
    Copyright (c) 2025 GregValiant (Greg Foresi)
    Suitable to Prusa, Orca, Bambu, and Creality slicers
    Depending the the selected options, this script can:
        <Retract> <Lift nozzle> <Park> <Quick purge> <Unload filament> <Pause> <Load filament> <Purge> <Retract> <Move back> <Lower nozzle> <Unretract>
"""

import sys
import re
import os

sourceFile = sys.argv[1]
#sourceFile = "C:/Users/grego/Documents/Creality/gcode/PrusaShape.gcode"
final_file = open(sourceFile, "r")
lines = final_file.readlines()

# If Add Layer Numbers didn't run first then exit
layer_numbers_added = False
for line in lines:
    if "[Add Layer Numbers]" in line:
        layer_numbers_added = True
        break
if not layer_numbers_added:
    input("'Pause at Layer' requires that 'Add Layer Numbers' runs before it.  The script will exit.")
    exit(0)

# Run the script or exit?
response = "r"
while response == "r":
    response = input("\nGreg Valiants      [Pause at Layer]\n for PrusaSlicer/OrcaSlicer/BambuStudio/CrealityPrint has started.\n  This will insert 'park - pause - resume' code at the indicated layers.  You can make insertions at more than one layer provided that they all use the same general settings (same park position, filament temp's, etc.).\n (There may be as many as 24 settings and then a 'Review'.)\n  Do you wish to Continue?\n <y> Yes\n <n> No\n").lower()
    if response not in ["y", "n"]:
        input("Invalid response.  Enter a 'y' for Yes or an 'n' for No.")
        response = "r"
if response == "n":
    final_file.close()
    exit(0)    

# Initialize some variables
fan_speed_0_to_1 = False
extruder_count = 1
layer_count = 0
unload_amount = 0
enable_quick_purge = False
reload_amount = 0

def main(lines):
    # Insert the post-processor name
    by_line = ";     Post Processed by Greg Valiant's [Pause at Layer] for Prusa/Orca/Bambu/Creality\n"
    for index, line in enumerate(lines):
        if "; HEADER_BLOCK_END" in line or "; external perimeters extrusion width =" in line:
            lines.insert(index, by_line)
            break
            
    # Get slicer settings from slicer   
    slicer_settings = get_slicer_settings(lines)    
    # Assign to variables
    relative_extrusion = slicer_settings[0]
    retract_enabled_ext_0 = slicer_settings[1]
    retract_length_ext_0 = slicer_settings[24]
    retract_speed_ext_0 = slicer_settings[2]
    deretract_speed_ext_0 = slicer_settings[3]
    retract_enabled_ext_1 = slicer_settings[4]
    retract_length_ext_1 = slicer_settings[25]
    retract_speed_ext_1 = slicer_settings[5]
    deretract_speed_ext_1 = slicer_settings[6]
    firmware_retract = slicer_settings[7]
    speed_travel = slicer_settings[8]
    bed_min_x = slicer_settings[9]
    bed_max_x = slicer_settings[10]
    bed_min_y = slicer_settings[11]
    bed_max_y = slicer_settings[12]
    bed_max_z = slicer_settings[26]
    nozzle_size = slicer_settings[13]
    initial_layer_height = slicer_settings[14]
    layer_height = slicer_settings[15]
    z_hop_ext_0 = slicer_settings[16]
    z_hop_ext_1 = slicer_settings[17]
    temperature_ext_0 = slicer_settings[18]
    temperature_ext_1 = slicer_settings[19]
    layer_count = slicer_settings[20]
    slicer_name = slicer_settings[21]
    speed_unload = slicer_settings[22]
    extruder_count = slicer_settings[23]
    speed_z_hop = 1200

    # Get settings from the user
    script_settings = get_post_settings(layer_count, bed_max_x, bed_min_x, bed_max_y, bed_min_y, speed_unload, nozzle_size, extruder_count)
    # Assign to variables
    pause_layer_list = script_settings[0]
    pause_method = script_settings[1]
    dwell_time = script_settings[2]
    reason_for_pause = script_settings[3]
    unload_amount = script_settings[4]
    enable_quick_purge = script_settings[5]
    reload_amount = script_settings[6]
    speed_unload = script_settings[7]
    purge_amount = script_settings[8]
    extra_prime_amount = script_settings[9]
    hold_steppers_on = script_settings[10]
    disarm_timeout = script_settings[11]
    head_park_enable = script_settings[12]
    park_x = script_settings[13]
    park_y = script_settings[14]
    move_z = script_settings[15]
    standby_temperature = script_settings[16]
    resume_temperature_cmd = script_settings[17]
    resume_print_temperature = script_settings[18]
    custom_gcode_before_pause = script_settings[19]
    beep_at_pause = script_settings[20]
    custom_gcode_after_pause = script_settings[21]
    redo_layer = script_settings[22]
    redo_layer_flow = script_settings[23]
    display_text_list = script_settings[24]

    for index, pause_layer in enumerate(pause_layer_list):
        tool_nr = 0
        if extruder_count > 1:
            for l_index, line in enumerate(lines):
                if line == f";Layer#:{pause_layer}\n":
                    pause_index = l_index
                    break
            for num in range(1, pause_index):
                if lines[num].startswith("T"):
                    tool_nr = lines[num][1:]
        if tool_nr == 0:
            z_hop_enabled = bool(z_hop_ext_0)
            z_hop_height = z_hop_ext_0
        elif tool_nr == 1:
            z_hop_enabled = bool(z_hop_ext_1)
            z_hop_height = z_hop_ext_1

        purge_speed = round(nozzle_size * 500) # calculate the purge speed based on the nozzle size.  A 0.4 will be 200 and a 0.8 will be 400 mm/min.
        min_purge_clearance = 15
        layers_started = False
        if redo_layer and reason_for_pause == "Filament Change":
            redo_layer_flow_cmd = f"M221 S{redo_layer_flow}" + str(" " * (27 - len("M221 S" + str(redo_layer_flow)))) + "; Set 'Redo Layer' Flow Rate\n"
            redo_layer_flow_reset = "M221 S100" + str(" " * (27 - len("M221 S100"))) + "; End of Redo Layer - Reset Flow Rate\n"
        else:
            redo_layer_flow_cmd = ""
            redo_layer_flow_reset = ""
        use_tool_temperature = True
        control_temperatures = True

        # Capitalize the command letter of any added commands.  Some firmware doesn't acknowledge lower case commands.
        gcode_before = custom_gcode_before_pause
        if gcode_before != "":
            if "," in gcode_before:
                xtra_cmds = gcode_before.split(",")
                for index in range(0, len(xtra_cmds)):
                    xtra_cmds[index] = xtra_cmds[index][0].upper() + xtra_cmds[index][1:] + "; Custom code before pause"
                gcode_before = "\n".join(xtra_cmds)
            else:
                gcode_before = gcode_before[0].upper() + gcode_before[1:] + "; Custom code before pause"
        gcode_after = custom_gcode_after_pause
        if gcode_after != "":
            if "," in gcode_after:
                xtra_cmds = gcode_after.split(",")
                for index in range(0, len(xtra_cmds)):
                    xtra_cmds[index] = xtra_cmds[index][0].upper() + xtra_cmds[index][1:] + " ; Custom code after pause"
                gcode_after = "\n".join(xtra_cmds)
            else:
                gcode_after = gcode_after[0].upper() + gcode_after[1:] + " ; Custom code after pause"
        beep_length = 1500

        # Track values in the gcode
        current_z = initial_layer_height
        current_layer = 1
        got_first_g_cmd_on_layer_0 = False
        current_tool = 0 # Tracks the current extruder for tracking the target temperature.
        target_temperature = {} # Tracks the current target temperature for each extruder.
        prev_layer_index = 0
    for p_index, pause_layer in enumerate(pause_layer_list):
        for index, line in enumerate(lines):
            # Use the tool number to determine the speed and retraction distance at a pause (for dual-extruder printers)
            if line.startswith("T"):
                current_tool = getValue(line, "T")
            if current_tool == 0:
                retract_length = retract_length_ext_0
                retract_speed = retract_speed_ext_0
                deretract_speed = deretract_speed_ext_0
                retract_enabled = retract_enabled_ext_0
            elif current_tool == 1:
                retract_length = retract_length_ext_1
                retract_speed = retract_speed_ext_1
                deretract_speed = deretract_speed_ext_1
                retract_enabled = retract_enabled_ext_1
            if ";Layer#:1" in line:
                layers_started = True
            if not layers_started:
                continue
            # Look for the feed rate of an extrusion instruction
            if line.startswith(("G0 ", "G1 ", "G2 ", "G3 ", "G92 ")):
                if " F" in line and " X" in line and " Y" in line and " E" in line:
                    current_extrusion_f = getValue(line, "F")
                # If a Z instruction is in the line, read the current Z
                if getValue(line, "Z") is not None:
                    current_z = getValue(line, "Z")

            if not line.startswith(";Layer#:"):
                continue
            current_layer = int(line.split(":")[1][:-1])
            if current_layer < int(pause_layer):
                prev_layer_index = index
                if str(current_layer)[-2:] in ["00", "20", "40", "60", "80"]:
                    print("Working thru Layer: " + str(current_layer) + "\n")
                continue

            if current_layer == int(pause_layer):
            # Access last layer, browse it backwards to find last extruder absolute position check if it is a retraction
            # This also becomes the 'redo layer' if the option is chosen
                prev_lines = lines[prev_layer_index:index]
                is_retracted = None
                current_e = None
            for prevLine in reversed(prev_lines):
                if prevLine.startswith(("G0 ", "G1 ", "G2 ", "G3 ")):
                    current_e = getValue(prevLine, "E")
                    if re.search(r"G1 F(\d+\.|\d+) E(-?\d+\.|-?\d+)", prevLine) or "G10" in prevLine:
                        if is_retracted == None:
                            is_retracted = True
                    if current_e is not None:
                        if is_retracted is None:
                            is_retracted = False
                        break

            # and also find last X,Y
            for prevLine in reversed(prev_lines):
                if prevLine.startswith(("G0 ", "G1 ", "G2 ", "G3 ")):
                    if " X" in prevLine and " Y" in prevLine:
                        x = getValue(prevLine, "X")
                        y = getValue(prevLine, "Y")
                        break

            # Maybe redo the previous layer.
            redo_layer_str = ""
            if redo_layer and reason_for_pause == "Filament Change":
                prev_layer = lines[prev_layer_index:index]
                for z_index, line in enumerate(prev_layer):
                    if line.startswith(";Layer#:"):
                        prev_layer[z_index] = re.sub(";Layer#:", ";Redo_Layer#:", line)[:-1]
                        break
                temp_list = prev_layer
                temp_list[0] = temp_list[0] + str(" " * (29 - len(temp_list[0] + ".1"))) + "; Redo layer from PauseAtLayer\n" + redo_layer_flow_cmd
                prev_layer = "".join(temp_list)

                # Get the X Y position and the extruder's absolute position at the beginning of the redone layer.
                start_at = getNextXY(prev_layer_index)
                start_at_x = start_at[0]
                start_at_y = start_at[1]
                start_at_e = start_at[2]
                start_retracted = start_at[3]
                prev_layer = f"G1 F{speed_travel}\nG1 X{start_at_x} Y{start_at_y}\nG92 E{start_at_e}\n{prev_layer}"
                redo_layer_str = prev_layer + redo_layer_flow_reset
                
            # Start putting together the pause string 'prepend_gcode'
            prepend_gcode = f";TYPE:CUSTOM---------------; Pause before the start of layer {current_layer}\n"
            # Retraction
            prepend_gcode += "M83 ; Relative extrusion\n"
            if not is_retracted and retract_enabled:
                if firmware_retract:
                    prepend_gcode += "G10\n"
                else:
                    prepend_gcode += f"G1 F{retract_speed} E-{retract_length} ; Retract\n"
            if head_park_enable:
                # Move the head to the park location
                if current_z + move_z > bed_max_z:
                    move_z = 0
                prepend_gcode += f"G1 F{speed_z_hop} Z{round(current_z + move_z, 2)} ; Move up to clear the print\n"
                prepend_gcode += f"G1 F{speed_travel} X{park_x} Y{park_y} ; Move to park location\n"
                if current_z < move_z:
                    prepend_gcode += f"G1 F{speed_z_hop} Z{round(current_z + move_z, 2)} ; Move up to clear the print\n"
                if current_z < min_purge_clearance - move_z:
                    prepend_gcode += f"G1 F{speed_z_hop} Z{min_purge_clearance} ; Minimum clearance" + str(" to purge" if purge_amount != 0 and reason_for_pause == 'Filament Change' else "") + " - move up some more\n"            
            
            # 'Unload' and 'purge' are only available if there is a filament change.
            if reason_for_pause == "reason_filament" and int(unload_amount) > 0:
                # If it's a filament change then insert any 'unload' commands
                prepend_gcode += "M400 ; Complete all moves\n"
                # Break up the unload distance into chunks of 150mm to avoid any firmware balks for 'too long of an extrusion'
                if unload_amount > 0:
                    # The quick purge is meant to soften the filament end to insure it will retract.
                    if enable_quick_purge:
                        quick_purge_amt = retract_length + 7 if retract_length < 2 else retract_length * 2.5
                        prepend_gcode += f"G1 F{purge_speed} E{quick_purge_amt} ; Quick purge before unload\n"
                if unload_amount > 150:
                    temp_unload = unload_amount
                    while temp_unload > 150:
                        prepend_gcode += f"G1 F{speed_unload} E-150 ; Unload some\n"
                        temp_unload -= 150
                    if 0 < temp_unload <= 150:
                        prepend_gcode += f"G1 F{int(speed_unload)} E-{temp_unload} ; Unload the remainder\n"
                else:
                    prepend_gcode += f"G1 E{-unload_amount} F{int(speed_unload)} ; Unload\n"
            
            # Set extruder standby temperature
            if control_temperatures:
                prepend_gcode += f"M104 S{round(standby_temperature)} ; Standby temperature\n"

            if len(display_text_list) > 0:
                try:
                    if display_text_list[p_index] != "":
                        prepend_gcode += f"M117 {display_text_list[p_index]} ; Message to LCD\n"
                except:
                    pass            
           
            # Set the disarm timeout
            if hold_steppers_on:
                prepend_gcode += f"M84 S{disarm_timeout}"
                if int(disarm_timeout) > 0:
                    prepend_gcode += " ; Keep motors engaged for " + str(disarm_timeout/60) + " minutes\n"
                else:
                    prepend_gcode += " ; Keep motors engaged until printer power turned off (Marlin).\n"

            # Beep at pause
            if beep_at_pause:
                prepend_gcode += "M300 S440 P1500 ; Beep\n"

            # Set a custom GCODE section before pause
            if gcode_before:
                prepend_gcode += gcode_before + "\n"

            if len(display_text_list) > 0:
                try:
                    if display_text_list[p_index] != "":
                        prepend_gcode += f"M118 {display_text_list[p_index]} ; Message to print server\n"
                except:
                    pass
                    
            # Add the pause command
            temp_cmd = pause_method
            if temp_cmd == "M0 w/message":
                try:
                    if len(display_text_list) < len(pause_layer_list):
                        add_msg = display_text_list[0]
                    else:
                        add_msg = display_text_list[p_index]
                    if "w/message" in temp_cmd:
                        temp_cmd = temp_cmd.replace("w/message", add_msg + " click to resume")
                    if "w/message" in temp_cmd:
                        temp_cmd = "M0"
                except:
                    temp_cmd = "M0"

            prepend_gcode += temp_cmd + "; Do the actual pause\n"

            # Set a custom GCODE section after pause
            if gcode_after != "":
                prepend_gcode += gcode_after + "\n"

            # If redoing a layer then move back own to the previous layer height.
            if redo_layer:
                working_z = current_z - (layer_height if not z_hop_enabled else 0)
                working_z_txt = "; Move down to redo layer height\n"
            else:
                working_z = current_z
                working_z_txt = "; Move down to resume height\n"

            # Set extruder resume temperature
            prepend_gcode += f"{resume_temperature_cmd}{resume_print_temperature} ; Resume print temperature\n"

            # Load and Purge.  Break the load amount in 150mm chunks to avoid 'too long of extrusion' warnings from firmware.
            if reason_for_pause == "Filament Change":
                if int(reload_amount) > 0:
                    if reload_amount * .9 > 150:
                        temp_reload = reload_amount - reload_amount * .1
                        while temp_reload > 150:
                            prepend_gcode += f"G1 F{speed_unload} E150 ; Fast Reload\n"
                            temp_reload -= 150
                        if 0 < temp_reload <= 150:
                            prepend_gcode += f"G1 F{speed_unload} E{round(temp_reload)} ; Fast Reload\n"
                            prepend_gcode += f"G1 F{round(float(nozzle_size) * 16.666 * 60)} E{round(reload_amount * .1)} ; Reload the remaining 10% slow to avoid slamming the nozzle\n"
                        else:
                            prepend_gcode += f"G1 F{round(float(nozzle_size) * 16.666 * 60)} E{round(reload_amount * .1)} ; Reload the remaining 10% slow to avoid slamming the nozzle\n"
                    else:
                        prepend_gcode += f"G1 F{speed_unload} E{round(reload_amount * .9)} ; Fast Reload\n"
                        prepend_gcode += f"G1 F{round(float(nozzle_size) * 16.666 * 60)} E{round(reload_amount * .1)} ; Reload the last 10% slower to avoid ramming the nozzle\n"
                if int(purge_amount) > 0:
                    prepend_gcode += f"G1 F{round(float(nozzle_size) * 8.333 * 60)} E{purge_amount} ; Purge\n"
                    if not firmware_retract and retract_enabled_ext_0:
                        prepend_gcode += f"G1 F{retract_speed} E{-retract_length} ; Retract\n"
                    elif firmware_retract and retract_enabled:
                        prepend_gcode += "G10 ; Retract\n"
                    # If there is a purge then give the user time to grab the string before the head moves back to the print position.
                    prepend_gcode += "M400 ; Complete all moves\n"
                    prepend_gcode += "M300 P500 ; Beep\n"
                    prepend_gcode += "G4 S2 ; Wait for 2 seconds\n"

                # Move the head back
                if head_park_enable:
                    prepend_gcode += f"G1 F{speed_travel} X{x} Y{y} ; Move to resume location\n"
                    prepend_gcode += f"G1 F{speed_z_hop} Z{working_z} {working_z_txt}"

                if purge_amount != 0:
                    if firmware_retract and not is_retracted and retract_enabled_ext_0:
                        prepend_gcode += "G11 ;Unretract\n"
                    else:
                        if not is_retracted and retract_enabled_ext_0:
                            prepend_gcode += f"G1 F{deretract_speed} E{retract_length} ; Unretract\n"

                # If the pause is for something like an insertion then there might be an extra prime amount
                if extra_prime_amount != "0" and reason_for_pause == "All Others":
                    prepend_gcode += f"G1 F{deretract_speed} E{extra_prime_amount} ; Extra Prime\n"

                extrusion_mode_string = "absolute"
                extrusion_mode_numeric = 82

                if relative_extrusion:
                    extrusion_mode_string = "relative"
                    extrusion_mode_numeric = 83

                if not redo_layer:
                    prepend_gcode += f"M{extrusion_mode_numeric} ; Switch back to {extrusion_mode_string} E values\n"

                # Reset extruder value to pre pause value
                    prepend_gcode += f"G92 E{0 if relative_extrusion else current_e} ; Reset extruder location\n"

                if redo_layer and reason_for_pause == "Filament Change":
                    # All other options reset the E value to what it was before the pause because E things were added.
                    # If it's not yet reset, it still needs to be reset if there were any redo layers.
                    if is_retracted:
                        prepend_gcode += f"G92 E{0 if relative_extrusion else current_e - retract_length} ; Reset extruder location ~ retracted\n"
                        prepend_gcode += f"M{extrusion_mode_numeric} ; Switch back to {extrusion_mode_string} E values\n"
                    else:
                        prepend_gcode += f"G92 E{0 if relative_extrusion else current_e} ; Reset extruder location ~ unretracted\n"
                        prepend_gcode += f"M{extrusion_mode_numeric} ; Switch back to {extrusion_mode_string} E values\n"
                elif redo_layer and reason_for_pause == "All Others":
                    prepend_gcode += f"M{extrusion_mode_numeric} ; Switch back to {extrusion_mode_string} E values\n"
            else:
                if head_park_enable:
                    prepend_gcode += f"G1 F{speed_travel} X{x} Y{y} ; Move to resume location\n"
                prepend_gcode += f"G1 F{speed_z_hop} Z{working_z} {working_z_txt}"
                if extra_prime_amount > 0:
                    prepend_gcode += f"G1 F{deretract_speed} E{extra_prime_amount} ; Extra prime\n"
                prepend_gcode += f"G92 E{current_e} ; Reset extruder\n"
                    
            # Format prepend_gcode
            prepend_gcode += f";{'-' * 26}; End of the Pause code\n"
            temp_lines = prepend_gcode.split("\n")
            for temp_index, temp_line in enumerate(temp_lines):
                if ";" in temp_line and not temp_line.startswith(";"):
                    temp_lines[temp_index] = temp_line.replace(temp_line.split(";")[0], temp_line.split(";")[0] + str(" " * (27 - len(temp_line.split(";")[0]))),1)
            prepend_gcode = "\n".join(temp_lines)
            # Insert the Pause Prepend snippet at the end of the previous layer just before "TIME_ELAPSED".
            lines[index-1] += prepend_gcode + redo_layer_str
            prepend_gcode = ""
            break

    # Send the file back to the slicer as it was received, with each line a separate item in the lines list and each ending with a newline character
    for index, line in enumerate(lines):
        if "\n" in line[0:-1]:
            lines[index] = line[:-1]
            temp = lines.pop(index)
            temp1 = temp.split("\n")
            temp1.reverse()
            for n_line in temp1:
                lines.insert(index, n_line + "\n")
                
    # Write the new file
    print("Writing File...")
    dest_file = open(sourceFile, "w+")
    #dest_file = open("C:/Users/grego/Documents/Creality/gcode/PrusaOutput.gcode", "w+")
    for line in lines:
        dest_file.write(line)
    dest_file.close()
    final_file.close()

def get_slicer_settings(lines):
    slicer_name = ""
    for line in lines:
        if "Prusa" in line:
            slicer_name = "Prusa"
        if "Orca" in line:
            slicer_name = "Orca"
        if "Bambu" in line:
            slicer_name = "Bambu"
        if "Creality_Print" in line:
            slicer_name = "Creality"
        if slicer_name != "":
            break
            
    layer_count = 0    
    for line in lines:
        if ";Layer#:" in line:
            layer_count += 1
            
    retract_enabled_ext_0 = False
    retract_enabled_ext_1 = False
    retract_speed_ext_1 = 0
    deretract_speed_ext_1 = 0
    retract_length_ext_1 = 0
    z_hop_ext_1 = 0
    z_hop_enabled_ext_1 = False
    temperature_ext_1 = 0
    relative_extrusion = bool(int(os.environ["SLIC3R_USE_RELATIVE_E_DISTANCES"]))
    firmware_retract = bool(int(os.environ["SLIC3R_USE_FIRMWARE_RETRACTION"]))
    speed_travel = int(os.environ["SLIC3R_TRAVEL_SPEED"]) * 60
    layer_height = float(os.environ["SLIC3R_LAYER_HEIGHT"])        
    nozzle_size = float(os.environ["SLIC3R_NOZZLE_DIAMETER"].split(",")[0])

    if slicer_name == "Prusa":
        retract_dist_var = "SLIC3R_RETRACT_LENGTH"
        retract_speed_var = "SLIC3R_RETRACT_SPEED"
        deretract_speed_var = "SLIC3R_DERETRACT_SPEED"
        initial_layer_height_var = "SLIC3R_FIRST_LAYER_HEIGHT"
        machine_max_z_var = "SLIC3R_MAX_PRINT_HEIGHT"
        print_temp_var = "SLIC3R_TEMPERATURE"
        machine_max_speed_e_var = "SLIC3R_MACHINE_MAX_FEEDRATE_E"
        machine_bed_size_var = "SLIC3R_BED_SHAPE"
        machine_max_z_var = "SLIC3R_MAX_PRINT_HEIGHT"
        z_hop_height_var = "SLIC3R_RETRACT_LIFT"
    elif slicer_name in ["Orca","Bambu","Creality"]:
        retract_dist_var = "SLIC3R_RETRACTION_LENGTH"
        retract_speed_var = "SLIC3R_RETRACTION_SPEED"
        deretract_speed_var = "SLIC3R_DERETRACTION_SPEED"
        initial_layer_height_var = "SLIC3R_INITIAL_LAYER_PRINT_HEIGHT"
        machine_max_z_var = "SLIC3R_PRINTABLE_HEIGHT"
        print_temp_var = "SLIC3R_NOZZLE_TEMPERATURE"
        machine_max_speed_e_var = "SLIC3R_MACHINE_MAX_SPEED_E"
        machine_bed_size_var = "SLIC3R_PRINTABLE_AREA"
        machine_max_z_var = "SLIC3R_PRINTABLE_HEIGHT"
        z_hop_height_var = "SLIC3R_Z_HOP"

    retract_speed_ext_0 = int(os.environ[retract_speed_var].split(",")[0]) * 60
    
    extruder_count = 1
    if retract_speed_ext_0 != 0:
        retract_enabled_ext_0 = True
    if "," in os.environ[retract_speed_var]:
        retract_speed_ext_1 = int(os.environ[retract_speed_var].split(",")[1]) * 60
        extruder_count = 2
        if retract_speed_ext_1 != 0:
            retract_enabled_ext_1 = True
    
    retract_length_ext_0 = float(os.environ[retract_dist_var].split(",")[0])
    if "," in os.environ[retract_dist_var]:
        retract_length_ext_1 = float(os.environ[retract_dist_var].split(",")[1])

    deretract_speed_ext_0 = int(os.environ[deretract_speed_var].split(",")[0]) * 60
    if "," in os.environ[deretract_speed_var]:
        deretract_speed_ext_1 = int(os.environ[deretract_speed_var].split(",")[1]) * 60

    speed_unload = int(os.environ[machine_max_speed_e_var].split(",")[0]) * 60

    bed_size = str(os.environ[machine_bed_size_var])
    bed_list = bed_size.split(",")
    if len(bed_list) > 4:
        bed_shape = "elliptic"
        prev_x = 0
        prev_y = 0
        for coord in bed_list:
            x = float(coord.split("x")[0])
            y = float(coord.split("x")[1])
            if x > prev_x:
                prev_x = x
            if y > prev_y:
                prev_y = y
        bed_min_x = -abs(prev_x)
        bed_max_x = abs(prev_x)
        bed_min_y = -abs(prev_y)
        bed_max_y = abs(prev_y)
    else:
        bed_shape = "rectangle"
        bed_min_x = bed_size.split(",")[0].split("x")[0]
        bed_max_x = bed_size.split(",")[2].split("x")[0]
        bed_min_y = bed_size.split(",")[0].split("x")[1]
        bed_max_y = bed_size.split(",")[2].split("x")[1]
    
    bed_max_z = int(os.environ[machine_max_z_var])

    z_hop_ext_0 = float(os.environ[z_hop_height_var].split(",")[0])
    z_hop_enabled_ext_0 = False if z_hop_ext_0 == 0.0 else True
    if "," in os.environ[z_hop_height_var]:
        z_hop_ext_1 = float(os.environ[z_hop_height_var].split(",")[1])
        z_hop_enabled_ext_1 = False if z_hop_ext_1 == 0.0 else True
    temperature_ext_0 = str(os.environ[print_temp_var]).split(",")[0]
    if "," in os.environ[print_temp_var]:
        temperature_ext_1 = str(os.environ[print_temp_var]).split(",")[1]
    
    initial_layer_height = float(os.environ[initial_layer_height_var])

    if retract_length_ext_0 > 0:
        retract_enabled = True
    else:
        retract_enabled = False
    if speed_unload == None:
        speed_unload = 3000
    speed_z_hop = 1200

    return [
        relative_extrusion, #0
        retract_enabled_ext_0,
        retract_speed_ext_0,
        deretract_speed_ext_0,
        retract_enabled_ext_1,
        retract_speed_ext_1, #5
        deretract_speed_ext_1,
        firmware_retract,
        speed_travel,
        bed_min_x,
        bed_max_x, #10
        bed_min_y,
        bed_max_y,
        nozzle_size,
        initial_layer_height,
        layer_height, #15
        z_hop_ext_0,
        z_hop_ext_1,
        temperature_ext_0,
        temperature_ext_1,
        layer_count, #20
        slicer_name,
        speed_unload,
        extruder_count,
        retract_length_ext_0,
        retract_length_ext_1, #25
        bed_max_z ]

# Get user settings
def get_post_settings(layer_count, bed_max_x, bed_min_x, bed_max_y, bed_min_y, speed_unload, nozzle_size, extruder_count) -> str:
    # Get the layer count and number of raft layers
    dwell_time = 0
    carry_on = False

    while carry_on == False:
        pause_layer_str = ""
        while pause_layer_str == "":
            pause_layer_list = []
            pause_layer_str = input(f"\n 'The Pause Layer(s)'\n The pauses occur at the start of the layer number(s) you enter.\n  If you have more than one pause, and they all use the same settings, you can enter them here delimited with commas.\nEx: 34,56,77. (There are {layer_count} layers in the gcode.) <enter>\n")
            if pause_layer_str == "":
                continue
            if "," in pause_layer_str:
                pause_layer_list = pause_layer_str.split(",")
                for q_index, layer in enumerate(pause_layer_list):
                    try:
                        pause_layer_list[q_index] = int(pause_layer_list[q_index])
                    except:
                        print("Invalid layer number.  Try again.")
                        pause_layer_str = ""
                        break
            else:
                try:
                    pause_layer_list.append(int(pause_layer_str))
                except:
                    print("Invalid response.  The layers must be integers and multiple layers must be delimited with commas.")
                    pause_layer_str = ""
                    continue

        pause_method_str = ""
        while pause_method_str == "":
            pause_method_str = input("\n 'The Pause Commmand'\n    NOTE: The command is firmware specific. You must know which one works with your printer.\n\n 1) M0 (Marlin w/message)\n 2) M0 (Marlin w/no message)\n 3) M25 (BQ)\n 4) M226 (RepRap)\n 5) @pause (Repetier/Octoprint)\n 6) M125 (alternate Octoprint)\n 7) M2000 (raise3D)\n 8) PAUSE (Klipper)\n 9) G4 (dwell)\n 10) M600 (filament change)\n 11) Custom Command\n (If you use 'G4', 'M600', or 'Custom' there will be additional settings)\n<enter>\n")
            match pause_method_str:
                case "1":
                    pause_method = "M0 w/message"
                case "2":
                    pause_method = "M0"
                case "3":
                    pause_method = "M25"
                case "4":
                    pause_method = "M226"
                case "5":
                    pause_method = "@pause"
                case "6":
                    pause_method = "M125"
                case "7":
                    pause_method = "M2000"
                case "8":
                    pause_method = "PAUSE"
                case "9":
                    pause_method = "G4 S"
                    dwell_time = 0
                    while dwell_time == 0:
                        dwell_time = input("\n 'G4 Dwell Time in Minutes'\n Enter the time to wait in minutes.  After this amount of time the printer will restart by it\n There is no way to lengthen or shorten the 'Dwell' once it starts.\n <enter>\n")
                        try:
                            dwell_time = int(dwell_time)*60
                        except:
                            print("Invalid response.  Dwell Time must be an integer indicating the number of minutes to wait.")
                            dwell_time = 0
                            continue
                        pause_method += str(dwell_time)
                case "10":
                    pause_method = get_m600_params(extruder_count)
                case "11":
                    pause_method = input(" Enter your 'Custom' command.\n<enter>\n")
                case _:
                    print("Invalid response.  Must be 1 thr 11 inclusive.")
                    pause_method = ""
                    pause_method_str = ""
                    continue

        reason_for_pause_int = 0
        while reason_for_pause_int == 0:
            reason_for_pause_int = int(input("\n 'The Reason for the Pause'\n 1) Filament Change\n 2) All others (insert magents or nuts etc.)\n"))
            if reason_for_pause_int not in [1, 2]:
                print("Invalid response.  Must be 1 or 2")
                reason_for_pause_int = 0
                continue
            if reason_for_pause_int == 1:
                reason_for_pause = "Filament Change"
            else:
                reason_for_pause = "All Others"

        unload_amount = 0
        reload_amount = 0
        purge_amount = 0
        enable_quick_purge = False
        if not pause_method.startswith("M600"):
            if reason_for_pause == "Filament Change":
                unload_amount = ""
                while unload_amount == "":
                    unload_amount = input("\n 'Unload Amount'\nHow much filament (in mm's) should be retracted to unload the extruder for the filament change.  This number will be split into segments in the gcode as a single long retraction might trip the 'excessive extrusion' warning in the firmware.\n   Enter a positive number or set to '0' to disable.\n")
                    if unload_amount == "":
                        print("Invalid response.  Must be '0' to disable, or the amount to unload.")
                        unload_amount = ""
                        continue
                    unload_amount = abs(int(unload_amount))

                if unload_amount > 0:
                    enable_quick_purge_str = ""
                    while enable_quick_purge_str == "":
                        enable_quick_purge_str = input("\n 'Quick Purge'\n Enable a quick purge before unloading.  This can help to insure that the filament doesn't get stuck in the hot end.\n  Enable quick purge?\n\n <y> Yes or <n> No\n").lower()
                        if enable_quick_purge_str not in ["y", "n"]:
                            print("Invalid response.  Must be 'y' or 'n'.")
                            enable_quick_purge_str = ""
                            continue
                        if enable_quick_purge_str == "y":
                            enable_quick_purge = True
                        else:
                            enable_quick_purge = False

                reload_amount = ""
                while reload_amount == "":
                    reload_amount = input("\n 'Reload Amount'\n How much filament (in mm's) should be pushed to reload the hot end after the filament change.  This number will be split into 150mm segments in the gcode because a single long retraction might trip the 'excessive extrusion' warning in the firmware.\n   Enter a positive number or enter '0' to disable.\n")
                    try:
                        reload_amount = int(reload_amount)
                    except:
                        print("Invalid response.  You must enter an integer.")
                        reload_amount = ""
                        continue
        if reason_for_pause == "Filament Change":
            purge_amount = None
            while purge_amount == None:
                purge_amount = input("\n 'Purge Amount'\n The purge amount of filament (in mm's) to be extruded after the pause. For most printers this is the amount of purge required for a complete a color change at the nozzle.  Changing from white generally requires at least 50mm.  Set this to '0' to disable.\n <enter the amount in mm's>\n")
                try:
                    purge_amount = int(purge_amount)
                except:
                    print("Invalid response.  Enter '0' to disable, or the amount to purge.")
                    purge_amount = None
                    continue

        if reason_for_pause == "All Others":
            extra_prime_amount = ""
            while extra_prime_amount == "":
                extra_prime_amount = input("\n 'Extra Prime Amount'\n The amount of extra prime after the nozzle returns to the print (mm's).  (At 0.2 layer height and 0.4 line width 0.5mm of 1.75 filament is 15mm of extrusion.) <enter>\n")
                if extra_prime_amount == "": extra_prime_amount = 0.0
                try:
                    extra_prime_amount = float(extra_prime_amount)
                except:
                    print("Invalid reponse.  Must be an integer or ')' to disable.")
                    extra_prime_amount = ""
                    continue
        else:
            extra_prime_amount = 0
        disarm_timeout = 0
        hold_steppers_on_str = ""
        while hold_steppers_on_str == "":
            hold_steppers_on_str = input("\n 'Hold Steppers On'\n Keep the steppers engaged so they don't lose position.  If you enter 'n' then the Stepper Disarm time will be the default disarm time within the printer (often 2 minutes). If you choose 'y' you will input the amount of time to hold the steppers on.\n <y> Yes or <n> No\n").lower()
            if hold_steppers_on_str not in ["y", "n"]:
                print("Invalid response.  Must be a 'y' or an 'n'")
                hold_steppers_on_str = ""
                continue
            if hold_steppers_on_str == "y":
                hold_steppers_on = True
            else:
                hold_steppers_on = False

            if hold_steppers_on:
                disarm_timeout_str = ""
                while disarm_timeout_str == "":
                    disarm_timeout_str = input("\n 'Disarm Timeout'\n How long to hold the steppers on (minutes).  A setting of '0' is firmware specific.  It might mean 'Disarm Right now' or 'Never Disarm'.\n  Some printers have a maximum timeout (Creality is often 4 hours (240 minutes)) <enter>\n")
                    try:
                        disarm_timeout = int(disarm_timeout_str) * 60
                    except:
                        print("Invalid response.  You must enter integer indicating the number of minutes for the timeout.\n")
                        disarm_timeout_str = ""
                        continue

        head_park_enable = False
        park_x = 0
        park_y = 0
        move_z = 1
        if not pause_method.startswith("M600"):
            head_park_enable_str = ""
            while head_park_enable_str == "":
                head_park_enable_str = input("\n 'Park the Print Head'\n Should the print head be parked away from the print?\n <y> Yes or <n> No\n").lower()
                if head_park_enable_str not in ["y", "n"]:
                    print("Invalid entry.  Must be 'y' or 'n'")
                    head_park_enable_str == ""
                    continue
                if head_park_enable_str == "y":
                    head_park_enable = True
                else:
                    head_park_enable = False

                if head_park_enable:
                    park_x = input(f"\n 'Head Park X'\n The X location to park the head. (min: {bed_min_x} to max: {bed_max_x})\n")
                    try:
                        park_x = int(park_x)
                    except:
                        print("Invalid response.  Must be a number.")
                        head_park_enable_str = ""
                        continue
                    if park_x < int(bed_min_x) or park_x > int(bed_max_x):
                        print(f"Invalid response.  Must be a number between {bed_min_x} and {bed_max_x}.")
                        head_park_enable_str = ""
                        continue

                    park_y = input(f"\n 'Head Park Y'\n The Y location to park the head. (min: {bed_min_y} to max: {bed_max_y})\n")
                    try:
                        park_y = int(park_y)
                    except:
                        print("Invalid response.  Must be a number.")
                        head_park_enable_str = ""
                        continue
                    if park_y < int(bed_min_y) or park_y > int(bed_max_y):
                        print(f"Invalid response.  Must be a number between {bed_min_y} and {bed_max_y}.")
                        head_park_enable_str = ""
                        continue

            move_z = ""
            while move_z == "":
                move_z = input("\n 'Z-up Before Parking'\n The lift of the nozzle (in mm's) above the part prior to parking. Enter '0' to disable. <enter>\n")
                try:
                    move_z = float(move_z)
                except:
                    print("Invalid entry.  Must be a number.")
                    move_z = ""
                    continue
                move_z = round(move_z, 2)

        standby_temperature = ""
        while standby_temperature == "":
            standby_temperature = input("\n 'Standby Temperature'\n This is the temperature the nozzle will hold at prior to the pause. If you will be present it can be the 'Print Temperature'.  If the printer will sit idle for a while it should wait at the Material Standby Temperature.\n <enter>\n")
            try:
                standby_temperature = int(standby_temperature)
            except:
                print("Invalid response.  Must be an integer.")
                standby_temperature = ""
                continue

        resume_print_temperature = ""
        while resume_print_temperature == "":
            resume_print_temperature = input("\n 'Resume Print Temperature'\n If you change materials you can change the print temperature for resumption of the print. <enter>\n")
            try:
                resume_print_temperature = int(resume_print_temperature)
            except:
                print("Invalid response.  Must be an integer.")
                resume_print_temperature = ""
                continue

        resume_temperature_cmd = ""
        while resume_temperature_cmd == "":
            resume_temperature_cmd = input("\n 'Resume Temperature Command'\n If the standby temperature is the same as the print temperature you can use M104.  If the standy temperature is lower then use M109 to wait for the nozzle before returning to the print.\n 1) M104\n 2) M109\n")
            if resume_temperature_cmd not in ["1", "2"]:
                print("Invalid response.  Must be an integer.")
                resume_temperature_cmd = ""
                continue
            if resume_temperature_cmd == "1":
                resume_temperature_cmd = "M104 S"
            else:
                resume_temperature_cmd = "M109 R"

        display_text_list = []
        display_text_str = None
        while display_text_str == None:
            display_text_str = input("\n 'Message to Display'\n If M117 works with your printer you can send a short message to the LCD.  M118 will always be inserted to send the same message to a print server like Octoprint.\n If you have entered multiple layers you can enter multiple messages delimited with commas.\n (If your pause command is 'M0 w/message' this will be the message.)\n Hit <enter> without any text to disable messages.\n")
            if "," in display_text_str:
                display_text_list = display_text_str.split(",")
            else:
                display_text_list.append(display_text_str)
            # Could have commas to match the layers.
        custom_gcode_before_pause = None
        while custom_gcode_before_pause == None:
            custom_gcode_before_pause = input("\n 'Gcode before Pause'\n Custom gcode before the pause.  If it is multi-line then delimit with commas.\n Hit enter without any text to disable.\n <enter>\n")

        beep_at_pause_str = ""
        while beep_at_pause_str == "":
            beep_at_pause_str = input("\n 'Beep at Pause'\n Whether to make an annoying noise or not.  Beep Length is 1.5 seconds\n <y> Yes or <n> No\n").lower()
            if beep_at_pause_str not in ["y", "n"]:
                print("Invalid response.  Must be 'y' or 'n'")
                beep_at_pause_str = ""
                continue
            if beep_at_pause_str == "y":
                beep_at_pause = True
            else:
                beep_at_pause = False

        custom_gcode_after_pause = None
        while custom_gcode_after_pause == None:
            custom_gcode_after_pause = input("\n 'Gcode after Pause'\n Custom gcode after the pause.  If it is multi-line then delimit with commas.\n Hit enter without any text to disable.\n <enter>\n")

        redo_layer_str = ""
        redo_layer_flow = 100
        while redo_layer_str == "":
            redo_layer_str = input("\n 'Redo Layer'\n Should the previous layer be redone?\n  (Some materials require this to enhance layer adhesion.  If you select to do this then next you will pick the flow rate for the 'redo layer'.)\n <y> Yes or <n> No\n").lower()
            if redo_layer_str not in ["y", "n"]:
                print("Invalid response.  Must be 'y' or 'n'.")
                redo_layer_str = ""
                continue
            if redo_layer_str == "y":
                redo_layer = True
            else:
                redo_layer = False

            if redo_layer:
                redo_layer_flow = input("'Flow Rate for the Redo Layer'\n This uses M221 to adjust the flow.  Enter the flow rate as a percentage of the normal flow rate.\n <enter>\n")
                try:
                    redo_layer_flow = int(redo_layer_flow)
                except:
                    print("Invalid response.  Must be an integer.")
                    redo_layer_flow = ""
                    continue
                #redo_layer_flow = f"M221 S{redo_layer_flow}                   ; Flow rate for the 'redo' layer\n"

    # Review the user settings
        input_str = "\nReview your Pause settings:\n\n"
        input_str += f"Pause Layer(s).............. {pause_layer_str}\n"
        input_str += f"Message(s) M117 and M118.... {str(display_text_list)}\n"
        input_str += f"Pause Method................ {pause_method}\n"
        if pause_method == "G4":
            input_str += f"G4 Dwell Time............... {dwell_time} minutes\n"
        input_str += f"Reason for Pause............ {reason_for_pause}\n"
        input_str += f"Unload Amount............... {unload_amount}\n"
        if unload_amount > 0:
            input_str += f"Enable Quick Purge.......... {enable_quick_purge}\n"
        input_str += f"Reload Amount............... {reload_amount}\n"
        if unload_amount > 0 or reload_amount > 0:
            input_str += f"Unload and Reload Speed..... {speed_unload}\n"
        input_str += f"Purge Amount................ {purge_amount}\n"
        if reason_for_pause == "All Others":
            input_str += f"Extra Prime Amount.......... {extra_prime_amount}\n"
        input_str += f"Keep Steppers Alive......... {hold_steppers_on}\n"
        if hold_steppers_on:
            input_str += f"  Disarm Timout............. {disarm_timeout}\n"
        input_str += f"Park the Print Head......... {head_park_enable}\n"
        if head_park_enable:
            input_str += f"  Park Head X............... {park_x}\n"
            input_str += f"  Park Head Y............... {park_y}\n"
            input_str += f"  Z-hop for Parking......... {move_z}\n"
        input_str += f"Standby Temperature......... {standby_temperature}\n"
        input_str += f"Resume Print Temperature Cmd {resume_temperature_cmd}\n"
        input_str += f"Resume Temperature.......... {resume_print_temperature}\n"
        if custom_gcode_before_pause != "":
            input_str += f"Custom Gcode Before Pause... {custom_gcode_before_pause}\n"
        input_str += f"Beep at Pause............... {beep_at_pause}\n"
        if custom_gcode_after_pause != "":
            input_str += f"Custom Gcode After Pause.... {custom_gcode_after_pause}\n"
        input_str += f"Redo Previous Layer......... {redo_layer}\n"
        if redo_layer:
            input_str += f"  Redo Layer Flow Rate...... {redo_layer_flow}%\n"

        response = None
        while response == None:
            response = input(input_str + "\n  <Continue?(y)  Redo?(r)  Quit?(x)>\n").lower()
            if response not in ["y", "r", "x"]:
                print("Invalid response.  The response must be either 'y', 'r', or 'x'.")
                response = None
        if response == "x":
            exit(0)
        if response == "y":
            carry_on = True
    return [
        pause_layer_list, #0
        pause_method,
        dwell_time,
        reason_for_pause,
        unload_amount,
        enable_quick_purge, #5
        reload_amount,
        speed_unload,
        purge_amount,
        extra_prime_amount,
        hold_steppers_on, #10
        disarm_timeout,
        head_park_enable,
        park_x,
        park_y,
        move_z, #15
        standby_temperature,
        resume_temperature_cmd,
        resume_print_temperature,
        custom_gcode_before_pause,
        beep_at_pause, #20
        custom_gcode_after_pause,
        redo_layer,
        redo_layer_flow,
        display_text_list ] #24

def get_m600_params(extruder_count):
    pause_method = "M600"
    print(" The parameters for M600 are dependent on what your firmware understands.\n  You will be asked to enter ALL parameters but your firmware may only accept some of them.\n")
    # M600 [B<beeps>] [E<pos>] [L<pos>] [R<temp>] [T<index>] [U<pos>] [X<pos>] [Y<pos>] [Z<pos>]
    b_param = ""
    while b_param == "":
        b_param = input(" 'Number of Beeps'\n Enter the number of times to beep.  Enter a '0' to disable.\n <enter>\n")
        try:
            b_param = int(b_param)
        except:
            print("Invalid Response.  Enter an integer.")
            b_param = ""
            continue
    e_param = ""
    while e_param == "":
        e_param = input(" 'Retract Amount'\n Retract before moving to change position.  The amount is typically your retract distance\n (enter a positive number or enter '0' to disable).\n <enter>\n")
        try:
            e_param = float(e_param)
        except:
            print("Invalid Response.  Enter a positive number.")
            e_param = ""
            continue
        if e_param < 0:
            print("Invalid Response.  Enter a positive number.")
            e_param = ""
            continue

    u_param = ""
    while u_param == "":
        u_param = input(" 'Unload Amount'\n The amount of filament required to pull the filament out of the extruder.  The amount is longer for bowden tubes.\n (enter a positive amount or enter '0' to disable).\n <enter>\n")
        try:
            u_param = float(u_param)
        except:
            print("Invalid Response.  Enter a number.")
            u_param = ""
            continue
    l_param = ""
    while l_param == "":
        l_param = input(" 'Re-load Amount'\n The amount of filament to reload in preparation of printing.  The amount is typically your retract distance (enter a negative amount or enter '0' to disable).\n <enter>\n")
        try:
            l_param = float(l_param)
        except:
            print("Invalid Response.  Enter a number.")
            l_param = ""
            continue
    r_param = ""
    while r_param == "":
        r_param = input(" 'Resume Temperature'\n The temperature to resume the print.  This is usually the print temperature but you can change it here.\n Enter a positive number.\n <enter>\n")
        try:
            r_param = int(r_param)
        except:
            print("Invalid Response.  Enter a number.")
            r_param = ""
            continue
    t_param = ""
    if extruder_count > 1:
        t_param = ""
        while t_param == "":
            t_param = input(" 'Tool Number'\n Enter the tool to effect.  This is usually '0' for the primary extruder, or '1' for the secondary extruder.\n <enter>\n")
            try:
                t_param = int(t_param)
            except:
                print("Invalid Response.  Enter a number.")
                t_param = ""
                continue
    if t_param == "": t_param = 0

    x_param = ""
    while x_param == "":
        x_param = input(" 'X Park Location'\n Enter an integer.\n<enter>\n")
        try:
            x_param = int(x_param)
        except:
            print("Invalid Response.  Enter a number.")
            x_param = ""
            continue
    y_param = ""
    while y_param == "":
        y_param = input(" 'Y Park Location'\n Enter an integer.\n<enter>\n")
        try:
            y_param = int(y_param)
        except:
            print("Invalid Response.  Enter a number.")
            y_param = ""
            continue
    z_param = ""
    while z_param == "":
        z_param = input(" 'Z hop before parking'\n The height to move the Z above the print before moving to the park position.  Enter an integer.\n<enter>\n")
        try:
            z_param = int(z_param)
        except:
            print("Invalid Response.  Enter a number.")
            z_param = ""
            continue

    if b_param == 0:
        b_param = ""
    else:
        b_param = " B" + str(b_param)

    if e_param == 0:
        e_param = ""
    else:
        e_param = " E-" + str(e_param)

    if u_param == 0:
        u_param = ""
    else:
        u_param = " U" + str(u_param)

    if l_param == 0:
        l_param = ""
    else:
        l_param = " L" + str(l_param)

    if r_param == 0:
        r_param = ""
    else:
        r_param = " R" + str(r_param)

    if t_param != "":
        t_param = " T" + str(t_param)

    if x_param != "":
        x_param = " X" + str(x_param)

    if y_param != "":
        y_param = " Y" + str(y_param)

    if z_param != "":
        z_param = " Z" + str(z_param)
    pause_method += b_param + e_param + u_param + l_param + r_param + t_param + x_param + y_param + z_param
    return pause_method

def getValue(line, param):
    if ";" in line:
        line = line.split(";")[0]
        if not line.endswith(" "):
            line += " "
    if ":" in line:
        param = param + ":"
    try:
        temp = line.split(param)[1][:-1]
        if " " in temp:
            the_value = temp.split(" ")[0]
        else:
            the_value = temp
    except:
        return None
    return float(the_value)

#  Get the X and Y values for a layer (will be used to get X and Y of the layer after the pause and of the 'redo' layer if that option is used).
def getNextXY(s_index):
    x = None
    y = None
    e = None
    is_retracted = None
    for num in range(s_index, 0, -1):
        line = lines[num]
        if line.startswith(("G0 ", "G1 ", "G2 ", "G3 ", "G92 ")):
            if " X" in line and x == None:
                x = getValue(line, "X")
            if " Y" in line and y == None:
                y = getValue(line, "Y")
            if " E" in line and e == None:
                e = getValue(line, "E")
            if re.search(r"G1 F(\d+\.\d+|\d+) E(-?\d+\.\d+|-?\d+)", line) or "G10" in line:
                if is_retracted == None:
                    is_retracted = True
            else:
                if e != None:
                    is_retracted = False
        if x != None and y != None and e != None and is_retracted != None:
            return [x, y, e, is_retracted]
    return [0, 0, 0, False]

if __name__ == "__main__":
    main(lines)