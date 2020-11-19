# -*- coding: utf-8 -*-
"""
DSV.py - Cliff Wells, 2002
  Import/export DSV (delimiter separated values, a generalization of CSV).

Basic use:

   from DSV import DSV

   data = file.read()
   qualifier = DSV.guessTextQualifier(data) # optional
   data = DSV.organizeIntoLines(data, textQualifier = qualifier)
   delimiter = DSV.guessDelimiter(data) # optional
   data = DSV.importDSV(data, delimiter = delimiter, textQualifier = qualifier)
   hasHeader = DSV.guessHeaders(data) # optional

If you know the delimiters, qualifiers, etc, you may skip the optional
'guessing' steps as they rely on heuristics anyway (although they seem
to work well, there is no guarantee they are correct). What they are
best used for is to make a good guess regarding the data structure and then
let the user confirm it.

As such there is a 'wizard' to aid in this process (use this in lieu of
the above code - requires wxPython):

   from DSV import DSV

   dlg = DSV.ImportWizardDialog(parent, -1, 'DSV Import Wizard', filename)
   dlg.ShowModal()
   headers, data = dlg.ImportData() # may also return None
   dlg.Destroy()

The dlg.ImportData() method may also take a function as an optional argument
specifying what it should do about malformed rows.  See the example at the bottom
of this file. A few common functions are provided in this file (padRow, skipRow,
useRow).

Requires Python 2.0 or later
Wizards tested with wxPython 2.2.5/NT 4.0, 2.3.2/Win2000 and Linux/GTK (RedHat 7.x)
"""

__version__ = '1.4'

"""
Bugs/Caveats:
   - Although I've tested this stuff on varied data, I'm sure there are cases
     that I haven't seen that will choke any one of these routines (or at least
     return invalid data). This is beta code!
   - guessTextQualifier() algorithm is limited to quotes (double or single).
   - Surprising feature: Hitting <enter> on wxSpinCtrl causes seg
     fault under Linux/GTK (not Win32). Strangely, pressing <tab> seems ok.
     Therefore, I had to use wxSpinButton.  Also, spurious spin events get
     generated for both of these controls (e.g. when calling wxBeginBusyCursor)
   - Keyboard navigation needs to be implemented on wizards
   - There may be issues with cr/lf translation, although I haven't yet seen any.
   
Why another CSV tool?:
   - Because I needed a more flexible CSV importer, one that could accept different
     delimiters (not just commas or tabs), one that could make an intelligent guess
     regarding file structure (for user convenience), be compatible with the files
     output by MS Excel, and finally, be easily integrated with a wizard.  All of the
     modules I have seen prior to this fell short on one count or another.
   - It seemed interesting.
     
To do:
   - Better guessTextQualifier() algorithm. In the perfect world I envision, I can
     use any character as a text qualifier, not just quotes.
   - Finish wizards and move them into separate module.
   - Better guessHeaders() algorithm, although this is difficult.
   - Optimize maps() - try to eliminate lambda when possible
   - Optimize memory usage.  Presently the entire file is loaded and then saved as
     a list.  A better approach might be to analyze a smaller part of the file and
     then return an iterator to step through it.
"""

# Changelog
# 1.4:
#   - Fixed small bug in demo (forgotten Destroy()) that caused a hang
#     when Cancel was pressed.
#   - Removed extraneous guessHeaders() call in wizard.  I can only say,
#     "what the??" and remember to profile.  This was a huge time waster.
#
# 1.3.9
#   - Fixed real problem on Win32 in that wxProgressDialog must reach max
#     value in order to close.
#
# 1.3.8
#   - Change demo to use wxApp rather than wxPySimpleApp as it seemed
#     to have problems on Win32 (per Kevin Altis)
#
# 1.37
#   - Fix for font issue under GTK2 (thanks to Ahmad Baitalmal)
#   - Added some space below the Ok/Cancel buttons.
#
# 1.36
#   - Bugfix submitted by "nobody" ;) on SF
#
# 1.3.4 to 1.3.5:
#   - Nigel Hathaway finds yet another bug (or two).  Can't seem to make him
#     use something else, so they had to be fixed.  It's especially difficult
#     to ignore him since he provided the fix.  Very annoying.
#     - Problem with odd quote/delimiter combinations (SF bug #620284)
#     - Losing empty fields at beginning/end (#619771)
#     - Whitespace stripped from around string (#620115)
#
# 1.3.3 to 1.3.4(a):
#   - Fixed bug in exportDSV that failed to quote data containing delimiter
#     thanks to nhathaway@users.sourceforge.net
#
# 1.3 to 1.3.1:
#   - Test for presence of wxPython (since it's not required except for wizard)
#   - Changed "from wxPython.wx import *" to "from wxPython import wx"
#   - Changed sample csv file (darkwave.csv) to demonstrate embedded quotes

import sys
# import pre as re # sre was broken, appears okay now. Try this if there are problems.
import re 
import copy
#import exceptions
import string
# RedHat 8.0 (or rather GTK2?) sets LANG = en_us.UTF-8 and apparently some
# older apps (including wxGTK) can't handle this.  The fix is to set LANG=C
# before running the app.  Thanks to Ahmad Baitalmal for supplying this info.
import os
from functools import reduce
os.putenv('LANG', 'C')

import gettext
_ = gettext.gettext

import wx
import wx.grid

class InvalidDelimiter(Exception): pass
class InvalidTextQualifier(Exception): pass
class InvalidData(Exception): pass
class InvalidNumberOfColumns(Exception): pass

# ------------------------------------------------------------------------------
def guessTextQualifier(input):
    """
    PROTOTYPE:
      guessTextQualifier(input)
    DESCRIPTION:
      tries to guess if the text qualifier (a character delimiting ambiguous data)
      is a single or double-quote (or None)
    ARGUMENTS:
      - input is raw data as a string
    RETURNS:
      single character or None
    """
    
    # Algorithm: looks for text enclosed between two identical quotes (the probable
    # qualifier) which are preceded and followed by the same character (the
    # probable delimiter), for example:
    #                        ,'some text',
    # The quote with the most wins.
    
    data = input[:16 * 1024] # limit sample to 16k
    
    regexp = re.compile('(?:(?:^|\n)(?P<b_quote>["\']).*?(?P=b_quote))|'
                        '(?:(?P<delim>.)(?P<quote>["\']).*?(?P=quote)(?=(?P=delim)|\n))|'
                        '(?:(?P<e_quote>["\']).*?(?P=e_quote)$)', re.M | re.S)
    matches = [i for i in regexp.findall(data) if reduce(lambda a, b: a + b, i)]
    if not matches: return None
    
    quotes = {}
    for q in ('b_quote', 'quote', 'e_quote'):
        n = regexp.groupindex[q] - 1
        for m in matches:
            key = m[n]
            if key:
                quotes[key] = quotes.get(key, 0) + 1

    return reduce(lambda a, b, quotes = quotes:
                  (quotes[a] > quotes[b]) and a or b, list(quotes.keys()))
    
# ------------------------------------------------------------------------------
def guessDelimiter(input, textQualifier = '"'):
    """
    PROTOTYPE:
      guessDelimiter(input, textQualifier = '\"')
    DESCRIPTION:
      Tries to guess the delimiter.
    ARGUMENTS:
      - input is raw data as string
      - textQualifier is a character used to delimit ambiguous data
    RETURNS:
      single character or None
    """
    
    # Algorithm: the delimiter /should/ occur the same number of times on each
    # row. However, due to malformed data, it may not. We don't want an all or
    # nothing approach, so we allow for small variations in the number.
    # 1) build a table of the frequency of each character on every line.
    # 2) build a table of freqencies of this frequency (meta-frequency?), e.g.
    #     "x occurred 5 times in 10 rows, 6 times in 1000 rows, 7 times in 2 rows"
    # 3) use the mode of the meta-frequency to decide what the frequency /should/
    #    be for that character 
    # 4) find out how often the character actually meets that goal 
    # 5) the character that best meets its goal is the delimiter 
    # For performance reasons, the data is evaluated in chunks, so it can try
    # and evaluate the smallest portion of the data possible, evaluating additional
    # chunks as necessary. 

    if type(input) != type([]): return None
    if len(input) < 2: return None

    if textQualifier:
        # eliminate text inside textQualifiers
        regexp = re.compile('%s(.*?)%s' % (textQualifier, textQualifier), re.S)
        subCode = compile("regexp.sub('', line)", '', 'eval')
    else:
        subCode = compile("line", '', 'eval')

    ascii = [chr(c) for c in range(127)] # 7-bit ASCII

    # build frequency tables
    chunkLength = min(10, len(input))
    iteration = 0
    charFrequency = {}
    modes = {}
    delims = {}
    start, end = 0, min(chunkLength, len(input))
    while start < len(input):
        iteration += 1
        for line in input[start:end]:
            l = eval(subCode)
            for char in ascii:
                metafrequency = charFrequency.get(char, {})
                freq = l.strip().count(char) # must count even if frequency is 0
                metafrequency[freq] = metafrequency.get(freq, 0) + 1 # value is the mode
                charFrequency[char] = metafrequency

        for char in list(charFrequency.keys()):
            items = list(charFrequency[char].items())
            if len(items) == 1 and items[0][0] == 0: continue
            # get the mode of the frequencies
            if len(items) > 1:
                modes[char] = reduce(lambda a, b: a[1] > b[1] and a or b, items)
                # adjust the mode - subtract the sum of all other frequencies
                items.remove(modes[char])
                modes[char] = (modes[char][0], modes[char][1]
                               - reduce(lambda a, b: (0, a[1] + b[1]), items)[1])
            else:
                modes[char] = items[0]

        # build a list of possible delimiters
        modeList = list(modes.items())
        total = float(chunkLength * iteration)
        consistency = 1.0 # (rows of consistent data) / (number of rows) = 100%
        threshold = 0.9  # minimum consistency threshold
        while len(delims) == 0 and consistency >= threshold:
            for k, v in modeList:
                if v[0] > 0 and v[1] > 0:
                    if (v[1]/total) >= consistency:
                        delims[k] = v
            consistency -= 0.01

        if len(delims) == 1:
            return list(delims.keys())[0]

        # analyze another chunkLength lines
        start = end
        end += chunkLength

    if not delims: return None
    
    # if there's more than one candidate, look at quoted data for clues.
    # while any character may be quoted, any delimiter that occurs as a
    # part of the data /must/ be quoted.
    if len(delims) > 1 and textQualifier is not None:
        regexp = re.compile('%s(.*?)%s' % (textQualifier, textQualifier), re.S)
        for line in input:
            inQuotes = "".join(regexp.findall(line))
            for d in list(delims.keys()):
                if not d in inQuotes:
                    del delims[d]
                if len(delims) == 1:
                    return list(delims.keys())[0]
    
    # if there's *still* more than one, fall back to a 'preferred' list
    if len(delims) > 1:
        for d in ['\t', ',', ';', ' ', ':']:
            if d in list(delims.keys()):
                return d
            
    # finally, just return the first damn character in the list
    return list(delims.keys())[0]

# ------------------------------------------------------------------------------
def modeOfLengths(input):
    """
    PROTOTYPE:
      modeOfLengths(input)
    DESCRIPTION:
      Finds the mode (most frequently occurring value) of the lengths of the lines.
    ARGUMENTS:
      - input is list of lists of data
    RETURNS:
      mode as integer
    """
    freq = {}
    for row in input:
        l = len(row)
        freq[l] = freq.get(l, 0) + 1

    return reduce(lambda a, b, freq = freq: (freq[a] > freq[b]) and a or b, list(freq.keys()))

# ------------------------------------------------------------------------------
def guessHeaders(input, columns = 0):
    """
    PROTOTYPE:
      guessHeaders(input, columns = 0)
    DESCRIPTION:
      Decides whether row 0 is a header row
    ARGUMENTS:
      - input is a list of lists of data (as returned by importDSV)
      - columns is either the expected number of columns in each row or 0
    RETURNS:
      - true if data has header row
    """
    
    # Algorithm: creates a dictionary of types of data in each column. If any column
    # is of a single type (say, integers), *except* for the first row, then the first
    # row is presumed to be labels. If the type can't be determined, it is assumed to
    # be a string in which case the length of the string is the determining factor: if
    # all of the rows except for the first are the same length, it's a header.
    # Finally, a 'vote' is taken at the end for each column, adding or subtracting from
    # the likelihood of the first row being a header. 

    if type(input) != type([]): raise InvalidData("list expected.")
    if len(input) < 2: return 0

    if not columns:
        columns = modeOfLengths(input)
        
    columnTypes = {}
    for i in range(columns): columnTypes[i] = None
    
    for row in input[1:]:
        if len(row) != columns:
            continue # skip rows that have irregular number of columns
        for col in list(columnTypes.keys()):
            try:
                try:
                    # is it a built-in type (besides string)?
                    thisType = type(eval(row[col]))
                except OverflowError:
                    # a long int?
                    thisType = type(eval(row[col] + 'L'))
                    thisType = type(0) # treat long ints as int
            except:
                # fallback to length of string
                thisType = len(row[col])

            if thisType != columnTypes[col]:
                if columnTypes[col] is None: # add new column type
                    columnTypes[col] = thisType
                else: # type is inconsistent, remove column from consideration
                    del columnTypes[col]
                    
    # finally, compare results against first row and vote on whether it's a header
    hasHeader = 0
    for col, colType in list(columnTypes.items()):
        if type(colType) == type(0): # it's a length
            if len(input[0][col]) != colType:
                hasHeader += 1
            else:
                hasHeader -= 1
        else: # attempt typecast
            try:
                eval("%s(%s)" % (colType.__name__, input[0][col]))
            except:
                hasHeader += 1
            else:
                hasHeader -= 1

    return hasHeader > 0

# ------------------------------------------------------------------------------
def organizeIntoLines(input, textQualifier = '"', limit = None):
    """
    PROTOTYPE:
      organizeIntoLines(input, textQualifier = '\"', limit = None)
    DESCRIPTION:
      Takes raw data (as from file.read()) and organizes it into lines.
      Newlines that occur within text qualifiers are treated as normal
      characters, not line delimiters.
    ARGUMENTS:
      - input is raw data as a string
      - textQualifier is a character used to delimit ambiguous data
      - limit is a integer specifying the maximum number of lines to organize
    RETURNS:
      list of strings
    """
    
    # Algorithm: there should be an even number of text qualifiers on every line.
    # If there isn't, that means that the newline at the end of the line must occur
    # within qualifiers and doesn't really indicate the end of a record.
    
    data = input.split('\n')
    line = 0
    while 1:
        try:
            while data[line].count(textQualifier) % 2: # while odd number
                data[line] = data[line] + '\n' + data[line + 1] # add the next line
                del data[line + 1] # delete the next line
            line += 1
            if limit and line > limit:
                del data[limit:] # kill any lines that weren't processed
                break
        except:
            break
        
    # filter out empty lines
    data = list(filter(lambda i: "".join(i), data))
    #data = list(filter(string.join, data))
    return data

# ------------------------------------------------------------------------------
# some common error handlers to pass to importDSV
# others might do things like log errors to a file.
# oldrow is the unparsed data, newrow is the parsed data
def padRow(oldrow, newrow, columns, maxColumns):
    "pads all rows to the same length with empty strings"
    difference = maxColumns - len(newrow)
    return newrow + ([''] * difference)

def skipRow(oldrow, newrow, columns, maxColumns):
    "skips any inconsistent rows"
    return None

def useRow(oldrow, newrow, columns, maxColumns):
    "returns row unchanged"
    return newrow

# ------------------------------------------------------------------------------
def importDSV(input, delimiter = ',', textQualifier = '"', columns = 0,
              updateFunction = None, errorHandler = None):
    """
    PROTOTYPE:
      importDSV(input, delimiter = ',', textQualifier = '\"', columns = 0,
                updateFunction = None, errorHandler = None)
    DESCRIPTION:
      parses lines of data in CSV format
    ARGUMENTS:
      - input is a list of strings (built by organizeIntoLines)
      - delimiter is the character used to delimit columns
      - textQualifier is the character used to delimit ambiguous data
      - columns is the expected number of columns in each row or 0
      - updateFunction is a callback function called once per record (could be
        used for updating progress bars). Its prototype is
           updateFunction(percentDone)
           - percentDone is an integer between 0 and 100
      - errorHandler is a callback invoked whenever a row has an unexpected number
        of columns. Its prototype is
           errorHandler(oldrow, newrow, columns, maxColumns)
              where
              - oldrow is the unparsed data
              - newrow is the parsed data
              - columns is the expected length of a row
              - maxColumns is the longest row in the data
    RETURNS:
      list of lists of data
    """
    if type(input) != type([]):
        raise InvalidData("expected list of lists of strings")  
    if type(delimiter) != type('') or not delimiter:
        raise InvalidDelimiter(repr(delimiter))

##    if textQualifier:
##        # fieldRex=re.compile('(?:(?:[,]|^)"(.*?)"(?=[,]|$))|(?:(?:[,]|^)([^",]*?)(?=[,]|$))')
##        fieldRex = re.compile('(?:(?:[%s]|^)%s(.*?)%s(?=[%s]|$))|(?:(?:[%s]|^)([^%s%s]*?)(?=[%s]|$))'
##                              % (delimiter, textQualifier, textQualifier, delimiter,
##                                 delimiter, textQualifier, delimiter, delimiter),
##                              re.S)
##    else:
##        fieldRex = re.compile('(?:[%s]|^)([^%s]*?)(?=[%s]|$)'
##                              % (delimiter, delimiter, delimiter), re.S)

    percent = 0.0
    lineno = 0.0
    newdata = []
    maxColumns = 0

##    for line in input:
##        line = line.strip()
##        record = fieldRex.findall(line)
##        print record
##        if textQualifier:
##            record = [(i[0] or i[1]) for i in record]

##        if textQualifier:
##            record = [c.replace(textQualifier * 2, textQualifier) for c in record]
##        newdata.append(record)

    # This code was submitted by Nigel to replace the code commented out above.
    # It addresses several issues with embedded quotes and delimiters.  It seems that
    # while off to a good start, regular expressions won't be able to handle certain
    # situations. i.e. '''"Say ""hello"", World", ""''' would seem to be a problem as
    # an embedded delimiter follows an embedded quote which throws off the re search.

    for line in input:
        if textQualifier:
            record = []
            inquotes = 0
            for s in line.split(delimiter):
                odd = s.count(textQualifier) % 2
                if inquotes:
                    accu += delimiter + s.replace(textQualifier * 2, delimiter).\
                            replace(textQualifier, '').replace(delimiter, textQualifier)
                    if odd:
                        record.append(accu)
                        inquotes = 0
                else:
                    # 1.3.6 bugfix: deal with case where s = "" to denote an empty string
                    if s.count(textQualifier): # discard whitespace outside of textQualifiers when they are used
                        s = s.strip()
                    # fix new problem with ""
                    if s == textQualifier * 2: 
                        s = ""

                    accu = s.replace(textQualifier * 2, delimiter).\
                           replace(textQualifier, '').replace(delimiter, textQualifier)
                    if odd:
                        inquotes = 1
                    else:
                        record.append(accu)
        else:
            record = list(map(lambda x: x.strip(), line.split(delimiter)))
            #record = list(map(string.strip, line.split(delimiter)))

        newdata.append(record)
        # (end of replacement code)
        
        if updateFunction is not None:
            lineno = lineno + 1.0
            newpercent = int((lineno / len(input)) * 100)
            if percent != newpercent:
                percent = newpercent
                if not updateFunction(percent):
                    return None
    
    if not columns:
        columns = modeOfLengths(newdata)
    maxColumns = max([len(line) for line in newdata])

    # consistency check
    for record in range(len(newdata)):
        length = len(newdata[record])
        difference = length - columns
        if difference:
            if errorHandler is None:
                raise InvalidNumberOfColumns(_("Expected %d, got %d") % (columns, length))
            else:
                newdata[record] = errorHandler(input[record], newdata[record], columns, maxColumns)
    
    # remove null values from data
    newdata = [_f for _f in newdata if _f]
    
    return newdata


# ------------------------------------------------------------------------------
def exportDSV(input, delimiter = ',', textQualifier = '"', quoteall = 0):
    """
    PROTOTYPE:
      exportDSV(input, delimiter = ',', textQualifier = '\"', quoteall = 0)
    DESCRIPTION:
      Exports to DSV (delimiter-separated values) format.
    ARGUMENTS:
      - input is list of lists of data (as returned by importDSV)
      - delimiter is character used to delimit columns
      - textQualifier is character used to delimit ambiguous data
      - quoteall is boolean specifying whether to quote all data or only data
        that requires it
    RETURNS:
      data as string
    """
    if not delimiter or type(delimiter) != type(''): raise InvalidDelimiter
    if not textQualifier or type(delimiter) != type(''): raise InvalidTextQualifier

    # double-up all text qualifiers in data (i.e. can't becomes can''t)
    data = list(map(lambda i, q = textQualifier:
               list(map(lambda j, q = q: str(j).replace(q, q * 2), i)),
               input))

    if quoteall: # quote every data value
        data = list(map(lambda i, q = textQualifier:
                   list(map(lambda j, q = q: q + j + q, i)),
                   data))
    else: # quote only the values that contain qualifiers, delimiters or newlines
        data = list(map(lambda i, q = textQualifier, d = delimiter:
                   list(map(lambda j, q = q, d = d: ((j.find(q) != -1 or j.find(d) != -1
                                          or j.find('\n') != -1)
                                         and (q + j + q)) or j, i)), data))
    # assemble each line with delimiters
    data = [delimiter.join(line) for line in data]
    
    # assemble all lines together, separated by newlines
    data = "\n".join(data)
    return data

if wx is not None:
    # ------------------------------------------------------------------------------
    class ImportWizardPanel_Delimiters(wx.Panel):
        """
        CLASS(SUPERCLASS):
          ImportWizardPanel_Delimiters(wx.Panel)
        DESCRIPTION:
          A wx.Panel that provides a basic interface for validating and changing the
          parameters for importing a delimited text file. Similar to MS Excel's
          CSV import wizard. Can be used in a series of wizards or embedded in an
          application.
        PROTOTYPE:
          ImportWizardPanel_Delimiters(parent, id, file, data, isValidCallback = None,
                                       pos = wx.DefaultPosition, size = wx.DefaultSize,
                                       style = wxTAB_TRAVERSAL, name = 'ImportWizardPanel')
        ARGUMENTS:
          - parent is the parent window
          - id is the id of this wizard panel
          - file is the name of the file being imported
          - data is the raw data to be parsed
          - isValidCallback is a callback function that accepts a single boolean argument
            If the argument is true, the wizard is in a valid state (all the settings are
            acceptable), if the argument is false, trying to import will likely cause an
            exception.
        METHODS:
          - GetDelimiters()
            returns list of characters used as delimiters
          - GetTextQualifiers()
            returns character used as text qualifier or None
          - GetHasHeaders()
            returns true if first row is header
        """

        def __init__(self, parent, id, file, data, isValidCallback = None,
                     pos = wx.DefaultPosition, size = wx.DefaultSize,
                     style = wx.TAB_TRAVERSAL, name = "ImportWizardPanel"):
            wx.Panel.__init__(self, parent, id, pos, size, style, name)
            self.SetAutoLayout(True)
            mainSizer = wx.FlexGridSizer(4, 1, gap=wx.Size(0,0))
            self.SetSizer(mainSizer)
            mainSizer.AddGrowableCol(0)

            self.initialized = False
            self.data = data
            self.isValidCallback = isValidCallback
            self.Validate = (isValidCallback and self.Validate) or self.BuildPreview

            dlg = wx.ProgressDialog(_("Import Wizard"),
                                   _("Analyzing %s... Please wait.") % file,
                                   3,
                                   parent,
                                   wx.PD_APP_MODAL | wx.PD_AUTO_HIDE)
            textQualifier = guessTextQualifier(data)
            dlg.Update(1)
            newdata = organizeIntoLines(data, textQualifier = textQualifier, limit = 100)
            dlg.Update(2)
            delimiter = guessDelimiter(newdata, textQualifier = textQualifier)
            dlg.Update(3)
            dlg.Destroy()

            # -------------
            msg = (_("This screen lets you set the delimiters your data contains.\n"
                   "You can see how your data is affected in the preview below."))
            message1 = wx.StaticText(self, -1, msg)

            # -------------
            delimiterBox = wx.BoxSizer(wx.HORIZONTAL)
            delimStaticBox = wx.StaticBox(self, -1, _("Delimiters"))
            delimStaticSizer = wx.StaticBoxSizer(delimStaticBox, wx.VERTICAL)
            delimGridSizer = wx.FlexGridSizer(2, 3, gap=wx.Size(0,0))

            delims = {
                _('Tab'):       '\t',
                _('Semicolon'): ';',
                _('Comma'):     ',',
                _('Space'):     ' ',
                }

            self.delimChecks = {}

            for label, value in list(delims.items()):
                self.delimChecks[value] = wx.CheckBox(self, -1, label)
                delimGridSizer.Add(self.delimChecks[value], 0, wx.ALL, 3)
                wx.EVT_CHECKBOX(self, self.delimChecks[value].GetId(), self.Validate)

            otherSizer = wx.BoxSizer(wx.HORIZONTAL)

            self.delimChecks['Other'] = wx.CheckBox(self, -1, _('Other:'))
            wx.EVT_CHECKBOX(self, self.delimChecks['Other'].GetId(), self.Validate)

            self.otherDelim = wx.TextCtrl(self, -1, size = (20, -1))
            wx.EVT_TEXT(self, self.otherDelim.GetId(), self.OnCustomDelim)

            if delimiter in self.delimChecks:
                self.delimChecks[delimiter].SetValue(True)
            elif delimiter is not None:
                self.delimChecks['Other'].SetValue(wx.T)
                self.otherDelim.SetValue(delimiter)

            otherSizer.AddMany([
                (self.delimChecks['Other'], 0, wx.ALL, 3),
                (self.otherDelim, 0, wx.ALIGN_CENTER),
                ])
            
            delimGridSizer.Add(otherSizer)
            delimStaticSizer.Add(delimGridSizer, 1, wx.EXPAND)
            delimOtherSizer = wx.BoxSizer(wx.VERTICAL)
            self.consecutiveDelimsAs1 = wx.CheckBox(self, -1, _("Treat consecutive delimiters as one"))
            self.consecutiveDelimsAs1.Enable(False)
            tqSizer = wx.BoxSizer(wx.HORIZONTAL)
            self.textQualifierChoice = wx.Choice(self, -1, choices = ['"', "'", "{None}"])
            wx.EVT_CHOICE(self, self.textQualifierChoice.GetId(), self.BuildPreview)
            if textQualifier is not None:
                self.textQualifierChoice.SetStringSelection(textQualifier)
            else:
                self.textQualifierChoice.SetStringSelection('{None}')
                
            tqSizer.AddMany([
                (wx.StaticText(self, -1, _("Text qualifier:")), 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL),
                (self.textQualifierChoice, 0, wx.ALL | wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL, 5),
                ])
            
            delimOtherSizer.AddMany([
                (self.consecutiveDelimsAs1, 1, wx.EXPAND | wx.ALL, 5),
                (tqSizer, 1, wx.ALL | wx.ALIGN_CENTER, 5),
                ])

            delimiterBox.AddMany([
                (delimStaticSizer, 0, wx.ALIGN_CENTER),
                (delimOtherSizer,  0, wx.ALIGN_CENTER),
                ])
            
            delimStaticBox.Fit()

            # -------------
            self.displayRows = 6
            previewSettingsBox = wx.BoxSizer(wx.HORIZONTAL)
            self.hasHeaderRow = wx.CheckBox(self, -1, _("First row is header"))
            wx.EVT_CHECKBOX(self, self.hasHeaderRow.GetId(), self.BuildPreview)

            if wx.Platform in ('__WX.WXGTK__', '__WX.WXMSW__'):
                # wx.SpinCtrl causes seg fault under GTK when <enter> is hit in text - use wx.SpinButton instead
                self.previewRowsText = wx.TextCtrl(self, -1, str(self.displayRows),
                                                  size = (30, -1), style = wx.TE_PROCESS_ENTER)
                h = self.previewRowsText.GetSize().height
                self.previewRows = wx.SpinButton(self, -1, size = (-1, h), style = wx.SP_VERTICAL)
                self.previewRows.SetRange(self.displayRows, 100)
                self.previewRows.SetValue(self.displayRows)
                wx.EVT_SPIN(self, self.previewRows.GetId(), self.OnSpinPreviewRows)
                wx.EVT_TEXT_ENTER(self, self.previewRowsText.GetId(), self.OnTextPreviewRows)
            else:
                self.previewRows = wx.SpinCtrl(self, -1, str(self.displayRows),
                                              min = self.displayRows, max = 100, size = (50, -1))
                wx.EVT_SPINCTRL(self, self.previewRows.GetId(), self.BuildPreview)

            previewSettingsBox.AddMany([
                (self.hasHeaderRow, 1, wx.ALL | wx.EXPAND, 5),
                (wx.StaticText(self, -1, _("Preview")), 0, wx.WEST | wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 10),
                ])
            if wx.Platform in ('__WX.WXGTK__', '__WX.WXMSW__'):
                previewSettingsBox.Add(self.previewRowsText, 0, wx.ALIGN_CENTER | wx.ALL, 3)
            previewSettingsBox.AddMany([
                (self.previewRows, 0, wx.ALIGN_CENTER | wx.ALL, 3),
                (wx.StaticText(self, -1, _("rows")), 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL),
                ])

            # -------------
            if delimiter is not None:
                previewData = importDSV(newdata[:self.displayRows],
                                        textQualifier = textQualifier,
                                        delimiter = delimiter,
                                        errorHandler = padRow)
                hasHeaders = guessHeaders(previewData)
                self.hasHeaderRow.SetValue(hasHeaders)

                cols = len(previewData[0])
            else:
                previewData = []
                hasHeaders = 0
                cols = 1

            previewStaticBox = wx.StaticBox(self, -1, _("Data Preview"))
            previewStaticSizer = wx.StaticBoxSizer(previewStaticBox, wx.VERTICAL)
            self.preview = wx.grid.Grid(self, -1)
            self.preview.CreateGrid(self.displayRows, cols)
            #self.preview.SetDefaultRowSize(self.preview.GetCharHeight() + 4, rue)
            self.preview.EnableEditing(False)
            self.preview.SetColLabelSize(0)
            self.preview.SetRowLabelSize(0)
            self.preview.SetMargins(1, 0)
            self.initialized = True
            self.BuildPreview()

            rowheight = self.preview.GetRowSize(0) + 2
            self.preview.SetSize((-1, rowheight * self.displayRows))
            previewStaticSizer.Add(self.preview, 0, wx.ALL | wx.EXPAND, 5)

            # -------------
            mainSizer.AddMany([
                (message1,     0, wx.ALL, 5),
                (delimiterBox, 0, wx.ALL, 5),
                (previewSettingsBox, 0, wx.ALL, 5),
                (previewStaticSizer, 0, wx.ALL | wx.EXPAND, 5)
                ])

            self.Layout()
            self.Fit()

        def OnSpinPreviewRows(self, event):
            self.previewRowsText.SetValue(str(event.GetPosition()))
            self.BuildPreview()

        def OnTextPreviewRows(self, event):
            try:    v = int(self.previewRowsText.GetValue())
            except: v = self.displayRows
            v = max(self.displayRows, v)
            v = min(v, 100)
            self.previewRowsText.SetValue(str(v))
            self.previewRows.SetValue(v)
            self.BuildPreview()

        def Validate(self, event = None):
            hasDelimiter = reduce(lambda a, b: a + b, [cb.GetValue() for cb in list(self.delimChecks.values())])
            if hasDelimiter == 1 and self.delimChecks['Other'].GetValue():
                hasDelimiter = self.otherDelim.GetValue() != ""
            self.BuildPreview()
            self.isValidCallback(hasDelimiter)

        def BuildPreview(self, event = None):
            if not self.initialized:
                return # got triggered before initialization was completed

            if wx.Platform != '__WX.WXGTK__':
                wx.BeginBusyCursor() # causes a spurious spin event under GTK
            wx.Yield() # allow controls to update first, in case of slow preview
            self.preview.BeginBatch()
            self.preview.DeleteCols(0, self.preview.GetNumberCols())
            self.preview.DeleteRows(0, self.preview.GetNumberRows())
            self.preview.ClearGrid()

            textQualifier = self.textQualifierChoice.GetStringSelection()
            if textQualifier == '{None}': textQualifier = None
            other = self.otherDelim.GetValue()
            delimiter = list(map(lambda i, other = other: i[0] != 'Other' and i[0] or other,
                            [i for i in list(self.delimChecks.items()) if i[1].GetValue()]))
            delimiter = "".join(delimiter)

            rows = self.previewRows.GetValue()

            newdata = organizeIntoLines(self.data, textQualifier, limit = rows)
            try:
                previewData = importDSV(newdata[:rows],
                                        textQualifier = textQualifier,
                                        delimiter = delimiter,
                                        errorHandler = padRow)
            except InvalidDelimiter as e:
                previewData = [[i] for i in newdata[:rows]]

            rows = min(rows, len(previewData))
            hasHeaders = self.hasHeaderRow.GetValue()
            self.preview.AppendRows(rows - hasHeaders)
            cols = max([len(row) for row in previewData])
            self.preview.AppendCols(cols)

            if hasHeaders:
                self.preview.SetColLabelSize(self.preview.GetRowSize(0))
                for col in range(cols):
                    try:    self.preview.SetColLabelValue(col, str(previewData[0][col]))
                    except: self.preview.SetColLabelValue(col, "")
                # self.preview.AutoSizeColumns(wx.true) # size columns to headers
            else:
                self.preview.SetColLabelSize(0)

            for row in range(hasHeaders, rows):
                for col in range(cols):
                    try:    self.preview.SetCellValue(row - hasHeaders, col, str(previewData[row][col]))
                    except: pass

            # if not hasHeaders:
            self.preview.AutoSizeColumns(True) # size columns to data

            rowheight = self.preview.GetRowSize(0)
            self.preview.SetRowSize(0, rowheight)
            self.preview.EndBatch()
            if wx.Platform != '__WX.WXGTK__':
                wx.EndBusyCursor()

            self.delimiters = delimiter
            self.textQualifier = textQualifier
            self.hasHeaders = hasHeaders

        def OnCustomDelim(self, event = None):
            self.delimChecks['Other'].SetValue(len(self.otherDelim.GetValue()))
            self.Validate()

        def GetDelimiters(self):
            return self.delimiters

        def GetTextQualifier(self):
            return self.textQualifier

        def GetHasHeaders(self):
            return self.hasHeaders

    # ------------------------------------------------------------------------------        
    class ImportWizardDialog(wx.Dialog):
        """
        CLASS(SUPERCLASS):
          ImportWizardDialog(wx.Dialog)
        DESCRIPTION:
          A dialog allowing the user to preview and change the options for importing
          a file.
        PROTOTYPE:
          ImportWizardDialog(parent, id, title, file,
                             pos = wx.DefaultPosition, size = wx.DefaultSize,
                             style = wx.DEFAULT_DIALOG_STYLE, name = 'ImportWizardDialog')
        ARGUMENTS:
          - parent: the parent window
          - id: the id of this window
          - title: the title of this dialog
          - file: the file to import
        METHODS:
          - GetImportInfo()
            returns a tuple (delimiters, text qualifiers, has headers)
          - ImportData(errorHandler = skipRow)
            returns (headers, data), headers may be None
            errorHandler is a callback function that instructs the method on what
            to do with irregular rows. The default skipRow function simply discards
            the bad row (see importDSV() above).
        """

        def __init__(self, parent, id, title, file,
                     pos = wx.DefaultPosition, size = wx.DefaultSize,
                     style = wx.DEFAULT_DIALOG_STYLE, name = "ImportWizardDialog"):
            wx.Dialog.__init__(self, parent, id, title, pos, size, style, name)
            self.SetAutoLayout(True)

            self.file = file
            f = open(file, 'r')
            self.data = f.read()
            f.close()

            sizer = wx.BoxSizer(wx.VERTICAL)
            self.delimPanel = ImportWizardPanel_Delimiters(self, -1, file, self.data, self.ValidState)
            buttonBox = self.ButtonBox()
            sizer.AddMany([
                (self.delimPanel, 0, wx.ALL, 5),
                (buttonBox, 0, wx.SOUTH | wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_TOP, 0),
                ])

            self.SetSizer(sizer)
            self.Layout()
            sizer.Fit(self.delimPanel)
            self.Fit()
            self.Centre()

        def ButtonBox(self):
            panel = wx.Panel(self, -1)
            panel.SetAutoLayout(True)
            sizer = wx.BoxSizer(wx.HORIZONTAL)
            panel.SetSizer(sizer)
            self.ok = wx.Button(panel, wx.ID_OK, "")
            cancel = wx.Button(panel, wx.ID_CANCEL, "")
            sizer.AddMany([
                (self.ok, 0, wx.ALIGN_TOP | wx.EAST | wx.SOUTH, 10),
                (cancel, 0, wx.ALIGN_TOP | wx.WEST | wx.SOUTH, 10),
                ])
            panel.Layout()
            panel.Fit()
            return panel

        def GetImportInfo(self):
            return (self.delimPanel.GetDelimiters(),
                    self.delimPanel.GetTextQualifier(),
                    self.delimPanel.GetHasHeaders())

        def ImportData(self, errorHandler = skipRow):
            delimiters, qualifier, hasHeaders = self.GetImportInfo()
            self.data = organizeIntoLines(self.data, textQualifier = qualifier)
            dlg = wx.ProgressDialog(_("Import DSV File"),
                                   self.file,
                                   100,
                                   self,
                                   wx.PD_CAN_ABORT | wx.PD_APP_MODAL | wx.PD_AUTO_HIDE)
            self.data = importDSV(self.data,
                                  delimiter = delimiters,
                                  textQualifier = qualifier,
                                  updateFunction = dlg.Update,
                                  errorHandler = errorHandler)
            if self.data is None: return None
            if hasHeaders:
                headers = copy.copy(self.data[0])
                del self.data[0]
            else:
                headers = None
            return (headers, self.data)

        def ValidState(self, isValid):
            self.ok.Enable(isValid)


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    #if wx is None:
        #print "\nYou need wxPython to run this sample*."
        #print "\n*Note that wxPython is _not_ necessary to use this module, but it is required"
        #print "to use the wizard dialog (which the sample requires)."
        #raise SystemExit


    def demo():
        class SampleApp(wx.App):
            def OnInit(self):
                dlg = wx.FileDialog(None, "Choose a file", ".", "",
                                   "CSV files (*.csv)|*.csv|Text files (*.txt)|*.txt|All files (*.*)|*.*",
                                   wx.OPEN)
                if dlg.ShowModal() == wx.ID_OK:
                    path = dlg.GetPath()
                    dlg.Destroy()

                    errorLog = open('import_error.log', 'a+') 
                    def logErrors(oldrow, newrow, expectedColumns, maxColumns, file = errorLog):
                        # log the bad row to a file
                        file.write(oldrow + '\n')

                    dlg = ImportWizardDialog(None, -1, 'CSV Import Wizard (v.%s)' % __version__, path)
                    if dlg.ShowModal() == wx.ID_OK:
                        results = dlg.ImportData(errorHandler = logErrors)
                        dlg.Destroy()
                        errorLog.close()

                        if results is not None:
                            headers, data = results
                            if 0: # print the output to stdout
                                if headers:
                                    print(headers)
                                    print(80*'=')
                                for row in data:
                                    print(row)

                            if 0: # for testing export functionality
                                if headers:
                                    print(exportDSV([headers] + data))
                                else:
                                    print(exportDSV(data))
                    else:
                        dlg.Destroy()

                else:
                    dlg.Destroy()

                return True

        app = SampleApp()
        app.MainLoop()

    demo()
