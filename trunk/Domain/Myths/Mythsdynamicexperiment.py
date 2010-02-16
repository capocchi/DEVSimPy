# -*- coding: Latin-1 -*-
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# templateExperiment.py --- Template for PythonDEVS experiments 
#                       --------------------------------
#                                November 2005
#                               Hans Vangheluwe
#                         McGill University (Montréal)
#                       --------------------------------
#       created: 20/11/05
# last modified: 20/11/05 
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

# Add the directory where pydevs lives to Python's import path
import sys
#import os.path
#sys.path.append('F:\python moi\Nouveau dossier\pydevs')
sys.path.append('D:\pydevs')

# Import code for model simulation:
#import pydevs
from infinity import *
from simulator import *

#    ======================================================================    #

# Import the model to be simulated
from Myths5dyntransformation import *

#    ======================================================================    #
#  The experiment
#

print "\n\n ** FIRST EXPERIMENT ******************************\n\n"

# 1. Instantiate the (Coupled or Atomic) DEVS at the root of the 
#  hierarchical model. This effectively instantiates the whole model 
#  thanks to the recursion in the DEVS model constructors (__init__).
#

#
# Reminder: the Root model has parameters 
#
#  np: number of processors
#  qs: queue size
#  ia: Job inter-arrival time lower bound
#  ib: Job inter-arrival time upper bound
#  sa: Job size lower bound
#  sb: Job size upper bound
#

# If the queue size is INFINITY (infinite capacity queue),
# only the first Processor will ever be used and Jobs will 
# never be DISCARDed.
#
#theSystem = Mythoot(np=2, qs=INFINITY, ia=3, ib=3, sa=4,  sb=6, name="theSystem")

# 1. Instantiate the (Coupled or Atomic) DEVS at the root of the 
#  hierarchical model. This effectively instantiates the whole model 
#  thanks to the recursion in the DEVS model constructors (__init__).
#
lm = []
teta = []
rep = ""
nmythestot = 0
print "voulez-vous charger des mythes???? (y/n)"
repcharg = input()
if repcharg == "y":
  print "loading"
  f = open('fichiermythes','r')
  lm = pickle.load(f)
  pickle.load(f)
  teta = pickle.load(f)
  print "teta!!!!"
  print teta, type(teta)
  print "???????"
  print lm, type(lm)
  fin = 1
  while fin==1:
    t = pickle.load (f)
    print t,type(t)
    if t == "fin":
      fin = 0

  f.close()

if repcharg == "n":
    rootModel = Mythsroot(name="rootModel")
    f = open('fichiermytheroot','w')
    print "je sauve root"
    pickle.dump(rootModel,f)
    pickle.dump("fin",f)
    f.close()
    #f = open('fichierteta','w')
    #print "je sauve teta"
    #pickle.dump(teta,f)
    #f.close()
    

else:
    f = open('fichiermytheroot','r')
    rootModel = pickle.load(f)
    print rootModel, type(rootModel)
    f.close ()
   
    
    
    
print"test 2"
print lm
print teta


#    ======================================================================    #

# 2. Link the model to a DEVS Simulator: 
#  i.e., create an instance of the 'Simulator' class,
#  using the model as a parameter.
sim = Simulator(rootModel)
print "test fin"

#    ======================================================================    #

# 3. Run the simulator on the model until a termination_condition is
# met, that is: the termination_condition function returns True.
# The termination_condition function receives two arguments
# from the simulation kernel:
#  * a reference to the root model 
#  * the current time
#
# sim.simulate(termination_condition= ..., verbose= ...)
#

# Typically, we set verbose=True when we want to debug a model and
# verbose=False when we are only interested in statistics/performance
# measures at the end of the simulation.

# Some typical termination_condition functions
#

# A. Simulate forever. 
#    The termination_condition function never returns True.
#


#########################################
#def terminate_never(model, clock):
# return False
#############################################


#sim.simulate(termination_condition=terminate_never,verbose=True)

# B. Simulate until a specified end_time is reached.
#    When the end_time is reached/exceeded, the 
#    termination_condition function returns True.
#
##################################################################
def terminate_whenEndTimeReached(model, clock, end_time=9):
  if clock >= end_time:
   return True
  else:
   return False

sim.simulate(termination_condition=terminate_whenEndTimeReached, 
            verbose=True)
################################################################"""
# C. Simulate until a specified end_state is reached.
#    When the end_state is reached, the 
#    termination_condition function returns True.
#
def terminate_whenStateIsReached(model, clock, end_state="manual"):
 print "test"
 aSubModel = model.getSubModel(name="subModelName")
 if aSubModel.state.get() == end_state:
   return True
 else:
  return False

sim.simulate(termination_condition=terminate_whenStateIsReached, 
            verbose=True)

#    ======================================================================    #

# Print statistics/performance measures
#
# Typically, extra state variables are added (but not printed
# in the behaviour trace) and updated in models to keep track
# of relevant performance measures such as
#  * mininum, maximum, mean, standard deviation of state variables
#  * distributions (GPSS TABULATE) of state variables' values
#
# At the end of the simulation experiment, these statistics are printed.
#
# Note that typically, verbose=True when we want to debug a model and
# verbose=False when we are only interested in statistics/performance
# measures at the end of the simulation.

#    ======================================================================    #

# Note how multiple experiments can be performed in sequence ...
# (or in some control structure if for example a parameter/initial
# state sweep is performed, for example when parameter estimation (shooting)
# or optimization is performed).




