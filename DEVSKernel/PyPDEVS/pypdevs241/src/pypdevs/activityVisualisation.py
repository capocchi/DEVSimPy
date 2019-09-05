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
Utility functions to visualize various kinds of data in a Cell DEVS way, that is: by creating a matrix containing single values. This matrix can then be processed by e.g. gnuplot to create a heatmap. Note that it is limited to 2D maps, as these are the most frequent and simplest to conceptually grasp.

These functions are supposed to be used later on in development for the Activity-Aware part.
"""

def visualizeLocations(kernel):
    """
    Visualize the locations in a Cell DEVS way

    :param kernel: a basesimulator object, to fetch the location of every model
    """
    location_map = [[0] * kernel.y_size for _ in range(kernel.x_size)]
    for i, loc in enumerate(kernel.destinations):
        try:
            model = kernel.model_ids[i]
            if isinstance(loc, int):
                locationMap[model.x][model.y] = loc
            else:
                locationMap[model.x][model.y] = kernel.name
        except AttributeError:
            pass
    visualizeMatrix(location_map, "%i", "locations-%f" % max(0, kernel.gvt))

def visualizeActivity(sim):
    """
    Visualize the activity in a Cell DEVS way

    :param sim: the simulator object, to access the model and their activity
    """
    activities = []
    cached = {}
    import pypdevs.middleware as middleware
    for i in range(len(sim.server.proxies)):
        proxy = sim.controller.getProxy(i)
        cached.update(proxy.getTotalActivity((float('inf'), float('inf'))))
    for aDEVS in sim.model.component_set:
        model_id = aDEVS.model_id
        activities.append([cached[model_id], aDEVS])

    if sim.x_size > 0 and sim.y_size > 0:
        activity_map = [[0.0] * sim.y_size for i in range(sim.x_size)]
        for entry in activities:
            try:
                activity_map[entry[1].x][entry[1].y] = entry[0]
            except AttributeError:
                pass
        visualizeMatrix(activity_map, "%.6f", "activity")
    else:
        activities.sort(key=lambda i: i[1].getModelFullName())
        for entry in activities:
            print(("%30s -- %.6f" % (entry[1].getModelFullName(), entry[0])))

def visualizeMatrix(matrix, formatstring, filename):
    """
    Perform the actual visualisation in a matrix style

    :param matrix: the 2D matrix to visualize, should be a list of lists
    :param formatstring: the string to use to format the values, most likely something like "%f"
    :param filename: file to write the matrix to. Can be both a string to create a new file with that name, or an opened file handle.
    """
    if isinstance(filename, str):
        outfile = open(filename, 'w')
        openfile = False
    else:
        outfile = filename
        openfile = True
    formatstring = formatstring + " "
    for x in matrix:
        for y in x:
            outfile.write(formatstring % y)
        outfile.write("\n")
    if not openfile:
        outfile.close()
