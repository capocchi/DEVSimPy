# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# WizardGUI.py ---
#                    --------------------------------
#                            Copyright (c) 2020
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 20/15/20
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

import wx
	
if wx.VERSION_STRING >= '4.0':
	from wx.adv import Wizard as wizmod
	wizmod.EVT_WIZARD_PAGE_CHANGED = wx.adv.EVT_WIZARD_PAGE_CHANGED
	wizmod.EVT_WIZARD_PAGE_CHANGING = wx.adv.EVT_WIZARD_PAGE_CHANGING
	wizmod.EVT_WIZARD_CANCEL = wx.adv.EVT_WIZARD_CANCEL
	wizmod.EVT_WIZARD_FINISHED = wx.adv.EVT_WIZARD_FINISHED
	WizardPage = wx.adv.WizardPage
else:
	from wx.wizard import Wizard as wizmod
	WizardPage = wx.wizard.PyWizardPage

	wizmod.EVT_WIZARD_PAGE_CHANGED = wx.wizard.EVT_WIZARD_PAGE_CHANGED
	wizmod.EVT_WIZARD_PAGE_CHANGING = wx.wizard.EVT_WIZARD_PAGE_CHANGING
	wizmod.EVT_WIZARD_CANCEL = wx.wizard.EVT_WIZARD_CANCEL
	wizmod.EVT_WIZARD_FINISHED = wx.wizard.EVT_WIZARD_FINISHED

import os
import sys
import zipfile
import wx.lib.filebrowsebutton as filebrowse
import datetime

import inspect
if not hasattr(inspect, 'getargspec'):
    inspect.getargspec = inspect.getfullargspec
    
import Container
import Components

_ = wx.GetTranslation

padding = 5
MAX_NB_PORT = 1000000
MIN_NB_PORT = 0
# Gives user's home directory
USERHOME = os.path.expanduser('~')

def atomicCode(label):
	code = """# -*- coding: utf-8 -*-

\"\"\"
-------------------------------------------------------------------------------
 Name:          		%s.py
 Model description:     <description>
 Authors:       		%s
 Organization:  		<your organization>
 Current date & time:   %s
 License:       		GPL v3.0
-------------------------------------------------------------------------------
\"\"\"

### Specific import ------------------------------------------------------------
from DomainInterface.DomainBehavior import DomainBehavior
from DomainInterface.Object import Message

### Model class ----------------------------------------------------------------
class %s(DomainBehavior):
	''' DEVS Class for the model %s
	'''

	def __init__(self):
		''' Constructor.
		'''
		DomainBehavior.__init__(self)

		self.initPhase('IDLE',INFINITY)

	def extTransition(self, *args):
		''' DEVS external transition function.
		'''
		return self.getState()

	def outputFnc(self):
		''' DEVS output function.
		'''
		return {}

	def intTransition(self):
		''' DEVS internal transition function.
		'''
		return self.getState()

	def timeAdvance(self):
		''' DEVS Time Advance function.
		'''
		return self.getSigma()

	def finish(self, msg):
		''' Additional function which is lunched just before the end of the simulation.
		'''
		pass
"""%(label,
	os.path.split(USERHOME)[-1],
	datetime.datetime.now(),
	label,
	label)

	### add confluent function only for PyPDEVS.
	code += """
	def confTransition(self, inputs):
		'''DEFAULT Confluent Transition Function.
		'''
		self.state = self.intTransition()
		self.state = self.extTransition(inputs)
		return self.getState()""" if 'PyPDEVS' in DEFAULT_DEVS_DIRNAME else ''

	### Dynamic structure only for PyPDEVS
	code += """

	def modelTransition(self, state):
		''' modelTransition method will be called at every step
			in simulated time on every model that transitioned
			in order to notify parent of structural change.
			Dynamic structure is possible for both Classic and Parallel DEVS,
			but only for local simulation.
		'''
		# Notify parent of structural change
		return True""" if 'PyPDEVS' in DEFAULT_DEVS_DIRNAME else ''

	return code

def coupledCode(label):
	code = """# -*- coding: utf-8 -*-

\"\"\"
-------------------------------------------------------------------------------
 Name:      			%s.py
 Model description:     <description>
 Authors:   			%s
 Date:     				%s
-------------------------------------------------------------------------------
\"\"\"

from DomainInterface.DomainStructure import DomainStructure
#    ======================================================================    #
class %s(DomainStructure):

	def __init__(self):
		DomainStructure.__init__(self)
"""%(label,
	os.path.split(USERHOME)[-1],
	datetime.datetime.now(),
	label)

	### Dynamic structure only for PyPDEVS
	code += """
	def modelTransition(self, state):
		''' modelTransition method will be called at every step
			in simulated time on every model that transitioned
			in order to notify parent of structural change.
			Dynamic structure is possible for both Classic and Parallel DEVS,
			but only for local simulation.
		'''
		### False if Top Level
		return True""" if 'PyPDEVS' in DEFAULT_DEVS_DIRNAME else ''

	return code

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# CLASSES DEFINITION
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

class TextObjectValidator(wx.PyValidator):
	""" TextObjectValidator()
	"""

	def __init__(self):
		""" Constructor.
		"""
		wx.PyValidator.__init__(self)

	def Clone(self):
		""" Clone method.
		"""
		return TextObjectValidator()

	def Validate(self, win):
		""" Validate fields.
		"""
		textCtrl = self.GetWindow()
		text = textCtrl.GetValue()

		if len(text.strip().split(' ')) > 1 :
			wx.MessageBox(_("The field must contain a string without space!"),_("Info"))
			textCtrl.SetBackgroundColour("pink")
			textCtrl.SetFocus()
			textCtrl.Refresh()
			return False
		else:
			textCtrl.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
			textCtrl.Refresh()
			return True

	def TransferToWindow(self):
		""" Prevent wxDialog from complaining.
		"""
		return True

	def TransferFromWindow(self):
		""" Prevent wxDialog from complaining.
		"""
		return True

class wizard_page(WizardPage):
	""" An extended panel obj with a few methods to keep track of its siblings.
	This should be modified and added to the wizard.  Season to taste."""
	
	def __init__(self, parent, title):
		""" Constructor.
		"""
		WizardPage.__init__(self, parent)
		self.next = self.prev = None
		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.title = wx.StaticText(self, wx.NewIdRef(), title)
		self.title.SetFont(wx.Font(18, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
		if wx.VERSION_STRING<'4.0':
			self.sizer.AddWindow(self.title, 0, wx.ALIGN_LEFT|wx.ALL, padding)
			self.sizer.AddWindow(wx.StaticLine(self, wx.NewIdRef()), 0, wx.EXPAND|wx.ALL, padding)
		else:
			self.sizer.Add(self.title, 0, wx.ALIGN_LEFT|wx.ALL, padding)
			self.sizer.Add(wx.StaticLine(self, wx.NewIdRef()), 0, wx.EXPAND|wx.ALL, padding)
				
		self.SetSizer(self.sizer)

	def add_stuff(self, stuff):
		"""Add aditional widgets to the bottom of the page"""
		self.sizer.Add(stuff, 0, wx.EXPAND|wx.ALL, padding)

	def SetNext(self, next):
		"""Set the next page"""
		self.next = next

	def SetPrev(self, prev):
		"""Set the previous page"""
		self.prev = prev

	def GetNext(self):
		"""Return the next page"""
		return self.next

	def GetPrev(self):
		"""Return the previous page"""
		return self.prev

class Wizard(wizmod):
	"""Add pages to this wizard object to make it useful."""

	def __init__(self, title, parent, img_filename = ""):
		""" Constructor.
		"""
		img = wx.Bitmap(img_filename) if img_filename and os.path.exists(img_filename) else wx.NullBitmap

		wizmod.__init__(self, parent, wx.NewIdRef(), title, img)

		self.SetPageSize((400,300))

		# pages list
		self.pages = []

		#flag
		self.canceled_flag = False
		self.overwrite_flag = True

		# Lets catch the events
		self.Bind(wizmod.EVT_WIZARD_PAGE_CHANGED, self.on_page_changed)
		self.Bind(wizmod.EVT_WIZARD_PAGE_CHANGING, self.on_page_changing)
		self.Bind(wizmod.EVT_WIZARD_CANCEL, self.on_cancel)
		self.Bind(wizmod.EVT_WIZARD_FINISHED, self.on_finished)
		self.Bind(wx.EVT_CLOSE, self.on_close)

	def add_page(self, page):
		"""Add a wizard page to the list."""
		if self.pages:
				previous_page = self.pages[-1]
				page.SetPrev(previous_page)
				previous_page.SetNext(page)
		self.pages.append(page)

	def run(self):
		""" Run wizard.
		"""
		self.RunWizard(self.pages[0])

	def on_page_changed(self, evt):
		"""Executed after the page has changed."""
		#if evt.GetDirection():  dir = "forward"
		#else:                   dir = "backward"
		#page = evt.GetPage()
		pass

	def on_page_changing(self, evt):
		"""Executed before the page changes, so we might veto it."""
		#if evt.GetDirection():  dir = "forward"
		#else:                   dir = "backward"
		#page = evt.GetPage()
		pass

	def on_cancel(self, evt):
		"""Cancel button has been pressed.  Clean up and exit without continuing."""
		self.canceled_flag = True
		self.on_close(evt)

	def on_finished(self, evt):
		"""Finish button has been pressed.  Give the specified values
		"""
		pass

	def on_close(self, evt):
		""" Close button has been pressed. Destroy the wizard.
		"""
		self.canceled_flag = True
		self.Destroy()

class ModelGeneratorWizard(Wizard):
	""" Model Generator Wizard Class.
	"""

	def __init__(self, *args, **kwargs):
		""" Constructor.
		"""

		if 'specific_domain_path' in kwargs:
			domain_path = kwargs['specific_domain_path']
			del kwargs['specific_domain_path']
		else:
			domain_path = DOMAIN_PATH

		Wizard.__init__(self, *args, **kwargs)

        # properties of model
		self.type = "Atomic"
		self.label = ""
		self.inputs = 1
		self.outputs = 1
		self.python_path = ""
		self.model_path = ""
		self.specific_behavior = ""

		# special properties for Port
		self.id = None

		# canvas parent
		parent = self.GetParent()

		# Create a page 1
		page1 = wizard_page(self, _('Type of Model'))
		bt1 = wx.RadioButton(page1, wx.NewIdRef(), _('Atomic model'), style = wx.RB_GROUP )
		bt2 = wx.RadioButton(page1, wx.NewIdRef(), _('Coupled model'))
		if wx.VERSION_STRING >= '4.0':
			bt1.SetToolTipString = bt1.SetToolTip
			bt2.SetToolTipString = bt2.SetToolTip

		bt1.SetToolTipString(_("DEVS classic atomic model. It is used to define the behavior (or a part of behavior) of the system"))
		bt2.SetToolTipString(_("DEVS classic coupled model. It is used to define the structure (or a part of structure) of the system"))
		page1.add_stuff(wx.StaticText(page1, wx.NewIdRef(), _('Choose the type of model:')))
		page1.add_stuff(bt1)
		page1.add_stuff(bt2)

		### if left click on the DetachedFrame, port instance can be created
		if isinstance(parent.GetTopLevelParent(), Container.DetachedFrame):
			bt3 = wx.RadioButton(page1, wx.NewIdRef(), _('Input Port'))
			bt4 = wx.RadioButton(page1, wx.NewIdRef(), _('Output Port'))
			if wx.VERSION_STRING >= '4.0':
				bt3.SetToolTipString = bt3.SetToolTip
				bt4.SetToolTipString = bt4.SetToolTip

			bt3.SetToolTipString(_("DEVS classic input model. It is used to link models"))
			bt4.SetToolTipString(_("DEVS classic output model. It is used to link models"))
			page1.add_stuff(bt3)
			page1.add_stuff(bt4)

			def onBt3Click(evt):
				""" input port radio button has been pressed. We redefine its action
				"""

				self.type = "IPort"
				page1.SetNext(page6)
				page6.SetNext(page5)
				page5.SetNext(None)
				page5.SetPrev(page1)
				page6.SetPrev(page1)

			def onBt4Click(evt):
				""" input port radio button has been pressed. We redefine its action
				"""

				self.type = "OPort"
				page1.SetNext(page7)
				page7.SetNext(page5)
				page5.SetNext(None)
				page5.SetPrev(page1)
				page7.SetPrev(page1)

			bt3.Bind(wx.EVT_RADIOBUTTON, onBt3Click)
			bt4.Bind(wx.EVT_RADIOBUTTON, onBt4Click)

		def python_path_call_back(evt):
			fn = evt.GetEventObject().GetValue()
			cls = Components.GetClass(fn)
			if inspect.isclass(cls):
				
                ### import are here because the simulator (PyDEVS or PyPDEVS) require it
				from DomainInterface.DomainBehavior import DomainBehavior
				from DomainInterface.DomainStructure import DomainStructure
				if not (issubclass(cls, DomainBehavior) or issubclass(cls, DomainStructure)):
					dlg = wx.MessageDialog(parent, _('The python file must contain a class that inherit of DomainBehavior or DomainStructure master class.\n Please choose a correct python file.'), _('Wizard Manager'), wx.ID_OK|wx.ICON_ERROR)
					dlg.ShowModal()
			else:
				dlg = wx.MessageDialog(parent, _('The python file not includes a class definition.\n Please choose a correct python file.'), _('Wizard Manager'), wx.ID_OK|wx.ICON_ERROR)
				dlg.ShowModal()

		def plugin_path_call_back(evt):
			fn = evt.GetEventObject().GetValue()
			if os.path.basename(fn) != 'plugins.py':
				dlg = wx.MessageDialog(parent, _('The name of plugin python file must be plugins.py.\n Please choose a correct plugin python file.'), _('Wizard Manager'), wx.ID_OK|wx.ICON_ERROR)
				dlg.ShowModal()

		# Create a page 2
		page2 = wizard_page(self, _('Atomic Model (AMD)'))
		sb1 = wx.StaticBoxSizer(wx.StaticBox(page2, wx.NewIdRef(), _('Properties')), orient=wx.VERTICAL)
		vb1 = wx.BoxSizer(wx.VERTICAL)
		vbox2 = wx.GridSizer(6, 2, 3, 3)
		bt5 = wx.CheckBox(page2, wx.NewIdRef(), _('Default python file'))
		bt5.SetValue(True)
		if wx.VERSION_STRING >= '4.0': bt5.SetToolTipString = bt5.SetToolTip 
		bt5.SetToolTipString(_("Choose python file from specific directory"))
		bt51 = wx.CheckBox(page2, wx.NewIdRef(), _('No plugin file'))
		if wx.VERSION_STRING >= '4.0': bt51.SetToolTipString = bt51.SetToolTip
		bt51.SetToolTipString(_("Choose plugin file from specific directory"))
		bt51.SetValue(True)
		cb0 = wx.ComboBox(page2, wx.NewIdRef(), _('Default'), choices=[_('Default'),_('Generator'),_('Viewer'), _('Collector')], style=wx.CB_READONLY)
		# filebrowse properties
		fb1 = filebrowse.FileBrowseButton(page2, wx.NewIdRef(), startDirectory=DOMAIN_PATH, labelText="", fileMask='Python File (*.py)|*.py|Compliled Python File (*.pyc)|*.pyc', toolTip=bt5.GetToolTip().GetTip(), changeCallback=python_path_call_back)
		fb12 = filebrowse.FileBrowseButton(page2, wx.NewIdRef(), startDirectory=DOMAIN_PATH, labelText="", fileMask='plugins.py', toolTip=bt51.GetToolTip().GetTip(), changeCallback=plugin_path_call_back)
		fb1.Enable(False)
		fb12.Enable(False)
		vbox2.AddMany([ (wx.StaticText(page2, wx.NewIdRef(), _('Label')), 0, wx.EXPAND|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL),
				(wx.TextCtrl(page2, wx.NewIdRef(), value = _("Atomic_Name"),validator=TextObjectValidator()), 0, wx.EXPAND|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL),
				(wx.StaticText(page2, wx.NewIdRef(), _('Specific Behavior')), 0, wx.EXPAND|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL),
				(cb0, 0,wx.EXPAND),
				(wx.StaticText(page2, wx.NewIdRef(), _('Inputs')), 0, wx.EXPAND|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL),
				(wx.SpinCtrl(page2, wx.NewIdRef(), '1', min=MIN_NB_PORT, max=MAX_NB_PORT), 0,wx.EXPAND),
				(wx.StaticText(page2, wx.NewIdRef(), _('Outputs')), 0, wx.EXPAND|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL),
				(wx.SpinCtrl(page2, wx.NewIdRef(), '1', min=MIN_NB_PORT, max=MAX_NB_PORT), 0,wx.EXPAND),
				(bt5,0),
				(fb1,0,wx.EXPAND|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL),
				(bt51,0),
				(fb12,0,wx.EXPAND|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
				])
		vb1.Add(vbox2,0,wx.EXPAND)
		sb1.Add(vb1,0,wx.EXPAND)

		page2.add_stuff(sb1)

		# Create a page 3
		page3 = wizard_page(self, _('Coupled Model (CMD)'))
		sb2 = wx.StaticBoxSizer(wx.StaticBox(page3, wx.NewIdRef(), _('Properties')), orient=wx.VERTICAL)
		vb2 = wx.BoxSizer(wx.VERTICAL)
		vbox3 = wx.GridSizer(6,2,3,3)
		bt6 = wx.CheckBox(page3, wx.NewIdRef(), _('Default python file'))
		if wx.VERSION_STRING >= '4.0': bt6.SetToolTipString = bt6.SetToolTip
		bt6.SetToolTipString(bt5.GetToolTip().GetTip())
		bt6.SetValue(True)
		bt61 = wx.CheckBox(page3, wx.NewIdRef(), _('No plugin file'))
		if wx.VERSION_STRING >= '4.0': bt61.SetToolTipString = bt61.SetToolTip
		bt61.SetToolTipString(bt51.GetToolTip().GetTip())
		bt61.SetValue(True)
		# filebrowse properties
		fb4 = filebrowse.FileBrowseButton(page3, wx.NewIdRef(), startDirectory=DOMAIN_PATH, labelText="", fileMask='Python File (*.py)|*.py|Compliled Python File (*.pyc)|*.pyc', toolTip=bt6.GetToolTip().GetTip(), changeCallback=plugin_path_call_back)
		fb41 = filebrowse.FileBrowseButton(page3, wx.NewIdRef(), startDirectory=DOMAIN_PATH, labelText="", fileMask='plugins.py', toolTip=bt61.GetToolTip().GetTip(), changeCallback=plugin_path_call_back)
		fb4.Enable(False)
		fb41.Enable(False)
		vbox3.AddMany([ (wx.StaticText(page3, wx.NewIdRef(), _('Label')), 0, wx.EXPAND|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL),
				(wx.TextCtrl(page3, wx.NewIdRef(), value = _("Coupled_Name"),validator=TextObjectValidator()), 0,  wx.EXPAND|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL),
				(wx.StaticText(page3, wx.NewIdRef(), _('Inputs')), 0,  wx.EXPAND|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL),
				(wx.SpinCtrl(page3, wx.NewIdRef(), '1', min = MIN_NB_PORT, max = MAX_NB_PORT), 0, wx.EXPAND),
				(wx.StaticText(page3, wx.NewIdRef(), _('Outputs')), 0,  wx.EXPAND|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL),
				(wx.SpinCtrl(page3, wx.NewIdRef(), '1', min = MIN_NB_PORT, max = MAX_NB_PORT), 0, wx.EXPAND),
				(bt6,0),
				(fb4,0,wx.EXPAND|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL),
				(bt61,0),
				(fb41,0,wx.EXPAND|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
				])
		#page3.add_stuff(vbox3)
		vb2.Add(vbox3,0,wx.EXPAND)
		sb2.Add(vb2,0,wx.EXPAND)
		page3.add_stuff(sb2)

		# Create a page 4_1
		page4_1 = wizard_page(self, _('Finish'))
		# save filebrowse
		init = os.path.join(domain_path, "%s.amd"%vbox2.GetItem(1).GetWindow().GetValue())
		fb2 = filebrowse.FileBrowseButton(	page4_1,
											wx.NewIdRef(),
											initialValue = init,
											fileMode=wx.SAVE,
											#startDirectory = DOMAIN_PATH,
											labelText = _("Save as"),
											fileMask = '*.amd')

		page4_1.add_stuff(fb2)

		# Create a page 4_2
		page4_2 = wizard_page(self, _('Finish'))
		init =  os.path.join(domain_path, "%s.cmd"%vbox3.GetItem(1).GetWindow().GetValue())
		# save filebrowse
		fb3 = filebrowse.FileBrowseButton(	page4_2,
											wx.NewIdRef(),
											initialValue = init,
											fileMode=wx.SAVE,
											#startDirectory = DOMAIN_PATH,
											labelText = _("Save as"),
											fileMask = '*.cmd')
		page4_2.add_stuff(fb3)

		# Create a page 5
		page5 = wizard_page(self, _('Finish'))
		page5.add_stuff(wx.StaticText(page5, wx.NewIdRef(), _('Port model has been created.')))

		### if left click on the DetachedFrame, port instance can be created
		if isinstance(parent.GetTopLevelParent(), Container.DetachedFrame):
			# Create a page 6
			page6 = wizard_page(self, _('Input Port'))
			sb3 = wx.StaticBoxSizer(wx.StaticBox(page6, wx.NewIdRef(), _('Properties')), orient = wx.VERTICAL)
			vb3 = wx.BoxSizer(wx.VERTICAL)
			#page6.add_stuff(wx.StaticBox(page6, -1, _('Properties')))
			cb_id1 = wx.CheckBox(page6, wx.NewIdRef(), _('Automatic Id'))
			spin_id1 = wx.SpinCtrl(page6, wx.NewIdRef(), str(parent.diagram.GetiPortCount()), min = MIN_NB_PORT, max = MAX_NB_PORT)
			cb_id1.SetValue(True)
			spin_id1.Enable(False)
			vbox6 = wx.GridSizer(2, 2, 3, 3)
			vbox6.AddMany([ (wx.StaticText(page6, wx.NewIdRef(), _('Label')), 0, wx.EXPAND|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL),
						(wx.TextCtrl(page6, wx.NewIdRef(), value = _("IPort ")), 0, wx.EXPAND|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL),
						(cb_id1, 0),
						(spin_id1, 0, wx.EXPAND)
						])
			vb3.Add(vbox6, 0, wx.EXPAND)
			sb3.Add(vb3, 0, wx.EXPAND)

			page6.add_stuff(sb3)
			#page6.add_stuff(vbox6)

			# Create a page 7
			page7 = wizard_page(self, _('Output Port'))
			#page7.add_stuff(wx.StaticBox(page7, -1, _('Properties')))
			sb4 = wx.StaticBoxSizer(wx.StaticBox(page7, wx.NewIdRef(), _('Properties')), orient=wx.VERTICAL)
			vb4 = wx.BoxSizer(wx.VERTICAL)
			cb_id2 = wx.CheckBox(page7, wx.NewIdRef(), _('Automatic Id'))
			spin_id2 = wx.SpinCtrl(page7, wx.NewIdRef(), str(parent.diagram.GetoPortCount()), min = MIN_NB_PORT, max = MAX_NB_PORT)
			cb_id2.SetValue(True)
			spin_id2.Enable(False)
			vbox7 = wx.GridSizer(2, 2, 3, 3)
			vbox7.AddMany([ (wx.StaticText(page7, wx.NewIdRef(), _('Label')), 0, wx.EXPAND|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL),
							(wx.TextCtrl(page7, wx.NewIdRef(), value = _("OPort ")), 0, wx.EXPAND|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL),
							(cb_id2,0),
							(spin_id2, 0,wx.EXPAND)
						])
			vb4.Add(vbox7,0,wx.EXPAND)
			sb4.Add(vb4,0,wx.EXPAND)

			page7.add_stuff(sb4)

		def onBt1Click(evt):
			""" Atomic radio button has been pressed. 
				We redefine its action.
			"""

			self.type = "Atomic"
			page1.SetNext(page2)
			page2.SetPrev(page1)
			page2.SetNext(page4_1)
			page4_1.SetPrev(page2)

		def onBt2Click(evt):
			""" Coupled radio button has been pressed. 
				We redefine its action.
			"""

			self.type = "Coupled"
			page1.SetNext(page3)
			page3.SetPrev(page1)
			page3.SetNext(page4_2)
			page4_2.SetPrev(page3)

		# event handler for check button
		def onBt5Check(evt):
			""" Python file selector is checked.
			"""
			fb1.Enable(not evt.GetEventObject().GetValue())

		# event handler for check button
		def onBt51Check(evt):
			""" Python file selector is checked.
			"""
			fb12.Enable(not evt.GetEventObject().GetValue())

		def onBt6Check(evt):
			""" Python file selector is checked.
			"""
			fb4.Enable(not evt.GetEventObject().GetValue())

		# event handler for check button
		def onBt61Check(evt):
			""" Python file selector is checked.
			"""
			fb41.Enable(not evt.GetEventObject().GetValue())
			
		def onCbId1(evt):
			"""
			"""
			spin_id1.Enable(not evt.GetEventObject().GetValue())
			
		def onCbId2(evt):
			"""
			"""
			spin_id2.Enable(not evt.GetEventObject().GetValue())

		def OnSpecificBehavior(evt):
			""" Give the control on the number of input and output form specific behavior choice
			"""

			### specific behavior choice
			val = evt.GetEventObject().GetValue()

			### if generator, 0 input and x output (1 is the default)
			if val == _('Generator'):

				### no input and
				vbox2.GetItem(5).GetWindow().SetValue(0)
				### update output
				if vbox2.GetItem(7).GetWindow().GetValue() == 0:
					vbox2.GetItem(7).GetWindow().SetValue(1)

				### Disable the choice
				vbox2.GetItem(4).GetWindow().Enable(False)
				vbox2.GetItem(5).GetWindow().Enable(False)
				### Enable the output choice
				vbox2.GetItem(6).GetWindow().Enable(True)
				vbox2.GetItem(7).GetWindow().Enable(True)

			### if collector, 0 output and x input (1 is the default)
			elif val in (_('Collector'),_('Viewer')):
				### no output
				vbox2.GetItem(7).GetWindow().SetValue(0)

				### update input
				if vbox2.GetItem(5).GetWindow().GetValue() == 0:
					vbox2.GetItem(5).GetWindow().SetValue(1)

				### Disable the choice
				vbox2.GetItem(7).GetWindow().Enable(False)
				vbox2.GetItem(6).GetWindow().Enable(False)
				### Enable the output choice
				vbox2.GetItem(5).GetWindow().Enable(True)
				vbox2.GetItem(4).GetWindow().Enable(True)

			### if Default, 1 output and input
			else:
				vbox2.GetItem(5).GetWindow().Enable(True)
				vbox2.GetItem(4).GetWindow().Enable(True)
				vbox2.GetItem(6).GetWindow().Enable(True)
				vbox2.GetItem(7).GetWindow().Enable(True)
				vbox2.GetItem(5).GetWindow().SetValue(1)
				vbox2.GetItem(7).GetWindow().SetValue(1)

		def OnInputAMDLabel(evt):
			fb2.SetValue(os.path.join(domain_path, "%s.amd"%evt.GetString()))

		def OnInputCMDLabel(evt):
			fb3.SetValue(os.path.join(domain_path, "%s.cmd"%evt.GetString()))

		# Binding
		bt1.Bind(wx.EVT_RADIOBUTTON, onBt1Click)
		bt2.Bind(wx.EVT_RADIOBUTTON, onBt2Click)
		bt5.Bind(wx.EVT_CHECKBOX, onBt5Check)
		bt51.Bind(wx.EVT_CHECKBOX, onBt51Check)
		bt6.Bind(wx.EVT_CHECKBOX, onBt6Check)
		bt61.Bind(wx.EVT_CHECKBOX, onBt61Check)
		### if left click on the DetachedFrame, port instance can be created
		if isinstance(parent.GetTopLevelParent(), Container.DetachedFrame):
			cb_id1.Bind(wx.EVT_CHECKBOX, onCbId1)
			cb_id2.Bind(wx.EVT_CHECKBOX, onCbId2)
		cb0.Bind(wx.EVT_COMBOBOX, OnSpecificBehavior)
		amd_input_label = vbox2.GetItem(1).GetWindow()
		amd_input_label.Bind(wx.EVT_TEXT, OnInputAMDLabel)
		cmd_input_label = vbox3.GetItem(1).GetWindow()
		cmd_input_label.Bind(wx.EVT_TEXT, OnInputCMDLabel)

		# Add some more pages
		self.add_page(page1)
		self.add_page(page2)
		self.add_page(page3)
		self.add_page(page4_1)
		self.add_page(page4_2)
		self.add_page(page5)

		### if left click on the DetachedFrame, port instance can be created
		if isinstance(parent.GetTopLevelParent(), Container.DetachedFrame):
			self.add_page(page6)
			self.add_page(page7)

		# define next and prev
		page1.SetNext(page2)
		page2.SetNext(page4_1)
		page2.SetPrev(page1)
		page3.SetPrev(page1)
		page3.SetNext(page4_2)
		page4_1.SetPrev(page2)
		page4_2.SetPrev(page3)
		page4_1.SetNext(None)
		page4_2.SetNext(None)

	def on_finished(self, evt):
		"""	Finish button has been pressed. 
			Give the specified values.
		"""

		# gridsizer depending on the type of choosing model
		if self.type in ('IPort', 'OPort'):
			page = self.pages[6] if self.type == 'IPort' else self.pages[7]
			gridSizer = page.sizer.GetItem(2).GetSizer().GetItem(0).GetSizer().GetItem(0).GetSizer()
			textCtrl = gridSizer.GetItem(1).GetWindow()
			self.label = textCtrl.GetValue()
			self.id = gridSizer.GetItem(3).GetWindow().GetValue()
			self.python_path = os.path.join(DOMAIN_PATH, 'Basic', self.type+'.py')

		else:

			if self.type == 'Atomic':
				gridSizer = self.pages[1].sizer.GetItem(2).GetSizer().GetItem(0).GetSizer().GetItem(0).GetSizer()
				filebrowse_python = gridSizer.GetItem(9).GetWindow()
				filebrowse_plugin = gridSizer.GetItem(11).GetWindow()
				filebrowse_model = self.pages[3].sizer.GetItem(2).GetWindow()

				### test if extention exists
				model_path = filebrowse_model.GetValue()
				if not model_path.endswith('.amd'):
					model_path +='.amd'

				# give the label
				textCtrl = gridSizer.GetItem(1).GetWindow()
				### give the python filename, inputs and outputs of corresponding model
				in_SpinCtrl = gridSizer.GetItem(5).GetWindow()
				out_SpinCtrl = gridSizer.GetItem(7).GetWindow()
				### give the specific behavior which can be Default, Generator or Collector (Scope and Disk)
				specific_behavior = gridSizer.GetItem(3).GetWindow()
				self.specific_behavior = specific_behavior.GetValue()

			elif self.type == 'Coupled':
				gridSizer = self.pages[2].sizer.GetItem(2).GetSizer().GetItem(0).GetSizer().GetItem(0).GetSizer()
				filebrowse_python = gridSizer.GetItem(7).GetWindow()
				filebrowse_plugin = gridSizer.GetItem(9).GetWindow()
				filebrowse_model = self.pages[4].sizer.GetItem(2).GetWindow()

				### test if extention exists
				model_path = filebrowse_model.GetValue()
				if not model_path.endswith('.cmd'):
					model_path +='.cmd'

				# give the label
				textCtrl = gridSizer.GetItem(1).GetWindow()
				### give the python filename, inputs and outputs of corresponding model
				in_SpinCtrl = gridSizer.GetItem(3).GetWindow()
				out_SpinCtrl = gridSizer.GetItem(5).GetWindow()

			self.model_path = os.path.abspath(model_path)
			self.python_path = filebrowse_python.GetValue()
			self.plugin_path = filebrowse_plugin.GetValue()

			self.label = textCtrl.GetValue()
			self.id = 0
			self.inputs = in_SpinCtrl.GetValue()
			self.outputs = out_SpinCtrl.GetValue()

			### model path exist ?
			if os.path.exists(self.model_path):
				msg = _("%s already exist.\nDo you want to rewrite it ?")%(self.model_path)
				dlg = wx.MessageDialog(self, msg, _('Wizard Manager'), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
				if dlg.ShowModal() in (wx.ID_NO, wx.ID_CANCEL):
					self.overwrite_flag = False

			if self.overwrite_flag:
				### create the model on the disk
				try:
					zout = zipfile.ZipFile(self.model_path, "w")
				except Exception as info:
					sys.stdout.write(_("ERROR: Enable to create Zip file in Wizard GUI (%s)"%info))
					return False
				else:
					if self.python_path == '':
						string = atomicCode(self.label) if self.type == 'Atomic' else coupledCode(self.label)

						python_name = os.path.basename(self.model_path).split('.')[0]

						txt = "%s.py"%python_name
						zout.writestr(txt, string)

						self.python_path = os.path.join(self.model_path,txt)
					else:
						py_file = os.path.basename(self.python_path)
						zout.write(self.python_path, py_file)

						self.python_path = os.path.join(self.model_path, py_file)

						### force model file (.amd or cmd) to have same name with the python file
						#ext = os.path.basename(self.model_path).split('.')[1]
						#self.model_path = os.path.join(os.path.dirname(self.model_path), "%s.%s"%(py_file.split('.')[0],ext))

					zout.writestr('DEVSimPyModel.dat', _("Call SaveFile method first!"))

					if self.plugin_path != '':
						zout.write(self.plugin_path, os.path.join('plugins',os.path.basename(self.plugin_path)))

					zout.close()
			else:
				### search python file in archive
				zin = zipfile.ZipFile(self.model_path, 'r')
				info_list = zin.infolist()
				### si le nom du fichier python py est le meme que le self.makeConnectionShape(sn, tn) nom du modèle .amd ou .cmd
				name = "%s.py"%os.path.splitext(os.path.basename(self.model_path))[0]
				if name in info_list:
					self.python_path = os.path.join(self.model_path, name)
				### sinon on cherche le .py dans le modèle en excluant plugins.py
				else:
					for item in info_list:
						name, ext = os.path.splitext(item.filename)
						if ext == ".py" and name != 'plugins':
							self.python_path = os.path.join(self.model_path, item.filename)
							### TODO: get class from python file and test with insepct module if is submodule of DomainBehavior
							break
				zin.close()

		return True

#if __name__ == '__main__':

	#app = wx.PySimpleApp()  # Start the application

	## Create wizard and add any kind pages you'd like
	#mywiz = ModelGeneratorWizard(_('DEVSimPy Model Generator'), img_filename = os.path.join(os.getcwd(),'bitmaps/IconeDEVSimPy.png'))
	## Show the main window
	#mywiz.run()
	## Cleanup
	#mywiz.Destroy()

	#app.MainLoop()
