from PyQt6 import QtWidgets, QtGui
# from PyQt6.QtCore import Qt, QTimer, QAbstractTableModel

from UI.design.Ui_CameraWindow import Ui_CameraWindow
from UI.camera_widget import CameraWidget


class CameraWindow(QtWidgets.QWidget, Ui_CameraWindow):
    def __init__(self, camera):
        super().__init__()
        self.setupUi(self)

        self.window_width = self.frameGeometry().width()
        self.window_height = self.frameGeometry().height()

        self.camera_grid = QtWidgets.QGridLayout()
        self.camera_grid.setContentsMargins(0,0,0,0)
        self.setLayout(self.camera_grid)

        #TODO: Implement ability to add multiple camera widgets
        cam0 = CameraWidget(self.window_width, self.window_height, camera, type(camera).__name__, aspect_ratio=True)
        self.camera_grid.addWidget(cam0)

    def startRecording(self, writer_params):
        widgets = (self.camera_grid.itemAt(i).widget() for i in range(self.camera_grid.count())) 
        for widget in widgets:
            if isinstance(widget, CameraWidget):
                widget.startWriter(writer_params)

    def clearLayout(self):
        while self.camera_grid.count() > 0:
            cam_widget = self.camera_grid.takeAt(0).widget()
            if cam_widget is not None:
                if cam_widget.recording:
                    cam_widget.stopWriter()
                cam_widget.stopCameraThread()
                cam_widget.deleteLater()