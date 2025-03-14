# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# PreferencesGUI.py ---
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
import builtins
import shutil
import sys
import configparser
import copy
import importlib

import wx.lib.filebrowsebutton as filebrowse

_ = wx.GetTranslation

from HtmlWindow import HtmlFrame

from PluginsGUI import PluginsPanel, GeneralPluginsList
from Utilities import playSound, GetUserConfigDir, GetWXVersionFromIni, AddToInitFile, DelToInitFile, install, getTopLevelWindow, load_and_resize_image
from Decorators import BuzyCursorNotification
from AIAdapter import AdapterFactory

import ReloadModule
import Menu

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# CLASSES DEFINITION
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

class GeneralPanel(wx.Panel):
	""" General preferences panel
	"""

	### wxPython version
	wxv = [wx.VERSION_STRING]

	def __init__(self, parent):
		"""
			Constructor.
		"""
		wx.Panel.__init__(self, parent)

		self.InitUI()

	def InitUI(self):

		### FileBrowse
		self.plugin_dir = filebrowse.DirBrowseButton(self, wx.NewIdRef(), startDirectory=PLUGINS_PATH, labelText=_("Plug-ins directory:"), toolTip=_("Change the plug-ins directory"), dialogTitle=_("Plug-ins directory..."))
		self.domain_dir = filebrowse.DirBrowseButton(self, wx.NewIdRef(), startDirectory=DOMAIN_PATH, labelText=_("Library directory:"), toolTip=_("Change the library directory"), dialogTitle=_("Libraries directory..."))
		self.out_dir = filebrowse.DirBrowseButton(self, wx.NewIdRef(), startDirectory=OUT_DIR, labelText=_("Output directory:"), toolTip=_("Change the output directory"), dialogTitle=_("Output directory..."))

		self.plugin_dir.SetValue(PLUGINS_PATH)
		self.domain_dir.SetValue(DOMAIN_PATH)
		self.out_dir.SetValue(OUT_DIR)

		### StaticText
		self.st1 = wx.StaticText(self, wx.NewIdRef(), _("Number of recent files:"))
		self.st2 = wx.StaticText(self, wx.NewIdRef(), _("Font size:"))
		self.st3 = wx.StaticText(self, wx.NewIdRef(), _("Deep of history item:"))
		self.st4 = wx.StaticText(self, wx.NewIdRef(), _("wxPython version:"))

		self.st1.SetToolTipString = self.st1.SetToolTip 
		self.st2.SetToolTipString = self.st2.SetToolTip
		self.st3.SetToolTipString = self.st3.SetToolTip
		self.st4.SetToolTipString = self.st4.SetToolTip

		self.st1.SetToolTipString(_("Feel free to change the length of list defining the recent opened files."))
		self.st2.SetToolTipString(_("Feel free to change the font size of DEVSimpy."))
		self.st3.SetToolTipString(_("Feel free to change the number of item for undo/redo command."))
		self.st4.SetToolTipString(_("Feel free to change the version of wxpython used loaded by DEVSimPy."))

		### number of opened file
		self.nb_opened_file = wx.SpinCtrl(self, wx.NewIdRef(), '')
		self.nb_opened_file.SetRange(2, 20)
		self.nb_opened_file.SetValue(NB_OPENED_FILE)

		### Block font size
		self.font_size = wx.SpinCtrl(self, wx.NewIdRef(), '')
		self.font_size.SetRange(2, 20)
		self.font_size.SetValue(FONT_SIZE)

		### number of undo/redo items
		self.nb_history_undo = wx.SpinCtrl(self, wx.NewIdRef(), '')
		self.nb_history_undo.SetRange(2, 100)
		self.nb_history_undo.SetValue(NB_HISTORY_UNDO)

		### CheckBox for transparancy
		self.cb1 = wx.CheckBox(self, wx.NewIdRef(), _('Transparency'))
		self.cb1.SetToolTipString = self.cb1.SetToolTip
		self.cb1.SetToolTipString(_("Transparency for the detached frame of diagrams"))
		self.cb1.SetValue(getattr(builtins, 'TRANSPARENCY'))

		### CheckBox for notification
		self.cb11 = wx.CheckBox(self, wx.NewIdRef(), _('Notififcations'))
		self.cb11.SetToolTipString = self.cb11.SetToolTip
		self.cb11.SetToolTipString(_("Enable the notification messages"))
		self.cb11.SetValue(getattr(builtins, 'NOTIFICATION'))
			
		self.cb2 = wx.ComboBox(self, wx.NewIdRef(), GetWXVersionFromIni(), choices=GeneralPanel.wxv, style=wx.CB_READONLY)
		self.cb2.SetToolTipString = self.cb2.SetToolTip
		self.cb2.SetToolTipString(_("Default version of wxPython."))
		self.default_wxv = self.cb2.GetValue()

		### Sizer
		box1 = wx.StaticBoxSizer(wx.StaticBox(self, wx.NewIdRef(), _('Properties')), orient=wx.VERTICAL)
		vsizer = wx.BoxSizer(wx.VERTICAL)
		hsizer = wx.GridSizer(5, 2, 20, 20)

		hsizer.AddMany( [	(self.st1, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 5),
							(self.nb_opened_file, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 5),
							(self.st3, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 5),
							(self.nb_history_undo, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 5),
							(self.st2, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 5),
							(self.font_size, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 5),
					(self.st4, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 5),
					(self.cb2, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 5)])

		vsizer.Add(self.plugin_dir, 1, wx.EXPAND)
		vsizer.Add(self.domain_dir, 1, wx.EXPAND)
		vsizer.Add(self.out_dir, 1, wx.EXPAND)
		vsizer.Add(hsizer, 0, wx.EXPAND)
		vsizer.Add(self.cb1, 1, wx.EXPAND)
		vsizer.Add(self.cb11, 1, wx.EXPAND)
		box1.Add(vsizer, 1, wx.EXPAND)

		### Set sizer
		self.SetSizer(box1)
		self.SetAutoLayout(True)

	def OnApply(self, event):
		""" Apply change.
		"""

		### safe copy of default_wxv to manage the wx version changing
		default_wxv = copy.copy(self.default_wxv)

		self.OnNbOpenedFileChanged(event)
		self.OnNbHistoryUndoChanged(event)
		self.OnFontSizeChanged(event)
		self.OnDomainPathChanged(event)
		self.OnPluginsDirChanged(event)
		self.OnOutDirChanged(event)
		self.OnTransparancyChanged(event)
		self.OnNotificationChanged(event)
		self.OnwxPythonVersionChanged(event)

		### if the version of wx has been changed in OnwxPythonVersionChanged, we inform the user.
		if self.default_wxv != default_wxv:
			dlg = wx.MessageDialog(self, _("wxPython version has been changed.\nDEVSimPy requires a reboot to load the new version of wxPython."), _('wxPython Version Manager'), wx.OK|wx.ICON_INFORMATION)
			dlg.ShowModal()
			dlg.Destroy()
	###
	def OnNbOpenedFileChanged(self, event):
		""" Update the number opened files.
		"""
		setattr(builtins, 'NB_OPENED_FILE', self.nb_opened_file.GetValue())		# number of recent files

	###
	def OnNbHistoryUndoChanged(self, event):
		""" Update the history for undo.
		"""
		setattr(builtins, 'NB_HISTORY_UNDO', self.nb_history_undo.GetValue())		# number of history undo

	###
	def OnFontSizeChanged(self, event):
		""" Update font size.
		"""
		setattr(builtins, 'FONT_SIZE', self.font_size.GetValue())		# Block font size

	###
	def OnDomainPathChanged(self, event):
		""" Update the domain path.
		"""
		new_domain_dir = self.domain_dir.GetValue()

		### if value has been changed, we clean the library control panel
		if getattr(builtins, 'DOMAIN_PATH') != new_domain_dir:

			old_parent_domain_dir = os.path.dirname(DOMAIN_PATH)

			### remove the parent of Domain directory of this one is not the devsimpy directory
			if old_parent_domain_dir != DEVSIMPY_PACKAGE_PATH:
				if old_parent_domain_dir in sys.path:
					sys.path.remove(old_parent_domain_dir)
			### remove the path from sys.path in order to update the import process
			for path in [p for p in sys.path if DOMAIN_PATH in p]:
				sys.path.remove(path)

			### TODO remove dirname of path from sys.modules ?

			### update the builtin
			setattr(builtins, 'DOMAIN_PATH', new_domain_dir)

			### update all Domain (the process add in sys.path the path invoked when import is used
			mainW = getTopLevelWindow()
			nb1 = mainW.GetControlNotebook()
			tree = nb1.GetTree()
			for item in tree.GetItemChildren(tree.GetRootItem()):
				tree.RemoveItem(item)
			
			### save in the config file
			mainW.SaveUserSettings()

	###
	def OnPluginsDirChanged(self, event):
		""" Update of plugins path has been invoked.
		"""
		setattr(builtins, 'PLUGINS_PATH', self.plugin_dir.GetValue())

	###
	def OnOutDirChanged(self, event):
		""" Update of output directory has been invoked.
		"""
		setattr(builtins, 'OUT_DIR', os.path.basename(self.out_dir.GetValue()))

	###
	def OnTransparancyChanged(self, event):
		""" Update of windwis transparency directory has been invoked.
		"""
		setattr(builtins, 'TRANSPARENCY', self.cb1.GetValue())

		###
	def OnNotificationChanged(self, event):
		""" Update of notifcation option directory has been invoked.
		"""
		setattr(builtins, 'NOTIFICATION', self.cb11.GetValue())

	def OnwxPythonVersionChanged(self, event):
		""" Update of wxpython version has been invoked.
			This option has been deprecated when wxversion has been removed from wx v. 4.x.
		"""

		### new value
		self.default_wxv = self.cb2.GetValue()

		### update the init file into GetUserConfigDir
		parser = configparser.ConfigParser()
		path = os.path.join(GetUserConfigDir(), 'devsimpy.ini')
		parser.read(path)

		section, option = ('wxversion', 'to_load')

		### if ini file exist we remove old section and option
		if os.path.exists(path):
			try:
				parser.remove_option(section, option)
			except:
				pass
			try:
				parser.remove_section(section)
			except:
				pass
			try:
				parser.add_section(section)
			except:
				pass

		if not parser.has_section(section):
			parser.add_section(section)

		parser.set(section, option, self.default_wxv)
		parser.write(open(path,'w'))

class SimulationPanel(wx.Panel):
	""" Simulation Panel.
	"""

	def __init__(self, parent):
		""" Constructor.
		"""
		wx.Panel.__init__(self, parent)

		self.InitUI()
	
	def InitUI(self):
		""" Init the UI.
		"""
		### Sizer
		hbox1 = wx.BoxSizer(wx.HORIZONTAL)
		hbox2 = wx.BoxSizer(wx.HORIZONTAL)
		hbox3 = wx.BoxSizer(wx.HORIZONTAL)
		hbox4 = wx.BoxSizer(wx.HORIZONTAL)
		hbox5 = wx.BoxSizer(wx.HORIZONTAL)
		vbox = wx.BoxSizer(wx.VERTICAL)

		self.sim_success_sound_path = SIMULATION_SUCCESS_SOUND_PATH
		self.sim_error_sound_path = SIMULATION_ERROR_SOUND_PATH

		### Buttons
		self.sim_success_sound_btn = wx.Button(self, wx.NewIdRef(), os.path.basename(self.sim_success_sound_path), (25, 105), name='success')
		self.sim_success_sound_btn.Enable(self.sim_success_sound_path is not os.devnull)
		self.sim_success_sound_btn.SetToolTipString = self.sim_success_sound_btn.SetToolTip
		self.sim_success_sound_btn.SetToolTipString(_("Press this button in order to change the song arriving at the end of the simulation."))

		self.sim_error_sound_btn = wx.Button(self, wx.NewIdRef(), os.path.basename(self.sim_error_sound_path), (25, 105), name='error')
		self.sim_error_sound_btn.Enable(self.sim_error_sound_path is not os.devnull)
		self.sim_error_sound_btn.SetToolTipString = self.sim_error_sound_btn.SetToolTip
		self.sim_error_sound_btn.SetToolTipString(_("Press this button in order to change the song arriving when an error occur in a model during the simulation."))

		self.devs_doc_btn = wx.Button(self, wx.ID_ABOUT, name='doc')
		self.devs_doc_btn.SetToolTipString = self.devs_doc_btn.SetToolTip
		self.devs_doc_btn.SetToolTipString(_("Press this button to read the documentation of the selected DEVS package"))

		### CheckBox
		self.cb1 = wx.CheckBox(self, wx.NewIdRef(), _('Notification'))
		self.cb1.SetToolTipString = self.cb1.SetToolTip
		self.cb1.SetToolTipString(_("Notification song is generate when the simulation is over."))
		self.cb1.SetValue(self.sim_success_sound_path is not os.devnull)

		self.cb2 = wx.CheckBox(self, wx.NewIdRef(), _('No Time Limit'))
		self.cb2.SetToolTipString = self.cb2.SetToolTip
		self.cb2.SetValue(NTL)
		self.cb2.SetToolTipString(_("No Time Limit allow the stop of simulation when all of models are idle."))

		### StaticText for DEVS Kernel directory
		self.txt3 = wx.StaticText(self, wx.NewIdRef(), _("DEVS packages:"))
		self.cb3 = wx.ComboBox(self, wx.NewIdRef(), DEFAULT_DEVS_DIRNAME, choices=list(DEVS_DIR_PATH_DICT.keys()), style=wx.CB_READONLY)
		self.cb3.SetToolTipString = self.cb3.SetToolTip
		self.cb3.SetToolTipString(_("Default DEVS Kernel package (PyDEVS, PyPDEVS, ect.)."))
		self.default_devs_dir = DEFAULT_DEVS_DIRNAME

		### StaticText for strategy
		self.txt = wx.StaticText(self, wx.NewIdRef(), _("Default strategy:"))
		### choice of combo-box depends on the default DEVS package directory
		c = list(PYDEVS_SIM_STRATEGY_DICT.keys()) if DEFAULT_DEVS_DIRNAME == 'PyDEVS' else list(PYPDEVS_SIM_STRATEGY_DICT.keys())

		self.cb4 = wx.ComboBox(self, wx.NewIdRef(), DEFAULT_SIM_STRATEGY, choices=c, style=wx.CB_READONLY)
		self.cb4.SetToolTipString = self.cb4.SetToolTip
		self.cb4.SetToolTipString(_("Default strategy for the simulation algorithm. Please see the DEVSimPy doc for more information of possible strategy."))
		self.sim_defaut_strategy = DEFAULT_SIM_STRATEGY

		### StaticText
		self.sim_defaut_plot_dyn_freq = DEFAULT_PLOT_DYN_FREQ
		self.txt2 = wx.StaticText(self, wx.NewIdRef(), _("Frequency of plotting refresh:"))
		self.sc = wx.SpinCtrl(self, wx.NewIdRef(), str(self.sim_defaut_plot_dyn_freq), (55, 90), (60, -1), min=10, max=10000)
		self.sc.SetToolTipString = self.sc.SetToolTip
		self.sc.SetToolTipString(_("Default frequency for dynamic plotting."))

		### Adding sizer
		hbox1.Add(self.cb1, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 15)
		hbox1.Add(self.sim_success_sound_btn, 1, wx.EXPAND|wx.ALL, 15)
		hbox1.Add(self.sim_error_sound_btn, 1, wx.EXPAND|wx.ALL, 15)

		hbox5.Add(self.txt3, 0, wx.EXPAND|wx.ALL, 15)
		hbox5.Add(self.cb3, 1, wx.EXPAND|wx.ALL, 15)
		hbox5.Add(self.devs_doc_btn, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL)

		hbox2.Add(self.txt, 0, wx.ALL|wx.EXPAND, 15)
		hbox2.Add(self.cb4, 1, wx.ALL|wx.EXPAND, 15)

		hbox3.Add(self.cb2, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 15)

		hbox4.Add(self.txt2, 0, wx.ALL, 15)
		hbox4.Add(self.sc, 1, wx.ALL, 15)

		#hbox4.Add(information, 1, wx.ALIGN_CENTER_VERTICAL, 15)
		##hbox4.Add(self.strategy_info, 1, wx.ALIGN_CENTER_VERTICAL, 15)

		vbox.Add(hbox1, 0, wx.EXPAND|wx.ALL, 10)
		vbox.Add(hbox5, 0, wx.EXPAND|wx.ALL, 10)
		vbox.Add(hbox2, 0, wx.EXPAND|wx.ALL, 10)
		vbox.Add(hbox3, 0, wx.EXPAND|wx.ALL, 10)
		vbox.Add(hbox4, 0, wx.EXPAND|wx.ALL, 10)

		### Set sizer
		self.SetSizer(vbox)
		self.SetAutoLayout(True)

		### Binding
		self.sim_success_sound_btn.Bind(wx.EVT_BUTTON, self.OnSelectSound)
		self.sim_error_sound_btn.Bind(wx.EVT_BUTTON, self.OnSelectSound)
		self.devs_doc_btn.Bind(wx.EVT_BUTTON, self.OnAbout)
		self.cb1.Bind(wx.EVT_CHECKBOX, self.onCb1Check)
		self.cb4.Bind(wx.EVT_COMBOBOX, self.onCb4)
		self.cb3.Bind(wx.EVT_COMBOBOX, self.onCb3)
		self.sc.Bind(wx.EVT_SPINCTRL, self.onSc)

	def OnAbout(self, evt):
		""" Search doc directory into 'doc' directory of DEVS package
		"""
		### DEVS package
		choice = self.cb3.GetValue()

		### possible path of doc directory
		path = os.path.join(os.path.dirname(getattr(builtins,'DEVS_DIR_PATH_DICT').get(choice)), 'doc', 'index.html')

		### Html frame
		frame = HtmlFrame(self, wx.NewIdRef(), "Doc", (600,600))
		### if page exist in <package_dir>/<doc>
		if os.path.exists(path):
			frame.LoadFile(path)
		else:
			frame.SetPage(_("<p> %s documentation directory not found! <p>")%choice)

		### Show frame
		frame.Show()

	def OnSelectSound(self, evt):
		"""
		"""
		dlg = wx.FileDialog(wx.GetTopLevelParent(self),
							_("Choose a sound file"),
							defaultDir = os.path.join(DEVSIMPY_PACKAGE_PATH,'sounds'),
							wildcard = _("MP3 files (*.mp3)|*.mp3| WAV files (*.wav)|*.wav"),
							style = wx.OPEN)

		if dlg.ShowModal() == wx.ID_OK:
			val = dlg.GetPath()
			name = evt.GetEventObject().GetName()
			try:

				playSound(val)

				if name == 'success':
					self.sim_success_sound_path = val
				elif name == 'error':
					self.sim_error_sound_path = val
				else:
					pass

			except NotImplementedError as v:
				wx.MessageBox(str(v), _("Exception Message"))

		dlg.Destroy()

	def onCb1Check(self, evt):
		""" CheckBox has been checked.
		"""

		if evt.GetEventObject().GetValue():
			self.sim_success_sound_btn.Enable(True)
			self.sim_error_sound_btn.Enable(True)
			self.sim_success_sound_path = SIMULATION_SUCCESS_SOUND_PATH
			self.sim_error_sound_path = SIMULATION_ERROR_SOUND_PATH
		else:
			self.sim_success_sound_btn.Enable(False)
			self.sim_error_sound_btn.Enable(False)
			self.sim_success_sound_path = os.devnull
			self.sim_error_sound_path = os.devnull

	def onCb4(self, evt):
		""" ComboBox has been checked.
		"""
		val = evt.GetEventObject().GetValue()
		self.sim_defaut_strategy = val

	def onCb3(self, evt):
		""" ComboBox has been checked.
		"""
		val = evt.GetEventObject().GetValue()

		### update cb below cb3
		self.cb4.Clear()
		if val == 'PyDEVS':
			for k in PYDEVS_SIM_STRATEGY_DICT:
				self.cb4.Append(k)
			self.cb4.SetValue('bag-based')
		else:
			### PyPDEVS
			for k in PYPDEVS_SIM_STRATEGY_DICT:
				self.cb4.Append(k)
			self.cb4.SetValue('classic')

		### update default value for devs dir et sim strategy
		self.default_devs_dir = val
		self.sim_defaut_strategy = self.cb4.GetValue()

	def onSc(self, evt):
		""" CheckBox has been checked.
		"""
		val = evt.GetEventObject().GetValue()
		self.sim_defaut_plot_dyn_freq = val

	def OnApply(self, evt):
		""" Apply changes.
		"""

		### Reload DomainBehavior and DomainStructure
		if DEFAULT_DEVS_DIRNAME != self.default_devs_dir:
			### change builtin before recompile the modules
			setattr(builtins, 'DEFAULT_DEVS_DIRNAME', self.default_devs_dir)

			### recompile the modules.
			### recompile DomainInterface.DomainBehavior , DomainInterfaceStructure and MasterModel
			### recompile all librairies that depend on DomainBehavior (all loaded lib)
			
			ReloadModule.recompile("DomainInterface.DomainBehavior")
			ReloadModule.recompile("DomainInterface.DomainStructure")
			ReloadModule.recompile("DomainInterface.MasterModel")

			mainW = getTopLevelWindow()
			nb1 = mainW.GetControlNotebook()
			tree = nb1.GetTree()
			tree.UpdateAll()

		### enable the priority (DEVS select function) icon depending on the selected DEVS kernel
		mainW = getTopLevelWindow()
		tb = mainW.GetToolBar()
		tb.EnableTool(Menu.ID_PRIORITY_DIAGRAM, not 'PyPDEVS' in DEFAULT_DEVS_DIRNAME)

		setattr(builtins, 'SIMULATION_SUCCESS_SOUND_PATH', self.sim_success_sound_path)
		setattr(builtins, 'SIMULATION_ERROR_SOUND_PATH', self.sim_error_sound_path)
		setattr(builtins, 'DEFAULT_SIM_STRATEGY', self.sim_defaut_strategy)
		setattr(builtins, 'DEFAULT_PLOT_DYN_FREQ', self.sim_defaut_plot_dyn_freq)
		setattr(builtins, 'NTL', self.cb2.GetValue())

class EditorPanel(wx.Panel):
	""" Edition Panel.
	"""

	EDITORS = ('spyder', 'pyzo')

	def __init__(self, parent):
		""" Constructor.
		"""

		wx.Panel.__init__(self, parent)

		self.parent = parent

		self.InitUI()
	
	def InitUI(self):
		""" Init the UI.
		"""

		vbox = wx.BoxSizer(wx.VERTICAL)

		self.cb = wx.CheckBox(self, wx.NewIdRef(), _("Use the DEVSimPy local code editor software"))
		self.cb.SetValue(LOCAL_EDITOR)
		self.cb.SetToolTipString = self.cb.SetToolTip
		self.cb.SetToolTipString(_("This option is available only for the python file. \n"
			"Modification of python file during the simulation is disabled when this checkbox is checked."))

		### populate the choices array depending on the code editor installed
		### if the code editor is not installed, we propose to install it
		choices = []

		for editor in EditorPanel.EDITORS:
			try:
				importlib.import_module(editor)
			except:
				pass
			else:
				choices.append(editor)

		### add the choice object to select one external code editor
		hbox = wx.BoxSizer(wx.HORIZONTAL)
		txt = wx.StaticText(self, -1, _("Select an external code editor:"))
		self.choice = wx.Choice(self, -1, choices=choices)
		
		self.UpdateExternalEditorBtn = wx.Button(self, wx.ID_REFRESH, size=(140, -1))
		self.UpdateExternalEditorBtn.SetToolTipString = self.UpdateExternalEditorBtn.SetToolTip			
		self.UpdateExternalEditorBtn.SetToolTipString(_("Update the list of available external editors"))

		### if external editor name is never stored in config file (.devsimpy)
		if EXTERNAL_EDITOR_NAME == "":
			self.choice.SetSelection(0)
		else:
			self.choice.SetSelection(EditorPanel.EDITORS.index(EXTERNAL_EDITOR_NAME))

		self.choice.Enable(not self.cb.IsChecked())

		### horizontal box
		hbox.Add(txt, 0, wx.ALL, 10)
		hbox.Add(self.choice, 0, wx.ALL, 10)
		hbox.Add(self.UpdateExternalEditorBtn, 0, wx.ALL, 10)

		### vertical box
		vbox.Add(self.cb, 0, wx.ALL, 10)
		vbox.Add(hbox, 0, wx.ALL, 10)

		### bind the checkbox in order to enable the choice object
		self.Bind(wx.EVT_CHECKBOX, self.OnCheck, self.cb)
		self.Bind(wx.EVT_BUTTON, self.OnUpdateExternalEditors, id=self.UpdateExternalEditorBtn.GetId())
	
		self.SetSizer(vbox)

	def OnUpdateExternalEditors(self, event):
		""" Update Button has been clicked in order to update the list of available external editors.
		"""

		installed = False
		for editor in EditorPanel.EDITORS:
			if self.choice.FindString(editor) == wx.NOT_FOUND and BuzyCursorNotification(install(editor)):
				installed = True
				items = self.choice.GetItems()+[editor]
				self.choice.SetItems(items)
				
		if installed:
			msg = _('You need to restart DEVSimPy to use the new installed code editor.')
		else:
			msg = _('All external editors are installed.')

		dial = wx.MessageDialog(self.parent, msg, _("External Code Editor Installation"), wx.OK | wx.ICON_INFORMATION)
		dial.ShowModal()

		event.Skip()

	def OnCheck(self, event):
		"""
		"""
		self.choice.Enable(not self.cb.IsChecked())
		
	def OnApply(self, evt):
		""" Apply changes.
		"""
		setattr(builtins, 'LOCAL_EDITOR', self.cb.IsChecked())
		setattr(builtins,'EXTERNAL_EDITOR_NAME',self.choice.GetString(self.choice.GetCurrentSelection()) if self.choice.IsEnabled() else "")

class AIPanel(wx.Panel):
	""" AI Panel"""

	AI_SET = ("", "ChatGPT", "Ollama")

	def __init__(self, parent):
		wx.Panel.__init__(self, parent)

		# Charger les paramètres sauvegardés au démarrage
		self.load_settings()

		self.InitUI()

	def InitUI(self):
		""" Init interface"""

		### --------------------------------------------------------------------------------------------------
		# Checkbox for enabling/disabling AI
		self.st_ia = wx.StaticText(self, label=_("Select an AI:"))
		self.choice_ia = wx.ComboBox(
										self, wx.NewIdRef(), 
										value=builtins.__dict__.get('SELECTED_IA', ''),
										choices=AIPanel.AI_SET, 
										style=wx.CB_READONLY
		)

		### ai parameters lauout
		hbox_select_ai = wx.BoxSizer(wx.HORIZONTAL)
		hbox_select_ai.Add(self.st_ia, 0, wx.RIGHT|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 10)
		hbox_select_ai.Add(self.choice_ia, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)

		### selected ai
		self.selected_ia = self.choice_ia.GetValue()

		### --------------------------------------------------------------------------------------------------
		### ChatGPT API Key setting
		st_api_key = wx.StaticText(self, label=_("API Key:"))
		self.api_key_ctrl = wx.TextCtrl(self, style=wx.TE_PASSWORD)
		self.api_key_ctrl.SetValue(getattr(builtins,'PARAMS_IA', {}).get('CHATGPT_API_KEY', ''))
		
		### GPT parameters lauout
		hbox_chatgpt = wx.BoxSizer(wx.HORIZONTAL)
		hbox_chatgpt.Add(st_api_key, 0, wx.RIGHT|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 10)
		hbox_chatgpt.Add(self.api_key_ctrl, 1, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)

		### Ollama server port setting
		st_port = wx.StaticText(self, label=_("Server port:"))
		self.port_ctrl = wx.TextCtrl(self)
		self.port_ctrl.SetValue(getattr(builtins,'PARAMS_IA', {}).get('OLLAMA_PORT', '11434'))

		### ollama parameters layout
		hbox_ollama = wx.BoxSizer(wx.HORIZONTAL)
		hbox_ollama.Add(st_port, 0, wx.RIGHT|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 10)
		hbox_ollama.Add(self.port_ctrl, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)

		### all of the ai box - Add here the ai bow you want to show
		self.ai_boxes = {'ChatGPT': hbox_chatgpt, 'Ollama': hbox_ollama}

		# ------------------------------------------------------------------------------------------------------
		
		### Check AI button
		self.ai_check_button = wx.Button(self, label=_("Check"))
		self.ai_check_button.Show(bool(self.selected_ia))

		### info AI button
		self.ai_info_button = wx.Button(self, label=_("Info"))
		icon = wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_BUTTON, (16, 16))  # Taille 16x16 pixels
		self.ai_info_button.SetBitmap(icon)
		self.ai_info_button.Show(bool(self.selected_ia))

		### buttons layout
		hbox_buttons = wx.BoxSizer(wx.HORIZONTAL)
		hbox_buttons.Add(self.ai_info_button, flag=wx.RIGHT | wx.ALIGN_LEFT, border=10)
		hbox_buttons.Add(self.ai_check_button, flag=wx.ALL | wx.ALIGN_LEFT)

		### SetToolTipString
		self.choice_ia.SetToolTipString = self.choice_ia.SetToolTip
		self.ai_info_button.SetToolTipString = self.ai_info_button.SetToolTip
		self.ai_check_button.SetToolTipString = self.ai_check_button.SetToolTip

		self.choice_ia.SetToolTipString(_("Select an AI for model code generation"))
		self.ai_info_button.SetToolTipString(_("More about the selected Gen AI"))
		self.ai_check_button.SetToolTipString(_("Check if the selected AI Gen is ready to work"))

		# ---------------------------------------------------------------------------------------------------------------------
		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.Add(hbox_select_ai, 0, wx.ALL, 10)
		vbox.Add(self.ai_boxes['ChatGPT'], 0, wx.ALL|wx.EXPAND, 10)
		vbox.Add(self.ai_boxes['Ollama'], 0, wx.ALL, 10)
		vbox.Add(hbox_buttons, flag=wx.ALL | wx.EXPAND, border=5)

		self.SetSizer(vbox)

		### Bind
		self.choice_ia.Bind(wx.EVT_COMBOBOX, self.OnAISelection)
		self.ai_info_button.Bind(wx.EVT_BUTTON, self.OnInfoButtonClick)	
		self.ai_check_button.Bind(wx.EVT_BUTTON, self.OnAICheck)
	
		# ---------------------------------------------------------------------------------------------------------------------
		self.UpdateFieldsVisibility()

	def UpdateFieldsVisibility(self):
		""" UI refresh depending on the selected AI (More Generic)"""
		selected_ia = self.choice_ia.GetValue()
		
		### Display the correct ai hbox depending on the selected ai name
		for ai_name,ai_hbox in self.ai_boxes.items():
			for item in ai_hbox.GetChildren():
				item.GetWindow().Show(selected_ia == ai_name)

		### update layout
		self.Layout()

	def OnAICheck(self, event):
		""" Check the selected AI

		Args:
			event (_type_): _description_
		"""

		self.SaveAISettings()

		# Créer ou récupérer l'instance de ChatGPTDevsAdapter via la factory
		if AdapterFactory.get_adapter_instance(None, params=PARAMS_IA):
			wx.MessageBox(_(f"{self.selected_ia} Code Generator is ready."), _("Success"), wx.OK | wx.ICON_INFORMATION)

	def OnInfoButtonClick(self, event):
		"""_summary_

		Args:
			event (_type_): _description_
		"""
		selected_ai = self.choice_ia.GetValue()
		
		if selected_ai == "ChatGPT":
			url = 'https://openai.com/research/chatgpt'
		elif selected_ai == "Ollama":
			url = 'https://ollama.com/'
		else:
			return 
		
        ### open default browser
		wx.LaunchDefaultBrowser(url)

	def OnAISelection(self, event):
		""" Select the AI """
		self.selected_ia = self.choice_ia.GetValue()
		
		setattr(builtins, 'SELECTED_IA', self.selected_ia)
		self.ai_check_button.Show(bool(self.selected_ia))
		self.ai_info_button.Show(bool(self.selected_ia))
		
		self.UpdateFieldsVisibility()  # Appeler UpdateFieldsVisibility pour actualiser les sous-champs

	def load_settings(self):
		""" Load the AI settings from builtins """
		### Init the builtins wirh AI info
		setattr(builtins, "SELECTED_IA", getattr(builtins, "SELECTED_IA", ""))
		setattr(builtins, "PARAMS_IA", getattr(builtins, "PARAMS_IA", {}))
		builtins.PARAMS_IA.setdefault('CHATGPT_API_KEY', '')
		builtins.PARAMS_IA.setdefault('OLLAMA_PORT', '11434')

	def OnApply(self, evt):
		""" Apply and save the current AI settings """
		### save AI settings
		self.SaveAISettings()

	def SaveAISettings(self):
		""" Save AI setting in builtins """
	
		### update selected AI
		selected_ai = self.choice_ia.GetValue()
		if getattr(builtins, "SELECTED_IA", "") != selected_ai:
			setattr(builtins, "SELECTED_IA",selected_ai)

		# update settings for all accessible Gen AI
		if selected_ai == "ChatGPT":
			new_chatgpt_api_key = self.api_key_ctrl.GetValue()
			if getattr(builtins, 'PARAMS_IA').get('CHATGPT_API_KEY') != new_chatgpt_api_key:
				builtins.__dict__['PARAMS_IA']['CHATGPT_API_KEY'] = new_chatgpt_api_key
		elif selected_ai == "Ollama":
			new_ollama_port = self.port_ctrl.GetValue()
			if getattr(builtins, 'PARAMS_IA').get('OLLAMA_PORT') != new_ollama_port:
				builtins.__dict__['PARAMS_IA']['OLLAMA_PORT'] = new_ollama_port

########################################################################
class Preferences(wx.Toolbook):
	""" Based Toolbook Preference class
	"""

	def __init__(self, parent):
		"""Constructor.
		"""

		wx.Toolbook.__init__(self, parent, wx.NewIdRef(), style=wx.BK_DEFAULT)

		self.InitUI()
	
	def InitUI(self):
		""" Init the UI.
		"""

		### don't try to translate this labels with _() because there are used to find png
		L = [('General',"(self)"),('Simulation',"(self)"), ('Editor',"(self)"), ('AI',"(self)"), ('Plugins',"(self)")]

		# make an image list using the LBXX images
		il = wx.ImageList(25, 25)
		for img in [load_and_resize_image("%s_pref.png"%a[0], 25, 25) for a in L]:
			il.Add(img)
		self.AssignImageList(il)

		imageIdGenerator = iter(range(il.GetImageCount()))

		for p, label in [("%sPanel%s"%(s,str(args)), _(s)) for s,args in L]:
			page = eval(p)
			self.AddPage(page, label, imageId=next(imageIdGenerator))

		### Plug-in page setting (populate is done when page is changed)
		self.pluginPanel = self.GetPage(self.GetPageCount()-1)

		self.CheckList = GeneralPluginsList(self.pluginPanel.GetRightPanel(), style= wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SORT_ASCENDING)
		self.pluginPanel.SetPluginsList(self.CheckList)

		lpanel = self.pluginPanel.GetLeftPanel()

		### Buttons for insert or delete plug-ins
		self.addBtn = wx.Button(lpanel, wx.ID_ADD, size=(140, -1))
		self.delBtn = wx.Button(lpanel, wx.ID_DELETE, size=(140, -1))
		self.refBtn = wx.Button(lpanel, wx.ID_REFRESH, size=(140, -1))
	
		self.addBtn.SetToolTipString = self.addBtn.SetToolTip
		self.delBtn.SetToolTipString = self.delBtn.SetToolTip
		self.refBtn.SetToolTipString = self.refBtn.SetToolTip

		self.addBtn.SetToolTipString(_("Add new plug-ins"))
		self.delBtn.SetToolTipString(_("Delete all existing plug-ins"))
		self.refBtn.SetToolTipString(_("Refresh plug-ins list"))

		### add widget to plug-in panel
		self.pluginPanel.AddWidget(3, self.addBtn)
		self.pluginPanel.AddWidget(4, self.delBtn)
		self.pluginPanel.AddWidget(5, self.refBtn)

		### Binding
		self.Bind(wx.EVT_TOOLBOOK_PAGE_CHANGED, self.OnPageChanged)
		self.Bind(wx.EVT_TOOLBOOK_PAGE_CHANGING, self.OnPageChanging)
		self.Bind(wx.EVT_BUTTON, self.OnAdd, id=self.addBtn.GetId())
		self.Bind(wx.EVT_BUTTON, self.OnDelete, id=self.delBtn.GetId())
		self.Bind(wx.EVT_BUTTON, self.OnRefresh, id=self.refBtn.GetId())

	def OnPageChanged(self, event):
		""" Page has been changed.
		"""
#		old = event.GetOldSelection()
		new = event.GetSelection()
#		sel = self.GetSelection()
		parent = self.GetTopLevelParent()
		### plug-ins page
		if new == 3:
			parent.SetSize((700,500))
		else:
			parent.SetSize((700,450))

		event.Skip()

	def OnPageChanging(self, event):
		""" Pas is changing.
		"""
		new = event.GetSelection()
		### plug-in page
		if new == 3:
			### list of plug-ins file in plug-in directory
			l = list(os.walk(PLUGINS_PATH))
			### populate checklist with file in plug-ins directory
			wx.CallAfter(self.CheckList.Populate, (l))
		event.Skip()

	def OnAdd(self, event):
		""" Add plug-in.
		"""
		wcd = 'All files (*)|*|Editor files (*.py)|*.py'
		open_dlg = wx.FileDialog(self, message=_('Choose a file'), defaultDir=DEVSIMPY_PACKAGE_PATH, defaultFile='', wildcard=wcd, style=wx.OPEN|wx.CHANGE_DIR)
		if open_dlg.ShowModal() == wx.ID_OK:
			filename = open_dlg.GetPath()
			### sure is python file
			if filename.endswith(('.py','pyc')):
				### Insert item in list
				basename,ext = os.path.splitext(os.path.basename(filename))
				root = os.path.dirname(filename)
				self.CheckList.Importing(root, basename)
				
				### trying to copy file in plug-in directory in order to find it again when the plugins list is populate (depending on the __init__.py file)
				try:
					shutil.copy2(filename, PLUGINS_PATH)
				except Exception as info:
					sys.stderr.write(_('ERROR: %s copy failed!\n%s')%(os.path.basename(filename), str(info)))
				else:
					### rewrite the new __init__.py file that contain the new imported plugin (basename) in order to populate the future generale plugins list
					AddToInitFile(PLUGINS_PATH, [basename])

			else:
				sys.stderr.write(_('ERROR: %s is not a python file.\nOnly python file can be added as plugin.')%(os.path.basename(filename)))

		open_dlg.Destroy()

	def OnDelete(self, event):
		""" Delete plugins item and python source file.
		"""

		for i in range(self.CheckList.GetItemCount()):
			if self.CheckList.IsSelected(i):
				### Delete query
				dial = wx.MessageDialog(self, _('Do you want to delete the selected %s plugins?'%self.CheckList.GetItemText(i)), _('Plugin MAnager'), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
				if dial.ShowModal() == wx.ID_YES:
					### for selected plug-ins
				
					module = self.CheckList.GetPyData(i)[0]
					basename,ext = os.path.splitext(os.path.basename(module.__file__))

					### delete item
					self.CheckList.DeleteItem(i)

					### TODO: remove also into __init__.py
					### delete the selected plugin from__init__.py
					DelToInitFile(PLUGINS_PATH, [basename])

					try:
						#name, ext = os.path.splitext(module.__file__)
						dlg = wx.MessageDialog(self, _('Do you want to remove the corresponding file %s?')%basename, _('Preference Manager'), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
						if dlg.ShowModal() == wx.ID_YES:
							os.remove(module.__file__)			
					except Exception:
						sys.stderr.write(_('ERROR: plugin file not deleted!'))
					else:
						dlg.Destroy()	
				else:
					sys.stderr.write(_('Select plugins to delete'))

				dial.Destroy()

	def OnRefresh(self, event):
		""" Refresh list of plugins.
		"""
		self.CheckList.Clear()
		l = list(os.walk(PLUGINS_PATH))
		### populate checklist with file in plug-ins directory
		wx.CallAfter(self.CheckList.Populate, (l))

	def OnApply(self,evt):
		""" Apply button has been pressed and we must take into account all changes for each panel
		"""
		for page in [self.GetPage(i) for i in range(self.GetPageCount())]:
			page.OnApply(evt)

########################################################################
class PreferencesGUI(wx.Frame):
	""" DEVSimPy Preferences General User Interface class
	"""

	def __init__(self, parent, title):
		"""
			Constructor.
		"""
		wx.Frame.__init__(self, parent, wx.NewIdRef(), title, style = wx.DEFAULT_FRAME_STYLE | wx.CLIP_CHILDREN)

		self.InitUI()

		self.Layout()
		self.Center()

	def InitUI(self):
		""" Init the UI.
		"""
		_icon = wx.Icon()
		_icon.CopyFromBitmap(load_and_resize_image("preferences.png"))
		self.SetIcon(_icon)

		self.SetMinSize((400,500))

		### Panel
		panel = wx.Panel(self, wx.NewIdRef())
		self.pref = Preferences(panel)

		### Buttons
		self.cancel = wx.Button(panel, wx.ID_CANCEL)
		self.apply = wx.Button(panel, wx.ID_OK)

		self.apply.SetToolTipString = self.apply.SetToolTip
		self.cancel.SetToolTipString = self.cancel.SetToolTip

		self.apply.SetToolTipString(_("Apply all changing"))
		self.cancel.SetToolTipString(_("Cancel without changing"))
		self.apply.SetDefault()

		### Sizers
		vsizer = wx.BoxSizer(wx.VERTICAL)
		hsizer = wx.BoxSizer(wx.HORIZONTAL)

		hsizer.Add(self.cancel, 0)
		hsizer.Add(self.apply, 0, wx.EXPAND|wx.LEFT, 5)
		vsizer.Add(self.pref, 1, wx.ALL|wx.EXPAND, 5)
		vsizer.Add(hsizer, 0, wx.ALL|wx.ALIGN_RIGHT, 5)

		panel.SetSizer(vsizer)
		vsizer.Fit(panel)

		### Binding
		self.Bind(wx.EVT_BUTTON, self.OnApply, id=wx.ID_OK)
		self.Bind(wx.EVT_BUTTON, self.OnCancel, id=wx.ID_CANCEL)
		self.Bind(wx.EVT_BUTTON, self.OnClose, id=wx.ID_CLOSE)

	def OnApply(self, evt):
		""" Apply button has been clicked.
		"""
		self.pref.OnApply(evt)
		self.Close()

	def OnCancel(self, evt):
		""" Cancel button has been invoked.
		"""
		self.Close()
		evt.Skip()

	def OnClose(self, evt):
		""" Close button has been invoked.
		"""
		self.Close()
		evt.Skip()
