# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# AttributeEditor.py ---
#                     --------------------------------
#                        Copyright (c) 2013
#                       Laurent CAPOCCHI
#                      University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 19/11/13
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
import sys
import linecache

import wx

#import Core.Components.Components as Components
import Core.Utilities.Utilities as Utilities
import Core.Components.PropertiesGridCtrl as PropertiesGridCtrl
import Core.Components.Decorators as Decorators

import Core.Patterns.Observer as Observer

import GUI.DiagramNotebook as DiagramNotebook
import GUI.DetachedFrame as DetachedFrame


###
class AttributeEditor(wx.Frame, wx.Panel):
	"""     Model attributes in Frame or Panel
	"""

	def __init__(self, parent, ID, model, canvas):
		"""     Constructor.

				@param parent: wxWindows parent
				@param ID: Id
				@param model: considered model
				@param canvas: canvas object

				@type parent: instance
				@type ID: integer
				@type title: String
				@type canvas: canvas object
		"""
		import Mixins.Achievable as Achievable

		# pour gerer l'affichage dans la page de gauche dans le notebook
		if isinstance(parent, (DiagramNotebook.DiagramNotebook, DetachedFrame)):
 			wx.Frame.__init__(self, parent, ID, model.label, size = wx.Size(400, 550), style = wx.DEFAULT_FRAME_STYLE | wx.CLIP_CHILDREN | wx.STAY_ON_TOP)
			self.SetIcon(self.MakeIcon(wx.Image(os.path.join(ICON_PATH_16_16, 'properties.png'), wx.BITMAP_TYPE_PNG)))
			self.Bind(wx.EVT_CLOSE, self.OnClose)
		else:
			if isinstance(parent, wx.Panel):
				wx.Panel.__init__(self, parent, ID)
				self.SetBackgroundColour(wx.WHITE)
			else:
				sys.stdout.write(_("Parent not defined for AttributeEditor class"))
		
		#local copy
		self.model = model
		self.parent = parent
		self.canvas = canvas

		# pour garder la relation entre les proprietes affichier et le model associe (voir OnLeftClick de Block)
		#self.parent.id = id(self.model)

		# properties list
		self._list = PropertiesGridCtrl(self)

		# Create a box sizer for self
		self._box = wx.BoxSizer(wx.VERTICAL)
		self._box.Add(self._list, 1, wx.EXPAND|wx.ALL)

		###linecache module which inspect uses. It caches the file contents and does not reload it accordingly.
		linecache.clearcache()

		## text doc de la classe
		#doc = inspect.getdoc(self.model.getDEVSModel().__class__)

		if Utilities.isInstance(self.model, "Achievable"): #HERE
			self._boxH = wx.BoxSizer(wx.HORIZONTAL)
			self._code = CodeCB(self, wx.ID_ANY, self.model)
			self._boxH.Add(self._code, 1, wx.ALL | wx.EXPAND, userData='code')
			self._box.Add(self._boxH, 1, wx.ALL | wx.EXPAND, userData='code')

		self.SetSizer(self._box)

		# self._box.SetSizeHints(self)
		self.CenterOnParent()

		self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
		self._list.Bind(wx.EVT_SIZE, self.OnSize)

	def OnSize(self, event):
		""" Frame has been resized.
		"""
		### widt and weight of frame
		width, height = self.GetClientSizeTuple()
		### number of column of wx.grid
		nb_cols = self._list.GetNumberCols()
		### width of new column depending of new wx.grid column
		width /= nb_cols
		for col in range(nb_cols):
			self._list.SetColSize(col, width)
		### refresh grid
		self._list.Refresh()

	def OnKeyDown(self, event):
		""" Keyboard has been pressed
		"""
		keycode = event.GetKeyCode()

		x, y = self._list.CalcUnscrolledPosition(event.GetPosition())
		coords = self._list.XYToCell(x, y)
		row = coords[0]
		col = coords[1]

		### enter key has been pressed
		if keycode == wx.WXK_RETURN:
			### save and exit the cell if it was edited
			if self._list.IsCellEditControlEnabled():
				self._list.DisableCellEditControl()
			### close frame
			else:
				if isinstance(self, wx.Frame):
					self.Close()
		### circular moving for rows of col 1
		elif keycode == wx.WXK_TAB:
			if not self._list.MoveCursorDown(False):
				self._list.MovePageUp()
		elif keycode == wx.WXK_DELETE:
			if not self._list.IsReadOnly(row, col):
				self._list.SetCellValue(row, col, "")
		else:
			event.Skip()

	###
	def MakeIcon(self, img):
		"""
		The various platforms have different requirements for the
		icon size...
		"""
		if "wxMSW" in wx.PlatformInfo:
			img = img.Scale(16, 16)
		elif "wxGTK" in wx.PlatformInfo:
			img = img.Scale(22, 22)

		# wxMac can be any size upto 128x128, so leave the source img alone....
		return wx.IconFromBitmap(img.ConvertToBitmap())

	def OnClose(self, event):
		self.canvas.UpdateShapes()
		self.Destroy()

class QuickAttributeEditor(wx.Frame, Observer.Subject):
	"""
	"""
	def __init__(self, parent, id, model):
		"""Constructor.
		"""
		wx.Frame.__init__(self, parent, id, size=(120, 30), style=wx.CLIP_CHILDREN | wx.STAY_ON_TOP | wx.FRAME_NO_TASKBAR | wx.NO_BORDER | wx.FRAME_SHAPED)
		
		Observer.Subject.__init__(self)

		### Subject init
		self.canvas = self.GetParent()
		self.__state = {}
		self.attach(model)
		self.attach(self.canvas.GetDiagram())

		#spinCtrl for input ans output port numbers
		self._sb_input = wx.SpinCtrl(self, wx.ID_ANY, size=(60, -1), min=0, max=100)
		self._sb_output = wx.SpinCtrl(self, wx.ID_ANY, size=(60, -1), min=0, max=100)

		# mouse postions
		xwindow, ywindow = wx.GetMousePosition()
		xm, ym = self.ScreenToClientXY(xwindow, ywindow)
		self.SetPosition((xm, ym))

		#defautl value for spinCtrl
		self._sb_input.SetValue(model.input)
		self._sb_output.SetValue(model.output)

		self.__do_layout()
		self.__set_binding()

	def __do_layout(self):
		sizer_1 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_1.Add(self._sb_input, 0, wx.ADJUST_MINSIZE, 0)
		sizer_1.Add(self._sb_output, 0, wx.ADJUST_MINSIZE, 0)
		self.SetSizer(sizer_1)
		sizer_1.Fit(self)
		self.Layout()

	def __set_binding(self):
		self._sb_input.Bind(wx.EVT_TEXT, self.OnInput)
		self._sb_output.Bind(wx.EVT_TEXT, self.OnOuput)
		self.Bind(wx.EVT_CLOSE, self.OnClose)

	@Decorators.Post_Undo
	def OnInput(self, event):
		self.__state['input'] = self._sb_input.GetValue()
		self.notify()

	@Decorators.Post_Undo
	def OnOuput(self, event):
		self.__state['output'] = self._sb_output.GetValue()
		self.notify()

	def GetState(self):
		return self.__state

	def Undo(self):
		self.canvas.Undo()

	def OnClose(self, event):
		self.Destroy()

def main():
    pass

if __name__ == '__main__':
    main()
