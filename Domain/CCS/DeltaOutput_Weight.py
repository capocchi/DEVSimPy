# -*- coding: utf-8 -*-

"""
-------------------------------------------------------------------------------
 Name:        <DeltaOutput_Weight.py>

 Model:       <New model added to a neural network to  calculate for a spacific layer its weight during learning phase>
 Author:      <Samuel TOMA>

 Created:     <2010-11-25>
-------------------------------------------------------------------------------
"""

### Specific import ------------------------------------------------------------
from DomainInterface.DomainBehavior import DomainBehavior
from Domain.Basic.Object import Message
#from simulation_object import SingeltonData
import random

### Model class ----------------------------------------------------------------
class DeltaOutput_Weight(DomainBehavior):
	
	def __init__(self):
		""" constructor.
		"""
		
		DomainBehavior.__init__(self)
		self.state = {	'status': 'Idel', 'sigma':INFINITY}
		self.layerId = None
		self.outError = {}
		self.sim = None
		self.msgListOut = [Message([None,None,None],0.0),Message([None,None,None],0.0)]
		
	def extTransition(self):
		""" receiving Errors and calculates new weights """
		for port,msg in self.peek_all(): 
			i = port.myID
			msg = self.peek(self.IPorts[i])
			
			if i == 0:
				self.sim = msg.value[0]
				self.layerId = msg.value[2]
			else:
				self.sim.errors = msg.value[0]
				self.outError = self.run(self.sim)
				self.state = {'status': 'ACTIVE', 'sigma':0}
		

	def run(self,sim):
		m = {}
		deltas = {}
		outError = {}
		for j in sim.wh:
			m[j] = self.dactivation(sim.outputs[j],sim.activation)
			deltas[j] = m[j]* float(sim.errors[j])
			for k in sim.wh[j]:
				change = deltas[j]*sim.inputs[k]
				try:
					outError[k] = outError[k] + deltas[j]*sim.wh[j][k]
				except:
					outError[k] = deltas[j] * sim.wh[j][k]
				sim.wh[j][k] = sim.wh[j][k]+sim.N*change + sim.M*sim.c[j][k]
				sim.c[j][k] = change
		return outError
	
	def outputFnc(self):
		if (len(self.outError)) != 0:
			msgError = self.msgListOut[0]
			msgError.value = [self.outError,None,None]
			msgSim = self.msgListOut[1]
			msgSim.value = self.sim
			self.poke(self.OPorts[1], msgError)
			self.poke(self.OPorts[0],msgSim)

	def intTransition(self):
		self.state = {'status': 'Idle', 'sigma':INFINITY}
	
	"""#def print_weight(self):
		#f = open(self.fileName,'a')
		#f.write(str(datetime.datetime.today()))
		#f.write("settings of neural network at :\n")
		#f.write("\tweights:\n\t")
		#for l in self.w:
			#for r in l:
				#f.write("%f "%r)
			#f.write("\n\t")
		#f.write("\n")
		#f.close()
	"""
	
	def concTransition(self):
		if self.state['status'] == 'ACTIVE':
			for Id in self.simData.simDico:
				try:				
					sim = self.simData.simDico[Id][self.layerId]
					errors = self.run(sim)
					self.simData.simDico[Id][sim.previousId].errors = errors
				except:
					pass
		
	def timeAdvance(self):
		return self.state['sigma']
	
	def dactivation(self,y,function="sigmoid"):
		if function == "tanh":
			return 1.0 - (y*y)    		# tanh
		elif function == "sigmoid":
			return y-y*y			# sigmoid
		else:
			return 1.0