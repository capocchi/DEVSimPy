# -*- coding: utf-8 -*-
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# Plot.py --- Ploting class
#                     --------------------------------
#                        Copyright (c) 2010
#                       Laurent CAPOCCHI
#                      University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 12/02/10 
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

import wx, os, sys, math
import wx.lib.plot as plot

_ = wx.GetTranslation

# for spectrum
try:
	from numpy import *
except ImportError:
	sys.stdout.write(_("Warning: Numpy module not found (www.scipy.org)"))
finally:
	try:
		from scipy.signal import cspline1d, cspline1d_eval
	except ImportError:
		sys.stdout.write(_("Warning: Scipy module not found (www.scipy.org)"))

from smooth import smooth

LColour=['black', 'red', 'green','blue','yellow','gray','magenta', 'maroon','orange','salmon','pink','plum']

class Plot(wx.Frame):
	def __init__(self, parent = None, id = wx.ID_ANY, title = _("Time Plotting"), data = None, xLabel = _('Time [s]'), yLabel = _('Amplitude [A]')):
		'''	@data : [(x,y)...]
		'''

		wx.Frame.__init__(self, parent, id, title, size = (800, 500))
		
		# local copy
		self.data = data

		##Now Create the menu bar and items
		self.mainmenu = wx.MenuBar()

		menu = wx.Menu()
		self.Bind(wx.EVT_MENU, self.OnFilePageSetup, menu.Append(wx.NewId(), _('Page Setup'), _('Setup the printer page')))
		self.Bind(wx.EVT_MENU, self.OnFilePrintPreview, menu.Append(wx.NewId(), _('Print Preview'), _('Show the current plot on page')))
		self.Bind(wx.EVT_MENU, self.OnFilePrint, menu.Append(wx.NewId(), _('Print'), _('Print the current plot')))
		self.Bind(wx.EVT_MENU, self.OnSaveFile, menu.Append(wx.NewId(), _('Save Plot'), _('Save current plot')))
		self.Bind(wx.EVT_MENU, self.OnFileExit, menu.Append(wx.NewId(), _('E&xit'), _('Enough of this already!')))
		self.mainmenu.Append(menu, _('&File'))

		menu = wx.Menu()
		self.Bind(wx.EVT_MENU,self.OnPlotRedraw, menu.Append(wx.NewId(), _('&Redraw'), _('Redraw plots')))
		self.Bind(wx.EVT_MENU,self.OnPlotScale, menu.Append(wx.NewId(), _('&Scale'), _('Scale canvas')))
		self.Bind(wx.EVT_MENU,self.OnEnableZoom, menu.Append(wx.NewId(), _('Enable &Zoom'), _('Enable Mouse Zoom'), kind=wx.ITEM_CHECK)) 
		self.Bind(wx.EVT_MENU,self.OnEnableGrid,  menu.Append(wx.NewId(), _('Enable Grid'), _('Enable Mouse Zoom'), kind=wx.ITEM_CHECK))
		self.Bind(wx.EVT_MENU,self.OnEnableDrag, menu.Append(wx.NewId(), _('Enable Drag'), _('Enable Mouse Zoom'), kind=wx.ITEM_CHECK))
		self.Bind(wx.EVT_MENU,self.OnEnableLegend, menu.Append(wx.NewId(), _('Enable &Legend'), _('Turn on Legend'), kind=wx.ITEM_CHECK))
		self.Bind(wx.EVT_MENU,self.OnEnablePointLabel, menu.Append(wx.NewId(), _('Enable &Point Label'), _('Show Closest Point'), kind=wx.ITEM_CHECK))
		self.Bind(wx.EVT_MENU,self.OnScrUp, menu.Append(wx.NewId(), _('Scroll Up 1'), _('Move View Up 1 Unit'))) 
		self.Bind(wx.EVT_MENU,self.OnScrRt, menu.Append(wx.NewId(), _('Scroll Rt 2'), _('Move View Right 2 Units')))
		self.Bind(wx.EVT_MENU,self.OnReset, menu.Append(wx.NewId(), _('&Plot Reset'), _('Reset to original plot')))
		self.mainmenu.Append(menu, _('&Plot'))
		
		menu = wx.Menu()
		### si mode fusion
		if isinstance(self.data,dict):
			for i in range(len(self.data)):
				self.Bind(wx.EVT_MENU,self.OnPlotSpectrum, menu.Append(wx.NewId(), _('Signal %d')%i, _('Spectrum Plot')))
			self.Bind(wx.EVT_MENU,self.OnPlotAllSpectrum, menu.Append(wx.NewId(), _('All'), _('Spectrum Plot')))
		else:
			self.Bind(wx.EVT_MENU,self.OnPlotSpectrum, menu.Append(wx.NewId(), _('Signal'), _('Spectrum Plot')))
		self.mainmenu.Append(menu, _('&Spectrum'))
		
		self.SetMenuBar(self.mainmenu)

		# A status bar to tell people what's happening
		self.CreateStatusBar(1)
		
		self.client = plot.PlotCanvas(self)

		## sans fusion
		if isinstance( self.data, list):
			
			line = plot.PolyLine(data, legend = '', colour = 'black', width = 1)
			gc = plot.PlotGraphics([line], '', xLabel, yLabel)

			xMin,xMax = min([ c[0] for c in data ]),max([ c[0] for c in data ])
			yMin,yMax = min([ c[1] for c in data ]),max([ c[1] for c in data ])
		##avec fusion (voir attribut _fusion de QuickScope)
		else:
			L=[]
			xMin, xMax = 0,0
			yMin, yMax = 0,0
			for d in self.data.values():
				L.append(plot.PolyLine(d, legend = '', colour = LColour[self.data.values().index(d)], width=1))
				
				a,b = min([ c[0] for c in d ]),max([ c[0] for c in d ])
				c,d = min([ c[1] for c in d ]),max([ c[1] for c in d ])

				if a < xMin: xMin=a
				if b > xMax: xMax= b
				if c < yMin: yMin=c
				if d > yMax:yMax=d

			gc = plot.PlotGraphics(L, '', xLabel, yLabel)
			
		self.client.Draw(gc, xAxis = (float(xMin),float(xMax)), yAxis = (float(yMin),float(yMax)))
		
		self.client.canvas.Bind(wx.EVT_LEFT_DOWN, self.OnMouseLeftDown)
		## Show closest point when enabled
		self.client.canvas.Bind(wx.EVT_MOTION, self.OnMotion)
		
		wx.EVT_CLOSE(self, self.OnQuit)

	def OnQuit(self, event):
		self.Destroy()

	def OnPlotAllSpectrum(self,evt):

		for k,s in self.data.items():
			frame = Spectrum(self,wx.ID_ANY, title= _("Spectrum of signal %d")%k,data=s)
			frame.Center()
			frame.Show()

	def OnPlotSpectrum(self, evt):
		'''
		'''

		# si mode fusion
		if isinstance(self.data,dict):
			#menu = evt.GetEventObject()
			item=self.mainmenu.FindItemById(evt.GetId())
			# permet d'identifier le numero du signal
			i = int(item.GetLabel().split(' ')[-1])
			frame = Spectrum(self,wx.ID_ANY, title= _("Spectrum of signal "),data=self.data[i])
			
		else:
			frame = Spectrum(self,wx.ID_ANY, title= _("Spectrum of signal "),data=self.data)
		
		frame.Center()
		frame.Show()

	def OnMouseLeftDown(self,event):
		s= _("Left Mouse Down at Point: (%.4f, %.4f)") % self.client._getXY(event)
		self.SetStatusText(s)
		event.Skip()            #allows plotCanvas OnMouseLeftDown to be called
	
	def OnMotion(self, event):
		#show closest point (when enbled)
		if self.client.GetEnablePointLabel() == True:
			#make up dict with info for the pointLabel
			#I've decided to mark the closest point on the closest curve
			dlst= self.client.GetClosestPoint( self.client._getXY(event), pointScaled= True)
			if dlst != []:    #returns [] if none
				curveNum, legend, pIndex, pointXY, scaledXY, distance = dlst
				#make up dictionary to pass to my user function (see DrawPointLabel) 
				mDataDict= {"curveNum":curveNum, "legend":legend, "pIndex":pIndex,\
							"pointXY":pointXY, "scaledXY":scaledXY}
				#pass dict to update the pointLabel
				self.client.UpdatePointLabel(mDataDict)
		event.Skip()           #go to next handler

	def OnFilePageSetup(self, event):
		self.client.PageSetup()
		
	def OnFilePrintPreview(self, event):
		self.client.PrintPreview()
		
	def OnFilePrint(self, event):
		self.client.Printout()
		
	def OnSaveFile(self, event):
		self.client.SaveFile()

	def OnFileExit(self, event):
		self.Close()

	def OnPlotRedraw(self,event):
		self.client.Redraw()
		
	def OnPlotScale(self, event):
		if self.client.last_draw != None:
			graphics, xAxis, yAxis= self.client.last_draw
			self.client.Draw(graphics,(1,3.05),(0,1))

	def OnEnableZoom(self, event):
		self.client.SetEnableZoom(event.IsChecked())
		self.mainmenu.Check(217, not event.IsChecked())
		
	def OnEnableGrid(self, event):
		self.client.SetEnableGrid(event.IsChecked())
		
	def OnEnableDrag(self, event):
		self.client.SetEnableDrag(event.IsChecked())
		self.mainmenu.Check(214, not event.IsChecked())
		
	def OnEnableLegend(self, event):
		self.client.SetEnableLegend(event.IsChecked())

	def OnEnablePointLabel(self, event):
		self.client.SetEnablePointLabel(event.IsChecked())

	def OnScrUp(self, event):
		self.client.ScrollUp(1)
		
	def OnScrRt(self,event):
		self.client.ScrollRight(2)

	def OnReset(self,event):
		self.client.Reset()

	def resetDefaults(self):
		"""Just to reset the fonts back to the PlotCanvas defaults"""
		self.client.SetFont(wx.Font(10,wx.SWISS,wx.NORMAL,wx.NORMAL))
		self.client.SetFontSizeAxis(10)
		self.client.SetFontSizeLegend(7)
		self.client.setLogScale((False,False))
		self.client.SetXSpec('auto')
		self.client.SetYSpec('auto')

class Spectrum(Plot):
	def __init__(self, parent=None, id=wx.ID_ANY, title=_("Spectrum Plotting"), data=[]):
		'''	@data : [(x,y)...]
		'''
		
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
		
		# nombre de points pour la fft
		p=1
		while(pow(2,p)<=Nb_pts):
			p+=1
			N=float(pow(2,p))
		assert(pow(2,p)>= Nb_pts)

		#application d'une fenetre
		signal = smooth(array(signal),window_len=10,window="hamming")
		
		# frequence d'echantillonnage
		Fe = 1.0/(float(duree)/float(len(signal)))

		#FFT
		Y = fft.fft(signal,int(N))
		Y = abs(fft.fftshift(Y))
		F = [Fe*i/N for i in range(int(-N/2), int(N/2))]

		# normalisation
		Max = max(Y)
		Y = [20*math.log(i/Max,10) for i in Y]

		#frequence max et min pour le plot
		FMin, FMax=0,200
		F_plot, Y_plot=[],[]
		for i in range(len(F)):
			if FMin<F[i]<FMax:
				F_plot.append(F[i])
				Y_plot.append(Y[i])
		
		# formate les donnees pour Plot
		self.data = map(lambda a,b:(a,b),F_plot,Y_plot)

		# invoque la frame
		self.frame = Plot.__init__(self, parent, id, title,self.data,xLabel=_('Frequency [Hz]'),yLabel=_('Amplitude [dB]'))

		#supression de l'item spectrum
		spectrumMenu=self.mainmenu.FindMenu(_('&Spectrum'))
		self.mainmenu.Remove(spectrumMenu)
	
		#menu = wx.Menu()
		#menu.Append(ID_SPECTRUM_SETTING, 'Setting', 'Spectrum Setting')
		#self.Bind(wx.EVT_MENU,self.OnSettingSpectrum, id=ID_SPECTRUM_SETTING)
		#self.mainmenu.Append(menu, '&Setting')
		
	def OnSettingSpectrum(self, evt):
		self.Redraw(self.Rescale(0,100))

	def Redraw(self,data=[]):
		size=self.client.GetSize()
		self.client.Clear()
		self.client = plot.PlotCanvas(self)
		self.client.SetInitialSize(size=size)

		xLabel=_('Frequency [Hz]')
		yLabel=_('Amplitude [dB]')
		line = plot.PolyLine(data, legend='', colour='black', width=1)
		gc = plot.PlotGraphics([line], '', xLabel, yLabel)

		xMin,xMax=min([ c[0] for c in data ]),max([ c[0] for c in data ])
		yMin,yMax=min([ c[1] for c in data ]),max([ c[1] for c in data ])
		
		self.client.Draw(gc,  xAxis= (float(xMin),float(xMax)), yAxis= (float(yMin),float(yMax)))

	def Rescale(self,FMin=0,FMax=200):
		#frequence max et min pour le plot
		F,Y,F_plot, Y_plot=[],[],[],[]
		for f,v in self.data:
			F.append(f)
			Y.append(v)
		for i in range(len(F)):
			if FMin<F[i]<FMax:
				F_plot.append(F[i])
				Y_plot.append(Y[i])
		
		# formate les donnees pour Plot
		return map(lambda a,b:(a,b),F_plot,Y_plot)