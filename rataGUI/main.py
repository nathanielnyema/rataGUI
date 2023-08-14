import sys

from config import logging_file
from utils import get_project_logger
logger = get_project_logger(logging_file)

from cameras import BaseCamera
from plugins import BasePlugin
from triggers import BaseTrigger

import darkdetect
from PyQt6.QtWidgets import QApplication
from interface.main_window import MainWindow


if __name__ == '__main__':
    logger.info("Starting RataGUI session")
    QApplication.setStyle('Fusion')
    app = QApplication(sys.argv)

    main_window = MainWindow(camera_models=BaseCamera.camera_models, plugins=BasePlugin.plugins, 
                             trigger_types=BaseTrigger.trigger_types, dark_mode=darkdetect.isDark())
    main_window.show()

    app.exit(app.exec())