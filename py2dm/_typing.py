"""Type hinting support module."""

try:
    from typing import Literal
except ImportError:  # pragma: no cover
    # Required for compatibilty with Python 3.7 (used in QGIS 3)
    from typing_extensions import Literal  # type: ignore

__all__ = [
    'Literal'
]
