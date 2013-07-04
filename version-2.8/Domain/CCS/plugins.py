# -*- coding: utf-8 -*-

import wx

from matplotlib.pyplot import show
from hcluster import pdist, linkage, dendrogram

def OnLeftDClick(self, event):
#def OnLeftDClick(event):
	""" Left Double Click has been invocked.
		This plugin call pdist function from hcluster package and
		plot the dendrogram using matplotlib.pyplot package.
	"""
	#canvas = event.GetEventObject()
	#model = canvas.getCurrentShape(event)
	devs = self.getDEVSModel()
	if devs:
		Y = pdist(devs.vectors)
		Z = linkage(Y)
		dendrogram(Z)
		show()
	else:
		wx.MessageBox(_("No DEVS model is instanciated.\nGo back to the simulation!"), _("Info"), wx.OK|wx.ICON_INFORMATION)