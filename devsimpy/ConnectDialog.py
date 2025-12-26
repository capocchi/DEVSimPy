# -*- coding: utf-8 -*-
'''
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# ConnectDialog.py ---
#                     --------------------------------
#                        Copyright (c) 2020
#                       Laurent CAPOCCHI
#                      University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 03/15/2020
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
'''

import wx

_ = wx.GetTranslation
from Utilities import load_and_resize_image

def function(obj, i):
    return 'iPort %d' % i if obj[i].__class__.__name__ == "INode" else 'oPort %d' % i

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# CLASSES DEFINITION
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

class ConnectDialog(wx.Dialog):
    def __init__(self, parent, id, title, sn="Source", snL=[None, None], tn="Target", tnL=[None, None]):
        super().__init__(parent, id, title, style=wx.DEFAULT_DIALOG_STYLE)
        
        # local copy
        self.sn = sn
        self.tn = tn
        self.parent = parent
        self._result = [0, 0]
        
        # Construire les listes de ports
        L1 = [function(snL, i) for i in range(len(snL))]
        L2 = [function(tnL, i) for i in range(len(tnL))]
        L1.insert(0, "%s" % _('All'))
        L2.insert(0, "%s" % _('All'))
        
        self._source_list = L1
        self._target_list = L2
        
        self.__init_ui()
        self.__set_properties()
        self.__set_events()
        
        self.Center()
    
    def __init_ui(self):
        """Initialize the user interface"""
        
        # Taille minimale confortable
        self.SetMinSize((400, 220))
        
        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
        
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # --- Section Ports ---
        ports_box = wx.StaticBoxSizer(wx.VERTICAL, panel, _("Port Connection"))
        
        ports_grid = wx.FlexGridSizer(rows=2, cols=2, vgap=10, hgap=15)
        ports_grid.AddGrowableCol(0, 1)
        ports_grid.AddGrowableCol(1, 1)
        
        # Source
        source_label = wx.StaticText(panel, wx.NewIdRef(), _('Source: %s') % self.sn)
        font = source_label.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        source_label.SetFont(font)
        ports_grid.Add(source_label, flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        
        # Target
        target_label = wx.StaticText(panel, wx.NewIdRef(), _('Target: %s') % self.tn)
        target_label.SetFont(font)
        ports_grid.Add(target_label, flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        
        # ComboBox Source
        self._combo_box_sn = wx.ComboBox(
            panel, 
            wx.NewIdRef(), 
            choices=self._source_list, 
            style=wx.CB_DROPDOWN | wx.CB_READONLY
        )
        self._combo_box_sn.SetSelection(0)
        self._combo_box_sn.Enable(len(self._source_list) != 2)
        self._combo_box_sn.SetToolTip(_("Select source port to connect"))
        ports_grid.Add(self._combo_box_sn, flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        
        # ComboBox Target
        self._combo_box_tn = wx.ComboBox(
            panel, 
            wx.NewIdRef(), 
            choices=self._target_list, 
            style=wx.CB_DROPDOWN | wx.CB_READONLY
        )
        self._combo_box_tn.SetSelection(0)
        self._combo_box_tn.Enable(len(self._target_list) != 2)
        self._combo_box_tn.SetToolTip(_("Select target port to connect"))
        ports_grid.Add(self._combo_box_tn, flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        
        ports_box.Add(ports_grid, flag=wx.ALL|wx.EXPAND, border=10)
        main_sizer.Add(ports_box, flag=wx.ALL|wx.EXPAND, border=15)
        
        # --- Info Text ---
        if not self._combo_box_sn.IsEnabled() and not self._combo_box_tn.IsEnabled():
            info_text = wx.StaticText(panel, label=_("Only one port available on each side"))
        elif not self._combo_box_sn.IsEnabled():
            info_text = wx.StaticText(panel, label=_("Only one source port available"))
        elif not self._combo_box_tn.IsEnabled():
            info_text = wx.StaticText(panel, label=_("Only one target port available"))
        else:
            info_text = wx.StaticText(panel, label=_("Select ports to connect or disconnect"))
        
        info_text.SetForegroundColour(wx.Colour(100, 100, 100))
        font_info = info_text.GetFont()
        font_info.SetPointSize(font_info.GetPointSize() - 1)
        info_text.SetFont(font_info)
        main_sizer.Add(info_text, flag=wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.ALIGN_CENTER, border=15)
        
        # --- Buttons ---
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self._button_disconnect = wx.Button(panel, wx.NewIdRef(), _("Disconnect"), size=(120, 32))
        self._button_disconnect.SetToolTip(_("Disconnect the selected ports"))
        button_sizer.Add(self._button_disconnect)
        
        self._button_connect = wx.Button(panel, wx.NewIdRef(), _("Connect"), size=(120, 32))
        self._button_connect.SetDefault()
        self._button_connect.SetToolTip(_("Connect the selected ports"))
        button_sizer.Add(self._button_connect, flag=wx.LEFT, border=5)
        
        main_sizer.Add(button_sizer, flag=wx.ALL|wx.ALIGN_RIGHT, border=15)
        
        panel.SetSizer(main_sizer)
        
        # Ajuster la taille
        main_sizer.SetSizeHints(self)
        panel.Layout()
        self.Fit()
        
    def __set_properties(self):
        """Set window properties"""
        icon = wx.Icon()
        icon.CopyFromBitmap(load_and_resize_image("direct_connector.png"))
        self.SetIcon(icon)
    
    def __set_events(self):
        """Bind events"""
        self.Bind(wx.EVT_COMBOBOX, self.EvtComboBox1, self._combo_box_sn)
        self.Bind(wx.EVT_COMBOBOX, self.EvtComboBox2, self._combo_box_tn)
        self.Bind(wx.EVT_BUTTON, self.OnConnect, self._button_connect)
        self.Bind(wx.EVT_BUTTON, self.OnDisconnect, self._button_disconnect)
    
    def EvtComboBox1(self, event):
        """Handle source combobox selection"""
        self._result[0] = event.GetSelection()
    
    def EvtComboBox2(self, event):
        """Handle target combobox selection"""
        self._result[1] = event.GetSelection()
    
    def OnConnect(self, event):
        """Handle Connect button click"""
        # Vous pouvez ajouter une logique de validation ici
        self.EndModal(wx.ID_OK)
    
    def OnDisconnect(self, event):
        """Handle Disconnect button click"""
        # Vous pouvez ajouter une logique de déconnexion ici
        self.EndModal(wx.ID_CANCEL)
    
    def GetSelectedIndex(self):
        """Return the selected indices"""
        return self._result
    
    def GetLabelSource(self):
        """Return the source label"""
        return self.sn
    
    def GetLabelTarget(self):
        """Return the target label"""
        return self.tn