"""Implementation of the mesh writing interface.

This module defines the :class:`py2dm.Writer` class. Unlike with
readers, this currently only provides a main reference implementation,
without any base class interfaces.
"""

import copy
import os
from types import TracebackType
from typing import Any, Dict, IO, List, Optional, Tuple, Type, Union, cast, overload
import warnings

from ._entities import Entity, Element, Node, NodeString, element_factory
from .errors import FileIsClosedError, Py2DMWarning, WriteError
from ._typing import Literal

__all__ = [
    'Writer'
]

_MeshObject = Union[Entity, NodeString]


class Writer:
    """Py2DM writer class used to validate and write 2DM files.

    Any elements are initially written to memory and only get committed
    to disk once the writer is closed or one of the ``flush_*()``
    methods is called.

    :param filepath: Path to the mesh file to write.
    :type filepath: :class:`str`
    """

    def __init__(self, filepath: str, **kwargs: Any) -> None:
        self.name = 'Unnamed mesh'
        """Display name of the mesh.

        A custom name to store in the mesh to aid with identification.
        Can be written to disk as part of a :meth:`write_header` call.

        :type: :class:`str`
        """
        self._closed: bool = True
        self._filepath = filepath
        self._file: IO[str]
        self._num_materials = int(kwargs.get('materials', -1))
        self._float_materials = bool(kwargs.get('allow_float_matid', True))
        self._zero_index = bool(kwargs.get('zero_index', False))
        self._count: Dict[Type[_MeshObject], int] = {
            Element: 0, Node: 0, NodeString: 0}
        self._cache: Dict[Type[_MeshObject], List[_MeshObject]] = {
            Element: [], Node: [], NodeString: []}
        self._write_history: List[str] = []

    def __enter__(self) -> 'Writer':
        self.open()
        return self

    def __exit__(self, exc_type: Optional[Type[BaseException]],
                 exc_value: Optional[BaseException],
                 exc_tb: Optional[TracebackType]) -> Literal[False]:
        _ = exc_type, exc_value, exc_tb
        self.close()
        return False

    def __str__(self) -> str:
        if self._closed:
            return 'Py2DM Writer (closed)'
        return ('Py2DM Writer\n'
                f'\t({os.path.basename(self._filepath)})\n'
                f'\t{self.num_nodes} nodes\n'
                f'\t{self.num_elements} elements\n'
                f'\t{self.num_node_strings} node strings')

    @property
    def closed(self) -> bool:
        """Return whether the underlying file is closed.

        After closing (either via the :meth:`close` method or by
        leaving the reader's context manager), any operations requiring
        use of the underlying file will raise a
        :exc:`py2dm.errors.FileIsClosedError`.

        :type: :class:`bool`
        """
        return self._closed

    @property
    def materials_per_element(self) -> int:
        """Number of materials per element.

        This value can be specified via the `materials` keyword as part
        of the :class:`Writer` class's initialiser, or it will be
        inferred from the first element passed. When
        :meth:`write_header` is called with no elements added, the
        number of elements is additionally initialised to zero.

        Once set, this value can not be modified. Errors will be raised
        for elements with fewer materials than required, and extraneous
        materials will be stripped as part of the :meth:`element`
        method.

        When writing the mesh to disk, this value will be stored in the
        ``NUM_MATERIALS_PER_ELEM <count>`` card at the top of the file.

        :type: :class:`int`
        """
        self._require_open()
        return self._num_materials

    @property
    def num_elements(self) -> int:
        """Return the number of elements in the mesh.

        :type: :class:`int`
        """
        self._require_open()
        return self._count[Element]

    @property
    def num_nodes(self) -> int:
        """Return the number of nodes in the mesh.

        :type: :class:`int`
        """
        self._require_open()
        return self._count[Node]

    @property
    def num_node_strings(self) -> int:
        """Return the number of node strings in the mesh.

        :type: :class:`int`
        """
        self._require_open()
        return self._count[NodeString]

    def close(self) -> None:
        """Close the mesh reader.

        This commits any pending data to disk and closes the underlying
        text file. The instance will become unusable after this call.

        .. note::

            This method is called automatically when using the class
            via the context manager.
        """
        if self.closed:
            return
        if 'header' not in self._write_history:
            if self._write_history:
                raise RuntimeError('')
            self.write_header()
            self._write_history.append('header')
        last = self._write_history[-1]
        if last == 'node string':
            self.flush_node_strings()
        elif last == 'node':
            self.flush_nodes()
        elif last == 'element':
            self.flush_elements()
        if self._cache[Node]:
            self.flush_nodes()
        if self._cache[Element]:
            self.flush_elements()
        if self._cache[NodeString]:
            self.flush_node_strings()
        self._file.close()
        self._closed = True

    def open(self) -> None:
        """Open the mesh reader.

        This performs the initial metadata read and sets up the class
        for continued access.

        When calling this function manually, be sure to call
        :meth:`close` once you no longer require file access.
        Alternatively, you can use the context manager interface, in
        which case both methods will be called automatically.
        """
        self._file = open(self._filepath, 'w')
        self._closed = False

    @overload
    def element(self, element: Element) -> int:
        """Add an element to the mesh.

        In this overload, a deep copy is created of the given `element`
        and added to the mesh.

        If the ID of the element is negative, one will be selected
        automatically based on the number of existing elements.

        :param element: The instance or type of element to add.
        :type element: :class:`py2dm.Element`
        :raises TypeError: Raised when extra arguments are passed while
            also passing a :class:`py2dm.Element` instance.
        :return: The ID of the element that was added.
        :rtype: :class:`int`
        """

    @overload
    def element(self, element: Union[Type[Element], str], id_: int,
                *nodes: int, materials: Tuple[Union[int, float], ...] = ...
                ) -> int:
        r"""Add an element to the mesh.

        In this overload, this method acts as a factory, with the
        `element` field being either the subclass to instantiate or the
        name of the 2DM card of the element. Any extra arguments are
        passed on to the class's initialiser.

        If the ID of the element is negative, one will be selected
        automatically based on the number of existing elements.

        :param element: The type of element to add.
        :type element: :obj:`typing.Union` [
            :obj:`typing.Type` [:class:`py2dm.Element`], :class:`str`]
        :param id_: The ID of the element.
        :type id_: :class:`int`
        :param \*nodes: The IDs of the nodes belonging to this element.
        :type \*nodes: :class:`int`
        :param materials: A tuple of material IDs for the element.
        :type materials: obj:`typing.Tuple` [:obj:`typing.Union` [
            :class:`int`, :class:`float`]]
        :return: The ID of the element that was added.
        :rtype: :class:`int`
        """

    def element(self, element: Union[Element, Type[Element], str],
                *args: Any, **kwargs: Any) -> int:
        r"""Add an element to the mesh.

        If `element` is an instance of a :class:`Element` subclass, a
        deep copy will be created. In this case, no other arguments may
        be passed.

        Alternatively, this method can be used as a factory, with the
        `element` field being either the subclass to instantiate or the
        name of the 2DM card of the element. When using the factory,
        any extra arguments are passed on to the class's initialiser.
        Refer to the docstring of the respective class for supported
        arguments.

        If the ID of the element is negative, one will be selected
        automatically based on the number of existing elements.

        :param element: The instance or type of element to add.
        :type element: :obj:`typing.Union` [:class:`py2dm.Element`,
            :obj:`typing.Type` [:class:`py2dm.Element`], :class:`str`]
        :param \*args: Extra arguments to forward to the class's
            initialiser.
        :type \*args: :obj:`typing.Any`
        :param \*\*kwargs: Extra keyword arguments to forward to the
            class's initialiser.
        :type \*\*kwargs: :obj:`typing.Any`
        :raises TypeError: Raised when extra arguments are passed while
            also passing a :class:`py2dm.Element` instance.
        :return: The ID of the element that was added.
        :rtype: :class:`int`
        """
        self._require_open()
        self._check_flush_state('element')
        if isinstance(element, Element):
            element = copy.deepcopy(element)
            if args or kwargs:
                raise TypeError(
                    'No extra arguments supported when providing an instance')
        else:
            if isinstance(element, str):
                element = element_factory(element)
            element = element(*args, **kwargs)
        if element.id < 0:
            element.id = self.num_elements - self._zero_index + 1
        if self._num_materials < 0:
            self._num_materials = element.num_materials
        elif element.num_materials < self._num_materials:
            raise ValueError(f'Mesh requires {self._num_materials} elements, '
                             f'element has {element.num_materials}')
        elif element.num_materials > self._num_materials:
            warnings.warn(
                f'{len(element.materials)-self._num_materials} extraneous '
                'materials were removed (mesh material count is set to '
                f'{self._num_materials})', Py2DMWarning)
            element.materials = element.materials[:self._num_materials]
        if not self._float_materials:
            for material in element.materials:
                if not isinstance(material, int):
                    raise ValueError('Mesh only accepts integer materials')
        self._cache[Element].append(element)
        self._count[Element] += 1
        return element.id

    @overload
    def node(self, node: Node) -> int:
        """Add a node to the mesh.

        In this overload, a deep copy is created of the given `node`
        and added to the mesh.

        If the ID of the node is negative, one will be selected
        automatically based on the number of existing nodes.

        :param node: The node instance to add.
        :type node: :class:`py2dm.Node`
        :raises TypeError: Raised when extra arguments are passed while
            also passing a :class:`py2dm.Node` instance.
        :return: The ID of the node that was added.
        :rtype: :class:`int`
        """

    @overload
    # pylint: disable=invalid-name
    def node(self, node: int, x: float, y: float, z: float) -> int:
        """Add a node to the mesh.

        In this overload, this method acts as a factory, with the
        `node` field being used for the ID of the node to create. Any
        extra arguments are passed on to the :class:`py2dm.Node`
        initialiser. Refer to its docstring for supported arguments.

        If the ID of the node is negative, one will be selected
        automatically based on the number of existing nodes.

        :param node: The ID of the node to create.
        :type node: :class:`int`
        :param x: X coordinate of the node.
        :type x: :class:`float`
        :param y: Y coordinate of the node.
        :type y: :class:`float`
        :param z: Z coordinate of the node.
        :type z: :class:`float`
        :return: The ID of the node that was added.
        :rtype: :class:`int`
        """

    def node(self, node: Union[Node, int], *args: Any, **kwargs: Any) -> int:
        r"""Add a node to the mesh.

        If `node` is an instance of :class:`Node`, a deep copy will be
        created. In this case, no other arguments may be passed.

        Alternatively, this method can be used as a factory, with the
        `node` field being used for the ID of the node to create. When
        using the factory, any extra arguments are passed on to the
        :class:`py2dm.Node` initialiser. Refer to its docstring for
        supported arguments.

        If the ID of the node is negative, one will be selected
        automatically based on the number of existing nodes.

        :param node: The node instance to add, or the ID of the node to
            create.
        :type node: :obj:`typing.Union` [
            :class:`py2dm.Node`, :class:`int`]
        :param \*args: Extra arguments to forward to the
            :class:`py2dm.Node` initialiser.
        :type \*args: :obj:`typing.Any`
        :param \*\*kwargs: Extra keyword arguments to forward to the
            :class:`py2dm.Node` initialiser.
        :type \*\*kwargs: :obj:`typing.Any`
        :raises TypeError: Raised when extra arguments are passed while
            also passing a :class:`py2dm.Node` instance.
        :return: The ID of the node that was added.
        :rtype: :class:`int`
        """
        self._require_open()
        self._check_flush_state('node')
        if isinstance(node, Node):
            node = copy.deepcopy(node)
            if args or kwargs:
                raise TypeError(
                    'No extra arguments supported when providing an instance')
        else:
            node = Node(node, *args, **kwargs)
        if node.id < 0:
            node.id = self.num_nodes - self._zero_index + 1
        self._cache[Node].append(node)
        self._count[Node] += 1
        return node.id

    @overload
    def node_string(self, node_string: NodeString) -> int:
        r"""Add a node string to the mesh.

        In this overload, a deep copy is created of the given
        `node_string` and added to the mesh.

        :param node_string: The node string instance to add.
        :type node: :class:`py2dm.NodeString`
        :raises TypeError: Raised when extra arguments are passed while
            also passing a :class:`py2dm.NodeString` instance.
        :return: The zero-based index of the node string in the mesh's
            list of node strings.
        :rtype: :class:`int`
        """

    @overload
    def node_string(self, node_string: int,
                    *nodes: int, name: Optional[str] = ...) -> int:
        r"""Add a node string to the mesh.

        In this overload, this method acts as a factory, with the
        `node_string` field being used for the first node ID in the
        string. Any extra arguments are passed on to the
        class:`py2dm.NodeString` initialiser.

        :param node_string: The ID of the first node for the node
            string to create.
        :type node: :class:`int`
        :param \*nodes: Additional node IDs to include in the node
            string.
        :type \*nodes: :class:`int`
        :param name: An optional name for the node string.
        :type name: :obj:`typing.Optional` [:class:`str`]
        :return: The zero-based index of the node string in the mesh's
            list of node strings.
        :rtype: :class:`int`
        """

    def node_string(self, node_string: Union[NodeString, int],
                    *args: Any, **kwargs: Any) -> int:
        r"""Add a node string to the mesh.

        If `node_string` is an instance of :class:`NodeString`, a deep
        copy will be created. In this case, no other arguments may be
        passed.

        Alternatively, this method can be used as a factory, with the
        `node_string` field being used for the first node ID in the
        string. When using the factory, any extra arguments are passed
        on to the :class:`py2dm.NodeString` initialiser. Refer to its
        docstring for supported arguments.

        :param node_string: The node string instance to add, or the ID
            of the first node for the node string to create.
        :type node: :obj:`typing.Union` [
            :class:`py2dm.NodeString`, :class:`int`]
        :param \*args: Extra arguments to forward to the
            :class:`py2dm.NodeString` initialiser.
        :type \*args: :obj:`typing.Any`
        :param \*\*kwargs: Extra keyword arguments to forward to the
            :class:`py2dm.NodeString` initialiser.
        :type \*\*kwargs: :obj:`typing.Any`
        :raises TypeError: Raised when extra arguments are passed while
            also passing a :class:`py2dm.NodeString` instance.
        :return: The zero-based index of the node string in the mesh's
            list of node strings.
        :rtype: :class:`int`
        """
        self._require_open()
        self._check_flush_state('node string')
        if isinstance(node_string, NodeString):
            node_string = copy.deepcopy(node_string)
            if args or kwargs:
                raise TypeError(
                    'No extra arguments supported when providing an instance')
        else:
            node_string = NodeString(node_string, *args, **kwargs)
        self._cache[NodeString].append(node_string)
        self._count[NodeString] += 1
        return self._count[NodeString]

    def flush_elements(self) -> None:
        """Write the local element cache to disk.

        This clears out the in-memory element cache and writes its
        contents to disk. This method is called automatically when the
        :class:`Writer` is closed.
        """
        self._require_open()
        if 'header' not in self._write_history:
            self.write_header()
        self._check_flush_state('element')
        # TODO: Add support for float material formats
        self._file.writelines(
            (f'{" ".join(e.to_line())}\n'
             for e in cast(List[Element], self._cache[Element])))
        self._update_flush_state('element')
        self._cache[Element].clear()

    def flush_nodes(self) -> None:
        """Write the local node cache to disk.

        This clears out the in-memory node cache and writes its
        contents to disk. This method is called automatically when the
        :class:`Writer` is closed.
        """
        self._require_open()
        if 'header' not in self._write_history:
            self.write_header()
        self._check_flush_state('node')
        # TODO: Add support for coordinate formats
        self._file.writelines(
            (f'{" ".join(n.to_line())}\n'
             for n in cast(List[Node], self._cache[Node])))
        self._update_flush_state('node')
        self._cache[Node].clear()

    def flush_node_strings(self) -> None:
        """Write the local node string cache to disk.

        This clears out the in-memory node string cache and writes its
        contents to disk. This method is called automatically when the
        :class:`Writer` is closed.
        """
        self._require_open()
        if 'header' not in self._write_history:
            self.write_header()
        self._check_flush_state('node string')
        # TODO: Add support for line folding
        self._file.writelines(
            (f'{" ".join(n.to_line())}\n'
             for n in cast(List[NodeString], self._cache[NodeString])))
        self._update_flush_state('node string')
        self._cache[NodeString].clear()

    def write_header(self, signature: str = '') -> None:
        """Write the header of the 2DM file.

        This writes the initial ``MESH2D`` format identifier, as well
        as the ``NUM_MATERIALS_PER_ELEM`` field.

        The optional `signature` argument allows specifying a custom
        string to append to the initial line in the form of a comment.
        This string may contain newlines.

        :param signature: An authoring signature to include.
        :type signature: :class:`str`
        """
        self._require_open()
        if self._write_history:
            raise WriteError('Header must be written on top of document')
        self._file.write('MESH2D')
        if signature:
            self._file.write(' ')
            self._file.writelines(
                (f'# {l}\n' for l in signature.splitlines()))
        else:
            self._file.write('\n')
        if self._num_materials < 0:
            self._num_materials = 0
        self._file.write(f'NUM_MATERIALS_PER_ELEM {self._num_materials}\n')
        self._write_history.append('header')

    def _check_flush_state(self, type_: str) -> None:
        """Check whether writing the given type is permitted.

        :param type_: A unique identifier for the entity.
        :type type_: :class:`str`
        :raises py2dm.errors.WriteError: Raised if `type_` has been
            written before and other types of entities have been
            written since.
        """
        if (self._write_history and self._write_history[-1] != type_
                and type_ in self._write_history):
            last_ = self._write_history[-1]
            raise WriteError(
                'Entities must be written in blocks, not interleaved '
                f'(found {type_}-{last_}-{type_} sequence)')

    def _require_open(self) -> None:
        """Check whether the underlying file is open.

        :raises py2dm.errors.FileIsClosedError: Raised if the
            underlying has already been closed, either via the
            :meth:`close` method or by leaving the body of the
            context manager.
        """
        if self._closed:
            raise FileIsClosedError(self._filepath)

    def _update_flush_state(self, type_: str) -> None:
        """Update the flush state, if required.

        This will set the given `type_` as the last flushed type if
        not already set.

        :param type_: A unique identifier for the entity.
        :type type_: :class:`str`
        """
        if not self._write_history or self._write_history[-1] != type_:
            self._write_history.append(type_)
