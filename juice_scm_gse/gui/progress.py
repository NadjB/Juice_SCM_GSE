# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'designer/progress.ui',
# licensing of 'designer/progress.ui' applies.
#
# Created: Sun May 19 18:16:03 2019
#      by: pyside2-uic  running on PySide2 5.12.3
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_Progress(object):
    def setupUi(self, Progress):
        Progress.setObjectName("Progress")
        Progress.setWindowModality(QtCore.Qt.WindowModal)
        Progress.resize(792, 286)
        self.gridLayout = QtWidgets.QGridLayout(Progress)
        self.gridLayout.setObjectName("gridLayout")
        self.step_name = QtWidgets.QLabel(Progress)
        self.step_name.setText("")
        self.step_name.setObjectName("step_name")
        self.gridLayout.addWidget(self.step_name, 1, 0, 1, 1)
        self.global_progress = QtWidgets.QProgressBar(Progress)
        self.global_progress.setProperty("value", 24)
        self.global_progress.setObjectName("global_progress")
        self.gridLayout.addWidget(self.global_progress, 1, 1, 1, 1)
        self.step_detail = QtWidgets.QLabel(Progress)
        self.step_detail.setText("")
        self.step_detail.setObjectName("step_detail")
        self.gridLayout.addWidget(self.step_detail, 2, 0, 1, 1)
        self.step_progress = QtWidgets.QProgressBar(Progress)
        self.step_progress.setProperty("value", 24)
        self.step_progress.setObjectName("step_progress")
        self.gridLayout.addWidget(self.step_progress, 2, 1, 1, 1)
        self.channel_progress = QtWidgets.QProgressBar(Progress)
        self.channel_progress.setProperty("value", 24)
        self.channel_progress.setObjectName("channel_progress")
        self.gridLayout.addWidget(self.channel_progress, 0, 1, 1, 1)
        self.channel_name = QtWidgets.QLabel(Progress)
        self.channel_name.setText("")
        self.channel_name.setObjectName("channel_name")
        self.gridLayout.addWidget(self.channel_name, 0, 0, 1, 1)

        self.retranslateUi(Progress)
        QtCore.QMetaObject.connectSlotsByName(Progress)

    def retranslateUi(self, Progress):
        Progress.setWindowTitle(QtWidgets.QApplication.translate("Progress", "Progress", None, -1))

