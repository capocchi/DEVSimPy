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
# This module was ported from Perl Spreadsheet::WriteExcel module
# The author of the Spreadsheet::WriteExcel module is John McNamara
# <jmcnamara@cpan.org>
#----------------------------------------------------------------------------
# See the README.txt distributed with pyXLWriter for more details.

"""pyXLWriter

pyXLWriter is a Python library for generating Excel compatible spreadsheets.
It's a port of John McNamara's Perl Spreadsheet::WriteExcel module
version 1.01 to Python. It allows writing of Excel compatible spreadsheets
without the need for COM objects.

This package was ported from Perl Spreadsheet::WriteExcel module
The author of the Spreadsheet::WriteExcel module is John McNamara
<jmcnamara@cpan.org>

"""

__revision__ = """$Id: __init__.py,v 1.33 2004/08/20 05:33:49 fufff Exp $"""

from utilites import *

from Workbook import Workbook
from Format import Format
from Formula import Formula

import sys as _sys


def _gen_version(vi):
    """Generate version from version_info tuple.
    
    Examples: 
        (0, 1, 0, "alpha", 1) -> "0.1a1"
        (3, 4, 6, "final", 0) -> "3.4.6"
        
    """
    assert len(vi) == 5
    i = 2
    while i > 1 and vi[i] == 0:
        i -= 1
    v = ".".join([str(x) for x in vi[:i+1]])
    if vi[3] != "final":
        v += "%1.1s%d" % vi[3:5]
    return v


###########################################################################
# Package information

__author__ = "Evgeny Filatov <fufff@users.sourceforge.net>"
__url__= "http://sourceforge.net/pyxlwriter/"
__license__ = "GNU LGPL"

__copyright__ = """\
Copyright (c) 2004 Evgeny Filatov <fufff@users.sourceforge.net>
Copyright (c) 2002-2004 John McNamara (Perl Spreadsheet::WriteExcel)
"""

version_info = (0, 4, 0, "alpha", 3)
    
__version__ = _gen_version(version_info)


# Writer is the Workbook's alias, only
Writer = Workbook