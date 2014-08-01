from __future__ import print_function

import numpy as np
import pysynphot

AIR_REFRACTIVE_INDEX = 1.000277 # @STP according to Wikipedia
LIGHTSPEED = 2.99792458e5       # c in km/s

class Bandpass(object):
    """A combination of telescope, instrument, camera/channel/ccd, filter

A wrapper around pysynphot.ObsBandpass
    """
    
    # Line transmission adjustments (determined by in-flight calibration)
    T_adjustments = {}

    def __init__(self, longname='wfc3,uvis1,f547m'):
        self.longname = longname
        try:
            # Cases such as acs,wfc1,f658n
            self.instrument, self.channel, self.fname = longname.split(',')
        except ValueError:
            # Cases such as wfpc2,f502n
            self.instrument, self.fname = longname.split(',')
            self.channel = None
        # Delegate all the hard work to pysynphot
        self._synphot_bp = pysynphot.ObsBandpass(longname)
        # Wavelength array
        self.wave = self._synphot_bp.wave
        # Transmission throughput curve array
        self.T = self._synphot_bp.throughput
        # Maximum transmission of filter
        self.Tm = self.T.max()
        # Rectangular width of filter
        self.Wj = np.trapz(self.T, self.wave)/self.Tm
        # Central wavelength of filter
        self.wav0 = self._synphot_bp.pivot()
      
    def Ti(self, emline):
        "Filter transmission at wavelength of line i (emline)"
        correction = self.T_adjustments.get((emline.wavid, self.longname), 1.0)
        return correction*np.interp(emline.wave, self.wave, self.T)

    def Wtwid(self, emline, kji=1.0):
        """Find W-twiddle for a given line of wavelength wav0
        with respect to a filter transmission curve T(wavs).
        And with color correction kji
        """
        return kji*self.Tm*self.Wj/self.Ti(emline)
  


# Accurate rest wavelengths (Source: NIST)
air_rest_wavelengths = {
    "H I 4340": 4340.47,
    "[O III] 4363": 4363.21,
    "H I 4861": 4861.63,
    "[O III] 5007": np.array([5006.843, 4958.911, 4931.227]),
    "[N II] 5755": 5755.08,
    "H I 6563": 6562.79,
    "[N II] 6583": np.array([6583.45, 6548.05, 6527.23]),
    "[S II] 6716": 6716.44,
    "[S II] 6731": 6730.816
}

# Source: NIST
multiplet_strengths = {
    "[O III] 5007": np.array([2.918, 1.0, 3.88e-4]),
    "[N II] 6583": np.array([2.963, 1.0, 5.33e-4]),
}

def _split_ids(lineid):
    pieces = lineid.split()
    return ' '.join(pieces[:-1]), pieces[-1]

class EmissionLine(object):
    velocity = 0.0
    def __init__(self, lineid, velocity=None):
        self.lineid = lineid
        self.species, self.wavid = _split_ids(lineid)
        # Rest wavelength(s) in air
        self.wav0_air = air_rest_wavelengths.get(lineid, float(self.wavid))
        try: 
            self.multiplicity = len(self.wav0_air)
            self.intensity = multiplet_strengths.get(lineid,
                                                     np.ones_like(self.wav0_air))
        except TypeError:
            # If scalar then it is a single component
            self.multiplicity = 1
            self.intensity = 1.0
        # Rest wavelength in vacuum
        self.wav0 = self.wav0_air * AIR_REFRACTIVE_INDEX
        # Topocentric velocity
        if velocity is None:
            # Allow velocity to be set at the class level for all lines
            self.velocity = self.__class__.velocity
        # Observed wavelength in vacuum
        self.wave = self.wav0 * (1.0 + self.velocity/LIGHTSPEED)
        

class Filterset(object):
    """A set of three emission line filters for measuring a line ratio"""

    def __init__(self, bpnames, lineids, velocity=0.0):
        assert len(bpnames) == 3, 'Need to specify exactly 3 filters'
        assert len(lineids) == 2, 'Need to specify exactly 2 emission lines'
        self.bpnames = bpnames
        self.lineids = lineids
        self.emlines = [EmissionLine(lineid, velocity) for lineid in lineids]
        self.bandpasses = [Bandpass(longname) for longname in bpnames]
        self._calculate_coefficients()

    def wavlimits(self):
        """Find suitable limits for plotting
        """
        wavmin = 1.e5
        wavmax = 0.0
        for bp in self.bandpasses:
            wavmin = min(wavmin, bp.wav0 - bp.Wj)
            wavmax = max(wavmax, bp.wav0 + bp.Wj)
        return wavmin - 100, wavmax + 100

    def _calculate_coefficients(self):
        I, II, III = self.bandpasses
        e1, e2 = self.emlines
        if e1.multiplicity == 1:
            T1_I = I.Ti(e1)
            T1_II = II.Ti(e1)
            T1_III = III.Ti(e1)
        else:
            T1_I = np.sum(I.Ti(e1)*e1.intensity) / e1.intensity.sum()
            T1_II = np.sum(II.Ti(e1)*e1.intensity) / e1.intensity.sum()
            T1_III = np.sum(III.Ti(e1)*e1.intensity) / e1.intensity.sum()
        if e2.multiplicity == 1:
            T2_I = I.Ti(e2)
            T2_II = II.Ti(e2)
            T2_III = III.Ti(e2)
        else:
            T2_I = np.sum(I.Ti(e2)*e2.intensity) / e2.intensity.sum()
            T2_II = np.sum(II.Ti(e2)*e2.intensity) / e2.intensity.sum()
            T2_III = np.sum(III.Ti(e2)*e2.intensity) / e2.intensity.sum()

        self.T2_T1 = T2_II / T1_I
        self.alpha = (T1_III / T1_I, T2_III / T2_II)
        self.beta = (I.Tm * I.Wj / (III.Tm * III.Wj),
                     II.Tm * II.Wj / (III.Tm * III.Wj))
        self.gamma = (T1_II / T1_I, T2_I / T2_II)
        
    def find_line_ratio(self, rates, colors=(1.0, 1.0), naive=False):
        """Find the line ratio I1/I2 given the count rates in the three filters"""
        R_I, R_II, R_III = rates
        k_I, k_II = colors
        e1, e2 = self.emlines
        if naive:
            ratio = R_I/R_II
        else:
            alpha_1, alpha_2 = self.alpha
            beta_I, beta_II = self.beta
            gamma_1, gamma_2 = self.gamma
            ratio = (1.0 - alpha_2*beta_II*k_II)*R_I \
                    + (alpha_2*beta_I*k_I - gamma_2)*R_II \
                    + (gamma_2*beta_II*k_II - beta_I*k_I)*R_III
            ratio /= (alpha_1*beta_II*k_II - gamma_1)*R_I \
                     + (1.0 - alpha_1*beta_I*k_I)*R_II \
                     + (gamma_1*beta_I*k_I - beta_II*k_II)*R_III 
        ratio *= self.T2_T1 * e2.wave / e1.wave
        return ratio
            

if __name__ == "__main__":
    from matplotlib import pyplot as plt
    
    filterset = Filterset(
        ["wfpc2,f658n", "wfpc2,f656n", "wfpc2,f547m"],
        ["[N II] 6583", "H I 6563"]
    )

    print("alpha = ", filterset.alpha)
    print("beta = ", filterset.beta)
    print("gamma = ", filterset.gamma)

    for bp in filterset.bandpasses:
        plt.plot(bp.wave, bp.T, label=bp.longname)
    for emline in filterset.emlines:
        if emline.multiplicity > 1:
            for wav, strength in zip(emline.wave, emline.intensity):
                plt.axvline(wav, 0.0, 0.3*strength, color='r', lw=2)
        else:
            plt.axvline(emline.wave, 0.0, 0.9, color='b', lw=2)

    plt.xlim(*filterset.wavlimits())
    plt.legend(fontsize='small', loc='upper left')
    plt.xlabel("Vacuum wavelength, Angstrom")
    plt.ylabel("Filter throughput")
    plt.gcf().set_size_inches(8,4)
    plt.gcf().tight_layout()
    plt.savefig('test-nebulium.pdf')




    
