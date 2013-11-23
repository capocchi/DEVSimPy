from Domain.Genetic.Lib.SimpleAtomicModel import SimpleAtomicModel

class AM_Bin_To_Tuple(SimpleAtomicModel):

    def __init__(self, seizeGene=14):
        SimpleAtomicModel.__init__(self)
        self.seizeGene = seizeGene
        self.inputData = []
        self.outputData = []
        
#--------------------Fonction entree------------------
    def extTransition(self):
        print "TRANSLATOR TO TUPLE : MESSAGE RECUS"
        self.updateInputMessagesDic()        
        self.updateInputData()
        self.updateOutputData()
        self.state['sigma'] = 0
                
#--------------------Fonction sortie------------------     
    def outputFnc(self):
        self.sendMessage(0,self.outputData)
        print "TRANSLATOR TO TUPLE : ENTREES",self.inputData[0]
        print "TRANSLATOR TO TUPLE : SORTIES",self.outputData[0]


#--------------------Fonction interne------------------
    def intTransition(self):
        self.state['sigma'] = INFINITY
        self.inputData = []
        self.outputData = []
        
#--------------------Fonction ToString------------
    def __str__(self):
        return "AM_Bin_To_Tuple"
    
    def updateInputData(self):
        self.inputData = self.inputDic['0'].individuals
    
    def updateOutputData(self):
        #SEGMENTATION
        listGroupGene = []
        for individual in self.inputData:
            ADNBin = individual.ADN
            
            if len(ADNBin) % self.seizeGene > 0:
                print "ERREUR TAILLE INCORECTE"
                
            else:
                gene = ""
                ADNInt = []
                for bit in ADNBin:
                    if len(gene) < self.seizeGene:
                        gene += str(bit)
                    else :
                        ADNInt.append(gene)
                        gene = "" +str(bit)
                ADNInt.append(gene)
                        
            listGroupGene.append(ADNInt)
        
        #TRADUCTION DES SEGMENTS
        for ADNInt in listGroupGene:
            self.outputData.append(map(self.translate,ADNInt))
            
        #print self.outputData[0]
        
    def translate(self,binGene):
        tuple1 = binGene[:len(binGene)/2]
        tuple2 = binGene[(len(binGene)/2):]
        return (int(tuple1,2),int(tuple2,2))
