# GregValiant

This Plugin is new in March of 2024.

    This script is for Flash Forge IDEX printers like the Creator 2 Pro and 3 Pro.  The intent is to convert a Cura slice into a gcode suitable for a Flash Forge printer.
    - The Cura M104 and M109 lines will convert from 'M104/9 T S' syntax to 'M104/9 S T' syntax.
    - The Tool Number is tracked through the gcode and the active tool number is added to all M104 and M109 lines.
    - The fan lines are changed from 'M106 P' to M106 T'
    - Cura ':TYPE:" lines will be changed to ";structure:" lines.  The gcode should preview correctly in Flash Print
    - Selecting the Print Mode (Normal, Duplicate, Mirror) will add relevant commands to the beginning of the file so the printer can adjust it's mode.
    - [Model Size XY] Normal: X_width up to build plate width.  Y depth up to build plate depth.
                      Duplicate and Mirror: the X_width limit about 45% of the width of the build plate.  Y depth up to build plate depth.
                      The gcode should be previewed in FLash Print to insure that the print will fit the bed.
    - [Model Placement]  The model must be at the 'X' midpoint of the Cura build plate.  If you have multiple models they must all be at the 'X' midpoint.
    - Duplicate and Mirror -
          All models on the build plate should be set to the same extruder

## Options

        Enable Flash Forge IDEX Converter : Activate the mode setting.
