# -*- coding: utf-8 -*-


import wx


import DragList
from Utilities import load_and_resize_image


_ = wx.GetTranslation


class PriorityGUI(wx.Frame):

    def __init__(self, parent, id, title, priorityList):
        wx.Frame.__init__(  self,
                            parent,
                            id,
                            title,
                            size = (350, 300),
                            style = wx.FRAME_NO_WINDOW_MENU|wx.DEFAULT_FRAME_STYLE|wx.CLOSE_BOX)

        icon = wx.Icon()
        icon.CopyFromBitmap(load_and_resize_image("priority.png"))
        self.SetIcon(icon)

        panel = wx.Panel(self, -1)

        self.listCtrl = DragList.DragList(panel, style = wx.LC_LIST)

        # append to list
        for item in priorityList:
            self.listCtrl.InsertItem(100000000, item)

        self.listCtrl.SetToolTip(_('Drag and drop a model in order to define its priority.'))

        ### if list not empty, first item is selected
        if self.listCtrl.GetItemCount():
            self.listCtrl.Select(0, 1)

        ### -------------------------------------------------------------------

        hbox = wx.BoxSizer(wx.HORIZONTAL)

        # Up button with icon
        up_btn = wx.Button(panel, wx.ID_UP, _("Up"))
        up_btn.SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_GO_UP, wx.ART_BUTTON))
        up_btn.SetToolTip(_("Move selected item up"))
        
        # Down button with icon
        down_btn = wx.Button(panel, wx.ID_DOWN, _("Down"))
        down_btn.SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_GO_DOWN, wx.ART_BUTTON))
        down_btn.SetToolTip(_("Move selected item down"))
        
        # Apply button with icon
        apply_btn = wx.Button(panel, wx.ID_APPLY, _("Apply"))
        apply_btn.SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_TICK_MARK, wx.ART_BUTTON))
        apply_btn.SetToolTip(_("Apply priority changes and close"))

        up_btn.Enable(self.listCtrl.GetItemCount() != 0)
        down_btn.Enable(self.listCtrl.GetItemCount() != 0)

        hbox.Add(up_btn, 1, wx.ALL, 2)
        hbox.Add(down_btn, 1, wx.ALL, 2)
        hbox.Add(apply_btn, 1, wx.ALL, 2)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.listCtrl, 1, wx.EXPAND | wx.ALL , 5)
        vbox.Add(hbox, 0, wx.EXPAND | wx.ALL, 5)

        panel.SetSizer(vbox)

        self.Bind(wx.EVT_BUTTON, self.OnApply, id=wx.ID_APPLY)
        self.Bind(wx.EVT_BUTTON, self.OnUp, id=wx.ID_UP)
        self.Bind(wx.EVT_BUTTON, self.OnDown, id=wx.ID_DOWN)

        self.Center()

    def OnApply(self, evt):
        self.Close()

    def GetSelectedItems(self):
        """    Gets the selected items for the list control.
        Selection is returned as a list of selected indices,
        low to high.
        """
        selection = []
        index = self.listCtrl.GetFirstSelected()
        if index != -1:
            selection.append(index)

        while len(selection) != self.listCtrl.GetSelectedItemCount():
            index = self.listCtrl.GetNextSelected(index)
            selection.append(index)

        return selection

    def OnUp(self, evt):
        """ Allow up moving for selected items.
        """

        for pos in self.GetSelectedItems():
            item = self.listCtrl.GetItem(pos)
            current_item = item

            new_pos = pos-1 if pos != 0 else self.listCtrl.GetItemCount()-1

            current_item.SetId(new_pos)
            self.listCtrl.DeleteItem(pos)
            self.listCtrl.InsertItem(item)
            self.listCtrl.SetItemState(new_pos, 1, wx.LIST_STATE_SELECTED)
            self.listCtrl.Select(new_pos,1)

    def OnDown(self, evt):
        """ Allow down moving for selected items.
        """

        for pos in self.GetSelectedItems():
            item = self.listCtrl.GetItem(pos)
            current_item = item

            new_pos = pos+1 if pos != self.listCtrl.GetItemCount()-1 else 0

            current_item.SetId(new_pos)
            self.listCtrl.DeleteItem(pos)
            self.listCtrl.InsertItem(item)
            self.listCtrl.SetItemState(new_pos, 1, wx.LIST_STATE_SELECTED)
            self.listCtrl.Select(new_pos, 1)
