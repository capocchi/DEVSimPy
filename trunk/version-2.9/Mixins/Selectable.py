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

import wx
import gettext

_ = gettext.gettext

import LabelGUI
import AttributeEditor

from Mixins.Attributable import Attributable

class Selectable:
    """ Allows Shape to be selected.
    """

    def __init__(self):
        """ Constructor
        """
        self.selected = False

    def ShowAttributes(self, event):
        """
        """

        canvas = event.GetEventObject()
        diagram = canvas.GetDiagram()

        ### only for Block and Port when control is down
        if isinstance(self, Attributable) and event.ControlDown():

            ### store old label before change it
            old_label = self.label

            ### ask new label
            d = LabelGUI.LabelDialog(canvas, self)
            d.ShowModal()

            ### update priority list if label is different and update panel properties only if is active
            if old_label in diagram.priority_list and old_label != self.label:
                ### find index of label priority list and replace it
                i = diagram.priority_list.index(old_label)
                diagram.priority_list[i] = self.label

                ### update of panel properties
                mainW = wx.GetApp().GetTopWindow()
                nb1 = mainW.GetControlNotebook()
                if nb1.GetSelection() == 1:
                    newContent = AttributeEditor(nb1.propPanel, wx.ID_ANY, self, canvas)
                    nb1.UpdatePropertiesPage(newContent)

                ### update of code editor panel
                #print mainW._mgr.GetPane("editor").IsOk()

        event.Skip()
