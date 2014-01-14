# -*- coding: utf-8 -*-
import pylab

def OnLeftDClick(self, event):
	model = self.getDEVSModel()
	coordinates = model.list
	
	#row = 0
	#col = 1
	#size = 0
	#colors = ['b--', 'r--']
	for k in coordinates:
		#row += 1
		#if size % 10 == 0:
		#	col += 1
		tup = coordinates[k]
		#pylab.subplot(row, 1, row)
		pylab.plot(tup[0], tup[1])
	pylab.show()
