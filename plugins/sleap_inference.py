from plugins import BasePlugin, ConfigManager

import os
import numpy as np
import cv2
import tensorflow as tf

import logging
logger = logging.getLogger(__name__)

class SleapInference(BasePlugin):
    """
    Plugin that inferences on frames using trained SLEAP model to predict animal pose and write keypoints as metadata
    """

    DEFAULT_CONFIG = {
        "Model directory": "",
        "Inference FPS": ["Automatic", "Match Camera", "Manual"],
        "Score Threshold": 0.5, 
        # "Cameras"
    }

    def __init__(self, cam_widget, config, queue_size=0):
        super().__init__(cam_widget, config, queue_size)
        self.model_dir = os.path.normpath(config.get("Model directory"))

        try:
            self.model = load_frozen_model(self.model_dir)
            self.model_input = self.model.inputs[0]

            # Warm start to load cuDNN
            input_shape = self.model_input.shape.as_list()
            input_shape[0] = 1 # Batch size
            dummy_frame = tf.zeros(input_shape, self.model_input.dtype)
            self.model(tf.constant(dummy_frame))
        except Exception as err:
            logger.exception(err)
            logger.debug("Unable to load model ... auto-disabling SLEAP plugin")
            self.active = False

        # self.cpu_bound = True
        self.interval = 10
        self.batch_size = input_shape[0]
        self.input_height = input_shape[1]
        self.input_width = input_shape[2]
        self.num_channels = input_shape[3]
        self.count = 0
        self.keypoints = np.zeros((1,4,2))
        self.keypoint_scores = np.zeros((1,4,1))

    def process(self, frame, metadata):
        img_h, img_w, num_ch = frame.shape
        self.interval -= 1

        if self.interval <= 0:
            image = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            image = cv2.resize(image, (self.input_width, self.input_height)) # resize uses reverse order
            image = np.reshape(image, (-1, self.input_height, self.input_width, 1))
            prediction = self.model(x=tf.constant(image)) # outputs list of tensors
            self.keypoints = prediction[3].numpy()[0]
            self.keypoint_scores = prediction[2].numpy()[0]
            # print(self.keypoint_scores.shape)
            fps_mode = self.config.get("Inference FPS")
            if fps_mode == "Match Camera":
                self.interval = 0
            elif fps_mode == "Automatic":
                self.interval = self.in_queue.qsize()
                # print(self.interval)

            # print(self.keypoint_scores)
            # print(prediction[2])
            # print(prediction[0])

        threshold = self.config.get("Score Threshold")
        for num, instance in enumerate(self.keypoints):
            color = [0,0,0]
            color[num % 3] = 255
            point_scores = self.keypoint_scores[num]
            for idx, point in enumerate(instance):
                if not(np.isnan(point[0]) or np.isnan(point[0])) and point_scores[idx] > threshold: 
                    resized_x = point[0] * (img_w/self.input_width)
                    resized_y = point[1] * (img_h/self.input_height)
                    frame = cv2.circle(frame, (int(resized_x), int(resized_y)), 5, color, -1)

        return frame, metadata

    def close(self):
        logger.info("Sleap Inference closed")
        self.active = False


def load_frozen_model(model_dir):
    # Load frozen graph using TensorFlow 1.x functions
    model_file = [file for file in os.listdir(model_dir) if file.endswith('.pb')]
    if len(model_file) > 1:
        raise IOError("Multiple model files found. Model folder should only contain one .pb file")
    elif len(model_file) == 0:
        raise IOError("Could not fild frozen model (.pb) file in specified folder")
    else:
        model_file = model_file[0]

    with tf.io.gfile.GFile(os.path.join(model_dir, model_file), "rb") as f:
        graph_def = tf.compat.v1.GraphDef()
        graph_def.ParseFromString(f.read())

    def _imports_graph_def():
        tf.compat.v1.import_graph_def(graph_def, name="")

    wrapped_import = tf.compat.v1.wrap_function(_imports_graph_def, [])
    import_graph = wrapped_import.graph

    inputs=["x:0"]
    outputs=["Identity:0", "Identity_1:0", "Identity_2:0", "Identity_3:0"]
    model = wrapped_import.prune(
        tf.nest.map_structure(import_graph.as_graph_element, inputs),
        tf.nest.map_structure(import_graph.as_graph_element, outputs)
    )

    # print("-" * 50)
    # print("Frozen model inputs: ")
    # print(model.inputs)
    # print("Frozen model outputs: ")
    # print(model.outputs)

    return model


