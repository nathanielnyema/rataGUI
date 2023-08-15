from .BaseCamera import BaseCamera

from pypylon import pylon

import logging
logger = logging.getLogger(__name__)


READ_TIMEOUT = 10000    # 10 sec

class BaslerCamera(BaseCamera):

    # DEFAULT_PROPS = {
    #     "Limit Framerate": {"On": True, "Off": False},
    #     "Framerate": 30,
    #     "TriggerSource": {"Off": "TriggerMode_Off", 
    #                       "Line 3": PySpin.TriggerSource_Line3, "Line 0": PySpin.TriggerSource_Line0, 
    #                       "Line 1": PySpin.TriggerSource_Line1, "Line 2": PySpin.TriggerSource_Line2,},
    #                     #   "Software": PySpin.TriggerSource_Software}, # TODO: Add TriggerSoftware.Execute()
    #     "Buffer Mode": {"OldestFirst": PySpin.StreamBufferHandlingMode_OldestFirst,
    #                     "NewestOnly": PySpin.StreamBufferHandlingMode_NewestOnly,},
    #     # ["Line0 Input", "Line0_Output"]: [{}, {}]
    #     "Line0 Output": {"None": PySpin.LineSource_Off,},
    #     "Line1 Output": {"None": PySpin.LineSource_Off,},
    #     "Line2 Output": {"User Output 0": PySpin.LineSource_UserOutput0, "Frame Acquired": PySpin.LineSource_ExposureActive,},
    #     "Line3 Output": {"None": PySpin.LineSource_Off,},
    #     # "PixelFormat": {"RGB8": PySpin.PixelFormat_RGB8Packed, "BGR8": PySpin.PixelFormat_BGR8} # TODO: Ensure consistency
    # }

    # DISPLAY_PROP_MAP = {
    #     "Limit Framerate": "AcquisitionFrameRateEnable",
    #     "Framerate": "AcquisitionFrameRate",
    #     "Buffer Mode": "TLStream.StreamBufferHandlingMode",
    # }

    @staticmethod
    def getCameraList():
        '''Return a list of Basler camera pointers.'''
        tl_factory = pylon.TlFactory.GetInstance()
        cam_list = tl_factory.EnumerateDevices()
        return cam_list


    @staticmethod
    def getAvailableCameras():
        '''Returns list of all available FLIR cameras'''
        cameras = []
        cam_list = BaslerCamera.getCameraList()
        for cam in cam_list:
            serial_number = cam.GetSerialNumber()
            # Create camera wrapper object
            cameras.append(BaslerCamera(serial_number))
        return cameras

    @staticmethod
    def releaseResources():
        pass
        # if FLIRCamera._SYSTEM is not None:
        #     FLIRCamera._SYSTEM.ReleaseInstance()
        #     del FLIRCamera._SYSTEM

    def __init__(self, cameraID: str):
        super().__init__(cameraID)
        self.last_frame = None
        self.frames_dropped = 0
        self.last_index = -1
        self.buffer_size = 0
        self.initial_frameID = 0 # on camera transport layer
        self.FPS = -1


    # def configure_custom_settings(self, prop_config, plugin_names):
    #     ''' Configure plugin-dependent settings when initializing camera '''
    #     if "VideoWriter" in plugin_names: # Camera is recording
    #         prop_config.set("Line2 Output", "Frame Acquired")
    #     else:
    #         prop_config.set("Line2 Output", "User Output 0")

    def initializeCamera(self, prop_config, plugin_names=[]) -> bool:
        # Reset camera session variables
        self.__init__(self.cameraID)

        try:
            cam_list = BaslerCamera.getCameraList()
            for device in cam_list:
                if device.GetSerialNumber() == self.cameraID:
                    self._stream = pylon.InstantCamera(
                        pylon.TlFactory.GetInstance().CreateDevice(device)
                    )
                    break
            if self._stream is None:
                raise OSError(f"Camera {self.getDisplayName()} not found")

            if not self._stream.IsOpen():
                self._stream.Open()
        except (Exception, pylon.GenericException) as err:
            logger.exception(err)
            return False

        # Start video stream
        self._stream.MaxNumBuffer = 20
        self._stream.StartGrabbing(pylon.GrabStrategy_OneByOne)
        self._running = True

        self.converter = pylon.ImageFormatConverter()
        self.converter.OutputPixelFormat = pylon.PixelType_RGB8packed
        self.converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

        return True

    # def stopStream(self):
    #     pass
    #     # self._stream.EndAcquisition()
    #     # self._running = False

    def readCamera(self):
        try:
            grab_data = self.cam.RetrieveResult(READ_TIMEOUT, pylon.TimeoutHandling_ThrowException)
            if not grab_data.GrabSucceeded():
                return False, None

            img_data = self.converter.Convert(grab_data)
            self.frames_acquired += 1

            self.last_frame = img_data.GetArray()
            grab_data.Release()
            return True, self.last_frame

        except pylon.GenericException as err:
            logger.exception(err)
            return False, None


    # def getMetadata(self):
    #     return {"Camera Index": self.last_index - self.initial_frameID, 
    #             "Frame Index": self.frames_acquired,}


    def closeCamera(self):
        try:
            if self._stream is not None:
                self.cam.StopGrabbing()
                del self._stream

            self._running = False
            return True
        except Exception as err:
            logger.exception(err)
            return False


    def isOpened(self):
        return self._running
