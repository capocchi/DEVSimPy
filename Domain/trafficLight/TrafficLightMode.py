#-------------------------------------------------------------------------------
# Name:        TrafficLightMode
# Purpose:
#
# Author:      capocchi_l
#
# Created:     17/11/2013
# Copyright:   (c) capocchi_l 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------

class TrafficLightMode:
	"""Encapsulates the system's state
	"""

	###
	def __init__(self, current="red"):
		"""Constructor (parameterizable).
		"""
		self.set(current)

	def set(self, value="red"):
		self.__colour=value

	def get(self):
		return self.__colour

	def __str__(self):
		return self.get()

def main():
	pass

if __name__ == '__main__':
	main()
