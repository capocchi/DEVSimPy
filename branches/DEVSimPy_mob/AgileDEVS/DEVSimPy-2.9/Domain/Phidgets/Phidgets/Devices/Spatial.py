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
from Phidgets.Events.Events import SpatialDataEventArgs, AttachEventArgs
import sys

class CPhidget_Timestamp(Structure):
    _fields_ = [("seconds",c_int),("microSeconds",c_int)]

class CPhidgetSpatial_SpatialEventData(Structure):
    _fields_ = [("acceleration",c_double * 3),("angularRate",c_double * 3),("magneticField",c_double * 3),("timestamp",CPhidget_Timestamp)]

class TimeSpan:
    """This class represents a timespan corresponding to the tiomestamp for a set of spacial event data."""
    def __init__(self, seconds, microSeconds):
        """Creates a new TimeSpan object from the seconds and microseconds count from the timestamp of spatial event data.
        
        Parameters:
            seconds<int>: Number of seconds since PhidgetSpatial was opened.
            microSeconds<int>: Number of microseconds since last data event packet.
        """
        self.seconds = seconds
        """Number of seconds since PhidgetSpatial was opened."""
        self.microSeconds = microSeconds
        """Number of microseconds since last data event packet."""

class SpatialEventData:
    """This class represents a set of spatial data for a moment in time."""
    def __init__(self, data, numAccelAxes, numGyroAxes, numCompassAxes):
        """Creates a new SpatialEventData object from a data structure and the counts for the accelerometer, gyro, and compass axes.
        
        Parameters:
            data<CPhidgetSpatial_SpatialEventData>: The event data structre received from the event callback.
            numAccelAxes<int>: The number of accelerometer axes.
            numGyroAxes<int>: The number of gyro axes.
            numCompassAxes<int>: The number of compass axes.
        """
        self.Acceleration = []
        """Acceleration data."""
        
        self.AngularRate = []
        """Angular rate (gyro) data."""
        
        self.MagneticField = []
        """Magnetic field strength (compass) data."""
        
        for i in range(numAccelAxes):
            self.Acceleration.append(data.acceleration[i])
        for i in range(numGyroAxes):
            self.AngularRate.append(data.angularRate[i])
        for i in range(numCompassAxes):
            self.MagneticField.append(data.magneticField[i])
        
        self.Timestamp = TimeSpan(data.timestamp.seconds, data.timestamp.microSeconds);
        """Timestamp of when this data was taken.
        
        This timestamp starts at 0 when the Phidget is opened/attached.
        """

class Spatial(Phidget):
    """This class represents a Phidget Spatial. A Phidget Spatial has up to 3 accelerometer axes, up to 3 magnetometer axes, and up to 3 gyroscope axes.
	
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
        
        self.__numAccelAxes = 0;
        self.__numGyroAxes = 0;
        self.__numCompassAxes = 0;
        
        self.__attach = None
        self.__spatialData = None;
        
        self.__onAttach = None
        self.__onSpatialData = None;
        
        try:
            PhidgetLibrary.getDll().CPhidgetSpatial_create(byref(self.handle))
        except RuntimeError:
            raise
        
        if sys.platform == 'win32':
            self.__ATTACHHANDLER = WINFUNCTYPE(c_int, c_void_p, c_void_p)
            self.__SPATIALDATAHANDLER = WINFUNCTYPE(c_int, c_void_p, c_void_p, POINTER(c_long), c_int)
        elif sys.platform == 'darwin' or sys.platform == 'linux2':
            self.__ATTACHHANDLER = CFUNCTYPE(c_int, c_void_p, c_void_p)
            self.__SPATIALDATAHANDLER = CFUNCTYPE(c_int, c_void_p, c_void_p, POINTER(c_long), c_int)

    def __del__(self):
        """The Destructor Method for the Spatial Class
        """
        Phidget.dispose(self)

    def getAccelerationAxisCount(self):
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
            result = PhidgetLibrary.getDll().CPhidgetSpatial_getAccelerationAxisCount(self.handle, byref(axisCount))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return axisCount.value

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
            result = PhidgetLibrary.getDll().CPhidgetSpatial_getAcceleration(self.handle, c_int(index), byref(value))
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
            result = PhidgetLibrary.getDll().CPhidgetSpatial_getAccelerationMax(self.handle, c_int(index), byref(value))
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
            result = PhidgetLibrary.getDll().CPhidgetSpatial_getAccelerationMin(self.handle, c_int(index), byref(value))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return value.value

    def getGyroAxisCount(self):
        """Returns the number of gyro axes.
        
        Currently all gyros provide three axes of angular rate - x, y, and z.
        
        Returns:
            The number of Available Axes <int>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this phidget is not opened or attached.
        """
        axisCount = c_int()
        try:
            result = PhidgetLibrary.getDll().CPhidgetSpatial_getGyroAxisCount(self.handle, byref(axisCount))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return axisCount.value

    def getAngularRate(self, index):
        """Gets the angular rate of rotation for this Gyro axis, in degrees per second.
        
        Parameters:
            index<int>: index of the axis.
        
        Returns:
            Angular rate of rotation for the selected gyro axis, in degrees per second. <double>
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        value = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetSpatial_getAngularRate(self.handle, c_int(index), byref(value))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return value.value

    def getAngularRateMax(self, index):
        """Gets the maximum supported angular rate for this gyro axis.
        
        Returns:
            The Maximum supported Angular Rate for this Gyro Axis. <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        value = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetSpatial_getAngularRateMax(self.handle, c_int(index), byref(value))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return value.value

    def getAngularRateMin(self, index):
        """Gets the minimum supported angular rate for this gyro axis.
        
        Returns:
            The Minimum supported Angular Rate for this gyro axis. <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        value = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetSpatial_getAngularRateMin(self.handle, c_int(index), byref(value))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return value.value

    def getCompassAxisCount(self):
        """Returns the number of compass axes.
        
        Currently all compass provide two or three axes of Magnetic field - x, y, and z.
        
        Returns:
            The number of Available Axes <int>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this phidget is not opened or attached.
        """
        axisCount = c_int()
        try:
            result = PhidgetLibrary.getDll().CPhidgetSpatial_getCompassAxisCount(self.handle, byref(axisCount))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return axisCount.value

    def getMagneticField(self, index):
        """Gets the current magnetic field stregth of an axis, in Gauss.
        
        Parameters:
            index<int>: index of the axis.
        
        Returns:
            The Magnetic Field strength for this compass axis, in Gauss. <double>
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        value = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetSpatial_getMagneticField(self.handle, c_int(index), byref(value))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return value.value

    def getMagneticFieldMax(self, index):
        """Gets the maximum magnetic field strength measurable by this compass axis.
        
        Returns:
            The Maximum measurable Magnetic Field strength for this Compass Axis. <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        value = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetSpatial_getMagneticFieldMax(self.handle, c_int(index), byref(value))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return value.value

    def getMagneticFieldMin(self, index):
        """Gets the minimum magnetic field strength measurable by this compass axis.
        
        Returns:
            The Minimum measurable Magnetic Field strength for this compass axis. <double>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        value = c_double()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetSpatial_getMagneticFieldMin(self.handle, c_int(index), byref(value))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return value.value

    def zeroGyro(self):
        """Zeroes the gyro.
        
        This takes 1-2 seconds to complete and should only be called when the board is stationary.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the Phidget does not have a gyro.
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetSpatial_zeroGyro(self.handle)
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def getDataRate(self):
        """Gets the event data rate in ms.
        
        Data rate needs to be between DataRateMin and DataRateMax.
        
        Returns:
            The current event data rate, in ms. <int>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        dataRate = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetSpatial_getDataRate(self.handle, byref(dataRate))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return dataRate.value
        
    def setDataRate(self, value):
        """Sets the event data rate in ms.
        
        Data rate needs to be between DataRateMin and DataRateMax.
        
        Parameters:
            value<int>: The desired event data rate value, in ms.
            
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or the data rate is out of range.
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetSpatial_setDataRate(self.handle, c_int(value))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def getDataRateMax(self):
        """Gets the maximum supported data rate in ms.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        dataRateMax = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetSpatial_getDataRateMax(self.handle, byref(dataRateMax))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return dataRateMax.value

    def getDataRateMin(self):
        """Gets the minimum supported data rate in ms.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        dataRateMin = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetSpatial_getDataRateMin(self.handle, byref(dataRateMin))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return dataRateMin.value

    def setCompassCorrectionParameters(self, magField, offset0, offset1, offset2, gain0, gain1, gain2, T0, T1, T2, T3, T4, T5):
        """Sets correction paramaters for the magnetometer triad. This is for filtering out hard and soft iron offsets, and scaling the output to match the local field strength.
        
        These parameters can be obtained from the compass calibration program provided by Phidgets Inc.
        
        Parameters:
            magField<double>: Local magnetic field strength.
            offset0<double>: Axis 0 offset correction.
            offset1<double>: Axis 1 offset correction.
            offset2<double>: Axis 2 offset correction.
            gain0<double>: Axis 0 gain correction.
            gain1<double>: Axis 1 gain correction.
            gain2<double>: Axis 2 gain correction.
            T0<double>: Non-orthogonality correction factor 0.
            T1<double>: Non-orthogonality correction factor 1.
            T2<double>: Non-orthogonality correction factor 2.
            T3<double>: Non-orthogonality correction factor 3.
            T4<double>: Non-orthogonality correction factor 4.
            T5<double>: Non-orthogonality correction factor 5.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetSpatial_setCompassCorrectionParameters(self.handle, c_double(magField), c_double(offset0), c_double(offset1), c_double(offset2), c_double(gain0), c_double(gain1), c_double(gain2), c_double(T0), c_double(T1), c_double(T2), c_double(T3), c_double(T4), c_double(T5))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def resetCompassCorrectionParameters(self):
        """Resets correction paramaters for the magnetometer triad. This returns magnetometer output to raw magnetic field strength.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetSpatial_resetCompassCorrectionParameters(self.handle)
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def __nativeSpatialDataEvent(self, handle, usrptr, data, count):
        spatialDataCollection = []
        for i in range(count):
            data2 = cast(data[i], POINTER(CPhidgetSpatial_SpatialEventData))
            if data2[0].acceleration[0] == 1e300:
                arg0 = 0
            else:
                arg0 = self.__numAccelAxes
            if data2[0].angularRate[0] == 1e300:
                arg1 = 0
            else:
                arg1 = self.__numGyroAxes
            if data2[0].magneticField[0] == 1e300:
                arg2 = 0
            else:
                arg2 = self.__numCompassAxes
            
            spatialDataCollection.append(SpatialEventData(data2[0], arg0, arg1, arg2))
        
        if self.__spatialData != None:
            self.__spatialData(SpatialDataEventArgs(self, spatialDataCollection))
        return 0

    def setOnSpatialDataHandler(self, spatialDataHandler):
        """Sets the spatial data event handler.
        
        Contains data for acceleration/gyro/compass depending on what the board supports, as well as a timestamp.
        This event is fired at a fixed rate as determined by the DataRate property.
        
        Parameters:
            spatialDataHandler: hook to the spatialDataHandler callback function.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException
        """
        if spatialDataHandler == None:
            self.__spatialData = None
            self.__onSpatialData = None
        else:
            self.__spatialData = spatialDataHandler
            self.__onSpatialData = self.__SPATIALDATAHANDLER(self.__nativeSpatialDataEvent)
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetSpatial_set_OnSpatialData_Handler(self.handle, self.__onSpatialData, None)
        except RuntimeError:
            self.__spatialData = None
            self.__onSpatialData = None
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def __nativeAttachEvent(self, handle, usrptr):
        self.__numAccelAxes = self.getAccelerationAxisCount()
        self.__numGyroAxes = self.getGyroAxisCount()
        self.__numCompassAxes = self.getCompassAxisCount()
        
        if self.__attach != None:
            self.__attach(AttachEventArgs(self))
        return 0
    
    def setOnAttachHandler(self, attachHandler):
        """Sets the Attach Event Handler.
        
        The attach handler is a method that will be called when this Phidget is physically attached to the system, and has gone through its initalization, and so is ready to be used.
        
        This is an 'overloaded' version for the spacial object as we needed to perform a few more actions in the native event in order to load and store the number of axes so we didn't have to poll for it all the time.
        
        Parameters:
            attachHandler: hook to the attachHandler callback function
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened.
        """
        if attachHandler == None:
            self.__attach = None
            self.__onAttach = None
        else:
            self.__attach = attachHandler
            self.__onAttach = self.__ATTACHHANDLER(self.__nativeAttachEvent)
        
        try:
            result = PhidgetLibrary.getDll().CPhidget_set_OnAttach_Handler(self.handle, self.__onAttach, None)
        except RuntimeError:
            self.__attach = None
            self.__onAttach = None
            raise
        
        if result > 0:
            raise PhidgetException(result)
