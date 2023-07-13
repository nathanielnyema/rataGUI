from cameras import BaseCamera
from config import video_file_paths

import os
import cv2

class VideoReader(BaseCamera):

    DEFAULT_PROPS = {
        "File path": "",
    }

    @staticmethod
    def getAvailableCameras():
        # Specify video path later
        if len(video_file_paths) == 0:
            return [VideoReader()]
        
        return [VideoReader(path) for path in video_file_paths]


    def __init__(self, file_path=""):
        super().__init__()
        self.cameraID = "File: " + str(file_path[:10])
        self.file_path = file_path
        self.last_frame = None

    def initializeCamera(self, config = dict()):
        self.input_params = {}
        self.output_params = {}
        for prop_name, value in config.items():
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

    def getName(self):
        if self.file_path == "":
            return "VideoReader"
        return self.cameraID