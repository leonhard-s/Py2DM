"""Python implementation of the 2DM card parser."""

from typing import List, Tuple, Union

from .errors import CardError, FormatError


def parse_element(line: str, allow_float_matid: bool = True,
                  allow_zero_index: bool = False
                  ) -> Tuple[int, Tuple[int, ...], Tuple[Union[float, int]]]:
    """Parse a string into an element.

    This converts a valid element definition string into a tuple that
    can be used to instantiate the corresponding
    :class:`py2dm.Element` subclass.
    """
    # Parse line
    chunks = line.split('#', maxsplit=1)[0].split()
    # Length (generic)
    if len(chunks) < 4:
        raise CardError('Element definitions require at least 3 fields '
                        f'(id, node_1, node_2), got {len(chunks)-1}')
    # 2DM card
    card = chunks[0]
    if not _card_is_element(card):
        raise CardError(f'Invalid element card "{card}"')
    # Length (card known)
    num_nodes = _nodes_per_element(card)
    assert num_nodes > 0
    if len(chunks) < num_nodes + 2:
        raise CardError(
            f'{card} element definition requires at least {num_nodes-1} '
            f'fields (id, node_1, ..., node_{num_nodes-1}), got {len(chunks)-1}')
    # Element ID
    id_ = int(chunks[1])
    if id_ <= 0 and not (id_ == 0 and allow_zero_index):
        raise FormatError(f'Invalid element ID: {id_}')
    # Node IDs
    nodes: List[int] = []
    for node_str in chunks[2:num_nodes+2]:
        node_id = int(node_str)
        if node_id < 0 and not (node_id == 0 and allow_zero_index):
            raise FormatError(f'Invalid node ID: {node_id}')
        nodes.append(node_id)
    # Material IDs
    materials: List[Union[int, float]] = []
    for mat_str in chunks[num_nodes+2:]:
        mat_id: Union[int, float]
        try:
            mat_id = int(mat_str)
        except ValueError as err:
            if not allow_float_matid:
                raise err from err
            mat_id = float(mat_str)
        materials.append(mat_id)
    return id_, tuple(nodes), tuple(materials)


def parse_node(line: str, allow_zero_index: bool = False
               ) -> Tuple[int, float, float, float]:
    """Parse a string into a node.

    This converts a valid node definition string into a tuple that can
    be used to isntantiate the corresponding :class:`py2dm.Node`
    object.
    """
    # Parse line
    chunks = line.split('#', maxsplit=1)[0].split()
    # Length
    if len(chunks) < 5:
        raise CardError(f'Node definitions require at least 4 fields '
                        f'(id, x, y, z), got {len(chunks)-1}')
    # 2DM card
    card = chunks[0]
    if card != "ND":
        raise CardError(f'Invalid node card "{card}"')
    # Node ID
    id_ = int(chunks[1])
    if id_ <= 0 and not (id_ == 0 and allow_zero_index):
        raise FormatError(f'Invalid node ID: {id_}')
    # Coordinates
    pos_x, pos_y, pos_z = tuple((float(s) for s in chunks[2:5]))
    # TODO: Warn about unused fields
    return id_, pos_x, pos_y, pos_z


def parse_node_string(line: str,   allow_zero_index: bool = False,
                      nodes: List[int] = None) -> Tuple[List[int], bool, str]:
    """Parse a string into a node string.

    This converts a valid node string definition string into a tuple
    that can be used to instantiate the corresponding
    :class:`py2dm.NodeString`.

    As nodestring can span multiple lines, the node string should only
    be created once the `done` flag (second entry in the returned
    tuple) is set to True.
    """
    # Set default value
    if nodes is None:
        nodes = []
    # Parse line
    chunks = line.split('#', maxsplit=1)[0].split()
    # Length
    if len(chunks) < 2:
        raise CardError('Node string definitions require at least 1 field '
                        f'(node_id), got {len(chunks)-1}')
    # 2DM card
    card = chunks[0]
    if card != 'NS':
        raise CardError(f'Invalid node string card "{card}"')
    # Node IDs
    is_done: bool = False
    name = ''
    for index, node_str in enumerate(chunks[1:]):
        node_id = int(node_str)
        if node_id == 0 and not allow_zero_index:
            raise FormatError(f'Invalid node ID: {node_id}')
        if node_id < 0:
            # End of node string
            is_done = True
            nodes.append(abs(node_id))
            # Check final identifier
            if index+1 < len(chunks):
                name = chunks[index+1]
            break
        nodes.append(node_id)
    return nodes, is_done, name


def _card_is_element(card: str) -> bool:
    return card in ('E2L', 'E3L', 'E3T', 'E4Q', 'E6T', 'E8Q', 'E9Q')


def _nodes_per_element(card: str) -> int:
    if card == 'E2L':
        return 2
    if card in ('E3L', 'E3T'):
        return 3
    if card == 'E4Q':
        return 4
    if card == 'E6T':
        return 6
    if card == 'E8Q':
        return 8
    if card == 'E9Q':
        return 9
    return -1
