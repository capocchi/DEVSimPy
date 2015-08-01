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
from Phidgets.Events.Events import PositionChangeEventArgs
import sys

class ServoTypes:
    """This is an enumeration of servo types and their values.
    
    This has been added to allow the user to select the type of servo they are using and the library will load known values
    for the selected motor's properties.
    """
    PHIDGET_SERVO_DEFAULT=1
    PHIDGET_SERVO_RAW_us_MODE=2
    PHIDGET_SERVO_HITEC_HS322HD=3
    PHIDGET_SERVO_HITEC_HS5245MG=4
    PHIDGET_SERVO_HITEC_805BB=5
    PHIDGET_SERVO_HITEC_HS422=6
    PHIDGET_SERVO_TOWERPRO_MG90=7
    PHIDGET_SERVO_HITEC_HSR1425CR=8
    PHIDGET_SERVO_HITEC_HS785HB=9
    PHIDGET_SERVO_HITEC_HS485HB=10
    PHIDGET_SERVO_HITEC_HS645MG=11
    PHIDGET_SERVO_HITEC_815BB=12
    PHIDGET_SERVO_FIRGELLI_L12_30_50_06_R=13
    PHIDGET_SERVO_FIRGELLI_L12_50_100_06_R=14
    PHIDGET_SERVO_FIRGELLI_L12_50_210_06_R=15
    PHIDGET_SERVO_FIRGELLI_L12_100_50_06_R=16
    PHIDGET_SERVO_FIRGELLI_L12_100_100_06_R=17
    PHIDGET_SERVO_USER_DEFINED=18
    PHIDGET_SERVO_INVALID=0
    

class Servo(Phidget):
    """This class represents a Phidget servo Controller.
    
    All methods to control a Servo Controller are implemented in this class.
    The Phidget Sevo controller simply outputs varying widths of PWM, which is what most servo motors take as an input driving signal.
	
	See your device's User Guide for more specific API details, technical information, and revision details. 
	The User Guide, along with other resources, can be found on the product page for your device.
    
    Extends:
        Phidget
    """
    #servoTypes = {'DEFAULT':1, 'RAW_us_MODE':2, 'HITEC_HS322HD':3, 'HITEC_HS5245MG':4, 'HITEC_805BB':5, 'HITEC_HS422':6, 'TOWERPRO_MG90':7, 'USER_DEFINED':8, 'INVALID':0}
    
    def __init__(self):
        """The Constructor Method for the Servo Class
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
        """
        Phidget.__init__(self)
        
        self.__positionChange = None
        
        self.__onPositionChange = None
        
        try:
            PhidgetLibrary.getDll().CPhidgetServo_create(byref(self.handle))
        except RuntimeError:
            raise
        
        if sys.platform == 'win32':
            self.__POSITIONCHANGEHANDLER = WINFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_double)
        elif sys.platform == 'darwin' or sys.platform == 'linux2':
            self.__POSITIONCHANGEHANDLER = CFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_double)

    def __del__(self):
        """The Destructor Method for the Servo Class
        """
        Phidget.dispose(self)

    def getMotorCount(self):
        """Returns the number of motors this Phidget can support.
        
        Note that there is no way of programatically determining how many motors are actually attached to the board.
        
        Returns:
            The number of motors <int>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        motorCount = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetServo_getMotorCount(self.handle, byref(motorCount))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return motorCount.value

    def getPosition(self, index):
        """Returns the position of a servo motor.
        
        Note that since servo motors do not offer any feedback in their interface, this value is simply whatever the servo was last set to.
        There is no way of determining the position of a servo that has been plugged in, until it's position has been set.
        Therefore, if an initial position is important, it should be set as part of initialization.
        
        If the servo is not engaged, the position is unknown and calling this function will throw an exception.
        
        The range here is between getPositionMin and getPositionMax, and corresponds aproximately to an angle in degrees. Note that most servos will not be able to operate accross this entire range.
        
        Parameters:
            index<int>: index of the motor.
        
        Returns:
            The current position of the selected motor <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range, or the motor is not engaged.
        """
        position = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetServo_getPosition(self.handle, c_int(index), byref(position))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return position.value

    def setPosition(self, index, value):
        """Sets the position of a servo motor.
        
        The range here is between getPositionMin and getPositionMax, and corresponds aproximately to an angle in degrees.
        Note that most servos will not be able to operate accross this entire range.
        Typically, the range might be 25 - 180 degrees, but this depends on the servo.
        
        Parameters:
            index<int>: index of the motor.
            position<double>: desired position for the motor.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index or position is out of range,
            or if the desired position is out of range, or if the motor is not engaged.
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetServo_setPosition(self.handle, c_int(index), c_double(value))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def getPositionMax(self, index):
        """Returns the maximum position that a servo will accept, or return.
        
        Returns:
            The maximum position in degrees <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        positionMax = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetServo_getPositionMax(self.handle, c_int(index), byref(positionMax))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return positionMax.value

    def getPositionMin(self, index):
        """Returns the minimum position that a servo will accept, or return.
        
        Returns:
            The minimum position in degrees <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        positionMin = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetServo_getPositionMin(self.handle, c_int(index), byref(positionMin))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return positionMin.value

    def __nativePositionChangeEvent(self, handle, usrptr, index, value):
        if self.__positionChange != None:
            self.__positionChange(PositionChangeEventArgs(self, index, value))
        return 0

    def setOnPositionChangeHandler(self, positionChangeHandler):
        """Sets the Position Change Event Handler.
        
        The servo position change handler is a method that will be called when the servo position has changed.
        The event will get fired after every call to setPosition.
        
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
            result = PhidgetLibrary.getDll().CPhidgetServo_set_OnPositionChange_Handler(self.handle, self.__onPositionChange, None)
        except RuntimeError:
            self.__positionChange = None
            self.__onPositionChange = None
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def getEngaged(self, index):
        """Returns the engaged state of a servo
        
        Returns:
            Motor Engaged state <boolean>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        engagedStatus = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetServo_getEngaged(self.handle, c_int(index), byref(engagedStatus))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            if engagedStatus.value == 1:
                return True
            else:
                return False

    def setEngaged(self, index, state):
        """Engage or disengage a servo motor
        
        This engages or disengages the servo.
        The motor is engaged whenever you set a position, use this function to
        disengage, and reengage without setting a position.
        
        Parameters:
            index<int>: index of a servo motor.
            state<boolean>: desired engaged state of the servo motor.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        if state == True:
            value = 1
        else:
            value = 0
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetServo_setEngaged(self.handle, c_int(index), c_int(value))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def getServoType(self, index):
        """Returns the servo type of the specified motor.
        
        Parameters:
            index<int>: index of a servo motor.
        
        Returns:
            Servo type for the motor<int>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        servoType = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetServo_getServoType(self.handle, c_int(index), byref(servoType))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return servoType.value
    
    def setServoType(self, index, servoType):
        """Sets the desired servo type for a specified motor.
        
        Parameters:
            index<int>: index of a servo motor.
            servoType<int>: The desired servo type for the motor.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetServo_setServoType(self.handle, c_int(index), c_int(servoType))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
    
    def setServoParameters(self, index, minimumPulseWidth, maximumPulseWidth, degrees):
        """Sets custom servo parameters for using a servo not in the predefined list.
        
        Pulse widths are specified in microseconds.
        
        Parameters:
            index<int>: index of a servo motor.
            minimumPulseWidth<double>: The minimum pulse width for this servo motor type.
            maximumPulseWidth<double>: The Maximum pulse width for this servo motor type.
            degrees<double>: The maximum degrees of rotation this servo motor type is capable of.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetServo_setServoParameters(self.handle, c_int(index), c_double(minimumPulseWidth), c_double(maximumPulseWidth), c_double(degrees))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)