# RataGUI
Customizable real-time video acquisition with intuitive interface for animal tracking and behavior quantification

# Installation
RataGUI is written entirely in Python and runs on all major platforms. To get started, clone the repository and create a virtual environment with the required dependencies.

## Conda Environment

### CPU-only environment
```
conda env create --file rataGUI-cpu.yaml
conda activate rataGUI
```

### GPU-enabled environment
```
conda env create --file rataGUI-gpu.yaml
conda activate rataGUI
```

## Pip Environment
```
python -m venv venv

source ./venv/bin/activate      # Linux/MacOS
.venv\Scripts\activate.bat      # Command Prompt
venv\Scripts\Activate.ps1       # Powershell

python -m pip install -r requirements.txt
```

<!-- ## Install FFmpeg

FFmpeg can be installed through the official download [links](https://ffmpeg.org/download.html) or using a package manager (e.g. `sudo apt install ffmpeg` on Debian/Ubuntu, `brew install ffmpeg` on macOS, etc.). -->

## External Hardware

### Spinnaker (FLIR) Cameras
To use RataGUI with Spinnaker (FLIR) cameras, follow the instructions [here](https://www.flir.com/products/spinnaker-sdk/) to download the full Spinnaker SDK for your specific Python version. 
In the downloaded folder, find the package wheel (spinnaker_python-\<version\>-\<system-info\>.whl) file and run the following command install PySpin into your Python enviornment. Then, restart the environment and/or reboot your computer to recapture the system and user environment variables.
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

<!-- ### TensorRT for NVIDIA GPUs (optional)
To optimize model inference speeds on a NVIDIA GPU, install the TensorRT SDK available for Windows and Linux following the instructions [here](https://docs.nvidia.com/deeplearning/tensorrt/install-guide/index.html#installing). Then, you will have the option to select **TensorRT** under **Model type** in the DLC/SLEAP Inference settings tab. -->

# Customization

## Implement Custom Camera Models
RataGUI's modular framework makes adding another camera model an easy and straightfoward process. Simply edit the provided TemplateCamera.py class with the required basic functionality to fit your specific camera model use-case. These functions enable the acquisition engine to find, initialize, read frames and properly close the camera.

## Implement Custom Plugins
