import os
import sys

import darkdetect
from PyQt6.QtWidgets import QApplication
from interface.main_window import MainWindow

from cameras import BaseCamera
from plugins import BasePlugin
from triggers import BaseTrigger

# import logging.config
from config import logging_file

# logging.config.dictConfig({
#     'version': 1,
#     'disable_existing_loggers': True,
# })

import logging

# set up logging INFO messages or higher to log file
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# # Silence other loggers
# for log_name, log_obj in logging.Logger.manager.loggerDict.items():
#      if log_name != 'rataGUI':
#           log_obj.disabled = True


logging_file = os.path.abspath(logging_file)
os.makedirs(os.path.dirname(logging_file), exist_ok=True)

file_handler = logging.FileHandler(logging_file, 'a')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s.%(msecs)03d  %(levelname)-8s %(name)-24s %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# logging.basicConfig(level=logging.INFO,
#                     format='%(asctime)s.%(msecs)03d  %(levelname)-8s %(name)-24s %(message)s',
#                     datefmt='%m-%d %H:%M:%S',
#                     filename=logging_file,
#                     filemode='w')

# set up logging DEBUG messages or higher to sys.stderr
console = logging.StreamHandler(sys.stdout)
console.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)-8s %(name)-24s %(message)s')
console.setFormatter(formatter)
logger.addHandler(console)


# import darkdetect
# from PyQt6.QtWidgets import QApplication
# from interface.main_window import MainWindow

if __name__ == '__main__':
    QApplication.setStyle('Fusion')
    app = QApplication(sys.argv)

    main_window = MainWindow(camera_models=BaseCamera.camera_models, plugins=BasePlugin.plugins, 
                             trigger_types=BaseTrigger.trigger_types, dark_mode=darkdetect.isDark())
    main_window.show()

    app.exit(app.exec())