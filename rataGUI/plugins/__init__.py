"""
Loads plugin modules listed in config.py (defaults to all plugins if none are specified) 

Stores utility functions available to every plugin in folder
"""

import logging
logger = logging.getLogger(__name__)

import os
from importlib import util
from rataGUI.config import enabled_plugins


# Automatically load plugin modules
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
        if len(enabled_plugins) == 0 or fname in enabled_plugins:
            try:
                load_module(os.path.join(dirpath, fname))
                logger.info(f"Loaded plugin module {fname}")
            except ModuleNotFoundError as err:
                logger.warning(f"Unable to load plugin module {fname}")
                logger.debug(err.msg)
            except Exception as err:
                logger.exception(err)