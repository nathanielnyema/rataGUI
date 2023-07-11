import os
import sys

from PyQt6.QtWidgets import QApplication
from UI.main_window import MainWindow

from cameras import BaseCamera
from plugins import BasePlugin

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Sort to ensure consistent ordering between operating systems
    BaseCamera.camera_models.sort(key=lambda c: c.__name__)
    BasePlugin.plugins.sort(key=lambda p: p.__name__)

    main_window = MainWindow(camera_models=BaseCamera.camera_models, plugins=BasePlugin.plugins)
    main_window.show()

    app.exit(app.exec())