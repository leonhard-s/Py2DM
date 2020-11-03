"""Implementation of the mesh reading interface."""

import enum


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
            specified by the :attr:`Reader.batch_size` argument. The
            beginning of each batch is cached, allowing for retrieval
            of a given node or element by matching its ID to its
            associated batch. Separate batches are created for nodes
            and elements.

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
