# -*- coding: utf-8 -*-

import wx
import wx.html

_ = wx.GetTranslation

class HtmlFrame(wx.Frame):
    """ General Frame displaying Html doc
    """

    ###
    def __init__(self, parent, id, title, size):
        wx.Frame.__init__(self, parent, id, title, size, style = wx.DEFAULT_FRAME_STYLE | wx.CLIP_CHILDREN )

        file = wx.Menu()
        file.Append(wx.ID_FILE, _('&File\tCtrl+F'), _('Open Html local file'))

        menubar = wx.MenuBar()
        menubar.Append(file, _('&File'))
        self.SetMenuBar(menubar)

        self.html = wx.html.HtmlWindow(self, wx.NewIdRef())
        if "gtk2" in wx.PlatformInfo:
            self.html.SetStandardFonts()

        self.Bind(wx.EVT_MENU, self.OnLoadFile, id=wx.ID_FILE)

    ###
    def LoadFile(self, path):
        """ Load Html File from local path
        """
        self.html.LoadFile(path)

    ###
    def SetPage(self, s):
        """ Set Html page from string
        """
        self.html.SetPage(s)

    ###
    def OnLoadFile(self, event):
        """ Load Html file from dialog
        """
        dlg = wx.FileDialog(self, wildcard = '*.htm*', style=wx.OPEN)
        if dlg.ShowModal():
            path = dlg.GetPath()
            self.html.LoadPage(path)
        dlg.Destroy()

    ###
    def OnClearPage(self, event):
        """ Clear page
        """
        self.html.SetPage("")

