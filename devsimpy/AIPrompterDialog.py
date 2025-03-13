# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# AIPrompterDialog.py ---
#                     --------------------------------
#                            Copyright (c) 2024
#                    A. Dominci (dominici_a@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 10/28/2024
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
import os

import gettext
_ = gettext.gettext

from Utilities import load_and_resize_image

# Définition du dialogue personnalisé
class AIPrompterDialog(wx.Dialog):
    def __init__(self, parent, title=_("AI Code Editor"), code_to_replace='', adapter=None):
        super().__init__(parent, id=wx.ID_ANY, title=title, size=(600, 400))

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

    # Sizer pour organiser les éléments
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Zone de texte pour le code sélectionné
        self.code_text = wx.TextCtrl(self, value=code_to_replace, style=wx.TE_MULTILINE)
        main_sizer.Add(wx.StaticText(self, label=_("Generated Code:")), 0, wx.ALL | wx.EXPAND, 5)
        main_sizer.Add(self.code_text, 1, wx.ALL | wx.EXPAND, 5)

        # Champ de texte pour le prompt
        self.prompt_input = wx.TextCtrl(self, value="", style=wx.TE_MULTILINE)
        main_sizer.Add(wx.StaticText(self, label=_("Please, tell me what you want:")), 0, wx.ALL | wx.EXPAND, 5)
        main_sizer.Add(self.prompt_input, 1, wx.ALL | wx.EXPAND, 5)

        # Set the focus to the prompt_input field to place the cursor there
        self.prompt_input.SetFocus()

        # Lier l'événement de texte pour détecter les saisies dans le champ de prompt
        self.prompt_input.Bind(wx.EVT_TEXT, self.on_prompt_input_change)

        # Sizer horizontal pour les boutons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Bouton pour envoyer la demande
        self.send_button = wx.Button(self, label=_("Send to AI"))
        self.send_button.Bind(wx.EVT_BUTTON, self.on_send_ai)
        self.send_button.SetToolTip(_("Send the prompt to AI for processing."))  # Ajouter un tooltip
        self.send_button.Enable(False)
        button_sizer.Add(self.send_button, 0, wx.ALL, 10)  # Ajout du bouton avec un espacement de 10

        # Bouton pour insérer la demande
        if self.editor:
            self.insert_button = wx.Button(self, label=_("Insert/Replace"))
            self.insert_button.Bind(wx.EVT_BUTTON, self.on_insert)
            self.insert_button.SetToolTip(_("Insert the generated code into the editor."))  # Ajouter un tooltip
            self.insert_button.Enable(False)
            button_sizer.Add(self.insert_button, 0, wx.ALL, 10)  # Ajout du bouton avec un espacement de 10
        else:
            self.insert_button = wx.Button(self, id=wx.ID_OK, label=_("Apply"))
            self.insert_button.Bind(wx.EVT_BUTTON, self.on_ok)  # Bind the button to close the dialog
            self.insert_button.Enable(False)
            button_sizer.Add(self.insert_button, 0, wx.ALL, 10)  # Ajout du bouton avec un espacement de 10

        main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER)  # Ajout du sizer de boutons au sizer principal

        self.SetSizer(main_sizer)
        self.Layout()

    def on_prompt_input_change(self, event):
        """Fonction de rappel qui s'active lorsque l'utilisateur tape dans le champ de prompt."""

        input_text = self.prompt_input.GetValue()

        # Ici, vous pouvez également activer ou désactiver les boutons selon le texte d'entrée
        if input_text:
            self.send_button.Enable(True)
        else:
            self.send_button.Enable(False)
            self.insert_button.Enable(False)

    def on_ok(self, event):
        self.generated_code = self.code_text.GetValue().strip()

        if self.generated_code:  # Only close if there's non-empty input
            self.EndModal(wx.ID_OK)  # Close the dialog by ending the modal state

    def on_insert(self, event):

        if not self.editor:
            return

        generated_code = self.code_text.GetValue()

        selection = self.editor.GetSelection()
        textstring = self.editor.GetRange(selection[0], selection[1])

        # Remplacement du texte dans l'éditeur si le texte a été modifié
        if generated_code and generated_code != textstring:	
            ### si text selectionné dans le code à remplace
            self.editor.ReplaceSelection(generated_code)

        ### sinon on insert en place
        else:
            self.editor.AddText(generated_code)

        self.parent.Notification(True, _('%s modified' % (os.path.basename(self.editor.GetFilename()))), '', '')

    def on_send_ai(self, event):
        # Récupération du prompt et du code sélectionné
        prompt = self.prompt_input.GetValue()
        code = self.code_text.GetValue()

        # Appel à l'IA via la méthode modify_model_part_prompt
        full_prompt = self.adapter.modify_model_part_prompt(code, prompt)
        modified_code = self.adapter.generate_output(full_prompt)

        # Mise à jour de la zone de texte avec le code modifié si une modification a été effectuée
        if modified_code:
            self.code_text.SetValue(modified_code)
            self.insert_button.Enable(True)
          