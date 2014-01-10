"""
Copyright 2011-2012 Kyle Lancaster

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

Contact me at kyle.lan@gmail.com
"""

from base import Kmlable
from substyle import IconStyle, LabelStyle, LineStyle, PolyStyle, BalloonStyle, ListStyle


class StyleSelector(Kmlable):
    """Abstract style class, extended by :class:`simplekml.Style` and :class:`simplekml.StyleMap`

    There are no arguments.
    """
    _id = 0
    def __init__(self):
        super(StyleSelector, self).__init__()
        self._id = "stylesel_{0}".format(StyleSelector._id)
        StyleSelector._id += 1

    @property
    def id(self):
        """The id of the style, read-only."""
        return self._id


class Style(StyleSelector):
    """Styles affect how Geometry is presented.

    Arguments are the same as the properties.
    """
    def __init__(self,
                 iconstyle=None,
                 labelstyle=None,
                 linestyle=None,
                 polystyle=None,
                 balloonstyle=None,
                 liststyle=None):
        super(Style, self).__init__()
        self._kml["IconStyle_"] = iconstyle
        self._kml["LabelStyle_"] = labelstyle
        self._kml["LineStyle_"] = linestyle
        self._kml["PolyStyle_"] = polystyle
        self._kml["BalloonStyle"] = balloonstyle
        self._kml["ListStyle"] = liststyle

    def __str__(self):
        return '<Style id="{0}">{1}</Style>'.format(self._id, super(Style, self).__str__())
      
    @property
    def iconstyle(self):
        """The iconstyle, accepts :class:`simplekml.IconStyle`."""
        if self._kml["IconStyle_"] is None:
            self._kml["IconStyle_"] = IconStyle()
        return self._kml["IconStyle_"]
        
    @iconstyle.setter
    def iconstyle(self, iconstyle):
        self._kml["IconStyle_"] = iconstyle
        
    @property
    def labelstyle(self):
        """The labelstyle, accepts :class:`simplekml.LabelStyle`."""
        if self._kml["LabelStyle_"] is None:
            self._kml["LabelStyle_"] = LabelStyle()
        return self._kml["LabelStyle_"]

    @labelstyle.setter
    def labelstyle(self, labelstyle):
        self._kml["LabelStyle_"] = labelstyle
        
    @property
    def linestyle(self):
        """The linestyle, accepts :class:`simplekml.LineStyle`."""
        if self._kml["LineStyle_"] is None:
            self._kml["LineStyle_"] = LineStyle()
        return self._kml["LineStyle_"]
        
    @linestyle.setter
    def linestyle(self, linestyle):
        self._kml["LineStyle_"] = linestyle

    @property
    def polystyle(self):
        """The polystyle, accepts :class:`simplekml.PolyStyle`."""
        if self._kml["PolyStyle_"] is None:
            self._kml["PolyStyle_"] = PolyStyle()
        return self._kml["PolyStyle_"]
        
    @polystyle.setter
    def polystyle(self, polystyle):
        self._kml["PolyStyle_"] = polystyle
        
    @property
    def balloonstyle(self):
        """The balloonstyle, accepts :class:`simplekml.BalloonStyle`."""
        if self._kml["BalloonStyle"] is None:
            self._kml["BalloonStyle"] = BalloonStyle()
        return self._kml["BalloonStyle"]

    @balloonstyle.setter
    def balloonstyle(self, balloonstyle):
        self._kml["BalloonStyle"] = balloonstyle

    @property
    def liststyle(self):
        """The liststyle, accepts :class:`simplekml.ListStyle`."""
        if self._kml["ListStyle"] is None:
            self._kml["ListStyle"] = ListStyle()
        return self._kml["ListStyle"]

    @liststyle.setter
    def liststyle(self, liststyle):
        self._kml["ListStyle"] = liststyle


class StyleMap(StyleSelector):
    """Styles affect how Geometry is presented.

    Arguments are the same as the properties.
    """
    def __init__(self,
                 normalstyle=None,
                 highlightstyle=None):
        super(StyleMap, self).__init__()
        self._pairnormal = None
        self._pairhighlight = None
        self.normalstyle = normalstyle
        self.highlightstyle = highlightstyle

    def __str__(self):
        buf = ['<StyleMap id="{0}">'.format(self._id),
               super(StyleMap, self).__str__()]
        if self._pairnormal is not None:
            buf.append("<Pair>")
            buf.append("<key>normal</key>")
            buf.append("<styleUrl>#{0}</styleUrl>".format(self._pairnormal._id))
            buf.append("</Pair>")
        if self._pairhighlight is not None:
            buf.append("<Pair>")
            buf.append("<key>highlight</key>")
            buf.append("<styleUrl>#{0}</styleUrl>".format(self._pairhighlight._id))
            buf.append("</Pair>")
        buf.append("</StyleMap>")
        return "".join(buf)

    @property
    def normalstyle(self):
        """The normal :class:`simplekml.Style`, accepts :class:`simplekml.Style`."""
        if self._pairnormal is None:
            self._pairnormal = Style()
        return self._pairnormal

    @normalstyle.setter
    def normalstyle(self, normal):
        self._pairnormal = normal

    @property
    def highlightstyle(self):
        """The highlighted :class:`simplekml.Style`, accepts :class:`simplekml.Style`."""
        if self._pairhighlight is None:
            self._pairhighlight = Style()
        return self._pairhighlight

    @highlightstyle.setter
    def highlightstyle(self, highlighturl):
        self._pairhighlight = highlighturl
