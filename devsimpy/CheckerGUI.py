# -*- coding: utf-8 -*-


import wx
import os
import sys
import webbrowser
from tempfile import gettempdir
from traceback import format_exception
import inspect
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin, ColumnSorterMixin


if not hasattr(inspect, 'getargspec'):
	inspect.getargspec = inspect.getfullargspec
	
from Utilities import getTopLevelWindow, load_and_resize_image


_ = wx.GetTranslation


from Utilities import GetMails, getInstance
import Components



class VirtualList(wx.ListCtrl, ListCtrlAutoWidthMixin, ColumnSorterMixin):
	""" Virtual List of devs model checking """
	
	def __init__(self, parent, D):
		wx.ListCtrl.__init__(self, parent, -1, style=wx.LC_REPORT|wx.LC_VIRTUAL|wx.LC_HRULES|wx.LC_VRULES)
		
		self.parent = parent
		
		# Image list
		self.il = wx.ImageList(16, 16)
		self.sm_up = self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_GO_UP, wx.ART_TOOLBAR, (16,16)))
		self.sm_dn = self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_GO_DOWN, wx.ART_TOOLBAR, (16,16)))
		self.idx1 = self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_CROSS_MARK, wx.ART_TOOLBAR, (16,16)))
		self.idx2 = self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_TICK_MARK, wx.ART_TOOLBAR, (16,16)))
		self.SetImageList(self.il, wx.IMAGE_LIST_SMALL)
		
		# Colonnes
		self.InsertColumn(0, _('Name'), wx.LIST_FORMAT_CENTRE, width=120)
		self.InsertColumn(1, _('Error'), wx.LIST_FORMAT_CENTRE, width=450)
		self.InsertColumn(2, _('Line'), wx.LIST_FORMAT_CENTRE, width=80)
		self.InsertColumn(3, _('Authors'), wx.LIST_FORMAT_CENTRE, width=80)
		self.InsertColumn(4, _('Path'), wx.LIST_FORMAT_CENTRE, width=120)
		
		# Data
		self.itemDataMap = D
		self.itemIndexMap = list(D.keys())
		self.SetItemCount(len(D))
		
		# Mixins
		ListCtrlAutoWidthMixin.__init__(self)
		ColumnSorterMixin.__init__(self, self.GetColumnCount())
		
		# Sort by column 2
		self.SortListItems(2, 0)
		
		# Events
		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)
		self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
		self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected)
		self.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick)
		self.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick)
		self.Bind(wx.EVT_LEFT_DOWN, self.OnClick)
		self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnRightClick)
		
		self.currentItem = 0


	def GetListCtrl(self):
		"""Requis par ColumnSorterMixin"""
		return self


	def GetSortImages(self):
		"""Requis par ColumnSorterMixin"""
		return (self.sm_dn, self.sm_up)


	def OnColClick(self, event):
		event.Skip()


	def OnClick(self, event):
		# Deselect all items
		for x in range(self.GetItemCount()):
			self.Select(x, False)
		
		# Get selected item position
		x, y = event.GetPosition()
		row, _ = self.HitTest((x, y))
		
		if row >= 0:
			self.Select(row)
			model_name = self.getColumnText(row, 0)
			path = self.getColumnText(row, 4)
			
			tempdir = os.path.realpath(gettempdir())
			
			if tempdir in os.path.dirname(path):
				from AttributeEditor import AttributeEditor
				mainW = getTopLevelWindow()
				canvas = mainW.nb2.GetCurrentPage()
				diagram = canvas.GetDiagram()
				f = AttributeEditor(canvas.GetParent(), wx.NewIdRef(), diagram.GetShapeByLabel(model_name), canvas)
				f.Show()


	def OnItemSelected(self, event):
		self.currentItem = event.Index
		
	def OnRightClick(self, event):
		line_number = self.getColumnText(self.currentItem, 2)
		
		if line_number != "":
			menu = wx.Menu()
			
			edit = wx.MenuItem(menu, wx.NewIdRef(), _("Edit"), _("Edit the source code"))
			edit.SetBitmap(load_and_resize_image('edit.png'))
			report = wx.MenuItem(menu, wx.NewIdRef(), _("Report"), _("Report error by mail to the author"))
			report.SetBitmap(load_and_resize_image('mail.png'))
			
			menu.AppendItem(edit)
			menu.AppendItem(report)
			
			menu.Bind(wx.EVT_MENU, self.OnEditor, id=edit.GetId())
			menu.Bind(wx.EVT_MENU, self.OnReport, id=report.GetId())
			
			self.PopupMenu(menu, event.GetPoint())
			menu.Destroy()


	def OnEditor(self, event):
		self.OnDoubleClick(event)


	def OnReport(self, event):
		info = self.getColumnText(self.currentItem, 1)
		line = self.getColumnText(self.currentItem, 2)
		mails_list = eval(self.getColumnText(self.currentItem, 3))
		python_path = self.getColumnText(self.currentItem, 4)
		
		model_name = os.path.basename(python_path)
		
		mailto = mails_list[0] if mails_list else ""
		cc = ""
		for mail in mails_list[1:]:
			cc += '%s,' % mail
		
		body = _("Dear DEVSimPy developers, \n Error in %s, line %s :\n %s") % (model_name, line, info)
		subject = _("Error in %s DEVSimPy model") % (model_name)
		webbrowser.open_new("mailto:%s?subject=%s&cc=%s&body=%s" % (mailto, subject, cc, body))


	def OnItemDeselected(self, event):
		line_number = self.getColumnText(self.currentItem, 2)
		python_path = self.getColumnText(self.currentItem, 4)
		
		if line_number != "":
			devs = getInstance(Components.GetClass(python_path))
			if not isinstance(devs, tuple):
				self.SetItemImage(self.currentItem, self.idx2)


	def OnDoubleClick(self, event):
		line_number = self.getColumnText(self.currentItem, 2)
		python_path = self.getColumnText(self.currentItem, 4)
		
		if line_number != "":
			devscomp = Components.DEVSComponent()
			devscomp.setDEVSPythonPath(python_path)
			
			editor_frame = Components.DEVSComponent.OnEditor(devscomp, event)
			if editor_frame:
				nb = editor_frame.GetNoteBook()
				page = nb.GetCurrentPage()
				pos = int(line_number)
				page.GotoLine(pos)
		
		event.Skip()


	def OnItemActivated(self, event):
		self.currentItem = event.Index
	
	def getColumnText(self, index, col):
		item = self.GetItem(index, col)
		try:
			return item.GetItemLabelText()
		except:
			return item.GetText()


	def OnGetItemText(self, item, col):
		index = self.itemIndexMap[item]
		if col < len(self.itemDataMap[index]):
			s = str(self.itemDataMap[index][col])
		else:
			s = ""
		return s


	def OnGetItemImage(self, item):
		index = self.itemIndexMap[item]
		data = self.itemDataMap[index][2]
		
		if data == "":
			return self.idx2
		else:
			return self.idx1


	def SortItems(self, sorter):
		items = list(self.itemDataMap.keys())
		items.sort()
		self.itemIndexMap = items
		self.Refresh()


class CheckerGUI(wx.Frame):
	""" Class which report the code checking of python file """
	
	def __init__(self, parent, title, D):
		wx.Frame.__init__(self, parent, wx.NewIdRef(), title, size=(1000, 600), style=wx.DEFAULT_FRAME_STYLE)
		
		icon = wx.Icon()
		icon.CopyFromBitmap(load_and_resize_image("check_master.png"))
		self.SetIcon(icon)
		
		self.parent = parent
		self.fullData = D

		# Create toolbar with search control
		self.toolbar = self.CreateToolBar()
		self.search_ctrl = wx.SearchCtrl(self.toolbar, style=wx.TE_PROCESS_ENTER, size=(200, -1))
		self.search_ctrl.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.OnSearch)
		self.search_ctrl.Bind(wx.EVT_TEXT_ENTER, self.OnSearch)
		self.toolbar.AddControl(self.search_ctrl)
		self.toolbar.Realize()
		
		# Main panel pour un meilleur contrôle visuel
		panel = wx.Panel(self)
		
		# Prepare dictionary - IMPORTANT: créer la liste APRÈS le panel
		try:
			self.list = self.getList(D, panel)
		except:
			self.list = VirtualList(panel, D)
			sys.stdout.write(_('Alone mode for CheckerGUI: List of plugins is not generated from a diagram.\n'))
		
		# Sizers
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		listSizer = wx.BoxSizer(wx.VERTICAL)
		
		# Liste prend tout l'espace disponible
		listSizer.Add(self.list, 1, wx.EXPAND|wx.ALL, 5)
		
		# Barre de boutons - BoxSizer horizontal pour tous les boutons
		buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
		
		# Boutons personnalisés à gauche
		update_btn = wx.Button(panel, wx.ID_REFRESH, _("Update"))
		update_btn.SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_REDO, wx.ART_BUTTON))
		
		export_btn = wx.Button(panel, wx.NewIdRef(), _("Export"))
		export_btn.SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE_AS, wx.ART_BUTTON))
		
		buttonSizer.Add(update_btn, 0, wx.ALL, 5)
		buttonSizer.Add(export_btn, 0, wx.ALL, 5)
		
		# Espace flexible pour pousser les boutons OK/Close à droite
		buttonSizer.AddStretchSpacer(1)
		
		# Boutons standards à droite avec StdDialogButtonSizer
		stdButtonSizer = wx.StdDialogButtonSizer()
		
		ok_btn = wx.Button(panel, wx.ID_OK, _("OK"))
		ok_btn.SetDefault()
		close_btn = wx.Button(panel, wx.ID_CLOSE, _("Close"))
		
		stdButtonSizer.AddButton(close_btn)
		stdButtonSizer.AddButton(ok_btn)
		stdButtonSizer.SetAffirmativeButton(ok_btn)
		stdButtonSizer.SetCancelButton(close_btn)
		stdButtonSizer.Realize()
		
		buttonSizer.Add(stdButtonSizer, 0, wx.ALL, 5)
		
		# Assemblage final
		mainSizer.Add(listSizer, 1, wx.EXPAND)
		mainSizer.Add(buttonSizer, 0, wx.EXPAND|wx.ALL, 10)
		
		panel.SetSizer(mainSizer)
		
		self.Center()
		
		# Events
		self.Bind(wx.EVT_BUTTON, self.OnClose, id=wx.ID_CLOSE)
		self.Bind(wx.EVT_BUTTON, self.OnOK, id=wx.ID_OK)
		self.Bind(wx.EVT_BUTTON, self.OnUpdate, id=wx.ID_REFRESH)
		self.Bind(wx.EVT_BUTTON, self.OnExport, id=export_btn.GetId())


	def OnSearch(self, event):
		"""Recherche et filtre dans la liste"""
		search_text = self.search_ctrl.GetValue().lower().strip()
		
		if not search_text:
			# Si recherche vide, restaurer toutes les données
			self.list.itemDataMap = dict(self.fullData)
			self.list.itemIndexMap = list(self.fullData.keys())
			self.list.SetItemCount(len(self.fullData))
		else:
			# Filtrer les données selon le texte recherché
			filtered_data = {}
			for key, value in self.fullData.items():
				# Recherche dans toutes les colonnes
				name = str(value[0]).lower() if len(value) > 0 else ""
				error = str(value[1]).lower() if len(value) > 1 else ""
				line = str(value[2]).lower() if len(value) > 2 else ""
				authors = str(value[3]).lower() if len(value) > 3 else ""
				path = str(value[4]).lower() if len(value) > 4 else ""
				
				# Si le texte recherché est trouvé dans n'importe quelle colonne
				if (search_text in name or 
					search_text in error or 
					search_text in line or 
					search_text in authors or 
					search_text in path):
					filtered_data[key] = value
			
			# Réindexer les résultats filtrés
			new_data = dict(zip(range(len(filtered_data)), filtered_data.values()))
			
			# Mettre à jour la liste
			self.list.itemDataMap = new_data
			self.list.itemIndexMap = list(new_data.keys())
			self.list.SetItemCount(len(new_data))
		
		# Rafraîchir l'affichage
		self.list.Refresh()


	def getList(self, D, parent=None):
		"""parent parameter permet de spécifier le parent du VirtualList"""
		if parent is None:
			parent = self
		
		tempdir = os.path.realpath(gettempdir())
		
		L = []
		if D:
			for k, v in D.items():
				path = ""
				line = ""
				
				if tempdir in os.path.dirname(k.python_path):
					L.append((k.label, _("Temporary python file!"), "", "", k.python_path))
				elif v:
					typ, val, tb = v
					list_exc = format_exception(typ, val, tb)
					list_exc.reverse()
					
					for s in list_exc:
						if 'line ' in s:
							path, line = s.split(',')[0:2]
							break
					
					python_path = str(path.split(' ')[-1].strip())[1:-1]
					line_number = line.split(' ')[-1].strip()
					
					module = Components.BlockFactory.GetModule(python_path)
					doc = module.__doc__ or ""
					mails = GetMails(doc) if inspect.ismodule(module) else []
					
					L.append((k.label, str(val), line_number, mails, python_path))
		
		# Créer le dictionnaire des données
		data_dict = dict(zip(range(len(L)), L)) if L != [] else {}
		
		# Sauvegarder les données complètes pour le filtrage
		self.fullData = data_dict
		
		return VirtualList(parent, data_dict) if L != [] else L


	def OnUpdate(self, evt):
		if hasattr(self, 'diagram'):
			D = self.diagram.DoCheck()
			# Récupérer le panel parent existant
			panel = self.list.GetParent()
			L = self.getList(D, panel)
			
			if isinstance(L, VirtualList):
				old_list = self.list
				self.list = L
				
				# Récupérer le sizer du panel
				sizer = panel.GetSizer()
				listSizer = sizer.GetItem(0).GetSizer()
				
				listSizer.Hide(0)
				listSizer.Remove(0)
				listSizer.Add(self.list, 1, wx.EXPAND|wx.ALL, 5)
				
				old_list.Destroy()
				
				# Réinitialiser la recherche après mise à jour
				self.search_ctrl.SetValue("")
				
				panel.Layout()
			else:
				sys.stdout.write(_('List not updated!'))
		else:
			sys.stdout.write(_('Call the SetDiagram method to define the diagram object.'))

	def OnExport(self, event):
		"""Exporter la liste vers un fichier texte"""
		with wx.FileDialog(self, _("Save errors as..."), 
						  wildcard="Text files (*.txt)|*.txt",
						  style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
			if fileDialog.ShowModal() == wx.ID_CANCEL:
				return
			
			pathname = fileDialog.GetPath()
			try:
				with open(pathname, 'w', encoding='utf-8') as f:
					for i in range(self.list.GetItemCount()):
						name = self.list.getColumnText(i, 0)
						error = self.list.getColumnText(i, 1)
						line = self.list.getColumnText(i, 2)
						f.write(f"{name}: {error} (Line: {line})\n")
			except IOError:
				wx.LogError("Cannot save current data in file '%s'." % pathname)


	def SetDiagram(self, diagram):
		self.diagram = diagram


	def getList(self, D, parent=None):
		"""parent parameter permet de spécifier le parent du VirtualList"""
		if parent is None:
			parent = self
		
		tempdir = os.path.realpath(gettempdir())
		
		L = []
		if D:
			for k, v in D.items():
				path = ""
				line = ""
				
				if tempdir in os.path.dirname(k.python_path):
					L.append((k.label, _("Temporary python file!"), "", "", k.python_path))
				elif v:
					typ, val, tb = v
					list_exc = format_exception(typ, val, tb)
					list_exc.reverse()
					
					for s in list_exc:
						if 'line ' in s:
							path, line = s.split(',')[0:2]
							break
					
					python_path = str(path.split(' ')[-1].strip())[1:-1]
					line_number = line.split(' ')[-1].strip()
					
					module = Components.BlockFactory.GetModule(python_path)
					doc = module.__doc__ or ""
					mails = GetMails(doc) if inspect.ismodule(module) else []
					
					L.append((k.label, str(val), line_number, mails, python_path))
		
		return VirtualList(parent, dict(zip(range(len(L)), L))) if L != [] else L


	def OnUpdate(self, evt):
		if hasattr(self, 'diagram'):
			D = self.diagram.DoCheck()
			# Récupérer le panel parent existant
			panel = self.list.GetParent()
			L = self.getList(D, panel)
			
			if isinstance(L, VirtualList):
				old_list = self.list
				self.list = L
				
				# Récupérer le sizer du panel
				sizer = panel.GetSizer()
				listSizer = sizer.GetItem(0).GetSizer()
				
				listSizer.Hide(0)
				listSizer.Remove(0)
				listSizer.Add(self.list, 1, wx.EXPAND|wx.ALL, 5)
				
				old_list.Destroy()  # Nettoyer l'ancienne liste
				panel.Layout()
			else:
				sys.stdout.write(_('List not updated!'))
		else:
			sys.stdout.write(_('Call the SetDiagram method to define the diagram object.'))


	def OnClose(self, evt):
		self.Close()


	def OnOK(self, evt):
		self.Close()


if __name__ == '__main__':
	import subprocess
	test_file = 'test_checkergui.py'
	args = sys.argv[1:] or ['--autoclose']
	subprocess.call(['python', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tests', test_file)] + args)
