# -*- coding: utf-8 -*-

'''
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# FTPGUI.py ---
#                    --------------------------------
#                            Copyright (c) 2020
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 2.0                                        last modified: 26/12/25
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
'''

from ftplib import FTP, all_errors
import wx
import os
import threading

_ = wx.GetTranslation

from Utilities import load_and_resize_image


class FTPStatusBar(wx.StatusBar):
	"""Enhanced status bar with connection indicator"""

	def __init__(self, *args, **kw):
		super(FTPStatusBar, self).__init__(*args, **kw)

		self.SetFieldsCount(3)
		self.SetStatusWidths([-5, -2, 100])
		self.SetStatusText(_('Welcome to DEVSimPy FTP client'), 0)
		
		# Connection icon
		self.icon = wx.StaticBitmap(self, wx.NewIdRef(), 
									 load_and_resize_image('disconnect_network.png'))
		
		# Progress gauge
		self.gauge = wx.Gauge(self, wx.NewIdRef(), 100)
		self.gauge.Hide()
		
		self.Bind(wx.EVT_SIZE, self.OnSize)
		self.PlaceWidgets()

	def PlaceWidgets(self):
		"""Position widgets in status bar fields"""
		rect1 = self.GetFieldRect(1)
		self.icon.SetPosition((rect1.x + 3, rect1.y + 3))
		
		rect2 = self.GetFieldRect(2)
		self.gauge.SetPosition((rect2.x + 2, rect2.y + 2))
		self.gauge.SetSize((rect2.width - 4, rect2.height - 4))

	def OnSize(self, event):
		self.PlaceWidgets()
		event.Skip()

	def ShowProgress(self, show=True):
		"""Show/hide progress gauge"""
		if show:
			self.gauge.Show()
			self.gauge.Pulse()
		else:
			self.gauge.Hide()
		self.Refresh()


class FTPFrame(wx.Frame):
	"""Modern FTP client interface for DEVSimPy"""
	
	def __init__(self, *args, **kw):
		super(FTPFrame, self).__init__(*args, **kw)

		self.ftp = None
		self.current_dir = "/"
		self.OnInit()

	def OnInit(self):
		"""Initialize the interface"""
		
		# Set icon
		icon = wx.Icon()
		icon.CopyFromBitmap(load_and_resize_image('ftp.png'))
		self.SetIcon(icon)
		
		# Main panel
		panel = wx.Panel(self)
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		
		# Connection parameters in a StaticBoxSizer
		connectionBox = wx.StaticBoxSizer(wx.VERTICAL, panel, _("Connection Settings"))
		
		# FTP Site
		ftpSizer = wx.BoxSizer(wx.HORIZONTAL)
		ftpLabel = wx.StaticText(panel, label=_('FTP Site:'))
		ftpLabel.SetMinSize((80, -1))
		ftpSizer.Add(ftpLabel, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
		self.ftpsite = wx.TextCtrl(panel, wx.NewIdRef(), 'ftp.example.com')
		ftpSizer.Add(self.ftpsite, 1, wx.EXPAND)
		connectionBox.Add(ftpSizer, 0, wx.EXPAND|wx.ALL, 5)
		
		# Login
		loginSizer = wx.BoxSizer(wx.HORIZONTAL)
		loginLabel = wx.StaticText(panel, label=_('Login:'))
		loginLabel.SetMinSize((80, -1))
		loginSizer.Add(loginLabel, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
		self.login = wx.TextCtrl(panel, wx.NewIdRef(), '')
		loginSizer.Add(self.login, 1, wx.EXPAND)
		connectionBox.Add(loginSizer, 0, wx.EXPAND|wx.ALL, 5)
		
		# Password - CORRECTION ICI
		passSizer = wx.BoxSizer(wx.HORIZONTAL)
		passLabel = wx.StaticText(panel, label=_('Password:'))
		passLabel.SetMinSize((80, -1))
		passSizer.Add(passLabel, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
		self.password = wx.TextCtrl(panel, wx.NewIdRef(), '', 
									style=wx.TE_PASSWORD|wx.TE_PROCESS_ENTER)
		self.password.Bind(wx.EVT_TEXT_ENTER, self.OnConnect)
		passSizer.Add(self.password, 1, wx.EXPAND)
		connectionBox.Add(passSizer, 0, wx.EXPAND|wx.ALL, 5)
		
		# Save credentials checkbox
		self.saveCredentials = wx.CheckBox(panel, label=_('Remember credentials'))
		connectionBox.Add(self.saveCredentials, 0, wx.ALL, 5)
		
		mainSizer.Add(connectionBox, 0, wx.EXPAND|wx.ALL, 10)
		
		# File browser section
		browserBox = wx.StaticBoxSizer(wx.VERTICAL, panel, _("Remote Files"))
		
		# Current directory
		dirSizer = wx.BoxSizer(wx.HORIZONTAL)
		dirLabel = wx.StaticText(panel, label=_('Directory:'))
		dirSizer.Add(dirLabel, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
		self.currentDirCtrl = wx.TextCtrl(panel, value="/", style=wx.TE_READONLY)
		dirSizer.Add(self.currentDirCtrl, 1, wx.EXPAND)
		browserBox.Add(dirSizer, 0, wx.EXPAND|wx.ALL, 5)
		
		# File list
		self.fileList = wx.ListCtrl(panel, style=wx.LC_REPORT|wx.LC_SINGLE_SEL)
		self.fileList.InsertColumn(0, _('Name'), width=200)
		self.fileList.InsertColumn(1, _('Size'), width=100)
		self.fileList.InsertColumn(2, _('Modified'), width=150)
		self.fileList.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnFileActivated)
		browserBox.Add(self.fileList, 1, wx.EXPAND|wx.ALL, 5)
		
		mainSizer.Add(browserBox, 1, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 10)
		
		# Button bar
		buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
		
		# Connection buttons
		self.connectBtn = wx.Button(panel, label=_('Connect'))
		self.connectBtn.SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_PLUS, wx.ART_BUTTON))
		self.connectBtn.Bind(wx.EVT_BUTTON, self.OnConnect)
		buttonSizer.Add(self.connectBtn, 0, wx.ALL, 5)
		
		self.disconnectBtn = wx.Button(panel, label=_('Disconnect'))
		self.disconnectBtn.SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_MINUS, wx.ART_BUTTON))
		self.disconnectBtn.Bind(wx.EVT_BUTTON, self.OnDisConnect)
		self.disconnectBtn.Enable(False)
		buttonSizer.Add(self.disconnectBtn, 0, wx.ALL, 5)
		
		buttonSizer.AddStretchSpacer(1)
		
		# File operation buttons
		self.uploadBtn = wx.Button(panel, label=_('Upload'))
		self.uploadBtn.SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_BUTTON))
		self.uploadBtn.Bind(wx.EVT_BUTTON, self.OnUpload)
		self.uploadBtn.Enable(False)
		buttonSizer.Add(self.uploadBtn, 0, wx.ALL, 5)
		
		self.downloadBtn = wx.Button(panel, label=_('Download'))
		self.downloadBtn.SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE, wx.ART_BUTTON))
		self.downloadBtn.Bind(wx.EVT_BUTTON, self.OnDownload)
		self.downloadBtn.Enable(False)
		buttonSizer.Add(self.downloadBtn, 0, wx.ALL, 5)
		
		self.deleteBtn = wx.Button(panel, label=_('Delete'))
		self.deleteBtn.SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_DELETE, wx.ART_BUTTON))
		self.deleteBtn.Bind(wx.EVT_BUTTON, self.OnDelete)
		self.deleteBtn.Enable(False)
		buttonSizer.Add(self.deleteBtn, 0, wx.ALL, 5)
		
		mainSizer.Add(buttonSizer, 0, wx.EXPAND|wx.ALL, 10)
		
		panel.SetSizer(mainSizer)
		
		# Status bar
		self.statusbar = FTPStatusBar(self)
		self.SetStatusBar(self.statusbar)
		
		self.SetSize((600, 500))
		self.Centre()


	def OnConnect(self, event):
		"""Connect to FTP server"""
		if self.ftp:
			wx.MessageBox(_('Already connected!'), _('Info'), wx.OK | wx.ICON_INFORMATION)
			return
		
		ftpsite = self.ftpsite.GetValue().strip()
		login = self.login.GetValue().strip()
		password = self.password.GetValue()
		
		if not ftpsite:
			wx.MessageBox(_('Please enter FTP site address'), _('Error'), 
						 wx.OK | wx.ICON_ERROR)
			return
		
		# Remove protocol prefix if present
		ftpsite = ftpsite.replace('ftp://', '').replace('http://', '')
		
		self.statusbar.SetStatusText(_('Connecting...'))
		self.statusbar.ShowProgress(True)
		
		try:
			self.ftp = FTP(ftpsite, timeout=10)
			
			if login and password:
				response = self.ftp.login(login, password)
			else:
				response = self.ftp.login()  # Anonymous
			
			self.statusbar.SetStatusText(_('Connected: ') + response)
			self.statusbar.icon.SetBitmap(load_and_resize_image('connect_network.png'))
			self.statusbar.ShowProgress(False)
			
			# Update UI
			self.connectBtn.Enable(False)
			self.disconnectBtn.Enable(True)
			self.uploadBtn.Enable(True)
			self.downloadBtn.Enable(True)
			self.deleteBtn.Enable(True)
			
			# Load file list
			self.LoadFileList()
			
		except all_errors as err:
			self.statusbar.SetStatusText(_('Connection failed: ') + str(err))
			self.statusbar.ShowProgress(False)
			self.ftp = None
			wx.MessageBox(str(err), _('Connection Error'), wx.OK | wx.ICON_ERROR)

	def OnDisConnect(self, event):
		"""Disconnect from FTP server"""
		if self.ftp:
			try:
				self.ftp.quit()
			except:
				pass
			
			self.ftp = None
			self.statusbar.SetStatusText(_('Disconnected'))
			self.statusbar.icon.SetBitmap(load_and_resize_image('disconnect_network.png'))
			
			# Update UI
			self.connectBtn.Enable(True)
			self.disconnectBtn.Enable(False)
			self.uploadBtn.Enable(False)
			self.downloadBtn.Enable(False)
			self.deleteBtn.Enable(False)
			
			# Clear file list
			self.fileList.DeleteAllItems()
			self.currentDirCtrl.SetValue("/")

	def LoadFileList(self):
		"""Load and display remote file list"""
		if not self.ftp:
			return
		
		self.fileList.DeleteAllItems()
		
		try:
			self.current_dir = self.ftp.pwd()
			self.currentDirCtrl.SetValue(self.current_dir)
			
			# Get file list
			files = []
			self.ftp.dir(files.append)
			
			for idx, line in enumerate(files):
				parts = line.split()
				if len(parts) >= 9:
					# Parse Unix-style listing
					permissions = parts[0]
					size = parts[4]
					month = parts[5]
					day = parts[6]
					time = parts[7]
					name = ' '.join(parts[8:])
					
					is_dir = permissions.startswith('d')
					
					# Add to list
					index = self.fileList.InsertItem(idx, name)
					if is_dir:
						self.fileList.SetItem(index, 1, _('<DIR>'))
					else:
						self.fileList.SetItem(index, 1, size)
					self.fileList.SetItem(index, 2, f"{month} {day} {time}")
			
			self.statusbar.SetStatusText(_('Files loaded: ') + str(len(files)))
			
		except all_errors as err:
			wx.MessageBox(str(err), _('Error'), wx.OK | wx.ICON_ERROR)

	def OnFileActivated(self, event):
		"""Handle double-click on file/directory"""
		if not self.ftp:
			return
		
		index = event.GetIndex()
		name = self.fileList.GetItemText(index, 0)
		size = self.fileList.GetItemText(index, 1)
		
		if size == _('<DIR>'):
			# Change directory
			try:
				if name == '..':
					self.ftp.cwd('..')
				else:
					self.ftp.cwd(name)
				self.LoadFileList()
			except all_errors as err:
				wx.MessageBox(str(err), _('Error'), wx.OK | wx.ICON_ERROR)

	def OnUpload(self, event):
		"""Upload file to FTP server"""
		if not self.ftp:
			return
		
		with wx.FileDialog(self, _("Choose file to upload"),
						  wildcard="All files (*.*)|*.*",
						  style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
			
			if fileDialog.ShowModal() == wx.ID_CANCEL:
				return
			
			pathname = fileDialog.GetPath()
			filename = os.path.basename(pathname)
			
			try:
				self.statusbar.SetStatusText(_('Uploading...'))
				self.statusbar.ShowProgress(True)
				
				with open(pathname, 'rb') as f:
					self.ftp.storbinary(f'STOR {filename}', f)
				
				self.statusbar.SetStatusText(_('Upload complete: ') + filename)
				self.statusbar.ShowProgress(False)
				self.LoadFileList()
				
			except all_errors as err:
				self.statusbar.ShowProgress(False)
				wx.MessageBox(str(err), _('Upload Error'), wx.OK | wx.ICON_ERROR)

	def OnDownload(self, event):
		"""Download selected file"""
		if not self.ftp:
			return
		
		index = self.fileList.GetFirstSelected()
		if index == -1:
			wx.MessageBox(_('Please select a file to download'), _('Info'), 
						 wx.OK | wx.ICON_INFORMATION)
			return
		
		filename = self.fileList.GetItemText(index, 0)
		size = self.fileList.GetItemText(index, 1)
		
		if size == _('<DIR>'):
			wx.MessageBox(_('Cannot download directory'), _('Error'), 
						 wx.OK | wx.ICON_ERROR)
			return
		
		with wx.FileDialog(self, _("Save file as"),
						  defaultFile=filename,
						  wildcard="All files (*.*)|*.*",
						  style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
			
			if fileDialog.ShowModal() == wx.ID_CANCEL:
				return
			
			pathname = fileDialog.GetPath()
			
			try:
				self.statusbar.SetStatusText(_('Downloading...'))
				self.statusbar.ShowProgress(True)
				
				with open(pathname, 'wb') as f:
					self.ftp.retrbinary(f'RETR {filename}', f.write)
				
				self.statusbar.SetStatusText(_('Download complete: ') + filename)
				self.statusbar.ShowProgress(False)
				
			except all_errors as err:
				self.statusbar.ShowProgress(False)
				wx.MessageBox(str(err), _('Download Error'), wx.OK | wx.ICON_ERROR)

	def OnDelete(self, event):
		"""Delete selected file"""
		if not self.ftp:
			return
		
		index = self.fileList.GetFirstSelected()
		if index == -1:
			wx.MessageBox(_('Please select a file to delete'), _('Info'), 
						 wx.OK | wx.ICON_INFORMATION)
			return
		
		filename = self.fileList.GetItemText(index, 0)
		
		dlg = wx.MessageDialog(self, 
							   _('Delete file: ') + filename + '?',
							   _('Confirm Delete'),
							   wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
		
		if dlg.ShowModal() == wx.ID_YES:
			try:
				self.ftp.delete(filename)
				self.statusbar.SetStatusText(_('Deleted: ') + filename)
				self.LoadFileList()
			except all_errors as err:
				wx.MessageBox(str(err), _('Delete Error'), wx.OK | wx.ICON_ERROR)
		
		dlg.Destroy()
