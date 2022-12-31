from .BaseCamera import BaseCamera

import cv2

class NetworkCamera(BaseCamera):

    def __init__(self, cameraID):
        super().__init__()
        self.cameraID = cameraID
        self.last_frame = None

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
        
    def verify_network_stream(self):
        """Attempts to receive a frame from network stream"""

        cap = cv2.VideoCapture(self.cameraID)
        if not cap.isOpened():
            return False
        cap.release()
        return True
    
    def initializeCamera(self):
        if self.verify_network_stream():
            self.stream = cv2.VideoCapture(self.cameraID)
            self._running = True
    
    def stopCamera(self):
        self.stream.release()
        self._running = False

    def getCameraID(self):
        return self.cameraID