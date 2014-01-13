# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# SpreadSheet.py ---
#                     --------------------------------
#                        Copyright (c) 2009
#                       Laurent CAPOCCHI
#                      University of Corsica
#                     --------------------------------
# Version 3.0                                        last modified: 05/03/2013
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

### at the beginning to prevent with statement for python vetrsion <= 2.5
from __future__ import with_statement
import os
import sys
import wx
from wx.lib import sheet

import GUI.PlotGUI as PlotGUI
# import Core.Components.Container as Container
from Core.Components.Container import *

# to send event
if wx.VERSION_STRING < '2.9':
	from wx.lib.pubsub import Publisher
else:
	from wx.lib.pubsub import pub as Publisher
###


class MySheet(sheet.CSheet):
	def __init__(self, parent, data):
		sheet.CSheet.__init__(self, parent)

		### local copy
		self.data = data

		self.row = len(data)
		self.col = len(data[-1])
		self._full_flag = False

		# set the rows and columns of the sheet
		self.SetNumberRows(self.row)
		self.SetNumberCols(self.col)

		# set column lable titles at the top
		self.SetRowLabelAlignment(wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)
		self.SetColLabelValue(0, _('Event'))
		self.SetColLabelValue(1, _('Message'))

		self.AutoSizeColumns(100)
		self.AutoSizeRows()

		wx.CallAfter(self.Populate, data)

	def UpdateColWidth(self):
		self.AutoSizeColumns()

	#self.ForceRefresh()

	def Populate(self, data):
		"""
		"""
		self._full_flag = False
		## remplissage des cellules
		for i in xrange(len(data)):
			try:
				d = data[i]
				self.SetCellValue(i, 0, str(d[0]))
				self.SetCellValue(i, 1, str(d[1]))
				Publisher.sendMessage("progress", i / float(self.GetNumberRows()))
				wx.Yield()
			except:
				pass

		self._full_flag = True
		### infor Frame that table us full for graph icon enabling
		Publisher.sendMessage("isfull", self._full_flag)

	def IsFull(self):
		return self._full_flag

	##def OnGridSelectCell(self, event):
	##self.row, self.col = event.GetRow(), event.GetCol()
	##control = self.GetParent().GetParent().position
	##value =  self.GetColLabelValue(self.col) + self.GetRowLabelValue(self.row)
	##control.SetValue(value)
	##event.Skip()

###


class Newt(wx.Frame):
	def __init__(self, parent, id, title, aDEVS, separator=" "):
		
		wx.Frame.__init__(self, parent, wx.ID_ANY, aDEVS.getBlockModel().label, size = (550, 500),style=wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE|wx.STAY_ON_TOP)

		self.model = aDEVS
		self.sep = separator
		
		### toolbar setting
		toolbar = wx.ToolBar(self, wx.ID_ANY, style= wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT | wx.TB_TEXT)
		toolbar.SetToolBitmapSize((25,25)) # juste for windows
		new = toolbar.AddSimpleTool(wx.NewId(), wx.Image(os.path.join(ICON_PATH,'new.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap(), 'New', '')
		open_file = toolbar.AddSimpleTool(wx.NewId(), wx.Image(os.path.join(ICON_PATH,'open.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap(), 'Open', '')
		saveas = toolbar.AddSimpleTool(wx.NewId(), wx.Image(os.path.join(ICON_PATH,'save.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap(), 'SaveAs', '')
		toolbar.AddSeparator()
		cut = toolbar.AddSimpleTool(wx.NewId(), wx.Image(os.path.join(ICON_PATH,'cut.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap(), 'Cut', '')
		copy = toolbar.AddSimpleTool(wx.NewId(), wx.Image(os.path.join(ICON_PATH,'copy.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap(), 'Copy', '')
		paste = toolbar.AddSimpleTool(wx.NewId(), wx.Image(os.path.join(ICON_PATH,'paste.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap(), 'Paste', '')
		self.delete = toolbar.AddSimpleTool(wx.NewId(), wx.Image(os.path.join(ICON_PATH,'delete.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap(), 'Delete', '')
		toolbar.AddSeparator()
		update = toolbar.AddSimpleTool(wx.NewId(), wx.Image(os.path.join(ICON_PATH,'reload.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap(), 'Update', '')
		toolbar.AddSeparator()
		self.chart = toolbar.AddSimpleTool(wx.NewId(), wx.Image(os.path.join(ICON_PATH, 'graph_guru.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap(), 'Chart', '')
		toolbar.EnableTool(self.chart.GetId(), False)
		toolbar.Realize()

		self.SetToolBar(toolbar)

		self.statusbar = self.CreateStatusBar()

		### notebook setting
		self.notebook = wx.Notebook(self, wx.ID_ANY)
		
		self.LoadingDataInPage()

		### Layout
		box = wx.BoxSizer(wx.VERTICAL)
		box.Add(toolbar)
		box.Add(self.notebook, 1, wx.EXPAND)
		self.SetSizer(box)

		### binding
		self.Bind(wx.EVT_TOOL, self.OnNew, new)
		self.Bind(wx.EVT_TOOL, self.OnOpen, open_file)
		self.Bind(wx.EVT_TOOL, self.OnSaveAs, saveas)
		self.Bind(wx.EVT_TOOL, self.OnCopy, copy)
		self.Bind(wx.EVT_TOOL, self.OnCut, cut)
		self.Bind(wx.EVT_TOOL, self.OnPaste, paste)
		self.Bind(wx.EVT_TOOL, self.OnDelete, self.delete)
		self.Bind(wx.EVT_TOOL, self.OnUpdate, update)
		self.Bind(wx.EVT_TOOL, self.OnGraph, self.chart)

		self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnTab, self.notebook)

		### pubsub
		### when is sheet is full, graph icon is enabled
		Publisher.subscribe(self.EnableGraphIcon, ("isfull"))
		Publisher.subscribe(self.OnProgress, ("progress"))
		
	def LoadingDataInPage(self):
		
		### read and load the data in sheet
		for i in xrange(len(self.model.IPorts)):
			fn = "%s%d.dat"%(self.model.fileName, i)
			oPort = self.model.IPorts[i].inLine[0]
			host = oPort.host
			if os.path.exists(fn):
				data = self.FileToData(fn, self.sep)
				label = _('%s (Port %i)')%(host.getBlockModel().label, oPort.myID)
				self.AddPage(data, label)
		
	def OnUpdate(self, event):
		
		### remove all pages
		while self.notebook.GetPageCount() >= 1:
			self.notebook.RemovePage(self.notebook.GetSelection())
		
		### reload all page
		self.LoadingDataInPage()

	def FileToData(self, fn, separator):
		""" Create data from file.
		"""
		with open(fn, 'r') as f:
			if separator != "":
				data = map(lambda a: a.replace('\n', '').split(separator), f.readlines())
			else:
				L = f.readlines()
				index = iter(range(len(L)))
				data = map(lambda a: (index.next(), a.replace('\n', '')), L)

		return data

	def EnableGraphIcon(self, msg):
		""" Enable graph button when loadin data is finished and clear the statusbar.
		"""

		### update the column width
		activePage = self.notebook.GetSelection()
		sheet = self.notebook.GetPage(activePage)
		sheet.UpdateColWidth()

		toolbar = self.GetToolBar()
		toolbar.EnableTool(self.chart.GetId(), msg.data)
		self.statusbar.SetStatusText("", 0)

	def OnTab(self, event):
		### update the column width
		activePage = self.notebook.GetSelection()
		sheet = self.notebook.GetPage(activePage)
		sheet.UpdateColWidth()

	def OnProgress(self, msg):
		""" Update status bar with loading data progression
		"""
		pourcent = 100 * float(msg.data)
		self.statusbar.SetStatusText(_("Loading data... (%d %%)") % int(pourcent), 0)

	def AddPage(self, data=None, label=""):
		""" Add new page to notebook knowing data and label
		"""
		if not data: data = [[]]

		sheet = MySheet(self.notebook, data)
		sheet.SetFocus()
		self.notebook.AddPage(sheet, label)

		### enable delete button
		toolbar = self.GetToolBar()
		toolbar.EnableTool(self.delete.GetId(), True)

	def OnNew(self, event):
		""" New button bas been pressed.
		"""
		data = [[]]
		label = _('New %d' % self.notebook.GetPageCount())
		self.AddPage(label=label)

	def OnOpen(self, event):
		""" Open button has been pressed.
		"""
		wcd = _("DataSheet file (*.dat)|*.dat|All files (*)|*")
		home = os.getenv('USERPROFILE') or os.getenv('HOME') or HOME_PATH
		open_dlg = wx.FileDialog(self, message=_('Choose a file'), defaultDir=home, defaultFile="", wildcard=wcd,
								 style=wx.OPEN | wx.MULTIPLE | wx.CHANGE_DIR)
		# get the new path from open file dialogue
		if open_dlg.ShowModal() == wx.ID_OK:
			### for selected paths
			for fn in open_dlg.GetPaths():
				if os.path.exists(fn):
					### separator request
					separator_dico = {"EMPTY": "", "SPACE": " ", "SEMICOLON": ";", "COMMA": ",", "POINT": "."}
					dlg = wx.SingleChoiceDialog(self, _("Choose a separator:"), _('Separator Manager'),
												separator_dico.keys(), wx.CHOICEDLG_STYLE)
					if dlg.ShowModal() == wx.ID_OK:
						separator = separator_dico[dlg.GetStringSelection()]
					else:
						separator = ""
					dlg.Destroy()

					data = self.FileToData(fn, separator)
					label = _('New %d' % self.notebook.GetPageCount())
					self.AddPage(data, label)

	def OnSaveAs(self, event):
		""" SaveAs button has been pressed.
		"""
		wcd = _("DataSheet file (*.dat)|*.dat|All files (*)|*")
		home = HOME_PATH
		save_dlg = wx.FileDialog(self, message=_('Save file as...'), defaultDir=home, defaultFile='', wildcard=wcd, style=wx.SAVE | wx.OVERWRITE_PROMPT)
		if save_dlg.ShowModal() == wx.ID_OK:
			fn = save_dlg.GetFilename()

			activePage = self.notebook.GetSelection()
			sheet = self.notebook.GetPage(activePage)
			nbr = sheet.GetNumberRows()
			nbc = sheet.GetNumberCols()

			with open(fn, 'w') as f:
				for row in xrange(nbr):
					f.write("%s %s\n" % (sheet.GetCellValue(row, 0), sheet.GetCellValue(row, 1)))

	def OnCopy(self, event):
		""" Copy button has been pressed.
		"""
		activePage = self.notebook.GetSelection()
		sheet = self.notebook.GetPage(activePage)
		sheet.Copy()

	def OnCut(self, event):
		""" Cut button has been pressed.
		"""
		activePage = self.notebook.GetSelection()
		sheet = self.notebook.GetPage(activePage)
		sheet.Copy()
		sheet.Clear()

	def OnPaste(self, event):
		""" Paste button has been pressed.
		"""
		activePage = self.notebook.GetSelection()
		sheet = self.notebook.GetPage(activePage)
		sheet.Paste()

	def OnDelete(self, event):
		""" Delete button has been pressed.
		"""

		### remove page
		if self.notebook.GetPageCount() >= 1:
			self.notebook.RemovePage(self.notebook.GetSelection())

		### disable delete button
		if self.notebook.GetPageCount() == 0:
			toolbar = self.GetToolBar()
			toolbar.EnableTool(self.delete.GetId(), False)

	def OnGraph(self, event):
		""" Graph button has been pressed.
		"""

		activePage = self.notebook.GetSelection()
		sheet = self.notebook.GetPage(activePage)
		title = self.notebook.GetPageText(activePage)

		### selected rows with mouse but on label colonn
		selected_rows = sheet.GetSelectedRows()

		### really selected cells with mouse
		a = sheet.GetSelectionBlockTopLeft()
		b = sheet.GetSelectionBlockBottomRight()

		if a != [] and b != []:
			selected_rows = range(a[0][0], b[0][0])

		nbc = xrange(sheet.GetNumberCols())
		nbr = xrange(sheet.GetNumberRows()) if selected_rows == [] else selected_rows

		try:
			data = [[float(sheet.GetCellValue(r, c)) for c in nbc] for r in nbr]
		except Exception, info:
			wx.MessageBox(_('Type of data should be float or int : %s' % info), _('Info'))
		else:
			frame = PlotGUI.StaticPlot(self, wx.ID_ANY, title, data)
			frame.Center()
			frame.Show()

		#if __name__ == '__main__':
		#app = wx.App(0)
		#newt = Newt(None, wx.ID_ANY, 'SpreadSheet')
		#app.MainLoop()
