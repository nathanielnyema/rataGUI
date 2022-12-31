from PyQt4 import QtCore, QtGui
import qdarkstyle
from threading import Thread
from collections import deque
from datetime import datetime
import time
import sys
import cv2
import imutils

class CameraWidget(QtGui.QWidget):
    """Independent camera feed
    Uses threading to grab IP camera frames in the background

    @param width - Width of the video frame
    @param height - Height of the video frame
    @param stream_link - IP/RTSP/Webcam link
    @param aspect_ratio - Whether to maintain frame aspect ratio or force into fraame
    """

    def __init__(self, width, height, stream_link=0, aspect_ratio=False, parent=None, deque_size=1):
        super(CameraWidget, self).__init__(parent)
        
        # Initialize deque used to store frames read from the stream
        self.deque = deque(maxlen=deque_size)

        # Slight offset is needed since PyQt layouts have a built in padding
        # So add offset to counter the padding 
        self.offset = 16
        self.screen_width = width - self.offset
        self.screen_height = height - self.offset
        self.maintain_aspect_ratio = aspect_ratio

        self.camera_stream_link = stream_link

        # Flag to check if camera is valid/working
        self.online = False
        self.capture = None
        self.video_frame = QtGui.QLabel()

        self.load_network_stream()
        
        # Start background frame grabbing
        self.get_frame_thread = Thread(target=self.get_frame, args=())
        self.get_frame_thread.daemon = True
        self.get_frame_thread.start()

        # Periodically set video frame to display
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.set_frame)
        self.timer.start(.5)

        print('Started camera: {}'.format(self.camera_stream_link))

    def load_network_stream(self):
        """Verifies stream link and open new stream if valid"""

        def load_network_stream_thread():
            if self.verify_network_stream(self.camera_stream_link):
                self.capture = cv2.VideoCapture(self.camera_stream_link)
                self.online = True
        self.load_stream_thread = Thread(target=load_network_stream_thread, args=())
        self.load_stream_thread.daemon = True
        self.load_stream_thread.start()

    def verify_network_stream(self, link):
        """Attempts to receive a frame from given link"""

        cap = cv2.VideoCapture(link)
        if not cap.isOpened():
            return False
        cap.release()
        return True

    def get_frame(self):
        """Reads frame, resizes, and converts image to pixmap"""

        while True:
            try:
                if self.capture.isOpened() and self.online:
                    # Read next frame from stream and insert into deque
                    status, frame = self.capture.read()
                    if status:
                        self.deque.append(frame)
                    else:
                        self.capture.release()
                        self.online = False
                else:
                    # Attempt to reconnect
                    print('attempting to reconnect', self.camera_stream_link)
                    self.load_network_stream()
                    self.spin(2)
                self.spin(.001)
            except AttributeError:
                pass

    def spin(self, seconds):
        """Pause for set amount of seconds, replaces time.sleep so program doesnt stall"""

        time_end = time.time() + seconds
        while time.time() < time_end:
            QtGui.QApplication.processEvents()

    def set_frame(self):
        """Sets pixmap image to video frame"""

        if not self.online:
            self.spin(1)
            return

        if self.deque and self.online:
            # Grab latest frame
            frame = self.deque[-1]

            # Keep frame aspect ratio
            if self.maintain_aspect_ratio:
                self.frame = imutils.resize(frame, width=self.screen_width)
            # Force resize
            else:
                self.frame = cv2.resize(frame, (self.screen_width, self.screen_height))

            # Add timestamp to cameras
            cv2.rectangle(self.frame, (self.screen_width-190,0), (self.screen_width,50), color=(0,0,0), thickness=-1)
            cv2.putText(self.frame, datetime.now().strftime('%H:%M:%S'), (self.screen_width-185,37), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255,255,255), lineType=cv2.LINE_AA)

            # Convert to pixmap and set to video frame
            self.img = QtGui.QImage(self.frame, self.frame.shape[1], self.frame.shape[0], QtGui.QImage.Format_RGB888).rgbSwapped()
            self.pix = QtGui.QPixmap.fromImage(self.img)
            self.video_frame.setPixmap(self.pix)

    def get_video_frame(self):
        return self.video_frame
    
def exit_application():
    """Exit program event handler"""

    sys.exit(1)

if __name__ == '__main__':

    # Create main application window
    app = QtGui.QApplication([])
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt())
    app.setStyle(QtGui.QStyleFactory.create("Cleanlooks"))
    mw = QtGui.QMainWindow()
    mw.setWindowTitle('Camera GUI')
    mw.setWindowFlags(QtCore.Qt.FramelessWindowHint)

    cw = QtGui.QWidget()
    ml = QtGui.QGridLayout()
    cw.setLayout(ml)
    mw.setCentralWidget(cw)
    mw.showMaximized()
    
    # Dynamically determine screen width/height
    screen_width = QtGui.QApplication.desktop().screenGeometry().width()
    screen_height = QtGui.QApplication.desktop().screenGeometry().height()
    
    # Create Camera Widgets 
    username = 'Your camera username!'
    password = 'Your camera password!'
    
    # Stream links
    camera0 = 'rtsp://{}:{}@192.168.1.43:554/cam/realmonitor?channel=1&subtype=0'.format(username, password)
    camera1 = 'rtsp://{}:{}@192.168.1.45/axis-media/media.amp'.format(username, password)
    camera2 = 'rtsp://{}:{}@192.168.1.47:554/cam/realmonitor?channel=1&subtype=0'.format(username, password)
    camera3 = 'rtsp://{}:{}@192.168.1.40:554/cam/realmonitor?channel=1&subtype=0'.format(username, password)
    camera4 = 'rtsp://{}:{}@192.168.1.44:554/cam/realmonitor?channel=1&subtype=0'.format(username, password)
    camera5 = 'rtsp://{}:{}@192.168.1.42:554/cam/realmonitor?channel=1&subtype=0'.format(username, password)
    camera6 = 'rtsp://{}:{}@192.168.1.46:554/cam/realmonitor?channel=1&subtype=0'.format(username, password)
    camera7 = 'rtsp://{}:{}@192.168.1.41:554/cam/realmonitor?channel=1&subtype=0'.format(username, password)
    
    # Create camera widgets
    print('Creating Camera Widgets...')




class Worker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the callback to our kwargs
        self.kwargs['progress_callback'] = self.signals.progress

    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''

        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done


    @pyqtSlot(np.ndarray)
    def update_image(self, frame):
        """Updates the image_label with a new opencv image"""
        qt_img = self.convert_cv_qt(frame)
        self.img_label.setPixmap(qt_img)

    def convert_cv_qt(self, cv_img):
        h, w, ch = cv_img.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(cv_img.data, w, h, bytes_per_line, QtGui.QImage.Format.Format_RGB888)
        display_width = self.img_label.frameGeometry().width()
        display_height = self.img_label.frameGeometry().height()
        p = convert_to_Qt_format.scaled(display_width, display_height, Qt.AspectRatioMode.KeepAspectRatio)
        return QtGui.QPixmap.fromImage(p)