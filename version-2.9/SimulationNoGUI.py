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

import __builtin__
from cStringIO import StringIO
from io import TextIOWrapper, BytesIO
import traceback

import gettext
_ = gettext.gettext

import InteractionSocket

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

def makeSimulation(master, T, socket_id, json_trace=True):
    """
    """
    import json
    from InteractionSocket import InteractionManager

    json_report = {'date':time.strftime("%c")}
    json_report['summary']  ="Simulation in batch mode with %s"%__builtin__.__dict__['DEFAULT_DEVS_DIRNAME']
    json_report['mode'] ='no-gui'
    json_report['time'] = T
    
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
        sim = runSimulation(master, T)
        thread = sim.Run()
        if socket_id != "":
            interactionManager = InteractionManager(socket_id=socket_id, simulation_thread=thread)
            interactionManager.start()

        first_time = time.time()
        
        while(thread.isAlive()):
            new_time = time.time()
            CPUduration = new_time - first_time
            if not json_trace:
                Printer(CPUduration)

        if interactionManager != None:
            interactionManager.stop()
            interactionManager.join()
    except:
        json_report['summary'] += " *** EXCEPTION raised in simulation ***"
        json_report['success'] = False
        json_report['info'] = traceback.format_exc()
        if interactionManager != None:
            interactionManager.stop()
            interactionManager.join()
        sys.stdout.write(json.dumps(json_report))
        raise

    json_report['summary'] += "...DEVS simulation completed!"

    json_report['duration'] = CPUduration
    
    json_report['output'] = []
    ### inform that data file has been generated
    for m in filter(lambda a: hasattr(a, 'fileName'), master.componentSet):
        for i in range(len(m.IPorts)):
            fn ='%s%s.dat'%(m.fileName,str(i))
            if os.path.exists(fn):
                json_report['output'].append({'filename':os.path.basename(fn), 'path':fn})
                
    ### Get live stream ids if exist :
    for m in filter(lambda a: hasattr(a, 'plotUrl'), master.componentSet):
        json_report['output'].append({'plotUrl':m.plotUrl})  
                
    sys.stdout.write(json.dumps(json_report))

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

        if self.master:
            from SimulationGUI import simulator_factory
            if not self.ntl:
                self.master.FINAL_TIME = float(self.time)

            self.thread = simulator_factory(self.master, self.selected_strategy, self.prof, self.ntl, self.verbose)

            return self.thread
