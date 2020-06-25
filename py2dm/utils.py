"""Shared utilities used for reading and writing 2DM files."""

import contextlib
from typing import Iterator, SupportsFloat

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


def clean_line(line: str) -> str:
    """Return a cleaned version of the input line's contents.

    This means removing any leading and trailing whitespace, as well as
    discarding any trailing inline comments.

    :param line: The input line to process
    :type line: str
    :return: The cleaned contents of the line
    :rtype: str
    """
    data = line.split('#', 1)[0]
    return data.strip()


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


def next_line(iterator: Iterator[str]) -> str:
    """Return the next valid 2DM line.

    This will jump over any empty lines, as well as strip out any
    comments.

    This will return an empty string only if the iterator is exhausted
    while attempting to return a valid line.

    :param iterator: The iterator to use for traversal of the file
    :type line: Iterator [str]
    :return: The next non-empty line
    :rtype: str
    """
    while True:
        try:
            line = next(iterator)
        except StopIteration:
            return ''
        line = clean_line(line)
        if line:
            return line
