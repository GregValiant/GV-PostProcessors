"""
 Copyright (c) 2025 GregValiant (Greg Foresi)
  Suitable to Prusa, Orca, and Bambu slicers
  Please note that the 'Layer Count' for the slicers is dependent on whether or not supports are enabled.  The 'Layer Count' used by this script will match the slicer preview.
  
  The script adds M117 and M118 lines at layer changes.  The form is "current_layer / total_layers | Estimated time to end" Example: '1/250 | ET 3h 45m'
    Estimated time is based on the 'Print Time' per the slicer.  The 'Time per Layer' is based on the number of gcode lines in a layer.
        (NOTE: The estimated time for certain models (like pyramids) can be off by a wide margin since the base and the top each consist of 4 lines of gcode.)
    An option is to add M73 with time and/or percentage.  When that option is chosen then M75 ad M77 are also added.
"""

import sys
import os
import math
import time
import datetime
import math

# Read the slicer gcode into memory
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
    input("'Display Info' requires that 'Add Layer Numbers' runs before it.  The script will exit.")
    exit(0)

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
# some local variables
all_at_once = True
layer_count = 0
layer_change_index_list = []
startup_end_list = []
for index, line in enumerate(lines):
    if ";TYPE:Custom" in line or "; EXECUTABLE_BLOCK_START" in line:
        startup_end_list.append(index)
        # Layer lines are added by the AddLayerNumbers post-processor
    if ";Layer:" in line:
        layer_count += 1
        layer_change_index_list.append(index)
        continue
    if "; complete_objects =" in line:
        all_at_once = bool(line.split("= ")[1][:-1])
    # Bambu and Orca
    if "; print_sequence =" in line: # ; print_sequence = by layer
        if line.split("= ")[1][:-1] == "by object":
            all_at_once = False
        else:
            all_at_once = True
    if "; model printing time:" in line:
        print_time = line.split(": ")[1].split(";")[0].strip()
    if "; estimated printing time (normal mode) =" in line:
        print_time = line.split("= ")[1].strip()
    # Get the end of the print
    if "M84" in line or "M18" in line:
        startup_end_list.append(index)

enable_script = "r"
while enable_script == "r":
    enable_script = input("\nGreg Valiant's [Display Info on LCD]\n  Displays a message on the LCD (using M117) and sends a message to a print server (using M118)\n Optionally adds M73 with print time and/or print percentage\n  (NOTE: M117, M118, M73 must be enabled in your firmware for them to work)\nYou may enter a 'q' for any setting to Quit.\nDo you wish to continue?\n <y> Yes\n <n> No\n").lower()
    if enable_script not in ["y", "n", "q"]:
        print("Invalid response.  Must be 'y' or 'n' or 'q'\n")
    if enable_script == "r":
        continue
    if enable_script == "n" or enable_script == "q":
        exit(0)

carry_on = True
while carry_on == True:
    display_option = "1"
    add_m117_line = True
    add_m118_line = True
    enable_countdown = False
    display_remaining_time = True
    display_total_layers = True

    add_m73_line = "r"
    while add_m73_line == "r" and carry_on == True:
        add_m73_line = input("'Add M73 line Adds M73 in addition to the M117.  For some firmware this will set the printers time and or percentage.  M75 is added to the beginning of the file and M77 is added to the end of the file.  You must select one or both of the Time and Percentage options that follow.\n <y> Yes\n <n> No\n").lower()
        if add_m73_line not in ["y", "n", "q"]:
            print("Invalid response.  Must be a 1 or 2 or 'q'\n")
            add_m73_line = "r"
            continue
        if add_m73_line == "q":
            carry_on = False
            break
        if add_m73_line == "y":
            add_m73_line = True
        elif add_m73_line == "n":
            add_m73_line = False
            continue
        if add_m73_line:
            add_m73_percent = "r"
            while add_m73_percent == "r" and carry_on == True:
                add_m73_percent = input("'Add M73 Print Percentage'\n <y> Yes\n <n> No\n").lower()
                if add_m73_percent not in ["y", "n", "q"]:
                    print("Invalid response.  Must be a 1 or 2 or 'q'\n")
                    add_m73_percent = "r"
                    continue
                if add_m73_percent == "q":
                    carry_on = False
                    break
                if add_m73_percent == "y":
                    add_m73_percent = True
                else:
                    add_m73_percent = False
            add_m73_time = "r"
            while add_m73_time == "r" and carry_on == True:
                add_m73_time = input("'Add M73 Print Time'\n <y> Yes\n <n> No\n").lower()
                if add_m73_time not in ["y", "n", "q"]:
                    print("Invalid response.  Must be a 'y' or 'n' or 'q'\n")
                    add_m73_time = "r"
                    continue
                if add_m73_time == "q":
                    carry_on = False
                    break
                if add_m73_time == "y":
                    add_m73_time = True
                else:
                    add_m73_time = False
    time_fudge_factor = "r"
    while time_fudge_factor == "r" and carry_on == True:
        time_fudge_factor = input("'Time Factor Adjustment'\n  Enter a fudge factor as a percentage.  The formula is 'Slicer Estimated Print Time * Fudge Factor'.  With some practice you can get the actual print time to display on the LCD very close to reality.\n If the slicer under-estimates the print time the fudge factor will be > 100.\n If the slicer over-estimates the print time the fudge factor will be < 100.\n  If the estimated print times are very close to the real print time then enter 100.\n  Enter an integer.\n  Fudge Factor %:\n").lower()
        if time_fudge_factor == "q":
            carry_on = False
            break
        try:
            time_fudge_factor = int(time_fudge_factor)
        except:
            time_fudge_factor = "r"
            print("Invalid response.  Please enter an integer between 50 and 150\n")
            continue
    time_fudge_factor /= 100
    enable_countdown = False
    carry_on = False

def main(lines):
    # Insert the post-processor name
    by_line = ";     Post Processed by Greg Valiant's [Display Info] for Prusa/Orca/Bambu\n"
    for index, line in enumerate(lines):
        if "; HEADER_BLOCK_END" in line or "; external perimeters extrusion width =" in line:
            lines.insert(index, by_line)
            break
    slice_time = convert_time_string(print_time)
    slice_time = round(slice_time * time_fudge_factor)
    actual_print_lines = layer_change_index_list[len(layer_change_index_list) - 1] - layer_change_index_list[0]

    percentage_list = [slice_time]
    for num in range(0, len(layer_change_index_list)):
        percentage_list.append(round(((actual_print_lines - layer_change_index_list[num]) / actual_print_lines) * slice_time))
    if display_option == "1":
        lines = display_progress(lines, percentage_list)
    else:
       lines = display_filename(lines, print_time)

    # Write the new file
    dest_file = open(sourceFile, "w+")
    for line in lines:
        dest_file.write(line)
    dest_file.close()
    final_file.close()

def display_progress(lines, percentage_list):
    start_index = layer_change_index_list[0]
    end_index = layer_change_index_list[len(layer_change_index_list)-1]
    if add_m73_line and add_m73_time:
        m73_time = True
    if add_m73_line and add_m73_percent:
        m73_percent = True
    if add_m73_line:
        lines[startup_end_list[0]] = "M75\n" + lines[startup_end_list[0]]
        lines[startup_end_list[len(startup_end_list) - 2]] += "M77\n"

    # Initialize some variables
    first_layer_index = start_index

    # If at least one of the settings is disabled, there is enough room on the display to display "layer"
    tindex = start_index
    m73_str = ""
    print_time_2 = convert_time_string(print_time)
    slicer_time = percentage_list[0]
    hhh = slicer_time/3600
    hr = round(hhh // 1)
    mmm = round((hhh % 1) * 60)
    orig_hhh = print_time_2/3600
    orig_hr = round(orig_hhh // 1)
    orig_mmm = math.floor((orig_hhh % 1) * 60)
    if add_m118_line:
        lines[start_index - 2] = f"M118 Your Adjusted Estimated Print Time: {hr} hr {mmm} min\n" + lines[start_index - 2]
        lines[start_index - 2] = f"M118 Slicer Estimated Print Time: {orig_hr} hr {orig_mmm} min\n" + lines[start_index - 2]
    if add_m117_line:
        lines[start_index - 2] = f"M117 ET {hr} hr {mmm} min\n" + lines[start_index - 2]
    # Add M73 line at beginning
    mins = int(60 * hr + mmm)
    if add_m73_line and (add_m73_time or add_m73_percent):
        if m73_time:
            m73_str += " R{}".format(mins)
        if m73_percent:
            m73_str += " P0"
        lines.insert(tindex + 4, "M73" + m73_str + "\n")
    # If Countdown to pause is enabled then count the pauses
    pause_str = ""
    if enable_countdown:
        pause_count = 0
        pause_setting = pause_cmd_str.upper()
        if pause_setting != "":
            pause_cmd = []
            if "," in pause_setting:
                pause_cmd = pause_setting.split(",")
            else:
                pause_cmd.append(pause_setting)
            for q in range(0, len(pause_cmd)):
                pause_cmd[q] = "\n" + pause_cmd[q]
            for num in range(2,len(lines) - 2, 1):
                for q in range(0,len(pause_cmd)):
                    if pause_cmd[q] in lines[num]:
                        pause_count += lines[num].count(pause_cmd[q], 0, len(lines[num]))
            pause_str = f"with {pause_count} pause" + ("s" if pause_count > 1 else "")
        else:
            pause_str = ""
            # This line goes in to convert seconds to hours and minutes
            lines.insert(tindex + 1, f";Cura Time Estimate: {orig_hr}hr {orig_mmm}min {pause_str}")
            lines[0] = "\n".join(lines)
            if add_m117_line:
                lines[len(lines)-1] += "M117 Orig Cura Est " + str(orig_hr) + "hr " + str(orig_mmm) + "min\n"
            if add_m118_line:
                lines[len(lines)-1] += "M118 Est w/FudgeFactor  " + str(time_fudge_factor * 100) + "% was " + str(hr) + "hr " + str(mmm) + "min\n"
    if not display_total_layers or not display_remaining_time:
        base_display_text = "layer "
    else:
        base_display_text = ""
    lines[layer_change_index_list[len(layer_change_index_list) - 1]] += ";End of Gcode" + "\n"
    #current_layer = 0
    for index, layer in enumerate(layer_change_index_list):
        current_layer = index + 1
        display_text = base_display_text
        display_text += str(index + 1)
        # add the total number of layers if this option is checked
        if display_total_layers:
            display_text += "/" + str(layer_count)
        # if display_remaining_time is checked, it is calculated in this loop
        if display_remaining_time:
            time_remaining_display = " | ET "  # initialize the time display
            m = percentage_list[index] // 60  # estimated time in minutes
            m = int(m)
            h, m = divmod(m, 60)  # convert to hours and minutes
            # add the time remaining to the display_text
            if h > 0:  # if it's more than 1 hour left, display format = xhxxm
                time_remaining_display += str(h) + "h"
                if m < 10:  # add trailing zero if necessary
                    time_remaining_display += "0"
                time_remaining_display += str(m) + "m"
            else:
                time_remaining_display += str(m) + "m"
            display_text += time_remaining_display
            # find time_elapsed at the end of the layer (used to calculate the remaining time of the next layer)

        if add_m117_line and index < len(layer_change_index_list):
            lines[layer] += "M117 " + display_text + "\n"
        if add_m118_line and index < len(layer_change_index_list):
            lines[layer] += "M118 " + display_text + "\n"
        # add M73 line
        if display_remaining_time:
            mins = int(60 * h + m)
        if add_m73_line and (add_m73_time or add_m73_percent):
            m73_str = ""
            if m73_time and display_remaining_time:
                m73_str += " R{}".format(mins)
            if m73_percent:
                m73_str += " P" + str(round(int(current_layer) / int(layer_count) * 100))
            lines[layer] = "M73 " + m73_str + "\n" + lines[layer]

    # If enabled then change the ET to TP for 'Time To Pause'
    #if enable_countdown:

    return lines

def convert_time_string(print_time: str) -> int:
    print_time_list = print_time.split(" ")
    h = int(print_time_list[0][:-1]) * 3600
    m = int(print_time_list[1][:-1]) * 60
    s = int(print_time_list[2][:-1])
    new_time = h + m + s
    return new_time

if __name__ == "__main__":
    main(lines)