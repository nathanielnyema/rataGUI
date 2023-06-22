from .BaseCamera import BaseCamera

import cv2

class NetworkCamera(BaseCamera):

    def __init__(self, cameraID):
        super().__init__()
        self.cameraID = cameraID
        # self._initialized = False
        self.last_frame = None

    def initializeCamera(self):
        cap = cv2.VideoCapture(self.cameraID)
        if cap.isOpened():
            self._running = True
            self.stream = cap
            return True
        else:
            self._running = False
            cap.release()
            return False

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
        
        return ret, self.last_frame
    
    def stopCamera(self):
        if self.stream is not None:
            self.stream.release()

        # self._initialized = False
        self._running = False

    def getCameraID(self):
        return self.cameraID