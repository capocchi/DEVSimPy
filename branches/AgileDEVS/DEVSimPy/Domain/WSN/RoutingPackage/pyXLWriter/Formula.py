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

"""pyXLWriter.Formula

Class for parsing Excel formulas

"""
__revision__ = """$Id: Formula.py,v 1.25 2004/08/20 05:16:16 fufff Exp $"""

import re
from struct import pack
from utilites import cell_to_rowcol

class Formula:
    """Formula - A class for generating Excel formulas."""

    _debug = 0

    def __init__(self):
        """Constructor."""
        self._workbook = ""
        self._ext_sheets = {}
        self._parser = None
        self._ptg = {}
        self._functions = {}
        # TODO: Move it to over good place
        self._max_row = 16384
        self._max_col = 256

    def _init_parser(self):
        """There is a small overhead involved in generating the parser. Therefore, the
        initialisation is delayed until a formula is required.

        """
        self._initialize_hashes()
        import parse
        self._parser = parse

    def parse_formula(self, formula):
        """Takes a textual description of a formula and returns a RPN encoded byte
        string.

        """
        if isinstance(formula, str):
            tokens = self.preparse_formula(formula)
        return self.parse_tokens(tokens)

    def preparse_formula(self, formula):
        """Return parsed list for formala."""
        if not self._parser:
            self._init_parser()
        if formula.startswith('='):
            formula = formula[1:]
        tokens = self._parser.parse(formula)
        # Formula with volatile function must be corrected
        if self._check_volatile(tokens):
            tokens = ['_vol'] + tokens
        return tokens
        
    def parse_tokens(self, tokens):
        """Convert each token or token pair to its Excel 'ptg' equivalent."""
        parse_str = ""
        last_type = ''
        modifier = ''
        num_args = 0
        cls = [1]
        # A note about the class modifiers used below. In general the class,
        # "reference" or "value", of a function is applied to all of its operands.
        # However, in certain circumstances the operands can have mixed classes,
        # e.g. =VLOOKUP with external references. These will eventually be dealt
        # with by the parser. However, as a workaround the class type of a token
        # can be changed via the repeat_formula interface. Thus, a _ref2d token can
        # be changed by the user to _ref2dA or _ref2dR to change its token class.
        #
        i = 0
        tokens_len = len(tokens)
        while i < tokens_len:
            token = tokens[i]
            if token == '_arg':
                i += 1
                num_args = tokens[i]
            elif token == '_class':
                i += 1
                token = tokens[i]
                try:
                    cl = self._functions[token][2]
                except KeyError:
                    # If class is undef then it means that the function isn't valid.
                    raise Exception("Unknown function %s() in formula" % (token))
                cls.append(cl)
            elif token == '_vol':
                parse_str += self._convert_volatile()
            elif token == 'ptgBool':
                i += 1
                token = tokens[i]
                parse_str += self._convert_bool(token)
            elif token == '_num':
                i += 1
                token = tokens[i]
                parse_str += self._convert_number(token)
            elif token == '_str':
                i += 1
                token = tokens[i]
                parse_str += self._convert_string(token)
            elif token == '_ref2d':
                i += 1
                token = tokens[i]
                cl = cls[-1]
                parse_str += self._convert_ref2d(token, cl)
            elif token == '_ref3d':
                i += 1
                token = tokens[i]
                cl = cls[-1]
                parse_str += self._convert_ref3d(token, cl)
            elif token == '_range2d':
                i += 1
                token = tokens[i]
                cl = cls[-1]
                parse_str += self._convert_range2d(token, cl)
            elif token == '_range3d':
                i += 1
                token = tokens[i]
                cl = cls[-1]
                parse_str += self._convert_range3d(token, cl)
            elif token == '_func':
                i += 1
                token = tokens[i]
                parse_str += self._convert_function(token, num_args)
                cls.pop()
                num_args = 0  # Reset after use
            elif self._ptg.has_key(token):
                parse_str += pack("<B", self._ptg[token])
            else:
                # Unrecognised token
                raise Exception("Unrecognised token %s" %(token))
            i += 1
        return parse_str

    def _check_volatile(self, tokens):
        """Check if the formula contains a volatile function, i.e. a function that must
        be recalculated each time a cell is updated. These formulas require a ptgAttr
        with the volatile flag set as the first token in the parsed expression.

        Examples of volatile functions: RAND(), NOW(), TODAY()

        """
        functions = self._functions
        is_funct = False
        for tok in tokens:
            if is_funct:
                try:
                    return functions[tok][3]
                except KeyError:
                    pass
            if tok == "_func":
                is_funct = True
            else:
                is_funct = False
        return False

    def _convert_volatile(self):
        """Convert _vol to a ptgAttr tag formatted to indicate that the formula contains
        a volatile function. See _check_volatile()

        """
        # Set bitFattrSemi flag to indicate volatile function, "w" is set to zero.
        return pack("<BBH", self._ptg['ptgAttr'], 0x1, 0x0)

    def _convert_bool(self, bool):
        """Convert a boolean token to ptgBool"""
        return pack("<BB", self._ptg[ptgBool], bool)

    def _convert_number(self, num):
        """Convert a number token to ptgInt or ptgNum"""
        # Integer in the range 0..2**16-1
        if (isinstance(num, int) and (num <= 65535)):
            return pack("<BH", self._ptg['ptgInt'], num)
        else: # A float
            num = pack("<d", float(num))
            return pack("<B", self._ptg['ptgNum']) + str(num)

    def _convert_string(self, str):
        """Convert a string to a ptg Str."""
        if str.startswith('"'): # Remove leading  "
            str = str[1:]
        if str.endswith('"'): # Remove trailing "
            str = str[:-1]
        # Substitute Excel's escaped double quote "" for "
        str= str.replace('""', '"')
        length = len(str)
        if length > 255:
            raise Exception("String in formula has more than 255 chars")
        return pack("<BB", self._ptg['ptgStr'], length) + str

    def _convert_ref2d(self, cell, cl):
        """Convert an Excel reference such as A1, $B2, C$3 or $D$4 to a ptgRefV."""
        row, col = self._cell_to_packed_rowcol(cell)
        # The ptg value depends on the class of the ptg.
        if cl == 0:
            ptgRef = pack("<B", self._ptg['ptgRef'])
        elif cl == 1:
            ptgRef = pack("<B", self._ptg['ptgRefV'])
        elif cl == 2:
            ptgRef = pack("<B", self._ptg['ptgRefA'])
        else:
            raise Exception("Unknown function class in formula")
        return ptgRef + str(row) + (col)

    def _convert_ref3d(self, cell3d, cl):
        """Convert an Excel 3d reference such as "Sheet1!A1" or "Sheet1:Sheet2!A1" to a
        ptgRef3dV.

        """
        # Split the ref at the ! symbol
        ext_ref, cell = cell3d.split('!', 1)
        # Convert the external reference part
        ext_ref = self._pack_ext_ref(ext_ref)
        # Convert the cell reference part
        row, col = self._cell_to_packed_rowcol(cell)
        # The ptg value depends on the class of the ptg.
        if cl == 0:
            ptgRef = pack("<B", self._ptg['ptgRef3d'])
        elif cl == 1:
            ptgRef = pack("<B", self._ptg['ptgRef3dV'])
        elif cl == 2:
            ptgRef = pack("<B", self._ptg['ptgRef3dA'])
        else:
            raise Exception("Unknown function class in formula")
        return ptgRef + ext_ref + str(row) + str(col)

    def _convert_range2d(self, cellrange, cl):
        """Convert an Excel range such as A1:D4 or A:D to a ptgRefV."""
        # Split the range into 2 cell refs
        cell1, cell2 = cellrange.split(':', 1)
        # A range such as A:D is equivalent to A1:D16384, so add rows as required
        if not re.search(r"\d", cell1):
            cell1 += '1'
        if not re.search(r"\d", cell2):
            cell2 += str(self._max_row)
        # Convert the cell references
        row1, col1 = self._cell_to_packed_rowcol(cell1)
        row2, col2 = self._cell_to_packed_rowcol(cell2)
        # The ptg value depends on the class of the ptg.
        if cl == 0:
            ptgArea = pack("<B", self._ptg['ptgArea'])
        elif cl == 1:
            ptgArea = pack("<B", self._ptg['ptgAreaV'])
        elif cl == 2:
            ptgArea = pack("<B", self._ptg['ptgAreaA'])
        else:
            raise Exception("Unknown function class in formula")
        return ptgArea + row1 + row2 + col1 + col2

    def _convert_range3d(self, range3d, cl):
        """Convert an Excel 3d range such as "Sheet1!A1:D4" or "Sheet1:Sheet2!A1:D4" to
        a ptgArea3dV.

        """
        # Split the ref at the ! symbol
        ext_ref, range = range3d.split('!')
        # Convert the external reference part
        ext_ref = self._pack_ext_ref(ext_ref)
        # Split the range into 2 cell refs
        cell1, cell2 = range.split(':')
        # A range such as A:D is equivalent to A1:D16384, so add rows as required
        if not re.search(r"\d", cell1):
            cell1 += '1'
        if not re.search(r"\d", cell2):
            cell2 += str(self._max_row)
        # Convert the cell references
        row1, col1 = self._cell_to_packed_rowcol(cell1)
        row2, col2 = self._cell_to_packed_rowcol(cell2)
        # The ptg value depends on the class of the ptg.
        if cl == 0:
            ptgArea = pack("<B", self._ptg['ptgArea3d'])
        elif cl == 1:
            ptgArea = pack("<B", self._ptg['ptgArea3dV'])
        elif cl == 2:
            ptgArea = pack("<B", self._ptg['ptgArea3dA'])
        else:
            raise Exception("Unknown function class in formula")
        return ptgArea + ext_ref + row1 + row2 + col1 + col2

    def _pack_ext_ref(self, ext_ref):
        """Convert the sheet name part of an external reference, for example "Sheet1" or
        "Sheet1:Sheet2", to a packed structure.

        """
        if ext_ref.startswith("'"):
            ext_ref = ext_ref[1:]
        if ext_ref.endswith("'"):
            ext_ref = ext_ref[:-1]
        # Check if there is a sheet range eg., Sheet1:Sheet2.
        if ext_ref.find(':') >= 0:
            sheet1, sheet2 = ext_ref.split(':')
            sheet1 = self._get_sheet_index(sheet1)
            sheet2 = self._get_sheet_index(sheet2)
            # Reverse max and min sheet numbers if necessary
            if (sheet1 > sheet2):
                sheet1, sheet2 = sheet2, sheet1
        else:
            # Single sheet name only.
            sheet1, sheet2 = ext_ref, ext_ref
            sheet1 = self._get_sheet_index(sheet1)
            sheet2 = sheet1
        # References are stored relative to 0xFFFF (-1).
        offset = 0xFFFF - sheet1
        return pack("<HdHH", offset, float(0x00), sheet1, sheet2)

    def _get_sheet_index(self, sheetname):
        """Look up the index that corresponds to an external sheet name. The hash of
        sheet names is updated by the addworksheet() method of the Workbook class.

        """
        try:
            ind = self._ext_sheets[sheetname]
        except KeyError:
            raise Exception("Unknown sheet name %s in formula" % (sheetname))
        return ind

    def set_ext_sheets(self, key, value):
        """This semi-public method is used to update the hash of sheet names. It is
        updated by the addworksheet() method of the Workbook class.

        """
        self._ext_sheets[key] = value

    def _convert_function(self, token, num_args):
        """Convert a function to a ptgFunc or ptgFuncVarV depending on the number of
        args that it takes.

        """
        functions = self._functions
        if not functions.has_key(token):
            raise Exception("Unknown function %s() in formula" % (token))
        args = functions[token][1]
        # Fixed number of args eg. TIME(i,j,k).
        if args >= 0:
            # Check that the number of args is valid.
            if args != num_args:
                raise Exception("Incorrect number of arguments for token() in formula")
            else:
                return pack("<BH", self._ptg['ptgFuncV'], functions[token][0])
        # Variable number of args eg. SUM(i,j,k, ..).
        if args == -1:
            return pack("<BBH", self._ptg['ptgFuncVarV'], num_args, functions[token][0])

    def _cell_to_packed_rowcol(self, cell):
        """pack() row and column into the required 3 byte format."""
        row, col, row_abs, col_abs = cell_to_rowcol(cell)
        if col >= self._max_col:
            raise Exception("Column %s greater than IV in formula" % cell)
        if row >= self._max_row:
            raise Exception("Row %s greater than %d in formula" % (cell, self._max_row))
        row |= int(not row_abs) << 15
        row |= int(not col_abs) << 14
        row = pack("<H", row)
        col = pack("<B", col)
        return row, col

    def _initialize_hashes(self):
        # The Excel ptg indices
        self._ptg = {
            'ptgExp'       : 0x01,
            'ptgTbl'       : 0x02,
            'ptgAdd'       : 0x03,
            'ptgSub'       : 0x04,
            'ptgMul'       : 0x05,
            'ptgDiv'       : 0x06,
            'ptgPower'     : 0x07,
            'ptgConcat'    : 0x08,
            'ptgLT'        : 0x09,
            'ptgLE'        : 0x0A,
            'ptgEQ'        : 0x0B,
            'ptgGE'        : 0x0C,
            'ptgGT'        : 0x0D,
            'ptgNE'        : 0x0E,
            'ptgIsect'     : 0x0F,
            'ptgUnion'     : 0x10,
            'ptgRange'     : 0x11,
            'ptgUplus'     : 0x12,
            'ptgUminus'    : 0x13,
            'ptgPercent'   : 0x14,
            'ptgParen'     : 0x15,
            'ptgMissArg'   : 0x16,
            'ptgStr'       : 0x17,
            'ptgAttr'      : 0x19,
            'ptgSheet'     : 0x1A,
            'ptgEndSheet'  : 0x1B,
            'ptgErr'       : 0x1C,
            'ptgBool'      : 0x1D,
            'ptgInt'       : 0x1E,
            'ptgNum'       : 0x1F,
            'ptgArray'     : 0x20,
            'ptgFunc'      : 0x21,
            'ptgFuncVar'   : 0x22,
            'ptgName'      : 0x23,
            'ptgRef'       : 0x24,
            'ptgArea'      : 0x25,
            'ptgMemArea'   : 0x26,
            'ptgMemErr'    : 0x27,
            'ptgMemNoMem'  : 0x28,
            'ptgMemFunc'   : 0x29,
            'ptgRefErr'    : 0x2A,
            'ptgAreaErr'   : 0x2B,
            'ptgRefN'      : 0x2C,
            'ptgAreaN'     : 0x2D,
            'ptgMemAreaN'  : 0x2E,
            'ptgMemNoMemN' : 0x2F,
            'ptgNameX'     : 0x39,
            'ptgRef3d'     : 0x3A,
            'ptgArea3d'    : 0x3B,
            'ptgRefErr3d'  : 0x3C,
            'ptgAreaErr3d' : 0x3D,
            'ptgArrayV'    : 0x40,
            'ptgFuncV'     : 0x41,
            'ptgFuncVarV'  : 0x42,
            'ptgNameV'     : 0x43,
            'ptgRefV'      : 0x44,
            'ptgAreaV'     : 0x45,
            'ptgMemAreaV'  : 0x46,
            'ptgMemErrV'   : 0x47,
            'ptgMemNoMemV' : 0x48,
            'ptgMemFuncV'  : 0x49,
            'ptgRefErrV'   : 0x4A,
            'ptgAreaErrV'  : 0x4B,
            'ptgRefNV'     : 0x4C,
            'ptgAreaNV'    : 0x4D,
            'ptgMemAreaNV' : 0x4E,
            'ptgMemNoMemN' : 0x4F,
            'ptgFuncCEV'   : 0x58,
            'ptgNameXV'    : 0x59,
            'ptgRef3dV'    : 0x5A,
            'ptgArea3dV'   : 0x5B,
            'ptgRefErr3dV' : 0x5C,
            'ptgAreaErr3d' : 0x5D,
            'ptgArrayA'    : 0x60,
            'ptgFuncA'     : 0x61,
            'ptgFuncVarA'  : 0x62,
            'ptgNameA'     : 0x63,
            'ptgRefA'      : 0x64,
            'ptgAreaA'     : 0x65,
            'ptgMemAreaA'  : 0x66,
            'ptgMemErrA'   : 0x67,
            'ptgMemNoMemA' : 0x68,
            'ptgMemFuncA'  : 0x69,
            'ptgRefErrA'   : 0x6A,
            'ptgAreaErrA'  : 0x6B,
            'ptgRefNA'     : 0x6C,
            'ptgAreaNA'    : 0x6D,
            'ptgMemAreaNA' : 0x6E,
            'ptgMemNoMemN' : 0x6F,
            'ptgFuncCEA'   : 0x78,
            'ptgNameXA'    : 0x79,
            'ptgRef3dA'    : 0x7A,
            'ptgArea3dA'   : 0x7B,
            'ptgRefErr3dA' : 0x7C,
            'ptgAreaErr3d' : 0x7D,
        }
        # Thanks to Michael Meeks and Gnumeric for the initial arg values.
        #
        # The following hash was generated by "function_locale.pl" in the distro.
        # Refer to function_locale.pl for non-English function names.
        #
        # The array elements are as follow:
        # ptg:   The Excel function ptg code.
        # args:  The number of arguments that the function takes:
        #           >=0 is a fixed number of arguments.
        #           -1  is a variable  number of arguments.
        # class: The reference, value or array class of the function args.
        # vol:   The function is volatile.
        #
        self._functions = {
            #                    ptg  args  class  vol
            'COUNT'        : [   0,   -1,    0,    0 ],
            'IF'           : [   1,   -1,    1,    0 ],
            'ISNA'         : [   2,    1,    1,    0 ],
            'ISERROR'      : [   3,    1,    1,    0 ],
            'SUM'          : [   4,   -1,    0,    0 ],
            'AVERAGE'      : [   5,   -1,    0,    0 ],
            'MIN'          : [   6,   -1,    0,    0 ],
            'MAX'          : [   7,   -1,    0,    0 ],
            'ROW'          : [   8,   -1,    0,    0 ],
            'COLUMN'       : [   9,   -1,    0,    0 ],
            'NA'           : [  10,    0,    0,    0 ],
            'NPV'          : [  11,   -1,    1,    0 ],
            'STDEV'        : [  12,   -1,    0,    0 ],
            'DOLLAR'       : [  13,   -1,    1,    0 ],
            'FIXED'        : [  14,   -1,    1,    0 ],
            'SIN'          : [  15,    1,    1,    0 ],
            'COS'          : [  16,    1,    1,    0 ],
            'TAN'          : [  17,    1,    1,    0 ],
            'ATAN'         : [  18,    1,    1,    0 ],
            'PI'           : [  19,    0,    1,    0 ],
            'SQRT'         : [  20,    1,    1,    0 ],
            'EXP'          : [  21,    1,    1,    0 ],
            'LN'           : [  22,    1,    1,    0 ],
            'LOG10'        : [  23,    1,    1,    0 ],
            'ABS'          : [  24,    1,    1,    0 ],
            'INT'          : [  25,    1,    1,    0 ],
            'SIGN'         : [  26,    1,    1,    0 ],
            'ROUND'        : [  27,    2,    1,    0 ],
            'LOOKUP'       : [  28,   -1,    0,    0 ],
            'INDEX'        : [  29,   -1,    0,    1 ],
            'REPT'         : [  30,    2,    1,    0 ],
            'MID'          : [  31,    3,    1,    0 ],
            'LEN'          : [  32,    1,    1,    0 ],
            'VALUE'        : [  33,    1,    1,    0 ],
            'TRUE'         : [  34,    0,    1,    0 ],
            'FALSE'        : [  35,    0,    1,    0 ],
            'AND'          : [  36,   -1,    1,    0 ],
            'OR'           : [  37,   -1,    1,    0 ],
            'NOT'          : [  38,    1,    1,    0 ],
            'MOD'          : [  39,    2,    1,    0 ],
            'DCOUNT'       : [  40,    3,    0,    0 ],
            'DSUM'         : [  41,    3,    0,    0 ],
            'DAVERAGE'     : [  42,    3,    0,    0 ],
            'DMIN'         : [  43,    3,    0,    0 ],
            'DMAX'         : [  44,    3,    0,    0 ],
            'DSTDEV'       : [  45,    3,    0,    0 ],
            'VAR'          : [  46,   -1,    0,    0 ],
            'DVAR'         : [  47,    3,    0,    0 ],
            'TEXT'         : [  48,    2,    1,    0 ],
            'LINEST'       : [  49,   -1,    0,    0 ],
            'TREND'        : [  50,   -1,    0,    0 ],
            'LOGEST'       : [  51,   -1,    0,    0 ],
            'GROWTH'       : [  52,   -1,    0,    0 ],
            'PV'           : [  56,   -1,    1,    0 ],
            'FV'           : [  57,   -1,    1,    0 ],
            'NPER'         : [  58,   -1,    1,    0 ],
            'PMT'          : [  59,   -1,    1,    0 ],
            'RATE'         : [  60,   -1,    1,    0 ],
            'MIRR'         : [  61,    3,    0,    0 ],
            'IRR'          : [  62,   -1,    0,    0 ],
            'RAND'         : [  63,    0,    1,    1 ],
            'MATCH'        : [  64,   -1,    0,    0 ],
            'DATE'         : [  65,    3,    1,    0 ],
            'TIME'         : [  66,    3,    1,    0 ],
            'DAY'          : [  67,    1,    1,    0 ],
            'MONTH'        : [  68,    1,    1,    0 ],
            'YEAR'         : [  69,    1,    1,    0 ],
            'WEEKDAY'      : [  70,   -1,    1,    0 ],
            'HOUR'         : [  71,    1,    1,    0 ],
            'MINUTE'       : [  72,    1,    1,    0 ],
            'SECOND'       : [  73,    1,    1,    0 ],
            'NOW'          : [  74,    0,    1,    1 ],
            'AREAS'        : [  75,    1,    0,    1 ],
            'ROWS'         : [  76,    1,    0,    1 ],
            'COLUMNS'      : [  77,    1,    0,    1 ],
            'OFFSET'       : [  78,   -1,    0,    1 ],
            'SEARCH'       : [  82,   -1,    1,    0 ],
            'TRANSPOSE'    : [  83,    1,    1,    0 ],
            'TYPE'         : [  86,    1,    1,    0 ],
            'ATAN2'        : [  97,    2,    1,    0 ],
            'ASIN'         : [  98,    1,    1,    0 ],
            'ACOS'         : [  99,    1,    1,    0 ],
            'CHOOSE'       : [ 100,   -1,    1,    0 ],
            'HLOOKUP'      : [ 101,   -1,    0,    0 ],
            'VLOOKUP'      : [ 102,   -1,    0,    0 ],
            'ISREF'        : [ 105,    1,    0,    0 ],
            'LOG'          : [ 109,   -1,    1,    0 ],
            'CHAR'         : [ 111,    1,    1,    0 ],
            'LOWER'        : [ 112,    1,    1,    0 ],
            'UPPER'        : [ 113,    1,    1,    0 ],
            'PROPER'       : [ 114,    1,    1,    0 ],
            'LEFT'         : [ 115,   -1,    1,    0 ],
            'RIGHT'        : [ 116,   -1,    1,    0 ],
            'EXACT'        : [ 117,    2,    1,    0 ],
            'TRIM'         : [ 118,    1,    1,    0 ],
            'REPLACE'      : [ 119,    4,    1,    0 ],
            'SUBSTITUTE'   : [ 120,   -1,    1,    0 ],
            'CODE'         : [ 121,    1,    1,    0 ],
            'FIND'         : [ 124,   -1,    1,    0 ],
            'CELL'         : [ 125,   -1,    0,    1 ],
            'ISERR'        : [ 126,    1,    1,    0 ],
            'ISTEXT'       : [ 127,    1,    1,    0 ],
            'ISNUMBER'     : [ 128,    1,    1,    0 ],
            'ISBLANK'      : [ 129,    1,    1,    0 ],
            'T'            : [ 130,    1,    0,    0 ],
            'N'            : [ 131,    1,    0,    0 ],
            'DATEVALUE'    : [ 140,    1,    1,    0 ],
            'TIMEVALUE'    : [ 141,    1,    1,    0 ],
            'SLN'          : [ 142,    3,    1,    0 ],
            'SYD'          : [ 143,    4,    1,    0 ],
            'DDB'          : [ 144,   -1,    1,    0 ],
            'INDIRECT'     : [ 148,   -1,    1,    1 ],
            'CALL'         : [ 150,   -1,    1,    0 ],
            'CLEAN'        : [ 162,    1,    1,    0 ],
            'MDETERM'      : [ 163,    1,    2,    0 ],
            'MINVERSE'     : [ 164,    1,    2,    0 ],
            'MMULT'        : [ 165,    2,    2,    0 ],
            'IPMT'         : [ 167,   -1,    1,    0 ],
            'PPMT'         : [ 168,   -1,    1,    0 ],
            'COUNTA'       : [ 169,   -1,    0,    0 ],
            'PRODUCT'      : [ 183,   -1,    0,    0 ],
            'FACT'         : [ 184,    1,    1,    0 ],
            'DPRODUCT'     : [ 189,    3,    0,    0 ],
            'ISNONTEXT'    : [ 190,    1,    1,    0 ],
            'STDEVP'       : [ 193,   -1,    0,    0 ],
            'VARP'         : [ 194,   -1,    0,    0 ],
            'DSTDEVP'      : [ 195,    3,    0,    0 ],
            'DVARP'        : [ 196,    3,    0,    0 ],
            'TRUNC'        : [ 197,   -1,    1,    0 ],
            'ISLOGICAL'    : [ 198,    1,    1,    0 ],
            'DCOUNTA'      : [ 199,    3,    0,    0 ],
            'ROUNDUP'      : [ 212,    2,    1,    0 ],
            'ROUNDDOWN'    : [ 213,    2,    1,    0 ],
            'RANK'         : [ 216,   -1,    0,    0 ],
            'ADDRESS'      : [ 219,   -1,    1,    0 ],
            'DAYS360'      : [ 220,   -1,    1,    0 ],
            'TODAY'        : [ 221,    0,    1,    1 ],
            'VDB'          : [ 222,   -1,    1,    0 ],
            'MEDIAN'       : [ 227,   -1,    0,    0 ],
            'SUMPRODUCT'   : [ 228,   -1,    2,    0 ],
            'SINH'         : [ 229,    1,    1,    0 ],
            'COSH'         : [ 230,    1,    1,    0 ],
            'TANH'         : [ 231,    1,    1,    0 ],
            'ASINH'        : [ 232,    1,    1,    0 ],
            'ACOSH'        : [ 233,    1,    1,    0 ],
            'ATANH'        : [ 234,    1,    1,    0 ],
            'DGET'         : [ 235,    3,    0,    0 ],
            'INFO'         : [ 244,    1,    1,    1 ],
            'DB'           : [ 247,   -1,    1,    0 ],
            'FREQUENCY'    : [ 252,    2,    0,    0 ],
            'ERROR.TYPE'   : [ 261,    1,    1,    0 ],
            'REGISTER.ID'  : [ 267,   -1,    1,    0 ],
            'AVEDEV'       : [ 269,   -1,    0,    0 ],
            'BETADIST'     : [ 270,   -1,    1,    0 ],
            'GAMMALN'      : [ 271,    1,    1,    0 ],
            'BETAINV'      : [ 272,   -1,    1,    0 ],
            'BINOMDIST'    : [ 273,    4,    1,    0 ],
            'CHIDIST'      : [ 274,    2,    1,    0 ],
            'CHIINV'       : [ 275,    2,    1,    0 ],
            'COMBIN'       : [ 276,    2,    1,    0 ],
            'CONFIDENCE'   : [ 277,    3,    1,    0 ],
            'CRITBINOM'    : [ 278,    3,    1,    0 ],
            'EVEN'         : [ 279,    1,    1,    0 ],
            'EXPONDIST'    : [ 280,    3,    1,    0 ],
            'FDIST'        : [ 281,    3,    1,    0 ],
            'FINV'         : [ 282,    3,    1,    0 ],
            'FISHER'       : [ 283,    1,    1,    0 ],
            'FISHERINV'    : [ 284,    1,    1,    0 ],
            'FLOOR'        : [ 285,    2,    1,    0 ],
            'GAMMADIST'    : [ 286,    4,    1,    0 ],
            'GAMMAINV'     : [ 287,    3,    1,    0 ],
            'CEILING'      : [ 288,    2,    1,    0 ],
            'HYPGEOMDIST'  : [ 289,    4,    1,    0 ],
            'LOGNORMDIST'  : [ 290,    3,    1,    0 ],
            'LOGINV'       : [ 291,    3,    1,    0 ],
            'NEGBINOMDIST' : [ 292,    3,    1,    0 ],
            'NORMDIST'     : [ 293,    4,    1,    0 ],
            'NORMSDIST'    : [ 294,    1,    1,    0 ],
            'NORMINV'      : [ 295,    3,    1,    0 ],
            'NORMSINV'     : [ 296,    1,    1,    0 ],
            'STANDARDIZE'  : [ 297,    3,    1,    0 ],
            'ODD'          : [ 298,    1,    1,    0 ],
            'PERMUT'       : [ 299,    2,    1,    0 ],
            'POISSON'      : [ 300,    3,    1,    0 ],
            'TDIST'        : [ 301,    3,    1,    0 ],
            'WEIBULL'      : [ 302,    4,    1,    0 ],
            'SUMXMY2'      : [ 303,    2,    2,    0 ],
            'SUMX2MY2'     : [ 304,    2,    2,    0 ],
            'SUMX2PY2'     : [ 305,    2,    2,    0 ],
            'CHITEST'      : [ 306,    2,    2,    0 ],
            'CORREL'       : [ 307,    2,    2,    0 ],
            'COVAR'        : [ 308,    2,    2,    0 ],
            'FORECAST'     : [ 309,    3,    2,    0 ],
            'FTEST'        : [ 310,    2,    2,    0 ],
            'INTERCEPT'    : [ 311,    2,    2,    0 ],
            'PEARSON'      : [ 312,    2,    2,    0 ],
            'RSQ'          : [ 313,    2,    2,    0 ],
            'STEYX'        : [ 314,    2,    2,    0 ],
            'SLOPE'        : [ 315,    2,    2,    0 ],
            'TTEST'        : [ 316,    4,    2,    0 ],
            'PROB'         : [ 317,   -1,    2,    0 ],
            'DEVSQ'        : [ 318,   -1,    0,    0 ],
            'GEOMEAN'      : [ 319,   -1,    0,    0 ],
            'HARMEAN'      : [ 320,   -1,    0,    0 ],
            'SUMSQ'        : [ 321,   -1,    0,    0 ],
            'KURT'         : [ 322,   -1,    0,    0 ],
            'SKEW'         : [ 323,   -1,    0,    0 ],
            'ZTEST'        : [ 324,   -1,    0,    0 ],
            'LARGE'        : [ 325,    2,    0,    0 ],
            'SMALL'        : [ 326,    2,    0,    0 ],
            'QUARTILE'     : [ 327,    2,    0,    0 ],
            'PERCENTILE'   : [ 328,    2,    0,    0 ],
            'PERCENTRANK'  : [ 329,   -1,    0,    0 ],
            'MODE'         : [ 330,   -1,    2,    0 ],
            'TRIMMEAN'     : [ 331,    2,    0,    0 ],
            'TINV'         : [ 332,    2,    1,    0 ],
            'CONCATENATE'  : [ 336,   -1,    1,    0 ],
            'POWER'        : [ 337,    2,    1,    0 ],
            'RADIANS'      : [ 342,    1,    1,    0 ],
            'DEGREES'      : [ 343,    1,    1,    0 ],
            'SUBTOTAL'     : [ 344,   -1,    0,    0 ],
            'SUMIF'        : [ 345,   -1,    0,    0 ],
            'COUNTIF'      : [ 346,    2,    0,    0 ],
            'COUNTBLANK'   : [ 347,    1,    0,    0 ],
            'ROMAN'        : [ 354,   -1,    1,    0 ],
        }
