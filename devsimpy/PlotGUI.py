# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# PlotGUI.py --- Plotting class
#                     --------------------------------
#                        Copyright (c) 2018
#                       	Laurent CAPOCCHI
#                      	University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 06/03/18
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
import math
import threading
import csv
import bisect

_ = wx.GetTranslation

import wx.lib.agw.aui as aui

try:
	import matplotlib as mpl
	import matplotlib.figure as fig
	from matplotlib.backends.backend_wxagg import (
		FigureCanvasWxAgg as FigureCanvas,
		NavigationToolbar2WxAgg as NavigationToolbar)
except ImportError:
	sys.stdout.write("matplotlib module not found. You need it if you plan to use models like QuickScope.\n")

# for spectrum
try:
	from numpy import *
except ImportError:
	platform_sys = os.name

	if platform_sys in ('nt', 'mac'):
		sys.stdout.write("Numpy module not found. Go to www.scipy.numpy.org.\n")
	elif platform_sys == 'posix':
		sys.stdout.write("Numpy module not found. Install python-numpy (ubuntu) package.\n")
	else:
		sys.stdout.write("Unknown operating system.\n")
		sys.exit()
else:
	#This module requires the Numeric/numarray or NumPy module, which could not be imported.
	import wx.lib.plot as plot

from Utilities import smooth, get_downloads_folder, load_and_resize_image

LColour = ('black', 'red', 'green', 'blue', 'yellow', 'gray', 'magenta', 'maroon', 'orange', 'salmon', 'pink', 'plum')
Markers = ('circle', 'triangle', 'square',  'cross', 'triangle_down', 'plus', 'dot')

def get_limit(d):
	""" Function which give the limits of d
	"""
	L1,L2 = [],[]
	for c in d:
		bisect.insort(L1, float(c[0]))
		bisect.insort(L2, float(c[1]))

	### 0.5 in order to visualize the max and min value correctly
	return L1[0],L1[-1],L2[0]-0.5,L2[-1]+0.5

def PlotManager(parent, label, atomicModel, xl, yl):
	""" Manager for the plotting process which depends of the fusion option of QuickScope.
	"""

	### there is a active simulation thread ?
	dyn_flag = True in ['Simulator' in a.getName() for a in threading.enumerate()[1:]]

	### plots are superposed ?
	fusion_flag = atomicModel.fusion

	### data to plot
	data = atomicModel if dyn_flag else atomicModel.results

	if data == {}:
		wx.MessageBox(_('Data set is empty.\nOnly for QuickScope: Please verify if the received data are float or int.'), _('Info'), wx.OK|wx.ICON_INFORMATION)
		return

	if data is None:
		wx.MessageBox(_('DEVS model is empty.'), _('Info'), wx.OK|wx.ICON_INFORMATION)
		return
	
	if dyn_flag:
		if fusion_flag:
			frame = DynamicPlot(parent, wx.NewIdRef(), _("Plotting %s")%label, data, xLabel=xl, yLabel=yl)
			frame.CenterOnParent()
			frame.Show()
		else:
			for key in atomicModel.results:
				frame = DynamicPlot(parent, wx.NewIdRef(), _("%s on port %s")%(label,str(key)), data, xLabel = xl, yLabel = yl, iport=key)
				frame.CenterOnParent()
				frame.Show()
	else:
		### values to plot are string (for state for instance) ?
		
		str_data_flag = isinstance(data[0][0][-1], str) if isinstance(data, dict) else isinstance(data[0][-1], str)
		
		if str_data_flag or fusion_flag:
			frame = StaticPlot(parent, wx.NewIdRef(), _("Plotting %s")%label, data, xLabel=xl, yLabel=yl, legend=atomicModel.blockModel.label, fusion=fusion_flag)	
			frame.SetBlockModel(atomicModel)
			frame.CenterOnParent()
			frame.Show()
		else:
			
			for key in data:
				frame = StaticPlot(parent, wx.NewIdRef(), _("%s on port %s")%(label,str(key)), data[key], xLabel = xl, yLabel = yl, legend = atomicModel.blockModel.label)
				frame.CenterOnParent()
				frame.Show()

class PlotPanel(wx.Panel):
	def __init__(self, parent, id=-1, dpi=None, **kwargs):
		wx.Panel.__init__(self, parent, id=id, **kwargs)
		self.figure = fig.Figure(dpi=dpi, figsize=(2, 2))
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

class PlotFrame(wx.Frame):
	def __init__(self, parent=None, id=wx.NewIdRef(), title="Time Plotting"):
		"""	Constructor.
		"""

		wx.Frame.__init__(self, parent, id, title, size=(800, 500), style=wx.DEFAULT_FRAME_STYLE|wx.CLIP_CHILDREN)

		self.type = "PlotLine"
		self.normalize = False
		self.home = DEVSIMPY_PACKAGE_PATH

		self.client = plot.PlotCanvas(self)

		self.InitUI()

		self.Layout()

	def InitUI(self):

		self.download_id = wx.NewIdRef()

		##Now Create the menu bar and items
		self.mainmenu = wx.MenuBar()

		menu = wx.Menu()
		setup = menu.Append(wx.NewIdRef(), _('Page Setup'), _('Setup the printer page'))
		file_print_preview = menu.Append(wx.NewIdRef(), _('Print Preview'), _('Show the current plot on page'))
		file_print = menu.Append(wx.NewIdRef(), _('Print'), _('Print the current plot'))
		file_save = menu.Append(wx.NewIdRef(), _('Save Plot'), _('Save current plot'))
		file_export = menu.Append(wx.NewIdRef(), _('Export Plot'), _('Export current plot'))
		file_exit = menu.Append(wx.NewIdRef(), _('&Exit'), _('Enough of this already!'))

		self.mainmenu.Append(menu, _('&File'))

		menu = wx.Menu()
		plotRedraw = menu.Append(wx.NewIdRef(), _('&Redraw'), _('Redraw plots'))
		plotScale = menu.Append(wx.NewIdRef(), _('&Scale'), _('Scale canvas'))

		type_submenu = wx.Menu()
		line = type_submenu.Append(wx.MenuItem(menu, wx.NewIdRef(), _('Line'), kind=wx.ITEM_RADIO))
		scatter = type_submenu.Append(wx.MenuItem(menu, wx.NewIdRef(), _('Scatter'), kind=wx.ITEM_RADIO))
		bar = type_submenu.Append(wx.MenuItem(menu, wx.NewIdRef(), _('Bar'), kind=wx.ITEM_RADIO))
		square = type_submenu.Append(wx.MenuItem(menu, wx.NewIdRef(), _('Square'), kind=wx.ITEM_RADIO))
		menu.Append(wx.NewIdRef(), _('Type'), type_submenu)

		enable_submenu = wx.Menu()
		self.enableTitle = enable_submenu.Append(wx.NewIdRef(), _('&Title'), _('Enable title'), kind=wx.ITEM_CHECK)
		self.enableTitle.Check(True)
		self.enableZoom = enable_submenu.Append(wx.NewIdRef(), _('&Zoom'), _('Enable zoom'), kind=wx.ITEM_CHECK)
		self.enableGrid = enable_submenu.Append(wx.NewIdRef(), _('Grid'), _('Enable grid'), kind=wx.ITEM_CHECK)
		self.enableGrid.Check(True)
		self.enableDrag = enable_submenu.Append(wx.NewIdRef(), _('Drag'), _('Enable drag'), kind=wx.ITEM_CHECK)
		self.enableLegend = enable_submenu.Append(wx.NewIdRef(), _('&Legend'), _('Turn on legend'), kind=wx.ITEM_CHECK)
		self.enablePointLabel = enable_submenu.Append(wx.NewIdRef(), _('&Point Label'), _('Show closest point'), kind=wx.ITEM_CHECK)
		self.norm = enable_submenu.Append(wx.NewIdRef(), _('Normalize'), _('Normalize Y axis'), kind=wx.ITEM_CHECK)
		menu.Append(wx.NewIdRef(), _('Enable'), enable_submenu)

		setx_submenu = wx.Menu()
		self.enableXStep = setx_submenu.Append(wx.NewIdRef(), _('Step'), _('X with step'), kind=wx.ITEM_RADIO)
		self.enableXDefault = setx_submenu.Append(wx.NewIdRef(), _('Default'), _('X with Simulation Time (Default)'), kind=wx.ITEM_RADIO)
		self.enableXDefault.Check(True)
		menu.Append(wx.NewIdRef(), _('Set X'), setx_submenu)

		setTitle = menu.Append(wx.NewIdRef(), _('Set Title'), _('Define title'))
		setXLabel = menu.Append(wx.NewIdRef(), _('Set X Label'), _('Define x label'))
		setYLabel = menu.Append(wx.NewIdRef(), _('Set Y Label'), _('Define y label'))
		scrUp = menu.Append(wx.NewIdRef(), _('Scroll Up 1'), _('Move View Up 1 Unit'))
		scrRt = menu.Append(wx.NewIdRef(), _('Scroll Rt 2'), _('Move View Right 2 Units'))
		reset = menu.Append(wx.NewIdRef(), _('&Plot Reset'), _('Reset to original plot'))

		self.mainmenu.Append(menu, _('&Plot'))

		self.SetMenuBar(self.mainmenu)

		self.Bind(wx.EVT_MENU, self.OnFilePageSetup, setup)
		self.Bind(wx.EVT_MENU, self.OnFilePrintPreview, file_print_preview)
		self.Bind(wx.EVT_MENU, self.OnFilePrint, file_print)
		self.Bind(wx.EVT_MENU, self.OnSaveFile, file_save)
		self.Bind(wx.EVT_MENU, self.OnExportFile, file_export)
		self.Bind(wx.EVT_MENU, self.OnFileExit, file_exit)
		self.Bind(wx.EVT_MENU, self.OnPlotRedraw, plotRedraw)
		self.Bind(wx.EVT_MENU, self.OnPlotLine, line)
		self.Bind(wx.EVT_MENU, self.OnPlotScatter, scatter)
		self.Bind(wx.EVT_MENU, self.OnPlotBar, bar)
		self.Bind(wx.EVT_MENU, self.OnPlotSquare, square)
		self.Bind(wx.EVT_MENU, self.OnPlotScale, plotScale)
		self.Bind(wx.EVT_MENU, self.OnEnableXStep, self.enableXStep)
		self.Bind(wx.EVT_MENU, self.OnEnableXDefault, self.enableXDefault)
		self.Bind(wx.EVT_MENU, self.OnEnableTitle, self.enableTitle)
		self.Bind(wx.EVT_MENU, self.OnEnableZoom, self.enableZoom)
		self.Bind(wx.EVT_MENU, self.OnEnableGrid,  self.enableGrid)
		self.Bind(wx.EVT_MENU, self.OnEnableDrag, self.enableDrag)
		self.Bind(wx.EVT_MENU, self.OnEnableLegend, self.enableLegend)
		self.Bind(wx.EVT_MENU, self.OnEnablePointLabel, self.enablePointLabel)
		self.Bind(wx.EVT_MENU, self.OnEnableNormalize, self.norm)
		self.Bind(wx.EVT_MENU, self.OnTitleSetting, setTitle)
		self.Bind(wx.EVT_MENU, self.OnXLabelSetting, setXLabel)
		self.Bind(wx.EVT_MENU, self.OnYLabelSetting, setYLabel)
		self.Bind(wx.EVT_MENU, self.OnScrUp, scrUp)
		self.Bind(wx.EVT_MENU, self.OnScrRt, scrRt)
		self.Bind(wx.EVT_MENU, self.OnReset, reset)
		
		self.Bind(wx.EVT_MENU, self.OnDownload, self.download_id)

		self.client.canvas.Bind(wx.EVT_LEFT_DOWN, self.OnMouseLeftDown)
		self.client.canvas.Bind(wx.EVT_MOTION, self.OnMotion)
		self.Bind(wx.EVT_CLOSE, self.OnQuit)
		
		### A status bar to tell people what's happening
		self.CreateStatusBar(1)

		### create tool bar
		self.BuildToolbar()

		vbox = wx.BoxSizer(wx.VERTICAL)
		
		vbox.Add(self.client, 1, wx.EXPAND)

		self.SetSizer(vbox)

	def BuildToolbar(self):
		""" Create ToolBar.
		"""

		tb = self.CreateToolBar()
		#tb = wx.ToolBar(self, style=wx.TB_HORIZONTAL|wx.NO_BORDER|wx.TB_FLAT)
		tb.SetToolBitmapSize((16,16))

		zoomLabel, zoomId = self.enableZoom.GetItemLabelText(), self.enableZoom.GetId()
		titleLabel, titleId = self.enableTitle.GetItemLabelText(), self.enableTitle.GetId()
		gridLabel, gridId = self.enableGrid.GetItemLabelText(), self.enableGrid.GetId()
		legendLabel, legendId = self.enableLegend.GetItemLabelText(), self.enableLegend.GetId()
		dragLabel, dragId = self.enableDrag.GetItemLabelText(), self.enableDrag.GetId()
		pointLabel, pointId = self.enablePointLabel.GetItemLabelText(), self.enablePointLabel.GetId()
		normalizedLabel, normalizedId = self.norm.GetItemLabelText(), self.norm.GetId()

		tb.AddCheckTool(zoomId, zoomLabel, load_and_resize_image('toggle-zoom.png'), shortHelp=_('Enable zoom'), longHelp='')
		titletb = tb.AddCheckTool(titleId, titleLabel, load_and_resize_image('toggle-title.png'), shortHelp=_('Enable title'), longHelp='')
		gridtb = tb.AddCheckTool(gridId, gridLabel, load_and_resize_image('toggle-grid.png'), shortHelp='Enable grid', longHelp='')
		tb.AddCheckTool(legendId, legendLabel, load_and_resize_image('toggle-legend.png'), shortHelp=_('Turn on legend'), longHelp='')
		tb.AddCheckTool(dragId, dragLabel, load_and_resize_image('toggle-drag.png'), shortHelp=_('Enable drag'), longHelp='')
		tb.AddCheckTool(pointId, pointLabel, load_and_resize_image('toggle-point.png'), shortHelp=_('Show closest point'), longHelp='')
		tb.AddCheckTool(normalizedId, normalizedLabel, load_and_resize_image('toggle-norm.png'), shortHelp=_('Normalize'), longHelp=_('Normalize Y axis'))
		tb.AddTool(self.download_id, _("Download"), load_and_resize_image('download.png'), shortHelp=_('Download the plot to the Download directory'))


		titletb.Toggle(True)
		gridtb.Toggle(True)

		tb.Realize()

	def OnMove(self, event):
		"""
		"""
		event.Skip()

	def OnMouseLeftDown(self,event):
		"""
		"""
		self.SetStatusText(_("Left Mouse Down at Point: (%.4f, %.4f)") % self.client._getXY(event))
		event.Skip()            #allows plotCanvas OnMouseLeftDown to be called

	def drawPointLabel(self, dc, nearest):
		"""
		"""
		ptx, pty = nearest["scaledXY"]

		dc.SetPen(wx.Pen(wx.BLACK))
		dc.SetBrush(wx.Brush(wx.WHITE, 106)) # wx.PENSTYLE_TRANSPARENT = 106
		dc.SetLogicalFunction(wx.INVERT)
		dc.CrossHair(ptx, pty)
		dc.DrawRectangle(ptx-3, pty-3, 7, 7)
		dc.SetLogicalFunction(wx.COPY)

		x,y = nearest["pointXY"] # data values
		self.SetStatusText("%s: x = %.4f, y = %.4f" % (nearest['legend'],x,y))

	def OnMotion(self, event):
		"""
		"""
		#show closest point (when enbled)
		if self.client.enablePointLabel and self.client.pointLabelFunc:
			#make up dict with info for the pointLabel
			#I've decided to mark the closest point on the closest curve
			dlst= self.client.GetClosestPoint(self.client._getXY(event), pointScaled= True)
			if dlst:    #returns [] if none
				curveNum, legend, pIndex, pointXY, scaledXY, distance = dlst
				#make up dictionary to pass to my user function (see DrawPointLabel)
				mDataDict = {"curveNum":curveNum, "legend":legend, "pIndex":pIndex, "pointXY":pointXY, "scaledXY":scaledXY}
				#pass dict to update the pointLabel
				self.client.UpdatePointLabel(mDataDict)

		event.Skip()           #go to next handler

	def OnFilePageSetup(self, event):
		"""
		"""
		self.client.PageSetup()

	def OnFilePrintPreview(self, event):
		"""
		"""
		self.client.PrintPreview()

	def OnFilePrint(self, event):
		"""
		"""
		try:
			self.client.Printout()
		except AttributeError as info:
			sys.stderr.write("Error: %s"%info)

	def OnExportFile(self, event):
		"""
		"""
		pass

	def OnSaveFile(self, event):
		"""
		"""
		dlg = wx.FileDialog(self, message=_('Save file as...'), defaultDir=self.home, defaultFile='', wildcard="*.jpg*", style=wx.SAVE | wx.OVERWRITE_PROMPT)
		if dlg.ShowModal() == wx.ID_OK:
			path = dlg.GetPath()
			self.home = os.path.dirname(path)
		else:
			path = ''
		dlg.Destroy()

		if path != '':
			self.client.SaveFile(path)

	def OnFileExit(self, event):
		"""
		"""
		self.Close()

	def OnPlotRedraw(self,event):
		"""
		"""
		eval("self.On%s(event)"%self.type)
		self.client.Redraw()

	def OnEnableNormalize(self, event):
		"""
		"""
		self.normalize = not self.normalize
		self.OnPlotRedraw(event)

	def OnPlotScale(self, event):
		"""
		"""
		if self.client.last_draw != None:
			graphics, xAxis, yAxis= self.client.last_draw
			self.client.Draw(graphics,(1,3.05),(0,1))

	def OnEnableZoom(self, event):
		"""
		"""
		self.client.enableZoom = event.IsChecked()
		#self.mainmenu.Check(self.enableZoom.GetId(), not event.IsChecked())

	def OnEnableGrid(self, event):
		"""
		"""
		self.client.enableGrid = event.IsChecked()

	def OnEnableDrag(self, event):
		"""
		"""
		self.client.enableDrag = event.IsChecked()
		#self.mainmenu.Check(self.enableDrag.GetId(), not event.IsChecked())

	def OnEnableTitle(self, event):
		"""
		"""
		self.client.enableTitle = event.IsChecked()

	def OnEnableLegend(self, event):
		"""
		"""
		self.client.enableLegend = event.IsChecked()

	def OnEnablePointLabel(self, event):
		"""
		"""
		self.client.enablePointLabel = event.IsChecked()

	def OnEnableXStep(self, event):
		"""
		"""
		pass

	def OnEnableXDefault(self, event):
		"""
		"""
		pass

	def OnTitleSetting(self, event):
		"""
		"""
		pass

	def OnXLabelSetting(self, event):
		"""
		"""
		pass

	def OnYLabelSetting(self, event):
		"""
		"""
		pass

	def OnScrUp(self, event):
		"""
		"""
		self.client.ScrollUp(1)

	def OnScrRt(self,event):
		"""
		"""
		self.client.ScrollRight(2)

	def OnReset(self,event):
		"""
		"""
		self.client.Reset()

	def OnDownload(self, event):
		"""_summary_

		Args:
			event (_type_): _description_
		"""
		pass
		
	def resetDefaults(self):
		"""Just to reset the fonts back to the PlotCanvas defaults"""
		self.client.SetFont(wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
		self.client.SetFontSizeAxis(10)
		self.client.SetFontSizeLegend(7)
		self.client.setLogScale((False,False))
		self.client.SetXSpec('auto')
		self.client.SetYSpec('auto')

	def OnQuit(self, event):
		"""
		"""
		self.Destroy()

class StaticPlot(PlotFrame):
	"""
	"""

	def __init__(self, parent = None, id = wx.NewIdRef(), title = "Time Plotting", data = None, xLabel = 'Time [s]', yLabel = 'Amplitude [A]', typ = 'PlotLine', legend='', fusion=False):
		"""	@data : [(t,y)...]
		"""

		# local copy
		self.data = data
		self.xLabel = xLabel
		self.yLabel = yLabel
		self.step = False
		self.typ = typ
		self.title = title
		self.legend = legend
		self.fusion_flag = fusion

		### Block model (from Collector lib)
		self.block = None
  
		### if values to plot are string (for state for instance)
		### the frame used to display the data is not PlotFrame.
		if (isinstance(data, dict) and isinstance(data[0][0][-1], str)) or (isinstance(data, list) and isinstance(data[0][-1], str)):
			wx.Frame.__init__(self, parent, id, title, size=(800, 500), style=wx.DEFAULT_FRAME_STYLE|wx.CLIP_CHILDREN)
			self.normalize = False
			self.OnPlotStep()
		else:

			PlotFrame.__init__(self, parent, id, title)
   
			menu = wx.Menu()
   
			### display legend if more than 1 curve to display
			if isinstance(self.data,dict) and len(self.data.keys())>1:
				self.client.enableLegend = True
    
				### update GUI
				tb = self.GetToolBar()
				tb.ToggleTool(self.enableLegend.GetId(),self.client.enableLegend)
				self.enableLegend.Check(self.client.enableLegend)

    
			### with fusion
			if self.fusion_flag:
				
				for i in range(len(self.data)):
					self.Bind(wx.EVT_MENU,self.OnPlotSpectrum, menu.Append(wx.NewIdRef(), _('Signal %d')%i, _('Spectrum Plot')))
				self.Bind(wx.EVT_MENU,self.OnPlotAllSpectrum, menu.Append(wx.NewIdRef(), _('All'), _('Spectrum Plot')))

			else:
				self.Bind(wx.EVT_MENU,self.OnPlotSpectrum, menu.Append(wx.NewIdRef(), _('Signal'), _('Spectrum Plot')))
			self.mainmenu.Append(menu, _('&Spectrum'))

			menu = wx.Menu()
			self.Bind(wx.EVT_MENU,self.OnRMSE, menu.Append(wx.NewIdRef(), _('RMSE'), _('Root Mean Square Error')))
			self.mainmenu.Append(menu, _('&Error'))

			menu = wx.Menu()
			self.Bind(wx.EVT_MENU, self.OnMean, menu.Append(wx.NewIdRef(), _('Mean'), _('Mean of the curve')))
			self.mainmenu.Append(menu, _('&Mean'))

			### call self.On<PlotLine>()
			getattr(self,'On%s'%self.typ)()

	def Normalize(self, data):
		m = max(a[1] for a in data)
		return [(b[0], b[1]/m) for b in data]

	def SetBlockModel(self,block):
		self.block = block
  
		### call self.On<PlotLine>()
		getattr(self,'On%s'%self.typ)()
  
	def getInputLabels(self,data):
		### find input label if it is defined b the user
		input_labels = {i:f"in{i}" for i in data.keys()}   
		if self.block:
			a = self.block.getBlockModel().getInputLabels()
			if a!={}:
				input_labels = a
		return input_labels

	def OnPlotStep(self, event=None)-> None:
		"""
		"""
		data = self.data

		plotter = PlotNotebook(self)
		x,y = zip(*data[0])
		axes1 = plotter.add(self.title).gca()
		axes1.set_xlabel(_('Time'), fontsize=16)
		axes1.set_ylabel(_('Label'), fontsize=16)
		axes1.step(x, y, LColour[0], label='Inport 0')
		axes1.grid(True)
		#axes1.set_title(_("Plotting %s")%label)

		### with fusion
		if self.fusion_flag:
			### if multiple inputs
			if len(data) >= 2:
				for k,v in data.items():
					if v != data[0]:
						x,y = zip(*v)
						axes1.step(x, y, LColour[k+1],label='Inport %s'%str(k))

				### show legend only of mulitple inputs
				axes1.legend()
		else:
			
			### if multiple inputs
			if len(data) >= 2:
				for k,v in data.items():
					if v != data[0]:
						x,y = zip(*v)
						ax = plotter.add(_("%s - Inport %s")%(self.title,str(k))).gca()
						ax.set_xlabel(_('Time'), fontsize=16)
						ax.set_ylabel(_('Label'), fontsize=16)
						ax.step(x, y, LColour[k])
						ax.grid(True)
						#axes1.set_title(_("Plotting %s")%label)

	def OnPlotLine(self, event=None)-> None:
		"""
		"""
		data = self.data

		### without fusion
		if isinstance(data, list):

			data = [(i if self.step else x[0], x[1]) for i,x in enumerate(data)]
			
			if self.normalize:
				data = self.Normalize(data)

			line = plot.PolyLine(data, legend = 'Port 0 (%s)'%self.legend, colour = 'black', width = 1)

			self.gc = plot.PlotGraphics([line], self.title, self.xLabel, self.yLabel)
			xMin,xMax,yMin,yMax = get_limit(data)

		### with fusion (see attribut _fusion of QuickScope)
		else:
			L=[]
			xMin, xMax, yMin, yMax = 0.0,0.0,0.0,0.0
			data_list = list(data.values())
   
			input_labels = self.getInputLabels(data)
	
			for ind, dd in enumerate(data_list):
				try:
					cc = LColour[ind]
				except IndexError:
					cc = LColour[0]

				if self.normalize:
					dd = self.Normalize(dd)

				L.append(plot.PolyLine(dd, legend = f'Port {input_labels[ind]}', colour = cc, width=1))

				a,b,c,d = get_limit(dd)

				if float(a) < float(xMin): xMin=float(a)
				if float(b) > float(xMax): xMax=float(b)
				if float(c) < float(yMin): yMin=float(c)
				if float(d) > float(yMax): yMax=float(d)

			
			self.gc = plot.PlotGraphics(L, self.title, self.xLabel, self.yLabel)

		self.client.Draw(self.gc, xAxis = (float(xMin),float(xMax)), yAxis = (float(yMin),float(yMax)))

	def OnPlotSquare(self, event=None)->None:
		"""
		"""

		data = self.data

		## without fusion
		if isinstance(data, list):

			### formatage des données spécifique au square
			data = []
			for v1,v2 in zip(self.data,[(self.data[i+1][0], self.data[i][1]) for i in range(len(self.data)-1)]):
				data.append(v1)
				data.append(v2)

			if self.normalize:
				data = self.Normalize(data)

			line = plot.PolyLine(data, legend = 'Port 0 (%s)'%self.legend, colour = 'black', width = 1)
			self.gc = plot.PlotGraphics([line], self.title, self.xLabel, self.yLabel)
			### gestion automatique des bornes
			xMin,xMax,yMin,yMax = get_limit(data)

		##avec fusion (voir attribut 'fusion' de QuickScope)
		else:

			L = []
			xMin, xMax, yMin, yMax = 0.0,0.0,0.0,0.0
			data_list = list(data.values())
   
			input_labels = self.getInputLabels(data)
   
			for ind,d in enumerate(data_list):

				### formatage des données spécifique au square
				dd = []
				for v1,v2 in zip(d,[ (d[i+1][0], d[i][1]) for i in range(len(d)-1)]):
					dd.append(v1)
					dd.append(v2)

				### gestion des couleures
				try:
					c = LColour[ind]
				except IndexError:
					c = LColour[0]

				if self.normalize:
					m = max([a[1] for a in dd])
					dd = [(b[0], b[1]/m) for b in dd]

				L.append(plot.PolyLine(dd, legend = f'Port {input_labels[ind]}', colour = c, width=1))
				
				### gestion automatique des bornes
				a,b,c,d = get_limit(dd)

				if float(a) < float(xMin): xMin=float(a)
				if float(b) > float(xMax): xMax=float(b)
				if float(c) < float(yMin): yMin=float(c)
				if float(d) > float(yMax): yMax=float(d)

			self.gc = plot.PlotGraphics(L, self.title, self.xLabel, self.yLabel)

		self.client.Draw(self.gc, xAxis = (float(xMin),float(xMax)), yAxis = (float(yMin),float(yMax)))

	def OnPlotScatter(self, event=None):

		data = self.data

		## sans fusion
		if isinstance(data, list):
			if self.normalize:
				data = self.Normalize(data)
			
			markers = plot.PolyMarker(data, colour = LColour[0], marker = Markers[0], size = 1)
			line = plot.PolyLine(data, legend = 'Port 0 (%s)'%self.legend, colour = LColour[0], width = 1)
			
			self.gc = plot.PlotGraphics([line, markers], self.title, self.xLabel, self.yLabel)
			xMin,xMax,yMin,yMax = get_limit(data)

		##avec fusion (voir attribut _fusion de QuickScope)
		else:
			L=[]
			xMin, xMax, yMin, yMax = 0.0,0.0,0.0,0.0
			data_list = list(data.values())
   
			for ind,dd in enumerate(data_list):
				try:
					c = LColour[ind]
				except IndexError:
					c = LColour[0]

				try:
					m = Markers[ind]
				except IndexError:
					m = Markers[0]

				if self.normalize:
					m = max([a[1] for a in dd])
					d = [(b[0], b[1]/m) for b in dd]

				L.append(plot.PolyLine(dd, legend = 'Port 0 %s'%self.legend, colour=c, width=1))
				L.append(plot.PolyMarker(dd, colour=c, marker=m, size=1))

				a,b,c,d = get_limit(dd)

				if float(a) < float(xMin): xMin=float(a)
				if float(b) > float(xMax): xMax=float(b)
				if float(c) < float(yMin): yMin=float(c)
				if float(d) > float(yMax): yMax=float(d)

			self.gc = plot.PlotGraphics(L, self.title, self.xLabel, self.yLabel)

		self.client.Draw(self.gc, xAxis = (float(xMin),float(xMax)), yAxis = (float(yMin),float(yMax)))

	def OnPlotBar(self, event=None):
		data = self.data

		## sans fusion
		if isinstance( data, list):

			line = [plot.PolyLine([(c[0], 0), (c[0],c[1])], legend='', colour='gray', width=25) for c in data]
			self.gc = plot.PlotGraphics(line, self.title, self.xLabel, self.yLabel)
			xMin,xMax,yMin,yMax = get_limit(data)

		##avec fusion (voir attribut _fusion de QuickScope)
		else:
			L=[]
			xMin, xMax, yMin, yMax = 0.0,0.0,0.0,0.0
			for k in data:
				dd = data[k]
				for c in dd:
					L.append(plot.PolyLine([(c[0], 0), (c[0],c[1])], legend='', colour='gray', width=25))

				a,b,c,d = get_limit(dd)

				if float(a) < float(xMin): xMin=float(a)
				if float(b) > float(xMax): xMax=float(b)
				if float(c) < float(yMin): yMin=float(c)
				if float(d) > float(yMax): yMax=float(d)

			self.gc = plot.PlotGraphics(L, self.title, self.xLabel, self.yLabel)

		self.client.Draw(self.gc, xAxis = (float(xMin),float(xMax)), yAxis = (float(yMin),float(yMax)))

	def OnMean(self, evt):
		"""
		"""
		if isinstance(self.data, dict):
			r = 0.0
		else:
			r = sum(c[-1] for c in self.data) / len(self.data)

		wx.MessageBox('Mean: %f'%r, _('Info'), wx.OK|wx.ICON_INFORMATION)

	def OnRMSE(self,evt):
		""" Get RMSE.
		"""
		if isinstance(self.data, dict):
			c1,c2 = self.data.values()
			assert(len(c1)==len(c2))
			diffcarr = map(lambda a,b: pow(float(a[-1])-float(b[-1]),2), c1,c2)
			r = sqrt(sum(diffcarr)/len(c1))
		
			wx.MessageBox('RMSE: %f'%r, _('Info'), wx.OK|wx.ICON_INFORMATION)
		else:
			wx.MessageBox('RMSE needs two curves!', _('Error'), wx.OK|wx.ICON_ERROR)

	#	for k,s in self.atomicModel.results.items():
	#		frame = Spectrum(self,wx.NewIdRef(), title= _("Spectrum of signal %d")%k,data = s)
	#		frame.Center()
	#		frame.Show()

	def OnPlotAllSpectrum(self, evt=None):
		"""
		"""
		for k,s in list(self.data.items()):
			frame = Spectrum(self,wx.NewIdRef(), title= _("Spectrum of signal %d")%k,data=s)
			frame.Center()
			frame.Show()

	def OnPlotSpectrum(self, evt=None):
		"""
		"""

		# si mode fusion
		if isinstance(self.data,dict):
			#menu = evt.GetEventObject()
			item=self.mainmenu.FindItemById(evt.GetId())
			# permet d'identifier le numero du signal
			i = int(item.GetLabel().split(' ')[-1])
			frame = Spectrum(self,wx.NewIdRef(), title= _("Spectrum of signal "),data = self.data[i])

		else:
			frame = Spectrum(self,wx.NewIdRef(), title= _("Spectrum of signal "),data = self.data)

		frame.Center()
		frame.Show()

	def OnEnableXStep(self, event):
		"""
		"""
		self.step = True
		eval("self.On%s()"%self.typ)
		self.gc.setXLabel("Step")
		self.client.Redraw()

	def OnEnableXDefault(self, event):
		"""
		"""
		self.step = False
		eval("self.On%s()"%self.typ)
		self.gc.setXLabel("Time [s]")
		self.client.Redraw()

	def OnTitleSetting(self, event):
		"""
		"""
		dlg = wx.TextEntryDialog(self, _('Enter new title'),_('Title Entry'))
		dlg.SetValue(self.title)
		if dlg.ShowModal() == wx.ID_OK:
			self.title = dlg.GetValue()
			self.gc.setTitle(self.title)
			self.client.Redraw()
		dlg.Destroy()

	def OnXLabelSetting(self, event):
		"""
		"""
		dlg = wx.TextEntryDialog(self, _('Enter new X label'),_('Label Entry'))
		dlg.SetValue(self.xLabel)
		if dlg.ShowModal() == wx.ID_OK:
			self.xLabel = dlg.GetValue()
			self.gc.setXLabel(self.xLabel)
			self.client.Redraw()
		dlg.Destroy()

	def OnYLabelSetting(self, event):
		"""
		"""
		dlg = wx.TextEntryDialog(self, _('Enter new Y label'),_('Label Entry'))
		dlg.SetValue(self.yLabel)
		if dlg.ShowModal() == wx.ID_OK:
			self.yLabel = dlg.GetValue()
			self.gc.setYLabel(self.yLabel)
			self.client.Redraw()
		dlg.Destroy()

	def OnExportFile(self, event):
		""" Export in CSV format
		"""
		
		dlg = wx.FileDialog(self, message=_('Export file as...'), defaultDir=self.home, defaultFile='', wildcard="*.csv*", style=wx.SAVE | wx.OVERWRITE_PROMPT)
		if dlg.ShowModal() == wx.ID_OK:
			path = dlg.GetPath()
			self.home = os.path.dirname(path)
		else:
			path = ''
		dlg.Destroy()
		
		if path != '':	
			d = [(0,0)]
	
			### TODO: adapt to consider all of the tab (not only 0)
			data  = self.data[0] if isinstance(self.data, dict) else self.data
   
			for i,x in enumerate(data):
				if x[0] != d[-1][0]:
					d.append((x[0],x[1]))
				else:
					d[-1] = (x[0],x[1])
			d=d[1:]

			if self.step:
				d = [(i, x[1]) for i,x in enumerate(d)]
			
			with open(path, 'w') as csvFile:
				writer = csv.writer(csvFile, delimiter=' ')
				writer.writerows(d)

	def OnDownload(self, event):
		"""_summary_

		Args:
			event (_type_): _description_
		"""
		path = os.path.join(get_downloads_folder(),self.title+'.png')
		self.client.SaveFile(path)
		wx.MessageBox(_('File saved in %s')%path, _('Info'), wx.OK|wx.ICON_INFORMATION)

class DynamicPlot(PlotFrame):
	"""
	"""

	def __init__(self, parent=None, id=wx.NewIdRef(), title="", atomicModel=None, xLabel="", yLabel="", iport=None):
		"""
			@parent: parent class
			@id: class id
			@title: title of frame
			@xLabel: label for x axe
			@yLabel: label for y axe
			@iport: the number of port when the fusion option is disabled.
			@atomicModel: QuicScope atomic model used for its data
		"""

		PlotFrame.__init__(self, parent, id, title)

		# local copy
		self.parent = parent
		self.atomicModel = atomicModel
		self.xLabel = xLabel
		self.yLabel = yLabel
		self.iport = iport

		self.title = ""

		# simulation thread
		self.sim_thread = None
		diagram = parent.diagram
		diagram_name = os.path.splitext(os.path.basename(diagram.last_name_saved))[0]
		# for all thread without the mainTread (the first is devsimpy)
		for thread in threading.enumerate()[1:]:
			# if the thread is for the current diagram
			if diagram_name in thread.name:
				self.sim_thread = thread
				break

		menu = wx.Menu()

		### si mode fusion
		if self.iport is None:
			for i in self.atomicModel.results:
				self.Bind(wx.EVT_MENU, self.OnPlotSpectrum, menu.Append(wx.NewIdRef(), _('Signal %s')%str(i), _('Spectrum Plot')))
			self.Bind(wx.EVT_MENU, self.OnPlotAllSpectrum, menu.Append(wx.NewIdRef(), _('All'), _('Spectrum Plot')))
		else:
			self.Bind(wx.EVT_MENU, self.OnPlotSpectrum, menu.Append(wx.NewIdRef(), _('Signal %s')%str(self.iport), _('Spectrum Plot')))
		self.mainmenu.Append(menu, _('&Spectrum'))

		self.timer = wx.Timer(self)
		### DEFAULT_PLOT_DYN_FREQ can be configured in preference-> simulation
		self.timer.Start(milliseconds=DEFAULT_PLOT_DYN_FREQ)

		self.Bind(wx.EVT_TIMER, self.OnPlotRedraw)
		#self.Bind(wx.EVT_TIMER, self.OnTimerEvent)
		#self.Bind(wx.EVT_PAINT, getattr(self, "On%s"%self.type))
		self.Bind(wx.EVT_CLOSE, self.OnQuit)

		getattr(self, "On%s"%self.type)()

	def OnTimerEvent(self, event):
		#self.GetEventHandler().ProcessEvent(wx.PaintEvent())
		self.OnPlotRedraw(event)
		
	def Normalize(self, data):
		m = max(a[1] for a in data)
		return [(b[0], b[1]/m) for b in data]

	def OnPlotLine(self, event=None)->None:
		""" Plot process depends to the timer event.
		"""

		#if self.timer.IsRunning():
		### unbinding paint event

		# if self.type != "PlotLine":
		# 	self.type = "PlotLine"
		# 	self.Unbind(wx.EVT_PAINT)
		# 	self.Bind(wx.EVT_PAINT, getattr(self, "On%s"%self.type))

		### without fusion
		if self.iport is not None:

			data = self.atomicModel.results[self.iport]

			if self.normalize:
				data = self.Normalize(data)

			line = plot.PolyLine(data, legend = 'Port 0 (%s)'%self.atomicModel.getBlockModel().label, colour = 'black', width = 1)
			self.gc = plot.PlotGraphics([line], self.title, self.xLabel, self.yLabel)
			xMin,xMax,yMin,yMax = get_limit(data)
		
		### with fusion (look QuickScope attribut _fusion)
		else:

			data = self.atomicModel.results
			label = self.atomicModel.getBlockModel().label

			L = []
			xMin, xMax, yMin, yMax = 0,0,0,0
			data_list = list(data.values())

			for ind,dd in enumerate(data_list):
				#ind = data_list.index(d)
				try:
					cc = LColour[ind]
				except IndexError:
					cc = LColour[0]

				if self.normalize:
					m = max([a[1] for a in dd])
					dd = [(b[0], b[1]/m) for b in dd]
				
				L.append(plot.PolyLine(dd, legend = 'Port %s (%s)'%(str(ind), label), colour = cc, width=1))

				a,b,c,d = get_limit(dd)

				if float(a) < float(xMin): xMin=float(a)
				if float(b) > float(xMax): xMax=float(b)
				if float(c) < float(yMin): yMin=float(c)
				if float(d) > float(yMax): yMax=float(d)

			self.gc = plot.PlotGraphics(L, self.title, self.xLabel, self.yLabel)

		try:
			self.client.Draw(self.gc, xAxis = (float(xMin),float(xMax)), yAxis = (float(yMin),float(yMax)))
		except Exception:
			sys.stdout.write(_("Error trying to plot"))
		
		# if self.sim_thread is None or not self.sim_thread.isAlive():
			# self.timer.Stop()

	def OnPlotSquare(self, event):

		#if self.timer.IsRunning():
		### unbinding paint event
		# if self.type != "PlotSquare":
		# 	self.type = "PlotSquare"
		# 	self.Unbind(wx.EVT_PAINT)
		# 	self.Bind(wx.EVT_PAINT, getattr(self, "On%s"%self.type))

		## without fusion
		if self.iport is not None:

			d = self.atomicModel.results[self.iport]

			### formating data for square
			data = []
			for v1,v2 in zip(d,[ (d[i+1][0], d[i][1]) for i in range(len(d)-1)]):
				data.append(v1)
				data.append(v2)

			if self.normalize:
				m = max([a[1] for a in data])
				data = [(b[0], b[1]/m) for b in data]

			line = plot.PolyLine(data, legend='Port 0 (%s)'%self.atomicModel.getBlockModel().label, colour='black', width=1)
			self.gc = plot.PlotGraphics([line], self.title, self.xLabel, self.yLabel)

			### dynamic managment of bounds
			xMin,xMax,yMin,yMax = get_limit(data)

		### with fusion ('fusion' attribut of QuickScope)
		else:

			data = self.atomicModel.results
			label = self.atomicModel.getBlockModel().label

			L = []
			xMin, xMax = 0,0
			yMin, yMax = 0,0

			data_list = list(data.values())
			for ind,d in enumerate(data_list):

				### data processing
				dd = []
				for v1,v2 in zip(d,[ (d[i+1][0], d[i][1]) for i in range(len(d)-1)]):
					dd.append(v1)
					dd.append(v2)

				### color
				try:
					c = LColour[ind]
				except IndexError:
					c = LColour[0]

				if self.normalize:
					m = max([a[1] for a in dd])
					dd = [(b[0], b[1]/m) for b in dd]

				### data construct
				L.append(plot.PolyLine(dd, legend='Port %s (%s)'%(str(ind),label), colour=c, width=1))

				### limit managment 
				a,b,c,d = get_limit(dd)

				if float(a) < float(xMin): xMin=float(a)
				if float(b) > float(xMax): xMax=float(b)
				if float(c) < float(yMin): yMin=float(c)
				if float(d) > float(yMax): yMax=float(d)

			self.gc = plot.PlotGraphics(L, self.title, self.xLabel, self.yLabel)

		try:
			self.client.Draw(self.gc, xAxis = (float(xMin),float(xMax)), yAxis = (float(yMin),float(yMax)))
		except Exception:
			sys.stdout.write(_("Error trying to plot"))

		cond = self.sim_thread.isAlive() if hasattr(self.sim_thread,'isAlive') else self.sim_thread.is_alive()

		if self.sim_thread is None or not cond:
			self.timer.Stop()

	def OnPlotScatter(self, event):
		"""
		"""

		#if self.timer.IsRunning():
		### unbinding paint event
		# if self.type != "PlotScatter":
		# 	self.type = "PlotScatter"
		# 	self.Unbind(wx.EVT_PAINT)
		# 	self.Bind(wx.EVT_PAINT, getattr(self, "On%s"%self.type))

		## without fusion
		if self.iport is not None:

			data = self.atomicModel.results[self.iport]

			if self.normalize:
				data = self.Normalize(data)

			markers = plot.PolyMarker(data, colour=LColour[0], marker=Markers[0], size=1)
			line = plot.PolyLine(data, legend='Port 0 (%s)'%self.atomicModel.getBlockModel().label, colour=LColour[0], width=1)
			
			self.gc = plot.PlotGraphics([line, markers], self.title, self.xLabel, self.yLabel)
			xMin,xMax,yMin,yMax = get_limit(data)

		## with fusion (see attribut _fusion of QuickScope)
		else:

			data = self.atomicModel.results
			label = self.atomicModel.getBlockModel().label

			L = []
			xMin, xMax = 0,0
			yMin, yMax = 0,0

			data_list = list(data.values())
			for ind,dd in enumerate(data_list):
				#ind = data.values().index(d)
				try:
					c = LColour[ind]
				except IndexError:
					c = LColour[0]

				try:
					m = Markers[ind]
				except IndexError:
					m = Markers[0]

				if self.normalize:
					m = max([a[1] for a in dd])
					dd = [(b[0], b[1]/m) for b in dd]

				L.append(plot.PolyLine(dd, colour=c, width=1))
				L.append(plot.PolyMarker(dd, legend='Port %s (%s)'%(str(ind), label), colour=c, marker=m, size=1))

				a,b,c,d = get_limit(dd)

				if float(a) < float(xMin): xMin=float(a)
				if float(b) > float(xMax): xMax=float(b)
				if float(c) < float(yMin): yMin=float(c)
				if float(d) > float(yMax): yMax=float(d)

			self.gc = plot.PlotGraphics(L, self.title, self.xLabel, self.yLabel)

		try:
			self.client.Draw(self.gc, xAxis = (float(xMin),float(xMax)), yAxis = (float(yMin),float(yMax)))
		except Exception:
			sys.stdout.write(_("Error trying to plot"))

		cond = self.sim_thread.isAlive() if hasattr(self.sim_thread,'isAlive') else self.sim_thread.is_alive()

		if self.sim_thread is None or not cond:
			self.timer.Stop()

	def OnPlotBar(self,event):

		#if self.timer.IsRunning():
		### unbinding paint event
		# if self.type != "PlotBar":
		# 	self.type = "PlotBar"
		# 	self.Unbind(wx.EVT_PAINT)
		# 	self.Bind(wx.EVT_PAINT, getattr(self, "On%s"%self.type))

		## without fusion
		if self.iport is not None:
			data = self.atomicModel.results[self.iport]

			line = [plot.PolyLine([(c[0], 0), (c[0],c[1])], legend='', colour='gray', width=25) for c in data]
			self.gc = plot.PlotGraphics(line, self.title, self.xLabel, self.yLabel)
			xMin,xMax,yMin,yMax = get_limit(data)

		## with fusion (see attribut _fusion of QuickScope)
		else:
			data = self.atomicModel.results

			L=[]
			xMin, xMax, yMin, yMax = 0,0,0,0
			data_list = list(data.values())
			for ind,dd in enumerate(data_list):
				#ind = data_list.index(d)
				try:
					c = LColour[ind]
				except IndexError:
					c = LColour[0]

				for c in dd:
					L.append(plot.PolyLine([(c[0], 0), (c[0],c[1])], legend='', colour='gray', width=25))

				a,b,c,d = get_limit(dd)

				if float(a) < float(xMin): xMin=float(a)
				if float(b) > float(xMax): xMax=float(b)
				if float(c) < float(yMin): yMin=float(c)
				if float(d) > float(yMax): yMax=float(d)

			self.gc = plot.PlotGraphics(L, self.title, self.xLabel, self.yLabel)

		try:

			self.client.Draw(self.gc, xAxis = (float(xMin),float(xMax)), yAxis = (float(yMin),float(yMax)))
		except Exception:
			sys.stdout.write(_("Error trying to plot"))

		cond = self.sim_thread.isAlive() if hasattr(self.sim_thread,'isAlive') else self.sim_thread.is_alive()

		if self.sim_thread is None or not cond:
			self.timer.Stop()

	def OnPlotAllSpectrum(self,evt):
		""" Plot all spectrum.
		"""
		for k,s in list(self.atomicModel.results.items()):
			frame = Spectrum(self,wx.NewIdRef(), title= _("Spectrum of signal %d")%k,data = s)
			frame.Center()
			frame.Show()

	def OnPlotSpectrum(self, evt):
		""" Plot spectrum.
		"""

		item = self.mainmenu.FindItemById(evt.GetId())
		# allow signal number identification
		i = int(item.GetLabel().split(' ')[-1])

		frame = Spectrum(self, wx.NewIdRef(), title= _("Spectrum of signal"), data=self.atomicModel.results[i])
		frame.Center()
		frame.Show()

	def OnTitleSetting(self, event):
		dlg = wx.TextEntryDialog(self, _('Enter a new title'), _('Title Entry'))
		dlg.SetValue(self.title)
		if dlg.ShowModal() == wx.ID_OK:
			self.title = dlg.GetValue()
			self.gc.setTitle(self.title)
			self.client.Redraw()
		dlg.Destroy()

	def OnXLabelSetting(self, event):
		dlg = wx.TextEntryDialog(self, _('Enter a new X label'), _('Label Entry'))
		dlg.SetValue(self.xLabel)
		if dlg.ShowModal() == wx.ID_OK:
			self.xLabel = dlg.GetValue()
			self.gc.setXLabel(self.xLabel)
			self.client.Redraw()
		dlg.Destroy()

	def OnYLabelSetting(self, event):
		dlg = wx.TextEntryDialog(self, _('Enter a new Y label'), _('Label Entry'))
		dlg.SetValue(self.yLabel)
		if dlg.ShowModal() == wx.ID_OK:
			self.yLabel = dlg.GetValue()
			self.gc.setYLabel(self.yLabel)
			self.client.Redraw()
		dlg.Destroy()

class Spectrum(StaticPlot):
	def __init__(self, parent=None, id=wx.NewIdRef(), title="", data=[]):
		"""	@data : [(x,y)...]
		"""

		# total time
		duree = data[-1][0]

		signal=[c[1] for c in data]

		Nb_pts=len(signal)

		#interpolation B-splines
		#dx=1
		#newx=r_[0:Nb_pts:duree]
		#y=array(self.signal)
		#newy=cspline1d_eval(cspline1d(y),newx,dx=dx,x0=y[0])
		#self.signal=newy

		### number of points for fft
		p=1
		while(pow(2,p)<=Nb_pts):
			p+=1
			N=float(pow(2,p))
		assert(pow(2,p)>= Nb_pts)

		### windows
		signal = smooth(array(signal),window_len=10,window="hamming")

		### frequence d'echantillonnage
		Fe = 1.0/(float(duree)/float(len(signal)))

		### FFT
		Y = fft.fft(signal,int(N))
		Y = abs(fft.fftshift(Y))
		F = [Fe*i/N for i in range(int(-N/2), int(N/2))]

		### normalization
		Max = max(Y)
		Y = [20*math.log(i/Max,10) for i in Y]

		### freqencies max and min for the plot
		FMin, FMax=0,200
		F_plot, Y_plot=[],[]
		for i in range(len(F)):
			if FMin<F[i]<FMax:
				F_plot.append(F[i])
				Y_plot.append(Y[i])

		### data processing
		self.data = list(map(lambda a,b: (a,b), F_plot, Y_plot))
		#self.data = [(a,b) for a in F_plot for b in Y_plot]

		# call the frame
		StaticPlot.__init__(self, parent, id, title, self.data, xLabel=_('Frequency [Hz]'),yLabel=_('Amplitude [dB]'))

		self.OnPlotLine()

		# range for fred and amplitude
#		self.sldh.SetRange(1, 300)
#		self.sldv.SetRange(0, 150)

		# start freq 100
#		self.sldh.SetValue(100)
		# start amplitude 0
#		self.sldv.SetValue(0)

		# Bind the Sliders
#		self.Bind(wx.EVT_SLIDER, self.sliderUpdate, id=self.sldh.GetId())
#		self.Bind(wx.EVT_SLIDER, self.sliderUpdate, id=self.sldv.GetId())

#	def sliderUpdate(self, event):
#		posh = self.sldh.GetValue()
#		posv = self.sldv.GetValue()
#		self.Redraw(self.Rescale(posv,posh))

	def Redraw(self,data:list=[]):
		"""Redraw the client

		Args:
			data (list, optional): data to redraw. Defaults to [].
		"""
		size=self.client.GetSize()
		self.client.Clear()
		self.client.SetInitialSize(size=size)

		#xLabel=_('Frequency [Hz]')
		#yLabel=_('Amplitude [dB]')
		line = plot.PolyLine(data, legend='', colour='black', width=1)
		gc = plot.PlotGraphics([line], '', self.xLabel, self.yLabel)
		xMin,xMax,yMin,yMax = get_limit(data)
		self.client.Draw(gc,  xAxis= (float(xMin),float(xMax)), yAxis= (float(yMin),float(yMax)))

	def Rescale(self,FMin:int=0,FMax:int=200)->list:
		""" Rescale the plot

		Args:
			FMin (int, optional): min frequency. Defaults to 0.
			FMax (int, optional): max frequency. Defaults to 200.

		Returns:
			list: [description]
		"""
		F,Y,F_plot, Y_plot=[],[],[],[]
		for f,v in self.data:
			F.append(f)
			Y.append(v)
		for i in range(len(F)):
			if FMin<F[i]<FMax:
				F_plot.append(F[i])
				Y_plot.append(Y[i])

		# formate les donnees pour Plot
		return list(map(lambda a,b: (a,b), F_plot, Y_plot))
		#return [(a,b) for a in F_plot for b in Y_plot]