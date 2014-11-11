"""Tests for composite filter """

from __future__ import (print_function, absolute_import, division, unicode_literals)

import os
import pytest
import numpy as np
import nebulio
import pysynphot
from nebulio.tests.utils import this_func_name
from matplotlib import pyplot as plt

def plot_composite_bandpass(cbp, emline=None):
    title = this_func_name(2)
    fig, ax = plt.subplots()
    # Plot the composite bandpass
    ax.plot(cbp.wave, cbp.T, '-', label='composite')
    # Plot the individual constituent bandpasses
    for bp in cbp.bandpasses:
        ax.plot(bp.wave, bp.T, '-', label=bp.fname)
    # Plot Gaussian profiles of all components of emission line multiplet
    if emline is not None:
        if emline.fwhm_kms is not None:
            title += ' {}, V = {:.1f} km/s, W = {:.1f} km/s'.format(
                emline.lineid, emline.velocity, emline.fwhm_kms)
            for wav0, strength, fwhm in zip(emline.wave, emline.intensity,
                                            emline.fwhm_angstrom):
                gauss = pysynphot.GaussianSource(1.0, wav0, fwhm)
                ax.plot(gauss.wave, gauss.flux*cbp.T.max()/gauss.flux.max(),
                        label='{:.2f} A'.format(wav0))
    ax.set_xlim(cbp.wav0 - cbp.Wj, cbp.wav0 + cbp.Wj)
    ax.set_title(title)
    ax.legend()
    plotfile = os.path.join("plots", '{}.pdf'.format(this_func_name(2)))
    fig.savefig(plotfile)


def test_twin_sii_filter():
    fnames = ['wfc3,uvis1,FQ672N', 'wfc3,uvis1,FQ674N']
    cbp = nebulio.CompositeBandpass(fnames)
    sii_doublet = nebulio.EmissionLine("[S II] 6724", velocity=25.0, fwhm_kms=40.0)
    plot_composite_bandpass(cbp, sii_doublet)
    assert cbp.Wj*cbp.Tm == np.sum([bp.Wj*bp.Tm for bp in cbp.bandpasses])
