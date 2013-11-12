import random

#Factories

class GeneLocationFactory:
    #Renvoi des points aleatoires a linterieur dun polygon (fonctionne uniquement avec carre actuellement)

    def __init__(self, polygon):
        self.maxLat = polygon[1][0] #premier point, premier valeur du tuple
        self.maxLon = polygon[1][1] #premier point, deuxieme valeur du tuple
        self.minLat = polygon[1][0]
        self.minLon = polygon[1][1]

        for point in polygon:
            if point[0] > self.maxLat:
                self.maxLat = point[0]
            if point[0] < self.minLat:
                self.minLat = point[0]

            if point[1] > self.maxLon:
                self.maxLon = point[1]
            if point[1] < self.minLon:
                self.minLon = point[1]

    def makeGene(self):
        #print "*** createGene***"
        randomLat = random.randint(self.minLat, self.maxLat)
        randomLon = random.randint(self.minLon, self.maxLon)
        return LocationGene(randomLat, randomLon)
        
class GeneCharFactory:
    
    def __init__(self, univers="1234"):
        self.univers = univers
        
    def makeGene(self):
        i = random.randint(0,len(self.univers)-1)
        return CharGene(self.univers[i])
    
class GeneBinFactory:
    
    def __init__(self):
        pass
    
    def makeGene(self):
        return random.randint(0,1)

#Genes

class LocationGene:
    
    def __init__(self, latitude, longitude, elevation=0):
        self.lat = latitude
        self.lon = longitude
        self.elv = elevation
        
    def getLat(self):
        return self.lat

    def getLon(self):
        return self.lon
    
    def getElev(self):
        return self.elv
        
        
    def __str__(self):
        return "<%d,%d,%d>" % (self.lat, self.lon, self.elv)
        
class CharGene:
    
    def __init__(self, char):
        self.char = char
    
    def __str__(self):
        return str(self.char)

