from rataGUI.plugins.base_plugin import BasePlugin
from rataGUI.utils import slugify
from rataGUI import launch_config

import os
import numpy as np
from datetime import datetime

import logging
logger = logging.getLogger(__name__)

class VideoWriter(BasePlugin):
    """
    Plugin that writes frames to video file using FFMPEG

    :param vcodec: Video codec used by ffmpeg binary
    """

    DEFAULT_CONFIG = {
        'save directory': "videos",
        'filename': "",
        'vcodec': ['libx264', 'libx265', 'h264_nvenc', 'hevc_nvenc', 'rawvideo'],
        'framerate': 30,
        'speed (preset)': ["fast", "veryfast", "ultrafast", "medium", "slow", "slower", "veryslow"], # Defaults to first item
        'quality (0-51)': (32, 0, 51),
        'pixel format': ['yuv420p', 'yuv422p', 'yuv444p', 'rgb24', 'yuv420p10le', 'yuv422p10le', 'yuv444p10le', 'gray'],
    }

    DISPLAY_CONFIG_MAP = {
        'speed (preset)': 'preset',
        'quality (0-51)': 'crf',
        'pixel format': 'pix_fmt',
    }

    def __init__(self, cam_widget, config, queue_size=0):
        super().__init__(cam_widget, config, queue_size)
        self.input_params = {}
        self.output_params = {}

        for name, value in config.as_dict().items():
            prop_name = VideoWriter.DISPLAY_CONFIG_MAP.get(name)
            if prop_name is None:
                prop_name = name

            if prop_name == "save directory":
                self.save_dir = os.path.normpath(value)
            elif prop_name == "filename":
                if value == "": # default value
                    print(cam_widget.camera.getDisplayName())
                    file_name = slugify(cam_widget.camera.getDisplayName()) + "_" + datetime.now().strftime('%H-%M-%S')
                else:
                    file_name = slugify(value)
            elif prop_name in ["framerate",] and value >= 0: # input parameters
                self.input_params['-'+prop_name] = str(value)

            else: # output parameters
                self.output_params['-'+prop_name] = str(value)
    
        extension = ".mp4"

        # Configure codec-specific parameters
        vcodec = self.output_params.get("-vcodec")
        if vcodec in ['rawvideo']:
            extension = ".raw"
        # if vcodec in ['h264_nvenc', 'hevc_nvenc']:
        #     self.output_params['-cq'] = self.output_params.pop('-crf')

        if not os.path.isabs(self.save_dir):
            self.save_dir = os.path.join(launch_config["Save Directory"], self.save_dir)

        os.makedirs(self.save_dir, exist_ok=True)
        self.file_path = os.path.join(self.save_dir, file_name + extension)
        count = 1
        while os.path.exists(self.file_path): # file already exists -> add copy
            self.file_path = os.path.join(self.save_dir, file_name + f" ({count})" + extension)
            count += 1

        self.writer = FFMPEG_Writer(str(self.file_path), input_dict=self.input_params, output_dict=self.output_params, verbosity=0)


    def process(self, frame, metadata):

        self.writer.write_frame(frame)
        return frame, metadata


    def close(self):
        logger.info("Video writer closed")
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

    def __init__(self, file_path, input_dict={}, output_dict={}, verbosity=0):
       
        self.file_path = os.path.abspath(os.path.normpath(file_path))
        dir_path = os.path.dirname(self.file_path)

        # Check for write permissions
        if not os.access(dir_path, os.W_OK): 
            logger.error("Cannot write to directory: " + dir_path)

        self.input_dict = input_dict
        self.output_dict = output_dict
        self.verbosity = verbosity
        self.initialized = False

        self._FFMPEG_PATH = which("ffmpeg")
        # if os.path.isfile(launch_config["FFMPEG Path"]):
        #     self._FFMPEG_PATH = launch_config["FFMPEG Path"]

        if self._FFMPEG_PATH is None:
            raise IOError("Could not find ffmpeg executable in the environment PATH.")


    def start_process(self, H, W, C):
        self.initialized = True

        if "-s" not in self.input_dict:
            self.input_dict["-s"] = str(W) + "x" + str(H)

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
        
        if self.verbosity >= 2:
            logger.info(cmd)
            self._proc = sp.Popen(cmd, stdin=sp.PIPE, stdout=sp.PIPE, stderr=None)
        elif self.verbosity == 1:
            cmd += ["-v", "warning"]
            logger.info(cmd)
            self._proc = sp.Popen(cmd, stdin=sp.PIPE, stdout=sp.PIPE, stderr=None)
        else:
            self._proc = sp.Popen(cmd, stdin=sp.PIPE, stdout=sp.DEVNULL, stderr=sp.STDOUT)


    def write_frame(self, img_array):
        """Writes one frame to the file."""

        H, W, C = img_array.shape

        if not self.initialized:
            self.start_process(H, W, C)

        # print(img_array.dtype)
        img_array = img_array.astype(np.uint8)

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