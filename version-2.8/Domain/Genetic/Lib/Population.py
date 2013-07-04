#CREATION DUN POPULATION

class PopulationFactory:


    def __init__(self, seize, individualFactory):
        self.seize = seize
        self.individualFactory = individualFactory

    def makePopulation(self):
        #print "*** Create Population***"
        population  = []
        for i in range(self.seize):
            population.append(self.individualFactory.makeIndividual())
        return Population(population)

class Population:


    def __init__(self, individuals):
        self.individuals = individuals

    def __str__(self):
        result = ""
        for individual in self.individuals:
            result += str(individual)
        return result

    def sortPopulation(self):
        self.individuals.sort(key = lambda indi: indi.evaluation)
        
    def clearSelection(self):
        for individual in self.individuals:
            individual.reproductor = False

    def integrateChildren(self, children):
        self.individuals = self.individuals[len(children):]
        self.individuals = children + self.individuals
