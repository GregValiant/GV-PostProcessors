# Copyright (c) 2025 GregValiant

import sys
import re
import os

sourceFile = sys.argv[1]
final_file = open(sourceFile, "r")
lines = final_file.readlines()
try:
    response = input("Greg Valiants [Search and Replace] for Prusa/Orca has started.\nDo you wish to continue? (y,n).\n").lower()
except:
    response = "n"
if response == "n":
    exit(0)

# Get the layer count and number of raft layers
raft_layers = 0
layer_count = 0
for line in lines:
    if ";LAYER_CHANGE" in line:
        layer_count += 1
    if "; raft_layers =" in line:
        raft_layers = int(line.split("= ")[1])

lines.insert(1, ";\n;   Post Processed by GregValiant [Search and Replace] for Prusa/Orca")
response = "r"
while response == "r":
    try:
        search_string = input("Enter the Search String (This is case specific) <Enter>\n")
    except:
        search_string = ""

    try:
        replace_string = input("Enter the Replacement String <Enter>\n")
    except:
        replace_string = ""

    try:
        is_regex = input("Is the Search String a 'Regular Expression'? <y,n>\n").lower()
        if is_regex == "y":
            is_regex = True
        else:
            is_regex = False
    except:
        is_regex = False

    try:
        enable_range_search_str = input("Search all the layers? <y>  or a Range of Layers? <n>\n").lower()
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
            start_layer = int(input("What is the Start Layer of the search range? <enter>\n"))
            end_layer = int(input("What is the End Layer of the search range? (top layer is " + str(layer_count) + ") <enter>\n"))
    except:
        start_layer = 1
        end_layer = layer_count

    ignore_startup = True
    ignore_end = True
    try:
        first_instance_only_str = input("Replace the first instance only? <y,n>\n").lower()
        if first_instance_only_str == "y":
            first_instance_only = True
        else:
            first_instance_only = False
    except:
        first_instance_only = False

    try:
        if not enable_range_search or start_layer == 1:
            ignore_startup_str = input("Ignore StartUp Gcode? <y,n>\n").lower()
            if ignore_startup_str == "y":
                ignore_startup = True
            else:
                ignore_startup = False
    except:
        ignore_startup = True

    try:
        if not enable_range_search and end_layer == layer_count:
            ignore_end_str = input("Ignore the Ending G-Code? <y,n>\n").lower()
            if ignore_end_str == "y":
                ignore_end = True
            else:
                ignore_end = False
    except:
        ignore_end = True

    try:
        msg_str = "The current Search and Replace settings are:\n\n"
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
        response = input("\n" + msg_str + " <Continue?(y)  Redo(r)  Quit(x)\n")
        if response == "x":
            exit(0)
    except:
        response = input("There was an error.  The scipt will exit. <enter>\n")
        exit(0)

data_list = [0]
for index, line in enumerate(lines):
    if ";TYPE:Custom" in line:
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
#[0, 17, 43, 1279, 1982, 2604, 3286, 3456, 3618, 3790, 3952, 4124, 4286, 4458, 4620, 4792, 4954, 5126, 5288, 5460, 5622, 5794, 5956, 6128, 6290, 6462, 6624, 6946, 7281, 7901, 8583, 9205, 9605, 9614]
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
    # First_instance only
    if first_instance_only:
        if re.search(search_regex, line) and replaced_one == False:
            lines[index] = re.sub(search_regex, replace_string, line, 1)
            replaced_one = True
            break

    # All instances
    else:
        if re.search(search_regex, line):
            lines[index] = re.sub(search_regex, replace_string, line)

lines.append("\n;...Start: " + str(start_index) + " ...End Index: " + str(end_index) + "  StartLayer: " + str(start_layer) + "\n")
lines.append("\n" + str(data_list) + "\n")
# Write the new file
dest_file = open(sourceFile, "w+")
for line in lines:
    dest_file.write(line)
dest_file.close()
final_file.close()