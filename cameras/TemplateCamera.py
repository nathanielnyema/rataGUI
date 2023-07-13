from cameras import BaseCamera

import cv2

class TemplateCamera(BaseCamera):

    @staticmethod
    def getAvailableCameras():
        # Return list of available camera objects for custom model
        return []

    def __init__(self, cameraID):
        super().__init__()
        self.cameraID = cameraID
        self.last_frame = None

    def initializeCamera(self, config = dict()):
        cap = cv2.VideoCapture(self.cameraID)
        if cap.isOpened():
            self._running = True
            self._stream = cap
            return True
        else:
            self._running = False
            cap.release()
            return False

    def readCamera(self, colorspace="RGB"):
        ret, frame = self._stream.read()
        if ret:
            self.frames_acquired += 1
            match colorspace:
                case "RGB":
                    self.last_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                case "HSV": 
                    self.last_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                case "GRAY":
                    self.last_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                case other:
                    self.last_frame = frame
        
        return ret, self.last_frame
    
    def closeCamera(self):
        if self._stream is not None:
            self._stream.release()

        self._running = False