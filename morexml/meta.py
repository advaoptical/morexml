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

"""Build the magic meta foundation for the :class:`morexml.XML` factory."""

from __future__ import absolute_import

from lxml.etree import Element  # pylint: disable=no-name-in-module
from moretools import SimpleTree, cached, getfunc, qualname
from six import text_type as unicode

from .tools import pyname_to_xmlname

__all__ = ('XMLMeta', )


class XMLMeta(type(SimpleTree)):
    """
    Metaclass for :class:`moretools.XML` factory.

    Provides creation of XML sub-classes bound to an XML tag via
    :meth:`.__getitem__`
    """

    #: The tag name of an ``XML['name']`` or ``XML['prefix:name']`` class
    _tag = None

    @cached
    def __getitem__(cls, tag):  # pylint: disable=no-self-argument
        """
        Create derived :class:`morexml.XML` factory classes with an XML tag.

        >>> from morexml import XML
        >>> XML['name']
        <class "morexml.XML['name']">

        Then, by instantiation, an XML element with that tag can be created:

        >>> XML['name'](attr='value')
        XML['name']:
        <name attr="value"/>

        The created classes are cached:

        >>> XML['name'] is XML['name']
        True
        """
        if cls._tag is not None:
            raise TypeError(
                "{!r} already has tag {!r}".format(cls, cls._tag))

        class taggedcls(cls):
            """Sub-class of :class:`morexml.XML` factory for XML tag {!r}."""

            __module__ = cls.__module__

            _tag = tag

            def __init__(self, attrs=None, xmlns=None, **kwattrs):
                """
                Create an XML <{tag}> element.

                >>> from morexml import XML
                >>> XML[{tag!r}](some_attr='value')
                XML[{tag!r}]:
                <{tag} some-attr="value"/>
                """
                tag = type(self)._tag
                if not tag.startswith('{') and ':' in tag:
                    # HACK: lxml Element creation doesn't support prefix:name
                    # tag scheme ==> temporarily store prefix and prepend
                    # {URI} later to Element tag
                    self._prefix, name = tag.split(':', 1)
                else:
                    name = tag

                # HACK: lxml Element creation also doesn't support prefix:name
                # scheme for attributes ==> also temporarily store all
                # attributes and exchange prefixes with {URI}s later before
                # finally adding attributes to lxml Element
                self._attrs = dict(attrs) if attrs is not None else {}
                self._attrs.update({
                    pyname_to_xmlname(attr): unicode(value)
                    for attr, value in kwattrs.items()})

                nsmeta = type(type(cls).NS)  # pylint: disable=no-member
                if nsmeta.context_stack:
                    nsctx = dict(nsmeta.context_stack[-1])
                    if xmlns is not None:
                        nsctx.update(xmlns)
                    xmlns = nsctx

                self._element = Element(name, nsmap=xmlns)
                # call super().__init__ last because self._element must exist
                # to make parent assignment via moretools.SimpleTree.__init__
                # work
                super(cls, self).__init__()  # pylint: disable=bad-super-call

        taggedcls.__name__ = tag
        taggedcls.__qualname__ = "{}[{!r}]".format(qualname(cls), tag)
        taggedcls.__doc__ = taggedcls.__doc__.format(tag)
        __init__ = getfunc(taggedcls.__init__)
        __init__.__doc__ = __init__.__doc__.format(tag=tag)
        return taggedcls
