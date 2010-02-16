# -*- coding: utf-8 -*-
import wxversion

wxversion.select('2.8')

import wx
import os
import sys

HOME_PATH = os.path.abspath(os.path.dirname(sys.argv[0]))
ICON_PATH = HOME_PATH+os.sep+'icons2'

#---------------------------------------------------------------------- 
def getNextImageID(count):
	imID = 0
	while True:
		yield imID
		imID += 1
		if imID == count:
			imID = 0

class GeneralPanel(wx.Panel):
	""" generale Panel
	"""

	def __init__(self, parent):
		wx.Panel.__init__(self, parent)

class SimulationPanel(wx.Panel):
	""" generale Panel
	"""

	def __init__(self, parent):
		wx.Panel.__init__(self, parent)

########################################################################
class Preferences(wx.Toolbook):
	""" Toolbook class
	"""

	#----------------------------------------------------------------------
	def __init__(self, parent):
		"""Constructor"""
		wx.Toolbook.__init__(self, parent, wx.ID_ANY, style=
								wx.BK_DEFAULT
								#wx.BK_TOP
								#wx.BK_BOTTOM
								#wx.BK_LEFT
								#wx.BK_RIGHT
							)

		# make an image list using the LBXX images
		il = wx.ImageList(32, 32)
		for img in [os.path.join(ICON_PATH,'General_pref.png'), os.path.join(ICON_PATH,'Simulation_pref.png')]:
			bmp = wx.Image(img, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
			il.Add(bmp)
		self.AssignImageList(il)
		imageIdGenerator = getNextImageID(il.GetImageCount())

		pages = [(GeneralPanel(self), "General"),
					(SimulationPanel(self), "Simulation")]
		imID = 0
		for page, label in pages:
			self.AddPage(page, label, imageId=imageIdGenerator.next())
			imID += 1

		self.Bind(wx.EVT_TOOLBOOK_PAGE_CHANGED, self.OnPageChanged)
		self.Bind(wx.EVT_TOOLBOOK_PAGE_CHANGING, self.OnPageChanging)

	#----------------------------------------------------------------------
	def OnPageChanged(self, event):
		old = event.GetOldSelection()
		new = event.GetSelection()
		sel = self.GetSelection()
		print 'OnPageChanged,  old:%d, new:%d, sel:%d\n' % (old, new, sel)
		event.Skip()

	#----------------------------------------------------------------------
	def OnPageChanging(self, event):
		old = event.GetOldSelection()
		new = event.GetSelection()
		sel = self.GetSelection()
		print 'OnPageChanging, old:%d, new:%d, sel:%d\n' % (old, new, sel)
		event.Skip()

########################################################################
class DemoFrame(wx.Frame):
	"""
	Frame that holds all other widgets
	"""

	#----------------------------------------------------------------------
	def __init__(self):
		"""Constructor"""
		wx.Frame.__init__(self, None, wx.ID_ANY,
							"Preferences",
							size=(700,400)
							)
		panel = wx.Panel(self)

		pref = Preferences(panel)
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(pref, 1, wx.ALL|wx.EXPAND, 5)
		panel.SetSizer(sizer)
		self.Layout()

		self.Show()

#----------------------------------------------------------------------
if __name__ == "__main__":

	app = wx.PySimpleApp()
	frame = DemoFrame()
	app.MainLoop()
