#!/usr/bin/env python
# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# devsimpy.py --- DEVSimPy - The Python DEVS GUI modeling and simulation software
#                     --------------------------------
#                            Copyright (c) 2021
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 4.0                                      last modified:  05/15/20
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
# strong depends: wxPython, PyPubSub (3.3.0)
# light depends: NumPy for spectrum analysis, mathplotlib for graph display
# remarks: lib tree is build by the TreeLitLib class.
# Moreover, __init__.py file is required for the build (see GetSubDomain method).
# in order to make a lib:
#	1/ make a MyLib rep with Message.py, DomainBehavior.py and DomaineStrucutre.py
#   2/ __all_ = [] in __init__.py file must use return
#   3/ python file that is not in __all__ is not imported
#   4/ the constructor of all class must have a default value of the parameters
#   5/ __str__ method must be implemented for .py in order to have a correct 
# name in the GUI (otherwise AM is displayed)
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GLOBAL VARIABLES AND FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

from csv import excel_tab
import datetime
import copy
import os
import sys
import time
import locale
import re
import gettext
import builtins
import platform
import threading
import subprocess
import pickle
import builtins
import glob
import pstats

from configparser import ConfigParser
from tempfile import gettempdir

if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3")

__authors__ = "Laurent Capocchi <capocchi_l@univ-corse.fr>, SISU project group <santucci_j@univ-corse.fr>"
__date__ = str(datetime.datetime.now())
__version__ = '4.0'
__docformat__ = 'epytext'
__min_wx_version__ = '4.0'

ABS_HOME_PATH = os.path.abspath(os.path.dirname(sys.argv[0]))

################################################################
### Loading wx python library
################################################################

### ini file exist ?
parser = ConfigParser()
parser.read(os.path.join(os.path.expanduser("~"),'devsimpy.ini'))
section, option = ('wxversion', 'to_load')
ini_exist = parser.has_option(section, option)

import wx

### check if an upgrade of wxpython is possible from pip !
sys.stdout.write("Importing wxPython %s%s for python %s on %s (%s) platform...\n"%(wx.version(), " from devsimpy.ini" if ini_exist else '', platform.python_version(), platform.system(), platform.version()))

import gettext
_ = gettext.gettext

try:
	import wx.aui as aui
except:
	import wx.lib.agw.aui as aui

import wx.py as py
import wx.lib.dialogs
import wx.html
import wx.lib.mixins.inspection as wit

try:
	from wx.lib.agw import advancedsplash
	AdvancedSplash = advancedsplash.AdvancedSplash
	old = False
except ImportError:
	AdvancedSplash = wx.SplashScreen
	old = True

# to send event
try:
	from pubsub import pub
except Exception:
	sys.stdout.write('Last version for Python2 is PyPubSub 3.3.0 \n pip install PyPubSub==3.3.0')
	sys.exit()

if wx.VERSION_STRING >= '4.0':

	import wx.adv
	
	wx.FutureCall = wx.CallLater
	wx.SAVE = wx.FD_SAVE
	wx.OPEN = wx.FD_OPEN
	wx.DEFAULT_STYLE = wx.FD_DEFAULT_STYLE
	wx.MULTIPLE = wx.FD_MULTIPLE
	wx.CHANGE_DIR = wx.FD_CHANGE_DIR
	wx.OVERWRITE_PROMPT = wx.FD_OVERWRITE_PROMPT
	
	wx.AboutDialogInfo = wx.adv.AboutDialogInfo
	wx.AboutBox = wx.adv.AboutBox
	
### specific built-in variables. (don't modify the default value. If you want to change it, go to the PreferencesGUI from devsimpy interface.)
builtin_dict = {'SPLASH_PNG': os.path.join(ABS_HOME_PATH, 'splash', 'splash.png'), # abslolute path
				'DEVSIMPY_PNG': 'iconDEVSimPy.png',	# png file for devsimpy icon
				'HOME_PATH': ABS_HOME_PATH,
				'ICON_PATH': os.path.join(ABS_HOME_PATH, 'icons'),
				'ICON_PATH_16_16': os.path.join(ABS_HOME_PATH, 'icons', '16x16'),
				'SIMULATION_SUCCESS_SOUND_PATH': os.path.join(ABS_HOME_PATH,'sounds', 'Simulation-Success.wav'),
				'SIMULATION_ERROR_SOUND_PATH': os.path.join(ABS_HOME_PATH,'sounds', 'Simulation-Error.wav'),
				'DOMAIN_PATH': os.path.join(ABS_HOME_PATH, 'Domain'), # path of local lib directory
				'NB_OPENED_FILE': 5, # number of recent files
				'NB_HISTORY_UNDO': 5, # number of undo
				'OUT_DIR': 'out', # name of local output directory (composed by all .dat, .txt files)
				'PLUGINS_PATH': os.path.join(ABS_HOME_PATH, 'plugins'), # path of plug-ins directory
				'FONT_SIZE': 12, # Block font size
				'LOCAL_EDITOR': True, # for the use of local editor
				'EXTERNAL_EDITOR_NAME': "", # the name of the external code editor (only if LOCAL_EDITOR is False) 
				'LOG_FILE': os.devnull, # log file (null by default)
				'DEFAULT_SIM_STRATEGY': 'bag-based', #choose the default simulation strategy for PyDEVS
				'PYDEVS_SIM_STRATEGY_DICT' : {'original':'SimStrategy1', 'bag-based':'SimStrategy2', 'direct-coupling':'SimStrategy3'}, # list of available simulation strategy for PyDEVS package
                'PYPDEVS_SIM_STRATEGY_DICT' : {'classic':'SimStrategy4', 'parallel':'SimStrategy5'}, # list of available simulation strategy for PyPDEVS package
				'PYPDEVS_221_SIM_STRATEGY_DICT' : {'classic':'SimStrategy4', 'parallel':'SimStrategy5'}, # list of available simulation strategy for PyPDEVS package
				'HELP_PATH' : os.path.join('doc', 'html'), # path of help directory
				'NTL' : False, # No Time Limit for the simulation
				'DYNAMIC_STRUCTURE' : False, # Dynamic Structure for local PyPDEVS simulation
				'REAL_TIME': False, ### PyPDEVS threaded real time simulation
				'VERBOSE':False,
				'TRANSPARENCY' : True, # Transparancy for DetachedFrame
				'NOTIFICATION': True,
				'DEFAULT_PLOT_DYN_FREQ' : 100, # frequence of dynamic plot of QuickScope (to avoid overhead),
				'DEFAULT_DEVS_DIRNAME':'PyDEVS', # default DEVS Kernel directory
				'DEVS_DIR_PATH_DICT':{'PyDEVS':os.path.join(ABS_HOME_PATH,'DEVSKernel','PyDEVS'),
									'PyPDEVS_221':os.path.join(ABS_HOME_PATH,'DEVSKernel','PyPDEVS','pypdevs221' ,'src'),
									'PyPDEVS':os.path.join(ABS_HOME_PATH,'DEVSKernel','PyPDEVS','old')},
				'GUI_FLAG':True
				}

### Check if the pypdevs241 directory is empty (not --recursive option when the devsimpy git has been cloned)
path = os.path.join(ABS_HOME_PATH,'DEVSKernel','PyPDEVS','pypdevs241')
if os.path.exists(path) and not len(os.listdir(path)) == 0:
	builtin_dict['PYPDEVS_241_SIM_STRATEGY_DICT'] = {'classic':'SimStrategy4', 'parallel':'SimStrategy5'}
	builtin_dict['DEVS_DIR_PATH_DICT'].update({'PyPDEVS_241':os.path.join(path ,'src','pypdevs')})
else:
	sys.stdout.write("PyPDEVS Kernel in version 2.4.1 is not loaded.\nPlease install it in the directory %s using git (https://msdl.uantwerpen.be/git/yentl/PythonPDEVS.git)\n"%path)

### here berfore the __main__ function
### warning, some module (like SimulationGUI) initialise GUI_FLAG macro before (import block below)
#builtin_dict['GUI_FLAG'] = False

# Sets the homepath variable to the directory where your application is located (sys.argv[0]).
builtins.__dict__.update(builtin_dict)

### Deprecation warnings with Python 3.8
wx._core.WindowIDRef.__index__ = wx._core.WindowIDRef.__int__

### import Container much faster loading than from Container import ... for os windows only
import Container
import Menu
import ReloadModule

from ImportLibrary import ImportLibrary
from Reporter import ExceptionHook
from PreferencesGUI import PreferencesGUI
from PluginManager import PluginManager
from Utilities import GetUserConfigDir, install, install_and_import, updatePiPPackages, updateFromGitRepo, updateFromGitArchive, NotificationMessage
from Decorators import redirectStdout, BuzyCursorNotification, ProgressNotification, cond_decorator
from DetachedFrame import DetachedFrame
from LibraryTree import LibraryTree
from LibPanel import LibPanel
from PropPanel import PropPanel
from ControlNotebook import ControlNotebook
from DiagramNotebook import DiagramNotebook
from Editor import GetEditor
from YAMLExportGUI import YAMLExportGUI
from wxPyMail import SendMailWx
from XMLModule import getDiagramFromXMLSES
from StandaloneGUI import StandaloneGUI

### only for wx 2.9 (bug)
### http://comments.gmane.org/gmane.comp.python.wxpython/98744
wx.Log.SetLogLevel(0)

#-------------------------------------------------------------------
def getIcon(path):
	""" Return icon from image path.
	"""
	icon = wx.EmptyIcon() if wx.VERSION_STRING < '4.0' else wx.Icon()
	bmp = wx.Bitmap(path)
	bmp.SetMask(wx.Mask(bmp, wx.WHITE))
	icon.CopyFromBitmap(bmp)
	return icon

#-------------------------------------------------------------------
def DefineScreenSize(percentscreen = None, size = None):
	""" Returns a tuple to define the size of the window
		percentscreen = float
	"""
	if not size and not percentscreen:
		percentscreen = 0.8
	if size:
		l, h = size
	elif percentscreen:
		x1, x2, l, h = wx.Display().GetClientArea()
		l, h = percentscreen * l, percentscreen * h
	return round(l), round(h)

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

		wx.Frame.__init__(self, parent, wx.NewIdRef(), title, style = wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE)

		self.window = None
		self.otherWin = None
		self.replace = False
		self.stdioWin = None

		# icon setting
		self.icon = getIcon(os.path.join(ICON_PATH, DEVSIMPY_PNG))
		self.SetIcon(self.icon)

		# tell FrameManager to manage this frame
		self._mgr = aui.AuiManager()
		self._mgr.SetManagedWindow(self)

		# Prevent TreeCtrl from displaying all items after destruction when True
		self.dying = False

#		if 0:
#			# This is another way to set Accelerators, in addition to
#			# using the '\t<key>' syntax in the menu items.
#			aTable = wx.AcceleratorTable([(wx.ACCEL_ALT,  ord('X'), exitID), (wx.ACCEL_CTRL, ord('H'), helpID),(wx.ACCEL_CTRL, ord('F'), findID),(wx.ACCEL_NORMAL, WXK_F3, findnextID)])
#			self.SetAcceleratorTable(aTable)

		# for spash screen
		pub.sendMessage('object.added',  message=_('Loading the libraries tree...\n'))

		### for open home path
		self.home = None

		# NoteBook
		self.nb1 = ControlNotebook(self, wx.NewIdRef(), style = wx.CLIP_CHILDREN)
		self.tree = self.nb1.GetTree()

		pub.sendMessage('object.added',  message=_('Loading the search tab on libraries tree...\n'))
		self.searchTree = self.nb1.GetSearchTree()

		self._mgr.AddPane(self.nb1, aui.AuiPaneInfo().Name("nb1").Hide().Caption("Control").
                          FloatingSize(wx.Size(280, 400)).CloseButton(True).MaximizeButton(True))

		#------------------------------------------------------------------------------------------
		# Create a Notebook 2
		self.nb2 = DiagramNotebook(self, wx.NewIdRef(), style = wx.CLIP_CHILDREN)

		self.nb2.AddEditPage(_("Diagram%d"%Container.ShapeCanvas.ID))

		self._mgr.AddPane(self.nb2, aui.AuiPaneInfo().Name("nb2").CenterPane().Hide())

		# Simulation panel
		self.panel3 = wx.Panel(self.nb1, wx.NewIdRef(), style = wx.WANTS_CHARS)
		self.panel3.SetBackgroundColour(wx.NullColour)
		self.panel3.Hide()

		#status bar avant simulation :-)
		self.MakeStatusBar()

		# Shell panel
		self.panel4 = wx.Panel(self, wx.NewIdRef(), style=wx.WANTS_CHARS)
		sizer4 = wx.BoxSizer(wx.VERTICAL)
		sizer4.Add(py.crust.Crust(self.panel4, intro=_("Welcome to DEVSimPy: The GUI for Python DEVS Simulator")), 1, wx.EXPAND)
		self.panel4.SetSizer(sizer4)
		self.panel4.SetAutoLayout(True)

		self._mgr.AddPane(self.panel4, aui.AuiPaneInfo().Name("shell").Hide().Caption("Shell").
										FloatingSize(wx.Size(280, 400)).CloseButton(True).MaximizeButton(True))

		### Editor is panel
		self.editor = GetEditor(self, -1, file_type='block')

		self._mgr.AddPane(self.editor, aui.AuiPaneInfo().Name("editor").Hide().Caption(_("Editor")).
						FloatingSize(wx.Size(280, 400)).CloseButton(True).MaximizeButton(True))

		self._mgr.GetPane("nb1").Show().Left().Layer(0).Row(0).Position(0).BestSize(wx.Size(280,-1)).MinSize(wx.Size(250,-1))
		self._mgr.GetPane("nb2").Show().Center().Layer(0).Row(1).Position(0)
		self._mgr.GetPane("shell").Bottom().Layer(0).Row(0).Position(0).BestSize(wx.Size(-1,100)).MinSize(wx.Size(-1,120))
		self._mgr.GetPane("editor").Right().Layer(0).Row(0).Position(0).BestSize(wx.Size(280,-1)).MinSize(wx.Size(250,-1))

		# "commit" all changes made to FrameManager (warning always before the MakeMenu)
		self._mgr.Update()

		self.MakeMenu()
		self.MakeToolBar()

		self.Bind(aui.EVT_AUI_PANE_CLOSE, self.OnPaneClose)
		self.Bind(wx.EVT_TREE_BEGIN_DRAG, self.OnDragInit, id = self.tree.GetId())
		#self.Bind(wx.EVT_TREE_END_DRAG, self.OnDragEnd, id = self.tree.GetId())
		self.Bind(wx.EVT_TREE_BEGIN_DRAG, self.OnDragInit, id = self.searchTree.GetId())
		self.Bind(wx.EVT_IDLE, self.OnIdle)
		self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

		sys.stdout.write("DEVSimPy is ready!\n")

		### load last size and position if exist
		self.SetSize(DefineScreenSize() if not self.last_size else self.last_size)
		
		if self.last_position: 
			self.SetPosition(self.last_position)
		else:
			self.Centre(wx.BOTH)
		
		self.Show()

	def GetVersion(self):
		return __version__

	def GetMGR(self):
		return self._mgr

	def GetConfig(self):
		""" Reads the config file for the application if it exists and return a configfile object for use later.
		"""
		return wx.FileConfig(localFilename = os.path.join(GetUserConfigDir(),'.devsimpy'))

	def WriteDefaultConfigFile(self, cfg):
		""" Write config file.
		"""

		### for spash screen
		pub.sendMessage('object.added',  message=_('Writing .devsimpy settings file...\n'))

		sys.stdout.write("Writing default .devsimpy settings file on %s directory..."%GetUserConfigDir())

		self.exportPathsList = []					# export path list
		self.openFileList = ['']*NB_OPENED_FILE		# number of last opened files
		self.language = 'fr' if 'fr_FR' in locale.getdefaultlocale() else 'en' # default language
		self.perspectives = {}	# perpsective is void
		self.last_position = None
		self.last_size = None

		### verison of the main (fo compatibility of DEVSimPy)
		cfg.Write('version', str(__version__))
		### list des chemins des librairies à importer
		cfg.Write('exportPathsList', str([]))
		### list de l'unique domain par defaut: Basic
		cfg.Write('ChargedDomainList', str([]))
		### list des 5 derniers fichier ouvert
		cfg.Write('openFileList', str(eval("self.openFileList")))
		cfg.Write('language', "'%s'"%str(eval("self.language")))
		cfg.Write('active_plugins', str("[]"))
		cfg.Write('perspectives', str(eval("self.perspectives")))
		cfg.Write('builtin_dict', str(eval("builtins.__dict__")))
		cfg.Write('last_position', str(eval("self.last_position")))
		cfg.Write('last_size', str(eval("self.last_size")))

		sys.stdout.write("OK! \n")

	def SetConfig(self, cfg):
		""" Set all config entry like language, external importpath, recent files...
		"""

		self.cfg = cfg

		### if .devsimpy config file already exist, load it
		if self.cfg.Exists('version'):

			### rewrite old configuration file
			rewrite = float(self.cfg.Read("version")) != float(self.GetVersion())

			if not rewrite:

				### for spash screen
				pub.sendMessage('object.added',  message=_('Loading .devsimpy settings file...\n'))

				sys.stdout.write("Loading DEVSimPy %s settings file from %s.devsimpy\n"%(self.GetVersion(), GetUserConfigDir()+os.sep))

				### load external import path
				self.exportPathsList = [path for path in eval(self.cfg.Read("exportPathsList")) if os.path.isdir(path)]
				### append external path to the sys module to futur import
				sys.path.extend(self.exportPathsList)

				### load recent files list
				self.openFileList = eval(self.cfg.Read("openFileList"))
				### update chargedDomainList
				chargedDomainList = [path for path in eval(self.cfg.Read('ChargedDomainList')) if path.startswith('http') or os.path.isdir(path)]

				self.cfg.DeleteEntry('ChargedDomainList')
				self.cfg.Write('ChargedDomainList', str(eval('chargedDomainList')))
				### load language
				self.language = eval(self.cfg.Read("language"))

				### load perspective profile
				self.perspectives = eval(self.cfg.Read("perspectives"))

				### load last position and size
				try:
					self.last_position = eval(self.cfg.Read("last_position"))
					self.last_size = eval(self.cfg.Read("last_size"))
				except:
					self.last_position = None
					self.last_size = None
				else:
					### check if the screen size has not changed (dual screen)
					if self.last_position:
						l_saved,h_saved=self.last_position

						### if the position saved is superior of the screen
						l,h=DefineScreenSize()
						if l_saved>l or h_saved>h:
							self.last_position = None
							self.last_size = None

				### restore the builtin dict
				try:
					D = eval(self.cfg.Read("builtin_dict"))
				except SyntaxError:
					wx.MessageBox('Error trying to read the builtin dictionary from config file. So, we load the default builtin',
								'Configuration',
								wx.OK | wx.ICON_INFORMATION)
					#sys.stdout.write('Error trying to read the builtin dictionary from config file. So, we load the default builtin \n')
					D = builtin_dict
				else:
					### try to start without error when .devsimpy need update (new version installed)
					if not os.path.isdir(D['HOME_PATH']):
						wx.MessageBox('.devsimpy file appears to be not liked with the DEVSimPy code source. Please, delete this configuration from %s file and restart DEVSimPy. \n'%(GetUserConfigDir()),
									'Configuration',
									wx.OK | wx.ICON_INFORMATION)
						#sys.stdout.write('.devsimpy file appear to be not liked with the DEVSimPy source. Please, delete this configuration from %s file and restart DEVSimPy. \n'%(GetUserConfigDir()))
						D['HOME_PATH'] = ABS_HOME_PATH
					
					### if pypdevs_241 is detected, it is added in the builtin in order to be able to select him from the simulation Preference panel
					if builtin_dict['DEVS_DIR_PATH_DICT'] != D['DEVS_DIR_PATH_DICT']:
						D['DEVS_DIR_PATH_DICT'].update(builtin_dict['DEVS_DIR_PATH_DICT'])
						
				try:
					### recompile DomainInterface if DEFAULT_DEVS_DIRNAME != PyDEVS
					recompile = D['DEFAULT_DEVS_DIRNAME'] != builtins.__dict__['DEFAULT_DEVS_DIRNAME']
				except KeyError:
					recompile = False

				### test if the DEVSimPy source directory has been moved
				### if icon path exists, then we can update builtin from cfg
				if os.path.exists(D['ICON_PATH']):
					builtins.__dict__.update(D)
					### recompile DomainInterface
					if recompile:
						ReloadModule.recompile("DomainInterface.DomainBehavior")
						ReloadModule.recompile("DomainInterface.DomainStructure")
						ReloadModule.recompile("DomainInterface.MasterModel")
					
				### icon path is wrong (generally .devsimpy is wrong because DEVSimPy directory has been moved)
				### .devsimpy must be rewrite
				else:
					sys.stdout.write("It seems that DEVSimPy source directory has been moved.\n")
					self.WriteDefaultConfigFile(self.cfg)

				### load any plugins from the list
				### here because it needs to PLUGINS_PATH macro defined in D
				for plugin in eval(self.cfg.Read("active_plugins")):
					PluginManager.load_plugins(plugin)
					PluginManager.enable_plugin(plugin)
			else:
				wx.MessageBox('.devsimpy file appear to be a very old version and should be updated....\nWe rewrite a new blank version.',
									'Configuration',
									wx.OK | wx.ICON_INFORMATION)
				self.WriteDefaultConfigFile(self.cfg)

		### create a new defaut .devsimpy config file
		else:
			self.WriteDefaultConfigFile(self.cfg)

		###sys.stdout.write("Loading DEVSimPy...\n")

	def Seti18n(self):
		""" Set local setting.
		"""

		# for spash screen
		pub.sendMessage('object.added',  message=_('Loading locale configuration...\n'))

		localedir = os.path.join(HOME_PATH, "locale")
		langid = wx.LANGUAGE_FRENCH if self.language == 'fr' else wx.LANGUAGE_ENGLISH    # use OS default; or use LANGUAGE_FRENCH, etc.
		domain = "DEVSimPy"             # the translation file is messages.mo

		# Set locale for wxWidgets
		self.locale = wx.Locale()
		self.locale.Init(langid)
		self.locale.AddCatalogLookupPathPrefix(localedir)
		self.locale.AddCatalog(domain)
	
		# language config from .devsimpy file
		if self.language in ('en','fr'):
			try:
				locale.setlocale(locale.LC_ALL, self.language)
			except:
				sys.stdout.write(_('new local (since wx 4.1.0) setting not applied'))
			translation = gettext.translation(domain, localedir, languages=[self.language]) 
		else:
			try:
				locale.setlocale(locale.LC_ALL, '')
			except:
				sys.stdout.write(_('new local (since wx 4.1.0) setting not applied'))
			#installing os language by default
			translation = gettext.translation(domain, localedir, [self.locale.GetCanonicalName()], fallback = True)

		translation.install()

	def MakeStatusBar(self):
		""" Make status bar.
		"""

		# for spash screen
		pub.sendMessage('object.added',  message=_('Making status bar...\n'))

		self.statusbar = self.CreateStatusBar(1, wx.ST_SIZEGRIP if wx.VERSION_STRING < '4.0' else wx.STB_SIZEGRIP)
		self.statusbar.SetFieldsCount(3)
		self.statusbar.SetStatusWidths([-2, -5, -1])

	def MakeMenu(self):
		""" Make main menu.
		"""

		# for spash screen
		pub.sendMessage('object.added',  message=_('Making Menu ...\n'))

		self.menuBar = Menu.MainMenuBar(self)
		self.SetMenuBar(self.menuBar)

		### commented before Phoenix transition 
		### bind menu that require update on open and close event (forced to implement the binding here !)
		for menu,title in [c for c in self.menuBar.GetMenus() if re.search("(File|Fichier|Options)", c[-1]) != None]:
			self.Bind(wx.EVT_MENU_OPEN, self.menuBar.OnOpenMenu)
			#self.Bind(wx.EVT_MENU_CLOSE, self.menuBar.OnCloseMenu)

	def MakeToolBar(self):
		""" Make main tools bar.
		"""

		# for spash screen
		pub.sendMessage('object.added',  message=_('Making tools bar ...\n'))
		
		tb = wx.ToolBar(self, wx.NewIdRef(), name='tb', style=wx.TB_HORIZONTAL | wx.NO_BORDER)
		tb.SetToolBitmapSize((16,16))

		self.toggle_list = [wx.NewIdRef(), wx.NewIdRef(), wx.NewIdRef(), wx.NewIdRef(), wx.NewIdRef(), wx.NewIdRef()]

		currentPage = self.nb2.GetCurrentPage()

		### Tools List - IDs come from Menu.py file
		if wx.VERSION_STRING < '4.0':
			self.tools = [	tb.AddTool(wx.ID_NEW, wx.Bitmap(os.path.join(ICON_PATH,'new.png')), shortHelpString=_('New diagram (Ctrl+N)'),longHelpString=_('Create a new diagram in tab')),
							tb.AddTool(wx.ID_OPEN, wx.Bitmap(os.path.join(ICON_PATH,'open.png')), shortHelpString=_('Open File (Ctrl+O)'), longHelpString=_('Open an existing diagram')),
							tb.AddTool(wx.ID_PREVIEW_PRINT, wx.Bitmap(os.path.join(ICON_PATH,'print-preview.png')), shortHelpString=_('Print Preview (Ctrl+P)'), longHelpString=_('Print preview of current diagram')),
							tb.AddTool(wx.ID_SAVE, wx.Bitmap(os.path.join(ICON_PATH,'save.png')), shortHelpString=_('Save File (Ctrl+S)'), longHelpString=_('Save the current diagram'), clientData=currentPage),
							tb.AddTool(wx.ID_SAVEAS, wx.Bitmap(os.path.join(ICON_PATH,'save_as.png')), shortHelpString=_('Save file as'), longHelpString=_('Save the diagram with an another name'), clientData=currentPage),
							tb.AddTool(wx.ID_UNDO, wx.Bitmap(os.path.join(ICON_PATH,'undo.png')),shortHelpString= _('Undo'), longHelpString=_('Click to go upward, hold to see history'), clientData=currentPage),
							tb.AddTool(wx.ID_REDO, wx.Bitmap(os.path.join(ICON_PATH,'redo.png')), shortHelpString=_('Redo'), longHelpString=_('Click to go forward, hold to see history'), clientData=currentPage),
							tb.AddTool(Menu.ID_ZOOMIN_DIAGRAM, wx.Bitmap(os.path.join(ICON_PATH,'zoom+.png')), shortHelpString=_('Zoom'), longHelpString=_('Zoom +'), clientData=currentPage),
							tb.AddTool(Menu.ID_ZOOMOUT_DIAGRAM, wx.Bitmap(os.path.join(ICON_PATH,'zoom-.png')), shortHelpString=_('UnZoom'), longHelpString=_('Zoom -'), clientData=currentPage),
							tb.AddTool(Menu.ID_UNZOOM_DIAGRAM, wx.Bitmap(os.path.join(ICON_PATH,'no_zoom.png')), shortHelpString=_('AnnuleZoom'), longHelpString=_('Normal size'), clientData=currentPage),
							tb.AddTool(Menu.ID_PRIORITY_DIAGRAM, wx.Bitmap(os.path.join(ICON_PATH,'priority.png')), shortHelpString=_('Priority (F3)'),longHelpString= _('Define model activation priority')),
							tb.AddTool(Menu.ID_CHECK_DIAGRAM, wx.Bitmap(os.path.join(ICON_PATH,'check_master.png')), shortHelpString=_('Debugger (F4)'),longHelpString= _('Check devs models')),
							tb.AddTool(Menu.ID_PLUGINS_SHAPE, wx.Bitmap(os.path.join(ICON_PATH,'plugins.png')), shortHelpString=_('Plugins'), longHelpString=_('Plugins Manager')),
							tb.AddTool(Menu.ID_SIM_DIAGRAM, wx.Bitmap(os.path.join(ICON_PATH,'simulation.png')), shortHelpString=_('Simulation (F5)'), longHelpString=_('Simulate the diagram')),
							tb.AddTool(self.toggle_list[0], wx.Bitmap(os.path.join(ICON_PATH,'direct_connector.png')),shortHelpString= _('Direct'),longHelpString=_('Direct connector'), isToggle=True),
							tb.AddTool(self.toggle_list[1], wx.Bitmap(os.path.join(ICON_PATH,'square_connector.png')), shortHelpString=_('Square'), longHelpString=_('Square connector'), isToggle=True),
							tb.AddTool(self.toggle_list[2], wx.Bitmap(os.path.join(ICON_PATH,'linear_connector.png')), shortHelpString=_('Linear'), longHelpString=_('Linear connector'), isToggle=True)
						]
		else:
			self.tools = [	tb.AddTool(wx.ID_NEW, "",wx.Bitmap(os.path.join(ICON_PATH,'new.png')), shortHelp=_('New diagram (Ctrl+N)')),
							tb.AddTool(wx.ID_OPEN, "",wx.Bitmap(os.path.join(ICON_PATH,'open.png')), shortHelp=_('Open File (Ctrl+O)')),
							tb.AddTool(wx.ID_PREVIEW_PRINT, "",wx.Bitmap(os.path.join(ICON_PATH,'print-preview.png')), shortHelp=_('Print Preview (Ctrl+P)')),
							tb.AddTool(wx.ID_SAVE, "",wx.Bitmap(os.path.join(ICON_PATH,'save.png')), wx.NullBitmap, shortHelp=_('Save File (Ctrl+S)'), longHelp=_('Save the current diagram'), clientData=currentPage),
							tb.AddTool(wx.ID_SAVEAS, "",wx.Bitmap(os.path.join(ICON_PATH,'save_as.png')), wx.NullBitmap, shortHelp=_('Save file as'), longHelp=_('Save the diagram with an another name'), clientData=currentPage),
							tb.AddTool(wx.ID_UNDO, "",wx.Bitmap(os.path.join(ICON_PATH,'undo.png')), wx.NullBitmap, shortHelp= _('Undo'), longHelp=_('Click to glongHelpString=o back, hold to see history'), clientData=currentPage),
							tb.AddTool(wx.ID_REDO, "",wx.Bitmap(os.path.join(ICON_PATH,'redo.png')), wx.NullBitmap, shortHelp=_('Redo'), longHelp=_('Click to go forward, hold to see history'), clientData=currentPage),
							tb.AddTool(Menu.ID_ZOOMIN_DIAGRAM, "",wx.Bitmap(os.path.join(ICON_PATH,'zoom+.png')), wx.NullBitmap, shortHelp=_('Zoom'), longHelp=_('Zoom +'), clientData=currentPage),
							tb.AddTool(Menu.ID_ZOOMOUT_DIAGRAM, "",wx.Bitmap(os.path.join(ICON_PATH,'zoom-.png')), wx.NullBitmap, shortHelp=_('UnZoom'), longHelp=_('Zoom -'), clientData=currentPage),
							tb.AddTool(Menu.ID_UNZOOM_DIAGRAM, "",wx.Bitmap(os.path.join(ICON_PATH,'no_zoom.png')), wx.NullBitmap, shortHelp=_('AnnuleZoom'), longHelp=_('Normal size'), clientData=currentPage),
							tb.AddTool(Menu.ID_PRIORITY_DIAGRAM, "",wx.Bitmap(os.path.join(ICON_PATH,'priority.png')), shortHelp=_('Priority (F3)')),
							tb.AddTool(Menu.ID_CHECK_DIAGRAM, "",wx.Bitmap(os.path.join(ICON_PATH,'check_master.png')), shortHelp=_('Debugger (F4)')),
							tb.AddTool(Menu.ID_PLUGINS_SHAPE, "", wx.Bitmap(os.path.join(ICON_PATH,'plugins.png')), shortHelp=_('Plugins Manager')),
							tb.AddTool(Menu.ID_SIM_DIAGRAM, "",wx.Bitmap(os.path.join(ICON_PATH,'simulation.png')), shortHelp=_('Simulation (F5)')),
							tb.AddTool(self.toggle_list[0], "",wx.Bitmap(os.path.join(ICON_PATH,'direct_connector.png')),shortHelp= _('Direct'), kind=wx.ITEM_CHECK),
							tb.AddTool(self.toggle_list[1], "",wx.Bitmap(os.path.join(ICON_PATH,'square_connector.png')), shortHelp=_('Square'), kind = wx.ITEM_CHECK),
							tb.AddTool(self.toggle_list[2], "",wx.Bitmap(os.path.join(ICON_PATH,'linear_connector.png')), shortHelp=_('Linear'), kind = wx.ITEM_CHECK)
						]

		##################################################################### Abstraction hierarchy
		diagram = currentPage.GetDiagram()
		level = currentPage.GetCurrentLevel()

		level_label = wx.StaticText(tb, -1, _("Level "))
		self.spin = wx.SpinCtrl(tb, self.toggle_list[3], str(level), pos=(55, 90), size=(50, -1), min=0, max=20)

		tb.AddControl(level_label)
		tb.AddControl(self.spin)

		### add button to define downward and upward rules
		ID_UPWARD = self.toggle_list[4]
		ID_DOWNWARD = self.toggle_list[5]

		if wx.VERSION_STRING < '4.0':
			self.tools.append(tb.AddTool(ID_DOWNWARD, wx.Bitmap(os.path.join(ICON_PATH,'downward.png')), shortHelpString=_('Downward rules'), longHelpString=_('Define Downward atomic model')))
			self.tools.append(tb.AddTool(ID_UPWARD, wx.Bitmap(os.path.join(ICON_PATH,'upward.png')), shortHelpString=_('Upward rules'), longHelpString=_('Define Upward atomic model')))
		else:
			self.tools.append(tb.AddTool(ID_DOWNWARD, "", wx.Bitmap(os.path.join(ICON_PATH,'downward.png')), shortHelp=_('Downward rules')))
			self.tools.append(tb.AddTool(ID_UPWARD, "", wx.Bitmap(os.path.join(ICON_PATH,'upward.png')), shortHelp=_('Upward rules')))

		tb.EnableTool(ID_DOWNWARD, False)
		tb.EnableTool(ID_UPWARD, False)

		##############################################################################################

		for i in (3,8,12,17,21):
			tb.InsertSeparator(i)
		
		### undo and redo button desabled
		tb.EnableTool(wx.ID_UNDO, False)
		tb.EnableTool(wx.ID_REDO, False)
	
		tb.EnableTool(Menu.ID_PRIORITY_DIAGRAM, not 'PyPDEVS' in builtins.__dict__['DEFAULT_DEVS_DIRNAME'])

		### default direct connector toogled
		tb.ToggleTool(self.toggle_list[0], 1)

		### Binding
		self.Bind(wx.EVT_TOOL, self.OnNew, self.tools[0])
		self.Bind(wx.EVT_TOOL, self.OnOpenFile, self.tools[1])
		self.Bind(wx.EVT_TOOL, self.OnPrintPreview, self.tools[2])
		self.Bind(wx.EVT_TOOL, self.OnSaveFile, self.tools[3])
		self.Bind(wx.EVT_TOOL, self.OnSaveAsFile, self.tools[4])
		self.Bind(wx.EVT_TOOL, self.OnUndo, self.tools[5])
		self.Bind(wx.EVT_TOOL, self.OnRedo, self.tools[6])
		self.Bind(wx.EVT_TOOL, self.OnZoom, self.tools[7])
		self.Bind(wx.EVT_TOOL, self.OnUnZoom, self.tools[8])
		self.Bind(wx.EVT_TOOL, self.AnnuleZoom, self.tools[9])
		self.Bind(wx.EVT_TOOL, self.OnPriorityGUI, self.tools[10])
		self.Bind(wx.EVT_TOOL, self.OnCheck, self.tools[11])
		self.Bind(wx.EVT_TOOL, self.OnPlugins, self.tools[12])
		self.Bind(wx.EVT_TOOL, self.OnSimulation, self.tools[13])
		self.Bind(wx.EVT_TOOL, self.OnDirectConnector, self.tools[14])
		self.Bind(wx.EVT_TOOL, self.OnSquareConnector, self.tools[15])
		self.Bind(wx.EVT_TOOL, self.OnLinearConnector, self.tools[16])

		##################################################################### Abstraction hierarchy
		self.Bind(wx.EVT_SPINCTRL, self.OnSpin, id=self.toggle_list[3])
		self.Bind(wx.EVT_TEXT, self.OnSpin, id=self.toggle_list[3])
		##############################################################################################

		self.Bind(wx.EVT_TOOL, self.OnUpWard, id=ID_UPWARD)
		self.Bind(wx.EVT_TOOL, self.OnDownWard, id=ID_DOWNWARD)

		tb.Realize()

		self.SetToolBar(tb)

	def GetExportPathsList(self):
		""" Return the list of exported path.
		"""
		return self.exportPathsList

	def GetDiagramNotebook(self):
		""" Return diagram notbook (right)
		"""
		return self.nb2

	def GetControlNotebook(self):
		""" Return control notebook (left)
		"""
		return self.nb1

	def GetEditorPanel(self):
		""" Return editor panel (rigth)
		"""
		return self.editor

	def OnDirectConnector(self, event):
		"""
		"""
		toolbar = event.GetEventObject()
		for id in self.toggle_list:
			toolbar.ToggleTool(id,0)
		toolbar.ToggleTool(event.GetId(),1)

		canvas = Container.ShapeCanvas
		canvas.CONNECTOR_TYPE = 'direct'
		#canvas.OnRefreshModel(canvas, event)

	def OnSquareConnector(self, event):
		"""
		"""
		self.OnDirectConnector(event)
		canvas = Container.ShapeCanvas
		canvas.CONNECTOR_TYPE = 'square'


	def OnLinearConnector(self, event):
		"""
		"""

		self.OnDirectConnector(event)
		canvas = Container.ShapeCanvas
		canvas.CONNECTOR_TYPE = 'linear'

	def OnPaneClose(self, event):
		""" Close pane has been invoked.
		"""
		caption = event.GetPane().caption

		if caption in ["Control", 'Editor', 'Shell']:
			msg = _("You realy want to close this pane?")
			dlg = wx.MessageDialog(self, msg, _("Question"),
									wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)

			if dlg.ShowModal() in [wx.ID_NO, wx.ID_CANCEL]:
				event.Veto()
			else:

				menuItemList = []
				menu = self.GetMenuBar().GetMenu(2)

				if caption == 'Shell':
					menuItemList.append(menu.FindItemById(Menu.ID_SHOW_SHELL))
				elif caption == 'Editor':
					menuItemList.append(menu.FindItemById(Menu.ID_SHOW_EDITOR))
				else:
					menuItemList.append(menu.FindItemById(Menu.ID_SHOW_LIB))
					menuItemList.append(menu.FindItemById(Menu.ID_SHOW_PROP))
					menuItemList.append(menu.FindItemById(Menu.ID_SHOW_SIM))

				for menu_item in menuItemList:
					getattr(menu_item, 'Check')(False)

			dlg.Destroy()

	###
	def OnOpenRecentFile(self, event):
		""" Recent file has been invoked.
		"""

		id = event.GetId()
	
		#menu=event.GetEventObject()
		##on Linux, event.GetEventObject() returns a reference to the menu item,
		##while on Windows, event.GetEventObject() returns a reference to the main frame.
					
		### before Phoenix transition
		#menu = self.GetMenuBar().FindItemById(id).GetMenu()
		#menuItem = menu.FindItemById(id)
		
		### after Phoenix transition
		menu = self.GetMenuBar().FindItemById(Menu.ID_RECENT).GetMenu()
		menuItem = menu.FindItemById(id)
		path = menuItem.GetItemLabel()

		if path.endswith(('.dsp','.yaml')):
			name = os.path.basename(path)
		
			diagram = Container.Diagram()
			#diagram.last_name_saved = path
			open_file_result = diagram.LoadFile(path)

			if isinstance(open_file_result, Exception):
				wx.MessageBox(_('Error opening file.\nInfo : %s')%str(open_file_result), _('Error'), wx.OK | wx.ICON_ERROR)
			else:
				self.nb2.AddEditPage(os.path.splitext(name)[0], diagram)

			self.EnableAbstractionButton()

	def EnableAbstractionButton(self):
		""" Enable DAM and UAM button depending of the abstraction level
		"""
		### update text filed
		level = self.spin.GetValue()

		### update doward and upward button
		tb = self.GetToolBar()
		flag = level != 0
		tb.EnableTool(self.toggle_list[4], flag)
		tb.EnableTool(self.toggle_list[5], flag)

	def OnDeleteRecentFiles(self, event):
		""" Delete the recent files list
		"""
	
		# update openFileList variable
		self.openFileList = ['']*NB_OPENED_FILE
		
		# update config file
		self.cfg.Write("openFileList", str(eval("self.openFileList")))
		self.cfg.Flush()
		
	def OnCreatePerspective(self, event):
		"""
		"""

		dlg = wx.TextEntryDialog(self, _("Enter a new perspective:"), _("Perspective Manager"), _("Perspective %d")%(len(self.perspectives)))
		if dlg.ShowModal() == wx.ID_OK:
			txt = dlg.GetValue()

			if len(self.perspectives) == 0:
				self.perspectivesmenu.AppendSeparator()

			ID = wx.NewIdRef()
			self.perspectivesmenu.Append(ID, txt)
			self.perspectives[txt] = self._mgr.SavePerspective()

			### Disable the delete function
			self.perspectivesmenu.FindItemById(Menu.ID_DELETE_PERSPECTIVE).Enable(True)
		
			### Bind right away to make activable the perspective without restart DEVSimPy
			self.Bind(wx.EVT_MENU, self.OnRestorePerspective, id=ID)

			NotificationMessage(_('Information'), _('%s has been added!')%txt, parent=self, timeout=5)

		dlg.Destroy()

	def OnRestorePerspective(self, event):
		"""
		"""
		
		id = event.GetId()
		item = self.GetMenuBar().FindItemById(id)
		mgr = self.GetMGR()
		mgr.LoadPerspective(self.perspectives[item.GetItemLabelText()])

	def OnDeletePerspective(self, event):
		"""
		"""
		
		# delete all path items
		L = list(self.perspectivesmenu.GetMenuItems())
		for item in L[4:]:
			self.perspectivesmenu.Remove(item)

		# update config file
		self.perspectives = {_("Default Startup"):self._mgr.SavePerspective()}
		self.cfg.Write("perspectives", str(eval("self.perspectives")))
		self.cfg.Flush()

		### Disable the delete function
		self.perspectivesmenu.FindItemById(Menu.ID_DELETE_PERSPECTIVE).Enable(False)

		NotificationMessage(_('Information'), _('All perspectives have been deleted!'), parent=self, timeout=5)

	###
	def OnDragInit(self, event):
		"""
		"""

		# version avec arbre
		item = event.GetItem()
		tree = event.GetEventObject()

		### in posix-based we drag only item (in window is automatic)
		platform_sys = os.name
		flag = True
		if platform_sys == 'posix':
			flag = tree.IsSelected(item)

		# Dnd uniquement sur les derniers fils de l'arbre
		if not tree.ItemHasChildren(item) and flag:
			text = tree.GetItemPyData(event.GetItem()) if wx.VERSION_STRING < '4.0' else tree.GetItemData(event.GetItem())
			try:
				tdo = wx.PyTextDataObject(text) if wx.VERSION_STRING < '4.0' else wx.TextDataObject(text)
				#tdo = wx.TextDataObject(text)
				tds = wx.DropSource(tree)
				tds.SetData(tdo)
				tds.DoDragDrop(True)
			except:
				sys.stderr.write(_("OnDragInit avorting \n"))

	###
	def OnIdle(self, event):
		"""
		"""

		if self.otherWin:
			self.otherWin.Raise()
			self.otherWin = None

	###
	def SaveLibraryProfile(self):
		""" Update config file with the librairies opened during the last use of DEVSimPy.
		"""
		
		### Show is in position 2 on Menu Bar
		show_menu = self.menuBar.GetMenu(2)
		### Control is in position 1
		control_item = show_menu.FindItemByPosition(0)
		### Libraries is in position 2
		libraries_item = control_item.GetSubMenu().FindItemByPosition(2)

		### if Libraries tab is not visible in DEVSimPy (in nb1), don't save the configuration of libraries
		if libraries_item.IsChecked():
			# save in config file the opened last library directory
			L = self.tree.GetItemChildren(self.tree.root)
			self.cfg.Write("ChargedDomainList", str([k for k in self.tree.ItemDico if self.tree.ItemDico[k] in L]))
			self.cfg.Flush()

	def SavePerspectiveProfile(self):
		""" Update the config file with the profile that are enabled during the last use of DEVSimPy
		"""
		# save in config file the last activated perspective
		self.cfg.Write("perspectives", str(self.perspectives))
		self.cfg.Flush()

	def SaveBuiltinDict(self):
		""" Save the specific builtin variable into the config file
		"""
		self.cfg.Write("builtin_dict", str(eval('dict((k, builtins.__dict__[k]) for k in builtin_dict)')))
		self.cfg.Flush()

	def SavePosition(self):
		self.cfg.Write("last_position", str(self.GetPosition()))
		self.cfg.Flush()

	def SaveSize(self):
		self.cfg.Write("last_size", str(self.GetSize()))
		self.cfg.Flush()

	###
	def OnCloseWindow(self, event):
		""" Close icon has been pressed. Closing DEVSimPy.
		"""

		exit = False
		### for all pages, we invoke their OnClosePage function
		for i in range(self.nb2.GetPageCount()):

			try:
				### select the first page
				self.nb2.SetSelection(0)
			except:
				pass
			if not self.nb2.OnClosePage(event):
				exit = True
				break

		if not exit:
			### Save process
			self.SaveLibraryProfile()
			self.SavePerspectiveProfile()
			self.SaveBuiltinDict()
			self.SavePosition()
			self.SaveSize()
			self._mgr.UnInit()
			del self._mgr
			#self.Close()
			
			#win = wx.Window_FindFocus()
			#if win != None:
				## Note: you really have to use wx.wxEVT_KILL_FOCUS
				## instead of wx.EVT_KILL_FOCUS here:
				#win.Disconnect(-1, -1, wx.wxEVT_KILL_FOCUS)
			#self.Destroy()

		event.Skip()

	def OnSpin(self, event):
		""" Spin button has been invoked (on the toolbar of the main windows or detached frame).
		"""

		### spin control object
		spin = event.GetEventObject()

		### get toolbar dynamically from frame
		tb = spin.GetParent()

		### main frame of spin control
		frame = tb.GetTopLevelParent()

		is_detached_frame = isinstance(frame, DetachedFrame)
		parent_frame_is_canvas = isinstance(frame.GetParent(), Container.ShapeCanvas)

		### update text filed
		level = spin.GetValue()

		### update doward and upward button
		tb.EnableTool(self.toggle_list[4], level != 0)
		tb.EnableTool(self.toggle_list[5], level != 0)

		### list of spin control to update
		L = [tb]
		### if spin control coming from DetachedFrame of notebooktab
		if parent_frame_is_canvas:
			L.append(self.GetToolBar())

		### text control object from its unique id
		for obj in L:
			s = obj.FindControl(self.toggle_list[3])
			if s:
				s.SetValue(level)

		### update diagram
		### currentPage is given by the client data embeded in the save item on tool bar (which is the same of spin ;-))
		if is_detached_frame and parent_frame_is_canvas:
			L = [tb.GetToolClientData(wx.ID_SAVE), self.nb2.GetCurrentPage()]
		else:
			if is_detached_frame:
				L = [tb.GetToolClientData(wx.ID_SAVE)]
			else:
				L = [self.nb2.GetCurrentPage()]

		for canvas in L:
			canvas.LoadDiagram(level)

	################################################################################ Abstraction hierarchy
	###
	def OnUpWard(self, event):
		"""
		"""

		### toolbar object
		tb = event.GetEventObject()

		### main frame of spin control
		frame = tb.GetTopLevelParent()

		is_detached_frame = isinstance(frame, DetachedFrame)

		### canvas
		if is_detached_frame:
			canvas = tb.GetToolClientData(wx.ID_SAVE)
		else:
			canvas = self.nb2.GetCurrentPage()

		### diagram
		dia = canvas.GetDiagram()

		### current level
		cl =  dia.current_level

		### Editor frame
		frame = GetEditor(canvas, -1, 'UAM%d'%cl)
		frame.AddEditPage('UAM%d'%cl, canvas.UAM[cl])
		frame.SetPosition((100, 100))
		frame.Show()

	###
	def OnDownWard(self, event):
		"""
		"""

				### toolbar object
		tb = event.GetEventObject()

		### main frame of spin control
		frame = tb.GetTopLevelParent()

		is_detached_frame = isinstance(frame, DetachedFrame)

		### canvas
		if is_detached_frame:
			canvas = tb.GetToolClientData(wx.ID_SAVE)
		else:
			canvas = self.nb2.GetCurrentPage()

		### diagram
		dia = canvas.GetDiagram()

		### current level
		cl =  dia.current_level

		### Editor frame
		frame = GetEditor(canvas, -1, 'DAM%d'%cl)
		frame.AddEditPage('DAM%d'%cl, canvas.DAM[cl])
		frame.SetPosition((100, 100))
		frame.Show()

	########################################################################################

	###
	def OnZoom(self, event):
		""" Zoom in icon has been pressed. Zoom in the current diagram.
		"""
		obj = event.GetEventObject()

		if isinstance(obj, wx.ToolBar):
			currentPage = obj.GetToolClientData(event.GetId()) if isinstance(obj.GetTopLevelParent(), DetachedFrame) else self.nb2.GetCurrentPage()
		else:
			currentPage = self.nb2.GetCurrentPage()

		currentPage.scalex=max(currentPage.scalex+.05,.3)
		currentPage.scaley=max(currentPage.scaley+.05,.3)
		currentPage.Refresh()

		self.statusbar.SetStatusText(_('Zoom In'))

	###
	def OnUnZoom(self, event):
		""" Zoom out icon has been pressed. Zoom out the current diagram.
		"""
		obj = event.GetEventObject()

		if isinstance(obj, wx.ToolBar):
			currentPage = obj.GetToolClientData(event.GetId()) if isinstance(obj.GetTopLevelParent(), DetachedFrame) else self.nb2.GetCurrentPage()
		else:
			currentPage = self.nb2.GetCurrentPage()

		currentPage.scalex=currentPage.scalex-.05
		currentPage.scaley=currentPage.scaley-.05
		currentPage.Refresh()

		self.statusbar.SetStatusText(_('Zoom Out'))

	###
	def AnnuleZoom(self, event):
		"""
		"""
		obj = event.GetEventObject()

		if isinstance(obj, wx.ToolBar):
			currentPage = obj.GetToolClientData(event.GetId()) if isinstance(obj.GetTopLevelParent(), DetachedFrame) else self.nb2.GetCurrentPage()
		else:
			currentPage = self.nb2.GetCurrentPage()

		currentPage.scalex = 1.0
		currentPage.scaley = 1.0
		currentPage.Refresh()

		self.statusbar.SetStatusText(_('No Zoom'))

	###
	def OnNew(self, event):
		""" New diagram has been invocked.
		"""
		self.nb2.AddEditPage("Diagram%d"%Container.ShapeCanvas.ID)
		return self.nb2.GetCurrentPage()

	###
	def OnOpenFile(self, event):
		""" Open file button has been pressed.
		"""

		wcd = _("DEVSimPy files (*.dsp)|*.dsp|YAML files (*.yaml)|*.yaml|All files (*)|*")
		home = self.home or os.getenv('USERPROFILE') or os.getenv('HOME') or HOME_PATH if self.openFileList == ['']*NB_OPENED_FILE else self.home or os.path.dirname(self.openFileList[0])
		
		open_dlg = wx.FileDialog(self, message = _('Choose a file'), defaultDir = home, defaultFile = "", wildcard = wcd, style = wx.OPEN|wx.MULTIPLE|wx.CHANGE_DIR)

		### path,diagram dictionary
		new_paths = {}

		# get the new path from open file dialogue
		if open_dlg.ShowModal() == wx.ID_OK:

			### for selected paths
			for path in [p  for p in open_dlg.GetPaths() if p.endswith(('.dsp','.yaml'))]:
				diagram = Container.Diagram()
				#diagram.last_name_saved = path

				### adding path with assocaited diagram
				new_paths[os.path.normpath(path)] = diagram

				self.home = os.path.dirname(path)

			open_dlg.Destroy()

		# load the new_path file with ConnectionThread function
		if new_paths != {}:

			for path,diagram in list(new_paths.items()):

				fileName = os.path.basename(path)
				open_file_result = diagram.LoadFile(path)

				if isinstance(open_file_result, Exception):
					type, value, traceback = sys.exc_info()
					if value:
						wx.MessageBox(_('Error opening %s: %s')%(value.filename, value.strerror), 'Error', wx.OK | wx.ICON_ERROR)
					else:	
						sys.stdout.write(_('Error opening %s')%(fileName))
				else:
					self.nb2.AddEditPage(os.path.splitext(fileName)[0], diagram)

					# ajout dans la liste des derniers fichiers ouverts (avec gestion de la suppression du dernier inseré)
					if path not in self.openFileList:
						self.openFileList.insert(0, path)
						del self.openFileList[-1]
						self.cfg.Write("openFileList", str(eval("self.openFileList")))
						self.cfg.Flush()

			self.EnableAbstractionButton()

	###
	def OnPrint(self, event):
		""" Print current diagram.
		"""
		self.nb2.print_canvas = self.nb2.GetCurrentPage()
		self.nb2.print_size = self.nb2.GetSize()

		if self.nb2.PrintButton(event):
			NotificationMessage(_('Information'), _('Print has been well done'), parent=self, timeout=5)
		else:
			NotificationMessage(_('Error'), _('Print not possible!\n Check the trace in background for more informations.'), parent=self, flag=wx.ICON_ERROR, timeout=5)
	
	###
	def OnPrintPreview(self, event):
		""" Print preview of current diagram.
		"""
		self.nb2.print_canvas = self.nb2.GetCurrentPage()
		self.nb2.print_size = self.nb2.GetSize()
	
		if self.nb2.PrintPreview(event):
			NotificationMessage(_('Information'), _('Print has been well done'), parent=self, timeout=5)
		else:
			NotificationMessage(_('Error'), _('Print not possible!\n Check the trace in background for more informations.'), parent=self, flag=wx.ICON_ERROR, timeout=5)
	###

	###
	def OnScreenCapture(self, event):
		""" Print preview of current diagram.
		"""

		### gi is in the pyobject package
		try:
			import gi
			package_installed = True
		except ImportError:
			package = "pygobject"
			package_installed = install(package)
			
		if package_installed:
			import gi
			gi.require_version("Gdk", "3.0")
			import gi.repository.Gdk as gdk

			currentPage = self.nb2.GetCurrentPage()
			currentPage.deselect()
			diagram = currentPage.GetDiagram()
			
			last_name_saved = getattr(diagram,'last_name_saved', os.path.join(HOME_PATH, 'screenshot.png'))
			
			### options building
			wcd = _("PNG files (*.png)|*.png|All files (*)|*)")
			home = self.home or os.path.dirname(last_name_saved) or HOME_PATH if self.openFileList == ['']*NB_OPENED_FILE else self.home or os.path.dirname(self.openFileList[0])
			save_dlg = wx.FileDialog(self, message=_('Save file as...'), defaultDir=home, defaultFile=os.path.basename(last_name_saved), wildcard=wcd, style=wx.SAVE | wx.OVERWRITE_PROMPT)

			if save_dlg.ShowModal() == wx.ID_OK:
				save_dlg.Destroy()
				
				### wait to avoid the message box that appear when a png already existe and ask to replace it !
				time.sleep(2)

				### screenshot for the whole window w
				w = gdk.get_default_root_window()
				pb = gdk.pixbuf_get_from_window(w, 0,0, w.get_width(), w.get_height())
				### saving
				if (pb != None):
					path = os.path.normpath(save_dlg.GetPath())
					ext = os.path.splitext(path)[-1][1:]
					pb.savev(path, ext,  ["quality"], ["100"])

					NotificationMessage(_('Information'), _("Screenshot saved in %s.")%path, parent=self, timeout=5)
				else:
					NotificationMessage(_('Error'), _("Unable to get the screenshot. \n Check the trace in background for more informations."), parent=self, flag=wx.ICON_ERROR, timeout=5)
		else:
			NotificationMessage(_('Error'), _('%s is not installed. \n Check the trace in background for more informations.'%(package)), parent=self, flag=wx.ICON_ERROR, timeout=5)

	###
	def OnUndo(self, event):
		""" Undo the diagram.
		"""
		### get toolbar and clientData defined in AddTool
		toolbar = event.GetEventObject()
		currentPage = toolbar.GetToolClientData(event.GetId()) if isinstance(toolbar.GetParent(), DetachedFrame) else self.nb2.GetCurrentPage()

		### append the stockredo and active it
		currentPage.stockRedo.append(pickle.dumps(obj=currentPage.GetDiagram(),protocol=0))
		toolbar.EnableTool(wx.ID_REDO, True)

		### change the current diagram with the last undo
		new_diagram = pickle.loads(currentPage.stockUndo.pop())
		new_diagram.parent = currentPage
		currentPage.DiagramReplace(new_diagram)
		original_diagram = currentPage.GetDiagram()

		## if model is containerBlock, the grand parent is DetachedFrame and we could update the diagram withou update the original canvas
		if isinstance(original_diagram.GetGrandParent(), DetachedFrame):
			## update of all shapes in the original diagram
			original_diagram.shapes = new_diagram.shapes
		else:
			## refresh original canvas with new diagram
			original_canvas = original_diagram.parent
			original_canvas.DiagramReplace(new_diagram)

		### desable undo btn if the stockUndo list is empty
		toolbar.EnableTool(wx.ID_UNDO, not currentPage.stockUndo == [])

	def OnRedo(self, event):
		""" Redo the diagram
		"""

		toolbar = event.GetEventObject()
		currentPage = toolbar.GetToolClientData(event.GetId()) if isinstance(toolbar.GetParent(), DetachedFrame) else self.nb2.GetCurrentPage()

		### append the stockundo and active it
		currentPage.stockUndo.append(pickle.dumps(obj=currentPage.GetDiagram(), protocol=0))
		toolbar.EnableTool(wx.ID_UNDO, True)

		### change the current canvas with the last undo
		new_diagram = pickle.loads(currentPage.stockRedo.pop())
		new_diagram.parent = currentPage
		currentPage.DiagramReplace(new_diagram)
		original_diagram = currentPage.GetDiagram()

		## if model is containerBlock, the grand parent is DetachedFrame and we could update the diagram withou update the original canvas
		if isinstance(original_diagram.GetGrandParent(), DetachedFrame):
			## update of all shapes in the original diagram
			original_diagram.shapes = new_diagram.shapes
		else:
			## refresh original canvas with new diagram
			original_canvas = original_diagram.parent
			original_canvas.DiagramReplace(new_diagram)

		### desable undo btn if the stockRedo list is empty
		toolbar.EnableTool(wx.ID_REDO, not currentPage.stockRedo == [])

	###
	def OnSaveFile(self, event):
		""" Save file button has been pressed.
		"""

		obj = event.GetEventObject()

		#if isinstance(obj, wx.ToolBar) and isinstance(obj.GetParent(), DetachedFrame):
		#	currentPage = obj.GetToolClientData(event.GetId())
		#else:
		currentPage = self.nb2.GetCurrentPage()

		### deselect all model to initialize select attribut for all models
		currentPage.deselect()

		diagram = currentPage.GetDiagram()

		### diagram preparation
		diagram.modify = False

		### save cmd file consists to export it
		#if isinstance(diagram, Container.ContainerBlock):
		#	Container.Block.OnExport(diagram, event)
		#else:
		if getattr(diagram,'last_name_saved', False):

			assert(os.path.isabs(diagram.last_name_saved))

			if Container.Diagram.SaveFile(diagram, diagram.last_name_saved):
				# Refresh canvas
				currentPage.Refresh()

				### enable save button on status bar
				tb = self.GetToolBar()
				tb.EnableTool(Menu.ID_SAVE, diagram.modify)

				### update the txt of the notebook tab (remove *that indicate that the file was modified)
				self.nb2.SetPageText(self.nb2.GetSelection(), "%s"%self.nb2.GetPageText(self.nb2.GetSelection()).replace('*',''))
				
			else:
				wx.MessageBox( _('Error saving file.') ,_('Error'), wx.OK | wx.ICON_ERROR)
		else:
			self.OnSaveAsFile(event)

	###
	def OnSaveAsFile(self, event):
		""" Save file menu as has been selected.
		"""

		currentPage = self.nb2.GetCurrentPage()

		### deselect all model to initialize select attribut for all models
		currentPage.deselect()

		diagram = copy.deepcopy(currentPage.GetDiagram())

		### options building
		msg = "DEVSimPy files (*.dsp)|*.dsp|"
		if builtins.__dict__['YAML_IMPORT']:
			msg+="YAML files (*.yaml)|*.yaml|"
		msg+="XML files (*.xml)|*.xml|All files (*)|*)"

		wcd = _(msg)
		
		home = self.home or os.path.dirname(diagram.last_name_saved)

		if not home:
			if self.openFileList == ['']*NB_OPENED_FILE:
				home = HOME_PATH 
			else: 
				home = self.home or os.path.dirname(self.openFileList[0])
	
		save_dlg = wx.FileDialog(self, message=_('Save file as...'), defaultDir=home, defaultFile=os.path.basename(diagram.last_name_saved), wildcard=wcd, style=wx.SAVE | wx.OVERWRITE_PROMPT)

		if save_dlg.ShowModal() == wx.ID_OK:
			path = os.path.normpath(save_dlg.GetPath())
			ext = os.path.splitext(path)[-1]
			file_name = save_dlg.GetFilename()
			wcd_i = save_dlg.GetFilterIndex()

			#ajoute de l'extention si abscente en fonction du wcd choisi (par defaut .dsp)
			if ext == '':
				if wcd_i == 0:
					path=''.join([path,'.dsp'])
				elif builtins.__dict__['YAML_IMPORT']:
					if wcd_i == 1:
						path=''.join([path,'.yaml'])
					elif wcd_i == 2:
						path=''.join([path,'.xml'])
				elif wcd_i == 1:
					path=''.join([path,'.xml'])

			### diagram preparation
			label = os.path.splitext(file_name)[0]
			diagram.LoadConstants(label)
			last_name_saved = diagram.last_name_saved
			diagram.last_name_saved = path
			diagram.modify = False

			#sauvegarde dans le nouveau fichier
			if Container.Diagram.SaveFile(diagram, path):

				### if OnSaveAs invocked from DetahcedFrame, we update the title
				df = self.GetWindowByEvent(event)
				if isinstance(df, DetachedFrame):
					df.SetTitle(label)

				if last_name_saved == '':
					self.nb2.SetPageText(self.nb2.GetSelection(), label)
					currentPage.SetDiagram(diagram)
				else:
					self.nb2.AddEditPage(label, diagram)

				### enable save button on status bar
				tb = self.GetToolBar()
				tb.EnableTool(Menu.ID_SAVE, diagram.modify)
			else:
				wx.MessageBox(_('Error saving file.'), _('Error'), wx.OK | wx.ICON_ERROR)

		save_dlg.Destroy()

	def OnImportXMLSES(self,event):
    	
		wcd = _("XML SES files (*.xmlsestree)|*.xmlsestree|XML SES files (*.sestree)|*.sestree|All files (*)|*")
		home = os.getenv('USERPROFILE') or os.getenv('HOME') or HOME_PATH if self.openFileList == ['']*NB_OPENED_FILE else os.path.dirname(self.openFileList[0])
		open_dlg = wx.FileDialog(self, message = _('Choose a file'), defaultDir = home, defaultFile = "", wildcard = wcd, style = wx.OPEN|wx.MULTIPLE|wx.CHANGE_DIR)

		### path,diagram dictionary
		new_paths = {}

		# get the new path from open file dialogue
		if open_dlg.ShowModal() == wx.ID_OK:

			### for selected paths
			for path in open_dlg.GetPaths():
				fileName = os.path.basename(path)
				self.nb2.AddEditPage(os.path.splitext(fileName)[0])
				actuel = self.nb2.GetSelection()
				canvas = self.nb2.GetPage(actuel)
		
				### if error whenimporting, we inform the user and we delete the tab of the notebook
				if not getDiagramFromXMLSES(fileName, canvas):
					wx.MessageBox(_('Error importing %s')%(fileName))
					self.nb2.DeletePage(actuel)
				else:
					wx.MessageBox(_('%s file imported!')%str(fileName), _('Info'), wx.OK|wx.ICON_INFORMATION)
	###
	def OnExportRest(self, event):
		""" Export YAML file to the 'uplaod' directory of a REST server.
		"""

		self.OnSaveFile(event)

		obj = event.GetEventObject()

		if isinstance(obj, wx.ToolBar) and isinstance(obj.GetParent(), DetachedFrame):
			currentPage = obj.GetToolClientData(event.GetId())
		else:
			currentPage = self.nb2.GetCurrentPage()

		### deselect all model to initialize select attribut for all models
		currentPage.deselect()

		diagram = currentPage.GetDiagram()

		### lauch the diag
		path = diagram.last_name_saved
		frame = YAMLExportGUI(self, -1, _('YAML Export'), path=path)
		frame.Show(True)

	###
	def OnExportStandalone(self, event):
		""" Export a Zip file to that can be used to simulate a yaml file in a no-gui and standalone mode. 
			The zip file contains all of the files needed to make a standalone version of devsimpy-nogui.
			It embedded also the yaml version of the current diagram in order to be able to stimulate him.
		"""

		

		obj = event.GetEventObject()

		if isinstance(obj, wx.ToolBar) and isinstance(obj.GetParent(), DetachedFrame):
			currentPage = obj.GetToolClientData(event.GetId())
		else:
			currentPage = self.nb2.GetCurrentPage()

		### deselect all model to initialize select attribut for all models
		currentPage.deselect()

		diagram = currentPage.GetDiagram()
	
		if diagram.last_name_saved == "":
			self.OnSaveFile(event)
   
		### temp path to save the dsp as a yaml
		path = os.path.join(gettempdir(), os.path.basename(diagram.last_name_saved).replace('.dsp','.yaml'))  

		### try to save the current diagram into a temp yaml file and launch the diag for the standalone exportation 
		if Container.Diagram.SaveFile(diagram, path):
			frame = StandaloneGUI(None, -1, _('Standalone settings'))
			frame.SetYAML(path)
			frame.Show(True)
		else:
			wx.MessageBox(_("An error occurred during the saving as yaml file."), _("Error"), wx.OK | wx.ICON_ERROR)
	###
	def OnImport(self, event):
		""" Import DEVSimPy library from Domain directory.
		"""

		# dialog pour l'importation de lib DEVSimPy (dans Domain) et le local
		dlg = ImportLibrary(self, wx.NewIdRef(), _('New/Import Library'), size=(550,400), style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)

		if (dlg.ShowModal() == wx.ID_OK):

			num = dlg._cb.GetItemCount()
			for index in range(num):
				label = dlg._cb.GetItemText(index)
				
				### met a jour le dico des elements selectionnes
				if dlg._cb.IsChecked(index) and label not in dlg._selectedItem:
					dlg._selectedItem.update({str(label):index})
				elif not dlg._cb.IsChecked(index) and label in dlg._selectedItem:
					del dlg._selectedItem[str(label)]

			for s in dlg._selectedItem:

				absdName = str(os.path.join(DOMAIN_PATH, s)) if s not in dlg._d else str(dlg._d[s])
				progress_dlg = wx.ProgressDialog(_('Importing library'), _("Loading %s ...")%s, parent=self, style=wx.PD_APP_MODAL | wx.PD_ELAPSED_TIME)
				progress_dlg.Pulse()

    			### add correct path to sys.path (always before InsertNewDomain)
				LibraryTree.AddToSysPath(absdName)
    			### add NewDomain

				self.tree.InsertNewDomain(absdName, self.tree.GetRootItem(), list(self.tree.GetSubDomain(absdName, self.tree.GetDomainList(absdName)).values())[0])

				progress_dlg.Destroy()
				wx.SafeYield()

			self.tree.SortChildren(self.tree.GetRootItem())

			### update the loaded libraries config file
			if (len(dlg._selectedItem)>0):
				self.SaveLibraryProfile()

		dlg.Destroy()

	###
	def OnSearch(self,evt):
		""" Method ofr the serach function.
		"""
		### search field
		search = evt.GetEventObject()

		# text taper par l'utilisateur
		text = search.GetValue()

		if text != '':

			#finded word list
			L = []

			#pour tout les parents qui n'ont pas de fils (bout de branche)
			for item in [elem for elem in list(self.tree.ItemDico.values()) if not self.tree.ItemHasChildren(elem)]:
				path = self.tree.GetPyData(item)
				dirName = os.path.basename(path)

				### plus propre que la deuxieme solution (a tester dans le temps)
				if dirName.startswith(text):
					L.append(path)

			#masque l'arbre
			self.tree.Hide()

			# Liste des domaines concernes
			if L:

				### on supprime l'ancien searchTree
				for item in self.searchTree.GetItemChildren(self.searchTree.GetRootItem()):
					self.searchTree.RemoveItem(item)

				### uniquify the list
				L = [os.path.dirname(a) for a in L]

				### construction du nouveau
				self.searchTree.Populate(L)

				### effacement des items qui ne correspondent pas
				for item in [elem for elem in list(copy.copy(self.searchTree.ItemDico).values()) if not self.searchTree.ItemHasChildren(elem)]:
					path = self.searchTree.GetPyData(item)

					### si les path ne commence pas par le text entre par l'utilsiateur, on les supprime
					if not os.path.basename(path).startswith(text):
						self.searchTree.RemoveItem(item)

				self.searchTree.Show()
				nb1 = self.GetControlNotebook()
				libPanel = nb1.GetLibPanel()
				libPanel.GetSizer().Layout()
				self.searchTree.ExpandAll()

			else:
				self.searchTree.Hide()
		else:
			self.searchTree.Hide()
			self.tree.Show()

	###
	def GetDiagramByWindow(self,window):
		""" Method that give the diagram present into the windows
		"""

		# la fenetre par laquelle a été invoqué l'action peut être principale (wx.App) ou detachée (DetachedFrame)
		if isinstance(window, DetachedFrame):
			return window.GetCanvas().GetDiagram()
		else:
			activePage = window.nb2.GetSelection()
			return window.nb2.GetPage(activePage).GetDiagram()

	###
	def GetWindowByEvent(self, event):
		""" Method that give the window instance from the event
		"""

		obj = event.GetEventObject()

		# si invocation de l'action depuis une ToolBar
		if isinstance(obj, (wx.ToolBar,wx.Frame)):
			window = obj.GetTopLevelParent()
		# si invocation depuis une Menu (pour le Show dans l'application principale)
		elif isinstance(obj, wx.Menu):
			window = wx.GetApp().GetTopWindow()
		else:
			sys.stdout.write(_("This option has not been implemented yet."))
			return False

		return window

	###
	def OnConstantsLoading(self, event):
		""" Method calling the AddConstants windows.
		"""
		parent = self.GetWindowByEvent(event)
		diagram = self.GetDiagramByWindow(parent)
		diagram.OnAddConstants(event)

	###
	def OnInfoGUI(self, event):
		""" Method calling the PriorityGui.
		"""
		parent = self.GetWindowByEvent(event)
		diagram = self.GetDiagramByWindow(parent)
		diagram.OnInformation(parent)

	###
	def OnPriorityGUI(self, event):
		""" Method calling the PriorityGui.
		"""
		parent = self.GetWindowByEvent(event)
		diagram = self.GetDiagramByWindow(parent)
		diagram.OnPriority(parent)

	###
	def OnCheck(self, event):
		""" Method calling the Check.
		"""
		parent = self.GetWindowByEvent(event)
		diagram = self.GetDiagramByWindow(parent)
		return diagram.OnCheck(event)

	###
	def OnPlugins(self, event):
		""" Method calling the plugins preference GUI.
		"""
		frame = PreferencesGUI(self,_("Preferences Manager"))
		### select the last page which is the plugins config page (unstable because depends on the page oreder)
		frame.pref.SetSelection(frame.pref.GetPageCount()-1)
		frame.Show()
	###
	def OnSimulation(self, event):
		""" Method calling the simulationGUI.
		"""
		parent = self.GetWindowByEvent(event)
		diagram = self.GetDiagramByWindow(parent)
		return diagram.OnSimulation(event)

	def OnLoadDiagram(self):
		### load .dsp or empty on empty diagram
		if len(sys.argv) >= 2:
			for arg in sys.argv[1:]:
				if os.path.exists(arg):
					if arg.endswith(('.dsp','.yaml')):
						diagram = Container.Diagram()
						#diagram.last_name_saved = arg
						name = os.path.basename(arg)
						diagram.label = name
						if not isinstance(diagram.LoadFile(arg), Exception):
							self.nb2.AddEditPage(os.path.splitext(name)[0], diagram)
							self.StartSimulationGUIWin(arg, [diagram])

				### want to open all dsp or yaml in directory
				elif arg.endswith(('*.dsp','*.yaml')):
					path = os.path.dirname(arg)
					if arg.endswith('*.dsp'):
						files = [f for f in glob.glob(path + "**/*.dsp", recursive=True)]
					else:
						files = [f for f in glob.glob(path + "**/*.yaml", recursive=True)]

					L = []
					for f in files:
						diagram = Container.Diagram()
						#diagram.last_name_saved = arg
						name = os.path.basename(f)
						diagram.label = name
						if not isinstance(diagram.LoadFile(f), Exception):
							self.nb2.AddEditPage(os.path.splitext(name)[0], diagram)
							L.append(diagram)

					self.StartSimulationGUIWin(arg, L)

	def StartSimulationGUIWin(self, arg, diagrams):
		"""try to lunch the sim windows if there is int or (ntl, inf, infinity) arg just after the .dsp or yaml.
		"""

		try:
			arg = sys.argv[sys.argv.index(arg)+1]
		except IndexError:
			pass
		else:
			if arg.isdigit() or arg in ('ntl','inf','infinity'):
				import SimulationGUI
				
				L = []
				for i,diagram in enumerate(diagrams):
				## make DEVS instance from diagram
					master = Container.Diagram.makeDEVSInstance(diagram)
					if not isinstance(master, tuple):
						simFrame = SimulationGUI.SimulationDialog(self, wx.NewIdRef(), _(" %s Simulator"%diagram.label))
						simFrame.SetMaster(master)

						### center and shit to avoid superposition
						if simFrame:								
							junk, junk, dw, dh = wx.ClientDisplayRect()
							w, h = simFrame.GetSize()
							g = 15*i
							x = dw - w + g
							y = dh - h + g
							simFrame.SetPosition((int(x/2), int(y/2)))
	
							simFrame.SetWindowStyle(wx.DEFAULT_FRAME_STYLE | wx.STAY_ON_TOP)

							if arg.isdigit():
								simFrame.SetNTL(False)
								simFrame.SetTime(arg)
								simFrame.Show()
							elif arg in ('ntl','inf','infinity'):
								simFrame.SetNTL(True)
								simFrame.Show()

							L.append(simFrame)

				### try to start a simulation
				try:
					arg = sys.argv[sys.argv.index(arg)+1]
				except IndexError:
					pass
				else:
					if arg in ('start','go'):
						for sf in L:
							evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId, sf._btn1.GetId())
							wx.PostEvent(sf._btn1, evt)
	
		finally:
			### Force to close DEVSimPy
			try:
				arg = sys.argv[-1]
			except IndexError:
				pass
			else:
				if arg in ('close','quit'):
					self.Close()

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

	####
	#def OnShowControl(self, evt):
		#""" Shell view menu has been pressed.
		#"""

		#menu = self.GetMenuBar().FindItemById(evt.GetId())
		#if menu.IsChecked():
			#self._mgr.GetPane("nb1").Show()
		#else:
			#self._mgr.GetPane("nb1").Hide()
		#self._mgr.Update()

	###
	def OnShowShell(self, evt):
		""" Shell view menu has been pressed.
		"""

		menu = self.GetMenuBar().FindItemById(evt.GetId())
		mgr = self.GetMGR()
		mgr.GetPane("shell").Show(menu.IsChecked())
		mgr.Update()

	###
	def OnShowSimulation(self, evt):
		""" Simulation view menu has been pressed.
		"""

		menu = self.GetMenuBar().FindItemById(evt.GetId())
		nb1 = self.GetControlNotebook()

		if menu.IsChecked():
			mgr = self.GetMGR()
			### Control panel is  not hide
			if mgr.GetPane('nb1').IsShown():
				menu.Check(self.OnSimulation(evt))
			else:

				mgr.GetPane("nb1").Show().Left().Layer(0).Row(0).Position(0).BestSize(wx.Size(280,-1)).MinSize(wx.Size(250,-1))
				mgr.Update()

				### delete both the properties and libraries panels (inserted by default)
				nb1.DeletePage(0)
				nb1.DeletePage(0)

				menu.Check(self.OnSimulation(evt))

		else:
			### delete the libraries panel (inserted by default)
			pos = nb1.GetPageIndex(nb1.GetSimPanel())
			if pos != None:
				nb1.DeletePage(pos)

	###
	def OnShowProperties(self, evt):
		""" Properties view menu has been pressed.
		"""

		menu = self.GetMenuBar().FindItemById(evt.GetId())
		nb1 = self.GetControlNotebook()

		if menu.IsChecked():
			mgr = self.GetMGR()
			### Control panel is not hide
			if mgr.GetPane('nb1').IsShown():

				propPanel = PropPanel(nb1, nb1.labelList[1])

				### Adding page
				nb1.AddPage(propPanel, propPanel.GetName(), imageId=1)

			else:
				self._mgr.GetPane("nb1").Show().Left().Layer(0).Row(0).Position(0).BestSize(wx.Size(280,-1)).MinSize(wx.Size(250,-1))
				self._mgr.Update()
				### delete the libraries panel (inserted by default)
				pos = nb1.GetPageIndex(nb1.GetLibPanel())
				nb1.DeletePage(pos)

			menu.Check()
		else:
			### position of the properties panel
			pos = nb1.GetPageIndex(nb1.GetPropPanel())
			if pos != None:
				nb1.DeletePage(pos)

	###
	def OnShowLibraries(self, evt):
		""" Libraries view menu has been pressed.
		"""

		menu = self.GetMenuBar().FindItemById(evt.GetId())
		nb1 = self.GetControlNotebook()

		if menu.IsChecked():

			mgr = self.GetMGR()
			### Control panel is  not hide
			if mgr.GetPane('nb1').IsShown():
				libPanel = LibPanel(nb1, nb1.labelList[0])

				## Adding page
				nb1.AddPage(libPanel, libPanel.GetName(), imageId=0)

				mainW = self.GetTopLevelParent()
				mainW.tree = nb1.GetTree()
				mainW.searchTree = nb1.GetSearchTree()
				mainW.search = nb1.GetSearch()

				mainW.Bind(wx.EVT_TREE_BEGIN_DRAG, mainW.OnDragInit, id = mainW.tree.GetId())
				mainW.Bind(wx.EVT_TREE_BEGIN_DRAG, mainW.OnDragInit, id = mainW.searchTree.GetId())

			### must to create a control panel
			else:
				self._mgr.GetPane("nb1").Show().Left().Layer(0).Row(0).Position(0).BestSize(wx.Size(280,-1)).MinSize(wx.Size(250,-1))
				self._mgr.Update()
				### delete the properties panel (insered by default)
				pos = nb1.GetPageIndex(nb1.GetPropPanel())
				nb1.DeletePage(pos)

			menu.Check()

		else:
			### position of the libraries panel
			pos = nb1.GetPageIndex(nb1.GetLibPanel())
			if pos != None:
				nb1.DeletePage(pos)

	###
	def OnShowToolBar(self, evt):
		tb=self.GetToolBar()
		tb.Show(not tb.IsShown())

	def OnShowEditor(self, evt):
		""" Editor view has been pressed.
		"""

		menu = self.GetMenuBar().FindItemById(evt.GetId())

		nb2 = self.GetDiagramNotebook()
		canvas = nb2.GetPage(nb2.GetSelection())
		mgr = self.GetMGR()
		mgr.GetPane("editor").Show(menu.IsChecked())
		panel = self.GetEditorPanel()

		if menu.IsChecked():
			### attach editor to notify event from ShapeCanvas
			canvas.attach(panel)
		else:
			### detach editor to notify event from ShapeCanvas
			canvas.detach(panel)

		mgr.Update()

	###
	def OnFrench(self, event):
		self.cfg.Write("language", "'fr'")
		if wx.Platform == '__WXGTK__':
			dlg = wx.MessageDialog(self, _('You need to restart DEVSimPy to take effect.\n\nDo you want to restart now ?'), _('Internationalization'), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
			if dlg.ShowModal() == wx.ID_YES:
				wx.CallAfter(self.OnRestart())
			dlg.Destroy()
		else:
			wx.MessageBox(_('You need to restart DEVSimPy to take effect.'), _('Info'), wx.OK|wx.ICON_INFORMATION)

	###
	def OnEnglish(self, event):
		self.cfg.Write("language", "'en'")

		if wx.Platform == '__WXGTK__':
			dlg = wx.MessageDialog(self, _('You need to restart DEVSimPy to take effect.\n\nDo you want to restart now ?'), _('Internationalization'), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
			if dlg.ShowModal() == wx.ID_YES:
				wx.CallAfter(self.OnRestart())
			dlg.Destroy()
		else:
			wx.MessageBox(_('You need to restart DEVSimPy to take effect.'), _('Info'), wx.OK|wx.ICON_INFORMATION)

	###
	def OnAdvancedSettings(self, event):
		frame = PreferencesGUI(self,_("Preferences Manager"))
		frame.Show()

	###
	@BuzyCursorNotification
	def OnProfiling(self, event):
		""" Simulation profiling for fn file.
		"""

		### find the prof file name
		menu_item = self.GetMenuBar().FindItemById(event.GetId())
		fn = menu_item.GetItemLabelText()
		prof_file_path = os.path.join(gettempdir(), fn)

		### list of item in single choice dialogue
		### gprof2dot needs graphviz
		choices = ['snakeviz', 'gprof2dot', _('Embedded in DEVSimPy')]

		if os.path.exists(prof_file_path):

			dlg = wx.SingleChoiceDialog(self, _('What profiling software are you using?'), _('Single Choice'), choices)
			if dlg.ShowModal() == wx.ID_OK:
				
				response = dlg.GetStringSelection()
				if response == 'snakeviz':
					dlg.Destroy()
					if install_and_import(response):
						threading.Thread(target=self.longRunning1,
						args=(response,prof_file_path),
						).start()
					else:
						wx.MessageBox(_('%s is not installed.'%(response)), _('Error'), wx.OK | wx.ICON_ERROR)
				elif response == 'gprof2dot':
					dlg.Destroy()
					if install_and_import(response):
						threading.Thread(target=self.longRunning2,
						args=(response,prof_file_path),
						).start()
					else:
						wx.MessageBox(_('%s is not installed.'%(response)), _('Error'), wx.OK | wx.ICON_ERROR)
				elif response == _('Embedded in DEVSimPy'):
					dlg.Destroy()
					output = self.LoadProfFile(prof_file_path)
					d = wx.lib.dialogs.ScrolledMessageDialog(self, output, _("Statistic of profiling"), style=wx.OK|wx.ICON_EXCLAMATION|wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
					d.CenterOnParent(wx.BOTH)
					d.ShowModal()
				else:
					dlg.Destroy()
		else:
			wx.MessageBox(_('The profile file %s does not exist.'%(prof_file_path)), _('Error'), wx.OK | wx.ICON_ERROR)

	@staticmethod
	def longRunning1(response, prof_file_path):
		subprocess.call(" ".join([response,prof_file_path]), shell=True)

	@staticmethod
	def longRunning2(response, prof_file_path):
		png_file_path = prof_file_path.replace('.prof', '.png')
		subprocess.call(" ".join([response,'-f pstats',prof_file_path,"|", "dot", "-Tpng", "-o", png_file_path, "&&", "eog", png_file_path]),  shell=True)

	@staticmethod
	@redirectStdout
	def LoadProfFile(prof_file_path):
		### lauch embedded prof editor
		stats = pstats.Stats(prof_file_path)
		# Clean up filenames for the report
		stats.strip_dirs()
		# Sort the statistics by the cumulative time spent in the function
		stats.sort_stats('cumulative')
		stats.print_stats()

	###
	def OnDeleteProfiles(self, event):
		dlg = wx.MessageDialog(self, _('Do you realy want to delete all files ?'), _('Profile Manager'), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
		if dlg.ShowModal() == wx.ID_YES:
			tmp_dir = gettempdir()
			for fn in [f for f in os.listdir(tmp_dir) if f.endswith(('.prof','.cachegrind'))]:
				os.remove(os.path.join(tmp_dir,fn))
		dlg.Destroy()

	###
	def OnRestart(self):
		""" Restart application.
		"""

		# permanently writes all changes (otherwise, they’re only written from object’s destructor)
		self.cfg.Flush()

		# restart application on the same process (erase)
		program = "python"
		arguments = ["devsimpy.py"]
		os.execvp(program, (program,) +  tuple(arguments))

	def OnHelp(self, event):
		""" Shows the DEVSimPy help file. """

		lang = eval('self.language')

		filename = os.path.join(HOME_PATH, 'doc', 'html', lang, 'Help.zip')
		if wx.VERSION_STRING >= '4.0':
			wx.FileSystem.AddHandler(wx.ArchiveFSHandler())     # add the Zip filesystem (only before HtmlHelpControler instance)
		else:
			wx.FileSystem.AddHandler(wx.ZipFSHandler())

		self.help = wx.html.HtmlHelpController()

		if not self.help.AddBook(filename, True):
			wx.MessageBox(_("Unable to open: %s")%filename, _("Error"), wx.OK|wx.ICON_ERROR)
		else:
			self.help.Display(os.path.join('html','toc.html'))

	def OnUpdatPiPPackage(self, event):
		msg = _("Do you really want to update all pip packages that DEVSimPy depends?")
		#info = ""
		dlg = wx.RichMessageDialog(self, msg, _("Update Manager"), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
		#dlg.ShowDetailedText(info)
		if dlg.ShowModal() not in [wx.ID_NO, wx.ID_CANCEL]:
			self.DoUpdatPiPPackage()	
		dlg.Destroy()

	@cond_decorator(builtins.__dict__.get('GUI_FLAG',True), ProgressNotification(_("Update of dependant pip packages")))
	def DoUpdatPiPPackage(self):
		if updatePiPPackages():
			args = (_('Information'), _('All pip packages that DEVSimPy depends have been updated! \nYou need to restart DEVSimPy to take effect'))
			kwargs = {'parent':self, 'timeout':5}
		else:
			args = (_('Error'), _('Pip packages update failed! \nCheck the trace in background for more informations.'))
			kwargs = {'parent':self, 'flag':wx.ICON_ERROR, 'timeout':5}

		NotificationMessage(*args, **kwargs)

	###
	def OnUpdatFromGitRepo(self, event):
		msg = _("Do you really want to update DEVSimPy with a Pull Git request?")
		#info = ""
		dlg = wx.RichMessageDialog(self, msg, _("Update Manager"), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
		#dlg.ShowDetailedText(info)
		if dlg.ShowModal() not in [wx.ID_NO, wx.ID_CANCEL]:
			if install_and_import('gitpython', 'git'):
				self.DoUpdatFromGitRepo()
		dlg.Destroy()

	@cond_decorator(builtins.__dict__.get('GUI_FLAG',True), ProgressNotification(_("DEVSimPy Update from git repo")))
	def DoUpdatFromGitRepo(self):
		if updateFromGitRepo():
			args = (_('Information'), _('Update of DEVSimPy from git done! \nYou need to restart DEVSimPy to take effect.'))
			kwargs = {'parent':self, 'timeout':5}
		else:
			args = (_('Error'), _('DEVSimPy update from git failed! \nCheck the trace in background for more informations.'))
			kwargs =  {'parent':self, 'flag':wx.ICON_ERROR, 'timeout':5}
		
		NotificationMessage(*args, **kwargs)

	###
	def OnUpdatFromGitArchive(self, event):
		msg = _("Do you really want to update DEVSimPy from the last master archive? \nAll files will be replaced and you cannot go backwards.")
		#info = ""
		dlg = wx.RichMessageDialog(self, msg, _("Update Manager"), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
		#dlg.ShowDetailedText(info)
		if dlg.ShowModal() not in [wx.ID_NO, wx.ID_CANCEL]:
			self.DoUpdatFromGitArchive()
		dlg.Destroy()

	@cond_decorator(builtins.__dict__.get('GUI_FLAG',True), ProgressNotification(_("DEVSimPy Update from git.")))
	def DoUpdatFromGitArchive(self):
		if updateFromGitArchive():
			args = (_('Information'), _('Update of DEVSimPy from git archive done! \nYou need to restart DEVSimPy to take effect.'))
			kwargs = {'parent':self, 'timeout':5}
		else:
			args = (_('Error'), _('DEVSimPy update from git archive failed! \nCheck the trace in background for more informations.'))
			kwargs =  {'parent':self, 'flag':wx.ICON_ERROR, 'timeout':5}
		
		NotificationMessage(*args, **kwargs)

	def OnAPI(self, event):
		""" Shows the DEVSimPy API help file. """

		#webbrowser.open_new(opj(self.installDir + "/docs/api/index.html"))
		wx.MessageBox(_("This option has not been implemented yet."), _('Info'), wx.OK|wx.ICON_INFORMATION)

	@BuzyCursorNotification
	def OnAbout(self, event):
		""" About menu has been pressed.
		"""

		description = _("""DEVSimPy is an advanced wxPython framework for the modeling and simulation of systems based on the DEVS formalism.
Features include powerful built-in editor, advanced modeling approach, powerful discrete event simulation algorithm,
import/export DEVS components library and more.

wxPython %s - python %s"""%(wx.version(),platform.python_version()))

		licence =_( """DEVSimPy is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the Free Software Foundation;
either version 3 of the License, or (at your option) any later version.

DEVSimPy is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU General Public License for more details. You should have received a copy of
the GNU General Public License along with File Hunter; if not, write to
the Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA""")

		info = wx.AboutDialogInfo()

		info.SetIcon(getIcon(os.path.join(ICON_PATH_16_16, SPLASH_PNG)))
		info.SetName("""DEVSimPy""")
		info.SetVersion(self.GetVersion())
		info.SetDescription(description)
		info.SetCopyright(_("""(C) 2020 SISU Project - UMR CNRS 6134 SPE Lab."""))
		info.SetWebSite("""http://spe.univ-corse.fr""")
		info.SetLicence(licence)
		info.AddDeveloper(_("""\nL. Capocchi (capocchi@univ-corse.fr)\n"""))
		info.AddDocWriter(_("""\nL. Capocchi (capocchi@univ-corse.fr)\n"""))
		info.AddTranslator(_("""\nL. Capocchi (capocchi@univ-corse.fr)\n"""))

		wx.AboutBox(info)

	@BuzyCursorNotification
	def OnContact(self, event):
		""" Launches the mail program to contact the DEVSimPy author. """

		frame = SendMailWx(None)
		frame.Show()
		   
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

		self.app = app

		### for Phoenix version ()
		if wx.VERSION_STRING < '4.0':
			splashStyle = wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_TIMEOUT
		else:
			splashStyle = wx.adv.SPLASH_CENTRE_ON_SCREEN | wx.adv.SPLASH_TIMEOUT

		splashBmp = wx.Bitmap(SPLASH_PNG)
		splashDuration = 2000

		if old:
			AdvancedSplash.__init__(self, splashBmp, splashStyle, splashDuration, None)
			self.CreateStatusBar()
		else:
			style=wx.NO_BORDER|wx.FRAME_NO_TASKBAR|wx.STAY_ON_TOP|wx.FRAME_SHAPED
			extrastyle = AdvancedSplashScreen.AS_TIMEOUT|AdvancedSplashScreen.AS_CENTER_ON_SCREEN #| AdvancedSplashScreen.AS_SHADOW_BITMAP
			shadow = wx.WHITE

			if wx.Platform == '__WXMAC__':
				AdvancedSplash.__init__(self, bitmap=splashBmp, timeout=splashDuration, style=style, shadowcolour=wx.WHITE, parent=None)
			else:
				if wx.VERSION_STRING >= '2.8.11':
					AdvancedSplash.__init__(self, bitmap=splashBmp, timeout=splashDuration, style=style, agwStyle=extrastyle, shadowcolour=shadow, parent=None)
				else:
					AdvancedSplash.__init__(self, bitmap=splashBmp, timeout=splashDuration, style=style, extrastyle=extrastyle, shadowcolour=shadow, parent=None)

			w = splashBmp.GetWidth()
			h = splashBmp.GetHeight()

			# Set The AdvancedSplash Size To The Bitmap Size
			self.SetSize((w, h))

			self.SetTextPosition((30, h-20))
			self.SetTextFont(wx.Font(9, 70, 1, 400, False))
			self.SetTextColour("#797373")

		self.Bind(wx.EVT_CLOSE,self.OnClose)
		
		self.fc = wx.FutureCall(500, self.ShowMain)
		
		# for splash info
		try:
			pub.subscribe(self.OnObjectAdded, 'object.added')
		except TypeError:
			pub.subscribe(self.OnObjectAdded, data='object.added')

		pub.sendMessage('load.diagrams')

	def OnObjectAdded(self, message):
		# data passed with your message is put in message.data.
		# Any object can be passed to subscribers this way.

		data = message.data if hasattr(message, 'data') else message
		
		try:
			self.SetText(data)
		### wx <= 2.8
		except AttributeError:
			try:
				self.PushStatusText(data)
			except:
				pass

		with open(LOG_FILE, 'a') as f:
			f.write("%s - %s"%(time.strftime("%Y-%m-%d %H:%M:%S"), data))

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

		self.app.SetExceptionHook()
		
		# Call after the loading diagram method which depends on the invocked command line
		try:
			wx.CallAfter(self.app.frame.OnLoadDiagram)
		except:
			pass
		
	def ShowMain(self):
		""" Shows the main application (DEVSimPy). """

		self.app.frame = MainApplication(None, wx.NewIdRef(), 'DEVSimPy %s'%__version__)

		self.app.frame.statusbar.SetStatusText(_('wxPython %s - python %s'%(wx.version(),platform.python_version())),1)

		# keep in a attribute of stdio which is invisible until now
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

		wx.Frame.__init__(self, parent, id, title, position, size, style=wx.DEFAULT_FRAME_STYLE|wx.STAY_ON_TOP)
		self.Bind(wx.EVT_CLOSE, self.OnClose)


	def OnClose(self, event):
		"""	Handles the wx.EVT_CLOSE event
		"""
		self.Show(False)
		event.Skip()

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
		self.st 	= None

	def SetParent(self, parent):
		"""Set the window to be used as the popup Frame's parent."""
		self.parent = parent

	def CreateOutputWindow(self, st):
		self.st = st
		self.start()

	def run(self):
		self.frame = LogFrame(self.parent, wx.NewIdRef(), self.title, self.pos, self.size)
		self.text  = wx.TextCtrl(self.frame, wx.NewIdRef(), "", style = wx.TE_MULTILINE|wx.HSCROLL)
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
class DEVSimPyApp(wx.App, wit.InspectionMixin):

	outputWindowClass = PyOnDemandOutputWindow

	def __init__(self, redirect=False, filename=None):
		wx.App.__init__(self, redirect, filename)

		# make sure we can create a GUI
		if not self.IsDisplayAvailable() and not builtins.__dict__.get('GUI_FLAG',True):

			if wx.Platform == '__WXMAC__':
				msg = """This program needs access to the screen.
				Please run with 'pythonw', not 'python', and only when you are logged
				in on the main display of your Mac."""

			elif wx.Platform == '__WXGTK__':
				msg = "Unable to access the X Display, is $DISPLAY set properly?"

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

		# initialize the inspection tool (enabled with Ctrl+Alt+I)
		self.Init()

		# Check runtime version
		if wx.VERSION_STRING < __min_wx_version__:
			wx.MessageBox(caption=_("Warning"),
							message=_("You're using version %s of wxPython, but DEVSimPy was written for min version %s.\n"
							"There may be some version incompatibilities...")
							% (wx.VERSION_STRING, __min_wx_version__))
		# For debugging
        #self.SetAssertMode(wx.PYAPP_ASSERT_DIALOG|wx.PYAPP_ASSERT_EXCEPTION)

		wx.SystemOptions.SetOption("mac.window-plain-transition", 1)
		self.SetAppName("DEVSimPy")

		# start our application with splash
		splash = AdvancedSplashScreen(self)
		splash.Show()

		return True

	def SetExceptionHook(self):
		# Set up the exception handler...
		sys.excepthook = ExceptionHook

#-------------------------------------------------------------------
if __name__ == '__main__':

	_ = wx.GetTranslation

	### python devsimpy.py -c|-clean in order to delete the config file
	if len(sys.argv) >= 2 and sys.argv[1] in ('-c', '-clean'):
		config_file1 = os.path.join(GetUserConfigDir(), '.devsimpy')
		config_file2 = os.path.join(GetUserConfigDir(), 'devsimpy.ini')
		r = input(_('Are you sure to delete DEVSimPy config files (.devsimpy and devsimpy.ini)? (Yes,No):'))
		if r in ('Y', 'y', 'yes', 'Yes', 'YES'):
			try:
				os.remove(config_file1)
			except Exception as info:
				#traceback.print_exc()
				pass
			else:
				sys.stdout.write(_('%s has been deleted!\n')%config_file1)
			
			try:
				os.remove(config_file2)
			except Exception as info:
				#traceback.print_exc()
				pass
			else:
				sys.stdout.write(_('%s has been deleted!\n')%config_file2)

		elif r in ('N','n','no', 'No'):
			pass
		else:
			pass
	elif len(sys.argv) >= 2 and sys.argv[1] in ('-m'):
		##########################################
		import compileall

		compileall.compile_dir('.', maxlevels=20, rx=re.compile(r'/\.svn'))
		###########################################
		sys.stdout.write(_('All .pyc has been updated!\n'))

	### python devsimpy.py -d|-debug in order to define log file
	elif len(sys.argv) >= 2 and sys.argv[1] in ('-d, -debug'):
		log_file = 'log.txt'
		sys.stdout.write(_('Writing %s file.\n')%log_file)

	### python devsimpy.py -h|-help in order to invoke command hepler
	elif len(sys.argv) >= 2 and sys.argv[1] in ('-h, -help'):
		sys.stdout.write(_('Welcome to the DEVSimpy helper.\n'))
		sys.stdout.write(_('\t To execute DEVSimPy GUI: python devsimpy.py\n'))
		sys.stdout.write(_('\t To load an existing dsp file / all .dsp files / all .yaml files in a directory: \n\t\t$ python devsimpy.py <absolute path of .dsp file/*.dsp/*.yaml>\n'))
		sys.stdout.write(_('\t To load an existing dsp with a simulation frame initialized with a time 10: \n\t\t$ python devsimpy.py <absolute path of the .dsp file> 10\n'))
		sys.stdout.write(_('\t To load an existing dsp with a simulation frame initialized with no time limit: \n\t\t$ python devsimpy.py <absolute path of the .dsp file> ntl/inf/infinity\n'))
		sys.stdout.write(_('\t To start simulation: \n\t\t$ python devsimpy.py <absolute path of the .dsp file> ntl/inf/infinity start/go\n'))
		sys.stdout.write(_('\t To execute DEVSimPy cleaner: python devsimpy.py -c|-clean\n'))
		sys.stdout.write(_('\t To close DEVSimPy: python devsimpy.py close|quit\n'))
		sys.stdout.write(_('Authors: L. Capocchi (capocchi@univ-corse.fr)\n'))
		sys.exit()

	else:
		pass

	## si redirect=True et filename=None alors redirection dans une fenetre
	## si redirect=True et filename="fichier" alors redirection dans un fichier
	## si redirect=False redirection dans la console
	app = DEVSimPyApp(redirect = False, filename = None)
	app.MainLoop()
