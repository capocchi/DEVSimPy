# -*- coding: utf-8 -*-

"""
	Authors: T. Ville (tim.ville@me.com)
	Date: 13/02/2013
	Description:
	Depends: behave, wx, devsimpy
"""


### ------------------------------------------------------------------------------------------- ###
# ===========================================Imports============================================= #
### ------------------------------------------------------------------------------------------- ###


# Common imports
import __builtin__
import sys
import os
import threading
import Queue
import subprocess
import time
import re
import zipfile
from tempfile import gettempdir
import copy
try:
	import cPickle as pickle
except:
	import pickle

### Graphical imports
import wx
import wx.py

_ = wx.GetTranslation

# imports from DEVSimPY directory
# if current directory is plugins
if not os.path.basename(os.getcwd()).lower() == 'version-2.8':
	sys.path.append(os.path.dirname(os.getcwd()))
else:
	sys.path.append(os.getcwd())

if __name__ == "__main__":
	__builtin__.__dict__['GUI_FLAG'] = True

import pluginmanager
from Container import Block, ConnectionShape, Testable
import Editor
from DetachedFrame import DetachedFrame
import ZipManager
from DEVSKernel.PyDEVS.DEVS import AtomicDEVS


### ------------------------------------------------------------------------------------------- ###
# ========================================Globals vars=========================================== #
### ------------------------------------------------------------------------------------------- ###


block = None
color = wx.BLACK


### ------------------------------------------------------------------------------------------- ###
# =======================================Utility  Methods======================================== #
### ------------------------------------------------------------------------------------------- ###


# NOTE: AgileDEVS.py :: behaveIsInstalled 	=> Assert that Behave module is installed
def behaveIsInstalled():
		try:
			import behave
			flag = True
		except ImportError:
			flag = False

		return flag


# NOTE: AgileDEVS.py :: getCurrentBlock	=> return the current model activated
def getCurrentBlock():
	global block
	return block


# NOTE: AgileDEVS.py :: GetStateColor		=> return the appropriate color
def getStateColor():
	global color
	return color


# NOTE: AgileDEVS.py :: GetFlatModelDict	=> return a <label,model> dictionnary of the selected diagram
def GetFlatModelDict(coupled_devs, d=None):
	""" Get the flat list of devs model composing coupled_devs (recursively)
	"""
	if not d: d = dict()
	for devs in coupled_devs.componentSet:
		if isinstance(devs, AtomicDEVS):
			model = Model(amd=devs)
			d[model.label] = model
		elif isinstance(devs, CoupledDEVS):
			d[devs.getBlockModel().label] = devs
			GetFlatModelDict(devs,l)
	return d


### ------------------------------------------------------------------------------------------- ###
# =======================================Plugins  methods======================================== #
### ------------------------------------------------------------------------------------------- ###


# NOTE: BddTest.py :: start_test 			=> first launched method on testing
@pluginmanager.register("START_TEST")
def start_test(**kwargs):
	global frame

	parent = kwargs['parent']

	mainW = wx.GetApp().GetTopWindow()
	nb = mainW.nb2
	diagram = nb.GetPage(nb.GetSelection()).diagram

	### plugin main frame instanciation
	frame = TestFrame(parent, wx.ID_ANY, _('Behave Testing Shell for %s ' % os.path.basename(diagram.last_name_saved)))
	frame.UpdateModels()

	### disable suspend and log button
	parent._btn3.Disable()
	parent._btn4.Disable()


# NOTE: BddTest.py :: test_manager 		=> launched method for simulation testing
@pluginmanager.register("SIM_TEST")
def test_manager(**kwargs):
	global frame
	global color
	global block

	model = kwargs['model']
	msg = kwargs['msg']

	### if frame is deleted (occur for dynamic coupled model)
	if not isinstance(frame, wx.Frame):
		return

	### DEVSimPy block
	if hasattr(model, 'getBlockModel'):

		block = model.getBlockModel()

		main = wx.GetApp().GetTopWindow()
		nb2 = main.nb2
		child = main.GetChildren()

		canvas = None

		### find CodeBlock in the nb2
		for can in nb2.pages:
			if block in filter(lambda a: not isinstance(a, ConnectionShape), can.diagram.shapes):
				canvas = can
				break

		### find CodeBlock in detached_frame
		if canvas is None:
			for detached_frame in filter(lambda child: isinstance(child, DetachedFrame) and hasattr(child, 'canvas'), child):
				can = detached_frame.canvas
				if block in filter(lambda a: not isinstance(a, ConnectionShape), can.diagram.shapes):
					canvas = can
					break

		if canvas is not None and isinstance(frame, wx.Frame):

			### ta checking
			if msg[0] is 0:
				color = wx.GREEN
			### internal transition
			elif msg[0] is 1:
				color = wx.BLUE
			### external transition
			elif type(msg[0]) == type({}):
				color = wx.RED

			else:
				color = wx.BLACK

			try:
			### step engine
				frame.flag = False
				while not frame.flag:
					pass
			except:
				pass

			color = wx.BLACK


### ------------------------------------------------------------------------------------------- ###
# =======================================Graphical  tools======================================== #
### ------------------------------------------------------------------------------------------- ###


# NOTE: TestFrame :: Main frame for testing
class TestFrame(wx.Frame):
	"""docstring for TestFrame"""
	def __init__(self, *args, **kwargs):

		kwargs["style"] = wx.DEFAULT_FRAME_STYLE
		kwargs["size"] = (1220, 750)

		super(TestFrame, self).__init__(*args, **kwargs)

		if behaveIsInstalled():
			self.models = dict()
			self.tags = list()
			self.ConfigGUI()
			self.Center()
			self.Show()
			self.attrs_to_del = ["myInput", "myOutput", "parent", "IPorts", "OPorts", "singleton"]
			self.SetMinSize(kwargs["size"])
		else:
			self.Destroy()

	# NOTE: TestFrame :: __str__		=> String representation of the class
	@classmethod
	def __str__(cls):
		pass

	# NOTE: TestFrame :: ConfigGUI		=> Configure the user interface
	def ConfigGUI(self):

		### Menu bar config------------------------------------------------------------------------
		menubar = wx.MenuBar()

		### File menu----------------------------------------------------------
		file_menu = wx.Menu()
		leave = wx.MenuItem(file_menu, wx.NewId(), _('&Quit\tCtrl+Q'), _('Quit the application'))
		file_menu.AppendItem(leave)
		### -------------------------------------------------------------------

		### Edition menu-------------------------------------------------------
		edition = wx.Menu()
		edit = wx.MenuItem(edition, wx.NewId(), _('&Edit\tCtrl+E'), _('Edit tests'))
		env = wx.MenuItem(edition, wx.NewId(), _('&Env\tCtrl+G'), _('Edit general environment'))
		selAllModel = wx.MenuItem(edition, wx.NewId(), _('&Select models\tCTRL+A'), _('Select all models'))
		deselAllModel = wx.MenuItem(edition, wx.NewId(), _('&Deselect models\tCTRL+D', _('Deselect all models')))
		edition.AppendItem(edit)
		edition.AppendItem(env)
		edition.AppendSeparator()
		edition.AppendItem(selAllModel)
		edition.AppendItem(deselAllModel)
		### -------------------------------------------------------------------

		### Behave menu--------------------------------------------------------
		behave = wx.Menu()
		run = wx.MenuItem(behave, wx.NewId(), _('&Run\tCtrl+R'), _('Run test on current model'))
		behave.AppendItem(run)
		### -------------------------------------------------------------------

		### Simulation menu----------------------------------------------------
		simulation = wx.Menu()
		forward = wx.MenuItem(simulation, wx.NewId(), _('&Forward\tCTRL+F'), _('Go to the next model activation'))
		terminate = wx.MenuItem(simulation, wx.NewId(), _('&Terminate\tCTRL+T'), _('Terminate the simulation without quit the test frame'))
		simulation.AppendItem(forward)
		simulation.AppendItem(terminate)
		### -------------------------------------------------------------------

		### Help menu----------------------------------------------------------
		help = wx.Menu()
		helper = wx.MenuItem(help, wx.NewId(), _('&Help\tCtrl+H'), _('Show help'))
		help.AppendItem(helper)
		### -------------------------------------------------------------------

		menubar.Append(file_menu, _('&File'))
		menubar.Append(edition, _('&Edition'))
		menubar.Append(behave, _('&Behave'))
		menubar.Append(simulation, _('&Simulation'))
		menubar.Append(help, _('&Help'))

		self.SetMenuBar(menubar)
		### ---------------------------------------------------------------------------------------
		#=========================================================================================#
		### Panel config---------------------------------------------------------------------------

		self.panel = wx.Panel(self)

		### Left-side of panel------------------------------------------------
		side_size = 175

		### Top :: Model viewer to check-------------------
		self.checkLBAMD = wx.CheckListBox(self.panel, wx.ID_ANY, size=(side_size, -1), choices=self.models.keys())
		### -----------------------------------------------

		### Middle :: Tags viewer to check-----------------
		self.checkLBTags = wx.CheckListBox(self.panel, wx.ID_ANY, size=(side_size, -1), choices=self.tags)
		### -----------------------------------------------

		### ------------------------------------------------------------------

		### Middle of panel---------------------------------------------------
		### Top :: Testing shell---------------------------

		self.shell = wx.py.shell.Shell(self.panel, InterpClass=Interpretor, style=wx.EXPAND)

		### -----------------------------------------------
		### ------------------------------------------------------------------

		### Right-side of panel-----------------------------------------------

		### Top :: Log frame-------------------------------
		logFrame_title = wx.StaticText(self.panel, wx.ID_ANY, 'Log Frame')
		self.logFrame = wx.TextCtrl(self.panel, wx.NewId(), size=(side_size, -1), style=wx.TE_MULTILINE | wx.TE_RICH2)
		self.logFrame.SetEditable(False)
		### -----------------------------------------------

		### ------------------------------------------------------------------

		### Bottom :: Tag info------------------------------------------------
		files = wx.StaticText(self.panel, wx.ID_ANY, 'Tag files : ')
		self.tag_files = wx.StaticText(self.panel, wx.ID_ANY, '')
		### ------------------------------------------------------------------

		### Organize----------------------------------------------------------

		### Left-side of panel-----------------------------
		left_vbox = wx.BoxSizer(wx.VERTICAL)

		left_vbox.Add(self.checkLBAMD, proportion=1, flag=wx.EXPAND | wx.TOP)
		left_vbox.Add(self.checkLBTags, proportion=1, flag=wx.EXPAND)

		### -----------------------------------------------

		### Right-side of panel----------------------------
		log_box = wx.BoxSizer(wx.VERTICAL)
		log_box.Add(logFrame_title, flag=wx.ALIGN_CENTER_HORIZONTAL)
		log_box.Add((-1, 5))
		log_box.Add(self.logFrame, flag=wx.EXPAND | wx.ALL, proportion=1)
		### -----------------------------------------------

		### Global frame-----------------------------------
		hbox = wx.BoxSizer(wx.HORIZONTAL)
		hbox.Add(left_vbox, flag=wx.LEFT | wx.EXPAND, border=2)
		hbox.Add((5, -1))
		hbox.Add(self.shell, flag=wx.EXPAND | wx.ALL, proportion=1)
		hbox.Add((5, -1))
		hbox.Add(log_box, flag=wx.EXPAND | wx.RIGHT)
		### -----------------------------------------------

		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.Add((-1, 2))
		vbox.Add(hbox, flag=wx.EXPAND | wx.ALL, proportion=1)
		vbox.Add((-1, 3))

		files_hbox = wx.BoxSizer(wx.HORIZONTAL)
		files_hbox.Add(files, flag=wx.LEFT, border=5)
		files_hbox.Add(self.tag_files, flag=wx.RIGHT, border=5)
		vbox.Add(files_hbox, flag=wx.BOTTOM | wx.EXPAND, border=5)

		self.shell.Show()
		self.panel.SetSizer(vbox)
		### ------------------------------------------------------------------
		#=========================================================================================#
		### Binding event--------------------------------------------------------------------------
		self.Bind(wx.EVT_MENU, self.OnClose, leave)

		self.Bind(wx.EVT_MENU, self.OnEditTests, edit)
		self.Bind(wx.EVT_MENU, self.OnEditEnv, env)
		self.Bind(wx.EVT_MENU, self.OnSelectAllModels, selAllModel)
		self.Bind(wx.EVT_MENU, self.OnDeselectAllModels, deselAllModel)

		self.Bind(wx.EVT_MENU, self.OnRun, run)

		self.Bind(wx.EVT_MENU, self.OnForward, forward)
		self.Bind(wx.EVT_MENU, self.OnTerminate, terminate)

		self.Bind(wx.EVT_MENU, self.OnAbout, helper)

		wx.EVT_LISTBOX(self, self.checkLBTags.GetId(), self.OnTagSelect)
		wx.EVT_CHECKLISTBOX(self, self.checkLBAMD.GetId(), self.OnModelCheck)
		### ---------------------------------------------------------------------------------------
		#=========================================================================================#
		### Shortcuts construction-----------------------------------------------------------------
		accel_tbl = wx.AcceleratorTable([(wx.ACCEL_CTRL, ord('r'), run.GetId()),
										 (wx.ACCEL_CTRL, ord('h'), helper.GetId()),
										 (wx.ACCEL_CTRL, ord('f'), forward.GetId()),
										 (wx.ACCEL_CTRL, ord('t'), terminate.GetId()),
										 (wx.ACCEL_CTRL, ord('e'), edit.GetId()),
										 (wx.ACCEL_CTRL, ord('g'), env.GetId()),
										 (wx.ACCEL_CTRL, ord('a'), selAllModel.GetId()),
										 (wx.ACCEL_CTRL, ord('d'), deselAllModel.GetId())])
		self.SetAcceleratorTable(accel_tbl)
		### ---------------------------------------------------------------------------------------

	# NOTE: TestFrame :: UpdateModels	=> Refresh the models list
	def UpdateModels(self):
		mainW = wx.GetApp().GetTopWindow()
		nb = mainW.nb2
		diagram = nb.GetPage(nb.GetSelection()).diagram
		master = diagram.getDEVSModel()

		self.models = GetFlatModelDict(master, self.models)
		self.checkLBAMD.Set(self.models.keys())

	# NOTE: TestFrame :: SetTagsList	=> Set the list of tags on the left-side of panel
	def SetTagsList(self, tags=None):
		if not tags: tags = list()
		self.tags = tags
		self.checkLBTags.Set(self.tags)

	# NOTE: TestFrame :: GetCurrentModel
	def GetCurrentModel(self):
		for i in xrange(self.checkLBAMD.GetCount()):
			if self.checkLBAMD.IsSelected(i):
				return self.models[self.checkLBAMD.GetString(i)]

	# NOTE: TestFrame :: GetCheckedModels
	def GetCheckedModels(self):
		models = []
		for i in xrange(self.checkLBAMD.GetCount()):
			if self.checkLBAMD.IsChecked(i):
				models.append(self.models[self.checkLBAMD.GetString(i)])
		return models

	# NOTE: TestFrame :: GetCheckedTags
	def GetCheckedTags(self):
		tags = []
		for i in xrange(self.checkLBTags.GetCount()):
			if self.checkLBTags.IsChecked(i):
				tags.append(self.checkLBTags.GetString(i))
		return tags

	# NOTE: TestFrame :: FileTagSearch		=> Search files where tags are
	def FileTagSearch(self, tag):
		files = []
		for m in self.GetCheckedModels():
			if tag in m.tags:
				files.append(m.label)
		return files

	# NOTE: TestFrame :: SerializeAllModels	=> note
	def SerializeModel(self, model):
		amd = copy.deepcopy(model.amd)

		for attr in self.attrs_to_del:
			if hasattr(amd, attr):
				delattr(amd, attr)

		serial = os.path.join(gettempdir(), "AtomicModel_%s.serial" % model.label)
		pickle.dump(amd, open(serial, "wb"))

	# NOTE: TestFrame :: TagsFormatter		=> Format tags for command
	def TagsConfig(self, tags=None):
		return (','.join(tags) if tags else '')

	# NOTE: TestFrame :: CommandConfig		=> Configure the behave command
	def CommandConfig(self, feature):
		checkedTags = self.GetCheckedTags()
		return ["behave %s" % feature, "behave --tags %s %s" % (self.TagsConfig(checkedTags), feature)][checkedTags is []]

	### Events-------------------------------------------------------------------------------------

	# NOTE: TestFrame :: OnAbout			=> note
	def OnAbout(self, event):
		wx.MessageBox('Not implemented yet...', 'Info', wx.OK | wx.ICON_INFORMATION)

	# NOTE: TestFrame :: OnClose			=> Event when Quit button os clicked
	def OnClose(self, event):

		### Remove temporary tests files
		Testable.RemoveTempTests()

		self.GetParent().OnStop(event)
		self.Close()
		event.Skip()

	# NOTE: TestFrame :: OnEditTests 		=> Open TestEditor with current model tests
	def OnEditTests(self, event):
		self.GetCurrentModel().block.OnTestEditor(event)

	# NOTE: TestFrame :: OnEditEnv			=> Open TestEditor for general environment file
	def OnEditEnv(self, event):
		### Retrieve environment file--------------------------------------------------------------
		env_path = os.path.join(gettempdir(), 'environment.py')
		if os.path.exists(env_path):
			env = env_path
		else:
			env = Testable.CreateEnv(gettempdir())
		### ---------------------------------------------------------------------------------------

		mainW = wx.GetApp().GetTopWindow()
		### Editor instanciation and configuration---------------------
		editorFrame = Editor.GetEditor(
				mainW,
				wx.ID_ANY,
				'enviroment.py',
				file_type="test"
				)
		editorFrame.AddEditPage('General environment', env)
		editorFrame.Show()

	# NOTE: TestFrame :: OnModelCheck
	def OnModelCheck(self, event):
		temp_tags = []
		tags = []

		checked_models = self.GetCheckedModels()

		for model in checked_models:
			[temp_tags.append(tag) for tag in model.tags]

		for tag in temp_tags:
			if not tag in tags:
				tags.append(tag)

		self.SetTagsList(tags)

	# NOTE: TestFrame :: OnTagSelect
	def OnTagSelect(self, event):
		tag = self.checkLBTags.GetStringSelection()
		# self.tag_name.SetLabel(tag)

		tag_files = " :: ".join(self.FileTagSearch(tag))
		self.tag_files.SetLabel(tag_files)

	# NOTE: TestFrame :: OnSelectAllModels		=> note
	def OnSelectAllModels(self, event):
		for i in xrange(self.checkLBAMD.GetCount()):
			self.checkLBAMD.Check(i, True)
		self.OnModelCheck(event)

	# NOTE: TestFrame :: OnDeselectAllModels	=> note
	def OnDeselectAllModels(self, event):
		for i in xrange(self.checkLBAMD.GetCount()):
			self.checkLBAMD.Check(i, False)
		self.OnModelCheck(event)

	# NOTE: TestFrame :: OnForward				=> note
	def OnForward(self, event):
		"""
		"""

		parent = self.GetParent()

		model = getCurrentBlock()

		### Log text construction
		log = ""
		ta = "\n%s ta checking\n" % model.label
		deltInt = "\n%s internal transition\n" % model.label
		deltExt = "\n%s external transition\n" % model.label

		### Log frame update
		if getStateColor() is wx.GREEN:
			log = ta
		elif getStateColor() is wx.BLUE:
			log = deltInt
		elif getStateColor() is wx.RED:
			log = deltExt

		self.logFrame.SetDefaultStyle(wx.TextAttr(getStateColor()))
		self.logFrame.AppendText(log)

		self.flag = True

	# NOTE: TestFrame :: OnTerminate			=> note
	def OnTerminate(self, event):
		self.logFrame.Clear()
		parent = self.GetParent()
		parent.OnStop(event)
		### FIX : OnTerminate method raise windows bad sound

	# NOTE: TestFrame :: OnRun					=> note
	def OnRun(self, event):
		models = self.GetCheckedModels()
		features = []

		global_flag = [False, True][len(models) > 1]

		self.shell.clear()

		for model in models:
			self.SerializeModel(model)

			feat, steps, env = model.block.GetTempTests(global_flag)
			feat = feat[2:]
			self.shell.push(self.CommandConfig(feat))

			Testable.RemoveTempTests()
			[os.remove(os.path.join(gettempdir(), f)) for f in os.listdir(gettempdir()) if re.match('^AtomicModel_.*\.{1}serial$', f)]


### -----------------------------------------------------------------------------------------------
# NOTE: Model :: Model object
class Model(object):
	"""docstring for Model"""
	def __init__(self, *args, **kwargs):
		super(Model, self).__init__()

		if kwargs.has_key('tags'):
			self.tags = kwargs['tags']
		else:
			self.tags = list()
		self.amd = kwargs['amd']
		self.block = self.amd.getBlockModel()
		self.label = self.block.label
		self.SearchTags()

	# NOTE: Model :: SearchTags			=> Search tags of model
	def SearchTags(self):
		model_path = os.path.dirname(self.block.python_path)
		name, ext = os.path.splitext(os.path.basename(self.block.python_path))

		### Zip configuration-------------------------------------------------
		tests_files = ZipManager.Zip.GetTests(model_path)
		feat_name = filter(lambda t: t.endswith(".feature"), tests_files)[0]
		importer = zipfile.ZipFile(model_path, "r")
		featInfo = importer.getinfo(feat_name)
		feat_code = importer.read(featInfo)
		importer.close()
		### ------------------------------------------------------------------

		pattern = re.compile('@[^,\s]*')
		matched = pattern.findall(feat_code)
		matched = [m[1:] for m in matched]

		tags = []

		for tag in matched:
			if not tag in tags:
				tags.append(tag)

		self.tags = tags


### -----------------------------------------------------------------------------------------------
# NOTE: Interpretor :: Shell interpretor
class Interpretor(object):
	"""docstring for Interpretor"""
	def __init__(self, locals, rawin, stdin, stdout, stderr):
		super(Interpretor, self).__init__()
		self.introText = """
#####################################################################################################
#                              *~. Welcome to behave testing console .~*                            #
#####################################################################################################
"""
		self.locals = locals
		self.revision = 1.0
		self.rawin = rawin
		self.stdin = stdin
		self.stdout = stdout
		self.stderr = stderr

		self.more = False

		#bash process
		if os.name == "posix":
			term = "bash"
		else:
			term = "cmd"

		self.bp = subprocess.Popen(term, shell=False, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

		# start output grab thread
		self.outputThread = TermProcessThread(self.bp.stdout.readline)
		self.outputThread.start()

		# start err grab thread
		self.errorThread = TermProcessThread(self.bp.stderr.readline)
		self.errorThread.start()

	# NOTE: Interpretor :: __str__		=> String representation of the class
	@classmethod
	def __str__(cls):
		attrs = [('introText', 'str'), ('locals', 'UNDEFINED'), ('revision', 'float'), ('rawin', 'UNDEFINED'),
		         ('stdin', 'subprocess.PIPE'), ('stdout', 'subprocess.PIPE'), ('stderr', 'subprocess.PIPE')
				]
		class_name = "Interpretor"
		parent = "object"
		methods = [
					('__init__', 'self, locals, rawin, stdin, stdout, stderr'),
					('getAutoCompleteKeys', 'self'),
					('getAutoCompleteList', 'self, *args, **kwargs'),
					('getCallTip', 'self, command'),
					('push', 'self, command')
				]
		return "\n--------------------------------------------------\
		\n\tClass :\t\t%s\n\n\tInherit from :\t%s\n\n\tAttributes :\t%s\n\n\tMethods :\t%s\n"%(
			class_name, parent, '\n\t\t\t'.join([attr + "\t:: " + typ for attr, typ in attrs]), "\n\t\t\t".join([method + "\tparams :: " + params for method, params in methods])
		)

	# NOTE: Interpretor :: getAutoCompleteKeys => Shortcut for autocompletion
	def getAutoCompleteKeys(self):
		return [ord('\t')]

	# NOTE: Interpretor :: getAutoCompleteList => todo
	def getAutoCompleteList(self, *args, **kwargs):
		return []

	# NOTE: Interpretor :: getCallTip 		=> todo
	def getCallTip(self, command):
		return ""

	# NOTE: Interpretor :: push 			=> Push command to shell and get results
	def push(self, command):
		command = command.strip()
		if not command:
			return
		self.bp.stdin.write(command + "\n")
		# wait a bit
		time.sleep(1)

		# print output
		self.stdout.write(self.outputThread.getOutput())

		# print error
		self.stderr.write(self.errorThread.getOutput())
		self.bp.stdin.write("\n")


### -----------------------------------------------------------------------------------------------
# NOTE: TermProcessThread :: Thread to manage terminal
class TermProcessThread(threading.Thread):
	"""docstring for TermProcessThread"""
	def __init__(self, readlineFunc):
		super(TermProcessThread, self).__init__()
		self.readlineFunc = readlineFunc
		self.outputQueue = Queue.Queue()
		self.setDaemon(True)

	# NOTE: TermProcessThread :: __str__		=> String representation of the class
	@classmethod
	def __str__(cls):
		attrs = [('readlineFunc', 'str'), ('outputQueue', 'Queue')]
		class_name = "TermProcessThread"
		parent = "threading.Thread"
		methods = [
					('__init__', 'self, *args, **kwargs'),
					('run', 'self'),
					('getOutput', 'self')
				]
		return "\n--------------------------------------------------\
		\n\tClass :\t\t%s\n\n\tInherit from :\t%s\n\n\tAttributes :\t%s\n\n\tMethods :\t%s\n"%(
			class_name, parent, '\n\t\t\t'.join([attr + "\t:: " + typ for attr, typ in attrs]),
			"\n\t\t\t".join([method + "\tparams :: " + params for method, params in methods])
		)

	def run(self):
		while True:
			line = self.readlineFunc()
			self.outputQueue.put(line)

	def getOutput(self):
		""" called from another thread """
		lines = []
		while True:
			try:
				line = self.outputQueue.get_nowait()
				lines.append(line)
			except Queue.Empty:
				break

		return ''.join(lines)


### ------------------------------------------------------------------------------------------- ###
# =======================================Main Application======================================== #
### ------------------------------------------------------------------------------------------- ###


def start():
	app = wx.App()
	frame = TestFrame(None, -1, 'Testing Shell')
	app.MainLoop()


def info():
	os.system(['clear', 'cls'][os.name == 'nt'])
	print TestFrame.__str__()
	print Interpretor.__str__()
	print TermProcessThread.__str__()


def manager(args):
	if args.start:
		start()
	if args.info:
		info()


def main():
	parser = argparse.ArgumentParser(description='Behave test manager for DEVSimPY application')

	### Class info---------------------------------------------------------------------------------
	parser.add_argument('-c', '--class-info', action="store_true", dest="info", help='Show __str__ for each class')

	### Start App----------------------------------------------------------------------------------
	parser.add_argument('-s', '--start', action="store_true", dest="start", help='Start testing app')

	args = parser.parse_args()
	manager(args)


if __name__ == "__main__":
	try:
		import argparse
		main()
	except ImportError:
		sys.stderr.write("\nTo access to command line utils, please upgrade your python version to 2.7\n")
		start()