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
#
# See the README.txt distributed with pyXLWriter for more details.

"""pyXLWriter.parse

TODO: IMHO, using of PLY is not good idea for this project.

"""
__revision__ = """$Id: parse.py,v 1.18 2004/08/20 05:16:16 fufff Exp $"""

import re
import lex
import yacc

__all__ = ["parse"]


#############################################################################
# lex

tokens = (
    'NUMBER', 'STRING',
    'ADD','SUB','MUL','DIV','COMMA',
    'REF2D', 'REF3D_1', 'REF3D_2', 'RANGE2D', 'RANGE3D_1', 'RANGE3D_2',
    'LPAREN','RPAREN',
    'TRUE', 'FALSE',
    "CONCAT", "EQ", "NE", "LE", "GE", "LT", "GT", 'POWER',
    'FNAME', )

# Tokens
t_COMMA   = r','
t_ADD     = r'\+'
t_SUB     = r'-'
t_MUL     = r'\*'
t_DIV     = r'/'
t_LPAREN  = r'\('
t_RPAREN  = r'\)'

t_CONCAT  = r'&'
t_EQ      = r'='
t_NE      = r'<>'
t_LE      = r'<='
t_GE      = r'>='
t_LT      = r'<'
t_GT      = r'>'
t_POWER   = r'\^'

# Match A1, $A1, A$1 or $A$1.
t_REF2D = r"\$?[A-I]?[A-Z]\$?\d+"

# Match an external sheet reference: Sheet1!A1 or 'Sheet (1)'!A1
t_REF3D_1 = r"[^!(,]+!\$?[A-I]?[A-Z]\$?\d+"
t_REF3D_2 = r"'[^']+'!\$?[A-I]?[A-Z]\$?\d+"

# Match A1:C5, $A1:$C5 or A:C etc.
t_RANGE2D = r"\$?[A-I]?[A-Z]\$?(\d+)?:\$?[A-I]?[A-Z]\$?(\d+)?"

t_RANGE3D_1 = r"[^!(,]+!\$?[A-I]?[A-Z]\$?(\d+)?:\$?[A-I]?[A-Z]\$?(\d+)?"
t_RANGE3D_2 = r"'[^']+'!\$?[A-I]?[A-Z]\$?(\d+)?:\$?[A-I]?[A-Z]\$?(\d+)?"

t_TRUE = r"TRUE"
t_FALSE = r"FALSE"

t_NUMBER  = r"(?=\d|\.\d)\d*(\.\d*)?([Ee]([+-]?\d+))?"  # ([+-]?)
t_STRING = r'"[^"]*"'

re_name = re.compile(r"([a-zA-Z_][a-zA-Z0-9_]*)")
def t_FNAME(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*\w*\('
    s = t.value
    m = re_name.match(s)
    if m:
        res = m.group(1)
        t.value = res
        return t

t_ignore = " \t"

def t_error(t):
    print "Illegal character '%s'" % t.value[0]
    t.skip(1)

lex.lex(lextab='_lextab', optimize=1)

#############################################################################
# yacc

def _linize_list(list):
    reslist = []
    for item in list:
        reslist += item
    return reslist

# Parsing rules

precedence = (
    ('left', 'ADD', 'SUB', 'COMMA', "CONCAT", "EQ", "NE", "LE", "GE", "LT", "GT", 'POWER'),
    ('left', 'MUL', 'DIV'),
    ('right', 'UMINUS'),
)

def p_statement_list(t):
    'statement : list'
    list_len = len(t[1])
    t[0] = _linize_list(t[1])
    t[0] += ["_arg", list_len]

def p_list_comma(t):
    """list : list COMMA expression"""
    t[0] = t[1]
    t[0].append(t[3])

def p_list_expression(t):
    """list : expression"""
    t[0] = [t[1]]

_bin_operators = {
    '^': 'ptgPower', '*': 'ptgMul', '/': 'ptgDiv',
    '+': 'ptgAdd', '-': 'ptgSub', '&': 'ptgConcat',
    '=': 'ptgEQ', '<>': 'ptgNE',
    '<=': 'ptgLE', '>=': 'ptgGE', '<': 'ptgLT', '>': 'ptgGT',
}

def p_expression_binop(t):
    """expression : expression POWER expression
                  | expression MUL expression
                  | expression DIV expression
                  | expression ADD expression
                  | expression SUB expression
                  | expression CONCAT expression
                  | expression EQ expression
                  | expression NE expression
                  | expression LE expression
                  | expression GE expression
                  | expression LT expression
                  | expression GT expression"""
    op = _bin_operators[t[2]]
    t[0] = t[1] + t[3] + [op]

def p_expression_string(t):
    'expression : STRING'
    t[0] = ['_str', t[1]]

def _number(s):
    try:
        val = int(s)
    except ValueError:
        val = float(s)
    return val

def p_expression_uminus_number(t):
    'expression : SUB NUMBER %prec UMINUS'
    t[0] = ['_num', -_number(t[2])]

def p_expression_number(t):
    'expression : NUMBER'
    t[0] = ['_num', _number(t[1])]

def p_expression_group(t):
    'expression : LPAREN expression RPAREN'
    t[0] = t[2] + ['_arg', 1, 'ptgParen']

def p_expression_ref2d(t):
    'expression : REF2D'
    t[0] = ['_ref2d', t[1]]

def p_expression_ref3d(t):
    """expression : REF3D_1
                  | REF3D_2"""
    t[0] = ['_ref3d', t[1]]

def p_expression_range2d(t):
    'expression : RANGE2D'
    t[0] = ['_range2d', t[1]]

def p_expression_range3d(t):
    """expression : RANGE3D_1
                  | RANGE3D_2"""
    t[0] = ['_range3d', t[1]]

def p_expression_true(t):
    'expression : TRUE'
    t[0] = ['ptgBool', 1]

def p_expression_false(t):
    'expression : FALSE'
    t[0] = ['ptgBool', 0]

def p_expression_function(t):
    'expression : function'
    t[0] = t[1]

def p_function_void(t):
    'function : FNAME RPAREN'
    t[0] = ['_class', t[1], '_func', t[1]]

#~ def p_function_expression(t):
    #~ 'function : FNAME expression RPAREN'
    #~ t[0] = ['_class', t[1]] + t[2] + ['_arg', 1, '_func', t[1]]

def p_function_list(t):
    'function : FNAME list RPAREN'
    list_len = len(t[2])
    list = _linize_list(t[2])
    t[0] = ['_class', t[1]] + list + ['_arg', list_len, '_func', t[1]]

def p_error(t):
    print "Syntax error at '%s'" % t.value

yacc.yacc(tabmodule='_parsetab', optimize=1, debug=0)

#############################################################################

def parse(formula):
    """Alias for yacc.parse.

    This function is used as method of the 'class' parse (this module).

    """
    return yacc.parse(formula)


if __name__ == "__main__":
    print yacc.parse("1*2,6+3")
    print yacc.parse("1+2*3")
