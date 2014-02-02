# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# PrintOut.py ---
#                     --------------------------------
#                          Copyright (c) 2013
#                           Laurent CAPOCCHI
#                         University of Corsica
#                     --------------------------------
# Version 3.1                                        last modified: 11/12/2012
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


import wx


class Printout(wx.Printout):
	def __init__(self, canvas, title="", size=(800, 800)):

		wx.Printout.__init__(self, title)

		self.print_canvas = canvas
		self.print_size = size

	def OnBeginDocument(self, start, end):
		return super(Printout, self).OnBeginDocument(start, end)

	def OnEndDocument(self):
		super(Printout, self).OnEndDocument()

	def OnBeginPrinting(self):
		super(Printout, self).OnBeginPrinting()

	def OnEndPrinting(self):
		super(Printout, self).OnEndPrinting()

	def OnPreparePrinting(self):
		super(Printout, self).OnPreparePrinting()

	def HasPage(self, page):
		if page <= 2:
			return True
		else:
			return False

	def GetPageInfo(self):
		""" Number of page for the print
		"""
		return 1, 2, 1, 2

	def OnPrintPage(self, page):

		dc = self.GetDC()

		#-------------------------------------------
		# One possible method of setting scaling factors...
		maxX, maxY = self.print_canvas.GetSize()

		## Let's have at least 50 device units margin
		marginX = 50
		marginY = 50

		## Add the margin to the graphic size
		maxX += 2 * marginX
		maxY += 2 * marginY

		## Get the size of the DC in pixels
		(w, h) = dc.GetSizeTuple()

		## Calculate a suitable scaling factor

		scaleX = float(w) / maxX
		scaleY = float(h) / maxY

		## Use x or y scaling factor, whichever fits on the DC
		self.actualScale = min(scaleX, scaleY)

		## Calculate the position on the DC for centering the graphic
		#posX = (w - (self.print_canvas.getWidth() * self.actualScale)) / 2.0
		#posY = (h - (self.print_canvas.getHeight() * self.actualScale)) / 2.0
		posX = (w - (maxX * self.actualScale)) / 2.0
		posY = (h - (maxY * self.actualScale)) / 2.0

		# Set the scale and origin
		dc.SetUserScale(self.actualScale, self.actualScale)
		dc.SetDeviceOrigin(int(posX), int(posY))

		#-------------------------------------------
		self.print_canvas.DoDrawing(dc)

		#dc.DrawText("Page: %d" % page, marginX, marginY)

		return True
