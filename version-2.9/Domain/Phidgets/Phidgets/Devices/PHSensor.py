"""Copyright 2012 Phidgets Inc.
This work is licensed under the Creative Commons Attribution 2.5 Canada License. 
To view a copy of this license, visit http://creativecommons.org/licenses/by/2.5/ca/
"""

__author__ = 'Adam Stelmack'
__version__ = '2.1.8'
__date__ = 'May 17 2010'

import threading
from ctypes import *
from Phidgets.PhidgetLibrary import PhidgetLibrary
from Phidgets.Phidget import Phidget
from Phidgets.PhidgetException import PhidgetErrorCodes, PhidgetException
from Phidgets.Events.Events import PHChangeEventArgs
import sys

class PHSensor(Phidget):
    """This class represents a Phidget PH Sensor.
    
    All methods to read PH data from the PH Sensor are implemented in this class.
    The Phidget PH Sensor provides one standard PH sensor input.
	
	See your device's User Guide for more specific API details, technical information, and revision details. 
	The User Guide, along with other resources, can be found on the product page for your device.
    
    Extends:
        Phidget
    """
    def __init__(self):
        """The Constructor Method for the PHSensor Class
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
        """
        Phidget.__init__(self)
        
        self.__phChange = None
        
        self.__onPhChange = None
        
        try:
            PhidgetLibrary.getDll().CPhidgetPHSensor_create(byref(self.handle))
        except RuntimeError:
            raise
        
        if sys.platform == 'win32':
            self.__PHCHANGEHANDLER = WINFUNCTYPE(c_int, c_void_p, c_void_p, c_double)
        elif sys.platform == 'darwin' or sys.platform == 'linux2':
            self.__PHCHANGEHANDLER = CFUNCTYPE(c_int, c_void_p, c_void_p, c_double)

    def __del__(self):
        """The Destructor Method for the PHSensor Class
        """
        Phidget.dispose(self)

    def getPH(self):
        """Returns the measured pH.
        
        This value can range from between getPHMin and getPHMax, but some of this range is likely outside of the valid range of most ph sensors.
        For example, when there is no ph sensor attached, the board will often report an (invalid) ph of 15, which while technically within a valid
        ph range, is unlikely to be seen.
        
        Returns:
            The current pH reading <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        phVal = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetPHSensor_getPH(self.handle, byref(phVal))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return phVal.value

    def getPHMax(self):
        """Returns the maximum ph that will be returned by the ph sensor input.
        
        Returns:
            The Maximum pH readable <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        phMax = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetPHSensor_getPHMax(self.handle, byref(phMax))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return phMax.value

    def getPHMin(self):
        """Returns the minimum ph that will be returned by the ph sensor input.
        
        Returns:
            The Minimum pH readable <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        phMin = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetPHSensor_getPHMin(self.handle, byref(phMin))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return phMin.value

    def __nativePHChangeEvent(self, handle, usrptr, value):
        if self.__phChange != None:
            self.__phChange(PHChangeEventArgs(self, value))
        return 0

    def setOnPHChangeHandler(self, phChangeHandler):
        """Sets the PHChange Event Handler.
        
        The ph change handler is a method that will be called when the pH has changed by at least the Trigger that has been set.
        
        Parameters:
            phChangeHandler: hook to the phChangeHandler callback function.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException
        """
        if phChangeHandler == None:
            self.__phChange = None
            self.__onPhChange = None
        else:
            self.__phChange = phChangeHandler
            self.__onPhChange = self.__PHCHANGEHANDLER(self.__nativePHChangeEvent)
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetPHSensor_set_OnPHChange_Handler(self.handle, self.__onPhChange, None)
        except RuntimeError:
            self.__phChange = None
            self.__onPhChange = None
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def getPHChangeTrigger(self):
        """Returns the pH change trigger.
        
        This is how much the pH much change between successive PHChangeEvents. By default this value is set to 0.05
        
        Returns:
            The current pH change Trigger <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        sensitivity = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetPHSensor_getPHChangeTrigger(self.handle, byref(sensitivity))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return sensitivity.value

    def setPHChangeTrigger(self, value):
        """Sets the pH change trigger.
        
        This is how much the pH much change between successive PHChangeEvents. By default this value is set to 0.05.
        
        Parameters:
            value<double>: The requested pH change trigger value.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or the trigger value is out of range.
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetPHSensor_setPHChangeTrigger(self.handle, c_double(value))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def getPotential(self):
        """Returns the Potential, in millivolts.
        
        This returns the actual voltage potential measured by the A/D.
        This value will always be between getPotentialMin and getPotentialMax.
        This is the value that is internally used to calculate pH in the library.
        
        Returns:
            The current potential <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        potential = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetPHSensor_getPotential(self.handle, byref(potential))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return potential.value

    def getPotentialMax(self):
        """Returns the maximum potential that will be returned by the ph sensor input.
        
        Returns:
            The Maximum potential in millivolts <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        potentialMax = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetPHSensor_getPotentialMax(self.handle, byref(potentialMax))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return potentialMax.value

    def getPotentialMin(self):
        """Returns the minimum potential that will be returned by the ph sensor input.
        
        Returns:
            The Minimum potential in millivolts <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        potentialMin = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetPHSensor_getPotentialMin(self.handle, byref(potentialMin))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return potentialMin.value

    def setTemperature(self, value):
        """Sets the probe temperature in degrees celcius.
        
        This value is used while calculating the PH. The default value in the libary is 20 degrees celcius.
        If the temperature of the liquid being measured is not 20 degrees, then it should be measued and set for maximum accuracy.
        
        Note: All that this does is set a value in the library that is used for calculating ph. This does not set anything in the hardware itself.
        
        Parameters:
            value<double>: the requested temperature.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetPHSensor_setTemperature (self.handle, c_double(value))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
