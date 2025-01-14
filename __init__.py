# Initial Copyright (c)2022 5@xes
# The CalibrationShapes plugin is released under the terms of the AGPLv3 or higher.

from . import CalibrationShapesReborn

def getMetaData():
    return {}

def register(app):
    return {"extension": CalibrationShapesReborn.CalibrationShapesReborn()}
