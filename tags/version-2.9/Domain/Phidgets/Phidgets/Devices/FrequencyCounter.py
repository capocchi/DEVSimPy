"""Copyright 2012 Phidgets Inc.
This work is licensed under the Creative Commons Attribution 2.5 Canada License.
To view a copy of this license, visit http://creativecommons.org/licenses/by/2.5/ca/
"""

__author__="Adam Stelmack"
__version__="2.1.8"
__date__ ="12-Jan-2011 3:39:00 PM"

import ctypes
from ctypes import byref, c_double, c_int, c_void_p, c_longlong
import threading
import sys
from Phidgets.PhidgetLibrary import PhidgetLibrary
from Phidgets.Phidget import Phidget
from Phidgets.PhidgetException import PhidgetErrorCodes, PhidgetException
from Phidgets.Events.Events import FrequencyCounterCountEventArgs

class FilterType:
    FILTERTYPE_ZERO_CROSSING=1
    FILTERTYPE_LOGIC_LEVEL=2
    FILTERTYPE_UNKNOWN=3

class FrequencyCounter(Phidget):
    """This class represents a Phidget Frequency Counter Controller.

    All methods to control a Frequency Counter Controller are implemented in this class.

    See your device's User Guide for more specific API details, technical information, and revision details. 
	The User Guide, along with other resources, can be found on the product page for your device.

    Extends:
        Phidget
    """
    def __init__(self):
        """The Constructor Method for the FrequencyCounter Class

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
        """
        Phidget.__init__(self)

        self.__frequencyCountDelegate = None

        self.__onFrequencyCountHandlerHandler = None

        try:
            PhidgetLibrary.getDll().CPhidgetFrequencyCounter_create(byref(self.handle))
        except RuntimeError:
            raise

        if sys.platform == 'win32':
            self.__FREQUENCYCOUNTHANDLER = ctypes.WINFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_int, c_int)
        elif sys.platform == 'darwin' or sys.platform == 'linux2':
            self.__FREQUENCYCOUNTHANDLER = ctypes.CFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_int, c_int)

    def __del__(self):
        """The Destructor Method for the FrequencyCounter Class
        """
        Phidget.dispose(self)

    def getFrequencyInputCount(self):
        """Returns the number of frequency inputs.

        Current version of the Phidget Frequency Counter has 2 frequency inputs, future versions could have more or less.

        Returns:
            The number of available frequency inputs <int>.

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this phidget is not opened or attached.
        """
        inputCount = c_int()

        try:
            result = PhidgetLibrary.getDll().CPhidgetFrequencyCounter_getFrequencyInputCount(self.handle, byref(inputCount))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)
        else:
            return inputCount.value

    def getFrequency(self, index):
        """Gets the last calculated frequency on the specified channel, in Hz.
        This function will return 0 if The Timeout value elapses without detecting a signal.
        Frequency is recalculated up to 31.25 times a second, depending on the pulse rate.

        Parameters:
            index<int>: index of the frequency input channel

        Returns:
            The last calculated frequency on the specified input channel <double>.

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        frequency = c_double()

        try:
            result = PhidgetLibrary.getDll().CPhidgetFrequencyCounter_getFrequency(self.handle, c_int(index), byref(frequency))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)
        else:
            return frequency.value

    def getTotalTime(self, index):
        """Gets the total elapsed time since Phidget was opened, or since the last reset, in microseconds.
        This time corresponds to the TotalCount property.

        Parameters:
            index<int>: index of the frequency input channel

        Returns:
            The total elapsed time <long long>.

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        time = c_longlong()

        try:
            result = PhidgetLibrary.getDll().CPhidgetFrequencyCounter_getTotalTime(self.handle, c_int(index), byref(time))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)
        else:
            return time.value

    def getTotalCount(self, index):
        """Gets the total number of pulses detected on the specified channel since the Phidget was opened, or since the last reset.

        Parameters:
            index<int>: index of the frequency input channel

        Returns:
            The current number of pulses detected <long long>.

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        count = c_longlong()

        try:
            result = PhidgetLibrary.getDll().CPhidgetFrequencyCounter_getTotalCount(self.handle, c_int(index), byref(count))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)
        else:
            return count.value

    def __nativeFrequencyCountEvent(self, handle, usrptr, index, time, counts):
        if self.__frequencyCountDelegate != None:
            self.__frequencyCountDelegate(FrequencyCounterCountEventArgs(self, index, time, counts))
        return 0

    def setOnFrequencyCountHandler(self, frequencyCountHandler):
        """Set the Frequency Count Event Handler.

        The frequency count handler is a method that will be called when a frequency channel input on
        this FrequencyCounter has detected a count.This event will fire at up to 31.25 times a second,
        depending on the pulse rate. The time is in microseconds and represents the amount of time in which
        the number of counts occurred. This event can be used to calculate frequency independently of the phidget21
        library frequency implementation.

        This event will fire with a count of 0 once, after the Timeout time has elapsed with no counts for a channel, to indicate 0Hz.

        Parameters:
            frequencyCountHandler: hook to the frequencyCountHandler callback function.

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException
        """
        if frequencyCountHandler == None:
            self.__frequencyCountDelegate = None
            self.__onFrequencyCountHandler = None
        else:
            self.__frequencyCountDelegate = frequencyCountHandler
            self.__onFrequencyCountHandler = self.__FREQUENCYCOUNTHANDLER(self.__nativeFrequencyCountEvent)

        try:
            result = PhidgetLibrary.getDll().CPhidgetFrequencyCounter_set_OnCount_Handler(self.handle, self.__onFrequencyCountHandler, None)
        except RuntimeError:
            self.__frequencyCountDelegate = None
            self.__onFrequencyCountHandler = None
            raise

        if result > 0:
            raise PhidgetException(result)

    def getTimeout(self, index):
        """Gets the Timeout value, in microseconds.

        This value is used to set the time to wait without detecting a signal before reporting 0 Hz.
        The valid range in 0.1 - 100 seconds (100,000 - 100,000,000 microseconds).
        
        1/Timeout represents the lowest frequency that will be measurable.

        Parameters:
            index<int>: index of the frequency input channel

        Returns:
            The timeout value, in microseconds <int>.

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        timeout = c_int()

        try:
            result = PhidgetLibrary.getDll().CPhidgetFrequencyCounter_getTimeout(self.handle, c_int(index), byref(timeout))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)
        else:
            return timeout.value

    def setTimeout(self, index, timeout):
        """Set the Timeout value, in microseconds.

        This value is used to set the time to wait without detecting a signal before reporting 0 Hz.
        The valid range in 0.1 - 100 seconds (100,000 - 100,000,000 microseconds).

        1/Timeout represents the lowest frequency that will be measurable.
        
        Parameters:
            index<int>: index of the frequency input channel
            timeout<int>: the timeout value, in microseconds

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, if the index is out of range, or if the value provided for the timeout is out of range.
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetFrequencyCounter_setTimeout(self.handle, c_int(index), c_int(timeout))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)

    def getFilter(self, index):
        """Gets the channel filter mode.

        The controls the type of signal that the frequency counter will respond to - either a zero-centered signal, or a logic level signal.

        Parameters:
            index<int>: index of the frequency input channel

        Returns:
            The channel filter mode <int/FilterType>.

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        filterMode = c_int()

        try:
            result = PhidgetLibrary.getDll().CPhidgetFrequencyCounter_getFilter(self.handle, c_int(index), byref(filterMode))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)
        else:
            return filterMode.value

    def setFilter(self, index, filterMode):
        """Sets the channel filter mode.

        The controls the type of signal that the frequency counter will respond to - either a zero-centered signal, or a logic level signal.

        Parameters:
            index<int>: index of the frequency input channel
            filterMode<int>: the channel filter mode

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, if the index is out of range, or if the filter mode provided is invalid.
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetFrequencyCounter_setFilter(self.handle, c_int(index), c_int(filterMode))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)

    def getEnabled(self, index):
        """Gets the enabled state on the specified channel.

        When the channel is disabled, it will no longer register counts.
        TotalTime and TotalCount properties will not be incremented until the channel is re-enabled.

        Parameters:
            index<int>: index of the frequency input channel

        Returns:
            The enabled state of the specified channel <boolean>.

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        enabledState = c_int()

        try:
            result = PhidgetLibrary.getDll().CPhidgetFrequencyCounter_getEnabled(self.handle, c_int(index), byref(enabledState))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)
        else:
            if enabledState.value == 1:
                return True
            else:
                return False

    def setEnabled(self, index, enabledState):
        """Sets the enabled state on the specified channel.

        When the channel is disabled, it will no longer register counts.
        TotalTime and TotalCount properties will not be incremented until the channel is re-enabled.

        Parameters:
            index<int>: index of the frequency input channel

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        if enabledState == True:
            value = 1
        else:
            value = 0

        try:
            result = PhidgetLibrary.getDll().CPhidgetFrequencyCounter_setEnabled(self.handle, c_int(index), c_int(value))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)

    def reset(self, index):
        """Resets the TotalCount and TotalTime counters to 0 for the specified channel.

        For best performance, this should be called when the channel is disabled.

        Parameters:
            index<int>: index of the frequency input channel

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetFrequencyCounter_reset(self.handle, c_int(index))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)