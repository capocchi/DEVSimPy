# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# ConnectionThread.py ---
#                     --------------------------------
#                        Copyright (c) 2010
#                       Laurent CAPOCCHI
#                      University of Corsica
#                     --------------------------------
# Version 3.1                                        last modified: 23/01/2014
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

import os
import sys
from threading import Thread
import urllib
import tempfile
import zipfile

import wx

__version_lib__ = 0.2


class unzip:
	def __init__(self, verbose=False, percent=10):
		self.verbose = verbose
		self.percent = percent

	def extract(self, file, dir):
		if not dir.endswith(':') and not os.path.exists(dir):
			os.mkdir(dir)

		zf = zipfile.ZipFile(file)

		# create directory structure to house files
		self._createstructure(file, dir)

		num_files = len(zf.namelist())
		percent = self.percent
		divisions = 100 / percent
		perc = int(num_files / divisions)

		# extract files to directory structure
		for i, name in enumerate(zf.namelist()):

			if self.verbose:
				sys.stdout.write(_("Extracting %s\n") % name)
			elif perc > 0 and (i % perc) == 0 and i > 0:
				complete = int(i / perc) * percent
				sys.stdout.write(_("%s \% complete\n") % complete)

			if not name.endswith('/'):
				outfile = open(os.path.join(dir, name), 'wb')
				outfile.write(zf.read(name))
				outfile.flush()
				outfile.close()


	def _createstructure(self, file, dir):
		self._makedirs(self._listdirs(file), dir)

	def _makedirs(self, directories, basedir):
		""" Create any directories that don't currently exist """
		for dir in directories:
			curdir = os.path.join(basedir, dir)
			if not os.path.exists(curdir):
				os.mkdir(curdir)

	def _listdirs(self, file):
		""" Grabs all the directories in the zip structure
		This is necessary to create the structure before trying
		to extract the file to it. """
		zf = zipfile.ZipFile(file)

		dirs = []

		for name in zf.namelist():
			if name.endswith('/'):
				dirs.append(name)

		dirs.sort()
		return dirs


class UpgradeLibThread(Thread):
	""" Worker thread class to attempt upgrade the libraries"""

	def __init__(self, parent):
		""" Initialize the worker thread.
		"""

		Thread.__init__(self)

		self._parent = parent

		self.setDaemon(True)
		self.start()

	def LoadZip(self, url):
		"""
		"""

		temp = tempfile.NamedTemporaryFile()
		zip = urllib.urlopen(url).read()
		try:
			temp.write(zip)
			temp.seek(0)
		finally:

			dlg = wx.MessageDialog(None, _("Are you sure to upgrade librairies from new version ?"), _("Upgrade Manager"), wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION)

			if dlg.ShowModal() == wx.ID_YES:
				unzipper = unzip()
				zipsource = temp.name
				zipdest = DOMAIN_PATH
				unzipper.extract(zipsource, zipdest)

			temp.close()

	def CheckVersion(self, text):
		""" Called by a worker thread which check DEVSimPy web page on the internet.
		"""

		if text is None:
			# We can't get to the internet?
			dial = wx.MessageDialog(None, _("Unable to connect to the internet."), _('Update Manager'), wx.OK | wx.ICON_ERROR)
			dial.ShowModal()
		else:
			# A bit shaky, but it seems to work...
			url = "http://devsimpy.googlecode.com/files/DEVSimPy_lib"
			prefix = "_"
			suffix = ".zip"
			indx = text.find(url)
			indx2 = text[indx:].find(prefix)
			indx3 = text[indx:].find(suffix)
			version = text[indx + indx2 + len(prefix + suffix):indx + indx3]

			if float(version) > float(__version_lib__):
				# Time to upgrade maybe?
				strs = _(
					"A new version of DEVSimPy libraries is available!\n\n Do you want to download and install it ?")
				dlg = wx.MessageDialog(None, strs, _("Update Manager"), wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION)
			else:
				# No upgrade required
				strs = _("You have the latest version of DEVSimPy libraries.")
				dlg = wx.MessageDialog(None, strs, _("Update Manager"), wx.OK)

			if dlg.ShowModal() == wx.ID_YES:
				### update the message of the Progess dialog
				self._parent.UpdatePulse(_("Downloading new libraries...."))
				### go to download zip file
				self.LoadZip(url + prefix + version + suffix)

	def run(self):
		""" Run worker thread. 
		"""

		# This is the code executing in the new thread. Simulation of
		# a long process as a simple urllib2 call
		try:
			# Try to read my web page
			url = "http://code.google.com/p/devsimpy/downloads/list"
			text = urllib.urlopen(url).read()
			wx.CallAfter(self.CheckVersion, text)
		except IOError:
			# Unable to get to the internet
			wx.CallAfter(self.CheckVersion, None)
		except Exception:
			# Some other strange error...
			wx.CallAfter(self.CheckVersion, None)

		return

	def finish(self):
		""" Return final value.
		"""
		return True