from Domain.Strategy.evaluator.abstractEvaluator import AbstractEvaluator

class TopologieEvaluator(AbstractEvaluator):

    def __init__(self):
        AbstractEvaluator.__init__(self)

    def getNextPlacement(self):
        pass

    def getRangePlacement(self):
        pass

    def __str__(self):
        return "TopologieEvaluator"