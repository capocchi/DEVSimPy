if (self.msgProcessFrom.typ == "ACK"):
			self.msgProcessFrom = self.FiFoOut.pop(0)
			self.msgWF0 = copy.copy.msgProcessFrom
			self.msgWF0.typ = "WhiteFlag"
			self.msgWF1 = copy.copy.msgProcessFrom
			self.msgWF1.typ = "WhiteFlag"
			self.msgWF2 = copy.copy.msgProcessFrom
			self.msgWF2.typ = "WhiteFlag"
			if (self.msgProcessFrom.destination == self.DirectionSet[0,0]):
				self.poke(self.DirectionSet[0,0], self.msgProcessFrom)			
				self.msgWF0.destination = self.DirectionSet[1,0]
				self.msgWF1.detination = self.DirectionSet[2,0]	
				self.msgWF2.destination = self.DirectionSet[3,0]
			elif (self.msgProcessFrom.destination == self.DirectionSet[1,0]):
				self.poke(self.DirectionSet[1,0], self.msgProcessFrom)		
				self.msgWF0.destination = self.DirectionSet[0,0]
				self.msgWF1.detination = self.DirectionSet[2,0]	
				self.msgWF2.destination = self.DirectionSet[3,0]
			elif (self.msgProcessFrom.destination == self.DirectionSet[2,0]):
				self.poke(self.DirectionSet[2,0], self.msgProcessFrom)						
				self.msgWF0.destination = self.DirectionSet[0,0]
				self.msgWF1.detination = self.DirectionSet[1,0]	
				self.msgWF2.destination = self.DirectionSet[3,0]
			elif (self.msgProcessFrom.destination == self.DirectionSet[3,0]):
				self.poke(self.DirectionSet[3,0], self.msgProcessFrom)		
				self.msgWF0.destination = self.DirectionSet[0,0]
				self.msgWF1.detination = self.DirectionSet[1,0]	
				self.msgWF2.destination = self.DirectionSet[2,0]		
			self.FiFoOut.insert(0,self.msgWF0)
			self.FiFoOut.insert(1,self.msgWF1)
			self.FiFoOut.insert(2,self.msgWF2)
		elif (self.msgProcessFrom.typ != "ACK"): 
			for self.i in self.DirectionSet :
				if (self.msgProcessFrom.destination == self.DirectionSet[self.i,0]):
					self.msgProcessFrom = self.FiFoIn.pop(0)
					self.poke(self.i[1], self.msgProcessFrom)
					break	