# August 2024 - GregValiant (Greg Foresi)
#
#  NOTE: You may have purge lines in your startup, or you may use this script, you should not do both.
# 'Add Purge Lines to StartUp' Allows the user to determine where the purge lines are on the build plate, or to not use purge lines if a print extends to the limits of the build surface.  Any Purge lines currently in the StartUp should be removed before using this script.  There is a wipe move after the purge lines are extruded.
# The setting 'Purge Line Length' is only avaialble for rectangular beds because I was too lazy to calculate the 45° arcs.
# 'Move to Start' takes an orthogonal path around the periphery before moving in to the print start location.  It eliminates strings across the print area.
# 'Adjust Starting E' is a correction in the E location before the skirt/brim starts.  The user can make an adjustment so that the skirt / brim / raft starts where it should.
# 'Unload' adds code to the ending gcode that will unload the filament from the machine.  The unlaod distance is broken into chunks to avoid overly long E distances.


from ..Script import Script
from UM.Application import Application
from UM.Message import Message
import re
import os

class PurgeLinesAndUnload(Script):

    def initialize(self) -> None:
        super().initialize()
        # Get the StartUp Gcode from Cura and attempt to catch if it contains purge lines.  Message the user if an extrusion is in the startup.
        curaApp = Application.getInstance().getGlobalContainerStack()
        startup_gcode = curaApp.getProperty("machine_start_gcode", "value")
        start_lines = startup_gcode.splitlines()
        for line in start_lines:
            if line.startswith("G1") and " E" in line and (" X" in line or " Y" in line):
                Message(title = "[Purge Lines and Unload]", text = "It appears that there are 'purge lines' in the StartUp Gcode.  They should be removed, or commented out, before using the 'Add Purge Lines' function of this script.").show()
                break
        self._instance.setProperty("is_rectangular", "value", True if curaApp.getProperty("machine_shape", "value") == "rectangular" else False)
        extruder = curaApp.extruderList
        #This is set in 'Add Purge Lines' and is used by 'Move to Start' to indicate which corner the nozzle is in after the purge lines
        self._purge_end_loc = None
        self._instance.setProperty("adjust_e_loc_to", "value", round(float(extruder[0].getProperty("retraction_amount", "value")) * -1), 1)

    """ Procedures and Settings:
        add_purge_lines
            purge_line_location
            purge_line_length
        move_to_start
        adjust_starting_e
            adjust_e_loc_to
        enable_unload
            unload_distance
        is_rectangular (hidden - enables 'purge_line_length' for rectangular beds only)"""

    def getSettingDataString(self):
        return """{
            "name": "Purge Lines and Unload Filament",
            "key": "PurgeLinesAndUnload",
            "metadata": {},
            "version": 2,
            "settings":
            {
            "add_purge_lines":
                {
                    "label": "Add Purge Lines to StartUp",
                    "description": "The purge lines can be left, right, front or back.  If there are purge lines present in the StartUp Gcode remove them or comment them out before using this script.  You don't want to double dip.",
                    "type": "bool",
                    "default_value": false,
                    "value": false,
                    "enabled": true
                },
                "purge_line_location":
                {
                    "label": "    Purge Line Location",
                    "description": "What edge of the build plate should have the purge lines.  If the printer is 'Elliptical' then it is assumed to be an 'Origin At Center' printer and the purge lines are 90° arcs.",
                    "type": "enum",
                    "options": {
                        "purge_left": "On left edge (Xmin)",
                        "purge_right": "On right edge (Xmax)",
                        "purge_bottom": "On front edge (Ymin)",
                        "purge_top": "On back edge (Ymax)"},
                    "default_value": "purge_left",
                    "enabled": "add_purge_lines"
                },
                "purge_line_length":
                {
                    "label": "    Purge Line Length",
                    "description": "Select 'Full' for the entire Height or Width of the build plate.  Select 'Half' for shorter purge lines.  NOTE: This has no effect on elliptic beds.",
                    "type": "enum",
                    "options": {
                        "purge_full": "Full",
                        "purge_half": "Half"},
                    "default_value": "purge_full",
                    "enabled": "add_purge_lines and is_rectangular"
                },
                "move_to_start":
                {
                    "label": "Circle around to layer start",
                    "description": "Depending on where the 'Layer Start X' and 'Layer Start Y' are for the print, the opening travel move can pass across the print area and leave a string there.  This option will generate an orthogonal path that moves the nozzle around the edges of the build plate and then comes in to the Start Point.  The nozzle will drop and touch the build plate at each stop in order to nail down the string so it doesn't follow in a straight line.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": true
                },
                "adjust_starting_e":
                {
                    "label": "Adjust Starting E location",
                    "description": "If there is a retraction after the purge lines in the Startup Gcode (like the 'Add Purge Lines' script here does) then often the skirt does not start where the nozzle starts.  It is because Cura always adds a retraction prior to the print starting which results in a double retraction.  Enabling this will allow you to adjust the starting E location and tune it so the skirt/brim/model starts right where it should.  To fix a blob enter a positive number.  To fix a 'dry start' enter a negative number.",
                    "type": "bool",
                    "default_value": false,
                    "value": false,
                    "enabled": true
                },
                "adjust_e_loc_to":
                {
                    "label": "    Starting E location",
                    "description": "This is usually a negative amount and often equal to the '-Retraction Distance'.  This 'G92 E' adjustment changes where the printer 'thinks' the end of the filament is in relation to the nozzle.  It replaces the retraction that Cura adds prior to the start of 'LAYER:0'.  If retraction is not enabled then this setting has no effect.",
                    "type": "float",
                    "unit": "mm  ",
                    "default_value": -6.5,
                    "enabled": "adjust_starting_e"
                },
                "enable_unload":
                {
                    "label": "Unload filament at print end",
                    "description": "Adds an unload script to the Ending Gcode section.  It goes in just ahead of the M104 S0.  This scripts always unloads the active extruder.  If the unload distance is greater than 150mm it will be broken into chunks to avoid tripping the excessive extrusion warning in some firmware.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": true
                },
                "unload_distance":
                {
                    "label": "    Unload Distance",
                    "description": "The amount of filament to unload.  Bowden printers usually require a significant amount and direct drives not as much.",
                    "type": "int",
                    "default_value": 440,
                    "unit": "mm  ",
                    "enabled": "enable_unload"
                },
                "is_rectangular":
                {
                    "label": "Bed is rectangular",
                    "description": "Hidden setting that disnables 'purge line length' for elliptical beds.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": false
                }
            }
        }"""

    def execute(self, data):
        # Decide which procedures to run
        if self.getSettingValueByKey("add_purge_lines"):
            self._add_purge_lines(data)
        if self.getSettingValueByKey("move_to_start"):
            self._move_to_start(data)
        if self.getSettingValueByKey("adjust_starting_e"):
            self._adjust_starting_e(data)
        if self.getSettingValueByKey("enable_unload"):
            self._unload_filament(data)
        # Format the startup and ending gcodes
        data[1] = self._format_string(data[1])
        data[len(data) - 1] = self._format_string(data[len(data) - 1])
        return data

    # Add Purge Lines to the user defined position on the build plate
    def _add_purge_lines(self, data: str):
        curaApp = Application.getInstance().getGlobalContainerStack()
        extruder = curaApp.extruderList
        retract_dist = extruder[0].getProperty("retraction_amount", "value")
        retract_enable = extruder[0].getProperty("retraction_enable", "value")
        retract_speed = extruder[0].getProperty("retraction_retract_speed", "value") * 60
        bed_shape = str(curaApp.getProperty("machine_shape", "value"))
        origin_at_center = bool(curaApp.getProperty("machine_center_is_zero", "value"))
        startup_gcode = curaApp.getProperty("machine_start_gcode", "value")
        machine_width = curaApp.getProperty("machine_width", "value")
        machine_depth = curaApp.getProperty("machine_depth", "value")
        material_diameter = extruder[0].getProperty("material_diameter", "value")
        mm3_per_mm = (material_diameter / 2)**2 * 3.14159
        init_line_width = extruder[0].getProperty("skirt_brim_line_width", "value")
        where_at = self.getSettingValueByKey("purge_line_location")
        travel_speed = extruder[0].getProperty("speed_travel", "value") * 60
        print_speed = round(extruder[0].getProperty("speed_print", "value") * 60 * .75)
        purge_extrusion_full = True if self.getSettingValueByKey("purge_line_length") == "purge_full" else False
        purge_str = ";TYPE:CUSTOM----------[Purge Lines]\nG0 F600 Z2 ; Move up\nG92 E0 ; Reset extruder\n"
        # Normal cartesian printer with origin at the left front corner
        if bed_shape == "rectangular" and not origin_at_center:
            if where_at == "purge_left":
                purge_len = int(machine_depth) - 20 if purge_extrusion_full else int(machine_depth / 2)
                y_stop = int(machine_depth - 10) if purge_extrusion_full else int(machine_depth / 2)
                purge_volume = round((init_line_width * 0.3 * purge_len) * 1.25 / mm3_per_mm, 5)
                purge_str = purge_str.replace("Lines", "Lines at MinX")
                purge_str += f"G0 F{travel_speed} X0 Y10 ; Move to start\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                purge_str += f"G1 F{print_speed} X0 Y{y_stop} E{purge_volume} ; First line\n"
                purge_str += f"G0 X3 Y{y_stop} ; Move over\n"
                purge_str += f"G1 F{print_speed} X3 Y10 E{round(purge_volume * 2,5)} ; Second line\n"
                purge_str += f"G1 F{int(retract_speed)} E{round(purge_volume * 2 - retract_dist,5)} ; Retract\n" if retract_enable else ""
                purge_str += "G0 F600 Z8 ; Move Up\nG4 S1 ; Wait for 1 second\n"
                purge_str += f"G0 F{print_speed} X3 Y20 Z0.3 ; Slide over and down\n"
                purge_str += "G0 X3 Y35 ; Wipe\n"
                self._purge_end_loc = "LF"
            elif where_at == "purge_right":
                purge_len = int(machine_depth) - 20 if purge_extrusion_full else int(machine_depth / 2)
                y_stop = 10 if purge_extrusion_full else int(machine_depth / 2)
                purge_volume = round((init_line_width * 0.3 * purge_len) * 1.25 / mm3_per_mm, 5)
                purge_str = purge_str.replace("Lines", "Lines at MaxX")
                purge_str += f"G0 F{travel_speed} X{machine_width} ; Move\nG0 Y{machine_depth - 10} ; Move\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                purge_str += f"G1 F{print_speed} X{machine_width} Y{y_stop} E{purge_volume} ; First line\n"
                purge_str += f"G0 X{machine_width - 3} Y{y_stop} ; Move over\n"
                purge_str += f"G1 F{print_speed} X{machine_width - 3} Y{machine_depth - 10} E{purge_volume * 2} ; Second line\n"
                purge_str += f"G1 F{int(retract_speed)} E{round(purge_volume * 2 - retract_dist,5)} ; Retract\n" if retract_enable else ""
                purge_str += "G0 F600 Z8 ; Move Up\nG4 S1 ; Wait for 1 second\n"
                purge_str += f"G0 F{print_speed} X{machine_width - 3} Y{machine_depth - 20} Z0.3 ; Slide over and down\n"
                purge_str += f"G0 X{machine_width - 3} Y{machine_depth - 35} ; Wipe\n"
                self._purge_end_loc = "RR"
            elif where_at == "purge_bottom":
                purge_len = int(machine_width) - 20 if purge_extrusion_full else int(machine_width / 2)
                x_stop = int(machine_width - 10) if purge_extrusion_full else int(machine_width / 2)
                purge_str = purge_str.replace("Lines", "Lines at MinY")
                purge_volume = round((init_line_width * 0.3 * purge_len) * 1.25 / mm3_per_mm, 5)
                purge_str += f"G0 F{travel_speed} X10 Y0 ; Move to start\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                purge_str += f"G1 F{print_speed} X{x_stop} Y0 E{purge_volume} ; First line\n"
                purge_str += f"G0 X{x_stop} Y3 ; Move over\n"
                purge_str += f"G1 F{print_speed} X10 Y3 E{purge_volume * 2} ; Second line\n"
                purge_str += f"G1 F{int(retract_speed)} E{round(purge_volume * 2 - retract_dist,5)} ; Retract\n" if retract_enable else ""
                purge_str += "G0 F600 Z8 ; Move Up\nG4 S1 ; Wait for 1 second\n"
                purge_str += f"G0 F{print_speed} X20 Y3 Z0.3 ; Slide over and down\n"
                purge_str += "G0 X35 Y3 ; Wipe\n"
                self._purge_end_loc = "LF"
            elif where_at == "purge_top":
                purge_len = int(machine_width - 20) if purge_extrusion_full else int(machine_width / 2)
                x_stop = 10 if purge_extrusion_full else int(machine_width / 2)
                purge_str = purge_str.replace("Lines", "Lines at MaxY")
                purge_len = int(machine_width) - 20
                purge_volume = round((init_line_width * 0.3 * purge_len) * 1.25 / mm3_per_mm, 5)
                purge_str += f"G0 F{travel_speed} Y{machine_depth} ; Ortho Move to back\n"
                purge_str += f"G0 X{machine_width - 10} ; Ortho move to start\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                purge_str += f"G1 F{print_speed} X{x_stop} Y{machine_depth} E{purge_volume} ; First line\n"
                purge_str += f"G0 X{x_stop} Y{machine_depth - 3} ; Move over\n"
                purge_str += f"G1 F{print_speed} X{machine_width - 10} Y{machine_depth - 3} E{purge_volume * 2} ; Second line\n"
                purge_str += f"G1 F{int(retract_speed)} E{round(purge_volume * 2 - retract_dist,5)} ; Retract\n" if retract_enable else ""
                purge_str += "G0 F600 Z8 ; Move Up\nG4 S1 ; Wait 1 second\n"
                purge_str += f"G0 F{print_speed} X{machine_width - 20} Y{machine_depth - 3} Z0.3 ; Slide over and down\n"
                purge_str += f"G0 X{machine_width - 35} Y{machine_depth - 3} ; Wipe\n"
                self._purge_end_loc = "RR"
        # Some cartesian printers are Origin at Center
        elif bed_shape == "rectangular" and origin_at_center:
            if where_at == "purge_left":
                purge_len = int(machine_depth - 20) if purge_extrusion_full else int(machine_depth / 2)
                y_stop = int((machine_depth / 2) - 10) if purge_extrusion_full else 0
                purge_volume = round((init_line_width * 0.3 * purge_len) * 1.25 / mm3_per_mm, 5)
                purge_str += f"G0 F{travel_speed} X-{machine_width / 2} Y-{(machine_depth / 2) - 10} ; Move to start\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                purge_str += f"G1 F{print_speed} X-{machine_width / 2} Y{y_stop} E{purge_volume} ; First line\n"
                purge_str += f"G0 X-{(machine_width / 2) - 3} Y{y_stop} ; Move over\n"
                purge_str += f"G1 F{print_speed} X-{(machine_width / 2) - 3} Y-{(machine_depth / 2) - 10} E{round(purge_volume * 2, 5)} ; Second line\n"
                purge_str += f"G1 F{int(retract_speed)} E{round(purge_volume * 2 - retract_dist, 5)} ; Retract\n" if retract_enable else ""
                purge_str += "G0 F600 Z8 ; Move Up\nG4 S1 ; Wait for 1 second\n"
                purge_str += f"G0 F{print_speed} X-{(machine_width / 2) - 3} Y-{(machine_depth / 2) - 20} Z0.3 ; Slide over and down\n"
                purge_str += f"G0 X-{(machine_depth / 2) - 3} Y-{(machine_depth / 2) - 35} ; Wipe\n"
                self._purge_end_loc = "LF"
            elif where_at == "purge_right":
                purge_len = int(machine_depth - 20) if purge_extrusion_full else int(machine_depth / 2)
                y_stop = int((machine_depth / 2) - 10) if purge_extrusion_full else 0
                purge_volume = round((init_line_width * 0.3 * purge_len) * 1.25 / mm3_per_mm, 5)
                purge_str += f"G0 F{travel_speed} X{machine_width / 2} Z1 ; Move\nG0 Y{(machine_depth / 2) - 10} Z1 ; Move to start\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                purge_str += f"G1 F{print_speed} X{machine_width / 2} Y-{y_stop} E{purge_volume} ; First line\n"
                purge_str += f"G0 X{(machine_width / 2) - 3} Y-{y_stop} ; Move over\n"
                purge_str += f"G1 F{print_speed} X{(machine_width / 2) - 3} Y{(machine_depth / 2) - 10} E{purge_volume * 2} ; Second line\n"
                purge_str += f"G1 F{int(retract_speed)} E{round(purge_volume * 2 - retract_dist,5)} ; Retract\n" if retract_enable else ""
                purge_str += "G0 F600 Z8 ; Move Up\nG4 S1 ; Wait for 1 second\n"
                purge_str += f"G0 F{print_speed} X{(machine_width / 2) - 3} Y{(machine_depth / 2) - 20} Z0.3 ; Slide over and down\n"
                purge_str += f"G0 F{travel_speed} X{(machine_depth / 2) - 3} Y{(machine_depth / 2) - 35} ; Wipe\n"
                self._purge_end_loc = "RR"
            elif where_at == "purge_bottom":
                purge_len = int(machine_width - 20) if purge_extrusion_full else int(machine_width / 2)
                x_stop = int((machine_width / 2) - 10) if purge_extrusion_full else 0
                purge_volume = round((init_line_width * 0.3 * purge_len) * 1.25 / mm3_per_mm, 5)
                purge_str += f"G0 F{travel_speed} X-{machine_width / 2 - 10} Z1 ; Move\nG0 Y-{machine_depth / 2} Z1 ; Move to start\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                purge_str += f"G1 F{print_speed} X{x_stop} Y-{machine_depth / 2} E{purge_volume} ; First line\n"
                purge_str += f"G0 X{x_stop} Y-{machine_depth / 2 - 3} ; Move over\n"
                purge_str += f"G1 F{print_speed} X-{machine_width / 2 - 10} Y-{machine_depth / 2 - 3} E{purge_volume * 2} ; Second line\n"
                purge_str += f"G1 F{int(retract_speed)} E{round(purge_volume * 2 - retract_dist,5)} ; Retract\n" if retract_enable else ""
                purge_str += "G0 F600 Z8 ; Move Up\nG4 S1 ; Wait for 1 second\n"
                purge_str += f"G0 F{print_speed} X-{(machine_width / 2) - 20} Y-{(machine_depth / 2) - 3} Z0.3 ; Slide over and down\n"
                purge_str += f"G0 F{print_speed} X-{(machine_width / 2) - 35} Y-{(machine_depth / 2) - 3} ; Wipe\n"
                self._purge_end_loc = "LF"
            elif where_at == "purge_top":
                purge_len = int(machine_width - 20) if purge_extrusion_full else int(machine_width / 2)
                x_stop = int((machine_width / 2) - 10) if purge_extrusion_full else 0
                purge_volume = round((init_line_width * 0.3 * purge_len) * 1.25 / mm3_per_mm, 5)
                purge_str += f"G0 F{travel_speed} Y{machine_depth / 2} Z1; Ortho Move to back\n"
                purge_str += f"G0 X{machine_width / 2 - 10} Z1 ; Ortho Move to start\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                purge_str += f"G1 F{print_speed} X-{x_stop} Y{machine_depth / 2} E{purge_volume} ; First line\n"
                purge_str += f"G0 X-{x_stop} Y{machine_depth / 2 - 3} ; Move over\n"
                purge_str += f"G1 F{print_speed} X{machine_width / 2 - 10} Y{machine_depth / 2 - 3} E{purge_volume * 2} ; Second line\n"
                purge_str += f"G1 F{int(retract_speed)} E{round(purge_volume * 2 - retract_dist,5)} ; Retract\n" if retract_enable else ""
                purge_str += "G0 F600 Z8 ; Move Up\nG4 S1 ; Wait for 1 second\n"
                purge_str += f"G0 F{print_speed} X{machine_width / 2 - 20} Y{machine_depth / 2 - 3} Z0.3 ; Slide over and down\n"
                purge_str += f"G0 F{print_speed} X{machine_width / 2 - 35} Y{machine_depth / 2 - 3} ; Wipe\n"
                self._purge_end_loc = "RR"
        # Elliptic printers with Origin at Center
        elif bed_shape == "elliptic":
            if where_at in ["purge_left","purge_right"]:
                radius_1 = round((machine_width / 2) - 1,2)
            elif where_at in ["purge_bottom", "purge_top"]:
                radius_1 = round((machine_depth / 2) - 1,2)
            purge_len = int(radius_1) * 3.14159 / 4
            purge_volume = round((init_line_width * 0.3 * purge_len) * 1.25 / mm3_per_mm, 5)
            if where_at == "purge_left":
                purge_str += f"G0 F{travel_speed} X-{round(radius_1 * .707, 2)} Y-{round(radius_1 * .707,2)} ; Travel\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                purge_str += f"G2 F{print_speed} X-{round(radius_1 * .707,2)} Y{round(radius_1 * .707,2)} I{round(radius_1 * .707,2)} J{round(radius_1 * .707,2)} E{purge_volume} ; First Arc\n"
                purge_str += f"G0 X-{round((radius_1 - 3) * .707,2)} Y{round((radius_1 - 3) * .707,2)} ; Move Over\n"
                purge_str += f"G3 F{print_speed} X-{round((radius_1 - 3) * .707,2)} Y-{round((radius_1 - 3) * .707,2)} I{round((radius_1 - 3) * .707,2)} J-{round((radius_1 - 3) * .707,2)} E{purge_volume * 2} ; Second Arc\n"
                purge_str += f"G1 X-{round((radius_1 - 3) * .707 - 25,2)} E{round(purge_volume * 2 + 1,5)} ; Move Over\n"
                purge_str += f"G1 F{int(retract_speed)} E{round((purge_volume * 2 + 1) - retract_dist,5)} ; Retract\n" if retract_enable else ""
                purge_str += "G0 F600 Z5 ; Move Up\nG4 S1 ; Wait 1 Second\n"
                purge_str += f"G0 F{print_speed} X-{round((radius_1 - 3) * .707 - 15,2)} Z0.3 ; Slide Over\n"
                purge_str += f"G0 F{print_speed} X-{round((radius_1 - 3) * .707,2)} ; Wipe\n"
                self.purge_end_loc = "LR"
            elif where_at == "purge_right":
                purge_str += f"G0 F{travel_speed} X{round(radius_1 * .707, 2)} Y-{round(radius_1 * .707,2)} ; Travel\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                purge_str += f"G3 F{print_speed} X{round(radius_1 * .707,2)} Y{round(radius_1 * .707,2)} I-{round(radius_1 * .707,2)} J{round(radius_1 * .707,2)} E{purge_volume} ; First Arc\n"
                purge_str += f"G0 X{round((radius_1 - 3) * .707,2)} Y{round((radius_1 - 3) * .707,2)} ; Move Over\n"
                purge_str += f"G2 F{print_speed} X{round((radius_1 - 3) * .707,2)} Y-{round((radius_1 - 3) * .707,2)} I-{round((radius_1 - 3) * .707,2)} J-{round((radius_1 - 3) * .707,2)} E{purge_volume * 2} ; Second Arc\n"
                purge_str += f"G1 X{round((radius_1 - 3) * .707 - 25,2)} E{round(purge_volume * 2 + 1,5)} ; Move Over\n"
                purge_str += f"G1 F{int(retract_speed)} E{round((purge_volume * 2 + 1) - retract_dist,5)} ; Retract\n" if retract_enable else ""
                purge_str += "G0 F600 Z5 ; Move Up\nG4 S1 ; Wait 1 Second\n"
                purge_str += f"G0 F{print_speed} X{round((radius_1 - 3) * .707 - 15,2)} Z0.3 ; Slide Over\n"
                purge_str += f"G0 F{print_speed} X{round((radius_1 - 3) * .707,2)}\n"
                self.purge_end_loc = "RR"
            elif where_at == "purge_bottom":
                purge_str += f"G0 F{travel_speed} X-{round(radius_1 * .707, 2)} Y-{round(radius_1 * .707,2)} ; Travel\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                purge_str += f"G3 F{print_speed} X{round(radius_1 * .707,2)} Y-{round(radius_1 * .707,2)} I{round(radius_1 * .707,2)} J{round(radius_1 * .707,2)} E{purge_volume} ; First Arc\n"
                purge_str += f"G0 X{round((radius_1 - 3) * .707,2)} Y-{round((radius_1 - 3) * .707,2)} ; Move Over\n"
                purge_str += f"G2 F{print_speed} X-{round((radius_1 - 3) * .707,2)} Y-{round((radius_1 - 3) * .707,2)} I-{round((radius_1 - 3) * .707,2)} J{round((radius_1 - 3) * .707,2)} E{purge_volume * 2} ; Second Arc\n"
                purge_str += f"G1 Y-{round((radius_1 - 3) * .707 - 25,2)} E{round(purge_volume * 2 + 1, 5)} ; Move Over\n"
                purge_str += f"G1 F{int(retract_speed)} E{round((purge_volume * 2 + 1) - retract_dist,5)} ; Retract\n" if retract_enable else ""
                purge_str += "G0 F600 Z5 ; Move Up\nG4 S1 ; Wait 1 Second\n"
                purge_str += f"G0 F{print_speed} Y-{round((radius_1 - 3) * .707 - 15,2)} Z0.3 ; Slide Over\n"
                purge_str += f"G0 F{print_speed} Y-{round((radius_1 - 3) * .707,2)}\n"
                self.purge_end_loc = "LF"
            elif where_at == "purge_top":
                purge_str += f"G0 F{travel_speed} X{round(radius_1 * .707, 2)} Y{round(radius_1 * .707,2)} ; Travel\n"
                purge_str += f"G0 F600 Z0.3 ; Move down\n"
                purge_str += f"G3 F{print_speed} X-{round(radius_1 * .707,2)} Y{round(radius_1 * .707,2)} I-{round(radius_1 * .707,2)} J-{round(radius_1 * .707,2)} E{purge_volume} ; First Arc\n"
                purge_str += f"G0 X-{round((radius_1 - 3) * .707,2)} Y{round((radius_1 - 3) * .707,2)} ; Move Over\n"
                purge_str += f"G2 F{print_speed} X{round((radius_1 - 3) * .707,2)} Y{round((radius_1 - 3) * .707,2)} I{round((radius_1 - 3) * .707,2)} J-{round((radius_1 - 3) * .707,2)} E{purge_volume * 2} ; Second Arc\n"
                purge_str += f"G1 Y{round((radius_1 - 3) * .707 - 25,2)} E{round(purge_volume * 2 + 1,5)} ; Move Over\n"
                purge_str += f"G1 F{int(retract_speed)} E{round((purge_volume * 2 + 1) - retract_dist,5)} ; Retract\n" if retract_enable else ""
                purge_str += "G0 F600 Z5\nG4 S1\n"
                purge_str += f"G0 F{print_speed} Y{round((radius_1 - 3) * .707 - 15,2)} Z0.3 ; Slide Over\n"
                purge_str += f"G0 F{print_speed} Y{round((radius_1 - 3) * .707,2)}\n"
                self.purge_end_loc = "RR"
        # Common ending for purge_str
        purge_str += "G0 F600 Z1 ; Move Z\n;---------------------[End of Purge]"
        # Find the insertion location in data[1]
        purge_str = self._format_string(purge_str)
        startup_section = data[1].split("\n")
        for num in range(len(startup_section) - 1, 0, -1):
            # In Absolute Extrusion mode - insert above the last G92 E0 line
            if "G92 E0" in startup_section[num]:
                insert_index = num
                break
            # In Relative Extrusion mode - insert above the M83 line
            elif "M83" in startup_section[num]:
                insert_index = num
                break
        startup_section.insert(insert_index, purge_str)
        data[1] = "\n".join(startup_section)
        return

    # Travel moves around the bed periphery to keep strings from crossing the footprint of the model.
    def _move_to_start(self, data: str) -> str:
        layer = data[2].split("\n")
        for line in layer:
            if line.startswith("G0") and " X" in line and " Y" in line:
                start_x = self.getValue(line, "X")
                start_y = self.getValue(line, "Y")
                break
        if start_x == None: start_x = 0
        if start_y == None: start_y = 0
        if self._purge_end_loc == None:
            purge_end_loc = "LF"
        else:
            purge_end_loc = self._purge_end_loc
        curaApp = Application.getInstance().getGlobalContainerStack()
        extruder = curaApp.extruderList
        bed_shape = str(curaApp.getProperty("machine_shape", "value"))
        origin_at_center = bool(curaApp.getProperty("machine_center_is_zero", "value"))
        machine_width = curaApp.getProperty("machine_width", "value")
        machine_depth = curaApp.getProperty("machine_width", "value")
        travel_speed = round(extruder[0].getProperty("speed_travel", "value") * 60)
        move_str = f";MESH:NONMESH---------[Travel to Layer Start]\nG0 F600 Z2 ; Move up\n"
        midpoint_x = machine_width / 2
        midpoint_y = machine_depth / 2
        if not origin_at_center:
            if float(start_x) <= float(midpoint_x):
                goto_str = "Lt"
            else:
                goto_str = "Rt"
            if float(start_y) <= float(midpoint_y):
                goto_str += "Frt"
            else:
                goto_str += "Bk"
        else:
            if float(start_x) <= 0:
                goto_str = "Lt"
            else:
                goto_str = "Rt"
            if float(start_y) <= 0:
                goto_str += "Frt"
            else:
                goto_str += "Bk"
        # Depending on which quadrant the XY layer start is, move around the periphery before coming in to the start position
        if bed_shape == "rectangular" and not origin_at_center:
            if purge_end_loc == "LF":
                if goto_str == "LtFrt":
                    move_str += f"G0 F{travel_speed} X5 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z1 ; Move up\n"
                    move_str += f"G0 F{travel_speed} Y5 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z1 ; Move up\n"
                elif goto_str == "RtFrt":
                    move_str += f"G0 F{travel_speed} X5 Z1; Ortho Move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z1 ; Move up\n"
                    move_str += f"G0 F{travel_speed} Y5 Z1 ; Ortho Move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z1 ; Move up\n"
                    move_str += f"G0 F{travel_speed} X{start_x} ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z1 ; Move up\n"
                elif goto_str == "LtBk":
                    move_str += f"G0 F{travel_speed} X5 ; Ortho Move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z1 ; Move up\n"
                    move_str += f"G0 F{travel_speed} Y5 Z1 ; Move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z1 ; Move up\n"
                    move_str += f"G0 F{travel_speed} Y{start_y} Z1 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z1 ; Move up\n"
                elif goto_str == "RtBk":
                    move_str += f"G0 F{travel_speed} X5 ; Move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z1 ; Move up\n"
                    move_str += f"G0 F{travel_speed} Y5 Z1 ; Move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z1 ; Move up\n"
                    move_str += f"G0 F{travel_speed} X{machine_width - 5} Z1 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z1 ; Move up\n"
                    move_str += f"G0 F{travel_speed} Y{start_y} Z1 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z1 ; Move up\n"
            elif purge_end_loc == "RR":
                if goto_str == "LtFrt":
                    move_str += f"G0 F{travel_speed} X5 Z1 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z1 ; Move up\n"
                    move_str += f"G0 F{travel_speed} Y5 Z1 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z1 ; Move up\n"
                elif goto_str == "RtFrt":
                    move_str += f"G0 F{travel_speed} X{start_x} Z1 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z1 ; Move up\n"
                    move_str += f"G0 F{travel_speed} Y5 Z1 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z1 ; Move up\n"
                elif goto_str == "LtBk":
                    move_str += f"G0 F{travel_speed} X5 Z1 ; Move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z1 ; Move up\n"
                elif goto_str == "RtBk":
                    move_str += f"G0 F{travel_speed} X{machine_width - 5} Z1 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z1 ; Move up\n"
                    move_str += f"G0 F{travel_speed} Y{start_y} Z1 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z1 ; Move up\n"
        elif bed_shape == "rectangular" and origin_at_center:
            if purge_end_loc == "LF":
                if goto_str == "LtFrt":
                    move_str += f"G0 F{travel_speed} X-{machine_width / 2 - 5} Z1 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z1 ; Move up\n"
                    move_str += f"G0 F{travel_speed} Y-{machine_depth / 2 - 5} Z1 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z1 ; Move up\n"
                elif goto_str == "RtFrt":
                    move_str += f"G0 F{travel_speed} X{machine_width / 2 - 5} Z1 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z1 ; Move up\n"
                    move_str += f"G0 F{travel_speed} Y-{machine_depth / 2 - 5} Z1 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z1 ; Move up\n"
                elif goto_str == "LtBk":
                    move_str += f"G0 F{travel_speed} X-{machine_width / 2 - 5} Z1 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z1 ; Move up\n"
                    move_str += f"G0 F{travel_speed} Y{machine_depth / 2 - 5} Z1 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z1 ; Move up\n"
                elif goto_str == "RtBk":
                    move_str += f"G0 F{travel_speed} X{machine_width / 2 - 5} Z1 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z1 ; Move up\n"
                    move_str += f"G0 F{travel_speed} Y{machine_depth / 2 - 5} Z1 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z1 ; Move up\n"
            elif purge_end_loc == "RR":
                if goto_str == "LtFrt":
                    move_str += f"G0 F{travel_speed} X{machine_width / 2 - 5} Z1 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z1 ; Move up\n"
                    move_str += f"G0 F{travel_speed} Y-{machine_depth / 2 - 5} Z1 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z1 ; Move up\n"
                elif goto_str == "RtFrt":
                    move_str += f"G0 F{travel_speed} X{machine_width / 2 - 5} Z1 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z1 ; Move up\n"
                    move_str += f"G0 F{travel_speed} Y-{machine_depth / 2 - 5} Z1 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z1 ; Move up\n"
                elif goto_str == "LtBk":
                    move_str += f"G0 F{travel_speed} X-{machine_width / 2 - 5} Z1 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z1 ; Move up\n"
                    move_str += f"G0 F{travel_speed} Y{machine_depth / 2 - 5} Z1 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z1 ; Move up\n"
                elif goto_str == "RtBk":
                    move_str += f"G0 F{travel_speed} X{machine_width / 2 - 5} Z1 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z1 ; Move up\n"
                    move_str += f"G0 F{travel_speed} Y{machine_depth / 2 - 5} Z1 ; Ortho move\n"
                    move_str += f"G0 F600 Z0 ; Nail down the string\nG0 Z1 ; Move up\n"

        elif bed_shape == "elliptic" and origin_at_center:
            radius = machine_width / 2
            offset_sin = round(2**.5 / 2 * radius, 2)
            if purge_end_loc == "LR":
                if goto_str == "LtFrt":
                    move_str += f"G0 F{travel_speed} X-{offset_sin} Z1 ; Move\nG0 Y-{offset_sin} Z1 ; Move to start\n"
                elif goto_str == "LtBk":
                    move_str += f"G2 X0 Y{offset_sin} I{offset_sin} J{offset_sin} ; Move around to start\n"
                elif goto_str == "RtFrt":
                    move_str += f"G0 F{travel_speed} X{offset_sin} Z1 ; Ortho move\nG0 Y-{offset_sin} Z1 ; Ortho move\n"
                elif goto_str == "RtBk":
                    move_str += f"G0 F{travel_speed} X{offset_sin} Z1 ; Ortho move\nG0 Y{offset_sin} Z1 ; Ortho move\n"
            elif purge_end_loc == "RR":
                if goto_str == "LtFrt":
                    move_str += f"G0 F{travel_speed} X-{offset_sin} Z1 ; Move\nG0 Y-{offset_sin} Z1 ; Move to start\n"
                elif goto_str == "LtBk":
                    move_str += f"G0 F{travel_speed} X-{offset_sin} Z1 ; Ortho move\nG0 Y{offset_sin} Z1 ; Ortho move\n"
                elif goto_str == "RtFrt":
                    move_str += f"G0 F{travel_speed} X{offset_sin} Z1 ; Ortho move\nG0 Y-{offset_sin} Z1 ; Ortho move\n"
                elif goto_str == "RtBk":
                    move_str += f"G0 F{travel_speed} X{offset_sin} Z1 ; Ortho move\nG0 Y{offset_sin} Z1 ; Ortho move\n"
            elif purge_end_loc == "LF":
                if goto_str == "LtFrt":
                    move_str += f"G0 F{travel_speed} X-{offset_sin} Z1 ; Move\nG0 Y-{offset_sin} Z1 ; Move to start\n"
                elif goto_str == "LtBk":
                    move_str += f"G0 F{travel_speed} X-{offset_sin} Z1 ; Ortho move\nG0 Y{offset_sin} Z1 ; Ortho move\n"
                elif goto_str == "RtFrt":
                    move_str += f"G0 F{travel_speed} X{offset_sin} Z1 ; Ortho move\nG0 Y-{offset_sin} Z1 ; Ortho move\n"
                elif goto_str == "RtBk":
                    move_str += f"G0 F{travel_speed} X{offset_sin} Z1 ; Ortho move\nG0 Y{offset_sin} Z1 ; Ortho move\n"
        move_str += ";---------------------[End of layer start travels]"
        startup = data[2].split("\n")
        move_str = self._format_string(move_str)
        startup.insert(2, move_str)
        data[2] = "\n".join(startup)
        return

    # Unloading a large amount of filament in a single command can trip the 'Overlong Extrusion' warning in some firmware.  Unloads longer than 150mm are split into chunks.
    def _unload_filament(self, data: str) -> str:
        extrude_speed = 3000
        unload_distance = self.getSettingValueByKey("unload_distance")
        lines = data[len(data) - 1].split("\n")
        for index, line in enumerate(lines):
            # Unload the filament just before the hot end turns off.
            if "M104 S0" in line:
                filament_str = "M83 ; [Unload] Relative extrusion\nM400 ; Complete all moves\n"
                if unload_distance > 150:
                    temp_unload = unload_distance
                    while temp_unload > 150:
                        filament_str += "G1 F" + str(int(extrude_speed)) + " E-150 ; Unload some\n"
                        temp_unload -= 150
                    if 0 < temp_unload <= 150:
                        filament_str += "G1 F" + str(int(extrude_speed)) + " E-" + str(temp_unload) + " ; Unload the remainder\nM82 ; Absolute Extrusion\nG92 E0 ; Reset Extruder\n"
                else:
                    filament_str += "G1 F" + str(int(extrude_speed)) + " E-" + str(unload_distance) + " ; Unload\nM82 ; Absolute Extrusion\nG92 E0 ; Reset Extruder\n"
                break
        lines[index] = filament_str + lines[index]
        data[len(data) - 1] = "\n".join(lines)
        return

    # Make an adjustment to the starting E location so the skirt/brim/raft starts out when the nozzle starts out.
    def _adjust_starting_e(self, data: str) -> str:
        curaApp = Application.getInstance().getGlobalContainerStack()
        extruder = curaApp.extruderList
        retract_enabled = extruder[0].getProperty("retraction_enable", "value")
        if not retract_enabled:
            return
        adjust_amt = self.getSettingValueByKey("adjust_e_loc_to")
        lines = data[1].split("\n")
        lines.reverse()
        for index, line in enumerate(lines):
            if re.search("G1 F(\d*) E-(\d.*)", line) is not None:
                lines[index] = re.sub("G1 F(\d*) E-(\d.*)", f"G92 E{adjust_amt}", line)
                lines.reverse()
                data[1] = "\n".join(lines)
                break
        return

    # Format the purge or travel-to-start strings.  No reason they shouldn't look nice.
    def _format_string(self, any_gcode_str: str):
        temp_lines = any_gcode_str.split("\n")
        gap_len = 0
        for temp_line in temp_lines:
            if ";" in temp_line and not temp_line.startswith(";"):
                if gap_len - len(temp_line.split(";")[0]) + 1 < 0:
                    gap_len = len(temp_line.split(";")[0]) + 1
        if gap_len < 30: gap_len = 30
        for temp_index, temp_line in enumerate(temp_lines):
            if ";" in temp_line and not temp_line.startswith(";"):
                temp_lines[temp_index] = temp_line.replace(temp_line.split(";")[0], temp_line.split(";")[0] + str(" " * (gap_len - len(temp_line.split(";")[0]))),1)
            # This formats lines that are commented out but contain additional comments Ex:  ;M420 ; leveling mesh
            elif temp_line.startswith(";") and ";" in temp_line[1:]:
                temp_lines[temp_index] = temp_line[1:].replace(temp_line[1:].split(";")[0], ";" + temp_line[1:].split(";")[0] + str(" " * (gap_len - 1 - len(temp_line[1:].split(";")[0]))),1)
        any_gcode_str = "\n".join(temp_lines)
        return any_gcode_str