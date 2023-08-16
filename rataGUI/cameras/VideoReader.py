from rataGUI.cameras.BaseCamera import BaseCamera
from rataGUI.config import num_video_readers

import os
import cv2

import logging
logger = logging.getLogger(__name__)


class VideoReader(BaseCamera):

    DEFAULT_PROPS = {
        "File path": "",
    }

    @staticmethod
    def getAvailableCameras():
        return [VideoReader(f"Video Reader {i+1}") for i in range(num_video_readers)]


    def __init__(self, readerID):
        super().__init__(readerID)
        self.last_frame = None
        self.file_path = ""

    def initializeCamera(self, prop_config, plugin_names=[]):
        self.input_params = {}
        self.output_params = {}
        for prop_name, value in prop_config.as_dict().items():
            if prop_name == "File path":
                self.file_path = os.path.normpath(value)

        cap = cv2.VideoCapture(self.file_path)
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
            if colorspace == "RGB":
                self.last_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            elif colorspace == "GRAY":
                self.last_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            else:
                self.last_frame = frame
        
        return ret, self.last_frame
    
    def closeCamera(self):
        if self._stream is not None:
            self._stream.release()

        self._running = False