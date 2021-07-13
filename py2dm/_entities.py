"""Python versions of the objects represented by the 2DM mesh."""

import abc
import functools
import warnings
from typing import (Any, ClassVar, Iterable, List, Optional, SupportsFloat,
                    Tuple, Type, TypeVar, Union)

from .errors import CardError, CustomFormatIgnored
from ._parser import parse_element, parse_node, parse_node_string

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

_Material = Union[int, float]
_EntityT = TypeVar('_EntityT', bound='Entity')
_ElementT = TypeVar('_ElementT', bound='Element')


class Entity(metaclass=abc.ABCMeta):
    """Base class for geometries defined in the 2DM specification.

    This includes :class:`Node`, :class:`NodeString`, and
    the subclasses of :class:`Element`.

    This is an abstract class, subclasses must implement the
    :meth:`from_line` and :meth:`to_line` methods, as well as provide
    a :attr:`card` class attribute associating it with its 2DM card.
    """

    __slots__: List[str] = []
    card: ClassVar[str]
    """The 2DM card associated with this geometry."""

    def __eq__(self, other: Any) -> bool:
        # pylint: disable=unidiomatic-typecheck
        return type(self) == type(other) and self.card == other.card

    @classmethod
    @abc.abstractmethod
    def from_line(cls: Type[_EntityT], line: str, **kwargs: Any) -> _EntityT:
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
    def to_line(self, **kwargs: Any) -> List[str]:
        """Generate the canonical 2DM representation of this entity.

        The line is returned as a list of strings to facilitate
        formatting into constant-width columns if requested.

        :return: A list of words to write to disk.
        :rtype: :obj:`typing.List` [:class:`str`]
        """


class Node(Entity):
    """A unique, numbered point in space.

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
    # pylint: disable=invalid-name

    __slots__ = ['id', 'x', 'y', 'z']
    card: ClassVar[str] = 'ND'

    def __init__(self, id_: int, x: float, y: float, z: float) -> None:
        self.id: int = id_
        """Unique identifier of the node.

        :type: :class:`int`
        """
        self.x: float = x
        """X coordinate of the node.

        :type: :class:`float`

        .. seealso::

            :attr:`pos` -- A tuple of floats representing the X, Y, and
            Z coordinate of the node.
        """
        self.y: float = y
        """Y coordinate of the node.

        :type: :class:`float`

        .. seealso::

            :attr:`pos` -- A tuple of floats representing the X, Y, and
            Z coordinate of the node.
        """
        self.z: float = z
        """Z coordinate of the node.

        :type: :class:`float`

        .. seealso::

            :attr:`pos` -- A tuple of floats representing the X, Y, and
            Z coordinate of the node.
        """

    def __eq__(self, other: Any) -> bool:
        if not super().__eq__(other):
            return False
        return self.id == other.id and self.pos == other.pos

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
        id_, *pos = parse_node(line, **kwargs)
        if len(line.split()) > 5 and len(line.split('#')[0].split()) > 5:
            warnings.warn('unexpected node fields', CustomFormatIgnored)
        return cls(id_, *pos)

    def to_line(self, **kwargs: Any) -> List[str]:
        """Generate the canonical 2DM representation of this entity.

        This is returned as a list of strings to facilitate formatting
        into constant-width columns.

        :return: A list of words to write to disk.
        :rtype: :class:`typing.List` [:class:`str`]
        """
        id_width = int(kwargs.get('id_width', 8))
        list_ = [self.card, f'{self.id:{id_width}}']
        if kwargs.get('compact', False):
            list_.extend((str(x) for x in (self.x, self.y, self.z)))
        else:
            decimals = int(kwargs.get('decimals', 6))
            list_.extend((str(_format_float(x, decimals=decimals))
                          for x in (self.x, self.y, self.z)))
        return list_


class Element(Entity):
    r"""Base class for all mesh Elements.

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
                 materials: Optional[Tuple[_Material, ...]] = None) -> None:
        if hasattr(self, 'num_nodes') and len(nodes) != self.num_nodes:
            raise CardError(f'{self.card} element requires {self.num_nodes} '
                            f'nodes, got {len(nodes)}')
        self.id: int = id_
        """The unique ID of the element.

        :type: :class:`int`
        """
        self.materials: Tuple[Union[int, float], ...] = materials or ()
        """Material IDs assigned to this element.

        Depending on the 2DM-like format used, this could be a floating
        point value used to store e.g. element centroid elevation.

        :type: :obj:`typing.Tuple` [
            :obj:`typing.Union` [:class:`int`, :class:`float`], ...]
        """
        self.nodes: Tuple[int, ...] = tuple(nodes)
        """The defining nodes for this element.

        :type: :obj:`typing.Tuple` [:class:`int`, ...]
        """

    def __eq__(self, other: Any) -> bool:
        if not super().__eq__(other):
            return False
        return (self.id == other.id and
                self.nodes == other.nodes and
                self.materials == other.materials)

    def __repr__(self) -> str:
        string = f'<Element #{self.id} [{self.card}]: Node IDs {self.nodes}'
        string += f' Materials {self.materials}>' if self.materials else '>'
        return string

    @property
    def num_materials(self) -> int:
        """The number of materials defined for this element.

        :type: :class:`int`
        """
        return len(self.materials)

    @classmethod
    def from_line(cls: Type[_ElementT], line: str, **kwargs: Any) -> _ElementT:
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
        id_, nodes, materials = parse_element(
            line, allow_float_matid=True, **kwargs)
        for matid in materials:
            if isinstance(matid, float) and not flag:
                warnings.warn('float materials removed', CustomFormatIgnored)
        materials = tuple(
            filter(lambda m: flag or not isinstance(m, float), materials))
        return cls(id_, *nodes, materials=materials)

    def to_line(self, **kwargs: Any) -> List[str]:
        """Generate the canonical 2DM representation of this entity.

        This is returned as a list of strings to facilitate formatting
        into constant-width columns.

        :return: A list of words to write to disk.
        :rtype: :class:`typing.List` [:class:`str`]
        """
        id_width = int(kwargs.get('id_width', 8))
        out = [self.card, f'{self.id:{id_width}}']
        out.extend((f'{n:{id_width}}' for n in self.nodes))
        # Discard floating point material indices if disallowed
        matids: Iterable[_Material] = self.materials
        if not kwargs.get('allow_float_matid', True):
            matids = filter(lambda m: isinstance(m, int), self.materials)
        # Format materials
        if kwargs.get('compact', False):
            out.extend((str(m) for m in matids))
        else:
            decimals = int(kwargs.get('decimals', 3))
            out.extend((_format_matid(m, decimals=decimals) for m in matids))
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

    This differs from the other mesh entity classes in that the
    :meth:`from_line` method features an optional parameter that allows
    specification of an existing node string to extend.

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
        if len(nodes) < 2:
            raise CardError('At least two node required')
        self.name: Optional[str] = name
        """An optional name used to identify the node string.

        :type: :obj:`typing.Optional` [:class:`str`]
        """
        self.nodes: Tuple[int, ...] = tuple(nodes)
        """The defining nodes of the node strings.

        :type: :obj:`typing.Tuple` [:class:`int`]
        """

    def __eq__(self, other: Any) -> bool:
        # pylint: disable=unidiomatic-typecheck
        if not (type(self) == type(other) and self.card == other.card):
            return False
        return self.nodes == other.nodes and self.name == other.name

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
        nodes, is_done, name = parse_node_string(line, nodes=nodes, **kwargs)
        if node_string is None:
            node_string = NodeString(*nodes)
        else:
            node_string.nodes = tuple(nodes)
        if name:
            node_string.name = name.strip('"')
        return node_string, is_done

    def to_line(self, **kwargs: Any) -> List[str]:
        """Generate the canonical 2DM representation of this entity.

        The returned list should be written as a whitespace-separated
        list with irregular line width. It may also contain newline
        characters. No whitespace should be inserted around newlines.

        :return: A list of words to write to disk
        :rtype: :obj:`typing.List` [:class:`str`]
        """
        list_ = [self.card]
        fold = int(kwargs.get('fold_after', 10))
        if fold > 0:
            for index, node in enumerate(self.nodes):
                if (index != 0 and index % fold == 0
                        and len(self.nodes) > index):
                    list_.extend(('\n', self.card))
                list_.append(str(node))
        else:
            list_.extend((str(n) for n in self.nodes))
        # Flip last node ID to signify the end of the node sign
        list_[-1] = f'-{list_[-1]}'
        if self.name is not None and kwargs.get('include_name', True):
            list_.append(self.name)
        return list_


def _format_float(value: SupportsFloat, *, decimals: int = 6) -> str:
    """Format a node position into a string.

    This uses the format requested by 2DM: up to nine significant
    digits followed by an exponent, e.g. ``0.5 -> 5.0e-01``.

    :param value: A object that supports casting to :class:`float`.
    :type value: :obj:`typing.SupportsFloat`
    :param decimals: The number of decimal places to include, defaults
        to ``6``.
    :type decimals: :class:`int`, optional
    :return: The formatted string with no extra whitespace.
    :rtype: :class:`str`
    """
    string = f'{" " if float(value) >= 0.0 else ""}{float(value):.{decimals}e}'
    return string


def _format_matid(value: _Material, *, decimals: int = 6) -> str:
    """Format a material index.

    The decimals parameter will be ignored if the input value is an
    integer.

    :param value: The material index to format.
    :type value: :obj:`typing.Union` [:class:`int`, :class:`float`]
    :param decimals: The number of decimal places to include for
        floating point material IDs, defaults to ``6``.
    :type decimals: :class:`int`, optional
    :return: The formatted material index.
    :rtype: :class:`str`
    """
    if isinstance(value, int):
        return str(value) if value < 0 else f' {value}'
    return _format_float(value, decimals=decimals)


@functools.lru_cache(None)
def element_factory(line: str) -> Type[Element]:
    """Return a :class:`py2dm.Element` subclass by card.

    :param line: The line to create an element fro.
    :type line: :class:`str`
    :raises ValueError: Raised if the given card doesn't match any
        :class:`py2dm.Element` subclass'.
    :return: The element type matching the given card.
    :rtype: :obj:`typing.Type` [:class:`py2dm.Element`]
    """
    for element_group in Element.__subclasses__():
        for subclass in element_group.__subclasses__():
            if line.startswith(subclass.card):
                return subclass
    if not line.split() or not line.split('#')[0].split():
        raise ValueError('Line is blank')
    card = line.split(maxsplit=1)[0]
    raise NotImplementedError(f'Unsupported card name \'{card}\'')
