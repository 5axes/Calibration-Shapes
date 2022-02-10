#------------------------------------------------------------------------------------------------------------------------------------
#
# Cura PostProcessing Script
# Author:   5axes
# Date:     January 13, 2020
#
# Description:  postprocessing-script to easily use an temptower and not use 10 changeAtZ-scripts
#
#
#------------------------------------------------------------------------------------------------------------------------------------
#
#   Version 1.1 9/01/2020
#   Version 1.2 11/01/2020  Fan modification after Bridge
#   Version 1.3 18/04/2021  : ChangeLayerOffset += 2
#   Version 1.4 18/05/2021  : ChangeLayerOffset
#
#------------------------------------------------------------------------------------------------------------------------------------

from ..Script import Script
from UM.Application import Application
from UM.Logger import Logger

__version__ = '1.4'

class TempFanTower(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name": "TempFanTower",
            "key": "TempFanTower",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "startTemperature":
                {
                    "label": "Starting Temperature",
                    "description": "The starting temperature of the TempTower",
                    "type": "int",
                    "default_value": 220,
                    "minimum_value": 100,
                    "maximum_value": 300,
                    "minimum_value_warning": 170,
                    "maximum_value_warning": 280
                },
                "temperaturechange":
                {
                    "label": "Temperature Increment",
                    "description": "The temperature change of each block, can be positive or negative. If you want 220 and then 210, you need to set this to -10",
                    "type": "int",
                    "default_value": -5,
                    "minimum_value": -100,
                    "maximum_value": 100,
                    "minimum_value_warning": -20,
                    "maximum_value_warning": 20
                },
                "changelayer":
                {
                    "label": "Change Layer",
                    "description": "How many layers needs to be printed before the temperature should be changed",
                    "type": "float",
                    "default_value": 52,
                    "minimum_value": 1,
                    "maximum_value": 1000,
                    "minimum_value_warning": 5,
                    "maximum_value_warning": 100
                },
                "changelayeroffset":
                {
                    "label": "Change Layer Offset",
                    "description": "If the Temptower has a base, put the layer high off it here",
                    "type": "float",
                    "default_value": 5,
                    "minimum_value": 0,
                    "maximum_value": 1000,
                    "maximum_value_warning": 100
                },
                "usefanvalue":
                {
                    "label": "Activate Fan Tower",
                    "description": "Activate also a fan variation to create a Fan Tower",
                    "type": "bool",
                    "default_value": false
                },
                "fanchange":
                {
                    "label": "Fan values in %",
                    "description": "The fan speed change of each block, list value separated by a comma ';' ",
                    "type": "str",
                    "default_value": "100;40;0",
                    "enabled": "usefanvalue"
                }
            }
        }"""

    def execute(self, data):
        
        startTemperature = self.getSettingValueByKey("startTemperature")
        temperaturechange = self.getSettingValueByKey("temperaturechange")
        changelayer = self.getSettingValueByKey("changelayer")
        ChangeLayerOffset = self.getSettingValueByKey("changelayeroffset")
        ChangeLayerOffset += 2  # Modification to take into account the numbering offset in Gcode
                                # layer_index = 0 for initial Block 1= Start Gcode normaly first layer = 0
        
        fanvalues_str = self.getSettingValueByKey("fanchange")
        fanvalues = fanvalues_str.split(";")
        nbval = len(fanvalues) - 1
        usefan = False
        
        if (nbval>0):
            usefan = bool(self.getSettingValueByKey("usefanvalue"))
        else:
            usefan = False

        
        currentTemperature = startTemperature
        currentfan = int((int(fanvalues[0])/100)*255)  #  100% = 255 pour ventilateur

        idl=0
        afterbridge = False
        
        for layer in data:
            layer_index = data.index(layer)
            
            lines = layer.split("\n")
            for line in lines:
                if line.startswith("M106 S") and ((layer_index-ChangeLayerOffset)>0) and (usefan) and (afterbridge):
                    line_index = lines.index(line)
                    currentfan = int((int(fanvalues[idl])/100)*255)  #  100% = 255 pour ventilateur
                    lines[line_index] = "M106 S"+str(int(currentfan))+ " ; FAN MODI"
                    afterbridge == False                    

                if line.startswith("M107") and ((layer_index-ChangeLayerOffset)>0) and (usefan):
                    afterbridge == True
                    line_index = lines.index(line)
                
                if line.startswith(";LAYER:"):
                    line_index = lines.index(line)
                    
                    if (layer_index==ChangeLayerOffset):
                        lines.insert(line_index + 1, ";TYPE:CUSTOM LAYER")
                        lines.insert(line_index + 2, "M104 S"+str(currentTemperature))
                        idl=0
                        if (usefan):
                            currentfan = int((int(fanvalues[idl])/100)*255)  #  100% = 255 pour ventilateur
                            lines.insert(line_index + 3, "M106 S"+str(currentfan))
                        
                    if ((layer_index-ChangeLayerOffset) % changelayer == 0) and ((layer_index-ChangeLayerOffset)>0):
                        if (usefan) and (idl < nbval):
                            idl += 1
                            currentfan = int((int(fanvalues[idl])/100)*255)  #  100% = 255 pour ventilateur
                            lines.insert(line_index + 1, ";TYPE:CUSTOM FAN")
                            lines.insert(line_index + 2, "M106 S"+str(int(currentfan)))    
                        else:
                            currentTemperature += temperaturechange
                            lines.insert(line_index + 1, ";TYPE:CUSTOM TEMP")
                            lines.insert(line_index + 2, "M104 S"+str(currentTemperature))
                            if (usefan):
                                # On repart à la valeur de départ
                                idl = 0
                                currentfan = int((int(fanvalues[idl])/100)*255)  #  100% = 255 pour ventilateur
                                lines.insert(line_index + 3, "M106 S"+str(int(currentfan)))
                                                
            
            result = "\n".join(lines)
            data[layer_index] = result

        return data
