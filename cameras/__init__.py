import os
import traceback

__all__ = ['ConfigManager', 'BaseCamera']
from pyqtconfig import ConfigManager
from .BaseCamera import BaseCamera

from importlib import util
from config import enabled_camera_models

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
                print(f"Unable to load camera module {fname}")
            except Exception:
                traceback.print_exc()