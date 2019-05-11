#!/usr/bin/env python3


import sys
import time
import subprocess
import zmq
from pathlib import Path
from PySide2.QtWidgets import QMainWindow, QApplication, QMessageBox
from PySide2.QtCore import QCoreApplication, Signal, QThread, Slot, Qt, QObject
from discovery_driver import turn_on_psu

from juice_scm_gse.gui.mainwindow import Ui_MainWindow


class TemperaturesWorker(QThread):

    updateTemperatures = Signal(float,float,float)

    def __init__(self, port = 9990):
        QThread.__init__(self)
        self.context = zmq.Context()
        self.sock = self.context.socket(zmq.SUB)
        self.sock.connect(f"tcp://localhost:{port}")
        self.sock.setsockopt(zmq.SUBSCRIBE, b"Temperatures")

    def run(self):
        while(True):
            string = self.sock.recv()
            topic, data = string.split()
            t,tempA,tempB,tempC =data.decode().split(',')
            self.updateTemperatures.emit(float(tempA),float(tempB),float(tempC))


class DiscoveryWorker(QObject):

    update_psu = Signal(str)

    def __init__(self, push_port=9991, pull_port=9992):
        QObject.__init__(self)
        self.thread = QThread()
        self.thread.start()
        self.moveToThread(self.thread)
        self.context = zmq.Context()
        self.push_sock = self.context.socket(zmq.PUSH)
        self.push_sock.bind(f"tcp://*:{push_port}")
        self.pull_sock = self.context.socket(zmq.PULL)
        self.pull_sock.bind(f"tcp://*:{pull_port}")
        self.disco_process = subprocess.Popen(['python','discovery_driver/__init__.py'])

    def __del__(self):
        self.disco_process.kill()

    def turn_on(self):
        self.push_sock.send_json(turn_on_psu("CHX"))
        self.update_psu.emit(self.pull_sock.recv_json())

class ApplicationWindow(QMainWindow):
    """Main Window"""
    def __init__(self, parent=None):
        super(ApplicationWindow, self).__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.tempWorker = TemperaturesWorker()
        self.tempWorker.updateTemperatures.connect(self.updateTemperatures)
        self.tempWorker.start()
        self.tempWorker.moveToThread(self.tempWorker)

        self.discoWorker = DiscoveryWorker()
        self.discoWorker.update_psu.connect(self.ui.PSU_STATUS.setText)
        self.ui.PSU_ON_PB.clicked.connect(self.discoWorker.turn_on)


    def updateTemperatures(self,tempA,tempB,tempC):
        self.ui.tempA_LCD.display(tempA)
        self.ui.tempB_LCD.display(tempB)
        self.ui.tempC_LCD.display(tempC)

    def quit_app(self):
        self.close()

def main(args=sys.argv):
    app = QApplication(args)
    application = ApplicationWindow()
    application.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
