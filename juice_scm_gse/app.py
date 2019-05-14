#!/usr/bin/env python3


import sys
import time
import subprocess
import zmq
from pathlib import Path
from PySide2.QtWidgets import QMainWindow, QApplication, QMessageBox
from PySide2.QtCore import QCoreApplication, Signal, QThread, Slot, Qt, QObject
from discovery_driver import do_measurements
import numpy as np

from juice_scm_gse.gui.mainwindow import Ui_MainWindow


class TemperaturesWorker(QThread):
    updateTemperatures = Signal(float, float, float)

    def __init__(self, port=9990):
        QThread.__init__(self)
        self.context = zmq.Context()
        self.sock = self.context.socket(zmq.SUB)
        self.sock.connect(f"tcp://localhost:{port}")
        self.sock.setsockopt(zmq.SUBSCRIBE, b"Temperatures")

    def run(self):
        while (True):
            string = self.sock.recv()
            topic, data = string.split()
            t, tempA, tempB, tempC = data.decode().split(',')
            self.updateTemperatures.emit(float(tempA), float(tempB), float(tempC))


class VoltagesWorker(QThread):
    updateVoltages = Signal(dict)

    def __init__(self, port=9990):
        QThread.__init__(self)
        self.context = zmq.Context()
        self.sock = self.context.socket(zmq.SUB)
        self.sock.connect(f"tcp://localhost:{port}")
        self.sock.setsockopt(zmq.SUBSCRIBE, b"Voltages")

    def run(self):
        while (True):
            string = self.sock.recv()
            topic, data = string.split()
            values = data.decode().split(',')
            self.updateVoltages.emit({
                key: float(value) for key, value in zip(
                    ["V_BIAS_LNA_CHX", "V_BIAS_LNA_CHY", "V_BIAS_LNA_CHZ", "M_CHX", "M_CHY", "M_CHZ", "VDD_CHX",
                     "VDD_CHY", "VDD_CHZ", "I_CHX", "I_CHY", "I_CHZ", "V_CHX", "V_CHY", "V_CHZ"], values[1:])
            })


class ArduinoStatusWorker(QThread):
    updateStatus = Signal(str)

    def __init__(self, port=9990):
        QThread.__init__(self)
        self.context = zmq.Context()
        self.sock = self.context.socket(zmq.SUB)
        self.sock.connect(f"tcp://localhost:{port}")
        self.sock.setsockopt(zmq.SUBSCRIBE, b"Status")

    def run(self):
        while (True):
            string = self.sock.recv()
            topic, data = string.split()
            self.updateStatus.emit("Temperatures and Voltages monitor: " + data.decode())


class DiscoveryWorker(QObject):
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
        self.disco_process = subprocess.Popen(['python', 'discovery_driver.py'])

    def __del__(self):
        self.disco_process.kill()

    def Launch_Measurements(self):
        self.push_sock.send_json(
            do_measurements.make_cmd("CHX", psd_output_dir='/tmp', psd_snapshots_count=256, d_tf_output_dir='/tmp',
                                     s_tf_output_dir='/tmp', d_tf_frequencies=np.logspace(2, 6, num=20).tolist(),
                                     s_tf_amplitude=.9, s_tf_steps=100))
        print(self.pull_sock.recv_json())


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

        self.voltagesWorker = VoltagesWorker()
        self.voltagesWorker.updateVoltages.connect(self.updateVoltages)
        self.voltagesWorker.start()
        self.voltagesWorker.moveToThread(self.voltagesWorker)

        self.arduinoStatusWorker = ArduinoStatusWorker()
        self.arduinoStatusWorker.updateStatus.connect(self.ui.statusbar.showMessage)
        self.arduinoStatusWorker.start()
        self.arduinoStatusWorker.moveToThread(self.arduinoStatusWorker)

        self.discoWorker = DiscoveryWorker()
        self.ui.Launch_Measurements.clicked.connect(self.discoWorker.Launch_Measurements)

    def updateTemperatures(self, tempA, tempB, tempC):
        self.ui.tempA_LCD.display(tempA)
        self.ui.tempB_LCD.display(tempB)
        self.ui.tempC_LCD.display(tempC)

    def updateVoltages(self, values):
        for ch in ["X", "Y", "Z"]:
            self.ui.__dict__[f"CH{ch}_PW_V"].display(1.e-3 * values[f"V_CH{ch}"])
            self.ui.__dict__[f"CH{ch}_PW_I"].display(1.e-3 * values[f"I_CH{ch}"])
            self.ui.__dict__[f"CH{ch}_VDD"].display(10. / 1024. * values[f"VDD_CH{ch}"])
            self.ui.__dict__[f"CH{ch}_BIAS"].display(5. / 1024. * values[f"V_BIAS_LNA_CH{ch}"])
            self.ui.__dict__[f"CH{ch}_M"].display(5. / 1024. * values[f"M_CH{ch}"])

    def quit_app(self):
        self.close()


def main(args=sys.argv):
    app = QApplication(args)
    application = ApplicationWindow()
    application.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
