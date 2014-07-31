filtratio
============

A python library to derive emission line ratios from count rates in HST filters

Takes account of overlapping transmission curves and contamination by continuum and non-target lines. 


## Requirements

Depends on 

1. The [pysynphot](http://stsdas.stsci.edu/pysynphot/) python package.  Install with `pip install pysynphot` or similar.  Tested with version `0.9.5`. 

2. [CDBS database](http://www.stsci.edu/hst/observatory/crds/cdbs_throughput.html). Tested with version `cdbs.20.1rc1`. 
