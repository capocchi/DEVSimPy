# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# ImportLibrary.py --- Importing library dialog
#                     --------------------------------
#                                Copyright (c) 2009
#                                 Laurent CAPOCCHI
#                               University of Corsica
#                     --------------------------------
# Version 3.1                                      last modified:  15/04/09
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

### at the beginning to prevent with statement for python version <= 2.5
from __future__ import with_statement
import os
import sys
import shutil
import inspect

import wx.lib.dialogs
import wx.lib.filebrowsebutton as filebrowse
import wx.aui
import wx
from wx.lib.mixins.listctrl import CheckListCtrlMixin, ListCtrlAutoWidthMixin
import Core.Components.Decorators as Decorators

import Core.Utilities.Utilities as Utilities


class CheckListCtrl(wx.ListCtrl, CheckListCtrlMixin, ListCtrlAutoWidthMixin):
	def __init__(self, parent):
		wx.ListCtrl.__init__(self, parent, wx.ID_ANY, style=wx.LC_REPORT | wx.SUNKEN_BORDER)
		CheckListCtrlMixin.__init__(self)
		ListCtrlAutoWidthMixin.__init__(self)

		font = wx.SystemSettings_GetFont(wx.SYS_SYSTEM_FONT)

		self.InsertColumn(0, _('Name'), width=140)
		self.InsertColumn(1, _('Size (Ko)'), width=100)
		self.InsertColumn(2, _('Repository'), width=100)
		self.InsertColumn(3, _('Path'), width=100)
		self.SetFont(font)

		### for itemData
		self.map = {}

	def AddItem(self, path, dName):
		""" Add item to the list
		"""
		index = self.InsertStringItem(sys.maxint, dName)
		self.SetStringItem(index, 1, str(Utilities.getDirectorySize(path)) if os.path.exists(path) else '0')
		self.SetStringItem(index, 2, 'local' if not path.startswith('http') else 'web')
		self.SetStringItem(index, 3, "..%s%s" % (
		os.sep, os.path.basename(DOMAIN_PATH) if os.path.basename(DOMAIN_PATH) in path else os.path.basename(path)))
		self.SetData(index, path)
		self.SetItemData(index, index)

	def GetData(self, id):
		return self.map[id]

	def SetData(self, id, data):
		self.map.update({id: data})

	@Decorators.BuzyCursorNotification
	def Populate(self, D=None):
		""" Populate the list
		"""
		if not D: D = {}
		for path, dName in D.items():
			self.AddItem(path, dName)


class DeleteBox(wx.Dialog):
	""" Delete Box for libraires Manager.
	"""

	def __init__(self, *args, **kwargs):
		""" Constructor.
		"""
		wx.Dialog.__init__(self, *args, **kwargs)

		### Widgets
		txt = wx.StaticText(self, wx.ID_ANY, _('You want to delete:'), (15, 10))
		self.rb1 = wx.RadioButton(self, wx.ID_ANY, _('label'), (20, 30))
		self.rb2 = wx.RadioButton(self, wx.ID_ANY, _('label and files'), (20, 55))
		btn_cancel = wx.Button(self, wx.ID_CANCEL, pos=(35, 90), size=(80, -1))
		btn_ok = wx.Button(self, wx.ID_OK, pos=(135, 90), size=(80, -1))

		### Sizers
		hbox = wx.BoxSizer(wx.HORIZONTAL)
		vbox = wx.BoxSizer(wx.VERTICAL)

		### And into Sizers
		hbox.Add(btn_cancel, 1, wx.EXPAND | wx.ALIGN_CENTER)
		hbox.Add(btn_ok, 1, wx.EXPAND | wx.ALIGN_CENTER)

		vbox.Add(txt, 0, wx.ALIGN_TOP, 10)
		vbox.Add(self.rb1, 1, wx.ALIGN_LEFT, 5)
		vbox.Add(self.rb2, 1, wx.ALIGN_LEFT, 5)
		vbox.Add(hbox, 1, wx.ALIGN_CENTER)

		### Set Sizer
		self.SetSizer(vbox)

		self.Centre()

#-------------------------------------------------------------------
class ImportLibrary(wx.Dialog):
	def __init__(self, *args, **kwargs):
		wx.Dialog.__init__(self, *args, **kwargs)

		#local copy
		self.parent = args[0]

		###list des item selectionnes
		self._selectedItem = {}

		### recuperation des lib a partir du dico D du tree (library)
		lst = filter(lambda s: not self.parent.tree.IsChildRoot(s), self.parent.tree.GetDomainList(DOMAIN_PATH)) if self.parent else []

		exportPathsList = self.parent.exportPathsList if self.parent else []
		
		### if lst is empty, perhaps DOMAIN_PATH is false
		if not lst:
			self.CheckDomainPath()

		### Dico pour correspondance entre nom et path pour les exported path
		self._d = {}
		for path in exportPathsList:
			name = os.path.basename(path)
			if not self.parent.tree.IsChildRoot(name):
				lst.append(name)
				self._d[name] = os.path.abspath(path)

		### construction du dico pour populate aves les paths local et exportes
		D = {}
		for v in lst:
			### path is on the domain dir by default
			path = os.path.join(DOMAIN_PATH, v)
			### else we find the path in the exportPathsList
			if not os.path.exists(path):
				for s in filter(lambda p: v in p, self.parent.exportPathsList):
					if os.path.isdir(s):
						path = v
					### update the exported path list
					else:
						path = None
						i = self.parent.exportPathsList.index(s)
						del self.parent.exportPathsList[i]

			if path: D[path] = v

		### Panels
		panel = wx.Panel(self, wx.ID_ANY)
		leftPanel = wx.Panel(panel, wx.ID_ANY)
		rightPanel = wx.Panel(panel, wx.ID_ANY)

		### check list of libraries
		self._cb = CheckListCtrl(rightPanel)
		### Populate Check List dynamicaly
		wx.CallAfter(self._cb.Populate, D)

		### Box Sizer
		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox2 = wx.BoxSizer(wx.VERTICAL)
		hbox = wx.BoxSizer(wx.HORIZONTAL)
		hbox1 = wx.BoxSizer(wx.HORIZONTAL)

		### Buttons
		self._dbb = filebrowse.DirBrowseButton(rightPanel, wx.ID_ANY, startDirectory=HOME_PATH, labelText=_("New"), changeCallback=self.OnChange)
		self._btn_Add = wx.Button(rightPanel, id=wx.ID_ADD)
		self._btn_Add.Enable(False)
		sel = wx.Button(leftPanel, id=wx.ID_SELECTALL, size=(100, -1))
		des = wx.Button(leftPanel, wx.ID_ANY, _('Deselect All'), size=(100, -1))
		apply = wx.Button(leftPanel, id=wx.ID_OK, size=(100, -1))

		### Set Sizer
		hbox1.Add(self._dbb, 1, wx.EXPAND)
		hbox1.Add(self._btn_Add, 0, wx.RIGHT | wx.CENTER, 3)

		vbox2.Add(sel, 0, wx.TOP, 2)
		vbox2.Add(des, 0, wx.TOP, 2)
		#vbox2.Add((-1, 300))
		vbox2.Add(apply, 0, wx.TOP, 2)

		vbox.Add(self._cb, 1, wx.EXPAND | wx.TOP, 3)
		vbox.Add((-1, 10))
		vbox.Add(hbox1, 0.5, wx.EXPAND)
		vbox.Add((-1, 10))

		hbox.Add(rightPanel, 1, wx.EXPAND, 5)
		hbox.Add(leftPanel, 0, wx.EXPAND | wx.RIGHT)
		hbox.Add((3, -1))

		### SetSizer
		leftPanel.SetSizer(vbox2)
		rightPanel.SetSizer(vbox)
		panel.SetSizer(hbox)

		##Binding Events
		self.Bind(wx.EVT_BUTTON, self.OnSelectAll, id=sel.GetId())
		self.Bind(wx.EVT_BUTTON, self.OnDeselectAll, id=des.GetId())
		self.Bind(wx.EVT_BUTTON, self.OnAdd, self._btn_Add)
		self.Bind(wx.EVT_CHECKLISTBOX, self.EvtCheckListBox, self._cb)
		self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnItemRightClick)

		self.Centre()
		self.Layout()

		### just for windows
		e = wx.SizeEvent(self.GetSize())
		self.ProcessEvent(e)

	def CheckDomainPath(self):
		ABS_HOME_PATH = os.path.abspath(os.path.dirname(sys.argv[0]))
		if os.path.join(ABS_HOME_PATH, "Domain") != DOMAIN_PATH:
			dlg = wx.MessageDialog(self, _("Local domain path is different from the .devsimpy.\nGo to options and preferences to change the domain path."), 'Info', wx.OK | wx.ICON_INFORMATION)
			dlg.ShowModal()
			dlg.Destroy()

	def OnSelectAll(self, event):
		num = self._cb.GetItemCount()
		for i in range(num):
			self._cb.CheckItem(i)

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

		doc = wx.MenuItem(menu, wx.NewId(), _('Doc'), _('Documentation of item'))
		doc.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH_16_16, 'doc.png')))
		menu.AppendItem(doc)
		wx.EVT_MENU(self, doc.GetId(), self.OnDoc)

		### delete option only for the export path
		if label in self._d:
			delete = wx.MenuItem(menu, wx.NewId(), _('Delete'), _('Delete item'))
			delete.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH_16_16, 'delete.png')))
			menu.AppendItem(delete)
			wx.EVT_MENU(self, delete.GetId(), self.OnDelete)

		self.PopupMenu(menu, evt.GetPosition())
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
			lst = Utilities.getFileListFromInit(init_file)
			if lst:
				# for each python filename, inspect its module info
				for fn in lst:
					fn_path = os.path.join(path, fn + '.py')
					t = inspect.getmoduleinfo(fn_path)
					if t is not None:
						name, suffix, mode, module_type = t
						doc += _("---------- %s module :\n") % fn + \
							   _("\tname : %s\n") % name + \
							   _("\tsuffix : %s\n") % suffix + \
							   _("\tmode : %s\n") % mode + \
							   _("\ttype of module : %s\n") % module_type + \
							   _("\tpath : %s\n\n") % fn_path
					else:
						doc += _("----------%s module not inspectable !\n") % fn
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

		doc = "---------- %s Directory ----------\n\n" % label
		doc += self.DocDirectory(path)

		for root, dirs, files in os.walk(path):
			if not root.startswith('.'):
				doc += "---------- %s Sub-Directory ----------\n\n" % os.path.basename(root)
				doc += self.DocDirectory(root)

		d = wx.lib.dialogs.ScrolledMessageDialog(self, doc, _("Documentation of %s library") % label)
		d.CenterOnParent(wx.BOTH)
		d.ShowModal()

	def OnDelete(self, evt):
		""" Delete Button has been clicked.
		"""
		index = self._cb.GetFocusedItem()
		label = self._cb.GetItemText(index)

		### box pour choix de suppression du label ou du lable+des fichiers du package
		db = DeleteBox(self, -1, _("Delete Options"), size=(250, 110))

		if db.ShowModal() == wx.ID_OK:

			### suppresion des fichiers sur le disque
			if db.rb2.GetValue():
				dial = wx.MessageDialog(None, _('Are you sure to delete python files into the %s directory?') % label,
										_('Question'), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
			if dial.ShowModal() == wx.ID_YES:
				try:
					### delete directory
					shutil.rmtree(self._d[label])
				except Exception, info:
					sys.stdout.write(_("%s not deleted !\n Error : %s") % (label, info))

			dial.Destroy()

			# mise a jour du fichier .devsimpy
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
		if self._cb.IsChecked(index) and not self._selectedItem.has_key(label):
			self._selectedItem.update({str(label): index})
		elif not self._cb.IsChecked(index) and self._selectedItem.has_key(label):
			del self._selectedItem[str(label)]

	def OnChange(self, evt):
		self._btn_Add.Enable(True)

	@staticmethod
	def CreateInitFile(path):
		""" Static method to create the __init_.py file which contain the name of accessing models
		"""

		dial = wx.MessageDialog(None, _(
			'If %s contain python files, do you want to insert it in __all__ variable of __init__.py file?') % os.path.basename(
			path), 'Question', wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION)
		if dial.ShowModal() == wx.ID_YES:
			### if there is python file in the importing directory
			L = filter(lambda f: f.endswith(".py"), os.listdir(path))
		else:
			L = []

		### how many python file to insert on __init__.py file
		if L:
			dlg = wx.lib.dialogs.MultipleChoiceDialog(None, _('List of python file in %s') % (os.path.dirname(path)),
													  _('Select the python files to insert in the __init__.py file'), L)
			if dlg.ShowModal() == wx.ID_OK:
				select = dlg.GetValueString()
			else:
				select = []
			dlg.Destroy()

		### if path exist, we create the __init__.py file with __all__ empty
		if os.path.isdir(path):
			with open(os.path.join(path, '__init__.py'), 'w') as f:
				f.write("__all__ = [ \n")
				for fn in select:
					name, ext = fn.split('.')
					f.write("\t\t'%s', \n" % name)
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
		self._cb.AddItem(path, dName)

		### mise a jour du fichier .devsimpy
		if path not in self.parent.exportPathsList:
			self.parent.exportPathsList.append(str(path))
			self.parent.cfg.Write('exportPathsList', str(self.parent.exportPathsList))

		### ajout dans le dictionnaire pour recupere le chemin a l'insertion dans DEVSimPy (voir OnImport)
		self._d.update({dName: path})

		### create the __init__.py file if doesn't exist
		if not path.startswith('http') and not os.path.exists(os.path.join(path, '__init__.py')):
			dial = wx.MessageDialog(self, _('%s directory has no __init__.py file.\nDo you want to create it?') % path,
									'Question', wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION)
			if dial.ShowModal() == wx.ID_YES:
				self.CreateInitFile(path)
			dial.Destroy()

	def OnAdd(self, evt):

		path = self._dbb.GetValue()
		dName = os.path.basename(path) if not path.startswith('http') else filter(lambda a: a != '', path.split('/'))[-1]

		# si la lib n'est pas deja importee
		if not self.parent.tree.IsChildRoot(dName):
			if not self._d.has_key(dName) or (self._d.has_key(dName) and self._d[dName] != path):
				### si importation a partir du local
				if os.path.isdir(path):
					self.DoAdd(path, dName)
				### si importation a partir du web
				elif Utilities.checkURL(path):
					self.DoAdd(path, dName)
				### gestion de l'erreur
				else:
					if path.startswith('http'):
						msg = _('%s is an invalid url') % path
					else:
						msg = _('%s directory does not exist') % dName
					dial = wx.MessageDialog(self, msg, _('Error'), wx.OK | wx.ICON_ERROR)
					dial.ShowModal()
					self._dbb.SetValue('')
			else:
				dial = wx.MessageDialog(self, _('%s is already imported') % dName, _('Info'), wx.OK)
				dial.ShowModal()
				self._dbb.SetValue('')
		else:
			dial = wx.MessageDialog(self, _('%s is already imported') % dName, _('Info'), wx.OK)
			dial.ShowModal()
			self._dbb.SetValue('')

		# on reactive le bouton pour un eventuel autre ajout
		self._btn_Add.Enable(True)

### ------------------------------------------------------------
# class TestApp(wx.App):
	# """ Testing application
	# """
	
	# def OnInit(self):
		
		# import __builtin__
		# import gettext
		
		# __builtin__.__dict__['HOME_PATH'] = os.getcwd()
		# __builtin__.__dict__['DOMAIN_PATH'] = 'Domain'
		# __builtin__.__dict__['_'] = gettext.gettext
		
		# frame = ImportLibrary(None, size=(600,600), id=-1, title="Test")
		# frame.Show()
		# return True
	
	# def OnQuit(self, event):
		# self.Close()
		
# if __name__ == '__main__':

	# app = TestApp(0)
	# app.MainLoop()