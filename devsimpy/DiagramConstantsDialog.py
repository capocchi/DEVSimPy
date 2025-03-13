#!/usr/bin/env python
# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# DiagramConstantsDialog.py --- Dialog to define constantes in a diagram.
#                     --------------------------------
#                            Copyright (c) 2020
#                     L. CAPOCCHI (capocchi@univ-corse.fr)
#                		SPE Lab - University of Corsica
#                     --------------------------------
# Version 1.0                                      last modified:  10/30/21
# ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import wx
import os
import builtins
import csv
import DSV

ID_IMPORT = wx.NewIdRef()
ID_EXPORT = wx.NewIdRef()
ID_ADD = wx.NewIdRef()
ID_REMOVE = wx.NewIdRef()
ID_HELP = wx.NewIdRef()

_ = wx.GetTranslation

from Utilities import load_and_resize_image

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# CLASS DEFIINTION
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

class DiagramConstantsDialog(wx.Dialog):
	""" Dialogue to define constantes in a diagram.
	"""
	def __init__(self, *args, **kw):
		""" Constructor.
		"""
		super(DiagramConstantsDialog, self).__init__(*args, **kw)

		### local copy
		self.label = args[2]

		### all of the constants
		self.data = {}

		self.InitUI()

	def InitUI(self):
		""" Init the user interface.
		"""

		self.SetTitle(_("%s - Constants Manager")%(self.label))

		icon = wx.Icon()
		icon.CopyFromBitmap(load_and_resize_image("properties.png"))
		self.SetIcon(icon)

		panel = wx.Panel(self)
		vbox = wx.BoxSizer(wx.VERTICAL)

		### Add a toolbar in order to add, delete, import, export and have help on the user of constant.
		tb = wx.ToolBar(panel)
		vbox.Add(tb, 0, wx.EXPAND)

		tb.SetToolBitmapSize((16,16))

		tb.AddTool(ID_ADD, "", load_and_resize_image('comment_add.png'), shortHelp=_('New constant'))
		tb.AddTool(ID_REMOVE, "", load_and_resize_image('comment_remove.png'), shortHelp=_('Delete constant'))
		tb.AddTool(ID_EXPORT, "", load_and_resize_image('export.png'), shortHelp=_('Export constants into file'))
		tb.AddTool(ID_IMPORT, "", load_and_resize_image('import.png'), wx.NullBitmap, shortHelp=_('Import constants from file'))
		tb.AddTool(ID_HELP, "", load_and_resize_image('info.png'), wx.NullBitmap, shortHelp=_('Help'))

		tb.Realize()

		self._grid = wx.grid.Grid(panel, size=(300,200))
		self._grid.AutoSizeColumns(True)
		self._grid.CreateGrid(1, 2)
		self._grid.SetColLabelValue(0, _("Name"))
		self._grid.SetColSize(0, 150)
		self._grid.SetColLabelValue(1, _("Value"))
		self._grid.SetColSize(1, 150)
	
		### label column is not visible
		self._grid.SetRowLabelSize(0)
		
		vbox.Add(self._grid, 1, wx.EXPAND|wx.ALL,0)

		vbox.Add((-1, 5))
		
		self._button_ok = wx.Button(panel, wx.ID_OK, size=(70, 30))
		self._button_cancel = wx.Button(panel, wx.ID_CANCEL, size=(70, 30))
		
		hbox = wx.BoxSizer(wx.HORIZONTAL)
		hbox.Add(self._button_cancel)
		hbox.Add(self._button_ok, flag=wx.LEFT|wx.BOTTOM, border=5)

		vbox.Add(hbox, 0, flag=wx.CENTER, border=5)

#	From http://docs.wxwidgets.org/trunk/overview_windowsizing.html, wxWidgets provides two main methods for sizing:
#
#   Fit() sets the size of a window to fit around its children. 
#	The size of each children is added and then this parent window changes its size to fit them all.
#   Layout() the opposite. The children will change their size, according to sizer rules, so they can fit into available space of their parent. 
#	[...] is what is called by the default EVT_SIZE handler for container windows

#	Because a grid can have thousands of rows/cols its size can be huge. 
#	Don't try to tell the parent to fit around it. 
#	You better set max and min sizes for the grid (or its sizer) and then use Fit() or Layout() each time you change number of rows/cols or their sizes.

		panel.SetSizerAndFit(vbox)
		self.SetAutoLayout(True)
		self.Fit()

		self.__set_events()

		### just for windows
#		e = wx.SizeEvent(self.GetSize())
#		self.ProcessEvent(e)

		self.Center()

	def __set_events(self):
		""" Binding
		"""
		self.Bind(wx.EVT_TOOL, self.OnAdd, id=ID_ADD)
		self.Bind(wx.EVT_TOOL, self.OnRemove, id=ID_REMOVE)
		self.Bind(wx.EVT_TOOL, self.OnExport, id=ID_EXPORT)
		self.Bind(wx.EVT_TOOL, self.OnImport, id=ID_IMPORT)
		self.Bind(wx.EVT_TOOL, self.OnHelp, id=ID_HELP)
		self.Bind(wx.EVT_BUTTON, self.OnOk, self._button_ok)
		self.Bind(wx.EVT_BUTTON, self.OnCancel, self._button_cancel)

	def Populate(self, data):
		""" Populate the grid from a dictionary data.
		"""

		### populate the grid
		if data != {}:
			self._grid.DeleteRows(0)
			for i,key in enumerate(data):
				self._grid.AppendRows()
				self._grid.SetCellValue(i, 0, key)
				self._grid.SetCellValue(i, 1, str(data[key]))

	def OnAdd(self,evt):
		"""	Add line.
		"""
		self._grid.AppendRows()

	def OnRemove(self, evt):
		"""	Delete selected lines.
		"""

		### only if the grid has rows
		if self._grid.GetNumberRows():
			try:
				### only possible solution to have correct selected rows!
				i = self._grid.GetSelectionBlockTopLeft()[0][0]
				j = self._grid.GetSelectionBlockBottomRight()[0][0]

				if i == j:
					self._grid.DeleteRows(i)
				else:
					self._grid.DeleteRows(i,j)

			### no cells have been selected. We delete the current row according to the current position of the cursor.
			except:
				row = self._grid.GetGridCursorRow()
				self._grid.DeleteRows(row)

	def OnImport(self, event):
		""" csv file importing.
		"""

		dlg = wx.FileDialog(self, _("Choose a file"), os.getenv('USERPROFILE') or os.getenv('HOME') or DEVSIMPY_PACKAGE_PATH, "",
                                   _("CSV files (*.csv)|*.csv|Text files (*.txt)|*.txt|All files (*.*)|*.*"),
                                   wx.OPEN)
		if dlg.ShowModal() == wx.ID_OK:
			path = dlg.GetPath()
			dlg.Destroy()

			errorLog = open('import_error.log', 'a+')
			def logErrors(oldrow, newrow, expectedColumns, maxColumns, file = errorLog):
				# log the bad row to a file
				file.write(oldrow + '\n')

			dlg = DSV.ImportWizardDialog(self, wx.NewIdRef(), _('CSV Import Wizard'), path)
			if dlg.ShowModal() == wx.ID_OK:
				results = dlg.ImportData(errorHandler = logErrors)
				dlg.Destroy()
				errorLog.close()

			if results != None:

				dial = wx.MessageDialog(self, _('Do you want to clear the current values before importing?'), _('Import Manager'), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
				if dial.ShowModal() == wx.ID_YES:
					# delete rows
					self._grid.DeleteRows(0,self._grid.GetNumberRows())
				dial.Destroy()

				nbRows=self._grid.GetNumberRows()
				# import data to the grid
				for (row,data) in zip(list(range(len(results[1]))),results[1]):
					self._grid.AppendRows()
					self._grid.SetCellValue(row+nbRows,0,data[0])
					self._grid.SetCellValue(row+nbRows,1,str(data[1]))
				dial = wx.MessageDialog(self, _('Import completed!'), _('Import Manager'), wx.OK|wx.ICON_INFORMATION)
				dial.ShowModal()
			else:
				dlg.Destroy()
				 
		else:
			dlg.Destroy()

	def OnExport(self,evt):
		"""	csv file exporting.
		"""

		wcd = _("CSV files (*.csv)|*.csv|Text files (*.txt)|*.txt|All files (*.*)|*.*")
		home = os.getenv('USERPROFILE') or os.getenv('HOME') or DEVSIMPY_PACKAGE_PATH
		export_dlg = wx.FileDialog(self, message=_('Choose a file'), defaultDir=home, defaultFile='data.csv', wildcard=wcd, style=wx.SAVE|wx.OVERWRITE_PROMPT)
		if export_dlg.ShowModal() == wx.ID_OK:
			fileName = export_dlg.GetPath()
			try:
				spamWriter = csv.writer(open(fileName, 'w'), delimiter=' ', quotechar='|', lineterminator='\n', quoting=csv.QUOTE_MINIMAL)
				for row in range(self._grid.GetNumberRows()):
					spamWriter.writerow([self._grid.GetCellValue(row,0),self._grid.GetCellValue(row,1)])

			except Exception as info:
				dlg = wx.MessageDialog(self, _('Error exporting data: %s\n'%info), _('Export Manager'), wx.OK|wx.ICON_ERROR)
				dlg.ShowModal()

			dial = wx.MessageDialog(self, _('Export completed'), _('Export Manager'), wx.OK|wx.ICON_ERROR)
			dial.ShowModal()
			export_dlg.Destroy()

	def OnOk(self,evt):
		"""	Defintion of constantes in builtin and close dialog
		"""

		for row in range(self._grid.GetNumberRows()):
			const=self._grid.GetCellValue(row,0)
			val= self._grid.GetCellValue(row,1)
			if val != '':
				if type(val) in [float, int]:
					self.data[const]=float(val)
				elif type(val) in [str, str]:
					self.data[const]=val
				else:
					pass

		if self.data != {}:
			setattr(builtins, os.path.splitext(self.label)[0], self.data)
		elif os.path.splitext(self.label)[0] in builtins.__dict__:
			del builtins.__dict__[os.path.splitext(self.label)[0]]

		evt.Skip()

	def GetData(self):
		""" Return the constants stored in the grid as a dictionnary.
		"""
		return self.data

	def OnCancel(self,evt):
		"""	Close dialog.
		"""
		self.Destroy()

	def OnHelp(self, event):
		""" Help message dialogue.
		"""
		dial = wx.MessageDialog(self, _("In order to use constante:\n\nCall constante by using \"Name of Diagram\"[\'Name of constante\']\n"), _('Help Manager'), wx.OK|wx.ICON_INFORMATION)
		dial.ShowModal()