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

# Définition du dialogue personnalisé
class AIPrompterDialog(wx.Dialog):
    def __init__(self, parent, code_to_replace, adapter):
        super().__init__(parent, title=_("AI Code Editor"), size=(600, 400))
        
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
            
       # Sizer pour organiser les éléments
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Zone de texte pour le code sélectionné
        self.code_text = wx.TextCtrl(self, value=code_to_replace, style=wx.TE_MULTILINE)
        main_sizer.Add(wx.StaticText(self, label=_("Code to replace/insert:")), 0, wx.ALL | wx.EXPAND, 5)
        main_sizer.Add(self.code_text, 1, wx.ALL | wx.EXPAND, 5)

        # Champ de texte pour le prompt
        self.prompt_input = wx.TextCtrl(self, value="", style=wx.TE_MULTILINE)
        main_sizer.Add(wx.StaticText(self, label=_("Enter Prompt for AI:")), 0, wx.ALL | wx.EXPAND, 5)
        main_sizer.Add(self.prompt_input, 1, wx.ALL | wx.EXPAND, 5)
        
        # Lier l'événement de texte pour détecter les saisies dans le champ de prompt
        self.prompt_input.Bind(wx.EVT_TEXT, self.on_prompt_input_change)

        # Sizer horizontal pour les boutons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Bouton pour envoyer la demande
        self.send_button = wx.Button(self, label=_("Send to Prompt"))
        self.send_button.Bind(wx.EVT_BUTTON, self.on_send_ai)
        self.send_button.SetToolTip(_("Send the prompt to AI for processing."))  # Ajouter un tooltip
        self.send_button.Enable(False)
        button_sizer.Add(self.send_button, 0, wx.ALL, 10)  # Ajout du bouton avec un espacement de 10

        # Bouton pour insérer la demande
        self.insert_button = wx.Button(self, label=_("Insert/Replace"))
        self.insert_button.Bind(wx.EVT_BUTTON, self.on_insert)
        self.insert_button.SetToolTip(_("Insert the generated code into the editor."))  # Ajouter un tooltip
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

    def on_insert(self, event):

        if not self.editor:
            return

        modified_text = self.code_text.GetValue()
		
        selection = self.editor.GetSelection()
        textstring = self.editor.GetRange(selection[0], selection[1])
        
		# Remplacement du texte dans l'éditeur si le texte a été modifié
        if modified_text and modified_text != textstring:	
            ### si text selectionné dans le code à remplace
            self.editor.ReplaceSelection(modified_text)
        
        ### sinon on insert en place
        else:
            self.editor.AddText(modified_text)

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

# Fonction principale pour exécuter l'application
def main():
    # Initialisation de l'application wxPython
    app = wx.App(False)

    # Crée un objet d'adaptateur fictif (à remplacer par votre propre logique)
    class DummyAdapter:
        def modify_model_part_prompt(self, code, prompt):
            return f"{code}\n# Prompt: {prompt}"

        def generate_output(self, full_prompt):
            return f"# Modified Code based on prompt:\n{full_prompt}"

    # Code de démonstration
    demo_code = ""

    # Création et affichage du dialogue
    dialog = AIPrompterDialog(None, demo_code, DummyAdapter())
    dialog.ShowModal()  # Affiche le dialogue
    dialog.Destroy()  # Détruit le dialogue après fermeture

    # Démarre la boucle principale de l'application
    app.MainLoop()

if __name__ == "__main__":
    main()