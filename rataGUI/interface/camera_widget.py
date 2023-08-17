# import sys
import time
from datetime import datetime

from PyQt6 import QtWidgets, QtGui
from PyQt6.QtCore import Qt, QThreadPool, QObject, QTimer, pyqtSlot, pyqtSignal, QRect

from rataGUI.utils import WorkerThread
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
    :param plugins: List of plugin types and configs in processing pipeline to instantiate
    :param triggers: List of initialized trigger objects to execute when needed
    """

    # Signal for when camera and plugins have been initialized
    pipeline_initialized = pyqtSignal()

    def __init__(self, camera=None, cam_config=None, plugins=[], triggers=[]):
        super().__init__()
        self.setupUi(self)

        # Set widget fields
        self.frame_width = self.frameGeometry().width()
        self.frame_height = self.frameGeometry().height()

        # Set camera fields
        self.camera = camera
        self.camera_model = type(camera).__name__
        self.camera_config = cam_config

        # Make triggers available to camera pipeline
        self.triggers = triggers

        # Instantiate plugins with camera-specific settings
        self.plugins = []
        self.plugin_names = []
        for Plugin, config in plugins:
            try:
                self.plugins.append(Plugin(self, config))
                self.plugin_names.append(Plugin.__name__)
            except Exception as err:
                logger.exception(err)
                logger.error(f"Plugin: {type(Plugin).__name__} for camera: {self.camera.getDisplayName()} failed to initialize")


        if "FrameDisplay" in self.plugin_names: self.show() # Show widget UI if displaying 
        self.avg_latency = 0    # in milliseconds
        self.active = True      # acquiring frames

        # Threadpool for asynchronous tasks with signals and slots
        self.threadpool = QThreadPool().globalInstance()


        # Start thread to initialize and process camera stream and plugin pipeline
        self.pipeline_thread = WorkerThread(self.start_camera_pipeline)
        self.threadpool.start(self.pipeline_thread)


    @pyqtSlot()
    def start_camera_pipeline(self):
        try:
            success = self.camera.initializeCamera(self.camera_config, self.plugin_names)
            if not success:
                raise IOError(f"Camera: {self.camera.getDisplayName()} failed to initialize")
            self.camera._running = True
            self.pipeline_initialized.emit()
            logger.info('Started pipeline for camera: {}'.format(self.camera.getDisplayName()))
            asyncio.run(self.process_plugin_pipeline(), debug=False)

        except Exception as err:
            logger.exception(err)
            self.close_widget()

    def stop_camera_pipeline(self):
        logger.info('Stopped pipeline for camera: {}'.format(self.camera.getDisplayName()))
        # Signal to event loop to stop camera and plugins
        self.camera._running = False
        self.active = False
        self.stop_plugins()


    async def acquire_frames(self):
        try:
            loop = asyncio.get_running_loop()
            t0 = time.time()
            while self.camera._running:
                if self.active:
                    status, frame = await loop.run_in_executor(None, self.camera.readCamera)
                    metadata = self.camera.getMetadata()
                    metadata['Camera Name'] = self.camera.getDisplayName()
                    metadata['Timestamp'] = datetime.now()
                    metadata['Average Latency'] = self.avg_latency

                    if status: 
                        # Send acquired frame to first plugin process in pipeline
                        # print('Camera queue: ' + str(self.plugins[0].in_queue.qsize()))
                        await self.plugins[0].in_queue.put((frame, metadata))
                        await asyncio.sleep(0)
                    else:
                        raise IOError("Camera frame not found ... stopping")

                else: # Pass to next coroutine
                    await asyncio.sleep(0)

            t1 = time.time()
            logger.debug('FPS: '+str(self.camera.frames_acquired / (t1-t0)))
            # Close camera when camera stops streaming
            self.camera.closeCamera()

        except Exception as err:
            logger.exception(err)


    # Asynchronous execution loop for an arbitrary plugin 
    async def plugin_process(self, plugin):
        loop = asyncio.get_running_loop()
        failures = 0
        while True:
            frame, metadata = await plugin.in_queue.get()
            # print(f'{type(plugin).__name__} queue: ' + str(plugin.in_queue.qsize()))
            try:
                # Execute plugin
                if plugin.active:
                    if plugin.blocking: # possibly move queues outside plugins
                        result = await loop.run_in_executor(None, plugin.process, frame, metadata)
                    else:
                        result = plugin.process(frame, metadata)
                else:
                    result = (frame, metadata)

                # Send output to next plugin
                if plugin.out_queue != None:
                    await plugin.out_queue.put(result)
                else:
                    delta_t = datetime.now() - metadata['Timestamp']
                    self.avg_latency = delta_t.total_seconds()*1000 * EXP_AVG_DECAY + self.avg_latency * (1 - EXP_AVG_DECAY)
            except Exception as err:
                logger.exception(err)
                failures += 1
                if failures > 5: # close plugin after 5 failures
                    plugin.active = False
                    plugin.close()
            finally:
                plugin.in_queue.task_done()

            # TODO: Add plugin-specific data
            # TODO: Parallelize with Thread Executor

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


    @pyqtSlot(QtGui.QImage)
    def set_window_pixmap(self, qt_image):
        pixmap = QtGui.QPixmap.fromImage(qt_image)
        self.video_frame.setPixmap(pixmap)

        
    def close_widget(self):
        self.stop_camera_pipeline()

        # Wait for thread to finish and queues to empty before closing
        self.pipeline_thread.signals.finished.connect(self.close_plugins)
        self.pipeline_thread.signals.finished.connect(self.deleteLater)



# async def repeat_trigger(trigger, interval):
#     """
#     Execute trigger every interval seconds.
#     """
#     while trigger.active:
#         await asyncio.gather(
#             trigger.execute,
#             asyncio.sleep(interval),
#         )