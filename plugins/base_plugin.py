from abc import ABC, abstractmethod
from typing import Any
import numpy.typing as npt

from asyncio import Queue

class BasePlugin(ABC):
    """
    Abstract plugin class with generic functions. All custom plugins should be subclassed
    to ensure that all the necessary methods are available to the camera acquistion engine.
    """

    # Static variable to contain all plugin subclasses
    plugins = []

    # For every class that inherits from the current,
    # the class name will be added to plugins
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.plugins.append(cls)

    # @abstractmethod (Make cam_window required)
    def __init__(self):
        self.in_queue = Queue()
        self.out_queue = None

    @abstractmethod
    def execute(self):
        pass

    @abstractmethod
    def stop(self):
        pass