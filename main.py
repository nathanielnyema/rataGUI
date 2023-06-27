import os
import sys

from PyQt6.QtWidgets import QApplication
from UI.main_window import MainWindow

from cameras import BaseCamera
from plugins import BasePlugin

if __name__ == '__main__':
    app = QApplication(sys.argv)

    main_window = MainWindow(camera_types=BaseCamera.camera_types, plugins=BasePlugin.plugins)
    main_window.show()

    app.exit(app.exec())