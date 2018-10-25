#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wx
import wx.stc


class SimpleEditor (wx.stc.StyledTextCtrl):
    def __init__ (self, parent, id = wx.ID_ANY, \
            pos = wx.DefaultPosition, \
            size = wx.DefaultSize,\
            style = 0,\
            name = "editor"):
        wx.stc.StyledTextCtrl.__init__ (self, parent, id, pos, size, style, name)


class FrameEditor(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        sizer = wx.BoxSizer(wx.VERTICAL)        

        self.editor = SimpleEditor(self)
        sizer.Add (self.editor, 1, flag=wx.EXPAND)

        self.SetSizer(sizer)
        self.Layout()

    def AddText(self,txt):
        self.editor.AddText(txt)

if __name__ == "__main__":
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frame_1 = FrameEditor(None, -1, "Test")
    frame_1.AddText("Test \n zzeze")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
