#!/usr/bin/env python
# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# LogFrame.py --- DEVSimPy - The Python DEVS GUI modeling and simulation software 
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

import wx


#------------------------------------------------------------------------
class LogFrame(wx.Frame):
	""" Log Frame class
	"""

	def __init__(self, parent, id, title, position, size):
		""" constructor
		"""

		wx.Frame.__init__(self, parent, id, title, position, size, style=wx.DEFAULT_FRAME_STYLE | wx.STAY_ON_TOP)
		self.Bind(wx.EVT_CLOSE, self.OnClose)


	def OnClose(self, event):
		"""	Handles the wx.EVT_CLOSE event
		"""
		self.Show(False)
			
