# RataGUI
Easy-to-use real-time video acquisition for animal tracking and behavior quantification

# Installation
RataGUI is written entirely in Python and runs on all major platforms. To get started, clone the repository and create a virtual environment with the required dependencies.

## Conda Environment
```
conda env create -f rataGUI.yaml
conda activate rataGUI
```

## Pip Environment
```
python -m venv venv
source ./venv/bin/activate
pip install -r requirements.txt
```

## Install Spinnaker SDK (optional)
To use RataGUI with Spinnaker cameras, follow the instructions [here](https://www.flir.com/products/spinnaker-sdk/) to download the Spinnaker SDK for your specific Python version. 
In the downloaded folder, find the package wheel (spinnaker_python-\<version\>-\<system-info\>.whl) file and run the following command install PySpin into your Python enviornment.
```
pip install <PATH-TO-SPINNAKER-WHEEL-FILE>.whl
```

# Custom Camera Models
RataGUI's modular framework makes adding another camera model an easy and straightfoward process. Simply edit the provided TemplateCamera.py class with the required basic functionality
to fit your specific camera model use-case. These functions enable the acquisition engine to find, initialize, extract frames from the camera and properly closing it. 

# Custom Plugins

