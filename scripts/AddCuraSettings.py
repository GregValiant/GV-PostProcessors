# Copyright (c) 2024 GregValiant (Greg Foresi)
#   This post processor adds most of the Cura settings to the end of the Gcode file.  Which settings are added depends on things like the Extruder Count, Cura setup, etc.  For example if Generate Support is turned off then there won't be any support settings.
#   The "Full Set" contains all the settings.  The "Simple Set" has been filtered.

from UM.Application import Application
from cura.CuraApplication import CuraApplication
import UM.Util
from ..Script import Script
import time
import re
from UM.Qt.Duration import DurationFormat
import configparser
from UM.Preferences import Preferences
from UM.Message import Message

class AddCuraSettings(Script):
    """Add the Cura settings as a post-script to the g-code.
    """

    def getSettingDataString(self):
        return """{
            "name": "Add Cura Settings 5.9",
            "key": "AddCuraSettings",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "all_or_some":
                {
                    "label": "All or Some...",
                    "description": "Include all categories or you can pick which categories to include.  Selecting 'All' will add about 360 lines for a single extruder print and about 440 lines for a dual extruder print.",
                    "type": "enum",
                    "options": {
                        "all_settings": "All Categories",
                        "pick_settings": "Select Categories"},
                    "default_value": "all_settings"
                },
                "complete_or_short":
                {
                    "label": "Full Set or Simple set",
                    "description": "'Full Set' includes the Complete Cura Settings.  'Simple Set' includes the main settings only.",
                    "type": "enum",
                    "options": {
                        "complete_set": "Full Set",
                        "short_set": "Simple Set"},
                    "default_value": "short_set",
                    "enabled": true
                },
                "general_set":
                {
                    "label": "General",
                    "description": "The General settings.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "all_or_some == 'pick_settings'"
                },
                "machine_set":
                {
                    "label": "Machine",
                    "description": "The machine settings.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "all_or_some == 'pick_settings'"
                },
                "quality_set":
                {
                    "label": "Quality",
                    "description": "The Quality settings.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "all_or_some == 'pick_settings'"
                },
                "wall_set":
                {
                    "label": "Wall",
                    "description": "The Wall settings.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "all_or_some == 'pick_settings'"
                },
                "topbot_set":
                {
                    "label": "Top/Bottom",
                    "description": "The Top/Bottom settings.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "all_or_some == 'pick_settings'"
                },
                "infill_set":
                {
                    "label": "Infill",
                    "description": "The Infill settings.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "all_or_some == 'pick_settings'"
                },
                "material_set":
                {
                    "label": "Material",
                    "description": "The Material settings.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "all_or_some == 'pick_settings'"
                },
                "speed_set":
                {
                    "label": "Speed",
                    "description": "The Speed settings.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "all_or_some == 'pick_settings'"
                },
                "speed_set_max_min_calc":
                {
                    "label": "  Max/Min speeds in the gcode",
                    "description": "Goes through the gcode and determines the Max and Min Travel Speeds' and the 'Max and Min Print Speeds'.  This has been separated from the Speed settings because calculations can be time intensive for large prints and it adds Statistics rather than Settings.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": true
                },
                "travel_set":
                {
                    "label": "Travel",
                    "description": "The Travel settings.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "all_or_some == 'pick_settings'"
                },
                "cooling_set":
                {
                    "label": "Cooling",
                    "description": "The Cooling settings.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "all_or_some == 'pick_settings'"
                },
                "support_set":
                {
                    "label": "Support",
                    "description": "The Support settings.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "all_or_some == 'pick_settings'"
                },
                "adhesion_set":
                {
                    "label": "Build Plate Adhesion",
                    "description": "The Build Plate Adhesion settings.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "all_or_some == 'pick_settings'"
                },
                "dualext_set":
                {
                    "label": "Dual-Extruder",
                    "description": "The Multi-Extruder settings are only available for multi-extruder printers.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "all_or_some == 'pick_settings'"
                },
                "meshfix_set":
                {
                    "label": "Mesh Fixes",
                    "description": "The Mesh Fixes settings.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "all_or_some == 'pick_settings'"
                },
                "special_set":
                {
                    "label": "Special Modes",
                    "description": "The Special Mode settings.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "all_or_some == 'pick_settings'"
                },
                "experimental_set":
                {
                    "label": "Experimental",
                    "description": "The Experimental settings.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "all_or_some == 'pick_settings'"
                },
                "postprocess_set":
                {
                    "label": "PostProcessors",
                    "description": "Active Post Processor settings.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "all_or_some == 'pick_settings'"
                }
            }
        }"""

    def execute(self, data): # Application.getInstance().getPrintInformation().
        curaApp = Application.getInstance().getGlobalContainerStack()
        cura_version = CuraApplication.getInstance().getVersion()
        cura_version_int = cura_version.split("-")[0]
        cura_version_int = int(cura_version_int.replace(".", ""))
        currency_symbol = Application.getInstance().getPreferences().getValue("cura/currency")
        extruderMgr = Application.getInstance().getExtruderManager()
        extruder = Application.getInstance().getGlobalContainerStack().extruderList
        all_or_some = str(self.getSettingValueByKey("all_or_some"))
        complete_set = True if str(self.getSettingValueByKey("complete_or_short")) == "complete_set" else False
        machine_extruder_count = int(curaApp.getProperty("machine_extruder_count", "value"))
        setting_data = ";\n;  <<< Cura User Settings >>>\n"
        setting_data += ";    Cura Version: " + str(Application.getInstance().getVersion()) + "\n"
        setting_data += ";    Machine Name: " + str(curaApp.getProperty("machine_name", "value")) + "\n"
        # Extruder Assignments-------------------------------------------------------
        wall_extruder_nr = int(curaApp.getProperty("wall_extruder_nr", "value"))
        if wall_extruder_nr == -1: wall_extruder_nr = 0
        wall_0_extruder_nr = int(curaApp.getProperty("wall_0_extruder_nr", "value"))
        if wall_0_extruder_nr == -1: wall_0_extruder_nr = 0
        wall_x_extruder_nr = int(curaApp.getProperty("wall_x_extruder_nr", "value"))
        if wall_x_extruder_nr == -1: wall_x_extruder_nr = 0
        roofing_extruder_nr = int(curaApp.getProperty("roofing_extruder_nr", "value"))
        if roofing_extruder_nr == -1: roofing_extruder_nr = 0
        top_bottom_extruder_nr = int(curaApp.getProperty("top_bottom_extruder_nr", "value"))
        if top_bottom_extruder_nr == -1: top_bottom_extruder_nr = 0
        infill_extruder_nr = int(curaApp.getProperty("infill_extruder_nr", "value"))
        if infill_extruder_nr == -1: infill_extruder_nr = 0
        support_extruder_nr = int(curaApp.getProperty("support_extruder_nr", "value"))
        if support_extruder_nr == -1: support_extruder_nr = 0
        support_infill_extruder_nr = int(curaApp.getProperty("support_infill_extruder_nr", "value"))
        if support_infill_extruder_nr == -1: support_infill_extruder_nr = 0
        support_extruder_nr_layer_0 = int(curaApp.getProperty("support_extruder_nr_layer_0", "value"))
        if support_extruder_nr_layer_0 == -1: support_extruder_nr_layer_0 = 0
        support_interface_extruder_nr = int(curaApp.getProperty("support_interface_extruder_nr", "value"))
        if support_interface_extruder_nr == -1: support_interface_extruder_nr = 0
        support_roof_extruder_nr = int(curaApp.getProperty("support_roof_extruder_nr", "value"))
        if support_roof_extruder_nr == -1: support_roof_extruder_nr = 0
        support_bottom_extruder_nr = int(curaApp.getProperty("support_bottom_extruder_nr", "value"))
        if support_bottom_extruder_nr == -1: support_bottom_extruder_nr = 0
        #  For Compatibility with 4.x-------------------------------------------------------
        try:
            skirt_brim_extruder_nr = int(curaApp.getProperty("skirt_brim_extruder_nr", "value"))
            if skirt_brim_extruder_nr == -1: skirt_brim_extruder_nr = 0
        except:
            pass
        adhesion_extruder_nr = int(curaApp.getProperty("adhesion_extruder_nr", "value"))
        if adhesion_extruder_nr == -1: adhesion_extruder_nr = 0
        raft_base_extruder_nr = int(curaApp.getProperty("raft_base_extruder_nr", "value"))
        raft_interface_extruder_nr = int(curaApp.getProperty("raft_interface_extruder_nr", "value"))
        raft_surface_extruder_nr = int(curaApp.getProperty("raft_surface_extruder_nr", "value"))
        #General Settings-------------------------------------------------------
        if bool(self.getSettingValueByKey("general_set")) or all_or_some == "all_settings":
            setting_data += ";\n;  [General]\n"
            setting_data += str(cura_version) + "\n"
            setting_data += ";Job Name: " + str(Application.getInstance().getPrintInformation().jobName) + "\n"
            setting_data += ";Print Time: " + str(Application.getInstance().getPrintInformation().currentPrintTime.getDisplayString(DurationFormat.Format.ISO8601)) + "\n"
            setting_data += ";Slice Start Time: " + str(time.strftime("%H:%M:%S")) + " (24hr)\n"
            setting_data += ";Slice Date: " + str(time.strftime("%m-%d-%Y")) + " (mm-dd-yyyy)\n"
            setting_data += ";Slice Day: " + str(["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"][int(time.strftime("%w"))]) + "\n"
            filament_amt = Application.getInstance().getPrintInformation().materialLengths
            filament_wt = Application.getInstance().getPrintInformation().materialWeights
            filament_cost = Application.getInstance().getPrintInformation().materialCosts
            for num in range(0,machine_extruder_count):
                setting_data += ";Extruder " + str(num + 1) + " (T" + str(num) + "):\n"
                setting_data += ";  Filament Diameter: " + str(extruder[num].getProperty("material_diameter", "value")) + " mm\n"
                setting_data += ";  Filament Type: " + str(extruder[num].material.getMetaDataEntry("material", "")) + "\n"
                setting_data += ";  Filament Name: " + str(extruder[num].material.getMetaDataEntry("name", "")) + "\n"
                setting_data += ";  Filament Brand: " + str(extruder[num].material.getMetaDataEntry("brand", "")) + "\n"
                setting_data += ";  Filament Amount: " + str(round(filament_amt[num],2)) + "m\n"
                setting_data += ";  Filament Weight: " + str(round(filament_wt[num],2)) + "gm\n"
                setting_data += ";  Filament Cost: " + currency_symbol + "{:.2f}".format(filament_cost[num]) + "\n"
            setting_data += ";Keep Models Apart: " + str(Application.getInstance().getPreferences().getValue("physics/automatic_push_free")) + "\n"
            setting_data += ";Drop Models to Build Plate: " + str(Application.getInstance().getPreferences().getValue("physics/automatic_drop_down")) + "\n"

        #Machine Settings-------------------------------------------------------
        if bool(self.getSettingValueByKey("machine_set")) or all_or_some == "all_settings":
            setting_data += ";\n;  [Machine]\n"
            if complete_set: setting_data += ";Wait for bed heatup: " + str(curaApp.getProperty("material_bed_temp_wait", "value")) + "\n"
            if complete_set: setting_data += ";Wait for Nozzle Heatup: " + str(curaApp.getProperty("material_print_temp_wait", "value")) + "\n"
            if complete_set: setting_data += ";Add Print Temp Before StartUp: " + str(curaApp.getProperty("material_print_temp_prepend", "value")) + "\n"
            if complete_set: setting_data += ";Add Bed Temp Before StartUp: " + str(curaApp.getProperty("material_bed_temp_prepend", "value")) + "\n"
            setting_data += ";Machine Width: " + str(curaApp.getProperty("machine_width", "value")) + " mm\n"
            setting_data += ";Machine Depth: " +	str(curaApp.getProperty("machine_depth", "value")) + " mm\n"
            setting_data += ";Machine Height: " + str(curaApp.getProperty("machine_height", "value")) + " mm\n"
            setting_data += ";Platform: " + str(curaApp.getMetaDataEntry("platform", "value")) + "\n"
            if complete_set: setting_data += ";Machine Bed Shape: " + str(curaApp.getProperty("machine_shape", "value")) + "\n"
            if complete_set: setting_data += ";Machine Bed Heated: " + str(curaApp.getProperty("machine_heated_bed", "value")) + "\n"
            if complete_set: setting_data += ";Machine Heated Build Volume: " + str(curaApp.getProperty("machine_heated_build_volume", "value")) + "\n"
            if complete_set and bool(curaApp.getProperty("machine_heated_build_volume", "value")):
                setting_data += ";Machine Build Volume Fan#: " + str(curaApp.getProperty("build_volume_fan_nr", "value")) + "\n"
            if complete_set: setting_data += ";Machine Center is Zero: " + str(curaApp.getProperty("machine_center_is_zero", "value")) + "\n"
            if complete_set: setting_data += ";Machine Extruder Count: " + str(curaApp.getProperty("machine_extruder_count", "value")) + "\n"
            enabled_list = list([curaApp.isEnabled for curaApp in curaApp.extruderList])
            for num in range(0,len(enabled_list)):
                setting_data += ";  Extruder " + str(num + 1) + " (T" + str(num) + ") Enabled: " + str(enabled_list[num]) + "\n"
            if complete_set: setting_data += ";Enable Nozzle Temperature Control: " + str(curaApp.getProperty("machine_nozzle_temp_enabled", "value")) + "\n"
            if complete_set: setting_data += ";Heat Up Speed: " + str(curaApp.getProperty("machine_nozzle_heat_up_speed", "value")) + "°/sec\n"
            if complete_set: setting_data += ";Cool Down Speed: " + str(curaApp.getProperty("machine_nozzle_cool_down_speed", "value")) + "°/sec\n"
            if complete_set: setting_data += ";Minimal Time Standby Temperature: " + str(curaApp.getProperty("machine_min_cool_heat_time_window", "value")) + " sec\n"
            if complete_set: setting_data += ";G-code Flavor: " + str(curaApp.getProperty("machine_gcode_flavor", "value")) + "\n"
            if complete_set: setting_data += ";Firmware Retraction: " + str(curaApp.getProperty("machine_firmware_retract", "value")) + "\n"
            if machine_extruder_count > 1:
                setting_data += "; Extruders Share Heater: " + str(curaApp.getProperty("machine_extruders_share_heater", "value")) + "\n"
                setting_data += "; Extruders Share Nozzle: " + str(curaApp.getProperty("machine_extruders_share_nozzle", "value")) + "\n"
                setting_data += "; Shared Nozzle Initial Retraction: " + str(curaApp.getProperty("machine_extruders_shared_nozzle_initial_retraction", "value")) + " mm\n"
            if complete_set:
                mach_dis_areas = curaApp.getProperty("machine_disallowed_areas", "value")
                templist = ""
                for num in range(0,len(mach_dis_areas)-1):
                    templist += str(mach_dis_areas[num]) + ", "
                if templist == "": templist = "None"
                setting_data += ";Disallowed Areas: " + templist + "\n"
                nozzle_dis_areas = curaApp.getProperty("nozzle_disallowed_areas", "value")
                templist = ""
                for num in range(0,len(nozzle_dis_areas)-1):
                    templist += str(nozzle_dis_areas[num]) + ", "
                if templist == "": templist = "None"
                setting_data += ";Nozzle Disallowed Areas: " + templist + "\n"
            machine_head_with_fans_polygon = curaApp.getProperty("machine_head_with_fans_polygon", "value")
            if complete_set: setting_data += ";Print Head Disallowed Area (for One-At-A-Time): " + str(machine_head_with_fans_polygon[0]) + str(machine_head_with_fans_polygon[1]) + str(machine_head_with_fans_polygon[2]) + str(machine_head_with_fans_polygon[3]) + "\n"
            if complete_set: setting_data += ";Gantry Height: " + str(curaApp.getProperty("gantry_height", "value")) + " mm\n"
            if complete_set: setting_data += ";Nozzle Identifier: " + str(curaApp.getProperty("machine_nozzle_id", "value")) + "\n"
            setting_data += ";Extruder Nozzle Size:\n"
            for num in range(0,machine_extruder_count):
                setting_data += ";  Extruder " + str(num + 1) + " (T" + str(num) + "): " + str(extruder[num].getProperty("machine_nozzle_size", "value")) + " mm\n"
            if complete_set:
                setting_data += ";Use Extruder Offsets in Gcode: " + str(curaApp.getProperty("machine_use_extruder_offset_to_offset_coords", "value")) + "\n"
                setting_data += ";Z Position for Extruder Prime: " + str(curaApp.getProperty("extruder_prime_pos_z", "value")) + "\n"
                setting_data += ";Absolute Extruder Prime: " + str(curaApp.getProperty("extruder_prime_pos_abs", "value")) + "\n"
                setting_data += ";Max Feedrate X: " + str(curaApp.getProperty("machine_max_feedrate_x", "value")) + " mm/sec\n"
                setting_data += ";Max Feedrate Y: " + str(curaApp.getProperty("machine_max_feedrate_y", "value")) + " mm/sec\n"
                setting_data += ";Max Feedrate Z: " + str(curaApp.getProperty("machine_max_feedrate_z", "value")) + " mm/sec\n"
                setting_data += ";Max Feedrate E: " + str(curaApp.getProperty("machine_max_feedrate_e", "value")) + " mm/sec\n"
                setting_data += ";Max Accel X: " + str(curaApp.getProperty("machine_max_acceleration_x", "value")) + " mm/sec²\n"
                setting_data += ";Max Accel Y: " + str(curaApp.getProperty("machine_max_acceleration_y", "value")) + " mm/sec²\n"
                setting_data += ";Max Accel Z: " + str(curaApp.getProperty("machine_max_acceleration_z", "value")) + " mm/sec²\n"
                setting_data += ";Max Accel E: " + str(curaApp.getProperty("machine_max_acceleration_e", "value")) + " mm/sec²\n"
                setting_data += ";Default Machine Accel: " + str(curaApp.getProperty("machine_acceleration", "value")) + " mm/sec²\n"
                setting_data += ";Default XY Jerk: " + str(curaApp.getProperty("machine_max_jerk_xy", "value")) + " mm/sec\n"
                setting_data += ";Default Z Jerk: " + str(curaApp.getProperty("machine_max_jerk_z", "value")) + " mm/sec\n"
                setting_data += ";Default E Jerk: " + str(curaApp.getProperty("machine_max_jerk_e", "value")) + " mm/sec\n"
                setting_data += ";RepRap 0-1 Fan Scale: " + str(bool(extruder[0].getProperty("machine_scale_fan_speed_zero_to_one", "value"))) + "\n"
                try:
                    setting_data += ";Reset Flow Duration: " + str(round(extruder[0].getProperty("reset_flow_duration", "value"),2)) + "\n"
                except:
                    pass

        #Quality Settings-------------------------------------------------------
        if bool(self.getSettingValueByKey("quality_set")) or all_or_some == "all_settings":
            setting_data += ";\n;  [Quality]\n"
            setting_data += ";Layer Height: " + str(curaApp.getProperty("layer_height", "value")) + " mm\n"
            setting_data += ";Initial Layer Height: " + str(curaApp.getProperty("layer_height_0", "value")) + " mm\n"
            for num in range(0,machine_extruder_count):
                setting_data += ";Extruder " + str(num + 1) + " (T" + str(num) + "):\n"
                setting_data += ";  Line Width: " + str(extruder[num].getProperty("line_width", "value")) + " mm\n"
                setting_data += ";  Wall Line Width: " + str(extruder[wall_extruder_nr].getProperty("wall_line_width", "value")) + " mm\n"
                setting_data += ";  Outer-Wall Line Width: " + str(extruder[wall_0_extruder_nr].getProperty("wall_line_width_0", "value")) + " mm\n"
                setting_data += ";  Inner-Wall Line Width: " + str(extruder[wall_x_extruder_nr].getProperty("wall_line_width_x", "value")) + " mm\n"
                setting_data += ";  Skin Line Width: " + str(extruder[top_bottom_extruder_nr].getProperty("skin_line_width", "value")) + " mm\n"
                setting_data += ";  Infill Line Width: " + str(extruder[infill_extruder_nr].getProperty("infill_line_width", "value")) + " mm\n"
            try:
                setting_data += ";  Skirt/Brim Line Width: " + str(extruder[skirt_brim_extruder_nr].getProperty("skirt_brim_line_width", "value")) + " mm\n"
            except:
                pass
            setting_data += ";  Support Line Width: " + str(extruder[support_extruder_nr].getProperty("support_line_width", "value")) + " mm\n"
            setting_data += ";  Support Interface Line Width: " + str(extruder[support_interface_extruder_nr].getProperty("support_interface_line_width", "value")) + " mm\n"
            setting_data += ";  Support Roof Line Width: " + str(extruder[support_roof_extruder_nr].getProperty("support_roof_line_width", "value")) + " mm\n"
            setting_data += ";  Support Floor Line Width: " + str(extruder[support_bottom_extruder_nr].getProperty("support_bottom_line_width", "value")) + " mm\n"
            if bool(curaApp.getProperty("prime_tower_enable", "value")) and machine_extruder_count > 1:
                setting_data += ";Prime Tower Line Width: " + str(curaApp.getProperty("prime_tower_line_width", "value")) + " mm\n"
            setting_data += ";Initial Layer Line Width: " + str(curaApp.getProperty("initial_layer_line_width_factor", "value")) + " %\n"

        #Wall Settings-------------------------------------------------------
        if bool(self.getSettingValueByKey("wall_set")) or all_or_some == "all_settings":
            setting_data += ";\n;  [Walls]\n"
            if complete_set and machine_extruder_count > 1: setting_data += ";Wall Extruder: E" + str(wall_extruder_nr + 1) + " (T" + str(wall_extruder_nr) + ")\n"
            if complete_set and machine_extruder_count > 1: setting_data += ";Outer-Wall Extruder: E" + str(wall_0_extruder_nr + 1) + " (T" + str(wall_0_extruder_nr) + ")\n"
            if complete_set and machine_extruder_count > 1: setting_data += ";Inner-Wall Extruder: E" + str(wall_x_extruder_nr + 1) + " (T" + str(wall_x_extruder_nr) + ")\n"
            setting_data += ";Wall Thickness: " + str(round(extruder[wall_x_extruder_nr].getProperty("wall_thickness", "value"),2)) + " mm\n"
            setting_data += ";Wall Line Count: " + str(extruder[wall_x_extruder_nr].getProperty("wall_line_count", "value")) + "\n"
            if complete_set: setting_data += ";Wall Transition Length: " + str(curaApp.getProperty("wall_transition_length", "value")) + " mm\n"
            setting_data += ";Outer-Wall Wipe Dist: " + str(extruder[wall_0_extruder_nr].getProperty("wall_0_wipe_dist", "value")) + " mm\n"
            if complete_set: setting_data += ";Wall Distribution Count: " + str(curaApp.getProperty("wall_distribution_count", "value")) + "\n"
            if complete_set: setting_data += ";Wall Transitioning Threshold Angle: " + str(curaApp.getProperty("wall_transition_angle", "value")) + "°\n"
            if complete_set: setting_data += ";Wall Transitioning Filter Distance: " + str(curaApp.getProperty("wall_transition_filter_distance", "value")) + " mm\n"
            if complete_set: setting_data += ";Wall Transitioning Filter Margin: " + str(curaApp.getProperty("wall_transition_filter_deviation", "value")) + " mm\n"
            setting_data += ";Outer-Wall Inset: " + str(extruder[wall_0_extruder_nr].getProperty("wall_0_inset", "value")) + " mm\n"
            setting_data += ";Optimize Wall Printing Order: " + str(curaApp.getProperty("optimize_wall_printing_order", "value")) + "\n"
            setting_data += ";Wall Ordering: " + str(extruder[0].getProperty("inset_direction", "value")) + "\n"
            setting_data += ";Alternate Extra Wall: " + str(extruder[infill_extruder_nr].getProperty("alternate_extra_perimeter", "value")) + "\n"
            setting_data += ";Minimum Wall Line Width: " + str(curaApp.getProperty("min_wall_line_width", "value")) + " mm\n"
            if complete_set: setting_data += ";Minimum Even Wall Line Width: " + str(curaApp.getProperty("min_even_wall_line_width", "value")) + " mm\n"
            if complete_set: setting_data += ";Minimum Odd Wall Line Width: " + str(curaApp.getProperty("min_odd_wall_line_width", "value")) + " mm\n"
            setting_data += ";Print Thin Walls: " + str(curaApp.getProperty("fill_outline_gaps", "value")) + "\n"
            setting_data += ";Minimum Feature Size: " + str(extruder[wall_0_extruder_nr].getProperty("min_feature_size", "value")) + " mm\n"
            setting_data += ";Minimum Thin Wall Line: " + str(extruder[wall_0_extruder_nr].getProperty("min_bead_width", "value")) + " mm\n"
            setting_data += ";Horizontal Expansion: " + str(extruder[wall_0_extruder_nr].getProperty("xy_offset", "value")) + " mm\n"
            setting_data += ";Initial Layer Horiz Expansion: " + str(extruder[wall_0_extruder_nr].getProperty("xy_offset_layer_0", "value")) + " mm\n"
            setting_data += ";Hole Horizontal Expansion: " + str(extruder[wall_0_extruder_nr].getProperty("hole_xy_offset", "value")) + " mm\n"
            setting_data += ";Hole Horizontal Expansion Max Diameter: " + str(extruder[wall_0_extruder_nr].getProperty("hole_xy_offset_max_diameter", "value")) + " mm\n"
            setting_data += ";Z Seam Type: " + str(extruder[wall_0_extruder_nr].getProperty("z_seam_type", "value")) + "\n"
            setting_data += ";Z Seam On Vertex: " + str(extruder[wall_0_extruder_nr].getProperty("z_seam_on_vertex", "value")) + "\n"
            setting_data += ";Z Seam Position: " + str(extruder[wall_0_extruder_nr].getProperty("z_seam_position", "value")) + "\n"
            setting_data += ";Z Seam X: " + str(extruder[wall_0_extruder_nr].getProperty("z_seam_x", "value")) + "\n"
            setting_data += ";Z Seam Y: " + str(extruder[wall_0_extruder_nr].getProperty("z_seam_y", "value")) + "\n"
            setting_data += ";Z Seam Corner: " + str(extruder[wall_0_extruder_nr].getProperty("z_seam_corner", "value")) + "\n"
            setting_data += ";Z Seam Relative: " + str(extruder[wall_0_extruder_nr].getProperty("z_seam_relative", "value")) + "\n"

        #Top/Bottom Settings-------------------------------------------------------
        if bool(self.getSettingValueByKey("topbot_set")) or all_or_some == "all_settings":
            setting_data += ";\n;  [Top/Bottom]\n"
            if complete_set and machine_extruder_count > 1: setting_data += ";Top Surface Skin Extruder: " + str(roofing_extruder_nr + 1) + " (T" + str(roofing_extruder_nr) + ")\n"
            if complete_set and machine_extruder_count > 1: setting_data += ";Top/Bottom Extruder: " + str(top_bottom_extruder_nr + 1) + " (T" + str(top_bottom_extruder_nr) + ")\n"
            setting_data += ";Top Surface Skin Count: " + str(curaApp.getProperty("roofing_layer_count", "value")) + "\n"
            setting_data += ";Top Surface Skin Line Width: " + str(extruder[roofing_extruder_nr].getProperty("roofing_line_width", "value")) + " mm\n"
            setting_data += ";Top Surface Skin Pattern: " + str(curaApp.getProperty("roofing_pattern", "value")) + "\n"
            setting_data += ";Top Surface Monotonic: " + str(curaApp.getProperty("roofing_monotonic", "value")) + "\n"
            setting_data += ";Top Surface Skin Line Directions: " + str(extruder[roofing_extruder_nr].getProperty("roofing_angles", "value")) + "°\n"
            setting_data += ";Top/Bottom Thickness: " + str(round(curaApp.getProperty("top_bottom_thickness", "value"),2)) + " mm\n"
            setting_data += ";Top Thickness: " + str(round(curaApp.getProperty("top_thickness", "value"),2)) + " mm\n"
            setting_data += ";Top Layers: " + str(curaApp.getProperty("top_layers", "value")) + "\n"
            setting_data += ";Bottom Thickness: " + str(round(curaApp.getProperty("bottom_thickness", "value"),2)) + " mm\n"
            setting_data += ";Bottom Layers: " + str(curaApp.getProperty("bottom_layers", "value")) + "\n"
            setting_data += ";Initial Bottom Layers: " + str(curaApp.getProperty("initial_bottom_layers", "value")) + "\n"
            setting_data += ";Top/Bottom Pattern: " + str(extruder[top_bottom_extruder_nr].getProperty("top_bottom_pattern", "value")) + "\n"
            setting_data += ";Initial Top/Bottom Pattern: " + str(curaApp.getProperty("top_bottom_pattern_0", "value")) + "\n"
            if complete_set: setting_data += ";Connect Top/Bottom Polygons: " + str(extruder[top_bottom_extruder_nr].getProperty("connect_skin_polygons", "value")) + "\n"
            setting_data += ";Monotonic Top/Bottom: " + str(extruder[top_bottom_extruder_nr].getProperty("skin_monotonic", "value")) + "\n"
            setting_data += ";Top/Bottom Line Directions: " + str(extruder[top_bottom_extruder_nr].getProperty("skin_angles", "value")) + "°\n"
            if complete_set: setting_data += ";Small Top/Bottom Width: " + str(curaApp.getProperty("small_skin_width", "value")) + "\n"
            if complete_set: setting_data += ";Small Top/Bottom On Surface: " + str(curaApp.getProperty("small_skin_on_surface", "value")) + "\n"
            if complete_set: setting_data += ";No Skin in Z Gaps: " + str(extruder[top_bottom_extruder_nr].getProperty("skin_no_small_gaps_heuristic", "value")) + "\n"
            setting_data += ";Extra Skin Wall Count: " + str(curaApp.getProperty("skin_outline_count", "value")) + "\n"
            setting_data += ";Ironing Enabled: " + str(extruder[top_bottom_extruder_nr].getProperty("ironing_enabled", "value")) + "\n"
            if bool(extruder[top_bottom_extruder_nr].getProperty("ironing_enabled", "value")):
                setting_data += ";  Ironing Top Layer Only: " + str(extruder[0].getProperty("ironing_only_highest_layer", "value")) + "\n"
                setting_data += ";  Ironing Pattern: " + str(curaApp.getProperty("ironing_pattern", "value")) + "\n"
                setting_data += ";  Ironing Monotonic: " + str(extruder[top_bottom_extruder_nr].getProperty("ironing_monotonic", "value")) + "\n"
                if complete_set: setting_data += ";  Ironing Spacing: " + str(extruder[top_bottom_extruder_nr].getProperty("ironing_line_spacing", "value")) + " mm\n"
                setting_data += ";  Ironing Flow: " + str(extruder[top_bottom_extruder_nr].getProperty("ironing_flow", "value")) + " %\n"
                if complete_set: setting_data += ";  Ironing Inset: " + str(extruder[top_bottom_extruder_nr].getProperty("ironing_inset", "value")) + " %\n"
                setting_data += ";  Ironing Speed: " + str(round(extruder[top_bottom_extruder_nr].getProperty("speed_ironing", "value"),2)) + " mm/sec\n"
                if complete_set: setting_data += ";  Ironing Acceleration: " + str(round(extruder[top_bottom_extruder_nr].getProperty("acceleration_ironing", "value"),2)) + " mm/sec²\n"
                if complete_set: setting_data += ";  Ironing Jerk: " + str(round(extruder[top_bottom_extruder_nr].getProperty("jerk_ironing", "value"),2)) + " mm/sec\n"

            if complete_set: setting_data += ";Skin Overlap Percentage: " + str(extruder[top_bottom_extruder_nr].getProperty("skin_overlap", "value")) + "°\n"
            if complete_set: setting_data += ";Skin Overlap: " + str(extruder[top_bottom_extruder_nr].getProperty("skin_overlap_mm", "value")) + " mm\n"
            if complete_set: setting_data += ";Skin Removal Width: " + str(round(extruder[top_bottom_extruder_nr].getProperty("skin_preshrink", "value"), 2)) + " mm\n"
            setting_data += ";Top Skin Removal Width: " + str(round(extruder[top_bottom_extruder_nr].getProperty("top_skin_preshrink", "value"), 2)) + " mm\n"
            setting_data += ";Bottom Skin Removal Width: " + str(round(extruder[top_bottom_extruder_nr].getProperty("bottom_skin_preshrink", "value"), 2)) + " mm\n"
            if complete_set: setting_data += ";Skin Expand Distance: " + str(round(extruder[top_bottom_extruder_nr].getProperty("expand_skins_expand_distance", "value"),2)) + " mm\n"
            setting_data += ";Top Skin Expand Distance: " + str(round(extruder[top_bottom_extruder_nr].getProperty("top_skin_expand_distance", "value"),2)) + " mm\n"
            setting_data += ";Bottom Skin Expand Distance: " + str(round(extruder[top_bottom_extruder_nr].getProperty("bottom_skin_expand_distance", "value"),2)) + " mm\n"
            if complete_set: setting_data += ";Maximum Skin Angle for Expansion: " + str(extruder[top_bottom_extruder_nr].getProperty("max_skin_angle_for_expansion", "value")) + "°\n"
            if complete_set: setting_data += ";Minimum Skin Width for Expansion: " + str(round(extruder[top_bottom_extruder_nr].getProperty("min_skin_width_for_expansion", "value"), 2)) + " mm\n"

        #Infill Settings-------------------------------------------------------
        if bool(self.getSettingValueByKey("infill_set")) or all_or_some == "all_settings":
            setting_data += ";\n;  [Infill]\n"
            if complete_set and machine_extruder_count > 1: setting_data += ";Infill Extruder: " + str(infill_extruder_nr + 1) + " (T" + str(infill_extruder_nr) + ")\n"
            setting_data += ";Infill Density: " + str(extruder[infill_extruder_nr].getProperty("infill_sparse_density", "value")) + " %\n"
            setting_data += ";Infill Line Distance: " + str(extruder[infill_extruder_nr].getProperty("infill_line_distance", "value")) + " mm\n"
            setting_data += ";Connect Infill Lines: " + str(extruder[infill_extruder_nr].getProperty("zig_zaggify_infill", "value")) + "\n"
            setting_data += ";Connect Infill Polygons: " + str(extruder[infill_extruder_nr].getProperty("connect_infill_polygons", "value")) + "\n"
            setting_data += ";Infill Pattern: " + str(extruder[infill_extruder_nr].getProperty("infill_pattern", "value")) + "\n"
            if complete_set: setting_data += ";Cubic Subdivision Shell: " + str(extruder[infill_extruder_nr].getProperty("sub_div_rad_add", "value")) + "\n"
            if complete_set: setting_data += ";Infill Overlap Percentage: " + str(extruder[infill_extruder_nr].getProperty("infill_overlap", "value")) + "°\n"
            setting_data += ";Infill Overlap: " + str(extruder[infill_extruder_nr].getProperty("infill_overlap_mm", "value")) + " mm\n"
            setting_data += ";Infill Wipe Dist: " + str(extruder[infill_extruder_nr].getProperty("infill_wipe_dist", "value")) + " mm\n"
            setting_data += ";Infill Line Directions: " + str(extruder[infill_extruder_nr].getProperty("infill_angles", "value")) + "°\n"
            setting_data += ";Infill X Offset: " + str(extruder[infill_extruder_nr].getProperty("infill_offset_x", "value")) + " mm\n"
            setting_data += ";Infill Y Offset: " + str(extruder[infill_extruder_nr].getProperty("infill_offset_y", "value")) + " mm\n"
            setting_data += ";Randomize Infill Start: " + str(extruder[infill_extruder_nr].getProperty("infill_randomize_start_location", "value")) + "\n"
            setting_data += ";Infill Line Multiplier: " + str(extruder[infill_extruder_nr].getProperty("infill_multiplier", "value")) + "\n"
            setting_data += ";Infill Wall Line Count: " + str(extruder[infill_extruder_nr].getProperty("infill_wall_line_count", "value")) + "\n"
            setting_data += ";Infill Layer Thickness: " + str(extruder[infill_extruder_nr].getProperty("infill_sparse_thickness", "value")) + " mm\n"
            setting_data += ";Infill Steps: " + str(extruder[infill_extruder_nr].getProperty("gradual_infill_steps", "value")) + "\n"
            setting_data += ";Gradual Infill Step Height: " + str(extruder[infill_extruder_nr].getProperty("gradual_infill_step_height", "value")) + " mm\n"
            setting_data += ";Infill Before Walls: " + str(extruder[infill_extruder_nr].getProperty("infill_before_walls", "value")) + "\n"
            setting_data += ";Minimum Infill Area: " + str(extruder[infill_extruder_nr].getProperty("min_infill_area", "value")) + " mm²\n"
            if complete_set: setting_data += ";Skin Edge Support Thickness: " + str(extruder[infill_extruder_nr].getProperty("skin_edge_support_thickness", "value")) + " mm\n"
            if complete_set: setting_data += ";Skin Edge Support Layers: " + str(extruder[infill_extruder_nr].getProperty("skin_edge_support_layers", "value")) + "\n"
            if complete_set: setting_data += ";Extra Infill Lines To Support Skins: " + str(extruder[infill_extruder_nr].getProperty("extra_infill_lines_to_support_skins", "value")) + "\n"
            setting_data += ";Infill As Support: " + str(extruder[infill_extruder_nr].getProperty("infill_support_enabled", "value")) + "\n"
            if bool(extruder[infill_extruder_nr].getProperty("infill_support_enabled", "value")):
                setting_data += ";Infill Support Angle: " + str(extruder[infill_extruder_nr].getProperty("infill_support_angle", "value")) + "°\n"
            if str(extruder[infill_extruder_nr].getProperty("infill_pattern", "value")) == "lightning":
                setting_data += ";Infill Lightning Support Angle: " + str(extruder[infill_extruder_nr].getProperty("lightning_infill_support_angle", "value")) + "°\n"
                setting_data += ";Lightning Infill Overhang Angle: " + str(extruder[infill_extruder_nr].getProperty("lightning_infill_overhang_angle", "value")) + "°\n"
                setting_data += ";Lightning Infill Prune Angle: " + str(extruder[infill_extruder_nr].getProperty("lightning_infill_prune_angle", "value")) + "°\n"
                setting_data += ";Lightning Infill Straightening Angle: " + str(extruder[infill_extruder_nr].getProperty("lightning_infill_straightening_angle", "value")) + "°\n"

        #Material Settings-------------------------------------------------------
        if bool(self.getSettingValueByKey("material_set")) or all_or_some == "all_settings":
            setting_data += ";\n;  [Material]\n"
            if complete_set: setting_data += ";Heated Build Volume: " + str(curaApp.getProperty("machine_heated_build_volume", "value")) + "\n"
            if complete_set and bool(curaApp.getProperty("machine_heated_build_volume", "value")):
                setting_data += ";Build Volume Temp: " + str(curaApp.getProperty("build_volume_temperature", "value")) + "°\n"
            if complete_set: setting_data += ";Extrusion Cool Down Speed Modifier: " + str(curaApp.getProperty("material_extrusion_cool_down_speed", "value")) + " mm/sec\n"
            setting_data += ";Print Bed Temperature: " + str(curaApp.getProperty("material_bed_temperature", "value")) + "°\n"
            setting_data += ";Print Bed Temperature Initial Layer: " + str(curaApp.getProperty("material_bed_temperature_layer_0", "value")) + "°\n"
            for num in range(0,machine_extruder_count):
                setting_data += ";Extruder " + str(num + 1) + " (T" + str(num) + "):\n"
                setting_data += ";  Print Temperature: " + str(extruder[num].getProperty("material_print_temperature", "value")) + "°\n"
                setting_data += ";  Print Temperature Initial Layer: " + str(extruder[num].getProperty("material_print_temperature_layer_0", "value")) + "°\n"
                if complete_set: setting_data += ";  Print Initial Temp: " + str(extruder[num].getProperty("material_initial_print_temperature", "value")) + "°\n"
                if complete_set: setting_data += ";  Print Final Temp: " + str(extruder[num].getProperty("material_final_print_temperature", "value")) + "°\n"
                setting_data += ";  Material Flow: " + str(extruder[num].getProperty("material_flow", "value")) + " %\n"
                setting_data += ";  Wall Flow: " + str(extruder[num].getProperty("wall_material_flow", "value")) + " %\n"
                setting_data += ";  Outer-Wall Flow: " + str(extruder[num].getProperty("wall_0_material_flow", "value")) + " %\n"
                setting_data += ";  Inner-Wall Flow: " + str(extruder[num].getProperty("wall_x_material_flow", "value")) + " %\n"
                if complete_set: setting_data += ";  Top Surface Outer Wall Flow: " + str(extruder[num].getProperty("wall_0_material_flow_roofing", "value")) + " %\n"
                if complete_set: setting_data += ";  Top Surface Inner Wall(s) Flow: " + str(extruder[num].getProperty("wall_x_material_flow_roofing", "value")) + " %\n"
                setting_data += ";  Skin Flow: " + str(extruder[num].getProperty("skin_material_flow", "value")) + " %\n"
                if complete_set: setting_data += ";  Top Sufrace Skin Flow: " + str(extruder[num].getProperty("roofing_material_flow", "value")) + " %\n"
                if complete_set: setting_data += ";  Infill Flow: " + str(extruder[num].getProperty("infill_material_flow", "value")) + " %\n"
                if complete_set: setting_data += ";  Skirt/Brim Flow: " + str(extruder[num].getProperty("skirt_brim_material_flow", "value")) + " %\n"
                setting_data += ";  Support Flow: " + str(extruder[num].getProperty("support_material_flow", "value")) + " %\n"
                if complete_set: setting_data += ";  Support Interface Flow: " + str(extruder[num].getProperty("support_interface_material_flow", "value")) + " %\n"
                setting_data += ";  Support Roof Interface Flow: " + str(extruder[num].getProperty("support_roof_material_flow", "value")) + " %\n"
                setting_data += ";  Support Bottom Interface Flow: " + str(extruder[num].getProperty("support_bottom_material_flow", "value")) + " %\n"
                if bool(curaApp.getProperty("prime_tower_enable", "value")) and machine_extruder_count > 1:
                    setting_data += ";  Prime Tower Flow: " + str(extruder[num].getProperty("prime_tower_flow", "value")) + " %\n"
                setting_data += ";  Initial Layer Flow: " + str(extruder[num].getProperty("material_flow_layer_0", "value")) + " %\n"
                if complete_set: setting_data += ";  Initial Layer Inner-Wall Flow: " + str(extruder[num].getProperty("wall_x_material_flow_layer_0", "value")) + " %\n"
                if complete_set: setting_data += ";  Initial Layer Outer-Wall Flow: " + str(extruder[num].getProperty("wall_0_material_flow_layer_0", "value")) + " %\n"
                if complete_set: setting_data += ";  Initial Layer Skin Flow: " + str(extruder[num].getProperty("skin_material_flow_layer_0", "value")) + " %\n"
                if complete_set: setting_data += ";  Material Standby Temp: " + str(extruder[num].getProperty("material_standby_temperature", "value")) + "°\n"
                if complete_set: setting_data += ";  Material is Support Material: " + str(extruder[num].getProperty("material_is_support_material", "value")) + "\n"
                setting_data += ";  Gradual Flow Enabled: " + str(extruder[num].getProperty("gradual_flow_enabled", "value")) + "\n"
                if complete_set: setting_data += ";  Max Flow Acceleration: " + str(extruder[num].getProperty("max_flow_acceleration", "value")) + " mm/sec\n"
                if complete_set: setting_data += ";  Initial Layer Max Flow Acceleration: " + str(extruder[num].getProperty("layer_0_max_flow_acceleration", "value")) + " mm/sec\n"
                if complete_set: setting_data += ";  Gradual flow discretisation step size: " + str(extruder[num].getProperty("gradual_flow_discretisation_step_size", "value")) + " sec\n"

        #Speed Settings-------------------------------------------------------
        if bool(self.getSettingValueByKey("speed_set")) or all_or_some == "all_settings":
            setting_data += ";\n;  [Speed]\n"
            for num in range(0,machine_extruder_count):
                setting_data += ";Extruder " + str(num + 1) + " (T" + str(num) + "):\n"
                setting_data += ";  Speed Print: " + str(extruder[num].getProperty("speed_print", "value")) + " mm/sec\n"
                if complete_set: setting_data += ";  Speed Infill: " + str(extruder[num].getProperty("speed_infill", "value")) + " mm/sec\n"
                if complete_set: setting_data += ";  Speed Walls: " + str(extruder[num].getProperty("speed_wall", "value")) + " mm/sec\n"
                if complete_set: setting_data += ";  Speed Outer-Walls: " + str(extruder[num].getProperty("speed_wall_0", "value")) + " mm/sec\n"
                if complete_set: setting_data += ";  Speed Inner-Walls: " + str(extruder[num].getProperty("speed_wall_x", "value")) + " mm/sec\n"
                if complete_set: setting_data += ";  Top Surface Outer Wall Speed: " + str(extruder[num].getProperty("speed_wall_0_roofing", "value")) + " mm/sec\n"
                if complete_set: setting_data += ";  Top Surface Inner Wall Speed: " + str(extruder[num].getProperty("speed_wall_x_roofing", "value")) + " mm/sec\n"
                if complete_set: setting_data += ";  Speed Top Skins: " + str(extruder[num].getProperty("speed_roofing", "value")) + " mm/sec\n"
                if complete_set: setting_data += ";  Speed Top/Bottom: " + str(extruder[num].getProperty("speed_topbottom", "value")) + " mm/sec\n"
                setting_data += ";  Speed Travel: " + str(extruder[num].getProperty("speed_travel", "value")) + " mm/sec\n"
                if complete_set: setting_data += ";  Speed Initial Layer: " + str(extruder[num].getProperty("speed_layer_0", "value")) + " mm/sec\n"
                setting_data += ";  Speed Print Initial Layer: " + str(extruder[num].getProperty("speed_print_layer_0", "value")) + " mm/sec\n"
                setting_data += ";  Speed Travel Initial Layer: " + str(extruder[num].getProperty("speed_travel_layer_0", "value")) + " mm/sec\n"
                if complete_set: setting_data += ";  Speed Z-Hop: " + str(extruder[num].getProperty("speed_z_hop", "value")) + " mm/sec\n"
                setting_data += ";  Flow Equalization Ratio: " + str(extruder[num].getProperty("speed_equalize_flow_width_factor", "value")) + " %\n"
                setting_data += ";  Acceleration Enabled: " + str(extruder[num].getProperty("acceleration_enabled", "value")) + "\n"
                setting_data += ";  Acceleration Print: " + str(extruder[num].getProperty("acceleration_print", "value")) + " mm/sec²\n"
                setting_data += ";  Acceleration Travel: " + str(extruder[num].getProperty("acceleration_travel", "value")) + " mm/sec²\n"
                if complete_set: setting_data += ";  Acceleration Infill: " + str(extruder[num].getProperty("acceleration_infill", "value")) + " mm/sec²\n"
                if complete_set: setting_data += ";  Acceleration Wall: " + str(extruder[num].getProperty("acceleration_wall", "value")) + " mm/sec²\n"
                if complete_set: setting_data += ";  Acceleration Outer Wall: " + str(extruder[num].getProperty("acceleration_wall_0", "value")) + " mm/sec²\n"
                if complete_set: setting_data += ";  Acceleration Inner Wall: " + str(extruder[num].getProperty("acceleration_wall_x", "value")) + " mm/sec²\n"
                if complete_set: setting_data += ";  Acceleration Top Surface Outer Wall: " + str(extruder[num].getProperty("acceleration_wall_0_roofing", "value")) + " mm/sec²\n"
                if complete_set: setting_data += ";  Acceleration Top Surface Inner Wall: " + str(extruder[num].getProperty("acceleration_wall_x_roofing", "value")) + " mm/sec²\n"
                if complete_set: setting_data += ";  Acceleration Top Surface Skin: " + str(extruder[num].getProperty("acceleration_roofing", "value")) + " mm/sec²\n"
                if complete_set: setting_data += ";  Acceleration Top/Bottom: " + str(extruder[num].getProperty("acceleration_topbottom", "value")) + " mm/sec²\n"
                if complete_set: setting_data += ";  Acceleration Support: " + str(extruder[num].getProperty("acceleration_support", "value")) + " mm/sec²\n"# true
                if complete_set: setting_data += ";  Acceleration Support Infill: " + str(extruder[num].getProperty("acceleration_support_infill", "value")) + " mm/sec²\n"# true
                if complete_set: setting_data += ";  Acceleration Support Interface: " + str(extruder[num].getProperty("acceleration_support_interface", "value")) + " mm/sec²\n"# true
                if complete_set: setting_data += ";  Acceleration Support Roof: " + str(extruder[num].getProperty("acceleration_support_roof", "value")) + " mm/sec²\n"# true
                if complete_set: setting_data += ";  Acceleration Support Floor: " + str(extruder[num].getProperty("acceleration_support_bottom", "value")) + " mm/sec²\n"# true
                if complete_set: setting_data += ";  Acceleration Prime Tower: " + str(curaApp.getProperty("acceleration_prime_tower", "value")) + " mm/sec²\n"
                setting_data += ";  Jerk Enabled: " + str(extruder[num].getProperty("jerk_enabled", "value")) + "\n"
                setting_data += ";  Jerk Print: " + str(extruder[num].getProperty("jerk_print", "value")) + " mm/sec\n"
                if complete_set: setting_data += ";  Jerk Infill: " + str(extruder[num].getProperty("jerk_infill", "value")) + " mm/sec\n"
                if complete_set: setting_data += ";  Jerk Walls: " + str(extruder[num].getProperty("jerk_wall", "value")) + " mm/sec\n"
                if complete_set: setting_data += ";  Jerk Wall Outer: " + str(extruder[num].getProperty("jerk_wall_0", "value")) + " mm/sec\n"
                if complete_set: setting_data += ";  Jerk Wall Inner: " + str(extruder[num].getProperty("jerk_wall_x", "value")) + " mm/sec\n"
                if complete_set: setting_data += ";  Jerk Wall Top Surface Wall: " + str(extruder[num].getProperty("jerk_roofing", "value")) + " mm/sec\n"
                if complete_set: setting_data += ";  Jerk Top Surface Wall Outer: " + str(extruder[num].getProperty("jerk_wall_0_roofing", "value")) + " mm/sec\n"
                if complete_set: setting_data += ";  Jerk Top Surface Wall Inner: " + str(extruder[num].getProperty("jerk_wall_x_roofing", "value")) + " mm/sec\n"
                if complete_set: setting_data += ";  Jerk Top/Bottom: " + str(extruder[num].getProperty("jerk_topbottom", "value")) + " mm/sec\n"
                if complete_set: setting_data += ";  Jerk Support: " + str(extruder[support_extruder_nr].getProperty("jerk_support", "value")) + " mm/sec\n"
                if complete_set: setting_data += ";  Jerk Support Infill: " + str(extruder[support_extruder_nr].getProperty("jerk_support_infill", "value")) + " mm/sec\n"
                if complete_set: setting_data += ";  Jerk Support Interface: " + str(extruder[support_interface_extruder_nr].getProperty("jerk_support_interface", "value")) + " mm/sec\n"
                if complete_set: setting_data += ";  Jerk Support Roof: " + str(extruder[support_interface_extruder_nr].getProperty("jerk_support_roof", "value")) + " mm/sec\n"
                if complete_set: setting_data += ";  Jerk Support Floor: " + str(extruder[support_interface_extruder_nr].getProperty("jerk_support_bottom", "value")) + " mm/sec\n"
                if complete_set: setting_data += ";  Jerk Prime Tower: " + str(extruder[num].getProperty("jerk_prime_tower", "value")) + " mm/sec\n"
                setting_data += ";  Jerk Travel: " + str(extruder[num].getProperty("jerk_travel", "value")) + " mm/sec\n"
                if complete_set: setting_data += ";  Jerk Initial Layer: " + str(extruder[num].getProperty("jerk_layer_0", "value")) + " mm/sec\n"
                setting_data += ";  Jerk Print Initial Layer: " + str(extruder[num].getProperty("jerk_print_layer_0", "value")) + " mm/sec\n"
                setting_data += ";  Jerk Travel Initial Layer: " + str(extruder[num].getProperty("jerk_travel_layer_0", "value")) + " mm/sec\n"
                if complete_set: setting_data += ";  Jerk Skirt/Brim: " + str(extruder[num].getProperty("jerk_skirt_brim", "value")) + " mm/sec\n"
            setting_data += ";Speed Support: " + str(extruder[support_extruder_nr].getProperty("speed_support", "value")) + " mm/sec\n"
            setting_data += ";Speed Support Infill: " + str(extruder[support_infill_extruder_nr].getProperty("speed_support_infill", "value")) + " mm/sec\n"
            if complete_set: setting_data += ";Speed Support Interface: " + str(extruder[support_interface_extruder_nr].getProperty("speed_support_interface", "value")) + " mm/sec\n"
            setting_data += ";Speed Support Interface Roof: " + str(extruder[support_roof_extruder_nr].getProperty("speed_support_roof", "value")) + " mm/sec\n"
            setting_data += ";Speed Support Interface Bottom: " + str(extruder[support_bottom_extruder_nr].getProperty("speed_support_bottom", "value")) + " mm/sec\n"
            try: #  For compatibility with 4.x
                setting_data += ";Speed Skirt/Brim: " + str(extruder[skirt_brim_extruder_nr].getProperty("skirt_brim_speed", "value")) + " mm/sec\n"
            except:
                pass
            if bool(curaApp.getProperty("prime_tower_enable", "value")) and machine_extruder_count > 1:
                if complete_set: setting_data += ";Speed Prime Tower: " + str(curaApp.getProperty("speed_prime_tower", "value")) + " mm/sec\n"
            setting_data += ";Slower Initial Layers: " + str(curaApp.getProperty("speed_slowdown_layers", "value")) + "\n"
        if self.getSettingValueByKey("speed_set_max_min_calc"):
            #  Get the actual speeds from the gcode
            f_extrusion_speed_hi = 0.0
            f_extrusion_speed_lo = 100000.0
            f_travel_speed_hi = 0.0
            f_travel_speed_lo = 100000.0
            for num in range(2, len(data)-1):
                layer = data[num]
                lines = layer.split("\n")
                for line in lines:
                    #  If a line is a Z-hop or a retraction then ignore it.
                    if re.match("G1 F(\d*) Z", line) is not None or re.match("G1 F(\d*) E", line) is not None:
                        continue
                    if line.startswith("G"):
                        cmd = self.getValue(line, "G")
                        if cmd is not None:
                            #   Extrusion speeds
                            if cmd in [1, 2, 3]:
                                if " X" in line and " Y" in line and " E" in line and " F" in line:
                                    f_temp = int(self.getValue(line, "F"))
                                    if f_temp > int(f_extrusion_speed_hi):
                                        f_extrusion_speed_hi = int(f_temp)
                                    if f_temp < int(f_extrusion_speed_lo):
                                        f_extrusion_speed_lo = f_temp
                            #  Travel speeds
                            elif cmd == 0:
                                if " X" in line and " Y" in line and " F" in line and not " Z" in line:
                                    f_temp = int(self.getValue(line, "F"))
                                    if f_temp > int(f_travel_speed_hi):
                                        f_travel_speed_hi = f_temp
                                    if f_temp < int(f_travel_speed_lo):
                                        f_travel_speed_lo = f_temp
            setting_data += ";The speed ranges for this print >\n"
            setting_data += f";  Maximum Travel Speed: {round(f_travel_speed_hi / 60)} mm/sec\n;  Minimum Travel Speed: {round(f_travel_speed_lo / 60)} mm/sec\n"
            setting_data += f";  Maximum Extrusion Speed: {round(f_extrusion_speed_hi / 60, 1)} mm/sec\n;  Minimum Extrusion Speed: {round(f_extrusion_speed_lo / 60, 1)} mm/sec\n"
            msg_text = ";The speed ranges for this print >\n"
            msg_text += f";  Maximum Travel Speed: {round(f_travel_speed_hi / 60)} mm/sec\n;  Minimum Travel Speed: {round(f_travel_speed_lo / 60)} mm/sec\n"
            msg_text += f";  Maximum Extrusion Speed: {round(f_extrusion_speed_hi / 60, 1)} mm/sec\n;  Minimum Extrusion Speed: {round(f_extrusion_speed_lo / 60, 1)} mm/sec\n"
            Message(title = "[Add Cura Settings]", text = msg_text).show()
        else:
            setting_data += ";The speed ranges for this print >\n;  Calculation is not enabled\n"

        # Travel Settings-------------------------------------------------------
        if bool(self.getSettingValueByKey("travel_set")) or all_or_some == "all_settings":
            setting_data += ";\n;  [Travel]\n"
            for num in range(0,machine_extruder_count):
                setting_data += ";Extruder " + str(num + 1) + " (T" + str(num) + "):\n"
                setting_data += ";  Retraction Enabled: " + str(extruder[num].getProperty("retraction_enable", "value")) + "\n"
                setting_data += ";  Retraction at Layer Change: " + str(extruder[num].getProperty("retract_at_layer_change", "value")) + "\n"
                setting_data += ";  Retraction Distance: " + str(extruder[num].getProperty("retraction_amount", "value")) + " mm\n"
                if complete_set: setting_data += ";  Retraction Speed: " + str(extruder[num].getProperty("retraction_speed", "value")) + " mm/sec\n"
                setting_data += ";  Retraction Retract Speed: " + str(extruder[num].getProperty("retraction_retract_speed", "value")) + " mm/sec\n"
                setting_data += ";  Retraction Prime Speed: " + str(extruder[num].getProperty("retraction_prime_speed", "value")) + " mm/sec\n"
                setting_data += ";  Retraction Extra Prime Amount: " + str(extruder[num].getProperty("retraction_extra_prime_amount", "value")) + "mm³\n"
                setting_data += ";  Retraction Minimum Travel: " + str(extruder[num].getProperty("retraction_min_travel", "value")) + " mm\n"
                setting_data += ";  Retraction Maximum Count: " + str(extruder[num].getProperty("retraction_count_max", "value")) + "\n"
                setting_data += ";  Retraction Min Extr Dist Window: " + str(extruder[num].getProperty("retraction_extrusion_window", "value")) + "\n"
                setting_data += ";  Retraction Combing: " + str(extruder[num].getProperty("retraction_combing", "value")) + "\n"
                setting_data += ";  Retraction Max Combing with no Retract: " + str(extruder[num].getProperty("retraction_combing_max_distance", "value")) + " mm\n"
                setting_data += ";  Retract Before Outer Wall: " + str(extruder[num].getProperty("travel_retract_before_outer_wall", "value")) + "\n"
                setting_data += ";  Layer Start X: " + str(extruder[num].getProperty("layer_start_x", "value")) + "\n"
                setting_data += ";  Layer Start Y: " + str(extruder[num].getProperty("layer_start_y", "value")) + "\n"
                setting_data += ";  Travel Avoid Parts: " + str(extruder[num].getProperty("travel_avoid_other_parts", "value")) + "\n"
                setting_data += ";  Travel Avoid Supports: " + str(extruder[num].getProperty("travel_avoid_supports", "value")) + "\n"
                setting_data += ";  Travel Avoid Distance: " + str(extruder[num].getProperty("travel_avoid_distance", "value")) + " mm\n"
                setting_data += ";  Z-Hops Enabled: " + str(extruder[num].getProperty("retraction_hop_enabled", "value")) + "\n"
                if bool(extruder[num].getProperty("retraction_hop_enabled", "value")):
                    setting_data += ";  Z-Hop Only Over Printed Parts: " + str(extruder[num].getProperty("retraction_hop_only_when_collides", "value")) + "\n"
                    setting_data += ";  Z-Hop Height: " + str(extruder[num].getProperty("retraction_hop", "value")) + " mm\n"
                if machine_extruder_count > 1:
                    setting_data += ";  Z-Hop After Extruder Switch: " + str(extruder[num].getProperty("retraction_hop_after_extruder_switch", "value")) + "\n"
                    setting_data += ";  Z-Hop Height After Extruder Switch: " + str(extruder[num].getProperty("retraction_hop_after_extruder_switch_height", "value")) + " mm\n"

        # Cooling Settings-------------------------------------------------------
        if bool(self.getSettingValueByKey("cooling_set")) or all_or_some == "all_settings":
            setting_data += ";\n;  [Cooling]\n"
            for num in range(0,machine_extruder_count):
                setting_data += ";Extruder " + str(num + 1) + " (T" + str(num) + "):\n"
                setting_data += ";  Cooling Enabled: " + str(extruder[num].getProperty("cool_fan_enabled", "value")) + "\n"
                if bool(extruder[num].getProperty("cool_fan_enabled", "value")):
                    if complete_set: setting_data += ";  Cooling Fan Number: " + str((extruder[num].getProperty("machine_extruder_cooling_fan_number", "value"))) + "\n"
                    setting_data += ";  Cooling Fan Speed at Height: " + str(curaApp.getProperty("build_fan_full_at_height", "value")) + " mm\n"
                    setting_data += ";  Cooling Fan Speed at Layer: " + str(curaApp.getProperty("build_fan_full_layer", "value")) + " layer#\n"
                    setting_data += ";  Cooling Fan Speed: " + str(extruder[num].getProperty("cool_fan_speed", "value")) + " %\n"
                    setting_data += ";  Cooling Fan Minimum Speed: " + str(extruder[num].getProperty("cool_fan_speed_min", "value")) + " %\n"
                    setting_data += ";  Cooling Fan Maximum Speed: " + str(extruder[num].getProperty("cool_fan_speed_max", "value")) + " %\n"
                    setting_data += ";  Cooling Fan Min/Max Threshold: " + str(extruder[num].getProperty("cool_min_layer_time_fan_speed_max", "value")) + " %\n"
                    setting_data += ";  Cooling Fan Initial Speed: " + str(extruder[num].getProperty("cool_fan_speed_0", "value")) + " %\n"
                    setting_data += ";  Cooling Fan Regular Speed at Height: " + str(round(extruder[num].getProperty("cool_fan_full_at_height", "value"),2)) + " mm\n"
                    setting_data += ";  Cooling Fan Regular Speed at Layer: " + str(extruder[num].getProperty("cool_fan_full_layer", "value")) + "\n"
                    setting_data += ";  Cooling Minimum Layer Time: " + str(extruder[num].getProperty("cool_min_layer_time", "value")) + "sec\n"
                    setting_data += ";  Cooling Minimum Print Speed: " + str(extruder[num].getProperty("cool_min_speed", "value")) + " mm/sec\n"
                    setting_data += ";  Lift Head: " + str(extruder[num].getProperty("cool_lift_head", "value")) + "\n"
                    setting_data += ";  Small Layer Print Temperature: " + str(extruder[num].getProperty("cool_min_temperature", "value")) + "°\n"
                    if machine_extruder_count > 1:
                        setting_data += ";  Cooling during extruder switch: " + str(extruder[num].getProperty("cool_during_extruder_switch", "value")) + "\n"

        # Support Settings-------------------------------------------------------
        if bool(self.getSettingValueByKey("support_set")) or all_or_some == "all_settings":
            setting_data += ";\n;  [Support]\n"
            setting_data += ";Enable Support: " + str(curaApp.getProperty("support_enable", "value")) + "\n"
            if bool(curaApp.getProperty("support_enable", "value")):
                if machine_extruder_count > 1:
                    setting_data += ";Support Extruder: E" + str(support_extruder_nr + 1) + " (T" + str(support_extruder_nr) + ")\n"
                    setting_data += ";Support Infill Extruder: E" + str(support_infill_extruder_nr + 1) + " (T" + str(support_infill_extruder_nr) + ")\n"
                    setting_data += ";Support Initial Layer Extruder: E" + str(support_extruder_nr_layer_0 + 1) + " (T" + str(support_extruder_nr_layer_0) + ")\n"
                    setting_data += ";Support Interface Extruder: E" + str(support_interface_extruder_nr + 1) + " (T" + str(support_interface_extruder_nr) + ")\n"
                    setting_data += ";Support Interface Roof Extruder: E" + str(support_roof_extruder_nr + 1) + " (T" + str(support_roof_extruder_nr) + ")\n"
                    setting_data += ";Support Interface Bottom Extruder: E" + str(support_bottom_extruder_nr + 1) + " (T" + str(support_bottom_extruder_nr) + ")\n"
                    for num in range(0, machine_extruder_count):
                        setting_data += ";Extruder " + str(num + 1) + " (T" + str(num) + "):\n"
                        setting_data += "; Support Z Seam Away from Model: " + str(extruder[support_extruder_nr].getProperty("support_z_seam_away_from_model", "value")) + "\n"
                        setting_data += "; Min Z Seam Distance from Model: " + str(extruder[support_extruder_nr].getProperty("support_z_seam_min_distance", "value")) + "\n"

                setting_data += ";Support Structure: " + str(extruder[support_extruder_nr].getProperty("support_structure", "value")) + "\n"
                setting_data += ";Support Type: " + str(extruder[support_extruder_nr].getProperty("support_type", "value")) + "\n"
                if complete_set and str(extruder[support_extruder_nr].getProperty("support_structure", "value")) == "tree":
                    setting_data += ";Maximum Branch Angle: " + str(extruder[support_infill_extruder_nr].getProperty("support_tree_angle", "value")) + "°\n"
                    setting_data += ";Branch Diameter: " + str(extruder[support_infill_extruder_nr].getProperty("support_tree_branch_diameter", "value")) + " mm\n"
                    setting_data += ";Trunk Diameter: " + str(extruder[support_infill_extruder_nr].getProperty("support_tree_max_diameter", "value")) + " mm\n"
                    setting_data += ";Branch Diameter Angle: " + str(extruder[support_infill_extruder_nr].getProperty("support_tree_branch_diameter_angle", "value")) + "°\n"
                    setting_data += ";Preferred Branch Angle: " + str(extruder[support_infill_extruder_nr].getProperty("support_tree_angle_slow", "value")) + "°\n"
                    setting_data += ";Diameter Increase To Model: " + str(extruder[support_infill_extruder_nr].getProperty("support_tree_max_diameter_increase_by_merges_when_support_to_model", "value")) + "\n"
                    setting_data += ";Minimum Height To Model: " + str(extruder[support_infill_extruder_nr].getProperty("support_tree_min_height_to_model", "value")) + "°\n"
                    setting_data += ";Initial Layer Diameter: " + str(extruder[support_infill_extruder_nr].getProperty("support_tree_bp_diameter", "value")) + " mm\n"
                    setting_data += ";Branch Density: " + str(extruder[support_infill_extruder_nr].getProperty("support_tree_top_rate", "value")) + " %\n"
                    setting_data += ";Tip Diameter: " + str(round(extruder[support_infill_extruder_nr].getProperty("support_tree_tip_diameter", "value"), 2)) + " mm\n"
                    setting_data += ";Limit Branch Reach: " + str(curaApp.getProperty("support_tree_limit_branch_reach", "value")) + " mm\n"
                    setting_data += ";Optimal Branch Range: " + str(curaApp.getProperty("support_tree_branch_reach_limit", "value")) + " mm\n"
                    setting_data += ";Rest Preference: " + str(curaApp.getProperty("support_tree_rest_preference", "value")) + " mm\n"
                setting_data += ";Support Overhang Angle: " + str(extruder[support_extruder_nr].getProperty("support_angle", "value")) + "°\n"
                setting_data += ";Support Pattern: " + str(extruder[support_infill_extruder_nr].getProperty("support_pattern", "value")) + "\n"
                setting_data += ";Support Wall Count: " + str(extruder[support_extruder_nr].getProperty("support_wall_count", "value")) + "\n"
                if complete_set: setting_data += ";Support Interface Wall Line Count: " + str(extruder[support_interface_extruder_nr].getProperty("support_interface_wall_count", "value")) + "\n"
                if complete_set: setting_data += ";Support Roof Wall Line Count: " + str(extruder[support_extruder_nr].getProperty("support_roof_wall_count", "value")) + "\n"
                if complete_set: setting_data += ";Support Bottom Wall Line Count: " + str(extruder[support_extruder_nr].getProperty("support_bottom_wall_count", "value")) + "\n"
                setting_data += ";Connect Support Lines: " + str(extruder[support_infill_extruder_nr].getProperty("zig_zaggify_support", "value")) + "\n"
                setting_data += ";Connect Support ZigZags: " + str(extruder[support_infill_extruder_nr].getProperty("support_connect_zigzags", "value")) + "\n"
                setting_data += ";Support Density: " + str(extruder[support_infill_extruder_nr].getProperty("support_infill_rate", "value")) + " %\n"
                setting_data += ";Support Infill Line Directions: " + str(extruder[support_infill_extruder_nr].getProperty("support_infill_angles", "value")) + "°\n"
                setting_data += ";Support Initial Line Distance: " + str(round(extruder[support_extruder_nr].getProperty("support_initial_layer_line_distance", "value"),2)) + " mm\n"
                setting_data += ";Support Initial Infill Density Multiplier: " + str(extruder[support_extruder_nr].getProperty("support_infill_density_multiplier_initial_layer", "value")) + "\n"
                setting_data += ";Support Brim Enabled: " + str(extruder[support_extruder_nr].getProperty("support_brim_enable", "value")) + "\n"
                setting_data += ";Support Brim Width: " + str(extruder[support_extruder_nr].getProperty("support_brim_width", "value")) + " mm\n"
                if complete_set: setting_data += ";Support Z Distance: " + str(extruder[support_extruder_nr].getProperty("support_z_distance", "value")) + " mm\n"
                setting_data += ";Support Top Distance: " + str(extruder[support_extruder_nr].getProperty("support_top_distance", "value")) + " mm\n"
                setting_data += ";Support Bottom Distance: " + str(extruder[support_extruder_nr].getProperty("support_bottom_distance", "value")) + " mm\n"
                setting_data += ";Support XY Distance: " + str(extruder[support_extruder_nr].getProperty("support_xy_distance", "value")) + " mm\n"
                setting_data += ";Support XY Overrides Z: " + str(extruder[support_extruder_nr].getProperty("support_xy_overrides_z", "value")) + "\n"
                setting_data += ";Support Horizontal Expansion: " + str(extruder[support_extruder_nr].getProperty("support_offset", "value")) + " mm\n"
                setting_data += ";Support Infill Layer Thickness: " + str(extruder[support_infill_extruder_nr].getProperty("support_infill_sparse_thickness", "value")) + " mm\n"
                setting_data += ";Support Minimum Support Area: " + str(extruder[support_extruder_nr].getProperty("minimum_support_area", "value")) + " mm²\n"
                setting_data += ";Support Fan Enabled: " + str(extruder[support_extruder_nr].getProperty("support_fan_enable", "value")) + "\n"
                setting_data += ";Enable Support Interface: " + str(extruder[support_interface_extruder_nr].getProperty("support_interface_enable", "value")) + "\n"
                if bool(extruder[support_interface_extruder_nr].getProperty("support_interface_enable", "value")):
                    setting_data += ";Support Interface Wall Count: " + str(extruder[support_interface_extruder_nr].getProperty("support_interface_wall_count", "value")) + "\n"
                    setting_data += ";Enable Support Roof: " + str(extruder[support_roof_extruder_nr].getProperty("support_roof_enable", "value")) + "\n"
                    setting_data += ";Enable Support Floor: " + str(extruder[support_bottom_extruder_nr].getProperty("support_bottom_enable", "value")) + "\n"
                    setting_data += ";Support Interface Height: " + str(extruder[support_interface_extruder_nr].getProperty("support_interface_height", "value")) + " mm\n"
                    setting_data += ";Support Roof Height: " + str(extruder[support_roof_extruder_nr].getProperty("support_roof_height", "value")) + " mm\n"
                    setting_data += ";Support Floor Height: " + str(extruder[support_bottom_extruder_nr].getProperty("support_bottom_height", "value")) + " mm\n"
                    setting_data += ";Support Interface Density: " + str(extruder[support_roof_extruder_nr].getProperty("support_interface_density", "value")) + " %\n"
                    setting_data += ";Support Interface Pattern: " + str(extruder[support_roof_extruder_nr].getProperty("support_interface_pattern", "value")) + "\n"
                    setting_data += ";Support Interface Min Area: " + str(extruder[support_roof_extruder_nr].getProperty("minimum_interface_area", "value")) + " mm²\n"
                    setting_data += ";Support Interface Horizontal Expansion: " + str(extruder[support_roof_extruder_nr].getProperty("support_interface_offset", "value")) + " mm\n"
                    if complete_set: setting_data += ";Support Interface Line Directions: " + str(extruder[support_interface_extruder_nr].getProperty("support_interface_angles", "value")) + "°\n"
                    if complete_set: setting_data += ";Support Roof Line Directions: " + str(extruder[support_interface_extruder_nr].getProperty("support_roof_angles", "value")) + "°\n"
                    if complete_set: setting_data += ";Support Floor Line Directions: " + str(extruder[support_interface_extruder_nr].getProperty("support_bottom_angles", "value")) + "°\n"
                setting_data += ";Fan Speed Override: " + str(curaApp.getProperty("support_fan_enable", "value")) + "\n"
                setting_data += ";Supported Skin Fan Speed: " + str(curaApp.getProperty("support_supported_skin_fan_speed", "value")) + "°\n"
                setting_data += ";Support Use Towers: " + str(curaApp.getProperty("support_use_towers", "value")) + "\n"
                if complete_set: setting_data += ";Support Tower Diameter: " + str(curaApp.getProperty("support_tower_diameter", "value")) + " mm\n"
                if complete_set: setting_data += ";Maximum Tower-Supported Diameter: " + str(extruder[support_infill_extruder_nr].getProperty("support_tower_maximum_supported_diameter", "value")) + " mm\n"
                if complete_set: setting_data += ";Tower Roof Angle: " + str(extruder[support_infill_extruder_nr].getProperty("support_tower_roof_angle", "value")) + "°\n"
                if complete_set: setting_data += ";Dropdown Support Mesh: " + str(curaApp.getProperty("support_mesh_drop_down", "value")) + "\n"
                if complete_set: setting_data += ";Scene Has Support Meshes: " + str(curaApp.getProperty("support_meshes_present", "value")) + "\n"

        # Bed Adhesion Settings-------------------------------------------------------
        if bool(self.getSettingValueByKey("adhesion_set")) or all_or_some == "all_settings":
            setting_data += ";\n;  [Bed Adhesion]\n"
            if complete_set:
                try:
                    for num in range(0, machine_extruder_count):
                        setting_data += ";Extruder: E" + str(num + 1) + " (T" + str(num) + ")\n"
                        setting_data += ";  Prime Blob Enable: " + str(extruder[num].getProperty("prime_blob_enable", "value")) + "\n"
                        setting_data += ";  Extruder Prime X Position: " + str(extruder[num].getProperty("extruder_prime_pos_x", "value")) + "\n"
                        setting_data += ";  Extruder Prime Y Position: " + str(extruder[num].getProperty("extruder_prime_pos_y", "value")) + "\n"
                except:
                    pass
            setting_data += ";Adhesion Type: " + str(curaApp.getProperty("adhesion_type", "value")) + "\n"
            if str(curaApp.getProperty("adhesion_type", "value")) != "none":
                if machine_extruder_count > 1:
                    setting_data += ";Adhesion Extruder Number: E" + str(adhesion_extruder_nr + 1) + " (T" + str(adhesion_extruder_nr) + ")\n"
                    try:
                        setting_data += ";Adhesion Skirt/Brim Extruder: E" + str(skirt_brim_extruder_nr + 1) + " (T" + str(skirt_brim_extruder_nr) + ")\n"
                    except:
                        pass
                if str(curaApp.getProperty("adhesion_type", "value")) == "skirt":
                    setting_data += ";Adhesion Skirt Line Count: " + str(extruder[skirt_brim_extruder_nr].getProperty("skirt_line_count", "value")) + "\n"
                    setting_data += ";Adhesion Skirt Height: " + str(extruder[skirt_brim_extruder_nr].getProperty("skirt_height", "value")) + " layer(s)\n"
                    if complete_set: setting_data += ";Adhesion Skirt Gap: " + str(extruder[skirt_brim_extruder_nr].getProperty("skirt_gap", "value")) + " mm\n"
                    if complete_set: setting_data += ";Skirt/Brim Minimum Length: " + str(extruder[skirt_brim_extruder_nr].getProperty("skirt_brim_minimal_length", "value")) + " mm\n"
                elif str(curaApp.getProperty("adhesion_type", "value")) == "brim":
                    setting_data += ";Brim Width: " + str(extruder[skirt_brim_extruder_nr].getProperty("brim_width", "value")) + " mm\n"
                    setting_data += ";Brim Line Count: " + str(extruder[skirt_brim_extruder_nr].getProperty("brim_line_count", "value")) + "\n"
                    setting_data += ";Brim Gap: " + str(extruder[skirt_brim_extruder_nr].getProperty("brim_gap", "value")) + " mm\n"
                    setting_data += ";Brim Replaces Support: " + str(extruder[skirt_brim_extruder_nr].getProperty("brim_replaces_support", "value")) + "\n"
                    setting_data += ";Brim Location: " + str(extruder[skirt_brim_extruder_nr].getProperty("brim_location", "value")) + "\n"
                    setting_data += ";Brim Avoid Margin: " + str(extruder[skirt_brim_extruder_nr].getProperty("brim_inside_margin", "value")) + "\n"
                    setting_data += ";Smart Brim: " + str(extruder[skirt_brim_extruder_nr].getProperty("brim_smart_ordering", "value")) + "\n"
                elif str(curaApp.getProperty("adhesion_type", "value")) == "raft":
                    if machine_extruder_count > 1:
                        setting_data += ";Raft Base Extruder: " + str(raft_base_extruder_nr) + "\n"
                        setting_data += ";Raft Interface Extruder: " + str(raft_interface_extruder_nr) + "\n"
                        setting_data += ";Raft Surface Extruder: " + str(raft_surface_extruder_nr) + "\n"
                    if complete_set: setting_data += ";Raft Margin: " + str(extruder[skirt_brim_extruder_nr].getProperty("raft_margin", "value")) + " mm\n"
                    setting_data += ";Raft Air Gap: " + str(extruder[raft_surface_extruder_nr].getProperty("raft_airgap", "value")) + " mm\n"
                    if complete_set: setting_data += ";Raft Speed: " + str(extruder[adhesion_extruder_nr].getProperty("raft_speed", "value")) + " mm/sec\n"
                    if complete_set: setting_data += ";Raft Base Print Speed: " + str(extruder[raft_base_extruder_nr].getProperty("raft_interface_speed", "value")) + " mm/sec\n"
                    if complete_set: setting_data += ";Raft Middle Print Speed: " + str(extruder[raft_interface_extruder_nr].getProperty("raft_speed", "value")) + " mm/sec\n"
                    if complete_set: setting_data += ";Raft Top Print Speed: " + str(extruder[raft_surface_extruder_nr].getProperty("raft_surface_speed", "value")) + " mm/sec\n"
                    if complete_set: setting_data += ";Raft Middle Extra Margin: " + str(extruder[raft_interface_extruder_nr].getProperty("raft_base_margin", "value")) + " mm/sec\n"
                    if complete_set: setting_data += ";Raft Base Extra Margin: " + str(extruder[raft_base_extruder_nr].getProperty("raft_interface_margin", "value")) + " mm/sec\n"
                    if complete_set: setting_data += ";Raft Top Extra Margin: " + str(extruder[raft_surface_extruder_nr].getProperty("raft_surface_margin", "value")) + " mm/sec\n"
                    if complete_set: setting_data += ";Raft Remove Inside Corners: " + str(curaApp.getProperty("raft_remove_inside_corners", "value")) + " mm/sec\n"
                    if complete_set: setting_data += ";Raft Remove Base Inside Corners: " + str(curaApp.getProperty("raft_base_remove_inside_corners", "value")) + " mm/sec\n"
                    if complete_set: setting_data += ";Raft Remove Middle Inside Corners: " + str(curaApp.getProperty("raft_interface_remove_inside_corners", "value")) + " mm/sec\n"
                    if complete_set: setting_data += ";Raft Remove Top Inside Corners: " + str(curaApp.getProperty("raft_surface_remove_inside_corners", "value")) + " mm/sec\n"
                    if complete_set: setting_data += ";Raft Smoothing: " + str(curaApp.getProperty("raft_smoothing", "value")) + " mm\n"
                    if complete_set: setting_data += ";Raft Base Smoothing: " + str(curaApp.getProperty("raft_base_smoothing", "value")) + " mm\n"
                    if complete_set: setting_data += ";Raft Middle Smoothing: " + str(curaApp.getProperty("raft_interface_smoothing", "value")) + " mm\n"
                    if complete_set: setting_data += ";Raft Top Smoothing: " + str(curaApp.getProperty("raft_surface_smoothing", "value")) + " mm\n"
                    if complete_set: setting_data += ";Initial Layer Z Overlap: " + str(extruder[raft_surface_extruder_nr].getProperty("layer_0_z_overlap", "value")) + " mm\n"
                    if complete_set: setting_data += ";Raft Base Thickness: " + str(extruder[raft_base_extruder_nr].getProperty("raft_base_thickness", "value")) + " mm\n"
                    if complete_set: setting_data += ";Raft Base Line Width: " + str(extruder[raft_base_extruder_nr].getProperty("raft_base_line_width", "value")) + " mm\n"
                    if complete_set: setting_data += ";Raft Base Line Spacing: " + str(extruder[raft_base_extruder_nr].getProperty("raft_base_line_spacing", "value")) + " mm\n"
                    if complete_set: setting_data += ";Raft Middle Layers: " + str(extruder[raft_interface_extruder_nr].getProperty("raft_interface_layers", "value")) + "\n"
                    if complete_set: setting_data += ";Raft Middle Thickness: " + str(round(extruder[raft_interface_extruder_nr].getProperty("raft_interface_thickness", "value"), 2)) + " mm\n"
                    if complete_set: setting_data += ";Raft Middle Line Width: " + str(extruder[raft_interface_extruder_nr].getProperty("raft_interface_line_width", "value")) + " mm\n"
                    if complete_set: setting_data += ";Raft Middle Spacing: " + str(extruder[raft_interface_extruder_nr].getProperty("raft_interface_line_spacing", "value")) + " mm\n"
                    if complete_set: setting_data += ";Raft Top Layers: " + str(extruder[raft_surface_extruder_nr].getProperty("raft_surface_layers", "value")) + "\n"
                    if complete_set: setting_data += ";Raft Top Layer Thickness: " + str(extruder[raft_surface_extruder_nr].getProperty("raft_surface_thickness", "value")) + " mm\n"
                    if complete_set: setting_data += ";Raft Top Line Width: " + str(extruder[raft_surface_extruder_nr].getProperty("raft_surface_line_width", "value")) + " mm\n"
                    if complete_set: setting_data += ";Raft Top Spacing: " + str(extruder[raft_surface_extruder_nr].getProperty("raft_surface_line_spacing", "value")) + " mm\n"
                    if complete_set: setting_data += ";Raft Monotonic Top Surface Order: " + str(extruder[raft_surface_extruder_nr].getProperty("raft_surface_monotonic", "value")) + "\n"
                    if complete_set: setting_data += ";Raft Wall Count: " + str(curaApp.getProperty("raft_wall_count", "value")) + "\n"
                    if complete_set: setting_data += ";Raft Base Wall Count: " + str(curaApp.getProperty("raft_base_wall_count", "value")) + "\n"
                    if complete_set: setting_data += ";Raft Interface Wall Count: " + str(curaApp.getProperty("raft_interface_wall_count", "value")) + "\n"
                    if complete_set: setting_data += ";Raft Top Wall Count: " + str(curaApp.getProperty("raft_surface_wall_count", "value")) + "\n"
                    if complete_set: setting_data += ";Raft Print Acceleration: " + str(extruder[adhesion_extruder_nr].getProperty("raft_acceleration", "value")) + " mm/sec²\n"
                    if complete_set: setting_data += ";Raft Base Print Acceleration: " + str(extruder[raft_base_extruder_nr].getProperty("raft_base_acceleration", "value")) + " mm/sec²\n"
                    if complete_set: setting_data += ";Raft Middle Print Acceleration: " + str(extruder[raft_interface_extruder_nr].getProperty("raft_interface_acceleration", "value")) + " mm/sec²\n"
                    if complete_set: setting_data += ";Raft Top Print Acceleration: " + str(extruder[raft_surface_extruder_nr].getProperty("raft_surface_acceleration", "value")) + " mm/sec²\n"
                    if complete_set: setting_data += ";Raft Print Jerk: " + str(extruder[adhesion_extruder_nr].getProperty("raft_jerk", "value")) + " mm/sec\n"
                    if complete_set: setting_data += ";Raft Base Print Jerk: " + str(extruder[raft_base_extruder_nr].getProperty("raft_base_jerk", "value")) + " mm/sec\n"
                    if complete_set: setting_data += ";Raft Middle Print Jerk: " + str(extruder[raft_interface_extruder_nr].getProperty("raft_interface_jerk", "value")) + " mm/sec\n"
                    if complete_set: setting_data += ";Raft Top Print Jerk: " + str(extruder[raft_surface_extruder_nr].getProperty("raft_surface_jerk", "value")) + " mm/sec\n"
                    if complete_set: setting_data += ";Raft Fan Speed: " + str(extruder[adhesion_extruder_nr].getProperty("raft_fan_speed", "value")) + "%\n"
                    if complete_set: setting_data += ";Raft Base Fan Speed: " + str(extruder[raft_base_extruder_nr].getProperty("raft_base_fan_speed", "value")) + "%\n"
                    if complete_set: setting_data += ";Raft Middle Fan Speed: " + str(extruder[raft_interface_extruder_nr].getProperty("raft_interface_fan_speed", "value")) + "%\n"
                    if complete_set: setting_data += ";Raft Top Fan Speed: " + str(extruder[raft_surface_extruder_nr].getProperty("raft_surface_fan_speed", "value")) + "%\n"
                    if complete_set: setting_data += ";Raft Base Infill Overlap: " + str(extruder[raft_base_extruder_nr].getProperty("raft_base_infill_overlap", "value")) + "%\n"
                    if complete_set: setting_data += ";Raft Base Infill Overlap mm: " + str(extruder[raft_base_extruder_nr].getProperty("raft_base_infill_overlap_mm", "value")) + " mm\n"
                    if complete_set: setting_data += ";Raft Interface Z Offset: " + str(extruder[raft_interface_extruder_nr].getProperty("raft_interface_z_offset", "value")) + " mm\n"
                    if complete_set: setting_data += ";Raft Interface Infill Overlap: " + str(extruder[raft_interface_extruder_nr].getProperty("raft_interface_infill_overlap", "value")) + "%\n"
                    if complete_set: setting_data += ";Raft Interface Infill Overlap: " + str(extruder[raft_interface_extruder_nr].getProperty("raft_interface_infill_overlap_mm", "value")) + " mm\n"
                    if complete_set: setting_data += ";Raft Surface Z Offset: " + str(extruder[raft_surface_extruder_nr].getProperty("raft_surface_z_offset", "value")) + " mm\n"
                    if complete_set: setting_data += ";Raft Surface Infill Overlap: " + str(extruder[raft_interface_extruder_nr].getProperty("raft_surface_infill_overlap", "value")) + "%\n"
                    if complete_set: setting_data += ";Raft Surface Infoll Overlap: " + str(extruder[raft_interface_extruder_nr].getProperty("raft_surface_infill_overlap_mm", "value")) + " mm\n"
                    if complete_set: setting_data += ";Raft Flow: " + str(curaApp.getProperty("raft_flow", "value")) + "%\n"
                    if complete_set: setting_data += ";Raft Base Flow: " + str(extruder[raft_base_extruder_nr].getProperty("raft_base_flow", "value")) + "%\n"
                    if complete_set: setting_data += ";Raft Interface Flow: " + str(extruder[raft_interface_extruder_nr].getProperty("raft_interface_flow", "value")) + "%\n"

        # Dual Extrusion Settings-------------------------------------------------------
        if (bool(self.getSettingValueByKey("dualext_set")) or all_or_some == "all_settings") and machine_extruder_count > 1:
            setting_data += ";\n;  [Dual Extrusion]\n"
            setting_data += ";Initial Extruder Number: E" + str(extruderMgr.getInitialExtruderNr() + 1) + " (T" + str(extruderMgr.getInitialExtruderNr()) + ")\n"
            setting_data += ";Prime Tower Enable: " + str(curaApp.getProperty("prime_tower_enable", "value")) + "\n"
            if bool(curaApp.getProperty("prime_tower_enable", "value")):
                setting_data += ";  Prime Tower Type: " + str(curaApp.getProperty("prime_tower_mode", "value")) + "\n"
                setting_data += ";  Prime Tower Size: " + str(curaApp.getProperty("prime_tower_size", "value")) + "\n"
                for num in range(0, machine_extruder_count):
                    setting_data += ";  Prime Tower Min Volume: " + str(curaApp.getProperty("prime_tower_min_volume", "value")) + " mm³\n"
                    if complete_set: setting_data += ";  Prime Tower Max Bridging Distance: " + str(curaApp.getProperty("prime_tower_max_bridging_distance", "value")) + " mm\n"
                    if complete_set: setting_data += ";  Prime Tower Min Shell Thickness: " + str(curaApp.getProperty("prime_tower_min_shell_thickness", "value")) + " mm\n"
                setting_data += ";  Prime Tower X Pos: " + str(curaApp.getProperty("prime_tower_position_x", "value")) + "\n"
                setting_data += ";  Prime Tower Y Pos: " + str(curaApp.getProperty("prime_tower_position_y", "value")) + "\n"
                if complete_set: setting_data += ";  Prime Tower Wipe Enabled: " + str(curaApp.getProperty("prime_tower_wipe_enabled", "value")) + "\n"
                setting_data += ";  Prime Tower Brim: " + str(curaApp.getProperty("prime_tower_brim_enable", "value")) + "\n"
                setting_data += ";  Prime Tower Base Size: " + str(curaApp.getProperty("prime_tower_base_size", "value")) + " mm\n"
                if complete_set: setting_data += ";  Prime Tower Base Height: " + str(curaApp.getProperty("prime_tower_base_height", "value")) + " mm\n"
                if complete_set: setting_data += ";  Prime Tower Base Slope: " + str(extruder[raft_base_extruder_nr].getProperty("prime_tower_base_curve_magnitude", "value")) + "°\n"
                if complete_set: setting_data += ";  Prime Tower Raft Line Spacing: " + str(curaApp.getProperty("prime_tower_raft_base_line_spacing", "value")) + " mm\n"
            setting_data += ";Ooze Shield Enable: " + str(curaApp.getProperty("ooze_shield_enabled", "value")) + "\n"
            if bool(curaApp.getProperty("ooze_shield_enabled", "value")):
                if complete_set: setting_data += ";  Ooze Shield Angle: " + str(curaApp.getProperty("ooze_shield_angle", "value")) + "°\n"
                if complete_set: setting_data += ";  Ooze Shield Distance: " + str(curaApp.getProperty("ooze_shield_dist", "value")) + " mm\n"

            if machine_extruder_count > 1:
                for num in range(0, machine_extruder_count):
                    setting_data += ";Extruder: E" + str(num + 1) + " (T" + str(num) + ")\n"
                    setting_data += ";  Nozzle Switch Retraction Distance: " + str(extruder[num].getProperty("switch_extruder_retraction_amount", "value")) + " mm\n"
                    setting_data += ";  Nozzle Switch Retraction Speed: " + str(extruder[num].getProperty("switch_extruder_retraction_speeds", "value")) + " mm/sec\n"
                    if complete_set: setting_data += ";  Nozzle Switch Retract Speed: " + str(extruder[num].getProperty("switch_extruder_retraction_speed", "value")) + " mm/sec\n"
                    if complete_set: setting_data += ";  Nozzle Switch Prime Speed: " + str(extruder[num].getProperty("switch_extruder_prime_speed", "value")) + " mm/sec\n"
                    setting_data += ";  Extruder Switch Extra Prime: " + str(extruder[num].getProperty("switch_extruder_extra_prime_amount", "value")) + " mm³\n"

        # Mesh Fixes Settings-------------------------------------------------------
        if bool(self.getSettingValueByKey("meshfix_set")) or all_or_some == "all_settings":
            setting_data += ";\n;  [Mesh Fixes]\n"
            setting_data += ";Union Overlapping Volumes: " + str(curaApp.getProperty("meshfix_union_all", "value")) + "\n"
            setting_data += ";Remove All Holes: " + str(curaApp.getProperty("meshfix_union_all_remove_holes", "value")) + "\n"
            if complete_set: setting_data += ";Extensive Stitching: " + str(curaApp.getProperty("meshfix_extensive_stitching", "value")) + "\n"
            if complete_set: setting_data += ";Keep Disconnected Faces: " + str(curaApp.getProperty("meshfix_keep_open_polygons", "value")) + "\n"
            if complete_set: setting_data += ";Merged Mesh Overlap: " + str(curaApp.getProperty("multiple_mesh_overlap", "value")) + " mm\n"
            if complete_set: setting_data += ";Remove Mesh Intersection: " + str(curaApp.getProperty("carve_multiple_volumes", "value")) + "\n"
            if complete_set: setting_data += ";Alternate Mesh Removal: " + str(curaApp.getProperty("alternate_carve_order", "value")) + "\n"
            setting_data += ";Remove Empty First Layers: " + str(curaApp.getProperty("remove_empty_first_layers", "value")) + "\n"
            if complete_set: setting_data += ";Maximum Resolution: " + str(curaApp.getProperty("meshfix_maximum_resolution", "value")) + " mm\n"
            if complete_set: setting_data += ";Maximum Travel Resolution: " + str(curaApp.getProperty("meshfix_maximum_travel_resolution", "value")) + " mm\n"
            if complete_set: setting_data += ";Maximum Deviation: " + str(curaApp.getProperty("meshfix_maximum_deviation", "value")) + " mm\n"
            if complete_set: setting_data += ";Maximum Extrusion Area Deviation: " + str(curaApp.getProperty("meshfix_maximum_extrusion_area_deviation", "value")) + " µm²\n"
            setting_data += ";Fluid Motion Enable: " + str(curaApp.getProperty("meshfix_fluid_motion_enabled", "value")) + "\n"
            if complete_set: setting_data += ";Fluid Motion Shift Distance: " + str(curaApp.getProperty("meshfix_fluid_motion_shift_distance", "value")) + " mm\n"
            if complete_set: setting_data += ";Fluid Motion Small Distance: " + str(curaApp.getProperty("meshfix_fluid_motion_small_distance", "value")) + " mm\n"
            if complete_set: setting_data += ";Fluid Motion Angle: " + str(curaApp.getProperty("meshfix_fluid_motion_angle", "value")) + "°\n"

        # Special Modes-------------------------------------------------------
        if bool(self.getSettingValueByKey("special_set")) or all_or_some == "all_settings":
            setting_data += ";\n;  [Special Modes]\n"
            setting_data += ";Print Sequence: " + str(curaApp.getProperty("print_sequence", "value")) + "\n"
            setting_data += ";Mold Enabled: " + str(curaApp.getProperty("mold_enabled", "value")) + "\n"
            if bool(curaApp.getProperty("mold_enabled", "value")):
                setting_data += ";Mold Width: " + str(curaApp.getProperty("mold_width", "value")) + " mm\n"
                setting_data += ";Mold Roof Height: " + str(curaApp.getProperty("mold_roof_height", "value")) + " mm\n"
                setting_data += ";Mold Angle: " + str(curaApp.getProperty("mold_angle", "value")) + "°\n"
            setting_data += ";Surface Mode: " + str(curaApp.getProperty("magic_mesh_surface_mode", "value")) + "\n"
            setting_data += ";Spiralize: " + str(curaApp.getProperty("magic_spiralize", "value")) + "\n"
            if bool(curaApp.getProperty("magic_spiralize", "value")):
                setting_data += ";  Smooth Spiralized Contours : " + str(curaApp.getProperty("smooth_spiralized_contours", "value")) + "\n"
            setting_data += ";Relative Extrusion: " + str(curaApp.getProperty("relative_extrusion", "value")) + "\n"

        # Experimental-------------------------------------------------------
        if bool(self.getSettingValueByKey("experimental_set")) or all_or_some == "all_settings":
            setting_data += ";\n;  [Experimental]\n"
            setting_data += ";Slicing Tolerance: " + str(curaApp.getProperty("slicing_tolerance", "value")) + "\n"
            setting_data += ";Infill Travel Optimization: " + str(curaApp.getProperty("infill_enable_travel_optimization", "value")) + "\n"
            if machine_extruder_count > 1 and complete_set:
                for num in range(0, machine_extruder_count):
                    setting_data += ";Extruder E" + str(num + 1) + " (T" + str(num) + "):\n"
                    setting_data += ";  Flow Temperature Graph: " + str(extruder[num].getProperty("material_flow_temp_graph", "value")) + "\n"
            if complete_set: setting_data += ";Minimum Polygon Circumference: " + str(curaApp.getProperty("minimum_polygon_circumference", "value")) + "\n"
            setting_data += ";Generate Interlocking Structure: " + str(curaApp.getProperty("interlocking_enable", "value")) + "\n"
            if bool(curaApp.getProperty("interlocking_enable", "value")):
                if machine_extruder_count > 1:
                    for num in range(0, machine_extruder_count):
                        setting_data += ";Extruder " + str(num + 1) + " (T" + str(num) + "):\n"
                        setting_data += ";  Interlock Beam Width: " + str(extruder[num].getProperty("interlocking_beam_width", "value")) + " mm\n"
                else:
                    setting_data += ";  Interlock Beam Width: " + str(extruder[num].getProperty("interlocking_beam_width", "value")) + " mm\n"

                setting_data += ";  Interlock Orientation: " + str(curaApp.getProperty("interlocking_orientation", "value")) + "\n"
                setting_data += ";  Interlock Beam Layer Count: " + str(curaApp.getProperty("interlocking_beam_layer_count", "value")) + "\n"
                setting_data += ";  Interlock Depth: " + str(curaApp.getProperty("interlocking_depth", "value")) + " mm\n"
                setting_data += ";  Interlock Avoid: " + str(curaApp.getProperty("interlocking_boundary_avoidance", "value")) + "\n"
                setting_data += ";Break Up Support In Chunks: " + str(extruder[support_infill_extruder_nr].getProperty("support_skip_some_zags", "value")) + "\n"
                if complete_set: setting_data += ";Support Chunk Size: " + str(extruder[support_infill_extruder_nr].getProperty("support_skip_zag_per_mm", "value")) + "\n"
                if complete_set: setting_data += ";Support Chunk Line Count: " + str(extruder[support_infill_extruder_nr].getProperty("support_zag_skip_count", "value")) + "\n"
            setting_data += ";Draft Shield Enable: " + str(curaApp.getProperty("draft_shield_enabled", "value")) + "\n"
            if bool(curaApp.getProperty("draft_shield_enabled", "value")) and complete_set:
                setting_data += ";  Draft Shield Distance: " + str(curaApp.getProperty("draft_shield_dist", "value")) + " mm\n"
                setting_data += ";  Draft Shield Limitation: " + str(curaApp.getProperty("draft_shield_height_limitation", "value")) + " mm\n"
                setting_data += ";  Draft Shield Height: " + str(curaApp.getProperty("draft_shield_height", "value")) + " mm\n"
            setting_data += ";Make Overhang Printable: " + str(curaApp.getProperty("conical_overhang_enabled", "value")) + "\n"
            if bool(curaApp.getProperty("conical_overhang_enabled", "value")) and complete_set:
                setting_data += ";  Maximum Model Angle: " + str(curaApp.getProperty("conical_overhang_angle", "value")) + " mm\n"
                setting_data += ";  Maximum Overhang Hole Area: " + str(curaApp.getProperty("conical_overhang_hole_size", "value")) + " mm\n"
            setting_data += ";Coasting Enable: " + str(curaApp.getProperty("coasting_enable", "value")) + "\n"
            if bool(curaApp.getProperty("coasting_enable", "value")):
                if machine_extruder_count > 1 and complete_set:
                    for num in range(0, machine_extruder_count):
                        setting_data += ";Extruder " + str(num + 1) + " (T" + str(num) + "):\n"
                        setting_data += ";  Coasting Volume: " + str(extruder[num].getProperty("coasting_volume", "value")) + " mm³\n"
                        setting_data += ";  Minimum Volume Before Coasting: " + str(extruder[num].getProperty("coasting_min_volume", "value")) + " mm³\n"
                        setting_data += ";  Coasting Speed: " + str(extruder[num].getProperty("coasting_speed", "value")) + " mm/sec\n"
            if complete_set: setting_data += ";Cross 3D Pocket Size: " + str(extruder[infill_extruder_nr].getProperty("cross_infill_pocket_size", "value")) + " mm²\n"
            if complete_set: setting_data += ";Cross Infill Density Image: " + str(extruder[support_infill_extruder_nr].getProperty("cross_infill_density_image", "value")) + "\n"
            setting_data += ";Enable Conical Support: " + str(extruder[support_infill_extruder_nr].getProperty("support_conical_enabled", "value")) + "\n"
            if bool(curaApp.getProperty("support_conical_enabled", "value")) and complete_set:
                if machine_extruder_count > 1:
                    for num in range(0, machine_extruder_count):
                        setting_data += ";Extruder " + str(num + 1) + " (T" + str(num) + "):\n"
                        setting_data += ";  Conical Support Angle: " + str(extruder[support_infill_extruder_nr].getProperty("support_conical_angle", "value")) + "°\n"
                        setting_data += ";  Conical Support Minimum Width: " + str(extruder[support_infill_extruder_nr].getProperty("support_conical_min_width", "value")) + " mm\n"
            setting_data += ";Fuzzy Skin Enable: " + str(extruder[wall_0_extruder_nr].getProperty("magic_fuzzy_skin_enabled", "value")) + "\n"
            if bool(curaApp.getProperty("support_conical_enabled", "value")):
                setting_data += ";  Fuzzy Skin Outside Only: " + str(extruder[wall_0_extruder_nr].getProperty("magic_fuzzy_skin_outside_only", "value")) + "\n"
                setting_data += ";  Fuzzy Skin Thickness: " + str(extruder[wall_0_extruder_nr].getProperty("magic_fuzzy_skin_thickness", "value")) + " mm\n"
                if complete_set: setting_data += ";  Fuzzy Skin Density: " + str(extruder[wall_0_extruder_nr].getProperty("magic_fuzzy_skin_point_density", "value")) + " %\n"
                if complete_set: setting_data += ";  Fuzzy Skin Point Distance: " + str(extruder[wall_0_extruder_nr].getProperty("magic_fuzzy_skin_point_dist", "value")) + " %\n"
            setting_data += ";Flow Rate Compensation Max Extrusion Offset: " + str(curaApp.getProperty("flow_rate_max_extrusion_offset", "value")) + " mm\n"
            setting_data += ";Flow Rate Compensation Factor: " + str(curaApp.getProperty("flow_rate_extrusion_offset_factor", "value")) + " %\n"
            setting_data += ";Adaptive Layers: " + str(curaApp.getProperty("adaptive_layer_height_enabled", "value")) + "\n"
            if bool(curaApp.getProperty("adaptive_layer_height_enabled", "value")):
                setting_data += ";  Adaptive Height Variation: " + str(curaApp.getProperty("adaptive_layer_height_variation", "value")) + "\n"
                setting_data += ";  Adaptive Height Step: " + str(curaApp.getProperty("adaptive_layer_height_variation_step", "value")) + "\n"
                setting_data += ";  Adaptive Height Threshold: " + str(curaApp.getProperty("adaptive_layer_height_threshold", "value")) + "\n"
            if complete_set: setting_data += ";Overhanging Wall Angle: " + str(curaApp.getProperty("wall_overhang_angle", "value")) + "°\n"
            if complete_set: setting_data += ";Overhanging Seam Angle: " + str(curaApp.getProperty("seam_overhang_angle", "value")) + "°\n"
            if complete_set: setting_data += ";Overhanging Wall Speed: " + str(curaApp.getProperty("wall_overhang_speed_factor", "value")) + " %\n"
            setting_data += ";Bridge Settings Enabled: " + str(curaApp.getProperty("bridge_settings_enabled", "value")) + "\n"
            if bool(curaApp.getProperty("bridge_settings_enabled", "value")):
                if complete_set: setting_data += ";  Bridge Wall Min Length: " + str(curaApp.getProperty("bridge_wall_min_length", "value")) + "\n"
                if complete_set: setting_data += ";  Bridge Skin Supt Threshold: " + str(curaApp.getProperty("bridge_skin_support_threshold", "value")) + "\n"
                if complete_set: setting_data += ";  Bridge Sparse Infill Max Density: " + str(curaApp.getProperty("bridge_sparse_infill_max_density", "value")) + " %\n"
                if complete_set: setting_data += ";  Bridge Wall Coast: " + str(curaApp.getProperty("bridge_wall_coast", "value")) + "\n"
                if complete_set: setting_data += ";  Bridge Wall Speed: " + str(curaApp.getProperty("bridge_wall_speed", "value")) + " mm/sec\n"
                if complete_set: setting_data += ";  Bridge Wall Matl Flow: " + str(curaApp.getProperty("bridge_wall_material_flow", "value")) + " %\n"
                if complete_set: setting_data += ";  Bridge Skin Speed: " + str(curaApp.getProperty("bridge_skin_speed", "value")) + " mm/sec\n"
                if complete_set: setting_data += ";  Bridge Skin Matl Flow: " + str(curaApp.getProperty("bridge_skin_material_flow", "value")) + " %\n"
                if complete_set: setting_data += ";  Bridge Skin Density: " + str(curaApp.getProperty("bridge_skin_density", "value")) + " %\n"
                if complete_set: setting_data += ";  Bridge Fan Speed: " + str(curaApp.getProperty("bridge_fan_speed", "value")) + " %\n"
                if complete_set: setting_data += ";  Bridge Enable More Layers: " + str(curaApp.getProperty("bridge_enable_more_layers", "value")) + "\n"
                if bool(curaApp.getProperty("bridge_enable_more_layers", "value")):
                    if complete_set: setting_data += ";    Bridge Skin Speed 2: " + str(curaApp.getProperty("bridge_skin_speed_2", "value")) + " mm/sec\n"
                    if complete_set: setting_data += ";    Bridge Skin Matl Flow 2: " + str(curaApp.getProperty("bridge_skin_material_flow_2", "value")) + " %\n"
                    if complete_set: setting_data += ";    Bridge Skin Density 2: " + str(curaApp.getProperty("bridge_skin_density_2", "value")) + " %\n"
                    if complete_set: setting_data += ";    Bridge Fan Speed 2: " + str(curaApp.getProperty("bridge_fan_speed_2", "value")) + " %\n"
                    if complete_set: setting_data += ";      Bridge Skin Speed 3: " + str(curaApp.getProperty("bridge_skin_speed_3", "value")) + " mm/sec\n"
                    if complete_set: setting_data += ";      Bridge Skin Matl Flow 3: " + str(curaApp.getProperty("bridge_skin_material_flow_3", "value")) + " %\n"
                    if complete_set: setting_data += ";      Bridge Skin Density 3: " + str(curaApp.getProperty("bridge_skin_density_3", "value")) + " %\n"
                    if complete_set: setting_data += ";      Bridge Fan Speed 3: " + str(curaApp.getProperty("bridge_fan_speed_3", "value")) + " %\n"

            setting_data += ";Alternate Wall Directions: " + str(curaApp.getProperty("material_alternate_walls", "value")) + "\n"
            for num in range(0, machine_extruder_count):
                if bool(extruder[num].getProperty("clean_between_layers", "value")):
                    setting_data += ";Extruder " + str(num + 1) + " (T" + str(num) + ")\n"
                    setting_data += ";  Wipe Between Layers: " + str(extruder[num].getProperty("clean_between_layers", "value")) + "\n"
                    setting_data += ";  Material Volume Between Wipes: " + str(extruder[num].getProperty("max_extrusion_before_wipe", "value")) + "mm³\n"
                    setting_data += ";  Wipe Retraction Enable: " + str(curaApp.getProperty("wipe_retraction_enable", "value")) + "\n"
                    if complete_set: setting_data += ";  Wipe Retraction Distance: " + str(curaApp.getProperty("wipe_retraction_amount", "value")) + " mm\n"
                    if complete_set: setting_data += ";  Wipe Retraction Extra Prime Amount: " + str(curaApp.getProperty("wipe_retraction_extra_prime_amount", "value")) + "mm³\n"
                    if complete_set: setting_data += ";  Wipe Retraction Speed: " + str(curaApp.getProperty("wipe_retraction_speed", "value")) + " mm/sec\n"
                    if complete_set: setting_data += ";    Wipe Retraction Retract Speed: " + str(curaApp.getProperty("wipe_retraction_retract_speed", "value")) + " mm/sec\n"
                    if complete_set: setting_data += ";    Wipe Retraction Prime Speed: " + str(curaApp.getProperty("wipe_retraction_prime_speed", "value")) + " mm/sec\n"
                    setting_data += ";  Wipe Pause: " + str(curaApp.getProperty("wipe_pause", "value")) + "\n"
                    setting_data += ";  Wipe Z Hop: " + str(curaApp.getProperty("wipe_hop_enable", "value")) + "\n"
                    if bool(curaApp.getProperty("wipe_hop_enable", "value")):
                        if complete_set: setting_data += ";    Wipe Z Hop Height: " + str(curaApp.getProperty("wipe_hop_amount", "value")) + " mm\n"
                        if complete_set: setting_data += ";    Wipe Hop Speed: " + str(curaApp.getProperty("wipe_hop_speed", "value")) + " mm/sec\n"
                    if complete_set: setting_data += ";  Wipe Brush X Position: " + str(curaApp.getProperty("wipe_brush_pos_x", "value")) + "\n"
                    if complete_set: setting_data += ";  Wipe Repeat Count: " + str(curaApp.getProperty("wipe_repeat_count", "value")) + "\n"
                    if complete_set: setting_data += ";  Wipe Move Distance: " + str(curaApp.getProperty("wipe_move_distance", "value")) + " mm\n"
                else:
                    setting_data += ";Extruder " + str(num + 1) + " (T" + str(num) + "):\n"
                    setting_data += ";  Wipe Between Layers: " + str(extruder[num].getProperty("clean_between_layers", "value")) + "\n"
            try:
                setting_data += ";Small Hole Max Size: " + str(extruder[0].getProperty("small_hole_max_size", "value")) + " mm\n"
                if complete_set: setting_data += ";Small Feature Max Length: " + str(round(extruder[0].getProperty("small_feature_max_length", "value"), 2)) + " mm\n"
                if complete_set: setting_data += ";Small Feature Speed: " + str(extruder[0].getProperty("small_feature_speed_factor", "value")) + " mm/sec\n"
                if complete_set: setting_data += ";Small Feature Speed Initial Layer: " + str(extruder[0].getProperty("small_feature_speed_factor_0", "value")) + " mm/sec\n"
                setting_data += ";Group Outer Walls: " + str(curaApp.getProperty("group_outer_walls", "value")) + "\n"
                if cura_version_int > 581:
                    setting_data += ";Scarf Seam Length: " + str(extruder[wall_0_extruder_nr].getProperty("scarf_joint_seam_length", "value")) + " mm\n"
                    if extruder[wall_0_extruder_nr].getProperty("scarf_joint_seam_length", "value") != 0:
                        setting_data += ";  Scarf Seam Start Height: " + str(extruder[wall_0_extruder_nr].getProperty("scarf_joint_seam_start_height_ratio", "value")) + " %\n"
                        setting_data += ";  Scarf Seam Step Length: " + str(extruder[wall_0_extruder_nr].getProperty("scarf_split_distance", "value")) + " mm\n"
                    if complete_set:
                        for num in range(0, machine_extruder_count):
                            setting_data += ";Extruder " + str(num + 1) + " (T" + str(num) + "):\n"
                            setting_data += ";  Outer Wall Start Speed Ratio: " + str(extruder[num].getProperty("wall_0_start_speed_ratio", "value")) + " %\n"
                            setting_data += ";  Outer Wall Acceleration: " + str(extruder[num].getProperty("wall_0_acceleration", "value")) + " mm/sec\u00b2\n"
                            setting_data += ";  Outer Wall End Speed Ratio: " + str(extruder[num].getProperty("wall_0_end_speed_ratio", "value")) + " %\n"
                            setting_data += ";  Outer Wall Deceleration: " + str(extruder[num].getProperty("wall_0_deceleration", "value")) + " mm/sec\u00b2\n"
                            setting_data += ";  Outer Wall Speed Split Distance: " + str(extruder[num].getProperty("wall_0_speed_split_distance", "value")) + " mm\n"
            except:
                pass

        # PostProcessor Settings-------------------------------------------------------
        if bool(self.getSettingValueByKey("postprocess_set")) or all_or_some == "all_settings":
            setting_data += ";\n;  [Post-Processors]\n"
            scripts_list = curaApp.getMetaDataEntry("post_processing_scripts")
            for script_str in scripts_list.split("\n"):
                script_str = script_str.replace(r"\\\n", "\n;  ").replace("\n;  \n;  ", "\n")
                setting_data += ";" + str(script_str)

        # End of Settings-------------------------------------------------------------------------------
        setting_data += ";\n;  <<< End of Cura Settings >>>\n;\n"
        setting_data = self._format_string(setting_data)
        data[len(data)-1] += setting_data
        return data

    def _format_string(self, any_gcode_str: str):
        # Format the setting_data string.  No reason it shouldn't look nice.
        temp_lines = any_gcode_str.split("\n")
        gap_len = 0
        for temp_line in temp_lines:
            if ":" in temp_line:
                if gap_len - len(temp_line.split(":")[0]) + 1 < 0:
                    gap_len = len(temp_line.split(":")[0]) + 1
        if gap_len < 40: gap_len = 40
        for temp_index, temp_line in enumerate(temp_lines):
            if ":" in temp_line and not ";Extruder" in temp_line:
                temp_lines[temp_index] = temp_line.replace(temp_line.split(":")[0], temp_line.split(":")[0] + str("." * (gap_len - len(temp_line.split(":")[0]))),1)
        any_gcode_str = "\n".join(temp_lines)
        return any_gcode_str