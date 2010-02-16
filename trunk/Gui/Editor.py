# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# Editor.py ---
#                     --------------------------------
#                        Copyright (c) 2009
#                       Laurent CAPOCCHI
#                      University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GLOBAL VARIABLES AND FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import wx
import os
import sys
import keyword
import inspect

from wx import stc

from ReloadModule import recompile
import Container

if wx.Platform == '__WXMSW__':
    faces = { 'times': 'Times New Roman',
              'mono' : 'Courier New',
              'helv' : 'Arial',
              'other': 'Comic Sans MS',
              'size' : 10,
              'size2': 8,
             }
elif wx.Platform == '__WXMAC__':
    faces = { 'times': 'Times New Roman',
              'mono' : 'Monaco',
              'helv' : 'Arial',
              'other': 'Comic Sans MS',
              'size' : 12,
              'size2': 10,
             }
else:
    faces = { 'times': 'Times',
              'mono' : 'Courier',
              'helv' : 'Helvetica',
              'other': 'new century schoolbook',
              'size' : 12,
              'size2': 10,
             }


###----------------------------------------------------------------------
class PythonSTC(stc.StyledTextCtrl):

    fold_symbols = 2
    
    def __init__(self, parent, ID,
                 pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=0):
        stc.StyledTextCtrl.__init__(self, parent, ID, pos, size, style)

        self.CmdKeyAssign(ord('B'), stc.STC_SCMOD_CTRL, stc.STC_CMD_ZOOMIN)
        self.CmdKeyAssign(ord('N'), stc.STC_SCMOD_CTRL, stc.STC_CMD_ZOOMOUT)

        self.SetLexer(stc.STC_LEX_PYTHON)
        self.SetKeyWords(0, " ".join(keyword.kwlist))

        self.SetProperty("fold", "1")
        self.SetProperty("tab.timmy.whinge.level", "1")
        self.SetMargins(0,0)

        self.SetViewWhiteSpace(False)
        #self.SetBufferedDraw(False)
        #self.SetViewEOL(True)
        #self.SetEOLMode(stc.STC_EOL_CRLF)
        #self.SetUseAntiAliasing(True)
        
        self.SetEdgeMode(stc.STC_EDGE_BACKGROUND)
        self.SetEdgeColumn(78)

        # Setup a margin to hold fold markers
        self.SetMarginType(2, stc.STC_MARGIN_SYMBOL)
        self.SetMarginMask(2, stc.STC_MASK_FOLDERS)
        self.SetMarginSensitive(2, True)
        self.SetMarginWidth(2, 12)

        if self.fold_symbols == 0:
            # Arrow pointing right for contracted folders, arrow pointing down for expanded
            self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPEN,    stc.STC_MARK_ARROWDOWN, "black", "black")
            self.MarkerDefine(stc.STC_MARKNUM_FOLDER,        stc.STC_MARK_ARROW, "black", "black")
            self.MarkerDefine(stc.STC_MARKNUM_FOLDERSUB,     stc.STC_MARK_EMPTY, "black", "black")
            self.MarkerDefine(stc.STC_MARKNUM_FOLDERTAIL,    stc.STC_MARK_EMPTY, "black", "black")
            self.MarkerDefine(stc.STC_MARKNUM_FOLDEREND,     stc.STC_MARK_EMPTY,     "white", "black")
            self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPENMID, stc.STC_MARK_EMPTY,     "white", "black")
            self.MarkerDefine(stc.STC_MARKNUM_FOLDERMIDTAIL, stc.STC_MARK_EMPTY,     "white", "black")
            
        elif self.fold_symbols == 1:
            # Plus for contracted folders, minus for expanded
            self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPEN,    stc.STC_MARK_MINUS, "white", "black")
            self.MarkerDefine(stc.STC_MARKNUM_FOLDER,        stc.STC_MARK_PLUS,  "white", "black")
            self.MarkerDefine(stc.STC_MARKNUM_FOLDERSUB,     stc.STC_MARK_EMPTY, "white", "black")
            self.MarkerDefine(stc.STC_MARKNUM_FOLDERTAIL,    stc.STC_MARK_EMPTY, "white", "black")
            self.MarkerDefine(stc.STC_MARKNUM_FOLDEREND,     stc.STC_MARK_EMPTY, "white", "black")
            self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPENMID, stc.STC_MARK_EMPTY, "white", "black")
            self.MarkerDefine(stc.STC_MARKNUM_FOLDERMIDTAIL, stc.STC_MARK_EMPTY, "white", "black")

        elif self.fold_symbols == 2:
            # Like a flattened tree control using circular headers and curved joins
            self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPEN,    stc.STC_MARK_CIRCLEMINUS,          "white", "#404040")
            self.MarkerDefine(stc.STC_MARKNUM_FOLDER,        stc.STC_MARK_CIRCLEPLUS,           "white", "#404040")
            self.MarkerDefine(stc.STC_MARKNUM_FOLDERSUB,     stc.STC_MARK_VLINE,                "white", "#404040")
            self.MarkerDefine(stc.STC_MARKNUM_FOLDERTAIL,    stc.STC_MARK_LCORNERCURVE,         "white", "#404040")
            self.MarkerDefine(stc.STC_MARKNUM_FOLDEREND,     stc.STC_MARK_CIRCLEPLUSCONNECTED,  "white", "#404040")
            self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPENMID, stc.STC_MARK_CIRCLEMINUSCONNECTED, "white", "#404040")
            self.MarkerDefine(stc.STC_MARKNUM_FOLDERMIDTAIL, stc.STC_MARK_TCORNERCURVE,         "white", "#404040")

        elif self.fold_symbols == 3:
            # Like a flattened tree control using square headers
            self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPEN,    stc.STC_MARK_BOXMINUS,          "white", "#808080")
            self.MarkerDefine(stc.STC_MARKNUM_FOLDER,        stc.STC_MARK_BOXPLUS,           "white", "#808080")
            self.MarkerDefine(stc.STC_MARKNUM_FOLDERSUB,     stc.STC_MARK_VLINE,             "white", "#808080")
            self.MarkerDefine(stc.STC_MARKNUM_FOLDERTAIL,    stc.STC_MARK_LCORNER,           "white", "#808080")
            self.MarkerDefine(stc.STC_MARKNUM_FOLDEREND,     stc.STC_MARK_BOXPLUSCONNECTED,  "white", "#808080")
            self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPENMID, stc.STC_MARK_BOXMINUSCONNECTED, "white", "#808080")
            self.MarkerDefine(stc.STC_MARKNUM_FOLDERMIDTAIL, stc.STC_MARK_TCORNER,           "white", "#808080")


        self.Bind(stc.EVT_STC_UPDATEUI, self.OnUpdateUI)
        self.Bind(stc.EVT_STC_MARGINCLICK, self.OnMarginClick)

        # Make some styles,  The lexer defines what each style is used for, we
        # just have to define what each style looks like.  This set is adapted from
        # Scintilla sample property files.

        # Global default styles for all languages
        self.StyleSetSpec(stc.STC_STYLE_DEFAULT,     "face:%(helv)s,size:%(size)d" % faces)
        self.StyleClearAll()  # Reset all to be like the default

        # Global default styles for all languages
        self.StyleSetSpec(stc.STC_STYLE_DEFAULT,     "face:%(helv)s,size:%(size)d" % faces)
        self.StyleSetSpec(stc.STC_STYLE_LINENUMBER,  "back:#C0C0C0,face:%(helv)s,size:%(size2)d" % faces)
        self.StyleSetSpec(stc.STC_STYLE_CONTROLCHAR, "face:%(other)s" % faces)
        self.StyleSetSpec(stc.STC_STYLE_BRACELIGHT,  "fore:#FFFFFF,back:#0000FF,bold")
        self.StyleSetSpec(stc.STC_STYLE_BRACEBAD,    "fore:#000000,back:#FF0000,bold")

        # Python styles
        # Default 
        self.StyleSetSpec(stc.STC_P_DEFAULT, "fore:#000000,face:%(helv)s,size:%(size)d" % faces)
        # Comments
        self.StyleSetSpec(stc.STC_P_COMMENTLINE, "fore:#007F00,face:%(other)s,size:%(size)d" % faces)
        # Number
        self.StyleSetSpec(stc.STC_P_NUMBER, "fore:#007F7F,size:%(size)d" % faces)
        # String
        self.StyleSetSpec(stc.STC_P_STRING, "fore:#7F007F,face:%(helv)s,size:%(size)d" % faces)
        # Single quoted string
        self.StyleSetSpec(stc.STC_P_CHARACTER, "fore:#7F007F,face:%(helv)s,size:%(size)d" % faces)
        # Keyword
        self.StyleSetSpec(stc.STC_P_WORD, "fore:#00007F,bold,size:%(size)d" % faces)
        # Triple quotes
        self.StyleSetSpec(stc.STC_P_TRIPLE, "fore:#7F0000,size:%(size)d" % faces)
        # Triple double quotes
        self.StyleSetSpec(stc.STC_P_TRIPLEDOUBLE, "fore:#7F0000,size:%(size)d" % faces)
        # Class name definition
        self.StyleSetSpec(stc.STC_P_CLASSNAME, "fore:#0000FF,bold,underline,size:%(size)d" % faces)
        # Function or method name definition
        self.StyleSetSpec(stc.STC_P_DEFNAME, "fore:#007F7F,bold,size:%(size)d" % faces)
        # Operators
        self.StyleSetSpec(stc.STC_P_OPERATOR, "bold,size:%(size)d" % faces)
        # Identifiers
        self.StyleSetSpec(stc.STC_P_IDENTIFIER, "fore:#000000,face:%(helv)s,size:%(size)d" % faces)
        # Comment-blocks
        self.StyleSetSpec(stc.STC_P_COMMENTBLOCK, "fore:#7F7F7F,size:%(size)d" % faces)
        # End of line where string is not closed
        self.StyleSetSpec(stc.STC_P_STRINGEOL, "fore:#000000,face:%(mono)s,back:#E0C0E0,eol,size:%(size)d" % faces)

        self.SetCaretForeground("BLUE")

    def OnUpdateUI(self, evt):
        # check for matching braces
        braceAtCaret = -1
        braceOpposite = -1
        charBefore = None
        caretPos = self.GetCurrentPos()

        if caretPos > 0:
            charBefore = self.GetCharAt(caretPos - 1)
            styleBefore = self.GetStyleAt(caretPos - 1)

        # check before
        if charBefore and chr(charBefore) in "[]{}()" and styleBefore == stc.STC_P_OPERATOR:
            braceAtCaret = caretPos - 1

        # check after
        if braceAtCaret < 0:
            charAfter = self.GetCharAt(caretPos)
            styleAfter = self.GetStyleAt(caretPos)

            if charAfter and chr(charAfter) in "[]{}()" and styleAfter == stc.STC_P_OPERATOR:
                braceAtCaret = caretPos

        if braceAtCaret >= 0:
            braceOpposite = self.BraceMatch(braceAtCaret)

        if braceAtCaret != -1  and braceOpposite == -1:
            self.BraceBadLight(braceAtCaret)
        else:
            self.BraceHighlight(braceAtCaret, braceOpposite)

    def OnMarginClick(self, evt):
        # fold and unfold as needed
        if evt.GetMargin() == 2:
            if evt.GetShift() and evt.GetControl():
                self.FoldAll()
            else:
                lineClicked = self.LineFromPosition(evt.GetPosition())

                if self.GetFoldLevel(lineClicked) & stc.STC_FOLDLEVELHEADERFLAG:
                    if evt.GetShift():
                        self.SetFoldExpanded(lineClicked, True)
                        self.Expand(lineClicked, True, True, 1)
                    elif evt.GetControl():
                        if self.GetFoldExpanded(lineClicked):
                            self.SetFoldExpanded(lineClicked, False)
                            self.Expand(lineClicked, False, True, 0)
                        else:
                            self.SetFoldExpanded(lineClicked, True)
                            self.Expand(lineClicked, True, True, 100)
                    else:
                        self.ToggleFold(lineClicked)


    def FoldAll(self):
        lineCount = self.GetLineCount()
        expanding = True

        # find out if we are folding or unfolding
        for lineNum in range(lineCount):
            if self.GetFoldLevel(lineNum) & stc.STC_FOLDLEVELHEADERFLAG:
                expanding = not self.GetFoldExpanded(lineNum)
                break

        lineNum = 0

        while lineNum < lineCount:
            level = self.GetFoldLevel(lineNum)
            if level & stc.STC_FOLDLEVELHEADERFLAG and \
               (level & stc.STC_FOLDLEVELNUMBERMASK) == stc.STC_FOLDLEVELBASE:

                if expanding:
                    self.SetFoldExpanded(lineNum, True)
                    lineNum = self.Expand(lineNum, True)
                    lineNum = lineNum - 1
                else:
                    lastChild = self.GetLastChild(lineNum, -1)
                    self.SetFoldExpanded(lineNum, False)

                    if lastChild > lineNum:
                        self.HideLines(lineNum+1, lastChild)

            lineNum = lineNum + 1



    def Expand(self, line, doExpand, force=False, visLevels=0, level=-1):
        lastChild = self.GetLastChild(line, level)
        line = line + 1

        while line <= lastChild:
            if force:
                if visLevels > 0:
                    self.ShowLines(line, line)
                else:
                    self.HideLines(line, line)
            else:
                if doExpand:
                    self.ShowLines(line, line)

            if level == -1:
                level = self.GetFoldLevel(line)

            if level & stc.STC_FOLDLEVELHEADERFLAG:
                if force:
                    if visLevels > 1:
                        self.SetFoldExpanded(line, True)
                    else:
                        self.SetFoldExpanded(line, False)

                    line = self.Expand(line, doExpand, force, visLevels-1)

                else:
                    if doExpand and self.GetFoldExpanded(line):
                        line = self.Expand(line, True, force, visLevels-1)
                    else:
                        line = self.Expand(line, False, force, visLevels-1)
            else:
                line = line + 1

        return line

###-----------------------------------------------------------------------------
class CodeEditor(PythonSTC):
	def __init__(self, parent):
		PythonSTC.__init__(self, parent, -1, style=wx.BORDER_NONE)
		self.SetUpEditor()

	# Some methods to make it compatible with how the wxTextCtrl is used
	def SetValue(self, value):
		if wx.USE_UNICODE:
			value = value.decode('iso8859_1')
		self.SetText(value)
		self.EmptyUndoBuffer()
		self.SetSavePoint()

	def GetValue(self):
		return self.GetText()

	def IsModified(self):
		return self.GetModify()

	def Clear(self):
		self.ClearAll()

	def SetInsertionPoint(self, pos):
		self.SetCurrentPos(pos)
		self.SetAnchor(pos)

	def ShowPosition(self, pos):
		line = self.LineFromPosition(pos)
		#self.EnsureVisible(line)
		self.GotoLine(line)

	def GetLastPosition(self):
		return self.GetLength()

	def GetPositionFromLine(self, line):
		return self.PositionFromLine(line)

	def GetRange(self, start, end):
		return self.GetTextRange(start, end)

	def GetSelection(self):
		return self.GetAnchor(), self.GetCurrentPos()

	def SetSelection(self, start, end):
		self.SetSelectionStart(start)
		self.SetSelectionEnd(end)

	def SelectLine(self, line):
		start = self.PositionFromLine(line)
		end = self.GetLineEndPosition(line)
		self.SetSelection(start, end)
		
	def SetUpEditor(self):
		"""
		This method carries out the work of setting up the demo editor.            
		It's seperate so as not to clutter up the init code.
		"""
		import keyword
		
		self.SetLexer(stc.STC_LEX_PYTHON)
		self.SetKeyWords(0, " ".join(keyword.kwlist))

		# Enable folding
		self.SetProperty("fold", "1" ) 

		# Highlight tab/space mixing (shouldn't be any)
		self.SetProperty("tab.timmy.whinge.level", "1")

		# Set left and right margins
		self.SetMargins(2,2)

		# Set up the numbers in the margin for margin #1
		self.SetMarginType(1, wx.stc.STC_MARGIN_NUMBER)
		# Reasonable value for, say, 4-5 digits using a mono font (40 pix)
		self.SetMarginWidth(1, 40)

		# Indentation and tab stuff
		self.SetIndent(4)               # Proscribed indent size for wx
		self.SetIndentationGuides(True) # Show indent guides
		self.SetBackSpaceUnIndents(True)# Backspace unindents rather than delete 1 space
		self.SetTabIndents(True)        # Tab key indents
		self.SetTabWidth(4)             # Proscribed tab size for wx
		self.SetUseTabs(True)          # Use spaces rather than tabs, or
						# TabTimmy will complain!    
		# White space
		self.SetViewWhiteSpace(False)   # Don't view white space

		# EOL: Since we are loading/saving ourselves, and the
		# strings will always have \n's in them, set the STC to
		# edit them that way.            
		self.SetEOLMode(wx.stc.STC_EOL_LF)
		self.SetViewEOL(False)
		
		# No right-edge mode indicator
		self.SetEdgeMode(stc.STC_EDGE_NONE)

		# Setup a margin to hold fold markers
		self.SetMarginType(2, stc.STC_MARGIN_SYMBOL)
		self.SetMarginMask(2, stc.STC_MASK_FOLDERS)
		self.SetMarginSensitive(2, True)
		self.SetMarginWidth(2, 12)

		# and now set up the fold markers
		self.MarkerDefine(stc.STC_MARKNUM_FOLDEREND,     stc.STC_MARK_BOXPLUSCONNECTED,  "white", "black")
		self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPENMID, stc.STC_MARK_BOXMINUSCONNECTED, "white", "black")
		self.MarkerDefine(stc.STC_MARKNUM_FOLDERMIDTAIL, stc.STC_MARK_TCORNER,  "white", "black")
		self.MarkerDefine(stc.STC_MARKNUM_FOLDERTAIL,    stc.STC_MARK_LCORNER,  "white", "black")
		self.MarkerDefine(stc.STC_MARKNUM_FOLDERSUB,     stc.STC_MARK_VLINE,    "white", "black")
		self.MarkerDefine(stc.STC_MARKNUM_FOLDER,        stc.STC_MARK_BOXPLUS,  "white", "black")
		self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPEN,    stc.STC_MARK_BOXMINUS, "white", "black")

		# Global default style
		if wx.Platform == '__WXMSW__':
			self.StyleSetSpec(stc.STC_STYLE_DEFAULT, 'fore:#000000,back:#FFFFFF,face:Courier New,size:9')
		elif wx.Platform == '__WXMAC__':
		# TODO: if this looks fine on Linux too, remove the Mac-specific case 
		# and use this whenever OS != MSW.
			self.StyleSetSpec(stc.STC_STYLE_DEFAULT, 'fore:#000000,back:#FFFFFF,face:Monaco')
		else:
			self.StyleSetSpec(stc.STC_STYLE_DEFAULT, 'fore:#000000,back:#FFFFFF,face:Courier,size:9')

		# Clear styles and revert to default.
		self.StyleClearAll()

		# Following style specs only indicate differences from default.
		# The rest remains unchanged.

		# Line numbers in margin
		self.StyleSetSpec(wx.stc.STC_STYLE_LINENUMBER,'fore:#000000,back:#99A9C2')    
		# Highlighted brace
		self.StyleSetSpec(wx.stc.STC_STYLE_BRACELIGHT,'fore:#00009D,back:#FFFF00')
		# Unmatched brace
		self.StyleSetSpec(wx.stc.STC_STYLE_BRACEBAD,'fore:#00009D,back:#FF0000')
		# Indentation guide
		self.StyleSetSpec(wx.stc.STC_STYLE_INDENTGUIDE, "fore:#CDCDCD")

		# Python styles
		self.StyleSetSpec(wx.stc.STC_P_DEFAULT, 'fore:#000000')
		# Comments
		self.StyleSetSpec(wx.stc.STC_P_COMMENTLINE,  'fore:#008000,back:#F0FFF0')
		self.StyleSetSpec(wx.stc.STC_P_COMMENTBLOCK, 'fore:#008000,back:#F0FFF0')
		# Numbers
		self.StyleSetSpec(wx.stc.STC_P_NUMBER, 'fore:#008080')
		# Strings and characters
		self.StyleSetSpec(wx.stc.STC_P_STRING, 'fore:#800080')
		self.StyleSetSpec(wx.stc.STC_P_CHARACTER, 'fore:#800080')
		# Keywords
		self.StyleSetSpec(wx.stc.STC_P_WORD, 'fore:#000080,bold')
		# Triple quotes
		self.StyleSetSpec(wx.stc.STC_P_TRIPLE, 'fore:#800080,back:#FFFFEA')
		self.StyleSetSpec(wx.stc.STC_P_TRIPLEDOUBLE, 'fore:#800080,back:#FFFFEA')
		# Class names
		self.StyleSetSpec(wx.stc.STC_P_CLASSNAME, 'fore:#0000FF,bold')
		# Function names
		self.StyleSetSpec(wx.stc.STC_P_DEFNAME, 'fore:#008080,bold')
		# Operators
		self.StyleSetSpec(wx.stc.STC_P_OPERATOR, 'fore:#800000,bold')
		# Identifiers. I leave this as not bold because everything seems
		# to be an identifier if it doesn't match the above criterae
		self.StyleSetSpec(wx.stc.STC_P_IDENTIFIER, 'fore:#000000')

		# Caret color
		self.SetCaretForeground("BLUE")
		# Selection background
		self.SetSelBackground(1, '#66CCFF')

		self.SetSelBackground(True, wx.SystemSettings_GetColour(wx.SYS_COLOUR_HIGHLIGHT))
		self.SetSelForeground(True, wx.SystemSettings_GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT))

	def RegisterModifiedEvent(self, eventHandler):
		self.Bind(wx.stc.EVT_STC_CHANGE, eventHandler)

###---------------------------------------------------------
class Editor(wx.Frame, wx.Panel):
	def __init__(self, parent, id, title, codeBlock):
		
		if isinstance(parent,wx.BoxSizer):
			wx.Panel.__init__(self, parent, ID)
			self.SetBackgroundColour(wx.WHITE)
		else:
			wx.Frame.__init__(self, parent, id, title, size=(600, 500))
			self.SetIcon(self.MakeIcon(wx.Image(os.path.join(ICON_PATH_20_20,'pythonFile.png'), wx.BITMAP_TYPE_PNG)))

		#local copy
		self.cb = codeBlock

		# variables
		self.modify = False
		self.last_name_saved = ''
		self.replace = False
		
		# setting up menubar
		menubar = wx.MenuBar()
		
		file = wx.Menu()
				
		save = wx.MenuItem(file, wx.NewId(), _('&Save\tCtrl+S'), _('Save the file'))
		quit = wx.MenuItem(file, wx.NewId(), _('&Quit\tCtrl+Q'), _('Quit the application'))

		save.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'save.png')))
		quit.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'exit.png')))

		file.AppendItem(save)
		file.AppendItem(quit)
		
		edit = wx.Menu()
		cut = wx.MenuItem(edit, wx.NewId(), _('&Cut\tCtrl+X'), _('Cut the selection'))
		copy = wx.MenuItem(edit, wx.NewId(), _('&Copy\tCtrl+C'), _('Copy the selection'))
		paste = wx.MenuItem(edit, wx.NewId(), _('&Paste\tCtrl+V'), _('Paste text from clipboard'))
		delete = wx.MenuItem(edit, wx.NewId(), _('&Delete'), _('Delete the selected text'))
		select = wx.MenuItem(edit, wx.NewId(), _('Select &All\tCtrl+A'), _('Select the entire text'))

		cut.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'cut.png')))
		copy.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'copy.png')))
		paste.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'paste.png')))
		delete.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'delete.png')))

		edit.AppendItem(cut)
		edit.AppendItem(copy)
		edit.AppendItem(paste)		
		edit.AppendItem(delete)
		edit.AppendSeparator()
		edit.AppendItem(select)
		
		view = wx.Menu()
		showStatusBar = wx.MenuItem(view, wx.NewId(), _('&Statusbar'), _('Show statusBar'))
		view.AppendItem(showStatusBar)
		
		help = wx.Menu()
		about = wx.MenuItem(help, wx.NewId(), _('&About\tF1'), _('About editor'))
		about.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'info.png')))
		help.AppendItem(about)
		
		menubar.Append(file, _('&File'))
		menubar.Append(edit, _('&Edit'))
		menubar.Append(view, _('&View'))
		menubar.Append(help, _('&Help'))
		self.SetMenuBar(menubar)
		
		self.Bind(wx.EVT_MENU, self.OnSaveFile, id=save.GetId())
		self.Bind(wx.EVT_MENU, self.QuitApplication, id=quit.GetId())
		self.Bind(wx.EVT_MENU, self.OnCut, id=cut.GetId())
		self.Bind(wx.EVT_MENU, self.OnCopy, id=copy.GetId())
		self.Bind(wx.EVT_MENU, self.OnPaste, id=paste.GetId())
		self.Bind(wx.EVT_MENU, self.OnDelete, id=delete.GetId())
		self.Bind(wx.EVT_MENU, self.OnSelectAll, id=select.GetId())
		self.Bind(wx.EVT_MENU, self.ToggleStatusBar, id=showStatusBar.GetId())
		self.Bind(wx.EVT_MENU, self.OnAbout, id=about.GetId())
		
		self.toolbar = self.CreateToolBar( wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT | wx.TB_TEXT )
				
		self.Bind(wx.EVT_TOOL, self.OnSaveFile, self.toolbar.AddSimpleTool(wx.NewId(), wx.Bitmap(os.path.join(ICON_PATH,'save.png')), 'Save', ''))
		self.toolbar.AddSeparator()
		self.Bind(wx.EVT_TOOL, self.OnCut, self.toolbar.AddSimpleTool(wx.NewId(), wx.Bitmap(os.path.join(ICON_PATH,'cut.png')), 'Cut', ''))
		self.Bind(wx.EVT_TOOL, self.OnCopy, self.toolbar.AddSimpleTool(wx.NewId(), wx.Bitmap(os.path.join(ICON_PATH,'copy.png')), 'Copy', ''))
		self.Bind(wx.EVT_TOOL, self.OnPaste, self.toolbar.AddSimpleTool(wx.NewId(), wx.Bitmap(os.path.join(ICON_PATH,'paste.png')), 'Paste', ''))
		self.Bind(wx.EVT_TOOL, self.QuitApplication, id=quit.GetId())
	
		self.toolbar.Realize()

		self.text = CodeEditor(self)
		self.text.SetFocus()
		self.text.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
		self.text.Bind(wx.EVT_TEXT, self.OnTextChanged, id=self.text.GetId())
		self.Bind(wx.EVT_CLOSE, self.QuitApplication)
		
		self.StatusBar()
		self.Centre()

	def MakeIcon(self, img):
		"""
		The various platforms have different requirements for the
		icon size...
		"""
		if "wxMSW" in wx.PlatformInfo:
			img = img.Scale(16, 16)
		elif "wxGTK" in wx.PlatformInfo:
			img = img.Scale(22, 22)
		
		# wxMac can be any size upto 128x128, so leave the source img alone....
		icon = wx.IconFromBitmap(img.ConvertToBitmap() )
		return icon

	def NewApplication(self, event):
		editor = Editor(None, wx.ID_ANY, _('Editor'))
		editor.Centre()
		editor.Show()

	def OnOpenFile(self, event):
		file_name = os.path.basename(self.last_name_saved)
		if self.modify:
			dlg = wx.MessageDialog(self, _('Save changes?'), '', wx.YES_NO | wx.YES_DEFAULT | wx.CANCEL |wx.ICON_QUESTION)
			val = dlg.ShowModal()
			if val == wx.ID_YES:
				self.OnSaveFile(event)
				self.DoOpenFile()
			elif val == wx.ID_CANCEL:
				dlg.Destroy()
			else:
				self.DoOpenFile()
		else:
			self.DoOpenFile()
	
	def DoOpenFile(self):
		wcd = 'All files (*)|*|Editor files (*.py)|*.py'
		dir = HOME_PATH
		open_dlg = wx.FileDialog(self, message=_('Choose a file'), defaultDir=dir, defaultFile='', wildcard=wcd, style=wx.OPEN|wx.CHANGE_DIR)
		if open_dlg.ShowModal() == wx.ID_OK:
			path = open_dlg.GetPath()
	
			try:
				file = open(path, 'r')
				text = file.read()
				file.close()
				if self.text.GetLastPosition():
					self.text.Clear()
				self.text.WriteText(text)
				self.last_name_saved = path
				self.statusbar.SetStatusText('', 1)
				self.modify = False
	
			except Exception, info:
				dlg = wx.MessageDialog(self, _('Error opening file\n') + str(info))
				dlg.ShowModal()
	
		open_dlg.Destroy()

	###
	def Update(self):
		""" Reloading associated module and devs model
		"""
		
		## recuperation du module correspondant à la classe
		moduleName = Container.PathToModule(self.cb.python_path)

		### re importation du module de la classe avec verification des erreurs éventuelles dans le code
		recompile(moduleName)
		
		### le reload necessite une reimportation
		try:
			exec "import %s"%(str(moduleName))
		except Exception, info:
			sys.stderr.write(_("Import Error in GetDEVSModel: %s\n"%info))
			return False

		# classes composing the imported module
		clsmembers = dict(inspect.getmembers(sys.modules[str(moduleName)], inspect.isclass))
	
		for c in clsmembers.values(): 
			if str(c.__module__) == str(moduleName):
				classe = c
				break

		# get behavioral attribute from python file through constructor class
		constructor = inspect.getargspec(classe.__init__)
		if constructor.defaults != None:
			for k,v in zip(constructor.args[1:], constructor.defaults):
				if not self.cb.args.has_key(k):
					self.cb.args.update({k:v})

		# code update if it was modified during the simulation
		devs = self.cb.getDEVSModel()
		if devs != None:
			devs.__class__ = classe

	###
	def OnSaveFile(self, event):
		if self.last_name_saved:
			try:
				##--------------- open and write ---------- #
				file = open(self.last_name_saved, 'w')
				text = self.text.GetValue()
				file.write(text.encode('utf8'))
				file.close()
				self.statusbar.SetStatusText(os.path.basename(self.last_name_saved) + _(' saved'), 0)
				self.modify = False
				self.statusbar.SetStatusText('', 1)
			
				### -------------- relaod module and get new atomicDEVS --------- #
				self.Update()
				
			except Exception, info:
				dlg = wx.MessageDialog(self, _('Error saving file\n') + str(info))
				dlg.ShowModal()

			dial = wx.MessageDialog(self, _('Saving completed successfully'), 'Info', wx.OK)
			dial.ShowModal()

		else:
			self.OnSaveAsFile(event)

	def OnSaveAsFile(self, event):
		wcd='All files(*)|*|Editor files (*.py)|*.py'
		dir = HOME_PATH
		save_dlg = wx.FileDialog(self, message=_('Save file as...'), defaultDir=dir, defaultFile='', wildcard=wcd, style=wx.SAVE | wx.OVERWRITE_PROMPT)
		if save_dlg.ShowModal() == wx.ID_OK:
			path = save_dlg.GetPath()
			try:
				file = open(path, 'w')
				text = self.text.GetValue()
				file.write(text.encode('utf8'))
				file.close()
				self.last_name_saved = os.path.basename(path)
				self.statusbar.SetStatusText(self.last_name_saved + _(' saved'), 0)
				self.modify = False
				self.statusbar.SetStatusText('', 1)
	
				### relaod module and get new atomicDEVS
				self.Update()

			except Exception, info:
				dlg = wx.MessageDialog(self, _('Error saving file\n') + str(info))
				dlg.ShowModal()
			
			dial = wx.MessageDialog(self, _('Save completed'), 'Info', wx.OK)
			dial.ShowModal()

		save_dlg.Destroy()
	
	def OnCut(self, event):
		self.text.Cut()
	
	def OnCopy(self, event):
		self.text.Copy()
	
	def OnPaste(self, event):
		self.text.Paste()
	
	def QuitApplication(self, event):
		if self.modify:
			dlg = wx.MessageDialog(self, _('Save before Exit?'), '', wx.YES_NO | wx.YES_DEFAULT | wx.CANCEL | wx.ICON_QUESTION)
			val = dlg.ShowModal()
			if val == wx.ID_YES:
				self.OnSaveFile(event)
				if not self.modify:
					wx.Exit()
			elif val == wx.ID_CANCEL:
				dlg.Destroy()
			else:
				self.Destroy()
		else:
			self.Destroy()
	
	def OnDelete(self, event):
		frm, to = self.text.GetSelection()
		self.text.Remove(frm, to)
	
	def OnSelectAll(self, event):
		self.text.SelectAll()
	
	def OnTextChanged(self, event):
		self.modify = True
		self.statusbar.SetStatusText(_(' modified'), 1)
		event.Skip()
	
	def OnKeyDown(self, event):
		keycode = event.GetKeyCode()
		if keycode == wx.WXK_INSERT:
			if not self.replace:
				self.statusbar.SetStatusText(_(' insert'), 2)
				self.replace = True
			else:
				self.statusbar.SetStatusText('', 2)
				self.replace = False
		event.Skip()
	
	def ToggleStatusBar(self, event):
		if self.statusbar.IsShown():
			self.statusbar.Hide()
		else:
			self.statusbar.Show()
	
	def StatusBar(self):
		self.statusbar = self.CreateStatusBar()
		self.statusbar.SetFieldsCount(3)
		self.statusbar.SetStatusWidths([-5, -2, -1])
	
	def OnAbout(self, event):
		dlg = wx.MessageDialog(self, _('\tPython Code Editor\t\n \tDEVSimPy\t\n\tdec  2008-2009'), _('About Editor'), wx.OK | wx.ICON_INFORMATION)
		dlg.ShowModal()
		dlg.Destroy()