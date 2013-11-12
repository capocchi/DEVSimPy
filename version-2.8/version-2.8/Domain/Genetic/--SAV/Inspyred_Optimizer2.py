from Domain.Genetic.Lib.SimpleAtomicModel import SimpleAtomicModel
from inspyred import ec
from inspyred.ec import terminators
from random import Random

class Inspyred_Optimizer2(SimpleAtomicModel):

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


#--------------------Fonction sortie------------------     
    def outputFnc(self):
        #GENERATION DUNE PREMIER POPULATION SANS ES
	if self.state['MODE'] == 'INIT':
	    self.pop = [generator(self.rand,self.seizeADN) for i in range(self.seizePop)]
            self.sendMessage(0, self.pop)

        #GENERATION DUNE NOUVELLE POPULATION AVEC ES
	elif self.state['MODE'] == "OPTIMIZING":
            es = ec.ES(self.rand)
	    self.population = es.evolve(generator=self.generatorFromExternalResults,
					evaluator=self.evaluatorFromExternalResults,
					pop_size=self.seizePop,
					maximize=False,
					bounder=ec.Bounder(-5.00, 5.00),
					max_evaluations=1,
                                        populationSave=self.pop, #UTILE AU GENERATEUR
                                        simulationResult=self.simulationResults, #UTILE A LEVALUATEUR
					mutation_rate=0.5)
            print self.population
            #TRADUCTION (CAR [x1, x2] donne [x1, x2, z1,z2] je ne sais pas a quoi ca correspond)
            self.pop = []
            coupure = len(self.population[0].candidate)/2
            for indiv in self.population:
                self.pop.append(indiv.candidate[:coupure])
            self.sendMessage(0, self.pop)

#--------------------Fonction interne------------------
    def intTransition(self):	
        if self.state['MODE'] == 'INIT':
            self.state['MODE'] = "OPTIMIZING"
        self.becomeDesactivate()
  
#--------------------Fonction entree------------------
    def extTransition(self):
	print "****************************************"
        print "OPTIMIZER : RECEPTION RESULTATS"
	self.simulationResults = self.readMessage()
        print self.simulationResults
	self.becomeActivate()
        
#--------------------Fonction ToString------------
    def __str__(self):
        return "Inspyred_Optimizer2"

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
    #Ce modele recupere la population qui a ete enregistree avant detre transmise au modele du problem
    return args['populationSave'].pop(0)
    
def evaluatorFromExternalResults(population, args):
    #Ce modele recupere les resultats qui ont ete transmis par le vrai evaluateur et les envois dans le processus d'optimisation
    return args['simulationResult']