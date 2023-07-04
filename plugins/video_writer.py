from datetime import datetime

from plugins import BasePlugin

import skvideo.io

class VideoWriter(BasePlugin):

    def __init__(self, cam_widget, queue_size=0, input_params={}, output_params={}):
        super().__init__(cam_widget, queue_size)
        print("Started VideoWriter for: {}".format(cam_widget.camera.cameraID))
        self.input_params = input_params
        self.output_params = output_params

        self.output_params = {"-vcodec": "libx264", "-crf": "28", "-preset": "ultrafast"}

        file_name = "videos/" + str(cam_widget.camera.cameraID) + "_" + datetime.now().strftime('%H-%M-%S') + ".mp4"
        self.writer = skvideo.io.FFmpegWriter(file_name, inputdict=input_params, outputdict=output_params)

    def execute(self, frame):
        # print("frame saved")
        self.writer.writeFrame(frame)

        return frame

    def stop(self):
        print("Video writer stopped")
        self.active = False