# -*- coding: utf-8 -*-

""" 
	Authors: L. Capocchi (capocchi@univ-corse.fr)
	Date: 15/10/2010
	Description:
		Give a SIG view
	Depends: ftplib, Google Earth
"""

### ----------------------------------------------------------
 
import sys
import wx
import os
import webbrowser

from ftplib import FTP, all_errors
import wx.lib.agw.foldpanelbar as fpb

import pluginmanager
from Container import CodeBlock
from which import which
from FTPGUI import FTPStatusBar

from plugins.ExtendedFrame import Extended, GetExpandedIconBitmap, GetCollapsedIconBitmap


### dict of software use by this plugin
sft_lst = {'Google Earth':os.path.join(ICON_PATH_16_16,'googleearth-icon.png'), 'Google Maps':os.path.join(ICON_PATH_16_16,'firefox.png')}

@pluginmanager.register("START_SIG_VIEW")
def start_sig_viewer(*args, **kwargs):
	""" Start the web browser frame.
	"""

	fn = kwargs['fn']
	model = kwargs['model']

	### if google map has been chose
	if 'Maps' in model.software:

		wx.BeginBusyCursor()
		wx.Yield()

		### try to connect and copy the kml file on the ftp server
		try:
			sftp = FTP(ConfigFrame.FTP_SITE, ConfigFrame.LOGIN, ConfigFrame.PWD)
			fp = open(fn, 'rb') # file to send
			sftp.storbinary('STOR %s'%os.path.join(ConfigFrame.FTP_DIR,os.path.basename(fn)), fp) # Send the file
			fp.close() # Close file and FTP
			sftp.quit()
		except:
			sys.stdout.write(_("FTP connection failed!"))
		finally:
			wx.EndBusyCursor()

		### open web browser with google maps
		webbrowser.open('http://maps.google.fr/maps?f=q&source=s_q&hl=fr&geocode=&q=http:%2F%2Flcapocchi.free.fr%2Fdevsimpy%2Fout.kml&sll=46.75984,1.738281&sspn=11.456796,25.378418&ie=UTF8&z=10')

	### if google earth has been chose
	else:
		### open kml file with default client (googleearth) in regards with the os.
		if "wxMSW" in wx.PlatformInfo:
			#os.system("\"C:\Program Files\Google\Google Earth\client\googleearth.exe\"")
			os.startfile(fn)
		elif "wxGTK" in wx.PlatformInfo:
			try:
				os.system(which('googleearth')+' &')
			except:
				try:
					os.system(which('google-earth')+' &')
				except:
					sys.stdout.write(_("Where is Google Earth?\n"))
		else:
			os.system('open '+fn)

def Config(parent):
	""" Plugin settings frame.
	"""

	frame = ConfigFrame(parent, wx.ID_ANY, title = _('SIG Viewer'), size= (700,450), style = wx.DEFAULT_FRAME_STYLE | wx.CLIP_CHILDREN | wx.STAY_ON_TOP)
	frame.CenterOnParent(wx.BOTH)
	frame.Show()

class ConfigFrame(Extended):

	FTP_SITE = 'ftpperso.free.fr'
	FTP_DIR = 'devsimpy/'
	LOGIN = 'lcapocchi'
	PWD = ''


	def __init__(self, parent, id=wx.ID_ANY, title="", pos=wx.DefaultPosition, size=wx.DefaultSize, style = wx.DEFAULT_FRAME_STYLE | wx.CLIP_CHILDREN | wx.STAY_ON_TOP):
		""" Constructor.
		"""
		main = wx.GetApp().GetTopWindow()
		currentPage = main.nb2.GetCurrentPage()
		self.diagram = currentPage.diagram

		Extended.__init__(self, parent, id, title, pos, size, style)

		self.statusbar = FTPStatusBar(self)
		self.SetStatusBar(self.statusbar)

	def CreateRemainingSpace(self):

		model_lst = map(lambda a: a.label, filter(lambda s: "SIGViewer" in s.python_path, self.diagram.GetShapeList()))

		#model_lst = map(lambda a: a.label, filter(lambda s: "Dendrogram" in s.python_path, self.diagram.GetShapeList()))

		panel = wx.Panel(self, wx.ID_ANY, style=wx.SUNKEN_BORDER)

		vsizer = wx.BoxSizer(wx.VERTICAL)

		st = wx.StaticText(panel, wx.ID_ANY, _("Select SIG viewer model:"))
		self.cb = wx.CheckListBox(panel, wx.ID_ANY, (10, 30), (460, 330), model_lst)
		self.okBtn = wx.Button(panel, wx.ID_OK)
		self.cb.SetChecked([index for index in range(self.cb.GetCount()) if self.diagram.GetShapeByLabel(self.cb.GetString(index)).__class__ == SIGViewer])

		vsizer.Add(st, 0, wx.TOP,5)
		vsizer.Add((-1, 5))
		vsizer.Add(self.cb, 1,  wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
		vsizer.Add((-1, 5))
		vsizer.Add(self.okBtn, 0, wx.BOTTOM|wx.CENTER, 5)

		panel.SetSizer(vsizer)

		self._leftWindow1.Bind(wx.EVT_SASH_DRAGGED_RANGE, self.OnFoldPanelBarDrag, id=wx.NewId(), id2=wx.NewId())
		self.Bind(wx.EVT_SIZE, self.OnSize)
		self.Bind(wx.EVT_SCROLL, self.OnSlideColour)

		self.okBtn.Bind(wx.EVT_BUTTON, self.OnOk)
		self.cb.Bind(wx.EVT_LISTBOX, self.OnSelect)

		return panel

	def ReCreateFoldPanel(self, fpb_flags):

		# delete earlier panel
		self._leftWindow1.DestroyChildren()

		### only if the list of model is not empty
		if self.cb.GetCount() != 0:

			# recreate the foldpanelbar

			self._pnl = fpb.FoldPanelBar(self._leftWindow1, -1, wx.DefaultPosition, wx.Size(-1,-1), fpb_flags)

			Images = wx.ImageList(16,16)
			Images.Add(GetExpandedIconBitmap())
			Images.Add(GetCollapsedIconBitmap())
		###---------------------------------------------------------------------------------

			item = self._pnl.AddFoldPanel(_("Options"), collapsed=False, foldIcons=Images)

			self.selBtn = wx.Button(item, wx.ID_SELECTALL)
			self.desBtn = wx.Button(item, wx.ID_ANY, _("Deselect All"))

			self._pnl.AddFoldPanelWindow(item, self.selBtn, fpb.FPB_ALIGN_WIDTH, 5, 20)
			self._pnl.AddFoldPanelWindow(item, self.desBtn, fpb.FPB_ALIGN_WIDTH, 5, 20)

			self.selBtn.Bind(wx.EVT_BUTTON, self.OnSelectAll)
			self.desBtn.Bind(wx.EVT_BUTTON, self.OnDeselectAll)

		###---------------------------------------------------------------------------------

			item = self._pnl.AddFoldPanel(_("Softwares"), False, foldIcons=Images)

			self.ch = wx.combo.BitmapComboBox(item, wx.ID_ANY, pos=(100, 50), size=(170,-1))
			for elem in sft_lst:
				bmp = wx.Image(sft_lst[elem]).ConvertToBitmap()
				self.ch.Append(elem,bmp,elem)

			self._pnl.AddFoldPanelWindow(item, self.ch, fpb.FPB_ALIGN_WIDTH, 5, 20)

			self.ch.Bind(wx.EVT_COMBOBOX, self.EvtChoice)

		###---------------------------------------------------------------------------------

			item = self._pnl.AddFoldPanel(_("Network"), False, foldIcons=Images)

			self.ftpsite = wx.TextCtrl(item, wx.ID_ANY, ConfigFrame.FTP_SITE,  (110, 15), (120, -1))
			self.ftpdir = wx.TextCtrl(item, wx.ID_ANY, ConfigFrame.FTP_DIR,  (110, 55), (120, -1))
			self.login = wx.TextCtrl(item, wx.ID_ANY, ConfigFrame.LOGIN,  (110, 95), (120, -1))
			self.password = wx.TextCtrl(item, wx.ID_ANY, ConfigFrame.PWD,  (110, 135), (120, -1), style=wx.TE_PASSWORD)

			self._pnl.AddFoldPanelWindow(item, wx.StaticText(item, wx.ID_ANY,_('Ftp site'), (20, 20)), fpb.FPB_ALIGN_WIDTH, 5, 20)
			self._pnl.AddFoldPanelWindow(item, self.ftpsite, fpb.FPB_ALIGN_WIDTH, 5, 20)

			self._pnl.AddFoldPanelWindow(item, wx.StaticText(item, wx.ID_ANY,_('Ftp directory'), (20, 60)), fpb.FPB_ALIGN_WIDTH, 5, 20)
			self._pnl.AddFoldPanelWindow(item, self.ftpdir, fpb.FPB_ALIGN_WIDTH, 5, 20)

			self._pnl.AddFoldPanelWindow(item, wx.StaticText(item, wx.ID_ANY, _('Login'), (20, 100)), fpb.FPB_ALIGN_WIDTH, 5, 20)
			self._pnl.AddFoldPanelWindow(item, self.login, fpb.FPB_ALIGN_WIDTH, 5, 20)

			self._pnl.AddFoldPanelWindow(item, wx.StaticText(item, wx.ID_ANY, _('Password'), (20, 150)), fpb.FPB_ALIGN_WIDTH, 5, 20)
			self._pnl.AddFoldPanelWindow(item, self.password, fpb.FPB_ALIGN_WIDTH, 5, 20)

			self.test_btn = wx.Button(item, -1, _("Test"))
			self._pnl.AddFoldPanelWindow(item, self.test_btn, fpb.FPB_ALIGN_WIDTH, 5, 20)

			self.ftpsite.Bind(wx.EVT_TEXT, self.OnFtpSite)
			self.login.Bind(wx.EVT_TEXT, self.OnLogin)
			self.password.Bind(wx.EVT_TEXT, self.OnPassword)

			### try to read pwd from personnal config file (.devsimpy)
			try:
				self.password.SetValue(wx.GetApp().GetTopWindow().cfg.Read("ftppwd").decode('base64'))
			except:
				self.test_btn.Enable(False)

			self.test_btn.Bind(wx.EVT_BUTTON, self.OnConnect)

			self._leftWindow1.SizeWindows()


	def OnFtpSite(self, evt):
		ConfigFrame.FTP_SITE = self.ftpsite.GetValue()

	def OnLogin(self, evt):
		ConfigFrame.LOGIN = self.login.GetValue()

	def OnPassword(self, evt):
		ConfigFrame.PWD = self.password.GetValue()
		### crypt and stock the password
		wx.GetApp().GetTopWindow().cfg.Write('ftppwd', ConfigFrame.PWD.encode('base64'))

		self.test_btn.Enable(True)

	def OnConnect(self, evt):
		""" Test ftp connexion
		"""

		ftpsite = self.ftpsite.GetValue()
		login = self.login.GetValue()
		password = self.password.GetValue()

		wx.BeginBusyCursor()
		wx.Yield()

		try:
			self.ftp = FTP(ftpsite,login, password)
			self.statusbar.SetStatusText(_('User connected'))
			self.statusbar.icon.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH_16_16, 'connect_network.png')))
		except AttributeError:
			self.statusbar.SetForegroundColour(wx.RED)
			self.statusbar.SetStatusText(_('Incorrect params'))
			self.statusbar.icon.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH_16_16, 'disconnect_network.png')))
			self.ftp = None
		except all_errors, err:
			self.statusbar.SetStatusText(str(err))
			self.statusbar.icon.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH_16_16, 'disconnect_network.png')))
			self.ftp = None
		finally:
			### close de ftp connexion
			if hasattr(self, 'ftp') and self.ftp is not None:
				self.ftp.quit()

		wx.EndBusyCursor()

	def EvtChoice(self, evt):
		""" When the software has been selected.
		"""
		bcb = evt.GetEventObject()
		idx = evt.GetInt()
		self.software = bcb.GetString(idx)

		### if Google maps, the network setting is enabled
	#		if self.software == sft_lst.keys()[1]:


	def OnSelectAll(self, evt):
		""" Select All button has been pressed and all plugins are enabled.
		"""
		self.cb.SetChecked(range(self.cb.GetCount()))

	def OnDeselectAll(self, evt):
		""" Deselect All button has been pressed and all plugins are disabled.
		"""
		self.cb.SetChecked([])

	def OnOk(self, evt):
		""" When the frame has been closed.
		"""

		#btn = evt.GetEventObject()
		#frame = btn.GetTopLevelParent()
		for index in range(self.cb.GetCount()):
			label = self.cb.GetString(index)
			shape = self.diagram.GetShapeByLabel(label)
			shape.__class__ = SIGViewer if self.cb.IsChecked(index) else CodeBlock
			### we stock the software in the shape in order to find it on the start_sig_viewer function
			if hasattr(self, 'software'):
				shape.software = self.software
			else:
				shape.software = sft_lst.keys()[0]

		self.Destroy()

	def OnSelect(self, evt):
		""" When the sig_viewer model has been selected.
		"""

		label = self.cb.GetStringSelection()
		if label != "":
			shape = self.diagram.GetShapeByLabel(label)
			if not hasattr(shape,'software'):
				shape.software = sft_lst.keys()[0]

			self.ch.SetSelection(sft_lst.keys().index(shape.software))

#--------------------------------------------------
class SIGViewer(CodeBlock):
	""" SIGViewer(label)
	"""

	def __init__(self, label='SIGViewer'):
		""" Constructor
		"""

		CodeBlock.__init__(self, label, 1, 0)

	def OnLeftDClick(self, event):
		""" Left Double Click has been appeared.
		"""

		# If the frame is call before the simulation process, the atomicModel is not instanciate (Instanciation delegate to the makeDEVSconnection after the run of the simulation process)
		devs = self.getDEVSModel()

		if devs is not None:
			pluginmanager.trigger_event('START_SIG_VIEW', fn = devs.fn, model = self)
		else:
			dial = wx.MessageDialog(None, _('No data available \n Go to the simulation process first !'), 'Info', wx.OK)
			dial.ShowModal()