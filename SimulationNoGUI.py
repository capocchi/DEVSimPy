# -*- coding: utf-8 -*-

"""
Name: SimulationNoGUI.py
Brief description: Overwrite some methods to implement the no gui version of DEVSimPy and make simulation from dsp file
in batch mode
Author(s): A-T. Luciani <atluciani@univ-corse.fr>, capocchi <capocchi@univ-corse.fr>
Version:  1.0
Last modified: 2015.01.11 by L. Capocchi
GENERAL NOTES AND REMARKS:

GLOBAL VARIABLES AND FUNCTIONS:
"""

import os
import sys
import time
import threading


import __builtin__
from cStringIO import StringIO
from io import TextIOWrapper, BytesIO
import traceback

import gettext
_ = gettext.gettext

import InteractionSocket
import json
import pusher

from Decorators import hotshotit
from Patterns.Strategy import *

sys.path.append(os.path.join('Domain', 'Phidgets'))


class Printer:
    """
    Print things to stdout on one line dynamically
    """
    def __init__(self,data):
        sys.stdout.write("\r\x1b[K"+data.__str__())
        sys.stdout.flush()
        

def yes(prompt = 'Please enter Yes/No: '):
    while True:
        try:
            i = raw_input(prompt)
        except KeyboardInterrupt:
            return False
        if i.lower() in ('yes','y'): return True
        elif i.lower() in ('no','n'): return False
        

class SimuPusher():
    
    def __init__(self, simu_name):
        # app_id/key/secret might be linked to user TBC
        self.app_id = '178867'
        self.key    = 'c2d255356f53779e6020'
        self.secret = '9d41a54d45d25274df63'
        self.pusher = pusher.Pusher(app_id=self.app_id,key=self.key,secret=self.secret,ssl=True,port=443)
        self.channel = simu_name
    
    def push(self, event, data):
        self.pusher.trigger(self.channel, event, json.dumps(data))
    
class PrintPusher():
    def __init__(self, simu_name):
        pass
    
    def push(self, event, data):
        print(json.dumps(data))
    
def makeSimulation(master, T, simu_name="simu", is_remote=False, json_trace=True):
    """
    """
    from InteractionSocket import InteractionManager

    json_report = {'date':time.strftime("%c")}
    json_report['summary']  ="Simulation in batch mode with %s"%__builtin__.__dict__['DEFAULT_DEVS_DIRNAME']
    json_report['mode'] ='no-gui'
    json_report['time'] = T
    json_report['success'] = True
    json_report['output'] = []
    
    if not master : return False
    
    json_report['devs_instance'] = str(master)
    if isinstance(master, tuple):
        json_report['summary'] += "...DEVS instance not created: %s\n"%str(master)
        sys.stdout.write(json.dumps(json_report))
        return False
    
    else:
        json_report['summary'] += "...DEVS instance created"
        
    # Start Simulation               
    json_report['summary'] += "...Performing DEVS simulation"

    CPUduration = 0.0
    interactionManager = None
    try:
        if is_remote:
            # Pusher service for Simulation --> User communication
            simuPusher = SimuPusher(simu_name)
        else:
            simuPusher = PrintPusher(simu_name)
        
        ### Get live stream URL if exist :
        for m in filter(lambda a: hasattr(a, 'plotUrl'), master.componentSet):
            if m.plotUrl != '':
                json_report['output'].append({'label':m.name, 'plotUrl':m.plotUrl})          
        ### Get live stream URL if exist :
        for m in filter(lambda a: hasattr(a, 'pusherChannel'), master.componentSet):
            m.pusherChannel = simu_name
            json_report['output'].append({'label':m.name, 'pusherChannel':m.pusherChannel}) 
        # Send to user 
        simuPusher.push('live_streams', {'live_streams': json_report['output']})
        
        sim = runSimulation(master, T)
        thread = sim.Run()
        
        if is_remote:
            # Socket service for WebService <--> Simulation communication
            socket_id='socket_'+simu_name
            interactionManager = InteractionManager(socket_id=socket_id, simulation_thread=thread)
            interactionManager.start()

        first_real_time = time.time()
        progress = 0
        
        while(thread.isAlive()):
            new_real_time = time.time()
            CPUduration = new_real_time - first_real_time
            new_progress = 100.0*(thread.model.timeLast / T)
            if new_progress - progress > 5:
                progress = new_progress
                simuPusher.push('progress', {'progress':progress}) 
            if not json_trace:
                Printer(CPUduration)

        if interactionManager != None:
            interactionManager.stop()
            interactionManager.join()
            
        simuPusher.push('progress', {'progress':100}) 
        
    except:
        json_report['summary'] += " *** EXCEPTION raised in simulation ***"
        json_report['success'] = False
        sys.stderr.write(traceback.format_exc())
        if interactionManager != None:
            interactionManager.stop()
            interactionManager.join()
        with open(simu_name+'.report', 'w') as f:
            f.write(json.dumps(json_report))

    json_report['summary'] += "...DEVS simulation completed!"

    json_report['duration'] = CPUduration
    
    ### inform that data file has been generated
    json_report['output'] = []
    for m in filter(lambda a: hasattr(a, 'fileName'), master.componentSet):
        for i in range(len(m.IPorts)):
            fn ='%s%s.dat'%(m.fileName,str(i))
            if os.path.exists(fn):
                json_report['output'].append({'label':m.name+'_port_' + str(i),
                                              'filename':os.path.basename(fn)}) 
    for m in filter(lambda a: hasattr(a, 'plotUrl'), master.componentSet):
        json_report['output'].append({'label':m.name, 'plotUrl':m.plotUrl}) 
            
    with open(simu_name+'.report', 'w') as f:
            f.write(json.dumps(json_report))

    return True

class runSimulation:
    """
    """

    def __init__(self, master, time):
        """ Constructor.
        """

        # local copy
        self.master = master
        self.time = time

        ### No time limit simulation (defined in the builtin dico from .devsimpy file)
        self.ntl = __builtin__.__dict__['NTL']

        # simulator strategy
        self.selected_strategy = DEFAULT_SIM_STRATEGY
        self.dynamic_structure_flag = __builtin__.__dict__['DYNAMIC_STRUCTURE']
        self.real_time_flag = __builtin__.__dict__['REAL_TIME']
         
        ### profiling simulation with hotshot
        self.prof = False

        self.verbose = False

        # definition du thread, du timer et du compteur pour les % de simulation
        self.thread = None
        self.count = 10.0
        self.stdioWin = None

    ###
    def Run(self):
        """ run simulation
        """

        assert(self.master is not None)
        ### pour prendre en compte les simulations multiples sans relancer un SimulationDialog
        ### si le thread n'est pas lanc� (pas pendant un suspend)
        # if self.thread is not None and not self.thread.thread_suspend:
        diagram = self.master.getBlockModel()
        # diagram.Clean()
        # print self.master
        ################################################################################################################
        ######### To Do : refaire l'enregistrement du chemin d'enregistrements des resultats du to_disk ###################
        for m in self.master.componentSet:
            if str(m)=='To_Disk':
                dir_fn = os.path.dirname(diagram.last_name_saved).replace('\t','').replace(' ','')
                label = m.getBlockModel()
                m.fileName = os.path.join(dir_fn,"%s_%s"%(os.path.basename(diagram.last_name_saved).split('.')[0],os.path.basename(m.fileName)))
        ################################################################################################################
        ################################################################################################################
        #print __builtin__.__dict__
        if self.master:
            #from SimulationGUI import simulator_factory
            if not self.ntl:
                self.master.FINAL_TIME = float(self.time)
            self.thread = simulator_factory(self.master, self.selected_strategy, self.prof, self.ntl, self.verbose, self.dynamic_structure_flag, self.real_time_flag)

            return self.thread

def simulator_factory(model, strategy, prof, ntl, verbose, dynamic_structure_flag, real_time_flag):
	""" Preventing direct creation for Simulator
        disallow direct access to the classes
	"""

	### find the correct simulator module depending on the
	for pydevs_dir, filename in __builtin__.__dict__['DEVS_DIR_PATH_DICT'].items():
		if pydevs_dir == __builtin__.__dict__['DEFAULT_DEVS_DIRNAME']:
			from DEVSKernel.PyDEVS.simulator import Simulator as BaseSimulator

	class Simulator(BaseSimulator):
		"""
		"""
		###
		def __init__(self, model):
			"""Constructor.
			"""

			BaseSimulator.__init__(self, model)

			self.model = model
			self.__algorithm = SimStrategy1(self)

		def simulate(self, T = sys.maxint):
			return self.__algorithm.simulate(T)

		def getMaster(self):
			return self.model

		def setMaster(self, model):
			self.model = model

		def setAlgorithm(self, s):
			self.__algorithm = s

		def getAlgorithm(self):
			return self.__algorithm

	class SimulationThread(threading.Thread, Simulator):
		"""
			Thread for DEVS simulation task
		"""

		def __init__(self, model = None, strategy = '', prof = False, ntl = False, verbose=False, dynamic_structure_flag=False, real_time_flag=False):
			""" Constructor.
			"""
			threading.Thread.__init__(self)
			Simulator.__init__(self, model)

			### local copy
			self.strategy = strategy
			self.prof = prof
			self.ntl = ntl
			self.verbose = verbose
			self.dynamic_structure_flag = dynamic_structure_flag
			self.real_time_flag = real_time_flag

			self.end_flag = False
			self.thread_suspend = False
			self.sleep_time = 0.0
			self.thread_sleep = False
			self.cpu_time = -1

			self.start()

		@hotshotit
		def run(self):
			""" Run thread
			"""

			### define the simulation strategy
			args = {'simulator':self}
			### TODO: isinstance(self, PyDEVSSimulator)
			if DEFAULT_DEVS_DIRNAME == "PyDEVS":
				cls_str = eval(PYDEVS_SIM_STRATEGY_DICT[self.strategy])
			else:
				cls_str = eval(PYPDEVS_SIM_STRATEGY_DICT[self.strategy])

			self.setAlgorithm(apply(cls_str, (), args))

			while not self.end_flag:
				### traceback exception engine for .py file
				try:
					self.simulate(self.model.FINAL_TIME)
				except Exception, info:
					self.terminate(error=True, msg=sys.exc_info())

		def terminate(self, error = False, msg = None):
			""" Thread termination routine
				param error: False if thread is terminate without error
				param msg: message to submit
			"""

			if not self.end_flag:
				if error:

					###for traceback
					etype = msg[0]
					evalue = msg[1]
					etb = traceback.extract_tb(msg[2])
					sys.stderr.write('Error in routine: your routine here\n')
					sys.stderr.write('Error Type: ' + str(etype) + '\n')
					sys.stderr.write('Error Value: ' + str(evalue) + '\n')
					sys.stderr.write('Traceback: ' + str(etb) + '\n')

					### only for displayed application (-nogui)
					#if wx.GetApp():
					#	wx.CallAfter(Publisher.sendMessage, "error", msg)
						### error sound
					#	wx.CallAfter(playSound, SIMULATION_ERROR_SOUND_PATH)

				else:
					for m in filter(lambda a: hasattr(a, 'finish'), self.model.componentSet):
						### call finished method
						if __builtin__.__dict__['GUI_FLAG']:
							Publisher.sendMessage('%d.finished'%(id(m)))
						else:
							m.finish(None)

					### only for displayed application (-nogui)
					#if wx.GetApp() : wx.CallAfter(playSound, SIMULATION_SUCCESS_SOUND_PATH)

			self.end_flag = True

		def set_sleep(self, sleeptime):
			self.thread_sleep = True
			self._sleeptime = sleeptime

		def suspend(self):

			#main_thread = threading.currentThread()
			#for t in threading.enumerate():
			#	t.thread_suspend = True

			self.thread_suspend = True

		def resume_thread(self):
			self.thread_suspend = False

	return SimulationThread(model, strategy, prof, ntl, verbose, dynamic_structure_flag, real_time_flag)
