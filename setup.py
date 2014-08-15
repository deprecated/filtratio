from __future__ import print_function
from setuptools import setup, find_packages
from os.path import join, dirname
from setuptools.command.test import test as TestCommand
import sys

import nebulio

class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errcode = pytest.main(self.test_args)
        sys.exit(errcode)

setup(
    name='nebulio',
    version=nebulio.__version__,
    description='Derive emission line ratios from count rates in HST filters ',
    long_description=open(join(dirname(__file__), 'README.md')).read(),
    url='https://github.com/deprecated/nebulio',
    author='William Henney',
    author_email='w.henney@crya.unam.mx',
    license='MIT',
    packages=find_packages(),
    install_requires=[
        'numpy',
        'matplotlib',
        'pysynphot',
    ],
    cmdclass={'test': PyTest},
    zip_safe=False,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: Scientific/Engineering :: Astronomy',
        'Topic :: Scientific/Engineering :: Physics',
    ],
)
