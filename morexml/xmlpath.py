from __future__ import division

import sys
from copy import copy, deepcopy

import zetup
from moretools import isdict, isinteger, qualname
from six import PY2

import morexml

from .meta import XMLMeta
from .xml import XML

__all__ = ('Path', )


class Segment(zetup.object):

    __package__ = __name__

    _tag = None

    _xmlns = None

    def __init__(self, xmlns=None):
        # TODO: message
        assert self._tag is not None
        self._xmlns = dict(xmlns) if xmlns is not None else {}

    @property
    def tag(self):
        return self._tag

    def xmlns(self):
        return dict(self._xmlns)

    def __str__(self):
        return self._tag


class Root(Segment):

    _tag = ''


class Deep(Segment):

    _tag = ''


class Element(Segment):

    _xml = None

    _index = None

    def __init__(self, index=None, xmlns=None, **xmlattrs):
        super(Element, self).__init__(xmlns=xmlns)
        # TODO: message
        assert index is None or isinteger(index)

        tag = self._tag if self._tag not in '.*' else 'X'
        self._xml = XML.root[tag](xmlns=xmlns, **xmlattrs)
        self._index = index

    def __str__(self):
        text = super(Element, self).__str__()
        xmlattrs = self._xml._element.attrib
        if xmlattrs:
            text += "[{}]".format(','.join(
                "{}='{}'".format(*item) for item in xmlattrs.items()))
        if self._index is not None:
            text += "[{}]".format(self._index)
        return text


class Any(Element):

    _tag = '*'


class Tagged(Element):

    def __init__(self, tag, index=None, xmlns=None, **xmlattrs):
        self._tag = tag
        super(Tagged, self).__init__(index=index, xmlns=xmlns, **xmlattrs)


class Meta(zetup.meta):

    def segment_to_xml(cls, segment, root=False):
        # TODO: exception type + message
        assert isinstance(segment._xml, XML)

        if root:
            return segment._xml.to_root()

        return copy(segment._xml)


class Path(zetup.object, metaclass=Meta):
    """The :class:`morexml.XML.Path` factory."""

    # used by zetup.meta's class __repr__ instead of __module__
    __package__ = morexml

    # API: reflect exposure as nested class morexml.XML.Path
    __qualname__ = "XML.Path"

    _segments = None

    def __init__(
            self, tag=None, index=None, parentpath=None, xmlns=None,
            **xmlattrs):
        _ns = {}

        nsmeta = type(XML.NS)  # pylint: disable=no-member
        if nsmeta.context_stack:
            _ns.update(nsmeta.context_stack[-1])

        if parentpath is not None:
            _ns.update(parentpath.xmlns())
        if xmlns is not None:
            _ns.update(xmlns)

        if tag is None:
            # TODO: message
            assert parentpath is None
            self._segments = (Root(xmlns=_ns), )

        else:
            if tag == '':
                # TODO: message
                assert index is None and not xmlattrs
                seg = Deep(xmlns=_ns)
            elif tag == '*':
                seg = Any(index=index, xmlns=_ns, **xmlattrs)
            else:
                seg = Tagged(tag, index=index, xmlns=_ns, **xmlattrs)

            self._segments = (
                (parentpath and deepcopy(parentpath._segments) or ()) +
                (seg, ))

    def parentpath(self):
        if len(self._segments) == 1:
            return None

        path = type(self)()
        path._segments = deepcopy(self._segments[:-1])
        return path

    def xmlns(self):
        return self._segments[-1].xmlns()

    def __div__(self, tag):
        return type(self)(tag, parentpath=self)

    __truediv__ = __div__

    def __floordiv__(self, tag):
        return self / '' / tag

    def __getitem__(self, key):
        lastseg = self._segments[-1]
        xmlattrs = dict(
            lastseg._xml._element.attrib)  # pylint: disable=no-member

        if isinteger(key):
            return type(self)(
                lastseg.tag, index=key, xmlns=lastseg.xmlns(),
                parentpath=self.parentpath(),
                **lastseg._xml._element.attrib)  # pylint: disable=no-member

        xmlattrs.update(key)
        return type(self)(
            lastseg.tag, index=lastseg._index,  # pylint: disable=no-member
            xmlns=lastseg.xmlns(), parentpath=self.parentpath(), **key)

    def __add__(self, other):
        if not isinstance(other, Path):
            raise TypeError(
                "Can only add {!r} instances to {!r}, not {!r}"
                .format(Path, type(self), type(other)))

        # TODO: message
        assert not isinstance(other._segments[0], Root)

        path = Path()
        path._segments = (
            deepcopy(self._segments) + deepcopy(other._segments))
        return path

    def __str__(self):
        return '/'.join(str(seg) for seg in self._segments)

    def to_xml(self, root=False):
        # TODO: exception type + message
        assert all(isinstance(seg, Tagged) for seg in self._segments)

        cls = type(self)

        def segments_to_xml(segments, _root=False):
            with cls.segment_to_xml(segments[0], root=_root) as xml:
                if len(segments) > 1:
                    segments_to_xml(segments[1:])
            return xml

        return segments_to_xml(self._segments, _root=root)

    def to_xpath(self):
        # TODO: message
        assert all(isinstance(seg, Tagged) for seg in self._segments)

        def segment_to_xpath(segment):
            tag = segment.tag
            if ':' in tag:
                prefix, tag = tag.split(':')
                uri = segment.xmlns()[prefix]
            else:
                uri = None

            filters = "name()='{}'".format(tag)
            if uri is not None:
                filters += " and namespace-uri()='{}'".format(uri)
            return "*[{}]".format(filters)

        return '/'.join(map(segment_to_xpath, self._segments))

    def __repr__(self):
        """Create an XPath-style representation."""
        return "{}: {}".format(qualname(type(self)), self)


# API: expose Path as nested class morexml.XML.Path
XMLMeta.Path = Path
