#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wx
import wx.stc

from Utilities import load_and_resize_image
    
import wx.adv

wx.FutureCall = wx.CallLater
wx.SAVE = wx.FD_SAVE
wx.OPEN = wx.FD_OPEN
wx.DEFAULT_STYLE = wx.FD_DEFAULT_STYLE
wx.MULTIPLE = wx.FD_MULTIPLE
wx.CHANGE_DIR = wx.FD_CHANGE_DIR
wx.OVERWRITE_PROMPT = wx.FD_OVERWRITE_PROMPT

class SimpleEditor(wx.stc.StyledTextCtrl):
    def __init__ (self, parent, id = wx.NewIdRef(), \
            pos = wx.DefaultPosition, \
            size = wx.DefaultSize,\
            style = 0,\
            name = "editor"):
        wx.stc.StyledTextCtrl.__init__ (self, parent, id, pos, size, style, name)


class FrameEditor(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        self.title = args[2]
        self.flag = 0

        # Menu Bar
        self.frame_1_menubar = wx.MenuBar()
        self.SetMenuBar(self.frame_1_menubar)
        self.File = wx.Menu()        
        self.Save = wx.MenuItem(self.File, wx.NewIdRef(), "Save &As", "", wx.ITEM_NORMAL)
        self.Save.SetBitmap(load_and_resize_image('save_as.png'))
        self.File.Append(self.Save)
        self.Open = wx.MenuItem(self.File, wx.NewIdRef(), "&Open", "", wx.ITEM_NORMAL)
        self.Open.SetBitmap(load_and_resize_image('open.png'))
        self.File.Append(self.Open)
        self.frame_1_menubar.Append(self.File, "&File")
        # Menu Bar end

        self.frame_1_statusbar = self.CreateStatusBar(1, 0)

        sizer = wx.BoxSizer(wx.VERTICAL)        

        self.editor = SimpleEditor(self)
        sizer.Add(self.editor, 1, flag=wx.EXPAND)

        self.Bind(wx.EVT_MENU, self.file_save, self.Save)
        self.Bind(wx.EVT_MENU, self.open_file, self.Open)

        self.SetSizer(sizer)
        self.Layout()

    def file_save(self, event): # wxGlade: MyFrame.<event_handler>
        
        label = self.title.split(' ')[0]
        if label in ('Rapport','logger'):
            label = self.title.split(' ')[1]

        dialog = wx.FileDialog( None, "Save %s file"%label, style = wx.SAVE, defaultFile="%s.dat"%label )
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
            wx.CallAfter(self.editor.SetValue,file_content)
        dialog.Destroy()

    def AddText(self,txt):
        self.editor.AddText(txt)
