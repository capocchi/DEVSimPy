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

import sys

import gettext
_ = gettext.gettext

from Mixins.Attributable import Attributable

import Container

#---------------------------------------------------------
class Abstractable:
    """  Mixin class for the abstraction hierarchy.
        Adds dynamically the 'layers' attribute. This one contains the list of diagrams associated with one level.
    """

    DUMP_ATTR = ['layers', 'current_level', 'DAM', 'UAM']

    ###
    def __init__(self, dia):
        """ Constructor.
        """
        ### current level
        self.current_level = 0

        self.diagram = dia

        ### dico of layers, dico of Downward and Upward functions according to layers
        if hasattr(dia, 'layers'):
            self.layers = getattr(dia, 'layers')
            self.DAM = getattr(dia, 'DAM')
            self.UAM = getattr(dia, 'UAM')
        else:
            self.layers = {0:dia}
            self.DAM = {}
            self.UAM = {}

#===============================================================================
# overwriting for Diagram class
#===============================================================================
    ###
    def SetDiagram(self, diagram):
        """ Set the diagram.
        """

        ### if diagram has layers attribute and layer exist, then load it
        if hasattr(diagram, 'layers') and diagram.current_level in diagram.layers:
            self.diagram = diagram.layers[self.GetCurrentLevel()]
            #self.layers = diagram.layers
            #self.current_level = diagram.current_level
            self.DAM  = diagram.DAM
            self.UAM = diagram.UAM
        else:
            self.diagram = diagram
            self.AddLayer(diagram, self.GetCurrentLevel())

    ###
    def GetDiagram(self):
        """ Return Diagram instance.
        """
        return self.diagram
#===============================================================================
#
#===============================================================================

    ###
    def GetDiagramByLevel(self, l):
        """ Return layer form level l.
            if layer dosen't exist, None is returned.
        """
        return self.layers.get(l, None)

    ###
    def SetDiagramByLevel(self, d, l):
        """ Update the layers form diagram d at level l.
        """
        self.layers.update({l:d})

    ###
    def GetLayers(self):
        """ Get layers dico.
        """
        return self.layers

    ###
    def GetCurrentLevel(self):
        """ Return the current layer viewed in the canvas.
        """
        return self.current_level

    def GetUAM(self):
        """ Return the dictionary of the code of Upward Atomic Model.
        """
        return self.UAM

    def GetDAM(self):
        """ Return the dictionary of the code of Downward Atomic Model.
        """
        return self.DAM

    def SetDAM(self, cl, val):
        """
        """
        self.DAM[cl] = val

    def SetUAM(self, cl, val):
        """
        """
        self.UAM[cl] = val

    def SetCurrentLevel(self, l):
        """ Set the current level viewed in the canvas.
        """
        self.current_level = l

    ###
    def NextLevel(self):
        """ return the last depth abstract level.
        """
        return self.GetLevelLenght()

    ###
    def GetLevelLenght(self):
        """ Get the number of layers defined in the canvas.
        """
        return len(self.GetLayers())

    ###
    def AddLayer(self, d, l):
        """ Add the diagram d at level l/
        """
        if l in self.layers:
            self.SetDiagramByLevel(d, l)
        else:
            ### add new diagram according the new layer
            self.layers[l] = d

            import WizardGUI
            
            ### add new DAM and UAM according to new layer
            self.SetUAM(l, WizardGUI.atomicCode('UAM%d'%l))
            self.SetDAM(l, WizardGUI.atomicCode('DAM%d'%l))

    ###
    def LoadDiagram(self, l):
        """ Load diagram at the level l in the current canvas.
        """
        layers = self.GetLayers()
        canvas = self

        print("current level is", l, layers)

        if l in layers:
            dia = canvas.GetDiagramByLevel(l)
            canvas.SetCurrentLevel(l)
            sys.stdout.write("load diagram %d"%l)

        else:

            dia = Container.Diagram()
            dia.SetParent(canvas)

            canvas.SetCurrentLevel(l)
            #canvas.SetDiagram(dia)

            sys.stdout.write("New diagram at level %s"%l)

        sys.stdout.write(str(self.layers))

        ### add new or update new attributes layers and current_layer to diagram
        setattr(dia, 'layers', canvas.GetLayers())
        setattr(dia, 'current_level', canvas.GetCurrentLevel())
        setattr(dia, 'DAM', canvas.GetDAM())
        setattr(dia, 'UAM', canvas.GetUAM())

        ### add new or update new attributes layers and current_layer to diagram at level 0
        d0 = canvas.GetDiagramByLevel(0)
        setattr(d0, 'layers', canvas.GetLayers())
        setattr(d0, 'current_level', canvas.GetCurrentLevel())
        setattr(d0, 'DAM', canvas.GetDAM())
        setattr(d0, 'UAM', canvas.GetUAM())

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
