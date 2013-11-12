def creerListTemps(num,temps):
    return map(lambda v: (v*num)+temps, range(1,int(1/num)+1))

def creerListValeur(num,valeur):
    myRange = int(1/num)
    result = []
    for i in range(1,myRange+1):
        result.append(num*valeur)
    return result

#Exemple

fichier = [(0,100),(1,200),(5,500)]
T = []
V = []
for ligne in fichier:
    T += creerListTemps(0.25,ligne[0])
    V += creerListValeur(0.25,ligne[1])

print T
print V
