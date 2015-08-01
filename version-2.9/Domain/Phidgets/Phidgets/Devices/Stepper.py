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
from Phidgets.Events.Events import CurrentChangeEventArgs, InputChangeEventArgs, StepperPositionChangeEventArgs, VelocityChangeEventArgs
import sys

class Stepper(Phidget):
    """This class represents a Phidget Stepper Controller.
    
    All methods to to control a stepper controller and read back stepper data are implemented in this class.
    The Phidget Stepper is able to control 1 or more Stepper motors.
    Motor Acceleration and Velocity are controllable, and micro-stepping is used for bipolar motors.
    The type and number of motors that can be controlled depend on the Stepper Controller.
    Digital inputs are available on select Phidget Stepper Controllers.
	
	See your device's User Guide for more specific API details, technical information, and revision details. 
	The User Guide, along with other resources, can be found on the product page for your device.
    
    Extends:
        Phidget
    """
    def __init__(self):
        """The Constructor Method for the Stepper Class
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
        """
        Phidget.__init__(self)
        
        self.__inputChange = None
        self.__velocityChange = None
        self.__positionChange = None
        self.__currentChange = None
        
        self.__onInputChange = None
        self.__onVelocityChange = None
        self.__onPositionChange = None
        self.__onCurrentChange = None
        
        try:
            PhidgetLibrary.getDll().CPhidgetStepper_create(byref(self.handle))
        except RuntimeError:
            raise
        
        if sys.platform == 'win32':
            self.__INPUTCHANGEHANDLER = WINFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_int)
            self.__VELOCITYCHANGEHANDLER = WINFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_double)
            self.__POSITIONCHANGEHANDLER = WINFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_longlong)
            self.__CURRENTCHANGEHANDLER = WINFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_double)
        elif sys.platform == 'darwin' or sys.platform == 'linux2':
            self.__INPUTCHANGEHANDLER = CFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_int)
            self.__VELOCITYCHANGEHANDLER = CFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_double)
            self.__POSITIONCHANGEHANDLER = CFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_longlong)
            self.__CURRENTCHANGEHANDLER = CFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_double)

    def __del__(self):
        """The Destructor Method for the Stepper Class
        """
        Phidget.dispose(self)

    def getInputCount(self):
        """Returns the number of digital inputs.
        
        Not all Stepper Controllers have digital inputs.
        
        Returns:
            The number of digital inputs available <int>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        inputCount = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetStepper_getInputCount(self.handle, byref(inputCount))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return inputCount.value

    def getInputState(self, index):
        """Returns the state of a digital input.
        
        True means that the input is activated, and False indicated the default state.
        
        Parameters:
            index<int>: The index of the input.
        
        Returns:
            The state of the input <boolean>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is invalid.
        """
        inputState = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetStepper_getInputState(self.handle, c_int(index), byref(inputState))
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
        """Set the InputChange event handler
        
        The input change handler is a method that will be called when an input on this Stepper Controller board has changed.
        
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
            result = PhidgetLibrary.getDll().CPhidgetStepper_set_OnInputChange_Handler(self.handle, self.__onInputChange, None)
        except RuntimeError:
            self.__inputChange = None
            self.__onInputChange = None
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def getMotorCount(self):
        """Returns the number of stepper motors supported by this Phidget.
        
        This does not neccesarily correspond to the number of motors actually attached to the board.
        
        Returns:
            The number of supported motors <int>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        motorCount = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetStepper_getMotorCount(self.handle, byref(motorCount))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return motorCount.value

    def getAcceleration(self, index):
        """Returns a motor's acceleration.
        
        The valid range is between getAccelerationMin and getAccelerationMax, and refers to how fast the Stepper Controller will change the speed of a motor.
        This value is in (micro)steps per second squared. The step unit will depend on the Stepper Controller.
        For example, the Bipolar Stepper controller has an accuracy of 16th steps, so this value would be in 16th steps per second squared.
        
        Parameters:
            index<int>: INdex of a motor.
        
        Returns:
            The acceleration of the motor <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is invalid, or if the acceleration is unknown.
        """
        accel = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetStepper_getAcceleration(self.handle, c_int(index), byref(accel))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return accel.value

    def setAcceleration(self, index, value):
        """Sets a motor's acceleration.
        
        The valid range is between getAccelerationMin and getAccelerationMax, and refers to how fast the Stepper Controller will change the speed of a motor.
        This value is in (micro)steps per second squared. The step unit will depend on the Stepper Controller.
        For example, the Bipolar Stepper controller has an accuracy of 16th steps, so this value would be in 16th steps per second squared.
        
        Parameters:
            index<int>: Index of the motor.
            value<double>: Desired acceleration for that motor.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is invalid, or if the acceleration is unknown.
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetStepper_setAcceleration(self.handle, c_int(index), c_double(value))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def getAccelerationMax(self, index):
        """Returns the maximum acceleration that a motor will accept, or return.
        
        This value uses the same units as setAcceleration/getAcceleration.
        
        Parameters:
            index<int>: Index of the motor.
        
        Returns:
            The maximum allowable acceleration <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or the index is invalid.
        """
        accelMax = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetStepper_getAccelerationMax(self.handle, c_int(index), byref(accelMax))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return accelMax.value

    def getAccelerationMin(self, index):
        """Returns the minimum acceleration that a motor will accept, or return.
        
        This value uses the same units as setAcceleration/getAcceleration.
        
        Parameters:
            index<int>: Index of the motor.
        
        Returns:
            The minumum allowable acceleration <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is invalid.
        """
        accelMin = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetStepper_getAccelerationMin(self.handle, c_int(index), byref(accelMin))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return accelMin.value

    def getVelocityLimit(self, index):
        """Returns a motor's velocity limit.
        
        This is the maximum velocity that the motor will turn at.
        The valid range is between getVelocityMin and getVelocityMax, with 0 being stopped.
        
        This value is in (micro)steps per second. The step unit will depend on the Stepper Controller.
        For example, the Bipolar Stepper controller has an accuracy of 16th steps, so this value would be in 16th steps per second.
        
        Parameters:
            index<int>: The index of the motor.
        
        Returns:
            The maximum speed the motor will run at <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is invalid.
        """
        velocityLimit = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetStepper_getVelocityLimit(self.handle, c_int(index), byref(velocityLimit))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return velocityLimit.value

    def setVelocityLimit(self, index, value):
        """Sets a motor's velocity limit.
        
        This is the maximum velocity that the motor will turn at. The valid range is between getVelocityMin and getVelocityMax, with 0 being stopped.
        This value is in (micro)steps per second. The step unit will depend on the Stepper Controller.
        For example, the Bipolar Stepper controller has an accuracy of 16th steps, so this value would be in 16th steps per second.
        
        Parameters:
            index<int>: The index of the motor.
            value<double>: Desired velocity for the motor.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index or velocity are invalid.
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetStepper_setVelocityLimit(self.handle, c_int(index), c_double(value))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def getVelocity(self, index):
        """Returns a motor's current velocity.
        
        The valid range is between getVelocityMin and getVelocityMax, with 0 being stopped.
        This value is in (micro)steps per second. The step unit will depend on the Stepper Controller.
        For example, the Bipolar Stepper controller has an accuracy of 16th steps, so this value would be in 16th steps per second.
        
        Parameters:
            index<int>: The index of the motor.
        
        Returns:
            The current velocity of the motor <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is invalid, or if the velocity in unknown.
        """
        velocity = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetStepper_getVelocity(self.handle, c_int(index), byref(velocity))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return velocity.value

    def getVelocityMax(self, index):
        """Returns the maximum velocity that a stepper motor will accept, or return.
        
        This value uses the same units as setVelocityLimit/getVelocityLimit and getVelocity.
        
        Parameters:
            index<int>: The index of the motor.
        
        Returns:
            The maximum allowable velocity of the motor <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is invalid.
        """
        velocityMax = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetStepper_getVelocityMax(self.handle, c_int(index), byref(velocityMax))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return velocityMax.value

    def getVelocityMin(self, index):
        """Returns the minimum velocity that a stepper motor will accept, or return.
        
        This value uses the same units as setVelocityLimit/getVelocityLimit and getVelocity.
        
        Parameters:
            index<int>: The index of the motor.
        
        Returns:
            The minimum allowable velocity of the motor <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is invalid.
        """
        velocityMin = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetStepper_getVelocityMin(self.handle, c_int(index), byref(velocityMin))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return velocityMin.value

    def __nativeVelocityChangeEvent(self, handle, usrptr, index, value):
        if self.__velocityChange != None:
            self.__velocityChange(VelocityChangeEventArgs(self, index, value))
        return 0

    def setOnVelocityChangeHandler(self, velocityChangeHandler):
        """Sets the VelocityChange event handler.
        
        The velocity change handler is a method that will be called when the stepper velocity has changed.
        
        Parameters:
            velocityChangeHandler: hook to the velocityChangeHandler callback function.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException
        """
        if velocityChangeHandler == None:
            self.__velocityChange = None
            self.__onVelocityChange = None
        else:
            self.__velocityChange = velocityChangeHandler
            self.__onVelocityChange = self.__VELOCITYCHANGEHANDLER(self.__nativeVelocityChangeEvent)
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetStepper_set_OnVelocityChange_Handler(self.handle, self.__onVelocityChange, None)
        except RuntimeError:
            self.__velocityChange = None
            self.__onVelocityChange = None
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def getTargetPosition(self, index):
        """Returns a motor's target position.
        
        This is the position that the motor wants to be at. If the motor is not moving,
        it probably has reached the target position, and this will match getCurrentPosition.
        
        The valid range is between getPositionMin and getPositionMax.
        
        This value is in (micro)steps. The step unit will depend on the Stepper Controller.
        For example, the Bipolar Stepper controller has an accuracy of 16th steps, so this value would be in 16th steps.
        
         Parameters:
            index<int>: The index of the motor.
        
        Returns:
            The target position of the motor <longlong>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is invalid, or if the position in unknown.
        """
        targetPosition = c_longlong()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetStepper_getTargetPosition(self.handle, c_int(index), byref(targetPosition))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return targetPosition.value

    def setTargetPosition(self, index, value):
        """Sets a motor's target position.
        
        Use this is set the target position for the stepper. If the stepper is engaged (getEngaged) it will start moving towards this target position.
        The valid range is between getPositionMin and getPositionMax.
        
        This value is in (micro)steps. The step unit will depend on the Stepper Controller.
        For example, the Bipolar Stepper controller has an accuracy of 16th steps, so this value would be in 16th steps.
        
        Parameters:
            index<int>: The index of the motor.
            value<longlong>: The desired position for the motor.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index or position are invalid.
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetStepper_setTargetPosition(self.handle, c_int(index), c_longlong(value))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def getCurrentPosition(self, index):
        """Returns a motor's current position.
        
        This is the actual step position that the motor is at right now.
        The valid range is between getPositionMin and getPositionMax.
        
        This value is in (micro)steps. The step unit will depend on the Stepper Controller.
        For example, the Bipolar Stepper controller has an accuracy of 16th steps, so this value would be in 16th steps.
        
        Parameters:
            index<int>: Index of the motor.
        
        Returns:
            The current position of the motor <longlong>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is invalid.
        """
        currentPosition = c_longlong()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetStepper_getCurrentPosition(self.handle, c_int(index), byref(currentPosition))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return currentPosition.value

    def setCurrentPosition(self, index, value):
        """Sets a motor's current position.
        
        Use this is (re)set the current physical position of the motor to a specific position value.
        This does not move the motor, and if the motor is moving, calling this will cause it to stop moving.
        Use setTargetPosition to move the motor to a position.
        The valid range is between getPositionMin and getPositionMax.
        
        This value is in (micro)steps. The step unit will depend on the Stepper Controller.
        For example, the Bipolar Stepper controller has an accuracy of 16th steps, so this value would be in 16th steps.
        
        Parameters:
            index<int>: Index of the motor.
            value<longlong>: The current position of the motor.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index or position are invalid.
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetStepper_setCurrentPosition(self.handle, c_int(index), c_longlong(value))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def getPositionMax(self, index):
        """Returns the maximum position that a stepper motor will accept, or return.
        
        This value uses the same usits as setTargetPosition/getTargetPosition and setCurrentPosition/getCurrentPosition.
        
        Parameters:
            index<int>: Index of the motor.
        
        Returns:
            The maximum allowable position <longlong>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is invalid.
        """
        positionMax = c_longlong()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetStepper_getPositionMax(self.handle, c_int(index), byref(positionMax))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return positionMax.value

    def getPositionMin(self, index):
        """Returns the minimum position that a stepper motor will accept, or return.
        
        This value uses the same usits as setTargetPosition/getTargetPosition and setCurrentPosition/getCurrentPosition.
        
        Parameters:
            index<int>: Index of the motor.
        
        Returns:
            The minimum allowable position <longlong>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is invalid.
        """
        positionMin = c_longlong()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetStepper_getPositionMin(self.handle, c_int(index), byref(positionMin))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return positionMin.value

    def __nativePositionChangeEvent(self, handle, usrptr, index, value):
        if self.__positionChange != None:
            self.__positionChange(StepperPositionChangeEventArgs(self, index, value))
        return 0

    def setOnPositionChangeHandler(self, positionChangeHandler):
        """Sets the PositionChange event handler
        
        The position change handler is a method that will be called when the stepper position has changed.
        
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
            result = PhidgetLibrary.getDll().CPhidgetStepper_set_OnPositionChange_Handler(self.handle, self.__onPositionChange, None)
        except RuntimeError:
            self.__positionChange = None
            self.__onPositionChange = None
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def getCurrentLimit(self, index):
        """Gets a motor's current usage limit.
        
        The valid range is between getCurrentMin and getCurrentMax.
        This gets the maximum current that a motor will be allowed to draw.
        
        Use this with the Bipolar stepper controller to get smooth micro stepping - see the product manual for more details. This value is in Amps.
        
        Note that this is not supported on all stepper controllers.
        
        Parameters:
            index<int>: Index of the motor.
        
        Returns:
            The Current limit for the motor <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, if the index is invalid, if the value is unknown, or if this is not supported.
        """
        currentLimit = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetStepper_getCurrentLimit(self.handle, c_int(index), byref(currentLimit))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return currentLimit.value

    def setCurrentLimit(self, index, value):
        """Sets a motor's current usage limit.
        
        The valid range is between getCurrentMin and getCurrentMax.
        This sets the maximum current that a motor will be allowed to draw.
        
        Use this with the Bipolar stepper controller to get smooth micro stepping - see the product manual for more details. This value is in Amps.
        
        Note that this is not supported on all stepper controllers.
        
        Parameters:
            index<int>: Index of the motor.
            value<double>: The desired Current limit for the motor.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, if the index or value are invalid, or if this is not supported.
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetStepper_setCurrentLimit(self.handle, c_int(index), c_double(value))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def getCurrent(self, index):
        """Returns a motor's current usage.
        
        The valid range is between getCurrentMin and getCurrentMax.
        This value is in Amps.
        
        Note that this is not supported on all stepper controllers.
        
        Parameters:
            index<int>: Index of the motor.
        
        Returns:
            The Current usage for the motor <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, if the index is invalid, if the value is unknown, or if this is not supported.
        """
        current = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetStepper_getCurrent(self.handle, c_int(index), byref(current))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return current.value

    def getCurrentMax(self, index):
        """Returns the maximum current that a stepper motor will accept, or return.
        
        This value is in Amps.
        
        Parameters:
            index<int>: Index of the motor.
        
        Returns:
            The Maximum allowable Current usage for the motor <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, if the index is invalid, or if this is not supported.
        """
        currentMax = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetStepper_getCurrentMax(self.handle, c_int(index), byref(currentMax))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return currentMax.value

    def getCurrentMin(self, index):
        """Returns the minimum current that a stepper motor will accept, or return.
        
        This value is in Amps.
        
        Parameters:
            index<int>: Index of the motor.
        
        Returns:
            The Minimum allowable Current usage for the motor <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, if the index is invalid, or if this is not supported.
        """
        currentMin = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetStepper_getCurrentMin(self.handle, c_int(index), byref(currentMin))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return currentMin.value

    def __nativeCurrentChangeEvent(self, handle, usrptr, index, value):
        if self.__currentChange != None:
            self.__currentChange(CurrentChangeEventArgs(self, index, value))
        return 0

    def setOnCurrentChangeHandler(self, currentChangeHandler):
        """Sets the CurrentChange event handler
        
        The current change handler is a method that will be called when the stepper current has changed.
        
        Note that not all stepper controllers support current sensing.
        
        Parameters:
            currentChangeHandler: hook to the currentChangeHandler callback function.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this is not supported.
        """
        if currentChangeHandler == None:
            self.__currentChange = None
            self.__onCurrentChange = None
        else:
            self.__currentChange = currentChangeHandler
            self.__onCurrentChange = self.__CURRENTCHANGEHANDLER(self.__nativeCurrentChangeEvent)
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetStepper_set_OnCurrentChange_Handler(self.handle, self.__onCurrentChange, None)
        except RuntimeError:
            self.__currentChange = None
            self.__onCurrentChange = None
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def getEngaged(self, index):
        """Returns the engaged state of a motor.
        
        Parameters:
            index<int>: Index of the motor.
        
        Returns:
            The engaged state for the motor <boolean>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        engagedState = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetStepper_getEngaged(self.handle, c_int(index), byref(engagedState))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            if engagedState.value == 1:
                return True
            else:
                return False

    def setEngaged(self, index, state):
        """Engage or disengage a motor.
        
        This engages or disengages the stepper motor. The motors are by default disengaged when the stepper controller is plugged in.
        When the stepper is disengaged, position, velocity, etc. can all be set, but the motor will not start moving until it is engaged.
        If position is read when a motor is disengaged, it will throw an exception.
        
        Parameters:
            index<int>: Index of the motor.
            state<boolean>: The desired engaged state for the motor.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        if state == True:
            value = 1
        else:
            value = 0
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetStepper_setEngaged(self.handle, c_int(index), c_int(value))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def getStopped(self, index):
        """Returns the stopped state of a motor.
        
        Use this to determine if the motor is moving and/or up to date with the latest commands you have sent.
        If this is true, the motor is guaranteed to be stopped and to have processed every command issued.
        Generally, this would be polled after a target position is set to wait until that position is reached.
        
        Parameters:
            index<int>: Index of the motor.
        
        Returns:
            The stopped state of the motor <boolean>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        stoppedState = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetStepper_getStopped(self.handle, c_int(index), byref(stoppedState))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            if stoppedState.value == 1:
                return True
            else:
                return False