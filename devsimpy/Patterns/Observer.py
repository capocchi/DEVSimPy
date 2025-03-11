# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# Observer.py ---
#                    --------------------------------
#                            Copyright (c) 2020
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 2.0                                        last modified: 03/15/20
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

class Observer:
	""" Observer class (abstract or interface)
	"""
	def update(self, theChangedSubject = None):
		""" update method with changed subject param
		"""
		pass

class Subject:
	""" Subject class
	"""
	
	def __init__(self):
		""" Constructor
		"""
		self.observerList = []
		
	def attach(self, observer):
		""" Attach method with observer param
		"""
		if observer not in self.observerList:
			self.observerList.append(observer)
		
	def detach(self, observer):
		""" Detach method with observer param
		"""
		if observer in self.observerList:
			self.observerList.remove(observer)
	
	def notify(self):
		""" Notify method which invokes the observer's update method
		"""
		for observer in self.observerList:
			observer.update(self)
