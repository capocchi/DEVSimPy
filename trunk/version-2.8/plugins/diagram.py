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

	label = DEVSComponent.getBlockModel(devs).label
	id = devs.myID

	if isinstance(devs, DomainBehavior):
		graph.add_edge(par, "%s(%s)"%(label, id), weight=0.0, color='b')
	elif isinstance(devs, (DomainStructure, Master)):
		graph.add_edge(par, "%s(%s)"%(label, id), weight=0.0, color='m')
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


@pluginmanager.register("START_DIAGRAM")
def start_diagram(*args, **kwargs):
	""" Start the diagram frame.
	"""

	dia = kwargs['diagram']

	###-------------------------------
	import matplotlib
	matplotlib.use('WXAgg')
	f = pylab.figure()

	### title of windows is label
	fig = pylab.gcf()
	fig.canvas.set_window_title("%s - Abstract simulator three"%dia.label)

	### title of canvas is given by the user
	#pylab.title(devs.title)

	###-------------------------------

	# graph to plot
	graph = getSimulatorTree(dia.getDEVSModel(), nx.DiGraph(), dia.label)

	### remove the node corresponding to the master diagram (the first one on the top)
	graph.remove_node(dia.label)

	### list of edges and color
	edges,edge_colors = zip(*nx.get_edge_attributes(graph,'color').items())


	### list of nodes
	nodes = []
	for c1,c2 in edges:
		if c1 not in nodes and dia.label != c1:
			nodes.append(c1)
		if c2 not in nodes and dia.label != c2:
			nodes.append(c2)


	node_colors=[]
	### list of node colors
	for block in map(dia.GetShapeByLabel, map(lambda a: a.split('(')[0], nodes)):
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

	try:
		pos=nx.graphviz_layout(graph, prog='dot')
	except ValueError:
		pos=nx.spring_layout(graph)

	### draw the graph
	nx.draw(graph, pos, edgelist=edges, nodelist=nodes, edge_color=edge_colors, node_color=node_colors, node_size = node_sizes, width=2)

	### draw the weights
	edge_labels=dict([((u,v,),d['weight']) for u,v,d in graph.edges(data=True)])
	nx.draw_networkx_edge_labels(graph,pos,edge_labels=edge_labels)

	### Update function binded with the EVT_IDLE event
	def update(idleevent):
		""" Update the figure
		"""

		### simulate the weight evolution
		edge_labels=dict([((u,v,),round(random.uniform(1, 10),3)) for u,v,d in graph.edges(data=True)])
		nx.draw_networkx_edge_labels(graph,pos,edge_labels=edge_labels)

		###---------------------------
		try:
			fig.canvas.draw_idle()                 # redraw the canvas
		except:
			pass
		###----------------------------

	###----------------------------------------
	wx.EVT_IDLE(wx.GetApp(), update)
	f.autofmt_xdate()
	f.show()
	###----------------------------------------

def Config(parent):
	""" Plugin settings frame.
	"""
	dlg = wx.MessageDialog(parent, _('No settings available for this plugin\n'), _('Diagram plugin configuration'), wx.OK | wx.ICON_EXCLAMATION)
	dlg.ShowModal()