from abc import ABC, abstractmethod

from asyncio import Queue
from PyQt6.QtWidgets import QWidget
from pyqtconfig import ConfigManager

from typing import Dict, Tuple
from numpy.typing import NDArray

import logging
logger = logging.getLogger(__name__)

class BasePlugin(ABC):
    """
    Abstract plugin class with generic functions. All custom plugins should be subclassed
    to ensure that all the necessary methods are available to the processing pipeline.
    """

    # Static variable to contain all plugin subclasses
    plugins = []

    # # Overwrite with any metadata produced by plugin
    # @staticmethod
    # def get_metadata_names(self) -> list:
    #     """ 
    #     Returns list of metadata names produced by plugin (ex. DLC Pose)
        
    #     Used to populate metadata 
    #     """
    #     return list()


    # For every class that inherits from BasePlugin, the class name will be added to triggers
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.plugins.append(cls)

    # @staticmethod
    # def execute_process(plugin, frame, metadata):
    #     return plugin.process(frame, metadata)

    def __init__(self, cam_widget: QWidget, config: ConfigManager, queue_size=0):
        logger.info(f"Started {type(self).__name__} for: {cam_widget.camera.getDisplayName()}")
        self.active = True
        self.blocking = False
        self.config = config
        self.in_queue = Queue(queue_size)
        self.out_queue = None


    @abstractmethod
    def process(self, frame: NDArray, metadata: Dict) -> Tuple[NDArray, Dict]:
        raise NotImplementedError("Plugin process function not implemented")

    # Overrite for custom behavior
    def close(self):
        """ Deactivates plugin and closes any plugin-dependent objects """
        self.active = False
        logger.info(f"{type(self).__name__} closed")