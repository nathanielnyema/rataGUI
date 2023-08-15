# RataGUI
Customizable and intuitive video acquisition system for real-time animal tracking and behavior quantification

# Installation
RataGUI is written entirely in Python and runs on all major platforms. To get started, clone the repository and create a virtual environment with the required dependencies.

## Conda Installation (Recommended)

### CPU-only environment
```
conda env create --file rataGUI-cpu.yaml
conda activate rataGUI
```

### GPU-enabled environment

For real-time model inference, using a GPU is strongly encouraged to minimize latency. If you have a NVIDIA GPU, make sure the latest [driver](https://www.nvidia.com/download/index.aspx) and [CUDA](https://www.nvidia.com/download/index.aspx) versions installed before creating the conda environment. You can verify your CUDA and driver versions by running the command: `nvidia-smi`. 

```
conda env create --file rataGUI-gpu.yaml
conda activate rataGUI
```

## Pip Installation (CPU-only)

If you don't want to download Anaconda or its lightweight variants (miniconda, miniforge etc.), you can install RataGUI as a standalone pip package instead.

```
python -m venv venv             # Make virtual env (or use existing one)

source ./venv/bin/activate      # for Linux/MacOS
.venv\Scripts\activate.bat      # for Command Prompt
venv\Scripts\Activate.ps1       # for Powershell

python -m pip install -r requirements.txt
```
> Note: Unlike conda, pip can't automatically install ffmpeg for video encoding so it needs to be installed through the official download [links](https://ffmpeg.org/download.html) or using a package manager (e.g. `sudo apt install ffmpeg` on Debian/Ubuntu, `brew install ffmpeg` on macOS, etc.).

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

RataGUI's modular framework was built for easy user customizability and integration. You are encouraged to clone the package reponsitory from Github and add additional camera models or plugins for your specific use case. 
```
git clone https://github.com/BrainHu42/rataGUI.git
```

## Implement Custom Camera Models
Currently, RataGUI has built-in support for FLIR, Basler and OpenCV-compatible cameras. If you need to add another camera model, simply rename and edit the required functions provided in `cameras/TemplateCamera.py` to fit your camera model's specifications. RataGUI will use these functions to find, initialize, read frames from and close the camera. 

## Implement Custom Plugins
Currently, RataGUI has built-in support for multi-animal pose estimation with SLEAP and DeepLabCut (DLC) models as well as writing video stream to file or displaying it on screen. Any metadata collected during acquistion can be written directly on the frame or in a csv file using the **MetadataWriter** plugin. If you need additional functionality, simply rename and edit the required functions provided in `plugins/template_plugin.py` with the custom processing needed for your use case. RataGUI will use these functions to attach your plugin to an active camera widget's processing pipeline.