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

"""Little internal helpers useful here and there."""

from __future__ import absolute_import

__all__ = ('pyname_to_xmlname', 'xmlname_to_pyname')


def xmlname_to_pyname(name):
    """
    Convert an XML identifier name to Python style.

    By replacing hyphens with underscores:

    >>> xmlname_to_pyname('some-name')
    'some_name'
    """
    return name.replace('-', '_')


def pyname_to_xmlname(name):
    """
    Convert a Python identifier name to XML style.

    By replacing underscores with hyphens:

    >>> pyname_to_xmlname('some_name')
    'some-name'
    """
    return name.replace('_', '-')
