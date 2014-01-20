# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# Abstractable.py ---
#                     --------------------------------
#                        Copyright (c) 2014
#                       Laurent CAPOCCHI
#                      University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 20/01/14
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GLOBAL VARIABLES AND FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

#---------------------------------------------------------
class Abstractable:
    """  Mixin class for the abstraction hierarchy
    """

    ###
    def __init__(self):
        """ Constructor.
        """
        ### current level
        self.current_level = 0

        ### dico of diagram
        self.diagrams = {}

    def GetDiagrams(self):
        """ Get Diagrams dico
        """
        return self.diagrams

    def GetDiagram(self, l):
        """ Get diagram at level l
        """
        dia = self.GetDiagrams()
        return dia[l] if l in dia else None

    def GetCurrentLevel(self):
        """
        """
        return self.current_level

    def SetCurrentLevel(self, l):
        """
        """
        self.current_level = l

    def NextLevel(self):
        """ return the last depth abstract level
        """
        return self.GetLevelLenght()+1

    def GetLevelLenght(self):
        """
        """
        return len(self.GetDiagrams())

    def AddDiagram(self, dia):
        """ Add diagram to next abstract level
        """
        if not self.diagrams:
            self.diagrams[self.GetCurrentLevel()] = dia
        else:
            self.diagrams[self.NextLevel()] = dia

    def ReplaceDiagram(self, dia, level):
        """ Replace the diagram
        """
        if level in self.diagram:
            self.diagrams.update({level:dia})
        else:
            self.diagrams[level] = dia
