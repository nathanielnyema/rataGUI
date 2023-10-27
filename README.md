# RataGUI

[![Downloads](https://static.pepy.tech/badge/ratagui)](https://pepy.tech/project/ratagui) 
[![Downloads](https://static.pepy.tech/badge/ratagui/month)](https://pepy.tech/project/ratagui)
[![PyPI version](https://badge.fury.io/py/rataGUI.svg)](https://badge.fury.io/py/rataGUI)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Generic badge](https://img.shields.io/badge/Contributions-Welcome-brightgreen.svg)](CONTRIBUTING.md)

<div align="center">
<p align="center">
<img src="docs/images/banner.png" width="95%">
</p>
</div>

RataGUI is a **customizable** and **user-friendly** Python framework for real-time animal tracking and behavioral control. At a high level, it connects video streams from cameras to online processing pipelines that can trigger external devices in real-time, enabling experiments with low latency, closed-loop feedback. 


# Features
RataGUI was developed with four primary design principles:

* **Accessibility** - RataGUI features an adaptive and intuitive graphical user interface (GUI) that makes it easier to conduct complex experiments involving heterogenous hardware without any additional programming. Using minimal dependencies and efficient multi-threaded processing, RataGUI is designed to run on a wide variety of different systems.

* **Modularity** - RataGUI's plug-and-play architecture enables easy customization of data processing pipelines to support your experiment's specific needs. Cameras, plugins and triggers are separated into individual modules (see tables below) and configured together in a single unified interface.

* **Extensitibility** - RataGUI's modular framework allows for seamless integration of user-created modules for additional functionality. You are encouraged to fork the repository and write additional modules using the provided instructions and template code. RataGUI aims to provide a platform for researchers to share code and contribute to the growing list of modules below.

* **Reproducibility** - RataGUI automatically logs all relevant experimental info and saves its state in a restorable, human-readable JSON format. This allows RataGUI to replicate an experiment's parameters from a single session directory. 


## Available Camera Modules
| Name | Description | Contributor |
| -------- | -------- | -------- |
| BaslerCamera | Support for Basler cameras using pypylon | [BrainHu42](https://github.com/BrainHu42) |
| FLIRCamera  | Support for Spinnaker cameras using PySpin | [BrainHu42](https://github.com/BrainHu42) |
| VideoReader | Support for video file playback for offline processing  | [BrainHu42](https://github.com/BrainHu42) |
| WebCamera | Support for OpenCV-enabled cameras such as web or network cameras | [BrainHu42](https://github.com/BrainHu42) |


## Available Plugin Modules
| Name | Description | Contributor |
| -------- | -------- | -------- |
| DLCInference | Pose estimation using exported DeepLabCut model | [BrainHu42](https://github.com/BrainHu42) |
| FrameDisplay  | Displays video stream in a separate window | [BrainHu42](https://github.com/BrainHu42) |
| MetadataWriter | Overlays metadata onto frames and/or into a log file | [BrainHu42](https://github.com/BrainHu42) |
| SleapInference | Pose estimation using exported SLEAP model | [BrainHu42](https://github.com/BrainHu42) |
| VideoWriter | Writes frames to video file using FFMPEG | [BrainHu42](https://github.com/BrainHu42) |

## Available Trigger Modules
| Name | Description | Contributor |
| -------- | -------- | -------- |
| NIDAQmxCounter | Support for writing tasks to National Instrument counter cards through the NI-DAQmx driver. | [BrainHu42](https://github.com/BrainHu42) |
| UDPSocket  | Publishes information to a network socket using UDP protocol | [BrainHu42](https://github.com/BrainHu42) |


# [Installation Guide](docs/install-guide.md)

## Quick Start
```
conda create -n rataGUI ffmpeg pip python=3.10 cudnn=8.2 cudatoolkit=11.3 nvidia::cuda-nvcc=11.3
conda activate rataGUI
python -m pip install rataGUI
```
<!-- # Documentation
## Video Demo -->


# Customization Guide

RataGUI's modular framework was built for user customizability and integration. We encourage you to fork the package repository from Github and add additional modules for your specific use case. 
```
git clone https://github.com/BrainHu42/rataGUI.git
```

## Implement Custom Camera Models
To add another camera model, simply rename and edit the required functions provided in `cameras/TemplateCamera.py` to fit your camera model's specifications. RataGUI will use these functions to find, initialize, read frames from and close the camera. Any configurable camera settings should be specified in the dictionary named `DEFAULT_PROPS`. RataGUI will use these default settings to automatically create a dynamic menu and add it to the user interface. The configured settings will be passed into the `initializeCamera` function.

## Implement Custom Plugins
To incorporate additional functionality, simply rename and edit the required functions provided in `plugins/template_plugin.py` with the custom processing needed for your use case. RataGUI will use these functions to attach your plugin to an active camera widget's processing pipeline. Any configurable plugin settings should be specified in the dictionary named `DEFAULT_CONFIG`. RataGUI will use these default settings to automatically create a dynamic menu and add it to the user interface. 

## Implement Custom Triggers
To interface with other external devices, simply rename and edit the required functions provided in `triggers/template_trigger.py` to fit your custom use case. RataGUI will use these functions to populate the trigger tab in the user interface with all available devices and their configurable settings. Trigger devices can be controlled through the interface as well as within a plugin process. 

## Contributing
If you think your module would be useful to other people, please consider submitting a merge request so that we can review and integrate your code into the main branch. We'll also add you to the list of module contributors!