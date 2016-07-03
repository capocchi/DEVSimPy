# -*- coding: utf-8 -*-

"""
-------------------------------------------------------------------------------
 Name:          Image_Classifer.py
 Model:         Proceed to image classification using tensorflow 
 Authors:       L. Capocchi <capocchi@univ-corse.fr>
 Organization:  UMR CNRS 6134
 Date:          06.15.2016
 License:       GPL v.3
-------------------------------------------------------------------------------
"""

### Specific import ------------------------------------------------------------
from DomainInterface.DomainBehavior import DomainBehavior
from DomainInterface.Object import Message

import subprocess
import os

### Model class ----------------------------------------------------------------
class Image_Classifier(DomainBehavior):
	''' DEVS Class for Image_Classifier model
	'''

	def __init__(self, image_name="image.jpg", wait=True):
		''' Constructor.

			@param image_name : name of image to classify
			@param wait : wait the end of the procces to send message
		'''
		DomainBehavior.__init__(self)

		self.image_name = image_name
		if not os.path.isfile(self.image_name):
			basename = os.path.basename(self.image_name)
			self.image_name = os.path.join('/opt', 'celine', 'mysite', 'static','img', basename)
			
		self.wait = wait
		
		#self.process_file=os.path.join(os.path.dirname(os.path.dirname(inspect.getfile(DomainBehavior))),'Domain', 'TensorFlow', 'test.py')
	
		self.process_file=os.path.join('/opt', 'celine', 'devsimpy', 'version-2.9', 'Domain', 'TensorFlow', 'test.py')
	
		self.state = {	'status': 'SEND', 'sigma':0}

	def extTransition(self):
		''' DEVS external transition function.
		'''
		self.state['sigma'] = INFINITY

	def outputFnc(self):
		''' DEVS output function.
		'''
		if self.state['status'] == 'SEND' and os.path.isfile(self.image_name):
			
			process = subprocess.Popen(['python', self.process_file, self.image_name], stdout=subprocess.PIPE)
			if self.wait:
				process.wait()
			out = process.communicate()[0]
			#print(out)
			# Adjust form of result : 
			# Turn the string to an array of (label, score) objects
			result=[]
			for value in out.split('\n'):
				list = value.split(' (score = ')
				if len(list) == 2:
					label = list[0]
					score = list[1].replace(')', '')
					result.append({'label':label, 'score':float(score)})
			self.poke(self.OPorts[0], Message([result,0,0], self.timeNext))

	def intTransition(self):
		''' DEVS internal transition function.
		'''
		self.state['sigma'] = INFINITY
		self.state['status'] = 'IDLE'

	def timeAdvance(self):
		''' DEVS Time Advance function.
		'''
		return self.state['sigma']

	def finish(self, msg):
		''' Additional function which is lunched just before the end of the simulation.
		'''
		pass
