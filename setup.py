from __future__ import print_function
from setuptools import setup

import nebulio

setup(name='nebulio',
      version=nebulio.__version__,
      description='Derive emission line ratios from count rates in HST filters ',
      url='https://github.com/deprecated/nebulio',
      author='William Henney',
      author_email='w.henney@crya.unam.mx',
      license='MIT',
      packages=['nebulio'],
      zip_safe=False)
