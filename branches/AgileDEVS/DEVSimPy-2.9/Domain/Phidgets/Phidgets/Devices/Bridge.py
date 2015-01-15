"""Copyright 2012 Phidgets Inc.
This work is licensed under the Creative Commons Attribution 2.5 Canada License.
To view a copy of this license, visit http://creativecommons.org/licenses/by/2.5/ca/
"""

__author__="Adam Stelmack"
__version__="2.1.8"
__date__ ="12-Jan-2011 12:03:47 PM"

import ctypes
from ctypes import byref, c_double, c_int, c_void_p
import threading
import sys
from Phidgets.PhidgetLibrary import PhidgetLibrary
from Phidgets.Phidget import Phidget
from Phidgets.PhidgetException import PhidgetException
from Phidgets.Events.Events import BridgeDataEventArgs

class BridgeGain:
    PHIDGET_BRIDGE_GAIN_1=1
    PHIDGET_BRIDGE_GAIN_8=2
    PHIDGET_BRIDGE_GAIN_16=3
    PHIDGET_BRIDGE_GAIN_32=4
    PHIDGET_BRIDGE_GAIN_64=5
    PHIDGET_BRIDGE_GAIN_128=6
    PHIDGET_BRIDGE_GAIN_UNKNOWN=7

class Bridge(Phidget):
    """This class represents a Phidget Bridge Controller.

    All methods to control a Bridge Controller are implemented in this class.

    See your device's User Guide for more specific API details, technical information, and revision details. 
	The User Guide, along with other resources, can be found on the product page for your device.

    Extends:
        Phidget
    """
    def __init__(self):
        """The Constructor Method for the Bridge Class

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
        """
        Phidget.__init__(self)

        self.__bridgeDataDelegate = None

        self.__onBridgeDataHandler = None

        try:
            PhidgetLibrary.getDll().CPhidgetBridge_create(byref(self.handle))
        except RuntimeError:
            raise

        if sys.platform == 'win32':
            self.__BRIDGEDATAHANDLER = ctypes.WINFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_double)
        elif sys.platform == 'darwin' or sys.platform == 'linux2':
            self.__BRIDGEDATAHANDLER = ctypes.CFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_double)

    def __del__(self):
        """The Destructor Method for the Bridge Class
        """
        Phidget.dispose(self)

    def getInputCount(self):
        """Returns the number of Bridge inputs.

        Current version of the Phidget Bridge has 4 Bridge inputs, future versions could have more or less.

        Returns:
            The number of available Bridge inputs <int>.

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this phidget is not opened or attached.
        """
        inputCount = c_int()

        try:
            result = PhidgetLibrary.getDll().CPhidgetBridge_getInputCount(self.handle, byref(inputCount))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)
        else:
            return inputCount.value

    def getDataRateMax(self):
        """Returns the maximum supported data rate value that can be set, in ms.

        This is currently 8.

        Returns:
            The maximum supported data rate <int>

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        dataRateMax = c_int()

        try:
            result = PhidgetLibrary.getDll().CPhidgetBridge_getDataRateMax(self.handle, byref(dataRateMax))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)
        else:
            return dataRateMax.value

    def getDataRateMin(self):
        """Returns the minimum supported data rate value that can be set, in ms.

        This is currently 1000.

        Returns:
            The minimum supported data rate <int>

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        dataRateMin = c_int()

        try:
            result = PhidgetLibrary.getDll().CPhidgetBridge_getDataRateMin(self.handle, byref(dataRateMin))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)
        else:
            return dataRateMin.value

    def getDataRate(self):
        """Returns the maximum rate at which events will be fired, in ms.

        Data rate applies to all 4 bridges simultaneously. Setting a slower data rate will reduce noise at the cost of sample time.
        Also note that each bridge is being sampled only 1/4 of the time - this is probably ok for very stable signals, but for changing signals,
        it's probably best to set a higher sampling rate and do averaging in software.

        Data rate must be a multiple of 8ms. Trying to set something between multiples of 8 will cause an EPHIDGET_INVALIDARG exception to be thrown.
        
        Returns:
            The specified data rate (in milliseconds) <int>

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        dataRate = c_int()

        try:
            result = PhidgetLibrary.getDll().CPhidgetBridge_getDataRate(self.handle, byref(dataRate))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)
        else:
            return dataRate.value

    def setDataRate(self, dataRate):
        """Sets the maximum rate at which events will be fired, in ms.

        Data rate applies to all 4 bridges simultaneously. Setting a slower data rate will reduce noise at the cost of sample time.
        Also note that each bridge is being sampled only 1/4 of the time - this is probably ok for very stable signals, but for changing signals,
        it's probably best to set a higher sampling rate and do averaging in software.

        Data rate must be a multiple of 8ms. Trying to set something between multiples of 8 will cause an EPHIDGET_INVALIDARG exception to be thrown.

        Parameters:
            value<int>: The desired Data Rate Value.

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or the supplied data rate value is out of range.
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetBridge_setDataRate(self.handle, c_int(dataRate))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)

    def getGain(self, index):
        """Gets the gain for a selected bridge.

        Supported gains are 8, 16, 32, 64, 128, or no gain.
        Note that increasing the gains will reduce the measurable voltage difference by the gain factor, with +-1000mV/V being the maximum, with no gain.

        Parameters:
            index<int>: index of the Bridge input

        Returns:
            The currently set gain level for that Bridge input <int/BridgeGain>.

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        gain = c_int()

        try:
            result = PhidgetLibrary.getDll().CPhidgetBridge_getGain(self.handle, c_int(index), byref(gain))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)
        else:
            return gain.value

    def setGain(self, index, gain):
        """Sets the gain for a selected bridge.
        Supported gains are 8, 16, 32, 64, 128, or no gain.
        Note that increasing the gains will reduce the measurable voltage difference by the gain factor, with +-1000mV/V being the maximum, with no gain.

        Parameters:
            index<int>: index of the Bridge input
            gain<int/BridgeGain>: desired gain to set the input to

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, if the index is out of range, or if the gain specified is out of range.
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetBridge_setGain(self.handle, c_int(index), c_int(gain))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)
    
    def getBridgeMax(self, index):
        """Returns the maximum value that the selected Bridge can measure, in mV/V.

        This value will depend on the selected gain. At a gain of 1, BridgeMax == 1000mV/V.

        Parameters:
            index<int>: index of the Bridge input

        Returns:
            The minimum value that the selected Bridge can measure, in mV/V <double>.

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        bridgeMax = c_double()

        try:
            result = PhidgetLibrary.getDll().CPhidgetBridge_getBridgeMax(self.handle, c_int(index), byref(bridgeMax))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)
        else:
            return bridgeMax.value

    def getBridgeMin(self, index):
        """Returns the minimum value that the selected Bridge can measure, in mV/V.

        This value will depend on the selected gain. At a gain of 1, BridgeMin == -1000mV/V.

        Parameters:
            index<int>: index of the Bridge input

        Returns:
            The minimum value that the selected Bridge can measure, in mV/V <double>.

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        bridgeMin = c_double()

        try:
            result = PhidgetLibrary.getDll().CPhidgetBridge_getBridgeMin(self.handle, c_int(index), byref(bridgeMin))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)
        else:
            return bridgeMin.value

    def getBridgeValue(self, index):
        """Returns the value of the selected input, in mV/V.

        If the input is not enabled, this is throw an EPHIDGET_UNKNOWNVAL exception.
        If the bridge is saturated, this will be equal to BridgeMax or BridgeMin and an error event will be fired - in this case, gain should be reduced if possible.

        Parameters:
            index<int>: index of the Bridge input

        Returns:
            The currently value at that Bridge input, in mV/V <double>.

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, if the index is out of range, or if the value read is out of range
        """
        bridgeValue = c_double()

        try:
            result = PhidgetLibrary.getDll().CPhidgetBridge_getBridgeValue(self.handle, c_int(index), byref(bridgeValue))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)
        else:
            return bridgeValue.value

    def __nativeBridgeDataEvent(self, handle, usrptr, index, value):
        if self.__bridgeDataDelegate != None:
            self.__bridgeDataDelegate(BridgeDataEventArgs(self, index, value))
        return 0

    def setOnBridgeDataHandler(self, bridgeDataHandler):
        """Set the BridgeData Event Handler.

        The bridge data handler is a method that will be called when a Bridge input on
        this Bridge has received data.

        Parameters:
            bridgeDataHandler: hook to the bridgeDataHandler callback function.

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException
        """
        if bridgeDataHandler == None:
            self.__bridgeDataDelegate = None
            self.__onBridgeDataHandler = None
        else:
            self.__bridgeDataDelegate = bridgeDataHandler
            self.__onBridgeDataHandler = self.__BRIDGEDATAHANDLER(self.__nativeBridgeDataEvent)

        try:
            result = PhidgetLibrary.getDll().CPhidgetBridge_set_OnBridgeData_Handler(self.handle, self.__onBridgeDataHandler, None)
        except RuntimeError:
            self.__bridgeDataDelegate = None
            self.__onBridgeDataHandler = None
            raise

        if result > 0:
            raise PhidgetException(result)

    def getEnabled(self, index):
        """Gets the enabled state for the specified Bridge input index.

        This applies power between +5v and Ground and starts measuring the differential on the +/- pins.

        By default, all Bridges are disabled, and need to be explicitly enabled on startup.

        Parameters:
            index<int>: index of the Bridge input.

        Returns:
            The current enabled state of the specified Bridge input index <boolean>.

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is invalid.
        """
        enabledState = c_int()

        try:
            result = PhidgetLibrary.getDll().CPhidgetBridge_getEnabled(self.handle, c_int(index), byref(enabledState))
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
        """Sets the enabled state for an Bridge input.

        This applies power between +5v and Ground and starts measuring the differential on the +/- pins.

        By default, all Bridges are disabled, and need to be explicitly enabled on startup.

        Parameters:
            index<int>: Index of the Bridge input.
            enabledState<boolean>: State to set the enabled state of this Bridge input to.

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is out of range.
        """
        if enabledState == True:
            value = 1
        else:
            value = 0

        try:
            result = PhidgetLibrary.getDll().CPhidgetBridge_setEnabled(self.handle, c_int(index), c_int(value))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)