"""
Loads plugin modules listed in config.py (defaults to all plugins if none are specified) 

Stores utility functions available to every plugin in folder
"""

import os
import traceback

from .base_plugin import BasePlugin

from importlib import util
from config import active_plugins

# Automatically load plugin modules
def load_module(path):
    name = os.path.split(path)[-1]
    spec = util.spec_from_file_location(name, path)
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Asynchronous execution loop for an arbitrary plugin 
async def plugin_process(plugin):
    while True:
        frame = await plugin.in_queue.get()

        # TODO: Add plugin-specific data

        # TODO: Parallelize with Thread Executor

        # Execute plugin
        if plugin.active:
            result = plugin.execute(frame)
        # Send output to next plugin
        if plugin.out_queue != None:
            await plugin.out_queue.put(result)
        
        plugin.in_queue.task_done()


# Get current path
path = os.path.relpath(__file__)
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