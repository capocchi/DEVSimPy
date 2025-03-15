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
import traceback
import json
# import pusher

import gettext
_ = gettext.gettext


path = os.path.join('Domain')
if path not in sys.path:
    sys.path.append(path)

class Printer:
    """
    Print things to stdout on one line dynamically
    """
    def __init__(self,data):
        sys.stdout.write("\r\x1b[K"+data.__str__())
        sys.stdout.flush()
        

# def yes(prompt:str = 'Please enter Yes/No: ')->bool:
#     while True:
#         try:
#             i = input(prompt)
#         except KeyboardInterrupt:
#             return False
#         if i.lower() in ('yes','y'): return True
#         elif i.lower() in ('no','n'): return False  

# class SimuPusher():
    
#     def __init__(self, simu_name):
#         # app_id/key/secret might be linked to user TBC
#         self.app_id = '178867'
#         self.key    = 'c2d255356f53779e6020'
#         self.secret = '9d41a54d45d25274df63'

#         self.pusher = pusher.Pusher(app_id=self.app_id, key=self.key, secret=self.secret, ssl=True, port=443)
#         self.channel = simu_name
    
#     def push(self, event, data):
#         self.pusher.trigger(self.channel, event, json.dumps(data))
    
# class PrintPusher():
#     def __init__(self, simu_name):
#         pass
    
#     def push(self, event, data):
#         sys.stdout.write((json.dumps(data)))

def makeSimulation(master, T, simu_name:str="simu", is_remote:bool=False, stdout:bool=False):
    """
    """

    from InteractionSocket import InteractionManager

    json_report = {'date': time.strftime("%c")}
    json_report['summary'] = f"Simulation in batch mode with {DEFAULT_DEVS_DIRNAME}"
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
        
        # # Pusher service for Simulation --> User communication
        # simuPusher = SimuPusher(simu_name) if is_remote else PrintPusher(simu_name)
        
        # ### Get live stream URL if exist :
        # for m in [a for a in master.getComponentSet() if hasattr(a, 'plotUrl') and a.plotUrl != '']:
        #     json_report['output'].append({'label':m.name, 'plotUrl':m.plotUrl})     
        
        # ### Get live stream URL if exist :
        # for m in [a for a in master.getComponentSet() if hasattr(a, 'pusherChannel')]:
        #     m.pusherChannel = simu_name
        #     json_report['output'].append({'label':m.name, 'pusherChannel':m.pusherChannel}) 
        
        # # Send to user 
        # simuPusher.push('live_streams', {'live_streams': json_report['output']})
        
        sim = runSimulation(master, T)
        thread = sim.Run()
        
        if is_remote:
            # Socket service for WebService <--> Simulation communication
            socket_id='socket_'+simu_name
            interactionManager = InteractionManager(socket_id=socket_id, simulation_thread=thread)
            interactionManager.start()

        # first_real_time = time.time()
        progress = 0
        
        if not NTL:
            is_alive = thread.isAlive if hasattr(thread, 'isAlive') else thread.is_alive
            while is_alive():
                try:
                    # new_real_time = time.time()
                    # CPUduration = new_real_time - first_real_time
                    new_progress = 100.0 * (float(thread.model.timeLast) / float(T)) if float(T) != 0 else 100.0
                    
                    if new_progress - progress > 5:
                        progress = new_progress
                        # Print progress to debug
                        if stdout:
                            Printer(f"Progress: {progress:.2f}%\n")
                        else:
                            sys.stdout.flush()
                        # simuPusher.push('progress', {'progress':progress})

                    # if not json_trace:
                        # Printer(CPUduration)
                        
                    # Add little wait to avoid the CPU overhead
                    time.sleep(0.001)
                except Exception as e:
                    print(f"Error in the simulation loop : {e}")
                    break

            if interactionManager != None:
                interactionManager.stop()
                interactionManager.join()

            if stdout:
                Printer(f"Progress: 100%")    
            # simuPusher.push('progress', {'progress':100})
        
    except:
        json_report['summary'] += " *** EXCEPTION raised in simulation ***"
        json_report['success'] = False
        sys.stderr.write(traceback.format_exc())
        if interactionManager != None:
            interactionManager.stop()
            interactionManager.join()
        ### if sim_name is in param, a log file is writed on the logs dir
        if simu_name:
            os.makedirs('logs', exist_ok=True)
            with open(os.path.join('logs', simu_name+'.report'), 'w') as f:
                    f.write(json.dumps(json_report))

    json_report['summary'] += "...DEVS simulation completed!"

    json_report['duration'] = CPUduration

    # ### inform that data file has been generated
    # json_report['output'] = []
    # for m in [a for a in master.getComponentSet() if hasattr(a, 'fileName')]:
    #     for i in range(len(m.IPorts)):
    #         fn ='%s%s.dat'%(m.fileName,str(i))
    #         if os.path.exists(fn):
    #             json_report['output'].append({'label':m.name+'_port_' + str(i),
    #                                           'filename':os.path.basename(fn)}) 
    # for m in [a for a in master.getComponentSet() if hasattr(a, 'plotUrl')]:
    #     json_report['output'].append({'label':m.name, 'plotUrl':m.plotUrl}) 
            
    # ### if sim_name is in param, a log file is writed on the logs dir
    # if simu_name:
    #     os.makedirs('logs', exist_ok=True)
    #     with open(os.path.join('logs',simu_name+'.report'), 'w') as f:
    #             f.write(json.dumps(json_report))
    
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
        self.ntl = NTL

        # simulator strategy
        self.selected_strategy = DEFAULT_SIM_STRATEGY
        self.dynamic_structure_flag = DYNAMIC_STRUCTURE
        self.real_time_flag = REAL_TIME
         
        ### profiling simulation
        self.prof = False

        self.verbose = False

        # definition du thread, du timer et du compteur pour les % de simulation
        self.thread = None
        self.count = 10.0
        self.stdioWin = None

    ###
    def Run(self):
        """ run simulation.
        """

        assert(self.master is not None)

        ### pour prendre en compte les simulations multiples sans relancer un SimulationDialog
        ### si le thread n'est pas lanc� (pas pendant un suspend)
        # if self.thread is not None and not self.thread.thread_suspend:
        diagram = self.master.getBlockModel()
        
        ################################################################################################################
        ######### To Do : refaire l'enregistrement du chemin d'enregistrements des resultats du to_disk ###################
        for m in self.master.getComponentSet():
            if str(m)=='To_Disk':
                dir_fn = os.path.dirname(diagram.last_name_saved).replace('\t','').replace(' ','')
                # label = m.getBlockModel()
                m.fileName = os.path.join(dir_fn,"%s_%s"%(os.path.basename(diagram.last_name_saved).split('.')[0],os.path.basename(m.fileName)))
        ################################################################################################################
        ################################################################################################################
        if self.master:
            from Patterns import simulator_factory
            if not self.ntl:
                self.master.FINAL_TIME = float(self.time)
            
            self.thread = simulator_factory(self.master, self.selected_strategy, self.prof, self.ntl, self.verbose, self.dynamic_structure_flag, self.real_time_flag)

            return self.thread
