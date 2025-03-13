# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# ConnectDialog.py ---
#                     --------------------------------
#                        Copyright (c) 2020
#                       Laurent CAPOCCHI
#                      University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 03/15/2020
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

_ = wx.GetTranslation

from Utilities import load_and_resize_image

def function(obj, i):
	return 'iPort %d'%i if obj[i].__class__.__name__ == "INode" else 'oPort %d'%i

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# CLASSES DEFINITION
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

###
class ConnectDialog(wx.Frame):
	def __init__(self, parent, id, title, sn="Source", snL=[None,None], tn="Target", tnL=[None,None]):
		wx.Frame.__init__(self, parent, id, title, size=(240,200), style= wx.CAPTION | wx.CLOSE_BOX | wx.SYSTEM_MENU)

		# local copy
		self.sn = sn
		self.tn = tn
		self.parent = parent

		self._result = [0,0]

		L1 = [function(snL,i) for i in range(len(snL))]
		L2 = [function(tnL,i) for i in range(len(tnL))]

		L1.insert(0,"%s"%_('All'))
		L2.insert(0,"%s"%_('All'))

		self._label_source = wx.StaticText(self, wx.NewIdRef(), '%s'%self.sn)
		self._label_target = wx.StaticText(self, wx.NewIdRef(), '%s'%self.tn)
		self._combo_box_sn = wx.ComboBox(self, wx.NewIdRef(), choices = L1, style = wx.CB_DROPDOWN|wx.CB_READONLY)
		self._combo_box_tn = wx.ComboBox(self, wx.NewIdRef(), choices = L2, style = wx.CB_DROPDOWN|wx.CB_READONLY)
		self._button_disconnect = wx.Button(self, wx.NewIdRef(), _("Disconnect"))
		self._button_connect = wx.Button(self, wx.NewIdRef(), _("Connect"))

		self._combo_box_sn.SetSelection(0)
		self._combo_box_tn.SetSelection(0)
		self._combo_box_sn.Enable(len(L1) != 2)
		self._combo_box_tn.Enable(len(L2) != 2)

		self.__set_properties()
		self.__do_layout()
		self.__set_events()

	def __set_properties(self):
		icon = wx.Icon()
		icon.CopyFromBitmap(load_and_resize_image("direct_connector.png"))
		self.SetIcon(icon)

	def __do_layout(self):
		grid_sizer_1 = wx.GridSizer(3, 2, 0, 0)
		grid_sizer_1.Add(self._label_source, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
		grid_sizer_1.Add(self._label_target, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
		grid_sizer_1.Add(self._combo_box_sn, 0, wx.EXPAND)
		grid_sizer_1.Add(self._combo_box_tn, 0, wx.EXPAND)
		grid_sizer_1.Add(self._button_disconnect, 0, wx.EXPAND)
		grid_sizer_1.Add(self._button_connect, 0, wx.EXPAND)
		self.SetSizer(grid_sizer_1)
		grid_sizer_1.Fit(self)
		self.Layout()
		self.Center()

	def __set_events(self):
		self.Bind(wx.EVT_COMBOBOX, self.EvtComboBox1, self._combo_box_sn)
		self.Bind(wx.EVT_COMBOBOX, self.EvtComboBox2, self._combo_box_tn)

	def EvtComboBox1(self,event):
		self._result[0] = event.GetSelection()

	def EvtComboBox2(self,event):
		self._result[1] = event.GetSelection()

	def GetSelectedIndex(self):
		return self._result

	def GetLabelSource(self):
		return self._label_source.GetLabel()

	def GetLabelTarget(self):
		return self._label_target.GetLabel()