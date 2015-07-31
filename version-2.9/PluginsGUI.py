# -*- coding: utf-8 -*-

import wx
import os
import datetime
import sys
import imp
import abc
import re
import zipimport
import zipfile
import inspect
import types
import inspect

from wx.lib.mixins.listctrl import CheckListCtrlMixin, ListCtrlAutoWidthMixin

from Decorators import BuzyCursorNotification

from pluginmanager import enable_plugin, disable_plugin, load_plugins
from Utilities import FormatSizeFile, getFileListFromInit

import ZipManager
import Editor

class CheckListCtrl(wx.ListCtrl, CheckListCtrlMixin, ListCtrlAutoWidthMixin):
	""" General Check list Class.
	"""

	def __init__(self, parent):
		""" Constructor.
		"""

		wx.ListCtrl.__init__(self, parent, wx.ID_ANY, style=wx.LC_REPORT | wx.SUNKEN_BORDER)
		CheckListCtrlMixin.__init__(self)
		ListCtrlAutoWidthMixin.__init__(self)

		self.id = -sys.maxint
		self.map = {}

		images = [	os.path.join(ICON_PATH_16_16,'disable_plugin.png'),
					os.path.join(ICON_PATH_16_16,'enable_plugin.png'),
					os.path.join(ICON_PATH_16_16,'no_ok.png')
					]

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

	def SetPyData(self, item, data):
		""" Set python object Data
		"""
		self.map[self.id] = data
		self.SetItemData(item, self.id)
		self.id += 1

	def GetPyData(self, item):
		""" Get python object Data
		"""
		return self.map[self.GetItemData(item)]

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
		"""Returns next selected item, or -1 when no more"""

		return self.GetNextItem(current,
								wx.LIST_NEXT_ALL,
								wx.LIST_STATE_SELECTED)

class Populable(object):
	""" Abstract class defined in order to populate list
	"""
	__metaclass__ = abc.ABCMeta

	@abc.abstractmethod
	def Populate(self):
		""" Abstract method
		"""
		return

class GeneralPluginsList(CheckListCtrl, Populable):
	""" Class for populate CheckListCtrl with DEVSimPy plug-ins stored in configuration file
	"""

	def __init__(self, *args, **kwargs):
		""" Constructor.
		"""
		CheckListCtrl.__init__(self, *args, **kwargs)

		self.InsertColumn(0, _('Name'), width=180)
		self.InsertColumn(1, _('Size'))
		self.InsertColumn(2, _('Date'))

		self.mainW = wx.GetApp().GetTopWindow()

		### Populate method is called ?
		self.is_populate = False

		### active plug-ins stored in DEVSimPy config file
		try:
			self.active_plugins_list = eval(self.mainW.cfg.Read("plugins"))
		except AttributeError:
			self.active_plugins_list = []

		### if pluginsList (2 parameters in constructor) is in constructor, we can populate
		try:
			pluginsList = args[1]
		except IndexError:
			#sys.stdout.write(_('Don't forget to call Populate method!\n'))
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
				if files != []:
					#for filename in filter(lambda f: not f.startswith('__') and f.endswith('.py'), files):
					for filename in filter(lambda f: f == "__init__.py", files):
						for basename in getFileListFromInit(os.path.join(root,filename)):
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


	def InsertItem(self, root, basename):
		""" Insert plug-in in list
		"""

		### absolute name
		absname = os.path.join(root,"%s.py"%basename)

		### file size
		size = FormatSizeFile(os.path.getsize(absname))

		### date manager
		date = datetime.datetime.fromtimestamp(os.path.getmtime(absname))
		if hasattr(self.mainW,'language') and self.mainW.language == 'fr':
			date = date.strftime("%d/%m/%y")
		else:
			date = str(date.date())

		# add to the CheckListCtrl
		index = self.InsertStringItem(sys.maxint, basename)
		self.SetStringItem(index, 1, size)
		self.SetStringItem(index, 2, date)

		return index

	def Importing(self, root, basename):
		""" Importing module and set pydata object
		"""

		# check the loaded module during the start of plug-ins
		module = load_plugins(basename)

		### if module is exception (or tuple)
		if not inspect.ismodule(module):
			error = str(module)
			module = imp.new_module(basename)
			module.__doc__ = error
			module.__file__ = None

		index = self.InsertItem(root, basename)

		if module.__file__ != None:
			### only module to be activated is checked
			if basename in self.active_plugins_list:
				self.CheckItem(index)
			else:
				disable_plugin(basename)
		else:
			self.SetItemImage(index, 2)

		#### pyData setting
		self.SetPyData(index, (module, None))

	def Clear(self):
		""" Delete all items of list
		"""
		self.DeleteAllItems()
		self.is_populate = False

	def OnApply(self, event):
		""" Method called by PreferenceGUI class.
				- Active plug-in through pluginmanager
				- Write the plug-in list in the DEVSimPy config file
		"""

		### list of plug-in names which are to write in DEVSimPy config file
		pluginsList = []
		### all listed plug-ins
		for i in xrange(self.GetItemCount()):
			module = self.GetPyData(i)[0]
			if inspect.ismodule(module):
				### plug-in file path
				file = module.__file__
				### built-in module coming from empty module create by error manager
				if file is not None:
					### get abspath and exclude .pyc
					name,ext = os.path.splitext(os.path.basename(file))
					### if plug-in is checked, we activate
					if self.IsChecked(i):
						pluginsList.append(name)
						enable_plugin(name)
					else:
						disable_plugin(name)

		### config file writing
		self.mainW.cfg.Write('plugins', str(pluginsList))
		self.mainW.cfg.Flush()

class BlockPluginsList(CheckListCtrl, Populable):
	""" Class for populate CheckListCtrl with Block plug-ins stored compressed python file (in .amd or .cmd)
	"""

	def __init__(self, *args, **kwargs):
		""" Constructor.
		"""
		CheckListCtrl.__init__(self, *args, **kwargs)

		self.InsertColumn(0, _('Name'), width=180)
		self.InsertColumn(1, _('Type'), width=180)
		self.InsertColumn(2, _('Info'), width=180)

		### Populate method is called ?
		self.is_populate = False

		### if pluginsList (2 param in constructor) is in constructor, we can populate
		try:
			pluginsList = args[1]
		except IndexError:
			#sys.stdout.write(_('D'ont forget to call Populate method!\n'))
			pass
		else:
			self.Populate(pluginsList)
			self.is_populate = True

	def OnCheckItem(self, index, flag):
		""" Item has been checked
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
					exec "del self.model.%s"%(pluginName)
				### restore overwriting attribute
				else:
					setattr(self.model, pluginName, types.MethodType(old, self.model))

				### update plug-ins list
				if pluginName in self.model.plugins:
					del self.model.plugins[self.model.plugins.index(pluginName)]

		elif inspect.isclass(new):
			### TODO: monkey patchin !!! (most simple is to change python file for override class)
			sys.stdout.write(_('WARNING: class can\'t be overwritted'))

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
				msg = ('Error in plugins.py file:\n\n%s\n\nDo you want to edit this file?'%plugins_list)

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
					index = self.InsertStringItem(sys.maxint, name)
					self.SetStringItem(index, 1, str(type(m)))
					self.SetStringItem(index, 2, _('overriding') if hasattr(self.model, name) else _('new'))

					### if plug-ins contains error, error is stored in doc object and icon is changed
					if isinstance(new, Exception):
						new.__doc__ = srt(new)
						self.SetItemImage(index, 2)

					#### set the pydata object
					self.SetPyData(index, (new, old))

					### enabling stored plug-ins (after SetPyData)
					if name in self.model.plugins:
						self.CheckItem(index)

				self.is_populate = True

	@staticmethod
	def IsInPackage(model_path):
		""" Return True if plugins.py file is in plug-ins package
			Warning : importer.is_package('plug-ins') don't work !!!
		"""
		zf = zipfile.ZipFile(model_path, 'r')
		nl = zf.namelist()
		zf.close()
		return any(map(lambda s: re.search("^plugins%s[a-zA-Z]*"%os.sep, s), nl))

	@staticmethod
	def IsInRoot(model_path):
		""" Return True is plugins.py is in zipfile
		"""
		zf = zipfile.ZipFile(model_path, 'r')
		nl = zf.namelist()
		zf.close()
		return any(map(lambda s: re.search("^plugins.py$", s), nl))

		#return 'plugins.py' in nl
		#importer = zipimport.zipimporter(model_path)
		#return importer.find_module('plug-ins') is not None

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

				except Exception, info:
					sys.stderr.write(_("Error loading plug-ins: %s\n"%info))
					return info
			else:
				module = None

			### list of tuple composed by parent module, new module and old module
			L = []

			if module:
				### for element (function, method or class) in module coming from plugins.py
				for name,m in inspect.getmembers(module, inspect.isfunction):

					### it's method
					if 'self' in inspect.getargspec(m).args:

						### trying to eval new element to assign
						try:
							new = eval("module.%s"%name)
						except Exception, info:
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

	def __init__(self,  parent):
		""" Constructor.
		"""
		wx.Panel.__init__(self,  parent)

		### local copy
		self.parent = parent

		### Sizer
		self.vbox1 = wx.BoxSizer(wx.VERTICAL)
		self.vbox2 = wx.BoxSizer(wx.VERTICAL)
		hbox = wx.BoxSizer(wx.HORIZONTAL)

		### Panels
		self.leftPanel = wx.Panel(self, wx.ID_ANY)
		self.rightPanel = wx.Panel(self, wx.ID_ANY)

		### plug-in documentation area
		self.log = wx.TextCtrl(self.rightPanel, wx.ID_ANY, size=(-1,150), style=wx.TE_MULTILINE)
		self.log.SetToolTipString(_("Plug-in documentation area.\nSelect plug-in in order to print its documentation."))

		### Default plug-ins list
		self.check_list = CheckListCtrl(self.rightPanel)

		### Buttons
		selBtn = wx.Button(self.leftPanel, wx.ID_SELECTALL, size=(140, -1))
		desBtn = wx.Button(self.leftPanel, wx.ID_ANY, _('Deselect All'), size=(140, -1))
		self.configBtn = wx.Button(self.leftPanel, wx.ID_PROPERTIES, size=(140, -1))
		self.configBtn.Enable(False)

		selBtn.SetToolTipString(_("Select all plug-ins"))
		desBtn.SetToolTipString(_("Unselect all plug-ins"))
		self.configBtn.SetToolTipString(_("Selected plug-in setting"))

		### Sizer adding
		self.vbox2.Add((-1, 15))
		self.vbox2.Add(selBtn, 0, wx.TOP, 5)
		self.vbox2.Add(desBtn, 0, wx.TOP, 5)
		self.vbox2.Add(wx.StaticLine(self.leftPanel), 0, wx.ALL|wx.EXPAND, 5)
		self.vbox2.Add(self.configBtn)

		self.vbox1.Add(self.check_list, 1, wx.EXPAND | wx.TOP, 3)
		self.vbox1.Add((-1, 10))
		self.vbox1.Add(self.log, 0.5, wx.EXPAND)

		hbox.Add(self.rightPanel, 1, wx.EXPAND|wx.ALL)
		hbox.Add(self.leftPanel, 0, wx.EXPAND | wx.RIGHT|wx.ALL, 5)
		hbox.Add((3, -1))

		### Set Sizer
		self.leftPanel.SetSizer(self.vbox2)
		self.rightPanel.SetSizer(self.vbox1)
		self.SetSizer(hbox)
		#self.SetAutoLayout(True)

		### Binding
		self.Bind(wx.EVT_BUTTON, self.OnSelectAll, id=selBtn.GetId())
		self.Bind(wx.EVT_BUTTON, self.OnDeselectAll, id=desBtn.GetId())
		self.Bind(wx.EVT_BUTTON, self.OnConfig, id=self.configBtn.GetId())
		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelected, id=self.check_list.GetId())

		### Layout
		self.Centre()
		self.Show(True)

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
		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelected, id=self.check_list.GetId())

	def OnApply(self, event):
		""" Call OnApply method ig CheckList class
		"""
		self.check_list.OnApply(event)

	def OnSelected(self, event):
		""" Item has been select and the documentation of module is immediately printed to the button CtrlText
		"""
		sel = self.check_list.GetFirstSelected()
		if sel != -1:
			item = self.check_list.GetItem(sel)
			new_element = self.check_list.GetPyData(sel)[0]
			doc = new_element.__doc__
			self.log.ChangeValue(doc + '\n' if doc else _("No documentation available for this plug-in."))
			module = inspect.getmodule(new_element)
			self.configBtn.Enable(hasattr(module, "Config"))

	def OnSelectAll(self, event):
		""" Select All button has been pressed and all plug-ins are enabled.
		"""
		num = self.check_list.GetItemCount()
		for i in xrange(num):
			self.check_list.CheckItem(i, True)

	def OnDeselectAll(self, event):
		""" Deselect All button has been pressed and all plug-ins are disabled.
		"""
		num = self.check_list.GetItemCount()
		for i in xrange(num):
			self.check_list.CheckItem(i, False)

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
			apply(module.Config, (), {'parent':self})

class ModelPluginsManager(wx.Frame):
	""" Plug-ins Manager for DEVSimPy Block
	"""
	def __init__(self, **kwargs):
		""" Constructor.
		"""

		self.model = kwargs.pop('model')

		wx.Frame.__init__(self, **kwargs)

		### plug-in panel
		self.pluginPanel = PluginsPanel(self)

		### two panel into plug-in panel
		rpanel = self.pluginPanel.GetRightPanel()
		lpanel = self.pluginPanel.GetLeftPanel()

		### checklist to insert in right panel
		self.CheckList = BlockPluginsList(rpanel)
		wx.CallAfter(self.CheckList.Populate, (self.model))

		### Buttons for insert or delete plug-ins
		self.addBtn = wx.Button(lpanel, wx.ID_ADD, size=(140, -1))
		self.delBtn = wx.Button(lpanel, wx.ID_DELETE, size=(140, -1))
		self.editBtn = wx.Button(lpanel, wx.ID_EDIT, size=(140, -1))
		self.updateBtn = wx.Button(lpanel, wx.ID_APPLY, size=(140, -1))
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

		self.CenterOnParent(wx.BOTH)
		self.Layout()

	@staticmethod
	def GetEditor(parent, model, filename=None):
		"""
		"""
		path = os.path.join(model.model_path, ZipManager.Zip.GetPluginFile(model.model_path)) if not filename else filename
		name = os.path.basename(path)

		### editor frame for the text of plug-ins
		editorFrame = Editor.GetEditor(None, \
									wx.ID_ANY, \
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
	 		except Exception, info:
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


		import __builtin__
		import gettext

		__builtin__.__dict__['HOME_PATH'] = os.getcwd()
		__builtin__.__dict__['_'] = gettext.gettext

		frame = ModelPluginsManager(parent=None, id=-1, title="Test", model=None)
		frame.Show()
		return True

	def OnQuit(self, event):
		self.Close()

if __name__ == '__main__':

	app = TestApp(0)
	app.MainLoop()