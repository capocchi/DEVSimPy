# -*- coding: utf-8 -*-

#Author : Bastien POGGI
#Mail : bpoggi@univ-corse.fr
#Corporation : University Of Corsica Laboratory SPE
#Description : The library to get data from Google Fusion Table
#Date : 2010-09-30
 
from .ftclient import GoogleClientLogin, FTClient
from math import fabs

import urllib.request, urllib.error, urllib.parse

class Request:
	def __init__(self, tableID, time, data, login, password):

		#Query
		query = "SELECT '" + time + "','" + data + "' FROM " + tableID

		### try connexion
		try:
			con = urllib.request.urlopen("http://173.194.32.32/") ### google
			#con = urllib2.urlopen("http://www.google.fr")
			#data = con.read()
		except urllib.error.URLError:
			self.listTime = []
			self.listData = []
			print("No connexion for fusionTable in Generator library!")
		else:
			if login != "" and password != "":
				#Connexion
				connexion = GoogleClientLogin(login, password)
				client = (FTClient(connexion))

				#Query execution
				result = client.runPostQuery(query)

				#Query interpretation
				self.listResult = result.split("\n") #Decoupage ligne
				del self.listResult[0] #Supression de l'entete
				self.listTime=[]
				self.listData=[]
				for line in self.listResult:
					lineCut = line.split(",")
					self.listTime.append(lineCut[0])
					if(len(line)>1): # Si on a la semaine mais pas de valeur dans la base
						self.listData.append(lineCut[1])

				self.listData = list(map(charToFloat,self.listData))
				self.listTime = list(map(charToInt,self.listTime))
			else:
				self.listTime=[0]
				self.listData=[0]
			
	def getListData(self):
		return self.listData

	def getListTime(self):
		return self.listTime

	def getDifference(self):
		size = len(self.listData)
		indice = 1
		resultList = [0]
		while(indice<size):
			resultList.append(fabs(self.listData[indice]-self.listData[indice-1]))
			indice += 1
		return resultList

	def showData(self):
		cpt = 0
		for i in self.listData:
			print("Ligne " + str(cpt) + " Valeur " + str(i))
			cpt += 1

	def getResult(self):
		return self.listData

#Internal functions
def charToFloat(char):
	if char == "":
		return 0
	else:
		return float(char)

def charToInt(char):
	if char =="":
		return 0
	else:
		return int(char)

if __name__ == '__main__':
	myRequester = Request("264928","Semaine","1994") #ID TABLE | ANNEE