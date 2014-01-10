# Create a simulator with your model
model = Model()
sim = Simulator(model)

# Some of the most common options
# Enable verbose tracing
sim.setVerbose("output")

# End the simulation at simulation time 200
sim.setTerminationTime(200)
# Or use a termination condition to do the same
#def cond(model, time):
#    return time >= 200
#sim.setTerminationCondition(cond)

# If you want to reinit it later
sim.setAllowLocalReinit(True)

# Finally simulate it
sim.simulate()

# Now possibly use the altered model by accessing the model attributes

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# !!! Only possible in local simulation, distributed simulation requires !!!
# !!!           another configuration option to achieve this.            !!!
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# You might want to rerun the simulation (for whatever reason)
# Just call the simulate method again, all configuration from before will be
# used again. Altering configuration options is possible (to some extent)
sim.simulate()

# Or if you want to alter a specific attribute
sim.setReinitState(model.generator, GeneratorState())
sim.setReinitStateAttr(model.generator, "generated", 4)
sim.setReinitAttributes(model.generator, "delay", 1)

# Now run it again
sim.simulate()
