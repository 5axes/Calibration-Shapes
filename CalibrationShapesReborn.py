# Part of initial code by fieldOfView 2018
# Based on Calibration Shapes by 5@xes 2020-2022
# Reborn edition by Slashee the Cow 2025-

# Version history (Reborn)
# 1.0:    Initial release.
#       - Rebranded
#       - Removed towers and tests that require use of post-processing scripts - AutoTowers Generator does them so much better and asking the user to add a script is a pain.
#       - Removed support for Cura versions below 5.0 to get rid of legacy code

    
# Imports from the python standard library to build the plugin functionality
import os
import sys
import re
import math
import numpy
import trimesh

from typing import Optional, List

from UM.Extension import Extension
from UM.PluginRegistry import PluginRegistry
from UM.Application import Application
from cura.CuraApplication import CuraApplication

from UM.Mesh.MeshData import MeshData, calculateNormalsFromIndexedVertices
from UM.Resources import Resources
from UM.Settings.SettingInstance import SettingInstance
from cura.Scene.CuraSceneNode import CuraSceneNode
from UM.Scene.SceneNode import SceneNode
from UM.Scene.Selection import Selection
from UM.Scene.SceneNodeSettings import SceneNodeSettings
from cura.Scene.SliceableObjectDecorator import SliceableObjectDecorator
from cura.Scene.BuildPlateDecorator import BuildPlateDecorator
from UM.Operations.AddSceneNodeOperation import AddSceneNodeOperation
from UM.Operations.RemoveSceneNodeOperation import RemoveSceneNodeOperation
from UM.Operations.SetTransformOperation import SetTransformOperation

from cura.CuraVersion import CuraVersion  # type: ignore
from UM.Version import Version

from UM.Logger import Logger
from UM.Message import Message

from UM.i18n import i18nCatalog

from PyQt6.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot, QUrl
from PyQt6.QtGui import QDesktopServices

i18n_cura_catalog = i18nCatalog("cura")
i18n_catalog = i18nCatalog("fdmprinter.def.json")
i18n_extrud_catalog = i18nCatalog("fdmextruder.def.json")

# Suggested solution from fieldOfView . in this discussion solved in Cura 4.9
# https://github.com/5axes/Calibration-Shapes/issues/1
# Cura are able to find the scripts from inside the plugin folder if the scripts are into a folder named resources
Resources.addSearchPath(
    os.path.join(os.path.abspath(os.path.dirname(__file__)),'resources')
)  # Plugin translation file import

catalog = i18nCatalog("calibration")

if catalog.hasTranslationLoaded():
    Logger.log("i", "Calibration Shapes Reborn Plugin translation loaded!")

#This class is the extension and doubles as QObject to manage the qml    
class CalibrationShapesReborn(QObject, Extension):
    #Create an api
    from cura.CuraApplication import CuraApplication
    api = CuraApplication.getInstance().getCuraAPI()
    
    # The QT signal, which signals an update for user information text
    userInfoTextChanged = pyqtSignal()
    userSizeChanged = pyqtSignal()
    
    def __init__(self, parent = None) -> None:
        QObject.__init__(self, parent)
        Extension.__init__(self)
        
        
        # set the preferences to store the default value
        self._preferences = CuraApplication.getInstance().getPreferences()
        self._preferences.addPreference("calibrationshapesreborn/size", 20)
        
        # convert as float to avoid further issue
        self._size = float(self._preferences.getValue("calibrationshapesreborn/size"))       
 
        self.Major=1
        self.Minor=0

        # Logger.log('d', "Info Version CuraVersion --> " + str(Version(CuraVersion)))
        Logger.log('d', "Info CuraVersion --> " + str(CuraVersion))
        
        # Test version for Cura Master
        # https://github.com/smartavionics/Cura
        if "master" in CuraVersion :
            self.Major=4
            self.Minor=20
        else:
            try:
                self.Major = int(CuraVersion.split(".")[0])
                self.Minor = int(CuraVersion.split(".")[1])
            except:
                pass
 

        self._qml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'qml', "CalibrationShapesReborn.qml")
        
        self._controller = CuraApplication.getInstance().getController()
        self._message = None
        
        self.setMenuName(catalog.i18nc("@item:inmenu", "Calibration Shapes"))
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a cube"), self.addCube)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a cylinder"), self.addCylinder)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a sphere"), self.addSphere)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a tube"), self.addTube)
        self.addMenuItem("", lambda: None)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a Calibration Cube"), self.addCalibrationCube)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a Layer Adhesion Test"), self.addLayerAdhesion)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a Retract Test"), self.addRetractTest)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a XY Calibration Test"), self.addXYCalibration)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a Dimensional Accuracy Test"), self.addDimensionalTest)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a Tolerance Test"), self.addTolerance)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a Hole Test"), self.addHoleTest)
        
        # self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a Junction Deviation Tower"), self.addJunctionDeviationTower)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a Bridge Test"), self.addBridgeTest)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a Thin Wall Test"), self.addThinWall)
        # self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a Thin Wall Test Cura 5.0"), self.addThinWall2)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add an Overhang Test"), self.addOverhangTest)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a Flow Test"), self.addFlowTest)
        
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a Support Test"), self.addSupportTest)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a Lithophane Test"), self.addLithophaneTest)
        
        # self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a MultiCube Calibration"), self.addMultiCube)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a Bed Level Calibration"), self.addBedLevelCalibration)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a Backlash Test"), self.addBacklashTest)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a Linear/Pressure Adv Tower"), self.addPressureAdvTower)
        self.addMenuItem("  ", lambda: None)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a Cube bi-color"), self.addCubeBiColor)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a Bi-Color Calibration Cube"), self.addHollowCalibrationCube)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add an Extruder Offset Calibration Part"), self.addExtruderOffsetCalibration)        
        self.addMenuItem("   ", lambda: None)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Set default size"), self.defaultSize)
  
        #Initialize variables
        self.userText = ""
        self._continueDialog = None


    # Define the default value pour the standard element
    def defaultSize(self) -> None:
 
        if self._continueDialog is None:
            self._continueDialog = self._createDialogue()
        self._continueDialog.show()
        #self.userSizeChanged.emit()

    #====User Input=====================================================================================================
    @pyqtProperty(str, notify= userSizeChanged)
    def sizeInput(self):
        return str(self._size)
        
    #The QT property, which is computed on demand from our userInfoText when the appropriate signal is emitted
    @pyqtProperty(str, notify= userInfoTextChanged)
    def userInfoText(self):
        return self.userText

    #This method builds the dialog from the qml file and registers this class
    #as the manager variable
    def _createDialogue(self):
        #qml_file_path = os.path.join(PluginRegistry.getInstance().getPluginPath(self.getPluginId()), "CalibrationShapes.qml")
        #Logger.log('d', 'Qml_path : ' + str(self._qml_path)) 
        component_with_context = Application.getInstance().createQmlComponent(self._qml_path, {"manager": self})
        return component_with_context

    def getSize(self) -> float:
    
        return self._size
        
    # is called when a key gets released in the size inputField (twice for some reason)
    @pyqtSlot(str)
    def sizeEntered(self, text):
        # Is the textfield empty ? Don't show a message then
        if text =="":
            #self.writeToLog("size-Textfield: Empty")
            self.userMessage("", "ok")
            return

        #Convert commas to points
        text = text.replace(",",".")

        #self.writeToLog("Size-Textfield: read value "+text)

        #Is the entered Text a number?
        try:
            float(text)
        except ValueError:
            self.userMessage(catalog.i18nc("@info:error", "Entered size invalid: ") + text,"wrong")
            return
        self._size = float(text)

        #Check if positive
        if self._size <= 0:
            self.userMessage(catalog.i18nc("@info:error", "Size value must be positive !"),"wrong")
            self._size = 20
            return

        self.writeToLog("Set calibrationshapesreborn/size printFromHeight to : " + text)
        self._preferences.setValue("calibrationshapesreborn/size", self._size)
        
        #clear the message Field
        self.userMessage("", "ok")
 
    #===== Text Output ===================================================================================================
    #writes the message to the log, includes timestamp, length is fixed
    def writeToLog(self, str):
        Logger.log("d", "Debug Calibration Shapes Reborn = %s", str)

    #Sends an user message to the Info Textfield, color depends on status (prioritized feedback)
    # Red wrong for Errors and Warnings
    # Grey for details and messages that aren't interesting for advanced users
    def userMessage(self, message, status):
        if status is "wrong":
            #Red
            self.userText = "<font color='#a00000'>" + message + "</font>"
        else:
            # Grey
            if status is "ok":
                self.userText = "<font color='#9fa4b0'>" + message + "</font>"
            else:
                self.writeToLog("Error: Invalid status: "+status)
                return
        #self.writeToLog("User Message: "+message)
        self.userInfoTextChanged.emit()
          
    def gotoHelp(self) -> None:
        QDesktopServices.openUrl(QUrl("https://github.com/Slashee-the-Cow/CalibrationShapesReborn"))


    def addBedLevelCalibration(self) -> None:
        # Get the build plate Size
        machine_manager = CuraApplication.getInstance().getMachineManager()        
        stack = CuraApplication.getInstance().getGlobalContainerStack()

        global_stack = machine_manager.activeMachine
        m_w=global_stack.getProperty("machine_width", "value") 
        m_d=global_stack.getProperty("machine_depth", "value")
        if (m_w/m_d)>1.15 or (m_d/m_w)>1.15:
            factor_w=round((m_w/100), 1)
            factor_d=round((m_d/100), 1) 
        else:
            factor_w=int(m_w/100)
            factor_d=int(m_d/100)          
        
        # Logger.log("d", "factor_w= %.1f", factor_w)
        # Logger.log("d", "factor_d= %.1f", factor_d)
        
        model_definition_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "ParametricBedLevel.stl")
        mesh = trimesh.load(model_definition_path)
        origin = [0, 0, 0]
        DirX = [1, 0, 0]
        DirY = [0, 1, 0]
        # DirZ = [0, 0, 1]
        mesh.apply_transform(trimesh.transformations.scale_matrix(factor_w, origin, DirX))
        mesh.apply_transform(trimesh.transformations.scale_matrix(factor_d, origin, DirY))
        # addShape
        self._addShape("BedLevelCalibration",self._toMeshData(mesh))       
            
    def _registerShapeStl(self, mesh_name, mesh_filename=None, **kwargs) -> None:
        if mesh_filename is None:
            mesh_filename = mesh_name + ".stl"
        
        model_definition_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", mesh_filename)
        mesh =  trimesh.load(model_definition_path)
        
        # addShape
        self._addShape(mesh_name,self._toMeshData(mesh), **kwargs)
 
    # Source code from MeshTools Plugin 
    # Copyright (c) 2020 Aldo Hoeben / fieldOfView
    def _getAllSelectedNodes(self) -> List[SceneNode]:
        selection = Selection.getAllSelectedObjects()[:]
        if selection:
            deep_selection = []  # type: List[SceneNode]
            for selected_node in selection:
                if selected_node.hasChildren():
                    deep_selection = deep_selection + selected_node.getAllChildren()
                if selected_node.getMeshData() != None:
                    deep_selection.append(selected_node)
            if deep_selection:
                return deep_selection

        Message(catalog.i18nc("@info:status", "Please select one or more models first"))

        return []
 
    def _sliceableNodes(self):
        # Add all sliceable scene nodes to check
        scene = Application.getInstance().getController().getScene()
        for node in DepthFirstIterator(scene.getRoot()):
            if node.callDecoration("isSliceable"):
                yield node
                       
    def addCalibrationCube(self) -> None:
        self._registerShapeStl("CalibrationCube")

    def addMultiCube(self) -> None:
        self._registerShapeStl("MultiCube")

    def addJunctionDeviationTower(self) -> None:
        self._registerShapeStl("JunctionDeviationTower")
        
    def addRetractTest(self) -> None:
        self._registerShapeStl("RetractTest")

    def addLayerAdhesion(self) -> None:
        self._registerShapeStl("LayerAdhesion")    
    
    def addXYCalibration(self) -> None:
        self._registerShapeStl("xy_calibration")
        
    def addBridgeTest(self) -> None:
        self._registerShapeStl("BridgeTest")

    def addThinWall(self) -> None:
        self._registerShapeStl("ThinWall")
 
    def addThinWall2(self) -> None:
        self._registerShapeStl("ThinWallRought")

    def addBacklashTest(self) -> None:
        self._registerShapeStl("Backlash")  
  
    def addOverhangTest(self) -> None:
        self._registerShapeStl("OverhangTest", "Overhang.stl")
 
    def addFlowTest(self) -> None:
        self._registerShapeStl("FlowTest", "FlowTest.stl")
        
    def addHoleTest(self) -> None:
        self._registerShapeStl("FlowTest", "HoleTest.stl")

    def addTolerance(self) -> None:
        self._registerShapeStl("Tolerance")

    def addLithophaneTest(self) -> None:
        self._registerShapeStl("Lithophane")
        
    # Dotdash addition 2 - Support test
    def addSupportTest(self) -> None:
        self._registerShapeStl("SupportTest")

    # Dimensional Accuracy Test
    def addDimensionalTest(self) -> None:
        self._registerShapeStl("DimensionalAccuracyTest")
        
    # Dotdash addition - for Linear/Pressure advance
    def addPressureAdvTower(self) -> None:
        self._registerShapeStl("PressureAdv", "PressureAdvTower.stl")

    #-----------------------------
    #   Dual Extruder 
    #----------------------------- 
    def addCubeBiColor(self) -> None:
        self._registerShapeStl("CubeBiColorExt1", "CubeBiColorWhite.stl", ext_pos=1)
        self._registerShapeStl("CubeBiColorExt2", "CubeBiColorRed.stl", ext_pos=2)

    def addHollowCalibrationCube(self) -> None:
        self._registerShapeStl("CubeBiColorExt", "HollowCalibrationCube.stl", ext_pos=1)
        self._registerShapeStl("CubeBiColorInt", "HollowCenterCube.stl", ext_pos=2)
        
    def addExtruderOffsetCalibration(self) -> None:
        self._registerShapeStl("CalibrationMultiExtruder1", "nozzle-to-nozzle-xy-offset-calibration-pattern-a.stl", ext_pos=1)
        self._registerShapeStl("CalibrationMultiExtruder1", "nozzle-to-nozzle-xy-offset-calibration-pattern-b.stl", ext_pos=2)

    #-----------------------------
    #   Standard Geometry  
    #-----------------------------    
    # Origin, xaxis, yaxis, zaxis = [0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]
    # S = trimesh.transformations.scale_matrix(20, origin)
    # xaxis = [1, 0, 0]
    # Rx = trimesh.transformations.rotation_matrix(math.radians(90), xaxis)    
    def addCube(self) -> None:
        Tz = trimesh.transformations.translation_matrix([0, 0, self._size*0.5])
        self._addShape("Cube",self._toMeshData(trimesh.creation.box(extents = [self._size, self._size, self._size], transform = Tz )))
        
    def addCylinder(self) -> None:
        mesh = trimesh.creation.cylinder(radius = self._size / 2, height = self._size, sections=90)
        mesh.apply_transform(trimesh.transformations.translation_matrix([0, 0, self._size*0.5]))
        self._addShape("Cylinder",self._toMeshData(mesh))

    def addTube(self) -> None:
        mesh = trimesh.creation.annulus(r_min = self._size / 4, r_max = self._size / 2, height = self._size, sections = 90)
        mesh.apply_transform(trimesh.transformations.translation_matrix([0, 0, self._size*0.5]))
        self._addShape("Tube",self._toMeshData(mesh))
        
    # Sphere are not very usefull but I leave it for the moment    
    def addSphere(self) -> None:
        # subdivisions (int) – How many times to subdivide the mesh. Note that the number of faces will grow as function of 4 ** subdivisions, so you probably want to keep this under ~5
        mesh = trimesh.creation.icosphere(subdivisions=4,radius = self._size / 2,)
        mesh.apply_transform(trimesh.transformations.translation_matrix([0, 0, self._size*0.5]))
        self._addShape("Sphere",self._toMeshData(mesh))

    #----------------------------------------------------------
    # Check retraction_enable must be True
    #----------------------------------------------------------   
    def _checkRetract(self, val):
        # Logger.log("d", "In checkRetract = %s", str(val))
        global_container_stack = CuraApplication.getInstance().getGlobalContainerStack() 
        extruder = global_container_stack.extruderList[0]
        extruder_stack = CuraApplication.getInstance().getExtruderManager().getActiveExtruderStacks()[0]
        retraction_e = float(extruder.getProperty("retraction_enable", "value"))
        
        if retraction_e !=  val :
            key="retraction_enable"
            definition_key=key + " label"
            untranslated_label=extruder_stack.getProperty(key,"label")
            translated_label=i18n_catalog.i18nc(definition_key, untranslated_label)
            Message(text = catalog.i18nc("@info:label","! Modification ! in the current profile of : ") + translated_label + catalog.i18nc("@info:label","\nNew value :") + " %s" % (str(val)), title = catalog.i18nc("@info:title", "Warning ! Calibration Shapes"), message_type = Message.MessageType.WARNING).show()
            
            # Define retraction_enable
            extruder.setProperty("retraction_enable", "value", True)
        
        
        retraction_amount = extruder.getProperty("retraction_amount", "value")
        Logger.log("d", "In checkRetract retraction_amount = %s", str(retraction_amount))
        
        if  (retraction_amount == 0) :
            key="retraction_amount"
            definition_key=key + " label"
            untranslated_label=extruder_stack.getProperty(key,"label")
            translated_label=i18n_catalog.i18nc(definition_key, untranslated_label)
            Message(text = catalog.i18nc("@info:label", "! Modification ! in the current profile of : ") + translated_label + catalog.i18nc("@info:label","\nNew value :") + " %s" % (str(1.0)), title = catalog.i18nc("@info:title", "Warning ! Calibration Shapes"), message_type = Message.MessageType.WARNING).show()
               
            # Define retraction_amount
            extruder.setProperty("retraction_amount", "value", 1.0)
            
    #----------------------------------------------------------
    # Check adaptive_layer_height_enabled must be False
    #----------------------------------------------------------   
    def _checkAdaptativ(self, val):
        # Logger.log("d", "In checkAdaptativ = %s", str(val))
        # Fix some settings in Cura to get a better result
        global_container_stack = CuraApplication.getInstance().getGlobalContainerStack()
        extruder_stack = CuraApplication.getInstance().getExtruderManager().getActiveExtruderStacks()[0]        
        adaptive_layer = global_container_stack.getProperty("adaptive_layer_height_enabled", "value")
        extruder = global_container_stack.extruderList[0]
        
        if adaptive_layer !=  val :
            key="adaptive_layer_height_enabled"
            definition_key=key + " label"
            untranslated_label=extruder_stack.getProperty(key,"label")
            translated_label=i18n_catalog.i18nc(definition_key, untranslated_label)  
            Message(text = catalog.i18nc("@info:label", "! Modification ! in the current profile of : ") + translated_label + catalog.i18nc("@info:label","\nNew value :") + " %s" % (str(val)), title = catalog.i18nc("@info:title", "Warning ! Calibration Shapes"), message_type = Message.MessageType.WARNING).show()
            # Define adaptive_layer
            global_container_stack.setProperty("adaptive_layer_height_enabled", "value", False)
 
    #--------------------------------------------------------------------------  
    # Check meshfix_union_all_remove_holes Set to true if nozzle_size > 0.4
    #--------------------------------------------------------------------------    
    def _checkAllRemoveHoles(self, val)-> bool:
        global_container_stack = CuraApplication.getInstance().getGlobalContainerStack()
        extruder_stack = CuraApplication.getInstance().getExtruderManager().getActiveExtruderStacks()[0]        
        extruder = global_container_stack.extruderList[0]
        _Remove = False
        
        nozzle_size = float(extruder.getProperty("machine_nozzle_size", "value"))
        remove_holes = extruder.getProperty("meshfix_union_all_remove_holes", "value")
        # Logger.log("d", "In checkAdaptativ nozzle_size = %s", str(nozzle_size))
        # Logger.log("d", "In checkAdaptativ remove_holes = %s", str(remove_holes))
        
        if (nozzle_size > 0.4) and (remove_holes == False) :
            _Remove = True
            key="meshfix_union_all_remove_holes"
            definition_key=key + " label"
            untranslated_label=extruder_stack.getProperty(key,"label")
            translated_label=i18n_catalog.i18nc(definition_key, untranslated_label)  
            Message(text = catalog.i18nc("@info:label","Individual definition for the calibration part of : ") + translated_label + catalog.i18nc("@info:label","\n(machine_nozzle_size>0.4)\nSet value :") + " %s" % (str(True)), title = catalog.i18nc("@info:title", "Information ! Calibration Shapes"), message_type = Message.MessageType.POSITIVE).show()
                
            # Define adaptive_layer
            # extruder.setProperty("meshfix_union_all_remove_holes", "value", True) 
        return _Remove
        
    #--------------------------------------------------------------
    # Check fill_outline_gaps (Print Thin Walls V5.0) must be True
    #--------------------------------------------------------------   
    def _checkThinWalls(self, val)-> bool:
        # Logger.log("d", "In checkThinWalls = %s", str(val))
        # Fix some settings in Cura to get a better result
        global_container_stack = CuraApplication.getInstance().getGlobalContainerStack() 
        extruder_stack = CuraApplication.getInstance().getExtruderManager().getActiveExtruderStacks()[0] 
        thin_wall = global_container_stack.getProperty("fill_outline_gaps", "value")
        
        if thin_wall !=  val :
            key="fill_outline_gaps"
            definition_key=key + " label"
            untranslated_label=extruder_stack.getProperty(key,"label")
            translated_label=i18n_catalog.i18nc(definition_key, untranslated_label)            
            Message(text = catalog.i18nc("@info:label","Individual definition for the calibration part of : ") + translated_label + catalog.i18nc("@info:label","\nSet value :") + " %s" % (str(val)), title = catalog.i18nc("@info:title", "Information ! Calibration Shapes"), message_type = Message.MessageType.POSITIVE).show()
            
            thin_wall =  val
            # global_container_stack.setProperty("fill_outline_gaps", "value", val)
           
        return thin_wall
        
    #----------------------------------------------------------
    # Check fill_perimeter_gaps (Fill Gaps Between Walls) must be "nowhere"
    #----------------------------------------------------------   
    def _checkFill_Perimeter_Gaps(self, val):
        # Logger.log("d", "In checkAdaptativ = %s", str(val))
        # Fix some settings in Cura to get a better result
        global_container_stack = CuraApplication.getInstance().getGlobalContainerStack()
        extruder_stack = CuraApplication.getInstance().getExtruderManager().getActiveExtruderStacks()[0]         
        fill_perimeter_gaps = global_container_stack.getProperty("fill_perimeter_gaps", "value")
        
        if fill_perimeter_gaps !=  val :
            key="fill_perimeter_gaps"
            definition_key=key + " label"
            untranslated_label=extruder_stack.getProperty(key,"label")
            translated_label=i18n_catalog.i18nc(definition_key, untranslated_label) 
            Message(text = catalog.i18nc("@info:label","! Modification ! in the current profile of : ") + translated_label + atalog.i18nc("@info:label","\nNew value :") + " %s" % (str(val)), title = catalog.i18nc("@info:title", "Warning ! Calibration Shapes"), message_type = Message.MessageType.WARNING).show()
            # Define adaptive_layer
            global_container_stack.setProperty("fill_perimeter_gaps", "value", val)
        
        extruder = global_container_stack.extruderList[0]
        fill_perimeter_gaps = extruder.getProperty("fill_perimeter_gaps", "value")
        
        if fill_perimeter_gaps !=  val :
            Message(text = catalog.i18nc("@info:label","! Modification ! for the extruder definition of : ") + translated_label + atalog.i18nc("@info:label","\nNew value :") + " %s" % (str(val)), title = catalog.i18nc("@info:title", "Warning ! Calibration Shapes"), message_type = Message.MessageType.WARNING).show()
            # Define adaptive_layer
            extruder.setProperty("fill_perimeter_gaps", "value", val)
            
    #----------------------------------------
    # Initial Source code from  fieldOfView
    #----------------------------------------  
    def _toMeshData(self, tri_node: trimesh.base.Trimesh) -> MeshData:
        # Rotate the part to laydown on the build plate
        # Modification from 5@xes
        tri_node.apply_transform(trimesh.transformations.rotation_matrix(math.radians(90), [-1, 0, 0]))
        tri_faces = tri_node.faces
        tri_vertices = tri_node.vertices

        # Following Source code from  fieldOfView
        # https://github.com/fieldOfView/Cura-SimpleShapes/blob/bac9133a2ddfbf1ca6a3c27aca1cfdd26e847221/SimpleShapes.py#L45
        indices = []
        vertices = []

        index_count = 0
        face_count = 0
        for tri_face in tri_faces:
            face = []
            for tri_index in tri_face:
                vertices.append(tri_vertices[tri_index])
                face.append(index_count)
                index_count += 1
            indices.append(face)
            face_count += 1

        vertices = numpy.asarray(vertices, dtype=numpy.float32)
        indices = numpy.asarray(indices, dtype=numpy.int32)
        normals = calculateNormalsFromIndexedVertices(vertices, indices, face_count)

        mesh_data = MeshData(vertices=vertices, indices=indices, normals=normals)

        return mesh_data        
        
    # Initial Source code from  fieldOfView
    # https://github.com/fieldOfView/Cura-SimpleShapes/blob/bac9133a2ddfbf1ca6a3c27aca1cfdd26e847221/SimpleShapes.py#L70
    def _addShape(self, mesh_name, mesh_data: MeshData, ext_pos = 0 , hole = False , thin = False , mode = "" ) -> None:
        application = CuraApplication.getInstance()
        global_stack = application.getGlobalContainerStack()
        if not global_stack:
            return

        node = CuraSceneNode()

        node.setMeshData(mesh_data)
        node.setSelectable(True)
        if len(mesh_name)==0:
            node.setName("TestPart" + str(id(mesh_data)))
        else:
            node.setName(str(mesh_name))

        scene = self._controller.getScene()
        op = AddSceneNodeOperation(node, scene.getRoot())
        op.push()

        extruder_stack = application.getExtruderManager().getActiveExtruderStacks() 
        
        extruder_nr=len(extruder_stack)
        # Logger.log("d", "extruder_nr= %d", extruder_nr)
        # default_extruder_position  : <class 'str'>
        if ext_pos>0 and ext_pos<=extruder_nr :
            default_extruder_position = int(ext_pos-1)
        else :
            default_extruder_position = int(application.getMachineManager().defaultExtruderPosition)
        # Logger.log("d", "default_extruder_position= %s", type(default_extruder_position))
        default_extruder_id = extruder_stack[default_extruder_position].getId()
        # Logger.log("d", "default_extruder_id= %s", default_extruder_id)
        node.callDecoration("setActiveExtruder", default_extruder_id)
 
        stack = node.callDecoration("getStack") # created by SettingOverrideDecorator that is automatically added to CuraSceneNode
        settings = stack.getTop()
        # Remove All Holes
        if hole :
            definition = stack.getSettingDefinition("meshfix_union_all_remove_holes")
            new_instance = SettingInstance(definition, settings)
            new_instance.setProperty("value", True)
            new_instance.resetState()  # Ensure that the state is not seen as a user state.
            settings.addInstance(new_instance) 
        # Print Thin Walls    
        if thin :
            definition = stack.getSettingDefinition("fill_outline_gaps")
            new_instance = SettingInstance(definition, settings)
            new_instance.setProperty("value", True)
            new_instance.resetState()  # Ensure that the state is not seen as a user state.
            settings.addInstance(new_instance)
 
        if len(mode) :
            definition = stack.getSettingDefinition("magic_mesh_surface_mode")
            new_instance = SettingInstance(definition, settings)
            new_instance.setProperty("value", mode)
            new_instance.resetState()  # Ensure that the state is not seen as a user state.
            settings.addInstance(new_instance)

        node.setSetting(SceneNodeSettings.AutoDropDown, True)
            
        active_build_plate = application.getMultiBuildPlateModel().activeBuildPlate
        node.addDecorator(BuildPlateDecorator(active_build_plate))

        node.addDecorator(SliceableObjectDecorator())

        application.getController().getScene().sceneChanged.emit(node)