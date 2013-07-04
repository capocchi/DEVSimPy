# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#Classe Message.py --- message in network and in the node.
#                     --------------------------------
#                       Copyright (c) 2005
#                       Thierry Antoine-Santoni
#                      	University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 27/10/06
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
#  GLOBAL VARIABLES AND FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
import sys, os
#for spath in [os.pardir+os.sep+'Library']:
	#if not spath in sys.path: sys.path.append(spath)

class Message:
	###
	def __init__(self, v = None, t = None):
		''''	Constructor method.

			@param v: Value of the transaction
			@param t : simulation time
		'''

		# make local copy
		self.value 	= v
		self.time	= t
		self.name = ""

		if self.value:
			self.origin,self.parent,self.sender,self.destination,self.ndid,self.typ,self.hop,self.Temp,self.humidity,self.pressure,self.GPS,self.conso,self.hierarchy,self.lkq,self.Port= self.value
		else:
			self.origin		= ""
			self.parent		= ""
			self.sender		= ""
			self.destination	= ""
			self.ndid		= 0
			self.typ		= ""
			self.hop		= 0
			self.Temp		= 0
			self.humidity		= 0
			self.pressure		= 0
			self.GPS		= 0
			self.conso		= 0.0
			self.hierarchy	= ""
			self.lkq		= 0
			self.Port		= ""
  
  
	def __str__(self):
		return self.v
		
#class Message:
	
 #def __init__ (self, ori = "", part = "" ,send = "" ,dest = "", nid = 0, tp = "", hp = 0, tmp = 0, hu = 0, pres = 0, gps = 0, cns = 0.0, hchy ="", link = 0, Prt  = ""):
	
  #self.origin		= ori
  #self.parent		= part
  #self.sender		= send
  #self.destination	= dest
  #self.ndid		= nid
  #self.typ		= tp
  #self.hop		= hp
  #self.Temp		= tmp
  #self.humidity		= hu
  #self.pressure		= pres
  #self.GPS		= gps
  #self.conso		= cns
  #self.hierarchy	= hchy
  #self.lkq		= link
  #self.Port		= Prt
   		
 #def __str__(self):
  #return "< origin = %s,parent = %s ,sender = %s,destination = %s, ndid = %d, typ = %s, hop = %d, Temp = %d, humidity = %d, pressure = %d, GPS = %d, conso = %F, hchy = %s, link = %d, Prt = %s>"%(self.origin , self.parent ,self.sender ,self.destination , self.ndid , self.typ , self.hop , self.Temp , self.humidity , self.pressure , self.GPS, self.conso, self.hierarchy, self.lkq, self.Port)
####################################################################################################################