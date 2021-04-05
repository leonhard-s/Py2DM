"""The Py2DM module provides read and write support for 2DM mesh files.

Visit the project repository at https://github.com/leonhard-s/Py2DM for
detailed usage instructions and to provide feedback.

For additional information on the 2DM format, refer to the 2DM file
format specification at
https://www.xmswiki.com/wiki/SMS:2D_Mesh_Files_*.2dm.

"""

from . import errors, utils
from ._entities import (Element, Element2L, Element3L, Element3T, Element4Q,
                        Element6T, Element8Q, Element9Q, LinearElement, Node,
                        NodeString, QuadrilateralElement, TriangularElement)
from ._read import Reader, ReaderBase
from ._write import Writer

__all__ = [
    'Element',
    'Element2L',
    'Element3L',
    'Element3T',
    'Element4Q',
    'Element6T',
    'Element8Q',
    'Element9Q',
    'errors',
    'LinearElement',
    'Node',
    'NodeString',
    'QuadrilateralElement',
    'Reader',
    'ReaderBase',
    'TriangularElement',
    'utils',
    'Writer'
]

__version__ = '0.2.0'
