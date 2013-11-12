#------------------------------------------------------------------------------
#           Name: dictionary2.py
#         Author: Kevin Harris
#  Last Modified: 02/20/04
#    Description: This Python script demonstrates how to create and access a
#                 dictionary.
#------------------------------------------------------------------------------

usedCars = { ('Jeep', 'Liberty'):(2002, 32000, 25000),
             ('Toyota', 'Rav 4'):(2002, 15000, 22000),
             ('Volvo', 'XC 90'):(2003, 5500, 37000) }

for eachCar in usedCars:
    print 'Make: %s\tModel: %s' % eachCar
    print 'Year: %s\tMileage: %s\tPrice:%s\n' % usedCars[eachCar]

raw_input( '\n\nPress Enter to exit...' )
