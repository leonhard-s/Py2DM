"""Implementation of the mesh reading interface.

This module defines the :class:`py2dm.Reader` interface, as well as
subclasses implementing this interface to provide variations optimised
for specific use-cases. Refer to the :class:`py2dm.ReadMode` enumerator
for details.

"""

from types import TracebackType
from typing import Any, Iterator, List, Optional, Tuple, Type

from .entities import Element, Node, NodeString

try:
    from typing import Literal
except ModuleNotFoundError as err:  # pragma: no cover
    # Required for compatibilty with Python 3.7 (used in QGIS 3)
    try:
        from typing_extensions import Literal  # type: ignore
    except ModuleNotFoundError:
        raise err from err

__all__ = [
    'Reader'
]


# A list of all tags that are considered elements
_ELEMENTS = [
    'E2L',
    'E3L',
    'E3T',
    'E6T',
    'E4Q',
    'E8Q',
    'E9Q'
]


class Reader:
    """Reader interface specification and class factory."""

    def __init__(self, filepath: str, **kwargs: Any) -> None:
        """Initialise the mesh reader.

        This opens the underlying file and preloads metadata for the
        mesh.

        Arguments:
            filepath: The path of the mesh file to read.

        """
        self._filepath = filepath
        # Load all searchable entities into memory
        self._cache_nodes: List[Node] = [
            Node.parse_line(l) for l in self._filter_lines('ND')]
        self._cache_elements: List[Element] = [
            _element_factory(l[0]).parse_line(l)
            for l in self._filter_lines(*_ELEMENTS)]
        # Node strings are special and require multiline parsing
        self._cache_node_strings: List[NodeString] = []
        with open(self._filepath, 'r') as file_:
            for line in iter(file_):
                if line.startswith('NS'):
                    node_string, is_done = NodeString.parse_line(line.split())
                    if is_done:
                        self._cache_node_strings.append(node_string)

    def __enter__(self) -> 'Reader':
        """Enter the context manager.

        This has no side effects and does not alter the class in any
        way.

        """
        return self

    def __exit__(self, exc_type: Optional[Type[BaseException]],
                 exc_value: Optional[BaseException],
                 exc_tb: Optional[TracebackType]) -> Literal[False]:
        """Exit the context manager.

        This closes the underlying mesh file if it is still open.

        This will never suppress any exceptions.

        """
        _ = exc_type, exc_value, exc_tb
        self.close()
        return False

    def __str__(self) -> str:
        return ('Py2DM Reader\n'
                f'\t{self.num_nodes} nodes\n'
                f'\t{self.num_elements} elements\n'
                f'\t{self.num_node_strings} node strings')

    @property
    def bbox(self) -> Tuple[float, float, float, float]:
        """Alias for :attr:`Reader.extent`."""
        return self.extent

    @property
    def extent(self) -> Tuple[float, float, float, float]:
        """Return the extents of the mesh as a tuple of four floats.

        The tuple is structured as ``[minX, maxX, minY, maxY]``.

        If the given mesh is empty, the returned tuple will consist of
        four ``nan`` (not a number) values.

        .. note::

            The 2DM format does not cache the mesh extents. The first
            time this property is accessed, all nodes are checked to
            find the extreme values, which can take considerable time
            for very large meshes (i.e. ones with millions of nodes).

            Any successive calls will re-use this value.

        """
        iterator = iter(self.iter_nodes())
        # Get initial node for base values
        try:
            node = next(iterator)
        except StopIteration:
            # Mesh is empty/contains no nodes
            return (float('nan'),) * 4
        minX, maxX, minY, maxY = (*node.x, *node.y)
        # Update value
        for node in self.iter_nodes():
            if node.x < minX:
                minX = node.x
            elif node.x > maxX:
                maxX = node.x
            if node.y < minY:
                minY = node.y
            elif node.y > maxY:
                maxY = node.y
        return minX, maxX, minY, maxY

    @property
    def elements(self) -> Iterator[Element]:
        """Iterate over the mesh elements.

        This is synonymous to calling
        :meth:`py2dm.Reader.iter_elements()` with default arguments.

        If you prefer a list of elements, pass this iterator into the
        ``list()`` constructor instead:

        .. code-block:: python

            with py2dm.Reader('mesh.2dm') as mesh:
                elements = list(mesh.elements)

        """
        return self.iter_elements()

    @property
    def nodes(self) -> Iterator[Node]:
        """Iterate over the mesh nodes.

        This is synonymous to calling :meth:`py2dm.Reader.iter_nodes()`
        with default arguments.

        If you prefer a list of nodes, pass this iterator into the
        ``list()`` constructor instead:

        .. code-block:: python

            with py2dm.Reader('mesh.2dm') as mesh:
                nodes = list(mesh.nodes)

        """
        return self.iter_nodes()

    @property
    def node_strings(self) -> Iterator[NodeString]:
        """Iterate over the node strings in the mesh.

        This is synonymous to calling
        :meth:`py2dm.Reader.iter_node_strings()` with default
        arguments.

        If you prefer a list of node strings instead, pass this
        iterator into the ``list()`` constructor instead:

        .. code-block:: python

            with py2dm.Reader('mesh.2dm') as mesh:
                nodes = list(mesh.nodes)

        """
        return self.iter_node_strings()

    @property
    def num_elements(self) -> int:
        """Return the number of elements in the mesh."""
        return len(self._cache_elements)

    @property
    def num_nodes(self) -> int:
        """Return the number of nodes in the mesh."""
        return len(self._cache_nodes)

    @property
    def num_node_strings(self) -> int:
        """Return the number of node strings in the mesh."""
        return len(self._cache_node_strings)

    def close(self) -> None:
        """Close the mesh reader.

        This closes the underlying text file and discards any cached
        objects or metadata. The instance will become unusable after
        this call.

        .. note::

            This method is called automatically when using the class
            via the context manager.

        """

    def element(self, id_: int) -> Element:
        """Return a mesh element by its unique ID.

        Arguments:
            id_: The ID of the element to return.

        Raises:
            KeyError: Raised if the given `id_` is invalid

        Returns:
            The element matching the given ID.

        """
        # Conform ID to always be one-indexed
        id_conf = id_+1 if self._zero_index else id_
        # Check ID range
        if not 1 <= id_conf <= self.num_elements:
            id_min = 0 if self._zero_index else 1
            id_max = (
                self.num_elements-1 if self._zero_index else self.num_elements)
            raise KeyError(f'Invalid element ID {id_}, element IDs must be '
                           f'between {id_min} and {id_max}')
        if self._lazy:
            # TODO: Check if element is contained in cached blocks
            # TODO: Get block containing this element
            # TODO: Resolve and add block to cache
            # TODO: Return element
            raise NotImplementedError()
        else:
            return self._cache_elements[id_conf-1]

    def node(self, id_: int) -> Node:
        """Return a mesh node by its unique ID.

        Arguments:
            id_: The ID of the node to return.

        Raises:
            KeyError: Raised if the given `id_` is invalid

        Returns:
            The node matching the given ID.

        """
        # Conform ID to alwasy be one-indexed
        id_conf = id_+1 if self._zero_index else id_
        # Check ID range
        if not 1 <= id_conf <= self.num_nodes:
            id_min = 0 if self._zero_index else 1
            id_max = self.num_nodes-1 if self._zero_index else self.num_nodes
            raise KeyError(f'Invalid node ID {id_}, node IDs must be between '
                           f'{id_min} and {id_max}')
        if self._lazy:
            # TODO: Check if node is contained in a cached block
            # TODO: Get block containing this node
            # TODO: Resolve and add block to cache
            # TODO: Return element
            raise NotImplementedError()
        else:
            return self._cache_nodes[id_conf-1]

    def node_string(self, name: str) -> NodeString:
        """Return a node string by its unique name.

        This is only available if the node strings define a name. For
        meshes whose node strings are not named, convert
        :meth:`Reader.iter_node_strings` to a :class:`list` and access
        the node strings by index.

        .. code-block:: python3

            with py2dm.Reader('my-mesh.2dm') as mesh:
                node_strings = list(mesh.iter_node_strings())
                node_string_two = node_strings[1]

        :param name: Unique name of the node string
        :raises KeyError: Raised if no node string of the given name
            exists
        :return: The node string of the given name, if any.
        """
        for node_string in self.iter_node_strings():
            if node_string.name == name:
                return node_string
        raise KeyError(f'Node string \'{name}\' not found')

    def iter_elements(self, start: int = 1,
                      end: int = -1) -> Iterator[Element]:
        """Iterate over the mesh elements.

        Arguments:
            start (optional): The starting element ID. Must be greater
                than or equal to ``1``. Defaults to ``1``.

            end (optional): The end element ID (exclusive). If
                negative, continues until the list of elements is
                exhausted. Defaults to ``-1``.

        Raises:
            IndexError: Raised if the `start` ID is less than ``1``, or
                if the `end` ID is less than or equal to the `start`
                ID, or if either of the IDs exceeds the number of
                elements in the mesh.

        Yields:
            Mesh elements from the given range of IDs.

        """
        if start < 1:
            raise IndexError(f'Start element ID must be greater than or equal '
                             f'to 1 ({start})')
        if 0 < end <= start:
            raise IndexError('End element ID must be greater than than start '
                             f'element ID ({start}>={end})')
        try:
            return iter(self._cache_elements[start-1:end-1])
        except IndexError as err:
            raise IndexError(f'Invalid end element ID {end}; mesh only has '
                             f'{len(self._cache_elements)} elements') from err

    def iter_nodes(self, start: int = 1, end: int = -1) -> Iterator[Node]:
        """Iterate over the mesh elements.

        If the `end` ID is less than the `start` ID, the IDs will be
        traversed in reverse order.

        Arguments:
            start (optional): The starting node ID. Must be greater
                than or equal to ``1``. Defaults to ``1``.

            end (optional): The end node ID (exclusive). If negative,
                continues until the list of nodes is exhausted.
                Defaults to ``-1``.

        Raises:
            IndexError: Raised if the `start` ID is less than ``1``, or
                if the `end` ID is less than or equal to the `start`
                ID, or if either of the IDs exceeds the number of
                nodes in the mesh.

        Yields:
            Mesh nodes from the given range of IDs.

        """
        if start < 1:
            raise IndexError(f'Start node ID must be greater than or equal '
                             f'to 1 ({start})')
        if 0 < end <= start:
            raise IndexError('End node ID must be greater than than start '
                             f'node ID ({start}>={end})')
        try:
            if end < 0:
                return iter(self._cache_nodes[start-1:])
            return iter(self._cache_nodes[start-1:end-1])
        except IndexError as err:
            raise IndexError(f'Invalid end node ID {end}; mesh only has '
                             f'{len(self._cache_nodes)} node') from err

    def iter_node_strings(self) -> Iterator[NodeString]:
        """Iterate over the mesh node strings.

        Yields:
            Mesh node strings in order of definition.

        """
        return iter(self._cache_node_strings)

    def _filter_lines(self, card: str, *args: str) -> Iterator[List[str]]:
        """Filter the mesh's lines by their card.

        This iterates over the entire file, returning only those lines
        matching the given card.

        This also filters out any comments appended to the end of a
        line.

        Arguments:
            card: The card to match lines against.

            *args: Additional cards whos lines will be returned.

        Yields:
            A list of whitespace-separated words of the matching line.

        """
        valid_cards = card, *args
        with open(self._filepath, 'r') as file_:
            for line in file_:
                if line.startswith(valid_cards):
                    line, *_ = line.split('#', maxsplit=1)
                    yield line.split()


def _element_factory(card: str) -> Type[Element]:
    """Return a :class:`py2dm.Element` subclass by card.

    Arguments:
        card: The card to look up

    Raises:
        ValueError: Raised if the given card doesn't match any subclass

    Returns:
        The element class mataching the given tag

    """
    for element_group in Element.__subclasses__():
        for subclass in element_group.__subclasses__():
            if subclass.card == card:
                return subclass
    raise NotImplementedError(f'Unsupported card name \'{card}\'')
