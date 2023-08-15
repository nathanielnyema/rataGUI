"""
Loads trigger modules listed in config.py

Stores utility functions available to every trigger in folder
"""

import logging
logger = logging.getLogger(__name__)

import os
from importlib import util
from rataGUI.config import enabled_trigger_types


# Automatically load trigger modules
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
        if fname in enabled_trigger_types: # len(enabled_trigger_types) == 0 or
            try:
                load_module(os.path.join(dirpath, fname))
                logger.info(f"Loaded trigger module {fname}")
            except ModuleNotFoundError as err:
                logger.warning(f"Unable to load trigger module {fname}")
                logger.error(err.msg)
            except Exception as err:
                logger.exception(err)