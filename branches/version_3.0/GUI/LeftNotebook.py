#!/usr/bin/env python
# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# LeftNotebook.py --- DEVSimPy - The Python DEVS GUI modeling and simulation software 
#                     --------------------------------
#                            Copyright (c) 2013
#                              Laurent CAPOCCHI
#                        SPE - University of Corsica
#                     --------------------------------
# Version 3.0                                      last modified:  08/01/13
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GLOBAL VARIABLES AND FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import os
import wx

import Core.Components.Container as Container
import GUI.LibraryTree as LibraryTree
import GUI.SearchLib as SearchLib
import Core.Patterns.Observer as Observer

_ = wx.GetTranslation

#-------------------------------------------------------------------
class LeftNotebook(wx.Notebook, Observer.Observer):
	"""
	"""

	def __init__(self, *args, **kwargs):
		"""
		Notebook class that allows overriding and adding methods for the left pane of DEVSimPy

		@param parent: parent windows
		@param id: id
		@param pos: windows position
		@param size: windows size
		@param style: windows style
		@param name: windows name
		"""

		wx.Notebook.__init__(self, *args, **kwargs)

		### Define drop source
		#DropTarget.SOURCE = self

		### Add pages
		self.libPanel = wx.Panel(self, wx.ID_ANY)
		self.propPanel = wx.Panel(self, wx.ID_ANY)

		### selected model for libPanel managing
		self.selected_model = None

		### Creation de l'arbre des librairies
		self.tree = LibraryTree.LibraryTree(self.libPanel, wx.ID_ANY, wx.DefaultPosition, style=wx.TR_DEFAULT_STYLE | wx.TR_HIDE_ROOT | wx.TR_LINES_AT_ROOT | wx.TR_HAS_BUTTONS | wx.SUNKEN_BORDER)

		mainW = self.GetTopLevelParent()

		### lecture de ChargedDomainList dans .devsimpy
		cfg_domain_list = mainW.cfg.Read('ChargedDomainList')
		chargedDomainList = eval(cfg_domain_list) if cfg_domain_list else []

		self.tree.Populate(chargedDomainList)

		### Creation de l'arbre de recherche hide au depart (voir __do_layout)
		self.searchTree = LibraryTree.LibraryTree(self.libPanel, wx.ID_ANY, wx.DefaultPosition,
												  style=wx.TR_DEFAULT_STYLE | wx.TR_HIDE_ROOT | wx.TR_MULTIPLE | wx.TR_LINES_AT_ROOT | wx.TR_HAS_BUTTONS | wx.SUNKEN_BORDER)

		### Creation de l'option de recherche dans tree
		self.search = SearchLib.SearchLib(self.libPanel, size=(200, -1), style=wx.TE_PROCESS_ENTER)

		self.tree.UpdateAll()

		self.__set_properties()
		self.__do_layout()
		self.__set_tips()

		self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.__PageChanged)

	def __set_properties(self):
		"""
		"""
		imgList = wx.ImageList(16, 16)
		for img in [os.path.join(ICON_PATH_16_16,'db.png'), os.path.join(ICON_PATH_16_16,'properties.png'), os.path.join(ICON_PATH_16_16,'simulation.png')]:
			imgList.Add(wx.Image(img, wx.BITMAP_TYPE_PNG).ConvertToBitmap())
		self.AssignImageList(imgList)

		self.libPanel.SetBackgroundColour(wx.WHITE)
		self.propPanel.SetBackgroundColour(wx.WHITE)
		self.searchTree.Hide()

	def GetTree(self):
		return self.tree

	def GetSearchTree(self):
		return self.searchTree

	def __set_tips(self):
		"""
		"""

		self.propToolTip = [_("No model selected.\nChose a model to show in this panel its properties"), _("You can change the properties by editing the cellule")]
		self.propPanel.SetToolTipString(self.propToolTip[0])

	def __do_layout(self):
		"""
		"""
		libSizer = wx.BoxSizer(wx.VERTICAL)
		libSizer.Add(self.tree, 1, wx.EXPAND)
		libSizer.Add(self.searchTree, 1, wx.EXPAND)
		libSizer.Add(self.search, 0, wx.BOTTOM | wx.EXPAND)

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

	def Update(self, concret_subject=None):
		""" Update method that manages the panel propertie depending of the selected model in the canvas
		"""

		state = concret_subject.GetState()
		canvas = state['canvas']
		model = state['model']

		if self.GetSelection() == 1:
			if model:
				if model != self.selected_model:
					newContent = Container.AttributeEditor(self.propPanel, wx.ID_ANY, model, canvas)
					self.UpdatePropertiesPage(newContent)
					self.selected_model = model
					self.propPanel.SetToolTipString(self.propToolTip[1])
			else:
				self.UpdatePropertiesPage(self.defaultPropertiesPage())
				self.selected_model = None
				self.propPanel.SetToolTipString(self.propToolTip[0])

	def defaultPropertiesPage(self):
		"""
		"""

		propContent = wx.StaticText(self.propPanel, wx.ID_ANY, _("Properties panel"))
		sum_font = propContent.GetFont()
		sum_font.SetWeight(wx.BOLD)
		propContent.SetFont(sum_font)

		return propContent

	def UpdatePropertiesPage(self, panel=None):
		"""	Update the propPanel with teh new panel param of the model
		"""
		sizer = self.propPanel.GetSizer()
		sizer.DeleteWindows()
		sizer.Add(panel, 1, wx.EXPAND | wx.ALL)
		sizer.Layout()

