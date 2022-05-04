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

class Connectable:
	""" Mixin to create connectable nodes or ports.
	"""
	DUMP_ATTR = ['_input_labels','_output_labels']

	###
	def __init__(self, nb_in:int=1, nb_out:int=3)->None:
		""" Constructor.
		"""
		self.input = nb_in
		self.output = nb_out
		### to store label of ports
		self._input_labels = {}
		self._output_labels = {}

	def getInputLabel(self, port:int)->str:
		""" return the label of the input port n
		"""
		return self._input_labels.get(port,None) if hasattr(self,'_input_labels') else None

	def getOutputLabel(self, port:int)->str:
		""" return the label of the output port n
		"""
		return self._output_labels.get(port,None) if hasattr(self,'_output_labels') else None

	def getInputLabels(self)->dict:
		""" return the input label dict
		"""
		return self._input_labels

	def getOutputLabels(self)->dict:
		""" return the output label dict
		"""
		return self._output_labels

	def setInputLabels(self,v:dict)->None:
		""" set the input label dict
		"""
		self._input_labels = v

	def setOutputLabels(self, v:dict)->None:
		""" set the output label dict
		"""
		self._output_labels = v
		
	def addInputLabels(self, port:int, label:str)->None:
		""" add a label to the input port
		"""
		self._input_labels[port] = label

	def addOutputLabels(self, port:int, label:str)->None:
		""" add a label to the output port
		"""
		self._output_labels[port] = label

	###
	def getPortXY(self, type:str, num)->tuple:
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
