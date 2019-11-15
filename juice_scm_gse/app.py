#!/usr/bin/env python3


import sys, os
from functools import partial
import subprocess
import zmq, json
from datetime import datetime

from PySide2.QtGui import QValidator, QRegExpValidator
from PySide2.QtWidgets import QMainWindow, QApplication, QWidget, QMessageBox
from PySide2.QtCore import Signal, QThread, Slot, QObject, QMetaObject, QGenericArgument, Qt
#from juice_scm_gse.arduino_monitor import alimManagement
#from juice_scm_gse.discovery_driver import do_measurements, turn_on_psu, turn_off_psu
import numpy as np
import juice_scm_gse.config as cfg
from juice_scm_gse.gui.settings_pannel import SettingsPannel
from juice_scm_gse.gui.progress_pannel import ProgressPannel
from juice_scm_gse.gui.mainwindow import Ui_MainWindow
from juice_scm_gse import config
from juice_scm_gse.utils import list_of_floats, ureg, Q_, mkdir
from juice_scm_gse.utils.mail import send_mail
import psutil

import logging as log

desktop_entry = """[Desktop Entry]
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


class VoltagesWorker(QThread):
    updateVoltages = Signal(dict)
    restartDisco = Signal()
    signalUpdatePower = Signal(bool)


    def __init__(self, port=9990, portPair=9991):
        QThread.__init__(self)                                                                                          #Creat a thread
        self.context = zmq.Context()                                                                                    #Initialize ZMQ
        self.sock = self.context.socket(zmq.SUB)                                                                        #Configure it as Subscriber (mode Publish/Subscribe)
        self.sock.connect(f"tcp://localhost:{port}")
        self.sock.setsockopt(zmq.SUBSCRIBE, b"Voltages")                                                                #Subscribe to the topic: Voltages

        self.sockPair = self.context.socket(zmq.PAIR)
        self.sockPair.connect(f"tcp://localhost:{portPair}")

        self.alimsEnabled = False
        #self.asicsList = []

    def asics(self, asic="XXX"):

        asicID = f"ASIC_JUICEMagic3_SN_{asic}"
        self.sockPair.send(asicID.encode())
        print(f"{asicID} sent")



    def startAlims(self):

        if self.alimsEnabled:
            message = f"Disable alims"

        else:
            message = f"Enable alims"

        self.sockPair.send(message.encode())
        self.alimsEnabled = not self.alimsEnabled
        self.signalUpdatePower.emit(self.alimsEnabled)


    def __del__(self):
        del self.sock
        del self.sockPair
        del self.context

    def run(self):
        while True:
            try:
                string = self.sock.recv(flags=zmq.NOBLOCK)                                                              #Recieve the Voltages
                topic, data = string.split()
                values = data.decode().split(',')
                values = {                                                                                              #??? damn tricky
                    key: float(value) for key, value in zip(
                        ["VDD_CHX", "M_CHX", "V_BIAS_LNA_CHX", "S_CHX", "RTN_CHX",
                         "VDD_CHY", "M_CHY", "V_BIAS_LNA_CHY", "S_CHY", "RTN_CHY",
                         "VDD_CHZ", "M_CHZ", "V_BIAS_LNA_CHZ", "S_CHZ", "RTN_CHZ",
                         "ADC_VDD_CHX", "ADC_M_CHX", "ADC_V_BIAS_LNA_CHX", "ADC_S_CHX", "ADC_RTN_CHX",
                         "ADC_VDD_CHY", "ADC_M_CHY", "ADC_V_BIAS_LNA_CHY", "ADC_S_CHY", "ADC_RTN_CHY",
                         "ADC_VDD_CHZ", "ADC_M_CHZ", "ADC_V_BIAS_LNA_CHZ", "ADC_S_CHZ", "ADC_RTN_CHZ",
                         "CONSO_CHX", "CONSO_CHY", "CONSO_CHZ",
                         "ALIM_CHX", "ALIM_CHY", "ALIM_CHZ"],
                        values[1:])
                }
                for key, value in values.items():
                    if "VDD" in key:
                        if "ADC" in key:
                            values[key] = (6.0 + 0.023) / 4096. * value
                        else:
                            values[key] = (6.0 + 0.023) / 1024. * value

                    elif "CONSO" in key:
                        values[key] = value / 1000.

                    elif "ALIM" in key:
                        values[key] = value / 1000.
                    else:
                        if "ADC" in key:
                            values[key] = 5. / 4096. * value
                        else:
                            values[key] = 5. / 1024. * value

                print(values)
                self.updateVoltages.emit(values)                                                                        #MAJ Voltages

            except zmq.ZMQError:
                pass
            if self.isInterruptionRequested():
                return
            QThread.msleep(10)
            QApplication.processEvents()


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
                    proc.kill()                                                                                         #If the process exist kill it to start clean
            if os.path.exists('arduino_monitor.py'):                                                                    #If "arduino_monitor.py" existe create a subprocess using it
                self.arduino_process = subprocess.Popen(['python', 'arduino_monitor.py'])                               #???
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
                string = self.sock.recv(flags=zmq.NOBLOCK)                                                              #recieve msgs
                topic, data = string.split()
                self.updateStatus.emit("Temperatures and Voltages monitor: " + data.decode())
            except zmq.ZMQError:
                pass
            if self.isInterruptionRequested():
                self.stop()
                return
            QThread.msleep(10)



class ApplicationWindow(QMainWindow):
    """Main Window"""
    Launch_Measurements = Signal(str)

    def __init__(self, parent=None):
        super(ApplicationWindow, self).__init__(parent)
        self.settings_ui = SettingsPannel()
        self.progress_pannel = ProgressPannel()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.actionSettings.triggered.connect(self.settings_ui.show)
        self.asicsList = []
        self.acknowledgedAsicID = False
        self.asicPowered = False
        self.asicFileName = ""
        self.path = cfg.global_workdir.get() + "/ASICs"
        mkdir(self.path)  # create a "monitor" file in the working directory
        self.measuementRequested = False


#        self.ui.power_button.clicked.connect(self.turn_on)
#        self.is_on = False
#        self.tempWorker = TemperaturesWorker()
#        self.tempWorker.updateTemperatures.connect(self.updateTemperatures)
#        self.tempWorker.start()
#        self.tempWorker.moveToThread(self.tempWorker)

        self.arduinoStatusWorker = ArduinoStatusWorker()
        self.arduinoStatusWorker.updateStatus.connect(self.ui.statusbar.showMessage)
        self.arduinoStatusWorker.start()
        self.arduinoStatusWorker.moveToThread(self.arduinoStatusWorker)

        self.voltagesWorker = VoltagesWorker()
        self.voltagesWorker.updateVoltages.connect(self.updateVoltages)
        self.voltagesWorker.updateVoltages.connect(self.asicRecording)
        self.voltagesWorker.start()
        self.voltagesWorker.moveToThread(self.voltagesWorker)
        self.ui.power_button.clicked.connect(self.voltagesWorker.startAlims, Qt.QueuedConnection)
        self.voltagesWorker.signalUpdatePower.connect(self.updatePowerButton)
        self.ui.asicSN.setValidator(QRegExpValidator("[0-9]{3}"))                                                       #3 Chifre
        self.ui.asicSN.returnPressed.connect(lambda: print("Declenché"))                                                #test
        self.ui.asicSN.returnPressed.connect(lambda: self.asicManagement(self.ui.asicSN.text()))
        self.ui.Launch_Measurements.clicked.connect(self.requestMeasurement)
        self.ui.asicsListe.currentIndexChanged.connect(lambda: self.ui.asicSN.setText(self.ui.asicsListe.currentText()))
        self.ui.asicsListe.currentIndexChanged.connect(lambda: self.asicManagement(False))




        # self.already_restarting_disco = False
        # self.discoWorker = DiscoveryWorker()
        # self.ui.Launch_Measurements.clicked.connect(self.start_measurement)
        # self.Launch_Measurements.connect(self.discoWorker.Launch_Measurements)
        # self.ui.Launch_Measurements.clicked.connect(self.progress_pannel.show)
        # self.ui.Launch_Measurements.clicked.connect(partial(self.ui.Launch_Measurements.setDisabled, True))
        # self.ui.Launch_Measurements.clicked.connect(partial(self.ui.power_button.setDisabled, True))
        #
        # self.discoWorker.measurementsDone.connect(partial(self.ui.Launch_Measurements.setEnabled, True))
        # self.discoWorker.measurementsDone.connect(partial(self.ui.power_button.setEnabled, True))
        # self.discoWorker.measurementsDone.connect(self.progress_pannel.hide)
        # self.discoWorker.progress_update.connect(self.progress_pannel.update_progress)

#        self.voltagesWorker.restartDisco.connect(self.restart_disco)


    def __del__(self):
        for thr in [self.arduinoStatusWorker, self.voltagesWorker]:
            thr.requestInterruption()
            while thr.isRunning():
                QThread.msleep(10)
#        del self.discoWorker
        del self.arduinoStatusWorker
#        del self.tempWorker
        del self.voltagesWorker
        self.close()

#    def updateTemperatures(self, tempA, tempB, tempC):
#        self.ui.tempA_LCD.display(tempA)
#        self.ui.tempB_LCD.display(tempB)
#        self.ui.tempC_LCD.display(tempC)

    def asicManagement(self, asicID="Rien n'est passé"):

        print(asicID)
        if asicID in self.asicsList:
            choice = QMessageBox.question(self, 'Conflict',
                                                f"{asicID}\n\nThis ID already exist, begin anyway?",
                                                QMessageBox.Yes | QMessageBox.No)
            if choice == QMessageBox.Yes:
                self.acknowledgedAsicID = True
                self.asicFileName = f"{self.path}/ASIC_JUICEMagic3_SN_{asicID}-{str(datetime.now())}.txt"  # create a file with the current date to dump the data
                print(self.asicFileName)
                self.voltagesWorker.asics(asicID)
                self.ui.asicSN.setStyleSheet("QLineEdit {background-color: green;}")

            else:
                pass

        elif asicID == False:
            self.acknowledgedAsicID = False
            self.ui.asicSN.setStyleSheet('')



        else:
            choice = QMessageBox.question(self, 'Confirmation',                                                         #confirmation a enlever
                                                f"The ID you entered is \n\n{asicID}\n\nconfirm?",
                                                QMessageBox.Yes | QMessageBox.No)
            if choice == QMessageBox.Yes:
                self.asicsList.append(asicID)
                self.ui.asicsListe.clear()                                                                              #Sauvage mais fonctionne
                self.ui.asicsListe.addItems(self.asicsList[::-1])
                self.acknowledgedAsicID = True
                self.asicFileName = f"{self.path}/ASIC_JUICEMagic3_SN_{asicID}-{str(datetime.now())}.txt"  # create a file with the current date to dump the data
                print(self.asicFileName)
                self.voltagesWorker.asics(asicID)
                self.ui.asicSN.setStyleSheet("QLineEdit {background-color: green;}")


            else:
                pass

    def requestMeasurement(self):
        self.measuementRequested = True

    def asicRecording(self, values):
        if self.acknowledgedAsicID and self.asicPowered:
            self.ui.asicSN.setDisabled(True)
            self.ui.asicsListe.setDisabled(True)
            self.ui.Launch_Measurements.setEnabled(True)
            if self.measuementRequested:
                self.ui.Launch_Measurements.setDisabled(True)
                self.ui.Launch_Measurements.setStyleSheet('QPushButton {background-color: #69ff69;}')

                with open(self.asicFileName, 'a') as out:
                    out.write(str(datetime.now()) + '\t')
                    for channel, value in values.items():
                        out.write(f"{channel}: {value}, ")

                    out.write('\n')
                    print("recording")
        else:
            self.ui.Launch_Measurements.setStyleSheet('')
            self.ui.Launch_Measurements.setDisabled(True)
            self.ui.asicSN.setEnabled(True)
            self.ui.asicsListe.setEnabled(True)


    def updateVoltages(self, values):
        if self.measuementRequested:
            for ch in ["X", "Y", "Z"]:
                self.ui.__dict__[f"CH{ch}_VDD"].display(values[f"VDD_CH{ch}"])
                self.ui.__dict__[f"CH{ch}_BIAS"].display(values[f"V_BIAS_LNA_CH{ch}"])
                self.ui.__dict__[f"CH{ch}_M"].display(values[f"M_CH{ch}"])
                self.ui.__dict__[f"CH{ch}_RTN"].display(values[f"RTN_CH{ch}"])
                self.ui.__dict__[f"CH{ch}_S"].display(values[f"S_CH{ch}"])
                self.ui.__dict__[f"CH{ch}_I"].display(values[f"CONSO_CH{ch}"])
                self.ui.__dict__[f"CH{ch}_V"].display(values[f"ALIM_CH{ch}"])
                self.ui.__dict__[f"CH{ch}_VDD_ADC"].display(values[f"ADC_VDD_CH{ch}"])
                self.ui.__dict__[f"CH{ch}_BIAS_ADC"].display(values[f"ADC_V_BIAS_LNA_CH{ch}"])
                self.ui.__dict__[f"CH{ch}_M_ADC"].display(values[f"ADC_M_CH{ch}"])
                self.ui.__dict__[f"CH{ch}_RTN_ADC"].display(values[f"ADC_RTN_CH{ch}"])
                self.ui.__dict__[f"CH{ch}_S_ADC"].display(values[f"ADC_S_CH{ch}"])


    def updatePowerButton(self, powered):
        if powered:
            self.ui.power_button.setText("Alive")
            self.ui.power_button.setStyleSheet('QPushButton {background-color: green;}')
            self.asicPowered = True
            if self.asicsList:
                if self.asicsList[-1] == self.ui.asicSN.text():
                    self.acknowledgedAsicID = True
                    self.ui.asicSN.setStyleSheet("QLineEdit {background-color: green;}")

        else:
            self.ui.power_button.setText("Dead")
            self.ui.power_button.setStyleSheet('QPushButton {background-color: #900000;}')
            self.asicManagement(False)
            self.measuementRequested = False
            self.asicPowered = False


    def start_measurement(self):
        now = str(datetime.now())
        work_dir = f'/{config.global_workdir.get()}/run-{now}/'
        self.Launch_Measurements.emit(work_dir)
        mkdir(work_dir)
        manifest = {
            section_name: {name: (value if 'pass' not in name else '******') for name, value in section_values.items()}
            for section_name, section_values in config._config.items()}
        manifest["result_dir"] = work_dir
        manifest["notes"] = self.ui.notes.toPlainText()
        manifest["start_time"] = now
        with open(f'{work_dir}/config.json', 'w') as out:
            out.write(json.dumps(manifest))
        manifest_html = json.dumps(manifest, indent=4).replace(' ', '&nbsp').replace(',\n', ',<br>').replace('\n',
                                                                                                             '<br>')
        html = f'''
 <!DOCTYPE html>
<html>
<body>
<h1>Measurement started at {now}</h1>
<p>
{manifest_html}
</p>

</body>
</html> 
        '''
        send_mail(server=config.mail_server.get(), sender="juicebot@lpp.polytechnique.fr",
                  recipients=config.mail_recipients.get(), subject="Starting measurement", html_body=html,
                  username=config.mail_login.get(), password=config.mail_password.get(), port=465, use_tls=True)

    def quit_app(self):
        self.close()


def main(args=sys.argv):
    lib_dir = os.path.dirname(os.path.realpath(__file__))
    bin_dir = lib_dir + "/../../../../bin"
    desktop_entry_path = os.path.expanduser("~") + '/.local/share/applications/Juice-scm-egse.desktop'
    if not os.path.exists(desktop_entry_path):
        with open(desktop_entry_path, 'w') as d:
            d.write(desktop_entry.format(exec=bin_dir + "/Juice_SCM_GSE", icon="juice-scm-egse.svg", path=bin_dir))
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
