# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# Strategy.py --- Strategy Pattern
#                     --------------------------------
#                            Copyright (c) 2020
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 1.0                                      last modified:  03/15/20
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GLOBAL VARIABLES AND FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import sys
import time
import copy
import weakref
import heapq
import threading
import importlib
import json

import inspect
if not hasattr(inspect, 'getargspec'):
    inspect.getargspec = inspect.getfullargspec
    
from PluginManager import PluginManager #trigger_event
from Utilities import getOutDir
from DEVSKernel.KAFKADEVS.simulator import Simulator
from DEVSKernel.KAFKADEVS.coordinator import KafkaCoordinator 

import logging
logger = logging.getLogger('SimStrategyKafka')

import builtins
import re
import os

### import the DEVS module depending on the selected DEVS package in DEVSKernel directory
for pydevs_dir, path in getattr(builtins,'DEVS_DIR_PATH_DICT').items():
    if os.path.exists(path):
        ### split from DEVSKernel string and replace separator with point
        d = re.split("DEVSKernel", path)[-1].replace(os.sep, '.')

        ### for py 3.X
        import importlib
        exec("%s = importlib.import_module('DEVSKernel%s.DEVS')"%(pydevs_dir,d))
    
    #exec("import DEVSKernel%s.DEVS as %s"%(d,pydevs_dir))

#import DEVSKernel.PyDEVS.DEVS as PyDEVS
#import DEVSKernel.PyPDEVS.DEVS as PyPDEVS

def getFlatImmChildrenList(model, flat_imm_list:list = [])->list:
    """ Set priority flat list.
    """

    for m in model.immChildren:
        if isinstance(m, PyDEVS.AtomicDEVS):
            flat_imm_list.append(m)
        elif isinstance(m, PyDEVS.CoupledDEVS):
            getFlatImmChildrenList(m, flat_imm_list)

    return flat_imm_list

def getFlatPriorityList(model, flat_priority_list:list = [])->list:
    """ Set priority flat list.
    """

    ### if priority list never edited, priority is componentList order.
    L = model.PRIORITY_LIST if hasattr(model, 'PRIORITY_LIST') and model.PRIORITY_LIST else model.componentSet

    for m in L:
        if isinstance(m, PyDEVS.AtomicDEVS):
            flat_priority_list.append(m)
        elif isinstance(m, PyDEVS.CoupledDEVS):
            getFlatPriorityList(m, flat_priority_list)
        else:
            sys.stdout.write(_('Unknow model'))

    return flat_priority_list

def HasActiveChild(L:list)->bool:
    """ Return true if a children of master is active.
    """
    return L and True in [a.timeNext != INFINITY for a in L]

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# CLASS DEFINITION
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

class SimStrategy:
    """ Strategy abstract class or interface.
    """

    def __init__(self, simulator=None):
        """ Constructor.
        """
        self._simulator = simulator

    def simulate(self, T = 100000000):
        """ Simulate abstract method
        """
        pass

class SimStrategy1(SimStrategy):
    """ Original strategy for PyDEVS simulation.
    """

    def __init__(self, simulator = None):
        """ Constructor.
        """
        SimStrategy.__init__(self, simulator)

    def simulate(self, T = 100000000):
        """Simulate the model (Root-Coordinator).
        """

        clock = 0.0
        model = self._simulator.getMaster()
        send = self._simulator.send

        # Initialize the model --- set the simulation clock to 0.
        send(model, (0, [], 0))

        # Main loop repeatedly sends $(*,\,t)$ messages to the model's root DEVS.
        while clock <= T:

            send(model, (1, model.immChildren, clock))
            clock = model.myTimeAdvance

        self._simulator.terminate()

class SimStrategy2(SimStrategy):
    """ Strategy for DEVSimPy hierarchical simulation.

        This strategy is based on Zeigler's hierarchical simulation algorithm based on atomic and coupled Solver.
    """

    def __init__(self, simulator=None):
        """ Constructor.
        """
        SimStrategy.__init__(self, simulator)

    def simulate(self, T = 100000000):
        """ Simulate for T
        """

        master = self._simulator.getMaster()
        send = self._simulator.send
        #clock = master.myTimeAdvance

        # Initialize the model --- set the simulation clock to 0.
        send(master, (0, [], 0))

        clock = master.myTimeAdvance

        ### ref to cpu time evaluation
        t_start = time.time()

        ### if suspend, we could store the future ref
        old_cpu_time = 0

        ### stoping condition depend on the ntl (no time limit for the simulation)
        condition = lambda clock: HasActiveChild(getFlatImmChildrenList(master, [])) if self._simulator.ntl else clock <= T

        # Main loop repeatedly sends $(*,\,t)$ messages to the model's root DEVS.
        while condition(clock) and self._simulator.end_flag == False:

            ##Optional sleep
            if self._simulator.thread_sleep:
                time.sleep(self._simulator._sleeptime)

            elif self._simulator.thread_suspend:
                ### Optional suspend
                while self._simulator.thread_suspend:
                    time.sleep(1.0)
                    old_cpu_time = self._simulator.cpu_time
                    t_start = time.time()

            else:
                # The SIM_VERBOSE event occurs
                PluginManager.trigger_event("SIM_VERBOSE", clock = clock)

                send(master, (1, {}, clock))

                clock = master.myTimeAdvance

                self._simulator.cpu_time = old_cpu_time + (time.time()-t_start)

        self._simulator.terminate()

###--------------------------------------------------------------------Strategy

### decorator for poke
def Post_Poke(f):
    def wrapper(*args):
        p = args[0]
        v = args[1]
        r = f(*args)
        #parallel_ext_transtion_manager(p)
        serial_ext_transtion_manager(p)
        return r
    return wrapper


def parallel_ext_transtion_manager(p):

    hosts = p.weak.GetHosts()

    ###----------------------------------------------------------------------------------------
    ### thread version
    threads = []

    for val in hosts:
        t = threading.Thread(target=val[2], args=(val[1],))
        threads.append(t)
        t.start()

    #### Wait for all worker threads to finish
    for thread in threads:
        thread.join()
    ###-----------------------------------------------------------------------------------------

    ### clear output port (then input port of hosts) of model in charge of activate hosts
    p.weak.SetValue(None)

def serial_ext_transtion_manager(p):
    """ achieve external transition function of host from p
     """


    hosts = p.weak.GetHosts()

    ### serial version
    for val in hosts:
        val[2](*(val[1],))

    ### clear output port (then input port of hosts) of model in charge of activate hosts
    p.weak.SetValue(None)

###
@Post_Poke
def poke(p, v):
    p.weak.SetValue(v)

    ### just for plugin verbose
    p.host.myOutput[p] = v

###
def peek(p):
    return copy.deepcopy(p.weak.GetValue())

def peek_all(self):
    """Retrives messages from all input port {\tt p}.
    """
    return [a for a in [(p, peek(p)) for p in self.IPorts] if a[1]!=None]

###
class WeakValue:
    """ Weak Value class
    """
    def __init__(self, port=None):
        """ Constructor
        """

        ### port of weak value
        self.port = port

        ### value and time of msg
        self._value = None
        self._host = []

    def SetValue(self, v):
        """ Set value and time
        """

        self._value = v

    def GetValue(self):
        """ Get value at time t
        """

        return self._value

    def AddHosts(self,p):
        """ Make host list composed by tuple of priority, model and transition function.
        """
        model = p.host
        v = (model.priority/10000.0, model, execExtTransition)
        if v not in self._host and hasattr(model, 'priority'):
            self._host.append(v)

    def GetHosts(self):
        """ Return the host.
        """
        return self._host

def FlatConnection(p1, p2):
    """ Make flat connection.
    """

    if isinstance(p1.host, PyDEVS.AtomicDEVS) and isinstance(p2.host, PyDEVS.AtomicDEVS):
        if isinstance(p1, PyDEVS.OPort) and isinstance(p2, PyDEVS.IPort):
            if not isinstance(p1.weak, weakref.ProxyType):
                wr = weakref.proxy(p1.weak)
                p2_weak_old = p2.weak
                if not isinstance(p2.weak, weakref.ProxyType):
                    p2.weak = wr
                else:
                    p1.weak = p2.weak
            else:
                p2.weak = p1.weak

            ## build hosts list in WeakValue class
            p1.weak.AddHosts(p2)

    elif isinstance(p1.host, PyDEVS.AtomicDEVS) and isinstance(p2.host, PyDEVS.CoupledDEVS):
        if isinstance(p1, PyDEVS.OPort):
            ### update outLine port list removing ports of coupled model
            p1.outLine = [a for a in p1.outLine if isinstance(a.host, PyDEVS.AtomicDEVS)]
            for p in p2.outLine:
                if not hasattr(p, 'weak'): setattr(p, 'weak', WeakValue(p))
                FlatConnection(p1, p)

    elif isinstance(p1.host, PyDEVS.CoupledDEVS) and isinstance(p2.host, PyDEVS.AtomicDEVS):
        if isinstance(p1, PyDEVS.OPort) and isinstance(p2, PyDEVS.IPort):
            for p in p1.inLine:
                if not hasattr(p, 'weak'): setattr(p, 'weak', WeakValue(p))
                FlatConnection(p, p2)

    elif isinstance(p1.host, PyDEVS.CoupledDEVS) and isinstance(p2.host, PyDEVS.CoupledDEVS):
        if isinstance(p1, PyDEVS.OPort) and isinstance(p2, PyDEVS.IPort):
            for p in p1.inLine:
                for pp in p2.outLine:
                    FlatConnection(p, pp)

def setAtomicModels(atomic_model_list, ts):
    """ Set atomic DEVS model flat list and initialize it.
    """

    for i,m in enumerate(atomic_model_list):
        m.elapsed = m.timeLast = m.timeNext = 0.0
        m.myTimeAdvance = m.timeAdvance()
        m.poke = poke
        m.peek = peek
        funcType = type(PyDEVS.AtomicDEVS.peek_all)
        m.peek_all = funcType(peek_all, m, PyDEVS.AtomicDEVS)
        setattr(m, 'priority', i)
        setattr(m, 'ts', ts())

    for m in atomic_model_list:
        for p1 in m.OPorts:
            if not hasattr(p1, 'weak'): setattr(p1, 'weak', WeakValue(p1))
            for p2 in p1.outLine:
                if not hasattr(p2, 'weak'): setattr(p2, 'weak', WeakValue(p2))

                #p2.weak = p1.weak
                FlatConnection(p1,p2)

        for p1 in m.IPorts:
            if not hasattr(p1, 'weak'): setattr(p1, 'weak', WeakValue(p1))
            for p2 in p1.inLine:
                if not hasattr(p2, 'weak'): setattr(p2, 'weak', WeakValue(p2))

                #p1.weak = p2.weak
                #FlatConnection(p1,p2)

###
def execExtTransition(m):
    """
    """

    ts =  m.ts.Get()

    m.elapsed =ts - m.timeLast

    m.extTransition()

    m.timeLast = ts
    m.myTimeAdvance = m.timeAdvance()
    m.timeNext = m.timeLast+m.myTimeAdvance
    if m.myTimeAdvance != INFINITY: m.myTimeAdvance += ts
    m.elapsed = 0.0

    # The SIM_VERBOSE event occurs
    PluginManager.trigger_event("SIM_VERBOSE", model=m, msg=1)
    PluginManager.trigger_event("SIM_BLINK", model=m, msg=[{}])
    PluginManager.trigger_event("SIM_TEST", model=m, msg=[{}])

    return m

###
def execIntTransition(m):
    """
    """

    ts =  m.ts.Get()

    if m.timeNext != INFINITY:
        m.outputFnc()

    m.elapsed = ts - m.timeLast

    m.intTransition()
    m.timeLast = ts
    m.myTimeAdvance = m.timeAdvance()
    m.timeNext = m.timeLast+m.myTimeAdvance
    if m.myTimeAdvance != INFINITY: m.myTimeAdvance += ts
    m.elapsed = 0.0

    # The SIM_VERBOSE event occurs
    PluginManager.trigger_event("SIM_VERBOSE", model=m, msg=0)
    PluginManager.trigger_event("SIM_BLINK", model=m, msg=[1])
    PluginManager.trigger_event("SIM_TEST", model=m, msg=[1])

class Clock(object):
    def __init__(self, time):
        self._val = time
    def Get(self):
        return self._val
    def Set(self, val):
        self._val = val

###
class SimStrategy3(SimStrategy):
    """ Strategy 3 for DEVSimPy thread-based direct-coupled simulation

        The simulate methode use heapq tree-like data library to manage model priority for activation
        and weak library to simplify the connexion algorithm between port.
        The THREAD_LIMIT control the limit of models to thread (default 5).
        The performance of this algorithm depends on the THREAD_LIMIT number and the number of coupled models.
    """

    def __init__(self, simulator=None):
        """ Cosntructor.
        """

        SimStrategy.__init__(self, simulator)

        ### simulation time
        self.ts = Clock(0.0)

        ### master model and flat list of atomic model
        self.master = self._simulator.getMaster()
        self.flat_priority_list = getFlatPriorityList(self.master, [])

        ### init all atomic model from flat list
        setAtomicModels(self.flat_priority_list, weakref.ref(self.ts))

        ### udpate the componentSet list of master (that no longer contains coupled model)
        self.master.componentSet = self.flat_priority_list


    def simulate(self, T = 100000000):
        """ Simulate for T.
        """

        ### ref to cpu time evaluation
        t_start = time.time()
        ### if suspend, we could store the future ref
        old_cpu_time = 0

        ### stopping condition depend on the ntl (no time limit for the simulation)
        condition = lambda clk: HasActiveChild(getFlatPriorityList(self.master, [])) if self._simulator.ntl else clk <= T

        ### simulation time and list of flat models ordered by devs priority
        L = [m.myTimeAdvance for m in self.flat_priority_list if m.myTimeAdvance < INFINITY] or [INFINITY]
        self.ts.Set(min(L))
        formated_priority_list = [(1+i/10000.0, m, execIntTransition) for i,m in enumerate(self.flat_priority_list)]

        while condition(self.ts.Get()) and self._simulator.end_flag == False:

            ### Optional sleep
            if self._simulator.thread_sleep:
                time.sleep(self._simulator._sleeptime)

            elif self._simulator.thread_suspend:
            ### Optional suspend
                while self._simulator.thread_suspend:
                    time.sleep(1.0)
                    old_cpu_time = self._simulator.cpu_time
                    t_start = time.time()

            else:

                ### The SIM_VERBOSE event occurs
                PluginManager.trigger_event("SIM_VERBOSE", self.master, None, clock = self.ts.Get())

                ### tree-like data structure ordered by devsimpy priority
                priority_scheduler = [a for a in formated_priority_list if self.ts.Get() == a[1].myTimeAdvance]
                heapq.heapify(priority_scheduler)

                ### TODO: execute with process of model are parallel !
                while(priority_scheduler):
                    ### get most priority model and apply its internal transition
                    priority, model, transition_fct = heapq.heappop(priority_scheduler)
                    transition_fct(*(model,))

                ### update simulation time
                self.ts.Set(min([m.myTimeAdvance for m in self.flat_priority_list]))

                ### just for progress bar
                self.master.timeLast = self.ts.Get() if self.ts.Get() != INFINITY else self.master.timeLast
                self._simulator.cpu_time = old_cpu_time + (time.time()-t_start)

        self._simulator.terminate()

# A. Simulate forever.
#    The termination_condition function never returns True.
#
def terminate_never(model, clock):
    return False

class SimStrategy4(SimStrategy):
    """ classic strategy for PyPDEVS simulation
        setClassicDEVS is True and confTransition in disabled
    """

    def __init__(self, simulator = None):
        SimStrategy.__init__(self, simulator)

    def simulate(self, T = 100000000):
        """Simulate the model (Root-Coordinator).
        """		
                
        path = getattr(builtins, 'DEVS_DIR_PATH_DICT')[DEFAULT_DEVS_DIRNAME]
        d = re.split("DEVSKernel", path)[-1].replace(os.sep, '.')
        simulator = importlib.import_module("DEVSKernel%s.simulator"%d)
        #exec("from DEVSKernel%s.simulator import Simulator"%d)

        S = simulator.Simulator(self._simulator.model)

        ### old version of PyPDEVS
        if len(inspect.getargspec(S.simulate).args) > 1:

            kwargs = {'verbose':True}

            ### TODO
            if self._simulator.ntl:
                kwargs['termination_condition'] = terminate_never
            else:
                kwargs['termination_time'] = T

            S.simulate(**kwargs)

        ### new version of PyPDEVS (due to the number of config param which is growing)
        else:

            ### see simconfig.py to have informations about setters

            ### verbose manager, if None print are displayed in stdout, else in the out/verbose.txt file
            if self._simulator.verbose:
                S.setVerbose(None)
            else:
                out_dir = os.path.join(DEVSIMPY_PACKAGE_PATH, 'out')
                if not os.path.exists(out_dir):
                    os.mkdir(out_dir)

                verbose_file = os.path.join(getOutDir(), 'verbose.txt')
                S.setVerbose(verbose_file)

            ### TODO
            if self._simulator.ntl:
                S.setTerminationCondition(terminate_never)
            else:
                S.setTerminationTime(T)

            S.setClassicDEVS(self.SetClassicDEVSOption())

            ### dynamic structure for local PyPDEVS simulation
            S.setDSDEVS(self._simulator.dynamic_structure_flag)
            
            #S.setMemoization(self._simulator.memoization_flag)

            ### real time simulation
            if self._simulator.real_time_flag:
                S.setRealTime(self._simulator.real_time_flag)
                S.setRealTimeInputFile(None)
                #S.setRealTimePorts(refs)
                S.setRealTimePlatformThreads()

            S.simulate()

        self._simulator.terminate()

    def SetClassicDEVSOption(self):
        return True

class SimStrategy5(SimStrategy4):
    """ Parallel strategy for PyPDEVS simulation
        setClassicDEVS is False and confTransition in enabled
    """

    def __init__(self, simulator = None):
        """ Constructor.
        """
        SimStrategy4.__init__(self, simulator)

    def SetClassicDEVSOption(self):
        return False

class SimStrategyKafka(SimStrategy):
    def __init__(self, simulator=None):
        """Initialize Kafka simulation strategy"""
        SimStrategy.__init__(self, simulator)
        
        # Initialize simulation time
        self.ts = Clock(0.0)
        
        # Get master model 
        self.master = self._simulator.getMaster()
        logger.info("Master model initialized: %s", self.master.name)
        
        # Get flat list of atomic models
        self.flat_priority_list = []
        self._collect_atomic_models(self.master)
        logger.info("Found %d atomic models", len(self.flat_priority_list))
        
        # Initialize all atomic models with time references
        self._initialize_atomic_models()
        
        # Create coordinator
        self.coordinator = KafkaCoordinator(
            model=self.master,
            clock=weakref.ref(self.ts)
        )

        # Initialize all atomic models with time references
        for model in self.flat_priority_list:
            model.timeLast = 0.0
            model.timeNext = model.timeAdvance()

        # Store model connections
        self.connections = {}
        self._build_connections(self.master)
        logger.info("Built connection map: %s", self.connections)

    def _initialize_atomic_models(self):
        """Initialize atomic models with time references"""
        for model in self.flat_priority_list:
            # Set time reference
            model.timeLast = 0.0
            model.myTimeAdvance = model.timeAdvance()
            model.clock = weakref.ref(self.ts)
            
            # Initialize model state
            if hasattr(model, 'initPhase'):
                model.initPhase()
            
            logger.debug("Initialized atomic model: %s", model.name)
    
    
    def _build_connections(self, model):
        """Build map of model connections"""
        self.connections = {}
        
        # Handle IC (Internal Couplings)
        for coupling in model.IC:
            # Extract source and destination from coupling
            (src, dst) = coupling
            src_model, src_port = src
            dst_model, dst_port = dst
            
            if src_model.name not in self.connections:
                self.connections[src_model.name] = []
                
            self.connections[src_model.name].append({
                'target': dst_model.name,
                'src_port': src_port,
                'dst_port': dst_port
            })
            logger.debug("Added IC connection: %s.%s -> %s.%s", 
                        src_model.name, src_port.name,
                        dst_model.name, dst_port.name)

        # Handle EIC (External Input Couplings) 
        for coupling in model.EIC:
            (src, dst) = coupling
            _, src_port = src
            dst_model, dst_port = dst
            
            model_name = model.name
            if model_name not in self.connections:
                self.connections[model_name] = []
                
            self.connections[model_name].append({
                'target': dst_model.name,
                'src_port': src_port,
                'dst_port': dst_port
            })
            logger.debug("Added EIC connection: %s.%s -> %s.%s",
                        model_name, src_port.name, 
                        dst_model.name, dst_port.name)

        # Handle EOC (External Output Couplings)
        for coupling in model.EOC:
            (src, dst) = coupling
            src_model, src_port = src
            _, dst_port = dst
            
            if src_model.name not in self.connections:
                self.connections[src_model.name] = []
                
            self.connections[src_model.name].append({
                'target': model.name,
                'src_port': src_port,
                'dst_port': dst_port
            })
            logger.debug("Added EOC connection: %s.%s -> %s.%s",
                        src_model.name, src_port.name,
                        model.name, dst_port.name)
        
        logger.info("Built connection map with %d source models", len(self.connections))

    def _collect_atomic_models(self, model):
        """Recursively collect atomic models"""
        if not hasattr(model, 'componentSet'):
            self.flat_priority_list.append(model)
            logger.debug("Added atomic model: %s", model.name)
            return
            
        for component in model.componentSet:
            if hasattr(component, 'componentSet'):
                self._collect_atomic_models(component)
            else:
                self.flat_priority_list.append(component)
                logger.debug("Added atomic model: %s", component.name)

    def simulate(self, T=100000000):
        """Main simulation loop"""
        if not self.flat_priority_list:
            logger.error("No atomic models found - cannot simulate")
            return
            
        logger.info("Starting simulation with %d models", len(self.flat_priority_list))
        
        # Start coordinator
        coord_thread = threading.Thread(target=self.coordinator.start)
        coord_thread.daemon = True
        coord_thread.start()
        
        # Initialize timing
        t_start = time.time()
        old_cpu_time = 0
        
        while (self.ts.Get() <= T or self._simulator.ntl) and not self._simulator.end_flag:
            try:
                current_time = self.ts.Get()
                
                # Find imminent models
                imm_models = []
                next_ta = INFINITY
                
                for model in self.flat_priority_list:
                    if abs(model.timeNext - current_time) < 0.000001:
                        imm_models.append(model)
                    elif model.timeNext > current_time and model.timeNext < next_ta:
                        next_ta = model.timeNext
                
                # Process imminent models
                if imm_models:
                    for model in imm_models:
                        logger.info("Processing model %s at time %f", model.name, current_time)
                        
                        # Get output
                        output = model.outputFnc()
                        if output and model.name in self.connections:
                            # Route output to connected models via Kafka
                            for connection in self.connections[model.name]:
                                if connection['src_port'] in output:
                                    message = {
                                        'type': 'output',
                                        'time': current_time,
                                        'port': connection['dst_port'].name,
                                        'data': output[connection['src_port']]
                                    }
                                    
                                    # Produce to source model's output topic
                                    self.coordinator.producer.produce(
                                        f'devs.{model.name}.out',
                                        json.dumps(message).encode('utf-8')
                                    )
                                    
                                    # Produce to destination model's input topic
                                    self.coordinator.producer.produce(
                                        f'devs.{connection["target"]}.in',
                                        json.dumps(message).encode('utf-8')
                                    )
                                    
                                    logger.debug("Routed message from %s to %s", 
                                               model.name, connection['target'])
                        
                        # Internal transition
                        model.intTransition()
                        model.timeLast = current_time
                        model.timeNext = current_time + model.timeAdvance()
                        logger.info("Model %s completed internal transition", model.name)
                
                # Update simulation time
                if next_ta != INFINITY:
                    self.ts.Set(next_ta)
                    logger.info("Advanced simulation to time %f", next_ta)
                else:
                    logger.info("No more events - simulation complete")
                    break
                    
                # Handle simulation control
                if self._simulator.thread_sleep:
                    time.sleep(self._simulator._sleeptime)
                elif self._simulator.thread_suspend:
                    while self._simulator.thread_suspend:
                        time.sleep(1.0)
                        old_cpu_time = self._simulator.cpu_time
                        t_start = time.time()
                
                # Update CPU time
                self._simulator.cpu_time = old_cpu_time + (time.time() - t_start)
                
            except Exception as e:
                logger.exception("Error in simulation loop: %s", e)
                break
        
        # Cleanup
        logger.info("Simulation complete - cleaning up")
        self.coordinator.stop()
        coord_thread.join(timeout=1.0)
        self._simulator.terminate()