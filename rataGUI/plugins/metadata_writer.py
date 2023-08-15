from rataGUI.plugins.base_plugin import BasePlugin

import cv2

import logging
logger = logging.getLogger(__name__)


class MetadataWriter(BasePlugin):
    """
    Plugin that overlays metadata onto frames and/or into a log file
    """
    DEFAULT_CONFIG = {
        'Overlay Frame Index': False,
        'Abbreviate': False,
        'Overlay Timestamp': False,
        'Include date': False,
        'Overlay Camera Name': False,
    }

    def __init__(self, cam_widget, config, queue_size=0):
        super().__init__(cam_widget, config, queue_size)


    def process(self, frame, metadata):

        img_h, img_w, num_ch = frame.shape

        abbreviate = self.config.get('Abbreviate')
        count = 0
        for name, value in metadata.items():
            key = 'Overlay ' + name

            # # check if write function was passed with data
            # if isinstance(value, tuple) and len(value) == 2:
            #     # don't do anything if 2nd element is not a function
            #     if callable(value[1]):
            #         write_function = value[1]
            #         write_function()

            # Check config to determine what to write
            if self.config.get(key):
                if name == "Timestamp":
                    if self.config.get('Include date'):
                        overlay = value.strftime('%m/%d/%y-%H:%M:%S.%f')
                    else:
                        overlay = value.strftime('%H:%M:%S.%f')
                    
                    if abbreviate:
                        overlay = overlay
                else:
                    if abbreviate:
                        name = ''.join([word[0] for word in name.split(' ')]) # find initials
                    overlay = name+": "+str(value)

                (text_w, text_h), _ = cv2.getTextSize(overlay, cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.75, thickness=2)
                pos = (6, img_h - count*(text_h+6))
                cv2.rectangle(frame, pos, (pos[0] + text_w, pos[1] - text_h), (0, 0, 0), cv2.FILLED)
                cv2.putText(frame, overlay, pos, cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.75, color=(255, 255, 255), thickness=2, lineType=cv2.LINE_4)
                count += 1

        return frame, metadata


    def close(self):
        logger.info("Metadata writer closed")
        self.active = False