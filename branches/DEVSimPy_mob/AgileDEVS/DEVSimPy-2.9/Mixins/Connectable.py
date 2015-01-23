# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# Connectable.py ---
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

#---------------------------------------------------------
class Connectable:
	""" Mixin to create connectable nodes or ports
	"""

	###
	def __init__(self, nb_in = 1, nb_out = 3):
		""" Constructor.
		"""

		self.input = nb_in
		self.output = nb_out

	###
	def getPortXY(self, type, num):
		""" Return the tuple (x,y).
		"""

		# width and height of model
		w = self.x[1]-self.x[0]
		h = self.y[1]-self.y[0]

		### x position
		if type=='input':
			div = float(self.input)+1.0
			### direction for all ports
			dir = self.input_direction

		elif type=='output':
			div = float(self.output)+1.0
			### direction for all ports
			dir = self.output_direction

		### delta for x and y
		dx=float(w)/div
		dy=float(h)/div

		### init x and y position
		x = self.x[0]
		y = self.y[0]

		# ouest -> nord
		if dir == "nord":
			x+=dx*(num+1)
		# nord -> est
		elif dir == "est":
			x+=w
			y+=dy*(num+1)
		# est -> sud
		elif dir == "sud":
			x+=dx*(num+1)
			y+=h
		# sud -> ouest
		elif dir == "ouest":
			y+=dy*(num+1)

		return (x,y)

def main():
    pass

if __name__ == '__main__':
    main()
