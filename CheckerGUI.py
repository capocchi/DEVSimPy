# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# CheckerGUI.py ---
#                    --------------------------------
#                            Copyright (c) 2020
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 2.0                                        last modified: 03/15/20
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
import os
import sys
import webbrowser
import tempfile

import inspect
if not hasattr(inspect, 'getargspec'):
    inspect.getargspec = inspect.getfullargspec
    
from traceback import format_exception

import gettext
_ = gettext.gettext

if __name__ == '__main__':
	import builtins
	path = os.path.dirname(os.getcwd())
	if path not in sys.path:
		sys.path.append(path)
	builtins.__dict__['GUI_FLAG'] = True
	builtins.__dict__['HOME_PATH'] = os.path.abspath(os.path.dirname(sys.argv[0]))
	builtins.__dict__['DEFAULT_DEVS_DIRNAME'] = "PyDEVS"
	builtins.__dict__['DEVS_DIR_PATH_DICT'] = {\
	'PyDEVS':os.path.join(os.pardir,'DEVSKernel','PyDEVS'),\
	'PyPDEVS':os.path.join(os.pardir,'DEVSKernel','PyPDEVS', 'old')}
	

from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin, ColumnSorterMixin
from Utilities import GetMails, getInstance

import Components

class VirtualList(wx.ListCtrl, ListCtrlAutoWidthMixin, ColumnSorterMixin):
	""" Virtual List of devs model checking
	"""
	def __init__(self, parent, D):
		""" Constructor.
		"""
		wx.ListCtrl.__init__( self, parent, -1, style=wx.LC_REPORT|wx.LC_VIRTUAL|wx.LC_HRULES|wx.LC_VRULES)

		### local copy
		self.parent = parent

		### adding some art
		self.il = wx.ImageList(16, 16)
		a={"sm_up":"GO_UP","sm_dn":"GO_DOWN","idx1":"CROSS_MARK","idx2":"TICK_MARK"}
		ArtProvider = "wx.ArtProvider_GetBitmap" if wx.VERSION_STRING < '4.0' else "wx.ArtProvider.GetBitmap"

		for k,v in a.items():
			s="self.%s= self.il.Add(%s(wx.ART_%s,wx.ART_TOOLBAR,(16,16)))" % (k,ArtProvider,v)
			exec(s)

		self.SetImageList(self.il, wx.IMAGE_LIST_SMALL)

		### building the columns
		self.InsertColumn(0, _('Name'), wx.LIST_FORMAT_CENTRE, width=120)
		self.InsertColumn(1, _('Error'), wx.LIST_FORMAT_CENTRE, width=450)
		self.InsertColumn(2, _('Line'), wx.LIST_FORMAT_CENTRE, width=80)
		self.InsertColumn(3, _('Authors'), wx.LIST_FORMAT_CENTRE, width=80)
		self.InsertColumn(4, _('Path'), wx.LIST_FORMAT_CENTRE, width=120)

		### These two should probably be passed to init more cleanly
		### setting the numbers of items = number of elements in the dictionary
		self.itemDataMap = D
		self.itemIndexMap = list(D.keys())
		self.SetItemCount(len(D))

		### mixins
		ListCtrlAutoWidthMixin.__init__(self)
		ColumnSorterMixin.__init__(self, self.GetColumnCount())

		### sort by genre (column 2), A->Z ascending order (1)
		self.SortListItems(2, 0)

		### events binding
		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)
		self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
		self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected)
		self.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick)
		self.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick)
		self.Bind(wx.EVT_LEFT_DOWN, self.OnClick)
		self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnRightClick)

	def OnColClick(self,event):
		"""
		"""
		event.Skip()

	def OnClick(self, event):
		"""
		"""

		### deselect all item
		for x in range(self.GetItemCount()):
			self.Select(x, False)

		### get selected item position
		x,y = event.GetPosition() 
		row,flags = self.HitTest((x,y)) 

		### select the item
		self.Select(row)

		model_name = self.getColumnText(row, 0)
		path = self.getColumnText(row, 4)

		tempdir = tempfile.gettempdir()
		
		### open file diag only if python file is temp
		if tempdir in os.path.dirname(path):
			from AttributeEditor import AttributeEditor

			### get model from active diagram			
			mainW = wx.GetApp().GetTopWindow()
			canvas = mainW.nb2.GetCurrentPage()
			diagram = canvas.GetDiagram()

			f = AttributeEditor(canvas.GetParent(), wx.NewIdRef(), diagram.GetShapeByLabel(model_name), canvas)
			f.Show()

	def OnItemSelected(self, event):
		""" Item has been selected
		"""
		self.currentItem = event.m_itemIndex if wx.VERSION_STRING < '4.0' else event.Index
		
	def OnRightClick(self, event):
		""" Right Click on cell has been invoked
		"""
		# record what was clicked
		line_number = self.getColumnText(self.currentItem, 2)

		### pop-up menu only for cell with line_number
		if line_number != "":

			### 2. Launcher creates wxMenu. ###
			menu = wx.Menu()

			edit = wx.MenuItem(menu, wx.NewIdRef(),_("Edit"), _("Edit the source code"))
			edit.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH_16_16,'edit.png')))
			report = wx.MenuItem(menu, wx.NewIdRef(),_("Report"), _("Report error by mail to the author"))
			report.SetBitmap(wx.Bitmap(os.path.join(ICON_PATH_16_16,'mail.png')))

			menu.AppendItem(edit)
			menu.AppendItem(report)

			menu.Bind(wx.EVT_MENU,self.OnEditor,id= edit.GetId())
			menu.Bind(wx.EVT_MENU,self.OnReport,id= report.GetId())

			### 5. Launcher displays menu with call to PopupMenu, invoked on the source component, passing event's GetPoint. ###
			self.PopupMenu( menu, event.GetPoint() )
			menu.Destroy() # destroy to avoid mem leak

	def OnEditor(self, event):
		""" Edit pop-up menu has been clicked
		"""
		self.OnDoubleClick(event)

	def OnReport(self, event):
		""" Report pop-up menu has been clicked
		"""

		### get error info
		info = self.getColumnText(self.currentItem, 1)
		line = self.getColumnText(self.currentItem, 2)
		mails_list = eval(self.getColumnText(self.currentItem, 3))
		python_path = self.getColumnText(self.currentItem, 4)

		model_name = os.path.basename(python_path)

		### send mail to mailto and cc (for associated developpers)
		mailto = mails_list[0]
		cc = ""
		for mail in mails_list[1:]:
			cc += '%s,'%mail

		body = _("Dear DEVSimPy developpers, \n Error in %s, line %s :\n %s")%(model_name,line,info)
		subject = _("Error in %s DEVSimPy model")%(model_name)
		webbrowser.open_new("mailto:%s?subject=%s&cc=%s&body=%s"%(mailto,subject,cc,body))

	def OnItemDeselected(self, event):
		""" Item has been deselected
		"""
		line_number = self.getColumnText(self.currentItem, 2)
		python_path = self.getColumnText(self.currentItem, 4)

		if line_number != "":
			### DEVS model retrieve
			devs = getInstance(Components.GetClass(python_path))
			### check error and change image
			if not isinstance(devs, tuple):
				self.SetItemImage(self.currentItem, self.idx2)

	def OnDoubleClick(self, event):
		""" Double click on cell has been invoked
		"""
		line_number = self.getColumnText(self.currentItem, 2)
		python_path = self.getColumnText(self.currentItem, 4)

		if line_number != "":
			devscomp = Components.DEVSComponent()
			devscomp.setDEVSPythonPath(python_path)

			editor_frame = Components.DEVSComponent.OnEditor(devscomp, event)
			if editor_frame:
				nb = editor_frame.GetNoteBook()
				page = nb.GetCurrentPage()
				pos = int(line_number)
				page.GotoLine(pos)

		event.Skip()

	def OnItemActivated(self, event):
		""" Item has been activated
		"""
		self.currentItem = event.m_itemIndex if wx.VERSION_STRING < '4.0' else event.Index
	
	def getColumnText(self, index, col):
		"""
		"""
		item = self.GetItem(index, col)
		try:
			return item.GetItemLabelText()
		except:
			return item.GetText()

	#---------------------------------------------------
	# These methods are callbacks for implementing the
	# "virtualness" of the list...

	def OnGetItemText(self, item, col):
		"""
		"""
		index = self.itemIndexMap[item]
		s = str(self.itemDataMap[index][col])
		return s

	def OnGetItemImage(self, item):
		"""
		"""
		index=self.itemIndexMap[item]
		data=self.itemDataMap[index][2]

		if data=="":
			return self.idx2
		else:
			return self.idx1

	def SortItems(self,sorter):
		"""
		"""
		items = list(self.itemDataMap.keys())
		items.sort()
		self.itemIndexMap = items

		# redraw the list
		self.Refresh()

	# Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
	def GetListCtrl(self):
		"""
		"""
		return self

	# Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
	def GetSortImages(self):
		"""
		"""
		return (self.sm_dn, self.sm_up)

class CheckerGUI(wx.Frame):
	""" Class which report the code checking of python file
	"""

	def __init__(self, parent, D):
		""" Constructor.
		"""
		wx.Frame.__init__(self, parent, wx.NewIdRef(), _("DEVS Model Checking"), size=(900,400), style = wx.DEFAULT_FRAME_STYLE)

		icon = wx.EmptyIcon() if wx.VERSION_STRING < '4.0' else wx.Icon()
		icon.CopyFromBitmap(wx.Bitmap(os.path.join(ICON_PATH_16_16, "check_master.png"), wx.BITMAP_TYPE_ANY))
		self.SetIcon(icon)

		### local copy
		self.parent = parent

		##############################################" comment for unitest
		### prepare dictionary
		try:
			self.list = self.getList(D)
		except:
			self.list = VirtualList(self, D)
			sys.stdout.write(_('Alone mode for CheckerGUI: List of plugins is not generated from a diagram.\n'))
		#################################################

		self.mainSizer = wx.BoxSizer(wx.VERTICAL)
		controlSizer = wx.StdDialogButtonSizer() #wx.BoxSizer(wx.HORIZONTAL)
		self.listSizer = wx.BoxSizer(wx.VERTICAL)

		close_btn = wx.Button(self, wx.ID_CLOSE)
		ok_btn = wx.Button(self, wx.ID_OK)
		update_btn = wx.Button(self, wx.ID_REFRESH)

		controlSizer.Add(close_btn,0, wx.CENTER|wx.ALL, 5)
		controlSizer.Add(update_btn,0, wx.CENTER|wx.ALL, 5)
		controlSizer.Add(ok_btn,0, wx.CENTER|wx.ALL, 5)
		controlSizer.Realize()

		self.listSizer.Add(self.list, 1, wx.EXPAND, 10)

		self.mainSizer.Add(self.listSizer, 1, wx.EXPAND, 10)
		self.mainSizer.Add(controlSizer,0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM,border=10)

		self.SetSizer(self.mainSizer)
		self.Center()

		### just for windows
		e = wx.SizeEvent(self.GetSize())
		self.ProcessEvent(e)

		self.Bind(wx.EVT_BUTTON, self.OnClose, id = close_btn.GetId())
		self.Bind(wx.EVT_BUTTON, self.OnOK, id = ok_btn.GetId())
		self.Bind(wx.EVT_BUTTON, self.OnUpdate, id = update_btn.GetId())

	def SetDiagram(self, diagram):
		""" Set the diagram.
		"""
		self.diagram = diagram

	def getList(self, D):
		""" Return list to populate de virtualList
		"""

		tempdir = tempfile.gettempdir()
		
		L = []
		if D:
			for k,v in D.items():

				path = ""
				line = ""

				if tempdir in os.path.dirname(k.python_path):
					### append infos
					L.append((k.label, _("Temporary python file!"), "", "", k.python_path))
				elif v:
					typ, val, tb = v
					list = format_exception(typ, val, tb)
					### reverse because we want the last error of the traceback
					list.reverse()
					### find the line containing the 'line' word
					for s in list:
						if 'line ' in s:
							path, line = s.split(',')[0:2]
							break

					### erase whitespace and clear the Line word and the File word
					python_path = str(path.split(' ')[-1].strip())[1:-1]
					line_number = line.split(' ')[-1].strip()

					### find mail from doc of module
					module = Components.BlockFactory.GetModule(python_path)
					doc = module.__doc__ or ""
					mails = GetMails(doc) if inspect.ismodule(module) else []

					### append the error information
					L.append((k.label, str(val), line_number, mails, python_path))
		
		return VirtualList(self, dict(zip(range(len(L)),L))) if L != [] else L

	def OnUpdate(self, evt):
		""" Update list has been invocked
		"""

		### get list by ckecking all block models of the diagram
		if hasattr(self, 'diagram'):
			D = self.diagram.DoCheck()
			L = self.getList(D)

			if isinstance(L, VirtualList):
				self.list = L

				### display the updated list
				self.listSizer.Hide(0)
				self.listSizer.Remove(0)
				self.listSizer.Add(self.list, 1, wx.EXPAND, 10)
				self.Layout()
			else:
				sys.stdou.write(_('List not updated!'))
		else:
			sys.stdout.write(_('Call the SetDiagram method to define the diagram object.'))

	def OnClose(self,evt):
		"""
		"""
		self.Close()

	def OnOK(self, evt):
		"""
		"""
		self.Close()

### ------------------------------------------------------------
class TestApp(wx.App):
	""" Testing application
	"""

	musicdata = {
	1 : ("Bad English", "The Price Of Love", "Rock"),
	2 : ("DNA featuring Suzanne Vega", "Tom's Diner", "Rock"),
	3 : ("George Michael", "Praying For Time", "Rock"),
	4 : ("Gloria Estefan", "Here We Are", "Rock"),
	5 : ("Linda Ronstadt", "Don't Know Much", "Rock"),
	6 : ("Michael Bolton", "How Am I Supposed To Live Without You", "Blues"),
	7 : ("Paul Young", "Oh Girl", "Rock"),
	8 : ("Paula Abdul", "Opposites Attract", "Rock"),
	9 : ("Richard Marx", "Should've Known Better", "Rock"),
	10: ("Rod Stewart", "Forever Young", "Rock"),
	11: ("Roxette", "Dangerous", "Rock"),
	12: ("Sheena Easton", "The Lover In Me", "Rock"),
	13: ("Sinead O'Connor", "Nothing Compares 2 U", "Rock"),
	14: ("Stevie B.", "Because I Love You", "Rock"),
	15: ("Taylor Dayne", "Love Will Lead You Back", "Rock"),
	16: ("The Bangles", "Eternal Flame", "Rock"),
	17: ("Wilson Phillips", "Release Me", "Rock"),
	18: ("Billy Joel", "Blonde Over Blue", "Rock"),
	19: ("Billy Joel", "Famous Last Words", "Rock"),
	20: ("Billy Joel", "Lullabye (Goodnight, My Angel)", "Rock"),
	21: ("Billy Joel", "The River Of Dreams", "Rock"),
	22: ("Billy Joel", "Two Thousand Years", "Rock"),
	23: ("Janet Jackson", "Alright", "Rock"),
	24: ("Janet Jackson", "Black Cat", "Rock"),
	25: ("Janet Jackson", "Come Back To Me", "Rock"),
	26: ("Janet Jackson", "Escapade", "Rock"),
	27: ("Janet Jackson", "Love Will Never Do (Without You)", "Rock"),
	28: ("Janet Jackson", "Miss You Much", "Rock"),
	29: ("Janet Jackson", "Rhythm Nation", "Rock"),
	30: ("Janet Jackson", "State Of The World", "Rock"),
	31: ("Janet Jackson", "The Knowledge", "Rock"),
	32: ("Spyro Gyra", "End of Romanticism", "Jazz"),
	33: ("Spyro Gyra", "Heliopolis", "Jazz"),
	34: ("Spyro Gyra", "Jubilee", "Jazz"),
	35: ("Spyro Gyra", "Little Linda", "Jazz"),
	36: ("Spyro Gyra", "Morning Dance", "Jazz"),
	37: ("Spyro Gyra", "Song for Lorraine", "Jazz"),
	38: ("Yes", "Owner Of A Lonely Heart", "Rock"),
	39: ("Yes", "Rhythm Of Love", "Rock"),
	40: ("Cusco", "Dream Catcher", "New Age"),
	41: ("Cusco", "Geronimos Laughter", "New Age"),
	42: ("Cusco", "Ghost Dance", "New Age"),
	43: ("Blue Man Group", "Drumbone", "New Age"),
	44: ("Blue Man Group", "Endless Column", "New Age"),
	45: ("Blue Man Group", "Klein Mandelbrot", "New Age"),
	46: ("Kenny G", "Silhouette", "Jazz"),
	47: ("Sade", "Smooth Operator", "Jazz"),
	48: ("David Arkenstone", "Papillon (On The Wings Of The Butterfly)", "New Age"),
	49: ("David Arkenstone", "Stepping Stars", "New Age"),
	50: ("David Arkenstone", "Carnation Lily Lily Rose", "New Age"),
	51: ("David Lanz", "Behind The Waterfall", "New Age"),
	52: ("David Lanz", "Cristofori's Dream", "New Age"),
	53: ("David Lanz", "Heartsounds", "New Age"),
	54: ("David Lanz", "Leaves on the Seine", "New Age"),
	}

	def OnInit(self):

		import gettext
		import builtins

		builtins.__dict__['ICON_PATH']='icons'
		builtins.__dict__['ICON_PATH_16_16']=os.path.join(ICON_PATH,'16x16')
		builtins.__dict__['_'] = gettext.gettext

		self.frame = CheckerGUI(None, TestApp.musicdata)
		self.frame.Show()
		return True

	def OnQuit(self, event):
		self.Close()

if __name__ == '__main__':

	app = TestApp(0)
	app.MainLoop()