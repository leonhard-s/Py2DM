"""Writer class."""

import math
from types import TracebackType
from typing import IO, List, Optional, Tuple, Type
from typing_extensions import Literal

from .entities import Element, Node, NodeString
from .types import MaterialIndex


class Writer:
    """In-place file writer for 2DM mesh files.

    This class can be used with context managers to implicitly open and
    close the mesh file. This is the recommended option when writing
    large (>50k elements) mesh files.

    Note that the element order in the result file will depend on the
    insertion order.

    :param filepath: The 2DM mesh file to create
    :type filepath: str
    :param signature: A comment to append to the first line of the file
    :type signature: str, optional
    """

    def __init__(self, filepath: str, signature: Optional[str] = None) -> None:
        self._file: Optional[IO[str]] = None
        self._filepath = filepath
        self._signature = signature
        self._nmpe = 1
        self.nodes: List[Node] = []
        self.elements: List[Element] = []
        self.node_strings: List[NodeString] = []

    def __enter__(self) -> 'Writer':
        self.open()
        return self

    def __exit__(self, exc_type: Optional[Type[BaseException]],
                 exc_value: Optional[BaseException],
                 exc_tb: Optional[TracebackType]) -> Literal[False]:
        if self._file is not None:
            self.close()
        return False

    def __repr__(self) -> str:
        string = (f'2DM Writer ({self._filepath})\n'
                  f'  {len(self.nodes)} nodes\n'
                  f'  {len(self.elements)} elements\n'
                  f'  {len(self.node_strings)} node strings')
        num_materials = self._nmpe
        if num_materials > 0:
            plural = 's' if num_materials > 1 else ''
            string += f'\n {num_materials} material{plural} per element'
        return string

    def close(self) -> None:
        """Close the associated mesh file.

        You only have to call this yourself if you opened the file
        using :meth:`open`. The context manager will do this
        automatically.
        """
        if self._file is not None:
            self._file.close()

    def element(self, type_: Type[Element], nodes: Tuple[int, ...],
                materials: Optional[Tuple[MaterialIndex, ...]] = None) -> int:
        """Create a new node at the given position.

        This will always create a new element, even if one already
        exists at this location.

        :param type_: The type of element to create
        :type type_: Type[:class:`~py2dm.entities.Element`]
        :param nodes: The nodes to create the element from
        :type nodes: Tuple[int, ...]
        :param materials: Material indices for this element, defaults
            to ``None``
        :type materials: Union[int, float], optional
        :return: The ID of the created element
        :rtype: int
        """
        id_ = len(self.elements) + 1
        self.elements.append(type_(id_, *nodes, materials=materials))
        return id_

    def find_node(self, pos_x: float, pos_y: float, pos_z: float
                  ) -> Optional[Node]:
        """Return the node at the given position, if any.

        This performs an exact check, be wary of floating point errors.

        Note that this might have to scan every recorded node before
        returning, which  makes this a fairly expensive operation for
        very large meshes.

        :param x: X position of the node to return
        :type x: float
        :param y: Y position of the node to return
        :type y: float
        :param z: Z position of the node to return
        :type z: float
        :return: The node with the given position, or ``None``
        :rtype: Optional[Node]
        """
        for node in self.nodes:
            if node.pos == (pos_x, pos_y, pos_z):
                return node
        return None

    def node(self, pos_x: float, pos_y: float, pos_z: float) -> int:
        """Create a new node at the given position.

        This will always create a new node, even if one already exists
        at this location. Use :meth:`find_node` to check if a node
        already exists at a location.

        :param x: X position of the node to create
        :type x: float
        :param y: Y position of the node to create
        :type y: float
        :param z: Z position of the node to create
        :type z: float
        :return: The ID of the created node
        :rtype: int
        """
        id_ = len(self.nodes) + 1
        self.nodes.append(Node(id_, pos_x, pos_y, pos_z))
        return id_

    def node_string(self, nodes: Tuple[int, ...], name: Optional[str] = None
                    ) -> None:
        """Create a new node string from the given node IDs.

        :param nodes: The node to create the node string from
        :type nodes: Tuple[int, ...]
        :param name: An optional name to append to the mesh. This
            argument should be considered deprecated by design and will
            likely be removed in upcoming versions.
        :type name: Optional[str]
        """
        self.node_strings.append(NodeString(*nodes, name=name))

    def num_materials_per_elem(self, value: int) -> None:
        """Set the number of materials per element for the mesh.

        :param value: Number of materials
        :type value: int
        """
        self._nmpe = value

    def open(self) -> IO[str]:
        """Open the mesh file to write.

        Note that the preferred way of accessing mesh files is vai the
        context manager interface.
        If you use the manual method, it is your responsibility to call
        :meth:`close` via a try block or other catching mechanism.

        :return: The file-like object returned
        :rtype: IO[str]
        """
        self._file = open(self._filepath, 'w')
        return self._file

    def _require_open(self) -> None:
        """Utility method for requiring the current file to be open."""
        if self._file is None:
            raise RuntimeError('Writer has not been opened')

    def write(self) -> None:
        """Helper function for writing meshes in default node order.

        This calls :meth:`write_header`, :meth:`write_nodes`,
        :meth:`write_elements`, and :meth:`write_node_strings` in
        order.
        """
        self.write_header()
        self.write_nodes()
        self.write_elements()
        self.write_node_strings()

    def write_elements(self) -> None:
        """Write all elements registered."""
        node_col = int(math.log10(len(self.nodes))) + 1
        ele_col = int(math.log10(len(self.elements))) + 1
        if self._nmpe > 0:
            matid_col = int(math.log10(self._nmpe)) + 1
        for element in self.elements:
            columns = (3, ele_col, *(node_col,)*element.num_nodes)
            if self._nmpe > 0:
                columns = *columns, *(matid_col,)*self._nmpe
            self._write_line(element.to_list(), columns=columns)

    def write_header(self) -> None:
        """Write the 2DM file header.

        This includes the two required tags MESH2D and
        NUM_MATERIALS_PER_ELEM.
        """
        self._require_open()
        assert self._file is not None
        self._file.write('MESH2D')
        if self._signature is not None:
            self._file.write(f' # {self._signature}')
        self._file.write(f'\nNUM_MATERIALS_PER_ELEM {self._nmpe}\n')

    def _write_line(self, line: List[str],
                    columns: Optional[Tuple[int, ...]] = None) -> None:
        """Print a single line to the output file.

        :param line: The list of words to write
        :type line: List[str]
        :param columns: Minimum column width for each written word,
            defaults to None
        :type columns: Tuple[int, ...], optional
        :raises ValueError: Raised if the columns tuple length does not
            match the input list length
        """
        self._require_open()
        assert self._file is not None
        if columns is not None:
            if len(line) != len(columns):
                raise ValueError(
                    f'Sequence length mismatch: line has {len(line)} items, '
                    f'columns has {len(columns)}')
            for index, word in enumerate(line):
                line[index] = word.rjust(columns[index])
        string = ' '.join(line)
        self._file.write(f'{string}\n')

    def write_node_strings(self) -> None:
        """Write all node strings registered."""
        for node_string in self.node_strings:
            line = node_string.to_list()
            self._write_line(line)

    def write_nodes(self) -> None:
        """Write all nodes registered."""
        node_col = int(math.log10(len(self.nodes))) + 1
        columns = (2, node_col, 0, 0, 0)
        for node in self.nodes:
            self._write_line(node.to_list(), columns=columns)
