"""Python versions of the objects represented by the 2DM mesh."""

import abc
from py2dm.errors import CardError, CustomFormatIgnored, FormatError
import warnings
from typing import Any, ClassVar, Iterable, List, Optional, Tuple, Type, TypeVar

from .types import MaterialIndex
from .utils import format_float, format_matid

try:
    from ._cparser import parse_element, parse_node, parse_node_string
except ImportError:
    from ._parser import parse_element, parse_node, parse_node_string
    import platform
    if platform.python_implementation() == 'CPython':
        warnings.warn('C parser not found, using Python implementation')

__all__ = [
    'Entity',
    'Element',
    'Element2L',
    'Element3L',
    'Element3T',
    'Element4Q',
    'Element6T',
    'Element8Q',
    'Element9Q',
    'LinearElement',
    'Node',
    'NodeString',
    'QuadrilateralElement',
    'TriangularElement'
]

EntityT = TypeVar('EntityT', bound='Entity')
ElementT = TypeVar('ElementT', bound='Element')


class Entity(metaclass=abc.ABCMeta):
    """Base class for geometries defined in the 2DM specification.

    This includes :class:`Node`, :class:`NodeString`, and
    the subclasses of :class:`Element`.

    This is an abstract class, subclasses must implement the
    :meth:`from_line` and :meth:`to_list` methods, as well as provide
    a :attr:`card` class attribute associating it with its 2DM card.
    """

    __slots__: List[str] = []
    card: ClassVar[str]
    """The 2DM card associated with this geometry."""

    @classmethod
    @abc.abstractmethod
    def from_line(cls: Type[EntityT], line: str, **kwargs: Any) -> EntityT:
        """Create a new instance from the given line.

        Lines passed into this element must start with the appropriate
        card identifier; trailing whitespace is allowed.

        If any bad data is encountered, a
        :class:`~py2dm.errors.FormatError` should be raised by the
        implementation.

        :param line: The line to parse.
        :type line: :class:`str`
        :return: An instance as described by the provided `line`.
        :rtype: :class:`Entity`
        """

    @abc.abstractmethod
    def to_list(self, **kwargs: Any) -> List[str]:
        """Generate the canonical 2DM representation of this entity.

        The line is returned as a list of strings to facilitate
        formatting into constant-width columns if requested.

        :return: A list of words to write to disk.
        :rtype: :obj:`typing.List` [:class:`str`]
        """


class Node(Entity):
    """A unique, numbered point in space.

    This is a subclass of :class:`Entity`.

    Nodes are the only geometries that define position in a mesh. Other
    objects like elements or node strings reference them by ID to
    position themselves.

    :param id_: The unique ID of the node. Always positive or zero.
    :type id_: :class:`int`
    :param x: X position of the node.
    :type x: :class:`float`
    :param y: Y position of the node.
    :type y: :class:`float`
    :param z: Z position of the node.
    :type z: :class:`float`
    """

    __slots__ = ['id', 'x', 'y', 'z']
    card: ClassVar[str] = 'ND'

    # pylint: disable=invalid-name
    def __init__(self, id_: int, x: float, y: float, z: float) -> None:
        self.id = id_
        """Unique identifier of the node.
        
        :type: :class:`int`
        """
        self.x = x
        """X coordinate of the node.
        
        :type: :class:`float`

        .. seealso::
        
            :attr:`pos` -- A tuple of floats representing the X, Y, and
            Z coordinate of the node.
        """
        self.y = y
        """Y coordinate of the node.
                
        :type: :class:`float`

        .. seealso::
        
            :attr:`pos` -- A tuple of floats representing the X, Y, and
            Z coordinate of the node.
        """
        self.z = z
        """Z coordinate of the node.
                
        :type: :class:`float`

        .. seealso::
        
            :attr:`pos` -- A tuple of floats representing the X, Y, and
            Z coordinate of the node.
        """

    def __repr__(self) -> str:
        return f'<Node #{self.id}: {self.pos}>'

    @property
    def pos(self) -> Tuple[float, float, float]:
        """The 3D position of the node as a tuple of three floats.

        :type: :obj:`typing.Tuple` [
            :class:`float`, :class:`float`, :class:`float`]
        """
        return self.x, self.y, self.z

    @classmethod
    def from_line(cls, line: str, **kwargs: Any) -> 'Node':
        """Instantiate a new :class:`Node` from the given line.

        Any extraneous keyword arguments are silently ignored.

        :param line: The line to parse.
        :type line: :class:`str`
        :param allow_zero_index: Whether to allow a node ID of zero.
        :type allow_zero_index: :class:`bool`, optional
        :return: A node representing the given line.
        :rtype: :class:`Node`
        """
        try:
            id_, *pos = parse_node(line, **kwargs)
        except ValueError as err:
            raise FormatError(*err.args) from err
        if len(line.split()) > 5 and len(line.split('#')[0].split()) > 5:
            warnings.warn('unexpected node fields', CustomFormatIgnored)
        return cls(id_, *pos)

    def to_list(self, **kwargs: Any) -> List[str]:
        """Generate the canonical 2DM representation of this entity.

        This is returned as a list of strings to facilitate formatting
        into constant-width columns.

        :return: A list of words to write to disk.
        :rtype: :class:`typing.List` [:class:`str`]
        """
        list_ = [self.card, str(self.id)]
        list_.extend((str(format_float(x)) for x in (self.x, self.y, self.z)))
        return list_


class Element(Entity):
    r"""Base class for all mesh Elements.

    This is a subclass of :class:`Entity`.

    This implements all of the abstract methods required to parse the
    element. The actual element classes themselves mostly serve to
    specify the 2DM card and number of nodes.

    :param id_: The unique ID of the element
    :type id_: :class:`int`
    :param \*nodes: Any number of nodes making up the element
    :type \*nodes: :class:`int`
    :param materials: Any number of material IDs for the element,
        defaults to ``None``
    :type materials: :obj:`typing.Tuple` [
        :obj:`typing.Union` [:class:`int`, :class:`float`]], optional
    """

    # pylint: disable=invalid-name
    __slots__ = ['id', 'materials', 'nodes']
    card: ClassVar[str]
    num_nodes: ClassVar[int]
    """The number of nodes of this element."""

    def __init__(self, id_: int, *nodes: int,
                 materials: Optional[Tuple[MaterialIndex, ...]] = None
                 ) -> None:
        self.id = id_
        """The unique ID of the element.
        
        :type: :class:`int`
        """
        self.materials = materials or ()
        """Material IDs assigned to this element.

        Depending on the 2DM-like format used, this could be a floating
        point value used to store e.g. element centroid elevation.

        :type: :obj:`typing.Optional` [:obj:`typing.Tuple` [
            :obj:`typing.Union` [:class:`int`, :class:`float`]]]
        """
        self.nodes = tuple(nodes)
        """The defining nodes for this element.
        
        :type: :obj:`typing.Tuple` [
            :class:`int`, :class:`int`, :class:`int`]
        """

    def __repr__(self) -> str:
        return f'<Element #{self.id} [{self.card}]: Node IDs {self.nodes}>'

    @property
    def num_materials(self) -> int:
        """The number of materials defined for this element.

        :type: :class:`int`
        """
        return len(self.materials)

    @classmethod
    def from_line(cls: Type[ElementT], line: str, **kwargs: Any) -> ElementT:
        """Create a new instance from the given line.

        :param line: The line to parse.
        :type line: :class:`str`
        :param allow_float_matid: Whether to allow floating point
            values as material indices. This is used by BASEMENT 3.x to
            store element centroid elevation.
        :type allow_float_matid: :class:`bool`, optional
        :param allow_zero_index: Whether to allow a node ID of zero.
        :type allow_zero_index: :class:`bool`, optional
        """
        if not line.startswith(cls.card):
            raise CardError('Bad card', line.split(maxsplit=1)[0])
        flag = kwargs.pop('allow_float_matid', True)
        try:
            id_, nodes, materials = parse_element(
                line, allow_float_matid=True, **kwargs)
        except ValueError as err:
            raise CardError(*err.args, None) from err
        for matid in materials:
            if isinstance(matid, float) and not flag:
                warnings.warn('float materials removed', CustomFormatIgnored)
        materials = tuple(
            filter(lambda m: flag or not isinstance(m, float), materials))
        return cls(id_, *nodes, materials=materials)

    def to_list(self, **kwargs: Any) -> List[str]:
        """Generate the canonical 2DM representation of this entity.

        This is returned as a list of strings to facilitate formatting
        into constant-width columns.

        :return: A list of words to write to disk.
        :rtype: :class:`typing.List` [:class:`str`]
        """
        out = [self.card, str(self.id)]
        out.extend((str(n) for n in self.nodes))
        # Discard floating point material indices if disallowed
        matids: Iterable[MaterialIndex] = self.materials
        if not kwargs.get('allow_float_matid', True):
            matids = filter(lambda m: isinstance(m, int), self.materials)
        out.extend((format_matid(m) for m in matids))
        return out


class LinearElement(Element):
    """Base class for linear mesh elements.

    This is a subclass of :class:`Element`.

    This is exclusively provided to group related element types
    together and to allow checking for element type via their shared
    base class:

    .. code-block:: python3

        if isinstance(obj, py2dm.LinearElement):
            ...

    """


class TriangularElement(Element):
    """Base class for triangular mesh elements.

    This is a subclass of :class:`Element`.

    This is exclusively provided to group related element types
    together and to allow checking for element type via their shared
    base class:

    .. code-block:: python3

        if isinstance(obj, py2dm.TriangularElement):
            ...

    """


class QuadrilateralElement(Element):
    """Base class for quadrilateral mesh elements.

    This is a subclass of :class:`Element`.

    This is exclusively provided to group related element types
    together and to allow checking for element type via their shared
    base class:

    .. code-block:: python3

        if isinstance(obj, py2dm.QuadrilateralElement):
            ...

    """


class Element2L(LinearElement):
    """Two-noded, linear element (E2L).

    This is a subclass of :class:`LinearElement`.
    """

    card: ClassVar[str] = 'E2L'
    num_nodes: ClassVar[int] = 2


class Element3L(LinearElement):
    """Three-noded, linear element (E3L).

    This is a subclass of :class:`LinearElement`.
    """

    card: ClassVar[str] = 'E3L'
    num_nodes: ClassVar[int] = 3


class Element3T(TriangularElement):
    """Three-noded, triangular mesh element (E3T).

    This is a subclass of :class:`TriangularElement`.
    """

    card: ClassVar[str] = 'E3T'
    num_nodes: ClassVar[int] = 3


class Element6T(TriangularElement):
    """Six-noded, triangular mesh element (E6T).

    This is a subclass of :class:`TriangularElement`.
    """

    card: ClassVar[str] = 'E6T'
    num_nodes: ClassVar[int] = 6


class Element4Q(QuadrilateralElement):
    """Four-noded, quadrilateral mesh element (E4Q).

    This is a subclass of :class:`QuadrilateralElement`.
    """

    card: ClassVar[str] = 'E4Q'
    num_nodes: ClassVar[int] = 4


class Element8Q(QuadrilateralElement):
    """Eight-noded, quadrilateral mesh element (E8Q).

    This is a subclass of :class:`QuadrilateralElement`.
    """

    card: ClassVar[str] = 'E8Q'
    num_nodes: ClassVar[int] = 8


class Element9Q(QuadrilateralElement):
    """Nine-noded, quadrilateral mesh element (E9Q).

    This is a subclass of :class:`QuadrilateralElement`.
    """

    card: ClassVar[str] = 'E9Q'
    num_nodes: ClassVar[int] = 9


class NodeString:
    r"""A polyline represented by a string of nodes (NS).

    This mostly satisfies the interface laid out by the :class:`Entity`
    ABC, except that the :meth:`from_line` method features an optional
    parameter that allows specification of an existing node string.

    This is necessary as node strings may be split across multiple
    lines in a 2DM file as lines may not exceed 10 tags.

    :param \*nodes: A list of node IDs making up the node string
    :type \*nodes: :class:`int`
    :param name: An optional name to give to a particular node string,
        defaults to ``None``
    :type name: :class:`str`, optional
    """

    __slots__ = ['name', 'nodes']
    card: ClassVar[str] = 'NS'

    def __init__(self, *nodes: int, name: Optional[str] = None) -> None:
        self.name = name
        """An optional name used to identify the node string.

        :type: :obj:`typing.Optional` [:class:`str`]
        """
        self.nodes = tuple(nodes)
        """The defining nodes of the node strings.

        :type: :obj:`typing.Tuple` [:class:`int`]
        """

    def __repr__(self) -> str:
        if self.name is not None:
            return f'<NodeString "{self.name}": {self.nodes}>'
        return f'<Unnamed NodeString: {self.nodes}>'

    @property
    def num_nodes(self) -> int:
        """Return the number of nodes in the node string.

        :type: :class:`int`
        """
        return len(self.nodes)

    @classmethod
    def from_line(cls, line: str, node_string: Optional['NodeString'] = None,
                  **kwargs: Any) -> Tuple['NodeString', bool]:
        """Create a new instance from the given line.

        This returns a tuple consisting of the :class:`NodeString`
        instance generated, as well as a flag indicating whether the
        node string is complete, which is indicated by a negative node
        ID.

        :param line: The line to parse
        :type lint: :class:`str`
        :param node_string: An existing node string to append, defaults
            to ``None``
        :type node_string: :class:`NodeString`, optional
        :return: The created node string and the final flag
        :rtype: :obj:`typing.Tuple` [
            :class:`NodeString`, :class:`bool`]
        """
        nodes: List[int] = (
            [] if node_string is None else list(node_string.nodes))
        try:
            nodes, is_done, name = parse_node_string(
                line, nodes=nodes, **kwargs)
        except ValueError as err:
            raise FormatError(*err.args) from err
        if node_string is None:
            node_string = NodeString()
        node_string.nodes = tuple(nodes)
        if name:
            node_string.name = name.strip('"')
        return node_string, is_done

    def to_list(self, **kwargs: Any) -> List[str]:
        """Generate the canonical 2DM representation of this entity.

        It is returned as a list of strings to facilitate formatting
        into constant-width columns.

        :return: A list of words to write to disk
        :rtype: :obj:`typing.List` [:class:`str`]
        """
        list_ = [self.card]
        list_.extend((str(n) for n in self.nodes))
        # Flip last node ID to signify the end of the node sign
        list_[-1] = f'-{list_[-1]}'
        if self.name is not None and kwargs.get('include_name', True):
            list_.append(self.name)
        return list_
