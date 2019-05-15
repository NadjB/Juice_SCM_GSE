import configparser, os
from appdirs import user_config_dir
from juice_scm_gse.utils import mkdir

_CONFIG_FNAME = str(user_config_dir(appname="Juice_SCM_EGSE", appauthor="LPP")) + "/config.ini"
mkdir(os.path.dirname(_CONFIG_FNAME))
_config = configparser.ConfigParser()
_config.read(_CONFIG_FNAME)


class ConfigEntry:
    def __init__(self, key1, key2, default=""):
        self.key1 = key1
        self.key2 = key2
        self.default = default

    def get(self):
        if self.key1 in _config and self.key2 in _config[self.key1]:
            return _config[self.key1][self.key2]
        else:
            return self.default

    def set(self, value):
        if self.key1 not in _config:
            _config.add_section(self.key1)
        _config[self.key1][self.key2] = value
        with open(_CONFIG_FNAME, 'w') as f:
            _config.write(f)


global_workdir = ConfigEntry("Global", "workdir", "/tmp")

mail_server = ConfigEntry("mail", "server", "localhost")
mail_login = ConfigEntry("mail", "login")
mail_password = ConfigEntry("mail", "password")
mail_recipients = ConfigEntry("mail", "recipients")

asic_chx_disco = ConfigEntry("ASIC", "chx_disco")
asic_chy_disco = ConfigEntry("ASIC", "chy_disco")
asic_chz_disco = ConfigEntry("ASIC", "chz_disco")
asic_current_limit = ConfigEntry("ASIC", "current_limit","11mA")

psd_snapshots_count = ConfigEntry("PSD", "snapshots_count", "10")
psd_sampling_freq = ConfigEntry("PSD", "sampling_freq", "100000.")

dtf_start_freq_exp = ConfigEntry("DTF", "start_freq_exp", "0.")
dtf_stop_freq_exp = ConfigEntry("DTF", "stop_freq_exp", "6.")
dtf_freq_points = ConfigEntry("DTF", "freq_points", "200")

stf_amplitude = ConfigEntry("STF", "amplitude", ".5")
stf_steps = ConfigEntry("STF", "steps", "100")
