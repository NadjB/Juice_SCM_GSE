#!/usr/bin/env python3


import sys
import zmq
from pathlib import Path
from PySide2.QtWidgets import QMainWindow, QApplication, QMessageBox
from PySide2.QtCore import QCoreApplication, Signal, QThread

from juice_scm_gse.gui.mainwindow import Ui_MainWindow


class ApplicationWindow(QMainWindow):
    """Main Window"""
    def __init__(self, parent=None):
        super(ApplicationWindow, self).__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

    def quit_app(self):
        self.close()

def main(args=sys.argv):
    app = QApplication(args)
    application = ApplicationWindow()
    application.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
