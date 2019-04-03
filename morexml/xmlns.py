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

"""Namespace management for the :class:`morexml.XML` factory."""

from __future__ import absolute_import

from moretools import dictitems, simpledict, qualname
from six import reraise, with_metaclass
import zetup

import morexml
from .meta import XMLMeta
from .tools import pyname_to_xmlname, xmlname_to_pyname

__all__ = ('NS', 'NSLookupError')


class NSLookupError(with_metaclass(zetup.meta, LookupError)):
    """An XML namespace prefix is not defined during tree creation."""

    # API: used by zetup.meta's class __repr__ instead of __module__
    __package__ = morexml

    # API: reflect exposure as nested exc class morexml.XML.NSLookupError
    __qualname__ = 'XML.NSLookupError'


# API: expose NSLookupError as nested exc class morexml.XML.NSLookupError
XMLMeta.NSLookupError = NSLookupError


NSDict = simpledict(
    'NSDict', key_to_attr=xmlname_to_pyname, attr_to_key=pyname_to_xmlname)


class NSMeta(type(NSDict.frozen)):
    """
    Metaclass for :class:`morexml.XML.NS` namespace factory.

    Holds the namespace context manager stack
    """

    #: The stack of active :class:`morexml.XML.NS` context managers.
    context_stack = []


class NS(with_metaclass(  # pylint: disable=invalid-metaclass
        NSMeta, NSDict.frozen)):
    """
    The :class:`morexml.XML.NS` namespace factory.

    A ``prefix: namespace`` mapping providing a context manager for applying
    namespace definitions to the :class:`morexml.XML` factory. Note that
    underscores in keyword arguments used for initialization are converted to
    hyphens for XML:

    >>> from morexml import XML

    >>> with XML.NS({'pfx': 'urn:some:namespace'}), XML['pfx:name'](
    ...         {'attr': 'value'}) as xml:
    ...     with XML.NS(other_pfx='urn:other:namespace'):
    ...         XML['other-pfx:name']()
    XML[...

    >>> xml
    XML['pfx:name']:
    <pfx:name xmlns:pfx="urn:some:namespace" attr="value">
      <other-pfx:name xmlns:other-pfx="urn:other:namespace"/>
    </pfx:name>
    """

    # API: used by zetup.meta's class __repr__ instead of __module__
    __package__ = morexml.__name__

    # API: reflect exposure as nested class morexml.XML.NS
    __qualname__ = 'XML.NS'

    def __init__(self, mapping=None, **items):
        """
        Initialize with ``prefix: namespace`` `mapping` and keyword `items`.

        Keyword `items` have higher priority

        When initialized inside the context code block of another
        :class:`morexml.XML.NS` factory instance, then the mapping items from
        that namespace context will be added (with lower priority):

        >>> from morexml import XML

        >>> with XML.NS({'pfx': 'urn:some:namespace'}):
        ...     with XML.NS(other_pfx='urn:other:namespace') as subns:
        ...         pass

        >>> from moretools import dictitems

        >>> list(sorted(dictitems(subns)))
        [('other-pfx', 'urn:other:namespace'), ('pfx', 'urn:some:namespace')]
        """
        mapping = dict(mapping) if mapping is not None else {}
        for key, value in items.items():
            mapping[pyname_to_xmlname(key)] = value
        meta = type(type(self))
        if meta.context_stack:
            for key, value in dictitems(meta.context_stack[-1]):
                mapping.setdefault(key, value)
        super(NS, self).__init__(mapping)

    def __enter__(self):
        """
        Entry point of the namespace context manager.

        Puts this namespace mapping on the top of the namespace context stack
        """
        meta = type(type(self))
        meta.context_stack.append(self)
        return self

    def __exit__(self, *exc_info):
        """
        Exit point of the namespace context manager.

        Pops this namespace mapping from the top of the context stack and
        then reraises any exception that occured within the context code
        block
        """
        meta = type(type(self))
        stack = meta.context_stack
        assert stack and stack[-1] is self, (
            "Corrupted .context_stack of {!r}".format(meta))

        meta.context_stack.pop(-1)
        if exc_info[0] is not None:
            reraise(*exc_info)

    def __repr__(self):
        """Create an initialization-code-style representation."""
        return "{}({!r})".format(qualname(type(self)), self.__dict__)


# API: expose NS as nested class morexml.XML.NS
XMLMeta.NS = NS
