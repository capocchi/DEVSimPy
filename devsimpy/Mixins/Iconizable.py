# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# Iconizable.py ---
#                     --------------------------------
#                        Copyright (c) 2023
#                       Laurent CAPOCCHI
#                      University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 15/12/23
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GLOBAL VARIABLES AND FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##-


import os

import gettext
_ = gettext.gettext

class Icon:
    def __init__(self, name:str, offset_pos:tuple):
        """Constructor.

        Args:
            name (str): name of the picture of icon (png)
            offset_pos (tuple): position offset to add to the current position (x,y) refreshed in the DC.
        """

        ## local copy
        self._name = name
        self._offset_x, self._offset_y = offset_pos
        
        ### icon png path
        self._image_path = os.path.join(ICON_PATH, self.getFileName())
        
        assert(os.path.exists(self._image_path))

    def getImagePath(self):
        return self._image_path
    
    def getName(self):
        return self._name
    
    def getFileName(self):
        return f"{self._name}.png"

    
    def getOffSet(self, pos:str):
        assert(pos in ('x','y'))
        return self._offset_x if pos == 'x' else self._offset_y
    
#-------------------------------------------------------------------------------
class Iconizable():
    """ Iconizable mixin to create binding icin on Block.
    """
    # Assuming your bitmap is 16x16 pixels
    bitmap_width, bitmap_height = 16, 16

    ###
    def __init__(self, icon_names:list):
        """Constructor.

        Args:
            icon_names (list): list of picture name and its offset positions.
        """
        self.icons = {name:(-20*(i+1), +2) for i,name in enumerate(icon_names)}
        self.hide_icons = False
        
    def onTimerTick(self):
        """Cacher les icônes après le délai du minuteur."""
        self.hide_icons = True
        
        # Vous pouvez forcer un rafraîchissement graphique si nécessaire (ex: self.Refresh())

    def getIcon(self, icon_name:str)->Icon:
        """Get icons from names list.

        Args:
            icon_name (str): name of the picture representing the icon.
        """
        return Icon(icon_name, self.icons.get(icon_name, None))
    
    def getDisplayedIconNames(self)->list:
        """Get the names of the icones to display.

        Yields:
            str: returned name
        """
        return self.icons.keys()

    def getClickedIconName(self, container_x:int, container_y:int, mouse_x:int, mouse_y:int)->str:
        """Get the name of the clicked icon.

        Args:
            mouse_x (int): x position of the mousse
            mouse_y (int): y postion of the mousse

        Returns:
            str: name of the clicked icon
        """
        # for name, icon in self.icons.items():
            # x, y = int(container_x[1]+icon.getOffSet('x')), int(container_y[0]+icon.getOffSet('y'))
        for name, offset in self.icons.items():
            x, y = int(container_x[1]+offset[0]), int(container_y[0]+offset[1])
            if (
                x <= mouse_x <= x + Iconizable.bitmap_width and
                y <= mouse_y <= y + Iconizable.bitmap_height):
                return name
        
        return ""
