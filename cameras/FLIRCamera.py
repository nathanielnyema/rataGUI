from cameras import *

import cv2
import PySpin

class FLIRCamera(BaseCamera):

    DEFAULT_PROPS = {
        "Limit framerate": True,
        "Framerate" : 30,
        # "Buffer size mode" : ["Manual", "Auto"], # Defaults to first item
        # "Buffer size": 20,
        "Buffer handling mode" : {"NewestOnly": PySpin.StreamBufferHandlingMode_NewestOnly,
                                 "NewestFirst": PySpin.StreamBufferHandlingMode_NewestFirst},  # Defaults to first item
        "LineSelector" : PySpin.LineSelector_Line2,
        "LineMode" : PySpin.LineMode_Output,
        "LineSource": PySpin.LineSource_ExposureActive,
    }

    DISPLAY_PROP_MAP = {
        "Framerate": "AcquisitionFrameRate",
        "Limit framerate": "AcquisitionFrameRateEnable",
        # "Buffer size mode": "StreamBufferCountMode",
        # "Buffer size": "StreamBufferCountManual",
        "Buffer handling mode": "TLStream.StreamBufferHandlingMode",
    }

    # Global pyspin system variable
    _SYSTEM = None

    @staticmethod
    def releaseResources():
        if FLIRCamera._SYSTEM is not None:
            FLIRCamera._SYSTEM.ReleaseInstance()
            del FLIRCamera._SYSTEM

    @staticmethod
    def getCameraList():
        '''Return a list of Spinnaker cameras that must be cleared. Also initializes the PySpin 'System', if needed.'''

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

    def __init__(self, cameraID: str):
        super().__init__()
        self.cameraID = cameraID
        self.initialized = False
        self.frames_dropped = 0
        self.last_frame = None
        self.last_index = -1

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
                print('Unable to retrieve chunk selector. Aborting...\n')
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
                            print(f'{chunk_str} enabled for FLIR camera: {self.cameraID}')
                        elif PySpin.IsWritable(chunk_enable):
                            chunk_enable.SetValue(True)
                            print(f'{chunk_str} enabled for FLIR camera: {self.cameraID}')
                        else:
                            print(f'{chunk_str} not writable for FLIR cameraa: {self.cameraID}')
                            result = False
                    else:
                        # Disable the boolean to disable the corresponding chunk data
                        if PySpin.IsWritable(chunk_enable):
                            chunk_enable.SetValue(False)
                        else:
                            result = False

        except PySpin.SpinnakerException as ex:
            print('Error: %s' % ex)
            result = False

        return result

    def initializeCamera(self, prop_config: dict = {}) -> bool:
        # Reset session variables
        self.__init__(self.cameraID)

        cam_list = FLIRCamera.getCameraList()
        if cam_list.GetSize() == 0:
            print("No camera available")
            cam_list.Clear()
            return False
        
        self.stream = cam_list.GetBySerial(self.cameraID)
        cam_list.Clear()

        # Initialize stream
        if not self.stream.IsInitialized():
            self.stream.Init()

        nodemap = self.stream.GetNodeMap()
        enabled_chunks = ["FrameID", "Timestamp"] # ExposureTime, PixelFormat
        self.configure_chunk_data(nodemap, enabled_chunks)

        for name, value in prop_config.items():
            prop_name = FLIRCamera.DISPLAY_PROP_MAP.get(name)
            if prop_name is None:
                prop_name = name

            try:
                # Recursively access QuickSpin API
                node = self.stream
                for attr in prop_name.split('.'):
                    node = getattr(node, attr)

                node.SetValue(value)
            except Exception as err:
                print(err)
                return False  
                
        self.initialized = True
        self.startStream()

        return True

    def startStream(self):
        self.stream.BeginAcquisition()
        self._running = True

    def stopStream(self):
        self.stream.EndAcquisition()
        self._running = False

    def readCamera(self, colorspace="RGB"):
        if not self._running:
            return False, None

        img_data = self.stream.GetNextImage()
        if img_data.IsIncomplete():
            print('Image incomplete with image status %d ...' % img_data.GetImageStatus())
            img_data.Release()
            return False, None

        # Parse image metadata
        chunk_data = img_data.GetChunkData()
        new_index = chunk_data.GetFrameID()

        # Detect dropped frames
        if self.last_index > 0:
            self.frames_dropped += new_index - self.last_index - 1
        self.last_index = new_index
        self.frames_acquired += 1

        frame = img_data.GetNDArray()
        match colorspace:
            case "BGR":
                self.last_frame = cv2.cvtColor(frame, cv2.COLOR_BayerBG2BGR)
            case "RGB":
                self.last_frame = cv2.cvtColor(frame, cv2.COLOR_BayerBG2RGB)
            case "GRAY":
                self.last_frame = cv2.cvtColor(frame, cv2.COLOR_BayerBG2GRAY)

        # Release image from camera buffer
        img_data.Release()
        return True, self.last_frame

    def closeCamera(self):
        try:
            if self.stream is not None:
                if self.stream.IsStreaming():
                    self.stopStream()
                
                self.stream.DeInit()
                del self.stream

            self.initialized = False
            self._running = False
            return True
        except Exception as err:
            print(err)
            return False

    def isOpened(self):
        return self._running


# EnumerationCount - Camera_EnumerationCount_get(self)
# TransferQueueOverflowCount
# GetCounterValue