Differences from PyDEVS
=======================

This section is aimed at people used to the API as presented in PyDEVS up to version 1.1. Since this version, the aim was shifted to performance and efficient simulation, together with several specific (and hopefully useful) features.

Users not familiar with PyDEVS do not need to read this section, as it contains parts of the old API.

Parallel DEVS
-------------

The major shift in PyPDEVS is the switch to Parallel DEVS, which is also where the additional *'P'* in the name comes from.

For the modeller, the main difference is in the content of the messages that are being passed. Previously, only a single message was put on every port. In the new version, a message is *always* a list containing the actual messages. As specified in the PDEVS standard, this is actually to be interpreted as a *bag* and therefore there is **no guaranteed order** to the elements in the list.

Another change is in the removal of the *select()* function, which is no longer needed due to all transitions being processed simultaneously.

There is also the addition of the *confTransition(inputs)* function, which will be called in situations where both an internal and external transition happen together. This function is set to a combination of the *extTransition(inputs)* and *intTransition()* function by default.

Even though the default formalism was shifted to Parallel DEVS (and with it, all internal algorithms), Classic DEVS is still supported by using the *setClassicDEVS()* configuration option. Classic DEVS is a lot slower though, due to the *select()* function, so it is advised to use Parallel DEVS whenever possible.

Different API
-------------

The old interface of the *Simulator* class was very small and all options were passed to the *simulate()* method. Due to the explosive amount of new configurations, this became unmanageable and it required a lot of checking. These configuration settings are now done using setters, which are all documented under the *Simulator* interface.

Not only the *Simulator* interface has changed, but also the methods to access the input in the *extTransition* and *confTransition* functions. Previously, this was done using the *peek* and *poke* functions. This became unnatural for Parallel DEVS (as it is unknown whether to overwrite or append the output) and also incurred a significant overhead due to the enormous amount of function calls. In the new interface, the methods receive a dictionary containing all ports on which input was received and the corresponding values. Ports without input are not mentioned in the dictionary. The *poke* message is similarly replaced by having the *outputFnc* return a similar dictionary.

Allow for distribution and parallellisation
-------------------------------------------

The main improvement in version 2.1 is the possibility to distribute the model and run it in parallel. For the modeller, the only difference is the addition of several API calls (which are optional, as some sane default values are chosen).

Additionally, the *addSubModel()* function takes an optional parameter *location* which specifies the number of the node on which the simulation of this model and its submodels should run. It is not necessary to specify this parameter manually, as there is a configuration option for automatic distribution of the model.

All these extensions do not change the interface for the local simulations or for local model construction.

Additional tracers
------------------

The tracing framework has been extensively rewritten and now supports both *verbose*, *VCD* and *XML*. These options themselves were already available in previous versions (through extended versions of PyDEVS), though the traced data is now flushed to disk immediately instead of being saved in memory. This was a severe limitation in big simulation runs, as they were unable to be traced.

Additionally, multiple tracers of the same kind are now also possible from within PyPDEVS itself. Though it should be noted that this will not perform any optimisations and literally run the same code twice. If such situation is really desired in combination with performance, please look at the *tee* UNIX command.

.. versionadded:: 2.1.4 A new Cell DEVS style tracer is also added, which prints the output to a file that can be used for e.g. visualisation.

Custom copy method for messages
-------------------------------

The DEVS formalism states that messages should be copies of the original message that is being send, in order to prevent different models from influencing each others. This was rather inefficient and PyDEVS was actually (one of) the only simulators that actually did this, though copying is the correct behaviour.

In order to allow for fair comparisons to other simulators, such as ADEVS, the modeller now has the possibility to define a custom *copy()* method on the message being sent. This method should return a *deep* copy of the original message. 

While this might seem bothersome for the modeller, even a simple data class can be copied up to 10 times faster by only defining a *copy()* method which makes a copy itself instead of relying on the default *pickle* behaviour. Furthermore, the modeller might have some further knowledge about the model and thus know that a message will not be used for such unacceptable purposes.

In the most extreme case, it is even possible to disable message copies completely. This is the only behaviour in most simulators, so it is mainly implemented to allow for fair performance comparisons.

.. warning::
   While it would be possible to violate the DEVS formalism by using these shortcuts, they are **not** supported in any way. In local simulation, such alterations might probably work in some versions, though this behaviour is not guaranteed to stay the same between several versions. On distributed simulation, the situation gets worse, since it will probably **never** work and might lead to seemingly random state modifications due to state saving.

Realtime simulation
-------------------

Realtime simulation is now possible using the *Simulator* configuration parameters. The model itself does not need to be modified, though it is necessary to pass a dictionary containing the ports on which input can be passed. File input is also possible and can be interleaved with input from stdin.

Simulation can be halted by using the standard termination options, or by sending the empty string as input.

Checkpointing added
-------------------

Distributed simulation has an increased possibility for failure and therefore checkpointing support was added. Checkpoints are made using the *pickle* modules present in Python and therefore require the states and attributes of the models to be picklable themself. This should not be a problem, as it would be unnatural to have unpicklable attributes there. Furthermore, distributed simulation already requires the states to be picklable for state saving.

To restore from a checkpoint, the *load_checkpoint* function can be used, which will automatically search for the latest (complete) checkpoint and use it. In case none is found, this function will return *None*. In case a suitable checkpoint was found, it will return the original simulator object to be used in further code. It is therefore important to **not** call *simulate()* on this returned simulator and the *load_checkpoint* call should be (one of) the first lines of code.

Checkpoints are *disabled* by default, as they take some time and require disk access.

Logging support
---------------

Logging support is present using a Syslog server (by default, the one at *localhost* will be used). This is not really useful for normal users, though it provides great debugging for the simulation kernel. To disable this logging (as it increases simulation time by a noticable factor), it is possible to either run the *disableAsserts.sh* script, or run *python* with the *-O* flag. This logger is also used for messages from the simulator itself, though fatal and important errors are always thrown using the exception system (as a *DEVSException*).

Due to the huge performance impact, logging is disabled by default at the *source* level. If you require logging support, use the *enableAsserts.sh* shell script.

Model visualisation
-------------------

It is possible to export the model in a format that is understandable for *Graphviz*, as to visualize the model. The primary advantage of this is that it also visualizes the location where the node runs (at least at the start of the simulation). It furthermore allows the modeller to see what kind of model is being simulated and whether or not some connections are wrong. 

.. note:: Huge models might have problems being visualized due to *Graphviz* drawing the edge labels by default. This causes a lot of collision checking to be done and probably results in an unreadable file. For this reason, the *hideEdgeLabels* is present and will hide these edge labels.

Progress bar added
------------------

Some nice *'eye candy'* that is present in PyPDEVS is the progress bar. While its primary purpose is to visualize the progress of the different nodes, it is also usable in local simulation.

An example output is::

  0 |######################==                                               | 35%
  1 |######################=================================================|DONE
  2 |######################==                                               | 35%

In this situation, a simulation runs over 3 nodes, where node 1 is already finished. Node 0 and 2 are both at 35% of their simulation. This percentage is calculated based on the current simulation time and the termination time provided during configuration.

The *'#'* symbols indicate the parts of the simulation that are already confirmed to be definitive by the GVT. The *'='* symbols indicate pending parts of the simulation that are not yet confirmed and are still possible to be reverted.

Clearly, simulation finishes as soon as all nodes are *'DONE'*.

.. note:: It is certainly possible for progress bars to fall back, even before the lowest of them all (though not below the GVT). This is due to messages that might still be in the network and are not taken into account by the progress bars. Of course, these messages are still taken into account by the GVT algorithm.

.. note:: Because these progress bars are updated using terminal escape codes, it is possible that they only work in specific terminals. Additionally, the progress bars will always overwrite the last few lines, which could contain your own prints or verbose tracing output. 

Different schedulers
--------------------

In PyDEVS, the scheduler was fixed, whereas PyPDEVS now allows the user to choose which kind of scheduler to use. The current version supports 7 different schedulers: Sorted List, Minimal List, Activity Heap, HeapSet, NoAge, Discrete and Polymorphic. This modularised approach allows for domain-specific schedulers to be used if one can be implemented more efficiently.

If you do not care about performance, simply use the default scheduler.

Python 3 compliant
------------------

With Python 3 being the new version of Python, the PythonPDEVS simulator was also written with Python 3 compatibility in mind. The main development still happens on Python 2, though tests are sporadically also ran using Python 3.

Several possibilities for Python 3 compliance exist, though the method implemented in PythonPDEVS is the use of a restricted subset of Python 2, which is still present in Python 3 (with the same semantics of course).

.. note:: Python 2 and Python 3 have modifications to several key aspects of the language, such as the use of iterators for the *range* function. For this reason, there might be a performance gap between using either of the interpreters.

.. warning:: Even though the semantics of most core elements stay the same, several other parts of the language might behave slightly different and produce different results. It can therefore not be guaranteed that Python 3 is perfectly supported, though it should be considered a bug if there is a deviation.

Reinitialisation
----------------

Previous versions of PythonDEVS did not have the possibility to reinitialize the model and simply restart simulation (with possibly slightly different configuration options). Now it is possible to simply call the *simulate()* function multiple times, which will reinitialize the model on subsequent calls.

For local simulation, this requires a non-default simulation configuration. This decision was made for two reasons:
1 Reinitialisation was previously not supported, so there would be no change for normal simulation
2 Resetting the model requires to create a copy of the model in the original state, which takes some time to pickle the model
3 Saving a copy of the original model will take some additional memory, which can be rather high for large models

Distributed simulation has this option enabled by default, because the pickled representation of the model is already made and distributed in the initial setup. Furthermore, in local simulation it is much easier to reconstruct the model and simply restart the simulation on it. On the other hand, distributed simulation would require model distribution all over again, which can cause a high network load.

.. note:: When changing model attributes after the first call of the *simulate()* method, this should happen using the interface provided by the *Simulator*. This is because the model that is visible in the experiment file, is **not** the version of the model that is still present on the remote nodes. Changing attributes on this model will thus have no effect.

Activity Tracking
-----------------

Together with the possibility for distributed simulation, load balancing based on activity information was added. This is a huge feature and can allow for severe speedups in several cases. All of default activity tracking, custom activity tracking and custom activity prediction are possible. For more details on this feature, we refer to its own section.
