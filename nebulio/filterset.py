from __future__ import print_function

"""A set of filters that is used to determine an emission line ratio
"""

import numpy as np
import pysynphot

AIR_REFRACTIVE_INDEX = 1.000277  # @STP according to Wikipedia
LIGHTSPEED = 2.99792458e5        # c in km/s


class Bandpass(object):
    """A combination of telescope, instrument, camera/channel/ccd, filter

    The Bandpass class is a wrapper around :class:`pysynphot.ObsBandpass` and
    encapsulates the total throughput of an instrument.

    Parameters
    ----------
    obsmode : str
              A string giving a comma-separated list of instrument,
              [channel,] and filter, which is passed directly to
              :class:`pysynphot.ObsBandpass`

    Notes
    -----
    The `obsmode` parameter does not support all possible synphot [1]
    observation modes yet.   Only INSTRUMENT,CHANNEL,FILTER  (e.g.,
    'wfc3,uvis1,f547m') or INSTRUMENT,FILTER (e.g., 'wfpc2,f658n') are
    supported.

    """

    # Line transmission adjustments (determined by in-flight calibration)
    T_adjustments = {}

    def __init__(self, obsmode='wfc3,uvis1,f547m'):
        self.obsmode = obsmode
        try:
            # Cases such as acs,wfc1,f658n
            self.instrument, self.channel, self.fname = obsmode.split(',')
        except ValueError:
            # Cases such as wfpc2,f502n
            self.instrument, self.fname = obsmode.split(',')
            self.channel = None
        # Delegate all the hard work to pysynphot
        self._synphot_bp = pysynphot.ObsBandpass(obsmode)
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
        """Filter transmission at the wavelength of an emission line

        If the `emline` has a finite width, then this will be the average
        transmission over a Gaussian line profile

        Parameters
        ----------
        emline : :class:`EmissionLine`

        Note
        ----
        Will return an array of values in the case where `emline` is a multiplet. 

        """
        correction = self.T_adjustments.get((emline.wavid, self.obsmode), 1.0)
        if emline.fwhm_angstrom is None:
            # Original delta function method
            return correction*np.interp(emline.wave, self.wave, self.T)
        else:
            result = []
            clear_filter = pysynphot.UniformTransmission(1.0)
            for wav, strength, fwhm in zip(emline.wave, emline.intensity,
                                           emline.fwhm_angstrom):
                gauss = pysynphot.GaussianSource(1e-15*strength, wav, fwhm)
                counts = pysynphot.Observation(gauss,
                                               self._synphot_bp).countrate()
                # Explicitly pass binset for uniform transmission to prevent warning
                clearcounts = pysynphot.Observation(gauss,
                                                    clear_filter,
                                                    binset=gauss.wave).countrate()
                result.append(counts/clearcounts)
            return correction*np.array(result)

    def Wtwid(self, emline, kji=1.0):
        """Find W-twiddle for a given line of wavelength wav0
        with respect to a filter transmission curve T(wavs).
        And with color correction kji
        """
        return kji*self.Tm*self.Wj/self.Ti(emline)



class CompositeBandpass(Bandpass):
    """A composite bandpass that is the sum of two or more filters"""

    def __init__(self, obsmodes):
        self.bandpasses = [Bandpass(obsmode) for obsmode in obsmodes]
        self.fname = "+".join([bp.fname for bp in self.bandpasses])
        # Create a wavelength array that is a superset of all the
        # wavelengths used in the individual bandpasses
        self.wave = np.sort(list(set(
            np.concatenate([bp.wave for bp in self.bandpasses]))))
        # And sum all the bandpass transmissions interpolated onto this array
        self.T = np.sum([np.interp(self.wave, bp.wave, bp.T, left=0.0, right=0.0)
                         for bp in self.bandpasses], axis=0)
        # Maximum and rectangular width are calculated using the
        # interpolated transmission
        self.Tm = self.T.max()
        self.Wj = np.trapz(self.T, self.wave)/self.Tm
        # Central wavelength is simply the average of the individual filters
        self.wav0 = np.mean([bp.wav0 for bp in self.bandpasses])
    
    def Ti(self, emline):
        # Line transmission is calulated by summing transmission
        # through individual filters.  This means that the corrections
        # through T_adjustments are automatically picked up
        return np.sum([bp.Ti(emline) for bp in self.bandpasses])

# Accurate rest wavelengths (Source: NIST)
air_rest_wavelengths = {
    "H I 4340": [4340.47],
    "[O III] 4363": [4363.21],
    "H I 4861": [4861.63],
    "[O III] 5007": [5006.843, 4958.911, 4931.227],
    "[N II] 5755": [5755.08],
    "H I 6563": [6562.79],
    "[N II] 6583": [6583.45, 6548.05, 6527.23],
    "[S II] 6716": [6716.44],
    "[S II] 6731": [6730.816],
    "[S II] 6724": [6716.44, 6730.816],
}

# Source: NIST
multiplet_strengths = {
    #
    # These share an upper level, so should be fixed
    # 
    "[O III] 5007": [2.918, 1.0, 3.88e-4],
    "[N II] 6583": [2.963, 1.0, 5.33e-4],
    #
    # These vary with physical conditions
    #
    # [S II] ratio varies with density between ~1.1 -> ~0.4
    "[S II] 6724": [1.0, 1.0],
}


def _split_ids(lineid):
    pieces = lineid.split()
    return ' '.join(pieces[:-1]), pieces[-1]


class EmissionLine(object):
    """A single line, or a multiplet with known intensity ratio"""
    velocity = 0.0

    def __init__(self, lineid, velocity=None, fwhm_kms=None):
        self.lineid = lineid
        self.species, self.wavid = _split_ids(lineid)
        # Rest wavelength(s) in air
        self.wav0_air = np.array(
            air_rest_wavelengths.get(lineid, [float(self.wavid)]))
        self.multiplicity = len(self.wav0_air)
        self.intensity = np.array(
            multiplet_strengths.get(lineid, np.ones_like(self.wav0_air)))
        # Rest wavelength in vacuum
        self.wav0 = self.wav0_air * AIR_REFRACTIVE_INDEX
        # Topocentric velocity
        if velocity is None:
            # Allow velocity to be set at the class level for all lines
            self.velocity = self.__class__.velocity
        else:
            self.velocity = velocity
        # Observed wavelength in vacuum
        self.wave = self.wav0 * (1.0 + self.velocity/LIGHTSPEED)
        # Line width
        self.fwhm_kms = fwhm_kms
        if fwhm_kms is not None:
            # This will give an array for multiplets
            self.fwhm_angstrom = self.wave * fwhm_kms / LIGHTSPEED
        else:
            self.fwhm_angstrom = None

def _bandpass(arg):
    """This is a bit of a hack to give either a CompositeBandpass or a
    normal Bandpass depending on if the argument is a list or not"""
    if isinstance(arg, list):
        return CompositeBandpass(arg)
    else:
        return Bandpass(arg)

class Filterset(object):
    """A set of three emission line filters for measuring a line ratio"""

    def __init__(self, bpnames, lineids, velocity=0.0, fwhm_kms=None):
        assert len(bpnames) == 3, 'Need to specify exactly 3 filters'
        assert len(lineids) == 2, 'Need to specify exactly 2 emission lines'
        self.bpnames = bpnames
        self.lineids = lineids
        self.emlines = [EmissionLine(lineid, velocity, fwhm_kms)
                        for lineid in lineids]
        self.bandpasses = [_bandpass(longname) for longname in bpnames]
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
        T1_I = np.sum(I.Ti(e1)*e1.intensity) / e1.intensity[0]
        T1_II = np.sum(II.Ti(e1)*e1.intensity) / e1.intensity[0]
        T1_III = np.sum(III.Ti(e1)*e1.intensity) / e1.intensity[0]
        T2_I = np.sum(I.Ti(e2)*e2.intensity) / e2.intensity[0]
        T2_II = np.sum(II.Ti(e2)*e2.intensity) / e2.intensity[0]
        T2_III = np.sum(III.Ti(e2)*e2.intensity) / e2.intensity[0]

        self.T2_T1 = T2_II / T1_I
        self.alpha = (T1_III / T1_I, T2_III / T2_II)
        self.beta = (I.Tm * I.Wj / (III.Tm * III.Wj),
                     II.Tm * II.Wj / (III.Tm * III.Wj))
        self.gamma = (T1_II / T1_I, T2_I / T2_II)

    def find_line_ratio(self, rates, colors=(1.0, 1.0), naive=False):
        """Find the line ratio I1/I2 given the count *rates* in the three filters

        :param list rates: Count rates in each of the three filters
        :param tuple colors: 2-tuple of k-twiddle for filters I and II
        :para bool naive: if ``True`` then ignore all contamination
        terms: alpha, beta, gamma = 0
        :rtype: float

        """
        R_I, R_II, R_III = rates
        k_I, k_II = colors
        e1, e2 = self.emlines
        if naive:
            ratio = R_I/R_II
        else:
            alpha_1, alpha_2 = self.alpha
            beta_I, beta_II = self.beta
            gamma_1, gamma_2 = self.gamma
            ratio = ((1.0 - alpha_2*beta_II*k_II)*R_I
                     + (alpha_2*beta_I*k_I - gamma_2)*R_II
                     + (gamma_2*beta_II*k_II - beta_I*k_I)*R_III)
            ratio /= ((alpha_1*beta_II*k_II - gamma_1)*R_I
                      + (1.0 - alpha_1*beta_I*k_I)*R_II
                      + (gamma_1*beta_I*k_I - beta_II*k_II)*R_III)
        ratio *= self.T2_T1 * e2.wave[0] / e1.wave[0]
        return ratio


if __name__ == "__main__":
    from matplotlib import pyplot as plt

    filterset = Filterset(
        ["wfpc2,f658n", "wfpc2,f656n", "wfpc2,f547m"],
        ["[N II] 6583", "H I 6563"]
    )

    print("T2/T1 =", filterset.T2_T1)
    print("alpha =", filterset.alpha)
    print("beta =", filterset.beta)
    print("gamma =", filterset.gamma)

    rates = [280.1/500, 610.6/200, 32.6/50]

    print("I_1 / I_2 =", filterset.find_line_ratio(rates))
    print("Naive I_1 / I_2 =", filterset.find_line_ratio(rates, naive=True))

    for bp in filterset.bandpasses:
        plt.plot(bp.wave, bp.T, label=bp.obsmode)
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
    plt.gcf().set_size_inches(8, 4)
    plt.gcf().tight_layout()
    plt.savefig('test-nebulio.pdf')
