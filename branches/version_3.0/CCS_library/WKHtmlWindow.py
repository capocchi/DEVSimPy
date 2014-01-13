# -*- coding: utf-8 -*-


import wxversion

wxversion.select("2.8")

import wx

import gobject
gobject.threads_init()

import pygtk
pygtk.require('2.0')
import gtk, gtk.gdk

# pywebkitgtk (http://code.google.com/p/pywebkitgtk/)
import webkit

'''
As far as I know (I may be wrong), a wx.Panel is "composed" by a GtkPizza
as a child of GtkScrolledWindow. GtkPizza is a custom widget created for
wxGTK.

WebKitGTK+ - the webkit port for GTK+ that has python bindings - wants a
GtkScrolledWindow as parent.

So all we need to embed webkit in wxGTK is find the wx.Panel's
GtkScrolledWindow.
This is acomplished using pygtk that is present in major distro's by
default, at least those that use gnome as its main desktop environment.

A last note is that for get a handle of a window in X, the window must be
"realized" first, in other words, must already exists. So we must Show
the wx.Frame before use this WKHtmlWindow class.

'''
class WKHtmlWindow(wx.Panel):
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)

        # Here is where we do the "magic" to embed webkit into wxGTK.
        whdl = self.GetHandle()
        window = gtk.gdk.window_lookup(whdl)

        # We must keep a reference of "pizza". Otherwise we get a crash.
        self.pizza = pizza = window.get_user_data()

        self.scrolled_window = scrolled_window = pizza.parent

        # Removing pizza to put a webview in it's place
        scrolled_window.remove(pizza)

        self.ctrl = ctrl = webkit.WebView()
        scrolled_window.add(ctrl)

        scrolled_window.show_all()

    # Some basic usefull methods
    def SetEditable(self, editable=True):
        self.ctrl.set_editable(editable)

    def LoadUrl(self, url):
        self.ctrl.load_uri(url)

    def HistoryBack(self):
        self.ctrl.go_back()

    def HistoryForward(self):
        self.ctrl.go_forward()

    def StopLoading(self):
        self.ctrl.stop_loading()


class TestWKPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        self.html = WKHtmlWindow(self)
        self.html.SetEditable(True)

        self.box = wx.BoxSizer(wx.VERTICAL)
        self.box.Add(self.html, 1, wx.EXPAND)

        subbox = wx.BoxSizer(wx.HORIZONTAL)

        btn = wx.Button(self, -1, "Load File")
        self.Bind(wx.EVT_BUTTON, self.OnLoadFile, btn)
        subbox.Add(btn, 1, wx.EXPAND | wx.ALL, 2)

        btn = wx.Button(self, -1, "Load URL")
        self.Bind(wx.EVT_BUTTON, self.OnLoadURL, btn)
        subbox.Add(btn, 1, wx.EXPAND | wx.ALL, 2)

        btn = wx.Button(self, -1, "Back")
        self.Bind(wx.EVT_BUTTON, self.OnBack, btn)
        subbox.Add(btn, 1, wx.EXPAND | wx.ALL, 2)

        btn = wx.Button(self, -1, "Forward")
        self.Bind(wx.EVT_BUTTON, self.OnForward, btn)
        subbox.Add(btn, 1, wx.EXPAND | wx.ALL, 2)

        self.box.Add(subbox, 0, wx.EXPAND)
        self.SetSizer(self.box)
        self.Layout()

    def OnLoadFile(self, event):
        dlg = wx.FileDialog(self, wildcard = '*.htm*', style=wx.OPEN)

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.html.LoadUrl("file://%s" % path)

        dlg.Destroy()

    def OnLoadURL(self, event):
        dlg = wx.TextEntryDialog(self, "Enter a URL", defaultValue="http://")

        if dlg.ShowModal() == wx.ID_OK:
            url = dlg.GetValue()
            if not url.startswith('http://'):
                url = "http://%s" % url
            self.html.LoadUrl(url)

        dlg.Destroy()

    def OnBack(self, event):
        self.html.HistoryBack()

    def OnForward(self, event):
        self.html.HistoryForward()


class Frame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None)
        self.Show()

        TestWKPanel(self)

        # This is need it for wxPython2.8,
        # for 2.6 doesnt hurt
        self.SendSizeEvent()


if __name__ == '__main__':
    app = wx.App()
    f = Frame()
    app.MainLoop()