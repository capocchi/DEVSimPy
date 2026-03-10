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

### at the beginning to prevent with statement for python version <=2.5
from __future__ import with_statement

import sys
import wx
import os
import inspect
import subprocess
import importlib

import gettext
_ = gettext.gettext

import wx.lib.agw.aui as aui

import matplotlib as mpl
from matplotlib.backends.backend_wxagg import (
    FigureCanvasWxAgg as FigureCanvas,
    NavigationToolbar2WxAgg as NavigationToolbar)

class PlotPanel(wx.Panel):
    def __init__(self, parent, id=-1, dpi=None, **kwargs):

        wx.Panel.__init__(self, parent, id=id, **kwargs)
        self.figure = mpl.figure.Figure(dpi=dpi, figsize=(2, 2))
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
from Utilities import load_and_resize_image

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
    states.SetBitmap(load_and_resize_image('graph.png'))

    States_menu = menu.Insert(2, states)
    menu.Bind(wx.EVT_MENU, OnPlot, id=ID_SHAPE)

######################################################################
###
######################################################################

def Config(parent):
    """ Plug-in settings frame with optimized UI.
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
                    style = wx.DEFAULT_FRAME_STYLE | wx.CLIP_CHILDREN | wx.STAY_ON_TOP,
                    size=(700, 500))
    panel = wx.Panel(frame, wx.ID_ANY)

    lst_1 = GetFlatShapesList(diagram,[])
    lst_2  = ('confTransition', 'extTransition', 'intTransition')

    # Main sizers
    main_sizer = wx.BoxSizer(wx.VERTICAL)
    
    # ===== TITLE SECTION =====
    title_font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
    title = wx.StaticText(panel, wx.ID_ANY, _("Select Models & Transition Functions"))
    title.SetFont(title_font)
    title_color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_HOTLIGHT)
    title.SetForegroundColour(title_color)
    main_sizer.Add(title, 0, wx.ALL, 10)
    
    # ===== CONTENT AREA WITH SPLITTER =====
    content_panel = wx.Panel(panel, wx.ID_ANY)
    content_sizer = wx.BoxSizer(wx.HORIZONTAL)
    
    # --- LEFT PANEL: MODELS ---
    left_box = wx.StaticBoxSizer(wx.VERTICAL, content_panel, _("Models"))
    search_box1 = wx.SearchCtrl(content_panel, wx.ID_ANY, size=(200, -1))
    search_box1.ShowSearchButton(True)
    search_box1.ShowCancelButton(True)
    search_box1.SetHint(_("Search models..."))
    
    cb1 = wx.CheckListBox(content_panel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, lst_1, style=wx.LB_SORT)
    cb1.SetMinSize((250, 250))
    
    left_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
    sel_btn1 = wx.Button(content_panel, wx.ID_ANY, _('Select All'), size=(100, -1))
    desel_btn1 = wx.Button(content_panel, wx.ID_ANY, _('Deselect All'), size=(100, -1))
    left_btn_sizer.Add(sel_btn1, 0, wx.RIGHT, 5)
    left_btn_sizer.Add(desel_btn1, 0, wx.RIGHT, 5)
    
    left_box.Add(search_box1, 0, wx.EXPAND | wx.BOTTOM, 8)
    left_box.Add(cb1, 1, wx.EXPAND, 0)
    left_box.Add(left_btn_sizer, 0, wx.TOP | wx.EXPAND, 8)
    content_sizer.Add(left_box, 1, wx.EXPAND | wx.RIGHT, 10)
    
    # --- RIGHT PANEL: TRANSITION FUNCTIONS ---
    right_box = wx.StaticBoxSizer(wx.VERTICAL, content_panel, _("Transition Functions"))
    desc_text = wx.StaticText(content_panel, wx.ID_ANY, 
        _("• confTransition: Confluent transition\n"
          "• extTransition: External transition\n"
          "• intTransition: Internal transition"))
    desc_text.SetForegroundColour(wx.Colour(100, 100, 100))
    small_font = wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL)
    desc_text.SetFont(small_font)
    
    cb2 = wx.CheckListBox(content_panel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, lst_2)
    cb2.SetMinSize((200, 250))
    
    right_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
    sel_btn2 = wx.Button(content_panel, wx.ID_ANY, _('Select All'), size=(100, -1))
    desel_btn2 = wx.Button(content_panel, wx.ID_ANY, _('Deselect All'), size=(100, -1))
    right_btn_sizer.Add(sel_btn2, 0, wx.RIGHT, 5)
    right_btn_sizer.Add(desel_btn2, 0, wx.RIGHT, 5)
    
    right_box.Add(desc_text, 0, wx.EXPAND | wx.BOTTOM, 10)
    right_box.Add(cb2, 1, wx.EXPAND, 0)
    right_box.Add(right_btn_sizer, 0, wx.TOP | wx.EXPAND, 8)
    content_sizer.Add(right_box, 1, wx.EXPAND, 0)
    
    content_panel.SetSizer(content_sizer)
    main_sizer.Add(content_panel, 1, wx.EXPAND | wx.ALL, 10)
    
    # ===== BUTTON SECTION =====
    btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
    okBtn = wx.Button(panel, wx.ID_OK, _('Apply'), size=(100, -1))
    cancelBtn = wx.Button(panel, wx.ID_CANCEL, _('Cancel'), size=(100, -1))
    helpBtn = wx.Button(panel, wx.ID_HELP, _('Help'), size=(100, -1))
    
    btn_sizer.Add(helpBtn, 0, wx.RIGHT, 10)
    btn_sizer.AddStretchSpacer()
    btn_sizer.Add(cancelBtn, 0, wx.RIGHT, 5)
    btn_sizer.Add(okBtn, 0, wx.RIGHT, 0)
    
    main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 10)
    panel.SetSizer(main_sizer)

    # ===== LOAD PREVIOUS SETTINGS =====
    num = cb1.GetCount()
    L1 = []  # indices of checked shapes
    L2 = {}  # function dictionary per block
    for index in range(num):
        block = diagram.GetShapeByLabel(cb1.GetString(index))
        if hasattr(block, 'state_trajectory'):
            L1.append(index)
            L2[block.label] = block.state_trajectory.keys()

    if L1:
        cb1.SetCheckedItems(L1)
        cb2.SetCheckedItems(list(L2.values())[0])
    else:
        # Default: select extTransition and intTransition
        cb2.SetCheckedItems([1, 2])

    # ===== EVENT HANDLERS =====
    def OnSearchModels(event):
        """Filter/highlight models based on search text"""
        search_text = search_box1.GetValue().lower()
        for i in range(cb1.GetCount()):
            item_text = cb1.GetString(i).lower()
            # Show/hide items based on search match (visual feedback)
            if search_text == "" or search_text in item_text:
                cb1.SetSelection(i)  # Highlight matching items
                break  # Select first match
            
        # Optional: Update checklist to reflect search results
        # This is visual-only feedback; actual selection happens on Apply

    def OnSelectAllModels(evt):
        """Select all models"""
        cb1.SetCheckedItems(range(cb1.GetCount()))

    def OnDeselectAllModels(evt):
        """Deselect all models"""
        cb1.SetCheckedItems([])

    def OnSelectAllFunctions(evt):
        """Select all transition functions"""
        cb2.SetCheckedItems(range(cb2.GetCount()))

    def OnDeselectAllFunctions(evt):
        """Deselect all transition functions"""
        cb2.SetCheckedItems([])

    def OnPlot(event):
        """State trajectory plotting has been invoked via double-click"""
        cb1_obj = event.GetEventObject()
        index = cb1_obj.GetSelection()
        if index >= 0:
            selected_label = cb1_obj.GetString(index)
            if cb1_obj.IsChecked(index):
                Plot(diagram, selected_label)

    def OnHelp(event):
        """Show help dialog"""
        help_msg = _(
            "State Trajectory Plotting Plugin\n\n"
            "1. Select Models: Choose which atomic models to track\n"
            "2. Select Functions: Choose which transition functions to plot\n"
            "   • confTransition: Confluent transition\n"
            "   • extTransition: External transition\n"
            "   • intTransition: Internal transition\n"
            "3. Use 'Select All' / 'Deselect All' for quick actions\n"
            "4. Search field to filter models by name\n"
            "5. Double-click a model name to plot immediately (if checked)\n"
            "6. Click 'Apply' to confirm your selections"
        )
        dlg = wx.MessageDialog(frame, help_msg, _("Help"), wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def OnOk(evt):
        """Apply button - save selections and close"""
        btn = evt.GetEventObject()
        frame_obj = btn.GetTopLevelParent()
        num1 = cb1.GetCount()
        num2 = cb2.GetCount()

        for index in range(num1):
            label = cb1.GetString(index)
            shape = diagram.GetShapeByLabel(label)
            plotting_condition = hasattr(shape, 'state_trajectory')

            assert(isinstance(shape, Block))

            if cb1.IsChecked(index):
                # Create dictionary: {func_index: func_name} for checked functions
                D = {idx: cb2.GetString(idx) for idx in range(num2) if cb2.IsChecked(idx)}
                
                if not plotting_condition:
                    setattr(shape, 'state_trajectory', D)
                else:
                    shape.state_trajectory = D
            elif plotting_condition:
                del shape.state_trajectory

        frame_obj.Destroy()

    # ===== BIND EVENT HANDLERS =====
    search_box1.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, OnSearchModels)
    search_box1.Bind(wx.EVT_TEXT, OnSearchModels)
    sel_btn1.Bind(wx.EVT_BUTTON, OnSelectAllModels)
    desel_btn1.Bind(wx.EVT_BUTTON, OnDeselectAllModels)
    sel_btn2.Bind(wx.EVT_BUTTON, OnSelectAllFunctions)
    desel_btn2.Bind(wx.EVT_BUTTON, OnDeselectAllFunctions)
    okBtn.Bind(wx.EVT_BUTTON, OnOk)
    cancelBtn.Bind(wx.EVT_BUTTON, lambda e: frame.Close())
    helpBtn.Bind(wx.EVT_BUTTON, OnHelp)
    cb1.Bind(wx.EVT_LEFT_DCLICK, OnPlot)

    # ===== FRAME SETUP =====
    frame.CenterOnParent(wx.BOTH)
    frame.Show()

def UnConfig():
    """ Reset the plugin effects when disabled
    """

    global cb1
    global cb2
    global diagram

    main = wx.GetApp().GetTopWindow()

    if hasattr(main, 'GetDiagramNotebook'):
        nb2 = main.GetDiagramNotebook()
        currentPage = nb2.GetCurrentPage()
        diagram = currentPage.diagram

        lst = [a.label for a in [s for s in diagram.GetShapeList() if isinstance(s, CodeBlock)]]

        for label in lst:
            shape = diagram.GetShapeByLabel(label)
            if hasattr(shape, 'state_trajectory'):
                del shape.state_trajectory