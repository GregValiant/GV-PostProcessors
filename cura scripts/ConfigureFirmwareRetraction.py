

from ..Script import Script
from UM.Application import Application
from UM.Message import Message
import re
import os

class ConfigureFirmwareRetraction(Script):

    def initialize(self) -> None:
        super().initialize()
        curaApp = Application.getInstance().getGlobalContainerStack()
        extruder = curaApp.extruderList
        
        self.extruder_count = curaApp.getProperty("machine_extruder_count", "value")
        if self.extruder_count > 1:
            self._instance.setProperty("multi_extruder", "value", True)
            self.retract_amt_t1 = extruder[1].getProperty("retraction_amount", "value")        
            self._instance.setProperty("retract_amount_t1", "value", self.retract_amt_t1)
                
            self.retract_speed_t1 = extruder[1].getProperty("retraction_retract_speed", "value")        
            self._instance.setProperty("retract_speed_t1", "value", self.retract_speed_t1)
                
            self.default_hop_height_t1 = extruder[1].getProperty("retraction_hop", "value")        
            self._instance.setProperty("retract_hop_t1", "value", self.default_hop_height_t1)
            
            self.extra_prime_t1 = extruder[1].getProperty("retraction_extra_prime_amount", "value")        
            self._instance.setProperty("prime_extra_t1", "value", self.extra_prime_t1)
            
            self.prime_speed_t1 = extruder[1].getProperty("retraction_prime_speed", "value")        
            self._instance.setProperty("prime_speed_t1", "value", self.prime_speed_t1)
            
        
        self.retract_amt_t0 = extruder[0].getProperty("retraction_amount", "value")        
        self._instance.setProperty("retract_amount_t0", "value", self.retract_amt_t0)
            
        self.retract_speed_t0 = extruder[0].getProperty("retraction_retract_speed", "value")        
        self._instance.setProperty("retract_speed_t0", "value", self.retract_speed_t0)
            
        self.default_hop_height_t0 = extruder[0].getProperty("retraction_hop", "value")        
        self._instance.setProperty("retract_hop_t0", "value", self.default_hop_height_t0)
        
        self.extra_prime_t0 = extruder[0].getProperty("retraction_extra_prime_amount", "value")        
        self._instance.setProperty("prime_extra_t0", "value", self.extra_prime_t0)
        
        self.prime_speed_t0 = extruder[0].getProperty("retraction_prime_speed", "value")        
        self._instance.setProperty("prime_speed_t0", "value", self.prime_speed_t0)
 

    def getSettingDataString(self):
        return """{
            "name": "Configure Firmware Retractions",
            "key": "ConfigureFirmwareRetraction",
            "metadata": {},
            "version": 2,
            "settings":
            {                
                "enable_this_script":
                {
                    "label": "Enable the script",
                    "description": "Check the box to enable the script.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": true
                },
                "retract_amount_t0":
                {
                    "label": "T0 Retraction Amount",
                    "description": "The length of filament to retract.",
                    "type": "float",
                    "default_value": 0.0,
                    "unit": "mm",
                    "enabled": "enable_this_script"
                },
                "retract_speed_t0":
                {
                    "label": "T0 Retraction Speed",
                    "description": "How fast to pull back the filament for a retraction.",
                    "type": "int",
                    "default_value": 0,
                    "unit": "mm",
                    "enabled": "enable_this_script"
                },
                "retract_hop_t0":
                {
                    "label": "T0 Z hop height for retractions",
                    "description": "Set to the Hop Height or set to '0' to turn it off.",
                    "type": "float",
                    "unit": "mm",
                    "default_value": 0.0,
                    "enabled": "enable_this_script"
                },
                "prime_speed_t0":
                {
                    "label": "T0 Prime Speed",
                    "description": "T0 Prime Speed",
                    "type": "float",
                    "unit": "mm/sec",
                    "default_value": 0,
                    "enabled": "enable_this_script"
                },
                "prime_extra_t0":
                {
                    "label": "T0 Extra Prime Amount",
                    "description": "T0 Extra Prime amount",
                    "type": "float",
                    "default_value": 0.0,
                    "unit": "mm",
                    "enabled": "enable_this_script"
                },
                "retract_amount_t1":
                {
                    "label": "T1 Retraction Amount",
                    "description": "T1 Retraction Amount",
                    "type": "float",
                    "default_value": 0.0,
                    "enabled": "enable_this_script and multi_extruder"
                },
                "retract_speed_t1":
                {
                    "label": "T1 Retract Speed",
                    "description": "T1 retraction speed",
                    "type": "float",
                    "default_value": 0.0,
                    "unit": "mm/sec",
                    "enabled": "enable_this_script and multi_extruder"
                },
                "retract_hop_t1":
                {
                    "label": "T1 Z hop height",
                    "description": "Set to the Hop Height or set to '0' to turn it off.",
                    "type": "float",
                    "unit": "mm",
                    "default_value": 0.0,
                    "enabled": "enable_this_script and multi_extruder"
                },
                "prime_speed_t1":
                {
                    "label": "T1 Prime Speed",
                    "description": "The prime speed for T1.",
                    "type": "float",
                    "unit": "mm/sec",
                    "default_value": 0,
                    "enabled": "enable_this_script and multi_extruder"
                },
                "prime_extra_t1":
                {
                    "label": "T1 Extra Prime Amount",
                    "description": "T1 extra prime amount.",
                    "type": "float",
                    "default_value": 0.0,
                    "unit": "mm",
                    "enabled": "enable_this_script and multi_extruder"
                },
                "multi_extruder":
                {
                    "label": "Multi-extruder printer",
                    "description": "Hidden setting that enables the T",
                    "type": "bool",
                    "default_value": false,
                    "enabled": false
                }
            }
        }"""
        
    def execute(self, data):
        if not self.getSettingValueByKey("enable_this_script"):
            data[0] += ";    [Configure Firmware Retraction] Not enabled\n"
            return data
        # When retraction is enabled a final retraction goes in as a single line data item after the last layer.
        t0_string = ""
        t1_string = ""
        t0_retract_amt = self.getSettingValueByKey("retract_amount_t0")
        t0_retract_speed = self.getSettingValueByKey("retract_speed_t0")
        t0_hop_hgt = self.getSettingValueByKey("retract_hop_t0")
        t0_prime_speed = self.getSettingValueByKey("prime_speed_t0")
        t0_extra_prime_amt = self.getSettingValueByKey("prime_extra_t0")
        t0_string = f"\nM207 T0 S{t0_retract_amt} F{t0_retract_speed*60} Z{t0_hop_hgt} ; Configure Firmware Retraction"
        t0_string += f"\nM208 T0 F{t0_prime_speed*60} S{t0_extra_prime_amt} ; Configure Firmware Prime"
        if self.extruder_count > 1:
            t1_retract_amt = self.getSettingValueByKey("retract_amount_t1")
            t1_retract_speed = self.getSettingValueByKey("retract_speed_t1")
            t1_hop_hgt = self.getSettingValueByKey("retract_hop_t1")
            t1_prime_speed = self.getSettingValueByKey("prime_speed_t1")
            t1_extra_prime_amt = self.getSettingValueByKey("prime_extra_t1")
            t1_string = f"\nM207 T1 S{t1_retract_amt} F{t1_retract_speed*60} Z{t1_hop_hgt} ;\n; Configure Firmware Retraction"
            t1_string += f"\nM208 T1 F{t1_prime_speed*60} S{t1_extra_prime_amt} ; Configure Firmware Prime"
        start_up = data[1].split("\n")
        for index, line in enumerate(start_up):
            if ";Generated with Cura_SteamEngine" in line:
                start_up[index] += t0_string
                if self.extruder_count > 1:
                    start_up[index] += t1_string + "\n;"
                else:
                    start_up[index] += "\n;"
        data[1] = "\n".join(start_up)
        cura_version = str(Application.getInstance().getVersion())
        data[0] += "\n" + cura_version + "\n"
        return data