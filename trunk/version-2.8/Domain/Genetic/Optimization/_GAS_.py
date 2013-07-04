import random

class GAs:
    
    #Le constructeur doit revevoir les different objets qui eux meme on comme attributs le GAs.
    
    def __init__(self, numberSolutions=50, seizeSolution=5):
        #Solutions
        self.solutions = []
        self.numberSolutions = numberSolutions
        self.seizeSolution = seizeSolution
    
#         #Fitness History
#         self.minFitness = None
#         self.avgFitness = None
#         self.middleFitness = None
#         self.maxFitness = None
#         
#         #Solutions History
#         self.worst = None
#         self.best = None
#         self.avg = None
#         self.middle = None
#         
#     #Fitness History
#     def getBestFitness(self):
#         return self.getBest().fitness
#         
#     def getWorstFitness(self):
#         return self.getWorst().fitness
#         
#     #Solutions History
#     def getBest(self):
#         return self.solutions[len(self.solutions)-1]
#         
#     def getWorst(self):
#         return self.solutions[0]
#         
#     def getMiddle(self):
#         return self.solutions[len(self.solutions)/2]
    
    #Autres    
    def __str__(self):
        result = ""
        for s in self.solutions:
            result = result + str(s) + "\n"
        return result
        
        
        
#---------------------------------------------------------------Generators
class Generator:
    
    def __init__(self, gas):
        self.myGAs = gas
        
    def generate():
        pass
        
class GeneratorCoordinates(Generator):
    
    def __init__(self,
                gas,
                minLatCoordinate, 
                maxLatCoordinate, 
                minLonCoordinate, 
                maxLonCoordinate, 
                numberSolutions, 
                seizeSolution):
                    
        Generator.__init__(self, gas)
        self.minLatCoordinate = minLatCoordinate
        self.maxLatCoordinate = maxLatCoordinate
        self.minLonCoordinate = minLonCoordinate
        self.maxLonCoordinate = maxLonCoordinate
        self.numberSolutions = numberSolutions
        self.seizeSolution = seizeSolution
        
    def generate(self):
        generatedSolutions = []
        for i in xrange(self.numberSolutions):
            ADN = []
            for j in xrange(self.seizeSolution):
                lat = random.randint(self.minLatCoordinate, self.maxLatCoordinate)
                lon = random.randint(self.minLonCoordinate, self.maxLonCoordinate)
                ADN.append((lat,lon))
            solution = Solution(ADN, 0.0, False)
            generatedSolutions.append(solution)
        self.myGAs.solutions = generatedSolutions
        
#---------------------------------------------------------------Evaluators
class Evaluator:
    def __init__(self, gas):
        self.myGAs = gas
        
    def evaluate(self):
        pass
        
class EvaluatorDEVS(Evaluator):

    def __init__(self, gas, weights):
        Evaluator.__init__(self, gas)
        self.weights = weights
        
    def evaluate(self):
        for solution in self.myGAs.solutions:
            somme = sum(map(lambda x: x[0]+x[1],solution.ADN))
            solution.fitness = somme
        
        
#---------------------------------------------------------------Selector
class Selector:
    
    def __init__(self, gas):
        self.myGAs = gas
        
    def select(self):
        pass
        
    def sortPopulation(self):
        self.myGAs.solutions = sorted(self.myGAs.solutions, self.compareSolutions)
        
    def compareSolutions(self, Solution1, Solution2):
        return Solution1.fitness - Solution2.fitness
        
class SelectorHalf(Selector):
    
    def __init__(self, gas):
        Selector.__init__(self, gas)
        
    def select(self):
        self.sortPopulation()
        self.defineReproductor()
        self.defineDead()

    def defineReproductor(self):
        for i in range(len(self.myGAs.solutions)/2,len(self.myGAs.solutions)):
            self.myGAs.solutions[i].reproductor = True
            
    def defineDead(self):
        for i in range(0,len(self.myGAs.solutions)/2):
            self.myGAs.solutions[i].reproductor = False
        
        
class SelectorPercent(Selector):
    
    def __init__(self, gas):
        Selector.__init__(self, gas)
        
    def select(self):
        pass

class SelectorKingQueen(Selector):
    
    def __init__(self, gas):
        Selector.__init__(self, gas)
        
    def select(self):
        pass
        
class SelectorTournament(Selector):
    
    def __init__(self, gas):
        Selector.__init__(self, gas)
        
    def select(self):
        pass
        
#---------------------------------------------------------------Reproductor
class Reproductor:
    
    def __init__(self, gas):
        self.myGAs = gas
        self.reproductors = filter(self.isReproductor, self.myGAs.solutions)
        self.deads = filter(self.isNotReproductor, self.myGAs.solutions)
        self.news = []
        
    def isReproductor(self, solution):
        if solution.reproductor:
            return True
        else:
            return False
    
    def isNotReproductor(self,solution):
        return not(self.isReproductor(solution))
        
class ReproductorHalf(Reproductor):
    
    def __init__(self, gas):
        Reproductor.__init__(self, gas)
        
    def reproduct(self):
        

        self.reproductors.reverse() #To avoid 1er and 2nd to have only one child in case of odd number
        for i,r in enumerate(self.reproductors):
            if(i<len(self.reproductors)-2):
                self.news.append(self.createNew(r, self.reproductors[i+1]))
                if len(self.news) < len(self.deads):
                    self.news.append(self.createNew(self.reproductors[i+1], r))

        self.reproductors.reverse()
        self.myGAs.solutions = self.news + self.reproductors
        del self.deads
        
    def createNew(self, solutionA, solutionB):
        Aadn = solutionA.ADN[0:len(solutionA.ADN)/2]
        Badn = solutionB.ADN[len(solutionA.ADN)/2:]
        Cadn = Aadn + Badn
        return Solution(Cadn,0.0,False)
        
class ReproductorOneOnTwo(Reproductor):
    
    def __init__(self):
        pass

class ReproductorRelative(Reproductor):
    
    def __init__(self):
        pass
        
#---------------------------------------------------------------Mutators
class Mutator:
    
    def __init__(self, gas):
        self.myGAs = gas
    
    def mutate(self):
        pass
        
class MutatorCoordinate(Mutator):
    
    def __init__(self, gas, rate):
        Mutator.__init__(self, gas)
        self.rate = rate
        
    def mutate(self):
        numberGeneToMutate = int(self.myGAs.seizeSolution * self.rate / 100)
        for solution in self.myGAs.solutions:
            indiceToMutate = random.sample(range(self.myGAs.seizeSolution),numberGeneToMutate)
            for i in indiceToMutate:
                solution.ADN[i] = self.changeGene()
            
    def changeGene(self):
        return ((random.randint(0,100),random.randint(0,100)))
        
#---------------------------------------------------------------Terminators
class Terminator:
    
    def __init__(self):
        pass
        
class TerminatorClassical:
    
    def __init__(self):
        pass
        
    





  
class Solution:
    
    def __init__(self, ADN, fitness, reproductor):
        self.ADN = ADN
        self.fitness = fitness
        self.reproductor = reproductor
        
    def __str__(self):
        return str(self.ADN) + " | " + str(self.fitness) + " | " + str(self.reproductor)