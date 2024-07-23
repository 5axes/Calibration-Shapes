#------------------------------------------------------------------------------------------------------------------------------------
#
# Cura PostProcessing Script
# Author:   5axes
# Date:     February 29, 2020
#
# Description:  postprocessing script to easily define a Speed Tower 
#           Option for  Speed
#                       Acceleration
#                       Jerk
#                       Junction Deviation
#                       Marlin Linear Advance
#                       RepRap Pressure Advance
#
#------------------------------------------------------------------------------------------------------------------------------------
#
#   Version 1.0 29/02/2020
#   Version 1.1 29/01/2021
#   Version 1.2 05/04/2021 by dotdash32(https://github.com/dotdash32) for Marlin Linear Advance & RepRap Pressure Advance
#   Version 1.3 18/04/2021  : ChangeLayerOffset += 2
#   Version 1.4 18/05/2021  : float
#   Version 1.5 14/02/2022  : Set Speed using M220 S
#   Version 1.6 15/02/2022  : Change Int for changelayeroffset & changelayer
#   Version 1.7 04/08/2022  : Restore and Save the Speed Factor in case of Speed option by using M220 B and M220 R
#                             https://marlinfw.org/docs/gcode/M220.html
#
#------------------------------------------------------------------------------------------------------------------------------------

from ..Script import Script
from UM.Application import Application
from UM.Logger import Logger
import re #To perform the search

__version__ = '1.7'

class SpeedTower(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name": "SpeedTower",
            "key": "SpeedTower",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "command": {
                    "label": "Command",
                    "description": "GCode Commande",
                    "type": "enum",
                    "options": {
                        "speed": "Speed",
                        "acceleration": "Acceleration",
                        "jerk": "Jerk",
                        "junction": "Junction Deviation",
                        "marlinadv": "Marlin Linear",
                        "marlinadv2": "Marlin M493 K",
                        "rrfpresure": "RepRap Pressure"
                    },
                    "default_value": "acceleration"
                },
                "startValue":
                {
                    "label": "Starting value",
                    "description": "The starting value of the Tower.",
                    "type": "float",
                    "default_value": 8.0
                },
                "valueChange":
                {
                    "label": "Value Increment",
                    "description": "The value change of each block, can be positive or negative. I you want 50 and then 40, you need to set this to -10.",
                    "type": "float",
                    "default_value": 4.0
                },
                "changelayer":
                {
                    "label": "Change Layer",
                    "description": "How many layers needs to be printed before the value should be changed.",
                    "type": "int",
                    "default_value": 30,
                    "minimum_value": 1,
                    "maximum_value": 1000,
                    "maximum_value_warning": 100
                },
                "changelayeroffset":
                {
                    "label": "Change Layer Offset",
                    "description": "If the print has a base, indicate the number of layers from which to start the changes.",
                    "type": "int",
                    "default_value": 4,
                    "minimum_value": 0,
                    "maximum_value": 1000,
                    "maximum_value_warning": 100
                },
                "lcdfeedback":
                {
                    "label": "Display details on LCD",
                    "description": "This setting will insert M117 gcode instructions, to display current modification in the G-Code is being used.",
                    "type": "bool",
                    "default_value": true
                }                
            }
        }"""

    def execute(self, data):

        UseLcd = self.getSettingValueByKey("lcdfeedback")
        Instruction = self.getSettingValueByKey("command")
        StartValue = float(self.getSettingValueByKey("startValue"))
        ValueChange = float(self.getSettingValueByKey("valueChange"))
        ChangeLayer = int(self.getSettingValueByKey("changelayer"))
        ChangeLayerOffset = int(self.getSettingValueByKey("changelayeroffset"))
        ChangeLayerOffset += 2  # Modification to take into account the numbering offset in Gcode
                                # layer_index = 0 for initial Block 1= Start Gcode normaly first layer = 0 

        CurrentValue = StartValue
        Command=""
        max_layer=9999
        idl=0
        
        for layer in data:
            layer_index = data.index(layer)
            
            lines = layer.split("\n")
            for line in lines:                  
                if line.startswith(";LAYER_COUNT:"):
                    max_layer = int(line.split(":")[1])   # Recuperation Nb Layer Maxi
                    # Logger.log('d', 'Max_layer : {}'.format(max_layer))
                    
                if line.startswith(";LAYER:"):
                    line_index = lines.index(line)
                    # Logger.log('d', 'Instruction : {}'.format(Instruction))
                    # Logger.log('d', 'layer_index : {}'.format(layer_index))
                    # Logger.log('d', 'ChangeLayerOffset : {}'.format(ChangeLayerOffset))

                    if (layer_index==ChangeLayerOffset):
                        if  (Instruction=='speed'):
                            Command = "M220 B\nM220 S{:d}".format(int(CurrentValue))
                            lcd_gcode = "M117 Speed S{:d}".format(int(CurrentValue))
                        if  (Instruction=='acceleration'):
                            Command = "M204 S{:d}".format(int(CurrentValue))
                            lcd_gcode = "M117 Acceleration S{:d}".format(int(CurrentValue))
                        if  (Instruction=='jerk'):
                            Command = "M205 X{:d} Y{:d}".format(int(CurrentValue), int(CurrentValue))
                            lcd_gcode = "M117 Jerk X{:d} Y{:d}".format(int(CurrentValue), int(CurrentValue))
                        if  (Instruction=='junction'):
                            Command = "M205 J{:.3f}".format(float(CurrentValue))
                            lcd_gcode = "M117 Junction J{:.3f}".format(float(CurrentValue))     
                        if  (Instruction=='marlinadv'):
                            Command = "M900 K{:.3f}".format(float(CurrentValue))
                            lcd_gcode = "M117 Linear Advance K{:.3f}".format(float(CurrentValue))  
                        if  (Instruction=='marlinadv2'):
                            Command = "M493 K{:.6f}".format(float(CurrentValue)/1000)
                            lcd_gcode = "M117 Linear Advance K{:.3f}".format(float(CurrentValue))
                        if  (Instruction=='rrfpresure'):
                            Command = "M572 D0 S{:.3f}".format(float(CurrentValue))
                            lcd_gcode = "M117 Pressure Advance S{:.3f}".format(float(CurrentValue))   
                            
                        lines.insert(line_index + 1, ";TYPE:CUSTOM LAYER")
                        lines.insert(line_index + 2, Command)
                        if UseLcd == True :               
                            lines.insert(line_index + 3, lcd_gcode)

                    if ((layer_index-ChangeLayerOffset) % ChangeLayer == 0) and ((layer_index-ChangeLayerOffset)>0):
                            CurrentValue += ValueChange
                            if  (Instruction=='speed'):
                                Command = "M220 S{:d}".format(int(CurrentValue))
                                lcd_gcode = "M117 Speed S{:d}".format(int(CurrentValue))
                            if  (Instruction=='acceleration'):
                                Command = "M204 S{:d}".format(int(CurrentValue))
                                lcd_gcode = "M117 Acceleration S{:d}".format(int(CurrentValue))
                            if  (Instruction=='jerk'):
                                Command = "M205 X{:d} Y{:d}".format(int(CurrentValue), int(CurrentValue))
                                lcd_gcode = "M117 Jerk X{:d} Y{:d}".format(int(CurrentValue), int(CurrentValue))
                            if  (Instruction=='junction'):
                                Command = "M205 J{:.3f}".format(float(CurrentValue))
                                lcd_gcode = "M117 Junction J{:.3f}".format(float(CurrentValue))
                            if (Instruction=='marlinadv'):
                                Command = "M900 K{:.3f}".format(float(CurrentValue))
                                lcd_gcode = "M117 Linear Advance K{:.3f}".format(float(CurrentValue))
                            if (Instruction=='marlinadv2'):
                                Command = "M493 K{:.6f}".format(float(CurrentValue)/1000)
                                lcd_gcode = "M117 Linear Advance K{:.3f}".format(float(CurrentValue))
                            if  (Instruction=='rrfpresure'):
                                Command = "M572 D0 S{:.3f}".format(float(CurrentValue))
                                lcd_gcode = "M117 Pressure Advance S{:.3f}".format(float(CurrentValue)) 
                                
                            lines.insert(line_index + 1, ";TYPE:CUSTOM VALUE")
                            lines.insert(line_index + 2, Command)
                            if UseLcd == True :               
                               lines.insert(line_index + 3, lcd_gcode)                                              
            
            # Logger.log('d', 'layer_index : {}'.format(layer_index))
            if  (Instruction=='speed') and  (layer_index==max_layer+1) :
                line_index = len(lines)
                # Logger.log('d', 'line_index : {}'.format(line_index))
                lines.insert(line_index, "M220 R\n")
                
            result = "\n".join(lines)
            data[layer_index] = result
        
        return data
