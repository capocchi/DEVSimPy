from Domain.Genetic.Lib.SimpleAtomicModel import SimpleAtomicModel
from Domain.Optimization._GAS_ import *

class Generator(SimpleAtomicModel):
    """
    This class ...
    @author: Bastien POGGI
    @organization: University Of Corsica
    @contact: bpoggi@univ-corse.fr
    @since: 2013.05.01
    @version: 1.0
    """

    def __init__(self, numberSolutions=50, seizeSolution=5):
        SimpleAtomicModel.__init__(self)
        self.ga = GAs()
        self.myGenerator = GeneratorCoordinates(self.ga, 0, 100, 0, 100, 10, 5)
        self.becomeActivate()
        
    def extTransition(self):
        pass
        
    def outputFnc(self):
        self.showScreen("Send generated population")
        self.showScreen("\n" + str(self.ga))
        self.myGenerator.generate()
        self.sendMessage(0,self.ga)

    def intTransition(self):
        self.becomeDesactivate()


    def __str__(self):
        return "Generator"
