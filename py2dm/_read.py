"""Implementation of the mesh reading interface.

This module defines the :class:`py2dm.Reader` interface, as well as
subclasses implementing this interface to provide variations optimised
for specific use-cases. Refer to the :class:`py2dm.ReadMode` enumerator
for details.

"""

from types import TracebackType
from typing import Any, Iterator, List, NamedTuple, Optional, Tuple, Type

from ._entities import Element, Node, NodeString
from .errors import FormatError, ReadError

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


class _Metadata(NamedTuple):
    """Container for mesh metadata."""

    num_nodes: int
    num_elements: int
    num_node_strings: int
    name: Optional[str] = None
    num_materials_per_elem: Optional[int] = None


class Reader:
    """Py2DM reader class used to parse and validate 2DM files.

    This class wraps the underlying mesh file and provides getters and
    iterators to access its contents. The preferred way to use it is
    via the context manger interface. This ensures the underlying file
    is closed properly after access.

    Py2DM supports two different read modes depending on the use case.
    By default, the entire file is parsed and read into memory upon
    initialisation of the reader. This is the faster option for most
    use cases, but may cause issues with very large meshes with
    millions of elements or multiple Gigabytes in file size.

    Alternatively, passing `lazy=True` into the :class:`Reader` class's
    initialiser will switch to a different implementation. In this
    mode, the file is parsed once to provide metadata like element or
    node count, but nodes and elements will not be read into memory to
    save space in exchange for higher access latency.

    In lazy read mode, file iterators are used for sequential access
    like :meth:`Reader.iter_nodes`, while random ID-based getters like
    :meth:`Reader.node` use a binary search to identify the requested
    element instead.

    For more information on the lazy read mode, refer to the `Py2DM
    documentation <https://py2dm.readthedocs.io/en/latest/>`_.
    """

    def __init__(self, filepath: str, lazy: bool = False,
                 materials: int = None, **kwargs: Any) -> None:
        """Initialise the mesh reader.

        This opens the underlying file and preloads metadata for the
        mesh.

        :param filepath: Path to the mesh file to open
        :type filepath: :class:`str`
        :param lazy: Disables preloading of node and element data. Use this
            setting to reduce memory usage with large meshes
        :type lazy: :class:`bool`
        """
        self.materials_per_element = int(kwargs.get('materials', 0))
        """Number of materials per element.

        This value will be set by the `NUM_MATERIALS_PER_ELEM <count>``
        card. Alternatively, the user may specify the number of
        materials to use via the `materials` argument of the
        :class:`Reader` class.

        If the number of materials is not specified in the file or via
        the `materials` argument, the number of elements will default
        to `0`.

        :type: :class:`int`
        """
        # TODO: Add MATERIALS_PER_ELEM parser
        self.name = 'Unnamed mesh'
        """Display name of the mesh.

        If the ``GM "<name>"`` or ``MESHNAME "<name>"`` cards are
        provided, their specified name will be used here. If neither
        card is given, the mesh name will default to
        ``"Unnamed mesh"``.

        :type: :class:`str`
        """
        # TODO: Add MESHNAME and GM parsers
        self._filepath = filepath
        self._lazy = lazy
        self._zero_index = bool(kwargs.get('zero_index', False))

        # Parse metadata
        data = self._parse_metadata()
        self.name = data.name
        self.materials_per_element = data.num_materials_per_elem
        if materials is not None:
            self.materials_per_element = int(materials)
        self._num_elements = data.num_elements
        self._num_nodes = data.num_nodes
        self._num_node_strings = data.num_node_strings

        if not lazy:

            # Create a cache of all
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
        return self

    def __exit__(self, exc_type: Optional[Type[BaseException]],
                 exc_value: Optional[BaseException],
                 exc_tb: Optional[TracebackType]) -> Literal[False]:
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
        """Alias for :attr:`Reader.extent`.

        :type: :obj:`typing.Tuple` [:class:`float`, :class:`float`,
            :class:`float`, :class:`float`]
        """
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


            :type: :obj:`typing.Tuple` [:class:`float`, :class:`float`,
                :class:`float`, :class:`float`]
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
        """Return an iterator over all elements in the mesh.

        This is synonymous to calling
        :meth:`py2dm.Reader.iter_elements()` with default arguments.

        If you prefer a list of elements, cast this iterator to
        :class:`list`.

        .. code-block:: python

            with py2dm.Reader('mesh.2dm') as mesh:
                elements = list(mesh.elements)

        :yield: Elements from the mesh in order.
        :type: :class:`py2dm.Element`
        """
        for element in self.iter_elements():
            yield element

    @property
    def nodes(self) -> Iterator[Node]:
        """Return an iterator over all nodes in the mesh.

        This is synonymous to calling :meth:`py2dm.Reader.iter_nodes()`
        with default arguments.

        If you prefer a list of nodes, cast this iterator to
        :class:`list`.

        .. code-block:: python

            with py2dm.Reader('mesh.2dm') as mesh:
                nodes = list(mesh.nodes)

        :yield: Nodes from the mesh in order.
        :type: :class:`py2dm.Node`
        """
        for node in self.iter_nodes():
            yield node

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

        :yield: Node strings from the mesh in order.
        :type: :class:`py2dm.NodeString`
        """
        for node_string in self.iter_node_strings():
            yield node_string

    @property
    def num_elements(self) -> int:
        """Return the number of elements in the mesh.

        :type: :class:`int`
        """
        return self._num_elements

    @property
    def num_nodes(self) -> int:
        """Return the number of nodes in the mesh.

        :type: :class:`int`
        """
        return self._num_nodes

    @property
    def num_node_strings(self) -> int:
        """Return the number of node strings in the mesh.

        :type: :class:`int`
        """
        return self._num_node_strings

    def close(self) -> None:
        """Close the mesh reader.

        This closes the underlying text file and discards any cached
        objects or metadata. The instance will become unusable after
        this call.

        .. note::

            This method is called automatically when using the class
            via the context manager.

        """
        _ = self

    def element(self, id_: int) -> Element:
        """Return a mesh element by its unique ID.

        :param id_: The ID of the element to return.
        :type id_: :class:`int`
        :raises KeyError: Raised if the given `id_` is invalid.
        :return: The element matching the given ID.
        :rtype: :class:`py2dm.Element`
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

        :param id_: The ID of the node to return.
        :type id_: :class:`int`
        :raises KeyError: Raised if the given `id_` is invalid.
        :return: The node matching the given ID.
        :rtype: :class:`py2dm.Node`
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
        :rtype: :class:`py2dm.NodeString`
        """
        for node_string in self.iter_node_strings():
            if node_string.name == name:
                return node_string
        raise KeyError(f'Node string \'{name}\' not found')

    def iter_elements(self, start: int = -1,
                      end: int = -1) -> Iterator[Element]:
        """Iterator over the mesh elements.

        :param start: The starting element ID. If not specified, the
            first node in the mesh is used as the starting point.
        :type start: :class:`int`
        :param end: The end element ID (excluding the `end` ID). If
            negative, the entire range of elements is yielded.
        :type end: :class:`int`
        :raises IndexError: Raised if the `start` ID is less than
            ``1``, or if the `end` ID is less than or equal to the
            `start` ID, or if either of the IDs exceeds the number of
            elements in the mesh.
        :yield: Mesh elements from the given range of IDs.
        :type: :class:`py2dm.Element`
        """
        if self.num_elements < 1:
            return ()
        # Get defaults
        id_min = 0 if self._zero_index else 1
        id_max = self.num_elements+1 if self._zero_index else self.num_elements
        if start < 0:
            start = id_min
        if end < 0:
            end = id_max
        # Check bounds
        if start > id_max:
            raise IndexError(f'Start element ID must be less than or equal to '
                             f'{id_max} ({start})')
        if end <= start:
            raise IndexError('End element ID must be greater than the start '
                             f'element ID ({end}<={start})')
        if end > id_max:
            raise IndexError('End element ID must be less than or equal to '
                             f'{id_max} ({end})')
        if self._lazy:
            # TODO: Implement lazy iterator
            raise NotImplementedError()
        else:
            offset = int(self._zero_index)
            for index, element in enumerate(
                    self._cache_elements[start-offset:end-offset]):
                if index == 0 and element.id != int(self._zero_index):
                    raise FormatError('idk', 'idk', 1)

    def iter_nodes(self, start: int = 1, end: int = -1) -> Iterator[Node]:
        """Iterator over the mesh nodes.

        :param start: The starting node ID. If not specified, the
            first node in the mesh is used as the starting point.
        :type start: :class:`int`
        :param end: The end node ID (excluding the `end` ID). If
            negative, the entire range of nodes is yielded.
        :type end: :class:`int`
        :raises IndexError: Raised if the `start` ID is less than
            ``1``, or if the `end` ID is less than or equal to the
            `start` ID, or if either of the IDs exceeds the number of
            nodes in the mesh.
        :yield: Mesh nodes from the given range of IDs.
        :type: :class:`py2dm.Node`
        """
        if self.num_nodes < 1:
            return ()
        # Get defaults
        id_min = 0 if self._zero_index else 1
        id_max = self.num_nodes+1 if self._zero_index else self.num_nodes
        if start < 0:
            start = id_min
        if end < 0:
            end = id_max
        # Check bounds
        if start > id_max:
            raise IndexError(f'Start node ID must be less than or equal to '
                             f'{id_max} ({start})')
        if end <= start:
            raise IndexError('End node ID must be greater than the start '
                             f'element ID ({end}<={start})')
        if end > id_max:
            raise IndexError('End node ID must be less than or equal to '
                             f'{id_max} ({end})')
        if self._lazy:
            # TODO: Implement lazy iterator
            raise NotImplementedError()
        else:
            offset = int(self._zero_index)
            return iter(self._cache_nodes[start-offset:end-offset])

    def iter_node_strings(self, start: int = 0,
                          end: int = -1) -> Iterator[NodeString]:
        """Iterator over the mesh's node strings.

        .. node::

            Unlike :meth:`Reader.iter_elements` or
            :meth:`Reader.iter_nodes`, this method uses Python slicing
            notation for its ranges due to node strings not having
            explicit IDs.

            Even if the mesh is using one-indexed IDs, starting
            iteration on the second node string still requires setting
            `start` to ``1`` when using this function.

        :param start: Starting offset for the iterator.
        :type start: :class:`int`
        :param end: End index for the node strings (exclusive).
        :type end: :class:`int`
        :raises IndexError: Raised if the `start` ID is less than
            ``0``, or if the `end` ID is less than or equal to the
            `start` ID, or if either of the IDs reaches the number of
            node strings in the mesh.
        :yield: Mesh node strings in order of definition.
        :type: :class:`py2dm.NodeString`
        """
        if self.num_node_strings < 1:
            return ()
        if self._lazy:
            # TODO: Implement lazy iterator
            raise NotImplementedError()
        else:
            if end < 0:
                return iter(self._cache_node_strings[start:])
            else:
                return iter(self._cache_node_strings[start:end])

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

    def _parse_metadata(self) -> _Metadata:
        """Parse the file for metadata.

        This method is only intended to be called as part of the
        initialiser and should not be called by other functions.
        """
        num_materials_per_elem: Optional[int] = None
        name: Optional[str] = None
        num_nodes = 0
        num_elements = 0
        num_node_strings = 0
        mesh2d_found: bool = False
        with open(self._filepath) as file_:
            for index, line in enumerate(file_):
                if not mesh2d_found and line.split('#', maxsplit=1)[0].strip():
                    if line.startswith('MESH2D'):
                        mesh2d_found = True
                    else:
                        raise ReadError(
                            'File is not a 2DM mesh file', self._filepath)
                if line.startswith('NUM_MATERIALS_PER_ELEM'):
                    chunks = line.split('#', maxsplit=1)[0].split(maxsplit=2)
                    num_materials_per_elem = int(chunks[1])
                elif line.startswith('MESHNAME') or line.startswith('GM'):
                    # NOTE: This fails for meshes with double quotes in their
                    # mesh name, but that is an unreasonable thing to want to
                    # do anyway. "We'll fix it later" (tm)
                    chunks = line.split('"', maxsplit=2)
                    name = chunks[1]
                elif line.startswith('ND'):
                    if(int(line.split(maxsplit=2)[1]) == 0
                            and not self._zero_index):
                        raise FormatError(
                            'Zero index encountered in non-zero-indexed file',
                            self._filepath, index+1)
                    num_nodes += 1
                elif (line.startswith('NS')
                        and '-' in line.split('#', maxsplit=1)[0]):
                    num_node_strings += 1
                elif line.split(maxsplit=1)[0] in _ELEMENTS:
                    if (int(line.split(maxsplit=2)[1]) == 0
                            and not self._zero_index):
                        raise FormatError(
                            'Zero index encountered in non-zero-indexed file',
                            self._filepath, index+1)
                    num_elements += 1
        return _Metadata(num_nodes, num_elements, num_node_strings, name,
                         num_materials_per_elem)


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
