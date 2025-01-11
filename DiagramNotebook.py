# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# DiagramNoteBook.py ---
#                     --------------------------------
#                            Copyright (c) 2020
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 03/15/2020
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
import builtins

from pubsub import pub

import Container
import Menu

from DetachedFrame import DetachedFrame
from PrintOut import Printable
from Utilities import printOnStatusBar, load_and_resize_image

_ = wx.GetTranslation

#-------------------------------------------------------------------
class GeneralNotebook(Printable):
	"""
	"""

	def __init__(self, *args, **kwargs):
		""" General Notebook class for Diagram Notebook on the right part of DEVSimPy.
		"""

		# for splash screen
		pub.sendMessage('object.added', message='Loading notebook diagram...\n')
		
		Printable.__init__(self)

		# local copy
		self.parent = args[0]
		self.pages = []			# keeps track of pages

		### to propagate the dsp file path in __setstate__ of Block object
		self.current_dsp_file_path = ""

		#icon under tab
		imgList = wx.ImageList(16, 16)
		for img in ['network.png']:
			imgList.Add(load_and_resize_image(img))
		self.AssignImageList(imgList)

		### binding
		self.Bind(wx.EVT_LEFT_DCLICK, self.__AddPage)

	def GetPages(self):
		""" Return pages array.
		"""
		return self.pages

	def __AddPage(self, event):
		""" Add page.
		"""

		self.AddEditPage(_("Diagram%d")%len(self.pages))

	def AddEditPage(self, title, defaultDiagram = None):
		""" Adds a new page for editing to the notebook and keeps track of it.

			@type title: string
			@param title: Title for a new page
		"""

		### title page list
		title_pages = [p.name for p in self.pages]

		### occurrence of title in existing title pages
		c = title_pages.count(title)
		title = title+"(%d)"%c if c != 0 else title

		### new page
		newPage = Container.ShapeCanvas(self, wx.NewIdRef(), name=title)

		### new diagram
		d = defaultDiagram or Container.Diagram()
		d.SetParent(newPage)

		### diagram and background new page setting
		newPage.SetDiagram(d)

		### print canvas variable setting
		self.print_canvas = newPage
		self.print_size = self.GetSize()

		self.pages.append(newPage)
		self.AddPage(newPage, title, imageId=0)

		self.SetSelection(self.GetPageCount()-1)

	def OnClearPage(self, evt):
		""" Clear page.

			@type evt: event
			@param  evt: Event Object, None by default
		"""
		id = self.GetSelection()

		if self.GetPageCount() > 0:
			canvas = self.GetPage(id)
			diagram = canvas.GetDiagram()

			diagram.DeleteAllShapes()
			diagram.modified = True

			canvas.deselect()
			canvas.Refresh()

	def OnRenamePage(self, evt):
		""" Rename the title of notebook page.

			@type evt: event
			@param  evt: Event Object, None by default
		"""
		selection = self.GetSelection()
		dlg = wx.TextEntryDialog(self, _("Enter a new name:"), _("Diagram Manager"))
		dlg.SetValue(self.GetPageText(selection))

		if dlg.ShowModal() == wx.ID_OK:
			txt = dlg.GetValue()
			self.SetPageText(selection,txt)

		dlg.Destroy()

	def OnDetachPage(self, evt):
		"""
			Detach the notebook page on frame.

			@type evt: event
			@param  evt: Event Object, None by default
		"""

		selection = self.GetSelection()
		canvas = self.GetPage(selection)
		title = self.GetPageText(selection)

		frame = DetachedFrame(canvas, wx.NewIdRef(), title, canvas.GetDiagram())
		frame.SetIcon(self.parent.GetIcon())
		frame.SetFocus()
		frame.Show()

	def OnPageChanged(self, evt):
		""" Page has been changed.
		"""

		id = self.GetSelection()

		### id is -1 when DEVSimPy is starting
		if id != -1 and self.GetPageCount() > 0:

			canvas = self.GetPage(id)
			self.print_canvas = canvas
			self.print_size = self.GetSize()

			### action history
			if hasattr(self.parent, 'tb'):
				self.parent.tb.EnableTool(wx.ID_UNDO, not len(canvas.stockUndo) == 0)
				self.parent.tb.EnableTool(wx.ID_REDO, not len(canvas.stockRedo) == 0)

			### refresh canvas
			canvas.deselect()
			canvas.Refresh()

			### update status bar depending on the diagram modification
			if hasattr(self.parent, 'statusbar'):
				diagram = canvas.GetDiagram()
				txt = _('%s modified')%(self.GetPageText(id)) if diagram.modify else ""
				printOnStatusBar(self.parent.statusbar,{0:txt})

		### propagate event also error in OnClosePage because GetSelection is wrong
		evt.Skip()

	def DeleteBuiltinConstants(self):
		""" Delete builtin constants for the diagram.
		"""
		try:
			name = self.GetPageText(self.GetSelection())
			del builtins.__dict__[str(os.path.splitext(name)[0])]
		except Exception:
			pass
			#sys.stdout.write("Constants builtin not delete for %s : %s"%(name, info))

### ---------------------------------------------
### if flatnotebook can be imported, we work with it
### more information about FlatNotebook http://wiki.wxpython.org/Flatnotebook%20(AGW)

USE_FLATNOTEBOOK = False

try:
	if (wx.VERSION >= (2, 8, 9, 2)):
		import wx.lib.agw.flatnotebook as fnb
	else:
		import wx.lib.flatnotebook as fnb
	USE_FLATNOTEBOOK = True
except:
	pass

if USE_FLATNOTEBOOK:
	#
	# FlatNotebook generalized class
	#

	class DiagramNotebook(fnb.FlatNotebook, GeneralNotebook):
		""" Diagram FlatNotebook class.
		"""

		###
		def __init__(self, *args, **kwargs):
			""" Constructor.
				FlatNotebook class that allows overriding and adding methods for the right pane of DEVSimPy
			"""
			fnb.FlatNotebook.__init__(self, *args, **kwargs)
			GeneralNotebook.__init__(self, *args, **kwargs)

			self.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSING, self.OnClosingPage)
			self.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CHANGED, self.OnPageChanged)

			self.CreateRightClickMenu()
			self.SetRightClickMenu(self._rmenu)

		def CreateRightClickMenu(self):
			""" Right click has been invoked and contextual menu is displayed.
			"""

			self._rmenu = Menu.DiagramTabPopupMenu(self).get()

			### 4 because 3 is the separator object in Menu.py !!!
			close_item = self._rmenu.FindItemByPosition(4)
			#close_item.Enable(self.GetPageCount() > 1)

			### unbind last event binding with OnClose Page
			self.Unbind(wx.EVT_MENU, close_item)

			### bind event with new OnDeletePage
			self.Bind(wx.EVT_MENU, self.OnClosePage, close_item)

		###
		def OnClosingPage(self, evt):
			""" Called when tab is closed.
				With FlatNoteBock, this method is used to ask if diagram should be saved and to update properties panel.
			"""

			id = self.GetSelection()
			canvas = self.GetPage(id)
			diagram = canvas.GetDiagram()

			mainW =  self.GetTopLevelParent()

			val = None

			if diagram.modify:
				title = self.GetPageText(id).replace("*",'')
				dlg = wx.MessageDialog(self, _('%s\nSave changes to the current diagram?')%(title), _("Save diagram"), wx.YES_NO | wx.YES_DEFAULT | wx.CANCEL |wx.ICON_QUESTION)
				val = dlg.ShowModal()

				if val == wx.ID_YES:
					mainW.OnSaveFile(evt)
				elif val == wx.ID_NO:
					self.DeleteBuiltinConstants()
				dlg.Destroy()

			else:
				self.DeleteBuiltinConstants()

			### if user cancel the delete process, we stop the event propagation in order to enable the DeletePage function
			if val == wx.ID_CANCEL:
				evt.Veto()
			else:
				self.pages.remove(canvas)

				### update (clear) of properties panel (Control notebook)
				propPanel = mainW.GetControlNotebook().GetPropPanel()
				### If properties panel is active, we update it
				if propPanel:
					propPanel.UpdatePropertiesPage(propPanel.defaultPropertiesPage())

				evt.Skip()

		def DeletePage(self, *args, **kwargs):
			""" Delete the current diagram.
			"""
			try:
				canvas = self.GetPage(args[0])
			except IndexError:
				return False
			else:
				result = fnb.FlatNotebook.DeletePage(self, *args, **kwargs)
				return canvas not in self.pages

		def OnClosePage(self, evt):
			""" Close the page.
			"""
			return self.DeletePage(self.GetSelection())

else:

	#
	# Classic Notebook class
	#

	class DiagramNotebook(wx.Notebook, GeneralNotebook):
		""" Diagram classic NoteBook class.
		"""

		def __init__(self, *args, **kwargs):
			""" Notebook class that allows overriding and adding methods for the right pane of DEVSimPy.
			"""

			wx.Notebook.__init__(self, *args, **kwargs)
			GeneralNotebook.__init__(self,*args, **kwargs)

			self.Bind(wx.EVT_RIGHT_DOWN, self.__ShowMenu)
			self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)

		def __ShowMenu(self, evt):
			"""	Callback for the right click on a tab. Displays the menu.

				@type   evt: event
				@param  evt: Event Object, None by default
			"""

			### mouse position
			pos = evt.GetPosition()
			### pointed page and flag
			page,flag = self.HitTest(pos)

			### if no where click (don't hit with windows)
			if flag == wx.BK_HITTEST_NOWHERE:
				self.PopupMenu(Menu.DiagramNoTabPopupMenu(self).get(), pos)
			### if tab has been clicked
			elif flag == wx.BK_HITTEST_ONLABEL:
				self.PopupMenu(Menu.DiagramTabPopupMenu(self).get(), pos)
			else:
				pass

		def OnClosePage(self, evt):
			""" Close current page.

				@type evt: event
				@param  evt: Event Object, None by default
			"""

			if self.GetPageCount() <= 0:
				return

			id = self.GetSelection()
			canvas = self.GetPage(id)
			diagram = canvas.GetDiagram()

			mainW =  self.GetTopLevelParent()

			if diagram.modify:
				title = self.GetPageText(id).replace('*','')
				dlg = wx.MessageDialog(self, _('%s\nSave changes to the current diagram?')%(title), _("Save diagram"), wx.YES_NO | wx.YES_DEFAULT | wx.CANCEL |wx.ICON_QUESTION)
				val = dlg.ShowModal()

				if val == wx.ID_YES:
					mainW.OnSaveFile(evt)
				elif val == wx.ID_NO:
					self.DeleteBuiltinConstants()
					self.pages.remove(canvas)
					if not self.DeletePage(id):
						sys.stdout.write(_("%s not deleted! \n"%(title)))
				else:
					dlg.Destroy()

					return False

				dlg.Destroy()

			else:

				self.DeleteBuiltinConstants()
				self.pages.remove(canvas)

				if not self.DeletePage(id):
					sys.stdout.write(_("%s not deleted ! \n"%(title)))

			### clear "property" notebook
			nb1 = mainW.GetControlNotebook()
			propPanel = nb1.GetPropPanel()
			### if page is active, then update and stay on this
			if propPanel:
				propPanel.UpdatePropertiesPage(propPanel.defaultPropertiesPage())

			return True
