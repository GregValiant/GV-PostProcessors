# Copyright (c) 2024 GregValiant
# Flash Forge IDEX Converter is released under the terms of the AGPLv3 or higher.

from . import FlashForge_IDEX_Plugin


def getMetaData():
    return {}

def register(app):
    return {"extension": FlashForge_IDEX_Plugin.FlashForge_IDEX_Plugin()}
