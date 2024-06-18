# By GregValiant (Greg Foresi) in August of 2023
# For Raise3D IDEX printers - Adds M605 S0 for Normal, M605 S1 for Duplication, or M605 S2 for Mirror mode

from ..Script import Script
from UM.Application import Application

class Raise3D_IDEX(Script):
    """Adds 'Print Mode' to the startup and resets at the end.
    """
    def __init__(self):
        super().__init__()

    def initialize(self) -> None:
        super().initialize()
        # Disable the Power-Resume and Pressure Advance settings if they are in the Startup Gcode
        mycura = Application.getInstance().getGlobalContainerStack()
        startup_gcode = mycura.getProperty("machine_start_gcode", "value")
        machine_name = str(mycura.getProperty("machine_name", "value"))
        if "Raise3D" in machine_name:
            if "M572" in startup_gcode:
                self._instance.setProperty("pres_adv_enable", "value", False)
            else:
                self._instance.setProperty("pres_adv_enable", "value", True)
            if "M1001" in startup_gcode:
                self._instance.setProperty("power_enable", "value", False)
            else:
                self._instance.setProperty("power_enable", "value", True)
        else:
            self._instance.setProperty("power_enable", "value", False)
            self._instance.setProperty("pres_adv_enable", "value", False)
            
    def getSettingDataString(self):
        return """{
            "name": "Raise3D IDEX Setting",
            "key": "Raise3D_IDEX",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "idex_mode_cmd":
                {
                    "label": "Mode Command",
                    "description": "Enter the mode command that applies to your printer.  Raise3D uses 'M605', others might use 'D'.",
                    "type": "enum",
                    "options": {
                        "cmd_m605": "M605",
                        "cmd_D": "D"},
                    "default_value": "cmd_m605"
                },
                "idex_setting":
                {
                    "label": "Print Mode",
                    "description": "Pick the one that applies to this print.  For 'Duplication' and 'Mirror' you must correctly locate the model on the left half of the bed.",
                    "type": "enum",
                    "options": {
                        "mode_N": "Normal",
                        "mode_D": "Duplication",
                        "mode_M": "Mirror"},
                    "default_value": "mode_N"
                },
                "power_enable":
                {
                    "label": "Power Enable",
                    "description": "Hidden.  If M1001 is in the Startup Gcode this disables 'power_resume' here.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": false
                },
                "power_resume":
                {
                    "label": "Power Resume (M1001)",
                    "description": "Enable 'Power Resume' with M1001.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "power_enable"
                },
                "pres_adv_enable":
                {
                    "label": "Pressure Advance Enable",
                    "description": "Hidden.  If M572 is in the StartUp Gcode this disables pa_e1 and pa_e2.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": false
                },
                "pa_e1":
                {
                    "label": "Pressure Advance Extruder1",
                    "description": "Enable 'Presure Advance' for Extruder 1.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "pres_adv_enable"
                },
                "pa_e1_amt":
                {
                    "label": "   PresAdv E1 time",
                    "description": "'Presure Advance' time for Extruder 1",
                    "type": "str",
                    "default_value": "0.05",
                    "enabled": "pa_e1",
                    "unit": "seconds"
                },
                "pa_e2":
                {
                    "label": "Pressure Advance Extruder2",
                    "description": "Enable 'Presure Advance' for Extruder 2.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "pres_adv_enable"
                },
                "pa_e2_amt":
                {
                    "label": "   PresAdv E2 time",
                    "description": "'Presure Advance' time for Extruder 2.",
                    "type": "str",
                    "default_value": "0.05",
                    "enabled": "pa_e2",
                    "unit": "seconds"
                }
            }
        }"""

    def execute(self, data):
        MyCura = Application.getInstance().getGlobalContainerStack()
        extruder = Application.getInstance().getGlobalContainerStack().extruderList
        idex_mode_cmd = str(self.getSettingValueByKey("idex_mode_cmd"))
        # Configure IDEX, Pressure Advance, and Power Resume commands--------------------------------
        pa_e1 = bool(self.getSettingValueByKey("pa_e1"))
        if pa_e1:
            pa_e1_amt = "M572 D0 S" + str(self.getSettingValueByKey("pa_e1_amt")) + " ;Pressure Advance E1"
        pa_e2 = bool(self.getSettingValueByKey("pa_e2"))
        if pa_e2:
            pa_e2_amt = "M572 D1 S" + str(self.getSettingValueByKey("pa_e2_amt")) + " ;Pressure Advance E2"
        idex_setting = self.getSettingValueByKey("idex_setting")
        if idex_setting == "mode_N":
            idex_cmd = idex_mode_cmd + " S0 ;Normal Mode"
        elif idex_setting == "mode_D":
            idex_cmd = idex_mode_cmd + " S1 ;Duplication Mode"
        elif idex_setting == "mode_M":
            idex_cmd = idex_mode_cmd + " S2 ;Mirror Mode"
        idex_startup_power = "M1001 ;Power Resume On"
        
        # Insert the commands in the StartUp Gcode----------------------------------------
        startup_gcode = data[1].split("\n")
        startup_gcode.insert(1,idex_cmd)
        startup_temp = startup_gcode
        for index, line in enumerate(startup_gcode):
            if line.startswith(";LAYER_COUNT:"):
                if not "M572" in data[1]:
                    if pa_e2:
                        startup_temp.insert(index,pa_e2_amt)
                    if pa_e1:
                        startup_temp.insert(index,pa_e1_amt)
                if not "M1001" in data[1] and bool(self.getSettingValueByKey("power_resume")):
                    startup_temp.insert(index,idex_startup_power)    
                break
        data[1] = "\n".join(startup_temp)
        
        # Insert the reset commands in the Ending Gcode--------------------------------------
        end_gcode = data[len(data)-1]
        end_lines = end_gcode.split("\n")
        end_temp = end_lines
        for index, line in enumerate(end_lines):
            if line.startswith(";End of Gcode"):
                end_temp.insert(index,"M605 S0 ;Reset to Normal Mode")
                if not "G28 X0 U0" in data[len(data)-1]:
                    end_temp.insert(index,"G28 X0 U0 ;Auto-Home X and U axes if required")
                if not "M1002" in data[len(data)-1] and bool(self.getSettingValueByKey("power_resume")):
                    end_temp.insert(index,"M1002 ;Power Resume Off")
                break
        data[len(data)-1] = "\n".join(end_temp)
        return data