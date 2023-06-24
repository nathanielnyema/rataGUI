"""
    Abstract camera class with generic functions. All camera models should be subclassed
    to ensure that all the necessary methods are available to the camera acquistion engine.
"""
from abc import ABC, abstractmethod
from typing import Any
import numpy.typing as npt

class BaseCamera(ABC):

    @staticmethod
    @abstractmethod
    def getAvailableCameras() -> dict[str, Any]:
        pass
    
    @abstractmethod
    def __init__(self):
        self.stream = None
        self._running = False
        self.frames = 0

        # TODO: Add required properties

    @abstractmethod
    def initializeCamera(self) -> bool:
        """
        Initializes the camera.
        """
        pass

    @abstractmethod
    def getCameraID(self) -> str:
        """
        Returns the ID of the camera.
        """
        pass

    @abstractmethod
    def readCamera(self) -> tuple[bool, npt.ArrayLike]:
        """
        Gets next frame
        """
        pass

    @abstractmethod
    def stopCamera(self) -> bool:
        """
        Stops the acquisition and closes the connection with the camera.
        """
        pass

    def __str__(self):
        return 'CameraID: {}'.format(self.cameraID)


    # def triggerCamera(self):
    #     """
    #     Triggers the camera.
    #     """
    #     print("Not Implemented")

    # def setAcquisitionMode(self, mode):
    #     """
    #     Set the readout mode of the camera: Single or continuous.
    #     :param int mode: One of self.MODE_CONTINUOUS, self.MODE_SINGLE_SHOT
    #     :return:
    #     """
    #     self.mode = mode

    # def getAcquisitionMode(self):
    #     """
    #     Returns the acquisition mode, either continuous or single shot.
    #     """
    #     return self.mode

    # def acquisitionReady(self):
    #     """
    #     Checks if the acquisition in the camera is over.
    #     """
    #     print("Not Implemented")

    # def setExposure(self,exposure):
    #     """
    #     Sets the exposure of the camera.
    #     """
    #     self.exposure = exposure
    #     print("Not Implemented")

    # def getExposure(self):
    #     """
    #     Gets the exposure time of the camera.
    #     """
    #     print("Not Implemented")
    #     return self.exposure

    # def setROI(self,X,Y):
    #     """ Sets up the ROI. Not all cameras are 0-indexed, so this is an important
    #     place to define the proper ROI.
    #     :param array X: array type with the coordinates for the ROI X[0], X[1]
    #     :param array Y: array type with the coordinates for the ROI Y[0], Y[1]
    #     :return:
    #     """
    #     print("Not Implemented")

    # def clearROI(self):
    #     """
    #     Clears the ROI from the camera.
    #     """
    #     self.setROI(self.maxWidth, self.maxHeight)

    # def getSize(self):
    #     """Returns the size in pixels of the image being acquired. This is useful for checking the ROI settings.
    #     """
    #     print("Not Implemented")

    # def GetCCDWidth(self):
    #     """
    #     Returns the CCD width in pixels
    #     """
    #     print("Not Implemented")

    # def GetCCDHeight(self):
    #     """
    #     Returns: the CCD height in pixels
    #     """
    #     print("Not Implemented")

    # def setBinning(self,xbin,ybin):
    #     """
    #     Sets the binning of the camera if supported. Has to check if binning in X/Y can be different or not, etc.
    #     :param xbin:
    #     :param ybin:
    #     :return:
    #     """
    #     print("Not Implemented")