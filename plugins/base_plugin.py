from abc import ABC, abstractmethod
from typing import Any
import numpy.typing as npt

from collections import deque

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

    def __init__(self, deque_size=100):
        self.frames = deque(maxlen = deque_size)

    @abstractmethod
    def start_process(self):
        pass