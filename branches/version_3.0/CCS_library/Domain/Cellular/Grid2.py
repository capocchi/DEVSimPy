# -*- coding: utf-8 -*-

"""
Name : Grid.py 
Brief descritpion : Grid Cellular automata
Author(s) : Laurent CAPOCCHI (capocchi@univ-corse.fr), Jean-francois Santucci (santucci@univ-corse.fr)
Version :  1.0                                        
Last modified : 01/12/12
GENERAL NOTES AND REMARKS: depends on matplotlib (python-matplotlib for ubuntu install)
GLOBAL VARIABLES AND FUNCTIONS:
"""

import sys
import numpy as np
import matplotlib.pyplot as plt

from DomainInterface.DomainBehavior import DomainBehavior
from Domain.PowerSystem.Object import Message

#    ======================================================================    #
class Grid(DomainBehavior):
	""" Grid Cellular Automata
	"""

	###
	def __init__(self, row=30, col=30, active_cell=[(10,10),(11,10),(12,10),(13,10),(14,10),(15,10),(16,10),(17,10),(18,10),(19,10),(20,10)], neighborhoods=('Moore','VonNeumann', 'Hexagonal'), dtype=bool):
		"""	Constructor

			@param row : grid row
			@param col : grid col
			@active_cell : active cellular at the begining 
			@param neighborhoods : neighborhoods method
			@dtype : type of cellule
		"""

		DomainBehavior.__init__(self)
		
		# state variable declaration
		self.state = {	'status':'ACTIVE','sigma':0}
		
		# Local copy    
		self.row = col
		self.col = col
		self.neighborhood_method = neighborhoods[0]
		self.dtype = dtype
		
		self.matrix = np.array([None for x in range(row*col)], dtype=self.dtype).reshape(row,col)
		
		for x,y in map(lambda a: eval(str(a)),active_cell):
			self.matrix[x,y] = True
			
		### for plot
		self.x = np.arange(0, row+1)
		self.y = np.arange(0, col+1)
		self.X,self.Y = np.meshgrid(self.x,self.y)
		self.ims = []
		self.ims.append((plt.pcolor(self.X, self.Y, self.matrix),))
	
	
	def next_state(self, coords, el):
		# Gets all information from the neighbors
		(x, y) = coords
		
		
		if x==0:
			x1=0
		else:
			x1=x-1
			
		if x==self.row-1:
			x2=self.row-1
		else:
			x2=x+1

		if y==0:
			y1=0
		else:
			y1=y-1
			
		if y==self.col-1:
			y2=self.col-1
		else:
			y2=y+1
		
		neighbors = 0
		if self.neighborhood_method == "Moore":
			for n in self.matrix[x1:x2+1, y1:y2+1].flat:
				if n:
					neighbors += 1
		### TODO
		else:
			pass
		
		# Excludes the main element
		if el:
			neighbors -= 1
		
		if el: # el alives
			if neighbors==2 or neighbors==3:
				return True
			if neighbors<2 or neighbors>3:
				return False
		else: # el death
			if neighbors==3:
				return True
                
	###
	def intTransition(self):
		"""
		"""
		# copy the matrix
		old_matrix = self.matrix.copy()
		itr = self.matrix.flat
		coords = itr.coords
		for el in itr:
			old_matrix[coords] = self.next_state(coords, el)
			coords = itr.coords

		# copy all the modifications
		self.matrix = old_matrix
		
		### plot
		self.ims.append((plt.pcolor(self.X, self.Y, self.matrix),))
		
		if not self.matrix.max():
			self.state['sigma'] = INFINITY
		else:
			self.state['sigma'] = 1
		
	###
	def outputFnc(self):
		"""
		"""
		pass
	
	###
	def timeAdvance(self): return self.state['sigma']

	###
	def __str__(self): return "Gird"
