from PySide2.QtWidgets import QDialog
import juice_scm_gse.config as cfg
from .settings import Ui_Settings


class SettingsPannel(QDialog):
    cfg_items = ['global_workdir','mail_server', 'mail_login', 'mail_password','mail_recipients', 'psd_snapshots_count', 'psd_sampling_freq',
                 'dtf_start_freq_exp', 'dtf_stop_freq_exp', 'dtf_freq_points', 'stf_amplitude', 'stf_steps',
                 'asic_chx_disco', 'asic_chy_disco', 'asic_chz_disco', 'asic_current_limit']

    def __init__(self, parent=None):
        super(SettingsPannel, self).__init__(parent)
        self.ui = Ui_Settings()
        self.ui.setupUi(self)
        self.load_settings()
        self.accepted.connect(self.validate)
        self.rejected.connect(self.cancel)

    def load_settings(self):
        for item in self.cfg_items:
            self.ui.__dict__[item].setText(cfg.__dict__[item].get())

    def save_settings(self):
        for item in self.cfg_items:
            cfg.__dict__[item].set(self.ui.__dict__[item].text())

    def validate(self):
        self.save_settings()

    def cancel(self):
        self.load_settings()
