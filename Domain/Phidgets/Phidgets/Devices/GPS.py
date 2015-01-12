"""Copyright 2012 Phidgets Inc.
This work is licensed under the Creative Commons Attribution 2.5 Canada License.
To view a copy of this license, visit http://creativecommons.org/licenses/by/2.5/ca/
"""

__author__="Adam Stelmack"
__version__="2.1.8"
__date__ ="13-Jan-2011 12:29:34 PM"

import ctypes
from ctypes import byref, c_int, c_double, c_void_p, c_short, Structure
import threading
import sys
from Phidgets.PhidgetLibrary import PhidgetLibrary
from Phidgets.Phidget import Phidget
from Phidgets.PhidgetException import PhidgetException
from Phidgets.Events.Events import GPSPositionChangeEventArgs, GPSPositionFixStatusChangeEventArgs

class CPhidgetGPS_GPSTime(Structure):
    _fields_ = [("tm_ms",c_short),
                ("tm_sec",c_short),
                ("tm_min",c_short),
                ("tm_hour",c_short)]

class GPSTime:
    def __init__(self, GPSTime_struct):
        self.ms = GPSTime_struct.tm_ms
        self.sec = GPSTime_struct.tm_sec
        self.min = GPSTime_struct.tm_min
        self.hour = GPSTime_struct.tm_hour

    def toCPhidgetGPS_GPSTime(self):
        gpsTime = CPhidgetGPS_GPSTime()

        gpsTime.tm_ms = self.ms
        gpsTime.tm_sec = self.sec
        gpsTime.tm_min = self.min
        gpsTime.tm_hour = self.hour

        return gpsTime

    def toString(self):
        return str(self.hour).zfill(2)+":"+str(self.min).zfill(2)+":"+str(self.sec).zfill(2)+"."+str(self.ms).zfill(3)

class CPhidgetGPS_GPSDate(Structure):
    _fields_ = [("tm_mday",c_short),
                  ("tm_mon",c_short),
                  ("tm_year",c_short)]

class GPSDate:
    def __init__(self, GPSDate_struct):
        self.day = GPSDate_struct.tm_mday
        self.month = GPSDate_struct.tm_mon
        self.year = GPSDate_struct.tm_year

    def toCPhidgetGPS_GPSDate(self):
        gpsDate = CPhidgetGPS_GPSDate()

        gpsDate.tm_mday = self.day
        gpsDate.tm_mon = self.month
        gpsDate.tm_year = self.year

        return gpsDate

    def toString(self):
        return str(self.day).zfill(2)+"/"+str(self.month).zfill(2)+"/"+str(self.year).zfill(4)

class GPS(Phidget):
    """This class represents a Phidget GPS.

    All methods to control a GPS are implemented in this class.

    See your device's User Guide for more specific API details, technical information, and revision details. 
	The User Guide, along with other resources, can be found on the product page for your device.

    Extends:
        Phidget
    """
    def __init__(self):
        """The Constructor Method for the GPS Class

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
        """
        Phidget.__init__(self)

        self.__positionChangeDelegate = None;
        self.__positionFixStatusChangeDelegate = None;

        self.__onPositionChangeHandler = None;
        self.__onPositionFixStatusChangeHandler = None;

        try:
            PhidgetLibrary.getDll().CPhidgetGPS_create(byref(self.handle))
        except RuntimeError:
            raise

        if sys.platform == 'win32':
            self.__POSITIONCHANGEHANDLER = ctypes.WINFUNCTYPE(c_int, c_void_p, c_void_p, c_double, c_double, c_double)
            self.__POSITIONFIXSTATUSCHANGEHANDLER = ctypes.WINFUNCTYPE(c_int, c_void_p, c_void_p, c_int)
        elif sys.platform == 'darwin' or sys.platform == 'linux2':
            self.__POSITIONCHANGEHANDLER = ctypes.CFUNCTYPE(c_int, c_void_p, c_void_p, c_double, c_double, c_double)
            self.__POSITIONFIXSTATUSCHANGEHANDLER = ctypes.CFUNCTYPE(c_int, c_void_p, c_void_p, c_int)

    def __del__(self):
        """The Destructor Method for the GPS Class
        """
        Phidget.dispose(self)

    def getLatitude(self):
        """Returns the current latitude of the active antenna in signed decimal degree format.

        Returns:
            The current latitude of the active antenna in signed decimal degree format <double>.

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this phidget is not opened or attached.
        """
        latitude = c_double()

        try:
            result = PhidgetLibrary.getDll().CPhidgetGPS_getLatitude(self.handle, byref(latitude))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)
        else:
            return latitude.value

    def getLongitude(self):
        """Returns the current longitude of the active antenna in signed decimal degree format.

        Returns:
            The current longitude of the active antenna in signed decimal degree format <double>.

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this phidget is not opened or attached.
        """
        longitude = c_double()

        try:
            result = PhidgetLibrary.getDll().CPhidgetGPS_getLongitude(self.handle, byref(longitude))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)
        else:
            return longitude.value

    def getAltitude(self):
        """Returns the current altitude of the active antenna from mean sea level(geoid), ranges from -9999.9 to 17999.9.

        Units are in meters.

        Returns:
            The current altitude of the active antenna in meters <double>.

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this phidget is not opened or attached.
        """
        altitude = c_double()

        try:
            result = PhidgetLibrary.getDll().CPhidgetGPS_getAltitude(self.handle, byref(altitude))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)
        else:
            return altitude.value

    def getHeading(self):
        """Returns the current true course over ground of the active antenna in degrees (000.0 - 359.9).

        000.0 indicates True North, 180.0 indicates True South.

        Returns:
            The current true course over ground of the active antenna <double>.

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this phidget is not opened or attached.
        """
        heading = c_double()

        try:
            result = PhidgetLibrary.getDll().CPhidgetGPS_getHeading(self.handle, byref(heading))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)
        else:
            return heading.value

    def getVelocity(self):
        """Returns the current speed over ground of the active antenna in km/h.

        Has a maximum value of 1800.0.

        Returns:
            The current speed over ground of the active antenna in km/h <double>.

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this phidget is not opened or attached.
        """
        velocity = c_double()

        try:
            result = PhidgetLibrary.getDll().CPhidgetGPS_getVelocity(self.handle, byref(velocity))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)
        else:
            return velocity.value

    def getTime(self):
        """Returns the current time as transmitted by the GPS receiver.

        Time is in UTC format.

        Returns:
            The current time as transmitted by the GPS receiver <GPSTime>.

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this phidget is not opened or attached.
        """
        time = CPhidgetGPS_GPSTime()

        try:
            result = PhidgetLibrary.getDll().CPhidgetGPS_getTime(self.handle, byref(time))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)
        else:
            return GPSTime(time)

    def getDate(self):
        """Returns the date of the last received position.

        Returns:
            The current date of the last received position <GPSDate>.

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this phidget is not opened or attached.
        """
        date = CPhidgetGPS_GPSDate()

        try:
            result = PhidgetLibrary.getDll().CPhidgetGPS_getDate(self.handle, byref(date))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)
        else:
            return GPSDate(date)

    def getPositionFixStatus(self):
        """

        """
        positionFixStatus = c_int()

        try:
            result = PhidgetLibrary.getDll().CPhidgetGPS_getPositionFixStatus(self.handle, byref(positionFixStatus))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)
        else:
            if positionFixStatus.value == 1:
                return True
            else:
                return False

    def __nativePositionChangeEvent(self, handle, usrptr, latitude, longitude, altitude):
        if self.__positionChangeDelegate != None:
            self.__positionChangeDelegate(GPSPositionChangeEventArgs(self, latitude, longitude, altitude))
        return 0

    def setOnPositionChangeHandler(self, positionChangeHandler):
        """Set the GPS Positon Change Event Handler.

        An event that is issued whenever a change in position occurs. Event arguments are latitude, longitude, altitude.

        Parameters:
            positionChangeHandler: hook to the positionChangeHandler callback function.

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException
        """
        if positionChangeHandler == None:
            self.__positionChangeDelegate = None
            self.__onPositionChangeHandler = None
        else:
            self.__positionChangeDelegate = positionChangeHandler
            self.__onPositionChangeHandler = self.__POSITIONCHANGEHANDLER(self.__nativePositionChangeEvent)

        try:
            result = PhidgetLibrary.getDll().CPhidgetGPS_set_OnPositionChange_Handler(self.handle, self.__onPositionChangeHandler, None)
        except RuntimeError:
            self.__positionChangeDelegate = None
            self.__onPositionChangeHandler = None
            raise

        if result > 0:
            raise PhidgetException(result)

    def __nativePositionFixStatusChangeEvent(self, handle, usrptr, status):
        if self.__positionFixStatusChangeDelegate != None:
            self.__positionFixStatusChangeDelegate(GPSPositionFixStatusChangeEventArgs(self, status))
        return 0

    def setOnPositionFixStatusChangeHandler(self, positionFixStatusChangeHandler):
        """Set the GPS Position Fix Status Change Event Handler.

        An event that is issued when a position fix is obtained or lost. The event argument can be used to inform you whether or not you are getting a signal.

        Parameters:
            positionFixStatusChangeHandler: hook to the positionFixStatusChangeHandler callback function.

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException
        """
        if positionFixStatusChangeHandler == None:
            self.__positionFixStatusChangeDelegate = None
            self.__onPositionFixStatusChangeHandler = None
        else:
            self.__positionFixStatusChangeDelegate = positionFixStatusChangeHandler
            self.__onPositionFixStatusChangeHandler = self.__POSITIONFIXSTATUSCHANGEHANDLER(self.__nativePositionFixStatusChangeEvent)

        try:
            result = PhidgetLibrary.getDll().CPhidgetGPS_set_OnPositionFixStatusChange_Handler(self.handle, self.__onPositionFixStatusChangeHandler, None)
        except RuntimeError:
            self.__positionFixStatusChangeDelegate = None
            self.__onPositionFixStatusChangeHandler = None
            raise

        if result > 0:
            raise PhidgetException(result)