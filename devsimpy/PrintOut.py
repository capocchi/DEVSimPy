# -*- coding: utf-8 -*-
################################################################################
# file: printout.py
################################################################################

import wx
import sys

_ = wx.GetTranslation

class Printout(wx.Printout):

    def __init__(self, canvas, title = "", size=(800, 800)):

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
        return (1, 2, 1, 2)

    def OnPrintPage(self, page):
	
        dc = self.GetDC()

        #-------------------------------------------
        # One possible method of setting scaling factors...
        maxX, maxY = self.print_canvas.GetSize()
		
        ## Let's have at least 50 device units margin
        marginX = 50
        marginY = 50

        ## Add the margin to the graphic size
        maxX += 2*marginX
        maxY += 2*marginY

        ## Get the size of the DC in pixels
        (w, h) = dc.GetSize()
		
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
        c = self.print_canvas
				
        printout = Printout(c)

        if printer.Print(parent, printout, True):
            self.printData = wx.PrintData(printer.GetPrintDialogData().GetPrintData())
            printout.Destroy()
            return True
        else:
            printout.Destroy()
            return False

    def PrintPreview(self, event):

        parent = self.print_canvas.GetTopLevelParent()
		
        ### copy in order to not change the size of original canvas when we rescal with zoom
        c = self.print_canvas
		
        data = wx.PrintDialogData(self.printData)
	
        printout = Printout(c)
        printout2 = Printout(c)

        self.preview = wx.PrintPreview(printout, printout2, data)
        self.preview.SetZoom(100)

        if self.preview.IsOk():
            pfrm = wx.PreviewFrame(self.preview, parent, _("Print Preview"), style = wx.DEFAULT_FRAME_STYLE | wx.CLIP_CHILDREN )
            pfrm.SetIcon(parent.GetIcon())
            pfrm.Initialize()
            pfrm.SetPosition((300, 200))
            pfrm.SetSize((550, 700))
            pfrm.Show(True)
            return True
            
        else:
            sys.stderr.write(_("Problem on print preview...\n"))
            return False

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
