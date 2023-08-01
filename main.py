import os
import sys
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