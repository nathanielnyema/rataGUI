"""
Loads trigger modules listed in config.py

Stores utility functions available to every trigger in folder
"""

import logging
logger = logging.getLogger(__name__)

import os
from importlib import util
from rataGUI.config import enabled_trigger_types

import pkgutil
import sys


# def load_all_modules_from_dir(dirname):
#     for importer, package_name, _ in pkgutil.iter_modules([dirname]):
#         full_package_name = '%s.%s' % (dirname, package_name)
#         if full_package_name not in sys.modules:
#             try:
#                 module = importer.find_module(package_name
#                             ).load_module(package_name)
#             except ModuleNotFoundError as err:
#                 logger.warning(f"Unable to load trigger module {package_name}")
#                 logger.error(err.msg)
#             except Exception as err:
#                 logger.exception(err)
#             print(module)

# Get current path
path = os.path.relpath(__file__)
dirpath = os.path.dirname(path)
# load_all_modules_from_dir(dirpath)


# Automatically load trigger modules
def load_module(path):
    name = os.path.split(path)[-1]
    spec = util.spec_from_file_location(name, path)
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


for fname in os.listdir(dirpath):
    # Load only "real modules"
    if not fname.startswith('.') and not fname.startswith('__') and fname.endswith('.py'):
        if len(enabled_trigger_types) == 0: # fname in enabled_trigger_types: # len(enabled_trigger_types) == 0 or
            try:
                load_module(os.path.join(dirpath, fname))
                logger.info(f"Loaded trigger module {fname}")
            except ModuleNotFoundError as err:
                logger.warning(f"Unable to load trigger module {fname}")
                logger.error(err.msg)
            except Exception as err:
                logger.exception(err)