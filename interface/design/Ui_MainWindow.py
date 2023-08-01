# Form implementation generated from reading ui file 'mainWindow.ui'
#
# Created by: PyQt6 UI code generator 6.5.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(720, 550)
        MainWindow.setIconSize(QtCore.QSize(15, 15))
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setContentsMargins(5, 5, 5, 5)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.camControl = QtWidgets.QHBoxLayout()
        self.camControl.setObjectName("camControl")
        self.camListLayout = QtWidgets.QVBoxLayout()
        self.camListLayout.setContentsMargins(-1, -1, 3, -1)
        self.camListLayout.setSpacing(6)
        self.camListLayout.setObjectName("camListLayout")
        self.camListLabel = QtWidgets.QLabel(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.camListLabel.setFont(font)
        self.camListLabel.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self.camListLabel.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.camListLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.camListLabel.setObjectName("camListLabel")
        self.camListLayout.addWidget(self.camListLabel)
        self.cam_list = QtWidgets.QListWidget(parent=self.centralwidget)
        self.cam_list.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.cam_list.setObjectName("cam_list")
        self.camListLayout.addWidget(self.cam_list)
        self.camControl.addLayout(self.camListLayout)
        self.camAttributes = QtWidgets.QTabWidget(parent=self.centralwidget)
        self.camAttributes.setObjectName("camAttributes")
        self.camPropsTab = QtWidgets.QWidget()
        self.camPropsTab.setObjectName("camPropsTab")
        self.gridLayout = QtWidgets.QGridLayout(self.camPropsTab)
        self.gridLayout.setObjectName("gridLayout")
        self.cam_props = VerticalTabWidget(parent=self.camPropsTab)
        self.cam_props.setObjectName("cam_props")
        self.gridLayout.addWidget(self.cam_props, 0, 0, 1, 1)
        self.camAttributes.addTab(self.camPropsTab, "")
        self.camStatsTab = QtWidgets.QWidget()
        self.camStatsTab.setObjectName("camStatsTab")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.camStatsTab)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.cam_stats = QtWidgets.QTableWidget(parent=self.camStatsTab)
        self.cam_stats.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.cam_stats.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.cam_stats.setAlternatingRowColors(False)
        self.cam_stats.setRowCount(0)
        self.cam_stats.setObjectName("cam_stats")
        self.cam_stats.setColumnCount(4)
        item = QtWidgets.QTableWidgetItem()
        self.cam_stats.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.cam_stats.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.cam_stats.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.cam_stats.setHorizontalHeaderItem(3, item)
        self.cam_stats.horizontalHeader().setCascadingSectionResizes(False)
        self.cam_stats.horizontalHeader().setSortIndicatorShown(False)
        self.cam_stats.horizontalHeader().setStretchLastSection(False)
        self.cam_stats.verticalHeader().setVisible(False)
        self.cam_stats.verticalHeader().setSortIndicatorShown(False)
        self.cam_stats.verticalHeader().setStretchLastSection(False)
        self.gridLayout_2.addWidget(self.cam_stats, 0, 0, 1, 1)
        self.camAttributes.addTab(self.camStatsTab, "")
        self.pluginPipelineTab = QtWidgets.QWidget()
        self.pluginPipelineTab.setObjectName("pluginPipelineTab")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.pluginPipelineTab)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.plugin_pipeline = QtWidgets.QTableWidget(parent=self.pluginPipelineTab)
        self.plugin_pipeline.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.plugin_pipeline.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.plugin_pipeline.setObjectName("plugin_pipeline")
        self.plugin_pipeline.setColumnCount(0)
        self.plugin_pipeline.setRowCount(0)
        self.plugin_pipeline.horizontalHeader().setDefaultSectionSize(74)
        self.gridLayout_3.addWidget(self.plugin_pipeline, 0, 0, 1, 1)
        self.camAttributes.addTab(self.pluginPipelineTab, "")
        self.camTriggersTab = QtWidgets.QWidget()
        self.camTriggersTab.setObjectName("camTriggersTab")
        self.gridLayout_4 = QtWidgets.QGridLayout(self.camTriggersTab)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.cam_triggers = VerticalTabWidget(parent=self.camTriggersTab)
        self.cam_triggers.setObjectName("cam_triggers")
        self.gridLayout_4.addWidget(self.cam_triggers, 0, 0, 1, 1)
        self.camAttributes.addTab(self.camTriggersTab, "")
        self.camControl.addWidget(self.camAttributes)
        self.camControl.setStretch(0, 2)
        self.camControl.setStretch(1, 6)
        self.verticalLayout_2.addLayout(self.camControl)
        self.pluginControl = QtWidgets.QHBoxLayout()
        self.pluginControl.setSizeConstraint(QtWidgets.QLayout.SizeConstraint.SetMinimumSize)
        self.pluginControl.setContentsMargins(0, -1, 0, -1)
        self.pluginControl.setObjectName("pluginControl")
        self.pluginListLayout = QtWidgets.QVBoxLayout()
        self.pluginListLayout.setContentsMargins(-1, -1, 0, -1)
        self.pluginListLayout.setSpacing(6)
        self.pluginListLayout.setObjectName("pluginListLayout")
        self.pluginListLabel = QtWidgets.QLabel(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.pluginListLabel.setFont(font)
        self.pluginListLabel.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self.pluginListLabel.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.pluginListLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.pluginListLabel.setObjectName("pluginListLabel")
        self.pluginListLayout.addWidget(self.pluginListLabel)
        self.plugin_list = QtWidgets.QListWidget(parent=self.centralwidget)
        self.plugin_list.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.plugin_list.setDragEnabled(True)
        self.plugin_list.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.DragDrop)
        self.plugin_list.setDefaultDropAction(QtCore.Qt.DropAction.MoveAction)
        self.plugin_list.setObjectName("plugin_list")
        self.pluginListLayout.addWidget(self.plugin_list)
        self.pluginControl.addLayout(self.pluginListLayout)
        self.plugin_settings = QtWidgets.QTabWidget(parent=self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.plugin_settings.sizePolicy().hasHeightForWidth())
        self.plugin_settings.setSizePolicy(sizePolicy)
        self.plugin_settings.setObjectName("plugin_settings")
        self.pluginControl.addWidget(self.plugin_settings)
        self.frame = QtWidgets.QFrame(parent=self.centralwidget)
        self.frame.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self.frame.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
        self.frame.setObjectName("frame")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.frame)
        self.verticalLayout.setObjectName("verticalLayout")
        self.start_button = QtWidgets.QPushButton(parent=self.frame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.start_button.sizePolicy().hasHeightForWidth())
        self.start_button.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(15)
        font.setBold(True)
        font.setWeight(75)
        self.start_button.setFont(font)
        self.start_button.setObjectName("start_button")
        self.verticalLayout.addWidget(self.start_button)
        self.stop_button = QtWidgets.QPushButton(parent=self.frame)
        self.stop_button.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.stop_button.sizePolicy().hasHeightForWidth())
        self.stop_button.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(15)
        font.setBold(True)
        font.setWeight(75)
        self.stop_button.setFont(font)
        self.stop_button.setMouseTracking(False)
        self.stop_button.setAutoFillBackground(False)
        self.stop_button.setAutoDefault(False)
        self.stop_button.setDefault(False)
        self.stop_button.setFlat(False)
        self.stop_button.setObjectName("stop_button")
        self.verticalLayout.addWidget(self.stop_button)
        self.pause_button = QtWidgets.QPushButton(parent=self.frame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pause_button.sizePolicy().hasHeightForWidth())
        self.pause_button.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(15)
        font.setBold(True)
        font.setWeight(75)
        self.pause_button.setFont(font)
        self.pause_button.setObjectName("pause_button")
        self.verticalLayout.addWidget(self.pause_button)
        self.pluginControl.addWidget(self.frame)
        self.pluginControl.setStretch(0, 3)
        self.pluginControl.setStretch(1, 7)
        self.pluginControl.setStretch(2, 2)
        self.verticalLayout_2.addLayout(self.pluginControl)
        self.verticalLayout_2.setStretch(0, 3)
        self.verticalLayout_2.setStretch(1, 2)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(parent=MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 720, 18))
        self.menubar.setNativeMenuBar(False)
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(parent=self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuEdit = QtWidgets.QMenu(parent=self.menubar)
        self.menuEdit.setObjectName("menuEdit")
        self.menuView = QtWidgets.QMenu(parent=self.menubar)
        self.menuView.setObjectName("menuView")
        self.menuProject = QtWidgets.QMenu(parent=self.menubar)
        self.menuProject.setObjectName("menuProject")
        self.menuOperate = QtWidgets.QMenu(parent=self.menubar)
        self.menuOperate.setObjectName("menuOperate")
        self.menuTools = QtWidgets.QMenu(parent=self.menubar)
        self.menuTools.setObjectName("menuTools")
        self.menuWindow = QtWidgets.QMenu(parent=self.menubar)
        self.menuWindow.setObjectName("menuWindow")
        self.menuHelp = QtWidgets.QMenu(parent=self.menubar)
        self.menuHelp.setObjectName("menuHelp")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(parent=MainWindow)
        self.statusbar.setSizeGripEnabled(True)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionNew = QtGui.QAction(parent=MainWindow)
        self.actionNew.setObjectName("actionNew")
        self.actionOpen = QtGui.QAction(parent=MainWindow)
        self.actionOpen.setObjectName("actionOpen")
        self.actionSave = QtGui.QAction(parent=MainWindow)
        self.actionSave.setObjectName("actionSave")
        self.menuFile.addAction(self.actionNew)
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addAction(self.actionSave)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuEdit.menuAction())
        self.menubar.addAction(self.menuView.menuAction())
        self.menubar.addAction(self.menuProject.menuAction())
        self.menubar.addAction(self.menuOperate.menuAction())
        self.menubar.addAction(self.menuTools.menuAction())
        self.menubar.addAction(self.menuWindow.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())

        self.retranslateUi(MainWindow)
        self.camAttributes.setCurrentIndex(3)
        self.plugin_settings.setCurrentIndex(-1)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "RataGUI"))
        self.camListLabel.setText(_translate("MainWindow", "Available Cameras"))
        self.cam_list.setSortingEnabled(True)
        self.camAttributes.setTabText(self.camAttributes.indexOf(self.camPropsTab), _translate("MainWindow", "Properties"))
        item = self.cam_stats.horizontalHeaderItem(0)
        item.setText(_translate("MainWindow", "Camera Name"))
        item = self.cam_stats.horizontalHeaderItem(1)
        item.setText(_translate("MainWindow", "Frames Acquired"))
        item = self.cam_stats.horizontalHeaderItem(2)
        item.setText(_translate("MainWindow", "Frames Dropped"))
        item = self.cam_stats.horizontalHeaderItem(3)
        item.setText(_translate("MainWindow", "Buffer Size"))
        self.camAttributes.setTabText(self.camAttributes.indexOf(self.camStatsTab), _translate("MainWindow", "Statistics"))
        self.camAttributes.setTabText(self.camAttributes.indexOf(self.pluginPipelineTab), _translate("MainWindow", "Plugin Pipeline"))
        self.camAttributes.setTabText(self.camAttributes.indexOf(self.camTriggersTab), _translate("MainWindow", "Triggers"))
        self.pluginListLabel.setText(_translate("MainWindow", "Plugin Order"))
        self.start_button.setText(_translate("MainWindow", "Start"))
        self.stop_button.setText(_translate("MainWindow", "Stop"))
        self.pause_button.setText(_translate("MainWindow", "Pause"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.menuEdit.setTitle(_translate("MainWindow", "Edit"))
        self.menuView.setTitle(_translate("MainWindow", "View"))
        self.menuProject.setTitle(_translate("MainWindow", "Project"))
        self.menuOperate.setTitle(_translate("MainWindow", "Operate"))
        self.menuTools.setTitle(_translate("MainWindow", "Tools"))
        self.menuWindow.setTitle(_translate("MainWindow", "Window"))
        self.menuHelp.setTitle(_translate("MainWindow", "Help"))
        self.actionNew.setText(_translate("MainWindow", "New"))
        self.actionOpen.setText(_translate("MainWindow", "Open"))
        self.actionSave.setText(_translate("MainWindow", "Save"))
from interface.vtab_widget import VerticalTabWidget
