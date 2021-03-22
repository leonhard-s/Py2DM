"""Python versions of the objects represented by the 2DM mesh."""

import abc
from py2dm.errors import CardError, CustomFormatIgnored, FormatError
import warnings
from typing import Any, ClassVar, List, Optional, Tuple, Type, TypeVar

from .types import MaterialIndex
from .utils import format_float, format_matid

try:
    from ._cparser import parse_element, parse_node, parse_node_string
except ImportError:
    from ._parser import parse_element, parse_node, parse_node_string
    import platform
    if platform.python_implementation() == 'CPython':
        warnings.warn('C parser not found, using Python implementation')

__all__ = ['Entity', 'Element', 'Element2L', 'Element3L', 'Element3T',
           'Element4Q', 'Element6T', 'Element8Q', 'Element9Q', 'LinearElement',
           'Node', 'NodeString', 'QuadrilateralElement', 'TriangularElement']

EntityT = TypeVar('EntityT', bound='Entity')
ElementT = TypeVar('ElementT', bound='Element')


class Entity(metaclass=abc.ABCMeta):
    """Base class for all entities defined in a 2DM file.

    This includes :class:`Node`, :class:`NodeString`, and
    :class:`Element`.

    This is an abstract class, subclasses must implement the
    :meth:`from_line` and :meth:`to_list` methods.

    """

    __slots__: List[str] = []
    card: ClassVar[str]  #: The 2DM card representing this type

    @classmethod
    @abc.abstractmethod
    def from_line(cls: Type[EntityT], line: str, **kwargs: Any) -> EntityT:
        """Create a new instance from the given line.

        The line passed will start with the entity's tag and have
        already been split in to chunks/words.

        If any bad data is encountered, a
        :class:`~py2dm.errors.FormatError` should be raised.

        :param line: The line to parse
        :type line: str
        :return: The instance described by the given line
        :rtype: :class:`Entity`
        """

    @abc.abstractmethod
    def to_list(self) -> List[str]:
        """Generate the canonical 2DM representation of this entity.

        It is returned as a list of strings to facilitate formatting
        into constant-width columns.

        :return: A list of words to write to disk
        :rtype: List[str]
        """


class Node(Entity):
    """A unique, numbered point in space.

    This is a subclass of :class:`Entity`.

    Nodes are the only geometries that define position in a mesh. Other
    objects like elements or node strings reference them by ID to
    position themselves in space.

    :param id_: The unique ID of the node
    :type id_: int
    :param x: X position of the node
    :type x: float
    :param y: Y position of the node
    :type y: float
    :param z: Z position of the node
    :type z: float
    """

    __slots__ = ['id', 'x', 'y', 'z']
    card: ClassVar[str] = 'ND'

    # pylint: disable=invalid-name
    def __init__(self, id_: int, x: float, y: float, z: float) -> None:
        self.id = id_  #: The unique ID of the noe
        self.x = x  #: The X position of the node
        self.y = y  #: The Y position of the node
        self.z = z  #: The Z position of the node

    def __repr__(self) -> str:
        return f'Node #{self.id}: {self.pos}'

    @property
    def pos(self) -> Tuple[float, float, float]:
        """The 3D position of the node as a tuple of floats."""
        return self.x, self.y, self.z

    @classmethod
    def from_line(cls, line: str, **kwargs: Any) -> 'Node':
        try:
            id_, *pos = parse_node(line, **kwargs)
        except ValueError as err:
            raise FormatError(*err.args) from err
        if len(line.split()) > 5:
            warnings.warn('unexpected node fields', CustomFormatIgnored)
        return cls(id_, *pos)

    def to_list(self) -> List[str]:
        coords = [format_float(v) for v in (self.x, self.y, self.z)]
        return [self.card, *(str(x) for x in (self.id, *coords))]


class Element(Entity):
    r"""Base class for all mesh Elements.

    This is a subclass of :class:`Entity`.

    This implements all of the abstract methods required to parse the
    element. The actual element classes themselves mostly serve to
    specify the 2DM card and number of nodes.

    :param id_: The unique ID of the element
    :type id_: int
    :param \*nodes: Any number of nodes making up the element
    :type \*nodes: int
    :param materials: Any number of material IDs for the element,
        defaults to ``None``
    :type materials: Tuple[Union[int, float], ...], optional
    """

    # pylint: disable=invalid-name
    __slots__ = ['id', 'materials', 'nodes']
    card: ClassVar[str]
    num_nodes: ClassVar[int]  #: The number of nodes of the element

    def __init__(self, id_: int, *nodes: int,
                 materials: Optional[Tuple[MaterialIndex, ...]] = None
                 ) -> None:
        self.id = id_  #: The unique ID of the element
        self.materials = materials or ()  #: The material IDs of the element
        self.nodes = tuple(nodes)  #: The nodes making up the element

    def __repr__(self) -> str:
        return f'Element #{self.id} [{self.card}]: Node IDs {self.nodes}'

    @property
    def num_materials(self) -> int:
        """The number of materials for this element."""
        return len(self.materials)

    @classmethod
    def from_line(cls: Type[ElementT], line: str, **kwargs: Any) -> ElementT:
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

    def to_list(self) -> List[str]:
        nodes = [str(n) for n in self.nodes]
        materials = [format_matid(m) for m in self.materials]
        return [self.card, str(self.id), *nodes, *materials]


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
    """Two-noded, linear element.

    This type's card tag is ``E2L``.

    This is a subclass of :class:`LinearElement`.

    """

    card: ClassVar[str] = 'E2L'
    num_nodes: ClassVar[int] = 2


class Element3L(LinearElement):
    """Three-noded, linear element.

    This type's card tag is ``E3L``.

    This is a subclass of :class:`LinearElement`.

    """

    card: ClassVar[str] = 'E3L'
    num_nodes: ClassVar[int] = 3


class Element3T(TriangularElement):
    """Three-noded, triangular mesh element.

    This type's card tag is ``E3T``.

    This is a subclass of :class:`TriangularElement`.

    """

    card: ClassVar[str] = 'E3T'
    num_nodes: ClassVar[int] = 3


class Element6T(TriangularElement):
    """Six-noded, triangular mesh element.

    This type's card tag is ``E6T``.

    This is a subclass of :class:`TriangularElement`.

    """

    card: ClassVar[str] = 'E6T'
    num_nodes: ClassVar[int] = 6


class Element4Q(QuadrilateralElement):
    """Four-noded, quadrilateral mesh element.

    This type's card tag is ``E4Q``.

    This is a subclass of :class:`QuadrilateralElement`.

    """

    card: ClassVar[str] = 'E4Q'
    num_nodes: ClassVar[int] = 4


class Element8Q(QuadrilateralElement):
    """Eight-noded, quadrilateral mesh element.

    This type's card tag is ``E8Q``.

    This is a subclass of :class:`QuadrilateralElement`.

    """

    card: ClassVar[str] = 'E8Q'
    num_nodes: ClassVar[int] = 8


class Element9Q(QuadrilateralElement):
    """Nine-noded, quadrilateral mesh element.

    This type's card tag is ``E9Q``.

    This is a subclass of :class:`QuadrilateralElement`.

    """

    card: ClassVar[str] = 'E9Q'
    num_nodes: ClassVar[int] = 9


class NodeString:
    r"""A polyline represented by a string of nodes.

    This mostly satisfies the interface laid out by the :class:`Entity`
    ABC, except that the :meth:`from_line` method features an optional
    parameter that allows specification of an existing node string.

    This is necessary as node strings may be split across multiple
    lines in a 2DM.

    This type's card tag is ``NS``.

    :param \*nodes: A list of node IDs making up the node string
    :type \*nodes: int
    :param name: An optional name to give to a particular node string,
        defaults to ``None``
    :type name: str, optional
    """

    __slots__ = ['name', 'nodes']
    card: ClassVar[str] = 'NS'  #: The 2DM card representing this type

    def __init__(self, *nodes: int, name: Optional[str] = None) -> None:
        self.name = name
        self.nodes = tuple(nodes)

    def __repr__(self) -> str:
        if self.name is not None:
            return f'NodeString "{self.name}": {self.nodes}'
        return f'Unnamed NodeString: {self.nodes}'

    @property
    def num_nodes(self) -> int:
        """Return the number of nodes in the node string."""
        return len(self.nodes)

    @classmethod
    def parse_line(cls, line: str, node_string: Optional['NodeString'] = None,
                   **kwargs: Any) -> Tuple['NodeString', bool]:
        """Create a new instance from the given line.

        This returns a tuple consisting of the :class:`NodeString`
        instance generated, as well as a flag indicating whether the
        node string is complete, which is indicated by a negative node
        ID.

        :param line: The line to parse
        :type lint: str
        :param node_string: An existing node string to append, defaults
            to ``None``
        :type node_string: :class:`NodeString`, optional
        :return: The created node string and the final flag
        :rtype: Tuple[:class:`NodeString`, bool]
        """
        nodes: List[int] = [] if node_string is None else list(
            node_string.nodes)
        allow_zero_index = bool(kwargs.pop('allow_zero_index', False))
        try:
            nodes, is_done, name = parse_node_string(
                line, allow_zero_index=allow_zero_index, nodes=nodes)
        except ValueError as err:
            raise FormatError(*err.args) from err
        if node_string is None:
            node_string = NodeString()
        node_string.nodes = tuple(nodes)
        if name:
            node_string.name = name.strip('"')
        return node_string, is_done

    def to_list(self) -> List[str]:
        """Generate the canonical 2DM representation of this entity.

        It is returned as a list of strings to facilitate formatting
        into constant-width columns.

        :return: A list of words to write to disk
        :rtype: List[str]
        """
        list_ = [self.card, *[str(n) for n in self.nodes]]
        list_[-1] = f'-{list_[-1]}'
        if self.name is not None:
            list_.append(self.name)
        return list_
