Mesh Entities
=============

The following classes are Python object representations of 2DM geometries.

They are retrieved directly via the :class:`py2dm.Reader` class, or can be converted manually by passing a line into their ``.from_line()`` factory method.

To convert an instance back into its 2DM text representation, use the ``.to_line()`` method. It returns a list of strings that can be formatted to match fixed-width columns if desired.

Nodes
=====

.. autoclass:: py2dm.Node
    :members:

Elements
========

Base classes
------------

.. autoclass:: py2dm.Element
    :members:

.. autoclass:: py2dm.LinearElement
    :members:

.. autoclass:: py2dm.TriangularElement
    :members:

.. autoclass:: py2dm.QuadrilateralElement
    :members:

Element types
-------------

.. autoclass:: py2dm.Element2L
    :members:

.. autoclass:: py2dm.Element3L
    :members:

.. autoclass:: py2dm.Element3T
    :members:

.. autoclass:: py2dm.Element4Q
    :members:

.. autoclass:: py2dm.Element6T
    :members:

.. autoclass:: py2dm.Element8Q
    :members:

.. autoclass:: py2dm.Element9Q
    :members:

Node strings
============

.. autoclass:: py2dm.NodeString
    :members:
