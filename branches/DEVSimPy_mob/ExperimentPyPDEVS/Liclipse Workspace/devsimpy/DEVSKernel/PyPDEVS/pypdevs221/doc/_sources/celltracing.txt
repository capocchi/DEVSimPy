Cell Tracing
============

Cell tracing is somewhat different from the *verbose* and *XML* tracers, in that it is only applicable for several models. The models that support it however, can profit from it, as this is a very visual and easy to understand tracer.

.. note:: For those familiar with Cell DEVS (and particularly CD++): this tracer aims at providing the same tracing functionality for 2D DEVS models as CD++ provides for them. This does introduce parts of Cell DEVS in Parallel DEVS, but of course the only affected parts are the actual tracing and not model construction and simulation.

There are only 2 requirements on the model for Cell tracing:

* The models have an *x* and *y* attribute, which signify the location where the cell will be drawn.
* The states have an *toCellState()* method, which should return the value to be shown in the matrix.

.. note:: If two models have unique coordinates, only one of them will be considered in the tracing. There is no support for dimensions above 2D.

Thus a very simple cell would look like this::

    class CellState(object):
        def __init__(self, value):
            self.value = value

        def toCellState(self):
            # Simply return the value, but could also first 
            # perform some operations on the value
            return value

    class Cell(AtomicDEVS):
        def __init__(self, x, y):
            AtomicDEVS.__init__(self, 'Cell(%i, %i)' % (x, y))
            self.x = x
            self.y = y
            self.state = CellState()

The coupled model would then be responsible for assigning unique coordinates to every cell. The following configurations now still need to be set in the experiment file::

    # Save the coordinates of the model somewhere, as we need them later
    x, y = 20, 20
    model = MyCoupledCellModel(x, y)
    sim = Simulator(model)
    sim.setCell(True, x, y, cell_file="celltrace", multifile=False)
    sim.simulate()

This will then generate a file with a matrix of the current state at every timestep. The matrices are simply appended with a delimiter between them. Sadly, this kind of data is not directly usable in gnuplot, which is why the *multifile* option comes in handy.

When setting *multifile=True*, every timestep will have its own file, which contains only the matrix and can be directly drawn using *gnuplot*. Simulator-defined files are not that handy, because you probably want it in a slightly different format. For this reason, the *cell_file* parameter will be interpreted as a *format string* when *multifile* is set to *True*. An example invocation of this could be::
    
    sim.setCell(True, x, y, cell_file="celltrace-%05d", multifile=True)

This will then create the files *celltrace-00001*, *celltrace-00002*, ... until the termination time is reached.

.. note:: Remember that the *cell_file* parameter will be used as a format string if *multifile* is *True*!

After these files are generated, we can simply plot them with e.g. *gnuplot* as follows:

.. code-block:: gnuplot

   set pm3d map
   set pm3d interpolate 0, 0
   splot 'celltrace-00001' matrix

This will generate in interpolated version (which is slightly nicer than the original version). Naturally, scripting immediately comes to mind when a lot of files with similar data are created. It is now even possible to create an animation of the simulation, thus visualizing the change over time. This can be done in e.g. bash as follows:

.. code-block:: bash

   for f in `ls -1 celltrace-*`
   do
       echo "set view map" > plot
       echo "set terminal png size 400, 300 enhanced" >> plot
       echo "set pm3d map" >> plot
       echo "set pm3d interpolate 0, 0" >> plot
       echo "set output '$f.png'" >> plot
       echo "splot '$f' matrix" >> plot
       gnuplot plot
       rm plot
   done
   avconv -i celltrace-%5d.png out.avi

Which will create an animation visualizing e.g. a *fire spread* model. Since *gnuplot* will automatically determine the range of colors to use, it might be interesting to provide this range yourself, as to keep it consistent between all different images. This can be done by adding the following line right before the *splot* line:

.. code-block:: bash

   echo "set cbrange [27:800]" >> plot

Each individual file will then look something like:

.. image:: celldevs.png
   :alt: Cell view
   :width: 100%

And an animated version looks like:

.. image:: celldevs.gif
   :alt: Cell view animation
   :width: 100%

.. note:: It is technically possible to visualize this data in (semi)-realtime. If local simulation is done, each trace file will be written as soon as possible. It would require some additional lines of scripting to actually poll for these files and render them of course. In distributed simulation, visualisation at run time is not so simple, as these files will only be written at GVT boundaries.
