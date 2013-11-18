from Domain.Genetic.Lib.SimpleAtomicModel import SimpleAtomicModel

class AM_Bin_To_DeployedObject(SimpleAtomicModel):

    def __init__(self, seizeGene=14, maxGeneValue=100, objectRange=10, mode="LOG"):
        SimpleAtomicModel.__init__(self)
        self.seizeGene = seizeGene
        self.maxGeneValue = maxGeneValue
        self.objectRange = objectRange
        self.inputData = []
        self.outputData = []
        self.mode = mode
        
#--------------------Fonction entree------------------
    def extTransition(self):
        self.showScreen("DEMANDE DE TRADUCTION RECUE")
        self.updateInputMessagesDic()        
        self.updateInputData()
        self.updateOutputData()
        self.showScreen("TRADUCTION TERMINEE")
        self.becomeActivate()
                
#--------------------Fonction sortie------------------     
    def outputFnc(self):
        self.showScreen("ENVOI DE LA TRADUCTION")
        self.sendMessage(0,self.outputData)
#         print "TRANSLATOR TO TUPLE 3 : ENTREES 1 ELEMENT", self.inputData[0]
#         print "TRANSLATOR TO TUPLE 3 : SORTIES 1 ELEMENT", self.outputData[0]

#--------------------Fonction interne------------------
    def intTransition(self):
        self.becomeDesactivate()
        self.inputData = []
        self.outputData = []
    
    def updateInputData(self):
        self.inputData = self.inputDic['0'].individuals
    
    def updateOutputData(self):
        #SEGMENTATION
        listADNconverted = []
        for individual in self.inputData:
            ADNBin = individual.ADN
            
            if len(ADNBin) % self.seizeGene > 0:
                print "ERREUR LA TAILLE DU CODE GENETIQUE NEST PAS UN MULTIPLE DE", self.seizeGene
                
            else:#A AMELIORER
                aGene = ""
                ADNListChainesBinaires = []
                for bit in ADNBin:
                    if len(aGene) < self.seizeGene:#REPLISSAGE LISTE BINAIRE
                        aGene += str(bit)
                    else : #AJOUT A LA LISTE DE LISTES BINAIRES ET DEBUT DUNE NOUVELLE LISTE
                        ADNListChainesBinaires.append(aGene)
                        del aGene
                        aGene = str(bit)
                ADNListChainesBinaires.append(aGene)     
                      
            listADNconverted.append(ADNListChainesBinaires)
        
        #TRADUCTION DES SEGMENTS
        for ADNListChainesBinaires in listADNconverted:
            self.outputData.append(map(self.translate,ADNListChainesBinaires))
        
    def translate(self,binGene):
        tuple1 = binGene[:len(binGene)/2]
        tuple2 = binGene[(len(binGene)/2):]
        
        v1 = int(tuple1,2)
        if v1> self.maxGeneValue:
            v1 = self.maxGeneValue
        
        v2 = int(tuple2,2)
        if v2> self.maxGeneValue:
            v2 = self.maxGeneValue
            
        return (v1,v2,self.objectRange)
        
    #--------------------Fonction ToString------------
    def __str__(self):
        return "AM_Bin_To_DeployedObject"
