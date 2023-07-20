from plugins import BasePlugin, ConfigManager
from config import FFMPEG_BINARY

from skvideo.io import FFmpegWriter

import os
import cv2
import numpy as np

from datetime import datetime

class VideoWriter(BasePlugin):
    """
    
    :param aspect_ratio: Whether to maintain frame aspect ratio or force into frame
    """

    DEFAULT_CONFIG = {
        'vcodec': ['libx264', 'libx265'],
        'framerate': 30,
        'speed (preset)': ["fast", "veryfast", "ultrafast", "medium", "slow", "slower", "veryslow"], # Defaults to first item
        'quality (0-51)': 32,
        'pixel format': ['yuv420p', 'yuv422p', 'yuv444p', 'rgb24', 'yuv420p10le', 'yuv422p10le', 'yuv444p10le', 'gray'],
        'save timestamp': False,
        'save directory': "videos",
        'filename': "",
    }

    DISPLAY_CONFIG_MAP = {
        'speed (preset)': 'preset',
        'quality (0-51)': 'crf',
        'pixel format': 'pix_fmt',
    }

    def __init__(self, cam_widget, config, queue_size=0):
        super().__init__(cam_widget, config, queue_size)
        print("Started VideoWriter for: {}".format(cam_widget.camera.cameraID))
        self.input_params = {'-framerate': '30'}
        self.output_params = {}

        for name, value in config.as_dict().items():
            prop_name = VideoWriter.DISPLAY_CONFIG_MAP.get(name)
            if prop_name is None:
                prop_name = name

            if prop_name == "save directory":
                self.save_dir = os.path.normpath(value)
            elif prop_name == "filename":
                if value == "": # default value
                    file_name = str(cam_widget.camera.cameraID) + "_" + datetime.now().strftime('%H-%M-%S')
                else:
                    file_name = value
            elif prop_name != "save timestamp":
                self.output_params['-'+prop_name] = str(value)
    
        if self.output_params.get("-vcodec") in ['libx264', 'libx265']:
            extension = ".mp4"
        # elif self.output_params.get("-vcodec") in ['huffyuv', 'rawvideo']: # lossless
        #     extension = ".yuv"
        
        os.makedirs(self.save_dir, exist_ok=True)
        self.file_path = os.path.join(self.save_dir, file_name + extension)
        count = 1
        while os.path.exists(self.file_path): # file already exists -> add copy
            self.file_path = os.path.join(self.save_dir, file_name + f" ({count})" + extension)
            count += 1

        print(self.output_params)
        self.writer = FFMPEG_Writer(str(self.file_path), input_dict=self.input_params, output_dict=self.output_params, debug=True)

    def execute(self, frame):
        # print("frame saved")

        img_h, img_w, num_ch = frame.shape

        if self.config.get('save timestamp'):
            cv2.rectangle(frame, (img_w-190,0), (img_w,50), color=(0,0,0), thickness=-1)
            cv2.putText(frame, datetime.now().strftime('%H:%M:%S'), (img_w-185,37), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255,255,255), lineType=cv2.LINE_AA)

        self.writer.write_frame(frame)

        return frame

    def close(self):
        print("Video writer closed")
        self.active = False
        self.writer.close()


import subprocess as sp
from shutil import which

class FFMPEG_Writer():
    """Write frames using ffmpeg as backend
    
    :param filename: path to write video file to
    :param input_dict: dictionary of input parameters to interpret data from Python
    :param output_dict: dictionary of output parameters to encode data to disk
    """

    def __init__(self, file_path, input_dict={}, output_dict={}, debug=True):
       
        self.file_path = os.path.abspath(file_path)
        dir_path = os.path.dirname(self.file_path)

        # Check for write permissions
        if not os.access(dir_path, os.W_OK): 
            print("Cannot write to directory: " + dir_path)

        self.input_dict = input_dict
        self.output_dict = output_dict
        self.debug = debug
        self.initialized = False

        if FFMPEG_BINARY is not None and "ffmpeg" in FFMPEG_BINARY:
            self._FFMPEG_PATH = FFMPEG_BINARY
        else:
            self._FFMPEG_PATH = which("ffmpeg")
        
        if self._FFMPEG_PATH is None:
            print("Could not find ffmpeg executable ... aborting")
            return


    def start_process(self, M, N, C):
        self.initialized = True

        if "-s" not in self.input_dict:
            self.input_dict["-s"] = str(N) + "x" + str(M)

        if "-pix_fmt" not in self.input_dict:
            if C == 1:
                self.input_dict["-pix_fmt"] = "gray"
            elif C == 2:
                self.input_dict["-pix_fmt"] = "ya8"
            elif C == 3:
                self.input_dict["-pix_fmt"] = "rgb24"
            elif C == 4:
                self.input_dict["-pix_fmt"] = "rgba"

        in_args = []
        for key, value in self.input_dict.items():
            in_args.append(key)
            in_args.append(value)
        
        out_args = []
        for key, value in self.output_dict.items():
            out_args.append(key)
            out_args.append(value)

        cmd = [self._FFMPEG_PATH, "-y", "-f", "rawvideo"] + in_args + ["-i", "-", '-an'] + out_args + [self.file_path]

        self._cmd = " ".join(cmd)
        print(self._cmd)
        if self.debug:
            cmd += ["-v", "warning"]
            self._proc = sp.Popen(cmd, stdin=sp.PIPE, stdout=sp.PIPE, stderr=None)
        else:
            cmd += ["-v", "error"]
            self._proc = sp.Popen(cmd, stdin=sp.PIPE, stdout=sp.DEVNULL, stderr=sp.STDOUT)


    def write_frame(self, img_array):
        """Writes one frame to the file."""

        M, N, C = img_array.shape

        if not self.initialized:
            self.start_process(M, N, C)

        # print(img_array.dtype)
        # img_array = img_array.astype(np.uint8)

        try:
            self._proc.stdin.write(img_array.tobytes())
        except IOError as err:
            # Show the command and stderr from pipe
            msg = f"{str(err)}\n\n FFMPEG COMMAND:{self._cmd}\n"
            raise IOError(msg)


    def close(self):
        """Closes the writer and terminates the subprocess if is still alive."""
        if self._proc is None or self._proc.poll() is not None:
            return
        
        if self._proc.stdin:
            self._proc.stdin.close()
        if self._proc.stderr:
            self._proc.stderr.close()

        self._proc.wait()
        self._proc = None