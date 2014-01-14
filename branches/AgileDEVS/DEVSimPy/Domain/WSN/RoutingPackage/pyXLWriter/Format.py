# pyXLWriter: A library for generating Excel Spreadsheets
# Copyright (c) 2004 Evgeny Filatov <fufff@users.sourceforge.net>
# Copyright (c) 2002-2004 John McNamara (Perl Spreadsheet::WriteExcel)
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 2.1 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser
# General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#----------------------------------------------------------------------------
# This module was written/ported from PERL Spreadsheet::WriteExcel module
# The author of the PERL Spreadsheet::WriteExcel module is John McNamara
# <jmcnamara@cpan.org>
#----------------------------------------------------------------------------
# See the README.txt distributed with pyXLWriter for more details.

"""pyXLWriter.Format

Used in conjunction with pyXLWriter.

"""
__revision__ = """$Id: Format.py,v 1.22 2004/08/20 05:16:16 fufff Exp $"""

import re
from struct import pack


class Format:
    """Format - A class for defining Excel formatting."""

    def __init__(self, xf_index=0, **properties):
        """Constructor."""
        self._xf_index = xf_index
        self._font_index = 0
        self._font = "Arial"
        self._size = 10
        self._bold = 0x0190
        self._italic = 0
        self._color = 0x7FFF
        self._underline = 0
        self._font_strikeout = 0
        self._font_outline = 0
        self._font_shadow = 0
        self._font_script = 0
        self._font_family = 0
        self._font_charset = 0
        self._num_format = "0"
        self._hidden = 0
        self._locked = 1
        self._text_h_align = 0
        self._text_wrap = 0
        self._text_v_align = 2
        self._text_justlast = 0
        self._rotation = 0
        self._fg_color = 0x40
        self._bg_color = 0x41
        self._pattern = 0
        self._bottom = 0
        self._top = 0
        self._left = 0
        self._right = 0
        self._bottom_color = 0x40
        self._top_color = 0x40
        self._left_color = 0x40
        self._right_color = 0x40
        self._merge_range = 0
        # Set properties passed to Workbook::addformat()
        if properties:
            self.set_properties(**properties)
            
    def assign(self, format):
        """Assing format parameters to current format object.
        
        In original library this method has name 'copy'. 
        
        """
        xf = self._xf_index       # Store XF index assigned by Workbook.pm
        self.__dict__.update(format.__dict__) # Copy properties
        self._xf_index = xf       # Restore XF index

    def get_xf(self, style=0):
        """Generate an Excel BIFF XF record.
        
        style - Style and other options
        
        """
        # Set the type of the XF record and some of the attributes.
        if style == "style":
            style = 0xFFF5
        else:
            style = self._locked
            style = style | (self._hidden << 1)
        # Flags to indicate if attributes have been set.
        atr_num = (self._num_format != "0")
        atr_fnt = (self._font_index != 0)
        if ((self._text_h_align != 0) or (self._text_v_align != 2) or
                (self._text_wrap != 0)):
            atr_alc = 1
        else:
            atr_alc = 0
        if ((self._bottom != 0) or (self._top != 0) or
                (self._left != 0) or (self._right != 0)):
            atr_bdr = 1
        else:
            atr_bdr = 0
        if ((self._fg_color != 0x40) or (self._bg_color != 0x41) or
                (self._pattern != 0x00)):
            atr_pat = 1
        else:
            atr_pat = 0
        if ((self._hidden != 0) or (self._locked != 1)):
            atr_prot = 1
        else:
            atr_prot = 0
        # Reset the default colours for the non-font properties
        if self._fg_color == 0x7FFF: 
            self._fg_color = 0x40
        if self._bg_color == 0x7FFF: 
            self._bg_color = 0x41
        if self._bottom_color == 0x7FFF: 
            self._bottom_color = 0x40
        if self._top_color == 0x7FFF: 
            self._top_color = 0x40
        if self._left_color == 0x7FFF: 
            self._left_color = 0x40
        if self._right_color == 0x7FFF: 
            self._right_color = 0x40
        # Zero the default border colour if the border has not been set.
        if self._bottom == 0: 
            self._bottom_color = 0
        if self._top == 0: 
            self._top_color = 0
        if self._right == 0: 
            self._right_color = 0
        if self._left == 0: 
            self._left_color = 0
        # The following 2 logical statements take care of special cases in relation
        # to cell colours and patterns:
        # 1. For a solid fill (_pattern == 1) Excel reverses the role of foreground
        #    and background colours.
        # 2. If the user specifies a foreground or background colour without a
        #    pattern they probably wanted a solid fill, so we fill in the defaults.
        if (self. _pattern <= 0x01 and self._bg_color != 0x41
                and self._fg_color == 0x40):
            self._fg_color = self._bg_color
            self._bg_color = 0x40
            self._pattern = 1
        if (self._pattern <= 0x01 and self._bg_color == 0x41 and
                self._fg_color != 0x40):
            self._bg_color = 0x40
            self._pattern = 1
        record = 0x00E0                     # Record identifier
        length = 0x0010                     # Number of bytes to follow
        ifnt = self._font_index             # Index to FONT record
        ifmt = int(float(self._num_format)) # Index to FORMAT record
        align = self._text_h_align          # Alignment
        align |= self._text_wrap << 3
        align |= self._text_v_align << 4
        align |= self._text_justlast << 7
        align |= self._rotation << 8
        align |= atr_num << 10
        align |= atr_fnt << 11
        align |= atr_alc << 12
        align |= atr_bdr << 13
        align |= atr_pat << 14
        align |= atr_prot << 15
        icv = self._fg_color                # fg and bg pattern colors
        icv |= self._bg_color << 7
        fill = self._pattern                # Fill and border line style
        fill |= self._bottom << 6
        fill |= self._bottom_color << 9
        border1 = self._top                 # Border line style and color
        border1 |= self._left << 3
        border1 |= self._right << 6
        border1 |= self._top_color << 9
        border2 = self._left_color          # Border color
        border2 |= self._right_color << 7
        header = pack("<HH", record, length)
        data = pack("<HHHHHHHH", ifnt, ifmt, style, align,
                                           icv, fill,
                                           border1, border2)

        return(header + data)

    def get_font(self):
        """Generate an Excel BIFF FONT record."""
        dyHeight = self._size * 20          # Height of font (1/20 of a point)
        icv = self._color                   # Index to color palette
        bls = self._bold                    # Bold style
        sss = self._font_script             # Superscript/subscript
        uls = self._underline               # Underline
        bFamily = self._font_family         # Font family
        bCharSet = self._font_charset       # Character set
        rgch = self._font                   # Font name
        cch = len(rgch)                     # Length of font name
        record = 0x31                       # Record identifier
        length = 0x0F + cch                 # Record length
        reserved = 0x00                     # Reserved
        grbit = 0x00                        # Font attributes
        if self._italic: grbit |= 0x02
        if self._font_strikeout: grbit |= 0x08
        if self._font_outline: grbit |= 0x10
        if self._font_shadow: grbit |= 0x20
        header  = pack("<HH", record, length)
        data = pack("<HHHHHBBBBB", dyHeight, grbit, icv, bls,    \
                                         sss, uls, bFamily,      \
                                         bCharSet, reserved, cch)
        return(header + data + self._font)

    def get_font_key(self):
        """Returns a unique hash key for a font. Used by Workbook->_store_all_fonts()"""
        # The following elements are arranged to increase the probability of
        # generating a unique key. Elements that hold a large range of numbers
        # eg. _color are placed between two binary elements such as _italic
        #
        key = self._font + str(self._size)
        key += str(self._font_script) + str(self._underline)
        key += str(self._font_strikeout) + str(self._bold) + repr(self._font_outline)
        key += str(self._font_family) + str(self._font_charset)
        key += str(self._font_shadow) + str(self._color) + repr(self._italic)
        key = re.sub(r" ", "_", key) # Convert the key to a single word
        return key

    def get_xf_index(self):
        """Returns the used by Worksheet._XF()"""
        return self._xf_index

    def _get_color(self, color=None):
        """Used in conjunction with the set_xxx_color methods to convert a color
        string into a number. Color range is 0..63 but we will restrict it
        to 8..63 to comply with Gnumeric. Colors 0..7 are repeated in 8..15.

        """
        colors = {
                "aqua": 0x0F,
                "cyan": 0x0F,
                "black": 0x08,
                "blue": 0x0C,
                "brown": 0x10,
                "magenta": 0x0E,
                "fuchsia": 0x0E,
                "gray": 0x17,
                "grey": 0x17,
                "green": 0x11,
                "lime": 0x0B,
                "navy": 0x12,
                "orange": 0x35,
                "purple": 0x14,
                "red": 0x0A,
                "silver": 0x16,
                "white": 0x09,
                "yellow": 0x0D,
                }
        # Return the default color, 0x7FFF, if undef,
        if color is None: return 0x7FFF
        # or the color string converted to an integer,
        if isinstance(color, str):
            color = color.lower()
            if colors.has_key(color):
                return colors[color]
        if isinstance(color, int):
            # or the default color if string is unrecognised,
            #return 0x7FFF if (_[0] =~ m/\D/)
            # or an index < 8 mapped into the correct range,
            if color < 8:
                return color + 8
            # or the default color if arg is outside range,
            if color > 63:
                return 0x7FFF
            # or an integer in the valid range
            return color
        return 0x7FFF

    def set_align(self, location=None):
        """Set cell alignment."""
        if location is None:
            return                 # No default
        if not isinstance(location, str):
            return    # Ignore numbers
        location = location.lower()
        if (location == 'left'):
            self.set_text_h_align(1)
        if (location == 'centre'):
            self.set_text_h_align(2)
        if (location == 'center'):
            self.set_text_h_align(2)
        if (location == 'right'):
            self.set_text_h_align(3)
        if (location == 'fill'):
            self.set_text_h_align(4)
        if (location == 'justify'):
            self.set_text_h_align(5)
        if (location == 'merge'):
            self.set_text_h_align(6)
        if (location == 'equal_space'):
            self.set_text_h_align(7)   # For T.K.
        if (location == 'top'):
            self.set_text_v_align(0)
        if (location == 'vcentre'):
            self.set_text_v_align(1)
        if (location == 'vcenter'):
            self.set_text_v_align(1)
        if (location == 'bottom'):
            self.set_text_v_align(2)
        if (location == 'vjustify'):
            self.set_text_v_align(3)
        if (location == 'vequal_space'):
            self.set_text_v_align(4)  # For T.K.

    def set_valign(self, location=None):
        """Set vertical cell alignment. This is required by the set_properties() method
        to differentiate between the vertical and horizontal properties.

        """
        self.set_align(location)

    def set_merge(self, tmp=None):
        """This is an alias for the unintuitive set_align('merge')"""
        self.set_text_h_align(6)

    def set_bold(self, weight=1):
        """Set bold format. Bold has a range 0x64..0x3E8 (100..1000).
        
        weight = 0 is mapped to 0x190 (400)      - text is normal,
        weight = 1 is mapped to 0x2BC (700)      - text is bold. 

        """
        assert isinstance(weight, (int, float, long))  # Must be numeric type
        if weight == 0: 
            self._bold = 0x190          # Normal text
        elif weight == 1: 
            self._bold = 0x2BC          # Bold text
        elif weight <  0x064: 
            self._bold = 0x64           # Lower bound
        elif weight >  0x3E8: 
            self._bold = 0x3E8          # Upper bound
        else: 
            self._bold = int(weight)    # Custom by user

    def set_border(self, style):
        """Set cells borders to the same style."""
        self.set_bottom(style)
        self.set_top(style)
        self.set_left(style)
        self.set_right(style)

    def set_border_color(self, color):
        """Set cells border to the same color."""
        self.set_bottom_color(color)
        self.set_top_color(color)
        self.set_left_color(color)
        self.set_right_color(color)

    def set_properties(self, **properties):
        """Convert hashes of properties to method calls."""
        for  key, value in properties.items():
            # Call method set_%s{key}(value)
            getattr(self,"set_" + key)(value)
            
    #######################################################################
    ## AUTOLOAD emulation - setting properties
    def set_font(self, font):
        self._font = font

    def set_size(self, size):
        self._size = size

    def set_italic(self, italic=1):
        self._italic = italic

    def set_color(self, color):
        self._color = self._get_color(color)

    def set_underline(self, underline=1):
        self._underline=underline

    def set_font_strikeout(self, font_strikeout=1):
        self._font_strikeout = font_strikeout

    def set_font_outline(self, font_outline=1):
        self._font_outline = font_outline

    def set_font_shadow(self, font_shadow=1):
        self._font_shadow = font_shadow

    def set_font_script(self, font_script=1):
        self._font_script = font_script

    def set_font_family(self, font_family=1):
        self._font_family = font_family

    def set_font_charset(self, font_charset=1):
        self._font_charset = font_charset

    def set_num_format(self, num_format=1):
        self._num_format = num_format

    def set_hidden(self, hidden=1):
        self._hidden = hidden

    def set_locked(self, locked=1):
        self._locked = locked

    def set_text_h_align(self, align):
        self._text_h_align = align

    def set_text_wrap(self, wrap=1):
        self._text_wrap = wrap

    def set_text_v_align(self, align):
        self._text_v_align = align

    def set_text_justlast(self, text_justlast=1):
        self._text_justlast = text_justlast

    def set_rotation(self, rotation=1):
        self._rotation = rotation

    def set_fg_color(self, color):
        self._fg_color = self._get_color(color)

    def set_bg_color(self, color):
        self._bg_color = self._get_color(color)

    def set_pattern(self, pattern=1):
        self._pattern = pattern

    def set_bottom(self, bottom=1):
        self._bottom = bottom

    def set_top(self, top=1):
        self._top = top

    def set_left(self, left=1):
        self._left = left

    def set_right(self, right=1):
         self._right = right

    def set_bottom_color(self, color):
        self._bottom_color = self._get_color(color)

    def set_top_color(self, color):
        self._top_color = self._get_color(color)

    def set_left_color(self, color):
        self._left_color = self._get_color(color)

    def set_right_color(self, color):
        self._right_color = self._get_color(color)
    
    def set_merge_range(self, range=True):
        self._merge_range = range