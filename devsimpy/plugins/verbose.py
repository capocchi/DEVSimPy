# -*- coding: utf-8 -*-

"""
	Authors: L. Capocchi (capocchi@univ-corse.fr)
	Date: 05/11/2011
	Description:
		Give some informations about the simulation process on the standard output.
		To use it, just send the SIM_VERBOSE event with the PluginManager.trigger_event function and some parameters like msg, model or clock.
		Example:
			PluginManager.trigger_event("SIM_VERBOSE", model=aDEVS, msg=0) for print informations when an external event (msg=0) occurs on the model aDEVS.
		The configuration dialog now also provides an option for writing the
		verbose output to a text file; if enabled, all messages are appended to the
		specified filename.
		For more details see the verbose.py file in plug-ins directory.
"""

import wx
import wx.richtext
import sys
import os
import builtins

import gettext
_ = gettext.gettext

from PluginManager import PluginManager
from config import GLOBAL_SETTINGS

# Constants
INFINITY = float('inf')
ICON_PATH = GLOBAL_SETTINGS['ICON_PATH']
DEVSIMPY_ICON = GLOBAL_SETTINGS['DEVSIMPY_ICON']

global show_ext_trans
global show_int_trans
global show_clock
global show_coll

# path of the file where verbose output should be appended.  An empty
# string disables file logging.
global logfile_path

# list to store verbose output lines for display after simulation
global verbose_log

show_ext_trans = True
show_int_trans = True
show_clock = True
show_coll = True
logfile_path = ""
verbose_log = []

if 'PyPDEVS' in getattr(builtins, 'DEFAULT_DEVS_DIRNAME', ''):
	raise AssertionError("Verbose plug-in is not compatible with the PyPDEVS simulation kernel!")

class RedirectText(object):
	def __init__(self,aWxTextCtrl):
		self.out = aWxTextCtrl

	def write(self, string):
		if wx.Platform == '__WXGTK__':
			wx.CallAfter(self.out.WriteText, string)
		else:
			self.out.WriteText(string)

	def flush(self):
		pass

@PluginManager.register("SIM_VERBOSE")
def LongRunningProcess(*args, **kwargs):
	""" Plug-in function for simulation printing.
	"""

	global show_ext_trans
	global show_int_trans
	global show_clock
	global show_coll

	if 'model' in kwargs and 'msg' in kwargs:
		### changing frame content: need global
		global frame
		global logfile_path
		global verbose_log

		model = kwargs['model']
		msg = kwargs['msg']

		if hasattr(model, 'getBlockModel'):

			block = model.getBlockModel()

			txt = [""]

			### here because DEVS package can be changed during DEVSimPy running
			from DomainInterface import DomainBehavior, DomainStructure

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
				txt = [_("\n\tCollision occurred in %s, involving:\n")%(block.label)]
				txt.extend([_("    \t   %s\n")%(m.__class__.__name__) for m in model.immChildren])
				txt.append(_("\t  select chooses %s\n")%(kwargs['dstar'].__class__.__name__))

			output = ''.join(txt)
			sys.stdout.write(output)
			verbose_log.append(output)
			if logfile_path:
				try:
					with open(logfile_path, 'a', encoding='utf-8') as f:
						f.write(output)
				except Exception:
					pass

		else:
			msg2 = _("No verbose for %s dynamic model (%s)!\n")%(str(model), model.myID)
			sys.stdout.write(msg2)
			verbose_log.append(msg2)
			if logfile_path:
				try:
					with open(logfile_path, 'a', encoding='utf-8') as f:
						f.write(msg2)
				except Exception:
					pass

	elif 'clock' in kwargs and show_clock:
		txt = "\n"+"* "* 10+"CLOCK : %f \n"%(kwargs['clock'])
		sys.stdout.write(txt)
		verbose_log.append(txt)
		if logfile_path:
			try:
				with open(logfile_path, 'a', encoding='utf-8') as f:
					f.write(txt)
			except Exception:
				pass

# start_print_data used to be part of LongRunningProcess; it should be a
# separate handler for the START_SIM_VERBOSE event.  The original refactor
# accidentally left the code inside LongRunningProcess, causing a KeyError when
# the event was triggered without a 'parent' key.  Move it out and make the
# parent lookup defensive.

@PluginManager.register("START_SIM_VERBOSE")
def start_print_data(*args, **kwargs):
	"""Start the log frame for simulation verbose output.

	This function is called when the GUI requests that the verbose log window
	be shown.  The <parent> keyword argument is optional; if it is missing the
	window will be created without a valid parent (wx will handle that).
	"""

	parent = kwargs.get('parent', None)

	global frame
	global verbose_log

	frame = wx.Frame(parent, wx.ID_ANY, _("Simulation Report"))
	# create a toolbar with copy icon
	tb = frame.CreateToolBar()
	copy_tool = tb.AddTool(wx.ID_COPY, _("Copy"), wx.ArtProvider.GetBitmap(wx.ART_COPY, wx.ART_TOOLBAR))
	saveas_tool = tb.AddTool(wx.ID_SAVEAS, _("Save As"), wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE, wx.ART_TOOLBAR))
	tb.Realize()
	
	# Add a panel so it looks the correct on all platforms
	panel = wx.Panel(frame, wx.ID_ANY)
	log = wx.richtext.RichTextCtrl(panel, wx.ID_ANY, size=wx.DefaultSize, style=wx.richtext.RE_READONLY|wx.richtext.RE_MULTILINE)

	# copy button action
	def on_copy(event):
		text = log.GetValue()
		if wx.TheClipboard.Open():
			wx.TheClipboard.SetData(wx.TextDataObject(text))
			wx.TheClipboard.Close()
		else:
			wx.MessageBox(_("Unable to open clipboard"), _("Error"))
	
	tb.Bind(wx.EVT_TOOL, on_copy, copy_tool)


	# Filter controls
	filter_sizer = wx.BoxSizer(wx.HORIZONTAL)
	filter_label = wx.StaticText(panel, wx.ID_ANY, _("Filter by model name:"))
	filter_text = wx.TextCtrl(panel, wx.ID_ANY, "", style=wx.TE_PROCESS_ENTER)
	filter_button = wx.Button(panel, wx.ID_ANY, _("Filter"))
	clear_button = wx.Button(panel, wx.ID_ANY, _("Show All"))
	
	# Clock navigation
	clock_label = wx.StaticText(panel, wx.ID_ANY, _("Go to clock:"))
	clock_combo = wx.Choice(panel, wx.ID_ANY)
	
	filter_sizer.Add(filter_label, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
	filter_sizer.Add(filter_text, 1, wx.ALL|wx.EXPAND, 5)
	filter_sizer.Add(filter_button, 0, wx.ALL, 5)
	filter_sizer.Add(clear_button, 0, wx.ALL, 5)
	filter_sizer.Add(clock_label, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
	filter_sizer.Add(clock_combo, 0, wx.ALL, 5)

	# Extract clock times
	clock_times = []
	for i, line in enumerate(verbose_log):
		if "CLOCK :" in line:
			parts = line.split("CLOCK :")
			if len(parts) > 1:
				time_str = parts[1].strip().rstrip('\n')
				try:
					time_val = float(time_str)
					clock_times.append((time_val, i))
				except ValueError:
					pass
	clock_times.sort()
	clock_choices = ["All"] + [str(time) for time, idx in clock_times]
	clock_combo.SetItems(clock_choices)
	clock_combo.SetSelection(0)

	current_max_index = None
	current_clock_positions = []
	model_colors = {}  # Dictionary to store model name -> color mapping
	
	# Color palette for different models
	color_palette = [
		wx.Colour(255, 0, 0),      # Red
		wx.Colour(0, 128, 0),      # Green
		wx.Colour(0, 0, 255),      # Blue
		wx.Colour(255, 165, 0),    # Orange
		wx.Colour(128, 0, 128),    # Purple
		wx.Colour(0, 128, 128),    # Teal
		wx.Colour(255, 192, 203),  # Pink
		wx.Colour(165, 42, 42),    # Brown
		wx.Colour(0, 100, 0),      # Dark Green
		wx.Colour(139, 69, 19),    # Saddle Brown
	]

	def get_model_color(model_name):
		"""Get or assign a color to a model name"""
		if model_name not in model_colors:
			color_index = len(model_colors) % len(color_palette)
			model_colors[model_name] = color_palette[color_index]
		return model_colors[model_name]

	def update_display(filter_str="", max_index=None):
		import re
		if max_index is None:
			max_index = len(verbose_log)
		log.Clear()
		current_clock_positions.clear()
		clock_indices = {idx for time, idx in clock_times}
		
		# Create styles
		clock_attr = wx.richtext.RichTextAttr()
		clock_attr.SetTextColour(wx.Colour(0, 0, 255))  # Blue for clock lines
		clock_attr.SetFontWeight(wx.FONTWEIGHT_BOLD)
		
		normal_attr = wx.richtext.RichTextAttr()
		normal_attr.SetTextColour(wx.Colour(0, 0, 0))  # Black for normal lines
		
		for j, line in enumerate(verbose_log[:max_index]):
			if not filter_str or filter_str.lower() in line.lower() or "clock" in line.lower():
				if j in clock_indices:
					current_clock_positions.append(log.GetLastPosition())
					log.SetDefaultStyle(clock_attr)
					log.WriteText(line)
				else:
					log.SetDefaultStyle(normal_attr)
					# Check for model transitions and apply coloring to model names
					model_match = re.search(r'(EXTERNAL TRANSITION|INTERNAL TRANSITION|Collision occurred in):\s+(.+?)\s+\(', line)
					if model_match:
						model_name = model_match.group(2)
						# Write text before model name
						prefix_end = model_match.start(2)
						log.WriteText(line[:prefix_end])
						# Write model name with assigned color
						model_attr = wx.richtext.RichTextAttr()
						model_attr.SetTextColour(get_model_color(model_name))
						model_attr.SetFontWeight(wx.FONTWEIGHT_BOLD)
						log.SetDefaultStyle(model_attr)
						log.WriteText(model_name)
						# Write rest of line with normal style
						log.SetDefaultStyle(normal_attr)
						log.WriteText(line[model_match.end(2):])
					else:
						log.WriteText(line)

	# Display the stored verbose output
	update_display()

	def on_filter(event):
		filter_str = filter_text.GetValue().strip()
		update_display(filter_str)

	def on_clear(event):
		filter_text.SetValue("")
		update_display()

	def on_clock_select(event):
		selection = clock_combo.GetSelection()
		if selection == 0:  # All
			pass  # already showing all
		else:
			index = selection - 1
			if index < len(current_clock_positions):
				log.ShowPosition(current_clock_positions[index])

	filter_button.Bind(wx.EVT_BUTTON, on_filter)
	clear_button.Bind(wx.EVT_BUTTON, on_clear)
	filter_text.Bind(wx.EVT_TEXT_ENTER, on_filter)
	filter_text.Bind(wx.EVT_KILL_FOCUS, on_filter)
	clock_combo.Bind(wx.EVT_CHOICE, on_clock_select)

	filter_button.Bind(wx.EVT_BUTTON, on_filter)
	clear_button.Bind(wx.EVT_BUTTON, on_clear)
	filter_text.Bind(wx.EVT_TEXT_ENTER, on_filter)
	filter_text.Bind(wx.EVT_KILL_FOCUS, on_filter)

	# Add menu bar with Save As option
	menubar = wx.MenuBar()
	filemenu = wx.Menu()
	saveas_item = filemenu.Append(wx.ID_SAVEAS, "&Save As\tCtrl+S")
	menubar.Append(filemenu, "&File")
	frame.SetMenuBar(menubar)

	def on_save_as(event):
		with wx.FileDialog(frame, _("Save verbose log"), wildcard=_("Text files (*.txt)|*.txt"), style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
			if fileDialog.ShowModal() == wx.ID_CANCEL:
				return
			pathname = fileDialog.GetPath()
			try:
				with open(pathname, 'w', encoding='utf-8') as file:
					file.write(log.GetValue())
			except IOError:
				wx.LogError(_("Cannot save current data in file '%s'.") % pathname)

	frame.Bind(wx.EVT_MENU, on_save_as, saveas_item)
	# also bind toolbar save button
	tb.Bind(wx.EVT_TOOL, on_save_as, saveas_tool)

	# Add widgets to a sizer
	sizer = wx.BoxSizer(wx.VERTICAL)
	sizer.Add(filter_sizer, 0, wx.EXPAND)
	sizer.Add(log, 1, wx.ALL|wx.EXPAND, 5)
	panel.SetSizer(sizer)

	frame.SetSize((600, 400))
	frame.Show()

class VerboseConfig(wx.Frame):
	def __init__(self, *args, **kwds):
		""" Constructor with optimized UI
		"""

		kwds["style"] = wx.STAY_ON_TOP | wx.DEFAULT_FRAME_STYLE
		wx.Frame.__init__(self, *args, **kwds)
		self.SetSize((600, 450))

		self.panel = wx.Panel(self, wx.ID_ANY)

		# ===== TITLE SECTION =====
		title_font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
		self.title = wx.StaticText(self.panel, wx.ID_ANY, _("Simulation Verbose Output Configuration"))
		self.title.SetFont(title_font)
		title_color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_HOTLIGHT)
		self.title.SetForegroundColour(title_color)

		# ===== DISPLAY OPTIONS SECTION =====
		self.sizer_display_box = wx.StaticBox(self.panel, wx.ID_ANY, _("Display Options"))
		self.checkbox_clock = wx.CheckBox(self.panel, wx.ID_ANY, _("Show clock"))
		self.checkbox_ext = wx.CheckBox(self.panel, wx.ID_ANY, _("Show external transition trace"))
		self.checkbox_int = wx.CheckBox(self.panel, wx.ID_ANY, _("Show internal transition trace"))
		self.checkbox_collision = wx.CheckBox(self.panel, wx.ID_ANY, _("Show collision trace"))

		# Add tooltips for better UX
		self.checkbox_clock.SetToolTip(_("Display simulation clock/time for each event"))
		self.checkbox_ext.SetToolTip(_("Display when external events are received"))
		self.checkbox_int.SetToolTip(_("Display when internal transitions occur"))
		self.checkbox_collision.SetToolTip(_("Display when messages collide in ports"))

		# ===== FILE OUTPUT SECTION =====
		self.sizer_file_box = wx.StaticBox(self.panel, wx.ID_ANY, _("File Logging"))
		self.checkbox_file = wx.CheckBox(self.panel, wx.ID_ANY, _("Write verbose output to file"))
		self.checkbox_file.SetToolTip(_("Save all verbose output to a log file"))

		self.text_filename = wx.TextCtrl(self.panel, wx.ID_ANY, "", style=wx.TE_PROCESS_ENTER)
		self.button_browse = wx.Button(self.panel, wx.ID_ANY, _("Browse…"), size=(100, -1))

		# ===== BUTTON SECTION =====
		self.button_help = wx.Button(self.panel, wx.ID_HELP, _("Help"), size=(100, -1))
		self.button_cancel = wx.Button(self.panel, wx.ID_CANCEL, _("Cancel"), size=(100, -1))
		self.button_ok = wx.Button(self.panel, wx.ID_OK, _("Apply"), size=(100, -1))

		self.__set_properties()
		self.__do_layout()

		self.Bind(wx.EVT_BUTTON, self.OnOk, id=wx.ID_OK)
		self.Bind(wx.EVT_BUTTON, self.OnCancel, id=wx.ID_CANCEL)
		self.Bind(wx.EVT_BUTTON, self.OnHelp, id=wx.ID_HELP)
		self.Bind(wx.EVT_BUTTON, self.OnBrowse, self.button_browse)
		self.Bind(wx.EVT_CHECKBOX, self.OnFileCheckbox, self.checkbox_file)

	def __set_properties(self):
		""" Set properties for all widgets
		"""

		global show_ext_trans
		global show_int_trans
		global show_clock
		global show_coll

		_icon = wx.Icon()
		_icon.CopyFromBitmap(wx.Bitmap(os.path.join(ICON_PATH, DEVSIMPY_ICON), wx.BITMAP_TYPE_ANY))

		self.SetIcon(_icon)
		self.SetToolTip(_("Display options for the verbose plug-in"))
		self.checkbox_clock.SetValue(show_clock)
		self.checkbox_ext.SetValue(show_ext_trans)
		self.checkbox_int.SetValue(show_int_trans)
		self.checkbox_collision.SetValue(show_coll)

		# file output initial state
		self.checkbox_file.SetValue(bool(logfile_path))
		self.text_filename.SetValue(logfile_path)
		self.text_filename.Enable(bool(logfile_path))

		self.button_ok.SetDefault()

	def __do_layout(self):
		""" Layout of the frame with improved organization
		"""

		main_sizer = wx.BoxSizer(wx.VERTICAL)

		# ===== TITLE =====
		main_sizer.Add(self.title, 0, wx.ALL, 10)

		# ===== DISPLAY OPTIONS SECTION =====
		display_sizer = wx.StaticBoxSizer(self.sizer_display_box, wx.VERTICAL)
		display_sizer.Add(self.checkbox_clock, 0, wx.ALL | wx.EXPAND, 5)
		display_sizer.Add(self.checkbox_ext, 0, wx.ALL | wx.EXPAND, 5)
		display_sizer.Add(self.checkbox_int, 0, wx.ALL | wx.EXPAND, 5)
		display_sizer.Add(self.checkbox_collision, 0, wx.ALL | wx.EXPAND, 5)
		main_sizer.Add(display_sizer, 0, wx.ALL | wx.EXPAND, 10)

		# ===== FILE LOGGING SECTION =====
		file_desc = wx.StaticText(self.panel, wx.ID_ANY, 
			_("Log file path (leave empty to disable file logging):"))
		small_font = wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL)
		file_desc.SetFont(small_font)
		file_desc.SetForegroundColour(wx.Colour(100, 100, 100))

		file_sizer = wx.StaticBoxSizer(self.sizer_file_box, wx.VERTICAL)
		file_sizer.Add(self.checkbox_file, 0, wx.ALL | wx.EXPAND, 5)
		
		desc_sizer = wx.BoxSizer(wx.VERTICAL)
		desc_sizer.Add(file_desc, 0, wx.ALL, 5)
		file_sizer.Add(desc_sizer, 0, wx.ALL | wx.EXPAND, 0)

		path_sizer = wx.BoxSizer(wx.HORIZONTAL)
		path_sizer.Add(self.text_filename, 1, wx.ALL | wx.EXPAND, 5)
		path_sizer.Add(self.button_browse, 0, wx.ALL, 5)
		file_sizer.Add(path_sizer, 0, wx.ALL | wx.EXPAND, 0)
		main_sizer.Add(file_sizer, 0, wx.ALL | wx.EXPAND, 10)

		# ===== BUTTONS =====
		button_sizer = wx.BoxSizer(wx.HORIZONTAL)
		button_sizer.Add(self.button_help, 0, wx.RIGHT, 10)
		button_sizer.AddStretchSpacer()
		button_sizer.Add(self.button_cancel, 0, wx.RIGHT, 5)
		button_sizer.Add(self.button_ok, 0, wx.RIGHT, 0)
		main_sizer.Add(button_sizer, 0, wx.ALL | wx.EXPAND, 10)

		self.panel.SetSizer(main_sizer)
		self.Centre()

	def OnOk(self, evt):
		""" Apply button clicked - save settings
		"""

		global show_ext_trans
		global show_int_trans
		global show_clock
		global show_coll
		global logfile_path

		show_clock = self.checkbox_clock.GetValue()
		show_ext_trans = self.checkbox_ext.GetValue()
		show_int_trans = self.checkbox_int.GetValue()
		show_coll = self.checkbox_collision.GetValue()

		# file logging
		if self.checkbox_file.GetValue():
			logfile_path = self.text_filename.GetValue()
		else:
			logfile_path = ""

		self.Close()

	def OnCancel(self, evt):
		""" Cancel button clicked - close without saving
		"""
		self.Close()

	def OnHelp(self, evt):
		""" Help button clicked - show help dialog
		"""
		help_msg = _(
			"Verbose Plug-in Configuration\n\n"
			"Display Options:\n"
			"• Show clock: Display simulation time for each event\n"
			"• Show external transition trace: Log external state changes\n"
			"• Show internal transition trace: Log internal state changes\n"
			"• Show collision trace: Log message collisions on ports\n\n"
			"File Logging:\n"
			"• Enable 'Write verbose output to file' to save all output\n"
			"• Use 'Browse' to select or create a log file\n"
			"• Leave file path empty to disable file logging\n\n"
			"Click 'Apply' to save your settings."
		)
		dlg = wx.MessageDialog(self, help_msg, _("Verbose Plug-in Help"), 
			wx.OK | wx.ICON_INFORMATION)
		dlg.ShowModal()
		dlg.Destroy()

	def OnFileCheckbox(self, evt):
		""" Enable/disable file path controls based on checkbox
		"""
		enabled = self.checkbox_file.GetValue()
		self.text_filename.Enable(enabled)
		self.button_browse.Enable(enabled)

	def OnBrowse(self, evt):
		""" Browse button clicked - show file dialog
		"""
		with wx.FileDialog(self, message=_("Select log file"),
			defaultDir=os.getcwd(),
			defaultFile=self.text_filename.GetValue(),
			style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as dlg:
			if dlg.ShowModal() == wx.ID_OK:
				self.text_filename.SetValue(dlg.GetPath())

def Config(parent):
	""" Plug-in settings frame.
	"""

	config_frame = VerboseConfig(parent, wx.ID_ANY, _("Verbose plug-in"), style = wx.DEFAULT_FRAME_STYLE)
	config_frame.Show()