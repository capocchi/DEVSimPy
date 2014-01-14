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

"""pyXLWriter.OLEWriter

Used in conjunction with Spreadsheet::WriteExcel

"""
__revision__ = """$Id: OLEWriter.py,v 1.21 2004/08/20 05:16:16 fufff Exp $"""

from struct import pack


class OLEWriter:
    """OLEwriter - A writer class to store BIFF data in a OLE compound
    storage file.

    """

    def __init__(self, olefile=None):
        """Constructor."""
        self._olefile = olefile
        self._filehandle = None
        self._fileclosed = False
        self._internal_fh = False
        self._biff_only = 0
        self._size_allowed = 0
        self._biffsize = 0
        self._booksize = 0
        self._big_blocks = 0
        self._list_blocks = 0
        self._root_start = 0
        self._block_count = 4
        self._initialize()

    def _initialize(self):
        """Check for a valid filename and store the filehandle."""
        if isinstance(self._olefile, str):
            # Create a new file, open for writing
            self._internal_fh = True
            self._filehandle = file(self._olefile, "wb")
        else:
            self._internal_fh = False
            self._filehandle = self._olefile

    def set_size(self, biffsize):
        """Set the size of the data to be written to the OLE stream

        big_blocks - (109 depot block x (128 -1 marker word)
                       - (1 x end words)) = 13842
        maxsize - big_blocks * 512 bytes = 7087104

        """
        maxsize = 7087104  # Use Spreadsheet::WriteExcel::Big to exceed this
        if biffsize > maxsize:
            self._size_allowed = False
            raise Exception("Max size error")
        self._biffsize = biffsize
        # Set the min file size to 4k to avoid having to use small blocks
        self._booksize = max(biffsize, 4096)
        self._size_allowed = True

    def _calculate_sizes(self):
        """Calculate various sizes needed for the OLE stream"""
        datasize = self._booksize
        if datasize % 512 == 0:
            self._big_blocks = datasize // 512
        else:
            self._big_blocks = datasize // 512 + 1
        # There are 127 list blocks and 1 marker blocks for each big block
        # depot + 1 end of chain block
        self._list_blocks = self._big_blocks // 127 + 1
        self._root_start = self._big_blocks

    def close(self):
        """ Write root entry, big block list and close the filehandle.
        This routine is used to explicitly close the open filehandle without
        having to wait for DESTROY.

        """
        if not self._size_allowed:
            return
        if not self._biff_only:
            self._write_padding()
        if not self._biff_only:
            self._write_property_storage()
        if not self._biff_only:
            self._write_big_block_depot()
        # Close the filehandle if it was created internally.
        if self._internal_fh:
            self._filehandle.close()
        self._fileclosed = True

    #~ def __del__(self):
        #~ """Close the filehandle if it hasn't already been explicitly closed."""
        #~ if not self._fileclosed:
            #~ self.close()

    def write(self, data):
        """Write BIFF data to OLE file."""
        self._filehandle.write(data)

    def write_header(self):
        """Write OLE header block."""
        fh = self._filehandle
        if self._biff_only:
            return
        self._calculate_sizes()
        root_start = self._root_start
        num_lists = self._list_blocks
        id = pack("<8B", 0xD0, 0xCF, 0x11, 0xE0, 0xA1, 0xB1, 0x1A, 0xE1)
        unknown1 = pack("<LLLL", 0x00, 0x00, 0x00, 0x00)
        unknown2 = pack("<HH", 0x3E, 0x03)
        unknown3 = pack("<H", -2)
        unknown4 = pack("<H", 0x09)
        unknown5 = pack("<LLL", 0x06, 0x00, 0x00)
        num_bbd_blocks = pack("<L", num_lists)
        root_startblock = pack("<L", root_start)
        unknown6 = pack("<LL", 0x00, 0x1000)
        sbd_startblock = pack("<L", -2)
        unknown7 = pack("<LLL", 0x00, -2 ,0x00)
        unused = pack("<L", -1)
        fh.write(id)
        fh.write(unknown1)
        fh.write(unknown2)
        fh.write(unknown3)
        fh.write(unknown4)
        fh.write(unknown5)
        fh.write(num_bbd_blocks)
        fh.write(root_startblock)
        fh.write(unknown6)
        fh.write(sbd_startblock)
        fh.write(unknown7)
        for i in xrange(num_lists):
            root_start += 1
            fh.write(pack("<L", root_start))
        for i in xrange(num_lists, 108 + 1):
            fh.write(unused)

    def _write_big_block_depot(self):
        """Write big block depot."""
        fh = self._filehandle
        num_blocks = self._big_blocks
        num_lists = self._list_blocks
        total_blocks = num_lists * 128
        used_blocks = num_blocks + num_lists + 2
        marker = pack("<L", -3)
        end_of_chain = pack("<L", -2)
        unused = pack("<L", -1)
        for i in xrange(1, num_blocks):
            fh.write(pack("<L", i))
        fh.write(end_of_chain)
        fh.write(end_of_chain)
        for i in xrange(1, num_lists+1):
            fh.write(marker)
        for i in xrange(used_blocks, total_blocks+1):
            fh.write(unused)

    def _write_property_storage(self):
        """Write property storage. TODO: add summary sheets"""
        rootsize = -2
        booksize = self._booksize
        #                name         type   dir start size
        self._write_pps('Root Entry', 0x05,   1,   -2, 0x00)
        self._write_pps('Book',       0x02,  -1, 0x00, booksize)
        self._write_pps('',           0x00,  -1, 0x00, 0x0000)
        self._write_pps('',           0x00,  -1, 0x00, 0x0000)

    def _write_pps(self, name, type_, dir, sb, size):
        """Write property sheet in property storage"""
        fh = self._filehandle
        length = 0
        if name:
            name  = name + "\0"
            length = len(name) * 2
        # Simulate a Unicode string
        if name:
            rawname = "\x00".join(name) + "\x00"
        else:
            rawname = ""
        zero = pack("<B", 0)
        pps_sizeofname = pack("<H", length)    #0x40
        pps_type = pack("<H", type_)           #0x42
        pps_prev = pack("<L", -1)              #0x44
        pps_next = pack("<L", -1)              #0x48
        pps_dir = pack("<L", dir)              #0x4c
        unknown1 = pack("<L", 0)
        pps_ts1s = pack("<L", 0)               #0x64
        pps_ts1d = pack("<L", 0)               #0x68
        pps_ts2s = pack("<L", 0)               #0x6c
        pps_ts2d = pack("<L", 0)               #0x70
        pps_sb = pack("<L", sb)                #0x74
        pps_size = pack("<L", size)            #0x78
        fh.write(rawname)
        fh.write(zero * (64 - length))
        fh.write(pps_sizeofname)
        fh.write(pps_type)
        fh.write(pps_prev)
        fh.write(pps_next)
        fh.write(pps_dir)
        fh.write(unknown1 * 5)
        fh.write(pps_ts1s)
        fh.write(pps_ts1d)
        fh.write(pps_ts2d)
        fh.write(pps_ts2d)
        fh.write(pps_sb)
        fh.write(pps_size)
        fh.write(unknown1)

    def _write_padding(self):
        """Pad the end of the file"""
        biffsize = self._biffsize
        if biffsize < 4096:
            min_size = 4096
        else:
            min_size = 512
        if biffsize % min_size:
            padding = min_size - (biffsize % min_size)
            self._filehandle.write("\0" * padding)