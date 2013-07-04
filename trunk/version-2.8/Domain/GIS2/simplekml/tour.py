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
from abstractview import Camera, LookAt

class GxTourPrimitive(Kmlable):
    """Abstract class extended by all tour types.

    .. note::
      Not to be used directly.
    """
    _id = 0

    def __init__(self):
        super(GxTourPrimitive, self).__init__()
        self._id = "tour_{0}".format(GxTourPrimitive._id)
        GxTourPrimitive._id += 1

    @property
    def id(self):
        """The id string."""
        return self._id


class GxSoundCue(GxTourPrimitive):
    """Specifies a sound to be played in a tour.

    The arguments are the same as the properties.
    """
    def __init__(self,
                 href=None,
                 gxdelayedstart=None):
        super(GxSoundCue, self).__init__()
        self._kml['href'] = href
        self._kml['gx:delayedStart'] = gxdelayedstart

    @property
    def href(self):
        """A string reference to a sound file to play."""
        return self._kml['href']

    @href.setter
    def href(self, href):
        self._kml['href'] = href

    @property
    def gxdelayedstart(self):
        """Double telling the number of seconds to delay playing the file."""
        return self._kml['gx:delayedStart']

    @gxdelayedstart.setter
    def gxdelayedstart(self, gxdelayedstart):
        self._kml['gx:delayedStart'] = gxdelayedstart

    def __str__(self):
        buf = ['<gx:SoundCue id="{0}">'.format(self._id),
               super(GxSoundCue, self).__str__(),
               '</gx:SoundCue>'.format(self._id)]
        return "".join(buf)


class GxTourControl(GxTourPrimitive):
    """Allows a tour to be paused.

    The arguments are the same as the properties.
    """
    def __init__(self,
                 gxplaymode='pause'):
        super(GxTourControl, self).__init__()
        self._kml['gx:playMode'] = gxplaymode

    @property
    def gxplaymode(self):
        """String to pause the tour."""
        return self._kml['gx:playMode']

    @gxplaymode.setter
    def gxplaymode(self, gxplaymode):
        self._kml['gx:playMode'] = gxplaymode

    def __str__(self):
        buf = ['<gx:TourControl id="{0}">'.format(self._id),
               super(GxTourControl, self).__str__(),
               '</gx:TourControl>'.format(self._id)]
        return "".join(buf)


class GxWait(GxTourPrimitive):
    """Allows a tour to be paused.

    The arguments are the same as the properties.
    """
    def __init__(self,
                 gxduration=None):
        super(GxWait, self).__init__()
        self._kml['gx:duration'] = gxduration

    @property
    def gxduration(self):
        """Double indicating how long the camera remains still."""
        return self._kml['gx:duration']

    @gxduration.setter
    def gxduration(self, gxduration):
        self._kml['gx:duration'] = gxduration

    def __str__(self):
        buf = ['<gx:Wait id="{0}">'.format(self._id),
               super(GxWait, self).__str__(), '</gx:Wait>'.format(self._id)]
        return "".join(buf)


class GxFlyTo(GxTourPrimitive):
    """Allows unbroken flight from point to point.

    The arguments are the same as the properties.
    """

    bounce = "bounce"
    smooth = "smooth"

    def __init__(self,
                 gxduration=None,
                 gxflytomode=None,
                 camera=None,
                 lookat=None):
        super(GxFlyTo, self).__init__()
        self._kml['gx:duration'] = gxduration
        self._kml['gx:flyToMode'] = gxflytomode
        self._abstractview = None
        if camera is not None:
            self._abstractview = camera
        else:
            self._abstractview = lookat

    @property
    def gxduration(self):
        """Double indicating how long the camera remains still."""
        return self._kml['gx:duration']

    @gxduration.setter
    def gxduration(self, gxduration):
        self._kml['gx:duration'] = gxduration

    @property
    def gxflytomode(self):
        """How the caera behaves, smooth or bounce string."""
        return self._kml['gx:flyToMode']

    @gxflytomode.setter
    def gxflytomode(self, gxflytomode):
        self._kml['gx:flyToMode'] = gxflytomode

    @property
    def camera(self):
        """Camera that views the scene, accepts :class:`simplekml.Camera`"""
        if self._abstractview is None or type(self._abstractview) == LookAt:
            self._abstractview = Camera()
        return self._abstractview

    @camera.setter
    def camera(self, camera):
        self._abstractview = camera

    @property
    def lookat(self):
        """Camera relative to the feature, accepts :class:`simplekml.LookAt`"""
        if self._abstractview is None or type(self._abstractview) == Camera:
            self._abstractview = LookAt()
        return self._abstractview

    @lookat.setter
    def lookat(self, lookat):
        self._abstractview = lookat

    def __str__(self):
        buf = ['<gx:FlyTo id="{0}">'.format(self._id),
               super(GxFlyTo, self).__str__(),
               '</gx:FlyTo>'.format(self._id)]
        return "".join(buf)


class GxAnimatedUpdate(GxTourPrimitive):
    """Controls changes during a tour to KML features.

    The arguments are the same as the properties.
    """

    def __init__(self,
                 gxduration=None,
                 gxdelayedstart=None,
                 update=None):
        super(GxAnimatedUpdate, self).__init__()
        self._kml['gx:duration'] = gxduration
        self._kml['gx:delayedStart'] = gxdelayedstart
        self._kml['Update'] = update

    @property
    def gxduration(self):
        """Double indicating how long the camera remains still."""
        return self._kml['gx:duration']

    @gxduration.setter
    def gxduration(self, gxduration):
        self._kml['gx:duration'] = gxduration

    @property
    def gxdelayedstart(self):
        """Double of number of seconds to wait before starting."""
        return self._kml['gx:delayedStart']

    @gxdelayedstart.setter
    def gxdelayedstart(self, gxdelayedstart):
        self._kml['gx:delayedStart'] = gxdelayedstart

    @property
    def update(self):
        """Instance of :class:`simplekml.Update`"""
        if self._kml['Update'] is None:
            self._kml['Update'] = Update()
        return self._kml['Update']

    @update.setter
    def update(self, update):
        self._kml['Update'] = update

    def __str__(self):
        buf = ['<gx:AnimatedUpdate id="{0}">'.format(self._id),
               super(GxAnimatedUpdate, self).__str__(),
               '</gx:AnimatedUpdate>'.format(self._id)]
        return "".join(buf)


class Update(Kmlable):
    """Action to take when animation updates.

    The arguments are the same as the properties.
    """
    def __init__(self,
                 targethref=None,
                 change=None,
                 create=None,
                 delete=None):
        super(Update, self).__init__()
        if targethref is None:
            targethref = ""
        self._kml['targetHref'] = targethref
        self._kml['Change'] = change
        self._kml['Create'] = create
        self._kml['Delete'] = delete


    @property
    def targethref(self):
        """A string reference to a sound file to play."""
        return self._kml['targetHref']

    @targethref.setter
    def targethref(self, targethref):
        self._kml['targetHref'] = targethref

    @property
    def change(self):
        """KML string representing a change in animation."""
        return self._kml['Change']

    @change.setter
    def change(self, change):
        self._kml['Change'] = change

    @property
    def create(self):
        """KML string representing a creation during animation."""
        return self._kml['Create']

    @create.setter
    def create(self, create):
        self._kml['Create'] = create

    @property
    def delete(self):
        """KML string representing a deletion during animation."""
        return self._kml['Delete']

    @delete.setter
    def delete(self, delete):
        self._kml['Delete'] = delete


class GxPlaylist(Kmlable):
    """Defines a part of a tour.

    The arguments are the same as the properties.
    """
    def __init__(self, gxtourprimitives=None):
        super(GxPlaylist, self).__init__()
        self.gxtourprimitives = []
        if gxtourprimitives is not None:
            self.gxtourprimitives += gxtourprimitives

    def addgxtourprimitive(self, gxtourprimitive):
        """Adds a :class:`simplekml.GxTourPrimitive` sub-class."""
        self.gxtourprimitives.append(gxtourprimitive)

    def newgxanimatedupdate(self, **kwargs):
        """Creates a new :class:`simplekml.GxAnimatedUpdate` and adds it to the playlist.

        Accepts the same agruments as :class:`simplekml.GxAnimatedUpdate` and returns an instance
        of :class:`simplekml.GxAnimatedUpdate`
        """
        gxanimatedupdate = GxAnimatedUpdate(**kwargs)
        self.addgxtourprimitive(gxanimatedupdate)
        return gxanimatedupdate

    def newgxflyto(self, **kwargs):
        """Creates a new :class:`simplekml.GxFlyTo` and adds it to the playlist.

        Accepts the same agruments as :class:`simplekml.GxFlyTo` and returns an instance
        of :class:`simplekml.GxFlyTo`
        """
        gxflyto = GxFlyTo(**kwargs)
        self.addgxtourprimitive(gxflyto)
        return gxflyto

    def newgxsoundcue(self, **kwargs):
        """Creates a new :class:`simplekml.GxSoundCue` and adds it to the playlist.

        Accepts the same agruments as :class:`simplekml.GxSoundCue` and returns an instance
        of :class:`simplekml.GxSoundCue`
        """
        gxsoundcue = GxSoundCue(**kwargs)
        self.addgxtourprimitive(gxsoundcue)
        return gxsoundcue

    def newgxtourcontrol(self, **kwargs):
        """Creates a new :class:`simplekml.GxTourControl` and adds it to the playlist.

        Accepts the same agruments as :class:`simplekml.GxTourControl` and returns an instance
        of :class:`simplekml.GxTourControl`
        """
        gxtourcontrol = GxTourControl(**kwargs)
        self.addgxtourprimitive(gxtourcontrol)
        return gxtourcontrol

    def newgxwait(self, **kwargs):
        """Creates a new :class:`simplekml.GxWait` and adds it to the playlist.

        Accepts the same agruments as :class:`simplekml.GxWait` and returns an instance
        of :class:`simplekml.GxWait`
        """
        gxwait = GxWait(**kwargs)
        self.addgxtourprimitive(gxwait)
        return gxwait

    def __str__(self):
        buf = ["<gx:Playlist>"]
        for gxtourprimitive in self.gxtourprimitives:
            buf.append(gxtourprimitive.__str__())
        buf.append("</gx:Playlist>")
        return "".join(buf)


class GxTour(GxTourPrimitive):
    """Defines a tour.

    The arguments are the same as the properties.
    """
    def __init__(self,
                 name=None,
                 description=None,
                 gxplaylists=None):
        super(GxTourPrimitive, self).__init__()
        self._kml['name'] = name
        self._kml['description'] = description
        self.gxplaylists = []
        if gxplaylists is not None:
            self.gxplaylists += gxplaylists

    @property
    def name(self):
        """String name of the tour"""
        return self._kml['name']

    @name.setter
    def name(self, name):
        self._kml['name'] = name

    @property
    def description(self):
        """String description of the tour."""
        return self._kml['description']

    @description.setter
    def description(self, description):
        self._kml['description'] = description
        
    def newgxplaylist(self, gxtourprimitives=None):
        """Adds a :class:`simplekml.GxPlaylist` and returns it."""
        gxplaylist = GxPlaylist(gxtourprimitives)
        self.gxplaylists.append(gxplaylist)
        return gxplaylist

    def __str__(self):
        buf = ["<gx:Tour>",
               super(GxTour, self).__str__()]
        for gxplaylist in self.gxplaylists:
            buf.append(gxplaylist.__str__())
        buf.append("</gx:Tour>")
        return "".join(buf)
