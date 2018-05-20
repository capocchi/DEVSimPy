# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# ConnectDialog.py ---
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

def function(obj, i):
	return 'iPort %d'%i if obj[i].__class__.__name__ == "INode" else 'oPort %d'%i

###
class ConnectDialog(wx.Frame):
	def __init__(self, parent, id, title, sn="Source", snL=[None,None], tn="Target", tnL=[None,None]):
		wx.Frame.__init__(self, parent, id, title, size=(240,200), style= wx.CAPTION | wx.CLOSE_BOX | wx.STAY_ON_TOP| wx.SYSTEM_MENU)

		# local copy
		self.sn = sn
		self.tn = tn
		self.parent = parent

		self._result = [0,0]

		L1 = map(lambda i:function(snL,i),range(len(snL)-1))
		L2 = map(lambda i:function(tnL,i),range(len(tnL)-1))

		L1.append("%s"%_('All'))
		L2.append("%s"%_('All'))

		self._label_source = wx.StaticText(self, wx.ID_ANY, '%s:'%self.sn)
		self._label_target = wx.StaticText(self, wx.ID_ANY, '%s:'%self.tn)
		self._combo_box_sn = wx.ComboBox(self, wx.ID_ANY, choices = L1, style = wx.CB_DROPDOWN|wx.CB_READONLY|wx.CB_SORT)
		self._combo_box_tn = wx.ComboBox(self, wx.ID_ANY, choices = L2, style = wx.CB_DROPDOWN|wx.CB_READONLY|wx.CB_SORT)
		self._button_disconnect = wx.Button(self, wx.ID_ANY, _("Disconnect"))
		self._button_connect = wx.Button(self, wx.ID_ANY, _("Connect"))

		self._combo_box_sn.SetSelection(0)
		self._combo_box_tn.SetSelection(0)
		self._combo_box_sn.Enable(len(L1) != 2)
		self._combo_box_tn.Enable(len(L2) != 2)

		self.__set_properties()
		self.__do_layout()
		self.__set_events()

	def __set_properties(self):
		icon = wx.EmptyIcon() if wx.VERSION_STRING < '4.0' else wx.Icon()
		icon.CopyFromBitmap(wx.Bitmap(os.path.join(ICON_PATH_16_16, "connect.png"), wx.BITMAP_TYPE_ANY))
		self.SetIcon(icon)

	def __do_layout(self):
		grid_sizer_1 = wx.GridSizer(3, 2, 0, 0)
		grid_sizer_1.Add(self._label_source, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
		grid_sizer_1.Add(self._label_target, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
		grid_sizer_1.Add(self._combo_box_sn, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		grid_sizer_1.Add(self._combo_box_tn, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		grid_sizer_1.Add(self._button_disconnect, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		grid_sizer_1.Add(self._button_connect, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
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

### ------------------------------------------------------------
class TestApp(wx.App):
	""" Testing application
	"""

	def OnInit(self):

		import gettext
		import __builtin__

		__builtin__.__dict__['ICON_PATH']='icons'
		__builtin__.__dict__['ICON_PATH_16_16']=os.path.join(ICON_PATH,'16x16')
		__builtin__.__dict__['_'] = gettext.gettext

		self.frame = ConnectDialog(None, -1, 'Connect Manager')
		self.frame.Show()
		return True

	def OnQuit(self, event):
		self.Close()

if __name__ == '__main__':

	app = TestApp(0)
	app.MainLoop()