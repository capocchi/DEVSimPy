#! /bin/env python
#import stacktracer
#stacktracer.trace_start("trace.html",interval=1,auto=True) # Set auto flag to always update file!

try:
    from mpi4py import MPI
except ImportError:
    pass

import models
import sys
from pypdevs.simulator import Simulator, loadCheckpoint

mn = sys.argv[1]
args = {}
args["setTerminationTime"] = [40]
args["setVerbose"] = ["output/" + mn.partition("_local")[0]]
run = True

def counter(t, m):
    return m.processor2.coupled[0].state.counter != float('inf')

def counter_pull(t, m):
    s = m.processor1.coupled[0].getState(t)
    print((s.counter))
    return s.counter != float('inf')

if mn == "confluent":
    model = models.Chain(1.00)
elif mn == "confluent_local":
    model = models.Chain_local(1.00)
elif mn == "rollback":
    args["setTerminationTime"] = [20000]
    model = models.Chain_bad()
elif mn == "normal_long":
    args["setTerminationTime"] = [20000]
    #args["setVerbose"] = [False]
    model = models.Chain(0.66)
elif mn == "normal_long_local":
    args["setTerminationTime"] = [20000]
    #args["setVerbose"] = [False]
    model = models.Chain_local(0.66)
elif mn == "dualdepth":
    model = models.DualDepth(0.66)
elif mn == "dualdepth_local":
    model = models.DualDepth_local(0.66)
elif mn == "dual":
    model = models.DualChain(0.66)
elif mn == "dual_local":
    model = models.DualChain_local(0.66)
elif mn == "dual_mp":
    model = models.DualChainMP(0.66)
elif mn == "dual_mp_local":
    model = models.DualChainMP_local(0.66)
elif mn == "local":
    model = models.Local()
elif mn == "local_local":
    model = models.Local()
elif mn == "longtime":
    model = models.Chain(0.66)
    args["setTerminationTime"] = [200]
elif mn == "longtime_local":
    model = models.Chain_local(0.66)
    args["setTerminationTime"] = [200]
elif mn == "atomic_local":
    model = models.Generator()
elif mn == "multi":
    model = models.Chain(0.50)
elif mn == "multi_local":
    model = models.Chain_local(0.50)
elif mn == "multinested":
    model = models.MultiNested()
    args["setTerminationTime"] = [10]
elif mn == "nested_local":
    model = models.Nested_local()
    args["setTerminationTime"] = [20]
elif mn == "nested_realtime_local":
    model = models.Nested_local()
    args["setTerminationTime"] = [20]
    args["setRealTime"] = [True]
    args["setRealTimePorts"] = [{}]
    args["setRealTimePlatformThreads"] = []
elif mn == "remotedc":
    model = models.RemoteDC()
elif mn == "remotedc_long":
    args["setTerminationTime"] = [200]
    model = models.RemoteDC()
elif mn == "normal":
    model = models.Chain(0.66)
elif mn == "allocate":
    args["setTerminationTime"] = [10000]
    args["setGreedyAllocator"] = []
    #args["setDrawModel"] = [True, "model.dot", False]
    model = models.Chain(0.66)
elif mn == "normal_local":
    model = models.Chain_local(0.66)
elif mn == "zeroLookahead":
    model = models.Chain(0.00)
elif mn == "zeroLookahead_local":
    model = models.Chain_local(0.00)
elif mn == "stateStop":
    model = models.Chain(0.66)
    args["setTerminationModel"] = [model.processor2.coupled[0]]
    args["setTerminationCondition"] = [counter]
    del args["setTerminationTime"]
elif mn == "stateStop_local":
    model = models.Chain_local(0.66)
    args["setTerminationModel"] = [model.processor2.coupled[0]]
    args["setTerminationCondition"] = [counter]
    del args["setTerminationTime"]
elif mn == "checkpoint":
    model = models.Chain(0.66)
    args["setTerminationTime"] = [2000]
    args["setCheckpointing"] = ["testing", 1]
    if loadCheckpoint("testing") is not None:
        run = False
elif mn == "checkpoint_long":
    model = models.Chain(0.66)
    args["setTerminationTime"] = [20000]
    args["setCheckpointing"] = ["testing", 1]
    if loadCheckpoint("testing") is not None:
        run = False
elif mn == "checkpoint_long_local":
    model = models.Chain_local(0.66)
    args["setTerminationTime"] = [20000]
    args["setCheckpointing"] = ["testing", 1]
    if loadCheckpoint("testing") is not None:
        run = False
elif mn == "autodist":
    model = models.AutoDistChain(3, totalAtomics=500, iterations=1)
elif mn == "autodist_original":
    from mpi4py import MPI
    model = models.AutoDistChain(MPI.COMM_WORLD.Get_size(), totalAtomics=500, iterations=1)
elif mn == "autodist_checkpoint":
    from mpi4py import MPI
    model = models.AutoDistChain(MPI.COMM_WORLD.Get_size(), totalAtomics=500, iterations=1)
    args["setTerminationTime"] = [200]
    args["setShowProgress"] = []
    args["setCheckpointing"] = ["testing", 1]
    if loadCheckpoint("testing") is not None:
        run = False
elif mn == "relocation":
    model = models.Chain(0.66)
    args["setTerminationTime"] = [2000]
    args["setRelocationDirectives"] = [[[500, model.processor1.coupled[0], 0], [1000, model.processor1.coupled[0], 2]]]
    args["setGVTInterval"] = [1]
elif mn == "relocation_activity":
    model = models.Chain(0.66)
    args["setTerminationTime"] = [20000]
    args["setActivityRelocatorBasicBoundary"] = [1.2]
    del args["setVerbose"]
    args["setGVTInterval"] = [2]
elif mn == "relocation_noactivity":
    model = models.Chain(0.66)
    args["setTerminationTime"] = [20000]
    del args["setVerbose"]
    args["setGVTInterval"] = [2]
elif mn == "boundary":
    model = models.Boundary()
    args["setTerminationTime"] = [2000]
    args["setRelocationDirectives"] = [[[100, 2, 0]]]
    args["setGVTInterval"] = [1]
elif mn == "relocation_faster":
    model = models.Chain(0.66)
    del args["setVerbose"]
    args["setTerminationTime"] = [20000]
    args["setRelocationDirectives"] = [[[0, model.processor1.coupled[0], 1], [0, model.processor2.coupled[0], 2], [0, model.processor2.coupled[1], 2]]]
elif mn.startswith("realtime"):
    from trafficLightModel import *
    model = TrafficSystem(name="trafficSystem")
    refs = {"INTERRUPT": model.trafficLight.INTERRUPT}
    args["setVerbose"] = ["output/realtime"]
    args["setTerminationTime"] = [35]
    if "0.5" in mn:
        scale = 0.5
    elif "2.0" in mn:
        scale = 2.0
    else:
        scale = 1.0
    args["setRealTime"] = [True, scale]
    args["setRealTimeInputFile"] = ["testmodels/input"]
    args["setRealTimePorts"] = [refs]
    if mn.startswith("realtime_thread"):
        args["setRealTimePlatformThreads"] = []
    elif mn.startswith("realtime_loop"):
        args["setRealTimePlatformGameLoop"] = []
    elif mn.startswith("realtime_tk"):
        from tkinter import *
        myTk = Tk()
        args["setRealTimePlatformTk"] = [myTk]
    else:
        print("Unknown subsystem requested")
        sys.exit(1)
elif mn == "progress":
    model = models.Chain(0.66)
    args["setShowProgress"] = []
    args["setTerminationTime"] = [2000]
elif mn == "progress_local":
    model = models.Chain_local(0.66)
    args["setShowProgress"] = []
    args["setTerminationTime"] = [2000]
elif mn == "trace":
    model = models.Binary()
    args["setVCD"] = ["devstrace.vcd"]
    args["setXML"] = ["devstrace.xml"]
elif mn == "trace_local":
    model = models.Binary_local()
    args["setVCD"] = ["devstrace.vcd"]
    args["setXML"] = ["devstrace.xml"]
elif mn == "fetch":
    model = models.Chain(0.66)
    args["setFetchAllAfterSimulation"] = []
elif mn == "draw":
    model = models.Chain(0.66)
    args["setDrawModel"] = [True]
elif mn == "draw_local":
    model = models.Chain_local(0.66)
    args["setDrawModel"] = [True]
elif mn == "auto_allocate":
    # Take the local variant, as this does not contain location info
    model = models.Chain_local(0.66)
    args["setDrawModel"] = [True]
    args["setAutoAllocator"] = []
elif mn == "multiinputs":
    model = models.MultipleInputs()
elif mn == "multiinputs_local":
    model = models.MultipleInputs_local()
elif mn == "doublelayer_local":
    model = models.DoubleLayerRoot()
elif mn == "dynamicstructure_local":
    model = models.DSDEVSRoot()
    args["setDSDEVS"] = [True]
elif mn == "dynamicstructure_realtime_local":
    model = models.DSDEVSRoot()
    args["setRealTime"] = [True]
    args["setRealTimePorts"] = [{}]
    args["setRealTimePlatformThreads"] = []
    args["setDSDEVS"] = [True]
elif mn == "classicDEVS_local":
    model = models.ClassicCoupled()
    args["setClassicDEVS"] = [True]
elif mn == "classicDEVSconnect_local":
    model = models.AllConnectClassic()
    args["setClassicDEVS"] = [True]
elif mn == "random":
    model = models.RandomCoupled()
elif mn == "random_local":
    model = models.RandomCoupled_local()
elif mn == "stateStop_pull":
    model = models.Chain(0.66)
    args["setTerminationCondition"] = [counter_pull]
    del args["setTerminationTime"]
elif mn.startswith("reinit"):
    model = models.AutoDistChain(3, totalAtomics=500, iterations=1)
    if "local" in mn:
        model.forceSequential()
    sim = Simulator(model)
    sim.setAllowLocalReinit(True)
    sim.setTerminationTime(40)
    sim.setVerbose("output/reinit1")
    sim.simulate()
    sim.reinit()
    sim.setVerbose("output/reinit2")
    sim.setModelStateAttr(model.generator.generator, "value", 2)
    sim.simulate()
    sim.reinit()
    sim.setVerbose("output/reinit3")
    sim.setModelStateAttr(model.generator.generator, "value", 3)
    sim.simulate()
    run = False
elif mn.startswith("multisim"):
    if "local" in mn:
        sim = Simulator(models.Chain_local(0.66))
    else:
        sim = Simulator(models.Chain(0.66))
    sim.setVerbose("output/normal")
    sim.setTerminationTime(40)
    sim.simulate()

    if "local" in mn:
        sim2 = Simulator(models.DualDepth_local(0.66))
    else:
        sim2 = Simulator(models.DualDepth(0.66))
    sim2.setVerbose("output/dualdepth")
    sim2.setTerminationTime(40)
    sim2.simulate()
    run = False
elif mn.startswith("continue"):
    if "local" in mn:
        sim = Simulator(models.Chain_local(0.66))
    else:
        sim = Simulator(models.Chain(0.66))
    sim.setVerbose("output/run1")
    sim.setTerminationTime(100.0)
    sim.simulate()
    sim.setModelStateAttr(sim.model.generator.generator, "value", 2)
    sim.setVerbose("output/run2")
    sim.setTerminationTime(200.0)
    sim.simulate()
    run = False
elif mn.startswith("z"):
    if "local" in mn:
        model = models.ZChain_local()
    else:
        model = models.ZChain()

if run:
    sim = Simulator(model)
    for arg in list(args.keys()):
        function = getattr(sim, arg)
        function(*args[arg])
    sim.simulate()
if mn.startswith("realtime_loop"):
    # Start a game loop ourselves
    import time
    start_time = time.time()
    while time.time() < start_time + 35.5 * scale:
        before = time.time()
        sim.realtime_loop_call()
        time.sleep(0.001 - (before - time.time()))
elif mn.startswith("realtime_tk"):
    myTk.after(int(35000 * scale), myTk.quit)
    myTk.mainloop()
elif mn.startswith("realtime_thread"):
    import time
    time.sleep((35+0.2) * scale)
elif "realtime" in mn:
    import time
    time.sleep(args["setTerminationTime"][0])
elif mn == "fetch":
    f = open(args["setVerbose"][0], 'w')
    f.write("Generator: " + str(model.generator.generator.state) + "\n")
    f.write("Processor1.Processor1: " + str(model.processor1.coupled[0].state) + "\n")
    f.write("Processor1.Processor2: " + str(model.processor1.coupled[1].state) + "\n")
    f.write("Processor2.Processor1: " + str(model.processor2.coupled[0].state) + "\n")
    f.write("Processor2.Processor2: " + str(model.processor2.coupled[1].state) + "\n")
    f.write("Processor2.Processor3: " + str(model.processor2.coupled[2].state) + "\n")
    f.close()
