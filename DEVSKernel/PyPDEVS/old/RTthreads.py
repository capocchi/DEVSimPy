# -*- coding: Latin-1 -*-
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# RTthreads.py 
#
# Sender of events - Main simulation loop, both in threads  
#
#                       --------------------------------
#                                June 2013 
#                           Yentl Van Tendeloo
#                             Hans Vangheluwe 
#                         McGill University (Montréal)
#                       --------------------------------
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

# Add the directory where RTpythonDEVS lives to Python's import path
import sys
import string

# For the Real-Time simulator
import time, threading, sys, signal

# human-readable local time
def now():                        
  return time.ctime(time.time())

from .cores import *

# Import for model simulation:
from .infinity import *
from .simulator import *

class EventReceiver(EventThread):

 def __init__(self, model, sim, core):

   self.model = model
   self.sim = sim

   self.startTime = time.time() # start-time of the simulation, wall-clock time

   EventThread.__init__(self, core) 

 def printAndWait(self, waitTime = None):
        if waitTime == None:
                waitTime = self.sim.waitTimeInterval
        if waitTime < INFINITY:
           print("wait %ss until next event (unless interrupted)" % str(waitTime))
           self.scheduleAfter(waitTime, self.performIntTransition)
        else:
           print("wait until interrupted") 

 def performIntTransition(self):
        #TODO fix with the real termination condition
        if self.sim.termination_time <= self.sim.clock[0]:
                # Simulation finished
                self.stop()
                return
        self.relativeTime = time.time() - self.startTime
        print("\nafter timeout: %s" % now())
        print("relative time %s" % str(self.relativeTime))
  
        self.sim.simulatorProcessEvent()
        self.printAndWait()
  
 def performExtTransition(self, event):
        self.relativeTime = time.time() - self.startTime
        if event == "": # denotes end of simulation
             print("EventReceiver got termination signal at time %s" % now())
             # Simulation finished
             self.stop()
             return
        else:
             print("interrupt '%s' at time %s" % (event, now()))
                
        (eventPort, eventValue) = event.split()
        self.sim.simulatorProcessEvent(eventPort, eventValue, self.relativeTime)
        self.printAndWait()

 def start(self):
        EventThread.start(self, self.func)

 def func(self):
   try:
     # The initial call
     # Only wait for the time itself, not the age
     self.printAndWait(self.sim.clock[0])
   except DEVSException as e:
     print(e)
  
class EventSender(EventThread):
 def __init__(self, gen, subsystem):
     self.gen = gen
     EventThread.__init__(self, subsystem) 

 def start(self):
     EventThread.start(self, self.run)

 def run(self):
    self.gen.run()
  
 """
 def run(self):
     while True:
       input = self.gen.getInput()
       self.notifyExternal(input)
       if self.gen.terminationCondition(input):
         self.stop()
         break
 """
  
def main(model, gen, sim, core = PythonThreads):
  if isinstance(core, TkinterThreads):
    # Tkinter must be run in the main loop
    import tkinter
    TkinterThreads.tk = tkinter.Tk()
    TkinterThreads.tk.withdraw()

  sim.send(None, Message((0, 0), 0))
  sim.clock = sim.getTimeNext()

  eventReceiver = EventReceiver(model, sim, core)
  EventThread.threadList.append(eventReceiver)
  eventReceiver.daemon = True
  eventReceiver.start()

  gen.setReceiver(eventReceiver)
  gen.startFileInput()

  eventSender = EventSender(gen, core)
  EventThread.threadList.append(eventSender)
  eventSender.daemon = True
  eventSender.start()

  if isinstance(core, TkinterThreads):
    TkinterThreads.tk.after(0, TkinterThreads.performActions)
    TkinterThreads.tk.mainloop()
  
  for evThread in EventThread.threadList:
    evThread.end()
  print("terminating application")
