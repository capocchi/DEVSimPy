# -*- coding: utf-8 -*-

"""
-------------------------------------------------------------------------------
 Name:          PlotlyStream.py
 Model:         Plot input data as a graph for plot.ly (https://plot.ly/)
 Authors:       L. Capocchi (capocchi@univ-corse.fr)
 Organization:  UMR CNRS 6134
 Date:          04/11/2016
 License:       GPL V3.0
-------------------------------------------------------------------------------
"""

### Specific import ------------------------------------------------------------
from DomainInterface.DomainBehavior import DomainBehavior
from DomainInterface.Object import Message

import chart_studio.plotly as py
import plotly.graph_objects as go

#import plotly.plotly as py
#from plotly.graph_objs import *

import time

# Patch TIC : 
#  TIC server antivirus does not send any data through a persistent HTTP request
#  until the request is closed. 
CT_MAX_DELAY = 2.0; # seconds, should be less than 1minute or stream will be closed by server

### Model class ----------------------------------------------------------------
class PlotlyStream(DomainBehavior):
	''' DEVS Class for PlotlyStream model
	'''

	def __init__(self, fn='test', token='', key='', username='', plotUrl='',
				sharing=['public', 'private', 'secret'],
				fileopt = ['new', 'overwrite', 'extend', 'append']):
		''' Constructor.

			fn (string) -- the name that will be associated with this figure
			fileopt ('new' | 'overwrite' | 'extend' | 'append') -- 'new' creates a
				'new': create a new, unique url for this plot
				'overwrite': overwrite the file associated with `filename` with this
				'extend': add additional numbers (data) to existing traces
				'append': add additional traces to existing data lists
			world_readable (default=True) -- make this figure private/public
			auto_open (default=True) -- Toggle browser options
				True: open this plot in a new browser tab
				False: do not open plot in the browser, but do return the unique url
			sharing ('public' | 'private' | 'sharing') -- Toggle who can view this graph
				- 'public': Anyone can view this graph. It will appear in your profile 
					and can appear in search engines. You do not need to be 
					logged in to Plotly to view this chart.
				- 'private': Only you can view this plot. It will not appear in the
					Plotly feed, your profile, or search engines. You must be
					logged in to Plotly to view this graph. You can privately
					share this graph with other Plotly users in your online
					Plotly account and they will need to be logged in to
					view this plot.
				- 'secret': Anyone with this secret link can view this chart. It will
					not appear in the Plotly feed, your profile, or search
					engines. If it is embedded inside a webpage or an IPython
					notebook, anybody who is viewing that page will be able to
					view the graph. You do not need to be logged in to view
					this plot.
		'''
		DomainBehavior.__init__(self)
		
		if token != '' and key != '' and username != '':
			py.sign_in(username, key)
			trace1 = Scatter(
				x=[],
				y=[],
				stream=dict(token=token)
			)
			data = Data([trace1])
			self.plotUrl = py.plot(data, filename=fn, auto_open=False, sharing=sharing[0], fileopt=fileopt[0])
			#print(self.plotUrl)
			self.s = py.Stream(token)
			self.s.open()
			# patch TIC
			self.sTime = time.time()
			self.sNbData = 0
			self.x = []
			self.y = []
		else:
			self.s = None

		self.state = {	'status': 'IDLE', 'sigma':INFINITY}

	def extTransition(self):
		''' DEVS external transition function.
		'''
		msg = self.peek(self.IPorts[0])
		#print(msg.time)
		if self.s: 
			#self.s.write(dict(x=msg.time, y=msg.value[0]))
			# patch TIC
			self.x.append(msg.time)
			self.y.append(msg.value[0])
			self.sNbData += 1

		self.state['sigma'] = 0

	def outputFnc(self):
		''' DEVS output function.
		'''
		pass

	def intTransition(self):
		''' DEVS internal transition function.
		'''
		#patch TIC
		now = time.time()
		if (self.sNbData >= 100) or (now - self.sTime >= CT_MAX_DELAY):
			self.s.write(dict(x=self.x, y=self.y))
			self.s.close();
			self.s.open();
			#print('close/open')
			self.sNbData = 0
			self.sTime = now
		
		self.state["sigma"] = INFINITY
		return self.state

	def timeAdvance(self):
		''' DEVS Time Advance function.
		'''
		return self.state['sigma']

	def finish(self, msg):
		''' Additional function which is lunched just before the end of the simulation.
		'''
		if self.s:
			self.s.close()
