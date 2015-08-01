"""Copyright 2010 Phidgets Inc.
This work is licensed under the Creative Commons Attribution 2.5 Canada License. 
To view a copy of this license, visit http://creativecommons.org/licenses/by/2.5/ca/
"""

__author__ = 'Adam Stelmack'
__version__ = '2.1.8'
__date__ = 'May 17 2010'

import threading
from ctypes import *
import sys

class PhidgetLibrary:
    __dll = None
    @staticmethod
    def getDll():
        if PhidgetLibrary.__dll is None:
            if sys.platform == 'win32':
                PhidgetLibrary.__dll = windll.LoadLibrary("phidget21.dll")
            elif sys.platform == 'darwin':
                PhidgetLibrary.__dll = cdll.LoadLibrary("/Library/Frameworks/Phidget21.framework/Versions/Current/Phidget21")
            elif sys.platform == 'linux2':
                PhidgetLibrary.__dll = cdll.LoadLibrary("libphidget21.so.0")
            else:
                raise RuntimeError("Platform not supported")
        
        return PhidgetLibrary.__dll