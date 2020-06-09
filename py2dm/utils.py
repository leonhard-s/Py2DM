"""Shared utilities used for reading and writing 2DM files."""

import contextlib
from typing import SupportsFloat

from .types import MaterialIndex


def cast_matid(value: str) -> MaterialIndex:
    """Cast a given string to a material index.

    :param value: The string version of the value to cast
    :raises TypeError: Raised if the string literal cannot be cast
    :return: The cast value of the string, either ``int`` or ``float``

    """
    with contextlib.suppress(ValueError):
        return int(value)
    with contextlib.suppress(ValueError):
        return float(value)
    raise TypeError(f'Unable to convert string literal to MATID: {value}')


def format_float(value: SupportsFloat, *, decimals: int = 8) -> str:
    """Format a node position into a string.

    This uses the format requested by 2DM: up to nine significant
    digits followed by an exponent, e.g. ::0.5 -> 5.0e-01::.

    :param value: A object that supports casting to float
    :return: The formatted string with no extra whitespace

    """
    string = f'{float(value):.{decimals}e}'  # Format
    string = f'{string.rstrip("0")}0'  # Strip all but 1 trailing zero
    return string


def format_matid(value: MaterialIndex) -> str:
    """Format a material index."""
    return str(value) if isinstance(value, int) else format_float(value)
