# Copyright (c) 2023 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

# Cura PostProcessingPlugin
# Description:  This plugin is superceded by 'Pause at Layer'

from ..Script import Script
from UM.Application import Application
from UM.Message import Message

class PauseAtHeight(Script):
    def initialize(self) -> None:
        Message(title = "[Pause At Height]", text = "This script is obsolete.  Use 'Pause at Layer'.").show()
    
    def getSettingDataString(self):
        return """{
            "name": "PauseAtHeight obsolete use PauseAtLayer",
            "key": "PauseAtHeight",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "notify_user":
                {
                    "label": "Obsolete",
                    "description": "'Pause at Height' has been replaced by 'Pause at Layer.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": true
                }
            }
        }"""

    def execute(self, data):
        Message(title = "[Pause at Height]", text = "This script is obsolete.  Use 'Pause at Layer'.").show()
        data[0] += ";  [Pause at Height] This script is obsolete.  Use 'Pause at Layer'.\n"
        return data
