import math
import libSatisfaction


#IMPLEMENTATIONS

def satisfactionPyramide(valeur, optimum, ecart):
    return -math.fabs(valeur-optimum)  / ecart + 1

def satisfactionGauss(valeur, optimum, ecart):
    partie1 = 1.0 / (ecart * math.sqrt(2*math.pi))
    partie2 = math.exp(- (((valeur-optimum)**2)/(2*(ecart**2))) )
    return partie1 * partie2

def satisfactionGaussNormalisee(valeur, optimum, ecart):
    meilleure = satisfactionGauss(optimum, optimum, ecart)          #RECUPERATION DE LA MEILLEURE VALEUR
    multiplicateur = 1.0 / meilleure                                #CALCUL DU MULTIPLICATEUR (REMONTER MEILLEURE VAL A 1)
    return multiplicateur * satisfactionGauss(valeur, optimum, ecart)

def satisfactionCourbePerso(valeur, listePoints):                                   #LISTE DOIT ETRE ORDONNEE
    if valeur < listePoints[0][0] or valeur > listePoints[len(listePoints)-1][0]:   #SI LA VALEUR EST EN DEHORS DE LA COURBE
        return 0
    else:                                                                           #SI LA VALEUR EST DANS LA COURBE
        i = 0
        while valeur > listePoints[i+1][0]:                                         #POSITIONNEMENT DANS LA COURBE
            i += 1
        coefficientDirecteur = (listePoints[i+1][1] - listePoints[i][1]) / (listePoints[i+1][0] - listePoints[i][0])
        nombrePas = valeur - listePoints[i][0]                                      #CALCUL DU MULTIPLICATEUR DU COEF DIR
        return listePoints[i][1] + coefficientDirecteur * nombrePas                 #AJOUT A LA POSITION DE DEPART DU CALCUL
