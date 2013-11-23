# -*- coding: utf-8 -*-
import wx
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

def OnLeftDClick(self, event):
	""" Left Double Click has been invocked.
		This plugin call pdist function from hcluster package and
		plot the dendrogram using matplotlib.pyplot package.
	"""
	#canvas = event.GetEventObject()
	#model = canvas.getCurrentShape(event)
	
	devs = self.getDEVSModel()
	
	if devs:
		
		x = np.arange(0, devs.row+1)
		y = np.arange(0, devs.col+1)
		X,Y = np.meshgrid(x,y)
		ims = [(plt.pcolor(X, Y, devs.matrix),)]
	
		for i in xrange(len(devs.ims)):
			ims.append((plt.pcolor(X, Y, devs.ims[i]),))
			
		fig = plt.figure(1)
		im_ani = animation.ArtistAnimation(fig, ims, interval=50,\
			repeat_delay=3000,\
			blit=True)

		im_ani.save('im.mp4')
		plt.axis([0, devs.col, devs.col, 0])
		plt.axis('off')
		plt.show()
    
	else:
		wx.MessageBox(_("No DEVS model is instanciated.\nGo back to the simulation!"), _("Info"), wx.OK|wx.ICON_INFORMATION)