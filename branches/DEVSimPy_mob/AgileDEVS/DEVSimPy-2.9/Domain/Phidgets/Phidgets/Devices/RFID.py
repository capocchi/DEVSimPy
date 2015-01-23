"""Copyright 2012 Phidgets Inc.
This work is licensed under the Creative Commons Attribution 2.5 Canada License. 
To view a copy of this license, visit http://creativecommons.org/licenses/by/2.5/ca/
"""

__author__ = 'Adam Stelmack'
__version__ = '2.1.8'
__date__ = 'May 17 2010'

import threading
from ctypes import *
from Phidgets.Common import prepOutput
from Phidgets.PhidgetLibrary import PhidgetLibrary
from Phidgets.Phidget import Phidget
from Phidgets.PhidgetException import PhidgetErrorCodes, PhidgetException
from Phidgets.Events.Events import OutputChangeEventArgs, TagEventArgs
import sys

class RFIDTagProtocol:
    """This is an enumeration of Tag Protocols and their values.
    """
    PHIDGET_RFID_PROTOCOL_EM4100 = 1
    PHIDGET_RFID_PROTOCOL_ISO11785_FDX_B = 2
    PHIDGET_RFID_PROTOCOL_PHIDGETS = 3

class RFID(Phidget):
    """This class represents a Phidget RFID Reader.
    
    All methods to read tags and set outputs on the RFID reader are implemented in this class.
    
    The Phidget RFID reader can read one tag at a time. Both tag and tagloss event handlers are provided,
    as well as control over the antenna so that multiple readers can exists in close proximity without interference.
	
	See your device's User Guide for more specific API details, technical information, and revision details. 
	The User Guide, along with other resources, can be found on the product page for your device.
    
    Extends:
        Phidget
    """
    def __init__(self):
        """The Constructor Method for the RFID Class
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
        """
        Phidget.__init__(self)
        
        self.__outputChange = None
        self.__tagGain = None
        self.__tagLoss = None
        
        self.__onTagHandler = None
        self.__onTagLostHandler = None
        self.__onOutputChange = None
        
        try:
            PhidgetLibrary.getDll().CPhidgetRFID_create(byref(self.handle))
        except RuntimeError:
            raise
        
        if sys.platform == 'win32':
            self.__OUTPUTCHANGEHANDLER = WINFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_int)
            self.__TAG2HANDLER = WINFUNCTYPE(c_int, c_void_p, c_void_p, c_char_p, c_int)
            self.__TAGLOST2HANDLER = WINFUNCTYPE(c_int, c_void_p, c_void_p, c_char_p, c_int)
        elif sys.platform == 'darwin' or sys.platform == 'linux2':
            self.__OUTPUTCHANGEHANDLER = CFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_int)
            self.__TAG2HANDLER = CFUNCTYPE(c_int, c_void_p, c_void_p, c_char_p, c_int)
            self.__TAGLOST2HANDLER = CFUNCTYPE(c_int, c_void_p, c_void_p, c_char_p, c_int)

    def __del__(self):
        """The Destructor Method for the RFID Class
        """
        Phidget.dispose(self)

    def getOutputCount(self):
        """Returns the number of outputs.
        
        These are the outputs provided by the terminal block. Older RFID readers do not have these outputs, and this method will return 0.
        
        Returns:
            The number of outputs available <int>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        outputCount = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetRFID_getOutputCount(self.handle, byref(outputCount))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return outputCount.value

    def getOutputState(self, index):
        """Returns the state of an output.
        
        True indicated activated, False deactivated, which is the default.
        
        Parameters:
            index<int>: index of the output.
        
        Returns:
            The state of the output <boolean>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, of the index is out of range.
        """
        outputState = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetRFID_getOutputState(self.handle, c_int(index), byref(outputState))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            if outputState.value == 1:
                return True
            else:
                return False

    def setOutputState(self, index, state):
        """Sets the state of a digital output.
        
        True indicated activated, False deactivated, which is the default.
        
        Parameters:
            index<int>: the index of the output.
            state<boolean>: the state of the output.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or the index or state value are out of range.
        """
        if state == True:
            value = 1
        else:
            value = 0
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetRFID_setOutputState(self.handle, c_int(index), c_int(value))
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
        
        The output change handler is a method that will be called when an output has changed.
        
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
            result = PhidgetLibrary.getDll().CPhidgetRFID_set_OnOutputChange_Handler(self.handle, self.__onOutputChange, None)
        except RuntimeError:
            self.__outputChange = None
            self.__onOutputChange = None
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def getAntennaOn(self):
        """Returns the state of the antenna.
        
        True indicated that the antenna is active, False indicated inactive.
        
        Returns:
            The state of the antenna <boolean>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        antenna = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetRFID_getAntennaOn(self.handle, byref(antenna))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            if antenna.value == 1:
                return True
            else:
                return False

    def setAntennaOn(self, state):
        """Sets the state of the antenna.
        
        True turns the antenna on, False turns it off.
        The antenna if by default turned off, and needs to be explicitely activated before tags can be read.
        
        Control over the antenna allows multiple readers to be used in close proximity, as multiple readers will
        interfere with each other if their antenna's are activated simultaneously.
        
        Parameters:
            state<boolean>: desired state of the antenna.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the desired state is out of range.
        """
        if state == True:
            value = 1
        else:
            value = 0
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetRFID_setAntennaOn(self.handle, c_int(value))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def getLEDOn(self):
        """Returns the state of the onboard LED.
        
        This LED is by default turned off.
        
        Returns:
            The state of the LED <boolean>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        ledStatus = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetRFID_getLEDOn(self.handle, byref(ledStatus))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            if ledStatus.value == 1:
                return True
            else:
                return False

    def setLEDOn(self, state):
        """Sets the state of the onboard LED.
        
        True turns the LED on, False turns it off. The LED is by default turned off.
        
        Parameters:
            state<boolean>: the desired LED state.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the desired state value is out of range.
        """
        if state == True:
            value = 1
        else:
            value = 0
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetRFID_setLEDOn(self.handle, c_int(value))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def write(self, tagString, tagProtocol, lock=False):
        """writes data to a tag.
        
        Consult the product manual for details.
        
        Protocol should be one of: PHIDGET_RFID_PROTOCOL_EM4100, PHIDGET_RFID_PROTOCOL_ISO11785_FDX_B, PHIDGET_RFID_PROTOCOL_PHIDGETS.
        lock locks the tag from further writes.
        """
        if lock == True:
            value = 1
        else:
            value = 0
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetRFID_write(self.handle, c_char_p(tagString), c_int(tagProtocol), c_int(value))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def getLastTag(self):
        """Returns the last tag read.
        
        This method will only return a valid tag after a tag has been seen.
        This method can be used even after a tag has been removed from the reader.
        
        Returns:
            The last tag read <string>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        tagString = c_char_p()
        protocol = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetRFID_getLastTag2(self.handle, byref(tagString), byref(protocol))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return prepOutput(tagString)

    def getLastTagProtocol(self):
        """Returns the protocol of the last tag read.
        
        This method will only return a valid protocol after a tag has been seen.
        This method can be used even after a tag has been removed from the reader.
        
        Returns:
            The protocol of the last tag read <int>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        tagString = c_char_p()
        protocol = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetRFID_getLastTag2(self.handle, byref(tagString), byref(protocol))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return protocol.value

    def getTagStatus(self):
        """Returns the state of whether or not a tag is being read by the reader.
        
        True indicated that a tag is on (or near) the reader, False indicates that one is not.
        
        Returns:
            The tag read state <int>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        tagStatus = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetRFID_getTagStatus(self.handle, byref(tagStatus))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            if tagStatus.value == 1:
                return True
            else:
                return False

    def __nativeTagGainEvent(self, handle, usrptr, tagString, protocol):
        
        if self.__tagGain != None:
            self.__tagGain(TagEventArgs(self, tagString))
        return 0

    def setOnTagHandler(self, tagHandler):
        """Sets the Tag Gained Event Handler.
        
        The tag gained handler is a method that will be called when a new tag is seen by the reader.
        The event is only fired one time for a new tag, so the tag has to be removed and then replaced before another tag gained event will fire.
        
        Parameters:
            tagHandler: hook to the tagHandler callback function.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException
        """
        if tagHandler == None:
            self.__tagGain = None
            self.__onTagHandler = None
        else:
            self.__tagGain = tagHandler
            self.__onTagHandler = self.__TAG2HANDLER(self.__nativeTagGainEvent)
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetRFID_set_OnTag2_Handler(self.handle, self.__onTagHandler, None)
        except RuntimeError:
            self.__tagGain = None
            self.__onTagHandler = None
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def __nativeTagLossEvent(self, handle, usrptr, tagString, protocol):
        
        if self.__tagLoss != None:
            self.__tagLoss(TagEventArgs(self, tagString))
        return 0

    def setOnTagLostHandler(self, tagLostHandler):
        """Sets the Tag Lost Event Handler.
        
        The tag lost handler is a method that will be called when a tag is removed from the reader.
        
        Parameters:
            tagLostHandler: hook to the tagLostHandler callback function.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException
        """
        if tagLostHandler == None:
            self.__tagLoss = None
            self.__onTagLostHandler = None
        else:
            self.__tagLoss = tagLostHandler
            self.__onTagLostHandler = self.__TAGLOST2HANDLER(self.__nativeTagLossEvent)
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetRFID_set_OnTagLost2_Handler(self.handle, self.__onTagLostHandler, None)
        except RuntimeError:
            self.__tagLoss = None
            self.__onTagLostHandler = None
            raise
        
        if result > 0:
            raise PhidgetException(result)
