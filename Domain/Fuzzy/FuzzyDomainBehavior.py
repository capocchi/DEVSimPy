# -*- coding: utf-8 -*-

from DomainInterface.DomainBehavior import DomainBehavior, Master
from idevs import *

class FuzzyDomainBehavior(DomainBehavior):
    '''	Abstract class of Fuzzy Behavioral Domain.
    '''

    ###
    def __init__(self):
	    ''' Constructor method.
	    '''
	    DomainBehavior.__init__(self)

    ###
    def timeAdvance(self):
      self.state['simulTime']+=self.state['sigma']	# increment final simulation time
      tmp = self.state['simulTime']			# 
      if type(self.state['sigma']) == type(tmp):	# if the time is fuzzy
	res = tmp.anglaniCOEF()		# time defuzzification
	nbDefuz=+1				# defuzzification ++ 
	somL+= tmp.ordinate(res)		# membership degree
	self.state['average'] = somL / nbDefuz
	return res
      else:
	return self.state['sigma']