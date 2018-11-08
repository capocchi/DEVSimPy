# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# Editor.py ---
#                     --------------------------------
#                          Copyright (c) 2013
#                           T. ville
#                           Laurent CAPOCCHI
#                         University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 28/02/2014
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

from __future__ import with_statement

import wx
import os
import sys
import keyword
import inspect
import zipfile
import imp
import threading
import re
import codecs
import tabnanny
import __builtin__
import traceback

from traceback import format_exception, extract_tb
from tempfile import gettempdir
from wx import stc

from Decorators import redirectStdout
from Utilities import path_to_module, PrintException

import ReloadModule
import ZipManager

_ = wx.GetTranslation

# Turn on verbose mode
tabnanny.verbose = 1

if wx.Platform == '__WXMSW__':
	faces = dict(times='Times New Roman', mono='Courier New', helv='Arial', other='Comic Sans MS', size=10, size2=8)
elif wx.Platform == '__WXMAC__':
	faces = dict(times='Times New Roman', mono='Monaco', helv='Arial', other='Comic Sans MS', size=12, size2=10)
else:
	faces = dict(times='Times', mono='Courier', helv='Helvetica', other='new century schoolbook', size=12, size2=10)

wx.SystemSettings_GetColour = wx.SystemSettings.GetColour if wx.VERSION_STRING >= '4.0' else wx.SystemSettings_GetColour


#################################################################
###
###		GENERAL FUNCTIONS
###
#################################################################


### NOTE: Editor.py :: isError 				=> check if file is well-formed and if requirements are corrects
def isError(scriptlet):
	"""
	"""
	try:
		code = compile(scriptlet, '<string>', 'exec')
		exec code
	except Exception, info:
		return info
	else:
		return False

### NOTE: Editor.py :: getObjectFromString	=> todo
def getObjectFromString(scriptlet):
	"""
	"""

	assert scriptlet != ''

	# Compile the scriptlet.
	try:
		code = compile(scriptlet, '<string>', 'exec')
	except Exception, info:
		### Add line number to the error trace
		for frame in traceback.extract_tb(sys.exc_info()[2]):
			fname,lineno,fn,text = frame
		L = list(info.args)
		L.append("line %i"%lineno)
		info.args = tuple(L)
		return info

	else:
		# Create the new 'temp' module.
		temp = imp.new_module("temp")
		sys.modules["temp"] = temp

		### there is syntaxe error ?
		try:
			exec code in temp.__dict__

		except Exception, info:
			### Add line number to the error trace
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				fname,lineno,fn,text = frame
			L = list(info.args)
			L.append("line %i"%lineno)
			info.args = tuple(L)

			return info

		else:
			classes = inspect.getmembers(temp, callable)
			for name, value in classes:
				if value.__module__ == "temp":
					# Create the instance.
					try:
						return eval("temp.%s" % name)()

					except Exception, info:
						### Add line number to the error trace
						for frame in traceback.extract_tb(sys.exc_info()[2]):
							fname,lineno,fn,text = frame
						L = list(info.args)
						L.append("line %i"%lineno)
						info.args = tuple(L)

						return info


### NOTE: Editor.py :: GetEditor 			=> Return the appropriate Editor
def GetEditor(parent, id, title="", obj=None, **kwargs):
	""" Factory Editor
	@param: parent
	@param: id
	@param: title
	@param: obj
	@param: file_type
	"""

	if "file_type" in kwargs.keys():
		file_type = kwargs["file_type"]

		if file_type == "test":
			editor = TestEditor(parent, id, title)
		elif file_type == "block":
			editor = BlockEditor(parent, id, title, obj)
		else:
			editor = GeneralEditor(parent, id, title)
	else:
		editor = GeneralEditor(parent, id, title)

	return editor

#################################################################
###
###		GENERAL CLASSES
###
#################################################################

### NOTE: PythonSTC << stc.StyledTextCtrl :: todo
class PythonSTC(stc.StyledTextCtrl):
	"""
	"""

	fold_symbols = 2

	### NOTE: PythonSTC:: constructor => __init__(self, parent, ID, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0)
	def __init__(self, parent, ID, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
		"""
		"""
		stc.StyledTextCtrl.__init__(self, parent, ID, pos, size, style)

		self.CmdKeyAssign(ord('B'), stc.STC_SCMOD_CTRL, stc.STC_CMD_ZOOMIN)
		self.CmdKeyAssign(ord('N'), stc.STC_SCMOD_CTRL, stc.STC_CMD_ZOOMOUT)

		self.SetLexer(stc.STC_LEX_PYTHON)
		self.SetKeyWords(0, " ".join(keyword.kwlist))

		self.SetProperty("fold", "1")
		self.SetProperty("tab.timmy.whinge.level", "1")
		self.SetMargins(0, 0)

		self.SetViewWhiteSpace(False)
		self.SetBufferedDraw(False)
		self.SetViewEOL(True)
		self.SetEOLMode(stc.STC_EOL_CRLF)
		
		if wx.VERSION_STRING < '4.0': self.SetUseAntiAliasing(True)

		self.SetEdgeMode(stc.STC_EDGE_BACKGROUND)
		self.SetEdgeColumn(78)

		# Setup a margin to hold fold markers
		self.SetMarginType(2, stc.STC_MARGIN_SYMBOL)
		self.SetMarginMask(2, stc.STC_MASK_FOLDERS)
		self.SetMarginSensitive(2, True)
		self.SetMarginWidth(2, 12)

		if self.fold_symbols == 0:
			# Arrow pointing right for contracted folders, arrow pointing down for expanded
			self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPEN, stc.STC_MARK_ARROWDOWN, "black", "black")
			self.MarkerDefine(stc.STC_MARKNUM_FOLDER, stc.STC_MARK_ARROW, "black", "black")
			self.MarkerDefine(stc.STC_MARKNUM_FOLDERSUB, stc.STC_MARK_EMPTY, "black", "black")
			self.MarkerDefine(stc.STC_MARKNUM_FOLDERTAIL, stc.STC_MARK_EMPTY, "black", "black")
			self.MarkerDefine(stc.STC_MARKNUM_FOLDEREND, stc.STC_MARK_EMPTY, "white", "black")
			self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPENMID, stc.STC_MARK_EMPTY, "white", "black")
			self.MarkerDefine(stc.STC_MARKNUM_FOLDERMIDTAIL, stc.STC_MARK_EMPTY, "white", "black")

		elif self.fold_symbols == 1:
			# Plus for contracted folders, minus for expanded
			self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPEN, stc.STC_MARK_MINUS, "white", "black")
			self.MarkerDefine(stc.STC_MARKNUM_FOLDER, stc.STC_MARK_PLUS, "white", "black")
			self.MarkerDefine(stc.STC_MARKNUM_FOLDERSUB, stc.STC_MARK_EMPTY, "white", "black")
			self.MarkerDefine(stc.STC_MARKNUM_FOLDERTAIL, stc.STC_MARK_EMPTY, "white", "black")
			self.MarkerDefine(stc.STC_MARKNUM_FOLDEREND, stc.STC_MARK_EMPTY, "white", "black")
			self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPENMID, stc.STC_MARK_EMPTY, "white", "black")
			self.MarkerDefine(stc.STC_MARKNUM_FOLDERMIDTAIL, stc.STC_MARK_EMPTY, "white", "black")

		elif self.fold_symbols == 2:
			# Like a flattened tree control using circular headers and curved joins
			self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPEN, stc.STC_MARK_CIRCLEMINUS, "white", "#404040")
			self.MarkerDefine(stc.STC_MARKNUM_FOLDER, stc.STC_MARK_CIRCLEPLUS, "white", "#404040")
			self.MarkerDefine(stc.STC_MARKNUM_FOLDERSUB, stc.STC_MARK_VLINE, "white", "#404040")
			self.MarkerDefine(stc.STC_MARKNUM_FOLDERTAIL, stc.STC_MARK_LCORNERCURVE, "white", "#404040")
			self.MarkerDefine(stc.STC_MARKNUM_FOLDEREND, stc.STC_MARK_CIRCLEPLUSCONNECTED, "white", "#404040")
			self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPENMID, stc.STC_MARK_CIRCLEMINUSCONNECTED, "white", "#404040")
			self.MarkerDefine(stc.STC_MARKNUM_FOLDERMIDTAIL, stc.STC_MARK_TCORNERCURVE, "white", "#404040")

		elif self.fold_symbols == 3:
			# Like a flattened tree control using square headers
			self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPEN, stc.STC_MARK_BOXMINUS, "white", "#808080")
			self.MarkerDefine(stc.STC_MARKNUM_FOLDER, stc.STC_MARK_BOXPLUS, "white", "#808080")
			self.MarkerDefine(stc.STC_MARKNUM_FOLDERSUB, stc.STC_MARK_VLINE, "white", "#808080")
			self.MarkerDefine(stc.STC_MARKNUM_FOLDERTAIL, stc.STC_MARK_LCORNER, "white", "#808080")
			self.MarkerDefine(stc.STC_MARKNUM_FOLDEREND, stc.STC_MARK_BOXPLUSCONNECTED, "white", "#808080")
			self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPENMID, stc.STC_MARK_BOXMINUSCONNECTED, "white", "#808080")
			self.MarkerDefine(stc.STC_MARKNUM_FOLDERMIDTAIL, stc.STC_MARK_TCORNER, "white", "#808080")

		self.Bind(stc.EVT_STC_UPDATEUI, self.OnUpdateUI)
		self.Bind(stc.EVT_STC_MARGINCLICK, self.OnMarginClick)

		# Make some styles,  The lexer defines what each style is used for, we
		# just have to define what each style looks like.  This set is adapted from
		# Scintilla sample property files.

		# Global default styles for all languages
		self.StyleSetSpec(stc.STC_STYLE_DEFAULT, "face:%(helv)s,size:%(size)d" % faces)
		#self.StyleSetSpec(STC_CODE_ERROR, 'fore:#FF0000,back:#FFFF00,size:%(size)d' % faces)
		#self.StyleSetSpec(STC_CODE_SEARCH_RESULT, 'fore:#FFFFFF,back:#FFA500,size:%(size)d' % faces)

		self.StyleClearAll()  # Reset all to be like the default

		# Global default styles for all languages
		self.StyleSetSpec(stc.STC_STYLE_DEFAULT, "face:%(helv)s,size:%(size)d" % faces)
		self.StyleSetSpec(stc.STC_STYLE_LINENUMBER, "back:#C0C0C0,face:%(helv)s,size:%(size2)d" % faces)
		self.StyleSetSpec(stc.STC_STYLE_CONTROLCHAR, "face:%(other)s" % faces)
		self.StyleSetSpec(stc.STC_STYLE_BRACELIGHT, "fore:#FFFFFF,back:#0000FF,bold")
		self.StyleSetSpec(stc.STC_STYLE_BRACEBAD, "fore:#000000,back:#FF0000,bold")

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

	# NOTE: PythonSTC :: __str__		=> String representation of the class
	@classmethod
	def __str__(cls):
		attrs = [('fold_symbols', 'integer')]
		class_name = "PythonSTC"
		parent = "stc.StyledTextCtrl"
		methods = [
			('__init__', 'self, parent, ID, pos, size, style'),
			('FoldAll', 'self'),
			('Expand', 'self, line, doExpand, force, visLevels, level'),
			('OnUpdateUI', 'self, event'),
			('OnMarginClick', 'self, event')
		]
		return "\n--------------------------------------------------\
		\n\tClass :\t\t%s\n\n\tInherit from :\t%s\n\n\tAttributes :\t%s\n\n\tMethods :\t%s\n" % (
			class_name, parent, '\n\t\t\t'.join([attr + "\t:: " + typ for attr, typ in attrs]),
			"\n\t\t\t".join([method + "\tparams :: " + params for method, params in methods])
		)

	### NOTE: PythonSTC :: OnUpdateUI 			=> Event for update user interface
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

		if braceAtCaret != -1 and braceOpposite == -1:
			self.BraceBadLight(braceAtCaret)
		else:
			self.BraceHighlight(braceAtCaret, braceOpposite)

	### NOTE: PythonSTC :: OnMarginClick 		=> Event for click on margin
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

	### NOTE: PythonSTC :: FoldAll 			=> Fold entire code
	def FoldAll(self):
		lineCount = self.GetLineCount()
		expanding = True

		# find out if we are folding or unfolding
		for lineNum in xrange(lineCount):
			if self.GetFoldLevel(lineNum) & stc.STC_FOLDLEVELHEADERFLAG:
				expanding = not self.GetFoldExpanded(lineNum)
				break

		lineNum = 0

		while lineNum < lineCount:
			level = self.GetFoldLevel(lineNum)
			if level & stc.STC_FOLDLEVELHEADERFLAG and (level & stc.STC_FOLDLEVELNUMBERMASK) == stc.STC_FOLDLEVELBASE:

				if expanding:
					self.SetFoldExpanded(lineNum, True)
					lineNum = self.Expand(lineNum, True)
					lineNum -= 1
				else:
					lastChild = self.GetLastChild(lineNum, -1)
					self.SetFoldExpanded(lineNum, False)

					if lastChild > lineNum:
						self.HideLines(lineNum + 1, lastChild)

			lineNum += 1

	def Paste(self):
#		success = False
		#do = wx.TextDataObject()
#		if wx.TheClipboard.Open():
#		    success = wx.TheClipboard.GetData(do)
#		    wx.TheClipboard.Close()

#		if success:
#		    if not self.execplugin('on_paste', self, do.GetText()):
#		        wx.stc.StyledTextCtrl.Paste(self)
		wx.stc.StyledTextCtrl.Paste(self)

	def Copy(self):
		wx.stc.StyledTextCtrl.Copy(self)

	### NOTE: PythonSTC :: Expand 				=> Expand selected line
	def Expand(self, line, doExpand, force=False, visLevels=0, level=-1):
		lastChild = self.GetLastChild(line, level)
		line += 1

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

					line = self.Expand(line, doExpand, force, visLevels - 1)

				else:
					if doExpand and self.GetFoldExpanded(line):
						line = self.Expand(line, True, force, visLevels - 1)
					else:
						line = self.Expand(line, False, force, visLevels - 1)
			else:
				line += 1

		return line


###-----------------------------------------------------------------------------
### NOTE: CodeEditor << PythonSTC :: todo
class CodeEditor(PythonSTC):
	#### NOTE: CodeEditor :: constructor 		=> __init__(self, parent)
	def __init__(self, parent):
		""" Constructor
		"""
		PythonSTC.__init__(self, parent, wx.ID_ANY, style=wx.BORDER_NONE)
		self.SetUpEditor()
		self.last_name_saved = ""

	# NOTE: CodeEditor :: __str__		=> String representation of the class
	@classmethod
	def __str__(cls):
		attrs = [('last_name_saved', 'str')]
		class_name = "CodeEditor"
		parent = "PythonSTC"
		methods = [
			('__init__', 'self, parent'),
			('GetFilename', 'self'),
			('SetFilename', 'self, filename'),
			('GetValue', 'self'),
			('SetValue', 'self, value'),
			('IsModified', 'self'),
			('Clear', 'self'),
			('SetInsertionPoint', 'self, pos'),
			('ShowPosition', 'self, pos'),
			('GetLastPosition', 'self'),
			('GetPositionFromLine', 'self, line'),
			('GetRange', 'self, start, end'),
			('GetSelection', 'self'),
			('SetSelection', 'self, start, end'),
			('SelectLine', 'self, line'),
			('SetUpEditor', 'self'),
			('RegisterModifiedEvent', 'self, eventHandler')
		]
		return "\n--------------------------------------------------\
		\n\tClass :\t\t%s\n\n\tInherit from :\t%s\n\n\tAttributes :\t%s\n\n\tMethods :\t%s\n" % (
			class_name, parent, '\n\t\t\t'.join([attr + "\t:: " + typ for attr, typ in attrs]),
			"\n\t\t\t".join([method + "\tparams :: " + params for method, params in methods])
		)

	### NOTE: CodeEditor :: GetFilename 		=> Get the last name saved
	def GetFilename(self):
		return self.last_name_saved

	### NOTE: CodeEditor :: SetFilename 		=> Set the last name saved
	def SetFilename(self, filename):
		self.last_name_saved = filename

	### NOTE: CodeEditor :: SetValue 			=> Set the text to print in the editor
	### Some methods to make it compatible with how the wxTextCtrl is used
	def SetValue(self, value):

		#if wx.USE_UNICODE:
			#value = value.decode('utf-8')
		#else:
			#value = value.decode('iso8859_1')

		self.SetText(value)
		self.EmptyUndoBuffer()
		self.SetSavePoint()

	### NOTE: CodeEditor :: GetValue 			=> Get the text printed in the editor
	def GetValue(self):
		return self.GetText()

	### NOTE: CodeEditor :: IsModified 		=> Flag to determine if the text is modified or not
	def IsModified(self):
		return self.GetModify()

	### NOTE: CodeEditor :: Clear 				=> Clear the text
	def Clear(self):
		self.ClearAll()

	### NOTE: CodeEditor :: SetInsertionPoint	=> Set an anchor for insertion
	def SetInsertionPoint(self, pos):
		self.SetCurrentPos(pos)
		self.SetAnchor(pos)

	### NOTE: CodeEditor :: ShowPosition 		=> Go to the line of selected position
	def ShowPosition(self, pos):
		line = self.LineFromPosition(pos)
#		self.EnsureVisible(line)
		self.GotoLine(line)

	### NOTE: CodeEditor :: GetLastPosition 	=> todo
	def GetLastPosition(self):
		return self.GetLength()

	### NOTE: CodeEditor :: GetPositionFromLine => todo
	def GetPositionFromLine(self, line):
		return self.PositionFromLine(line)

	### NOTE: CodeEditor :: GetRange 			=> Get the text range
	def GetRange(self, start, end):
		return self.GetTextRange(start, end)

	### NOTE: CodeEditor :: GetSelection 		=> Get the selected text
	def GetSelection(self):
		return self.GetAnchor(), self.GetCurrentPos()

	### NOTE: CodeEditor :: SetSelection 		=> Set the selected text
	def SetSelection(self, start, end):
		self.SetSelectionStart(start)
		self.SetSelectionEnd(end)

	### NOTE: CodeEditor :: SelectLine 		=> Select the line
	def SelectLine(self, line):
		start = self.PositionFromLine(line)
		end = self.GetLineEndPosition(line)
		self.SetSelection(start, end)

	### NOTE: CodeEditor :: SetUpEditor 		=> Configure lexer and color
	def SetUpEditor(self):
		"""
		This method carries out the work of setting up the demo editor.
		It's seperate so as not to clutter up the init code.
		"""
		import keyword

		self.SetLexer(stc.STC_LEX_PYTHON)
		self.SetKeyWords(0, " ".join(keyword.kwlist))

		### Enable folding
		self.SetProperty("fold", "1")

		### Highlight tab/space mixing (shouldn't be any)
		self.SetProperty("tab.timmy.whinge.level", "1")

		### Set left and right margins
		self.SetMargins(2, 2)

		### Set up the numbers in the margin for margin #1
		self.SetMarginType(1, wx.stc.STC_MARGIN_NUMBER)
		### Reasonable value for, say, 4-5 digits using a mono font (40 pix)
		self.SetMarginWidth(1, 40)

		### Indentation and tab stuff
		self.SetIndent(4)               # Proscribed indent size for wx
		self.SetIndentationGuides(True) # Show indent guides
		self.SetBackSpaceUnIndents(True)# Backspace unindents rather than delete 1 space
		self.SetTabIndents(True)        # Tab key indents
		self.SetTabWidth(4)             # Proscribed tab size for wx
		self.SetUseTabs(True)          # Use spaces rather than tabs, or
		# TabTimmy will complain!
		### White space
		self.SetViewWhiteSpace(False)   # Don't view white space

		### EOL: Since we are loading/saving ourselves, and the
		### strings will always have \n's in them, set the STC to
		### edit them that way.
		self.SetEOLMode(wx.stc.STC_EOL_LF)
		self.SetViewEOL(False)

		### No right-edge mode indicator
		self.SetEdgeMode(stc.STC_EDGE_NONE)

		### Setup a margin to hold fold markers
		self.SetMarginType(2, stc.STC_MARGIN_SYMBOL)
		self.SetMarginMask(2, stc.STC_MASK_FOLDERS)
		self.SetMarginSensitive(2, True)
		self.SetMarginWidth(2, 12)

		### and now set up the fold markers
		self.MarkerDefine(stc.STC_MARKNUM_FOLDEREND, stc.STC_MARK_BOXPLUSCONNECTED, "white", "black")
		self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPENMID, stc.STC_MARK_BOXMINUSCONNECTED, "white", "black")
		self.MarkerDefine(stc.STC_MARKNUM_FOLDERMIDTAIL, stc.STC_MARK_TCORNER, "white", "black")
		self.MarkerDefine(stc.STC_MARKNUM_FOLDERTAIL, stc.STC_MARK_LCORNER, "white", "black")
		self.MarkerDefine(stc.STC_MARKNUM_FOLDERSUB, stc.STC_MARK_VLINE, "white", "black")
		self.MarkerDefine(stc.STC_MARKNUM_FOLDER, stc.STC_MARK_BOXPLUS, "white", "black")
		self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPEN, stc.STC_MARK_BOXMINUS, "white", "black")

		### Global default style
		if wx.Platform == '__WXMSW__':
			self.StyleSetSpec(stc.STC_STYLE_DEFAULT, 'fore:#000000,back:#FFFFFF,face:Courier New,size:9')
		elif wx.Platform == '__WXMAC__':
		### TODO: if this looks fine on Linux too, remove the Mac-specific case
		### and use this whenever OS != MSW.
			self.StyleSetSpec(stc.STC_STYLE_DEFAULT, 'fore:#000000,back:#FFFFFF,face:Monaco')
		else:
			self.StyleSetSpec(stc.STC_STYLE_DEFAULT, 'fore:#000000,back:#FFFFFF,face:Courier,size:9')

		# Clear styles and revert to default.
		self.StyleClearAll()

		# Following style specs only indicate differences from default.
		# The rest remains unchanged.

		# Line numbers in margin
		self.StyleSetSpec(wx.stc.STC_STYLE_LINENUMBER, 'fore:#000000,back:#99A9C2')
		# Highlighted brace
		self.StyleSetSpec(wx.stc.STC_STYLE_BRACELIGHT, 'fore:#00009D,back:#FFFF00')
		# Unmatched brace
		self.StyleSetSpec(wx.stc.STC_STYLE_BRACEBAD, 'fore:#00009D,back:#FF0000')
		# Indentation guide
		self.StyleSetSpec(wx.stc.STC_STYLE_INDENTGUIDE, "fore:#CDCDCD")

		# Python styles
		self.StyleSetSpec(wx.stc.STC_P_DEFAULT, 'fore:#000000')
		# Comments
		self.StyleSetSpec(wx.stc.STC_P_COMMENTLINE, 'fore:#008000,back:#F0FFF0')
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

		self.SetSelBackground(True, wx.SystemSettings_GetColour(wx.SYS_COLOUR_HIGHLIGHT) )
		self.SetSelForeground(True, wx.SystemSettings_GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT))

	### NOTE: CodeEditor :: RegisterModifiedEvent => todo
	def RegisterModifiedEvent(self, eventHandler):
		"""
		"""
		self.Bind(wx.stc.EVT_STC_CHANGE, eventHandler)


### EditionFile-----------------------------------------------------
### NOTE: EditionFile << CodeEditor :: Expect EditionFile objects to clearly separate file and notebook attributes
class EditionFile(CodeEditor):
	"""
	"""

	#
	def __init__(self, parent, path, code):
		""" Constructor
		"""
		CodeEditor.__init__(self, parent)

		# variables
		self.modify = False
		self.error_flag = False
		self.SetFilename(path)
		self.SetValue(code)

	# NOTE: EditionFile :: __str__		=> String representation of the class
	@classmethod
	def __str__(cls):
		attrs = [('modify', 'boolean'), ('error_flag', 'boolean')]
		class_name = "EditionFile"
		parent = "CodeEditor"
		methods = [
			('__init__', 'self, parent'),
			('ContainError', 'self')
		]
		return "\n--------------------------------------------------\
		\n\tClass :\t\t%s\n\n\tInherit from :\t%s\n\n\tAttributes :\t%s\n\n\tMethods :\t%s\n" % (
			class_name, parent, '\n\t\t\t'.join([attr + "\t:: " + typ for attr, typ in attrs]),
			"\n\t\t\t".join([method + "\tparams :: " + params for method, params in methods])
		)

	# NOTE: EditionFile :: ContainError 		=> Getter of the error flag
	def ContainError(self):
		"""
		"""
		return self.error_flag

### ----------------------------------------------------------------


### EditionNotebook-------------------------------------------------
### NOTE: EditionNotebook << wx.Notebook :: Notebook for multiple file edition
class EditionNotebook(wx.Notebook):
	"""
	"""

	### NOTE: EditionNotebook :: constructor 	=> __init__(self, *args, **kwargs)
	def __init__(self, *args, **kwargs):
		"""
		Notebook class that allows overriding and adding methods.

		@param parent: parent windows
		@param id: id
		@param pos: windows position
		@param size: windows size
		@param style: windows style
		@param name: windows name
		"""

		wx.Notebook.__init__(self, *args, **kwargs)

		# local copy
		self.parent = args[0]
		self.pages = []            # keeps track of pages

		# variables
		self.force_saving = False

		#icon under tab
		imgList = wx.ImageList(16, 16)
		for img in [os.path.join(ICON_PATH_16_16, 'featureFile.png')]:
			imgList.Add(wx.Image(img, wx.BITMAP_TYPE_PNG).ConvertToBitmap())
		self.AssignImageList(imgList)

		### binding
		self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.__PageChanged)

		self.Show()

	# NOTE: EditionNotebook :: __str__		=> String representation of the class
	@classmethod
	def __str__(cls):
		attrs = [('parent', 'UNDEFINED'), ('pages', 'list<EditionFile>'), ('force_saving', 'boolean')]
		class_name = "EditionNotebook"
		parent = "wx.Notebook"
		methods = [
			('__init__', 'self, parent, ID, pos, size, style'),
			('GetPages', 'self'),
			('AddEditPage', 'self, title, path'),
			('GetPageByName', 'self, name'),
			('DoOpenFile', 'self'),
			('DoSaveFile', 'self, base_name, code'),
			('__PageChanged', 'self, event'),
			('OnClosePage', 'self, event'),
			('OnKeyDown', 'self, event'),
			('OnCut', 'self, event'),
			('OnCopy', 'self, event'),
			('OnPaste', 'self, event'),
			('OnReIndent', 'self, event'),
			('OnDelete', 'self, event'),
			('OnSelectAll', 'self, event'),
			('<static> WriteFile', 'fileName, code, encode'),
			('<static> CheckIndent', 'filename')
		]
		return "\n--------------------------------------------------\
		\n\tClass :\t\t%s\n\n\tInherit from :\t%s\n\n\tAttributes :\t%s\n\n\tMethods :\t%s\n" % (
			class_name, parent, '\n\t\t\t'.join([attr + "\t:: " + typ for attr, typ in attrs]),
			"\n\t\t\t".join([method + "\tparams :: " + params for method, params in methods])
		)

	### NOTE: EditionNotebook :: GetPages 		=> Get the list of created pages
	def GetPages(self):
		"""
		"""
		return self.pages

	### NOTE: EditionNotebook :: AddEditPage 	=> Create a new page
	def AddEditPage(self, title="", path=""):
		"""
		Adds a new page for editing to the notebook and keeps track of it.

		@type title: string
		@param title: Title for a new page
		"""

		fileCode = ""

		
		### FIXME: try to consider zipfile in zipfile
		L = re.findall("(.*\.(amd|cmd))\%s(.*)" % os.sep, path)

		if L != []:
			model_path, ext, name = L.pop(0)
			if zipfile.is_zipfile(model_path):
				importer = zipfile.ZipFile(model_path, "r")
				fileInfo = importer.getinfo(name)
				fileCode = importer.read(fileInfo)
				importer.close()
		else:
			if os.path.exists(path):
    				with open(path, 'r') as f:
						fileCode = f.read()
			else:
				### fileCode is path (user work with IOString code, not file object)
				fileCode = path

		### new page
		newPage = EditionFile(self, path, fileCode)
		newPage.SetFocus()

		### bind the page
		newPage.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
		newPage.Bind(wx.EVT_CHAR, self.parent.OnChar)

		### add page
		self.pages.append(newPage)
		self.AddPage(newPage, title, imageId=0)

	### NOTE: EditionNotebook :: GetPageByName => Return the page with the required name
	def GetPageByName(self, name=''):
		"""
		"""
		for i in xrange(len(self.pages)):
			if name == self.GetPageText(i):
				return self.GetPage(i)
		return None

	### NOTE: EditionNotebook :: __PageChanged => Event when page changed
	def __PageChanged(self, evt):
		"""
		"""

		try:
			canvas = self.GetPage(self.GetSelection())

			### permet d'activer les redo et undo pour chaque page
			self.parent.tb.EnableTool(wx.ID_UNDO, not len(canvas.stockUndo) == 0)
			self.parent.tb.EnableTool(wx.ID_REDO, not len(canvas.stockRedo) == 0)

			canvas.deselect()
			canvas.Refresh()

		except Exception:
			pass
		evt.Skip()

	### NOTE: EditionNotebook :: OnClosePage 	=> Event when the close button is clicked
	def OnClosePage(self, evt, id):
		""" Close current page.

			@type evt: event
			@param  evt: Event Object, None by default
		"""

		if self.GetPageCount() > 0:
			self.pages.remove(self.GetPage(id))
			return self.DeletePage(id)

		return True

	### NOTE: EditionNotebook :: OnKeyDown 	=> Event when key is pressed
	def OnKeyDown(self, event):
		"""
		"""
		keycode = event.GetKeyCode()
		controlDown = event.CmdDown()
		currentPage = self.GetCurrentPage()

		if keycode == wx.WXK_UP or keycode == wx.WXK_DOWN:
			event.Skip()
		elif keycode == 68 and controlDown:
			cur_line = currentPage.GetCurrentLine()
			shiftDown = event.ShiftDown()
			if shiftDown:
				indent = currentPage.GetLineIndentPosition(cur_line)
				currentPage.Home()
				currentPage.DelWordRight()
				currentPage.SetCurrentPos(indent)
			else:
				currentPage.InsertText(currentPage.PositionFromLine(cur_line), "#")
		else:
			event.Skip()

	### NOTE: EditionNotebook :: DoOpenFile 	=> Opening file method
	def DoOpenFile(self):
		"""
		"""
		currentPage = self.GetCurrentPage()
		wcd = 'All files (*)|*|Editor files (*.py)|*.py'
		dir = HOME_PATH
		open_dlg = wx.FileDialog(self, message=_('Choose a file'), defaultDir=dir, defaultFile='', wildcard=wcd,
		                         style=wx.OPEN | wx.CHANGE_DIR)
		if open_dlg.ShowModal() == wx.ID_OK:
			path = open_dlg.GetPath()

			try:
				with codecs.open(path, 'r', 'utf-8') as f:
					text = f.read()

				if currentPage.GetLastPosition():
					currentPage().Clear()
				currentPage().WriteText(text)
				currentPage().SetFilename(path)

				currentPage.modify = False

			except Exception, info:
				wx.MessageBox(_('Error opening file:\n%s\n')%str(info),\
							"Open file function",\
							wx.OK | wx.ICON_ERROR)

		open_dlg.Destroy()

	### NOTE: EditionNotebook :: DoSaveFile 	=> Saving file method
	def DoSaveFile(self, code):
		"""
		"""

		currentPage = self.GetCurrentPage()
		
		abs_path = currentPage.GetFilename()    # /home/../toto.*
		fic_filename = os.path.basename(abs_path)    # fileName toto.*
		model_dir = os.path.dirname(abs_path)        # model toto.amd
		
		### if zipfile
		if zipfile.is_zipfile(model_dir):

			model_name, model_ext = os.path.basename(model_dir).split('.')        # toto, .amd or .cmd
			fic_name, fic_ext = fic_filename.split('.')            # toto, *

			### write code in base_name temporary file
			self.WriteFile(fic_filename, code)

			### update archive
			zf = ZipManager.Zip(model_dir)
			zf.Update(replace_files=[fic_filename])

			### Clean up the temporary file yourself
			os.remove(fic_filename)

			### reload module only if zipped python file is not plugins
			### update only for python file of model which have path like .../name.amd(.cmd)/name.ext
			if isinstance(self.parent, Base) and fic_name == model_name and fic_ext == 'py':
				self.parent.UpdateModule()

		### if python file in zipfile but also in directory into zipfile
		elif zipfile.is_zipfile(os.path.dirname(model_dir)):

			r_file = os.path.join(os.path.basename(model_dir), fic_filename)
			model_dir = os.path.dirname(model_dir)

			model_name, model_ext = os.path.basename(model_dir).split('.')        # toto, .amd or .cmd
			fic_name, fic_ext = fic_filename.split('.')            # toto, *

			### write code in base_name temporary file
			self.WriteFile(fic_filename, code)

			### update archive
			zf = ZipManager.Zip(model_dir)

			zf.Update(replace_files=[r_file])

			# Clean up the temporary file yourself
			os.remove(fic_filename)

			### reload module only if zipped python file is not plugins
			### update only for python file of model which have path like .../name.amd(.cmd)/name.ext
			if isinstance(self.parent, Base) and fic_name == model_name and fic_ext == 'py':
				self.parent.UpdateModule()

		### if python file not in zipfile
		else:
			#assert (os.path.isfile(abs_path))
			if os.path.isfile(abs_path):
				### write code in last name saved file
				self.WriteFile(abs_path, code)

				if isinstance(self.parent, Base):
					### reload module
					self.parent.UpdateModule()
			else:
				pass

		### disable save icon in toolbar
		self.parent.toolbar.EnableTool(self.parent.save.GetId(), False)

		### status bar notification
		self.parent.Notification(False, _('%s saved') % fic_filename, '', '')

	### NOTE: EditionNotebook :: @WriteFile 	=> Write with correct encode
	@staticmethod
	def WriteFile(fileName, code, encode='utf-8'):
		""" Static method which write modification to the fileName file
		"""

		with codecs.open(fileName, 'w', encode) as f:
			f.write(code.decode(encode))

	### NOTE: EditionNotebook :: OnCut 		=> Event on cut
	def OnCut(self, event):
		"""
		"""
		self.GetCurrentPage().Cut()

	### NOTE: EditionNotebook :: OnCopy 		=> Event on copy
	def OnCopy(self, event):
		"""
		"""
		self.GetCurrentPage().Copy()

	### NOTE: EditionNotebook :: OnPaste 		=> Event on paste
	def OnPaste(self, event):
		"""
		"""
		self.GetCurrentPage().Paste()

	### NOTE: EditionNotebook :: CheckIndent 	=> Check the code indentation
	@staticmethod
	@redirectStdout
	def CheckIndent(fileName):
		"""
		"""
		tabnanny.check(fileName)

	### NOTE: EditionNotebook :: OnReIndent 	=> Event on re-indent
	def OnReIndent(self, event):
		"""
		"""
		cp = self.GetCurrentPage()

		parent_path = os.path.dirname(cp.GetFilename())

		### if zipfile
		if zipfile.is_zipfile(parent_path):
			### python name file
			name = os.path.basename(cp.GetFilename())

			### extract python file from zip in tmp directory
			sourceZip = zipfile.ZipFile(parent_path, 'r')
			sourceZip.extract(name, gettempdir())
			sourceZip.close()

			### temporary python name file
			python_file = os.path.join(gettempdir(), name)
		else:
			### python name file
			python_file = cp.GetFilename()

		### reindent from file
		os.system("python %s" % os.path.join(HOME_PATH, "reindent.py") + " " + python_file)

		### only with python 2.6
		with codecs.open(str(python_file), 'r', 'utf-8') as f:
			text = f.read()

		### relaod text in the textCtrl of Editor
		cp.Clear()
		cp.SetValue(text)

		### status bar notification
		self.parent.Notification(True, _('re-indented'), '', '')

	def OnComment(self, event):
		""" Comment current line
		"""
		cp = self.GetCurrentPage()
		cur_line = cp.GetCurrentLine()
		cp.InsertText(cp.PositionFromLine(cur_line), "#")

	def OnUnComment(self, event):
		""" Uncomment current line
		"""
		cp = self.GetCurrentPage()
		cur_line = cp.GetCurrentLine()
		indent = cp.GetLineIndentPosition(cur_line)
		cp.Home()
		cp.DelWordRight()
		cp.SetCurrentPos(indent)

	### 
	def OnDelete(self, event):
		"""
		"""
		cp = self.GetCurrentPage()
		frm, to = cp.GetSelection()
		cp.Remove(frm, to)

	###
	def OnSelectAll(self, event):
		"""
		"""
		self.GetCurrentPage().SelectAll()

###------------------------------------------------------------
class Base(object):
	""" Editor Base class
	"""

	### 
	def __init__(self, parent, id, title):
		""" Constructor.
		"""

		### copy
		self.parent = parent

#		### if parent, we want Editor as a panel
#		if self.parent:
#
#			### call constructor and set background color of panel
#			wx.Panel.__init__(self, self.parent, id)
#			self.SetBackgroundColour(wx.WHITE)
#
#			### Define sizer
#			sizer = wx.BoxSizer(wx.VERTICAL)
#
#			### create notebook
#			self.nb = EditionNotebook(self, wx.ID_ANY, style=wx.CLIP_CHILDREN)
#			### create juste for the bind of action (save,...) of the toolbar - Warning it must stay here !
#			self.menuBar = self.CreateMenu()
#			### create toolbar
#			self.toolbar = self.CreateTB()
#			###recover the statusbar of mainW
#			self.statusbar = parent.GetStatusBar()
#
#			### add toolbar and notebook
#			sizer.Add(self.toolbar, 0, wx.ALL | wx.ALIGN_LEFT | wx.EXPAND)
#			sizer.Add(self.nb, 1 ,wx.EXPAND)
#
#			### set sizer and layout of panel
#			self.SetSizer(sizer)
#			self.SetAutoLayout(True)
#
#		### if parent is none we want editor as a frame
#		else:
#
#			### call constructor
#			wx.Frame.__init__(self, self.parent, id, title, size=(600, 500), style=wx.DEFAULT_FRAME_STYLE)
#
#			### Create notebook
#			self.nb = EditionNotebook(self, wx.ID_ANY, style=wx.CLIP_CHILDREN)
#
#			### create menu, toolbar and statusbar for the frame
#			self.menuBar = self.CreateMenu()
#			self.SetMenuBar(self.menuBar)
#			self.toolbar = self.CreateTB()
#			self.statusbar= self.GetStatusBar()
#
#			### binding
#			self.Bind(wx.EVT_CLOSE, self.QuitApplication)
#
#			self.Centre()
#
#			### just for windows
#			e = wx.SizeEvent(self.GetSize())
#			self.ProcessEvent(e)

		# notebook
		self.read_only = False

		# find param
		self.pos = 0
		self.size = 0

	def update(self, concret_subject=None):
		""" Update method that manages the embedded editor depending of the selected model in the canvas
		"""

		state = concret_subject.GetState()
		canvas = state['canvas']
		model = state['model']

		### delete all tab on notebook
		while(self.nb.GetPageCount()):
			self.nb.DeletePage(0)

		### add behavioral code
		self.AddEditPage(model.label, model.python_path)

		### add test file
		if hasattr(model, 'GetTestFile'):
			L = model.GetTestFile()
			for i,s in enumerate(map(lambda l: os.path.join(model.model_path, l), L)):
				self.AddEditPage(L[i], s)

		self.cb = model

	def CreateMenu(self):
		""" Create the menu
		"""
		# setting up menubar
		menubar = wx.MenuBar()

		### file sub menu---------------------------------------------------
		file = wx.Menu()

		self.save = wx.MenuItem(file, wx.NewId(), _('&Save\tCtrl+S'), _('Save the file'))
		self.save_as = wx.MenuItem(file, wx.NewId(), _('&Save As\tCtrl+S'), _('Save as an other file'))
		self.quit = wx.MenuItem(file, wx.NewId(), _('&Quit\tCtrl+Q'), _('Quit the application'))

		self.save.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH, 'save.png')))
		self.save_as.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH, 'save_as.png')))
		self.quit.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH, 'exit.png')))

		items = [self.save, self.save_as, self.quit]

		if wx.VERSION_STRING < '4.0':
			for item in items: file.AppendItem(item)
		else:
			for item in items: file.Append(item)

		### -----------------------------------------------------------------

		### edit sub menu----------------------------------------------------
		edit = wx.Menu()

		self.search = wx.MenuItem(edit, wx.NewId(), _('&Search\tCtrl+F'), _('Search text'))

		self.cut = wx.MenuItem(edit, wx.NewId(), _('&Cut\tCtrl+X'), _('Cut the selection'))
		self.copy = wx.MenuItem(edit, wx.NewId(), _('&Copy\tCtrl+C'), _('Copy the selection'))
		self.paste = wx.MenuItem(edit, wx.NewId(), _('&Paste\tCtrl+V'), _('Paste text from clipboard'))
		delete = wx.MenuItem(edit, wx.NewId(), _('&Delete'), _('Delete the selected text'))
		select = wx.MenuItem(edit, wx.NewId(), _('Select &All\tCtrl+A'), _('Select the entire text'))
		reindent = wx.MenuItem(edit, wx.NewId(), _('Re-indent\tCtrl+R'), _('re-indent all code'))
		comment = wx.MenuItem(edit, wx.NewId(), _('&Comment\tCtrl+D'), _('comment current ligne'))
		uncomment = wx.MenuItem(edit, wx.NewId(), _('&Uncomment\tCtrl+Shift+D'), _('uncomment current ligne'))

		self.cut.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH, 'cut.png')))
		self.copy.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH, 'copy.png')))
		self.paste.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH, 'paste.png')))
		delete.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH, 'delete.png')))
		reindent.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH, 're-indent.png')))
		comment.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH, 'comment_add.png')))
		uncomment.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH, 'comment_remove.png')))

		### Shortcut
		accel_tbl = wx.AcceleratorTable([(wx.ACCEL_CTRL,  ord('S'), self.save.GetId()),
										(wx.ACCEL_CTRL,  ord('X'), self.cut.GetId()),
										(wx.ACCEL_CTRL,  ord('C'), self.copy.GetId()),
										(wx.ACCEL_CTRL,  ord('V'), self.paste.GetId()),
										(wx.ACCEL_CTRL,  ord('D'), comment.GetId()),
										(wx.ACCEL_CTRL| wx.ACCEL_SHIFT,  ord('D'), uncomment.GetId()),
										(wx.ACCEL_CTRL,  ord('F'), self.search.GetId())
										])
		self.SetAcceleratorTable(accel_tbl)

		if wx.VERSION_STRING < '4.0':
			edit.AppendItem(self.cut)
			edit.AppendItem(self.copy)
			edit.AppendItem(self.paste)
			edit.AppendItem(reindent)
			edit.AppendItem(comment)
			edit.AppendItem(uncomment)
			edit.AppendItem(self.search)
			edit.AppendSeparator()
			edit.AppendItem(delete)
			edit.AppendSeparator()
			edit.AppendItem(select)
		else:
			edit.Append(self.cut)
			edit.Append(self.copy)
			edit.Append(self.paste)
			edit.Append(reindent)
			edit.Append(comment)
			edit.Append(uncomment)
			edit.Append(self.search)
			edit.AppendSeparator()
			edit.Append(delete)
			edit.AppendSeparator()
			edit.Append(select)
		### -------------------------------------------------------------------

		### view sub menu------------------------------------------------------
		view = wx.Menu()

		showStatusBar = wx.MenuItem(view, wx.NewId(), _('&Statusbar'), _('Show statusBar'))
		if wx.VERSION_STRING < '4.0':
			view.AppendItem(showStatusBar)
		else:
			view.Append(showStatusBar)

		### ------------------------------------------------------------------

		### help sub menu-----------------------------------------------------
		help = wx.Menu()

		about = wx.MenuItem(help, wx.NewId(), _('&About\tF1'), _('About editor'))
		about.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH, 'info.png')))
		if wx.VERSION_STRING < '4.0':
			help.AppendItem(about)
		else:
			help.Append(about)
		### -------------------------------------------------------------------

		menubar.Append(file, _('&File'))
		menubar.Append(edit, _('&Edit'))
		menubar.Append(view, _('&View'))
		menubar.Append(help, _('&Help'))

		### binding event
		self.Bind(wx.EVT_MENU, self.OnSaveFile, id=self.save.GetId())
		self.Bind(wx.EVT_MENU, self.OnSaveAsFile, id=self.save_as.GetId())
		self.Bind(wx.EVT_MENU, self.QuitApplication, id=self.quit.GetId())
		self.Bind(wx.EVT_MENU, self.nb.OnCut, id=self.cut.GetId())
		self.Bind(wx.EVT_MENU, self.nb.OnCopy, id=self.copy.GetId())
		self.Bind(wx.EVT_MENU, self.nb.OnPaste, id=self.paste.GetId())
		self.Bind(wx.EVT_MENU, self.nb.OnReIndent, id=reindent.GetId())
		self.Bind(wx.EVT_MENU, self.nb.OnComment, id=comment.GetId())
		self.Bind(wx.EVT_MENU, self.OnSearch, id=self.search.GetId())
		self.Bind(wx.EVT_MENU, self.nb.OnUnComment, id=uncomment.GetId())
		self.Bind(wx.EVT_MENU, self.nb.OnDelete, id=delete.GetId())
		self.Bind(wx.EVT_MENU, self.nb.OnSelectAll, id=select.GetId())
		self.Bind(wx.EVT_MENU, self.ToggleStatusBar, id=showStatusBar.GetId())
		self.Bind(wx.EVT_MENU, self.OnAbout, id=about.GetId())
		self.Bind(wx.EVT_FIND, self.OnFind)
		self.Bind(wx.EVT_FIND_NEXT, self.OnFind)

		return menubar

	def CreateTB(self):
		""" Create tool-bar
		"""

		if not self.parent:
			tb = self.CreateToolBar(wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT | wx.TB_TEXT)

			self.Bind(wx.EVT_TOOL, self.OnSaveFile, tb.AddSimpleTool(self.save.GetId(), wx.Bitmap(os.path.join(ICON_PATH, 'save.png')), _('Save'), ''))
			tb.AddSeparator()
			self.Bind(wx.EVT_TOOL, self.nb.OnCut, tb.AddSimpleTool(self.cut.GetId(), wx.Bitmap(os.path.join(ICON_PATH,'cut.png')), _('Cut'), ''))
			self.Bind(wx.EVT_TOOL, self.nb.OnCopy, tb.AddSimpleTool(self.copy.GetId(), wx.Bitmap(os.path.join(ICON_PATH,'copy.png')), _('Copy'), ''))
			self.Bind(wx.EVT_TOOL, self.nb.OnPaste, tb.AddSimpleTool(self.paste.GetId(), wx.Bitmap(os.path.join(ICON_PATH,'paste.png')), _('Paste'), ''))
			self.Bind(wx.EVT_TOOL, self.QuitApplication, id = self.quit.GetId())

		else:

			tb = wx.ToolBar(self, -1)
			tb.SetToolBitmapSize((16, 16))# this required for non-standard size buttons on MSW

			if wx.VERSION_STRING < '4.0':
				tb.AddTool(self.save.GetId(), wx.Bitmap(os.path.join(ICON_PATH, 'save.png')), shortHelpString=_('Save'), longHelpString=_('Save the file'))
				tb.AddTool(self.cut.GetId(), wx.Bitmap(os.path.join(ICON_PATH,'cut.png')), shortHelpString=_('Cut'), longHelpString=_('Cut the selection'))
				tb.AddTool(self.copy.GetId(), wx.Bitmap(os.path.join(ICON_PATH,'copy.png')), shortHelpString=_('Copy'), longHelpString=_('Copy the selection'))
				tb.AddTool(self.paste.GetId(), wx.Bitmap(os.path.join(ICON_PATH,'paste.png')), shortHelpString=_('Paste'), longHelpString=_('Paste text from clipboard'))
			else:
				tb.AddTool(self.save.GetId(), "",wx.Bitmap(os.path.join(ICON_PATH, 'save.png')), shortHelp=_('Save'))
				tb.AddTool(self.cut.GetId(), "",wx.Bitmap(os.path.join(ICON_PATH,'cut.png')), shortHelp=_('Cut'))
				tb.AddTool(self.copy.GetId(), "",wx.Bitmap(os.path.join(ICON_PATH,'copy.png')), shortHelp=_('Copy'))
				tb.AddTool(self.paste.GetId(), "",wx.Bitmap(os.path.join(ICON_PATH,'paste.png')), shortHelp=_('Paste'))

			self.Bind(wx.EVT_TOOL, self.OnSaveFile, id=self.save.GetId())
			self.Bind(wx.EVT_TOOL, self.nb.OnCut, id=self.cut.GetId())
			self.Bind(wx.EVT_TOOL, self.nb.OnCopy, id=self.copy.GetId())
			self.Bind(wx.EVT_TOOL, self.nb.OnPaste, id= self.paste.GetId())

		tb.Realize()
		return tb

	def GetNoteBook(self):
		""" Return the NoteBook
		"""
		return self.nb

	# NOTE: Editor :: __str__		=> String representation of the class
	@classmethod
	def __str__(cls):
		attrs = [('read_only', 'boolean'), ('nb', 'EditionNotebook'), ('save', 'wx.MenuItem'),('toolbar', 'wx.Toolbar')]
		class_name = "Editor"
		parent = "wx.Frame, wx.Panel"
		methods = [
			('__init__', 'self, parent, id, title'),
			('AddEditPage', 'self, title, path'),
			('SetReadOnly', 'self, bol'),
			('MakeIcon', 'self, img'),
			('ConfigSaving', 'self, base_name, dir_name, code'),
			('CheckErrors', 'self, base_name, code, new_instance'),
			('SavingErrors', 'self, new_instance'),
			('Notification', 'self, modify, *args'),
			('GetStatusBar', 'self'),
			('ToggleStatusBar', 'self, event'),
			('OnChar', 'self, event'),
			('OnOpenFile', 'self, event'),
			('OnSaveFile', 'self, event'),
			('QuitApplication', 'self, event'),
			('OnAbout', 'self, event')
		]
		return "\n--------------------------------------------------\
		\n\tClass :\t\t%s\n\n\tInherit from :\t%s\n\n\tAttributes :\t%s\n\n\tMethods :\t%s\n" % (
			class_name, parent, '\n\t\t\t'.join([attr + "\t:: " + typ for attr, typ in attrs]),
			"\n\t\t\t".join([method + "\tparams :: " + params for method, params in methods])
		)

	# NOTE: Editor :: AddEditPage		=> Add new page
	def AddEditPage(self, title='', path=''):
		self.nb.AddEditPage(title, path)

	### NOTE: Editor :: SetReadOnly 			=> Set the editor read-only
	def SetReadOnly(self, bol):
		self.read_only = bol

	### NOTE: Editor :: MakeIcon 				=> Make icons for the various platforms
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
		if wx.VERSION_STRING < '4.0':
			icon =  wx.IconFromBitmap(img.ConvertToBitmap())
		else:
			icon =  wx.Icon(img.ConvertToBitmap())

		return icon

	### NOTE: Editor :: OnOnpenFile 			=> Event OnOpenFile
	def OnOpenFile(self, event):
		""" Open File has been invoked
		"""
		if self.nb.GetCurrentPage().isModified():
			dlg = wx.MessageDialog(self, _('Save changes?'), _('Code Editor'), wx.YES_NO | wx.YES_DEFAULT | wx.CANCEL |wx.ICON_QUESTION)
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

	### NOTE: Editor :: OnSaveFile			=> Event when save menu has been clicked
	def OnSaveFile(self, event):
		""" Save menu has been clicked.
		"""
		currentPage = self.nb.GetCurrentPage()
		fn = currentPage.GetFilename()

		if not self.read_only:

			assert fn != ''

			### base and dir name of python file
			base_name = os.path.basename(fn)
			dir_name = os.path.dirname(fn)

			### code text
			code = currentPage.GetValue().encode('utf-8')
			code = '\n'.join(code.splitlines()) + '\n'

			new_instance = self.ConfigSaving(base_name, dir_name, code)

			### there is error in file ?
			currentPage.error_flag = isinstance(new_instance, Exception)

			self.CheckErrors(base_name, code, new_instance)

		else:
			### status bar notification
			self.Notification(False, _('%s not saved' % fn), _('file in readonly'), '')

	def OnSearch(self, evt):
		currentPage = self.nb.GetCurrentPage()
		self.txt = currentPage.GetValue().encode('utf-8')
		self.data = wx.FindReplaceData()   # initializes and holds search parameters
		self.dlg = wx.FindReplaceDialog(currentPage, self.data, 'Find')
		self.dlg.Show()
	
	def OnFind(self, evt):
		fstring = self.data.GetFindString()          # also from event.GetFindString()
		self.pos = self.txt.find(fstring, self.pos+self.size)
		self.size = len(fstring)

		highlight_start_pos = self.pos
		highlight_end_pos = self.pos+self.size

		### go to the finded word
		currentPage = self.nb.GetCurrentPage()
		currentPage.GotoPos(self.pos)
		
		currentPage.StartStyling(highlight_start_pos, 0xff)
		currentPage.SetStyling(highlight_end_pos - highlight_start_pos, stc.STC_P_COMMENTLINE)
		currentPage.StartStyling(highlight_end_pos, 0x00)
		currentPage.SetStyling(len(self.txt) - highlight_end_pos, stc.STC_STYLE_DEFAULT)

	def OnSaveAsFile(self, event):
		"""
		"""

		currentPage = self.nb.GetCurrentPage()
		fn = currentPage.GetFilename()

		if not self.read_only:

			assert fn != ''

			dir_name = os.path.dirname(fn)

			msg = "Python files (*.py)|*.py|All files (*)|*"

			wcd = _(msg)
			home = dir_name or HOME_PATH
			save_dlg = wx.FileDialog(self, message=_('Save file as...'), defaultDir=home, defaultFile='', wildcard=wcd, style=wx.SAVE | wx.OVERWRITE_PROMPT)

		if save_dlg.ShowModal() == wx.ID_OK:

			path = os.path.normpath(save_dlg.GetPath())
			ext = os.path.splitext(path)[-1]
			file_name = save_dlg.GetFilename()

			### code text
			code = currentPage.GetValue().encode('utf-8')
			code = '\n'.join(code.splitlines()) + '\n'

			### write code in last name saved file
			self.nb.WriteFile(path, code)

	### NOTE: Editor :: ConfigSaving 			=> Configure save vars
	def ConfigSaving(self, base_name, dir_name, code):
		"""
		"""

		new_instance = None
		### if force saving when quitting Editor
		if self.nb.force_saving:
			self.nb.DoSaveFile(code)
		else:
			new_instance = getObjectFromString(code)

		return new_instance

	# NOTE: Editor :: CheckErrors 			=> Check errors in files before saving
	def CheckErrors(self, base_name, code, new_instance):
		"""
		"""
		if not self.nb.GetCurrentPage().ContainError():
			self.nb.DoSaveFile(code)

			### DAM and UAM update which are implemented in string object
			if not base_name.endswith('.py'):
				### canvas and diagram
				canvas = self.parent
				dia = canvas.GetDiagram()

				### current level
				cl =  dia.current_level

				### if DAM string is in code
				if 'DAM' in code:
					canvas.SetDAM(cl, code)
				else:
					canvas.SetUAM(cl, code)

		### some errors in file
		else:
			self.SavingErrors(new_instance)

	# NOTE: Editor :: SavingErrors			=> Errors treatment
	def SavingErrors(self, new_instance):
		""" perhaps re-indent ?
		"""

		fn = self.nb.GetCurrentPage().GetFilename()

		output_checking = EditionNotebook.CheckIndent(fn)
		if "indent not equal" in output_checking:
			dial = wx.MessageDialog(self, _('Tab problem in %s.\n%s \
				\nYou can try to re-indent it with Edit-> Re-indent sub-menu.' % (fn, output_checking)),
			                        _('Code Editor'), wx.OK | wx.ICON_INFORMATION)
			dial.ShowModal()
		else:
			### status bar notification
			msg = _('Saving Error')

			try:
				self.Notification(True, msg, str(new_instance.args[0]), str(new_instance.args[1]))
			except UnicodeDecodeError:
				self.Notification(True, msg, str(new_instanceargs[0]).decode('latin-1').encode("utf-8"), str(new_instanceargs[1]).decode('latin-1').encode("utf-8"))

	### NOTE: Editor :: Notification 			=> Notify something on the statusbar
	def Notification(self, modify, *args):
		""" Notify event in status bar
		"""
		self.nb.GetCurrentPage().modify = modify

		if hasattr(self, 'statusbar'):
			for i, s in enumerate(args):
				self.statusbar.SetStatusText(s, i)

	### NOTE: Editor :: StatusBar 			=> Create a status bar
	def GetStatusBar(self):
		""" Get the status bar
		"""
		sb = self.CreateStatusBar()
		sb.SetFieldsCount(3)
		sb.SetStatusWidths([-5, -3, -1])
		return sb

	### NOTE: Editor :: ToggleStatusBar 		=> Event for show or hide status bar
	def ToggleStatusBar(self, event):
		"""
		"""
		if self.statusbar.IsShown():
			self.statusbar.Hide()
		else:
			self.statusbar.Show()

	### NOTE: Editor :: OnChar 				=> Event when a char is typed
	def OnChar(self, event):
		"""
		"""

		### enable save icon in toolbar
		self.toolbar.EnableTool(self.save.GetId(), True)
		### status bar notification
		self.Notification(True, _('%s modified' % (os.path.basename(self.nb.GetCurrentPage().GetFilename()))), '', '')
		event.Skip()

	### NOTE: Editor :: OnOpenFile 			=> Event OnOpenFile
	def OnOpenFile(self, event):
		"""
		"""
		if self.nb.GetCurrentPage().isModified():
			dlg = wx.MessageDialog(self, _('Save changes?'), _('Code Editor'),
			                       wx.YES_NO | wx.YES_DEFAULT | wx.CANCEL | wx.ICON_QUESTION)
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

	### NOTE: Editor :: OnSaveFile			=> Event when save menu has been clicked
	def OnSaveFile(self, event):
		""" Save menu has been clicked.
		"""
		currentPage = self.nb.GetCurrentPage()

		if not self.read_only:

			assert currentPage.GetFilename() != ''

			### base and dir name of python file
			base_name = os.path.basename(currentPage.GetFilename())
			dir_name = os.path.dirname(currentPage.GetFilename())

			### code text
			code = currentPage.GetValue().encode('utf-8')
			code = '\n'.join(code.splitlines()) + '\n'

			new_instance = self.ConfigSaving(base_name, dir_name, code)

			### there is error in file ?
			currentPage.error_flag = isinstance(new_instance, Exception)

			self.CheckErrors(base_name, code, new_instance)

		else:
			### status bar notification
			self.Notification(False, _('%s not saved' % (currentPage.GetFilename())), _('file in readonly'))

	### NOTE: Editor :: QuitApplication 		=> Event on quit application
	def QuitApplication(self, event):
		"""
		"""
		# FIXME: Editor :: QuitApplication 		=> Corrupted file saving crash DEVSimPY

		cp = self.nb.GetCurrentPage()
		if cp.modify:
			### if no error
			if not cp.ContainError():
				dlg = wx.MessageDialog(self, _('Save before Exit?'), _('Code Editor'), wx.YES_NO | wx.YES_DEFAULT | wx.CANCEL | wx.ICON_QUESTION)
			else:
				dlg = wx.MessageDialog(self, _('File contain errors.\nDo you want to force saving before exit knowing that the file can be corrupts?'), _('Code Editor'), wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_QUESTION)
			val = dlg.ShowModal()
			if val == wx.ID_YES:
				self.nb.force_saving = cp.ContainError()
				self.OnSaveFile(event)
				self.nb.force_saving = False
				if not cp.modify:
					wx.Exit()
			elif val == wx.ID_CANCEL:
				dlg.Destroy()
			else:
				self.Destroy()
		else:
			self.Destroy()

	### NOTE: Editor :: OnAbout 				=> Event when about button is clicked
	def OnAbout(self, event):
		dial = wx.MessageDialog(self, _('\tPython Code Editor\t\n \tDEVSimPy \t\n'), _('About editor'), wx.OK | wx.ICON_INFORMATION)
		dial.ShowModal()

### ----------------------------------------------------------------
class EditorPanel(Base, wx.Panel):
	""" Editor class which is a Panel
	"""
	def __init__(self, parent, id, title):
		""" Constructor.
		"""
		
		self.parent = parent
		
		### call constructor and set background color of panel
		wx.Panel.__init__(self, self.parent, id)
		self.SetBackgroundColour(wx.WHITE)

		### Define sizer
		sizer = wx.BoxSizer(wx.VERTICAL)

		### create notebook
		self.nb = EditionNotebook(self, wx.ID_ANY, style=wx.CLIP_CHILDREN)
		### create juste for the bind of action (save,...) of the toolbar - Warning it must stay here !
		self.menuBar = self.CreateMenu()
		### create toolbar
		self.toolbar = self.CreateTB()
		###recover the statusbar of mainW
		self.statusbar = parent.GetStatusBar()

		### add toolbar and notebook
		sizer.Add(self.toolbar, 0, wx.ALL | wx.ALIGN_LEFT | wx.EXPAND)
		sizer.Add(self.nb, 1 ,wx.EXPAND)

		### set sizer and layout of panel
		self.SetSizer(sizer)
		self.SetAutoLayout(True)
	
		Base.__init__(self, parent, id, title)
		
###------------------------------------------------------------
class EditorFrame(Base, wx.Frame):
	""" Editor class which is a Frame
	"""

	### 
	def __init__(self, parent, id, title):
		""" Constructor.
		"""

		### copy
		self.parent = parent
		
		### call constructor
		wx.Frame.__init__(self, self.parent, id, title, size=(600, 500), style=wx.DEFAULT_FRAME_STYLE)

		### Create notebook
		self.nb = EditionNotebook(self, wx.ID_ANY, style=wx.CLIP_CHILDREN)

		### create menu, toolbar and statusbar for the frame
		self.menuBar = self.CreateMenu()
		self.SetMenuBar(self.menuBar)
		self.toolbar = self.CreateTB()
		self.statusbar= self.GetStatusBar()

		### binding
		self.Bind(wx.EVT_CLOSE, self.QuitApplication)

		self.Centre()

		### just for windows
		e = wx.SizeEvent(self.GetSize())
		self.ProcessEvent(e)

		Base.__init__(self, parent, id, title)

class BlockBase(object):
	### 
	def __init__(self, parent, id, title, block):
		""" Constructor
		"""
		
		self.cb = block

	###
	def OnInsertPeekPoke(self, event):
		""" Event when insert peek or insert poke button is clicked
		"""

		### selected submenu
		menubar = self.GetMenuBar()
		label = menubar.GetLabel(event.GetId())
		sins = None

		if "peek" in label:
			sins = map(str, range(self.cb.input if hasattr(self.cb, 'input') else 10))
		elif "poke" in label:
			sins = map(str, range(self.cb.output if hasattr(self.cb, 'output') else 10))
		else:
			sys.stdout.write(_("function not implemented"))

		if sins != []:
			dlg = wx.SingleChoiceDialog(self, _('Port number'), _(' %s on which port?')%label, sins, wx.CHOICEDLG_STYLE)
			if dlg.ShowModal() == wx.ID_OK:
				port = dlg.GetStringSelection()
			else:
				port = None
			dlg.Destroy()

			if port is not None:
				cp = self.nb.GetCurrentPage()
				if "peek" in label:
					cp.AddTextRaw("self.peek(self.IPorts[%d])" % int(port))
				elif "poke" in label:
					cp.AddTextRaw("return self.poke(self.OPorts[%d], Message(<>, self.timeNext))" % int(port))
				else:
					pass

				cp.modify = True

	def OnInsertGetPortId(self, event):
		""" Insert a sentence to get port ID
		"""
		cp = self.nb.GetCurrentPage()
		cp.AddTextRaw("id = self.getPortId(<port>)")
		cp.modify = True

	def OnInsertGetMsgValue(self, event):
		""" Insert a sentence to get the message value
		"""
		cp = self.nb.GetCurrentPage()
		cp.AddTextRaw("v = self.getMsgValue(<msg>)")
		cp.modify = True

	###
	def OnInsertHoldInState(self, event):
		""" Insert a sentence to change the state
		"""
		cp = self.nb.GetCurrentPage()
		cp.AddTextRaw("self.holdIn('<phase>',<sigma>)")
		cp.modify = True

	###
	def OnInsertPhaseIs(self, event):
		""" Insert a sentence to test the phase
		"""
		cp = self.nb.GetCurrentPage()
		cp.AddTextRaw("self.phaseIs('<phase>')")
		cp.modify = True
		
	###
	def OnInsertPassivateInState(self, event):
		""" Insert a sentence to change the state
		"""
		cp = self.nb.GetCurrentPage()
		cp.AddTextRaw("self.passivateIn('<phase>')")
		cp.modify = True

	###
	def OnInsertPassivateState(self, event):
		""" Insert a sentence to change the state
		"""
		cp = self.nb.GetCurrentPage()
		cp.AddTextRaw("self.passivate()")
		cp.modify = True

	###
	def OnInsertDebug(self, event):
		""" Insert a sentence to invoke the debugger function that trace message into the log of model
		"""
		cp = self.nb.GetCurrentPage()
		cp.AddTextRaw("self.debugger('<message>')")
		cp.modify = True

	###
	def ConfigSaving(self, base_name, dir_name, code):
		""" Saving method
		"""

		new_instance = None

		### if force saving when quitting Editor
		if self.nb.force_saving:
			self.nb.DoSaveFile(code)
		else:
			### get new instance from text loaded in Editor
			if not base_name.endswith('plugins.py'):
				new_instance = getObjectFromString(code)

			### typical plugins python file
			else:
				new_instance = isError(code) or None

		return new_instance

	###
	def UpdateArgs(self, new_args):
		""" Update the args or constructor class from new_args
		"""

		### update args (behavioral attributes) before saving
		if isinstance(new_args, dict):

			### add new attributes
			for key, val in new_args.items():
				if not self.cb.args.has_key(key):
					self.cb.args[key]=val

			### del old attributes
			for key, val in self.cb.args.items():
				if not new_args.has_key(key):
					del self.cb.args[key]

		else:
			### status bar notification
			self.Notification(False, _('args not updated'), _('New class from %s') % (new_class))

	###
	def CheckErrors(self, base_name, code, new_instance):
		"""
		"""

		if not self.nb.GetCurrentPage().ContainError():

			### if some simulation is running
			on_simulation_flag = True in map(lambda thread: _('Simulator') in thread.getName() and thread.isAlive(), threading.enumerate()[1:])

			new_class = new_instance.__class__

			if new_instance:
				import Components
				new_args = Components.GetArgs(new_class)
				self.UpdateArgs(new_args)

			### user would change the behavior during a simulation without saving
			if on_simulation_flag and new_instance is not bool:

				assert self.cb.getDEVSModel() is not None, _("Close Simulation Diag!")

				self.cb.setDEVSClassModel(new_class)

				if base_name.split('.')[1] == 'py':
					self.nb.DoSaveFile(code)
				else:
					### status bar notification
					self.Notification(False, _('File not saved during simulation'), _('New class from %s')%(new_class))
			### save file
			else:
				self.nb.DoSaveFile(code)

		### some errors in file
		else:
			self.SavingErrors(new_instance)

	###
	def UpdateModule(self):
		""" Reloading associated module and devs model.
		"""

		### re importation du module de la classe avec verification des erreurs éventuelles dans le code
		if hasattr(self.cb, 'model_path') and zipfile.is_zipfile(self.cb.model_path):
			module_name = self.cb.model_path
		# recuperation du module correspondant à la classe
		else:
			module_name = path_to_module(self.cb.python_path)

		info = ReloadModule.recompile(module_name)
		cp = self.nb.GetCurrentPage()
		cp.error_flag = isinstance(info, Exception) or isinstance(info, str)

		if cp.error_flag:
			wx.MessageBox(_('Error saving file:\n%s')%str(info), \
						"UpdateModule method", \
						wx.OK | wx.ICON_ERROR)
		else:
			import Components

			classe = Components.GetClass(cp.GetFilename())

			if not isinstance(classe, Exception):

				### for plugins.py file, i is not a class !
				if inspect.isclass(classe):

					# get behavioral attribute from python file through constructor class
					# args must have default value in the constructor
					constructor = inspect.getargspec(classe.__init__)
					new_args = dict(zip(constructor[0][1:], constructor[-1])) if constructor[-1] else {}
					self.UpdateArgs(new_args)

					# code update if it was modified during the simulation (out of constructor code,
					# because we don't re-instanciated the devs model but only change the class reference)
					devs = self.cb.getDEVSModel()
					if devs is not None:
						self.cb.setDEVSClassModel(classe)
						self.cb.setBlock(devs)
			else:
				wx.MessageBox(_('Error trying to give class: %s\n')%str(classe), \
							"GetClass Function", \
							wx.OK | wx.ICON_ERROR)

	###
	@classmethod
	def __str__(cls):
		"""
		"""
		attrs = [('cb', 'Block')]
		class_name = "BlockEditor"
		parent = "Editor"
		methods = [
			('__init__', 'self, parent, ID, title'),
			('ConfigureGUI', 'self'),
			('ConfigSaving', 'self, base_name, dir_name, code'),
			('CheckErrors', 'self, base_name, code, new_instance'),
			('UpdateModule', 'self'),
			('OnInsertPeekPoke', 'self, event'),
			('OnInsertHoldInState', 'self, event')
		]
		return "\n--------------------------------------------------\
		\n\tClass :\t\t%s\n\n\tInherit from :\t%s\n\n\tAttributes :\t%s\n\n\tMethods :\t%s\n" % (
			class_name, parent, '\n\t\t\t'.join([attr + "\t:: " + typ for attr, typ in attrs]),
			"\n\t\t\t".join([method + "\tparams :: " + params for method, params in methods])
		)

### CodeBlock editor with special submenu---------------------------
class BlockEditorFrame(BlockBase, EditorFrame):
	""" Block Editor class which inherit of Editor class
	"""

	### 
	def __init__(self, parent, id, title, block):
		""" Constructor
		"""

		EditorFrame.__init__(self, parent, id, title)
		BlockBase.__init__(self, parent, id, title, block)

		#if not parent:
		self.SetIcon(self.MakeIcon(wx.Image(os.path.join(ICON_PATH_16_16, 'pythonFile.png'), wx.BITMAP_TYPE_PNG)))
		self.ConfigureGUI()
		#else:
		#	### in panel
		#	self.ConfigureTB()

	###
	def ConfigureGUI(self):
		"""
		"""
		### insert sub menu-------------------------------------------------
		insert = wx.Menu()

		peek = wx.MenuItem(insert, wx.NewId(), _('New peek'), _('Generate new peek code'))
		poke = wx.MenuItem(insert, wx.NewId(), _('New poke'), _('Generate new poke code'))
		getPortId = wx.MenuItem(insert, wx.NewId(), _('Get Port Id'), _('Get the port ID from port instance self.getPortId(port)->int'))
		getMsgValue = wx.MenuItem(insert, wx.NewId(), _('Get message value'), _('Get message value self.getMsgValue(msg)->Object'))
		holdInState = wx.MenuItem(insert, wx.NewId(), _('New hold in state'), _('Generate new hold in state code self.holdIn(...)'))
		phaseIs = wx.MenuItem(insert, wx.NewId(), _('New phaseIs test'), _('Generate phase test code self.phaseIs(...)'))
		passivateInState = wx.MenuItem(insert, wx.NewId(), _('New passivate in state'), _('Generate new passivate in state code self.passivateIn(...)'))
		passivateState = wx.MenuItem(insert, wx.NewId(), _('New passivate state'), _('Generate new passivate state code self.passivate(...)'))
		debug = wx.MenuItem(insert, wx.NewId(), _('New debugger'), _('Generate new debugger code (print into the log of model)'))
		
		insert.AppendItem(peek)
		insert.AppendItem(poke)
		insert.AppendSeparator()
		insert.AppendItem(getPortId)
		insert.AppendItem(getMsgValue)
		insert.AppendSeparator()
		insert.AppendItem(holdInState)
		insert.AppendItem(phaseIs)
		insert.AppendItem(passivateInState)
		insert.AppendItem(passivateState)
		insert.AppendSeparator()
		insert.AppendItem(debug)

		menu = self.GetMenuBar().GetMenu(1)
		menu.PrependMenu(wx.NewId(), _("Insert"), insert)
		### -------------------------------------------------------------------

		### insert new icon in toolbar (icon are not available in embeded editor (Show menu)
		tb = self.GetToolBar()
		tb.InsertSeparator(tb.GetToolsCount())

		if wx.VERSION_STRING < '4.0':
			tb.AddTool(peek.GetId(), wx.Bitmap(os.path.join(ICON_PATH_16_16,'peek.png')), shortHelpString=_('New peek'), longHelpString=_('Insert a code for a new peek'))
			tb.AddTool(poke.GetId(), wx.Bitmap(os.path.join(ICON_PATH_16_16,'poke.png')), shortHelpString=_('New poke'), longHelpString=_('Insert a code for a new poke'))
			tb.AddTool(holdInState.GetId(), wx.Bitmap(os.path.join(ICON_PATH_16_16,'new_state.png')), shortHelpString=_('New hold in state'), longHelpString=_('Insert a code for a new hold in state'))
			tb.AddTool(passivateInState.GetId(), wx.Bitmap(os.path.join(ICON_PATH_16_16,'new_state.png')), shortHelpString=_('New passivate in state'), longHelpString=_('Insert a code for a new passivate in state'))
			tb.AddTool(passivateState.GetId(), wx.Bitmap(os.path.join(ICON_PATH_16_16,'new_state.png')), shortHelpString=_('New passivate state'), longHelpString=_('Insert a code for a new passivate state'))
			tb.AddTool(debug.GetId(), wx.Bitmap(os.path.join(ICON_PATH_16_16,'debugger.png')),shortHelpString=_('New debugger'), longHelpString=_('Insert a code for print information into the log of model'))
		else:
			tb.AddTool(peek.GetId(), "", wx.Bitmap(os.path.join(ICON_PATH_16_16,'peek.png')), shortHelp=_('New peek'))
			tb.AddTool(poke.GetId(), "", wx.Bitmap(os.path.join(ICON_PATH_16_16,'poke.png')), shortHelp=_('New poke'))
			tb.AddTool(holdInState.GetId(), "", wx.Bitmap(os.path.join(ICON_PATH_16_16,'new_state.png')), shortHelp=_('New hold in state'))
			tb.AddTool(passivateInState.GetId(), "", wx.Bitmap(os.path.join(ICON_PATH_16_16,'new_state.png')), shortHelp=_('New passivate in state'))
			tb.AddTool(passivateState.GetId(), "", wx.Bitmap(os.path.join(ICON_PATH_16_16,'new_state.png')), shortHelp=_('New passivate state'))
			tb.AddTool(debug.GetId(), "", wx.Bitmap(os.path.join(ICON_PATH_16_16,'debugger.png')),shortHelp=_('New debugger'))
		
		tb.Realize()

		self.Bind(wx.EVT_MENU, self.OnInsertPeekPoke, id=peek.GetId())
		self.Bind(wx.EVT_MENU, self.OnInsertPeekPoke, id=poke.GetId())
		self.Bind(wx.EVT_MENU, self.OnInsertGetPortId, id=getPortId.GetId())
		self.Bind(wx.EVT_MENU, self.OnInsertGetMsgValue, id=getMsgValue.GetId())
		self.Bind(wx.EVT_MENU, self.OnInsertHoldInState, id=holdInState.GetId())
		self.Bind(wx.EVT_MENU, self.OnInsertPhaseIs, id=phaseIs.GetId())
		self.Bind(wx.EVT_MENU, self.OnInsertPassivateInState, id=passivateInState.GetId())
		self.Bind(wx.EVT_MENU, self.OnInsertPassivateState, id=passivateState.GetId())
		self.Bind(wx.EVT_MENU, self.OnInsertDebug, id=debug.GetId())

class BlockEditorPanel(BlockBase, EditorPanel):
	""" Block Editor class which inherit of Editor class
	"""

	### 
	def __init__(self, parent, id, title, block):
		""" Constructor
		"""

		EditorPanel.__init__(self, parent, id, title)
		BlockBase.__init__(self, parent, id, title, block)

		#if not parent:
			#self.SetIcon(self.MakeIcon(wx.Image(os.path.join(ICON_PATH_16_16, 'pythonFile.png'), wx.BITMAP_TYPE_PNG)))
			#self.ConfigureGUI()
		#else:
		#	### in panel
		self.ConfigureTB()

	def ConfigureTB(self):
		"""
		"""
		id = [wx.NewId()]*4
		#tb = self.GetToolBar()
		self.toolbar.InsertSeparator(self.toolbar.GetToolsCount())

		if wx.VERSION_STRING < '4.0':
			self.toolbar.AddTool(id[0], wx.Bitmap(os.path.join(ICON_PATH_16_16,'peek.png')),shortHelpString=_('New peek'), longHelpString=_('Insert a code for a new peek'))
			self.toolbar.AddTool(id[1], wx.Bitmap(os.path.join(ICON_PATH_16_16,'poke.png')),shortHelpString=_('New poke'), longHelpString=_('Insert a code for a new poke'))
			self.toolbar.AddTool(id[2], wx.Bitmap(os.path.join(ICON_PATH_16_16,'new_state.png')),shortHelpString=_('New hold in state'), longHelpString=_('Insert a code for a new hold in state'))
			self.toolbar.AddTool(id[3], wx.Bitmap(os.path.join(ICON_PATH_16_16,'debugger.png')),shortHelpString=_('New debugger'), longHelpString=_('Insert a code for print information into the log of model'))
		else:
			self.toolbar.AddTool(id[0], "",wx.Bitmap(os.path.join(ICON_PATH_16_16,'peek.png')),shortHelp=_('New peek'))
			self.toolbar.AddTool(id[1], "",wx.Bitmap(os.path.join(ICON_PATH_16_16,'poke.png')),shortHelp=_('New poke'))
			self.toolbar.AddTool(id[2], "",wx.Bitmap(os.path.join(ICON_PATH_16_16,'new_state.png')),shortHelp=_('New hold in state'))
			self.toolbar.AddTool(id[3], "",wx.Bitmap(os.path.join(ICON_PATH_16_16,'debugger.png')),shortHelp=_('New debugger'))
		
		self.toolbar.Realize()

		self.Bind(wx.EVT_MENU, self.OnInsertPeekPoke, id=id[0])
		self.Bind(wx.EVT_MENU, self.OnInsertPeekPoke, id=id[1])
		self.Bind(wx.EVT_MENU, self.OnInsertHoldInState, id=id[2])
		self.Bind(wx.EVT_MENU, self.OnInsertDebug, id=id[3])

### factory function for BlockEditor
def BlockEditor(*args):
	parent = args[0]
	if not parent:
		return BlockEditorFrame(*args)
	else:
		return BlockEditorPanel(*args)
	
### Edition of any files with notebook------------------------------
# NOTE: TestEditor << Editor :: Specific editor for tests files
class TestEditor(EditorFrame):
	""" Test Editor class wich inherit of Editor class
	"""

	# NOTE: TestEditor :: contructor 		=> __init__(self, parent, id, title, feature_path, steps_path)
	def __init__(self, parent, id, title):
		"""Constructor.
		"""

		EditorFrame.__init__(self, parent, id, title)

		if not parent:
			self.SetIcon(self.MakeIcon(wx.Image(os.path.join(ICON_PATH, 'iconDEVSimPy.png'), wx.BITMAP_TYPE_PNG)))
			self.ConfigureGUI()

	# NOTE: TestEditor :: __str__		=> String representation of the class
	@classmethod
	def __str__(cls):
		"""
		"""
		attrs = []
		class_name = "TestEditor"
		parent = "Editor"
		methods = [
			('__init__', 'self, parent, id, title, feature_path, steps_path'),
			('ConfigureGUI', 'self'),
			('OnFeatureSkeleton', 'self, event'),
			('OnStepsSkeleton', 'self, event'),
			('OnHeaderGeneration', 'self, event')
		]
		return "\n--------------------------------------------------\
		\n\tClass :\t\t%s\n\n\tInherit from :\t%s\n\n\tAttributes :\t%s\n\n\tMethods :\t%s\n" % (
			class_name, parent, '\n\t\t\t'.join([attr + "\t:: " + typ for attr, typ in attrs]),
			"\n\t\t\t".join([method + "\tparams :: " + params for method, params in methods])
		)

	# NOTE: TestEditor :: ConfigureGUI 		=> Configure the interface for tests edition
	def ConfigureGUI(self):
		"""
		"""
		### insert sub menu-------------------------------------------------
		insert = wx.Menu()

		feature = wx.MenuItem(insert, wx.NewId(), _('Feature skeleton'), _('Generate feature skeleton'))
		steps = wx.MenuItem(insert, wx.NewId(), _('Steps skeleton'), _('Generate steps skeleton'))
		env_header = wx.MenuItem(insert, wx.NewId(), _('Environment header generation'), _('Generate environment header'))
		env_gen_def = wx.MenuItem(insert, wx.NewId(), _('Environment methods generation'), _('Generate minimal methods for environment'))
		# env_spec_def = wx.MenuItem(insert, wx.NewId(), _('Specific environment methods generation'), _('Generate minimal methods for specific environment'))

		insert.AppendItem(feature)
		insert.AppendItem(steps)
		insert.AppendItem(env_header)
		insert.AppendItem(env_gen_def)
		# insert.AppendItem(env_spec_def)

		menu = self.GetMenuBar().GetMenu(1)
		menu.PrependMenu(wx.NewId(), _("Insert"), insert)
		### ----------------------------------------------------------------

		### Bind all new event----------------------------------------------
		self.Bind(wx.EVT_MENU, self.OnFeatureSkeleton, id=feature.GetId())
		self.Bind(wx.EVT_MENU, self.OnStepsSkeleton, id=steps.GetId())
		self.Bind(wx.EVT_MENU, self.OnHeaderGeneration, id=env_header.GetId())
		self.Bind(wx.EVT_MENU, self.OnEnvDefGeneration, id=env_gen_def.GetId())
		# self.Bind(wx.EVT_MENU, self.OnSpecEnvDefGeneration, id=env_spec_def.GetId())

	### ----------------------------------------------------------------

	# NOTE: TestEditor :: OnFeatureSkeleton => Event when insert feature skeleton button is clicked
	def OnFeatureSkeleton(self, event):
		FEATURE_SKELETON = "Feature: # Feature description\n\tScenario: # Scenario description\n\t\tGiven # Context\n\t\tWhen # Event\n\t\tThen # Assertions"
		self.nb.GetCurrentPage().AddTextRaw(FEATURE_SKELETON)

	# NOTE: TestEditor :: OnStepsSkeleton 	=> Event when insert steps skeleton button is clicked
	def OnStepsSkeleton(self, event):
		STEP_FUNCTION = 'def step(context):\n\tpass\n'
		STEPS_SKELETON = "from behave import *\n\n@given('your given text')\n" + STEP_FUNCTION + "\n@when('your event text')\n" + STEP_FUNCTION + "\n@then('yout assertions text')\n" + STEP_FUNCTION
		self.nb.GetCurrentPage().AddTextRaw(STEPS_SKELETON)

	# NOTE: TestEditor :: OnHeaderGeneration		=> note
	def OnHeaderGeneration(self, event):
		HEADER = """
import os\nimport __builtin__\nimport sys\nimport pickle\nfrom tempfile import gettempdir\nABS_PATH = '%s'\nsys.path.append(ABS_PATH)
__builtin__.__dict__['HOME_PATH'] = ABS_PATH\n__builtin__.__dict__['DOMAIN_PATH'] = os.path.join(ABS_PATH, 'Domain')
__builtin__.__dict__['GUI_FLAG'] = True\n\nsys.path.append(os.path.join(gettempdir(), "AtomicDEVS"))\n\nmodels = {}
""" % HOME_PATH
		self.nb.GetCurrentPage().AddTextRaw(HEADER)

	# NOTE: TestEditor :: OnGenEnvDefGeneration		=> note
	def OnEnvDefGeneration(self, event):
		GEN_ENV_DEF = """import re\n
# NOTE: environment.py :: addModel		=> note
def loadModel():\n\tglobal models\n\tfiles = [os.path.join(gettempdir(), f) for f in os.listdir(gettempdir()) if re.match('^AtomicModel_.*\.{1}serial$', f)]\n\tfor f in files:\n\t\tm = pickle.load(open(f, "rb"))
\t\tif not m.blockModel.label in models.keys():\n\t\t\tmodels[m.blockModel.label] = m\n
def before_all(context):\n\tglobal models\n\tloadModel()\n\tcontext.models = models\n
"""
		self.nb.GetCurrentPage().AddTextRaw(GEN_ENV_DEF)

	# NOTE: TestEditor :: OnEnvironmentSkeleton		=> note
# 	def OnSpecEnvDefGeneration(self, event):
# 		SPEC_ENV_DEF = """
# # NOTE: environment.py :: addModel		=> note
# def loadModel():\n\tglobal models\n\tm = pickle.load(open(os.path.join(gettempdir(), "AtomicModel_'your_model_label'.serial"), "rb"))\n\tif not m.blockModel.label in models.keys():\n\t\tmodels[m.blockModel.label] = m\n
# \ndef before_all(context):\n\tglobal models\n\tloadModel()\n\tcontext.models = models\n
# """
# 		self.nb.GetCurrentPage().AddTextUTF8(SPEC_ENV_DEF)

### ----------------------------------------------------------------
### NOTE: GeneralEditor << Editor :: Editor for simple files like text files
class GeneralEditor(EditorFrame):
	""" General Editor class which inherit of Editor class
	"""

	### NOTE: GeneralEditor :: constructor 	=> __init__(self, parent, id, title)
	def __init__(self, parent, id, title):
		""" Constructor.
		"""

		### call constructor of parent
		EditorFrame.__init__(self, parent, id, title)

		### if not parent, we configure a frame
		if not parent:
			self.SetIcon(self.MakeIcon(wx.Image(os.path.join(ICON_PATH, 'iconDEVSimPy.png'), wx.BITMAP_TYPE_PNG)))
			self.ConfigureGUI()

	# NOTE: GeneralEditor :: __str__		=> String representation of the class
	@classmethod
	def __str__(cls):
		"""
		"""
		attrs = []
		class_name = "GeneralEditor"
		parent = "Editor"
		methods = [
			('__init__', 'self, parent, id, title'),
			('ConfigureGUI', 'self'),
			('OnAddPage', 'self, event'),
			('OnClosePage', 'self, event')
		]
		return "\n--------------------------------------------------\
		\n\tClass :\t\t%s\n\n\tInherit from :\t%s\n\n\tAttributes :\t%s\n\n\tMethods :\t%s\n" % (
			class_name, parent, '\n\t\t\t'.join([attr + "\t:: " + typ for attr, typ in attrs]),
			"\n\t\t\t".join([method + "\tparams :: " + params for method, params in methods])
		)

	### NOTE: GeneralEditor :: ConfigureGUI 	=> Configure the interface by default
	def ConfigureGUI(self):
		"""
		"""

		### AddPage button in toolbar---------------------------------------
		filemenu = self.GetMenuBar().GetMenu(0)
		add = wx.MenuItem(filemenu, wx.NewId(), _('&Add'), _('Add new page'))
		close = wx.MenuItem(filemenu, wx.NewId(), _('&Close'), _('Close current page'))
		### ----------------------------------------------------------------
		### Construct new toolbar-------------------------------------------
		self.toolbar.AddSeparator()
		### ----------------------------------------------------------------
		### Bind all new event----------------------------------------------
		self.Bind(wx.EVT_TOOL, self.OnAddPage, self.toolbar.AddSimpleTool(add.GetId(), wx.Bitmap(os.path.join(ICON_PATH, 'new.png')), _('Add'), ''))
		self.Bind(wx.EVT_TOOL, self.OnClosePage, self.toolbar.AddSimpleTool(close.GetId(), wx.Bitmap(os.path.join(ICON_PATH, 'close.png')), _('Close'), ''))
		### ----------------------------------------------------------------
		self.toolbar.Realize()

	### NOTE: GeneralEditor :: OnAddPage 		=> Event when Add page button is clicked
	def OnAddPage(self, event):
		""" Add page to the notebook
		"""

		self.nb.AddEditPage(_("New File"), '')

	### NOTE: GeneralEditor :: OnClosePage 	=> Event when close page button is clicked
	def OnClosePage(self, event):
		""" Close button has been invoked
		"""

		if self.nb.GetPageCount() > 1:

			id = self.nb.GetSelection()
			page = self.nb.GetPage(id)

			if page.IsModified():
				dlg = wx.MessageDialog(self, _('%s\nSave changes to the current diagram?')%(title), _('Save'), wx.YES_NO | wx.YES_DEFAULT | wx.CANCEL |wx.ICON_QUESTION)
				val = dlg.ShowModal()
				if val == wx.ID_YES:
					self.OnSaveFile(event)
				elif val == wx.ID_NO:
					self.nb.OnClosePage(event, id)
				else:
					dlg.Destroy()
					return False

				dlg.Destroy()

			else:
				self.nb.OnClosePage(event, id)

			return True

		else:
			return True

### -----------------------------------------------------------------------------------------------
class TestApp(wx.App):
	""" Testing application
	"""

	def OnInit(self):
		import gettext

		__builtin__.__dict__['HOME_PATH'] = os.getcwd()
		__builtin__.__dict__['ICON_PATH'] = os.path.join('icons')
		__builtin__.__dict__['ICON_PATH_16_16'] = os.path.join(ICON_PATH, '16x16')

		__builtin__.__dict__['_'] = gettext.gettext

		fn = os.path.join(gettempdir(), 'test.py')
		with open(fn, 'w') as f:
			f.write("Hello world !")

		frame1 = GetEditor(None, -1, 'Test1')
		frame1.AddEditPage("Hello world", fn)
		frame1.SetPosition((100, 100))
		frame1.Show()

		frame2 = GetEditor(None, -1, 'Test2', file_type='test')
		frame2.AddEditPage("Hello world", fn)
		frame2.AddEditPage("Hello world", fn)
		frame2.SetPosition((200, 200))
		frame2.Show()

		frame3 = GetEditor(None, -1, 'Test3', None, file_type='block')
		frame3.AddEditPage("Hello world", fn)
		frame3.SetPosition((300, 300))
		frame3.Show()

		return True

	def OnQuit(self, event):
		self.Close()


### -----------------------------------------------------------------------------------------------
def manager(args):
	os.system(['clear', 'cls'][os.name == 'nt'])
	if args.start:
		start()
	if args.info:
		info()


def info():
	sys.stdout.write(PythonSTC.__str__())
	sys.stdout.write(CodeEditor.__str__())
	sys.stdout.write(EditionFile.__str__())
	sys.stdout.write(EditionNotebook.__str__())
	sys.stdout.write(Editor.__str__())
	sys.stdout.write(BlockEditor.__str__())
	sys.stdout.write(TestEditor.__str__())
	sys.stdout.write(GeneralEditor.__str__())


def start():
	app = TestApp(0)
	app.MainLoop()


def main():
	parser = argparse.ArgumentParser(description='Text Editor for DEVSimPy')

	### Class info---------------------------------------------------------------------------------
	parser.add_argument('-c', '--class-info', action="store_true", dest="info", help='Show __str__ for each class')

	### Start App----------------------------------------------------------------------------------
	parser.add_argument('-s', '--start', action="store_true", dest="start", help='Start testing app')

	args = parser.parse_args()
	manager(args)


if __name__ == '__main__':
	import argparse

	main()