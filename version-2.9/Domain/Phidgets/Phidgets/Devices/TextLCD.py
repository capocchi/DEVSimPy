"""Copyright 2012 Phidgets Inc.
This work is licensed under the Creative Commons Attribution 2.5 Canada License. 
To view a copy of this license, visit http://creativecommons.org/licenses/by/2.5/ca/
"""

__author__ = 'Adam Stelmack'
__version__ = '2.1.8'
__date__ = 'May 17 2010'

import ctypes
from ctypes import byref, c_int, c_char_p, c_ubyte
import threading
import sys
from Phidgets.PhidgetLibrary import PhidgetLibrary
from Phidgets.Phidget import Phidget
from Phidgets.PhidgetException import PhidgetException

class TextLCD_ScreenSize:
    PHIDGET_TEXTLCD_SCREEN_NONE=1    #< no screen attached
    PHIDGET_TEXTLCD_SCREEN_1x8=2     #< 1 row, 8 column screen
    PHIDGET_TEXTLCD_SCREEN_2x8=3     #< 2 row, 8 column screen
    PHIDGET_TEXTLCD_SCREEN_1x16=4    #< 1 row, 16 column screen
    PHIDGET_TEXTLCD_SCREEN_2x16=5    #< 2 row, 16 column screen
    PHIDGET_TEXTLCD_SCREEN_4x16=6    #< 4 row, 16 column screen
    PHIDGET_TEXTLCD_SCREEN_2x20=7    #< 2 row, 20 column screen
    PHIDGET_TEXTLCD_SCREEN_4x20=8    #< 4 row, 20 column screen
    PHIDGET_TEXTLCD_SCREEN_2x24=9    #< 2 row, 24 column screen
    PHIDGET_TEXTLCD_SCREEN_1x40=10   #< 1 row, 40 column screen
    PHIDGET_TEXTLCD_SCREEN_2x40=11   #< 2 row, 40 column screen
    PHIDGET_TEXTLCD_SCREEN_4x40=12   #< 4 row, 40 column screen (special case, requires both screen connections)
    PHIDGET_TEXTLCD_SCREEN_UNKNOWN=13

class TextLCD(Phidget):
    """This class represents a Phidget Text LCD.
    
    All methods to control the Text LCD are implemented in this class.
    The TextLCD Phidget consists of a Vacuum Fluorescent display that is
    capable of displaying Standard as well as custom characters in multiple rows.
	
	See your device's User Guide for more specific API details, technical information, and revision details. 
	The User Guide, along with other resources, can be found on the product page for your device.
    
    Extends:
        Phidget
    """
    def __init__(self):
        """The Constructor Method for the TextLCD Class
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
        """
        Phidget.__init__(self)
        
        try:
            PhidgetLibrary.getDll().CPhidgetTextLCD_create(byref(self.handle))
        except RuntimeError:
            raise

    def __del__(self):
        """The Destructor Method for the TextLCD Class
        """
        Phidget.dispose(self)

    def getRowCount(self):
        """Returns the number of rows available on the display.
        
        Returns:
            The number of rows <int>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        rowCount = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetTextLCD_getRowCount(self.handle, byref(rowCount))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return rowCount.value

    def getColumnCount(self):
        """Returns the number of columns (characters per row) available on the display.
        
        This value is the same for every row.
        
        Returns:
            The number of rows <int>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        columnCount = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetTextLCD_getColumnCount(self.handle, byref(columnCount))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return columnCount.value

    def getBacklight(self):
        """Returns the status of the backlight.
        
        True indicated that the backlight is on, False indicated that it is off.
        The backlight is by default turned on.
        
        Returns:
            The status of the backlight <boolean>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        backlightStatus = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetTextLCD_getBacklight(self.handle, byref(backlightStatus))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            if backlightStatus.value == 1:
                return True
            else:
                return False

    def setBacklight(self, state):
        """Sets the status of the backlight.
        
        True turns the backlight on, False turns it off.
        The backlight is by default turned on.
        
        Parameters:
            state<boolean>: the desired backlight state.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        if state == True:
            value = 1
        else:
            value = 0
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetTextLCD_setBacklight(self.handle, c_int(value))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def getContrast(self):
        """Returns the contrastof the display.
        
        This is the contrast of the entire display.
        
        Returns:
            The current contrast setting <int>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        contrast = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetTextLCD_getContrast(self.handle, byref(contrast))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return contrast.value

    def setContrast(self, value):
        """Sets the contrast of the display.
        
        The valid range is 0-255.
        Changing the contrast can increase the readability of the display in certain viewing situation, such as at an odd angle.
        
        Parameters:
            value<int>: the desired contrast value.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetTextLCD_setContrast(self.handle, c_int(value))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def getBrightness(self):
        """Returns the brightness of the display.
        
        This is the brightness of the entire display. For devices that support a range of backlight brightnesses.
        
        Returns:
            The current brightness setting <int>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        brightness = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetTextLCD_getBrightness(self.handle, byref(brightness))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            return brightness.value
    
    def setBrightness(self, value):
        """Sets the brightness of the display.
        
        For devices that support a range of backlight brightnesses.
        The valid range is 0-255.
        
        Parameters:
            value<int>: the desired brightness value.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetTextLCD_setBrightness(self.handle, c_int(value))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def getCursor(self):
        """Returns the status of the cursor.
        
        True indicates that the cursor on, False indicates that it is off.
        The cursor is an underscore which appears directly to the right of the last entered character on the display.
        The cursor is by default disabled.
        
        Returns:
            The status of the cursor <boolean>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        cursorStatus = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetTextLCD_getCursorOn(self.handle, byref(cursorStatus))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            if cursorStatus.value == 1:
                return True
            else:
                return False

    def setCursor(self, state):
        """Sets the state of the cursor.
        
        True turns the cursor is on, False turns it off.
        The cursor is an underscore which appears directly to the right of the last entered character on the display.
        The cursor is by default disabled.
        
        Parameters:
            state<boolean>: the desired cursor state.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        if state == True:
            value = 1
        else:
            value = 0
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetTextLCD_setCursorOn(self.handle, c_int(value))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def getCursorBlink(self):
        """Returns the status of the cursor blink.
        
        True indicates that the cursor blink is on, False indicates that it is off.
        The cursor blink is an flashing box which appears directly to the right of
        the last entered character on the display, in the same spot as the cursor if it is enabled.
        The cursor blink is by default disabled.
        
        Returns:
            The current status of the cursor blink <boolean>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        cursorBlinkStatus = c_int()
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetTextLCD_getCursorBlink(self.handle, byref(cursorBlinkStatus))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)
        else:
            if cursorBlinkStatus.value == 1:
                return True
            else:
                return False

    def setCursorBlink(self, state):
        """Sets the state of the cursor blink.
        
        True turns the cursor blink on, False turns it off.
        The cursor blink is an flashing box which appears directly to the right
        of the last entered character on the display, in the same spot as the cursor if it is enabled.
        The cursor blink is by default disabled.
        
        Parameters:
            state - the desired state of the cursor blink <boolean>.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        if state == True:
            value = 1
        else:
            value = 0
        
        try:
            result = PhidgetLibrary.getDll().CPhidgetTextLCD_setCursorBlink(self.handle, c_int(value))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def setDisplayCharacter(self, row, column, character):
        """Sets a single character on the display.

        On linux, it has been found that encoding the string with iso-8859-15 encoding prevents a "UnicodeEncodeError" that would occur and ensure
        the character being displayed is correct between windows and linux.

        e.g. textLCD.setDisplayCharacter(0, 0, chr(223).encode("iso-8859-15"))

        Parameters:
            row<int>: the index of the row to write the character to.
            column<int>: the index of the column to write the character to.
            character<char>: the character to display.

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the row index is invalid.
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetTextLCD_setDisplayCharacter(self.handle, c_int(row), c_int(column), c_ubyte(character))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)

    def setDisplayString(self, index, string):
        """Sets the display string of a certain row.
        
        If the string is longer then the row, it will be truncated.
        
        On linux, it has been found that encoding the string with iso-8859-15 encoding prevents a "UnicodeEncodeError" that would occur and ensure
        the character being displayed is correct between windows and linux.
        
        e.g. textLCD.setDisplayString(0, chr(223).encode("iso-8859-15"))
        
        Parameters:
            index<int>: the index of the row to write the string to.
            string<string>: the string to display.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the row index is invalid.
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetTextLCD_setDisplayString(self.handle, c_int(index), c_char_p(string))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def setCustomCharacter(self, index, part1, part2):
        """Sets a custom character.
        
        You can set up to 8 (0-7) custom characters, each one is completely defined by two integers,
        and gets stored in the character display until power is removed, whence they must be re-programmed.
        
        See TextLCD-simple.py for an example of how this works.
        
        Parameters:
            index<int>: custom character list index.
            part1<int>: first half of the character code.
            part2<int>: second half of the character code.
        
        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached, or if the index is invalid.
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetTextLCD_setCustomCharacter(self.handle, c_int(index + 8), c_int(part1), c_int(part2))
        except RuntimeError:
            raise
        
        if result > 0:
            raise PhidgetException(result)

    def getCustomCharacter(self, index):
        """Returns the custom character location in the ascii character storage space in the TextLCD
        
        This returns the hex representation of the actual index location into the ascii character table where
        the custom character is stored.  This function can be called and the result sent to the setDisplayString function
        to display the custom character.
        
        See TextLCD-simple.py for an example of how this works.
        
        Parameters:
            index<int>: custom character list index.
        
        Returns:
            The Stringcode at the specified index (hex format) <string>.
        
        Exceptions:
            IndexError: If the supplied index is out of range.
        """
        if index == 0:
            return "\010"
        elif index == 1:
            return "\011"
        elif index == 2:
            return "\012"
        elif index == 3:
            return "\013"
        elif index == 4:
            return "\014"
        elif index == 5:
            return "\015"
        elif index == 6:
            return "\016"
        elif index == 7:
            return "\017"
        else:
            message = "Index value %i is out of range" % index
            raise IndexError(message)

    def getScreenCount(self):
        """Gets the number of Display supported by this TextLCD

        Returns:
            The number of supported screens <int>.

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        screenCount = c_int()

        try:
            result = PhidgetLibrary.getDll().CPhidgetTextLCD_getScreenCount(self.handle, byref(screenCount))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)
        else:
            return screenCount.value

    def getScreenIndex(self):
        """Gets the active screen.

        Returns:
            The active screen index <int>.

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        screenIndex = c_int()

        try:
            result = PhidgetLibrary.getDll().CPhidgetTextLCD_getScreen(self.handle, byref(screenIndex))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)
        else:
            return screenIndex.value

    def setScreenIndex(self, screenIndex):
        """Sets the active screen.

        This is the screen that all subsequent API calls will apply to.

        Parameters:
            screenIndex<int>: The desired active screen index.

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetTextLCD_setScreen(self.handle, c_int(screenIndex))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)

    def getScreenSize(self):
        """Gets the screen size.

        Returns:
            The screen size <int/TextLCD_ScreenSize>.

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        screenSize = c_int()

        try:
            result = PhidgetLibrary.getDll().CPhidgetTextLCD_getScreen(self.handle, byref(screenSize))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)
        else:
            return screenSize.value

    def setScreenSize(self, screenSize):
        """Sets the active screen size.

        Only supported on the TextLCD Adapter.

        Parameters:
            screenIndex<int/TextLCD_ScreenSize>: The desired active screen index.

        Exceptions:
            RuntimeError - If current platform is not supported/phidget c dll cannot be found
            PhidgetException: If this Phidget is not opened and attached.
        """
        try:
            result = PhidgetLibrary.getDll().CPhidgetTextLCD_setScreenSize(self.handle, c_int(screenSize))
        except RuntimeError:
            raise

        if result > 0:
            raise PhidgetException(result)
