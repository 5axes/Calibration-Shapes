// Import the standard GUI elements from QTQuick
import QtQuick 6.0
import QtQuick.Controls 6.0

// Imports the Uranium GUI elements, which are themed for Cura.
import UM 1.6 as UM

// Imports the Cura GUI elements.
import Cura 1.7 as Cura


// UM.Dialog
// Dialog
Window
{
    id: base
	
	property variant catalog: UM.I18nCatalog { name: "calibrationshapesreborn" }

    title: catalog.i18nc("@title", "Calibration Shapes Reborn")

    color: "#fafafa" //Background color of cura: #fafafa

    // NonModal like that the dialog to block input in the main window
    modality: Qt.NonModal

    // WindowStaysOnTopHint to stay on top
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowCloseButtonHint

    // Setting the dimensions of the dialog window
    width: 200
    height: 60
    minimumWidth: 200
    minimumHeight: 60

    // Position of the window
    x: Screen.width*0.5 - width - 50
    y: 400 

    // Define a Window a border (Red for) and a background color
    Rectangle {
        id: bg_rect
        width: 200
        height: 60
        color: "#fff"
        border.color: "#D22"
        border.width: 3
        radius: 4
    }

    // Connecting our variable to the computed property of the manager
    property string userInfoText: manager.userInfoText
	
	property string sizeInput: manager.sizeInput

    // Button for closing the dialogbox
    Button
    {
        id: close_button
        text: "<font color='#ffffff'>" + "X" + "</font>"
        width: 25
        height: 25

        anchors.top: parent.top
        anchors.topMargin: 18
        anchors.right: parent.right
        anchors.rightMargin: 10

		ToolTip.delay: 2000
		ToolTip.timeout: 1000
		ToolTip.visible: hovered
		ToolTip.text: qsTr("Close this dialog box")
				
		background: Rectangle {
			implicitWidth: 100
			implicitHeight: 25
			radius: 3
			color: "#D22"
		}

        onClicked:
        {
            base.close();
        }
    }


    //Textfield for User Messages
    Text
    {
        id: user_text

        width: 200
        anchors.top: parent.top
        anchors.topMargin: 2
        anchors.left: parent.left
        anchors.leftMargin: 10

        text: userInfoText

        font.family: "Arial"
        font.pointSize: 10
        //The color gets overwritten by the html tags added to the text
        color: "black"

        wrapMode: Text.Wrap
    }
	
    // Label "Size: "
    Label
    {
        id: label_size
        text: catalog.i18nc("@label", "Size:")
        font.family: "Arial"
        font.pointSize: 12
        color: "#131151"

        anchors.top: close_button.top
        anchors.topMargin: 10
        anchors.left: parent.left
        anchors.leftMargin: 10
    }

    //User input of height
    UM.TextFieldWithUnit
    {
        id: size_input
        width: 90
        text: sizeInput
		// "ie. 20.0"

        anchors.top: label_size.top
        anchors.topMargin: -2
        anchors.left: label_size.right
        anchors.leftMargin: 10

		font.family: "Arial"
        font.pointSize: 12
		
		unit: "mm"
		
        // Validate entered value
        Keys.onReturnPressed:
        {
			event.accepted = true
        }

        // Return the new entered value
        Keys.onReleased:
        {
            manager.sizeEntered(size_input.text)
        }
    }

}
