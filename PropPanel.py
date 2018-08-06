# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# PropPanel.py ---
#                     --------------------------------
#                        Copyright (c) 2013
#                       Laurent CAPOCCHI
#                      University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 27/02/2014
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

import gettext
_ = gettext.gettext

class PropPanel(wx.Panel):
	"""
	"""
	def __init__(self, parent, name):
		wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY, name=name)

		self.frame = parent
		
		propSizer = wx.BoxSizer(wx.VERTICAL)
		propSizer.Add(self.defaultPropertiesPage(), 1, wx.EXPAND|wx.ALL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTRE_VERTICAL, 10)

		self.SetAutoLayout(True)
		self.SetSizerAndFit(propSizer)
		self.Layout()
		self.SetBackgroundColour(wx.WHITE)

		self.__set_tips()

	def defaultPropertiesPage(self):
		"""
		"""

		propContent = wx.StaticText(self, wx.ID_ANY, _("Select a model from diagram \n to see their properties."))
		sum_font = propContent.GetFont()
		sum_font.SetWeight(wx.BOLD)
		propContent.SetFont(sum_font)

		return propContent

	def UpdatePropertiesPage(self, panel=None):
		"""	Update the propPanel with the new panel parameter of the model.
		"""
		sizer = self.GetSizer()
		
		if wx.VERSION_STRING < '4.0':
			sizer.DeleteWindows()
		else:
			sizer.Clear(True)
		 
		sizer.Add(panel, 1, wx.EXPAND|wx.ALL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTRE_VERTICAL, 10)
		
		self.SetSizerAndFit(sizer)
		self.Layout()

		if wx.VERSION_STRING > '4.0':
			self.frame.Layout()

	def __set_tips(self):
		"""
		"""

		self.propToolTip =[_("No model selected.\nChoose a model to show in this panel its properties."),_("You can change the properties by editing the cell.")]
		if wx.VERSION_STRING < '4.0':
			self.SetToolTipString(self.propToolTip[0])
		else:
			self.SetToolTip(self.propToolTip[0])