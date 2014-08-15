"""These tests compare filter parameters from pysynphot with the ones
I have calculated myself."""

from __future__ import (print_function, absolute_import, division, unicode_literals)

import os
import nebulio
from nebulio.tests.utils import this_func_name

def test_version():
    """Silly test just to test that tests work"""
    assert nebulio.__version__ == "0.1a1", nebulio.__version__

from nebulio.legacy import wfc3_utils
from matplotlib import pyplot as plt

def test_wfc3_utils():
    """Compare results from `nebulio.filterset` with results from wfc3_utils"""
    
    fn = "F656N"
    wavs, T = wfc3_utils.get_filter(fn, return_wavelength=True)
    Tm = wfc3_utils.Tm(T)
    assert Tm > 0.1, "Transmission too small: {}".format(Tm)

    bp = nebulio.Bandpass(','.join(['wfc3', 'uvis1', fn]))
    assert abs(Tm - bp.Tm) < 1e-3, "Max transmissions for {}: {}, {}".format(fn, Tm, bp.Tm)

    plt.plot(wavs, T, 'x', label='legacy')
    plt.plot(bp.wave, bp.T, '.', label='synphot')
    plt.xlim(bp.wav0 - bp.Wj, bp.wav0 + bp.Wj)
    plt.legend()
    plotfile = os.path.join("plots", '{}-{}.pdf'.format(this_func_name(), fn))
    plt.savefig(plotfile)

    assert abs(Tm - bp.Tm) < 1e-3, "Disagreement: {} vs {}".format(Tm, bp.Tm)
    
