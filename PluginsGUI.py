# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# PluginGUI.py ---
#                    --------------------------------
#                            Copyright (c) 2020
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 03/20/20
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
import os
import datetime
import sys
import re
import zipimport
import zipfile
import types

import inspect
if not hasattr(inspect, 'getargspec'):
    inspect.getargspec = inspect.getfullargspec

from abc import abstractmethod
from concurrent.futures import ThreadPoolExecutor
from wx.lib.mixins.listctrl import CheckListCtrlMixin, ListCtrlAutoWidthMixin

from Decorators import BuzyCursorNotification
from PluginManager import PluginManager 
from Utilities import FormatSizeFile, getPYFileListFromInit

import ZipManager
import Editor

_ = wx.GetTranslation

class CheckListCtrl(wx.ListCtrl, CheckListCtrlMixin, ListCtrlAutoWidthMixin):
	""" General Check list Class.
	"""

	def __init__(self, *args, **kw):
		""" Constructor.
		"""
		wx.ListCtrl.__init__(self, *args, **kw)
		ListCtrlAutoWidthMixin.__init__(self)

		if wx.VERSION_STRING >= '4.1.0':
			self.Bind(wx.EVT_LIST_ITEM_CHECKED, self.OnEnable)
			self.Bind(wx.EVT_LIST_ITEM_UNCHECKED, self.OnDisable)

			self.EnableCheckBoxes(True)
			self.IsChecked = self.IsItemChecked
		else:		
			CheckListCtrlMixin.__init__(self)
		
		if wx.VERSION_STRING < '4.0':
			self.SetStringItem = self.SetStringItem
			self.InsertStringItem = self.InsertStringItem
		else:
			self.SetStringItem = self.SetItem
			self.InsertStringItem = self.InsertItem

		self.id = -100000000
		self.map = {}

		images = [os.path.join(ICON_PATH_16_16, s) for s in ('disable_plugin.png','enable_plugin.png','no_ok.png')]

		self.il = wx.ImageList(16, 16)
		for i in images:
			self.il.Add(wx.Bitmap(i))
		self.SetImageList(self.il, wx.IMAGE_LIST_SMALL)

		#adding some art
		#self.il = wx.ImageList(16, 16)
		#a={"idx1":"CROSS_MARK","idx2":"TICK_MARK","idx3":"DELETE"}
		#for k,v in a.items():
		#	exec "self.%s= self.il.Add(wx.ArtProvider_GetBitmap(wx.ART_%s,wx.ART_TOOLBAR,(16,16)))" % (k,v)
		#self.SetImageList(self.il, wx.IMAGE_LIST_SMALL)

		# for wxMSW
		self.Bind(wx.EVT_COMMAND_RIGHT_CLICK, self.OnRightClick)

		# for wxGTK
		self.Bind(wx.EVT_RIGHT_UP, self.OnRightClick)

		### Layout
		self.Centre()
		self.Show(True)

		#self.Bind(wx.EVT_MOTION, self.OnMotion)

	# def OnMotion(self, evt):
	# 	"""
	# 	"""
	# 	item, flags = self.HitTest(evt.GetPosition())
		
	# 	try:
	# 		path = self.GetPyData(item)
	# 		self.SetToolTip(path[0].__file__)
	# 	except:
	# 		self.SetToolTip(None)
		
	# 	### only from wx 4.1.0
	# 	self.EnableCheckBoxes(True)

	# 	### else the drag and drop dont run
	# 	evt.Skip()

	def OnRightClick(self, event):
		""" Right click has been invoked.
		"""

		# make a menu
		menu = wx.Menu()

		enable = wx.MenuItem(menu, wx.NewIdRef(), _('Enable'), _("Enable the plugin"))
		disable = wx.MenuItem(menu, wx.NewIdRef(), _('Disable'), _("Disable the plugin"))
		edit = wx.MenuItem(menu, wx.NewIdRef(), _('Edit'), _("Edit the plugin"))
		
		enable.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH_16_16,'enable_plugin.png')))
		disable.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH_16_16,'disable_plugin.png')))
		edit.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH_16_16,'edit.png')))

		self.Bind(wx.EVT_MENU, self.OnEnable, id=enable.GetId() )
		self.Bind(wx.EVT_MENU, self.OnDisable, id=disable.GetId())
		self.Bind(wx.EVT_MENU, self.OnEdit, id=edit.GetId())

		if wx.VERSION_STRING < '4.0':
    		# add some items
			menu.AppendItem(enable)
			menu.AppendItem(disable)
			menu.AppendItem(edit)	
		else:
			# add some items
			menu.Append(enable)
			menu.Append(disable)
			menu.Append(edit)

		index = self.currentItem
		path = self.GetPath(index)
		### if not path, the module corresponding to the item is
		if path:
			### disable the edit menu for the .pyc file
			if path.endswith('.pyc'):
				edit.Enable(False)
			else:
				### is py file and enable only the right sumbemu depending on the stats of the check box
				sel = self.IsChecked(index)
				if sel:
					enable.Enable(False)
					disable.Enable(True)
				else:
					enable.Enable(True)
					disable.Enable(False)
		else:
			enable.Enable(False)
			disable.Enable(False)
			edit.Enable(False)				

		# Popup the menu.  If an item is selected then its handler
		# will be called before PopupMenu returns.
		self.PopupMenu(menu)
		menu.Destroy()

	def isOk(self, item):
		""" item is well imported
		"""
		
		module = self.GetPyData(item)[0]
		return module and module.__file__

	def GetPath(self,item):
		""" Get the path stored as PyData of the file
		"""
		py_data = self.GetPyData(item)
	
		### return path if the first elem of tuple (py_data) is file (can be a function for local plugin...)
		if py_data:
			### is function (global plugin)?
			if callable(py_data[0]):
				func = py_data[0]
				return func.__code__.co_filename
			### is file (local plugin) ?
			elif  os.path.isfile(py_data[0]):
				file = py_data[0]
				return file.__file__
			else:
				return None
		else:
			return None

	def GetIndex(self, event):
		""" Return index from event or currentItem
		"""
		return event.Index if hasattr(event,'Index') else self.currentItem

	def OnEnable(self, event):
		""" Ebnable the current item.
		"""
		index = self.GetIndex(event)
		#self.CheckItem(index, True)
		self.SetItemImage(index,1)
		event.Skip()

	def OnDisable(self, event):
		""" Disable the current item.
		"""
		index = self.GetIndex(event)
		#self.CheckItem(index, False)
		self.SetItemImage(index,0)
		event.Skip()

	@abstractmethod
	def OnEdit(self, event):
		""" Abstract method to edit plug-ins python file.
		"""
		pass
		
	def SetPyData(self, item, data):
		""" Set python object Data.
		"""
		self.map[self.id] = data
		self.SetItemData(item, self.id)
		self.id += 1

	def GetPyData(self, item):
		""" Get python object Data.
		"""
		return self.map.get(self.GetItemData(item),None)

	def get_selected_items(self):
		"""
		Gets the selected items for the list control.
		Selection is returned as a list of selected indices,
		low to high.
		"""
		selection = []

		# start at -1 to get the first selected item
		current = -1
		while True:
			next = self.GetNextSelected(current)
			if next == -1:
				return selection

			selection.append(next)
			current = next

	def GetNextSelected(self, current):
		"""Returns next selected item, or -1 when no more."""

		return self.GetNextItem(current,
								wx.LIST_NEXT_ALL,
								wx.LIST_STATE_SELECTED)

class GeneralPluginsList(CheckListCtrl):
	""" Class for populate CheckListCtrl with DEVSimPy plug-ins stored in configuration file.
	"""

	def __init__(self, *args, **kwargs):
		""" Constructor.
		"""
		CheckListCtrl.__init__(self, *args, **kwargs)

		self.InsertColumn(0, _('Name'), width=180)
		self.InsertColumn(1, _('Size'))
		self.InsertColumn(2, _('Date'))
		self.InsertColumn(3, _('Type'))

		self.mainW = wx.GetApp().GetTopWindow()

		### Populate method is called ?
		self.is_populate = False

		### active plug-ins stored in DEVSimPy configuration file
		try:
			self.active_plugins_list = eval(self.mainW.cfg.Read("active_plugins"))
		except AttributeError:
			sys.stderr.write(_("Plugin not stored in configuration file!"))
			self.active_plugins_list = []

		### if pluginsList (2 parameters in constructor) is in constructor, we can populate
		try:
			pluginsList = args[1]
		except IndexError:
			#sys.stdout.write(_("Don't forget to call Populate method!\n"))
			pass
		else:
			self.Populate(pluginsList)
			self.is_populate = True

	@BuzyCursorNotification
	def Populate(self, pluginsList):
		""" Populate method must be called just before constructor.
		"""

		if not self.is_populate:
			# all plug_ins file in plug_ins directory and already loaded
			# list of all file (without __init__.py)
			for root, dirs, files in pluginsList:

				### append the plug-ins directory to sys.path in order to use local importing notation (import...) in plug-in file.
				if root not in sys.path:
					sys.path.append(root)

				### dirs must contain python file
				if files:
					for filename in [f for f in files if f == "__init__.py"]:
						path = os.path.join(root, filename)
						L = getPYFileListFromInit(path,'.py')+getPYFileListFromInit(path,'.pyc')
						for basename in L:
							### try to add dynamically plug-ins
							#try:
								#t = threading.Thread(target=self.Importing, args=(root, basename,))
								#t.start()
							#except Exception:
								#if wx.Platform == '__WXGTK__':
									##i+=1
									#wx.CallLater(500, self.Importing, root, basename,)
								#else:
								self.Importing(root, basename)

			self.is_populate = True

	def MyInsertItem(self, root, basename):
		""" Insert plug-in in list.
		"""

		### absolute name
		ext = 'py'
		absname = os.path.join(root,"%s.%s"%(basename,ext))

		### try for pyc if py not exists
		if not os.path.exists(absname):
			ext = 'pyc'
			absname = os.path.join(root,"%s.%s"%(basename,ext))

		if os.path.exists(absname):
			### file size
			size = FormatSizeFile(os.path.getsize(absname))

			### date manager
			date = datetime.datetime.fromtimestamp(os.path.getmtime(absname))
			if hasattr(self.mainW,'language') and self.mainW.language == 'fr':
				date = date.strftime("%d/%m/%y")
			else:
				date = str(date.date())

			# add to the CheckListCtrl
			index = self.InsertItem(100000000, basename)
		
			self.SetItem(index, 1, size)
			self.SetItem(index, 2, date)
			self.SetItem(index, 3, ext)

			return index
		else:
			sys.stderr.write(_("The format of the Plugin file is not .py or .pyc!"))
			return None

	def Importing(self, root, basename):
		""" Importing module and set pydata object
		"""

		# check the loaded module during the start of plug-ins
		module = PluginManager.load_plugins(basename)

		### if module is exception (or tuple)
		if not inspect.ismodule(module):
			error = str(module)
			module = types.ModuleType(basename)
			module.__doc__ = error
			module.__file__ = None

		index = self.MyInsertItem(root, basename)

		if index is not None:
			if module.__file__ != None:
				### only module to be activated is checked
				if basename in self.active_plugins_list:
					self.CheckItem(index, True)
					self.SetItemImage(index,1)
				else:
					PluginManager.disable_plugin(basename)
			else:
				self.SetItemImage(index, 2)

			#### pyData setting
			self.SetPyData(index, (module, None))

	def Clear(self):
		""" Delete all items of list
		"""
		self.DeleteAllItems()
		self.is_populate = False

	def OnEdit(self, event):
		"""
		"""
		index = self.currentItem
		path = self.GetPath(index)
		if self.IsSelected(index) and path and path.endswith('.py'):
			name = os.path.basename(path)
			module = self.GetPyData(index)[0]
			### editor frame for the text of plug-ins
			editorFrame = Editor.GetEditor(None, \
							wx.NewIdRef(), \
							_("%s - Plug-ins Editor")%name, \
							module, \
							file_type = 'block')
			editorFrame.AddEditPage(name, path)
			editorFrame.Show()
		### for .pyc file
		else:
			pass

	def OnApply(self, event):
		""" Method called by PreferenceGUI class.
				- Active plug-in through pluginmanager
				- Write the plug-in list in the DEVSimPy config file
		"""

		### list of plug-in names which are to write in DEVSimPy config file
		pluginsList = []
		### all listed plug-ins
		for i in range(self.GetItemCount()):
			module = self.GetPyData(i)[0]
			if inspect.ismodule(module):
				### plug-in file path
				path = module.__file__
				### built-in module coming from empty module create by error manager
				if path:
					### get abspath and exclude .pyc
					name,ext = os.path.splitext(os.path.basename(path))
					### if plug-in is checked, we activate it
					
					if self.IsChecked(i):
						pluginsList.append(name)
						PluginManager.enable_plugin(name)
					else:
						PluginManager.disable_plugin(name)

		### config file writing
		self.mainW.cfg.Write('active_plugins', str(pluginsList))
		self.mainW.cfg.Flush()

class BlockPluginsList(CheckListCtrl):
	""" Class for populate CheckListCtrl with Block plug-ins stored compressed python file (in .amd or .cmd)
	"""

	def __init__(self, *args, **kwargs):
		""" Constructor.
		"""
		CheckListCtrl.__init__(self,*args, **kwargs)

		self.InsertColumn(0, _('Name'), width=180)
		self.InsertColumn(1, _('Type'), width=180)
		self.InsertColumn(2, _('Info'), width=180)

		### Populate method is called ?
		self.is_populate = False

		### if pluginsList (2 param in constructor) is in constructor, we can populate
		try:
			PluginManager.pluginsList = args[1]
		except IndexError:
			#sys.stdout.write(_('D'ont forget to call Populate method!\n'))
			pass
		else:
			try:
				### Populate Check List dynamicaly
				pool = ThreadPoolExecutor(3)
				future = pool.submit(self.Populate, (PluginManager.pluginsList))
				future.done()
			except:
				self.Populate(PluginManager.pluginsList)
			
			self.is_populate = True
	
	def OnEnable(self, event):
		""" Ebnable the current item.
		"""
		CheckListCtrl.OnEnable(self, event) 
		self.DoChekItem(self.GetIndex(event))
		event.Skip()

	def OnDisable(self, event):
		""" Disable the current item.
		"""
		CheckListCtrl.OnDisable(self, event) 
		self.DoChekItem(self.GetIndex(event))
		event.Skip()

	def DoChekItem(self, index):
		"""
		"""

		pluginName = self.GetItemText(index)
		new, old = self.GetPyData(index)

		### new is function
		if inspect.isfunction(new):
			### create or override attribute
			if self.IsChecked(index):
				### add method object (not unbounded method)
				setattr(self.model, pluginName, types.MethodType(new, self.model))
				### add plug-in in plug-ins list
				if pluginName not in self.model.plugins:
					self.model.plugins.append(pluginName)
			else:
				### delete dynamic attribute
				if old is None:
					exec("del self.model.%s"%(pluginName))
				### restore overwriting attribute
				else:
					setattr(self.model, pluginName, types.MethodType(old, self.model))

				### update plug-ins list
				if pluginName in self.model.plugins:
					del self.model.plugins[self.model.plugins.index(pluginName)]

		elif inspect.isclass(new):
			### TODO: monkey patchin !!! (most simple is to change python file for override class)
			sys.stdout.write(_('WARNING: class can\'t be overwritted'))
		else:
			pass
		
	def OnCheckItem(self, index, flag):
		""" Item has been checked.
		"""
		self.DoChekItem(self, index)

	#@BuzyCursorNotification
	def Populate(self, model):
		""" Populate method must be called just before constructor.
		"""
		if not self.is_populate:
			self.model = model

			if self.model and not hasattr(self.model, "plugins"):
				self.model.plugins = []		### dynamic append attribute

			plugins_list = self.GetPluginsList(self.model.model_path) if self.model else []

			if not isinstance(plugins_list, list):
				msg = _('Error in plugins.py file:\n\n%s\n\nDo you want to edit this file?'%plugins_list)

				dial = wx.MessageDialog(None, msg, _('Plug-ins Manager'), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_ERROR)

				if dial.ShowModal() == wx.ID_YES:
					### editor frame for text of plug-ins
					editorFrame = ModelPluginsManager.GetEditor(None, self.model)
					editorFrame.Show()

				self.is_populate = False
			else:
				### for plug-ins given by GetPluginsList method
				for m, new, old in plugins_list:
					name = m.__name__

					# add to the CheckListCtrl
					index = self.InsertItem(100000000, name)
					self.SetItem(index, 1, str(type(m)))
					self.SetItem(index, 2, _('overriding') if hasattr(self.model, name) else _('new'))

					### if plug-ins contains error, error is stored in doc object and icon is changed
					if isinstance(new, Exception):
						new.__doc__ = srt(new)
						self.SetItemImage(index, 2)

					#### set the pydata object
					self.SetPyData(index, (new, old))

					### enabling stored plug-ins (after SetPyData)
					if name in self.model.plugins:
						self.CheckItem(index, True)
						self.SetItemImage(index,1)

				self.is_populate = True

	@staticmethod
	def IsInPackage(model_path):
		""" Return True if plugins.py file is in plug-ins package
			Warning : importer.is_package('plug-ins') don't work !!!
		"""
		
		zf = zipfile.ZipFile(model_path, 'r')
		nl = zf.namelist()
		zf.close()
		return any([re.search("^plugins%s[a-zA-Z]*"%os.sep, s) for s in nl])

	@staticmethod
	def IsInRoot(model_path):
		""" Return True is plugins.py is in zipfile
		"""

		zf = zipfile.ZipFile(model_path, 'r')
		nl = zf.namelist()
		zf.close()
		return any([re.search("^plugins.py$", s) for s in nl])

	def GetPluginsList(self, model_path):
		""" Get plug-ins list from plug-in file
		"""

		### if amd or cmd
		if zipfile.is_zipfile(model_path):
			### zip importer from model path
			importer = zipimport.zipimporter(model_path)

			### where is the puglins.py file ?
			name = "plugins"
			if BlockPluginsList.IsInPackage(model_path):
				fullname = os.path.join(name,name)
			elif BlockPluginsList.IsInRoot(model_path):
				fullname = name
			else:
				fullname = None

			### There is errors in {plugins/}plugins.py file ?
			if fullname:
				try:
					module = importer.load_module(fullname)

				except Exception as info:
					sys.stderr.write(_("Error loading plug-ins: %s\n"%info))
					return info
			else:
				module = None

			### list of tuple composed by parent module, new module and old module
			L = []

			if module:
				### for element (function, method or class) in module coming from plugins.py
				for name,m in inspect.getmembers(module, inspect.isfunction):

					### it's a method
					#if 'self' in inspect.getargspec(m).args:
					if 'self' in list(inspect.signature(m).parameters):

						### trying to eval new element to assign
						try:
							new = eval("module.%s"%name)
						except Exception as info:
							new = info
							new.__doc__ = str(info)

						### new element is function
						if inspect.isfunction(new):
							### object has attribute (override)
							if name in self.model.__class__.__dict__:
								old = self.model.__class__.__dict__[name]
							### object don't have attribute (create)
							else:
								old = None
						### new element is class
						#elif inspect.isclass(new):
							#old = self.model.__class__
						else:
							sys.stdout.write(_('WARNING: plug-in type (%s) not supported!'%(name)))

						L.append((m,new,old))

			return L

	def Clear(self):
		""" Delete all items of list
		"""

		self.DeleteAllItems()
		self.is_populate = False

class PluginsPanel(wx.Panel):
	""" Plug-ins Panel
	"""

	def __init__(self, *args, **kwargs):
		""" Constructor.
		"""
		wx.Panel.__init__(self, *args, **kwargs)

		### local copy
		self.parent = args[0]

		### Sizer
		self.vbox1 = wx.BoxSizer(wx.VERTICAL)
		self.vbox2 = wx.BoxSizer(wx.VERTICAL)
		hbox = wx.BoxSizer(wx.HORIZONTAL)

		### Panels
		self.leftPanel = wx.Panel(self)
		self.rightPanel = wx.Panel(self)

		### plug-in documentation area
		self.log = wx.TextCtrl(self.rightPanel, wx.NewIdRef(), size=(-1,150), style=wx.TE_MULTILINE)
		if wx.VERSION_STRING >= '4.0': self.log.SetToolTipString = self.log.SetToolTip
		self.log.SetToolTipString(_("Plug-in documentation area.\nSelect plug-in in order to print its documentation."))

		### Default plug-ins list
		self.check_list = CheckListCtrl(parent=self.rightPanel, style=wx.LC_REPORT | wx.SUNKEN_BORDER|wx.LC_SORT_ASCENDING)

		### Buttons
		selBtn = wx.Button(self.leftPanel, wx.ID_SELECTALL, size=(140, -1))
		desBtn = wx.Button(self.leftPanel, wx.NewIdRef(), _('Deselect All'), size=(140, -1))
		self.configBtn = wx.Button(self.leftPanel, wx.ID_PROPERTIES, size=(140, -1))
		self.configBtn.Enable(False)

		if wx.VERSION_STRING >= '4.0': 
			selBtn.SetToolTipString = selBtn.SetToolTip
			desBtn.SetToolTipString = desBtn.SetToolTip
			self.configBtn.SetToolTipString = self.configBtn.SetToolTip
		
		selBtn.SetToolTipString(_("Select all plug-ins"))
		desBtn.SetToolTipString(_("Unselect all plug-ins"))
		self.configBtn.SetToolTipString(_("Selected plug-in setting"))

		### Sizer adding
		self.vbox2.Add((-1, 15))
		self.vbox2.Add(selBtn, 0, wx.TOP, 5)
		self.vbox2.Add(desBtn, 0, wx.TOP, 5)
		self.vbox2.Add(wx.StaticLine(self.leftPanel), 0, wx.EXPAND|wx.TOP, 5)
		self.vbox2.Add(self.configBtn, 0, wx.TOP, 5)

		self.vbox1.Add(self.check_list, 1, wx.EXPAND|wx.TOP, 5)
		self.vbox1.Add((-1, 10))
		self.vbox1.Add(self.log, 1, wx.EXPAND|wx.ALL, 5)

		hbox.Add(self.rightPanel, 1, wx.EXPAND|wx.ALL)
		hbox.Add(self.leftPanel, 0, wx.EXPAND|wx.ALL, 5)
		#hbox.Add((3, -1))

		### Set Sizer
		self.leftPanel.SetSizer(self.vbox2)
		self.rightPanel.SetSizer(self.vbox1)
		self.SetSizerAndFit(hbox)
		#self.SetAutoLayout(True)

		### Binding
		self.Bind(wx.EVT_BUTTON, self.OnSelectAll, id=selBtn.GetId())
		self.Bind(wx.EVT_BUTTON, self.OnDeselectAll, id=desBtn.GetId())
		self.Bind(wx.EVT_BUTTON, self.OnConfig, id=self.configBtn.GetId())
		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelectedItem, id=self.check_list.GetId())
		
#		self.check_list.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick)
#		self.check_list.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)

	def AddWidget(self, before, widget):
		""" Add widget to right panel
		"""
		self.vbox2.Insert(before, widget, 0, wx.TOP, 5)

	def GetLeftPanel(self):
		""" Return left panel
		"""
		return self.leftPanel

	def GetRightPanel(self):
		""" Return left panel
		"""
		return self.rightPanel

	def SetPluginsList(self, Checklist = None):
		""" Update right panel with new check_list
		"""
		### DONT USE DETACH FOR WINDOWS, PREFER HIDE !!!
		self.vbox1.Hide(self.check_list)
		self.check_list = Checklist
		self.vbox1.Insert(0, self.check_list, 1, wx.EXPAND | wx.TOP, 3)
		self.rightPanel.SetSizer(self.vbox1)
		self.Refresh()

		self.Unbind(wx.EVT_LIST_ITEM_SELECTED)
		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelectedItem, id=self.check_list.GetId())

	def OnApply(self, event):
		""" Call OnApply method ig CheckList class
		"""

		self.check_list.OnApply(event)

	def OnSelectedItem(self, event):
		""" Item has been select and the documentation of module is immediately printed to the button CtrlText
		"""
		
		sel = event.Index
		self.check_list.currentItem = sel

#		sel = self.check_list.GetFirstSelected()

		if sel != -1:
			item = self.check_list.GetItem(sel)
			new_element = self.check_list.GetPyData(sel)[0]
			doc = new_element.__doc__
			self.log.ChangeValue(doc + '\n' if doc else _("No documentation available for this plug-in."))
			module = inspect.getmodule(new_element)
			self.configBtn.Enable(hasattr(module, "Config"))
		
		event.Skip()

	def OnSelectAll(self, event):
		""" Select All button has been pressed and all plug-ins are enabled.
		"""
		num = self.check_list.GetItemCount()
		for i in range(num):
			self.check_list.CheckItem(i, True)
			self.check_list.SetItemImage(i,1)

	def OnDeselectAll(self, event):
		""" Deselect All button has been pressed and all plug-ins are disabled.
		"""
		num = self.check_list.GetItemCount()
		for i in range(num):
			self.check_list.CheckItem(i, False)
			self.check_list.SetItemImage(i,0)

	def OnConfig(self, event):
		""" Setting button has been pressed and the plug-in config function is call.
		"""

		sel = self.check_list.GetFirstSelected()
		if sel != -1:
			obj = self.check_list.GetPyData(sel)[0]
			if inspect.ismodule(obj):
				module = obj
			elif inspect.isfunction(obj):
				module = inspect.getmodule(obj)
			else:
				sys.stderr.write(_("Warning: Type of list object unknown in PluginsGUI"))

			# call the Config plug-in function
			module.Config(*(), **{'parent':self})

class ModelPluginsManager(wx.Frame):
	""" Plug-ins Manager for DEVSimPy Block
	"""
	def __init__(self, *args, **kwargs):
		""" Constructor.
		"""

		self.model = kwargs.pop('model')

		super(wx.Frame,self).__init__(*args, **kwargs)

		### plug-in panel
		self.pluginPanel = PluginsPanel(self)

		### two panel into plug-in panel
		rpanel = self.pluginPanel.GetRightPanel()
		lpanel = self.pluginPanel.GetLeftPanel()

		### checklist to insert in right panel
		self.CheckList = BlockPluginsList(parent=rpanel, style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SORT_ASCENDING)
		wx.CallAfter(self.CheckList.Populate, (self.model))

		### Buttons for insert or delete plug-ins
		self.addBtn = wx.Button(lpanel, wx.ID_ADD, size=(140, -1))
		self.delBtn = wx.Button(lpanel, wx.ID_DELETE, size=(140, -1))
		self.editBtn = wx.Button(lpanel, wx.ID_EDIT, size=(140, -1))
		self.updateBtn = wx.Button(lpanel, wx.ID_APPLY, size=(140, -1))

		if wx.VERSION_STRING >= '4.0':
			self.addBtn.SetToolTipString=self.addBtn.SetToolTip
			self.delBtn.SetToolTipString=self.delBtn.SetToolTip
			self.editBtn.SetToolTipString=self.editBtn.SetToolTip
			self.updateBtn.SetToolTipString = self.updateBtn.SetToolTip

		self.addBtn.SetToolTipString(_("Add new plug-ins"))
		self.delBtn.SetToolTipString(_("Delete all existing plug-ins"))
		self.editBtn.SetToolTipString(_("Edit plug-in file"))
		self.updateBtn.SetToolTipString(_("Update plug-in list"))

		### add widget to plug-in panel
		self.pluginPanel.SetPluginsList(self.CheckList)
		self.pluginPanel.AddWidget(3, self.addBtn)
		self.pluginPanel.AddWidget(4, self.editBtn)
		self.pluginPanel.AddWidget(5, self.updateBtn)
		self.pluginPanel.AddWidget(6, self.delBtn)

		#### zipfile (amd or cmd)
		try:
			self.zf = ZipManager.Zip(self.model.model_path)
			cond = ZipManager.Zip.HasPlugin(self.model.model_path)
		except AttributeError:
			sys.stdout.write(_('PluginsGUI in mode alone.\n'))
			cond=False

		### enable del, add and update buttons
		self.delBtn.Enable(cond)
		self.addBtn.Enable(not cond)
		self.editBtn.Enable(cond)
		self.updateBtn.Enable(False)

		self.Bind(wx.EVT_BUTTON, self.OnAdd, id=self.addBtn.GetId())
		self.Bind(wx.EVT_BUTTON, self.OnDelete, id=self.delBtn.GetId())
		self.Bind(wx.EVT_BUTTON, self.OnEdit, id=self.editBtn.GetId())
		self.Bind(wx.EVT_BUTTON, self.OnRefresh, id=self.updateBtn.GetId())

		self.CheckList.OnEdit = self.OnEdit

		self.CenterOnParent(wx.BOTH)
		self.Layout()
		#self.Fit()

	@staticmethod
	def GetEditor(parent, model, filename=None):
		"""
		"""
		path = os.path.join(model.model_path, ZipManager.Zip.GetPluginFile(model.model_path)) if not filename else filename
		name = os.path.basename(path)

		### editor frame for the text of plug-ins
		editorFrame = Editor.GetEditor(None, \
									wx.NewIdRef(), \
									_("%s - Plug-ins Editor")%os.path.basename(model.model_path), \
									model, \
									file_type = 'block')
		editorFrame.AddEditPage(name, path)

		return editorFrame

	def OnEdit(self, event):
		""" Edit plug-ins python file
		"""

		### plug-ins text
		if self.model:

			editorFrame = ModelPluginsManager.GetEditor(self, self.model)
			editorFrame.Show()

			self.addBtn.Enable(False)
			self.editBtn.Enable(False)
			self.delBtn.Enable(False)
			self.updateBtn.Enable(True)

	def OnRefresh(self, event):
		### Clear before populate with new plug-ins
		self.CheckList.Clear()
		wx.CallAfter(self.CheckList.Populate, (self.model))

		self.addBtn.Enable()
		self.editBtn.Enable()
		self.delBtn.Enable()
		self.updateBtn.Enable(False)

	def OnAdd(self, event):
		""" Add plug-in
		"""
		filename = None
		wcd = 'All files (*)|*|Editor files (*.py)|*.py'
		dir = HOME_PATH
		open_dlg = wx.FileDialog(self, message=_('Choose a file'), defaultDir=dir, defaultFile='plugins.py', wildcard=wcd, style=wx.OPEN|wx.CHANGE_DIR)
		if open_dlg.ShowModal() == wx.ID_OK:
			### TODO
			### first test is for old devsimpy model presenting plug-ins at the root of zipfile
			### filename handling depending on the existing plug-ins package in zipfile model
			if BlockPluginsList.IsInPackage(self.model.model_path):
				filename = os.path.join('plugins', open_dlg.GetPath())
			else:
				filename = open_dlg.GetPath()

		open_dlg.Destroy()

		if filename:
			source = open(filename, 'r').read() + '\n'
			code = compile(source, filename, 'exec')

			### try to find error before compressed in the archive model
			try:
				eval(code)
			### Error occur
			except Exception as info:
				msg = _('Error trying to load plug-in.\nInfo : %s\nDo you want to edit this plug-in file?')%info
				dial = wx.MessageDialog(None, msg, self.model.label, wx.YES_NO | wx.NO_DEFAULT | wx.ICON_ERROR)

				### user choose to edit plugins.py file
				if dial.ShowModal() == wx.ID_YES:
					### Editor instance depends on the location of plugins.py
					kargs = {'parent':None, 'model':self.model}
					### plugins.py is not in model ?
					if not BlockPluginsList.IsInPackage(self.model.model_path):
						kargs.update({'filename':filename})

					### execute Editor depending on kargs
					editorFrame = ModelPluginsManager.GetEditor(**kargs)
					editorFrame.Show()

				dial.Destroy()
			else:
				self.zf.Update([filename])

				### Clear before populate with new plug-ins
				self.CheckList.Clear()
				wx.CallAfter(self.CheckList.Populate, (self.model))

				### Update button access
				self.addBtn.Enable(False)
				self.delBtn.Enable(True)
				self.editBtn.Enable(True)

	def OnDelete(self, event):
		""" Delete plug-ins
		"""
		### delete file from zipfile
		dial = wx.MessageDialog(self, _('Do You really want to delete plug-ins file?'), self.model.label, wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
		if dial.ShowModal() == wx.ID_YES:
			### TODO
			### first test is for old devsimpy model presenting plug-ins at the root of zipfile
			### path depends on the existing plug-ins package in zipfile model
			path = os.path.join('plugins', 'plugins.py') if BlockPluginsList.IsInPackage(self.model.model_path) else 'plugins.py'
			self.zf.Delete([path])
			### Clear before populate with empty plug-ins file
			self.CheckList.Clear()
			wx.CallAfter(self.CheckList.Populate, (self.model))
		dial.Destroy()

		### Update button access
		self.delBtn.Enable(False)
		self.addBtn.Enable(True)
		self.editBtn.Enable(False)

### ------------------------------------------------------------
class TestApp(wx.App):
	""" Testing application
	"""

	def OnInit(self):


		import builtins
		import gettext

		builtins.__dict__['HOME_PATH'] = os.getcwd()
		builtins.__dict__['ICON_PATH_16_16']=os.path.join('icons','16x16')
		builtins.__dict__['_'] = gettext.gettext

		frame = ModelPluginsManager(parent=None, title="Test", model=None)
		frame.Show()
		return True

	def OnQuit(self, event):
		self.Close()

if __name__ == '__main__':

	app = TestApp(0)
	app.MainLoop()