# 2024 Greg Foresi (GregValiant)
#
# Description:  Post processing script to add M207 and M208 commands to the StartUp Gcode to configure firmware retraction.
#    There are 3 settings and are installed below "Firmware Retraction" in the Machine Settings.
#    Z-hops are an option.  The rest of the settings come from the Travel settings (and Dual Settings if applicable).
#
# Cura maximum version is in line 22.  The '0' is added to accomodate 5.10.0 if it is released.

from collections import OrderedDict
from UM.Message import Message
from UM.Extension import Extension
from UM.Application import Application
from UM.Settings.SettingDefinition import SettingDefinition
from UM.Settings.DefinitionContainer import DefinitionContainer
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Logger import Logger
from UM.Message import Message

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
            Message(title = "[Max Volumetric Flow]", text = "Did not load because it has not been tested with Cura Versions less than 5.6.0 or greater than 5.9.0.").show()
            return
        self._application = Application.getInstance()

        self._i18n_catalog = None

        self._settings_dict = OrderedDict()
        self._settings_dict["max_volumetric_speed_enable"] = {
            "label": "Enable Volumetric Speed Limit",
            "description": "If you wish to control the print speed to keep it under your max volumetric limit - enable this command.  Travel speeds are not affected.",
            "type": "bool",
            "value": False,
            "default_value": False,
            "enabled": True
        }
        self._settings_dict["enable_hop_t0"] = {
            "label": "    Max Volumetric Flow",
            "description": "Enter the maximum volumetric flow rate that your printer is comfortable with.",
            "type": "bool",
            "default_value": False,
            "enabled": "config_firmware_retract_enable and machine_firmware_retract"
        }
        self._settings_dict["enable_hop_t1"] = {
            "label": "        Enable Z hops (T1)",
            "description": "Enable Z-hops for the second extruder.  When this is enabled there will be Z-hops for every retraction.  The 'Z-Hop Height' for Extruder 2 from the Cura Travel Settings will be used.  You should disable 'Z-Hop on Retraction' for Extruder 2 in the Travel Settings.",
            "type": "bool",
            "default_value": False,
            "enabled": "config_firmware_retract_enable and machine_firmware_retract and machine_extruder_count > 1"
        }

        ContainerRegistry.getInstance().containerLoadComplete.connect(self._onContainerLoadComplete)

        self._application.getOutputDeviceManager().writeStarted.connect(self._ParseGcode)


    def _onContainerLoadComplete(self, container_id):
        if not ContainerRegistry.getInstance().isLoaded(container_id):
            # skip containers that could not be loaded, or subsequent findContainers() will cause an infinite loop
            return

        try:
            container = ContainerRegistry.getInstance().findContainers(id = container_id)[0]

        except IndexError:
            # the container no longer exists
            return

        if not isinstance(container, DefinitionContainer):
            # skip containers that are not definitions
            return

        machine_category = container.findDefinitions(key="machine_settings")

        config_firmware_retract_enable = container.findDefinitions(key=list(self._settings_dict.keys())[0])
        enable_hop_t0 = container.findDefinitions(key=list(self._settings_dict.keys())[1])
        enable_hop_t1 = container.findDefinitions(key=list(self._settings_dict.keys())[2])

        cura_version = str(Application.getInstance().getVersion())
        if "5.8" in cura_version:
            insert_pt = 33
        elif "5.7" in cura_version:
            insert_pt = 31
        elif "5.9" in cura_version:
            insert_pt = 33
        else:
            insert_pt = 31
        if machine_category:
            machine_category = machine_category[0]
            for setting_key, setting_dict in self._settings_dict.items():

                definition = SettingDefinition(setting_key, container, machine_category, self._i18n_catalog)
                definition.deserialize(setting_dict)

                # add the setting to the already existing platform adhesion setting definition
                machine_category._children.insert(insert_pt, definition)
                container._definition_cache[setting_key] = definition
                container._updateRelations(definition)
                insert_pt += 1

    def _ParseGcode(self, output_device):
        scene = self._application.getController().getScene()

        global_container_stack = self._application.getGlobalContainerStack()
        if not global_container_stack:
            return

        extruder = global_container_stack.extruderList
        config_firmware_retract_enable = extruder[0].getProperty("config_firmware_retract_enable", "value")

        # get settings from Cura
        zhop_t0 = extruder[0].getProperty("enable_hop_t0", "value")
        if global_container_stack.getProperty("machine_extruder_count", "value") > 1:
            zhop_t1 = extruder[0].getProperty("enable_hop_t1", "value")
        else:
            zhop_t1 = False

        gcode_dict = getattr(scene, "gcode_dict", {})
        if not gcode_dict: # this also checks for an empty dict
            Logger.log("w", "Scene has no gcode to process")
            return

        dict_changed = False
        for plate_id in gcode_dict:
            gcode_list = gcode_dict[plate_id]
            if len(gcode_list) < 2:
                Logger.log("w", "G-Code %s does not contain any layers", plate_id)
                continue

            # Exit if the script is not enabled
            if not config_firmware_retract_enable:
                Logger.log("i", "[Configure Firmware Retract] was not enabled.")
                return

            # If the gcode has already been processed then don't run again.
            if ";  [Configure Firmware Retraction] plugin is enabled\n" not in gcode_list[0]:
                if not config_firmware_retract_enable:
                    gcode_list[0] += ";    [Configure Firmware Retraction] Not enabled\n"
                    return
                # If 'Firmware Retraction' is not enabled then don't run
                if not global_container_stack.getProperty("machine_firmware_retract", "value"):
                    return

                # Get the relevant settings from Cura for the T0 M207 and M208 strings
                extruder_count = global_container_stack.getProperty("machine_extruder_count", "value")
                t0_string = ""
                t1_string = ""
                t0_retract_amt = extruder[0].getProperty("retraction_amount", "value")
                t0_tool_swap_amt = extruder[0].getProperty("switch_extruder_retraction_amount", "value")
                t0_tool_swap_extra_amt = extruder[0].getProperty("switch_extruder_extra_prime_amount", "value")
                t0_retract_speed = extruder[0].getProperty("retraction_retract_speed", "value")
                t0_tool_swap_retract_speed = extruder[0].getProperty("switch_extruder_retraction_speeds", "value")
                if bool(extruder[0].getProperty("enable_hop_t0", "value")):
                    t0_hop_hgt = extruder[0].getProperty("retraction_hop", "value")
                else:
                    t0_hop_hgt = 0.0
                t0_prime_speed = extruder[0].getProperty("retraction_prime_speed", "value")
                t0_extra_prime_amt = extruder[0].getProperty("retraction_extra_prime_amount", "value")
                if extruder_count == 1:
                    t0_nr = ""
                    t0_tool_swap_amt = ""
                    t0_tool_swap_extra_amt = ""
                    t0_tool_swap_retract_speed = ""
                    t0_m207_desc = "; Configure G10 Retract ('S'retract amt, 'F'retract speed, 'Z'zhop hgt)"
                    t0_m208_desc = "; Configure G11 Prime ('S'extra prime amt, 'F'prime speed)"
                # Account for the different parameters used for multi-extruder printers
                else:
                    t0_nr = "T0 "
                    t0_tool_swap_amt = f"W{t0_tool_swap_amt} "
                    t0_tool_swap_extra_amt = f"W{t0_tool_swap_extra_amt} "
                    t0_tool_swap_retract_speed = f"R{t0_tool_swap_retract_speed*60} "
                    t0_m207_desc = "; Configure G10 Retract ('T'tool num, 'S'retract amt, 'F'retract speed, 'W'tool switch amt, 'Z'Z-hop hgt)"
                    t0_m208_desc = "; Configure G11 Prime ('T'tool num, 'S'extra prime amt, 'F'prime speed, 'W'tool switch extra prime amt, 'R'tool switch retract speed)"
                t0_string = f"\n;\nM207 {t0_nr}S{t0_retract_amt} F{t0_retract_speed*60} {t0_tool_swap_amt}Z{t0_hop_hgt}"
                t0_string = t0_string + str(" " * (35 - len(t0_string))) + t0_m207_desc
                t0_string2 = f"\nM208 {t0_nr}S{t0_extra_prime_amt} F{t0_prime_speed*60} {t0_tool_swap_extra_amt}{t0_tool_swap_retract_speed}"
                t0_string2 = t0_string2 + str(" " * (33 - len(t0_string2))) + t0_m208_desc
                t0_string += t0_string2
                # If it is a multi-extruder printer then get the settings for T1
                if extruder_count > 1:
                    t1_retract_amt = extruder[1].getProperty("retraction_amount", "value")
                    t1_tool_swap_amt = extruder[1].getProperty("switch_extruder_retraction_amount", "value")
                    t1_tool_swap_extra_amt = extruder[1].getProperty("switch_extruder_extra_prime_amount", "value")
                    t1_retract_speed = extruder[1].getProperty("retraction_retract_speed", "value")
                    t1_tool_swap_retract_speed = extruder[1].getProperty("switch_extruder_retraction_speeds", "value")
                    if bool(extruder[0].getProperty("enable_hop_t1", "value")):
                        t1_hop_hgt = extruder[1].getProperty("retraction_hop", "value")
                    else:
                        t1_hop_hgt = 0.0
                    t1_prime_speed = extruder[1].getProperty("retraction_prime_speed", "value")
                    t1_extra_prime_amt = extruder[1].getProperty("retraction_extra_prime_amount", "value")
                    t1_string = f"\nM207 T1 S{t1_retract_amt} F{t1_retract_speed*60} W{t1_tool_swap_amt} Z{t1_hop_hgt}"
                    t1_string = t1_string + str(" " * (33 - len(t1_string))) + "; Configure G10 Retract"
                    t1_string2 = f"\nM208 T1 S{t1_extra_prime_amt} F{t1_prime_speed*60} W{t1_tool_swap_extra_amt} R{t1_tool_swap_retract_speed*60}"
                    t1_string2 = t1_string2 + str(" " * (33 - len(t1_string2))) + "; Configure G11 Prime"
                    t1_string += t1_string2

                # Insert the string(s) at the beginning of the StartUp Gcode
                start_up = gcode_list[1].split("\n")
                for index, line in enumerate(start_up):
                    if ";Generated with Cura_SteamEngine" in line:
                        start_up[index] += t0_string
                        if extruder_count > 1:
                            start_up[index] += t1_string + "\n;"
                        else:
                            start_up[index] += "\n;"
                gcode_list[1] = "\n".join(start_up)
                gcode_list[0] += ";  [Configure Firmware Retraction] plugin is enabled\n"
                gcode_dict[plate_id] = gcode_list
                dict_changed = True
            else:
                Logger.log("d", "G-Code %s has already been processed", plate_id)
                continue
            if dict_changed:
                setattr(scene, "gcode_dict", gcode_dict)
        return