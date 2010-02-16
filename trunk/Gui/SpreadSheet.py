# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# SpreadSheet.py ---
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
from wx.lib import sheet
from Container import *
from Plot import*

###
class MySheet(sheet.CSheet):
	def __init__(self, parent, data):
		sheet.CSheet.__init__(self, parent)
		
		self.row = self.col = 0
		
		xC=[c[0] for c in data]
		yC=[c[1] for c in data]
		
		# nombre de lignes et colonnes
		self.SetNumberRows(len(xC))
		self.SetNumberCols(10)
		
		# taile des cellules (ne fonctionne pas sous win)
		#for i in range(len(xC)):
			#self.SetColSize(i, 200)
		#for i in range(10):
			#self.SetRowSize(i, 10)
		
		# remplissage des cellules
		for i in range(len(xC)):
			self.SetCellValue(i,0,str(xC[i]))
		for i in range(len(yC)):
			self.SetCellValue(i,1,str(yC[i]))
		
	##def OnGridSelectCell(self, event):
		##self.row, self.col = event.GetRow(), event.GetCol()
		##control = self.GetParent().GetParent().position
		##value =  self.GetColLabelValue(self.col) + self.GetRowLabelValue(self.row)
		##control.SetValue(value)
		##event.Skip()

###
class Newt(wx.Frame):
	def __init__(self, parent, id, title, data):
		wx.Frame.__init__(self, parent, -1, title, size = ( 550, 500))
		
		#from Container import PATH, ICON_PATH

		# local copy
		self.data = data

		fonts = ['Times New Roman', 'Times', 'Courier', 'Courier New', 'Helvetica', 'Sans', 'verdana', 'utkal', 'aakar', 'Arial']
		box = wx.BoxSizer(wx.VERTICAL)
		
		#menuBar = wx.MenuBar()
		#menu1 = wx.Menu()
		#menuBar.Append(menu1, '&File')
		#menu2 = wx.Menu()
		#menuBar.Append(menu2, '&Edit')
		#menu4 = wx.Menu()
		#menuBar.Append(menu4, '&Insert')
		#menu5 = wx.Menu()
		#menuBar.Append(menu5, 'F&ormat')
		#menu6 = wx.Menu()
		#menuBar.Append(menu6, '&Tools')
		#menu7 = wx.Menu()
		#menuBar.Append(menu7, '&Data')
	
		#menu7 = wx.Menu()
		#menuBar.Append(menu7, '&Help')
	
		#self.SetMenuBar(menuBar)
	
		toolbar1 = wx.ToolBar(self, wx.ID_ANY, style= wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT | wx.TB_TEXT)
		toolbar1.SetToolBitmapSize((25,25)) # juste for windows

		toolbar1.AddSimpleTool(wx.NewId(), wx.Image(os.path.join(ICON_PATH,'new.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap(), 'New', '')
		toolbar1.AddSimpleTool(wx.NewId(), wx.Image(os.path.join(ICON_PATH,'open.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap(), 'Open', '')
		toolbar1.AddSimpleTool(wx.NewId(), wx.Image(os.path.join(ICON_PATH,'save.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap(), 'Save', '')
		toolbar1.AddSeparator()
		toolbar1.AddSimpleTool(wx.NewId(), wx.Image(os.path.join(ICON_PATH,'cut.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap(), 'Cut', '')
		toolbar1.AddSimpleTool(wx.NewId(), wx.Image(os.path.join(ICON_PATH,'copy.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap(), 'Copy', '')
		toolbar1.AddSimpleTool(wx.NewId(), wx.Image(os.path.join(ICON_PATH,'paste.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap(), 'Paste', '')
		toolbar1.AddSimpleTool(wx.NewId(), wx.Image(os.path.join(ICON_PATH,'delete.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap(), 'Delete', '')
		toolbar1.AddSeparator()
		#toolbar1.AddSimpleTool(wx.NewId(), wx.Image('icons/stock_undo.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap(), 'Undo', '')
		#toolbar1.AddSimpleTool(wx.NewId(), wx.Image('icons/stock_redo.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap(), 'Redo', '')
		#toolbar1.AddSeparator()
		#toolbar1.AddSimpleTool(wx.NewId(), wx.Image('icons/incr22.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap(), 'Sort Increasing', '')
		#toolbar1.AddSimpleTool(wx.NewId(), wx.Image('icons/decr22.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap(), 'Sort Decreasing', '')
		#toolbar1.AddSeparator()
		chart=toolbar1.AddSimpleTool(wx.NewId(), wx.Image(os.path.join(HOME_PATH,'icons','graph_guru.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap(), 'Chart', '')
		toolbar1.AddSeparator()
		#toolbar1.AddSimpleTool(wx.NewId(), wx.Image('icons/stock_exit.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap(), 'Quit', '')
	
		toolbar1.Realize()
	
		#toolbar2 = wx.ToolBar(self, wx.TB_HORIZONTAL | wx.TB_TEXT)
		#toolbar2.SetToolBitmapSize((25,25)) # juste for windows
		#self.position = wx.TextCtrl(toolbar2)
		#font = wx.ComboBox(toolbar2, -1, value = 'Times', choices=fonts, size=(100, -1), style=wx.CB_DROPDOWN)
		#font_height = wx.ComboBox(toolbar2, -1, value = '10',  choices=['10', '11', '12', '14', '16'], size=(50, -1), style=wx.CB_DROPDOWN)
		#toolbar2.AddControl(self.position)
		#toolbar2.AddControl(wx.StaticText(toolbar2, -1, '  '))
		#toolbar2.AddControl(font)
		#toolbar2.AddControl(wx.StaticText(toolbar2, -1, '  '))
		#toolbar2.AddControl(font_height)
		#toolbar2.AddSeparator()
		#bold = wx.Image('icons/stock_text_bold.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap()
		#toolbar2.AddCheckTool(-1, bold , shortHelp = 'Bold')
		#italic = wx.Image('icons/stock_text_italic.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap()
		#toolbar2.AddCheckTool(-1, italic,  shortHelp = 'Italic')
		#under = wx.Image('icons/stock_text_underline.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap()
		#toolbar2.AddCheckTool(-1, under, shortHelp = 'Underline')
		#toolbar2.AddSeparator()
		#toolbar2.AddSimpleTool(-1, wx.Image('icons/stock_text_align_left.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap(), 'Align Left', '')
		#toolbar2.AddSimpleTool(-1, wx.Image('icons/stock_text_align_center.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap(), 'Center', '')
		#toolbar2.AddSimpleTool(-1, wx.Image('icons/stock_text_align_right.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap(), 'Align Right', '')
	
		#toolbar2.Realize()

		box.Add(toolbar1, border=5)
		box.Add((5,5) , 0)
		#box.Add(toolbar2)
		#box.Add((5,10) , 0)
			
		self.SetSizer(box)

		self.notebook = wx.Notebook(self, wx.ID_ANY)
		# un sheet par port d'entree
		for d in self.data:
			sheet = MySheet(self.notebook, self.data[d])
			sheet.SetFocus()
			self.notebook.AddPage(sheet, _('Sheet %d')%d)
		
		box.Add(self.notebook, 1, wx.EXPAND)
	
		self.CreateStatusBar()
		
		self.Bind(wx.EVT_TOOL, self.OnGraph, chart)
		
	def OnGraph(self,event):
		activePage=self.notebook.GetSelection()
		frame=Plot(self, wx.ID_ANY,_("Plotting "), self.data[activePage])
		frame.Center()
		frame.Show()
		
if __name__ == '__main__':
	app = wx.App(0)
	newt = Newt(None, wx.ID_ANY, 'SpreadSheet')
	app.MainLoop()