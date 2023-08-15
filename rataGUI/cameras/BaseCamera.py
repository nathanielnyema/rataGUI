from abc import ABC, abstractmethod
from pyqtconfig import ConfigManager
from typing import Any, Tuple, List, Dict
from numpy.typing import NDArray

class BaseCamera(ABC):
    """
    Abstract camera class with generic functions. All camera models should be subclassed
    to ensure that all the necessary methods are available to the camera acquistion engine.
    """

    # Static variable to contain all camera subclasses
    camera_models = []

    # For every class that inherits from BaseCamera, the class name will be added to camera_models
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.camera_models.append(cls)

    @staticmethod
    @abstractmethod
    def getAvailableCameras() -> List[Any]:
        """ Returns list of camera objects wrapping every available device """
        pass

    # Optional method to release static resources upon exiting
    @staticmethod
    def releaseResources():
        pass

    def __init__(self, cameraID):
        self._stream = None
        self.cameraID = cameraID
        self.display_name = None
        self._running = False
        self.frames_acquired = 0


    @abstractmethod
    def initializeCamera(self, prop_config: ConfigManager, plugin_names: List[str]) -> bool:
        """
        Initializes the camera and returns whether it was successful

        :param prop_config: ConfigManager that stores settings to initialize camera
        :param plugin_names: List of plugin names to determine plugin-dependent settings 
        """
        raise NotImplementedError()

    @abstractmethod
    def readCamera(self) -> Tuple[bool, NDArray]:
        """
        Reads next frame on camera and whether retrieval was successful
        """
        raise NotImplementedError()

    @abstractmethod
    def closeCamera(self) -> bool:
        """
        Stops the acquisition and closes the connection with the camera.
        """
        raise NotImplementedError()

    def getDisplayName(self) -> str:
        """
        Returns the display name of the camera. Defaults to cameraID if display is not set.
        """
        if self.display_name is not None:
            return str(self.display_name)
        return str(self.cameraID)

    def isOpened(self) -> bool:
        """
        Returns true if camera has been initialized and is streaming.
        """
        return self._running  # Overwrite for custom behavior

    def getMetadata(self) -> Dict[str, Any]:
        """
        Returns camera metadata associated with last acquired frame
        """
        return {"Frame Index": self.frames_acquired}

    def __str__(self):
        return 'Camera ID: {}'.format(str(self.cameraID))