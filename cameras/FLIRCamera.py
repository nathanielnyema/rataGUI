from cameras import BaseCamera, ConfigManager

import cv2
import PySpin

import os
import logging
logger = logging.getLogger(__name__)


READ_TIMEOUT = 10000    # 10 sec

class FLIRCamera(BaseCamera):

    DEFAULT_PROPS = {
        "Limit Framerate": {"On": True, "Off": False},
        "Framerate": 30,
        "Height": 1000,
        "Width": 1000,  
        "TriggerSource": {"Off": "TriggerMode_Off", 
                          "Line 3": PySpin.TriggerSource_Line3, "Line 0": PySpin.TriggerSource_Line0, 
                          "Line 1": PySpin.TriggerSource_Line1, "Line 2": PySpin.TriggerSource_Line2,},
        "Buffer Mode": {"OldestFirst": PySpin.StreamBufferHandlingMode_OldestFirst,
                        "NewestOnly": PySpin.StreamBufferHandlingMode_NewestOnly,},
        "Line0 Output": {"None": PySpin.LineSource_Off,},
        "Line1 Output": {"None": PySpin.LineSource_Off,},
        "Line2 Output": {"User Output 0": PySpin.LineSource_UserOutput0, "Frame Acquired": PySpin.LineSource_ExposureActive,},
        "Line3 Output": {"None": PySpin.LineSource_Off,},
        # "PixelFormat": {"RGB8": PySpin.PixelFormat_RGB8Packed, "BGR8": PySpin.PixelFormat_BGR8} # TODO: Ensure consistency
    }

    DISPLAY_PROP_MAP = {
        "Limit Framerate": "AcquisitionFrameRateEnable",
        "Framerate": "AcquisitionFrameRate",
        "Buffer Mode": "TLStream.StreamBufferHandlingMode",
    }

    # Global pyspin system variable
    _SYSTEM = None

    @staticmethod
    def getCameraList():
        '''
        Return a list of Spinnaker camera pointers that must be cleared and initializes the PySpin 'System' interface
        '''

        if FLIRCamera._SYSTEM is None:
            FLIRCamera._SYSTEM = PySpin.System.GetInstance()
        else:
            FLIRCamera._SYSTEM.UpdateCameras()
    
        return FLIRCamera._SYSTEM.GetCameras()

    @staticmethod
    def getAvailableCameras():
        '''Returns list of all available FLIR cameras'''
        cameras = []
        cam_list = FLIRCamera.getCameraList()
        for cam in cam_list:
            # print(camera.TLDevice.DeviceSerialNumber.ToString())
            if cam.TLDevice.DeviceSerialNumber.GetAccessMode() == PySpin.RO:
                serial_number = cam.TLDevice.DeviceSerialNumber.ToString()
                # Create camera wrapper object
                cameras.append(FLIRCamera(serial_number))
        cam_list.Clear()
        return cameras

    @staticmethod
    def releaseResources():
        if FLIRCamera._SYSTEM is not None:
            FLIRCamera._SYSTEM.ReleaseInstance()
            del FLIRCamera._SYSTEM

    def __init__(self, cameraID: str):
        super().__init__(cameraID)
        self.display_name = "FLIR:" + cameraID
        self.initialized = False
        self.last_frame = None
        self.frames_dropped = 0
        self.last_index = -1
        self.buffer_size = 0
        self.initial_frameID = 0 # on camera transport layer
        self.FPS = -1


    def configure_custom_settings(self, prop_config, plugin_names):
        ''' Configure plugin-dependent settings when initializing camera'''
        
        # Note: set the underlying value, not the display name
        if "VideoWriter" in plugin_names: # Camera is recording
            prop_config.set("Line2 Output", PySpin.LineSource_ExposureActive)
        else:
            prop_config.set("Line2 Output", PySpin.LineSource_UserOutput0)


    def initializeCamera(self, prop_config: ConfigManager, plugin_names=[]) -> bool:
        # Reset camera session variables
        self.__init__(self.cameraID)

        try:
            cam_list = FLIRCamera.getCameraList()
            self._stream = cam_list.GetBySerial(self.cameraID)

            if not self._stream.IsInitialized():
                self._stream.Init()
        except (Exception, PySpin.SpinnakerException) as err:
            logger.exception(err)
            return False
        finally:
            cam_list.Clear()

        self.configure_custom_settings(prop_config, plugin_names)
        try:
            nodemap = self._stream.GetNodeMap()
            enabled_chunks = ["FrameID",] # ExposureTime, PixelFormat
            self.configure_chunk_data(nodemap, enabled_chunks)

            for name, value in prop_config.as_dict().items():
                prop_name = FLIRCamera.DISPLAY_PROP_MAP.get(name)
                if prop_name is None:
                    prop_name = name
                    
                if prop_name.startswith("Line") and prop_name.endswith("Output"):
                    line_num = prop_name[4]
                    selector = getattr(PySpin, "LineSelector_Line" + line_num)
                    self._stream.LineSelector.SetValue(selector)
                    try: 
                        self._stream.LineMode.SetValue(PySpin.LineMode_Output)
                        self._stream.LineSource.SetValue(value)
                    except PySpin.SpinnakerException as ex:
                        logger.debug(f"Unable to write enum entry to Line {line_num}")
                        pass
                elif prop_name == "TriggerSource":
                    self._stream.TriggerMode.SetValue(PySpin.TriggerMode_Off)
                    if value != "TriggerMode_Off":
                        self._stream.TriggerSource.SetValue(value)
                        self._stream.TriggerMode.SetValue(PySpin.TriggerMode_On)
                else: 
                    # Recursively access QuickSpin API
                    node = self._stream
                    for attr in prop_name.split('.'):
                        node = getattr(node, attr)

                    if type(node) in [PySpin.IInteger, PySpin.IFloat]:
                        node_min = node.GetMin()
                        node_max = node.GetMax()
                        clipped = min(max(value, node_min), node_max)
                        if clipped != value:
                            logger.warning(f"{prop_name} must be in the range [{node_min}, {node_max}] \
                                    so {value} was clipped to {clipped}")
                            value = clipped

                    if node.GetAccessMode() == PySpin.RW:
                        node.SetValue(value)

        except (Exception, PySpin.SpinnakerException) as err:
            logger.exception(err)
            return False  
        
        if prop_config.get("Limit Framerate"):
            self.FPS = int(prop_config.get("Framerate"))
        else:
            self.FPS = -1
        
        # print(dir(self._stream.TLStream))
        # print(self._stream.TLStream.StreamBufferHandlingMode.ToString())
        # print(self._stream.TLStream.StreamOutputBufferCount.GetValue())
        # print(self._stream.AcquisitionMode.ToString())

        self.initialized = True
        self.startStream()

        return True

    def startStream(self):
        self._stream.BeginAcquisition()
        self._running = True

    def stopStream(self):
        self._stream.EndAcquisition()
        self._running = False

    def readCamera(self, colorspace="RGB"):
        try:
            img_data = self._stream.GetNextImage(READ_TIMEOUT)
            if img_data.IsIncomplete():
                logger.error('Image incomplete with image status %d ...' % img_data.GetImageStatus())
                return False, None

            # Parse image metadata
            chunk_data = img_data.GetChunkData()
            new_index = chunk_data.GetFrameID()
            # time_stamp = chunk_data.GetTimestamp()

            # Detect dropped frames
            if self.last_index >= 0:
                self.frames_dropped += new_index - self.last_index - 1
                self.buffer_size = self._stream.TLStream.StreamOutputBufferCount.GetValue()
            else:
                self.initial_frameID = new_index
            self.last_index = new_index
            self.frames_acquired += 1

            frame = img_data.GetNDArray()
            if colorspace == "BGR":
                self.last_frame = cv2.cvtColor(frame, cv2.COLOR_BayerBG2BGR)
            elif colorspace == "RGB":
                self.last_frame = cv2.cvtColor(frame, cv2.COLOR_BayerBG2RGB)
            elif colorspace == "GRAY":
                self.last_frame = cv2.cvtColor(frame, cv2.COLOR_BayerBG2GRAY)
            else:
                self.last_frame = frame

            # Release image from camera buffer
            img_data.Release()
            return True, self.last_frame

        except PySpin.SpinnakerException as ex:
            logger.exception(ex)
            return False, None


    def getMetadata(self):
        return {"Camera Index": self.last_index - self.initial_frameID, 
                "Frame Index": self.frames_acquired,}


    def closeCamera(self):
        try:
            if self._stream is not None:
                if self._stream.IsStreaming():
                    self.stopStream()
                
                self._stream.DeInit()
                del self._stream

            self.initialized = False
            self._running = False
            return True
        except Exception as err:
            logger.exception(err)
            return False


    def isOpened(self):
        return self._running


    def configure_chunk_data(self, nodemap, selected_chucks, enable = True) -> bool:
            """
            Configures the camera to add chunk data to each image.

            :param nodemap: Transport layer device nodemap.
            :type nodemap: INodeMap
            """
            try:
                result = True

                # Activate chunk mode
                # Once enabled, chunk data will be available at the end of the payload of every image captured until it is disabled.
                chunk_mode_active = PySpin.CBooleanPtr(nodemap.GetNode('ChunkModeActive'))

                if PySpin.IsAvailable(chunk_mode_active) and PySpin.IsWritable(chunk_mode_active):
                    chunk_mode_active.SetValue(True)

                chunk_selector = PySpin.CEnumerationPtr(nodemap.GetNode('ChunkSelector'))

                if not PySpin.IsAvailable(chunk_selector) or not PySpin.IsReadable(chunk_selector):
                    logger.error('Unable to retrieve chunk selector. Aborting...\n')
                    return False

                # Retrieve entries from enumeration ptr
                entries = [PySpin.CEnumEntryPtr(chunk_selector_entry) for chunk_selector_entry in chunk_selector.GetEntries()]

                # Select entry nodes to enable
                for chunk_selector_entry in entries:
                    # Go to next node if problem occurs
                    if not PySpin.IsAvailable(chunk_selector_entry) or not PySpin.IsReadable(chunk_selector_entry):
                        result = False
                        continue

                    chunk_str = chunk_selector_entry.GetSymbolic()

                    if chunk_str in selected_chucks:
                        chunk_selector.SetIntValue(chunk_selector_entry.GetValue())

                        # Retrieve corresponding boolean
                        chunk_enable = PySpin.CBooleanPtr(nodemap.GetNode('ChunkEnable'))

                        # Enable the corresponding chunk data
                        if enable:
                            if chunk_enable.GetValue() is True:
                                logger.info(f'{chunk_str} enabled for FLIR camera: {self.cameraID}')
                            elif PySpin.IsWritable(chunk_enable):
                                chunk_enable.SetValue(True)
                                logger.info(f'{chunk_str} enabled for FLIR camera: {self.cameraID}')
                            else:
                                logger.error(f'{chunk_str} not writable for FLIR cameraa: {self.cameraID}')
                                result = False
                        else:
                            # Disable the boolean to disable the corresponding chunk data
                            if PySpin.IsWritable(chunk_enable):
                                chunk_enable.SetValue(False)
                            else:
                                result = False

            except PySpin.SpinnakerException as ex:
                logger.exception(ex)
                result = False

            return result