from abc import ABC, abstractmethod

from pyqtconfig import ConfigManager

from typing import Any

import logging
logger = logging.getLogger(__name__)

class BaseTrigger(ABC):
    """
    Abstract trigger class with generic functions. All custom triggers should be subclassed
    to ensure that all the necessary methods are available to the triggering interface.
    """

    # Static variable to contain all trigger subclasses
    trigger_types = []

    # For every class that inherits from BaseTrigger, the class name will be added to triggers
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.trigger_types.append(cls)

    @staticmethod
    @abstractmethod
    def getAvailableDevices():
        pass

    # Optional method to release static resources upon exiting
    @staticmethod
    def releaseResources():
        pass

    def __init__(self, deviceID):
        self.initialized = False
        self.deviceID = deviceID


    def initialize(self, config: ConfigManager) -> bool:
        """
        Initializes the trigger and returns whether or not it was successful

        :param config: ConfigManager that stores settings to initialize trigger
        """
        raise NotImplementedError()


    @abstractmethod
    def execute(self, signal: Any) -> bool:
        raise NotImplementedError()


    def close(self):
        """
        Deactivates trigger and closes any trigger-dependent objects
        """
        self.active = False  # Overwrite for custom behavior
        logger.info(f"{type(self).__name__} closed")