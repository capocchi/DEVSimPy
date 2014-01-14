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
# This module based on PERL OLE::Storage_Lite module.
# The author of the PERL OLE::Storage_Lite module is Kawai Takanori 
# <kwitknr@cpan.org>
#----------------------------------------------------------------------------
# See the README.txt distributed with pyXLWriter for more details.

"""pyXLWriter.OLEWriterBig

"""
__revision__ = """$Id: OLEWriterBig.py,v 1.8 2004/08/20 05:16:16 fufff Exp $"""

from struct import pack


__all__ = ["OLEWriterBig"]


_BIG_BLOCK_SIZE = 0x200
_SMALL_BLOCK_SIZE = 0x40
_PPS_SIZE = 0x80
_SMALL_SIZE = 0x1000
_LONG_INT_SIZE = 4


def _ceil_div(a, b):
    """Return ceil(a/b).
    
    int(a / b) + (a % b)?(1):(0)
    
    """
    return (a-1) // b + 1
    

class _PPS:

    def __init__(self, fh, name="", type=0, dir=0, start=0, size=0):
        self._fh = fh
        self.name = self._asc2ucs(name)
        self.type = type
        self.dir = dir
        self.start_block = start
        self.size = size
        
    def save_pps_wk(self):
        fh = self._fh
        # 1. Write _PPS
        fh.write(self.name)
        fh.write("\x00" * (64 - len(self.name)))    #64
        fh.write(pack("<H", len(self.name) + 2))    #66
        fh.write(pack("<B", self.type))             #67
        fh.write(pack("<B", 0x00))           # UK   #68
        fh.write(pack("<L", 0xFFFFFFFFL))    # Prev #72
        fh.write(pack("<L", 0xFFFFFFFFL))    # Next #76
        fh.write(pack("<L", self.dir))              # Dir  #80
        fh.write("\x00\x09\x02\x00")                #84
        fh.write("\x00\x00\x00\x00")                #88
        fh.write("\xc0\x00\x00\x00")                #92
        fh.write("\x00\x00\x00\x46")                #96
        fh.write("\x00\x00\x00\x00")                #100
        fh.write("\x00" * 8)              # time1st #108
        fh.write("\x00" * 8)              # time2nd #116
        fh.write(pack("<L", self.start_block))      #116
        fh.write(pack("<L", self.size))             #124
        fh.write(pack("<L", 0))                     #128

    def _asc2ucs(self, s):
        """Convert ascii strring to unicode."""
        if s:
            return "\x00".join(s) + "\x00" 
        else:
            return ""


class OLEWriterBig:
    """A writer class to store BIFF data in a OLE compound
    storage file.
    
    """
    
    def __init__(self, olefile=None):
        """Constructor."""
        self._olefile = olefile
        self._booksize = None       # Isn't initialized
        self._fh = None
        self._fh_internal = False
        self._fileclosed = False
        self._initialize()
        self._ppsroot = None
        self._ppsfile = None 
        self._sbdcnt = 0
        self._bbcnt = 0
        self._ppscnt = 0
        self._initialize()
        
    def _initialize(self):
        """Initialize file handle and pps objects."""
        if isinstance(self._olefile, str):
            # Create a new file, open for writing
            self._fh_internal = True
            self._fh = file(self._olefile, "wb")
        else:
            self._fh_internal = False
            self._fh = self._olefile
        self._ppsroot = _PPS(self._fh, "Root Entry", 5, 1)
        self._ppsfile = _PPS(self._fh, "Book", 2, 0xFFFFFFFFL)

    def set_size(self, biffsize):
        self._booksize = biffsize

    def write_header(self):
        # 1. Make an array of _PPS (for Save)
        fh = self._fh
        ppsfile = self._ppsfile
        ppsroot = self._ppsroot
        sbdcnt, bbcnt, ppscnt = self._calc_sizes()
        # 2. Save Header
        self._save_header()
        # 3. Make Small Data string and set it to RootEntry Data
        self._make_small_data() 
        
    def write(self, data):
        self._fh.write(data)

    def _calc_sizes(self):
        size = self._booksize        
        bbcnt = 0
        sbcnt = 0
        self._ppsfile.size = size
        rtsize = 0
        if size < _SMALL_SIZE:
            sbcnt += _ceil_div(size, _SMALL_BLOCK_SIZE)
            ftlen = 0
            if size % _SMALL_BLOCK_SIZE:
                ftlen = (_SMALL_BLOCK_SIZE - (size % _SMALL_BLOCK_SIZE))
            rtsize = size + ftlen 
        else:
            bbcnt += _ceil_div(size, _BIG_BLOCK_SIZE)
        self._ppsroot.size = rtsize
        slcnt = _BIG_BLOCK_SIZE // _LONG_INT_SIZE
        sbdcnt = _ceil_div(sbcnt, slcnt)
        smllen = sbcnt * _SMALL_BLOCK_SIZE        
        bbcnt += _ceil_div(smllen, _BIG_BLOCK_SIZE)
        bdcnt = _BIG_BLOCK_SIZE // _PPS_SIZE
        ppscnt = _ceil_div(2, bdcnt)
        self._sbdcnt, self._bbcnt, self._ppscnt = sbdcnt, bbcnt, ppscnt
        return sbdcnt, bbcnt, ppscnt

    def _write_footer(self):
        self._save_smbg()
        # 5. Write _PPS
        self._save_pps()
        # 6. Write BD and BDList and Adding Header informations
        self._save_bbd()

    def _save_header(self):
        fh = self._fh
        sbdcnt, bbcnt, ppscnt = self._sbdcnt, self._bbcnt, self._ppscnt
        
        # 0. Calculate Basic Setting
        blcnt = _BIG_BLOCK_SIZE // _LONG_INT_SIZE
        fstbdl = (_BIG_BLOCK_SIZE - 0x4C) // _LONG_INT_SIZE
        fstbd_max = fstbdl * blcnt - fstbdl
        bdexl = 0
        all = bbcnt + ppscnt + sbdcnt
        allw = all
        bdcntw = _ceil_div(allw, blcnt)
        bdcnt = 0
        
        # 0.1 Calculate BD count
        blcnt -= 1  #the BlCnt is reduced in the count of the last sect is used for a pointer the next Bl
        bbleftover = all - fstbd_max
        if all > fstbd_max:
            while True:
                bdcnt = _ceil_div(bbleftover, blcnt)
                bdexl = _ceil_div(bdcnt, blcnt)
                bbleftover += bdexl
                if bdcnt == _ceil_div(bbleftover, blcnt):
                    break
        bdcnt += fstbdl
        
        # 1.Save Header
        fh.write("\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1")
        fh.write("\x00\x00\x00\x00" * 4)
        fh.write(pack("<H", 0x3b))
        fh.write(pack("<H", 0x03))
        fh.write(pack("<H", -2))
        fh.write(pack("<H", 9))
        fh.write(pack("<H", 6))
        fh.write(pack("<H", 0))
        fh.write("\x00\x00\x00\x00" * 2)
        fh.write(pack("<L", bdcnt))
        fh.write(pack("<L", bbcnt + sbdcnt))  # ROOT START
        fh.write(pack("<L", 0))
        fh.write(pack("<L", 0x1000))
        fh.write(pack("<L", 0))                 # Small Block Depot
        fh.write(pack("<L", 1))
        
        # 2. Extra BDList Start, Count
        if all < fstbd_max:
            fh.write(pack("<L", -2))        # Extra BDList Start
            fh.write(pack("<L", 0))         # Extra BDList Count
        else:
            fh.write(pack("<L", all+bdcnt))
            fh.write(pack("<L", bdexl))
            
        # 3. BDList
        i = 0
        while i < fstbdl and i < bdcnt:
            fh.write(pack("<L", all+i))
            i += 1
        if i < fstbdl:
            fh.write((pack("<L", -1)) * (fstbdl-i)) 

    def _make_small_data(self):
        fh = self._fh
        pps = self._ppsfile
        size = self._booksize
        # 1. Make SBD, small data string
        if size < _SMALL_SIZE:
            smbcnt = _ceil_div(size, _SMALL_BLOCK_SIZE)
            # 1.1 Add to SBD
            for i in xrange(smbcnt-1):
                fh.write(pack("<L", i+1))
            fh.write(pack("<L", -2))
            smblk = smbcnt
            sbcnt = _BIG_BLOCK_SIZE // _LONG_INT_SIZE
            if smblk % sbcnt:
                fh.write(pack("<L", -1) * (sbcnt - (smblk % sbcnt)))

    def _save_smbg(self):
        fh = self._fh
        size = self._booksize
        # Save small
        if size < _SMALL_SIZE:
            if size % _SMALL_BLOCK_SIZE:
                ftlen = (_SMALL_BLOCK_SIZE - (size % _SMALL_BLOCK_SIZE))
                fh.write("\x00" * ftlen)
            pps = self._ppsroot
        else:
            pps = self._ppsfile
        # Save big ?
        if pps.size % _BIG_BLOCK_SIZE:
            ftlen = _BIG_BLOCK_SIZE - (pps.size % _BIG_BLOCK_SIZE)
            fh.write("\x00" * ftlen) 
            pps.start_block = self._sbdcnt

    def _save_pps(self):
        fh = self._fh
        # 1. Save _PPS
        ppsroot = self._ppsroot
        ppsfile = self._ppsfile
        ppsroot.save_pps_wk()
        ppsfile.save_pps_wk()
        # 2. Adjust for Block
        cnt = 2
        bcnt = _BIG_BLOCK_SIZE // _PPS_SIZE
        if cnt % bcnt:
            count = (bcnt - (cnt % bcnt)) * _PPS_SIZE
            fh.write("\x00" * count)

    def _save_bbd(self):
        fh = self._fh
        sbdsize, bsize, ppscnt = self._sbdcnt, self._bbcnt, self._ppscnt
        
        # 0. Calculate Basic Setting
        bbcnt = _BIG_BLOCK_SIZE // _LONG_INT_SIZE
        blcnt = bbcnt - 1
        fstbdl = (_BIG_BLOCK_SIZE - 0x4C) // _LONG_INT_SIZE
        fstbd_max = fstbdl * bbcnt - fstbdl
        bdexl = 0
        all = bsize + ppscnt + sbdsize
        allw = all
        bdcntw = _ceil_div(allw, bbcnt)
        bdcnt = 0 #_ceil_div(all + bdcntw, ibdcnt)
        
        # 0.1 Calculate BD count
        bbleftover = all - fstbd_max;
        if all > fstbd_max:
            while True:
                bdcnt = _ceil_div(bbleftover, blcnt)
                bdexl = _ceil_div(bdcnt, blcnt)
                bbleftover += bdexl;
                if bdcnt == _ceil_div(bbleftover, blcnt):
                    break
        allw += bdexl
        bdcnt += fstbdl

        # 1. Making BD
        # 1.1 Set for SBD
        if sbdsize > 0:
            for i in xrange(sbdsize-1):
                fh.write(pack("<L", i+1))
            fh.write(pack("<L", -2))
            
        # 1.2 Set for B
        for i in xrange(bsize-1):
            fh.write(pack("<L", i + sbdsize + 1))
        fh.write(pack("<L", -2))
        
        # 1.3 Set for _PPS
        for i in xrange(ppscnt-1):
            fh.write(pack("<L", i + sbdsize + bsize + 1))
        fh.write(pack("<L", -2))
        
        # 1.4 Set for BBD itself ( 0xFFFFFFFD : BBD)
        for i in xrange(bdcnt):
            fh.write(pack("<L", 0xFFFFFFFDL))
            
        # 1.5 Set for ExtraBDList
        for i in xrange(bdexl):
            fh.write(pack("<L", 0xFFFFFFFCL))
            
        # 1.6 Adjust for Block
        if (allw + bdcnt) % bbcnt:
            fh.write(pack("<L", -1) * (bbcnt - ((allw + bdcnt) % bbcnt)))
            
        # 2.Extra BDList
        if bdcnt > fstbdl:
            n = 0
            nb = 0
            i = fstbdl
            while i < bdcnt: 
                if n >= (bbcnt-1):
                    n = 0
                    nb += 1
                    fh.write(pack("<L", all + bdcnt + nb))
                fh.write(pack("<L", bsize + sbdsize + ppscnt + i))
                i += 1
                n += 1
            if (bdcnt-fstbdl) % (bbcnt-1):
                fh.write(pack("<L", -1) * (bbcnt - 1 - ((bdcnt-fstbdl) % (bbcnt-1)))) 
            fh.write(pack("<L", -2))

    def close(self):
        self._write_footer()
        if self._fh_internal:
            self._fh.close()
        self._fileclosed = True