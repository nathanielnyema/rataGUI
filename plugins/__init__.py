import os
import traceback

from .base_plugin import BasePlugin

from importlib import util
from config import active_plugins

# Automatically load camera modules
def load_module(path):
    name = os.path.split(path)[-1]
    spec = util.spec_from_file_location(name, path)
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Get current path
path = os.path.abspath(__file__)
dirpath = os.path.dirname(path)

if len(active_plugins) == 0:
    for fname in os.listdir(dirpath):
        # Load only "real modules"
        if not fname.startswith('.') and not fname.startswith('__') and fname.endswith('.py'):
            try:
                load_module(os.path.join(dirpath, fname))
            except ModuleNotFoundError:
                print(f"Unable to load plugin module {fname}")
            except Exception:
                traceback.print_exc()
else:
    for plugin in active_plugins:
        # TODO
        pass  