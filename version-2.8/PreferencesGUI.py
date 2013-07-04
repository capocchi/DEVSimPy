# -*- coding: utf-8 -*-

import wx
import os
import __builtin__
import __main__
import shutil
import sys

import wx.lib.filebrowsebutton as filebrowse

from PluginsGUI import PluginsPanel, GeneralPluginsList

#---------------------------------------------------------------------- 
class GeneralPanel(wx.Panel):
	""" general Panel
	"""

	def __init__(self, parent):
		"""
			Constructor
		"""
		wx.Panel.__init__(self, parent)

		### FileBrowse
		self.plugin_dir = filebrowse.DirBrowseButton(self, wx.ID_ANY, labelText=_("Plugins directory"), toolTip=_("Change the plugins directory"))
		self.domain_dir = filebrowse.DirBrowseButton(self, wx.ID_ANY, labelText=_("Library directory"), toolTip=_("Change the library directory"))
		self.out_dir = filebrowse.DirBrowseButton(self, wx.ID_ANY, labelText=_("Output directory"), toolTip=_("Change the output directory"))
		
		self.plugin_dir.SetValue(PLUGINS_DIR)
		self.domain_dir.SetValue(DOMAIN_PATH)
		self.out_dir.SetValue(OUT_DIR)

		### StaticText
		self.st1 = wx.StaticText(self, wx.ID_ANY, _("Number of recent file"))
		self.st2 = wx.StaticText(self, wx.ID_ANY, _("Font size"))
		self.st3 = wx.StaticText(self, wx.ID_ANY, _("Deep of history item"))
		
		self.st1.SetToolTipString(_("Feel free to change the lenght of list defining the recent opend files."))
		self.st2.SetToolTipString(_("Feel free to change the font size of DEVSimpy."))
		self.st3.SetToolTipString(_("Feel free to change the number of item for undo/redo command"))

		### SpinCtrl
		
		### number of opened file
		self.nb_opened_file = wx.SpinCtrl(self, wx.ID_ANY, '')
		self.nb_opened_file.SetRange(2, 20)
		self.nb_opened_file.SetValue(NB_OPENED_FILE)

		### Blcok font size
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
		__builtin__.__dict__['NB_OPENED_FILE'] = self.nb_opened_file.GetValue()		# number of recent files
		__builtin__.__dict__['NB_HISTORY_UNDO'] = self.nb_history_undo.GetValue()		# number of history undo
		__builtin__.__dict__['FONT_SIZE'] = self.font_size.GetValue()		# Block font size
		__builtin__.__dict__['DOMAIN_PATH'] = self.domain_dir.GetValue()
		__builtin__.__dict__['PLUGINS_DIR'] = os.path.basename(self.plugin_dir.GetValue())
		__builtin__.__dict__['OUT_DIR'] = os.path.basename(self.out_dir.GetValue())
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
		
		### Buttons
		self.sim_success_wav_btn = wx.Button(self, wx.ID_ANY, _("Finish.wav"), (25, 105), name='success')
		self.sim_error_wav_btn = wx.Button(self, wx.ID_ANY, _("Error.wav"), (25, 105), name='error')
		
		self.sim_success_wav_path = __builtin__.__dict__['SIMULATION_SUCCESS_WAV_PATH']
		self.sim_success_wav_btn.Enable(self.sim_success_wav_path is not os.devnull)
		self.sim_success_wav_btn.SetToolTipString(_("Press this button in order to change the song emmited for the end of the simulation."))

		self.sim_error_wav_path = __builtin__.__dict__['SIMULATION_ERROR_WAV_PATH']
		self.sim_error_wav_btn.Enable(self.sim_error_wav_path is not os.devnull)
		self.sim_error_wav_btn.SetToolTipString(_("Press this button in order to change the song emmited when an error occur in a model during the simulation."))

		### CheckBox
		self.bt5 = wx.CheckBox(self, wx.ID_ANY, _('Notification'))
		self.bt5.SetToolTipString(_("Notification song is generate when the simulation is over."))
		self.bt5.SetValue(self.sim_success_wav_path is not os.devnull)

		self.bt6 = wx.CheckBox(self, wx.ID_ANY, _('No Time Limit'))
		self.bt6.SetValue(__builtin__.__dict__['NTL'])
		self.bt6.SetToolTipString(_("No Time Limit allow the stop of simulation when all of models are idle."))
		
		### StaticText
		self.txt = wx.StaticText(self, wx.ID_ANY, _("Default strategy:"))
		self.cb = wx.ComboBox(self, wx.ID_ANY, DEFAULT_SIM_STRATEGY, choices=SIM_STRATEGY_LIST, style=wx.CB_READONLY)
		self.cb.SetToolTipString(_("Default strategy for the simulation algorithm. Please see the DEVSimPy doc for more information of possible strategy."))
		self.sim_defaut_strategy = DEFAULT_SIM_STRATEGY

		### StaticText
		self.sim_defaut_plot_dyn_freq = __builtin__.__dict__['DEFAULT_PLOT_DYN_FREQ']
		self.txt2 = wx.StaticText(self, wx.ID_ANY, _("Frequence of plotting refresh:"))
		self.sc = wx.SpinCtrl(self, wx.ID_ANY, str(self.sim_defaut_plot_dyn_freq), (55, 90), (60, -1), min=10, max=10000)
		self.sc.SetToolTipString(_("Default frequence for dynamic plotting."))
		
		### StaticBox and StaticText
		#information = wx.StaticText(self, wx.ID_ANY, _("Strategy information:"))
		#self.strategy_info = wx.StaticText(self, wx.ID_ANY, _("Default strategy\ndscdsc\n"),style=wx.ALIGN_CENTRE)
		
		### Adding sizer
		hbox1.Add(self.bt5, 0, wx.ALIGN_CENTER_VERTICAL, 15)
		hbox1.Add(self.sim_success_wav_btn, 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND,15)
		hbox1.Add(self.sim_error_wav_btn, 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND,15)

		hbox2.Add(self.txt, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT, 15)
		hbox2.Add(self.cb, 1, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT, 15)

		hbox3.Add(self.bt6, 0, wx.ALIGN_CENTER_VERTICAL, 15)

		hbox4.Add(self.txt2, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT, 15)
		hbox4.Add(self.sc, 1, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT, 15)
		
		#hbox4.Add(information, 1, wx.ALIGN_CENTER_VERTICAL, 15)
		##hbox4.Add(self.strategy_info, 1, wx.ALIGN_CENTER_VERTICAL, 15)
		
		vbox.Add(hbox1, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 10)
		vbox.Add(hbox2, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND,10)
		vbox.Add(hbox3, 0, wx.ALIGN_CENTER_VERTICAL,10)
		vbox.Add(hbox4, 0, wx.ALIGN_CENTER_VERTICAL,10)
		#vbox.Add(hbox4, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND,10)

		### Set sizer
		self.SetSizer(vbox)
		self.SetAutoLayout(True)
		
		### Binding
		self.sim_success_wav_btn.Bind(wx.EVT_BUTTON, self.OnSelectSound)
		self.sim_error_wav_btn.Bind(wx.EVT_BUTTON, self.OnSelectSound)
		self.bt5.Bind(wx.EVT_CHECKBOX, self.onBt5Check)
		self.cb.Bind(wx.EVT_COMBOBOX, self.onCb)
		self.sc.Bind(wx.EVT_SPINCTRL, self.onSc)
		
	def OnSelectSound(self, evt):
		"""
		"""
		dlg = wx.FileDialog(wx.GetTopLevelParent(self),
							_("Choose a sound file"),
							wildcard = _("WAV files (*.wav)|*.wav"),
							style = wx.OPEN)
							
		if dlg.ShowModal() == wx.ID_OK:
			val = dlg.GetPath()
			name = evt.GetEventObject().GetName()
			try:
				### test the selected sound
				wx.Sound.PlaySound(val, wx.SOUND_SYNC)
				
				if name == 'success':
					self.sim_success_wav_path = val
				elif name == 'error':
					self.sim_error_wav_path = val
				else:
					pass
				
			except NotImplementedError, v:
				wx.MessageBox(str(v), _("Exception Message"))
				
		dlg.Destroy()
			
	def onBt5Check(self, evt):
		""" CheckBox has been checked
		"""
		
		if evt.GetEventObject().GetValue():
			self.sim_success_wav_btn.Enable(True)
			self.sim_error_wav_btn.Enable(True)
			self.sim_success_wav_path = __main__.builtin_dict['SIMULATION_SUCCESS_WAV_PATH']
			self.sim_error_wav_path = __main__.builtin_dict['SIMULATION_ERROR_WAV_PATH']
		else:
			self.sim_success_wav_btn.Enable(False)
			self.sim_error_wav_btn.Enable(False)
			self.sim_success_wav_path = os.devnull
			self.sim_error_wav_path = os.devnull
	
	def onCb(self, evt):
		""" CheckBox has been checked
		"""
		val = evt.GetEventObject().GetValue()
		self.sim_defaut_strategy = val
	
	def onSc(self, evt):
		""" CheckBox has been checked
		"""
		val = evt.GetEventObject().GetValue()
		self.sim_defaut_plot_dyn_freq = val
		
	def OnApply(self, evt):
		""" Apply changes
		"""
		__builtin__.__dict__['SIMULATION_SUCCESS_WAV_PATH'] = self.sim_success_wav_path
		__builtin__.__dict__['SIMULATION_ERROR_WAV_PATH'] = self.sim_error_wav_path
		__builtin__.__dict__['DEFAULT_SIM_STRATEGY'] = self.sim_defaut_strategy
		__builtin__.__dict__['DEFAULT_PLOT_DYN_FREQ'] = self.sim_defaut_plot_dyn_freq
		__builtin__.__dict__['NTL'] = self.bt6.GetValue()
		
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
		self.cb.SetToolTipString(_("This option dont work for the .amd and .cmd file. \n"
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
	
		### dont try to translate this labels with _() because there are used to find png
		L = [('General',"(self)"),('Simulation',"(self)"), ('Editor',"(self)"), ('Plugins',"(self)")]
		
		# make an image list using the LBXX images
		il = wx.ImageList(32, 32)
		for img in map(lambda a: wx.Image(os.path.join(ICON_PATH, "%s_pref.png"%a[0]), wx.BITMAP_TYPE_PNG).ConvertToBitmap(), L):
			il.Add(img)
		self.AssignImageList(il)

		imageIdGenerator = iter(range(il.GetImageCount()))
		for page, label in [(eval("%sPanel%s"%(s,str(args))), _(s)) for s,args in L]:
			self.AddPage(page, label, imageId=imageIdGenerator.next())

		### Plugin page setting (populate is done when page is chnaged)
		self.pluginPanel = self.GetPage(self.GetPageCount()-1)
		self.CheckList = GeneralPluginsList(self.pluginPanel.GetRightPanel())
		self.pluginPanel.SetPluginsList(self.CheckList)

		lpanel = self.pluginPanel.GetLeftPanel()
		
		### Buttons for insert or delete plugins
		self.addBtn = wx.Button(lpanel, wx.ID_ADD, size=(140, -1))
		self.delBtn = wx.Button(lpanel, wx.ID_DELETE, size=(140, -1))
		self.refBtn = wx.Button(lpanel, wx.ID_REFRESH, size=(140, -1))
		self.addBtn.SetToolTipString(_("Add new plugins"))
		self.delBtn.SetToolTipString(_("Delete all existing plugins"))
		self.refBtn.SetToolTipString(_("Refresh plugins list"))
		
		### add widget to plugin panel
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
		### plugins page
		if new == 3:
			parent.SetSize((700,500))
		else:
			parent.SetSize((700,450))
		    
		event.Skip()

	def OnPageChanging(self, event):
		"""
		"""
		new = event.GetSelection()
		### plugin page
		if new == 3:
			### list of plugins file in plugin directory
			l = list(os.walk(os.path.join(HOME_PATH, PLUGINS_DIR)))
			### populate checklist with file in plugins directory
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
				
				### trying to copy file in plugin directory
				try:
					shutil.copy2(filename, os.path.join(HOME_PATH, PLUGINS_DIR))
				except Exception, info:
					sys.stderr.write(_('ERROR: %s copy failed!\n%s')%(os.path.basename(filemane), str(info)))
			else:
				sys.stderr.write(_('ERROR: %s is not a python file.\nOnly python file can be added as plugin.')%(os.path.basename(filemane)))

		open_dlg.Destroy()

	def OnDelete(self, event):
		""" Delete plugins item and python source file
		"""

		### selected plugins
		L = self.CheckList.get_selected_items()

		if L != []:
			### Delete query
			dial = wx.MessageDialog(self, _('Do You realy want to delete selected plugins?'), 'Question', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
			if dial.ShowModal() == wx.ID_YES:
				### for selected plugins
				for plugin in L:

					### delete item
					self.CheckList.DeleteItem(plugin)

					try:
						### Delete python file
						name, ext = os.path.splitext(self.CheckList.GetPyData(plugin)[0].__file__)
						filename = "%s.py"%name
						dlg = wx.MessageDialog(self, _('Do You realy want to remove %s plugin file?')%os.path.basename(filename), 'Question', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
						if dlg.ShowModal() == wx.ID_YES:
							os.remove(filename)
					except Exception:
						sys.stderr.write(_('ERROR: plugin file not deleted!'))
						
			dial.Destroy()
		else:
			sys.stderr.write(_('Select plugins to delete'))

	def OnRefresh(self, event):
		""" Refresh list of plugins
		"""
		self.CheckList.Clear()
		l = list(os.walk(os.path.join(HOME_PATH, PLUGINS_DIR)))
		### populate checklist with file in plugins directory
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
		self.apply = wx.Button(panel, wx.ID_APPLY)
		self.cancel = wx.Button(panel, wx.ID_CANCEL)

		self.apply.SetToolTipString(_("Apply all changing"))
		self.cancel.SetToolTipString(_("Cancel without changing"))
		self.apply.SetDefault()

		### Sizers
		vsizer = wx.BoxSizer(wx.VERTICAL)
		hsizer = wx.StdDialogButtonSizer()

		hsizer.AddButton(self.cancel)
		hsizer.AddButton(self.apply)
		hsizer.Realize()
		vsizer.Add(self.pref, 1, wx.ALL|wx.EXPAND, 5)
		vsizer.Add(hsizer, 0, wx.CENTER, 5)
		panel.SetSizer(vsizer)
		vsizer.Fit(panel)

		### Binding
		self.Bind(wx.EVT_BUTTON, self.OnApply, id=wx.ID_APPLY)
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
	
		__builtin__.__dict__['HOME_PATH'] = os.getcwd()
		__builtin__.__dict__['ICON_PATH'] = os.path.join('icons')
		__builtin__.__dict__['ICON_PATH_16_16'] = os.path.join(ICON_PATH, '16x16')
		__builtin__.__dict__['PLUGINS_DIR'] = 'plugins'
		__builtin__.__dict__['DOMAIN_PATH'] = 'Domain'
		__builtin__.__dict__['OUT_DIR'] = 'out'
		__builtin__.__dict__['NB_OPENED_FILE'] = 5
		__builtin__.__dict__['FONT_SIZE'] = 10
		__builtin__.__dict__['NB_HISTORY_UNDO'] = 10
		__builtin__.__dict__['SIM_STRATEGY_LIST'] = ['Strategy1']
		__builtin__.__dict__['TRANSPARENCY'] = False
		__builtin__.__dict__['SIMULATION_ERROR_WAV_PATH'] = os.path.join(HOME_PATH,'sounds', 'Simulation-Error.wav')
		__builtin__.__dict__['SIMULATION_SUCCESS_WAV_PATH'] = os.path.join(HOME_PATH,'sounds', 'Simulation-Success.wav')
		__builtin__.__dict__['NTL'] = False
		__builtin__.__dict__['DEFAULT_SIM_STRATEGY'] = 'Strategy2'
		__builtin__.__dict__['DEFAULT_PLOT_DYN_FREQ'] = 100
		__builtin__.__dict__['LOCAL_EDITOR'] = False
		
		__builtin__.__dict__['_'] = gettext.gettext
	
	
		frame = PreferencesGUI(None, "Test")
		frame.Show()
	
		return True
	
	def OnQuit(self, event):
		self.Close()
		
if __name__ == '__main__':

	app = TestApp(0)
	app.MainLoop()