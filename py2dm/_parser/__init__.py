"""Py2DM parser submodule."""

from ._pyparser import scan_metadata

implementation: str = 'unknown'

try:
    from ._cparser import parse_element, parse_node, parse_node_string
except ImportError:  # pragma: no cover
    from ._pyparser import parse_element, parse_node, parse_node_string
    implementation = 'python'
else:
    implementation = 'c'


__all__ = [
    'implementation',
    'parse_element',
    'parse_node',
    'parse_node_string',
    'scan_metadata',
]
