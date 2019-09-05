from pypdevs.simulator import Simulator

from mymodel import MyModel

model = MyModel()
simulator = Simulator(model)

simulator.setVerbose()

simulator.simulate()