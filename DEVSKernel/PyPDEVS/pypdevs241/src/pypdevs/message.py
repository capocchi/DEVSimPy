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
Network messages used in the distributed simulation
"""

class NetworkMessage(object):
    """
    Network messages used in the distributed simulation, simply a data class.
    """
    def __init__(self, timestamp, content, uuid, color, destination):
        """
        Constructor

        :param timestamp: timestamp of the message
        :param content: content of the message
        :param uuid: UUID of the message
        :param color: color of the message for Mattern's algorithm
        :param destination: the model_id of the destination model
        """
        self.timestamp = timestamp
        self.content = content
        self.uuid = uuid
        self.color = color
        self.destination = destination

    def __lt__(self, other):
        """
        Comparison of different NetworkMessages, necessary for Python3
        """
        return self.timestamp < other.timestamp
