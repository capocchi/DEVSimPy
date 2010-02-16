# -*- coding: iso-8859-1 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# Object.py ---
#                     --------------------------------
#                        Copyright (c) 2008
#                      University of Corsica
#                     --------------------------------
# Version 3.0                                        last modified: 9/03/04
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
#  GENERAL NOTES AND REMARKS:
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

#    ======================================================================    #

# Add the directory where pydevs lives to Python's import path
import sys
#import os.path
import pickle

# Import for uniform random number generators 
from random import uniform
from random import randint

modif = 0
listesauv =[]
lm = []
nbmythes = 0
repcharg = ""
teta = []
bibhom = {}
bibsym = {}
bibopp = {}
bibinv = {}
bibhom['ogre'] = 'Sybille'
bibhom['villageois'] = 'Saint Martin'
bibinv['ogre'] = 'berger'
bibinv['secret'] = 'au grand jour'
numdep = 0
listeret =[]

class action:
  """ A job has a unique, strictly positive integer ID number, 
      and a positive 'size', in this case directly indicating 
      the time a processor needs to process this job.
  """
  IDCounter = 0   # class variable, globally unique

  def __init__(self, actiontyp, param):
    """ 
    """
    action.IDCounter += 1
    self.ID = action.IDCounter
    print actiontyp
    self.transf = actiontyp
    self.param = param
    

  def __str__(self):
    print self.ID
    print self.transf
    return "(action %d, transformation %f)" %(self.ID, self.transf)
  
#    ======================================================================    #

class GeneratorState:
  """ A class to hold the state of a Generator Atomic DEVS.
  
  Not really required, but allows us to define 
  the __str__ method for pretty printing.
  """

  def __init__(self, first):
    # keep track whether this is the first
    # time an internal transition is invoked
    self.first = first
    if repcharg == "n":
      listesauv.append(self)
    

  def __str__(self):
    return "\n\
            first           = %s" % self.first

#    ======================================================================    #

class TransformationADEVSState:

  """Encapsulate the Atomic DEVS' state
     This is not absolutely necessary, but it makes
     it easier to 
     (1) stick to the DEVS formalism
     (and not modify the state "behind the back of the simulator" --
     this will be enforced once we have a DEVS compiler), and
     (2) to produce a clean simulation trace (thanks to __str__).
  """

  ###
  def __init__(self, myths = [],fonction = [], liste = [],currentST = None,active= None):
    """Constructor (parameterizable).
    """

    # set the initial state
    # the state may be multi-dimensional: 
    # consist of multiple state variables
    self.fonction = fonction
    self.liste = liste
    self.currentST = currentST
    self.myths = myths
    self.active = active
   
    if repcharg == "n":
      listesauv.append(self)
    
   

  # string representation
  def __str__(self):
   # return a string representing the entire TransformationADEVSState
   # print self.myths
   # print self.liste
   # print self.currentST
    return "(list %d, currentST %f)"

#    ======================================================================    #

class MythemADEVSState :

  """Encapsulate the Atomic DEVS' state
     This is not absolutely necessary, but it makes
     it easier to 
     (1) stick to the DEVS formalism
     (and not modify the state "behind the back of the simulator" --
     this will be enforced once we have a DEVS compiler), and
     (2) to produce a clean simulation trace (thanks to __str__).
  """

  ###
  def __init__(self, a,x) :
    """Constructor (parameterizable).
    """

    # set the initial state
    # the state may be multi-dimensional: 
    # consist of multiple state variables
    self.a = a
    self.x = x
    listesauv.append(self.a)
    listesauv.append(self.x)

  # string representation
  def __str__(self) :
   # return a string representing the entire SampleADEVSState
   return "(a %d, x %f)" % (self.a,self.x)

#    ======================================================================    #

def homologie (mythe,newmodel, term1,term2,prevport,na):
  listeret=[]
  print "on applique une homologie"
  print "sur le mythe courant"
  print "du terme"
  print term1
  print "en terme"
  print term2
  l = len(mythe.componentSet)
  print l
  print "myth�me (s)"
  k = 0
  
    
  while k < l:
    print mythe.componentSet[k].a
    if term1 == mythe.componentSet[k].a :
      print "attention"
      print newmodel
      print mythe
      tmp = newmodel.addSubModel(MythemADEVS(term2,mythe.componentSet[k].x,name=na))
      newmodel.connectPorts(prevport, tmp.IN)
      prevport = tmp.OUT
      print prevport
      print tmp
    else:
      tmp = newmodel.addSubModel(MythemADEVS(mythe.componentSet[k].a,mythe.componentSet[k].x,name=na))
      newmodel.connectPorts(prevport, tmp.IN)
      prevport = tmp.OUT

    k = k + 1
    
  listeret.append(prevport )
  listeret.append(newmodel)
  return listeret


def inversion (mythe,term):
  print "on applique une inversion"
  print "sur le mythe courant"
  print "du terme"
  print term
  
  return mythe

def symetrie(mythe,term):
  print "on applique une symetrie"
  print "sur le mythe courant"
  print "sur le terme"
  print term

  return mythe

def opposition (mythe,term):
  print "on applique une opposition"
  print "sur le mythe courant"
  print "sur le terme"
  print term
 
  return mythe

def fc (mythe,nbmytheme):
  print "on applique transformation de type formule canonique"
  print "sur le mythe courant"
  print "pour le myth�me"
  print nbmytheme

  return mythe

def putiphar(mythe,nbmytheme):
  print "on applique transformation putiphar"
  print "sur le mythe courant"
  print "pour le myth�me"
  print nbmytheme

  return mythe

def calculnouveletat (mythecourant, etatcourant):
  print "calculnouveletat"
  print etatcourant
  if etatcourant =="st0":
    return "st1"
  if etatcourant == "st1":
    return "st2"
  if etatcourant == "st2":
    return "st3"
  if etatcourant == "st3":
    return "st4"
  else:
    raise DEVSException(\
      "unknown state <%s> in SampelADEVS external transition function")