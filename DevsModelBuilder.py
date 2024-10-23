
from openai import OpenAI 
import os

class DevsModelBuilder:
    def __init__(self, api_key):
        self.api_key = api_key
        self.model_types = {
            "Générateur": self._example_generator,
            "Collecteur": self._example_collector,
            "Afficheur": self._example_viewer,
            "Défaut": self._example_generator
        }
        
    def _example_generator(self):
        return """
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
        """

    def _example_viewer(self):
        return """
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

    def _example_collector(self):
        return """
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
"""

    def create_model(self, model_name, num_inputs, num_outputs, model_type, prompt):
        """
        Crée un modèle DEVS en utilisant GPT-4 en fonction des informations fournies.
        
        Arguments :
        - model_name : nom du modèle à créer.
        - num_inputs : nombre d'entrées du modèle.
        - num_outputs : nombre de sorties du modèle.
        - model_type : type général du modèle (générateur, viewer, etc.).
        - prompt : prompt spécifique donné pour affiner la construction du modèle.

        Retourne : La description du modèle générée par GPT-4.
        """
        if model_type not in self.model_types:
            raise ValueError(f"Le type de modèle '{model_type}' n'est pas supporté.")

        # Exemple de construction de modèle pour le type spécifique
        example = self.model_types[model_type]()
        
        # Structure du prompt envoyé à GPT-4
        full_prompt = f"""
        Tu es un assistant expert en modélisation DEVS. Crée un modèle DEVS appelé '{model_name}'.
        Ce modèle a {num_inputs} entrées et {num_outputs} sorties.
        C'est un modèle de type '{model_type}'.
        Voici un exemple de modèle {model_type} :
        {example}

        N'inclue que le code du modèle, je ne veux pas de balise code du style ```python.
        Je ne veux pas de message expliquant quoi que ce soit juste le code.

        Détails supplémentaires :
        {prompt}
        """
        client = OpenAI(api_key=self.api_key)
        # Appel à GPT-4 pour générer le modèle
        try:
            completion = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert in DEVS modeling."},
                    {"role": "user", "content": full_prompt}
                ],
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Une erreur est survenue lors de la création du modèle : {e}"

    def add_model_type(self, model_type, example_function):
        """
        Ajoute un nouveau type de modèle avec un exemple spécifique.
        
        Arguments :
        - model_type : nom du nouveau type de modèle.
        - example_function : fonction retournant un exemple de ce type de modèle.
        """
        self.model_types[model_type] = example_function
