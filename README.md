# RataGUI
Customizable and intuitive video acquisition system for real-time animal tracking and behavior quantification

# Installation
RataGUI is written entirely in Python and runs on all platforms with minimal dependencies.

## Conda Installation (Recommended)

### CPU-only environment
```
conda create -n rataGUI ffmpeg pip python=3.10
conda activate rataGUI
python -m pip install rataGUI
```

### GPU-enabled environment

For real-time model inference, using a GPU is strongly encouraged to minimize latency. If you have a NVIDIA GPU, make sure the latest [driver](https://www.nvidia.com/download/index.aspx) version is installed. 
> Note: CUDA is automatically installed in the conda environment.

```
conda create -n rataGUI ffmpeg pip python=3.10 cudnn=8.2 cudatoolkit=11.3 nvidia::cuda-nvcc=11.3
conda activate rataGUI
python -m pip install rataGUI
```

## Pip Installation (CPU-only)

If you don't want to download Anaconda or its lightweight variants (miniconda, miniforge etc.), you can install RataGUI as a standalone pip package in any python>=3.10 environment. However, creating a separate virtual environment is strongly suggested so that RataGUI doesn't conflict with other installed packages. 
> Note: Unlike conda, pip can't automatically install ffmpeg for video encoding so it needs to be installed through the official download [links](https://ffmpeg.org/download.html) or using a package manager (e.g. `sudo apt install ffmpeg` on Debian/Ubuntu, `brew install ffmpeg` on macOS, etc.).

```
python -m pip install rataGUI
```

## External Hardware

### Spinnaker (FLIR) Cameras
To use RataGUI with Spinnaker (FLIR) cameras, follow the instructions [here](https://www.flir.com/products/spinnaker-sdk/) to download the full Spinnaker SDK for your specific Python version. 
In the downloaded folder, find the package wheel file (`spinnaker_python-\<version\>-\<system-info\>.whl`) and run the following command install PySpin into your Python enviornment. Then, restart the environment or reboot your computer to recapture the system and user environment variables.
```
python -m pip install <PATH-TO-SPINNAKER-WHEEL-FILE>.whl
```

### Basler (Pylon) Cameras
To use RataGUI with Basler cameras, install the python wrapper package for the PyPylon SDK. 
```
python -m pip install pypylon
```

### National Instruments (NI-DAQmx) Devices
To use RataGUI with National Instruments hardware, install the python wrapper package for the NI-DAQmx driver.
```
python -m pip install nidaqmx
``` 

# Customization

RataGUI's modular framework was built for easy user customizability and integration. You are encouraged to clone the package repository from Github and add additional camera models or plugins for your specific use case. 
```
git clone https://github.com/BrainHu42/rataGUI.git
```

## Implement Custom Camera Models
Currently, RataGUI has built-in support for FLIR, Basler and OpenCV-compatible cameras. If you need to add another camera model, simply rename and edit the required functions provided in `cameras/TemplateCamera.py` to fit your camera model's specifications. RataGUI will use these functions to find, initialize, read frames from and close the camera. 

## Implement Custom Plugins
Currently, RataGUI has built-in support for multi-animal pose estimation with SLEAP and DeepLabCut (DLC) models as well as writing video stream to file or displaying it on screen. If you need additional functionality, simply rename and edit the required functions provided in `plugins/template_plugin.py` with the custom processing needed for your use case. RataGUI will use these functions to attach your plugin to an active camera widget's processing pipeline. Any configurable plugin settings should be specified in the dictionary named `DEFAULT_CONFIG`. RataGUI will use these default settings to automatically create a dynamic menu and add it to the user interface.

## Implement Custom Triggers
Currently, RataGUI has built-in support for interfacing with National Instrument cards as well as network devices like a Rasperry Pi through a UDP socket. If you need to interface with other external devices, simply rename and edit the required functions provided in `triggers/template_trigger.py` to fit your custom use case. RataGUI will use these functions to populate the trigger tab in the user interface with all available devices and their configurable settings. Trigger devices can be controlled through the interface as well as within a plugin process. 