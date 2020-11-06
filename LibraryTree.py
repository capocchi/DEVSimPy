# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# LibraryTree.py ---
#                     --------------------------------
#                        Copyright (c) 2013
#                       Laurent CAPOCCHI
#                      University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 10/11/2013
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
import sys
import urllib.parse
import http.client
import copy
import inspect
import zipfile
import subprocess
import importlib
import tempfile

import Container
import Menu

from Utilities import replaceAll, getPYFileListFromInit, path_to_module, printOnStatusBar, NotificationMessage, install_and_import, module_list
from Decorators import BuzyCursorNotification
from Components import BlockFactory, DEVSComponent, GetClass
from ZipManager import Zip, getPythonModelFileName
from ReloadModule import recompile
from ImportLibrary import DeleteBox
from Complexity import GetMacCabeMetric

from pubsub import pub

_ = wx.GetTranslation

#----------------------------------------------------------------------------------------------------
class LibraryTree(wx.TreeCtrl):
	"""	Class of libraries tree of DEVSimPy model and Python files.

		EXT_LIB_FILE = tuple of considered DEVSimPy file extention.
		EXT_LIB_PYTHON_FLAG = flag to used model from Python file instanciation.
		EXCLUDE_DOMAIN = List of exclude directory
	"""

	### type of considered files
	EXT_LIB_FILE = ('.cmd', '.amd')
	### if True, Python files are visible in the tree
	EXT_LIB_PYTHON_FLAG = True
	### exclude rep from Domain
	EXCLUDE_DOMAIN = ['Basic', '.svn']
	### To sort models depending on their maccabe metric else is aphabetic
	COMPARE_BY_MACABE_METRIC = False

	###
	def __init__(self, *args, **kwargs):
		""" Constructor.
		"""

		super(LibraryTree, self).__init__(*args, **kwargs)

		### association between path (key) and tree item (value)
		self.ItemDico = {}

		### store metrics data
		self.MetricDico = {}

		isz = (16,16)
		il = wx.ImageList(isz[0], isz[1])
		if wx.VERSION_STRING < '4.0':
			self.fileidx = il.Add(wx.ArtProvider_GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, isz))
		else:
			self.fileidx = il.Add(wx.ArtProvider.GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, isz))

		self.fldridx = il.Add(wx.Bitmap(os.path.join(ICON_PATH_16_16, 'folder_close.png')))
		self.fldropenidx = il.Add(wx.Bitmap(os.path.join(ICON_PATH_16_16, 'folder_open.png')))
		self.atomicidx = il.Add(wx.Bitmap(os.path.join(ICON_PATH_16_16, 'atomic3.png')))
		self.coupledidx = il.Add(wx.Bitmap(os.path.join(ICON_PATH_16_16, 'coupled3.png')))
		self.pythonfileidx = il.Add(wx.Bitmap(os.path.join(ICON_PATH_16_16, 'pythonFile.png')))
		self.pythoncfileidx = il.Add(wx.Bitmap(os.path.join(ICON_PATH_16_16, 'pyc.png')))
		self.not_importedidx = il.Add(wx.Bitmap(os.path.join(ICON_PATH_16_16, 'no_ok.png')))
		self.SetImageList(il)
		self.il = il

		self.root = self.AddRoot(os.path.basename(DOMAIN_PATH))
		self.SetItemBold(self.root)

		self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.OnRightItemClick)
		self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightClick)
		self.Bind(wx.EVT_TREE_ITEM_MIDDLE_CLICK, self.OnMiddleClick)
		self.Bind(wx.EVT_LEFT_DOWN,self.OnLeftClick)
		self.Bind(wx.EVT_MOTION, self.OnMotion)

		### for Phoenix
		if wx.VERSION_STRING >= '4.0':
			self.InsertItemBefore = self.InsertItem
			self.SetPyData = self.SetItemData
			self.GetPyData = self.GetItemData
			self.GetItemPyData = self.GetItemData

	@classmethod
	def AddToSysPath(self, absdName):
		""" Add path to the sys.path module
		"""

        ### add directory to the sys.path for importing
		if absdName not in sys.path:
			sys.path.append(absdName)

		dirname = os.path.dirname(absdName)

		### if external domain we add also the dirname directory
		if not dirname.startswith(DOMAIN_PATH):
			if dirname not in sys.path:
				### insert at position 2 before the path of the devsimpy source directory!
				sys.path.insert(2,dirname)

		### if module from Domain we add the DOMAIN_PATH is sys.path
		elif DOMAIN_PATH not in sys.path:
            ### Add DOMAIN_PATH and its parent directory to the sys.path
			### in order to allows the user to import their module using Domain. or directly without the name of domain
			sys.path.extend([DOMAIN_PATH,os.path.dirname(DOMAIN_PATH)])

	###
	def Populate(self, chargedDomainList = []):
		""" Populate the Tree from a list of domain path.
		"""

		assert self.root != None, _("Missing root")
		#import threading

		### add DOMAIN_PATH in sys.path whatever happens
		LibraryTree.AddToSysPath(DOMAIN_PATH)

		L = []
		for absdName in chargedDomainList:

			### add absdName to sys.path (always before InsertNewDomain)
			LibraryTree.AddToSysPath(absdName)

			### add new domain
			#threading.Thread(target=self.InsertNewDomain,
        	#args=(absdName, self.root, list(self.GetSubDomain(absdName, self.GetDomainList(absdName)).values())[0],)
    		#).start()
			self.InsertNewDomain(absdName, self.root, list(self.GetSubDomain(absdName, self.GetDomainList(absdName)).values())[0])

		wx.CallAfter(self.SortChildren,self.root)

	###
	def OnMotion(self, evt):
		""" Motion engine over item.
		"""
		item, flags = self.HitTest(evt.GetPosition())

		if (flags & wx.TREE_HITTEST_ONITEMLABEL) and not evt.LeftIsDown():
		
			path = self.GetItemData(item)


			if os.path.isdir(path):
				model_list = self.GetModelList(path)
				domain_list = self.GetDomainList(path)

				tip = '\n'.join(model_list) if model_list else ""
				tip += '\n'
				tip += '\n'.join(domain_list) if domain_list else ""

			### is last item
			else:
				module = BlockFactory.GetModule(path)
				info = Container.CheckClass(path)

				if isinstance(info, tuple):
					doc = str(info)
				elif isinstance(module, tuple):
					doc = str(module)
				else:
					doc = inspect.getdoc(module)

				tip = doc if doc is not None else _("No documentation for selected model.")

			### add maccabe metric info
			if item in self.MetricDico:
				mcc = self.MetricDico[item]['mcc']
				tip =''.join([tip,'\n','macCabe metric: %d'%mcc])

			self.SetToolTip(tip)
		
		else:
			self.SetToolTip(None)

		### else the drag and drop dont run
		evt.Skip()

	###
	def OnLeftClick(self, evt):
		""" Left click has been invoked.
		"""

		self.UnselectAll()
		mainW = wx.GetApp().GetTopWindow()
		printOnStatusBar(mainW.statusbar, {0:'', 1:''})
		#self.SetFocus()
		evt.Skip()

	###
	def OnMiddleClick(self, evt):
		""" Middle click has been invoked.
		"""
		item_selected = evt.GetItem()

		if not self.ItemHasChildren(item_selected):
			path = self.GetItemPyData(item_selected)
			mainW = wx.GetApp().GetTopWindow()
			nb2 = mainW.GetDiagramNotebook()
			canvas = nb2.GetPage(nb2.GetSelection())
			### define path for Python and model component

			if path.endswith('.py'):
				### create component
				m = BlockFactory.CreateBlock(	canvas = canvas,
									x = 140,
									y = 140,
									label = self.GetItemText(item_selected),
									id = 0,
									inputs = 1,
									outputs = 1,
									python_file = path,
									model_file = "")
				if m:

					# Adding graphical model to diagram
					canvas.AddShape(m)

					sys.stdout.write(_("Adding DEVSimPy model: \n"))
					sys.stdout.write(repr(m))

					# focus
					#canvas.SetFocus()

			else:
				sys.stdout.write(_("This option has not been implemented yet. \n"))
	###
	def OnRightClick(self, evt):
		""" Right click has been invoked.
		"""
		pos = evt.GetPosition()
		item, flags = self.HitTest(pos)

		# if no, evt.Skip is propagated to OnRightItemClick
		if not item.IsOk():
			self.PopupMenu(Menu.LibraryPopupMenu(self), pos)
		else:
			self.SelectItem(item)
			evt.Skip()

	###
	def OnRightItemClick(self, evt):
		""" Right click on a item has been invoked.
		"""
		self.PopupMenu(Menu.ItemLibraryPopupMenu(self), evt.GetPoint())
		evt.Skip()

	###
	def OnDelete(self, evt):
		""" Delete the item from Tree
		"""

		item = self.GetFocusedItem()
		if item.IsOk():
			path = self.GetItemPyData(item)

			if path and os.path.exists(path):
				### msgbox to select what you wan to delete: file or/and item ?
				db = DeleteBox(self, wx.NewIdRef(), _("Delete Options"))

				if db.ShowModal() == wx.ID_OK:

					### delete file
					if db.rb2.GetValue():
						label = os.path.basename(path)
						dial = wx.MessageDialog(None, _('Are you sure to delete the python file %s ?')%(label), label, wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
						if dial.ShowModal() == wx.ID_YES:
							try:
								### delete file
								os.remove(path)
								### delete item
								self.RemoveItem(item)

							except Exception as info:
								info = str(info)
								sys.stdout.write(_("%s not deleted! \n Error: %s")%(label,info))

						dial.Destroy()

					else:
						self.RemoveItem(item)

					###TODO unload associated module

			else:
				wx.MessageBox(_("No library selected!"),_("Delete Manager"))

	def UpdateSubLib(self, path:str)->bool:
		""" Do update lib.
		"""
		### reload .py module from path 
		for s in module_list(path):
			module_name = ".".join(s.split('.')[1:])
			if module_name in sys.modules:
				module = sys.modules[module_name]
				dirname = os.path.dirname(module.__file__)
				try:
					### .amd or .cmd
					if zipfile.is_zipfile(dirname):
						zf = Zip(dirname)
						if isinstance(zf.ReImport(), Exception):
							return False
					else:
						importlib.reload(module)
				except:
					return False
		return True

	###
	@BuzyCursorNotification
	def OnUpdateSubLib(self, evt):
		""" ReImport all module (.py and .amd/.cmd) in lib.
		"""
		item = self.GetFocusedItem()
		path = self.GetItemPyData(item)
		if self.UpdateSubLib(path):
			NotificationMessage(_('Information'), _('%s has been updated!')%os.path.basename(path), parent=self, timeout=5)
		else:
			NotificationMessage(_('Error'), _('%s has not been updated! See traceback for more information')%os.path.basename(path), parent=self, timeout=5)

	###
	def OnNewModel(self, evt):
		""" New model action has been invoked.
		"""

		mainW = wx.GetApp().GetTopWindow()
		nb2 = mainW.GetDiagramNotebook()
		canvas = nb2.GetPage(nb2.GetSelection())

		gmwiz = Container.ShapeCanvas.OnStartWizard(canvas, evt)

		### update the view of the domain
		if gmwiz:

			### save .dat file in the .cmd or .amd
			m = BlockFactory.CreateBlock(label = gmwiz.label,
										inputs = gmwiz.inputs,
										outputs = gmwiz.outputs,
										python_file = gmwiz.python_path,
										model_file = gmwiz.model_path)
			if m:
				if not m.SaveFile(gmwiz.model_path):
					dlg = wx.MessageDialog(self, \
										_('Error saving file %s\n')%os.path.basename(gmwiz.model_path), \
										gmwiz.label, \
										wx.OK | wx.ICON_ERROR)
					dlg.ShowModal()

			item = self.ItemDico[os.path.dirname(gmwiz.model_path)]
			self.UpdateDomain(self.GetPyData(item))

			### sort all item
			self.SortChildren(self.root)

		# Cleanup
		if gmwiz: gmwiz.Destroy()

	def OnNewDir(self, evt):
		""" New dir has been invoked.
		"""
		pass

	###
	def GetDomainList(self, dName):
		""" Get the list of sub-directory of dName directory
		"""

		if dName.startswith('http'):
			o = urlparse(dName)
			if dName.startswith('https'):
				c = http.client.HTTPSConnection(o.netloc)
			else:
				c = http.client.HTTPConnection(o.netloc)
			c.request('GET', o.path+'/__init__.py')

			r = c.getresponse()

			code = r.read()
			if r.status == 200:
				exec(code)
				return __all__
			else:
				return []

		else:
			return [f for f in os.listdir(dName) if os.path.isdir(os.path.join(dName, f)) and f not in LibraryTree.EXCLUDE_DOMAIN and f != '__pycache__'] if os.path.isdir(dName) else []

	###
	def GetItemChildren(self, item, recursively = False):
		""" Return the children of item as a list. This method is not )
		part of the API of any tree control, but very convenient to
		have available.
		"""

		children = []
		child, cookie = self.GetFirstChild(item)
		while child:
			children.append(child)
			if recursively:
				children.extend(self.GetItemChildren(child, True))
			child, cookie = self.GetNextChild(item, cookie)
		return children

	@staticmethod
	def GetPYFileList(dName, ext=".py"):
		""" Return .py files that are instanciable. 
		"""
		
		### import are here because the simulator (PyDEVS or PyPDEVS) require it
		from DomainInterface.DomainBehavior import DomainBehavior

		try:
			name_list = getPYFileListFromInit(os.path.join(dName,'__init__.py'), ext)
			py_file_list = []
			
			for s in name_list:
				python_file = os.path.join(dName, s+ext)
				### test if tmp is only composed by python file (case of the user write into the __init__.py file directory name is possible ! then we delete the directory names)
				if os.path.isfile(python_file):

					cls = GetClass(python_file)

					if cls is not None and not isinstance(cls, tuple):

						### only model that herite from DomainBehavior is shown in lib
						if issubclass(cls, DomainBehavior):
							py_file_list.append(s)
						else:
							sys.stderr.write(_("%s not imported: Class is not DomainBehavior\n"%(s)))

					### If cls is tuple, there is an error but we load the model to correct it.
					### If its not DEVS model, the Dnd don't allows the instantiation and when the error is corrected, it don't appear before a update.
					else:
						py_file_list.append(s)

		except Exception as info:
			py_file_list = []
			# if dName contains a python file, __init__.py is forced
			if os.path.isdir(dName):
				for f in os.listdir(dName):
					if f.endswith(ext):
						sys.stderr.write(_("Exception, %s not imported: %s \n"%(dName,info)))
						break

		return py_file_list

	###
	def GetModelList(self, dName):
		""" Get the list of files from dName directory.
		"""

		### list of py file from __init__.py
		if LibraryTree.EXT_LIB_PYTHON_FLAG:

			### list of py file from url
			if dName.startswith('http'):

				o = urlparse(dName)
				c = http.client.HTTPConnection(o.netloc)
				c.request('GET', o.path+'/__init__.py')

				r = c.getresponse()
				code = r.read()

				if r.status == 200:
					exec(code)
					tmp = [s for s in __all__ if s.replace('\n','').replace('\t','').replace(',','').replace('"',"").replace('\'',"").strip()]
					### test if the content of __init__.py file is python file (isfile equivalent)
					py_file_list = [s for s in tmp if 'python' in urlopen(dName+'/'+s+'.py').info().type]

				else:
					py_file_list = []

				return py_file_list
			else:
				py_file_list = LibraryTree.GetPYFileList(dName)
				
				### try to list the pyc file
				if py_file_list == []:
					py_file_list = LibraryTree.GetPYFileList(dName, '.pyc')
					
		else:
			py_file_list = []

		# list of amd and cmd files
		devsimpy_file_list = [f for f in os.listdir(dName) if os.path.isfile(os.path.join(dName, f)) and (f[:2] != '__') and (f.endswith(LibraryTree.EXT_LIB_FILE))]

		return py_file_list + devsimpy_file_list

	###
	def InsertNewDomain(self, dName, parent, L = []):
		""" Recurrent function that insert new Domain on library panel.
		"""

		### first only for the root
		if dName not in list(self.ItemDico.keys()):
		
			label = os.path.basename(dName) if not dName.startswith('http') else [a for a in dName.split('/') if a!=''][-1]
			id = self.InsertItemBefore(parent, 0, label)
			self.SetItemImage(id, self.fldridx, wx.TreeItemIcon_Normal)
			self.SetItemImage(id, self.fldropenidx, wx.TreeItemIcon_Expanded)
			self.SetItemBold(id)
			self.ItemDico.update({dName:id})
			self.SetPyData(id,dName)

		### end
		if L == []:
			return
		else:
			item = L.pop(0)

			isunicode = isinstance(item, str)
			isstr = isinstance(item, str)
			isdict = isinstance(item, dict)

			### element to insert in the list
			D = []
			### if child is build from DEVSimPy
			if isstr:

				### parent is retrieved from dict
				parent = self.ItemDico[dName]
				assert parent != None
	
				### parent path
				parentPath = self.GetPyData(parent)
				come_from_net = parentPath.startswith('http')

				### comma replace
				item = item.strip()

				### suppression de l'extention su .cmd (model atomic lu à partir de __init__ donc pas d'extention)
				if item.endswith('.cmd'):
					### gestion de l'importation de module (.py) associé au .cmd si le fichier .py n'a jamais été decompresssé (pour edition par exemple)
					if not come_from_net:
						path = os.path.join(parentPath, item)
						zf = Zip(path)
						module = zf.GetModule()
						image_file = zf.GetImage()
					else:
						path = "".join([parentPath,'/',item,'.py'])
						module = load_module_from_net(path)

					### check error
					error = isinstance(module, Exception)

					### change icon depending on the error and the presence of image in amd
					if error:
						img = self.not_importedidx
					elif image_file is not None:
						img = self.il.Add(image_file.ConvertToBitmap())
					else:
						img = self.coupledidx

					### insert into the tree
					id = self.InsertItemBefore(parent, 0, os.path.splitext(item)[0], img, img)
					self.SetPyData(id, path)

					self.MetricDico.update({id:{'mcc':0.0, 'parent':parent}})
					s = sum([d['mcc'] for id,d in self.MetricDico.items() if d['parent']==parent])
					self.MetricDico.update({parent:{'mcc':s, 'parent':None}})

				elif item.endswith('.amd'):
					### gestion de l'importation de module (.py) associé au .amd si le fichier .py n'a jamais été decompresssé (pour edition par exemple)
					if not come_from_net:
						path = os.path.join(parentPath, item)
						zf = Zip(path)
						module = zf.GetModule()
						image_file = zf.GetImage()
					else:
						path = "".join([parentPath,'/',item,'.py'])
						module = load_module_from_net(path)

					### check error
					error = isinstance(module, Exception)

					### change icon depending on the error and the presence of image in amd
					if error:
						img = self.not_importedidx
					elif image_file is not None:
						img = self.il.Add(image_file.ConvertToBitmap())
					else:
						img = self.atomicidx

					mcc = GetMacCabeMetric(path)

					### insert in the tree
					id = self.InsertItemBefore(parent, 0, os.path.splitext(item)[0], img, img)
					self.SetPyData(id, path)

					self.MetricDico.update({id:{'mcc':mcc, 'parent':parent}})
					s = sum([d['mcc'] for id,d in self.MetricDico.items() if d['parent']==parent])
					self.MetricDico.update({parent:{'mcc':s, 'parent':None}})

				else:
					
					path = os.path.join(parentPath, "".join([item,'.py'])) if not come_from_net else "".join([parentPath,'/',item,'.py'])

					### try for .pyc
					ispyc = False
					if not os.path.exists(path):
						path = os.path.join(parentPath, "".join([item,'.pyc'])) if not come_from_net else "".join([parentPath,'/',item,'.pyc'])
						ispyc = True

					devs = Container.CheckClass(path)
					
					#mcc = float(subprocess.check_output('python {} {}'.format('Complexity.py', path), shell = True))
					mcc = GetMacCabeMetric(path)

					error = isinstance(devs, tuple)
					img = self.not_importedidx if error else self.pythoncfileidx if ispyc else self.pythonfileidx
					
					### insert in the tree
					id = self.InsertItemBefore(parent, 0, item, img, img)
					self.SetPyData(id, path)

					self.MetricDico.update({id:{'mcc':mcc, 'parent':parent}})
					s = sum([d['mcc'] for id,d in self.MetricDico.items() if d['parent']==parent])
					self.MetricDico.update({parent:{'mcc':s, 'parent':None}})

				### error info back propagation
				if error:
					while(parent):
						self.SetItemImage(parent, self.not_importedidx, wx.TreeItemIcon_Normal)
						### next parent item
						parent = self.GetItemParent(parent)

				### insertion des donnees dans l'item et gestion du ItemDico
				self.ItemDico.update({os.path.join(parentPath,item,):id})

			### si le fils est un sous repertoire contenant au moins un fichier (all dans __init__.py different de [])
			elif isdict and list(item.values()) != [[]]:

				### name to insert in the tree
				dName = os.path.basename(list(item.keys())[0])

				### new parent
				parent = self.ItemDico[os.path.dirname(list(item.keys())[0])] if not dName.startswith('http') else self.ItemDico[list(item.keys())[0].replace('/'+dName,'')]

				assert(parent!=None)

				### insert of the fName above the parent
				id = self.InsertItemBefore(parent, 0, dName)
				
				self.SetItemBold(id)

				self.SetItemImage(id, self.fldridx, wx.TreeItemIcon_Normal)
				self.SetItemImage(id, self.fldropenidx, wx.TreeItemIcon_Expanded)

				### stockage du parent avec pour cle le chemin complet avec extention (pour l'import du moule dans le Dnd)
				self.ItemDico.update({list(item.keys())[0]:id})
				self.SetPyData(id,list(item.keys())[0])

				self.MetricDico.update({id:{'mcc':0.0, 'parent':parent}})
				self.MetricDico.update({parent:{'mcc':0.0, 'parent':None}})

				### for the childrens of the sub-domain
				for elem in list(item.values())[0]:
					# si elem simple (modèle couple ou atomic)
					if isinstance(elem, str):
						### replace the spaces
						elem = elem.strip() #replace(' ','')

						### parent provisoir
						p = self.ItemDico[list(item.keys())[0]]
						assert(p!=None)
						come_from_net = list(item.keys())[0].startswith('http')
						### si model atomic
						if elem.endswith('.cmd'):
							### gestion de l'importation de module (.py) associé au .amd si le fichier .py n'a jamais été decompresssé (pour edition par exemple)
							if not come_from_net:
								path = os.path.join(list(item.keys())[0], elem)
								zf = Zip(path)
								module = zf.GetModule()
								image_file = zf.GetImage()
							else:
								path = "".join([list(item.keys())[0],'/',elem,'.py'])
								module = load_module_from_net(path)

							### check error
							error = isinstance(module, Exception)

							### change icon depending on the error and the presence of image in amd
							if error:
								img = self.not_importedidx
							elif image_file is not None:
								img = self.il.Add(image_file.ConvertToBitmap())
							else:
								img = self.coupledidx

							### insertion dans le tree
							id = self.InsertItemBefore(p, 0, os.path.splitext(elem)[0], img, img)
							self.SetPyData(id, path)

							self.MetricDico.update({id:{'mcc':0.0, 'parent':parent}})
							s = sum([d['mcc'] for id,d in self.MetricDico.items() if d['parent']==parent])
							self.MetricDico.update({parent:{'mcc':s, 'parent':None}})

						elif elem.endswith('.amd'):
							### gestion de l'importation de module (.py) associé au .amd si le fichier .py n'a jamais été decompresssé (pour edition par exemple)
							if not come_from_net:
								path = os.path.join(list(item.keys())[0], elem)
								zf = Zip(path)
								module = zf.GetModule()
								image_file = zf.GetImage()
							else:
								path = "".join([list(item.keys())[0],'/',elem,'.py'])
								module = load_module_from_net(path)

							### check error
							error = isinstance(module, Exception)

							### change icon depending on the error and the presence of image in amd
							if error:
								img = self.not_importedidx
							elif image_file is not None:
								img = self.il.Add(image_file.ConvertToBitmap())
							else:
								img = self.atomicidx

							mcc = GetMacCabeMetric(path)

							### insert in the tree
							id = self.InsertItemBefore(p, 0, os.path.splitext(elem)[0], img, img)
							self.SetPyData(id, path)

							self.MetricDico.update({id:{'mcc':mcc, 'parent':parent}})
							s = sum([d['mcc'] for id,d in self.MetricDico.items() if d['parent']==parent])
							self.MetricDico.update({parent:{'mcc':s, 'parent':None}})

						else:
			
							path = os.path.join(list(item.keys())[0],"".join([elem,'.py'])) if not list(item.keys())[0].startswith('http') else list(item.keys())[0]+'/'+elem+'.py'
							### try for .pyc file
							ispyc = False
							if not os.path.exists(path):
								path = os.path.join(list(item.keys())[0],"".join([elem,'.pyc'])) if not list(item.keys())[0].startswith('http') else list(item.keys())[0]+'/'+elem+'.pyc'
								ispyc = True
								
							devs = Container.CheckClass(path)

							mcc = GetMacCabeMetric(path)

							error = isinstance(devs, tuple)
							img = self.not_importedidx if error else self.pythoncfileidx if ispyc else self.pythonfileidx

							### insert in the tree
							id = self.InsertItemBefore(p, 0, elem, img, img)
							self.SetPyData(id, path)
							self.MetricDico.update({id:{'mcc':mcc, 'parent':parent}})

							s = sum([d['mcc'] for id,d in self.MetricDico.items() if d['parent']==parent])
							self.MetricDico.update({parent:{'mcc':s, 'parent':None}})

						### error info back propagation
						if error:
							### insert error to the doc field
							while(p):
								self.SetItemImage(p, self.not_importedidx, wx.TreeItemIcon_Normal)
								### next parent item
								p = self.GetItemParent(p)
						
						self.ItemDico.update({os.path.join(list(item.keys())[0], elem):id})

					else:
						### in order to go up the information in the list
						D.append(elem)

				### update with whole name
				dName = list(item.keys())[0]

			### for spash screen
			try:
				### format the string depending the nature of the item
				if isdict:
					item = " ".join([os.path.basename(list(item.keys())[0]), 'from', os.path.basename(os.path.dirname(list(item.keys())[0]))])
				else:
					item = " ".join([item, 'from', os.path.basename(dName)])

				pub.sendMessage('object.added', message='Loading %s domain...'%item)
			except:
				pass

			### managment of the recursion
			if D:
				self.InsertNewDomain(dName, parent, D)
			
			try:
				self.SortChildren(parent)
			except:
				pass

			return self.InsertNewDomain(dName, parent, L)

    ###
	def GetSubDomain(self, dName, domainSubList = []):
		""" Get the dico composed by all of the sub domain of dName
			(like{'../Domain/PowerSystem': ['PSDomainStructure', 'PSDomainBehavior', 'Object', 'PSSDB', {'../Domain/PowerSystem/Rt': []}, {'../Domain/PowerSystem/PowerMachine': ['toto.cmd', 'Integrator.cmd', 'titi.cmd', 'Mymodel.cmd', {'../Domain/PowerSystem/PowerMachine/TOTO': []}]}, {'../Domain/PowerSystem/Sources': ['StepGen', 'SinGen', 'CosGen', 'RampGen', 'PWMGen', 'PulseGen', 'TriphaseGen', 'ConstGen']}, {'../Domain/PowerSystem/Sinks': ['To_Disk', 'QuickScope']}, {'../Domain/PowerSystem/MyLib': ['', 'model.cmd']}, {'../Domain/PowerSystem/Hybrid': []}, {'../Domain/PowerSystem/Continuous': ['WSum', 'Integrator', 'Gain', 'Gain2', 'NLFunction']}]}
			)
		"""

		if domainSubList == []:
			### attention il faut que le fichier __init__.py respecte une certain ecriture
			return {dName:self.GetModelList(dName)}
		else:

			### on comptabilise les fichiers si il y en a dans le rep courant (la recusion s'occupe des sous domaines)
			D = {dName: self.GetModelList(dName)}
			### on lance la recursion sur les repertoires fils
			for d in domainSubList:
				p = os.path.join(dName, d)
				D[dName].append(self.GetSubDomain(p, self.GetDomainList(p)))
			return D

	###
	def GetChildRoot(self):
		""" Return the list compsed by the childs of the Root
		"""
		return [str(self.GetItemText(s)) for s in self.GetItemChildren(self.root)]

	###
	def IsChildRoot(self, dName):
		""" Return True if dName library has child Root
		"""
		return (dName in self.GetChildRoot())

	###
	def HasString(self, s = ""):
		""" Return s parameter if exists in opened libraries
		"""
		return s in [str(self.GetItemText(item)) for item in list(self.ItemDico.values())]

	###
	def CheckItem(self, path):
		""" Check if the model is valide
		"""

		item = self.ItemDico[path]
		file_path = "".join([path,'.py'])

		### try to find pyc files
		if not os.path.exists(file_path):
			file_path = "".join([path,'.pyc'])

		if os.path.exists(file_path):

			### Check the class
			info = Container.CheckClass(file_path)

			### there is error during the chek of class?
			if isinstance(info, tuple):

				### if module are missing, we propose to install him with pip
				if ModuleNotFoundError in info:
					package = info[1].name
					if install_and_import(package):
						wx.CallAfter(self.UpdateAll)

				### else there is an error in the code of the model...
				else:

					### recompile if no error
					info = recompile(path_to_module(file_path))

					### there is error during recompilation?
					if isinstance(info, (Exception,str)):
						### Until it has parent, we redifine icon to inform user
						while(item):
							### change image
							self.SetItemImage(item, self.not_importedidx, wx.TreeItemIcon_Normal)
							### next parent item
							item = self.GetItemParent(item)
					else:
							### change image
							self.SetItemImage(item, self.pythonfileidx, wx.TreeItemIcon_Normal)

							#### Until it has parent, we redifine icon to inform user
							while(item):
								#### change image
								self.SetItemImage(item, self.fldropenidx if self.IsExpanded(item) else self.fldridx, wx.TreeItemIcon_Normal)
								#### next parent item
								item = self.GetItemParent(item)
		else:
			sys.stdout.write("File %s is not checked!")

	###
	def UpdateDomain(self, path):
		""" Update the Tree Library with new path of the corresponding domain
		"""

		### only of the path is in the tree
		if self.HasString(os.path.basename(path)):
			dName = path

			### try to find focused item from dName
			try:
				item = self.ItemDico[dName]
			### if dName is not present in ItemDico but exist and represent the same directory, we find the path strored in ItemDico
			except KeyError:
				for p in self.ItemDico:
					if p.endswith(os.path.basename(dName)):
						item = self.ItemDico[p]

			### save parent before deleting item
			parent = self.GetItemParent(item)

			### save expanded info before deleting item
			L = [dName] if self.IsExpanded(item) else []
			for k,v in list(self.ItemDico.items()):
				if self.IsExpanded(v):
					L.append(k)

			### remove for create udpated new item
			self.RemoveItem(item)

			### insertion du nouveau domain
			self.InsertNewDomain(dName, parent, list(self.GetSubDomain(dName, self.GetDomainList(dName)).values())[0])

			### module checking
			for d in list(self.GetSubDomain(dName, self.GetDomainList(dName)).values())[0]:
				if isinstance(d, dict):
					name_list =  list(d.values())[0]
					if name_list:
						for name in [a for a in name_list if not isinstance(a, dict)]:
							path = list(d.keys())[0]
							if not name.endswith(('.cmd','.amd')):
								self.CheckItem(os.path.join(path, name))

			### restor expanded item
			for item in [self.ItemDico[name] for name in L]:
				self.Expand(item)

	@BuzyCursorNotification
	def OnUpdateAll(self, event):
		""" Update all imported domain
		"""
		result = self.UpdateAll()
		if len(result) == 0:
			NotificationMessage(_('Information'), _("All libraries have been succeffully updated!"), self, timeout=5)
		else:
			NotificationMessage(_('Error'), _("The following libraries updates crash:\n %s")%" \n".join(map(os.path.basename,result)), self, timeout=5)

	def OnMCCClick(self, event):
		""" 
		"""
		tb = event.GetEventObject()
		LibraryTree.COMPARE_BY_MACABE_METRIC = not tb.GetToolState(Menu.ID_MCC_LIB)
		self.OnUpdateAll(event)

	###
	def UpdateAll(self):
		""" Update all loaded libraries.
		"""
	
		fault = set()
		### update all Domain
		for item in self.GetItemChildren(self.GetRootItem()):
			path = self.GetItemPyData(item)
			if self.UpdateSubLib(path):
				self.UpdateDomain(self.GetPyData(item))
			else:
				fault.add(path)

		### to sort domain
		wx.CallAfter(self.SortChildren,self.root)
		
		return fault

		#self.SortChildren(self.root)

	###
# 	def UpgradeAll(self, evt):
# 		"""
# 		"""
# 		progress_dlg = wx.ProgressDialog(_("DEVSimPy upgrade libraries"),
# 								_("Connecting to %s ...")%"code.google.com", parent=self,
# 								style=wx.PD_APP_MODAL | wx.PD_ELAPSED_TIME)
# 		progress_dlg.Pulse()
#
# 		thread = UpgradeLibThread(progress_dlg)
#
# 		while thread.isAlive():
# 			time.sleep(0.3)
# 			progress_dlg.Pulse()
#
# 		progress_dlg.Destroy()
# 		wx.SafeYield()
#
# 		return thread.finish()

	def OnCompareItems(self, item1, item2):
		""" overriden method OnCompareItems  used by sortChildren
		"""

		if LibraryTree.COMPARE_BY_MACABE_METRIC:
			t1 = float(self.MetricDico[item1]['mcc'])
			t2 = float(self.MetricDico[item2]['mcc'])
		
			if t1 > t2: return -1
			if t1 == t2: return 0
			return 1
		else:
			t1 = self.GetItemText(item1)
			t2 = self.GetItemText(item2)

			if t1 < t2: return -1
			if t1 == t2: return 0
			return 1

	###
	def RemoveItem(self, item):
		""" Remove item from Tree and also the corresponding elements of ItemDico
		"""

		### delete all references from the ItemDico
		for key in copy.copy(self.ItemDico):
			if os.path.basename(self.GetPyData(item)) in key.split(os.sep):
				del self.ItemDico[key]

		self.Delete(item)

	###
	def OnItemRefresh(self, evt):
		""" Refresh action has been invoked.
		"""

		try:
			item = self.GetSelection()
			path = self.GetItemPyData(item)
			ext = os.path.splitext(path)[1]

			if ext in (".py",".pyc"):
				self.CheckItem(os.path.splitext(path)[0])
			else:
				self.CheckItem(path)
		except:
			NotificationMessage(_('Error'), _("Error updating the model %s")%self.GetItemText(item), self, timeout=5)
		finally:
			if self.GetItemImage(item) != 1:
				
				NotificationMessage(_('Information'), _("Model %s has been succeffully updated!")%self.GetItemText(item), self, timeout=5)

	###
	def OnItemEdit(self, evt):
		""" Edition menu has been invoked.
		"""

		item = self.GetSelection()
		path = self.GetItemPyData(item)

		### virtual DEVS component just for edition
		devscomp = DEVSComponent()

		### path depends on the nature of droped component
		### if pure python path
		if path.endswith('.py'):
			devscomp.setDEVSPythonPath(path)
		### if devsimpy model
		elif zipfile.is_zipfile(path):
			#zf = Zip(path)
			devscomp.setDEVSPythonPath(os.path.join(path, getPythonModelFileName(path)))
			devscomp.model_path = path
		else:
			sys.stdout.write(_('The code of this type of model is not editable.'))
			return

		### call frame editor
		DEVSComponent.OnEditor(devscomp, evt)

	###
	def OnItemRename(self, evt):
		""" Rename action has been invoked.
		"""

		item = self.GetSelection()
		name = self.GetItemText(item)

		### dialog to ask new label
		if wx.VERSION_STRING < '4.0':
			d = wx.TextEntryDialog(self, _('New file name'), defaultValue = name, style=wx.OK)
		else:
			d = wx.TextEntryDialog(self, _('New file name'), value = name, style=wx.OK)
		d.ShowModal()

		### new label
		new_label = d.GetValue()
		### if new and old label are different
		if new_label != name:

			### path of file
			old_path = self.GetItemPyData(item)
			
			old_bn = os.path.basename(old_path)
			dn = os.path.dirname(old_path)
			old_name, ext = os.path.splitext(old_bn)
			
			new_filepath = "".join([os.path.join(dn, new_label),ext])

			if old_path.endswith('.py'):
				
				#read input file
				fin = open(old_path, "rt")
				#read file contents to string
				data = fin.read()
				
				if 'DomainBehavior' in data or 'DomainStructure' in data:
					
					#replace all occurrences of the required string
					data = data.replace(old_name, new_label)
					#close the input file
					fin.close()

					#open the input file in write mode
					fin = open(old_path, "wt")
					#overrite the input file with the resulting data
					fin.write(data)
					#close the file
					fin.close()

					### relace on file system
					os.rename(old_path, new_filepath)

					### replace in __init__.py file
					replaceAll(os.path.join(dn,'__init__.py'), old_name, new_label)
				else:
					wx.MessageBox(_("It seams that the python file dont inherite of the DomainBehavior or DomainStructure classes.\n \
									Please correct this aspect before wanted to rename the python file from DEVSimPy."), _("Error"), wx.OK|wx.ICON_ERROR)
					return

			### if devsimpy model
			elif zipfile.is_zipfile(old_path):
				### extract behavioral python file (from .amd or .cmd) to tempdir 
				### in order to rename it and change the name of contening class
				temp_file = None
				with zipfile.ZipFile(old_path) as zf:
					### find all python files
					for file in zf.namelist():
						if file.endswith(".py"):
							r = repr(zf.read(file))
							### first find python file with the same of the archive
							if file.endswith(old_bn):
								#new_bn = os.path.basename(new_filepath)
								temp_file = zf.extract(old_bn,tempfile.gettempdir())
								new_temp_file = temp_file

							### then find a python file that inherite of the DomainBehavior or StructureBehavior class
							elif 'DomainBehavior' in r or 'DomainStructure' in r:

								old_name = os.path.splitext(file)[0]
								
								### first we must change the name of this python file in order to have the same as the archive!
								temp_file = zf.extract(file,tempfile.gettempdir())
								new_temp_file = os.path.join(tempfile.gettempdir(),new_label+'.py')
								### rename temp_file to new_temp_file according to the correspondance between the name of the python file and the name of the archive
								### for exemple C:\Users\Laurent\AppData\Local\Temp\MyOld.py C:\Users\Laurent\AppData\Local\Temp\MyNew.py
								if os.path.isfile(new_temp_file):
									os.remove(new_temp_file)

								os.rename(temp_file, new_temp_file)

						elif file.endswith(".dat"):
							import pickle
							### replace in new_temp_file file
							temp_dat_file = zf.extract(file,tempfile.gettempdir())

							with open(temp_dat_file, 'rb') as sf:
								scores = pickle.load(sf)
					
							scores[0] = new_filepath
							scores[1] = os.path.join(new_filepath,os.path.basename(new_filepath).replace('.amd','.py').replace('.cmd','.py'))

							with open(temp_dat_file, "wb") as sf:
								pickle.dump(scores, sf)

				if temp_file:

					print("Replace %s by %s into %s"%(old_name,new_label,new_temp_file))
					### replace in new_temp_file file
					replaceAll(new_temp_file, old_name, new_label)

					print("open %s"%old_path)
					zip = Zip(old_path)
					
					if zip.Delete([os.path.basename(temp_file)]):
						print("Delete %s"%os.path.basename(temp_file))
						
						print("Update %s"%new_temp_file)
						zip.Update([new_temp_file,temp_dat_file])

						print("rename %s to %s"%(old_path,new_filepath))	
						
						### relace on file system
						os.rename(old_path, new_filepath)

					#try:
					#	os.remove(temp_file)
					#except:
					#	pass

				else:
					wx.MessageBox(_("It seams that the python filename and the model name are diffrent!\n \
									Please correct this aspect by extracting the archive."), _("Error"), wx.OK|wx.ICON_ERROR)
					return
			else:
				sys.stdout.write(_('Rename failed!'))
				return

			self.UpdateAll()

	###
	def OnItemDocumentation(self, evt):
		""" Display the item's documentation on miniFrame.
		"""

		item = self.GetSelection()
		path = self.GetItemPyData(item)
		name = self.GetItemText(item)

		module = BlockFactory.GetModule(path)
		info = Container.CheckClass(path)

		if isinstance(info, tuple):
			doc = str(info)
		elif isinstance(module, tuple):
			doc = str(module)
		else:
			doc = inspect.getdoc(module)

		### Add maccabe complexity measure
		doc += "".join([_("\n\n MacCabe Complexity: %d")%self.MetricDico[item]['mcc']])

		if doc:
			dlg = wx.lib.dialogs.ScrolledMessageDialog(self, doc, _("%s Documentation")%name, style=wx.OK|wx.ICON_EXCLAMATION|wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
			dlg.CenterOnParent(wx.BOTH)
			dlg.ShowModal()
		else:
			wx.MessageBox(_("No documentation! \n Please define the documentation of the model %s in the header of its python file.")%name, _("%s Documentation")%name, wx.OK|wx.ICON_INFORMATION)

	###
	def OnInfo(self, event):
		"""
		"""
		wx.MessageBox(_('Libraries Import Manager.\nYou can import, refresh or upgrade libraries using right options.\nDefault libraries directory is %s.')%(DOMAIN_PATH))
