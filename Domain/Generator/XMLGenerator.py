# -*- coding: utf-8 -*-

from Generator.Generator import *
from xml.dom import minidom
import os.path

class XMLGenerator(Generator):
	"""
	This module extract data from a standard XML file and use it with DEVS formalism
	@author: Bastien POGGI
	@organization: University Of Corsica
	@contact: bpoggi@univ-corse.fr
	@since: 2010.10.23
	@version: 1.0
	@attention: The list parameter are case sensitive
	"""

	def __init__(self, fileName=os.path.join(os.getcwd(),"fichier.xml"),line="line",listValues=["temperature","humidity","luminosity"],time="time",outPutFrequency=1.0):
		"""
			@param fileName : The name of the input XML file
			@param line : The tag for the whole recording
			@param listValues : The list of each filter tag
			@param time : The time tag
			@param outPutFrequency : The frequency of send

			@fileName :file path of model
			@line : name of attribut line
			@listValues : numbers or strings of considered columns
			@time : name of time column
			@outPutFrequency : sigma step
		"""

		Generator.__init__(self,fileName, listValues)

		self.line = line
		self.time = time
		self.outPutFrequency = outPutFrequency
		self.V = self.initDictionnaryValues(listValues)

		if os.path.exists(self.sourceName):
			myFile = minidom.parse(self.sourceName)
			allData = myFile.getElementsByTagName(self.line)

			for data in allData:
				self.T.append(int(data.getElementsByTagName(time)[0].firstChild.data))
				for value in listValues:
					d = float(data.getElementsByTagName(value)[0].firstChild.data)
					self.V[value].append(d)

		### if xml file and time data exists
		sig = self.T[0] if self.T != [] else INFINITY

		self.state = {'status':'ACTIVE','sigma':sig}

	def __str__(self):
		return "XMLGenerator"


