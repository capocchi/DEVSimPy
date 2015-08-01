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
from Phidgets.Events.Events import TemperatureChangeEventArgs
import sys

class ThermocoupleType:
    """This is an enumeration of thermocouple types and their values.
    
    This has been added for a more straightforward way of displaying and checking the thermocouple types.
    """
    PHIDGET_TEMPERATURE_SENSOR_K_TYPE = 1
    PHIDGET_TEMPERATURE_SENSOR_J_TYPE = 2
    PHIDGET_TEMPERATURE_SENSOR_E_TYPE = 3
    PHIDGET_TEMPERATURE_SENSOR_T_TYPE = 4

class TemperatureSensor(Phidget):
    """This class represents a Phidget temperature Sensor.
    
    All methods to read temperaure data from the sensor are implemented in this class.
    The Temperature Phidget consists of a thermocouple interface, and a temperature sensing IC,
    which is used to measure the temperature of the thermocouple cold junction and calibrate the thermocouple sensed temperature.
    
    Both the thermocouple temperature and IC temperature can be read. Value are returned in degrees celcius.
	
	See your device's User Guide for more specific API details, technical information, and revision details. 
	The User Guide, along with other resources, can be found on the product page for your device.
    
    Extends:
        Phidget
    """
    def __init__(self):
        """The Constructor Method for the TemperatureSensor Class
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
        """
        Phidget.__init__(self)
        
        self.__tempChange = None
        
        self.__onTemperatureChange = None
        
        try:
            PhidgetLibrary.getDll().CPhidgetTemperatureSensor_create(byref(self.handle))
        except RuntimeError:
            raise
        
        if sys.platform == 'win32':
            self.__TEMPCHANGEHANDLER = WINFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_double)
        elif sys.platform == 'darwin' or sys.platform == 'linux2':
            self.__TEMPCHANGEHANDLER = CFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_double)

    def __del__(self):
        """The Destructor Method for the TemperatureSensor Class
        """
        Phidget.dispose(self)

    def getTemperatureInputCount(self):
        """Returns the number of thermocouples.
        
        Returns:
            Number of thermocouple temperature inputs <int>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        inputCount = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetTemperatureSensor_getTemperatureInputCount(self.handle, byref(inputCount))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return inputCount.value

    def getTemperature(self, index):
        """Returns the temperature of a thermocouple.
        
        This value is returned in degrees celcius but can easily be converted into other units.
        This value will always be between getTemperatureMin and getTemperatureMax.
        The accuracy depends on the thermocouple used. The board is calibrated during manufacture.
        
        Parameters:
            index<int>: index of the thermocouple input.
        
        Returns:
            Temperature in degrees celcius <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, index is out of range.
        """
        temperature = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetTemperatureSensor_getTemperature(self.handle, c_int(index), byref(temperature))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return temperature.value

    def getTemperatureMax(self, index):
        """Returns the maximum temperature that will be returned by a thermocouple input.
        
        This value depends on the thermocouple type.
        
        Parameters:
            index<int>: index of the thermocouple input.
        
        Returns:
            Maximum temperature in degrees celcius <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, index is out of range.
        """
        temperatureMax = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetTemperatureSensor_getTemperatureMax(self.handle, c_int(index), byref(temperatureMax))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return temperatureMax.value

    def getTemperatureMin(self, index):
        """Returns the minimum temperature that will be returned by a thermocouple input.
        
        This value depends on the thermocouple type.
        
        Parameters:
            index<int>: index of the thermocouple input.
        
        Returns:
            Minimum temperature in degrees celcius <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, index is out of range.
        """
        temperatureMin = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetTemperatureSensor_getTemperatureMin(self.handle, c_int(index), byref(temperatureMin))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return temperatureMin.value

    def __nativeTemperatureChangeEvent(self, handle, usrptr, index, value):
        if self.__tempChange != None:
            potential = 0
            try:
                potential = self.getPotential(index)
            except PhidgetException:
                potential = 0
            self.__tempChange(TemperatureChangeEventArgs(self, index, value, potential))
        return 0

    def setOnTemperatureChangeHandler(self, temperatureChangeHandler):
        """Sets the Temperature Change Event Handler.
        
        The temperature change handler is a method that will be called when the temperature has changed by at least the Trigger that has been set.
        
        Parameters:
            temperatureChangeHandler: hook to the temperatureChangeHandler callback function.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException
        """
        if temperatureChangeHandler == None:
            self.__tempChange = None
            self.__onTemperatureChange = None
        else:
            self.__tempChange = temperatureChangeHandler
            self.__onTemperatureChange = self.__TEMPCHANGEHANDLER(self.__nativeTemperatureChangeEvent)
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetTemperatureSensor_set_OnTemperatureChange_Handler(self.handle, self.__onTemperatureChange, None)
        except RuntimeError:
            self.__tempChange = None
            self.__onTemperatureChange = None
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def getTemperatureChangeTrigger(self, index):
        """Returns the change trigger for an input.
        
        This is the amount by which the sensed temperature must change between TemperatureChangeEvents.
        By default this is set to 0.5.
        
        Parameters:
            index<int>: index of the thermocouple input.
        
        Returns:
            The temperature change trigger value <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, index is out of range.
        """
        sensitivity = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetTemperatureSensor_getTemperatureChangeTrigger(self.handle, c_int(index), byref(sensitivity))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return sensitivity.value

    def setTemperatureChangeTrigger(self, index, value):
        """Sets the change trigger for an input.
        
        This is the amount by which the sensed temperature must change between TemperatureChangeEvents.
        By default this is set to 0.5.
        
        Parameters:
            index<int>: index of the thermocouple input.
            value<double>: temperature change trigger value.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or index or value are out of range.
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetTemperatureSensor_setTemperatureChangeTrigger(self.handle, c_int(index), c_double(value))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def getPotential(self, index):
        """Returns the potential of a thermocouple input.
        
        This value is returned in millivolts. This value will always be between getPotentialMin and getPotentialMax.
        This is very accurate, as it is a raw value from the A/D.
        This is the value that is internally used to calculate temperature in the library.
        
        Parameters:
            index<int>: index of the thermocouple input.
        
        Returns:
            Potential in millivolts <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, index is out of range.
        """
        potential = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetTemperatureSensor_getPotential(self.handle, c_int(index), byref(potential))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return potential.value

    def getPotentialMax(self, index):
        """Returns the maximum potential that will be returned by a thermocouple input.
        
        Parameters:
            index<int>: index of the thermocouple input.
        
        Returns:
            Maximum Potential in millivolts <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, index is out of range.
        """
        potentialMax = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetTemperatureSensor_getPotentialMax(self.handle, c_int(index), byref(potentialMax))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return potentialMax.value

    def getPotentialMin(self, index):
        """Returns the minimum potential that will be returned by a thermocouple input.
        
        Parameters:
            index<int>: index of the thermocouple input.
        
        Returns:
            Minimum Potential in millivolts <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, index is out of range.
        """
        potentialMin = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetTemperatureSensor_getPotentialMin(self.handle, c_int(index), byref(potentialMin))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return potentialMin.value

    def getAmbientTemperature(self):
        """Returns the temperature of the ambient sensor.
        
        This value is returned in degrees celcius but can easily be converted into other units.
        This value will always be between getAmbientTemperatureMin and getAmbientTemperatureMax.
        This is the temperature of the board at the thermocouple cold junction.
        
        Returns:
            Ambient Temperature in derees celcius <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        ambient = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetTemperatureSensor_getAmbientTemperature(self.handle, byref(ambient))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return ambient.value

    def getAmbientTemperatureMax(self):
        """Returns the maximum temperature that will be returned by the ambient sensor.
        
        Returns:
            Maximum Ambient Temperature in derees celcius <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        ambientMax = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetTemperatureSensor_getAmbientTemperatureMax(self.handle, byref(ambientMax))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return ambientMax.value

    def getAmbientTemperatureMin(self):
        """Returns the minimum temperature that will be returned by the ambient sensor.
        
        Returns:
            Minimum Ambient Temperature in derees celcius <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        ambientMin = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetTemperatureSensor_getAmbientTemperatureMin(self.handle, byref(ambientMin))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return ambientMin.value

    def getThermocoupleType(self, index):
        """Returns the thermocouple type for an input.
        
        The possible values for type are PHIDGET_TEMPERATURE_SENSOR_K_TYPE,
        PHIDGET_TEMPERATURE_SENSOR_J_TYPE, PHIDGET_TEMPERATURE_SENSOR_E_TYPE and
        PHIDGET_TEMPERATURE_SENSOR_T_TYPE.
        
        (See ThermocoupleType class for values associated with these names)
        
        Parameters:
            index<int>: index of the thermocouple input.
        
        Returns:
            The Thermocouple Type <int>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, index is out of range.
        """
        thermocoupleType = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetTemperatureSensor_getThermocoupleType(self.handle, c_int(index), byref(thermocoupleType))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return thermocoupleType.value

    def setThermocoupleType(self, index, value):
        """Sets the thermocouple type for an input.
        
        The Phidget Temperature Sensor board can be used with K, E, J and T-Type Thermocouples.
        Support for other thermocouple types, and voltage sources other then thermocouples in the valid range
        (between getPotentialMin and getPotentialMax) can be achieved using getPotential.
        
        The possible values for type are PHIDGET_TEMPERATURE_SENSOR_K_TYPE, PHIDGET_TEMPERATURE_SENSOR_J_TYPE,
        PHIDGET_TEMPERATURE_SENSOR_E_TYPE and PHIDGET_TEMPERATURE_SENSOR_T_TYPE.
        
        By default, type is set to PHIDGET_TEMPERATURE_SENSOR_K_TYPE.
        
        (See ThermocoupleType class for values associated with these names)
        
        Parameters:
            index<int>: index of the thermocouple input.
            value<int>: The Thermocouple Type.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, index or value are out of range.
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetTemperatureSensor_setThermocoupleType(self.handle, c_int(index), c_int(value))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
