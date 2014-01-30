##Gestion du temps (conversions)
#
#        def exploseTime(T,outPutTime):
#            maliste = []
#            for t in T:
#                maliste += creerListTemps(outPutTime,t)
#            print maliste
#
#        def exploseValue(V,outPutTime):
#            maliste = []
#            for v in V:
#                maliste += creerListValeur(outPutTime,v)
#                print maliste
#
#        def creerListTemps(num,temps):
#            return map(lambda t: (t*num)+temps, range(1,int(1/num)+1))
#
#        def creerListValeur(num,valeur):
#            return map(lambda v: num*valeur,range(1,int(1/num)+1))