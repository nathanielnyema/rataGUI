import os
import time
import json
import shutil
from datetime import datetime

from PyQt6 import QtWidgets, QtGui
from PyQt6.QtCore import QThreadPool, pyqtSlot, pyqtSignal

from rataGUI import rataGUI_icon, __version__
from rataGUI.utils import WorkerThread, slugify
from rataGUI.interface.design.Ui_CameraWidget import Ui_CameraWidget

import asyncio
from concurrent.futures import ThreadPoolExecutor

import logging

logger = logging.getLogger(__name__)

# process_pool = ProcessPoolExecutor()
thread_pool = ThreadPoolExecutor()

EXP_AVG_DECAY = 0.8


class CameraWidget(QtWidgets.QWidget, Ui_CameraWidget):
    """
    Encapsulates running camera object and its plugin processing pipeline by connecting Camera and Plugin APIs.

    :param camera: Camera object to extract frames from
    :param cam_config: ConfigManager that stores settings to initialize camera
    :param plugins: List of plugin types and ConfigManagers in processing pipeline to instantiate
    :param triggers: List of initialized trigger objects to execute when needed
    """

    # Signal for when camera and plugins have been initialized
    pipeline_initialized = pyqtSignal()

    def __init__(
        self, camera=None, cam_config=None, plugins=[], triggers=[], session_dir=""
    ):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(rataGUI_icon))

        # Directory for all data generated by widget
        self.session_dir = session_dir
        self.save_dir = os.path.join(session_dir, slugify(camera.getDisplayName()))
        os.makedirs(self.save_dir, exist_ok=True)

        # Set camera fields
        self.camera = camera
        self.camera_type = type(camera).__name__
        self.camera_config = cam_config

        # Make triggers available to camera pipeline
        self.triggers = triggers

        # Instantiate plugins with camera-specific settings
        self.plugins = []
        self.plugin_names = []
        self.failed_plugins = {}
        for Plugin, config in plugins:
            try:
                self.plugins.append(Plugin(self, config))
                self.plugin_names.append(Plugin.__name__)
            except Exception as err:
                config_dict = config.as_dict()
                config_dict["Error Message"] = repr(err)
                self.failed_plugins[Plugin.__name__] = config_dict
                logger.exception(err)
                logger.error(
                    f"Plugin: {Plugin.__name__} for camera: {self.camera.getDisplayName()} failed to initialize"
                )

        self.save_widget_data()  # Log metadata to file

        if "FrameDisplay" in self.plugin_names:
            self.show()  # Show widget UI if displaying
        self.avg_latency = 0  # in milliseconds
        self.active = True  # acquiring frames

        # Threadpool for asynchronous tasks with signals and slots
        self.threadpool = QThreadPool().globalInstance()

        # Start thread to initialize and process camera stream and plugin pipeline
        self.pipeline_thread = WorkerThread(self.start_camera_pipeline)

        # Close widget as soon as thread finishes and queues empty
        self.pipeline_thread.signals.finished.connect(self.close_widget)
        self.threadpool.start(self.pipeline_thread)

    @pyqtSlot()
    def start_camera_pipeline(self):
        try:
            success = self.camera.initializeCamera(
                self.camera_config, self.plugin_names
            )
            if not success:
                raise IOError(
                    f"Camera: {self.camera.getDisplayName()} failed to initialize"
                )
            self.camera._running = True
            self.camera.frames_acquired = 0
            self.pipeline_initialized.emit()
            logger.info(
                "Started pipeline for camera: {}".format(self.camera.getDisplayName())
            )
            asyncio.run(self.process_plugin_pipeline(), debug=False)

        except Exception as err:
            logger.exception(err)
            self.stop_camera_pipeline()

    def stop_camera_pipeline(self):
        # Signal to event loop to stop camera and plugins
        self.camera._running = False
        self.active = False
        # self.stop_plugins()
        self.clean_session_dir()

    async def acquire_frames(self):
        t0 = time.time()
        try:
            loop = asyncio.get_running_loop()
            while self.camera._running:
                if self.active:
                    status, frame = await loop.run_in_executor(
                        None, self.camera.readCamera
                    )
                    metadata = self.camera.getMetadata()
                    metadata["Camera Name"] = self.camera.getDisplayName()
                    metadata["Timestamp"] = datetime.now()
                    metadata["Average Latency"] = self.avg_latency

                    if status:
                        # print('Camera queue: ' + str(self.plugins[0].in_queue.qsize()))
                        # Send acquired frame to first plugin process in pipeline
                        await self.plugins[0].in_queue.put((frame, metadata))
                        await asyncio.sleep(0)
                    else:
                        raise IOError(
                            f"Frame not found on camera: {self.camera.getDisplayName()}"
                        )

                else:  # Pass to next coroutine
                    await asyncio.sleep(0)

        except Exception as err:
            logger.exception(err)
            logger.error(
                f"Exception occured acquiring frame from camera: {self.camera.getDisplayName()} ... stopping"
            )
            self.stop_camera_pipeline()

        t1 = time.time()
        logger.debug("FPS: " + str(self.camera.frames_acquired / (t1 - t0)))
        # Close camera when camera stops streaming
        self.camera.closeCamera()

    # Asynchronous execution loop for an arbitrary plugin
    async def plugin_process(self, plugin):
        loop = asyncio.get_running_loop()
        failures = 0
        while True:
            frame, metadata = await plugin.in_queue.get()
            try:
                # Execute plugin
                if plugin.active:
                    if plugin.blocking:  # possibly move queues outside plugins
                        result = await loop.run_in_executor(
                            None, plugin.process, frame, metadata
                        )
                    else:
                        result = plugin.process(frame, metadata)
                else:
                    result = (frame, metadata)

                # Send output to next plugin
                if plugin.out_queue != None:
                    await plugin.out_queue.put(result)
                else:
                    delta_t = datetime.now() - metadata["Timestamp"]
                    self.avg_latency = (
                        delta_t.total_seconds() * 1000 * EXP_AVG_DECAY
                        + self.avg_latency * (1 - EXP_AVG_DECAY)
                    )
            except Exception as err:
                logger.exception(err)
                failures += 1
                if failures > 5:  # close plugin after 5 failures
                    plugin.active = False
                    plugin.close()
            finally:
                plugin.in_queue.task_done()

    async def process_plugin_pipeline(self):
        # Add process to continuously acquire frames from camera
        acquisition_task = asyncio.create_task(self.acquire_frames())

        # Add all plugin processes (pipeline) to async event loop
        plugin_tasks = []
        for cur_plugin, next_plugin in zip(self.plugins, self.plugins[1:]):
            # Connect outputs and inputs of consecutive plugin pairs
            cur_plugin.out_queue = next_plugin.in_queue
            plugin_tasks.append(asyncio.create_task(self.plugin_process(cur_plugin)))
        # Add terminating plugin
        plugin_tasks.append(asyncio.create_task(self.plugin_process(self.plugins[-1])))

        # Wait until camera stops running
        await acquisition_task

        # Wait for plugins to finish processing
        for plugin in self.plugins:
            await plugin.in_queue.join()

        # Cancel idle plugin processes
        for task in plugin_tasks:
            task.cancel()

    def stop_plugins(self):
        for plugin in self.plugins:
            plugin.active = False

    def close_plugins(self):
        for plugin in self.plugins:
            try:
                plugin.close()
            except Exception as err:
                logger.exception(err)
                logger.error(f"Plugin: {type(plugin).__name__} failed to close")

    def close_widget(self):
        logger.info(
            "Stopped pipeline for camera: {}".format(self.camera.getDisplayName())
        )
        self.close_plugins()
        self.deleteLater()

    def clean_session_dir(self):
        if os.path.isdir(self.save_dir):
            dir_list = os.listdir(self.save_dir)
            metadata_file = slugify(self.camera.getDisplayName()) + "_metadata.json"
            if len(dir_list) == 0 or (
                len(dir_list) == 1 and metadata_file == dir_list[0]
            ):
                shutil.rmtree(self.save_dir)

                sess_dir_list = os.listdir(self.session_dir)
                if len(sess_dir_list) == 0 or (
                    len(sess_dir_list) == 1 and "settings" == sess_dir_list[0]
                ):
                    shutil.rmtree(self.session_dir)
            else:  # Log metadata to file
                self.save_widget_data()

    def save_widget_data(self):  # TODO: Compare settings before and after
        metadata = {}
        metadata["RataGUI Version"] = __version__
        metadata["Session Directory"] = self.session_dir
        metadata["Camera ID"] = str(self.camera.cameraID)
        metadata["Display Name"] = str(self.camera.display_name)
        metadata["Camera Type"] = self.camera_type
        metadata["Frames Acquired"] = str(self.camera.frames_acquired)
        metadata["Camera Settings"] = self.camera_config.as_dict()
        active_plugins = {}
        disabled_plugins = {}
        for name, plugin in zip(self.plugin_names, self.plugins):
            if plugin.active:
                active_plugins[name] = plugin.config
            else:
                disabled_plugins[name] = plugin.config
        metadata["Active Plugins"] = active_plugins
        metadata["Disabled Plugins"] = disabled_plugins
        metadata["Failed Plugins"] = self.failed_plugins

        metadata["Enabled Triggers"] = [str(trig.deviceID) for trig in self.triggers]

        file_path = os.path.join(
            self.save_dir, slugify(self.camera.getDisplayName()) + "_metadata.json"
        )
        with open(file_path, "w") as file:
            json.dump(metadata, file, indent=2)

        # enabled_triggers = {}
        # for trig in self.triggers:
        #     triggers = enabled_triggers.get(type(trig).__name__, [])
        #     triggers.append(trig.device)

    @pyqtSlot(QtGui.QImage)
    def set_window_pixmap(self, qt_image):
        pixmap = QtGui.QPixmap.fromImage(qt_image)
        self.video_frame.setPixmap(pixmap)


# async def repeat_trigger(trigger, interval):
#     """
#     Execute trigger every interval seconds.
#     """
#     while trigger.active:
#         await asyncio.gather(
#             trigger.execute,
#             asyncio.sleep(interval),
#         )
