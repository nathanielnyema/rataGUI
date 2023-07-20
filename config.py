# Specify path to alternative ffmpeg binary or program uses default path
# FFMPEG_BINARY = "C:/media-autobuild_suite/local64/bin-video/ffmpeg.exe"
FFMPEG_BINARY = None

# Specify which subclasses to use in cameras folder or program defaults to all
enabled_camera_models = ["FLIRCamera.py", "VideoReader.py"]

# Specify which subclasses to use in plugins folder or program defaults to all
enabled_plugins = []

# Specify paths to video files for VideoReader
video_file_paths = []

# Save and restore settings between sessions
restore_session = True