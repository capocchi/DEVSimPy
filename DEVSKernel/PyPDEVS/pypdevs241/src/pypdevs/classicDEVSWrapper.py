# Copyright 2014 Modelling, Simulation and Design Lab (MSDL) at 
# McGill University and the University of Antwerp (http://msdl.cs.mcgill.ca/)
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
A wrapper for AtomicDEVS models that are to be interpreted as Classic DEVS models
"""

class ClassicDEVSWrapper(object):
    """
    Wraps around a normal AtomicDEVS model and intercepts the DEVS specific functions. All attribute read/writes need to be redirected to the model itself.
    """
    def __init__(self, model):
        """
        Constructor

        :param model: the model to wrap around
        """
        self.model = model

    def __getattr__(self, attr):
        """
        Fetches the attributes of the model. This is a 'magic' function.

        :param attr: the attribute to fetch
        :returns: the fetched attributed
        """
        return getattr(self.model, attr)

    def __setattr__(self, attr, val):
        """
        Sets the attribute of the model. This is a 'magic' function. Only the 'model' attribute is not proxied!

        :param attr: the attribute to set
        :param val: the value to set it to
        """
        if attr == "model":
            object.__setattr__(self, attr, val)
        return setattr(self.model, attr, val)

    def extTransition(self, inputs):
        """
        Wrap around the extTransition function by changing the input dictionary

        :param inputs: the input dictionary with lists as values
        :returns: the new state, as the normal extTransition method would do
        """
        return self.model.extTransition({i: inputs[i][0] for i in inputs})

    def outputFnc(self):
        """
        Wrap around the outputFnc function by changing the returned dictionary

        :returns: the changed dictionary
        """
        retval = self.model.outputFnc()
        return {i: [retval[i]] for i in retval}
