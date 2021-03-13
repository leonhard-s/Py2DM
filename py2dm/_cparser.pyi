from typing import List, Tuple, Union


def parse_element(line: str, allow_float_matid: bool = ...,
                  allow_zero_index: bool = ...
                  ) -> Tuple[int, Tuple[int, ...], Tuple[Union[int, float]]]:
    """Parse a 2DM element definition."""
    ...


def parse_node(line: str, allow_zero_index: bool = ...
               ) -> Tuple[int, float, float, float]:
    """Parse a 2DM node definition."""
    ...


def parse_node_string(line: str, allow_zero_index: bool = ...,
                      nodes: List[int] = ...) -> Tuple[List[int], bool, str]:
    """Parse a 2DM node string definition."""
    ...
