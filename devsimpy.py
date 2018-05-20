# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# devsimpy.py --- DEVSimPy - The Python DEVS GUI modeling and simulation software
#                     --------------------------------
#                            Copyright (c) 2018
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 3.0                                      last modified:  03/05/18
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
# strong depends: wxPython
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
# To install with git: git clone -b version-3.0 https://github.com/capocchi/DEVSimPy.git DEVSimPy-v3.0
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GLOBAL VARIABLES AND FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

### at the beginning to prevent with statement for python version <=2.5
from __future__ import with_statement

import datetime

__authors__ = "Laurent Capocchi <capocchi_l@univ-corse.fr>, SISU project group <santucci_j@univ-corse.fr>"
__date__ = str(datetime.datetime.now())
__version__ = '3.0'
__docformat__ = 'epytext'

import copy
import os
import sys
import time
import re
import gettext
import __builtin__
import webbrowser
import platform
import threading
import cPickle
import itertools
import shutil

from ConfigParser import SafeConfigParser
from tempfile import gettempdir

try:
	import hotshot
	import hotshot.stats
except ImportError:
	sys.stdout.write("Hotshot module not found. If you want to perform profiling simulation, install it!")

__min_wx_version__ = ['4.0','3.0','2.9','2.8','2.7','2.6','2.5']

__wxpython_url__ = 'http://wxpython.org'
__get__wxpython__ = 'Get it from %s'%__wxpython_url__

def import_pip():
	"""
	""" 
	try:
		import pip
		
	### if there is an import error, we install pip
	except ImportError, info:
		### get get-pip.py file from DEVSimPy-site repository and install it
		temp_directory = gettempdir()
		
		try:
			downloadFile('https://raw.githubusercontent.com/capocchi/DEVSimPy-site/gh-pages/get-pip.py', temp_directory)
			os.system('{} {}'.format('python', os.path.join(temp_directory, 'get-pip.py')))
		
			import pip
		except Exception, info:
			sys.stdout.write(info)
			sys.stdout.write('pip installation process has been interrupted!\n Try to install pip yourself.\n')
			sys.exit()
					
def install_and_import(package):
	import importlib
	
	try:
		importlib.import_module(package)
	
	except ImportError:
		import_pip()
	
		sys.stdout.write("Install %s form pip\n"%package)
		
		try:
			raw_input(_("Press Enter to continue (Ctrl+C to skip)"))
		except SyntaxError:
			sys.exit()
		else:
			try:
				pip.main(['install', package])
			except:
				sys.stdout.write("Unable to install %s using pip. Please read the instructions for \
				manual installation.. Exiting" % package)
				sys.stdout.write("Error: %s: %s" % (exc_info()[0], exc_info()[1]))
	finally:
		globals()[package] = importlib.import_module(package)

def downloadFile(url, directory) :

	install_and_import('requests')

	localFilename = url.split('/')[-1]
	with open(directory + '/' + localFilename, 'wb') as f:
		start = time.clock()
		try:
			r = requests.get(url, stream=True)
		except:
			sys.stdout.write('Failed to establish internet connection\n.')
			sys.exit()
		total_length = r.headers.get('content-length')
		dl = 0
		if total_length is None: # no content length header
			f.write(r.content)
		else:
			for chunk in r.iter_content(1024):
				dl += len(chunk)
				f.write(chunk)
				done = int(50 * dl / int(total_length))
				sys.stdout.write("\r[%s%s] %s bps" % ('=' * done, ' ' * (50-done), dl//(time.clock() - start)))
				print ''
	return (time.clock() - start)

ABS_HOME_PATH = os.path.abspath(os.path.dirname(sys.argv[0]))

################################################################
### Loading wx python library
################################################################

### ini file exist ?
parser = SafeConfigParser()
parser.read(os.path.join(os.path.expanduser("~"),'devsimpy.ini'))
section, option = ('wxversion', 'to_load')
ini_exist = parser.has_option(section, option)

if not hasattr(sys, 'frozen'):
	### try to import wxversion
	try:
		import wxversion

	except ImportError:
		### install wxversion by coping the wxversion.py file into python site-packages
		import shutil
		from distutils.sysconfig import get_python_lib

		try:
			shutil.copy(os.path.join(ABS_HOME_PATH, 'wxversion.py'),  get_python_lib())
		# eg. src and dest are the same file
		except shutil.Error as e:
			print('Error: %s' % e)
		# eg. source or destination doesn't exist
		except IOError as e:
			print('Error: %s' % e.strerror)
		else:
			### import wxversion
			import wxversion

	finally:
		### if devsimpy.ini file exist, it contains the wx version to load.
		if ini_exist:
			v = parser.get(section, option)
			if v.isdigit():
				wxversion.select([v])
			#else:
				### wx is not installed, we try to install it from pip (local or remote)
			#	sys.stderr.write("Try to import the version %s of wx Failed!\n"%v)

		### select the wxpython version from __min_wx_version__
		else:
			if wxversion.checkInstalled(__min_wx_version__):
				wxversion.select(__min_wx_version__)

	### trying to import wx
	try:
		### if wxpython has been installed using portable python solution (winpython, PythonXY, anaconda...), we add the wx path to the python path
		from distutils.sysconfig import get_python_lib
		path = os.path.join(get_python_lib(), 'wx-3.0-msw')
		if os.path.exists(path) and path not in sys.path:
			sys.path.append(path)

		import wx

	except ImportError:

		try:
			### wx is not installed, we try to install it from pip (local or remote)
			sys.stderr.write("Error: DEVSimPy requires the wxPython package, which doesn't seem to be installed\n")

			r = raw_input("Do you want to install wxPython package form: \n 1 - the PyPi repository \n 2 (default) - the DEVSimPy github repository\n Choice:") or '2'
			
			if r == '1':
				install_and_import('wxpython')	
			else:
			
				import_pip()
					
				### find the CPU architecture
				is_64bits = sys.maxsize > 2**32
		
				### its win32, maybe there is win64 too?
				is_windows = sys.platform.startswith('win')
				
				if is_windows:
					### get whl file from DEVSimPy-site hosted by github
					if is_64bits :
						file = 'wxPython-3.0.2.0-cp27-none-win_amd64.whl' 
					else :
						file = 'wxPython-3.0.2.0-cp27-none-win32.whl' 
				else:
					sys.stdout.write('Please install wx 3.x from your package manager\n')
					sys.exit()
					
				### url to download the whl file
				whl_url = 'https://raw.githubusercontent.com/capocchi/DEVSimPy-site/gh-pages/pip-packages/'+file
					
				### temp directory to store whl file
				temp_directory = gettempdir()
		
				whl_path = os.path.join(temp_directory, file)
		
				sys.stdout.write("Downloading %s from DEVSimPy GitHub repository...\n"%(file))
				time_elapsed = downloadFile(whl_url, temp_directory)
				sys.stdout.write("Download complete!\n")
				
				raw_input("Press Enter to continue wxPython installation (Ctrl+C to skip)")
				
				### install wx package form whl file
				pip.main(['install', whl_path])
				
				raw_input("Press Enter to to patch wxPython with the corrected plot.py file (Ctrl+C to skip)")
				
				### Add plot.py patched file
				from distutils.sysconfig import get_python_lib
		
				### download plot.py file
				url = 'https://raw.githubusercontent.com/capocchi/DEVSimPy-site/gh-pages/patched_files/plot.py'
				sys.stdout.write("Downloading plot.py patched file from DEVSimPy GitHub repository...\n")
				time_elapsed = downloadFile(url, temp_directory)
				sys.stdout.write("Download complete!\n")
		
				### new plot.py temp file
				new_plot_path = os.path.join(temp_directory, 'plot.py')
		
				### path of the wx lib that contain the plot.py file
				wx_path = os.path.join(get_python_lib(),'wx-3.0-msw','wx','lib')
		
				### try to remove the plot.py file that need to be replace by the patched plot.py file
				try:
					os.remove(os.path.join(wx_path, 'plot.py'))
				except Exception, info:
					sys.stdout.write("Error removing the plot.py file: %s\n"%info)
				else:
					### copy the patched plot.py file into the wx directory
					shutil.copy(new_plot_path, wx_path)
					sys.stdout.write("Patched plot.py file applied!\n")
		
				### delete temp file
				try:
					if os.path.exists(whl_path):
						os.remove(whl_path)
					if os.path.exists(new_plot_path):
						os.remove(new_plot_path)
				except Exception, info:
					sys.stdout.write("Error cleaning temp file: %s\n"%info)
				else:
					sys.stdout.write("Clean temp file complete!\n")
		
				### add wx-3.0-msw to the path and import it
				sys.path.append(os.path.join(get_python_lib(),'wx-3.0-msw'))
		
				import wx

		except ImportError, info:
			sys.stdout.write(info)
			sys.stdout.write("DEVSimPy requires the wx package, please install it.\n")
			sys.exit()

		else:
			if wx.VERSION_STRING < __min_wx_version__:
				sys.stdout.write("You need to updgarde wxPython to v%s (or higer) to run DEVSimPy\n"%__min_wx_version__)
				sys.stdout.write(__get__wxpython__)
				sys.exit()
import wx

sys.stdout.write("Importing wxPython %s%s for python %s on %s (%s) platform...\n"%(wx.version(), " from devsimpy.ini" if ini_exist else '', platform.python_version(), platform.system(), platform.version()))

try:
	import wx.aui as aui
except:
	import wx.lib.agw.aui as aui

import wx.py as py
import wx.lib.dialogs
import wx.html

#try:
#	import  wx.lib.floatbar
#except:
#	pass

try:
	from wx.lib.agw import advancedsplash
	AdvancedSplash = advancedsplash.AdvancedSplash
	old = False
except ImportError:
	AdvancedSplash = wx.SplashScreen
	old = True


# to send event
if wx.VERSION_STRING < '2.9':
	from wx.lib.pubsub import Publisher as pub
else:
	
	#from wx.lib.pubsub import setuparg1
	from wx.lib.pubsub import pub
 
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
builtin_dict = {'SPLASH_PNG': os.path.join(ABS_HOME_PATH, 'splash', 'splash.png'),
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
				'LOG_FILE': os.devnull, # log file (null by default)
				'DEFAULT_SIM_STRATEGY': 'bag-based', #choose the default simulation strategy for PyDEVS
				'PYDEVS_SIM_STRATEGY_DICT' : {'original':'SimStrategy1', 'bag-based':'SimStrategy2', 'direct-coupling':'SimStrategy3'}, # list of available simulation strategy for PyDEVS package
                'PYPDEVS_SIM_STRATEGY_DICT' : {'classic':'SimStrategy4', 'distributed':'SimStrategy5', 'parallel':'SimStrategy6'}, # list of available simulation strategy for PyPDEVS package
				'HELP_PATH' : os.path.join('doc', 'html'), # path of help directory
				'NTL' : False, # No Time Limit for the simulation
				'DYNAMIC_STRUCTURE' : False, # Dynamic Structure for local PyPDEVS simulation
				'REAL_TIME': False, ### PyPDEVS threaded real time simulation
				'VERBOSE':False,
				'TRANSPARENCY' : True, # Transparancy for DetachedFrame
				'DEFAULT_PLOT_DYN_FREQ' : 100, # frequence of dynamic plot of QuickScope (to avoid overhead),
				'DEFAULT_DEVS_DIRNAME':'PyDEVS', # default DEVS Kernel directory
				'DEVS_DIR_PATH_DICT':{'PyDEVS':os.path.join(ABS_HOME_PATH,'DEVSKernel','PyDEVS'),
									'PyPDEVS_221':os.path.join(ABS_HOME_PATH,'DEVSKernel','PyPDEVS','pypdevs221' ,'src'),
									'PyPDEVS_241':os.path.join(ABS_HOME_PATH,'DEVSKernel','PyPDEVS','pypdevs241' ,'src','pypdevs'),
									'PyPDEVS':os.path.join(ABS_HOME_PATH,'DEVSKernel','PyPDEVS','old')},
				'GUI_FLAG':True
				}

### here berfore the __main__ function
### warning, some module (like SimulationGUI) initialise GUI_FLAG macro before (import block below)
#builtin_dict['GUI_FLAG'] = False

# Sets the homepath variable to the directory where your application is located (sys.argv[0]).
__builtin__.__dict__.update(builtin_dict)

### import Container much faster loading than from Container import ... for os windows only
import Container
import Menu
import ReloadModule

from ImportLibrary import ImportLibrary
from Reporter import ExceptionHook
from PreferencesGUI import PreferencesGUI
from pluginmanager import load_plugins, enable_plugin
from which import which
from Utilities import GetMails, IsAllDigits, GetUserConfigDir
from Decorators import redirectStdout, BuzyCursorNotification
from DetachedFrame import DetachedFrame
from LibraryTree import LibraryTree
from LibPanel import LibPanel
from PropPanel import PropPanel
from ControlNotebook import ControlNotebook
from DiagramNotebook import DiagramNotebook
from Editor import GetEditor
from YAMLExportGUI import YAMLExportGUI
from wxPyMail import SendMailWx

### only for wx. 2.9 bug
### http://comments.gmane.org/gmane.comp.python.wxpython/98744
wx.Log.SetLogLevel(0)

#-------------------------------------------------------------------
def getIcon(path):
	""" Return icon from image path
	"""
	icon = wx.EmptyIcon() if wx.VERSION_STRING < '4.0' else wx.Icon()
	bmp = wx.Image(path).ConvertToBitmap()
	bmp.SetMask(wx.Mask(bmp, wx.WHITE))
	icon.CopyFromBitmap(bmp)
	return icon

#-------------------------------------------------------------------
def DefineScreenSize(percentscreen = None, size = None):
	"""Returns a tuple to define the size of the window
		percentscreen = float
	"""
	if not size and not percentscreen:
		percentscreen = 0.8
	if size:
		l, h = size
	elif percentscreen:
		x1, x2, l, h = wx.Display().GetClientArea()
		l, h = percentscreen * l, percentscreen * h
	return l, h

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

		wx.Frame.__init__(self, parent, wx.ID_ANY, title, size = DefineScreenSize(), style = wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE)

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
		pub.sendMessage('object.added',  message='Loading the libraries tree...\n')
		pub.sendMessage('object.added',  message='Loading the search tab on libraries tree...\n')

		# NoteBook
		self.nb1 = ControlNotebook(self, wx.ID_ANY, style = wx.CLIP_CHILDREN)
		self.tree = self.nb1.GetTree()
		self.searchTree = self.nb1.GetSearchTree()

		self._mgr.AddPane(self.nb1, aui.AuiPaneInfo().Name("nb1").Hide().Caption("Control").
                          FloatingSize(wx.Size(280, 400)).CloseButton(True).MaximizeButton(True))

		#------------------------------------------------------------------------------------------
		# Create a Notebook 2
		self.nb2 = DiagramNotebook(self, wx.ID_ANY, style = wx.CLIP_CHILDREN)

		### load .dsp or empty on empty diagram
		if len(sys.argv) >= 2:
			for arg in map(os.path.abspath, filter(lambda a :a.endswith('.dsp'), sys.argv[1:])):
				diagram = Container.Diagram()
				#diagram.last_name_saved = arg
				name = os.path.basename(arg)
				if not isinstance(diagram.LoadFile(arg), Exception):
					self.nb2.AddEditPage(os.path.splitext(name)[0], diagram)
		else:
			self.nb2.AddEditPage(_("Diagram%d"%Container.ShapeCanvas.ID))

		self._mgr.AddPane(self.nb2, aui.AuiPaneInfo().Name("nb2").CenterPane().Hide())

		# Simulation panel
		self.panel3 = wx.Panel(self.nb1, wx.ID_ANY, style = wx.WANTS_CHARS)
		self.panel3.SetBackgroundColour(wx.NullColour)
		self.panel3.Hide()

		#status bar avant simulation :-)
		self.MakeStatusBar()

		# Shell panel
		self.panel4 = wx.Panel(self, wx.ID_ANY, style=wx.WANTS_CHARS)
		sizer4 = wx.BoxSizer(wx.VERTICAL)
		sizer4.Add(py.shell.Shell(self.panel4, introText=_("Welcome to DEVSimPy: The GUI for Python DEVS Simulator")), 1, wx.EXPAND)
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
		""" Write config file
		"""

		# for spash screen
		pub.sendMessage('object.added',  message='Writing .devsimpy settings file...\n')

		sys.stdout.write("Writing default .devsimpy settings file on %s directory..."%GetUserConfigDir())

		self.exportPathsList = []					# export path list
		self.openFileList = ['']*NB_OPENED_FILE		#number of last opened files
		self.language = 'default'						# default language
		self.perspectives = {}

		# verison of the main (fo compatibility of DEVSimPy)
		cfg.Write('version', str(__version__))
		# list des chemins des librairies à importer
		cfg.Write('exportPathsList', str([]))
		# list de l'unique domain par defaut: Basic
		cfg.Write('ChargedDomainList', str([]))
		# list des 5 derniers fichier ouvert
		cfg.Write('openFileList', str(eval("self.openFileList")))
		cfg.Write('language', "'%s'"%str(eval("self.language")))
		cfg.Write('plugins', str("[]"))
		cfg.Write('perspectives', str(eval("self.perspectives")))
		cfg.Write('builtin_dict', str(eval("__builtin__.__dict__")))

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
				pub.sendMessage('object.added',  message='Loading .devsimpy settings file...\n')

				sys.stdout.write("Loading DEVSimPy %s settings file from %s.devsimpy\n"%(self.GetVersion(), GetUserConfigDir()+os.sep))

				### load external import path
				self.exportPathsList = filter(lambda path: os.path.isdir(path), eval(self.cfg.Read("exportPathsList")))
				### append external path to the sys module to futur import
				sys.path.extend(self.exportPathsList)

				### load recent files list
				self.openFileList = eval(self.cfg.Read("openFileList"))
				### update chargedDomainList
				chargedDomainList = filter(lambda path: path.startswith('http') or os.path.isdir(path), eval(self.cfg.Read('ChargedDomainList')))

				self.cfg.DeleteEntry('ChargedDomainList')
				self.cfg.Write('ChargedDomainList', str(eval('chargedDomainList')))
				### load language
				self.language = eval(self.cfg.Read("language"))

				### load perspective profile
				self.perspectives = eval(self.cfg.Read("perspectives"))

				### restore the builtin dict (just for )
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

				try:
					### recompile DomainInterface if DEFAULT_DEVS_DIRNAME != PyDEVS
					recompile = D['DEFAULT_DEVS_DIRNAME'] != __builtin__.__dict__['DEFAULT_DEVS_DIRNAME']
				except KeyError:
					recompile = False

				### test if the DEVSimPy source directory has been moved
				### if icon path exists, then we can update builtin from cfg
				if os.path.exists(D['ICON_PATH']):
					__builtin__.__dict__.update(D)
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
				for plugin in eval(self.cfg.Read("plugins")):
					load_plugins(plugin)
					enable_plugin(plugin)
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
		pub.sendMessage('object.added',  message='Loading locale configuration...\n')

		localedir = os.path.join(HOME_PATH, "locale")
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
		pub.sendMessage('object.added',  message='Making status bar...\n')

		self.statusbar = self.CreateStatusBar(1, wx.ST_SIZEGRIP if wx.VERSION_STRING < '4.0' else wx.STB_SIZEGRIP)
		self.statusbar.SetFieldsCount(3)
		self.statusbar.SetStatusWidths([-5, -2, -1])

	def MakeMenu(self):
		""" Make main menu.
		"""

		# for spash screen
		pub.sendMessage('object.added',  message='Making Menu ...\n')

		self.menuBar = Menu.MainMenuBar(self)
		self.SetMenuBar(self.menuBar)

		### commented before Phoenix transition 
		### bind menu that require update on open and close event (forced to implement the binding here !)
		for menu,title in filter(lambda c : re.search("(File|Fichier|Options)", c[-1]) != None, self.menuBar.GetMenus()):
			self.Bind(wx.EVT_MENU_OPEN, self.menuBar.OnOpenMenu)
			#self.Bind(wx.EVT_MENU_CLOSE, self.menuBar.OnCloseMenu)

	def MakeToolBar(self):
		""" Make main tools bar.
		"""

		# for spash screen
		pub.sendMessage('object.added',  message='Making tools bar ...\n')

		self.tb = self.CreateToolBar(style = wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT | wx.TB_TEXT, name = 'tb')

		self.toggle_list = [wx.NewId(), wx.NewId(), wx.NewId(), wx.NewId(), wx.NewId(), wx.NewId()]

		currentPage = self.nb2.GetCurrentPage()

		### Tools List - IDs come from Menu.py file
		if wx.VERSION_STRING < '4.0':
			self.tb.SetToolBitmapSize((25,25)) # juste for windows

			self.tools = [	self.tb.AddTool(wx.ID_NEW, wx.Bitmap(os.path.join(ICON_PATH,'new.png')), shortHelpString=_('New diagram (Ctrl+N)'),longHelpString=_('Create a new diagram in tab')),
							self.tb.AddTool(wx.ID_OPEN, wx.Bitmap(os.path.join(ICON_PATH,'open.png')), shortHelpString=_('Open File (Ctrl+O)'), longHelpString=_('Open an existing diagram')),
							self.tb.AddTool(wx.ID_PREVIEW_PRINT, wx.Bitmap(os.path.join(ICON_PATH,'print-preview.png')), shortHelpString=_('Print Preview (Ctrl+P)'), longHelpString=_('Print preview of current diagram')),
							self.tb.AddTool(wx.ID_SAVE, wx.Bitmap(os.path.join(ICON_PATH,'save.png')), shortHelpString=_('Save File (Ctrl+S)'), longHelpString=_('Save the current diagram'), clientData=currentPage),
							self.tb.AddTool(wx.ID_SAVEAS, wx.Bitmap(os.path.join(ICON_PATH,'save_as.png')), shortHelpString=_('Save file as'), longHelpString=_('Save the diagram with an another name'), clientData=currentPage),
							self.tb.AddTool(wx.ID_UNDO, wx.Bitmap(os.path.join(ICON_PATH,'undo.png')),shortHelpString= _('Undo'), longHelpString=_('Click to glongHelpString=o back, hold to see history'), clientData=currentPage),
							self.tb.AddTool(wx.ID_REDO, wx.Bitmap(os.path.join(ICON_PATH,'redo.png')), shortHelpString=_('Redo'), longHelpString=_('Click to go forward, hold to see history'), clientData=currentPage),
							self.tb.AddTool(Menu.ID_ZOOMIN_DIAGRAM, wx.Bitmap(os.path.join(ICON_PATH,'zoom+.png')), shortHelpString=_('Zoom'), longHelpString=_('Zoom +'), clientData=currentPage),
							self.tb.AddTool(Menu.ID_ZOOMOUT_DIAGRAM, wx.Bitmap(os.path.join(ICON_PATH,'zoom-.png')), shortHelpString=_('UnZoom'), longHelpString=_('Zoom -'), clientData=currentPage),
							self.tb.AddTool(Menu.ID_UNZOOM_DIAGRAM, wx.Bitmap(os.path.join(ICON_PATH,'no_zoom.png')), shortHelpString=_('AnnuleZoom'), longHelpString=_('Normal size'), clientData=currentPage),
							self.tb.AddTool(Menu.ID_PRIORITY_DIAGRAM, wx.Bitmap(os.path.join(ICON_PATH,'priority.png')), shortHelpString=_('Priority (F3)'),longHelpString= _('Define model activation priority')),
							self.tb.AddTool(Menu.ID_CHECK_DIAGRAM, wx.Bitmap(os.path.join(ICON_PATH,'check_master.png')), shortHelpString=_('Debugger (F4)'),longHelpString= _('Check devs models')),
							self.tb.AddTool(Menu.ID_SIM_DIAGRAM, wx.Bitmap(os.path.join(ICON_PATH,'simulation.png')), shortHelpString=_('Simulation (F5)'), longHelpString=_('Simulate the diagram')),
							self.tb.AddTool(self.toggle_list[0], wx.Bitmap(os.path.join(ICON_PATH,'direct_connector.png')),shortHelpString= _('Direct'),longHelpString=_('Direct connector'), isToggle=True),
							self.tb.AddTool(self.toggle_list[1], wx.Bitmap(os.path.join(ICON_PATH,'square_connector.png')), shortHelpString=_('Square'), longHelpString=_('Square connector'), isToggle=True),
							self.tb.AddTool(self.toggle_list[2], wx.Bitmap(os.path.join(ICON_PATH,'linear_connector.png')), shortHelpString=_('Linear'), longHelpString=_('Linear connector'), isToggle=True)
						]
		else:
			self.tools = [	self.tb.AddTool(wx.ID_NEW, "",wx.Bitmap(os.path.join(ICON_PATH,'new.png')), shortHelp=_('New diagram (Ctrl+N)')),
							self.tb.AddTool(wx.ID_OPEN, "",wx.Bitmap(os.path.join(ICON_PATH,'open.png')), shortHelp=_('Open File (Ctrl+O)')),
							self.tb.AddTool(wx.ID_PREVIEW_PRINT, "",wx.Bitmap(os.path.join(ICON_PATH,'print-preview.png')), shortHelp=_('Print Preview (Ctrl+P)')),
							self.tb.AddTool(wx.ID_SAVE, "",wx.Bitmap(os.path.join(ICON_PATH,'save.png')), wx.NullBitmap, shortHelp=_('Save File (Ctrl+S)'), longHelp=_('Save the current diagram'), clientData=currentPage),
							self.tb.AddTool(wx.ID_SAVEAS, "",wx.Bitmap(os.path.join(ICON_PATH,'save_as.png')), wx.NullBitmap, shortHelp=_('Save file as'), longHelp=_('Save the diagram with an another name'), clientData=currentPage),
							self.tb.AddTool(wx.ID_UNDO, "",wx.Bitmap(os.path.join(ICON_PATH,'undo.png')), wx.NullBitmap, shortHelp= _('Undo'), longHelp=_('Click to glongHelpString=o back, hold to see history'), clientData=currentPage),
							self.tb.AddTool(wx.ID_REDO, "",wx.Bitmap(os.path.join(ICON_PATH,'redo.png')), wx.NullBitmap, shortHelp=_('Redo'), longHelp=_('Click to go forward, hold to see history'), clientData=currentPage),
							self.tb.AddTool(Menu.ID_ZOOMIN_DIAGRAM, "",wx.Bitmap(os.path.join(ICON_PATH,'zoom+.png')), wx.NullBitmap, shortHelp=_('Zoom'), longHelp=_('Zoom +'), clientData=currentPage),
							self.tb.AddTool(Menu.ID_ZOOMOUT_DIAGRAM, "",wx.Bitmap(os.path.join(ICON_PATH,'zoom-.png')), wx.NullBitmap, shortHelp=_('UnZoom'), longHelp=_('Zoom -'), clientData=currentPage),
							self.tb.AddTool(Menu.ID_UNZOOM_DIAGRAM, "",wx.Bitmap(os.path.join(ICON_PATH,'no_zoom.png')), wx.NullBitmap, shortHelp=_('AnnuleZoom'), longHelp=_('Normal size'), clientData=currentPage),
							self.tb.AddTool(Menu.ID_PRIORITY_DIAGRAM, "",wx.Bitmap(os.path.join(ICON_PATH,'priority.png')), shortHelp=_('Priority (F3)')),
							self.tb.AddTool(Menu.ID_CHECK_DIAGRAM, "",wx.Bitmap(os.path.join(ICON_PATH,'check_master.png')), shortHelp=_('Debugger (F4)')),
							self.tb.AddTool(Menu.ID_SIM_DIAGRAM, "",wx.Bitmap(os.path.join(ICON_PATH,'simulation.png')), shortHelp=_('Simulation (F5)')),
							self.tb.AddTool(self.toggle_list[0], "",wx.Bitmap(os.path.join(ICON_PATH,'direct_connector.png')),shortHelp= _('Direct'), kind=wx.ITEM_CHECK),
							self.tb.AddTool(self.toggle_list[1], "",wx.Bitmap(os.path.join(ICON_PATH,'square_connector.png')), shortHelp=_('Square'), kind = wx.ITEM_CHECK),
							self.tb.AddTool(self.toggle_list[2], "",wx.Bitmap(os.path.join(ICON_PATH,'linear_connector.png')), shortHelp=_('Linear'), kind = wx.ITEM_CHECK)
						]

		##################################################################### Abstraction hierarchy
		diagram = currentPage.GetDiagram()
		level = currentPage.GetCurrentLevel()

		level_label = wx.StaticText(self.tb, -1, _("Level "))
		self.spin = wx.SpinCtrl(self.tb, self.toggle_list[3], str(level), (55, 90), (50, -1), min=0, max=10)

		self.tb.AddControl(level_label)
		self.tb.AddControl(self.spin)

		### add button to define downward and upward rules
		ID_UPWARD = self.toggle_list[4]
		ID_DOWNWARD = self.toggle_list[5]

		if wx.VERSION_STRING < '4.0':
			self.tools.append(self.tb.AddTool(ID_DOWNWARD, wx.Bitmap(os.path.join(ICON_PATH,'downward.png')), shortHelpString=_('Downward rules'), longHelpString=_('Define Downward atomic model')))
			self.tools.append(self.tb.AddTool(ID_UPWARD, wx.Bitmap(os.path.join(ICON_PATH,'upward.png')), shortHelpString=_('Upward rules'), longHelpString=_('Define Upward atomic model')))
		else:
			self.tools.append(self.tb.AddTool(ID_DOWNWARD, "", wx.Bitmap(os.path.join(ICON_PATH,'downward.png')), shortHelp=_('Downward rules')))
			self.tools.append(self.tb.AddTool(ID_UPWARD, "", wx.Bitmap(os.path.join(ICON_PATH,'upward.png')), shortHelp=_('Upward rules')))

		self.tb.EnableTool(ID_DOWNWARD, False)
		self.tb.EnableTool(ID_UPWARD, False)

		##############################################################################################

		self.tb.InsertSeparator(3)
		self.tb.InsertSeparator(8)
		self.tb.InsertSeparator(12)
		self.tb.InsertSeparator(16)
		self.tb.InsertSeparator(20)
		
		### undo and redo button desabled
		self.tb.EnableTool(wx.ID_UNDO, False)
		self.tb.EnableTool(wx.ID_REDO, False)
		self.tb.EnableTool(Menu.ID_PRIORITY_DIAGRAM, not 'PyPDEVS' in __builtin__.__dict__['DEFAULT_DEVS_DIRNAME'])

		### default direct connector toogled
		self.tb.ToggleTool(self.toggle_list[0], 1)

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
		self.Bind(wx.EVT_TOOL, self.OnSimulation, self.tools[12])
		self.Bind(wx.EVT_TOOL, self.OnDirectConnector, self.tools[13])
		self.Bind(wx.EVT_TOOL, self.OnSquareConnector, self.tools[14])
		self.Bind(wx.EVT_TOOL, self.OnLinearConnector, self.tools[15])

		##################################################################### Abstraction hierarchy
		self.Bind(wx.EVT_SPINCTRL, self.OnSpin, id=self.toggle_list[3])
		self.Bind(wx.EVT_TEXT, self.OnSpin, id=self.toggle_list[3])
		##############################################################################################

		self.Bind(wx.EVT_TOOL, self.OnUpWard, id=ID_UPWARD)
		self.Bind(wx.EVT_TOOL, self.OnDownWard, id=ID_DOWNWARD)

		self.tb.Realize()

	def GetExportPathsList(self):
		"""
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
		Container.ShapeCanvas.CONNECTOR_TYPE = 'direct'
		for id in self.toggle_list:
			toolbar.ToggleTool(id,0)
		toolbar.ToggleTool(event.GetId(),1)

	def OnSquareConnector(self, event):
		"""
		"""
		toolbar = event.GetEventObject()
		Container.ShapeCanvas.CONNECTOR_TYPE = 'square'
		for id in self.toggle_list:
			toolbar.ToggleTool(id,0)
		toolbar.ToggleTool(event.GetId(),1)

	def OnLinearConnector(self, event):
		"""
		"""
		toolbar = event.GetEventObject()
		Container.ShapeCanvas.CONNECTOR_TYPE = 'linear'
		for id in self.toggle_list:
			toolbar.ToggleTool(id,0)
		toolbar.ToggleTool(event.GetId(),1)

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
		self.tb.EnableTool(self.toggle_list[4], level != 0)
		self.tb.EnableTool(self.toggle_list[5], level != 0)

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
		dlg = wx.TextEntryDialog(self, _("Enter a new name:"), _("Perspective Manager"), _("Perspective %d")%(len(self.perspectives)))
		if dlg.ShowModal() == wx.ID_OK:
			txt = dlg.GetValue()

			if len(self.perspectives) == 0:
				self.perspectivesmenu.AppendSeparator()

			ID = wx.NewId()
			self.perspectivesmenu.Append(ID, txt)
			self.perspectives[txt] = self._mgr.SavePerspective()

			### Bind right away to make activable the perspective without restart DEVSimPy
			self.Bind(wx.EVT_MENU, self.OnRestorePerspective, id=ID)

	def OnRestorePerspective(self, event):
		"""
		"""
		id = event.GetId()
		item = self.GetMenuBar().FindItemById(id)
		mgr = self.GetMGR()
		mgr.LoadPerspective(self.perspectives[item.GetText()])

	def OnDeletePerspective(self, event):
		"""
		"""
		# delete all path items
		L = list(self.perspectivesmenu.GetMenuItems())
		for item in L[4:]:
			self.perspectivesmenu.RemoveItem(item)

		# update config file
		self.perspectives = {_("Default Startup"):self._mgr.SavePerspective()}
		self.cfg.Write("perspectives", str(eval("self.perspectives")))
		self.cfg.Flush()

	###
	def OnDragInit(self, event):

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
			self.cfg.Write("ChargedDomainList", str(filter(lambda k: self.tree.ItemDico[k] in L ,self.tree.ItemDico)))
			self.cfg.Flush()

			# save in config file the charged last external library directory
			#self.cfg.Write('exportPathsList', str(filter(lambda a: os.path.isdir(a), self.exportPathsList)))

	def SavePerspectiveProfile(self):
		""" Update the config file with the profile that are enabled during the last use of DEVSimPy
		"""
		# save in config file the last activated perspective
		self.cfg.Write("perspectives", str(self.perspectives))
		self.cfg.Flush()

	def SaveBuiltinDict(self):
		""" Save the specific builtin variable into the config file
		"""
		self.cfg.Write("builtin_dict", str(eval('dict((k, __builtin__.__dict__[k]) for k in builtin_dict)')))
		self.cfg.Flush()

	###
	def OnCloseWindow(self, event):
		""" Close icon has been pressed. Closing DEVSimPy.
		"""

		exit = False
		### for all pages, we invoke their OnClosePage function
		for i in xrange(self.nb2.GetPageCount()):

			### select the first page
			self.nb2.SetSelection(0)

			if not self.nb2.OnClosePage(event):
				exit = True
				break

		if not exit:
			### Save process
			self.SaveLibraryProfile()
			self.SavePerspectiveProfile()
			self.SaveBuiltinDict()
			self._mgr.UnInit()
			del self._mgr
			self.Destroy()

			#win = wx.Window_FindFocus()
			#if win != None:
				## Note: you really have to use wx.wxEVT_KILL_FOCUS
				## instead of wx.EVT_KILL_FOCUS here:
				#win.Disconnect(-1, -1, wx.wxEVT_KILL_FOCUS)
			#self.Destroy()

	def OnSpin(self, event):
    		""" Spin button has been invoked (on the toolbar of the main windows or detached frame)
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
		#print 'UAM%d'%cl, canvas.UAM[cl]
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
		home = os.getenv('USERPROFILE') or os.getenv('HOME') or HOME_PATH
		open_dlg = wx.FileDialog(self, message = _('Choose a file'), defaultDir = home, defaultFile = "", wildcard = wcd, style = wx.OPEN|wx.MULTIPLE|wx.CHANGE_DIR)

		### path,diagram dictionary
		new_paths = {}

		# get the new path from open file dialogue
		if open_dlg.ShowModal() == wx.ID_OK:

			### for selected paths
			for path in open_dlg.GetPaths():
				diagram = Container.Diagram()
				#diagram.last_name_saved = path

				### adding path with assocaited diagram
				new_paths[os.path.normpath(path)] = diagram

				open_dlg.Destroy()

		# load the new_path file with ConnectionThread function
		if new_paths != {}:

			for path,diagram in new_paths.items():

				fileName = os.path.basename(path)
				open_file_result = diagram.LoadFile(path)

				if isinstance(open_file_result, Exception):
					wx.MessageBox(_('Error opening file : %s')%str(open_file_result), 'Error', wx.OK | wx.ICON_ERROR)
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
		""" Print current diagram
		"""
		self.nb2.print_canvas = self.nb2.GetCurrentPage()
		self.nb2.print_size = self.nb2.GetSize()
		self.nb2.PrintButton(event)
	###
	def OnPrintPreview(self, event):
		""" Print preview of current diagram
		"""

		self.nb2.print_canvas = self.nb2.GetCurrentPage()
		self.nb2.print_size = self.nb2.GetSize()
		self.nb2.PrintPreview(event)
	###
	def OnScreenCapture(self, event):
		""" Print preview of current diagram
		"""

		try:
			import gtk.gdk
		except ImportError:
			id = event.GetId()
			menu = self.GetMenuBar().FindItemById(id).GetMenu()
			menuItem = menu.FindItemById(id)
			### enable the menu
			menuItem.Enable(False)
			sys.stdout.write(_("Unable to import gtk module.\n"))
		else:
			### dfault filename
			fn = "screenshot.png"

			#### filename dialog request
			dlg = wx.TextEntryDialog(self, _('Enter a new name:'),_('ScreenShot Filename'), fn)
			if dlg.ShowModal() == wx.ID_OK:
				fn = dlg.GetValue()
			dlg.Destroy()

			### screenshot
			w = gtk.gdk.get_default_root_window()
			sz = w.get_size()
			### "The size of the window is %d x %d" % sz
			pb = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, sz[0], sz[1])
			pb = pb.get_from_drawable(w,w.get_colormap(), 0, 0, 0, 0, sz[0], sz[1])
			### saving
			if (pb != None):
				ext = os.path.splitext(fn)[-1][1:]
				pb.save(fn, ext)
				wx.MessageBox(_("Screenshot saved in %s.")%fn, _("Success"), wx.OK|wx.ICON_INFORMATION)
			else:
				wx.MessageBox(_("Unable to get the screenshot."), _("Error"), wx.OK|wx.ICON_ERROR)
	###
	def OnUndo(self, event):
		""" Undo the diagram
		"""
		### get toolbar and clientData defined in AddTool
		toolbar = event.GetEventObject()
		currentPage = toolbar.GetToolClientData(event.GetId()) if isinstance(toolbar.GetParent(), DetachedFrame) else self.nb2.GetCurrentPage()

		### append the stockredo and active it
		currentPage.stockRedo.append(cPickle.dumps(obj=currentPage.GetDiagram(),protocol=0))
		toolbar.EnableTool(wx.ID_REDO, True)

		### change the current diagram with the last undo
		new_diagram = cPickle.loads(currentPage.stockUndo.pop())
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
		currentPage.stockUndo.append(cPickle.dumps(obj=currentPage.GetDiagram(), protocol=0))
		toolbar.EnableTool(wx.ID_UNDO, True)

		### change the current canvas with the last undo
		new_diagram = cPickle.loads(currentPage.stockRedo.pop())
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

		if isinstance(obj, wx.ToolBar) and isinstance(obj.GetParent(), DetachedFrame):
			currentPage = obj.GetToolClientData(event.GetId())
		else:
			currentPage = self.nb2.GetCurrentPage()

		### deselect all model to initialize select attribut for all models
		currentPage.deselect()

		diagram = currentPage.GetDiagram()

		### diagram preparation
		diagram.modify = False

		### save cmd file consists to export it
		if isinstance(diagram, Container.ContainerBlock):
			Container.Block.OnExport(diagram, event)
		else:
			if diagram.last_name_saved:

				assert(os.path.isabs(diagram.last_name_saved))

				if Container.Diagram.SaveFile(diagram, diagram.last_name_saved):
					# Refresh canvas
					currentPage.Refresh()

					### enable save button on status bar
					self.tb.EnableTool(Menu.ID_SAVE, diagram.modify)

					#self.statusbar.SetStatusText(_('%s saved')%diagram.last_name_saved)
				else:
					wx.MessageBox( _('Error saving file.') ,_('Error'), wx.OK | wx.ICON_ERROR)
			else:
				self.OnSaveAsFile(event)

	###
	def OnSaveAsFile(self, event):
		""" Save file menu as has been selected.
		"""

		obj = event.GetEventObject()
		if isinstance(obj, wx.ToolBar) and isinstance(obj.GetParent(), DetachedFrame):
			currentPage = obj.GetToolClientData(event.GetId())
		else:
			currentPage = self.nb2.GetCurrentPage()

		### deselect all model to initialize select attribut for all models
		currentPage.deselect()

		diagram = copy.deepcopy(currentPage.GetDiagram())

		### options building
		msg = "DEVSimPy files (*.dsp)|*.dsp|"
		if __builtin__.__dict__['YAML_IMPORT']:
			msg+="YAML files (*.yaml)|*.yaml|"
		msg+="XML files (*.xml)|*.xml|All files (*)|*)"

		wcd = _(msg)
		home = os.path.dirname(diagram.last_name_saved) or HOME_PATH
		save_dlg = wx.FileDialog(self, message=_('Save file as...'), defaultDir=home, defaultFile='', wildcard=wcd, style=wx.SAVE | wx.OVERWRITE_PROMPT)


		if save_dlg.ShowModal() == wx.ID_OK:
			path = os.path.normpath(save_dlg.GetPath())
			ext = os.path.splitext(path)[-1]
			file_name = save_dlg.GetFilename()
			wcd_i = save_dlg.GetFilterIndex()

			#ajoute de l'extention si abscente en fonction du wcd choisi (par defaut .dsp)
			if ext == '':
				if wcd_i == 0:
					path=''.join([path,'.dsp'])
				elif __builtin__.__dict__['YAML_IMPORT']:
					if wcd_i == 1:
						path=''.join([path,'.yaml'])
					elif wcd_i == 2:
						path=''.join([path,'.xml'])
				elif wcd_i == 1:
					path=''.join([path,'.xml'])

			### diagram preparation
			label = os.path.splitext(file_name)[0]
			diagram.LoadConstants(label)
			diagram.last_name_saved = path
			diagram.modify = False

			#sauvegarde dans le nouveau fichier
			if Container.Diagram.SaveFile(diagram, path):

				### if OnSaveAs invocked from DetahcedFrame, we update the title
				df = self.GetWindowByEvent(event)
				if isinstance(df, DetachedFrame):
					df.SetTitle(label)

				if diagram.last_name_saved == '':
					self.nb2.SetPageText(self.nb2.GetSelection(), label)
					currentPage.SetDiagram(diagram)
				else:
					self.nb2.AddEditPage(label, diagram)

				### enable save button on status bar
				self.tb.EnableTool(Menu.ID_SAVE, diagram.modify)
			else:
				wx.MessageBox(_('Error saving file.'), _('Error'), wx.OK | wx.ICON_ERROR)

		save_dlg.Destroy()

	###
	def OnExportRest(self, event):
		""" Export YAML file to the 'uplaod' directory of a REST server
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
	def OnImport(self, event):
		""" Import DEVSimPy library from Domain directory.
		"""

		# dialog pour l'importation de lib DEVSimPy (dans Domain) et le local
		dlg = ImportLibrary(self, wx.ID_ANY, _('New/Import Library manager'), size=(550,400), style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)

		if (dlg.ShowModal() == wx.ID_OK):

			num = dlg._cb.GetItemCount()
			for index in xrange(num):
				label = dlg._cb.GetItemText(index)

				### met a jour le dico des elements selectionnes
				if dlg._cb.IsChecked(index) and not dlg._selectedItem.has_key(label):
					dlg._selectedItem.update({str(label):index})
				elif not dlg._cb.IsChecked(index) and dlg._selectedItem.has_key(label):
					del dlg._selectedItem[str(label)]

			for s in dlg._selectedItem:

				absdName = str(os.path.join(DOMAIN_PATH, s)) if s not in dlg._d else str(dlg._d[s])
				progress_dlg = wx.ProgressDialog(_('Importing library'), _("Loading %s ...")%s, parent=self, style=wx.PD_APP_MODAL | wx.PD_ELAPSED_TIME)
				progress_dlg.Pulse()

    			### add correct path to sys.path (always before InsertNewDomain)
				LibraryTree.AddToSysPath(absdName)
    			### add NewDomain

				self.tree.InsertNewDomain(absdName, self.tree.GetRootItem(), self.tree.GetSubDomain(absdName, self.tree.GetDomainList(absdName)).values()[0])

				progress_dlg.Destroy()
				wx.SafeYield()

			self.tree.SortChildren(self.tree.GetRootItem())

		dlg.Destroy()

	###
	def OnSearch(self,evt):
		"""
		"""
		### search field
		search = evt.GetEventObject()

		# text taper par l'utilisateur
		text = search.GetValue()

		if text != '':

			#finded word list
			L = []

			#pour tout les parents qui n'ont pas de fils (bout de branche)
			for item in filter(lambda elem: not self.tree.ItemHasChildren(elem), self.tree.ItemDico.values()):
				path = self.tree.GetPyData(item)
				dirName = os.path.basename(path)

				### plus propre que la deuxieme solution (a tester dans le temps)
				if dirName.startswith(text):
					L.append(path)

			#masque l'arbre
			self.tree.Show(False)

			# Liste des domaines concernes
			if L != []:

				### on supprime l'ancien searchTree
				for item in self.searchTree.GetItemChildren(self.searchTree.GetRootItem()):
					self.searchTree.RemoveItem(item)

				### uniquify the list
				L = set(map(os.path.dirname, L))

				### construction du nouveau
				self.searchTree.Populate(L)

				### effacement des items qui ne correspondent pas
				for item in filter(lambda elem: not self.searchTree.ItemHasChildren(elem), copy.copy(self.searchTree.ItemDico).values()):
					path = self.searchTree.GetPyData(item)

					### si les path ne commence pas par le text entre par l'utilsiateur, on les supprime
					if not os.path.basename(path).startswith(text):
						self.searchTree.RemoveItem(item)

				self.searchTree.Show(True)
				nb1 = self.GetControlNotebook()
				nb1.libPanel.GetSizer().Layout()
				self.searchTree.ExpandAll()

			else:
				self.searchTree.Show(False)
		else:
			self.tree.Show(True)

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
		parent = self.GetWindowByEvent(event)
		diagram = self.GetDiagramByWindow(parent)
		return diagram.OnCheck(event)

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
		self.tb.Show(not self.tb.IsShown())

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
		""" Simulation profiling for fn file
		"""

		### find the prof file name
		menu_item = self.GetMenuBar().FindItemById(event.GetId())
		fn = menu_item.GetLabel()
		prof_file_path = os.path.join(gettempdir(), fn)

		### list of item in single choice dialogue
		choices = [_('Embedded in DEVSimPy')]

		### editor of profiling software
		try :
			kcachegrind = which('kcachegrind')
			choices.append('kcachegrind')
		except Exception:
			kcachegrind = False
		try:
			kprof = which('kprof')
			choices.append('kprof')
		except Exception:
			kprof = False
		try:
			converter = which('hotshot2calltree')
		except Exception:
			converter = False

		choices.append(_('Other...'))

		dlg = wx.SingleChoiceDialog(self, _('What profiling software are you using?'), _('Single Choice'), choices)
		if dlg.ShowModal() == wx.ID_OK:
			response = dlg.GetStringSelection()
			if response == 'kcachegrind':
				dlg.Destroy()

				if converter:
					### cache grind file name that will be generated
					cachegrind_fn = os.path.join(gettempdir(), "%s%s"%(fn[:-len('.prof')],'.cachegrind'))
					### transform profile file for cachegrind
					os.system("%s %s %s %s"%(converter,"-o", cachegrind_fn, prof_file_path))

					self.LoadCachegrindFile(cachegrind_fn)
				else:
					wx.MessageBox(_("Hotshot converter (hotshot2calltree) not found"), _('Error'), wx.OK|wx.ICON_ERROR)

			elif response == 'kprof':
				dlg.Destroy()
				self.LoadProfFileFromKProf(prof_file_path)
			elif response == _('Embedded in DEVSimPy'):
				dlg.Destroy()
				output = self.LoadProfFile(prof_file_path)
				d = wx.lib.dialogs.ScrolledMessageDialog(self, output, _("Statistic of profiling"), style=wx.OK|wx.ICON_EXCLAMATION|wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
				d.CenterOnParent(wx.BOTH)
				d.ShowModal()
			else:
				pass

	@staticmethod
	def LoadCachegrindFile(cachegrind_fn):
		### lauch  kcachegrid
		os.system(" ".join(['kcachegrind',cachegrind_fn,"&"]))

	@staticmethod
	def LoadProfFileFromKProf(prof_file_path):
		### lauch  kprof
		os.system(" ".join(['kprof',prof_file_path,"&"]))

	@staticmethod
	@redirectStdout
	def LoadProfFile(prof_file_path):
		### lauch embedded prof editor
		stats = hotshot.stats.load(prof_file_path)
		stats.strip_dirs()
		stats.sort_stats('time', 'calls')
		stats.print_stats(100)

	def OnDeleteProfiles(self, event):
		dlg = wx.MessageDialog(self, _('Do you realy want to delete all files ?'), _('Profile Manager'), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
		if dlg.ShowModal() == wx.ID_YES:
			tmp_dir = gettempdir()
			for fn in filter(lambda f: f.endswith(('.prof','.cachegrind')), os.listdir(tmp_dir)):
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

		## language config from .devsimpy file
		if self.language == 'default':
			lang = 'en'
		else:
			lang = eval('self.language')

		filename = os.path.join(HOME_PATH, 'doc', 'html', lang, 'Help.zip')
		if wx.VERSION_STRING >= '4.0':
			wx.FileSystem.AddHandler(wx.ZipFSHandler())     # add the Zip filesystem (only before HtmlHelpControler instance)
		else:
			wx.FileSystem.AddHandler(wx.ArchiveFSHandler())

		self.help = wx.html.HtmlHelpController()

		if not self.help.AddBook(filename, True):
			wx.MessageBox(_("Unable to open: %s")%filename, _("Error"), wx.OK|wx.ICON_ERROR)
		else:
			self.help.Display(os.path.join('html','toc.html'))

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
import/export DEVS components library and more.""")

		licence =_( """DEVSimPy is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the Free Software Foundation;
either version 2 of the License, or (at your option) any later version.

DEVSimPy is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU General Public License for more details. You should have received a copy of
the GNU General Public License along with File Hunter; if not, write to
the Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA""")

		info = wx.AboutDialogInfo()

		info.SetIcon(getIcon(os.path.join(ICON_PATH_16_16, SPLASH_PNG)))
		info.SetName('DEVSimPy')
		info.SetVersion(self.GetVersion())
		info.SetDescription(description)
		info.SetCopyright(_('(C) 2018 SISU Project - UMR CNRS 6134 SPE Lab.'))
		info.SetWebSite('http://www.spe.univ-corse.fr')
		info.SetLicence(licence)
		info.AddDeveloper(_('L. Capocchi.'))
		info.AddDocWriter(_('L. Capocchi.'))
		info.AddArtist(_('L. Capocchi.'))
		info.AddTranslator(_('L. Capocchi.'))

		wx.AboutBox(info)

	@BuzyCursorNotification
	def OnContact(self, event):
		""" Launches the mail program to contact the DEVSimPy author. """

		frame = SendMailWx()
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

		splashBmp = wx.Image(SPLASH_PNG).ConvertToBitmap()
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
			self.SetTextFont(wx.Font(9, wx.SWISS, wx.ITALIC, wx.NORMAL, False))
			self.SetTextColour("#797373")

		self.Bind(wx.EVT_CLOSE,self.OnClose)
		
		#if wx.VERSION_STRING < '4.0':
		self.fc = wx.FutureCall(500, self.ShowMain)
		#else:
		#self.fc = wx.CallLater(500, self.ShowMain)

		# for splash info
		try:
			pub.subscribe(self.OnObjectAdded, 'object.added')
		except TypeError:
			pub.subscribe(self.OnObjectAdded, data='object.added')

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

	def ShowMain(self):
		""" Shows the main application (DEVSimPy). """

		self.app.frame = MainApplication(None, wx.ID_ANY, 'DEVSimPy - Version %s'%__version__)

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
		wx.App.__init__(self, redirect, filename)

		# make sure we can create a GUI
		if not self.IsDisplayAvailable() and not __builtin__.__dict__['GUI_FLAG']:

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

		# to avoid conflict between the locale of the machine and the wx locale
		self.locale = wx.Locale(wx.LANGUAGE_DEFAULT)

		# start our application with splash
		splash = AdvancedSplashScreen(self)
		splash.Show()

		return True

	def SetExceptionHook(self):
		# Set up the exception handler...
		sys.excepthook = ExceptionHook

#-------------------------------------------------------------------
if __name__ == '__main__':

	import gettext
	_ = gettext.gettext

	### python devsimpy.py -c|-clean in order to delete the config file
	if len(sys.argv) >= 2 and sys.argv[1] in ('-c', '-clean'):
		config_file1 = os.path.join(GetUserConfigDir(), '.devsimpy')
		config_file2 = os.path.join(GetUserConfigDir(), 'devsimpy.ini')
		r = raw_input(_('Are you sure to delete DEVSimPy config files (.devsimpy and devsimpy.ini)? (Yes,No):'))
		if r in ('Y', 'y', 'yes', 'Yes', 'YES'):
			os.remove(config_file1)
			sys.stdout.write(_('%s has been deleted!\n')%config_file1)
			os.remove(config_file2)
			sys.stdout.write(_('%s has been deleted!\n')%config_file2)

		elif r in ('N','n','no', 'No'):
			pass
		else:
			pass
		sys.exit()
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
		sys.stdout.write(_('\t To execute DEVSimPy cleaner: python devsimpy.py -c|-clean\n'))
		sys.stdout.write(_('Authors: L. Capocchi (capocchi@univ-corse.fr)\n'))
		sys.exit()

	else:
		## si redirect=True et filename=None alors redirection dans une fenetre
		## si redirect=True et filename="fichier" alors redirection dans un fichier
		## si redirect=False redirection dans la console
		app = DEVSimPyApp(redirect = False, filename = None)
		app.MainLoop()
