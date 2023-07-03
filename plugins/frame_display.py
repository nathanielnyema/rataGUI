from UI.design.Ui_FrameDisplay import Ui_FrameDisplay

from plugins import BasePlugin

import cv2
from datetime import datetime
from PyQt6 import QtWidgets, QtGui
from PyQt6.QtCore import Qt

class FrameDisplay(BasePlugin):

    def __init__(self, cam_window: QtWidgets.QWidget):
        super().__init__()
        self.video_frame = cam_window.video_frame
        self.frame_width = cam_window.frame_width
        self.frame_height = cam_window.frame_height

    def execute(self, frame):
        """Sets pixmap image to video frame"""
        # Get image dimensions
        img_h, img_w, num_ch = frame.shape

        # # Possibly convert color here if other plugins use different colorspaces
        # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # TODO: Add timestamp to frame
        cv2.rectangle(frame, (img_w-190,0), (img_w,50), color=(0,0,0), thickness=-1)
        cv2.putText(frame, datetime.now().strftime('%H:%M:%S'), (img_w-185,37), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255,255,255), lineType=cv2.LINE_AA)

        # Convert to pixmap and set to video frame
        bytes_per_line = num_ch * img_w
        qt_image = QtGui.QImage(frame.data, img_w, img_h, bytes_per_line, QtGui.QImage.Format.Format_RGB888)
        qt_image = qt_image.scaled(self.frame_width, self.frame_height, Qt.AspectRatioMode.KeepAspectRatio)
        pixmap = QtGui.QPixmap.fromImage(qt_image)
        self.video_frame.setPixmap(pixmap)

    def stop(self):
        print("Frame display stopped")