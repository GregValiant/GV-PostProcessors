# 2024 Greg Foresi (GregValiant)
#  This script uses M203 increase the Espeed for retractions and primes and immediately after, lowers the E speed to max speed for the input volumetric limit.

from collections import OrderedDict
from UM.Message import Message
from UM.Extension import Extension
from UM.Application import Application
from UM.Settings.SettingDefinition import SettingDefinition
from UM.Settings.DefinitionContainer import DefinitionContainer
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Logger import Logger
from UM.Message import Message
import math
import re

class MaxVolumetricFlowPlugin(Extension):
    def __init__(self):
        super().__init__()
        # Min and Max versions numbers are adjusted with the extra 0 in case 5.10 is released
        cura_min_version = 4.130
        cura_max_version = 5.090
        cura_version = Application.getInstance().getVersion()
        if "-" in cura_version:
            cura_version = cura_version.split("-")[0]
        cura_sub = cura_version.split(".")
        cura_maj = cura_sub[0]
        cura_min = cura_sub[1] if len(cura_sub[1]) >= 2 else "0" + cura_sub[1]
        if len(cura_sub) == 2:
            suffix = 0
        else:
            suffix = cura_sub[2]
        cura_ver = float(str(cura_maj) + "." + str(cura_min) + str(suffix))
        # Exit if the version number is above max or less than min.
        if cura_ver < cura_min_version or cura_ver > cura_max_version:
            Logger.log("w", "[Max Volumetric Flow] Did not load because it has not been tested with Cura Versions less than 5.6.0 or greater than 5.9.0.")
            Message(title = "[Max Volumetric Flow Plugin]", text = "Did not load because it has not been tested with Cura Versions less than 5.6.0 or greater than 5.9.0.").show()
            return
        self._application = Application.getInstance()

        self._i18n_catalog = None

        self._settings_dict = OrderedDict()
        self._settings_dict["max_volumetric_flow_plugin_enable"] = {
            "label": "Volumetric Speed Control",
            "description": "When enabled - M203 will be used to adjust the 'maximum E speed' in the printer to limit the flow rate through the nozzle.  The formula is 'Max Flow Rate / Filament Cross-section Area'.",
            "type": "bool",
            "value": False,
            "default_value": False,
            "settable_per_extruder": True,
            "enabled": True
        }
        self._settings_dict["max_volume_flow_rate"] = {
            "label": "   Maximum Flow Rate",
            "description": "Limit the E motor speed so that this Volumetric Maximum is not exceeded.  This does not affect Travel Speeds.  This setting may affect the print time and that will not be reflected in the Cura time estimate.",
            "type": "float",
            "unit": "mm³/sec",
            "default_value": 12.0,
            "settable_per_extruder": True,
            "enabled": "max_volumetric_flow_plugin_enable"
        }
        self._settings_dict["use_units"] = {
            "label": "    The units for M203",
            "description": "Most firmwares (Ex: Marlin) use mm/second for the M203 Max Speeds.  RepRap might use mm/minute.",
            "type": "enum",
            "options": {
                "per_second": "mm / second",
                "per_minute": "mm / minute" },
            "default_value": "per_second",
            "limit_to_extruder": 0,
            "enabled": "max_volumetric_flow_plugin_enable"
        }
        self._settings_dict["enable_jerk_adjustment"] = {
            "label": "    Enable Jerk adjustment for retracts",
            "description": "Check the box to also add commands (M205 or M566) to adjust the Jerk for each retract and prime.",
            "type": "bool",
            "default_value": False,
            "settable_per_extruder": True,
            "enabled": "max_volumetric_flow_plugin_enable"
        }
        self._settings_dict["jerk_cmd"] = {
            "label": "        Jerk Command",
            "description": "Most firmwares (Ex: Marlin) use M205 for Jerk.  RepRap/Repetier might use M566.  You need to know which is correct.",
            "type": "enum",
            "options": {
                "M205": "M205",
                "M566": "M566" },
            "default_value": "M205",
            "limit_to_extruder": 0,
            "enabled": "max_volumetric_flow_plugin_enable and enable_jerk_adjustment"
        }
        self._settings_dict["max_e_jerk"] = {
            "label": "        Retract/Prime Jerk",
            "description": "This will adjust the Jerk before each retract/prime and then reset it after.  The reset value is 'Default Filament Jerk' in the Cura 'Printer Settings'.  The 'Printer Settings' plugin from the MarketPlace must be installed to access it.",
            "type": "float",
            "unit": "mm/sec  ",
            "default_value": 10,
            "settable_per_extruder": True,
            "enabled": "max_volumetric_flow_plugin_enable and enable_jerk_adjustment"
        }

        ContainerRegistry.getInstance().containerLoadComplete.connect(self._onContainerLoadComplete)

        self._application.getOutputDeviceManager().writeStarted.connect(self._ParseGcode)

    def _onContainerLoadComplete(self, container_id):
        if not ContainerRegistry.getInstance().isLoaded(container_id):
            # skip bad containers
            return

        try:
            container = ContainerRegistry.getInstance().findContainers(id = container_id)[0]
        except IndexError:
            # the container no longer exists
            return

        if not isinstance(container, DefinitionContainer):
            # Only use a definition container
            return

        # The settings will go at the top of the 'Speed' settings for each extruder.
        speed_category = container.findDefinitions(key="speed")
        max_volumetric_flow_plugin_enable = container.findDefinitions(key=list(self._settings_dict.keys())[0])
        max_volume_flow_rate = container.findDefinitions(key=list(self._settings_dict.keys())[1])
        use_units = container.findDefinitions(key=list(self._settings_dict.keys())[2])
        enable_jerk_adjustment = container.findDefinitions(key=list(self._settings_dict.keys())[3])
        jerk_cmd = container.findDefinitions(key=list(self._settings_dict.keys())[4])
        max_e_jerk = container.findDefinitions(key=list(self._settings_dict.keys())[5])

        cura_version = str(Application.getInstance().getVersion())
        insert_pt = 0
        if speed_category:
            speed_category = speed_category[0]
            for setting_key, setting_dict in self._settings_dict.items():
                definition = SettingDefinition(setting_key, container, speed_category, self._i18n_catalog)
                definition.deserialize(setting_dict)
                # Add each setting to the existing speed setting definition
                speed_category._children.insert(insert_pt, definition)
                container._definition_cache[setting_key] = definition
                container._updateRelations(definition)
                insert_pt += 1

    def _ParseGcode(self, output_device):
        scene = self._application.getController().getScene()
        # Define the stack
        cura_stack = self._application.getGlobalContainerStack()
        if not cura_stack:
            Logger.log("w", "No GlobarContainerStack")
            return

        # Make sure there is a dictionary and it isn't empty
        gcode_dict = getattr(scene, "gcode_dict", {})
        if not gcode_dict:
            Logger.log("w", "Scene has no gcode to process")
            return

        dict_changed = False
        for plate_id in gcode_dict:
            gcode_list = gcode_dict[plate_id]
            if len(gcode_list) < 2:
                Logger.log("w", "G-Code %s does not contain any layers", plate_id)
                continue

            # Get some settings
            extruder = cura_stack.extruderList
            extruder_count = cura_stack.getProperty("machine_extruder_count", "value")
            firmware_retraction = bool(cura_stack.getProperty("machine_firmware_retract", "value"))
            max_flow_enable_t0 = extruder[0].getProperty("max_volumetric_flow_plugin_enable", "value")
            max_flow_enable_t1 = extruder[1].getProperty("max_volumetric_flow_plugin_enable", "value") if extruder_count > 1 else False
            use_mm_per_sec = True if extruder[0].getProperty("use_units", "value") == "per_second" else False
            jerk_cmd = extruder[0].getProperty("jerk_cmd", "value")

            # Exit if the script is not enabled
            if not max_flow_enable_t0 and not max_flow_enable_t1:
                Logger.log("i", "[Max Volumetric Flow Plugin] was not enabled.")
                return

            # Only run if the G-Code has not been post-processed.
            if not ";  [Max Volumetric Flow] Plugin is enabled\n" in gcode_list[0]:
                # These need values in only 1 extruder is being adjusted
                speed_e_reset_t1 = 35
                filament_dia_t1 = 1.75
                nozzle_size_t1 = 0.40
                speed_e_reset_t0 = float(extruder[0].getProperty("retraction_retract_speed", "value"))
                speed_e_reset_t1 = speed_e_reset_t0
                filament_dia_t0 = extruder[0].getProperty("material_diameter", "value")
                filament_dia_t1 = filament_dia_t0
                nozzle_size_t0 = extruder[0].getProperty("machine_nozzle_size", "value")
                nozzle_size_t1 = nozzle_size_t0
                if max_flow_enable_t0:
                    max_rate_for_t0 = float(extruder[0].getProperty("max_volume_flow_rate", "value"))
                    retract_enabled_t0 = bool(extruder[0].getProperty("retraction_enable", "value"))
                    cura_retract_speed_t0 = float(extruder[0].getProperty("retraction_retract_speed", "value"))
                    cura_prime_speed_t0 = float(extruder[0].getProperty("retraction_prime_speed", "value"))
                    speed_e_reset_t0 = cura_retract_speed_t0 if cura_retract_speed_t0 >= cura_prime_speed_t0 else cura_prime_speed_t0

                if max_flow_enable_t1 and extruder_count > 1:
                    max_rate_for_t1 = extruder[1].getProperty("max_volume_flow_rate", "value")
                    nozzle_size_t1 = extruder[1].getProperty("machine_nozzle_size", "value")
                    filament_dia_t1 = extruder[1].getProperty("material_diameter", "value")
                    retract_enabled_t1 = bool(extruder[1].getProperty("retraction_enable", "value"))
                    cura_retract_speed_t1 = float(extruder[1].getProperty("retraction_retract_speed", "value"))
                    cura_prime_speed_t1 = float(extruder[1].getProperty("retraction_prime_speed", "value"))
                    speed_e_reset_t1 = cura_retract_speed_t1 if cura_retract_speed_t1 >= cura_prime_speed_t1 else cura_prime_speed_t1

                jerk_control_enable_t0 = extruder[0].getProperty("enable_jerk_adjustment", "value") if max_flow_enable_t0 else False
                jerk_control_enable_t1 = extruder[1].getProperty("enable_jerk_adjustment", "value") if extruder_count > 1 and max_flow_enable_t1 else False
                if jerk_control_enable_t0:
                    extruder_jerk_t0 = round(extruder[0].getProperty("max_e_jerk", "value"),1)
                    default_jerk_t0 = cura_stack.getProperty("machine_max_jerk_e", "value")
                if jerk_control_enable_t1:
                    extruder_jerk_t1 = round(extruder[1].getProperty("max_e_jerk", "value"),1) if extruder_count > 1 and jerk_control_enable_t1 else round(extruder[0].getProperty("max_e_jerk", "value"),1)
                    default_jerk_t1 = cura_stack.getProperty("machine_max_jerk_e", "value")
                if extruder_count > 1:
                    final_speed_reset = speed_e_reset_t0 if speed_e_reset_t0 >= speed_e_reset_t1 else speed_e_reset_t1
                else:
                    final_speed_reset = speed_e_reset_t0
                # Get the relevant settings from Cura
                # Adjust the 'Retract/Prime' search parameter depending on Firmware Retraction
                if not firmware_retraction:
                    search_string = "G1 F(\d+\.\d+|\d+) E(-?\d+\.\d+|-?\d+)"
                else:
                    search_string = "G1[0-1]"
                search_regex = re.compile(search_string)
                # Calculate the E Speed Maximum for the print
                cross_sect_t0 = ((filament_dia_t0/2)**2)*math.pi
                if max_flow_enable_t0:
                    speed_e_max_t0 = round(max_rate_for_t0 / cross_sect_t0, 2)
                else:
                    speed_e_max_t0 = speed_e_reset_t0
                cross_sect_t1 = ((filament_dia_t1/2)**2)*math.pi
                if max_flow_enable_t1:
                    speed_e_max_t1 = round(max_rate_for_t1 / cross_sect_t1, 2)
                else:
                    speed_e_max_t1 = speed_e_reset_t1
                # RepRap firmware may require that the M203 units are mm/minute
                if not use_mm_per_sec:
                    speed_e_max_t0 = round(speed_e_max_t0 * 60)
                    speed_e_reset_t0 = round(speed_e_reset_t0 * 60)
                    speed_e_max_t1 = round(speed_e_max_t1 * 60)
                    speed_e_reset_t1 = round(speed_e_reset_t1 * 60)
                replacement_before_t0 = ""
                replacement_after_t0 = ""
                replacement_before_t1 = ""
                replacement_after_t1 = ""
                if max_flow_enable_t0:
                    replacement_before_t0 += self._format_line(f"M203 E{speed_e_reset_t0} ; E Speed for Retract and Prime" + (" T0\n" if extruder_count > 1 else "\n"))
                    replacement_after_t0 += "\n" + self._format_line(f"M203 E{speed_e_max_t0} ; E Speed Volume Limit" + (" T0" if extruder_count > 1 else ""))
                if jerk_control_enable_t0:
                    replacement_before_t0 += self._format_line(f"{jerk_cmd} E{extruder_jerk_t0} ; E Jerk for Retract and Prime" + (" T0\n" if extruder_count > 1 else "\n"))
                    replacement_after_t0 += "\n" + self._format_line(f"{jerk_cmd} E{default_jerk_t0} ; E Jerk for Print" + (" T0" if extruder_count > 1 else ""))
                if max_flow_enable_t1:
                    replacement_before_t1 += self._format_line(f"M203 E{speed_e_reset_t1} ; E Speed for Retract and Prime T1\n")
                    replacement_after_t1 += "\n" + self._format_line(f"M203 E{speed_e_max_t1} ; E Speed Volume Limit T1")
                if jerk_control_enable_t1:
                    replacement_before_t1 += self._format_line(f"{jerk_cmd} E{extruder_jerk_t1} ; E Jerk for Retract and Prime T1\n")
                    replacement_after_t1 += "\n" + self._format_line(f"{jerk_cmd} E{default_jerk_t1} ; E Jerk for Print T1")
                # Set the tool number
                active_tool = 0
                # Multi-extruders must track the tool number
                if extruder_count > 1:
                    startup = gcode_list[1].split("\n")
                    for line in startup:
                        if line.startswith("T"):
                            active_tool = int(line[1])
                # Make the replacements
                for num in range(2, len(gcode_list) - 1):
                    lines = gcode_list[num].split("\n")
                    for index, line in enumerate(lines):
                        if line.startswith("T"):
                            active_tool = int(line[1])
                        if active_tool == 0:
                            repl_bef = replacement_before_t0
                            repl_aft = replacement_after_t0
                        else:
                            repl_bef = replacement_before_t1
                            repl_aft = replacement_after_t1
                        if re.search(search_regex, line):
                            lines[index] = repl_bef + line + repl_aft
                    gcode_list[num] = "\n".join(lines)
                # Reset the E speed at the end of the print
                if max_flow_enable_t0 or max_flow_enable_t1:
                    gcode_list[len(gcode_list)-1] = f"M203 E{final_speed_reset} ; Reset max E speed\n" + gcode_list[len(gcode_list)-1]
                # Add a line at the beginning of the gcode to indicate that this script has already been run
                gcode_list[0] += ";  [Max Volumetric Flow] Plugin is enabled\n"
                gcode_dict[plate_id] = gcode_list
                dict_changed = True
            # If the gcode was previously post-processed, leave a note in the Log
            else:
                Logger.log("d", "[Max Volumetric Flow] G-Code %s has already been processed", plate_id)
            if dict_changed:
                setattr(scene, "gcode_dict", gcode_dict)
        return

    def _format_line(self, line: str) -> str:
        line = line.split(";")[0] + (" " * (15 - len(line.split(";")[0]))) + ";" + line.split(";")[1]
        return line