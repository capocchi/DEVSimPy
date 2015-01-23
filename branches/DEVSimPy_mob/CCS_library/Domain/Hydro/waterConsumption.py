# -*- coding: utf-8 -*-

from DomainInterface.DomainBehavior import DomainBehavior
from Object import Message

### Model class ----------------------------------------------------------------
class waterConsumption(DomainBehavior):
        """
        This class model the water demand according to population (input)
        @author: Bastien POGGI
        @organization: University Of Corsica
        @contact: bpoggi@univ-corse.fr
        @since: 2010.10.10
        @version: 1.0
        """

	def __init__(self,ConsumptionPerTourist=1155):
            """
            @param ConsumptionPerTourist: average consumption
            """
            DomainBehavior.__init__(self)
            self.state = {
                                'status': 'OFF',
				'sigma':INFINITY,
                                'ConsumptionPerTourist':ConsumptionPerTourist,
                         }

	def extTransition(self):
                self.state['status'] = 'ON'
		self.state['sigma'] = 0

	def outputFnc(self):
            print "OUT"
            self.touristNumberIP = self.IPorts[0]
            self.consumptionOP = self.OPorts[0]
            
            if(self.state['status']!='OFF'):
                    population =  self.peek(self.touristNumberIP).value[0]
                    averageConso = self.state['ConsumptionPerTourist']
                    totalConsumption = population * averageConso
                    print totalConsumption
#                    totalConsumption = int(self.peek(self.touristNumberIP))[0] * self.state['ConsumptionPerTourist']

                    m = Message()
                    m.value = [totalConsumption,0.0,0.0]
                    m.time = self.timeNext

                    self.poke(self.consumptionOP,m)

	def intTransition(self):
                self.state['status']='OFF'
                self.state['sigma']=INFINITY

	def timeAdvance(self):
		return self.state['sigma']
            
        def __str__(self):
		return "waterConsumption"


