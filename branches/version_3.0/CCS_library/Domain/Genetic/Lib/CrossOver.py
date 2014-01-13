from Individual import Individual

class CrossOverHalfAndHalf:

    def __init__(self, individual1, individual2):
        self.individualADN1 = individual1.ADN
        self.individualADN2 = individual2.ADN
        self.factory = individual1.geneFactory

    def createChild(self):
        ADN = self.individualADN1[:len(self.individualADN1)/2] + self.individualADN2[len(self.individualADN2)/2:]
        return Individual(ADN, self.factory)

class CrossOverOneOfTwo:

    def __init__(self, individual1, individual2):
        self.individualADN1 = individual1.ADN
        self.individualADN2 = individual2.ADN
        self.factory = individual1.geneFactory

    def createChild(self):
         ADN = []
         for i in range(len(self.individualADN1)):
             if i % 2 == 0:
                ADN.append(self.individualADN1[i])
             else:
                 ADN.append(self.individualADN2[i])
         return Individual(ADN, self.factory)