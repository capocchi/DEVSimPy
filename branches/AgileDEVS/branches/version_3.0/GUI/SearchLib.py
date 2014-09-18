#!/usr/bin/env python
# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# main.py --- DEVSimPy - The Python DEVS GUI modeling and simulation software 
#                     --------------------------------
#                            Copyright (c) 2013
#                              Laurent CAPOCCHI
#                        SPE - University of Corsica
#                     --------------------------------
# Version 3.0                                      last modified:  08/01/13
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

#-----------------------------------------------------------------------
class SearchLib(wx.SearchCtrl):
	"""
	"""

	def __init__(self, *args, **kwargs):
		"""
		"""
		wx.SearchCtrl.__init__(self, *args, **kwargs)

		self.treeChildren = []
		self.treeCopy = None
		self.ShowCancelButton(True)
		self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancel)
		self.Bind(wx.EVT_TEXT, self.OnSearch)

		self.SetToolTipString(_("Find model in the library depending its name."))

	def OnCancel(self, evt):
		"""
		"""
		self.Clear()

	def OnSearch(self, evt):
		"""
		"""
		mainW = evt.GetEventObject().GetTopLevelParent()
		mainW.OnSearch(evt)

