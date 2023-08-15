from rataGUI.cameras.BaseCamera import BaseCamera, ConfigManager

import cv2

import logging
logger = logging.getLogger(__name__)


class WebCamera(BaseCamera):

    PROPS = {
        "FPS": 30,
    }

    @staticmethod
    def getAvailableCameras(search = 1):
        '''Returns list of all available web cameras'''
        cameras = []
        for i in range(search):
            cam = WebCamera(i)
            cam.initializeCamera(ConfigManager())
            # Try to read a couple frames
            for _ in range(2):
                if cam.readCamera()[0]:
                    cameras.append(cam)
                    cam.frames_acquired = 0
                    break
            cam.closeCamera()
        return cameras


    def __init__(self, cameraID):
        super().__init__(cameraID)
        self.last_frame = None


    def initializeCamera(self, prop_config, plugin_names=[]):
        self._stream = cv2.VideoCapture(self.cameraID)
        self._running = True
        return True

    def readCamera(self, colorspace="RGB"):
        ret, frame = self._stream.read()
        if ret:
            self.frames_acquired += 1
            if colorspace == "BGR":
                self.last_frame = frame
            elif colorspace == "RGB":
                self.last_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            elif colorspace == "GRAY":
                self.last_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            else:
                self.last_frame = frame
        
        return ret, self.last_frame

    def closeCamera(self):
        try:
            self._stream.release()
            self._running = False
            return True
        except Exception as err:
            logger.exception(err)
            return False
    
    def isOpened(self):
        return self._running

    def getDisplayName(self):
        return "Web Camera " + str(self.cameraID)
