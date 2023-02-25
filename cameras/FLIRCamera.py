from .BaseCamera import BaseCamera

import cv2
import EasyPySpin
import PySpin

PropertyConverter = { 
    'AcquisitionFrameRateEnable': bool, 
    'AcquisitionFrameRate': float,  
    'GainAuto': str, 
    'ExposureAuto': str,
    'TriggerMode': str, 
    'TriggerDelay': float, 
    'Width': int, 
    'Height': int, 
    'OffsetX': int, 
    'OffsetY': int,
    'ExposureTime': float,
    'Gain': float, 
}




class FLIRCamera(BaseCamera):

    CameraAttributes = {
        "LineSelector" : "Line 2",
        "LineMode" : "Output",
        "LineSource": "Exposure Active",
    }

    # Global pyspin system variable
    _SYSTEM = None

    @staticmethod
    def getCameraList():
        '''Return a list of Spinnaker cameras. Also initializes the PySpin 'System', if needed.'''

        if FLIRCamera._SYSTEM is None:
            FLIRCamera._SYSTEM = PySpin.System.GetInstance()

        return FLIRCamera._SYSTEM.GetCameras()

    def __init__(self, cameraID=0):

        super().__init__()
        self.cameraID = cameraID
        self._initialized = False
        self.last_frame = None


    def initializeCamera(self, prop_dict = {}):
        #TODO Add more configurations
        if self.verify_network_stream():
            self.stream = EasyPySpin.VideoCapture(self.cameraID)
            # self.stream.set(cv2.CAP_PROP_EXPOSURE, -1)  # -1 sets exposure_time to auto
            # self.stream.set(cv2.CAP_PROP_GAIN, -1)  # -1 sets gain to auto

            for prop_name, value in prop_dict.items():
                if prop_name in PropertyConverter:
                    self.stream.set_pyspin_value(prop_name, value)

            self._running = True

    def readCamera(self, colorspace="BGR"):
        ret, frame = self.stream.read()
        if ret:
            match colorspace:
                case "BGR":
                    self.last_frame = cv2.cvtColor(frame, cv2.COLOR_BayerBG2BGR)
                case "RGB":
                    self.last_frame = cv2.cvtColor(frame, cv2.COLOR_BayerBG2RGB)
                case "HSV": 
                    self.last_frame = cv2.cvtColor(frame, cv2.COLOR_BayerBG2HSV)
                case "GRAY":

                    
                    self.last_frame = cv2.cvtColor(frame, cv2.COLOR_BayerBG2GRAY)
        
        return ret, self.last_frame

    def verify_network_stream(self):
        """Attempts to receive a frame from network stream to test if initialized"""

        cap = EasyPySpin.VideoCapture(self.cameraID)
        if cap.isOpened():
            self._initialized = True
        else:
            self._initialized = False
        cap.release()
        return True

    def stopCamera(self):
        if self.stream is not None:
            self.stream.release()
        self._running = False

    def getCameraID(self):
        return self.cameraID