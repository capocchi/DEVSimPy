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
from Phidgets.PhidgetException import PhidgetException
from Phidgets.Events.Events import CurrentChangeEventArgs, InputChangeEventArgs, VelocityChangeEventArgs
from Phidgets.Events.Events import EncoderPositionChangeEventArgs, BackEMFEventArgs, CurrentUpdateEventArgs
from Phidgets.Events.Events import EncoderPositionUpdateEventArgs, SensorUpdateEventArgs
import sys

class MotorControl(Phidget):
    """This class represents a Phidget Motor Controller. All methods to to control a motor controller and read back motor data are implemented in this class.
    
    The Motor Control Phidget is able to control 1 or more DC motors and has 0 or more digital inputs. 
	Both speed and acceleration are controllable. Speed is controlled via PWM.
    The size of the motors that can be driven depends on the motor controller. 
	See your device's User Guide for more specific API details, technical information, and revision details. 
	The User Guide, along with other resources, can be found on the product page for your device.
    
    Extends:
        Phidget
    """
    def __init__(self):
        """The Constructor Method for the MotorControl Class
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
        """
        Phidget.__init__(self)
        
        self.__inputChange = None
        self.__velocityChange = None
        self.__currentChange = None
        self.__currentUpdate = None
        self.__positionChange = None
        self.__positionUpdate = None
        self.__sensorUpdate = None
        self.__backEMFUpdate = None
        
        self.__onInputChange = None
        self.__onVelocityChange = None
        self.__onCurrentChange = None
        self.__onCurrentUpdate = None
        self.__onPositionChange = None
        self.__onPositionUpdate = None
        self.__onSensorUpdate = None
        self.__onBackEMFUpdate = None
        
        try:
            PhidgetLibrary.getDll().CPhidgetMotorControl_create(byref(self.handle))
        except RuntimeError:
            raise
        
        if sys.platform == 'win32':
            self.__INPUTCHANGEHANDLER = WINFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_int)
            self.__VELOCITYCHANGEHANDLER = WINFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_double)
            self.__CURRENTCHANGEHANDLER = WINFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_double)
            self.__CURRENTUPDATEHANDLER = WINFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_double)
            self.__POSITIONCHANGEHANDLER = WINFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_int, c_int)
            self.__POSITIONUPDATEHANDLER = WINFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_int)
            self.__SENSORUPDATEHANDLER = WINFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_int)
            self.__BACKEMFUPDATEHANDLER = WINFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_double)
        elif sys.platform == 'darwin' or sys.platform == 'linux2':
            self.__INPUTCHANGEHANDLER = CFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_int)
            self.__VELOCITYCHANGEHANDLER = CFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_double)
            self.__CURRENTCHANGEHANDLER = CFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_double)
            self.__CURRENTUPDATEHANDLER = CFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_double)
            self.__POSITIONCHANGEHANDLER = CFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_int, c_int)
            self.__POSITIONUPDATEHANDLER = CFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_int)
            self.__SENSORUPDATEHANDLER = CFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_int)
            self.__BACKEMFUPDATEHANDLER = CFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_double)

    def __del__(self):
        """The Destructor Method for the MotorControl Class
        """
        Phidget.dispose(self)

    def getMotorCount(self):
        """Returns the number of motors supported by this Phidget.
        
        This does not neccesarily correspond to the number of motors actually attached to the board.
        
        Returns:
            The number of supported motors <int>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        motorCount = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetMotorControl_getMotorCount(self.handle, byref(motorCount))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return motorCount.value

    def getVelocity(self, index):
        """Returns a motor's velocity.
        
        The valid range is -100 - 100, with 0 being stopped.
        
        Parameters:
            index<int>: index of the motor.
        
        Returns:
            The current velocity of the motor <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is invalid.
        """
        veloctiy = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetMotorControl_getVelocity(self.handle, c_int(index), byref(veloctiy))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return veloctiy.value

    def setVelocity(self, index, value):
        """Sets a motor's velocity.
        
        The valid range is from -100 to 100, with 0 being stopped. -100 and 100 both corespond to full voltage,
        with the value in between corresponding to different widths of PWM.
        
        Parameters:
            index<int>: index of the motor.
            value<double>: requested velocity for the motor.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index or velocity value are invalid.
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetMotorControl_setVelocity(self.handle, c_int(index), c_double(value))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def __nativeVelocityChangeEvent(self, handle, usrptr, index, value):
        if self.__velocityChange != None:
            self.__velocityChange(VelocityChangeEventArgs(self, index, value))
        return 0

    def setOnVelocityChangeHandler(self, velocityChangeHandler):
        """Sets the VelocityChange Event Handler.
        
        The velocity change handler is a method that will be called when the velocity of a motor changes.
        These velocity changes are reported back from the Motor Controller and so correspond to actual motor velocity over time.
        
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
            result = PhidgetLibrary.getDll().CPhidgetMotorControl_set_OnVelocityChange_Handler(self.handle, self.__onVelocityChange, None)
        except RuntimeError:
            self.__velocityChange = None
            self.__onVelocityChange = None
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def getAcceleration(self, index):
        """Returns a motor's acceleration.
        
        The valid range is between getAccelerationMin and getAccelerationMax,
        and refers to how fast the Motor Controller will change the speed of a motor.
        
        Parameters:
            index<int>: index of motor.
        
        Returns:
            The acceleration of the motor <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is invalid.
        """
        accel = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetMotorControl_getAcceleration(self.handle, c_int(index), byref(accel))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return accel.value

    def setAcceleration(self, index, value):
        """Sets a motor's acceleration.
        
        The valid range is between getAccelerationMin and getAccelerationMax.
        This controls how fast the motor changes speed.
        
        Parameters:
            index<int>: index of the motor.
            value<double>: requested acceleration for that motor.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index or acceleration value are invalid.
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetMotorControl_setAcceleration(self.handle, c_int(index), c_double(value))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def getAccelerationMax(self, index):
        """Returns the maximum acceleration that a motor will accept, or return.
        
        Parameters:
            index<int>: Index of the motor.
        
        Returns:
            Maximum acceleration of the motor <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        accelMax = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetMotorControl_getAccelerationMax(self.handle, c_int(index), byref(accelMax))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return accelMax.value

    def getAccelerationMin(self, index):
        """Returns the minimum acceleration that a motor will accept, or return.
        
        Parameters:
            index<int>: Index of the motor.
        
        Returns:
            Minimum acceleration of the motor <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        accelMin = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetMotorControl_getAccelerationMin(self.handle, c_int(index), byref(accelMin))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return accelMin.value

    def getCurrent(self, index):
        """Returns a motor's current usage.
        
        The valid range is 0 - 255. Note that this is not supported on all motor controllers.
        
        Parameters:
            index<int>: index of the motor.
        
        Returns:
            The current usage of the motor <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is invalid.
        """
        current = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetMotorControl_getCurrent(self.handle, c_int(index), byref(current))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return current.value

    def __nativeCurrentChangeEvent(self, handle, usrptr, index, value):
        if self.__currentChange != None:
            self.__currentChange(CurrentChangeEventArgs(self, index, value))
        return 0

    def setOnCurrentChangeHandler(self, currentChangeHandler):
        """Sets the CurrentCHange Event Handler.
        
        The current change handler is a method that will be called when the current consumed by a motor changes.
        Note that this event is not supported with the current motor controller, but will be supported in the future
        
        Parameters:
            currentChangeHandler: hook to the currentChangeHandler callback function.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException
        """
        if currentChangeHandler == None:
            self.__currentChange = None
            self.__onCurrentChange = None
        else:
            self.__currentChange = currentChangeHandler
            self.__onCurrentChange = self.__CURRENTCHANGEHANDLER(self.__nativeCurrentChangeEvent)
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetMotorControl_set_OnCurrentChange_Handler(self.handle, self.__onCurrentChange, None)
        except RuntimeError:
            self.__currentChange = None
            self.__onCurrentChange = None
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def __nativeCurrentUpdateEvent(self, handle, usrptr, index, current):
        if self.__currentUpdate != None:
            self.__currentUpdate(CurrentUpdateEventArgs(self, index, current))
        return 0

    def setOnCurrentUpdateHandler(self, currentUpdateHandler):
        """Sets the CurrentCHange Event Handler.

        The current change handler is a method that will be called when the current consumed by a motor changes.
        Note that this event is not supported with the current motor controller, but will be supported in the future

        Parameters:
            currentChangeHandler: hook to the currentChangeHandler callback function.

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException
        """
        if currentUpdateHandler == None:
            self.__currentUpdate = None
            self.__onCurrentUpdate = None
        else:
            self.__currentUpdate = currentUpdateHandler
            self.__onCurrentUpdate = self.__CURRENTUPDATEHANDLER(self.__nativeCurrentUpdateEvent)

        try:
            result = PhidgetLibrary.getDll().CPhidgetMotorControl_set_OnCurrentUpdate_Handler(self.handle, self.__onCurrentUpdate, None)
        except RuntimeError:
            self.__currentUpdate = None
            self.__onCurrentUpdate = None
            raise

        if result > 0:
            raise PhidgetException(result)

    def getInputCount(self):
        """Returns the number of digital inputs.
        
        Not all Motor Controllers have digital inputs.
        
        Returns:
            The number of digital Inputs <int>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        inputCount = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetMotorControl_getInputCount(self.handle, byref(inputCount))
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
            index<int> index of the input.
        
        Returns:
            The state of the input <boolean>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is invalid.
        """
        inputState = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetMotorControl_getInputState(self.handle, c_int(index), byref(inputState))
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
        """Sets the InputChange Event Handler.
        
        The input change handler is a method that will be called when an input on this Motor Controller board has changed.
        
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
            result = PhidgetLibrary.getDll().CPhidgetMotorControl_set_OnInputChange_Handler(self.handle, self.__onInputChange, None)
        except RuntimeError:
            self.__inputChange = None
            self.__onInputChange = None
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def getEncoderCount(self):
        """

        """
        encoderCount = c_int()

        try:
            result = PhidgetLibrary.getDll().CPhidgetMotorControl_getEncoderCount(self.handle, byref(encoderCount))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)
        else:
            return encoderCount.value

    def getEncoderPosition(self, index):
        """

        """
        encoderPosition = c_int()

        try:
            result = PhidgetLibrary.getDll().CPhidgetMotorControl_getEncoderPosition(self.handle, c_int(index), byref(encoderPosition))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)
        else:
            return encoderPosition.value

    def setEncoderPosition(self, index, encoderPosition):
        """

        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetMotorControl_setEncoderPosition(self.handle, c_int(index), c_int(encoderPosition))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)

    def __nativePositionChangeEvent(self, handle, usrptr, index, time, positionChange):
        if self.__positionChange != None:
            self.__positionChange(EncoderPositionChangeEventArgs(self, index, time, positionChange))
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
            result = PhidgetLibrary.getDll().CPhidgetMotorControl_set_OnEncoderPositionChange_Handler(self.handle, self.__onPositionChange, None)
        except RuntimeError:
            self.__positionChange = None
            self.__onPositionChange = None
            raise

        if result > 0:
            raise PhidgetException(result)
    
    def __nativePositionUpdateEvent(self, handle, usrptr, index, positionChange):
        if self.__positionUpdate != None:
            self.__positionUpdate(EncoderPositionUpdateEventArgs(self, index, positionChange))
        return 0

    def setOnPositionUpdateHandler(self, positionUpdateHandler):
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
        if positionUpdateHandler == None:
            self.__positionUpdate = None
            self.__onPositionUpdate = None
        else:
            self.__positionUpdate = positionUpdateHandler
            self.__onPositionUpdate = self.__POSITIONUPDATEHANDLER(self.__nativePositionUpdateEvent)

        try:
            result = PhidgetLibrary.getDll().CPhidgetMotorControl_set_OnEncoderPositionUpdate_Handler(self.handle, self.__onPositionUpdate, None)
        except RuntimeError:
            self.__positionUpdate = None
            self.__onPositionUpdate = None
            raise

        if result > 0:
            raise PhidgetException(result)

    def getSensorCount(self):
        """Returns the number of analog inputs on the Motor Control.

        

        Returns:
            Number of analog inputs <int>.

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        sensorCount = c_int()

        try:
            result = PhidgetLibrary.getDll().CPhidgetMotorControl_getSensorCount(self.handle, byref(sensorCount))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)
        else:
            return sensorCount.value

    def getSensorValue(self, index):
        """Returns the value of a analog input.

        The analog inputs are where analog sensors are attached on the Motor Control.

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
            result = PhidgetLibrary.getDll().CPhidgetMotorControl_getSensorValue(self.handle, c_int(index), byref(sensorValue))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)
        else:
            return sensorValue.value

    def getSensorRawValue(self, index):
        """Returns the raw value of a analog input.

        This is a more accurate version of getSensorValue. The valid range is 0-4095.
        Note however that the analog outputs on the Motor Control are only 10-bit values and this value represents an oversampling to 12-bit.

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
            result = PhidgetLibrary.getDll().CPhidgetMotorControl_getSensorRawValue(self.handle, c_int(index), byref(sensorValue))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)
        else:
            return sensorValue.value

    def __nativeSensorUpdateEvent(self, handle, usrptr, index, value):
        if self.__sensorUpdate != None:
            self.__sensorUpdate(SensorUpdateEventArgs(self, index, value))
        return 0

    def setOnSensorUpdateHandler(self, sensorUpdateHandler):
        """Set the SensorChange Event Handler.

        The sensor change handler is a method that will be called when a sensor on
        this Motor Controller has changed by at least the Trigger that has been set for this sensor.

        Parameters:
            sensorUpdateHandler: hook to the sensorUpdateHandler callback function.

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException
        """
        if sensorUpdateHandler == None:
            self.__sensorUpdate = None
            self.__onSensorUpdate = None
        else:
            self.__sensorUpdate = sensorUpdateHandler
            self.__onSensorUpdate = self.__SENSORUPDATEHANDLER(self.__nativeSensorUpdateEvent)
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetMotorControl_set_OnSensorUpdate_Handler(self.handle, self.__onSensorUpdate, None)
        except RuntimeError:
            self.__sensorUpdate = None
            self.__onSensorUpdate = None
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
            result = PhidgetLibrary.getDll().CPhidgetMotorControl_getRatiometric(self.handle, byref(ratiometricState))
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
            result = PhidgetLibrary.getDll().CPhidgetMotorControl_setRatiometric(self.handle, c_int(value))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)

    def getBraking(self, index):
        """

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, the supplied index is out of range, or if this motor controller does not support braking.
        """
        braking = c_double()

        try:
            result = PhidgetLibrary.getDll().CPhidgetMotorControl_getBraking(self.handle, c_int(index), byref(braking))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)
        else:
            return braking.value

    def setBraking(self, index, braking):
        """

        Parameters:
            braking<double>: 

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, the supplied index is out of range, or if this Motor Controller does not support braking.
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetMotorControl_setBraking(self.handle, c_int(index), c_double(braking))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)

    def getSupplyVoltage(self):
        """

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if this Phidget does not support this feature.
        """
        supplyVoltage = c_double()

        try:
            result = PhidgetLibrary.getDll().CPhidgetMotorControl_getSupplyVoltage(self.handle, byref(supplyVoltage))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)
        else:
            return supplyVoltage.value

    def getBackEMFSensingState(self, index):
        """

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, the supplied index is out of range, or if this motor controller does not support braking.
        """
        state = c_int()

        try:
            result = PhidgetLibrary.getDll().CPhidgetMotorControl_getBackEMFSensingState(self.handle, c_int(index), byref(state))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)
        else:
            if state.value == 1:
                return True
            else:
                return False

    def setBackEMFSensingState(self, index, state):
        """

        Parameters:
            state<boolean>:

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, the supplied index is out of range, or if this Motor Controller does not support braking.
        """
        if state == True:
            value = 1
        else:
            value = 0
            
        try:
            result = PhidgetLibrary.getDll().CPhidgetMotorControl_setBackEMFSensingState(self.handle, c_int(index), c_int(value))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)

    def getBackEMF(self, index):
        """

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if this Phidget does not support this feature.
        """
        voltage = c_double()

        try:
            result = PhidgetLibrary.getDll().CPhidgetMotorControl_getBackEMF(self.handle, c_int(index), byref(voltage))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)
        else:
            return voltage.value

    def __nativeBackEMFUpdateEvent(self, handle, usrptr, index, voltage):
        if self.__backEMFUpdate != None:
            self.__backEMFUpdate(BackEMFEventArgs(self, index, voltage))
        return 0

    def setOnBackEMFUpdateHandler(self, backEMFUpdateHandler):
        """Set the BackEMF Update Event Handler.
        

        Parameters:
            sensorUpdateHandler: hook to the sensorUpdateHandler callback function.

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException
        """
        if backEMFUpdateHandler == None:
            self.__backEMFUpdate = None
            self.__onBackEMFUpdate = None
        else:
            self.__backEMFUpdate = backEMFUpdateHandler
            self.__onBackEMFUpdate = self.__SENSORUPDATEHANDLER(self.__nativeBackEMFUpdateEvent)

        try:
            result = PhidgetLibrary.getDll().CPhidgetMotorControl_set_OnBackEMFUpdate_Handler(self.handle, self.__onBackEMFUpdate, None)
        except RuntimeError:
            self.__backEMFUpdate = None
            self.__onBackEMFUpdate = None
            raise

        if result > 0:
            raise PhidgetException(result)
