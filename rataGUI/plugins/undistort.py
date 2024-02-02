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
            param_file = os.path.normpath(
                os.path.abspath(cam_widget.camera_config.get("Camera Parameters File"))
            )

            f = loadmat(param_file)
            cam_mtx = f["K"].squeeze()
            rad = f["RadialDistortion"].squeeze()
            tan = f["TangentialDistortion"].squeeze()
            h, w = f["ImageSize"].squeeze()
            logger.debug(str((w, h)))

            dist_coeffs = np.concatenate((rad[:2], tan))
            if rad.size == 3:
                dist_coeffs = np.append(dist_coeffs, rad[-1])
            self.map1, self.map2 = cv.initUndistortRectifyMap(
                cam_mtx, dist_coeffs, None, cam_mtx, (w, h), cv.CV_32FC1
            )

        except Exception as err:
            logger.exception(err)
            logger.debug(
                "Unable to load Parameters File ... auto-disabling Undistort plugin"
            )
            self.active = False

    def process(self, frame, metadata):
        frame = cv.remap(frame, self.map1, self.map2, cv.INTER_LINEAR)
        metadata["Undistorted"] = True
        return frame, metadata
