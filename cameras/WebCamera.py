import cv2
import numpy as np

from .BaseCamera import BaseCamera

class WebCamera(BaseCamera):
    def __init__(self, cameraID):
        super().__init__()
        self.cameraID = cameraID
        # self.maxFPS = 0
        self.last_frame = None

    @staticmethod
    def getAllCameras(search = 2):
        '''Returns dictionary of available web cameras'''
        cameras = {}
        for i in range(search):
            cam = WebCamera(i)
            cam.initializeCamera()
            # Try to read a couple frames
            for _ in range(2):
                if cam.readCamera()[0]:
                    cameraName = "Web Camera " + str(i)
                    cameras[cameraName] = cam
                    break
            cam.stopCamera()
        return cameras

    def initializeCamera(self):
        self.stream = cv2.VideoCapture(self.cameraID)
        self._running = True

    def readCamera(self, colorspace="BGR"):
        ret, frame = self.stream.read()
        if ret:
            match colorspace:
                case "RGB":
                    self.last_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                case "HSV": 
                    self.last_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                case "GRAY":
                    self.last_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                case other: # Not necessary
                    self.last_frame = frame
        
        return ret, self.last_frame

    def stopCamera(self):
        self.stream.release()
        self._running = False

    def getCameraID(self):
        return self.cameraID
    
    def isOpened(self):
        return self.stream != None and self.stream.isOpened()
