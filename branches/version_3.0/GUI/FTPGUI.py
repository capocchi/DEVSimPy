#! /usr/bin/python
# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# FTPGUI.py ---
#                     --------------------------------
#                          Copyright (c) 2013
#                           Laurent CAPOCCHI
#                         University of Corsica
#                     --------------------------------
# Version 3.0                                        last modified: 11/12/2012
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
import os

import wx


class FTPStatusBar(wx.StatusBar):
	def __init__(self, parent):
		wx.StatusBar.__init__(self, parent)

		self.SetFieldsCount(2)
		self.SetStatusText('Welcome to DEVSimPy server', 0)
		self.SetStatusWidths([-5, -2])
		self.icon = wx.StaticBitmap(self, wx.ID_ANY, wx.Bitmap(os.path.join(ICON_PATH_16_16, 'disconnect_network.png')))
		self.Bind(wx.EVT_SIZE, self.OnSize)
		self.PlaceIcon()

	def PlaceIcon(self):
		rect = self.GetFieldRect(1)
		self.icon.SetPosition((rect.x + 3, rect.y + 3))

	def OnSize(self, event):
		self.PlaceIcon()


class FTPFrame(wx.Frame):
	"""
	"""

	def __init__(self, parent, id, title):
		""" Constructor.
		"""

		wx.Frame.__init__(self, parent, id, title, size=(260, 270))

		wx.StaticText(self, wx.ID_ANY, 'Ftp site', (20, 20))
		wx.StaticText(self, wx.ID_ANY, 'Login', (20, 60))
		wx.StaticText(self, wx.ID_ANY, 'Password', (20, 100))

		self.ftpsite = wx.TextCtrl(self, wx.ID_ANY, 'http://lcapocchi.free.fr', (110, 15), (120, -1))
		self.login = wx.TextCtrl(self, wx.ID_ANY, 'lcapocchi', (110, 55), (120, -1))
		self.password = wx.TextCtrl(self, wx.ID_ANY, '', (110, 95), (120, -1), style=wx.TE_PASSWORD)

		self.ftp = None

		con = wx.Button(self, 1, 'Connect', (20, 160))
		discon = wx.Button(self, 2, 'DisConnect', (150, 160))

		self.Bind(wx.EVT_BUTTON, self.OnConnect, id=1)
		self.Bind(wx.EVT_BUTTON, self.OnDisConnect, id=2)

		self.statusbar = FTPStatusBar(self)
		self.SetStatusBar(self.statusbar)
		self.Centre()

	def OnConnect(self, event):
		if not self.ftp:
			ftpsite = self.ftpsite.GetValue()
			login = self.login.GetValue()
			password = self.password.GetValue()

		try:
			self.ftp = FTP(ftpsite)
			var = self.ftp.login(login, password)
			self.statusbar.SetStatusText('User connected')
			self.statusbar.icon.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH_16_16, 'connect_network.png')))
			self.OnSend()
		except AttributeError:
			self.statusbar.SetForegroundColour(wx.RED)
			self.statusbar.SetStatusText('Incorrect params')
			self.ftp = None

		except all_errors, err:
			self.statusbar.SetStatusText(str(err))
			self.ftp = None


	def OnSend(self, fn='out.kml'):

		with open(fn, 'rb') as f:
			sftp.storbinary('STOR %s' % "devsimpy/" + fn, f) # Send the file

	def OnDisConnect(self, event):
		if self.ftp:
			self.ftp.quit()
			self.ftp = None
			self.statusbar.SetStatusText('User disconnected')
			self.statusbar.icon.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH_16_16, 'disconnect_network.png')))