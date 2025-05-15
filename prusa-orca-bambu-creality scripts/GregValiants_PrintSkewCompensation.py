
'''
Copyright (c) 2025 GregValiant (Greg Foresi)
    Suitable to Prusa, Orca, Bambu, Creality slicers

    NOTES:
    To 'initialize' the Skew Compensation you must print calibration models for each plane (XY, XZ, YZ).  They must be printed with no skew compensation. (The models can be printed together or individually but you will need all three.)
    Measure the models and choose option 2 'Enter Measurements' to enter the measurements into this script.  The measurements will be saved in a log file that is based on the printer name (EX: ENDER3.log) and will be in the same folder as this file.
    Once you have the meaurements in then you may print a model and check it for skew.
    The Skew Calibration Models are available at:
    https://github.com/GregValiant/GV-PostProcessors/tree/StartPoint/cura%20scripts/Skew%20Calibration%20Models
'''

import sys
import os
import math
import os.path

# Get the file information from the slicer
sourceFile = sys.argv[1]
final_file = open(sourceFile, "r")
lines = final_file.readlines()
final_file.close()

# Check if 'Add Layer Numbers' ran first.
layer_numbers_added = False
for line in lines:
    if "[Add Layer Numbers]" in line:
        layer_numbers_added = True
        break
if not layer_numbers_added:
    input("'Print Skew Compensation' requires that 'Add Layer Numbers' runs before it.  The script will exit.")
    exit(0)

# Whether to run the script or exit without without making changes.
response = "r"
while response == "r":
    response = input("\nGreg Valiant's      [Print Skew Compensation]\n for PrusaSlicer/OrcaSlicer/BambuStudio/CrealityPrint has started.\n Do you wish to continue?\n <y> Yes\n <n> No\n").lower()
    if response not in ["y", "n"]:
        input("Invalid response.  Enter a 'y' for Yes or an 'n' for No.")
        response = "r"
if response == "n":
    exit(0)

def main(lines):
    # Insert the post-processor name
    for index, line in enumerate(lines):
        if "; HEADER_BLOCK_END" in line or str("; external perimeters extrusion width =") in line:
            lines[index - 1] += "; Skew Compensation by Greg Valiant's [Print Skew Compensation] for Prusa/Orca/Bambu/Creality\n"
        if ";LAYER_CHANGE" in line:
            marlin_klipper_insert_pt = index
            break
    # Get the user option whether to use existing skew factors or to create new ones.
    how_to = ""
    how_to_str = ""
    while how_to_str == "":
        how_to_str = input("\n 'Print Skew Compensation'\n 1) Use existing measurements (from a log file for the Active Printer).\n 2) Use the measurements from the log file but change the Compensation Method (Slicer, Marln, Klipper)\n 3) Enter measurements and calculate new Skew Factors\n<enter>\n")
        match how_to_str:
            case "1":
                how_to = "from_existing"
            case "2":
                how_to = "edit_settings"
            case "3":
                how_to = "create_new"
            case _:
                print("Invalid response.  Must be 1, 2, or 3.")
                how_to = ""
                how_to_str = ""

    # Get the name of the active printer and use it to create the name of the log file.
    active_printer = os.environ["SLIC3R_PRINTER_MODEL"]
    script_path = os.path.dirname(__file__)
    log_file_name = script_path + str("\\") + active_printer + ".skew.log"

    if how_to == "from_existing" or how_to == "edit_settings":
        try:
            read_file = open(log_file_name, "r")
            the_log = read_file.readlines()
            read_file.close()
        except:
            input("Unable to find the log file " + str(log_file_name) + ".\n The script will exit without making changes.\n <enter>")
            exit(0)

        printer_name = the_log[0].split(":")[1].strip()
        compensation_method = the_log[1].split(":")[1].strip()
        xy_ac_dist = float(the_log[2].split(":")[1].strip())
        xy_bd_dist = float(the_log[3].split(":")[1].strip())
        xy_ad_dist = float(the_log[4].split(":")[1].strip())
        xz_ac_dist = float(the_log[5].split(":")[1].strip())
        xz_bd_dist = float(the_log[6].split(":")[1].strip())
        xz_ad_dist = float(the_log[7].split(":")[1].strip())
        yz_ac_dist = float(the_log[8].split(":")[1].strip())
        yz_bd_dist = float(the_log[9].split(":")[1].strip())
        yz_ad_dist = float(the_log[10].split(":")[1].strip())
        xy_skew_factor = float(the_log[11].split(":")[1].strip())
        xz_skew_factor = float(the_log[12].split(":")[1].strip())
        yz_skew_factor = float(the_log[13].split(":")[1].strip())
        add_settings_to_gcode = bool(the_log[14].split(":")[1].strip())
        if how_to == "edit_settings":
            compensation_method_str = ""
            while compensation_method_str == "":
                compensation_method_str = input("\n 'Compensation Method'\n    NOTE: Marlin and Klipper methods must be enabled in the printer firmware.\n\n 1) Slicer Compensation (Post-Process the Gode)\n 2) Marlin (add M852 line)\n 3) Klipper (add SET_SKEW line)\n<enter>\n")
                match compensation_method_str:
                    case "1":
                        compensation_method = "method_slicer"
                    case "2":
                        compensation_method = "method_marlin"
                    case "3":
                        compensation_method = "method_klipper"
                    case _:
                        print("Invalid response.  Must be 1, 2, or 3.")
                        compensation_method = ""
                        compensation_method_str = ""
            
    elif how_to == "create_new":
        script_settings_list = get_post_settings(lines)
        printer_name = active_printer
        compensation_method = script_settings_list[0]
        xy_ac_dist = script_settings_list[1]
        xy_bd_dist = script_settings_list[2]
        xy_ad_dist = script_settings_list[3]
        xz_ac_dist = script_settings_list[4]
        xz_bd_dist = script_settings_list[5]
        xz_ad_dist = script_settings_list[6]
        yz_ac_dist = script_settings_list[7]
        yz_bd_dist = script_settings_list[8]
        yz_ad_dist = script_settings_list[9]
        add_settings_to_gcode = script_settings_list[10]
    
        # Skew Factors
        xy_skew_factor = calculate_skew_factor(xy_ac_dist, xy_bd_dist, xy_ad_dist)
        xz_skew_factor = calculate_skew_factor(xz_ac_dist, xz_bd_dist, xz_ad_dist)
        yz_skew_factor = calculate_skew_factor(yz_ac_dist, yz_bd_dist, yz_ad_dist)

    # Make changes to the file, or add the Marlin or Klipper lines
    if compensation_method == "method_slicer":
        lines = slicer_compensation(lines, xy_skew_factor, xz_skew_factor, yz_skew_factor)
    elif compensation_method == "method_marlin":
        lines = marlin_compensation(lines, xy_skew_factor, xz_skew_factor, yz_skew_factor, marlin_klipper_insert_pt)
    elif compensation_method == "method_klipper":
        lines = klipper_compensation(lines, xy_ac_dist, xy_bd_dist, xy_ad_dist, xz_ac_dist, xz_bd_dist, xz_ad_dist, yz_ac_dist, yz_bd_dist, yz_ad_dist, xy_skew_factor, xz_skew_factor, yz_skew_factor, marlin_klipper_insert_pt)

    # If requested, add the settings to the end of the gcode file.
    if add_settings_to_gcode:
        setting_string = ";  Print Skew Compensation Settings:\n"
        setting_string += f";      xy_ac_measurement:    {xy_ac_dist}\n"
        setting_string += f";      xy_bd_measurement:    {xy_bd_dist}\n"
        setting_string += f";      xy_ad_measurement:    {xy_ad_dist}\n"
        setting_string += f";         XY skew factor:    {round(xy_skew_factor,8)}\n"
        setting_string += f";      xz_ac_measurement:    {xz_ac_dist}\n"
        setting_string += f";      xz_bd_measurement:    {xz_bd_dist}\n"
        setting_string += f";      xz_ad_measurement:    {xz_ad_dist}\n"
        setting_string += f";         XZ skew factor:    {round(xz_skew_factor,8)}\n"
        setting_string += f";      yz_ac_measurement:    {yz_ac_dist}\n"
        setting_string += f";      yz_bd_measurement:    {yz_bd_dist}\n"
        setting_string += f";      yz_ad_measurement:    {yz_ad_dist}\n"
        setting_string += f";         YZ skew factor:    {round(yz_skew_factor,8)}\n"
        lines.insert(len(lines) - 1, setting_string)

    # Write the log file.
    write_settings_to_log(log_file_name,
                   active_printer,
                   compensation_method,
                   xy_ac_dist,
                   xy_bd_dist,
                   xy_ad_dist,
                   xz_ac_dist,
                   xz_bd_dist,
                   xz_ad_dist,
                   yz_ac_dist,
                   yz_bd_dist,
                   yz_ad_dist,
                   xy_skew_factor,
                   xz_skew_factor,
                   yz_skew_factor,
                   add_settings_to_gcode)

    # Write the altered gode for the slicer
    dest_file = open(sourceFile, "w+")
    for line in lines:
        dest_file.write(line)
    dest_file.close()

def get_post_settings(lines) -> str:
    carry_on = False
    # Get the skew measurements from the user
    while carry_on == False:
        compensation_method_str = ""
        while compensation_method_str == "":
            compensation_method_str = input("\n 'Compensation Method'\n    NOTE: Marlin and Klipper methods must be enabled in the printer firmware.\n\n 1) Slicer Compensation (Post-Process the Gode)\n 2) Marlin (add M852 line)\n 3) Klipper (add SET_SKEW line)\n<enter>\n")
            match compensation_method_str:
                case "1":
                    compensation_method = "method_slicer"
                case "2":
                    compensation_method = "method_marlin"
                case "3":
                    compensation_method = "method_klipper"
                case _:
                    print("Invalid response.  Must be 1, 2, or 3.")
                    compensation_method = ""
                    compensation_method_str = ""
                    continue

        xy_ac_dist = 0.0
        while xy_ac_dist == 0.0:
            xy_ac_dist_str = input("\n 'The XY plane A to C diagonal distance'\nEnter the meaurement from the non-compensated 'XY Calibration Model'.\n (The default for a 100mm calibration model is 141.42.)\n")
            if xy_ac_dist_str == "":
                print("Invalid response.")
                continue
            try:
                xy_ac_dist = float(xy_ac_dist_str)
            except:
                xy_ac_dist = 0.0

        xy_bd_dist = 0.0
        while xy_bd_dist == 0.0:
            xy_bd_dist_str = input("\n 'The XY plane B to D diagonal distance'\nEnter the meaurement from the non-compensated 'XY Calibration Model'.\n (The default for a 100mm calibration model is 141.42.)\n")
            if xy_bd_dist_str == "":
                print("Invalid response.")
                continue
            try:
                xy_bd_dist = float(xy_bd_dist_str)
            except:
                xy_bd_dist = 0.0

        xy_ad_dist = 0.0
        while xy_ad_dist == 0.0:
            xy_ad_dist_str = input("\n 'The XY plane A to D width measurement'\nEnter the meaurement from the non-compensated 'XY Calibration Model'.\n (The default for a 100mm calibration model is 100.00.)\n")
            if xy_ad_dist_str == "":
                print("Invalid response.")
                continue
            try:
                xy_ad_dist = float(xy_ad_dist_str)
            except:
                xy_ad_dist = 0.0

        xz_ac_dist = 0.0
        while xz_ac_dist == 0.0:
            xz_ac_dist_str = input("\n 'The XZ plane A to C diagonal distance'\nEnter the meaurement from the non-compensated 'XZ Calibration Model'.\n (The default for a 100mm calibration model is 141.42.)\n")
            if xz_ac_dist_str == "":
                print("Invalid response.")
                continue
            try:
                xz_ac_dist = float(xz_ac_dist_str)
            except:
                xz_ac_dist = 0.0

        xz_bd_dist = 0.0
        while xz_bd_dist == 0.0:
            xz_bd_dist_str = input("\n 'The XZ plane B to D diagonal distance'\nEnter the meaurement from the non-compensated 'XZ Calibration Model'.\n (The default for a 100mm calibration model is 141.42.)\n")
            if xz_bd_dist_str == "":
                print("Invalid response.")
                continue
            try:
                xz_bd_dist = float(xz_bd_dist_str)
            except:
                xz_bd_dist = 0.0

        xz_ad_dist = 0.0
        while xz_ad_dist == 0.0:
            xz_ad_dist_str = input("\n 'The XZ plane A to D width measurement'\nEnter the meaurement from the non-compensated 'XZ Calibration Model'.\n (The default for a 100mm calibration model is 100.00.)\n")
            if xz_ad_dist_str == "":
                print("Invalid response.")
                continue
            try:
                xz_ad_dist = float(xz_ad_dist_str)
            except:
                xz_ad_dist = 0.0

        yz_ac_dist = 0.0
        while yz_ac_dist == 0.0:
            yz_ac_dist_str = input("\n 'The YZ plane A to C diagonal distance'\nEnter the meaurement from the non-compensated 'YZ Calibration Model'.\n (The default for a 100mm calibration model is 141.42.)\n")
            if yz_ac_dist_str == "":
                print("Invalid response.")
                continue
            try:
                yz_ac_dist = float(yz_ac_dist_str)
            except:
                yz_ac_dist = 0.0

        yz_bd_dist = 0.0
        while yz_bd_dist == 0.0:
            yz_bd_dist_str = input("\n 'The YZ plane B to D diagonal distance'\nEnter the meaurement from the non-compensated 'YZ Calibration Model'.\n (The default for a 100mm calibration model is 141.42.)\n")
            if yz_bd_dist_str == "":
                print("Invalid response.")
                continue
            try:
                yz_bd_dist = float(yz_bd_dist_str)
            except:
                yz_bd_dist = 0.0

        yz_ad_dist = 0.0
        while yz_ad_dist == 0.0:
            yz_ad_dist_str = input("\n 'The YZ plane A to D width measurement'\nEnter the meaurement from the non-compensated 'YZ Calibration Model'.\n (The default for a 100mm calibration model is 100.00.)\n")
            if yz_ad_dist_str == "":
                print("Invalid response.")
                continue
            try:
                yz_ad_dist = float(yz_ad_dist_str)
            except:
                yz_ad_dist = 0.0

        add_settings_str = None
        while add_settings_str == None:
            add_settings_str = input("\n 'Add the settings to the Gcode'\n You can add these settings to the end of the gcode so there is a record.\nEnter <y> for Yes or <n> for No\n")
            if add_settings_str not in ["y", "n"]:
                print("Invalid response.  Must be 'y' or 'n'.")
                add_settings_str = None
                continue
            if add_settings_str == "y":
                add_settings_to_gcode = True
            else:
                add_settings_to_gcode = False

        # Review the user settings
        input_str = "\nReview your Skew measurements and settings:\n\n"
        input_str += f"Compensation Method....... {compensation_method}\n"
        input_str += "XY Plane:\n"
        input_str += f"   A to D diagonal.... {str(xy_ac_dist)}\n"
        input_str += f"   B to D diagonal.... {str(xy_bd_dist)}\n"
        input_str += f"   A to D width....... {str(xy_ad_dist)}\n"
        input_str += "XZ Plane:\n"
        input_str += f"   A to D diagonal.... {str(xz_ac_dist)}\n"
        input_str += f"   B to D diagonal.... {str(xz_bd_dist)}\n"
        input_str += f"   A to D width....... {str(xz_ad_dist)}\n"
        input_str += "YZ Plane:\n"
        input_str += f"   A to D diagonal.... {str(yz_ac_dist)}\n"
        input_str += f"   B to D diagonal.... {str(yz_bd_dist)}\n"
        input_str += f"   A to D width....... {str(yz_ad_dist)}\n"
        input_str += f"Add settings to Gcode. {str(add_settings_to_gcode)}\n"

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
            compensation_method,
            xy_ac_dist,
            xy_bd_dist,
            xy_ad_dist,
            xz_ac_dist,
            xz_bd_dist,
            xz_ad_dist,
            yz_ac_dist,
            yz_bd_dist,
            yz_ad_dist,
            add_settings_to_gcode]

# Use the settings to skew the Gcode so it prints straight on the hardware.
def slicer_compensation(gcode: str, xy_skew_factor: float, xz_skew_factor: float, yz_skew_factor: float) -> str:
    # z_input is cummulative
    z_input = 0
    cur_x = 0
    cur_y = 0
    cur_z = 0
    start_here = False
    for index, line in enumerate(gcode):
        if ";Layer#:1" in line:
            start_here = True
        # Get the X, Y, Z locations
        if line.startswith(("G0", "G1")):
            cur_x = getValue(line, "X")
            cur_y = getValue(line, "Y")
            cur_z = getValue(line, "Z")

            # Reset x_input and y_input every time through
            x_input = 0
            y_input = 0

            if cur_x != None:
                x_input = cur_x
            if cur_y != None:
                y_input = cur_y
            if cur_z != None:
                z_input = cur_z

            # Calculate the skew compensation
            x_out = round(x_input - y_input * xy_skew_factor, 3)
            x_out = round(x_out - z_input * xz_skew_factor, 3)
            y_out = round(y_input - z_input * yz_skew_factor, 3)

            # If the first layer hasn't started then jump out (after tracking the XYZ).
            if not start_here:
                continue
            # Alter the current line
            if cur_x != None:
                gcode[index] = gcode[index].replace(f"X{cur_x}", f"X{x_out}")
            if cur_y != None:
                gcode[index] = gcode[index].replace(f"Y{cur_y}", f"Y{y_out}")
    return gcode

# Add a Marlin M852 line before the start of the first layer
def marlin_compensation(gcode: str, xy_skew_factor: float, xz_skew_factor: float, yz_skew_factor: float, insert_pt: int) -> str:
    # If the skew_factors are zero then return
    if xy_skew_factor == 0 and xz_skew_factor == 0 and yz_skew_factor == 0:
        cmd_line = ";No Skew Compensation Required"
    else:
        cmd_line = "M852"
    # If only the XY skew factor is > 0 the use the "S" parameter
    if xy_skew_factor and (xz_skew_factor == 0 and yz_skew_factor == 0):
        cmd_line += f" S{round(xy_skew_factor, 8)}"
    elif xy_skew_factor and (xz_skew_factor != 0 or yz_skew_factor != 0):
        cmd_line += f" I{round(xy_skew_factor,8)}"
    if xz_skew_factor != 0:
        cmd_line += f" J{round(xz_skew_factor,8)}"
    if yz_skew_factor != 0:
        cmd_line += f" K{round(yz_skew_factor,8)}"
    cmd_line += "\n"
    gcode.insert(insert_pt, cmd_line)
    return gcode

# Add a Klipper SET_SKEW line before the start of the first layer
def klipper_compensation(gcode: str, xy_ac_measurement: float, xy_bd_measurement: float, xy_ad_measurement: float, xz_ac_measurement: float, xz_bd_measurement: float, xz_ad_measurement: float, yz_ac_measurement: float, yz_bd_measurement: float, yz_ad_measurement: float, xy_skew_factor: float, xz_skew_factor: float, yz_skew_factor: float, insert_pt: int) -> str:
    # z_input is cummulative
    if xy_skew_factor == 0 and xz_skew_factor == 0 and yz_skew_factor == 0:
        cmd_line = ";No Skew Compensation Required"
    else:
        cmd_line = "SET_SKEW"
    if xy_skew_factor != 0:
        cmd_line += f" XY={xy_ac_measurement},{xy_bd_measurement},{xy_ad_measurement}"
    if xz_skew_factor != 0:
        cmd_line += f" XZ={xz_ac_measurement},{xz_bd_measurement},{xz_ad_measurement}"
    if yz_skew_factor != 0:
        cmd_line += f" YZ={yz_ac_measurement},{yz_bd_measurement},{yz_ad_measurement}"
    if cmd_line == "SET_SKEW":
        cmd_line = ";No Skew Compensation Required"
    cmd_line += "\n"
    gcode.insert(insert_pt, cmd_line)
    return gcode

def calculate_skew_factor(ac: float, bd: float, ad:float) -> str:
    ab = math.sqrt(2*ac*ac+2*bd*bd-4*ad*ad)/2
    skew_comp = math.tan(math.pi/2-math.acos((ac*ac-ab*ab-ad*ad)/(2*ab*ad)))
    return skew_comp

# Write the log file so the user doesn't have to enter settings every time.
def write_settings_to_log(
        log_file_name: str,
        active_printer: str,
        compensation_method: str,
        xy_ac_dist: float,
        xy_bd_dist: float,
        xy_ad_dist: float,
        xz_ac_dist: float,
        xz_bd_dist: float,
        xz_ad_dist: float,
        yz_ac_dist: float,
        yz_bd_dist: float,
        yz_ad_dist: float,
        xy_skew_factor: float,
        xz_skew_factor: float,
        yz_skew_factor: float,
        add_settings_to_gcode: bool
        ):
    dest_file = open(log_file_name, "w+")
    dest_file.write('"printer_name":' + str(active_printer).strip() + "\n")
    dest_file.write('"compensation_method":' + str(compensation_method).strip() + "\n")
    dest_file.write('"xy_ac_dist":' + str(xy_ac_dist) + "\n")
    dest_file.write('"xy_bd_dist":' + str(xy_bd_dist) + "\n")
    dest_file.write('"xy_ad_dist":' + str(xy_ad_dist) + "\n")
    dest_file.write('"xz_ac_dist":' + str(xz_ac_dist) + "\n")
    dest_file.write('"xz_bd_dist":' + str(xz_bd_dist) + "\n")
    dest_file.write('"xz_ad_dist":' + str(xz_ad_dist) + "\n")
    dest_file.write('"yz_ac_dist":' + str(yz_ac_dist) + "\n")
    dest_file.write('"yz_bd_dist":' + str(yz_bd_dist) + "\n")
    dest_file.write('"yz_ad_dist":' + str(yz_ad_dist) + "\n")
    dest_file.write('"xy_skew_factor":' + str(round(xy_skew_factor,8)) + "\n")
    dest_file.write('"xz_skew_factor":' + str(round(xz_skew_factor,8)) + "\n")
    dest_file.write('"yz_skew_factor":' + str(round(yz_skew_factor,8)) + "\n")
    dest_file.write('"add_settings_to_gcode":' + str(add_settings_to_gcode))
    dest_file.close()
    return None

# Helper function to pull the values from Gcode lines
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

# Register 'main' so it will run
if __name__ == "__main__":
    main(lines)