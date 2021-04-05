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

.. note:: As of v0.1.0, the :attr:`Element.nodes <py2dm.Element.nodes>` attribute returns node IDs, not the node objects themselves.

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
