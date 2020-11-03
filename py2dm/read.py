"""Implementation of the mesh reading interface.

This module defines the :class:`py2dm.Reader` interface.

"""

import abc
import enum
from types import TracebackType
from typing import Any, ClassVar, Iterator, Optional, Type

from .entities import Element, Node, NodeString

try:
    from typing import Literal
except ModuleNotFoundError as err:
    # Required for compatibilty with Python 3.7 (used in QGIS 3)
    try:
        from typing_extensions import Literal  # type: ignore
    except ModuleNotFoundError:
        raise err from err

__all__ = [
    'Reader',
    'ReadMode'
]


class ReadMode(enum.Enum):
    """Enumerator for different file reading strategies.

    These modes alter the way the :class:`py2dm.Reader` class accesses
    the underlying file data. Depending on the application and mesh
    size, specifying a different file reading strategy can lead to
    significant improvements or degradations in performance.

    For more information on which modes are better suited for a given
    application, refer to the [Optimisation] section of the project
    documentation.

    Attributes:
        MEMORY: The entire mesh is loaded at once, and the object
            representations of all nodes and elements are stored in
            memory.

            This minimises random access times, but also consumes a lot
            of memory in the process, which in turn can lead to poor
            system performance or instability.

        BATCHED: Mesh data is retrieved in batches of a given size as
            specified by the :attr:`py2dm.Reader.batch_size` argument.
            The beginning of each batch is cached, allowing for
            retrieval of a given node or element by matching its ID to
            its associated batch. Separate batches are created for
            nodes and elements.

            This mode provides a good balance of random read speeds and
            memory usage, particularly when there is some correlation
            between access order and entity IDs, as entities with
            similar IDs are likely to be stored in the same batch.

        LAZY: This mode keeps the entire mesh on disk and reads single
            lines of data as required. When retrieving objects by ID,
            a binary-search is performed to identify the corresponding
            line of data.

            This mode minimises memory usage and is recommended for
            extremely large files, but is heavily bottlenecked by the
            seek and read speeds of the storage medium used.

    """

    MEMORY = 10
    BATCHED = 20
    LAZY = 30


class Reader(metaclass=abc.ABCMeta):
    """Reader interface specification and class factory.

    This class acts as the ABC defining the endpoints available for all
    of its subclasses regardless of implementation.

    It also acts as a factory method for retrieving the corresponding
    subclass by mode:

    .. code-block:: python

        >>> reader = py2dm.Reader('mesh.2dm', mode=ReadMode.LAZY)
        >>> type(reader)
        <class 'py2dm.read.LazyReader'>

    Subclasses are only meant to implement the abstract methods of this
    ABC. The only tags they are responsible for are nodes, elements and
    node strings. Everything else (metadata, mesh names, node or
    element count, etc.) is handled by the :class:`py2dm.Reader` class.

    """

    # This attribute is used by subclasses to indicate which ReadMode they
    # correspond to
    _mode: ClassVar[Optional[ReadMode]] = None

    def __init__(self, filepath: str, validate: bool = True) -> None:
        """Initialise the mesh reader.

        This opens the underlying file and preloads metadata for the
        mesh.

        Arguments:
            filepath: The path of the mesh file to read.
            validate (optional): Whether to check the mesh for
                inconsistencies and other issues. Disabling this may
                slightly improve performance when opening large meshes.
                Defaults to True.

        """
        self._file = open(filepath)
        self._filepath = filepath
        if validate:
            self._validate()

    def __new__(cls, *args: Any, mode: ReadMode = ReadMode.BATCHED,
                **kwargs: Any) -> 'Reader':
        """Return a new :class:`py2dm.Reader` instance.

        If `mode` has been set to a value other than ``None``, this
        method will act as a factory method dispensing the appropriate
        subclass of the :class:`py2dm.Reader` interface.

        Arguments:
            mode (optional): The read mode to use. This controls which
                subclass of :class:`py2dm.Reader` will be returned.
                Defaults to :attr:`py2dm.ReadMode.BATCHED`.

        Raises:
            ValueError: Raised if the given `mode` does not match any
                subclass of :class:`py2dm.Reader`.

        Returns:
            A subclass of :class:`py2dm.Reader` if the `mode` argument
            has been set to a value other than ``None``, or a regular
            object instance as per the default implementation of
            :meth:`object.__new__()`.

        """
        if cls == Reader:
            for subclass in cls.__subclasses__():
                if subclass._mode == mode:
                    return subclass(*args, **kwargs)
            raise ValueError(
                f'No subclass registered for read mode \'{mode}\'')
        # NOTE: A mode of None is reserved to allow propagation of this call to
        # the default object constructor, since this method has to act work as
        # both the factory and as part of the regular object instantiation MRO.
        instance: 'Reader' = super().__new__(cls)
        return instance

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
        self.close()
        return False

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

    def close(self) -> None:
        """Close the mesh reader.

        This closes the underlying text file and discards any cached
        objects or metadata. The instance will become unusable after
        this call.

        .. note::

            This method is called automatically when using the class
            via the context manager.

        """
        if not self._file.closed:
            self._file.close()

    @abc.abstractmethod
    def get_element(self, id_: int) -> Element:
        """Return a mesh element by its unique ID.

        Arguments:
            id_: The ID of the element to return.

        Raises:
            IndexError: Raised if the given `id_` is negative or
                exceeds the number of elements in the mesh.

        Returns:
            The element matching the given ID.

        """
        ...

    @abc.abstractmethod
    def get_node(self, id_: int) -> Node:
        """Return a mesh node by its unique ID.

        Arguments:
            id_: The ID of the node to return.

        Raises:
            IndexError: Raised if the given `id_` is negative or
                exceeds the number of nodes in the mesh.

        Returns:
            The node matching the given ID.

        """
        ...

    @abc.abstractmethod
    def iter_elements(self, start: int = -1,
                      end: int = -1) -> Iterator[Element]:
        """Iterate over the mesh elements.

        Arguments:
            start (optional): The starting element ID. If negative, the
                first element in the mesh (i.e. 0 or 1) will be used.
                Defaults to ``-1``.
            end (optional): The end element ID (exclusive). If
                negative, continues until the list of elements is
                exhausted. Defaults to ``-1``.

        Raises:
            IndexError: Raised if the `end` ID is less than or equal to
                the `start` ID.

        Yields:
            Mesh elements from the given range of IDs.

        """
        ...

    @abc.abstractmethod
    def iter_nodes(self, start: int = -1, end: int = -1) -> Iterator[Node]:
        """Iterate over the mesh elements.

        If the `end` ID is less than the `start` ID, the IDs will be
        traversed in reverse order.

        Arguments:
            start (optional): The starting node ID. If negative, the
                first node in the mesh (i.e. ID 0 or 1) will be used.
                Defaults to ``-1``.
            end (optional): The end node ID (exclusive). If negative,
                continues until the list of nodes is exhausted.
                Defaults to ``-1``.

        Raises:
            IndexError: Raised if the `end` ID is less than or equal to
                the `start` ID.

        Yields:
            Mesh nodes from the given range of IDs.

        """
        ...

    @abc.abstractmethod
    def iter_node_strings(self) -> Iterator[NodeString]:
        """Iterate over the mesh node strings.

        Yields:
            Mesh node strings in order of definition.

        """
        ...

    def _validate(self) -> None:
        """Check the mesh file for issues and incompatibilities."""
        # TODO: Implement 'Reader._validate()'
