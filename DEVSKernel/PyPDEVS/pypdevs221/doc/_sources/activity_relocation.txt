Automatic activity-based relocation
===================================

As was mentioned in the previous section, manual relocation is possible in PyPDEVS. However, the knowledge of the modeler about which models need to be moved and at what time exactly, might be rather vague or even non-existent. Clearly, slightly altering the models parameters could completely alter the time at which relocation would be ideal. Additionally, such manual relocation is time consuming to write and benchmark.

In order to automate the approach, PyPDEVS can use *activity* to guide it into making autonomous decisions. Since activity is a rather broad concept, several options are possible, most of them also offering the modeller the possibility to plug in its own relocators or activity definitions. Together with custom modules, comes also the possibility for inserting domain specific knowledge.

We distinguish several different situations:

.. toctree::
    
   Activity Tracking <activitytracking>
   Custom Activity Tracking <customactivitytracking>
   Custom Activity Prediction <activityprediction>
