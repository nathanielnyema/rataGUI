# from UI.design.Ui_FrameDisplay import Ui_FrameDisplay

from plugins import BasePlugin

class VideoWriter(BasePlugin):

    def __init__(self):
        super().__init__()
        self.writer = skvideo.io.FFmpegWriter(file_name, inputdict=input_params, outputdict=output_params)

    def execute(self, frame):
        pass

    def stop(self):
        print("Video writer stopped")