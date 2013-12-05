# -*- coding: utf-8 -*-

"""
	Authors: L. Capocchi (capocchi@univ-corse.fr)
	Date: 03/12/2013
	Description:
		Give the abstract simulator three from master model.
		Its appear when user want simulate a model by clicking on the "Ok" button in the simulation dialogue.
		The three depends on the simulation strategy chosen by the user.
	Depends: python-networkx, python-profiler(for gato) (for windows user: matplotlib (http://sourceforge.net/projects/matplotlib/files/)and networkx )
	User can find all of these package from http://www.lfd.uci.edu/~gohlke/pythonlibs/
"""

import sys
import os
import wx
import random

# to send event
if wx.VERSION_STRING < '2.9':
	from wx.lib.pubsub import Publisher as pub
else:
	from wx.lib.pubsub import setuparg1
	from wx.lib.pubsub import pub

#for ploting
try:
	import pylab
except ImportError, info:
	platform_sys = os.name
	if platform_sys in ('nt', 'mac'):
		msg = _("ERROR: Matplotlib module not found.\nhttp://sourceforge.net/projects/matplotlib/files/\nor http://www.lfd.uci.edu/~gohlke/pythonlibs/")
		sys.stderr.write(msg)
		raise ImportError, "%s\n%s"%(msg,info)
	elif platform_sys == 'posix':
		msg = _("ERROR: Matplotlib module not found.\nPlease install the python-matplotlib package.\n")
		sys.stderr.write(msg)
		raise ImportError, "%s\n%s"%(msg,info)
	else:
		msg = _("Unknown operating system.\n")
		sys.stdout.write(msg)
		raise ImportError, "%s\n%s"%(msg,info)

# for graph
try:
	import networkx as nx
except ImportError, info:
	platform_sys = os.name
	if platform_sys in ('nt', 'mac'):
		msg = _("ERROR: Networkx module not found.\nhttp://networkx.lanl.gov/download/networkx/\nor http://www.lfd.uci.edu/~gohlke/pythonlibs/\n")
		sys.stderr.write(msg)
		raise ImportError, "%s\n%s"%(msg,info)
	elif platform_sys == 'posix':
		msg = _("ERROR: Networkx module not found.\nPlease install the python-networkx package.\n")
		sys.stderr.write(msg)
		raise ImportError, "%s\n%s"%(msg,info)
	else:
		msg = _("Unknown operating system.\n")
		sys.stdout.write(msg)
		raise ImportError, "%s\n%s"%(msg,info)

import pluginmanager

from Container import CodeBlock
from DomainInterface.DomainBehavior import DomainBehavior
from DomainInterface.DomainStructure import DomainStructure
from DomainInterface.MasterModel import Master
from Components import DEVSComponent

def getSimulatorTree(devs, graph, par):
	"""
	"""

	block = DEVSComponent.getBlockModel(devs)
	label = block.label
	id = devs.myID

	if isinstance(devs, DomainBehavior):
		graph.add_edge(par, "%s(%s)"%(label, id), color='b')
	elif isinstance(devs, (DomainStructure, Master)):
		graph.add_edge(par, "%s(%s)"%(label, id), color='m')
		for c in devs.componentSet:
			getSimulatorTree(c, graph, "%s(%s)"%(label, id))
	return graph

def dep(arg):
	'''
	    Dependency resolver

	"arg" is a dependency dictionary in which
	the values are the dependencies of their respective keys.
	if __name__=='__main__':
    d=dict(
        a=('b','c'),
        b=('c','d'),
        e=(),
        f=('c','e'),
        g=('h','f'),
        i=('f',)
    )
    print dep(d)
	'''
	d=dict((k, set(arg[k])) for k in arg)
	r=[]
	while d:
	    # values not in keys (items without dep)
	    t=set(i for v in d.values() for i in v)-set(d.keys())
	    # and keys without value (items without dep)
	    t.update(k for k, v in d.items() if not v)
	    # can be done right away
	    r.append(t)
	    # and cleaned up
	    d=dict(((k, v-t) for k, v in d.items() if v))
	return r

###
class Graph:
	""" NX Graph class with nx grpah attribut
	"""
	def __init__(self, master, parent):
		""" Constructor.
		"""

		self.master = master
		self.parent = parent

		self.diagram = self.master.getBlockModel()

		# graph
		self.graph = getSimulatorTree(self.diagram.getDEVSModel(), nx.DiGraph(), self.diagram.label)

	def PopulateGraph(self):
		"""
		"""
		label = self.diagram.label

		### remove the node corresponding to the master diagram (the first one on the top)
		self.graph.remove_node(label)

		### list of edges and color
		edges,edge_colors = zip(*nx.get_edge_attributes(self.graph,'color').items())

		### list of nodes
		nodes = []
		for c1,c2 in edges:
			if c1 not in nodes and label != c1:
				nodes.append(c1)
			if c2 not in nodes and label != c2:
				nodes.append(c2)

		node_colors=[]
		edge_labels = []
		### list of node colors
		for block in map(self.diagram.GetShapeByLabel, map(lambda a: a.split('(')[0], nodes)):
			### SimulatorSolver is blue
			if isinstance(block, CodeBlock):
				node_colors.append('b')
			else:
				### CoupledSolver is yellow if there is the root red else
				### test if GetShapeByLabel return False because diagram have not block
				if isinstance(block, bool):
					node_colors.append('y')
				else:
					node_colors.append('r')

		### odes size
		node_sizes = [ 800 for node in nodes]

		#try:
		#	pos=nx.graphviz_layout(graph, prog='dot')
		#except ValueError:
		pos=nx.spring_layout(self.graph)

		### draw the graph
		nx.draw(self.graph, pos, edgelist=edges, nodelist=nodes, edge_color=edge_colors, node_color=node_colors, node_size = node_sizes, width=2)

		### draw activity edge label
 		edge_labels=dict([((u,v,),round(self.getActivity(u)+self.getActivity(v),3)) for u,v,d in self.graph.edges(data=True)])
 	 	nx.draw_networkx_edge_labels(self.graph,pos,edge_labels=edge_labels)

	###
 	def getActivity(self, label, key='cpu'):
 		""" Return the activity key from model with label
 		"""
 		### get block because devs must be get dynamically
 		block = self.diagram.GetShapeByLabel(label.split('(')[0])
 		### if instance is code block (atomic model)
 		if isinstance(block, CodeBlock):
 			devs = block.getDEVSModel()
 			if devs and hasattr(devs, 'activity'):
 				return devs.activity[key]
 		 	else:
 		 		return 0.0
 		### container block or other doesn't have activity
 		else:
 			return 0.0

	def OnUpdate(self, evt):
		""" Update the figure with the activity value
			### TODO : test is edge_label have changed
		"""

 		if hasattr(self, 'fig'):
	 		pos=nx.spring_layout(self.graph)

			### weight evolution
	 		edge_labels=dict([((u,v,),round(self.getActivity(u)+self.getActivity(v),3)) for u,v,d in self.graph.edges(data=True)])

			###---------------------------
			nx.draw_networkx_edge_labels(self. graph,pos,edge_labels=edge_labels)
			# redraw the canvas
			self.fig.canvas.draw_idle()

	def setFig(self, fig):
		self.fig = fig

@pluginmanager.register("START_DIAGRAM")
def start_diagram(*args, **kwargs):
	""" Start the diagram frame.
	"""

	master = kwargs['master']
	parent = kwargs['parent']

 	dia = master.getBlockModel()
#
# 	###-------------------------------
	import matplotlib
	matplotlib.use('WXAgg')
	f = pylab.figure()

	### title of windows is label
	fig = pylab.gcf()
	fig.canvas.set_window_title("%s - Abstract simulator three"%dia.label)

	graph = Graph(master, parent)
	graph.PopulateGraph()
	graph.setFig(fig)

	#pub().subscribe(graph.OnUpdate, ("activity"))
	wx.EVT_IDLE(parent, graph.OnUpdate)
	f.autofmt_xdate()
	f.show()

	### The START_ACTIVITY_TRACKING event occurs
	pluginmanager.trigger_event("VIEW_ACTIVITY_REPORT", parent=parent, master=dia.getDEVSModel())

def Config(parent):
	""" Plugin settings frame.
	"""
	dlg = wx.MessageDialog(parent, _('No settings available for this plugin\n'), _('Diagram plugin configuration'), wx.OK | wx.ICON_EXCLAMATION)
	dlg.ShowModal()