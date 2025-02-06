# Copyright (c) May of 2024 GregValiant (Greg Foresi)
#   This post processor opens the relevant fddmprinter.def.json files and goes through the settings.  The print is thrown out and the setting name and 'settable_per_extruder" are pulled out and added to the gcode file.  Two versions can be compared and the differences are noted.

# Some of these may no longer be required.  I'm to lazy to figure out which.
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

class DiscoverSettings(Script):
    """ Remove all printing and then add all the Cura settings to the g-code.
    """

    def getSettingDataString(self):
        return """{
            "name": "Discover Settings 5.9.0",
            "key": "DiscoverSettings",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "cura_version":
                {
                    "label": "Cura version number to check",
                    "description": "Select the version number.  The script should find fdmprinter.def.json and check all the settings in the file.",
                    "type": "enum",
                    "options": {
                        "v5_90": "5.9.0",
                        "v5_81": "5.8.1",
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
                },
                "compare_to_version":
                {
                    "label": "Compare to version...",
                    "description": "Select the version number.  The script should find fdmprinter.def.json and check all the settings in the file.",
                    "type": "enum",
                    "options": {
                        "no_compare": "No Compare",
                        "v5_81": "5.8.1",
                        "v5_72": "5.7.2",
                        "v5_71": "5.7.1",
                        "v5_70": "5.7.0",
                        "v5_6": "5.6.0",
                        "v5_5": "5.5.0",
                        "v5_4": "5.4.0",
                        "v5_2": "5.2.2",
                        "v4_13": "4.13.1"
                        },
                    "default_value": "no_compare"
                }
            }
        }"""

    def execute(self, data): #Application.getInstance().getPrintInformation().
        init_version = self.getSettingValueByKey("cura_version")
        if init_version == "v5_90":
            init_path = r"C:\Program Files\UltiMaker Cura 5.9.0\share\cura\resources\definitions\fdmprinter.def.json"
        if init_version == "v5_81":
            init_path = r"C:\Program Files\UltiMaker Cura 5.8.1\share\cura\resources\definitions\fdmprinter.def.json"
        elif init_version == "v5_72":
            init_path = r"C:\Program Files\UltiMaker Cura 5.7.2\share\cura\resources\definitions\fdmprinter.def.json"
        elif init_version == "v5_71":
            init_path = r"C:\Program Files\UltiMaker Cura 5.7.1\share\cura\resources\definitions\fdmprinter.def.json"
        elif init_version == "v5_70":
            init_path = r"C:\Program Files\UltiMaker Cura 5.7.0\share\cura\resources\definitions\fdmprinter.def.json"
        elif init_version == "v5_6":
            init_path = r"C:\Program Files\UltiMaker Cura 5.6.0\share\cura\resources\definitions\fdmprinter.def.json"
        elif init_version == "v5_5":
            init_path = r"C:\Program Files\UltiMaker Cura 5.5.0\share\cura\resources\definitions\fdmprinter.def.json"
        elif init_version == "v5_4":
            init_path = r"C:\Program Files\UltiMaker Cura 5.4.0\share\cura\resources\definitions\fdmprinter.def.json"
        elif init_version == "v5_2":
            init_path = r"C:\Program Files\UltiMaker Cura 5.2.2\share\cura\resources\definitions\fdmprinter.def.json"
        elif init_version == "v4_13":
            init_path = r"C:\Program Files\Ultimaker Cura 4.13.1\resources\definitions\fdmprinter.def.json"
        elif init_version == "v5_7b":
            init_path = r"C:\Program Files\UltiMaker Cura 5.7.0-beta.1\share\cura\resources\definitions\fdmprinter.def.json"

        compare_to_version = self.getSettingValueByKey("compare_to_version")
        if compare_to_version == "no_compare":
            ct_init_path = ""
        elif compare_to_version == "v5_81":
            ct_init_path = r"C:\Program Files\UltiMaker Cura 5.8.1\share\cura\resources\definitions\fdmprinter.def.json"
        elif compare_to_version == "v5_72":
            ct_init_path = r"C:\Program Files\UltiMaker Cura 5.7.2\share\cura\resources\definitions\fdmprinter.def.json"
        elif compare_to_version == "v5_71":
            ct_init_path = r"C:\Program Files\UltiMaker Cura 5.7.1\share\cura\resources\definitions\fdmprinter.def.json"
        elif compare_to_version == "v5_70":
            ct_init_path = r"C:\Program Files\UltiMaker Cura 5.7.0\share\cura\resources\definitions\fdmprinter.def.json"
        elif compare_to_version == "v5_6":
            ct_init_path = r"C:\Program Files\UltiMaker Cura 5.6.0\share\cura\resources\definitions\fdmprinter.def.json"
        elif compare_to_version == "v5_5":
            ct_init_path = r"C:\Program Files\UltiMaker Cura 5.5.0\share\cura\resources\definitions\fdmprinter.def.json"
        elif compare_to_version == "v5_4":
            ct_init_path = r"C:\Program Files\UltiMaker Cura 5.4.0\share\cura\resources\definitions\fdmprinter.def.json"
        elif compare_to_version == "v5_2":
            ct_init_path = r"C:\Program Files\UltiMaker Cura 5.2.2\share\cura\resources\definitions\fdmprinter.def.json"
        elif compare_to_version == "v4_13":
            ct_init_path = r"C:\Program Files\Ultimaker Cura 4.13.1\resources\definitions\fdmprinter.def.json"
        elif compare_to_version == "v5_7b":
            ct_init_path = r"C:\Program Files\UltiMaker Cura 5.7.0-beta.1\share\cura\resources\definitions\fdmprinter.def.json"

        data[0] = "Cura Settings in version: " + str(init_version) + "\n"
        versions = [init_version]
        if compare_to_version != "no_compare":
            versions.append(compare_to_version)
        for cura_version in versions:
            if cura_version == init_version:
                fdm_path = init_path
            elif cura_version == compare_to_version:
                fdm_path = ct_init_path
            machine_setting_list = []
            quality_setting_list =[]
            fdm_file = open(fdm_path, "r")
            whole_file = fdm_file.read()
            fdm_file.close()
            total_setting_list = []
            category_list = []
            data[0] += "Total Settings: XXX"
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
            end_at = "    dual:"
            bed_adhesion_setting_list = self._get_settings(whole_file, start_at, end_at)[0]
            label_list = self._get_settings(whole_file, start_at, end_at)[1]
            data[0] += "\n    [Build Plate Adhesion]\n"
            for lnum in range(0, len(bed_adhesion_setting_list),1):
                data[0] += bed_adhesion_setting_list[lnum] + str("."*(50-len(bed_adhesion_setting_list[lnum]))) + " ;" + label_list[lnum] + "\n"
            total_setting_list.append(str(len(bed_adhesion_setting_list)))
            category_list.append("Adhesion:        ")
            
            start_at = "    dual:"
            end_at = "    meshfix:"
            dual_extruder_setting_list = self._get_settings(whole_file, start_at, end_at)[0]
            label_list = self._get_settings(whole_file, start_at, end_at)[1]
            data[0] += "\n    [Dual Extruder]\n"
            for lnum in range(0, len(dual_extruder_setting_list),1):
                data[0] += dual_extruder_setting_list[lnum] + str("."*(50-len(dual_extruder_setting_list[lnum]))) + " ;" + label_list[lnum] + "\n"
            total_setting_list.append(str(len(dual_extruder_setting_list)))
            category_list.append("Dual Extruder:   ")

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
                data[0] += commandline_setting_list[lnum] + str("."*(51-len(commandline_setting_list[lnum]))) + " ;" +label_list[lnum] + "\n"
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
            if cura_version == init_version:
                init_setting_list = cura_setting_list
                data[0] += "\n\n\ncura_keywords_1 = " + str(cura_setting_list) + "\n\n\n"
            elif cura_version == compare_to_version:
                ct_setting_list = cura_setting_list
                data[0] += "\n\n\ncura_keywords_2 = " + str(cura_setting_list) + "\n\n\n"
        add_setting_list = ['ADDED to ' + init_version]
        del_setting_list = ['OBSOLETED from ' + compare_to_version]
        for setting in init_setting_list:
            if setting not in ct_setting_list:
                add_setting_list.append(setting)
        for setting in ct_setting_list:
            if setting not in init_setting_list:
                del_setting_list.append(setting)
        add_setting_list[0] += " (" + str(len(add_setting_list) - 1) + ")"
        del_setting_list[0] += " (" + str(len(del_setting_list) - 1) + ")"
        data[0] = "\n".join(add_setting_list) + "\n\n" + "\n".join(del_setting_list) + "\n\n" + data[0]
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
