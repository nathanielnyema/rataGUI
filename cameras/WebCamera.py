from cameras import BaseCamera

import cv2
import numpy as np


class WebCamera(BaseCamera):
    def __init__(self, cameraID):
        super().__init__()
        self.cameraID = cameraID
        self.last_frame = None

    @staticmethod
    def getAvailableCameras(search = 2):
        '''Returns list of all available web cameras'''
        cameras = []
        for i in range(search):
            cam = WebCamera(i)
            cam.initializeCamera()
            # Try to read a couple frames
            for _ in range(2):
                if cam.readCamera()[0]:
                    cameras.append(cam)
                    break
            cam.stopCamera()
        return cameras

    def initializeCamera(self):
        self.stream = cv2.VideoCapture(self.cameraID)
        self._running = True

    def readCamera(self, colorspace="BGR"):
        ret, frame = self.stream.read()
        if ret:
            self.frames_acquired += 1
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
        try:
            self.stream.release()
            self._running = False
            return True
        except Exception as err:
            print(err)
            return False
    
    def isOpened(self):
        return self.stream != None and self.stream.isOpened()

    def getName(self):
        return "Web Camera " + str(self.cameraID)
