"""
 Copyright (c) 2025 GregValiant (Greg Foresi)
  Suitable to Prusa, Orca, Bambu, and Creality slicers
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
#sourceFile = "C:/Users/grego/Documents/Creality/gcode/PrusaShape.gcode"
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
    if "Creality_Print" in line:
        slicer_name = "Creality"
    if slicer_name != "":
        break
        
if slicer_name == "":
    response = ""
    while response == "":    
        response = input("The script was not able to determine the name of the slicer app.  The script should handle any of the three.\n Please enter:\n<p> for PrusaSlicer\n <o> for OrcaSlicer\n <b> for Bambu Studio\n <c> for Creality_Print\n").lower()
        if response not in ["p","o","b"]:
            print("Invalid response.  Must be <b>, <o>, <p>, <c>")
            response = ""
            continue
    if response == "b":
        slicer_name = "Bambu"
    elif response == "o":
        slicer_name = "Orca"
    elif response == "p":
        slicer_name = "Prusa"
    elif response == "c":
        slicer_name = "Creality"
        
# some local variables
all_at_once = True
layer_count = 0
layer_change_index_list = []
startup_end_list = []
allow_m73 = True
for index, line in enumerate(lines):
    if line.startswith("M73"):
        allow_m73 = False
    if ";TYPE:Custom" in line or "; EXECUTABLE_BLOCK_START" in line:
        startup_end_list.append(index)
        # Layer lines are added by the AddLayerNumbers post-processor
    if ";Layer#:" in line:
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
    if ("M84" in line or "M18" in line) and not "end_gcode" in line:
        startup_end_list.append(index)
        lines[index] += ";End of Gcode\n"

enable_script = "r"
while enable_script == "r":
    enable_script = input("\nGreg Valiant's      [Display Info on LCD]\n  PrusaSlicer/OrcaSlicer/BambuStudio/CrealityPrint\n Displays a message on the LCD (using M117) and sends a message to a print server (using M118)\n Optionally adds M73 with print time and/or print percentage\n  (NOTE: M117, M118, M73 must be enabled in your firmware for them to work)\nDo you wish to continue?\n <y> Yes\n <n> No\n").lower()
    if enable_script not in ["y", "n", "q"]:
        print("Invalid response.  Must be 'y' or 'n'\n")
        enable_script = "r"
        continue
    if enable_script == "n":
        exit(0)

carry_on = True
while carry_on == True:
    display_option = "1"
    add_m117_line = True
    add_m118_line = True
    enable_countdown = False
    display_remaining_time = True
    display_total_layers = True    
    add_m73_line = False
    add_m73_percent = False
    add_m73_time = False
    if allow_m73:
        add_m73_line = "r"
        while add_m73_line == "r" and carry_on == True:
            add_m73_line = input("\n'Add M73 line Adds M73 in addition to the M117.  For some firmware this will set the printers time and or percentage.  M75 is added to the beginning of the file and M77 is added to the end of the file.  You must select one or both of the Time and Percentage options that follow.\n <y> Yes\n <n> No\n").lower()
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
                    add_m73_percent = input("\n'Add M73 Print Percentage'\n <y> Yes\n <n> No\n").lower()
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
                    add_m73_time = input("\n'Add M73 Print Time'\n <y> Yes\n <n> No\n").lower()
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
        time_fudge_factor = input("\n'Time Factor Adjustment'\n  Enter a fudge factor as a percentage.  The formula is 'Slicer Estimated Print Time * Fudge Factor'.  With some practice you can get the actual print time that displays very close to reality.\n If the slicer under-estimates the print time the fudge factor will be > 100.\n If the slicer over-estimates the print time the fudge factor will be < 100.\n  If the estimated print times are very close to the real print time then enter 100.\n  <Enter an integer for Fudge Factor %>\n").lower()
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
    by_line = ";     Post Processed by Greg Valiant's [Display Info] for Prusa/Orca/Bambu/Creality\n"
    for index, line in enumerate(lines):
        if "; HEADER_BLOCK_END" in line or "; external perimeters extrusion width =" in line:
            lines[index - 1] += by_line
            break
    slice_time = convert_time_string(print_time)
    slice_time = round(slice_time * time_fudge_factor)
    actual_print_lines = layer_change_index_list[len(layer_change_index_list) - 1] - layer_change_index_list[0]

    # Calculate the time of each layer using general numbers to figure out what percentage of the overall print time each layer takes
    m118_list = []    
    time_list = []
    prev_x = 0
    prev_y = 0
    cur_x = 0
    cur_y = 0
    print_speed = 50
    calc_print_time = 0
    layer_time = 0
    for index, line in enumerate(lines):
        if line[0:3] in ["G0 ","G1 ","G2 ","G3 "]:
            if getValue(line, "F") is not None:
                print_speed = getValue(line, "F") / 60
            if getValue(line, "X") is not None:
                cur_x = getValue(line, "X")
            if getValue(line, "Y") is not None:
                cur_y = getValue(line, "Y")
            layer_time += (getDistance(prev_x, prev_y, cur_x, cur_y)) / print_speed
            prev_x = cur_x
            prev_y = cur_y
        if ";Layer#:" in line:
            if line.endswith("0\n"):
                print("Working on " + line[:-1])
            calc_print_time += layer_time
            time_list.append(round(calc_print_time))
            layer_time = 0
    # Add the number for first layer
    calc_print_time += layer_time
    time_list.append(round(calc_print_time))
    
    # Calculate the numbers for the M117 and M118 insertions, and for the Time Elapsed lines.
    elapsed_times = []
    end_time = round(calc_print_time)
    for index, tl in enumerate(time_list):
        m118_list.append(round(slice_time - ((tl/end_time) * slice_time)))
        elapsed_times.append(round((tl/end_time) * slice_time))
    
    # Add the Time Elapsed line to the gcode
    num = 2
    for index, line in enumerate(lines):
        if f";Layer#:{num}\n" in line:
            lines[index - 1] += f";Time_Elapsed:{round(elapsed_times[num - 1])}\n"
            num += 1
            
    # Send the m118_list to Display_Progress
    lines = display_progress(lines, m118_list)
    
    # Send the file back to the slicer as it was received, with each line a separate item in the lines list
    for index, line in enumerate(lines):
        if "\n" in line[0:-1]:
            lines[index] = line[:-1]
            temp = lines.pop(index)
            temp1 = temp.split("\n")
            temp1.reverse()
            for n_line in temp1:
                lines.insert(index, n_line + "\n")
    print("Writing file...")
    # Write the new file
    #dest_file = open("C:/Users/grego/Documents/Creality/gcode/DisplayInfoB.gcode", "w+")
    dest_file = open(sourceFile, "w+")
    for line in lines:
        dest_file.write(line)
    dest_file.close()
    final_file.close()

def display_progress(lines, m118_list):
    start_index = layer_change_index_list[0]
    end_index = layer_change_index_list[len(layer_change_index_list)-1]
    if add_m73_line and add_m73_time:
        m73_time = True
    if add_m73_line and add_m73_percent:
        m73_percent = True
    if add_m73_line:
        lines[startup_end_list[0]] = "M75\n" + lines[startup_end_list[0]]
        lines[startup_end_list[len(startup_end_list) - 3]] += "M77\n"

    # Initialize some variables
    first_layer_index = start_index

    # If at least one of the settings is disabled, there is enough room on the display to display "layer"
    tindex = start_index
    m73_str = ""
    print_time_2 = convert_time_string(print_time)
    slicer_time = m118_list[0]
    hhh = slicer_time/3600
    hr = round(hhh // 1)
    mmm = math.floor((hhh % 1) * 60)
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
        lines[tindex + 3] += "M73" + m73_str + "\n"
    
    if not display_total_layers or not display_remaining_time:
        base_display_text = "layer "
    else:
        base_display_text = ""
    
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
            m = m118_list[index] // 60  # estimated time in minutes
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
    return lines

def convert_time_string(print_time: str) -> int:
    print_time_list = print_time.split(" ")
    h = 0
    m = 0
    s = 0
    for t_line in print_time_list:
        if "h" in t_line:
            h = int(t_line[:-1]) * 3600
        elif "m" in t_line:
            m = int(t_line[:-1]) * 60
        elif "s" in t_line:
            s = int(t_line[:-1])
    new_time = h + m + s
    return new_time

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

def getDistance(prev_x, prev_y, cur_x, cur_y):
    leg_x = cur_x - prev_x
    leg_y = cur_y - prev_y
    hyp = ((leg_x**2) + (leg_y**2))**.5
    return hyp

if __name__ == "__main__":
    main(lines)