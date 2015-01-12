"""Copyright 2011 Phidgets Inc.
This work is licensed under the Creative Commons Attribution 2.5 Canada License.
To view a copy of this license, visit http://creativecommons.org/licenses/by/2.5/ca/
"""

__author__ = 'Adam Stelmack'
__version__ = '2.1.8'
__date__ = 'July 19 2011'

import sys

def prepOutput(output):
    if sys.version_info < (3, 2):
        return output.value
    else:
        return output.value.decode('utf-8')