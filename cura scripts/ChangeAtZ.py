# ChangeAtZ script - Obsolete - use Change At Layer

from typing import List, Dict
from ..Script import Script


# this was broken up into a separate class so the main ChangeAtZ script could be debugged outside of Cura
class ChangeAtZ(Script):

    def getSettingDataString(self):
        return """{
            "name": "Obsolete - Use ChangeAtLayer",
            "key": "ChangeAtZ",
            "metadata": {},
            "version": 2,
            "settings": {
                "caz_enabled": {
                    "label": "Enabled",
                    "description": "Allows adding multiple ChangeAtZ mods and disabling them as needed.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": false
                }
            }
        }"""

    def execute(self, data):
        return data