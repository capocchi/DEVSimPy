from Domain.Genetic.Lib.SimpleAtomicModel import SimpleAtomicModel
from Domain.Optimization._GAS_ import *

class Mutator(SimpleAtomicModel):
    """
    This class ...
    @author: Bastien POGGI
    @organization: University Of Corsica
    @contact: bpoggi@univ-corse.fr
    @since: 2013.05.01
    @version: 1.0
    """

    def __init__(self, mutateRate=20.0):
        SimpleAtomicModel.__init__(self)
        self.becomeDesactivate()
        self.mutateRate = mutateRate
        self.myMutator = None

    def extTransition(self):
        self.showScreen("Population reproducted received")
        self.ga = self.readMessage()
        self.myMutator = MutatorCoordinate(self.ga, self.mutateRate)
        self.becomeActivate()
        

    def outputFnc(self):
        self.showScreen("send population mutate")
        self.myMutator.mutate()
        self.showScreen("\n" + str(self.ga))
        self.sendMessage(0,self.ga)


    def intTransition(self):
        self.becomeDesactivate()


    def __str__(self):
        return "Mutator"
