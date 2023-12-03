from rataGUI.plugins.base_plugin import BasePlugin
import numpy as np
import cv2 as cv
from scipy.io import loadmat
import os

import logging
logger = logging.getLogger(__name__)


class Undistort(BasePlugin):


    def __init__(self, cam_widget, config, queue_size=0):
        super().__init__(cam_widget, config, queue_size)
        logger.debug(str(BasePlugin.modules.keys()))

        try:

            param_file = os.path.normpath(os.path.abspath(cam_widget.camera_config.get("Camera Parameters File")))

            f = loadmat(param_file)
            self.cam_mtx = f["K"].squeeze()
            rad = f["RadialDistortion"].squeeze()
            tan = f["TangentialDistortion"].squeeze()
            
            self.dist_coeffs = np.concatenate((rad[:2], tan))
            if rad.size == 3: 
                self.dist_coeffs = np.append(self.dist_coeffs, rad[-1])

        except Exception as err:
            logger.exception(err)
            logger.debug("Unable to Parameters File ... auto-disabling DLC Inference plugin")
            self.active = False


    def process(self, frame, metadata):

        frame = cv.undistort(frame, self.cam_mtx, self.dist_coeffs)
        metadata["Undistorted"] = True

        return frame, metadata