# -*- coding: utf-8 -*-

"""
    Authors: T. Ville (tim.ville@me.com)
    Date: 08/12/2014
    Description:
    Depends: wx, devsimpy
"""

# ## ----------------------------------------------------------------------- ###
# =================================Imports=================================== #
# ## ----------------------------------------------------------------------- ###

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
def get_flat_devs_list(coupled_devs, recurs=None):
    """ Get the flat list of devs model composing coupled_devs (recursively)
    :param coupled_devs:
    :param recurs:
    """
    if not recurs:
        recurs = []
    for devs in coupled_devs.componentSet:
        # Les instances recuperees doivent  etre de type AMD ou CMD
        if isinstance(devs, AtomicDEVS) and zipfile.is_zipfile(os.path.dirname(devs.getBlockModel().python_path)):
            recurs.append(devs)
        elif isinstance(devs, CoupledDEVS):
            recurs.append(devs)
            get_flat_devs_list(devs, recurs)
    return recurs


# -----------------------------------------------------------------------------
def behavior(inst):
    """ Manage transitionnal methods decoration of Atomic models
    :param inst: devs model instance
    """
    model = inst.getBlockModel()
    methods = []
    for name, _ in inspect.getmembers(inst, inspect.ismethod):
        methods.append(name)

    # Retrieve test files from AMD model
    spec_file, behavior_file = model.GetTempTests()

    # Parse spec file to generate decorators and patch in behavior test file
    os.system("python plugins/ScriptsTools/Grammar.py %s %s" % (spec_file, behavior_file))
    with open(behavior_file, 'r') as behavior_f:
        behavior_code = behavior_f.read()
    model.UpdateBehavior(behavior_code)

    # Search decorators function object in the test file
    tests = importation(behavior_file)
    tests = [tests.__dict__.get(a) for a in dir(tests) if isinstance(tests.__dict__.get(a), types.FunctionType)]

    # Construct a dictionnary
    #	<name of function to decorate   : decorator function object>
    #   <name of function to patch      : patch function object>
    # Name constraint   : dec_"name of the function to decorate"
    #                   : patch_"name of the function to patch"
    decorators = dict()
    patches = dict()
    for test in tests:
        name = test.__name__
        if name.startswith("dec_") and name.replace("dec_", '') in methods:
            name = name.replace('dec_', '')
            decorators[name] = test
        elif name.startswith("patch_") and name.replace("patch_", '') in methods:
            name = name.replace('patch_', '')
            patches[name] = test
        else:
            print "Unknown test function: %s" % test.__name__

    # Decorate or patch?
    for name, obj in inspect.getmembers(inst, inspect.ismethod):
        # Only retrieve commune methods between decorators and model
        if name in decorators.keys():
            if not fnc_is_empty(obj):
                # We decorate the method with the appropriate decorator
                setattr(inst, name, decorators[name](obj))
            else:
                print "Error during {0} decoration of {1} object".format(name, str(obj))
        elif name in patches.keys():
            if fnc_is_empty(obj):
                setattr(inst, name, patches[name](obj))
    return inst


# ------------------------------------------------------------------------------
def importation(test_file):
    """ DocString
    :param test_file: path
    """
    loader = imp.load_source('decorators', test_file)
    return loader


# ------------------------------------------------------------------------------
# NOTE: DEVSBehaviorAssistant :: fncIsEmpty			=>
def fnc_is_empty(fnc):
    """ DocString
    :param fnc: function object
    """
    source = inspect.getsource(fnc)
    code = ""
    for line in source.splitlines():
        if not "def " in line \
                and not line.startswith("'''") \
                and not line.startswith('"""') \
                and not line.startswith("#"):
            code += line
    code = code.strip()
    return code == 'pass'


# ------------------------------------------------------------------------------

# NOTE: DEVSBehaviorAssistant :: start_test			=>
@pluginmanager.register("START_TEST")
def start_test(**kwargs):
    """ DocString
    :param kwargs: dict
    """
    master = kwargs['master']

    # Parcours de la liste des modeles recuperes
    for devs in get_flat_devs_list(master, []):
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


class BehaviorAssistant(wx.Frame):
    """ DocString for BehaviorAssistant
    """

    def __init__(self, *args, **kwargs):
        kwargs["style"] = wx.DEFAULT_FRAME_STYLE
        kwargs["size"] = (1220, 750)

        super(BehaviorAssistant, self).__init__(*args, **kwargs)

        self.panel = wx.Panel(self)
        self.ConfigGUI()
        self.Show()

    def ConfigGUI(self):
        # ## Menu bar config----------------------------------------------------
        """
        Configure the GUI
        """
        menubar = wx.MenuBar()

        ### File menu----------------------------------------------------------
        file_menu = wx.Menu()
        leave = wx.MenuItem(file_menu, wx.NewId(), '&Quit\tCtrl+Q', 'Quit the application')
        file_menu.AppendItem(leave)
        ### -------------------------------------------------------------------

        ### Edition menu-------------------------------------------------------
        edition = wx.Menu()
        specs = wx.MenuItem(edition, wx.NewId(), '&Specs\tCtrl+T', 'Edit specifications')
        model = wx.MenuItem(edition, wx.NewId(), '&Model\tCtrl+M', 'Edit model DEVS')
        edition.AppendItem(specs)
        edition.AppendItem(model)
        ### -------------------------------------------------------------------

        ### Run menu-----------------------------------------------------------
        run = wx.Menu()
        test = wx.MenuItem(run, wx.NewId(), '&Run\tCtrl+R', 'Run test on model')
        run.AppendItem(test)
        ### -------------------------------------------------------------------

        ### Help menu----------------------------------------------------------
        help = wx.Menu()
        helper = wx.MenuItem(help, wx.NewId(), '&Help\tCtrl+H', 'Show help')
        help.AppendItem(helper)
        ### -------------------------------------------------------------------

        menubar.Append(file_menu, '&File')
        menubar.Append(edition, '&Edition')
        menubar.Append(run, '&Run')
        menubar.Append(help, '&Help')

        self.SetMenuBar(menubar)
        ### -------------------------------------------------------------------
        #=====================================================================#
        ### Panel config-------------------------------------------------------
