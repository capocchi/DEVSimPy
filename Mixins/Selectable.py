# -*- coding: utf-8 -*-

"""
Name: Savable.py
Brief descritpion:
Author(s): L. Capocchi <capocchi@univ-corse.fr>, A-T. Luciani <atluciani@univ-corse.fr>
Version:  1.0
Last modified: 2012.04.04
GENERAL NOTES AND REMARKS:

GLOBAL VARIABLES AND FUNCTIONS:
"""

import gettext

_ = gettext.gettext

from Mixins.Attributable import Attributable

class Selectable:
    """ Allows Shape to be selected.
    """

    def __init__(self):
        """ Constructor.
        """
        self.selected = False

    def OnRenameFromClick(self, event):
        """ Rename the component from click.
        """

        canvas = event.GetEventObject()
        self.DoLabelDialog(canvas)
        event.Skip()

    def OnRenameFromMenu(self, event):
        """ Rename the component from menu.
        """

        canvas = event.GetEventObject().GetParent()
        self.DoLabelDialog(canvas)
        event.Skip()

    def DoLabelDialog(self, canvas):
        """ Dialog to ask new label.
        """

         ### only for Block and Port when control is down
        if isinstance(self, Attributable):

            ### here for no-gui mode
            import LabelGUI
            import AttributeEditor

            diagram = canvas.GetDiagram()

            ### store old label before change it
            old_label = self.label

            ### ask new label
            d = LabelGUI.LabelDialog(canvas, self)
            d.SetCanvas(canvas)
            d.ShowModal()

            ### update priority list if label is different and update panel properties only if is active
            if old_label in diagram.priority_list and old_label != self.label:
                ### find index of label priority list and replace it
                i = diagram.priority_list.index(old_label)
                diagram.priority_list[i] = self.label

                ### update of panel properties
                import wx
                mainW = wx.GetApp().GetTopWindow()
                nb1 = mainW.GetControlNotebook()
                if nb1.GetSelection() == 1:
                    newContent = AttributeEditor(nb1.propPanel, wx.NewIdRef(), self, canvas)
                    nb1.UpdatePropertiesPage(newContent)