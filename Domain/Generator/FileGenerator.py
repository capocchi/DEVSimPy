# -*- coding: utf-8 -*-

"""
Name: FileGenerator.py
Brief descritpion: This module extract data from a standard CSV file and use it with DEVS formalism
Author(s): L. Capocchi <capocchi@univ-corse.fr>, B. Poggi <bpoggi@univ-corse.fr>
Version:  1.0
Last modified: 2011.11.16
GENERAL NOTES AND REMARKS:

If listValues parameters is empty, all columns are considered and only one output port send a list of row values.
If you want to change the output frequency, you can set the outPutFequency paramater.

GLOBAL VARIABLES AND FUNCTIONS:
"""

### at the beginning to prevent with statement for python vetrsion <=2.5
from __future__ import with_statement

from Domain.Generator.Generator import *

import os

class FileGenerator(Generator):
	""" FileGenerator atomic Model.
		This model, sends message from information contained in a file.
		The number of output can be one or more depending of the listValues parameter.
		If listValues is empty, only one ouptut port is used. If the listValues is composed by the column numbers,
		the number of output ports and the lenght of the listValues should be the same.
	"""

	def __init__(self, fileName=os.path.join(os.getcwd(), "fichier.csv"), listValues=[1], time=0, outPutFrequency=1.0, comma=" "):
		"""
		@param fileName : path of the data file
		@param listValues : considered columns numbers (as number of output)
		@param time : time column number
		@param outPutFrequency : sigma step
		@param comma : separating character (default space)

		"""

		Generator.__init__(self, fileName, listValues)

		self.V = self.initDictionnaryValues(listValues)

		self.time = time
		self.outPutFrequency = outPutFrequency
		self.__comma = comma

		if self.file_error_flag:
			with open(fileName, "rb") as f:
				for i,l in enumerate(filter(lambda b: b != '' , map(lambda a: a.replace('\n', ''), f.readlines()))):

					### ligne courante de valeurs et longueur
					row = map(lambda b:b.strip(), filter(lambda a: a!='', l.split(self.__comma)))
					lenght = len(row)

					### listValues est vide, liste de temps remplit avec entiers dependant de la frÃ©quence de sortie
					if self.list_empty_flag :
						t = i*self.outPutFrequency
					### listValues non vide alors la colonne de temps est spÃ©cifier par time
					else:
						t = row[self.time]

					### empty lines
					if t != '':
						self.T.append(float(t))
					else:
						continue

					### si listValues vide alors un seul port de sortie
					if self.list_empty_flag:
						self.V[0].append(row)
					else:
						### pour chaque port de sortie specifier dans listValues
						for val in self.V.keys():
							### si l'utilsiateur demande une colonne superieur au nombre de colonne dans le fichier -> derniere selectionnÃ©e
							if val >= lenght:
								self.V[val].append(row[lenght-1].strip())
							### l'utilisateur demande une colonne inferieur a 0 ou egale a 0 (colonne de temps) -> premiere selectionnÃ©e
							elif val < 0 or val == 0:
								self.V[val].append(row[1].strip())
							else:
								self.V[val].append(row[val].strip())

			sig = self.T[0] if self.T != [] else INFINITY
		else:
			sig = INFINITY

		self.state = {'status':'ACTIVE','sigma':sig}

	def __str__(self): return "FileGenerator"
