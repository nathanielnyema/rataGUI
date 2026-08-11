from rataGUI.cameras.BaseCamera import BaseCamera

import cv2
import PySpin

import logging
from typing import Any, Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)


READ_TIMEOUT = 15000


class FLIRCamera(BaseCamera):
    DEFAULT_PROPS = {  # Order Sensitive
        "Line0 Output": {
            "None": PySpin.LineSource_Off,
        },
        "Line1 Output": {
            "None": PySpin.LineSource_Off,
            "User Output 0": PySpin.LineSource_UserOutput0,
            "Frame Acquired": PySpin.LineSource_ExposureActive,
        },
        "Line2 Output": {
            "User Output 0": PySpin.LineSource_UserOutput0,
            "Frame Acquired": PySpin.LineSource_ExposureActive,
        },
        "Line3 Output": {
            "None": PySpin.LineSource_Off,
        },
        "Timestamp Line": ["None", "Line0", "Line1", "Line2", "Line3"],
        "Timestamp While Recording": True,
        "TriggerSource": {
            "Off": "TriggerMode_Off",
            "Line 3": PySpin.TriggerSource_Line3,
            "Line 0": PySpin.TriggerSource_Line0,
            "Line 1": PySpin.TriggerSource_Line1,
            "Line 2": PySpin.TriggerSource_Line2,
        },
        "Buffer Mode": {
            "OldestFirst": PySpin.StreamBufferHandlingMode_OldestFirst,
            "NewestOnly": PySpin.StreamBufferHandlingMode_NewestOnly,
        },
        "Limit Framerate": {"On": True, "Off": False},
        "Framerate": 30,
        "Buffer Size": 20,  # Auto
        "Gain": -1,
        "Gamma": -1.0,
        "Exposure (μs)": -1,
        "Width": 10000,
        "Height": 10000,
        "OffsetX": 0,
        "OffsetY": 0,
        "Pixel Format": {"Bayer RG 8-bit": PySpin.PixelFormat_BayerRG8,
                         "Mono 8-bit": PySpin.PixelFormat_Mono8},
    }

    DISPLAY_PROP_MAP = {
        "Limit Framerate": "AcquisitionFrameRateEnable",
        "Framerate": "AcquisitionFrameRate",
        "Buffer Mode": "TLStream.StreamBufferHandlingMode",
        "Buffer Size": "TLStream.StreamBufferCountManual",
        "Exposure (μs)": "ExposureTime",
    }

    # Global pyspin system variable
    _SYSTEM = None

    # ---- Discovery tables ----------------------------------------------------

    # Symbolic LineSource entry -> display name. Unlisted entries fall back to
    # their raw symbolic name (e.g. "Counter0Active").
    LINE_SOURCE_NAMES = {
        "Off": "None",
        "UserOutput0": "User Output 0",
        "UserOutput1": "User Output 1",
        "UserOutput2": "User Output 2",
        "UserOutput3": "User Output 3",
        "ExposureActive": "Frame Acquired",
    }
    # add_config_handler defaults a dropdown to its first key, so ordering matters.
    # LINE_SOURCE_DEFAULTS = {"Line2 Output": "UserOutput0"}
    LINE_SOURCE_ORDER = ["Off", "UserOutput0", "ExposureActive"]

    TRIGGER_SOURCE_NAMES = {
        "Line0": "Line 0",
        "Line1": "Line 1",
        "Line2": "Line 2",
        "Line3": "Line 3",
        "Software": "Software",
        "Counter0Start": "Counter 0 Start",
        "Counter1Start": "Counter 1 Start",
    }
    TRIGGER_SOURCE_ORDER = ["Line0", "Line1", "Line2", "Line3", "Software"]

    # Sentinel meaning "no external trigger" — not a device enum entry.
    TRIGGER_OFF = "TriggerMode_Off"

    PIXEL_FORMAT_NAMES = {
        "Mono8": "Mono 8-bit",
        "BayerRG8": "Bayer RG 8-bit",
        "BayerGR8": "Bayer GR 8-bit",
        "BayerGB8": "Bayer GB 8-bit",
        "BayerBG8": "Bayer BG 8-bit",
        "RGB8": "RGB 8-bit (camera ISP)",
        "BGR8": "BGR 8-bit (camera ISP)",
    }
    PIXEL_FORMAT_ORDER = ["BayerRG8", "Mono8"]  # preserve current color default
    MONO_FORMATS = {"Mono8", "Mono16"}

    # NOTE: OpenCV's Bayer naming is offset by one row/column relative to the
    # GenICam convention, so GenICam BayerRG maps to cv2.COLOR_BayerBG*. This
    # is intentional — do not "correct" it to COLOR_BayerRG*.
    BAYER_CONVERSIONS = {
        "BayerRG8": (cv2.COLOR_BayerBG2RGB, cv2.COLOR_BayerBG2BGR),
        "BayerGR8": (cv2.COLOR_BayerGB2RGB, cv2.COLOR_BayerGB2BGR),
        "BayerGB8": (cv2.COLOR_BayerGR2RGB, cv2.COLOR_BayerGR2BGR),
        "BayerBG8": (cv2.COLOR_BayerRG2RGB, cv2.COLOR_BayerRG2BGR),
    }

    # Discovered props cached per DeviceModelName — line/format capability is
    # fixed by firmware, so one query per model is enough.
    _DEVICE_PROPS_CACHE: Dict[str, Tuple[Dict[str, Any], List[str]]] = {}

    SKIP_PROPS = {"Camera Parameters File", "Pixel Format",
                "Timestamp Line", "Timestamp While Recording"}


    @staticmethod
    def _order_options(entries, names, preferred=None, order=None) -> Dict[str, Any]:
        order = order or []

        def sort_key(item):
            symbolic, _value = item
            if preferred is not None and symbolic == preferred:
                return (0, 0, symbolic)
            if symbolic in order:
                return (1, order.index(symbolic), symbolic)
            return (2, 0, symbolic)

        return {
            names.get(symbolic, symbolic): value
            for symbolic, value in sorted(entries.items(), key=sort_key)
        }

    @staticmethod
    def _enum_entries(nodemap, node_name: str) -> Dict[str, Any]:
        """Return {symbolic: value} for every available, readable entry of an enum node."""
        node = PySpin.CEnumerationPtr(nodemap.GetNode(node_name))
        if not PySpin.IsAvailable(node) or not PySpin.IsReadable(node):
            return {}
        entries = {}
        for ptr in node.GetEntries():
            entry = PySpin.CEnumEntryPtr(ptr)
            if PySpin.IsAvailable(entry) and PySpin.IsReadable(entry):
                entries[entry.GetSymbolic()] = entry.GetValue()
        return entries


    @staticmethod
    def _enum_options(
        nodemap,
        node_name: str,
        names: Dict[str, str],
        preferred: Optional[str] = None,
        order: Optional[List[str]] = None,
        strict: bool = True,
    ) -> Dict[str, Any]:
        """Enumerate an enum node as an ordered {display name: value} prop dict.

        :param names: Symbolic -> display name. With ``strict``, entries absent
            from this map are dropped; otherwise the symbolic name is used as-is.
        """
        entries = FLIRCamera._enum_entries(nodemap, node_name)
        if strict:
            entries = {s: v for s, v in entries.items() if s in names}
        return FLIRCamera._order_options(entries, names, preferred, order)

    @staticmethod
    def _iter_selector(nodemap, selector_name: str, prefix: str = ""):
        """Yield (symbolic, node) for each selectable entry, restoring the selector after.

        Note: do not ``break`` out of this loop — the selector is restored when the
        generator closes, which is deferred on an early exit.
        """
        selector = PySpin.CEnumerationPtr(nodemap.GetNode(selector_name))
        if not PySpin.IsAvailable(selector) or not PySpin.IsReadable(selector):
            return
        original = selector.GetIntValue()
        try:
            for ptr in selector.GetEntries():
                entry = PySpin.CEnumEntryPtr(ptr)
                if not PySpin.IsAvailable(entry) or not PySpin.IsReadable(entry):
                    continue
                symbolic = entry.GetSymbolic()
                if prefix and not symbolic.startswith(prefix):
                    continue
                selector.SetIntValue(entry.GetValue())
                yield symbolic
        finally:
            selector.SetIntValue(original)

    @staticmethod
    def _query_pixel_formats(nodemap) -> Dict[str, Any]:
        return FLIRCamera._enum_options(
            nodemap, "PixelFormat", FLIRCamera.PIXEL_FORMAT_NAMES,
            order=FLIRCamera.PIXEL_FORMAT_ORDER,
        )


    @staticmethod
    def _query_trigger_sources(nodemap, input_lines=None) -> Dict[str, Any]:
        options = FLIRCamera._enum_options(
            nodemap, "TriggerSource", FLIRCamera.TRIGGER_SOURCE_NAMES,
            order=FLIRCamera.TRIGGER_SOURCE_ORDER,
        )
        if input_lines is not None:
            allowed = {FLIRCamera.TRIGGER_SOURCE_NAMES[s] for s in input_lines
                    if s in FLIRCamera.TRIGGER_SOURCE_NAMES}
            options = {d: v for d, v in options.items()
                    if d in allowed or not d.startswith("Line ")}
        if not options:
            return {}
        return {"Off": FLIRCamera.TRIGGER_OFF, **options}


    @staticmethod
    def _query_line_props(nodemap, modes: Dict[str, set]) -> Dict[str, Dict[str, Any]]:
        props = {}
        for line_name in FLIRCamera._iter_selector(nodemap, "LineSelector", prefix="Line"):
            if "Output" not in modes.get(line_name, set()):
                continue
            options = FLIRCamera._enum_options(
                nodemap, "LineSource", FLIRCamera.LINE_SOURCE_NAMES,
                order=FLIRCamera.LINE_SOURCE_ORDER, strict=False,
            )
            if options:
                props[f"{line_name} Output"] = options
        return props

    @staticmethod
    def _query_line_modes(nodemap) -> Dict[str, set]:
        modes = {}
        for line_name in FLIRCamera._iter_selector(nodemap, "LineSelector", prefix="Line"):
            mode = PySpin.CEnumerationPtr(nodemap.GetNode("LineMode"))
            if not PySpin.IsAvailable(mode):
                continue
            if PySpin.IsWritable(mode):
                available = {m for m in ("Input", "Output")
                            if (e := mode.GetEntryByName(m)) is not None
                            and PySpin.IsAvailable(e)}
            else:
                current = mode.GetCurrentEntry()
                available = {current.GetSymbolic()} if current is not None else set()
            if available:
                modes[line_name] = available
        return modes

    def getDeviceProps(self) -> Tuple[Dict[str, Any], List[str]]:
        """Query this camera for the settings it actually supports.

        :return: (props to merge over DEFAULT_PROPS, DEFAULT_PROPS keys to drop)
        """
        cam_list = None
        stream = None
        did_init = False
        self.props_complete = False
        try:
            cam_list = FLIRCamera.getCameraList()
            stream = cam_list.GetBySerial(self.serial_num)

            model = "unknown"
            if stream.TLDevice.DeviceModelName.GetAccessMode() == PySpin.RO:
                model = stream.TLDevice.DeviceModelName.ToString()
            if model in FLIRCamera._DEVICE_PROPS_CACHE:
                props, remove = FLIRCamera._DEVICE_PROPS_CACHE[model]
                return dict(props), list(remove)

            if not stream.IsInitialized():
                stream.Init()
                did_init = True
            nodemap = stream.GetNodeMap()

            props: Dict[str, Any] = {}
            remove: List[str] = []

            modes = FLIRCamera._query_line_modes(nodemap)
            lines = FLIRCamera._query_line_props(nodemap, modes)
            if lines:
                props.update(lines)
                # Prune hardcoded lines this model doesn't expose as outputs.
                # Only when the query succeeded — otherwise keep the fallbacks.
                remove = [
                    k for k in FLIRCamera.DEFAULT_PROPS
                    if k.startswith("Line") and k.endswith("Output") and k not in lines
                ]
                if remove:
                    logger.debug("Camera %s does not expose %s", self.serial_num, remove)

                # Only offer lines that can actually be driven by ExposureActive
                capable = [
                    key.split()[0] for key, opts in lines.items()
                    if PySpin.LineSource_ExposureActive in opts.values()
                ]
                if capable:
                    props["Timestamp Line"] = ["None"] + capable
                    props["Timestamp While Recording"] = True
            else:
                self.props_complete = False
                logger.warning("No line outputs discovered on camera %s; using DEFAULT_PROPS",
                            self.serial_num)
    
            formats = FLIRCamera._query_pixel_formats(nodemap)
            if formats:
                props["Pixel Format"] = formats
            else:
                self.props_complete = False
                logger.warning("No pixel formats discovered on camera %s; using DEFAULT_PROPS",
                            self.serial_num)

            input_lines = {name for name, m in modes.items() if "Input" in m}
            triggers = FLIRCamera._query_trigger_sources(nodemap, input_lines or None)
            if triggers:
                props["TriggerSource"] = triggers

            FLIRCamera._DEVICE_PROPS_CACHE[model] = (dict(props), list(remove))
            return props, remove

        except PySpin.SpinnakerException as err:
            logger.warning(
                "Could not query device properties for camera %s; using DEFAULT_PROPS",
                self.serial_num,
            )
            logger.debug(err)
            return {}, []
        finally:
            try:
                if did_init and stream is not None and stream.IsInitialized():
                    stream.DeInit()
            except PySpin.SpinnakerException:
                pass
            del stream
            if cam_list is not None:
                cam_list.Clear()

    @staticmethod
    def getCameraList():
        """
        Return a list of Spinnaker camera pointers that must be cleared and initializes the PySpin 'System' interface
        """

        if FLIRCamera._SYSTEM is None:
            FLIRCamera._SYSTEM = PySpin.System.GetInstance()
        else:
            FLIRCamera._SYSTEM.UpdateCameras()

        return FLIRCamera._SYSTEM.GetCameras()

    @staticmethod
    def getAvailableCameras():
        """Returns list of all available FLIR cameras"""
        cameras = []
        cam_list = FLIRCamera.getCameraList()
        for cam in cam_list:
            if cam.TLDevice.DeviceSerialNumber.GetAccessMode() == PySpin.RO:
                serial_number = cam.TLDevice.DeviceSerialNumber.ToString()
                # Create camera wrapper object
                cameras.append(FLIRCamera(serial_number))
        cam_list.Clear()
        return cameras

    @staticmethod
    def releaseResources():
        if FLIRCamera._SYSTEM is not None and not FLIRCamera._SYSTEM.IsInUse():
            FLIRCamera._SYSTEM.ReleaseInstance()
            del FLIRCamera._SYSTEM

    def __init__(self, serial: str):
        """Initialize a FLIRCamera wrapper for the given serial number."""
        super().__init__("FLIR:" + serial)
        self.serial_num = serial
        self.last_frame = None
        self.frames_dropped = 0
        self.last_index = -1
        self.buffer_size = 0
        self.initial_frameID = 0  # on camera transport layer
        self.pixel_format = None

    def configure_custom_settings(self, prop_config, plugin_names):
        """Apply plugin-dependent settings when initializing camera."""
        recording = "VideoWriter" in plugin_names
        settings = prop_config.as_dict()

        line = settings.get("Timestamp Line", "None")
        auto = settings.get("Timestamp While Recording", False)

        if auto and line != "None":
            key = f"{line} Output"
            if key not in settings:
                logger.warning(
                    "Timestamp line %s is not available on camera %s; "
                    "frame timestamps will not be generated", line, self.serial_num,
                )
            elif recording:
                # Override the idle value only while recording
                prop_config.set(key, PySpin.LineSource_ExposureActive)
                logger.info(
                    "Recording: driving %s with ExposureActive for frame timestamps", line,
                )
            # Not recording -> leave the user's configured idle value untouched

        if prop_config.get("TriggerSource") != "TriggerMode_Off":
            prop_config.set("Limit Framerate", False)

    def initializeCamera(self, prop_config, plugin_names=[]) -> bool:
        """Configure and start the FLIR camera stream via PySpin. Returns True on success."""
        # Reset camera session variables
        self.frames_dropped = 0
        self.last_index = -1
        self.buffer_size = 0
        self.initial_frameID = 0
        self.pixel_format = None

        try:
            cam_list = FLIRCamera.getCameraList()
            self._stream = cam_list.GetBySerial(self.serial_num)

            # Force a clean camera state regardless of previous session.
            # If the previous process crashed, the camera may still be
            # streaming or initialized, which makes property nodes read-only.
            if self._stream.IsStreaming():
                logger.warning(
                    "Camera %s was still streaming (stale session?), stopping acquisition",
                    self.serial_num,
                )
                self._stream.EndAcquisition()

            if self._stream.IsInitialized():
                logger.warning(
                    "Camera %s was already initialized, reinitializing for clean state",
                    self.serial_num,
                )
                self._stream.DeInit()

            self._stream.Init()
            logger.info("Camera %s initialized successfully", self.serial_num)
        except PySpin.SpinnakerException as err:
            logger.exception(err)
            logger.error("PySpin failed to find and initialize camera")
            return False
        finally:
            cam_list.Clear()

        self.configure_custom_settings(prop_config, plugin_names)
        try:
            nodemap = self._stream.GetNodeMap()
            enabled_chunks = [
                "FrameID",
            ]  # ExposureTime, PixelFormat
            self.configure_chunk_data(nodemap, enabled_chunks)

            for name, value in prop_config.as_dict().items():
                if name in FLIRCamera.SKIP_PROPS:
                    continue
                if name.startswith("Line") and name.endswith("Output"):
                    line_num = name[4]
                    try:
                        selector = getattr(PySpin, "LineSelector_Line" + line_num)
                        self._stream.LineSelector.SetValue(selector)
                        self._stream.LineMode.SetValue(PySpin.LineMode_Output)
                        self._stream.LineSource.SetValue(value)
                    except (PySpin.SpinnakerException, AttributeError):
                        logger.warning(f"Unable to write enum entry to Line {line_num}")
                elif name == "TriggerSource":
                    if value == "TriggerMode_Off":
                        self._stream.TriggerMode.SetValue(PySpin.TriggerMode_Off)
                    else:
                        self._stream.TriggerMode.SetValue(PySpin.TriggerMode_On)
                        self._stream.TriggerOverlap.SetValue(
                            PySpin.TriggerOverlap_ReadOut
                        )  # Off or ReadOut to speed up
                        self._stream.TriggerSource.SetValue(value)
                        self._stream.TriggerActivation.SetValue(
                            PySpin.TriggerActivation_RisingEdge
                        )  # LevelHigh or RisingEdge
                        self._stream.TriggerSelector.SetValue(
                            PySpin.TriggerSelector_FrameStart
                        )  # require trigger for each frame

                else:
                    # Set to auto mode if value is negative
                    if name == "Buffer Size":
                        # if value < 0: # No buffer auto mode
                        #     continue
                        self._stream.TLStream.StreamBufferCountMode.SetValue(
                            PySpin.StreamBufferCountMode_Manual
                        )
                    elif name == "Gain":
                        if value < 0:
                            self._stream.GainAuto.SetValue(PySpin.GainAuto_Continuous)
                            continue
                        self._stream.GainAuto.SetValue(PySpin.GainAuto_Off)
                    elif name == "Gamma":
                        if value < 0:
                            self._stream.GammaEnable.SetValue(False)
                            continue
                        self._stream.GammaEnable.SetValue(True)
                    elif name == "Exposure (μs)":
                        if value < 0:
                            self._stream.ExposureAuto.SetValue(
                                PySpin.ExposureAuto_Continuous
                            )
                            continue
                        self._stream.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)
                        self._stream.ExposureMode.SetValue(PySpin.ExposureMode_Timed)

                    # Recursively access QuickSpin API
                    prop_name = FLIRCamera.DISPLAY_PROP_MAP.get(name, name)
                    node = self._stream
                    attrs = prop_name.split(".")
                    if len(attrs) > 0 and hasattr(node, attrs[0]):
                        for attr in prop_name.split("."):
                            node = getattr(node, attr)

                        if type(node) in [PySpin.IInteger, PySpin.IFloat]:
                            node_min = node.GetMin()
                            node_max = node.GetMax()
                            clipped = min(max(value, node_min), node_max)
                            if clipped != value:
                                logger.warning(
                                    f"{prop_name} must be in the range [{node_min}, {node_max}]"
                                    f" so {value} was clipped to {clipped}"
                                )
                                prop_config.set(name, int(clipped))
                                value = clipped

                        if node.GetAccessMode() == PySpin.RW:
                            node.SetValue(value)

            fmt = prop_config.get("Pixel Format")

            # ISP must be on for camera-side debayering (RGB8/BGR8), off for raw output.
            # Set before PixelFormat: ISP state gates which formats are selectable.
            if self._stream.IspEnable.GetAccessMode() == PySpin.RW:
                self._stream.IspEnable.SetValue(
                    fmt in (PySpin.PixelFormat_RGB8, PySpin.PixelFormat_BGR8)
                )

            if fmt is not None and self._stream.PixelFormat.GetAccessMode() == PySpin.RW:
                try:
                    self._stream.PixelFormat.SetValue(fmt)
                except PySpin.SpinnakerException:
                    logger.warning("Pixel format unavailable on camera %s; using camera default",
                                self.serial_num)

            # Read back rather than trusting config — needed for readCamera's conversion
            self.pixel_format = self._stream.PixelFormat.GetCurrentEntry().GetSymbolic()

        except PySpin.SpinnakerException as err:
            logger.exception(err)
            logger.error("PySpin failed to configure camera property values")
            return False

        logger.info("Camera %s beginning acquisition", self.serial_num)
        self._stream.BeginAcquisition()
        self._running = True
        logger.info("Camera %s acquisition started", self.serial_num)

        return True

    def readCamera(self, colorspace="RGB"):
        """Read the next frame from the FLIR camera. Returns (success, frame)."""
        try:
            img_data = self._stream.GetNextImage(READ_TIMEOUT)
            if img_data.IsIncomplete():
                logger.error(
                    "Image incomplete with image status %d ..."
                    % img_data.GetImageStatus()
                )
                return False, None

            # Parse image metadata
            chunk_data = img_data.GetChunkData()
            new_index = chunk_data.GetFrameID()
            # time_stamp = chunk_data.GetTimestamp()

            # Detect dropped frames
            if self.last_index >= 0:
                self.frames_dropped += new_index - self.last_index - 1
                self.buffer_size = (
                    self._stream.TLStream.StreamOutputBufferCount.GetValue()
                )
            else:
                self.initial_frameID = new_index
            self.last_index = new_index
            self.frames_acquired += 1


            raw = img_data.GetNDArray()
            fmt = self.pixel_format

            if fmt in FLIRCamera.MONO_FORMATS:
                # Expand to (H, W, 3): the ring buffer, VideoWriter and FrameDisplay
                # all unpack a 3-tuple shape.
                code = cv2.COLOR_GRAY2BGR if colorspace == "BGR" else cv2.COLOR_GRAY2RGB
                self.last_frame = cv2.cvtColor(raw, code)
            elif fmt in FLIRCamera.BAYER_CONVERSIONS:
                rgb_code, bgr_code = FLIRCamera.BAYER_CONVERSIONS[fmt]
                self.last_frame = cv2.cvtColor(raw, bgr_code if colorspace == "BGR" else rgb_code)
            else:
                if fmt not in ("RGB8", "BGR8"):
                    logger.warning("Unhandled pixel format %s on camera %s; passing through raw",
                                fmt, self.serial_num)
                self.last_frame = raw.copy()

            # Release image from camera buffer
            img_data.Release()
            return True, self.last_frame

        except PySpin.SpinnakerException as ex:
            logger.exception(ex)
            return False, None

    def getMetadata(self):
        """Return a dict of camera-specific metadata for the most recent frame."""
        return {
            "Camera Index": self.last_index - self.initial_frameID,
            "Frame Index": self.frames_acquired,
        }

    def closeCamera(self):
        """Stop acquisition and release the FLIR camera."""
        logger.info(f"Closing camera: {self.getDisplayName()}")
        try:
            if self._stream is not None:
                if self._stream.IsStreaming():
                    self._stream.EndAcquisition()

                self._stream.DeInit()
                self._stream = None

            self._running = False
            return True
        except Exception as err:
            logger.exception(err)
            return False

    def configure_chunk_data(self, nodemap, selected_chucks, enable=True) -> bool:
        """
        Configures the camera to add chunk data to each image.

        :param nodemap: Transport layer device nodemap.
        :type nodemap: INodeMap
        """
        try:
            result = True

            # Activate chunk mode
            # Once enabled, chunk data will be available at the end of the payload of every image captured until it is disabled.
            chunk_mode_active = PySpin.CBooleanPtr(nodemap.GetNode("ChunkModeActive"))

            if PySpin.IsAvailable(chunk_mode_active) and PySpin.IsWritable(
                chunk_mode_active
            ):
                chunk_mode_active.SetValue(True)

            chunk_selector = PySpin.CEnumerationPtr(nodemap.GetNode("ChunkSelector"))

            if not PySpin.IsAvailable(chunk_selector) or not PySpin.IsReadable(
                chunk_selector
            ):
                logger.error("Unable to retrieve chunk selector. Aborting...\n")
                return False

            # Retrieve entries from enumeration ptr
            entries = [
                PySpin.CEnumEntryPtr(chunk_selector_entry)
                for chunk_selector_entry in chunk_selector.GetEntries()
            ]

            # Select entry nodes to enable
            for chunk_selector_entry in entries:
                # Go to next node if problem occurs
                if not PySpin.IsAvailable(
                    chunk_selector_entry
                ) or not PySpin.IsReadable(chunk_selector_entry):
                    result = False
                    continue

                chunk_str = chunk_selector_entry.GetSymbolic()

                if chunk_str in selected_chucks:
                    chunk_selector.SetIntValue(chunk_selector_entry.GetValue())

                    # Retrieve corresponding boolean
                    chunk_enable = PySpin.CBooleanPtr(nodemap.GetNode("ChunkEnable"))

                    # Enable the corresponding chunk data
                    if enable:
                        if chunk_enable.GetValue() is True:
                            logger.info(
                                f"{chunk_str} enabled for FLIR camera: {self.serial_num}"
                            )
                        elif PySpin.IsWritable(chunk_enable):
                            chunk_enable.SetValue(True)
                            logger.info(
                                f"{chunk_str} enabled for FLIR camera: {self.serial_num}"
                            )
                        else:
                            logger.error(
                                f"{chunk_str} not writable for FLIR camera: {self.serial_num}"
                            )
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
