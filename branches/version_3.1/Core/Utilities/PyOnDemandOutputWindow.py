#!/usr/bin/env python
# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# PyOnDemandOutputWindow.py --- DEVSimPy - The Python DEVS GUI modeling and simulation software
#                     --------------------------------
#                            Copyright (c) 2013
#                              Laurent CAPOCCHI
#                        SPE - University of Corsica
#                     --------------------------------
# Version 3.1                                      last modified:  08/01/13
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GLOBAL VARIABLES AND FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import threading

import wx

import GUI.LogFrame as LogFrame


#------------------------------------------------------------------------------
class PyOnDemandOutputWindow(threading.Thread):
	"""
	A class that can be used for redirecting Python's stdout and
	stderr streams.  It will do nothing until something is wrriten to
	the stream at which point it will create a Frame with a text area
	and write the text there.
	"""

	def __init__(self, title="wxPython: stdout/stderr"):
		threading.Thread.__init__(self)
		self.frame = None
		self.title = title
		self.pos = wx.DefaultPosition
		self.size = (450, 300)
		self.parent = None
		self.st = None

	def SetParent(self, parent):
		"""Set the window to be used as the popup Frame's parent."""
		self.parent = parent

	def CreateOutputWindow(self, st):
		self.st = st
		self.start()

	#self.frame.Show(True)

	def run(self):
		self.frame = LogFrame.LogFrame(self.parent, wx.ID_ANY, self.title, self.pos, self.size)
		self.text = wx.TextCtrl(self.frame, wx.ID_ANY, "", style=wx.TE_MULTILINE | wx.HSCROLL)
		self.text.AppendText(self.st)

	# These methods provide the file-like output behaviour.
	def write(self, text):
		"""
		If not called in the context of the gui thread then uses
		CallAfter to do the work there.
		"""
		if self.frame is None:
			if not wx.Thread_IsMain():
				wx.CallAfter(self.CreateOutputWindow, text)
			else:
				self.CreateOutputWindow(text)
		else:
			if not wx.Thread_IsMain():
				wx.CallAfter(self.text.AppendText, text)
			else:
				self.text.AppendText(text)

	def close(self):
		if self.frame is not None:
			wx.CallAfter(self.frame.Close)

	def flush(self):
		pass

