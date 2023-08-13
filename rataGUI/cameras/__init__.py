"""
Loads camera modules listed in config.py (defaults to all camera models if none are specified) 

Stores utility functions available to every camera model in folder
"""

__all__ = ['ConfigManager', 'BaseCamera']
from pyqtconfig import ConfigManager
from .BaseCamera import BaseCamera
from config import enabled_camera_models

import logging
logger = logging.getLogger(__name__)

import os
from importlib import util

# Automatically load camera modules
def load_module(path):
    name = os.path.split(path)[-1]
    spec = util.spec_from_file_location(name, path)
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Get current path
path = os.path.relpath(__file__)
dirpath = os.path.dirname(path)

for fname in os.listdir(dirpath):
    # Load only "real modules"
    if not fname.startswith('.') and not fname.startswith('__') and fname.endswith('.py'):
        if len(enabled_camera_models) == 0 or fname in enabled_camera_models:
            try:
                load_module(os.path.join(dirpath, fname))
            except ModuleNotFoundError:
                logger.info(f"Unable to load camera module {fname}")
            except Exception as err:
                logger.exception(err)