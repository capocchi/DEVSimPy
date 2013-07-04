# pyXLWriter: A library for generating Excel Spreadsheets
# Copyright (c) 2004 Evgeny Filatov <fufff@users.sourceforge.net>
# Copyright (c) 2002-2004 John McNamara (Perl Spreadsheet::WriteExcel, ver .42)
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
# This module was ported from PERL Spreadsheet::WriteExcel module.
# The author of the Spreadsheet::WriteExcel module is John McNamara
# <jmcnamara@cpan.org>
#----------------------------------------------------------------------------
# See the README.txt distributed with pyXLWriter for more details.

"""pyXLWriter.BIFFWriter

This module is used in conjunction with Spreadsheet::WriteExcel.

"""
__revision__ = """$Id: BIFFWriter.py,v 1.18 2004/08/20 05:16:16 fufff Exp $"""


from struct import pack


class BIFFWriter:
    """BIFFwriter - An abstract base class for Excel workbooks and
    worksheets.

    """

    BIFF_version = 0x0500

    def __init__(self):
        """Constructor."""
        self._data = ""
        self._datasize = 0
        self._limit = 2080

    def _prepend(self, *args):
        """General storage function."""
        joined = "".join(args)  
        self._data = joined + self._data
        self._datasize += len(joined)

    def _append(self, *args):
        """General storage function."""
        joined = "".join(args) 
        self._data += joined
        self._datasize += len(joined)

    def _store_eof(self):
        """Writes Excel EOF record to indicate the end of a BIFF stream."""
        record = 0x000A
        length = 0x0000
        header = pack("<HH", record, length)
        self._append(header)

    def _store_bof(self, type=0x0005):
        """Writes Excel BOF record to indicate the beginning of a stream or
        sub-stream in the BIFF file.

        type = 0x0005, Workbook
        type = 0x0010, Worksheet

        """
        name = 0x0809
        length = 0x0008
        version = self.BIFF_version
        # According to the SDK build and year should be set to zero.
        # However, this throws a warning in Excel 5. So, use these
        # magic numbers.
        build = 0x096C
        year = 0x07C9
        header = pack("<HH", name, length)
        data = pack("<HHHH", version, type, build, year)
        self._prepend(header, data)

    def _add_continue(self, data):
        """Excel limits the size of BIFF records. In Excel 5 the limit is 2084 bytes.
        In Excel 97 the limit is 8228 bytes. Records that are longer than these limits
        must be split up into CONTINUE blocks.

        This function take a long BIFF record and inserts CONTINUE records as
        necessary.

        """
        data = data
        limit = self._limit
        record = 0x003C     # Record identifier
        # The first 2080/8224 bytes remain intact. However, we have to change
        # the length field of the record.
        tmp = data[0:limit]
        data = data[limit:]
        tmp = tmp[:2] + pack("<H", limit-4) + tmp[4:]
        # Strip out chunks of 2080/8224 bytes +4 for the header.
        while (len(data) > limit):
            header = pack("<HH", record, limit)
            tmp += header
            tmp += data[0:limit] 
            data = data[limit:]
        # Mop up the last of the data
        header = pack("<HH", record, len(data))
        tmp += header
        tmp += data
        return tmp