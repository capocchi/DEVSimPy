# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# Utilities.py ---
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

import builtins
import os
import sys
import time
import traceback
import platform
import string
import re
import shutil
import configparser 
import tempfile
import pathlib

import inspect
if not hasattr(inspect, 'getargspec'):
    inspect.getargspec = inspect.getfullargspec
    
from datetime import datetime

import gettext
_ = gettext.gettext

from zipfile import ZipFile, ZIP_DEFLATED 

if builtins.__dict__.get('GUI_FLAG',True):
	import wx
	
	### for Phoenix
	if wx.VERSION_STRING >= '4.0':
		import wx.adv
		wx.Sound = wx.adv.Sound
		wx.SOUND_ASYNC = wx.adv.SOUND_ASYNC	

	try:
		from agw import pybusyinfo as PBI
	except ImportError: # if it's not there locally, try the wxPython lib.
		import wx.lib.agw.pybusyinfo as PBI

	from pubsub import pub

### for replaceAll
import fileinput

# Used to recurse subdirectories
import fnmatch
import urllib.request, urllib.parse, urllib.error, urllib.request, urllib.error, urllib.parse, http.client
from urllib.request import urlretrieve
	
import pip
import importlib

from subprocess import check_call, Popen, PIPE

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

#-------------------------------------------------------------------------------

def getFilePathInfo(path):
	"""
	"""
	assert os.path.isabs(path)

	dirname = os.path.dirname(path)
	basename = os.path.basename(path)
	info = os.path.splitext(basename)
	filename = info[0]
	extend = info[1][1:]

	return dirname, basename, filename, extend

def printOnStatusBar(statusbar, data={}):
	""" Send data on status bar
	"""
	for k,v in list(data.items()):
		statusbar.SetStatusText(v, k)

def NotificationMessage(title,message,parent, flag=2048, timeout=False):
	""" 2048 is wx.ICON_INFORMATION
	"""
	if builtins.__dict__['NOTIFICATION']:
		notify = wx.adv.NotificationMessage(
		title=title,
		message=message,
		parent=parent, flags=flag)

		# Various options can be set after the message is created if desired.
		# notify.SetFlags(# wx.ICON_INFORMATION
		#                 wx.ICON_WARNING
		#                 # wx.ICON_ERROR
		#                 )
		# notify.SetTitle("Wooot")
		# notify.SetMessage("It's a message!")
		# notify.SetParent(self)
		if timeout:
			notify.Show(timeout=timeout) # 1 for short timeout, 100 for long timeout
		else:
			notify.Show()

def now()->str:
    """ Returns the current time formatted. """

    t = time.localtime(time.time())
    st = time.strftime("%d %B %Y @ %H:%M:%S", t)

    return st

def module_list(topdir:str)->[str]:
	for root,dirs,files in os.walk(topdir):
		modpath = os.path.basename(topdir)
		r = os.path.relpath(root,topdir)
		if r != '.':
			modpath += '.' + r
		for extension in ('*.py', '*.amd', '*.cmd'):
			for f in fnmatch.filter(files, extension):
				if f == '__init__.py':
					yield modpath
				elif f not in ['__main__.py']:
					yield '.'.join([modpath,os.path.splitext(f)[0]])

def shortNow()->str:
    """ Returns the current time formatted. """

    t = time.localtime(time.time())
    st = time.strftime("%H:%M:%S", t)

    return st

class FixedList(list):
	""" List with fixed size (for undo/redo).
	"""

	def __init__(self, size = 5):
		list.__init__(self)
		self.__size =  size

	def GetSize(self):
		return self.__size

	def append(self, v):
		if len(self) == self.GetSize():
			del self[0]

		self.insert(len(self),v)

def getOutDir():
	"""
	"""
	out_dir = os.path.join(HOME_PATH, 'out')
	if not os.path.exists(out_dir):
		os.mkdir(out_dir)
	return out_dir

def PyBuzyInfo(msg, time):
	"""
	"""
	busy = PBI.PyBusyInfo(msg, parent=None, title=_("Info"))

	wx.Yield()

	for indx in range(time):
		wx.MilliSleep(1000)

	del busy

def check_internet():
	url = 'https://github.com/capocchi/DEVSimPy'
	timeout = 5
	try:
		
		_ = urllib.request.urlopen(url, timeout=timeout)
	except Exception as e:
		print(e)
		return False
	else:
		return True

def updatePiP():
	"""
	"""

	if check_internet():	
		try:
			command = "python -m pip install --upgrade pip"
			run_command(command, "to_progress_diag")
		except Exception as ee:
			print(ee.output)
			return False
		else:
			return True
	else:
		return False

def downloadFromURL(url):
	"""
	"""
	
	try:
		# downloading with request
		# download the file contents in binary format
		pub.sendMessage("to_progress_diag", message=_(f"Download git archive from:\n{url}"))
		r = urllib.request.urlopen(url)
	except Exception as e:
		print(e)
		return None
	else:
		if r.getcode() == 200:
		# 200 means a successful request
			tempdir = tempfile.gettempdir()
			fn = os.path.join(tempdir, "DEVSimPy.zip")
			# downloading with urllib
			# Copy a network object to a local file
			pub.sendMessage("to_progress_diag", message=_(f"Copy a network object to:\n{fn}"))
			urlretrieve(url, fn)
			pub.sendMessage("to_progress_diag", message=_(f"Copy done!"))
			return fn

		else:
			return None

def zipdir(path, ziph):
	# ziph is zipfile handle
	lenDirPath = len(path)
	for root, dirs, files in os.walk(path):
		for file in files:
			filePath = os.path.join(root, file)
			ziph.write(filePath , filePath[lenDirPath:])

def copy_dir(src, dst):
	dst.mkdir(parents=True, exist_ok=True)
	for item in os.listdir(src):
		s = src / item
		d = dst / item
		if s.is_dir():
			copy_dir(s, d)
		else:
			shutil.copy2(str(s), str(d))

def updateFromGitRepo():
	""" Updated DEVSimPy from Git with a zip (not with git command)
	"""
	import git

	try:
		pub.sendMessage("to_progress_diag", message=_("Pull..."))
		repo = git.Repo(HOME_PATH)
		o = repo.remotes.origin
		o.pull()
	except Exception as err:
		print('print_exc():')
		traceback.print_exc(file=sys.stdout)
		print('\n')
		print('print_exc(1):')
		traceback.print_exc(limit=1, file=sys.stdout)
		return False
	else:
		pub.sendMessage("to_progress_diag", message=_("Done!"))
		return True

def updateFromGitArchive():
	""" Updated DEVSimPy from Git with a zip (not with git command)
	"""

	# specifying the zip file name 
	fn = downloadFromURL("https://github.com/capocchi/DEVSimPy/archive/master.zip")
	
	if fn:

		tempdir = tempfile.gettempdir()
		now = datetime.now() # current date and time

		try:
			### make a backup of DEVSimPy sources to temp directory with the file DEVSimPy-backup-m_d_y
			pub.sendMessage("to_progress_diag", message=_(f"Backup DEVSimPy in {tempdir} directory..."))
			
			zipf = ZipFile(os.path.join(tempdir,''.join(['DEVSimPy-backup-',now.strftime("%m_%d_%Y"),'.zip'])), 'w', ZIP_DEFLATED)
			zipdir(os.getcwd(), zipf)
			zipf.close()
		except Exception as err:
			print('print_exc():')
			traceback.print_exc(file=sys.stdout)
			print('\n')
			print('print_exc(1):')
			traceback.print_exc(limit=1, file=sys.stdout)
			return False
		else:
			pub.sendMessage("to_progress_diag", message=_(f"Done!"))

		# opening the downloaded zip file in READ mode 
		with ZipFile(fn, 'a') as zip:
			
			# extracting all the files (simulate in order to wait if the user want to stop the process)
			pub.sendMessage("to_progress_diag", message=_("Extracting all the files..."))
			for elem in zip.infolist():
				time.sleep(0.1)
				
				p = pathlib.PurePosixPath(elem.filename)
				pub.sendMessage("to_progress_diag", message=_(f"Extract...\n{p.relative_to('DEVSimPy-master')}"))
			
			### effective extraction in temp directory
			zip.extractall(tempdir)

			### Copy the extracted files into the DEVSimPy folder.
			pub.sendMessage("to_progress_diag", message=_(f"Copy...\n{p.relative_to('DEVSimPy-master')}"))
			try:
				if platform.python_version() >= '3.8':
					shutil.copytree(os.path.join(tempdir, 'DEVSimPy-master'), os.path.join(tempdir, 'test'), dirs_exist_ok=True) 
				else:
					src = pathlib.Path(os.path.join(tempdir, 'DEVSimPy-master'))
					dest = pathlib.Path(os.path.join(tempdir, os.getcwd()))
					copy_dir(src, dest)
			except Exception as err:
				print('print_exc():')
				traceback.print_exc(file=sys.stdout)
				print('\n')
				print('print_exc(1):')
				traceback.print_exc(limit=1, file=sys.stdout)
				return False

		pub.sendMessage("to_progress_diag", message=_("Done!"))

		### delete temporary zip file
		#os.remove(fn)

		return True
			
	else:
		return False

def run_command(command, message=None):
	""" run command and send a message for each output of the process using pubsub
	"""
	### dynamic output of the process to progress diag using pubsub!
	try:
		#process = Popen(shlex.split(command), stdout=PIPE, stderr = PIPE, shell=True, encoding='utf-8')
		process = Popen(command, stdout=PIPE, stderr = PIPE, shell=True, encoding='utf-8')
		while True:
			output = process.stdout.readline()
			if output == '' and process.poll() is not None:
				break
			if output and message:
				pub.sendMessage(message, message=output.strip())
		process.poll()
	except:
		check_call(command, shell=True)

def updatePiPPackages():
	""" Update all pip packages that DEVSimPy depends.
	"""

	if updatePiP():

		if pip.__version__ > '10.0.1':
			command = "pip install --user --upgrade -r requirements.txt"
		else:
			packages = [dist.project_name for dist in pip.get_installed_distributions() if 'PyPubSub' not in dist.project_name]
			command = "pip install --user --upgrade " + ' '.join(packages)

		try:
			run_command(command, "to_progress_diag")
		except Exception as err:
			print('print_exc():')
			traceback.print_exc(file=sys.stdout)
			print('\n')
			print('print_exc(1):')
			traceback.print_exc(limit=1, file=sys.stdout)
			return False
		else:
			return True
	else:
		return False

def install_and_import(package_to_install, package_to_import=None):
	""" Install and import the package
	"""
	### if package to import is different to the package to install
	if not package_to_import:
		package_to_import = package_to_install

	installed = install(package_to_install, package_to_import)
	if installed and package_to_import not in sys.modules: globals()[package_to_import] = importlib.import_module(package_to_import)
	return installed

def install(package_to_install, package_to_import=None):
	""" Install the package
	"""

	### if package to import is different to the package to install
	if not package_to_import:
		package_to_import = package_to_install
		
	try:
		importlib.import_module(package_to_import)
	except ImportError:
		if pip.main(['search', package_to_install]) != 23:
			dial = wx.MessageDialog(None, _('We find that the package %s is missing. \n\n Do you want to install him using pip?'%(package_to_install)), _('Package Manager'), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)

			if dial.ShowModal() == wx.ID_YES:
				installed = not pip.main(['install', package_to_install])
			else:
				installed = False

			dial.Destroy()
	else:
		installed = True

	return installed

def getObjectFromString(scriptlet):
	"""
	"""

	assert scriptlet != ''

	# Compile the scriptlet.
	try:
		code = compile(scriptlet, '<string>', 'exec')
	except Exception as info:
		return info
	else:
		# Create the new 'temp' module.
		temp = types.ModuleType("temp")
		sys.modules["temp"] = temp

		### there is syntaxe error ?
		try:
			exec(code, temp.__dict__)
		except Exception as info:
			return info

		else:
			classes = inspect.getmembers(temp, callable)
			for name, value in classes:
				if value.__module__ == "temp":
					# Create the instance.
					try:
						return eval("temp.%s" % name)()
					except Exception as info:
						return info

def vibrate(windowName, distance=15, times=5, speed=0.05, direction='horizontal'):
	""" Speed is the number of seconds between movements
		If times is odd, it increments so that window ends up in same location
	"""

	if not times % 2 == 0:
		times += 1
	
	location = windowName.GetPositionTuple()
	
	if direction == 'horizontal':
		newLoc = (location[0] + distance, location[1])
	elif direction == 'vertical':
		newLoc = (location[0], location[1] + distance)
	
	for x in range(times):
		time.sleep(speed)
		windowName.Move(wx.Point(int(newLoc[0]), int(newLoc[1])))
		time.sleep(speed)
		windowName.Move(wx.Point(int(location[0]), int(location[1])))

def GetUserConfigDir():
	""" Return the standard location on this platform for application data.
	"""
	return os.path.expanduser("~")

def GetWXVersionFromIni():
	""" Return the wx version loaded in devsimpy (from ini file if exist).
	"""

	### update the init file into GetUserConfigDir
	parser = configparser.ConfigParser()
	path = os.path.join(GetUserConfigDir(), 'devsimpy.ini')
	parser.read(path)

	section, option = ('wxversion', 'to_load')

	### if ini file exist we remove old section and option
	try:
		return parser.get(section, option)
	except:
		return  wx.VERSION_STRING

def AddToInitFile(init_dir_path, L):
	""" Add the name of file in L to the __init__.py file located to init_path.
	"""

	init_path = os.path.join(init_dir_path, '__init__.py')

	if os.path.exists(init_path):
		### find all py and pyc file in PLUGINS_PATH
		files = []
		# r=root, d=directories, f = files
		for r, d, f in os.walk(init_dir_path):
			for file in f:
				if file.endswith(('.py','.pyc')):
					b,e=os.path.splitext(file)
					files.append(b)

		### str of __all__ variable extracted from __init__.py file
		f = open(init_path,"r")
		init_str = "".join([a.replace('\n','\t') for a in f.readlines()])

		### rewrite __init__.py file with the new basename plugin
		with open(init_path,"w+") as f:
			f.write('__all__ = [\n')
			for n in files:
				if n in init_str:
					f.write("'%s',\n"%n)
			for basename in L[:-1]:
				if basename not in init_str:
					f.write("'%s',\n"%basename)
			if L[-1] not in init_str:
				f.write("'%s'\n]"%L[-1])
			else:
				f.write("\n]")
	else:
		sys.stderr.write(_("__init__.py file doesn't exists in %s directory!"%init_dir_path))

def DelToInitFile(init_dir_path, L):
	""" Delete the name of file in L to the __init__.py file located to init_path
	"""

	init_path = os.path.join(init_dir_path, '__init__.py')

	if os.path.exists(init_path):
		### find all py and pyc file in PLUGINS_PATH
		files = []
		# r=root, d=directories, f = files
		for r, d, f in os.walk(init_dir_path):
			for file in f:
				if file.endswith(('.py','.pyc')):
					b,e=os.path.splitext(file)
					files.append(b)

		### str of __all__ variable extracted from __init__.py file
		f = open(init_path,"r")
		init_str = "".join([a.replace('\n','\t') for a in f.readlines()])

		### rewrite __init__.py file with the new basename plugin
		with open(init_path,"w+") as f:
			f.write('__all__ = [\n')
			L = [f for f in files if f not in L and f in init_str]
			for n in L[:-1]:
				f.write("'%s',\n"%n)
			f.write("'%s'\n]"%L[-1])
	else:
		sys.stderr.write(_("__init__.py file doesn't exists in %s directory!"%init_dir_path))

def getPYFileListFromInit(init_file, ext='.py'):
	""" Return list of name composing all variable in __init__.py file.
	"""

	assert(ext in ('.py', '.pyc'))

	file_list = []
	if os.path.basename(init_file) == "__init__.py":

		dName = os.path.dirname(init_file)

		with open(init_file,'r') as f:
			tmp = [s.replace('\n','').replace('\t','').replace(',','').replace('"',"").replace('\'',"").strip() for s in f.readlines()[1:-1] if not s.startswith('#')]
			for s in tmp:
				python_file = os.path.join(dName,s+ext)
				### test if tmp is only composed by python file (case of the user write into the __init__.py file directory name is possible ! then we delete the directory names)
				if os.path.isfile(python_file):
					file_list.append(s)

	return file_list

def path_to_module(abs_python_filename):
	""" Convert and replace sep to . in abs_python_filename.
	"""

	# delete extention if exist
	abs_python_filename = os.path.splitext(abs_python_filename)[0]

	## si Domain est dans le chemin du module à importer (le fichier .py est dans un sous repertoire du rep Domain)
	if abs_python_filename.startswith(DOMAIN_PATH):
		dir_name = os.path.basename(DOMAIN_PATH)
		path = str(abs_python_filename[abs_python_filename.index(dir_name):]).strip('[]').replace(os.sep,'.').replace('/','.')
	else:

		path = os.path.basename(abs_python_filename).replace(os.sep,'.').replace('/','.')

		### Ajout du chemin dans le path pour l'import d'un lib exterieur
		domainPath = os.path.dirname(abs_python_filename)
		if domainPath not in sys.path:
			sys.path.insert(0, domainPath)

		# si commence par . (transfo de /) supprime le
		if path.startswith('.'):
			path = path[1:]

	return path

def getInstance(cls, args = {}):
	""" Function that return the instance from class and args.
	"""

	if inspect.isclass(cls):
		try:
			devs = cls(**args)
		except Exception as info:
			sys.stderr.write(_("Error in getInstance: %s not instanciated with %s.\n"%(cls,str(args))))
			sys.stderr.write(traceback.format_exc())
			return sys.exc_info()
		else:
			return devs
	else:
		sys.stderr.write(_("Error in getInstance: First parameter (%s) is not a class.\n")%str(cls))
		return sys.exc_info()

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

def getTopLevelWindow():
	"""
	"""
	return wx.GetApp().GetTopWindow()

def GetActiveWindow(event=None):
	"""
	"""
	aW = None

	for win in wx.GetTopLevelWindows():
		if getattr(win, 'IsActive', lambda:False)():
			aW = win

	if aW is None:
		try:
			child = wx.Window.FindFocus()
			aW = wx.GetTopLevelParent(child)
		except:
			pass
			
	if aW is None and event is not None:

		obj = event.GetEventObject()
		#### conditional statement only for windows
		aW = obj.GetInvokingWindow() if isinstance(obj, wx.Menu) else obj

	return aW

def sendEvent(from_obj, to_obj, evt):
	""" Send Event 'evt' from 'form_obj' object 'to to_obj'.
	"""
	evt.SetEventObject(from_obj)
	evt.SetId(to_obj.GetId())
	from_obj.GetEventHandler().ProcessEvent(evt)

def playSound(sound_path):
	""" Play sound from sound_path.
	"""

	if sound_path != os.devnull:
		sound = wx.Sound(sound_path)
		if sound.IsOk():
			sound.Play(wx.SOUND_ASYNC)
			wx.YieldIfNeeded()
		else:
			sys.stderr.write(_("No sound\n"))

def GetMails(string):
	""" Get list of mails from string.
	"""

	regex = re.compile('([a-zA-Z0-9-_.]+[@][a-zA-Z0-9-_.]+)')
	return regex.findall(string)

def MoveFromParent(frame=None, interval=10, direction='right'):
	"""
	"""
	assert(isinstance(frame, wx.Frame))

	frame.CenterOnParent(wx.BOTH)
	parent = frame.GetParent()
	if direction == 'right':
		x = parent.GetPosition()[0]+parent.GetSize()[0] + interval
		y = parent.GetScreenPosition()[1]
	elif direction == 'left':
		x = parent.GetPositionTuple()[0]-parent.GetSizeTuple()[0] - interval
		y = parent.GetScreenPosition()[1]
	elif direction == 'top':
		x = parent.GetScreenPosition()[0]
		y = parent.GetPositionTuple()[1]-parent.GetSizeTuple()[1] - interval
	else:
		x = parent.GetScreenPosition()[0]
		y = parent.GetPositionTuple()[1]+parent.GetSizeTuple()[1] + interval

	frame.Move(x,y)

def getDirectorySize(directory):
	"""
	"""
	dir_size = 0
	for (path, dirs, files) in os.walk(str(directory)):
		for file in [a for a in files if a.endswith(('.py', '.amd', '.cmd'))]:
			filename = os.path.join(path, file)
			dir_size += os.path.getsize(filename)
	return dir_size/1000

def exists(site, path):
	"""
	"""
	conn = http.client.HTTPConnection(site)
	conn.request('HEAD', path)
	response = conn.getresponse()
	conn.close()
	return response.status == 200

def checkURL(url):
	"""
	"""
	class Authentification_Dialog(wx.Dialog):

		def __init__(self, parent, id, title):
			wx.Dialog.__init__(self, parent, id, title, size=(250, 180))


			wx.StaticText(self, -1, 'Login', (10, 20))
			wx.StaticText(self, -1, 'Password', (10, 60))

			self.login = wx.TextCtrl(self, -1, '',  (110, 15), (120, -1))
			self.password = wx.TextCtrl(self, -1, '',  (110, 55), (120, -1), style=wx.TE_PASSWORD)

			con = wx.Button(self, wx.ID_OK, 'Connect', (10, 120))
			btn_cancel = wx.Button(self, wx.ID_CANCEL, pos = (120, 120))

			self.Bind(wx.EVT_BUTTON, self.OnConnect, id=wx.ID_OK)

			self.Centre()

		def OnConnect(self, event):
			login = self.login.GetValue()
			password = self.password.GetValue()
			event.Skip()

	if url.startswith('https'):
		req = urllib.request.Request(url)
		password_manager = urllib.request.HTTPPasswordMgrWithDefaultRealm()

		flag = False

		### while login and password is no good
		while(not flag):
			dlg = Authentification_Dialog(None, -1, _('Login to %s'%url))

			if dlg.ShowModal() == wx.ID_OK:
				login = dlg.login.GetValue()
				password = dlg.password.GetValue()
				dlg.Destroy()

				### if login and password are not empty
				if login != '' and password != '':
					password_manager.add_password(None, url, login, password)

					auth_manager = urllib.request.HTTPBasicAuthHandler(password_manager)
					opener = urllib.request.build_opener(auth_manager)
					### try to access at the url with login and password
					try:
						urllib.request.install_opener(opener)
						handler = urllib.request.urlopen(req)
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
			urllib.request.urlopen(urllib.request.Request(url))
			return True
		except urllib.error.URLError:
			return False
	else:
		return False

def replaceAll(file,searchExp,replaceExp):
    """
    """
    for line in fileinput.input(file, inplace=1):
        if searchExp in line:
                line = line.replace(searchExp,replaceExp)
        sys.stdout.write(line)

def listf(data):
	"""
	"""
	buffer = ""
	for line in data:
		buffer = buffer + line + "\n"
	return buffer

def RGBToHEX(rgb_tuple):
    """ convert an (R, G, B) tuple to #RRGGBB """

    hexcolor = f'#%02x%02x%02x'%rgb_tuple[:-1]
    # that's it! '%02x' means zero-padded, 2-digit hex values
    return hexcolor
    

def HEXToRGB(colorstring):
    """ convert #RRGGBB to an (R, G, B) tuple """
    colorstring = colorstring.strip()
    if colorstring[0] == '#': colorstring = colorstring[1:]
    if len(colorstring) != 6:
        raise ValueError("input #%s is not in #RRGGBB format" % colorstring)
    r, g, b = colorstring[:2], colorstring[2:4], colorstring[4:]
    r, g, b = [int(n, 16) for n in (r, g, b)]
    return (r, g, b)

def IsAllDigits(str):
	""" Is the given string composed entirely of digits? """

	match = string.digits+'.'
	ok = 1
	for letter in str:
		if letter not in match:
			ok = 0
			break
	return ok

def relpath(path=''):
	### change sep from platform
	from sys import platform
	if platform == "linux" or platform == "linux2":
		return path.replace('\\',os.sep)
	elif platform == "darwin":
		return path.replace('\\',os.sep)
	elif platform == "win32":
		return path.replace('/',os.sep)

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
    """
    """
    if 0 <= size <1000 :
        txt = str(size) + " bytes"
    elif 1000 <= size < 1000000 :
        txt = str(size/1000) + " Ko"
    else :
        txt = str(size/1000000) + " Mo"
    return txt

def listf(data):
	buffer = ""
	for line in data:
		buffer = buffer + line + "\n"
	return buffer
	
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

def smooth(x,window_len=10,window='hanning'):
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

    t=linspace(-2,2,0.1)
    x=sin(t)+randn(len(t))*0.1
    y=smooth(x)

    see also:

    numpy.hanning, numpy.hamming, numpy.bartlett, numpy.blackman, numpy.convolve
    scipy.signal.lfilter

    TODO: the window parameter could be the window itself if an array instead of a string
    """

    if x.ndim != 1:
        raise ValueError("smooth only accepts 1 dimension arrays.")

    if x.size < window_len:
        raise ValueError("Input vector needs to be bigger than window size.")


    if window_len<3:
        return x

    if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
        raise ValueError("Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'")


    s=r_[2*x[0]-x[window_len:1:-1],x,2*x[-1]-x[-1:-window_len:-1]]

    if window == 'flat': #moving average
        w=ones(window_len,'d')
    else:
        w=eval(window+'(window_len)')

    y=convolve(w/w.sum(),[float(val) for val in s],mode='same')
    return y[window_len-1:-window_len+1]

def EnvironmentInfo():
    """
    Returns a string of the systems information.


    **Returns:**

    *  System information string

    **Note:**

    *  from Editra.dev_tool
    """

    info = "---- Notes ----\n"
    info += "Please provide additional information about the crash here \n"
    info += "---- System Information ----\n"
    info += "Operating System: %s\n" % wx.GetOsDescription()
    if sys.platform == 'darwin':
        info += "Mac OSX: %s\n" % platform.mac_ver()[0]
    info += "Python Version: %s\n" % sys.version
    info += "wxPython Version: %s\n" % wx.version()
    info += "wxPython Info: (%s)\n" % ", ".join(wx.PlatformInfo)
    info += "Python Encoding: Default=%s  File=%s\n" % \
                (sys.getdefaultencoding(), sys.getfilesystemencoding())
    info += "wxPython Encoding: %s\n" % wx.GetDefaultPyEncoding() if wx.VERSION_STRING < '4.0' else str(wx.Font.GetDefaultEncoding())
    info += "System Architecture: %s %s\n" % (platform.architecture()[0], \
                                                platform.machine())
    info += "Byte order: %s\n" % sys.byteorder
    info += "Frozen: %s\n" % str(getattr(sys, 'frozen', 'False'))
    info += "---- End System Information ----"

    return info
