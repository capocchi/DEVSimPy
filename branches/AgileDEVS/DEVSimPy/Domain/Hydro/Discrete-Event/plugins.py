# -*- coding: utf-8 -*-

import wx

def OnLeftDClick(self, event):
	""" Left Double Click has been invocked.
		This plugin call pdist function from hcluster package and
		plot the dendrogram using matplotlib.pyplot package.
	"""
	COLOR = ('red', 'green', 'grey', 'blue', 'yellow', 'cyan', 'black', 'magenta')
	#canvas = event.GetEventObject()
	#model = canvas.getCurrentShape(event)
	devs = self.getDEVSModel()
	if devs:
		import numpy

		import matplotlib
		matplotlib.use('WXAgg') # do this before importing pylab
		import pylab

		f = pylab.figure()
		
		### title of windows is label
		fig = pylab.gcf()
		fig.canvas.set_window_title(self.label)

		### title of canavs is given by the user
		pylab.title(devs.title)

		self.line = {}

		if devs.fusion:
			ax = f.add_subplot(1,1,1)
			for i in devs.y:
				y = devs.y[i]
				N = len(y)	
				x = numpy.arange(N)
				typ = devs.typ
				if typ == 'bar':
					line, = ax.bar(x, y, facecolor=COLOR[i], alpha=0.75)
				elif typ == 'line':
					line, = ax.plot(x,y)
				
				self.line[i]=line

				ax.grid(True)
				#Create a y label
				ax.set_ylabel('Volume [m3]')
				ax.set_xticks(x)
				ax.set_xticklabels([i for i in range(N)])
		else:
			for i in devs.y:
				y = devs.y[i]
				N = len(y)	
				x = numpy.arange(N)
				ax = f.add_subplot(len(devs.y),1,i+1)
				typ = devs.typ
				if typ == 'bar':
					line, = ax.bar(x, y, facecolor=COLOR[i], alpha=0.75)
				elif typ == 'line':
					line, = ax.plot(x,y)

				self.line[i]=line
				ax.grid(True)
				#Create a y label
				ax.set_ylabel('Volume [m3]')
				ax.set_xticks(x)
				ax.set_xticklabels([i for i in range(N)])

		def update_line(idleevent):
			for i in devs.y:
				y = devs.y[i]
#				N = len(y)	
#				x = numpy.arange(N)
				self.line[i].set_ydata(y)
				try:
					fig.canvas.draw_idle()                 # redraw the canvas
				except:
					pass
		import wx
		wx.EVT_IDLE(wx.GetApp(), update_line)
		f.autofmt_xdate()
		f.show()		
	else:
		wx.MessageBox(_("No DEVS model is instanciated.\nGo back to the simulation!"), _("Info"), wx.OK|wx.ICON_INFORMATION)

def Config(parent):
	print parent