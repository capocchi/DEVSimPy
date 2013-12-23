# -*- coding: utf-8 -*-

import wx
import os
import __builtin__
import __main__
import shutil
import sys

import wx.lib.filebrowsebutton as filebrowse

if __name__ == '__main__':
	__builtin__.__dict__['HOME_PATH'] = os.getcwd()
	__builtin__.__dict__['DEFAULT_DEVS_DIRNAME'] = 'PyDEVS'
	__builtin__.__dict__['DEVS_DIR_PATH_DICT'] = {'PyDEVS':os.path.join(HOME_PATH,'DEVSKernel','PyDEVS'),
									'PyPDEVS_221':os.path.join(HOME_PATH,'DEVSKernel','PyPDEVS','pypdevs221' ,'src'),
									'PyPDEVS':os.path.join(HOME_PATH,'DEVSKernel','PyPDEVS','old')}

from HtmlWindow import HtmlFrame

from PluginsGUI import PluginsPanel, GeneralPluginsList
from Utilities import playSound

import ReloadModule

#----------------------------------------------------------------------
class GeneralPanel(wx.Panel):
	""" General preferences panel
	"""

	def __init__(self, parent):
		"""
			Constructor.
		"""
		wx.Panel.__init__(self, parent)

		### FileBrowse
		self.plugin_dir = filebrowse.DirBrowseButton(self, wx.ID_ANY, labelText=_("Plug-ins directory:"), toolTip=_("Change the plug-ins directory"))
		self.domain_dir = filebrowse.DirBrowseButton(self, wx.ID_ANY, labelText=_("Library directory:"), toolTip=_("Change the library directory"))
		self.out_dir = filebrowse.DirBrowseButton(self, wx.ID_ANY, labelText=_("Output directory:"), toolTip=_("Change the output directory"))

		self.plugin_dir.SetValue(PLUGINS_PATH)
		self.domain_dir.SetValue(DOMAIN_PATH)
		self.out_dir.SetValue(OUT_DIR)

		### StaticText
		self.st1 = wx.StaticText(self, wx.ID_ANY, _("Number of recent file:"))
		self.st2 = wx.StaticText(self, wx.ID_ANY, _("Font size:"))
		self.st3 = wx.StaticText(self, wx.ID_ANY, _("Deep of history item:"))

		self.st1.SetToolTipString(_("Feel free to change the length of list defining the recent opened files."))
		self.st2.SetToolTipString(_("Feel free to change the font size of DEVSimpy."))
		self.st3.SetToolTipString(_("Feel free to change the number of item for undo/redo command"))

		### number of opened file
		self.nb_opened_file = wx.SpinCtrl(self, wx.ID_ANY, '')
		self.nb_opened_file.SetRange(2, 20)
		self.nb_opened_file.SetValue(NB_OPENED_FILE)

		### Block font size
		self.font_size = wx.SpinCtrl(self, wx.ID_ANY, '')
		self.font_size.SetRange(2, 20)
		self.font_size.SetValue(FONT_SIZE)

		### number of undo/redo items
		self.nb_history_undo = wx.SpinCtrl(self, wx.ID_ANY, '')
		self.nb_history_undo.SetRange(2, 100)
		self.nb_history_undo.SetValue(NB_HISTORY_UNDO)

		### CheckBox
		self.cb1 = wx.CheckBox(self, wx.ID_ANY, _('Transparency'))
		self.cb1.SetToolTipString(_("Transparency for the detached frame of diagrams"))
		self.cb1.SetValue(__builtin__.__dict__['TRANSPARENCY'])

		### Sizer
		box1 = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, _('Properties')), orient=wx.VERTICAL)
		vsizer = wx.BoxSizer(wx.VERTICAL)
		hsizer = wx.GridSizer(3, 2, 20, 20)

		hsizer.AddMany( [	(self.st1, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 5),
							(self.nb_opened_file, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 5),
							(self.st3, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 5),
							(self.nb_history_undo, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 5),
							(self.st2, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 5),
							(self.font_size, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 5)])

		vsizer.Add(self.plugin_dir, 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		vsizer.Add(self.domain_dir, 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		vsizer.Add(self.out_dir, 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		vsizer.Add(hsizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		vsizer.Add(self.cb1, 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		box1.Add(vsizer, 1, wx.EXPAND)

		### Set sizer
		self.SetSizer(box1)
		self.SetAutoLayout(True)

	def OnApply(self, event):
		""" Apply change
		"""
		self.OnNbOpenedFileChanged(event)
		self.OnNbHistoryUndoChanged(event)
		self.OnFontSizeChanged(event)
		self.OnDomainPathChanged(event)
		self.OnPluginsDirChanged(event)
		self.OnOutDirChanged(event)
		self.OnTransparancyChanged(event)

	###
	def OnNbOpenedFileChanged(self, event):
		__builtin__.__dict__['NB_OPENED_FILE'] = self.nb_opened_file.GetValue()		# number of recent files

	###
	def OnNbHistoryUndoChanged(self, event):
		__builtin__.__dict__['NB_HISTORY_UNDO'] = self.nb_history_undo.GetValue()		# number of history undo

	###
	def OnFontSizeChanged(self, event):
		__builtin__.__dict__['FONT_SIZE'] = self.font_size.GetValue()		# Block font size

	###
	def OnDomainPathChanged(self, event):
		"""
		"""
		v = self.domain_dir.GetValue()

		### if value has been changed, we clean the library control panel
		if __builtin__.__dict__['DOMAIN_PATH'] != v:
			__builtin__.__dict__['DOMAIN_PATH'] = v

			mainW = wx.GetApp().GetTopWindow()
			nb1 = mainW.GetControlNotebook()
			tree = nb1.GetTree()

			### update all Domain
			for item in tree.GetItemChildren(tree.GetRootItem()):
				tree.RemoveItem(item)

	###
	def OnPluginsDirChanged(self, event):
		__builtin__.__dict__['PLUGINS_PATH'] = self.plugin_dir.GetValue()

	###
	def OnOutDirChanged(self, event):
		__builtin__.__dict__['OUT_DIR'] = os.path.basename(self.out_dir.GetValue())

	###
	def OnTransparancyChanged(self, event):
		__builtin__.__dict__['TRANSPARENCY'] = self.cb1.GetValue()

class SimulationPanel(wx.Panel):
	""" Simulation Panel
	"""

	def __init__(self, parent):
		""" Constructor
		"""
		wx.Panel.__init__(self, parent)

		### Sizer
		hbox1 = wx.BoxSizer(wx.HORIZONTAL)
		hbox2 = wx.BoxSizer(wx.HORIZONTAL)
		hbox3 = wx.BoxSizer(wx.HORIZONTAL)
		hbox4 = wx.BoxSizer(wx.HORIZONTAL)
		hbox5 = wx.BoxSizer(wx.HORIZONTAL)
		vbox = wx.BoxSizer(wx.VERTICAL)

		self.sim_success_sound_path = __builtin__.__dict__['SIMULATION_SUCCESS_SOUND_PATH']
		self.sim_error_sound_path = __builtin__.__dict__['SIMULATION_ERROR_SOUND_PATH']

		### Buttons
		self.sim_success_sound_btn = wx.Button(self, wx.ID_ANY, os.path.basename(self.sim_success_sound_path), (25, 105), name='success')
		self.sim_success_sound_btn.Enable(self.sim_success_sound_path is not os.devnull)
		self.sim_success_sound_btn.SetToolTipString(_("Press this button in order to change the song arriving at the end of the simulation."))

		self.sim_error_sound_btn = wx.Button(self, wx.ID_ANY, os.path.basename(self.sim_error_sound_path), (25, 105), name='error')
		self.sim_error_sound_btn.Enable(self.sim_error_sound_path is not os.devnull)
		self.sim_error_sound_btn.SetToolTipString(_("Press this button in order to change the song arriving when an error occur in a model during the simulation."))

		self.devs_doc_btn = wx.Button(self, wx.ID_ABOUT, name='doc')
		self.devs_doc_btn.SetToolTipString(_("Press this button to read the documentation of the selected DEVS package"))

		### CheckBox
		self.cb1 = wx.CheckBox(self, wx.ID_ANY, _('Notification'))
		self.cb1.SetToolTipString(_("Notification song is generate when the simulation is over."))
		self.cb1.SetValue(self.sim_success_sound_path is not os.devnull)

		self.cb2 = wx.CheckBox(self, wx.ID_ANY, _('No Time Limit'))
		self.cb2.SetValue(__builtin__.__dict__['NTL'])
		self.cb2.SetToolTipString(_("No Time Limit allow the stop of simulation when all of models are idle."))

		### StaticText for DEVS Kernel directory
		self.txt3 = wx.StaticText(self, wx.ID_ANY, _("DEVS package:"))
		self.cb3 = wx.ComboBox(self, wx.ID_ANY, DEFAULT_DEVS_DIRNAME, choices=DEVS_DIR_PATH_DICT.keys(), style=wx.CB_READONLY)
		self.cb3.SetToolTipString(_("Default DEVS Kernel package (PyDEVS, PyPDEVS, ect.)."))
		self.default_devs_dir = DEFAULT_DEVS_DIRNAME

		### StaticText for strategy
		self.txt = wx.StaticText(self, wx.ID_ANY, _("Default strategy:"))
		### choice of combo-box depends on the default DEVS package directory
		c= PYDEVS_SIM_STRATEGY_DICT.keys() if DEFAULT_DEVS_DIRNAME == 'PyDEVS' else PYPDEVS_SIM_STRATEGY_DICT.keys()

		self.cb4 = wx.ComboBox(self, wx.ID_ANY, DEFAULT_SIM_STRATEGY, choices=c, style=wx.CB_READONLY)
		self.cb4.SetToolTipString(_("Default strategy for the simulation algorithm. Please see the DEVSimPy doc for more information of possible strategy."))
		self.sim_defaut_strategy = DEFAULT_SIM_STRATEGY

		### StaticText
		self.sim_defaut_plot_dyn_freq = __builtin__.__dict__['DEFAULT_PLOT_DYN_FREQ']
		self.txt2 = wx.StaticText(self, wx.ID_ANY, _("Frequency of plotting refresh:"))
		self.sc = wx.SpinCtrl(self, wx.ID_ANY, str(self.sim_defaut_plot_dyn_freq), (55, 90), (60, -1), min=10, max=10000)
		self.sc.SetToolTipString(_("Default frequency for dynamic plotting."))

		### Adding sizer
		hbox1.Add(self.cb1, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 15)
		hbox1.Add(self.sim_success_sound_btn, 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND|wx.ALL, 15)
		hbox1.Add(self.sim_error_sound_btn, 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND|wx.ALL, 15)

		hbox5.Add(self.txt3, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND|wx.ALL, 15)
		hbox5.Add(self.cb3, 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND|wx.ALL, 15)
		hbox5.Add(self.devs_doc_btn, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL)


		hbox2.Add(self.txt, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL|wx.EXPAND, 15)
		hbox2.Add(self.cb4, 1, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALL|wx.EXPAND, 15)

		hbox3.Add(self.cb2, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 15)

		hbox4.Add(self.txt2, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT|wx.ALL, 15)
		hbox4.Add(self.sc, 1, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 15)

		#hbox4.Add(information, 1, wx.ALIGN_CENTER_VERTICAL, 15)
		##hbox4.Add(self.strategy_info, 1, wx.ALIGN_CENTER_VERTICAL, 15)

		vbox.Add(hbox1, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.EXPAND|wx.ALL, 10)
		vbox.Add(hbox5, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.EXPAND|wx.ALL, 10)
		vbox.Add(hbox2, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.EXPAND|wx.ALL, 10)
		vbox.Add(hbox3, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 10)
		vbox.Add(hbox4, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 10)

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
		path = os.path.join(os.path.dirname(__builtin__.__dict__['DEVS_DIR_PATH_DICT'][choice]), 'doc', 'index.html')

		### Html frame
		frame = HtmlFrame(self, wx.ID_ANY, "Doc", (600,600))
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
							defaultDir = os.path.join(HOME_PATH,'sounds'),
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

			except NotImplementedError, v:
				wx.MessageBox(str(v), _("Exception Message"))

		dlg.Destroy()

	def onCb1Check(self, evt):
		""" CheckBox has been checked
		"""

		if evt.GetEventObject().GetValue():
			self.sim_success_sound_btn.Enable(True)
			self.sim_error_sound_btn.Enable(True)
			self.sim_success_sound_path = __main__.builtin_dict['SIMULATION_SUCCESS_SOUND_PATH']
			self.sim_error_sound_path = __main__.builtin_dict['SIMULATION_ERROR_SOUND_PATH']
		else:
			self.sim_success_sound_btn.Enable(False)
			self.sim_error_sound_btn.Enable(False)
			self.sim_success_sound_path = os.devnull
			self.sim_error_sound_path = os.devnull

	def onCb4(self, evt):
		""" ComboBox has been checked
		"""
		val = evt.GetEventObject().GetValue()
		self.sim_defaut_strategy = val

	def onCb3(self, evt):
		""" ComboBox has been checked
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
			self.cb4.SetValue('original')

		### update default value for devs dir et sim strategy
		self.default_devs_dir = val
		self.sim_defaut_strategy = self.cb4.GetValue()

	def onSc(self, evt):
		""" CheckBox has been checked
		"""
		val = evt.GetEventObject().GetValue()
		self.sim_defaut_plot_dyn_freq = val

	def OnApply(self, evt):
		""" Apply changes
		"""

		### Reload DomainBehavior and DomainStructure
		if __builtin__.__dict__['DEFAULT_DEVS_DIRNAME'] != self.default_devs_dir:
			### change builtin before recompile the modules
			__builtin__.__dict__['DEFAULT_DEVS_DIRNAME'] = self.default_devs_dir
			### recompile the modules.
			ReloadModule.recompile("DomainInterface.DomainBehavior")
			ReloadModule.recompile("DomainInterface.DomainStructure")
			ReloadModule.recompile("DomainInterface.MasterModel")

		__builtin__.__dict__['SIMULATION_SUCCESS_SOUND_PATH'] = self.sim_success_sound_path
		__builtin__.__dict__['SIMULATION_ERROR_SOUND_PATH'] = self.sim_error_sound_path
		__builtin__.__dict__['DEFAULT_SIM_STRATEGY'] = self.sim_defaut_strategy
		__builtin__.__dict__['DEFAULT_PLOT_DYN_FREQ'] = self.sim_defaut_plot_dyn_freq
		__builtin__.__dict__['NTL'] = self.cb2.GetValue()

class EditorPanel(wx.Panel):
	""" Edition Panel
	"""

	def __init__(self, parent):
		""" Constructor
		"""

		wx.Panel.__init__(self, parent)

		vbox = wx.BoxSizer(wx.VERTICAL)

		self.cb = wx.CheckBox(self, wx.ID_ANY, _("Use local programmer software"))
		self.cb.SetValue(__builtin__.__dict__['LOCAL_EDITOR'])
		self.cb.SetToolTipString(_("This option don't work for the .amd and .cmd file. \n"
			"Modification of python file during the simulation is disabled when this checkbox is checked."))

		vbox.Add(self.cb, 0, wx.ALL,10)

		self.SetSizer(vbox)

	def OnApply(self, evt):
		""" Apply changes
		"""
		__builtin__.__dict__['LOCAL_EDITOR'] = self.cb.IsChecked()

########################################################################
class Preferences(wx.Toolbook):
	""" Based Toolbook Preference class
	"""

	def __init__(self, parent):
		"""
			Constructor.
		"""

		wx.Toolbook.__init__(self, parent, wx.ID_ANY, style=wx.BK_DEFAULT)

		### don't try to translate this labels with _() because there are used to find png
		L = [('General',"(self)"),('Simulation',"(self)"), ('Editor',"(self)"), ('Plugins',"(self)")]

		# make an image list using the LBXX images
		il = wx.ImageList(32, 32)
		for img in map(lambda a: wx.Image(os.path.join(ICON_PATH, "%s_pref.png"%a[0]), wx.BITMAP_TYPE_PNG).ConvertToBitmap(), L):
			il.Add(img)
		self.AssignImageList(il)

		imageIdGenerator = iter(range(il.GetImageCount()))
		for page, label in [(eval("%sPanel%s"%(s,str(args))), _(s)) for s,args in L]:
			self.AddPage(page, label, imageId=imageIdGenerator.next())

		### Plug-in page setting (populate is done when page is changed)
		self.pluginPanel = self.GetPage(self.GetPageCount()-1)
		self.CheckList = GeneralPluginsList(self.pluginPanel.GetRightPanel())
		self.pluginPanel.SetPluginsList(self.CheckList)

		lpanel = self.pluginPanel.GetLeftPanel()

		### Buttons for insert or delete plug-ins
		self.addBtn = wx.Button(lpanel, wx.ID_ADD, size=(140, -1))
		self.delBtn = wx.Button(lpanel, wx.ID_DELETE, size=(140, -1))
		self.refBtn = wx.Button(lpanel, wx.ID_REFRESH, size=(140, -1))
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

	#----------------------------------------------------------------------
	def OnPageChanged(self, event):
		"""
		"""
#		old = event.GetOldSelection()
		new = event.GetSelection()
#		sel = self.GetSelection()
#		print 'OnPageChanged,  old:%d, new:%d, sel:%d\n' % (old, new, sel)
		parent = self.GetTopLevelParent()
		### plug-ins page
		if new == 3:
			parent.SetSize((700,500))
		else:
			parent.SetSize((700,450))

		event.Skip()

	def OnPageChanging(self, event):
		"""
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
		""" Add plugin
		"""
		wcd = 'All files (*)|*|Editor files (*.py)|*.py'
		open_dlg = wx.FileDialog(self, message=_('Choose a file'), defaultDir=HOME_PATH, defaultFile='', wildcard=wcd, style=wx.OPEN|wx.CHANGE_DIR)
		if open_dlg.ShowModal() == wx.ID_OK:
			filename = open_dlg.GetPath()
			### sure is python file
			if filename.endswith('.py'):
				### Insert item in list
				basename,ext = os.path.splitext(os.path.basename(filename))
				root = os.path.dirname(filename)
				self.CheckList.InsertItem(root, basename)

				### trying to copy file in plug-in directory
				try:
					shutil.copy2(filename, PLUGINS_PATH)
				except Exception, info:
					sys.stderr.write(_('ERROR: %s copy failed!\n%s')%(os.path.basename(filemane), str(info)))
			else:
				sys.stderr.write(_('ERROR: %s is not a python file.\nOnly python file can be added as plugin.')%(os.path.basename(filemane)))

		open_dlg.Destroy()

	def OnDelete(self, event):
		""" Delete plug-ins item and python source file
		"""

		### selected plug-ins
		L = self.CheckList.get_selected_items()

		if L != []:
			### Delete query
			dial = wx.MessageDialog(self, _('Do You really want to delete selected plug-ins?'), _('Plug-in MAnager'), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
			if dial.ShowModal() == wx.ID_YES:
				### for selected plug-ins
				for plugin in L:

					### delete item
					self.CheckList.DeleteItem(plugin)

					try:
						### Delete python file
						name, ext = os.path.splitext(self.CheckList.GetPyData(plugin)[0].__file__)
						filename = "%s.py"%name
						dlg = wx.MessageDialog(self, _('Do You really want to remove %s plug-in file?')%os.path.basename(filename), _('Preference Manager'), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
						if dlg.ShowModal() == wx.ID_YES:
							os.remove(filename)
					except Exception:
						sys.stderr.write(_('ERROR: plug-in file not deleted!'))

			dial.Destroy()
		else:
			sys.stderr.write(_('Select plug-ins to delete'))

	def OnRefresh(self, event):
		""" Refresh list of plug-ins
		"""
		self.CheckList.Clear()
		l = list(os.walk(PLUGINS_PATH))
		### populate checklist with file in plug-ins directory
		wx.CallAfter(self.CheckList.Populate, (l))

	def OnApply(self,evt):
		""" Apply button has been pressed and we must take into account all changes for each panel
		"""
		for page in [self.GetPage(i) for i in xrange(self.GetPageCount())]:
			page.OnApply(evt)

########################################################################
class PreferencesGUI(wx.Frame):
	""" DEVSimPy Preferences General User Interface class
	"""

	def __init__(self, parent, title):
		"""
			Constructor.
		"""
		wx.Frame.__init__(self, parent, wx.ID_ANY, title, style = wx.DEFAULT_FRAME_STYLE | wx.CLIP_CHILDREN | wx.STAY_ON_TOP)

		_icon = wx.EmptyIcon()
		_icon.CopyFromBitmap(wx.Bitmap(os.path.join(ICON_PATH_16_16, "preferences.png"), wx.BITMAP_TYPE_ANY))
		self.SetIcon(_icon)

		self.SetMinSize((400,500))

		### Panel
		panel = wx.Panel(self, wx.ID_ANY)
		self.pref = Preferences(panel)

		### Buttons
		self.cancel = wx.Button(panel, wx.ID_CANCEL)
		self.apply = wx.Button(panel, wx.ID_OK)

		self.apply.SetToolTipString(_("Apply all changing"))
		self.cancel.SetToolTipString(_("Cancel without changing"))
		self.apply.SetDefault()

		### Sizers
		vsizer = wx.BoxSizer(wx.VERTICAL)
		hsizer = wx.BoxSizer(wx.HORIZONTAL)

		hsizer.Add(self.cancel,0)
 		hsizer.Add(self.apply,0)
		vsizer.Add(self.pref, 1, wx.ALL|wx.EXPAND, 5)
		vsizer.Add(hsizer, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

		panel.SetSizer(vsizer)
		vsizer.Fit(panel)

		### Binding
		self.Bind(wx.EVT_BUTTON, self.OnApply, id=wx.ID_OK)
		self.Bind(wx.EVT_BUTTON, self.OnCancel, id=wx.ID_CANCEL)
		self.Bind(wx.EVT_BUTTON, self.OnClose, id=wx.ID_CLOSE)

		self.Layout()
		self.Center()

	def OnApply(self, evt):
		""" Apply button has been clicked.
		"""
		self.pref.OnApply(evt)
		self.Close()

	def OnCancel(self, evt):
		self.Close()

	def OnClose(self, evt):
		self.Close()

### ------------------------------------------------------------
class TestApp(wx.App):
	""" Testing application
	"""

	def OnInit(self):

		import gettext

		__builtin__.__dict__['ICON_PATH'] = os.path.join('icons')
		__builtin__.__dict__['ICON_PATH_16_16'] = os.path.join(ICON_PATH, '16x16')
		__builtin__.__dict__['PLUGINS_PATH'] = os.path.join(HOME_PATH, 'plugins')
		__builtin__.__dict__['DOMAIN_PATH'] = 'Domain'
		__builtin__.__dict__['OUT_DIR'] = 'out'
		__builtin__.__dict__['NB_OPENED_FILE'] = 5
		__builtin__.__dict__['FONT_SIZE'] = 10
		__builtin__.__dict__['NB_HISTORY_UNDO'] = 10
		__builtin__.__dict__['TRANSPARENCY'] = False
		__builtin__.__dict__['SIMULATION_ERROR_SOUND_PATH'] = os.path.join(HOME_PATH,'sounds', 'Simulation-Error.mp3')
		__builtin__.__dict__['SIMULATION_SUCCESS_SOUND_PATH'] = os.path.join(HOME_PATH,'sounds', 'Simulation-Success.mp3')
		__builtin__.__dict__['NTL'] = False
		__builtin__.__dict__['DEFAULT_SIM_STRATEGY'] = 'bag-based'
		__builtin__.__dict__['DEFAULT_PYPDEVS_SIM_STRATEGY'] = 'original'
		__builtin__.__dict__['DEFAULT_PLOT_DYN_FREQ'] = 100
		__builtin__.__dict__['LOCAL_EDITOR'] = False
		__builtin__.__dict__['PYDEVS_SIM_STRATEGY_DICT'] = {'original':'SimStrategy1', 'bag-based':'SimStrategy2', 'direct-coupling':'SimStrategy3'}
		__builtin__.__dict__['PYPDEVS_SIM_STRATEGY_DICT'] = {'original':'SimStrategy4', 'distributed':'SimStrategy5', 'parallel':'SimStrategy6'}

		__builtin__.__dict__['_'] = gettext.gettext


		frame = PreferencesGUI(None, "Test")
		frame.Show()

		return True

	def OnQuit(self, event):
		self.Close()

if __name__ == '__main__':

	app = TestApp(0)
	app.MainLoop()