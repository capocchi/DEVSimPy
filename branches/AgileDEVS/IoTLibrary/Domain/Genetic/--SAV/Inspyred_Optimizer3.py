from Domain.Genetic.Lib.SimpleAtomicModel import SimpleAtomicModel
from inspyred import ec
from inspyred.ec import terminators
from random import Random

class Inspyred_Optimizer3(SimpleAtomicModel):

    def __init__(self, seizeADN=2, seizePop=10):
        SimpleAtomicModel.__init__(self)
        self.state['MODE'] = 'INIT'
	self.seizeADN = seizeADN
        self.seizePop =seizePop
	
	#PARAMETRE 1er GENERATION
        self.generator = generator
	
	#PARAMETRE 2ieme GENERATION
        self.generatorFromExternalResults = generatorFromExternalResults
        self.evaluatorFromExternalResults = evaluatorFromExternalResults
	
	#PARAMETRE OBJET OPTIMISATION
	self.rand = Random()
	
        self.becomeActivate()
        print "OPTIMIZER : INITIALISATION TERMINEE"

#--------------------Fonction sortie------------------     
    def outputFnc(self):
        #GENERATION DUNE PREMIER POPULATION SANS ES
	if self.state['MODE'] == 'INIT':
            print "OPTIMIZER : ENVOIS DE LA POPULATION INITIALE"
	    self.pop = [generator(self.rand,self.seizeADN) for i in range(self.seizePop)]
            self.sendMessage(0, self.pop)

        #GENERATION DUNE NOUVELLE POPULATION AVEC ES
	elif self.state['MODE'] == "OPTIMIZING":
            ea = ec.GA(Random())
            ea.terminator = ec.terminators.evaluation_termination
            
	    print "OPTIMIZER : ITERATION DOPTIMISATION"
	    self.population = ea.evolve(generator=self.generatorFromExternalResults,
					evaluator=self.evaluatorFromExternalResults,
					pop_size=self.seizePop,
					maximize=False,
					bounder=ec.Bounder(-5.00, 5.00),
					max_evaluations=10,
					num_elites=1,
					populationSave=self.pop, #UTILE AU GENERATEUR
					simulationResult=self.simulationResults, #UTILE A LEVALUATEUR
					mutation_rate=0.5)

            self.pop = []
            for indiv in self.population:
                self.pop.append(indiv.candidate)
            self.sendMessage(0, self.pop)
	    
	    print "OPTIMIZER : LE MEILLEUR RESULTAT EST : ", max(self.population).fitness

#--------------------Fonction interne------------------
    def intTransition(self):	
        if self.state['MODE'] == 'INIT':
            self.state['MODE'] = "OPTIMIZING"
            print "OPTIMIZER : PASSAGE EN MODE OPTIMISATION"
            
        self.becomeDesactivate()
  
#--------------------Fonction entree------------------
    def extTransition(self):
        print "OPTIMIZER : RECEPTION RESULTATS"
	self.simulationResults = self.readMessage()
	self.becomeActivate()
        
#--------------------Fonction ToString------------
    def __str__(self):
        return "Inspyred_Optimizer3"

#-------------------------
#  UTILISATION 1 ITERATION
#-------------------------
def generator(random, taille):
    #Genere un code genetique dune taille definie
    solution = []
    for i in range(taille):
        solution.append(random.uniform(-5.00, 5.00))
    return solution

#------------------------------------
#  UTILISATION PROCESSUS OPTIMISATION
#------------------------------------
def generatorFromExternalResults(random, args):
    #Ce modele recupere la population qui a ete enregistree avant detre transmise au modele du problem (on lui ajoutera levaluation)
    return args['populationSave'].pop(0)
    
def evaluatorFromExternalResults(candidates, args):
    #Ce modele recupere les resultats qui ont ete transmis par le vrai evaluateur et les envois dans le processus d'optimisation
    return args['simulationResult']