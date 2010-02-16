# -*- coding: utf-8 -*-

import wx
import wx.wizard as wizmod
import os

import  wx.lib.filebrowsebutton as filebrowse
from tempfile import gettempdir, gettempprefix, NamedTemporaryFile
from random import randint

padding = 5
MAX_NB_PORT = 50
MIN_NB_PORT = 0

_ = wx.GetTranslation

def atomicCode(label):		
	return [	'# -*- coding: utf-8 -*-\n',
							'from DomainInterface.DomainBehavior import DomainBehavior \n',
							'from Object import Message\n',
							'#    ======================================================================    #\n',
							'class %s(DomainBehavior):\n'%label,
							'\n',
							'\t def __init__(self):\n',
							'\t\t DomainBehavior.__init__(self)\n'
							'\n'
							'\t def extTransition(self):\n',
							'\t\t pass\n',
							'\n',
							'\t def outputFnc(self):\n',
							'\t\t pass\n',
							'\n',
							'\t def intTransition(self):\n',
							'\t\t pass\n',
							'\n',
							'\t def timeAdvance(self):\n',
							'\t\t pass\n'
			]

def coupledCode(label):
	return [	'# -*- coding: utf-8 -*-\n',
							'from DomainInterface.DomainStructure import DomainStructure\n',
							'#    ======================================================================    #\n',
							'class %s(DomainStructure):\n'%label,
							'\n',
							'\t def __init__(self):\n',
							'\t\t DomainStructure.__init__(self)\n'
			]

class wizard_page(wizmod.PyWizardPage):
	""" An extended panel obj with a few methods to keep track of its siblings.  
	This should be modified and added to the wizard.  Season to taste."""
	def __init__(self, parent, title):
		wx.wizard.PyWizardPage.__init__(self, parent)
		self.next = self.prev = None
		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.title = wx.StaticText(self, -1, title)
		self.title.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
		self.sizer.AddWindow(self.title, 0, wx.ALIGN_LEFT|wx.ALL, padding)
		self.sizer.AddWindow(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.ALL, padding)
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

class Wizard(wx.wizard.Wizard):
	"""Add pages to this wizard object to make it useful."""

	def __init__(self, title, parent, img_filename = ""):
		""" Constructor
		"""
		if img_filename and os.path.exists(img_filename):
				img = wx.Bitmap(img_filename)
		else:   
				img = wx.NullBitmap
		wx.wizard.Wizard.__init__(self, parent, -1, title, img)

		self.SetPageSize((400,300))

		# pages list
		self.pages = []

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
		self.on_close(evt)

	def on_finished(self, evt):
		"""Finish button has been pressed.  Give the specified values
		"""
		pass
	
	def on_close(self, evt):
		""" Close button has been pressed. Destroy the wizard.
		"""
		self.Destroy()

class ModelGeneratorWizard(Wizard):
	""" Model Generator Wizard Class.
	"""

	def __init__(self, *args, **kwargs):
		""" Constructor
		"""
		
		Wizard.__init__(self, *args, **kwargs)

        # properties of model
		self.type = "Atomic"
		self.label = ""
		self.inputs = 1
		self.outputs = 1
		self.python_path = ""
		self.model_path = ""
		
		# special properties for Port
		self.id = None
		
		# canvas parent
		parent = self.GetParent()

		# Create a page 1
		page1 = wizard_page(self, _('Type of Model'))
		bt1 = wx.RadioButton(page1, -1, _('Atomic Model'), style = wx.RB_GROUP )
		bt2 = wx.RadioButton(page1, -1, _('Coupled Model'))
		bt3 = wx.RadioButton(page1, -1, _('Input Port'))
		bt4 = wx.RadioButton(page1, -1, _('Output Port'))
		page1.add_stuff(wx.StaticText(page1, -1, _('Choose the type of model:')))
		page1.add_stuff(bt1)
		page1.add_stuff(bt2)
		page1.add_stuff(bt3)
		page1.add_stuff(bt4)

		# Create a page 2
		page2 = wizard_page(self, _('Atomic Model'))
		page2.add_stuff(wx.StaticBox(page2, -1, _('Properties')))
		vbox2 = wx.GridSizer(3, 2, 3, 3)
		bt5 = wx.CheckBox(page2, -1, _('Default python file'))
		bt5.SetValue(True)	
		vbox2.AddMany([ (wx.StaticText(page2, -1, _('Label')), 0, wx.EXPAND|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL),
				(wx.TextCtrl(page2, -1, value = _("Atomic_Name")), 0, wx.EXPAND|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL),
				(wx.StaticText(page2, -1, _('Inputs')), 0, wx.EXPAND|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL),
				(wx.SpinCtrl(page2, -1, '1', min=MIN_NB_PORT, max=MAX_NB_PORT), 0,wx.EXPAND),
				(wx.StaticText(page2, -1, _('Outputs')), 0, wx.EXPAND|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL),
				(wx.SpinCtrl(page2, -1, '1', min=MIN_NB_PORT, max=MAX_NB_PORT), 0,wx.EXPAND),
				(bt5,0)
				])
		page2.add_stuff(vbox2)

		# filebrowse properties
		domain_dir = os.path.join(os.path.dirname(os.getcwd()), DOMAIN_DIR)
		label = _("Existing python file")
		mask = '*.py'
		fb1 = filebrowse.FileBrowseButton(page2, -1, startDirectory=domain_dir, labelText=label, fileMask=mask)
		fb1.Enable(False)
		page2.add_stuff(fb1)

		# Create a page 3
		page3 = wizard_page(self, _('Coupled Model'))
		page3.add_stuff(wx.StaticBox(page3, -1, _('Properties')))
		vbox3 = wx.GridSizer(3,2,3,3)
		bt6 = wx.CheckBox(page3, -1, _('Default python file'))
		bt6.SetValue(True)
		vbox3.AddMany([ (wx.StaticText(page3, -1, _('Label')), 0, wx.EXPAND|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL),
				(wx.TextCtrl(page3, -1, value = _("Coupled_Name")), 0,  wx.EXPAND|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL),
				(wx.StaticText(page3, -1, _('Inputs')), 0,  wx.EXPAND|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL),
				(wx.SpinCtrl(page3, -1, '1', min = MIN_NB_PORT, max = MAX_NB_PORT), 0, wx.EXPAND),
				(wx.StaticText(page3, -1, _('Outputs')), 0,  wx.EXPAND|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL),
				(wx.SpinCtrl(page3, -1, '1', min = MIN_NB_PORT, max = MAX_NB_PORT), 0, wx.EXPAND),
				(bt6,0)
				])
		page3.add_stuff(vbox3)
		fb4 = filebrowse.FileBrowseButton(page3, -1, startDirectory=domain_dir, labelText=label, fileMask=mask)
		fb4.Enable(False)
		page3.add_stuff(fb4)

		# Create a page 4_1
		page4_1 = wizard_page(self, _('Finish'))
		# save filebrowse
		domain_dir = os.path.join(os.path.dirname(os.getcwd()), DOMAIN_DIR)
		init = "%s.amd"%vbox2.GetItem(1).GetWindow().GetValue()	
		fb2 = filebrowse.FileBrowseButton(	page4_1, 
											-1, 
											initialValue = init, 
											startDirectory = domain_dir, 
											labelText = "Save as",
											fileMask = '*.amd')
		page4_1.add_stuff(fb2)
		
		# Create a page 4_2
		page4_2 = wizard_page(self, _('Finish'))
		init = "%s.cmd"%vbox3.GetItem(1).GetWindow().GetValue()
		# save filebrowse
		fb3 = filebrowse.FileBrowseButton(	page4_2, 
											-1,
											initialValue = init, 
											startDirectory = domain_dir, 
											labelText = "Save as", 
											fileMask = '*.cmd')
		page4_2.add_stuff(fb3)

		# Create a page 5
		page5 = wizard_page(self, _('Finish'))
		page5.add_stuff(wx.StaticText(page5, -1, _('Port model has been create.')))

		# Create a page 6
		page6 = wizard_page(self, _('Input Port'))
		page6.add_stuff(wx.StaticBox(page6, -1, _('Properties')))
		cb_id1 = wx.CheckBox(page6, -1, _('Automatic Id'))
		spin_id1 = wx.SpinCtrl(page6, -1, str(parent.diagram.GetiPortCount()), min = MIN_NB_PORT, max = MAX_NB_PORT)
		cb_id1.SetValue(True)
		spin_id1.Enable(False)
		vbox6 = wx.GridSizer(2, 2, 3, 3)
		vbox6.AddMany([ (wx.StaticText(page6, -1, _('Label')), 0, wx.EXPAND|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL),
					(wx.TextCtrl(page6, -1, value = _("IPort ")), 0, wx.EXPAND|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL),
					(cb_id1,0),
					(spin_id1, 0,wx.EXPAND)
					])
		page6.add_stuff(vbox6)

		# Create a page 7
		page7 = wizard_page(self, _('Output Port'))
		page7.add_stuff(wx.StaticBox(page7, -1, _('Properties')))
		cb_id2 = wx.CheckBox(page7, -1, _('Automatic Id'))
		spin_id2 = wx.SpinCtrl(page7, -1, str(parent.diagram.GetoPortCount()), min = MIN_NB_PORT, max = MAX_NB_PORT)
		cb_id2.SetValue(True)
		spin_id2.Enable(False)
		vbox7 = wx.GridSizer(2, 2, 3, 3)
		vbox7.AddMany([ (wx.StaticText(page7, -1, _('Label')), 0, wx.EXPAND|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL),
						(wx.TextCtrl(page7, -1, value = _("OPort ")), 0, wx.EXPAND|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL),
						(cb_id2,0),
						(spin_id2, 0,wx.EXPAND)
					])
		page7.add_stuff(vbox7)

		def onBt1Click(evt):
			""" Atomic radio button has been pressed. We redefine its action
			"""

			self.type = "Atomic"
			page1.SetNext(page2)
			page2.SetPrev(page1)
			page2.SetNext(page4_1)
			page4_1.SetPrev(page2)

		def onBt2Click(evt):
			""" Coupled radio button has been pressed. We redefine its action
			"""

			self.type = "Coupled"
			page1.SetNext(page3)
			page3.SetPrev(page1)
			page3.SetNext(page4_2)
			page4_2.SetPrev(page3)

		def onBt3Click(evt):
			""" input port radio button has been pressed. We redefine its action
			"""

			self.type = "iPort"
			page1.SetNext(page6)
			page6.SetNext(page5)
			page5.SetNext(None)
			page5.SetPrev(page1)
			page6.SetPrev(page1)

		def onBt4Click(evt):
			""" input port radio button has been pressed. We redefine its action
			"""

			self.type = "oPort"
			page1.SetNext(page7)
			page7.SetNext(page5)
			page5.SetNext(None)
			page5.SetPrev(page1)
			page7.SetPrev(page1)

		# event handler for check button
		def onBt5Check(evt):
			""" Python file selector is cheked.
			"""
		
			if evt.GetEventObject().GetValue():
				fb1.Enable(False)
			else:
				fb1.Enable(True)

		def onBt6Check(evt):
			""" Python file selector is cheked.
			"""
		
			if evt.GetEventObject().GetValue():
				fb4.Enable(False)
			else:
				fb4.Enable(True)

		def onCbId1(evt):
			if evt.GetEventObject().GetValue():
				spin_id1.Enable(False)
			else:
				spin_id1.Enable(True)

		def onCbId2(evt):
			if evt.GetEventObject().GetValue():
				spin_id2.Enable(False)
			else:
				spin_id2.Enable(True)

		# Binding
		bt1.Bind(wx.EVT_RADIOBUTTON, onBt1Click)
		bt2.Bind(wx.EVT_RADIOBUTTON, onBt2Click)
		bt3.Bind(wx.EVT_RADIOBUTTON, onBt3Click)
		bt4.Bind(wx.EVT_RADIOBUTTON, onBt4Click)
		bt5.Bind(wx.EVT_CHECKBOX, onBt5Check)
		bt6.Bind(wx.EVT_CHECKBOX, onBt6Check)
		cb_id1.Bind(wx.EVT_CHECKBOX, onCbId1)
		cb_id2.Bind(wx.EVT_CHECKBOX, onCbId2)

		# Add some more pages
		self.add_page(page1)
		self.add_page(page2)
		self.add_page(page3)
		self.add_page(page4_1)
		self.add_page(page4_2)
		self.add_page(page6)
		self.add_page(page7)
		self.add_page(page5)

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
		"""Finish button has been pressed. Give the specified values
		"""
	
		# gridsizer depending on the type of choosing model
		if self.type == 'Atomic':
			gridSizer = self.pages[1].sizer.GetItem(3).GetSizer()
			filebrowse_python = self.pages[1].sizer.GetItem(4).GetWindow()
			filebrowse_model = self.pages[3].sizer.GetItem(2).GetWindow()
			self.python_path = filebrowse_python.GetValue()
			self.model_path = filebrowse_model.GetValue()
			if not self.model_path.endswith('.amd'):
				self.model_path +='.amd'
		elif self.type == 'Coupled':
			gridSizer = self.pages[2].sizer.GetItem(3).GetSizer()
			filebrowse_model = self.pages[4].sizer.GetItem(2).GetWindow()
			self.model_path = filebrowse_model.GetValue()
			if not self.model_path.endswith('.cmd'):
				self.model_path +='.cmd'
		elif self.type == 'iPort':
			gridSizer = self.pages[5].sizer.GetItem(3).GetSizer()
		else:
			gridSizer = self.pages[6].sizer.GetItem(3).GetSizer()
			

		if self.type in ('Atomic', 'Coupled'):

			# give the label, inputs and outputs of corresponding model
			textCtrl = gridSizer.GetItem(1).GetWindow()
			in_SpinCtrl = gridSizer.GetItem(3).GetWindow()
			out_SpinCtrl = gridSizer.GetItem(5).GetWindow()
			
			self.label = textCtrl.GetValue()
			self.id = 0
			self.inputs = in_SpinCtrl.GetValue()
			self.outputs = out_SpinCtrl.GetValue()

			# validation of the python file
			if self.python_path == '':
				fileName = os.path.join(os.path.dirname(self.model_path),"%s.py"%self.label)
				f = open(fileName,'w')
				try:
					if self.type == 'Atomic':
						f.writelines(atomicCode(self.label))
					else:
						f.writelines(coupledCode(self.label))
					f.seek(0)
				finally:
					f.close()
			
				self.python_path = fileName

				# if __init__ file dont exist, we create it because it's necessary for python_path futur importation
				#fn = os.path.join(os.path.dirname(self.model_path),'__init__.py')
				#if not os.path.exists(fn):
					#f = open(fn, 'w')
					#f.writelines(['__all__ = [\n','\t ]'])
					#f.close()
		else:
			textCtrl = gridSizer.GetItem(1).GetWindow()
			self.label = textCtrl.GetValue()
			self.id = gridSizer.GetItem(3).GetWindow().GetValue()

			basic_path = os.path.join(os.path.dirname(os.getcwd()), DOMAIN_DIR, 'Basic')
			if self.type == 'iPort':
				self.python_path = os.path.join(basic_path, 'IPort.py')
			else:
				self.python_path = os.path.join(basic_path, 'OPort.py')

		return True

if __name__ == '__main__':

	DOMAIN_DIR = os.getcwd()

	app = wx.PySimpleApp()  # Start the application
	
	# Create wizard and add any kind pages you'd like
	mywiz = ModelGeneratorWizard(_('DEVSimPy Model Generator'), img_filename = os.path.join(os.getcwd(),'bitmaps/IconeDEVSimPy.png'))
	# Show the main window
	mywiz.run() 
	# Cleanup
	mywiz.Destroy()
	
	app.MainLoop()