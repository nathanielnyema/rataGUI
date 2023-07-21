from plugins import BasePlugin, ConfigManager

import os
import cv2
import numpy as np

from datetime import datetime

def draw_text(img, text,
          font=cv2.FONT_HERSHEY_PLAIN,
          pos=(0, 0),
          font_scale=3,
          font_thickness=2,
          text_color=(255, 255, 255),
          text_color_bg=(0, 0, 0)
          ):

    x, y = pos
    text_size, _ = cv2.getTextSize(text, font, font_scale, font_thickness)
    text_w, text_h = text_size
    cv2.rectangle(img, pos, (x + text_w, y + text_h), text_color_bg, -1)
    cv2.putText(img, text, (x, y + text_h + font_scale - 1), font, font_scale, text_color, font_thickness)

    return text_size

class MetadataWriter(BasePlugin):
    """
    Plugin that overlays metadata onto frames and/or into a log file
    """
    DEFAULT_CONFIG = {
        'Overlay Timestamp': False,
        'Overlay Frame Index': False,
    }

    def __init__(self, cam_widget, config, queue_size=0):
        super().__init__(cam_widget, config, queue_size)

        print("Started Metadata Writer for: {}".format(cam_widget.camera.cameraID))
            

    def execute(self, frame, metadata):

        img_h, img_w, num_ch = frame.shape

        for idx, (name, value) in enumerate(metadata.items()):
            key = 'Overlay ' + name
            if self.config.get(key):
                draw_text(frame, name+": "+str(value), pos=(img_h - 100*idx, 0))

        return frame, metadata

        # if self.config.get('save timestamp'):
        #     cv2.rectangle(frame, (img_w-190,0), (img_w,50), color=(0,0,0), thickness=-1)
        #     cv2.putText(frame, datetime.now().strftime('%H:%M:%S'), (img_w-185,37), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255,255,255), lineType=cv2.LINE_AA)
