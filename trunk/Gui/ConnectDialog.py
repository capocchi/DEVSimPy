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

###
class ConnectDialog(wx.Frame):
	def __init__(self, parent, id, title, sn="Source", snL=[None,None], tn="Target", tnL=[None,None]):
		wx.Frame.__init__(self, parent, id, title, size=(240,200))

		# local copy
		self.sn=sn
		self.tn=tn
		self.parent = parent

		self.result=[0,0]

		L1=[]
		for i in range(len(snL)):
			if snL[i].__class__.__name__ == "INode":
				L1.append('iPort %d'%i)
			else:
				L1.append('oPort %d'%i)

		L2=[]
		for i in range(len(tnL)):
			if tnL[i].__class__.__name__ == 'INode':
				L2.append('iPort %d'%i)
			else:
				L2.append('oPort %d'%i)

		L1.append("%s"%_('All'))
		L2.append("%s"%_('All'))

		self.label_source = wx.StaticText(self, -1, '%s:'%self.sn)
		self.label_target = wx.StaticText(self, -1, '%s:'%self.tn)
		self.combo_box_sn = wx.ComboBox(self, -1, choices=L1, style=wx.CB_DROPDOWN|wx.CB_READONLY|wx.CB_SORT)
		self.combo_box_tn = wx.ComboBox(self, -1, choices=L2, style=wx.CB_DROPDOWN|wx.CB_READONLY|wx.CB_SORT)
		self.button_disconnect = wx.Button(self, -1, _("Disconnect"))
		self.button_connect = wx.Button(self, -1, _("Connect"))

		self.combo_box_sn.SetSelection(0)
		self.combo_box_tn.SetSelection(0)
		self.combo_box_sn.Enable(len(L1) != 2)
		self.combo_box_tn.Enable(len(L2) != 2)

		self.__set_properties()
		self.__do_layout()
		self.__set_events()

	def __set_properties(self):
		_icon = wx.EmptyIcon()
		_icon.CopyFromBitmap(wx.Bitmap(os.path.join(ICON_PATH_20_20, "connect.png"), wx.BITMAP_TYPE_ANY))
		self.SetIcon(_icon)

	def __do_layout(self):
		grid_sizer_1 = wx.GridSizer(3, 2, 0, 0)
		grid_sizer_1.Add(self.label_source, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
		grid_sizer_1.Add(self.label_target, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
		grid_sizer_1.Add(self.combo_box_sn, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		grid_sizer_1.Add(self.combo_box_tn, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		grid_sizer_1.Add(self.button_disconnect, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		grid_sizer_1.Add(self.button_connect, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		self.SetSizer(grid_sizer_1)
		grid_sizer_1.Fit(self)
		self.Layout()
		self.Center()

	def __set_events(self):
		self.Bind(wx.EVT_COMBOBOX, self.EvtComboBox1, self.combo_box_sn)
		self.Bind(wx.EVT_COMBOBOX, self.EvtComboBox2, self.combo_box_tn)

	def EvtComboBox1(self,event):
		self.result[0]=event.GetSelection()
	
	def EvtComboBox2(self,event):
		self.result[1]=event.GetSelection()
	
#class MyApp(wx.App):
	#def OnInit(self):
		#frame = ConnectDialog(None, -1, '')
		#frame.Show(True)
		#self.SetTopWindow(frame)
		#return True

#if __name__ == '__main__':
	#app = MyApp(0)
	#app.MainLoop()