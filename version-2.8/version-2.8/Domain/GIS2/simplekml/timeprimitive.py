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


class TimePrimitive(Kmlable):
    """Abstract class extended by all time primitive types.

    .. note::
      Not to be used directly.
    """
    _id = 0

    def __init__(self):
        super(TimePrimitive, self).__init__()
        self._id = "time_{0}".format(TimePrimitive._id)
        TimePrimitive._id += 1

    @property
    def id(self):
        """The id string."""
        return self._id


class TimeSpan(TimePrimitive):
    """Represents an extent in time bounded by begin and end dates.

    The arguments are the same as the properties.
    """
    def __init__(self, begin=None, end=None):
        super(TimeSpan, self).__init__()
        self._kml["begin"] = begin
        self._kml["end"] = end

    @property
    def begin(self):
        """The starting time, accepts string."""
        return self._kml['begin']

    @begin.setter
    def begin(self, begin):
        self._kml['begin'] = begin

    @property
    def end(self):
        """The ending time, accepts string."""
        return self._kml['end']

    @end.setter
    def end(self, end):
        self._kml['end'] = end

    def __str__(self):
        buf = ['<TimeSpan id="{0}">'.format(self._id),
               super(TimeSpan, self).__str__(),
               '</TimeSpan>'.format(self._id)]
        return "".join(buf)


class GxTimeSpan(TimeSpan):
    """A copy of the :class:`simplekml.TimeSpan` element, in the extension namespace.

    Args:
      * *same as properties*
      * *all other args same as* :class:`simplekml.TimeSpan`
    """
    def __init__(self, **kwargs):
        super(GxTimeSpan, self).__init__(**kwargs)

    def __str__(self):
        buf = ['<gx:TimeSpan id="{0}">'.format(self._id),
               super(TimeSpan, self).__str__(),
               '</gx:TimeSpan>'.format(self._id)]
        return "".join(buf)


class TimeStamp(TimePrimitive):
    """Represents a single moment in time.

    The arguments are the same as the properties.
    """

    def __init__(self, when=None):

        super(TimeStamp, self).__init__()
        self._kml["when"] = when

    @property
    def when(self):
        """A moment in time, accepts string."""
        return self._kml['when']

    @when.setter
    def when(self, when):
        self._kml['when'] = when

    def __str__(self):
        buf = ['<TimeStamp id="{0}">'.format(self._id),
               super(TimeStamp, self).__str__(),
               '</TimeStamp>'.format(self._id)]
        return "".join(buf)


class GxTimeStamp(TimeStamp):
    """A copy of the :class:`simplekml.TimeStamp` element, in the extension namespace.

    Args:
      * *same as properties*
      * *all other args same as* :class:`simplekml.TimeStamp`
    """
    def __init__(self, **kwargs):
        """
        Creates a gx:timestamp element.

        Keyword Arguments:
        when (string) -- a moment in time (default None)

        """
        super(GxTimeStamp, self).__init__(**kwargs)

    def __str__(self):
        buf = ['<gx:TimeStamp id="{0}">'.format(self._id),
               super(TimeStamp, self).__str__(),
               '</gx:TimeStamp>'.format(self._id)]
        return "".join(buf)
