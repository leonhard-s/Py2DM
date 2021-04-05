"""Py2DM parser submodule."""

import platform
import warnings

from ._pyparser import scan_metadata

try:
    from ._cparser import parse_element, parse_node, parse_node_string
except ImportError:  # pragma: no cover
    from ._pyparser import parse_element, parse_node, parse_node_string
    if platform.python_implementation() == 'CPython':
        warnings.warn('C parser not found, using Python implementation')

__all__ = [
    'parse_element',
    'parse_node',
    'parse_node_string',
    'scan_metadata'
]
