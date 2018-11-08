#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wx
import wx.stc

if wx.VERSION_STRING >= '4.0':
    
	import wx.adv
	
	wx.FutureCall = wx.CallLater
	wx.SAVE = wx.FD_SAVE
	wx.OPEN = wx.FD_OPEN
	wx.DEFAULT_STYLE = wx.FD_DEFAULT_STYLE
	wx.MULTIPLE = wx.FD_MULTIPLE
	wx.CHANGE_DIR = wx.FD_CHANGE_DIR
	wx.OVERWRITE_PROMPT = wx.FD_OVERWRITE_PROMPT

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

        self.flag = 0

        # Menu Bar
        self.frame_1_menubar = wx.MenuBar()
        self.SetMenuBar(self.frame_1_menubar)
        self.File = wx.Menu()        
        self.Save = wx.MenuItem(self.File, wx.NewId(), "Save &As", "", wx.ITEM_NORMAL)
        self.File.Append(self.Save)
        self.open = wx.MenuItem(self.File, wx.NewId(), "&Open", "", wx.ITEM_NORMAL)
        self.File.Append(self.open)
        self.frame_1_menubar.Append(self.File, "&File")
        # Menu Bar end

        self.frame_1_statusbar = self.CreateStatusBar(1, 0)

        sizer = wx.BoxSizer(wx.VERTICAL)        

        self.editor = SimpleEditor(self)
        sizer.Add(self.editor, 1, flag=wx.EXPAND)


        self.Bind(wx.EVT_MENU, self.file_save, self.Save)
        self.Bind(wx.EVT_MENU, self.open_file, self.open)

        self.SetSizer(sizer)
        self.Layout()

    def file_save(self, event): # wxGlade: MyFrame.<event_handler>
        
        dialog = wx.FileDialog ( None, style = wx.SAVE )
        # Show the dialog and get user input
        if dialog.ShowModal() == wx.ID_OK:
            file_path = dialog.GetPath()
            file = open(file_path,'w')
            file_content = self.editor.GetValue()
            file.write(file_content)
        
        # Destroy the dialog            
        dialog.Destroy()
        
    def open_file(self, event): # wxGlade: MyFrame.<event_handler>
        
        filters = 'Text files (*.txt)|*.txt'
        dialog = wx.FileDialog ( None, message = 'Open something....', wildcard = filters, style = wx.OPEN|wx.MULTIPLE )
        if dialog.ShowModal() == wx.ID_OK:
            filename = dialog.GetPath()
            file = open(filename,'r')
            file_content = file.read()
            self.editor.SetValue(file_content)
        dialog.Destroy()

    def AddText(self,txt):
        self.editor.AddText(txt)

if __name__ == "__main__":
    app = wx.App(0)
    wx.InitAllImageHandlers()
    frame_1 = FrameEditor(None, -1, "Test")
    frame_1.AddText("Test \n zzeze")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
