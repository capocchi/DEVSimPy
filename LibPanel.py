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

		if wx.VERSION_STRING < 4.0:
			self.SetToolTipString(_("Find model in the library depending its name."))
		else:
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
		wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY, name=name)

		libSizer = wx.BoxSizer(wx.VERTICAL)

		### create libraries tree
		self.tree = LibraryTree(self, wx.ID_ANY, wx.DefaultPosition, style=wx.TR_DEFAULT_STYLE|wx.TR_HIDE_ROOT|wx.TR_LINES_AT_ROOT|wx.TR_HAS_BUTTONS|wx.SUNKEN_BORDER)

		mainW = parent.GetTopLevelParent()

		### read ChargedDomainList from .devsimpy
		cfg_domain_list = mainW.cfg.Read('ChargedDomainList')
		chargedDomainList = eval(cfg_domain_list) if cfg_domain_list else []

		self.tree.Populate(chargedDomainList)

		### search tree that is hide when starting devsimpy (see __do_layout)
		self.searchTree = LibraryTree(self, wx.ID_ANY, wx.DefaultPosition, style=wx.TR_DEFAULT_STYLE|wx.TR_HIDE_ROOT|wx.TR_MULTIPLE|wx.TR_LINES_AT_ROOT|wx.TR_HAS_BUTTONS|wx.SUNKEN_BORDER)

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

		tb = wx.ToolBar( self, -1 )
		self.ToolBar = tb
		tb.SetToolBitmapSize( ( 16, 16 ) )# this required for non-standard size buttons on MSW

		### for Phoenix version ()
		if wx.VERSION_STRING < 4.0:
			tb.AddTool(Menu.ID_NEW_LIB, wx.Bitmap(os.path.join(ICON_PATH_16_16,'db+2.png')), shortHelpString=_('New library'), longHelpString=_('Create or import a new directory'))
			tb.AddTool(Menu.ID_DELETE_LIB, wx.Bitmap(os.path.join(ICON_PATH_16_16,'db-2.png')), shortHelpString=_('Delete library'), longHelpString=_('Delete the selected librarie'))
			tb.AddTool(Menu.ID_REFRESH_LIB, wx.Bitmap(os.path.join(ICON_PATH_16_16,'db_refresh2.png')), shortHelpString=_('Refresh library'), longHelpString=_('Force the refresh of the loaded libraries'))
			#tb.AddTool(Menu.ID_IMPORT_LIB, wx.Bitmap(os.path.join(ICON_PATH_16_16,'dbimport2.png')), shortHelpString=_('Import library'), longHelpString=_('Call the import manager'))
			tb.AddTool(Menu.ID_HELP_LIB, wx.Bitmap(os.path.join(ICON_PATH_16_16, 'dbinfo2.png')), shortHelpString=_('Help'), longHelpString=_('Information about import manager'))
		else:
			tb.AddTool(Menu.ID_NEW_LIB, "",wx.Bitmap(os.path.join(ICON_PATH_16_16,'db+2.png')), shortHelp=_('New library'))
			tb.AddTool(Menu.ID_DELETE_LIB, "",wx.Bitmap(os.path.join(ICON_PATH_16_16,'db-2.png')), shortHelp=_('Delete library'))
			tb.AddTool(Menu.ID_REFRESH_LIB, "",wx.Bitmap(os.path.join(ICON_PATH_16_16,'db_refresh2.png')), shortHelp=_('Refresh library'))
			tb.AddTool(Menu.ID_HELP_LIB, "",wx.Bitmap(os.path.join(ICON_PATH_16_16, 'dbinfo2.png')), shortHelp=_('Help'))
			

		mainW = self.GetTopLevelParent()

		### for Phoenix version ()
		if wx.VERSION_STRING < 4.0:
			wx.EVT_TOOL(self, Menu.ID_NEW_LIB, mainW.OnImport)
			wx.EVT_TOOL(self, Menu.ID_DELETE_LIB, self.tree.OnDelete)
			#wx.EVT_TOOL(self, Menu.ID_IMPORT_LIB, mainW.OnImport)
			wx.EVT_TOOL(self, Menu.ID_REFRESH_LIB, self.tree.OnUpdateAll)
			wx.EVT_TOOL(self, Menu.ID_HELP_LIB, self.tree.OnInfo)
		else:
			self.Bind(wx.EVT_TOOL, mainW.OnImport, id=Menu.ID_NEW_LIB)
			self.Bind(wx.EVT_TOOL, self.tree.OnDelete, id=Menu.ID_DELETE_LIB)
			#wx.EVT_TOOL(self, Menu.ID_IMPORT_LIB, mainW.OnImport)
			self.Bind(wx.EVT_TOOL, self.tree.OnUpdateAll, id=Menu.ID_REFRESH_LIB)
			self.Bind(wx.EVT_TOOL, self.tree.OnInfo, id=Menu.ID_HELP_LIB)

		tb.Realize()
		return tb

	def __set_tips(self):
		"""
		"""

		self.propToolTip =[_("Select model and instantiate it in the diagram (right part) using a drag-and-drop.")]
		### for Phoenix version ()
		if wx.VERSION_STRING < 4.0:
			self.SetToolTipString(self.propToolTip[0])
		else:
			self.SetToolTip(self.propToolTip[0])
