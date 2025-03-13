# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# FTPGUI.py ---
#                    --------------------------------
#                            Copyright (c) 2020
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 20/15/20
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

from ftplib import FTP, all_errors
import wx

_ = wx.GetTranslation

from Utilities import load_and_resize_image

class FTPStatusBar(wx.StatusBar):

	def __init__(self, *args, **kw):
		super(FTPStatusBar, self).__init__(*args, **kw)

		self.SetFieldsCount(2)
		self.SetStatusText('Welcome to DEVSimPy server', 0)
		self.SetStatusWidths([-5, -2])
		self.icon = wx.StaticBitmap(self, wx.NewIdRef(), load_and_resize_image('disconnect_network.png'))
		self.Bind(wx.EVT_SIZE, self.OnSize)
		self.PlaceIcon()

	def PlaceIcon(self):
		rect = self.GetFieldRect(1)
		self.icon.SetPosition((rect.x+3, rect.y+3))

	def OnSize(self, event):
		self.PlaceIcon()

class FTPFrame(wx.Frame):
	"""
	"""
	def __init__(self, *args, **kw):
		super(FTPFrame, self).__init__(*args, **kw)

		self.ftp = None
		self.OnInit()

	def OnInit(self):

		panel = wx.Panel(self)

		vbox = wx.BoxSizer(wx.VERTICAL)

		hbox1 = wx.BoxSizer(wx.HORIZONTAL)
		st1 = wx.StaticText(panel, label=_('Ftp site'))
		hbox1.Add(st1, flag=wx.RIGHT, border=8)
		self.ftpsite =  wx.TextCtrl(panel, wx.NewIdRef(), 'http://lcapocchi.free.fr')
		hbox1.Add(self.ftpsite, proportion=1)
		vbox.Add(hbox1, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)

		vbox.Add((-1, 10))

		hbox2 = wx.BoxSizer(wx.HORIZONTAL)
		st2 = wx.StaticText(panel, label=_('Login'))
		hbox2.Add(st2, flag=wx.RIGHT, border=8)
		self.login = wx.TextCtrl(panel, wx.NewIdRef(), 'lcapocchi')
		hbox2.Add(self.login, proportion=1)
		vbox.Add(hbox2, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)

		vbox.Add((-1, 10))

		hbox3 = wx.BoxSizer(wx.HORIZONTAL)
		st3 = wx.StaticText(panel, label=_('Password'))
		hbox3.Add(st3, flag=wx.RIGHT, border=8)
		self.password = wx.TextCtrl(panel, wx.NewIdRef(), '', style=wx.TE_PASSWORD)
		hbox3.Add(self.password, proportion=1)
		vbox.Add(hbox3, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)

		vbox.Add((-1, 10))

		hbox4 = wx.BoxSizer(wx.HORIZONTAL)
		con = wx.Button(panel, label=_('Connect'), size=(70, 30))
		hbox4.Add(con)
		discon = wx.Button(panel, label=_('DisConnect'), size=(100, 30))
		hbox4.Add(discon, flag=wx.LEFT|wx.BOTTOM, border=5)
		vbox.Add(hbox4, flag=wx.ALIGN_RIGHT|wx.RIGHT, border=10)

		#wx.StaticText(self.panel, wx.NewIdRef(), _('Ftp site'), (20, 20))
		#wx.StaticText(self.panel, wx.NewIdRef(), _('Login'), (20, 60))
		#wx.StaticText(self.panel, wx.NewIdRef(), _('Password'), (20, 100))

		#self.ftpsite = wx.TextCtrl(self.panel, wx.NewIdRef(), 'http://lcapocchi.free.fr',  (110, 15), (120, -1))
		#self.login = wx.TextCtrl(self.panel, wx.NewIdRef(), 'lcapocchi',  (110, 55), (120, -1))
		#self.password = wx.TextCtrl(self.panel, wx.NewIdRef(), '',  (110, 95), (120, -1), style=wx.TE_PASSWORD)

		#con = wx.Button(self.panel, wx.NewIdRef(), _('Connect'), (20, 160))
		#discon = wx.Button(self.panel, wx.NewIdRef(), _('DisConnect'), (120, 160))

		self.Bind(wx.EVT_BUTTON, self.OnConnect, id=con.GetId())
		self.Bind(wx.EVT_BUTTON, self.OnDisConnect, id=discon.GetId())

		self.statusbar = FTPStatusBar(self)
		self.SetStatusBar(self.statusbar)

		panel.SetSizer(vbox)
		self.Centre()

	def OnConnect(self, event):
		"""
		"""
		if not self.ftp:
			ftpsite = self.ftpsite.GetValue()
			login = self.login.GetValue()
			password = self.password.GetValue()

		try:
			self.ftp = FTP(ftpsite)
			var = self.ftp.login(login, password)
			self.statusbar.SetStatusText(_('User connected'))
			self.statusbar.icon.SetBitmap(load_and_resize_image('connect_network.png'))
			self.OnSend()
		except AttributeError:
			self.statusbar.SetForegroundColour(wx.RED)
			self.statusbar.SetStatusText(_('Incorrect params'))
			self.ftp = None
		except all_errors as err:
			self.statusbar.SetStatusText(str(err))
			self.ftp = None

	def OnSend(self, fn='out.kml'):
		"""
		"""
		with open(fn, 'rb') as f:
			sftp.storbinary('STOR %s'%"devsimpy/"+fn, f) # Send the file
	
	def OnDisConnect(self, event):
		"""
		"""
		if self.ftp:
			self.ftp.quit()
			self.ftp = None
			self.statusbar.SetStatusText('User disconnected')
			self.statusbar.icon.SetBitmap(load_and_resize_image('disconnect_network.png'))