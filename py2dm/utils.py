"""Shared utilities used for reading and writing 2DM files."""

import contextlib
from typing import SupportsFloat

from .types import MaterialIndex


def cast_matid(value: str) -> MaterialIndex:
    """Cast a given string to a material index.

    :param value: The string version of the value to cast
    :type value: str
    :raises TypeError: Raised if the string literal cannot be cast
    :return: The cast value of the string, either ``int`` or ``float``
    :rtype: Union[int, float]
    """
    with contextlib.suppress(ValueError):
        return int(value)
    with contextlib.suppress(ValueError):
        return float(value)
    raise TypeError(f'Unable to convert string literal to MATID: {value}')


def format_float(value: SupportsFloat, *, decimals: int = 8) -> str:
    """Format a node position into a string.

    This uses the format requested by 2DM: up to nine significant
    digits followed by an exponent, e.g. ``0.5 -> 5.0e-01``.

    :param value: A object that supports casting to float
    :type value: SupportsFloat
    :param decimals: The number of decimal places to include, defaults
        to ``8``.
    :type decimals: int, optional
    :return: The formatted string with no extra whitespace
    :rtype: str
    """
    string = f'{" " if float(value) >= 0.0 else ""}{float(value):.{decimals}e}'
    return string


def format_matid(value: MaterialIndex, *, decimals: int = 8) -> str:
    """Format a material index.

    The decimals parameter will be ignored if the input value is an
    integer.

    :param value: The material index to format
    :type value: Union[int, float]
    :param decimals: The number of decimal places to include, defaults
        to ``8``.
    :type decimals: int, optional
    :return: The formatted material index
    :rtype: str
    """
    return (str(value) if isinstance(value, int)
            else format_float(value, decimals=decimals))
