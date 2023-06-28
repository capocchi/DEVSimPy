# -*- coding: utf-8 -*-

"""
    Authors: L. Capocchi (capocchi@univ-corse.fr)
    Date: 30/10/2020
    Description:
        Plot the state trajectory of model.
        Based on transition function decorator.
        Warning: "Activity pattern" and "State trajectory" plug-in can not coexist simultaneously.
        Activity must be disabled !
    Depends:
"""

### ----------------------------------------------------------

### at the beginning to prevent with statement for python version <=2.5
from __future__ import with_statement

import sys
import wx
import os
import subprocess
import importlib

import inspect
if not hasattr(inspect, 'getargspec'):
    inspect.getargspec = inspect.getfullargspec
    
import gettext
_ = gettext.gettext

import wx.lib.agw.aui as aui

import matplotlib
from matplotlib.backends.backend_wxagg import (
    FigureCanvasWxAgg as FigureCanvas,
    NavigationToolbar2WxAgg as NavigationToolbar)

class PlotPanel(wx.Panel):
    def __init__(self, parent, id=-1, dpi=None, **kwargs):

        wx.Panel.__init__(self, parent, id=id, **kwargs)
        self.figure = matplotlib.figure.Figure(dpi=dpi, figsize=(2, 2))
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.toolbar = NavigationToolbar(self.canvas)
        self.toolbar.Realize()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas, 1, wx.EXPAND)
        sizer.Add(self.toolbar, 0, wx.LEFT | wx.EXPAND)
        self.SetSizer(sizer)
        self.SetAutoLayout(True)

class PlotNotebook(wx.Panel):
    def __init__(self, parent, id=-1):
        wx.Panel.__init__(self, parent, id=id)
        self.nb = aui.AuiNotebook(self)
        sizer = wx.BoxSizer()
        sizer.Add(self.nb, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.SetAutoLayout(True)

    def add(self, name="plot"):
        page = PlotPanel(self.nb)
        self.nb.AddPage(page, name)
        return page.figure

# to send event
try:
    from pubsub import pub
except Exception:
    sys.stdout.write('Last version for Python2 is PyPubSub 3.3.0 \n pip install PyPubSub==3.3.0')
    sys.exit()

from PluginManager import PluginManager
from Container import Block, CodeBlock, ContainerBlock

ID_SHAPE = wx.NewIdRef()

def log(func):
    def wrapped(*args, **kwargs):

        try:
            #print "Entering: [%s] with parameters %s" % (func.__name__, args)
            try:

                ### DEVS instance
                devs = func.__self__

                ### create
                func_name = func.__name__

                #if func_name not in devs.state_trajectory:
                #    devs.state_trajectory[func_name] = {}

                ### condition
                cond = hasattr(devs, 'state') and 'status' in devs.state.keys()

                ### is DEVS model has no state_trajectory attribute, we create it only for init!
                if not hasattr(devs, 'state_trajectory'):
                    in_state = devs.getStatus() if cond else 'Undefined'
                    setattr(devs,'state_trajectory', {func_name:{0.0: in_state}})

                ### if transition function is not yet introduced
                if func_name not in devs.state_trajectory:
                    devs.state_trajectory[func_name] = {}

                r =  func(*args, **kwargs)

                ### for number in axis
                try:
                    #ts = devs.timeLast + devs.elapsed
                    ts = devs.timeNext
                ### PyPDEVS has a tuple for timeLast
                except TypeError:
                    ts = devs.timeNext[0]
                    #ts = devs.timeLast[0] + devs.elapsed

                ### Add the output state at time ts for the func_name transition function
                out_state = devs.getStatus() if cond else 'Undefined'
                devs.state_trajectory[func_name][ts] = out_state

                return r

            except Exception as e:
                sys.stdout.write(_('Exception for state trajectory plug-in in %s : %s' % (func.__name__, e)))
        finally:
            pass

    return wrapped

def state_trajectory_decorator(inst):
    ''' Decorator for all atomic model transition function to build state trajectory.
    '''

    for name, m in inspect.getmembers(inst, inspect.isfunction)+inspect.getmembers(inst, inspect.ismethod):
        if name in inst.getBlockModel().state_trajectory.values():
            setattr(inst, name, log(m))

    return inst

def GetFlatDEVSList(coupled_devs, l=[]):
    """ Get the flat list of devs model composing coupled_devs (recursively)
    """

    from DomainInterface.DomainBehavior import DomainBehavior
    from DomainInterface.DomainStructure import DomainStructure

    for devs in coupled_devs.componentSet:
        if isinstance(devs, DomainBehavior):
            l.append(devs)
        elif isinstance(devs, DomainStructure):
            l.append(devs)
            GetFlatDEVSList(devs,l)
    return l

def GetFlatShapesList(diagram,L):
    """ Get the list of shapes recursively
    """
    for m in diagram.GetShapeList():
        if isinstance(m, CodeBlock):
            L.append(m.label)
        elif isinstance(m, ContainerBlock):
             GetFlatShapesList(m,L)
    return L

def PlotStateTrajectory(m):
    """ Plot the state trajectory of m model.
    """

    if m:
        label = m.getBlockModel().label

        if hasattr(m, 'state_trajectory'):

            frame = wx.Frame(None, -1, '%s State Trajectory'%label)
            plotter = PlotNotebook(frame)

            ### tabs of plot depend on the transition function selected
            for func_name,st in m.state_trajectory.items():
                #states = list(set(st.values()))

                ### adapted to PyPDEVS
                times_lst = list(map(lambda a: a[0] if isinstance(a, tuple) else a, st.keys()))

                ### display index instead of state as string
                #states_lst = [states.index(st[k]) for k in st]

                ### state can be specified as IDLE:4 with 4 for ta function !
                states_lst = [s.split(':')[0] for s in st.values()]

                items = zip(times_lst, states_lst)
    
                sorted_items = sorted(items, key=lambda x: (x[0], x[1]))
                
                x, y = zip(*sorted_items)

                assert len(x)==len(y)
                
                axes = plotter.add(func_name).gca()
                axes.set_xlabel('Time',fontsize=16)
                axes.set_ylabel('State',fontsize=16)
                axes.step(x, y)
                axes.grid(True)
                axes.set_title('%s (%s)'%(label,func_name))
            
            frame.Show()

        else:
            dial = wx.MessageDialog(None,
                            _('Select at least one decorate transition function for %s.')%label,
                            _('Plot Manager'),
                            wx.OK | wx.ICON_EXCLAMATION)
            dial.ShowModal()
    else:
        dial = wx.MessageDialog(None,
                        _('Go to simulation process first.'),
                        _('Plot Manager'),
                        wx.OK | wx.ICON_EXCLAMATION)
        dial.ShowModal()

def Plot(diagram, selected_label):

    master = diagram.getDEVSModel()

    if master:
        ### for all devs models
        for m in GetFlatDEVSList(master, []):
            label = m.getBlockModel().label

            ### model is checked and selected
            if selected_label == label:
                PlotStateTrajectory(m)
    else:
        dial = wx.MessageDialog(None,
                        _('Go to simulation process first.'),
                        _('Plot Manager'),
                        wx.OK | wx.ICON_EXCLAMATION)
        dial.ShowModal()

######################################################################
###                Pluginmanager Function Definition
######################################################################

@PluginManager.register("START_STATE_TRAJECTORY")
def start_state_trajectory(*args, **kwargs):
    """ Start the definition of the state trajectory attributes for all selected block model
    """

    master = kwargs['master']
    parent = kwargs['parent']

    if not PluginManager.is_enable('start_activity_tracking'):
        for devs in GetFlatDEVSList(master, []):
            block = devs.getBlockModel()
            if hasattr(block, 'state_trajectory'):
                devs = state_trajectory_decorator(devs)
    else:
        sys.stdout.write("Activity pattern must be disabled!\n")

@PluginManager.register("ADD_STATE_TRAJECTORY_MENU")
def add_state_trajectory_menu(*args, **kwargs):

    global block

    menu = kwargs['parent']
    block = kwargs['model']

    def OnPlot(event):
        PlotStateTrajectory(block.getDEVSModel())

    states = wx.MenuItem(menu, ID_SHAPE, _("State Trajectory"), _("State trajectory graph"))
    states.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH_16_16, 'graph.png')))

    States_menu = menu.Insert(2, states)
    menu.Bind(wx.EVT_MENU, OnPlot, id=ID_SHAPE)

######################################################################
###
######################################################################

def Config(parent):
    """ Plug-in settings frame.
    """

    global cb1
    global cb2
    global diagram

    main = wx.GetApp().GetTopWindow()
    nb2 = main.GetDiagramNotebook()
    currentPage = nb2.GetCurrentPage()
    diagram = currentPage.diagram
    master = None

    frame = wx.Frame(parent,
                    wx.ID_ANY,
                    title = _('State Trajectory Plotting'),
                    style = wx.DEFAULT_FRAME_STYLE | wx.CLIP_CHILDREN | wx.STAY_ON_TOP)
    panel = wx.Panel(frame, wx.ID_ANY)

    lst_1 = GetFlatShapesList(diagram,[])
    lst_2  = ('confTransition', 'extTransition', 'intTransition')

    vbox = wx.BoxSizer(wx.VERTICAL)
    hbox = wx.BoxSizer(wx.HORIZONTAL)
    hbox2 = wx.BoxSizer(wx.HORIZONTAL)

    st = wx.StaticText(panel, wx.ID_ANY, _("Select models and functions:"), (10,10))

    cb1 = wx.CheckListBox(panel, wx.ID_ANY, (10, 30), wx.DefaultSize, lst_1, style=wx.LB_SORT)
    cb2 = wx.CheckListBox(panel, wx.ID_ANY, (10, 30), wx.DefaultSize, lst_2)

    selBtn = wx.Button(panel, wx.ID_SELECTALL)
    desBtn = wx.Button(panel, wx.ID_ANY, _('Deselect All'))
    okBtn = wx.Button(panel, wx.ID_OK)
    #reportBtn = wx.Button(panel, wx.ID_ANY, _('Report'))

    hbox2.Add(cb1, 1, wx.EXPAND, 5)
    hbox2.Add(cb2, 1, wx.EXPAND, 5)

    hbox.Add(selBtn, 0, wx.LEFT)
    hbox.Add(desBtn, 0, wx.CENTER)
    hbox.Add(okBtn, 0, wx.RIGHT)

    vbox.Add(st, 0, wx.ALL, 5)
    vbox.Add(hbox2, 1, wx.EXPAND, 5, 5)
    vbox.Add(hbox, 0, wx.CENTER, 10, 10)

    panel.SetSizer(vbox)

    ### si des mod�les sont deja activ�s pour le plugin il faut les checker
    num = cb1.GetCount()
    L1=[] ### liste des shapes � checker
    L2={} ### la liste des function tracer (identique pour tous les block pour l'instant)
    for index in range(num):
        block=diagram.GetShapeByLabel(cb1.GetString(index))
        if hasattr(block,'state_trajectory'):
            L1.append(index)
            L2[block.label] = block.state_trajectory.keys()

    if L1:
        cb1.SetCheckedItems(L1)
        ### tout les blocks on la meme liste de function active pour le trace, donc on prend la premi�re
        cb2.SetCheckedItems(list(L2.values())[0])

    ### ckeck par defaut delta_ext et delta_int
    if L2 == {}:
        cb2.SetCheckedItems([1,2])

    def OnPlot(event):
        ''' State trajectory plotting has been invoked
        '''

        cb1 = event.GetEventObject()
        index = cb1.GetSelection()
        selected_label = cb1.GetString(cb1.GetSelection())
        if cb1.IsChecked(index):
            Plot(diagram, selected_label)

    def OnSelectAll(evt):
        """ Select All button has been pressed and all plug-ins are enabled.
        """
        cb1.SetCheckedItems(range(cb1.GetCount()))

    def OnDeselectAll(evt):
        """ Deselect All button has been pressed and all plugins are disabled.
        """
        cb1.SetCheckedItems([])

    def OnOk(evt):
        btn = evt.GetEventObject()
        frame = btn.GetTopLevelParent()
        num1 = cb1.GetCount()
        num2 = cb2.GetCount()

        for index in range(num1):
            label = cb1.GetString(index)

            shape = diagram.GetShapeByLabel(label)
            plotting_condition = hasattr(shape, 'state_trajectory')

            assert(isinstance(shape, Block))

            if cb1.IsChecked(index):
                ### dictionnaire avec des cles correspondant aux index de la liste de function de transition et avec des valeurs correspondant aux noms de ces fonctions
                D = dict([(index,cb2.GetString(index)) for index in range(num2) if cb2.IsChecked(index)])

                if not plotting_condition:
                    setattr(shape, 'state_trajectory', D)
                else:
                    shape.state_trajectory = D
            elif plotting_condition:
                del shape.state_trajectory

        frame.Destroy()

    selBtn.Bind(wx.EVT_BUTTON, OnSelectAll)
    desBtn.Bind(wx.EVT_BUTTON, OnDeselectAll)
    okBtn.Bind(wx.EVT_BUTTON, OnOk)

    def showPopupMenu(event):
        """
        Create and display a popup menu on right-click event
        """

        win  = event.GetEventObject()

        ### make a menu
        menu = wx.Menu()
        # Show how to put an icon in the menu
        item = wx.MenuItem(menu, wx.NewIdRef(), "Aext")
        menu.AppendItem(item)
        menu.Append(wx.NewIdRef(), "Aint")
        menu.Append(wx.NewIdRef(), "A=Aext+Aint")

        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        win.PopupMenu(menu)
        menu.Destroy()

    def OnRightClickCb1(evt):
        showPopupMenu(evt)

    def OnRightDClickCb1(evt):
        OnPlot(evt)

    ### 1. Register source's EVT_s to inOvoke launcher.
    #cb1.Bind(wx.EVT_RIGHT_DOWN, OnRightClickCb1)
    cb1.Bind(wx.EVT_LEFT_DCLICK, OnRightDClickCb1)

    frame.CenterOnParent(wx.BOTH)
    frame.Show()

def UnConfig():
    """ Reset the plugin effects
    """

    global cb1
    global cb2
    global diagram

    main = wx.GetApp().GetTopWindow()
    nb2 = main.GetDiagramNotebook()
    currentPage = nb2.GetCurrentPage()
    diagram = currentPage.diagram

    lst  = [a.label for a in [s for s in diagram.GetShapeList() if isinstance(s, CodeBlock)]]

    for label in lst:
        shape = diagram.GetShapeByLabel(label)
        if hasattr(shape, 'state_trajectory'):
            del shape.state_trajectory
