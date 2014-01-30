# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# Printable.py ---
#                     --------------------------------
#                          Copyright (c) 2014
#                           Laurent CAPOCCHI
#                         University of Corsica
#                     --------------------------------
# Version 3.0                                        last modified: 04/03/2013
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
import copy
import sys
import wx

import GUI.PrintOut as Printout


#-------------------------------------------------
class Printable:
	"""
	Mixin for printable windows.
	"""

	def __init__(self, print_canvas=None, print_size=(1100, 850)):

		self.print_canvas = print_canvas
		self.print_size = print_size

		# setup printing:
		self.printData = wx.PrintData()
		self.printData.SetPaperId(wx.PAPER_A4)
		self.printData.SetPrintMode(wx.PRINT_MODE_PRINTER)


	def PrintButton(self, event):

		parent = self.print_canvas.GetTopLevelParent()

		pdd = wx.PrintDialogData(self.printData)
		pdd.SetToPage(1)
		printer = wx.Printer(pdd)


		### copy in order to not change the size of original canvas when we rescal with zoom
		c = copy.copy(self.print_canvas)

		### scale with A4 paper dim
		c.scalex = min(float(c.getWidth()) / 1654.0, float(c.getHeight()) / 2339.0)
		c.scaley = min(float(c.getWidth()) / 1654.0, float(c.getHeight()) / 2339.0)

		printout = Printout.Printout(c)

		if printer.Print(parent, printout, True):
			self.printData = wx.PrintData(printer.GetPrintDialogData().GetPrintData())
		printout.Destroy()


	def PrintPreview(self, event):

		parent = self.print_canvas.GetTopLevelParent()

		### copy in order to not change the size of original canvas when we rescal with zoom
		c = copy.copy(self.print_canvas)

		data = wx.PrintDialogData(self.printData)

		### scale with A4 paper dim
		c.scalex = min(float(c.getWidth()) / 1654.0, float(c.getHeight()) / 2339.0)
		c.scaley = min(float(c.getWidth()) / 1654.0, float(c.getHeight()) / 2339.0)

		printout = Printout.Printout(c)
		printout2 = Printout.Printout(c)

		self.preview = wx.PrintPreview(printout, printout2, data)

		if self.preview.Ok():
			pfrm = wx.PreviewFrame(self.preview, parent, _("Print preview"), style=wx.DEFAULT_FRAME_STYLE | wx.CLIP_CHILDREN | wx.STAY_ON_TOP)
			pfrm.SetIcon(parent.GetIcon())
			pfrm.Initialize()
			pfrm.SetPosition((300, 200))
			pfrm.SetSize((550, 700))
			pfrm.Show(True)

		else:
			sys.stderr.write(_("Problem on print preview...\n"))

	def PageSetup(self, evt):
		psdd = wx.PageSetupDialogData(self.printData)
		psdd.CalculatePaperSizeFromId()
		dlg = wx.PageSetupDialog(self, psdd)
		dlg.ShowModal()

		# this makes a copy of the wx.PrintData instead of just saving
		# a reference to the one inside the PrintDialogData that will
		# be destroyed when the dialog is destroyed
		self.printData = wx.PrintData(dlg.GetPageSetupData().GetPrintData())
		dlg.Destroy()

def main():
    pass

if __name__ == '__main__':
    main()
