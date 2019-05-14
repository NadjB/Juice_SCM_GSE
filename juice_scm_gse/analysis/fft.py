
import numpy as np

def __fact(window):
    """Computes the amplitude conpensation factor to apply to a FFT for the given window.
    Just equivalent to 1/RMS(window).

    Args:
       window ( iterable object):  The windows to analyse.

    Returns:
        float: The compensation factor.
    """
    return 1./np.sqrt(np.mean(np.square(window)))


def fft(waveform, sampling_frequency=1., window=None, remove_mean=True):
    """Compute the FFT of the given signal wf and return result in a fashion way.

    Args:
        wf ( iterable object):  The time domain signal on which you want to compute FFT.
        fs (Optional[float]): Sampling frequency of wf, used for frequency vector normalization.
        window ( Optional[iterable object]):  The window to apply.
        removeMean (Optional[bool]):  Set to True if you want to remove mean on signal befor
            computing FFT.

    Returns:
        dict: The FFT result simplified and stored in a dict. The FFT result is trucated from F=0 to
            F=Fs/2 and amplitude is normalized to its real value and in case of windowing, the
            window correction factor is applied.
            keys ( strings ):
                f ( numpy array of float ): Frequency vector normalized to given "fs" frequency
                mod ( numpy array of float ): Amplitude vector divided by len(wf) and corrected if a
                    window is applied.
                phi ( numpy array of float ): Phase vector.
    """
    scale_factor = 1./len(waveform)
    if remove_mean:
        waveform = waveform - np.mean(waveform)
    if not window is None:
        waveform = waveform*window
        scale_factor = scale_factor *__fact(window)
    spectrum = np.fft.fft(waveform) *scale_factor
    frequency = np.fft.fftfreq(len(spectrum), 1/sampling_frequency)
    frequency[int(len(frequency)/2)] = abs(frequency[int(len(frequency)/2)])
    return {"f":frequency[0:int(len(frequency)/2)+1],
            "mod":abs(spectrum[0:int(len(spectrum)/2)+1]),
            "phi":np.angle(spectrum[0:int(len(spectrum)/2)+1], False)}

