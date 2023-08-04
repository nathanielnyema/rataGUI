# import sys
import time
import numpy as np
import os
from datetime import datetime
# import logging

from PyQt6 import QtWidgets, QtGui
from PyQt6.QtCore import Qt, QThreadPool, QObject, QTimer, pyqtSlot, pyqtSignal, QRect

from threads import WorkerThread
from interface.design.Ui_CameraWidget import Ui_CameraWidget

import asyncio
from concurrent.futures import ThreadPoolExecutor

# process_pool = ProcessPoolExecutor()
thread_pool = ThreadPoolExecutor()

# Change to camera widget
class CameraWidget(QtWidgets.QWidget, Ui_CameraWidget):
    """Encapsulates running camera object and its plugin processing pipeline by connecting Camera and Plugin APIs.

    :param camera: Camera object to extract frames from
    :param cam_config: ConfigManager that stores settings to initialize camera
    :param plugins: List of plugin types in processing pipeline to instantiate
    :param triggers: List of initialized trigger objects to execute when needed
    """

    def __init__(self, camera=None, cam_config=None, plugins=[], triggers=[]):
        super().__init__()
        self.setupUi(self)

        # Set widget fields
        self.frame_width = self.frameGeometry().width()
        self.frame_height = self.frameGeometry().height()

        # Initialize camera object
        self.camera = camera
        self.camera_model = type(camera).__name__
        self.camera_config = cam_config

        # Threadpool for asynchronous tasks with signals and slots
        self.threadpool = QThreadPool().globalInstance()

        # Start thread to process triggering
        self.triggers = triggers
        # self.trigger_thread = WorkerThread(self.start_camera_triggers)
        # self.threadpool.start(self.trigger_thread)

        # Instantiate plugins with camera-specific settings
        self.plugins = [Plugin(self, config) for Plugin, config in plugins]
        self.active = True

        # Start thread to process camera stream and plugin pipeline
        self.pipeline_thread = WorkerThread(self.start_camera_pipeline)
        self.threadpool.start(self.pipeline_thread)


    # async def run_triggering(self):
    #     tasks = []
    #     for trigger in self.triggers:
    #         tasks.append(asyncio.create_task(repeat_trigger(trigger, trigger.interval)))

    #     await asyncio.gather(*tasks)

    # def start_camera_triggers(self):
    #     print('Started camera trigger: {}'.format(self.camera.getName()))
    #     try:
    #         asyncio.run(self.run_triggering(), debug=False)
    #     except Exception as err:
    #         print('ERROR--Trigger Loop: %s' % err)
    #         os._exit(42)


    async def acquire_frames(self):
        loop = asyncio.get_running_loop()
        t0 = time.time()
        while self.camera._running:
            if self.active:
                try:
                    status, frame = await loop.run_in_executor(None, self.camera.readCamera)
                    metadata = self.camera.getMetadata()
                    metadata['Timestamp'] = datetime.now()
                    metadata['CameraID'] = self.camera.getName()

                    if status: 
                        # Send acquired frame to first plugin process in pipeline
                        # print('Camera queue: ' + str(self.plugins[0].in_queue.qsize()))
                        await self.plugins[0].in_queue.put((frame, metadata))
                        await asyncio.sleep(0)
                    else:
                        raise IOError("Camera frame not found ... stopping")
                except Exception as err:
                    print('ERROR--Acquisition: %s' % err)
                    break

            else: # Pass to next coroutine
                await asyncio.sleep(0)

        t1 = time.time()
        print(self.camera.frames_acquired, str(t1-t0))
        print('FPS: '+str(self.camera.frames_acquired / (t1-t0)))

        # Close camera if camera stops streaming
        self.camera.closeCamera()

    async def process_plugin_pipeline(self):
        # Add process to continuously acquire frames from camera
        acquisition_task = asyncio.create_task(self.acquire_frames())

        # Add all plugin processes (pipeline) to async event loop
        plugin_tasks = [] 
        for cur_plugin, next_plugin in zip(self.plugins, self.plugins[1:]):
            # Connect outputs and inputs of consecutive plugin pairs
            cur_plugin.out_queue = next_plugin.in_queue
            plugin_tasks.append(asyncio.create_task(plugin_process(cur_plugin)))
        # Add terminating plugin
        plugin_tasks.append(asyncio.create_task(plugin_process(self.plugins[-1])))

        # Wait until camera stops running
        await acquisition_task

        # Wait for plugins to finish processing
        for plugin in self.plugins:
            await plugin.in_queue.join()

        # Cancel idle plugin processes
        for task in plugin_tasks:
            task.cancel()

    def stop_plugin_pipeline(self):
        for plugin in self.plugins:
            plugin.active = False

    def close_plugin_pipeline(self):
        for plugin in self.plugins:
            plugin.close()


    @pyqtSlot()
    def start_camera_pipeline(self):
        print('Started camera: {}'.format(self.camera.getName()))
        try:
            self.camera.initializeCamera(self.camera_config)
            asyncio.run(self.process_plugin_pipeline(), debug=False)
        except Exception as err:
            print('ERROR--Camera Loop: %s' % err)
            self.close_widget()

    def stop_camera_pipeline(self):
        print('Stopped camera: {}'.format(self.camera.cameraID))
        # Signal to event loop to stop camera and plugins
        self.camera._running = False
        self.stop_plugin_pipeline()
        
    def close_widget(self):
        # def clean_up():
        #     self.close_plugin_pipeline()
        #     self.setParent(None)
        #     self.deleteLater()
        self.stop_camera_pipeline()
        # Wait for thread to finish and queues to empty before closing
        self.pipeline_thread.signals.finished.connect(self.close_plugin_pipeline)
        self.pipeline_thread.signals.finished.connect(self.deleteLater)


# Asynchronous execution loop for an arbitrary plugin 
async def plugin_process(plugin):
    loop = asyncio.get_running_loop()
    failures = 0
    while True:
        frame, metadata = await plugin.in_queue.get()
        # print(f'{type(plugin).__name__} queue: ' + str(plugin.in_queue.qsize()))
        try:
            # Execute plugin
            if plugin.active:
                if plugin.cpu_bound or plugin.io_bound: # possibly move queues outside plugins
                    result = await loop.run_in_executor(None, plugin.process, frame, metadata)
                else:
                    result = plugin.process(frame, metadata)
            else:
                result = (frame, metadata)

            # Send output to next plugin
            if plugin.out_queue != None:
                await plugin.out_queue.put(result)
        except Exception as err:
            print('ERROR--%s: %s' % (type(plugin).__name__, err))
            failures += 1
            if failures > 5: # close plugin after 5 failures
                plugin.active = False
                plugin.close()
        finally:
            plugin.in_queue.task_done()

        # TODO: Add plugin-specific data
        # TODO: Parallelize with Thread Executor

# async def repeat_trigger(trigger, interval):
#     """
#     Execute trigger every interval seconds.
#     """
#     while trigger.active:
#         await asyncio.gather(
#             trigger.execute,
#             asyncio.sleep(interval),
#         )