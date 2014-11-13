"""Tests for composite filter """

from __future__ import (print_function, absolute_import, division, unicode_literals)

import os
import pytest
import numpy as np
import nebulio
import pysynphot
from nebulio.tests.utils import this_func_name
from matplotlib import pyplot as plt

def plot_filterset(fs):
    title = this_func_name(2)
    fig, ax = plt.subplots()
    # Plot each bandpass
    for bp in fs.bandpasses:
        ax.plot(bp.wave, bp.T, '-', label=bp.fname)
    for emline in fs.emlines:
        if emline.fwhm_kms is not None:
            for wav0, strength, fwhm in zip(emline.wave, emline.intensity,
                                            emline.fwhm_angstrom):
                gauss = pysynphot.GaussianSource(1.0, wav0, fwhm)
                ax.plot(gauss.wave,
                        strength*gauss.flux*fs.bandpasses[0].T.max()/(emline.intensity[0]*gauss.flux.max()),
                        label='{:.2f} A'.format(wav0))
    ax.set_title(title)
    ax.set_xlim(min([bp.wav0 - bp.Wj for bp in fs.bandpasses[:2]]),
                max([bp.wav0 + bp.Wj for bp in fs.bandpasses[:2]]))
    ax.legend()
    plotfile = os.path.join("plots", '{}.pdf'.format(this_func_name(2)))
    fig.savefig(plotfile)
    


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


def test_filterset_with_composite_sii():
    fs = nebulio.Filterset(
        bpnames=[['wfc3,uvis1,FQ672N', 'wfc3,uvis1,FQ674N'],
                 "wfc3,uvis1,F673N", "wfc3,uvis1,F547M"],
        lineids=['[S II] 6724', '[S II] 6724'],
        velocity=25.0, fwhm_kms=20.0
    )
    print(fs.__dict__)
    plot_filterset(fs)
    assert True                # what to test?    


def test_filterset_with_nii_ha():
    fs = nebulio.Filterset(
        bpnames=["wfc3,uvis1,F658N", "wfc3,uvis1,F656N", "wfc3,uvis1,F547M"],
        lineids=['[N II] 6583', 'H I 6563'],
        velocity=25.0, fwhm_kms=20.0
    )
    print(fs.__dict__)
    plot_filterset(fs)
    assert True                # what to test?    
