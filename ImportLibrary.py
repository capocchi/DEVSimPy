# -*- coding: utf-8 -*-

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

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GLOBAL VARIABLES AND FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

### at the beginning to prevent with statement for python vetrsion <=2.5


import os
import sys
import shutil
import inspect
import wx
import wx.lib.dialogs
import wx.lib.filebrowsebutton as filebrowse
from wx.lib.mixins.listctrl import CheckListCtrlMixin, ListCtrlAutoWidthMixin
import wx.lib.dialogs
from concurrent.futures import ThreadPoolExecutor
 
from Utilities import checkURL, getDirectorySize, RecurseSubDirs, getPYFileListFromInit
from Decorators import BuzyCursorNotification

class CheckListCtrl(wx.ListCtrl, CheckListCtrlMixin, ListCtrlAutoWidthMixin):
	def __init__(self, *args, **kw):
		wx.ListCtrl.__init__(self, *args, **kw)
		ListCtrlAutoWidthMixin.__init__(self)
		
		if wx.VERSION_STRING >= '4.1.0':
			self.EnableCheckBoxes(True)
			self.IsChecked = self.IsItemChecked
		else:
			CheckListCtrlMixin.__init__(self)

		self.InsertColumn(0, _('Name'), width=140)
		self.InsertColumn(1, _('Size [Ko]'), width=80)
		self.InsertColumn(2, _('Repository'), width=90)
		self.InsertColumn(3, _('Path'), width=100)

		### for itemData
		self.map = {}

		if wx.VERSION_STRING < '4.0':
			self.SetStringItem = self.SetStringItem
			self.InsertStringItem = self.InsertStringItem
			font = wx.SystemSettings_GetFont(wx.SYS_SYSTEM_FONT)
		else:
			self.SetStringItem = self.SetItem
			self.InsertStringItem = self.InsertItem
			font = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT)

		self.SetFont(font)

	# 	self.Bind(wx.EVT_LIST_ITEM_CHECKED, self.OnCheck)
	# 	self.Bind(wx.EVT_LIST_ITEM_UNCHECKED, self.OnUnCheck)

	# def OnCheck(self, evt):
	# 	index = evt.GetItem().GetId()
	# 	self.CheckItem(index, True)

	# def OnUnCheck(self, evt):
	# 	index = evt.GetItem().GetId()
	# 	self.CheckItem(index, False)

	def AddItem(self, path, dName, check=False):
		""" Add item to the list
		"""

		index = self.InsertStringItem(100000000, dName) 
		self.SetStringItem(index, 1, str(getDirectorySize(path)) if os.path.exists(path) else '0')
		self.SetStringItem(index, 2, 'local' if not path.startswith('http') else 'web' )
		self.SetStringItem(index, 3, "..%s%s"%(os.sep,os.path.basename(DOMAIN_PATH) if path.startswith(DOMAIN_PATH) else path))
		
		self.CheckItem(index, check)

		self.SetData(index, path)
		self.SetItemData(index, index)

	def GetData(self, id):
		return self.map[id]

	def SetData(self, id, data):
		self.map.update({id:data})

	@BuzyCursorNotification
	def Populate(self, D={}):
		""" Populate the list
		"""
		for path, dName in D.items():
			self.AddItem(path, dName)

class DeleteBox(wx.Dialog):
	""" Delete box for libraries manager.
	"""
	def __init__(self, *args, **kwargs):
		""" Constructor.
		"""
		super(DeleteBox, self).__init__(*args, **kwargs)

		self.InitUI()
		self.SetSize((250, 200))
       
	def InitUI(self):

		pnl = wx.Panel(self)
		vbox = wx.BoxSizer(wx.VERTICAL)

		sb = wx.StaticBox(pnl, label='Delete?')
		sbs = wx.StaticBoxSizer(sb, orient=wx.VERTICAL)
		self.rb1 = wx.RadioButton(pnl, label=_('label'))
		self.rb2 = wx.RadioButton(pnl, label=_('label and files'))
		sbs.Add(self.rb1)
		sbs.Add(self.rb2)
		
		pnl.SetSizer(sbs)

		hbox2 = wx.BoxSizer(wx.HORIZONTAL)
		okButton = wx.Button(self, wx.ID_OK, label='Ok')
		closeButton = wx.Button(self, wx.ID_CANCEL, label='Close')
		hbox2.Add(okButton)
		hbox2.Add(closeButton, flag=wx.LEFT, border=5)

		vbox.Add(pnl, proportion=1,
			flag=wx.ALL|wx.EXPAND, border=5)
		vbox.Add(hbox2, flag=wx.ALIGN_CENTER|wx.TOP|wx.BOTTOM, border=10)

		self.SetSizer(vbox)

		self.Centre()

		### Widgets
#		txt = wx.StaticText(self, wx.NewIdRef(), _('What do you want to delete:'), (15, 10))
#		self.rb1 = wx.RadioButton(self, wx.NewIdRef() , _('label'), (20, 30))
#		self.rb2 = wx.RadioButton(self, wx.NewIdRef() , _('label and files'), (20, 55))
#		btn_cancel = wx.Button(self, wx.ID_CANCEL, pos = (35, 90), size = (80, -1))
#		btn_ok = wx.Button(self, wx.ID_OK, pos = (135, 90), size = (80, -1))

		### Sizers
#		hbox = wx.BoxSizer(wx.HORIZONTAL)
#		vbox = wx.BoxSizer(wx.VERTICAL)

		### And into Sizers
#		hbox.Add(btn_cancel, 1, wx.EXPAND|wx.ALIGN_CENTER)
#		hbox.Add(btn_ok, 1, wx.EXPAND|wx.ALIGN_CENTER)

#		vbox.Add(txt, 0, wx.ALIGN_TOP, 10)
#		vbox.Add(self.rb1, 1,wx.ALIGN_LEFT, 5)
#		vbox.Add(self.rb2, 1,wx.ALIGN_LEFT, 5)
#		vbox.Add(hbox, 1, wx.ALIGN_CENTER)

		### Set Sizer
#		self.SetSizer(vbox)

#		vbox.SetSizeHints(self)

#-------------------------------------------------------------------
class ImportLibrary(wx.Dialog):
	def __init__(self, *args, **kwargs):
		super(ImportLibrary, self).__init__(*args, **kwargs)

		### local copy
		self.parent = args[0]

		### selected item list
		self._selectedItem = {}

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

		### Check list of libraries
		self._cb = CheckListCtrl(parent=rightPanel, style=wx.LC_REPORT | wx.SUNKEN_BORDER|wx.LC_SORT_ASCENDING)
		
		try:
			if wx.Platform == '__WXMSW__':
				pool = ThreadPoolExecutor(3)
				future = pool.submit(self._cb.Populate, (D))
				future.done()
			else:
				### Populate Check List dynamicaly	
				with ThreadPoolExecutor(max_workers=5) as executor:
					executor.submit(self._cb.Populate, (D))
		except:
			self._cb.Populate(D)
			
		### Static box sizer
		#sbox = wx.StaticBox(leftPanel, -1, '')
		#vbox2 = wx.StaticBoxSizer(sbox, wx.VERTICAL) 

		### Box Sizer
		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox2 = wx.BoxSizer(wx.VERTICAL)
		hbox = wx.BoxSizer(wx.HORIZONTAL)
		hbox1 = wx.BoxSizer(wx.HORIZONTAL)

		### Buttons
		new = wx.Button(leftPanel, id = wx.ID_NEW, size=(120, -1))
		imp = wx.Button(leftPanel, wx.NewIdRef(), _('Import'), size=(120, -1))
		sel = wx.Button(leftPanel, id = wx.ID_SELECTALL, size=(120, -1))
		des = wx.Button(leftPanel, wx.NewIdRef(), _('Deselect All'), size=(120, -1))
		apply = wx.Button(rightPanel, id=wx.ID_OK, size=(100, -1))
		cancel = wx.Button(rightPanel, id=wx.ID_CANCEL, size=(100, -1))

		vbox2.Add(new, 0, wx.TOP|wx.LEFT, 6)
		vbox2.Add(imp, 0, wx.TOP|wx.LEFT, 6)
		#vbox2.Add((-1, 5))
		vbox2.Add(sel, 0, wx.TOP|wx.LEFT, 6)
		vbox2.Add(des, 0, wx.TOP|wx.LEFT, 6)

		hbox1.Add(cancel, 1,  wx.ALL|wx.ALIGN_CENTER, 2)
		hbox1.Add(apply, 1,  wx.ALL|wx.ALIGN_CENTER, 2)

		vbox.Add(self._cb, 1, wx.EXPAND | wx.TOP, 3)
		vbox.Add((-1, 10))
		vbox.Add(hbox1, 0.5, wx.ALL|wx.ALIGN_CENTER)
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
		self.Bind(wx.EVT_BUTTON, self.OnAdd, id = imp.GetId()) 
		self.Bind(wx.EVT_BUTTON, self.OnSelectAll, id = sel.GetId())
		self.Bind(wx.EVT_BUTTON, self.OnDeselectAll, id = des.GetId())
		self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnItemRightClick)
		self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

		self.Centre()
		self.Layout()

		### just for windows
		e = wx.SizeEvent(self.GetSize())
		self.ProcessEvent(e)

	def CheckDomainPath(self):
		ABS_HOME_PATH = os.path.abspath(os.path.dirname(sys.argv[0]))
		if os.path.join(ABS_HOME_PATH, "Domain") != DOMAIN_PATH:
			dlg = wx.MessageDialog(self, _("Local domain path is different from the .devsimpy.\nGo to options and preferences to change the domain path."), _('Import Manager'), wx.OK|wx.ICON_INFORMATION)
			dlg.ShowModal()
			dlg.Destroy()

	def OnSelectAll(self, event):
		num = self._cb.GetItemCount()
		for i in range(num):
			self._cb.CheckItem(i,True)

	def OnDeselectAll(self, event):
		num = self._cb.GetItemCount()
		for i in range(num):
			self._cb.CheckItem(i, False)

	def OnItemRightClick(self, evt):
		"""Launcher creates wxMenu.
		"""
		index = self._cb.GetFocusedItem()
		label = self._cb.GetItemText(index)

		menu = wx.Menu()

		doc = wx.MenuItem(menu, wx.NewIdRef(), _('Doc'), _('Documentation of item'))
		doc.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH_16_16,'doc.png')))
		menu.Append(doc)

		self.Bind(wx.EVT_MENU, self.OnDoc, id = doc.GetId())

		### delete option only for the export path
		if label in self._d:
			delete = wx.MenuItem(menu, wx.NewIdRef(), _('Delete'), _('Delete item'))
			delete.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH_16_16,'delete.png')))
			menu.Append(delete)
			self.Bind(wx.EVT_MENU, self.OnDelete, id=delete.GetId())

		try:
			self.PopupMenu(menu, evt.GetPosition())
		except AttributeError as info:
			self.PopupMenu(menu, evt.GetPoint())
		else:
			sys.stdout.write("Error in OnItemRightClick for ImportLibrary class.")

		menu.Destroy() # destroy to avoid mem leak

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
						doc += 	_("---------- %s module :\n")%fn+ \
								_("\tname : %s\n")%name+ \
								_("\tsuffix : %s\n")%suffix+ \
								_("\tmode : %s\n")%mode+ \
								_("\ttype of module : %s\n")%module_type+ \
								_("\tpath : %s\n\n")%fn_path
					else:
						doc +=_("----------%s module not inspectable !\n")%fn
			#else:
				#pass
				#doc += _("%s is empty !\n")%init_file
		#else:
			#pass
			#doc += _("%s dont exist !\n")%init_file

			### TODO take in charge also amd and cmd !

		return doc

	def OnDoc(self, evt):
		""" documentation of item has been invocked
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
				dial = wx.MessageDialog(None, _('Are you sure to delete python files into the %s directory?')%(label), label, wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
				
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

			self._cb.DeleteItem(index)

	def EvtCheckListBox(self, evt):
		index = self._cb.GetFocusedItem()
		label = self._cb.GetItemText(index)
		
		#met a jour le dico des elements selectionnes
		if self._cb.IsChecked(index) and label not in self._selectedItem:
			self._selectedItem.update({str(label):index})
		elif not self._cb.IsChecked(index) and label in self._selectedItem:
			del self._selectedItem[str(label)]

	@staticmethod
	def CreateInitFile(path):
		""" Static method to create the __init_.py file which contain the name of accessing models
		"""

		dial = wx.MessageDialog(None, _('If %s contain python files, do you want to insert it in __all__ variable of __init__.py file?')%os.path.basename(path), _('New file Manager'), wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION)
		if dial.ShowModal() == wx.ID_YES:
			### if there is python file in the importing directory
			L = [f for f in os.listdir(path) if f.endswith(".py")]
		else:
			L = []

		### how many python file to insert on __init__.py file
		if L:
			dlg = wx.lib.dialogs.MultipleChoiceDialog(None, _('List of python file in %s')%(os.path.dirname(path)), _('Select the python files to insert in the __init__.py file'), L)
			if dlg.ShowModal() == wx.ID_OK:
				select = dlg.GetValueString()
			else:
				select = []
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

	def OnNew(self, event):
		dlg1 = wx.TextEntryDialog(self, _('Enter new directory name'), _('New Library'), _("New_lib"))
		if dlg1.ShowModal() == wx.ID_OK:
			dName = dlg1.GetValue()
			path = os.path.join(DOMAIN_PATH, dName)
			if not os.path.exists(path):
				os.makedirs(path)
				f = open(os.path.join(path,'__init__.py'),'w')
				f.write("__all__=[\n]")
				f.close()
				self.DoAdd(path, dName)

			else:
				wx.MessageBox(_('Directory already exist.\nChoose another name.'), _('Information'), wx.OK | wx.ICON_INFORMATION)

		dlg1.Destroy()

	def DoAdd(self, path, dName):

		### ajout dans la liste box
		self._cb.AddItem(path, dName, True)

		### mise a jour du fichier .devsimpy
		if path not in self.parent.exportPathsList:
			self.parent.exportPathsList.append(str(path))
			self.parent.cfg.Write('exportPathsList', str(self.parent.exportPathsList))

		### ajout dans le dictionnaire pour recupere le chemin à l'insertion dans DEVSimPy (voir OnImport)
		self._d.update({dName:path})

		### create the __init__.py file if doesn't exist
		if not path.startswith('http') and not os.path.exists(os.path.join(path,'__init__.py')):
			dial = wx.MessageDialog(self, _('%s directory has no __init__.py file.\nDo you want to create it?')%path, _('New librarie Manager'), wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION)
			if dial.ShowModal() == wx.ID_YES:
				self.CreateInitFile(path)
			dial.Destroy()

	def OnAdd(self, evt):
		"""
		"""

		### Get path to add
		dialog = wx.DirDialog(self, "Choose a directory:",style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON)
		if dialog.ShowModal() == wx.ID_OK:
			path = dialog.GetPath()
		else:
			path = None
		dialog.Destroy()
		
		if path:
			dName = os.path.basename(path) if not path.startswith('http') else [a for a in path.split('/') if a!=''][-1]

			# si la lib n'est pas deja importee
			if not self.parent.tree.IsChildRoot(dName):
				if dName not in self._d or (dName in self._d and self._d[dName] != path):
					### si importation a partir du local
					if os.path.isdir(path):
						self.DoAdd(path, dName)
					### si importation à partir du web
					elif checkURL(path):
						self.DoAdd(path, dName)
					### gestion de l'erreur
					else:
						if path.startswith('http'):
							msg = _('%s is an invalid url')%path
						else:
							msg = _('%s directory does not exist')%dName
						dial = wx.MessageDialog(self, msg, _('New librarie manager'), wx.OK | wx.ICON_ERROR)
						dial.ShowModal()
				else:
					dial = wx.MessageDialog(self, _('%s is already imported!')%dName, _('New librarie manager'), wx.OK|wx.ICON_INFORMATION)
					dial.ShowModal()
			else:
				dial = wx.MessageDialog(self, _('%s is already imported!')%dName, _('New librarie manager'), wx.OK|wx.ICON_INFORMATION)
				dial.ShowModal()
				
	def OnCloseWindow(self, event):
		self.Destroy()
		event.Skip()

### ------------------------------------------------------------
class TestApp(wx.App):
	""" Testing application
	"""

	def OnInit(self):

		import builtins
		import gettext

		builtins.__dict__['HOME_PATH'] = os.getcwd()
		builtins.__dict__['DOMAIN_PATH'] = 'Domain'
		builtins.__dict__['_'] = gettext.gettext

		frame = ImportLibrary(None, size=(600,600), id=-1, title="Test")
		frame.Show()
		return True

	def OnQuit(self, event):
		self.Close()

if __name__ == '__main__':

	app = TestApp(0)
	app.MainLoop()
