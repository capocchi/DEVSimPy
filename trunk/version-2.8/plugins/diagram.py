# -*- coding: utf-8 -*-

"""
	Authors: L. Capocchi (capocchi@univ-corse.fr)
	Date: 16/10/2012
	Description:
		Give diagram representation of the DEVS model
	Depends: python-networkx, python-profiler(for gato) (for windows user: matplotlib (http://sourceforge.net/projects/matplotlib/files/)and networkx )
"""

import sys
import os
import wx
import webbrowser

#for ploting
try:
	import pylab
except ImportError, info:
	platform_sys = os.name
	if platform_sys in ('nt', 'mac'):
		msg = _("ERROR: Matplotlib module not found.\nhttp://sourceforge.net/projects/matplotlib/files/\n")
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
		msg = _("ERROR: Networkx module not found.\nhttp://networkx.lanl.gov/download/networkx/\n")
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

from Container import CodeBlock, ContainerBlock, ConnectionShape, Diagram

def getSimulatorTree(dia, graph, par):
	if isinstance(dia, CodeBlock):
		graph.add_edge(par,  "%s(%s)"%(dia.label,str(dia.getDEVSModel().myID)))
	elif isinstance(dia, (ContainerBlock,Diagram)):
		graph.add_edge(par,  "%s(%s)"%(dia.label,str(dia.getDEVSModel().myID)))
		for c in filter(lambda component: not isinstance(component, ConnectionShape), dia.GetShapeList()):
			getSimulatorTree(c, graph, "%s(%s)"%(dia.label,str(dia.getDEVSModel().myID)))
	return graph

@pluginmanager.register("START_DIAGRAM")
def start_diagram(*args, **kwargs):
	""" Start the diagram frame.
	"""

	dia = kwargs['diagram']

	#global G
	G = getSimulatorTree(dia, nx.Graph(), dia.label)

	### plot the grahp
	nx.draw(G)
	pylab.show()

def Config(parent):
	""" Plugin settings frame.
	"""
	dlg = wx.MessageDialog(parent, _('No settings available for this plugin\n'), _('Diagram plugin configuration'), wx.OK | wx.ICON_EXCLAMATION)
	dlg.ShowModal()