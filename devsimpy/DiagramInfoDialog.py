#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# DiagramInfoDialog.py --- Dialog to dislay the information of the diagram
#                     and the generated PlantUML code
#
#                     --------------------------------
#                            Copyright (c) 2025
#                     L. CAPOCCHI (capocchi@univ-corse.fr)
#                		SPE Lab - University of Corsica
#                     --------------------------------
# Version 1.0                                      last modified:  12/24/25
# ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
'''

import wx

_ = wx.GetTranslation

class DiagramInfoDialog(wx.Dialog):
	"""Dialogue pour afficher les informations du diagramme et les codes PlantUML"""
	
	def __init__(self, parent, diagram_info, puml_component, puml_class):
		"""
		Args:
			parent: Parent window
			diagram_info: String avec les informations du diagramme
			puml_component: String avec le code PlantUML du diagramme de composants
			puml_class: String avec le code PlantUML du diagramme de classes
		"""
		wx.Dialog.__init__(self, parent, wx.ID_ANY, _("Diagram Information"), 
						  style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
		self.SetSize((700, 500))
		
		self.puml_component = puml_component
		self.puml_class = puml_class
		
		# Panel principal
		panel = wx.Panel(self)
		main_sizer = wx.BoxSizer(wx.VERTICAL)
		
		# Notebook avec 3 onglets
		notebook = wx.Notebook(panel)
		
		# --- PAGE 1: Information ---
		info_panel = wx.Panel(notebook)
		info_sizer = wx.BoxSizer(wx.VERTICAL)
		
		text_ctrl = wx.TextCtrl(info_panel, wx.ID_ANY, diagram_info, 
							   style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_WORDWRAP)
		info_sizer.Add(text_ctrl, 1, wx.EXPAND|wx.ALL, 10)
		info_panel.SetSizer(info_sizer)
		
		notebook.AddPage(info_panel, _("Information"))
		
		# --- PAGE 2: PlantUML Component Diagram ---
		comp_panel = wx.Panel(notebook)
		comp_sizer = wx.BoxSizer(wx.VERTICAL)
		
		comp_text = wx.TextCtrl(comp_panel, wx.ID_ANY, puml_component, 
							  style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_WORDWRAP|wx.HSCROLL)
		comp_text.SetFont(wx.Font(9, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
		comp_sizer.Add(comp_text, 1, wx.EXPAND|wx.ALL, 10)
		
		# Boutons pour Component diagram
		comp_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
		
		btn_comp_copy = wx.Button(comp_panel, wx.ID_ANY, _("Copy to Clipboard"))
		btn_comp_view = wx.Button(comp_panel, wx.ID_ANY, _("View Online"))
		
		comp_btn_sizer.Add(btn_comp_copy, 0, wx.ALL, 5)
		comp_btn_sizer.Add(btn_comp_view, 0, wx.ALL, 5)
		comp_btn_sizer.AddStretchSpacer()
		
		comp_sizer.Add(comp_btn_sizer, 0, wx.EXPAND|wx.ALL, 5)
		comp_panel.SetSizer(comp_sizer)
		
		notebook.AddPage(comp_panel, _("Component Diagram"))
		
		# --- PAGE 3: PlantUML Class Diagram ---
		class_panel = wx.Panel(notebook)
		class_sizer = wx.BoxSizer(wx.VERTICAL)
		
		class_text = wx.TextCtrl(class_panel, wx.ID_ANY, puml_class, 
							   style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_WORDWRAP|wx.HSCROLL)
		class_text.SetFont(wx.Font(9, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
		class_sizer.Add(class_text, 1, wx.EXPAND|wx.ALL, 10)
		
		# Boutons pour Class diagram
		class_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
		
		btn_class_copy = wx.Button(class_panel, wx.ID_ANY, _("Copy to Clipboard"))
		btn_class_view = wx.Button(class_panel, wx.ID_ANY, _("View Online"))
		
		class_btn_sizer.Add(btn_class_copy, 0, wx.ALL, 5)
		class_btn_sizer.Add(btn_class_view, 0, wx.ALL, 5)
		class_btn_sizer.AddStretchSpacer()
		
		class_sizer.Add(class_btn_sizer, 0, wx.EXPAND|wx.ALL, 5)
		class_panel.SetSizer(class_sizer)
		
		notebook.AddPage(class_panel, _("Class Diagram"))
		
		main_sizer.Add(notebook, 1, wx.EXPAND|wx.ALL, 5)
		
		# Bouton Close
		button_sizer = wx.BoxSizer(wx.HORIZONTAL)
		btn_close = wx.Button(panel, wx.ID_OK, _("Close"))
		button_sizer.AddStretchSpacer()
		button_sizer.Add(btn_close, 0, wx.ALL, 5)
		
		main_sizer.Add(button_sizer, 0, wx.EXPAND|wx.ALL, 5)
		
		panel.SetSizer(main_sizer)
		
		# Event handlers - Component diagram
		btn_comp_copy.Bind(wx.EVT_BUTTON, lambda e: self.OnCopyToClipboard('component'))
		btn_comp_view.Bind(wx.EVT_BUTTON, lambda e: self.OnViewOnline('component'))
		
		# Event handlers - Class diagram
		btn_class_copy.Bind(wx.EVT_BUTTON, lambda e: self.OnCopyToClipboard('class'))
		btn_class_view.Bind(wx.EVT_BUTTON, lambda e: self.OnViewOnline('class'))
		
		btn_close.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_OK))
	
	def OnCopyToClipboard(self, diagram_type):
		"""Copier le code PlantUML dans le presse-papier"""
		content = self.puml_component if diagram_type == 'component' else self.puml_class
		
		if wx.TheClipboard.Open():
			wx.TheClipboard.SetData(wx.TextDataObject(content))
			wx.TheClipboard.Close()
			wx.MessageBox(_("PlantUML code copied to clipboard!"), 
						 _("Success"), wx.OK|wx.ICON_INFORMATION)
	
	def OnViewOnline(self, diagram_type):
		"""Ouvrir PlantUML web viewer avec encodage correct"""
		import webbrowser
		
		content = self.puml_component if diagram_type == 'component' else self.puml_class
		
		try:
			import zlib
			
			# PlantUML utilise DEFLATE (pas de header zlib)
			compressed = zlib.compress(content.encode('utf-8'), 9)
			# Enlever les 2 premiers bytes (header zlib) et 4 derniers (checksum)
			compressed = compressed[2:-4]
			
			# Alphabet PlantUML (pas base64 standard!)
			plantuml_alphabet = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_'
			
			def encode_plantuml(data):
				"""Encode bytes to PlantUML format"""
				result = []
				i = 0
				while i < len(data):
					# Prendre 3 bytes
					b1 = data[i] if i < len(data) else 0
					b2 = data[i+1] if i+1 < len(data) else 0
					b3 = data[i+2] if i+2 < len(data) else 0
					
					# Convertir en 4 caractères (6 bits chacun)
					c1 = b1 >> 2
					c2 = ((b1 & 0x3) << 4) | (b2 >> 4)
					c3 = ((b2 & 0xF) << 2) | (b3 >> 6)
					c4 = b3 & 0x3F
					
					result.append(plantuml_alphabet[c1])
					result.append(plantuml_alphabet[c2])
					result.append(plantuml_alphabet[c3] if i+1 < len(data) else '')
					result.append(plantuml_alphabet[c4] if i+2 < len(data) else '')
					
					i += 3
				
				return ''.join(result)
			
			encoded = encode_plantuml(compressed)
			
			url = f"https://editor.plantuml.com/uml/{encoded}"
			
			webbrowser.open(url)
			
		except Exception as e:
			# Fallback : copier dans le presse-papier et ouvrir le site
			if wx.TheClipboard.Open():
				wx.TheClipboard.SetData(wx.TextDataObject(content))
				wx.TheClipboard.Close()
			
			wx.MessageBox(
				_("PlantUML code copied to clipboard!\nOpening PlantUML website - please paste the code there."),
				_("Info"), wx.OK|wx.ICON_INFORMATION
			)
			webbrowser.open("https://editor.plantuml.com/uml/")

