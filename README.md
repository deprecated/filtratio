Nebulio
============

A python library to derive emission line ratios from count rates in HST filters

Takes account of overlapping transmission curves and contamination by continuum and non-target lines. 

![Schematic illustration of how the intensity ratio between two target lines is derived using observations in three filters.](images/filter-schematic.jpg)

### About the name

Nebulio is a spanish translation of [Nebulium](http://en.wikipedia.org/wiki/Nebulium), which is a hypothetical chemical element that was once believed to be responsible for strong green and blue emission lines seen in the spectra of astronomical nebulae.  However, it turned out that they were acually due to forbidden lines of singly ionized and doubly ionized oxygen. 

### Installation requirements

Depends on 

1. The [pysynphot](http://stsdas.stsci.edu/pysynphot/) python package.  Install with `pip install pysynphot` or similar.  Tested with version `0.9.5`. 

2. [CDBS database](http://www.stsci.edu/hst/observatory/crds/cdbs_throughput.html). Tested with version `cdbs.20.1rc1`. 
