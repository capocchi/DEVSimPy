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
	"""Dialogue pour afficher les informations du diagramme et le code PlantUML"""
	
	def __init__(self, parent, diagram_info, puml_content):
		"""
		Args:
			parent: Parent window
			diagram_info: String avec les informations du diagramme
			puml_content: String avec le code PlantUML généré
		"""
		wx.Dialog.__init__(self, parent, wx.ID_ANY, _("Diagram Information"), 
						  style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
		self.SetSize((700, 500))
		
		self.puml_content = puml_content
		
		# Panel principal
		panel = wx.Panel(self)
		main_sizer = wx.BoxSizer(wx.VERTICAL)
		
		# Notebook pour séparer Info et PlantUML
		notebook = wx.Notebook(panel)
		
		# --- PAGE 1: Information ---
		info_panel = wx.Panel(notebook)
		info_sizer = wx.BoxSizer(wx.VERTICAL)
		
		text_ctrl = wx.TextCtrl(info_panel, wx.ID_ANY, diagram_info, 
							   style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_WORDWRAP)
		info_sizer.Add(text_ctrl, 1, wx.EXPAND|wx.ALL, 10)
		info_panel.SetSizer(info_sizer)
		
		notebook.AddPage(info_panel, _("Information"))
		
		# --- PAGE 2: PlantUML ---
		uml_panel = wx.Panel(notebook)
		uml_sizer = wx.BoxSizer(wx.VERTICAL)
		
		uml_text = wx.TextCtrl(uml_panel, wx.ID_ANY, puml_content, 
							  style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_WORDWRAP|wx.HSCROLL)
		uml_text.SetFont(wx.Font(9, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
		uml_sizer.Add(uml_text, 1, wx.EXPAND|wx.ALL, 10)
		
		# Boutons pour PlantUML
		uml_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
		
		btn_copy = wx.Button(uml_panel, wx.ID_ANY, _("Copy to Clipboard"))
		btn_view_online = wx.Button(uml_panel, wx.ID_ANY, _("View Online"))
		
		uml_btn_sizer.Add(btn_copy, 0, wx.ALL, 5)
		uml_btn_sizer.Add(btn_view_online, 0, wx.ALL, 5)
		uml_btn_sizer.AddStretchSpacer()
		
		uml_sizer.Add(uml_btn_sizer, 0, wx.EXPAND|wx.ALL, 5)
		uml_panel.SetSizer(uml_sizer)
		
		notebook.AddPage(uml_panel, _("PlantUML"))
		
		main_sizer.Add(notebook, 1, wx.EXPAND|wx.ALL, 5)
		
		# Bouton Close
		button_sizer = wx.BoxSizer(wx.HORIZONTAL)
		btn_close = wx.Button(panel, wx.ID_OK, _("Close"))
		button_sizer.AddStretchSpacer()
		button_sizer.Add(btn_close, 0, wx.ALL, 5)
		
		main_sizer.Add(button_sizer, 0, wx.EXPAND|wx.ALL, 5)
		
		panel.SetSizer(main_sizer)
		
		# Event handlers
		btn_copy.Bind(wx.EVT_BUTTON, self.OnCopyToClipboard)
		btn_view_online.Bind(wx.EVT_BUTTON, self.OnViewOnline)
		btn_close.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_OK))
	
	def OnCopyToClipboard(self, evt):
		"""Copier le code PlantUML dans le presse-papier"""
		if wx.TheClipboard.Open():
			wx.TheClipboard.SetData(wx.TextDataObject(self.puml_content))
			wx.TheClipboard.Close()
			wx.MessageBox(_("PlantUML code copied to clipboard!"), 
						 _("Success"), wx.OK|wx.ICON_INFORMATION)
	
	def OnViewOnline(self, evt):
		"""Ouvrir PlantUML web viewer avec encodage correct"""
		import webbrowser
		
		try:
			import zlib
			
			# PlantUML utilise DEFLATE (pas de header zlib)
			compressed = zlib.compress(self.puml_content.encode('utf-8'), 9)
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
				wx.TheClipboard.SetData(wx.TextDataObject(self.puml_content))
				wx.TheClipboard.Close()
			
			wx.MessageBox(
				_("PlantUML code copied to clipboard!\nOpening PlantUML website - please paste the code there."),
				_("Info"), wx.OK|wx.ICON_INFORMATION
			)
			webbrowser.open("https://editor.plantuml.com/uml/")
