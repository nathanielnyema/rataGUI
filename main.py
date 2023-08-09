import os
import sys


import logging
from config import logging_file

# set up logging INFO messages or higher to log file
logging_file = os.path.abspath(logging_file)
os.makedirs(os.path.dirname(logging_file), exist_ok=True)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s.%(msecs)03d  %(levelname)-8s %(name)-24s %(message)s',
                    datefmt='%m-%d %H:%M:%S',
                    filename=logging_file,
                    filemode='w')

# set up logging DEBUG messages or higher to sys.stderr
console = logging.StreamHandler(sys.stdout)
console.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)-8s %(name)-20s %(message)s')
console.setFormatter(formatter)
logging.getLogger().addHandler(console)


import darkdetect
from PyQt6.QtWidgets import QApplication
from interface.main_window import MainWindow

from cameras import BaseCamera
from plugins import BasePlugin
from triggers import BaseTrigger

if __name__ == '__main__':
    QApplication.setStyle('Fusion')
    app = QApplication(sys.argv)

    main_window = MainWindow(camera_models=BaseCamera.camera_models, plugins=BasePlugin.plugins, 
                             trigger_types=BaseTrigger.trigger_types, dark_mode=darkdetect.isDark())
    main_window.show()

    app.exit(app.exec())