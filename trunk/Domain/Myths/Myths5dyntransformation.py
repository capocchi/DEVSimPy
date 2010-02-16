
# -*- coding: Latin-1 -*-
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

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


# Add the directory where pydevs lives to Python's import path
import sys
#import os.path
import pickle
# sys.path.append(os.path.expanduser('~/src/projects/PythonDEVS/'))
#sys.path.append('F:\python moi\Nouveau dossier\pydevs')
sys.path.append('D:\pydevs')
# Import code for DEVS model representation:
#import pydevs
#from pydevs.devs_exceptions import *
#from pydevs.infinity import *
#from pydevs.DEVS import *

from devs_exceptions import *
from infinity import *
from DEVS import *

# Import for uniform random number generators 
from random import uniform
from random import randint

#    ======================================================================    #
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
   
#class actioncode:
  #""" A job has a unique, strictly positive integer ID number, 
      #and a positive 'size', in this case directly indicating 
      #the time a processor needs to process this job.
  #"""
  #IDCounter = 0   # class variable, globally unique

  #def __init__(self, actiontyp, param):
    #""" 
    #"""
    #action.IDCounter += 1
    #self.ID = action.IDCounter
    #print actiontyp
    #self.transf = actiontyp
    #self.param = param
    

  #def __str__(self):
    #print self.ID
    #print self.transf
    #return "(action %d, transformation %f)" %(self.ID, self.transf)
##    ======================================================================    #

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

class Generator(AtomicDEVS):
  """ Generates actions.


  """

  # all arguments should be strictly positive integers
  def __init__(self,ia,ib,name=None):

    # Always call parent class' constructor FIRST:
    self.ia=ia
    self.ib = ib
    AtomicDEVS.__init__(self, name)
    
   
    # make a local copy of the constructor's arguments
    
    self.IN = self.addInPort(name="IN")
    
   
    # add one output port
    self.OUT = self.addOutPort(name="OUT")
    self.state=GeneratorState(first=True)
    if repcharg == "n":
      listesauv.append(self)
    # Alternative:
    # self.elapsed = arbitrary_number
    
  def intTransition(self):
    self.state.first = False 
    return self.state
    
  def outputFnc(self):
    print "executer actions? (y/n) "
    answer1 = input()
    if answer1 == "y":
      repaction = ""
      term1 = ""
      term2 = ""
      term3 = ""
      term4 = ""
      term5 = 0
      listeactions = []
      i = 0
      nba = 0
      print "Nombre d'actions � executer?"
      nba = input()
      while i<nba:
        i = i + 1
      
        print "action generator"
    
        print "quelle action?"
        print "Numero "
        print i
        print "vous avez le choix entre :"
        print "(h)omologie"
        print "(i)nversion"
        print "(s)ym�trie"
        print "(o)pposition"
        print "(f)ormule canonique"
        print "(p) transformation putiphar"
        print "(l) last form of the CF"
        repaction = input()
        if repaction == "h":
          act = 1
          print "Avec quel terme doit-on effectuer l'homologie?"
          term1 = input ()
          print "Quel et le nouveau terme apres homologie?"
          term2 = input ()
        elif repaction == "i":
          act = 2
          print "Avec quel terme doit-on effectuer l'inverion?"
          term1 = input ()
        elif repaction == "s":
          act = 3
          print "Avec quel terme doit-on effectuer la sym�trie?"
          term1 = input ()
        elif repaction == "o":
          act = 4
          print "Avec quel terme doit-on effectuer l'opposition?"
          term1 = input ()
        elif repaction == "f":
          act = 5
          print "Quel myth�me est concern�?"
          term5 = input()
        elif repaction == "p":
          act = 6
          print "Quel myth�me est concern�?"
          term5 = input()
        elif repaction == "l":
          act = 6
          print "Quel myth�me est concern�?"
          term5 = input()


        listeactions.append((act,term1,term2,term3,term4,term5))
    
    
    #act = input ()
  
      act = action(act,listeactions)        
    # In pythonDEVS, event objects are "poke"d on output ports
    # in the outputFnc. Conversely, in the extTransition
    # function, it is possible to "peek" input ports for incoming
    # event objects. This deviates from classic DEVS which 
    # does not have ports.
      self.poke(self.OUT, act)
      print "fin generator"
    

  def timeAdvance(self):
    if self.state.first == True:
     return 0
    else:
     return uniform(self.ia, self.ib)
    # Alternative
    # if self.state.first == True:
    #  return arbitrary_number 
    # else:
    #  return uniform(self.ia, self.ib)
    # 
    
#    ======================================================================    #




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


class TransformationADEVS(AtomicDEVS) :
  """Sample Atomic-DEVS descriptive class.
  """
  
  ###
  def __init__(self, myths, fonction, liste, currentST, name= None):
    """Constructor (parameterizable).
       Giving a name (string) to a model is not mandatory
       (a globally unique name "A<i>" is assigned by default).
       If a name is given, the simulation trace becomes far more
       readable.
    """
    
    # Always call parent class' constructor FIRST:
    AtomicDEVS.__init__(self, name)
    print "Mythe de d�part ?"
    print "donner le numero du mythe?"
    numdep = input ()
    mythdep = numdep
    #mythdep = "st%s" % numdep 
    print mythdep
    #f= open('fichiermythes','w')
    self.state = TransformationADEVSState(myths = [], fonction = [], liste = [], currentST = mythdep, active = mythdep - 1)
    
    if repcharg == "n":
      listesauv.append(self.state)
      print self.state
    
    #pickle.dump(self.state,f)
    # TOTAL STATE:
    #  Define 'state' attribute (initial sate):
    #print "commbien de mythes voulez-vous?"
    #nmyths = input()
    #ll = []
    #for i in range(1,nmyths):
     # tmpName = "st%s" % i
     # tmp = self.addSubModel(MythvariantCDEVS(name=tmpName))
      # ll = ll + [tmp]

   # self.list = TransformationADEVSState(self,list=ll)
   # self.currentST = list[1]

    # ELAPSED TIME:
    #  Initialize 'elapsed time' attribute if required.
    #  (by default (if not set by user), self.elapsed is initialized to 0.0)
    self.elapsed = 0.0
    #  With elapsed time for example initially 1.1 and 
    #  this SampleADEVS initially in 
    #  a state which has a time advance of 60,
    #  there are 60-1.1 = 58.9 time-units remaining until the first 
    #  internal transition 

    # HV: check in simulator that elapsed can not be larger than
    # timeAdvance
    
    # PORTS:
    #  Declare as many input and output ports as desired
    #  (usually store returned references in local variables):
    self.IN = self.addInPort(name="IN")
    self.OUT = self.addOutPort(name="OUT")
    
    #pickle.dump(self.IN,f)
    #pickle.dump(self.OUT,f)
    #f.close()
  ###
  def extTransition(self) :
    """External Transition Function."""
    
    # Compute and return the new state based (typically) on current
    # State, Elapsed time parameters and calls to 'self.peek(self.IN)'.
    # When extTransition gets invoked, input has arrived
    # on at least one of the input ports. Thus, peek() will
    # return a non-None value for at least one input port.

   
   
    #print self
   # print self.state
    a = self.state.currentST
   # print a
    evenemt = self.peek(self.IN)
   # print "event"
   # print evenemt
   # print "current state"
   # print self
   # print "etce cela?"
    #print self.state.currentST
   # print "oui oui"
    self.state.fonction.append(evenemt.transf)
   # print self.state.fonction
   # print "non non"
   # print evenemt.ID
   # print evenemt.transf
   # print "oui oui"
    print "param"
    print evenemt.param
    
    print "fonction"
    print self.state.fonction

    
   
    
    print "le mythe courant est le suivant :"
    print self.state.currentST
    i = 0
    #print len(teta)
    #print teta[0]
   #print teta[0][0]
    #while i < len(teta):
     # if self.state.currentST == teta[i][0]:
      #  myth = teta[i][1]
      #  i = len(teta)
     # i = i + 1
    longactions = 0
    longactions =  len (evenemt.param)
    print longactions
   # longactions = longactions - 1
    print evenemt.param

    j = 0
   
    print "le mythe courant est le suivant :"
    print "ATTENTION"
    print self.state.currentST
    print self.state
    print self
    print self.state.myths[0]
    print "il  est compos� de "
    print self.parent.dynamicComponentSet
    myth = self.parent.dynamicComponentSet[self.state.currentST - 1]
    print "MYTHE !!!"
    print myth
    l = len(myth.componentSet)
    print l
    print "myth�me (s)"
    i = 0
    print "le mythe est donc:"
    while i < l:
      print myth.componentSet[i].a
      print "poss�de"
      print myth.componentSet[i].x
      i = i + 1
    modif = 1
    nummyth = self.state.currentST-1
    mythcourant = myth
    print self.state.currentST
    na = "mythe%s" % (self.state.currentST+1)
    print na
    print self.parent
    #ERREUR SUB = self.parent.addSubModel(MythvariantbisCDEVS(name=na))
    SUB = MythvariantCDEVS(name=na)
    newmodel = SUB
    print "!!!!attention!!!!"
    print self.parent
    prevport = SUB.IN
    print "l(a)es transformation(s) suivante(s) es(son)t appliqu�e(s):"
    while j < longactions:     
      if evenemt.param[j][0] ==1:
          print "homologie entre "
          print evenemt.param [j][1]
          print "et"
          print evenemt.param [j][2]
          listeret = homologie (mythcourant,newmodel,evenemt.param [j][1],evenemt.param [j][2],newmodel.IN,na) 
          prevport = listeret[0]
          mythcourant = listeret[1]
          print "homologie"
          print prevport
          print mythcourant
          print SUB
          
      if evenemt.param[j][0] ==2:
          print "inversion du terme"
          print evenemt.param [j][1]
          mythcourant = inversion(mythcourant,evenemt.param [j][1])

      if evenemt.param[j][0] ==3:
          print "symetrie entre "
          print evenemt.param [j][1]
          print "et"
          print evenemt.param [j][2]
          mythcourant = symetrie(mythcourant,evenemt.param [j][1],evenemt.param [j][2])

      if evenemt.param[j][0] ==4:
          print "opposition du terme"
          print evenemt.param [j][1]
          mythcourant = oppostion(mythcourant,evenemt.param [j][1])

      if evenemt.param[j][0] ==5:
          print "formule canonique appliqu�e sur le myth�me : "
          print evenemt.param [j][4]
          mythcourant = fc (myth,evenemt.param [j][4])

      if evenemt.param[j][0] ==6:
          print "transformation putiphar appliqu�e sur le myth�me :"
          print evenemt.param [j][4]
          mythcourant = putiphar (myth,evenemt.param [j][4])
      print "boucle"
      print j
      print mythcourant
      print prevport
      if j != 1:
        na = "mythe%s" % (self.state.currentST+1)
        newmodel = MythvariantCDEVS(name=na)
      j = j + 1
    #ATTENTION ERREUR mythcourant.connectPorts(prevport, mythcourant.OUT)
    print "myth courant connect port fait"
    self.state.currentST =  self.state.currentST + 1
    #ATTENTION ERREUR self.state.myths.append(mythcourant)
    #remplacer self par myhticalthought
    self.parent.dynamicComponentSet.append(SUB)
    print "IC"
    print mythcourant.IC
    print "EOC"
    print mythcourant.EOC
    self.parent.dynamicIC.append(mythcourant.IC)
    self.parent.dynamicEOC.append(mythcourant.EOC)
    self.parent.dynamicEIC.append (mythcourant.EIC)
    supervis = self.parent.supervisor
    print "supervis"
    print supervis
    #erreur supervis.state.myths.append(mythcourant)  
    # � remettre 2 self.parent.connectPorts(supervis.OUT, mythcourant.IN)
    #mythanc = self.state.myths[self.state.currentST-2]
    #self.parent.disconnectPorts(supervis.OUT,mythanc.IN)
    #self.parent.disconnectPorts(mythanc.OUT,mythanc.IN)
    #self.parent.disconnectPorts(supervis.OUT,mythanc.IN)
    print "connect ports 2 fait"
    # � remettre 2 self.parent.connectPorts(mythcourant.OUT, self.parent.OUT)
    
    # a remettre self.parent.disconnectPorts(mythanc.OUT, self.parent.OUT)
    transf = self.parent.componentSet[0]
    print "TRANSF���"
    print transf
    #a remettre self.parent.disconnectPorts(transf.OUT,mythanc.IN)
    i = 0
    
    print "current state"
    print self.state.currentST
    # ATTENTION ERREUR ind = self.state.currentST - 1
    print "ind"
   # ATTENTION ERREUR print ind
    # ATTENTION ERREUR myth = self.state.myths[ind]
    l = len(SUB.componentSet)
    print l
    print "myth�me (s)"
    k = 0
    print "le mythe est donc:"
    while k < l:
      print SUB.componentSet[k].a
      print "poss�de"
      print SUB.componentSet[k].x
      k = k + 1
    print "self.state.currentST"
    print supervis.state.myths
    return self.state

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
     
        
     

  ###
 # def intTransition(self):
  #  """Internal Transition Function.
  #  """

    # Compute and return the new state  based (typically) on current State.
    # Remember that intTransition gets called after the outputFnc,
    # timeAdvance time after the current state was entered.
  
    #state = self.state

    # Typical logic:

   # if state == some_state_1:
     # return SampleADEVSState(new state parameters)
   # if state in (some set of states):
   #   return SampleADEVSState(other new state parameters)
   # ...
   # else:
   #   raise DEVSException(\
    #  "unknown state <%s> in SampelADEVS external transition function"\
    #  % state)

  ###
 #def outputFnc(self):
   # """Output Function.
   # """
    
    # Send events via a subset of the atomic-DEVS' 
    # output ports by means of the 'poke' method.
    # More than one port may be poke-d.
    # The content of the messages is based (typically) on the current State.
    # 
    # BEWARE: ouput is based on the CURRENT state
    # and is produced BEFORE making the internal transition.
    # Often, we want output based on the NEW state (which
    # the system will transition to by means of the internal 
    # transition. The solution is to keep the NEW state in mind
    # when poke-ing the output. 
    # This will only work if the internal transition function 
    # is deterministic !

   # state = self.state

   # if state == some_state_1:
    #  self.poke(self.OUT, SampleEvent(some params))
    # elif state == some_state_2:
    #  self.poke(self.OUT, SampleEvent(some other params))
      # NOT self.poke(self.OBSERVED, "grey")
   # ...
   # else:
    #  raise DEVSException(\
    #    "unknown state <%s> in SampelADEVS external transition function"\
    #    % state)
    
  ###
  #def timeAdvance(self):
   # """Time-Advance Function.
    #"""
    
    # Compute 'ta', the time to the next scheduled internal transition,
    # based (typically) on the current State.
    
    # Note how it 
   # state = self.state

   # if state == some_state_1:
   #   return 20
    # elif state == some_state_2:
   #   return 10.123 
   # ...
   # elif state == passive_state:
   #   return INFINITY 
   # else:
    #  raise DEVSException(\
    #    "unknown state <%s> in SampelADEVS time advance function"\
    #    % state)

    #return ta


##### Mythem #################




class MythemADEVS(AtomicDEVS):
  
  
  def __init__(self, a, x, name=None):
    
    
    
    AtomicDEVS.__init__(self, name)
    
    # TOTAL STATE:
    #  Define 'state' attribute (initial sate):
    self.a = a
    self.x = x
    
   

    # ELAPSED TIME:
    #  Initialize 'elapsed time' attribute if required.
    #  (by default (if not set by user), self.elapsed is initialized to 0.0)
    self.elapsed = 0.0
    #  With elapsed time for example initially 1.1 and 
    #  this SampleADEVS initially in 
    #  a state which has a time advance of 60,
    #  there are 60-1.1 = 58.9 time-units remaining until the first 
    #  internal transition 

    # HV: check in simulator that elapsed can not be larger than
    # timeAdvance
    
    # PORTS:
    #  Declare as many input and output ports as desired
    #  (usually store returned references in local variables):
    self.IN = self.addInPort(name="IN")
    self.OUT = self.addOutPort(name="OUT")
    #pickle.dump(self.IN,f)
    #pickle.dump(self.OUT,f)
    #print "faut-il sauver le ports??????????????"
    #listesauv.append(self.IN)
    #listesauv.append(self.OUT)
    #f.close()

  ###
  def extTransition(self):
    """External Transition Function."""
    
    # Compute and return the new state based (typically) on current
    # State, Elapsed time parameters and calls to 'self.peek(self.IN)'.
    # When extTransition gets invoked, input has arrived
    # on at least one of the input ports. Thus, peek() will
    # return a non-None value for at least one input port.

    evenemt= self.peek(self.IN)

   # state = self.state

    # Typical logic:

   # if input == some_input_1:
    #  if state == some_state_1:
     #  return SampleADEVSState(new state parameters)
     # if state in (some set of states):
     #  return SampleADEVSState(other new state parameters)
     # else:
     #  raise DEVSException(\
     #   "unknown state <%s> in SampelADEVS external transition function"\
      #  % state)
    
   # if input == some_input_2:
   #   ...

   # ...

   # raise DEVSException(\
    #  "unknown input <%s> in SampelADEVS external transition function"\
     # % input) 

  ###
 # def intTransition(self):
  #  """Internal Transition Function.
   # """

    # Compute and return the new state  based (typically) on current State.
    # Remember that intTransition gets called after the outputFnc,
    # timeAdvance time after the current state was entered.
  
  #  state = self.state

    # Typical logic:

  #  if state == some_state_1:
  #    return SampleADEVSState(new state parameters)
  #  if state in (some set of states):
   #   return SampleADEVSState(other new state parameters)
   # ...
   # else:
    #  raise DEVSException(\
    #  "unknown state <%s> in SampelADEVS external transition function"\
    #  % state)

  ###
 # def outputFnc(self):
  #  """Output Function.
   # """
    
    # Send events via a subset of the atomic-DEVS' 
    # output ports by means of the 'poke' method.
    # More than one port may be poke-d.
    # The content of the messages is based (typically) on the current State.
    # 
    # BEWARE: ouput is based on the CURRENT state
    # and is produced BEFORE making the internal transition.
    # Often, we want output based on the NEW state (which
    # the system will transition to by means of the internal 
    # transition. The solution is to keep the NEW state in mind
    # when poke-ing the output. 
    # This will only work if the internal transition function 
    # is deterministic !

   # state = self.state

   # if state == some_state_1:
  #    self.poke(self.OUT, SampleEvent(some params))
  #  elif state == some_state_2:
  #    self.poke(self.OUT, SampleEvent(some other params))
      # NOT self.poke(self.OBSERVED, "grey")
   # ...
   # else:
   #   raise DEVSException(\
   #     "unknown state <%s> in SampelADEVS external transition function"\
    #    % state)
    
  ###
 # def timeAdvance(self):
 #   """Time-Advance Function.
  #  """
    
    # Compute 'ta', the time to the next scheduled internal transition,
    # based (typically) on the current State.
    
    # Note how it 
  #  state = self.state

  #  if state == some_state_1:
   #   return 20
   # elif state == some_state_2:
   #   return 10.123 
  #  ...
   # elif state == passive_state:
   #   return INFINITY 
   # else:
    #  raise DEVSException(\
    #    "unknown state <%s> in SampelADEVS time advance function"\
     #   % state)

    #return ta


  
#    ======================================================================    #
class Mythsroot(CoupledDEVS) :

 def __init__(self , ia = 2, ib = 7, name=None):
    CoupledDEVS.__init__(self, name)
    self.IN = self.addInPort(name="IN")
    self.OUT = self.addOutPort(name="OUT")
   
   
      
  
    self.GDEVS = self.addSubModel(Generator (ia,ib,name="GeneratorDEVS"))
   
    self.connectPorts(self.IN,self.GDEVS.IN)
    precport = self.GDEVS.OUT
    
    self.SUB = self.addSubModel(MythicalThoughtCDEVS(name="coupledDEVS"))
    print "mythical tought"
    print self.SUB
    self.connectPorts(self.SUB.OUT,self.OUT)
    self.connectPorts(precport,self.SUB.IN)
     


   

class DynamiqueCDEVS(CoupledDEVS):
  """Sample Coupled-DEVS descriptive class: compulsory material.
  """
  
  ###
  def __init__(self,supervisor, myIDNetwork,myInputNetwork, myOutputNetwork, dynamicComponentSet, dynamicIC, dynamicEIC, dynamicEOC,name=None):
    
  
    
    CoupledDEVS.__init__(self, name)
   
    #self.IN = self.addInPort(name="IN")
    #self.OUT = self.addOutPort(name="OUT")
    self.dynamicComponentSet = []
    self.dynamicIC = []
    self.dynamicEIC = []
    self.dynamicEOC = []
   
  def delSubModel (self,model):
    """Constructor (parameterizable).
       Giving a name (string) to a model is not mandatory
       (a globally unique name "C<i>" is assigned by default).
       If a name is given, the simulation trace becomes far more
       readable.
    """
    self.componentSet.remove(model)
    
  # def addSubModel(self, model):
  
    #self.componentSet.append(model)    
   # model.parent = self
   # return model
    # Always call parent class' constructor FIRST:
    #CoupledDEVS.__init__(self, name)
    #def getSubModel(self, name):
    """Get a sub-model by name, return None if not found.
    """
    # HV: TODO: allow complete path names (e.g., "C1.C2.A") as names

    #subModels = self.componentSet

    #for i in range(len(subModels)):
    #  if subModels[i].getModelName() == name:
     #   return subModels[i]

    #return None
  def disconnectPorts (self,p1,p2):
    if ((p1.hostDEVS.parent == self and p2.hostDEVS.parent == self) and (p1.type() == 'OUTPORT' and p2.type() == 'INPORT')):
      self.IC.remove(( (p1.hostDEVS,p1), (p2.hostDEVS,p2)))
      p1.outLine.remove(p2)
      p2.inLine.remove(p1)
    elif ((p1.hostDEVS == self and p2.hostDEVS.parent == self) and(p1.type() == p2.type() == 'INPORT')):
      self.EIC.remove( ( (p1.hostDEVS, p1), (p2.hostDEVS, p2) ) )
      p1.outLine.remove(p2)
      p2.inLine.remove(p1)
    elif ((p1.hostDEVS.parent == self and p2.hostDEVS == self) and(p1.type() == p2.type() == 'OUTPORT')):
      self.EOC.append( ( (p1.hostDEVS, p1), (p2.hostDEVS, p2) ) )
      p1.outLine.remove(p2)
      p2.inLine.remove(p1)
    

    # For a coupling to be valid, two requirements must be met:
    # 1- at least one of the DEVS the ports belong to is a child of the
    #    coupled-DEVS ({\it i.e.}, {\tt self}), while the other is either the
    #    coupled-DEVS itself or {\sl another\/} of its children. The DEVS'
    #   'parenthood relationship' uniquely determine the type of coupling;
    # 2- the types of the ports are consistent with the 'parenthood' of the
    #    associated DEVS. This validates the coupling determined above.
    
    # {\sl Internal Coupling\/}:
   # if ((p1.hostDEVS.parent == self and p2.hostDEVS.parent == self) and
     #   (p1.type() == 'OUTPORT' and p2.type() == 'INPORT')):
     # if p1.hostDEVS == p2.hostDEVS:
      #  raise DEVSException("In coupled model '" + self.getModelFullName() + \
                       #     "' connecting ports '" + p1.getPortFullName() + \
                      #      "' and '" + p2.getPortFullName() + \
                      #      "' belong to the same model '" + \
                  #          p1.hostDEVS.getModelFullName() + "'. " + \
                       #     "Direct feedback coupling not allowed", 0)
   #   else:
    #    self.IC.append( ( (p1.hostDEVS, p1), (p2.hostDEVS, p2) ) )
    #    p1.outLine.append(p2)
     #   p2.inLine.append(p1)
    
    # {\sl external input couplings\/}:
   # elif ((p1.hostDEVS == self and p2.hostDEVS.parent == self) and
      #   (p1.type() == p2.type() == 'INPORT')):
      #  self.EIC.append( ( (p1.hostDEVS, p1), (p2.hostDEVS, p2) ) )
     #   p1.outLine.append(p2)
      #  p2.inLine.append(p1)
    
    # {\sl external output couplings\/}:
   # elif ((p1.hostDEVS.parent == self and p2.hostDEVS == self) and
#	        (p1.type() == p2.type() == 'OUTPORT')):
   #     self.EOC.append( ( (p1.hostDEVS, p1), (p2.hostDEVS, p2) ) )
   #     p1.outLine.append(p2)
   #     p2.inLine.append(p1)

    # Always call parent class' constructor FIRST:
    #CoupledDEVS.__init__(self, name)

  #def couplingFct (self,index):
    #ajouter les connections voulues dans les attributs voulus
  
    # Always call parent class' constructor FIRST:
    #CoupledDEVS.__init__(self, name)


    
    # COUPLINGS:
    #  Method 'connectPorts' takes two parameters 'p1' and 'p2' which are
    #  references to ports. 
    #  The coupling is to BEGIN at 'p1' and to END at 'p2'.
    #  Each input/output port can have 
    #  multiple incoming/outgoing connections.
    #  Note how PythonDEVS does NOT support Z_i,j transfer
    #  functions (as defined in DEVS) yet.
    #  On the other hand, PythonDEVS does have named ports.
   
      
  
#    ======================================================================    #
   
class MythicalThoughtCDEVS(DynamiqueCDEVS):
 
  

  def __init__(self,name=None):
    
    #CoupledDEVS.__init__(self, name)
    DynamiqueCDEVS.__init__(self,[],[],[],[],[],[], [],[],name=None)
  
    print "Mythical INIT"
    print self
    self.IN = self.addInPort(name="IN")
    self.OUT = self.addOutPort(name="OUT")
    self.SUB = self.addSubModel(TransformationADEVS(None,[],lm,None,name="Thought"))
    self.supervisor = self.SUB
    print "SUPERVISOR"
    print self.supervisor
    print "Fin supervisor"
    self.connectPorts(self.IN, self.SUB.IN)
    #Mythe 1
    l =[]
    self.SUB1 = self.addSubModel(MythvariantCDEVS(name="mythe1"))
    #self.myIDNetwork = self.SUB1.myID
    #self.myInputNetwork = self.SUB1.Iports
    #self.myOutputNetwork = self.SUB1.Oports
    print "IC"
    print self.SUB1.IC
    print "EOC"
    print self.SUB1.EOC
    self.dynamicComponentSet.append(self.SUB1)
    self.dynamicIC.append(self.SUB1.IC)
    self.dynamicEOC.append(self.SUB1.EOC)
    self.dynamicEIC.append (self.SUB1.EIC)
    self.SUB.state.myths.append(self.SUB1)
    print "ports :"
    print self.SUB.OUT
    print self.SUB1.IN
    print self.SUB1.OUT
    print self.OUT
    self.connectPorts(self.SUB.OUT, self.SUB1.IN)
    self.connectPorts(self.SUB1.OUT, self.OUT)
        
    
   #myIDNetwork,myInputNetwork, myOutputNetwork, dynamicComponentSet, dynamicIC, dynamicEIC, dynamicEOC

    # COUPLINGS:
    #  Method 'connectPorts' takes two parameters 'p1' and 'p2' which are
    #  references to ports. 
    #  The coupling is to BEGIN at 'p1' and to END at 'p2'.
    #  Each input/output port can have 
    #  multiple incoming/outgoing connections.
    #  Note how PythonDEVS does NOT support Z_i,j transfer
    #  functions (as defined in DEVS) yet.
    #  On the other hand, PythonDEVS does have named ports.
   
      
  

#    ======================================================================    #


class MythvariantCDEVS(CoupledDEVS) :
 
 
  def __init__(self,name=None):
    
    CoupledDEVS.__init__(self, name)
    self.IN = self.addInPort(name="IN")
    self.OUT = self.addOutPort(name="OUT")
  
   # self.supervisor = super
    # SUB-MODELS:
    #  Declare as many sub-models as desired. Method 'addSubModel' takes as a
    #  parameter an INSTANCE of an atomic- or coupled-DEVS descriptive class,
    #  and returns a reference to that instance (usually kept in a local
    #  variable for future reference):
   #myIDNetwork,myInputNetwork, myOutputNetwork, dynamicComponentSet, dynamicIC, dynamicEIC, dynamicEOC
    print "modif!!!!"
    print modif
    print "name!!!"
    print name
    if name == "mythe1":
      prevport = self.IN
      print "donnez le nombre de mythemes?"
      nmythems = input ()
      for i in range(0, nmythems) :
        tmpName = "st%s" % i
        print "quel est la fonction du mytheme numero " , i , "du mythe " , self.name
        x = input ()
        print "quel est le terme du mytheme numero " , i , "du mythe " , self.name
        a = input ()
        tmp = self.addSubModel(MythemADEVS(a,x,name=tmpName))
        self.connectPorts(prevport, tmp.IN)
        prevport = tmp.OUT
      self.connectPorts(prevport, self.OUT)
    
   
class MythvariantbisCDEVS(CoupledDEVS) :
 
 
  def __init__(self,name=None):
    
    CoupledDEVS.__init__(self, name)
    self.IN = self.addInPort(name="IN")
    self.OUT = self.addOutPort(name="OUT")
    print self
  
   
    
   
    # COUPLINGS:
    #  Method 'connectPorts' takes two parameters 'p1' and 'p2' which are
    #  references to ports. 
    #  The coupling is to BEGIN at 'p1' and to END at 'p2'.
    #  Each input/output port can have 
    #  multiple incoming/outgoing connections.
    #  Note how PythonDEVS does NOT support Z_i,j transfer
    #  functions (as defined in DEVS) yet.
    #  On the other hand, PythonDEVS does have named ports.
    # self.connectPorts(self.SUB1.OUT1, self.SUB2.IN1) # INTERNAL COUPLING
    #self.connectPorts(self.IN, self.SUB.IN)   # EXTERNAL INPUT COUPLING

     
 

#    ======================================================================    #
