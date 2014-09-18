import random
# CREATION DUN INDIVIDU

class IndividualFactory:

    def __init__(self, seize, geneFactory):
        self.seize = seize
        self.geneFactory = geneFactory

    def makeIndividual(self):
        ADN = []
        for i in range(self.seize):
            ADN.append(self.geneFactory.makeGene())
        return Individual(ADN, self.geneFactory)

class Individual:

    def __init__(self, ADN, geneFactory, reproductor=False):
        self.ADN = ADN
        self.evaluation = 0
        self.reproductor = reproductor
        self.geneFactory = geneFactory

    def __str__(self):
        genome = ""
        for gene in self.ADN:
            genome += str(gene)
        return "%s-%s-%s \n" % (str(genome), self.evaluation, self.reproductor)

    def setEvaluation(self, evaluation):
        self.evaluation = evaluation

    def becomeReproductor(self):
        self.reproductor = True

    def mutateIndividual(self, percent):
        #Number gene to mutate
        numberGeneToMutate = len(self.ADN) * percent / 100
        
        #Compute the index list of mutate gene
        listIndexToUpdate = random.sample(range(len(self.ADN)), numberGeneToMutate)
        #print "The index of mutate gen is : ", listIndexToUpdate, "(", len(listIndexToUpdate), ")"
        
        for i in listIndexToUpdate:
            self.ADN[i] = self.geneFactory.makeGene()

