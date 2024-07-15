# GregValiant

This Plugin is new in March of 2024.

    This script is for Sovol SV04 IDEX printer.  The intent is to convert a Cura slice into a gcode suitable for the Sovol printer.
    - M605 S0 is added before the startup when in 'Single Mode 01 and 02' or in Dual mode.  M605 S2 is added when in Copy (duplicate) and M605 S3 is added for Mirror mode.
    - Tool Start gcode macros and Tool End gcode macros are available in Dual mode.
    - The user must select the Printer definition by Mode (Normal, Duplicate, Mirror, Single 01, Single 02).

## Options

        Enable Flash Forge IDEX Converter : Activate the mode setting.
		When in Dual Mode:
			There are options for adding single startup and single ending gcode macros.  Individual commands in the text boxes are delimited with commas.  Spaces are not allowed between commands.
