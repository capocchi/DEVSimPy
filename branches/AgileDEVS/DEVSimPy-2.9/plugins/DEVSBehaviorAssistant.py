# -*- coding: utf-8 -*-

"""
	Authors: T. Ville (tim.ville@me.com)
	Date: 04/11/2013
	Description:
	Depends: wx, devsimpy
"""

### ----------------------------------------------------------------------- ###
# =================================Imports=================================== #
### ----------------------------------------------------------------------- ###

import wx
import pluginmanager
from DEVSKernel.PyDEVS.DEVS import AtomicDEVS, CoupledDEVS
import zipfile
import os
import inspect
import imp
import types

### ------------------------------------------------------------------------ ###
# =============================Graphical  tools=============================== #
### ------------------------------------------------------------------------ ###

# NOTE: DEVSBehaviorAssistant :: GetFlatDEVSList
#		=> This method retrieve all Atomic models from the diagram in a list,
#				no matter the hierarchy
def GetFlatDEVSList(coupled_devs, recurs=[]):
    """ Get the flat list of devs model composing coupled_devs (recursively)
	"""
    for devs in coupled_devs.componentSet:
        # Les instances recuperees doivent  etre de type AMD ou CMD
        if isinstance(devs, AtomicDEVS) and zipfile.is_zipfile(os.path.dirname(devs.getBlockModel().python_path)):
            recurs.append(devs)
        elif isinstance(devs, CoupledDEVS):
            recurs.append(devs)
            GetFlatDEVSList(devs, recurs)
    return recurs
# -----------------------------------------------------------------------------
def behavior(inst):
    """ Manage transitionnal methods decoration of Atomic models
    """
    model = inst.getBlockModel()
    methods = []
    for name, _ in inspect.getmembers(inst, inspect.ismethod):
        methods.append(name)
    methods.append("inject")

	# Retrieve test files from AMD model
    spec_file, behavior_file = model.GetTempTests()

	# Parse spec file to generate decorators and patch in behavior test file
    os.system("python plugins/ScriptsTools/Grammar.py %s %s"%(spec_file, behavior_file))
    with open(behavior_file, 'r') as behavior_f:
        behavior_code = behavior_f.read()
    model.UpdateBehavior(behavior_code)

	# Search decorators function object in the test file
    decorators = None
    decorators = importation(behavior_file)
    decorators = [decorators.__dict__.get(a) for a in dir(decorators) if isinstance(decorators.__dict__.get(a), types.FunctionType)]

	# Construct a dictionnary
	#	<name of function to decorate : decorator function object>
	# Name constraint : dec_"name of the function to decorate"
    decors = dict()
    for decorator in decorators:
        name = decorator.__name__
        name = name.replace('dec_', '')
        if name in methods:
            decors[name] = decorator
        else:
            print "Unknown decorator %s"%decorator.__name__

	# Decorate or patch?
    for name, obj in inspect.getmembers(inst, inspect.ismethod):
		# Only retrieve commune methods between decorators and model
        if name in decors.keys():
			# If method is not empty
            if not fncIsEmpty(obj):
				# We decorate the method with the appropriate decorator
                setattr(inst, name, decors[name](obj))
            else:
				# Else we patch the method with mock object
                pass
    return inst
# ------------------------------------------------------------------------------
def importation(test_file):
    """ DocString
    """
    loader = imp.load_source('decorators', test_file)
    return loader
# ------------------------------------------------------------------------------
# NOTE: DEVSBehaviorAssistant :: fncIsEmpty			=>
def	fncIsEmpty(fnc):
    """ DocString
    """
    source = inspect.getsource(fnc)
    code = ""
    for line in source.splitlines():
        if not "def " in line:
            code += line
    code = code.strip()
    return code == 'pass'
# ------------------------------------------------------------------------------

# NOTE: DEVSBehaviorAssistant :: start_test			=>
@pluginmanager.register("START_TEST")
def start_test(*args, **kwargs):
    """ DocString
    """
    master = kwargs['master']

	# Parcours de la liste des modeles recuperes
    for devs in GetFlatDEVSList(master, []):
        block = devs.getBlockModel()

		# Si le modele embarque des tests
        if block.hasTests():
            devs = behavior(devs)
# -----------------------------------------------------------------------------

# NOTE: DEVSBehaviorAssistant :: test_manager		=>
# @pluginmanager.register("SIM_TEST")
# def test_manager(*args, **kwargs):
#     """ DocString
#     """
#     pass


# class BehaviorAssistant(wx.Frame):
# 	""" DocString for BehaviorAssistant
#     """
#     def __init__(self, *args, **kwargs):

# 		kwargs["style"] = wx.DEFAULT_FRAME_STYLE
# 		kwargs["size"] = (1220, 750)

# 		super(BehaviorAssistant, self).__init__(*args, **kwargs)

# 		self.ConfigGUI()
# 		self.Show()

# 	def ConfigGUI(self):

# 		### Menu bar config----------------------------------------------------
# 		menubar = wx.MenuBar()

# 		### File menu----------------------------------------------------------
# 		file_menu = wx.Menu()
# 		leave = wx.MenuItem(file_menu, wx.NewId(), _('&Quit\tCtrl+Q'), _('Quit the application'))
# 		file_menu.AppendItem(leave)
# 		### -------------------------------------------------------------------

# 		### Edition menu-------------------------------------------------------
# 		edition = wx.Menu()
# 		specs = wx.MenuItem(edition, wx.NewId(), _('&Specs\tCtrl+T'), _('Edit specifications'))
# 		model = wx.MenuItem(edition, wx.NewId(), _('&Model\tCtrl+M'), _('Edit model DEVS'))
# 		edition.AppendItem(specs)
# 		edition.AppendItem(model)
# 		### -------------------------------------------------------------------

# 		### Run menu-----------------------------------------------------------
# 		run = wx.Menu()
# 		test = wx.MenuItem(run, wx.NewId(), _('&Run\tCtrl+R'), _('Run test on model'))
# 		run.AppendItem(test)
# 		### -------------------------------------------------------------------

# 		### Help menu----------------------------------------------------------
# 		help = wx.Menu()
# 		helper = wx.MenuItem(help, wx.NewId(), _('&Help\tCtrl+H'), _('Show help'))
# 		help.AppendItem(helper)
# 		### -------------------------------------------------------------------

# 		menubar.Append(file_menu, _('&File'))
# 		menubar.Append(edition, _('&Edition'))
# 		menubar.Append(run, _('&Run'))
# 		menubar.Append(help, _('&Help'))

# 		self.SetMenuBar(menubar)
# 		### -------------------------------------------------------------------
# 		#=====================================================================#
# 		### Panel config-------------------------------------------------------

# 		self.panel = wx.Panel(self)