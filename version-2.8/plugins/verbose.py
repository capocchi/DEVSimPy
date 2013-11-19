# -*- coding: utf-8 -*-

"""
	Authors: L. Capocchi (capocchi@univ-corse.fr)
	Date: 05/11/2011
	Description:
		Give some informations about the simulation process on the standard output.
		To use it, just send the SIM_VERBOSE event with the pluginmanager.trigger_event function and some parameters like msg, model or clock.
		Example:
			pluginmanager.trigger_event("SIM_VERBOSE", model=aDEVS, msg=0) for print informations when an external event (msg=0) occurs on the model aDEVS.
		For more details see the verbose.py file in plugins directory.
"""

import wx
import sys
import os

from DomainInterface import DomainBehavior, DomainStructure

import pluginmanager

global show_ext_trans
global show_int_trans
global show_clock
global show_coll

show_ext_trans = True
show_int_trans = True
show_clock = True
show_coll = True

class RedirectText(object):
	def __init__(self,aWxTextCtrl):
		self.out = aWxTextCtrl

	def write(self, string):
		if wx.Platform == '__WXGTK__':
			wx.CallAfter(self.out.WriteText, string)
		else:
			self.out.WriteText(string)

@pluginmanager.register("SIM_VERBOSE")
def LongRunningProcess(*args, **kwargs):
	""" Plugin function for simulation printing.
	"""

	global show_ext_trans
	global show_int_trans
	global show_clock
	global show_coll

	if kwargs.has_key('model') and kwargs.has_key('msg'):
		### changing frame content: need global
		global frame

		model = kwargs['model']
		msg = kwargs['msg']

		if hasattr(model, 'getBlockModel'):

			block = model.getBlockModel()

			txt = [""]

			if isinstance(model, DomainBehavior):
				if msg == 1 and show_ext_trans:
					txt = [	_("\n\tEXTERNAL TRANSITION: %s (%s)\n")%(block.label,model.myID),
							_("\t  New State: %s\n")%(model.state),
							_("\t  Input Port Configuration:\n")]


					txt.extend(["\t    %s: %s\n"%(m, model.peek(m)) for m in model.IPorts])

					if model.myTimeAdvance == INFINITY:
						txt.append(_("\t  Next scheduled internal transition at INFINITY\n"))
					else:
						txt.append(_("\t  Next scheduled internal transition at %f\n")%(model.myTimeAdvance))
				elif show_int_trans:

						txt = [	_("\n\tINTERNAL TRANSITION: %s (%s)\n")%(block.label,model.myID),
								_("\t  New State: %s\n")%(model.state),
								_("\t  Output Port Configuration:\n")]

						for m in model.OPorts:
							if m in model.myOutput.keys():
								txt.append("\t    %s: %s\n"%(m, model.myOutput[m]))
							else:
								txt.append("\t    %s: None\n" %(m))
						if model.myTimeAdvance == INFINITY:
							txt.append(_("\t  Next scheduled internal transition at INFINITY\n"))
						else:
							txt.append(_("\t  Next scheduled internal transition at %f\n")%(model.myTimeAdvance))

			elif isinstance(model, DomainStructure) and show_coll:
				txt = [_("\n\tCollision occured in %s, involving:\n")%(block.label)]
				txt.extend([_("    \t   %s\n")%(m.__class__.__name__) for m in model.immChildren])
				txt.append(_("\t  select chooses %s\n")%(kwargs['dstar'].__class__.__name__))

			sys.stdout.write(''.join(txt))

		else:
			sys.stdout.write(_("No verbose for %s dynamic model (%s)!\n")%(str(model), model.myID))

	elif kwargs.has_key('clock') and show_clock:
		txt = "\n"+"* "* 10+"CLOCK : %f \n"%(kwargs['clock'])
		sys.stdout.write(txt)

@pluginmanager.register("START_SIM_VERBOSE")
def start_print_data(*args, **kwargs):
	""" Start the log frame.
	"""

	parent = kwargs['parent']

	global frame

	frame = wx.Frame(parent, wx.ID_ANY, _("Simulation Report"))

	# Add a panel so it looks the correct on all platforms
	panel = wx.Panel(frame, wx.ID_ANY)
	log = wx.TextCtrl(panel, wx.ID_ANY, size=(300,100), style = wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL)

	# Add widgets to a sizer
	sizer = wx.BoxSizer(wx.VERTICAL)
	sizer.Add(log, 1, wx.ALL|wx.EXPAND, 5)
	panel.SetSizer(sizer)

	# redirect text here
	redir = RedirectText(log)
	sys.stdout=redir
	frame.Show()

class VerboseConfig(wx.Frame):
	def __init__(self, *args, **kwds):
		""" Constructor
		"""

		kwds["style"] = wx.CLOSE_BOX|wx.STAY_ON_TOP|wx.FRAME_NO_TASKBAR|wx.FRAME_FLOAT_ON_PARENT
		wx.Frame.__init__(self, *args, **kwds)
		self.sizer_3_staticbox = wx.StaticBox(self, -1, _("Display options"))
		self.checkbox_3 = wx.CheckBox(self, -1, _("Show clock"))
		self.checkbox_4 = wx.CheckBox(self, -1, _("Show external transition trace"))
		self.checkbox_5 = wx.CheckBox(self, -1, _("Show internal transition trace"))
		self.checkbox_6 = wx.CheckBox(self, -1, _("Show collision trace"))
		self.button_2 = wx.Button(self, wx.ID_CANCEL, "")
		self.button_3 = wx.Button(self, wx.ID_OK, "")

		self.__set_properties()
		self.__do_layout()

		self.Bind(wx.EVT_BUTTON, self.OnOk, id=wx.ID_OK)
		self.Bind(wx.EVT_BUTTON, self.OnCancel, id=wx.ID_CANCEL)

	def __set_properties(self):

		global show_ext_trans
		global show_int_trans
		global show_clock
		global show_coll

		_icon = wx.EmptyIcon()
		_icon.CopyFromBitmap(wx.Bitmap(os.path.join(ICON_PATH_16_16,DEVSIMPY_PNG), wx.BITMAP_TYPE_ANY))
		self.SetIcon(_icon)
		self.SetSize((433, 148))
		self.SetToolTipString(_("Display options for the plugin verbose"))
		self.checkbox_3.SetValue(show_clock)
		self.checkbox_4.SetValue(show_ext_trans)
		self.checkbox_5.SetValue(show_int_trans)
		self.checkbox_6.SetValue(show_coll)
		self.button_3.SetDefault()
		# end wxGlade

	def __do_layout(self):
		# begin wxGlade: MyFrame.__do_layout
		sizer_3 = wx.StaticBoxSizer(self.sizer_3_staticbox, wx.VERTICAL)
		sizer_4 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_3.Add(self.checkbox_3, 0, 0, 0)
		sizer_3.Add(self.checkbox_4, 0, 0, 0)
		sizer_3.Add(self.checkbox_5, 0, 0, 0)
		sizer_3.Add(self.checkbox_6, 0, 0, 0)
		sizer_4.Add(self.button_2, 1, wx.ALIGN_BOTTOM|wx.ALIGN_CENTER_HORIZONTAL, 0)
		sizer_4.Add(self.button_3, 1, wx.ALIGN_BOTTOM, 0)
		sizer_3.Add(sizer_4, 1, wx.EXPAND, 0)
		self.SetSizer(sizer_3)
		self.Layout()
		self.Centre()
		# end wxGlade

	def OnOk(self, evt):

		global show_ext_trans
		global show_int_trans
		global show_clock
		global show_coll

		show_clock = self.checkbox_3.GetValue()
		show_ext_trans = self.checkbox_4.GetValue()
		show_int_trans = self.checkbox_5.GetValue()
		show_coll = self.checkbox_6.GetValue()

		self.Close()

	def OnCancel(self, evt):
		self.Close()

def Config(parent):
	""" Plugin settings frame.
	"""

	config_frame = VerboseConfig(parent, -1, _("Verbose configuration"))
	config_frame.Show()