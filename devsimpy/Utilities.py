# -*- coding: utf-8 -*- # noqa: UP009

'''
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
'''

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
from tempfile import gettempdir
import pathlib
import types
import inspect
from functools import lru_cache

if not hasattr(inspect, 'getargspec'):
    inspect.getargspec = inspect.getfullargspec
    
from datetime import datetime  

import gettext
_ = gettext.gettext

from zipfile import ZipFile, ZIP_DEFLATED  


if getattr(builtins,'GUI_FLAG', True):
	import wx
	
	_ = wx.GetTranslation

	import wx.adv
	wx.Sound = wx.adv.Sound
	wx.SOUND_ASYNC = wx.adv.SOUND_ASYNC	

	try:
		from agw import pybusyinfo as PBI # type: ignore  
	except ImportError: # if it's not there locally, try the wxPython lib.
		import wx.lib.agw.pybusyinfo as PBI

	from pubsub import pub
	
	@lru_cache(maxsize=128)
	def load_and_resize_image(filename, width=16, height=16):
		"""Charge une image et la redimensionne à width x height"""
		image_path = os.path.join(ICON_PATH, filename) # type: ignore

		if not os.path.isfile(image_path):
			raise FileNotFoundError(f"File not found: {image_path}")

		bitmap = wx.Bitmap(image_path)
		if not bitmap.IsOk():  # vérification essentielle sur macOS
			raise RuntimeError(f"Failed to load bitmap: {image_path}")

		image = bitmap.ConvertToImage()
		image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
		return wx.Bitmap(image)
		
else:
	def load_and_resize_image(filename, width=16, height=16):
		pass

### for replaceAll
import fileinput  

# Used to recurse subdirectories
import fnmatch
import urllib.request, urllib.parse, urllib.error, urllib.request, urllib.error, urllib.parse, http.client
from urllib.request import urlretrieve
	
import pip
import importlib

from subprocess import check_call, Popen, PIPE

from importlib.metadata import version, PackageNotFoundError

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

import tomllib  
from pathlib import Path

#-------------------------------------------------------------------------------

def get_version():
    """Récupère la version du package depuis pyproject.toml ou via importlib.metadata."""
    try:
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        if pyproject_path.exists():
            with pyproject_path.open("rb") as f:
                pyproject_data = tomllib.load(f)
            return pyproject_data["project"]["version"]
    except FileNotFoundError:
        pass
    except Exception as e:  # noqa: BLE001
        print(f"Warning: Could not retrieve version from pyproject.toml. {e}")
    
    # Fallback to importlib.metadata
    try:
        return version("devsimpy")
    except PackageNotFoundError:
        return "unknown"


def getFilePathInfo(path):
	""" File Path
	"""
	assert os.path.isabs(path)

	dirname = os.path.dirname(path)
	basename = os.path.basename(path)
	info = os.path.splitext(basename)
	filename = info[0]
	extend = info[1][1:]

	return dirname, basename, filename, extend

def printOnStatusBar(statusbar, data={}):  # noqa: B006
	""" Send data on status bar
	"""
	for k,v in list(data.items()):
		statusbar.SetStatusText(v, k)

def NotificationMessage(title, message, parent, flag=2048, timeout=False):
	""" 2048 is wx.ICON_INFORMATION
	"""
	if NOTIFICATION: # type: ignore
		
		notify = wx.adv.NotificationMessage(
		title=title,
		message=message,
		parent=parent, flags=flag)

		if timeout:
			wx.CallAfter(notify.Show,timeout=timeout) # 1 for short timeout, 100 for long timeout
		else:
			wx.CallAfter(notify.Show)

def now()->str:
    """ Returns the current time formatted. """

    t = time.localtime(time.time())
    st = time.strftime("%d %B %Y @ %H:%M:%S", t)

    return st

def module_list(topdir:str)->[str]: # type: ignore
	for root,_,files in os.walk(topdir):
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

	def SetSize(self, size):
		""" Change the maximum size of the list and drop the oldest elements if needed.
		"""
		### NB: do not use the builtin max() here, it is shadowed by numpy in this module
		try:
			new_size = int(size)
		except (TypeError, ValueError):
			return

		### the size must be at least 1
		new_size = builtins.max(new_size, 1)

		self.__size = new_size

		### truncate the oldest elements when the new size is smaller
		while len(self) > self.__size:
			del self[0]

	def is_empty(self):
		""" Return True if the list is empty.
		"""
		return len(self) == 0

	def top(self):
		""" Return the last inserted element without removing it (None if empty).
		"""
		return self[-1] if self else None

	def append(self, v):
		if len(self) >= self.GetSize():
			del self[0]

		self.insert(len(self),v)

def getOutDir():
	""" Out Dir
	"""
	out_dir = os.path.join(DEVSIMPY_PACKAGE_PATH, 'out') # type: ignore
	if not os.path.exists(out_dir):
		os.mkdir(out_dir)
	return out_dir

def PyBuzyInfo(msg, time):
	""" Buzy Info
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
	except Exception as e:  # noqa: BLE001
		print(e)
		return False
	else:
		return True

def updatePiP():
	""" Update Pip
	"""

	if check_internet():	
		try:
			command = "python -m pip install --upgrade pip"
			run_command(command, "to_progress_diag")
		except Exception as ee:  # noqa: BLE001
			print(ee.output)
			return False
		else:
			return True
	else:
		return False

def downloadFromURL(url):
	""" Dowload From URL
	"""
	
	try:
		# downloading with request
		# download the file contents in binary format
		pub.sendMessage("to_progress_diag", message=_(f"Download git archive from:\n{url}"))  # noqa: INT001
		r = urllib.request.urlopen(url)
	except Exception as e:  # noqa: BLE001
		print(e)
		return None
	else:
		if r.getcode() == 200:
		# 200 means a successful request
			tempdir = os.path.realpath(gettempdir())
			fn = os.path.join(tempdir, "DEVSimPy.zip")
			# downloading with urllib
			# Copy a network object to a local file
			pub.sendMessage("to_progress_diag", message=_(f"Copy a network object to:\n{fn}"))  # noqa: INT001
			urlretrieve(url, fn)
			pub.sendMessage("to_progress_diag", message=_("Copy done!"))
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
	import git # type: ignore  

	try:
		pub.sendMessage("to_progress_diag", message=_("Pull..."))
		repo = git.Repo(DEVSIMPY_PACKAGE_PATH) # type: ignore
		o = repo.remotes.origin
		o.pull()
	except Exception:  # noqa: BLE001
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

		tempdir = os.path.realpath(gettempdir())
		now = datetime.now() # current date and time  # noqa: DTZ005

		try:
			### make a backup of DEVSimPy sources to temp directory with the file DEVSimPy-backup-m_d_y
			pub.sendMessage("to_progress_diag", message=_(f"Backup DEVSimPy in {tempdir} directory..."))  # noqa: INT001
			
			zipf = ZipFile(os.path.join(tempdir,''.join(['DEVSimPy-backup-',now.strftime("%m_%d_%Y"),'.zip'])), 'w', ZIP_DEFLATED)
			zipdir(os.getcwd(), zipf)
			zipf.close()
		except Exception:  # noqa: BLE001
			print('print_exc():')
			traceback.print_exc(file=sys.stdout)
			print('\n')
			print('print_exc(1):')
			traceback.print_exc(limit=1, file=sys.stdout)
			return False
		else:
			pub.sendMessage("to_progress_diag", message=_("Done!"))

		# opening the downloaded zip file in READ mode 
		with ZipFile(fn, 'a') as zip:
			
			# extracting all the files (simulate in order to wait if the user want to stop the process)
			pub.sendMessage("to_progress_diag", message=_("Extracting all the files..."))
			for elem in zip.infolist():
				time.sleep(0.1)
				
				p = pathlib.PurePosixPath(elem.filename)
				pub.sendMessage("to_progress_diag", message=_(f"Extract...\n{p.relative_to('DEVSimPy-master')}"))  # noqa: INT001
			
			### effective extraction in temp directory
			zip.extractall(tempdir)

			### Copy the extracted files into the DEVSimPy folder.
			pub.sendMessage("to_progress_diag", message=_(f"Copy...\n{p.relative_to('DEVSimPy-master')}"))  # noqa: INT001
			try:
				if platform.python_version() >= '3.8':
					shutil.copytree(os.path.join(tempdir, 'DEVSimPy-master'), os.path.join(tempdir, 'test'), dirs_exist_ok=True) 
				else:
					src = pathlib.Path(os.path.join(tempdir, 'DEVSimPy-master'))
					dest = pathlib.Path(os.path.join(tempdir, os.getcwd()))
					copy_dir(src, dest)
			except Exception:  # noqa: BLE001
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
	except:  # noqa: E722
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
		except Exception:  # noqa: BLE001
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
			dial = wx.MessageDialog(None, _(f'We find that the package {package_to_install} is missing. \n\n Do you want to install him using pip?'), _('Package Manager'), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)  # noqa: INT001

			if dial.ShowModal() == wx.ID_YES:
				installed = not pip.main(['install', package_to_install])
			else:
				installed = False

			dial.Destroy()
	else:
		installed = True

	return installed

def getObjectFromString(scriptlet):
	""" Object from String
	"""

	assert scriptlet != ''

	# Compile the scriptlet.
	try:
		code = compile(scriptlet, '<string>', 'exec')
	except Exception as info:  # noqa: BLE001
		return info
	else:
		# Create the new 'temp' module.
		temp = types.ModuleType("temp")
		sys.modules["temp"] = temp

		### there is syntaxe error ?
		try:
			exec(code, temp.__dict__)  # noqa: S102
		except Exception as info:  # noqa: BLE001
			return info

		else:
			classes = inspect.getmembers(temp, callable)
			for name, value in classes:
				if value.__module__ == "temp":
					# Create the instance.
					try:
						return eval(f"temp.{name}")()
					except Exception as info:  # noqa: BLE001
						return info

def vibrate(windowName, distance=15, times=5, speed=0.05, direction='horizontal'):
	""" Speed is the number of seconds between movements
		If times is odd, it increments so that window ends up in same location
	"""

	if times % 2 != 0:
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
	except:  # noqa: E722
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
					b, _=os.path.splitext(file)
					files.append(b)

		### str of __all__ variable extracted from __init__.py file
		f = open(init_path,"r")  # noqa: SIM115
		init_str = "".join([a.replace('\n','\t') for a in f])

		### rewrite __init__.py file with the new basename plugin
		with open(init_path,"w+") as f:
			f.write('__all__ = [\n')
			for n in files:
				if n in init_str:
					f.write(f"'{n}',\n")
			for basename in L[:-1]:
				if basename not in init_str:
					f.write(f"'{basename}',\n")
			if L[-1] not in init_str:
				f.write(f"'{L[-1]}'\n]")
			else:
				f.write("\n]")
	else:
		sys.stderr.write(_(f"__init__.py file doesn't exists in {init_dir_path} directory!"))  # noqa: INT001

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
					b, _=os.path.splitext(file)
					files.append(b)

		### str of __all__ variable extracted from __init__.py file
		f = open(init_path,"r")  # noqa: SIM115
		init_str = "".join([a.replace('\n','\t') for a in f])

		### rewrite __init__.py file with the new basename plugin
		with open(init_path,"w+") as f:
			f.write('__all__ = [\n')
			L = [f for f in files if f not in L and f in init_str]
			f.writelines(f"'{n}',\n" for n in L[:-1])
			f.write(f"'{L[-1]}'\n]")
	else:
		sys.stderr.write(_(f"__init__.py file doesn't exists in {init_dir_path} directory!"))  # noqa: INT001

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

def get_downloads_folder():
    """
    Retourne le chemin du dossier Téléchargements quel que soit le système d'exploitation.
    """
    # Pour Windows
    if os.name == 'nt':
        import winreg
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, 
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
            )
            downloads_path = winreg.QueryValueEx(key, "{374DE290-123F-4565-9164-39C4925E467B}")[0]
            winreg.CloseKey(key)
            return downloads_path
        except OSError:
            return os.path.join(os.path.expanduser('~'), 'Downloads')
    
    # Pour macOS
    elif os.name == 'posix' and os.uname().sysname == 'Darwin':
        return os.path.join(os.path.expanduser('~'), 'Downloads')
    
    # Pour Linux
    elif os.name == 'posix':
        xdg_downloads = os.path.join(os.path.expanduser('~'), 'Downloads')
        
        # Essayer de récupérer le chemin via XDG
        try:
            from xdg import BaseDirectory
            xdg_downloads = BaseDirectory.get_xdg_download_dir()
        except ImportError:
            pass
        
        return xdg_downloads
    
    # Fallback
    return os.path.join(os.path.expanduser('~'), 'Downloads')

def path_to_module(abs_python_filename):
	""" Convert and replace sep to . in abs_python_filename.
	"""

	# delete extention if exist
	abs_python_filename = os.path.splitext(abs_python_filename)[0]

	## si Domain est dans le chemin du module à importer (le fichier .py est dans un sous repertoire du rep Domain)
	if abs_python_filename.startswith(DOMAIN_PATH): # type: ignore
		### if you want Domain in the path (Domain.)
		### dir_name = os.path.basename(DOMAIN_PATH)
		dir_name = os.path.basename(os.path.dirname(DOMAIN_PATH)) # type: ignore
		path = str(abs_python_filename[abs_python_filename.index(dir_name):]).strip('[]').replace(os.sep,'.').replace('/','.')
	else:

		path = os.path.basename(abs_python_filename).replace(os.sep,'.').replace('/','.')

		### Ajout du chemin dans le path pour l'import d'un lib exterieur
		domainPath = os.path.dirname(abs_python_filename)
		if domainPath not in sys.path:
			sys.path.insert(0, domainPath)

		# si commence par . (transfo de /) supprime le
		path = path.removeprefix('.')

	return path

def getInstance(cls, args = {}):  # noqa: B006
	""" Function that return the instance from class and args.
	"""
	
	if inspect.isclass(cls):
		try:
			devs = cls(**args)
		except Exception:  # noqa: BLE001
			sys.stderr.write(_(f"Error in getInstance: {cls} not instanciated with {args!s}.\n"))  # noqa: INT001
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
		raise TypeError('itersubclasses must be called with '  # noqa: UP031
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
			for sub in itersubclasses(sub, _seen):  # noqa: B020
				yield sub

def relpath(path=''):
	### change sep from platform
	from sys import platform
	if platform == "linux" or platform == "linux2" or platform == "darwin":
		return path.replace('\\',os.sep)
	elif platform == "win32":
		return path.replace('/',os.sep)
	
def getTopLevelWindow():
	""" Top Window
	"""
	return wx.GetApp().GetTopWindow()

def GetActiveWindow(event=None):
	""" Active Window
	"""
	aW = None

	for win in wx.GetTopLevelWindows():
		if getattr(win, 'IsActive', lambda:False)():
			aW = win

	if aW is None:
		try:
			child = wx.Window.FindFocus()
			aW = wx.GetTopLevelParent(child)
		except:  # noqa: E722, S110
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
	""" Move
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
	""" Size
	"""
	dir_size = 0
	for (path, dirs, files) in os.walk(str(directory)):
		for file in [a for a in files if a.endswith(('.py', '.amd', '.cmd'))]:
			filename = os.path.join(path, file)
			dir_size += os.path.getsize(filename)
	return dir_size/1000

def exists(site, path):
	""" Exits
	"""
	conn = http.client.HTTPConnection(site)
	conn.request('HEAD', path)
	response = conn.getresponse()
	conn.close()
	return response.status == 200

def checkURL(url):
	""" Check URL
	"""
	class Authentification_Dialog(wx.Dialog):

		def __init__(self, parent, id, title):
			wx.Dialog.__init__(self, parent, id, title, size=(250, 180))


			wx.StaticText(self, -1, 'Login', (10, 20))
			wx.StaticText(self, -1, 'Password', (10, 60))

			self.login = wx.TextCtrl(self, -1, '',  (110, 15), (120, -1))
			self.password = wx.TextCtrl(self, -1, '',  (110, 55), (120, -1), style=wx.TE_PASSWORD)

			# con = wx.Button(self, wx.ID_OK, 'Connect', (10, 120))
			# btn_cancel = wx.Button(self, wx.ID_CANCEL, pos = (120, 120))

			self.Bind(wx.EVT_BUTTON, self.OnConnect, id=wx.ID_OK)

			self.Centre()

		def OnConnect(self, event):
			# login = self.login.GetValue()
			# password = self.password.GetValue()
			event.Skip()

	if url.startswith('https'):
		# req = urllib.request.Request(url)
		password_manager = urllib.request.HTTPPasswordMgrWithDefaultRealm()

		flag = False

		### while login and password is no good
		while(not flag):
			dlg = Authentification_Dialog(None, -1, _(f'Login to {url}'))  # noqa: INT001

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
						# handler = urllib.request.urlopen(req)
						flag = True
						deadLinkFound = True
					except:  # noqa: E722
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
    """ Replace all
    """
    for line in fileinput.input(file, inplace=1):  # noqa: SIM115
        if searchExp in line:
                line = line.replace(searchExp,replaceExp)
        sys.stdout.write(line)

def listf(data):
    """
    Concatenate a list of strings into a single string,
    separated by newlines.

    Args:
        data: A list of strings.

    Returns:
        A string containing the concatenated elements.
    """

    return "\n".join(data)

def RGBToHEX(rgb_tuple):
    """ convert an (R, G, B) tuple to #RRGGBB """

    hexcolor = '#{:02x}{:02x}{:02x}'.format(*rgb_tuple[:-1])
    # that's it! '%02x' means zero-padded, 2-digit hex values
    return hexcolor
    

def HEXToRGB(colorstring):
    """ convert #RRGGBB to an (R, G, B) tuple """
    colorstring = colorstring.strip()
    if colorstring[0] == '#': colorstring = colorstring[1:]
    if len(colorstring) != 6:
        raise ValueError(f"input #{colorstring} is not in #RRGGBB format")
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


def FormatSizeFile(size):
    """ Format Size File
    """
    if 0 <= size <1000 :
        txt = str(size) + " bytes"
    elif 1000 <= size < 1000000 :
        txt = str(size/1000) + " Ko"
    else :
        txt = str(size/1000000) + " Mo"
    return txt

def listf(data):  # noqa: F811
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
    exc.insert(0, f"*** {now()} ***{os.linesep}")
    return "".join(exc)


def generate_plantuml_from_diagram_recursive(diagram, level=0, parent_package=None):
    """
    Generate PlantUML recursively by exploring ContainerBlock's internal shapes.
    ContainerBlock IS a Diagram, so we can call GetShapeList() directly on it.
    """
    indent = "  " * level
    uml_code = []
    
    if level == 0:
        uml_code.append("@startuml")
        uml_code.append("!theme plain")
        uml_code.append("skinparam linetype polyline")
        uml_code.append("")
    
    # Get diagram name
    diagram_name = getattr(diagram, 'name', getattr(diagram, 'label', f'Model_Level_{level}'))
    # safe_name = diagram_name.replace(' ', '_').replace('-', '_')
    
    # Start package
    uml_code.append(f'{indent}package "{diagram_name}" {{')
    uml_code.append("")
    
    blocks = {}
    connections = []
    
    # STEP 1: Collect all blocks
    for shape in diagram.GetShapeList():
        shape_type = shape.__class__.__name__
        
        # Skip connections and port shapes
        if shape_type in ['iPort', 'oPort', 'ConnectionShape']:
            continue
        
        if hasattr(shape, 'label'):
            block_label = shape.label
            block_id = id(shape)
            safe_label = block_label.replace(' ', '_').replace('-', '_')
            
            is_coupled = (shape_type == 'ContainerBlock')
            
            # Extract ports
            input_ports = []
            output_ports = []
            
            try:
                if hasattr(shape, 'input'):
                    inp = shape.input
                    if isinstance(inp, int):
                        input_ports = [f'in{i}' for i in range(inp)] if inp > 0 else []
                    elif isinstance(inp, list):
                        for p in inp:
                            if isinstance(p, dict):
                                input_ports.append(p.get('name', 'in'))
                            elif hasattr(p, 'label'):
                                input_ports.append(p.label)
                            elif isinstance(p, str):
                                input_ports.append(p)
            except:  # noqa: E722, S110
                pass
            
            try:
                if hasattr(shape, 'output'):
                    out = shape.output
                    if isinstance(out, int):
                        output_ports = [f'out{i}' for i in range(out)] if out > 0 else []
                    elif isinstance(out, list):
                        for p in out:
                            if isinstance(p, dict):
                                output_ports.append(p.get('name', 'out'))
                            elif hasattr(p, 'label'):
                                output_ports.append(p.label)
                            elif isinstance(p, str):
                                output_ports.append(p)
            except:  # noqa: E722, S110
                pass
            
            blocks[block_id] = {
                'label': block_label,
                'safe_label': safe_label,
                'type': shape_type,
                'is_coupled': is_coupled,
                'input_ports': input_ports,
                'output_ports': output_ports,
                'shape': shape
            }
    
    # STEP 2: Extract connections
    block_labels = {bid: binfo['safe_label'] for bid, binfo in blocks.items()}
    
    for shape in diagram.GetShapeList():
        if shape.__class__.__name__ == 'ConnectionShape':
            try:
                src_shape = None
                dst_shape = None
                src_port_idx = 0
                dst_port_idx = 0
                
                if hasattr(shape, 'input') and shape.input:  # noqa: SIM102
                    if isinstance(shape.input, tuple) and len(shape.input) >= 2:
                        src_shape = shape.input[0]
                        src_port_idx = shape.input[1]
                
                if hasattr(shape, 'output') and shape.output:  # noqa: SIM102
                    if isinstance(shape.output, tuple) and len(shape.output) >= 2:
                        dst_shape = shape.output[0]
                        dst_port_idx = shape.output[1]
                
                if src_shape and dst_shape:
                    src_id = id(src_shape)
                    dst_id = id(dst_shape)
                    
                    if src_id in block_labels and dst_id in block_labels:
                        src_block = blocks[src_id]
                        dst_block = blocks[dst_id]
                        
                        src_port_name = ''
                        if src_block['output_ports'] and src_port_idx < len(src_block['output_ports']):
                            src_port_name = src_block['output_ports'][src_port_idx]
                        else:
                            src_port_name = f'out{src_port_idx}'
                        
                        dst_port_name = ''
                        if dst_block['input_ports'] and dst_port_idx < len(dst_block['input_ports']):
                            dst_port_name = dst_block['input_ports'][dst_port_idx]
                        else:
                            dst_port_name = f'in{dst_port_idx}'
                        
                        connections.append({
                            'src': block_labels[src_id],
                            'dst': block_labels[dst_id],
                            'src_port': src_port_name,
                            'dst_port': dst_port_name
                        })
            except:  # noqa: E722, S110
                pass
    
    # STEP 3: Generate components
    for block_id, block_info in blocks.items():
        safe_label = block_info['safe_label']
        label = block_info['label']
        
        if block_info['is_coupled']:
            # ContainerBlock IS a Diagram - recurse directly!
            container_shape = block_info['shape']
            
            # print(f"{'  '*level}Recursing into ContainerBlock: {label}")
            
            # Recursive call on the ContainerBlock itself (it's a Diagram)
            internal_uml = generate_plantuml_from_diagram_recursive(
                container_shape,  # Pass the ContainerBlock directly
                level + 1,
                safe_label
            )
            
            # Extract only the package content (remove @startuml/@enduml)
            lines = internal_uml.split('\n')
            for line in lines:
                stripped = line.strip()
                if stripped and not stripped.startswith('@'):
                    uml_code.append(line)
        else:
            # Atomic model
            uml_code.append(f'{indent}  component "{label}" as {safe_label} {{')
            
            for port in block_info['input_ports']:
                uml_code.append(f'{indent}    portin {port}')
            
            for port in block_info['output_ports']:
                uml_code.append(f'{indent}    portout {port}')
            
            uml_code.append(f'{indent}  }}')
        
        uml_code.append('')
    
    # STEP 4: Add connections
    if connections:
        uml_code.append(f'{indent}  \' Connections')
        
        unique_connections = []
        seen = set()
        for conn in connections:
            key = (conn['src'], conn['dst'], conn['src_port'], conn['dst_port'])
            if key not in seen:
                seen.add(key)
                unique_connections.append(conn)
        
        for conn in unique_connections:
            conn_str = f'{indent}  {conn["src"]} --> {conn["dst"]}'
            if conn['src_port'] or conn['dst_port']:
                port_label = f'{conn["src_port"]}→{conn["dst_port"]}' if conn['src_port'] and conn['dst_port'] else (conn['src_port'] or conn['dst_port'])
                conn_str += f' : {port_label}'
            
            uml_code.append(conn_str)
        uml_code.append('')
    
    uml_code.append(f'{indent}}}')
    
    if level == 0:
        uml_code.append("")
        uml_code.append("@enduml")
    
    return '\n'.join(uml_code)

def export_diagram_to_plantuml(diagram, output_path="diagram.puml", detailed=False):
    """
    Export DEVSimPy diagram to PlantUML with recursive exploration.
    
    Args:
        diagram: DEVSimPy Diagram instance
        output_path: Output file path
        detailed: If True, generate class diagram; If False, component diagram
    """
    try:
        if detailed:
            uml_code = generate_detailed_class_diagram_recursive(diagram)
        else:
            uml_code = generate_plantuml_from_diagram_recursive(diagram)
    except Exception as e:  # noqa: BLE001
        print(f"Generation failed: {e}")
        import traceback
        traceback.print_exc()
        uml_code = f"@startuml\nnote \"Error: {e}\" as N1\n@enduml"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(uml_code)
    
    print(f"PlantUML diagram exported to {output_path}")
    return uml_code

def generate_detailed_class_diagram_recursive(diagram, level=0):
    """
    Generate detailed class diagram with REAL inheritance hierarchy.
    Uses Components.GetClass to load classes from pythonpath WITHOUT needing DEVS instantiation.
    """
    import inspect

    import Components
    
    print("\n=== STARTING CLASS DIAGRAM GENERATION ===")
    
    uml_code = []
    
    if level == 0:
        uml_code.append("@startuml")
        uml_code.append("!theme plain")
        uml_code.append("skinparam classAttributeIconSize 0")
        uml_code.append("skinparam class {")
        uml_code.append("  BackgroundColor<<atomic>> LightBlue")
        uml_code.append("  BackgroundColor<<coupled>> LightGreen")
        uml_code.append("  BackgroundColor<<framework>> WhiteSmoke")
        uml_code.append("}")
        uml_code.append("")
    
    all_classes = {}
    
    def collect_blocks(diag, prefix=''):
        """Recursively collect all Block models and their class hierarchies"""
        
        shapes = diag.GetShapeList()
        print(f"\n{prefix}Diagram has {len(shapes)} shapes")
        
        for shape in shapes:
            shape_type = shape.__class__.__name__
            
            if shape_type in ['iPort', 'oPort', 'ConnectionShape']:
                continue
            
            if shape_type not in ['CodeBlock', 'ContainerBlock']:
                continue
            
            label = getattr(shape, 'label', 'Unknown')
            
            print(f"\n  Block: {shape_type} - Label: {label}")
            
            # STRATEGY 1: Try to get pythonpath directly from shape
            python_path = getattr(shape, 'python_path', None)
            if not python_path:
                python_path = getattr(shape, 'pythonpath', None)
            if not python_path:
                python_path = getattr(shape, 'model_path', None)
            if not python_path:
                python_path = getattr(shape, 'modelpath', None)
            
            # STRATEGY 2: If no path on shape, try to get from DEVS model instance
            if not python_path:
                devs_model = getattr(shape, 'model', None)
                if devs_model:
                    python_path = getattr(devs_model, 'pythonpath', None)
                    if python_path:
                        print(f"    -> Got pythonpath from DEVS instance: {python_path}")
            
            if not python_path:
                print("    -> No pythonpath found, skipping")
                continue
            
            print(f"    -> Python path: {python_path}")
            
            # Load the Python class using Components.GetClass
            try:
                python_class = Components.GetClass(python_path)
                
                if python_class is None:
                    print("    -> ERROR: Components.GetClass returned None")
                    continue
                
                if isinstance(python_class, ImportError):
                    print(f"    -> ERROR: ImportError - {python_class}")
                    continue
                
                if isinstance(python_class, tuple):
                    print(f"    -> ERROR: Tuple returned (error) - {python_class}")
                    continue
                
                print(f"    -> SUCCESS: Loaded class {python_class.__name__}")
                
            except Exception as e:  # noqa: BLE001
                print(f"    -> EXCEPTION loading class: {e}")
                import traceback
                traceback.print_exc()
                continue
            
            # Analyze the complete MRO
            try:
                mro = inspect.getmro(python_class)
                print(f"    -> MRO: {[c.__name__ for c in mro]}")
            except Exception as e:  # noqa: BLE001
                print(f"    -> ERROR getting MRO: {e}")
                continue
            
            # Analyze each class in the hierarchy
            for cls in mro:
                class_name = cls.__name__
                
                # Skip object
                if class_name == 'object':
                    continue
                
                # Already processed
                if class_name in all_classes:
                    continue
                
                print(f"      -> Processing class: {class_name}")
                
                # Get module info
                module = cls.__module__
                is_framework = ('DomainInterface' in module or 
                              'Components' in module or 
                              'Domain' in module or
                              'PyPDEVS' in module or
                              'pypdevs' in module.lower())
                
                # Get parent class
                parent_class = None
                mro_list = list(mro)
                cls_index = mro_list.index(cls)
                if cls_index + 1 < len(mro_list):
                    parent = mro_list[cls_index + 1]
                    if parent.__name__ != 'object':
                        parent_class = parent.__name__
                
                # Extract methods defined in THIS class (not inherited)
                methods = []
                for method_name in dir(cls):
                    if method_name.startswith('_'):
                        continue
                    
                    if method_name in cls.__dict__:
                        attr = getattr(cls, method_name)
                        if callable(attr):
                            try:
                                sig = inspect.signature(attr)
                                params = str(sig).replace('self, ', '').replace('self', '').replace('()', '')
                                if params:
                                    methods.append(f"{method_name}({params})")
                                else:
                                    methods.append(f"{method_name}()")
                            except:  # noqa: E722
                                methods.append(f"{method_name}()")
                
                # Extract attributes defined in THIS class
                attributes = []
                for attr_name in dir(cls):
                    if attr_name.startswith('_'):
                        continue
                    
                    if attr_name in cls.__dict__:
                        attr = getattr(cls, attr_name)
                        if not callable(attr):
                            attr_type = type(attr).__name__
                            attributes.append((attr_name, attr_type))
                
                # For the main class, get ports
                ports_in = []
                ports_out = []
                
                if cls == python_class:
                    # Try to get ports from class definition
                    if hasattr(cls, 'IPorts'):
                        iports = cls.IPorts
                        if isinstance(iports, list):
                            ports_in = [p if isinstance(p, str) else f'in{i}' 
                                       for i, p in enumerate(iports)]
                    
                    if hasattr(cls, 'OPorts'):
                        oports = cls.OPorts
                        if isinstance(oports, list):
                            ports_out = [p if isinstance(p, str) else f'out{i}' 
                                        for i, p in enumerate(oports)]
                    
                    # Fallback to shape ports
                    if not ports_in and hasattr(shape, 'input') and isinstance(shape.input, int):
                        ports_in = [f'in{i}' for i in range(shape.input)] if shape.input > 0 else []
                    
                    if not ports_out and hasattr(shape, 'output') and isinstance(shape.output, int):
                        ports_out = [f'out{i}' for i in range(shape.output)] if shape.output > 0 else []
                
                # Store class info
                all_classes[class_name] = {
                    'class_name': class_name,
                    'parent_class': parent_class,
                    'module': module,
                    'is_framework': is_framework,
                    'is_coupled': shape_type == 'ContainerBlock',
                    'is_abstract': inspect.isabstract(cls),
                    'attributes': attributes[:8],
                    'methods': methods[:10],
                    'ports_in': ports_in if cls == python_class else [],
                    'ports_out': ports_out if cls == python_class else []
                }
                
                print(f"         -> Added class {class_name} (parent: {parent_class})")
            
            # Recurse into ContainerBlock
            if shape_type == 'ContainerBlock':
                print(f"    -> Recursing into ContainerBlock: {label}")
                nested_blocks = collect_blocks(shape, f"{prefix}  {label}.")
                # Merge nested blocks
                for nested_class, nested_info in nested_blocks.items():
                    if nested_class not in all_classes:
                        all_classes[nested_class] = nested_info
        
        return all_classes
    
    # Collect all classes
    all_classes = collect_blocks(diagram)
    
    print(f"\n=== TOTAL CLASSES FOUND: {len(all_classes)} ===")
    print(f"Classes: {list(all_classes.keys())}")
    
    if level == 0:
        # No classes found
        if not all_classes:
            uml_code.append("note \"No classes found.\\n\\nMake sure blocks have valid pythonpath,\\nor run 'Check' to instantiate DEVS models.\" as N1")
            uml_code.append("")
            uml_code.append("@enduml")
            return '\n'.join(uml_code)
        
        # Separate framework and user classes
        framework_classes = {k: v for k, v in all_classes.items() if v['is_framework']}
        user_classes = {k: v for k, v in all_classes.items() if not v['is_framework']}
        
        print(f"Framework classes: {len(framework_classes)}")
        print(f"User classes: {len(user_classes)}")
        
        # Generate framework package
        if framework_classes:
            uml_code.append("package \"DEVS Framework\" {")
            uml_code.append("")
            
            for class_name in sorted(framework_classes.keys()):
                info = framework_classes[class_name]
                
                class_keyword = "abstract class" if info['is_abstract'] else "class"
                uml_code.append(f"  {class_keyword} {class_name} <<framework>> {{")
                
                if info['module']:
                    uml_code.append(f"    ' {info['module']}")
                
                # Attributes
                if info['attributes']:
                    for attr_name, attr_type in info['attributes'][:4]:
                        uml_code.append(f"    # {attr_name} : {attr_type}")
                    if info['methods']:
                        uml_code.append("    --")
                
                # Methods
                for method in info['methods'][:8]:
                    uml_code.append(f"    + {method}")
                
                uml_code.append("  }")
                uml_code.append("")
            
            uml_code.append("}")
            uml_code.append("")
        
        # Generate user classes package
        if user_classes:
            uml_code.append("package \"User Models\" {")
            uml_code.append("")
            
            for class_name in sorted(user_classes.keys()):
                info = user_classes[class_name]
                
                stereotype = "coupled" if info['is_coupled'] else "atomic"
                uml_code.append(f"  class {class_name} <<{stereotype}>> {{")
                
                if info['module'] and info['module'] != '__main__':
                    uml_code.append(f"    ' {info['module']}")
                
                # Attributes
                if info['attributes']:
                    for attr_name, attr_type in info['attributes']:
                        uml_code.append(f"    - {attr_name} : {attr_type}")
                
                # Ports
                if info['ports_in'] or info['ports_out']:
                    uml_code.append("    --")
                    for port in info['ports_in']:
                        uml_code.append(f"    + {port} : InputPort")
                    for port in info['ports_out']:
                        uml_code.append(f"    + {port} : OutputPort")
                
                # Methods
                if info['methods']:
                    uml_code.append("    --")
                    for method in info['methods']:
                        uml_code.append(f"    + {method}")
                
                uml_code.append("  }")
                uml_code.append("")
            
            uml_code.append("}")
            uml_code.append("")
        
        # Generate inheritance relationships
        uml_code.append("' Inheritance relationships")
        for class_name, info in all_classes.items():
            if info['parent_class']:
                uml_code.append(f"{info['parent_class']} <|-- {class_name}")
        
        uml_code.append("")
        uml_code.append("@enduml")
    
    return '\n'.join(uml_code)

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


    s=[2*x[0]-x[window_len:1:-1],x,2*x[-1]-x[-1:-window_len:-1]]

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
    info += f"Operating System: {wx.GetOsDescription()}\n"
    if sys.platform == 'darwin':
        info += f"Mac OSX: {platform.mac_ver()[0]}\n"
    info += f"Python Version: {sys.version}\n"
    info += f"wxPython Version: {wx.version()}\n"
    info += "wxPython Info: ({})\n".format(", ".join(wx.PlatformInfo))
    info += f"Python Encoding: Default={sys.getdefaultencoding()}  File={sys.getfilesystemencoding()}\n"
    info += f"wxPython Encoding: {wx.Font.GetDefaultEncoding()!s}\n"
    info += f"System Architecture: {platform.architecture()[0]} {platform.machine()}\n"
    info += f"Byte order: {sys.byteorder}\n"
    info += "Frozen: {}\n".format(str(getattr(sys, 'frozen', 'False')))
    info += "---- End System Information ----"

    return info
