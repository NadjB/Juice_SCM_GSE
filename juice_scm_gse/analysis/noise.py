
import numpy as np
from .fft import *


def psd(waveforms,sampling_freq,window=True,removeMean=True):
    if len(waveforms):
        if window is True:
            window=np.hanning(len(waveforms[0]))
        else:
            window=None
        spect = fft(waveform=waveforms[0], sampling_frequency=sampling_freq, window=None, remove_mean=removeMean)
        freq = spect["f"]
        psd = spect["mod"]**2
        for wf in waveforms[1:]:
                psd += (fft(waveform=wf, sampling_frequency=sampling_freq, window=None, remove_mean=removeMean)["mod"])**2
        # factor 2 accounts for negative and positives frequencies
        # in count^2/Hz unit
        psd =  psd/len(waveforms) / (sampling_freq/len(waveforms[0]))
        return freq, psd
    return None
