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

import os
import cgi
import xml.dom.minidom
from makeunicode import u

class Kmlable(object):
    """Enables a subclass to be converted into KML."""

    _images = []
    _kmz = False
    _parse = True
    _namespaces = ['xmlns="http://www.opengis.net/kml/2.2"', 'xmlns:gx="http://www.google.com/kml/ext/2.2"']

    def __init__(self):
        self._kml = {}

    def __str__(self):
        """This is where the magic happens."""
        buf = []
        for var, val in self._kml.items():
            if val is not None:  # Exclude all variables that are None
                if var.endswith("_"):
                    buf.append("{0}".format(val))  # Use the variable's __str__ as is
                else:
                    if var in ['name', 'description', 'text'] and Kmlable._parse: # Parse value for HTML and convert
                        val = Kmlable._chrconvert(val)
                    elif (var == 'href' and os.path.exists(val) and Kmlable._kmz == True)\
                            or (var == 'targetHref' and os.path.exists(val) and Kmlable._kmz == True): # Check for local images
                        Kmlable._addimage(val)
                        val = os.path.join('files', os.path.split(val)[1])
                    buf.append(u("<{0}>{1}</{0}>").format(var, val))  # Enclose the variable's __str__ with the variables name
                    # Add namespaces
                    if var.startswith("atom:") and 'xmlns:atom="http://www.w3.org/2005/Atom"' not in Kmlable._namespaces:
                        Kmlable._namespaces.append('xmlns:atom="http://www.w3.org/2005/Atom"')
                    elif var.startswith("xal:") and 'xmlns:xal="urn:oasis:names:tc:ciq:xsdschema:xAL:2.0"' not in Kmlable._namespaces:
                        Kmlable._namespaces.append('xmlns:xal="urn:oasis:names:tc:ciq:xsdschema:xAL:2.0"')
        return "".join(buf)

    @classmethod
    def _parsetext(cls, parse=True):
        """Sets whether text elements are escaped."""
        Kmlable._parse = parse

    @classmethod
    def _chrconvert(cls, text):
        return cgi.escape(text)

    @classmethod
    def _addimage(cls, image):
        Kmlable._images.append(image)

    @classmethod
    def _getimages(cls):
        return set(Kmlable._images)

    @classmethod
    def _clearimages(cls):
        Kmlable._images = []

    @classmethod
    def _setkmz(cls, kmz=True):
        Kmlable._kmz = kmz

    @classmethod
    def _getnamespaces(cls):
        """Return the namespaces as a string."""
        return " ".join(Kmlable._namespaces)


class Vector2(object):
    """Abstract class representing a vector.

    Args:
      * x: int in xunits (default None)
      * y: int in yunits (default None)
      * xunits: string of type of x units. See :class:`simplekml.Units` (default None)
      * yunits: string of type of y units. See :class:`simplekml.Units` (default None)
      
    .. note::
      Not to be used directly.
    """

    def __init__(self,
                 x=None,
                 y=None,
                 xunits=None,
                 yunits=None):
        self._kml = {}
        self.x = x
        self.y = y
        self.xunits = xunits
        self.yunits = yunits


    @property
    def x(self):
        """Number in xunits, accepts int."""
        return self._kml['x']

    @x.setter
    def x(self, x):
        self._kml['x'] = x

    @property
    def y(self):
        """Number in yunits, accepts int."""
        return self._kml['y']

    @y.setter
    def y(self, y):
        self._kml['y'] = y

    @property
    def xunits(self):
        """Type of x units, see [Units] for values."""
        return self._kml['xunits']

    @xunits.setter
    def xunits(self, xunits):
        self._kml['xunits'] = xunits

    @property
    def yunits(self):
        """Type of y units, See :class:`simplekml.Units` for values."""
        return self._kml['yunits']

    @yunits.setter
    def yunits(self, yunits):
        self._kml['yunits'] = yunits



    def __str__(self):
        cname = self.__class__.__name__[0].lower() + self.__class__.__name__[1:]
        return '<{0} x="{1}" y="{2}" xunits="{3}" yunits="{4}" />'.format(cname, self._kml['x'], self._kml['y'], self._kml['xunits'], self._kml['yunits'])


class OverlayXY(Vector2):
    """Point in overlay image that is mapped to screen coordinate :class:`simplekml.ScreenXY`

    Arguments are the same as the properties.
    """

    def __init__(self, **kwargs):
        super(OverlayXY, self).__init__(**kwargs)


class ScreenXY(Vector2):
    """
    Point relative to the screen origin that the overlay image is mapped to.

    Arguments are the same as the properties.
    """

    def __init__(self, **kwargs):
        super(ScreenXY, self).__init__(**kwargs)


class RotationXY(Vector2):
    """
    Point relative to the screen about which the screen overlay is rotated.

    Arguments are the same as the properties.
    """

    def __init__(self, **kwargs):
        super(RotationXY, self).__init__(**kwargs)


class Size(Vector2):
    """
    Specifies the size of the image for the screen overlay.

    Arguments are the same as the properties.
    """
    def __init__(self, **kwargs):
        super(Size, self).__init__(**kwargs)

        
class HotSpot(Vector2):
    """
    Specifies the position inside the [Icon] that is anchored to the [Point].

    Arguments are the same as the properties.
    """

    def __init__(self, **kwargs):
        super(HotSpot, self).__init__(**kwargs)


class Snippet(object):
    """A short description of the feature.

    Arguments are the same as the properties.
    """

    def __init__(self, content='', maxlines=None):
        self._kml = {}
        self.content = content
        self.maxlines = maxlines

    @property
    def content(self):
        """The description to be used in the snippet, accepts string."""
        return self._kml['content']

    @content.setter
    def content(self, content):
        self._kml['content'] = content

    @property
    def maxlines(self):
        """Number of lines to display, accepts int."""
        return self._kml['maxlines']

    @maxlines.setter
    def maxlines(self, maxlines):
        self._kml['maxlines'] = maxlines
        
    def __str__(self):
        if self._kml['maxlines'] is not None:
            return '<Snippet maxLines="{0}">{1}</Snippet>'.format(self._kml['maxlines'],
                                                                  self._kml['content'])
        else:
            return '<Snippet>{0}</Snippet>'.format(self._kml['content'])



class KmlElement(xml.dom.minidom.Element):
    """Overrides the original Element to format the KML to GMaps standards."""

    _original_element = xml.dom.minidom.Element

    @classmethod
    def patch(cls):
        """Patch xml.dom.minidom.Element to use KmlElement instead."""
        cls._original_element = xml.dom.minidom.Element
        xml.dom.minidom.Element = KmlElement

    @classmethod
    def unpatch(cls):
        """Unpatch xml.dom.minidom.Element to use the Element class used last."""
        xml.dom.minidom.Element = cls._original_element

    def writexml(self, writer, indent="", addindent="", newl=""):
        """If the element only contains a single string value then don't add white space around it."""
        if self.childNodes and len(self.childNodes) == 1 and\
           self.childNodes[0].nodeType == xml.dom.minidom.Node.TEXT_NODE:
            writer.write(indent)
            KmlElement._original_element.writexml(self, writer)
            writer.write(newl)
        else:
            KmlElement._original_element.writexml(self, writer, indent, addindent, newl)
