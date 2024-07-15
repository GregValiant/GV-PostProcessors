# Copyright (c) 2023 GregValiant (Greg Foresi)
#   This post processor adds most of the Cura settings (~400) to the end of the Gcode file.  Which settings are added depends on things like the Extruder Count, Cura setup, etc.
# My thanks to Aldo Hoeben who pointed out how to get the 'currency symbol' from Cura.  It was the icing on the cake.

from UM.Application import Application
import UM.Util
from ..Script import Script
import time
import re
from UM.Qt.Duration import DurationFormat
import configparser
from UM.Preferences import Preferences
from UM.Message import Message
from UM.Platform import Platform
import os

class DiscoverSettings572(Script):
    """Add the Cura settings as a post-script to the g-code.
    """

    def getSettingDataString(self):
        return """{
            "name": "Discover Settings 5.7.2",
            "key": "DiscoverSettings572",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "cura_version":
                {
                    "label": "Cura version number to check.",
                    "description": "Enter the version number.  The script should find fdmprinter.def.json and check all the settings in the file.",
                    "type": "enum",
                    "options": {
                        "v5_72": "5.7.2",
                        "v5_71": "5.7.1",
                        "v5_70": "5.7.0",
                        "v5_6": "5.6.0",
                        "v5_5": "5.5.0",
                        "v5_4": "5.4.0",
                        "v5_2": "5.2.2",
                        "v4_13": "4.13.1"
                        },
                    "default_value": "v5_6"
                }
            }
        }"""

    def execute(self, data): #Application.getInstance().getPrintInformation().
        cura_version = self.getSettingValueByKey("cura_version")
        if cura_version == "v5_72":
            fdm_path = r"C:\Program Files\UltiMaker Cura 5.7.2\share\cura\resources\definitions\fdmprinter.def.json"
        if cura_version == "v5_71":
            fdm_path = r"C:\Program Files\UltiMaker Cura 5.7.1\share\cura\resources\definitions\fdmprinter.def.json"
        if cura_version == "v5_70":
            fdm_path = r"C:\Program Files\UltiMaker Cura 5.7.0\share\cura\resources\definitions\fdmprinter.def.json"
        if cura_version == "v5_6":
            fdm_path = r"C:\Program Files\UltiMaker Cura 5.6.0\share\cura\resources\definitions\fdmprinter.def.json"
        elif cura_version == "v5_5":
            fdm_path = r"C:\Program Files\UltiMaker Cura 5.5.0\share\cura\resources\definitions\fdmprinter.def.json"
        elif cura_version == "v5_4":
            fdm_path = r"C:\Program Files\UltiMaker Cura 5.4.0\share\cura\resources\definitions\fdmprinter.def.json"
        elif cura_version == "v5_2":
            fdm_path = r"C:\Program Files\UltiMaker Cura 5.2.2\share\cura\resources\definitions\fdmprinter.def.json"
        elif cura_version == "v4_13":
            fdm_path = r"C:\Program Files\Ultimaker Cura 4.13.1\resources\definitions\fdmprinter.def.json"
        elif cura_version == "v5_7b":
            fdm_path = r"C:\Program Files\UltiMaker Cura 5.7.0-beta.1\share\cura\resources\definitions\fdmprinter.def.json"
        machine_setting_list = []
        quality_setting_list =[]
        fdm_file = open(fdm_path, "r")
        whole_file = fdm_file.read()
        fdm_file.close()
        total_setting_list = []
        category_list = []
        data[0] = "Total Settings: XXX"
        whole_file = re.sub('"', "",whole_file)
        whole_file = re.sub('{', "",whole_file)
        whole_file = re.sub('},', "",whole_file)
        whole_file = re.sub('}', "",whole_file)
        whole_file = re.sub(',', "",whole_file)
        cleanUp = whole_file.split("\n")
        shit_list = ["description:", "default_value:", "value:", " enabled:", "children:", "options:"]
        for index, line in enumerate(cleanUp):
            for bad_word in shit_list:
                if bad_word in cleanUp[index]:
                    cleanUp[index] = ""
        whole_file = "\n".join(cleanUp)

        start_at = "    machine_settings:"
        end_at = "    resolution:"
        machine_setting_list = self._get_settings(whole_file, start_at, end_at)[0]
        label_list = self._get_settings(whole_file, start_at, end_at)[1]
        data[0] += "\n    [Machine]\n"
        for lnum in range(0, len(machine_setting_list),1):
            data[0] += machine_setting_list[lnum] + str("."*(50-len(machine_setting_list[lnum]))) + " ;" + label_list[lnum] + "\n"
        total_setting_list.append(str(len(machine_setting_list)))
        category_list.append("Machine:         ")

        start_at = "    resolution:"
        end_at = "    shell:"
        quality_setting_list = self._get_settings(whole_file, start_at, end_at)[0]
        label_list = self._get_settings(whole_file, start_at, end_at)[1]
        data[0] += "\n    [Quality]\n"
        for lnum in range(0, len(quality_setting_list),1):
            data[0] += quality_setting_list[lnum] + str("."*(50-len(quality_setting_list[lnum]))) + " ;" + label_list[lnum] + "\n"
        total_setting_list.append(str(len(quality_setting_list)))
        category_list.append("Quality:         ")

        start_at = "    shell:"
        end_at = "    top_bottom:"
        shell_setting_list = self._get_settings(whole_file, start_at, end_at)[0]
        label_list = self._get_settings(whole_file, start_at, end_at)[1]
        data[0] += "\n    [Shell]\n"
        for lnum in range(0, len(shell_setting_list),1):
            data[0] += shell_setting_list[lnum] + str("."*(50-len(shell_setting_list[lnum]))) + " ;" + label_list[lnum] + "\n"
        total_setting_list.append(str(len(shell_setting_list)))
        category_list.append("Shell:           ")

        start_at = "    top_bottom:"
        end_at = "    infill:"
        topbottom_setting_list = self._get_settings(whole_file, start_at, end_at)[0]
        label_list = self._get_settings(whole_file, start_at, end_at)[1]
        data[0] += "\n    [Top/Bottom]\n"
        for lnum in range(0, len(topbottom_setting_list),1):
            data[0] += topbottom_setting_list[lnum] + str("."*(50-len(topbottom_setting_list[lnum]))) + " ;" + label_list[lnum] + "\n"
        total_setting_list.append(str(len(topbottom_setting_list)))
        category_list.append("Top/Bottom:      ")

        start_at = "    infill:"
        end_at = "    material:"
        infill_setting_list = self._get_settings(whole_file, start_at, end_at)[0]
        label_list = self._get_settings(whole_file, start_at, end_at)[1]
        data[0] += "\n    [Infill]\n"
        for lnum in range(0, len(infill_setting_list),1):
            data[0] += infill_setting_list[lnum] + str("."*(50-len(infill_setting_list[lnum]))) + " ;" + label_list[lnum] + "\n"
        total_setting_list.append(str(len(infill_setting_list)))
        category_list.append("Infill:          ")

        start_at = "    material:"
        end_at = "    speed:"
        material_setting_list = self._get_settings(whole_file, start_at, end_at)[0]
        label_list = self._get_settings(whole_file, start_at, end_at)[1]
        data[0] += "\n    [Material]\n"
        for lnum in range(0, len(material_setting_list),1):
            data[0] += material_setting_list[lnum] + str("."*(50-len(material_setting_list[lnum]))) + " ;" + label_list[lnum] + "\n"
        total_setting_list.append(str(len(material_setting_list)))
        category_list.append("Material:        ")

        start_at = "    speed:"
        end_at = "    travel:"
        speed_setting_list = self._get_settings(whole_file, start_at, end_at)[0]
        label_list = self._get_settings(whole_file, start_at, end_at)[1]
        data[0] += "\n    [Speed]\n"
        for lnum in range(0, len(speed_setting_list),1):
            data[0] += speed_setting_list[lnum] + str("."*(50-len(speed_setting_list[lnum]))) + " ;" + label_list[lnum] + "\n"
        total_setting_list.append(str(len(speed_setting_list)))
        category_list.append("Speed:           ")

        start_at = "    travel:"
        end_at = "    cooling:"
        travel_setting_list = self._get_settings(whole_file, start_at, end_at)[0]
        label_list = self._get_settings(whole_file, start_at, end_at)[1]
        data[0] += "\n    [Travel]\n"
        for lnum in range(0, len(travel_setting_list),1):
            data[0] += travel_setting_list[lnum] + str("."*(50-len(travel_setting_list[lnum]))) + " ;" + label_list[lnum] + "\n"
        total_setting_list.append(str(len(travel_setting_list)))
        category_list.append("Travel:          ")

        start_at = "    cooling:"
        end_at = "    support:"
        cooling_setting_list = self._get_settings(whole_file, start_at, end_at)[0]
        label_list = self._get_settings(whole_file, start_at, end_at)[1]
        data[0] += "\n    [Cooling]\n"
        for lnum in range(0, len(cooling_setting_list),1):
            data[0] += cooling_setting_list[lnum] + str("."*(50-len(cooling_setting_list[lnum]))) + " ;" + label_list[lnum] + "\n"
        total_setting_list.append(str(len(cooling_setting_list)))
        category_list.append("Cooling:         ")

        start_at = "    support:"
        end_at = "    platform_adhesion:"
        support_setting_list = self._get_settings(whole_file, start_at, end_at)[0]
        label_list = self._get_settings(whole_file, start_at, end_at)[1]
        data[0] += "\n    [Support]\n"
        for lnum in range(0, len(support_setting_list),1):
            data[0] += support_setting_list[lnum] + str("."*(50-len(support_setting_list[lnum]))) + " ;" + label_list[lnum] + "\n"
        total_setting_list.append(str(len(support_setting_list)))
        category_list.append("Support:         ")

        start_at = "    platform_adhesion:"
        end_at = "    meshfix:"
        bed_adhesion_setting_list = self._get_settings(whole_file, start_at, end_at)[0]
        label_list = self._get_settings(whole_file, start_at, end_at)[1]
        data[0] += "\n    [Build Plate Adhesion]\n"
        for lnum in range(0, len(bed_adhesion_setting_list),1):
            data[0] += bed_adhesion_setting_list[lnum] + str("."*(50-len(bed_adhesion_setting_list[lnum]))) + " ;" + label_list[lnum] + "\n"
        total_setting_list.append(str(len(bed_adhesion_setting_list)))
        category_list.append("Adhesion:        ")

        start_at = "    meshfix:"
        end_at = "    blackmagic:"
        meshfix_setting_list = self._get_settings(whole_file, start_at, end_at)[0]
        label_list = self._get_settings(whole_file, start_at, end_at)[1]
        data[0] += "\n    [Mesh Fixes]\n"
        for lnum in range(0, len(meshfix_setting_list),1):
            data[0] += meshfix_setting_list[lnum] + str("."*(50-len(meshfix_setting_list[lnum]))) + " ;" + label_list[lnum] + "\n"
        total_setting_list.append(str(len(meshfix_setting_list)))
        category_list.append("Mesh Fixes:      ")

        start_at = "    blackmagic:"
        end_at = "    experimental:"
        specialmode_setting_list = self._get_settings(whole_file, start_at, end_at)[0]
        label_list = self._get_settings(whole_file, start_at, end_at)[1]
        data[0] += "\n    [Special Modes]\n"
        for lnum in range(0, len(specialmode_setting_list),1):
            data[0] += specialmode_setting_list[lnum] + str("."*(50-len(specialmode_setting_list[lnum]))) + " ;" + label_list[lnum] + "\n"
        total_setting_list.append(str(len(specialmode_setting_list)))
        category_list.append("Special Modes:   ")

        start_at = "    experimental:"
        end_at = "    command_line_settings:"
        experimental_setting_list = self._get_settings(whole_file, start_at, end_at)[0]
        label_list = self._get_settings(whole_file, start_at, end_at)[1]
        data[0] += "\n    [Experimental]\n"
        for lnum in range(0, len(experimental_setting_list),1):
            data[0] += experimental_setting_list[lnum] + str("."*(50-len(experimental_setting_list[lnum]))) + " ;" +label_list[lnum] + "\n"
        total_setting_list.append(str(len(experimental_setting_list)))
        category_list.append("Experimental:    ")

        start_at = "    command_line_settings:"
        end_at = "    cura:"
        commandline_setting_list = self._get_settings(whole_file, start_at, end_at)[0]
        label_list = self._get_settings(whole_file, start_at, end_at)[1]
        data[0] += "\n    [Command Line]\n"
        for lnum in range(0, len(commandline_setting_list),1):
            data[0] += commandline_setting_list[lnum] + str("."*(50-len(commandline_setting_list[lnum]))) + " ;" +label_list[lnum] + "\n"
        total_setting_list.append(str(len(commandline_setting_list)))
        category_list.append("Command Line:     ")
        data[0] += "\n\n\n"

        for num in range(1, len(data), 1):
            data[num] = ""

        number_of_settings = 0
        setting_str = ""
        for num in range(0,len(total_setting_list),1):
            number_of_settings += int(total_setting_list[num])
            setting_str += category_list[num] + str(total_setting_list[num]) + "\n"
        setting_str = "Total Settings: " + str(number_of_settings) + "\n" + setting_str
        data[0] = re.sub("Total Settings: XXX", setting_str, data[0])
        data[0] = "Cura version: " + str(cura_version) + " settings\n" + data[0]
        #data[0] += "\n\n\n" + str(machine_setting_list) + "\n" + str(quality_setting_list) + "\n" + str(shell_setting_list) + "\n" + str(topbottom_setting_list) + "\n" + str(infill_setting_list) + "\n" + str(material_setting_list) + "\n" + str(speed_setting_list) + "\n" + str(travel_setting_list) + "\n" + str(cooling_setting_list) + "\n" + str(support_setting_list) + "\n" + str(bed_adhesion_setting_list) + "\n" + str(meshfix_setting_list) + "\n" + str(specialmode_setting_list) + "\n" + str(experimental_setting_list) + "\n" + str(commandline_setting_list) + "\n\n\n"
        
        cura_setting_list = []
        for setting in machine_setting_list:
            cura_setting_list.append(setting[1:])
        for setting in quality_setting_list:
            cura_setting_list.append(setting[1:])
        for setting in shell_setting_list:
            cura_setting_list.append(setting[1:])
        for setting in topbottom_setting_list:
            cura_setting_list.append(setting[1:])
        for setting in infill_setting_list:
            cura_setting_list.append(setting[1:])
        for setting in material_setting_list:
            cura_setting_list.append(setting[1:])
        for setting in speed_setting_list:
            cura_setting_list.append(setting[1:])
        for setting in travel_setting_list:
            cura_setting_list.append(setting[1:])
        for setting in cooling_setting_list:
            cura_setting_list.append(setting[1:])
        for setting in support_setting_list:
            cura_setting_list.append(setting[1:])
        for setting in bed_adhesion_setting_list:
            cura_setting_list.append(setting[1:])
        for setting in meshfix_setting_list:
            cura_setting_list.append(setting[1:])
        for setting in specialmode_setting_list:
            cura_setting_list.append(setting[1:])
        for setting in experimental_setting_list:
            cura_setting_list.append(setting[1:])
        for setting in commandline_setting_list:
            cura_setting_list.append(setting[1:])
        data[0] += "\n\n\ncura_keywords = " + str(cura_setting_list) + "\n\n\n"


        #data[0] = "  Total Settings: " + str(len(commandline_setting_list) + len(experimental_setting_list) + len(specialmode_setting_list) + len(meshfix_setting_list) + len(bed_adhesion_setting_list) + len(support_setting_list) + len(cooling_setting_list) + len(travel_setting_list) + len(speed_setting_list) + len(material_setting_list) + len(infill_setting_list) + len(topbottom_setting_list) + len(shell_setting_list) + len(quality_setting_list) + len(machine_setting_list)) + "\n\n" + data[0]
        return data

    def _get_settings(self, whole_file: str, start_at: str, end_at:str) -> str:
        setting_list = []
        label_list = []
        settings = whole_file.split(start_at)[1]
        commands = settings.split("\n")
        found_cmd = False
        for num in range(0,len(commands),1):
            if end_at in commands[num]:
                break
            if re.search("[\t]", commands[num]) is not None:
                commands[num] = re.sub("\t", "    ", commands[num])
            if commands[num].startswith("                ") and commands[num].endswith(":"):
                found_cmd = True
                setting_list.append("#" + commands[num][:-1].strip())
            if "label:" in commands[num] and found_cmd:
                label_list.append("#" + commands[num].split(":")[1].strip())
            if "settable_per_extruder" in commands[num] and found_cmd:
                if "true" in commands[num].split(":")[1]:
                    label_list[len(label_list)-1] += str("."*(36-len(label_list[len(label_list)-1]))) + "Settable Per:" + commands[num].split(":")[1]
            if "limit_to_extruder" in commands[num] and found_cmd:
                label_list[len(label_list)-1] += str("."*(36-len(label_list[len(label_list)-1]))) + "  Limit To:" + commands[num].split(":")[1]
                found_cmd = False
        return setting_list, label_list

        cura_keywords = ["time", "date", "day", "initial_extruder_nr", "material_id", "material_type", "material_name", "material_brand", "print_time", "filament_amount", "filament_weight", "filament_cost", "jobname", "machine_name", "machine_show_variants", "machine_start_gcode", "machine_end_gcode", "material_guid", "material_diameter", "material_bed_temp_wait", "material_print_temp_wait", "material_print_temp_prepend", "material_bed_temp_prepend", "machine_width", "machine_depth", "machine_height", "machine_shape", "machine_buildplate_type", "machine_heated_bed", "machine_heated_build_volume", "machine_always_write_active_tool", "machine_center_is_zero", "machine_extruder_count", "extruders_enabled_count", "machine_nozzle_tip_outer_diameter", "machine_nozzle_head_distance", "machine_nozzle_expansion_angle", "machine_heat_zone_length", "machine_nozzle_temp_enabled", "machine_nozzle_heat_up_speed", "machine_nozzle_cool_down_speed", "machine_min_cool_heat_time_window", "machine_gcode_flavor", "machine_firmware_retract", "machine_extruders_share_heater", "machine_extruders_share_nozzle", "machine_extruders_shared_nozzle_initial_retraction", "machine_disallowed_areas", "nozzle_disallowed_areas", "machine_head_with_fans_polygon", "gantry_height", "machine_nozzle_id", "machine_nozzle_size", "machine_use_extruder_offset_to_offset_coords", "extruder_prime_pos_z", "extruder_prime_pos_abs", "machine_max_feedrate_x", "machine_max_feedrate_y", "machine_max_feedrate_z", "machine_max_feedrate_e", "machine_max_acceleration_x", "machine_max_acceleration_y", "machine_max_acceleration_z", "machine_max_acceleration_e", "machine_acceleration", "machine_max_jerk_xy", "machine_max_jerk_z", "machine_max_jerk_e", "machine_steps_per_mm_x", "machine_steps_per_mm_y", "machine_steps_per_mm_z", "machine_steps_per_mm_e", "machine_endstop_positive_direction_x", "machine_endstop_positive_direction_y", "machine_endstop_positive_direction_z", "machine_minimum_feedrate", "machine_feeder_wheel_diameter", "machine_scale_fan_speed_zero_to_one", "layer_height", "layer_height_0", "line_width", "wall_line_width", "wall_line_width_0", "wall_line_width_x", "skin_line_width", "infill_line_width", "skirt_brim_line_width", "support_line_width", "support_interface_line_width", "support_roof_line_width", "support_bottom_line_width", "prime_tower_line_width", "initial_layer_line_width_factor", "wall_extruder_nr", "wall_0_extruder_nr", "wall_x_extruder_nr", "wall_thickness", "wall_line_count", "wall_transition_length", "wall_distribution_count", "wall_transition_angle", "wall_transition_filter_distance", "wall_transition_filter_deviation", "wall_0_wipe_dist", "wall_0_inset", "optimize_wall_printing_order", "inset_direction", "alternate_extra_perimeter", "min_wall_line_width", "min_even_wall_line_width", "min_odd_wall_line_width", "fill_outline_gaps", "min_feature_size", "min_bead_width", "xy_offset", "xy_offset_layer_0", "hole_xy_offset", "hole_xy_offset_max_diameter", "z_seam_type", "z_seam_position", "z_seam_x", "z_seam_y", "z_seam_corner", "z_seam_relative", "roofing_extruder_nr", "roofing_layer_count", "roofing_line_width", "roofing_pattern", "roofing_monotonic", "roofing_angles", "top_bottom_extruder_nr", "top_bottom_thickness", "top_thickness", "top_layers", "bottom_thickness", "bottom_layers", "initial_bottom_layers", "top_bottom_pattern", "top_bottom_pattern_0", "connect_skin_polygons", "skin_monotonic", "skin_angles", "small_skin_width", "small_skin_on_surface", "skin_no_small_gaps_heuristic", "skin_outline_count", "ironing_enabled", "ironing_only_highest_layer", "ironing_pattern", "ironing_monotonic", "ironing_line_spacing", "ironing_flow", "ironing_inset", "speed_ironing", "acceleration_ironing", "jerk_ironing", "skin_overlap", "skin_overlap_mm", "skin_preshrink", "top_skin_preshrink", "bottom_skin_preshrink", "expand_skins_expand_distance", "top_skin_expand_distance", "bottom_skin_expand_distance", "max_skin_angle_for_expansion", "min_skin_width_for_expansion", "infill_extruder_nr", "infill_sparse_density", "infill_line_distance", "infill_pattern", "zig_zaggify_infill", "connect_infill_polygons", "infill_angles", "infill_offset_x", "infill_offset_y", "infill_randomize_start_location", "infill_multiplier", "infill_wall_line_count", "sub_div_rad_add", "infill_overlap", "infill_overlap_mm", "infill_wipe_dist", "infill_sparse_thickness", "gradual_infill_steps", "gradual_infill_step_height", "infill_before_walls", "min_infill_area", "infill_support_enabled", "infill_support_angle", "skin_edge_support_thickness", "skin_edge_support_layers", "lightning_infill_support_angle", "lightning_infill_overhang_angle", "lightning_infill_prune_angle", "lightning_infill_straightening_angle", "default_material_print_temperature", "build_volume_temperature", "material_print_temperature", "material_print_temperature_layer_0", "material_initial_print_temperature", "material_final_print_temperature", "material_extrusion_cool_down_speed", "default_material_bed_temperature", "material_bed_temperature", "material_bed_temperature_layer_0", "material_adhesion_tendency", "material_surface_energy", "material_shrinkage_percentage", "material_shrinkage_percentage_xy", "material_shrinkage_percentage_z", "material_crystallinity", "material_anti_ooze_retracted_position", "material_anti_ooze_retraction_speed", "material_break_preparation_retracted_position", "material_break_preparation_speed", "material_break_preparation_temperature", "material_break_retracted_position", "material_break_speed", "material_break_temperature", "material_flush_purge_speed", "material_flush_purge_length", "material_end_of_filament_purge_speed", "material_end_of_filament_purge_length", "material_maximum_park_duration", "material_no_load_move_factor", "material_flow", "wall_material_flow", "wall_0_material_flow", "wall_x_material_flow", "wall_0_material_flow_roofing", "wall_x_material_flow_roofing", "skin_material_flow", "roofing_material_flow", "infill_material_flow", "skirt_brim_material_flow", "support_material_flow", "support_interface_material_flow", "support_roof_material_flow", "support_bottom_material_flow", "prime_tower_flow", "material_flow_layer_0", "wall_x_material_flow_layer_0", "wall_0_material_flow_layer_0", "skin_material_flow_layer_0", "material_standby_temperature", "material_is_support_material", "speed_print", "speed_infill", "speed_wall", "speed_wall_0", "speed_wall_x", "speed_wall_0_roofing", "speed_wall_x_roofing", "speed_roofing", "speed_topbottom", "speed_support", "speed_support_infill", "speed_support_interface", "speed_support_roof", "speed_support_bottom", "speed_prime_tower", "speed_travel", "speed_layer_0", "speed_print_layer_0", "speed_travel_layer_0", "skirt_brim_speed", "speed_z_hop", "speed_slowdown_layers", "speed_equalize_flow_width_factor", "acceleration_enabled", "acceleration_travel_enabled", "acceleration_print", "acceleration_infill", "acceleration_wall", "acceleration_wall_0", "acceleration_wall_x", "acceleration_wall_0_roofing", "acceleration_wall_x_roofing", "acceleration_roofing", "acceleration_topbottom", "acceleration_support", "acceleration_support_infill", "acceleration_support_interface", "acceleration_support_roof", "acceleration_support_bottom", "acceleration_prime_tower", "acceleration_travel", "acceleration_layer_0", "acceleration_print_layer_0", "acceleration_travel_layer_0", "acceleration_skirt_brim", "jerk_enabled", "jerk_travel_enabled", "jerk_print", "jerk_infill", "jerk_wall", "jerk_wall_0", "jerk_wall_x", "jerk_wall_0_roofing", "jerk_wall_x_roofing", "jerk_roofing", "jerk_topbottom", "jerk_support", "jerk_support_infill", "jerk_support_interface", "jerk_support_roof", "jerk_support_bottom", "jerk_prime_tower", "jerk_travel", "jerk_layer_0", "jerk_print_layer_0", "jerk_travel_layer_0", "jerk_skirt_brim", "retraction_enable", "retract_at_layer_change", "retraction_amount", "retraction_speed", "retraction_retract_speed", "retraction_prime_speed", "retraction_extra_prime_amount", "retraction_min_travel", "retraction_count_max", "retraction_extrusion_window", "retraction_combing", "retraction_combing_max_distance", "travel_retract_before_outer_wall", "travel_avoid_other_parts", "travel_avoid_supports", "travel_avoid_distance", "layer_start_x", "layer_start_y", "retraction_hop_enabled", "retraction_hop_only_when_collides", "retraction_hop", "retraction_hop_after_extruder_switch", "retraction_hop_after_extruder_switch_height", "cool_fan_enabled", "cool_fan_speed", "cool_fan_speed_min", "cool_fan_speed_max", "cool_min_layer_time_fan_speed_max", "cool_fan_speed_0", "cool_fan_full_at_height", "cool_fan_full_layer", "cool_min_layer_time", "cool_min_speed", "cool_lift_head", "cool_min_temperature", "support_enable", "support_extruder_nr", "support_infill_extruder_nr", "support_extruder_nr_layer_0", "support_interface_extruder_nr", "support_roof_extruder_nr", "support_bottom_extruder_nr", "support_structure", "support_tree_angle", "support_tree_branch_diameter", "support_tree_max_diameter", "support_tree_branch_diameter_angle", "support_type", "support_tree_angle_slow", "support_tree_max_diameter_increase_by_merges_when_support_to_model", "support_tree_min_height_to_model", "support_tree_bp_diameter", "support_tree_top_rate", "support_tree_tip_diameter", "support_tree_limit_branch_reach", "support_tree_branch_reach_limit", "support_tree_rest_preference", "support_angle", "support_pattern", "support_wall_count", "support_interface_wall_count", "support_roof_wall_count", "support_bottom_wall_count", "zig_zaggify_support", "support_connect_zigzags", "support_infill_rate", "support_line_distance", "support_initial_layer_line_distance", "support_infill_angles", "support_brim_enable", "support_brim_width", "support_brim_line_count", "support_z_distance", "support_top_distance", "support_bottom_distance", "support_xy_distance", "support_xy_overrides_z", "support_xy_distance_overhang", "support_bottom_stair_step_height", "support_bottom_stair_step_width", "support_bottom_stair_step_min_slope", "support_join_distance", "support_offset", "support_infill_sparse_thickness", "gradual_support_infill_steps", "gradual_support_infill_step_height", "minimum_support_area", "support_interface_enable", "support_roof_enable", "support_bottom_enable", "support_interface_height", "support_roof_height", "support_bottom_height", "support_interface_skip_height", "support_interface_density", "support_roof_density", "support_roof_line_distance", "support_bottom_density", "support_bottom_line_distance", "support_interface_pattern", "support_roof_pattern", "support_bottom_pattern", "minimum_interface_area", "minimum_roof_area", "minimum_bottom_area", "support_interface_offset", "support_roof_offset", "support_bottom_offset", "support_interface_priority", "support_interface_angles", "support_roof_angles", "support_bottom_angles", "support_fan_enable", "support_supported_skin_fan_speed", "support_use_towers", "support_tower_diameter", "support_tower_maximum_supported_diameter", "support_tower_roof_angle", "support_mesh_drop_down", "support_meshes_present", "prime_blob_enable", "extruder_prime_pos_x", "extruder_prime_pos_y", "adhesion_type", "adhesion_extruder_nr", "skirt_brim_extruder_nr", "raft_base_extruder_nr", "raft_interface_extruder_nr", "raft_surface_extruder_nr", "skirt_line_count", "skirt_height", "skirt_gap", "skirt_brim_minimal_length", "brim_width", "brim_line_count", "brim_gap", "brim_replaces_support", "brim_outside_only", "brim_inside_margin", "brim_smart_ordering", "raft_margin", "raft_smoothing", "raft_airgap", "layer_0_z_overlap", "raft_surface_layers", "raft_surface_thickness", "raft_surface_line_width", "raft_surface_line_spacing", "raft_interface_layers", "raft_interface_thickness", "raft_interface_line_width", "raft_interface_line_spacing", "raft_base_thickness", "raft_base_line_width", "raft_base_line_spacing", "raft_speed", "raft_surface_speed", "raft_interface_speed", "raft_base_speed", "raft_acceleration", "raft_surface_acceleration", "raft_interface_acceleration", "raft_base_acceleration", "raft_jerk", "raft_surface_jerk", "raft_interface_jerk", "raft_base_jerk", "raft_fan_speed", "raft_surface_fan_speed", "raft_interface_fan_speed", "raft_base_fan_speed", "prime_tower_enable", "prime_tower_size", "prime_tower_min_volume", "prime_tower_position_x", "prime_tower_position_y", "prime_tower_wipe_enabled", "prime_tower_brim_enable", "prime_tower_base_size", "prime_tower_base_height", "prime_tower_base_curve_magnitude", "prime_tower_raft_base_line_spacing", "ooze_shield_enabled", "ooze_shield_angle", "ooze_shield_dist", "switch_extruder_retraction_amount", "switch_extruder_retraction_speeds", "switch_extruder_retraction_speed", "switch_extruder_prime_speed", "switch_extruder_extra_prime_amount", "meshfix_union_all", "meshfix_union_all_remove_holes", "meshfix_extensive_stitching", "meshfix_keep_open_polygons", "multiple_mesh_overlap", "carve_multiple_volumes", "alternate_carve_order", "remove_empty_first_layers", "meshfix_maximum_resolution", "meshfix_maximum_travel_resolution", "meshfix_maximum_deviation", "meshfix_maximum_extrusion_area_deviation", "meshfix_fluid_motion_enabled", "meshfix_fluid_motion_shift_distance", "meshfix_fluid_motion_small_distance", "meshfix_fluid_motion_angle", "print_sequence", "infill_mesh", "infill_mesh_order", "cutting_mesh", "mold_enabled", "mold_width", "mold_roof_height", "mold_angle", "support_mesh", "anti_overhang_mesh", "magic_mesh_surface_mode", "magic_spiralize", "smooth_spiralized_contours", "relative_extrusion", "slicing_tolerance", "infill_enable_travel_optimization", "material_flow_temp_graph", "minimum_polygon_circumference", "interlocking_enable", "interlocking_beam_width", "interlocking_orientation", "interlocking_beam_layer_count", "interlocking_depth", "interlocking_boundary_avoidance", "support_skip_some_zags", "support_skip_zag_per_mm", "support_zag_skip_count", "draft_shield_enabled", "draft_shield_dist", "draft_shield_height_limitation", "draft_shield_height", "conical_overhang_enabled", "conical_overhang_angle", "conical_overhang_hole_size", "coasting_enable", "coasting_volume", "coasting_min_volume", "coasting_speed", "cross_infill_pocket_size", "cross_infill_density_image", "cross_support_density_image", "support_conical_enabled", "support_conical_angle", "support_conical_min_width", "magic_fuzzy_skin_enabled", "magic_fuzzy_skin_outside_only", "magic_fuzzy_skin_thickness", "magic_fuzzy_skin_point_density", "magic_fuzzy_skin_point_dist", "flow_rate_max_extrusion_offset", "flow_rate_extrusion_offset_factor", "adaptive_layer_height_enabled", "adaptive_layer_height_variation", "adaptive_layer_height_variation_step", "adaptive_layer_height_threshold", "wall_overhang_angle", "wall_overhang_speed_factor", "bridge_settings_enabled", "bridge_wall_min_length", "bridge_skin_support_threshold", "bridge_sparse_infill_max_density", "bridge_wall_coast", "bridge_wall_speed", "bridge_wall_material_flow", "bridge_skin_speed", "bridge_skin_material_flow", "bridge_skin_density", "bridge_fan_speed", "bridge_enable_more_layers", "bridge_skin_speed_2", "bridge_skin_material_flow_2", "bridge_skin_density_2", "bridge_fan_speed_2", "bridge_skin_speed_3", "bridge_skin_material_flow_3", "bridge_skin_density_3", "bridge_fan_speed_3", "clean_between_layers", "max_extrusion_before_wipe", "wipe_retraction_enable", "wipe_retraction_amount", "wipe_retraction_extra_prime_amount", "wipe_retraction_speed", "wipe_retraction_retract_speed", "wipe_retraction_prime_speed", "wipe_pause", "wipe_hop_enable", "wipe_hop_amount", "wipe_hop_speed", "wipe_brush_pos_x", "wipe_repeat_count", "wipe_move_distance", "small_hole_max_size", "small_feature_max_length", "small_feature_speed_factor", "small_feature_speed_factor_0", "material_alternate_walls", "raft_remove_inside_corners", "raft_base_wall_count", "group_outer_walls", "center_object", "mesh_position_x", "mesh_position_y", "mesh_position_z", "mesh_rotation_matrix", "extruder_nr", "extruder_prime_pos_z", "machine_extruder_cooling_fan_number", "machine_extruder_end_code", "machine_extruder_end_pos_abs", "machine_extruder_end_pos_x", "machine_extruder_end_pos_y", "machine_extruder_start_code", "machine_extruder_start_pos_abs", "machine_extruder_start_pos_x", "machine_extruder_start_pos_y", "machine_nozzle_id", "machine_nozzle_offset_x", "machine_nozzle_offset_y", "machine_nozzle_size", "material_diameter", "extruder_prime_pos_x", "extruder_prime_pos_y"]
        data[0] += "\n\n All Settings Length: " + str(len(all_settings)) + "\n\n;machine_setting_list: " + str(machine_setting_list) + "\n\n"

        return data
#currency_symbol=ApplicationgetInstancegetPreferencesgetValuecuracurrency#extruderMgr=ApplicationgetInstancegetExtruderManager#extruder=ApplicationgetInstancegetGlobalContainerStackextruderList#all_or_some=strselfgetSettingValueByKeyall_or_some#machine_extruder_count=intmycuragetPropertymachine_extruder_countvalue##ExtruderAssignments#wall_extruder_nr=intmycuragetPropertywall_extruder_nrvalue