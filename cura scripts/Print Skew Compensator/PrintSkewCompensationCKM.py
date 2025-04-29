"""
Designed by GregValiant (Greg Foresi) in April of 2025.
The script requires that a calibration print is done for each axis plane (XY, XZ, YZ) and it is measured.
There are three main options:
    'Cura':
        Will go through the gcode and adjust it per the skew factors.
    'Marlin' and 'Klipper':
        Will use the entered values to calculate the skew factors and then enter them into the StartUp Gcode.  For 'Marlin' that is an M852 line.  'Klipper' is 'SET_SKEW'.
"""

from UM.Application import Application
from ..Script import Script
from UM.Message import Message
from UM.Logger import Logger
import re
import math

class PrintSkewCompensationCKM(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name":"Print Skew Compensation CKM",
            "key": "PrintSkewCompensationCKM",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "enable_print_skew_comp":
                {
                    "label": "Enable Print Skew Comp",
                    "description": "Enable the script",
                    "type": "bool",
                    "default_value": true,
                    "enabled": true
                },
                "compensation_for":
                {
                    "label": "Compensation for...",
                    "description": "Select 'Cura' to directly alter the gcode.  Select 'Marlin' to calculate the M852 parameters and enter them into the StartUp Gcode.  Select 'Klipper' to calculate the Skew parameters and insert 'SET_SKEW' into the StartUp Gcode.  Both 'Marlin' and 'Klipper' are firmware specific.",
                    "type": "enum",
                    "options": {
                        "method_cura": "Cura",
                        "method_marlin": "Marlin",
                        "method_klipper": "Klipper"
                        },
                    "default_value": "method_cura",
                    "enabled": "enable_print_skew_comp"
                },
                "enable_xy_skew":
                {
                    "label": "Enable XY plane Skew Compensation",
                    "description": "Compensate skewing in the XY plane.  The is the 'Top View' in Cura.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": "enable_print_skew_comp"
                },
                "xy_AC_measurement":
                {
                    "label": "    A to C diagonal",
                    "description": "The distance measured across the A to C diagonal (lower left to upper right) of the calibration print.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 141.4213562,
                    "maximum_value": 250.0,
                    "minimum_value": 100,
                    "enabled": "enable_print_skew_comp and enable_xy_skew"
                },
                "xy_BD_measurement":
                {
                    "label": "    B to D diagonal",
                    "description": "The distance measured across the B to D diagonal (upper left to lower right) of the calibration print",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 141.4213562,
                    "maximum_value": 250.0,
                    "minimum_value": 100,
                    "enabled": "enable_print_skew_comp and enable_xy_skew"
                },
                "xy_AD_measurement":
                {
                    "label": "    A to D distance",
                    "description": "The distance across the print.  The model was designed to 100mm but enter the measurement.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 100.0,
                    "maximum_value": 300.0,
                    "minimum_value": 25,
                    "enabled": "enable_print_skew_comp and enable_xy_skew"
                },
                "enable_xz_skew":
                {
                    "label": "Enable XZ plane Skew Compensation",
                    "description": "Compensate skewing in the XZ plane.  The is the 'Front View' in Cura.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": "enable_print_skew_comp"
                },
                "xz_AC_measurement":
                {
                    "label": "    A to C diagonal",
                    "description": "The distance measured across the A to C diagonal (lower left to upper right) of the calibration print.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 141.4213562,
                    "maximum_value": 250.0,
                    "minimum_value": 100,
                    "enabled": "enable_print_skew_comp and enable_xz_skew"
                },
                "xz_BD_measurement":
                {
                    "label": "    B to D diagonal",
                    "description": "The distance measured across the B to D diagonal (upper left to lower right) of the calibration print",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 141.4213562,
                    "maximum_value": 250.0,
                    "minimum_value": 100,
                    "enabled": "enable_print_skew_comp and enable_xz_skew"
                },
                "xz_AD_measurement":
                {
                    "label": "    A to D distance",
                    "description": "The distance across the print.  The model was designed to 100mm but enter the measurement.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 100.0,
                    "maximum_value": 300.0,
                    "minimum_value": 25,
                    "enabled": "enable_print_skew_comp and enable_xz_skew"
                },

                "enable_yz_skew":
                {
                    "label": "Enable YZ plane Skew Compensation",
                    "description": "Compensate skewing in the XZ plane.  The is the 'Side View' in Cura.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": "enable_print_skew_comp"
                },
                "yz_AC_measurement":
                {
                    "label": "    A to C diagonal",
                    "description": "The distance measured across the A to C diagonal (lower left to upper right) of the calibration print.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 141.4213562,
                    "maximum_value": 250.0,
                    "minimum_value": 100,
                    "enabled": "enable_print_skew_comp and enable_yz_skew"
                },
                "yz_BD_measurement":
                {
                    "label": "    B to D diagonal",
                    "description": "The distance measured across the B to D diagonal (upper left to lower right) of the calibration print",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 141.4213562,
                    "maximum_value": 250.0,
                    "minimum_value": 100,
                    "enabled": "enable_print_skew_comp and enable_yz_skew"
                },
                "yz_AD_measurement":
                {
                    "label": "    A to D distance",
                    "description": "The distance across the print.  The model was designed to 100mm but enter the measurement.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 100.0,
                    "maximum_value": 300.0,
                    "minimum_value": 25,
                    "enabled": "enable_print_skew_comp and enable_yz_skew"
                },
                "add_settings_to_gcode":
                {
                    "label": "Add settings to the gcode",
                    "description": "Whether to make a record of these settings in the gcode file.  They go in at the end of the file.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "enable_print_skew_comp"
                }
            }
        }"""

    def execute(self, data: list):

        """
        For Cura, this script compensates skew in the print by adjusting the X and Y parameters in each line of the gcode.
        For Marlin an M825 I J K S line is added to the startup
        for Klipper a SET_SKEW XY=, X=, YZ= line is added to the startup
        params:
            enable_print_skew_comp:  Whether the script will run or not.
            compensation_for:  'Cura' will adjust the gcode of the print.  'Marlin' adds M852 skew correction line to the startup gcode.  'Klipper' adds SET_SKEW to the startup gcode
            enable_xy_skew:   Whether to apply the XY (Top View) correction.
            xy_AC_measurement:  The lower-left to upper-right cross corner measurement of the calibration print
            xy_BD_measurement:  The upper-left to lower-right cross corner measurement of the calibration print
            xy_AD_measurement:  The width of the calibration print
            enable_xz_skew:   Whether to apply the XZ (Front View) correction.
            xz_AC_measurement:  The lower-left to upper-right cross corner measurement of the calibration print
            xz_BD_measurement:  The upper-left to lower-right cross corner measurement of the calibration print
            xz_AD_measurement:  The width of the calibration print
            enable_yz_skew:   Whether to apply the YZ (Side View) correction.
            yz_AC_measurement:  The lower-left to upper-right cross corner measurement of the calibration print
            yz_BD_measurement:  The upper-left to lower-right cross corner measurement of the calibration print
            yz_AD_measurement:  The width of the calibration print.
        """

        # Exit if the post processor is not enabled
        if not bool(self.getSettingValueByKey("enable_print_skew_comp")):
            data[0] += ";  [Print Skew Compensation] not enabled\n"
            return data

        # Exit if the gcode has already been post-processed
        if ";POSTPROCESSED" in data[0]:
            return data

        # Notify the user that this script should run first
        scripts = Application.getInstance().getGlobalContainerStack().getMetaDataEntry("post_processing_scripts")
        scripts = scripts.replace("\\", "")
        script_list = scripts.split("\n")
        for s_index, script in enumerate(script_list):
            script_list[s_index] = script.split("]")[0]
            script_list[s_index] = script_list[s_index].replace("[", "")
        for s_index, script in enumerate(script_list):
            if "PrintSkewCompensation" in script and s_index != 0:
                Message(title = "[Print Skew Compensation]", text = "Should be first in the Post-Processor list.  It will run if it isn't first, but any following post-processors should act on the changes made by 'Print Skew Compensation'.").show()
                break

        compensation_method = self.getSettingValueByKey("compensation_for")
        enable_xy_skew = self.getSettingValueByKey("enable_xy_skew")
        self.xy_AC_measurement = round(self.getSettingValueByKey("xy_AC_measurement"),4)
        self.xy_BD_measurement = round(self.getSettingValueByKey("xy_BD_measurement"),4)
        self.xy_AD_measurement = round(self.getSettingValueByKey("xy_AD_measurement"),4)

        enable_xz_skew = self.getSettingValueByKey("enable_xz_skew")
        self.xz_AC_measurement = round(self.getSettingValueByKey("xz_AC_measurement"),4)
        self.xz_BD_measurement = round(self.getSettingValueByKey("xz_BD_measurement"),4)
        self.xz_AD_measurement = round(self.getSettingValueByKey("xz_AD_measurement"),4)

        enable_yz_skew = self.getSettingValueByKey("enable_yz_skew")
        self.yz_AC_measurement = round(self.getSettingValueByKey("yz_AC_measurement"),4)
        self.yz_BD_measurement = round(self.getSettingValueByKey("yz_BD_measurement"),4)
        self.yz_AD_measurement = round(self.getSettingValueByKey("yz_AD_measurement"),4)

        if enable_xy_skew:
            self.xy_skew_factor = self.calculate_skew_factor(self.xy_AC_measurement, self.xy_BD_measurement, self.xy_AD_measurement)
        else:
            self.xy_skew_factor = 0.0

        if enable_xz_skew:
            self.xz_skew_factor = self.calculate_skew_factor(self.xz_AC_measurement, self.xz_BD_measurement, self.xz_AD_measurement)
        else:
            self.xz_skew_factor = 0.0

        if enable_yz_skew:
            self.yz_skew_factor = self.calculate_skew_factor(self.yz_AC_measurement, self.yz_BD_measurement, self.yz_AD_measurement)
        else:
            self.yz_skew_factor = 0.0

       # Exit if there are no error values entered
        if self.xy_skew_factor == 0 and self.xz_skew_factor == 0 and self.yz_skew_factor == 0:
            data[0] += ";  [Print Skew Compensation] did not run (no errors calculated)\n"
            return data

        if compensation_method == "method_cura":
            data = self.cura_compensation(data)
        elif compensation_method == "method_marlin":
            data = self.marlin_compensation(data)
        elif compensation_method == "method_klipper":
            data = self.klipper_compensation(data)

        if self.getSettingValueByKey("add_settings_to_gcode"):
            setting_string = ";  Print Skew Compensation Settings:\n"
            setting_string += ";    enable_xy_skew:  " + str(enable_xy_skew) + "\n"
            setting_string += f";      xy_AC_measurement:    {self.xy_AC_measurement}\n"
            setting_string += f";      xy_BD_measurement:    {self.xy_BD_measurement}\n"
            setting_string += f";      xy_AD_measurement:    {self.xy_AD_measurement}\n"
            setting_string += f";    enable_xz_skew:  " + str(enable_xz_skew) + "\n"
            setting_string += f";      xz_AC_measurement:    {self.xz_AC_measurement}\n"
            setting_string += f";      xz_BD_measurement:    {self.xz_BD_measurement}\n"
            setting_string += f";      xz_AD_measurement:    {self.xz_AD_measurement}\n"
            setting_string += f";    enable_xz_skew:  " + str(enable_yz_skew) + "\n"
            setting_string += f";      yz_AC_measurement:    {self.yz_AC_measurement}\n"
            setting_string += f";      yz_BD_measurement:    {self.yz_BD_measurement}\n"
            setting_string += f";      yz_AD_measurement:    {self.yz_AD_measurement}\n"
            data[len(data) - 1] += setting_string
        return data

    def calculate_skew_factor(self, ac: float, bd: float, ad:float) -> str:
        ab = math.sqrt(2*ac*ac+2*bd*bd-4*ad*ad)/2
        skew_comp = math.tan(math.pi/2-math.acos((ac*ac-ab*ab-ad*ad)/(2*ab*ad)))
        return skew_comp

    def cura_compensation(self, cura_data: str) -> str:
        """
            x_input, y_input, z_input: values used when X, Y, Z are != None
            x_out, Y_out, z_out: the replacement values to fix the skew
        """
        # z_input is cummulative
        z_input = 0
        for layer_index, layer in enumerate(cura_data):
            lines = layer.split("\n")
            # Get the X, Y, Z locations
            for index, line in enumerate(lines):
                if line.startswith(("G0", "G1")):
                    cur_x = self.getValue(line, "X", None)
                    cur_y = self.getValue(line, "Y", None)
                    cur_z = self.getValue(line, "Z", None)

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
                    x_out = round(x_input - y_input * self.xy_skew_factor, 3)
                    x_out = round(x_out - z_input * self.xz_skew_factor, 3)
                    y_out = round(y_input - z_input * self.yz_skew_factor, 3)

                    # If the first layer hasn't started then jump out (after tracking the XYZ).
                    if layer_index < 2:
                        continue

                    # Alter the current line
                    if cur_x != None:
                        lines[index] = lines[index].replace(f"X{cur_x}", f"X{x_out}")
                    if cur_y != None:
                        lines[index] = lines[index].replace(f"Y{cur_y}", f"Y{y_out}")

            cura_data[layer_index] = "\n".join(lines)
        return cura_data

    def marlin_compensation(self, cura_data: str) -> str:
        cmd_line = "M852"
        if self.xy_skew_factor and (self.xz_skew_factor == 0 and self.yz_skew_factor == 0):
            cmd_line += f" S{round(self.xy_skew_factor, 8)}"
        elif self.xy_skew_factor and (self.xz_skew_factor != 0 or self.yz_skew_factor != 0):
            cmd_line += f" I{round(self.xy_skew_factor, 8)}"
        if self.xz_skew_factor != 0:
            cmd_line += f" J{round(self.xz_skew_factor, 8)}"
        if self.yz_skew_factor != 0:
            cmd_line += f" K{round(self.yz_skew_factor, 8)}"
        cmd_line += " ; Skew Compensation"
        startup = cura_data[1].split("\n")
        startup.insert(1, cmd_line)
        cura_data[1] = "\n".join(startup)
        return cura_data

    def klipper_compensation(self, cura_data: str) -> str:
        cmd_line = "SET_SKEW"
        if self.xy_skew_factor != 0:
            cmd_line += f" XY={self.xy_AC_measurement},{self.xy_BD_measurement},{self.xy_AD_measurement}"
        if self.xz_skew_factor != 0:
            cmd_line += f" XZ={self.xz_AC_measurement},{self.xz_BD_measurement},{self.xz_AD_measurement}"
        if self.yz_skew_factor != 0:
            cmd_line += f" YZ={self.yz_AC_measurement},{self.yz_BD_measurement},{self.yz_AD_measurement}"
        cmd_line += " ; Skew Compensation"
        startup = cura_data[1].split("\n")
        startup.insert(1, cmd_line)
        cura_data[1] = "\n".join(startup)
        return cura_data