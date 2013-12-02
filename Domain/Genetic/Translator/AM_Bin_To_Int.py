from Domain.Genetic.Lib.SimpleAtomicModel import SimpleAtomicModel

class AM_Bin_To_Int(SimpleAtomicModel):

    def __init__(self, seizeGene=14):
        SimpleAtomicModel.__init__(self)
        self.seizeGene = seizeGene
        self.inputData = []
        self.outputData = []
        
#--------------------Fonction entree------------------
    def extTransition(self):
        print "TRANSLATOR TO INT : MESSAGE RECUS"
        self.updateInputMessagesDic()        
        self.updateInputData()
        self.updateOutputData()
                
#--------------------Fonction sortie------------------     
    def outputFnc(self):
        self.sendMessage(0,self.outputData)

#--------------------Fonction interne------------------
    def intTransition(self):
        self.state['sigma'] = INFINITY
        self.inputData = []
        self.outputData = []
        
#--------------------Fonction ToString------------
    def __str__(self):
        return "AM_Bin_To_Int"
    
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
                        gene = ""
            listGroupGene.append(ADNInt)
            
        #TRADUCTION DES SEGMENTS
        for ADNInt in listGroupGene:
            self.outputData.append(map(lambda x : int(x,2),ADNInt))
        print self.outputData
