# By GregValiant (Greg Foresi) February 1, 2025
# This script will:
#    Add layer number lines below the "LAYER_CHANGE" lines.  The layer numbers coincide with the preview layers.
#    Remove empty lines.

import sys
import re
import os

# Get the file information from the slicer
sourceFile = sys.argv[1]
final_file = open(sourceFile, "r")
lines = final_file.readlines()

# Let the user decide to run the script or exit without running.
try:
    response = input("\nGreg Valiants [Add Layer Numbers] for Prusa/Orca has started.  Layer numbers are required for some post-processors.  Layers are numbered as per the preview and start with ';Layer:1'.\nDo you wish to continue? (y) or (n).\n").lower()
except:
    response = "n"
if response == "n":
    exit(0)
# Insert the post-processor name
lines.insert(1, ";   Post Processed by Greg Valiant's [Add Layer Numbers] for Prusa/Orca")

# Start to do the actual post-processing

lay_num = 1

# Add the ';layer:#' lines below the 'LAYER_CHANGE' lines
for index, line in enumerate(lines):
    if line == ";LAYER_CHANGE\n":
        lines[index] = line + f";Layer:{lay_num}\n"
        lay_num += 1
    # Format the 'HEIGHT' lines so they are rounded to 3 decimal places
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