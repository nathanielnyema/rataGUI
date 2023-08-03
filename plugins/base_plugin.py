from abc import ABC, abstractmethod

from asyncio import Queue
from PyQt6.QtWidgets import QWidget
from pyqtconfig import ConfigManager

from typing import Dict, Tuple
from numpy.typing import NDArray

class BasePlugin(ABC):
    """
    Abstract plugin class with generic functions. All custom plugins should be subclassed
    to ensure that all the necessary methods are available to the processing pipeline.
    """

    # Static variable to contain all plugin subclasses
    plugins = []

    # For every class that inherits from BasePlugin, the class name will be added to triggers
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.plugins.append(cls)

    # @staticmethod
    # def execute_process(plugin, frame, metadata):
    #     return plugin.process(frame, metadata)

    @abstractmethod
    def __init__(self, cam_widget: QWidget, config: ConfigManager, queue_size=0):
        self.active = True
        self.cpu_bound = False
        self.io_bound = False
        self.config = config
        self.in_queue = Queue(queue_size)
        self.out_queue = None

    @abstractmethod
    def process(self, frame: NDArray, metadata: Dict) -> Tuple[NDArray, Dict]:
        raise NotImplementedError()

    def close(self):
        """
        Deactivates plugin and closes any plugin-dependent objects
        """
        self.active = False  # Overwrite for custom behavior
        print(f"{type(self).__name__} closed")

    # @abstractmethod
    # def close(self):
    #     raise NotImplementedError()