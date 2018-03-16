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

		### direction for all ports
		dir = self.direction

		# width and height of model
		w = self.x[1]-self.x[0]
		h = self.y[1]-self.y[0]

		### x position
		if type=='input':
			div = float(self.input)+1.0
			x=self.x[0]

		elif type=='output':
			div = float(self.output)+1.0
			x=self.x[1]

		### delta for x nd y
		dx=float(w)/div
		dy=float(h)/div

		### y position
		y= self.y[0]+dy*(num+1)

		# ouest -> nord
		if dir == "nord":
			if type=='input':
				x+=dx*(num+1)
				y-=dy*(num+1)
			else:
				x-=dx*(num+1)
				y+=h-dy*(num+1)
		# nord -> est
		elif dir == "est":
			if type=='input':
				x+=w
				y+=0
			else:
				x-=w
				y+=0
		# est -> sud
		elif dir == "sud":
			if type=='input':
				x+=dx*(num+1)
				y+=h-dy*(num+1)
			else:
				x-=dx*(num+1)
				y-=dy*(num+1)
		# sud -> ouest
		elif dir == "ouest":
			if type=='input':
				x+=0
				y+=0
			else:
				x+=0
				y+=0

		return (x,y)

def main():
    pass

if __name__ == '__main__':
    main()
