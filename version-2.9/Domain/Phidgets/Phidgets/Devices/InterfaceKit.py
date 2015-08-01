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
from Phidgets.Events.Events import InputChangeEventArgs, OutputChangeEventArgs, SensorChangeEventArgs
import sys

class InterfaceKit(Phidget):
    """This class represents a Phidget Interface Kit. All methods to read and write data to and from an Interface Kit are implemented in this class.
    
    There are many types of Interface Kits, but each is simply a collection of 0 or more digital inputs, digital outpus and analog sensors.
    Inputs can be read and outputs can be set, and event handlers can be set for each of these.
    
    See your device's User Guide for more specific API details, technical information, and revision details. 
	The User Guide, along with other resources, can be found on the product page for your device.
    
    Extends:
        Phidget
    """
    def __init__(self):
        """The Constructor Method for the InterfaceKit Class
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened.
        """
        Phidget.__init__(self)
        
        self.__inputChange = None
        self.__outputChange = None
        self.__sensorChange = None
        
        self.__onInputChange = None
        self.__onSensorChange = None
        self.__onOutputChange = None
        
        try:
            PhidgetLibrary.getDll().CPhidgetInterfaceKit_create(byref(self.handle))
        except RuntimeError:
            raise
        
        if sys.platform == 'win32':
            self.__INPUTCHANGEHANDLER = WINFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_int)
            self.__OUTPUTCHANGEHANDLER = WINFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_int)
            self.__SENSORCHANGEHANDLER = WINFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_int)
        elif sys.platform == 'darwin' or sys.platform == 'linux2':
            self.__INPUTCHANGEHANDLER = CFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_int)
            self.__OUTPUTCHANGEHANDLER = CFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_int)
            self.__SENSORCHANGEHANDLER = CFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_int)

    def __del__(self):
        """The Destructor Method for the InterfaceKit Class
        """
        Phidget.dispose(self)

    def getInputCount(self):
        """Returns the number of ditigal inputs on this Interface Kit.
        
        Not all interface kits have the same number of digital inputs, and some don't have any digital inputs at all.
        
        Returns:
            The Number of analog inputs <int>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        inputCount = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetInterfaceKit_getInputCount(self.handle, byref(inputCount))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return inputCount.value

    def getInputState(self, index):
        """Returns the state of a digital input.
        
        Digital inputs read True where they are activated and False when they are in their default state.
        Be sure to check getInputCount first if you are unsure as to the number of inputs, so as not to set an Index that is out of range.
        
        Parameters:
            index<int>: Index of the input.
        
        Returns:
            State of the input <boolean>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        inputState = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetInterfaceKit_getInputState(self.handle, c_int(index), byref(inputState))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            if inputState.value == 1:
                return True
            else:
                return False

    def __nativeInputChangeEvent(self, handle, usrptr, index, value):
        if self.__inputChange != None:
            if value == 1:
                state = True
            else:
                state = False
            self.__inputChange(InputChangeEventArgs(self, index, state))
        return 0

    def setOnInputChangeHandler(self, inputChangeHandler):
        """Set the InputChange Event Handler.
        
        The input change handler is a method that will be called when an input on this Interface Kit has changed.
        
        Parameters:
            inputChangeHandler: hook to the inputChangeHandler callback function.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException
        """
        if inputChangeHandler == None:
            self.__inputChange = None
            self.__onInputChange = None
        else:
            self.__inputChange = inputChangeHandler
            self.__onInputChange = self.__INPUTCHANGEHANDLER(self.__nativeInputChangeEvent)
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetInterfaceKit_set_OnInputChange_Handler(self.handle, self.__onInputChange, None)
        except RuntimeError:
            self.__inputChange = None
            self.__onInputChange = None
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def getSensorCount(self):
        """Returns the number of analog inputs on the Interface Kit.
        
        Not all interface kits have the same number of analog inputs, and some don't have any analog inputs at all.
        
        Returns:
            Number of analog inputs <int>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        sensorCount = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetInterfaceKit_getSensorCount(self.handle, byref(sensorCount))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return sensorCount.value

    def getSensorValue(self, index):
        """Returns the value of a analog input.
        
        The analog inputs are where analog sensors are attached on the InterfaceKit 8/8/8.
        On the Linear and Circular touch sensor Phidgets, analog input 0 represents position on the slider.
        
        The valid range is 0-1000. In the case of a sensor, this value can be converted to an actual sensor
        value using the formulas provided in the sensor product manual.
        
        Parameters:
            index<int>: Index of the sensor.
        
        Returns:
            The Sensor value <int>
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        sensorValue = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetInterfaceKit_getSensorValue(self.handle, c_int(index), byref(sensorValue))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return sensorValue.value

    def getSensorRawValue(self, index):
        """Returns the raw value of a analog input.
        
        This is a more accurate version of getSensorValue. The valid range is 0-4095.
        Note however that the analog outputs on the Interface Kit 8/8/8 are only 10-bit values and this value represents an oversampling to 12-bit.
        
        Parameters:
            index<int>: Index of the sensor.
        
        Returns:
            The Raw Sensor value <int>
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        sensorValue = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetInterfaceKit_getSensorRawValue(self.handle, c_int(index), byref(sensorValue))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return sensorValue.value
    
    def getDataRate(self, index):
        """
        Returns the maximum rate at which events will be fired, in ms.
        
        Parameters:
            index<int>: Index of the sensor.
        
        Returns:
            The specified data rate <int>
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        dataRate = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetInterfaceKit_getDataRate(self.handle, c_int(index), byref(dataRate))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return dataRate.value
    
    def setDataRate(self, index, value):
        """
        Sets the maximum rate at which events will be fired, in ms.
        
        This value needs to be a multiple of 8, between DataRateMin and DataRateMax.  I.E. 1,2,4,8,16,24,32,....
        
        Parameters:
            index<int>: Index of the sensor.
            value<int>: The desired Data Rate Value.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, if the index is out of range, or the supplied data rate value is out of range.
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetInterfaceKit_setDataRate(self.handle, c_int(index), c_int(value))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
    
    def getDataRateMax(self, index):
        """
        Returns the maximum supported data rate value that can be set.
        
        Parameters:
            index<int>: Index of the sensor.
        
        Returns:
            The maximum supported data rate <int>
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        maxVal = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetInterfaceKit_getDataRateMax(self.handle, c_int(index), byref(maxVal))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return maxVal.value
    
    def getDataRateMin(self, index):
        """
        Returns the minimum supported data rate value that can be set.
        
        Parameters:
            index<int>: Index of the sensor.
        
        Returns:
            The minimum supported data rate <int>
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        minVal = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetInterfaceKit_getDataRateMin(self.handle, c_int(index), byref(minVal))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return minVal.value

    def getSensorChangeTrigger(self, index):
        """Returns the change trigger for an analog input.
        
        This is the amount that an inputs must change between successive SensorChangeEvents.
        This is based on the 0-1000 range provided by getSensorValue. This value is by default set to 10 for most Interface Kits with analog inputs.
        
        Parameters:
            index<int>: Index of the sensor.
        
        Returns:
            The Trigger value <int>
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        sensitivity = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetInterfaceKit_getSensorChangeTrigger(self.handle, c_int(index), byref(sensitivity))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return sensitivity.value

    def setSensorChangeTrigger(self, index, value):
        """Sets the change trigger for an analog input.
        
        This is the amount that an inputs must change between successive SensorChangeEvents.
        This is based on the 0-1000 range provided by getSensorValue. This value is by default set to 10 for most Interface Kits with analog inputs.
        
        Parameters:
            index<int>: Index of the sensor.
            value<int>: The Trigger Value.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetInterfaceKit_setSensorChangeTrigger(self.handle, c_int(index), c_int(value))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def __nativeSensorChangeEvent(self, handle, usrptr, index, value):
        if self.__sensorChange != None:
            self.__sensorChange(SensorChangeEventArgs(self, index, value))
        return 0

    def setOnSensorChangeHandler(self, sensorChangeHandler):
        """Set the SensorChange Event Handler.
        
        The sensor change handler is a method that will be called when a sensor on
        this Interface Kit has changed by at least the Trigger that has been set for this sensor.
        
        Parameters:
            sensorChangeHandler: hook to the sensorChangeHandler callback function.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException
        """
        if sensorChangeHandler == None:
            self.__sensorChange = None
            self.__onSensorChange = None
        else:
            self.__sensorChange = sensorChangeHandler
            self.__onSensorChange = self.__SENSORCHANGEHANDLER(self.__nativeSensorChangeEvent)
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetInterfaceKit_set_OnSensorChange_Handler(self.handle, self.__onSensorChange, None)
        except RuntimeError:
            self.__sensorChange = None
            self.__onSensorChange = None
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def getOutputCount(self):
        """Returns the number of digital outputs on this Interface Kit.
        
        Not all interface kits have the same number of digital outputs, and some don't have any digital outputs at all.
        
        Returns:
            The Number of digital outputs <int>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        outputCount = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetInterfaceKit_getOutputCount(self.handle, byref(outputCount))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return outputCount.value

    def getOutputState(self, index):
        """Returns the state of a digital output.
        
        Depending on the Phidget, this value may be either the value that you last wrote out to the Phidget, or the value that the Phidget last returned.
        This is because some Phidgets return their output state and others do not.
        This means that with some devices, reading the output state of a pin directly after setting it, may not return the value that you just set.
        
        Be sure to check getOutputCount first if you are unsure as to the number of outputs, so as not to attempt to get an Index that is out of range.
        
        Parameters:
            index<int>: Index of the output.
        
        Returns:
            State of the output <boolean>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        outputState = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetInterfaceKit_getOutputState(self.handle, c_int(index), byref(outputState))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            if outputState.value == 1:
                return True
            else:
                return False

    def setOutputState (self, index, state):
        """Sets the state of a digital output.
        
        Setting this to True will activate the output, False is the default state.
        
        Parameters:
            index<int>: Index of the output.
            state<boolean>: State to set the output to.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        if state == True:
            value = 1
        else:
            value = 0
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetInterfaceKit_setOutputState(self.handle, c_int(index), c_int(value))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def __nativeOutputChangeEvent(self, handle, usrptr, index, value):
        if self.__outputChange != None:
            if value == 1:
                state = True
            else:
                state = False
            self.__outputChange(OutputChangeEventArgs(self, index, state))
        return 0

    def setOnOutputChangeHandler(self, outputChangeHandler):
        """Sets the OutputChange Event Handler.
        
        The output change handler is a method that will be called when an output on this Interface Kit has changed.
        
        Parameters:
            outputChangeHandler: hook to the outputChangeHandler callback function.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException
        """
        if outputChangeHandler == None:
            self.__outputChange = None
            self.__onOutputChange = None
        else:
            self.__outputChange = outputChangeHandler
            self.__onOutputChange = self.__OUTPUTCHANGEHANDLER(self.__nativeOutputChangeEvent)
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetInterfaceKit_set_OnOutputChange_Handler(self.handle, self.__onOutputChange, None)
        except RuntimeError:
            self.__outputChange = None
            self.__onOutputChange = None
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def getRatiometric(self):
        """Gets the ratiometric state for the analog sensors
        
        Returns:
            State of the Ratiometric setting.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if this phidget does not support ratiometric.
        """
        ratiometricState = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetInterfaceKit_getRatiometric(self.handle, byref(ratiometricState))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            if ratiometricState.value == 1:
                return True
            else:
                return False

    def setRatiometric(self, state):
        """Sets the ratiometric state for the analog inputs.
        
        The default is for ratiometric to be set on and this is appropriate for most sensors.
        
        False - off
        True - on
        
        Parameters:
            state<boolean>: State of the ratiometric setting.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if this Phidget does not support ratiometric.
        """
        if state == True:
            value = 1
        else:
            value = 0
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetInterfaceKit_setRatiometric(self.handle, c_int(value))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
