# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# AiAdapter.py ---
#                    --------------------------------
#                            Copyright (c) 2020
#                    A. Dominici and L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 11/01/24
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

import logging
from abc import ABC, abstractmethod
from openai import OpenAI
import socket
import subprocess
import builtins
import wx
import ollama
import os
import sys
import urllib.request

from Decorators import BuzyCursorNotification, cond_decorator, ProgressNotification
from Utilities import check_internet

import gettext
_ = gettext.gettext

# Configuration de base du logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class DevsAIAdapter(ABC):
    """
    Parent class to interface the DEVS software with generative AI models.
    This class defines the base methods that child classes can override
    or use as is to interact with specific generative AI models.
    """
    def __init__(self, parent=None):
        logging.info("DevsAIAdapter initialized.")
        self.base_prompt = self._load_base_prompt("AI/DEVS_Explanation.txt")
    
    def _load_base_prompt(self, file_path):
        """
        Loads the base prompt from the DEVS model explanation file.
        """
        try:
            with open(file_path, "r") as file:
                return file.read()
        except FileNotFoundError:
            logging.error("File not found: %s", file_path)
            raise

    def create_prompt(self, model_name, num_inputs, num_outputs, model_type, prompt):
        """
        Creates a prompt to generate a DEVS model based on the type and the provided details.
        The prompt is based on instructions from the DEVS explanation file.
        """
        logging.info("Creating prompt for model: %s, type: %s", model_name, model_type)
        
        # Constructing the prompt for the AI
        full_prompt = f"""
        You are an expert in DEVS modeling. Create a DEVS model called '{model_name}'.
        This model has {num_inputs} inputs and {num_outputs} outputs.
        It is a '{model_type}' type model.

        Use the following guidelines for DEVS model creation:
        {self.base_prompt}

        Include only the model code. Do not include any code block markers like ```python.
        Do not provide any explanations, only the code. All the tabulation with be made using tab and not space.

        Additional details:
        {prompt}
        """
        logging.debug("Prompt created successfully for model: %s", model_name)
        return full_prompt

    def modify_model_prompt(self, code, prompt):
        """
        Generates a prompt to modify an existing DEVS model.
        Takes into account the model name, the current code, and additional details.
        """
        logging.info("Modifying model")
        
        # Constructing the prompt for the AI
        full_prompt = f"""
        You are an expert in DEVS modeling. You need to modify a DEVS model.
        Here is the current model code:
        {code}

        Use the following DEVS model guidelines for reference:
        {self.base_prompt}

        Here are the specific details to modify the model:
        {prompt}

        Include only the modified model code. Do not include any code block markers like ```python.
        Do not provide any explanations, only the code.
        """
        logging.debug("Modification prompt created for model.")
        return full_prompt
    
    def modify_model_part_prompt(self, code, prompt):
        """
        Generates a prompt to modify a specific part of an existing DEVS model.
        Takes into account the model name, the current code, and details about the part to modify.
        """
        logging.info("Modifying part of model.")
        
        # Constructing the prompt for the AI
        full_prompt = f"""
        You are an expert in DEVS modeling. You need to modify a specific part of a DEVS model.
        Here is the current model code:
        <{code}>
        
        Use the following DEVS model guidelines for reference:
        {self.base_prompt}

        Here are the specific details to modify this part of the model:
        {prompt}

        Include only the code of the modified part of the model. Do not include any code block markers like ```python.
        Do not provide any explanations, only the code. Keep the indentation, it is really important.
        """
        logging.debug("Modification part prompt created for model")
        return full_prompt

    @abstractmethod
    def generate_output(self, prompt, **kwargs):
        """
        Abstract method to generate an output from the AI model.
        Child classes should override this method to specify how the generative AI produces outputs based on a prompt.
        `**kwargs` can include parameters such as the API key for models that require it.
        """
        pass

    def validate_model(self, model_name):
        """
        Placeholder method for future implementation.
        """
        logging.info("Validation not implemented for model: %s", model_name)
        pass

##########################################################
###
### FACTORY
###
##########################################################
class AdapterFactory:
    _instance = None
    _current_selected_ia = None  # Suivi de l'état actuel de l'IA sélectionnée

    @staticmethod
    def verify_adapter_instance():
        """ 
        Verifie que l'instance de l'adapteur fonctionne
        """
        return not AdapterFactory._instance is None

    @staticmethod
    def get_adapter_instance(parent=None, params=None):
        """ 
        Retourne une instance unique de l'adaptateur sélectionné.
        Réinitialise l'instance si `selected_ia` a changé en cours d'exécution.
        """
        selected_ia = builtins.__dict__.get("SELECTED_IA", "")

        # Vérifie si l'IA sélectionnée a changé
        if AdapterFactory._current_selected_ia != selected_ia:
            AdapterFactory._instance = None  # Réinitialise l'instance
            AdapterFactory._current_selected_ia = selected_ia  # Met à jour la sélection

        # Crée une nouvelle instance si nécessaire
        if AdapterFactory._instance is None:
            # Récupère les paramètres d'API et de port de PARAMS_IA

            api_key = params.get('CHATGPT_API_KEY') if params else None
            port = params.get('OLLAMA_PORT') if params else None
            
            # Validation pour ChatGPT
            if selected_ia == "ChatGPT":
                if not api_key:
                    AdapterFactory._show_error(_("API key is required for ChatGPT."))
                    return None
                    # raise ValueError(_("API key is required for ChatGPT."))
                else:
                    AdapterFactory._instance = ChatGPTDevsAdapter(parent=parent, api_key=api_key)

            # Validation pour Ollama
            elif selected_ia == "Ollama":
                if not port:
                    AdapterFactory._show_error(_("Port is required for Ollama."))
                    return None
                    # raise ValueError(_("Port is required for Ollama."))
                else:
                    AdapterFactory._instance = OllamaDevsAdapter(parent=parent, port=port)

            else:
                AdapterFactory._show_error(_("No AI selected or unknown AI."))
                # raise ValueError(_("No AI selected or unknown AI."))

        return AdapterFactory._instance

    @staticmethod
    def reset_instance():
        """ Réinitialise manuellement l'instance et l'IA sélectionnée. """
        AdapterFactory._instance = None
        AdapterFactory._current_selected_ia = None

    @staticmethod
    def _show_error(message):
        """ Affiche un message d'erreur sous forme de toast avec wx. """
        wx.MessageBox(message, _("Error"), wx.ICON_ERROR)

##########################################################
###
### CHATGPT
###
##########################################################
class ChatGPTDevsAdapter(DevsAIAdapter):
    """
    Adaptateur spécifique pour ChatGPT, utilisant GPT-4 pour générer des modèles DEVS.
    """

    def __init__(self, api_key=None, parent=None):
        super().__init__()
        # if not api_key:
            # raise ValueError(_("API key is required for ChatGPT."))
        self.api_key = api_key
        self.wxparent = parent
        self.api_client = OpenAI(api_key=self.api_key)  # Instancie le client API ici
        logging.info(_("ChatGPTDevsAdapter initialized with provided API key."))

    @BuzyCursorNotification
    def generate_output(self, prompt):
        """
        Génère une sortie en utilisant l'API ChatGPT basée sur le prompt donné.
        """
        try:
            # Validation de la présence du prompt
            if not prompt:
                raise ValueError("Prompt cannot be empty")

            # Envoi de la requête à l'API
            response = self.api_client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert in DEVS modeling."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Validation de la réponse
            if not hasattr(response, 'choices') or not response.choices:
                logging.error("No choices found in response.")
                return _("No response received from the AI model.")
            
            # Retourner le contenu du message
            return response.choices[0].message.content
        
        except ValueError as ve:
            logging.error(_(f"Validation error: {ve}"))
            return _(f"Validation error: {ve}")
        
        except Exception as e:
            # Journalisation de l'erreur avec les détails de l'exception
            logging.error(_(f"Error while generating output: {e}"))
            return _(f"An error occurred while generating the output: {e}")

##########################################################
###
### OLLAMA
###
##########################################################
class OllamaDevsAdapter(DevsAIAdapter):
    """
    Adaptateur spécifique pour Ollama, utilisé pour générer des modèles DEVS.
    """

    def __init__(self, port='11434', model_name='qwen2.5-coder', parent=None):
        super().__init__()

        if not port:
            raise ValueError("Le port est requis pour Ollama.")
        
        ### local copy
        self.port = port
        self.wxparent = parent
        self.model_name = model_name
        # logging.info(_(f"OllamaDevsAdapter initialized with port {port} and model {model_name}."))
        
        # Vérification de l'installation d'Ollama
        if not self._is_ollama_installed():
            if check_internet():
                self._prompt_install_ollama()
            else:
                message = _("No internet connection. Please check your internet connection and try again.")
                wx.CallAfter(wx.MessageBox, message, _("Information"), wx.ICON_INFORMATION)
                logging.info(message)
        else:    
            # Obtenir la liste des modèles téléchargés localement
            self.local_model = self._get_models()

        # Téléchargement du modèle spécifié
        self._ensure_model_downloaded()

            # Vérification si le serveur est lancé au démarrage
            if not self._is_server_running():
                logging.info(_("The Ollama server is not running. Attempting to start..."))
                self._start_server()
            else:
                logging.info(_("The Ollama server is already running."))

            # Téléchargement du modèle spécifié
            self._ensure_model_downloaded()

    def _is_ollama_installed(self):
        """ Vérifie si Ollama est installé en cherchant son exécutable. """
        command = ["where", "ollama"] if sys.platform == "win32" else ["which", "ollama"]
        return subprocess.run(command, capture_output=True).returncode == 0

    def _prompt_install_ollama(self):
        """ Affiche une fenêtre `wx` pour proposer l'installation d'Ollama. """
        
        message = _("Ollama is not installed. Would you like to install it now?")
        dialog = wx.MessageDialog(None, message, _("Ollama install"), wx.YES_NO | wx.ICON_QUESTION)
        
        if dialog.ShowModal() == wx.ID_YES:
            logging.info(_("Starting the installation of Ollama..."))
            self._install_ollama()
        else:
            logging.error(_("Ollama is required to run this class."))
            raise RuntimeError(_("Ollama is not installed and is required to run this class."))
                
        dialog.Destroy()

    @cond_decorator(builtins.__dict__.get('GUI_FLAG', True), ProgressNotification(_(f"Download")))        
    def _install_ollama(self):
        """ Installe Ollama selon le système d'exploitation. """
        platform = sys.platform

        try:
            if platform == "darwin":  # macOS
                subprocess.run("curl -O https://ollama.com/download/Ollama-darwin.zip && unzip Ollama-darwin.zip -d /usr/local/bin && rm Ollama-darwin.zip", shell=True, check=True)
            elif platform.startswith("linux"):  # Linux
                subprocess.run("curl -fsSL https://ollama.com/install.sh | sh", shell=True, check=True)
            elif platform == "win32":  # Windows
                ollama_path = os.path.join(os.environ['USERPROFILE'], "Downloads", "OllamaSetup.exe")
                download_url = "https://ollama.com/download/OllamaSetup.exe"
                
                # Téléchargement avec message de chargement
                # self._show_download_message(download_url, ollama_path)
                # Effectue le téléchargement
                urllib.request.urlretrieve(download_url, ollama_path)

                # Exécution de l'installateur
                subprocess.run([ollama_path], check=True)

            logging.info(_("Ollama installation completed. Restart devsimpy and the terminal if necessary."))

        except subprocess.CalledProcessError as e:
            logging.error(_("Error during Ollama installation: %s"), e)
            raise RuntimeError(_("Ollama installation failed."))

    # def _show_download_message(self, url, dest_path):
    #     """Affiche une fenêtre wx avec le message de téléchargement sans interférer avec l'application wx existante."""
    #     frame = wx.Frame(None, -1, _("Download"), size=(500, 100))
    #     panel = wx.Panel(frame, -1)
        
    #     text = wx.StaticText(panel, -1, _("Downloading..."), pos=(50, 20))
    #     font = text.GetFont()
    #     font.PointSize += 2
    #     font = font.Bold()
    #     text.SetFont(font)
        
    #     frame.Centre()
    #     frame.Show()

    #     # Effectue le téléchargement
    #     urllib.request.urlretrieve(url, dest_path)

    #     # Ferme la fenêtre une fois le téléchargement terminé
    #     frame.Close()

    def _is_ollama_installed(self):
        """ Vérifie si Ollama est installé en cherchant son exécutable. """
        command = ["where", "ollama"] if sys.platform == "win32" else ["which", "ollama"]
        return subprocess.run(command, capture_output=True).returncode == 0

    def _prompt_install_ollama(self):
        """ Affiche une fenêtre `wx` pour proposer l'installation d'Ollama. """
        
        message = _("Ollama is not installed. Would you like to install it now?")
        dialog = wx.MessageDialog(None, message, _("Ollama install"), wx.YES_NO | wx.ICON_QUESTION)
        
        if dialog.ShowModal() == wx.ID_YES:
            logging.info(_("Starting the installation of Ollama..."))
            self._install_ollama()
        else:
            logging.error(_("Ollama is required to run this class."))
            raise RuntimeError(_("Ollama is not installed and is required to run this class."))
                
        dialog.Destroy()

    @cond_decorator(builtins.__dict__.get('GUI_FLAG', True), ProgressNotification(_(f"Download")))        
    def _install_ollama(self):
        """ Installe Ollama selon le système d'exploitation. """
        platform = sys.platform

        try:
            if platform == "darwin":  # macOS
                subprocess.run("curl -O https://ollama.com/download/Ollama-darwin.zip && unzip Ollama-darwin.zip -d /usr/local/bin && rm Ollama-darwin.zip", shell=True, check=True)
            elif platform.startswith("linux"):  # Linux
                subprocess.run("curl -fsSL https://ollama.com/install.sh | sh", shell=True, check=True)
            elif platform == "win32":  # Windows
                ollama_path = os.path.join(os.environ['USERPROFILE'], "Downloads", "OllamaSetup.exe")
                download_url = "https://ollama.com/download/OllamaSetup.exe"
                
                # Téléchargement avec message de chargement
                # self._show_download_message(download_url, ollama_path)
                # Effectue le téléchargement
                urllib.request.urlretrieve(download_url, ollama_path)

                # Exécution de l'installateur
                subprocess.run([ollama_path], check=True)

            logging.info(_("Ollama installation completed. Restart devsimpy and the terminal if necessary."))

        except subprocess.CalledProcessError as e:
            logging.error(_("Error during Ollama installation: %s"), e)
            raise RuntimeError(_("Ollama installation failed."))

    # def _show_download_message(self, url, dest_path):
    #     """Affiche une fenêtre wx avec le message de téléchargement sans interférer avec l'application wx existante."""
    #     frame = wx.Frame(None, -1, _("Download"), size=(500, 100))
    #     panel = wx.Panel(frame, -1)
        
    #     text = wx.StaticText(panel, -1, _("Downloading..."), pos=(50, 20))
    #     font = text.GetFont()
    #     font.PointSize += 2
    #     font = font.Bold()
    #     text.SetFont(font)
        
    #     frame.Centre()
    #     frame.Show()

    #     # Effectue le téléchargement
    #     urllib.request.urlretrieve(url, dest_path)

    #     # Ferme la fenêtre une fois le téléchargement terminé
    #     frame.Close()

    def _is_server_running(self):
        """ Vérifie si le serveur Ollama est en cours d'exécution sur le port spécifié. """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            result = sock.connect_ex(('localhost', int(self.port)))
            return result == 0  # Renvoie True si le port est ouvert

    @cond_decorator(builtins.__dict__.get('GUI_FLAG', True), ProgressNotification(_("Starting Server")))
    def _start_server(self):
        """ Démarre le serveur Ollama en arrière-plan. """
        try:
            subprocess.Popen(["ollama", "serve"])
            logging.info(_("Ollama starts with success."))
        except Exception as e:
            logging.error(_("Failed to start the Ollama server: %s"), str(e))
            raise RuntimeError(_("Failed to start the Ollama server"))
        
    def _stop_server(self):
        """Stop the Ollama server."""
        if not self._is_server_running():
            return
        
        try:
            # This is a placeholder command; replace it with the actual command to stop your server
            subprocess.run(["ollama", "stop"], check=True)
            logging.info("Ollama server stopped successfully.")
        except subprocess.CalledProcessError as e:
            logging.error("Failed to stop the Ollama server: %s", str(e))
            raise RuntimeError("Could not stop the Ollama server.")

    def _restart_server(self):
        """Restart the Ollama server."""

        if not self._is_server_running():
            return
        
        if self._is_server_running():
            logging.info("Stopping the Ollama server...")
            self._stop_server()  # Stop the server first
        
        logging.info("Starting the Ollama server...")
        self._start_server()  # Start it again

    def _get_models(self):
        # Commande pour lister les modèles disponibles localement
        cmd = ["ollama", "list"]

        try:
            # Exécuter la commande et capturer la sortie
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            
            # Affiche la liste des modèles disponibles localement
            return result.stdout
            
        except subprocess.CalledProcessError as e:
            logging.error("Erreur lors de l'exécution de la commande:", e)
            logging.error(e.stderr)

    @cond_decorator(builtins.__dict__.get('GUI_FLAG', True), ProgressNotification(_(f"Pulling process")))
    def _pull(self):
        try:
            # Commande pour effectuer le pull via la ligne de commande
            cmd = ["ollama", "pull", self.model_name]

             # Lancer la commande sans redirection
            result = subprocess.run(cmd, text=True, check=True)

            # Vérifier si le processus a réussi
            if result.returncode != 0:
                logging.error(f"Error while downloading model {self.model_name}: {result.stderr.strip()}")
                raise RuntimeError(f"Failed to download model {self.model_name}.")
            
        except subprocess.CalledProcessError as e:
            logging.error(f"Error while downloading model {self.model_name}: {e.stderr}")
            raise RuntimeError(f"Failed to download model {self.model_name}.")
        except Exception as e:
            logging.error(_("Failed to start the Ollama server: %s"), str(e))
            raise RuntimeError(_("Failed to start the Ollama server"))

    def _stop_server(self):
        """Stop the Ollama server."""
        if not self._is_server_running():
            return
        
        try:
            # This is a placeholder command; replace it with the actual command to stop your server
            subprocess.run(["ollama", "stop"], check=True)
            logging.info("Ollama server stopped successfully.")
        except subprocess.CalledProcessError as e:
            logging.error("Failed to stop the Ollama server: %s", str(e))
            raise RuntimeError("Could not stop the Ollama server.")

    def _restart_server(self):
        """Restart the Ollama server."""

        if not self._is_server_running():
            return
        
        if self._is_server_running():
            logging.info("Stopping the Ollama server...")
            self._stop_server()  # Stop the server first
        
        logging.info("Starting the Ollama server...")
        self._start_server()  # Start it again

    def _get_models(self):
        # Commande pour lister les modèles disponibles localement
        cmd = ["ollama", "list"]

        try:
            # Exécuter la commande et capturer la sortie
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            
            # Affiche la liste des modèles disponibles localement
            return result.stdout
            
        except subprocess.CalledProcessError as e:
            logging.error("Erreur lors de l'exécution de la commande:", e)
            logging.error(e.stderr)

    @cond_decorator(builtins.__dict__.get('GUI_FLAG', True), ProgressNotification(_(f"Pulling process")))
    def _pull(self):
        try:
            # Commande pour effectuer le pull via la ligne de commande
            cmd = ["ollama", "pull", self.model_name]

             # Lancer la commande sans redirection
            result = subprocess.run(cmd, text=True, check=True)

            # Vérifier si le processus a réussi
            if result.returncode != 0:
                logging.error(f"Error while downloading model {self.model_name}: {result.stderr.strip()}")
                raise RuntimeError(f"Failed to download model {self.model_name}.")
            
        except subprocess.CalledProcessError as e:
            logging.error(f"Error while downloading model {self.model_name}: {e.stderr}")
            raise RuntimeError(f"Failed to download model {self.model_name}.")
        except Exception as e:
            logging.error(f"Error while downloading model {self.model_name}: {e}")
            raise RuntimeError(f"Failed to download model {self.model_name}.")
        else:
            logging.info(f"Model '{self.model_name}' downloaded successfully.")

    def _ensure_model_downloaded(self):
        """Télécharge ou met à jour le modèle spécifié via Ollama."""
        
        if self.model_name in self.local_model:       
            logging.info(f"The model '{self.model_name}' is already downloaded and is ready to start.")
        else:
            logging.info(f"The model '{self.model_name}' is not downloaded. Starting pull...")
            if check_internet():
                self._pull()
            else:
                message = _("No internet connection. Please check your internet connection and try again.")
                wx.CallAfter(wx.MessageBox, message, _("Information"), wx.ICON_INFORMATION)
                logging.info(message)
    
    @BuzyCursorNotification
    def generate_output(self, prompt):
        """
        Génère une sortie en utilisant l'API Ollama basée sur le prompt donné.
        Vérifie d'abord si le serveur est en cours d'exécution, et le démarre si nécessaire.
        """
        # Check if the server is running before sending the prompt
        if not self._is_server_running():
            logging.info(_("The Ollama server is not active. Attempting to start..."))
            self._start_server()

        try:
            # Send the prompt to the Ollama server
            response = ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}]
            )
            return response['message']['content']
        except Exception as e:
            logging.error(_(f"Error while generating output: {e}"))
            return _(f"An error occurred while generating the output: {e}")

