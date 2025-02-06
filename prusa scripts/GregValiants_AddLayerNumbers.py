# By GregValiant
# This script will:
#    Add layer numbers to the "LAYER_CHANGE" lines.  Raft layers get negative numbers and the actual model starts on layer 1.
#    Remove empty lines.
#    Remove lines that start with "WIPE", "WIDTH", "BEFORE", and "AFTER".
#  The results are a gcode file approximately 20% smaller

import sys
import re
import os

# Get the file information from the slicer
sourceFile = sys.argv[1]
final_file = open(sourceFile, "r")
lines = final_file.readlines()
try:
    response = input("\nGreg Valiants [Add Layer Numbers] for Prusa/Orca has started.  Layer numbers are required for some post-processors.  Layers are numbered as per the preview and start with ';Layer:1'.\nDo you wish to continue? (y,n).\n").lower()
except:
    response = "n"
if response == "n":
    exit(0)
# Insert the post-processor name
lines.insert(1, ";\n;   Post Processed by Greg Valiant's [Add Layer Numbers] for Prusa/Orca")
"""
Start to do the actual post-processing

"""
lay_num = 1

# Add the ';layer:#' lines below the 'LAYER_CHANGE' lines
for index, line in enumerate(lines):
    if line == ";LAYER_CHANGE\n":
        lines[index] = line + f";Layer:{lay_num}\n"
        lay_num += 1
        # Even if raft is enabled don't allow a ;Layer:0
        #if lay_num == 0: lay_num = 1
    # Format the 'HEIGHT' lines so they are to 3 decimal places
    if line.startswith(";HEIGHT:"):
        hgt = float(line.split(":")[1])
        lines[index] = f";HEIGHT:{round(hgt, 3)}\n"
    # Remove blank lines
    if line == "\n":
        lines[index] = ""
# Create the destination file and write the new code to it
dest_file = open(sourceFile, "w+")
for line in lines:
    dest_file.write(line)
dest_file.close()
final_file.close()