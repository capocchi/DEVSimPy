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
from timeprimitive import GxTimeStamp, GxTimeSpan


class AbstractView(Kmlable):
    """Abstract element, extended by :class:`simplekml.Camera` and :class:`simplekml.LookAt`

    The arguments are the same as the properties.
    
     .. note::
       Not to be used directly.


    """
    def __init__(self,
                 longitude=None,
                 latitude=None,
                 altitude=None,
                 heading=None,
                 tilt=None,
                 altitudemode=None,
                 gxaltitudemode=None,
                 gxtimespan=None,
                 gxtimestamp=None,
                 gxhorizfov=None):
        super(AbstractView, self).__init__()
        self._kml["longitude"] = longitude
        self._kml["latitude"] = latitude
        self._kml["altitude"] = altitude
        self._kml["heading"] = heading
        self._kml["tilt"] = tilt
        self._kml["altitudeMode"] = altitudemode
        self._kml["gx:AltitudeMode"] = gxaltitudemode
        self._kml["gx:TimeSpan_"] = gxtimespan
        self._kml["gx:TimeStamp_"] = gxtimestamp
        self._kml['gx:horizFov'] = gxhorizfov

    @property
    def longitude(self):
        """Decimal degree value in WGS84 datum, accepts float."""
        return self._kml['longitude']

    @longitude.setter
    def longitude(self, longitude):
        self._kml['longitude'] = longitude

    @property
    def latitude(self):
        """Decimal degree value in WGS84 datum, accepts float."""
        return self._kml['latitude']

    @latitude.setter
    def latitude(self, latitude):
        self._kml['latitude'] = latitude

    @property
    def altitude(self):
        """Height above the earth in meters (m), accepts int."""
        return self._kml['altitude']

    @altitude.setter
    def altitude(self, altitude):
        self._kml['altitude'] = altitude

    @property
    def heading(self):
        """Rotation about the z axis, accepts float."""
        return self._kml['heading']

    @heading.setter
    def heading(self, heading):
        self._kml['heading'] = heading

    @property
    def tilt(self):
        """Rotation about the x axis, accepts float."""
        return self._kml['tilt']

    @tilt.setter
    def tilt(self, tilt):
        self._kml['tilt'] = tilt

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
    def gxaltitudemode(self, gxaltmode):
        self._kml['gx:altitudeMode'] = gxaltmode

    @property
    def gxtimestamp(self):
        """Represents a single moment in time, accepts :class:`simplekml.GxTimeStamp`"""
        if self._kml['gx:TimeStamp_'] is None:
            self._kml['gx:TimeStamp_'] = GxTimeStamp()
        return self._kml['gx:TimeStamp_']

    @gxtimestamp.setter
    def gxtimestamp(self, gxtimestamp):
        self._kml['gx:TimeStamp_'] = gxtimestamp

    @property
    def gxtimespan(self):
        """Period of time, accepts :class:`simplekml.GxTimeSpan`"""
        if self._kml['gx:TimeSpan_'] is None:
            self._kml['gx:TimeSpan_'] = GxTimeSpan()
        return self._kml['gx:TimeSpan_']

    @gxtimespan.setter
    def gxtimespan(self, gxtimespan):
        self._kml['gx:TimeSpan_'] = gxtimespan

    @property
    def gxhorizfov(self):
        """Rotation about the x axis, accepts float."""
        return self._kml['gx:horizFov']

    @gxhorizfov.setter
    def gxhorizfov(self, gxhorizfov):
        self._kml['gx:horizFov'] = gxhorizfov


class Camera(AbstractView):
    """A virtual camera that views the scene.

    The arguments are the same as the properties (most inherited from
    :class:`simplekml.AbstractView`)
    """

    def __init__(self, roll=None, **kwargs):
        super(Camera, self).__init__(**kwargs)
        self._kml['roll'] = roll

    @property
    def roll(self):
        """Rotation about the y axis, accepts float."""
        return self._kml['roll']

    @roll.setter
    def roll(self, roll):
        self._kml['roll'] = roll


class LookAt(AbstractView): # --Document--
    """Positions the camera in relation to the object that is being viewed.

    The arguments are the same as the properties (most inherited from
    :class:`simplekml.AbstractView`)
    """

    def __init__(self, range=None, **kwargs):
        super(LookAt, self).__init__(**kwargs)
        self._kml['range'] = range

    @property
    def range(self):
        """Distance in meters from the point, accepts int."""
        return self._kml['range']

    @range.setter
    def range(self, range):
        self._kml['range'] = range


class GxOption(Kmlable):
    """Child element of :class:`simplekml.GxViewerOptions`.

    The arguments are the same as the properties.
    """
    streetview = "streetview"  # Used in Street View
    historicalimagery = "historicalimagery"  #Used for Historical Imagery
    sunlight = "sunlight"  # Used to control lighting

    def __init__(self, name=None, enabled=False):
        super(GxOption, self).__init__()
        self._kml = {'name': name,
                     'enabled': enabled}

    @property
    def name(self):
        """Name of the effect being applied.

        The following strings can be used :attr:`simplekml.GxOption.streetview`,
        :attr:`simplekml.GxOption.historicalimagery` or :attr:`simplekml.GxOption.sunlight`
        """
        return self._kml['name']

    @name.setter
    def name(self, name):
        self._kml['name'] = name

    @property
    def enabled(self):
        """Whether the effect must be turned on or off, boolean."""
        return self._kml['enabled']

    @enabled.setter
    def enabled(self, enabled):
        self._kml['enabled'] = enabled

    def __str__(self):
        return '<gx:option name="{0}" enabled={1}></gx:option>'.format(self._kml['name'], self._kml['enabled'])


class GxViewerOptions(Kmlable):
    """Enables special viewer modes.

    The arguments are the same as the properties.
    """
    def __init__(self, gxoptions=None):
        super(GxViewerOptions, self).__init__()
        self.gxoptions = []
        if gxoptions is not None:
            self.gxoptions += gxoptions

    def newgxoption(self, name, enabled=True):
        """Adds a :class:`simplekml.GxOption`."""
        self.gxoptions.append(GxOption(name, enabled))

    def __str__(self):
        buf = ['<gx:ViewerOptions>']
        for gxoption in self.gxoptions:
            buf.append(gxoption.__str__())
        buf.append("</gx:ViewerOptions>")
        return "".join(buf)
