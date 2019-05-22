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

"""Build the magic :class:`morexml.XML` factory."""

from __future__ import absolute_import

import zetup
from lxml.etree import tounicode  # pylint: disable=no-name-in-module
from moretools import SimpleTree, dictitems, isinteger, qualname
from six import PY2, text_type as unicode, with_metaclass

import morexml
from .meta import XMLMeta
from .xmllist import List
from .xmlns import NSLookupError

__all__ = ('XML', )


class XML(with_metaclass(XMLMeta, SimpleTree)):
    """
    The :class:`morexml.XML` factory.

    Single entry point for all XML (sub-)tree creation and data handling:

    >>> from morexml import XML

    Every instance defines an XML (sub-)tree. Its actual XML element data is
    created by first sub-classing the XML factory with an XML tag in ``name``
    or ``prefix:name`` format using ``XML['...']`` syntax, and then
    instantiating the sub-class with the XML element's attributes, which can
    be given as a dictionary and/or keyword arguments:

    >>> XML['name']({'some-attr': 'value'})
    XML['name']:
    <name some-attr="value"/>

    Note that underscores from keyword arguments are converted to hyphens:

    >>> XML['name'](other_attr='other value')
    XML['name']:
    <name other-attr="other value"/>

    The XML instance can be directly used as an iterator over all its
    ``(attribute, value)`` pairs. So you can create a ``dict`` from it:

    >>> xml = XML['name']({'some-attr': 'value'}, other_attr='other value')

    >>> list(sorted(dict(xml).items()))
    [('other-attr', 'other value'), ('some-attr', 'value')]

    Sub-elements are created using the XML factory's context manager:

    >>> with XML['name'](attr='value') as xml:
    ...     with XML['sub-name']({'sub-attr': 'sub value'}):
    ...         XML['sub-sub-name'](sub_sub_attr='sub sub value')
    ...     XML['other-name'](other_attr='other value')
    XML[...

    >>> xml
    XML['name']:
    <name attr="value">
      <sub-name sub-attr="sub value">
        <sub-sub-name sub-sub-attr="sub sub value"/>
      </sub-name>
      <other-name other-attr="other value"/>
    </name>

    For creating ``prefix:name`` tags, a namespace has to be defined for
    every prefix. If a definition for a prefix is missing, a
    :exc:`morexml.XML.NSLookupError` is raised. The ``xmlns`` argument can be
    used for defining the namespaces:

    >>> with XML['pfx:name'](
    ...         {'attr': 'value'},
    ...         xmlns={'pfx': 'urn:some:namespace'}) as xml:
    ...     XML['other:name'](
    ...         xmlns={'other': 'urn:other:namespace'},
    ...         attr='other value')
    XML[...

    >>> xml
    XML['pfx:name']:
    <pfx:name xmlns:pfx="urn:some:namespace" attr="value">
      <other:name xmlns:other="urn:other:namespace" attr="other value"/>
    </pfx:name>

    An alternative way is to use the additional :class:`morexml.XML.NS`
    context manager. Both ways can be mixed. The ``xmlns`` argument has
    higher priority:

    >>> with XML.NS(pfx='urn:some:namespace'), XML['pfx:name'](
    ...         {'attr': 'value'}) as xml:
    ...     with XML.NS({'other': 'urn:other:namespace'}):
    ...         XML['other:name'](attr='other value')
    ...         XML['pfx:sub-name'](xmlns={'pfx': 'urn:new:namespace'})
    XML[...

    >>> xml
    XML['pfx:name']:
    <pfx:name xmlns:pfx="urn:some:namespace" attr="value">
      <other:name xmlns:other="urn:other:namespace" attr="other value"/>
      <pfx:sub-name ...xmlns:pfx="urn:new:namespace".../>
    </pfx:name>
    """

    # used by zetup.meta's class __repr__ instead of __module__
    __package__ = morexml

    #: A temporary prefix store for creation of ``XML['prefix:name']`` trees.
    _prefix = None

    #: A temporary store for supporting ``{'prefix:name': 'value'}`` attributes.
    _attrs = None

    #: The internal lxml ``Element`` instance as node of this XML (sub-)tree.
    _element = None

    #: The parent XML tree instance of this sub-tree.
    _parent = None

    class sub(zetup.object):
        """
        Override for abstract ``moretools.SimpleTree.sub``.

        Gives access to the direct sub-trees of an XML (sub-)tree:

        >>> from morexml import XML

        >>> with XML['name']() as xml:
        ...     XML['sub-name']()
        ...     XML['other-name']()
        XML[...

        >>> xml.sub
        XML['name'].sub: ['sub-name', 'other-name']

        See :meth:`.__getitem__` for more details
        """

        def __init__(self, owner):
            """
            Initialize internal XML sub-tree list.

            And bind this ``sub`` instance to its :class:`morexml.XML`
            `owner` instance
            """
            self._owner = owner
            self._list = []

        def __len__(self):
            """Get the number of sub-trees."""
            return len(self._list)

        def __call__(self, *tag_filter, **xmlattr_filter):
            """
            Create a :class:`morexml.XML.List` of all matching XML sub-trees.

            The sub-trees' lxml ``Element`` node tag must be one of the given
            `tag_filter` names. If none are given, then every tag matches

            All ``attr='value'`` pairs in `xmlattr_filter` must exist in the
            sub-trees' lxml ``Element`` node

            >>> from morexml import XML

            >>> with XML['name']() as xml:
            ...     XML['sub-name'](attr='value')
            ...     XML['other-name'](attr='other value')
            ...     XML['sub-name'](attr='other value')
            XML[...

            >>> xml.sub('sub-name', attr='value')
            XML.List: ['sub-name']

            >>> xml.sub(attr='other value')
            XML.List: ['other-name', 'sub-name']
            """
            def select():
                for xml in self:
                    if (not tag_filter or xml.tag in tag_filter) and all(
                            xml[attr] == value
                            for attr, value in xmlattr_filter.items()):
                        yield xml

            return type(self._owner).List(select())

        def __iter__(self):
            """
            Iterate the XML sub-trees.

            >>> from morexml import XML

            >>> with XML['name']() as xml:
            ...     XML['sub-name']()
            ...     XML['other-name']()
            XML[...

            >>> sublist = list(iter(xml.sub))

            >>> len(sublist)
            2

            >>> sublist[0]
            XML['sub-name']:
            <sub-name/>

            >>> sublist[1]
            XML['other-name']:
            <other-name/>
            """
            return iter(self._list)

        def __getitem__(self, key):
            """
            Get XML sub-tree(s) by index or element tag.

            >>> from morexml import XML

            >>> with XML['name']() as xml:
            ...     XML['sub-name']()
            ...     XML['other-name']()
            ...     XML['sub-name']()
            XML[...

            If `key` is a single numerical index, the according sub-tree is
            directly returned:

            >>> xml.sub[1]
            XML['other-name']:
            <other-name/>

            If `key` is a ``slice``, an :class:`XML.List` containing the
            sub-trees of that index range is returned:

            >>> xml.sub[0:2]
            XML.List: ['sub-name', 'other-name']

            If `key` is a tag string, an :class:`XML.List` containing all
            matching sub-trees is returned:

            >>> xml.sub['sub-name']
            XML.List: ['sub-name', 'sub-name']
            """
            if isinteger(key):
                return self._list[key]

            if isinstance(key, slice):
                return type(self._owner).List(self._list[key])

            return type(self._owner).List(
                xml for xml in self if xml.tag == key)

        def __eq__(self, other):
            """
            Check if this and `other` contain equal XML sub-trees.

            >>> from morexml import XML

            >>> with XML.NS(pfx='urn:some:namespace'):
            ...     with XML['name']() as xml:
            ...         XML['pfx:sub-name']()
            ...         XML['other-name'](attr='value')
            XML[...

            >>> with XML.NS(pfx='urn:some:namespace'):
            ...     with XML['name']() as other_xml:
            ...         XML['pfx:sub-name']()
            ...         XML['other-name'](attr='other value')
            XML[...

            >>> with XML['name'](
            ...         xmlns={'pfx': 'urn:some:namespace'}
            ... ) as yet_another_xml:
            ...     XML['pfx:sub-name']()
            ...     XML['other-name'](attr='value')
            XML[...

            >>> with XML['name'](
            ...         xmlns={'pfx': 'urn:other:namespace'}
            ... ) as xml_with_other_xmlns:
            ...     XML['pfx:sub-name']()
            ...     XML['other-name'](attr='value')
            XML[...

            >>> xml == other_xml
            False

            >>> xml == yet_another_xml
            True

            >>> xml == xml_with_other_xmlns
            False
            """
            return isinstance(other, XML.sub) and self._list == other._list

        def __repr__(self):
            """Create a list representation of the sub-trees' tag names."""
            return "{}.sub: {!r}".format(
                qualname(type(self._owner)), [xml.tag for xml in self])

    def __init__(self, xmltext=None):
        """Create XML tree from parsing XML text."""
        raise NotImplementedError(
            "Instantiating morexml.XML from XML text is not implemented yet")

    def __copy__(self):
        # TODO: include subtree
        return XML[self.tag](attrs=self.element.attrib, xmlns=self.xmlns())

    @property
    def parent(self):
        """
        Get the parent XML (sub-)tree of this XML sub-tree.

        >>> from morexml import XML
        >>> with XML['name']() as xml:
        ...     XML['sub-name']()
        XML[...

        >>> xml.sub[0].parent is xml
        True

        Or ``None`` if this is not a sub-tree:

        >>> xml.parent
        """
        return self._parent

    @parent.setter
    def parent(self, parentxml):
        tag = self.element.tag
        xmlns = dict(parentxml.xmlns()) if parentxml is not None else {}
        xmlns.update(self.xmlns())

        if not tag.startswith('{'):
            # check if temporarily stored namespace prefix from instantiation
            # needs to be exchanged with namespace URI
            prefix = self._prefix
            if prefix is not None:
                try:
                    uri = xmlns[prefix]
                except KeyError:
                    raise NSLookupError(
                        "Unknown prefix {!r} in XML tag {!r}"
                        .format(prefix, ":".join((prefix, tag))))

                self.element.tag = "{{{}}}{}".format(uri, tag)
            self._prefix = None

        attrs = self._attrs
        if attrs is not None:
            for key, value in attrs.items():
                if not key.startswith('{') and ':' in key:
                    prefix, name = key.split(':', 1)
                    try:
                        uri = xmlns[prefix]
                    except KeyError:
                        raise NSLookupError(
                            "Unknown prefix {!r} in XML attribute {!r}"
                            .format(prefix, key))

                    key = "{{{}}}{}".format(uri, name)
                self.element.set(key, value)

        if parentxml is not None:
            self._parent = parentxml
            parentxml.sub._list.append(self)
            parentxml.element.append(self.element)

    @property
    def element(self):
        """
        Get the lxml ``Element`` of this XML (sub-)tree.

        >>> from morexml import XML
        >>> xml = XML['name']()
        >>> xml.element
        <Element name ...>
        """
        return self._element

    @property
    def tag(self):
        """
        Get the tag ``name`` or ``prefix:name`` of this XML (sub-)tree.

        >>> from morexml import XML

        >>> xml = XML['name']()
        >>> xml.tag
        'name'

        >>> xml = XML['pfx:name'](xmlns={'pfx': 'urn:some:namespace'})
        >>> xml.tag
        'pfx:name'
        """
        tag = self.element.tag
        if tag.startswith('{'):  # ==> contains namespace
            namespace, name = tag[1:].split('}')
            for key, value in dictitems(self.xmlns()):
                if value == namespace:
                    return ':'.join((key, name))

        return tag

    def xmlns(self):
        """
        Get the ``prefix: namespace`` mapping of this XML (sub-)tree.

        >>> from morexml import XML
        >>> with XML['pfx:name'](xmlns={'pfx': 'urn:some:namespace'}) as xml:
        ...     XML['other:name'](xmlns={'other': 'urn:other:namespace'})
        XML[...

        >>> xml.xmlns()
        {'pfx': 'urn:some:namespace'}

        >>> list(sorted(xml.sub[0].xmlns().items()))
        [('other', 'urn:other:namespace'), ('pfx', 'urn:some:namespace')]
        """
        return self.element.nsmap

    def __getitem__(self, xmlattr):
        """
        Get an attribute value from this XML (sub-)tree's lxml ``Element``.

        >>> from morexml import XML
        >>> xml = XML['name'](attr='value')
        >>> xml['attr']
        'value'
        """
        return self.element.attrib[xmlattr]

    def __setitem__(self, xmlattr, value):
        """
        Set an attribute `value` in this XML (sub-)tree's lxml ``Element``.

        >>> from morexml import XML
        >>> xml = XML['name'](attr='value')
        >>> xml
        XML['name']:
        <name attr="value"/>

        >>> xml['attr'] = 'other value'
        >>> xml
        XML['name']:
        <name attr="other value"/>
        """
        self.element.attrib[xmlattr] = value

    @property
    def text(self):
        """
        Get and set the inner text of this (sub-)tree's ``Element``.

        >>> from morexml import XML

        >>> with XML['name']() as xml:
        ...     XML['sub-name']().text = "Some text"
        >>> xml
        XML['name']:
        <name>
          <sub-name>Some text</sub-name>
        </name>

        >>> xml.sub[0].text
        'Some text'

        >>> xml.sub[0].text = "Other text"
        >>> xml
        XML['name']:
        <name>
          <sub-name>Other text</sub-name>
        </name>
        """
        return self.element.text

    @text.setter
    def text(self, value):
        self.element.text = unicode(value)

    def __iter__(self):
        """Iterate ``(attr, value)`` pairs of this XML tree's ``Element``."""
        return self.element.attrib.iteritems()

    def __eq__(self, other):
        """Check if all this XML tree's data equals `other` tree's data."""
        return (
            self.element.tag == other.element.tag and
            self.element.attrib == other.element.attrib and
            self.element.nsmap == other.element.nsmap and
            self.sub == other.sub)

    def __str__(self):
        """Create pretty-printed XML text from this (sub-)tree."""
        return tounicode(self.element, pretty_print=True).strip()

    if PY2:
        __unicode__ = __str__  # pragma: no cover

    def __repr__(self):
        """Create an XML text representation from this (sub-)tree."""
        return "{}:\n{}".format(qualname(type(self)), self)
