from Domain.Genetic.Lib.SimpleAtomicModel import SimpleAtomicModel
from inspyred import ec
from inspyred.ec import terminators
from random import Random

import time

class Inspyred_Optimizer(SimpleAtomicModel):

    def __init__(self, n=2):
        SimpleAtomicModel.__init__(self)
        self.state['MODE'] = 'INIT'
	self.n = 2
	
	#PARAMETRE 1er GENERATION
        self.generator = generator
	self.evaluator = evaluator
	
	#PARAMETRE 2ieme GENERATION
        self.generatorFromExternalResults = generatorFromExternalResults
        self.evaluatorFromExternalResults = evaluatorFromExternalResults
	
	#PARAMETRE OBJET OPTIMISATION
	rand = Random()
	self.es = ec.ES(rand)
	
        self.becomeActivate()

#--------------------Fonction entree------------------
    def extTransition(self):
	print "****************************************"
        print "OPTIMIZER : RECEPTION RESULTATS"
	self.simulationResults = self.readMessage()
	print self.simulationResults
	self.becomeActivate()

#--------------------Fonction sortie------------------     
    def outputFnc(self):
	if self.state['MODE'] == 'INIT':
	    print "OPTIMIZER : CALCUL 1er SORTIE"
	    self.population = self.es.evolve(generator=self.generator,
					evaluator=self.evaluator,
					pop_size=self.n,
					maximize=False,
					bounder=ec.Bounder(-5.00, 5.00),
					max_evaluations=1,
					mutation_rate=0.5)
	    print "OPTIMIZER : LA POPULATION EST \n",self.population
	
	elif self.state['MODE'] == "OPTIMIZING":
	    print "OPTIMIZER : CALCUL SORTIE SUIVANTE"
	    self.population = self.es.evolve(generator=self.generatorFromExternalResults,
					     populationSave=self.populationSave, #UTILE AU GENERATEUR
					    evaluator=self.evaluatorFromExternalResults,
					    simulationResult=self.simulationResults, #UTILE A LEVALUATEUR
					    pop_size=self.n,
					    maximize=False,
					    bounder=ec.Bounder(-5.00, 5.00),
					    max_evaluations=1,
					    mutation_rate=0.5)
	    
	print "OPTIMIZER : ENVOI DE LA SORTIE"    
	self.populationSave = self.population #SAUVEGARDE DE LA POP ENVOYEE QUI SERA ASSOCIEE AUX RESULTATS OBTENUS
	
	####DEBUT TRADUCTION POUR MODELE EXTERNE
	pop = []
	coupure = len(self.populationSave[0].candidate)/2
	for indiv in self.populationSave:
	    pop.append(indiv.candidate[:coupure])
	print pop
	self.sendMessage(0, pop)

#--------------------Fonction interne------------------
    def intTransition(self):	
        if self.state['MODE'] == 'INIT':
            self.state['MODE'] = "OPTIMIZING"
        self.becomeDesactivate()

#--------------------Fonction ToString------------
    def __str__(self):
        return "Inspyred_Optimizer"

#-------------------------
#  UTILISATION 1 ITERATION
#-------------------------
def generator(random, args):
    #Genere un code genetique dune taille definie
    solution = []
    for i in range(2):
        solution.append(random.uniform(-5.00, 5.00))
    return solution

def evaluator(population, args):
    #Genere une liste de resultat neutres (le processus doptimisation debutera literation suivante)
    evaluations = []
    for p in population:
        evaluations.append(0.0)
    return evaluations

#------------------------------------
#  UTILISATION PROCESSUS OPTIMISATION
#------------------------------------
def generatorFromExternalResults(random, args):
    #Ce modele recupere la population qui a ete enregistree avant detre transmise au modele du problem
    coupure = len(args['populationSave'][0].candidate)/2
    val = args['populationSave'][0].candidate[:coupure]
    del args['populationSave'][0]
    return val
    
def evaluatorFromExternalResults(population, args):
    #Ce modele recupere les resultats qui ont ete transmis par le vrai evaluateur et les envois dans le processus d'optimisation
    return args['simulationResult']