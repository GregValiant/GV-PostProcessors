#------------------------------------------------------------------------------------------------------------------------------------
# Initial Copyright(c) 2024 Greg Foresi (GregValiant)
#
# Flash Forge IDEX Converter is released under the terms of the AGPLv3 or higher.
#
# Description:  Postprocessing script to convert Cura Gcode to Normal, Duplicate, or Mirror gcodes for FLash Forge Creator IDEX printers
#
#------------------------------------------------------------------------------------------------------------------------------------

import re
from collections import OrderedDict
from UM.Message import Message
from UM.Extension import Extension
from UM.Application import Application
from UM.Settings.SettingDefinition import SettingDefinition
from UM.Settings.DefinitionContainer import DefinitionContainer
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Logger import Logger

class FlashForge_IDEX_Plugin(Extension):
    def __init__(self):
        super().__init__()

        self._application = Application.getInstance()

        self._i18n_catalog = None

        self._settings_dict = OrderedDict()
        self._settings_dict["flashforgeidexconverter_enable"] = {
            "label": "Enable Flash Forge IDEX Converter",
            "description": "Enable the converter to create Flash Forge IDEX compatible gcode files from Cura slices.",
            "type": "bool",
            "default_value": True,
            "settable_per_mesh": False,
            "settable_per_extruder": False,
            "settable_per_meshgroup": False,
            "enabled": "machine_extruder_count > 1"
        }
        self._settings_dict["print_mode"] = {
            "label": "    Print Mode",
            "description": "Normal, Duplicate, or Mirror",
            "type": "enum",
            "options": {
                "mode_normal": "Normal",
                "mode_duplicate": "Duplicate",
                "mode_mirror": "Mirror"},
            "default_value": "mode_normal",
            "enabled": "flashforgeidexconverter_enable and machine_extruder_count > 1"
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

        experimental_category = container.findDefinitions(key="experimental")

        flashforgeidexconverter_enable = container.findDefinitions(key=list(self._settings_dict.keys())[0])
        print_mode = container.findDefinitions(key=list(self._settings_dict.keys())[1])

        if experimental_category:
            experimental_category = experimental_category[0]
            for setting_key, setting_dict in self._settings_dict.items():

                definition = SettingDefinition(setting_key, container, experimental_category, self._i18n_catalog)
                definition.deserialize(setting_dict)

                # add the setting to the already existing platform adhesion setting definition
                experimental_category._children.append(definition)
                container._definition_cache[setting_key] = definition
                container._updateRelations(definition)

    def _ParseGcode(self, output_device):
        scene = self._application.getController().getScene()

        global_container_stack = self._application.getGlobalContainerStack()
        if not global_container_stack:
            return
            extruder = global_container_stack.extruderList
            # Check the extruder count to see if more than one is enabled and if that one is T0.
            flashforgeidexconverter_enable = extruder[0].getProperty("flashforgeidexconverter_enable", "value")
            # Exit if more than one extruder is enabled and that extruder is not T0
            if flashforgeidexconverter_enable and int(global_container_stack.getProperty("machine_extruder_count", "value")) == 1:
                Logger.log("w", "[FLash Forge IDEX Converter] Requires multi-extruder printer model.  The plugin did not run.")
                Message(title = "[FLash Forge IDEX Converter]", text = "Requires multi-extruder printer model.  The plugin did not run.").show()
                return
            # get settings from Cura
            print_mode = extruder[0].getProperty("print_mode", "value")
            if not flashforgeidexconverter_enable:
                return

        gcode_dict = getattr(scene, "gcode_dict", {})
        if not gcode_dict: # this also checks for an empty dict
            Logger.log("w", "Scene has no gcode to process")
            return

        dict_changed = False
        interface_not_found = ""
        for plate_id in gcode_dict:
            gcode_list = gcode_dict[plate_id]
            if len(gcode_list) < 2:
                Logger.log("w", "G-Code %s does not contain any layers", plate_id)
                continue
            if ";  [Support-Interface Material Change] plugin is enabled\n" not in gcode_list[0]:
                mycura = Application.getInstance().getGlobalContainerStack()
                extruder = mycura.extruderList
                machine_width = int(mycura.getProperty("machine_width", "value"))
                print_mode = extruder[0].getProperty("print_mode", "value")
                cura_start = gcode_list[0].split("\n")
                for line in cura_start:
                    if "MINX:" in line or "MIN.X:" in line:
                        min_x = abs(float(line.split(":")[1]))
                    if "MAXX:" in line or "MAX.X" in line:
                        max_x = abs(float(line.split(":")[1]))
                x_size = max_x + min_x
                if print_mode != "mode_normal" and x_size > .45 * machine_width or print_mode == "mode_normal" and x_size > machine_width:
                    msgtext = "The X footprint of the 'model+skirt/brim/raft+supports' is " + str(x_size) + "mm.\nYou must view the gcode file in the Flash Print preview to ensure the print will fit the build plate of the printer."
                    Message(title = "[FlashForge Max Footprint]", text = msgtext).show()
                # Exit if the printer is a single extruder printer
                if int(mycura.getProperty("machine_extruder_count", "value")) == 1:
                    Message(title = "[Flash Forge IDEX Temp Tools]", text = "The script only works on dual extruder printers.  The script exited without running").show()
                    return
                if extruder[0].isEnabled:
                    t0_enabled = True
                else:
                    t0_enabled = False
                if extruder[1].isEnabled:
                    t1_enabled = True
                else:
                    t1_enabled = False
                t0_material = str(extruder[0].material.getMetaDataEntry("material", ""))
                t0_temp = str(extruder[0].getProperty("material_print_temperature", "value"))
                t1_material = str(extruder[1].material.getMetaDataEntry("material", ""))
                t1_temp = str(extruder[1].getProperty("material_print_temperature", "value"))
                bed_temp = str(mycura.getProperty("material_bed_temperature", "value"))
                layer_height = str(mycura.getProperty("layer_height", "value"))
                insert_str = ";machine_type: Creator 3\n;right_extruder_material: " + t0_material + "\n;right_extruder_material_density: 1.24\n;left_extruder_material: " + t1_material + "\n;left_extruder_material_density: 1.24\n;filament_diameter0: 1.75\n;right_extruder_temperature: " + t0_temp + "\n;filament_diameter1: 1.75\n;left_extruder_temperature: " + t1_temp + "\n;platform_temperature: " + bed_temp + "\n"
                active_extruder = "0"
                if print_mode == "mode_normal":
                    if t1_enabled and not t0_enabled:
                        active_extruder = "1"
                location_str = ";start gcode\nM118 X31.60 Y69.10 Z26.65"
                if t0_enabled:
                    location_str += " T0"
                if t1_enabled and print_mode in ["mode_mirror", "mode_duplicate"]:
                    location_str += " T1"
                if print_mode == "mode_mirror":
                    location_str += " D1"
                elif print_mode == "mode_duplicate":
                    location_str += " D2"
                location_str += " ; " + print_mode
                if print_mode == "mode_mirror":
                    location_str += "\nM7 T0\nM6 T0\nM6 T1\nM651 S255\nM109 T1"
                elif print_mode == "mode_duplicate":
                    location_str += "\nM7 T0\nM6 T0\nM6 T1\nM651 S255\nM109 T2"
                elif print_mode == "mode_normal":
                    location_str += "\nM7 T0"
                    if t0_enabled:
                        location_str += "\nM6 T0"
                    if t1_enabled:
                        location_str += "\nM6 T1"
                    location_str += "\nM651 S255\nM108 T" + str(active_extruder)
                location_str += "\n;extrude_ratio:1"
                opening_paragraph = gcode_list[1].split("\n")
                opening_paragraph.insert(1, insert_str + location_str)
                gcode_list[1] = "\n".join(opening_paragraph)
                active_tool = "0"
                # Go through the StartUp Gcode section and track the active tool.  It is assumed that the StartUp Gcode is correct and works.  If there is an M106 or M107 it will be changed.
                lines = gcode_list[1].split("\n")
                for index, line in enumerate(lines):
                    if line.startswith("T"):
                        active_tool = self.getValue(line, "T")
                    if line.startswith("M106 S"):
                        if " P" in line:
                            lines[index] = lines[index].replace(" P", " T")
                    if line.startswith("M107"):
                        lines[index] = "M107 T0\nM107 T1"
                gcode_list[1] = "\n".join(lines)

                # Go through all the layers and make the changes.
                for num in range(2, len(gcode_list) - 1):
                    lines = gcode_list[num].split("\n")
                    for index, line in enumerate(lines):
                        if line.startswith("T"):
                            active_tool = str(self.getValue(line, "T"))
                            continue
                        # Rearrange the tool numbers in the temperature lines.  Add the tool number if it isn't there.
                        if line[0:4] in ["M104","M109"]:
                            if " T" in line and not ";" in line:
                                g_cmd = self.getValue(line, "M")
                                tool_num = self.getValue(line, "T")
                                temp = self.getValue(line, "S")
                                lines[index] = f"M{g_cmd} S{temp} T{tool_num}"
                            if not " T" in line and not ";" in line:
                                lines[index] = line + " T" + str(active_tool)
                            if " T" in line and ";" in line:
                                g_cmd = self.getValue(line, "M")
                                tool_num = self.getValue(line, "T")
                                temp = self.getValue(line, "S")
                                c_comment = self._get_comment
                                lines[index] = f"M{g_cmd} S{temp} T{tool_num} {c_comment}"
                            # If there is a comment at the end of the line it needs to be handled differently
                            elif not "T" in line and ";" in line:
                                frt_part = line.split(";")[0].rstrip()
                                frt_part = frt_part + " T" + str(active_tool)
                                c_comment = self._get_comment(line)
                                lines[index] = frt_part + (" " * spaces) + c_comment

                        # Move any F parameters to the end of the line
                        if " F" in line and self.getValue(line, "F") is not None:
                            f_val = self.getValue(line, "F")
                            if not ";" in line:
                                lines[index] = lines[index].replace(" F" + str(f_val), "") + " F" + str(f_val)
                            # If there is a comment at the end of the line it needs to be handled differently
                            else:
                                frt_part = line.split(";")[0].rstrip()
                                c_comment = self._get_comment(line)
                                frt_part = frt_part.replace(" F" + str(f_val), "") + " F" + str(f_val)
                                lines[index] = frt_part + (" " * spaces) + ";" + c_comment
                        # Make adjustments to the fan lines
                        if line.startswith("M107"):
                            lines[index] = "M106 S0 T" + str(active_tool)
                        if line.startswith("M106"):
                            lines[index] = line.replace("P", "T")
                            fan_speed = self.getValue(line, "S")
                            lines[index] += "\nM106 S" + str(fan_speed) + " T"
                            lines[index] += "0" if active_tool == "1" else "1"

                        # Flash print doens't use G0 so change them all to G1
                        if line.startswith("G0"):
                            lines[index] = lines[index].replace("G0", "G1")
                            continue

                        # Changing the "TYPE" lines to "structure" lines allows the preview to show correctly in Flash Print
                        if "TYPE:WALL-OUTER" in line:
                            lines[index] = lines[index].replace("TYPE:WALL-OUTER", "structure:shell-outer")
                            continue
                        if "TYPE:WALL-INNER" in line:
                            lines[index] = lines[index].replace("TYPE:WALL-INNER", "structure:shell-inner")
                            continue
                        if "TYPE:FILL" in line:
                            lines[index] = lines[index].replace("TYPE:FILL", "structure:infill-sparse")
                            continue
                        if "TYPE:SKIN" in line:
                            lines[index] = lines[index].replace("TYPE:SKIN", "structure:infill-solid")
                            continue
                        if "TYPE:SKIRT" in line:
                            lines[index] = lines[index].replace("TYPE:SKIRT", "structure:pre-extrude\n;raft")
                            continue
                        if "TYPE:RAFT" in line:
                            lines[index] = lines[index].replace("TYPE:RAFT", "structure:raft")
                            continue
                        if "TYPE:BRIM" in line:
                            lines[index] = lines[index].replace("TYPE:BRIM", "structure:brim")
                            continue
                        if "TYPE:SUPPORT" in line:
                            lines[index] = ";support-start\n;structure:line-support-sparse"
                            new_index = index + 1
                            for nr in range(new_index, len(lines) - 1):
                                if lines[nr].startswith(";"):
                                    lines[nr] = ";support-end\n" + lines[nr]
                                    break
                            continue
                    gcode_list[num] = "\n".join(lines)

                # This final section adds the ';layer:x.xx' lines that indicate the layer height to the Flash Print Gcode pre-viewer.
                # Both Adaptive Layers and Z-hops must be considered.
                cur_z = float(mycura.getProperty("layer_height_0", "value"))
                z_hop_enabled = bool(extruder[0].getProperty("retraction_hop_enabled", "value"))
                layer_hgt = cur_z
                working_z = cur_z
                prev_z = 0.0
                hop_up = False
                if not z_hop_enabled:
                    for num in range(2, len(gcode_list) - 1):
                        # For one-at-a-time items in the gcode_list[list] that are not layers.
                        if re.search(";LAYER:", gcode_list[num]) is None:
                            continue
                        lines = gcode_list[num].split("\n")
                        for index, line in enumerate(lines):
                            if " Z" in line and self.getValue(line, "Z") is not None:
                                cur_z = float(self.getValue(line, "Z"))
                                layer_hgt = round(cur_z - prev_z, 2)
                                prev_z = cur_z
                            if line.startswith(";LAYER:"):
                                lines[index] = line + "\n;layer:" + str(layer_hgt)
                        gcode_list[num] = "\n".join(lines)

                elif z_hop_enabled:
                    l_index = 0
                    for num in range(1, len(gcode_list) - 1):
                        # For one-at-a-time items in the gcode_list[list] that are not layers.
                        if re.search(";LAYER:", gcode_list[num]) is None:
                            continue
                        lines = gcode_list[num].split("\n")
                        for index, line in enumerate(lines):
                            # In case another post processor added lines before the LAYER line.
                            if re.search(";LAYER:", line) is not None:
                                l_index = index
                                # Track the Z so the actual layer height can be calculated
                            if re.search("G1 Z(\d.*) F(\d.*)", line) is not None:
                                cur_z = float(self.getValue(line, "Z"))
                                continue
                            if line.startswith("G1") and " X" in line and " Y" in line and " Z" in line:
                                cur_z = float(self.getValue(line, "Z"))
                                continue
                            if line.startswith("G1") and " X" in line and " Y" in line and " E" in line:
                                if "\n" not in lines[l_index]:
                                    layer_hgt = round(cur_z - prev_z, 2)
                                    lines[l_index] = lines[l_index] + "\n;layer:" + str(layer_hgt)
                                    prev_z = cur_z
                        gcode_list[num] = "\n".join(lines)
                gcode_list[0] += ";  [Flash Forge IDEX Converter] plugin is enabled\n"
                gcode_dict[plate_id] = gcode_list
                dict_changed = True
            else:
                Logger.log("d", "G-Code %s has already been processed", plate_id)
                continue
        if dict_changed:
            setattr(scene, "gcode_dict", gcode_dict)
        return

    def _get_comment(self, c_line: str) -> str:
        frt_part = c_line.split(";")[0]
        frt_len = len(frt_part)
        frt_part = frt_part.rstrip()
        frt_2_len = len(frt_part)
        spaces = frt_len - frt_2_len
        c_comment = spaces + ";" + line.split(";")[1]
        return c_comment

    def getValue(self, line: str, param: str)->str:
        the_num = line.split(param)[1]
        if " " in the_num:
            the_num = the_num.split(" ")[0]
        return the_num