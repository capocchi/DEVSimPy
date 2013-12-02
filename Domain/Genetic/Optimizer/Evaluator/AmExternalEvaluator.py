from Domain.Genetic.Lib.SimpleAtomicModel import SimpleAtomicModel
from Domain.Basic.Object import Message
import csv

class AmExternalEvaluator(SimpleAtomicModel):
    """
    This class allow a evaluation from external model such as WSN or GIS
    @author: Bastien POGGI
    @organization: University Of Corsica
    @contact: bpoggi@univ-corse.fr
    @since: 2012.03.29
    @version: 1.0
    """
#-----------------------------------------------------

    def __init__(self, listWeight=[1.0], mode="LOG"):
        SimpleAtomicModel.__init__(self)
        """
        @param listWeight: ponderation of each ports results
        """  
        #ATTRIBUTES
        self.dicoExternalResult = {} #keys are ports and values are received list evaluation
        self.listWeight = listWeight
        self.mode = mode
        
        #STATE MANAGEMENT
        self.becomeDesactivate()
        self.state['action'] = "WAIT POPULATION"
        
        self.logs = csv.writer(open('evalutor.csv','wb'),delimiter=":")


    def extTransition(self):
        #1- FIRST GENERATION
        if self.state['action'] == "WAIT POPULATION":
            self.showScreen("RECEPTION DUNE POPULATION")
            self.population = self.readMessage()
            self.becomeActivate()
                            
        #2- RESULT(S) RECEIVED
        if self.state['action'] == "WAIT RESPONSE":
            self.showScreen("RECEPTION DUNE REPONSE")
            for i in range(1,len(self.IPorts)):
                if self.peek(self.IPorts[i]):
                    msg = self.peek(self.IPorts[i])
                    results = msg.value[0]
                    self.dicoExternalResult[i] = results
                    
            self.becomeDesactivate()

            #All results are collected
            if len(self.dicoExternalResult) == len(self.IPorts) - 1:
                self.showScreen("All models results get")
                self.state['action'] = "EVALUATIONS FINISH"
                self.becomeActivate()

        
    def outputFnc(self):
        #1- EVAL REQUEST
        if self.state['action'] == "WAIT POPULATION":
            for i in range(len(self.OPorts)-1):
                self.showScreen("Send evaluations request " + str(i))
                self.sendMessage(i,self.population)

        #2- SEND EVAL COMPUTED
        if self.state['action'] == "EVALUATIONS FINISH":
            self.showScreen("Compute average fitness")
            self.computeAndSetPonderateEvaluation()
            
            self.showScreen("Eval process finish")
            self.sendMessage(len(self.OPorts)-1,self.population)


    def intTransition(self):
        if self.state['action'] == "WAIT POPULATION":
            self.state['action'] = "WAIT RESPONSE"
            self.showScreen("waiting responses")
        
        if self.state['action'] == "EVALUATIONS FINISH":
            self.resetParameters()
            self.state['action'] = "WAIT POPULATION"

        self.becomeDesactivate()


    def __str__(self):
        return "AmExternalEvaluator"


    def resetParameters(self):
        self.saveCSV()
        self.dicoExternalResult = {}
        self.population = []
        
    def saveCSV(self):
        listePonderateEvaluation = map(lambda indiv: indiv.evaluation,self.population.individuals)
        bestPonderateEvaluation = max(listePonderateEvaluation)
        
        bestIndice = listePonderateEvaluation.index(bestPonderateEvaluation)
        bestADN = self.population.individuals[bestIndice].ADN
        bestADN = map(lambda gene: (gene.lat, gene.lon),bestADN)
        
        listValuesBest = [bestADN, bestPonderateEvaluation]
        
        for listFitnessReceived in self.dicoExternalResult.values():
            listValuesBest.append(listFitnessReceived[bestIndice])
            
        self.logs.writerow(listValuesBest)


    def computeAndSetPonderateEvaluation(self):
        i = 0
        for individual in self.population.individuals:
            individualFitness = 0
            for key in self.dicoExternalResult.keys():
                individualFitness += self.dicoExternalResult[key][i] * self.listWeight[key-1] #The dico port debing at 1, 0 is the input population port, weight list debing at 0 so -1
            self.population.individuals[i].setEvaluation(individualFitness)
            i+=1