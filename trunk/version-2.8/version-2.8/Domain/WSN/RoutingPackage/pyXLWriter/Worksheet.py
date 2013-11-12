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

"""pyXLWriter.Worksheet

Used in conjunction with Spreadsheet::WriteExcel

"""
__revision__ = """$Id: Worksheet.py,v 1.42 2004/08/20 05:16:16 fufff Exp $"""

import os, os.path
import re
from struct import pack, unpack
import tempfile

# dt.datetime, dt.time, dt.date
# Distributed with python 2.3+
try:
    import datetime as dt
except ImportError:
    dt = None   

# mxdt.DateTime
# See: http://www.lemburg.com/files/python/eGenix-mx-Extensions.html
try:
    import mx.DateTime as mxdt
except ImportError:
    mxdt = None
            
from BIFFWriter import BIFFWriter
from Format import Format
from utilites import cell_to_rowcol2, cellrange_to_rowcol_pair


def _asc2ucs(s):
    """Convert ascii string to unicode."""
    return "\x00".join(s) + "\x00" 


class Worksheet(BIFFWriter):
    """Worksheet - A writer class for Excel Worksheets."""

    def __init__(self, name, workbook, index=0, parser=None):
        """Constructor."""
        BIFFWriter.__init__(self)
        rowmax = 65536    # 16384 in Excel 5
        colmax = 256
        strmax = 255
        self._name = name
        self._workbook = workbook
        self._index = index
        self._parser = parser
        self._ext_sheets = []
        self._using_tmpfile = True
        self._filehandle = None
        self._fileclosed = True
        self._offset = 0
        self._xls_rowmax = rowmax
        self._xls_colmax = colmax
        self._xls_strmax = strmax
        self._dim_rowmin = rowmax +1
        self._dim_rowmax = 0
        self._dim_colmin = colmax +1
        self._dim_colmax = 0
        self._dim_changed = 0
        self._colinfo = []
        self._selection = (0, 0, 0, 0)
        self._panes = []
        self._active_pane = 3
        self._frozen = False
        self._selected = 0
        self._paper_size = 0x0
        self._orientation = 0x1
        self._header = ''
        self._footer = ''
        self._hcenter = 0
        self._vcenter = 0
        self._margin_head = 0.50
        self._margin_foot = 0.50
        self._margin_left = 0.75
        self._margin_right = 0.75
        self._margin_top = 1.00
        self._margin_bottom = 1.00
        self._title_rowmin = None
        self._title_rowmax = None
        self._title_colmin = None
        self._title_colmax = None
        self._print_rowmin = None
        self._print_rowmax = None
        self._print_colmin = None
        self._print_colmax = None
        self._print_gridlines = 1
        self._screen_gridlines = 1
        self._print_headers = 0
        self._fit_page = 0
        self._fit_width = 0
        self._fit_height = 0
        self._hbreaks = []
        self._vbreaks = []
        self._protect = 0
        self._password = None
        self._col_sizes = {}
        self._row_sizes = {}
        self._col_formats = {}
        self._row_formats = {}
        self._zoom = 100
        self._print_scale = 100
        self._leading_zeros = 0
        self._outline_row_level = 0
        self._outline_style = 0
        self._outline_below = 1
        self._outline_right = 1
        self._outline_on = 1
        
        self._initialize()

    def _initialize(self):
        """Open a tmp file to store the majority of the Worksheet data. If this fails,
        for example due to write permissions, store the data in memory. This can be
        slow for large files.

        """
        self._filehandle = tempfile.TemporaryFile()
        self._fileclosed = False

    def _close(self, sheetnames):
        """Add data to the beginning of the workbook (note the reverse order)
        and to the end of the workbook.

        """
        num_sheets = len(sheetnames)
        ################################################
        # Prepend in reverse order!!
        #
        # Prepend the sheet dimensions
        self._store_dimensions()
        # Prepend the COLINFO records if they exist
        if (self._colinfo):
            while (self._colinfo):
                arrayref = self._colinfo.pop()
                self._store_colinfo(*arrayref)
            self._store_defcol()
        # Prepend the sheet password
        self._store_password()
        # Prepend the sheet protection
        self._store_protect()
        # Prepend EXTERNSHEET references
        for i in xrange(num_sheets, 0, -1):
            sheetname = sheetnames[i-1]
            self._store_externsheet(sheetname)
        # Prepend the EXTERNCOUNT of external references.
        self._store_externcount(num_sheets)
        # Prepend the page setup
        self._store_setup()
        # Prepend the bottom margin
        self._store_margin_bottom()
        # Prepend the top margin
        self._store_margin_top()
        # Prepend the right margin
        self._store_margin_right()
        # Prepend the left margin
        self._store_margin_left()
        # Prepend the page vertical centering
        self._store_vcenter()
        # Prepend the page horizontal centering
        self._store_hcenter()
        # Prepend the page footer
        self._store_footer()
        # Prepend the page header
        self._store_header()
        # Prepend the vertical page breaks
        self._store_vbreak()
        # Prepend the horizontal page breaks
        self._store_hbreak()
        # Prepend WSBOOL
        self._store_wsbool()
        # Prepend GUTS
        self._store_guts()
        # Prepend GRIDSET
        self._store_gridset()
        # Prepend PRINTGRIDLINES
        self._store_print_gridlines()
        # Prepend PRINTHEADERS
        self._store_print_headers()
        # Prepend the BOF record
        self._store_bof(0x0010)
        #
        # End of prepend. Read upwards from here.
        ################################################
        # Append
        self._store_window2()
        self._store_zoom()
        if (self._panes):
            self._store_panes(*self._panes)
        self._store_selection(*self._selection)
        self._store_eof()

    def get_name(self):
        """Retrieve the worksheet name.

        """
        return self._name

    def get_data(self):
        """Retrieves data from memory in one chunk, or from disk in buffer
        sized chunks.

        """
        buffer = 4096
        # Return data stored in memory
        if self._data:
            tmp = self._data
            self._data = None
            fh = self._filehandle
            if self._using_tmpfile:
                fh.seek(0, 0)
            return tmp
        # Return data stored on disk
        if self._using_tmpfile:
            tmp = self._filehandle.read(buffer)
            if tmp:
                return tmp
        # No data to return
        return None

    def select(self):
        """Set this worksheet as a selected worksheet, i.e. the worksheet has its tab
        highlighted.

        """
        self._selected = 1

    def get_index(self):
        """
            TODO:
        """
        return self._index
        
    def activate(self):
        """Set this worksheet as the active worksheet, i.e. the worksheet that is
        displayed when the workbook is opened. Also set it as selected.

        """
        self._workbook.activate_sheet(self)

    def set_first_sheet(self):
        """Set this worksheet as the first visible sheet. This is necessary
        when there are a large number of worksheets and the activated
        worksheet is not visible on the screen.

        """
        self._workbook.set_first_sheet(self)

    def protect(self, password=None):
        """Set the worksheet protection flag to prevent accidental modification and to
        hide formulas if the locked and hidden format properties have been set.

        """
        self._protect = 1
        if password is not None:
            self._password = self._encode_password(password)

    def set_column(self, colrange, width=0, format=None, hidden=False, level=None):
        """Set the width of a single column or a range of column.
        See also: _store_colinfo

        """
        row1, col1, row2, col2 = self._process_colrange(colrange)
        firstcol, lastcol = col1, col2
        self._colinfo.append([firstcol, lastcol, width, format, hidden, level])
        # Store the col sizes for use when calculating image vertices taking
        # hidden columns into account. Also store the column formats.
        if hidden:
            width = 0 # Set width to zero if column is hidden
        for col in xrange(firstcol, lastcol+1):
            self._col_sizes[col] = width
            if format is not None:
                self._col_formats[col] = format

    def set_selection(self, cellrange): #cells):
        """Set which cell or cells are selected in a worksheet: see also the
        sub _store_selection

        """
        self._selection = self._process_cellrange(cellrange)

    def freeze_panes(self, y=0, x=0, rwTop=None, colLeft=None, pnnAct=None): #cells):
        """Set panes and mark them as frozen. See also _store_panes(self)."""
        self._frozen = True
        self._panes = (y, x, rwTop, colLeft, pnnAct,)

    def thaw_panes(self, y=0, x=0, rwTop=None, colLeft=None, pnnAct=None): #cells):
        """Set panes and mark them as unfrozen. See also _store_panes(self)."""
        self._frozen = False
        self._panes = (y, x, rwTop, colLeft, pnnAct,)

    def set_portrait(self):
        """Set the page orientation as portrait."""
        self._orientation = 1

    def set_landscape(self):
        """Set the page orientation as landscape."""
        self._orientation = 0

    def set_paper(self, type=0):
        """Set the paper type. Ex. 1 = US Letter, 9 = A4"""
        self._paper_size = type

    def set_header(self, string="", margin=0.50):
        """Set the page header caption and optional margin."""
        if (len(string) >= 255):
            raise Exception("Header string must be less than 255 characters")
        self._header = string
        self._margin_head = margin

    def set_footer(self, string="", margin=0.50):
        """Set the page footer caption and optional margin."""
        if (len(string) >= 255):
            raise Exception("Footer string must be less than 255 characters")
        self._footer = string
        self._margin_foot = margin

    def center_horizontally(self, hcenter=1):
        """Center the page horinzontally."""
        self._hcenter = hcenter

    def center_vertically(self, vcenter=1):
        """Center the page horinzontally."""
        self._vcenter = vcenter

    def set_margins(self, margin):
        """Set all the page margins to the same value in inches."""
        self.set_margin_left(margin)
        self.set_margin_right(margin)
        self.set_margin_top(margin)
        self.set_margin_bottom(margin)

    def set_margins_LR(self, margin):
        """Set the left and right margins to the same value in inches."""
        self.set_margin_left(margin)
        self.set_margin_right(margin)

    def set_margins_TB(self, margin):
        """Set the top and bottom margins to the same value in inches."""
        self.set_margin_top(margin)
        self.set_margin_bottom(margin)

    def set_margin_left(self, margin=0.75):
        """Set the left margin in inches."""
        self._margin_left = margin

    def set_margin_right(self, margin=0.75):
        """Set the right margin in inches."""
        self._margin_right = margin

    def set_margin_top(self, margin=1.00):
        """Set the top margin in inches."""
        self._margin_top = margin

    def set_margin_bottom(self, margin=1.00):
        """Set the bottom margin in inches."""
        self._margin_bottom = margin

    def repeat_rows(self, rowrange):
        """Set the rows to repeat at the top of each printed page. See also the
        _store_name_xxxx() methods in Workbook.pm.

        """
        row1, col1, row2, col2 = self._process_rowrange(rowrange)
        self._title_rowmin, self._title_rowmax = row1, row2

    def repeat_columns(self, colrange):
        """Set the columns to repeat at the left hand side of each printed page.
        See also the _store_names() methods in Workbook.pm.

        """
        row1, col1, row2, col2 = self._process_colrange(colrange)
        self._title_colmin, self._title_colmax = col1, col2

    def print_area(self, cellrange):
        """Set the area of each worksheet that will be printed. See also the
        _store_names() methods in Workbook.pm.

        """
        row1, col1, row2, col2 = self._process_cellrange(cellrange)
        self._print_rowmin, self._print_colmin = row1, col1
        self._print_rowmax, self._print_colmax = row2, col2

    def hide_gridlines(self, option=1):
        """Set the option to hide gridlines on the screen and the printed page.
        There are two ways of doing this in the Excel BIFF format: The first is by
        setting the DspGrid field of the WINDOW2 record, this turns off the screen
        and subsequently the print gridline. The second method is to via the
        PRINTGRIDLINES and GRIDSET records, this turns off the printed gridlines
        only. The first method is probably sufficient for most cases. The second
        method is supported for backwards compatibility. Porters take note.

        option = 1  -  Default to hiding printed gridlines

        """
        if (option == 0):
            self._print_gridlines = 1  # 1 = display, 0 = hide
            self._screen_gridlines = 1
        elif (option == 1):
            self._print_gridlines = 0
            self._screen_gridlines = 1
        else:
            self._print_gridlines = 0
            self._screen_gridlines = 0

    def print_row_col_headers(self, print_headers=1):
        """Set the option to print the row and column headers on the printed page.
        See also the _store_print_headers() method below.

        """
        self._print_headers = print_headers

    def fit_to_pages(self, width=0, height=0):
        """Store the vertical and horizontal number of pages that will define the
        maximum area printed. See also _store_setup() and _store_wsbool() below.

        """
        self._fit_page = 1
        self._fit_width = width
        self._fit_height = height

    def set_h_pagebreaks(self, *breaks):
        """Store the horizontal page breaks on a worksheet."""
        self._hbreaks.extend(breaks)

    def set_v_pagebreaks(self, *breaks):
        """Store the vertical page breaks on a worksheet."""
        self._vbreaks.extend(breaks)

    def set_zoom(self, scale=100):
        """Set the worksheet zoom factor."""
        # Confine the scale to Excel's range
        if (scale < 10 or scale > 400):
            raise Exception("Zoom factor scale outside range: 10 <= zoom <= 400")
            scale = 100
        self._zoom = scale  #int(scale)

    def set_print_scale(self, scale=100):
        """Set the scale factor for the printed page."""
        # Confine the scale to Excel's range
        if (scale < 10 or scale > 400):
            raise Exception("Print scale scale outside range: 10 <= zoom <= 400")
            scale = 100
        # Turn off "fit to page" option
        self._fit_page = 0
        self._print_scale = scale #int(scale)

    def keep_leading_zeros(self, leading_zeros=1):
        """Causes the write() method to treat integers with a leading zero as a string.
        This ensures that any leading zeros such, as in zip codes, are maintained.

        """
        self._leading_zeros = leading_zeros

    def write(self, cell, token=None, format=None):
        """Parse token and call appropriate write method. row and column are zero
        indexed. format is optional.

        """
        if token is None:
            self.write_blank(cell, format)
        elif isinstance(token, tuple) or (isinstance(token, list)):
            self.write_row(cell, token, format)
        elif (isinstance(token, float) or (isinstance(token, int)
                or (isinstance(token, long)))):
            self.write_number(cell, token, format)
        elif ((dt and isinstance(token, (dt.datetime, dt.time, dt.date)))
               or (mxdt and isinstance(token, mxdt.DateTimeType))):
            self.write_date(cell, token, format)
        # Match integer with leading zero(s)
        elif (self._leading_zeros and (re.match(r"^0\d+$", token))):
            self.write_string(cell, token, format)
        elif re.match(r"^([+-]?)(?=\d|\.\d)\d*(\.\d*)?([Ee]([+-]?\d+))?$", token):
            self.write_number(cell, token, format)
        # Match http, https or ftp URL
        elif re.match(r"^[fh]tt?ps?://", token):
            self.write_url(cell, token, format=format)
        # Match mailto:
        elif re.match(r"^mailto:", token):
            self.write_url(cell, token, format=format)
        # Match internal or external sheet link
        elif re.match(r"^(?:in|ex)ternal:", token):
            self.write_url(cell, token, format=format)
        # Match formula
        elif re.match(r"^=", token):
            self.write_formula(cell, token, format)
        else:
            self.write_string(cell, token, format)

    def write_row(self, cell, tokens, format=None):
        """Write a row of data starting from (row, col). Call write_col() if any of
        the elements of the array ref are in turn array refs. This allows the writing
        of 1D or 2D arrays of data in one go.

        Returns: the first encountered error value or zero for no errors

        """
        row, col = self._process_cell(cell)
        error = 0
        for token in tokens:
            # Check for nested arrays
            if (isinstance(token, list) or isinstance(token, tuple)):
                ret = self.write_col((row, col), token, format)
            else:
                ret = self.write((row, col), token, format)
            # Return only the first error encountered, if any.
            error = error or ret
            col += 1
        return error

    def write_col(self, cell, tokens, format=None):
        """Write a column of data starting from (row, col). Call write_row() if any of
        the elements of the array ref are in turn array refs. This allows the writing
        of 1D or 2D arrays of data in one go.

        Returns: the first encountered error value or zero for no errors

        """
        row, col = self._process_cell(cell)
        error = 0
        for token in tokens:
            # write() will deal with any nested arrays
            ret = self.write((row, col), token, format)
            # Return only the first error encountered, if any.
            error = error or ret
            row += 1
        return error

    def write_comment(self, cell, comment):
        """write_comment(row, col, comment)

        Write a comment to the specified row and column (zero indexed). The maximum
        comment size is 30831 chars. Excel5 probably accepts 32k-1 chars. However, it
        can only display 30831 chars. Excel 7 and 2000 will crash above 32k-1.

        In Excel 5 a comment is referred to as a NOTE.

        Returns  0 : normal termination
                -1 : insufficient number of arguments
                -2 : row or column out of range
                -3 : long comment truncated to 30831 chars

        """
        row, col = self._process_cell(cell)
        str = comment
        strlen = len(comment)
        str_error = 0
        str_max = 30831
        note_max = 2048
        
        # Check that row and col are valid and store max and min values
        if self._check_dimensions(row, col):
            return -2
            
        # String must be <= 30831 chars
        if strlen > str_max:
            str = str[:str_max]
            strlen = str_max
            str_error = -3
        # A comment can be up to 30831 chars broken into segments of 2048 chars.
        # The first NOTE record contains the total string length. Each subsequent
        # NOTE record contains the length of that segment.
        #
        #comment = substr(str, 0, note_max, '')
        comment = str[0:note_max]
        str = str[note_max:]
        self._store_comment(row, col, comment, strlen) # First NOTE
        # Subsequent NOTE records
        while str:
            #comment = substr(str, 0, note_max, '')
            comment = str[0:note_max]
            str = str[note_max:]
            strlen  = len(comment)
            # Row is -1 to indicate a continuation NOTE
            self._store_comment(-1, 0, comment, strlen)
        return str_error

    def _XF(self, row, col, format=None):
        """Returns an index to the XF record in the workbook.

        Note: this is a function, not a method.

        """
        if (isinstance(format, Format)):
            return format._xf_index
        elif self._row_formats.has_key(row):
            return self._row_formats[row]._xf_index
        elif self._col_formats.has_key(col):
            return self._col_formats[col]._xf_index
        else:
            return 0x0F

    ###############################################################################
    ###############################################################################
    #
    # Internal methods
    def _append(self, *args):
        """Store Worksheet data in memory using the base class _append() or to a
        temporary file, the default.

        """
        if (self._using_tmpfile):
            data = "".join(args)  
            # Add CONTINUE records if necessary
            if len(data) > self._limit:
                data = self._add_continue(data)
            self._filehandle.write(data)
            self._datasize += len(data)
        else:
            BIFFWriter._append(self, *args)

    def _sort_pagebreaks(self, *breaks):
        """This is an internal method that is used to filter elements of the array of
        pagebreaks used in the _store_hbreak() and _store_vbreak() methods. It:
          1. Removes duplicate entries from the list.
          2. Sorts the list.
          3. Removes 0 from the list if present.

        """
        hash = {}
        array = []
        for key in breaks:    # Hash slice to remove duplicates
            hash[key] = True
        array = hash.keys()
        array.sort()
        if array[0] == 0:
            del arrya[0]      # Remove zero
        # 1000 vertical pagebreaks appears to be an internal Excel 5 limit.
        # It is slightly higher in Excel 97/200, approx. 1026
        if len(array) > 1000:
            del array[1000:len(array)]
        return array

    def _encode_password(self, plaintext):
        """Based on the algorithm provided by Daniel Rentz of OpenOffice."""
        i = 0
        chars = list(plaintext)
        count = len(chars)
        for char in chars:
            i += 1
            char = ord(char) << i
            low_15 = char & 0x7fff
            high_15 = char & 0x7fff << 15
            high_15 = high_15 >> 15
            char = low_15 | high_15
        password = 0x0000
        for char in chars:
            password ^= char
        password ^= count
        password ^= 0xCE4B
        return password

    def  outline_settings(self, visible=1, symbols_below=1, symbols_right=1, auto_style=0):
        """outline_settings(visible, symbols_below, symbols_right, auto_style)

        This method sets the properties for outlining and grouping. The defaults
        correspond to Excel's defaults.

        """
        self._outline_on = visible
        self._outline_below = symbols_below
        self._outline_right = symbols_right
        self._outline_style = auto_style
        # Ensure this is a boolean vale for Window2
        if self._outline_on:
            self._outline_on = 1

    ###############################################################################
    #
    # BIFF RECORDS
    def write_number(self, cell, num, format=None):
        """Write a double to the specified row and column (zero indexed).
        An integer can be written as a double. Excel will display an
        integer. format is optional.

        Returns  0 : normal termination
                -1 : insufficient number of arguments
                -2 : row or column out of range

        row - Zero indexed row
        col - Zero indexed column

        """
        row, col = self._process_cell(cell)
        record = 0x0203               # Record identifier
        length = 0x000E               # Number of bytes to follow
        xf = self._XF(row, col, format)   # The cell format
        # Check that row and col are valid and store max and min values
        if self._check_dimensions(row, col):
            return -2
        header = pack("<HH", record, length)
        data = pack("<HHH", row, col, xf)
        xl_double = pack("<d", float(num))
        self._append(header, data, xl_double)
        return 0

    def write_string(self, cell, str, format=None):
        """Write a string to the specified row and column (zero indexed).
        NOTE: there is an Excel 5 defined limit of 255 characters.
        format is optional.
        Returns  0 : normal termination
                -1 : insufficient number of arguments
                -2 : row or column out of range
                -3 : long string truncated to 255 chars

        row - zero indexed row
        col - zero indexed column

        """
        row, col = self._process_cell(cell)
        record = 0x0204               # Record identifier
        length = 0x0008 + len(str)    # Bytes to follow
        strlen = len(str)
        xf = self._XF(row, col, format)   # The cell format
        str_error = 0
        # Check that row and col are valid and store max and min values
        if self._check_dimensions(row, col):
            #raise Exception("row and col not valid")
            return -2
        if (strlen > self._xls_strmax): # LABEL must be < 255 chars
            str = str[0:self._xls_strmax]
            length = 0x0008 + self._xls_strmax
            strlen = self._xls_strmax
            str_error = -3
        header = pack("<HH", record, length)
        data = pack("<HHHH", row, col, xf, strlen)
        self._append(header, data, str)
        return str_error

    def write_blank(self, cell, format=None):
        """Write a blank cell to the specified row and column (zero indexed).
        A blank cell is used to specify formatting without adding a string
        or a number.

        A blank cell without a format serves no purpose. Therefore, we don't write
        a BLANK record unless a format is specified. This is mainly an optimisation
        for the write_row() and write_col() methods.

        Returns  0 : normal termination (including no format)
                -1 : insufficient number of arguments
                -2 : row or column out of range

        row - zero indexed row
        col - zero indexed column

        """
        row, col = self._process_cell(cell)
        # Don't write a blank cell unless it has a format
        if format is None: return 0
        record = 0x0201               # Record identifier
        length = 0x0006               # Number of bytes to follow
        xf = self._XF(row, col, format)   # The cell format
        # Check that row and col are valid and store max and min values
        if self._check_dimensions(row, col):
            return -2
        header = pack("<HH", record, length)
        data = pack("<HHH", row, col, xf)
        self._append(header, data)
        return 0

    def write_formula(self, cell, formula, format=None):
        """Write a formula to the specified row and column (zero indexed).
        The textual representation of the formula is passed to the parser in
        Formula.pm which returns a packed binary string.

        Returns  0 : normal termination
                -1 : insufficient number of arguments
                -2 : row or column out of range

        row - zero indexed row
        col - zero indexed column

        """
        row, col = self._process_cell(cell)
        record = 0x0006  # Record identifier
        # length -  Bytes to follow
        # Excel normally stores the last calculated value of the formula in num.
        # Clearly we are not in a position to calculate this a priori. Instead
        # we set num to zero and set the option flags in grbit to ensure
        # automatic calculation of the formula when the file is opened.
        #
        xf = self._XF(row, col, format) # The cell format
        num = 0x00    # Current value of formula
        grbit = 0x03  # Option flags
        chn = 0x0000  # Must be zero
        # Check that row and col are valid and store max and min values
        if self._check_dimensions(row, col):
            return -2
        # In order to raise formula errors from the point of view of the calling
        # program we use an eval block and re-raise the error from here.
        formula = self._parser.parse_formula(formula)
        formlen = len(formula)    # Length of the binary string
        length = 0x16 + formlen   # Length of the record data
        header = pack("<HH", record, length)
        data = pack("<HHHdHLH", row, col, xf, num, grbit, chn, formlen)
        self._append(header, data, formula)
        return 0

    def store_formula(self, formula):
        """Pre-parse a formula. This is used in conjunction with repeat_formula()
        to repetitively rewrite a formula without re-parsing it.

        """
        # In order to raise formula errors from the point of view of the calling
        # program we use an eval block and re-raise the error from here.
        tokens = self._parser.preparse_formula(formula)
        # Return the parsed tokens in an anonymous array
        return tokens

    def repeat_formula(self, cell, formula_ref, format=None, patterns=None): 
        """Write a formula to the specified row and column (zero indexed) by
        substituting pattern replacement pairs in the formula created via
        store_formula(). This allows the user to repetitively rewrite a formula
        without the significant overhead of parsing.

        Returns  0 : normal termination
                -1 : insufficient number of arguments
                -2 : row or column out of range

        """
        row, col = self._process_cell(cell)
        record = 0x0006           # Record identifier
        # length -  Bytes to follow
        # formula_ref = forumla_ref     # Array ref with formula tokens
        # Check that formula is an array ref
        if not isinstance(formula_ref, list) and not isinstance(formula_ref, tuple):
            raise Exception("Not a valid formula")
        tokens = formula_ref[:]
        for pattern, replace in patterns:
            for i in xrange(len(tokens)):
                token = str(tokens[i])
                if re.search(pattern, token):
                    tokens[i] = re.sub(pattern, replace, str(token))
        # Change the parameters in the formula cached by the Formula.pm object
        formula = self._parser.parse_tokens(tokens)
        if not formula:
            raise Exception("Unrecognised token in formula")
        # Excel normally stores the last calculated value of the formula in num.
        # Clearly we are not in a position to calculate this a priori. Instead
        # we set num to zero and set the option flags in grbit to ensure
        # automatic calculation of the formula when the file is opened.
        #
        xf = self._XF(row, col, format) # The cell format
        num = 0x00                      # Current value of formula
        grbit = 0x03                    # Option flags
        chn = 0x0000                    # Must be zero
        # Check that row and col are valid and store max and min values
        if self._check_dimensions(row, col):
            return -2
        formlen  = len(formula)         # Length of the binary string
        length = 0x16 + formlen         # Length of the record data
        header = pack("<HH", record, length)
        data = pack("<HHHdHLH", row, col, xf, num, grbit, chn, formlen)
        self._append(header, data, formula)
        return 0

    def write_date(self, cell, date, format=None):
        """Write date/datetime/time into cell.

        See: examples/dates.py
        
        TODO: rfct
        
        """
        assert ((dt and isinstance(date, (dt.datetime, dt.time, dt.date)))
                    or (mxdt and isinstance(date, mxdt.DateTimeType)))
        
        row, col = self._process_cell(cell)
        if format is None:
            if (dt and (isinstance(date, dt.date) 
                            and (not isinstance(date, dt.datetime)))):
                format = self._workbook.get_default_date_format()
            elif dt and isinstance(date, dt.time):
                format = self._workbook.get_default_time_format()
            elif (dt and isinstance(date, dt.datetime) 
                    or (mxdt and isinstance(date, mxdt.DateTimeType))):
                format = self._workbook.get_default_datetime_format()
        
        assert format   # what's happend?
        
        xf = self._XF(row, col, format) # The cell format
        if not self._workbook.get_1904():
            if dt and isinstance(date, (dt.datetime, dt.time, dt.date)):
                xl_date = self._excel_date_dt(date)
            elif mxdt and isinstance(date, (mxdt.DateTimeType)):
                xl_date = self._excel_date_mxdt(date)
        else:
            if dt and isinstance(date, (dt.datetime, dt.time, dt.date)):
                xl_date = self._excel_date_1904_dt(date)
            elif mxdt and isinstance(date, (mxdt.DateTimeType)):
                xl_date = self._excel_date_1904_mxdt(date)
                
        self.write_number((row, col), xl_date, format)

    def _excel_date_dt(self, date):
        """Create an Excel date in the 1900 format. All of the arguments are optional
        but you should at least add years.
    
        Corrects for Excel's missing leap day in 1900. See excel_time1.pl for an
        explanation.
        
        """
        if isinstance(date, dt.date) and (not isinstance(date, dt.datetime)):
            epoch = dt.date(1899, 12, 31)
        elif isinstance(date, dt.time):
            date = dt.datetime.combine(dt.datetime(1900, 1, 1), date)
            epoch = dt.datetime(1900, 1, 1, 0, 0, 0)
        else:
            epoch = dt.datetime(1899, 12, 31, 0, 0, 0)
        delta = date - epoch
        xldate = delta.days + float(delta.seconds) / (24*60*60)
        # Add a day for Excel's missing leap day in 1900
        if xldate > 59:
            xldate += 1
        return xldate
        
    def _excel_date_mxdt(self, date):
        """Create an Excel date in the 1900 format. All of the arguments are optional
        but you should at least add years.
    
        Corrects for Excel's missing leap day in 1900. See excel_time1.pl for an
        explanation.
        
        """
        epoch = mxdt.DateTime(1899, 12, 31, 0, 0, 0)
        delta = date - epoch
        xldate = float(delta.seconds) / (24*60*60)
        # Add a day for Excel's missing leap day in 1900
        if xldate > 59:
            xldate += 1
        return xldate


    def _excel_date_1904_dt(self, date):
        """Create an Excel date in the 1904 format. All of the arguments are optional
        but you should at least add years.
        
        You will also need to call workbook.set_1904() for this format to be valid.
        
        """
        if isinstance(date, dt.date) and (not isinstance(date, dt.datetime)):
            epoch = dt.date(1904, 1, 1)
        elif isinstance(date, dt.time):
            date = dt.datetime.combine(dt.datetime(1904, 1, 1), date)
            epoch = dt.datetime(1904, 1, 1, 0, 0, 0)
        else:
            epoch = dt.datetime(1904, 1, 1, 0, 0, 0)
        delta = date - epoch
        xldate = delta.days + float(delta.seconds) / (24*60*60)
        return xldate

    def _excel_date_1904_mxdt(self, date):
        """Create an Excel date in the 1904 format. All of the arguments are optional
        but you should at least add years.
        
        You will also need to call workbook.set_1904() for this format to be valid.
        
        """
        epoch = mxdt.DateTime(1904, 1, 1, 0, 0, 0)
        delta = date - epoch
        xldate = float(delta.seconds) / (24*60*60)
        return xldate

    def write_url(self, cell, url, str=None, format=None):
        """Write a hyperlink. This is comprised of two elements: the visible label and
        the invisible link. The visible label is the same as the link unless an
        alternative string is specified. The label is written using the
        write_string() method. Therefore the 255 characters string limit applies.
        string and format are optional and their order is interchangeable.

        The hyperlink can be to a http, ftp, mail, internal sheet, or external
        directory url.

        Returns  0 : normal termination
                -1 : insufficient number of arguments
                -2 : row or column out of range
                -3 : long string truncated to 255 chars

        """
        if str is None:
            str = url
        return self.write_url_range(cell, url, str, format)

    def write_url_range(self, cellrange, url, str=None, format=None):
        """This is the more general form of write_url(). It allows a hyperlink to be
        written to a range of cells. This function also decides the type of hyperlink
        to be written. These are either, Web (http, ftp, mailto), Internal
        (Sheet1!A1) or external ('c:\temp\foo.xls#Sheet1!A1').

        See also write_url() above for a general description and return values.

        """
        row1, col1, row2, col2 = self._process_cellrange(cellrange)
        if str is None:
            str = url
        # Check for internal/external sheet links or default to web link
        if re.match(r"^internal:", url):
            return self._write_url_internal(row1, col1, row2, col2, url, str, format)
        if re.match(r"^external:", url):
            return self._write_url_external(row1, col1, row2, col2, url, str, format)
        return self._write_url_web(row1, col1, row2, col2, url, str, format)

    def _write_url_web(self, row1, col1, row2, col2, url, string="", format=None):
        """Used to write http, ftp and mailto hyperlinks.
        The link type (options) is 0x03 is the same as absolute dir ref without
        sheet. However it is differentiated by the unknown2 data stream.

        See also write_url() above for a general description and return values.

        row1 - Start row
        col1 - Start column
        row2 - End row
        col2 - End column
        url  - URL string
        str  - Alternative label
        format - cell format

        """
        record = 0x01B8                # Record identifier
        length = 0x00000               # Bytes to follow
        if format is None:
            xf = self._workbook.get_default_url_format()   # The cell format
        else:
            xf = format
        # Write the visible label using the write_string() method.
        if string is None: string = url
        str_error = self.write_string((row1, col1), string, xf)
        if str_error == -2:
            return str_error
        # Pack the undocumented parts of the hyperlink stream
        unknown1 = "\xD0\xC9\xEA\x79\xF9\xBA\xCE\x11\x8C\x82\x00\xAA\x00\x4B\xA9\x0B\x02\x00\x00\x00"
        unknown2 = "\xE0\xC9\xEA\x79\xF9\xBA\xCE\x11\x8C\x82\x00\xAA\x00\x4B\xA9\x0B"
        # Pack the option flags
        options = pack("<L", 0x03)
        # Convert URL to a null terminated wchar string
        url = _asc2ucs(url) + "\x00\x00"
        # Pack the length of the URL
        url_len = pack("<L", len(url))
        # Calculate the data length
        length = 0x34 + len(url)
        # Pack the header data
        header = pack("<HH", record, length)
        data = pack("<HHHH", row1, row2, col1, col2)
        # Write the packed data
        self._append(header, data, unknown1, options, unknown2, url_len, url)
        return str_error

    def _write_url_internal(self, row1, col1, row2, col2, url, str=None, format=None):
        """Used to write internal reference hyperlinks such as "Sheet1!A1".

        See also write_url() above for a general description and return values.

        row1 - Start row
        col1 -  Start column
        row2 - End row
        col2 - End column
        url  - URL string
        str  - Alternative label
        format - cell format

        """
        record = 0x01B8                       # Record identifier
        length = 0x00000                      # Bytes to follow
        if format is None:
            xf = self._workbook.get_default_url_format()
        else:
            xf = format
        # Strip URL type
        url = url[len("internal:"):] #url =~ s[^internal:][] :-)
        # Write the visible label
        if str is None:
            str = url
        str_error = self.write_string((row1, col1), str, xf)
        if str_error == -2:
            return str_error
        # Pack the undocumented parts of the hyperlink stream
        unknown1 = "\xD0\xC9\xEA\x79\xF9\xBA\xCE\x11\x8C\x82\x00\xAA\x00\x4B\xA9\x0B\x02\x00\x00\x00"
        # Pack the option flags
        options = pack("<L", 0x08)
        # Convert the URL type and to a null terminated wchar string
        url = _asc2ucs(url) + "\x00\x00"
        # Pack the length of the URL as chars (not wchars)
        url_len = pack("<L", len(url) // 2)
        # Calculate the data length
        length = 0x24 + len(url)
        # Pack the header data
        header = pack("<HH", record, length)
        data = pack("<HHHH", row1, row2, col1, col2)
        # Write the packed data
        self._append(header, data, unknown1, options, url_len, url)
        return str_error

    def _write_url_external(self, row1, col1, row2, col2, url, str, format=None):
        """Write links to external directory names such as 'c:\foo.xls',
        c:\foo.xls#Sheet1!A1', '../../foo.xls'. and '../../foo.xls#Sheet1!A1'.

        Note: Excel writes some relative links with the dir_long string. We ignore
        these cases for the sake of simpler code.

        See also write_url() above for a general description and return values.

        row1 - Start row
        col1 -  Start column
        row2 - End row
        col2 - End column
        url  - URL string
        str  - Alternative label
        format - cell format

        """
        if url.startswith("external:\\\\"):
            return self._write_url_external_net(row1, col1, row2, col2, url, str, format)
        #~ # Network drives are different. We will handle them separately
        #~ # MS/Novell network drives and shares start with \\
        record = 0x01B8                       # Record identifier
        length = 0x00000                      # Bytes to follow
        if format is None:
            xf = self._workbook.get_default_url_format()
        else:
            xf = format
        # Strip URL type and change Unix dir separator to Dos style (if needed)
        #
        url = url[len("external:"):]
        url = url.replace("/", "\\")
        # Write the visible label
        if str is None:
            str = url.replace("#", " - ") #  =~ s[\#][ - ]
        str_error   = self.write_string((row1, col1), str, xf)
        if str_error == -2:
            return str_error
        # Determine if the link is relative or absolute:
        # Absolute if link starts with DOS drive specifier like C:
        # Otherwise default to 0x00 for relative link.
        absolute = 0x00
        m = re.match(r"^[A-Za-z]:", url)
        if m:
           absolute = 0x02
        # Determine if the link contains a sheet reference and change some of the
        # parameters accordingly.
        # Split the dir name and sheet name (if it exists)
        sheet = None
        res = url.split("#", 1)
        dir_long = res[0]
        if len(res) > 1:
            sheet = res[1]
        link_type = 0x01 | absolute
        #sheet_len
        if sheet is not None:
            link_type |= 0x08
            sheet_len  = pack("<L", len(sheet) + 0x01)
            sheet = _asc2ucs(sheet) + "\x00\x00"
        else:
            sheet_len = ''
            sheet = ''
        # Pack the link type
        link_type = pack("<L", link_type)
        # Calculate the up-level dir count e.g. (..\..\..\ == 3)
        up_count = 0
        #up_count++       while dir_long =~ s[^\.\.\\][]
        while dir_long.startswith("..\\"):
            dir_long = dir_long[3:]
            up_count += 1
        up_count = pack("<H", up_count)
        # Store the short dos dir name (null terminated)
        dir_short = dir_long + "\0"
        # Store the long dir name as a wchar string (non-null terminated)
        dir_long = _asc2ucs(dir_long)
        # Pack the lengths of the dir strings
        dir_short_len = pack("<L", len(dir_short))
        dir_long_len  = pack("<L", len(dir_long))
        stream_len = pack("<L", len(dir_long) + 0x06)
        # Pack the undocumented parts of the hyperlink stream
        unknown1 = '\xD0\xC9\xEA\x79\xF9\xBA\xCE\x11\x8C\x82\x00\xAA\x00\x4B\xA9\x0B\x02\x00\x00\x00'
        unknown2 = '\x03\x03\x00\x00\x00\x00\x00\x00\xC0\x00\x00\x00\x00\x00\x00\x46'
        unknown3 = '\xFF\xFF\xAD\xDE\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        unknown4 = pack("<H", 0x03)
        # Pack the main data stream
        data = pack("<HHHH", row1, row2, col1, col2) + \
                          unknown1     +\
                          link_type    +\
                          unknown2     +\
                          up_count     +\
                          dir_short_len+\
                          dir_short    +\
                          unknown3     +\
                          stream_len   +\
                          dir_long_len +\
                          unknown4     +\
                          dir_long     +\
                          sheet_len    +\
                          sheet
        # Pack the header data
        length = len(data)
        header = pack("<HH", record, length)
        # Write the packed data
        self._append(header, data)
        return str_error


    def _write_url_external_net(self, row1, col1, row2, col2, url, str=None, format=None):
        """Write links to external MS/Novell network drives and shares such as
        '//NETWORK/share/foo.xls' and '//NETWORK/share/foo.xls#Sheet1!A1'.

        See also write_url() above for a general description and return values.

        row1 - Start row
        col1 -  Start column
        row2 - End row
        col2 - End column
        url  - URL string
        str  - Alternative label
        format - cell format

        """
        record      = 0x01B8                       # Record identifier
        length      = 0x00000                      # Bytes to follow
        if format is None:
            xf = self._workbook.get_default_url_format()
        else:
            xf = format
        # Strip URL type and change Unix dir separator to Dos style (if needed)
        url = url[len("external:"):] #url =~ s[^external:][]
        url = url.replace("/", "\\") #url =~ s[/][\\]g
        # Write the visible label
        if str is None:
            str = url.replace("#", " - ") # (str = url)   =~ s[\#][ - ]
        str_error  = self.write_string((row1, col1), str, xf)
        if str_error == -2:
            return str_error
        # Determine if the link contains a sheet reference and change some of the
        # parameters accordingly.
        # Split the dir name and sheet name (if it exists)
        sheet = None
        res = url.split("#", 1)
        dir_long = res[0]
        if len(res) > 1:
            sheet = res[1]
        link_type = 0x0103 # Always absolute
        #sheet_len
        if sheet is not None:
            link_type |= 0x08
            sheet_len = pack("<L", len(sheet) + 0x01)
            sheet = _asc2ucs(sheet) + "\x00\x00"
        else:
            sheet_len  = ''
            sheet = ''
        # Pack the link type
        link_type = pack("<L", link_type)
        # Make the string null terminated
        dir_long = dir_long + "\0"
        # Pack the lengths of the dir string
        dir_long_len  = pack("<L", len(dir_long))
        # Store the long dir name as a wchar string (non-null terminated)
        dir_long = _asc2ucs(dir_long)
        # Pack the undocumented part of the hyperlink stream
        unknown1 = "\xD0\xC9\xEA\x79\xF9\xBA\xCE\x11\x8C\x82\x00\xAA\x00\x4B\xA9\x0B\x02\x00\x00\x00"
        # Pack the main data stream
        data        = (pack("<HHHH", row1, row2, col1, col2) +
                           unknown1 +
                           link_type +
                           dir_long_len + dir_long +
                           sheet_len + sheet       )
        # Pack the header data
        length = len(data)
        header = pack("<HH", record, length)
        # Write the packed data
        self._append(header, data)
        return str_error

    def set_row(self, row, height=None, format=None, hidden=0, level=0):
        """This method is used to set the height and XF format for a row.
        Writes the  BIFF record ROW.

        height  - Format object
        format  - Format object
        hidden  - Hidden flag
        level  - Outline level

        """
        record = 0x0208         # Record identifier
        length = 0x0010         # Number of bytes to follow
        rw = row                # Row Number
        colMic = 0x0000         # First defined column
        colMac = 0x0000         # Last defined column
        irwMac = 0x0000         # Used by Excel to optimise loading
        reserved = 0x0000       # Reserved
        grbit = 0x0000          # Option flags
        # Check for a format object
        if (isinstance(format, Format)):
            ixfe = format.get_xf_index()    # XF index
        else:
            ixfe = 0x0F
        # Set the row height in units of 1/20 of a point. Note, some heights may
        # not be obtained exactly due to rounding in Excel.
        if (height is not None):
            miyRw = height * 20   # Row height
        else:
            miyRw = 0xff      # The default row height
        # Set the limits for the outline levels (0 <= x <= 7).
        if level < 0:
            level = 0
        if level > 7:
            level = 7
        if level > self._outline_row_level:
            self._outline_row_level = level
        # Set the options flags. fUnsynced is used to show that the font and row
        # heights are not compatible. This is usually the case for WriteExcel.
        # The collapsed flag 0x10 doesn't seem to be used to indicate that a row
        # is collapsed. Instead it is used to indicate that the previous row is
        # collapsed. The zero height flag, 0x20, is used to collapse a row.
        grbit |= level
        if hidden:
            grbit |= 0x0020
        grbit |= 0x0040 # fUnsynced
        if format is not None:
            grbit |= 0x0080
        grbit |= 0x0100
        header = pack("<HH", record, length)
        data = pack("<HHHHHHHH", rw, colMic, colMac, miyRw,
                                        irwMac, reserved, grbit, ixfe)
        self._append(header, data)
        # Store the row sizes for use when calculating image vertices.
        # Also store the column formats.
        self._row_sizes[row] = height
        if format is not None: self._row_formats[row] = format

    def _check_dimensions(self, row, col):
        """Check that row and col are valid and store max and min values for use in
        DIMENSIONS record. See, _store_dimensions().

        """
        if (row >= self._xls_rowmax): return -2
        if (col >= self._xls_colmax): return -2
        self._dim_changed = 1
        if (row < self._dim_rowmin):
            self._dim_rowmin = row
        if (row > self._dim_rowmax):
            self._dim_rowmax = row
        if (col < self._dim_colmin):
            self._dim_colmin = col
        if (col > self._dim_colmax):
            self._dim_colmax = col
        return 0

    def _store_dimensions(self):
        """Writes Excel DIMENSIONS to define the area in which there is data."""
        record = 0x0000         # Record identifier
        length = 0x000A         # Number of bytes to follow
        reserved  = 0x0000      # Reserved by Excel
        # Set the data range if data has been written to the worksheet
        if (self._dim_changed):
            row_min = self._dim_rowmin
            row_max = self._dim_rowmax + 1
            col_min = self._dim_colmin
            col_max = self._dim_colmax + 1
        else:
            # Special case, not data was written
            row_min = 0
            row_max = 0
            col_min = 0
            col_max = 256
        header = pack("<HH", record, length)
        data = pack("<HHHHH", row_min, row_max, col_min, col_max, reserved)
        self._prepend(header, data)

    def _store_window2(self):
        """Write BIFF record Window2."""
        record = 0x023E                     # Record identifier
        length = 0x000A                     # Number of bytes to follow
        grbit = 0x00B6                      # Option flags
        rwTop = 0x0000                      # Top row visible in window
        colLeft = 0x0000                    # Leftmost column visible in window
        rgbHdr = 0x00000000                 # Row/column heading and gridline color
        # The options flags that comprise grbit
        fDspFmla = 0                        # 0 - bit
        fDspGrid = self._screen_gridlines   # 1
        fDspRwCol = 1                       # 2
        fFrozen = self._frozen              # 3
        fDspZeros = 1                       # 4
        fDefaultHdr = 1                     # 5
        fArabic = 0                         # 6
        fDspGuts = self._outline_on         # 7
        fFrozenNoSplit = 0                  # 0 - bit
        fSelected = self._selected          # 1
        fPaged = 1                          # 2
        grbit = fDspFmla
        grbit |= fDspGrid << 1
        grbit |= fDspRwCol << 2
        grbit |= fFrozen << 3
        grbit |= fDspZeros << 4
        grbit |= fDefaultHdr << 5
        grbit |= fArabic << 6
        grbit |= fDspGuts << 7
        grbit |= fFrozenNoSplit << 8
        grbit |= fSelected << 9
        grbit |= fPaged << 10
        header = pack("<HH", record, length)
        data = pack("<HHHL", grbit, rwTop, colLeft, rgbHdr)
        self._append(header, data)

    def _store_defcol(self):
        """Write BIFF record DEFCOLWIDTH if COLINFO records are in use."""
        record = 0x0055             # Record identifier
        length = 0x0002             # Number of bytes to follow
        colwidth = 0x0008           # Default column width
        header = pack("<HH", record, length)
        data = pack("<H", colwidth)
        self._prepend(header, data)

    def _store_colinfo(self, firstcol=0, lastcol=0, width=8.43, format=None, hidden=0, level=0):
        """Write BIFF record COLINFO to define column widths

        Note: The SDK says the record length is 0x0B but Excel writes a 0x0C
        length record.
        
        firstcol  - First formatted column
        lastcol  -  Last formatted column
        width  - Col width in user units, 8.43 is default
        hidden  - Hidden flag
        level  - Outline level

        """
        record = 0x007D          # Record identifier
        length = 0x000B          # Number of bytes to follow
        # Excel rounds the column width to the nearest pixel. Therefore we first
        # convert to pixels and then to the internal units. The pixel to users-units
        # relationship is different for values less than 1.
        if width < 1:
            pixels = int(width * 12)    # Col width in pixels
        else:
            pixels = int(width * 7) + 5
        coldx = int(pixels * 256 // 7)  # Col width in internal units
        grbit = 0x0000    # Option flags
        reserved = 0x00   # Reserved
        # Check for a format object
        if (isinstance(format, Format)):
            ixfe = format.get_xf_index()    # XF index
        else:
            ixfe = 0x0F
        # Set the limits for the outline levels (0 <= x <= 7).
        if level < 0:
            level = 0
        if level > 7:
            level = 7
        # Set the options flags.
        # The collapsed flag 0x10 doesn't seem to be used to indicate that a col
        # is collapsed. Instead it is used to indicate that the previous col is
        # collapsed. The zero height flag, 0x20, is used to collapse a col.
        if hidden:
            grbit |= 0x0001
        grbit |= level << 8
        header = pack("<HH", record, length)
        data = pack("<HHHHHB", firstcol, lastcol, coldx, ixfe, grbit, reserved)
        self._prepend(header, data)

    def _store_selection(self, row1, col1, row2, col2):
        """Write BIFF record SELECTION."""
        # TODO:!!!
        row_first, col_first, row_last, col_last = row1, col1, row2, col2
        record = 0x001D              # Record identifier
        length = 0x000F              # Number of bytes to follow
        pnn = self._active_pane      # Pane position
        rwAct = row_first            # Active row
        colAct = col_first           # Active column
        irefAct = 0                  # Active cell ref
        cref = 1                     # Number of refs
        # Swap last row/col for first row/col as necessary
        if row_first > row_last and row_last != -1:
            row_first, row_last = row_last, row_first
        if col_first > col_last and col_last != -1:
            col_first, col_last = col_last, col_first
        if row_last == -1:
            row_last = self._xls_rowmax-1
        if col_last == -1:
            col_last = self._xls_colmax-1
        rwFirst, rwLast, colFirst, colLast = row_first, row_last, col_first, col_last
        header = pack("<HH", record, length)
        data = pack("<BHHHHHHBB",  pnn, rwAct, colAct, irefAct, cref,
                        rwFirst, rwLast, colFirst, colLast)
        self._append(header, data)

    def _store_externcount(self, count):
        """Write BIFF record EXTERNCOUNT to indicate the number of external sheet
        references in a worksheet.

        Excel only stores references to external sheets that are used in formulas.
        For simplicity we store references to all the sheets in the workbook
        regardless of whether they are used or not. This reduces the overall
        complexity and eliminates the need for a two way dialogue between the formula
        parser the worksheet objects.

        count  Number of external references

        """
        record = 0x0016          # Record identifier
        length = 0x0002          # Number of bytes to follow
        header = pack("<HH", record, length)
        data = pack("<H", count)
        self._prepend(header, data)

    def _store_externsheet(self, sheetname):
        """Writes the Excel BIFF EXTERNSHEET record. These references are used by
        formulas. A formula references a sheet name via an index. Since we store a
        reference to all of the external worksheets the EXTERNSHEET index is the same
        as the worksheet index.

        sheetname  - Worksheet name

        """
        record = 0x0017   # Record identifier
        # length  Number of bytes to follow
        # cch     Length of sheet name
        # rgch    Filename encoding
        # References to the current sheet are encoded differently to references to
        # external sheets.
        if (self._name == sheetname):
            sheetname = ''
            length = 0x02     # The following 2 bytes
            cch = 1           # The following byte
            rgch = 0x02       # Self reference
        else:
            length = 0x02 + len(sheetname)
            cch = len(sheetname)
            rgch = 0x03       # Reference to a sheet in the current workbook
        header = pack("<HH", record, length)
        data = pack("<BB", cch, rgch)
        self._prepend(header, data, sheetname)

    def _store_panes(self, y=0, x=0, rwTop=None, colLeft=None, pnnAct=None):
        """Writes the Excel BIFF PANE record.
        The panes can either be frozen or thawed (unfrozen).
        Frozen panes are specified in terms of a integer number of rows and columns.
        Thawed panes are specified in terms of Excel's units for rows and columns.

        y        Vertical split position
        x        Horizontal split position
        rwTop    Top row visible
        colLeft Leftmost column visible
        pnnAct  Active pane

        """
        record  = 0x0041       # Record identifier
        length  = 0x000A       # Number of bytes to follow
        # Code specific to frozen or thawed panes.
        if self._frozen:
            # Set default values for rwTop and colLeft
            if rwTop is None: rwTop = y
            if colLeft is None: colLeft = x
        else:
            # Set default values for rwTop and colLeft
            if rwTop is None: rwTop = 0
            if colLeft is None: colLeft = 0
            # Convert Excel's row and column units to the internal units.
            # The default row height is 12.75
            # The default column width is 8.43
            # The following slope and intersection values were interpolated.
            y = 20*y + 255
            x = 113.879*x + 390
        # Determine which pane should be active. There is also the undocumented
        # option to override this should it be necessary: may be removed later.
        if (pnnAct is None):
            if (x != 0 and y != 0): pnnAct = 0  # Bottom right
            if (x != 0 and y == 0): pnnAct = 1  # Top right
            if (x == 0 and y != 0): pnnAct = 2  # Bottom left
            if (x == 0 and y == 0): pnnAct = 3  # Top left
        self._active_pane = pnnAct  # Used in _store_selection
        header = pack("<HH", record, length)
        data = pack("<HHHHH", x, y, rwTop, colLeft, pnnAct)
        self._append(header, data)

    def _store_setup(self):
        """Store the page setup SETUP BIFF record."""
        record = 0x00A1                   # Record identifier
        length = 0x0022                   # Number of bytes to follow
        iPaperSize = self._paper_size     # Paper size
        iScale = self._print_scale        # Print scaling factor
        iPageStart = 0x01                 # Starting page number
        iFitWidth = self._fit_width       # Fit to number of pages wide
        iFitHeight   = self._fit_height   # Fit to number of pages high
        grbit        = 0x00               # Option flags
        iRes         = 0x0258             # Print resolution
        iVRes        = 0x0258             # Vertical print resolution
        numHdr       = self._margin_head  # Header Margin
        numFtr       = self._margin_foot  # Footer Margin
        iCopies      = 0x01               # Number of copies
        fLeftToRight = 0x0                # Print over then down
        fLandscape = self._orientation    # Page orientation
        fNoPls = 0x0                      # Setup not read from printer
        fNoColor = 0x0                    # Print black and white
        fDraft = 0x0                      # Print draft quality
        fNotes = 0x0                      # Print notes
        fNoOrient = 0x0                   # Orientation not set
        fUsePage = 0x0                    # Use custom starting page
        grbit = fLeftToRight
        grbit |= fLandscape << 1
        grbit |= fNoPls << 2
        grbit |= fNoColor << 3
        grbit |= fDraft << 4
        grbit |= fNotes << 5
        grbit |= fNoOrient << 6
        grbit |= fUsePage << 7
        numHdr = pack("<d", numHdr)
        numFtr = pack("<d", numFtr)
        header = pack("<HH",         record, length)
        data1 = pack("<HHHHHHHH", iPaperSize, iScale, iPageStart, iFitWidth, iFitHeight,
                        grbit, iRes, iVRes)
        data2 = numHdr + numFtr
        data3 = pack("<H", iCopies)
        self._prepend(header, data1, data2, data3)

    def _store_header(self):
        """Store the header caption BIFF record."""
        record  = 0x0014               # Record identifier
        str = self._header # header string
        cch = len(str)         # Length of header string
        length = 1 + cch
        header = pack("<HH", record, length)
        data = pack("<B", cch)
        self._prepend(header, data, str)

    def _store_footer(self):
        """Store the footer caption BIFF record."""
        record = 0x0015               # Record identifier
        str = self._footer # Footer string
        cch = len(str)         # Length of footer string
        length  = 1 + cch
        header = pack("<HH", record, length)
        data = pack("<B", cch)
        self._prepend(header, data, str)

    def _store_hcenter(self):
        """Store the horizontal centering HCENTER BIFF record."""
        record = 0x0083              # Record identifier
        length = 0x0002              # Bytes to follow
        fHCenter = self._hcenter # Horizontal centering
        header = pack("<HH", record, length)
        data = pack("<H", fHCenter)
        self._prepend(header, data)

    def _store_vcenter(self):
        """Store the vertical centering VCENTER BIFF record."""
        record = 0x0084              # Record identifier
        length = 0x0002              # Bytes to follow
        fVCenter = self._vcenter # Horizontal centering
        header = pack("<HH", record, length)
        data = pack("<H", fVCenter)
        self._prepend(header, data)

    def _store_margin_left(self):
        """Store the LEFTMARGIN BIFF record."""
        record = 0x0026             # Record identifier
        length = 0x0008             # Bytes to follow
        margin = self._margin_left  # Margin in inches
        header = pack("<HH", record, length)
        data = pack("<d", margin)
        self._prepend(header, data)

    def _store_margin_right(self):
        """Store the RIGHTMARGIN BIFF record."""
        record = 0x0027             # Record identifier
        length = 0x0008             # Bytes to follow
        margin = self._margin_right # Margin in inches
        header = pack("<HH", record, length)
        data = pack("<d", margin)
        self._prepend(header, data)

    def _store_margin_top(self):
        """Store the TOPMARGIN BIFF record."""
        record = 0x0028               # Record identifier
        length = 0x0008               # Bytes to follow
        margin = self._margin_top     # Margin in inches
        header = pack("<HH",  record, length)
        data = pack("<d", margin)
        self._prepend(header, data)

    def _store_margin_bottom(self):
        """Store the BOTTOMMARGIN BIFF record."""
        record = 0x0029                 # Record identifier
        length = 0x0008                 # Bytes to follow
        margin = self._margin_bottom    # Margin in inches
        header = pack("<HH", record, length)
        data = pack("<d", margin)
        self._prepend(header, data)

    def merge_cells(self, cellrange):
        """This is an Excel97/2000 method. It is required to perform more complicated
        merging than the normal align merge in Format.pm

        """
        first_row, first_col, last_row, last_col = self._process_cellrange(cellrange)
        record  = 0x00E5                # Record identifier
        length  = 0x000A                # Bytes to follow
        cref = 1                        # Number of refs
        # Excel doesn't allow a single cell to be merged
        if (first_row == last_row and first_col == last_col): return
        # Swap last row/col with first row/col as necessary
        if first_row  > last_row:
            rwFirst,  rwLast = rwLast,  rwFirst
        if first_col > last_col:
            first_col, last_col = last_col, first_col
        header = pack("<HH", record, length)
        data = pack("<HHHHH", cref, first_row, last_row, first_col, last_col)
        self._append(header, data)

    def merge_range(self, cellrange, str, format):
        """This is a wrapper to ensure correct use of the merge_cells method, i.e., write
        the first cell of the range, write the formatted blank cells in the range and
        then call the merge_cells record. Failing to do the steps in this order will
        cause Excel 97 to crash.

        """
        first_row, first_col, last_row, last_col = self._process_cellrange(cellrange)
        # Set the merge_range property of the format object. For BIFF8+.
        format.set_merge_range()
        # Excel doesn't allow a single cell to be merged
        if (first_row == last_row and first_col == last_col):
            raise Exception("Can't merge single cell")
        # Swap last row/col with first row/col as necessary
        if (first_row > last_row):
            first_row,  last_row = last_row, first_row
        if (first_col > last_col):
            first_col,  last_col = last_col, first_col
        # Write the first cell
        self.write([first_row, first_col], str, format)
        # Pad out the rest of the area with formatted blank cells.
        for row in xrange(first_row, last_row+1):
            for col in xrange(first_col, last_col+1):
                if (row == first_row and col == first_col): 
                    continue
                self.write_blank([row, col], format)
        self.merge_cells([first_row, first_col, last_row, last_col])

    def _store_print_headers(self):
        """Write the PRINTHEADERS BIFF record."""
        record      = 0x002a                  # Record identifier
        length      = 0x0002                  # Bytes to follow
        fPrintRwCol = self._print_headers     # Boolean flag
        header = pack("<HH", record, length)
        data = pack("<H", fPrintRwCol)
        self._prepend(header, data)

    def _store_print_gridlines(self):
        """Write the PRINTGRIDLINES BIFF record. Must be used in conjunction with the
        GRIDSET record.

        """
        record = 0x002b                    # Record identifier
        length = 0x0002                    # Bytes to follow
        fPrintGrid  = self._print_gridlines # Boolean flag
        header = pack("<HH", record, length)
        data = pack("<H", fPrintGrid)
        self._prepend(header, data)

    def _store_gridset(self):
        """Write the GRIDSET BIFF record. Must be used in conjunction with the
        PRINTGRIDLINES record.

        """
        record = 0x0082                       # Record identifier
        length = 0x0002                       # Bytes to follow
        fGridSet = not self._print_gridlines  # Boolean flag
        header = pack("<HH", record, length)
        data = pack("<H", fGridSet)
        self._prepend(header, data)

    def _store_guts(self):
        """_store_guts()

        Write the GUTS BIFF record. This is used to configure the gutter margins
        where Excel outline symbols are displayed. The visibility of the gutters is
        controlled by a flag in WSBOOL. See also _store_wsbool().

        We are all in the gutter but some of us are looking at the stars.

        """
        record = 0x0080   # Record identifier
        length = 0x0008   # Bytes to follow
        dxRwGut = 0x0000  # Size of row gutter
        dxColGut = 0x0000 # Size of col gutter
        row_level = self._outline_row_level
        col_level = 0
        # Calculate the maximum column outline level. The equivalent calculation
        # for the row outline level is carried out in set_row().
        for colinfo in self._colinfo:
            # Skip cols without outline level info.
            if len(colinfo) < 6:
                continue
            if colinfo[5] > col_level:
                col_level = colinfo[5]
        # Set the limits for the outline levels (0 <= x <= 7).
        if col_level < 0:
            col_level = 0
        if col_level > 7:
            col_level = 7
        # The displayed level is one greater than the max outline levels
        if row_level > 0:
            row_level += 1
        if col_level > 0:
            col_level += 1
        header = pack("<HH", record, length)
        data = pack("<HHHH", dxRwGut, dxColGut, row_level, col_level)
        self._prepend(header, data)

    def _store_wsbool(self):
        """Write the WSBOOL BIFF record, mainly for fit-to-page. Used in conjunction
        with the SETUP record.

        """
        record = 0x0081   # Record identifier
        length = 0x0002   # Bytes to follow
        # grbit                  # Option flags
        # The only option that is of interest is the flag for fit to page. So we
        # set all the options in one go.
        grbit = 0x0000   # Option flags
        # Set the option flags
        grbit |= 0x0001         # Auto page breaks visible
        if self._outline_style:
            grbit |= 0x0020     # Auto outline styles
        if self._outline_below:
            grbit |= 0x0040     # Outline summary below
        if self._outline_right:
            grbit |= 0x0080     # Outline summary right
        if self._fit_page:
            grbit |= 0x0100     # Page setup fit to page
        if self._outline_on:
            grbit |= 0x0400     # Outline symbols displayed
        header = pack("<HH", record, length)
        data = pack("<H", grbit)
        self._prepend(header, data)

    def _store_hbreak(self):
        """Write the HORIZONTALPAGEBREAKS BIFF record."""
        # Return if the user hasn't specified pagebreaks
        if not self._hbreaks: return
        # Sort and filter array of page breaks
        breaks = self._sort_pagebreaks(*self._hbreaks)
        record = 0x001b               # Record identifier
        cbrk = len(breaks)            # Number of page breaks
        length = (cbrk + 1) * 2       # Bytes to follow
        header = pack("<HH", record, length)
        data = pack("<H", cbrk)
        # Append each page break
        for br in breaks:
            data += pack("<H", br)
        self._prepend(header, data)

    def _store_vbreak(self):
        """Write the VERTICALPAGEBREAKS BIFF record."""
        # Return if the user hasn't specified pagebreaks
        if not self._vbreaks: return
        # Sort and filter array of page breaks
        breaks = self._sort_pagebreaks(*self._vbreaks)
        record = 0x001a               # Record identifier
        cbrk = len(breaks)       # Number of page breaks
        length = (cbrk + 1) * 2      # Bytes to follow
        header = pack("<HH", record, length)
        data = pack("<H", cbrk)
        # Append each page break
        for br in breaks:
            data += pack("<H", br)
        self._prepend(header, data)

    def _store_protect(self):
        """Set the Biff PROTECT record to indicate that the worksheet is protected."""
        # Exit unless sheet protection has been specified
        if not self._protect:
            return
        record = 0x0012               # Record identifier
        length = 0x0002               # Bytes to follow
        fLock = self._protect # Worksheet is protected
        header = pack("<HH", record, length)
        data = pack("<H", fLock)
        self._prepend(header, data)

    def _store_password(self):
        """Write the worksheet PASSWORD record."""
        # Exit unless sheet protection and password have been specified
        if ((not self._protect) or (not self._password)): return
        record = 0x0013               # Record identifier
        length = 0x0002               # Bytes to follow
        wPassword = self._password    # Encoded password
        header = pack("<HH", record, length)
        data = pack("<H",  wPassword)
        self._prepend(header, data)

    def insert_bitmap(self, cell, filename, x=0, y=0, scale_x=1, scale_y=1):
        """Insert a 24bit bitmap image in a worksheet. The main record required is
        IMDATA but it must be proceeded by a OBJ record to define its position.

        """
        row, col = self._process_cell(cell)
        width, height, size, data = self._process_bitmap(filename)
        # Scale the frame of the image.
        width *= scale_x
        height *= scale_y
        # Calculate the vertices of the image and write the OBJ record
        self._position_image(row, col, x, y, width, height)
        # Write the IMDATA record to store the bitmap data
        record = 0x007f
        length = 8 + size
        cf = 0x09
        env = 0x01
        lcb = size
        header = pack("<HHHHL", record, length, cf, env, lcb)
        self._append(header, data)

    def _position_image(self, row_start, col_start, x1, y1, width, height):
        """Calculate the vertices that define the position of the image as required by
        the OBJ record.

                 +------------+------------+
                 |     A      |      B     |
           +-----+------------+------------+
           |     |(x1,y1)     |            |
           |  1  |(A1)._______|______      |
           |     |    |              |     |
           |     |    |              |     |
           +-----+----|    BITMAP    |-----+
           |     |    |              |     |
           |  2  |    |______________.     |
           |     |            |        (B2)|
           |     |            |     (x2,y2)|
           +---- +------------+------------+

        Example of a bitmap that covers some of the area from cell A1 to cell B2.

        Based on the width and height of the bitmap we need to calculate 8 vars:
            col_start, row_start, col_end, row_end, x1, y1, x2, y2.
        The width and height of the cells are also variable and have to be taken into
        account.
        The values of col_start and row_start are passed in from the calling
        function. The values of col_end and row_end are calculated by subtracting
        the width and height of the bitmap from the width and height of the
        underlying cells.
        The vertices are expressed as a percentage of the underlying cell width as
        follows (rhs values are in pixels):

               x1 = X / W *1024
               y1 = Y / H *256
               x2 = (X-1) / W *1024
               y2 = (Y-1) / H *256

               Where:  X is distance from the left side of the underlying cell
                       Y is distance from the top of the underlying cell
                       W is the width of the cell
                       H is the height of the cell

        Note: the SDK incorrectly states that the height should be expressed as a
        percentage of 1024.

        col_start  - Col containing upper left corner of object
        row_start  - Row containing top left corner of object
        x1  - Distance to left side of object
        y1  - Distance to top of object
        width  - Width of image frame
        height  - Height of image frame
        
        """
        # Adjust start column for offsets that are greater than the col width
        while x1 >= self._size_col(col_start):
            x1 -= self._size_col(col_start)
            col_start += 1
        # Adjust start row for offsets that are greater than the row height
        while y1 >= self._size_row(row_start):
            y1 -= self._size_row(row_start)
            row_start += 1
        # Initialise end cell to the same as the start cell
        row_end = row_start   # Row containing bottom right corner of object
        col_end = col_start   # Col containing lower right corner of object
        width = width + x1 - 1
        height = height + y1 - 1
        # Subtract the underlying cell widths to find the end cell of the image
        while (width >= self._size_col(col_end)):
            width -= self._size_col(col_end)
            col_end += 1
        # Subtract the underlying cell heights to find the end cell of the image
        while (height >= self._size_row(row_end)):
            height -= self._size_row(row_end)
            row_end += 1
        # Bitmap isn't allowed to start or finish in a hidden cell, i.e. a cell
        # with zero eight or width.
        if ((self._size_col(col_start) == 0) or (self._size_col(col_end) == 0)
                or (self._size_row(row_start) == 0) or (self._size_row(row_end) == 0)):
            return
        # Convert the pixel values to the percentage value expected by Excel
        x1 = float(x1) / self._size_col(col_start) * 1024
        y1 = float(y1) / self._size_row(row_start) *  256
        # Distance to right side of object
        x2 = float(width) / self._size_col(col_end) * 1024
        # Distance to bottom of object
        y2 = float(height) / self._size_row(row_end) *  256
        self._store_obj_picture(col_start, x1, row_start, y1, col_end, x2, row_end, y2)

    def _size_col(self, col):
        """Convert the width of a cell from user's units to pixels. By interpolation
        the relationship is: y = 7x +5. If the width hasn't been set by the user we
        use the default value. If the col is hidden we use a value of zero.

        """
        # Look up the cell value to see if it has been changed
        if self._col_sizes.has_key(col):
            width = self._col_sizes[col]
            # The relationship is different for user units less than 1.
            if width < 1:
                return int(width * 12)
            else:
                return int(width * 7) + 5
        else:
            return 64

    def _size_row(self, row):
        """Convert the height of a cell from user's units to pixels. By interpolation
        the relationship is: y = 4/3x. If the height hasn't been set by the user we
        use the default value. If the row is hidden we use a value of zero. (Not
        possible to hide row yet).

        """
        # Look up the cell value to see if it has been changed
        if self._row_sizes.has_key(row):
            if (self._row_sizes[row] == 0):
                return 0
            else:
                return int(4.0 / 3.0 * self._row_sizes[row])
        else:
            return 17

    def _store_obj_picture(self, col_start, x1, row_start, y1, col_end, x2, row_end, y2):
        """Store the OBJ record that precedes an IMDATA record. This could be generalise
        to support other Excel objects.

        """
        record = 0x005d    # Record identifier
        length = 0x003c    # Bytes to follow
        cObj = 0x0001      # Count of objects in file (set to 1)
        OT = 0x0008        # Object type. 8 = Picture
        id = 0x0001        # Object ID
        grbit = 0x0614     # Option flags
        colL = col_start    # Col containing upper left corner of object
        dxL = x1            # Distance from left side of cell
        rwT = row_start     # Row containing top left corner of object
        dyT = y1            # Distance from top of cell
        colR = col_end      # Col containing lower right corner of object
        dxR = x2            # Distance from right of cell
        rwB = row_end       # Row containing bottom right corner of object
        dyB = y2            # Distance from bottom of cell
        cbMacro = 0x0000    # Length of FMLA structure
        Reserved1 = 0x0000  # Reserved
        Reserved2 = 0x0000  # Reserved
        icvBack = 0x09      # Background colour
        icvFore = 0x09      # Foreground colour
        fls = 0x00          # Fill pattern
        fAuto = 0x00        # Automatic fill
        icv = 0x08          # Line colour
        lns = 0xff          # Line style
        lnw = 0x01          # Line weight
        fAutoB = 0x00       # Automatic border
        frs = 0x0000        # Frame style
        cf = 0x0009         # Image format, 9 = bitmap
        Reserved3 = 0x0000  # Reserved
        cbPictFmla = 0x0000 # Length of FMLA structure
        Reserved4 = 0x0000  # Reserved
        grbit2 = 0x0001     # Option flags
        Reserved5 = 0x0000  # Reserved
        header = pack("<HH", record, length)
        data = pack("<L", cObj)
        data += pack("<H", OT)
        data += pack("<H", id)
        data += pack("<H", grbit)
        data += pack("<H", colL)
        data += pack("<H", dxL)
        data += pack("<H", rwT)
        data += pack("<H", dyT)
        data += pack("<H", colR)
        data += pack("<H", dxR)
        data += pack("<H", rwB)
        data += pack("<H", dyB)
        data += pack("<H", cbMacro)
        data += pack("<L", Reserved1)
        data += pack("<H", Reserved2)
        data += pack("<B", icvBack)
        data += pack("<B", icvFore)
        data += pack("<B", fls)
        data += pack("<B", fAuto)
        data += pack("<B", icv)
        data += pack("<B", lns)
        data += pack("<B", lnw)
        data += pack("<B", fAutoB)
        data += pack("<H", frs)
        data += pack("<L", cf)
        data += pack("<H", Reserved3)
        data += pack("<H", cbPictFmla)
        data += pack("<H", Reserved4)
        data += pack("<H", grbit2)
        data += pack("<L", Reserved5)
        self._append(header, data)

    def _process_bitmap(self, bitmap):
        """Convert a 24 bit bitmap into the modified internal format used by Windows.
        This is described in BITMAPCOREHEADER and BITMAPCOREINFO structures in the
        MSDN library.

        """
        # Open file and binmode the data in case the platform needs it.
        fh = file(bitmap, "rb")
        try:
            # Slurp the file into a string.
            data = fh.read()
        finally:
            fh.close()
        # Check that the file is big enough to be a bitmap.
        if len(data) <= 0x36:
            raise Exception("bitmap doesn't contain enough data.")
        # The first 2 bytes are used to identify the bitmap.
        if (data[:2] != "BM"):
            raise Exception("bitmap doesn't appear to to be a valid bitmap image.")
        # Remove bitmap data: ID.
        data = data[2:]
        # Read and remove the bitmap size. This is more reliable than reading
        # the data size at offset 0x22.
        #
        size = unpack("<L", data[:4])[0]
        size -=  0x36   # Subtract size of bitmap header.
        size +=  0x0C   # Add size of BIFF header.
        data = data[4:]
        # Remove bitmap data: reserved, offset, header length.
        data = data[12:]
        # Read and remove the bitmap width and height. Verify the sizes.
        width, height = unpack("<LL", data[:8])
        data = data[8:]
        if (width > 0xFFFF):
            raise Exception("bitmap: largest image width supported is 65k.")
        if (height > 0xFFFF):
            raise Exception("bitmap: largest image height supported is 65k.")
        # Read and remove the bitmap planes and bpp data. Verify them.
        planes, bitcount = unpack("<HH", data[:4])
        data = data[4:]
        if (bitcount != 24):
            raise Exception("bitmap isn't a 24bit true color bitmap.")
        if (planes != 1):
            raise Exception("bitmap: only 1 plane supported in bitmap image.")
        # Read and remove the bitmap compression. Verify compression.
        compression = unpack("<L", data[:4])[0]
        data = data[4:]
        if (compression != 0):
            raise Exception("bitmap: compression not supported in bitmap image.")
        # Remove bitmap data: data size, hres, vres, colours, imp. colours.
        data = data[20:]
        # Add the BITMAPCOREHEADER data
        header = pack("<LHHHH", 0x000c, width, height, 0x01, 0x18)
        data = header + data
        return (width, height, size, data)

    def _store_zoom(self): #, zoom):
        """Store the window zoom factor. This should be a reduced fraction but for
        simplicity we will store all fractions with a numerator of 100.

        """
        if self._zoom == 100:
            return
        record = 0x00A0               # Record identifier
        length = 0x0004               # Bytes to follow
        header = pack("<HH", record, length)
        data = pack("<HH", self._zoom, 100)
        self._append(header, data)

    def _store_comment(self, row, col, str, strlen=0):
        """_store_comment

        Store the Excel 5 NOTE record. This format is not compatible with the Excel 7
        record.

        row  - Zero indexed row
        col  - Zero indexed column
        str  -
        strlen  -

        """
        record = 0x001C       # Record identifier
        # The length of the first record is the total length of the NOTE.
        # Therefore, it can be greater than 2048.
        if strlen > 2048:
            length = 0x06 + 2048  # Bytes to follow
        else:
            length = 0x06 + strlen
        header = pack("<HH",  record, length)
        data = pack("<HHH", row, col, strlen)
        self._append(header, data, str)

    def _process_cell(self, cell):
        if isinstance(cell, str):
            row, col = cell_to_rowcol2(cell)
        elif isinstance(cell, tuple) or isinstance(cell, list):
            assert len(cell) == 2
            row, col = cell
        else:
            raise Exception("Cell's type error")
        return row, col

    def _process_cellrange(self, cellrange):
        if isinstance(cellrange, str):
            row1, col1, row2, col2 = cellrange_to_rowcol_pair(cellrange)
        elif isinstance(cellrange, tuple) or isinstance(cellrange, list):
            assert len(cellrange) in (2, 4)
            if len(cellrange) == 2:
                row1, col1 = cellrange
                row2, col2 = row1, col1
            else:   # len(cellrange) == 4
                row1, col1, row2, col2 = cellrange
        else:
            raise Exception("Type of cell range error")
        return row1, col1, row2, col2

    def _process_rowrange(self, rowrange):
        if isinstance(rowrange, str):
            row1, col1, row2, col2 = cellrange_to_rowcol_pair(rowrange)
            assert col1 == 0 and col2 == -1
        elif isinstance(rowrange, int):
            row1, row2 = rowrange, rowrange
            col1, col2 = 0, -1
        elif isinstance(rowrange, tuple) or isinstance(rowrange, list):
            assert len(rowrange) in (2, 4)
            if len(rowrange) == 2:
                row1, row2 = rowrange
                col1, col2 = 0, -1
            else:   # len(rowrange) == 4
                row1, col1, row2, col2 = rowrange
                # assert col1 == 0 and col2 == -1
        else:
            raise Exception("Type of row range error [%s]" % (type(rowrange)))
        return row1, col1, row2, col2

    def _process_colrange(self, colrange):
        if isinstance(colrange, str):
            row1, col1, row2, col2 = cellrange_to_rowcol_pair(colrange)
            assert row1 == 0 and row2 == -1
        elif isinstance(colrange, int):
            row1, row2 = 0, -1
            col1, col2 = colrange, colrange
        elif isinstance(colrange, tuple) or isinstance(colrange, list):
            assert len(colrange) in (2, 4)
            if len(colrange) == 2:
                row1, row2 = 0, -1
                col1, col2 = colrange
            else:   # len(rowrange) == 4
                row1, col1, row2, col2 = rowrange
                # assert row1 == 0 and row2 == -1
        else:
            raise Exception("Type of col range error [%s]" % (type(colrange)))
        return row1, col1, row2, col2
    
    def _close_tmp(self):
        """Close and unlink the tempfile."""
        if not self._fileclosed:
            self._filehandle.close() # Temp file will be auto removed
            self._fileclosed = True