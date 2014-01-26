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

from Mixins.Attributable import Attributable

import Container
import DetachedFrame
import Components

#---------------------------------------------------------
class Abstractable:
    """  Mixin class for the abstraction hierarchy
        Adds dynamically the 'layers' attribute . This one contains the list of diagrams associated with one level
    """

    ###
    def __init__(self, dia):
        """ Constructor.
        """
        ### current level
        self.current_level = 0

        self.diagram = dia

        ### dico of layers
        if hasattr(dia, 'layers'):
            self.layers = getattr(dia, "layers")
        else:
            self.layers = {0:dia}

#===============================================================================
# overwriting for Diagram class
#===============================================================================
    ###
    def SetDiagram(self, diagram):
        """ Set the diagram
        """

        ### if diagram has layers attribute and layer exist, then load it
        if hasattr(diagram, 'layers') and diagram.current_level in diagram.layers:
            self.diagram = diagram.layers[diagram.current_level]
            self.layers = diagram.layers
            self.current_level = diagram.current_level
        else:
            self.diagram = diagram
            self.AddLayer(diagram, self.GetCurrentLevel())

    ###
    def GetDiagram(self):
        """ Return Diagram instance
        """
        return self.diagram
#===============================================================================
#
#===============================================================================

    ###
    def GetDiagramByLevel(self, l):
        """ Return layer form level l
            if layer dosen't exist, None is returned
        """
        return self.layers.get(l, None)

    ###
    def SetDiagramByLevel(self, d, l):
        """ Update the layers form diagram d at level l
        """
        self.layers.update({l:d})

    ###
    def GetLayers(self):
        """ Get layers dico
        """
        return self.layers

    ###
    def GetCurrentLevel(self):
        """ Return the current layer viewed in the canvas
        """
        return self.current_level

    def SetCurrentLevel(self, l):
        """ Set the current level viewed in the canvas
        """
        self.current_level = l

    ###
    def NextLevel(self):
        """ return the last depth abstract level
        """
        return self.GetLevelLenght()

    ###
    def GetLevelLenght(self):
        """ Get the number of layers defined in the canvas
        """
        return len(self.GetLayers())

    ###
    def AddLayer(self, d, l):
        """ Add the diagram d at level l
        """
        if l in self.layers:
            self.SetDiagramByLevel(d, l)
        else:
            self.layers[l] = d

    ###
    def LoadDiagram(self, l):
        """ Load diagram at the level l in the current canvas
        """

        layers = self.GetLayers()
        canvas = self

        print "current level is", l, layers

        if l in layers:
            dia = canvas.GetDiagramByLevel(l)
            if l != canvas.GetCurrentLevel():
                canvas.SetCurrentLevel(l)

                print "load diagram %d"%l
                print self.layers

        else:

            dia = Container.Diagram()
            dia.SetParent(canvas)

            canvas.SetCurrentLevel(l)
            #canvas.SetDiagram(dia)

            print "New diagram at level %s"%l, self.layers

        ### add new or update new attributes layers and current_layer to diagram
        setattr(dia, 'layers', canvas.GetLayers())
        setattr(dia, 'current_level', canvas.GetCurrentLevel())

        ### add new or update new attributes layers and current_layer to diagram at level 0
        d0 = canvas.GetDiagramByLevel(0)
        setattr(d0, 'layers', canvas.GetLayers())
        setattr(d0, 'current_level', canvas.GetCurrentLevel())

        #=======================================================================
        # ### Add Attributes for dump only for ContainerBlock
        #=======================================================================
        # frame = canvas.GetTopLevelParent()
        # is_detached_frame = isinstance(frame, DetachedFrame.DetachedFrame)
        # parent_frame_is_canvas = isinstance(frame.GetParent(), Container.ShapeCanvas)
        # if is_detached_frame and not parent_frame_is_canvas:
        #     d0 = canvas.GetDiagramByLevel(0)
        #     ### only once
        #     if not (d0.HasAttr('layers') and d0.HasAttr('current_level')):
        #         d0.AddAttributes(['layers', 'current_level'])
        #         self.SetDiagramByLevel(0, d0)
        #=======================================================================

        ### update canvas
        canvas.SetDiagram(dia)
        canvas.deselect()
        canvas.Refresh()


