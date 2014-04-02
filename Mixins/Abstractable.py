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
from DomainInterface.DomainBehavior import DomainBehavior

import Container
import DetachedFrame
import Components
import WizardGUI

#---------------------------------------------------------
class Abstractable:
    """  Mixin class for the abstraction hierarchy
        Adds dynamically the 'layers' attribute. This one contains the list of diagrams associated with one level
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

    def GetUAM(self):
        """ Return the dictionary of the code of Upward Atomic Model
        """
        return self.UAM

    def GetDAM(self):
        """ Return the dictionary of the code of Downward Atomic Model
        """
        return self.DAM

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
            ### add new diagram according the new layer
            self.layers[l] = d
            ### add new DAM and UAM according to new layer
            self.UAM[l] = WizardGUI.atomicCode('UAM%d'%l)
            self.DAM[l] = WizardGUI.atomicCode('DAM%d'%l)

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
        setattr(dia, 'DAM', canvas.GetDAM())
        setattr(dia, 'UAM', canvas.GetUAM())

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

#===============================================================================
# Downward Atomic Model
#===============================================================================
class Downward(DomainBehavior):
    """
        the number of input ports is the number of coupled level 0 input ports.
        the number of output ports is the number of coupled level i output ports.
    """

    def __init__(self, rule_fct=None):
        """ Constructor
        """
        DomainBehavior.__init__(self)

        ### dico of rules
        self.rule = rule_fct
        ### list of messages
        self.msg_dict = {}

        self.state = {'status':'Passif', 'sigma':float('inf')}

    def extTransition(self):
        """
        """

        ### acquisition of messages
        for port in self.IPorts:
            msg = self.peek(port)
            if msg:
                self.msg_dict[port.id] = msg

        ### change state to active
        self.state['status'] = 'actif'

        ### update time advance
        self.state['sigma'] = 0

    def intTransition(self):
        """
        """
        self.state['sigma'] = float('inf')
        self.state['status'] = 'Passif'
        self.msg_dict = {}

    def outputFnc(self):
        """
        """
        for i in self.msg_list:
            msg = self.msg_list[i]
            self.poke(self.OPort[i], self.rule(i, msg))

    def timeAdvance(self):
        """
        """
        return self.state['sigma']

#===============================================================================
# Upward Atomic Model
#===============================================================================
class Upward(DomainBehavior):
    """
    """

    def __init__(self):
        """ Constructor.

            the number of input ports is the number of coupled level i inputs ports.
            the number of output ports is the number of coupled level 0 output ports.

        """
        DomainBehavior.__init__(self)

        ### dico of rules
        self.rule = rule_fct
        ### list of messages
        self.msg_dict = {}

        self.state = {'status':"Passif", 'sigma':float('inf')}

    def extTransition(self):
        """
        """

        ### acquisition of messages
        for port in self.IPorts:
            msg = self.peek(port)
            if msg:
                self.msg_dict[port.id] = msg

        ### change state to active
        self.state['status'] = 'actif'

        ### update time advance
        self.state['sigma'] = 0

    def intTransition(self):
        """
        """
        self.state['sigma'] = float('inf')
        self.state['status'] = "Passif"
        self.msg_dict = {}

    def outputFnc(self):
        """
        """
        for i in self.msg_list:
            msg = self.msg_list[i]
            self.poke(self.OPort[i], self.rule(i, msg))

    def timeAdvance(self):
        """
        """
        return self.state['sigma']