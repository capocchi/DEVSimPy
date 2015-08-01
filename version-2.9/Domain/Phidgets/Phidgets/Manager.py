"""Copyright 2010 Phidgets Inc.
This work is licensed under the Creative Commons Attribution 2.5 Canada License. 
To view a copy of this license, visit http://creativecommons.org/licenses/by/2.5/ca/
"""

__author__ = 'Adam Stelmack'
__version__ = '2.1.8'
__date__ = 'May 17 2010'

import threading
from ctypes import *
from Phidgets.PhidgetException import PhidgetErrorCodes, PhidgetException
from Phidgets.Events.Events import AttachEventArgs, DetachEventArgs, ErrorEventArgs, ServerConnectArgs, ServerDisconnectArgs
from Phidgets.Phidget import Phidget
from Phidgets.PhidgetLibrary import PhidgetLibrary
import sys

class Manager:
    """This class represents a Phidget Manager.
    
    The Phidget manager is a way to keep track of attached phidgets,
    it will send Attach and Detach events as Phidgets are added and removed fromt the system.
    
    The Phidget manager deals in base Phidget objects.
    These objects are not actually connected to opened Phidgets but can be used
    to get serial number, name, version, etc.
    """
    def __init__(self):
        """The Constructor Method for the Manager Class
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened.
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
        elif sys.platform == 'darwin' or sys.platform == 'linux2':
            self.__ATTACHHANDLER = CFUNCTYPE(c_int, c_void_p, c_void_p)
            self.__DETACHHANDLER = CFUNCTYPE(c_int, c_void_p, c_void_p)
            self.__ERRORHANDLER = CFUNCTYPE(c_int, c_void_p, c_void_p, c_int, c_char_p)
            self.__SERVERATTACHHANDLER = CFUNCTYPE(c_int, c_void_p, c_void_p)
            self.__SERVERDETACHHANDLER = CFUNCTYPE(c_int, c_void_p, c_void_p)
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetManager_create(byref(self.handle))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def __del__(self):
        try:
            result = PhidgetLibrary.getDll().CPhidgetManager_delete(self.handle)
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)
        else:
            self.handle = None

    def __nativeAttachEvent(self, handle, usrptr):
        phid = Phidget()
        phid.handle = c_void_p(handle)
        if self.__attach != None:
            self.__attach(AttachEventArgs(phid))
        return 0

    def setOnAttachHandler(self, attachHandler):
        """Set the Attach event handler.
        
        The attach handler is a method that will be called when a Phidget is phisically attached to the system,
        and has gone through its initalization, and so is ready to be used.
        
        Parameters:
            attachHandler: hook to the attachHandler callback function.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException
        """
        if attachHandler == None:
            self.__attach = None
            self.__onAttach = None
        else:
            self.__attach = attachHandler
            self.__onAttach = self.__ATTACHHANDLER(self.__nativeAttachEvent)

        try:
            result = PhidgetLibrary.getDll().CPhidgetManager_set_OnAttach_Handler(self.handle, self.__onAttach, None)
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def __nativeDetachEvent(self, handle, usrptr):
        phid = Phidget()
        phid.handle = c_void_p(handle)
        if self.__detach != None:
            self.__detach(DetachEventArgs(phid))
        return 0

    def setOnDetachHandler(self, detachHandler):
        """Set the Detach event handler.
        
        The detach handler is a method that will be called when a Phidget is phisically detached from the system, and is no longer available.
        
        Parameters:
            detachHandler: hook to the detachHandler callback function.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException
        """
        if detachHandler == None:
            self.__detach = None
            self.__onDetach = None
        else:
            self.__detach = detachHandler
            self.__onDetach = self.__DETACHHANDLER(self.__nativeDetachEvent)
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetManager_set_OnDetach_Handler(self.handle, self.__onDetach, None)
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def __nativeErrorEvent(self, handle, usrptr, errorCode, errorMessage):
        if self.__error != None:
            code = errorCode.value
            message = errorMessage.value
            self.__error(ErrorEventArgs(self, message, code))
        return 0

    def setOnErrorHandler(self, errorHandler):
        """Sets the error event handler.
        
        The error handler is a method that will be called when an asynchronous error occurs.
        Error events are not currently used, but will be in the future to report any problems that happen out of context from a direct function call.
        
        Parameters:
            errorHandler: hook to the errorHandler callback function.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException
        """
        if errorHandler == None:
            self.__error = None
            self.__onError = None
        else:
            self.__error = errorHandler
            self.__onError = self.__ERRORHANDLER(self.__nativeErrorEvent)
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetManager_set_OnError_Handler(self.handle, self.__onError, None)
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def __nativeServerConnectEvent(self, handle, usrptr):
        if self.__serverConnect != None:
            self.__serverConnect(ServerConnectArgs(self))
        return 0

    def setOnServerConnectHandler(self, serverConnectHandler):
        """Sets the ServerConnect event handler
        
        The serverConnect handler is a method that will be called when a connection to a server is made
        
        Parameters:
            serverConnectHandler: hook to the serverConnectHandler callback function.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException
        """
        if serverConnectHandler == None:
            self.__serverConnect = None
            self.__onServerConnect = None
        else:
            self.__serverConnect = serverConnectHandler
            self.__onServerConnect = self.__SERVERATTACHHANDLER(self.__nativeServerConnectEvent)
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetManager_set_OnServerConnect_Handler(self.handle, self.__onServerConnect, None)
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def __nativeServerDisconnectEvent(self, handle, usrptr):
        if self.__serverDisconnect != None:
            self.__serverDisconnect(ServerConnectArgs(self))
        return 0

    def setOnServerDisconnectHandler(self, serverDisconnectHandler):
        """Sets the ServerDisconnect event handler.
        
        The serverDisconnect handler is a method that will be called when a connection to a server is terminated.
        
        Parameters:
            serverDisconnectHandler: hook to the serverDisconnectHandler callback function.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException
        """
        if serverDisconnectHandler == None:
            self.__serverDisconnect = None
            self.__onServerDisconnect = None
        else:
            self.__serverDisconnect = serverDisconnectHandler
            self.__onServerDisconnect = self.__SERVERDETACHHANDLER(self.__nativeServerDisconnectEvent)
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetManager_set_OnServerDisconnect_Handler(self.handle, self.__onServerDisconnect, None)
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def getAttachedDevices(self):
        """Returns a list of Phidgets attached to the host computer.
        
        This list is updated right before the attach and detach events, and so will be up to date within these events.
        
        Returns:
            The list of attached phidgets <array of Phidget objects>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException
        """
        devices = []
        count = c_int()
        listptr = pointer(c_void_p())
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetManager_getAttachedDevices(self.handle, byref(listptr), byref(count))
        except RuntimeError:
            raise
        
        if result > 0:
                raise PhidgetException(result)
        
        for i in range(count.value):
            phid = Phidget()
            devicePtr = c_void_p(listptr[i])
            phid.handle = devicePtr
            devices.append(phid)
        
        return devices

    def openManager(self):
        """Starts the PhidgetManager.
        
        This method starts the phidget manager running in the base Phidget21 C library.
        If attach and detach listeners are to be used, they should be registered before start is called so that no events are missed.
        Once start is called, the Phidget Manager will be active until close is called.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetManager_open(self.handle)
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def openRemote(self, serverID, password=""):
        """Open this Manager remotely using a Server ID, and securely using a Password.
        
        ServerID can be NULL to get a listing of all Phidgets on all Servers
        
        This password can be set as a parameter when starting the Phidget Webservice.
        The use of a password is optional and calling the function without providing a password will
        connect normally.
        
        Parameters:
            serverID<string>: ServerID of the Phidget Webservice.
            password<string>: The secure password for the Phidget Webservice.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: if the Phidget Webservice cannot be contacted
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetManager_openRemote(self.handle, c_char_p(serverID), c_char_p(password))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def openRemoteIP(self, IPAddress, port, password=""):
        """Open this Manager remotely using an IP Address and port, and securely using a password.
        
        This password can be set as a parameter when starting the Phidget Webservice.
        The use of a password is optional and calling the function without providing a password will
        connect normally.
        
        Parameters:
            IPAddress<string>: IP Address or hostname of the Phidget Webservice
            port<int>: Port of the Phidget Webservice
            password<string>: The secure password for the Phidget Webservice
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: if the Phidget Webservice cannot be contacted
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetManager_openRemoteIP(self.handle, c_char_p(IPAddress), c_int(port), c_char_p(password))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def closeManager(self):
        """Shuts down the Phidget Manager.
        
        This method should be called to close down the Phidget Manager.
        Events will no longer be recieved. This method gets calledd automatically when the class is destroyed so calling it is not required.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this manager is not opened.
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetManager_close(self.handle)
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def getServerID(self):
        """Returns the Server ID of a Phidget Webservice when this Manager was opened as remote.
        
        This is an arbitrary server identifier, independant of IP address and Port.
        
        Returns:
            The serverID <string>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this manager is not opened or opened remotely.
        """
        serverID = c_char_p()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetManager_getServerID(self.handle, byref(serverID))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return serverID.value

    def getServerAddress(self):
        """Returns the Address of a Phidget Webservice when this Manager was opened as remote.
        
        This may be an IP Address or a hostname.
        
        Returns:
            The server address for the webservice <string>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: if the Manager was not opened or opened remotely.
        """
        serverAddr = c_char_p()
        port = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetManager_getServerAddress(self.handle, byref(serverAddr), byref(port))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return serverAddr.value

    def getServerPort(self):
        """Returns the Port of a Phidget Webservice when this Manager was opened as remote.
        
        Returns:
            The server port for the webservice.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: if the Manager was not opened or opened remotely.
        """
        serverAddr = c_char_p()
        port = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetManager_getServerAddress(self.handle, byref(serverAddr), byref(port))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return port.value

    def isAttachedToServer(self):
        """Returns the network attached status for remotely opened Phidgets.
        
        This method returns True or False, depending on whether a connection to the Phidget WebService is open - or not.
        If this is false for a remote Phidget then the connection is not active - either because a connection has not yet been established,
        or because the connection was terminated.
        
        Returns:
            The attached status <boolean>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: if the Manager was not opened or opened remotely.
        """
        serverStatus = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetManager_getServerStatus(self.handle, byref(serverStatus))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            if serverStatus.value == 1:
                return True
            else:
                return False
