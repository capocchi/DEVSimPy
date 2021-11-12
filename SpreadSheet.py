# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# SpreadSheet.py ---
#                     --------------------------------
#                        Copyright (c) 2009
#                       Laurent CAPOCCHI
#                      University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified:
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

### at the beginning to prevent with statement for python version <=2.5

import wx
from wx.lib import sheet

import pubsub

# to send event
from pubsub import pub as Publisher

#from Container import *
from PlotGUI import *
from Utilities import printOnStatusBar

import gettext
_ = gettext.gettext

###
class MySheet(sheet.CSheet):
	"""
	"""

	###
	def __init__(self, parent, data):
		""" Constructor.
		"""
		sheet.CSheet.__init__(self, parent)

		### local copy
		self.data = data

		self.row = len(data)
		self.col = len(data[-1])
		self._full_flag = False

		# set the rows and columns of the sheet
		self.SetNumberRows(self.row)
		self.SetNumberCols(self.col)

		# set column label titles at the top
		self.SetRowLabelAlignment(wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)
		self.SetColLabelValue(0, _('Event'))
		self.SetColLabelValue(1, _('Message'))

		wx.CallAfter(self.Populate, (data))

	###
	def UpdateColWidth(self):
		self.AutoSizeColumns()

	###
	def Populate(self, data):
		"""
		"""
		self._full_flag = False

		size = len(data)

		n = float(self.GetNumberRows())

		## load cell
		for i in range(size):
			try:
				d = data[i]
				self.SetCellValue(i,0,str(d[0]))
				self.SetCellValue(i,1,str(d[1]))
				Publisher.sendMessage("progress", msg=str(i/n))
				self.Update()
			except:
				pass

		self._full_flag = True
		try:
			### inform Frame that table us full for graph icon enabling
			Publisher.sendMessage("isfull", msg=self._full_flag)
		except pubsub.pub.SenderMissingReqdMsgDataError as info:
			pass

		try:
			### resize and refresh the frame
			self.AutoSize()
			self.Refresh()
		except Exception as info:
			pass
		
	###
	def IsFull(self):
		return self._full_flag

	def OnLeftClick(self, event):
		"""
		"""
		### veto because bug exist (TypeError: PaintBackground() takes 3 positional arguments but 4 were given)
		event.Veto()

	def OnLeftDoubleClick(self, event):
		"""
		"""
		### veto because bug exist (TypeError: PaintBackground() takes 3 positional arguments but 4 were given)
		event.Veto()

	##def OnGridSelectCell(self, event):
		##self.row, self.col = event.GetRow(), event.GetCol()
		##control = self.GetParent().GetParent().position
		##value =  self.GetColLabelValue(self.col) + self.GetRowLabelValue(self.row)
		##control.SetValue(value)
		##event.Skip()

###
class Newt(wx.Frame):
	"""
	"""

	###
	def __init__(self, parent, id, title, aDEVS, separator=" "):
		""" Constructor
		"""

		wx.Frame.__init__(self,
						parent,
						wx.NewIdRef(),
						aDEVS.getBlockModel().label,
						size = (550, 500),
						style=wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE)

		self.model = aDEVS
		self.sep = separator

		toolbar = self.CreateToolBar()
		toolbar.SetToolBitmapSize((16,16))

		### for Phoenix version
		if wx.VERSION_STRING < '4.0':
			new = toolbar.AddTool(wx.NewIdRef(), wx.Bitmap(os.path.join(ICON_PATH,'new.png')), _('New'), '')
			open_file = toolbar.AddTool(wx.NewIdRef(), wx.Bitmap(os.path.join(ICON_PATH,'open.png')), _('Open'), '')
			saveas = toolbar.AddTool(wx.NewIdRef(), wx.Bitmap(os.path.join(ICON_PATH,'save.png')), _('SaveAs'), '')
			toolbar.AddSeparator()
			cut = toolbar.AddTool(wx.NewIdRef(), wx.Bitmap(os.path.join(ICON_PATH,'cut.png')), _('Cut'), '')
			copy = toolbar.AddTool(wx.NewIdRef(), wx.Bitmap(os.path.join(ICON_PATH,'copy.png')), _('Copy'), '')
			paste = toolbar.AddTool(wx.NewIdRef(), wx.Bitmap(os.path.join(ICON_PATH,'paste.png')), _('Paste'), '')
			self.delete = toolbar.AddTool(wx.NewIdRef(), wx.Bitmap(os.path.join(ICON_PATH,'close.png')), _('Delete'), '')
			toolbar.AddSeparator()
			update = toolbar.AddTool(wx.NewIdRef(), wx.Bitmap(os.path.join(ICON_PATH,'reload.png')), _('Update'), '')
			toolbar.AddSeparator()
			self.chart = toolbar.AddTool(wx.NewIdRef(), wx.Bitmap(os.path.join(ICON_PATH,'graph_guru.png')), _('Chart'), '')
		else:

			new = toolbar.AddTool(wx.NewIdRef(), "", wx.Bitmap(os.path.join(ICON_PATH,'new.png')), _('New'))
			open_file = toolbar.AddTool(wx.NewIdRef(), "", wx.Bitmap(os.path.join(ICON_PATH,'open.png')), _('Open'))
			saveas = toolbar.AddTool(wx.NewIdRef(), "", wx.Bitmap(os.path.join(ICON_PATH,'save.png')), _('SaveAs'))
			toolbar.AddSeparator()
			cut = toolbar.AddTool(wx.NewIdRef(), "", wx.Bitmap(os.path.join(ICON_PATH,'cut.png')), _('Cut'))
			copy = toolbar.AddTool(wx.NewIdRef(), "" ,wx.Bitmap(os.path.join(ICON_PATH,'copy.png')), _('Copy'))
			paste = toolbar.AddTool(wx.NewIdRef(), "" ,wx.Bitmap(os.path.join(ICON_PATH,'paste.png')), _('Paste'))
			self.delete = toolbar.AddTool(wx.NewIdRef(), "", wx.Bitmap(os.path.join(ICON_PATH,'close.png')), _('Delete'))
			toolbar.AddSeparator()
			update = toolbar.AddTool(wx.NewIdRef(), "", wx.Bitmap(os.path.join(ICON_PATH,'reload.png')), _('Update'))
			toolbar.AddSeparator()
			self.chart = toolbar.AddTool(wx.NewIdRef(), "", wx.Bitmap(os.path.join(ICON_PATH,'graph_guru.png')), _('Chart'))

		toolbar.EnableTool(self.chart.GetId(), False)
		### Calling this method is not obligatory in Linux
		### On Windows it is!
		toolbar.Realize()

		#self.SetToolBar(toolbar)

		self.statusbar = self.CreateStatusBar()

		### notebook setting
		self.notebook = wx.Notebook(self, wx.NewIdRef())

		### Load data form devs model
		self.LoadingDataInPage()

		### Layout
		box = wx.BoxSizer(wx.VERTICAL)
		box.Add(self.notebook, 1, wx.EXPAND)
		self.SetSizer(box)

		### binding
		self.Bind(wx.EVT_TOOL, self.OnNew, new)
		self.Bind(wx.EVT_TOOL, self.OnOpen, open_file)
		self.Bind(wx.EVT_TOOL, self.OnSaveAs, saveas)
		self.Bind(wx.EVT_TOOL, self.OnCopy, copy)
		self.Bind(wx.EVT_TOOL, self.OnCut, cut)
		self.Bind(wx.EVT_TOOL, self.OnPaste, paste)
		self.Bind(wx.EVT_TOOL, self.OnDelete, self.delete)
		self.Bind(wx.EVT_TOOL, self.OnUpdate, update)
		self.Bind(wx.EVT_TOOL, self.OnGraph, self.chart)

		self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnTab, self.notebook)

		### pubsub
		### when is sheet is full, graph icon is enabled
		Publisher.subscribe(self.EnableGraphIcon, "isfull")
		Publisher.subscribe(self.OnProgress, "progress")

	###
	def LoadingDataInPage(self):

		### read and load the data in sheet
		for i in range(len(self.model.IPorts)):
			if hasattr(self.model, 'fileName'):
				fn = "%s%d.dat"%(self.model.fileName, i)
				if os.path.exists(fn):
					iPort = self.model.IPorts[i]
					if iPort.inLine:
						oPort = iPort.inLine[0]
						host = oPort.host if hasattr(oPort, 'host') else oPort.hostDEVS
						label = _('%s (on in_%s)')%(host.getBlockModel().label if hasattr(host, 'getBlockModel') else host.name, str(iPort.myID) if hasattr(iPort,'myID') else iPort.name)
						data = self.FileToData(fn, self.sep)
						self.AddPage(data, label)

	###
	def OnUpdate(self, event):

		### remove all pages
		while self.notebook.GetPageCount() >= 1:
			self.notebook.RemovePage(self.notebook.GetSelection())

		### reload all page
		self.LoadingDataInPage()

	###
	def FileToData(self, fn, separator):
		""" Create data from file.
		"""
		with open(fn, 'r') as f:
			if separator != "":
				data = [a.replace('\n','').split(separator) for a in f.readlines()]
			else:
				L = f.readlines()
				index = iter(list(range(len(L))))
				data = [(next(index), a.replace('\n','')) for a in L]

		return data

	###
	def EnableGraphIcon(self, msg):
		""" Enable graph button when loading data is finished and clear the statusbar.
		"""

		### update the column width
		try:
			activePage = self.notebook.GetSelection()
		except Exception as info:
			activePage = 0
			sys.stdout.write(_("Error in SpreadSheet: %s"%info))

		try:
			sheet = self.notebook.GetPage(activePage)
			sheet.UpdateColWidth()
		except Exception as info:
			sys.stdout.write(_("Error in SpreadSheet: %s"%info))
		else:
			toolbar = self.GetToolBar()
			toolbar.EnableTool(self.chart.GetId(), msg)
			printOnStatusBar(self.statusbar, {0:""})

	###
	def OnTab(self, event):
		### update the column width
		activePage = self.notebook.GetSelection()
		sheet = self.notebook.GetPage(activePage)
		sheet.UpdateColWidth()

	###
	def OnProgress(self, msg):
		""" Update status bar with loading data progression
		"""
		pourcent = 100*float(msg)
		printOnStatusBar(self.statusbar, {0:_("Loading data... (%d %%)")%int(pourcent)})

	###
	def AddPage(self, data = [[]], label = ""):
		""" Add new page to notebook knowing data and label
		"""
		sheet = MySheet(self.notebook, data)
		sheet.SetFocus()
		self.notebook.AddPage(sheet, label)
		
		### enable delete button
		toolbar = self.GetToolBar()
		toolbar.EnableTool(self.delete.GetId(), True)

	###
	def OnNew(self, event):
		""" New button bas been pressed.
		"""
		data = [[]]
		label = _('New %d'%self.notebook.GetPageCount())
		self.AddPage(label=label)

	###
	def OnOpen(self, event):
		""" Open button has been pressed.
		"""
		wcd = _("DataSheet file (*.dat)|*.dat|All files (*)|*")
		home = os.getenv('USERPROFILE') or os.getenv('HOME') or HOME_PATH
		open_dlg = wx.FileDialog(self, message = _('Choose a file'), defaultDir = home, defaultFile = "", wildcard = wcd, style = wx.OPEN|wx.MULTIPLE|wx.CHANGE_DIR)
		# get the new path from open file dialogue
		if open_dlg.ShowModal() == wx.ID_OK:
			### for selected paths
			for fn in open_dlg.GetPaths():
				if os.path.exists(fn):
					### separator request
					separator_dico = {"EMPTY":"","SPACE":" ","SEMICOLON":";","COMMA":",","POINT":"."}
					dlg = wx.SingleChoiceDialog(self, _("Choose a separator:"), _('Separator Manager'), list(separator_dico.keys()), wx.CHOICEDLG_STYLE)
					if dlg.ShowModal() == wx.ID_OK:
						separator = separator_dico[dlg.GetStringSelection()]
					else:
						separator = ""
					dlg.Destroy()

					data = self.FileToData(fn, separator)
					label = _('New %d'%self.notebook.GetPageCount())
					self.AddPage(data, label)


	###
	def OnSaveAs(self, event):
		""" SaveAs button has been pressed.
		"""
		wcd = _("DataSheet file (*.dat)|*.dat|All files (*)|*")
		home = HOME_PATH
		save_dlg = wx.FileDialog(self, message=_('Save file as...'), defaultDir=home, defaultFile='', wildcard=wcd, style=wx.SAVE | wx.OVERWRITE_PROMPT)
		if save_dlg.ShowModal() == wx.ID_OK:
			fn = os.path.normpath(save_dlg.GetPath())

			activePage = self.notebook.GetSelection()
			sheet = self.notebook.GetPage(activePage)
			nbr = sheet.GetNumberRows()
			nbc = sheet.GetNumberCols()
			#print "sdf", fn
			with open(fn,'w') as f:
				for row in range(nbr):
					#print sheet.GetCellValue(row,0),sheet.GetCellValue(row,1)
					f.write("%s %s\n"%(sheet.GetCellValue(row,0),sheet.GetCellValue(row,1)))

	###
	def OnCopy(self, event):
		""" Copy button has been pressed.
		"""
		activePage = self.notebook.GetSelection()
		sheet = self.notebook.GetPage(activePage)
		sheet.Copy()

	###
	def OnCut(self, event):
		""" Cut button has been pressed.
		"""
		activePage = self.notebook.GetSelection()
		sheet = self.notebook.GetPage(activePage)
		sheet.Copy()
		sheet.Clear()

	###
	def OnPaste(self, event):
		""" Paste button has been pressed.
		"""
		activePage = self.notebook.GetSelection()
		sheet = self.notebook.GetPage(activePage)
		sheet.Paste()

	###
	def OnDelete(self, event):
		""" Delete button has been pressed.
		"""

		### remove page
		if self.notebook.GetPageCount() >= 1:
			self.notebook.RemovePage(self.notebook.GetSelection())

		### disable delete button
		if self.notebook.GetPageCount() == 0:
			toolbar = self.GetToolBar()
			toolbar.EnableTool(self.delete.GetId(), False)

	###
	def OnGraph(self, event):
		""" Graph button has been pressed.
		"""

		activePage = self.notebook.GetSelection()
		sheet = self.notebook.GetPage(activePage)
		title = self.notebook.GetPageText(activePage)

		### selected rows with mouse but on label colonn
		#selected_rows = sheet.GetSelectedRows()

		### really selected cells with mouse
		a = sheet.GetSelectionBlockTopLeft()
		b = sheet.GetSelectionBlockBottomRight()

		### selected rows with mouse
		try:
			i=a[0][0]
			j=b[0][0]
		### selected all rows
		except IndexError:
			i=0
			j=sheet.GetNumberRows()
		
		selected_rows = list(range(i,j))
		
		nbc = range(sheet.GetNumberCols())
		nbr = range(sheet.GetNumberRows()) if selected_rows == [] else selected_rows

		data = []
		select = -1
		for i in nbr:
			v = sheet.GetCellValue(i,sheet.GetNumberCols()-1)
			
			if '<<' in v or '>>' in v: 
				s = sheet.GetCellValue(i,sheet.GetNumberCols()-1).replace('<< ', '').replace('<<', '').replace('>>','').replace('],','];')
			else:
				s = "value = %s; time = %s"%(v,sheet.GetCellValue(i,0))
			try:
				### globals containt the time and value variables after exec of the statement
				exec(str(s), globals())
			except Exception as info:
				sys.stdout.write(str(info))
			else:
				### if value is a list, we must choose an index to plot amoung the values of the list
				if isinstance(value, list):
					if select == -1:
						if len(value) > 1 :
							dlg = wx.TextEntryDialog(self, _('Choose one index between [%d-%d] to plot into the list of values.')%(0,len(value)-1),_('Plotting Manager'), value="0")
							if dlg.ShowModal() == wx.ID_OK:
								select=int(dlg.GetValue())
								dlg.Destroy()
							else:
								dlg.Destroy()
								break
						else:
							select = 0

					### choice is digit else we break
					# if value[select]:
					if select == 0 or select in range(0,len(value)-1):
						if not isinstance(value[select], str):
							data.append((time, float(value[select])))
						else:
							#wx.MessageBox(_('Value to plot must be digit!'), _('Warning'), wx.OK | wx.ICON_WARNING)
							data.append((time, value[select]))
					
				### first if int is digit or if float is digit
				else:
					v = str(format(value,'f')).lstrip('-')
					if v.isdigit() or v.replace(".", "", 1).isdigit():
						data.append((time,float(value)))
					else:
						#wx.MessageBox(_('Type of data should be float or int: %s')%str(value), _('Info'))
						data.append((time, value))

		if data:
			### if the first value of y is str, we plot with tick in y axe
			if isinstance(data[0][-1], str):
				x,y = zip(*data)
				frame = wx.Frame(None, -1, _('Plotter'))
				plotter = PlotNotebook(frame)
				axes1 = plotter.add(title).gca()
				axes1.set_xlabel(_('Time'), fontsize=16)
				axes1.set_ylabel(_('State'), fontsize=16)
				axes1.step(x, y)
				axes1.grid(True)
				axes1.set_title(title)

				#axes2 = plotter.add('figure 2').gca()
				#axes2.plot([1, 2, 3, 4, 5], [2, 1, 4, 2, 3])
				
				frame.Show()

			### values of y is digits
			else:
				frame = StaticPlot(None, wx.NewIdRef(), title, data)
				frame.Center()
				frame.Show()

##if __name__ == '__main__':
##	import builtins
##	import Container
##
##	builtins.__dict__['FONT_SIZE'] = 12
##	#app = wx.App(0)
##	devs =  Container.DiskGUI()
##	newt = Newt(None, wx.NewIdRef(), 'SpreadSheet', devs)
##	app.MainLoop()
