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
import os

from LibraryTree import LibraryTree

import Menu

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

		self.SetToolTipString(_("Find model in the library depending its name."))

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
		wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY, name=name)

		libSizer = wx.BoxSizer(wx.VERTICAL)

		### Creation de l'arbre des librairies
		self.tree = LibraryTree(self, wx.ID_ANY, wx.DefaultPosition, style=wx.TR_DEFAULT_STYLE|wx.TR_HIDE_ROOT|wx.TR_LINES_AT_ROOT|wx.TR_HAS_BUTTONS|wx.SUNKEN_BORDER)

		mainW = parent.GetTopLevelParent()

		### lecture de ChargedDomainList dans .devsimpy
		cfg_domain_list = mainW.cfg.Read('ChargedDomainList')
		chargedDomainList = eval(cfg_domain_list) if cfg_domain_list else []

		self.tree.Populate(chargedDomainList)

		### Creation de l'arbre de recherche hide au depart (voir __do_layout)
		self.searchTree = LibraryTree(self, wx.ID_ANY, wx.DefaultPosition, style=wx.TR_DEFAULT_STYLE|wx.TR_HIDE_ROOT|wx.TR_MULTIPLE|wx.TR_LINES_AT_ROOT|wx.TR_HAS_BUTTONS|wx.SUNKEN_BORDER)

		### Creation de l'option de recherche dans tree
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
		"""	creates one of the toolbars
		The buttons act like radio buttons, setting a mode for the Panel
		Only one of them is pressed at a time. The SetMode() method handles this
		"""

		tb = wx.ToolBar( self, -1 )
		self.ToolBar = tb
		tb.SetToolBitmapSize( ( 16, 16 ) )# this required for non-standard size buttons on MSW

		tb.AddTool(Menu.ID_NEW_LIB, wx.Bitmap(os.path.join(ICON_PATH_16_16,'db+.png')), shortHelpString=_('New library'), longHelpString=_('Create a new directory in the Domain directory'))
		tb.AddTool(Menu.ID_IMPORT_LIB, wx.Bitmap(os.path.join(ICON_PATH_16_16,'dbimport.png')), shortHelpString=_('Import library'), longHelpString=_('Call the import manager'))
		tb.AddTool(Menu.ID_REFRESH_LIB, wx.Bitmap(os.path.join(ICON_PATH_16_16,'db_refresh.png')), shortHelpString=_('Refresh library'), longHelpString=_('Force the refresh of the loaded libraries'))
		tb.AddTool(Menu.ID_HELP_LIB, wx.Bitmap(os.path.join(ICON_PATH_16_16, 'dbinfo.png')), shortHelpString=_('Help'), longHelpString=_('Information about import manager'))

		mainW = self.GetTopLevelParent()

		wx.EVT_TOOL(self, Menu.ID_NEW_LIB, mainW.OnNewLib)
		wx.EVT_TOOL(self, Menu.ID_IMPORT_LIB, mainW.OnImport)
		wx.EVT_TOOL(self, Menu.ID_REFRESH_LIB, self.tree.OnUpdateAll)
		wx.EVT_TOOL(self, Menu.ID_HELP_LIB, self.tree.OnInfo)

		tb.Realize()
		return tb

	def __set_tips(self):
		"""
		"""

		self.propToolTip =[_("Select model and instantiate it in the diagram (right part) using a drag-and-drop.")]
		self.SetToolTipString(self.propToolTip[0])