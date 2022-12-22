==================
Writing mesh files
==================

To write a 2DM mesh file, instantiate a :class:`py2dm.Writer` object.

As with :class:`py2dm.Reader`, the preferred way to do this is via a context manager. This ensures the file is written and closed properly after writing.

Basic usage
===========

You can add geometries to the mesh using the :meth:`py2dm.Writer.element`, :meth:`py2dm.Writer.node`, and :meth:`py2dm.Writer.node_string` methods.

These methods support two modes. In the first, the target object is instantiated first and passed to the method as a finished instance:

.. code-block:: python3

   with py2dm.Writer('path/to/mesh.2dm') as mesh:
      my_node = py2dm.Node(1, 25.0, 20.0, 5.0)
      ...
      mesh.node(my_nodes)

This is the recommended mode when using Py2DM objects as your main data type, such as when copying entities across files or when merging two files.

.. note::

   Any mutable lists are deep copied when passing a class instance to any of these methods. There is no danger of unintentional mutation of an object's data after it was passed to this method.

Alternatively, all the above methods also support a factory interface, where the values passed are forwarded directly to the corresponding object constructor:

.. code-block:: python3

   with py2dm.Writer('path/to/mesh.2dm') as mesh:
      mesh.node(1, 25.0, 20.0, 5.0)

When creating elements via the factory pattern, you must also specify the class or 2DM card of the element type to create:

.. code-block:: python3

   with py2dm.Writer('path/to/mesh.2dm') as mesh:
      mesh.element('E3T', 1, 1, 2, 3)
      # Or, alternatively:
      mesh.element(py2dm.Element3T, 2, 3, 2, 4)

Automatically assigned IDs
--------------------------

The :meth:`py2dm.Writer.node` and :meth:`py2dm.Writer.element` methods both allow passing negative integers as IDs, in which case the ID will be determined based on the number of existing nodes/elements in the mesh. The assigned ID is then returned:

.. code-block:: python3

   with py2dm.Writer('path/to/mesh.2dm') as mesh:
      mesh.node(-1, -1.0, 1.0, 0.0)  # returns 1
      mesh.node(-1, 1.0, -1.0, 0.0)  # returns 2
      mesh.node(-1, 1.0, 1.0, 0.0)  # returns 3
      mesh.element('E3T', -1, 1, 2, 3)  # returns 1

Writing chunks
==============

The :meth:`py2dm.Writer.element`, :meth:`py2dm.Writer.node`, and :meth:`py2dm.Writer.node_string` methods do not commit any changes to disk. Instead, they write the elements to an internal cache that is later written to disk in a single chunk.

When the :class:`py2dm.Writer` class's context manager is existed, this is done automatically. Until then, the entire node and element list is cached in memory.

For small meshes (<100'000 elements), this is not a problem. However, for larger meshes it may be preferable to write the file in chunks of a few thousand entities (i.e. rows) at a time.

To do this, the :class:`py2dm.Writer` class provides the :meth:`py2dm.Writer.flush_elements`, :meth:`py2dm.Writer.flush_nodes`, and :meth:`py2dm.Writer.flush_node_strings` methods respectively, which allow committing the cache to disk, freeing up its memory:

.. code-block:: python3
   :emphasize-lines: 10-11

   import random
   import py2dm

   def random_point(scale):
     return tuple((random.random()*scale for _ in range(3)))

   with py2dm.Reader('path/to/mesh.2dm') as mesh:
      for i in range(1_000_000):
        mesh.node(-1, *random_point())
        if i % 10_000 == 0:
         mesh.flush_nodes()
      ...

This is particularly useful when converting large files from other formats, since both the read and write operations can be done without loading either file into memory completely.

.. important::

   When writing files in chunks, it is not possible to intermix entity types. This is due to the node and element ID ranges needing to be consecutive blocks in the file.
   
   If you already committed nodes to a file and write any elements or node strings, you can no longer add any new nodes without an error being raised (and vice-versa).

Writer class interface
======================

.. autoclass:: py2dm.Writer()
   
   .. automethod:: __init__(filepath: str, **kwargs) -> None

   .. autoattribute:: name

   .. autoproperty:: closed

   .. autoproperty:: materials_per_element

   .. autoproperty:: num_elements

   .. autoproperty:: num_nodes

   .. autoproperty:: num_node_strings

   .. automethod:: close() -> None

   .. automethod:: open() -> None

   .. method:: element(element: py2dm.Element) -> int

   .. automethod:: element(element: type[py2dm.Element] | str, id_: int, *nodes: int, materials: tuple[int | float, ...] = None) -> int
      :noindex:

   .. method:: node(node: py2dm.Node) -> int

   .. automethod:: node(node: int, x: float, y: float, z: float) -> int
      :noindex:

   .. method:: node_string(node_string: py2dm.NodeString) -> int

   .. automethod:: node_string(node_string: int, *nodes: int, name: Union[str, None] = None) -> int
      :noindex:

   .. automethod:: flush_elements(**kwargs) -> None

   .. automethod:: flush_nodes(**kwargs) -> None

   .. automethod:: flush_node_strings(**kwargs) -> None

   .. automethod:: write_header(signature: str = '') -> None
