import os
import sys

import logging.handlers
from rataGUI.config import logging_file

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
logging_file = os.path.abspath(logging_file)
os.makedirs(os.path.dirname(logging_file), exist_ok=True)
with open(logging_file, 'a') as f:
    f.write('\n\n')
file_handler = logging.handlers.RotatingFileHandler(logging_file, mode='a', maxBytes=1e7, backupCount=3)
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s.%(msecs)03d  %(levelname)-8s %(module)-16s %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

logger.info(f"Logging to {logging_file}")