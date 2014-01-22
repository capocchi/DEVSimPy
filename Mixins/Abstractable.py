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

import Container

#---------------------------------------------------------
class Abstractable:
    """  Mixin class for the abstraction hierarchy
    """

    ###
    def __init__(self, dia):
        """ Constructor.
        """
        ### current level
        self.current_level = 0

        self.diagram = dia

        ### dico of diagram
        if hasattr(dia,'diagrams'):
            self.diagrams = dia.diagrams
        else:
            self.diagrams = {0:dia}

    def SetDiagram(self, diagram):
        """ Set the diagram
        """
        self.diagram = diagram
        self.AddDiagram(diagram, self.GetCurrentLevel())

    def GetDiagram(self):
        """ Return Diagram instance
        """
        return self.diagram

    def GetDiagramByLevel(self, level):
        """
        """
        if level in self.diagrams:
            return self.diagrams[level]
        else:
            return None

    def SetDiagramByLevel(self, dia, level):
        """
        """
        self.diagrams.update({level:dia})

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
        return self.GetLevelLenght()

    def GetLevelLenght(self):
        """
        """
        return len(self.GetDiagrams())

    def AddDiagram(self, dia, l):
        """ Add the diagram at level l
        """
        if l in self.diagrams:
            self.diagrams.update({l:dia})
        else:
            self.diagrams[l] = dia

    def LoadDiagram(self, level):
        """
        """

        diagrams = self.GetDiagrams()
        canvas = self

        print "current level is", level, diagrams

        if level in diagrams:
            dia = self.GetDiagramByLevel(level)
            if level != self.current_level:
                self.SetCurrentLevel(level)

                print "load diagram %d"%level

                print self.diagrams

        else:
            dia = Container.Diagram()
            dia.SetParent(canvas)

            canvas.SetCurrentLevel(level)
            canvas.SetDiagram(dia)

            print "New diagram at level %s"%level, self.diagrams

        canvas.diagram = dia
        canvas.diagram.diagrams = self.diagrams
        canvas.deselect()
        canvas.Refresh()
