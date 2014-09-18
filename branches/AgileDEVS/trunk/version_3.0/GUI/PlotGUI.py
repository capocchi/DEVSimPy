# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# Plot.py --- Plotting class
#                     --------------------------------
#                        Copyright (c) 2010
#                       Laurent CAPOCCHI
#                      University of Corsica
#                     --------------------------------
# Version 3.0                                        last modified: 12/02/10
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
import math
import threading
import bisect

import wx


# for spectrum
import Core.Utilities.Utilities as Utilities

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

LColour = ('black', 'red', 'green', 'blue', 'yellow', 'gray', 'magenta', 'maroon', 'orange', 'salmon', 'pink', 'plum')
Markers = ('circle', 'triangle', 'square', 'cross', 'triangle_down', 'plus', 'dot')


def get_limit(d):
	""" Function whwich give the limits of d
	"""

	L1, L2 = [], []
	for c in d:
		bisect.insort(L1, c[0])
		bisect.insort(L2, c[1])
		#L1.append(c[0])
		#L2.append(c[1])

	#L1.sort();L2.sort()

	return L1[0], L1[-1], L2[0], L2[-1]


def PlotManager(parent, label, atomicModel, xl, yl):
	""" Manager for the plotting process which depends of the fusion option of QuickScope.
	"""

	### there is a active simulation thread ?
	dyn = True in map(lambda a: 'Simulator' in a.getName(), threading.enumerate()[1:])

	if atomicModel.fusion:
		if dyn:
			frame = DynamicPlot(parent, wx.ID_ANY, _("Plotting %s") % label, atomicModel, xLabel=xl, yLabel=yl)
		else:
			frame = StaticPlot(parent, wx.ID_ANY, _("Plotting %s") % label, atomicModel.results, xLabel=xl, yLabel=yl,
							   legend=atomicModel.blockModel.label)
		frame.CenterOnParent()
		frame.Show()
	else:
		if dyn:
			for key in atomicModel.results:
				frame = DynamicPlot(parent, wx.ID_ANY, _("%s on port %s") % (label, str(key)), atomicModel, xLabel=xl,
									yLabel=yl, iport=key)
				frame.CenterOnParent()
				frame.Show()
		else:
			for key in atomicModel.results:
				frame = StaticPlot(parent, wx.ID_ANY, _("%s on port %s") % (label, str(key)), atomicModel.results[key],
								   xLabel=xl, yLabel=yl, legend=atomicModel.blockModel.label)
				frame.CenterOnParent()
				frame.Show()


class PlotFrame(wx.Frame):
	def __init__(self, parent=None, id=wx.ID_ANY, title="Time Plotting"):
		"""	Constructor.
		"""

		wx.Frame.__init__(self, parent, id, title, size=(800, 500),
						  style=wx.DEFAULT_FRAME_STYLE | wx.CLIP_CHILDREN | wx.STAY_ON_TOP)

		self.type = "PlotLine"
		self.normalize = False

		self.sldh = wx.Slider(self, wx.ID_ANY, 10, 0, 50, (-1, -1), (250, -1), wx.SL_AUTOTICKS | wx.SL_HORIZONTAL | wx.SL_LABELS)
		self.sldv = wx.Slider(self, wx.ID_ANY, 10, 0, 50, (-1, -1), (50, 150), wx.SL_AUTOTICKS | wx.SL_VERTICAL | wx.SL_LABELS)

		self.client = plot.PlotCanvas(self)
		self.client.SetPointLabelFunc(self.drawPointLabel)

		##Now Create the menu bar and items
		self.mainmenu = wx.MenuBar()

		menu = wx.Menu()
		setup = menu.Append(wx.NewId(), _('Page Setup'), _('Setup the printer page'))
		file_print_preview = menu.Append(wx.NewId(), _('Print Preview'), _('Show the current plot on page'))
		file_print = menu.Append(wx.NewId(), _('Print'), _('Print the current plot'))
		file_save = menu.Append(wx.NewId(), _('Save Plot'), _('Save current plot'))
		file_exit = menu.Append(wx.NewId(), _('E&xit'), _('Enough of this already!'))

		self.mainmenu.Append(menu, _('&File'))

		menu = wx.Menu()
		plotRedraw = menu.Append(wx.NewId(), _('&Redraw'), _('Redraw plots'))
		plotScale = menu.Append(wx.NewId(), _('&Scale'), _('Scale canvas'))

		type_submenu = wx.Menu()
		line = type_submenu.AppendItem(wx.MenuItem(menu, wx.NewId(), _('Line'), kind=wx.ITEM_RADIO))
		scatter = type_submenu.AppendItem(wx.MenuItem(menu, wx.NewId(), _('Scatter'), kind=wx.ITEM_RADIO))
		bar = type_submenu.AppendItem(wx.MenuItem(menu, wx.NewId(), _('Bar'), kind=wx.ITEM_RADIO))
		square = type_submenu.AppendItem(wx.MenuItem(menu, wx.NewId(), _('Square'), kind=wx.ITEM_RADIO))
		menu.AppendMenu(wx.NewId(), _('Type'), type_submenu)

		enable_submenu = wx.Menu()
		enableTitle = enable_submenu.Append(wx.NewId(), _('&Title'), _('Enable Title'), kind=wx.ITEM_CHECK)
		self.enableZoom = enable_submenu.Append(wx.NewId(), _('&Zoom'), _('Enable Mouse Zoom'), kind=wx.ITEM_CHECK)
		enableGrid = enable_submenu.Append(wx.NewId(), _('Grid'), _('Enable Mouse Zoom'), kind=wx.ITEM_CHECK)
		self.enableDrag = enable_submenu.Append(wx.NewId(), _('Drag'), _('Enable Mouse Zoom'), kind=wx.ITEM_CHECK)
		enableLegend = enable_submenu.Append(wx.NewId(), _('&Legend'), _('Turn on Legend'), kind=wx.ITEM_CHECK)
		enablePointLabel = enable_submenu.Append(wx.NewId(), _('&Point Label'), _('Show Closest Point'),
												 kind=wx.ITEM_CHECK)
		normalize = enable_submenu.Append(wx.NewId(), _('Normalize'), _('Normalize Y axis'), kind=wx.ITEM_CHECK)
		menu.AppendMenu(wx.NewId(), _('Enable'), enable_submenu)

		setTitle = menu.Append(wx.NewId(), _('Set Title'), _('Define title'))
		setXLabel = menu.Append(wx.NewId(), _('Set X Label'), _('Define x label'))
		setYLabel = menu.Append(wx.NewId(), _('Set Y Label'), _('Define y label'))
		scrUp = menu.Append(wx.NewId(), _('Scroll Up 1'), _('Move View Up 1 Unit'))
		scrRt = menu.Append(wx.NewId(), _('Scroll Rt 2'), _('Move View Right 2 Units'))
		reset = menu.Append(wx.NewId(), _('&Plot Reset'), _('Reset to original plot'))

		self.mainmenu.Append(menu, _('&Plot'))

		self.SetMenuBar(self.mainmenu)

		self.Bind(wx.EVT_MENU, self.OnFilePageSetup, setup)
		self.Bind(wx.EVT_MENU, self.OnFilePrintPreview, file_print_preview)
		self.Bind(wx.EVT_MENU, self.OnFilePrint, file_print)
		self.Bind(wx.EVT_MENU, self.OnSaveFile, file_save)
		self.Bind(wx.EVT_MENU, self.OnFileExit, file_exit)
		self.Bind(wx.EVT_MENU, self.OnPlotRedraw, plotRedraw)
		self.Bind(wx.EVT_MENU, self.OnPlotLine, line)
		self.Bind(wx.EVT_MENU, self.OnPlotScatter, scatter)
		self.Bind(wx.EVT_MENU, self.OnPlotBar, bar)
		self.Bind(wx.EVT_MENU, self.OnPlotSquare, square)
		self.Bind(wx.EVT_MENU, self.OnPlotScale, plotScale)
		self.Bind(wx.EVT_MENU, self.OnEnableTitle, enableTitle)
		self.Bind(wx.EVT_MENU, self.OnEnableZoom, self.enableZoom)
		self.Bind(wx.EVT_MENU, self.OnEnableGrid, enableGrid)
		self.Bind(wx.EVT_MENU, self.OnEnableDrag, self.enableDrag)
		self.Bind(wx.EVT_MENU, self.OnEnableLegend, enableLegend)
		self.Bind(wx.EVT_MENU, self.OnEnablePointLabel, enablePointLabel)
		self.Bind(wx.EVT_MENU, self.OnEnableNormalize, normalize)
		self.Bind(wx.EVT_MENU, self.OnTitleSetting, setTitle)
		self.Bind(wx.EVT_MENU, self.OnXLabelSetting, setXLabel)
		self.Bind(wx.EVT_MENU, self.OnYLabelSetting, setYLabel)
		self.Bind(wx.EVT_MENU, self.OnScrUp, scrUp)
		self.Bind(wx.EVT_MENU, self.OnScrRt, scrRt)
		self.Bind(wx.EVT_MENU, self.OnReset, reset)

		# A status bar to tell people what's happening
		self.CreateStatusBar(1)

		toggleZoom = wx.CheckBox(self, label=self.enableZoom.GetLabel())
		toggleTitle = wx.CheckBox(self, label=enableTitle.GetLabel())
		toggleGrid = wx.CheckBox(self, label=enableGrid.GetLabel())
		toggleLegend = wx.CheckBox(self, label=enableLegend.GetLabel())
		toggleDrag = wx.CheckBox(self, label=self.enableDrag.GetLabel())
		togglePointLabel = wx.CheckBox(self, label=enablePointLabel.GetLabel())
		toggleNormalize = wx.CheckBox(self, label=normalize.GetLabel())

		toggleTitle.Bind(wx.EVT_CHECKBOX, self.OnEnableTitle)
		toggleZoom.Bind(wx.EVT_CHECKBOX, self.OnEnableZoom)
		toggleGrid.Bind(wx.EVT_CHECKBOX, self.OnEnableGrid)
		toggleLegend.Bind(wx.EVT_CHECKBOX, self.OnEnableLegend)
		toggleDrag.Bind(wx.EVT_CHECKBOX, self.OnEnableDrag)
		togglePointLabel.Bind(wx.EVT_CHECKBOX, self.OnEnablePointLabel)
		toggleNormalize.Bind(wx.EVT_CHECKBOX, self.OnEnableNormalize)

		vbox = wx.BoxSizer(wx.VERTICAL)
		hbox = wx.BoxSizer(wx.HORIZONTAL)
		hhbox = wx.BoxSizer(wx.HORIZONTAL)

		hbox.Add(self.sldv, 0, wx.BOTTOM)
		hbox.Add(self.client, 1, wx.EXPAND | wx.ALIGN_CENTRE)

		hhbox.Add(toggleZoom, 0, wx.BOTTOM)
		hhbox.Add(toggleTitle, 0, wx.BOTTOM)
		hhbox.Add(toggleGrid, 0, wx.BOTTOM)
		hhbox.Add(toggleLegend, 0, wx.BOTTOM)
		hhbox.Add(toggleDrag, 0, wx.BOTTOM)
		hhbox.Add(togglePointLabel, 0, wx.BOTTOM)
		hhbox.Add(toggleNormalize, 0, wx.BOTTOM)

		vbox.Add(hbox, 1, wx.EXPAND | wx.ALIGN_CENTRE)
		vbox.Add(self.sldh, 0, wx.BOTTOM)
		vbox.Add(hhbox, 0, wx.BOTTOM)

		self.SetSizer(vbox)

		self.client.canvas.Bind(wx.EVT_LEFT_DOWN, self.OnMouseLeftDown)
		self.client.canvas.Bind(wx.EVT_MOTION, self.OnMotion)

		self.Bind(wx.EVT_CLOSE, self.OnQuit)
		self.Bind(wx.EVT_SLIDER, self.sliderUpdate, id=self.sldh.GetId())
		self.Bind(wx.EVT_SLIDER, self.sliderUpdate, id=self.sldv.GetId())
		self.Layout()

	#def Rescale(self, data, xMin=0,xMax=200):
		##frequence max et min pour le plot
		#x,y,x_plot, y_plot=[],[],[],[]
		#for f,v in data:
			#x.append(f)
			#y.append(v)
		#for i in xrange(len(x)):
			#if xMin<x[i]<xMax:
				#x_plot.append(x[i])
				#y_plot.append(y[i])

		## formate les donnees pour Plot
		#return map(lambda a,b:(a,b),x_plot,y_plot)
     
	def sliderUpdate(self, event):
		posh = self.sldh.GetValue()
		posv = self.sldv.GetValue()

		#self.client.Redraw(self.Rescale(data,posv,posh))
		### TODO look sprectum in order to rewrite Rescale and Redraw and rename them
		pass

	def OnMove(self, event):
		#print 'Move event, new pos:' + str(event.Position)
		event.Skip()

	def OnMouseLeftDown(self, event):
		self.SetStatusText(_("Left Mouse Down at Point: (%.4f, %.4f)") % self.client._getXY(event))
		event.Skip()            #allows plotCanvas OnMouseLeftDown to be called

	def drawPointLabel(self, dc, nearest):
		ptx, pty = nearest["scaledXY"]

		dc.SetPen(wx.Pen(wx.BLACK))
		dc.SetBrush(wx.Brush(wx.WHITE, wx.TRANSPARENT))
		dc.SetLogicalFunction(wx.INVERT)
		dc.CrossHair(ptx, pty)
		dc.DrawRectangle(ptx - 3, pty - 3, 7, 7)
		dc.SetLogicalFunction(wx.COPY)

		x, y = nearest["pointXY"] # data values
		self.SetStatusText("%s: x = %.4f, y = %.4f" % (nearest['legend'], x, y))

	def OnMotion(self, event):
		#show closest point (when enbled)
		if self.client.GetEnablePointLabel() == True and self.client.GetPointLabelFunc():
			#make up dict with info for the pointLabel
			#I've decided to mark the closest point on the closest curve
			dlst = self.client.GetClosestPoint(self.client._getXY(event), pointScaled=True)
			if dlst:    #returns [] if none
				curveNum, legend, pIndex, pointXY, scaledXY, distance = dlst
				#make up dictionary to pass to my user function (see DrawPointLabel) 
				mDataDict = {"curveNum": curveNum, "legend": legend, "pIndex": pIndex, "pointXY": pointXY,
							 "scaledXY": scaledXY}
				#pass dict to update the pointLabel		
				self.client.UpdatePointLabel(mDataDict)

		event.Skip()           #go to next handler

	def OnFilePageSetup(self, event):
		self.client.PageSetup()

	def OnFilePrintPreview(self, event):
		self.client.PrintPreview()

	def OnFilePrint(self, event):
		try:
			self.client.Printout()
		except AttributeError, info:
			sys.stderr.write("Error: %s" % info)

	def OnSaveFile(self, event):
		dlg = wx.FileDialog(self, message=_('Save file as...'), defaultDir=HOME_PATH, defaultFile='', wildcard="*.jpg*",
							style=wx.SAVE | wx.OVERWRITE_PROMPT)
		if dlg.ShowModal() == wx.ID_OK:
			path = dlg.GetPath()
		else:
			path = ''
		dlg.Destroy()

		if path != '':
			self.client.SaveFile(path)

	def OnFileExit(self, event):
		self.Close()

	def OnPlotRedraw(self, event):
		eval("self.On%s(event)" % self.type)
		self.client.Redraw()

	def OnEnableNormalize(self, event):
		self.normalize = not self.normalize
		self.OnPlotRedraw(event)

	def OnPlotScale(self, event):
		if self.client.last_draw is not None:
			graphics, xAxis, yAxis = self.client.last_draw
			self.client.Draw(graphics, (1, 3.05), (0, 1))

	def OnEnableZoom(self, event):
		self.client.SetEnableZoom(event.IsChecked())
		#self.mainmenu.Check(self.enableZoom.GetId(), not event.IsChecked())
		
	def OnEnableGrid(self, event):
		self.client.SetEnableGrid(event.IsChecked())

	def OnEnableDrag(self, event):
		self.client.SetEnableDrag(event.IsChecked())
		#self.mainmenu.Check(self.enableDrag.GetId(), not event.IsChecked())
		
	def OnEnableTitle(self, event):
		self.client.SetEnableTitle(event.IsChecked())

	def OnEnableLegend(self, event):
		self.client.SetEnableLegend(event.IsChecked())

	def OnEnablePointLabel(self, event):
		self.client.SetEnablePointLabel(event.IsChecked())

	def OnTitleSetting(self, event):
		pass

	def OnXLabelSetting(self, event):
		pass

	def OnYLabelSetting(self, event):
		pass

	def OnScrUp(self, event):
		self.client.ScrollUp(1)

	def OnScrRt(self, event):
		self.client.ScrollRight(2)

	def OnReset(self, event):
		self.client.Reset()

	def resetDefaults(self):
		"""Just to reset the fonts back to the PlotCanvas defaults"""
		self.client.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL))
		self.client.SetFontSizeAxis(10)
		self.client.SetFontSizeLegend(7)
		self.client.setLogScale((False, False))
		self.client.SetXSpec('auto')
		self.client.SetYSpec('auto')

	def OnQuit(self, event):
		self.Destroy()


class StaticPlot(PlotFrame):
	def __init__(self, parent=None, id=wx.ID_ANY, title="Time Plotting", data=None, xLabel='Time [s]',
				 yLabel='Amplitude [A]', typ='PlotLine', legend=''):
		"""	@data : [(t,y)...]
		"""

		PlotFrame.__init__(self, parent, id, title)

		# local copy
		self.data = data
		self.xLabel = xLabel
		self.yLabel = yLabel
		self.typ = typ
		self.title = title
		self.legend = legend

		menu = wx.Menu()
		### si mode fusion

		if isinstance(self.data, dict):
			for i in xrange(len(self.data)):
				self.Bind(wx.EVT_MENU, self.OnPlotSpectrum, menu.Append(wx.NewId(), _('Signal %d') % i, _('Spectrum Plot')))
			self.Bind(wx.EVT_MENU, self.OnPlotAllSpectrum, menu.Append(wx.NewId(), _('All'), _('Spectrum Plot')))
		else:
			self.Bind(wx.EVT_MENU, self.OnPlotSpectrum, menu.Append(wx.NewId(), _('Signal'), _('Spectrum Plot')))
		self.mainmenu.Append(menu, _('&Spectrum'))

		### call self.On<PlotLine>()
		getattr(self, 'On%s' % self.typ)()

	def OnPlotLine(self, event=None):

		data = self.data

		## sans fusion
		if isinstance(data, list):
			if self.normalize:
				m = max(map(lambda a: a[1], data))
				data = map(lambda b: (b[0], b[1] / m), data)
			line = plot.PolyLine(data, legend='Port 0 %s' % self.legend, colour='black', width=1)
			self.gc = plot.PlotGraphics([line], self.title, self.xLabel, self.yLabel)
			xMin, xMax, yMin, yMax = get_limit(data)

		##avec fusion (voir attribut _fusion de QuickScope)
		else:
			L = []
			xMin, xMax, yMin, yMax = 0, 0, 0, 0
			data_list = data.values()
			for ind, d in enumerate(data_list):
				try:
					c = LColour[ind]
				except IndexError:
					c = LColour[0]

				if self.normalize:
					m = max(map(lambda a: a[1], d))
					d = map(lambda b: (b[0], b[1] / m), d)

				L.append(plot.PolyLine(d, legend='Port %d %s' % (ind, self.legend), colour=c, width=1))

				a, b, c, d = get_limit(d)

				if a < xMin: xMin = a
				if b > xMax: xMax = b
				if c < yMin: yMin = c
				if d > yMax: yMax = d

			self.gc = plot.PlotGraphics(L, self.title, self.xLabel, self.yLabel)

		self.client.Draw(self.gc, xAxis=(float(xMin), float(xMax)), yAxis=(float(yMin), float(yMax)))

	def OnPlotSquare(self, event=None):

		data = self.data

		## sans fusion
		if isinstance(data, list):

			### formatage des donnees specifique au square
			data = []
			for v1, v2 in zip(self.data, [(self.data[i + 1][0], self.data[i][1]) for i in xrange(len(self.data) - 1)]):
				data.append(v1)
				data.append(v2)

			if self.normalize:
				m = max(map(lambda a: a[1], data))
				data = map(lambda b: (b[0], b[1] / m), data)

			line = plot.PolyLine(data, legend='Port 0 %s' % self.legend, colour='black', width=1)
			self.gc = plot.PlotGraphics([line], self.title, self.xLabel, self.yLabel)
			### gestion automatique des bornes
			xMin, xMax, yMin, yMax = get_limit(data)

		##avec fusion (voir attribut 'fusion' de QuickScope)
		else:

			L = []
			xMin, xMax, yMin, yMax = 0, 0, 0, 0
			data_list = data.values()
			for ind, d in enumerate(data_list):

				### formatage des donnees specifique au square
				dd = []
				for v1, v2 in zip(d, [(d[i + 1][0], d[i][1]) for i in xrange(len(d) - 1)]):
					dd.append(v1)
					dd.append(v2)

				### gestion des couleures
				try:
					c = LColour[ind]
				except IndexError:
					c = LColour[0]

				if self.normalize:
					m = max(map(lambda a: a[1], dd))
					dd = map(lambda b: (b[0], b[1] / m), dd)

				L.append(plot.PolyLine(dd, legend='Port %d %s' % (ind, self.legend), colour=c, width=1))

				### gestion automatique des bornes
				a, b, c, d = get_limit(dd)

				if a < xMin: xMin = a
				if b > xMax: xMax = b
				if c < yMin: yMin = c
				if d > yMax: yMax = d

			self.gc = plot.PlotGraphics(L, self.title, self.xLabel, self.yLabel)

		self.client.Draw(self.gc, xAxis=(float(xMin), float(xMax)), yAxis=(float(yMin), float(yMax)))

	def OnPlotScatter(self, event=None):

		data = self.data

		## sans fusion
		if isinstance(data, list):
			if self.normalize:
				m = max(map(lambda a: a[1], data))
				data = map(lambda b: (b[0], b[1] / m), data)
			markers = plot.PolyMarker(data, colour=LColour[0], marker=Markers[0], size=1)
			line = plot.PolyLine(data, legend='Port 0 %s' % self.legend, colour=LColour[0], width=1)
			self.gc = plot.PlotGraphics([line, markers], self.title, self.xLabel, self.yLabel)
			xMin, xMax, yMin, yMax = get_limit(data)

		##avec fusion (voir attribut _fusion de QuickScope)
		else:
			L = []
			xMin, xMax, yMin, yMax = 0, 0, 0, 0
			data_list = data.values()
			for ind, d in enumerate(data_list):
				try:
					c = LColour[ind]
				except IndexError:
					c = LColour[0]

				try:
					m = Markers[ind]
				except IndexError:
					m = Markers[0]

				if self.normalize:
					m = max(map(lambda a: a[1], d))
					d = map(lambda b: (b[0], b[1] / m), d)

				L.append(plot.PolyLine(d, legend='Port 0 %s' % self.legend, colour=c, width=1))
				L.append(plot.PolyMarker(d, colour=c, marker=m, size=1))

				a, b, c, d = get_limit(d)

				if a < xMin: xMin = a
				if b > xMax: xMax = b
				if c < yMin: yMin = c
				if d > yMax: yMax = d

			self.gc = plot.PlotGraphics(L, self.title, self.xLabel, self.yLabel)

		self.client.Draw(self.gc, xAxis=(float(xMin), float(xMax)), yAxis=(float(yMin), float(yMax)))


	def OnPlotBar(self, event=None):
		data = self.data

		## sans fusion
		if isinstance(data, list):

			line = [plot.PolyLine([(c[0], 0), (c[0], c[1])], legend='', colour='gray', width=25) for c in data]
			self.gc = plot.PlotGraphics(line, self.title, self.xLabel, self.yLabel)
			xMin, xMax, yMin, yMax = get_limit(data)

		##avec fusion (voir attribut _fusion de QuickScope)
		else:
			L = []
			xMin, xMax = 0, 0
			yMin, yMax = 0, 0

			for k in data:
				d = data[k]
				for c in d:
					L.append(plot.PolyLine([(c[0], 0), (c[0], c[1])], legend='', colour='gray', width=25))

				a, b, c, d = get_limit(d)

				if a < xMin: xMin = a
				if b > xMax: xMax = b
				if c < yMin: yMin = c
				if d > yMax: yMax = d

			self.gc = plot.PlotGraphics(L, self.title, self.xLabel, self.yLabel)

		self.client.Draw(self.gc, xAxis=(float(xMin), float(xMax)), yAxis=(float(yMin), float(yMax)))

	def OnPlotAllSpectrum(self, evt=None):
		for k, s in self.data.items():
			frame = Spectrum(self, wx.ID_ANY, title=_("Spectrum of signal %d") % k, data=s)
			frame.Center()
			frame.Show()

	def OnPlotSpectrum(self, evt=None):
		"""
		"""

		# si mode fusion
		if isinstance(self.data, dict):
			#menu = evt.GetEventObject()
			item = self.mainmenu.FindItemById(evt.GetId())
			# permet d'identifier le numero du signal
			i = int(item.GetLabel().split(' ')[-1])
			frame = Spectrum(self, wx.ID_ANY, title=_("Spectrum of signal "), data=self.data[i])

		else:
			frame = Spectrum(self, wx.ID_ANY, title=_("Spectrum of signal "), data=self.data)

		frame.Center()
		frame.Show()

	def OnTitleSetting(self, event):
		dlg = wx.TextEntryDialog(self, _('Enter new title'), _('Title Entry'))
		dlg.SetValue(self.title)
		if dlg.ShowModal() == wx.ID_OK:
			self.title = dlg.GetValue()
			self.gc.setTitle(self.title)
			self.client.Redraw()
		dlg.Destroy()

	def OnXLabelSetting(self, event):
		dlg = wx.TextEntryDialog(self, _('Enter new X label'), _('Label Entry'))
		dlg.SetValue(self.xLabel)
		if dlg.ShowModal() == wx.ID_OK:
			self.xLabel = dlg.GetValue()
			self.gc.setXLabel(self.xLabel)
			self.client.Redraw()
		dlg.Destroy()

	def OnYLabelSetting(self, event):
		dlg = wx.TextEntryDialog(self, _('Enter new Y label'), _('Label Entry'))
		dlg.SetValue(self.yLabel)
		if dlg.ShowModal() == wx.ID_OK:
			self.yLabel = dlg.GetValue()
			self.gc.setYLabel(self.yLabel)
			self.client.Redraw()
		dlg.Destroy()


class DynamicPlot(PlotFrame):
	"""
	"""

	def __init__(self, parent=None, id=wx.ID_ANY, title="", atomicModel=None, xLabel="", yLabel="", iport=None):
		"""	
			@data : [(x,y)...]
			@iport: the number of port when the fusion option is disabled.
			@atomicModel: QuicScope atomic model used for its data
		"""

		PlotFrame.__init__(self, parent, id, title)

		# local copy
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
				self.Bind(wx.EVT_MENU, self.OnPlotSpectrum,
						  menu.Append(wx.NewId(), _('Signal %s') % str(i), _('Spectrum Plot')))
			self.Bind(wx.EVT_MENU, self.OnPlotAllSpectrum, menu.Append(wx.NewId(), _('All'), _('Spectrum Plot')))
		else:
			self.Bind(wx.EVT_MENU, self.OnPlotSpectrum,
					  menu.Append(wx.NewId(), _('Signal %s') % str(self.iport), _('Spectrum Plot')))
		self.mainmenu.Append(menu, _('&Spectrum'))

		self.timer = wx.Timer(self)
		### DEFAULT_PLOT_DYN_FREQ can be configured in preference-> simulation
		self.timer.Start(milliseconds=DEFAULT_PLOT_DYN_FREQ)

		self.Bind(wx.EVT_TIMER, self.OnTimerEvent)
		self.Bind(wx.EVT_PAINT, getattr(self, "On%s" % self.type))
		self.Bind(wx.EVT_CLOSE, self.OnQuit)

	def OnTimerEvent(self, event):
		self.GetEventHandler().ProcessEvent(wx.PaintEvent())

	def OnPlotLine(self, event):
		""" Plot process depends to the timer event.
		"""

		#if self.timer.IsRunning():
		### unbinding paint event

		if self.type != "PlotLine":
			self.type = "PlotLine"
			self.Unbind(wx.EVT_PAINT)
			self.Bind(wx.EVT_PAINT, getattr(self, "On%s" % self.type))

		### without fusion
		if self.iport is not None:

			data = self.atomicModel.results[self.iport]

			if self.normalize:
				m = max(map(lambda a: a[1], data))
				data = map(lambda b: (b[0], b[1] / m), data)

			line = plot.PolyLine(data, legend='Port 0 (%s)' % self.atomicModel.getBlockModel().label, colour='black',
								 width=1)
			self.gc = plot.PlotGraphics([line], self.title, self.xLabel, self.yLabel)
			xMin, xMax, yMin, yMax = get_limit(data)

		### with fusion (look QuickScope attribut _fusion)
		else:

			data = self.atomicModel.results
			label = self.atomicModel.getBlockModel().label

			L = []
			xMin, xMax, yMin, yMax = 0, 0, 0, 0
			data_list = data.values()
			for ind, d in enumerate(data_list):
				#ind = data_list.index(d)
				try:
					c = LColour[ind]
				except IndexError:
					c = LColour[0]

				if self.normalize:
					m = max(map(lambda a: a[1], d))
					d = map(lambda b: (b[0], b[1] / m), d)

				L.append(plot.PolyLine(d, legend='Port %s (%s)' % (str(data.keys()[ind]), label), colour=c, width=1))

				a, b, c, d = get_limit(d)

				if a < xMin: xMin = a
				if b > xMax: xMax = b
				if c < yMin: yMin = c
				if d > yMax: yMax = d

			self.gc = plot.PlotGraphics(L, self.title, self.xLabel, self.yLabel)

		try:
			self.client.Draw(self.gc, xAxis=(float(xMin), float(xMax)), yAxis=(float(yMin), float(yMax)))
		except Exception:
			sys.stdout.write(_("Error trying to plot"))

		if self.sim_thread is None or not self.sim_thread.isAlive():
			self.timer.Stop()

	def OnPlotSquare(self, event):

		#if self.timer.IsRunning():
		### unbinding paint event
		if self.type != "PlotSquare":
			self.type = "PlotSquare"
			self.Unbind(wx.EVT_PAINT)
			self.Bind(wx.EVT_PAINT, getattr(self, "On%s" % self.type))

		## sans fusion
		if self.iport is not None:

			d = self.atomicModel.results[self.iport]

			### formatage des donnees pour le square
			data = []
			for v1, v2 in zip(d, [(d[i + 1][0], d[i][1]) for i in xrange(len(d) - 1)]):
				data.append(v1)
				data.append(v2)

			if self.normalize:
				m = max(map(lambda a: a[1], data))
				data = map(lambda b: (b[0], b[1] / m), data)

			line = plot.PolyLine(data, legend='Port 0 (%s)' % self.atomicModel.getBlockModel().label, colour='black',
								 width=1)
			self.gc = plot.PlotGraphics([line], self.title, self.xLabel, self.yLabel)

			### gestion dynamique des bornes
			xMin, xMax, yMin, yMax = get_limit(data)

		##avec fusion (voir attribut 'fusion' de QuickScope)
		else:

			data = self.atomicModel.results
			label = self.atomicModel.getBlockModel().label

			L = []
			xMin, xMax = 0, 0
			yMin, yMax = 0, 0

			data_list = data.values()
			for ind, d in enumerate(data_list):

				### formatage des donnees pour le square
				dd = []
				for v1, v2 in zip(d, [(d[i + 1][0], d[i][1]) for i in xrange(len(d) - 1)]):
					dd.append(v1)
					dd.append(v2)

				### gestion de la couleur
				try:
					c = LColour[ind]
				except IndexError:
					c = LColour[0]

				if self.normalize:
					m = max(map(lambda a: a[1], dd))
					dd = map(lambda b: (b[0], b[1] / m), dd)

				### construction des donnees
				L.append(plot.PolyLine(dd, legend='Port %s (%s)' % (str(data.keys()[ind]), label), colour=c, width=1))

				###gestion dynamique des bornes
				a, b, c, d = get_limit(dd)

				if a < xMin: xMin = a
				if b > xMax: xMax = b
				if c < yMin: yMin = c
				if d > yMax: yMax = d

			self.gc = plot.PlotGraphics(L, self.title, self.xLabel, self.yLabel)

		try:
			self.client.Draw(self.gc, xAxis=(float(xMin), float(xMax)), yAxis=(float(yMin), float(yMax)))
		except Exception:
			sys.stdout.write(_("Error trying to plot"))

		if self.sim_thread is None or not self.sim_thread.isAlive():
			self.timer.Stop()

	def OnPlotScatter(self, event):

		#if self.timer.IsRunning():
		### unbinding paint event
		if self.type != "PlotScatter":
			self.type = "PlotScatter"
			self.Unbind(wx.EVT_PAINT)
			self.Bind(wx.EVT_PAINT, getattr(self, "On%s" % self.type))

		## sans fusion
		if self.iport is not None:

			data = self.atomicModel.results[self.iport]

			if self.normalize:
				m = max(map(lambda a: a[1], data))
				data = map(lambda b: (b[0], b[1] / m), data)

			markers = plot.PolyMarker(data, colour=LColour[0], marker=Markers[0], size=1)
			markers = plot.PolyLine(data, legend='Port 0 (%s)' % self.atomicModel.getBlockModel().label,
									colour=LColour[0], width=1)
			self.gc = plot.PlotGraphics([line, markers], self.title, self.xLabel, self.yLabel)
			xMin, xMax, yMin, yMax = get_limit(data)

		##avec fusion (voir attribut _fusion de QuickScope)
		else:

			data = self.atomicModel.results
			label = self.atomicModel.getBlockModel().label

			L = []
			xMin, xMax = 0, 0
			yMin, yMax = 0, 0

			data_list = data.values()
			for ind, d in enumerate(data_list):
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
					m = max(map(lambda a: a[1], d))
					d = map(lambda b: (b[0], b[1] / m), d)

				L.append(plot.PolyLine(d, colour=c, width=1))
				L.append(plot.PolyMarker(d, legend='Port %s (%s)' % (str(data.keys()[ind]), label), colour=c, marker=m,
										 size=1))

				a, b, c, d = get_limit(d)

				if a < xMin: xMin = a
				if b > xMax: xMax = b
				if c < yMin: yMin = c
				if d > yMax: yMax = d

			self.gc = plot.PlotGraphics(L, self.title, self.xLabel, self.yLabel)

		try:
			self.client.Draw(self.gc, xAxis=(float(xMin), float(xMax)), yAxis=(float(yMin), float(yMax)))
		except Exception:
			sys.stdout.write(_("Error trying to plot"))

		if self.sim_thread is None or not self.sim_thread.isAlive():
			self.timer.Stop()

	def OnPlotBar(self, event):

		#if self.timer.IsRunning():
		### unbinding paint event
		if self.type != "PlotBar":
			self.type = "PlotBar"
			self.Unbind(wx.EVT_PAINT)
			self.Bind(wx.EVT_PAINT, getattr(self, "On%s" % self.type))

		## sans fusion
		if self.iport is not None:
			data = self.atomicModel.results[self.iport]

			line = [plot.PolyLine([(c[0], 0), (c[0], c[1])], legend='', colour='gray', width=25) for c in data]
			self.gc = plot.PlotGraphics(line, self.title, self.xLabel, self.yLabel)
			xMin, xMax, yMin, yMax = get_limit(data)

		##avec fusion (voir attribut _fusion de QuickScope)
		else:
			data = self.atomicModel.results

			L = []
			xMin, xMax, yMin, yMax = 0, 0, 0, 0
			data_list = data.values()
			for ind, d in enumerate(data_list):
				#ind = data_list.index(d)
				try:
					c = LColour[ind]
				except IndexError:
					c = LColour[0]

				for c in d:
					L.append(plot.PolyLine([(c[0], 0), (c[0], c[1])], legend='', colour='gray', width=25))

				a, b, c, d = get_limit(d)

				if a < xMin: xMin = a
				if b > xMax: xMax = b
				if c < yMin: yMin = c
				if d > yMax: yMax = d

			self.gc = plot.PlotGraphics(L, self.title, self.xLabel, self.yLabel)

		try:

			self.client.Draw(self.gc, xAxis=(float(xMin), float(xMax)), yAxis=(float(yMin), float(yMax)))
		except Exception:
			sys.stdout.write(_("Error trying to plot"))

		if self.sim_thread is None or not self.sim_thread.isAlive():
			self.timer.Stop()

	def OnPlotAllSpectrum(self, evt):
		""" Plot all spectrum.
		"""
		for k, s in self.atomicModel.results.items():
			frame = Spectrum(self, wx.ID_ANY, title=_("Spectrum of signal %d") % k, data=s)
			frame.Center()
			frame.Show()

	def OnPlotSpectrum(self, evt):
		""" Plot spectrum.
		"""

		item = self.mainmenu.FindItemById(evt.GetId())
		# permet d'identifier le numero du signal
		i = int(item.GetLabel().split(' ')[-1])

		frame = Spectrum(self, wx.ID_ANY, title=_("Spectrum of signal "), data=self.atomicModel.results[i])
		frame.Center()
		frame.Show()

	def OnTitleSetting(self, event):
		dlg = wx.TextEntryDialog(self, _('Enter new title'), _('Title Entry'))
		dlg.SetValue(self.title)
		if dlg.ShowModal() == wx.ID_OK:
			self.title = dlg.GetValue()
			self.gc.setTitle(self.title)
			self.client.Redraw()
		dlg.Destroy()

	def OnXLabelSetting(self, event):
		dlg = wx.TextEntryDialog(self, _('Enter new X label'), _('Label Entry'))
		dlg.SetValue(self.xLabel)
		if dlg.ShowModal() == wx.ID_OK:
			self.xLabel = dlg.GetValue()
			self.gc.setXLabel(self.xLabel)
			self.client.Redraw()
		dlg.Destroy()

	def OnYLabelSetting(self, event):
		dlg = wx.TextEntryDialog(self, _('Enter new Y label'), _('Label Entry'))
		dlg.SetValue(self.yLabel)
		if dlg.ShowModal() == wx.ID_OK:
			self.yLabel = dlg.GetValue()
			self.gc.setYLabel(self.yLabel)
			self.client.Redraw()
		dlg.Destroy()


class Spectrum(StaticPlot):
	def __init__(self, parent=None, id=wx.ID_ANY, title="", data=None):
		"""	@data : [(x,y)...]
		"""
		if not data: data = []

		# total time
		duree = data[-1][0]

		signal = [c[1] for c in data]

		Nb_pts = len(signal)

		#interpolation B-splines
		#dx = 1
		#newx = r_[0:Nb_pts:duree]
		#y = array(self.signal)
		#newy = cspline1d_eval(cspline1d(y),newx,dx = dx,x0 = y[0])
		#self.signal = newy

		# nombre de points pour la fft
		p = 1
		while pow(2, p) <= Nb_pts:
			p += 1
			N = float(pow(2, p))
		assert (pow(2, p) >= Nb_pts)

		#application d'une fenetre
		signal = Utilities.smooth(array(signal), window_len=10, window="hamming")

		# frequence d'echantillonnage
		Fe = 1.0 / (float(duree) / float(len(signal)))

		#FFT
		Y = fft.fft(signal, int(N))
		Y = abs(fft.fftshift(Y))
		F = [Fe * i / N for i in xrange(int(-N / 2), int(N / 2))]

		# normalisation
		Max = max(Y)
		Y = [20 * math.log(i / Max, 10) for i in Y]

		#frequence max et min pour le plot
		FMin, FMax = 0, 200
		F_plot, Y_plot = [], []
		for i in xrange(len(F)):
			if FMin < F[i] < FMax:
				F_plot.append(F[i])
				Y_plot.append(Y[i])

		# formate les donnees pour Plot
		self.data = map(lambda a, b: (a, b), F_plot, Y_plot)

		# invoque la frame
		StaticPlot.__init__(self, parent, id, title, self.data, xLabel=_('Frequency [Hz]'), yLabel=_('Amplitude [dB]'))

		self.OnPlotLine()

		# range for fred and amplitude
		self.sldh.SetRange(1, 300)
		self.sldv.SetRange(0, 150)

		# start freq 100
		self.sldh.SetValue(100)
		# start amplitude 0
		self.sldv.SetValue(0)

		# Bind the Sliders
		self.Bind(wx.EVT_SLIDER, self.sliderUpdate, id=self.sldh.GetId())
		self.Bind(wx.EVT_SLIDER, self.sliderUpdate, id=self.sldv.GetId())

	def sliderUpdate(self, event):
		posh = self.sldh.GetValue()
		posv = self.sldv.GetValue()
		self.Redraw(self.Rescale(posv, posh))

	def Redraw(self, data=None):
		""" Redraw the client
		"""
		if not data: data = []
		size = self.client.GetSize()
		self.client.Clear()
		self.client.SetInitialSize(size=size)

		#xLabel = _('Frequency [Hz]')
		#yLabel = _('Amplitude [dB]')
		line = plot.PolyLine(data, legend='', colour='black', width=1)
		gc = plot.PlotGraphics([line], '', self.xLabel, self.yLabel)
		xMin, xMax, yMin, yMax = get_limit(data)
		self.client.Draw(gc, xAxis=(float(xMin), float(xMax)), yAxis=(float(yMin), float(yMax)))

	def Rescale(self, FMin=0, FMax=200):
		#frequence max et min pour le plot
		F, Y, F_plot, Y_plot = [], [], [], []
		for f, v in self.data:
			F.append(f)
			Y.append(v)
		for i in xrange(len(F)):
			if FMin < F[i] < FMax:
				F_plot.append(F[i])
				Y_plot.append(Y[i])

		# formate les donnees pour Plot
		return map(lambda a, b: (a, b), F_plot, Y_plot)