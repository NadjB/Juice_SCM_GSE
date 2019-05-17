import numpy as np
from .fft import *
import peakutils


def merge_pikes(fftspec, index, width, scale=1.0):
    def merge(fftspec, index, width, scale=1.0):
        out = np.sum(fftspec[max(0, index-int(width/2)):min(len(fftspec), index+int(width/2)+1)]**2)
        return math.sqrt(out)*scale

    result = []
    if hasattr(index, '__iter__'):
        for i in index:
            result.append(merge(fftspec, i, width, scale))
        return result
    else:
        return merge(fftspec, index, width, scale)


def extract_pikes(waveform, frequency, scale, merging_width=50, window=None):
    spect = fft(waveform=waveform, sampling_frequency=frequency, window=window, remove_mean=True)
    fft_mod = spect["mod"]
    fft_mod[fft_mod < np.std(fft_mod)] = 0
    peaks = peakutils.indexes(fft_mod, min_dist=2)
    return [spect["f"][peaks], merge_pikes(spect["mod"], peaks, merging_width, scale)]


def tf(input, output, sampling_freq, window=True, removeMean=True):
    if len(input)==len(output) and len(input):
        if window is True:
            window=np.hanning(len(input))
        else:
            window=None
        in_spect = fft(waveform=input, sampling_frequency=sampling_freq, window=None, remove_mean=removeMean)
        out_spect = fft(waveform=output, sampling_frequency=sampling_freq, window=None, remove_mean=removeMean)
        freq = in_spect["f"]
        peaks = peakutils.indexes(in_spect["mod"], min_dist=4)
    return None
