# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# PropPanel.py ---
#                     --------------------------------
#                        Copyright (c) 2013
#                       Laurent CAPOCCHI
#                      University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 10/11/2013
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

class PropPanel(wx.Panel):
	"""
	"""
	def __init__(self, parent, name):
		wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY, name=name)

		propSizer = wx.BoxSizer(wx.VERTICAL)
		propSizer.Add(self.defaultPropertiesPage(), 1, wx.EXPAND|wx.ALL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTRE_VERTICAL, 10)

		self.SetSizer(propSizer)
		self.Layout()

		self.SetBackgroundColour(wx.WHITE)

		self.__set_tips()

	def defaultPropertiesPage(self):
		"""
		"""

		propContent = wx.StaticText(self, wx.ID_ANY, _("Select a model from diagram \n to see their properties"))
		sum_font = propContent.GetFont()
		sum_font.SetWeight(wx.BOLD)
		propContent.SetFont(sum_font)

		return propContent

	def UpdatePropertiesPage(self, panel=None):
		"""	Update the propPanel with teh new panel param of the model
		"""
		sizer = self.GetSizer()
		sizer.DeleteWindows()
		sizer.Add(panel, 0, wx.EXPAND|wx.ALL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTRE_VERTICAL, 10)
		sizer.Layout()

	def __set_tips(self):
		"""
		"""

		self.propToolTip =[_("No model selected.\nChoose a model to show in this panel its properties"),_("You can change the properties by editing the cellule")]
		self.SetToolTipString(self.propToolTip[0])