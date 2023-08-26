
import os
import sys
from datetime import datetime

import logging
logger = logging.getLogger(__name__)
logger.propagate = False
logger.setLevel(logging.DEBUG)

# set up logging DEBUG messages or higher to sys.stdout
console = logging.StreamHandler(sys.stdout)
console.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)-8s %(module)-16s %(message)s')
console.setFormatter(formatter)
logger.addHandler(console)

# set up logging INFO messages or higher to log file
def configure_file_logger():
    file_name = "info_" + datetime.now().strftime("%Y_%m_%d-%H_%M_%S") + ".log"
    logging_file = os.path.join(launch_config["Save Directory"], file_name)
    file_handler = logging.FileHandler(logging_file)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s.%(msecs)03d  %(levelname)-8s %(module)-16s %(message)s', '%Y-%m-%d,%H:%M:%S')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.info(f"Logging to {os.path.relpath(logging_file)}")


import json

config_path = os.path.join(os.path.dirname(__file__), "launch_config.json")
launch_config = {}
if os.path.isfile(config_path) and os.stat(config_path).st_size > 0:
    with open(config_path, 'r') as file:
        launch_config = json.load(file)
    os.makedirs(launch_config["Save Directory"], exist_ok=True)

# Path to rataGUI project icon
rataGUI_icon = os.path.join(os.path.dirname(__file__), 'interface/design/ratagui-icon.png')