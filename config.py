# Specify path to alternative ffmpeg binary or program uses default path
FFMPEG_BINARY = None
# FFMPEG_BINARY = "C:\\media-autobuild_suite\\local64\\bin-video\\ffmpeg.exe"

# Specify which modules to use in the cameras folder or program defaults to all
enabled_camera_models = ["FLIRCamera.py", "VideoReader.py"]

# Specify which modules to use in the plugins folder or program defaults to all
enabled_plugins = []

# Specify which modules to use in the triggers folder or program defaults to all
enabled_triggers = []

# Specify paths to video files for VideoReader
video_file_paths = []

# Save and restore settings between sessions
restore_session = True