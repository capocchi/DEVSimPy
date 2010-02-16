#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wx
import wx.grid
import os
import __builtin__
import csv

import DSV

class DiagramConstantsDialog(wx.Frame):
	def __init__(self, parent, id, title, model):

		wx.Frame.__init__(self, parent, id, title, wx.DefaultPosition, (500, 280))

		self.model = model
		self.label = title

		self.panel = wx.Panel(self,-1)
		self.grid = wx.grid.Grid(self.panel, -1, size=(1, 1))
		self.button_add = wx.Button(self.panel, wx.ID_ADD, "")
		self.button_remove = wx.Button(self.panel, wx.ID_REMOVE, "")
		self.static_line = wx.StaticLine(self.panel, -1)
		
		#self.button_import = wx.lib.buttons.GenBitmapTextButton(self.panel, -1, wx.Bitmap(os.path.join(ICON_PATH_20_20,"import.png"), wx.BITMAP_TYPE_ANY), ' Import ')
		#self.button_import.SetBezelWidth(3)
		
		self.button_import = wx.Button(self.panel, -1, _("Import"))
		self.button_export = wx.Button(self.panel, -1, _("Export"))
		self.button_cancel = wx.Button(self.panel, wx.ID_CANCEL, "")
		self.button_ok = wx.Button(self.panel, wx.ID_OK, "")
	
		self.__set_properties()
		self.__do_layout()
		self.__set_events()

	def __set_properties(self):
	
		self.SetTitle(_("%s - Constants parameters")%(self.label))
		_icon = wx.EmptyIcon()
		_icon.CopyFromBitmap(wx.Bitmap(os.path.join(ICON_PATH_20_20, "properties.png"), wx.BITMAP_TYPE_ANY))
		self.SetIcon(_icon)
		self.Center()
		self.SetBackgroundColour(wx.NullColour)
		self.panel.SetBackgroundColour(wx.NullColour)
		self.grid.AutoSizeColumns(True)
		self.grid.CreateGrid(1, 2)
		self.grid.SetColLabelValue(0, _("Name"))
		self.grid.SetColSize(0, 80)
		self.grid.SetColLabelValue(1, _("Value"))
		self.grid.SetColSize(1, 80)
		self.button_import.SetDefault()

		# chargement des constantes si elles existent déjà
		
		if __builtin__.__dict__.has_key(os.path.splitext(self.label)[0]):
			D = __builtin__.__dict__[os.path.splitext(self.label)[0]]
			row=0
			self.grid.DeleteRows(0)
			for key in D:
				self.grid.AppendRows()
				self.grid.SetCellValue(row,0,key)
				self.grid.SetCellValue(row,1,str(D[key]))
				row+=1

	def __do_layout(self):
		grid_sizer_1 = wx.GridSizer(1, 2, 0, 0)
		sizer_1 = wx.BoxSizer(wx.VERTICAL)
		grid_sizer_2 = wx.GridSizer(1, 2, 0, 0)
		sizer_2 = wx.BoxSizer(wx.VERTICAL)
		grid_sizer_3 = wx.GridSizer(3, 1, 0, 0)
		grid_sizer_1.Add(self.grid, 1, wx.ALL|wx.EXPAND, 0)
		grid_sizer_3.Add(self.button_add, 0, wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)
		grid_sizer_3.Add(self.button_remove, 0, wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)
		grid_sizer_3.Add(self.static_line, 0, wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)
		sizer_1.Add(grid_sizer_3, 1, wx.EXPAND, 0)
		sizer_2.Add(self.button_import, 0, wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
		sizer_2.Add(self.button_export, 0, wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
		sizer_2.Add((285, 80), 0, wx.ADJUST_MINSIZE, 0)
		sizer_1.Add(sizer_2, 1, wx.EXPAND, 0)
		grid_sizer_2.Add(self.button_cancel, 0, wx.ALIGN_BOTTOM|wx.ALIGN_CENTER_HORIZONTAL|wx.ADJUST_MINSIZE, 0)
		grid_sizer_2.Add(self.button_ok, 0, wx.ALIGN_BOTTOM|wx.ALIGN_CENTER_HORIZONTAL|wx.ADJUST_MINSIZE, 0)
		sizer_1.Add(grid_sizer_2, 1, wx.EXPAND, 0)
		grid_sizer_1.Add(sizer_1, 1, wx.EXPAND, 0)
		self.panel.SetSizer(grid_sizer_1)
		self.Layout()

	def __set_events(self):
		self.Bind(wx.EVT_BUTTON, self.OnAdd, self.button_add)
		self.Bind(wx.EVT_BUTTON, self.OnRemove, self.button_remove)
		self.Bind(wx.EVT_BUTTON, self.OnExport, self.button_export)
		self.Bind(wx.EVT_BUTTON, self.OnImport, self.button_import)
		self.Bind(wx.EVT_BUTTON, self.OnOk, self.button_ok)
		self.Bind(wx.EVT_BUTTON, self.OnCancel, self.button_cancel)
		
	def OnAdd(self,evt):
		"""	Ajout d'une ligne
		"""
		self.grid.AppendRows()

	def OnRemove(self,evt):
		"""	Suppression des lignes selectionnées
		"""
		for row in self.grid.GetSelectedRows():
			self.grid.DeleteRows(row)
	
	def OnImport(self, event):

		dlg = wx.FileDialog(self, _("Choose a file"), os.getenv('USERPROFILE') or os.getenv('HOME') or os.getcwd(), "",
                                   "CSV files (*.csv)|*.csv|Text files (*.txt)|*.txt|All files (*.*)|*.*",
                                   wx.OPEN)
                if dlg.ShowModal() == wx.ID_OK:
                    path = dlg.GetPath()
                    dlg.Destroy()

                    errorLog = open('import_error.log', 'a+') 
                    def logErrors(oldrow, newrow, expectedColumns, maxColumns, file = errorLog):
                        # log the bad row to a file
                        file.write(oldrow + '\n')

                    dlg = DSV.ImportWizardDialog(self, -1, _('CSV Import Wizard'), path)
                    if dlg.ShowModal() == wx.ID_OK:
                        results = dlg.ImportData(errorHandler = logErrors)
                        dlg.Destroy()
                        errorLog.close()

			if results != None:
				# delete first row
				self.grid.DeleteRows(0)
				# import data to the grid
				for (row,data) in zip(range(len(results[1])),results[1]):
					self.grid.AppendRows()
					self.grid.SetCellValue(row,0,data[0])
					self.grid.SetCellValue(row,1,str(data[1]))
				dial = wx.MessageDialog(self, 'Import completed', 'Info', wx.OK)
				dial.ShowModal()
                    else:
                        dlg.Destroy()

                else:
                    dlg.Destroy()

	def OnExport(self,evt):
		"""	Exportation dans un fichier csv
		"""
		
		wcd = "CSV files (*.csv)|*.csv|Text files (*.txt)|*.txt|All files (*.*)|*.*"
		home = os.getenv('USERPROFILE') or os.getenv('HOME') or os.getcwd()
		export_dlg = wx.FileDialog(self, message=_('Choose a file'), defaultDir=home, defaultFile='data.csv', wildcard=wcd, style=wx.SAVE|wx.OVERWRITE_PROMPT)
		if export_dlg.ShowModal() == wx.ID_OK:
			fileName = export_dlg.GetPath()
			try:
				spamWriter = csv.writer(open(fileName, 'w'), delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)
				for row in range(self.grid.GetNumberRows()):
					spamWriter.writerow([self.grid.GetCellValue(row,0),self.grid.GetCellValue(row,1)])
				
			except Exception, info:
				dlg = wx.MessageDialog(self, _('Error exporting data: %s\n'%info))
				dlg.ShowModal()

			dial = wx.MessageDialog(self, _('Export completed'), 'Info', wx.OK)
			dial.ShowModal()
			export_dlg.Destroy()

	def OnOk(self,evt):
		"""	Definition des constantes dans le builtin et fermeture du dialogue
		"""
		D={}
		for row in range(self.grid.GetNumberRows()):
			const=str(self.grid.GetCellValue(row,0))
			val= self.grid.GetCellValue(row,1)
			if val != '':
				D[const]=float(val)
		
		if D != {}:
			__builtin__.__dict__[os.path.splitext(self.label)[0]]=D
			self.model.constants_dico = D

		self.Close()

	def OnCancel(self,evt):
		"""	Fermeture du dialogue
		"""
		self.Close()

#if __name__ == "__main__":
	#app = wx.PySimpleApp(0)
	#wx.InitAllImageHandlers()
	#frame = DiagramConstantsDialog(None, -1, title="Model", size=(140,100), model="Model")
	#app.SetTopWindow(frame)
	#frame.Show()
	#app.MainLoop()
