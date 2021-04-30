# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# Structurable.py ---
#                     --------------------------------
#                        Copyright (c) 2013
#                       Laurent CAPOCCHI
#                      University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 19/11/13
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GLOBAL VARIABLES AND FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import Components
class Structurable(Components.DEVSComponent):
	""" Structurable class interface for DEVS coupled model integration.
	"""

	def __init__(self):
		""" Constructor of Structurable class interface.
		"""

		Components.DEVSComponent.__init__(self)

	def ConnectDEVSPorts(self, p1, p2):
		""" Connect DEVS ports.

				@param p1: DEVS port
				@param p2: DEVS port

				@type p1: instance
				@type p2: instance
		"""
		assert(self.devsModel != None)

		self.devsModel.connectPorts(p1, p2)

	def addSubModel(self, devs):
		""" Add sub model.

			@param devs DEVS instance
			@type devs: instance
		"""
		self.devsModel.addSubModel(devs)

	def addInPort(self):
		""" Add input port.
		"""
		return self.devsModel.addInPort()

	def addOutPort(self):
		""" Add output port.
		"""
		return self.devsModel.addOutPort()

	def getIPorts(self):
		""" Get inputs port list.
		"""
		return self.devsModel.IPorts

	def getOPorts(self):
		""" Get the outputs port list
		"""
		return self.devsModel.OPorts

	def ClearAllPorts(self):
		""" Clear all DEVS ports.
		"""
		self.devsModel.IC = []
		self.devsModel.EIC = []
		self.devsModel.EOC = []
		self.devsModel.IPorts = []
		self.devsModel.OPorts = []

	def removeSubModel(self, devs):
		""" Remove sub model.

			@param devs DEVS instance
			@type devs: instance
		"""
		if hasattr(self.devsModel, 'removeSubModel'):
			self.devsModel.removeSubModel(devs)

	def disconnectPorts(self, p1, p2):
		""" Disconnect DEVS ports.

			@param p1: DEVS port
			@param p2: DEVS port

			@type p1: instance
			@type p2: instance

		"""
		if hasattr(self.devsModel, 'disconnectPorts'):
			self.devsModel.disconnectPorts(p1, p2)

def main():
    pass

if __name__ == '__main__':
    main()
