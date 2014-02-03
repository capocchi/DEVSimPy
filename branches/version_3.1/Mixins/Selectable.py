# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# Selectable.py ---
#                     --------------------------------
#                          Copyright (c) 2014
#                           Laurent CAPOCCHI
#                        Andre-Toussaint Luciani
#                         University of Corsica
#                     --------------------------------
# Version 3.1                                        last modified: 22/01/2014
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
import GUI.LabelGUI as LabelGUI
import Core.Components.AttributeEditor as AttributeEditor

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
		import Core.Components.Container as Container

		canvas = event.GetEventObject()
		diagram = canvas.GetDiagram()

		if isinstance(self, (Container.Block, Container.Port)) and event.ControlDown():

			old_label = self.label
			
			d = LabelGUI.LabelDialog(canvas, self)
			d.ShowModal()

			### update priority list
			if self.label in diagram.priority_list and old_label != self.label:
				### find index of label priority list and replace it
				i = diagram.priority_list.index(self.label)
				diagram.priority_list[i] = new_label

				### if block we adapt the font according to the new label size
				if " " not in new_label and isinstance(self, Container.Block):
					font = wx.Font(self.font[0], self.font[1], self.font[2], self.font[3], False, self.font[4])
					ln = len(self.label) * font.GetPointSize()
					w = self.x[1] - self.x[0]

					if ln > w:
						a = ln - w
						self.x[0] -= a / 2
						self.x[1] += a / 2

				### update of panel properties
				mainW = wx.GetApp().GetTopWindow()
				nb1 = mainW.GetControlNotebook()

				### si le panel est actif, on update
				if nb1.GetSelection() == 1:
					newContent = AttributeEditor.AttributeEditor(nb1.propPanel, wx.ID_ANY, self, canvas)
					nb1.UpdatePropertiesPage(newContent)

		event.Skip()