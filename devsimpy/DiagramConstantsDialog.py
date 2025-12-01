#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# DiagramConstantsDialog.py --- Dialog to define constantes in a diagram.
#                     --------------------------------
#                            Copyright (c) 2020
#                     L. CAPOCCHI (capocchi@univ-corse.fr)
#                		SPE Lab - University of Corsica
#                     --------------------------------
# Version 1.0                                      last modified:  10/30/21
# ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
'''

import wx
import wx.grid
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
# CLASS DEFINITION
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

class DiagramConstantsDialog(wx.Dialog):
	""" Dialogue to define constantes in a diagram.
	"""
	def __init__(self, *args, **kw):
		""" Constructor.
		"""
		# Si on est dans GitHub Actions, changer wx.Dialog en wx.Frame
		if os.environ.get("GITHUB_ACTIONS") == "true":
			kw["style"] = wx.DEFAULT_FRAME_STYLE

		super().__init__(*args, **kw)

		### local copy
		self.label = args[2] if len(args) > 2 else "Diagram"

		### all of the constants
		self.data = {}

		self.InitUI()

	def InitUI(self):
		""" Init the user interface.
		"""

		self.SetTitle(_("%s - Constants Manager") % (self.label))

		icon = wx.Icon()
		icon.CopyFromBitmap(load_and_resize_image("properties.png"))
		self.SetIcon(icon)

		# Taille optimisée
		self.SetSize((550, 500))
		self.SetMinSize((500, 400))

		panel = wx.Panel(self)
		panel.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
		
		main_sizer = wx.BoxSizer(wx.VERTICAL)

		# --- Toolbar Section ---
		toolbar_box = wx.StaticBoxSizer(wx.HORIZONTAL, panel, _("Actions"))
		
		# Créer une barre d'outils plus moderne avec des boutons
		btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
		
		self._btn_add = wx.Button(panel, ID_ADD, _("Add"))
		self._btn_add.SetBitmap(load_and_resize_image('comment_add.png'))
		self._btn_add.SetToolTip(_('Add a new constant'))
		
		self._btn_remove = wx.Button(panel, ID_REMOVE, _("Remove"))
		self._btn_remove.SetBitmap(load_and_resize_image('comment_remove.png'))
		self._btn_remove.SetToolTip(_('Delete selected constant'))
		
		self._btn_import = wx.Button(panel, ID_IMPORT, _("Import"))
		self._btn_import.SetBitmap(load_and_resize_image('import.png'))
		self._btn_import.SetToolTip(_('Import constants from CSV file'))
		
		self._btn_export = wx.Button(panel, ID_EXPORT, _("Export"))
		self._btn_export.SetBitmap(load_and_resize_image('export.png'))
		self._btn_export.SetToolTip(_('Export constants to CSV file'))
		
		self._btn_help = wx.Button(panel, ID_HELP, _("Help"))
		self._btn_help.SetBitmap(load_and_resize_image('info.png'))
		self._btn_help.SetToolTip(_('Show help on using constants'))
		
		btn_sizer.Add(self._btn_add, flag=wx.ALL, border=3)
		btn_sizer.Add(self._btn_remove, flag=wx.ALL, border=3)
		btn_sizer.Add((10, -1))  # Séparateur
		btn_sizer.Add(self._btn_import, flag=wx.ALL, border=3)
		btn_sizer.Add(self._btn_export, flag=wx.ALL, border=3)
		btn_sizer.Add((10, -1))  # Séparateur
		btn_sizer.Add(self._btn_help, flag=wx.ALL, border=3)
		
		toolbar_box.Add(btn_sizer, flag=wx.ALL, border=5)
		main_sizer.Add(toolbar_box, flag=wx.ALL|wx.EXPAND, border=10)

		# --- Grid Section ---
		grid_box = wx.StaticBoxSizer(wx.VERTICAL, panel, _("Constants"))
		
		self._grid = wx.grid.Grid(panel)
		self._grid.CreateGrid(1, 2)
		self._grid.SetColLabelValue(0, _("Name"))
		self._grid.SetColLabelValue(1, _("Value"))
		
		# Ajuster les colonnes pour remplir l'espace disponible
		self._grid.SetColSize(0, 200)
		self._grid.SetColSize(1, 200)
		self._grid.EnableDragColSize(True)
		
		# Masquer les labels de lignes
		self._grid.SetRowLabelSize(0)
		
		# Activer le redimensionnement automatique
		self._grid.AutoSizeColumns(False)
		self._grid.SetDefaultCellAlignment(wx.ALIGN_LEFT, wx.ALIGN_CENTRE)
		
		# Style de la grille
		self._grid.EnableGridLines(True)
		self._grid.SetGridLineColour(wx.Colour(200, 200, 200))
		
		# Améliorer la navigation au clavier
		self._grid.SetTabBehaviour(wx.grid.Grid.Tab_Wrap)
		
		# Couleur alternée pour les lignes (optionnel, améliore la lisibilité)
		attr = wx.grid.GridCellAttr()
		attr.SetBackgroundColour(wx.Colour(245, 245, 245))
		self._grid.SetRowAttr(0, attr)
		
		grid_box.Add(self._grid, proportion=1, flag=wx.ALL|wx.EXPAND, border=5)
		main_sizer.Add(grid_box, proportion=1, flag=wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, border=10)

		# --- Information Section ---
		info_text = wx.StaticText(panel, label=_("Usage: DiagramName['ConstantName']"))
		info_text.SetForegroundColour(wx.Colour(100, 100, 100))
		font = info_text.GetFont()
		font.SetPointSize(font.GetPointSize() - 1)
		info_text.SetFont(font)
		main_sizer.Add(info_text, flag=wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)

		# --- Buttons ---
		button_sizer = wx.StdDialogButtonSizer()
		
		self._button_cancel = wx.Button(panel, wx.ID_CANCEL, _("Cancel"))
		button_sizer.AddButton(self._button_cancel)
		
		self._button_ok = wx.Button(panel, wx.ID_OK, _("OK"))
		self._button_ok.SetDefault()
		button_sizer.AddButton(self._button_ok)
		
		button_sizer.Realize()
		
		main_sizer.Add(button_sizer, flag=wx.ALL|wx.ALIGN_RIGHT, border=10)

		panel.SetSizer(main_sizer)
		
		self.__set_events()
		
		self.Layout()
		self.Center()

	def __set_events(self):
		""" Binding
		"""
		self.Bind(wx.EVT_BUTTON, self.OnAdd, id=ID_ADD)
		self.Bind(wx.EVT_BUTTON, self.OnRemove, id=ID_REMOVE)
		self.Bind(wx.EVT_BUTTON, self.OnExport, id=ID_EXPORT)
		self.Bind(wx.EVT_BUTTON, self.OnImport, id=ID_IMPORT)
		self.Bind(wx.EVT_BUTTON, self.OnHelp, id=ID_HELP)
		self.Bind(wx.EVT_BUTTON, self.OnOk, self._button_ok)
		self.Bind(wx.EVT_BUTTON, self.OnCancel, self._button_cancel)
		
		# Raccourcis clavier
		self.Bind(wx.grid.EVT_GRID_CELL_CHANGED, self.OnCellChanged, self._grid)

	def Populate(self, data):
		""" Populate the grid from a dictionary data.
		"""

		### populate the grid
		if data:
			self._grid.DeleteRows(0, self._grid.GetNumberRows())
			for i, key in enumerate(data):
				if i > 0:
					self._grid.AppendRows()
				self._grid.SetCellValue(i, 0, key)
				self._grid.SetCellValue(i, 1, str(data[key]))

	def OnAdd(self, evt):
		"""	Add line.
		"""
		self._grid.AppendRows()
		# Focus sur la nouvelle ligne
		new_row = self._grid.GetNumberRows() - 1
		self._grid.SetGridCursor(new_row, 0)
		self._grid.MakeCellVisible(new_row, 0)
		self._grid.EnableCellEditControl(True)  # Activer l'édition directement
	
	def OnCellChanged(self, evt):
		""" Update row color when cell is modified
		"""
		row = evt.GetRow()
		# Visual feedback that the row has been modified
		evt.Skip()

	def OnRemove(self, evt):
		"""	Delete selected lines.
		"""

		### only if the grid has rows
		if self._grid.GetNumberRows() == 0:
			wx.MessageBox(_("No constants to remove!"), _("Warning"), 
						 wx.OK | wx.ICON_WARNING)
			return

		try:
			### Get selected block
			top_left = self._grid.GetSelectionBlockTopLeft()
			bottom_right = self._grid.GetSelectionBlockBottomRight()
			
			if top_left and bottom_right:
				i = top_left[0][0]
				j = bottom_right[0][0]
				num_rows = j - i + 1
				self._grid.DeleteRows(i, num_rows)
			else:
				# No block selected, delete current row
				row = self._grid.GetGridCursorRow()
				self._grid.DeleteRows(row)

		except Exception as e:
			### Fallback: delete current row
			row = self._grid.GetGridCursorRow()
			if row >= 0 and row < self._grid.GetNumberRows():
				self._grid.DeleteRows(row)

	def OnImport(self, event):
		""" csv file importing.
		"""

		home = os.getenv('USERPROFILE') or os.getenv('HOME') or '.'
		dlg = wx.FileDialog(
			self, 
			_("Choose a file"), 
			home, 
			"",
			_("CSV files (*.csv)|*.csv|Text files (*.txt)|*.txt|All files (*.*)|*.*"),
			wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
		)
		
		if dlg.ShowModal() != wx.ID_OK:
			dlg.Destroy()
			return

		path = dlg.GetPath()
		dlg.Destroy()

		try:
			errorLog = open('import_error.log', 'a+')
			
			def logErrors(oldrow, newrow, expectedColumns, maxColumns, file=errorLog):
				file.write(oldrow + '\n')

			dlg = DSV.ImportWizardDialog(self, wx.NewIdRef(), _('CSV Import Wizard'), path)
			if dlg.ShowModal() == wx.ID_OK:
				results = dlg.ImportData(errorHandler=logErrors)
				dlg.Destroy()
				errorLog.close()

				if results is not None:
					dial = wx.MessageDialog(
						self, 
						_('Do you want to clear the current values before importing?'), 
						_('Import Manager'), 
						wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION
					)
					
					if dial.ShowModal() == wx.ID_YES:
						self._grid.DeleteRows(0, self._grid.GetNumberRows())
					dial.Destroy()

					nbRows = self._grid.GetNumberRows()
					
					# Import data to the grid
					for row, data in enumerate(results[1]):
						if row > 0 or nbRows == 0:
							self._grid.AppendRows()
						self._grid.SetCellValue(row + nbRows, 0, data[0])
						self._grid.SetCellValue(row + nbRows, 1, str(data[1]))
					
					wx.MessageBox(
						_('Import completed successfully!'), 
						_('Import Manager'), 
						wx.OK | wx.ICON_INFORMATION
					)
			else:
				dlg.Destroy()
				
		except Exception as e:
			wx.MessageBox(
				_('Error during import: {}').format(str(e)), 
				_('Import Error'), 
				wx.OK | wx.ICON_ERROR
			)

	def OnExport(self, evt):
		"""	csv file exporting.
		"""

		if self._grid.GetNumberRows() == 0:
			wx.MessageBox(_("No constants to export!"), _("Warning"), 
						 wx.OK | wx.ICON_WARNING)
			return

		home = os.getenv('USERPROFILE') or os.getenv('HOME') or '.'
		wcd = _("CSV files (*.csv)|*.csv|Text files (*.txt)|*.txt|All files (*.*)|*.*")
		
		export_dlg = wx.FileDialog(
			self, 
			message=_('Choose a file'), 
			defaultDir=home, 
			defaultFile='constants.csv', 
			wildcard=wcd, 
			style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
		)
		
		if export_dlg.ShowModal() != wx.ID_OK:
			export_dlg.Destroy()
			return

		fileName = export_dlg.GetPath()
		export_dlg.Destroy()

		try:
			with open(fileName, 'w', newline='') as csvfile:
				spamWriter = csv.writer(
					csvfile, 
					delimiter=',', 
					quotechar='"', 
					quoting=csv.QUOTE_MINIMAL
				)
				
				# Write header
				spamWriter.writerow(['Name', 'Value'])
				
				# Write data
				for row in range(self._grid.GetNumberRows()):
					name = self._grid.GetCellValue(row, 0)
					value = self._grid.GetCellValue(row, 1)
					if name:  # Only export non-empty rows
						spamWriter.writerow([name, value])

			wx.MessageBox(
				_('Export completed successfully!'), 
				_('Export Manager'), 
				wx.OK | wx.ICON_INFORMATION
			)

		except Exception as info:
			wx.MessageBox(
				_('Error exporting data: {}\n').format(info), 
				_('Export Error'), 
				wx.OK | wx.ICON_ERROR
			)

	def OnOk(self, evt):
		"""	Definition of constants in builtin and close dialog
		"""
		
		# Validation: vérifier qu'il n'y a pas de noms dupliqués
		names = []
		for row in range(self._grid.GetNumberRows()):
			const = self._grid.GetCellValue(row, 0).strip()
			if const:
				if const in names:
					wx.MessageBox(
						_('Duplicate constant name: "{}"').format(const), 
						_('Validation Error'), 
						wx.OK | wx.ICON_ERROR
					)
					self._grid.SetGridCursor(row, 0)
					self._grid.MakeCellVisible(row, 0)
					return
				names.append(const)

		for row in range(self._grid.GetNumberRows()):
			const = self._grid.GetCellValue(row, 0).strip()
			val = self._grid.GetCellValue(row, 1).strip()
			
			if const and val:
				try:
					# Try to evaluate as number
					self.data[const] = eval(val)
				except:
					# Keep as string
					self.data[const] = val

		if self.data:
			setattr(builtins, os.path.splitext(self.label)[0], self.data)
		elif os.path.splitext(self.label)[0] in builtins.__dict__:
			del builtins.__dict__[os.path.splitext(self.label)[0]]

		evt.Skip()

	def GetData(self):
		""" Return the constants stored in the grid as a dictionary.
		"""
		return self.data

	def OnCancel(self, evt):
		"""	Close dialog.
		"""
		self.EndModal(wx.ID_CANCEL)

	def OnHelp(self, event):
		""" Help message dialogue.
		"""
		help_text = _(
			"Constants Manager Help\n\n"
			"• Add: Create a new constant\n"
			"• Remove: Delete selected constant(s)\n"
			"• Import: Load constants from CSV file\n"
			"• Export: Save constants to CSV file\n\n"
			"Usage in your diagram:\n"
			"Access constants using: DiagramName['ConstantName']\n\n"
			"Example:\n"
			"If your diagram is 'MyModel' and you define a constant 'SPEED',\n"
			"use it as: MyModel['SPEED']"
		)
		
		dlg = wx.MessageDialog(
			self, 
			help_text, 
			_('Constants Manager - Help'), 
			wx.OK | wx.ICON_INFORMATION
		)
		dlg.ShowModal()
		dlg.Destroy()