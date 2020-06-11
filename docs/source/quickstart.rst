Quickstart
==========

.. note:: This library is in very early stages of development and may be subject to heavy changes.

This section covers the basics of how this module is used. Please note that this information is subject to change as the endpoints are updated.

Reading Mesh Files
------------------

To read a 2DM mesh file, create a :class:`py2dm.Reader` object and pass it the path of the 2DM file to read.

The preferred way to use this class is via the context manager interface.

.. code-block:: python

    >>> with py2dm.Reader('path/to/mesh.2dm') as mesh:
    ...   print(mesh)
    ...
    2DM Reader (path/to/mesh.2dm)
    124 nodes
    92 elements
    4 node strings

For most use-cases, it will be sufficient to retrieve the geometries defined via the :attr:`py2dm.Reader.nodes`, :attr:`py2dm.Reader.elements`, and :attr:`py2dm.Reader.node_strings` attributes.

.. note:: As of v0.1.0, the :attr:`Element.nodes <py2dm.entities.Element.nodes>` attribute returns node IDs, not the node objects themselves.

For larger meshes, it is not advisable to load all of the nodes or elements in a single batch. In these cases, you can process these attributes' information via their iterator counterparts, i.e. the :meth:`py2dm.Reader.iter_nodes`, :meth:`py2dm.Reader.iter_elements`, and :meth:`py2dm.Reader.iter_node_strings` methods respectively.

.. code-block:: python

    >>> with py2dm.Reader('path/to/mesh.2dm') as mesh:
    ...   for node in mesh.iter_nodes():
    ...     if node.id % 10 == 0:
    ...       print(node)
    ...
    Node #10: (1200.0, 200.0, 20.0)
    Node #20: (1120.0, 220.0, 10.0)
    (...)

For additional information and caveats regarding the methods available, please refer to the documentation for the :class:`py2dm.Reader` class.

Writing Mesh Files
------------------

To write a 2DM mesh file, instantiate a :class:`py2dm.Writer` object.

As with :class:`py2dm.Reader`, the preferred way to do this is via a context manager.

Adding Geometry
***************

You can add geometries to the mesh using the :meth:`py2dm.Writer.element`, :meth:`py2dm.Writer.node`, and :meth:`py2dm.Writer.node_string` methods.

:meth:`py2dm.Writer.element` and :meth:`py2dm.Writer.node` will return the auto-assigned ID of the created object. This is particularly important for nodes as these IDs must be referenced by other methods.

.. important:: These factory methods will add the methods to the local cache, but they will not be written to file until :meth:`py2dm.Writer.write` is called.

    This is done to allow for custom 2DM card orders, which are required by some programs.

Writing the file
****************

After defining your geometry, it will be added to the :class:`py2dm.Writer` object's cache, but not yet written to disk.

You can do this via the :meth:`Writer.write <py2dm.write.Writer.write` method. This is a utility method that calls :meth:`Writer.write_header`, :meth:`Writer.write_nodes`, :meth:`Writer.write_elements`, and :meth:`Writer.write_node_strings` in order. You can also call these methods individually to customise the 2DM card order.

Here is an example of the minimal mesh writing process:

.. code-block:: python

    >>> with py2dm.Writer('path/to/mesh.2dm') as mesh:
    ...   # Create nodes
    ...   for i in range(10):
    ...     mesh.node(float(i), 1.0, i % 2)
    ...   # Create elements
    ...   mesh.element(py2dm.Element2L, (1, 2))
    ...   mesh.element(py2dm.Element3T, (1, 2, 3))
    ...   # Save mesh
    ...   mesh.write()
