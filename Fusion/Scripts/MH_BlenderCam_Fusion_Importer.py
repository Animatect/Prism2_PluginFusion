# coding=utf-8

#################################################################################################
#                                                                                               #
#   Éste script es propiedad de Magic Hammer Studios, se corre en Fusion e importa data,        #
#   (por el momento la cámara seleccionada) que ha sido exportada por medio de otro script      #
#   desde Blender.                                                                              #
#   Para funcionar, éste Script debe estar localizado en el folder:                             #
#   %APPDATA%\Roaming\Blackmagic Design\Fusion\Scripts\Comp                                     #
#                                                                                               #
#################################################################################################

import os
import json, re, math, sys
import os.path as Path

class BlenderCameraImporter():
    def __init__(self) -> None:
        self.param_types = [
        "Number",
        "Clip",
        "Text",
        "Point",
        "FuID",
        "Audio",
        "Gradient",
        "StyledText",
        "Histogram",
        "LookUpTable",
        "ColorCurves",
        "Mesh",
        "Polyline",
        "Extrusion"
    ]

    def import_blender_camera(self, filepath):
        data = self.data_ingestion(filepath)
        self.pro_reload_camera_ainimate(data)

    def data_ingestion(self, filepath):
        recvData = os.path.normpath(filepath)
        if isinstance(recvData, str) and os.path.isfile(recvData):
            with open(recvData, "r") as f:
                data = json.load(f)
            return data
            
    def pro_reload_camera_ainimate(self, camData):
        comp.StartUndo("Set Camera Animation")
        
        camDict = camData['cam_animate_dict']
        camName = camDict["name"]
        camNode = comp.FindTool(camName)

        ####################################################
        ######## CREAMOS O SELECCIONAMOS LA CÁMARA #########
        ####################################################
        if camNode is None:
            camNode = self.create_cam_node(camName)
        else:
            #si ya hay un camnode le quitamos los Keyframes
            self.clearKeyframe(comp, camNode)

        #######################################################
        ########### COPIAMOS LOS VALORES DE BLENDER ###########
        #######################################################
        frame_list = [int(i) for i in camDict["trans_z"]]
        start_frame = min(frame_list)
        end_frame = max(frame_list)
        for num, frame in enumerate(range(start_frame, end_frame+1)):
            self.load_blendercamera_transformations(
                frame, num, camNode, camDict
            )
        if isinstance(camDict["focal_length"], dict):
            frame_list = [int(i) for i in camDict["focal_length"]]
            start_frame = min(frame_list)
            end_frame = max(frame_list)
            for num, frame in enumerate(range(start_frame, end_frame+1)):
                comp.SetAttrs({"COMPN_CurrentTime": frame})
                if num == 0:
                    camNode.FLength = comp.BezierSpline()
                camNode.FLength[comp.CurrentTime] = camDict["focal_length"][str(frame)]
        else:
            camNode.FLength[comp.CurrentTime] = camDict["focal_length"]

        camNode({
            "FilmGate": "User",
            "ResolutionGateFit": "Width",
            "AovType": "Horizontal",
            "PerspNearClip": camDict["clip_start"],
            "PerspFarClip": camDict["clip_end"]
        })

        if camDict["sensor_direction"] == "H":
            camNode({
                "ApertureW": camDict["sensor_value"],
                "ResolutionGateFit": "Width"
            })
        elif camDict["sensor_direction"] == "V":
            camNode({
                "ApertureH": camDict["sensor_value"],
                "ResolutionGateFit": "Height"
            })


        comp.EndUndo(True)
        
    def load_blendercamera_transformations(self, frame, num, camNode, camDict):
        comp.SetAttrs({"COMPN_CurrentTime": frame})
        if num == 0:
            camNode.Transform3DOp.Translate.X = comp.BezierSpline()
        camNode.Transform3DOp.Translate.X[comp.CurrentTime] = camDict["trans_x"][str(frame)]
        if num == 0:
            camNode.Transform3DOp.Translate.Y = comp.BezierSpline()
        camNode.Transform3DOp.Translate.Y[comp.CurrentTime] = camDict["trans_y"][str(frame)]
        if num == 0:
            camNode.Transform3DOp.Translate.Z = comp.BezierSpline()
        camNode.Transform3DOp.Translate.Z[comp.CurrentTime] = camDict["trans_z"][str(frame)]

        if num == 0:
            camNode.Transform3DOp.Rotate.X = comp.BezierSpline()
        camNode.Transform3DOp.Rotate.X[comp.CurrentTime] = camDict["rota_x"][str(frame)]
        if num == 0:
            camNode.Transform3DOp.Rotate.Y = comp.BezierSpline()
        camNode.Transform3DOp.Rotate.Y[comp.CurrentTime] = camDict["rota_y"][str(frame)]
        if num == 0:
            camNode.Transform3DOp.Rotate.Z = comp.BezierSpline()
        camNode.Transform3DOp.Rotate.Z[comp.CurrentTime] = camDict["rota_z"][str(frame)]

    def create_cam_node(self, camName):
            #Agregamos una nueva cámara y le ponemos nombre
        result = comp.AddTool("Camera3D")
        result.SetAttrs({"TOOLS_Name": camName})

        activeNode = comp.ActiveTool
        flow = comp.CurrentFrame.FlowView

            #Tiene un objeto asignado a ActiveNode o no
        if activeNode:
            x, y = flow.GetPosTable(activeNode).values()
            x -= 1.0
        else:
            x, y = [0, 0]

        flow.SetPos(result, x, y)
        return result
        
    def clearKeyframe(self, comp, node):

        comp.StartUndo("Record Start")
        for p in node.GetInputList().values():
            pName = p.Name
            pDataType = p.GetAttrs()["INPS_DataType"]
            if pDataType not in param_types:
                continue
            if p.GetConnectedOutput():
                p.ConnectTo()
        comp.EndUndo(True)

    def pro_radian_to_degrees(self, value):
            degrees = (value * 180) / math.pi
            return degrees


