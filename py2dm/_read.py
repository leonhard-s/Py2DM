"""Implementation of the mesh reading interface.

This module defines the :class:`py2dm.ReaderBase` interface, as well as
subclasses implementing this interface to provide variations optimised
for specific use-cases. Refer to the implementation classes
:class:`py2dm.Reader` and :class:`py2dm.LazyReader for details.
"""

import abc
import functools
from types import TracebackType
from typing import (Any, Iterator, List, NamedTuple, Optional, Tuple, Type,
                    TypeVar)

from ._entities import Element, Node, NodeString
from .errors import FormatError, ReadError

try:
    from typing import Literal
except ImportError:  # pragma: no cover
    # Required for compatibilty with Python 3.7 (used in QGIS 3)
    from typing_extensions import Literal  # type: ignore

__all__ = [
    'Reader',
    'ReaderBase'
]

T = TypeVar('T')

# A list of all 2DM cards that are considered elements
_ELEMENT_CARDS = [
    'E2L',
    'E3L',
    'E3T',
    'E6T',
    'E4Q',
    'E8Q',
    'E9Q'
]


class _Metadata(NamedTuple):
    """Typed named tuple containing mesh metadata."""

    num_nodes: int
    num_elements: int
    num_node_strings: int
    name: Optional[str]
    num_materials_per_elem: int
    # File seek offsets
    pos_nodes_start: int
    pos_nodes_end: int
    pos_elements_start: int
    pos_elements_end: int
    pos_node_strings_start: int
    pos_node_strings_end: int


class ReaderBase(metaclass=abc.ABCMeta):
    """Abstract class interface definition for 2DM reader classes.

    This ABC defines the endpoints to be implemented by readers. Use
    this as the type definition for any code meant to work with Py2DM
    readers.

    :param filepath: Path to the mesh file to open.
    :type filepath: :class:`str`
    """

    def __init__(self, filepath: str, **kwargs: Any) -> None:
        self.materials_per_element = int(kwargs.get('materials', 0))
        """Number of materials per element.

        This value will be set by the `NUM_MATERIALS_PER_ELEM <count>``
        card. Alternatively, the user may specify the number of
        materials to use via the `materials` keyword argument.

        If the number of materials is not specified in the file or via
        the `materials` argument, the number of elements will default
        to `0`.

        :type: :class:`int`
        """
        self.name = 'Unnamed mesh'
        """Display name of the mesh.

        If the ``GM "<name>"`` or ``MESHNAME "<name>"`` cards are
        provided, their specified name will be used here. If neither
        card is given, the mesh name will default to
        ``"Unnamed mesh"``.

        :type: :class:`str`
        """

        self._filepath = filepath
        self._metadata = self._parse_metadata()
        self._num_materials = int(kwargs.get('materials', 0))
        self._zero_index = bool(kwargs.get('zero_index', False))

    def __enter__(self: T) -> T:
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

    @property  # type: ignore
    @functools.lru_cache(1)
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
            return float('nan'), float('nan'), float('nan'), float('nan')
        min_x = max_x = node.x
        min_y = max_y = node.y
        # Update value
        for node in self.iter_nodes():
            if node.x < min_x:
                min_x = node.x
            elif node.x > max_x:
                max_x = node.x
            if node.y < min_y:
                min_y = node.y
            elif node.y > max_y:
                max_y = node.y
        return min_x, max_x, min_y, max_y

    @property
    @abc.abstractmethod
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

    @property
    @abc.abstractmethod
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

    @property
    @abc.abstractmethod
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

    @property
    def num_elements(self) -> int:
        """Return the number of elements in the mesh.

        :type: :class:`int`
        """
        return self._metadata.num_elements

    @property
    def num_nodes(self) -> int:
        """Return the number of nodes in the mesh.

        :type: :class:`int`
        """
        return self._metadata.num_nodes

    @property
    def num_node_strings(self) -> int:
        """Return the number of node strings in the mesh.

        :type: :class:`int`
        """
        return self._metadata.num_node_strings

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

    @abc.abstractmethod
    def element(self, id_: int) -> Element:
        """Return a mesh element by its unique ID.

        :param id_: The ID of the element to return.
        :type id_: :class:`int`
        :raises KeyError: Raised if the given `id_` is invalid.
        :return: The element matching the given ID.
        :rtype: :class:`py2dm.Element`
        """

    @abc.abstractmethod
    def node(self, id_: int) -> Node:
        """Return a mesh node by its unique ID.

        :param id_: The ID of the node to return.
        :type id_: :class:`int`
        :raises KeyError: Raised if the given `id_` is invalid.
        :return: The node matching the given ID.
        :rtype: :class:`py2dm.Node`
        """

    @abc.abstractmethod
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

    @abc.abstractmethod
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

    @abc.abstractmethod
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

    @abc.abstractmethod
    def iter_node_strings(self, start: int = 0,
                          end: int = -1) -> Iterator[NodeString]:
        """Iterator over the mesh's node strings.

        .. note::

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

    def _parse_metadata(self) -> Any:
        """Parse the file for metadata.

        This method is only intended to be called as part of the
        initialiser and should not be called by other functions.
        """
        # TODO: Rewrite metadata parser (C?)


class Reader(ReaderBase):
    """Default Py2DM reader class used to parse and validate 2DM files.

    This reader loads the entire mesh file into memory, allowing for
    fast ID-based access and iteration without needing to wait for the
    storage medium.

    Do note that this implementation also keeps the Python
    representation of all mesh entities in memory until the instance
    is destroyed, which can consume a significant amount of memory for
    very large meshes.
    """

    def __init__(self, filepath: str, **kwargs: Any) -> None:
        super().__init__(filepath, **kwargs)

        self._cache_nodes: List[Node] = []
        self._cache_elements: List[Element] = []
        self._cache_node_strings: List[NodeString] = []
        # Parse and load the entire file
        with open(filepath) as file_:
            # Nodes
            file_.seek(self._metadata.pos_nodes_start)
            for line in file_:
                node = Node.from_line(line)
                self._cache_nodes.append(node)
                if node.id >= self.num_nodes:
                    break
            # Elements
            file_.seek(self._metadata.pos_elements_start)
            for line in file_:
                element = _element_factory(line).from_line(line)
                self._cache_elements.append(element)
                if element.id >= self.num_elements:
                    break
            # Node strings
            file_.seek(self._metadata.pos_node_strings_start)
            node_string: Optional[NodeString] = None
            for line in file_:
                if line.startswith('NS'):
                    node_string, is_done = NodeString.from_line(
                        line, node_string)
                    if is_done:
                        self._cache_node_strings.append(node_string)
                        node_string = None

    @property
    def elements(self) -> Iterator[Element]:
        return iter(self._cache_elements)

    @property
    def nodes(self) -> Iterator[Node]:
        return iter(self._cache_nodes)

    @property
    def node_strings(self) -> Iterator[NodeString]:
        return iter(self._cache_node_strings)

    def element(self, id_: int) -> Element:
        # Conform ID to always be one-indexed
        id_conf = id_+1 if self._zero_index else id_
        # Check ID range
        if not 1 <= id_conf <= self.num_elements:
            id_min = 0 if self._zero_index else 1
            id_max = (
                self.num_elements-1 if self._zero_index else self.num_elements)
            raise KeyError(f'Invalid element ID {id_}, element IDs must be '
                           f'between {id_min} and {id_max}')
        return self._cache_elements[id_conf-1]

    def node(self, id_: int) -> Node:
        # Conform ID to alwasy be one-indexed
        id_conf = id_+1 if self._zero_index else id_
        # Check ID range
        if not 1 <= id_conf <= self.num_nodes:
            id_min = 0 if self._zero_index else 1
            id_max = self.num_nodes-1 if self._zero_index else self.num_nodes
            raise KeyError(f'Invalid node ID {id_}, node IDs must be between '
                           f'{id_min} and {id_max}')
        return self._cache_nodes[id_conf-1]

    def node_string(self, name: str) -> NodeString:
        for node_string in self.iter_node_strings():
            if node_string.name == name:
                return node_string
        raise KeyError(f'Node string \'{name}\' not found')

    def iter_elements(self, start: int = -1,
                      end: int = -1) -> Iterator[Element]:
        if self.num_elements < 1:
            return iter(())
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
        offset = int(self._zero_index)
        for index, element in enumerate(
                self._cache_elements[start-offset:end-offset]):
            if index == 0 and element.id != int(self._zero_index):
                raise FormatError('idk', 'idk', 1)
            yield element

    def iter_nodes(self, start: int = 1, end: int = -1) -> Iterator[Node]:
        if self.num_nodes < 1:
            return iter(())
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
        offset = int(self._zero_index)
        return iter(self._cache_nodes[start-offset:end-offset])

    def iter_node_strings(self, start: int = 0,
                          end: int = -1) -> Iterator[NodeString]:
        if self.num_node_strings < 1:
            return iter(())
        if end < 0:
            return iter(self._cache_node_strings[start:])
        else:
            return iter(self._cache_node_strings[start:end])


@functools.lru_cache(None)
def _element_factory(line: str) -> Type[Element]:
    """Return a :class:`py2dm.Element` subclass by card.

    Arguments:
        line: The line to create an element for.

    Raises:
        ValueError: Raised if the given card doesn't match any subclass

    Returns:
        The element class mataching the given tag

    """
    for element_group in Element.__subclasses__():
        for subclass in element_group.__subclasses__():
            if line.startswith(subclass.card):
                return subclass
    card = line.split(maxsplit=1)[0]
    raise NotImplementedError(f'Unsupported card name \'{card}\'')
