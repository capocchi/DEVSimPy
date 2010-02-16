# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# main.py --- DEVSimPy - The Python DEVS GUI modeling and simulation software 
#                     --------------------------------
#                                Copyright (c) 2009
#                                 Laurent CAPOCCHI
#                               University of Corsica
#                     --------------------------------
# Version 2.0                                      last modified:  15/01/10
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
# depends: NumPy, Scipy, wxPython, wxversion
#
# remarque; attention, la construction de l'arbre des librairies (ou domain) est fait par la classe TreeListLib. 
# De plus, cette construciton necessite la présence obligatoire du fichier __init__.py dans chaque sous domain d'un domaine repertorié dans le repertoire Domain (voir methode recursive GetSubDomain). 
# L'utilisateur doit donc ecrire se fichier en sautant les lignes dans le __all__ = []. Si le fichier n'existe pas le prog le cree. 
# Pour importer une lib: 1/ faire un rep MyLib dans Domain avec les fichier Message.py, DomainBehavior.py et DomaineStrucutre.py
#                                               2/ stocker tout les autre .py dans un sous rep contenant également un fichier __init__ dans lequel son ecris les fichier a importer.
#                                               3/ les fichier .cmd issu de l'environnement peuvent etre stocké nimport ou il seron pris en compte en tant que model couplé.
#                                               4/ les fichier init doivent respecter le format de saus de ligne pour une bonne importation.
#                                               5/ tout fichier .py qui ne se trouve pas dans init n'est ps importé
#                                               6/ lors de l'import des .py (DnD) attention, il faut aussi que les parametres du constructeurs aient des valeurs par defaut.
#                                               7/ le nom des modele atomique dans le G%UI necessite l'omplémentation de la méthode __str__ dans les classes (sinon il note les modèles AM)
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GLOBAL VARIABLES AND FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

__author__  = "Laurent Capocchi <capocchi@univ-corse.fr>"
__date__    = "14 Jan 2010, 13:15 GMT"
__version__ = "2.1"
__docformat__ = "epytext"

import re
import copy
import os
import sys
import time
import gettext
import __builtin__

import webbrowser

try:
	import wxversion
	wxversion.select('2.8')
except ImportError:
	pass

try:
	import wx.lib.filebrowsebutton as filebrowse
	import wx.aui
	import wx.py as py

	sys.stdout.write("Importing wxPython %s on %s platform \n"%(wx.__version__, wx.Platform))
except ImportError:
	sys.stdout.write("Error : wxPython not installed (go to www.wxpython.org) \n")

try:
	from wx.lib.agw import advancedsplash
	AdvancedSplash = advancedsplash.AdvancedSplash
	old=False
except:
	AdvancedSplash = wx.SplashScreen
	old=True

# to send event
from wx.lib.pubsub import Publisher as pub

from Container import *
from ImportLibrary import ImportLibrary
from Reporter import ExceptionHook

from ConnectionThread import LoadFileThread

# Sets the homepath variable to the directory where your application is located (sys.argv[0]).
__builtin__.__dict__['HOME_PATH'] = os.path.abspath(os.path.dirname(sys.argv[0]))
__builtin__.__dict__['ICON_PATH'] = HOME_PATH+os.sep+'icons2'
__builtin__.__dict__['ICON_PATH_20_20'] = ICON_PATH+os.sep+'20x20'
__builtin__.__dict__['NB_OPENED_FILE'] = 5		# number of recent files
__builtin__.__dict__['DOMAIN_DIR'] = 'Domain' 	# DOMAIN_DIR = Name of local lib directory

#-------------------------------------------------------------------
def getIcon():
	bmp = wx.Image(os.path.join('bitmaps','IconeDEVSimPy.png')).ConvertToBitmap()
	bmp.SetMask(wx.Mask(bmp, wx.WHITE))
	icon = wx.EmptyIcon()
	icon.CopyFromBitmap(bmp)
	return icon

#----------------------------------------------------------------------------------------------------
class LibraryTree(wx.TreeCtrl):
	"""	Class of libraries tree of devsimpy model and python files.

		EXT_LIB_FILE = tuple of considered devsimpy file extention.
		EXT_LIB_PYTHON_FLAG = flag to used model from python file instanciation.
	"""

	EXT_LIB_FILE = ('.cmd', '.amd')
	EXT_LIB_PYTHON_FLAG = True

	def __init__(self, *args, **kwargs):
		""" Constructor
		"""

		wx.TreeCtrl.__init__(self, *args, **kwargs)
		
		#Domain Path
		self.domainPath = os.path.join(os.path.dirname(os.getcwd()), DOMAIN_DIR)
		
		# correspondance entre path (cle) et item du Tree (valeur)
		self.ItemDico = {}

		isz = (20,20)
		il = wx.ImageList(isz[0], isz[1])
		self.fldridx = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FOLDER, wx.ART_OTHER, isz))
		self.fldropenidx = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN, wx.ART_OTHER, isz))
		self.fileidx = il.Add(wx.ArtProvider_GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, isz))
		self.atomicidx = il.Add(wx.Image(os.path.join(ICON_PATH_20_20, 'atomic3.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
		self.coupledidx = il.Add(wx.Image(os.path.join(ICON_PATH_20_20, 'coupled3.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
		self.pythonfileidx = il.Add(wx.Image(os.path.join(ICON_PATH_20_20, 'pythonFile.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
		self.SetImageList(il)
		self.il = il
		
		self.root=self.AddRoot(DOMAIN_DIR)
		self.SetItemBold(self.root)

		#### test for InsertNewDomain in tree
		#absdName=opj(self.domainPath+os.sep+'PowerSystem')
		#self.InsertNewDomain(absdName,self.root, self.GetSubDomain(absdName, self.GetDomainList(absdName)).values()[0])
		
		#absdName=opj(self.domainPath+os.sep+'WSN')
		#self.InsertNewDomain(absdName,self.root,self.GetSubDomain(absdName, self.GetDomainList(absdName)).values()[0])
		
		#absdName=os.path.abspath('/home/capocchi/Documents/TOTO')
		#self.InsertNewDomain(absdName,self.root,self.GetSubDomain(absdName, self.GetDomainList(absdName)).values()[0])
		
		self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.OnRightItemClick)
		self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightClick)
		#self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightClick)
		#self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)

		self.Bind(wx.EVT_LEFT_DOWN,self.OnLeftClick)
		#self.Bind(wx.EVT_TREE_ITEM_GETTOOLTIP, self.OnHover)
		
	#def OnContextMenu(self,evt):
		#print "sdd"
		#evt.Skip()

	def Create(self, chargedDomainList = []):
		""" Create the Tree from a list of domain path.
		"""
		
		assert self.root != None, _("Missing root")
		
		for absdName in chargedDomainList:
			self.InsertNewDomain(absdName, self.root, self.GetSubDomain(absdName, self.GetDomainList(absdName)).values()[0])

		self.UnselectAll()
		self.SortChildren(self.root)
	
	def OnHover(self, evt):
		"""
		"""
		pass
		## last child
		#if not self.ItemHasChildren(evt.GetItem()):
			## print info (todo: dialog with ? icon ...)
			#time.sleep(2.0)
		
	def OnLeftClick(self, evt):
		"""
		"""

		self.UnselectAll()
		mainW = self.GetTopLevelParent()
		mainW.statusbar.SetStatusText('', 0)
		mainW.statusbar.SetStatusText('', 1)
		self.SetFocus()
		evt.Skip()

	###
	def OnRightClick(self, evt):
		"""
		"""

		#print self.SelectItem(evt.GetItem(),True) 
		# si pas d'item selectionnner, le evt.Skip à la fin propage l'evenement vers OnRightItemClick			
		if self.GetSelections() == []:
			mainW = self.GetTopLevelParent()

			menu = wx.Menu()
			add = wx.MenuItem(menu, wx.NewId(), _('Import'), _('Import library'))
			refresh = wx.MenuItem(menu, wx.NewId(), _('Refresh'), _('Refresh library'))
			info = wx.MenuItem(menu, wx.NewId(), _('Help'), _('Library description'))

			add.SetBitmap(wx.Image(os.path.join(ICON_PATH_20_20,'dbimport.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())			
			refresh.SetBitmap(wx.Image(os.path.join(ICON_PATH_20_20,'db_refresh.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
			info.SetBitmap(wx.Image(os.path.join(ICON_PATH_20_20,'dbinfo.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())

			menu.AppendItem(add)
			menu.AppendItem(refresh)
			menu.AppendSeparator()
			menu.AppendItem(info)

			wx.EVT_MENU(menu, add.GetId(), mainW.OnImport)
			wx.EVT_MENU(menu, info.GetId(), self.OnInfo)
			wx.EVT_MENU(menu, refresh.GetId(), self.UpdateAll)

			self.PopupMenu(menu,evt.GetPosition())
			menu.Destroy()

		evt.Skip()

	###
	def OnRightItemClick(self, evt):
		"""
		"""
		
		self.item_selected=evt.GetItem()
		menu = wx.Menu()
		delete=wx.MenuItem(menu, wx.NewId(), _('Delete'), _('Delete selected library'))
		delete.SetBitmap(wx.Image(os.path.join(ICON_PATH_20_20,'db-.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
		menu.AppendItem(delete)
		# attention à le mettre avant le popUpMenu
		wx.EVT_MENU(menu, delete.GetId(), self.OnDelete)
		self.PopupMenu(menu,evt.GetPoint())
		menu.Destroy()
		
		evt.Skip()

	def OnDelete(self, evt):
		""" Delete the item from Tree
		"""

		self.RemoveItem(self.item_selected)
		
	###     
	def GetDomainList(self, dName):
		""" Get the list of sub-directory of dName directory
		"""

		return [f for f in os.listdir(dName) if os.path.isdir(os.path.join(dName, f))] if os.path.isdir(dName) else []

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
        
	###             
	def GetModelList(self, dName):
		""" Get the list of files from dName directory.
		"""

		#list of py file from __init__.py
		if LibraryTree.EXT_LIB_PYTHON_FLAG:
			
			try:
				init = open(dName+os.sep+'__init__.py','r')
				py_file_list = map(lambda s: s.replace('\n','').replace('\t','').replace(',','').replace('"',""), init.readlines()[1:-1])
				init.close()
			except Exception, info:
				py_file_list = []
				sys.stderr.write(_("%s not imported : %s \n"%(dName,info)))
		else:
			py_file_list = []
	
		# list of amd and cmd files
		devsimpy_file_list = [f for f in os.listdir(dName) if os.path.isfile(os.path.join(dName, f)) and (f[:2] != '__') and (f.endswith(LibraryTree.EXT_LIB_FILE))]

		return py_file_list + devsimpy_file_list

	###
	def InsertNewDomain(self, dName, parent, L = []):
		""" Recurcive function that insert new Domain on library panel
		"""
	
		# au depard seulement pour le parent de plus haut niveau (comme PowerSystem)
		if dName not in self.ItemDico.keys():
			id = self.InsertItemBefore(parent, 0, os.path.basename(dName))
			self.SetItemImage(id, self.fldridx, wx.TreeItemIcon_Normal)
			self.SetItemImage(id, self.fldropenidx, wx.TreeItemIcon_Expanded)
			self.SetItemBold(id)
			self.ItemDico.update({dName:id})
			self.SetPyData(id,dName)
		# fin de la recursion
		if L==[]:
			return
		else:
			item = L.pop(0)
			assert not isinstance(item,unicode), _("Warning unicode item !")
			#element à faire remonter dans la liste
			D = {}
			# si le fils est un modèle construit dans DEVSimPy
			if isinstance(item, str):
				# le parent est récupére dans le Dico
				parent = self.ItemDico[dName]
				assert parent != None
				# path correspondant au parent
				parentPath = self.GetPyData(parent)
				
				# remplacement des espaces
				item=item.strip() #replace(' ','')
		
				#suppression de l'extention su .cmd (model atomic lue a partir de __init__ donc pas d'extention)
				if item.endswith('.cmd'):
					#insertion dans le tree
					id = self.InsertItemBefore(parent, 0, os.path.splitext(item)[0], self.coupledidx,self.coupledidx)
					self.SetPyData(id, os.path.join(parentPath,item))
				elif item.endswith('.amd'):
					#insertion dans le tree
					id = self.InsertItemBefore(parent, 0, os.path.splitext(item)[0], self.atomicidx,self.atomicidx)
					self.SetPyData(id, os.path.join(parentPath,item))
				else:
					id = self.InsertItemBefore(parent, 0, item, self.pythonfileidx, self.pythonfileidx)
					self.SetPyData(id, os.path.join(parentPath, item+'.py'))

				# insertion des donnees dans l'item et gestion du ItemDico
				self.ItemDico.update({os.path.join(parentPath,item,):id})
			# si le fils est un sous repertoire contenant au moins un fichier (all dans __init__.py different de [])
			elif isinstance(item, dict) and item.values() != [[]]:
				# nom a inserer dans l'arbe
				dName=os.path.basename(item.keys()[0])
				#nouveau parent			
				parent=self.ItemDico[item.keys()[0].replace(os.sep+dName,'')]
			
				assert(parent!=None)
				#insertion de fName sous parent
				id= self.InsertItemBefore(parent, 0, dName)
				self.SetItemImage(id, self.fldridx, wx.TreeItemIcon_Normal)
				self.SetItemImage(id, self.fldropenidx, wx.TreeItemIcon_Expanded)
				#stockage du parent avec pour cle le chemin complet avec extention (pour l'import du moule dans le Dnd)
				self.ItemDico.update({item.keys()[0]:id})
				self.SetPyData(id,item.keys()[0]+'.py')
				# pour les fils du sous domain
				for elem in item.values()[0]:
					# si elem simple (modèle couple ou atomic)
					if isinstance(elem,str):
						#remplacement des espaces
						elem = elem.strip() #replace(' ','')
						# parent provisoir
						p=self.ItemDico[item.keys()[0]]
						assert(p!=None)
						# si model atomic
						if elem.endswith('.cmd'):
							id=self.InsertItemBefore(p, 0, os.path.splitext(elem)[0], self.coupledidx, self.coupledidx)
							self.SetPyData(id,os.path.join(item.keys()[0],elem))
						elif elem.endswith('.amd'):
							id=self.InsertItemBefore(p, 0, os.path.splitext(elem)[0], self.atomicidx, self.atomicidx)
							self.SetPyData(id,os.path.join(item.keys()[0],elem))
						else:
							id = self.InsertItemBefore(p, 0, elem, self.pythonfileidx, self.pythonfileidx)
							self.SetPyData(id, os.path.join(item.keys()[0],elem+'.py'))

						self.ItemDico.update({os.path.join(item.keys()[0], os.path.splitext(elem)[0]):id})
						#self.SetPyData(id,os.path.join(item.keys()[0],elem))
					else:
						# pour faire remonter l'info dans la liste
						D=elem
				# mise a jour avec le nom complet
				dName=item.keys()[0]
			
			# for spash screen
			pub.sendMessage('object.added', 'Making %s domain...'%item)

			# gestion de la recursion
			if D != {}:
				return self.InsertNewDomain(dName,parent, L+[D])
			else:
				return self.InsertNewDomain(dName,parent, L)
                        
    ###     
	def GetSubDomain(self, dName, domainSubList = []):
		""" Get the dico composed by all of the sub domain of dName (like{'../Domain/PowerSystem': ['PSDomainStructure', 'PSDomainBehavior', 'Object', 'PSSDB', {'../Domain/PowerSystem/Rt': []}, {'../Domain/PowerSystem/PowerMachine': ['toto.cmd', 'Integrator.cmd', 'titi.cmd', 'Mymodel.cmd', {'../Domain/PowerSystem/PowerMachine/TOTO': []}]}, {'../Domain/PowerSystem/Sources': ['StepGen', 'SinGen', 'CosGen', 'RampGen', 'PWMGen', 'PulseGen', 'TriphaseGen', 'ConstGen']}, {'../Domain/PowerSystem/Sinks': ['To_Disk', 'QuickScope']}, {'../Domain/PowerSystem/MyLib': ['', 'model.cmd']}, {'../Domain/PowerSystem/Hybrid': []}, {'../Domain/PowerSystem/Continuous': ['WSum', 'Integrator', 'Gain', 'Gain2', 'NLFunction']}]}
	)
		"""

		if domainSubList == []:
			# attention il faut que le fichier __init__.py respecte une certain ecriture
			return {dName:self.GetModelList(dName)}
		else:
			# on comptabilise les fichiers si il y en a dans le rep courant (la recusion s'occupe des sous domaines)
			D = {dName: self.GetModelList(dName)}
			# on lance la recursion sur les repertoires fils
			
			for d in domainSubList:
				D[dName].append(self.GetSubDomain(dName+os.sep+d,self.GetDomainList(dName+os.sep+d)))
			return D

	###
	def GetChildRoot(self):
		""" Return the list compsed by the childs of the Root
		"""
		return map(lambda s: str(self.GetItemText(s)), self.GetItemChildren(self.root))

	###
	def IsChildRoot(self, dName):
		"""
		"""
		# si dName est dans la liste des noms des fils du root (comme Basic)
		return (dName in self.GetChildRoot())

	###
	def UpdateDomain(self, path):
		""" Update the Tree Library with new path of the corresponding domain
		""" 
		
		assert self.IsChildRoot(os.path.basename(path)), _("You trying to update a library that is not present in Domain")
		
		dName = path
			
		#supression du domain de l'arbre
		item=self.ItemDico[dName]
		self.RemoveItem(item)

		#insertion du nouveau domain
		self.InsertNewDomain(dName,self.root, self.GetSubDomain(dName, self.GetDomainList(dName)).values()[0])
                
	def UpdateAll(self, event):
		"""
		"""
		for item in self.GetItemChildren(self.GetRootItem()):
			self.UpdateDomain(self.GetPyData(item))
		
		self.SortChildren(self.root)

	def RemoveItem(self, item):
		""" Remove item from Tree and also the corresponding elements of ItemDico
		"""
		
		#suppression des reference dans le ItemDico
		for key in copy.copy(self.ItemDico):
			if os.path.basename(self.GetPyData(item)) in key.split(os.sep):
				del self.ItemDico[key]
		
		self.Delete(item)

	def OnInfo(self, event):
		"""
		"""
		sys.stdout.write(_("This option has not been implemented yet.\n"))

#-----------------------------------------------------------------------
class SearchLib(wx.SearchCtrl):
	"""
	"""
	def __init__(self, *args, **kwargs):
		"""
		"""
		wx.SearchCtrl.__init__(self, *args, **kwargs)

		self.treeChildren = []
		self.treeCopy = None
		self.ShowCancelButton( True)
		self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancel)
		self.Bind(wx.EVT_TEXT, self.OnSearch)

	def OnCancel(self, evt):
		"""
		"""
		self.Clear()

	def OnSearch(self, evt):
		"""
		"""
		wx.GetApp().frame.OnSearch(evt)

#-------------------------------------------------------------------
class LeftNotebook(wx.Notebook):
	"""
	"""

	def __init__(self, *args, **kwargs):
		"""
		Notebook class that allows overriding and adding methods for the left splitter of DEVSimPy

		@param parent: parent windows
		@param id: id
		@param pos: windows position
		@param size: windows size
		@param style: windows style
		@param name: windows name
		"""
		
		wx.Notebook.__init__(self, *args, **kwargs)
		
		# --------------------  Define drop source ---------------
		TextDrop.SOURCE = self

		## -------------------- Add pages --------------
		
		self.libPanel = wx.Panel(self, wx.ID_ANY)
		self.propPanel = wx.Panel(self, wx.ID_ANY)
		
		# Creation de l'arbre des librairies
		self.tree = LibraryTree(self.libPanel, wx.ID_ANY, wx.DefaultPosition, (-1,-1), style=wx.TR_DEFAULT_STYLE|wx.TR_HIDE_ROOT|wx.TR_MULTIPLE|wx.TR_LINES_AT_ROOT|wx.TR_HAS_BUTTONS|wx.SUNKEN_BORDER) 
		
		mainW = self.GetTopLevelParent()
		# lecture de ChargedDomainList dans .devsimpy
		if mainW.cfg.Read('ChargedDomainList'):
			chargedDomainList = eval(mainW.cfg.Read('ChargedDomainList'))
		else:
			chargedDomainList = [os.path.join(self.tree.domainPath, 'Basic')]
			
		self.tree.Create(chargedDomainList)
		
		#Creation de l'arbre de recherche hide au depart (voir __do_layout)
		self.searchTree = LibraryTree(self.libPanel, wx.ID_ANY,wx.DefaultPosition, (-1,-1), style=wx.TR_DEFAULT_STYLE|wx.TR_HIDE_ROOT|wx.TR_MULTIPLE|wx.TR_LINES_AT_ROOT|wx.TR_HAS_BUTTONS|wx.SUNKEN_BORDER)
		
		# creation de l'option de recherche dans tree
		self.search=SearchLib(self.libPanel, size=(200,-1), style = wx.TE_PROCESS_ENTER)
	
		self.__set_properties()
		self.__do_layout()

		self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.__PageChanged)
		
	def __set_properties(self):
		"""
		"""
		imgList = wx.ImageList(20, 20)
		for img in [os.path.join(ICON_PATH_20_20,'db.png'), os.path.join(ICON_PATH_20_20,'properties.png'), os.path.join(ICON_PATH_20_20,'simulation.png')]:
			bmp = wx.Image(img, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
			imgList.Add(bmp)
		self.AssignImageList(imgList)
		
		self.libPanel.SetBackgroundColour(wx.WHITE)
		self.propPanel.SetBackgroundColour(wx.WHITE)
		self.searchTree.Hide()

	def __do_layout(self):
		"""
		"""
		libSizer = wx.BoxSizer(wx.VERTICAL)
		libSizer.Add(self.tree, 1 ,wx.EXPAND)
		libSizer.Add(self.searchTree, 1 ,wx.EXPAND)
		libSizer.Add(self.search, 0 ,wx.BOTTOM|wx.EXPAND)
		
		propSizer = wx.BoxSizer(wx.VERTICAL)
		propSizer.Add(self.defaultPropertiesPage(), 0, wx.ALL, 10)
		
		self.AddPage(self.libPanel, _("Library"), imageId=0)
		self.AddPage(self.propPanel, _("Properties"), imageId=1)

		self.libPanel.SetSizer(libSizer)
		self.libPanel.SetAutoLayout(True)

		self.propPanel.SetSizer(propSizer)
		self.propPanel.Layout()
	
	def __PageChanged(self, evt):
		"""
		"""
		if evt.GetSelection() == 1:
			pass
		evt.Skip()

	def defaultPropertiesPage(self):
		"""
		"""
		propContent = wx.StaticText(self.propPanel, -1, _("Properties panel"))
		propContent.SetFont(wx.Font(9, wx.SWISS, wx.NORMAL, wx.BOLD))
		propContent.SetSize(propContent.GetBestSize())
		return propContent

	def UpdatePropertiesPage(self, panel = None, model = None, parent = None):
		"""	Update the propPanel with teh new panel param of the model
		"""
		sizer = self.propPanel.GetSizer()
		sizer.DeleteWindows()
		sizer.Add(panel,1, wx.EXPAND|wx.ALL)
		sizer.Layout()

#-------------------------------------------------------------------
class DiagramNotebook(wx.Notebook):
	"""
	"""

	def __init__(self, *args, **kwargs):
		"""
		Notebook class that allows overriding and adding methods.

		@param parent: parent windows
		@param id: id
		@param pos: windows position
		@param size: windows size
		@param style: windows style
		@param name: windows name
		"""

		# for spash screen
		pub.sendMessage('object.added', 'Loading notebook diagram...')
		
		wx.Notebook.__init__(self, *args, **kwargs)
		
		# local copy
		self.parent = args[0]
		self.pages = []			# keeps track of pages

		#icon under tab
		imgList = wx.ImageList(20, 20)
		for img in [os.path.join(ICON_PATH_20_20,'network.png')]:
			bmp = wx.Image(img, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
			imgList.Add(bmp)
		self.AssignImageList(imgList)

		self.__CreateMenu()

		self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.__PageChanged)
		self.Bind(wx.EVT_RIGHT_DOWN, self.__ShowMenu)
		
	def AddEditPage(self, title, defaultDiagram = None):
		"""
		Adds a new page for editing to the notebook and keeps track of it.
		
		@type title: string
		@param title: Title for a new page
		"""
		
		newPage=ShapeCanvas(self, wx.NewId(), name=title)
		if defaultDiagram is None:
			d=ContainerBlock()
		else:
			d=defaultDiagram
		d.AddCoupledModel(Master())
		newPage.SetDiagram(d)
		newPage.SetBackgroundColour(wx.WHITE)
		
		self.pages.append(newPage)
		self.AddPage(newPage, title, imageId=0)
		self.SetSelection(self.GetPageCount()-1)
		
	def GetPageByName(self, name = ''):
		"""
		"""
		for i in range(len(self.pages)):
			if name == self.GetPageText(i):
				return self.GetPage(i)
		return None

	def __CreateMenu(self):
		"""	Creates the menu for a right click.
		"""
		self.menu = wx.Menu()
		
		close=wx.MenuItem(self.menu, wx.NewId(), _('Close'), _('Close Diagram'))
		detach=wx.MenuItem(self.menu, wx.NewId(), _('Detach'), _('Detach tab to window'))
		close.SetBitmap(wx.Image(os.path.join(ICON_PATH_20_20,'close.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
		detach.SetBitmap(wx.Image(os.path.join(ICON_PATH_20_20,'detach.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
		
		Detach_menu=self.menu.AppendItem(detach)
		self.menu.AppendSeparator()
		Close_menu=self.menu.AppendItem(close)
		
		self.Bind(wx.EVT_MENU, self.OnClosePage, Close_menu)
		self.Bind(wx.EVT_MENU, self.OnDetachPage, Detach_menu)
	
	def __PageChanged(self, evt):
		"""
		"""

		try:
			canvas = self.GetPage(self.GetSelection())
			canvas.deselect()
			canvas.Refresh()
		except ValueError:
			pass
		evt.Skip()

	def __ShowMenu(self, evt):
		"""	Callback for the right click on a tab. Displays the menu.
		
			@type   evt: event
			@param  evt: Event Objet, None by default
		"""
		
		self.PopupMenu(self.menu, (evt.GetX(),evt.GetY()))

	def OnClearPage(self, evt): 
		""" Clear page.

			@type evt: event
			@param  evt: Event Objet, None by default
		"""
		mainW=self.parent.GetTopLevelParent()
		canvas = self.GetPage(self.GetSelection())
		diagram=canvas.diagram

		diagram.DeleteAllShapes()
		diagram.modified=True

		canvas.deselect()
		canvas.Refresh()
		
	def OnClosePage(self, evt):
		""" Close current page.
		
			@type evt: event
			@param  evt: Event Objet, None by default
		"""
		mainW=self.parent.GetTopLevelParent()
		canvas = self.GetPage(self.GetSelection())
		diagram=canvas.diagram
		
		if diagram.modify:
			dlg = wx.MessageDialog(self, _('Save changes to the current diagram ?'), '', wx.YES_NO | wx.YES_DEFAULT | wx.CANCEL |wx.ICON_QUESTION)
			val = dlg.ShowModal()
			if val == wx.ID_YES:
				mainW.OnSaveFile(evt)
			elif val == wx.ID_CANCEL:
				dlg.Destroy()
			else:
				self.DeleteBuiltinConstants()

				if (self.GetPageCount() != 1):
					id = self.GetSelection()
					self.pages.remove(self.GetPage(id))
					if not self.DeletePage(id):
						sys.stdout.write(_(" %d not deleted ! \n"%id))
				else:
					mainW.OnCloseWindow(evt)
				##rafrechissement du dernier canvas recupere par defaut
				#canvas = self.GetPage(self.GetSelection())
				#canvas.deselect()
				#canvas.Refresh()
		else:
			self.DeleteBuiltinConstants()

			if (self.GetPageCount() != 1):
				id = self.GetSelection()
				self.pages.remove(self.GetPage(id))
				if not self.DeletePage(id):
					sys.stdout.write(_("%d not deleted ! \n"%id))
			else:
				mainW.OnCloseWindow(evt)
			
			##rafrechissement du dernier canvas recupere par defaut
			#canvas = self.GetPage(self.GetSelection())
			#canvas.deselect()
			#canvas.Refresh()
	      
		# effacement du notebook "property"
		nb1 = mainW.nb1
		activePage = nb1.GetSelection()
		parent = mainW
		#si la page active est celle de "properties" alors la met a jour et on reste dessus
		if activePage == 1:
			newContent = nb1.defaultPropertiesPage()
			nb1.UpdatePropertiesPage(newContent, self, parent)

	def OnDetachPage(self, evt=None):
		""" 
		Detach the notebook page on frame.
		
		@type evt: event
		@param  evt: Event Objet, None by default
		"""

		mainW = self.parent.GetTopLevelParent()
		canvas = self.GetPage(self.GetSelection())
		title = self.GetPageText(self.GetSelection())

		frame = DetachedFrame(mainW,wx.ID_ANY,title,canvas.GetDiagram())
		frame.SetIcon(mainW.icon)
		frame.SetFocus()
		frame.Show()

	def DeleteBuiltinConstants(self):
		""" Delete builtin constants for the diagram.
		"""
		try:
			name = self.GetPageText(self.GetSelection())
			del __builtin__.__dict__[str(os.path.splitext(name)[0])]
		except Exception ,info:
			pass
			#print "Constants builtin not delete for %s : %s"%(name, info)

# -------------------------------------------------------------------
class MainApplication(wx.Frame):
	""" DEVSimPy main application.
	"""

	def __init__(self, parent, id, title):
		""" Constructor.
		"""
		
		## Create Config file -------------------------------------------------------
		self.cfg = self.GetConfig()
		self.SetConfig(self.cfg)

		## Set i18n locales --------------------------------------------------------
		self.Seti18n()
		
		wx.Frame.__init__(self, parent, wx.ID_ANY, title, size = (900, 700), style = wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE)

		self.window = None
		self.otherWin = None
		self.replace = False
		self.stdioWin = None
		
		# icon setting
		self.icon = getIcon()
		self.SetIcon(self.icon)

		self.splitter1 = wx.SplitterWindow(self, wx.ID_ANY, name='splitter', style=wx.NO_3D|wx.SP_3D|wx.SP_LIVE_UPDATE|wx.SP_BORDER)
		self.splitter1.SetMinimumPaneSize(220)
		self.splitter2 = wx.SplitterWindow(self.splitter1, wx.ID_ANY, name='splitter', style=wx.NO_3D|wx.SP_3D|wx.SP_LIVE_UPDATE|wx.SP_BORDER)
		self.splitter2.SetMinimumPaneSize(150)

		# Prevent TreeCtrl from displaying all items after destruction when True
		self.dying = False

		if 0:
			# This is another way to set Accelerators, in addition to
			# using the '\t<key>' syntax in the menu items.
			aTable = wx.AcceleratorTable([(wx.ACCEL_ALT,  ord('X'), exitID), (wx.ACCEL_CTRL, ord('H'), helpID),(wx.ACCEL_CTRL, ord('F'), findID),(wx.ACCEL_NORMAL, WXK_F3, findnextID)])
			self.SetAcceleratorTable(aTable)
		
		# NoteBook for splitter1
		# for spash screen
		pub.sendMessage('object.added', 'Loading tree library...')
		pub.sendMessage('object.added', 'Loading search tree library...')
		
		self.nb1 = LeftNotebook(self.splitter1, wx.ID_ANY, style = wx.CLIP_CHILDREN)		
		self.tree = self.nb1.tree
		self.searchTree = self.nb1.searchTree
		self.search = self.nb1.search

		#------------------------------------------------------------------------------------------
		# Create a Notebook 2
		self.nb2 = DiagramNotebook(self.splitter2, wx.ID_ANY, style = wx.CLIP_CHILDREN)
		self.nb2.AddEditPage(_("Diagram %d"%ShapeCanvas.ID))
		
		# Simulation panel
		self.panel3 = wx.Panel(self.nb1, wx.ID_ANY, style = wx.WANTS_CHARS)
		self.panel3.SetBackgroundColour(wx.NullColour)
		self.panel3.Hide()
	
		#status bar avant simulation :-)
		self.MakeStatusBar()

		# Shell panel
		self.panel4 = wx.Panel(self.splitter2, wx.ID_ANY, style=wx.WANTS_CHARS)
		sizer4 = wx.BoxSizer(wx.VERTICAL)
		sizer4.Add(py.shell.Shell(self.panel4, introText=_("Welcome to DEVSimPy: The GUI Python DEVS Simulator")), 1, wx.EXPAND)
		self.panel4.SetSizer(sizer4)
		self.panel4.SetAutoLayout(True)

		# add the windows to the splitter and split it.
		self.splitter1.SplitVertically(self.nb1, self.splitter2, 350)
		self.splitter2.SplitHorizontally(self.nb2, self.panel4, 500)
		# au départ invisible (voir OnShowShell)
		self.splitter2.Unsplit()

		self.MakeMenu()	
		self.MakeToolBar()

		def EmptyHandler(evt): pass
		
		wx.EVT_ERASE_BACKGROUND(self.splitter1, EmptyHandler)
		wx.EVT_ERASE_BACKGROUND(self.splitter2, EmptyHandler)
		wx.EVT_TREE_BEGIN_DRAG(self, self.tree.GetId(), self.OnDragInit)
		wx.EVT_TREE_BEGIN_DRAG(self, self.searchTree.GetId(), self.OnDragInit)
		wx.EVT_IDLE(self, self.OnIdle)
		wx.EVT_CLOSE(self, self.OnCloseWindow)
		
		self.Centre(wx.BOTH)
		self.Show()

	def GetVersion(self):
		return __version__

	def GetUserConfigDir(self):
		""" Return the standard location on this platform for application data.
		"""
		sp = wx.StandardPaths.Get()
		return sp.GetUserConfigDir()

	def GetConfig(self):
		""" Reads the config file for the application if it exists and return a configfile object for use later.
		"""
		return wx.FileConfig(localFilename = os.path.join(self.GetUserConfigDir(),'.devsimpy'))
	
	def WriteConfigFile(self, cfg):
		""" Write config file
		"""

		# for spash screen
		pub.sendMessage('object.added', 'Writing .devsimpy settings file...')

		sys.stdout.write("Writing .devsimpy settings file...")

		self.exportPathsList = []					# export path list
		self.openFileList = ['']*NB_OPENED_FILE		#number of last opened files
		self.language = 'default'						# default language

		# verison of the main (fo compatibility of DEVSimPy)
		cfg.Write('version', str(__version__))
		# list des chemins des librairies à importer
		cfg.Write('exportPathsList', str([]))
		# list des 5 derniers fichier ouvert
		cfg.Write('openFileList', str(eval("self.openFileList")))
		cfg.Write('language', "'%s'"%str(eval("self.language")))
		sys.stdout.write("OK \n")

	def SetConfig(self, cfg):
		""" Set all config entry like language, external importpath, recent files...
		"""

		self.cfg = cfg

		# if .devsimpy config file already exist, load it
		if self.cfg.Exists('version'):

			# rewrite old configuration file
			rewrite = float(self.cfg.Read("version")) < float(self.GetVersion())

			if not rewrite:

				# for spash screen
				pub.sendMessage('object.added', 'Loading .devsimpy settings file...')
				
				sys.stdout.write("Load .devsimpy %s settings file... "%self.GetVersion())
				# load external import path
				self.exportPathsList = eval(self.cfg.Read("exportPathsList"))
				# load recent files list
				self.openFileList = eval(self.cfg.Read("openFileList"))
				# update chargedDomainList
				# if a filename has been deleted, it is deleted from the chargedDomainList
				chargedDomainList = [ abs_filename for abs_filename in eval(self.cfg.Read('ChargedDomainList')) if os.path.exists(os.path.join(abs_filename,'__init__.py')) ]
				self.cfg.DeleteEntry('ChargedDomainList')
				self.cfg.Write('ChargedDomainList', str(eval('chargedDomainList')))
				# load language 
				self.language = eval(self.cfg.Read("language"))
				sys.stdout.write("OK \n")

			else:
				self.WriteConfigFile(self.cfg)

		# create a new defaut .devsimpy config file
		else:
			self.WriteConfigFile(self.cfg)
		
	
	def Seti18n(self):
		""" Set local setting.
		"""

		# for spash screen
		pub.sendMessage('object.added', 'Loading locale configuration...')

		localedir = os.path.join(os.getcwd(), "locale")
		langid = wx.LANGUAGE_DEFAULT    # use OS default; or use LANGUAGE_FRENCH, etc.
		domain = "DEVSimPy"             # the translation file is messages.mo

		# Set locale for wxWidgets
		mylocale = wx.Locale(langid)
		mylocale.AddCatalogLookupPathPrefix(localedir)
		mylocale.AddCatalog(domain)
		
		# language config from .devsimpy file
		if self.language == 'en':
			translation = gettext.translation(domain, localedir, languages=['en']) # English
		elif self.language =='fr':
			translation = gettext.translation(domain, localedir, languages=['fr']) # French
		else:
			#installing os language by default
			translation = gettext.translation(domain, localedir, [mylocale.GetCanonicalName()], fallback = True)
		
		translation.install(unicode = True)


	def MakeStatusBar(self):
		""" Make status bar.
		"""

		# for spash screen
		pub.sendMessage('object.added', 'Making status bar...')
	
		self.statusbar = self.CreateStatusBar(1, wx.ST_SIZEGRIP)
		self.statusbar.SetFieldsCount(3)
		self.statusbar.SetStatusWidths([-5, -2, -1])

	def MakeMenu(self):
		""" Make main menu.
		"""

		# for spash screen
		pub.sendMessage('object.added', 'Making Menu ...')
		
		filemenu= wx.Menu()
		newModel=wx.MenuItem(filemenu, wx.NewId(), _('&New\tCtrl+N'),_('Creates a new diagram'))
		openModel=wx.MenuItem(filemenu, wx.NewId(), _('&Open\tCtrl+O'),_('Open an existing diagram'))
		#openRecentModel=wx.MenuItem(filemenu, wx.NewId(), '&Open Recent','Open recent diagram')
		saveModel=wx.MenuItem(filemenu, wx.NewId(), _('&Save\tCtrl+S'), _('Save the current diagram'))
		saveAsModel=wx.MenuItem(filemenu, wx.NewId(), _('&SaveAs'),_('Save the diagram with an another name'))
		#importModel=wx.MenuItem(filemenu, wx.NewId(), _('&Import\tCtrl+I'),_('Import new library'))
		#exportModel=wx.MenuItem(filemenu, wx.NewId(), _('&Export\tCtrl+E'),_('Export the diagram into a coupled model'))
		exitModel=wx.MenuItem(filemenu, wx.NewId(), _('&Quit\tCtrl+Q'),_('Quit the DEVSimPy application'))
		
		newModel.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'new.png')))
		openModel.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'open.png')))
		saveModel.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'save.png')))
		saveAsModel.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'save_as.png')))
		#importModel.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'import.png')))
		#exportModel.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'export.png')))
		exitModel.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'exit.png')))
				
		openRecentMenu = wx.Menu()

		# affichage du menu des dernier fichier consulté avec gestion des fichier qui n'existe plus 
		for path in filter(lambda p:p!='',self.openFileList):
			if not os.path.exists(path):
				index=self.openFileList.index(path)
				del self.openFileList[index]
				self.openFileList.insert(-1,'')
				self.cfg.Write("openFileList", str(eval("self.openFileList")))
			else:
				open_recent_menu_item=wx.MenuItem(openRecentMenu, wx.NewId(), path)
				openRecentMenu.AppendItem(open_recent_menu_item)
				self.Bind(wx.EVT_MENU, self.OnOpenRecentFile, id=open_recent_menu_item.GetId())

		#filemenu.AppendItem(newModel)
		filemenu.AppendItem(openModel)
		filemenu.AppendMenu(wx.NewId(),_("Recent files"),openRecentMenu)

		filemenu.AppendSeparator()
		filemenu.AppendItem(saveModel)
		filemenu.AppendItem(saveAsModel)
		
		#filemenu.AppendSeparator()
		#filemenu.AppendItem(importModel)

		#filemenu.AppendSeparator()
		#filemenu.AppendItem(exportModel)

		filemenu.AppendSeparator()
		filemenu.AppendItem(exitModel)
		
		showmenu=wx.Menu()
		id_shell=wx.NewId()
		id_sim = wx.NewId()
		id_toolBar = wx.NewId()
		showmenu.Append(id_shell, _('Console'), _("Show Python Shell console"),wx.ITEM_CHECK)
		showmenu.Append(id_sim, _('Simulation'), _("Show simulation tab"),wx.ITEM_CHECK)
		showmenu.Append(id_toolBar, _('Tools Bar'), _("Show icons tools bar"),wx.ITEM_CHECK)
		showmenu.Check(id_shell,False)
		showmenu.Check(id_sim,False)
		showmenu.Check(id_toolBar,True)

		diagrammenu=wx.Menu()
		newDiagram=wx.MenuItem(diagrammenu, wx.ID_ANY, _('New'), _("Create new diagram in tab"))
		detachDiagram = wx.MenuItem(diagrammenu, wx.ID_ANY, _('Detach'), _("Detach the tab to a frame window"))
		zoomIn=wx.MenuItem(diagrammenu, wx.ID_ANY, _('Zoom'), _("Zoom in"))
		zoomOut=wx.MenuItem(diagrammenu, wx.ID_ANY, _('UnZoom'), _("Zoom out"))
		annuleZoom=wx.MenuItem(diagrammenu, wx.ID_ANY, _('AnnuleZoom'), _("Normal view"))
		simulationDiagram=wx.MenuItem(diagrammenu, wx.ID_ANY, _('&Simulate\tF5'), _("Perform the simulation"))
		constantsDiagram=wx.MenuItem(diagrammenu, wx.ID_ANY, _('Add Constants'), _("Loading constants parameters"))
		priorityDiagram=wx.MenuItem(diagrammenu, wx.ID_ANY, _('Priority'), _("Priority for select function"))
		clearDiagram = wx.MenuItem(diagrammenu, wx.ID_ANY, _('Clear'), _("Remove all components in diagram"))
		closeDiagram = wx.MenuItem(diagrammenu, wx.ID_ANY, _('&Close\tCtrl+D'), _("Close the tab"))
		
		detachDiagram.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH_20_20,'detach.png')))
		zoomIn.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'zoom+.png')))
		zoomOut.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'zoom-.png')))
		annuleZoom.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'no_zoom.png')))
		simulationDiagram.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'simulation.png')))
		constantsDiagram.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH_20_20,'properties.png')))
		priorityDiagram.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH_20_20,'priority.png')))
		clearDiagram.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'delete.png')))
		closeDiagram.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'close.png')))

		diagrammenu.AppendItem(newModel)
		diagrammenu.AppendItem(detachDiagram)
		diagrammenu.AppendSeparator()
		diagrammenu.AppendItem(zoomIn)
		diagrammenu.AppendItem(zoomOut)
		diagrammenu.AppendItem(annuleZoom)
		diagrammenu.AppendSeparator()
		diagrammenu.AppendItem(simulationDiagram)
		diagrammenu.AppendItem(constantsDiagram)
		diagrammenu.AppendItem(priorityDiagram)
		diagrammenu.AppendSeparator()
		diagrammenu.AppendItem(clearDiagram)
		diagrammenu.AppendSeparator()
		diagrammenu.AppendItem(closeDiagram)

		settingsmenu=wx.Menu()
		moreitem=wx.MenuItem(settingsmenu, wx.ID_ANY, _('Preferences...'), _("Advanced setting options"))
		languagesSubmenu=wx.Menu()
		fritem = wx.MenuItem(languagesSubmenu, wx.ID_ANY, _('French'), _("French interface"))
		enitem = wx.MenuItem(languagesSubmenu, wx.ID_ANY, _('English'), _("English interface"))
		languagesSubmenu.AppendItem(fritem)
		languagesSubmenu.AppendItem(enitem)
		if self.language == 'fr':
			fritem.Enable(False)
		if self.language == 'en':
			enitem.Enable(False)
		settingsmenu.AppendMenu(wx.NewId(),_('Languages'),languagesSubmenu)
		settingsmenu.AppendItem(moreitem)

		helpmenu=wx.Menu()
		helpModel = wx.MenuItem(helpmenu, wx.ID_ANY, _('&DEVSimPy Help\tF1'), _("Help for DEVSimPy user"))
		apiModel = wx.MenuItem(helpmenu, wx.ID_ANY, _('&DEVSimPy API\tF2'), _("API for DEVSimPy user"))
		contactModel = wx.MenuItem(helpmenu, wx.ID_ANY, _('Contact the Author...'), _("Contact the author by mail"))
		aboutModel = wx.MenuItem(helpmenu, wx.ID_ANY, _('About DEVSimPy...'), _("About DEVSimPy"))

		helpModel.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'search.png')))
		apiModel.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'api.png')))

		contactModel.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'mail.png')))
		aboutModel.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'info.png')))

		helpmenu.AppendItem(helpModel)
		helpmenu.AppendItem(apiModel)
		helpmenu.AppendSeparator()
		helpmenu.AppendItem(aboutModel)
		helpmenu.AppendItem(contactModel)
		
		self.menuBar = wx.MenuBar()
		self.menuBar.Append(filemenu,_("&File"))
		self.menuBar.Append(diagrammenu,_("&Diagram"))
		self.menuBar.Append(showmenu, _("&Show"))
		self.menuBar.Append(settingsmenu, _("&Options"))
		self.menuBar.Append(helpmenu, _("&Help"))
		
		self.Bind(wx.EVT_MENU_HIGHLIGHT_ALL, self.OnMenuHighlight)

		self.SetMenuBar(self.menuBar)
		self.Bind(wx.EVT_MENU, self.OnOpenFile, id=openModel.GetId())
		self.Bind(wx.EVT_MENU, self.OnNew, id=newModel.GetId())
		self.Bind(wx.EVT_MENU, self.OnSaveFile, id=saveModel.GetId())
		self.Bind(wx.EVT_MENU, self.OnSaveAsFile, id=saveAsModel.GetId())
		#self.Bind(wx.EVT_MENU, self.OnExport, id=exportModel.GetId())
		#self.Bind(wx.EVT_MENU, self.OnImport, id=importModel.GetId())
		self.Bind(wx.EVT_MENU, self.OnDetruit, id=exitModel.GetId())
		self.Bind(wx.EVT_MENU, self.OnCloseWindow, id=exitModel.GetId())
		self.Bind(wx.EVT_MENU, self.OnHelp, id=helpModel.GetId())
		self.Bind(wx.EVT_MENU, self.OnAPI, id=apiModel.GetId())
		self.Bind(wx.EVT_MENU, self.OnAbout, id=aboutModel.GetId())
		self.Bind(wx.EVT_MENU, self.OnContact, id=contactModel.GetId())
		self.Bind(wx.EVT_MENU, self.OnShowShell, id=id_shell)
		self.Bind(wx.EVT_MENU, self.OnShowSimulation, id=id_sim)
		self.Bind(wx.EVT_MENU, self.OnShowToolBar, id=id_toolBar)

		self.Bind(wx.EVT_MENU, self.OnNew, id=newDiagram.GetId())
		self.Bind(wx.EVT_MENU, self.nb2.OnDetachPage, id=detachDiagram.GetId())
		self.Bind(wx.EVT_MENU, self.OnSimulation, id=simulationDiagram.GetId())
		self.Bind(wx.EVT_MENU, self.OnConstantsLoading, id=constantsDiagram.GetId())
		self.Bind(wx.EVT_MENU, self.OnPriorityGUI, id=priorityDiagram.GetId())
		self.Bind(wx.EVT_MENU, self.nb2.OnClearPage, id=clearDiagram.GetId())
		self.Bind(wx.EVT_MENU, self.OnZoom, id=zoomIn.GetId())
		self.Bind(wx.EVT_MENU, self.OnUnZoom, id=zoomOut.GetId())
		self.Bind(wx.EVT_MENU, self.AnnuleZoom, id=annuleZoom.GetId())
		self.Bind(wx.EVT_MENU, self.nb2.OnClosePage, id=closeDiagram.GetId())

		self.Bind(wx.EVT_MENU, self.OnFrench, id=fritem.GetId())
		self.Bind(wx.EVT_MENU, self.OnEnglish, id=enitem.GetId())
		self.Bind(wx.EVT_MENU, self.OnAdvancedSettings, id=moreitem.GetId())


	def MakeToolBar(self):
		""" Make main tools bar. 
		"""
	
		# for spash screen
		pub.sendMessage('object.added', 'Making tools bar ...')

		self.tb = self.CreateToolBar( wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT | wx.TB_TEXT)
		self.tb.SetToolBitmapSize((25,25)) # juste for windows
		
		self.Bind(wx.EVT_TOOL, self.OnNew, self.tb.AddSimpleTool(wx.NewId(), wx.Bitmap(os.path.join(ICON_PATH,'new.png')), _('New diagram (Ctrl+N)'),_('Create a new diagram in tab')))
		self.Bind(wx.EVT_TOOL, self.OnOpenFile, self.tb.AddSimpleTool(wx.NewId(), wx.Bitmap(os.path.join(ICON_PATH,'open.png')), _('Open File (Ctrl+O)'), _('Open an existing diagram')))
		self.tb.AddSeparator()
		self.Bind(wx.EVT_TOOL, self.OnSaveFile, self.tb.AddSimpleTool(wx.NewId(), wx.Bitmap(os.path.join(ICON_PATH,'save.png')), _('Save File (Ctrl+S)') , _('Save the current diagram')))
		self.Bind(wx.EVT_TOOL, self.OnSaveAsFile, self.tb.AddSimpleTool(wx.NewId(), wx.Bitmap(os.path.join(ICON_PATH,'save_as.png')), _('Save file as'), _('Save the diagram with an another name')))
		self.tb.AddSeparator()
		self.Bind(wx.EVT_TOOL, self.OnZoom, self.tb.AddSimpleTool(wx.NewId(), wx.Bitmap(os.path.join(ICON_PATH,'zoom+.png')), _('Zoom'),_('Zoom +')))
		self.Bind(wx.EVT_TOOL, self.OnUnZoom, self.tb.AddSimpleTool(wx.NewId(), wx.Bitmap(os.path.join(ICON_PATH,'zoom-.png')), _('UnZoom'),_('Zoom -')))
		self.Bind(wx.EVT_TOOL, self.AnnuleZoom, self.tb.AddSimpleTool(wx.NewId(), wx.Bitmap(os.path.join(ICON_PATH,'no_zoom.png')), _('AnnuleZoom'), _('Normal size')))
		self.tb.AddSeparator()
		self.Bind(wx.EVT_TOOL, self.OnPriorityGUI, self.tb.AddSimpleTool(wx.NewId(), wx.Bitmap(os.path.join(ICON_PATH,'priority.png')), _('Priority'), _('Define model activation priority')))
		self.Bind(wx.EVT_TOOL, self.OnSimulation, self.tb.AddSimpleTool(wx.NewId(), wx.Bitmap(os.path.join(ICON_PATH,'simulation.png')), _('Simulation (F5)'), _('Simulate the diagram')))
		self.tb.Realize()

	###
	def OnOpenRecentFile(self, event):
		""" Recent file has been invoked.
		"""

		id = event.GetId()
		#menu=event.GetEventObject()
		##on Linux, event.GetEventObject() returns a reference to the menu item, 
		##while on Windows, event.GetEventObject() returns a reference to the main frame.
		menu = self.GetMenuBar().FindItemById(event.GetId()).GetMenu()
		menuItem = menu.FindItemById(id)
		path = menuItem.GetItemLabelText()
		name = os.path.basename(path)

		diagram = ContainerBlock()
		diagram.last_name_saved = path

		if self.OpenFileProgess(diagram, path):
			self.nb2.AddEditPage(name, diagram)
		# si le fichier a été supprimé, on supprime le lien de la liste
		elif not os.path.exists(path):
			index = self.openFileList.index(path)
			del self.openFileList[index]
			self.cfg.Write("openFileList", str(eval("self.openFileList")))
		else:
			dlg = wx.MessageDialog(self, _('Error opening file\n'), 'Error', wx.OK | wx.ICON_ERROR)
			dlg.ShowModal()

	###	
	def OnMenuHighlight(self, event):
		# Show how to get menu item info from this event handler
		id = event.GetMenuId()
		item = self.GetMenuBar().FindItemById(id)
		if item:
			text = item.GetText()
			help = item.GetHelp()

		# but in this case just call Skip so the default is done
		event.Skip() 
	
	#def OnChange1(self, event):
		#'''
		#'''
		
		#if event.GetSelection() == 1:
			#canvas = self.nb2.GetPage(self.nb2.GetSelection())
			#parent= self
			#selectedList=canvas.getSelectedShapes()
			
			
			#if selectedList != []:
				
				#selectedModel=selectedList[0]
				
				##self.propSizer.Detach(self.propContent)
				##self.propContent.Show(False)
				#self.nb1.GetPage(self.nb1.GetSelection()).Show(False)
				#self.propPanel=AttributeEditor(self.nb1,wx.ID_ANY, selectedModel.label, selectedModel, parent.GetId())
				#self.nb1.GetPage(self.nb1.GetSelection()).Show(True)
				##self.propPanel.Show()
				##self.propSizer.Add(self.propContent, 0, wx.ALL, 10)
				
				##self.propContent=AttributeEditor(self.nb1,wx.ID_ANY, selectedModel.label, selectedModel, parent.GetId())
				##self.propSizer.Add(self.propContent, 1, wx.EXPAND)
				##self.propSizer.RecalcSizes()
				
				
				
				##self.nb1.InsertPage(2,AttributeEditor(self.nb1,wx.ID_ANY, selectedModel.label, selectedModel, parent.GetId()),_("Properties"),imageId=1
				##self.nb1.SetSelection(1)
				
			##else:
				##i=self.nb1.GetSelection()
				##panel1 = wx.Panel(self.nb1, wx.ID_ANY, style=wx.WANTS_CHARS)
				##panel1.SetBackgroundColour(wx.WHITE)
				##self.nb1.DeletePage(1)
				##self.nb1.InsertPage(1,panel1,_("Properties"), imageId=1)
				##self.nb1.SetSelection(i)
			### rester sur la selection retenu !
			##self.nb1.SetSelection(1)
			#event.Skip()
	
	###
	def OnDragInit(self, event):
		
		# version avec arbre
		item = event.GetItem()
		tree = event.GetEventObject()
		
		# Dnd uniquement sur les derniers fils de l'arbre
		if not tree.ItemHasChildren(item):
			text = tree.GetItemPyData(event.GetItem())
			try:
				tdo = wx.PyTextDataObject(text)
				tds = wx.DropSource(tree)
				tds.SetData(tdo)
				tds.DoDragDrop(True)
			except:
				sys.stderr.write("OnDragInit avorting \n")
			
	###
	def OnTaskBarActivate(self, evt):
		if self.IsIconized():
			self.Iconize(False)
		if not self.IsShown():
			self.Show(True)
		self.Raise()
	###
	def OnTaskBarMenu(self, evt):
		menu = wx.Menu()
		menu.Append(self.TBMENU_RESTORE, _("Restore DEVSimPy"))
		menu.Append(self.TBMENU_CLOSE,   _("Close"))
		self.tbicon.PopupMenu(menu)
		menu.Destroy()
	###
	def OnTaskBarClose(self, evt):
		self.Close()
		# because of the way wx.TaskBarIcon.PopupMenu is implemented we have to
		# prod the main idle handler a bit to get the window to actually close
		wx.GetApp().ProcessIdle()
	
	##---------------------------------------------
	#def ShowTip(self):
		#try:
			#showTipText = open(opj("data/showTips")).read()
			#showTip, index = eval(showTipText)
		#except IOError:
			#showTip, index = (1, 0)
		#if showTip:
			#tp = wx.CreateFileTipProvider(opj("data/tips.txt"), index)
			#showTip = wx.ShowTip(self, tp)
			#index = tp.GetCurrentTip()
			#open(opj("data/showTips"), "w").write(str( (showTip, index) ))
	
	###
	def OnIdle(self, event):
		if self.otherWin:
			self.otherWin.Raise()
			self.otherWin = None

	###
	def SaveLibraryProfile(self):
		#gestion du profil des libraries dans .DEVSimPy
		L = self.tree.GetItemChildren(self.tree.root)
		# écriture des domaines actuels
		ChargedDomainList = [item for item in filter(lambda k: self.tree.ItemDico[k] in L ,self.tree.ItemDico)]
		self.cfg.Write("ChargedDomainList", str(ChargedDomainList))
			
		self.dying = True
		self.mainmenu = None
		if hasattr(self, "tbicon"):
			del self.tbicon

	###
	def OnCloseWindow(self, event):
		currentPage = self.nb2.GetCurrentPage()
		diagram = currentPage.diagram
		file_name = os.path.basename(diagram.last_name_saved)
		if diagram.modify and self.nb2.GetPageCount() >= 1:
			dlg = wx.MessageDialog(self, _('Save changes to the current diagram ?'), '', wx.YES_NO | wx.YES_DEFAULT | wx.CANCEL | wx.ICON_QUESTION)
			val = dlg.ShowModal()
			if val == wx.ID_YES:
				self.OnSaveFile(event)
				self.SaveLibraryProfile()
				self.Destroy()
			elif val == wx.ID_CANCEL:
				dlg.Destroy()
			else:
				self.SaveLibraryProfile()
				self.Destroy()
		else:
			self.SaveLibraryProfile()
			self.Destroy()
	#---------------------------------------------
	#def OnIconfiy(self, evt):
		#wx.LogMessage("OnIconfiy")
		#evt.Skip()
	#---------------------------------------------
	#def OnMaximize(self, evt):
		#wx.LogMessage("OnMaximize")
		#evt.Skip()
	####
	#def OnFileExit(self, event):
		#self.Close()
	
	###
	def OnZoom(self,event):
		currentPage = self.nb2.GetCurrentPage()
		currentPage.scalex=max(currentPage.scalex+.05,.3)
		currentPage.scaley=max(currentPage.scaley+.05,.3)
		currentPage.Refresh()
	
	###
	def OnUnZoom(self,event):
		currentPage = self.nb2.GetCurrentPage()
		currentPage.scalex=currentPage.scalex-.05
		currentPage.scaley=currentPage.scaley-.05
		currentPage.Refresh()
	
	###
	def AnnuleZoom(self,event):
		currentPage = self.nb2.GetCurrentPage()
		currentPage.scalex = 1.0
		currentPage.scaley = 1.0
		currentPage.Refresh()
	
	###
	def OnNew(self, event):
		self.nb2.AddEditPage("Diagram %d"%ShapeCanvas.ID)
		return self.nb2.GetCurrentPage()

	###
	def OpenFileProgess(self, diagram, new_path):
		""" Decor the LoadFileThread with a progess Dialogue.
		"""

		progress_dlg = wx.ProgressDialog(_("DEVSimPy open file"),
								_("Loading %s ...")%os.path.basename(new_path), parent=self,
								style=wx.PD_APP_MODAL | wx.PD_ELAPSED_TIME)
		progress_dlg.Pulse()

		thread = LoadFileThread(diagram, new_path)

		while thread.isAlive():
			time.sleep(0.3)
			progress_dlg.Pulse()

		progress_dlg.Destroy()
		wx.SafeYield()

		return thread.finish()

	###
	def OnOpenFile(self, event):
		""" Open file button has been pressed.
		"""

		wcd = "DEVSimPy files (*.dsp)|*.dsp|All files (*)|*"
		home = os.getenv('USERPROFILE') or os.getenv('HOME') or os.getcwd()
		open_dlg = wx.FileDialog(self, message = 'Choose a file', defaultDir = home, defaultFile = "", wildcard = wcd, style = wx.OPEN|wx.MULTIPLE|wx.CHANGE_DIR)
		
		new_path = None
		# get the new path from open file dialogue
		if open_dlg.ShowModal() == wx.ID_OK:

			new_path = open_dlg.GetPath()
			fileName = open_dlg.GetFilename()
			diagram = ContainerBlock()
			diagram.last_name_saved = new_path

			open_dlg.Destroy()
		
		# load the new_path file with ConnectionThread function
		if new_path:

			if self.OpenFileProgess(diagram, new_path):
				
				self.nb2.AddEditPage(fileName,diagram)
				
				# ajout dans la liste des derniers fichier ouvert (avec gestion de la suppression du dernier inserer)
				if not new_path in self.openFileList:
					self.openFileList.insert(0, new_path)
					del self.openFileList[-1]
					self.cfg.Write("openFileList", str(eval("self.openFileList")))
			else:
				dlg = wx.MessageDialog(self, _('Error opening file\n'), 'Error', wx.OK | wx.ICON_ERROR)
				dlg.ShowModal()
	###
	def OnSaveFile(self, event):
		""" Save file button has been pressed.
		"""

		currentPage = self.nb2.GetCurrentPage()
		diagram = currentPage.diagram
		
		if diagram.last_name_saved:
			assert(os.path.isabs(diagram.last_name_saved))
			if currentPage.diagram.SaveFile(diagram.last_name_saved):
				currentPage.Refresh()
				diagram.modify = False
			else:
				dlg = wx.MessageDialog(self, _('Error saving file\n') ,'Error', wx.OK | wx.ICON_ERROR)
				dlg.ShowModal()
		else:
			wcd = "DEVSimPy files (*.dsp)|*.dsp|All files (*)|*"
			home = os.getenv('USERPROFILE') or os.getenv('HOME') or os.getcwd()
			save_dlg = wx.FileDialog(	self, 
										message = _('Save file as...'), 
										defaultDir = home, 
										defaultFile = currentPage.name, 
										wildcard = wcd, 
										style = wx.SAVE|wx.OVERWRITE_PROMPT)

			if save_dlg.ShowModal() == wx.ID_OK:
				path = save_dlg.GetPath()

				#ajoute .dsp si il existe pas
				if not path.endswith('.dsp'):
					path = ''.join([path,'.dsp'])

				if currentPage.diagram.SaveFile(path):
					self.nb2.SetPageText(self.nb2.GetSelection(),save_dlg.GetFilename())
					diagram.last_name_saved = path
					diagram.modify = False
				else:
					dlg = wx.MessageDialog(self, _('Error saving file\n') ,'Error', wx.OK | wx.ICON_ERROR)
					dlg.ShowModal()
				
			save_dlg.Destroy()
			
	###
	def OnSaveAsFile(self, event):
		""" Save file menu as has been selected. 
		"""
		currentPage = self.nb2.GetCurrentPage()
		diagram = currentPage.diagram
		
		wcd = "DEVSimPy files (*.dsp)|*.dsp|All files (*)|*"
		home = os.getenv('USERPROFILE') or os.getenv('HOME') or os.getcwd()
		save_dlg = wx.FileDialog(self, message=_('Save file as...'), defaultDir=home, defaultFile='', wildcard=wcd, style=wx.SAVE | wx.OVERWRITE_PROMPT)

		if save_dlg.ShowModal() == wx.ID_OK:

			path = save_dlg.GetPath()

			#ajoute .dsp si il existe pas
			if not path.endswith('.dsp'):
				path=''.join([path,'.dsp'])
			
			#sauvegarde dans le nouveau fichier
			if currentPage.diagram.SaveFile(path):
				diagram.last_name_saved = path
				self.nb2.AddEditPage(save_dlg.GetFilename(),diagram)
			else:
				dlg = wx.MessageDialog(self, _('Error saving file\n'), 'Error', wx.OK | wx.ICON_ERROR)
				dlg.ShowModal()

		save_dlg.Destroy()
		
	###
	def OnImport(self, event):
		""" Import DEVSimPy library from Domain directory.
		"""
		
		# dialog pour l'importation de lib DEVSiPy (dans Domain) et le local
		dlg = ImportLibrary(self,wx.ID_ANY,_("Import Library"))
		
		if (dlg.ShowModal() == wx.ID_OK):
			
			for s in dlg.selectedItem:
				absdName = str(self.tree.domainPath+os.sep+s) if s not in dlg.d else str(dlg.d[s])
				self.tree.InsertNewDomain(absdName, self.tree.GetRootItem(), self.tree.GetSubDomain(absdName, self.tree.GetDomainList(absdName)).values()[0])
			
			self.tree.SortChildren(self.tree.GetRootItem())
					
		dlg.Destroy()
		
	###     
	def OnSearch(self,evt):
		"""
		"""
		
		# text taper par l'utilisateur
		text = self.search.GetValue()
		
		#list des mots trouves
		L = []
		#pour tout les parents qui n'ont pas de fils (bout de branche)
		for item in filter(lambda elem: not self.tree.ItemHasChildren(elem), self.tree.ItemDico.values()):
			path = self.tree.GetPyData(item)
			dirName = os.path.basename(path)
			bool = False
			#comparaison lettre par lettre (pas optimal)
			for i,s in zip(range(len(text)),text):
				if s == dirName[i]:
					bool = True
				else:
					bool = False
					break
			# si jamais false alors ajout dans la list des nom trouve
			if bool:
				L.append(path)
		
		#masque l'arbre
		self.tree.Show(False)
		
		# Liste des domain concernes
		if L != []:
			
			# on supprime l'ancien searchTree
			for item in self.searchTree.GetItemChildren(self.searchTree.GetRootItem()):
				self.searchTree.RemoveItem(item)
			
			#construction du nouveau
			self.searchTree.Create(map(lambda s: os.path.dirname(s), L))
			
			for item in filter(lambda elem: not self.searchTree.ItemHasChildren(elem), copy.copy(self.searchTree.ItemDico).values()):
				path = self.tree.GetPyData(item)	
				if path not in L:
					self.searchTree.RemoveItem(item)
				
			self.searchTree.Show(True)
			self.nb1.libPanel.GetSizer().Layout()
			self.searchTree.ExpandAll()
			
		else:
			if len(text) == 0:
				self.tree.Show(True)
			else:
				self.tree.Show(False)
			
			self.searchTree.Show(False)

	###
	def GetDiagramByWindow(self,window):
		""" Method that give the diagram present into the windows
		"""

		# la fenetre par laquelle a été invoqué l'action peut être principale (wx.App) ou detachée (DetachedFrame)			
		if isinstance(window,DetachedFrame):
			return window.GetCanvas().GetDiagram()
		else:
			activePage = window.nb2.GetSelection()
			return window.nb2.GetPage(activePage).GetDiagram()
	###
	def GetWindowByEvent(self,event):
		""" Method that give the window instance from the event
		"""

		obj = event.GetEventObject()

		# si invocation de l'action depuis une ToolBar
		if isinstance(obj, wx.ToolBar) or isinstance(obj, wx.Frame):
			window = obj.GetTopLevelParent()
		# si invocation depuis une Menu (pour le Show dans l'application principale)
		elif isinstance(obj, wx.Menu):
			window = wx.GetApp().GetTopWindow()
		else:
			sys.stdout.write(_("This option has not been implemented yet.\n"))
			return False

		return window

	###
	def OnConstantsLoading(self, event):
		""" Method calling the AddConstants windows.
		"""

		diagram = self.GetDiagramByWindow(self.GetWindowByEvent(event))
		diagram.AddConstants(event)

	###
	def OnPriorityGUI(self, event):
		""" Method calling the PriorityGui.
		"""

		parent = self.GetWindowByEvent(event)
		diagram = self.GetDiagramByWindow(parent)
		diagram.OnPriority(parent)
	
	###             
	def OnSimulation(self, event):
		""" Method calling the simulationGUI.
		"""

		parent = self.GetWindowByEvent(event)
		diagram = self.GetDiagramByWindow(parent)
		return diagram.OnSimulation(event)

	##----------------------------------------------
	#def AdjustTab(self, evt):
		## clic sur simulation
		#if evt.GetSelection() == 2:
			#self.FindWindowByName("splitter").SetSashPosition(350)
		#elif evt.GetSelection() == 1:
		## clic sur property
			#self.FindWindowByName("splitter").SetSashPosition(350)
		## clic sur library
		#else:
			#self.FindWindowByName("splitter").SetSashPosition(350)
		#evt.Skip()

	###
	def OnDetruit(self, evt):
		""" Destroy button has been clicked.
		"""

		currentPage = self.nb2.GetCurrentPage()
		diagram = currentPage.diagram
		if diagram.modify:
			dlg = wx.MessageDialog(self, _('Save changes to the current diagram ?'), '', wx.YES_NO | wx.YES_DEFAULT | wx.CANCEL | wx.ICON_QUESTION)
			val = dlg.ShowModal()
			if val == wx.ID_YES:
				self.OnSaveFile(evt)
				self.OnOpenFile()
				self.nb2.OnClosePage()
			elif val == wx.ID_NO:
				dlg.Destroy()
				self.nb2.OnClosePage()
			else:
				dlg.Destroy()
		else:
			self.nb2.OnClosePage()

	###
	def OnShowShell(self, evt):
		""" Shell view menu has been pressed.
		"""

		menu = self.GetMenuBar().FindItemById(evt.GetId())
		if menu.IsChecked():
			self.splitter2.SplitHorizontally(self.nb2, self.panel4, 500)
		else:
			self.splitter2.Unsplit()

	###
	def OnShowSimulation(self, evt):
		""" Simulation view menu has been pressed.
		"""

		menu = self.GetMenuBar().FindItemById(evt.GetId())
		if menu.IsChecked():
			menu.Check(self.OnSimulation(evt))
		else:
			self.nb1.RemovePage(2)

	###
	def OnShowToolBar(self, evt):
		self.tb.Show(not self.tb.IsShown())
		
	###
	def OnFrench(self, event):
		self.cfg.Write("language", "'fr'")
		dlg = wx.MessageDialog(self, _('You need to restart DEVSimPy to take effect \n Do you want to restart now ?'), 'Question', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
		if dlg.ShowModal() == wx.ID_YES:
			self.Close()
	###		
	def OnEnglish(self, event):
		self.cfg.Write("language", "'en'")
		dlg = wx.MessageDialog(self, _('You need to restart DEVSimPy to take effect\n Do you want to restart now ?'), 'Question', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
		if dlg.ShowModal() == wx.ID_YES:
			self.Close()
	###
	def OnAdvancedSettings(self, event):
		sys.stdout.write(_("This option has not been implemented yet.\n"))
	###
	def OnRestart(self):
		pass

	def OnHelp(self, event):
		""" Shows the DEVSimPy help file. """

		# Not implemented yet...
		dlg = wx.MessageDialog(self, _("This option has not been implemented yet."), 'Info', wx.OK)
		dlg.ShowModal()

	def OnAPI(self, event):
		""" Shows the DEVSimPy API help file. """

		#webbrowser.open_new(opj(self.installDir + "/docs/api/index.html"))
		dlg = wx.MessageDialog(self, _("This option has not been implemented yet."), 'Info', wx.OK)
		dlg.ShowModal()

	#def OnCheckUpgrade(self, event):
		#""" Checks for a possible upgrade of GUI2Exe. """

		#dlg = wx.ProgressDialog(_("DEVSimPy: Check for upgrade"),
								#_("Attempting to connect to the internet..."), parent=self,
								#style=wx.PD_APP_MODAL | wx.PD_ELAPSED_TIME)
		#dlg.Pulse()
		## Run in a separate thread
		#thread = ConnectionThread(self)
		#while thread.isAlive():
			#time.sleep(0.3)
			#dlg.Pulse()

		#dlg.Destroy()
		#wx.SafeYield()

	@BuzyCursorNotification
	def OnAbout(self, event):
		""" About menu has been pressed.
		"""

		description = _("""DEVSimPy is an advanced wxPython framework for the modeling and simulation of systems based on the DEVS formalism. Features include powerful built-in editor, advanced modeling approach, powerful discrete event simulation algorithm, import/export DEVS components library and more.
		""")

		licence =_( """DEVSimPy is free software; you can redistribute it and/or modify it 
		under the terms of the GNU General Public License as published by the Free Software Foundation; 
		either version 2 of the License, or (at your option) any later version.

		DEVSimPy is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; 
		without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  
		See the GNU General Public License for more details. You should have received a copy of 
		the GNU General Public License along with File Hunter; if not, write to 
		the Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA""")

		info = wx.AboutDialogInfo()

		info.SetIcon(wx.Icon(os.path.join('bitmaps','IconeDEVSimPy.png'), wx.BITMAP_TYPE_PNG))
		info.SetName('DEVSimPy')
		info.SetVersion(self.GetVersion())
		info.SetDescription(description)
		info.SetCopyright(_('(C) 2008 dec SPE Laboratory'))
		info.SetWebSite('http://www.spe.univ-corse.fr')
		info.SetLicence(licence)
		info.AddDeveloper(_('L. Capocchi and all.'))
		info.AddDocWriter(_('L. Capocchi and all.'))
		info.AddArtist(_('L. Capocchi and all.'))
		info.AddTranslator(_('L. Capocchi and all.'))

		wx.AboutBox(info)

	def OnContact(self, event):
		""" Launches the mail program to contact the DEVSimPy author. """
		wx.BeginBusyCursor()
		webbrowser.open_new("mailto:capocchi@univ-corse.fr?subject=Comments On DEVSimPy&cc=lcapocchi@gmail.com")
		wx.CallAfter(wx.EndBusyCursor)


##-------------------------------------------------------------------
class AdvancedSplashScreen(AdvancedSplash):
	""" A splash screen class, with a shaped frame. 
	"""
	
	# # These Are Used To Declare If The AdvancedSplash Should Be Destroyed After The   
	# # Timeout Or Not   
	AS_TIMEOUT = 1   
	AS_NOTIMEOUT = 2   
	#    
	# # These Flags Are Used To Position AdvancedSplash Correctly On Screen   
	AS_CENTER_ON_SCREEN = 4   
	AS_CENTER_ON_PARENT = 8   
	AS_NO_CENTER = 16   
	#    
	# # This Option Allow To Mask A Colour In The Input Bitmap   
	AS_SHADOW_BITMAP = 32

	###
	def __init__(self, app):
		""" A splash screen constructor

		**Parameters:**

		* `app`: the current wxPython app.
		"""

		splashStyle = wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_TIMEOUT
		splashBmp = wx.Image(os.path.join('bitmaps','splash5.png')).ConvertToBitmap()
		splashDuration=2000
		
		if old:
			AdvancedSplash.__init__(self, bitmap=splashBmp, style=splashStyle, timeout=splashDuration, parent=None)
		else:
			style=wx.NO_BORDER|wx.FRAME_NO_TASKBAR|wx.STAY_ON_TOP|wx.FRAME_SHAPED
			extrastyle=AdvancedSplashScreen.AS_TIMEOUT|AdvancedSplashScreen.AS_CENTER_ON_SCREEN
			AdvancedSplash.__init__(self, bitmap=splashBmp, timeout=splashDuration, style=style, extrastyle=extrastyle, shadowcolour=wx.WHITE, parent=None)

		self.SetTextPosition((30,210))
		self.SetTextFont(wx.Font(9, wx.SWISS, wx.ITALIC, wx.NORMAL, False))
		self.SetTextColour("#afb6d0")
		
		wx.EVT_CLOSE(self, self.OnClose)
		self.fc = wx.FutureCall(500, self.ShowMain)
		self.app = app
		
		# for spash
		pub.subscribe(self.__onObjectAdded, 'object.added')


	def __onObjectAdded(self, message):
		# data passed with your message is put in message.data. 
		# Any object can be passed to subscribers this way. 
		self.SetText(message.data)

	def OnClose(self, event):
		""" Handles the wx.EVT_CLOSE event for SplashScreen. """

		# Make sure the default handler runs too so this window gets
		# destroyed
		event.Skip()
		self.Hide()

		# if the timer is still running then go ahead and show the
		# main frame now
		if self.fc.IsRunning():
		# Stop the wx.FutureCall timer
			self.fc.Stop()
			self.ShowMain()


	def ShowMain(self):
		""" Shows the main application (DEVSimPy). """

		self.app.frame = MainApplication(None, wx.ID_ANY, 'DEVSimPy')

		# recuperation dans un attribut de stdio qui est invisible pour l'instant
		self.app.frame.stdioWin = self.app.stdioWin
		wx.App.SetTopWindow(self.app, self.app.frame)

		if self.fc.IsRunning():
		# Stop the splash screen timer and close it
			self.Raise()

#------------------------------------------------------------------------
class LogFrame(wx.Frame):
	""" Log Frame class
	"""

	def __init__(self, parent, id, title, position, size):
		""" constructor
		"""
		
		wx.Frame.__init__(self, parent, id, title, position, size, style=wx.DEFAULT_FRAME_STYLE)
		self.Bind(wx.EVT_CLOSE, self.OnClose)


	def OnClose(self, event):
		"""	Handles the wx.EVT_CLOSE event
		"""
		self.Show(False)
			
#------------------------------------------------------------------------------                
class PyOnDemandOutputWindow(threading.Thread):
	"""
	A class that can be used for redirecting Python's stdout and
	stderr streams.  It will do nothing until something is wrriten to
	the stream at which point it will create a Frame with a text area
	and write the text there.
	"""
	def __init__(self, title = "wxPython: stdout/stderr"):
		threading.Thread.__init__(self)
		self.frame  = None
		self.title  = title
		self.pos    = wx.DefaultPosition
		self.size   = (450, 300)
		self.parent = None
		self.st = None
		
	def SetParent(self, parent):
		"""Set the window to be used as the popup Frame's parent."""
		self.parent = parent

	def CreateOutputWindow(self, st):
		self.st = st
		self.start()
		#self.frame.Show(True)

	def run(self):
		self.frame = LogFrame(self.parent, wx.ID_ANY, self.title, self.pos, self.size)
		self.text  = wx.TextCtrl(self.frame, wx.ID_ANY, "", style = wx.TE_MULTILINE|wx.HSCROLL)
		self.text.AppendText(self.st)
		
	# These methods provide the file-like output behaviour.
	def write(self, text):
		"""
		If not called in the context of the gui thread then uses
		CallAfter to do the work there.
		"""
		if self.frame is None:
			if not wx.Thread_IsMain():
				wx.CallAfter(self.CreateOutputWindow, text)
			else:
				self.CreateOutputWindow(text)
		else:
			if not wx.Thread_IsMain():
				wx.CallAfter(self.text.AppendText, text)
			else:
				self.text.AppendText(text)

	def close(self):
		if self.frame is not None:
			wx.CallAfter(self.frame.Close)

	def flush(self):
		pass

#-------------------------------------------------------------------
class DEVSimPyApp(wx.App):

	outputWindowClass = PyOnDemandOutputWindow

	def __init__(self, redirect=False, filename=None):
		wx.App.__init__(self,redirect, filename)
		
		# make sure we can create a GUI
		if not self.IsDisplayAvailable():
			
			if wx.Platform == '__WXMAC__':
				msg = """This program needs access to the screen.
				Please run with 'pythonw', not 'python', and only when you are logged
				in on the main display of your Mac."""
				
			elif wx.Platform == '__WXGTK__':
				msg ="Unable to access the X Display, is $DISPLAY set properly?"

			else:
				msg = 'Unable to create GUI'
				# TODO: more description is needed for wxMSW...

			raise SystemExit(msg)
		
		# Save and redirect the stdio to a window?
		self.stdioWin = None
		self.saveStdio = (sys.stdout, sys.stderr)
		if redirect:
			self.RedirectStdio(filename)

	def SetTopWindow(self, frame):
		"""Set the \"main\" top level window"""
		if self.stdioWin:
			self.stdioWin.SetParent(frame)
		wx.App.SetTopWindow(self, frame)
		
	def RedirectStdio(self, filename=None):
		"""Redirect sys.stdout and sys.stderr to a file or a popup window."""
		if filename:
			sys.stdout = sys.stderr = open(filename, 'a')
		else:
			# ici on cree la fenetre !
			DEVSimPyApp.outputWindowClass.parent=self
			self.stdioWin = DEVSimPyApp.outputWindowClass('DEVSimPy Output')
			sys.stdout = sys.stderr = self.stdioWin
			
	def RestoreStdio(self):
		try:
			sys.stdout, sys.stderr = self.saveStdio
		except:
			pass

	def MainLoop(self):
		"""Execute the main GUI event loop"""
		wx.App.MainLoop(self)
		self.RestoreStdio()

	def Destroy(self):
		self.this.own(False)
		wx.App.Destroy(self)
		
	def __del__(self, destroy = wx.App.__del__):
		self.RestoreStdio()  # Just in case the MainLoop was overridden
		destroy(self)

	def SetOutputWindowAttributes(self, title=None, pos=None, size=None):
		"""
		Set the title, position and/or size of the output window if
		the stdio has been redirected.  This should be called before
		any output would cause the output window to be created.
		"""
		if self.stdioWin:
			if title is not None:
				self.stdioWin.title = title
			if pos is not None:
				self.stdioWin.pos = pos
			if size is not None:
				self.stdioWin.size = size

	def OnInit(self):
		"""
		Create and show the splash screen.  It will then create and show
		the main frame when it is time to do so.
		"""
		wx.InitAllImageHandlers()
		
		# start our application
		#self.frame = MainApplication(None, wx.ID_ANY, 'DEVSimPy')
		#self.frame.stdioWin=self.stdioWin
		#self.frame.Show()
		
		# Set up the exception handler...
		sys.excepthook = ExceptionHook

		# start our application with splash
		splash = AdvancedSplashScreen(self)
		splash.Show()

		return True

#-------------------------------------------------------------------
if __name__ == '__main__':

	## si redirect=True et filename=None alors redirection dans une fenetre
	## si redirect=True et filename="fichier" alors redirection dans un fichier
	## si redirect=False redirection dans la console
	app = DEVSimPyApp(redirect = False, filename = None)
	app.MainLoop()
