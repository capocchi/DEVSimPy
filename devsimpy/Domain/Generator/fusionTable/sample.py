#Author : Bastien POGGI
#Mail : bpoggi@univ-corse.fr
#Corporation : University Of Corsica Laboratory SPE
#Description : The library for get data from Google Fusion Table
#Date : 2010-09-30

from .fusionTable import Request

myRequester = Request("265331","Semaine","1995")

print("\n \n Show data from table 265331 in 1995..... \n \n")
print(myRequester.getListData())

print("\n \n Show time from table 265331 in 1995..... \n \n")
print(myRequester.getListTime())

 #print "\n \n Show difference between the data..... \n \n"
#print myRequester.getDifference()

#myRequester = Request(self.sourceName,"Semaine","1995") #ID TABLE | ANNEE
