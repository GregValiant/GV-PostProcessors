# Copyright (c) 2024 GregValiant
# 'MaxVolumetricSpeed' is released under the terms of the AGPLv3 or higher.

from . import ConfigureFirmwareRetractPlugin


def getMetaData():
    return {}

def register(app):
    return {"extension": ConfigureFirmwareRetractPlugin.ConfigureFirmwareRetractPlugin()}
