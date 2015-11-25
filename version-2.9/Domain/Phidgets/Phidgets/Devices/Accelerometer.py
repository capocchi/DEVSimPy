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
from Phidgets.Events.Events import AccelerationChangeEventArgs
import sys

class Accelerometer(Phidget):
    """This class represents a Phidget Accelerometer. All methods to read acceleration data from an Accelerometer are implemented in this class.
    
    The Phidget Accelerometer provides 2 or 3 axes of acceleration data, at anywhere from 2g to 10g sensitivity, depending on the specific revision. 
	See your device's User Guide for more specific API details, technical information, and revision details. 
	The User Guide, along with other resources, can be found on the product page for your device.
    
    Extends:
        Phidget
    """
    def __init__(self):
        """The Constructor Method for the Accelerometer Class
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
        """
        Phidget.__init__(self)
        
        self.__accelChange = None
        
        self.__onAccelChange = None
        
        try:
            PhidgetLibrary.getDll().CPhidgetAccelerometer_create(byref(self.handle))
        except RuntimeError:
            raise
        
        if sys.platform == 'win32':
            self.__ACCELCHANGEHANDLER = WINFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_double)
        elif sys.platform == 'darwin' or sys.platform == 'linux2':
            self.__ACCELCHANGEHANDLER = CFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_double)

    def __del__(self):
        """The Destructor Method for the Accelerometer Class
        """
        Phidget.dispose(self)

    def getAcceleration(self, index):
        """Returns the acceleration of a particular axis.
        
        This value is returned in g's, where one g of acceleration is equal to gravity.
        This means that at a standstill each axis will measure between -1.0 and 1.0 g's depending on orientation.
        
        This value will always be between getAccelerationMin and getAccelerationMax.
        
        Index 0 is the x-axis, 1 is the y-axis, and 2 is the z-axis (where available).
        
        Parameters:
            index<int>: index of the axis.
        
        Returns:
            Acceleration of the selected axis <double>
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        value = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetAccelerometer_getAcceleration(self.handle, c_int(index), byref(value))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return value.value

    def getAccelerationMax(self, index):
        """Returns the maximum acceleration value that this axis will report.
        
        This will be set to just higher then the maximum acceleration that this axis can measure.
        If the acceleration is equal to this maximum, assume that that axis is saturated beyond what it can measure.
        
        Returns:
            The Maximum Accelration <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        value = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetAccelerometer_getAccelerationMax(self.handle, c_int(index), byref(value))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return value.value

    def getAccelerationMin(self, index):
        """Returns the minimum acceleration value that this axis will report.
        
        This will be set to just lower then the minimum acceleration that this axis can measure.
        If the acceleration is equal to this minimum, assume that that axis is saturated beyond what it can measure.
        
        Returns:
            The Minimum Acceleration <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        value = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetAccelerometer_getAccelerationMin(self.handle, c_int(index), byref(value))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return value.value

    def getAxisCount(self):
        """Returns the number of accelerometer axes.
        
        Currently all accelerometers provide two or three axes of acceleration - x, y, (and z).
        
        Returns:
            The number of Available Axes <int>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this phidget is not opened or attached.
        """
        axisCount = c_int()
        try:
            result = PhidgetLibrary.getDll().CPhidgetAccelerometer_getAxisCount(self.handle, byref(axisCount))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return axisCount.value

    def getAccelChangeTrigger(self, index):
        """Returns the change trigger for an Axis.
        
        This value is in g's and is by default set to 0.
        
        Parameters:
            index<int>: index of the axis.
        
        Returns:
            The change trigger of the selected axis <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        sensitivity = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetAccelerometer_getAccelerationChangeTrigger(self.handle, c_int(index), byref(sensitivity))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return sensitivity.value
        
    def setAccelChangeTrigger(self, index, sensitivity):
        """Sets the change trigger for an Axis.
        
        This value is in g's and is by default set to 0.
        This is the difference in acceleration that must appear between succesive calls to the OnAccelerationChange event handler.
        
        Parameters:
            index<int>: index of the axis.
            sensitivity<double>: the new change trigger for this axis.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetAccelerometer_setAccelerationChangeTrigger(self.handle, c_int(index), c_double(sensitivity))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def __nativeAccelerationChangeEvent(self, handle, usrptr, index, value):
        if self.__accelChange != None:
            self.__accelChange(AccelerationChangeEventArgs(self, index, value))
        return 0

    def setOnAccelerationChangeHandler(self, accelChangeHandler):
        """Sets the acceleration change event handler.
        
        The acceleration change handler is a method that will be called when the acceleration of an axis has changed by at least the ChangeTrigger that has been set for that axis.
        
        Parameters:
            accelChangeHandler: hook to the accelChangeHandler callback function.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException
        """
        if accelChangeHandler == None:
            self.__accelChange = None
            self.__onAccelChange = None
        else:
            self.__accelChange = accelChangeHandler
            self.__onAccelChange = self.__ACCELCHANGEHANDLER(self.__nativeAccelerationChangeEvent)
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetAccelerometer_set_OnAccelerationChange_Handler(self.handle, self.__onAccelChange, None)
        except RuntimeError:
            self.__accelChange = None
            self.__onAccelChange = None
            raise
        
        if result > 0:
            raise PhidgetException(result)
