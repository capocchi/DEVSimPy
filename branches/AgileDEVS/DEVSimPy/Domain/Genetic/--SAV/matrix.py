class GridArea:

    #PRIVATE METHODS
    ################
    def __init__(self, height, weight):
        self.height = height
        self.weight = weight
        self.sensorRepresentation = 'X'
        self.sensorRangeRepresentation = 'O'
        self.freeAreaRepresentation = '_'
        self.matrix = []
        for i in range(self.height):
            line = []
            for j in range(self.weight):
                line.append( self.freeAreaRepresentation )
            self.matrix.append(line)

    def __str__(self):
        result = ""
        for ligne in self.matrix:
            for element in ligne:
                result += str(element)
            result += "\n"
        return result

    #PUBLIC METHODS
    ###############
    def drawSensor(self, x, y):
        self.update(x, y, self.sensorRepresentation)
        #GAUCHE
        self.drawRange(x-1,y-1)
        self.drawRange(x-1,y)
        self.drawRange(x-1,y+1)
        #CENTRE
        self.drawRange(x, y-1)
        self.drawRange(x, y+1)
        #DROITE
        self.drawRange(x+1,y-1)
        self.drawRange(x+1,y)
        self.drawRange(x+1,y+1)


    def drawRange(self, x, y):
        self.update(x, y, self.sensorRangeRepresentation)


    def update(self, x, y, element):
        if x < self.height and y < self.weight:
            self.matrix[x][y] = element

    def evaluer(self):
        nbCell = self.height * self.weight
        nbCellCovered = 0
        for ligne in self.matrix:
            for element in ligne:
                if element == self.sensorRangeRepresentation or element == self.sensorRepresentation:
                    nbCellCovered += 1
        return float(nbCellCovered) / float(nbCell) * 100


m1 = GridArea(10, 10)
print m1
m1.drawSensor(5,5)
m1.drawSensor(5,9)
print m1
print m1.evaluer()


