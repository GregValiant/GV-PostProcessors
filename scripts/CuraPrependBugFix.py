# Authored by: GregValiant (Greg Foresi) 6/24
# Removes the M104 and M109 hot end temperature prepend lines if 'material_print_temperature' is in the StartUp Gcode (also covers 'material_print_temperature_layer_0')
# Removes the M140 and M190 bed temperature prepend lines if 'material_bed_temperature' is in the StartUp Gcode (also covers 'material_bed_temperature_layer_0')

from ..Script import Script
from UM.Application import Application

class CuraPrependBugFix(Script):

    def getSettingDataString(self):    
        return """{
            "name": "Cura Prepend Temperature Bugfix",
            "key": "CuraPrependBugFix",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "enable_prepend_bugfix":
                {
                    "label": "Enable this script",
                    "description": "When enabled the script will check if Bed and Hot End temperature prepends were required.  It will go ahead and remove the prepend temperature lines from before the StartUp Gcode if they were not.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": true
                }
            }
        }"""

    def execute(self, data):
        # Exit if the script is not enabled        
        if not bool(self.getSettingValueByKey("enable_prepend_bugfix")):
            return data
        startup = data[1].split("\n")
        startup_gcode = Application.getInstance().getGlobalContainerStack().getProperty("machine_start_gcode", "value")
        prepend_hot_end = True
        prepend_bed = True
        modified_data = []
        # Check the startup gcode for hot end temperature replacement patterns (keywords)
        if "material_print_temperature" in startup_gcode:
            prepend_hot_end = False
        # Check the startup gcode for bed temperature replacement patterns (keywords)
        if "material_bed_temperature" in startup_gcode:
            prepend_bed = False
        # If the prepend is required then exit.
        if prepend_hot_end and prepend_bed:
            return data
        for index, line in enumerate(startup):
            first_part = startup[index][0:4]
            if not prepend_hot_end:
                if first_part in ["M104", "M109"]:
                    continue
            if not prepend_bed:
                if first_part in ["M140", "M190"]:
                    continue
            if not prepend_hot_end and not prepend_bed:
                if first_part == "M105":
                    continue
            # Once the M82 line is reached then we are past the prepend lines so just continue.
            if line.startswith("M82"):
                prepend_hot_end = True
                prepend_bed = True
            modified_data.append(line)
        data[1] = "\n".join(modified_data)
        return data