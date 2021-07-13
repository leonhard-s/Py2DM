==================
Reading mesh files
==================

To read a 2DM mesh file, instantiate a :class:`py2dm.Reader` and pass it the path of the 2DM file to read.

The preferred way to use this class is via the context manager interface:

.. code-block:: python3

   >>> with py2dm.Reader('path/to/mesh.2dm') as mesh:
   ...   print(mesh)
   ...
   Py2DM Reader
      5 nodes
      4 elements
      2 node strings

Basic usage
===========

Metadata
--------

The :class:`py2dm.Reader` class exposes properties for the node, element, node string, and element material count of a mesh via its :attr:`num_* <py2dm.Reader.num_elements>` and :attr:`~py2dm.Reader.materials_per_element` properties.

Additionally, the :attr:`py2dm.Reader.extent` property allows finding the extreme X and Y values of a mesh. While this method is expensive for large meshes as it checks the entire list of nodes, it is also cached, meaning that subsequent calls will reuse the first value:

.. code-block:: python3

   with py2dm.Reader('path/to/mesh.2dm') as mesh:

      start = time.time()
      _ = mesh.extent
      print(time.time() - start)  # ~1.6 seconds

      start = time.time()
      _ = mesh.extent
      print(time.time() - start)  # ~0.0 seconds

Sequential access
-----------------

When retrieving mesh entities in bulk, it is generally recommended to use the iterator factory methods :meth:`py2dm.Reader.iter_nodes`, :meth:`py2dm.Reader.iter_elements`, and :meth:`py2dm.Reader.iter_node_strings`.

As a shorthand, you can also use the :attr:`py2dm.Reader.nodes`, :attr:`py2dm.Reader.elements`, and :attr:`py2dm.Reader.node_strings` properties respectively. These behave exactly the same as if the corresponding iterator were called with default arguments.

.. code-block:: python3

   >>> with py2dm.Reader('path/to/mesh.2dm') as mesh:
   ...   for node in mesh.nodes:
   ...    if node.id % 10 == 0:
   ...      print(node)
   ...
   Node #10: (1200.0, 200.0, 20.0)
   Node #20: (1120.0, 220.0, 10.0)
   (...)

Random access
-------------

To access elements randomly (i.e. by their unique ID), you can use the :meth:`py2dm.Reader.node`, :meth:`py2dm.Reader.element`, and :meth:`py2dm.Reader.node_string` methods.

Note that these use the unique identifier for a given entity. For nodes and elements, this is their ID. For node strings, this would be their unique ID when using a :doc:`subformat <subformats>` that supports unique identifiers for node strings.

Lazy read mode (NYI)
====================

.. note::
   
   This feature is not yet available in this version of Py2DM.

Reader class interface
======================

.. autoclass:: py2dm.Reader
   :inherited-members:
   :members:
