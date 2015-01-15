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
import sys

class LEDVoltage:
    """This is an enumeration of available voltage output level values.
    
    This has been added to allow the user to select the preset voltage output level values available in the hardware.
    """
    VOLTAGE_1_7V=1
    VOLTAGE_2_75V=2
    VOLTAGE_3_9V=3
    VOLTAGE_5_0V=4
    INVALID=0

class LEDCurrentLimit:
    """This is an enumeration of available current limit values.
    
    This has been added to allow the user to select the preset current limit values available in the hardware.
    """
    CURRENT_LIMIT_20mA=1
    CURRENT_LIMIT_40mA=2
    CURRENT_LIMIT_60mA=3
    CURRENT_LIMIT_80mA=4
    INVALID=0

class LED(Phidget):
    """This class represents a Phidget LED. All methods to control a Phidget LED are implemented in this class.
    
    The Phidget LED is a board that is meant for driving LEDs. Currently, the only available version drives 64 LEDs, but other versions may become available so this number is not absolute.
    
    LEDs can be controlled individually, at brightness levels from 0-100.
	
	See your device's User Guide for more specific API details, technical information, and revision details. 
	The User Guide, along with other resources, can be found on the product page for your device.
    
    Extends:
        Phidget
    """
    def __init__(self):
        """The Constructor Method for the LED Class
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
        """
        Phidget.__init__(self)
        
        try:
            PhidgetLibrary.getDll().CPhidgetLED_create(byref(self.handle))
        except RuntimeError:
            raise

    def __del__(self):
        """The Destructor Method for the LED Class
        """
        Phidget.dispose(self)

    def getDiscreteLED(self, index):
        """Deprecated: use getBrightness
        """
        ledVal = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetLED_getDiscreteLED(self.handle, c_int(index), byref(ledVal))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return ledVal.value

    def setDiscreteLED(self, index, value):
        """Deprecated: use setBrightness
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetLED_setDiscreteLED(self.handle,  c_int(index), c_int(value))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def getBrightness(self, index):
        """Returns the brightness value of an LED.
        
        This value ranges from 0-100.
        
        Parameters:
            index<int>: index of the Discrete LED.
        
        Returns:
            Brightness of the LED <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        ledVal = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetLED_getBrightness(self.handle, c_int(index), byref(ledVal))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return ledVal.value

    def setBrightness(self, index, value):
        """Sets the brightness of an LED.
        
        Valid values are 0-100, with 0 being off and 100 being the brightest.
        
        Parameters:
            index<int>: index of the Discrete LED.
            value<double>: brightness value of the Discrete LED.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index or brightness value are out of range.
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetLED_setBrightness(self.handle,  c_int(index), c_double(value))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def getCurrentLimitIndexed(self, index):
        """Returns the current limit value of an LED.
        
        This value ranges from 0-80 mA.
        
        Parameters:
            index<int>: index of the LED.
        
        Returns:
            Current limit of the LED <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        ledVal = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetLED_getCurrentLimitIndexed(self.handle, c_int(index), byref(ledVal))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return ledVal.value

    def setCurrentLimitIndexed(self, index, value):
        """Sets the current limit of an LED.
        
        Valid values are 0-80 mA.
        
        Parameters:
            index<int>: index of the Discrete LED.
            value<double>: current limit of the Discrete LED.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index or brightness value are out of range.
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetLED_setCurrentLimitIndexed(self.handle,  c_int(index), c_double(value))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def getLEDCount(self):
        """Returns the number of LEDs that this board can drive.
        
        This may not correspond to the actual number of LEDs attached.
        
        Returns:
            The number of available LEDs <int>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        LEDCount = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetLED_getLEDCount(self.handle, byref(LEDCount))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return LEDCount.value

    def getCurrentLimit(self):
        """Returns the current limit for the all outputs.
        
        This is only supported by some PhidgetLEDs - see the product manual.
        
        The possible values for type are LEDCurrentLimit.CURRENT_LIMIT_20mA, LEDCurrentLimit.CURRENT_LIMIT_40mA,
        LEDCurrentLimit.CURRENT_LIMIT_60mA and LEDCurrentLimit.CURRENT_LIMIT_80mA.
        
        Returns:
            The current limit for all the outputs <int>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if unsupported by this board.
        """
        currentLimit = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetLED_getCurrentLimit(self.handle, byref(currentLimit))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return currentLimit.value
    
    def setCurrentLimit(self, currentLimit):
        """Sets the current limit for all outputs.
        
        This is only supported by some PhidgetLEDs - see the product manual.
        
        The possible values for type are LEDCurrentLimit.CURRENT_LIMIT_20mA, LEDCurrentLimit.CURRENT_LIMIT_40mA,
        LEDCurrentLimit.CURRENT_LIMIT_60mA and LEDCurrentLimit.CURRENT_LIMIT_80mA.
        
        By default, currentLimit is set to LEDCurrentLimit.CURRENT_LIMIT_20mA.
        
        Parameters:
            currentLimit<int>: desired current limit to set for all the outputs.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if unsupported by this board.
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetLED_setCurrentLimit(self.handle,  c_int(currentLimit))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
    
    def getVoltage(self):
        """Returns the voltage output for the all outputs.
        
        This is only supported by some PhidgetLEDs - see the product manual.
        
        The possible values for type are LEDVoltage.VOLTAGE_1_7V, LEDVoltage.VOLTAGE_2_75V, LEDVoltage.VOLTAGE_3_9V and LEDVoltage.VOLTAGE_5_0V.
        
        Returns:
            The voltage level set for all the outputs <int>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if unsupported by this board.
        """
        voltage = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetLED_getVoltage(self.handle, byref(voltage))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return voltage.value
    
    def setVoltage(self, voltage):
        """Sets the voltage output for all outputs.
        
        This is only supported by some PhidgetLEDs - see the product manual.
        
        The possible values for type are LEDVoltage.VOLTAGE_1_7V, LEDVoltage.VOLTAGE_2_75V, LEDVoltage.VOLTAGE_3_9V and LEDVoltage.VOLTAGE_5_0V.
        By default, voltage is set to LEDVoltage.VOLTAGE_2_75V.
        
        Parameters:
            voltage<int>: desired voltage level to set for all the outputs.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if unsupported by this board.
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetLED_setVoltage(self.handle,  c_int(voltage))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
