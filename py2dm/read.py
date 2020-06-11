"""Reader class."""

import warnings
from types import TracebackType
from typing import Callable, Dict, IO, Iterator, List, Optional, Type
from typing_extensions import Literal

from .errors import CardError, FormatError, MissingCardError
from .entities import (Element, Element2L, Element3L, Element3T, Element4Q,
                       Element6T, Element8Q, Element9Q, Node, NodeString)
from .utils import next_line

# 2DM cards that can be read and re-written without losing information
_SUPPORTED_CARDS = ['E2L', 'E3L', 'E3T', 'E4Q', 'E6T', 'E8Q', 'E9Q',
                    'ND', 'NS', 'NUM_MATERIALS_PER_ELEM']


class Reader:
    """In-place file reader for 2DM mesh files.

    This class can be used with context managers to implicitly open and
    close the mesh file. This is the recommended option when opening
    large (>50k lines) mesh files.

    Note that this will iterate over all lines in the file for most
    operations; it is advisable to read from reasonably fast storage
    when using this class to reduce overhead.

    Alternatively, you can also handle the file yourself using the
    :meth:`open` and :meth:`close` methods. In this case, the
    same caveats as with all file-like objects apply.

    :param filepath: The 2DM mesh file to read
    :type filepath: str
    """

    def __init__(self, filepath: str) -> None:
        self._file: Optional[IO[str]] = None
        self._filepath = filepath

        self._stats: Dict[str, int] = {}
        self._nodes: List[Node]
        self._elements: List[Element]
        self._node_strings: List[NodeString]

    def __enter__(self) -> 'Reader':
        self.open()
        return self

    def __exit__(self, exc_type: Optional[Type[BaseException]],
                 exc_value: Optional[BaseException],
                 exc_tb: Optional[TracebackType]) -> Literal[False]:
        if self._file is not None:
            self.close()
        return False

    def __repr__(self) -> str:
        string = (f'2DM Reader ({self._filepath})\n'
                  f'  {self.num_nodes} nodes\n'
                  f'  {self.num_elements} elements\n'
                  f'  {self.num_node_strings} node strings')
        num_materials = self.materials_per_element
        if num_materials is not None:
            plural = '' if num_materials == 1 else 's'
            string += f'\n  {num_materials} material{plural} per element'
        return string

    @property
    def elements(self) -> List[Element]:
        """Return a list of elements in the mesh.

        This will process the entire file, filtering out any elements
        and returning them as a list.

        Consider using :meth:`iter_elements` or :meth:`element` instead.
        """
        try:
            return self._elements
        except AttributeError:
            self._elements = list(self.iter_elements())
            return self._elements

    @property
    def nodes(self) -> List[Node]:
        """Return a list of nodes in the mesh.

        This will process the entire file, filtering out the nodes and
        returning them as a list.

        Consider using :meth:`iter_nodes` or :meth:`nodes` instead.
        """
        try:
            return self._nodes
        except AttributeError:
            self._nodes = list(self.iter_nodes())
            return self._nodes

    @property
    def node_strings(self) -> List[NodeString]:
        """Return a list of node strings in the mesh.

        This will process the entire file, filtering out the node
        strings and returning them as a list.

        Consider using :meth:`iter_node_strings` or :meth:`node_string`
        instead.
        """
        try:
            return self._node_strings
        except AttributeError:
            self._node_strings = list(self.iter_node_strings())
            return self._node_strings

    @property
    def num_nodes(self) -> int:
        """Return the number of nodes in the mesh."""
        if not self._stats:
            self._calculate_stats()
        return self._stats['num_nodes']

    @property
    def num_elements(self) -> int:
        """Return the number of elements in the mesh."""
        if not self._stats:
            self._calculate_stats()
        return self._stats['num_elements']

    @property
    def num_node_strings(self) -> int:
        """Return the number of node strings in the mesh."""
        if not self._stats:
            self._calculate_stats()
        return self._stats['num_nodestrings']

    @property
    def materials_per_element(self) -> Optional[int]:
        """Return the maximum number of materials for mesh elements.

        If not specified, return ``None`` instead.
        """
        if not self._stats:
            self._calculate_stats()
        nmpe = self._stats['num_materials_per_element']
        if nmpe < 0:
            return None
        return nmpe

    def _calculate_stats(self) -> None:
        self._require_open()
        assert self._file is not None
        self._stats = {'num_materials_per_element': -1}
        nodes = 0
        elements = 0
        nodestrings = 0
        for line in iter(self._file):
            if line.startswith('ND'):
                nodes += 1
            elif line.startswith('NS'):
                nodestrings += 1
            elif line.startswith('E'):
                elements += 1
            elif line.startswith('NUM_MATERIALS_PER_ELEM'):
                self._stats['num_materials_per_element'] = int(line.split()[1])
        self._stats.update({'num_nodes': nodes,
                            'num_elements': elements,
                            'num_nodestrings': nodestrings})

    def _check_header(self) -> None:
        """Process the mesh header.

        This will raise an error or warnings if either of the required
        cards are missing.

        :raises MissingCardError: Raised if a required card is mising
        :raises CardError: Raised if required cards are malformatted
        """
        self._require_open()
        assert self._file is not None
        iterator = iter(self._file)
        if next_line(iterator) != 'MESH2D':
            raise MissingCardError('Missing required card MESH2D')
        line = next_line(iterator)
        nmpe_card = 'NUM_MATERIALS_PER_ELEM'
        if not line.startswith(nmpe_card):
            raise MissingCardError(f'Missing required card {nmpe_card}')
        chunks = line.split()
        if len(chunks) != 2:
            raise CardError(nmpe_card,
                            f'Expected 1 field, got {len(chunks)-1}')
        try:
            _ = int(chunks[1])
        except ValueError:
            raise CardError(nmpe_card,
                            f'Unable to convert {chunks[1]} to an integer')

    def close(self) -> None:
        """Close the associated mesh file.

        You only have to call this yourself if you opened the file
        using :meth:`open`. The context manager will do this
        automatically.
        """
        if self._file is not None:
            self._file.close()

    def element(self, element_id: int) -> Element:
        """Return a mesh element by ID.

        :param element_id: The ID of the element to retrieve
        :raises KeyError: Raised if the given element ID does not exist
        :return: The element with the given ID
        :rtype: :class:`~py2dm.entities.Element`
        """
        try:
            element = self.elements[element_id-1]
        except IndexError as err:
            raise KeyError(f'No element with ID {element_id} found') from err
        if element.id == element_id:
            return element
        for element in self.elements:
            if element.id == element_id:
                return element
        raise KeyError(f'No element with ID of {element_id} found') from err

    def _filter_lines(self, filter_: Callable[[str], bool]) -> Iterator[str]:
        """Walk the entire file and return matching lines.

        The line will be cleaned (i.e. stripped of whitespace and
        comments) before being passed to the filter callable.

        :param filter_: A filter used to determine whether to include a
            given line
        :type filter_: Callable[[str], bool
        """
        self._require_open()
        assert self._file is not None
        self._file.seek(0)
        while True:
            line = next_line(self._file)
            if not line:
                break
            if filter_(line):
                yield line

    def iter_elements(self) -> Iterator[Element]:
        """Iterate over the elements in the mesh.

        This will read the file line-by-line, yielding the appropriate
        :class:`~py2dm.entities.Element` instance for each line.

        It is advisable to process the returned instance immediately
        before allowing the iterator to yield the next item to keep
        memory usage low. If you do require the full list of elements,
        use :attr:`elements` instead.

        :raises FormatError: Raised if the list of elements is not
            ordered
        :yield: :class:`~py2dm.entities.Element`
        :rtype: Iterator[:class:`~py2dm.entities.Element`]
        """
        def is_element(line: str) -> bool:
            element_cards = ('E2L', 'E3L', 'E3T', 'E4Q', 'E6T', 'E8Q', 'E9Q')
            return line.strip().split()[0] in element_cards

        last_id = 0
        for line in self._filter_lines(is_element):
            card = line.split(maxsplit=1)[0]
            element = element_factory(card).parse_line(line.split())
            if element.id != last_id + 1:
                if last_id == 0 and element.id == 0:
                    warnings.warn(
                        'Element indices are starting at 0 instead of 1')
                else:
                    raise FormatError('Element list is not ordered')
            last_id = element.id
            yield element

    def iter_nodes(self) -> Iterator[Node]:
        """Iterate over the nodes in the mesh.

        This will read the file line-by-line, yielding the appropriate
        :class:`~py2dm.entities.Node` instance for each line.

        It is advisable to process the returned instance immediately
        before allowing the iterator to yield the next item to keep
        memory usage low. If you do require the full list of nodes,
        use :attr:`nodes` instead.

        :raises FormatError: Raised if the list of nodes is not ordered
        :yield: :class:`~py2dm.entities.Node`
        :rtype: Iterator[:class:`~py2dm.entities.Node`]
        """
        last_id = 0
        for line in self._filter_lines(lambda s: s.startswith('ND')):
            node = Node.parse_line(line.split())
            if node.id != last_id + 1:
                if last_id == 0 and node.id == 0:
                    warnings.warn(
                        'Node indices are starting at 0 instead of 1')
                else:
                    raise FormatError('Node list is not ordered')
            last_id = node.id
            yield node

    def iter_node_strings(self) -> Iterator[NodeString]:
        """Iterate over the node strings in the mesh.

        This will read the file line-by-line, yielding the appropriate
        :class:`~py2dm.entities.NodeString` instance for each line.

        It is advisable to process the returned instance immediately
        before allowing the iterator to yield the next item to keep
        memory usage low. If you do require the full list of node
        strings, use :attr:`node_strings` instead.

        :raises FormatError: Raised if the given list of node strings
            is not ordered.
        :yield: :class:`~py2dm.entities.NodeString`
        :rtype: Iterator[:class:`~py2dm.entities.NodeString`]
        """
        node_string: Optional[NodeString] = None
        for line in self._filter_lines(lambda s: s.startswith('NS')):
            node_string, is_done = NodeString.parse_line(
                line.split(), node_string)
            yield node_string
            if is_done:
                node_string = None

    def node(self, node_id: int) -> Node:
        """Return a mesh node by ID.

        :param node_id: The ID of the node to retrieve
        :raises KeyError: Raised if the given node ID does not exist
        :return: The node with the given ID
        :rtype: :class:`~py2dm.entities.Node`
        """
        try:
            node = self.nodes[node_id-1]
        except IndexError as err:
            raise KeyError(f'No node with ID {node_id} found') from err
        if node.id == node_id:
            return node
        for node in self.nodes:
            if node.id == node_id:
                return node
        raise KeyError(f'No node with ID of {node_id} found') from err

    def open(self) -> IO[str]:
        """Open the associated mesh file.

        Note that the preferred way of accessing mesh files is via the
        context manager interface.
        If you use the manual method, it is your responsibility to call
        :meth:`close` via a try block or other catching mechanism.

        :return: The file-like object returned
        :rtype: IO[str]
        """
        self._file = open(self._filepath)
        self._check_header()
        return self._file

    def _require_open(self) -> None:
        """Utility method for requiring the current file to be open."""
        if self._file is None:
            raise RuntimeError('Reader has not been opened')


def element_factory(card: str) -> Type['Element']:
    """Return a :class:`~py2dm.entities.Element` subclass by card.

    :param card: The card to look up
    :type card: str
    :raises ValueError: Raised if the card literal is unknown
    :return: The element class matching the given tag
    :rtype: Type[:class:`~py2dm.entities.Element`]
    """
    types = (Element2L, Element3L, Element3T, Element4Q, Element6T,
             Element8Q, Element9Q)
    element_map = {e.card: e for e in types}
    try:
        return element_map[card]
    except KeyError as err:
        raise ValueError(f'Invalid card name {card}') from err
