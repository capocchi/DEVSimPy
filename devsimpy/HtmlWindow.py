# -*- coding: utf-8 -*-

import wx
import wx.html2

_ = wx.GetTranslation

class HtmlFrame(wx.Frame):
    """ General Frame displaying Html doc """

    def __init__(self, parent=None, title="HTML", size=(800, 600)):
        super().__init__(
            parent,
            title=title,
            size=size,
            style=wx.DEFAULT_FRAME_STYLE | wx.CLIP_CHILDREN
        )

        file_menu = wx.Menu()
        file_menu.Append(wx.ID_OPEN, _('&Open\tCtrl+O'), _('Open Html local file'))

        menubar = wx.MenuBar()
        menubar.Append(file_menu, _('&File'))
        self.SetMenuBar(menubar)

        self.html = wx.html2.WebView.New(self)
        if "gtk2" in wx.PlatformInfo:
            self.html.SetStandardFonts()

        self.Bind(wx.EVT_MENU, self.OnLoadFile, id=wx.ID_OPEN)

    def LoadFile(self, path):
        self.html.LoadFile(path)

    def SetPage(self, s):
        self.html.SetPage(s, "")

    def OnLoadFile(self, event):
        dlg = wx.FileDialog(self, wildcard='*.htm*', style=wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.html.LoadPage(dlg.GetPath())
        dlg.Destroy()

    def OnClearPage(self, event):
        self.html.SetPage("")
