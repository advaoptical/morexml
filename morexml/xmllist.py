# moreXML >>> eXcitinglyMORE pythonicity on top of LXML's efficiency
#
# Copyright (C) 2019 ADVA Optical Networking SE
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Define the quite ``jQuery``-like :class:`morexml.XML.List`."""

from __future__ import absolute_import

import zetup
from moretools import isinteger, qualname

import morexml
from .meta import XMLMeta

__all__ = ('List', )


class List(zetup.object):
    """
    An ordered collection of :class:`morexml.XML` (sub-)trees.

    It follows an approach quite similar to JavaScript's ``jQuery``

    :meth:`.__getattr__`, :meth:`.__getitem__`, :meth:`.__setattr__`, and
    :meth:`.__setitem__` operate on the XML attributes of all contained
    items. The getters return a tuple of the according XML attribute values
    of all the items, and the setters set the accodring XML attribute values
    of all items at once

    But also numerical index access to the contained items is allowed
    """

    # used by zetup.meta's class __repr__ instead of __module__
    __package__ = morexml

    # API: reflect exposure as nested class morexml.XML.List
    __qualname__ = "XML.List"

    #: The actual internal ``list`` container for the XML (sub-)trees.
    #:
    #: Created during  :meth:`.__init__`
    _list = None

    def __init__(self, items):
        """Initialize the internal ``list`` with XML (sub-)tree `items`."""
        self._list = list(items)

    def __iter__(self):
        """Iterate over the contained XML (sub-)trees."""
        return iter(self._list)

    def __getitem__(self, key):
        """
        Get XML (sub-)trees by index, or get their attribute values.

        >>> from morexml import XML
        >>> xmllist = XML.List([
        ...     XML['name'](attr='value'),
        ...     XML['other-name'](attr='other value'),
        ...     XML['name'](other_attr='other value'),
        ... ])

        If `key` is a single numerical index, the according (sub-)tree is
        directly returned:

        >>> xmllist[1]
        XML['other-name']:
        <other-name attr="other value"/>

        If `key` is a ``slice``, another :class:`XML.List` containing only
        the (sub-)trees of that index range is returned:

        >>> xmllist[1:3]
        XML.List: ['other-name', 'name']

        Otherwise, `key` is taken as an XML attribute name, and a ``tuple``
        containing the according attribute values of all the (sub-)trees is
        returned. If any (sub-)tree is missing that attribute, then a
        ``KeyError`` is raised:

        >>> xmllist['attr']
        Traceback (most recent call last):
        ...
        KeyError: 'attr'

        >>> xmllist[:2]['attr']
        ('value', 'other value')
        """
        if isinteger(key):
            return self._list[key]

        if isinstance(key, slice):
            return type(self)(self._list[key])

        return tuple(xml[key] for xml in self)

    def __setitem__(self, key, value):
        for xml in self:
            xml[key] = value

    def __eq__(self, other):
        """
        Check if this and `other` contain equal XML (sub-)trees.

        >>> from morexml import XML

        >>> xmllist = XML.List([
        ...     XML['pfx:name'](
        ...         xmlns={'pfx': 'urn:some:namespace'}, attr='value'),
        ...     XML['name'](attr='value'),
        ... ])

        >>> other_xmllist = XML.List([
        ...     XML['pfx:name'](
        ...         xmlns={'pfx': 'urn:some:namespace'}, attr='value'),
        ...     XML['name'](attr='other value'),
        ... ])

        >>> xmllist_with_other_xmlns = XML.List([
        ...     XML['pfx:name'](
        ...         xmlns={'pfx': 'urn:other:namespace'}, attr='value'),
        ...     XML['name'](attr='value'),
        ... ])

        >>> xmllist == other_xmllist
        False
        >>> xmllist == xmllist_with_other_xmlns
        False

        >>> other_xmllist['attr'] = 'value'
        >>> xmllist == other_xmllist
        True
        """
        return isinstance(other, List) and self._list == other._list

    def __repr__(self):
        """Create a list representation of the (sub-)trees' tag names."""
        return "{}: {!r}".format(
            qualname(type(self)), [xml.tag for xml in self])


# API: expose List as nested class morexml.XML.List
XMLMeta.List = List
