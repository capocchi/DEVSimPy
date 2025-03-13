# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# FindGUI.py ---
#                    --------------------------------
#                            Copyright (c) 2020
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 03/22/20
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
import re

_ = wx.GetTranslation

class FindReplace(wx.Dialog):
	def __init__(self, parent, id, title):
		
		wx.Dialog.__init__(self, parent, id, title, size=(255, 365))

		panel = wx.Panel(self)

		vbox_top = wx.BoxSizer(wx.VERTICAL)
		vbox = wx.BoxSizer(wx.VERTICAL)

		# panel1
		panel1 = wx.Panel(panel)
		grid1 = wx.GridSizer(2, 2, 0, 0)
		self.input_find = wx.ComboBox(panel1, -1, size=(120, -1))
		self.input_replace = wx.ComboBox(panel1, -1, size=(120, -1))
		grid1.Add(wx.StaticText(panel1, -1, _('Find: '),(5, 5)), 0,  wx.ALIGN_CENTER_VERTICAL)
		grid1.Add(self.input_find)
		grid1.Add(wx.StaticText(panel1, -1, _('Replace with: '), (5, 5)), 0, wx.ALIGN_CENTER_VERTICAL)
		grid1.Add(self.input_replace)

		panel1.SetSizer(grid1)
		vbox.Add(panel1, 0, wx.BOTTOM | wx.TOP, 9)

		# panel2
		panel2 = wx.Panel(panel)
		hbox2 = wx.BoxSizer(wx.HORIZONTAL)
		sizer21 = wx.StaticBoxSizer(wx.StaticBox(panel2, -1, _('Direction')), orient=wx.VERTICAL)
		sizer21.Add(wx.RadioButton(panel2, -1, _('Forward'), style=wx.RB_GROUP))
		sizer21.Add(wx.RadioButton(panel2, -1, _('Backward')))
		hbox2.Add(sizer21, 1, wx.RIGHT, 5)

		sizer22 = wx.StaticBoxSizer(wx.StaticBox(panel2, -1, _('Scope')), orient=wx.VERTICAL)
		# we must define wx.RB_GROUP style, otherwise all 4 RadioButtons would be mutually exclusive
		sizer22.Add(wx.RadioButton(panel2, -1, _('All'), style=wx.RB_GROUP))
		sizer22.Add(wx.RadioButton(panel2, -1, _('Selected Lines')))
		hbox2.Add(sizer22, 1)

		panel2.SetSizer(hbox2)
		vbox.Add(panel2, 0, wx.BOTTOM, 9)

		# panel3
		panel3 = wx.Panel(panel, -1)
		sizer3 = wx.StaticBoxSizer(wx.StaticBox(panel3, -1, _('Options')), orient=wx.VERTICAL)
		vbox3 = wx.BoxSizer(wx.VERTICAL)
		grid = wx.GridSizer(3, 2, 0, 5)
		grid.Add(wx.CheckBox(panel3, -1, _('Case Sensitive')))
		grid.Add(wx.CheckBox(panel3, -1, _('Wrap Search')))
		grid.Add(wx.CheckBox(panel3, -1, _('Whole Word')))
		grid.Add(wx.CheckBox(panel3, -1, _('Incremental')))
		vbox3.Add(grid)
		vbox3.Add(wx.CheckBox(panel3, -1, _('Regular expressions')))
		sizer3.Add(vbox3, 0, wx.TOP, 4)

		panel3.SetSizer(sizer3)
		vbox.Add(panel3, 0, wx.BOTTOM, 15)

		# panel4

		panel4 = wx.Panel(panel)
		sizer4 = wx.GridSizer(2, 2, 2, 2)
		find_btn = wx.Button(panel4, -1,_('Find'), size=(120, -1))
		replace_find_btn = wx.Button(panel4, -1, _('Replace/Find'), size=(120, -1))
		replace_btn = wx.Button(panel4, -1, _('Replace'), size=(120, -1))
		replace_all_btn = wx.Button(panel4, -1, _('Replace All'), size=(120, -1))
		
		sizer4.Add(find_btn)
		sizer4.Add(replace_find_btn)
		sizer4.Add(replace_btn)
		sizer4.Add(replace_all_btn)

		panel4.SetSizer(sizer4)
		vbox.Add(panel4, 0, wx.BOTTOM, 9)

		# panel5
		panel5 = wx.Panel(panel)
		sizer5 = wx.BoxSizer(wx.HORIZONTAL)
		sizer5.Add((191, -1), 1, wx.EXPAND)
		close_btn = wx.Button(panel5, -1, _('Close'), size=(50, -1))
		sizer5.Add(close_btn)

		panel5.SetSizer(sizer5)
		vbox.Add(panel5, 1, wx.BOTTOM, 9)

		vbox_top.Add(vbox, 1, wx.LEFT, 5)
		panel.SetSizer(vbox_top)

		self.Bind(wx.EVT_BUTTON, self.OnClose, id=close_btn.GetId())
		self.Bind(wx.EVT_BUTTON, self.OnFind, id=find_btn.GetId())
		self.Bind(wx.EVT_TEXT, self.OnInput, id=self.input_find.GetId())
		self.Bind(wx.EVT_CLOSE, self.OnClose)
		
		self.Centre()
		
		### for Windows users, put self.SetClientSize(panel.GetBestSize()) line before the ShowModal() method. (http://zetcode.com/wxpython/layout/)
		self.SetClientSize(panel.GetBestSize())
		
		if parent:
			self.ShowModal()
		
	def OnClose(self, evt):
		""" Close button has been pressed
		"""
		self.Destroy()
		evt.Skip()
		
	def OnInput(self, evt):
		""" Init the iterator for the research
		"""
		txtCtrl = self.GetParent().txt.GetValue()
		input_find = self.input_find.GetValue()
		
		self.v = re.finditer(input_find, txtCtrl)
		
	def OnFind(self, evt):
		""" Highlight the pos in txt from finding text
		"""
		try:
			pos = self.v.next().start()
			txt = self.GetParent().txt
			txt.SetSelection(pos,pos+len(self.input_find.GetValue()))
		except StopIteration:
			pass