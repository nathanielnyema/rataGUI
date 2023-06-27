from UI.design.Ui_FrameDisplay import Ui_FrameDisplay

from plugins import BasePlugin

class FrameDisplay(BasePlugin):

    def __init__(self, deque_size=100):
        super().__init__(deque_size)

    def start_process(self):
        print("Frame display started")