# Copyright (c) 2024 GregValiant
# 'MaxVolumetricSpeed' is released under the terms of the AGPLv3 or higher.

from . import MaxVolumetricFlowPlugin


def getMetaData():
    return {}

def register(app):
    return {"extension": MaxVolumetricFlowPlugin.MaxVolumetricFlowPlugin()}
