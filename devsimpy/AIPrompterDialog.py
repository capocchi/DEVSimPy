# -*- coding: utf-8 -*-

'''
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# AIPrompterDialog.py ---
#                     --------------------------------
#                            Copyright (c) 2024
#                    A. Dominci (dominici_a@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 10/28/2024
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
'''

import json
import wx
import os

import gettext
_ = gettext.gettext

from Utilities import load_and_resize_image

# Définition du dialogue personnalisé
class AIPrompterDialog(wx.Dialog):
    def __init__(self, parent, title=_("AI Code Editor"), code_to_replace='', adapter=None):
        super().__init__(parent, id=wx.ID_ANY, title=title)

        _icon = wx.Icon()
        _icon.CopyFromBitmap(load_and_resize_image("puce_ai.png"))
        self.SetIcon(_icon)

        ### local copy
        self.adapter = adapter
        self.parent = parent
        self.code_to_replace = code_to_replace

        ### editor instance
        if parent:
            nb = parent.GetNoteBook()
            self.editor = nb.GetCurrentPage()
        else:
            self.editor = None

        ### Code generated inside the self.code_text field
        self.generated_code = ""

        # generated JSON representing a newly created model
        self.model_json = None

        self.__init_ui()
        self.Center()

    def __init_ui(self):
        """Initialize the user interface"""
        
        # Taille optimale
        self.SetSize((700, 600))
        self.SetMinSize((650, 500))
        
        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
        
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # --- Section Generated Code ---
        code_box = wx.StaticBoxSizer(wx.VERTICAL, panel, _("Generated Code"))
        
        self.code_text = wx.TextCtrl(
            panel, 
            value=self.code_to_replace, 
            style=wx.TE_MULTILINE | wx.TE_RICH2
        )
        # Police monospace pour le code
        font = wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.code_text.SetFont(font)
        
        code_box.Add(self.code_text, proportion=1, flag=wx.ALL|wx.EXPAND, border=5)
        main_sizer.Add(code_box, proportion=2, flag=wx.ALL|wx.EXPAND, border=15)
        
        # --- Section Prompt ---
        prompt_box = wx.StaticBoxSizer(wx.VERTICAL, panel, _("AI Prompt"))
        
        # Info text
        info_text = wx.StaticText(
            panel, 
            label=_("Describe what you want the AI to do with the code above:")
        )
        info_text.SetForegroundColour(wx.Colour(100, 100, 100))
        prompt_box.Add(info_text, flag=wx.ALL, border=5)
        
        self.prompt_input = wx.TextCtrl(
            panel, 
            value="", 
            style=wx.TE_MULTILINE | wx.TE_RICH2
        )
        self.prompt_input.SetFont(font)
        self.prompt_input.SetHint(_("Example: Add error handling to this function..."))
        prompt_box.Add(self.prompt_input, proportion=1, flag=wx.ALL|wx.EXPAND, border=5)
        
        # Set the focus to the prompt_input field
        self.prompt_input.SetFocus()
        
        # Bind text event
        self.prompt_input.Bind(wx.EVT_TEXT, self.on_prompt_input_change)
        
        main_sizer.Add(prompt_box, proportion=1, flag=wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, border=15)
        
        # --- Buttons Section ---
        button_panel = wx.Panel(panel)
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Bouton Help/Info à gauche
        self.help_button = wx.Button(button_panel, label=_("Help"), size=(100, 32))
        self.help_button.SetBitmap(load_and_resize_image("info.png"))
        self.help_button.Bind(wx.EVT_BUTTON, self.on_help)
        self.help_button.SetToolTip(_("Show help on how to use this dialog"))
        button_sizer.Add(self.help_button, flag=wx.RIGHT, border=10)
        
        # Spacer pour pousser les autres boutons à droite
        button_sizer.AddStretchSpacer()
        
        # Bouton Send to AI
        self.send_button = wx.Button(button_panel, label=_("Send to AI"), size=(120, 32))
        self.send_button.Bind(wx.EVT_BUTTON, self.on_send_ai)
        self.send_button.SetToolTip(_("Send the prompt to AI for processing"))
        self.send_button.Enable(False)
        button_sizer.Add(self.send_button, flag=wx.RIGHT, border=5)
        
        # Bouton Insert/Replace ou Apply
        if self.editor:
            self.insert_button = wx.Button(button_panel, label=_("Insert/Replace"), size=(120, 32))
            self.insert_button.Bind(wx.EVT_BUTTON, self.on_insert)
            self.insert_button.SetToolTip(_("Insert or replace the generated code in the editor"))
            self.insert_button.Enable(False)
            button_sizer.Add(self.insert_button, flag=wx.RIGHT, border=5)
        else:
            self.insert_button = wx.Button(button_panel, id=wx.ID_OK, label=_("Apply"), size=(120, 32))
            self.insert_button.Bind(wx.EVT_BUTTON, self.on_ok)
            self.insert_button.SetToolTip(_("Apply the generated code"))
            self.insert_button.Enable(False)
            button_sizer.Add(self.insert_button, flag=wx.RIGHT, border=5)

            self.download_json_button = wx.Button(button_panel, label=_("Download JSON"), size=(130, 32))
            self.download_json_button.Bind(wx.EVT_BUTTON, self.on_download_json)
            self.download_json_button.SetToolTip(_("Download the JSON corresponding to the atomic model"))
            self.download_json_button.Enable(False)
            button_sizer.Add(self.download_json_button, flag=wx.RIGHT, border=5)
        
        # Bouton Cancel
        self.cancel_button = wx.Button(button_panel, wx.ID_CANCEL, _("Cancel"), size=(100, 32))
        button_sizer.Add(self.cancel_button)
        
        button_panel.SetSizer(button_sizer)
        main_sizer.Add(button_panel, flag=wx.ALL|wx.EXPAND, border=15)
        
        panel.SetSizer(main_sizer)
        panel.Layout()

    def on_help(self, event):
        """Display help information"""
        
        if self.editor:
            help_text = _(
                "AI Code Editor - Help\n\n"
                "This tool helps you modify code using AI assistance.\n\n"
                "How to use:\n\n"
                "1. Generated Code Section:\n"
                "   • Shows the initial code or AI-generated modifications\n"
                "   • You can manually edit this code if needed\n\n"
                "2. AI Prompt Section:\n"
                "   • Describe what you want the AI to do\n"
                "   • Examples:\n"
                "     - 'Add error handling'\n"
                "     - 'Optimize this function'\n"
                "     - 'Add documentation comments'\n"
                "     - 'Refactor to use list comprehension'\n\n"
                "3. Buttons:\n"
                "   • Send to AI: Process your prompt and generate code\n"
                "   • Insert/Replace: Put the code into your editor\n"
                "   • Cancel: Close without changes\n\n"
                "Tips:\n"
                "• Be specific in your prompts for better results\n"
                "• You can send multiple prompts to refine the code\n"
                "• Review the generated code before inserting"
            )
        else:
            help_text = _(
                "AI Model Generator - Help\n\n"
                "This tool helps you generate model code using AI.\n\n"
                "How to use:\n\n"
                "1. Generated Code Section:\n"
                "   • Shows the AI-generated model code\n"
                "   • You can manually edit this code if needed\n\n"
                "2. AI Prompt Section:\n"
                "   • Describe the model you want to create\n"
                "   • Examples:\n"
                "     - 'Create a queue model with FIFO behavior'\n"
                "     - 'Generate a sensor model that samples data'\n"
                "     - 'Build a controller with PID algorithm'\n\n"
                "3. Buttons:\n"
                "   • Send to AI: Generate the model from your prompt\n"
                "   • Apply: Accept the generated code\n"
                "   • Download JSON: Save the model as JSON file\n"
                "   • Cancel: Close without saving\n\n"
                "Tips:\n"
                "• Describe the model behavior clearly\n"
                "• Specify inputs, outputs, and state variables\n"
                "• Review and test the generated model"
            )
        
        dlg = wx.MessageDialog(
            self,
            help_text,
            _("Help - AI Code Editor"),
            wx.OK | wx.ICON_INFORMATION
        )
        dlg.ShowModal()
        dlg.Destroy()

    def on_prompt_input_change(self, event):
        """Fonction de rappel qui s'active lorsque l'utilisateur tape dans le champ de prompt."""

        input_text = self.prompt_input.GetValue().strip()

        # Activer/désactiver les boutons selon le texte d'entrée
        if input_text:
            self.send_button.Enable(True)
        else:
            self.send_button.Enable(False)

    def on_ok(self, event):
        self.generated_code = self.code_text.GetValue().strip()

        if self.generated_code:  # Only close if there's non-empty input
            self.EndModal(wx.ID_OK)

    def on_insert(self, event):

        if not self.editor:
            return

        generated_code = self.code_text.GetValue()

        selection = self.editor.GetSelection()
        textstring = self.editor.GetRange(selection[0], selection[1])

        # Remplacement du texte dans l'éditeur si le texte a été modifié
        if generated_code and generated_code != textstring:	
            ### si text selectionné dans le code à remplacer
            self.editor.ReplaceSelection(generated_code)
        ### sinon on insère en place
        else:
            self.editor.AddText(generated_code)

        self.parent.Notification(
            True, 
            _('%s modified' % (os.path.basename(self.editor.GetFilename()))), 
            '', 
            ''
        )
        
        self.Close()

    def on_send_ai(self, event):
        # Désactiver le bouton pendant le traitement
        self.send_button.Enable(False)
        self.send_button.SetLabel(_("Processing..."))
        
        # Forcer le rafraîchissement de l'interface
        wx.SafeYield()
        
        try:
            # Récupération du prompt et du code sélectionné
            prompt = self.prompt_input.GetValue()
            code = self.code_text.GetValue()

            # Appel à l'IA via la méthode modify_model_part_prompt
            if not self.editor:
                self.model_json = self.adapter.generate_model_json(prompt)
                modified_code = self.adapter.generate_model_code(self.model_json)
            else:
                full_prompt = self.adapter.modify_model_part_prompt(code, prompt)
                modified_code = self.adapter.generate_output(full_prompt)

            # Mise à jour de la zone de texte avec le code modifié
            if modified_code:
                self.code_text.SetValue(modified_code)
                self.insert_button.Enable(True)
                # Activate download json button if json created
                if self.model_json:
                    self.download_json_button.Enable(True)
            else:
                wx.MessageBox(
                    _("No code was generated. Please try again with a different prompt."),
                    _("No Result"),
                    wx.OK | wx.ICON_WARNING
                )
        
        except Exception as e:
            wx.MessageBox(
                _("An error occurred while processing your request:\n{}").format(str(e)),
                _("Error"),
                wx.OK | wx.ICON_ERROR
            )
        
        finally:
            # Réactiver le bouton
            self.send_button.Enable(True)
            self.send_button.SetLabel(_("Send to AI"))

    def on_download_json(self, event):
        dlg = wx.FileDialog(
            self,
            message=_("Save file as..."),
            defaultFile="atomic_model.json",
            wildcard="JSON files (*.json)|*.json|All files (*.*)|*.*",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        )
        
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            try:
                with open(path, "w") as file:
                    file.write(json.dumps(self.model_json, indent=2))
                
                wx.MessageBox(
                    _("JSON file saved successfully!"),
                    _("Success"),
                    wx.OK | wx.ICON_INFORMATION
                )
            except Exception as e:
                wx.MessageBox(
                    _("Error saving file:\n{}").format(str(e)),
                    _("Error"),
                    wx.OK | wx.ICON_ERROR
                )
        
        dlg.Destroy()