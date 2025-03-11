# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# Menu.py ---
#                    --------------------------------
#                            Copyright (c) 2020
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 2.0                                        last modified: 03/15/20
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
import platform

from abc import ABC, abstractmethod
from tempfile import gettempdir

import Container

from PluginManager import PluginManager
from ExperimentGenerator import ExperimentGenerator
from Utilities import load_and_resize_image

_ = wx.GetTranslation

wx.NewId = wx.ID_ANY

#File menu identifiers
ID_NEW = wx.ID_NEW
ID_OPEN  = wx.ID_OPEN
ID_SAVE = wx.ID_SAVE
ID_SAVEAS = wx.ID_SAVEAS
ID_EXPORTREST = wx.NewIdRef()
ID_EXPORTSTANDALONE = wx.NewIdRef()
ID_IMPORTXMLSES = wx.NewIdRef()
ID_EXIT = wx.ID_EXIT
ID_ABOUT = wx.ID_ABOUT
ID_EXPORT = wx.NewIdRef()
ID_PREVIEW_PRINT = wx.ID_PREVIEW_PRINT
ID_SCREEN_CAPTURE = wx.NewIdRef()
ID_PRINT = wx.ID_PRINT
#ID_PAGE_SETUP = wx.NewIdRef()

# Recent file menu identifiers
ID_RECENT = wx.NewIdRef()
ID_DELETE_RECENT = wx.NewIdRef()

# Show menu identifiers
ID_SHOW_CONTROL = wx.NewIdRef()
ID_SHOW_SHELL = wx.NewIdRef()
ID_SHOW_SIM = wx.NewIdRef()
ID_SHOW_PROP = wx.NewIdRef()
ID_SHOW_LIB = wx.NewIdRef()
ID_SHOW_EDITOR = wx.NewIdRef()
ID_SHOW_TOOLBAR = wx.NewIdRef()


# Perspectives menu identifiers
ID_NEW_PERSPECTIVE = wx.NewIdRef()
ID_DELETE_PERSPECTIVE = wx.NewIdRef()
ID_FIRST_PERSPECTIVE = wx.NewIdRef()

# Diagram menu identifiers
ID_DETACH_DIAGRAM = wx.NewIdRef()
ID_RENAME_DIAGRAM = wx.NewIdRef()
ID_ZOOMIN_DIAGRAM = wx.ID_ZOOM_IN
ID_ZOOMOUT_DIAGRAM = wx.ID_ZOOM_OUT
ID_UNZOOM_DIAGRAM = wx.ID_ZOOM_100
ID_SIM_DIAGRAM = wx.NewIdRef()
ID_CHECK_DIAGRAM = wx.NewIdRef()
ID_CONST_DIAGRAM = wx.NewIdRef()
ID_PRIORITY_DIAGRAM = wx.NewIdRef()
ID_INFO_DIAGRAM = wx.NewIdRef()
ID_CLEAR_DIAGRAM = wx.NewIdRef()
ID_EXIT_DIAGRAM = wx.NewIdRef()

# Setting menu identifiers
ID_PREFERENCES = wx.NewIdRef()
ID_PROFILE = wx.NewIdRef()
ID_DELETE_PROFILES = wx.NewIdRef()
ID_FRENCH_LANGUAGE = wx.NewIdRef()
ID_ENGLISH_LANGUAGE = wx.NewIdRef()

# Help menu identifiers
ID_HELP = wx.ID_HELP
ID_API_HELP = wx.NewIdRef()
ID_UPDATE_PIP_PACKAGE = wx.NewIdRef()
ID_UPDATE_FROM_GIT_ARCHIVE = wx.NewIdRef()
ID_UPDATE_FROM_GIT_REPO = wx.NewIdRef()
ID_CONTACT = wx.NewIdRef()
ID_ABOUT = wx.ID_ABOUT

# Shape popup menu identifiers
ID_EDIT_SHAPE = wx.ID_EDIT
ID_LOG_SHAPE = wx.NewIdRef()
ID_RENAME_SHAPE = wx.NewIdRef()
ID_COPY_SHAPE = wx.ID_COPY
ID_PASTE_SHAPE = wx.ID_PASTE
ID_CUT_SHAPE = wx.ID_CUT
ID_ROTATE_ALL_SHAPE = wx.NewIdRef()
ID_ROTATE_INPUT_SHAPE = wx.NewIdRef()
ID_ROTATE_OUTPUT_SHAPE = wx.NewIdRef()
ID_ROTATE_SHAPE = wx.NewIdRef()
ID_RIGHT_ROTATE_SHAPE = wx.NewIdRef()
ID_LEFT_ROTATE_SHAPE = wx.NewIdRef()
ID_RIGHT_ROTATE_INPUT_SHAPE = wx.NewIdRef()
ID_LEFT_ROTATE_INPUT_SHAPE = wx.NewIdRef()
ID_RIGHT_ROTATE_OUTPUT_SHAPE = wx.NewIdRef()
ID_LEFT_ROTATE_OUTPUT_SHAPE = wx.NewIdRef()
ID_DELETE_SHAPE = wx.ID_DELETE
ID_LOCK_SHAPE = wx.NewIdRef()
ID_UNLOCK_SHAPE = wx.NewIdRef()
ID_ENABLE_SHAPE = wx.NewIdRef()
ID_DISABLE_SHAPE = wx.NewIdRef()
ID_EXPORT_SHAPE = wx.NewIdRef()
ID_EXPORT_AMD_SHAPE = wx.NewIdRef()
ID_EXPORT_CMD_SHAPE = wx.NewIdRef()
ID_EXPORT_XML_SHAPE = wx.NewIdRef()
ID_EXPORT_JS_SHAPE = wx.NewIdRef()
ID_PLUGINS_SHAPE = wx.NewIdRef()
ID_PROPERTIES_SHAPE = wx.ID_PROPERTIES
ID_EDIT_MODEL_SHAPE = wx.NewIdRef()
ID_TESTING_SHAPE = wx.NewIdRef()

# Shape canvas popup menu identifiers
ID_NEW_SHAPE = wx.NewIdRef()
ID_REFRESH_SHAPE = wx.NewIdRef()
ID_ADD_CONSTANTS = wx.NewIdRef()

# Experiment 
ID_GEN_EXPERIMENT = wx.NewIdRef()

# Stay on top
ID_STAY_ON_TOP = wx.NewIdRef()

# Library popup menu identifiers
ID_NEW_LIB = wx.NewIdRef()
ID_IMPORT_LIB = wx.NewIdRef()
ID_EDIT_LIB = wx.NewIdRef()
ID_RENAME_LIB = wx.NewIdRef()
ID_EXPORT_LIB = wx.NewIdRef()
ID_RENAME_DIR_LIB = wx.NewIdRef()
ID_REFRESH_LIB = wx.NewIdRef()
ID_MCC_LIB = wx.NewIdRef()
ID_UPGRADE_LIB = wx.NewIdRef()
ID_UPDATE_LIB = wx.NewIdRef()
ID_HELP_LIB = wx.NewIdRef()
ID_NEW_MODEL_LIB = wx.NewIdRef()
ID_NEW_DIR_LIB = wx.NewIdRef()
ID_UPDATE_SUBLIB = wx.NewIdRef()
ID_DELETE_LIB = wx.NewIdRef()

# Attribute popup menu identifiers
ID_EDIT_ATTR = wx.NewIdRef()
ID_INSERT_ATTR = wx.NewIdRef()
ID_CLEAR_ATTR = wx.NewIdRef()

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# FUNCTION DEFINITION
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

def AppendMenu(menu, ID, label, submenu):
	return menu.AppendSubMenu(submenu, label)

# def AppendItem(menu, item):
# 	return menu.Append(item)

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# CLASS DEFINITION
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

class Menu(ABC):
	def __init__(self, parent):
		"""Initialize the base Menu."""
		self.menu = wx.Menu()
		
		self.parent = parent

		# redifine AppendItem and AppendSeparator for wxPython 4.0 compatibility
		self.AppendItem = self.menu.Append
		self.AppendSeparator = self.menu.AppendSeparator

		# add items to the menu
		self._add_menu_items(parent)

	@abstractmethod
	def _add_menu_items(self, parent):
		"""Abstract method to add items to the menu."""
		pass

	def get(self):
		"""Return the encapsulated wx.Menu object."""
		return self.menu
	
class FileMenu(Menu):
	"""
	"""
	def __init__(self, parent):
		"""Initialize the FileMenu."""
		Menu.__init__(self, parent)
		
	def _add_menu_items(self, parent):

		openModel=wx.MenuItem(self.menu, ID_OPEN, _('&Open\tCtrl+O'),_('Open an existing diagram'))
		recentFile=wx.MenuItem(self.menu, ID_RECENT, _('Recent files'),_('Open recent files'))
		saveModel=wx.MenuItem(self.menu, ID_SAVE, _('&Save\tCtrl+S'), _('Save the current diagram'))
		saveAsModel=wx.MenuItem(self.menu, ID_SAVEAS, _('&SaveAs'),_('Save the diagram with a new name'))
		export = wx.MenuItem(self.menu, ID_EXPORT, _('&Export'),_('Export the current diagram'))
		importRest=wx.MenuItem(self.menu, ID_IMPORTXMLSES, _('&Import XML SES file'),_('Import SES specifications from the Python SES Editor'))
		printModel=wx.MenuItem(self.menu, ID_PRINT, _('&Print'),_('Print the current diagram'))
		printPreviewModel=wx.MenuItem(self.menu, ID_PREVIEW_PRINT, _('Preview'),_('Print preview for current diagram'))
		screenCapture=wx.MenuItem(self.menu, ID_SCREEN_CAPTURE, _('ScreenShot'),_('Capture the screen into an image'))
		exitModel=wx.MenuItem(self.menu, wx.ID_EXIT, _('&Quit\tCtrl+Q'),_('Quit the DEVSimPy application'))
		
		openModel.SetBitmap(load_and_resize_image('open.png'))
		recentFile.SetBitmap(load_and_resize_image('recent.png'))
		saveModel.SetBitmap(load_and_resize_image('save.png'))
		saveAsModel.SetBitmap(load_and_resize_image('save_as.png'))
		export.SetBitmap(load_and_resize_image('export.png'))
		importRest.SetBitmap(load_and_resize_image('import.png'))
		printModel.SetBitmap(load_and_resize_image('print.png'))
		printPreviewModel.SetBitmap(load_and_resize_image('print-preview.png'))
		screenCapture.SetBitmap(load_and_resize_image('ksnapshot.png'))
		exitModel.SetBitmap(load_and_resize_image('exit.png'))	
	
		self.AppendItem(openModel)
		recentFile.SetSubMenu(RecentFileMenu(parent).get())
		self.AppendItem(recentFile)
		self.AppendSeparator()

		self.AppendItem(saveModel)
		self.AppendItem(saveAsModel)
		self.AppendSeparator()
		
		export.SetSubMenu(ExportMenu(parent).get())
		self.AppendItem(export)
		self.AppendItem(importRest)
		self.AppendSeparator()
		
		self.AppendItem(printPreviewModel)
		self.AppendItem(printModel)
		self.AppendItem(screenCapture)
		self.AppendSeparator()

		self.AppendItem(exitModel)

		# bind the menu events to the methods that process them
		parent = parent.GetParent()
		parent.Bind(wx.EVT_MENU, parent.OnNew, id=ID_NEW)
		parent.Bind(wx.EVT_MENU, parent.OnOpenFile, id=ID_OPEN)
		parent.Bind(wx.EVT_MENU, parent.OnSaveFile, id=ID_SAVE)
		parent.Bind(wx.EVT_MENU, parent.OnSaveAsFile, id=ID_SAVEAS)
		parent.Bind(wx.EVT_MENU, parent.OnImportXMLSES, id=ID_IMPORTXMLSES)
		parent.Bind(wx.EVT_MENU, parent.OnPrint, id=ID_PRINT)
		parent.Bind(wx.EVT_MENU, parent.OnPrintPreview, id=ID_PREVIEW_PRINT)
		parent.Bind(wx.EVT_MENU, parent.OnScreenCapture, id=ID_SCREEN_CAPTURE)
		parent.Bind(wx.EVT_MENU, parent.OnCloseWindow, id=ID_EXIT)
	
class ProfileFileMenu(Menu):
	"""
	"""
	def __init__(self, parent):
		"""Initialize the FileMenu."""
		Menu.__init__(self, parent)
		
	def _add_menu_items(self, parent):

		parent = parent.GetParent()

		for fn in [f for f in os.listdir(os.path.realpath(gettempdir())) if f.endswith('.prof')]:
			id = wx.NewIdRef()
			self.AppendItem(wx.MenuItem(self.menu, id, fn))
			parent.Bind(wx.EVT_MENU, parent.OnProfiling, id=id)

		self.AppendSeparator()

		self.AppendItem(wx.MenuItem(self.menu, ID_DELETE_PROFILES, _("Delete all")))
		self.menu.Enable(ID_DELETE_PROFILES, self.menu.GetMenuItemCount() > 2)
		
		parent.Bind(wx.EVT_MENU, parent.OnDeleteProfiles, id=ID_DELETE_PROFILES)

class ExportMenu(Menu):
	"""
	"""
	def __init__(self, parent):
		"""Initialize the FileMenu."""
		Menu.__init__(self, parent)
		
	def _add_menu_items(self, parent):

		parent = parent.GetParent()
			
		exportRest=wx.MenuItem(self.menu, ID_EXPORTREST, _('To REST Server'),_('Export the diagram to a Rest server (DEVSimPy-rest)'))
		exportStandalone=wx.MenuItem(self.menu, ID_EXPORTSTANDALONE, _('To Standalone'),_('Generate a zip file which can be used to execute simulation of a yaml file in a no-gui and standaolne mode using devsimpy-nogui'))
		
		exportRest.SetBitmap(load_and_resize_image('api.png'))
		exportStandalone.SetBitmap(load_and_resize_image('zip.png'))

		self.AppendItem(exportRest)
		self.AppendItem(exportStandalone)

		parent.Bind(wx.EVT_MENU, parent.OnExportRest, id=ID_EXPORTREST)
		parent.Bind(wx.EVT_MENU, parent.OnExportStandalone, id=ID_EXPORTSTANDALONE)

class RecentFileMenu(Menu):
	"""
	"""
	def __init__(self, parent):
		"""Initialize the FileMenu."""
		Menu.__init__(self, parent)
		
	def _add_menu_items(self, parent):

		parent = parent.GetParent()
			
		# affichage du menu des derniers fichiers consultés avec gestion des fichiers qui n'existent plus
		for path in [p for p in parent.openFileList if p!='']:
			if not os.path.exists(path):
				index = parent.openFileList.index(path)
				del parent.openFileList[index]
				parent.openFileList.insert(-1,'')
				parent.cfg.Write("openFileList", str(eval("parent.openFileList")))
			else:
				newItem = wx.MenuItem(self.menu, wx.NewIdRef(), path)
				if path.endswith('.yaml'):
					img = load_and_resize_image('xml_file.png')
				elif path.endswith('.dsp'):
					img = load_and_resize_image('dsp_file.png')
				else:
					img = load_and_resize_image('file.png')
				newItem.SetBitmap(img)

				self.AppendItem(newItem)
				parent.Bind(wx.EVT_MENU, parent.OnOpenRecentFile, id = newItem.GetId())
				
		self.AppendSeparator()
		
		self.AppendItem(wx.MenuItem(self.menu, ID_DELETE_RECENT, _("Delete all")))
		self.menu.Enable(ID_DELETE_RECENT, self.menu.GetMenuItemCount() >= 2)
		
		parent.Bind(wx.EVT_MENU, parent.OnDeleteRecentFiles, id = ID_DELETE_RECENT)

class ShowMenu(Menu):
	"""
	"""
	def __init__(self, parent):
		"""Initialize the FileMenu."""
		Menu.__init__(self, parent)
		
	def _add_menu_items(self, parent):

		parent = parent.GetParent()

		control = wx.Menu()

		control.Append(ID_SHOW_SIM, _('Simulation'), _("Show simulation tab"), wx.ITEM_CHECK)
		control.Append(ID_SHOW_PROP, _('Properties'), _("Show properties tab"), wx.ITEM_CHECK)
		control.Append(ID_SHOW_LIB, _('Libraries'), _("Show libraries tab"), wx.ITEM_CHECK)
	
		AppendMenu(self.menu, ID_SHOW_CONTROL, _('Control'), control)

		self.menu.Append(ID_SHOW_SHELL, _('Shell'), _("Show Python Shell console"), wx.ITEM_CHECK)
		self.menu.Append(ID_SHOW_TOOLBAR, _('Tools Bar'), _("Show icons tools bar"), wx.ITEM_CHECK)
		self.menu.Append(ID_SHOW_EDITOR, _('Editor'), _("Show editor tab"), wx.ITEM_CHECK)

		self.menu.Check(ID_SHOW_SHELL, False)
		self.menu.Check(ID_SHOW_SIM, False)
		self.menu.Check(ID_SHOW_PROP, True)
		self.menu.Check(ID_SHOW_LIB, True)
		self.menu.Check(ID_SHOW_EDITOR, False)
		self.menu.Check(ID_SHOW_TOOLBAR, True)

		parent.Bind(wx.EVT_MENU, parent.OnShowShell, id = ID_SHOW_SHELL)
		parent.Bind(wx.EVT_MENU, parent.OnShowSimulation, id = ID_SHOW_SIM)
		parent.Bind(wx.EVT_MENU, parent.OnShowProperties, id = ID_SHOW_PROP)
		parent.Bind(wx.EVT_MENU, parent.OnShowLibraries, id = ID_SHOW_LIB)
		parent.Bind(wx.EVT_MENU, parent.OnShowEditor, id = ID_SHOW_EDITOR)
		parent.Bind(wx.EVT_MENU, parent.OnShowToolBar, id = ID_SHOW_TOOLBAR)

class PerspectiveMenu(Menu):
	"""
	"""
	def __init__(self, parent):
		"""Initialize the FileMenu."""
		Menu.__init__(self, parent)
		
	def _add_menu_items(self, parent):

		parent = parent.GetParent()

		new = wx.MenuItem(self.menu, ID_NEW_PERSPECTIVE, _('New'),_('New perspective'))
		new.SetBitmap(load_and_resize_image('new.png'))
		deleteall = wx.MenuItem(self.menu, ID_DELETE_PERSPECTIVE, _('Delete all'),_('Delete all perspectives'))
		deleteall.SetBitmap(load_and_resize_image('delete.png'))

		self.AppendItem(new)
		self.AppendItem(deleteall)
		self.AppendSeparator()

#		if _("Default Startup") not in parent.perspectives:
#			self.Append(ID_FIRST_PERSPECTIVE, _("Default Startup"))
#			parent.perspectives.update({_("Default Startup"):parent._mgr.SavePerspective()})

		### default perspective
		L = list(parent.perspectives.keys())
#		L.sort()
		for name in L:
			ID = wx.NewIdRef()
			self.menu.Append(ID, name)
			parent.Bind(wx.EVT_MENU, parent.OnRestorePerspective, id=ID)

		### Enable the delete function if the list of perspectives is not empty
		deleteall.Enable(len(L)> 1)

		parent.Bind(wx.EVT_MENU, parent.OnCreatePerspective, id=ID_NEW_PERSPECTIVE)
		parent.Bind(wx.EVT_MENU, parent.OnDeletePerspective, id=ID_DELETE_PERSPECTIVE)
		# parent.Bind(wx.EVT_MENU, parent.OnRestorePerspective, id=ID_FIRST_PERSPECTIVE)

class DiagramMenu(Menu):
	"""
	"""
	def __init__(self, parent):
		"""Initialize the FileMenu."""
		Menu.__init__(self, parent)
		
	def _add_menu_items(self, parent):

		parent = parent.GetParent()

		newDiagram = wx.MenuItem(self.menu, ID_NEW, _('New'), _("Create a new tab diagram"))
		detachDiagram = wx.MenuItem(self.menu, ID_DETACH_DIAGRAM, _('Detach'), _("Detach the tab to a frame window"))
		zoomIn = wx.MenuItem(self.menu, ID_ZOOMIN_DIAGRAM, _('Zoom'), _("Zoom in"))
		zoomOut = wx.MenuItem(self.menu, ID_ZOOMOUT_DIAGRAM, _('UnZoom'), _("Zoom out"))
		annuleZoom = wx.MenuItem(self.menu, ID_UNZOOM_DIAGRAM, _('AnnuleZoom'), _("Normal view"))
		checkDiagram = wx.MenuItem(self.menu, ID_CHECK_DIAGRAM, _('Debugger\tF4'), _("Check DEVS master model of diagram"))
		simulationDiagram = wx.MenuItem(self.menu, ID_SIM_DIAGRAM, _('&Simulate\tF5'), _("Perform the simulation"))
		constantsDiagram = wx.MenuItem(self.menu, ID_CONST_DIAGRAM, _('Add constants'), _("Loading constants parameters"))
		priorityDiagram = wx.MenuItem(self.menu, ID_PRIORITY_DIAGRAM, _('Priority\tF3'), _("Priority for select function"))
		infoDiagram = wx.MenuItem(self.menu, ID_INFO_DIAGRAM, _('Information'), _("Information about diagram (number of models, connections, etc)"))
		clearDiagram = wx.MenuItem(self.menu, ID_CLEAR_DIAGRAM, _('Clear'), _("Remove all components in diagram"))
		renameDiagram = wx.MenuItem(self.menu, ID_RENAME_DIAGRAM, _('Rename'), _("Rename diagram"))
		closeDiagram = wx.MenuItem(self.menu, ID_EXIT_DIAGRAM, _('&Close\tCtrl+D'), _("Close the tab"))

		newDiagram.SetBitmap(load_and_resize_image('new.png'))
		detachDiagram.SetBitmap(load_and_resize_image('detach.png'))
		zoomIn.SetBitmap(load_and_resize_image('zoom+.png'))
		zoomOut.SetBitmap(load_and_resize_image('zoom-.png'))
		annuleZoom.SetBitmap(load_and_resize_image('no_zoom.png'))
		checkDiagram.SetBitmap(load_and_resize_image('check_master.png'))
		simulationDiagram.SetBitmap(load_and_resize_image('simulation.png'))
		constantsDiagram.SetBitmap(load_and_resize_image('properties.png'))
		priorityDiagram.SetBitmap(load_and_resize_image('priority.png'))
		infoDiagram.SetBitmap(load_and_resize_image('info.png'))
		clearDiagram.SetBitmap(load_and_resize_image('delete.png'))
		renameDiagram.SetBitmap(load_and_resize_image('rename.png'))
		closeDiagram.SetBitmap(load_and_resize_image('close.png'))

		self.AppendItem(newDiagram)
		self.AppendItem(renameDiagram)
		self.AppendItem(detachDiagram)
		self.AppendSeparator()
		
		self.AppendItem(zoomIn)
		self.AppendItem(zoomOut)
		self.AppendItem(annuleZoom)
		self.AppendSeparator()
		
		self.AppendItem(checkDiagram)
		self.AppendItem(simulationDiagram)
		self.AppendItem(constantsDiagram)
		self.AppendItem(priorityDiagram)
		self.AppendItem(infoDiagram)
		self.AppendSeparator()
		
		self.AppendItem(clearDiagram)
		self.AppendSeparator()
		
		self.AppendItem(closeDiagram)

		# binding
		nb2 = parent.GetDiagramNotebook()
		parent.Bind(wx.EVT_MENU, parent.OnNew, id=ID_NEW)
		parent.Bind(wx.EVT_MENU, nb2.OnDetachPage, id=ID_DETACH_DIAGRAM)
		parent.Bind(wx.EVT_MENU, nb2.OnRenamePage, id=ID_RENAME_DIAGRAM)
		parent.Bind(wx.EVT_MENU, parent.OnCheck, id=ID_CHECK_DIAGRAM)
		parent.Bind(wx.EVT_MENU, parent.OnSimulation, id=ID_SIM_DIAGRAM)
		parent.Bind(wx.EVT_MENU, parent.OnConstantsLoading, id=ID_CONST_DIAGRAM)
		parent.Bind(wx.EVT_MENU, parent.OnPriorityGUI, id=ID_PRIORITY_DIAGRAM)
		parent.Bind(wx.EVT_MENU, parent.OnInfoGUI, id=ID_INFO_DIAGRAM)
		parent.Bind(wx.EVT_MENU, nb2.OnClearPage, id=ID_CLEAR_DIAGRAM)
		parent.Bind(wx.EVT_MENU, parent.OnZoom, id=ID_ZOOMIN_DIAGRAM)
		parent.Bind(wx.EVT_MENU, parent.OnUnZoom, id=ID_ZOOMOUT_DIAGRAM)
		parent.Bind(wx.EVT_MENU, parent.AnnuleZoom, id=ID_UNZOOM_DIAGRAM)
		parent.Bind(wx.EVT_MENU, nb2.OnClosePage, id=ID_EXIT_DIAGRAM)

class SettingsMenu(Menu):
	"""
	"""
	def __init__(self, parent):
		"""Initialize the FileMenu."""
		Menu.__init__(self, parent)
		
	def _add_menu_items(self, parent):

		languagesSubmenu = wx.Menu()
	
		pref_item = wx.MenuItem(self.menu, ID_PREFERENCES, _('Preferences'), _("Advanced setting options"))
		fritem = wx.MenuItem(languagesSubmenu, ID_FRENCH_LANGUAGE, _('French'), _("French interface"))
		enitem = wx.MenuItem(languagesSubmenu, ID_ENGLISH_LANGUAGE, _('English'), _("English interface"))

		pref_item.SetBitmap(load_and_resize_image('preferences.png'))
		fritem.SetBitmap(load_and_resize_image('french-flag.png'))
		enitem.SetBitmap(load_and_resize_image('united-states-flag.png'))

		languagesSubmenu.Append(fritem)
		languagesSubmenu.Append(enitem)
	
		AppendMenu(self.menu, wx.NewIdRef(), _('Languages'), languagesSubmenu)
		
		### Before Phoenix transition
		AppendMenu(self.menu, ID_PROFILE, _('Profile'), ProfileFileMenu(parent).get())

		self.AppendItem(pref_item)

		parent = parent.GetParent()

		fritem.Enable(not parent.language == 'fr')
		enitem.Enable(not parent.language == 'en')

		parent.Bind(wx.EVT_MENU, parent.OnFrench, id=ID_FRENCH_LANGUAGE)
		parent.Bind(wx.EVT_MENU, parent.OnEnglish, id=ID_ENGLISH_LANGUAGE)
		parent.Bind(wx.EVT_MENU, parent.OnAdvancedSettings, id=ID_PREFERENCES)
	
class HelpMenu(Menu):
	"""
	"""
	def __init__(self, parent):
		"""Initialize the FileMenu."""
		Menu.__init__(self, parent)
		
	def _add_menu_items(self, parent):
		
		helpModel = wx.MenuItem(self.menu, ID_HELP, _('&DEVSimPy Help\tF1'), _("Help for DEVSimPy user"))
		apiModel = wx.MenuItem(self.menu, ID_API_HELP, _('&DEVSimPy API\tF2'), _("API for DEVSimPy user")) 
		updatePipPackage = wx.MenuItem(self.menu, ID_UPDATE_PIP_PACKAGE, _('All Dependencies (PIP Packages)\tF3'), _("Update of dependant pip packages"))
		updateFromGitArchive = wx.MenuItem(self.menu, ID_UPDATE_FROM_GIT_ARCHIVE, _('DEVSimPy From Git Archive (zip)'), _("Update of DEVSimPy from Git archive"))
		updateFromGitRepo = wx.MenuItem(self.menu, ID_UPDATE_FROM_GIT_REPO, _('DEVSimPy From Git Repository (Pull)'), _("Update of DEVSimPy from its Git repo"))
		contactModel = wx.MenuItem(self.menu, ID_CONTACT, _('Contact the Author...'), _("Send mail to the author"))
		aboutModel = wx.MenuItem(self.menu, ID_ABOUT, _('About DEVSimPy...'), _("About DEVSimPy"))

		helpModel.SetBitmap(load_and_resize_image('search.png'))
		updatePipPackage.SetBitmap(load_and_resize_image('update.png'))
		updateFromGitArchive.SetBitmap(load_and_resize_image('zip.png'))
		updateFromGitRepo.SetBitmap(load_and_resize_image('git.png'))
		apiModel.SetBitmap(load_and_resize_image('api.png'))
		contactModel.SetBitmap(load_and_resize_image('mail.png'))
		aboutModel.SetBitmap(load_and_resize_image('info.png'))

		self.AppendItem(helpModel)
		self.AppendItem(apiModel)
		self.AppendSeparator()

		update_subMenu = wx.Menu()
		AppendMenu(self.menu, -1, _("Update"), update_subMenu)
		update_subMenu.Append(updatePipPackage)
		update_subMenu.AppendSeparator()
		
		update_subMenu.Append(updateFromGitArchive)
		update_subMenu.Append(updateFromGitRepo)
		self.AppendSeparator()
		
		self.AppendItem(aboutModel)
		self.AppendItem(contactModel)

		parent = parent.GetParent()

		parent.Bind(wx.EVT_MENU, parent.OnHelp, id=ID_HELP)
		parent.Bind(wx.EVT_MENU, parent.OnAPI, id=ID_API_HELP)
		parent.Bind(wx.EVT_MENU, parent.OnUpdatPiPPackage, id=ID_UPDATE_PIP_PACKAGE)
		parent.Bind(wx.EVT_MENU, parent.OnUpdatFromGitRepo, id=ID_UPDATE_FROM_GIT_REPO)
		parent.Bind(wx.EVT_MENU, parent.OnUpdatFromGitArchive, id=ID_UPDATE_FROM_GIT_ARCHIVE)
		parent.Bind(wx.EVT_MENU, parent.OnAbout, id=ID_ABOUT)
		parent.Bind(wx.EVT_MENU, parent.OnContact, id=ID_CONTACT)

class MainMenuBar(wx.MenuBar):
	"""
	"""
	def __init__(self, parent):
		""" Constructor.
		"""
		wx.MenuBar.__init__(self)

		self.parent = parent

		self.Append(FileMenu(self).get(),_("&File"))
		self.Append(DiagramMenu(self).get(),_("&Diagram"))
		self.Append(ShowMenu(self).get(), _("&Show"))
		self.parent.perspectivesmenu = PerspectiveMenu(self).get()
		self.Append(self.parent.perspectivesmenu, _("&Perspectives"))
		self.Append(SettingsMenu(self).get(), _("&Options"))
		self.Append(HelpMenu(self).get(), _("&Help"))

		self.Bind(wx.EVT_MENU_HIGHLIGHT, self.OnMenuHighlight)

	### useless until Phoenix transition
	def OnOpenMenu(self, event):
		""" Open menu has been detected.

			Add the recent files menu updated from recentFiles list
		"""
		
		menu = event.GetMenu()

		if menu:
			posm = self.FindMenu(menu.GetTitle())

			### if the opened menu is the File menu
			if isinstance(menu, FileMenu):
						
				if platform.system() == 'Windows':
					### After Pnoenix Transition
					self.Replace(posm, FileMenu(self), _("&File"))
				else:
					label = _("Recent files")
					ID = menu.FindItem(label)
					item, pos = menu.FindChildItem(ID)
					menu.Remove(ID)
					menu.Insert(pos, ID, label, RecentFileMenu(self).get())

			elif isinstance(menu, SettingsMenu):
			
				### After Pnoenix Transition
				if platform.system() == 'Windows':
					self.Replace(posm, SettingsMenu(self), _("&Options"))
				else:
					label = _('Profile')
					ID = menu.FindItem(label)
					item, pos = menu.FindChildItem(ID)
					menu.Remove(ID)
					menu.Insert(pos, ID, label, ProfileFileMenu(self).get())

					
	#def OnCloseMenu(self, event):
		#""" Close menu has been detected
		#"""

		#menu = event.GetEventObject()

		#### if the closed menu is FileMenu, we delete the recent menu
		#if isinstance(menu, FileMenu):
			#wx.CallAfter(menu.Delete, ID_RECENT)
		#elif isinstance(event.GetEventObject(), SettingsMenu):
			#wx.CallAfter(menu.Delete, ID_PROFILE)

	####
	def OnMenuHighlight(self, event):
		# Show how to get menu item info from this event handler
#		id = event.GetMenuId()
#		item = self.FindItemById(id)
#		if item:
#			text = item.GetText()
#			help = item.GetHelp()

		# but in this case just call Skip so the default is done
		event.Skip()

	def GetParent(self):
		return self.parent

class DiagramNoTabPopupMenu(Menu):
	""" Diagram noteBook popup menu
	"""

	def __init__(self, parent):
		"""Initialize the FileMenu."""
		Menu.__init__(self, parent)
		
	def _add_menu_items(self, parent):

		new_tab = wx.MenuItem(self.menu, ID_NEW, _('New'), _("Create a new tab diagram"))
		new_tab.SetBitmap(load_and_resize_image('new.png'))

		self.AppendItem(new_tab)

		### Bind is not necessary because ID_EXIT_DAIGRAM and ID_DETACH_DIAGRAM are already binded

class DiagramTabPopupMenu(Menu):
	""" Diagram noteBook popup menu
	"""

	def __init__(self, parent):
		"""Initialize the FileMenu."""
		Menu.__init__(self, parent)
		
	def _add_menu_items(self, parent):

		close = wx.MenuItem(self.menu, ID_EXIT_DIAGRAM, _('Close'), _('Close diagram'))
		detach = wx.MenuItem(self.menu, ID_DETACH_DIAGRAM, _('Detach'), _('Detach tab to window'))
		rename = wx.MenuItem(self.menu, ID_RENAME_DIAGRAM, _('Rename'), _('Rename diagram'))
		info = wx.MenuItem(self.menu, ID_INFO_DIAGRAM, _('Info'), _('Information diagram'))
		clear = wx.MenuItem(self.menu, ID_CLEAR_DIAGRAM, _('Clear'), _('Clear diagram'))

		close.SetBitmap(load_and_resize_image('close.png'))
		detach.SetBitmap(load_and_resize_image('detach.png'))
		rename.SetBitmap(load_and_resize_image('rename.png'))
		info.SetBitmap(load_and_resize_image('info.png'))
		clear.SetBitmap(load_and_resize_image('delete.png'))

		self.AppendItem(detach)
		self.AppendItem(rename)
		self.AppendItem(clear)
		self.AppendItem(info)
		self.AppendSeparator()
		self.AppendItem(close)
		
		### Bind is not necessary because ID_EXIT_DAIGRAM and ID_DETACH_DIAGRAM are already binded
class NodePopupMenu(Menu):
	""" Node popup menu
	"""

	def __init__(self, parent):
		"""Initialize the FileMenu."""
		Menu.__init__(self, parent)
		
	def _add_menu_items(self, parent):

		edit_label = wx.MenuItem(self.menu, -1, _('Edit'), _('Edit label'))
		edit_label.SetBitmap(load_and_resize_image('label.png'))
		
		self.AppendItem(edit_label)

		### bind event with new OnEditLabel
		self.menu.Bind(wx.EVT_MENU, parent.OnEditLabel, edit_label)
		self.menu.Bind(wx.EVT_MENU, parent.OnEditLabel, edit_label)

class PropertiesCtrlPopupMenu(wx.Menu):
	""" PropertiesCtrl popup menu.
	"""

	def __init__(self, parent, row, col, pos):
		""" Constructor.
		"""
		wx.Menu.__init__(self)

		self.parent = parent
		self.row = row
		self.col = col
		self.pos = pos

		edit = wx.MenuItem(self, ID_EDIT_ATTR, _('Edit'), _('Edit attribute'))
		insert = wx.MenuItem(self, ID_INSERT_ATTR, _('Insert'), _('Insert attribute'))
		clear = wx.MenuItem(self, ID_CLEAR_ATTR, _('Clear'), _('Clear value'))
		
		edit.SetBitmap(load_and_resize_image('edit.png'))
		insert.SetBitmap(load_and_resize_image('insert.png'))
		clear.SetBitmap(load_and_resize_image('edit_clear.png'))

		self.Append(edit)
		self.Append(insert)
		self.AppendSeparator()
		self.Append(clear)

		parent.Bind(wx.EVT_MENU, parent.OnEditCell, id=ID_EDIT_ATTR)
		parent.Bind(wx.EVT_MENU, parent.OnInsertCell, id=ID_INSERT_ATTR)
		parent.Bind(wx.EVT_MENU, parent.OnClearCell, id=ID_CLEAR_ATTR)

	def GetRow(self):
		return self.row

	def GetCol(self):
		return self.col

	def GetPosition(self):
		return self.pos
	
class ItemLibraryPopupMenu(Menu):
	""" Item library popup menu.
	"""

	def __init__(self, parent):
		"""Initialize the FileMenu."""
		Menu.__init__(self, parent)
		
	def _add_menu_items(self, parent):

		### last child of tree and not empty directory (then, has OnDocumentation method)

		item = parent.GetSelection()
		path = parent.GetItemPyData(item)

		if os.path.isdir(path):

			new_submenu = wx.Menu()

			new_model = wx.MenuItem(new_submenu, ID_NEW_MODEL_LIB, _('Model'), _('Add a new model to the selected library'))
			new_dir = wx.MenuItem(new_submenu, ID_NEW_DIR_LIB, _('Sub-directory'), _('Add a new sub directory to the selected library'))
			rename_dir = wx.MenuItem(self.menu, ID_RENAME_DIR_LIB, _('Rename'), _('Rename selected librarie'))
			update_lib = wx.MenuItem(self.menu, ID_UPDATE_SUBLIB, _('Update'), _('Update all models of the selected library'))
			doc = wx.MenuItem(self.menu, wx.NewIdRef(), _('Documentation'), _('Documentation of selected library'))

			new_model.SetBitmap(load_and_resize_image('new.png'))
			new_dir.SetBitmap(load_and_resize_image('new.png'))
			rename_dir.SetBitmap(load_and_resize_image('rename.png'))
			update_lib.SetBitmap(load_and_resize_image('reload.png'))
			doc.SetBitmap(load_and_resize_image('doc.png'))

			new_submenu.Append(new_model)
			new_submenu.Append(new_dir)
			AppendMenu(self.menu, -1, _('Add'), new_submenu)
			
			self.AppendItem(rename_dir)
			self.AppendItem(update_lib)
			self.AppendItem(doc)

			self.menu.Bind(wx.EVT_MENU, parent.OnNewModel, id=ID_NEW_MODEL_LIB)
			self.menu.Bind(wx.EVT_MENU, parent.OnDirRename, id=ID_RENAME_DIR_LIB)
			self.menu.Bind(wx.EVT_MENU, parent.OnNewDir, id=ID_NEW_DIR_LIB)
			self.menu.Bind(wx.EVT_MENU, parent.OnUpdateSubLib, id=ID_UPDATE_SUBLIB)	
			self.menu.Bind(wx.EVT_MENU, parent.OnLibDocumentation, id = doc.GetId())	# put before the popUpMenu

		else:

			edit = wx.MenuItem(self.menu, ID_EDIT_LIB, _('Edit'), _('Edit selected module'))
			rename = wx.MenuItem(self.menu, ID_RENAME_LIB, _('Rename'), _('Rename selected module'))
			export = wx.MenuItem(self.menu, ID_EXPORT_LIB, _('Export'), _('Rename selected module'))
			doc = wx.MenuItem(self.menu, wx.NewIdRef(), _('Documentation'), _('Documentation of selected library'))
			update = wx.MenuItem(self.menu, ID_UPDATE_LIB, _('Update'), _('Update selected module'))

			edit.SetBitmap(load_and_resize_image('edit.png'))
			rename.SetBitmap(load_and_resize_image('rename.png'))
			export.SetBitmap(load_and_resize_image('export.png'))
			doc.SetBitmap(load_and_resize_image('doc.png'))
			update.SetBitmap(load_and_resize_image('reload.png'))

			self.AppendItem(edit)
			self.AppendItem(rename)
			self.AppendItem(export)
			self.AppendItem(doc)
			self.AppendItem(update)

			path = parent.GetItemPyData(item)
			self.menu.Enable(ID_EDIT_LIB, not path.endswith('pyc'))
			
			self.menu.Bind(wx.EVT_MENU, parent.OnItemEdit, id = ID_EDIT_LIB)	# put before the popUpMenu
			self.menu.Bind(wx.EVT_MENU, parent.OnItemRename, id = ID_RENAME_LIB)	# put before the popUpMenu
			self.menu.Bind(wx.EVT_MENU, parent.OnItemExport, id = ID_EXPORT_LIB)	# put before the popUpMenu
			self.menu.Bind(wx.EVT_MENU, parent.OnItemDocumentation, id = doc.GetId())	# put before the popUpMenu
			self.menu.Bind(wx.EVT_MENU, parent.OnItemRefresh, id = ID_UPDATE_LIB)	# put before the popUpMenu

		### menu for all item of tree
		delete = wx.MenuItem(self.menu, ID_DELETE_LIB, _('Delete'), _('Delete selected library'))
		delete.SetBitmap(load_and_resize_image('delete.png'))

		self.AppendItem(delete)

		self.menu.Bind(wx.EVT_MENU, parent.OnDelete, id=ID_DELETE_LIB) # put before the popUpMenu

class LibraryPopupMenu(Menu):
	""" Popup menu for panel library.
	"""

	def __init__(self, parent):
		"""Initialize the FileMenu."""
		Menu.__init__(self, parent)
		
	def _add_menu_items(self, parent):

		new = wx.MenuItem(self.menu, ID_NEW_LIB, _('New/Import'), _('Create or import library'))
		refresh = wx.MenuItem(self.menu, ID_REFRESH_LIB, _('Reload'), _('Reload library'))
		#upgrade = wx.MenuItem(self, ID_UPGRADE_LIB, _('Upgrade'), _('Upgrade library'))
		info = wx.MenuItem(self.menu, ID_HELP_LIB, _('Help'), _('Library description'))

		new.SetBitmap(load_and_resize_image('plus.png'))
		refresh.SetBitmap(load_and_resize_image('reload.png'))
		#upgrade.SetBitmap(load_and_resize_image('upgrade.png'))
		info.SetBitmap(load_and_resize_image('info.png'))

		self.AppendItem(new)
		self.AppendItem(refresh)
		#self.AppendItem(upgrade)
		self.AppendSeparator()
		
		self.AppendItem(info)

		mainW = parent.GetTopLevelParent()

		self.menu.Bind(wx.EVT_MENU, mainW.OnImport, id= ID_NEW_LIB)
		self.menu.Bind(wx.EVT_MENU, parent.OnInfo, id=ID_HELP_LIB)
		self.menu.Bind(wx.EVT_MENU, parent.OnUpdateAll, id=ID_REFRESH_LIB)

class ShapeCanvasPopupMenu(Menu):
	""" ShapeCanvas menu class.
	"""

	def __init__(self, parent):
		"""Initialize the FileMenu."""
		Menu.__init__(self, parent)
		
	def _add_menu_items(self, parent):

		
		### make all items
		new = wx.MenuItem(self.menu, ID_NEW_SHAPE, _('&New'), _('New model'))
		refresh = wx.MenuItem(self.menu, ID_REFRESH_SHAPE, _('&Refresh'), _('Refresh model'))
		paste = wx.MenuItem(self.menu, wx.NewIdRef(), _('&Paste\tCtrl+V'), _('Paste the model'))
		add_constants = wx.MenuItem(self.menu, ID_ADD_CONSTANTS, _('Add constants'), _('Add constants parameters'))
		preview_dia = wx.MenuItem(self.menu, ID_PREVIEW_PRINT, _('Print preview'), _('Print preveiw of the diagram'))

		### Experiment generation
		generate_experiment = wx.MenuItem(self.menu, ID_GEN_EXPERIMENT, _('Generate PyPDEVS Experiment File'), _('Generate experiment model for PyPDEVS'))

		### bitmap item setting
		new.SetBitmap(load_and_resize_image('new_model.png'))
		refresh.SetBitmap(load_and_resize_image('reload.png'))
		paste.SetBitmap(load_and_resize_image('paste.png'))
		add_constants.SetBitmap(load_and_resize_image('properties.png'))
		preview_dia.SetBitmap(load_and_resize_image('print-preview.png'))
		generate_experiment.SetBitmap(load_and_resize_image('generation.png'))
	
		### append items
		self.AppendItem(new)
		self.AppendItem(refresh)
		self.AppendItem(paste)
		self.AppendItem(add_constants)
		self.AppendItem(preview_dia)
		self.AppendItem(generate_experiment)

		### Stay on top always for the detached frame (not for diagram into devsimpy as tab of notebook)
		if isinstance(self.parent.parent, wx.Frame):
			if self.parent.parent.GetWindowStyle() == self.parent.parent.default_style:
				stay_on_top = wx.MenuItem(self.menu, ID_STAY_ON_TOP, _('Enable stay on top'), _('Coupled model frame stay on top'))
				stay_on_top.SetBitmap(load_and_resize_image('pin_out.png'))
			else:
				stay_on_top = wx.MenuItem(self.menu, ID_STAY_ON_TOP, _('Disable stay on top'), _('Coupled model frame not stay on top'))
				stay_on_top.SetBitmap(load_and_resize_image('pin_in.png'))

			self.AppendItem(stay_on_top)
			parent.Bind(wx.EVT_MENU, parent.parent.OnStayOnTop, id=ID_STAY_ON_TOP)

		self.menu.Enable(paste.GetId(), Container.clipboard != [])

		### binding
		parent.Bind(wx.EVT_MENU, parent.OnNewModel, id=ID_NEW_SHAPE)
		parent.Bind(wx.EVT_MENU, parent.OnRefreshModels, id=ID_REFRESH_SHAPE)
		parent.Bind(wx.EVT_MENU, parent.OnPaste, id=paste.GetId())
		parent.Bind(wx.EVT_MENU, parent.diagram.OnAddConstants, id=ID_ADD_CONSTANTS)
		parent.Bind(wx.EVT_MENU, parent.parent.PrintPreview, id=ID_PREVIEW_PRINT)
		parent.Bind(wx.EVT_MENU, ExperimentGenerator(os.path.join(DEVSIMPY_PACKAGE_PATH,'out')).OnExperiment, id=ID_GEN_EXPERIMENT)

class ShapePopupMenu(wx.Menu):
	""" Shape menu class
	"""

	def __init__(self, shape, event):
		""" Constructor.
		"""

		wx.Menu.__init__(self)

		self.__canvas = event.GetEventObject()

		rotate_subMenu = wx.Menu()
		rotate_all_subMenu = wx.Menu()
		rotate_input_subMenu = wx.Menu()
		rotate_output_subMenu = wx.Menu()

		export_subMenu = wx.Menu()
		connectable_subMenu = wx.Menu()
		edit_subMenu = wx.Menu()

		edit=wx.MenuItem(self, ID_EDIT_SHAPE, _("Edit"), _("Edit the code"))
		editModel=wx.MenuItem(self, ID_EDIT_MODEL_SHAPE, _("Model"), _("Edit the model code"))
		editTest=wx.MenuItem(self, ID_TESTING_SHAPE, _("Tests"), _("Edit the tests code"))
		log = wx.MenuItem(self, ID_LOG_SHAPE, _("Log"), _("View log file"))
		copy=wx.MenuItem(self, ID_COPY_SHAPE, _("&Copy\tCtrl+C"), _("Copy the model"))
		paste=wx.MenuItem(self, ID_PASTE_SHAPE, _("&Paste\tCtrl+V"), _("Paste the model"))
		cut=wx.MenuItem(self, ID_CUT_SHAPE, _("&Cut\tCtrl+X"), _("Cut the model"))
		rotateAll=wx.MenuItem(self, ID_ROTATE_ALL_SHAPE, _("&All"), _("Rotate all ports"))
		rotateInput=wx.MenuItem(self, ID_ROTATE_INPUT_SHAPE, _("&Input ports"), _("Rotate input ports"))
		rotateOutput=wx.MenuItem(self, ID_ROTATE_OUTPUT_SHAPE, _("&Output ports"), _("Rotate output ports"))
		rotateR=wx.MenuItem(self, ID_RIGHT_ROTATE_SHAPE, _("&Right Rotate\tCtrl+R"), _("Rotate on the right"))
		rotateL=wx.MenuItem(self, ID_LEFT_ROTATE_SHAPE, _("&Left Rotate\tCtrl+L"), _("Rotate on the left"))
		rotateIR=wx.MenuItem(self, ID_RIGHT_ROTATE_INPUT_SHAPE, _("&Right Rotate\tCtrl+R"), _("Rotate on the right"))
		rotateIL=wx.MenuItem(self, ID_LEFT_ROTATE_INPUT_SHAPE, _("&Left Rotate\tCtrl+L"), _("Rotate on the left"))
		rotateOR=wx.MenuItem(self, ID_RIGHT_ROTATE_OUTPUT_SHAPE, _("&Right Rotate\tCtrl+R"), _("Rotate on the right"))
		rotateOL=wx.MenuItem(self, ID_LEFT_ROTATE_OUTPUT_SHAPE, _("&Left Rotate\tCtrl+L"), _("Rotate on the left"))
		rename=wx.MenuItem(self, ID_RENAME_SHAPE, _("&Rename"), _("Rename the label of the model"))
		delete=wx.MenuItem(self, ID_DELETE_SHAPE, _("Delete"), _("Delete the model"))
		lock=wx.MenuItem(self, ID_LOCK_SHAPE, _("Lock"), _("Lock the link"))
		unlock=wx.MenuItem(self, ID_UNLOCK_SHAPE, _("Unlock"), _("Unlock the link"))
		enable=wx.MenuItem(self, ID_ENABLE_SHAPE, _("Enable"), _("Enable the link for the simulation"))
		disable=wx.MenuItem(self, ID_DISABLE_SHAPE, _("Disable"), _("Disable the link for the simulation"))
		export=wx.MenuItem(self, ID_EXPORT_SHAPE, _("Export"), _("Export the model"))
		exportAMD=wx.MenuItem(self, ID_EXPORT_AMD_SHAPE, _("AMD"), _("Model exported to a amd file"))
		exportCMD=wx.MenuItem(self, ID_EXPORT_CMD_SHAPE, _("CMD"), _("Model exported to a cmd file"))
		exportXML=wx.MenuItem(self, ID_EXPORT_XML_SHAPE, _("XML"), _("Model exported to a xml file"))
		exportJS=wx.MenuItem(self, ID_EXPORT_JS_SHAPE, _("JS"), _("Model exported to a js (join) file"))
		plugin = wx.MenuItem(self, ID_PLUGINS_SHAPE, _("Plug-in"), _("Plug-in manager"))
		properties=wx.MenuItem(self, ID_PROPERTIES_SHAPE, _("Properties"), _("Edit the attributes"))

		edit.SetBitmap(load_and_resize_image('edit.png'))
		editModel.SetBitmap(load_and_resize_image('edit.png'))
		editTest.SetBitmap(load_and_resize_image( 'test.png'))
		log.SetBitmap(load_and_resize_image('log.png'))
		copy.SetBitmap(load_and_resize_image('copy.png'))
		paste.SetBitmap(load_and_resize_image('paste.png'))
		cut.SetBitmap(load_and_resize_image('cut.png'))
		rotateL.SetBitmap(load_and_resize_image('rotateL.png'))
		rotateR.SetBitmap(load_and_resize_image('rotateR.png'))
		rotateIL.SetBitmap(load_and_resize_image('rotateL.png'))
		rotateIR.SetBitmap(load_and_resize_image('rotateR.png'))
		rotateOL.SetBitmap(load_and_resize_image('rotateL.png'))
		rotateOR.SetBitmap(load_and_resize_image('rotateR.png'))
		rename.SetBitmap(load_and_resize_image('rename.png'))
		export.SetBitmap(load_and_resize_image('export.png'))
		delete.SetBitmap(load_and_resize_image('delete.png'))
		lock.SetBitmap(load_and_resize_image('lock.png'))
		unlock.SetBitmap(load_and_resize_image('unlock.png'))
		enable.SetBitmap(load_and_resize_image('check.png'))
		disable.SetBitmap(load_and_resize_image('no_ok.png'))
		plugin.SetBitmap(load_and_resize_image('plugins.png'))
		properties.SetBitmap(load_and_resize_image('properties.png'))

		AppendItem = self.Append

		edit_subMenu.AppendItem = edit_subMenu.Append
		rotate_subMenu.AppendItem = rotate_subMenu.Append
		rotate_all_subMenu.AppendItem =rotate_all_subMenu.Append
		rotate_input_subMenu.AppendItem = rotate_input_subMenu.Append
		rotate_output_subMenu.AppendItem = rotate_output_subMenu.Append
		export_subMenu.AppendItem = export_subMenu.Append
			
		if isinstance(shape, Container.ConnectionShape):
			
			AppendItem(delete)

			if shape.lock_flag:
				AppendItem(unlock) # Add unlock action to the menu
			else:
				AppendItem(lock)  # Add lock action to the menu

			if (shape.enable):
				AppendItem(disable)
			else:
				AppendItem(enable)

			self.__canvas.Bind(wx.EVT_MENU, self.__canvas.OnDelete, id=ID_DELETE_SHAPE)
			self.__canvas.Bind(wx.EVT_MENU, self.__canvas.OnLock, id=ID_LOCK_SHAPE)
			self.__canvas.Bind(wx.EVT_MENU, self.__canvas.OnUnLock, id=ID_UNLOCK_SHAPE)
			self.__canvas.Bind(wx.EVT_MENU, self.__canvas.OnEnable, id=ID_ENABLE_SHAPE)
			self.__canvas.Bind(wx.EVT_MENU, self.__canvas.OnDisable, id=ID_DISABLE_SHAPE)

		elif isinstance(shape, Container.ResizeableNode):
			Delete_menu = AppendItem(delete)

		elif isinstance(shape, Container.Node):
			pass
			#port_number=wx.MenuItem(self, wx.NewIdRef(), _("Enable port number"), _("Port number"),wx.ITEM_CHECK)
			#self.AppendItem(port_number)

			#rename_menu = self.AppendItem(rename)
			#self.__canvas.Bind(wx.EVT_MENU, shape.OnRename, id=ID_RENAME_SHAPE)
		else:
			
			if isinstance(shape, Container.CodeBlock) and shape.isAMD():
					Edit_menu = AppendMenu(self, -1, _("Edit"), edit_subMenu)
					edit_subMenu.AppendItem(editModel)
					edit_subMenu.AppendItem(editTest)
			else:
				Edit_menu = AppendItem(edit)
				
			if isinstance(shape, Container.CodeBlock) and shape.isPYC():
				Edit_menu.Enable(False)

			AppendItem(log)

			self.AppendSeparator()

			AppendItem(copy)
			AppendItem(paste)
			AppendItem(cut)

			if shape.lock_flag:
				AppendItem(unlock) # Add unlock action to the menu
			else:
				AppendItem(lock) # Add lock action to the menu

			rotate_subMenu.AppendItem = rotate_subMenu.Append
			rotate_subMenu.AppendMenu = rotate_subMenu.Append
			rotate_all_subMenu.AppendItem = rotate_all_subMenu.Append
			rotate_input_subMenu.AppendItem = rotate_input_subMenu.Append
			rotate_output_subMenu.AppendItem =  rotate_output_subMenu.Append

			### for port, just right of left rotation
			if isinstance(shape, Container.Port):    			
				rotate_subMenu.AppendItem(rotateR)
				rotate_subMenu.AppendItem(rotateL)

			else:
				rotate_all_subMenu.AppendItem(rotateR)
				rotate_all_subMenu.AppendItem(rotateL)
				rotate_input_subMenu.AppendItem(rotateIR)
				rotate_input_subMenu.AppendItem(rotateIL)
				rotate_output_subMenu.AppendItem(rotateOR)
				rotate_output_subMenu.AppendItem(rotateOL)

				rotate_subMenu.Append(ID_ROTATE_ALL_SHAPE, _("All"), rotate_all_subMenu)
				rotate_subMenu.Append(ID_ROTATE_INPUT_SHAPE, _("Input"), rotate_input_subMenu)
				rotate_subMenu.Append(ID_ROTATE_OUTPUT_SHAPE, _("Output"), rotate_output_subMenu)

			AppendMenu(self, ID_ROTATE_SHAPE, _("Rotate"), rotate_subMenu)
			AppendItem(rename)

			self.AppendSeparator()
			
			# pour tout les models sur le canvas, rangés par ordre alphabetique, ormis les connections et le modele que l'on veut connecter (la source)
			for label,item in sorted([(a.label,a) for a in self.__canvas.GetDiagram().GetShapeList() if a != shape and not isinstance(a, Container.ConnectionShape)], key = lambda x: x[0]):
				# avoid connections like: iPort->iPort, oPort->oPort
				if (isinstance(shape, Container.iPort) and not isinstance(item, Container.iPort)) or (isinstance(shape, Container.oPort) and not isinstance(item, Container.oPort)) or isinstance(shape, Container.Block):
					new_item = wx.MenuItem(connectable_subMenu, wx.NewIdRef(), label)
					connectable_subMenu.Append(new_item)
					self.__canvas.Bind(wx.EVT_MENU, self.__canvas.OnConnectTo, id=new_item.GetId())
			
			if connectable_subMenu.GetMenuItems():
				AppendMenu(self, -1, _('Connect to'), connectable_subMenu)
				self.AppendSeparator()

			if isinstance(shape, Container.CodeBlock):
				AppendMenu(self, -1, _("Export"), export_subMenu)
				Export_SubMenu1 = export_subMenu.Append(exportAMD)
				self.AppendSeparator()

				if shape.isPYC():
					Export_SubMenu1.Enable(False)

				### if Wcomp general plugin is enabled, sub menu appear in contextual menu of amd (right clic)
				PluginManager.trigger_event("ADD_WCOMP_EXPORT_MENU", parent=self, model=shape, submenu= export_subMenu)

			elif isinstance(shape, Container.ContainerBlock):
				
				AppendMenu(self, -1, _("Export"), export_subMenu)
				self.AppendSeparator()

				Export_SubMenu1 = export_subMenu.Append(exportCMD)
				export_subMenu.Append(exportXML)
				export_subMenu.Append(exportJS)

			else:
				self.Enable(ID_EDIT_SHAPE, False)

			if shape.enable:
				AppendItem(disable)
			else:
				AppendItem(enable)
				
			AppendItem(delete)

			### Plug-in manager only for Block model
			if isinstance(shape, Container.CodeBlock) or isinstance(shape, Container.ContainerBlock):
				### only for amd or cmd
				if shape.model_path != "":
					self.AppendSeparator()
					#if ZipManager.Zip.HasPlugin(shape.model_path):
					AppendItem(plugin)
					self.__canvas.Bind(wx.EVT_MENU, shape.OnPluginsManager, id=ID_PLUGINS_SHAPE)

					### if Wcomp general plug-in is enabled, sub menu appear in contextual menu of amd (right clic)
					PluginManager.trigger_event("ADD_WCOMP_STRATEGY_MENU", parent=self, model=shape)

				### if state trajectory general plug-in is enabled, sub menu appear in contextual menu (right clic)
				PluginManager.trigger_event("ADD_STATE_TRAJECTORY_MENU", parent=self, model=shape)

			self.AppendSeparator()
			AppendItem(properties)

			self.Enable(ID_PASTE_SHAPE, not Container.clipboard == [])
			self.Enable(ID_LOG_SHAPE, shape.getDEVSModel() is not None)

			# binding events
			if not isinstance(shape, Container.Port):
				self.__canvas.Bind(wx.EVT_MENU, shape.OnRotateInputR, id=ID_RIGHT_ROTATE_INPUT_SHAPE)
				self.__canvas.Bind(wx.EVT_MENU, shape.OnRotateInputL, id=ID_LEFT_ROTATE_INPUT_SHAPE)
				self.__canvas.Bind(wx.EVT_MENU, shape.OnRotateOutputR, id=ID_RIGHT_ROTATE_OUTPUT_SHAPE)
				self.__canvas.Bind(wx.EVT_MENU, shape.OnRotateOutputL, id=ID_LEFT_ROTATE_OUTPUT_SHAPE)

			self.__canvas.Bind(wx.EVT_MENU, shape.OnRotateR, id=ID_RIGHT_ROTATE_SHAPE)
			self.__canvas.Bind(wx.EVT_MENU, shape.OnRenameFromMenu, id=ID_RENAME_SHAPE)
			self.__canvas.Bind(wx.EVT_MENU, shape.OnRotateL, id=ID_LEFT_ROTATE_SHAPE)
			self.__canvas.Bind(wx.EVT_MENU, self.__canvas.OnDelete, id=ID_DELETE_SHAPE)
			self.__canvas.Bind(wx.EVT_MENU, self.__canvas.OnCut, id=ID_CUT_SHAPE)
			self.__canvas.Bind(wx.EVT_MENU, self.__canvas.OnCopy, id=ID_COPY_SHAPE)
			self.__canvas.Bind(wx.EVT_MENU, self.__canvas.OnPaste, id=ID_PASTE_SHAPE)
			self.__canvas.Bind(wx.EVT_MENU, self.__canvas.OnLock, id=ID_LOCK_SHAPE)
			self.__canvas.Bind(wx.EVT_MENU, self.__canvas.OnUnLock, id=ID_UNLOCK_SHAPE)
			self.__canvas.Bind(wx.EVT_MENU, self.__canvas.OnEnable, id=ID_ENABLE_SHAPE)
			self.__canvas.Bind(wx.EVT_MENU, self.__canvas.OnDisable, id=ID_DISABLE_SHAPE)
			self.__canvas.Bind(wx.EVT_MENU, self.__canvas.OnProperties, id=ID_PROPERTIES_SHAPE)

			# Codeblock specific binding
			if isinstance(shape, Container.CodeBlock):
				self.__canvas.Bind(wx.EVT_MENU, shape.OnEditor, id=ID_EDIT_MODEL_SHAPE)
				self.__canvas.Bind(wx.EVT_MENU, shape.OnLog, id=ID_LOG_SHAPE)
				self.__canvas.Bind(wx.EVT_MENU, shape.OnExport, id=ID_EXPORT_AMD_SHAPE)

				# AMD specific binding
				if shape.isAMD():
					self.__canvas.Bind(wx.EVT_MENU, shape.OnTestEditor, id=ID_TESTING_SHAPE)
				elif shape.isPY():
					self.__canvas.Bind(wx.EVT_MENU, shape.OnEditor, id=ID_EDIT_SHAPE)
				else:
					self.Enable(ID_EDIT_SHAPE, False)

			# ContainerBlock specific binding
			elif isinstance(shape, Container.ContainerBlock):
				self.__canvas.Bind(wx.EVT_MENU, shape.OnLog, id=ID_LOG_SHAPE)
				self.__canvas.Bind(wx.EVT_MENU, shape.OnEditor, id=ID_EDIT_SHAPE)
				self.__canvas.Bind(wx.EVT_MENU, shape.OnExport, id=ID_EXPORT_CMD_SHAPE)
				self.__canvas.Bind(wx.EVT_MENU, shape.OnExport, id=ID_EXPORT_XML_SHAPE)
				self.__canvas.Bind(wx.EVT_MENU, shape.OnExport, id=ID_EXPORT_JS_SHAPE)

		if isinstance(shape, Container.ResizeableNode):
			shape.OnDeleteNode(event)

	def GetParent(self):
		""" Return the parent.
		"""
		return self.__canvas