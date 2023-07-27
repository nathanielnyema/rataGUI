from plugins import BasePlugin, ConfigManager

import os
import numpy as np
import cv2
import tensorflow as tf
# sleap.disable_preallocation()


class SleapInference(BasePlugin):
    """
    Plugin that inferences on frames using trained SLEAP model to predict animal pose and write keypoints as metadata
    """

    DEFAULT_CONFIG = {
        "Model directory": ""
    }


    def __init__(self, cam_widget, config, queue_size=0):
        super().__init__(cam_widget, config, queue_size)

        print("Started Sleap Inference for: {}".format(cam_widget.camera.cameraID))
        self.model_path = os.path.normpath(config.get("Model directory"))

        self.model_fn = load_frozen_graph(config.get("Model directory"))
        self.input_width = 1920
        self.input_height = 1376
        self.count = 0
        self.keypoints = np.zeros((1,4,2))

    def execute(self, frame, metadata):
        self.count += 1
        img_h, img_w, num_ch = frame.shape

        if self.count >= 0:
            image = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            image = cv2.resize(image, (self.input_width, self.input_height)) # resize uses reverse order
            image = np.reshape(image, (-1, self.input_height, self.input_width, 1))
            prediction = self.model_fn(x=tf.constant(image))
            self.keypoints = prediction[3].numpy()[0]
            self.count = 0

            # print(self.keypoints.shape)
        for idx, instance in enumerate(self.keypoints):
            color = [0,0,0]
            color[idx % 3] = 255
            for point in instance:
                if not(np.isnan(point[0]) or np.isnan(point[0])): 
                    resized_x = point[0] * (img_w/self.input_width)
                    resized_y = point[1] * (img_h/self.input_height)
                    frame = cv2.circle(frame, (int(resized_x), int(resized_y)), 5, color, -1)


        return frame, metadata

    def close(self):
        print("Video writer closed")
        self.active = False

def load_frozen_graph(model_path):
    # Load frozen graph using TensorFlow 1.x functions
    with tf.io.gfile.GFile(model_path + "/frozen_graph.pb", "rb") as f:
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

    print("-" * 50)
    print("Frozen model inputs: ")
    print(model.inputs)
    print("Frozen model outputs: ")
    print(model.outputs)

    return model


