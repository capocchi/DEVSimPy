# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# PropertiesGridCtrl.py ---
#                     --------------------------------
#                        Copyright (c) 2013
#                       Laurent CAPOCCHI
#                      University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 19/11/13
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

import os
import sys
import re
import zipfile

import inspect
if not hasattr(inspect, 'getargspec'):
    inspect.getargspec = inspect.getfullargspec
    
import wx
import wx.grid as gridlib
from wx.lib import wordwrap
import wx.gizmos as gizmos
import wx.lib.imagebrowser as ib

### Phoenix
GridCellRenderer = gridlib.PyGridCellRenderer if wx.VERSION_STRING < '4.0' else gridlib.GridCellRenderer
GridTableBase = gridlib.PyGridTableBase if wx.VERSION_STRING < '4.0' else gridlib.GridTableBase
EditableListBox = gizmos.EditableListBox if wx.VERSION_STRING < '4.0' else wx.adv.EditableListBox

import Container
import Components
import Menu
import ZipManager

from Mixins.Attributable import Attributable
from Mixins.Achievable import Achievable
from Utilities import RGBToHEX
from Patterns.Observer import Subject

from collections import OrderedDict

wx.OPEN = wx.OPEN if wx.VERSION_STRING < '4.0' else wx.FD_OPEN
wx.CHANGE_DIR = wx.CHANGE_DIR if wx.VERSION_STRING < '4.0' else wx.FD_CHANGE_DIR

_ = wx.GetTranslation

###------------------------------------------------------------------------------
class DictionaryEditor(wx.Dialog):
	def __init__(self, parent, id, title, values):
		wx.Dialog.__init__(self, parent, id, _("Dictionary editor"), pos = (50,50), size = (250, 250), style = wx.DEFAULT_FRAME_STYLE)

		self.parent = parent

		panel = wx.Panel(self, wx.NewIdRef())
		vbox = wx.BoxSizer(wx.VERTICAL)

		self.elb = EditableListBox(panel, wx.NewIdRef(), title)

		D = eval(values) if values!='' else {}

		self.elb.SetStrings(list(map(lambda a,b: "(\"%s\",\"%s\")"%(str(a),str(b)), list(D.keys()), list(D.values()))))

		vbox.Add(self.elb, 1, wx.EXPAND | wx.ALL)
		panel.SetSizer(vbox)
		self.Center()

		self.elb.Bind(wx.EVT_LIST_END_LABEL_EDIT, self.OnExcludesChange)

		### just for window http://wiki.wxpython.org/wxPython%20Platform%20Inconsistencies#New_frames_not_showing_widgets_correctly_under_MS_Windows
		e = wx.SizeEvent(self.GetSize())
		self.ProcessEvent(e)

	def OnExcludesChange(self, evt):
		"""
		"""
		### try to catch exception for new expression in the list
		try:
			txt = evt.GetText()

			### if val not empty and not color
			if txt != '' and not txt.startswith('#'):
				eval(txt)

		except Exception as info:
			dial = wx.MessageDialog(self, _("Error editing attribute: %s")%info, _("Dictionary manager"), wx.OK | wx.ICON_ERROR)
			dial.ShowModal()

		evt.Skip()

	def GetValue(self):
		""" Return the list object
		"""

		try:
			return dict(eval, self.elb.GetStrings())
		except SyntaxError:
			return dict(eval, dict(repr, eval(str(self.elb.GetStrings()))))
		except Exception as info:
			return info

	def GetValueAsString(self):
		""" Return the list as string
		"""

		r = {}
		for elem in self.elb.GetStrings():

			k,v = eval(str(elem))

			### is digit or float
			if re.match(r"[-+]?[0-9\.]+$", str(v)) is not None:
				v = float(v)

			### if key is tuple, restore tuple
			try:
				e = eval(k)
				if isinstance(e, tuple): k=e
			### if k is not tuple, eval gives an error
			except Exception:
				pass

			r.update({k:v})

		return r if isinstance(r, Exception) else str(r)

###
class ListEditor(wx.Dialog):
	def __init__(self, parent, id, title, values):
		wx.Dialog.__init__(self, parent, id, _("List editor"), pos = (50,50), size = (250, 250), style = wx.DEFAULT_FRAME_STYLE)

		self.parent = parent

		panel = wx.Panel(self, wx.NewIdRef())
		vbox = wx.BoxSizer(wx.VERTICAL)

		self.elb = EditableListBox(panel, wx.NewIdRef(), title)

		L = eval(values) if values!='' else []

		self.elb.SetStrings([str(a) for a in L])

		vbox.Add(self.elb, 1, wx.EXPAND | wx.ALL)
		panel.SetSizer(vbox)
		self.Center()

		#self.elb.Bind(wx.EVT_LIST_END_LABEL_EDIT, self.OnExcludesChange)

		### just for window http://wiki.wxpython.org/wxPython%20Platform%20Inconsistencies#New_frames_not_showing_widgets_correctly_under_MS_Windows
		e = wx.SizeEvent(self.GetSize())
		self.ProcessEvent(e)

	def OnExcludesChange(self, evt):
		"""
		"""
		### try to catch exception for new expression in the list
		try:
			txt = evt.GetText()

			### if txt not empty and not color
			if txt != '' and not txt.startswith('#'):
				eval(txt)

		except Exception as info:
			dial = wx.MessageDialog(self, _("Error editing attribute: %s")%info, _("List manager"), wx.OK | wx.ICON_ERROR)
			dial.ShowModal()

		evt.Skip()

	def GetValue(self):
		""" Return the list object
		"""

		try:
			return [eval(a) for a in self.elb.GetStrings()]
		except SyntaxError:
			return [eval(b) for b in [repr(a) for a in eval(str(self.elb.GetStrings()))]]
		except Exception as info:
			return info

	def GetValueAsString(self):
		""" Return the list as string
		"""
		#r = self.GetValue()

		r = []
		for elem in self.elb.GetStrings():

			### is digit or float
			if re.match(r"[-+]?[0-9\.]+$", elem) is not None:
				r.append(eval(elem))
			else:
				r.append(str(elem))

		if isinstance(r, Exception):
			return r
		else:
			return str(r)

###------------------------------------------------------
class CodeCB(wx.Choicebook):
	def __init__(self, parent, id, model=None):
		wx.Choicebook.__init__(self, parent, id)

		self.parent  = parent

		cls = Components.GetClass(model.python_path)

		if inspect.isclass(cls):

			info = _("Unable to load sources")

			try:a = inspect.getdoc(cls)
			except:a = info

			try:b = inspect.getsource(cls)
			except:b = info

			try: c = inspect.getsource(cls.__init__)
			except: c = info

			try: d = inspect.getsource(cls.intTransition)
			except: d = info

			try: e = inspect.getsource(cls.extTransition)
			except: e = info

			try: f = inspect.getsource(cls.outputFnc)
			except: f = info

			try: g = inspect.getsource(cls.timeAdvance)
			except: g = info

			try:
				h = inspect.getsource(cls.finish) if  hasattr(cls, 'finish') else "\tpass"
			except:
				h = info

			pageTexts = {_('Doc'): a,
						 _('Class'): b,
						 _('Constructor'): c,
						 _('Internal Transition'): d,
						 _('External Transition'): e,
						 _('Output Function'): f,
						 _('Time Advance Function'): g,
						 _('Finish Function'): h
						}
		else:
			pageTexts = {_("Importing Error"): _("Error trying to import the module: %s.\nChange the python path by clicking in the above 'python_path' cell.\n %s"%(model.python_path,str(cls)))}

		# Now make a bunch of panels for the choice book
		for nameFunc in pageTexts:
			win = wx.Panel(self)
			box = wx.BoxSizer( wx.HORIZONTAL)
			st = wx.TextCtrl(win, wx.NewIdRef(), '', style = wx.TE_MULTILINE)
			try:
				txt = str(pageTexts[nameFunc], errors='replace')
			except TypeError:
				txt = pageTexts[nameFunc]
			finally:
				if txt:
					st.AppendText(txt)
					st.ShowPosition(wx.TOP)
					st.SetEditable(False)
					box.Add(st,1,wx.EXPAND)
					win.SetSizer(box)
				else:
					sys.stdout.write(_("Method %s of class %s unknown!\n"%(nameFunc,cls.__name__)))

			self.AddPage(win, nameFunc)

			# don't work in Windows
			#if wx.Platform == '__WXGTK__':
			#	self.SetSelection(5)

		#self.Bind(wx.EVT_CHOICEBOOK_PAGE_CHANGED, self.OnPageChanged)
		#self.Bind(wx.EVT_CHOICEBOOK_PAGE_CHANGING, self.OnPageChanging)


	def OnPageChanged(self, event):
		event.Skip()

	def OnPageChanging(self, event):
		event.Skip()


### --------------------------------------------------------------
class CutomGridCellAutoWrapStringRenderer(GridCellRenderer):
	""" Custom rendere for property grid
	"""
	def __init__(self):
		""" Constructor
		"""
		GridCellRenderer.__init__(self)

	def Draw(self, grid, attr, dc, rect, row, col, isSelected):
		text = grid.GetCellValue(row, col)

		### if cell is path
		if os.path.isdir(os.path.dirname(text)):
			text = os.path.basename(text)

		dc.SetFont( attr.GetFont() )
		text = wordwrap.wordwrap(text, grid.GetColSize(col), dc, breakLongWords = False)
		hAlign, vAlign = attr.GetAlignment()
		if isSelected:
			bg = grid.GetSelectionBackground()
			fg = grid.GetSelectionForeground()
		else:
			bg = attr.GetBackgroundColour()
			fg = attr.GetTextColour()
		dc.SetTextBackground(bg)
		dc.SetTextForeground(fg)
		dc.SetBrush(wx.Brush(bg, wx.BRUSHSTYLE_SOLID))
		dc.SetPen(wx.TRANSPARENT_PEN)
		dc.DrawRectangleRect(rect) if wx.VERSION_STRING < '4.0' else wx.DC.DrawRectangle(dc, rect)
		grid.DrawTextRectangle(dc, text, rect, hAlign, vAlign)

	def GetBestSize(self, grid, attr, dc, row, col):
		""" Get best size depending of the colom type
		"""
		text = grid.GetCellValue(row, col)
		dc.SetFont(attr.GetFont())
		text = wordwrap.wordwrap(text, grid.GetColSize(col), dc, breakLongWords = False)
		### if colom info (mutliline)
		if col == 2:
			w, h, lineHeight = dc.GetMultiLineTextExtent(text) if wx.VERSION_STRING < '4.0' else dc.GetFullMultiLineTextExtent(text)
			return wx.Size(w, h)
		### if colom label
		elif col == 0:
			w, h, lineHeight, a = dc.GetFullTextExtent(text)
			return wx.Size(w, h)
		### if colom choices elem
		else:
			return attr.GetSize()

	def Clone(self):
		return CutomGridCellAutoWrapStringRenderer()

#----------------------------------------------------------------------------------
class CustomDataTable(GridTableBase):
	""" CustomDataTable(model)
	"""

	def __init__(self):
		""" Constructor
		"""

		GridTableBase.__init__(self)

		### model initialized by Populate
		self.model = None

		### TODO rendre les keys (ormis la 1) générique en fonction des noms des variables
		self.info = { _('Unknown information') : _("Please get information of DEVS attribute \nthrough its class constructor using @ symbole. \n For example: @attribut_name : informations"),
						'python_path' : _("This is the path of python file.\nYou can change this path in order to change the behavior of the model."),
						'label' : _("This is the name of model.\nYou can change this name by clicking on its value field"),
						'pen' : _("This is the color and size of pen used to trace the model shape.\nYou can change these properies by clicking on its value field."),
						'fill' : _("This is the background color of the model shape.\nYou can change this properties by clicking on its value filed."),
						'font': _("This is the font of the label.")
						}

		self.colLabels = [_('Attribute'),_('Value'),_('Information')]

		### default graphical attribute label
		self.infoBlockLabelList = [_('Name'), _('Label position'), _('Color and size of pen'), _('Background color'), _('Font label'), _('Background image'),_('Input port'), _('Output port')]

		self.nb_graphic_var = len(self.infoBlockLabelList)

		### stock the bad field (pink) to control the bad_filename_path_flag in Update of Block model
		self.bad_flag = {}

	def Populate(self, model):
		""" Populate the data and dataTypes lists.
		"""

		self.model = model
		self.data = []
		self.dataTypes = []
		self.nb_behavior_var = 0
		self.nb_graphic_var = 0

		n = len(model.GetAttributes())             ### graphical attributes number
		m = len(self.infoBlockLabelList)           ### docstring graphical attributes number

		### if user define new graphical attributes we add their description in infoBlockLabelList
		if m != n:
			self.infoBlockLabelList.extend(model.GetAttributes()[m:])

		### default behavioral attributes dictionary
		if model.args:
			infoBlockBehavioralDict = dict([(attr, _('Unknown information')) for attr in list(model.args.keys())])
		else:
			infoBlockBehavioralDict = {}
		
		### if user code the information of behavioral attribute in docstring of class with @ or - symbol, we update the infoBlockBehavioralDict
		if hasattr(model, 'python_path') and infoBlockBehavioralDict != {}:
			### cls object from python file
			cls = Components.GetClass(model.python_path)

			### Behavioral sorted values fields
			args_in_constructor = Components.GetArgs(cls)

			### if cls is class
			if inspect.isclass(cls):
				regex = re.compile('[@|-][param]*[\s]*([a-zA-Z0-9-_\s]*)[=|:]([a-zA-Z0-9-_\s]+)')
				doc = cls.__init__.__doc__ or ""
				for attr, val in regex.findall(doc):
					### attr could be in model.args
					if attr.strip() in model.args:
						infoBlockBehavioralDict.update({attr.strip():val.strip()})
		else:
			args_in_constructor = None

		### Port class has specific attribute
		if isinstance(model, Container.Port):
			self.infoBlockLabelList.insert(4,_('Id number'))

		### Graphical values fields
		for i in range(n):
			attr = str(model.GetAttributes()[i])
			val = getattr(model, attr)
			if attr == "image_path":
				val = os.path.basename(val)
			self.data.append([attr, val, self.infoBlockLabelList[i]])
			self.dataTypes.append(self.GetTypeList(val))
		
		for attr_name,info in sorted(infoBlockBehavioralDict.items()):
			
			val = model.args[attr_name]

			### if the type of value has changed for an instance (edition of the code block), we reinitilize the value 
			if args_in_constructor and attr_name in list(args_in_constructor.keys()):
				val_in_constructor = args_in_constructor[attr_name]
				t1 = type(val)
				t2 = type(val_in_constructor)
			
				if t1 != t2 and (t1 not in (str,str) and t2 not in (str,str)):
					### spcecial case for OrderedDict as attribute in __init__ function
					if isinstance(val, dict) and isinstance(val_in_constructor, OrderedDict):
						val = OrderedDict(val.items())
					else:
						val = val_in_constructor
				### if val is tab and the len has been changed
				### when dict, the value on PropertiesGridCtrl is tuple like ('key', 'value')
				elif isinstance(val, (tuple,dict)) and len(val_in_constructor) != 0:
					if len(val_in_constructor) != len(val):
						val = val_in_constructor
				### if filename attr exist in the model and if it is 'result' by default, this means that the attr is randomly initialized
				### into the constructor of the model (its the case for MessageCollector...). So, we get the random path from a devs instance and
				### insert it into the prop field
				elif attr_name.lower() == 'filename' and val == 'result':
					cls = Components.GetClass(model.python_path)
					devs = cls()
					val = getattr(devs,attr_name)
					model.args[attr_name] = val
				else:
					pass
			else:
				pass
				
			self.data.append([attr_name, val, info])
			self.dataTypes.append(self.GetTypeList(val))
			self.nb_behavior_var += 1

		if args_in_constructor:
			for attr_name, val in list(args_in_constructor.items()):
				if attr_name not in list(infoBlockBehavioralDict.keys()):
					model.args[attr_name] = val
					self.data.append([attr_name, val, _('Unknown information')])
					self.dataTypes.append(self.GetTypeList(val))
					self.nb_behavior_var += 1
		else:
			sys.stdout.write(_("Args in constructor is none\n"))

		### Python File Path
		if hasattr(model, 'python_path'):
			val = os.path.basename(self.model.python_path)
			self.data.append(['python_path', val, _("Python file path")])
			self.dataTypes.append(self.GetTypeList(val))
			self.nb_behavior_var += 1

	def GetAttr(self, row, col, kind):
		"""
		"""

		attr = gridlib.GridCellAttr()
		val = self.GetValue(row, col)

		### format font of attr
		if col == 0:
			attr.SetReadOnly(True)
			attr.SetFont(wx.Font(10, 70, 0, 700))
			#attr.SetBackgroundColour("light blue")
		elif col == 2:
			attr.SetReadOnly(True)
			attr.SetFont(wx.Font(10, 70, 0, 400))
		else:
			### load color in cell for pen and fill
			if isinstance(val, list):
				### if elem in list begin by #. It is color.
				for s in [a for a in [str(b) for b in val] if a.startswith('#')]:
					attr.SetBackgroundColour(s)
					break

		### TODO : a ameliorer car bad_filename_path_flag ne prend pas en compte python_path.
		### relechir sur comment faire en sorte de ne pas donner la main a la simulation
		### en fonction de la validite des deux criteres plus bas

		### if the path dont exists, background color is red
		try:

			### if the type of cell is string
			if isinstance(val, str):

				if col == 1:

					v = self.GetValue(row, 0)

					### if bad filename (for instance generator)
					m = re.match('[a-zA-Z]*(ile)[n|N](ame)[_-a-zA-Z0-9]*', v, re.IGNORECASE)

					### if filename is match and not exist (ensuring that the filename are extension)
					if m is not None and not os.path.exists(self.GetValue(row, 1)) and os.path.splitext(self.GetValue(row, 1))[-1] != '':
						self.bad_flag.update({v:False})
						attr.SetBackgroundColour("pink")

					### if the python path is not found
					if v == "python_path":
						### si un le modèle est un fichier python et que le path n'existe pas ou si c'est un amd ou cmd et que le fichier modèle n'existe pas
						if (not os.path.exists(self.model.python_path) and not zipfile.is_zipfile(self.model.model_path)) or\
							(not os.path.exists(self.model.model_path) and zipfile.is_zipfile(self.model.model_path)):
							self.bad_flag.update({v:False})
							attr.SetBackgroundColour("pink")

			return attr

		except Exception as info:
			sys.stderr.write(_('Error in GetAttr : %s'%info))
			return

	def GetTypeList(self, val):
		"""
		"""

		if isinstance(val, bool):
			return [gridlib.GRID_VALUE_STRING, gridlib.GRID_VALUE_BOOL, gridlib.GRID_VALUE_STRING]
		elif isinstance(val,int):
			return [gridlib.GRID_VALUE_STRING, gridlib.GRID_VALUE_NUMBER + ':0,1000000', gridlib.GRID_VALUE_STRING]
		elif isinstance(val,float):
			return [gridlib.GRID_VALUE_STRING, gridlib.GRID_VALUE_FLOAT + ':10,6', gridlib.GRID_VALUE_STRING]
		elif isinstance(val,list):
			return [gridlib.GRID_VALUE_STRING,'list', gridlib.GRID_VALUE_STRING]
		elif isinstance(val,dict):
			return [gridlib.GRID_VALUE_STRING,'dict', gridlib.GRID_VALUE_STRING]
		elif isinstance(val, tuple):
			if isinstance(val[0], int):
				return [gridlib.GRID_VALUE_STRING, gridlib.GRID_VALUE_CHOICEINT+':'+str(val)[1:-1].replace(' ',''), gridlib.GRID_VALUE_STRING]
			else:
				return [gridlib.GRID_VALUE_STRING, gridlib.GRID_VALUE_CHOICE+':'+str(val)[1:-1].replace(' ','').replace('\'',''), gridlib.GRID_VALUE_STRING]
		else:
			return [gridlib.GRID_VALUE_STRING, gridlib.GRID_VALUE_STRING, gridlib.GRID_VALUE_STRING]

	def GetNumberRows(self):
		return len(self.data)

	def GetNumberCols(self):
		return len(self.data[0])

	def IsEmptyCell(self, row, col):
		try:
			return not self.data[row][col]
		except IndexError:
			return True

	# Get/Set values in the table.  The Python version of these
	# methods can handle any data-type, (as long as the Editor and
	# Renderer understands the type too,) not just strings as in the
	# C++ version.
	def GetValue(self, row, col):

		try:
			return self.data[row][col][0] if isinstance(self.data[row][col], tuple) else self.data[row][col]
		except Exception as e:
			return None

	def SetValue(self, row, col, value):
		"""
		"""
		### Attention si value est une expression et qu'elle contient des contantes litterale il faut que celle ci soient def par le ConstanteDialog

		#if wx.Platform == '__WXGTK__':
		## conserve le type de données dans la table :-)
		init_type = self.dataTypes[row][1]
		
		if value == "":
			self.data[row][col] = value
		elif 'double' in init_type:
			self.data[row][col] = float(value)
		elif 'list' in init_type:
			self.data[row][col] = list(eval(str(value)))
		elif 'dict' in init_type:
			self.data[row][col] = dict(eval(str(value)))
		elif 'long' in init_type:
			self.data[row][col] = int(value)
		elif 'bool' in init_type:
			self.data[row][col] = bool(value)
		elif 'choice' in init_type:
			### old_value casted in list to manage it
			old_value = list(self.data[row][col])
			selected_item = str(value).replace('\'','')
			### find index of selected item in old list
			index = old_value.index(selected_item)
			### delete selected item in old list to insert it in first place
			del old_value[index]
			old_value.insert(0, selected_item)
			### assign new tuple
			self.data[row][col] = tuple(old_value)
		else:
			self.data[row][col] = value

	# Called when the grid needs to display labels
	def GetColLabelValue(self, col):
		return self.colLabels[col]

	# Called to determine the kind of editor/renderer to use by
	# default, doesn't necessarily have to be the same type used
	# natively by the editor/renderer if they know how to convert.
	def GetTypeName(self, row, col):
		return self.dataTypes[row][col]

	# Called to determine how the data can be fetched and stored by the
	# editor and renderer.  This allows you to enforce some type-safety
	# in the grid.
	def CanGetValueAs(self, row, col, typeName):
		return typeName == self.dataTypes[row][col].split(':')[0]

	def CanSetValueAs(self, row, col, typeName):
		return self.CanGetValueAs(row, col, typeName)

	def UpdateRowBehavioralData(self, model):

		### delete only behavioral rows
		m = gridlib.GridTableMessage(self,  # the table
								gridlib.GRIDTABLE_NOTIFY_ROWS_DELETED, # what
								self.nb_graphic_var,  # from here
								self.nb_behavior_var) # how many

		self.Populate(model)

		self.GetView().ProcessTableMessage(m)

		msg = gridlib.GridTableMessage(self, gridlib.GRIDTABLE_REQUEST_VIEW_GET_VALUES )
		self.GetView().ProcessTableMessage(msg)

	def GetInformation(self, info):
		"""
		"""
		try:
			return self.info[info] if info in list(self.info.keys()) else None
		except :
			return None

#--------------------------------------------------------------------------
class PropertiesGridCtrl(gridlib.Grid, Subject):
	""" wx.Grid of model's properties
	"""

	###
	def __init__(self, parent):
		""" Constructor
		"""

		gridlib.Grid.__init__(self, parent, wx.NewIdRef())
		Subject.__init__(self)

		# local copy
		self.parent = parent

		### subject init
		self.canvas = self.parent.canvas
		self.__state = {}
		self.attach(self.parent.model)

		# Table setting
		table = CustomDataTable()
		table.Populate(self.parent.model)
		self.SetTable(table, False)

		### number of row and column from table
		nb_cols = table.GetNumberCols()
		nb_rows = table.GetNumberRows()

		self.SetRowLabelSize(0)
		self.SetMargins(0,0)
		self.EnableDragRowSize(False)

		### based on OnSize of AttributeEditor frame
		### define width of columns from column table number.
		width, height = self.parent.GetSize()
		width /= nb_cols
		for col in range(nb_cols):
			self.SetColSize(int(col), int(width))

		for i in range(nb_rows):
			self.SetReadOnly(i, 0, True)
			self.SetReadOnly(i, 2, True)
			self.SetCellBackgroundColour(i, 0, "#f1f1f1")

		### Custom render for display short path name and allows multiline for info
		self.SetDefaultRenderer(CutomGridCellAutoWrapStringRenderer())

		self.Bind(gridlib.EVT_GRID_CELL_CHANGE if wx.VERSION_STRING < '4.0' else gridlib.EVT_GRID_CELL_CHANGED , self.OnAcceptProp)
		self.Bind(gridlib.EVT_GRID_SELECT_CELL, self.OnSelectProp)
		self.Bind(wx.EVT_ENTER_WINDOW, self.OnEnterWindow)
		self.Bind(gridlib.EVT_GRID_CELL_RIGHT_CLICK, self.OnRightClick)
		self.Bind(gridlib.EVT_GRID_COL_SORT, self.OnGridColSort)

		# put a tooltip on a column label
		self.GetGridColLabelWindow().Bind(wx.EVT_MOTION,self.onMouseOverColLabel)
		# put a tooltip on a row label
		self.InstallGridHint(self, table.GetInformation)

	###
	def InstallGridHint(self, grid, rowcolhintcallback=None):
		"""
		"""
		prev_rowcol = [None, None]
		def OnMouseMotion(evt):
			# evt.GetRow() and evt.GetCol() would be nice to have here,
			# but as this is a mouse event, not a grid event, they are not
			# available and we need to compute them by hand.
			x, y = grid.CalcUnscrolledPosition(evt.GetPosition())
			row = grid.YToRow(y)
			col = grid.XToCol(x)
			table = grid.GetTable()
			
			if (row,col) != prev_rowcol and row >= 0 and col >= 0:
				prev_rowcol[:] = [row,col]
				hinttext = rowcolhintcallback(table.GetValue(row, col))
				### display the python path on tooltip
				if self.GetCellValue(row, 1).endswith(('.py','pyc','csv','dat','txt')):
					if col == 1:
						hinttext = self.parent.model.python_path 
				elif hinttext is None:
					hinttext = ''

				### display the data path on tooltip
				if self.GetCellValue(row, 1).endswith(('csv','dat','txt')) or self.GetCellValue(row, 0).lower() == 'filename':
					if col == 1:
						hinttext = self.parent.model.args.get('fileName',None) or self.parent.model.args.get('filename',None) or self.parent.model.args.get('FileName',None) 
				elif hinttext is None:
					hinttext = ''

				grid.GetGridWindow().SetToolTipString(hinttext) if wx.VERSION_STRING < '4.0' else grid.GetGridWindow().SetToolTip(hinttext)
			evt.Skip()
		grid.GetGridWindow().Bind(wx.EVT_MOTION, OnMouseMotion)

	###
	def OnRightClick(self, event):
		""" Right click has been invoked
		"""

		row = event.GetRow()
		col = event.GetCol()
		pos = event.GetPosition()
		prop = self.GetCellValue(row, col-1)

		### menu popup onlu on the column 1
		if col == 1:
			menu = Menu.PropertiesCtrlPopupMenu(self, row, col, pos)
			self.PopupMenu(menu, pos)
			menu.Destroy()

	def OnGridColSort(self, event):
		"""
		"""
		try:
			self.SetSortingColumn(event.Getcol())
		except AttributeError:
			pass
	###
	def OnEditCell(self, evt):
		"""
		"""
		self.SelectProp(evt.GetEventObject())

	###
	def OnInsertCell(self, evt):
		"""
		"""
		evt = evt.GetEventObject()
		row, col = evt.GetRow(), evt.GetCol()

		dlg = wx.TextEntryDialog(self, _('Paste new value from clipboard'),_('Paste value'), self.GetCellValue(row,col))
		if dlg.ShowModal() == wx.ID_OK:
			self.SetCellValue(row, 1, str(dlg.GetValue()))
			self.AcceptProp(row, col)
		dlg.Destroy()

	###
	def OnClearCell(self, event):
		"""
		"""
		obj = event.GetEventObject()
		row = obj.row
		col = obj.col
		val = self.GetCellValue(row,col)
		self.SetCellValue(row,col,"")

		self.AcceptProp(row,col)

	###
	def OnEnterWindow(self, event):
		"""
		"""
		#self.parent.SetFocus()
		pass

	###
	def onMouseOver(self, event):
		"""
		Displays a tooltip over any cell in a certain column
		"""
		# Use CalcUnscrolledPosition() to get the mouse position within the
		# entire grid including what's offscreen
		# This method was suggested by none other than Robin Dunn
		x, y = self.CalcUnscrolledPosition(event.GetX(),event.GetY())
		coords = self.XYToCell(x, y)
		col = coords[1]
		row = coords[0]

		if wx.VERSION_STRING >= '4.0': event.GetEventObject().SetToolTipString == event.GetEventObject().SetToolTip

		# Note: This only sets the tooltip for the cells in the column
		if col == 1:
			msg = "This is Row %s, Column %s!" % (row, col)
			event.GetEventObject().SetToolTipString(msg)
		else:
			event.GetEventObject().SetToolTipString('')

	###
	def onMouseOverColLabel(self, event):
		""" Displays a tooltip when mousing over certain column labels
		"""

		col = self.XToCol(event.GetX(), event.GetY())

		if col == 0: txt = _('Name of property')
		elif col == 1: txt = _('Value of property')
		else: txt = _('Information about property')

		win = self.GetGridColLabelWindow()
		win.SetToolTipString(txt) if wx.VERSION_STRING < '4.0' else win.SetToolTip(txt)
		event.Skip()

	###
	def onMouseOverRowLabel(self, event):
		""" Displays a tooltip on a row label
		"""

		row = self.YToRow(event.GetY())

		if row == 0: txt = ("Row One")
		elif row == 1: txt = _('Row Two')
		else: txt = ""

		self.GetGridRowLabelWindow().SetToolTipString(txt)
		event.Skip()

	###
	def AcceptProp(self, row, col):
		""" change the value and notify it
		"""
		table= self.GetTable()
		typ = table.dataTypes[row][1]
		prop = self.GetCellValue(row, 0)
		val = table.GetValue(row, 1)

		### just to adjust tuple type
		if 'choice' in typ:
			val = table.data[row][1]

		self.__state[prop] = val
		self.notify()

		self.canvas.Undo()

	###
	def OnAcceptProp(self, evt):
		"""
		"""
		self.AcceptProp(evt.GetRow(),1)
		evt.Skip()

	###
	def SelectProp(self, evt):
		"""
		"""

		row, col, pos= evt.GetRow(), evt.GetCol(), evt.GetPosition()

		table = self.GetTable()

		typ = table.dataTypes[row][1]
		prop = self.GetCellValue(row, 0)

		if prop == 'fill' or re.findall("[.]*color[.]*", prop, flags=re.IGNORECASE):
			val = self.GetCellValue(row, 1)
			dlg = wx.ColourDialog(self.parent)
			dlg.GetColourData().SetChooseFull(True)
			if dlg.ShowModal() == wx.ID_OK:
				data = dlg.GetColourData()
				val = str([RGBToHEX(data.GetColour().Get())])
				self.SetCellValue(row,1,val)
			else:
				dlg.Destroy()
				return False

			dlg.Destroy()

			self.AcceptProp(row, col)

		elif prop == 'font':
			val = eval(self.GetCellValue(row, 1))
			default_font = wx.Font(val[0], val[1] , val[2], val[3], False, val[4])
			data = wx.FontData()
			if sys.platform == 'win32':
				data.EnableEffects(True)
			data.SetAllowSymbols(False)
			data.SetInitialFont(default_font)
			data.SetRange(10, 30)
			dlg = wx.FontDialog(self.parent, data)
			if dlg.ShowModal() == wx.ID_OK:
				data = dlg.GetFontData()
				font = data.GetChosenFont()
				color = data.GetColour()
				val = [font.GetPointSize(), font.GetFamily(), font.GetStyle(), font.GetWeight(), font.GetFaceName()]
				self.SetCellValue(row,1,str(val))
			else:
				dlg.Destroy()
				return False

			dlg.Destroy()

			self.AcceptProp(row, col)

		elif prop == 'label':
			import LabelGUI

			d = LabelGUI.LabelDialog(self.parent, self.parent.model)
			d.SetCanvas(self.parent.canvas)
			d.ShowModal()

			self.SetCellValue(row,1,str(self.parent.model.label))
			self.AcceptProp(row, col)

		elif prop == 'image_path':
			
			dlg = ib.ImageDialog(self, os.path.join(HOME_PATH))
			dlg.Centre()
			
			if dlg.ShowModal() == wx.ID_OK:
				val = os.path.normpath(dlg.GetFile())
				if val != self.GetCellValue(row, 1):
					self.SetCellValue(row, 1, val)
					self.canvas.UpdateShapes([self.parent.model])
			else:
				dlg.Destroy()
				return False

			dlg.Destroy()

			self.AcceptProp(row, col)

		elif 'filename' in str(prop).lower():
			wcd = _('Data files All files (*)|*')
			val = self.GetCellValue(row, 1)
			default_dir = os.path.dirname(val) if os.path.exists(os.path.dirname(val)) else HOME_PATH
			dlg = wx.FileDialog(self, message=_("Select file ..."), defaultDir=default_dir, defaultFile="", wildcard=wcd, style=wx.OPEN | wx.CHANGE_DIR)
			if dlg.ShowModal() == wx.ID_OK:
				val = os.path.normpath(dlg.GetPath())
				if val != self.GetCellValue(row, 1):
					self.SetCellValue(row, 1, val)
					self.canvas.UpdateShapes([self.parent.model])
			else:
				dlg.Destroy()
				return False

			dlg.Destroy()

			self.AcceptProp(row, col)

		elif prop == 'python_path':

			model = self.parent.model

			### for .amd or .cmd
			if model.isAMD():
				wcd = _('Atomic DEVSimPy model (*.amd)|*.amd|All files (*)|*')
			elif model.isCMD():
				wcd = _('Coupled DEVSimPy model (*.cmd)|*.cmd|All files (*)|*')
			elif model.isPY():
				wcd = _('Python files (*.py)|*.py|All files (*)|*')
			else:
				wcd = _('All files (*)|*')

			default_dir = os.path.dirname(model.python_path) if os.path.exists(os.path.dirname(model.python_path)) else DOMAIN_PATH
			dlg = wx.FileDialog(self, message=_("Select file ..."), defaultDir=default_dir, defaultFile="", wildcard=wcd, style=wx.OPEN | wx.CHANGE_DIR)
			if dlg.ShowModal() == wx.ID_OK:
				new_python_path = os.path.normpath(dlg.GetPath())

				### if the user would like to load a compressed python file, he just give the name of compressed file that contain the python file
				if zipfile.is_zipfile(new_python_path):
					zf = zipfile.ZipFile(new_python_path, 'r')
					new_python_path = os.path.join(new_python_path, [f for f in  zf.namelist() if f.endswith('.py') and f!='plugins.py'][0])
					### update model path
					model.model_path = os.path.dirname(new_python_path)

				self.SetCellValue(row, 1, new_python_path)

				### behavioral args update (because depends of the new class coming from new python file)
				new_cls = Components.GetClass(new_python_path)

				if inspect.isclass(new_cls):

					### update attributes (behavioral ang graphic)
					old_args = model.args
					model.args = Components.GetArgs(new_cls)
					model.SetAttributes(Attributable.GRAPHICAL_ATTR)
					
					### copy of the same args value
					for k,v in old_args.items():
						if k in model.args:
							model.args[k] = v

					### TODO: when ScopeGUI and DiskGUI will be amd models, delete this line)
					### delete xlabel and ylabel attributes if exist
					model.RemoveAttribute('xlabel')
					model.RemoveAttribute('ylabel')
					### Update of DEVSimPy model from new python behavioral file (ContainerBlock is not considered because he did not behavioral)
					if new_cls.__name__ in ('To_Disk','MessagesCollector'):
						model.__class__ = Container.DiskGUI
					elif new_cls.__name__ == 'QuickScope':
						model.__class__ = Container.ScopeGUI
						model.AddAttribute("xlabel")
						model.AddAttribute("ylabel")
					elif True in ['DomainStructure' in str(a) for a in new_cls.__bases__]:
						model.__class__ = Container.ContainerBlock
					else:
						model.__class__ = Container.CodeBlock

					### if we change the python file from zipfile we compresse the new python file and we update the python_path value
					if zipfile.is_zipfile(model.model_path):
						zf = ZipManager.Zip(model.model_path)
						zf.Update([new_python_path])

					### update flag and color if bad filename
					if model.bad_filename_path_flag:
						model.bad_filename_path_flag = False
				else:
					Container.MsgBoxError(evt, self, new_cls)
					dlg.Destroy()
					return False
			else:
				dlg.Destroy()
				return False

			dlg.Destroy()

			self.AcceptProp(row, col)

		elif typ == "list":
			frame = ListEditor(self, wx.NewIdRef(), prop, values=self.GetCellValue(row, 1))
			if frame.ShowModal() == wx.ID_CANCEL:
				self.SetCellValue(row, 1, frame.GetValueAsString())
			else:
				frame.Destroy()

			self.AcceptProp(row, col)

		elif typ == 'dict':
			frame = DictionaryEditor(self, wx.NewIdRef(), prop, values=self.GetCellValue(row, 1))
			if frame.ShowModal() == wx.ID_CANCEL:
				self.SetCellValue(row, 1, frame.GetValueAsString())
			else:
				frame.Destroy()

			self.AcceptProp(row, col)
		elif 'choice' in typ:
			self.AcceptProp(row, col)
		else:
			pass

		### all properties grid update (because the python class has been changed)
		### here, because OnAcceptProp should be executed before
		if prop == 'python_path':

			### Update table from new model
			table.UpdateRowBehavioralData(model)
			self.SetTable(table, False)
			self.ForceRefresh()
			self.AutoSizeColumns()

			# code updating
			if isinstance(model, Achievable):
				new_code = CodeCB(self.parent, wx.NewIdRef(), model)
				#self.parent.boxH.Remove(0)
				if hasattr(self.parent, '_boxH'):
					# DeleteWindows work better in vista
					if wx.VERSION_STRING < '4.0':
						self.parent._boxH.DeleteWindows()
						self.parent._boxH.AddWindow(new_code, 1, wx.EXPAND, userData='code')
					else:
						self.parent._boxH.Clear()
						self.parent._boxH.Add(new_code, 1, wx.EXPAND, userData='code')

					self.parent._boxH.Layout()
				else:
					sys.stdout.write("_boxH is unknown!")

	###
	def OnSelectProp(self, evt):
		"""
		"""
		self.SelectProp(evt)
		evt.Skip()

	def GetState(self):
		return self.__state

	#def OnGridEditorCreated(self, event):
		#""" Bind the kill focus event to the newly instantiated cell editor """
		#editor = event.GetControl()
		#editor.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)
		#event.Skip()

	#def OnKillFocus(self, event):
		## Cell editor's grandparent, the grid GridWindow's parent, is the grid.
		#grid = event.GetEventObject().GetGrandParent()
		#grid.SaveEditControlValue()
		#grid.HideCellEditControl()
		#event.Skip()

def main():
    pass

if __name__ == '__main__':
    main()
