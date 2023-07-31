from abc import ABC, abstractmethod

from asyncio import Queue
from PyQt6.QtWidgets import QWidget
from pyqtconfig import ConfigManager

from typing import Dict, Tuple
from numpy.typing import NDArray

class BaseTrigger(ABC):
    """
    Abstract trigger class with generic functions. All custom triggers should be subclassed
    to ensure that all the necessary methods are available to the triggering interface.
    """

    # Static variable to contain all trigger subclasses
    triggers = []

    # For every class that inherits from BaseTrigger, the class name will be added to triggers
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.plugins.append(cls)

    @abstractmethod
    def __init__(self, interval: float, config: ConfigManager):
        self.active = True
        self.config = config

    @abstractmethod
    def execute(self, frame: NDArray, metadata: Dict) -> Tuple[NDArray, Dict]:
        raise NotImplementedError()

    @abstractmethod
    def close(self):
        raise NotImplementedError()