Visualisation
=============

Model visualisation is possible by using the *setDrawModel()* configuration option. For example like this::
    
    model = CQueue()
    sim = Simulator(model)
    sim.setDrawModel(True, "model.dot", False)
    sim.simulate()

This will output a file containing Graphviz syntax for your model. For our example, this gives a file similar to::

  digraph G {
    subgraph "clusterCQueue" {
    label = "CQueue"
    color=black
    "CQueue.Generator" [
      label = "Generator\nState: True"
      color="red"
      style=filled
    ]
    "CQueue.Queue" [
      label = "Queue\nState: None"
      color="red"
      style=filled
    ]
    }
    "CQueue.Generator" -> "CQueue.Queue" [label="outport -> input"];
  }

Running it through Graphviz with the command:

.. code-block:: bash

   dot -Tpng model.dot > model.png

Will generate a *png* file such as the one below

.. image:: model.png
   :alt: Graphical representation of the model

In it, we see the hierarchical composition, containing all atomic models. These models have their name shown, together with their initial condition. Connections between models are shown by arrows and will include the name of the link by default. This can be disabled (e.g. to increase clarity or decrease rendering time) by passing *True* instead of *False* for the *hideEdgeLabels* parameter of *setDrawModel*.

There is no real limit on how big the models can be to be drawn, as PythonPDEVS only generates the textual description. Note though that massive models might not be easily visualised by Graphviz itself. PyPDEVS does not provide anything of layout, this is completely the responsibility of Graphviz.

In distributed simulation, visualisation is helpful as it will give a different color to atomic models that run on different nodes. This allows for fast detection of possible bottlenecks and sources of revertions.

Of course, neither PyPDEVS nor GraphViz have any information about what you want your model to look like (that is, topologically) and it will only make a 'best bet'. This can often result in strange visualisations, certainly when the model was conceptually very structured, such as a grid.

.. note:: The colors that are being used for this visualisation are mentioned in :doc:`colors_int` and have no real special meaning. To save myself some time, only about 30 colors were entered. If you want to visualize a model that uses more nodes, you will need to provide additional colors yourself.

