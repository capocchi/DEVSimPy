"""Copyright 2010 Phidgets Inc.
This work is licensed under the Creative Commons Attribution 2.5 Canada License. 
To view a copy of this license, visit http://creativecommons.org/licenses/by/2.5/ca/
"""

__author__ = 'Adam Stelmack'
__version__ = '2.1.8'
__date__ = 'May 17 2010'

from Phidgets.Common import prepOutput
import threading
from ctypes import *
import Phidgets.Common
import sys

class PhidgetException(Exception):
    """This class represents Phidget related exceptions.
    
    All Phidget exceptions originate in the phidget21 C library.
    These exceptions can be thrown by most function in the library and cover such things as trying to access a Phidget before opening it,
    or before it is attached and ready to use, out of bounds Index and data values,
    trying to read data that isn't available, and other less common problems.
    
    Extends:
        Exception
    """
    def __init__(self, code):
        if sys.platform == 'win32':
            self.dll = windll.LoadLibrary("phidget21.dll")
        elif sys.platform == 'darwin':
            self.dll = cdll.LoadLibrary("/Library/Frameworks/Phidget21.framework/Versions/Current/Phidget21")
        elif sys.platform == 'linux2':
            self.dll = cdll.LoadLibrary("libphidget21.so.0")
        else:
            self.dll = None
            print("Platform not supported")
        
        if(self.dll != None):
            self.code = code
            description = c_char_p()
            result = self.dll.CPhidget_getErrorDescription(c_int(code), byref(description))
            self.details = prepOutput(description)
    
    @staticmethod
    def getErrorDescription(self, code):
        """
        """
        description = c_char_p()
        
        try:
            result = self.dll.CPhidget_getErrorDescription(c_int(code), byref(description))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return prepOutput(description)

class PhidgetErrorCodes:
    PHIDGET_ERROR_CODE_COUNT = 20
    """
    This is an enumeration that references a textual representation of an error type to its corresponding
    error code.
    """
    EPHIDGET_OK=0
    """This status code is returned if everything is ok
    """
    EPHIDGET_NOTFOUND=1
    """Phidget not found exception.
    
    "A Phidget matching the type and or serial number could not be found."
    This exception is not currently used externally.
    """
    EPHIDGET_NOMEMORY=2
    """No memory exception.
    
    "Memory could not be allocated."
    This exception is thrown when a memory allocation (malloc) call fails in the c library.
    """
    EPHIDGET_UNEXPECTED=3
    """Unexpected exception.
    
    "Unexpected Error. Contact Phidgets Inc. for support."
    This exception is thrown when something unexpected happens (more enexpected then another exception).
    This generally points to a bug or bad code in the C library, and hopefully won't even be seen.
    """
    EPHIDGET_INVALIDARG=4
    """Invalid argument exception.
    
    "Invalid argument passed to function."
    This exception is thrown whenever a function recieves an unexpected null pointer, or a value that is out of range.
    ie setting a motor's speed to 101 when the maximum is 100.
    """
    EPHIDGET_NOTATTACHED=5
    """Phidget not attached exception.
    
    "Phidget not physically attached."
    This exception is thrown when a method is called on a device that is not attached, and the method requires the device to be attached.
    ie trying to read the serial number, or the state of an ouput.
    """
    EPHIDGET_INTERRUPTED=6
    """Interrupted exception.
    
    "Read/Write operation was interrupted."
    This exception is not currently used externally.
    """
    EPHIDGET_INVALID=7
    """Invalid error exception.
    
    "The Error Code is not defined."
    This exception is thrown when trying to get the string description of an undefined error code.
    This should not be seen in Python.
    """
    EPHIDGET_NETWORK=8
    """Network exception.
    
    "Network Error."
    This exception is usually only seen in the Error event.
    It will generally be accompanied by a specific Description of the network problem.
    """
    EPHIDGET_UNKNOWNVAL=9
    """Value unknown exception.
    
    "Value is Unknown (State not yet received from device, or not yet set by user)."
    This exception is thrown when a device that is set to unknow is read.
    ie trying to read the position of a servo before setting it's position.
    
    Every effort is made in the library to fill in as much of a device's state before the attach event gets thrown,
    however, many there are some states that cannot be filled in automatically.
    ie older interface kits do not return their output states, and so these will be unknown until they are set.
    
    This is a quite common exception for some devices, and so should always be caught.
    """
    EPHIDGET_BADPASSWORD=10
    """Authorization exception.
    
    "Authorization Failed."
    This exception is thrown in the Error event.
    It means that a connection could not be authenticated because of a passwrod missmatch.
    """
    EPHIDGET_UNSUPPORTED=11
    """Unsupported exception.
    
    "Not Supported."
    This exception is thrown when a method is called that is not supported, either by that device, or by the system.
    ie calling setRatiometric on an interfaceKit that does not have sensors.
    
    This is also used for methods that are not yet complete, ie setLabel on Windows.
    """
    EPHIDGET_DUPLICATE=12
    """Duplicate request exception.
    
    "Duplicated request."
    This exception is thrown when open is called twice on a device, without calling close in between.
    The second call to open is ignored.
    """
    EPHIDGET_TIMEOUT=13
    """Timeout exception.
    
    "Given timeout has been exceeded."
    This exception is thrown by waitForAttachment(int) if the provided timeout expires before an attach happens.
    This may also be thrown by a device set request, if the set times out - though this should not happen,
    and would generally mean a problem with the device.
    """
    EPHIDGET_OUTOFBOUNDS=14
    """Out of bounds exception.
    
    "Index out of Bounds."
    This exception is thrown anytime an indexed set or get method is called with an out of bounds index.
    """
    EPHIDGET_EVENT=15
    """Event exception.
    
    "A non-null error code was returned from an event handler."
    This exception is not currently used.
    """
    EPHIDGET_NETWORK_NOTCONNECTED=16
    """Network not connected exception.
    
    "A connection to the server does not exist."
    This exception is thrown when a network specific method is called on a device
    that was opened remotely, but there is no connection to a server. ie getServerID.
    """
    EPHIDGET_WRONGDEVICE=17
    """Wrong device exception.
    
    "Function is not applicable for this device."
    This exception is thrown when a method from device is called by another device.
    ie casting an InterfaceKit to a Servo and calling setPosition.
    """
    PHIDGET_ERR_CLOSED=18
    """Phidget closed exception.
    
    "Phidget handle was closed."
    This exception is thrown when waitForAttachment is called on a Phidget that has not been opened, or was closed.
    """
    PHIDGET_ERR_BADVERSION=19
    """Version mismatch exception.
    
    "Webservice and Client protocol versions don't match. Update to newest release."
    """
    
    PHIDGET_ERREVENT_CODE_COUNT=10
    PHIDGET_ERREVENT_NETWORK=0x8001
    PHIDGET_ERREVENT_BADPASSWORD=0x8002
    PHIDGET_ERREVENT_BADVERSION=0x8003
    PHIDGET_ERREVENT_OVERRUN=0x9002
    PHIDGET_ERREVENT_PACKETLOST=0x9003
    PHIDGET_ERREVENT_WRAP=0x9004
    PHIDGET_ERREVENT_OVERTEMP=0x9005
    PHIDGET_ERREVENT_OVERCURRENT=0x9006
    PHIDGET_ERREVENT_OUTOFRANGE=0x9007
    PHIDGET_ERREVENT_BADPOWER=0x9008