# moreXML >>> eXcitinglyMORE pythonicity on top of LXML's efficiency
#
# Copyright (C) 2019 ADVA Optical Networking
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

"""
moreXML >>> eXcitinglyMORE pythonicity on top of LXML's efficiency.

Exposes the whole public :mod:`morexml` API via the :class:`morexml.XML`
factory

Uses ``zetup.toplevel`` ``module`` object wrapper for clean API exposure:

>>> import morexml
>>> morexml
<toplevel 'morexml' from '...__init__...'>

>>> [name for name in dir(morexml) if not name.startswith('_')]
['XML']

Provides ``morexml.__version__``, and ``morexml.__requires__`` list of
third-party dependencies
"""

from __future__ import absolute_import

from . import xmlpath
from .xml import XML

__import__('zetup').toplevel(__name__, (
    'XML',
))
