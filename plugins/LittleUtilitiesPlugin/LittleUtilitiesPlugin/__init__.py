# Copyright (c) 2024 GregValiant
# Little Utilities is released under the terms of the AGPLv3 or higher.

from . import LittleUtilitiesPlugin


def getMetaData():
    return {}

def register(app):
    return {"extension": LittleUtilitiesPlugin.LittleUtilitiesPlugin()}
