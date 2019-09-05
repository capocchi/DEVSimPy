#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wx
import os
import builtins
import csv

import DSV

_ = wx.GetTranslation

class DiagramConstantsDialog(wx.Dialog):

	def __init__(self, parent, id, title, model):
		""" Constructor
		"""

		wx.Dialog.__init__(self, parent, id, title, wx.DefaultPosition, (400, 380), style=wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE)

		### local copy
		self.model = model
		self.label = title

		self.SetTitle(_("%s - Constants Manager")%(self.label))

		icon = wx.EmptyIcon() if wx.VERSION_STRING < '4.0' else wx.Icon()
		icon.CopyFromBitmap(wx.Bitmap(os.path.join(ICON_PATH_16_16, "properties.png"), wx.BITMAP_TYPE_ANY))
		self.SetIcon(icon)

		self._panel = wx.Panel(self, wx.ID_ANY)

		grid_sizer_1 = wx.GridSizer(1, 2, 0, 0)

		self._grid = wx.grid.Grid(self._panel, wx.ID_ANY, size=(200, 100))
		self._grid.AutoSizeColumns(True)
		self._grid.CreateGrid(1, 2)
		self._grid.SetColLabelValue(0, _("Name"))
		self._grid.SetColSize(0, 100)
		self._grid.SetColLabelValue(1, _("Value"))
		self._grid.SetColSize(1, 100)
		### The label windows will still exist, but they will not be visible.

		# constants loading
		D = self.model.constants_dico if self.model else {}

		row = 0
		self._grid.DeleteRows(0)
		for key in D:
			self._grid.AppendRows()
			self._grid.SetCellValue(row, 0, key)
			self._grid.SetCellValue(row, 1, str(D[key]))
			row += 1

		grid_sizer_1.Add(self._grid, 1, wx.EXPAND|wx.ALL, 0)

		self._panel.SetSizer(grid_sizer_1)

		self._button_add = wx.Button(self._panel, wx.ID_ADD, "")
		self._button_remove = wx.Button(self._panel, wx.ID_REMOVE, "")
		self._button_help = wx.Button(self._panel, wx.ID_HELP, "")

		grid_sizer_3 = wx.GridSizer(3, 1, 0, 0)
		grid_sizer_3.Add(self._button_add, 0, wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)
		grid_sizer_3.Add(self._button_remove, 0, wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)
		grid_sizer_3.Add((-1,50), 0, wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)

		self._button_import = wx.Button(self._panel, wx.ID_ANY, _("Import"))
		self._button_export = wx.Button(self._panel, wx.ID_ANY, _("Export"))
		self._button_import.SetDefault()

		sizer_2 = wx.BoxSizer(wx.VERTICAL)
		sizer_2.Add(self._button_import, 0, wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
		sizer_2.Add(self._button_export, 0, wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
		sizer_2.Add(self._button_help, 0, wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)

		sizer_1 = wx.BoxSizer(wx.VERTICAL)
		sizer_1.Add(grid_sizer_3, 1, wx.EXPAND, 0)
		sizer_1.Add(sizer_2, 1, wx.EXPAND, 0)

		grid_sizer_1.Add(sizer_1, 1, wx.EXPAND, 0)

		self._button_cancel = wx.Button(self._panel, wx.ID_CANCEL, "")
		self._button_ok = wx.Button(self._panel, wx.ID_OK, "")

		grid_sizer_2 = wx.GridSizer(1, 2, 0, 0)
		grid_sizer_2.Add(self._button_cancel, 0, wx.ALIGN_BOTTOM|wx.ALIGN_CENTER_HORIZONTAL|wx.ADJUST_MINSIZE, 0)
		grid_sizer_2.Add(self._button_ok, 0, wx.ALIGN_BOTTOM|wx.ALIGN_CENTER_HORIZONTAL|wx.ADJUST_MINSIZE, 0)

		sizer_1.Add(grid_sizer_2, 1, wx.EXPAND, 0)

		self._panel.SetSizer(grid_sizer_1)

		self.__set_events()

		### just for windows
		e = wx.SizeEvent(self.GetSize())
		self.ProcessEvent(e)

		self.Center()

	def __set_events(self):
		""" Binding
		"""
		self.Bind(wx.EVT_BUTTON, self.OnAdd, self._button_add)
		self.Bind(wx.EVT_BUTTON, self.OnRemove, self._button_remove)
		self.Bind(wx.EVT_BUTTON, self.OnExport, self._button_export)
		self.Bind(wx.EVT_BUTTON, self.OnImport, self._button_import)
		self.Bind(wx.EVT_BUTTON, self.OnHelp, self._button_help)
		self.Bind(wx.EVT_BUTTON, self.OnOk, self._button_ok)
		self.Bind(wx.EVT_BUTTON, self.OnCancel, self._button_cancel)

	def OnAdd(self,evt):
		"""	Add line
		"""
		self._grid.AppendRows()

	def OnRemove(self, evt):
		"""	Delete selected lines
		"""

		for row in self._grid.GetSelectedRows():
			self._grid.DeleteRows(row)

	def OnImport(self, event):
		""" csv file importing
		"""

		dlg = wx.FileDialog(self, _("Choose a file"), os.getenv('USERPROFILE') or os.getenv('HOME') or HOME_PATH, "",
                                   _("CSV files (*.csv)|*.csv|Text files (*.txt)|*.txt|All files (*.*)|*.*"),
                                   wx.OPEN)
		if dlg.ShowModal() == wx.ID_OK:
			path = dlg.GetPath()
			dlg.Destroy()

			errorLog = open('import_error.log', 'a+')
			def logErrors(oldrow, newrow, expectedColumns, maxColumns, file = errorLog):
				# log the bad row to a file
				file.write(oldrow + '\n')

			dlg = DSV.ImportWizardDialog(self, wx.ID_ANY, _('CSV Import Wizard'), path)
			if dlg.ShowModal() == wx.ID_OK:
				results = dlg.ImportData(errorHandler = logErrors)
				dlg.Destroy()
				errorLog.close()

			if results != None:
				# delete first row
				self._grid.DeleteRows(0)
				# import data to the grid
				for (row,data) in zip(list(range(len(results[1]))),results[1]):
					self._grid.AppendRows()
					self._grid.SetCellValue(row,0,data[0])
					self._grid.SetCellValue(row,1,str(data[1]))
				dial = wx.MessageDialog(self, _('Import completed'), _('Import Manager'), wx.OK|wx.ICON_INFORMATION)
				dial.ShowModal()
			else:
	 			dlg.Destroy()

		else:
			dlg.Destroy()

	def OnExport(self,evt):
		"""	csv file exporting
		"""

		wcd = _("CSV files (*.csv)|*.csv|Text files (*.txt)|*.txt|All files (*.*)|*.*")
		home = os.getenv('USERPROFILE') or os.getenv('HOME') or HOME_PATH
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
		D={}
		for row in range(self._grid.GetNumberRows()):
			const=self._grid.GetCellValue(row,0)
			val= self._grid.GetCellValue(row,1)
			if val != '':
				if type(val) in [float, int]:
					D[const]=float(val)
				elif type(val) in [str, str]:
					D[const]=val
				else:
					pass

		if D != {}:
			builtins.__dict__[os.path.splitext(self.label)[0]]=D
		elif os.path.splitext(self.label)[0] in builtins.__dict__:
			del builtins.__dict__[os.path.splitext(self.label)[0]]

		self.model.constants_dico = D

		self.Destroy()

	def OnCancel(self,evt):
		"""	Close dialog
		"""
		self.Destroy()

	def OnHelp(self, event):
		dial = wx.MessageDialog(self, _("In order to use constante:\n\nCall constante by using \"Name of Diagram\"[\'Name of constante\']\n"), _('Help Manager'), wx.OK|wx.ICON_INFORMATION)
		dial.ShowModal()

### ------------------------------------------------------------
class TestApp(wx.App):
	""" Testing application
	"""

	def OnInit(self):

		import gettext

		builtins.__dict__['ICON_PATH_16_16']=os.path.join('icons','16x16')
		builtins.__dict__['_'] = gettext.gettext

		self.frame = DiagramConstantsDialog(None, -1, title="Model", model=None)
		self.frame.Show()
		return True

	def OnQuit(self, event):
		self.Close()

if __name__ == '__main__':

	app = TestApp(0)
	app.MainLoop()