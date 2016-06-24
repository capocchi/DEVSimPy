# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# Menu.py ---
#                     --------------------------------
#                        Copyright (c) 2010
#                       Laurent CAPOCCHI
#                      University of Corsica
#                     --------------------------------
# Version 2.0                                        last modified: 13/05/10
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
from tempfile import gettempdir

import Container
import ZipManager
import pluginmanager

_ = wx.GetTranslation

#File menu identifiers
ID_NEW = wx.ID_NEW
ID_OPEN  = wx.ID_OPEN
ID_SAVE = wx.ID_SAVE
ID_SAVEAS = wx.ID_SAVEAS
ID_EXIT = wx.ID_EXIT
ID_ABOUT = wx.ID_ABOUT
ID_EXPORT = wx.NewId()
ID_PREVIEW_PRINT = wx.ID_PREVIEW_PRINT
ID_SCREEN_CAPTURE = wx.NewId()
ID_PRINT = wx.ID_PRINT
#ID_PAGE_SETUP = wx.NewId()

# Recent file menu identifiers
ID_RECENT = wx.NewId()
ID_DELETE_RECENT = wx.NewId()

# Show menu identifiers
ID_SHOW_CONTROL = wx.NewId()
ID_SHOW_SHELL = wx.NewId()
ID_SHOW_SIM = wx.NewId()
ID_SHOW_PROP = wx.NewId()
ID_SHOW_LIB = wx.NewId()
ID_SHOW_EDITOR = wx.NewId()
ID_SHOW_TOOLBAR = wx.NewId()


# Perspectives menu identifiers
ID_NEW_PERSPECTIVE = wx.NewId()
ID_DELETE_PERSPECTIVE = wx.NewId()
ID_FIRST_PERSPECTIVE = wx.NewId()

# Diagram menu identifiers
ID_DETACH_DIAGRAM = wx.NewId()
ID_RENAME_DIAGRAM = wx.NewId()
ID_ZOOMIN_DIAGRAM = wx.ID_ZOOM_IN
ID_ZOOMOUT_DIAGRAM = wx.ID_ZOOM_OUT
ID_UNZOOM_DIAGRAM = wx.ID_ZOOM_100
ID_SIM_DIAGRAM = wx.NewId()
ID_CHECK_DIAGRAM = wx.NewId()
ID_CONST_DIAGRAM = wx.NewId()
ID_PRIORITY_DIAGRAM = wx.NewId()
ID_INFO_DIAGRAM = wx.NewId()
ID_CLEAR_DIAGRAM = wx.NewId()
ID_EXIT_DIAGRAM = wx.NewId()

# Setting menu identifiers
ID_PREFERENCES = wx.NewId()
ID_PROFILE = wx.NewId()
ID_DELETE_PROFILES = wx.NewId()
ID_FRENCH_LANGUAGE = wx.NewId()
ID_ENGLISH_LANGUAGE = wx.NewId()

# Help menu identifiers
ID_HELP = wx.ID_HELP
ID_API_HELP = wx.NewId()
ID_CONTACT = wx.NewId()
ID_ABOUT = wx.ID_ABOUT

# Shape popup menu identifiers
ID_EDIT_SHAPE = wx.ID_EDIT
ID_LOG_SHAPE = wx.NewId()
ID_RENAME_SHAPE = wx.NewId()
ID_COPY_SHAPE = wx.ID_COPY
ID_PASTE_SHAPE = wx.ID_PASTE
ID_CUT_SHAPE = wx.ID_CUT
ID_ROTATE_ALL_SHAPE = wx.NewId()
ID_ROTATE_INPUT_SHAPE = wx.NewId()
ID_ROTATE_OUTPUT_SHAPE = wx.NewId()
ID_ROTATE_SHAPE = wx.NewId()
ID_RIGHT_ROTATE_SHAPE = wx.NewId()
ID_LEFT_ROTATE_SHAPE = wx.NewId()
ID_RIGHT_ROTATE_INPUT_SHAPE = wx.NewId()
ID_LEFT_ROTATE_INPUT_SHAPE = wx.NewId()
ID_RIGHT_ROTATE_OUTPUT_SHAPE = wx.NewId()
ID_LEFT_ROTATE_OUTPUT_SHAPE = wx.NewId()
ID_DELETE_SHAPE = wx.ID_DELETE
ID_LOCK_SHAPE = wx.NewId()
ID_UNLOCK_SHAPE = wx.NewId()
ID_EXPORT_SHAPE = wx.NewId()
ID_EXPORT_AMD_SHAPE = wx.NewId()
ID_EXPORT_CMD_SHAPE = wx.NewId()
ID_EXPORT_XML_SHAPE = wx.NewId()
ID_EXPORT_JS_SHAPE = wx.NewId()
ID_PLUGINS_SHAPE = wx.NewId()
ID_PROPERTIES_SHAPE = wx.ID_PROPERTIES
ID_EDIT_MODEL_SHAPE = wx.NewId()
ID_TESTING_SHAPE = wx.NewId()

# Shape canvas popup menu identifiers
ID_NEW_SHAPE = wx.NewId()
ID_ADD_CONSTANTS = wx.NewId()

# Library popup menu identifiers
ID_NEW_LIB = wx.NewId()
ID_IMPORT_LIB = wx.NewId()
ID_EDIT_LIB = wx.NewId()
ID_RENAME_LIB = wx.NewId()
ID_REFRESH_LIB = wx.NewId()
ID_UPGRADE_LIB = wx.NewId()
ID_UPDATE_LIB = wx.NewId()
ID_HELP_LIB = wx.NewId()
ID_NEW_MODEL_LIB = wx.NewId()
ID_DELETE_LIB = wx.NewId()

# Attribute popup menu identifiers
ID_EDIT_ATTR = wx.NewId()
ID_INSERT_ATTR = wx.NewId()
ID_CLEAR_ATTR = wx.NewId()

class TaskBarMenu(wx.Menu):
	"""
	"""
	def __init__(self, parent):
		""" Constructor
		"""
		wx.Menu.__init__(self)

		self.Append(parent.TBMENU_RESTORE, _("Restore DEVSimPy"))
		self.Append(parent.TBMENU_CLOSE,   _("Close"))

class FileMenu(wx.Menu):
	"""
	"""
	def __init__(self, parent):
		wx.Menu.__init__(self)

		openModel=wx.MenuItem(self, ID_OPEN, _('&Open\tCtrl+O'),_('Open an existing diagram'))
		saveModel=wx.MenuItem(self, ID_SAVE, _('&Save\tCtrl+S'), _('Save the current diagram'))
		saveAsModel=wx.MenuItem(self, ID_SAVEAS, _('&SaveAs'),_('Save the diagram with an another name'))
		printModel=wx.MenuItem(self, ID_PRINT, _('&Print'),_('Print the current diagram'))
		printPreviewModel=wx.MenuItem(self, ID_PREVIEW_PRINT, _('Pre&view'),_('Print preview for current diagram'))
		screenCapture=wx.MenuItem(self, ID_SCREEN_CAPTURE, _('ScreenShot'),_('Capture the screen into a image'))
		exitModel=wx.MenuItem(self, wx.ID_EXIT, _('&Quit\tCtrl+Q'),_('Quit the DEVSimPy application'))

		openModel.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'open.png')))
		saveModel.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'save.png')))
		saveAsModel.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'save_as.png')))
		printModel.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'print.png')))
		printPreviewModel.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'print-preview.png')))
		screenCapture.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'ksnapshot.png')))
		exitModel.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'exit.png')))

		self.AppendItem(openModel)

		self.AppendSeparator()
		self.AppendItem(saveModel)
		self.AppendItem(saveAsModel)

		self.AppendSeparator()
		self.AppendItem(printPreviewModel)
		self.AppendItem(printModel)
		self.AppendItem(screenCapture)

		self.AppendSeparator()
		self.AppendItem(exitModel)

		parent = parent.GetParent()

		parent.Bind(wx.EVT_MENU, parent.OnNew, id=ID_NEW)
		parent.Bind(wx.EVT_MENU, parent.OnOpenFile, id=ID_OPEN)
		parent.Bind(wx.EVT_MENU, parent.OnSaveFile, id=ID_SAVE)
		parent.Bind(wx.EVT_MENU, parent.OnSaveAsFile, id=ID_SAVEAS)
		parent.Bind(wx.EVT_MENU, parent.OnPrint, id=ID_PRINT)
		parent.Bind(wx.EVT_MENU, parent.OnPrintPreview, id=ID_PREVIEW_PRINT)
		parent.Bind(wx.EVT_MENU, parent.OnScreenCapture, id=ID_SCREEN_CAPTURE)
		parent.Bind(wx.EVT_MENU, parent.OnCloseWindow, id=ID_EXIT)

class ProfileFileMenu(wx.Menu):
	"""
	"""
	def __init__(self, parent):
		wx.Menu.__init__(self)

		parent = parent.GetParent()

		for fn in filter(lambda f: f.endswith('.prof'), os.listdir(gettempdir())):
			id = wx.NewId()
			self.AppendItem(wx.MenuItem(self, id, fn))
			parent.Bind(wx.EVT_MENU, parent.OnProfiling, id=id)

		self.AppendSeparator()
		self.AppendItem(wx.MenuItem(self, ID_DELETE_PROFILES, _("Delete all")))
		self.Enable(ID_DELETE_PROFILES, self.GetMenuItemCount() > 2)
		parent.Bind(wx.EVT_MENU, parent.OnDeleteProfiles, id = ID_DELETE_PROFILES)

class RecentFileMenu(wx.Menu):
	"""
	"""
	def __init__(self, parent):
		wx.Menu.__init__(self)

		parent = parent.GetParent()

		# affichage du menu des dernier fichier consulté avec gestion des fichier qui n'existe plus
		for path in filter(lambda p:p!='', parent.openFileList):

			if not os.path.exists(path):
				index = parent.openFileList.index(path)
				del parent.openFileList[index]
				parent.openFileList.insert(-1,'')
				parent.cfg.Write("openFileList", str(eval("parent.openFileList")))
			else:
				id = wx.NewId()
				self.AppendItem(wx.MenuItem(self, id, path))
				parent.Bind(wx.EVT_MENU, parent.OnOpenRecentFile, id = id)

		self.AppendSeparator()
		self.AppendItem(wx.MenuItem(self, ID_DELETE_RECENT, _("Delete all")))
		self.Enable(ID_DELETE_RECENT, self.GetMenuItemCount() > 2)
		parent.Bind(wx.EVT_MENU, parent.OnDeleteRecentFiles, id = ID_DELETE_RECENT)


class ShowMenu(wx.Menu):
	"""
	"""
	def __init__(self, parent):
		wx.Menu.__init__(self)

		parent = parent.GetParent()

		control = wx.Menu()
		control.Append(ID_SHOW_SIM, _('Simulation'), _("Show simulation tab"), wx.ITEM_CHECK)
		control.Append(ID_SHOW_PROP, _('Properties'), _("Show properties tab"), wx.ITEM_CHECK)
		control.Append(ID_SHOW_LIB, _('Libraries'), _("Show libraries tab"), wx.ITEM_CHECK)

		self.AppendMenu(ID_SHOW_CONTROL, _('Control'), control)

		self.Append(ID_SHOW_SHELL, _('Shell'), _("Show Python Shell console"), wx.ITEM_CHECK)
		self.Append(ID_SHOW_TOOLBAR, _('Tools Bar'), _("Show icons tools bar"), wx.ITEM_CHECK)
		self.Append(ID_SHOW_EDITOR, _('Editor'), _("Show editor tab"), wx.ITEM_CHECK)
		self.Check(ID_SHOW_SHELL, False)
		self.Check(ID_SHOW_SIM, False)
		self.Check(ID_SHOW_PROP, True)
		self.Check(ID_SHOW_LIB, True)
		self.Check(ID_SHOW_EDITOR, False)
		self.Check(ID_SHOW_TOOLBAR, True)

		parent.Bind(wx.EVT_MENU, parent.OnShowShell, id = ID_SHOW_SHELL)
		parent.Bind(wx.EVT_MENU, parent.OnShowSimulation, id = ID_SHOW_SIM)
		parent.Bind(wx.EVT_MENU, parent.OnShowProperties, id = ID_SHOW_PROP)
		parent.Bind(wx.EVT_MENU, parent.OnShowLibraries, id = ID_SHOW_LIB)
		parent.Bind(wx.EVT_MENU, parent.OnShowEditor, id = ID_SHOW_EDITOR)
		parent.Bind(wx.EVT_MENU, parent.OnShowToolBar, id = ID_SHOW_TOOLBAR)

class PerspectiveMenu(wx.Menu):
	def __init__(self, parent):
		wx.Menu.__init__(self)

		parent = parent.GetParent()

		self.Append(ID_NEW_PERSPECTIVE, _("New"))
		self.Append(ID_DELETE_PERSPECTIVE, _("Delete all"))
		self.AppendSeparator()

		if _("Default Startup") not in parent.perspectives:
			self.Append(ID_FIRST_PERSPECTIVE, _("Default Startup"))
			parent.perspectives.update({_("Default Startup"):parent._mgr.SavePerspective()})

		### default perspective
		L = parent.perspectives.keys()
		L.sort()
		for name in L:
			ID = wx.NewId()
			self.Append(ID, name)
			parent.Bind(wx.EVT_MENU, parent.OnRestorePerspective, id=ID)

		parent.Bind(wx.EVT_MENU, parent.OnCreatePerspective, id=ID_NEW_PERSPECTIVE)
		parent.Bind(wx.EVT_MENU, parent.OnDeletePerspective, id=ID_DELETE_PERSPECTIVE)
		parent.Bind(wx.EVT_MENU, parent.OnRestorePerspective, id=ID_FIRST_PERSPECTIVE)

class DiagramMenu(wx.Menu):
	"""
	"""
	def __init__(self, parent):
		wx.Menu.__init__(self)

		parent = parent.GetParent()

		newDiagram = wx.MenuItem(self, ID_NEW, _('New'), _("Create a new tab diagram"))
		detachDiagram = wx.MenuItem(self, ID_DETACH_DIAGRAM, _('Detach'), _("Detach the tab to a frame window"))
		zoomIn = wx.MenuItem(self, ID_ZOOMIN_DIAGRAM, _('Zoom'), _("Zoom in"))
		zoomOut = wx.MenuItem(self, ID_ZOOMOUT_DIAGRAM, _('UnZoom'), _("Zoom out"))
		annuleZoom = wx.MenuItem(self, ID_UNZOOM_DIAGRAM, _('AnnuleZoom'), _("Normal view"))
		checkDiagram = wx.MenuItem(self, ID_CHECK_DIAGRAM, _('Debugger\tF4'), _("Check DEVS master model of diagram"))
		simulationDiagram = wx.MenuItem(self, ID_SIM_DIAGRAM, _('&Simulate\tF5'), _("Perform the simulation"))
		constantsDiagram = wx.MenuItem(self, ID_CONST_DIAGRAM, _('Add constants'), _("Loading constants parameters"))
		priorityDiagram = wx.MenuItem(self, ID_PRIORITY_DIAGRAM, _('Priority\tF3'), _("Priority for select function"))
		infoDiagram = wx.MenuItem(self, ID_INFO_DIAGRAM, _('Information'), _("Information about diagram (number of models, connections, etc)"))
		clearDiagram = wx.MenuItem(self, ID_CLEAR_DIAGRAM, _('Clear'), _("Remove all components in diagram"))
		renameDiagram = wx.MenuItem(self, ID_RENAME_DIAGRAM, _('Rename'), _("Rename diagram"))
		closeDiagram = wx.MenuItem(self, ID_EXIT_DIAGRAM, _('&Close\tCtrl+D'), _("Close the tab"))

		newDiagram.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'new.png')))
		detachDiagram.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'detach.png')))
		zoomIn.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'zoom+.png')))
		zoomOut.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'zoom-.png')))
		annuleZoom.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'no_zoom.png')))
		checkDiagram.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'check_master.png')))
		simulationDiagram.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'simulation.png')))
		constantsDiagram.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'properties.png')))
		priorityDiagram.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'priority.png')))
		infoDiagram.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'info.png')))
		clearDiagram.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'delete.png')))
		renameDiagram.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'rename.png')))
		closeDiagram.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'close.png')))

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

class SettingsMenu(wx.Menu):
	"""
	"""
	def __init__(self, parent):
		wx.Menu.__init__(self)

		parent = parent.GetParent()

		languagesSubmenu = wx.Menu()

		pref_item = wx.MenuItem(self, ID_PREFERENCES, _('Preferences'), _("Advanced setting options"))
		fritem = wx.MenuItem(languagesSubmenu, ID_FRENCH_LANGUAGE, _('French'), _("French interface"))
		enitem = wx.MenuItem(languagesSubmenu, ID_ENGLISH_LANGUAGE, _('English'), _("English interface"))

		pref_item.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'preferences.png')))
		fritem.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'french-flag.png')))
		enitem.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'united-states-flag.png')))


		languagesSubmenu.AppendItem(fritem)
		languagesSubmenu.AppendItem(enitem)

		self.AppendMenu(wx.NewId(), _('Languages'), languagesSubmenu)
		self.AppendItem(pref_item)

		fritem.Enable(not parent.language == 'fr')
		enitem.Enable(not parent.language in ('en','default'))

		parent.Bind(wx.EVT_MENU, parent.OnFrench, id=ID_FRENCH_LANGUAGE)
		parent.Bind(wx.EVT_MENU, parent.OnEnglish, id=ID_ENGLISH_LANGUAGE)
		parent.Bind(wx.EVT_MENU, parent.OnAdvancedSettings, id=ID_PREFERENCES)

class HelpMenu(wx.Menu):
	"""
	"""
	def __init__(self, parent):
		wx.Menu.__init__(self)

		parent = parent.GetParent()

		helpModel = wx.MenuItem(self, ID_HELP, _('&DEVSimPy Help\tF1'), _("Help for DEVSimPy user"))
		apiModel = wx.MenuItem(self, ID_API_HELP, _('&DEVSimPy API\tF2'), _("API for DEVSimPy user"))
		contactModel = wx.MenuItem(self, ID_CONTACT, _('Contact the Author...'), _("Send mail to the author"))
		aboutModel = wx.MenuItem(self, ID_ABOUT, _('About DEVSimPy...'), _("About DEVSimPy"))

		helpModel.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'search.png')))
		apiModel.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'api.png')))
		contactModel.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'mail.png')))
		aboutModel.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH,'info.png')))

		self.AppendItem(helpModel)
		self.AppendItem(apiModel)
		self.AppendSeparator()
		self.AppendItem(aboutModel)
		self.AppendItem(contactModel)

		parent.Bind(wx.EVT_MENU, parent.OnHelp, id=ID_HELP)
		parent.Bind(wx.EVT_MENU, parent.OnAPI, id=ID_API_HELP)
		parent.Bind(wx.EVT_MENU, parent.OnAbout, id=ID_ABOUT)
		parent.Bind(wx.EVT_MENU, parent.OnContact, id=ID_CONTACT)

class MainMenuBar(wx.MenuBar):
	def __init__(self, parent):
		wx.MenuBar.__init__(self)

		self.parent = parent

		self.Append(FileMenu(self),_("&File"))
		self.Append(DiagramMenu(self),_("&Diagram"))
		self.Append(ShowMenu(self), _("&Show"))
		self.parent.perspectivesmenu = PerspectiveMenu(self)
		self.Append(self.parent.perspectivesmenu, _("&Perspectives"))
		self.Append(SettingsMenu(self), _("&Options"))
		self.Append(HelpMenu(self), _("&Help"))

		self.Bind(wx.EVT_MENU_HIGHLIGHT_ALL, self.OnMenuHighlight)

	def OnOpenMenu(self, event):
		""" Open menu has been detected.

			Add the recent files menu updated from recentFiles list
		"""

		menu = event.GetMenu()

		### if the opened menu is the File menu
		if isinstance(menu, FileMenu):

			### if item exist, we delete him
			if menu.FindItemById(ID_RECENT):menu.Delete(ID_RECENT)

			### we insert the recent files menu
			menu.InsertMenu(1, ID_RECENT, _("Recent files"), RecentFileMenu(self))

		elif isinstance(menu, SettingsMenu) and 'hotshot' in sys.modules.keys():
			### if item exist, we delete him
			if menu.FindItemById(ID_PROFILE): menu.Delete(ID_PROFILE)
			### we insert the profile files menu
			menu.InsertMenu(1, ID_PROFILE, _('Profile'),  ProfileFileMenu(self))

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

class DiagramNoTabPopupMenu(wx.Menu):
	""" Diagram noteBook popup menu
	"""

	def __init__(self, parent):
		""" Constructor.
		"""
		wx.Menu.__init__(self)

		new_tab = wx.MenuItem(self, ID_NEW, _('New'), _("Create a new tab diagram"))
		new_tab.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH_16_16,'new.png')))

		self.AppendItem(new_tab)

		### Bind is not necessary because ID_EXIT_DAIGRAM and ID_DETACH_DIAGRAM are already binded

class DiagramTabPopupMenu(wx.Menu):
	""" Diagram noteBook popup menu
	"""

	def __init__(self, parent):
		""" Constructor.
		"""
		wx.Menu.__init__(self)

		close = wx.MenuItem(self, ID_EXIT_DIAGRAM, _('Close'), _('Close diagram'))
		detach = wx.MenuItem(self, ID_DETACH_DIAGRAM, _('Detach'), _('Detach tab to window'))
		rename = wx.MenuItem(self, ID_RENAME_DIAGRAM, _('Rename...'), _('Rename diagram'))
		clear = wx.MenuItem(self, ID_CLEAR_DIAGRAM, _('Clear...'), _('Clear diagram'))


		close.SetBitmap(wx.Image(os.path.join(ICON_PATH_16_16,'close.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
		detach.SetBitmap(wx.Image(os.path.join(ICON_PATH_16_16,'detach.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
		rename.SetBitmap(wx.Image(os.path.join(ICON_PATH_16_16,'rename.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
		clear.SetBitmap(wx.Image(os.path.join(ICON_PATH_16_16,'delete.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())

		self.AppendItem(detach)
		self.AppendItem(rename)
		self.AppendItem(clear)
		self.AppendSeparator()
		self.AppendItem(close)

		### Bind is not necessary because ID_EXIT_DAIGRAM and ID_DETACH_DIAGRAM are already binded

class PropertiesCtrlPopupMenu(wx.Menu):
	""" PropertiesCtrl popup menu
	"""

	def __init__(self, parent, row, col):
		""" Constructor.
		"""
		wx.Menu.__init__(self)

		self.parent = parent
		self.row = row
		self.col = col

		edit = wx.MenuItem(self, ID_EDIT_ATTR, _('Edit'), _('Edit attribute'))
		insert = wx.MenuItem(self, ID_INSERT_ATTR, _('Insert'), _('Insert attribute'))
		clear = wx.MenuItem(self, ID_CLEAR_ATTR, _('Clear'), _('Clear value'))
		edit.SetBitmap(wx.Image(os.path.join(ICON_PATH_16_16,'edit.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
		insert.SetBitmap(wx.Image(os.path.join(ICON_PATH_16_16,'insert.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
		clear.SetBitmap(wx.Image(os.path.join(ICON_PATH_16_16,'edit-clear.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())

		self.AppendItem(edit)
		self.AppendItem(insert)
		self.AppendSeparator()
		self.AppendItem(clear)

		parent.Bind(wx.EVT_MENU, parent.OnEditCell, id=ID_EDIT_ATTR)
		parent.Bind(wx.EVT_MENU, parent.OnInsertCell, id=ID_INSERT_ATTR)
		parent.Bind(wx.EVT_MENU, parent.OnClearCell, id=ID_CLEAR_ATTR)

	def GetRow(self):
		return self.row

	def GetCol(self):
		return self.col

class ItemLibraryPopupMenu(wx.Menu):
	""" Item library popup menu.
	"""

	def __init__(self, parent):
		""" Constructor.
		"""
		wx.Menu.__init__(self)

		### last child of tree and not empty directory (then, has OnDocumentation method)

		if parent.IsBold(parent.GetSelection()):
			new_model = wx.MenuItem(self, ID_NEW_MODEL_LIB, _('New Model'), _('Add new model to the selected library'))
			new_model.SetBitmap(wx.Image(os.path.join(ICON_PATH_16_16, 'new.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
			self.InsertItem(0, new_model)
			self.Bind(wx.EVT_MENU, parent.OnNewModel, id=ID_NEW_MODEL_LIB)

		else:

			edit = wx.MenuItem(self, ID_EDIT_LIB, _('Edit'), _('Edit selected module'))
			rename = wx.MenuItem(self, ID_RENAME_LIB, _('Rename'), _('Rename selected module'))
			doc = wx.MenuItem(self, wx.NewId(), _('Documentation'), _('Documentation of selected library'))
			update = wx.MenuItem(self, ID_UPDATE_LIB, _('Update'), _('Update selected module'))

			edit.SetBitmap(wx.Image(os.path.join(ICON_PATH_16_16,'edit.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
			rename.SetBitmap(wx.Image(os.path.join(ICON_PATH_16_16,'rename.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
			doc.SetBitmap(wx.Image(os.path.join(ICON_PATH_16_16,'doc.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())

			self.AppendItem(edit)
			self.AppendItem(rename)
			self.AppendItem(doc)
			self.AppendItem(update)

			self.Bind(wx.EVT_MENU, parent.OnItemEdit, id = ID_EDIT_LIB)	# put before the popUpMenu
			self.Bind(wx.EVT_MENU, parent.OnItemRename, id = ID_RENAME_LIB)	# put before the popUpMenu
			self.Bind(wx.EVT_MENU, parent.OnItemDocumentation, id = doc.GetId())	# put before the popUpMenu
			self.Bind(wx.EVT_MENU, parent.OnItemRefresh, id = ID_UPDATE_LIB)	# put before the popUpMenu

		### menu for all item of tree
		delete = wx.MenuItem(self, ID_DELETE_LIB, _('Delete'), _('Delete selected library'))
		delete.SetBitmap(wx.Image(os.path.join(ICON_PATH_16_16, 'db-2.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())

		self.AppendItem(delete)

		self.Bind(wx.EVT_MENU, parent.OnDelete, id=ID_DELETE_LIB) # put before the popUpMenu


class LibraryPopupMenu(wx.Menu):

	def __init__(self, parent):
		wx.Menu.__init__(self)

		new = wx.MenuItem(self, ID_NEW_LIB, _('New/Import'), _('Create or import library'))
		refresh = wx.MenuItem(self, ID_REFRESH_LIB, _('Refresh'), _('Refresh library'))
		#upgrade = wx.MenuItem(self, ID_UPGRADE_LIB, _('Upgrade'), _('Upgrade library'))
		info = wx.MenuItem(self, ID_HELP_LIB, _('Help'), _('Library description'))

		new.SetBitmap(wx.Image(os.path.join(ICON_PATH_16_16,'db+2.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
		refresh.SetBitmap(wx.Image(os.path.join(ICON_PATH_16_16,'db_refresh2.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
		#upgrade.SetBitmap(wx.Image(os.path.join(ICON_PATH_16_16,'upgrade.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
		info.SetBitmap(wx.Image(os.path.join(ICON_PATH_16_16,'dbinfo2.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())

		self.AppendItem(new)
		self.AppendItem(refresh)
		#self.AppendItem(upgrade)
		self.AppendSeparator()
		self.AppendItem(info)

		mainW = parent.GetTopLevelParent()

		wx.EVT_MENU(self, ID_NEW_LIB, mainW.OnImport)
		wx.EVT_MENU(self, ID_HELP_LIB, parent.OnInfo)
		wx.EVT_MENU(self, ID_REFRESH_LIB, parent.OnUpdateAll)
		#wx.EVT_MENU(self, ID_UPGRADE_LIB, parent.UpgradeAll)

class ShapeCanvasPopupMenu(wx.Menu):
	""" ShapeCanvas menu class
	"""
	def __init__(self, parent):
		""" Constructor.
		"""

		wx.Menu.__init__(self)

		### make all items
		new = wx.MenuItem(self, ID_NEW_SHAPE, _('&New'), _('New model'))
		paste = wx.MenuItem(self, ID_PASTE_SHAPE, _('&Paste\tCtrl+V'), _('Paste the model'))
		add_constants = wx.MenuItem(self, ID_ADD_CONSTANTS, _('Add constants'), _('Add constants parameters'))
		preview_dia = wx.MenuItem(self, ID_PREVIEW_PRINT, _('Print preview'), _('Print preveiw of the diagram'))

		### bitmap item setting
		new.SetBitmap(wx.Image(os.path.join(ICON_PATH_16_16,'new_model.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
		paste.SetBitmap(wx.Image(os.path.join(ICON_PATH_16_16,'paste.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
		add_constants.SetBitmap(wx.Image(os.path.join(ICON_PATH_16_16,'properties.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
		preview_dia.SetBitmap(wx.Image(os.path.join(ICON_PATH_16_16,'print-preview.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())

		### append items
		self.AppendItem(new)
		self.AppendItem(paste)
		self.AppendItem(add_constants)
		self.AppendItem(preview_dia)

		self.Enable(ID_PASTE_SHAPE, not Container.clipboard == [])

		### binding
		parent.Bind(wx.EVT_MENU, parent.OnNewModel, id=ID_NEW_SHAPE)
		parent.Bind(wx.EVT_MENU, parent.OnPaste, id=ID_PASTE_SHAPE)
		parent.Bind(wx.EVT_MENU, parent.diagram.OnAddConstants, id=ID_ADD_CONSTANTS)
		parent.Bind(wx.EVT_MENU, parent.parent.PrintPreview, id=ID_PREVIEW_PRINT)

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
		export=wx.MenuItem(self, ID_EXPORT_SHAPE, _("Export"), _("Export the model"))
		exportAMD=wx.MenuItem(self, ID_EXPORT_AMD_SHAPE, _("AMD"), _("Model exported to a amd file"))
		exportCMD=wx.MenuItem(self, ID_EXPORT_CMD_SHAPE, _("CMD"), _("Model exported to a cmd file"))
		exportXML=wx.MenuItem(self, ID_EXPORT_XML_SHAPE, _("XML"), _("Model exported to a xml file"))
		exportJS=wx.MenuItem(self, ID_EXPORT_JS_SHAPE, _("JS"), _("Model exported to a js (join) file"))
		plugin = wx.MenuItem(self, ID_PLUGINS_SHAPE, _("Plug-in"), _("Plug-in manager"))
		properties=wx.MenuItem(self, ID_PROPERTIES_SHAPE, _("Properties"), _("Edit the attributes"))

		edit.SetBitmap(wx.Image(os.path.join(ICON_PATH_16_16,'edit.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
		editModel.SetBitmap(wx.Image(os.path.join(ICON_PATH_16_16,'edit.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
		editTest.SetBitmap(wx.Image(os.path.join(ICON_PATH_16_16, 'test.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
		log.SetBitmap(wx.Image(os.path.join(ICON_PATH_16_16,'log.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
		copy.SetBitmap(wx.Image(os.path.join(ICON_PATH_16_16,'copy.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
		paste.SetBitmap(wx.Image(os.path.join(ICON_PATH_16_16,'paste.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
		cut.SetBitmap(wx.Image(os.path.join(ICON_PATH_16_16,'cut.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
		rotateL.SetBitmap(wx.Image(os.path.join(ICON_PATH_16_16,'rotateL.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
		rotateR.SetBitmap(wx.Image(os.path.join(ICON_PATH_16_16,'rotateR.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
		rotateIL.SetBitmap(wx.Image(os.path.join(ICON_PATH_16_16,'rotateL.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
		rotateIR.SetBitmap(wx.Image(os.path.join(ICON_PATH_16_16,'rotateR.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
		rotateOL.SetBitmap(wx.Image(os.path.join(ICON_PATH_16_16,'rotateL.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
		rotateOR.SetBitmap(wx.Image(os.path.join(ICON_PATH_16_16,'rotateR.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
		rename.SetBitmap(wx.Image(os.path.join(ICON_PATH_16_16,'rename.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
		export.SetBitmap(wx.Image(os.path.join(ICON_PATH_16_16,'export.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
		delete.SetBitmap(wx.Image(os.path.join(ICON_PATH_16_16,'delete.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
		lock.SetBitmap(wx.Image(os.path.join(ICON_PATH_16_16,'lock.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
		unlock.SetBitmap(wx.Image(os.path.join(ICON_PATH_16_16,'unlock.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
		plugin.SetBitmap(wx.Image(os.path.join(ICON_PATH_16_16,'plugin.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
		properties.SetBitmap(wx.Image(os.path.join(ICON_PATH_16_16,'properties.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())

		if isinstance(shape, Container.ConnectionShape):
			self.AppendItem(delete)
			self.AppendItem(lock)
			self.AppendItem(unlock)

			self.__canvas.Bind(wx.EVT_MENU, self.__canvas.OnDelete, id=ID_DELETE_SHAPE)
			self.__canvas.Bind(wx.EVT_MENU, self.__canvas.OnLock, id=ID_LOCK_SHAPE)
			self.__canvas.Bind(wx.EVT_MENU, self.__canvas.OnUnLock, id=ID_UNLOCK_SHAPE)


		elif isinstance(shape, Container.ResizeableNode):
			Delete_menu = self.AppendItem(delete)

		elif isinstance(shape, Container.Node):
			pass
			#port_number=wx.MenuItem(self, wx.NewId(), _("Enable port number"), _("Port number"),wx.ITEM_CHECK)
			#self.AppendItem(port_number)

			#rename_menu = self.AppendItem(rename)
			#self.__canvas.Bind(wx.EVT_MENU, shape.OnRename, id=ID_RENAME_SHAPE)
		else:
			if isinstance(shape, Container.CodeBlock) and shape.isAMD():
				Edit_menu=self.AppendMenu(-1, _("Edit"), edit_subMenu)
				Edit_SubMenu1 = edit_subMenu.AppendItem(editModel)
				Edit_SubMenu2 = edit_subMenu.AppendItem(editTest)
			else:
				Edit_menu=self.AppendItem(edit)

			Log_menu=self.AppendItem(log)
			self.AppendSeparator()

			Copy_menu=self.AppendItem(copy)
			Paste_menu=self.AppendItem(paste)
			Cut_menu=self.AppendItem(cut)
			Lock_item = self.AppendItem(lock)
			UnLock_item = self.AppendItem(unlock)

			### for port, just right of left rotation
			if isinstance(shape, Container.Port):
				Rotate_SubMenu1 = rotate_subMenu.AppendItem(rotateR)
				Rotate_SubMenu2 = rotate_subMenu.AppendItem(rotateL)
			else:

				Rotate_SubMenu11 = rotate_all_subMenu.AppendItem(rotateR)
				Rotate_SubMenu12 = rotate_all_subMenu.AppendItem(rotateL)
				Rotate_SubMenu21 = rotate_input_subMenu.AppendItem(rotateIR)
				Rotate_SubMenu22 = rotate_input_subMenu.AppendItem(rotateIL)
				Rotate_SubMenu31 = rotate_output_subMenu.AppendItem(rotateOR)
				Rotate_SubMenu32 = rotate_output_subMenu.AppendItem(rotateOL)

				Rotate_all_menu = rotate_subMenu.AppendMenu(ID_ROTATE_ALL_SHAPE, _("All"), rotate_all_subMenu)
				Rotate_in_menu = rotate_subMenu.AppendMenu(ID_ROTATE_INPUT_SHAPE, _("Input"), rotate_input_subMenu)
				Rotate_out_menu = rotate_subMenu.AppendMenu(ID_ROTATE_OUTPUT_SHAPE, _("Output"), rotate_output_subMenu)

			Rotate_menu = self.AppendMenu(ID_ROTATE_SHAPE, _("Rotate"), rotate_subMenu)
			Rename_menu = self.AppendItem(rename)

			self.AppendSeparator()
			# pour tout les model sur le canvas ormis les connection et le model que l'on veut connecter (la source)
			for i, item in enumerate(filter(lambda a: a != shape and not isinstance(a, Container.ConnectionShape), self.__canvas.GetDiagram().GetShapeList())):
				# on evite de proposer les connections suivante: iPort->iPort, oPort->oPort
				if (isinstance(shape, Container.iPort) and not isinstance(item, Container.iPort)) or (isinstance(shape, Container.oPort) and not isinstance(item, Container.oPort)) or isinstance(shape, Container.Block):
					new_item = wx.MenuItem(connectable_subMenu, wx.NewId(), item.label)
					connectable_subMenu.AppendItem(new_item)
					self.__canvas.Bind(wx.EVT_MENU, self.__canvas.OnConnectTo,id = new_item.GetId())
			self.AppendMenu(-1, _('Connect to'), connectable_subMenu)

			if isinstance(shape, Container.CodeBlock):
				self.AppendSeparator()
				Export_menu = self.AppendMenu(-1, _("Export"), export_subMenu)
				Export_SubMenu1 = export_subMenu.AppendItem(exportAMD)

				### if Wcomp general plugin is enabled, sub menu appear in contextual menu of amd (right clic)
				pluginmanager.trigger_event("ADD_WCOMP_EXPORT_MENU", parent=self, model=shape, submenu= export_subMenu)

			elif isinstance(shape, Container.ContainerBlock):
				self.AppendSeparator()
				Export_menu = self.AppendMenu(-1, _("Export"), export_subMenu)
				Export_SubMenu1 = export_subMenu.AppendItem(exportCMD)
				Export_SubMenu2 = export_subMenu.AppendItem(exportXML)
				Export_SubMenu3 = export_subMenu.AppendItem(exportJS)

			else:
				self.Enable(ID_EDIT_SHAPE, False)

			self.AppendSeparator()
			Delete_menu = self.AppendItem(delete)

			### Plug-in manager only for Block model
			if isinstance(shape, Container.CodeBlock) or isinstance(shape, Container.ContainerBlock):
				### only for amd or cmd
				if shape.model_path != "":
					self.AppendSeparator()
					#if ZipManager.Zip.HasPlugin(shape.model_path):
					Plugin_menu = self.AppendItem(plugin)
					self.__canvas.Bind(wx.EVT_MENU, shape.OnPluginsManager, id=ID_PLUGINS_SHAPE)

					### if Wcomp general plug-in is enabled, sub menu appear in contextual menu of amd (right clic)
					pluginmanager.trigger_event("ADD_WCOMP_STRATEGY_MENU", parent=self, model=shape)

				### if state trajectory general plug-in is enabled, sub menu appear in contextual menu (right clic)
				pluginmanager.trigger_event("ADD_STATE_TRAJECTORY_MENU", parent=self, model=shape)

			self.AppendSeparator()
			Properties_menu = self.AppendItem(properties)

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
			self.__canvas.Bind(wx.EVT_MENU, self.__canvas.OnProperties, id=ID_PROPERTIES_SHAPE)

			# Codeblock specific binding
			if isinstance(shape, Container.CodeBlock):
				self.__canvas.Bind(wx.EVT_MENU, shape.OnEditor, id=ID_EDIT_MODEL_SHAPE)
				self.__canvas.Bind(wx.EVT_MENU, shape.OnLog, id=ID_LOG_SHAPE)
				self.__canvas.Bind(wx.EVT_MENU, shape.OnExport, id=ID_EXPORT_AMD_SHAPE)

				# AMD specific binding
				if shape.isAMD():
				 	self.__canvas.Bind(wx.EVT_MENU, shape.OnTestEditor, id=ID_TESTING_SHAPE)
				else:
					self.__canvas.Bind(wx.EVT_MENU, shape.OnEditor, id=ID_EDIT_SHAPE)

			# ContainerBlock specific binding
			elif isinstance(shape, Container.ContainerBlock):
				self.__canvas.Bind(wx.EVT_MENU, shape.OnEditor, id=ID_EDIT_SHAPE)
				self.__canvas.Bind(wx.EVT_MENU, shape.OnExport, id=ID_EXPORT_CMD_SHAPE)
				self.__canvas.Bind(wx.EVT_MENU, shape.OnExport, id=ID_EXPORT_XML_SHAPE)
				self.__canvas.Bind(wx.EVT_MENU, shape.OnExport, id=ID_EXPORT_JS_SHAPE)

		if isinstance(shape, Container.ResizeableNode):
			shape.OnDeleteNode(event)

	def GetParent(self):
		return self.__canvas