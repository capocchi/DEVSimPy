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

"""pyXLWriter.Workbook

Used in conjunction with pyXLWriter.

"""
__revision__ = """$Id: Workbook.py,v 1.28 2004/08/20 05:16:16 fufff Exp $"""

import re
from struct import pack
from BIFFWriter import BIFFWriter
from OLEWriter import OLEWriter
from OLEWriterBig import OLEWriterBig
from Format import Format
from Formula import Formula
from Worksheet import Worksheet


class Workbook(BIFFWriter):
    """Workbook - A writer class for Excel Workbooks."""

    def __init__(self, workfile, big=False):
        """Constructor."""
        BIFFWriter.__init__(self)
        tmp_format = Format()
        parser = Formula()
        self._file = workfile
        self._parser = parser
        self._1904 = 0
        self._activesheet = 0
        self._firstsheet = 0
        self._selected = 0
        self._xf_index = 16     # 15 style XF's and 1 cell XF.
        self._fileclosed = False
        self._biffsize = 0
        self._sheetname = "Sheet"
        self._tmp_format = tmp_format
        self._codepage = 0x04E4
        self._worksheets = []
        self._sheetnames = []
        self._formats = []
        self._palette = []
        self._big = big
        
        # Add the default format for hyperlinks and others...
        self._url_format = self.add_format(color="blue", underline=1)
        self._date_format = self.add_format()
        self._date_format.set_num_format("d mmmm yyy")
        self._time_format = self.add_format()
        self._time_format.set_num_format("HH:MM:SS")
        self._datetime_format = self.add_format()
        self._datetime_format.set_num_format("d mmmm yyy HH:MM:SS")
        
        # Set colour palette.
        self.set_palette_xl97()

    def close(self):
        """Calls finalization methods and explicitly close the OLEwriter file
        handle.

        """
        try:
            if not self._fileclosed: # Prevent close() from being called twice.
                self._fileclosed = True
                self._store_workbook()
        finally:
            for sheet in self._worksheets:
                sheet._close_tmp()
            self._worksheets = [] # Simple fix memory leak :/

    #~ def __del__(self):
        #~ """Close the workbook if it hasn't already been explicitly closed."""
        #~ if not self._fileclosed:
            #~ self.close()

    def sheets(self):
        """An accessor for the _worksheets[] array

        Returns: a list of the worksheet objects in a workbook

        """
        return self._worksheets

    def worksheets(self):
        """An accessor for the _worksheets[] array.
        This method is now deprecated. Use the sheets() method instead.

        Returns: an array reference

        """
        return self._worksheets

    def add_worksheet(self, name=""):
        """Add a new worksheet to the Excel workbook.
        TODO: Add accessor for self._sheetname for international Excel versions.

        Returns: reference to a worksheet object

        """
        # Check that sheetname is <= 31 chars (Excel limit).
        if len(name) > 31:
            raise Exception("Sheetname %s must be <= 31 chars" % (name))
        # Check that sheetname doesn't contain any invalid characters
        if re.match(r"[:*?/\\]", name):
            raise Exception(r"Invalid Excel character [:*?/\\] in worksheet name: %s" % (name))
        index = len(self._worksheets)
        sheetname = self._sheetname
        if (name == ""):
            name = sheetname + str(index+1)
        # Check that the worksheet name doesn't already exist: a fatal Excel error.
        for tmp in self._worksheets:
            if name == tmp.get_name():
                raise Exception("Worksheet %s already exists" % (name))
        # Porters take note, the following scheme of passing references to Workbook
        # data (in the self._foo cases) instead of a reference to the Workbook
        # itself is a workaround to avoid circular references between Workbook and
        # Worksheet objects. Feel free to implement this in any way the suits your
        # language.
        #
        init_data = (
                     name,
                     self,
                     index,
                     #self._url_format,
                     self._parser,
                    )
        worksheet = Worksheet(*init_data)
        self._worksheets.append(worksheet)          # Store ref for iterator
        self._sheetnames.append(name)               # Store EXTERNSHEET names
        self._parser.set_ext_sheets(name, index)    # Store names in Formula.pm
        return worksheet
    
    def activate_sheet(self, sheet):
        """
            TODO:
        """
        sheet.select()
        self._activesheet = sheet.get_index()
    
    def set_first_sheet(self, sheet):
        """
            TODO:
        """
        self._firstsheet = sheet.get_index()
        
    def add_format(self, **properties):
        """Add a new format to the Excel workbook. This adds an XF record and
        a FONT record. Also, pass any properties to the Format::new().

        """
        format = Format(self._xf_index, **properties)
        self._xf_index += 1
        self._formats.append(format)
        return format

    def get_default_url_format(self):
        """Get default url format. It's used by worksheet.write_url() when 
        format is not defined.
        
        """
        return self._url_format
    
    def get_default_date_format(self):
        """Get default date format."""
        return self._date_format
        
    def get_default_time_format(self):
        """Get default time format."""
        return self._time_format
        
    def get_default_datetime_format(self):
        """Get default datetime format."""
        return self._datetime_format
        
    def set_1904(self, dsys=None):
        """Set the date system: 0 = 1900 (the default), 1 = 1904"""
        if dsys is not None:
            self._1904 = dsys
        else:
            self._1904 = 1

    def get_1904(self):
        """Return the date system: 0 = 1900, 1 = 1904"""
        return self._1904

    def set_custom_color(self, index, red, green=0, blue=0):
        """Change the RGB components of the elements in the colour palette."""
        if isinstance(red, str):
            # Match a HTML #xxyyzz style parameter
            res = re.match(r"^#(\w\w)(\w\w)(\w\w)", red)
            if (res):
                red, green, blue = [int(cn, 16) for cn in res.groups([1, 2, 3])]
        palette = self._palette
        # Check that the colour index is the right range
        if (index < 8 or index > 64):
            raise "Color index index outside range: 8 <= index <= 64"
        # Check that the colour components are in the right range
        if ( (red < 0 or red > 255) or \
                 (green < 0 or green > 255) or \
                 (blue < 0 or blue > 255) ):
            raise "Color component outside range: 0 <= color <= 255"
        index -= 8  # Adjust colour index (wingless dragonfly)
        # Set the RGB value
        palette[index] = [red, green, blue, 0x00]
        return index + 8

    def set_palette_xl97(self):
        """Sets the colour palette to the Excel 97+ default."""
        self._palette = [
            [0x00, 0x00, 0x00, 0x00],   # 8
            [0xff, 0xff, 0xff, 0x00],   # 9
            [0xff, 0x00, 0x00, 0x00],   # 10
            [0x00, 0xff, 0x00, 0x00],   # 11
            [0x00, 0x00, 0xff, 0x00],   # 12
            [0xff, 0xff, 0x00, 0x00],   # 13
            [0xff, 0x00, 0xff, 0x00],   # 14
            [0x00, 0xff, 0xff, 0x00],   # 15
            [0x80, 0x00, 0x00, 0x00],   # 16
            [0x00, 0x80, 0x00, 0x00],   # 17
            [0x00, 0x00, 0x80, 0x00],   # 18
            [0x80, 0x80, 0x00, 0x00],   # 19
            [0x80, 0x00, 0x80, 0x00],   # 20
            [0x00, 0x80, 0x80, 0x00],   # 21
            [0xc0, 0xc0, 0xc0, 0x00],   # 22
            [0x80, 0x80, 0x80, 0x00],   # 23
            [0x99, 0x99, 0xff, 0x00],   # 24
            [0x99, 0x33, 0x66, 0x00],   # 25
            [0xff, 0xff, 0xcc, 0x00],   # 26
            [0xcc, 0xff, 0xff, 0x00],   # 27
            [0x66, 0x00, 0x66, 0x00],   # 28
            [0xff, 0x80, 0x80, 0x00],   # 29
            [0x00, 0x66, 0xcc, 0x00],   # 30
            [0xcc, 0xcc, 0xff, 0x00],   # 31
            [0x00, 0x00, 0x80, 0x00],   # 32
            [0xff, 0x00, 0xff, 0x00],   # 33
            [0xff, 0xff, 0x00, 0x00],   # 34
            [0x00, 0xff, 0xff, 0x00],   # 35
            [0x80, 0x00, 0x80, 0x00],   # 36
            [0x80, 0x00, 0x00, 0x00],   # 37
            [0x00, 0x80, 0x80, 0x00],   # 38
            [0x00, 0x00, 0xff, 0x00],   # 39
            [0x00, 0xcc, 0xff, 0x00],   # 40
            [0xcc, 0xff, 0xff, 0x00],   # 41
            [0xcc, 0xff, 0xcc, 0x00],   # 42
            [0xff, 0xff, 0x99, 0x00],   # 43
            [0x99, 0xcc, 0xff, 0x00],   # 44
            [0xff, 0x99, 0xcc, 0x00],   # 45
            [0xcc, 0x99, 0xff, 0x00],   # 46
            [0xff, 0xcc, 0x99, 0x00],   # 47
            [0x33, 0x66, 0xff, 0x00],   # 48
            [0x33, 0xcc, 0xcc, 0x00],   # 49
            [0x99, 0xcc, 0x00, 0x00],   # 50
            [0xff, 0xcc, 0x00, 0x00],   # 51
            [0xff, 0x99, 0x00, 0x00],   # 52
            [0xff, 0x66, 0x00, 0x00],   # 53
            [0x66, 0x66, 0x99, 0x00],   # 54
            [0x96, 0x96, 0x96, 0x00],   # 55
            [0x00, 0x33, 0x66, 0x00],   # 56
            [0x33, 0x99, 0x66, 0x00],   # 57
            [0x00, 0x33, 0x00, 0x00],   # 58
            [0x33, 0x33, 0x00, 0x00],   # 59
            [0x99, 0x33, 0x00, 0x00],   # 60
            [0x99, 0x33, 0x66, 0x00],   # 61
            [0x33, 0x33, 0x99, 0x00],   # 62
            [0x33, 0x33, 0x33, 0x00],   # 63
        ]
        return 0

    def set_palette_xl5(self):
        """Sets the colour palette to the Excel 5 default."""
        self._palette = [
            [0x00, 0x00, 0x00, 0x00],   # 8
            [0xff, 0xff, 0xff, 0x00],   # 9
            [0xff, 0x00, 0x00, 0x00],   # 10
            [0x00, 0xff, 0x00, 0x00],   # 11
            [0x00, 0x00, 0xff, 0x00],   # 12
            [0xff, 0xff, 0x00, 0x00],   # 13
            [0xff, 0x00, 0xff, 0x00],   # 14
            [0x00, 0xff, 0xff, 0x00],   # 15
            [0x80, 0x00, 0x00, 0x00],   # 16
            [0x00, 0x80, 0x00, 0x00],   # 17
            [0x00, 0x00, 0x80, 0x00],   # 18
            [0x80, 0x80, 0x00, 0x00],   # 19
            [0x80, 0x00, 0x80, 0x00],   # 20
            [0x00, 0x80, 0x80, 0x00],   # 21
            [0xc0, 0xc0, 0xc0, 0x00],   # 22
            [0x80, 0x80, 0x80, 0x00],   # 23
            [0x80, 0x80, 0xff, 0x00],   # 24
            [0x80, 0x20, 0x60, 0x00],   # 25
            [0xff, 0xff, 0xc0, 0x00],   # 26
            [0xa0, 0xe0, 0xe0, 0x00],   # 27
            [0x60, 0x00, 0x80, 0x00],   # 28
            [0xff, 0x80, 0x80, 0x00],   # 29
            [0x00, 0x80, 0xc0, 0x00],   # 30
            [0xc0, 0xc0, 0xff, 0x00],   # 31
            [0x00, 0x00, 0x80, 0x00],   # 32
            [0xff, 0x00, 0xff, 0x00],   # 33
            [0xff, 0xff, 0x00, 0x00],   # 34
            [0x00, 0xff, 0xff, 0x00],   # 35
            [0x80, 0x00, 0x80, 0x00],   # 36
            [0x80, 0x00, 0x00, 0x00],   # 37
            [0x00, 0x80, 0x80, 0x00],   # 38
            [0x00, 0x00, 0xff, 0x00],   # 39
            [0x00, 0xcf, 0xff, 0x00],   # 40
            [0x69, 0xff, 0xff, 0x00],   # 41
            [0xe0, 0xff, 0xe0, 0x00],   # 42
            [0xff, 0xff, 0x80, 0x00],   # 43
            [0xa6, 0xca, 0xf0, 0x00],   # 44
            [0xdd, 0x9c, 0xb3, 0x00],   # 45
            [0xb3, 0x8f, 0xee, 0x00],   # 46
            [0xe3, 0xe3, 0xe3, 0x00],   # 47
            [0x2a, 0x6f, 0xf9, 0x00],   # 48
            [0x3f, 0xb8, 0xcd, 0x00],   # 49
            [0x48, 0x84, 0x36, 0x00],   # 50
            [0x95, 0x8c, 0x41, 0x00],   # 51
            [0x8e, 0x5e, 0x42, 0x00],   # 52
            [0xa0, 0x62, 0x7a, 0x00],   # 53
            [0x62, 0x4f, 0xac, 0x00],   # 54
            [0x96, 0x96, 0x96, 0x00],   # 55
            [0x1d, 0x2f, 0xbe, 0x00],   # 56
            [0x28, 0x66, 0x76, 0x00],   # 57
            [0x00, 0x45, 0x00, 0x00],   # 58
            [0x45, 0x3e, 0x01, 0x00],   # 59
            [0x6a, 0x28, 0x13, 0x00],   # 60
            [0x85, 0x39, 0x6a, 0x00],   # 61
            [0x4a, 0x32, 0x85, 0x00],   # 62
            [0x42, 0x42, 0x42, 0x00],   # 63
        ]
        return 0
        
    def set_tempdir(self, tempdir):
        """Change the default temp directory used by _initialize() in Worksheet.pm."""
        raise NotImplementedError("use 'import tempfile; tempfile.tempdir=<tempdir>'")

        
    def set_codepage(self, codepage=1):
        """See also the _store_codepage method. This is used to store the code page, i.e.
        the character set used in the workbook.

        codepage = 1 - ANSI, MS Windows
        codepage = 2 - Apple Macintosh

        """
        if codepage == 1: codepage = 0x04E4
        if codepage == 2: codepage = 0x8000
        self._codepage = codepage

    def _store_workbook(self):
        """Assemble worksheets into a workbook and send the BIFF data to an OLE
        storage.

        """
        # Ensure that at least one worksheet has been selected.
        if (self._activesheet == 0) and (len(self._worksheets) > 0):
            self._worksheets[0]._selected = True
        # Calculate the number of selected worksheet tabs and call the finalization
        # methods for each worksheet
        for sheet in self._worksheets:
            if sheet._selected:
                self._selected += 1
            sheet._close(self._sheetnames)
        # Add Workbook globals
        self._store_bof(0x0005)
        self._store_codepage()
        self._store_externs()           # For print area and repeat rows
        self._store_names()             # For print area and repeat rows
        self._store_window1()
        self._store_1904()
        self._store_all_fonts()
        self._store_all_num_formats()
        self._store_all_xfs()
        self._store_all_styles()
        self._store_palette()
        self._calc_sheet_offsets()
        # Add BOUNDSHEET records
        for sheet in self._worksheets:
            self._store_boundsheet(sheet._name, sheet._offset)
        # End Workbook globals
        self._store_eof()
        # Store the workbook in an OLE container
        self._store_OLE_file()           
        
    def _store_OLE_file(self):
        """Store the workbook in an OLE container if the total size of the workbook data
        is less than ~ 7MB.

        """
        if not self._big and self._biffsize <= 7087104:
            # Write Worksheet data if data size <~ 7MB            
            ole = OLEWriter(self._file)
        else:
            ole = OLEWriterBig(self._file)
        ole.set_size(self._biffsize)
        ole.write_header()
        ole.write(self._data)
        for sheet in self._worksheets:
            while 1:
                tmp = sheet.get_data()
                if not tmp: break
                ole.write(tmp)
        ole.close()
            
    def _calc_sheet_offsets(self):
        """Calculate offsets for Worksheet BOF records."""
        BOF = 11
        EOF = 4
        offset = self._datasize
        for sheet in self._worksheets:
            offset += BOF + len(sheet._name)
        offset += EOF
        for sheet in self._worksheets:
            sheet._offset = offset
            offset += sheet._datasize
        self._biffsize = offset

    def _store_all_fonts(self):
        """Store the Excel FONT records."""
        # _tmp_format is added by new(). We use this to write the default XF's
        format = self._tmp_format
        font = format.get_font()
        # Note: Fonts are 0-indexed. According to the SDK there is no index 4,
        # so the following fonts are 0, 1, 2, 3, 5
        for i in xrange(1, 6):
            self._append(font)
        # Iterate through the XF objects and write a FONT record if it isn't the
        # same as the default FONT and if it hasn't already been used.
        fonts = {}
        index = 6                   # The first user defined FONT
        key = format.get_font_key() # The default font from _tmp_format
        fonts[key] = 0              # Index of the default font
        for format in self._formats:
            key = format.get_font_key()
            if fonts.has_key(key):
                # FONT has already been used
                format._font_index = fonts[key]
            else:
                # Add a new FONT record
                fonts[key] = index
                format._font_index = index
                index += 1
                font = format.get_font()
                self._append(font)

    def _store_all_num_formats(self):
        """Store user defined numerical formats i.e. FORMAT records."""
        # Leaning num_format syndrome
        num_formats = {}
        num_formats_ = []
        index = 164
        # Iterate through the XF objects and write a FORMAT record if it isn't a
        # built-in format type and if the FORMAT string hasn't already been used.
        for format in self._formats:
            num_format = format._num_format
            # Check if num_format is an index to a built-in format.
            # Also check for a string of zeros, which is a valid format string
            # but would evaluate to zero.
            if not re.match(r"^0+\d", num_format):
                if re.match(r"^\d+", num_format):
                    continue
            if num_formats.has_key(num_format):
                # FORMAT has already been used
                format._num_format = num_formats[num_format]
            else:
                # Add a new FORMAT
                num_formats[num_format] = index
                format._num_format = index
                num_formats_.append(num_format)
                index+=1
        # Write the new FORMAT records starting from 0xA4
        index = 164
        for num_format in num_formats_:
            self._store_num_format(num_format, index)
            index += 1

    def _store_all_xfs(self):
        """Write all XF records.

        """
        # _tmp_format is added by new(). We use this to write the default XF's
        # The default font index is 0
        format = self._tmp_format
        for i in xrange(0, 15):
            xf = format.get_xf('style')     # Style XF
            self._append(xf)
        xf = format.get_xf('cell')          # Cell XF
        self._append(xf)
        # User defined XFs
        for format in self._formats:
            xf = format.get_xf('cell')
            self._append(xf)

    def _store_all_styles(self):
        """Write all STYLE records."""
        self._store_style()

    def _store_externs(self):
        """Write the EXTERNCOUNT and EXTERNSHEET records. These are used as indexes for
        the NAME records.

        """
        # Create EXTERNCOUNT with number of worksheets
        self._store_externcount(len(self._worksheets))
        # Create EXTERNSHEET for each worksheet
        for sheetname in self._sheetnames:
            self._store_externsheet(sheetname)

    def _store_names(self):
        """Write the NAME record to define the print area and the repeat rows and cols."""
        # Create the print area NAME records
        for worksheet in self._worksheets:
            # Write a Name record if the print area has been defined
            if (worksheet._print_rowmin is not None):
                self._store_name_short(
                    worksheet._index,
                    0x06, # NAME type
                    worksheet._print_rowmin,
                    worksheet._print_rowmax,
                    worksheet._print_colmin,
                    worksheet._print_colmax)
        # Create the print title NAME records
        for worksheet in self._worksheets:
            rowmin = worksheet._title_rowmin
            rowmax = worksheet._title_rowmax
            colmin = worksheet._title_colmin
            colmax = worksheet._title_colmax
            # Determine if row + col, row, col or nothing has been defined
            # and write the appropriate record
            if ((rowmin is not None) and (colmin is not None)):
                # Row and column titles have been defined.
                # Row title has been defined.
                self._store_name_long(
                    worksheet._index,
                    0x07, # NAME type
                    rowmin,
                    rowmax,
                    colmin,
                    colmax)
            elif (rowmin is not None):
                # Row title has been defined.
                self._store_name_short(
                    worksheet._index,
                    0x07, # NAME type
                    rowmin,
                    rowmax,
                    0x00,
                    0xff)
            elif (colmin is not None):
                # Column title has been defined.
                self._store_name_short(
                    worksheet._index,
                    0x07, # NAME type
                    0x0000,
                    0x3fff,
                    colmin,
                    colmax)
            else:
                # Print title hasn't been defined.
                pass

    ################################################################################
    #
    # BIFF RECORDS
    #
    def _store_window1(self):
        """Write Excel BIFF WINDOW1 record."""
        record = 0x003D                 # Record identifier
        length = 0x0012                 # Number of bytes to follow
        xWn = 0x0000                    # Horizontal position of window
        yWn = 0x0000                    # Vertical position of window
        dxWn = 0x25BC                   # Width of window
        dyWn = 0x1572                   # Height of window
        grbit = 0x0038                  # Option flags
        ctabsel = self._selected        # Number of workbook tabs selected
        wTabRatio = 0x0258              # Tab to scrollbar ratio
        itabFirst = self._firstsheet    # 1st displayed worksheet
        itabCur = self._activesheet     # Active worksheet
        header = pack("<HH", record, length)
        data = pack("<HHHHHHHHH", xWn, yWn, dxWn, dyWn,
                                  grbit,
                                  itabCur, itabFirst,
                                  ctabsel, wTabRatio)
        self._append(header, data)

    def _store_boundsheet(self, sheetname, offset):
        """Writes Excel BIFF BOUNDSHEET record.

        sheetname - Worksheet name
        offset    - Location of worksheet BOF

        """
        record = 0x0085                # Record identifier
        length = 0x07 + len(sheetname) # Number of bytes to follow
        grbit = 0x0000                 # Sheet identifier
        cch = len(sheetname)           # Length of sheet name
        header = pack("<HH", record, length)
        data = pack("<LHB", offset, grbit, cch) #"VvC"
        self._append(header, data, sheetname)

    def _store_style(self):
        """Write Excel BIFF STYLE records."""
        record = 0x0293  # Record identifier
        length = 0x0004  # Bytes to follow
        ixfe = 0x8000    # Index to style XF
        BuiltIn = 0x00   # Built-in style
        iLevel = 0xff    # Outline style level
        header = pack("<HH",  record, length)
        data = pack("<HBB", ixfe, BuiltIn, iLevel)
        self._append(header, data)

    def _store_num_format(self, format, ifmt):
        """Writes Excel FORMAT record for non "built-in" numerical formats.

        format - Custom format string
        ifmt   - Format index code

        """
        record = 0x041E                 # Record identifier
        #format = format
        length = 0x03 + len(format)     # Number of bytes to follow
        cch = len(format)               # Length of format string
        header = pack("<HH", record, length)
        data = pack("<HB", ifmt, cch)
        self._append(header, data, format)

    def _store_1904(self):
        """Write Excel 1904 record to indicate the date system in use."""
        record = 0x0022         # Record identifier
        length = 0x0002         # Bytes to follow
        f1904 = self._1904 # Flag for 1904 date system
        header = pack("<HH", record, length)
        data = pack("<H", f1904)
        self._append(header, data)

    def _store_externcount(self, count):
        """Write BIFF record EXTERNCOUNT to indicate the number of external sheet
        references in the workbook.

        Excel only stores references to external sheets that are used in NAME.
        The workbook NAME record is required to define the print area and the repeat
        rows and columns.

        A similar method is used in Worksheet.pm for a slightly different purpose.

        """
        record = 0x0016           # Record identifier
        length = 0x0002           # Number of bytes to follow
        cxals = count             # Number of external references
        header = pack("<HH", record, length)
        data = pack("<H",  cxals)
        self._append(header, data)

    def _store_externsheet(self, sheetname):
        """Writes the Excel BIFF EXTERNSHEET record. These references are used by
        formulas. NAME record is required to define the print area and the repeat
        rows and columns.

        A similar method is used in Worksheet.pm for a slightly different purpose.

        sheetname - Worksheet name

        """
        record = 0x0017               # Record identifier
        length = 0x02 + len(sheetname) # Number of bytes to follow
        cch = len(sheetname)   # Length of sheet name
        rgch = 0x03                 # Filename encoding
        header = pack("<HH", record, length)
        data = pack("<BB", cch, rgch)
        self._append(header, data, sheetname)

    def _store_name_short(self, index, type, rowmin, rowmax, colmin, colmax):
        """Store the NAME record in the short format that is used for storing the print
        area, repeat rows only and repeat columns only.

        index  - Sheet index
        type   -

        rowmin - Start row
        rowmax - End row
        colmin - Start column
        colmax - end column

        """
        record = 0x0018       # Record identifier
        length = 0x0024       # Number of bytes to follow
        grbit = 0x0020        # Option flags
        chKey = 0x00          # Keyboard shortcut
        cch = 0x01            # Length of text name
        cce = 0x0015          # Length of text definition
        ixals = index +1      # Sheet index
        itab = ixals          # Equal to ixals
        cchCustMenu = 0x00    # Length of cust menu text
        cchDescription = 0x00 # Length of description text
        cchHelptopic = 0x00   # Length of help topic text
        cchStatustext = 0x00  # Length of status bar text
        rgch = type           # Built-in name type
        unknown03 = 0x3b
        unknown04 = 0xffff-index
        unknown05 = 0x0000
        unknown06 = 0x0000
        unknown07 = 0x1087
        unknown08 = 0x8005
        header = pack("<HH", record, length)
        data = pack("<H", grbit)
        data += pack("<B", chKey)
        data += pack("<B", cch)
        data += pack("<H", cce)
        data += pack("<H", ixals)
        data += pack("<H", itab)
        data += pack("<B", cchCustMenu)
        data += pack("<B", cchDescription)
        data += pack("<B", cchHelptopic)
        data += pack("<B", cchStatustext)
        data += pack("<B", rgch)
        data += pack("<B", unknown03)
        data += pack("<H", unknown04)
        data += pack("<H", unknown05)
        data += pack("<H", unknown06)
        data += pack("<H", unknown07)
        data += pack("<H", unknown08)
        data += pack("<H", index)
        data += pack("<H", index)
        data += pack("<H", rowmin)
        data += pack("<H", rowmax)
        data += pack("<B", colmin)
        data += pack("<B", colmax)
        self._append(header, data)

    def _store_name_long(self, index, type, rowmin, rowmax, commin, commax):
        """Store the NAME record in the long format that is used for storing the repeat
        rows and columns when both are specified. This share a lot of code with
        _store_name_short() but we use a separate method to keep the code clean.
        Code abstraction for reuse can be carried too far, and I should know. -)

        index   -  Sheet index
        type

        rowmin  -  Start row
        rowmax  -  End row
        colmin  -  Start column
        colmax  -  end column

        """
        record = 0x0018         # Record identifier
        length = 0x003d         # Number of bytes to follow
        grbit = 0x0020          # Option flags
        chKey = 0x00            # Keyboard shortcut
        cch = 0x01              # Length of text name
        cce = 0x002e            # Length of text definition
        ixals = index +1        # Sheet index
        itab = ixals            # Equal to ixals
        cchCustMenu = 0x00      # Length of cust menu text
        cchDescription = 0x00   # Length of description text
        cchHelptopic = 0x00     # Length of help topic text
        cchStatustext = 0x00    # Length of status bar text
        rgch = type             # Built-in name type
        unknown01 = 0x29
        unknown02 = 0x002b
        unknown03 = 0x3b
        unknown04 = 0xffff-index
        unknown05 = 0x0000
        unknown06 = 0x0000
        unknown07 = 0x1087
        unknown08 = 0x8008
        header = pack("<HH",  record, length)
        data = pack("<H", grbit)
        data += pack("<B", chKey)
        data += pack("<B", cch)
        data += pack("<H", cce)
        data += pack("<H", ixals)
        data += pack("<H", itab)
        data += pack("<B", cchCustMenu)
        data += pack("<B", cchDescription)
        data += pack("<B", cchHelptopic)
        data += pack("<B", cchStatustext)
        data += pack("<B", rgch)
        data += pack("<B", unknown01)
        data += pack("<H", unknown02)
        # Column definition
        data += pack("<B", unknown03)
        data += pack("<H", unknown04)
        data += pack("<H", unknown05)
        data += pack("<H", unknown06)
        data += pack("<H", unknown07)
        data += pack("<H", unknown08)
        data += pack("<H", index)
        data += pack("<H", index)
        data += pack("<H", 0x0000)
        data += pack("<H", 0x3fff)
        data += pack("<B", colmin)
        data += pack("<B", colmax)
        # Row definition
        data += pack("<B", unknown03)
        data += pack("<H", unknown04)
        data += pack("<H", unknown05)
        data += pack("<H", unknown06)
        data += pack("<H", unknown07)
        data += pack("<H", unknown08)
        data += pack("<H", index)
        data += pack("<H", index)
        data += pack("<H", rowmin)
        data += pack("<H", rowmax)
        data += pack("<B", 0x00)
        data += pack("<B", 0xff)
        # End of data
        data += pack("<B", 0x10)
        self._append(header, data)

    def _store_palette(self):
        """Stores the PALETTE biff record."""
        aref = self._palette
        record = 0x0092           # Record identifier
        length = 2 + 4 * len(aref)   # Number of bytes to follow
        ccv = len(aref)   # Number of RGB values to follow
        # Pack the RGB data
        data = ""
        for pal in aref:
            data += pack("<BBBB", *pal)
        header = pack("<HHH", record, length, ccv)
        self._append(header, data)

    def _store_codepage(self):
        """Stores the CODEPAGE biff record."""
        record = 0x0042               # Record identifier
        length = 0x0002               # Number of bytes to follow
        cv = self._codepage   # The code page
        header = pack("<HH", record, length)
        data = pack("<H", cv)
        self._append(header, data)
