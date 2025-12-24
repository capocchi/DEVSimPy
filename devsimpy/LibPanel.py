# -*- coding: utf-8 -*-

'''
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# LibPanel.py ---
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
'''

import wx

_ = wx.GetTranslation

from LibraryTree import LibraryTree
from Utilities import load_and_resize_image

import Menu

#-----------------------------------------------------------------------
class SearchLib(wx.SearchCtrl):
	"""
	"""
	def __init__(self, *args, **kwargs):
		"""
		"""
		super(SearchLib, self).__init__(*args, **kwargs)

		self.treeChildren = []
		self.treeCopy = None
		self.ShowCancelButton( True)
		self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancel)
		self.Bind(wx.EVT_TEXT, self.OnSearch)

		self.SetToolTip(_("Find model in the library depending its name."))

	def OnCancel(self, evt):
		"""
		"""
		self.Clear()

	def OnSearch(self, evt):
		"""
		"""
		mainW = evt.GetEventObject().GetTopLevelParent()
		mainW.OnSearch(evt)

#-----------------------------------------------------------------------
class LibPanel(wx.Panel):
	"""
	"""
	def __init__(self, parent, name):
		super(LibPanel, self).__init__(parent, name=name)

		libSizer = wx.BoxSizer(wx.VERTICAL)

		### create libraries tree
		self.tree = LibraryTree(self, wx.NewIdRef(), wx.DefaultPosition, style=wx.TR_DEFAULT_STYLE|wx.TR_HIDE_ROOT|wx.TR_LINES_AT_ROOT|wx.TR_HAS_BUTTONS|wx.SUNKEN_BORDER)

		mainW = parent.GetTopLevelParent()

		### read ChargedDomainList from .devsimpy
		cfg_domain_list = mainW.cfg.Read('ChargedDomainList')
		chargedDomainList = eval(cfg_domain_list) if cfg_domain_list else []

		self.tree.Populate(chargedDomainList)

		self.tree.UnselectAll()
		
		### search tree that is hide when starting devsimpy (see __do_layout)
		self.searchTree = LibraryTree(self, wx.NewIdRef(), wx.DefaultPosition, style=wx.TR_DEFAULT_STYLE|wx.TR_HIDE_ROOT|wx.TR_MULTIPLE|wx.TR_LINES_AT_ROOT|wx.TR_HAS_BUTTONS|wx.SUNKEN_BORDER)

		### search field creation
		self.search = SearchLib(self, size=(200,-1), style = wx.TE_PROCESS_ENTER)

		#self.tree.UpdateAll()
		self.searchTree.Hide()

		tb = self.BuildToolbar()

		libSizer.Add(tb, 0, wx.ALL | wx.ALIGN_LEFT | wx.EXPAND)
		libSizer.Add(self.tree, 1 ,wx.EXPAND)
		libSizer.Add(self.searchTree, 1 ,wx.EXPAND)
		libSizer.Add(self.search, 0 ,wx.BOTTOM|wx.EXPAND)

		self.SetSizer(libSizer)
		self.SetAutoLayout(True)

		self.SetBackgroundColour(wx.WHITE)

		self.__set_tips()

	def BuildToolbar(self):
		""" creates one of the tool-bars
		The buttons act like radio buttons, setting a mode for the Panel
		Only one of them is pressed at a time. The SetMode() method handles this
		"""

		tb = wx.ToolBar(self, wx.NewIdRef())
		tb.SetToolBitmapSize((16,16))# this required for non-standard size buttons on MSW

		### Add tool
		tb.AddTool(Menu.ID_NEW_LIB, "", load_and_resize_image('plus.png'), shortHelp=_('Import'))
		tb.AddTool(Menu.ID_DELETE_LIB, "", load_and_resize_image('minus.png'), shortHelp=_('Delete'))
		tb.AddTool(Menu.ID_REFRESH_LIB, "", load_and_resize_image('reload.png'), shortHelp=_('Reload'))
		tb.AddTool(Menu.ID_HELP_LIB, "", load_and_resize_image('info.png'), shortHelp=_('Help'))
		tb.AddCheckTool(Menu.ID_MCC_LIB, '', load_and_resize_image('a-z.png'), shortHelp='MacCabe')
		tb.ToggleTool(Menu.ID_MCC_LIB, True)

		mainW = self.GetTopLevelParent()

		### Binding
		self.Bind(wx.EVT_TOOL, mainW.OnImport, id=Menu.ID_NEW_LIB)
		self.Bind(wx.EVT_TOOL, self.tree.OnDelete, id=Menu.ID_DELETE_LIB)
		#wx.EVT_TOOL(self, Menu.ID_IMPORT_LIB, mainW.OnImport)
		self.Bind(wx.EVT_TOOL, self.tree.OnUpdateAll, id=Menu.ID_REFRESH_LIB)
		self.Bind(wx.EVT_TOOL, self.OnShowLibraryHelp, id=Menu.ID_HELP_LIB)  # Modifié ici
		self.Bind(wx.EVT_TOOL, self.tree.OnMCCClick, id=Menu.ID_MCC_LIB) 

		tb.Realize()

		return tb

	def OnShowLibraryHelp(self, event):
		"""Show help dialog about library management"""
		
		help_msg = _(
			"LIBRARY MANAGEMENT PANEL\n\n"
			"═══════════════════════════════════════\n\n"
			"OVERVIEW:\n\n"
			"The library panel allows you to manage DEVS model libraries.\n"
			"Libraries are collections of reusable DEVS components that can be\n"
			"instantiated in your diagrams using drag-and-drop.\n\n"
			"═══════════════════════════════════════\n\n"
			"TOOLBAR BUTTONS:\n\n"
			"• Import (+): Add a new library to DEVSimPy.\n"
			"  You can import:\n"
			"  - Local directories containing Python DEVS models\n"
			"  - ZIP archives (.zip) with model collections\n"
			"  - Remote libraries from URLs\n\n"
			"• Delete (-): Remove selected library from the tree.\n"
			"  Warning: This only removes from DEVSimPy, not from disk.\n\n"
			"• Reload (⟳): Refresh all libraries to detect new models.\n"
			"  Use this after modifying model files externally.\n\n"
			"• Help (i): Show this help message.\n\n"
			"• A-Z: Toggle alphabetical sorting of models in libraries.\n"
			"  When enabled, models are sorted by name.\n"
			"  When disabled, models appear in directory order.\n\n"
			"═══════════════════════════════════════\n\n"
			"LIBRARY TREE:\n\n"
			"• Folders: Represent library directories\n"
			"• Green blocks: Atomic DEVS models (CodeBlock)\n"
			"• Yellow blocks: Coupled DEVS models (ContainerBlock)\n"
			"• Gray items: Invalid or incompatible models\n\n"
			"Right-click on items for context menu options:\n"
			"- Edit: Open model Python file in editor\n"
			"- Documentation: View model documentation\n"
			"- Properties: Inspect model metadata\n"
			"- Rename: Change model label\n"
			"- Export: Save model to file\n\n"
			"═══════════════════════════════════════\n\n"
			"SEARCH FIELD:\n\n"
			"Type to search for models by name across all libraries.\n"
			"Results appear in a temporary search tree.\n"
			"Click the X button to clear search and return to main tree.\n\n"
			"═══════════════════════════════════════\n\n"
			"HOW TO USE MODELS:\n\n"
			"1. Expand library folders to see available models\n"
			"2. Drag a model from the library tree\n"
			"3. Drop it onto the diagram canvas (right panel)\n"
			"4. The model is instantiated and ready to use\n"
			"5. Connect models by dragging from output to input ports\n\n"
			"═══════════════════════════════════════\n\n"
			"LIBRARY TYPES:\n\n"
			"• Domain Libraries: Official DEVSimPy model collections\n"
			"  (Physics, Networks, Control, etc.)\n\n"
			"• User Libraries: Your custom model collections\n"
			"  Add them via Import button\n\n"
			"• Remote Libraries: Libraries loaded from URLs\n"
			"  Automatically updated when available\n\n"
			"═══════════════════════════════════════\n\n"
			"TIPS:\n\n"
			"- Use search to quickly find models in large libraries\n"
			"- Keep libraries organized in thematic folders\n"
			"- Reload after editing model Python files\n"
			"- Right-click models to view documentation\n"
			"- Use alphabetical sorting for easier navigation\n"
			"- Import ZIP archives to share library collections\n\n"
			"═══════════════════════════════════════\n\n"
			"CREATING YOUR OWN LIBRARIES:\n\n"
			"1. Create a folder with your Python DEVS models\n"
			"2. Each model should inherit from DomainBehavior/DomainStructure\n"
			"3. Use Import button to add your folder to DEVSimPy\n"
			"4. Your models appear in the library tree\n"
			"5. Optionally, create a ZIP archive for distribution\n\n"
			"For more information, consult the DEVSimPy documentation."
		)
		
		try:
			import wx.lib.dialogs
			dlg = wx.lib.dialogs.ScrolledMessageDialog(
				self, 
				help_msg, 
				_("Library Management Help"),
				size=(650, 600)
			)
			dlg.ShowModal()
			dlg.Destroy()
		except Exception as e:
			# Fallback si wx.lib.dialogs n'est pas disponible
			wx.MessageBox(
				help_msg,
				_("Library Management Help"),
				wx.OK | wx.ICON_INFORMATION
			)


	def __set_tips(self):
		"""
		"""

		self.propToolTip =[_("Select model and instantiate it in the diagram (right part) using a drag-and-drop.")]
		
		self.SetToolTip(self.propToolTip[0])
