# -*- coding: utf-8 -*-

""" 
	Authors: T. Ville (tim.ville@me.com)
	Date: 04/11/2013
	Description:
	Depends: wx, devsimpy
"""

### ------------------------------------------------------------------------------------------- ###
# ===========================================Imports============================================= #
### ------------------------------------------------------------------------------------------- ###

import wx
import pluginmanager

### ------------------------------------------------------------------------------------------- ###
# =======================================Graphical  tools======================================== #
### ------------------------------------------------------------------------------------------- ###

@pluginmanager.register("START_TEST")
def start_test(**kwargs):
	global frame

	parent = kwargs['parent']

	mainW = wx.GetApp().GetTopWindow()
	nb = mainW.nb2
	diagram = nb.GetPage(nb.GetSelection()).diagram

	### plugin main frame instanciation
	frame = BehaviorAssistant(parent, wx.ID_ANY)

	### disable suspend and log button
	parent._btn3.Disable()
	parent._btn4.Disable()

@pluginmanager.register("SIM_TEST")
def test_manager(**kwargs):
	global frame

	model = kwargs['model']

	msg = kwargs['msg']
	mainW = wx.GetApp().GetTopWindow()
	nb = mainW.nb2
	diagram = nb.GetPage(nb.GetSelection()).diagram
	master = diagram.getDEVSModel()

	### if frame is deleted (occur for dynamic coupled model)
	if not isinstance(frame, wx.Frame):
		return

	### DEVSimPy block
	if hasattr(model, 'getBlockModel'):

			try:
			### step engine
				frame.flag = False
				while not frame.flag:
					pass
			except:
				pass


class BehaviorAssistant(wx.Frame):
	"""docstring for BehaviorAssistant"""
	def __init__(self, *args, **kwargs):

		kwargs["style"] = wx.DEFAULT_FRAME_STYLE
		kwargs["size"] = (1220, 750)

		super(BehaviorAssistant, self).__init__(*args, **kwargs)

		self.ConfigGUI()
		self.Show()

	def ConfigGUI(self):

		### Menu bar config------------------------------------------------------------------------
		menubar = wx.MenuBar()

		### File menu----------------------------------------------------------
		file_menu = wx.Menu()
		leave = wx.MenuItem(file_menu, wx.NewId(), _('&Quit\tCtrl+Q'), _('Quit the application'))
		file_menu.AppendItem(leave)
		### -------------------------------------------------------------------

		### Edition menu-------------------------------------------------------
		edition = wx.Menu()
		specs = wx.MenuItem(edition, wx.NewId(), _('&Specs\tCtrl+T'), _('Edit specifications'))
		model = wx.MenuItem(edition, wx.NewId(), _('&Model\tCtrl+M'), _('Edit model DEVS'))
		edition.AppendItem(specs)
		edition.AppendItem(model)
		### -------------------------------------------------------------------

		### Run menu--------------------------------------------------------
		run = wx.Menu()
		test = wx.MenuItem(run, wx.NewId(), _('&Run\tCtrl+R'), _('Run test on model'))
		run.AppendItem(test)
		### -------------------------------------------------------------------

		### Help menu----------------------------------------------------------
		help = wx.Menu()
		helper = wx.MenuItem(help, wx.NewId(), _('&Help\tCtrl+H'), _('Show help'))
		help.AppendItem(helper)
		### -------------------------------------------------------------------

		menubar.Append(file_menu, _('&File'))
		menubar.Append(edition, _('&Edition'))
		menubar.Append(run, _('&Run'))
		menubar.Append(help, _('&Help'))

		self.SetMenuBar(menubar)
		### ---------------------------------------------------------------------------------------
		#=========================================================================================#
		### Panel config---------------------------------------------------------------------------
		
		self.panel = wx.Panel(self)