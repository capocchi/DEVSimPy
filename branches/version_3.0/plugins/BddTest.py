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
import sys
import os
import threading
import Queue
import subprocess
import time
import re
import zipfile
from tempfile import gettempdir
from types import MethodType
import pickle

### Graphical imports
import wx
import wx.py

_ = wx.GetTranslation

# imports from DEVSimPY directory
# if current directory is plugins
if not os.path.basename(os.getcwd()).lower() == 'devsimpy':
	sys.path.append(os.path.dirname(os.getcwd()))
else:
	sys.path.append(os.getcwd())

import Core.Components.Container as Container
import __builtin__

__builtin__.__dict__['GUI_FLAG'] = True

import Mixins.Testable as Testable
import GUI.Editor as Editor
import GUI.ZipManager as ZipManager
import Core.Patterns.Observer as Observer
import Core.Utilities.pluginmanager as pluginmanager
import GUI.DetachedFrame as DetachedFrame


model = None
color = wx.BLACK

### ------------------------------------------------------------------------------------------- ###
# =======================================Utility  Methods======================================== #
### ------------------------------------------------------------------------------------------- ###


# NOTE: BddTest.py :: behaveIsInstalled 	=> Assert that Behave module is installed
def behaveIsInstalled():
	try:
		import behave

		flag = True
	except ImportError:
		flag = False

	return flag

# NOTE: BddTest.py :: GetState		=> Return state
def GetState(self):
	return self.__state


### ------------------------------------------------------------------------------------------- ###
# =======================================Plugins  methods======================================== #
### ------------------------------------------------------------------------------------------- ###


# NOTE: BddTest.py :: start_test 			=> first launched method on testing
@pluginmanager.register("START_TEST")
def start_test(**kwargs):
	global frame
	global sender
	# global parent

	parent = kwargs['parent']
	# parent.thread.suspend()

	mainW = wx.GetApp().GetTopWindow()
	nb = mainW.nb2
	actual = nb.GetSelection()
	diagram = nb.GetPage(actual).diagram

	frame = TestFrame(parent, wx.ID_ANY, _('Behave Testing Shell for %s ' % os.path.basename(diagram.last_name_saved)))

	# Get shape list from diagram
	shapes_list = [s for s in diagram.GetShapeList() if isinstance(s, Container.Block)]

	frame.SetItems(shapes_list)
	frame.ConstructTree()

	sender = Observer.Subject()
	sender.__state = {}
	sender.canvas = None
	sender.GetState = MethodType(GetState, sender)

	### disable suspend and log button
	parent._btn3.Disable()
	parent._btn4.Disable()


# NOTE: BddTest.py :: test_manager 		=> launched method for simulation testing
@pluginmanager.register("SIM_TEST")
def test_manager(**kwargs):
	global frame
	global model
	global sender
	global color

	model = kwargs['model']
	msg = kwargs['msg']

	### if frame is deleted (occur for dynamic coupled model)
	if not isinstance(frame, wx.Frame):
		return

	### DEVSimPy block
	if hasattr(model, 'getBlockModel'):

		block = model.getBlockModel()

		serial = os.path.join(gettempdir(), "serial")

		pickle.dump(block, open(serial, "wb"))

		main = wx.GetApp().GetTopWindow()
		nb2 = main.nb2
		child = main.GetChildren()

		canvas = None

		### find CodeBlock in the nb2
		for can in nb2.pages:
			if block in filter(lambda a: not isinstance(a, Container.ConnectionShape), can.diagram.shapes):
				canvas = can
				break

		### find CodeBlock in detached_frame
		if canvas is None:
			for detached_frame in filter(
					lambda child: isinstance(child, DetachedFrame.DetachedFrame) and hasattr(child, 'canvas'), child):
				can = detached_frame.canvas
				if block in filter(lambda a: not isinstance(a, Container.ConnectionShape), can.diagram.shapes):
					canvas = can
					break

		sender.canvas = canvas

		if canvas is not None and isinstance(frame, wx.Frame):

			### Add model to observer list
			sender.attach(block)

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
			sender.notify()
			sender.detach(block)


# NOTE: BddTest.py :: getCurrentModel		=> return the current model
def getCurrentModel():
	global model
	return model

# NOTE: BddTest.py :: GetStateColor		=> return the appropriate color
def getStateColor():
	global color
	return color


### ------------------------------------------------------------------------------------------- ###
# =======================================Graphical  tools======================================== #
### ------------------------------------------------------------------------------------------- ###

# NOTE: TestFrame :: Main frame for testing
class TestFrame(wx.Frame):
	"""
	"""

	# NOTE: TestFrame :: constructor 		=> __init__(self, *args, **kwargs)
	def __init__(self, *args, **kwargs):

		kwargs["style"] = wx.DEFAULT_FRAME_STYLE
		kwargs["size"] = (750, 750)

		wx.Frame.__init__(self, *args, **kwargs)

		if behaveIsInstalled():
			self.items = []
			self.selectedItem = None
			self.checkedTags = []
			self.flag = True
			self.previousBlock = None
			self.ConfigGUI()
			self.Center()
			self.Show()
		else:
			sys.exit()

	# NOTE: TestFrame :: __str__		=> String representation of the class
	@classmethod
	def __str__(cls):
		attrs = [('items', 'list<AMD>'), ('selectedItem', 'Block'), ('checkedTags', 'list<str>'), ('panel', 'wx.Panel')]
		class_name = "TestFrame"
		parent = "wx.Frame"
		methods = [
			('__init__', 'self, *args, **kwargs'),
			('ConfigGUI', 'self'),
			('ConstructTree', 'self, items'),
			('GetRootIdTree', 'self'),
			('SetItems', 'self, items'),
			('GetCurrentItem', 'self'),
			('GetTagManager', 'self, blocklist, all'),
			('SetCheckedTags', 'self, tags'),
			('TagsFormatter', 'self, tags'),
			('CommandConfig', 'self, feature'),
			('QuitApplication', 'self, event'),
			('OnEditTests', 'self, event'),
			('OnEditEnv', 'self, event'),
			('OnRun', 'self, event'),
			('DoRun', 'self'),
			('OnRunAll', 'self, event'),
			('DoRunAll', 'self'),
			('OnSelChanged', 'self, event'),
			('OnHelp', 'self, event'),
			('OnForward', 'self, event')
		]
		return "\n--------------------------------------------------\
		\n\tClass :\t\t%s\n\n\tInherit from :\t%s\n\n\tAttributes :\t%s\n\n\tMethods :\t%s\n" % (
		class_name, parent, '\n\t\t\t'.join([attr + "\t:: " + typ for attr, typ in attrs]),
		"\n\t\t\t".join([method + "\tparams :: " + params for method, params in methods])
		)

	# NOTE: TestFrame :: ConfigGUI 			=> Configure the graphical user interface
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
		edit = wx.MenuItem(edition, wx.NewId(), _('&Edit'), _('Edit tests'))
		env = wx.MenuItem(edition, wx.NewId(), _('&Env'), _('Edit general environment'))
		edition.AppendItem(edit)
		edition.AppendItem(env)
		### -------------------------------------------------------------------

		### Behave menu--------------------------------------------------------
		behave = wx.Menu()
		run = wx.MenuItem(behave, wx.NewId(), _('&Run'), _('Run test on current model'))
		runAll = wx.MenuItem(behave, wx.NewId(), _('&Run All Tests'), _('Run test for all models'))
		behave.AppendItem(run)
		behave.AppendItem(runAll)
		### -------------------------------------------------------------------

		### Help menu----------------------------------------------------------
		help = wx.Menu()
		helper = wx.MenuItem(help, wx.NewId(), _('&Help'), _('Show help'))

		help.AppendItem(helper)
		### -------------------------------------------------------------------

		menubar.Append(file_menu, _('&File'))
		menubar.Append(edition, _('&Edition'))
		menubar.Append(behave, _('&Behave'))
		menubar.Append(help, _('&Help'))

		self.SetMenuBar(menubar)
		### ---------------------------------------------------------------------------------------
		#=========================================================================================#
		### Panel config---------------------------------------------------------------------------
		self.panel = wx.Panel(self)

		### Left-side of panel :: TreeViewer for models------------------------
		modelTree = ModelTree(self.panel, size=(170, -1))
		modelTree.rootIdTree = modelTree.AddRoot('Overview')

		self.loggingFrame = wx.TextCtrl(self.panel, wx.NewId(), size=(170, -1), style=wx.TE_MULTILINE)
		self.loggingFrame.SetEditable(False)
		self.loggingFrame.AppendText("\tLog frame\n")
		### -------------------------------------------------------------------

		### Right-side of panel :: Shell Interpretor---------------------------
		shell = wx.py.shell.Shell(self.panel, InterpClass=Interpretor, style=wx.EXPAND)
		### -------------------------------------------------------------------

		### Step by step button------------------------------------------------
		forward = wx.Button(self.panel, wx.ID_ANY, label="Forward")
		### -------------------------------------------------------------------

		### BoxSizer config----------------------------------------------------
		lbox = wx.BoxSizer(wx.VERTICAL)
		vbox = wx.BoxSizer(wx.VERTICAL)
		hbox = wx.BoxSizer(wx.HORIZONTAL)

		lbox.Add(modelTree, flag=wx.TOP | wx.EXPAND, proportion=1)
		lbox.Add(self.loggingFrame, flag=wx.BOTTOM | wx.EXPAND, proportion=1)

		hbox.Add(lbox, flag=wx.LEFT | wx.EXPAND)
		hbox.Add(shell, 1, wx.EXPAND | wx.RIGHT)

		vbox.Add(hbox, flag=wx.EXPAND, proportion=1)
		vbox.Add(forward, flag=wx.ALIGN_CENTER | wx.EXPAND)
		### -------------------------------------------------------------------

		shell.Show()

		self.panel.SetSizer(vbox)
		### ---------------------------------------------------------------------------------------
		#=========================================================================================#
		### Binding event--------------------------------------------------------------------------
		### File menu binding--------------------------------------------------
		self.Bind(wx.EVT_MENU, self.OnClose, id=leave.GetId())
		# self.Bind(wx.EVT_CLOSE, self.QuitApplication)
		### -------------------------------------------------------------------
		### Edition menu binding-----------------------------------------------
		self.Bind(wx.EVT_MENU, self.OnEditTests, id=edit.GetId())
		self.Bind(wx.EVT_MENU, self.OnEditEnv, id=env.GetId())
		### -------------------------------------------------------------------
		### Behave menu binding------------------------------------------------
		self.Bind(wx.EVT_MENU, self.OnRun, id=run.GetId())
		self.Bind(wx.EVT_MENU, self.OnRunAll, id=runAll.GetId())
		### -------------------------------------------------------------------
		### Help menu binding--------------------------------------------------
		self.Bind(wx.EVT_MENU, self.OnHelp, id=helper.GetId())
		### -------------------------------------------------------------------
		self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelChanged, modelTree)
		self.Bind(wx.EVT_BUTTON, self.OnForward, forward)

	### ---------------------------------------------------------------------------------------

	# NOTE: TestFrame :: ConstructTree 		=> Construct well-formed tree
	def ConstructTree(self, items=None):
		if not items:
			label_list = [s.label for s in self.items]
		else:
			label_list = items
		tree = self.panel.GetChildren()[0]
		tree.SetTreeItems(label_list, self.GetRootIdTree(), None)
		tree.ExpandAll()

	# NOTE: TestFrame :: GetRootIdTree 		=> return the root id of the model tree
	def GetRootIdTree(self):
		return self.panel.GetChildren()[0].rootIdTree

	# NOTE: TestFrame :: OnForward		=> Event when forward button is pressed
	def OnForward(self, event):
		"""
		"""

		parent = self.GetParent()
		tree = self.panel.GetChildren()[0]

		### Update previous item text color to default color
		if self.previousBlock:
			tree.SetItemTextColour(self.previousBlock, wx.BLACK)

		item = getCurrentModel().getBlockModel()
		idItem = tree.GetIdItemByLabel(item.label)

		### Log text construction
		log = ""
		ta = "\n%s ta checking\n" % item.label
		deltInt = "\n%s internal transition\n" % item.label
		deltExt = "\n%s external transition\n" % item.label

		### Item text color update
		tree.SetItemTextColour(idItem, getStateColor())
		tree.SelectItem(idItem)

		### Log frame update
		if getStateColor() is wx.GREEN:
			log = ta
		elif getStateColor() is wx.BLUE:
			log = deltInt
		elif getStateColor() is wx.RED:
			log = deltExt

		self.loggingFrame.AppendText(log)

		#### Closing conditions doesn't seems to be good
		# if tree.GetItemText(self.previousBlock) == tree.GetItemText(idItem) and tree.GetItemTextColour(self.previousBlock) == tree.GetItemTextColour(idItem):
		# 	self.Close()
		# 	parent.OnStop(event)

		self.previousBlock = idItem

		self.flag = True

	# NOTE: TestFrame :: QuitApplication		=> Event when Quit button is pressed
	def OnClose(self, event):

		### Remove temporary tests files
		[item.RemoveTempTests() for item in self.items]

		self.GetParent().OnStop(event)
		self.Close()
		event.Skip()

	# NOTE: TestFrame :: OnEditTests 		=> Open TestEditor with current model tests
	def OnEditTests(self, event):
		block = self.GetCurrentItem()
		block.OnTestEditor(event)

	# NOTE: TestFrame :: OnEditEnv		=> Open TestEditor for general environment file
	def OnEditEnv(self, event):
		### Retrieve environment file--------------------------------------------------------------
		env_path = os.path.join(gettempdir(), 'environment.py')
		if os.path.exists(env_path):
			env = env_path
		else:
			env = Testable.Testable.CreateEnv(gettempdir())
		### ---------------------------------------------------------------------------------------

		mainW = wx.GetApp().GetTopWindow()
		### Editor instanciation and configuration---------------------
		editorFrame = Editor.GetEditor(
			mainW,
			wx.ID_ANY,
			'enviroment.py',
			file_type="test"
		)
		editorFrame.AddEditPage(os.path.basename(env), env)
		editorFrame.Show()

	# NOTE: TestFrame :: OnRun 				=> Run tests for the current model
	def OnRun(self, event):
		# TODO: TestFrame :: OnRun 			=> To code
		tagMan = self.GetTagManager([self.GetCurrentItem()])

	# NOTE: TestFrame :: DoRun		=> Do run action
	def DoRun(self):
		shell = self.panel.GetChildren()[1]
		currentBlock = self.GetCurrentItem()
		feature, steps, env = currentBlock.GetTempTests()
		feature = feature[2:]
		shell.clear()
		shell.push(self.CommandConfig(feature))

	# NOTE: TestFrame :: OnRunAll 			=> Run tests for all models
	def OnRunAll(self, event):
		# TODO: TestFrame :: OnRunAll 		=> To code
		tagMan = self.GetTagManager(self.items, True)

	# NOTE: TestFrame :: DoRunAll		=> Do run action for all models
	def DoRunAll(self, global_env=None):
		if not global_env: global_env = False

		shell = self.panel.GetChildren()[1]

		for item in self.items:
			feature, steps, env = item.GetTempTests(global_env)
			feature = feature[2:]
			shell.clear()
			shell.push(self.CommandConfig(feature))

	# NOTE: TestFrame :: SetItems 			=> Set the list of items
	def SetItems(self, items):
		for item in items:
			if item.isAMD():
				fn = os.path.dirname(item.python_path)
				if ZipManager.Zip.HasTests(fn):
					self.items.append(item)
				else:
					item.CreateTestsFiles()
					self.items.append(item)
			if isinstance(item, list):
				self.SetItems(item)

	# NOTE: TestFrame :: OnSelChanged 		=> When the selection changed in the tree
	def OnSelChanged(self, event):
		item = event.GetItem()
		tree = self.panel.GetChildren()[0]
		if item:
			self.selectedItem = tree.GetItemText(item)
		event.Skip()

	# NOTE: TestFrame :: GetCurrentItem		=> return the selected item as a block
	def GetCurrentItem(self):
		for block in self.items:
			if self.selectedItem == block.label:
				return block

	# NOTE: TestFrame :: GetTagManager		=> note
	def GetTagManager(self, blocklist=None, isRunAll=False):
		if not blocklist:
			blocklist = []
		tags = []
		tags_dict = {}

		for block in blocklist:
			model_path = os.path.dirname(block.python_path)
			name, ext = os.path.splitext(os.path.basename(block.python_path))

			### Zip configuration------------------------------------------
			tests_files = ZipManager.Zip.GetTests(model_path)
			feat_name = filter(lambda t: t.endswith(".feature"), tests_files)[0]
			importer = zipfile.ZipFile(model_path, "r")
			featInfo = importer.getinfo(feat_name)
			feat_code = importer.read(featInfo)
			importer.close()
			### -----------------------------------------------------------

			tags_tmp = BehaveManager.GetTagsList(feat_code)
			for tag in tags_tmp:
				tags.append(tag)
				if not tag in tags_dict.keys():
					tags_dict[tag] = [name]
				else:
					tags_dict[tag].append(name)

		tagMan = TagManager(isRunAll, self, wx.ID_ANY, "Tags Manager")
		tagMan.SetList(tags)
		tagMan.SetTagsDict(tags_dict)
		return tagMan

	# NOTE: TestFrame :: SetCheckedTags		=> MAJ checked tags
	def SetCheckedTags(self, tags=None):
		if not tags:
			tags = []
		self.checkedTags = tags

	# NOTE: TestFrame :: TagsFormatter		=> Format tags for command
	def TagsFormatter(self, tags=None):
		if not tags:
			tags = []
		tagsStr = ','.join(tags)
		return tagsStr

	# NOTE: TestFrame :: CommandConfig		=> Configure the behave command
	def CommandConfig(self, feature):
		# cmdSep = [';', '&'][os.name == 'nt']
		if not self.checkedTags:
			# command = "cd %s %s behave %s" % (os.path.join(gettempdir(), 'features'), cmdSep, feature)
			command = "behave %s" % feature
		else:
			# command = "cd %s %s behave --tags %s %s" % (os.path.join(gettempdir(), 'features'), cmdSep, self.TagsFormatter(self.checkedTags), feature)
			command = "behave --tags %s %s" % (self.TagsFormatter(self.checkedTags), feature)
		return command

	# NOTE: TestFrame :: OnHelp		=> Event when help menu item is clicked
	def OnHelp(self, event):
		help_dialog = HelpDialog(None, title='Help Dialog')
		help_dialog.ShowModal()
		help_dialog.Destroy()


### -----------------------------------------------------------------------------------------------
# NOTE: HelpDialog << wx.Dialog :: Help dialog
class HelpDialog(wx.Dialog):
	""" docstring for HelpDialog """

	# NOTE: HelpDialog :: constructor		=> __init__(self, *args, **kwargs)
	def __init__(self, *args, **kwargs):
		super(HelpDialog, self).__init__(*args, **kwargs)

		self.ConfigGUI()
		self.SetSize((400, 450))
		self.SetTitle('Help')

	# NOTE: HelpDialog :: __str__		=> String representation of the class
	@classmethod
	def __str__(cls):
		attrs = []
		class_name = "HelpDialog"
		parent = "wx.Dialog"
		methods = [
			('__init__', 'self, *args, **kwargs'),
			('ConfigGUI', 'self'),
			('OnClose', 'self, event')
		]
		return "\n--------------------------------------------------\
		\n\tClass :\t\t%s\n\n\tInherit from :\t%s\n\n\tAttributes :\t%s\n\n\tMethods :\t%s\n" % (
		class_name, parent, '\n\t\t\t'.join([attr + "\t:: " + typ for attr, typ in attrs]),
		"\n\t\t\t".join([method + "\tparams :: " + params for method, params in methods])
		)

	# NOTE: HelpDialog :: ConfigGUI		=> GUI configuration
	def ConfigGUI(self):
		panel = wx.Panel(self)
		vbox = wx.BoxSizer(wx.VERTICAL)

		behave_help = wx.HyperlinkCtrl(panel, wx.ID_ANY, 'http://pythonhosted.org/behave/',
									   'http://pythonhosted.org/behave/')
		behave_menu_help = wx.StaticText(panel, wx.ID_ANY,
										 """Run => Run tests for selected model only.
										RunAll => Run tests for all amd models.""")

		tag_man_help = wx.StaticText(panel, wx.ID_ANY,
									 """Tag manager parse your feature files and retrieve all tags.
									You can select which execute by checking."""
		)

		sim_test_help = wx.StaticText(panel, wx.ID_ANY,
									  """The forward button allow you to navigate step by step in simulation.
									Color code is this:
										Green => ta checking
										Blue  => internal transition
										Red   => external transition
										Black => IDLE"""
		)

		info_devs = wx.StaticText(panel, wx.ID_ANY, 'Developpers: T. Ville and SPE teams')
		info_bug = wx.StaticText(panel, wx.ID_ANY, 'Bug reporting: <tim.ville@me.com>')

		bh = wx.StaticBox(panel, label='Behave')
		behave_bhs = wx.StaticBoxSizer(bh, orient=wx.VERTICAL)
		behave_bhs.Add(behave_help, border=5)

		bmh = wx.StaticBox(panel, label='Behave Menu')
		behave_bmhs = wx.StaticBoxSizer(bmh, orient=wx.VERTICAL)
		behave_bmhs.Add(behave_menu_help, border=5)

		tmh = wx.StaticBox(panel, label='Tag Manager')
		tagMan_help = wx.StaticBoxSizer(tmh, orient=wx.VERTICAL)
		tagMan_help.Add(tag_man_help, border=5)

		sth = wx.StaticBox(panel, label='Tag Manager')
		simTest_help = wx.StaticBoxSizer(sth, orient=wx.VERTICAL)
		simTest_help.Add(sim_test_help, border=5)

		db = wx.StaticBox(panel, label='Development')
		devs_bhs = wx.StaticBoxSizer(db, orient=wx.VERTICAL)
		devs_bhs.Add(info_devs, border=5)
		devs_bhs.Add(info_bug, border=5)

		hs = wx.BoxSizer(wx.VERTICAL)
		hs.Add(behave_bhs, flag=wx.ALL | wx.EXPAND | wx.TOP, border=10)
		hs.Add(behave_bmhs, flag=wx.ALL | wx.EXPAND, border=10)
		hs.Add(tagMan_help, flag=wx.ALL | wx.EXPAND | wx.BOTTOM, border=10)
		hs.Add(simTest_help, flag=wx.ALL | wx.EXPAND | wx.BOTTOM, border=10)
		hs.Add(devs_bhs, flag=wx.ALL | wx.EXPAND | wx.BOTTOM, border=10)

		panel.SetSizer(hs)

		closeBtn = wx.Button(self, label="Close")

		vbox.Add(panel, proportion=1, flag=wx.ALL | wx.EXPAND, border=5)
		vbox.Add(closeBtn, flag=wx.ALIGN_CENTER | wx.BOTTOM, border=10)

		self.SetSizer(vbox)

		### Binding------------------------------------------------------------
		closeBtn.Bind(wx.EVT_BUTTON, self.OnClose)

	### -------------------------------------------------------------------

	# NOTE: HelpDialog :: OnClose		=> Event when close button is pressed
	def OnClose(self, event):
		self.Destroy()


### -----------------------------------------------------------------------------------------------
# NOTE: ModelTree :: TreeCtrl for models viewer
class ModelTree(wx.TreeCtrl):
	"""docstring for ModelTree"""

	# NOTE: ModelTree :: contructor 		=> __init__(self, *args, **kwargs)
	def __init__(self, *args, **kwargs):
		super(ModelTree, self).__init__(*args, **kwargs)
		self.rootIdTree = None

		# self.Bind(wx.EVT_TREE_ITEM_MENU, self.OnItemRightClick)

	# NOTE: ModelTree :: __str__		=> String representation of the class
	@classmethod
	def __str__(cls):
		attrs = [('rootIdTree', 'TreeItem')]
		class_name = "ModelTree"
		parent = "wx.TreeCtrl"
		methods = [
			('__init__', 'self, *args, **kwargs'),
			('SetTreeItems', 'self, element, child, firstchild'),
			('GetIdItemByLabel', 'self, label')
		]
		return "\n--------------------------------------------------\
		\n\tClass :\t\t%s\n\n\tInherit from :\t%s\n\n\tAttributes :\t%s\n\n\tMethods :\t%s\n" % (
		class_name, parent, '\n\t\t\t'.join([attr + "\t:: " + typ for attr, typ in attrs]),
		"\n\t\t\t".join([method + "\tparams :: " + params for method, params in methods])
		)

	# NOTE: ModelTree :: SetTreeItems 		=> Fill the tree
	def SetTreeItems(self, element, child, firstChild):
		newchild = child
		for e in element:
			if isinstance(e, list):
				self.SetTreeItems(e, newchild, firstChild)
			else:
				newchild = self.AppendItem(child, e)
				if not firstChild:
					firstChild = newchild

	# NOTE: ModelTree :: GetIdItemByLabel		=> note
	def GetIdItemByLabel(self, label):
		root = self.GetRootItem()
		child, cookie = self.GetFirstChild(root)
		while child.IsOk():
			if self.GetItemText(child) == label:
				return child
			else:
				child, cookie = self.GetNextChild(root, cookie)

			# # NOTE: ModelTree :: OnItemRightClick		=> Event when item right click event occurs
			# def OnItemRightClick(self ,event):
			# 	evtObj = event.GetItem()
			# 	if evtObj.GetParent() is None:
			# 		self.popupMenu = wx.Menu()
			# 		self.popupMenu.Append()


### -----------------------------------------------------------------------------------------------
# NOTE: TagManager << object :: Tag frame management
class TagManager(wx.Frame):
	""" docstring for TagManager """

	# NOTE: TagManager :: constructor		=> __init__(self, *args, **kwargs)
	def __init__(self, isRunAll=False, *args, **kwargs):
		kwargs['size'] = (480, 300)
		wx.Frame.__init__(self, *args, **kwargs)

		self.isRunAll = isRunAll
		self.parent = args[0]
		self.tagsList = []
		self.ConfigGUI()
		self.Center()
		self.Show()

	# NOTE: TagManager :: __str__		=> String representation of the class
	@classmethod
	def __str__(cls):
		attrs = [('isRunAll', 'boolean'), ('parent', 'UNDEFINED'), ('tagsList', 'list<str>'),
				 ('tags_dict', 'dict<str:str>'), ('panel', 'wx.Panel'), ('checkLB', 'wx.CheckListBox'),
				 ('helper', 'wx.StaticText')
		]
		class_name = "TagManager"
		parent = "wx.Frame"
		methods = [
			('__init__', 'self, isRunAll, *args, **kwargs'),
			('ConfigGUI', 'self'),
			('SetList', 'self, tags'),
			('SetTagsDict', 'self, tags_dict'),
			('GetCheckedTags', 'self'),
			('OnTagSelect', 'self, event'),
			('OnOK', 'self, event'),
			('OnClose', 'self, event')
		]
		return "\n--------------------------------------------------\
		\n\tClass :\t\t%s\n\n\tInherit from :\t%s\n\n\tAttributes :\t%s\n\n\tMethods :\t%s\n" % (
		class_name, parent, '\n\t\t\t'.join([attr + "\t:: " + typ for attr, typ in attrs]),
		"\n\t\t\t".join([method + "\tparams :: " + params for method, params in methods])
		)

	# NOTE: TagManager :: ConfigGUI		=> Configure the graphical user interface
	def ConfigGUI(self):
		self.panel = wx.Panel(self)
		sizer = wx.GridBagSizer(5, 4)

		checkLBText = wx.StaticText(self.panel, wx.ID_ANY, 'Tags list :: Check to select wich one to execute')
		self.checkLB = wx.CheckListBox(self.panel, wx.ID_ANY, size=(70, 10), choices=self.tagsList)
		self.helper = wx.StaticText(self.panel, wx.ID_ANY, '')
		self.genEnv = wx.CheckBox(self.panel, wx.ID_ANY, 'General environment file')
		valid = wx.Button(self.panel, wx.ID_ANY, "OK", size=(90, 28))
		close = wx.Button(self.panel, wx.ID_ANY, 'Close', size=(90, 28))

		sizer.Add(checkLBText, pos=(0, 0), flag=wx.TOP | wx.LEFT | wx.BOTTOM, border=5)
		sizer.Add(self.checkLB, pos=(1, 0), span=(1, 5), flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=5)
		sizer.Add(self.helper, pos=(2, 0), flag=wx.LEFT | wx.BOTTOM, border=5)
		sizer.Add(self.genEnv, pos=(3, 0), flag=wx.LEFT, border=5)
		sizer.Add(valid, pos=(4, 3))
		sizer.Add(close, pos=(4, 4), flag=wx.RIGHT | wx.BOTTOM, border=5)

		sizer.AddGrowableCol(1)
		sizer.AddGrowableRow(1)

		self.panel.SetSizer(sizer)

		self.Bind(wx.EVT_BUTTON, self.OnOK, id=valid.GetId())
		self.Bind(wx.EVT_BUTTON, self.OnClose, id=close.GetId())
		wx.EVT_LISTBOX(self, self.checkLB.GetId(), self.OnTagSelect)

	# NOTE: TagManager :: OnTagSelect		=> Event when tag is selected
	def OnTagSelect(self, event):
		item = self.checkLB.GetStringSelection()
		tip = "Appears in: " + ', '.join(self.tags_dict[item])
		self.helper.SetLabel(tip)


	# NOTE: TagManager :: SetList		=> note
	def SetList(self, tags=None):
		if not tags:
			tags = []
		tags_doublons = []
		for tag in tags:
			if not tag in tags_doublons:
				tags_doublons.append(tag)
		tags = tags_doublons

		self.tagsList = tags
		self.checkLB.Set(self.tagsList)

	# NOTE: TagManager :: SetTagsDict		=> Set the tags dictionnary variable
	def SetTagsDict(self, tags_dict):
		self.tags_dict = tags_dict

	# NOTE: TagManager :: GetSelectedTags		=> Retrieve checked tags
	def GetCheckedTags(self):
		checkedTags = []
		for i in xrange(len(self.tagsList)):
			if self.checkLB.IsChecked(i):
				checkedTags.append(self.tagsList[i])
		return checkedTags

	# NOTE: TagManager :: OnOK		=> Event when ok button is clicked
	def OnOK(self, event):
		checkedTags = self.GetCheckedTags()
		self.parent.SetCheckedTags(checkedTags)
		if self.isRunAll:
			if self.genEnv.IsChecked():
				self.parent.DoRunAll()
			else:
				self.parent.DoRunAll()
		else:
			self.parent.DoRun()
		self.Destroy()

	# NOTE: TagManager :: OnClose		=> Event when close button is clicked
	def OnClose(self, event):
		self.Destroy()


### -----------------------------------------------------------------------------------------------
# NOTE: Interpretor :: Shell interpretor
class Interpretor(object):
	"""docstring for Interpretor"""

	def __init__(self, locals, rawin, stdin, stdout, stderr):
		super(Interpretor, self).__init__()
		self.introText = "##################################################################\n#            *~. Welcome to behave testing console .~*           #\n##################################################################"
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

		self.bp = subprocess.Popen(term, shell=False, stdout=subprocess.PIPE, stdin=subprocess.PIPE,
								   stderr=subprocess.PIPE)

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
		\n\tClass :\t\t%s\n\n\tInherit from :\t%s\n\n\tAttributes :\t%s\n\n\tMethods :\t%s\n" % (
		class_name, parent, '\n\t\t\t'.join([attr + "\t:: " + typ for attr, typ in attrs]),
		"\n\t\t\t".join([method + "\tparams :: " + params for method, params in methods])
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
		time.sleep(2)

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
		\n\tClass :\t\t%s\n\n\tInherit from :\t%s\n\n\tAttributes :\t%s\n\n\tMethods :\t%s\n" % (
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


###------------------------------------------------------------------------------------------------
# NOTE: BehaveManager << object :: Object for behave managing
class BehaveManager(object):
	""" docstring for BehaveManager """

	# NOTE: BehaveManager :: constructor	=> __init__(self, *args, **kwargs)
	def __init__(self, *args, **kwargs):
		pass

	# NOTE: BehaveManager :: __str__		=> String representation of the class
	@classmethod
	def __str__(cls):
		attrs = []
		class_name = "BehaveManager"
		parent = "object"
		methods = [
			('__init__', 'self, *args, **kwargs'),
			('<static> GetTagsList', 'feature_code')
		]
		return "\n--------------------------------------------------\
		\n\tClass :\t\t%s\n\n\tInherit from :\t%s\n\n\tAttributes :\t%s\n\n\tMethods :\t%s\n" % (
		class_name, parent, '\n\t\t\t'.join([attr + "\t:: " + typ for attr, typ in attrs]),
		"\n\t\t\t".join([method + "\tparams :: " + params for method, params in methods])
		)

	# NOTE: BehaveManager :: GetTagsList	=> Retrieve from feature file a list of tags
	@staticmethod
	def GetTagsList(feature_code):
		pattern = re.compile("@[^,\s]*")
		matched = pattern.findall(feature_code)
		matched = [m[1:] for m in matched]
		return matched


### ------------------------------------------------------------------------------------------- ###
# =======================================Main Application======================================== #
### ------------------------------------------------------------------------------------------- ###

def start():
	app = wx.App()
	frame = TestFrame(None, -1, 'Testing Shell')
	tree = [(['CoupledSample', ['Atomic1', 'Atomic2', 'Atomic3']]), ['Atomic4'], ['Atomic5']]
	frame.ConstructTree(tree)
	app.MainLoop()


def info():
	print TestFrame.__str__()
	print ModelTree.__str__()
	print TagManager.__str__()
	print Interpretor.__str__()
	print TermProcessThread.__str__()
	print BehaveManager.__str__()


def manager(args):
	os.system(['clear', 'cls'][os.name == 'nt'])
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
