"""
Copyright 2010 Phidgets Inc.
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
from Phidgets.PhidgetLibrary import PhidgetLibrary
from Phidgets.PhidgetException import PhidgetErrorCodes, PhidgetException
from Phidgets.Events.Events import AttachEventArgs, DetachEventArgs, ErrorEventArgs, ServerConnectArgs, ServerDisconnectArgs
import sys

class PhidgetLogLevel:
    PHIDGET_LOG_CRITICAL = 1
    PHIDGET_LOG_ERROR = 2
    PHIDGET_LOG_WARNING = 3
    PHIDGET_LOG_DEBUG = 4
    PHIDGET_LOG_INFO = 5
    PHIDGET_LOG_VERBOSE = 6

class PhidgetClass:
    NOTHING = 1
    ACCELEROMETER = 2
    ADVANCEDSERVO = 3
    ANALOG = 22
    BRIDGE = 23
    ENCODER = 4
    FREQUENCYCOUNTER = 21
    GPS = 5
    INTERFACEKIT = 7
    IR = 19
    LED = 8
    MOTORCONTROL = 9
    PHSENSOR = 10
    RFID = 11
    SERVO = 12
    SPATIAL = 20
    STEPPER = 13
    TEMPERATURESENSOR = 14
    TEXTLCD = 15
    TEXTLED = 16
    WEIGHTSENSOR = 17
    
    @staticmethod
    def toString(val):
        if val == PhidgetClass.ACCELEROMETER:
            return "ACCELEROMETER"
        elif val == PhidgetClass.ADVANCEDSERVO:
            return "ADVANCEDSERVO"
        elif val == PhidgetClass.ANALOG:
            return "ANALOG"
        elif val == PhidgetClass.BRIDGE:
            return "BRIDGE"
        elif val == PhidgetClass.ENCODER:
            return "ENCODER"
        elif val == PhidgetClass.FREQUENCYCOUNTER:
            return "FREQUENCYCOUNTER"
        elif val == PhidgetClass.GPS:
            return "GPS"
        elif val == PhidgetClass.INTERFACEKIT:
            return "INTERFACEKIT"
        elif val == PhidgetClass.IR:
            return "IR"
        elif val == PhidgetClass.LED:
            return "LED"
        elif val == PhidgetClass.MOTORCONTROL:
            return "MOTORCONTROL"
        elif val == PhidgetClass.PHSENSOR:
            return "PHSENSOR"
        elif val == PhidgetClass.RFID:
            return "RFID"
        elif val == PhidgetClass.SERVO:
            return "SERVO"
        elif val == PhidgetClass.SPATIAL:
            return "SPATIAL"
        elif val == PhidgetClass.STEPPER:
            return "STEPPER"
        elif val == PhidgetClass.TEMPERATURESENSOR:
            return "TEMPERATURESENSOR"
        elif val == PhidgetClass.TEXTLCD:
            return "TEXTLCD"
        elif val == PhidgetClass.TEXTLED:
            return "TEXTLED"
        elif val == PhidgetClass.WEIGHTSENSOR:
            return "WEIGHTSENSOR"
        else:
            return "NOTHING"

class PhidgetID:
    # These are all current devices
    PHIDID_ACCELEROMETER_3AXIS				= 0x07E		#< Phidget 3-axis Accelerometer (1059)
    PHIDID_ADVANCEDSERVO_1MOTOR				= 0x082		#< Phidget 1 Motor Advanced Servo (1066)
    PHIDID_ADVANCEDSERVO_8MOTOR				= 0x03A		#< Phidget 8 Motor Advanced Servo (1061)
    PHIDID_ANALOG_4OUTPUT				= 0x037		#< Phidget Analog 4-output (1002)
    PHIDID_BIPOLAR_STEPPER_1MOTOR                       = 0x07B		#< Phidget 1 Motor Bipolar Stepper Controller with 4 Digital Inputs (1063)
    PHIDID_BRIDGE_4INPUT				= 0x03B		#< Phidget Bridge 4-input (1046)
    PHIDID_ENCODER_1ENCODER_1INPUT                      = 0x04B		#< Phidget Encoder - Mechanical (1052)
    PHIDID_ENCODER_HS_1ENCODER				= 0x080		#< Phidget High Speed Encoder (1057)
    PHIDID_ENCODER_HS_4ENCODER_4INPUT                   = 0x04F		#< Phidget High Speed Encoder - 4 Encoder (1047)
    PHIDID_FREQUENCYCOUNTER_2INPUT                      = 0x035		#< Phidget Frequency Counter 2-input (1054)
    PHIDID_GPS						= 0x079		#< Phidget GPS (1040)
    PHIDID_INTERFACEKIT_0_0_4				= 0x040		#< Phidget Interface Kit 0/0/4 (1014)
    PHIDID_INTERFACEKIT_0_0_8				= 0x081		#< Phidget Interface Kit 0/0/8 (1017)
    PHIDID_INTERFACEKIT_0_16_16				= 0x044		#< Phidget Interface Kit 0/16/16 (1012)
    PHIDID_INTERFACEKIT_2_2_2				= 0x036		#< Phidget Interface Kit 2/2/2 (1011)
    PHIDID_INTERFACEKIT_8_8_8				= 0x045		#< Phidget Interface Kit 8/8/8 (1013, 1018, 1019)
    PHIDID_INTERFACEKIT_8_8_8_w_LCD                     = 0x07D		#< Phidget Interface Kit 8/8/8 with TextLCD (1201, 1202, 1203)
    PHIDID_IR						= 0x04D		#< Phidget IR Receiver Transmitter (1055)
    PHIDID_LED_64_ADV                                   = 0x04C		#< Phidget LED 64 Advanced (1031)
    PHIDID_LINEAR_TOUCH					= 0x076		#< Phidget Linear Touch (1015)
    PHIDID_MOTORCONTROL_1MOTOR				= 0x03E		#< Phidget 1 Motor Motor Controller (1065)
    PHIDID_MOTORCONTROL_HC_2MOTOR                       = 0x059		#< Phidget 2 Motor High Current Motor Controller (1064)
    PHIDID_RFID_2OUTPUT					= 0x031		#< Phidget RFID with Digital Outputs and Onboard LED (1023)
    PHIDID_ROTARY_TOUCH					= 0x077		#< Phidget Rotary Touch (1016)
    PHIDID_SPATIAL_ACCEL_3AXIS				= 0x07F		#< Phidget Spatial 3-axis accel (1049)
    PHIDID_SPATIAL_ACCEL_GYRO_COMPASS                   = 0x033		#< Phidget Spatial 3/3/3 (1056)
    PHIDID_TEMPERATURESENSOR				= 0x070		#< Phidget Temperature Sensor (1051)
    PHIDID_TEMPERATURESENSOR_4				= 0x032		#< Phidget Temperature Sensor 4-input (1048)
    PHIDID_TEMPERATURESENSOR_IR				= 0x03C		#< Phidget Temperature Sensor IR (1045)
    PHIDID_TEXTLCD_2x20_w_8_8_8				= 0x17D		#< Phidget TextLCD with Interface Kit 8/8/8 (1201, 1202, 1203)
    PHIDID_TEXTLCD_ADAPTER                              = 0x03D		#< Phidget TextLCD Adapter (1204)
    PHIDID_UNIPOLAR_STEPPER_4MOTOR                      = 0x07A		#< Phidget 4 Motor Unipolar Stepper Controller (1062)
    
    # These are all past devices (no longer sold)
    PHIDID_ACCELEROMETER_2AXIS				= 0x071		#< Phidget 2-axis Accelerometer (1053, 1054)
    PHIDID_INTERFACEKIT_0_8_8_w_LCD                     = 0x053		#< Phidget Interface Kit 0/8/8 with TextLCD (1219, 1220, 1221)
    PHIDID_INTERFACEKIT_4_8_8				= 4		#< Phidget Interface Kit 4/8/8
    PHIDID_LED_64                                       = 0x04A		#< Phidget LED 64 (1030)
    PHIDID_MOTORCONTROL_LV_2MOTOR_4INPUT                = 0x058		#< Phidget 2 Motor Low Voltage Motor Controller with 4 Digital Inputs (1060)
    PHIDID_PHSENSOR					= 0x074		#< Phidget PH Sensor (1058)
    PHIDID_RFID						= 0x030		#< Phidget RFID without Digital Outputs
    PHIDID_SERVO_1MOTOR                                 = 0x039		#< Phidget 1 Motor Servo Controller (1000)
    PHIDID_SERVO_1MOTOR_OLD                             = 2		#< Phidget 1 Motor Servo Controller - Old Version
    PHIDID_SERVO_4MOTOR                                 = 0x038		#< Phidget 4 Motor Servo Controller (1001)
    PHIDID_SERVO_4MOTOR_OLD                             = 3		#< Phidget 4 Motor Servo Controller - Old Version
    PHIDID_TEXTLCD_2x20					= 0x052		#< Phidget TextLCD without Interface Kit (1210)
    PHIDID_TEXTLCD_2x20_w_0_8_8				= 0x153		#< Phidget TextLCD with Interface Kit 0/8/8 (1219, 1220, 1221)
    PHIDID_TEXTLED_1x8					= 0x049		#< Phidget TextLED 1x8
    PHIDID_TEXTLED_4x8					= 0x048		#< Phidget TextLED 4x8 (1040)
    PHIDID_WEIGHTSENSOR					= 0x072		#< Phidget Weight Sensor (1050)

    @staticmethod
    def toString(val):
        if val == PhidgetID.PHIDID_ACCELEROMETER_3AXIS:
            return "PHIDID_ACCELEROMETER_3AXIS"
        elif val == PhidgetID.PHIDID_ADVANCEDSERVO_1MOTOR:
            return "PHIDID_ADVANCEDSERVO_1MOTOR"
        elif val == PhidgetID.PHIDID_ADVANCEDSERVO_8MOTOR:
            return "PHIDID_ADVANCEDSERVO_8MOTOR"
        elif val == PhidgetID.PHIDID_ANALOG_4OUTPUT:
            return "PHIDID_ANALOG_4OUTPUT"
        elif val == PhidgetID.PHIDID_BIPOLAR_STEPPER_1MOTOR:
            return "PHIDID_BIPOLAR_STEPPER_1MOTOR"
        elif val == PhidgetID.PHIDID_BRIDGE_4INPUT:
            return "PHIDID_BRIDGE_4INPUT"
        elif val == PhidgetID.PHIDID_ENCODER_1ENCODER_1INPUT:
            return "PHIDID_ENCODER_1ENCODER_1INPUT"
        elif val == PhidgetID.PHIDID_ENCODER_HS_1ENCODER:
            return "PHIDID_ENCODER_HS_1ENCODER"
        elif val == PhidgetID.PHIDID_ENCODER_HS_4ENCODER_4INPUT:
            return "PHIDID_ENCODER_HS_4ENCODER_4INPUT"
        elif val == PhidgetID.PHIDID_FREQUENCYCOUNTER_2INPUT:
            return "PHIDID_FREQUENCYCOUNTER_2INPUT"
        elif val == PhidgetID.PHIDID_GPS:
            return "PHIDID_GPS"
        elif val == PhidgetID.PHIDID_INTERFACEKIT_0_0_4:
            return "PHIDID_INTERFACEKIT_0_0_4"
        elif val == PhidgetID.PHIDID_INTERFACEKIT_0_0_8:
            return "PHIDID_INTERFACEKIT_0_0_8"
        elif val == PhidgetID.PHIDID_INTERFACEKIT_0_16_16:
            return "PHIDID_INTERFACEKIT_0_16_16"
        elif val == PhidgetID.PHIDID_INTERFACEKIT_2_2_2:
            return "PHIDID_INTERFACEKIT_2_2_2"
        elif val == PhidgetID.PHIDID_INTERFACEKIT_8_8_8:
            return "PHIDID_INTERFACEKIT_8_8_8"
        elif val == PhidgetID.PHIDID_INTERFACEKIT_8_8_8_w_LCD:
            return "PHIDID_INTERFACEKIT_8_8_8_w_LCD"
        elif val == PhidgetID.PHIDID_IR:
            return "PHIDID_IR"
        elif val == PhidgetID.PHIDID_LED_64_ADV:
            return "PHIDID_LED_64_ADV"
        elif val == PhidgetID.PHIDID_LINEAR_TOUCH:
            return "PHIDID_LINEAR_TOUCH"
        elif val == PhidgetID.PHIDID_MOTORCONTROL_1MOTOR:
            return "PHIDID_MOTORCONTROL_1MOTOR"
        elif val == PhidgetID.PHIDID_MOTORCONTROL_HC_2MOTOR:
            return "PHIDID_MOTORCONTROL_HC_2MOTOR"
        elif val == PhidgetID.PHIDID_RFID_2OUTPUT:
            return "PHIDID_RFID_2OUTPUT"
        elif val == PhidgetID.PHIDID_ROTARY_TOUCH:
            return "PHIDID_ROTARY_TOUCH"
        elif val == PhidgetID.PHIDID_SPATIAL_ACCEL_3AXIS:
            return "PHIDID_SPATIAL_ACCEL_3AXIS"
        elif val == PhidgetID.PHIDID_SPATIAL_ACCEL_GYRO_COMPASS:
            return "PHIDID_SPATIAL_ACCEL_GYRO_COMPASS"
        elif val == PhidgetID.PHIDID_TEMPERATURESENSOR:
            return "PHIDID_TEMPERATURESENSOR"
        elif val == PhidgetID.PHIDID_TEMPERATURESENSOR_4:
            return "PHIDID_TEMPERATURESENSOR_4"
        elif val == PhidgetID.PHIDID_TEMPERATURESENSOR_IR:
            return "PHIDID_TEMPERATURESENSOR_IR"
        elif val == PhidgetID.PHIDID_TEXTLCD_2x20_w_8_8_8:
            return "PHIDID_TEXTLCD_2x20_w_8_8_8"
        elif val == PhidgetID.PHIDID_TEXTLCD_ADAPTER:
            return "PHIDID_TEXTLCD_ADAPTER"
        elif val == PhidgetID.PHIDID_UNIPOLAR_STEPPER_4MOTOR:
            return "PHIDID_UNIPOLAR_STEPPER_4MOTOR"
        elif val == PhidgetID.PHIDID_ACCELEROMETER_2AXIS:
            return "PHIDID_ACCELEROMETER_2AXIS"
        elif val == PhidgetID.PHIDID_INTERFACEKIT_0_8_8_w_LCD:
            return "PHIDID_INTERFACEKIT_0_8_8_w_LCD"
        elif val == PhidgetID.PHIDID_INTERFACEKIT_4_8_8:
            return "PHIDID_INTERFACEKIT_4_8_8"
        elif val == PhidgetID.PHIDID_LED_64:
            return "PHIDID_LED_64"
        elif val == PhidgetID.PHIDID_MOTORCONTROL_LV_2MOTOR_4INPUT:
            return "PHIDID_MOTORCONTROL_LV_2MOTOR_4INPUT"
        elif val == PhidgetID.PHIDID_PHSENSOR:
            return "PHIDID_PHSENSOR"
        elif val == PhidgetID.PHIDID_RFID:
            return "PHIDID_RFID"
        elif val == PhidgetID.PHIDID_SERVO_1MOTOR:
            return "PHIDID_SERVO_1MOTOR"
        elif val == PhidgetID.PHIDID_SERVO_1MOTOR_OLD:
            return "PHIDID_SERVO_1MOTOR_OLD"
        elif val == PhidgetID.PHIDID_SERVO_4MOTOR:
            return "PHIDID_SERVO_4MOTOR"
        elif val == PhidgetID.PHIDID_SERVO_4MOTOR_OLD:
            return "PHIDID_SERVO_4MOTOR_OLD"
        elif val == PhidgetID.PHIDID_TEXTLCD_2x20:
            return "PHIDID_TEXTLCD_2x20"
        elif val == PhidgetID.PHIDID_TEXTLCD_2x20_w_0_8_8:
            return "PHIDID_TEXTLCD_2x20_w_0_8_8"
        elif val == PhidgetID.PHIDID_TEXTLED_1x8:
            return "PHIDID_TEXTLED_1x8"
        elif val == PhidgetID.PHIDID_TEXTLED_4x8:
            return "PHIDID_TEXTLED_4x8"
        elif val == PhidgetID.PHIDID_WEIGHTSENSOR:
            return "PHIDID_WEIGHTSENSOR"
        else:
            return "NOTHING"

class Phidget:
    """This is the base class from which all Phidget device classes derive."""
    def __init__(self):
        """Default Class constructor.
        
        This constructor is to be used only by subclasses, as the Phidget calss should never need to be instatiated directly by the user.
        """
        self.handle = c_void_p()
        
        self.__attach = None
        self.__detach = None
        self.__error = None
        self.__serverConnect = None
        self.__serverDisconnect = None
        
        self.__onAttach = None
        self.__onDetach = None
        self.__onError = None
        self.__onServerConnect = None
        self.__onServerDisconnect = None
        
        if sys.platform == 'win32':
            self.__ATTACHHANDLER = WINFUNCTYPE(c_int, c_void_p, c_void_p)
            self.__DETACHHANDLER = WINFUNCTYPE(c_int, c_void_p, c_void_p)
            self.__ERRORHANDLER = WINFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_char_p)
            self.__SERVERATTACHHANDLER = WINFUNCTYPE(c_int, c_void_p, c_void_p)
            self.__SERVERDETACHHANDLER = WINFUNCTYPE(c_int, c_void_p, c_void_p)
        elif sys.platform == 'darwin' or sys.platform == 'linux' or sys.platform == 'linux2':
            self.__ATTACHHANDLER = CFUNCTYPE(c_int, c_void_p, c_void_p)
            self.__DETACHHANDLER = CFUNCTYPE(c_int, c_void_p, c_void_p)
            self.__ERRORHANDLER = CFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_char_p)
            self.__SERVERATTACHHANDLER = CFUNCTYPE(c_int, c_void_p, c_void_p)
            self.__SERVERDETACHHANDLER = CFUNCTYPE(c_int, c_void_p, c_void_p)

    @staticmethod
    def dispose(self):
        try:
            result = PhidgetLibrary.getDll().CPhidget_delete(self.handle)
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)
        else:
            self.handle = None

    def closePhidget(self):
        """Closes this Phidget.
        
        This will shut down all threads dealing with this Phidget and you won't recieve any more events.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened.
        """
        try:
            result = PhidgetLibrary.getDll().CPhidget_close(self.handle)
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)

    def openPhidget(self, serial=-1):
        """Open a Phidget with or without a serial number.
        
        Open is pervasive. What this means is that you can call open on a device before it is plugged in, and keep the device opened across device dis- and re-connections.
        
        Open is Asynchronous.  What this means is that open will return immediately -- before the device being opened is actually available,
        so you need to use either the attach event or the waitForAttachment method to determine if a device is available before using it.
        
        If no arguement is provided, the first available Phidget will be opened. If there are two Phidgets of the same type attached to the system,
        you should specify a serial number, as there is no guarantee which Phidget will be selected by the call to open().
        
        The serial number is a unique number assigned to each Phidget during production and can be used to uniquely identify specific phidgets.
        
        Parameters:
            serial<int>: The serial number of the device
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException
        """
        try:
            result = PhidgetLibrary.getDll().CPhidget_open(self.handle, c_int(serial))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def openRemote(self, serverID, serial=-1, password=""):
        """Open this Phidget remotely using a Server ID, securely providing a password, and whether or not to connect to a specific serial number.
        
        Providing a password will open the connection securely depending on if a password is set on the host machine's webservice.
        
        If no serial number is provided, the first available Phidget will be opened. If there are two Phidgets of the same type attached to the system,
        you should specify a serial number, as there is no guarantee which Phidget will be selected by the call to open().
        
        Parameters:
            serverID<string>: ServerID of the Phidget Webservice
            serial<int>: The serial number of the device
            password<string>: The secure password for the Phidget Webservice
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: if the Phidget Webservice cannot be contacted
        """
        if not isinstance(serial, int):
            if password == "":
                password = serial
                serial = -1
            else:
                raise TypeError("inappropriate arguement type: serial %s" % (type(serial)))
        
        try:
            result = PhidgetLibrary.getDll().CPhidget_openRemote(self.handle, c_int(serial), c_char_p(serverID), c_char_p(password))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def openRemoteIP(self, IPAddress, port, serial=-1, password=""):
        """Open this Phidget remotely using an IP Address, securely providing a password,and whether or not to connect to a specific serial number.
        
        Providing a password will open the connection securely depending on if a password is set on the host machine's webservice.
        
        If no serial number is provided, the first available Phidget will be opened. If there are two Phidgets of the same type attached to the system,
        you should specify a serial number, as there is no guarantee which Phidget will be selected by the call to open().
        
        Parameters:
            IPAddress<string>: IP Address or hostname of the Phidget Webservice
            port<int>: Port of the Phidget Webservice
            serial<int>: The serial number of the device
            password<string>: The secure password for the Phidget Webservice
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: if the Phidget Webservice cannot be contacted
        """
        if not isinstance(serial, int):
            if password == "":
                password = serial
                serial = -1
            else:
                raise TypeError("inappropriate arguement type: serial %s" % (type(serial)))
        
        try:
            result = PhidgetLibrary.getDll().CPhidget_openRemoteIP(self.handle, c_int(serial), c_char_p(IPAddress), c_int(port), c_char_p(password))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def getDeviceLabel(self):
        """Gets the label associated with this Phidget.
        
        This label is a String - up to ten digits - that is stored in the Flash memory of newer Phidgets.
        This label can be set programatically (see setDeviceLabel), and is non-volatile - so it is remembered even if the Phidget is unplugged.
        
        Returns:
            The label associated with this Phidget <string>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if this Phidget does not support labels.
        """
        label = c_char_p()
        
        try:
            result = PhidgetLibrary.getDll().CPhidget_getDeviceLabel(self.handle, byref(label))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return prepOutput(label)

    def getDeviceName(self):
        """Return the name of this Phidget.
        
        This is a string that describes the device. For example, a PhidgetInterfaceKit 
        could be described as "Phidget InterfaceKit 8/8/8", or "Phidget InterfaceKit 0/0/4", among others, depending on the specific device.
        
        This lets you determine the specific type of a Phidget, within the broader classes of Phidgets, such as PhidgetInterfaceKit, or PhidgetServo.
        
        Returns:
            The name of the device <string>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this phidget is not opened or attached.
        """
        ptr = c_char_p()
        
        try:
            result = PhidgetLibrary.getDll().CPhidget_getDeviceName(self.handle, byref(ptr))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return prepOutput(ptr)

    def getDeviceType(self):
        """Return the device type of this Phidget.
        
        This is a string that describes the device as a class of devices. For example, all PhidgetInterfaceKit Phidgets
        will returns the String "PhidgetInterfaceKit".
        
        Returns:
            The Device Type <string>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If there is no Phidget attached.
        """
        ptr = c_char_p()
        
        try:
            result = PhidgetLibrary.getDll().CPhidget_getDeviceType(self.handle, byref(ptr))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return prepOutput(ptr)

    def getDeviceClass(self):
        """Gets the class of this Phidget.
        
        Classes represent a group of Phidgets that use the same API type.
        
        Returns:
            The Device Class number<int>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If there is no Phidget attached.
        """
        classNum = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidget_getDeviceClass(self.handle, byref(classNum))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return classNum.value
    
    def getDeviceID(self):
        """Gets the ID of this Phidget.
        
        This ID specifies a specific Phidget device, within the phidget class.
        
        Returns:
            The Device ID <int>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If there is no Phidget attached.
        """
        deviceID = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidget_getDeviceID(self.handle, byref(deviceID))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return deviceID.value

    def getDeviceVersion(self):
        """Returns the device version of this Phidget.
        
        This number is simply a way of distinguishing between different revisions of a specific type of Phidget, and is
        only really of use if you need to troubleshoot device problems with Phidgets Inc.
        
        Returns:
            The Device Version <int>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If there is no Phidget attached.
        """
        version = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidget_getDeviceVersion(self.handle, byref(version))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return version.value

    def isAttached(self):
        """Returns the attached status of this Phidget.
        
        This method returns True or False, depending on whether the Phidget is phisically plugged into the computer, initialized, and ready to use - or not.
        If a Phidget is not attached, many functions calls will fail with a PhidgetException, so either checking this function, or using the Attach and Detach events, is recommended, if a device is likely to be attached or detached during use.
        
        Returns:
            Attached Status of the Phidget <boolean>
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened.
        """
        status = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidget_getDeviceStatus(self.handle, byref(status))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            if status.value == 1:
                return True
            else:
                return False

    def getLibraryVersion(self):
        """Returns the library version.
        
        This is the library version of the underlying phidget21 C library and not the version of the Python wrapper module implementation.
        The version is retured as a string which contains the version number and build date.
        
        Returns:
            The Library Version <string>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        libVer = c_char_p()
        
        try:
            result = PhidgetLibrary.getDll().CPhidget_getLibraryVersion(byref(libVer))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return prepOutput(libVer)

    def getSerialNum(self):
        """Returns the unique serial number of this Phidget.
        
        This number is set during manufacturing, and is unique across all Phidgets. This number can be used in calls to open to specify this specific Phidget to be opened.
        
        Returns:
            The Serial Number <int>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        serialNo = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidget_getSerialNumber(self.handle, byref(serialNo))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return serialNo.value

    def __nativeAttachEvent(self, handle, usrptr):
        if self.__attach != None:
            self.__attach(AttachEventArgs(self))
        return 0

    def setOnAttachHandler(self, attachHandler):
        """Sets the Attach Event Handler.
        
        The attach handler is a method that will be called when this Phidget is physically attached to the system, and has gone through its initalization, and so is ready to be used.
        
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

    def __nativeDetachEvent(self, handle, usrptr):
        if self.__detach != None:
            self.__detach(DetachEventArgs(self))
        return 0

    def setOnDetachHandler(self, detachHandler):
        """Sets the Detach Event Handler.
        
        The detach handler is a method that will be called when this Phidget is phisically detached from the system, and is no longer available.
        This is particularly usefull for applications when a phisical detach would be expected.
        
        Remember that many of the methods, if called on an unattached device, will throw a PhidgetException.
        This Exception can be checked to see if it was caused by a device being unattached, but a better method would be to regiter the detach handler,
        which could notify the main program logic that the device is no longer available, disable GUI controls, etc.
        
        Parameters:
            detachHandler: hook to the detachHandler callback function
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened.
        """
        if detachHandler == None:
            self.__detach = None
            self.__onDetach = None
        else:
            self.__detach = detachHandler
            self.__onDetach = self.__DETACHHANDLER(self.__nativeDetachEvent)
        
        try:
            result = PhidgetLibrary.getDll().CPhidget_set_OnDetach_Handler(self.handle, self.__onDetach, None)
        except RuntimeError:
            self.__detach = None
            self.__onDetach = None
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def __nativeErrorEvent(self, handle, usrptr, errorCode, errorMessage):
        if self.__error != None:
            code = errorCode
            message = errorMessage
            self.__error(ErrorEventArgs(self, message, code))
        return 0

    def setOnErrorhandler(self, errorHandler):
        """Sets the Error Event Handler.
        
        The error handler is a method that will be called when an asynchronous error occurs.
        Error events are not currently used, but will be in the future to report any problems that happen out of context from a direct function call.
        
        Parameters:
            errorHandler: hook to the errorHandler callback function.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened.
        """
        if errorHandler == None:
            self.__error = None
            self.__onError = None
        else:
            self.__error = errorHandler
            self.__onError = self.__ERRORHANDLER(self.__nativeErrorEvent)
        
        try:
            result = PhidgetLibrary.getDll().CPhidget_set_OnError_Handler(self.handle, self.__onError, None)
        except RuntimeError:
            self.__error = None
            self.__onError = None
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def waitForAttach(self, timeout):
        """Waits for this Phidget to become available.
        
        This method can be called after open has been called to wait for thid Phidget to become available.
        This is usefull because open is asynchronous (and thus returns immediately), and most methods will throw a PhidgetException is they are called before a device is actually ready.
        This method is synonymous with polling the isAttached method until it returns True, or using the Attach event.
        
        This method blocks for up to the timeout, at which point it will throw a PhidgetException. Otherwise, it returns when the phidget is attached and initialized.
        
        A timeout of 0 is infinite.
        
        Parameters:
            timeout<long>: Timeout in milliseconds
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened.
        """
        
        try:
            result = PhidgetLibrary.getDll().CPhidget_waitForAttachment(self.handle, c_long(timeout))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def __nativeServerConnectEvent(self, handle, usrptr):
        if self.__serverConnect != None:
            self.__serverConnect(ServerConnectArgs(self))
        return 0

    def setOnServerConnectHandler(self, serverConnectHandler):
        """Sets the Server Connect Event Handler.
        
        The serverConnect handler is a method that will be called when a connection to a server is made. This is only usefull for Phidgets opened remotely.
        
        Parameters:
            serverConnectHandler: hook to the serverConnectHandler callback function
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened
        """
        if serverConnectHandler == None:
            self.__serverConnect = None
            self.__onServerConnect = None
        else:
            self.__serverConnect = serverConnectHandler
            self.__onServerConnect = self.__SERVERATTACHHANDLER(self.__nativeServerConnectEvent)
        
        try:
            result = PhidgetLibrary.getDll().CPhidget_set_OnServerConnect_Handler(self.handle, self.__onServerConnect, None)
        except RuntimeError:
            self.__serverConnect = None
            self.__onServerConnect = None
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def __nativeServerDisconnectEvent(self, handle, usrptr):
        if self.__serverDisconnect != None:
            self.__serverDisconnect(ServerConnectArgs(self))
        return 0

    def setOnServerDisconnectHandler(self, serverDisconnectHandler):
        """Set the Server Disconnect event handler.
        
        The serverDisconnect handler is a method that will be called when a connection to a server is terminated. This is only usefull for Phidgets opened remotely.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened
        """
        if serverDisconnectHandler == None:
            self.__serverDisconnect = None
            self.__onServerDisconnect = None
        else:
            self.__serverDisconnect = serverDisconnectHandler
            self.__onServerDisconnect = self.__SERVERDETACHHANDLER(self.__nativeServerDisconnectEvent)
        
        try:
            result = PhidgetLibrary.getDll().CPhidget_set_OnServerDisconnect_Handler(self.handle, self.__onServerDisconnect, None)
        except RuntimeError:
            self.__serverDisconnect = None
            self.__onServerDisconnect = None
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def getServerAddress(self):
        """Returns the Address of a Phidget Webservice.
        
        Returns the Address of a Phidget Webservice when this Phidget was opened as remote.
        This may be an IP Address or a hostname.
        
        Returns:
            The Address of the Webservice <string>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: if this Phidget was open opened as a remote Phidget.
        """
        serverAddr = c_char_p()
        port = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidget_getServerAddress(self.handle, byref(serverAddr), byref(port))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return prepOutput(serverAddr)

    def getServerID(self):
        """Returns the Server ID of a Phidget Webservice.
        
        Returns the Server ID of a Phidget Webservice when this Phidget was opened as remote.
        This is an arbitrary server identifier, independant of IP address and Port.
        
        Returns:
            The ServerID of the Webservice <string>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: if this Phidget was open opened as a remote Phidget.
        """
        serverID = c_char_p()
        
        try:
            result = PhidgetLibrary.getDll().CPhidget_getServerID(self.handle, byref(serverID))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return prepOutput(serverID)

    def isAttachedToServer(self):
        """Returns the network attached status for remotely opened Phidgets.
        
        This method returns True or False, depending on whether a connection to the Phidget WebService is open - or not.
        If this is false for a remote Phidget then the connection is not active - either because a connection has not yet been established,
        or because the connection was terminated.
        
        Returns:
            Phidget Network Attached Status <boolean>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened remotely.
        """
        serverStatus = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidget_getServerStatus(self.handle, byref(serverStatus))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            if serverStatus.value == 1:
                return True
            else:
                return False

    @staticmethod
    def enableLogging(level, file):
        """Turns on logging in the native C Library.
        
        This is mostly usefull for debugging purposes - when an issue needs to be resolved by Phidgets Inc.
        The output is mostly low-level library information, that won't be usefull for most users.
        
        Logging may be usefull for users trying to debug their own problems, as logs can be inserted by the user using log.
        The level can be one of:
        PhidgetLogLevel.PHIDGET_LOG_VERBOSE ,
        PhidgetLogLevel.PHIDGET_LOG_INFO ,
        PhidgetLogLevel.PHIDGET_LOG_DEBUG ,
        PhidgetLogLevel.PHIDGET_LOG_WARNING ,
        PhidgetLogLevel.PHIDGET_LOG_ERROR or
        PhidgetLogLevel.PHIDGET_LOG_CRITICAL 
        
        Parameters:
            level<int>: highest level of logging that will be output, the PhidgetLogLevel object has been provided for a readable way to set this.
            file<string>: path and name of file to output to.  specify NULL to output to the console.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException
        """
        try:
            result = PhidgetLibrary.getDll().CPhidget_enableLogging(c_int(level), c_char_p(file))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    @staticmethod
    def disableLogging():
        """Turns off logging in the native C Library.
        
        This only needs to be called if enableLogging was called to turn logging on.
        This will turn logging back off.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException
        """
        try:
            result = PhidgetLibrary.getDll().CPhidget_disableLogging()
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    @staticmethod
    def log(level, id, log):
        """Adds a log entry into the phidget log.
        
        This log is enabled by calling enableLogging and this allows the entry of user logs in amongst the phidget library logs.
        
        The level can be one of:
        PhidgetLogLevel.PHIDGET_LOG_VERBOSE,
        PhidgetLogLevel.PHIDGET_LOG_INFO,
        PhidgetLogLevel.PHIDGET_LOG_DEBUG,
        PhidgetLogLevel.PHIDGET_LOG_WARNING,
        PhidgetLogLevel.PHIDGET_LOG_ERROR or
        PhidgetLogLevel.PHIDGET_LOG_CRITICAL
        
        Note: PhidgetLogLevel.PHIDGET_LOG_DEBUG should not be used, as these logs are only printed when using the debug library,
        which is not generally available.
        
        Parameters:
            level<int>: level to enter the log at.
            id<string>: an arbitrary identifier for this log.  This can be NULL. The C library uses this field for source filename and line number.
            log<string>: the message to log.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException
        """
        try:
            result = PhidgetLibrary.getDll().CPhidget_log(c_int(level), c_char_p(id), c_char_p(log))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
