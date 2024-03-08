from rataGUI.cameras.BaseCamera import BaseCamera

import cv2
import logging

from picamera2 import Picamera2

logger = logging.getLogger(__name__)


class PiCamera(BaseCamera):
    """
    Example subclass to overwrite with the required functionality for a custom camera model
    """

    DEFAULT_PROPS = {
        "Framerate": 30,
        "Buffer Size": 10,
        "Height": 1280,
        "Width": 720, 
    }

    @staticmethod
    def getAvailableCameras():
        # print(Picamera2.global_camera_info())
        return [PiCamera(cam['Num']) for cam in Picamera2.global_camera_info()]

    def __init__(self, cameraID):
        super().__init__(cameraID)
        self.display_name = "PiCam: " + str(cameraID)
        self.last_frame = None

    def initializeCamera(self, prop_config, plugin_names=[]):
        self._stream = Picamera2(self.cameraID)
        controls = {
            "FrameRate": prop_config.get("Framerate"),

        }
        sensor_props = {
            "output_size": (prop_config.get("Height"), prop_config.get("Width")),
        }

        video_config = self._stream.create_video_configuration(buffer_count=prop_config.get("Buffer Size"),
                                                               controls=controls, sensor=sensor_props)
        self._stream.configure(video_config)


        self._stream.start()
        self._running = True
        return True

    def readCamera(self, colorspace="RGB"):
        frame = self._stream.capture_array("main")
        self.frames_acquired += 1
        if colorspace == "RGB":
            self.last_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        elif colorspace == "GRAY":
            self.last_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            self.last_frame = frame

        return True, self.last_frame

    def closeCamera(self):
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()

        self._running = False
