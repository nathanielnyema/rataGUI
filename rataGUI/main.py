import sys
import argparse
import darkdetect
from PyQt6.QtWidgets import QApplication
from .interface.main_window import MainWindow

from rataGUI.cameras.BaseCamera import BaseCamera
from rataGUI.plugins.base_plugin import BasePlugin
from rataGUI.triggers.base_trigger import BaseTrigger

import logging
logger = logging.getLogger(__package__)


def main(args = None):
    """Starts new instance of RataGUI"""

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--reset",
        help=(
            "Reset session settings back to defaults."
        ),
        action="store_const",
        const=True,
        default=False,
    )

    args = parser.parse_args(args)

    logger.info("Starting RataGUI session")
    QApplication.setStyle('Fusion')
    app = QApplication([])

    main_window = MainWindow(camera_models=BaseCamera.camera_models, plugins=BasePlugin.plugins, 
                             trigger_types=BaseTrigger.trigger_types, dark_mode=darkdetect.isDark())
    main_window.show()

    app.exit(app.exec())


if __name__ == "__main__":
    main(sys.argv[1:])