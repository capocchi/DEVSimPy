# -*- coding: utf-8 -*-


'''
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# ImportLibrary.py --- Importing library dialog
#                     --------------------------------
#                            Copyright (c) 2020
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 1.0                                      last modified:  15/03/20
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
'''


### at the beginning to prevent with statement for python vetrsion <=2.5


import os
import sys
import shutil


import inspect
if not hasattr(inspect, 'getargspec'):
	inspect.getargspec = inspect.getfullargspec
	
import wx
import wx.lib.dialogs


from wx.lib.mixins.listctrl import CheckListCtrlMixin, ListCtrlAutoWidthMixin
import wx.lib.dialogs
from concurrent.futures import ThreadPoolExecutor


_ = wx.GetTranslation
 
from Utilities import checkURL, getDirectorySize, getPYFileListFromInit, NotificationMessage, load_and_resize_image
from Decorators import BuzyCursorNotification
from config import ABS_HOME_PATH


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GLOBAL VARIABLES AND FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# CLASS DEFIINTION
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##


class CheckListCtrl(wx.ListCtrl, CheckListCtrlMixin, ListCtrlAutoWidthMixin):
	"""
	"""
	def __init__(self, *args, **kw):
		""" Constructor.
		"""
		wx.ListCtrl.__init__(self, *args, **kw)
		ListCtrlAutoWidthMixin.__init__(self)
		
		self.EnableCheckBoxes(True)
		self.IsChecked = self.IsItemChecked


		self.InsertColumn(0, _('Name'), width=140)
		self.InsertColumn(1, _('Size [Ko]'), width=80)
		self.InsertColumn(2, _('Repository'), width=90)
		self.InsertColumn(3, _('Path'), width=100)


		### for itemData
		self.map = {}
		
		self.SetStringItem = self.SetItem
		self.InsertStringItem = self.InsertItem
		font = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT)


		self.SetFont(font)


	###
	def AddItem(self, path, dName, check=False):
		""" Add item to the list.
		"""


		index = self.InsertStringItem(100000000, dName) 
		self.SetStringItem(index, 1, str(getDirectorySize(path)) if os.path.exists(path) else '0')
		self.SetStringItem(index, 2, 'local' if not path.startswith('http') else 'web' )
		self.SetStringItem(index, 3, "..%s%s"%(os.sep,os.path.basename(DOMAIN_PATH) if path.startswith(DOMAIN_PATH) else path))
		
		self.CheckItem(index, check)
		self.SetData(index, path)
		self.SetItemData(index, index)


	###
	def GetData(self, id):
		return self.map[id]


	###
	def SetData(self, id, data):
		self.map.update({id:data})


	@BuzyCursorNotification
	def Populate(self, D={}):
		""" Populate the list.
		"""
		for path, dName in D.items():
			self.AddItem(path, dName)


class DeleteBox(wx.Dialog):
	""" Delete box for libraries manager.
	"""


	###
	def __init__(self, *args, **kwargs):
		""" Constructor.
		"""
		super(DeleteBox, self).__init__(*args, **kwargs)


		self.InitUI()
		self.SetSize((250, 200))
		self.Centre() 
	
	###
	def InitUI(self):
		""" Init the user interface.
		"""


		panel = wx.Panel(self) 
		vbox = wx.BoxSizer(wx.VERTICAL) 
		nm = wx.StaticBox(panel, -1, 'Delete?') 
		nmSizer = wx.StaticBoxSizer(nm, wx.VERTICAL) 
		
		nmbox = wx.BoxSizer(wx.VERTICAL) 
		self.rb1 = wx.RadioButton(panel, label=_('label'))
		self.rb2 = wx.RadioButton(panel, label=_('label and files')) 
					
		nmbox.Add(self.rb1, 0, wx.ALL|wx.LEFT, 5)
		nmbox.Add(self.rb2, 0, wx.ALL|wx.LEFT, 5)  
		nmSizer.Add(nmbox, 0, wx.ALL|wx.EXPAND, 10)  


		hbox = wx.BoxSizer(wx.HORIZONTAL)
		okButton = wx.Button(panel, wx.ID_OK, label='Ok')
		closeButton = wx.Button(panel, wx.ID_CANCEL, label='Close')
	
		hbox.Add(closeButton, 0, wx.ALL|wx.LEFT, 10)
		hbox.Add(okButton, 0, wx.ALL|wx.LEFT, 10)


		vbox.Add(nmSizer,0, wx.ALL|wx.EXPAND, 5) 
		vbox.Add(hbox,0, wx.ALL|wx.CENTER, 5) 
		panel.SetSizer(vbox) 
		
		panel.Fit() 
	
#-------------------------------------------------------------------
class ImportLibrary(wx.Dialog):
	"""
	"""


	def __init__(self, *args, **kwargs):
		""" Constructor.
		"""
		super(ImportLibrary, self).__init__(*args, **kwargs)

		icon_bitmap = load_and_resize_image('properties.png')
		icon = wx.Icon()
		icon.CopyFromBitmap(icon_bitmap)
		self.SetIcon(icon)
		
		### local copy
		self.parent = args[0]

		### selected item list
		self._selectedItem = {}
		
		### Variables pour le filtrage
		self._all_items = []
		self._current_filter = ""

		### get libs from tree D (library)
		lst = [s for s in self.parent.tree.GetDomainList(DOMAIN_PATH) if not self.parent.tree.IsChildRoot(s)] if self.parent else []

		exportPathsList = self.parent.exportPathsList if self.parent else []

		### if lst is empty, perhaps DOMAIN_PATH is false
		if self.parent and lst == []:
			self.CheckDomainPath()

		### dic for name and path correspondance (for exported paths)
		self._d = {}
		for path in exportPathsList:
			name = os.path.basename(path)
			if not self.parent.tree.IsChildRoot(name):
				lst.append(name)
				self._d[name] = os.path.abspath(path)

		### dic building to populate with local and exported paths
		D = {}
		for v in lst:
			### path is on the domain dir by default
			path = os.path.join(DOMAIN_PATH, v)
			### else we find the path in the exportPathsList
			if not os.path.exists(path):
				for s in [p for p in self.parent.exportPathsList if v in p]:
					if os.path.isdir(s):
						path = s
					### update the exported path list
					else:
						path = None
						i = self.parent.exportPathsList.index(s)
						del self.parent.exportPathsList[i]

			if path: D[path] = v

		### Panels
		panel = wx.Panel(self, wx.NewIdRef())
		leftPanel = wx.Panel(panel, wx.NewIdRef())
		rightPanel = wx.Panel(panel, wx.NewIdRef())

		### Search panel at the top
		searchPanel = wx.Panel(rightPanel, wx.NewIdRef())
		searchBox = wx.BoxSizer(wx.HORIZONTAL)

		searchIcon = wx.StaticBitmap(searchPanel, wx.NewIdRef(),
									wx.ArtProvider.GetBitmap(wx.ART_FIND, wx.ART_OTHER, (16, 16)))
		searchLabel = wx.StaticText(searchPanel, label=_("Search:"))
		self.searchCtrl = wx.SearchCtrl(searchPanel, wx.NewIdRef(), size=(250, -1))
		self.searchCtrl.ShowCancelButton(True)
		self.searchCtrl.SetDescriptiveText(_("Filter by name or path..."))
		self.searchCtrl.SetToolTip(_("Type to filter libraries by name or path"))

		searchBox.Add(searchIcon, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
		searchBox.Add(searchLabel, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
		searchBox.Add(self.searchCtrl, 1, wx.EXPAND)
		searchPanel.SetSizer(searchBox)

		### Check list of libraries
		self._cb = CheckListCtrl(parent=rightPanel, style=wx.LC_REPORT | wx.SUNKEN_BORDER|wx.LC_SORT_ASCENDING)
		
		# Population synchrone (pas de threading pour éviter les problèmes)
		self._cb.Populate(D)
		
		# Sauvegarder tous les items immédiatement
		self._SaveAllItems()
			
		### Box Sizer
		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox2 = wx.BoxSizer(wx.VERTICAL)
		hbox = wx.BoxSizer(wx.HORIZONTAL)
		hbox1 = wx.BoxSizer(wx.HORIZONTAL)

		### Buttons with icons
		new = wx.Button(leftPanel, id = wx.ID_NEW, size=(135, -1))
		new.SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_NEW, wx.ART_BUTTON, (16, 16)))
		new.SetToolTip(_("Add a new library from local directory or URL"))

		sel = wx.Button(leftPanel, id = wx.ID_SELECTALL, size=(135, -1))
		sel.SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_TICK_MARK, wx.ART_BUTTON, (16, 16)))
		sel.SetToolTip(_("Select all visible libraries"))

		des = wx.Button(leftPanel, wx.NewIdRef(), _('Deselect All'), size=(135, -1))
		des.SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_CROSS_MARK, wx.ART_BUTTON, (16, 16)))
		des.SetToolTip(_("Deselect all visible libraries"))

		apply = wx.Button(rightPanel, id=wx.ID_OK, size=(100, -1))
		apply.SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_TICK_MARK, wx.ART_BUTTON, (16, 16)))
		apply.SetToolTip(_("Apply changes and close"))
		apply.SetDefault()

		cancel = wx.Button(rightPanel, id=wx.ID_CANCEL, size=(100, -1))
		cancel.SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_CLOSE, wx.ART_BUTTON, (16, 16)))
		cancel.SetToolTip(_("Cancel and close"))

		vbox2.Add(new, 0, wx.TOP|wx.LEFT, 6)
		vbox2.Add((-1, 5))
		vbox2.Add(sel, 0, wx.TOP|wx.LEFT, 6)
		vbox2.Add(des, 0, wx.TOP|wx.LEFT, 6)

		hbox1.Add(cancel, 1,  wx.ALL|wx.ALIGN_CENTER, 2)
		hbox1.Add(apply, 1,  wx.ALL|wx.ALIGN_CENTER, 2)

		vbox.Add(searchPanel, 0, wx.EXPAND | wx.ALL, 5)
		vbox.Add(self._cb, 1, wx.EXPAND | wx.TOP, 3)
		vbox.Add((-1, 10))
		vbox.Add(hbox1, 0, wx.ALL|wx.ALIGN_CENTER)
		vbox.Add((-1, 10))

		hbox.Add(rightPanel, 1, wx.EXPAND, 5, 5)
		hbox.Add(leftPanel, 0, wx.EXPAND | wx.RIGHT, 5, 5)
		hbox.Add((3, -1))

		### SetSizer
		leftPanel.SetSizer(vbox2)
		rightPanel.SetSizer(vbox)
		panel.SetSizer(hbox)

		##Binding Events
		self.Bind(wx.EVT_BUTTON, self.OnNew, id = new.GetId())
		self.Bind(wx.EVT_BUTTON, self.OnSelectAll, id = sel.GetId())
		self.Bind(wx.EVT_BUTTON, self.OnDeselectAll, id = des.GetId())
		self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnItemRightClick)
		self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
		
		### Binding pour la recherche
		self.Bind(wx.EVT_TEXT, self.OnSearch, id=self.searchCtrl.GetId())
		self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnSearchCancel, id=self.searchCtrl.GetId())

		self.Centre()
		self.Layout()

		### just for windows
		e = wx.SizeEvent(self.GetSize())
		self.ProcessEvent(e)


	def _SaveAllItems(self):
		"""Save all items from the list for filtering"""
		# Ne sauvegarder que si la liste n'est pas déjà sauvegardée
		if self._all_items:
			return
		
		self._all_items = []
		num = self._cb.GetItemCount()
		
		for i in range(num):
			try:
				id_data = self._cb.GetItemData(i)
				item_data = {
					'name': self._cb.GetItemText(i, 0),
					'size': self._cb.GetItemText(i, 1),
					'repo': self._cb.GetItemText(i, 2),
					'path': self._cb.GetItemText(i, 3),
					'checked': self._cb.IsChecked(i),
					'full_path': self._cb.GetData(id_data) if (id_data is not None and id_data in self._cb.map) else None
				}
				self._all_items.append(item_data)
			except Exception as e:
				sys.stderr.write(f"Error saving item {i}: {str(e)}\n")

	###
	def _UpdateCheckedState(self):
		"""Update checked state in _all_items from current list"""
		# Créer un dictionnaire pour accès rapide
		checked_dict = {}
		num = self._cb.GetItemCount()
		
		for i in range(num):
			name = self._cb.GetItemText(i, 0)
			checked_dict[name] = self._cb.IsChecked(i)
		
		# Mettre à jour _all_items
		for item in self._all_items:
			if item['name'] in checked_dict:
				item['checked'] = checked_dict[item['name']]


	###
	def OnSearch(self, event):
		"""Filter libraries based on search text"""
		search_text = self.searchCtrl.GetValue().lower()
		self._current_filter = search_text
		
		# Sauvegarder l'état actuel des checkboxes avant de rafraîchir
		self._UpdateCheckedState()
		
		# Vider la liste
		self._cb.DeleteAllItems()
		
		# Repeupler avec les éléments filtrés
		visible_count = 0
		for item in self._all_items:
			name = item['name'].lower()
			path_display = item['path'].lower() if item['path'] else ""
			full_path = item['full_path'].lower() if item['full_path'] else ""
			
			# Vérifier si le texte de recherche correspond
			if not search_text or search_text in name or search_text in path_display or search_text in full_path:
				index = self._cb.InsertStringItem(100000000, item['name'])
				self._cb.SetStringItem(index, 1, item['size'])
				self._cb.SetStringItem(index, 2, item['repo'])
				self._cb.SetStringItem(index, 3, item['path'])
				self._cb.CheckItem(index, item['checked'])
				
				if item['full_path']:
					self._cb.SetData(index, item['full_path'])
					self._cb.SetItemData(index, index)
				
				visible_count += 1
		
		# Mettre à jour le titre avec le nombre de résultats
		if search_text:
			total = len(self._all_items)
			self.SetTitle(_("Import Library Manager - %d/%d libraries") % (visible_count, total))
		else:
			self.SetTitle(_("Import Library Manager"))


	###
	def OnSearchCancel(self, event):
		"""Reset search when cancel button is clicked"""
		self.searchCtrl.SetValue("")
		self._current_filter = ""
		
		# Sauvegarder l'état des checkboxes
		self._UpdateCheckedState()
		
		# Restaurer tous les items
		self.OnSearch(event)


	###
	def CheckDomainPath(self):
		"""
		"""
		if os.path.join(ABS_HOME_PATH, "Domain") != DOMAIN_PATH:
			dlg = wx.MessageDialog(self, _("Local domain path is different from the .devsimpy.\n\
				Go to options and preferences to change the domain path."), _('Import Manager'), wx.OK|wx.ICON_INFORMATION)
			dlg.ShowModal()
			dlg.Destroy()


	###
	def OnSelectAll(self, event):
		"""Select all visible items"""
		num = self._cb.GetItemCount()
		for i in range(num):
			self._cb.CheckItem(i, True)
		
		# Mettre à jour aussi dans _all_items
		self._UpdateCheckedState()


	###
	def OnDeselectAll(self, event):
		"""Deselect all visible items"""
		num = self._cb.GetItemCount()
		for i in range(num):
			self._cb.CheckItem(i, False)
		
		# Mettre à jour aussi dans _all_items
		self._UpdateCheckedState()


	###
	def OnItemRightClick(self, evt):
		"""Launcher creates wxMenu.
		"""
		index = self._cb.GetFocusedItem()
		label = self._cb.GetItemText(index)


		menu = wx.Menu()


		doc = wx.MenuItem(menu, wx.NewIdRef(), _('Doc'), _('Documentation of item'))
		doc.SetBitmap(load_and_resize_image('doc.png'))
		menu.Append(doc)


		self.Bind(wx.EVT_MENU, self.OnDoc, id = doc.GetId())


		### delete option only for the export path
		if label in self._d:
			delete = wx.MenuItem(menu, wx.NewIdRef(), _('Delete'), _('Delete item'))
			delete.SetBitmap(load_and_resize_image('delete.png'))
			menu.Append(delete)
			self.Bind(wx.EVT_MENU, self.OnDelete, id=delete.GetId())


		try:
			self.PopupMenu(menu, evt.GetPosition())
		except AttributeError as info:
			self.PopupMenu(menu, evt.GetPoint())
		else:
			sys.stdout.write("Error in OnItemRightClick for ImportLibrary class.")


		menu.Destroy() # destroy to avoid mem leak


	###
	def DocDirectory(self, path):
		""" Return doc of all modules composing path directory by reading its __ini__.py
		"""
		### init_file at first level !
		init_file = os.path.join(path, '__init__.py')


		doc = ""
		### if init_file exists in module
		if os.path.exists(init_file):
			### get list of content filename
			lst = getPYFileListFromInit(init_file)
			if lst:
				# for each python filename, inspect its module info
				for fn in lst:
					fn_path = os.path.join(path,fn+'.py')
					t = inspect.getmoduleinfo(fn_path)
					if t is not None:
						name, suffix, mode, module_type = t
						doc +=  _("---------- %s module:\n")%fn+ \
								_("\tname: %s\n")%name+ \
								_("\tsuffix: %s\n")%suffix+ \
								_("\tmode: %s\n")%mode+ \
								_("\ttype of module: %s\n")%module_type+ \
								_("\tpath: %s\n\n")%fn_path
					else:
						doc +=_("----------%s module not inspectable!\n")%fn


			### TODO take in charge also amd and cmd !


		return doc


	###
	def OnDoc(self, evt):
		""" Documentation of item has been invocked.
		"""
		index = self._cb.GetFocusedItem()
		label = self._cb.GetItemText(index)
		id = self._cb.GetItemData(index)
		path = self._cb.GetData(id)


		doc = "---------- %s Directory ----------\n\n"%label
		doc += self.DocDirectory(path)


		for root, dirs, files in os.walk(path):
			if not root.startswith('.'):
				doc += "---------- %s Sub-Directory ----------\n\n"%os.path.basename(root)
				doc += self.DocDirectory(root)


		d = wx.lib.dialogs.ScrolledMessageDialog(self, doc, _("Documentation of library %s")%label, style=wx.OK|wx.ICON_EXCLAMATION|wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
		d.CenterOnParent(wx.BOTH)
		d.ShowModal()


	###
	def OnDelete(self, evt):
		""" Delete Button has been clicked.
		"""
		index = self._cb.GetFocusedItem()
		label = self._cb.GetItemText(index)


		### diag to choose to delete label and/or source files
		db = DeleteBox(self, wx.NewIdRef(), _("Delete Options"))


		if db.ShowModal() == wx.ID_OK:


			### delete files
			if db.rb2.GetValue():
				dial = wx.MessageDialog(None, _('Are you sure to delete python files into the %s directory?')%(label), _("Delete Directory"), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
				
				if dial.ShowModal() == wx.ID_YES:
					try:
						### delete directory
						shutil.rmtree(self._d[label])
					except Exception as info:
						sys.stdout.write(_("%s not deleted!\n Error: %s")%(label,info))


				dial.Destroy()


			### update .devsimpy
			if label in self._d:
				try:
					del self.parent.exportPathsList[self.parent.exportPathsList.index(str(self._d[label]))]
					del self._d[label]
					self.parent.cfg.Write('exportPathsList', str(self.parent.exportPathsList))
				except Exception:
					pass


			# Mettre à jour _all_items
			self._all_items = [item for item in self._all_items if item['name'] != label]
			
			self._cb.DeleteItem(index)
			
			# Mettre à jour le titre si filtré
			if self._current_filter:
				visible = self._cb.GetItemCount()
				total = len(self._all_items)
				self.SetTitle(_("Import Library Manager - %d/%d libraries") % (visible, total))


	###
	def EvtCheckListBox(self, evt):
		"""
		"""
		index = self._cb.GetFocusedItem()
		label = self._cb.GetItemText(index)
		
		#met a jour le dico des elements selectionnes
		if self._cb.IsChecked(index) and label not in self._selectedItem:
			self._selectedItem.update({str(label):index})
		elif not self._cb.IsChecked(index) and label in self._selectedItem:
			del self._selectedItem[str(label)]


	@staticmethod
	def CreateInitFile(path):
		""" Static method to create the __init_.py file which contain the name of accessing models.
		"""


		dial = wx.MessageDialog(None, _('If %s contain python files, do you want to insert it in __all__ variable of __init__.py file?')%os.path.basename(path), _('New file Manager'), wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION)
		### if there is python file in the importing directory
		L = [f for f in os.listdir(path) if f.endswith(".py")] if dial.ShowModal() == wx.ID_YES else []


		### how many python file to insert on __init__.py file
		if L:
			dlg = wx.lib.dialogs.MultipleChoiceDialog(None, _('List of python file in %s')%(os.path.dirname(path)), _('Select the python files to insert in the __init__.py file'), L)
			select = dlg.GetValueString() if dlg.ShowModal() == wx.ID_OK else []
			dlg.Destroy()
		else:
			select = []


		### if path exist, we create the __init__.py file with __all__ empty
		if os.path.isdir(path):
			with open(os.path.join(path, '__init__.py'), 'w') as f:
				f.write("__all__ = [ \n")
				for fn in select:
					name, ext = fn.split('.')
					f.write("\t\t'%s', \n"%name)
				f.write('\t\t ]')


	###
	def OnNew(self, event):
		"""
		"""
		### Get path to add
		dialog = wx.DirDialog(self, _("Choose a new directory:"), DOMAIN_PATH, style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON)
		path = dialog.GetPath() if dialog.ShowModal() == wx.ID_OK else None
		dialog.Destroy()


		if path:
			# Getting the list of directories 
			dir = os.listdir(path) 
  
			# Checking if the list is empty or not 
			if len(dir) == 0:
				if not '__init__.py' in dir:
					ImportLibrary.CreateInitFile(path)


				self.DoAdd(path, os.path.basename(path))
				
			### selected directory exist, we import it
			else:
				dName = os.path.basename(path) if not path.startswith('http') else [a for a in path.split('/') if a!=''][-1]


				if dName not in self._d or (dName in self._d and self._d[dName] != path):
					### import form local or web
					if os.path.isdir(path) or checkURL(path):
						self.DoAdd(path, dName)
					### error
					else:
						msg = _('%s is an invalid url')%path if path.startswith('http') else _('%s directory does not exist')%dName
						dial = wx.MessageDialog(self, msg, _('New librarie manager'), wx.OK | wx.ICON_ERROR)
						dial.ShowModal()
				else:
					dial = wx.MessageDialog(self, _('%s is already imported!')%dName, _('New librarie manager'), wx.OK|wx.ICON_INFORMATION)
					dial.ShowModal()


	###
	def DoAdd(self, path, dName):
		"""
		"""
		# Ajouter l'item à la sauvegarde
		item_data = {
			'name': dName,
			'size': str(getDirectorySize(path)) if os.path.exists(path) else '0',
			'repo': 'local' if not path.startswith('http') else 'web',
			'path': "..%s%s"%(os.sep,os.path.basename(DOMAIN_PATH) if path.startswith(DOMAIN_PATH) else path),
			'checked': True,
			'full_path': path
		}
		self._all_items.append(item_data)
		
		# Ajouter dans la liste visible (si correspond au filtre)
		search_text = self._current_filter.lower()
		if not search_text or search_text in dName.lower() or search_text in path.lower():
			self._cb.AddItem(path, dName, True)


		### mise a jour du fichier .devsimpy
		if path not in self.parent.exportPathsList:
			self.parent.exportPathsList.append(str(path))
			self.parent.cfg.Write('exportPathsList', str(self.parent.exportPathsList))
		
		### ajout dans le dictionnaire pour recupere le chemin à l'insertion dans DEVSimPy (voir OnImport)
		self._d.update({dName:path})


		### create the __init__.py file if doesn't exist
		if not path.startswith('http') and (not os.path.exists(os.path.join(path,'__init__.py') and len(os.listdir(path)) == 0)):
			dial = wx.MessageDialog(self, _('%s directory has no __init__.py file.\nDo you want to create it?')%path, _('New librarie Manager'), wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION)
			if dial.ShowModal() == wx.ID_YES:
				ImportLibrary.CreateInitFile(path)
			dial.Destroy()
		
		NotificationMessage(_('Information'), _("Library %s has been successfully added!")%dName, self, timeout=5)
		
		# Mettre à jour le titre
		if self._current_filter:
			visible = self._cb.GetItemCount()
			total = len(self._all_items)
			self.SetTitle(_("Import Library Manager - %d/%d libraries") % (visible, total))


	###
	def OnAdd(self, evt):
		"""
		"""
		self.OnNew(evt)


	###     
	def OnCloseWindow(self, event):
		"""
		"""
		self.Destroy()
		event.Skip()
