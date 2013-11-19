# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# LabelGUI.py ---
#                     --------------------------------
#                        Copyright (c) 2013
#                       Laurent CAPOCCHI
#                      University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 16/04/13
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

import sys
import os
import wx
from wx import xrc

from AttributeEditor import AttributeEditor

__res = None

def __init_resources():
	global __res
	__res = xrc.EmptyXmlResource()
	__res.Load(os.path.join('XRC','LabelEditorDialog.xrc'))

def get_resources():
    """ This function provides access to the XML resources in this module."""
    global __res
    if __res == None:
        __init_resources()
    return __res

class LabelDialog(wx.Dialog):
	"""
	"""

	def PreCreate(self, pre):
		""" This function is called during the class's initialization.

		Override it for custom setup before the window is created usually to
		set additional window styles using SetWindowStyle() and SetExtraStyle().
		"""
		pass

	def __init__(self, parent, block=None):
		""" Constructor.
		"""

		### local copy
		self.block = block
		self.parent = parent

		self.canvas = self.parent.canvas

		_xrcName = "LabelEditorFrame"
		pre = wx.PreDialog()
		self.PreCreate(pre)
		get_resources().LoadOnDialog(pre, parent, _xrcName)
		self.PostCreate(pre)

		self.XrcResourceLoadAll()
		self.EventBinding()
		self.SetProperties()

	def EventBinding(self):
		""" Event Binding
		"""
		self.ok_btn.Bind(wx.EVT_BUTTON, self.OnOk)
		self.cancel_btn.Bind(wx.EVT_BUTTON, self.OnCancel)
		self.m_radioBtn1.Bind(wx.EVT_RADIOBUTTON, self.OnButton)
		self.m_radioBtn2.Bind(wx.EVT_RADIOBUTTON, self.OnButton)
		self.m_radioBtn3.Bind(wx.EVT_RADIOBUTTON, self.OnButton)
		self.label_txtCtrl.Bind(wx.EVT_TEXT, self.OnTextChange)

	def XrcResourceLoadAll(self):
		"""Loading Resource from XRC file
		"""
		self.ok_btn = xrc.XRCCTRL(self, 'ok_btn')
		self.cancel_btn = xrc.XRCCTRL(self, 'cancel_btn')
		self.label_txtCtrl = xrc.XRCCTRL(self, 'label_txtCtrl')
		self.m_radioBtn1 = xrc.XRCCTRL(self, 'm_radioBtn1')
		self.m_radioBtn2 = xrc.XRCCTRL(self, 'm_radioBtn2')
		self.m_radioBtn3 = xrc.XRCCTRL(self, 'm_radioBtn3')

	def SetProperties(self):
		"""
		"""

		### default label
		txt = self.block.label if self.block else ""
		self.label_txtCtrl.SetValue(txt)

		if txt != "":
			self.old_label = txt
			self.old_pos = self.block.label_pos

	def OnTextChange(self, evt):
		""" Text in CtrlText change
			dynamic update of label during edition
		"""
		txt = self.label_txtCtrl.GetValue()
		if txt != "" and self.block:
			self.block.label=txt

			### update of block from canvas
			self.canvas.UpdateShapes([self.block])
			if isinstance(self.parent, AttributeEditor):
				### update of label filed in propertie dialogue
				self.parent._list.SetCellValue(0, 1, self.block.label)

		evt.Skip()

	def OnButton(self, event):
		""" Radio button has been clicked
		"""
		btn = event.GetEventObject()
		label = btn.GetLabel()

		if self.block:
			### label of radio button and the vlaue of a label_pos attribut are similar ;-)
			self.block.label_pos = label

			### update of block from canvas
			self.canvas.UpdateShapes([self.block])
			if isinstance(self.parent, AttributeEditor):
				### update of label_pos filed in propertie dialogue
				self.parent._list.SetCellValue(1, 1, self.block.label_pos)

	def OnOk(self, evt):
		""" Ok button has been clicked
		"""
		if self.block:
			new_val = self.label_txtCtrl.GetValue()

			if new_val != "":
				self.block.label = new_val

			if self.m_radioBtn1.GetValue():
				self.block.label_pos = 'center'
			elif self.m_radioBtn2.GetValue():
				self.block.label_pos = 'top'
			else:
				self.block.label_pos = 'bottom'

			### update of block from canvas
			self.canvas.UpdateShapes([self.block])

		self.Close()

	def OnCancel(self, evt):
		""" Cancle button has been clicked
		"""
		if self.block:
			self.block.label = self.old_label
			self.block.label_pos = self.old_pos

			### update of block from canvas
			self.canvas.UpdateShapes([self.block])

		self.Destroy()

### ------------------------------------------------------------
class TestApp(wx.App):
	""" Testing application
	"""

	def OnInit(self):

		import gettext

		dia = LabelDialog(None, None)
		if dia.ShowModal() == wx.ID_CANCEL:
			dia.Destroy()
		else:
			dia.Destroy()

		return True

	def OnQuit(self, event):
		self.Close()

if __name__ == '__main__':

	app = TestApp(0)
	app.MainLoop()