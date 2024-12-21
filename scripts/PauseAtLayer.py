#  Revision by GregValiant 1-1-2024
#  "Pause at Height" is obsolete.  It didn't work with Z-hops enabled or with adaptive Layers.
#  Added 'Unload', 'Reload', and 'Purge' options and removed the 'Retraction' option.  Retractions will occur if there is no retraction prior to the pause.
#  Added 'Reason for Pause' option.  When 'Filament Change' is chosen then Unload, Reload, and Purge become available.  If 'All Others' reasons is chosen then those options aren't required.
#  Added option for pauses in a 'One at a Time' print.  Pauses can be at different layers in different parts.  All pause layers must be listed (use the Cura Preview layer numbers).  Simply telling it to pause at 'Layer:5' will only result in a pause at the first layer:5 encountered.  Models can be skipped, or have pauses at different layers than other models, and some models could be entirely different colors or material.
#  Added multiple messages if multiple pause layers are used in a single instance of the script. If pause layers are '23,31,45,110' then messages can be 'Blue,Red,Whte,Blue'.

from ..Script import Script
import re
from UM.Application import Application
from UM.Logger import Logger
from typing import List, Tuple
from UM.Message import Message

class PauseAtLayer(Script):

    def getSettingDataString(self) -> str:
        return """{
            "name": "Pause at Layer",
            "key": "PauseAtLayer",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "enable_pause_at_layer":
                {
                    "label": "Enable Pause at Layer",
                    "description": "When disabled it will remain in the post-processor list but will not run.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": true
                },
                "pause_layer":
                {
                    "label": "Pause at end of layer...",
                    "description": "Enter the number of the LAST layer you want to finish prior to the pause. Use the layer numbers from the Cura preview.  If you want to use these exact same settings for more than one pause then use a comma to delimit the layer numbers.  If the settings are different then you must add another instance of PauseAtLayer.",
                    "type": "str",
                    "value": "25",
                    "minimum_value": "1",
                    "enabled": "enable_pause_at_layer"
                },
                "pause_method":
                {
                    "label": "Pause Command",
                    "description": "The gcode command to use to pause the print.  This is firmware dependent.  'M0 w/message(Marlin)' is firmware dependent but may show the LCD message if there is one.  'M0 (Marlin)' is the plain 'M0' command",
                    "type": "enum",
                    "options": {
                        "marlin": "M0 w/message(Marlin)",
                        "marlin2": "M0 (Marlin)",
                        "griffin": "M0 (Griffin,firmware retract)",
                        "bq": "M25 (BQ)",
                        "reprap": "M226 (RepRap)",
                        "repetier": "@pause (Repet/Octo)",
                        "alt_octo": "M125 (alt Octo)",
                        "raise_3d": "M2000 (raise3D)",
                        "klipper": "PAUSE (Klipper)",
                        "g_4": "G4 (dwell)",
                        "custom": "Custom Command"
                        },
                    "default_value": "marlin",
                    "enabled": "enable_pause_at_layer"
                },
                "g4_dwell_time":
                {
                    "label": "    G4 dwell time (in minutes)",
                    "description": "The amount of time to pause for. 'G4 S' is a 'hard' number.  You cannot make it shorter at the printer.  At the end of the dwell time - the printer will restart by itself.",
                    "type": "float",
                    "default_value": 5.0,
                    "minimum_value": 0.5,
                    "maximum_value_warning": 30.0,
                    "unit": "minutes   ",
                    "enabled": "enable_pause_at_layer and pause_method == 'g_4'"
                },
                "custom_pause_command":
                {
                    "label": "    Custom Pause Command",
                    "description": "If none of the the stock options work with your printer you can enter a custom command here.  If you use 'M600' for the filament change you must include any other parameters.  Check the gcode carefully.",
                    "type": "str",
                    "default_value": "",
                    "enabled": "enable_pause_at_layer and pause_method == 'custom'"
                },
                "reason_for_pause":
                {
                    "label": "Reason for Pause",
                    "description": "Filament changes allow for the unload / load / purge sequence.  Other reasons (Ex: inserting nuts or magnets) don't require those.",
                    "type": "enum",
                    "options": {"reason_filament": "Filament Change", "reason_other": "All Others"},
                    "default_value": "reason_filament",
                    "enabled": "enable_pause_at_layer"
                },
                "one_at_a_time_renum":
                {
                    "label": "One-at-a-Time mode: Add pauses to all models",
                    "description": "When using 'One_at_a_Time' mode you can add pauses to each model.  Use the Cura preview layer numbers from the bottom through to the top.  Your model may be 150 layers tall and the pauses may be at '100,200,300' per the preview layer numbers.  Check the gcode to insure you get what you intended.  It is possible to give each model a pause at a different height (layer) or don't pause for some models.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "enable_pause_at_layer and pause_method != 'griffin'"
                },
                "unload_amount":
                {
                    "label": "     Unload Amount",
                    "description": "How much filament must be retracted to unload for the filament change.  This number will be split into segments in the gcode as a single command might trip the 'excessive extrusion' warning in the firmware.",
                    "unit": "mm   ",
                    "type": "int",
                    "value": 430,
                    "default_value": 0,
                    "enabled": "enable_pause_at_layer and pause_method != 'griffin' and reason_for_pause == 'reason_filament'"
                },
                "enable_quick_purge":
                {
                    "label": "    Quick purge before unload",
                    "description": "This can insure that the filament will unload by softening the tip so it can do the long retraction.  This purge is fixed length and will be 'retraction distance x 2'",
                    "type": "bool",
                    "default_value": true,
                    "enabled": "enable_pause_at_layer and pause_method != 'griffin' and reason_for_pause == 'reason_filament' and unload_amount > 0"
                },
                "unload_reload_speed":
                {
                    "label": "     Unload and Reload Speed",
                    "description": "How fast to unload or reload the filament in mm/sec.",
                    "unit": "mm/s   ",
                    "type": "int",
                    "value": 50,
                    "default_value": 50,
                    "enabled": "enable_pause_at_layer and pause_method not in ['griffin', 'repetier'] and reason_for_pause == 'reason_filament' and pause_at == 'layer_no'"
                },
                "reload_amount":
                {
                    "label": "     Reload Amount",
                    "description": "The length of filament to load before the purge.  90% of this distance will be fast and the final 10% at the purge speed.  If you prefer to reload up to the nozzle by hand then set this to '0'.",
                    "unit": "mm   ",
                    "type": "int",
                    "value": 370,
                    "default_value": 0,
                    "enabled": "enable_pause_at_layer and pause_method != 'griffin' and reason_for_pause == 'reason_filament'"
                },
                "purge_amount":
                {
                    "label": "     Purge Amount",
                    "description": "The amount of filament to be extruded after the pause. For most printers this is the amount to purge to complete a color change at the nozzle.  For Ultimaker2's this is to compensate for the retraction after the change. In that case 128+ is recommended.",
                    "unit": "mm   ",
                    "type": "int",
                    "value": 35,
                    "default_value": 35,
                    "enabled": "enable_pause_at_layer and pause_method != 'griffin' and reason_for_pause == 'reason_filament'"
                },
                "extra_prime_amount":
                {
                    "label": "Extra Prime Amount",
                    "description": "Sometimes a little more is needed to account for oozing during a pause.  At .2 layer height and .4 line width - 0.10mm of 1.75 filament of 'Extra Prime' is 3mm of extrusion.  0.10mm of 2.85 filament of 'Extra Prime' would be 8mm of extrusion.  Plan accordingly.",
                    "unit": "mm   ",
                    "type": "str",
                    "value": "0.30",
                    "default_value": "0.30",
                    "enabled": "enable_pause_at_layer and pause_method != 'griffin' and reason_for_pause == 'reason_other'"
                },
                "hold_steppers_on":
                {
                    "label": "Keep motors engaged",
                    "description": "Keep the steppers engaged so they don't lose position.  If this is unchecked then the Stepper Disarm time will be the default disarm time within the printer (often 2 minutes).",
                    "type": "bool",
                    "default_value": true,
                    "enabled": "enable_pause_at_layer and pause_method != 'griffin'"
                },
                "disarm_timeout":
                {
                    "label": "    Stepper disarm timeout",
                    "description": "After this amount of time (in minutes) the steppers will disarm (meaning that they will lose their positions). The behavior of a setting of '0' is dependent on the firmware.  It might mean 'disarm immediately' or 'not until the print ends'.",
                    "type": "int",
                    "default_value": 30,
                    "minimum_value": 0,
                    "maximum_value_warning": 120,
                    "unit": "minutes   ",
                    "enabled": "enable_pause_at_layer and hold_steppers_on and pause_method != 'griffin'"
                },
                "head_park_enabled":
                {
                    "label": "Park the PrintHead",
                    "description": "Move the head to a safe location when pausing (necessary for filament changes with nozzle purges, or just to move it out of the way to make insertions into the print). Leave this unchecked if your printer handles parking for you.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": "enable_pause_at_layer and pause_method != 'griffin'"
                },
                "head_park_x":
                {
                    "label": "     Park PrintHead X",
                    "description": "What X location does the head move to when pausing.",
                    "unit": "mm   ",
                    "type": "float",
                    "maximum_value": 230,
                    "default_value": 0,
                    "enabled": "enable_pause_at_layer and head_park_enabled and pause_method != 'griffin'"
                },
                "head_park_y":
                {
                    "label": "     Park PrintHead Y",
                    "description": "What Y location does the head move to when pausing.",
                    "unit": "mm   ",
                    "type": "float",
                    "maximum_value": 230,
                    "default_value": 0,
                    "enabled": "enable_pause_at_layer and head_park_enabled and pause_method != 'griffin'"
                },
                "head_move_z":
                {
                    "label": "     Lift Head Z",
                    "description": "The relative move of the Z-axis above the print before parking.  If the Z ends up at less than 'Minimum Dist Nozzle to Plate' there will be a second move to provide room for purging below the nozzle (if you happen to be changing filament).",
                    "unit": "mm   ",
                    "type": "float",
                    "default_value": 1.0,
                    "minimum_value": 0.0,
                    "minimum_value_warning": 0.2,
                    "maximum_value_warning": 8,
                    "maximum_value": 10,
                    "enabled": "enable_pause_at_layer and head_park_enabled and pause_method != 'repetier'"
                },
                "min_purge_clearance":
                {
                    "label": "     Minimum dist nozzle to plate",                    
                    "description": "Pausing at a low layer might not leave enough room below the nozzle to purge.  The number you enter here will be used as the minimum Z height at the park position.  If your pause is at Z=8.4 and you enter 25 here then there will be a second Z move at the park position to move up to 25.",
                    "unit": "mm   ",
                    "type": "int",
                    "default_value": 15,
                    "minimum_value": 0,
                    "maximum_value": 50,
                    "enabled": "enable_pause_at_layer and head_park_enabled and pause_method != 'repetier'"
                },
                    
                "standby_temperature":
                {
                    "label": "Standby Temperature",
                    "description": "The temperature to hold at during the pause.  If this temperature is different than your print temperature then use the 'M109' Resume Temperature Cmd option",
                    "unit": "°C   ",
                    "type": "int",
                    "default_value": 200,
                    "enabled": "enable_pause_at_layer and pause_method not in ['griffin\', 'repetier']"
                },
                "tool_temp_overide_enable":
                {
                    "label": "Hidden setting Temp Overide Enable",
                    "description": "Enable tool changes to overide the print temperature.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": false
                },
                "tool_temp_overide":
                {
                    "label": "Tool changes set the resume temperature",
                    "description": "For multi-extruder printers - resume the print at the temperature of the current extruder.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "tool_temp_overide_enable and enable_pause_at_layer"
                },
                "resume_temperature_cmd":
                {
                    "label": "Resume Temperature Cmd",
                    "description": "If you switch materials, or if your standby temperature is different than the Resume Printing temperature then use M109.  If they happen to be the same you can use M104 and there won't be a wait period.",
                    "type": "enum",
                    "options": {
                        "m109_cmd": "M109",
                        "m104_cmd": "M104"},
                    "default_value": "m104_cmd",
                    "enabled": "enable_pause_at_layer and pause_method not in ['griffin', 'repetier'] and not tool_temp_overide"
                },
                "resume_print_temperature":
                {
                    "label": "Resume Print Temperature",
                    "description": "The temperature to resume the print after the pause.  If this temperature is different than your standby temperature then use the 'M109' Resume Temperature Cmd option",
                    "unit": "°C   ",
                    "type": "int",
                    "default_value": 200,
                    "enabled": "enable_pause_at_layer and pause_method not in ['griffin\', 'repetier'] and not tool_temp_overide"
                },
                "display_text":
                {
                    "label": "Message to LCD",
                    "description": "Text that should appear on the display while paused. If left empty, there will not be any message.  Please note:  It is possible that the message will be immediately overridden by another message sent by the firmware.  If 'M0 w/message' is chosen as the pause command then the message is added to the pause command. You may have as many messages as pauses.  Delimit with a comma",
                    "type": "str",
                    "default_value": "",
                    "enabled": "enable_pause_at_layer and pause_method != 'repetier'"
                },
                "custom_gcode_before_pause":
                {
                    "label": "G-code Before Pause",
                    "description": "Custom g-code to run before the pause. EX: M300 to beep. Use a comma to separate multiple commands. EX: M400,M300,M117 Pause",
                    "type": "str",
                    "default_value": "",
                    "enabled": "enable_pause_at_layer"
                },
                "beep_at_pause":
                {
                    "label": "Beep at pause",
                    "description": "Make an annoying sound when pausing",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "enable_pause_at_layer"
                },
                "beep_length":
                {
                    "label": "Beep duration",
                    "description": "How long should the annoying sound last.  The units are in milliseconds so 1000 equals 1 second. ('250' is a quick chirp).",
                    "type": "int",
                    "default_value": "1000",
                    "unit": "msec   ",
                    "enabled": "enable_pause_at_layer and beep_at_pause"
                },
                "redo_layer":
                {
                    "label": "Redo Layer",
                    "description": "Redo the last layer before the pause, to get the filament flowing again after having oozed a bit during the pause.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "enable_pause_at_layer and reason_for_pause == 'reason_filament'"
                },
                "redo_layer_flow":
                {
                    "label": "     Flow Rate for Redo Layer",
                    "description": "You can adjust the Flow Rate of the 'Redo Layer' to help keep a layer from sticking out due to over-extrusion.  The flow will be reset to 100% at the end of the redo layer.",
                    "type": "int",
                    "default_value": 100,
                    "maximum_value": 150,
                    "minimum_value": 50,
                    "enabled": "enable_pause_at_layer and redo_layer and reason_for_pause == 'reason_filament'"
                },
                "custom_gcode_after_pause":
                {
                    "label": "G-code After Pause",
                    "description": "Custom g-code to run after the pause. Use a comma to separate multiple commands. EX: M204 X8 Y8,M106 S0,M999.  Some firmware that uses M25 to pause may need a buffer to avoid executing commands that are beyond the pause line.  You can use 'M105,M105,M105,M105,M105,M105' as a buffer.",
                    "type": "str",
                    "default_value": "",
                    "enabled": "enable_pause_at_layer"
                },
                "machine_name":
                {
                    "label": "Machine Type",
                    "description": "The name of your 3D printer model. This setting is controlled by the script and will not be visible.",
                    "default_value": "Unknown",
                    "type": "str",
                    "enabled": false
                },
                "machine_gcode_flavor":
                {
                    "label": "G-code flavor",
                    "description": "The type of g-code to be generated. This setting is controlled by the script and will not be visible.",
                    "type": "enum",
                    "options":
                    {
                        "RepRap (Marlin/Sprinter)": "Marlin",
                        "RepRap (Volumetric)": "Marlin (Volumetric)",
                        "RepRap (RepRap)": "RepRap",
                        "UltiGCode": "Ultimaker 2",
                        "Griffin": "Griffin",
                        "Makerbot": "Makerbot",
                        "BFB": "Bits from Bytes",
                        "MACH3": "Mach3",
                        "Repetier": "Repetier"
                    },
                    "default_value": "RepRap (Marlin/Sprinter)",
                    "enabled": false
                }
            }
        }"""

    #  Get the machine name and gcode flavor so we can use their value in the script stack
    def initialize(self) -> None:
        super().initialize()
        # Set up some defaults when loading.
        curaApp = Application.getInstance().getGlobalContainerStack()
        if curaApp is None or self._instance is None:
            return
            
        for key in ["machine_name", "machine_gcode_flavor"]:
            self._instance.setProperty(key, "value", curaApp.getProperty(key, "value"))
        extruder = curaApp.extruderList
        machine_extruder_count = int(curaApp.getProperty("machine_extruder_count", "value"))
        self._instance.setProperty("tool_temp_overide_enable", "value", machine_extruder_count > 1)
        self._instance.setProperty("tool_temp_overide", "value", machine_extruder_count > 1)
        standby_temperature = extruder[0].getProperty("material_print_temperature", "value")
        self._instance.setProperty("standby_temperature", "value", standby_temperature)
        resume_print_temperature = extruder[0].getProperty("material_print_temperature", "value")
        self._instance.setProperty("resume_print_temperature", "value", resume_print_temperature)
        unload_reload_speed = int(curaApp.getProperty("machine_max_feedrate_e", "value"))
        # If Cura has the max E speed at 299792458000 knock it down to something reasonable
        if unload_reload_speed > 100: unload_reload_speed = 100
        self._instance.setProperty("unload_reload_speed", "value", unload_reload_speed)
        self._machine_width = int(curaApp.getProperty("machine_width", "value"))
        self._machine_depth = int(curaApp.getProperty("machine_depth", "value"))
        self._machine_height = int(curaApp.getProperty("machine_height", "value"))
        self._instance.setProperty("head_park_x", "maximum_value", self._machine_width)
        self._instance.setProperty("head_park_y", "maximum_value", self._machine_depth)

    def execute(self, data):
        if not self.getSettingValueByKey("enable_pause_at_layer"):
            data[0] += ";    [Pause At Layer] Not enabled\n"
            return data
        curaApp = Application.getInstance().getGlobalContainerStack()
        one_at_a_time = curaApp.getProperty("print_sequence", "value")
        one_at_a_time_renum = bool(self.getSettingValueByKey("one_at_a_time_renum"))
        if one_at_a_time == "one_at_a_time" and one_at_a_time_renum:
            data = self._renumber_layers(data, "renum")
        pause_layer_setting = str(self.getSettingValueByKey("pause_layer"))
        display_text = str(self.getSettingValueByKey("display_text"))
        pause_layer_list = pause_layer_setting.split(",")
        display_text_list = display_text.split(",")
        for index, pause_layer in enumerate(pause_layer_list):
            try:
                txt_msg = display_text_list[index]
            except:
                txt_msg = display_text_list[len(display_text_list) - 1]                
            data = self._find_pause(data, int(pause_layer.strip()), txt_msg.strip())
        if one_at_a_time == "one_at_a_time" and one_at_a_time_renum:
            data = self._renumber_layers(data, "un_renum")
        return data

    #  Get the X and Y values for a layer (will be used to get X and Y of the layer after the pause and of the 'redo' layer if that option is used).
    def getNextXY(self, layer: str) -> Tuple[float, float]:
        lines = layer.split("\n")
        for line in lines:
            if line.startswith(("G0", "G1", "G2", "G3")):
                if self.getValue(line, "X") is not None and self.getValue(line, "Y") is not None:
                    x = self.getValue(line, "X")
                    y = self.getValue(line, "Y")
                    return x, y
        return 0, 0

    def _find_pause(self, new_data: [str], pause_layer: int, txt_msg: str) -> [str]:
        curaApp = Application.getInstance().getGlobalContainerStack()
        extruder = curaApp.extruderList
        speed_z_hop = extruder[0].getProperty("speed_z_hop", "value") * 60
        retraction_amount = extruder[0].getProperty("retraction_amount", "value")
        retraction_retract_speed = int(extruder[0].getProperty("retraction_retract_speed", "value")) * 60
        retraction_prime_speed = int(extruder[0].getProperty("retraction_prime_speed", "value")) * 60
        travel_speed = int(extruder[0].getProperty("speed_travel", "value")) * 60
        nozzle_size = extruder[0].getProperty("machine_nozzle_size", "value")
        hold_steppers_on = self.getSettingValueByKey("hold_steppers_on")
        disarm_timeout = self.getSettingValueByKey("disarm_timeout") * 60
        reason_for_pause = self.getSettingValueByKey("reason_for_pause")
        unload_amount = self.getSettingValueByKey("unload_amount")
        unload_quick_purge = self.getSettingValueByKey("enable_quick_purge")
        unload_reload_speed = int(self.getSettingValueByKey("unload_reload_speed")) * 60
        reload_amount = self.getSettingValueByKey("reload_amount")
        purge_amount = self.getSettingValueByKey("purge_amount")
        extra_prime_amount = self.getSettingValueByKey("extra_prime_amount")
        if reason_for_pause == "reason_filament":
            extra_prime_amount = "0"
        purge_speed = round(nozzle_size * 500) # calculate the purge speed based on the nozzle size.  A 0.4 will be 200 and a 0.8 will be 400 mm/min.
        park_enabled = self.getSettingValueByKey("head_park_enabled")
        park_x = self.getSettingValueByKey("head_park_x") if self.getSettingValueByKey("head_park_x") < self._machine_depth else self._machine_depth
        park_y = self.getSettingValueByKey("head_park_y") if self.getSettingValueByKey("head_park_y") < self._machine_width else self._machine_width
        move_z = self.getSettingValueByKey("head_move_z")
        min_purge_clearance = self.getSettingValueByKey("min_purge_clearance")
        layers_started = False
        redo_layer = self.getSettingValueByKey("redo_layer")
        if redo_layer and reason_for_pause == "reason_filament":
            redo_layer_flow = "M221 S" + str(self.getSettingValueByKey("redo_layer_flow")) + str(" " * (27 - len("M221 S" + str(self.getSettingValueByKey("redo_layer_flow"))))) + "; Set Redo Layer Flow"
            redo_layer_flow_reset = "M221 S100                  ; PauseAtLayer Reset flow\n"
        else:
            redo_layer_flow = ""
            redo_layer_flow_reset = ""
        resume_temperature_cmd = self.getSettingValueByKey("resume_temperature_cmd")
        standby_temperature = self.getSettingValueByKey("standby_temperature")
        use_tool_temperature = bool(self.getSettingValueByKey("tool_temp_overide"))
        resume_print_temperature = self.getSettingValueByKey("resume_print_temperature")

        firmware_retract = Application.getInstance().getGlobalContainerStack().getProperty("machine_firmware_retract", "value")
        control_temperatures = Application.getInstance().getGlobalContainerStack().getProperty("machine_nozzle_temp_enabled", "value")
        initial_layer_height = Application.getInstance().getGlobalContainerStack().getProperty("layer_height_0", "value")
        display_text = txt_msg #self.getSettingValueByKey("display_text")
        # Capitalize the command letter of any added commands.  Some firmware doesn't acknowledge lower case commands.
        gcode_before = self.getSettingValueByKey("custom_gcode_before_pause")
        if gcode_before != "":
            if "," in gcode_before:
                xtra_cmds = gcode_before.split(",")
                for index in range(0, len(xtra_cmds) - 1):
                    xtra_cmds[index] = xtra_cmds[index][0].upper() + xtra_cmds[index][1:]
                gcode_before = "\n".join(xtra_cmds)
            else:
                gcode_before = gcode_before[0].upper() + gcode_before[1:]
        gcode_after = self.getSettingValueByKey("custom_gcode_after_pause")
        if gcode_after != "":
            if "," in gcode_after:
                xtra_cmds = gcode_after.split(",")
                for index in range(0, len(xtra_cmds)):
                    xtra_cmds[index] = xtra_cmds[index][0].upper() + xtra_cmds[index][1:]
                gcode_after = "\n".join(xtra_cmds)
            else:
                gcode_after = gcode_after[0].upper() + gcode_after[1:]
        beep_at_pause = self.getSettingValueByKey("beep_at_pause")
        beep_length = self.getSettingValueByKey("beep_length")
        g4_dwell_time = round(self.getSettingValueByKey("g4_dwell_time") * 60)
        pause_method = self.getSettingValueByKey("pause_method")
        if pause_method == "custom":
            custom_pause_command = self.getSettingValueByKey("custom_pause_command")
        else:
            custom_pause_command = ""
        pause_command = {
            "marlin": "M0 " + txt_msg + " Click to resume",
            "marlin2": "M0",
            "griffin": self.putValue(M = 0),
            "bq": self.putValue(M = 25),
            "reprap": self.putValue(M = 226),
            "repetier": self.putValue("@pause now change filament and press continue printing"),
            "alt_octo": self.putValue(M = 125),
            "raise_3d": self.putValue(M = 2000),
            "klipper": self.putValue("PAUSE"),
            "custom": self.putValue(str(custom_pause_command)),
            "g_4": self.putValue(G = 4, S = g4_dwell_time)}[pause_method]

        # use offset to calculate the current height: <current_height> = <current_z> - <layer_0_z>
        layer_0_z = 0
        current_z = 0
        current_height = 0
        current_layer = 0
        current_extrusion_f = 0
        got_first_g_cmd_on_layer_0 = False
        current_t = 0 # Tracks the current extruder for tracking the target temperature.
        target_temperature = {} # Tracks the current target temperature for each extruder.

        nbr_negative_layers = 0

        for index, layer in enumerate(new_data):
            lines = layer.split("\n")

            # Scroll each line of instruction for each layer in the G-code
            for line in lines:
                # Fist positive layer reached
                if ";LAYER:0" in line:
                    layers_started = True
                # Count nbr of negative layers (raft)
                elif ";LAYER:-" in line:
                    nbr_negative_layers += 1
                # Track the latest printing temperature in order to resume at the correct temperature.
                if use_tool_temperature:
                    if line.startswith("M109 S") or line.startswith("M104 S"):
                        resume_print_temperature = self.getValue(line, "S")
                if not layers_started:
                    continue
                # Look for the feed rate of an extrusion instruction
                if self.getValue(line, "F") is not None and self.getValue(line, "E") is not None:
                    current_extrusion_f = self.getValue(line, "F")
                # If a Z instruction is in the line, read the current Z
                if self.getValue(line, "Z") is not None:
                    current_z = self.getValue(line, "Z")

                if not line.startswith(";LAYER:"):
                    continue
                current_layer = line[len(";LAYER:"):]
                try:
                    current_layer = int(current_layer)

                # Couldn't cast to int. Something is wrong with this g-code data
                except ValueError:
                    continue
                if current_layer < pause_layer - nbr_negative_layers:
                    continue

                # Access last layer, browse it backwards to find last extruder absolute position check if it is a retraction
                prev_layer = new_data[index - 1]
                prev_lines = prev_layer.split("\n")
                is_retracted = None
                current_e = None
                for prevLine in reversed(prev_lines):
                    current_e = self.getValue(prevLine, "E")
                    if re.search("G1 F(\d*) E(\d.*)", prevLine) is not None or re.search("G1 F(\d*) E-(\d.*)", prevLine) is not None or "G10" in prevLine:
                        if is_retracted == None:
                            is_retracted = True
                    if current_e is not None:
                        if is_retracted is None:
                            is_retracted = False
                        break
                # and also find last X,Y
                for prevLine in reversed(prev_lines):
                    if prevLine.startswith(("G0", "G1", "G2", "G3")):
                        if self.getValue(prevLine, "X") is not None and self.getValue(prevLine, "Y") is not None:
                            x = self.getValue(prevLine, "X")
                            y = self.getValue(prevLine, "Y")
                            break

                # Maybe redo the previous layer.
                if redo_layer and reason_for_pause == "reason_filament":
                    prev_layer = new_data[index - 1]
                    temp_list = prev_layer.split("\n")
                    temp_list[0] = temp_list[0] + ".5" + str(" " * (27 - len(temp_list[0] + ".1"))) + "; Redo layer from PauseAtLayer\n" + redo_layer_flow
                    prev_layer = "\n".join(temp_list)
                    layer = prev_layer + redo_layer_flow_reset + layer
                    new_data[index] = layer
                    # Get the X Y position and the extruder's absolute position at the beginning of the redone layer.
                    x, y = self.getNextXY(layer)
                    prev_lines = prev_layer.split("\n")
                    for lin in prev_lines:
                        new_e = self.getValue(lin, "E", current_e)
                        if new_e != current_e:
                            if re.search("G1 F(\d*) E(\d.*)", lin) is not None or re.search("G1 F(\d*) E-(\d.*)", lin) is not None or "G10" in lin:
                                if is_retracted == None:
                                    is_retracted = True
                                if current_e is not None:
                                    if is_retracted is None:
                                        is_retracted = False
                            current_e = new_e
                            break

                # Start putting together the pause string 'prepend_gcode'
                prepend_gcode = f";current layer: {current_layer}\n;TYPE:CUSTOM---------------; Pause at end of preview layer {current_layer} (end of Gcode LAYER:{int(current_layer) - 1})\n"
                if pause_method == "repetier":
                    # Retraction
                    prepend_gcode += self.putValue(M = 83) + "; Relative extrusion\n"
                    if not is_retracted:
                        prepend_gcode += self.putValue(G = 1, F = retraction_retract_speed, E = -retraction_amount) + "; Retract\n"
                    if park_enabled:
                        # Move the head to the park location
                        if current_z + move_z > self._machine_height:
                            move_z = 0
                        prepend_gcode += self.putValue(G = 1, F = speed_z_hop, Z = round(current_z + move_z, 2)) + "; Move up to clear the print\n"
                        prepend_gcode += self.putValue(G = 0, X = park_x, Y = park_y, F = travel_speed) + "; Move to park location\n"
                        if current_z < move_z:
                            prepend_gcode += self.putValue(G = 1, F = speed_z_hop, Z = current_z + move_z) + "; Move up to clear the print\n"
                    # Disable the E steppers
                    prepend_gcode += self.putValue(M = 84, E = 0) + "; Disable Steppers\n"

                elif pause_method != "griffin":
                    # Retraction
                    prepend_gcode += self.putValue(M = 83) + "; Relative extrusion\n"
                    if not is_retracted:
                        if firmware_retract:
                            prepend_gcode += "G10\n"
                        else:
                            prepend_gcode += self.putValue(G = 1, F = retraction_retract_speed, E = -retraction_amount) + "; Retract\n"
                    if park_enabled:
                        # Move the head to the park position
                        if current_z + move_z > self._machine_height:
                            move_z = 0
                        prepend_gcode += self.putValue(G = 1, F = speed_z_hop, Z = round(current_z + move_z, 2)) + "; Move up to clear the print\n"
                        prepend_gcode += self.putValue(G = 0, F = travel_speed, X = park_x, Y = park_y) + "; Move to park location\n"
                        if current_z < min_purge_clearance - move_z:
                            prepend_gcode += self.putValue(G = 1, F = speed_z_hop, Z = min_purge_clearance) + "; Minimum clearance" + str(" to purge" if purge_amount != 0 and reason_for_pause == 'reason_filament' else "") + " - move up some more\n"
                            
                    # 'Unload' and 'purge' are only available if there is a filament change.
                    if reason_for_pause == "reason_filament" and int(unload_amount) > 0:
                        # If it's a filament change then insert any 'unload' commands
                        prepend_gcode += self.putValue(M = 400) + "; Complete all moves\n"
                        # Break up the unload distance into chunks of 150mm to avoid any firmware balks for 'too long of an extrusion'
                        if unload_amount > 0:
                            # The quick purge is meant to soften the filament end to insure it will retract.
                            if unload_quick_purge:
                                quick_purge_amt = retraction_amount + 7 if retraction_amount < 2 else retraction_amount * 2.5
                                prepend_gcode += f"G1 F{purge_speed} E{quick_purge_amt} ; Quick purge before unload\n"
                        if unload_amount > 150:
                            temp_unload = unload_amount
                            while temp_unload > 150:
                                prepend_gcode += self.putValue(G = 1, F = int(unload_reload_speed), E = -150) + "; Unload some\n"
                                temp_unload -= 150
                            if 0 < temp_unload <= 150:
                                prepend_gcode += self.putValue(G = 1, F = int(unload_reload_speed), E = -temp_unload) + "; Unload the remainder\n"
                        else:
                            prepend_gcode += self.putValue(G = 1, E = -unload_amount, F = int(unload_reload_speed)) + "; Unload\n"

                    # Set extruder standby temperature
                    if control_temperatures:
                        prepend_gcode += self.putValue(M = 104, S = standby_temperature) + "; Standby temperature\n"

                if display_text:
                    prepend_gcode += "M117 " + txt_msg + "; Message to LCD\n"

                # Set the disarm timeout
                if pause_method != "griffin":
                    if hold_steppers_on and int(disarm_timeout) > 0:
                        prepend_gcode += self.putValue(M = 84, S = disarm_timeout) + "; Keep steppers engaged for " + str(disarm_timeout/60) + " minutes\n"

                # Beep at pause
                if beep_at_pause:
                    prepend_gcode += self.putValue(M = 300, S = 440, P = beep_length) + "; Beep\n"

                # Set a custom GCODE section before pause
                if gcode_before:
                    prepend_gcode += gcode_before + "\n"
                    
                if txt_msg:
                    prepend_gcode += "M118 " + str(txt_msg) + " ; Message to print server\n"
                    
                # Wait till the user continues printing
                prepend_gcode += pause_command + "; Do the actual pause\n"

                # Set a custom GCODE section after pause
                if gcode_after:
                    prepend_gcode += gcode_after + "\n"

                if pause_method == "repetier":
                    # Optionally extrude material
                    if int(purge_amount) != 0:
                        prepend_gcode += self.putValue(G = 1, F = purge_speed, E = purge_amount) + "; Extra extrude after the unpause\n"
                        prepend_gcode += self.putValue("     @info wait for cleaning nozzle from previous filament") + "\n"
                        prepend_gcode += self.putValue("     @pause remove the waste filament from parking area and press continue printing") + "\n"

                    # Retract before moving back to the print.
                    if purge_amount != 0:
                        prepend_gcode += self.putValue(G = 1, E = -retraction_amount, F = retraction_retract_speed) + ";Retract\n"

                    # Move the head back to the resume position
                    if park_enabled:
                        prepend_gcode += self.putValue(G = 0, F = travel_speed, X = x, Y = y) + ";Return to print location\n"
                        prepend_gcode += self.putValue(G = 1, F = speed_z_hop, Z = current_z) + ";Drop down to print height\n"

                    if purge_amount != 0:
                        prepend_gcode += self.putValue(G = 1, E = retraction_amount, F = retraction_prime_speed) + ";Unretract\n"

                    extrusion_mode_string = "absolute"
                    extrusion_mode_numeric = 82

                    relative_extrusion = Application.getInstance().getGlobalContainerStack().getProperty("relative_extrusion", "value")
                    if relative_extrusion:
                        extrusion_mode_string = "relative"
                        extrusion_mode_numeric = 83

                    prepend_gcode += self.putValue(M = extrusion_mode_numeric) + "; switch back to " + extrusion_mode_string + " E values\n"

                    # Reset extruder value to pre pause value
                    prepend_gcode += self.putValue(G = 92, E = current_e) + ";Reset extruder\n"

                elif pause_method != "griffin":
                    if control_temperatures:
                        # Set extruder resume temperature
                        if resume_temperature_cmd == "m109_cmd" or use_tool_temperature:
                            WFT_numeric = 109
                            Temp_resume_Text = "; Wait for resume temperature\n"
                        else:
                            WFT_numeric = 104
                            Temp_resume_Text = "; Resume temperature\n"

                        prepend_gcode += self.putValue(M=WFT_numeric, S=int(resume_print_temperature)) + Temp_resume_Text

                    # Load and Purge.  Break the load amount in 150mm chunks to avoid 'too long of extrusion' warnings from firmware.
                    if reason_for_pause == "reason_filament":
                        if int(reload_amount) > 0:
                            if reload_amount * .9 > 150:
                                temp_reload = reload_amount - reload_amount * .1
                                while temp_reload > 150:
                                    prepend_gcode += self.putValue(G = 1, E = 150, F = unload_reload_speed) + "; Fast Reload\n"
                                    temp_reload -= 150
                                if 0 < temp_reload <= 150:
                                    prepend_gcode += self.putValue(G = 1, E = round(temp_reload), F = round(int(unload_reload_speed))) + "; Fast Reload\n"
                                    prepend_gcode += self.putValue(G = 1, E = round(reload_amount * .1), F = round(float(nozzle_size) * 16.666 * 60)) + "; Reload the remaining 10% slow to avoid ramming the nozzle\n"
                                else:
                                    prepend_gcode += self.putValue(G = 1, E = round(reload_amount * .1), F = round(float(nozzle_size) * 16.666 * 60)) + "; Reload the remaining 10% slow to avoid ramming the nozzle\n"
                            else:
                                prepend_gcode += self.putValue(G = 1, E = round(reload_amount * .9), F = round(int(unload_reload_speed))) + "; Fast Reload\n"
                                prepend_gcode += self.putValue(G = 1, E = round(reload_amount * .1), F = round(float(nozzle_size) * 16.666 * 60)) + "; Reload the last 10% slower to avoid ramming the nozzle\n"
                        if int(purge_amount) > 0:
                            prepend_gcode += self.putValue(G = 1, E = purge_amount, F = round(float(nozzle_size) * 8.333 * 60)) + "; Purge\n"
                            if not firmware_retract:
                                prepend_gcode += self.putValue(G = 1, E = -retraction_amount, F = int(retraction_retract_speed)) + "; Retract\n"
                            else:
                                prepend_gcode += self.putValue(G = 10) + "; Retract\n"
                            # If there is a purge then give the user time to grab the string before the head moves back to the print position.
                            prepend_gcode += self.putValue(M = 400) + "; Complete all moves\n"
                            prepend_gcode += self.putValue(M = 300, P=250) + "; Beep\n"
                            prepend_gcode += self.putValue(G = 4, S = 2) + "; Wait for 2 seconds\n"

                    # Move the head back
                    if park_enabled:
                        prepend_gcode += self.putValue(G = 0, F = travel_speed, X = x, Y = y) + "; Move to resume location\n"
                        prepend_gcode += self.putValue(G = 1, F = speed_z_hop, Z = current_z) + "; Move back down to resume height\n"

                    if purge_amount != 0:
                        if firmware_retract and not is_retracted:
                            retraction_count = 1 if control_temperatures else 3 # Retract more if we don't control the temperature.
                            for i in range(retraction_count):
                                prepend_gcode += self.putValue(G = 11) + ";Unretract\n"
                        else:
                            if not is_retracted:
                                prepend_gcode += self.putValue(G = 1, F = retraction_prime_speed, E = retraction_amount) + "; Unretract\n"

                    # If the pause is for something like an insertion then there might be an extra prime amount
                    if extra_prime_amount != "0" and reason_for_pause == "reason_other":
                        prepend_gcode += self.putValue(G = 1, E = extra_prime_amount, F = int(retraction_prime_speed)) + "; Extra Prime\n"

                    extrusion_mode_string = "absolute"
                    extrusion_mode_numeric = 82

                    relative_extrusion = Application.getInstance().getGlobalContainerStack().getProperty("relative_extrusion", "value")
                    if relative_extrusion:
                        extrusion_mode_string = "relative"
                        extrusion_mode_numeric = 83

                    if not redo_layer:
                        prepend_gcode += self.putValue(M = extrusion_mode_numeric) + "; Switch back to " + extrusion_mode_string + " E values\n"

                    # Reset extrude value to pre pause value
                        prepend_gcode += self.putValue(G = 92, E = 0 if relative_extrusion else current_e) + "; Reset extruder location\n"

                    if redo_layer and reason_for_pause == "reason_filament":
                        # All other options reset the E value to what it was before the pause because E things were added.
                        # If it's not yet reset, it still needs to be reset if there were any redo layers.
                        if is_retracted:
                            prepend_gcode += self.putValue(G = 92, E = 0 if relative_extrusion else current_e - retraction_amount) + "; Reset extruder location ~ retracted\n"
                            prepend_gcode += self.putValue(M = extrusion_mode_numeric) + "; Switch back to " + extrusion_mode_string + " E values\n"
                        else:
                            prepend_gcode += self.putValue(G = 92, E = 0 if relative_extrusion else current_e) + "; Reset extruder location ~ unretracted\n"
                            prepend_gcode += self.putValue(M = extrusion_mode_numeric) + "; Switch back to " + extrusion_mode_string + " E values\n"
                    elif redo_layer and reason_for_pause == "reason_other":
                        prepend_gcode += self.putValue(M = extrusion_mode_numeric) + "; Switch back to " + extrusion_mode_string + " E values\n"
                # Format prepend_gcode
                prepend_gcode += f";{'-' * 26}; End of the Pause code"
                temp_lines = prepend_gcode.split("\n")
                for temp_index, temp_line in enumerate(temp_lines):
                    if ";" in temp_line and not temp_line.startswith(";"):
                        temp_lines[temp_index] = temp_line.replace(temp_line.split(";")[0], temp_line.split(";")[0] + str(" " * (27 - len(temp_line.split(";")[0]))),1)
                prepend_gcode = "\n".join(temp_lines)
                # Insert the Pause Prepend snippet at the end of the previous layer just before "TIME_ELAPSED".
                layer_lines = new_data[index - 1].split("\n")
                layer_lines.insert(len(layer_lines) - 2, prepend_gcode)
                new_data[index -1 ] = "\n".join(layer_lines)
                return new_data
        return new_data

    # Renumber Layers----------------------------------------------------------
    def _renumber_layers(self, one_data:str, renum:str)->str:
        renum_layers = str(renum)

        # Count the layers because "LAYER_COUNT" can be theoretical
        layer0_index = 2
        for num in range(1,len(one_data)-1,1):
            layer = one_data[num]
            if ";LAYER:0" in layer:
                layer0_index = num
                break

        # Concantenate the one_data list items that were added to the beginning of each separate model
        for num in range(layer0_index,len(one_data) - 2,1):
            if num + 1 == len(one_data) - 2: break # Avoid concantenating the Ending Gcode
            try:
                while not ";LAYER:" in one_data[num + 1]:
                    one_data[num] += str(one_data[num + 1]) + "\n"
                    one_data.pop(num + 1)
            except:
                continue

        # Renumber the layers
        if renum_layers == "renum":
            lay_num = 0
            for num in range(layer0_index,len(one_data),1):
                layer = one_data[num]
                if layer.startswith(";LAYER:") and not layer.startswith(";LAYER:-"):
                    temp = layer.split("\n")
                    one_data[num] = layer.replace(temp[0],";LAYER:" + str(lay_num))
                    lay_num += 1
            layer = one_data[layer0_index - 1]

        # Revert the numbering to OneAtATime if enabled
        elif renum_layers == "un_renum":
            lay_num = 0
            for num in range(layer0_index,len(one_data),1):
                layer = one_data[num]
                if layer.startswith(";LAYER:") and not layer.startswith(";LAYER:-"):
                    temp = layer.split("\n")
                    one_data[num] = layer.replace(temp[0],";LAYER:" + str(lay_num))
                    lay_num += 1
                if ";LAYER_COUNT:" in layer:
                    lay_num = 0
            layer = one_data[layer0_index - 1]

        # Move the 'Time_elapsed' and 'Layer_Count' lines to the end of their one_data sections in case of a following PauseAtHeight
        modified_data = ""
        for num in range(2,len(one_data)-2,1):
            layer = one_data[num]
            lines = layer.split("\n")
            modified_data = ""
            time_line = ""
            for line in lines:
                if line.startswith(";TIME_ELAPSED:") or line.startswith(";LAYER_COUNT:"):
                    time_line += line + "\n"
                    line = ""
                if line != "":
                    modified_data += line + "\n"
            one_data[num] = modified_data + time_line

        # If re-numbering then change each LAYER_COUNT line to reflect the new total layers
        if renum_layers == "renum":
            for num in range(1,len(one_data)-1,1):
                layer = one_data[num]
                one_data[num] = re.sub(";LAYER_COUNT:(\d*)",";LAYER_COUNT:" + str(len(one_data) - 3),layer)

        # If reverting to one-at-a-time then change the LAYER_COUNT back to per model
        elif renum_layers == "un_renum":
            model_lay_count = 0
            for num in range(len(one_data)-1,1,-1):
                if ";LAYER:" in one_data[num]:
                    model_lay_count += 1
                if ";LAYER:0" in one_data[num]:
                    one_data[num-1] = re.sub(";LAYER_COUNT:(\d*)",";LAYER_COUNT:" + str(model_lay_count), one_data[num-1])
                    model_lay_count = 0
        return one_data