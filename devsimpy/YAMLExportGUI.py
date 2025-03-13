# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# YAMLExportGUI.py ---
#                     --------------------------------
#                        Copyright (c) 2016
#                       Laurent CAPOCCHI (capocchi@univ-corse.fr)
#                      University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 09/13/16
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
import os
import builtins

_ = wx.GetTranslation

from Utilities import load_and_resize_image

def url_ok(url):
    """_summary_

    Args:
        url (_type_): _description_

    Returns:
        _type_: _description_
    """
    import requests
    try:
        r = requests.head(url)
    except Exception as info:
        return False
    else:
        return r.status_code == 200
class MyStatusBar(wx.StatusBar):

    def __init__(self, parent):
        wx.StatusBar.__init__(self, parent)

        self.SetFieldsCount(2)
        self.SetStatusText(_('Insert url to upload'), 0)
        self.SetStatusWidths([-1, 50])

        self.icon = wx.StaticBitmap(self, -1, load_and_resize_image("disconnect_network.png"))
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.PlaceIcon()

    def PlaceIcon(self):

        rect = self.GetFieldRect(1)
        self.icon.SetPosition((rect.x+5, rect.y+1))

    def OnSize(self, e):

        e.Skip()
        self.PlaceIcon()

class YAMLExportGUI(wx.Frame):

    def __init__(self, parent, id, title, path=""):
        wx.Frame.__init__(self, parent, id, title, size=(290, 270))

        self.path = path

        self.InitUI()

    def InitUI(self):

        panel  = wx.Panel(self)

        wx.StaticText(panel, -1,  label='url', pos=(10, 20))
        wx.StaticText(panel, -1, label='port', pos=(10, 60))
        wx.StaticText(panel, -1, label='filename', pos=(10, 100))

        self.url = wx.TextCtrl(panel, value="http://" if not 'URL_REST' in builtins.__dict__ else URL_REST, pos=(110, 15), size=(160, -1))
        self.port = wx.TextCtrl(panel, value="8080", pos=(110, 55), size=(50, -1))
        self.fn = wx.TextCtrl(panel, value=os.path.basename(self.path), pos=(110, 95), size=(120, -1))

        self.rest = None

        upload = wx.Button(panel, label='Upload', pos=(175, 160), size=(80, -1))
        close = wx.Button(panel, label='Close', pos=(15, 160), size=(80, -1))
        test = wx.Button(panel, label='Test', pos=(100, 160), size=(70, -1))

        self.Bind(wx.EVT_BUTTON, self.OnUpload, upload)
        self.Bind(wx.EVT_BUTTON, self.OnClose, close)
        self.Bind(wx.EVT_BUTTON, self.OnTest, test)

        self.Bind(wx.EVT_MAXIMIZE, self.OnMaximize)
        self.Bind(wx.EVT_SHOW, self.OnShown)

        self.sb = MyStatusBar(self)
        self.SetStatusBar(self.sb)

        self.Centre()

    def OnShown(self, e):

        if self.sb:
            self.sb.PlaceIcon()

    def OnMaximize(self, e):

        self.sb.PlaceIcon()

    def OnTest(self, e):

        self.sb.SetStatusText('Test Rest server')
        self.sb.icon.SetBitmap(load_and_resize_image("connect_network.png"))

        if url_ok(self.url.GetValue()+':'+self.port.GetValue()):
            self.sb.SetStatusText('Rest server is ok!')
            self.sb.icon.SetBitmap(load_and_resize_image("disconnect_network.png"))
        else:
            self.sb.SetStatusText('Rest server is down!')
            self.sb.icon.SetBitmap(load_and_resize_image("disconnect_network.png"))

    def OnUpload(self, e):

        if not self.rest:

            url = self.url.GetValue()
            port = self.port.GetValue()

            self.sb.SetStatusText('Test Rest server')
            self.sb.icon.SetBitmap(load_and_resize_image("connect_network.png"))

            try:
                import requests
                self.rest = requests.post(str(url)+':'+str(port)+'/upload', files={'file': open(str(self.path), 'rb')})

            except Exception as err:
                self.sb.icon.SetBitmap(load_and_resize_image("exclamation.png"))
                self.sb.SetStatusText(str(err))
                self.rest = None
            else:
                self.sb.SetStatusText('Upload finished')
                self.sb.icon.SetBitmap(load_and_resize_image("disconnect_network.png"))
                setattr(builtins, 'URL_REST', url)

    def OnClose(self, e):
        self.Close()