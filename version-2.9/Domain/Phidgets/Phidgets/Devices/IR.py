"""Copyright 20102 Phidgets Inc.
This work is licensed under the Creative Commons Attribution 2.5 Canada License. 
To view a copy of this license, visit http://creativecommons.org/licenses/by/2.5/ca/
"""

__author__ = 'Adam Stelmack'
__version__ = '2.1.8'
__date__ = 'May 10 2010'

import threading
from ctypes import *
from Phidgets.PhidgetLibrary import PhidgetLibrary
from Phidgets.Phidget import Phidget
from Phidgets.PhidgetException import PhidgetErrorCodes, PhidgetException
from Phidgets.Events.Events import IRCodeEventArgs, IRLearnEventArgs, IRRawDataEventArgs
import sys

IR_MAX_CODE_BIT_COUNT   = 128
IR_MAX_CODE_DATA_LENGTH = int(IR_MAX_CODE_BIT_COUNT / 8)
IR_MAX_REPEAT_LENGTH    = 26

class IRCode:
    """This class represents an IR Code.
    """
    def __init__(self, data, bitCount):
        """Creates a new IR Code from a string or from c_ubyte_Array.
        
        Parameters:
            data<string or c_ubyte_Array>: The IR code.
            bitCount<int>: The code length in bits.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException - If the length of the provided data is less than the expected length based on the provided bitCount
        """
        
        self.Data = None
        """IR Code Data
        
        This is MSB first, right justified.
        """
        
        self.BitCount = None
        """Data bits.
        
        This is important because many codes use a number of bits that doesn't line up with byte (8-bit) borders.
        """
        
        self.__hexLookup = (c_char*16)(b'0', b'1', b'2', b'3', b'4',
                b'5', b'6', b'7', b'8', b'9', b'A', b'B', b'C', b'D', b'E', b'F')
        
        if type(data).__name__ == 'str':
            self.Data = IR.HexToData(data)
            self.BitCount = bitCount
        elif type(data).__name__.find('c_ubyte_Array') != -1:
            if (bitCount % 8) > 0:
                length = int(bitCount / 8) + 1
            else:
                length = int(bitCount / 8) + 0
            
            if len(data) < length:
                raise PhidgetException(PhidgetErrorCodes.EPHIDGET_INVALIDARG)
            
            self.Data = []
            for i in range(length):
                self.Data.append(data[i])
            
            self.BitCount = bitCount
        elif type(data).__name__ == 'list':
            if (bitCount % 8) > 0:
                length = int(bitCount / 8) + 1
            else:
                length = int(bitCount / 8) + 0
            
            if len(data) < length:
                raise PhidgetException(PhidgetErrorCodes.EPHIDGET_INVALIDARG)
            
            self.Data = []
            for i in range(length):
                self.Data.append(data[i])
            
            self.BitCount = bitCount
    
    def toString(self):
        """String representation of the IR code.
        """
        str = ""
        for i in range(len(self.Data)):
            str += (self.__hexLookup[int(self.Data[i] / 16)]).decode()
            str += (self.__hexLookup[int(self.Data[i] % 16)]).decode()
        
        return str

class CPhidgetIR_CodeInfo(Structure):
    _fields_ = [("bitCount",c_int),
                ("encoding",c_int),
                ("length",c_int),
                ("gap",c_int),
                ("trail",c_int),
                ("header", c_int * 2),
                ("one",c_int * 2),
                ("zero",c_int * 2),
                ("repeat",c_int * IR_MAX_REPEAT_LENGTH),
                ("min_repeat",c_int),
                ("toggle_mask",c_ubyte * IR_MAX_CODE_DATA_LENGTH),
                ("carrierFrequency",c_int),
                ("dutyCycle",c_int)]

class IREncoding:
    """This is an enumeration of IR Encoding types and their values.
    """
    Unknown = 1
    Space = 2
    Pulse = 3
    BiPhase = 4
    RC5 = 5
    RC6 = 6
    
    @staticmethod
    def toString(val):
        if val == IREncoding.RC6:
            return "RC6"
        elif val == IREncoding.RC5:
            return "RC5"
        elif val == IREncoding.BiPhase:
            return "BiPhase"
        elif val == IREncoding.Pulse:
            return "Pulse"
        elif val == IREncoding.Space:
            return "Space"
        else:
            return "Unknown"

class IRCodeLength:
    """This is an enumeration of IR Code Length Types and their values.
    """
    Unknown = 1
    Constant = 2
    Variable = 3
    
    @staticmethod
    def toString(val):
        if val == IRCodeLength.Constant:
            return "Constant"
        elif val == IRCodeLength.Variable:
            return "Variable"
        else:
            return "Unknown"

class IRCodeInfo:
    """This class represents the encoding parameters needed to transmit a code.
    """
    def __init__(self, codeInfo=None):
        """The Constructor Method for the Accelerometer Class
        
        Sets the members to their defaults.  If a codeInfo structure is provided, will set the members to their values from the provided structure.
        
        Parameters:
            code<IRCode>: The learned code.
            codeInfo<IRCodeInfo>: The code encoding parameters.
        """
        #Defaults for Members
        self.Encoding = IREncoding.Unknown
        """Data Encoding.
        
        This defaults to Space encoding.
        """
        
        self.Length = IRCodeLength.Unknown
        """Code length.
        
        This defaults to Constant.
        """
        
        self.BitCount = 0
        """Code data length in bits."""
        
        self.Gap = 0
        """Gap length in us."""
        
        self.Trail = 0
        """Trailing pulse length in us."""
        
        self.Header = None #list of ints
        """Header data array in us."""
        
        self.One = [0, 0]
        """Pulse-Space encoding for a '1', in us."""
        
        self.Zero = [0, 0]
        """Pulse-Space encoding for a '0', in us."""
        
        self.MinRepeat = 1
        """Minimum number of times to repeat the code."""
        
        self.ToggleMask = None #IRCode
        """Mask of bits that should be toggled every time the code is sent.
        
        This is usually used in combination with MinRepeat.
        """
        
        self.Repeat = None #list of ints
        """Repeat code, in us."""
        
        self.CarrierFrequency = 38000
        """Carrier frequency"""
        
        self.DutyCycle = 33
        """Duty cycle."""
        #end Defaults
        
        if codeInfo != None:
            if (codeInfo.bitCount % 8) == 0:
                dataBytes = int(codeInfo.bitCount / 8) + 0
            else:
                dataBytes = int(codeInfo.bitCount / 8) + 1
            
            self.Encoding = codeInfo.encoding
            self.Length = codeInfo.length
            self.BitCount = codeInfo.bitCount
            self.Gap = codeInfo.gap
            self.Trail = codeInfo.trail
            
            
            if codeInfo.header[0] != 0:
                self.Header = [codeInfo.header[0], codeInfo.header[1]]
            else:
                self.Header = None
            
            self.Zero = [codeInfo.zero[0], codeInfo.zero[1]]
            self.One = [codeInfo.one[0], codeInfo.one[1]]
            
            self.MinRepeat = codeInfo.min_repeat
            self.CarrierFrequency = codeInfo.carrierFrequency
            self.DutyCycle = codeInfo.dutyCycle
            
            self.ToggleMask = IRCode(codeInfo.toggle_mask, codeInfo.bitCount)
            
            repCount = 0
            while codeInfo.repeat[repCount] != 0:
                repCount = repCount + 1
            
            if repCount > 0:
                self.Repeat = []
                for i in range(repCount):
                    self.Repeat.append(codeInfo.repeat[i])
            else:
                self.Repeat = None
    
    def toCPhidgetIR_CodeInfo(self):
        """
        """
        codeInfo = CPhidgetIR_CodeInfo()
        
        codeInfo.zero = (c_int * 2)(c_int(self.Zero[0]), c_int(self.Zero[1]))
        codeInfo.one = (c_int * 2)(c_int(self.One[0]), c_int(self.One[1]))
        
        codeInfo.header = (c_int * 2)()
        if self.Header != None:
            codeInfo.header[0] = c_int(self.Header[0])
            codeInfo.header[1] = c_int(self.Header[1])
        
        codeInfo.toggle_mask = (c_ubyte * IR_MAX_CODE_DATA_LENGTH)()
        if self.ToggleMask != None:
            if len(self.ToggleMask.Data) > IR_MAX_CODE_DATA_LENGTH:
                raise PhidgetException(PhidgetErrorCodes.EPHIDGET_OUTOFBOUNDS)
            else:
                for i in range(len(self.ToggleMask.Data)):
                    codeInfo.toggle_mask[i] = c_ubyte(self.ToggleMask.Data[i])
        
        codeInfo.repeat = (c_int * IR_MAX_REPEAT_LENGTH)()
        if self.Repeat != None:
            if len(self.Repeat) > IR_MAX_REPEAT_LENGTH:
                raise PhidgetException(PhidgetErrorCodes.EPHIDGET_OUTOFBOUNDS)
            else:
                for i in range(len(self.Repeat)):
                    codeInfo.repeat[i] = c_int(self.Repeat[i])
        
        codeInfo.carrierFrequency = self.CarrierFrequency
        codeInfo.bitCount = self.BitCount
        codeInfo.dutyCycle = self.DutyCycle
        codeInfo.encoding = self.Encoding
        codeInfo.gap = self.Gap
        codeInfo.length = self.Length
        codeInfo.min_repeat = self.MinRepeat
        codeInfo.trail = self.Trail
        
        return codeInfo

class IRLearnedCode:
    """This class represents a learned IR Code.
    
    This contains all data needed to re-transmit the code.
    """
    def __init__(self, code, codeInfo):
        """Creates a new IR Learned Code from a IRCode and a IRCodeInfo.
        
        Parameters:
            code<IRCode>: The learned code.
            codeInfo<IRCodeInfo>: The code encoding parameters.
        """
        self.Code = code #IRCode
        self.CodeInfo = codeInfo #IRCodeInfo

class IR(Phidget):
    """This class represents a Phidget IR controller.
    
    All methods to control an IR Controller are implemented in this class.
    
	See your device's User Guide for more specific API details, technical information, and revision details. 
	The User Guide, along with other resources, can be found on the product page for your device.
	
    Extends:
        Phidget
    """
    
    RAWDATA_LONGSPACE = 0x7fffffff
    
    def __init__(self):
        """The Constructor Method for the Accelerometer Class
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
        """
        Phidget.__init__(self)
        
        self.__IRCodeDelegate = None;
        self.__IRLearnDelegate = None;
        self.__IRRawDataDelegate = None;
        
        self.__onIRCodeHandler = None;
        self.__onIRLearnHandler = None;
        self.__onIRRawDataHandler = None;
        
        try:
            PhidgetLibrary.getDll().CPhidgetIR_create(byref(self.handle))
        except RuntimeError:
            raise
        
        if sys.platform == 'win32':
            self.__IRCODEHANDLER = WINFUNCTYPE(c_int, c_void_p, c_void_p, POINTER(c_ubyte), c_int, c_int, c_int)
            self.__IRLEARNHANDLER = WINFUNCTYPE(c_int, c_void_p, c_void_p, POINTER(c_ubyte), c_int, POINTER(CPhidgetIR_CodeInfo))
            self.__IRRAWDATAHANDLER = WINFUNCTYPE(c_int, c_void_p, c_void_p, POINTER(c_int), c_int)
        elif sys.platform == 'darwin' or sys.platform == 'linux2':
            self.__IRCODEHANDLER = CFUNCTYPE(c_int, c_void_p, c_void_p, POINTER(c_ubyte), c_int, c_int, c_int)
            self.__IRLEARNHANDLER = CFUNCTYPE(c_int, c_void_p, c_void_p, POINTER(c_ubyte), c_int, POINTER(CPhidgetIR_CodeInfo))
            self.__IRRAWDATAHANDLER = CFUNCTYPE(c_int, c_void_p, c_void_p, POINTER(c_int), c_int)

    def __del__(self):
        """The Destructor Method for the IR Class
        """
        Phidget.dispose(self)

    #Methods
    def transmit(self, code, codeInfo):
        """Transmits a code
        
        Parameters:
            code<IRCode>: The code to transmit.
            codeInfo<IRCodeInfo>: Code encoding information.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        codeInfoPtr = codeInfo.toCPhidgetIR_CodeInfo()
        codePtr = (c_ubyte * len(code.Data))()
        
        for posn in range(len(code.Data)):
            codePtr[posn] = c_ubyte(code.Data[posn])
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetIR_Transmit(self.handle, codePtr, byref(codeInfoPtr))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
    
    def transmitRepeat(self):
        """Transmits a repeat of a previously transmitted code.
        
        his must be called within the gap period after transmitting the original code.
        This is required for codes that use seperate sequences for the code and the repeat identifier.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetIR_TransmitRepeat(self.handle)
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
    
    def transmitRaw(self, data, gap=0, count=0, carrierFrequency=0, dutyCycle=0):
        """Transmits raw microsecond pulse data.
        
        Parameters:
            data<List of int>: An array of microsecond data which starts and ends with a pulse.
            gap<int>: A microsecond gap that will be maintained after the data is sent.
            count<int>: The number of data elements to transmit - this must be uneven.
            carrierFrequency<int>: The carrier frequency.
            dutyCycle<int>: The duty cycle.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        if count == 0:
            count = len(data)
        
        dataPtr = (c_int * count)()
        
        for i in range(count):
            dataPtr[i] = c_int(data[i])
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetIR_TransmitRaw(self.handle, dataPtr, count, carrierFrequency, dutyCycle, gap)
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        
    def readRaw(self):
        """Reads raw IR data.
        
        Returns:
            Buffer holding the read raw data <List of int>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        count = 2048 #this is as big as the library buffer, so the user doesn't have to poll as often
        buf = [] #buffer that will hold the read raw data and be returned to the user
        dataPtr = (c_int * count)()
        length = c_int()
        length.value = count;
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetIR_getRawData(self.handle, dataPtr, byref(length))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        
        for i in range(length.value):
            buf.append(dataPtr[i])
        
        return buf
    #endMethods
    
    #Properties
    def getLastCode(self):
        """Gets the last code that was recieved.
        
        Returns:
            The last IR Code received. <IRCode>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        codePtr = (c_ubyte * IR_MAX_CODE_DATA_LENGTH)(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)
        dataLength = c_int(IR_MAX_CODE_DATA_LENGTH)
        bitCount = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetIR_getLastCode(self.handle, codePtr, byref(dataLength), byref(bitCount))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            code = IRCode(codePtr, bitCount.value)
            return code
    
    def getLastLearnedCode(self):
        """Gets the last code the was learned.
        
        Returns:
            The last IR Code Learned. <IRLearnedCode>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        codePtr = (c_ubyte * IR_MAX_CODE_DATA_LENGTH)()
        dataLength = c_int(IR_MAX_CODE_DATA_LENGTH)
        codeInfo = CPhidgetIR_CodeInfo()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetIR_getLastLearnedCode(self.handle, codePtr, byref(dataLength), byref(codeInfo))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            learnedCode = IRLearnedCode(IRCode(codePtr, codeInfo.bitCount), IRCodeInfo(codeInfo))
            return learnedCode
    #end Properties
    
    #Events
    def __nativeIRCodeEvent(self, handle, usrptr, dataPtr, dataLength, bitCount, repeat):
        dataArray = []
        for i in range(dataLength):
            dataArray.append(dataPtr[i])
        repeatBool = False
        if repeat != 0:
            repeatBool = True
        if self.__IRCodeDelegate != None:
            self.__IRCodeDelegate(IRCodeEventArgs(self, IRCode(dataArray, bitCount), repeatBool))
        return 0

    def setOnIRCodeHandler(self, IRCodeHandler):
        """IR Code event.
        
        This event is called whenever a new code is recognized.
        
        Parameters:
            IRCodeHandler: hook to the IRCodeHandler callback function.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException
        """
        if IRCodeHandler == None:
            self.__IRCodeDelegate = None
            self.__onIRCodeHandler = None
        else:
            self.__IRCodeDelegate = IRCodeHandler
            self.__onIRCodeHandler = self.__IRCODEHANDLER(self.__nativeIRCodeEvent)
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetIR_set_OnCode_Handler(self.handle, self.__onIRCodeHandler, None)
        except RuntimeError:
            self.__IRCodeDelegate = None
            self.__onIRCodeHandler = None
            raise
        
        if result > 0:
            raise PhidgetException(result)
    
    def __nativeIRLearnEvent(self, handle, usrptr, dataPtr, dataLength, codeInfoPtr):
        codeInfo = codeInfoPtr[0]
        dataArray = []
        for i in range(dataLength):
            dataArray.append(dataPtr[i])
        if self.__IRLearnDelegate != None:
            self.__IRLearnDelegate(IRLearnEventArgs(self, IRCode(dataArray, codeInfo.bitCount), IRCodeInfo(codeInfo)))
        return 0

    def setOnIRLearnHandler(self, IRLearnHandler):
        """IR Learn event.
        
        This event is called when a new code has been learned. This generally requires the button to be held down for a second or two.
        
        Parameters:
            IRLearnHandler: hook to the IRLearnHandler callback function.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException
        """
        if IRLearnHandler == None:
            self.__IRLearnDelegate = None
            self.__onIRLearnHandler = None
        else:
            self.__IRLearnDelegate = IRLearnHandler
            self.__onIRLearnHandler = self.__IRLEARNHANDLER(self.__nativeIRLearnEvent)
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetIR_set_OnLearn_Handler(self.handle, self.__onIRLearnHandler, None)
        except RuntimeError:
            self.__IRLearnDelegate = None
            self.__onIRLearnHandler = None
            raise
        
        if result > 0:
            raise PhidgetException(result)
    
    def __nativeIRRawDataEvent(self, handle, usrptr, dataPtr, dataLength):
        dataArray = []
        for i in range(dataLength):
            dataArray.append(dataPtr[i])
        if self.__IRRawDataDelegate != None:
            self.__IRRawDataDelegate(IRRawDataEventArgs(self, dataArray))
        return 0

    def setOnIRRawDataHandler(self, IRRawDataHandler):
        """IR Raw Data event
        
        This event is called whenever new IR data is available. Data is in the form of an array of microsecond pulse values.
        This can be used if the user wishes to do their own data decoding, or for codes that the PhidgetIR cannot automatically recognize.
        
        Parameters:
            IRRawHandler: hook to the IRRawHandler callback function.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException
        """
        if IRRawDataHandler == None:
            self.__IRRawDataDelegate = None
            self.__onIRRawDataHandler = None
        else:
            self.__IRRawDataDelegate = IRRawDataHandler
            self.__onIRRawDataHandler = self.__IRRAWDATAHANDLER(self.__nativeIRRawDataEvent)
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetIR_set_OnRawData_Handler(self.handle, self.__onIRRawDataHandler, None)
        except RuntimeError:
            self.__IRRawDataDelegate = None
            self.__onIRRawDataHandler = None
            raise
        
        if result > 0:
            raise PhidgetException(result)
    #end Events
    
    @staticmethod
    def HexToData(hexString):
        if hexString.startswith("0x"):
            hexString = hexString[2:]
        
        if (len(hexString) % 2) == 1:
            hexString = '0' + hexString
        
        byteArrayLength = int(len(hexString) / 2)
        data = (c_ubyte * byteArrayLength)()
        
        for i in range(byteArrayLength):
            index = i*2;
            data[i] = c_ubyte(int(hexString[index:index+2], 16))
        
        return data