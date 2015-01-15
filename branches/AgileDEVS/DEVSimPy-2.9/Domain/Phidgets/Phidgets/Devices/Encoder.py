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
from Phidgets.Events.Events import EncoderPositionChangeEventArgs, InputChangeEventArgs
import sys

class Encoder(Phidget):
    """This class represents a Phidget Encoder. All methods to read encoder data from an encoder are implemented in this class.
    
    Phidget Encoder boards generally support 1 or more encoders with 0 or more digital inputs. Both high speed optical and low speed mechanical encoders are supported with this API.
	
	See your device's User Guide for more specific API details, technical information, and revision details. 
	The User Guide, along with other resources, can be found on the product page for your device.
    
    Extends:
        Phidget
    """
    def __init__(self):
        """The Constructor Method for the Encoder Class
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened.
        """
        Phidget.__init__(self)
        
        self.__inputChange = None
        self.__positionChange = None
        
        self.__onInputChange = None
        self.__onPositionChange = None
        
        try:
            PhidgetLibrary.getDll().CPhidgetEncoder_create(byref(self.handle))
        except RuntimeError:
            raise
        
        if sys.platform == 'win32':
            self.__INPUTCHANGEHANDLER = WINFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_int)
            self.__POSITIONCHANGEHANDLER = WINFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_int, c_int)
        elif sys.platform == 'darwin' or sys.platform == 'linux2':
            self.__INPUTCHANGEHANDLER = CFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_int)
            self.__POSITIONCHANGEHANDLER = CFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_int, c_int)

    def __del__(self):
        """The Destructor Method for the Encoder Class
        """
        Phidget.dispose(self)

    def getPosition(self, index):
        """Returns the position of an encoder.
        
        This is an absolute position as calcutated since the encoder was plugged in.
        This value can be reset to anything using setPosition.
        
        Parameters:
            index<int>: index of the encoder.
        
        Returns:
            The position of the encoder <int>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        position = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetEncoder_getPosition(self.handle, c_int(index), byref(position))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return position.value

    def setPosition(self, index, position):
        """Sets the position of a specific encoder.
        
        This resets the internal position count for an encoder.
        This call in no way actually sends information to the device, as an absolute position is maintained only in the library.
        After this call, position changes from the encoder will use the new value to calculate absolute position as reported by the change handler.
        
        Parameters:
            index<int>: index of the encoder.
            position<position>: new position for this encoder.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetEncoder_setPosition(self.handle, c_int(index), c_int(position))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
    
    def getIndexPosition(self, index):
        """Gets the index position for an encoder that supports index.
        
        For encoders that support index position, this function will return the index position for the encoder connected at the provided index.
        
        Parameters:
            index<int>: index of the encoder.
        
        Returns:
            The index position of the encoder <int>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        indexPositon = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetEncoder_getIndexPosition(self.handle, c_int(index), byref(indexPositon))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return indexPositon.value

    def getEnabled(self, index):
        """Gets the enabled state of an encoder.
        
        Returns whether power to the encoder is enabled or disabled.
        
        Parameters:
            index<int>: index of the encoder.
        
        Returns:
            The enabled state of the encoder <boolean>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        enabledState = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetEncoder_getEnabled(self.handle, c_int(index), byref(enabledState))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            if enabledState.value ==1:
                return True
            else:
                return False

    def setEnabled(self, index, state):
        """Sets the enabled state of an encoder.
        
        The enabled state controls whether to enable or disable power to the encoder.
        
        Parameters:
            index<int>: Index of the motor.
            state<boolean>: State to set the enabled state for this encoder to.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        if state == True:
            value = 1
        else:
            value = 0
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetEncoder_setEnabled(self.handle, c_int(index), c_int(value))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def getInputState(self, index):
        """Returns the state of a digital input.
        
        On the mechanical encoder this refers to the pushbutton.
        The high speed encoder does not have any digital inputs. A value of true means that the input is active(the button is pushed).
        
        Parameters:
            index<int>: index of the input.
        
        Returns:
            The state of the input <boolean>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        inputState = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetEncoder_getInputState(self.handle, c_int(index), byref(inputState))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            if inputState.value ==1:
                return True
            else:
                return False

    def getEncoderCount(self):
        """Returns number of encoders.
        
        All current encoder boards support one encoder.
        
        Returns:
            The number of encoders <int>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        encoderCount = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetEncoder_getEncoderCount(self.handle, byref(encoderCount))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return encoderCount.value

    def getInputCount(self):
        """Returns number of digital inputs.
        
        On the mechanical encoder this refers to the pushbutton.
        The high speed encoder does not have any digital inputs.
        
        Returns:
            The number of inputs <int>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        inputCount = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetEncoder_getInputCount(self.handle, byref(inputCount))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return inputCount.value

    def __nativeInputChangeEvent(self, handle, usrptr, index, value):
        if self.__inputChange != None:
            if value == 1:
                state = True
            else:
                state = False
            self.__inputChange(InputChangeEventArgs(self, index, state))
        return 0

    def setOnInputChangeHandler(self, inputChangeHandler):
        """Sets the input change event handler.
        
        The input change handler is a method that will be called when an input on this Encoder board has changed.
        
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
            result = PhidgetLibrary.getDll().CPhidgetEncoder_set_OnInputChange_Handler(self.handle, self.__onInputChange, None)
        except RuntimeError:
            self.__inputChange = None
            self.__onInputChange = None
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def __nativePositionChangeEvent(self, handle, usrptr, index, time, position):
        if self.__positionChange != None:
            self.__positionChange(EncoderPositionChangeEventArgs(self, index, time, position))
        return 0

    def setOnPositionChangeHandler(self, positionChangeHandler):
        """Sets the position change event handler.
        
        The position change handler is a method that will be called when the position of an encoder changes.
        The position change event provides data about how many ticks have occured, and how much time has passed since the last position change event,
        but does not contain an absolute position.
        This can be obtained from getEncoderPosition.
        
        Parameters:
            positionChangeHandler: hook to the positionChangeHandler callback function.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException
        """
        if positionChangeHandler == None:
            self.__positionChange = None
            self.__onPositionChange = None
        else:
            self.__positionChange = positionChangeHandler
            self.__onPositionChange = self.__POSITIONCHANGEHANDLER(self.__nativePositionChangeEvent)
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetEncoder_set_OnPositionChange_Handler(self.handle, self.__onPositionChange, None)
        except RuntimeError:
            self.__positionChange = None
            self.__onPositionChange = None
            raise
        
        if result > 0:
            raise PhidgetException(result)
