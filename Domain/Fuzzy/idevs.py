#!/usr/bin/python
# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# idevs.py --- classe de manipulation d'impr�cisions pour le formalisme DEVS
# idevs.py --- class manipulation inaccuracies for DEVS formalism
#
#                     --------------------------------
#                        Copyright (c) 2008
#                       Paul-Antoine Bisgambiglia
#			bisgambiglia@univ-corse.fr
#                      University of Corsica
#                     --------------------------------
# Version 4.0                                        last modified: 10/10/09
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
##
## GENERAL NOTES AND REMARKS:
##	Python 2.5.2 (r252:60911, Apr 21 2008, 11:12:42)
##	[GCC 4.2.3 (Ubuntu 4.2.3-2ubuntu7)] on linux2
##
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import sys,os, string, random
from math import *

for spath in ['../Lib']:
  if not spath in sys.path: sys.path.append(spath)

#from FilesGenerator import *

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
##									##
##		GLOBAL VARIABLES AND FUNCTIONS:				##
##									##
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

INC=0.01 # incrementation
DEC=1	# decimal des arrondis

def frange(start, end=None, inc=1.0):
    "A range function, that does accept float increments..."
	
    if end == None:
        end = start + 0.0
        start = 0.0

    L = []
    while 1:      
        next = start + len(L) * inc
        if inc > 0 and next >= end:
            L.append(str(next))
            break
        elif inc < 0 and next <= end:
            break
        L.append(str(next))
		
    return L

###
def realRound(value,decimal=DEC):
	''' Fonction qui arrondie un nombre � la d�cimale pres
	    function witch round value
	'''
	if decimal<=1: num =10
	elif decimal==2: num =100
	elif decimal==3: num =1000
	elif decimal==4: num =10000
	elif decimal>=5: num =100000
	return floor(value*num)/num

###
def intRound(value):
	''' Fonction qui arrondie a l'entier pres
	'''
	if value >=  0:
		return floor(value+0.5)			# math.floor(3.14159) => 3.0
	else:
		return ceil(value-0.5)			# math.ceil(3.14) => 4.0
###
def secondDegreeEq(a,b,c):
  ''' equation du second degré de type ax2+bx+c=0
  '''
  delta = pow(b,2)-4*a*c
  if a==b==0:
    return 0
  if a == 0: return -(c/b)
  elif delta > 0:
    return [(-b+sqrt(delta))/(2*a),(-b-sqrt(delta))/(2*a)]
  elif delta == 0:
    return -b/(2*a)
  else:
    return 0.0
  
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
##									##
##				fonctions de fuzzification		            ##
##									##
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
def fuzzifierPrC(value_a,value_b,leftPrC=10,rightPrc=10):
      ''' fonction qui fuzzifie value à partir d'un pourcentage => fonction triangulaire
      '''
      return FuzzyInt(a=value_a,b=value_b,psi=value_a-(leftPrC*abs(value_a))/100,omega=value_b+(rightPrc*abs(value_b))/100)
#
def fuzzifierKernel(value,kernelPrC=10,RaduisPrc=10):
      ''' fonction qui fuzzifie value à partir d'un pourcentage => fonction trapézoïdale
      '''
      return FuzzyInt(a=value-(kernelPrC*abs(value))/100,
		      b=value+(kernelPrC*abs(value))/100,
		      psi=(value-(kernelPrC*abs(value))/100)-(RaduisPrc*abs(value-(kernelPrC*abs(value))/100))/100,
		      omega=(value+(kernelPrC*abs(value))/100)+(RaduisPrc*abs(value+(kernelPrC*abs(value))/100))/100)

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
##									##
##				CLASS					##
##									##
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
##

class FuzzyInt:
	''' Classe qui d�crit un nouveau type de donn�e dit 'Impr�cis' sous forme triangulaire ou trap�zo�dale
	a et b repr�sentent les sommets de la fonction
	psi et omega les limites inf�rieur et supp�rieur
	alpha le rayon (alpha = a - psi) et beta le rayon (beta = omega - b)
	leftX et rightX repr�sente les �quations des fronts gauche et droite de la courbe en fonction de x (abscisse)
	leftL et rightL repr�sente les �quations des fronts gauche et droite de la courbe en fonction de lambda (ordonn�e)
	'''
	###
	nbr = 0
	def __init__(self, a = 0.0, b = 0.0, psi = 0.0, omega = 0.0, label="I"):
		''' fonction d'initialisation pseudo constructeur de la classe FuzzyInt avec psi et omega
		    initialization function with psi and omega
		'''
	
		# local copy
		self.a	 	= a				# left vertex
		self.b	 	= b				# right vertex
		self.psi 	= psi				# left limit
		self.omega 	= omega				# right limit
		self.alpha	= self.a - self.psi		# left radius
		self.beta	= self.omega - self.b		# right radius
		FuzzyInt.nbr+=1
		self.label	= label				# label
		self.name	= label+'_['+str(FuzzyInt.nbr)+']'	# name
	
	def left_fX(self,x):
		return float(x-self.psi)/(self.a - self.psi)	# left function
	def right_fX(self,x):
		return float(x-self.omega)/(self.b-self.omega)	# right function
	def left_fL(self,l):
		return float(l*self.psi+self.alpha)		# left front
	def right_fL(self,l):
		return float(self.beta-l*(self.beta-self.b))	# right front

	####
	def iRadius(self, a = 0.0, b = 0.0, alpha = 0.0, beta = 0.0, label="I"):
		''' fonction d'initialisation pseudo constructeur de la classe FuzzyInt avec alpha et beta
		    initialization function with alpha and beta
		'''
		return FuzzyInt(a=a,b=b,psi=a-alpha,omega=b+beta,label=label)
	###
	def inDico(self, inc = INC):	# inc permet d'utiliser la fct frange() avec un pas r�el (float)
		''' fonction qui remplit un dico avec des couples x,lambda (X => abscisse,L => ordonn�e)
		    function witch build a dico with (x,lambda)
		'''
		interval = {}							# dict
		for x in frange(self.psi,self.a,inc):				# left part
			interval.__setitem__(float(x),self.left_fX(float(x)))
		for x in frange(self.b,self.omega,inc):				# right part
			interval.__setitem__(float(x),self.right_fX(float(x)))
		return interval
	####
	def update(self, a, b, psi, omega, label="I"):
		''' fonction qui met � jour une instance de la classe
		    #update function for an instance	
		'''
		self.a	 	= a				# left vertex
		self.b	 	= b				# right vertex
		self.psi 	= psi				# left limit
		self.omega 	= omega				# right limit
		self.alpha	= self.a - self.psi		# left radius
		self.beta	= self.omega - self.b		# right radius
		self.label	= label				# label
		self.name	= label+'_['+str(FuzzyInt.nbr)+']'	# name
	####
	def cp(self, src):
		''' fonction qui copie src dans self
		    cp function src in self
		'''
		self.update(src.a, src.b, src.psi, src.omega)
	####
	def __len__(self):
            ''' renvoie la longueur de l'intervalle omega - psi
		    return omega - psi
	    '''
            return self.omega - self.psi
	###
	def abscissa(self,l):
                '''
                '''
                if (type(l) == int or type(l) == float):			# si le type est classique
                  return (self.left_fX(l),self.right_fX(l))
                else:
                  return None

	##
	def ordinate(self,value):
		''' renvoie l'ordonn�e pour la valeur value 
		'''
		if (type(value) == int or type(value) == float):			# si le type est classique
			if value < self.a:
				return self.left_fX(value)
			elif value > self.b:
				return self.right_fX(value)
			else:
				return 1.0
		else:
			return None
	##
	def kernel(self):
		''' renvoie le noyau / return the kernel
		'''
		return (self.a + self.b)/2
	#
	def is_(self,b):
		''' renvoie vrai si b est du meme type que self
		'''
		return isinstance(b,type(self))
	##
	def __abs__(self):
		''' abs
		'''
		l = [abs(self.a),abs(self.b),abs(self.psi),abs(self.omega)]
		l.sort()
		res = FuzzyInt(a=l[1],b=l[2],psi=l[0],omega=l[3])
		return res
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## #
#									#
#			OPERATOR					#
#									#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## #
	####
	def supMin(self,interval,operator,inc=INC):
		''' Principe d'extension pour les operations
			#/!\ ALGO LENT surtout pour la multiplication 
		    #Extension principle for operator
		'''
		minList = []			# liste (x,l) avec les min de l [(3,0),(4,0),(6,1),(4,1),(6,0),(7,0))]
		supList = []			# liste (x,l) avec pour tout x les max de l [(3,0),(4,1),(6,1),(7,0)]
		tmpList = []			# liste temporaire
		tmpDict = {}			# dict temporaire
		supDict = {}			# dico (x,l)
		selfDict = self.inDico()	# valeur de self
		interDict = interval.inDico()	# valeur de interval
		################# / by 0
		#if (operator == '/' and interval.psi == 0 or interval.omega == 0):
		#  print "division par 0"
		size = self.omega - self.psi
		inc = (inc * size)/10
		################# Algo du MIN
		try:
		  for x in frange(eval(str(self.psi)+operator+str(interval.psi)),eval(str(self.omega)+operator+str(interval.omega)),inc):
			  for y in selfDict.keys(): 		# frange(self.psi,self.omega,inc):
				  for z in interDict.keys(): 	# frange(interval.psi,interval.omega,inc):
					  if (eval(str(y)+operator+str(z))==float(x)):
						  minList.append((float(x),min(selfDict[y],interDict[z])))
								  ## list avec les ordonn�es min
		except ValueError:
		  return 0.0
		################ Algo du SUP
		for i in minList:
			if supList.__contains__(i)==False:
				for j in minList:
					if i[0]==j[0]:		# ecrasse les elements de m�me valeur
						tmpList.append(j)
				supList.append(max(tmpList))	# r�cup�re les max
				tmpList = []			# clear tmpList
		############### Creation d'un DICT
		for k in supList:
			supDict.__setitem__(k[0],k[1])		# dict couple
			if k[1]==1.0:
				tmpDict.__setitem__(k[0],k[1])	# dict values = 1
		############### RESULT
		c = min(tmpDict) 				# plus petite cle qui a pour valeur 1
		d = max(tmpDict) 				# plus grande cle qui a pour valeur 1
		e = min(supDict)
		f = max(supDict)
		g = self.label+operator+interval.label
		res = FuzzyInt(a=c,b=d,psi=e,omega=f,label=g)
		return res
	####
	def mult(self,value):
		''' Fonction de multiplication r�slutat approximatif
		'''
		s1 = [self.a*value.a,self.a*value.b,self.b*value.a,self.b*value.b]
		s2 = [(self.psi)*(value.psi),(self.psi)*(value.omega),(value.omega)*(self.psi),(value.omega)*(self.omega)]
		#print s1
		#print s2
		a = min(s1)
		b = max(s1)
		alpha = abs(min(s2)-min(s1))
		beta = abs(max(s2)-max(s1))
		res = FuzzyInt(a,b,a-alpha,b+beta,label=self.label+"*"+value.label)
		return res
	####
	def __add__(self, value):
          ''' Addition / add function (+) self + value
          '''
          res = FuzzyInt()
          if (type(value) in [int, float, long] and isinstance(self,FuzzyInt)):
            res.update(a = self.a+value, b = self.b+value, psi = self.psi + value, omega = self.omega+value)
            return res
          elif (type(value) == type(res)):						# si le type est FuzzyInt
            res.update(a = self.a+value.a, b = self.b+value.b, psi = self.psi + value.psi, omega = self.omega+value.omega, label=self.label+"+"+value.label)
            return res
          else:
            return self+value
	##
	def __radd__(self, value):
          ''' value + self
          '''
          res = FuzzyInt()
          if (type(self) in [int, float, long] and isinstance(value,FuzzyInt)):
            res.update(a = value.a+self, b = value.b+self, psi = value.psi+self, omega = value.omega+self)
            return res
          else:
            return self+value
	###
	def __iadd__(self,value):
          ''' self+=value
          '''
          self = self+value
          return self
        ###
	def __sub__(self, value):
		''' soustraction / sub function (self-value)
		'''
		res = FuzzyInt()
		if (type(value) in [int, float, long] and isinstance(self,FuzzyInt)):
			res.update(a = self.a-value, b = self.b-value, psi = self.psi-value, omega = self.omega-value)
			return res
		elif (type(value) == type(res)):						# si le type est FuzzyInt
			res.update(a = self.a-value.b, b = self.b-value.a, psi = self.psi-value.omega, omega = self.omega-value.psi, label=self.label+"-"+value.label)
			return res
		else:
			return self-value
	##
	def __rsub__(self, value):
	      ''' value - self
	      '''
	      res = FuzzyInt()
	      if (type(self) in [int, float, long] and isinstance(value,FuzzyInt)):
		res.update(a = value.a-self, b = value.b-self, psi = value.psi-self, omega = value.omega-self)
		return res
	      else:
		return self-value
	###
	def __isub__(self,value):
		'''	 self-=value
		'''
		self = self-value
		return self
	##
	def __mul__(self, value):
		''' multiplication / mul function (*)
		    /!\ La multiplication est longue, voir pour l'effecter avec une autre formule
		'''
		res = FuzzyInt()
		if (type(value) in [int, float, long] and isinstance(self,FuzzyInt)):# si le type est classique
			if value < 0:
				res.update(a = self.b*value, b = self.a*value, psi = self.omega*value, omega = self.psi*value, label=self.label+"*"+str(value))
				return res
			else:
				res.update(a = self.a*value, b = self.b*value, psi = self.psi*value, omega = self.omega*value,label=self.label+"*"+str(value))
				return res
		elif (type(value) == type(res)):						# si le type est FuzzyInt
			#res = self.supMin(value,'*') # /!\ Lent
			res = self.mult(value)
			return res
		else:
			return self*value
	##
	def __rmul__(self, value):
		''' multiplication / mul function (*)
		    /!\ La multiplication est longue, voir pour l'effecter avec une autre formule
		'''
		res = FuzzyInt()
		if (type(self) in [int, float, long] and isinstance(value,FuzzyInt)):# si le type est classique
			if self < 0:
				res.update(a=value.b*self,b=value.a*self,psi=value.omega*self,omega=value.psi*self,label=value.label+"*"+str(self))
				return res
			else:
				res.update(a=value.a*self,b=value.b*self,psi=value.psi*self,omega=value.omega*self,label=value.label+"*"+str(self))
				return res
		else:
			return self*value
	###
	def __imul__(self,value):
		'''	 self*=value
		'''
		self = self*value
		return self
	##
	##
	def __div__(self, value):
		''' division / div function (/)
		'''
		res = FuzzyInt()
		if (type(value) in [int, float, long] and isinstance(self,FuzzyInt)):# si le type est classique
			if value < 0:
				res.update(a=self.b/value,b=self.a/value,psi=self.omega/value,omega=self.psi/value,label=self.label+"/"+str(value))
				return res
			else:
				res.update(a=self.a/value,b=self.b/value,psi=self.psi/value,omega=self.omega/value,label=self.label+"/"+str(value))
				return res
		elif (type(value) == type(res)):						# si le type est FuzzyInt
			res = self.supMin(value,'/')
			return res
		else:
			return self/value
	##
	def __rdiv__(self, value):
		''' division / rdiv function (*)
		'''
		res = FuzzyInt()
		if (type(self) in [int, float, long] and isinstance(value,FuzzyInt)):# si le type est classique
			if self < 0:
				res.update(a=value.b/self,b=value.a/self,psi=value.omega/self,omega=value.psi/self,label=value.label+"/"+str(self))
				return res
			else:
				res.update(a=value.a/self,b=value.b/self,psi=value.psi/self,omega=value.omega/self,label=value.label+"/"+str(self))
				return res
		else:
			return self/value
	###
	def __idiv__(self,value):
		'''	 self/=value
		'''
		self = self/value
		return self
	##
	def __floordiv__(self, value):
		''' division enti�re / int div function (//)
		'''
		res = FuzzyInt()
		if (type(self) in [int, float, long] and isinstance(value,FuzzyInt)):		# si le type est classique
			res.update(a = self.a//value, b = self.b//value, psi = self.psi//value, omega = self.omega//value, label="//")
			return res
		elif (type(value) == type(res)):						# si le type est FuzzyInt
			res = self.supMin(value,'//')
			return res
		else:
			return self//value
	##
	def __ifloordiv(self,value):
		''' a//=b
		'''
		self = self // value
		return self
	def __mod__(self, value):
		''' modulo / modulo (%)
		'''
		res = FuzzyInt()
		if (type(self) in [int, float, long] and isinstance(value,FuzzyInt)):			# si le type est classique
			res.update(a = self.a%value, b = self.b%value, psi = self.psi%value, omega = self.omega%value, label="%")
			return res
		elif (type(value) == type(res)):						# si le type est FuzzyInt
			res = self.supMin(value,'%')
			return res
		else:
			return self%value
	##
	def __imod__(self,value):
		''' a%=b
		'''
		self = self % value
		return self
	###
	def __pow__(self, value):
		''' puissance / pow (**)
		'''
		res = FuzzyInt()
		if (type(self) in [int, float] and isinstance(value,FuzzyInt)):		# si le type est classique
			res.update(a = self.a**value, b = self.b**value, psi = self.psi**value, omega = self.omega**value, label="**")
			return res
		elif (type(value) == type(res)):						# si le type est FuzzyInt
			res = self.supMin(value,'**')
			return res
		else:
			return self**value
	##
	def __cmp__(self, value):
		''' equals (==)
		'''
		if not isinstance(value,FuzzyInt):
		  return False
		else:
		  return (self.integrant() == value.integrant())
	##
	def __lt__(self, value):
		''' plus petit / strictly lower (<)
		'''
		if self.__len__() < value.len:
			return True
		else:
			return False
	##
	def __le__(self, value):
		''' plus petit ou �gal / lower or equals (<=)
		'''
		if self.__len__() <= value.len:
			return True
		else:
			return False
	##
	def __gt__(self, value):
		''' plus grand /  strictly higher (>)
		'''
		if self.__len__() > value.__len__:
			return True
		else:
			return False
	##
	def __ge__(self, value):
		''' plus grand ou �gal / higher or equals (>=)
		'''
		if self.__len__() >= value.__len__:
			return True
		else:
			return False
	##
	def __and__(self, value):
		''' et logique / and (&)
		'''
		if type(self) and type(value):
			return True
		else:
			return False
	##
	def __or__(self, value):
		''' ou / or (|)
		'''
		if type(self) or type(value):
			return True
		else:
			return False
	##
	#def __xor__(self, value):
		#''' ou ex / or (^)
		#'''
		#return None
	#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## #
#									#
#				MATH					#
#									#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## #
	##
	#def sq(self):
		#''' fonction qui renvoie le carr�e de l'intervalle inter
		    #function witch return the square of the interval inter
		    #/!\ a revoir selon les cas
		#'''
		#if self.psi > 0:
			#res = FuzzyInt(a=self.a**2,b=self.b**2,psi=self.psi**2,omega=self.omega**2,label=self.label+'**2')
			#return res
		#elif self.omega < 0:
			#res = FuzzyInt(a=self.b**2,b=self.a**2,psi=self.omega**2,omega=self.psi**2,label=self.label+'**2')
			#return res
		#elif abs(self.a) < self.b:
			#res = FuzzyInt(a=self.a**2, b=self.b**2, psi=(self.a**2 - self.alpha**2), omega= (self.b**2 + self.beta**2),label=self.label+'**2')
			#return res
		#else:
			#res = FuzzyInt(a=self.b**2, b=self.a**2, psi=self.b**2 - self.alpha**2, omega= self.a**2 + self.beta**2,label=self.label+'**2')
			#return res
	##
	#def sqrt(self):
		#''' fonction qui renvoie la racine carr�e de l'intervalle inter
		    #function witch return the square root of the interval inter
		#'''
		#res = FuzzyInt(a=sqrt(self.a),b=sqrt(self.b),psi=sqrt(self.psi),omega=sqrt(self.omega),label="sqrt")
		#return res 
	##
	#def sin(self):
		#''' fonction qui renvoie le sinus de l'intervalle inter
		    #function witch return the sine of the interval inter
		    #/!\ fonction experimentale
		#'''
		#a = min(sin(self.a),sin(self.b))
		#b = max(sin(self.a),sin(self.b))
		#res = self.iRadius(a=a,b=b,alpha=self.alpha,beta=self.beta,label="sin")
		#return res
	##
	#def cos(self):
		#''' fonction qui renvoie le cosinus de l'intervalle inter
		    #function witch return the cosine of the interval inter
		    #/!\ fonction experimentale
		#'''
		#a = min(cos(self.a),sin(self.b))
		#b = max(cos(self.a),sin(self.b))
		#res = self.iRadius(a=a,b=b,alpha=self.alpha,beta=self.beta,label="cos")
		#return res
	##
	#def tan(self):
		#''' fonction qui renvoie la tan de l'intervalle inter
		    #function witch return the tangent of the interval inter
		    #/!\ fonction experimentale
		#'''
		#a = min(tan(self.a),tan(self.b))
		#b = max(tan(self.a),tan(self.b))
		#res = self.iRadius(a=a,b=b,alpha=self.alpha,beta=self.beta,label="tan")
		#return res
	##
	#def sinD(self):
		#''' fonction qui renvoie le sinus de l'intervalle inter en degre
		    #function witch return the sine of the interval inter degree angle
		    #/!\ fonction experimentale
		#'''
		#degree = pi/180
		#a = min(sin(self.a*degree),sin(self.b*degree))
		#b = max(sin(self.a*degree),sin(self.b*degree))
		#res = self.iRadius(a=a,b=b,alpha=self.alpha,beta=self.beta,label="sin")
		#return res
	##
	#def cosD(self):
		#''' fonction qui renvoie le cosinus de l'intervalle inter en degre
		    #function witch return the cosine of the interval inter degree angle
		    #/!\ fonction experimentale
		#'''
		#degree = pi/180
		#a = min(cos(self.a*degree),sin(self.b*degree))
		#b = max(cos(self.a*degree),sin(self.b*degree))
		#res = self.iRadius(a=a,b=b,alpha=self.alpha,beta=self.beta,label="cos")
		#return res
	##
	#def tanD(self):
		#''' fonction qui renvoie la tan de l'intervalle inter en degre
		    #function witch return the tangent of the interval inter degree angle
		    #/!\ fonction experimentale
		#'''
		#degree = pi/180
		#a = min(tan(self.a*degree),tan(self.b*degree))
		#b = max(tan(self.a*degree),tan(self.b*degree))
		#res = self.iRadius(a=a,b=b,alpha=self.alpha,beta=self.beta,label="tan")
		#return res
	#
	def integrant(self):
		''' fonction qui renvoie l'aire entre psi et omega
		    funtion wicth return the area between psi and omega
		'''
		if self.a-self.psi == 0.0: self.psi-=1		# gestion d'une exeption
		if self.b-self.omega == 0.0: self.omega+=1	# gestion d'une exeption
		c = self.a-self.psi
		d = self.b-self.omega

		# integrale entre psi et omega
		return (self.omega**2/(2.0*c) - (self.psi*self.omega)/c - self.psi**2/(2.0*c) + self.psi**2/c + self.omega**2/(2.0*d) - self.omega**2/d - self.psi**2/(2.0*d) + (self.omega*self.psi)/d)
	###
	def integrantX(self,x):
		''' fonction qui renvoie l'aire entre psi et x + psi et x
		    funtion wicth return the area between psi and x + between psi and x
		'''
		if self.a-self.psi == 0.0: self.psi-=1		# gestion d'une exeption
		if self.b-self.omega == 0.0: self.omega+=1	# gestion d'une exeption
		a = self.a
		b = self.b
		c = self.a-self.psi
		d = self.b-self.omega

		if x<self.psi:
			x=self.psi
		# integrale entre psi et x
		left = x**2/(2.0*c) - (self.psi*x)/c - self.psi**2/(2.0*c) + self.psi**2/c
		if x>self.omega:
			x=self.omega
		# intregrale entre b et x
		right = x**2/(2.0*d) - (self.omega*x)/d - self.psi**2/(2.0*d) + (self.omega*self.psi)/d
		return (left+right)
	###
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## #
#									#
#			DEFUZZIFICATION					#
#									#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## #
	#
	def defSurface(self):
		''' ((B+b)*h)/2
		'''
		return ((self.omega-self.psi) + (self.b - self.a))/2
	##
	def defCentroid(self):
		''' Centroid defuzzification returns the center of area under the curve.
		    http://fr.wikipedia.org/wiki/Calcul_du_centre_de_gravit%C3%A9_d%27un_polygone 
		''' 
		gB = self.omega-self.psi # grand base
		pB = self.b-self.a	 # petite base
		gM = gB/2		# milieu
		pM = pB/2		# milieu
		#hy = sqrt(pow((gM-pM),2)+1)
		return gM*((gB+2*pB)/(pB+gB))
	##
	def defBisector(self):
		''' The bisector is the vertical line that will divide the region into two sub-regions of equal area. It is sometimes, but not always coincident with the centroid line.
		eq. b1: y=(x-omega)/(a-omega)
		eq. b2: y=(x-psi)/(b-psi)
		res <- b1=b2
		'''
		res = self.psi*self.a - self.omega*self.b
		res/= self.a - self.omega - self.b + self.psi
		return res
	##
	def defMiddleofBase(self):
		''' Middle of base
		'''
		return (self.omega + self.psi)/2
	##
	def defMiddleofMaximum(self):
		''' Middle of Maximum
		'''
		return (self.b + self.a)/2
	##
	def defSmallestofMaximun(self):
		''' Smallest of Maximum
		'''
		return self.a
	##
	def defLargestofMaximun(self):
		''' Largest of Maximum
		'''
		return self.b
	##
	def defIntegrantL(self):
		''' fonction de defuzzification par integration qui renvoie l'int�grale de l'instance
		    defuzzification funtion wicth return the integrant value
		'''
		inte = self.psi + (self.a-self.psi)/2		# integrale du front gauche entre 0 et 1
		inte+= self.omega - (self.omega-self.b)/2	# integrale du front droit entre 0 et 1
		return inte/2
	##
	def defAnglaniEEM(self,coef=0.5):
		''' Fonction qui renvoie la date prevue d'execution
		    Expected existence measure function
		'''
		a = self.alpha - self.beta
		b = 2 * (self.psi * self.beta - self.omega * self.alpha)
		c = 2 * coef * self.integrant() * self.alpha * self.beta + self.psi*(2*self.omega*self.alpha - self.psi*self.alpha-self.psi*self.beta)
		res = secondDegreeEq(a,b,c)
		if type(res) == list:
		  return res[1]
		else:
		  return res
	####
	def defAnglaniCOEF(self,coef=0.5,inc=INC):
		''' Seconde partie de la fonction recherche  anglaniEEM()==coef
		    second part of the anglani function we seek anglaniEEM()==coef
		'''
		size = self.omega - self.psi
		inc = (inc * size)/10
		Li=map(lambda a: float(a),frange(self.psi,self.omega+inc,inc))
		Lv=map(lambda a:realRound(self.integrantX(float(a)) / self.integrant()) ,Li)
		
		#if coef >Lv[len(Li)/2]:
			#Li=Li[len(Li)/2:len(Li)]
			#Lv=Lv[len(Lv)/2:len(Lv)]
		#else:
			#Li=Li[0:len(Li)/2]
			#Lv=Lv[0:len(Lv)/2]

		#assert(len(Li)==len(Lv))
		try:
			return Li[Lv.index(coef)]
		except ValueError:
			return 0.0
		
		#Lr=map(lambda a: float(a),frange(self.psi,self.omega+inc,inc))
		#L=map(lambda a: (a,realRound(self.integrantX(float(a)) / self.integrant())),Lr)
		#D=dict(L)
		#try:
			#return [k for k, v in D.iteritems() if v == coef][0]
		#except IndexError:
			#return 0.0
		
		#for v in map(lambda a: float(a),frange(self.psi,self.omega+inc,inc)):
		############# Solution 1 ######################
			#if realRound(self.integrantX(v) / self.integrant())==coef:		# On arrondie le r�sultat
				#return v
		#return 0.0
	####
	def defuzzDEVS(self,L=[],coef=0.5,inc=INC,method='EEM'):
		''' Fonction de deuzzification pour DEVS compte le nombre de defuzz.
		'''
		# time defuzzification recupere la valeur defuzzifiee
		if method == 'surface':
		  tmpRes = self.defSurface()
		  name = 'Surface'
		elif method == 'bisector':
		  tmpRes = self.defBisector()
		  name = 'Bisector'
		elif method == 'centroid':
		  tmpRes = self.defCentroid()
		  name = 'Centroid'
		elif method == 'lmax':
		  tmpRes = self.defLargestofMaximun()
		  name = 'Largest of Maximun'
		elif method == 'mmax':
		  tmpRes = self.defMiddleofMaximum()
		  name = 'Middle of Maximum'
		elif method == 'smax':
		  tmpRes = self.defSmallestofMaximun()
		  name = 'Smallest of Maximun'
		elif method == 'base':
		  tmpRes = self.defMiddleofBase()
		  name = 'Middle of Base'
		elif method == 'integrant':
		  tmpRes = self.defIntegrantL()
		  name = 'Integrant'
		elif method == 'coef':
		  tmpRes = self.defAnglaniCOEF(coef=coef,inc=inc)
		  name = 'EEM (1)'
		elif method == 'eem':
		  tmpRes = self.defAnglaniEEM(coef=coef)
		  name = 'EEM (2)'
		else:
		  tmpRes = self.defAnglaniEEM(coef=coef)
		  name = 'EEM (2)'
		#
		L.append(self.ordinate(tmpRes))		# membership degree recupere le degres d'appartenance
		return {'method':name, 'result':tmpRes, 'mDegree':L, 'average':sum(L) / len(L)}
	####
	#def anglanInDict(self,inc=INC):
		#''' Affichage du tout dans un dico caster en string
		#'''
		#dic = {}
		#r = self.psi
		#while r<=self.omega:
			#val1 = realRound(self.anglaniEEM(r))
			#val2 = realRound(self.ordinate(r))
			#dic.__setitem__(str(r),(str(val2),str(val1)))
			#r+=inc
		##print dic
		#return dic
	####
	#def anglanInDict2(self,inc=INC):
		#''' Affichage du tout dans un dico caster en float
		#'''
		#dic = {}
		#r = self.psi
		#while r<=self.omega:
			#val1 = realRound(self.anglaniEEM(r))
			#val2 = realRound(self.ordinate(r))
			#dic.__setitem__(float(r),(float(val2),float(val1)))
			#r+=inc
		##print dic
		#return dic

        ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## #
        #									        #
        #				PRINT					        #
        #									        #
        ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## #
	####
	def __repr__(self):
		''' Affichage / print
		'''
		psi = str(self.psi)
		a = str(self.a)
		b = str(self.b)
		omega = str(self.omega)
		string = self.label +' =[' +psi+ ';' +a+ ';' +b+ ';' +omega+ ']'
		return str(string)

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
##									##
##				CLASS					##
##									##
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
##
class FuzzySets:
	''' Encapsulation of a FuzzyInt (Fuzzy Set).
	'''
	###
	nbr = 0
	def __init__(self, subSets, name):
            ''' build Fuzzy Sets
            '''
            self.subSets = subSets
            FuzzySets.nbr+=1
            self.name = name+'_['+str(FuzzySets.nbr)+']'
            self.size = len(self.subSets)
        ###
        def addSubSet(self, subSet):
            ''' add a subset
            '''
            self.subSets.append(subSet)
            self.size = len(self.subSets)
        ###
        def addNewSubSet(self,a,b,psi,omega,label):
            ''' add a new subset
            '''
            self.addSubSets(FuzzyInt(a,b,psi,omega,label))
        ###
        def updateName(self,newName):
            '''
            '''
            self.name = newName+'_['+str(FuzzySets.nbr)+']'
        ###
        def valueIs(self):
          ''' Returns list of sets in which
              the tested value has a member value
              greater then the threshold.
          '''
	  pass
        ###
        def valueInSet(self):
          ''' Returns the membership value in a specific set
          '''
	  pass
	###
        def selfLearning(self):
          ''' rules 
          '''
	  pass
        ###
	def findValue(self,value):
	  ''' find in FuzzySets a subset which contains the value
	  /!\ operator MAX
	  Returns the membership value and label in FuzzySet
	  '''
          res = {}
	  for i in self.subSets:
	    if value >= i.psi and value <= i.omega:
	      res.update({i.label:i.ordinate(value)})
          md = max(res.values())
          #md = min(res.values())
	  return [(k,v) for k, v in res.iteritems() if v == md][0]
          ###
	def findLabel(self, label, md):
	    ''' Returns subset with name matching label.
	    '''
	    for i in self.subSets:
	      if i.label == label:
		return i.abscissa(md)
	###
	def setLabels(self):
	    '''
	    '''
	    setLabels = []
	    for i in self.subSets:
	      setLabels.append(i.label)
	    return setLabels
	###
	def __repr__(self):
	    ''' Affichage / print
	    '''
	    string = 'Name:'+self.name+'\n Size:'+str(self.size)+'\n Sets'+str(self.subSets)+''
	    return str(string)
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
##									##
##				fonctions de création du SIF            ##
##									##
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
def newFuzzySets():
  '''
  '''
  lstSet = []
  print "Name of FuzzySets ? "
  name = input()
  name = str(name)
  print "Number of sets ? "
  nbr = input()
  nbr = int(nbr)
  for i in range(0,nbr):
    print "Set_["+str(i)+"] : (min,vertex,max,'label')"
    lstValue = input()
    lstSet.append(FuzzyInt(psi=lstValue[0],a=lstValue[1],b=lstValue[1],omega=lstValue[2],label=lstValue[3]))
  res = FuzzySets(lstSet,name)
  print res
  return res
  
 
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## #
#									#
#				TEST					#
#									#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## #

###########
if __name__  ==  "__main__":
	#''' /!\ Probleme avec la soustraction et la fonction supMin !
	    #/!\ Probleme avec la division par zero
	    #/!\ Probleme avec la multiplication et la fonction supMin Lenteur
	    #/!\ Probleme avec les op�ration /,//,%,**, la fonction supMin marche moyen
	#'''
	print "*********************************"
	print "*		TEST		*"
	print "*********************************"
	#v = 5
	#z = FuzzyInt(v,v,math.fabs(v)*(1-0.15),10000)
	#print z.anglaniCOEF(inc=0.1)
	#a = FuzzyInt(2,40,-10,70)
	#print a
	#print "def surface \t", a.defuzzDEVS(method='surface')
	#print "def integral \t", a.defuzzDEVS(method='integrant')
	#print "def mid of base \t", a.defuzzDEVS(method='base')
	#print "def mid of Max \t", a.defuzzDEVS(method='mmax')
	#print "def centroid \t", a.defuzzDEVS(method='centroid')
	#print "def bisector \t", a.defuzzDEVS(method='bisector')
	#print "def EEM \t", a.defuzzDEVS(coef=0.5,method='coef')
	#print "def coef \t", a.defuzzDEVS(coef=0.5,method='eem')
	#############
	a = FuzzySets([FuzzyInt(2,2,0,4,'c'),FuzzyInt(4,4,2,6,'f'),FuzzyInt(6,6,4,8,'t')],'test')
	print a.findLabel('f',0.9)
	print a.findValue(3)
	print a.setLabels()