"""These tests compare filter parameters from pysynphot with the ones
I have calculated myself."""

from __future__ import (print_function, absolute_import, division, unicode_literals)

import nebulio

def test_version():
    """Silly test just to test that tests work"""
    assert nebulio.__version__ == "0.1a1", nebulio.__version__


# Not needed now we are using the test runner
# if __name__ == "__main__":
#     test_version()
