# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# Utilities.py ---
#                     ----------------------------------
#                          Copyright (c) 2014
#                           Andre-T LUCIANI
#                         Laurent CAPOCCHI
#                        University of Corsica
#                     ----------------------------------
# Version 3.0                                        last modified: 18/02/2013
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


### at the beginning to prevent with statement for python vetrsion <= 2.5
from __future__ import with_statement
import os
import sys
from tempfile import gettempdir
import time
import traceback
import platform
import string
import re
import math
import inspect
from itertools import combinations
from cStringIO import StringIO

import wx

### for replaceAll
import fileinput

# Used to recurse subdirectories
import fnmatch
import urllib, urllib2, httplib

# Used for smooth (spectrum)

try:
	from numpy import *
except ImportError:

	platform_sys = os.name

	if platform_sys in ('nt', 'mac'):
		sys.stdout.write("Numpy module not found. Go to www.scipy.numpy.org.\n")
	elif platform_sys == 'posix':
		sys.stdout.write("Numpy module not found. Install python-numpy (ubuntu) package.\n")
	else:
		sys.stdout.write("Unknown operating system.\n")
		sys.exit()

def vibrate(windowName, distance=15, times=5, speed=0.05, direction='horizontal'):
	#Speed is the number of seconds between movements
	#If times is odd, it increments so that window ends up in same location
	import time

	if not times % 2 == 0:
		times += 1
	location = windowName.GetPositionTuple()
	if direction == 'horizontal':
		newLoc = (location[0] + distance, location[1])
	elif direction == 'vertical':
		newLoc = (location[0], location[1] + distance)
	for x in range(times):
		time.sleep(speed)
		windowName.Move(wx.Point(newLoc[0], newLoc[1]))
		time.sleep(speed)
		windowName.Move(wx.Point(location[0], location[1]))


def getFileListFromInit(init_file):
	""" Return list of name composing all variable in __init__.py file
	"""

	py_file_list = []
	if os.path.basename(init_file) == "__init__.py":
		dName = os.path.dirname(init_file)

		with open(init_file, 'r') as f:
			tmp = [s.replace('\n', '').replace('\t', '').replace(',', '').replace('"', "").replace('\'', "").strip() for s in f.readlines()[1:-1] if not s.startswith('#')]
			for s in tmp:
				python_file = os.path.join(dName, s + '.py')
				### test if tmp is only composed by python file (case of the user write into the __init__.py file directory name is possible ! then we delete the directory names)
				if os.path.isfile(python_file):
					py_file_list.append(s)

	return py_file_list


def path_to_module(abs_python_filename):
	""" convert and replace sep to . in abs_python_filename
	"""

	# delete extention if exist
	abs_python_filename = os.path.splitext(abs_python_filename)[0]

	dir_name = os.path.basename(DOMAIN_PATH)
	## si Domain est dans le chemin du module a importer (le fichier .py est dans un sous repertoire du rep Domain)
	if abs_python_filename.startswith(DOMAIN_PATH):
		path = str(abs_python_filename[abs_python_filename.index(dir_name):]).strip('[]').replace(os.sep, '.').replace('/', '.')
	else:
		path = os.path.basename(abs_python_filename).replace(os.sep, '.').replace('/', '.')

		### Ajout du chemin dans le path pour l'import d'un lib exterieur
		domainPath = os.path.dirname(abs_python_filename)
		if domainPath not in sys.path:
			sys.path.insert(0, domainPath)

		# si commence par . (transfo de /) supprime le
		if path.startswith('.'):
			path = path[1:]

	return path


def getInstance(cls, args=None):
	""" Function that return the instance from class and args
	"""
	if not args: args = {}
	if inspect.isclass(cls):
		try:
			devs = cls(**args)
		except Exception:
			sys.stderr.write(_("Error in getInstance: %s class not instanciated with %s\n" % (cls, str(args))))
			return sys.exc_info()
		else:
			return devs
	else:
		sys.stderr.write(_("Error in getInstance: First parameter is not a class\n"))
		return sys.exc_info()

def isInstance(obj, inst):

	l = map(lambda v: v.__name__, inspect.getmro(obj.__class__))
	if hasattr(obj, '__class__'):
		return inst.__class__.__name__ in l
	else:
		return inst.__name__ in l

def itersubclasses(cls, _seen=None):
	"""
	itersubclasses(cls)

	Generator over all subclasses of a given class, in depth first order.

	>>> list(itersubclasses(int)) == [bool]
	True
	>>> class A(object): pass
	>>> class B(A): pass
	>>> class C(A): pass
	>>> class D(B,C): pass
	>>> class E(D): pass
	>>>
	>>> for cls in itersubclasses(A):
	...     print(cls.__name__)
	B
	D
	E
	C
	>>> # get ALL (new-style) classes currently defined
	>>> [cls.__name__ for cls in itersubclasses(object)] #doctest: +ELLIPSIS
	['type', ...'tuple', ...]
	"""

	if not isinstance(cls, type):
		raise TypeError('itersubclasses must be called with '
						'new-style classes, not %.100r' % cls)
	if _seen is None: _seen = set()
	try:
		subs = cls.__subclasses__()
	except TypeError: # fails only when cls is type
		subs = cls.__subclasses__(cls)
	for sub in subs:
		if sub not in _seen:
			_seen.add(sub)
			yield sub
			for sub in itersubclasses(sub, _seen):
				yield sub


def show_error(parent, msg=None):
	if msg is None:
		msg = sys.exc_info()
	message = ''.join(traceback.format_exception(*msg))
	dialog = wx.MessageDialog(parent, message, _('Error Manager'), wx.OK | wx.ICON_ERROR)
	dialog.ShowModal()


def getTopLevelWindow():
	return wx.GetApp().GetTopWindow()


def GetActiveWindow(event=None):
	aW = None

	for win in wx.GetTopLevelWindows():
		if getattr(win, 'IsActive', lambda: False)():
			aW = win

	if aW is None:
		child = wx.Window.FindFocus()
		aW = wx.GetTopLevelParent(child)

	if aW is None and event is not None:
		obj = event.GetEventObject()
		#### conditionnal statement only for windows
		aW = obj.GetInvokingWindow() if isinstance(obj, wx.Menu) else obj

	return aW


def check_connectivity(reference):
	try:
		urllib.request.urlopen(reference, timeout=1)
		return True
	except urllib.request.URLError:
		return False


def sendEvent(from_obj, to_obj, evt):
	""" Send Event 'evt' from 'form_obj' object 'to to_obj'
	"""
	evt.SetEventObject(from_obj)
	evt.SetId(to_obj.GetId())
	from_obj.GetEventHandler().ProcessEvent(evt)


def playSound(sound_path):
	""" Play sound from sound_path
	"""

	if sound_path != os.devnull:
		sound = wx.Sound(sound_path)
		if sound.IsOk():
			sound.Play(wx.SOUND_ASYNC)
			wx.YieldIfNeeded()

		else:
			sys.stderr.write(_("No sound\n"))

def GetMails(string):
	""" Get list of mails from string
	"""
	regex = re.compile('([a-zA-Z0-9-_.]+[@][a-zA-Z0-9-_.]+)')
	return regex.findall(string)


def MoveFromParent(frame=None, interval=10, direction='right'):
	assert (isinstance(frame, wx.Frame))

	frame.CenterOnParent(wx.BOTH)
	parent = frame.GetParent()
	if direction == 'right':
		x = parent.GetPositionTuple()[0] + parent.GetSizeTuple()[0] + interval
		y = parent.GetScreenPosition()[1]
	elif direction == 'left':
		x = parent.GetPositionTuple()[0] - parent.GetSizeTuple()[0] - interval
		y = parent.GetScreenPosition()[1]
	elif direction == 'top':
		x = parent.GetScreenPosition()[0]
		y = parent.GetPositionTuple()[1] - parent.GetSizeTuple()[1] - interval
	else:
		x = parent.GetScreenPosition()[0]
		y = parent.GetPositionTuple()[1] + parent.GetSizeTuple()[1] + interval

	frame.MoveXY(x, y)


def getDirectorySize(directory):
	dir_size = 0
	for (path, dirs, files) in os.walk(str(directory)):
		for file in files:
			filename = os.path.join(path, file)
			dir_size += os.path.getsize(filename)
	return dir_size / 1000


def exists(site, path):
	conn = httplib.HTTPConnection(site)
	conn.request('HEAD', path)
	response = conn.getresponse()
	conn.close()
	return response.status == 200


class Authentification_Dialog(wx.Dialog):
	def __init__(self, parent, id, title):
		wx.Dialog.__init__(self, parent, id, title, size=(250, 180))

		wx.StaticText(self, -1, 'Login', (10, 20))
		wx.StaticText(self, -1, 'Password', (10, 60))

		self.login = wx.TextCtrl(self, -1, '', (110, 15), (120, -1))
		self.password = wx.TextCtrl(self, -1, '', (110, 55), (120, -1), style=wx.TE_PASSWORD)

		con = wx.Button(self, wx.ID_OK, 'Connect', (10, 120))
		btn_cancel = wx.Button(self, wx.ID_CANCEL, pos=(120, 120))

		self.Bind(wx.EVT_BUTTON, self.OnConnect, id=wx.ID_OK)

		self.Centre()

	def OnConnect(self, event):
		login = self.login.GetValue()
		password = self.password.GetValue()
		event.Skip()


def checkURL(url):
	if url.startswith('https'):
		req = urllib2.Request(url)
		password_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()

		flag = False

		### while login and password is no good
		while (not flag):
			dlg = Authentification_Dialog(None, -1, _('Login to %s' % url))

			if dlg.ShowModal() == wx.ID_OK:
				login = dlg.login.GetValue()
				password = dlg.password.GetValue()
				dlg.Destroy()

				### if login and password are not empty
				if login != '' and password != '':
					password_manager.add_password(None, url, login, password)

					auth_manager = urllib2.HTTPBasicAuthHandler(password_manager)
					opener = urllib2.build_opener(auth_manager)
					### try to access at the url with login and password
					try:
						urllib2.install_opener(opener)
						handler = urllib2.urlopen(req)
						flag = True
						deadLinkFound = True
					except:
						flag = False
						deadLinkFound = False
				else:
					flag = False
					deadLinkFound = False
			else:
				flag = True
				deadLinkFound = False

		return deadLinkFound

	elif url.startswith('http'):
		try:
			urllib2.urlopen(urllib2.Request(url))
			return True
		except urllib2.URLError:
			return False
	else:
		return False


def replaceAll(file, searchExp, replaceExp):
	for line in fileinput.input(file, inplace=1):
		if searchExp in line:
			line = line.replace(searchExp, replaceExp)
		sys.stdout.write(line)


def listf(data):
	buffer = ""
	for line in data:
		buffer = buffer + line + "\n"
	return buffer


def quick_sort(list):
	""" Sort list in non-decreasing order, using Quick Sort. """
	# If list contains at most 1 element, it is already sorted.
	if len(list) <= 1:
		return list
	# Select a pivot, then partition the list.
	pivot = list[0]
	smaller = [x for x in list if x < pivot]
	equal = [x for x in list if x == pivot]
	greater = [x for x in list if x > pivot]
	if len(greater) > 1:
		print # Set breakpoint here.  Inspect 'pivot' and list 'greater'
	# Recurse and copy the results back into list.
	quick_sort(smaller)
	quick_sort(greater)
	list[:] = smaller + equal + greater
	return list


def RGBToHEX(rgb_tuple):
	""" convert an (R, G, B) tuple to #RRGGBB """
	hexcolor = '#%02x%02x%02x' % rgb_tuple
	# that's it! '%02x' means zero-padded, 2-digit hex values
	return hexcolor


def HEXToRGB(colorstring):
	""" convert #RRGGBB to an (R, G, B) tuple """
	colorstring = colorstring.strip()
	if colorstring[0] == '#': colorstring = colorstring[1:]
	if len(colorstring) != 6:
		raise ValueError, "input #%s is not in #RRGGBB format" % colorstring
	r, g, b = colorstring[:2], colorstring[2:4], colorstring[4:]
	r, g, b = [int(n, 16) for n in (r, g, b)]
	return r, g, b


def IsAllDigits(str):
	""" Is the given string composed entirely of digits? """

	match = string.digits + '.'
	ok = 1
	for letter in str:
		if letter not in match:
			ok = 0
			break
	return ok


def cut(lst, indexes):
	last = 0
	for i in indexes:
		yield lst[last:i]
		last = i
	yield lst[last:]


def generate(lst, n):
	""" lst to split, n size of split
		lst = [1,2,3,4] n = 2
		-> [[1,2],[3,4]],...
	"""
	for indexes in combinations(list(range(1, len(lst))), n - 1):
		yield list(cut(lst, indexes))


def relpath(path=''):
	### change sep from platform
	if wx.Platform in ('__WXGTK__', '__WXMAC__'):
		return path.replace('\\', os.sep)
	else:
		return path.replace('/', os.sep)


def flatten(list):
	"""
	Internal function that flattens a N-D list.


	**Parameters:**

	* list: the N-D list that needs to be flattened.
	"""

	res = []
	for item in list:
		if type(item) == ListType:
			res = res + flatten(item)
		elif item is not None:
			res = res + [item]
	return res


def unique(list):
	"""
	Internal function, returning the unique elements in a list.


	**Parameters:**

	* list: the list for which we want the unique elements.
	"""

	# Create a fake dictionary
	res = {}

	for item in list:
		# Loop over all the items in the list
		key, value = item
		if res.has_key(key):
			res[key].append(value)
		else:
			res[key] = [value]

	# Return the dictionary values (a list)
	return res.items()


def now():
	""" Returns the current time formatted. """

	t = time.localtime(time.time())
	st = time.strftime("%d %B %Y @ %H:%M:%S", t)

	return st


def shortNow():
	""" Returns the current time formatted. """

	t = time.localtime(time.time())
	st = time.strftime("%H:%M:%S", t)

	return st


def FractSec(s):
	"""
	Formats time as hh:mm:ss.


	**Parameters:**

	* s: the number of seconds.
	"""

	min, s = divmod(s, 60)
	h, min = divmod(min, 60)
	return h, min, s


def GetFolderSize(exePath):
	"""
	Returns the size of the executable distribution folder.


	**Parameters:**

	* exePath: the path of the distribution folder.
	"""

	folderSize = numFiles = 0
	join, getsize = os.path.join, os.path.getsize
	# Recurse over all the folders and sub-folders
	for path, dirs, files in os.walk(exePath):
		for file in files:
			# Get the file size
			filename = join(path, file)
			folderSize += getsize(filename)
			numFiles += 1

	if numFiles == 0:
		# No files found, has the executable ever been built?
		return "", ""

	folderSize = "%0.2f" % (folderSize / (1024 * 1024.0))
	numFiles = "%d" % numFiles

	return numFiles, folderSize


def RecurseSubDirs(directory, userDir, extensions):
	"""
	Recurse one directory to include all the files and sub-folders in it.


	**Parameters:**

	* directory: the folder on which to recurse;
	* userDir: the directory chosen by the user;
	* extensions: the file extensions to be filtered.
	"""

	config = []
	baseStart = os.path.basename(directory)

	normpath, join = os.path.normpath, os.path.join
	splitext, match = os.path.splitext, fnmatch.fnmatch

	# Loop over all the sub-folders in the top folder
	for root, dirs, files in os.walk(directory):
		start = root.find(baseStart) + len(baseStart)
		dirName = userDir + root[start:]
		dirName = dirName.replace("\\", "/")
		paths = []
		# Loop over all the files
		for name in files:
			# Loop over all extensions
			for ext in extensions:
				if match(name, ext):
					paths.append(normpath(join(root, name)))
					break

		if paths:
			config.append((dirName, paths))

	return config


def FormatSizeFile(size):
	if 0 <= size < 1000:
		txt = str(size) + " bytes"
	elif 1000 <= size < 1000000:
		txt = str(size / 1000) + " Ko"
	else:
		txt = str(size / 1000000) + " Mo"
	return txt


def FormatTrace(etype, value, trace):
	"""Formats the given traceback

	**Returns:**

	*  Formatted string of traceback with attached timestamp

	**Note:**

	*  from Editra.dev_tool
	"""

	exc = traceback.format_exception(etype, value, trace)
	exc.insert(0, "*** %s ***%s" % (now(), os.linesep))
	return "".join(exc)

def smooth(x, window_len=10, window='hanning'):
	"""smooth the data using a window with requested size.

	This method is based on the convolution of a scaled window with the signal.
	The signal is prepared by introducing reflected copies of the signal
	(with the window size) in both ends so that transient parts are minimized
	in the begining and end part of the output signal.

	input:
		x: the input signal
		window_len: the dimension of the smoothing window
		window: the type of window from 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'
			flat window will produce a moving average smoothing.

	output:
		the smoothed signal

	example:

	t = linspace(-2,2,0.1)
	x = sin(t)+randn(len(t))*0.1
	y = smooth(x)

	see also:

	numpy.hanning, numpy.hamming, numpy.bartlett, numpy.blackman, numpy.convolve
	scipy.signal.lfilter

	TODO: the window parameter could be the window itself if an array instead of a string
	"""

	if x.ndim != 1:
		raise ValueError, "smooth only accepts 1 dimension arrays."

	if x.size < window_len:
		raise ValueError, "Input vector needs to be bigger than window size."

	if window_len < 3:
		return x

	if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
		raise ValueError, "Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'"

	s = r_[2 * x[0] - x[window_len:1:-1], x, 2 * x[-1] - x[-1:-window_len:-1]]

	if window == 'flat': #moving average
		w = ones(window_len, 'd')
	else:
		w = eval(window + '(window_len)')

	y = convolve(w / w.sum(), map(lambda val: float(val), s), mode='same')
	return y[window_len - 1:-window_len + 1]


def EnvironmentInfo():
	"""
	Returns a string of the systems information.


	**Returns:**

	*  System information string

	**Note:**

	*  from Editra.dev_tool
	"""

	info = list()
	info.append("---- Notes ----")
	info.append("Please provide additional information about the crash here")
	info.extend(["", "", ""])
	info.append("---- System Information ----")
	info.append("Operating System: %s" % wx.GetOsDescription())
	if sys.platform == 'darwin':
		info.append("Mac OSX: %s" % platform.mac_ver()[0])
	info.append("Python Version: %s" % sys.version)
	info.append("wxPython Version: %s" % wx.version())
	info.append("wxPython Info: (%s)" % ", ".join(wx.PlatformInfo))
	info.append("Python Encoding: Default = %s  File = %s" % \
				(sys.getdefaultencoding(), sys.getfilesystemencoding()))
	info.append("wxPython Encoding: %s" % wx.GetDefaultPyEncoding())
	info.append("System Architecture: %s %s" % (platform.architecture()[0], \
												platform.machine()))
	info.append("Byte order: %s" % sys.byteorder)
	info.append("Frozen: %s" % str(getattr(sys, 'frozen', 'False')))
	info.append("---- End System Information ----")

	return os.linesep.join(info)

