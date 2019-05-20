#!/usr/bin/env python3


import sys, os
from functools import partial
import subprocess
import zmq, json
from datetime import datetime
from PySide2.QtWidgets import QMainWindow, QApplication
from PySide2.QtCore import Signal, QThread, Slot, QObject, QMetaObject
from juice_scm_gse.discovery_driver import do_measurements, turn_on_psu, turn_off_psu
import numpy as np
from juice_scm_gse.gui.settings_pannel import SettingsPannel
from juice_scm_gse.gui.progress_pannel import ProgressPannel
from juice_scm_gse.gui.mainwindow import Ui_MainWindow
from juice_scm_gse import config
from juice_scm_gse.utils import list_of_floats, ureg, Q_, mkdir
from juice_scm_gse.utils.mail import send_mail
import psutil

import logging as log


desktop_entry="""[Desktop Entry]
Version=1.0
Name=JUICE-SCM-EGSE
Comment=JUICE SCM EGSE
Exec={exec}
Icon={icon}
Path={path}
Terminal=false
Type=Application
StartupNotify=true
Categories=Utility;Application;"""

class TemperaturesWorker(QThread):
    updateTemperatures = Signal(float, float, float)

    def __init__(self, port=9990):
        QThread.__init__(self)
        self.context = zmq.Context()
        self.sock = self.context.socket(zmq.SUB)
        self.sock.connect(f"tcp://localhost:{port}")
        self.sock.setsockopt(zmq.SUBSCRIBE, b"Temperatures")

    def __del__(self):
        del self.sock
        del self.context

    def run(self):
        while True:
            try:
                string = self.sock.recv(flags=zmq.NOBLOCK)
                topic, data = string.split()
                t, tempA, tempB, tempC = data.decode().split(',')
                self.updateTemperatures.emit(float(tempA), float(tempB), float(tempC))
            except zmq.ZMQError:
                pass
            if self.isInterruptionRequested():
                return
            QThread.msleep(10)


class VoltagesWorker(QThread):
    updateVoltages = Signal(dict)
    restartDisco = Signal()

    def __init__(self, port=9990):
        QThread.__init__(self)
        self.context = zmq.Context()
        self.sock = self.context.socket(zmq.SUB)
        self.sock.connect(f"tcp://localhost:{port}")
        self.sock.setsockopt(zmq.SUBSCRIBE, b"Voltages")

    def __del__(self):
        del self.sock
        del self.context

    def run(self):
        while True:
            try:
                string = self.sock.recv(flags=zmq.NOBLOCK)
                topic, data = string.split()
                values = data.decode().split(',')
                values = {
                    key: float(value) for key, value in zip(
                        ["V_BIAS_LNA_CHX", "V_BIAS_LNA_CHY", "V_BIAS_LNA_CHZ", "M_CHX", "M_CHY", "M_CHZ", "VDD_CHX",
                         "VDD_CHY", "VDD_CHZ", "I_CHX", "I_CHY", "I_CHZ", "V_CHX", "V_CHY", "V_CHZ"], values[1:])
                }
                self.updateVoltages.emit(values)

                limit = Q_(config.asic_current_limit.get())
                if any([ureg.milliampere * 1e-3 * value > limit for value in
                        [values["I_CHX"], values["I_CHY"], values["I_CHZ"]]]):
                    log.critical(f'Reached current limit {limit}, CHX:{ureg.milliampere * 1e-3 * values["I_CHX"]}  CHY:{ureg.milliampere * 1e-3 * values["I_CHY"]}  CHZ:{ureg.milliampere * 1e-3 * values["I_CHZ"]}')
                    self.restartDisco.emit()
            except zmq.ZMQError:
                pass
            if self.isInterruptionRequested():
                return
            QThread.msleep(10)

class ArduinoStatusWorker(QThread):
    updateStatus = Signal(str)

    def __init__(self, port=9990):
        QThread.__init__(self)
        self.context = zmq.Context()
        self.sock = self.context.socket(zmq.SUB)
        self.sock.connect(f"tcp://localhost:{port}")
        self.sock.setsockopt(zmq.SUBSCRIBE, b"Status")
        self.arduino_process = None
        self.arduino_process_started = False

    def __del__(self):
        del self.sock
        del self.context

    def _arduino_process_is_alive(self):
        if self.arduino_process is None:
            return False
        if self.arduino_process.poll() is None:
            return True
        return False

    def start(self):
        if not self.arduino_process_started or not self._arduino_process_is_alive():
            for proc in psutil.process_iter():
                # check whether the process name matches
                if 'arduino_monitor.py' in proc.cmdline():
                    proc.kill()
            if os.path.exists('arduino_monitor.py'):
                self.arduino_process = subprocess.Popen(['python', 'arduino_monitor.py'])
            else:
                self.arduino_process = subprocess.Popen(['Juice_Ardiuno_Monitor'])
            self.arduino_process_started = True
        QThread.start(self)

    def stop(self):
        if self.arduino_process_started:
            self.arduino_process_started = False
            self.arduino_process.kill()

    def run(self):
        while True:
            try:
                string = self.sock.recv(flags=zmq.NOBLOCK)
                topic, data = string.split()
                self.updateStatus.emit("Temperatures and Voltages monitor: " + data.decode())
            except zmq.ZMQError:
                pass
            if self.isInterruptionRequested():
                self.stop()
                return
            QThread.msleep(10)


class DiscoveryWorker(QObject):
    measurementsDone = Signal()
    progress_update = Signal(str,float,str,float,str,float)

    def __init__(self, push_port=9991, pull_port=9992, progress_port=9993):
        QObject.__init__(self)
        self.thread = QThread()
        self.thread.start()
        self.moveToThread(self.thread)
        self.context = zmq.Context()
        self.push_sock = self.context.socket(zmq.PUSH)
        self.push_sock.bind(f"tcp://*:{push_port}")
        self.pull_sock = self.context.socket(zmq.PULL)
        self.pull_sock.bind(f"tcp://*:{pull_port}")
        self.progress_sock = self.context.socket(zmq.PULL)
        self.progress_sock.bind(f"tcp://*:{progress_port}")
        self.disco_process = None
        self.disco_process_started = False
        self.current_channel = ""
        self.channel_progress = 0.
        self.start()

    def __del__(self):
        self.disco_process.kill()
        del self.push_sock
        del self.pull_sock
        del self.context

    def _disco_process_is_alive(self):
        if self.disco_process is None:
            return False
        if self.disco_process.poll() is None:
            return True
        return False

    def start(self):
        if not self.disco_process_started or not self._disco_process_is_alive():
            for proc in psutil.process_iter():
                # check whether the process name matches
                if 'discovery_driver.py' in proc.cmdline():
                    proc.kill()
            if os.path.exists('discovery_driver.py'):
                self.disco_process = subprocess.Popen(['python', 'discovery_driver.py'])
            else:
                self.disco_process = subprocess.Popen(['Juice_Discovery_Driver'])
            QThread.sleep(2.)
            self.disco_process_started = True

    def stop(self):
        if self.disco_process_started:
            self.disco_process_started = False
            self.disco_process.kill()
            QThread.sleep(1.)

    @Slot()
    def turn_on(self):
        self.start()
        for channel in ['CHX', 'CHY', 'CHZ']:
            log.info(f"Turn on {channel}")
            self.push_sock.send_json(
                turn_on_psu.make_cmd(channel))
            log.info(self.pull_sock.recv_json())

    @Slot()
    def turn_off(self):
        self.start()
        for channel in ['CHX', 'CHY', 'CHZ']:
            log.info(f"Turn off {channel}")
            self.push_sock.send_json(
                turn_off_psu.make_cmd(channel))
            log.info(self.pull_sock.recv_json())

    def _progress(self):
        try:
            resp = json.loads(self.progress_sock.recv_json(flags=zmq.NOBLOCK))
            self.progress_update.emit(self.current_channel,self.channel_progress, resp["step"],resp["global_progress"],resp["step_detail"],resp["step_progress"])
        except zmq.ZMQError:
            pass

    def Launch_Measurements(self):
        self.start()
        now = str(datetime.now())
        i = 0.
        send_mail(server=config.mail_server.get(), sender="juicebot@lpp.polytechnique.fr",
                  recipients=config.mail_recipients.get(), subject="Starting measurement", html_body="",
                  username=config.mail_login.get(), password=config.mail_password.get(), port=465, use_tls=True)
        for channel in ['CHX', 'CHY', 'CHZ']:
            self.current_channel = channel
            self.channel_progress = i/3.
            i += 1.
            log.info(f"Starting measurements on {channel}")
            kwargs = dict(psd_output_dir=config.global_workdir.get() + f'/run-{now}/{channel}/psd',
                          psd_snapshots_count=int(config.psd_snapshots_count.get()),
                          psd_sampling_freq=list_of_floats(config.psd_sampling_freq.get()),
                          d_tf_frequencies=np.logspace(float(config.dtf_start_freq_exp.get()),
                                                       float(config.dtf_stop_freq_exp.get()),
                                                       num=int(config.dtf_freq_points.get())).tolist(),
                          d_tf_output_dir=config.global_workdir.get() + f'/run-{now}/{channel}/dtf',
                          s_tf_amplitude=float(config.stf_amplitude.get()),
                          s_tf_steps=int(config.stf_steps.get()),
                          s_tf_output_dir=config.global_workdir.get() + f'/run-{now}/{channel}/stf'
                          )
            self.push_sock.send_json(
                do_measurements.make_cmd(channel, **kwargs))
            while True:
                self._progress()
                try:
                    resp = self.pull_sock.recv_json(flags=zmq.NOBLOCK)
                    log.info(resp)
                    break
                except zmq.ZMQError:
                    pass
                if not self._disco_process_is_alive():
                    self.start()
                    return
        self.measurementsDone.emit()
        send_mail(server=config.mail_server.get(), sender="juicebot@lpp.polytechnique.fr",
                  recipients=config.mail_recipients.get(), subject="Measurement Done!", html_body="",
                  username=config.mail_login.get(), password=config.mail_password.get(), port=465, use_tls=True)


class ApplicationWindow(QMainWindow):
    """Main Window"""

    def __init__(self, parent=None):
        super(ApplicationWindow, self).__init__(parent)
        self.settings_ui = SettingsPannel()
        self.progress_pannel = ProgressPannel()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.actionSettings.triggered.connect(self.settings_ui.show)
        self.ui.power_button.clicked.connect(self.turn_on)
        self.is_on = False
        self.tempWorker = TemperaturesWorker()
        self.tempWorker.updateTemperatures.connect(self.updateTemperatures)
        self.tempWorker.start()
        self.tempWorker.moveToThread(self.tempWorker)

        self.arduinoStatusWorker = ArduinoStatusWorker()
        self.arduinoStatusWorker.updateStatus.connect(self.ui.statusbar.showMessage)
        self.arduinoStatusWorker.start()
        self.arduinoStatusWorker.moveToThread(self.arduinoStatusWorker)

        self.already_restarting_disco = False
        self.discoWorker = DiscoveryWorker()
        self.ui.Launch_Measurements.clicked.connect(self.discoWorker.Launch_Measurements)
        self.ui.Launch_Measurements.clicked.connect(self.progress_pannel.show)
        self.ui.Launch_Measurements.clicked.connect(partial(self.ui.Launch_Measurements.setDisabled, True))
        self.ui.Launch_Measurements.clicked.connect(partial(self.ui.power_button.setDisabled, True))
        self.discoWorker.measurementsDone.connect(partial(self.ui.Launch_Measurements.setEnabled, True))
        self.discoWorker.measurementsDone.connect(partial(self.ui.power_button.setEnabled, True))
        self.discoWorker.measurementsDone.connect(self.progress_pannel.hide)
        self.discoWorker.progress_update.connect(self.progress_pannel.update_progress)

        self.voltagesWorker = VoltagesWorker()
        self.voltagesWorker.updateVoltages.connect(self.updateVoltages)
        self.voltagesWorker.start()
        self.voltagesWorker.moveToThread(self.voltagesWorker)
        self.voltagesWorker.restartDisco.connect(self.restart_disco)

    def __del__(self):
        for thr in [self.arduinoStatusWorker,self.tempWorker,self.voltagesWorker]:
            thr.requestInterruption()
            while thr.isRunning():
                QThread.msleep(10)
        del self.discoWorker
        del self.arduinoStatusWorker
        del self.tempWorker
        del self.voltagesWorker
        self.close()

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

    def restart_disco(self):
        if self.already_restarting_disco:
            return
        self.already_restarting_disco = True
        self.discoWorker.stop()
        self.already_restarting_disco = False
        self.ui.Launch_Measurements.setEnabled(True)

    def turn_on(self):
        if self.is_on:
            self.ui.Launch_Measurements.setEnabled(True)
            self.ui.power_button.setText("Turn ON")
            QMetaObject.invokeMethod(self.discoWorker, "turn_off")
            self.is_on = False
        else:
            self.ui.Launch_Measurements.setEnabled(False)
            self.ui.power_button.setText("Turn OFF")
            QMetaObject.invokeMethod(self.discoWorker, "turn_on")
            self.is_on = True

    def quit_app(self):
        self.close()


def main(args=sys.argv):
    lib_dir = os.path.dirname(os.path.realpath(__file__))
    bin_dir = lib_dir + "/../../../../bin"
    desktop_entry_path = os.path.expanduser("~")+'/.local/share/applications/Juice-scm-egse.desktop'
    if not os.path.exists(desktop_entry_path):
        with open(desktop_entry_path,'w') as d:
            d.write(desktop_entry.format(exec=bin_dir+"/Juice_SCM_GSE",icon="juice-scm-egse.svg",path=bin_dir))
    mkdir(config.log_dir())
    log.basicConfig(filename=f'{config.log_dir()}/gui-{datetime.now()}.log', format='%(asctime)s - %(message)s',
                    level=log.INFO)
    log.getLogger().addHandler(log.StreamHandler(sys.stdout))
    app = QApplication(args)
    application = ApplicationWindow()
    application.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
