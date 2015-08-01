"""Copyright 2012 Phidgets Inc.
This work is licensed under the Creative Commons Attribution 2.5 Canada License.
To view a copy of this license, visit http://creativecommons.org/licenses/by/2.5/ca/
"""

__author__="Adam Stelmack"
__version__="2.1.8"
__date__ ="12-Jan-2011 11:14:36 AM"

from ctypes import byref, c_double, c_int
import threading
import sys
from Phidgets.PhidgetLibrary import PhidgetLibrary
from Phidgets.Phidget import Phidget
from Phidgets.PhidgetException import PhidgetErrorCodes, PhidgetException

class Analog(Phidget):
    """This class represents a Phidget Analog Controller.

    All methods to control an Analog Controller are implemented in this class.

    See your device's User Guide for more specific API details, technical information, and revision details. 
	The User Guide, along with other resources, can be found on the product page for your device.

    Extends:
        Phidget
    """
    def __init__(self):
        """The Constructor Method for the Analog Class

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
        """
        Phidget.__init__(self)

        try:
            PhidgetLibrary.getDll().CPhidgetAnalog_create(byref(self.handle))
        except RuntimeError:
            raise

    def __del__(self):
        """The Destructor Method for the Analog Class
        """
        Phidget.dispose(self)

    def getOutputCount(self):
        """Returns the number of analog outputs.

        Currently all Phidget Analogs provide two analog outputs.

        Returns:
            The number of Available analog outputs <int>.

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this phidget is not opened or attached.
        """
        outputCount = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetAnalog_getOutputCount(self.handle, byref(outputCount))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)
        else:
            return outputCount.value

    def getVoltageMax(self, index):
        """Gets the maximum voltage level that can be set for a specified analog output index.

        Parameters:
            index<int>: index of the analog output

        Returns:
            The maximum voltage level that can be set for that output <double>.

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        voltageMax = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetAnalog_getVoltageMax(self.handle, c_int(index), byref(voltageMax))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)
        else:
            return voltageMax.value

    def getVoltageMin(self, index):
        """Gets the minimum voltage level that can be set for a specified analog output index.

        Parameters:
            index<int>: index of the analog output

        Returns:
            The minimum voltage level that can be set for that output <double>.

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        voltageMin = c_double()

        try:
            result = PhidgetLibrary.getDll().CPhidgetAnalog_getVoltageMin(self.handle, c_int(index), byref(voltageMin))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)
        else:
            return voltageMin.value

    def getVoltage(self, index):
        """Gets the currently set voltage level for a specified analog output index.

        Parameters:
            index<int>: index of the analog output

        Returns:
            The currently set voltage level for that output <double>.

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        voltage = c_double()

        try:
            result = PhidgetLibrary.getDll().CPhidgetAnalog_getVoltage(self.handle, c_int(index), byref(voltage))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)
        else:
            return voltage.value

    def setVoltage(self, index, voltage):
        """Sets the desired voltage for the specified analog output.

        Parameters:
            index<int>: index of the analog output
            voltage<double>: desired voltage level to set the output to

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, if the index is out of range, or if the voltage level specified is out of range.
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetAnalog_setVoltage(self.handle, c_int(index), c_double(voltage))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)

    def getEnabled(self, index):
        """Gets the enabled state for the specified analog output index.

        This is whether or not this particular output is currently enabled or not.

        Parameters:
            index<int>: index of the analog output.

        Returns:
            The current enabled state of the specified analog output index <boolean>.

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is invalid.
        """
        enabledState = c_int()

        try:
            result = PhidgetLibrary.getDll().CPhidgetAnalog_getEnabled(self.handle, c_int(index), byref(enabledState))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)
        else:
            if enabledState.value == 1:
                return True
            else:
                return False

    def setEnabled(self, index, enabledState):
        """Sets the enabled state for an analog output.

        This will enable or disbale the specified analog output index.

        Parameters:
            index<int>: Index of the analog output.
            enabledState<boolean>: State to set the enabled state of this analog output to.

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        if enabledState == True:
            value = 1
        else:
            value = 0
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetAnalog_setEnabled(self.handle, c_int(index), c_int(value))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)