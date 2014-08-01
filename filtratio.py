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
    5007: np.array([5006.843, 4958.911, 4931.227]),
    5755: 5755.08,
    6563: 6562.79,
    6583: np.array([6583.45, 6548.05, 6527.23]),
    6716: 6716.44,
    6731: 6730.816
}

multiplet_strengths = {
    5007: np.array([2.918, 1.0, 3.88e-4]),
    6583: np.array([2.963, 1.0, 5.33e-4]),
}

def _get_bandpass(fname):
    return pysynphot.ObsBandpass(fname)


def _vacuum_wavelength(wavid, topocentric_velocity):
    "Convert from wav identifier to an accurate (0.01 Ang) vacuum wavelength"
    wav = air_rest_wavelength.get(wavid, float(wavid))
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
        if line_id in multiplet_strengths:
            for wav, strength in zip(wavs, multiplet_strengths[line_id]):
                plt.axvline(wav, 0.0, 0.3*strength, color='r', lw=2)
        else:
            plt.axvline(wavs, 0.0, 0.9, color='b', lw=2)

    plt.xlim(*filterset.wavlimits())
    plt.legend(fontsize='small', loc='upper left')
    plt.xlabel("Vacuum wavelength, Angstrom")
    plt.ylabel("Filter throughput")
    plt.savefig('test-filtratio.pdf')




    
