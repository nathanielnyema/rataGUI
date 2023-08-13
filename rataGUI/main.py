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


logger = logging.getLogger()
logger.setLevel(logging.INFO)

# set up logging INFO messages or higher to log file
logging_file = os.path.abspath(logging_file)
os.makedirs(os.path.dirname(logging_file), exist_ok=True)

file_handler = logging.FileHandler(logging_file, 'w')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s.%(msecs)03d  %(levelname)-8s %(name)-24s %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# set up logging INFO messages or higher to sys.stdout
console = logging.StreamHandler(sys.stdout)
console.setLevel(logging.INFO)
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