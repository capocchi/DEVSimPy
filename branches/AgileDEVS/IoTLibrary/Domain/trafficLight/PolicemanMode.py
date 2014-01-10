#-------------------------------------------------------------------------------
# Name:        PolicemanMode
# Purpose:
#
# Author:      capocchi_l
#
# Created:     17/11/2013
# Copyright:   (c) capocchi_l 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------

class PolicemanMode:
	"""Encapsulates the Policeman's state
	"""

	###
	def __init__(self, current="idle"):
		"""Constructor (parameterizable).
		"""
		self.set(current)

	def set(self, value="idle"):
		self.__mode=value

	def get(self):
		return self.__mode

	def __str__(self):
		return self.get()

def main():
	pass

if __name__ == '__main__':
	main()
