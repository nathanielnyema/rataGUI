# Specify path to ffmpeg binary or program tries to find it using environment PATH 
FFMPEG_BINARY = None

# Specify which modules to use in the cameras folder or program defaults to all
enabled_camera_models = ["FLIRCamera.py", "VideoReader.py"]

# Specify which modules to use in the plugins folder or program defaults to all
enabled_plugins = []

# Specify which modules to use in the triggers folder or program defaults to all
enabled_trigger_types = []

# Specify paths to video files for VideoReader
video_file_paths = []

# Save and restore settings between sessions
restore_session = True
save_directory = "./session"

# # Specify color mode (Light or Dark) or program matches computer setting (None)
# color_mode = "Dark"