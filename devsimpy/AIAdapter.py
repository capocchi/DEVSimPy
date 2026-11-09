# -*- coding: utf-8 -*-  # noqa: UP009

"""
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
# TEST PART - invoque the correspond test file in strored in tests/
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GLOBAL VARIABLES AND FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
"""

import json
import logging
from abc import ABC, abstractmethod
import re
import socket
import subprocess
import builtins

try:
	from ollama import chat
except ImportError:
	pass

import wx
import os
import sys
import urllib.request
import gettext
import pathlib

from typing import Literal
from pydantic import BaseModel

from Decorators import cond_decorator
from Decorators import ProgressNotification
from Utilities import check_internet

_ = gettext.gettext

# Configuration de base du logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

ERR_MSG = _("Error while generating output")
AI_DIR = pathlib.Path(__file__).resolve().parent / "AI"

##########################################################
### Atomic Model JSON STRUCTURE
##########################################################
class State(BaseModel):
	name: str
	time: str | int | float  # noqa: FA102


class ModelProperty(BaseModel):
	name: str
	var_type: str
	value: str | float | int  # noqa: FA102
	description: str


class Function(BaseModel):
	description: str
	parameters: str


class Specifications(BaseModel):
	input_port: int
	output_port: int
	model_name: str
	model_type: Literal["Generator", "Collector", "Default"]
	states: list[State]
	model_description: str
	initial_state: State
	model_properties: list[ModelProperty]


class AtomicModel(BaseModel):
	specifications: Specifications
	init_function: Function
	ext_transition: Function
	int_transition: Function
	output_function: Function
	time_advance: Function


##########################################################
### BASE ADAPTER CLASS
##########################################################


class DevsAIAdapter(ABC):
	"""
	Parent class to interface the DEVS software with generative AI models.
	This class defines the base methods that child classes can override
	or use as is to interact with specific generative AI models.
	"""

	def __init__(self, parent=None):
		logging.info("DevsAIAdapter initialized.")  # noqa: LOG015
		self.base_prompt = self._load_base_prompt(
			AI_DIR / "DEVS_Explanation.txt"
		)

	def _load_base_prompt(self, file_path):
		"""
		Loads the base prompt from the DEVS model explanation file.
		"""
		try:
			with open(file_path, "r") as file:
				return file.read()
		except FileNotFoundError:
			logging.exception(f"File not found: {file_path}")  # noqa: LOG015
			raise

	def create_prompt(self, model_name, num_inputs, num_outputs, model_type, prompt):
		"""
		Creates a prompt to generate a DEVS model based on the type and the provided details.
		The prompt is based on instructions from the DEVS explanation file.
		"""
		logging.info("Creating prompt for model: %s, type: %s", model_name, model_type)  # noqa: LOG015

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
		logging.debug(f"Prompt created successfully for model: {model_name}")  # noqa: LOG015
		return full_prompt

	def modify_model_prompt(self, code, prompt):
		"""
		Generates a prompt to modify an existing DEVS model.
		Takes into account the model name, the current code, and additional details.
		"""
		logging.info("Modifying model")  # noqa: LOG015

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

		IMPORTANT: Preserve the header block at the beginning of the code (the block enclosed by 
		'-------------------------------------------------------------------------------'). This header is used by atomic and coupled models.
		The AI should generate new code without worrying about this header - it must include in its output
		the header from the reference code that was used as context.
		"""
		logging.debug("Modification prompt created for model.")  # noqa: LOG015
		return full_prompt

	def modify_model_part_prompt(self, code, prompt):
		"""
		Generates a prompt to modify a specific part of an existing DEVS model.
		Takes into account the model name, the current code, and details about the part to modify.
		"""
		logging.info("Modifying part of model.")  # noqa: LOG015

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
		logging.debug("Modification part prompt created for model")  # noqa: LOG015
		return full_prompt

	@abstractmethod
	def generate_output(
		self,
		prompt,
		system_prompt="",
		messages_history=None,
		output_format=None,
		**kwargs,
	):
		"""
		Abstract method to generate an output from the AI model.
		Child classes should override this method to specify how the generative AI produces outputs based on a prompt.
		`**kwargs` can include parameters such as the API key for models that require it.
		"""
		pass  # noqa: PIE790

	def generate_model_code(self, model_json=None, on_token=None, stop_event=None):
		"""Generates code for an atomic model function by function, using a JSON representation of the atomic model. Use the chat history to simulate a conversation between the llm and the user.

		The functions are : init (class init), intTransition, extTransition, outputFunction and timeAdvance()
		"""
		system_prompt = f"""You are an expert in DEVS modeling. You need to generate code for different functions of an atomic model.
		All the information needed is in the json. The fields 'input_ports' and 'output_ports' refer to the number of ports.

		Follow the DEVSimPy API and simulator contract below:
		{self.base_prompt}

		Use the 'specification' dictionary for basic informations on the model.
		The user will tell you which function to generate, and will give you indications to follow. Only output code for the function asked, without any textual explanations.

		Focus only on what is asked of you, ignore information unrelated to the model's specifications or the specific function needed. If the class has already been defined, there's no need to define it a second time.
		
		The model specification:
		{json.dumps(model_json["specifications"])}
		"""

		# store chat messages for current discussion
		messages_history = [{"role": "system", "content": system_prompt}]

		model_code = ""

		json_fields_functions = [
			"init_function",
			"ext_transition",
			"int_transition",
			"output_function",
			"time_advance",
		]

		# generates a response for every function
		for function_name in json_fields_functions:
			if stop_event is not None and stop_event.is_set():
				break
			if on_token is not None:
				on_token(f"\n[{function_name}]\n")
			function_guidelines = self._load_base_prompt(
				AI_DIR / "functions_prompt" / f"{function_name}.txt"
			)
			user_prompt = f"""Generate code for the {function_name} function.
			Use the following guidelines :
			{function_guidelines}
			and {model_json[function_name]} for specific details.
			"""

			messages_history.append({"role": "user", "content": user_prompt})
			response = self.generate_output(
				"", "", messages_history, on_token=on_token, stop_event=stop_event
			)

			# handle indentation and codeblock markers
			response = self.parse_codeblock_marker(response)
			if function_name != json_fields_functions[0]:
				response = self.indent_code(response)

			messages_history.append({"role": "assistant", "content": response})

			model_code += f"{response}\n"
			if stop_event is not None and stop_event.is_set():
				break
		# check indentation in code before return
		model_code = model_code.replace("    ", "\t")
		return model_code

	@abstractmethod
	def generate_model_json(self, prompt, on_token=None, stop_event=None):
		"""Abstract method used to generate a json representing an atomic model. The json describes the model specifications (states, properties) and its behaviors.
		Json generated with llm using structured outputs.

		Args:
			prompt (_type_): _description_
		"""
		pass  # noqa: PIE790

	def validate_model(self, model_name):
		"""
		Placeholder method for future implementation.
		"""
		logging.info("Validation not implemented for model: %s", model_name)  # noqa: LOG015
		pass  # noqa: PIE790

	def parse_codeblock_marker(self, code):
		"""Return code without codeblock marker."""
		pattern = r"^```(?:\w+)?\s*\n(.*?)(?=^```)```"
		match = re.search(
			pattern, code, re.DOTALL | re.MULTILINE
		)  # .DOTALL permet à `.` de correspondre aux sauts de ligne

		if match:
			# Si un bloc est trouvé, on retourne le code à l'intérieur des backticks
			return match.group(1)
		else:
			# Sinon, on retourne le code original sans modification
			return code

	def indent_code(self, code: str):
		"""Add a tab to every line in the provided code.
		Used to avoid indentation errors when generating a class function by function
		"""
		indented_lines = []
		for line in code.splitlines(True):
			indented_lines.append("\t")
			indented_lines.append(line)

		return "".join(indented_lines)


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

		selected_ia = getattr(builtins, "SELECTED_IA", "")

		# Vérifie si l'IA sélectionnée a changé
		if AdapterFactory._current_selected_ia != selected_ia:
			AdapterFactory._instance = None  # Réinitialise l'instance
			AdapterFactory._current_selected_ia = selected_ia  # Met à jour la sélection

		# Crée une nouvelle instance si nécessaire
		if AdapterFactory._instance is None:
			# Récupère les paramètres d'API et de port de PARAMS_IA

			params = params or {}
			api_key = params.get("CHATGPT_API_KEY")
			port = params.get("OLLAMA_PORT")

			# Validation pour ChatGPT
			if selected_ia == "ChatGPT":
				if not api_key:
					AdapterFactory._show_error(_("API key is required for ChatGPT."))
					return None
					# raise ValueError(_("API key is required for ChatGPT."))
				else:
					model_name = params.get("CHATGPT_MODEL", "gpt-4.1-nano")
					AdapterFactory._instance = ChatGPTDevsAdapter(
						parent=parent, api_key=api_key, model_name=model_name
					)

			# Validation pour Ollama
			elif selected_ia == "Ollama":
				if not port:
					AdapterFactory._show_error(_("Port is required for Ollama."))
					return None
					# raise ValueError(_("Port is required for Ollama."))
				else:
					model_name = params.get("OLLAMA_MODEL") if params else None
					if not model_name:
						model_name = "mistral"
					AdapterFactory._instance = OllamaDevsAdapter(
						parent=parent, port=port, model_name=model_name
					)
			elif selected_ia == "LM Studio":
				base_url = params.get("LMSTUDIO_BASE_URL", "http://localhost:1234/v1")
				model_name = params.get("LMSTUDIO_MODEL", "")
				if not model_name:
					AdapterFactory._show_error(_("Select an LM Studio model first."))
					return None
				AdapterFactory._instance = LMStudioDevsAdapter(
					base_url=base_url, model_name=model_name, parent=parent
				)
			else:
				AdapterFactory._show_error(_("No AI selected or unknown AI."))
				# raise ValueError(_("No AI selected or unknown AI."))

		return AdapterFactory._instance

	@staticmethod
	def reset_instance():
		"""Réinitialise manuellement l'instance et l'IA sélectionnée."""
		AdapterFactory._instance = None
		AdapterFactory._current_selected_ia = None

	@staticmethod
	def _show_error(message):
		"""Affiche un message d'erreur sous forme de toast avec wx."""
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

	def __init__(self, api_key=None, parent=None, model_name="gpt-4.1-nano"):
		super().__init__()
		# if not api_key:
		# raise ValueError(_("API key is required for ChatGPT."))
		self.api_key = api_key
		self.model_name = model_name
		self.wxparent = parent
		from openai import OpenAI

		self.api_client = OpenAI(api_key=self.api_key)  # Instancie le client API ici
		logging.info(_("ChatGPTDevsAdapter initialized with provided API key."))  # noqa: LOG015

	def get_available_models(self):
		"""Return chat-capable OpenAI model IDs available to this account."""
		prefixes = ("gpt-", "o1", "o3", "o4")
		return [
			model.id
			for model in self.api_client.models.list().data
			if model.id.startswith(prefixes)
		]

	def generate_model_json(self, prompt, on_token=None, stop_event=None):
		"""Generate a json representing an atomic model based on user's natural language description.
		Use openai chat API with structured output.
		Handle response to return the json as dict
		"""
		system_prompt = self._load_base_prompt(
			AI_DIR / "json_gen_prompt.txt"
		)
		try:
			system_prompt += (
				"\nReturn a single JSON object conforming to this schema:\n"
				+ json.dumps(AtomicModel.model_json_schema())
			)
			completion = self.api_client.chat.completions.create(
				model=self.model_name,
				messages=[
					{"role": "system", "content": system_prompt},
					{"role": "user", "content": prompt},
				],
				response_format={"type": "json_object"},
				stream=on_token is not None or stop_event is not None,
			)
			if on_token is not None or stop_event is not None:
				content_parts = []
				for chunk in completion:
					if stop_event is not None and stop_event.is_set():
						completion.close()
						break
					if not chunk.choices:
						continue
					content = chunk.choices[0].delta.content
					if content:
						content_parts.append(content)
						if on_token is not None:
							on_token(content)
				content = "".join(content_parts)
			else:
				content = completion.choices[0].message.content
			return AtomicModel.model_validate_json(content).model_dump()
		except ValueError as ve:
			logging.exception(_("Validation error"))  # noqa: LOG015
			return _(f"Validation error: {ve}")  # noqa: INT001

		except Exception as e:
			# Journalisation de l'erreur avec les détails de l'exception
			logging.exception(ERR_MSG)  # noqa: LOG015
			return _(f"An error occurred while generating the output: {e}")  # noqa: INT001

	def generate_output(
		self, prompt="", system_prompt="", messages_history=None, on_token=None, stop_event=None
	):
		"""
		Génère une sortie en utilisant l'API ChatGPT basée sur le prompt donné (génération unique) ou un historique de conversation.

		"""
		try:
			# Validation de la présence du prompt ou de l'historique
			if not prompt and not messages_history:
				raise ValueError("Prompt cannot be empty")

			# Envoi de la requête à l'API
			response = self.api_client.chat.completions.create(
				model=self.model_name,
				messages=messages_history
				if messages_history
				else [
					{"role": "system", "content": system_prompt},
					{"role": "user", "content": prompt},
				],
				stream=on_token is not None or stop_event is not None,
			)
			if on_token is not None or stop_event is not None:
				content_parts = []
				for chunk in response:
					if stop_event is not None and stop_event.is_set():
						response.close()
						break
					if not chunk.choices:
						continue
					content = chunk.choices[0].delta.content
					if content:
						content_parts.append(content)
						if on_token is not None:
							on_token(content)
				return "".join(content_parts)

			# Validation de la réponse
			if not hasattr(response, "choices") or not response.choices:
				logging.exception("No choices found in response.")  # noqa: LOG015
				return _("No response received from the AI model.")

			# Retourner le contenu du message
			return response.choices[0].message.content

		except ValueError as ve:
			logging.exception(_("Validation error"))  # noqa: LOG015
			return _(f"Validation error: {ve}")  # noqa: INT001

		except Exception as e:
			# Journalisation de l'erreur avec les détails de l'exception
			logging.exception(ERR_MSG)  # noqa: LOG015
			return _(f"An error occurred while generating the output: {e}")  # noqa: INT001


##########################################################
###
### OLLAMA
###
##########################################################
class OllamaDevsAdapter(DevsAIAdapter):
	"""
	Adaptateur spécifique pour Ollama, utilisé pour générer des modèles DEVS.
	"""

	def __init__(self, port="11434", model_name="qwen2.5-coder", parent=None):
		super().__init__()

		if not port:
			raise ValueError("Le port est requis pour Ollama.")

		### local copy
		self.port = port
		self.wxparent = parent
		self.model_name = model_name
		logging.info(_(f"OllamaDevsAdapter initialized with port {port} and model {model_name}."))  # noqa: INT001, LOG015

		# Vérification de l'installation d'Ollama
		if not self._is_ollama_installed():
			if check_internet():
				self._prompt_install_ollama()
			else:
				message = _(
					"No internet connection. Please check your internet connection and try again."
				)
				wx.CallAfter(wx.MessageBox, message, _("Information"), wx.ICON_INFORMATION)
				logging.info(message)  # noqa: LOG015
		else:
			# Vérification si le serveur est lancé au démarrage
			if not self._is_server_running():
				logging.info(_("The Ollama server is not running. Attempting to start..."))  # noqa: LOG015
				self._start_server()
			else:
				logging.info(_("The Ollama server is already running."))  # noqa: LOG015

			# Obtenir la liste des modèles téléchargés localement
			self.local_model = self.get_available_models()

			# Téléchargement du modèle spécifié
			self._ensure_model_downloaded()

	def _is_ollama_installed(self):
		"""Vérifie si Ollama est installé en cherchant son exécutable."""
		command = ["where", "ollama"] if sys.platform == "win32" else ["which", "ollama"]
		return subprocess.run(command, check=False, capture_output=True).returncode == 0

	def _prompt_install_ollama(self):
		"""Affiche une fenêtre `wx` pour proposer l'installation d'Ollama."""

		message = _("Ollama is not installed. Would you like to install it now?")
		dialog = wx.MessageDialog(None, message, _("Ollama install"), wx.YES_NO | wx.ICON_QUESTION)

		if dialog.ShowModal() == wx.ID_YES:
			logging.info(_("Starting the installation of Ollama..."))  # noqa: LOG015
			self._install_ollama()
		else:
			logging.exception(_("Ollama is required to run this class."))  # noqa: LOG015
			raise RuntimeError(_("Ollama is not installed and is required to run this class."))

		dialog.Destroy()

	@cond_decorator(getattr(builtins, "GUI_FLAG", True), ProgressNotification(_("Download")))
	def _install_ollama(self):
		"""Installe Ollama selon le système d'exploitation."""
		platform = sys.platform

		try:
			if platform == "darwin":  # macOS
				subprocess.run(
					"curl -O https://ollama.com/download/Ollama-darwin.zip && unzip Ollama-darwin.zip -d /usr/local/bin && rm Ollama-darwin.zip",
					shell=True,
					check=True,
				)
			elif platform.startswith("linux"):  # Linux
				subprocess.run(
					"curl -fsSL https://ollama.com/install.sh | sh", shell=True, check=True
				)
			elif platform == "win32":  # Windows
				ollama_path = os.path.join(
					os.environ["USERPROFILE"], "Downloads", "OllamaSetup.exe"
				)
				download_url = "https://ollama.com/download/OllamaSetup.exe"

				# Téléchargement avec message de chargement
				# self._show_download_message(download_url, ollama_path)
				# Effectue le téléchargement
				urllib.request.urlretrieve(download_url, ollama_path)

				# Exécution de l'installateur
				subprocess.run([ollama_path], check=True)

			logging.info(  # noqa: LOG015
				_("Ollama installation completed. Restart devsimpy and the terminal if necessary.")
			) 

		except subprocess.CalledProcessError:
			logging.exception(_("Error during Ollama installation"))  # noqa: LOG015
			raise RuntimeError(_("Ollama installation failed."))

	def _is_server_running(self):
		"""Vérifie si le serveur Ollama est en cours d'exécution sur le port spécifié."""
		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
			result = sock.connect_ex(("localhost", int(self.port)))
			return result == 0  # Renvoie True si le port est ouvert

	@cond_decorator(getattr(builtins, "GUI_FLAG", True), ProgressNotification(_("Starting Server")))
	def _start_server(self):
		"""Démarre le serveur Ollama en arrière-plan."""
		try:
			subprocess.Popen(["ollama", "serve"])
			logging.info(_("Ollama starts with success."))  # noqa: LOG015
		except Exception:
			logging.exception(_("Failed to start the Ollama server"))  # noqa: LOG015
			raise RuntimeError(_("Failed to start the Ollama server"))

	def _stop_server(self):
		"""Stop the Ollama server."""
		if not self._is_server_running():
			return

		try:
			# This is a placeholder command; replace it with the actual command to stop your server
			subprocess.run(["ollama", "stop"], check=True)
			logging.info("Ollama server stopped successfully.")  # noqa: LOG015
		except subprocess.CalledProcessError:
			logging.exception("Failed to stop the Ollama server")  # noqa: LOG015
			raise RuntimeError("Could not stop the Ollama server.")

	def _restart_server(self):
		"""Restart the Ollama server."""

		if not self._is_server_running():
			return

		if self._is_server_running():
			logging.info("Stopping the Ollama server...")  # noqa: LOG015
			self._stop_server()  # Stop the server first

		logging.info("Starting the Ollama server...")  # noqa: LOG015
		self._start_server()  # Start it again

	@staticmethod
	def get_available_models():
		# Commande pour lister les modèles disponibles localement
		cmd = ["ollama", "list"]

		try:
			logging.info(_("Start the command 'ollama list'..."))  # noqa: LOG015

			# Exécuter la commande et capturer la sortie
			result = subprocess.run(cmd, capture_output=True, text=True, check=True)

			models = []
			for line in result.stdout.splitlines():
				line = line.strip()
				if not line or line.lower().startswith("model"):
					continue
				parts = re.split(r"\s{2,}|\t", line)
				if parts:
					models.append(parts[0].strip())

			logging.info(_(f"Found Ollama models: {models}"))  # noqa: INT001, LOG015
			return models

		except (subprocess.CalledProcessError, FileNotFoundError):
			logging.exception("Erreur lors de l'exécution de la commande ollama list")  # noqa: LOG015
			return []

	@cond_decorator(getattr(builtins, "GUI_FLAG", True), ProgressNotification(_("Pulling process")))
	def _pull(self):
		try:
			# Commande pour effectuer le pull via la ligne de commande
			cmd = ["ollama", "pull", self.model_name]

			# Lancer la commande sans redirection
			result = subprocess.run(cmd, text=True, check=True)

			# Vérifier si le processus a réussi
			if result.returncode != 0:
				logging.exception(  # noqa: LOG015
					f"Error while downloading model {self.model_name}: {result.stderr.strip()}"
				)
				raise RuntimeError(f"Failed to download model {self.model_name}.")

		except subprocess.CalledProcessError:
			logging.exception(f"Error while downloading model {self.model_name}")  # noqa: LOG015
			raise RuntimeError(f"Failed to download model {self.model_name}.")
		except Exception:
			logging.exception(f"Error while downloading model {self.model_name}")  # noqa: LOG015
			raise RuntimeError(f"Failed to download model {self.model_name}.")
		else:
			logging.info(f"Model '{self.model_name}' downloaded successfully.")  # noqa: LOG015

	def _ensure_model_downloaded(self):
		"""Télécharge ou met à jour le modèle spécifié via Ollama."""

		if self.model_name in self.local_model:
			logging.info(  # noqa: LOG015
				f"The model '{self.model_name}' is already downloaded and is ready to start."
			)
		else:
			logging.info(f"The model '{self.model_name}' is not downloaded. Starting pull...")  # noqa: LOG015
			if check_internet():
				self._pull()
			else:
				message = _(
					"No internet connection. Please check your internet connection and try again."
				)
				wx.CallAfter(wx.MessageBox, message, _("Information"), wx.ICON_INFORMATION)
				logging.info(message)  # noqa: LOG015

	def generate_model_json(self, prompt, on_token=None, stop_event=None):
		"""Generate a json representing an atomic model based on user's natural language description.
		Use Ollama's API with structured output.
		Handle response to return the json as dict
		"""
		if not self._is_server_running():
			logging.info(_("The Ollama server is not active. Attempting to start..."))  # noqa: LOG015
			self._start_server()
		try:
			system_prompt = self._load_base_prompt(
					AI_DIR / "json_gen_prompt.txt"
			)
			# Send the prompt to the Ollama server
			# Sends the conversation history (if it exists) or the prompt
			response = chat(
				model=self.model_name,
				messages=[
					{"role": "system", "content": system_prompt},
					{"role": "user", "content": prompt},
				],
				format=AtomicModel.model_json_schema(),
				stream=on_token is not None or stop_event is not None,
			)
			if on_token is not None or stop_event is not None:
				content_parts = []
				for chunk in response:
					if stop_event is not None and stop_event.is_set():
						response.close()
						break
					content = chunk["message"]["content"]
					if content:
						content_parts.append(content)
						if on_token is not None:
							on_token(content)
				content = "".join(content_parts)
			else:
				content = response["message"]["content"]
			return json.loads(content)
		except Exception as e:
			logging.exception(ERR_MSG)  # noqa: LOG015
			return _(f"An error occurred while generating the output: {e}")  # noqa: INT001


	def generate_output(
		self, prompt, system_prompt="", messages_history=None, on_token=None, stop_event=None
	):
		"""
		Génère une sortie en utilisant l'API Ollama basée sur le prompt donné.
		Vérifie d'abord si le serveur est en cours d'exécution, et le démarre si nécessaire.
		"""
		# Check if the server is running before sending the prompt
		if not self._is_server_running():
			logging.info(_("The Ollama server is not active. Attempting to start..."))  # noqa: LOG015
			self._start_server()

		try:
			# Send the prompt to the Ollama server
			# Sends the conversation history (if it exists) or the prompt
			response = chat(
				model=self.model_name,
				messages=messages_history
				if messages_history
				else [
					{"role": "system", "content": system_prompt},
					{"role": "user", "content": prompt},
				],
				stream=on_token is not None or stop_event is not None,
			)
			if on_token is not None or stop_event is not None:
				content_parts = []
				for chunk in response:
					if stop_event is not None and stop_event.is_set():
						response.close()
						break
					content = chunk["message"]["content"]
					if content:
						content_parts.append(content)
						if on_token is not None:
							on_token(content)
				return "".join(content_parts)
			return response["message"]["content"]
		except Exception as e:
			logging.exception(ERR_MSG)  # noqa: LOG015
			return _(f"An error occurred while generating the output: {e}")  # noqa: INT001

##########################################################
###
### LM Studio
###
##########################################################
class LMStudioDevsAdapter(DevsAIAdapter):
	"""Adapter for LM Studio's OpenAI-compatible local server."""

	def __init__(self, base_url="http://localhost:1234/v1", model_name="", parent=None):
		super().__init__(parent)
		from openai import OpenAI

		self.base_url = base_url.rstrip("/")
		self.model_name = model_name.strip()
		self.wxparent = parent
		self.api_client = OpenAI(base_url=self.base_url, api_key="lm-studio")

	def get_available_models(self):
		"""Return the model IDs currently served by LM Studio."""
		return [model.id for model in self.api_client.models.list().data]

	def test_connection(self):
		"""Verify that LM Studio is reachable and the selected model is served."""
		models = self.get_available_models()
		if not models:
			raise RuntimeError("LM Studio is reachable, but no model is loaded.")
		if self.model_name not in models:
			raise RuntimeError(
				f"Model '{self.model_name}' is not available. Loaded models: {', '.join(models)}"
			)
		return True

	def generate_model_json(self, prompt, on_token=None, stop_event=None):
		system_prompt = self._load_base_prompt(AI_DIR / "json_gen_prompt.txt")
		system_prompt += (
			"\nReturn a single JSON object conforming to this schema:\n"
			+ json.dumps(AtomicModel.model_json_schema())
		)
		try:
			response = self.api_client.chat.completions.create(
				model=self.model_name,
				messages=[
					{"role": "system", "content": system_prompt},
					{"role": "user", "content": prompt},
				],
				response_format={"type": "json_object"},
				stream=on_token is not None or stop_event is not None,
			)
			if on_token is not None or stop_event is not None:
				content_parts = []
				for chunk in response:
					if stop_event is not None and stop_event.is_set():
						response.close()
						break
					if not chunk.choices:
						continue
					content = chunk.choices[0].delta.content
					if content:
						content_parts.append(content)
						if on_token is not None:
							on_token(content)
				content = "".join(content_parts)
			else:
				content = response.choices[0].message.content
			return AtomicModel.model_validate_json(content).model_dump()
		except Exception as error:
			logging.exception(ERR_MSG)  # noqa: LOG015
			return _(f"An error occurred while generating the output: {error}")  # noqa: INT001

	def generate_output(
		self, prompt="", system_prompt="", messages_history=None, on_token=None, stop_event=None
	):
		try:
			if not prompt and not messages_history:
				raise ValueError("Prompt cannot be empty")
			response = self.api_client.chat.completions.create(
				model=self.model_name,
				messages=messages_history
				if messages_history
				else [
					{"role": "system", "content": system_prompt},
					{"role": "user", "content": prompt},
				],
				stream=on_token is not None or stop_event is not None,
			)
			if on_token is not None or stop_event is not None:
				content_parts = []
				for chunk in response:
					if stop_event is not None and stop_event.is_set():
						response.close()
						break
					if not chunk.choices:
						continue
					content = chunk.choices[0].delta.content
					if content:
						content_parts.append(content)
						if on_token is not None:
							on_token(content)
				return "".join(content_parts)
			return response.choices[0].message.content
		except Exception as error:
			logging.exception(ERR_MSG)  # noqa: LOG015
			return _(f"An error occurred while generating the output: {error}")  # noqa: INT001
