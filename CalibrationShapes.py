#-----------------------------------------------------------------------------------
# Part of the initial source code for primitive Shape (c) 2018 fieldOfView
# The CalibrationShapes plugin is released under the terms of the AGPLv3 or higher.
# Modifications 5@xes 2020-2021
#-----------------------------------------------------------------------------------
# V1.04    : https://github.com/5axes/Calibration-Shapes/issues/4
#          : https://github.com/5axes/Calibration-Shapes/issues/3
# V1.0.8   : Add the Help function 2 test part (MultiCube and PETG Tower) 
# V1.0.9   : Bed Level
# V1.0.10  : Change default Name
# V1.1.0   : Add MultiExtruder Part https://github.com/5axes/Calibration-Shapes/issues/15
#          : Part Rotation added to the _toMeshData subroutine
#          : Stl File can no be also Drag & Drop on the Build Plate
# V1.1.1   : Stl File converted into binary STL format
#          : Try to set directly a different Extruder in case of MultiExtruder part
# V1.1.2   : Add a Hole Test
# V1.1.3   : Remove for the moment Junction deviation tower... waiting for User feedback
# V1.2.0   : Linear/Pressure Adv Tower by dotdash32 https://github.com/dotdash32
# V1.2.1   : Change CopyScript condition to fileSize
# V1.2.2   : Error correction
# V1.2.3   : Change error message
# V1.2.4   : Check Adaptive Layers options for Tower
# V1.2.5   : Set meshfix_union_all_remove_holes for Tower if Nozzle_Size > 0.4
# V1.2.6   : Retract tower script modification (Version 1.4)
#          : https://github.com/5axes/Calibration-Shapes/issues/28
# V1.3.0   : Test the version: since 4.9 the followin bug is solved .. Don't need to use the function CopyScript
#          : https://github.com/5axes/Calibration-Shapes/issues/1
#
#-----------------------------------------------------------------------------------
from PyQt5.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot, QUrl
from PyQt5.QtGui import QDesktopServices

# Imports from the python standard library to build the plugin functionality
import os
import re
import math
import numpy
import trimesh
import shutil
import platform
import sys
import html

from shutil import copyfile

from UM.Extension import Extension
from UM.PluginRegistry import PluginRegistry
from UM.Application import Application
from cura.CuraApplication import CuraApplication

from UM.Mesh.MeshData import MeshData, calculateNormalsFromIndexedVertices
from UM.Resources import Resources
from UM.Operations.AddSceneNodeOperation import AddSceneNodeOperation
from cura.Scene.CuraSceneNode import CuraSceneNode
from cura.Scene.SliceableObjectDecorator import SliceableObjectDecorator
from cura.Scene.BuildPlateDecorator import BuildPlateDecorator

from cura.CuraVersion import CuraVersion  # type: ignore
from UM.Version import Version

from UM.Logger import Logger
from UM.Message import Message

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

#This class is the extension and doubles as QObject to manage the qml    
class CalibrationShapes(QObject, Extension):
    #Create an api
    from cura.CuraApplication import CuraApplication
    api = CuraApplication.getInstance().getCuraAPI()
    
    # The QT signal, which signals an update for user information text
    userInfoTextChanged = pyqtSignal()
    userSizeChanged = pyqtSignal()
    
    def __init__(self, parent = None) -> None:
        QObject.__init__(self, parent)
        Extension.__init__(self)
        
        #Inzialize varables
        self.userText = ""
        self._continueDialog = None
        
        # set the preferences to store the default value
        self._preferences = CuraApplication.getInstance().getPreferences()
        self._preferences.addPreference("calibrationshapes/size", 20)
        
        # convert as float to avoid further issue
        self._size = float(self._preferences.getValue("calibrationshapes/size"))
        
        # Suggested solution from fieldOfView . Unfortunatly it doesn't works 
        # https://github.com/5axes/Calibration-Shapes/issues/1
        # Cura should be able to find the scripts from inside the plugin folder if the scripts are into a folder named resources
        Resources.addSearchPath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources"))
 
        self.Major=1
        self.Minor=0

        # Logger.log('d', "Info Version CuraVersion --> " + str(Version(CuraVersion)))
        Logger.log('d', "Info CuraVersion --> " + str(CuraVersion))
        
        # Test version for futur release 4.9
        if "master" in CuraVersion or "beta" in CuraVersion or "BETA" in CuraVersion:
            # Master is always a developement version.
            self.Major=4
            self.Minor=9

        else:
            try:
                self.Major = int(CuraVersion.split(".")[0])
                self.Minor = int(CuraVersion.split(".")[1])
            except:
                pass
                
        self._controller = CuraApplication.getInstance().getController()
        self._message = None
        
        self.setMenuName(catalog.i18nc("@item:inmenu", "Part for calibration"))
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a cube"), self.addCube)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a cylinder"), self.addCylinder)
        # self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a sphere"), self.addSphere)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a tube"), self.addTube)
        self.addMenuItem("", lambda: None)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a Calibration Cube"), self.addCalibrationCube)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a PLA TempTower"), self.addPLATempTower)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a PLA TempTower 190°C"), self.addPLATempTowerSimple)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a PLA+ TempTower"), self.addPLAPlusTempTower)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a PETG TempTower"), self.addPETGTempTower)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add an ABS TempTower"), self.addABSTempTower)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a Retract Tower"), self.addRetractTower)
        
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a Retract Test"), self.addRetractTest)
        # self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a Junction Deviation Tower"), self.addJunctionDeviationTower)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a Bridge Test"), self.addBridgeTest)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a Thin Wall Test"), self.addThinWall)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add an Overhang Test"), self.addOverhangTest)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a Flow Test"), self.addFlowTest)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a Hole Test"), self.addHoleTest)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a Tolerance Test"), self.addTolerance)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a MultiCube Calibration"), self.addMultiCube)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a Bed Level Calibration"), self.addBedLevelCalibration)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a Linear/Pressure Adv Tower"), self.addPressureAdvTower)
        self.addMenuItem("  ", lambda: None)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a Cube bi-color"), self.addCubeBiColor)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add a Bi-Color Calibration Cube"), self.addHollowCalibrationCube)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Add an Extruder Offset Calibration Part"), self.addExtruderOffsetCalibration)        
        self.addMenuItem("   ", lambda: None)
        if self.Major < 4 or ( self.Major == 4 and self.Minor < 9 ) :
            self.addMenuItem(catalog.i18nc("@item:inmenu", "Copy Scripts"), self.copyScript)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Define default size"), self.defaultSize)
        self.addMenuItem("    ", lambda: None)
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Help"), self.gotoHelp)
  
        #Inzialize varables
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
        qml_file_path = os.path.join(PluginRegistry.getInstance().getPluginPath(self.getPluginId()), "CalibrationShapes.qml")
        component_with_context = Application.getInstance().createQmlComponent(qml_file_path, {"manager": self})
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
            self.userMessage("Entered size invalid: " + text,"wrong")
            return
        self._size = float(text)

        #Check if positive
        if self._size <= 0:
            self.userMessage("Size value must be positive !","wrong")
            self._size = 20
            return

        self.writeToLog("Set calibrationshapes/size printFromHeight to : " + text)
        self._preferences.setValue("calibrationshapes/size", self._size)
        
        #clear the message Field
        self.userMessage("", "ok")
 
    #===== Text Output ===================================================================================================
    #writes the message to the log, includes timestamp, length is fixed
    def writeToLog(self, str):
        Logger.log("d", "Debug calibration shapes = %s", str)

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
 
    # Copy the scripts to the right directory ( Temporary solution)
    def copyScript(self) -> None:
        File_List = ['RetractTower.py', 'SpeedTower.py', 'TempFanTower.py']
        
        plugPath =  os.path.join(os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources"), "scripts")
        # Logger.log("d", "plugPath= %s", plugPath)
        
        stringMatch = re.split("plugins", plugPath)
        destPath = os.path.join(stringMatch[0], "scripts")
        nbfile=0
        # Copy the script
        for fl in File_List:
            script_definition_path = os.path.join(plugPath, fl)
            dest_definition_path = os.path.join(destPath, fl)
            self.writeToLog("Dest_definition_path = " + dest_definition_path)
            if os.path.isfile(dest_definition_path)==True:
                self.writeToLog("Script_definition_path st_size= " + str(os.stat(script_definition_path).st_size))
                self.writeToLog("Dest_definition_path st_size= " + str(os.stat(dest_definition_path).st_size))
            
            if os.path.isfile(dest_definition_path)==False:
                self.writeToLog("Copy Script_definition_path = " + script_definition_path)
                copyfile(script_definition_path,dest_definition_path)
                nbfile+=1
            # Change condition to File Size definition
            elif os.stat(script_definition_path).st_size > os.stat(dest_definition_path).st_size :
                self.writeToLog("Copy Script_definition_path = " + script_definition_path)
                copyfile(script_definition_path,dest_definition_path)
                nbfile+=1
        
        txt_Message = ""
        if nbfile > 0 :
            txt_Message =  str(nbfile) + " script(s) copied in :\n"
            txt_Message = txt_Message + destPath
            txt_Message = txt_Message + "\nYou must now restart Cura to see the scripts in the postprocessing script list"
        else:
            txt_Message = "Every script are up to date in :\n"
            txt_Message = txt_Message + destPath
          
        self._message = Message(catalog.i18nc("@info:status", txt_Message), title = catalog.i18nc("@title", "Calibration Shapes"))
        self._message.show()
     
    def gotoHelp(self) -> None:
        QDesktopServices.openUrl(QUrl("https://github.com/5axes/Calibration-Shapes/wiki"))

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
            mesh_filename = f"{mesh_name}.stl"
        
        model_definition_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", mesh_filename)
        mesh =  trimesh.load(model_definition_path)
        # addShape
        self._addShape(mesh_name,self._toMeshData(mesh), **kwargs)
        
    def addCalibrationCube(self) -> None:
        self._registerShapeStl("CalibrationCube")

    def addMultiCube(self) -> None:
        self._registerShapeStl("MultiCube")

    def addJunctionDeviationTower(self) -> None:
        self._registerShapeStl("JunctionDeviationTower")
    
    def addPLATempTower(self) -> None:
        self._registerShapeStl("PLATempTower", "TempTowerPLA.stl")
        self._checkAdaptativ(False)

    def addPLATempTowerSimple(self) -> None:
        self._registerShapeStl("PLATempTower", "TempTowerPLA190°C.stl")
        self._checkAdaptativ(False)

    def addPLAPlusTempTower(self) -> None:
        self._registerShapeStl("PLA+TempTower", "TempTowerPLA+.stl")
        self._checkAdaptativ(False)
        
    def addPETGTempTower(self) -> None:
        self._registerShapeStl("PETGTempTower", "TempTowerPETG.stl")
        self._checkAdaptativ(False)
        
    def addABSTempTower(self) -> None:
        self._registerShapeStl("ABSTempTower", "TempTowerABS.stl")
        self._checkAdaptativ(False)

    def addRetractTower(self) -> None:
        self._registerShapeStl("RetractTower")
        self._checkAdaptativ(False)
        
    def addRetractTest(self) -> None:
        self._registerShapeStl("RetractTest")
        
    def addBridgeTest(self) -> None:
        self._registerShapeStl("BridgeTest")

    def addThinWall(self) -> None:
        self._registerShapeStl("ThinWall")
 
    def addOverhangTest(self) -> None:
        self._registerShapeStl("OverhangTest", "Overhang.stl")
 
    def addFlowTest(self) -> None:
        self._registerShapeStl("FlowTest", "FlowTest.stl")

    def addHoleTest(self) -> None:
        self._registerShapeStl("FlowTest", "HoleTest.stl")

    def addTolerance(self) -> None:
        self._registerShapeStl("Tolerance")

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
    # Check adaptive_layer_height_enabled must be False
    #----------------------------------------------------------   
    def _checkAdaptativ(self, val):
        # Logger.log("d", "In checkAdaptativ = %s", str(val))
        # Fix some settings in Cura to get a better result
        global_container_stack = CuraApplication.getInstance().getGlobalContainerStack() 
        adaptive_layer = global_container_stack.getProperty("adaptive_layer_height_enabled", "value")
        extruder = global_container_stack.extruderList[0]
        
        if adaptive_layer !=  val :
            Message(text = "Info modification current profil adaptive_layer_height_enabled\nNew value : %s" % (str(val)), title = catalog.i18nc("@info:title", "Warning ! Calibration Shapes")).show()
            # Define adaptive_layer
            global_container_stack.setProperty("adaptive_layer_height_enabled", "value", False)
        
        nozzle_size = float(extruder.getProperty("machine_nozzle_size", "value"))
        remove_holes = extruder.getProperty("meshfix_union_all_remove_holes", "value")
        # Logger.log("d", "In checkAdaptativ nozzle_size = %s", str(nozzle_size))
        # Logger.log("d", "In checkAdaptativ remove_holes = %s", str(remove_holes))
        
        if (nozzle_size >  0.4) and (remove_holes == False) :
            Message(text = "Info modification current profil meshfix_union_all_remove_holes (machine_nozzle_size>0.4)\nNew value : %s" % (str(True)), title = catalog.i18nc("@info:title", "Warning ! Calibration Shapes")).show()
            # Define adaptive_layer
            extruder.setProperty("meshfix_union_all_remove_holes", "value", True) 
            
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
    def _addShape(self, mesh_name, mesh_data: MeshData, ext_pos = 0 ) -> None:
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

        extruder_nr=len(global_stack.extruders)
        # Logger.log("d", "extruder_nr= %d", extruder_nr)
        # default_extruder_position  : <class 'str'>
        if ext_pos>0 and ext_pos<=extruder_nr :
            default_extruder_position = str(ext_pos-1)
        else :
            default_extruder_position = application.getMachineManager().defaultExtruderPosition
        # Logger.log("d", "default_extruder_position= %s", type(default_extruder_position))
        # default_extruder_id = global_stack.extruders[default_extruder_position].getId()
        default_extruder_id = global_stack.extruders[default_extruder_position].getId()
        # Logger.log("d", "default_extruder_id= %s", default_extruder_id)
        node.callDecoration("setActiveExtruder", default_extruder_id)

        active_build_plate = application.getMultiBuildPlateModel().activeBuildPlate
        node.addDecorator(BuildPlateDecorator(active_build_plate))

        node.addDecorator(SliceableObjectDecorator())

        application.getController().getScene().sceneChanged.emit(node)
        

