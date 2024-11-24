# Copyright (c) 2023 GregValiant
#
# When Annealing:
#    The user may elect to hold the build plate at a temperature for a period of time.  When the hold expires, the 'Timed Cooldown' will begin.
#    If there is no Hold Time then the Timed Cooldown will begin when the print ends.
# When drying filament:
#    The bed must be empty because the printer will auto-home before raising the Z to 'machine_height - 20' and then park the head.
#    The bed will heat up.  G4 commands are used to keep the machine from turning the bed off until the Drying Time has expired.

from UM.Application import Application
from ..Script import Script
from UM.Message import Message

class AnnealingOrDrying(Script):

    def initialize(self) -> None:
        super().initialize()
        # Get the bed temperature from Cura
        bed_temp = str(Application.getInstance().getGlobalContainerStack().getProperty("material_bed_temperature", "value"))
        self._instance.setProperty("startout_temp", "value", bed_temp)
        # Get the build volume heat if there is one
        heated_build_volume = bool(Application.getInstance().getGlobalContainerStack().getProperty("machine_heated_build_volume", "value"))
        if heated_build_volume:
            chamber_temp = Application.getInstance().getGlobalContainerStack().getProperty("build_volume_temperature", "value")
            self._instance.setProperty("has_build_volume_heater", "value", heated_build_volume)
            self._instance.setProperty("build_volume_temp", "value", chamber_temp)

    def getSettingDataString(self):
        return """{
            "name": "Annealing CoolDown or Filament Drying",
            "key": "AnnealingOrDrying",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "enable_annealing":
                {
                    "label": "Enable the Script",
                    "description": "If it isn't enabled it doesn't run.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": true
                },
                "cycle_type":
                {
                    "label": "Anneal or Dry Filament",
                    "description": "Whether to Anneal the Print (by keeping the bed hot for a period of time), or to use the bed as a Filament Dryer.  If drying; you will still need to slice a model, but it will not print. The gcode will consist only of a short script to heat the bed, wait for a while, then turn the bed off.  The 'Z' will move to the max height and XY park position so the filament can be covered. The 'Hold Time', 'Bed Start Temp' and (if applicable) the 'Chamber Temp' come from these settings rather than from the Cura settings.  When annealing; the timed cooldown will commence when the print ends.",
                    "type": "enum",
                    "options":
                    {
                        "dry_cycle": "Dry Filament",
                        "anneal_cycle": "Anneal Print"},
                    "default_value": "dry_cycle",
                    "enabled": true,
                    "enabled": "enable_annealing"
                },
                "bed_and_chamber":
                {
                    "label": "Hold the Temp for the:",
                    "description": "Select the 'Bed' for just the bed, or 'Bed and Chamber' if you want to include your 'Heated Build Volume'.",
                    "type": "enum",
                    "options":
                    {
                        "bed_only": "Bed",
                        "bed_chamber": "Bed and Chamber"},
                    "default_value": "bed_only",
                    "enabled": "enable_annealing"
                },
                "wait_time":
                {
                    "label": "Hold Time at Temp(s)",
                    "description": "Hold the bed temp at the 'Bed Start Out Temperature' for this amount of time (in decimal hours).  When this time expires then the Annealing cool down will start.  This is also the 'Drying Time used when 'Drying Filament'.",
                    "type": "float",
                    "default_value": 0.0,
                    "unit": "Decimal Hrs ",
                    "enabled": "enable_annealing and cycle_type == 'anneal_cycle'"
                },
                "dry_time":
                {
                    "label": "Drying Time",
                    "description": "Hold the bed temp at the 'Bed Start Out Temperature' for this amount of time (in decimal hours).  When this time expires the bed will shut off.",
                    "type": "float",
                    "default_value": 4.0,
                    "unit": "Decimal Hrs ",
                    "enabled": "enable_annealing and cycle_type == 'dry_cycle'"
                },
                "pause_cmd":
                {
                    "label": "Pause Cmd for Auto-Home",
                    "description": "Not required when you are paying attention and the bed is empty; ELSE; Enter the pause command to use prior to the Auto-Home command.  The pause insures that the user IS paying attention and clears the build plate for Auto-Home.  If you leave the box empty then there won't be a pause.",
                    "type": "str",
                    "default_value": "",
                    "enabled": "enable_annealing and cycle_type == 'dry_cycle'"
                },
                "startout_temp":
                {
                    "label": "Bed Start Out Temperature:",
                    "description": "Enter the temperature to start at.  This is typically the bed temperature during the print but can be changed here.  This is also the temperature used when drying filament.",
                    "type": "int",
                    "value": 30,
                    "unit": "Degrees ",
                    "minimum_value": 30,
                    "maximum_value": 110,
                    "maximum_value_warning": 100,
                    "enabled": "enable_annealing"
                },
                "lowest_temp":
                {
                    "label": "Shut-Off Temp:",
                    "description": "Enter the lowest temperature to control the cool down.  This is the shut-off temperature for the build plate and (when applicable) the Heated Chamber.  The minimum value is 30",
                    "type": "int",
                    "default_value": 30,
                    "unit": "Degrees ",
                    "minimum_value": 30,
                    "enabled": "enable_annealing and cycle_type == 'anneal_cycle'"
                },
                "build_volume_temp":
                {
                    "label": "Build Volume Temperature:",
                    "description": "Enter the temperature for the Build Volume (Heated Chamber).  This is typically the temperature during the print but can be changed here.",
                    "type": "int",
                    "value": 24,
                    "unit": "Degrees ",
                    "minimum_value": 0,
                    "maximum_value": 90,
                    "maximum_value_warning": 75,
                    "enabled": "enable_annealing and has_build_volume_heater and bed_and_chamber == 'bed_chamber'"
                },
                "time_span":
                {
                    "label": "Cool Down Time Span:",
                    "description": "The total amount of time (in decimal hours) to control the cool down.  The build plate temperature will be dropped in 3° increments across this time span.  'Cool Down Time' starts at the end of the 'Hold Time' if you entered one.",
                    "type": "float",
                    "default_value": 1.0,
                    "unit": "Decimal Hrs ",
                    "minimum_value_warning": 0.25,
                    "enabled": "enable_annealing and cycle_type == 'anneal_cycle'"
                },
                "park_head":
                {
                    "label": "Park at MaxY and MaxX",
                    "description": "When unchecked, the park position is X0 Y0.  Enable this setting to move the nozzle to the Max X and Max Y to allow access to the print.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "enable_annealing and cycle_type == 'anneal_cycle'"
                },
                "park_max_z":
                {
                    "label": "Move to MaxZ",
                    "description": "Enable this setting to move the nozzle to 'Machine_Height - 20' to allow the print to be covered.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "enable_annealing and cycle_type == 'anneal_cycle'"
                },
                "beep_when_done":
                {
                    "label": "Beep when done",
                    "description": "Add an annoying noise when the Cool Down completes.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": "enable_annealing"
                },
                "beep_duration":
                {
                    "label": "Beep Duration",
                    "description": "The length of the buzzer sound.  Units are in milliseconds so 1000ms = 1 second.",
                    "type": "int",
                    "unit": "milliseconds ",
                    "default_value": 1000,
                    "enabled": "beep_when_done and enable_annealing"
                },
                "add_messages":
                {
                    "label": "Include M117 and M118 messages",
                    "description": "Add messages to the LCD and any print server.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "enable_annealing"
                },
                "has_build_volume_heater":
                {
                    "label": "Hidden setting",
                    "description": "Hidden.  This setting enables the build volume settings.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": false
                }
            }
        }"""

    def execute(self, data):
        # Exit if there is no heated bed.
        if not bool(Application.getInstance().getGlobalContainerStack().getProperty("machine_heated_bed", "value")):
            Message(title = "[Anneal or Dry Filament]", text = "The script did not run because Heated Bed is disabled in Machine Settings.").show()
            return data
        # Enter a message in the gcode if the script is not enabled.
        if not bool(self.getSettingValueByKey("enable_annealing")):
            data[0] += ";    [Anneal or Dry Filament] was not enabled\n"
            return data
        lowest_temp = int(self.getSettingValueByKey("lowest_temp"))

        # If the shutoff temp is under 30° then exit as a safety precaution so the bed doesn't stay on.
        if lowest_temp < 30:
            data[0] += ";  Anneal or Dry Filament did not run.  Shutoff Temp < 30\n"
            Message(title = "[Anneal or Dry Filament]", text = "The script did not run because the Shutoff Temp is less than 30°.").show()
            return data
        curaApp = Application.getInstance().getGlobalContainerStack()
        time_span = int(float(self.getSettingValueByKey("time_span")) * 3600)
        bed_temperature = int(self.getSettingValueByKey("startout_temp"))
        heated_chamber = bool(Application.getInstance().getGlobalContainerStack().getProperty("machine_heated_build_volume", "value"))
        anneal_type = self.getSettingValueByKey("bed_and_chamber")

        # Get the heated chamber temperature or set to 0 if no chamber
        if heated_chamber:
            chamber_temp = str(self.getSettingValueByKey("build_volume_temp"))
        else:
            anneal_type = "bed_only"
            chamber_temp = "0"
        # Park Head
        max_y = str(curaApp.getProperty("machine_depth", "value"))
        max_x = str(curaApp.getProperty("machine_width", "value"))
        # Max_z is limited to machine_height - 20 just so the print head doesn't smack into anything.
        max_z = str(int(curaApp.getProperty("machine_height", "value")) - 20)
        extruder = curaApp.extruderList
        travel_speed = str(round(extruder[0].getProperty("speed_travel", "value")*60, 2))
        park_xy = bool(self.getSettingValueByKey("park_head"))
        park_z = bool(self.getSettingValueByKey("park_max_z"))
        cycle_type = self.getSettingValueByKey("cycle_type")
        add_messages = bool(self.getSettingValueByKey("add_messages"))


        if cycle_type == "anneal_cycle":
            # Put the head parking string together
            park_string = ""
            if park_xy and not park_z:
                park_string = f"G0 F{travel_speed} X{max_x} Y{max_y} ;Park XY\nM18 X Y E ;Disable steppers except Z\n"
            elif park_xy and park_z:
                park_string = f"G0 F{travel_speed} X{max_x} Y{max_y} ;Park XY\nG0 Z{max_z} ;Raise Z to max - 20\nM18 X Y E ;Disable steppers except Z\n"
            elif not park_xy and park_z:
                park_string = f"G0 F{travel_speed} Z{max_z} ;Raise Z to max - 10\nM18 X Y E ;Disable steppers except Z\n"

            # Calculate the temperature differential
            hysteresis = bed_temperature - lowest_temp

            # if the bed temp is below the shutoff temp then exit
            if hysteresis <= 0:
                data[0] += ";  Anneal or Dry Filament did not run.  Bed Temp < Shutoff Temp\n"
                Message(title = "Anneal or Dry Filament", text = "Did not run because the Bed Temp < Shutoff Temp.").show()
                return data

            # Drop the bed temperature in 3° increments.  We only want integers.
            num_steps = int(hysteresis / 3)
            step_index = 2
            deg_per_step = int(hysteresis / num_steps)
            time_per_step = int(time_span / num_steps)
            step_down = bed_temperature - deg_per_step
            if cycle_type == "anneal_cycle":
                wait_time = int(float(self.getSettingValueByKey("wait_time")) * 3600)
            else:
                wait_time = int(float(self.getSettingValueByKey("dry_time")) * 3600)                

            # Put the first lines of the anneal string together
            anneal_string = ";TYPE:CUSTOM: Anneal or Dry Filament\n"
            if add_messages:
                anneal_string += "M117 Cool Down for " + str(round((wait_time + time_span)/3600,2)) + "hr\n"
                anneal_string += "M118 Cool Down for " + str(round((wait_time + time_span)/3600,2)) + "hr\n" + park_string
            if wait_time > 0:
                if anneal_type == "bed_only":
                    anneal_string += f"M190 S{bed_temperature}\n"
                if anneal_type == "bed_chamber":
                    anneal_string += f"M190 S{bed_temperature}\nM141 S{chamber_temp}\n"
                anneal_string += f"G4 S{wait_time}\n"
            anneal_string += f"M140 S{step_down}\nG4 S{time_per_step}\n"
            step_down -= deg_per_step

            # Step the bed/chamber temps down and add each step to the anneal string.  The chamber remains at temperature until the bed gets down to that temperature.
            for num in range(bed_temperature, lowest_temp, -3):
                anneal_string += f"M140 S{step_down}\n"
                if anneal_type == "bed_chamber" and int(step_down) < int(chamber_temp):
                    anneal_string += f"M141 S{step_down}\n"
                anneal_string += f"G4 S{time_per_step}\n"
                time_remaining = round((time_span-(step_index*time_per_step))/3600,2)
                if time_remaining >= 1.00:
                    if add_messages:
                        anneal_string += f"M117 CoolDown - {round(time_remaining,1)}hr\n"
                        anneal_string += f"M118 CoolDown - {round(time_remaining,1)}hr\n"
                else:
                    time_seconds = round(time_remaining * 60)
                    if add_messages:
                        anneal_string += f"M117 CoolDown - {time_seconds}min\n"
                        anneal_string += f"M118 CoolDown - {time_seconds}min\n"
                step_down -= deg_per_step
                step_index += 1
                if step_down < lowest_temp:
                    break

            # Maybe add the Beep line
            if bool(self.getSettingValueByKey("beep_when_done")):
                beep_string = "M300 S440 P" + str(self.getSettingValueByKey("beep_duration")) + "\n"
            else:
                beep_string = ""
                
            # Close out the anneal string
            anneal_string += "M140 S0 ;Shut off the bed heater" + "\n"
            if anneal_type == "bed_chamber":
                anneal_string += "M141 S0 ;Shut off the chamber heater\n"
            anneal_string += beep_string
            if add_messages:
                anneal_string += "M117 CoolDown Complete\n"
                anneal_string += "M118 CoolDown Complete\n;TYPE:CUSTOM End of Cool Down\n"
            layer = data[len(data)-1]
            lines = layer.split("\n")

            # Comment out the M140 S0 line in the ending gcode.
            for num in range(len(lines)-1,-1,-1):
                if lines[num].startswith("M140 S0"):
                    lines[num] = ";M140 S0 ; Shutoff Overide - Anneal or Dry Filament"
                    data[len(data)-1] = "\n".join(lines)

            # If there is a Heated Chamber and it's included then comment out the M141 S0 line
            if anneal_type == "bed_chamber" and heated_chamber:
                for num in range(0,len(lines)-1,1):
                    if lines[num].startswith("M141 S0"):
                        lines[num] = ";M141 S0 ; Shutoff Overide - Anneal or Dry Filament"
                        data[len(data)-1] = "\n".join(lines)

            # If park head is enabled then dont let the steppers disable until the head is parked
            disable_string = ""
            if bool(self.getSettingValueByKey("park_head")) or bool(self.getSettingValueByKey("park_max_z")):
                for num in range(0,len(lines)-1,1):
                    if lines[num].startswith("M84") or lines[num].startswith("M18"):
                        disable_string = lines[num] + "\n"
                        stepper_timeout = int(wait_time + time_span)
                        if stepper_timeout > 14400: stepper_timeout = 14400
                        lines[num] = ";" + lines[num] + " ; Overide - Anneal or Dry Filament"
                        lines.insert(num, "M84 S" + str(stepper_timeout) + " ; Increase stepper timeout - Anneal or Dry Filament")
                        data[len(data)-1] = "\n".join(lines)
                        break
            # The Anneal string is the new end of the gcode so move the 'End of Gcode' comment line in case there are other posts running
            data[len(data)-1] = data[len(data)-1].replace(";End of Gcode", anneal_string + disable_string + ";End of Gcode")
        
        elif cycle_type == "dry_cycle":
            data = self._dry_filament_only(data, anneal_type, heated_chamber, chamber_temp, bed_temperature, max_z, max_y)
        return data

    def _dry_filament_only(self, drydata: str, anneal_type: str, heated_chamber: bool, chamber_temp: int, bed_temperature: int, max_z:str, max_y:str) -> str:
        for num in range(2, len(drydata)):
            drydata[num] = ""
        drydata[0] = drydata[0].split("\n")[0] + "\n"
        add_messages = bool(self.getSettingValueByKey("add_messages"))
        pause_cmd = self.getSettingValueByKey("pause_cmd").upper()
        if pause_cmd != "":
            pause_cmd = "M300\n" + pause_cmd
        dry_time = self.getSettingValueByKey("dry_time") * 3600
        extruder = Application.getInstance().getGlobalContainerStack().extruderList
        speed_travel = str(extruder[0].getProperty("speed_travel", "value") * 60)
        lines = drydata[1].split("\n")
        drying_string = lines[0] + "\n" + ";............TYPE:CUSTOM: Dry Filament\n"
        if add_messages:
            drying_string += f"M117 Cool Down for {round(dry_time/3600,2)} hr ; Message\n"
            drying_string += f"M118 Cool Down for {round(dry_time/3600,2)} hr ; Message\n"
        # M113 sends messages to a print server as a 'Keep Alive' and can generate a lot of traffic over the USB
        drying_string += "M113 S0 ; No echo\n"
        drying_string += f"M84 S{round(dry_time)} ; Set stepper timeout\n"
        drying_string += f"M140 S{bed_temperature} ; Heat bed\n"
        if heated_chamber and anneal_type == "bed_chamber":
            drying_string += f"M141 S{chamber_temp} ; Chamber temp\n"
        if pause_cmd == "M0":
            pause_cmd = "M0 Clear bed and click...; Pause"
        if pause_cmd != "":
            drying_string += pause_cmd + " ; Pause\n"
        drying_string += "G28 ; Auto-Home\n"
        drying_string += f"G0 F{speed_travel} Z{max_z} ; Raise print head\n"
        drying_string += f"G0 F{speed_travel} X0 Y{max_y} ; Park print head\n"
        if dry_time <= 3600:
            if add_messages:
                drying_string += f"M117 {dry_time/3600} hr remaining ; Message\n"
                drying_string += f"M118 {dry_time/3600} hr remaining ; Message\n"
            drying_string += f"G4 S{dry_time} ; Dry time\n"
        elif dry_time > 3600:
            temp_time = dry_time
            while temp_time > 3600:
                if add_messages:
                    drying_string += f"M117 {temp_time/3600} hr remaining ; Message\n"
                    drying_string += f"M118 {temp_time/3600} hr remaining ; Message\n"
                drying_string += f"G4 S3600 ; Dry time split\n"
                if temp_time > 3600:
                    temp_time -= 3600
            if temp_time > 0:
                if add_messages:
                    drying_string += f"M117 {temp_time/3600} hr remaining ; Message\n"
                    drying_string += f"M118 {temp_time/3600} hr remaining ; Message\n"
                drying_string += f"G4 S{temp_time} ; Dry time\n"
        if heated_chamber and anneal_type == "bed_chamber":
            drying_string += f"M141 S0 ; Shut off chamber\n"
        drying_string += "M140 S0 ; Shut off bed\n"
        if self.getSettingValueByKey("beep_when_done"):
            beep_duration = self.getSettingValueByKey("beep_duration")
            drying_string += f"M300 P{beep_duration} ; Beep\n"
        if add_messages:
            drying_string += "M117 End of drying cycle ; Message\n"
            drying_string += "M118 End of drying cycle ; Message\n"
        drying_string += "M84 X Y E ; Disable steppers except Z\n"
        drying_string += ";End of Gcode"
        # Format
        lines = drying_string.split("\n")
        for index, line in enumerate(lines):
            if not line.startswith(";") and ";" in line:
                front_txt = lines[index].split(";")[0]
                back_txt = lines[index].split(";")[1]
                lines[index] = front_txt + str(" " * (30 - len(front_txt))) +";" +  back_txt
        drydata[1] = "\n".join(lines) + "\n"
        dry_txt = "Drying time ...................... " + str(self.getSettingValueByKey("dry_time")) + " hrs\n"
        dry_txt += "Drying temperature ........ " + str(bed_temperature) + "°\n"
        if heated_chamber and anneal_type == "bed_chamber":
            dry_txt += "Chamber temperature ... " + str(chamber_temp) + "°"
        Message(title = "[Dry Filament]", text = dry_txt).show()
        return drydata