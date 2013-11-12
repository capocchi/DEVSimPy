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

from abstractview import Camera, LookAt
from base import Kmlable, Snippet, OverlayXY, ScreenXY, RotationXY, Size
from coordinates import Coordinates
from icon import Icon, Link
from model import Location, Orientation, Scale, ResourceMap
from overlay import ViewVolume, ImagePyramid
from region import LatLonBox, GxLatLonQuad, Region
from schema import ExtendedData, Schema
from styleselector import Style, StyleMap
from timeprimitive import TimeSpan, TimeStamp
from tour import GxTour

class Feature(Kmlable):
    """Abstract class extended by all features.

    The arguments are the same as the properties.

    .. note::
      Not to be used directly.
    """

    _id = 0
    def __init__(self,
                 name=None,
                 visibility=None,
                 open=None,
                 atomauthor=None,
                 atomlink=None,
                 address=None,
                 xaladdressdetails=None,
                 phonenumber=None,
                 snippet=None,
                 description=None,
                 camera=None,
                 lookat=None,
                 timestamp=None,
                 timespan=None,
                 region=None,
                 extendeddata=None):
        Feature._id += 1
        super(Feature, self).__init__()
        self._kml['name'] = name
        self._kml['visibility'] = visibility
        self._kml['open'] = open
        self._kml['atom:author'] = atomauthor
        self._kml['atom:link'] = atomlink
        self._kml['address'] = address
        self._kml['xal:AddressDetails'] = xaladdressdetails
        self._kml['phoneNumber'] = phonenumber
        self._kml['description'] = description
        self._kml['Camera'] = camera
        self._kml['LookAt'] = lookat
        self._kml['snippet_'] = snippet
        self._kml['TimeStamp'] = timestamp
        self._kml['TimeSpan'] = timespan
        self._kml['Region'] = region
        self._kml['styleUrl'] = None
        self._kml['ExtendedData'] = extendeddata
        self._id = "feat_{0}".format(Feature._id)
        self._style = None
        self._stylemap = None
        self._features = []
        self._styles = []
        self._stylemaps = []
        self._folders = []

    @property
    def id(self):
        """The id string."""
        return self._id

    @property
    def name(self):
        """Name of placemark, accepts string."""
        return self._kml['name']

    @name.setter
    def name(self, name):
        self._kml['name'] = name

    @property
    def visibility(self):
        """Whether the feature is shown, accepts int 0 or 1."""
        return self._kml['visibility']

    @visibility.setter
    def visibility(self, visibility):
        self._kml['visibility'] = visibility

    @property
    def open(self):
        """Whether open or closed in Places panel, accepts int 0 or 1."""
        return self._kml['open']

    @open.setter
    def open(self, open):
        self._kml['open'] = open

    @property
    def atomauthor(self):
        """Author of the feature, accepts string."""
        return self._kml['atom:author']

    @atomauthor.setter
    def atomauthor(self, atomauthor):
        self._kml['atom:author'] = atomauthor

    @property
    def atomlink(self):
        """URL containing this KML, accepts string."""
        return self._kml['atom:link']

    @atomlink.setter
    def atomlink(self, atomlink):
        self._kml['atom:link'] = atomlink

    @property
    def address(self):
        """Standard address, accepts string."""
        return self._kml['address']

    @address.setter
    def address(self, address):
        self._kml['address'] = address

    @property
    def xaladdressdetails(self):
        """Address in xAL format, accepts string.

        .. note::
            There seems to be a bug in Google Earth where the inclusion of the namespace
            xmlns:xal="urn:oasis:names:tc:ciq:xsdschema:xAL:2.0" seems to break some other elements of the KML such
            as touring (a tour will not play). If xaladdressdetails is used the above namespace will be added to the
            KML and will possibly break other elements. Use with caution.
        """
        return self._kml['xal:AddressDetails']

    @xaladdressdetails.setter
    def xaladdressdetails(self, xaladdressdetails):
        self._kml['xal:AddressDetails'] = xaladdressdetails

    @property
    def phonenumber(self):
        """Phone number used by Google Maps mobile, accepts string."""
        return self._kml['phoneNumber']

    @phonenumber.setter
    def phonenumber(self, phonenumber):
        self._kml['phoneNumber'] = phonenumber

    @property
    def description(self):
        """Description shown in the information balloon, accepts string."""
        return self._kml['description']

    @description.setter
    def description(self, description):
        self._kml['description'] = description

    @property
    def camera(self):
        """Camera that views the scene, accepts :class:`simplekml.Camera`"""
        if self._kml['Camera'] is None:
            self._kml['Camera'] = Camera()
            self._kml['LookAt'] = None
        return self._kml['Camera']

    @camera.setter
    def camera(self, camera):
        self._kml['Camera'] = camera
        self._kml['LookAt'] = None

    @property
    def lookat(self):
        """Camera relative to the feature, accepts :class:`simplekml.LookAt`"""
        if self._kml['LookAt'] is None:
            self._kml['LookAt'] = LookAt()
            self._kml['Camera'] = None
        return self._kml['LookAt']

    @lookat.setter
    def lookat(self, lookat):
        self._kml['Camera'] = None
        self._kml['LookAt'] = lookat

    @property
    def snippet(self):
        """Short description of the feature, accepts :class:`simplekml.Snippet`"""
        if self._kml['snippet_'] is None:
            self._kml['snippet_'] = Snippet()
        return self._kml['snippet_']

    @snippet.setter
    def snippet(self, snippet):
        self._kml['snippet_'] = snippet

    @property
    def extendeddata(self):
        """Extra data for the feature."""
        if self._kml['ExtendedData'] is None:
            self._kml['ExtendedData'] = ExtendedData()
        return self._kml['ExtendedData']

    @extendeddata.setter
    def extendeddata(self, extendeddata):
        self._kml['ExtendedData'] = extendeddata

    @property
    def timestamp(self):
        """Single moment in time, accepts :class:`simplekml.TimeStamp`"""
        if self._kml['TimeStamp'] is None:
            self._kml['TimeStamp'] = TimeStamp()
        return self._kml['TimeStamp']

    @timestamp.setter
    def timestamp(self, timestamp):
        self._kml['TimeStamp'] = timestamp

    @property
    def timespan(self):
        """Period of time, accepts :class:`simplekml.TimeSpan`"""
        if self._kml['TimeSpan'] is None:
            self._kml['TimeSpan'] = TimeSpan()
        return self._kml['TimeSpan']

    @timespan.setter
    def timespan(self, timespan):
        self._kml['TimeSpan'] = timespan

    @property
    def region(self):
        """Bounding box of feature, accepts :class:`simplekml.Region`"""
        if self._kml['Region'] is None:
            self._kml['Region'] = Region()
        return self._kml['Region']

    @region.setter
    def region(self, region):
        self._kml['Region'] = region

    @property
    def id(self):
        """Id number of feature, read-only."""
        return self._id

    @property
    def style(self):
        """The current style of the feature, accepts :class:`simplekml.Style`"""
        if self._style is None:
            self._style = Style()
            self._setstyle(self._style)
            self._addstyle(self._style)
        return self._style

    @style.setter
    def style(self, style):
        self._setstyle(style)
        self._addstyle(style)
        self._style = style

    @property
    def stylemap(self):
        """The current StyleMap of the feature, accepts :class:`simplekml.StyleMap`"""
        if self._stylemap is None:
            self._stylemap = StyleMap()
            self._setstyle(self._stylemap)
            self._addstylemap(self._stylemap)
        return self._stylemap

    @stylemap.setter
    def stylemap(self, stylemap):
        self._setstyle(stylemap)
        self._addstylemap(stylemap)
        self._stylemap = stylemap

    @property
    def styleurl(self):
        """Reference to the current styleurl or the feature, accepts string."""
        return self._kml['styleUrl']

    @styleurl.setter
    def styleurl(self, styleurl):
        self._kml['styleUrl'] = styleurl

    @property
    def iconstyle(self):
        """IconStyle of the feature, accepts :class:`simplekml.IconStyle`"""
        return self.style.iconstyle

    @iconstyle.setter
    def iconstyle(self, iconstyle):
        self.style.iconstyle = iconstyle

    @property
    def labelstyle(self):
        """LabelStyle of the feature, accepts :class:`simplekml.LabelStyle`"""
        return self.style.labelstyle

    @labelstyle.setter
    def labelstyle(self, labelstyle):
        self.style.labelstyle = labelstyle

    @property
    def linestyle(self):
        """LineStyle of the feature, accepts :class:`simplekml.LineStyle`"""
        return self.style.linestyle

    @linestyle.setter
    def linestyle(self, linestyle):
        self.style.linestyle = linestyle

    @property
    def polystyle(self):
        """PolyStyle of the feature, accepts :class:`simplekml.PolyStyle`"""
        return self.style.polystyle

    @polystyle.setter
    def polystyle(self, polystyle):
        self.style.polystyle = polystyle

    @property
    def balloonstyle(self):
        """BalloonStyle of the feature, accepts :class:`simplekml.BalloonStyle`"""
        return self.style.balloonstyle

    @balloonstyle.setter
    def balloonstyle(self, balloonstyle):
        self.style.balloonstyle = balloonstyle

    @property
    def liststyle(self):
        """ListStyle of the feature, accepts :class:`simplekml.ListStyle`"""
        return self.style.liststyle

    @liststyle.setter
    def liststyle(self, liststyle):
        self.style.liststyle = liststyle

    def _addstyle(self, style):
        """Attaches the given style (style) to this feature."""
        if style not in self._styles:
            self._styles.append(style)

    def _addstylemap(self, style):
        """Attaches the given style (style) to this feature."""
        if style not in self._stylemaps:
            self._stylemaps.append(style)

    def _setstyle(self, style):
        self._kml['styleUrl'] = "#{0}".format(style.id)

    def __str__(self):
        buf = []
        for stylemap in self._stylemaps:
            self._addstyle(stylemap.normalstyle)
            self._addstyle(stylemap.highlightstyle)
        str = '<{0} id="{1}">'.format(self.__class__.__name__, self._id)
        buf.append(str)
        for style in self._styles:
            buf.append(style.__str__())
        for stylemap in self._stylemaps:
            buf.append(stylemap.__str__())
        buf.append(super(Feature, self).__str__())
        for folder in self._folders:
            buf.append(folder.__str__())
        for feat in self._features:
            buf.append(feat.__str__())
        buf.append("</{0}>".format(self.__class__.__name__))
        return "".join(buf)

    def _newfeature(self, cls, **kwargs):
        """Creates a new feature from the given class and attaches it to this
        feature.
        """
        feat = cls(**kwargs)
        feat._parent = self
        if isinstance(feat, Geometry):
            self._features.append(feat._placemark)
            feat._parent = self
            if feat._style is not None:
                self._addstyle(feat._style)
        else:
            self._features.append(feat)
        return feat

    def newpoint(self, **kwargs):
        """Creates a new :class:`simplekml.Point` and attaches it to this KML document.

        Arguments are the same as :class:`simplekml.Point`

        Returns:
          * an instance of :class:`simplekml.Point` class.
        """
        return self._newfeature(Point, **kwargs)

    def newlinestring(self, **kwargs):
        """Creates a new :class:`simplekml.LineString` and attaches it to this KML document.

        Arguments are the same as :class:`simplekml.LineString`

        Returns:
          * an instance of :class:`simplekml.LineString` class.
        """
        return self._newfeature(LineString, **kwargs)

    def newpolygon(self, **kwargs):
        """Creates a new :class:`simplekml.Polygon` and attaches it to this KML document.

        Arguments are the same as :class:`simplekml.Polygon`

        Returns:
          * an instance of :class:`simplekml.Polygon` class.
        """
        return self._newfeature(Polygon, **kwargs)

    def newmultigeometry(self, **kwargs):
        """Creates a new :class:`simplekml.MultiGeometry` and attaches it to this KML document.

        Arguments are the same as :class:`simplekml.MultiGeometry`

        Returns:
          * an instance of :class:`simplekml.MultiGeometry` class.
        """
        return self._newfeature(MultiGeometry, **kwargs)

    def newgroundoverlay(self, **kwargs):
        """Creates a new :class:`simplekml.GroundOverlay` and attaches it to this KML document.

        Arguments are the same as :class:`simplekml.GroundOverlay`

        Returns:
          * an instance of :class:`simplekml.GroundOverlay` class.
        """
        return self._newfeature(GroundOverlay, **kwargs)

    def newscreenoverlay(self, **kwargs):
        """Creates a new :class:`simplekml.ScreenOverlay` and attaches it to this KML document.

        Arguments are the same as :class:`simplekml.ScreenOverlay`

        Returns:
          * an instance of :class:`simplekml.ScreenOverlay` class.
        """
        return self._newfeature(ScreenOverlay, **kwargs)

    def newphotooverlay(self, **kwargs):
        """Creates a new :class:`simplekml.PhotoOverlay` and attaches it to this KML document.

        Arguments are the same as :class:`simplekml.PhotoOverlay`

        Returns:
          * an instance of :class:`simplekml.PhotoOverlay` class.
        """
        return self._newfeature(PhotoOverlay, **kwargs)

    def newmodel(self, **kwargs):
        """Creates a new :class:`simplekml.Model` and attaches it to this KML document.

        Arguments are the same as :class:`simplekml.Model`

        Returns:
          * an instance of :class:`simplekml.Model` class.
        """
        return self._newfeature(Model, **kwargs)

    def newgxtrack(self, **kwargs):
        """Creates a new :class:`simplekml.GxTrack` and attaches it to this KML document.

        Arguments are the same as :class:`simplekml.GxTrack`

        Returns:
          * an instance of :class:`simplekml.GxTrack` class.
        """
        return self._newfeature(GxTrack, **kwargs)

    def newgxmultitrack(self, **kwargs):
        """Creates a new :class:`simplekml.GxMultiTrack` and attaches it to this KML document.

        Arguments are the same as :class:`simplekml.GxMultiTrack`

        Returns:
          * an instance of :class:`simplekml.GxMultiTrack` class.
        """
        return self._newfeature(GxMultiTrack, **kwargs)


class Container(Feature):
    """Abstract class, extended by :class:`simplekml.Document` and :class:`simplekml.Folder`

    Arguments are the same as :class:`simplekml.Feature`

    .. note::
       Not to be used directly.
    """
    def __init__(self, **kwargs):
        super(Container, self).__init__(**kwargs)

    def newfolder(self, **kwargs):
        """Creates a new :class:`simplekml.Folder` and attaches it to this KML document.

        Arguments are the same as :class:`simplekml.Folder`

        Returns:
          * an instance of :class:`simplekml.Folder` class.
        """
        return self._newfeature(Folder, **kwargs)

    def newdocument(self, **kwargs):
        """Creates a new :class:`simplekml.Folder` and attaches it to this KML document.

        Arguments are the same as :class:`simplekml.Folder`

        Returns:
          * an instance of :class:`simplekml.Folder` class.
        """
        return self._newfeature(Document, **kwargs)

    def newnetworklink(self, **kwargs):
        """Creates a new :class:`simplekml.NetworkLink` and attaches it to this KML document.

        Arguments are the same as :class:`simplekml.NetworkLink`

        Returns:
          * an instance of :class:`simplekml.NetworkLink` class.
        """
        return self._newfeature(NetworkLink, **kwargs)

    def newgxtour(self, **kwargs):
        """Creates a new :class:`simplekml.GxTour` and attaches it to this KML document.

        Arguments are the same as :class:`simplekml.GxTour`

        Returns:
          * an instance of :class:`simplekml.NetworkLink` class.
        """
        return self._newfeature(GxTour, **kwargs)


class Document(Container):
    """A container for features and styles.

    Arguments are the same as the properties.
    """

    def __init__(self, **kwargs):
        super(Document, self).__init__(**kwargs)

    def newschema(self, **kwargs):
        """Creates a new :class:`simplekml.Schema` and attaches it to this KML document.

        Arguments are the same as :class:`simplekml.Schema`

        Returns:
          * an instance of :class:`simplekml.Schema` class.
        """
        return self._newfeature(Schema, **kwargs)


class Folder(Container):
    """A container for features that act like a folder.

    Arguments are the same as the properties.
    """

    def __init__(self, **kwargs):
        super(Folder, self).__init__(**kwargs)


class Placemark(Feature):
    """A Placemark is a Feature with associated Geometry.

    Args:
      * geometry: any class that inherits from :class:`simplekml.Geometry`
      * *all other args same as* :class:`simplekml.Feature`

    .. note::
       Not to be used directly.
    """

    def __init__(self, geometry=None, **kwargs):
        super(Placemark, self).__init__(**kwargs)
        self._kml['Geometry_'] = geometry

    @property
    def geometry(self):
        """A class that inherits from :class:`simplekml.Geometry`"""
        return self._kml['Geometry_']

    @geometry.setter
    def geometry(self, geom):
        self._kml['Geometry_'] = geom


class Geometry(Kmlable):
    """Abstract class for all Geometries.

    Arguments are the same as :class:`simplekml.Placemark`
    
    .. note::
       Not to be used directly.
    """
    _id = 0
    def __init__(self, **kwargs):
        super(Geometry, self).__init__()
        self._id = "geom_{0}".format(Geometry._id)
        Geometry._id += 1
        self._placemark = Placemark(**kwargs)
        self._placemark.geometry = self
        self._parent = None
        self._style = None
        self._stylemap = None


    @property
    def id(self):
        """The id string."""
        return self._id

    @property
    def name(self):
        """Name of placemark, accepts string."""
        return self._placemark.name

    @name.setter
    def name(self, name):
        self._placemark.name = name

    @property
    def visibility(self):
        """Whether the feature is shown, accepts int 0 or 1."""
        return self._placemark.visibility

    @visibility.setter
    def visibility(self, visibility):
        self._placemark.visibility = visibility

    @property
    def atomauthor(self):
        """Author of the feature, accepts string."""
        return self._placemark.atomauthor

    @atomauthor.setter
    def atomauthor(self, atomauthor):
        self._placemark.atomauthor = atomauthor

    @property
    def atomlink(self):
        """URL containing this KML, accepts string."""
        return self._placemark.atomlink

    @atomlink.setter
    def atomlink(self, atomlink):
        self._placemark.atomlink = atomlink

    @property
    def address(self):
        """Standard address, accepts string."""
        return self._placemark.address

    @address.setter
    def address(self, address):
        self._placemark.address = address

    @property
    def xaladdressdetails(self):
        """Address in xAL format, accepts string."""
        return self._placemark.xaladdressdetails

    @xaladdressdetails.setter
    def xaladdressdetails(self, xaladdressdetails):
        self._placemark.xaladdressdetails = xaladdressdetails

    @property
    def phonenumber(self):
        """Phone number used by Google Maps mobile, accepts string."""
        return self._placemark.phonenumber

    @phonenumber.setter
    def phonenumber(self, phonenumber):
        self._placemark.phonenumber = phonenumber

    @property
    def description(self):
        """Description shown in the information balloon, accepts string."""
        return self._placemark.description

    @description.setter
    def description(self, description):
        self._placemark.description = description

    @property
    def camera(self):
        """Camera that views the scene, accepts :class:`simplekml.Camera`"""
        if self._placemark.camera is None:
            self._placemark.camera = Camera()
        return self._placemark.camera

    @camera.setter
    def camera(self, camera):
        self._placemark.camera = camera

    @property
    def lookat(self):
        """Camera relative to the feature, accepts :class:`simplekml.LookAt`"""
        if self._placemark.lookat is None:
            self._placemark.lookat = LookAt()
        return self._placemark.lookat

    @lookat.setter
    def lookat(self, lookat):
        self._placemark.lookat = lookat

    @property
    def snippet(self):
        """Short description of the feature, accepts :class:`simplekml.Snippet`"""
        return self._placemark.snippet

    @snippet.setter
    def snippet(self, snippet):
        self._placemark.snippet = snippet

    @property
    def extendeddata(self):
        """Short description of the feature, accepts :class:`simplekml.Snippet`"""
        return self._placemark.extendeddata

    @extendeddata.setter
    def extendeddata(self, extendeddata):
        self._placemark.extendeddata = extendeddata

    @property
    def timespan(self):
        """Period of time, accepts :class:`simplekml.TimeSpan`"""
        return self._placemark.timespan

    @timespan.setter
    def timespan(self, timespan):
        self._placemark.timespan = timespan

    @property
    def timestamp(self):
        """Single moment in time, accepts :class:`simplekml.TimeStamp`"""
        return self._placemark.timestamp

    @timestamp.setter
    def timestamp(self, timestamp):
        self._placemark.timestamp = timestamp

    @property
    def region(self):
        """Bounding box of feature, accepts :class:`simplekml.Region`"""
        return self._placemark.region

    @region.setter
    def region(self, region):
        self._placemark.region = region

    @property
    def style(self):
        """The current style of the feature, accepts :class:`simplekml.Style`"""
        if self._style is None:
            self._style = Style()
            self._placemark._setstyle(self._style)
            if self._parent is not None:
                self._parent._addstyle(self._style)
        return self._style

    @style.setter
    def style(self, style):
        self._placemark._setstyle(style)
        if self._parent is not None:
            self._parent._addstyle(style)
        self._style = style

    @property
    def stylemap(self):
        """The current StyleMap of the feature, accepts :class:`simplekml.StyleMap`"""
        if self._stylemap is None:
            self._stylemap = StyleMap()
            self._placemark._setstyle(self._stylemap)
            if self._parent is not None:
                self._parent._addstylemap(self._stylemap)
        return self._stylemap

    @stylemap.setter
    def stylemap(self, stylemap):
        self._placemark._setstyle(stylemap)
        if self._parent is not None:
            self._parent._addstylemap(stylemap)
        self._stylemap = stylemap

    @property
    def iconstyle(self):
        """IconStyle of the feature, accepts :class:`simplekml.IconStyle`"""
        return self.style.iconstyle

    @iconstyle.setter
    def iconstyle(self, iconstyle):
        self.style.iconstyle = iconstyle

    @property
    def labelstyle(self):
        """LabelStyle of the feature, accepts :class:`simplekml.LabelStyle`"""
        return self.style.labelstyle

    @labelstyle.setter
    def labelstyle(self, labelstyle):
        self.style.labelstyle = labelstyle

    @property
    def linestyle(self):
        """LineStyle of the feature, accepts :class:`simplekml.LineStyle`"""
        return self.style.linestyle

    @linestyle.setter
    def linestyle(self, linestyle):
        self.style.linestyle = linestyle

    @property
    def polystyle(self):
        """PolyStyle of the feature, accepts :class:`simplekml.PolyStyle`"""
        return self.style.polystyle

    @polystyle.setter
    def polystyle(self, polystyle):
        self.style.polystyle = polystyle

    @property
    def balloonstyle(self):
        """BalloonStyle of the feature, accepts :class:`simplekml.BalloonStyle`"""
        return self.style.balloonstyle

    @balloonstyle.setter
    def balloonstyle(self, balloonstyle):
        self.style.balloonstyle = balloonstyle

    @property
    def liststyle(self):
        """ListStyle of the feature, accepts :class:`simplekml.ListStyle`"""
        return self.style.liststyle

    @liststyle.setter
    def liststyle(self, liststyle):
        self.style.liststyle = liststyle
    
    @property
    def placemark(self):
        """The placemark that contains this feature, read-only."""
        return self._placemark


class PointGeometry(Geometry):
    """Abstract class for any geometry requiring coordinates (not :class:`simplekml.Polygon`).

    Args:
      * coords: list of tuples (see :func:`simplekml.coords` for examples)
      * *all other args same as* :class:`simplekml.Geometry`

    .. note::
       Not to be used directly.
    """
    def __init__(self,
                 coords=(), **kwargs):
        super(PointGeometry, self).__init__(**kwargs)
        self._kml['coordinates'] = Coordinates()
        self._kml['coordinates'].addcoordinates(list(coords))

    @property
    def coords(self):
        """The coordinates of the feature, accepts list of tuples.

        A tuple represents a coordinate in lat/lon. The tuple has the option
        of specifying a height. If no height is given, it defaults to zero.
        A point feature has just one point, therefore a list with one tuple
        is given.

        Examples:
        No height: `[(1.0, 1.0), (2.0, 1.0)]`
        Height:    `[(1.0, 1.0, 50.0), (2.0, 1.0, 10.0)]`
        Point:     `[(1.0, 1.0)]`
        """
        return self._kml['coordinates']

    @coords.setter
    def coords(self, coords):
        self._kml['coordinates'] = Coordinates()
        self._kml['coordinates'].addcoordinates(coords)


class LinearRing(PointGeometry):
    """A closed line string, typically the outer boundary of a :class:`simplekml.Polygon`

    Arguments are the same as the properties.
    """
    def __init__(self, coords=(),
                 extrude=None,
                 tessellate=None,
                 altitudemode=None,
                 gxaltitudemode=None,
                 gxaltitudeoffset=None,
                 **kwargs):
        super(LinearRing, self).__init__(list(coords), **kwargs)
        self._kml['extrude'] = extrude
        self._kml['tessellate'] = tessellate
        self._kml['altitudeMode'] = altitudemode
        self._kml['gx:altitudeMode'] = gxaltitudemode
        self._kml['gx:altitudeOffset'] = gxaltitudeoffset

    @property
    def extrude(self):
        """Connect the LinearRing to the ground, accepts int (0 or 1)."""
        return self._kml['extrude']

    @extrude.setter
    def extrude(self, extrude):
        self._kml['extrude'] = extrude

    @property
    def tessellate(self):
        """Allows the LinearRing to follow the terrain, accepts int (0 or 1)."""
        return self._kml['tessellate']

    @tessellate.setter
    def tessellate(self, tessellate):
        self._kml['tessellate'] = tessellate

    @property
    def altitudemode(self):
        """Specifies how the altitude for the Camera is interpreted.

        Accepts :class:`simplekml.AltitudeMode` constants.
        """
        return self._kml['altitudeMode']

    @altitudemode.setter
    def altitudemode(self, mode):
        self._kml['altitudeMode'] = mode

    @property
    def gxaltitudemode(self):
        """Specifies how the altitude for the Camera is interpreted.

        With the addition of being relative to the sea floor.
        Accepts :class:`simplekml.GxAltitudeMode` constants.
        """
        return self._kml['gx:altitudeMode']

    @gxaltitudemode.setter
    def gxaltitudemode(self, mode):
        self._kml['gx:altitudeMode'] = mode

    @property
    def gxaltitudeoffset(self):
        """How much to offsets the LinearRing vertically, accepts int."""
        return self._kml['gx:altitudeOffset']

    @gxaltitudeoffset.setter
    def gxaltitudeoffset(self, offset):
        self._kml['gx:altitudeOffset'] = offset

    def __str__(self):
        return '<LinearRing id="{0}">{1}</LinearRing>'.format(self._id, super(LinearRing, self).__str__())


class Point(PointGeometry):
    """A geographic location defined by lon, lat, and altitude.

    Arguments are the same as the properties.
    """

    def __init__(self,
                 extrude=None,
                 altitudemode=None,
                 gxaltitudemode=None,
                 **kwargs):
        super(Point, self).__init__(**kwargs)
        self._kml['extrude'] = extrude
        self._kml['altitudeMode'] = altitudemode
        self._kml['gx:altitudeMode'] = gxaltitudemode

    @property
    def extrude(self):
        """Connect the Point to the ground, accepts int (0 or 1)."""
        return self._kml['extrude']

    @extrude.setter
    def extrude(self, extrude):
        self._kml['extrude'] = extrude

    @property
    def altitudemode(self):
        """Specifies how the altitude for the Camera is interpreted.

        Accepts :class:`simplekml.AltitudeMode` constants.
        """
        return self._kml['altitudeMode']

    @altitudemode.setter
    def altitudemode(self, mode):
        self._kml['altitudeMode'] = mode

    @property
    def gxaltitudemode(self):
        """Specifies how the altitude for the Camera is interpreted.

        With the addition of being relative to the sea floor.
        Accepts :class:`simplekml.GxAltitudeMode` constants.
        """
        return self._kml['gx:altitudeMode']

    @gxaltitudemode.setter
    def gxaltitudemode(self, mode):
        self._kml['gx:altitudeMode'] = mode

    def __str__(self):
        return '<Point id="{0}">{1}</Point>'.format(self._id, super(Point, self).__str__())


class LineString(PointGeometry):
    """A connected set of line segments.

    Arguments are the same as the properties.
    """
    def __init__(self,
                 extrude=None,
                 tessellate=None,
                 altitudemode=None,
                 gxaltitudemode=None,
                 gxaltitudeoffset=None,
                 gxdraworder=None,
                 **kwargs):
        super(LineString, self).__init__(**kwargs)
        self._kml['extrude'] = extrude
        self._kml['tessellate'] = tessellate
        self._kml['altitudeMode'] = altitudemode
        self._kml['gx:altitudeMode'] = gxaltitudemode
        self._kml['gx:altitudeOffset'] = gxaltitudeoffset
        self._kml['gx:drawOrder'] = gxdraworder

    @property
    def extrude(self):
        """Connect the LinearRing to the ground, accepts int (0 or 1)."""
        return self._kml['extrude']

    @extrude.setter
    def extrude(self, extrude):
        self._kml['extrude'] = extrude

    @property
    def tessellate(self):
        """Allowe the LinearRing to follow the terrain, accepts int (0 or 1)."""
        return self._kml['tessellate']

    @tessellate.setter
    def tessellate(self, tessellate):
        self._kml['tessellate'] = tessellate

    @property
    def altitudemode(self):
        """Specifies how the altitude for the Camera is interpreted.

        Accepts :class:`simplekml.AltitudeMode` constants.
        """
        return self._kml['altitudeMode']

    @altitudemode.setter
    def altitudemode(self, mode):
        self._kml['altitudeMode'] = mode

    @property
    def gxaltitudemode(self):
        """Specifies how the altitude for the Camera is interpreted.

        With the addition of being relative to the sea floor.
        Accepts :class:`simplekml.GxAltitudeMode` constants.
        """
        return self._kml['gx:altitudeMode']

    @gxaltitudemode.setter
    def gxaltitudemode(self, mode):
        self._kml['gx:altitudeMode'] = mode

    @property
    def gxaltitudeoffset(self):
        """How much to offsets the LinearRing vertically, accepts int."""
        return self._kml['gx:altitudeOffset']

    @gxaltitudeoffset.setter
    def gxaltitudeoffset(self, offset):
        self._kml['gx:altitudeOffset'] = offset

    @property
    def gxdraworder(self):
        """The order to draw the linestring, accepts int."""
        return self._kml['gx:drawOrder']

    @gxdraworder.setter
    def gxdraworder(self, gxdraworder):
        self._kml['gx:drawOrder'] = gxdraworder

    def __str__(self):
        return '<LineString id="{0}">{1}</LineString>'.format(self._id, super(LineString, self).__str__())


class Polygon(Geometry):
    """A Polygon is defined by an outer boundary and/or an inner boundary.

    Arguments are the same as the properties.
    """

    def __init__(self,
                 extrude=None,
                 tessellate=None,
                 altitudemode=None,
                 gxaltitudemode=None,
                 outerboundaryis=(),
                 innerboundaryis=(), **kwargs):
        super(Polygon, self).__init__(**kwargs)
        self._kml['extrude'] = extrude
        self._kml['tessellate'] = tessellate
        self._kml['altitudeMode'] = altitudemode
        self._kml['gx:altitudeMode'] = gxaltitudemode
        self._kml['outerBoundaryIs'] = LinearRing(list(outerboundaryis))
        self._kml['innerBoundaryIs'] = None
        self.innerboundaryis = list(innerboundaryis)

    @property
    def extrude(self):
        """Connect the LinearRing to the ground, accepts int (0 or 1)."""
        return self._kml['extrude']

    @extrude.setter
    def extrude(self, extrude):
        self._kml['extrude'] = extrude

    @property
    def tessellate(self):
        """Allows the Polygon to follow the terrain, accepts int (0 or 1)."""
        return self._kml['tessellate']

    @tessellate.setter
    def tessellate(self, tessellate):
        self._kml['tessellate'] = tessellate

    @property
    def altitudemode(self):
        """Specifies how the altitude for the Camera is interpreted.

        Accepts :class:`simplekml.AltitudeMode` constants.
        """
        return self._kml['altitudeMode']

    @altitudemode.setter
    def altitudemode(self, mode):
        self._kml['altitudeMode'] = mode

    @property
    def gxaltitudemode(self):
        """Specifies how the altitude for the Camera is interpreted.

        With the addition of being relative to the sea floor.
        Accepts :class:`simplekml.GxAltitudeMode` constants.
        """
        return self._kml['gx:altitudeMode']

    @gxaltitudemode.setter
    def gxaltitudemode(self, mode):
        self._kml['gx:altitudeMode'] = mode

    @property
    def innerboundaryis(self):
        """The inner boundaries.

        Accepts list of list of tuples of floats for multiple boundaries, or a
        list of tuples of floats for a single boundary.
        """
        return self._innerboundaryis

    @innerboundaryis.setter
    def innerboundaryis(self, rings):
        self._innerboundaryis = []
        if not len(rings):
            self._kml['innerBoundaryIs'] = None
        else:
            if type(rings[0]) == type(()):
                rings = [rings]
            self._kml['innerBoundaryIs'] = ''
            for ring in rings:
                self._kml['innerBoundaryIs'] += LinearRing(ring).__str__()
                self._innerboundaryis.append(LinearRing(ring))

    @property
    def outerboundaryis(self):
        """The outer boundary, accepts a list of tuples of floats."""
        return self._kml['outerBoundaryIs']

    @outerboundaryis.setter
    def outerboundaryis(self, coords):
        self._kml['outerBoundaryIs'] = LinearRing(coords)

    def __str__(self):
        return '<Polygon id="{0}">{1}</Polygon>'.format(self._id, super(Polygon, self).__str__())


class MultiGeometry(Geometry):
    """MultiGeometry is a collection of simple features (Points, LineStrings, etc).

    Arguments are the same as the properties.
    """

    def __init__(self,
                 geometries=(), **kwargs):
        super(MultiGeometry, self).__init__(**kwargs)
        self._geometries = list(geometries)

    def _newfeature(self, cls, **kwargs):
        feat = cls(**kwargs)
        feat._parent = self._placemark
        self._geometries.append(feat)
        return feat

    def newpoint(self, **kwargs):
        """Creates a new :class:`simplekml.Point` and attaches it to this MultiGeometry.

        The arguments are the same as :class:`simplekml.Point`

        Returns:
          * an instance of :class:`simplekml.Point`
        """
        return self._newfeature(Point, **kwargs)

    def newlinestring(self, **kwargs):
        """Creates a new :class:`simplekml.LineString` and attaches it to this MultiGeometry.

        The arguments are the same as :class:`simplekml.LineString`

        Returns:
          * an instance of :class:`simplekml.LineString`
        """
        return self._newfeature(LineString, **kwargs)

    def newpolygon(self, **kwargs):
        """Creates a new :class:`simplekml.Polygon` and attaches it to this MultiGeometry.

        The arguments are the same as :class:`simplekml.Polygon`

        Returns:
          * an instance of :class:`simplekml.Polygon`
        """
        return self._newfeature(Polygon, **kwargs)

    def newgroundoverlay(self, **kwargs):
        """Creates a new :class:`simplekml.GroundOverlay` and attaches it to this MultiGeometry.

        The arguments are the same as :class:`simplekml.GroundOverlay`

        Returns:
          * an instance of :class:`simplekml.GroundOverlay`
        """
        return self._newfeature(GroundOverlay, **kwargs)

    def newscreenoverlay(self, **kwargs):
        """Creates a new :class:`simplekml.ScreenOverlay` and attaches it to this MultiGeometry.

        The arguments are the same as :class:`simplekml.ScreenOverlay`

        Returns:
          * an instance of :class:`simplekml.ScreenOverlay`
        """
        return self._newfeature(ScreenOverlay, **kwargs)

    def newphotooverlay(self, **kwargs):
        """Creates a new :class:`simplekml.PhotoOverlay` and attaches it to this MultiGeometry.

        The arguments are the same as :class:`simplekml.PhotoOverlay`

        Returns:
          * an instance of :class:`simplekml.PhotoOverlay`
        """
        return self._newfeature(PhotoOverlay, **kwargs)

    def newmodel(self, **kwargs):
        """Creates a new :class:`simplekml.Model` and attaches it to this MultiGeometry.

        The arguments are the same as :class:`simplekml.Model`

        Returns:
          * an instance of :class:`simplekml.Model`
        """
        return self._newfeature(Model, **kwargs)

    def __str__(self):
        buf = ['<MultiGeometry id="{0}">'.format(self._id),
               super(MultiGeometry, self).__str__()]
        for geom in self._geometries:
            buf.append(geom.__str__())
        buf.append("</MultiGeometry>")
        return "".join(buf)


class Overlay(Feature):
    """Abstract class for image overlays.

    Arguments are the same as the properties.

    .. note::
      Not to be used directly.
    """
    def __init__(self, color=None,
                       draworder=None,
                       icon=None,
                       **kwargs):
        super(Overlay, self).__init__(**kwargs)
        self._kml['color'] = color
        self._kml['drawOrder'] = draworder
        self._kml['Icon_'] = icon

    @property
    def color(self):
        """The color of the overlay, accepts hex string."""
        return self._kml['color']

    @color.setter
    def color(self, color):
        self._kml['color'] = color

    @property
    def draworder(self):
        """The order to draw the overlay, accepts int."""
        return self._kml['drawOrder']

    @draworder.setter
    def draworder(self, draworder):
        self._kml['drawOrder'] = draworder

    @property
    def icon(self):
        """The icon to use for the overlay, accepts :class:`simplekml.Icon]`"""
        if self._kml['Icon_'] is None:
            self._kml['Icon_'] = Icon()
        return self._kml['Icon_']

    @icon.setter
    def icon(self, icon):
        self._kml['Icon_'] = icon


class GroundOverlay(Overlay):
    """Draws an image overlay draped onto the terrain.

    Arguments are the same as the properties.
    """

    def __init__(self, altitude=None,
                       altitudemode=None,
                       gxaltitudemode=None,
                       latlonbox=None,
                       gxlatlonquad=None,
                       **kwargs):
        super(GroundOverlay, self).__init__(**kwargs)
        self._kml['altitude'] = altitude
        self._kml['altitudeMode'] = altitudemode
        self._kml['gx:altitudeMode'] = gxaltitudemode
        self._kml['LatLonBox'] = latlonbox
        self._kml['gx:LatLonQuad'] = gxlatlonquad

    @property
    def altitude(self):
        """Distance above earth surface, accepts float."""
        return self._kml['altitude']

    @altitude.setter
    def altitude(self, altitude):
        self._kml['altitude'] = altitude

    @property
    def altitudemode(self):
        """Specifies how the altitude for the Camera is interpreted.

        Accepts :class:`simplekml.AltitudeMode` constants.
        """
        return self._kml['altitudeMode']

    @altitudemode.setter
    def altitudemode(self, altitudemode):
        self._kml['altitudeMode'] = altitudemode

    @property
    def gxaltitudemode(self):
        """Specifies how the altitude for the Camera is interpreted.

        With the addition of being relative to the sea floor.
        Accepts :class:`simplekml.GxAltitudeMode` constants.
        """
        return self._kml['gx:altitudeMode']

    @gxaltitudemode.setter
    def gxaltitudemode(self, gxaltitudemode):
        self._kml['gx:altitudeMode'] = gxaltitudemode

    @property
    def latlonbox(self):
        """Specifies where the top, bottom, right, and left sides are.

        Accepts :class:`simplekml.LatLonBox`.
        """
        if self._kml['LatLonBox'] is None:
            self._kml['LatLonBox'] = LatLonBox()
        return self._kml['LatLonBox']

    @latlonbox.setter
    def latlonbox(self, latlonbox):
        self._kml['LatLonBox'] = latlonbox

    @property
    def gxlatlonquad(self):
        """Specifies the coordinates of the four corner points of a quadrilateral
        defining the overlay area. Accepts :class:`simplekml.GxLatLonQuad`
        """
        if self._kml['gx:LatLonQuad'] is None:
            self._kml['gx:LatLonQuad'] = GxLatLonQuad()
        return self._kml['gx:LatLonQuad']

    @gxlatlonquad.setter
    def gxlatlonquad(self, gxlatlonquad):
        self._kml['gx:LatLonQuad'] = gxlatlonquad


class ScreenOverlay(Overlay):
    """Draws an image overlay fixed to the screen.

    Arguments are the same as the properties.
    """

    def __init__(self, overlayxy=None,
                       screenxy=None,
                       rotationxy=None,
                       size=None,
                       rotation=None,
                       **kwargs):
        super(ScreenOverlay, self).__init__(**kwargs)
        self._kml['rotation'] =rotation
        self._kml['overlayXY_'] = overlayxy
        self._kml['screenXY_'] = screenxy
        self._kml['rotationXY_'] = rotationxy
        self._kml['size_'] = size

    @property
    def rotation(self):
        """Rotation of the overlay, accepts float."""
        return self._kml['rotation']

    @rotation.setter
    def rotation(self, rotation):
        self._kml['rotation'] = rotation

    @property
    def overlayxy(self):
        """Point on the overlay image that is mapped to a screen coordinate.

        Specifies a point on (or outside of) the overlay image that is mapped
        to the screen coordinate :class:`simplekml.ScreenXY`,
        accepts :class:`simplekml.OverlayXY`
        """
        if self._kml['overlayXY_'] is None:
            self._kml['overlayXY_'] = OverlayXY()
        return self._kml['overlayXY_']

    @overlayxy.setter
    def overlayxy(self, overlayxy):
        self._kml['overlayXY_'] = overlayxy

    @property
    def screenxy(self):
        """Point relative to screen origin that the image is mapped to.

        Specifies a point relative to the screen origin that the overlay image
        is mapped to, accepts :class:`simplekml.ScreenXY`
        """
        if self._kml['screenXY_'] is None:
            self._kml['screenXY_'] = ScreenXY()
        return self._kml['screenXY_']

    @screenxy.setter
    def screenxy(self, screenxy):
        self._kml['screenXY_'] = screenxy

    @property
    def rotationxy(self):
        """Point relative to the screen about which the overlay is rotated.

        Accepts :class:`simplekml.RotationXY`
        """
        if self._kml['rotationXY_'] is None:
            self._kml['rotationXY_'] = RotationXY()
        return self._kml['rotationXY_']

    @rotationxy.setter
    def rotationxy(self, rotationxy):
        self._kml['rotationXY_'] = rotationxy

    @property
    def size(self):
        """The size of the image for the screen overlay, accepts :class:`simplekml.Size`"""
        if self._kml['size_'] is None:
            self._kml['size_'] = Size()
        return self._kml['size_']

    @size.setter
    def size(self, size):
        self._kml['size_'] = size


class PhotoOverlay(Overlay):
    """Geographically locate a photograph in Google Earth.

    Arguments are the same as the properties.
    """

    def __init__(self, rotation=None,
                       viewvolume=None,
                       imagepyramid=None,
                       point=None,
                       shape=None,
                       **kwargs):
        super(PhotoOverlay, self).__init__(**kwargs)
        self._kml['rotation'] = rotation
        self._kml['ViewVolume'] = viewvolume
        self._kml['ImagePyramid'] = imagepyramid
        self._kml['point_'] = point
        self._kml['shape'] = shape

    @property
    def rotation(self):
        """Rotation of the overlay, accepts float."""
        return self._kml['rotation']

    @rotation.setter
    def rotation(self, rotation):
        self._kml['rotation'] = rotation

    @property
    def viewvolume(self):
        """How much of the current scene is visible, accepts :class:`simplekml.ViewVolume`"""
        if self._kml['ViewVolume'] is None:
            self._kml['ViewVolume'] = ViewVolume()
        return self._kml['ViewVolume']

    @viewvolume.setter
    def viewvolume(self, viewvolume):
        self._kml['ViewVolume'] = viewvolume

    @property
    def imagepyramid(self):
        """Hierarchical set of images, accepts :class:`simplekml.ImagePyramid`"""
        if self._kml['ImagePyramid'] is None:
            self._kml['ImagePyramid'] = ImagePyramid()
        return self._kml['ImagePyramid']

    @imagepyramid.setter
    def imagepyramid(self, imagepyramid):
        self._kml['ImagePyramid'] = imagepyramid

    @property
    def point(self):
        """Draws an icon to mark the position of the overlay,accepts :class:`simplekml.Point`"""
        if self._kml['point_'] is None:
            self._kml['point_'] = Point()
        return self._kml['point_']

    @point.setter
    def point(self, point):
        self._kml['point_'] = point

    @property
    def shape(self):
        """Shape the photo is drawn, accepts string from :class:`simplekml.Shape` constants."""
        return self._kml['shape']

    @shape.setter
    def shape(self, shape):
        self._kml['shape'] = shape


class NetworkLink(Feature):
    """References a KML file or KMZ archive on a local or remote network.

    Arguments are the same as the properties.
    """
    
    def __init__(self, refreshvisibility=None,
                       flytoview=None,
                       link=None,
                       **kwargs):
        super(NetworkLink, self).__init__(**kwargs)
        self._kml['refreshVisibility'] = refreshvisibility
        self._kml['flyToView'] = flytoview
        self._kml['Link_'] = link

    @property
    def refreshvisibility(self):
        """How the visibility is affected by a refresh

        A value of 0 leaves the visibility of features within the control of
        the Google Earth user. Set the value to 1 to reset the visibility of
        features each time the NetworkLink is refreshed, accepts int (0 or 1).
         
        """
        return self._kml['refreshVisibility']

    @refreshvisibility.setter
    def refreshvisibility(self, refreshvisibility):
        self._kml['refreshVisibility'] = refreshvisibility

    @property
    def flytoview(self):
        """A value of 1 causes Google Earth to fly to the view of the AbstractView.

        Accepts int (0 or 1).
        """
        return self._kml['flyToView']

    @flytoview.setter
    def flytoview(self, flytoview):
        self._kml['flyToView'] = flytoview

    @property
    def link(self):
        """A :class:`simplekml.Link` class instance, accepts :class:`simplekml.Link`"""
        if self._kml['Link_'] is None:
            self._kml['Link_'] = Link()
        return self._kml['Link_']

    @link.setter
    def link(self, link):
        self._kml['Link_'] = link


class Model(Geometry):
    """A 3D object described in a COLLADA file.

    Arguments are the same as the properties.
    """

    def __init__(self,
                 altitudemode=None,
                 gxaltitudemode=None,
                 location=None,
                 orientation=None,
                 scale=None,
                 link=None,
                 resourcemap=None,
                 **kwargs):
        super(Model, self).__init__(**kwargs)
        self._kml['altitudeMode'] = altitudemode
        self._kml['gx:altitudeMode'] = gxaltitudemode
        self._kml['Location'] = location
        self._kml['Orientation'] = orientation
        self._kml['Scale'] = scale
        self._kml['Link_'] = link
        self._kml['ResourceMap'] = resourcemap

    @property
    def altitudemode(self):
        """Specifies how the altitude for the Camera is interpreted.

        Accepts :class:`simplekml.AltitudeMode` constants.
        """
        return self._kml['altitudeMode']

    @altitudemode.setter
    def altitudemode(self, altitudemode):
        self._kml['altitudeMode'] = altitudemode

    @property
    def gxaltitudemode(self):
        """Specifies how the altitude for the Camera is interpreted.

        With the addition of being relative to the sea floor.
        Accepts :class:`simplekml.GxAltitudeMode` constants.
        """
        return self._kml['gx:altitudeMode']

    @gxaltitudemode.setter
    def gxaltitudemode(self, gxaltitudemode):
        self._kml['gx:altitudeMode'] = gxaltitudemode

    @property
    def location(self):
        """Position of the origin of the model, accepts :class:`simplekml.Location`"""
        if self._kml['Location'] is None:
            self._kml['Location'] = Location()
        return self._kml['Location']

    @location.setter
    def location(self, location):
        self._kml['Location'] = location

    @property
    def orientation(self):
        """The rotation on the model, accepts :class:`simplekml.Orientation`"""
        if self._kml['Orientation'] is None:
            self._kml['Orientation'] = Orientation()
        return self._kml['Orientation']

    @orientation.setter
    def orientation(self, orientation):
        self._kml['Orientation'] = orientation

    @property
    def scale(self):
        """"The scale of the model, accepts :class:`simplekml.Scale`"""
        if self._kml['Scale'] is None:
            self._kml['Scale'] = Scale()
        return self._kml['Scale']

    @scale.setter
    def scale(self, scale):
        self._kml['Scale'] = scale

    @property
    def link(self):
        """"A :class:`simplekml.Link` class instance, accepts :class:`simplekml.Link`"""
        if self._kml['Link_'] is None:
            self._kml['Link_'] = Link()
        return self._kml['Link_']

    @link.setter
    def link(self, link):
        self._kml['Link_'] = link

    @property
    def resourcemap(self):
        """Used for mapping textures, accepts :class:`simplekml.ResourceMap`"""
        if self._kml['ResourceMap'] is None:
            self._kml['ResourceMap'] = ResourceMap()
        return self._kml['ResourceMap']

    @resourcemap.setter
    def resourcemap(self, resourcemap):
        self._kml['ResourceMap'] = resourcemap

    def __str__(self):
        return '<Model id="{0}">{1}</Model>'.format(self._id, super(Model, self).__str__())


class GxTrack(Geometry):
    """A track describes how an object moves through the world over a given time period.

    Arguments are the same as the properties.
    """

    def __init__(self,
                 extrude=None,
                 altitudemode=None,
                 gxaltitudemode=None,
                 **kwargs):
        super(GxTrack, self).__init__(**kwargs)
        self._kml['extrude'] = extrude
        self._kml['altitudeMode'] = altitudemode
        self._kml['gx:altitudeMode'] = gxaltitudemode
        self._kml['ExtendedData'] = None
        self.whens = []
        self.gxcoords = []
        self.angles = []

    @property
    def extrude(self):
        """Connect the GxTrack to the ground, accepts int (0 or 1)."""
        return self._kml['extrude']

    @extrude.setter
    def extrude(self, extrude):
        self._kml['extrude'] = extrude

    @property
    def altitudemode(self):
        """Specifies how the altitude for the Camera is interpreted.

        Accepts :class:`simplekml.AltitudeMode` constants.

        """
        return self._kml['altitudeMode']

    @altitudemode.setter
    def altitudemode(self, altitudemode):
        self._kml['altitudeMode'] = altitudemode

    @property
    def gxaltitudemode(self):
        """Specifies how the altitude for the Camera is interpreted.

        With the addition of being relative to the sea floor.
        Accepts :class:`simplekml.GxAltitudeMode` constants.
        """
        return self._kml['gx:altitudeMode']

    @gxaltitudemode.setter
    def gxaltitudemode(self, gxaltitudemode):
        self._kml['gx:altitudeMode'] = gxaltitudemode

    def newdata(self, gxcoord, when, angle=None):
        """Creates a new gxcoord, when time and angle (if provided).

        This is a convenience method for calling newwhen, newgxcoord and
        newangle. when and gxcoord are required, angle is optional.
        """
        self.newgxcoord(gxcoord)
        self.newwhen(when)
        if angle is not None:
            self.newangle(angle)

    def newwhen(self, when):
        """Creates a new when time, accepts string or list of string.

        If one string is given a single when entry is created, but if a list of
        strings is given, a when entry is created for each string in the list.
        """
        if type(when) == list:
            self.whens += when
        else:
            self.whens.append(when)

    def newgxcoord(self, coord):
        """Creates a gx:coord, accepts list of one tuples.

        A gxcoord entry is created for every tuple in the list.
        """
        if type(coord) == list:
            for crd in coord:
                coords = Coordinates()
                coords.addcoordinates([crd])
                self.gxcoords.append(coords)
        else:
            coords = Coordinates()
            coords.addcoordinates(list(coord))
            self.gxcoords.append(coords)

    def newangle(self, angle):
        """Creates a new angle, accepts float or list of floats.

        If one float is given a single angle entry is created, but if a list of
        floats is given, a angle entry is created for each float in the list.
        """
        if type(angle) == list:
            self.angles += angle
        else:
            self.angles.append(angle)

    @property
    def extendeddata(self):
        """Extra data for the feature."""
        if self._kml['ExtendedData'] is None:
            self._kml['ExtendedData'] = ExtendedData()
        return self._kml['ExtendedData']

    @extendeddata.setter
    def extendeddata(self, extendeddata):
        self._kml['ExtendedData'] = extendeddata

    def __str__(self):
        buf = ['<gx:Track>']
        for when in self.whens:
            buf.append("<when>{0}</when>".format(when))
        for angle in self.angles:
            buf.append("<angle>{0}</angle>".format(angle))
        for gxcoord in self.gxcoords:
            buf.append("<gx:coord>{0}</gx:coord>".format(gxcoord.__str__().replace(',', ' ')))
        buf.append(super(GxTrack, self).__str__())
        buf.append('</gx:Track>')
        return "".join(buf)


class GxMultiTrack(Geometry):
    """A container for grouping gx:tracks.

    Arguments are the same as the properties.
    """

    def __init__(self,
                 tracks=(), gxinterpolate=None, **kwargs):
        super(GxMultiTrack, self).__init__(**kwargs)
        self._kml['gx:interpolate'] = gxinterpolate
        self.tracks = list(tracks)

    def newgxtrack(self, **kwargs):
        """Creates a new :class:`simplekml.GxTrack` and attaches it to this mutlitrack.

        Returns an instance of :class:`simplekml.GxTrack` class.

        Args:
          * Same as :class:`simplekml.GxTrack`, except arguments that are not applicable in a multitrack grouping will be ignored, such as name, visibility, open, etc.
        """
        self.tracks.append(GxTrack(**kwargs))
        return self.tracks[-1]

    def __str__(self):
        buf = ['<gx:MultiTrack id="{0}">'.format(self._id),
               super(GxMultiTrack, self).__str__()]
        for track in self.tracks:
            buf.append(track.__str__())
        buf.append("</gx:MultiTrack>")
        return "".join(buf)
