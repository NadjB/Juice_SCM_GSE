from PySide2.QtWidgets import QWidget
from PySide2.QtCore import Qt
from .progress import Ui_Progress


class ProgressPannel(QWidget):
    def __init__(self, parent=None):
        super(ProgressPannel, self).__init__(parent)
        self.ui = Ui_Progress()
        self.ui.setupUi(self)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)

    def update_progress(self,channel_name:str,channel_progress, step:str, global_progress:float,step_detail:str, step_progress:float):
        self.ui.channel_name.setText(channel_name)
        self.ui.channel_progress.setValue(int(channel_progress*100))
        self.ui.step_name.setText(step)
        self.ui.global_progress.setValue(int(global_progress*100))
        self.ui.step_detail.setText(step_detail)
        self.ui.step_progress.setValue(int(step_progress*100))
