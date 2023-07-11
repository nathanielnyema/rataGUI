import os
import sys
import darkdetect

from PyQt6.QtWidgets import QApplication
from interface.main_window import MainWindow

from cameras import BaseCamera
from plugins import BasePlugin

if __name__ == '__main__':
    QApplication.setStyle('Fusion')
    app = QApplication(sys.argv)
    
    # Sort to ensure consistent ordering between operating systems
    BaseCamera.camera_models.sort(key=lambda c: c.__name__)
    BasePlugin.plugins.sort(key=lambda p: p.__name__)

    main_window = MainWindow(camera_models=BaseCamera.camera_models, plugins=BasePlugin.plugins, dark_mode=darkdetect.isDark())
    main_window.show()

    app.exit(app.exec())