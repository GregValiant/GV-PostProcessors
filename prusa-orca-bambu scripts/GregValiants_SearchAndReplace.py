# Copyright (c) 2025 GregValiant (Greg Foresi)
#  Suitable to Prusa, Orca, and Bambu slicers
#  Search and Replace through the gcode or ranges of layers.
#  Regex searches are an option.

import sys
import re
import os

sourceFile = sys.argv[1]
final_file = open(sourceFile, "r")
lines = final_file.readlines()
slicer_name = ""

# If Add Layer Numbers didn't run first then exit
layer_numbers_added = False
for line in lines:
    if "[Add Layer Numbers]" in line:
        layer_numbers_added = True
        break
if not layer_numbers_added:
    input("'Search and Replace' requires that 'Add Layer Numbers' runs before it.  The script will exit.")
    exit(0)

response = "r"
while response == "r":
    response = input("\nGreg Valiants [Search and Replace]\nfor Prusa/Orca/Bambu has started.\nDo you wish to Continue?\n <y> Yes\n <n> No\n").lower()
    if response not in ["y", "n"]:
        print("The response must be 'y' or 'n'.  Try again.")
        response = "r"
        continue
    if response == "n":
        exit(0)
    
def main():
    # Get the layer count and number of raft layers
    slicer_settings = get_slicer_settings()
    layer_count = slicer_settings[0]
    slicer_name = slicer_settings[1]
    by_line = ";     Post Processed by Greg Valiant's [Search and Replace] for Prusa/Orca/Bambu\n"
    for index, line in enumerate(lines):
        if "; HEADER_BLOCK_END" in line or "; external perimeters extrusion width =" in line:
            lines.insert(index, by_line)
            break
    post_settings = get_post_settings(layer_count)
    if post_settings == False:
        exit(0)
    search_string = post_settings[0]
    replace_string = post_settings[1]
    is_regex = post_settings[2]
    enable_range_search = post_settings[3]
    start_layer = post_settings[4]
    end_layer = post_settings[5]
    first_instance_only = post_settings[6]
    ignore_startup = post_settings[7]
    ignore_end = post_settings[8]
    
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
        elif ";END gcode" in lines[num] or "; filament end gcode" in lines[num]:
            data_list.append(num + 1)
            continue
        elif "M84" in lines[num] or "printer finish" in lines[num]:
            data_list.append(num + 2)
            break
    try:
        if start_layer == 1:
            if ignore_startup:
                start_index = data_list[2] - 1
            else:
                start_index = data_list[1] - 1
        elif start_layer > 1:
            start_index = data_list[start_layer + 1] - 1

        if end_layer == layer_count:
            if ignore_end:
                end_index = data_list[len(data_list) - 2] - 1
            else:
                end_index = data_list[len(data_list) - 1] - 1
        elif end_layer < layer_count:
            end_index = data_list[end_layer + 1] - 1
    except:
        pass
        
    # Make replacements
    replaced_one = False
    if not is_regex:
        search_string = re.escape(search_string)
    search_regex = re.compile(search_string)

    for index, line in enumerate(lines):
        if index < start_index or index > end_index:
            continue
        if first_instance_only:
            if re.search(search_regex, line) and replaced_one == False:
                lines[index] = re.sub(search_regex, replace_string, line, 1)
                replaced_one = True
                break
        else:
            if re.search(search_regex, line):
                lines[index] = re.sub(search_regex, replace_string, line)

    # Write the new file
    dest_file = open(sourceFile, "w+")
    for line in lines:
        dest_file.write(line)
    dest_file.close()
    final_file.close()
    
def get_post_settings(layer_count):
    response = "r"
    while response == "r":
        try:
            search_string = input("\nEnter the Search String (This is case specific) <Enter>\n")
        except:
            search_string = ""

        try:
            replace_string = input("\nEnter the Replacement String <Enter>\n")
        except:
            replace_string = ""

        try:
            is_regex = input("\nIs the Search String a 'Regular Expression'?\n <y> is Regular Expression\n <n> No (normal text search)\n").lower()
            if is_regex == "y":
                is_regex = True
            else:
                is_regex = False
        except:
            is_regex = False

        try:
            enable_range_search_str = input("\nSearch all the layers or a Range of Layers\n <y> Yes all layers\n <n> Range of Layers\n").lower()
            if enable_range_search_str == "n":
                enable_range_search = True
            else:
                enable_range_search = False
        except:
            enable_range_search = False

        start_layer = 1
        end_layer = layer_count
        try:
            if enable_range_search:
                start_layer = int(input("\nWhat is the Start Layer of the search range? <enter>\n"))
                end_layer = int(input("\nWhat is the End Layer of the search range? (top layer is " + str(layer_count) + ") <enter>\n"))
        except:
            start_layer = 1
            end_layer = layer_count

        ignore_startup = True
        ignore_end = True
        try:
            first_instance_only_str = input("\nReplace the first instance only?\n <y> Yes\n <n> No\n").lower()
            if first_instance_only_str == "y":
                first_instance_only = True
            else:
                first_instance_only = False
        except:
            first_instance_only = False

        try:
            if not enable_range_search or start_layer == 1:
                ignore_startup_str = input("\nIgnore StartUp Gcode?\n <y> Yes\n <n> No\n").lower()
                if ignore_startup_str == "y":
                    ignore_startup = True
                else:
                    ignore_startup = False
        except:
            ignore_startup = True

        try:
            if not enable_range_search and end_layer == layer_count:
                ignore_end_str = input("\nIgnore the Ending G-Code?\n <y> Yes\n <n> No\n").lower()
                if ignore_end_str == "y":
                    ignore_end = True
                else:
                    ignore_end = False
        except:
            ignore_end = True

        try:
            msg_str = "Review your Search and Replace settings\n\n"
            msg_str += "Search String......................: " + str(search_string) + "\n"
            msg_str += "Replace With.......................: " + str(replace_string) + "\n"
            msg_str += "Is Regex?..........................: " + str(is_regex) + "\n"
            msg_str += "Enable a Layer Range Search?.......: " + str(enable_range_search) + "\n"
            if enable_range_search:
                msg_str += "    Start Layer....................: " + str(start_layer) + "\n"
                msg_str += "    End Layer......................: " + str(end_layer) + "\n"
            msg_str += "Replace the First Instance only?...: " + str(first_instance_only) + "\n"
            msg_str += "Ignore Startup G-Code?.............: " + str(ignore_startup) + "\n"
            msg_str += "Ignore Ending G-Code?..............: " + str(ignore_end) + "\n\n"
            response = input("\n" + msg_str + " <y> Continue\n <r> Redo\n <x> Quit\n")
            if response == "x":
                return False
        except:
            response = input("There was an error.  The scipt will exit.\n <enter>\n")
            return False    
    return search_string, replace_string, is_regex, enable_range_search, start_layer, end_layer, first_instance_only, ignore_startup, ignore_end

def get_slicer_settings():
    layer_count = 0
    for line in lines:
        if "Prusa" in line:
            slicer_name = "Prusa"
        if "Orca" in line:
            slicer_name = "Orca"
        if "Bambu" in line:
            slicer_name = "Bambu"
        if ";Layer:" in line:
            layer_count += 1
    return layer_count, slicer_name

if __name__ == "__main__":
    main()