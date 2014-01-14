#MODULES DEVS
from Domain.Genetic.Lib.SimpleAtomicModel import SimpleAtomicModel

class AMclassiqueMutator(SimpleAtomicModel):

#-----------------------------------------------------

    def __init__(self, mutationPercent=15,mutationTotal=False, mode="LOG"):
        SimpleAtomicModel.__init__(self)
        self.mode = mode
        self.mutationPercent = mutationPercent
        self.mutationTotal = mutationTotal

        self.becomeDesactivate()

#-----------------------------------------------------

    def extTransition(self):
        self.showScreen("RECEPTION DUNE POPULATION")
        self.population = self.readMessage()
        self.makeMutationProcess() #MAKE MUTATION ON POPULATION
        
        self.becomeActivate()

#-----------------------------------------------------

    def outputFnc(self):
        self.showScreen("ENVOIS DE LA NOUVELLE POPULATION MUTEE")
        self.sendMessage(0,self.population)

#-----------------------------------------------------

    def intTransition(self):
        self.becomeDesactivate()

#-----------------------------------------------------

    def __str__(self):
        return "AMclassiqueMutator"

#-----------------------------------------------------

#GESTION DE LA MUTATION

    def makeMutationProcess(self):
        for individual in self.population.individuals:
            if self.mutationTotal == 1:
                individual.mutateIndividual(self.mutationPercent)
            else:
                if individual.reproductor == False:
                    individual.mutateIndividual(self.mutationPercent)

                

