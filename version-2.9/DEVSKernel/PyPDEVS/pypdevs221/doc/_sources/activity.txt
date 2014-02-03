Activity Tracking
=================

.. note:: This feature is still being worked on and all information is therefore prone to change.

*Activity Tracking* is a feature that will have the simulator time the invocation of each user-defined function, being the *intTransition*, *extTransition*, *confTransition*, *outputFnc* and *timeAdvance* functions. At the end, all this timing information is gathered and a list of all timings is shown to the user. In its current state, there is not really a big use for *Activity Tracking* apart from the user being aware of the load of every seperate model.

Two different output variants are currently supported:

* List view: this will simply show a flat list of the name of the model, followed by its activity (in seconds). Depending on the configuration options, this will either be sorted on model name or on activity.
* Cell view: this present the same information as the list view, only in a visual way. It will create a matrix-style file that contains the activity for that specific cell. This file can then be visualised using for example *Gnuplot*.

The following configuration options are related to this functionality:

* *setActivityTracking(at, sortOnActivity)*: enables or disables the printing of activity tracking information. Note that activity tracking is **always** performed internally, so disabling this will not increase performance.
* *setActivityTrackingCellMap(cellmap, x, y)*: when activity tracking is enabled, setting this to *True* will result in a matrix-style file instead of a (printed) flat list. The resulting file will be called *activity*.

In this example, we will create an activity Cell view, as this is a lot nicer than the other (more statistical) variant. Our model will be something more complex as the previous examples, but the model itself isn't really that important. A *fire spread* model was chosen, as this nicely reduces to a map and is thus perfect for Cell view.

.. note:: The Cell view furthermore requires models that are to be plotted have an *x* and *y* attribute. This value will determine their location in the map. Models without such attributes will simply be ignored.

This image was created by using the *experiment* file containing::

    x, y = 20, 20
    model = FireSpread(x, y)
    sim = Simulator(model)
    sim.setTerminationTime(1000.0)
    sim.setActivityTrackingVisualisation(True, x, y)
    sim.simulate()

After simulation, a file called *activity* was created. This file was plotted using *gnuplot* with the commands

.. code-block:: gnuplot

    set view map
    splot 'activity' matrix with image

.. image:: activity.png
   :alt: Activity Tracking cell view
   :width: 100%

.. note:: In order to make some more visually pleasing maps, the computation in the transition functions was severely increased. This is due to our transition function being rather small by default, which doesn't provide very accurate timings.

.. warning:: Don't forget to take the word of caution (see below) into account when analyzing the results.

Word of caution
---------------

The *Activity Tracking* feature uses the *time.time()* function from the Python *time* library. This means that it measures *wall clock* time instead of actual *CPU* time. Should the CPU be overloaded with work, these timings will thus be inaccurate due to possible interruptions of the simulation. Most of the time however, such interrupts should arrive either outside of the timed code. Otherwise, the interrupted models should be somewhat evenly spread out, thus reducing the impact.

Of course, Python provides functions to fetch the actual *CPU* time spend. These alternatives were checked, but were *insufficient* for our purpose for several reasons. The alternatives are mentioned below:

* Python *time.clock()* function: this has a very low granularity on Linux, which would show total nonsense in case the transition functions are small.
* Python *resource* library: this has the same problem as the *time.clock()* approach and furthermore is a lot slower
* External *psutil* library: this alternative has the same problems as the above alternatives, with the additional disadvantage that it is **extremely** slow.

Since *Activity Tracking* is done at every model, in every simulation step, performance of this call is critical. To show the difference between these alternatives, a *timeit* comparison is shown below:

.. code-block:: bash

    yentl ~ $ python -m timeit -s "import time" -- "time.time()"
    10000000 loops, best of 3: 0.0801 usec per loop
    yentl ~ $ python -m timeit -s "import time" -- "time.clock()"
    10000000 loops, best of 3: 0.199 usec per loop
    yentl ~ $ python -m timeit -s "import resource" -- "resource.getrusage(resource.RUSAGE_SELF).ru_utime"
    1000000 loops, best of 3: 0.642 usec per loop
    yentl ~ $ python -m timeit -s "import psutil" -- "psutil.cpu_times().user"
    10000 loops, best of 3: 25.9 usec per loop

As can be seen from this comparison, we have the following performance statistics:

+----------+---------------+----------------------------+
| method   | time per loop | times slower than *time()* |
+----------+---------------+----------------------------+
| time()   | 0.08 usec     |                         1x |
+----------+---------------+----------------------------+
| clock()  | 0.199 usec    |                       2.5x |
+----------+---------------+----------------------------+
| resource | 0.642 usec    |                         8x |
+----------+---------------+----------------------------+
| psutil   | 25.9 usec     |                       324x |
+----------+---------------+----------------------------+

Since this function will be called twice for every transition that happens, using one of the slower methods would have an immense difference on the actual simulation time. The main purpose of *Activity  Tracking* is to increase performance, but when when e.g. *psutil* is used, the simulation is already slowed down by a massive factor, removing any chance for improvement in general situations.
