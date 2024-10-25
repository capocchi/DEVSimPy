import logging
from abc import ABC, abstractmethod
from openai import OpenAI
from Decorators import BuzyCursorNotification, cond_decorator

import builtins
import wx

import gettext
_ = gettext.gettext

# Configuration de base du logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

class DevsAIAdapter(ABC):
    """
    Parent class to interface the DEVS software with generative AI models.
    This class defines the base methods that child classes can override
    or use as is to interact with specific generative AI models.
    """
    def __init__(self):
        self.model_types = ["Générateur", "Collecteur", "Afficheur", "Défaut"]
        logging.info("DevsAIAdapter initialized with model types: %s", self.model_types)
    
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
        logging.debug("Retrieved example for model type: %s", model_type)
        return examples.get(model_type, examples["Générateur"])
    
    def create_prompt(self, model_name, num_inputs, num_outputs, model_type, prompt):
        """
        Creates a prompt to generate a DEVS model based on the type and the provided details.
        Uses a default generative DEVS model example if the type is not found.
        """
        if model_type not in self.model_types:
            logging.error("Invalid model type: %s", model_type)
            raise ValueError(f"Invalid model type '{model_type}'. Available types: {self.model_types}")
        
        logging.info("Creating prompt for model: %s, type: %s", model_name, model_type)
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

        Here are the specific details to modify the model:
        {prompt}

        Include only the modified model code. I do not want any code block markers like ```python.
        Do not provide any explanations, only the code.
        """
        logging.debug("Modification prompt created for model")
        return full_prompt
    
    def modify_model_part_prompt(self, code, prompt):
        """
        Generates a prompt to modify a specific part of an existing DEVS model.
        Takes into account the model name, the current code, and details about the part to modify.
        """
        logging.info("Modifying part of model")
        
        # Constructing the prompt for the AI
        full_prompt = f"""
        You are an expert in DEVS modeling. You need to modify a specific part of a DEVS model'.
        Here is the current model code in between bracket : <{code}>
        Here are the specific details to modify this part of the model:
        {prompt}

        Include only the code of the modified part of the model. I do not want any code block markers like ```python.
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

class ChatGPTDevsAdapter(DevsAIAdapter):
    """
    Child class of DevsAIAdapter that uses ChatGPT (GPT-4) to generate DEVS models.
    """

    #@cond_decorator(builtins.__dict__.get('GUI_FLAG', True), BuzyCursorNotification) le cond fait suater le kwargs laurent, on verra plus tard
    def generate_output(self, prompt, **kwargs):
        """
        Generates an output using the ChatGPT API based on the given prompt.
        Expects an 'api_key' argument in **kwargs.
        """
        api_key = kwargs.get('api_key')
        if not api_key:
            raise ValueError("API key is required for ChatGPT.")

        api_client = OpenAI(api_key=api_key)
        try:
            response = api_client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert in DEVS modeling."},
                    {"role": "user", "content": prompt}
                ],
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.error("Error generating output: %s", str(e))
            return f"An error occurred while generating the output: {e}"


class OllamaDevsAdapter(DevsAIAdapter):
    """
    Child class of DevsAIAdapter that uses Ollama to generate DEVS models.
    """

    #@cond_decorator(builtins.__dict__.get('GUI_FLAG', True), BuzyCursorNotification) le cond fait suater le kwargs laurent, on verra plus tard
    def generate_output(self, prompt, **kwargs):
        """
        Generates an output using the Ollama API based on the given prompt.
        No API key is needed.
        """
        pass
