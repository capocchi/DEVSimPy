# -*- coding: utf-8 -*-

import os

import wx
import wx.html

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

def main():
    app = wx.App()
    # create a window/frame, no parent, -1 is default ID, title, size
    frame = HtmlFrame(None, -1, "Alone Mode", size=(800,600))
    # show the frame
    frame.Show()
    # start the event loop
    app.MainLoop()

if __name__ == '__main__':
    import builtins
    import gettext

    builtins.__dict__['HOME_PATH'] = os.getcwd()
    builtins.__dict__['_'] = gettext.gettext

    main()