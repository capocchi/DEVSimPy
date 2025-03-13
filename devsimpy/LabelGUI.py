# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# LabelGUI.py ---
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

import os
import wx
from wx import xrc

### avoid cyclic import during the test_labelgui.py execution
import sys
if 'LabelGUI' not in sys.modules:
	from AttributeEditor import AttributeBase

__res = None

RESFILE = os.path.join(DEVSIMPY_PACKAGE_PATH,'XRC','LabelEditorDialog.xrc')

def __init_resources():
	global __res
	__res = xrc.EmptyXmlResource() 
	#home = os.path.abspath(os.path.dirname(sys.argv[0]))
	__res.Load(RESFILE)
	
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

		wx.Dialog.__init__(self)
		
		### local copy
		self.block = block
		self.parent = parent
		
		_xrcName = "LabelEditorFrame"
		
		### with Phoenix, no need to pre definde the dialogue windows.
		### https://wxpython.org/Phoenix/docs/html/MigrationGuide.html?highlight=postcreate
		### no need to ues the self.Create methode because LoadDialog already does what's necessary.
		# XML Resources can be loaded from a file like this:
		res = xrc.XmlResource(RESFILE)		
		# Now create a panel from the resource data
		res.LoadDialog(self, parent, _xrcName)
			
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
			
			### update the radio button position depending on the model position label
			self.m_radioBtn1.SetValue(self.old_pos == 'center')
			self.m_radioBtn2.SetValue(self.old_pos == 'top')
			self.m_radioBtn3.SetValue(self.old_pos == 'bottom')

	def SetCanvas(self, canvas):
		"""
		"""
		self.canvas = canvas

	def OnTextChange(self, evt):
		""" Text in CtrlText change
			dynamic update of label during edition
		"""
		txt = self.label_txtCtrl.GetValue()
		if hasattr(self, 'canvas') and txt != "" and self.block:
			self.block.label=txt

			### update of block from canvas
			self.canvas.UpdateShapes([self.block])
			if isinstance(self.parent, AttributeBase):
				### update of label filed in properties dialogue
				self.parent._list.SetCellValue(0, 1, self.block.label)

		evt.Skip()

	def OnButton(self, event):
		""" Radio button has been clicked
		"""
		btn = event.GetEventObject()
		label = btn.GetLabel()

		if self.block:
			### label of radio button and the value of a label_pos attribute are similar ;-)
			self.block.label_pos = label

			### update of block from canvas
			self.canvas.UpdateShapes([self.block])
			if isinstance(self.parent, AttributeBase):
				### update of label_pos filed in properties dialogue
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
		""" Cancel button has been clicked
		"""
		if self.block:
			self.block.label = self.old_label
			self.block.label_pos = self.old_pos

			### update of block from canvas
			self.canvas.UpdateShapes([self.block])

		self.Destroy()

