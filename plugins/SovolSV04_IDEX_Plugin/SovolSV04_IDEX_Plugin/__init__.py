# Copyright (c) 2024 GregValiant
# Sovol SV04 IDEX Converter is released under the terms of the AGPLv3 or higher.

from . import SovolSV04_IDEX_Plugin


def getMetaData():
    return {}

def register(app):
    return {"extension": SovolSV04_IDEX_Plugin.SovolSV04_IDEX_Plugin()}
