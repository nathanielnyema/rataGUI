from cameras import BaseCamera

import cv2

class NetworkCamera(BaseCamera):

    @staticmethod
    def getAvailableCameras():
        # Return list of available NetworkCameras for user-specific setup
        return []

    def __init__(self, cameraID):
        super().__init__()
        self.cameraID = cameraID
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

        self._running = False