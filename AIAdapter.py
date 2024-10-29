import logging
from abc import ABC, abstractmethod
from openai import OpenAI
from Decorators import BuzyCursorNotification, cond_decorator
import socket
import subprocess
import builtins
import wx
import ollama
import os
import sys
import urllib.request


import gettext
_ = gettext.gettext

# Configuration de base du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DevsAIAdapter(ABC):
    """
    Parent class to interface the DEVS software with generative AI models.
    This class defines the base methods that child classes can override
    or use as is to interact with specific generative AI models.
    """
    def __init__(self):
        self.model_types = ["Générateur", "Collecteur", "Afficheur", "Défaut"]
        logging.info(_("DevsAIAdapter initialized with model types: %s"), self.model_types)
    
    def _get_example(self, model_type):
        """
        Returns a model example based on the specified model type.
        If the model type is not recognized, returns a default example.
        """
        examples = {
            "Générateur": """
\"\"\" Definition of a DEVS Generator model \"\"\" 
# Model implementation 
# -*- coding: utf-8 -*-
        \"\"\"
-------------------------------------------------------------------------------
 Name:          		PoissonSensor.py
 Model description:     <description>
 Authors:       		domin
 Organization:  		<your organization>
 Current date & time:   2020-02-27 11:10:33.801210
 License:       		GPL v3.0
-------------------------------------------------------------------------------
\"\"\"


### Specific import ------------------------------------------------------------

from DomainInterface.DomainBehavior import DomainBehavior
from DomainInterface.Object import Message


### Model class ----------------------------------------------------------------
class PoissonSensor(DomainBehavior):
	''' DEVS Class for the model Capteur
	'''

	def __init__(self, minValue=0, maxValue=1, start=0, id = -1, n= 1000, mu=5):
		
		DomainBehavior.__init__(self)
		self.mu=mu
		self.n=n
		self.state = {'sigma':start}
		self.minValue = minValue
		self.maxValue = maxValue
		self.tempActuel = 0 
		self.tempDepart = 0
		self.tempReserve = 0
		self.jourActuel = 0
		self.lat = 0 
		self.lon = 0
		self.heureDepart = 0 
		self.occupation = 1
		self.id = id
		self.msg = Message(None, None)


	def outputFnc(self):
		numberMessage = random.randint(1, len(self.OPorts))  #nombre de message a envoye, inutile dans le cas ou il n'y a que l'une seul sortie 
		portsToSend = random.sample(self.OPorts, numberMessage)  # le port avec le nombre de message 
		self.generationValeurs()

		
		if (self.occupation == 1 ):
			for port in portsToSend:
				self.msg.value = [self.occupation, self.tempReserve, self.id, self.lat, self.lon, self.mu] #envoie un message en sortie contenant, le jour, l'heure, le temp de reservation et l'heure de depart		
				return self.poke(port, self.msg)
		else :
			for port in portsToSend:
				self.msg.value = [self.occupation,0, self.id, self.lat, self.lon, self.mu] #envoie un message en sortie contenant, le jour, l'heure, le temp de reservation et l'heure de depart
				return self.poke(port, self.msg)

	def intTransition(self): 
		self.getNextStatueChange(self.timeNext)
		#a decomenter pour le temps rÃ©elle 
		#time.sleep( int( self.state['sigma'] /60 ) )
		return self.state

	def __str__(self):
		return "ModelComplet"

	def timeAdvance(self):
		return self.state['sigma']

	def tempToHeure(self, temp):
		return str( int(((temp%1440)-((temp%1440) % 60))/60)) + 'h' + str(int(temp % 60)) #transphorme un entier en une string au format hh-mm ( ne compte pas les jours ) 

	def poisson(self, k,m):
		p=e**(-m)
		for i in range(0,k):
			p*=m/k
			k-=1
		return p

	def reverse(self, m):
		ph=random.random()
		k=0
		pc=self.poisson(k,m)
		while ph>=pc:
			k+=1
			pc+=self.poisson(k,m)
		return k

	def getRandomValuesFromPoisson(self,m,nb=0):
		return self.reverse(m) if nb==0 else [self.reverse(m) for i in range(nb)]

	def generationValeurs(self):
		self.msg.time = self.timeNext
		minute = self.timeToMinute(self.timeNext)  #recuperation minute
		hour = self.timeToHour(self.timeNext)      #recuperation heure
		time = self.timeNext

		if ( self.occupation == 0 ): #generation capteur occupe
			self.occupation = 1
			self.generationValeursOccupe()
		else: 						 #generation capteur libre
			self.occupation = 0
			self.generationValeursLibre()
		#self.tempReserve = random.randint( self.tempReserve - int(self.tempReserve *0.3),self.tempReserve + int(self.tempReserve *0.3) )


	def generationValeursOccupe(self):
		self.msg.time = self.timeNext
		minute = self.timeToMinute(self.timeNext)  #recuperation minute
		hour = self.timeToHour(self.timeNext)      #recuperation heure
		time = self.timeNext
		day = self.timeToDay(self.timeNext)

		self.tempReserve = self.getRandomValuesFromPoisson(self.mu,0)



	def generationValeursLibre(self):
		self.msg.time = self.timeNext
		minute = self.timeToMinute(self.timeNext)  #recuperation minute
		hour = self.timeToHour(self.timeNext)      #recuperation heure
		time = self.timeNext
		day = self.timeToDay(self.timeNext)

		self.tempReserve = self.getRandomValuesFromPoisson(30,0)

	def getNextStatueChange(self, time):
		minute = self.timeToMinute(time)  #recuperation minute
		hour = self.timeToHour(time)      #recuperation heure

		if ( self.occupation == 0 ):
			self.state['sigma'] = self.tempReserve	
		else:
			self.state['sigma'] = self.tempReserve	

	def timeToHour(self, time):
		return int(((time%1440)-((time%1440) % 60))/60)

	
	def timeToMinute(self, time):
		return int(time % 60)

	def timeToDay(self, time):
		day = int(time / 1440)%7
		return day
""",
            "Collecteur": """
\"\"\" Definition of a DEVS Collector model \"\"\" 
# Model implementation 
# -*- coding: utf-8 -*-
\"\"\"
-------------------------------------------------------------------------------
Name :          		To_Disk.py
Brief description : 	Atomic Model writing results in text file on the disk
Author(s) :     		Laurent CAPOCCHI <capocchi@univ-corse.fr>
Version :       		2.0
Last modified : 		29/10/20
GENERAL NOTES AND REMARKS:
GLOBAL VARIABLES AND FUNCTIONS:
-------------------------------------------------------------------------------
\"\"\"

from QuickScope import *
import random
from decimal import *
import os
import tempfile

def append_new_line(file_name, text_to_append):
    \"\"\"Append given text as a new line at the end of file\"\"\"
    # Open the file in append & read mode ('a+')
    with open(file_name, "a+") as file_object:
        # Move read cursor to the start of file.
        file_object.seek(0)
        # If file is not empty then append '\n'
        data = file_object.read(100)
        if len(data) > 0:
            file_object.write("\n")
        # Append text at the end of file
        file_object.write(text_to_append)

#  ================================================================    #
class To_Disk(QuickScope):
    \"\"\"	Atomic Model writing on the disk.\"\"\"

    ###
    def __init__(self, fileName = "result", eventAxis = False, comma = " ", ext = '.dat', col = 0):
        \"\"\" Constructor.

            @param fileName : Name of output fileName
            @param eventAxis : Flag to plot depending events axis
            @param comma : Comma symbol
            @param ext : Output file extension
            @param col : Considered column
        \"\"\"
        QuickScope.__init__(self)

        # Override default filename with a random temporary one if not specified
        fileName = fileName if fileName != 'result' else os.path.join(tempfile.gettempdir(), "result%d" % random.randint(1, 100000))

        # Local copies of parameters
        self.fileName = fileName
        self.comma = comma
        self.ext = ext
        self.col = col
        
        # Decimal precision
        getcontext().prec = 6

        # Last time value for event tracking
        self.last_time_value = {}

        self.buffer = {}

        # Event axis flag
        self.ea = eventAxis

        # Remove old files corresponding to 1000 presumed ports
        for np in range(1000):
            fn = "%s%d%s" % (self.fileName, np, self.ext)
            if os.path.exists(fn):
                os.remove(fn)
    ###
    def extTransition(self, *args):
        \"\"\"
        External transition function
        \"\"\"
        n = len(self.IPorts)

        for np in range(n):
            if hasattr(self, 'peek'):
                msg = self.peek(self.IPorts[np])
            else:
                inputs = args[0]
                msg = inputs.get(self.IPorts[np])

            fn = "%s%d%s" % (self.fileName, np, self.ext)

            if self.timeLast == 0 and self.timeNext == INFINITY:
                self.last_time_value[fn] = 0.0

            if fn not in list(self.buffer.keys()):
                self.buffer[fn] = 0.0

            if msg:
                if self.ea:
                    self.ea += 1
                    t = self.ea
                    self.last_time_value.update({fn: -1})
                else:
                    if fn not in self.last_time_value:
                        self.last_time_value.update({fn: 1})

                    if hasattr(self, 'peek'):
                        t = Decimal(str(float(msg.time)))
                    else:
                        t = Decimal(str(float(msg[-1][0])))
                
                val = msg.value[self.col] if hasattr(self, 'peek') else msg[0][self.col]
                
                if isinstance(val, (int, float)):
                    v = Decimal(str(float(val)))
                else:
                    v = val
                
                if t != self.last_time_value[fn]:
                    append_new_line(fn, "%s%s%s" % (self.last_time_value[fn], self.comma, self.buffer[fn]))
                    self.last_time_value[fn] = t
                
                self.buffer[fn] = v
                
                del msg

        self.state["sigma"] = 0
        return self.state

    def finish(self, msg):
        n = len(self.IPorts)
        for np in range(n):
            fn = "%s%d%s" % (self.fileName, np, self.ext)
            if fn in self.last_time_value and fn in self.buffer:
                append_new_line(fn, "%s%s%s" % (self.last_time_value[fn], self.comma, self.buffer[fn]))

    ###
    def __str__(self):
        return "To_Disk"
""",
            "Afficheur": """
\"\"\" Definition of a DEVS Viewer model \"\"\" 
# Model implementation 
# -*- coding: utf-8 -*-
\"\"\"
Name : MessagesCollector.py 
Brief descritpion : collect to disk received messages 
Author(s) : Laurent CAPOCCHI (capocchi@univ-corse.fr)
Version : 1.0                                        
Last modified : 26/10/20
GENERAL NOTES AND REMARKS:
GLOBAL VARIABLES AND FUNCTIONS:
\"\"\"

### just for python 2.5

import os
import random
import tempfile

from DomainInterface.DomainBehavior import DomainBehavior

#  ================================================================    #
class MessagesCollector(DomainBehavior):
    \"\"\"	Messages Collector
    \"\"\"

    ###
    def __init__(self, fileName = "result", ext = '.dat', comma = ""):
        \"\"\" Constructor.
        
            @param fileName : name of output fileName
            @param ext : output file extension
            @param comma : comma separated
        \"\"\"
        DomainBehavior.__init__(self)

        # Override default filename with a random temporary one if not specified
        fileName = fileName if fileName != "result" else os.path.join(tempfile.gettempdir(),"result%d"%random.randint(1,100000))

        # Local copies of parameters
        self.fileName = fileName
        self.ext = ext
        self.comma = comma

        self.initPhase('IDLE', INFINITY)
        
        for np in range(10000):
            fn = "%s%d%s" % (self.fileName, np, self.ext)
            if os.path.exists(fn):
                os.remove(fn)
    ###
    def extTransition(self, *args):
        \"\"\"
        External transition function
        \"\"\"
        
        for port in self.IPorts:
            # Adapted with PyPDEVS
            msg = self.peek(port, *args)
            np = self.getPortId(port)

            if msg:
                # Filename
                fn = "%s%s%s" % (self.fileName, str(np), self.ext)
                
                with open(fn, 'a') as f:
                    f.write("%s\n" % (str(msg)))
                del msg

        self.holdIn('ACTIF', 0.0)

        return self.getState()
        
    ###
    def intTransition(self):
        self.passivateIn('IDLE')
        return self.getState()
    
    ###
    def timeAdvance(self):
        return self.getSigma()
    
    ###
    def __str__(self):
        return "MessagesCollector"
"""
        }
        logging.debug(_("Retrieved example for model type: %s"), model_type)
        return examples.get(model_type, examples["Générateur"])
    
    def create_prompt(self, model_name, num_inputs, num_outputs, model_type, prompt):
        """
        Creates a prompt to generate a DEVS model based on the type and the provided details.
        Uses a default generative DEVS model example if the type is not found.
        """
        if model_type not in self.model_types:
            logging.error(_("Invalid model type: %s"), model_type)
            raise ValueError(_(f"Invalid model type '{model_type}'. Available types: {self.model_types}"))
        
        logging.info(_("Creating prompt for model: %s, type: %s"), model_name, model_type)
        example = self._get_example(model_type)
        
        # Constructing the prompt for the AI
        full_prompt = f"""
        You are an expert in DEVS modeling. Create a DEVS model called '{model_name}'.
        This model has {num_inputs} inputs and {num_outputs} outputs.
        It is a '{model_type}' type model.
        Here is an example of a {model_type} model:
        {example}

        Include only the model code. I do not want any code block markers like ```python.
        Do not provide any explanations, only the code.

        Additional details:
        {prompt}
        """
        logging.debug(_("Prompt created successfully for model: %s"), model_name)
        return full_prompt

    def modify_model_prompt(self, code, prompt):
        """
        Generates a prompt to modify an existing DEVS model.
        Takes into account the model name, the current code, and additional details.
        """
        logging.info(_("Modifying model"))
        
        # Constructing the prompt for the AI
        full_prompt = f"""
        You are an expert in DEVS modeling. You need to modify a DEVS model.
        Here is the current model code:
        {code}

        Here are the specific details to modify the model:
        {prompt}

        Include only the modified model code. I do not want any code block markers like ```python.
        Do not provide any explanations, only the code.
        """
        logging.debug(_("Modification prompt created for model."))
        return full_prompt
    
    def modify_model_part_prompt(self, code, prompt):
        """
        Generates a prompt to modify a specific part of an existing DEVS model.
        Takes into account the model name, the current code, and details about the part to modify.
        """
        logging.info(_("Modifying part of model."))
        
        # Constructing the prompt for the AI
        full_prompt = f"""
        You are an expert in DEVS modeling. You need to modify a specific part of a DEVS model'.
        Here is the current model code in between bracket : <{code}>
        Here are the specific details to modify this part of the model:
        {prompt}

        Include only the code of the modified part of the model. I do not want any code block markers like ```python.
        Do not provide any explanations, only the code. Keep the indentation, it is really important.
        """
        logging.debug(_("Modification part prompt created for model"))
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
        logging.info(_("Validation not implemented for model: %s", model_name))
        pass

class ChatGPTDevsAdapter(DevsAIAdapter):
    """
    Adaptateur spécifique pour ChatGPT, utilisant GPT-4 pour générer des modèles DEVS.
    """

    def __init__(self, api_key):
        super().__init__()
        if not api_key:
            raise ValueError(_("API key is required for ChatGPT."))
        self.api_key = api_key
        self.api_client = OpenAI(api_key=self.api_key)  # Instancie le client API ici
        logging.info(_("ChatGPTDevsAdapter initialized with provided API key."))

    def generate_output(self, prompt):
        """
        Génère une sortie en utilisant l'API ChatGPT basée sur le prompt donné.
        """
        try:
            response = self.api_client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert in DEVS modeling."},
                    {"role": "user", "content": prompt}
                ],
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.error(__("Error while generating output: %s", str(e)))
            return _(f"An error occurred while generating the output: {e}")

class OllamaDevsAdapter(DevsAIAdapter):
    """
    Adaptateur spécifique pour Ollama, utilisé pour générer des modèles DEVS.
    """

    def __init__(self, port, model_name='llama3.1'):
        super().__init__()

        if not port:
            raise ValueError("Le port est requis pour Ollama.")
        
        ### local copy
        self.port = port
        self.model_name = model_name
        # logging.info(_(f"OllamaDevsAdapter initialized with port {port} and model {model_name}."))

        # Vérification de l'installation d'Ollama
        if not self._is_ollama_installed():
            self._prompt_install_ollama()

        # Vérification si le serveur est lancé au démarrage
        if not self._is_server_running():
            logging.info(_("The Ollama server is not running. Attempting to start..."))
            self._start_server()
        else:
            logging.info(_("The Ollama server is already running."))

        # Téléchargement du modèle spécifié
        self._ensure_model_downloaded()

        # Restart the server after loading the model
        # logging.info(_("Restarting the Ollama server to load the new model..."))
        # self._restart_server()  # Ensure you implement this method

    def _is_ollama_installed(self):
        """ Vérifie si Ollama est installé en cherchant son exécutable. """
        command = ["where", "ollama"] if sys.platform == "win32" else ["which", "ollama"]
        return subprocess.run(command, capture_output=True).returncode == 0

    def _prompt_install_ollama(self):
        """ Affiche une fenêtre `wx` pour proposer l'installation d'Ollama. """
        # app = wx.App(False)
        message = _("Ollama is not installed. Would you like to install it now?")
        dialog = wx.MessageDialog(None, message, _("Ollama install"), wx.YES_NO | wx.ICON_QUESTION)
        
        if dialog.ShowModal() == wx.ID_YES:
            logging.info(_("Starting the installation of Ollama..."))
            self._install_ollama()
        else:
            logging.error(_("Ollama is required to run this class."))
            raise RuntimeError(_("Ollama is not installed and is required to run this class."))
                
        dialog.Destroy()
        # app.MainLoop()

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
                self._show_download_message(download_url, ollama_path)
                
                # Exécution de l'installateur
                subprocess.run([ollama_path], check=True)

            logging.info(_("Ollama installation completed. Restart devsimpy and the terminal if necessary."))

        except subprocess.CalledProcessError as e:
            logging.error(_("Error during Ollama installation: %s"), e)
            raise RuntimeError(_("Ollama installation failed."))

    def _show_download_message(self, url, dest_path):
        """Affiche une fenêtre wx avec le message de téléchargement sans interférer avec l'application wx existante."""
        frame = wx.Frame(None, -1, _("Download"), size=(500, 100))
        panel = wx.Panel(frame, -1)
        
        text = wx.StaticText(panel, -1, _("Downloading..."), pos=(50, 20))
        font = text.GetFont()
        font.PointSize += 2
        font = font.Bold()
        text.SetFont(font)
        
        frame.Centre()
        frame.Show()

        # Effectue le téléchargement
        urllib.request.urlretrieve(url, dest_path)

        # Ferme la fenêtre une fois le téléchargement terminé
        frame.Close()

    def _is_server_running(self):
        """ Vérifie si le serveur Ollama est en cours d'exécution sur le port spécifié. """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            result = sock.connect_ex(('localhost', int(self.port)))
            return result == 0  # Renvoie True si le port est ouvert

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

    def _ensure_model_downloaded(self):
        """Télécharge ou met à jour le modèle spécifié via Ollama."""

        try:
            logging.info(_(f"Downloading model {self.model_name} if necessary..."))
            ollama.pull(self.model_name)
            logging.info(_(f"Model {self.model_name} downloaded successfully."))
        except Exception as e:
            logging.error(_(f"Error while downloading model {self.model_name}: {e}"))
            raise RuntimeError(_(f"Failed to download model {self.model_name}."))

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
            logging.error(_("Error while generating output: %s", str(e)))
            return _(f"An error occurred while generating the output: {e}")

class AdapterFactory:
    _instance = None
    _current_selected_ia = None  # Suivi de l'état actuel de l'IA sélectionnée

    @staticmethod
    def get_adapter_instance(params=None):
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
                    raise ValueError(_("API key is required for ChatGPT."))
                AdapterFactory._instance = ChatGPTDevsAdapter(api_key)

            # Validation pour Ollama
            elif selected_ia == "Ollama":
                if not port:
                    AdapterFactory._show_error(_("Port is required for Ollama."))
                    raise ValueError(_("Port is required for Ollama."))
                AdapterFactory._instance = OllamaDevsAdapter(port)

            else:
                AdapterFactory._show_error(_("No AI selected or unknown AI."))
                raise ValueError(_("No AI selected or unknown AI."))

        return AdapterFactory._instance

    @staticmethod
    def reset_instance():
        """ Réinitialise manuellement l'instance et l'IA sélectionnée. """
        AdapterFactory._instance = None
        AdapterFactory._current_selected_ia = None

    @staticmethod
    def _show_error(message):
        """ Affiche un message d'erreur sous forme de toast avec wx. """
        app = wx.GetApp()
        if app:
            wx.CallAfter(wx.MessageBox, message, _("Error"), wx.ICON_ERROR)