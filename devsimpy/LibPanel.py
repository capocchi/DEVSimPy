# -*- coding: utf-8 -*-

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
		"""	creates one of the tool-bars
		The buttons act like radio buttons, setting a mode for the Panel
		Only one of them is pressed at a time. The SetMode() method handles this
		"""

		tb = wx.ToolBar(self, wx.NewIdRef())
		#self.ToolBar = tb
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
		self.Bind(wx.EVT_TOOL, self.tree.OnInfo, id=Menu.ID_HELP_LIB)
		self.Bind(wx.EVT_TOOL, self.tree.OnMCCClick, id=Menu.ID_MCC_LIB) 

		tb.Realize()

		return tb

	def __set_tips(self):
		"""
		"""

		self.propToolTip =[_("Select model and instantiate it in the diagram (right part) using a drag-and-drop.")]
		
		self.SetToolTip(self.propToolTip[0])
