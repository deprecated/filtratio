from __future__ import print_function
import numpy as np
import pysynphot

AIR_REFRACTIVE_INDEX = 1.000277 # @STP according to Wikipedia
LIGHTSPEED = 2.99792458e5       # c in km/s

# Accurate rest wavelengths (Source: NIST)
air_rest_wavelength = {
    4340: 4340.47,
    4363: 4363.21,
    4861: 4861.63,
    5007: {5006.843: 2.918, 4958.911: 1.0, 4931.227: 3.88e-4},
    5755: 5755.08,
    6563: 6562.79,
    6583: {6583.45: 2.963, 6548.05: 1.0, 6527.23: 5.33e-4},
    6716: 6716.44,
    6731: 6730.816
}


def _get_bandpass(fname):
    return pysynphot.ObsBandpass(fname)


def _vacuum_wavelength(wav0, topocentric_velocity):
    "Convert from wav identifier to an accurate (0.01 Ang) vacuum wavelength"
    wav_or_dict = air_rest_wavelength.get(wav0, float(wav0))
    try:
        # case where we have a dict of multiplet components
        wav = np.array(list(wav_or_dict.keys()))
    except:
        # case where we just have a number
        wav = float(wav_or_dict)
    return  wav*AIR_REFRACTIVE_INDEX*(1.0 + topocentric_velocity/LIGHTSPEED)


class Filterset(object):
    """A set of three emission line filters for measuring a line ratio"""

    def __init__(self, filter_ids, line_ids, doppler=0.0):
        assert len(filter_ids) == 3, 'Need to specify exactly 3 filters'
        assert len(line_ids) == 2, 'Need to specify exactly 2 emission lines'
        self.filter_ids = filter_ids
        self.line_ids = line_ids
        self.line_vac_wavs = [_vacuum_wavelength(wav0, doppler) for wav0 in line_ids]
        self.filter_bandpasses = [_get_bandpass(fn) for fn in filter_ids]

    def wavlimits(self):
        """Find suitable limits for plotting
        """
        wavmin = 1.e5
        wavmax = 0.0
        for T in self.filter_bandpasses:
            wavmin = min(wavmin, T.pivot() - T.rectwidth())
            wavmax = max(wavmax, T.pivot() + T.rectwidth())
        return wavmin - 100, wavmax + 100

if __name__ == "__main__":
    from matplotlib import pyplot as plt
    
    filterset = Filterset(["wfpc2,f658n", "wfpc2,f656n", "wfpc2,f547m"], [6563, 6583])
    for T, fn in zip(filterset.filter_bandpasses, filterset.filter_ids):
        plt.plot(T.wave, T.throughput, label=fn)
    for line_id, wavs in zip(filterset.line_ids, filterset.line_vac_wavs):
        for wav0, vacwav in zip(air_rest_wavelength[line_id].keys(),
                                np.atleast_1d(wavs)):
            try: 
                strength = air_rest_wavelength[line_id][wav0]
            except:
                strength = 3.0
            plt.axvline(wav0, 0.0, 0.3*strength, color='r', lw=2)

    plt.xlim(*filterset.wavlimits())
    plt.legend(fontsize='small', loc='upper left')
    plt.xlabel("Vacuum wavelength, Angstrom")
    plt.ylabel("Filter throughput")
    plt.savefig('test-filtratio.pdf')




    
