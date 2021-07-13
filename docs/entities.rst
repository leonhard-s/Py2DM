=============
Mesh Entities
=============

The following classes are Python object representations of 2DM geometries.

They are retrieved directly via the :class:`py2dm.Reader` class, or can be converted manually by passing a line into their :meth:`~py2dm.Entity.from_line` factory method.

To convert an instance back into its 2DM text representation, use the :meth:`~py2dm.Entity.to_line` method. It returns a list of strings that can be formatted to match fixed-width columns if desired.

.. currentmodule:: py2dm

Nodes
=====

.. autoclass:: py2dm.Node()

   .. automethod:: __init__(id_: int, x: float, y: float, z: float) -> None

   .. autoattribute:: id

   .. autoattribute:: x

   .. autoattribute:: y

   .. autoattribute:: z

   .. autoproperty:: pos

   .. automethod:: __eq__(other: object) -> bool

   .. automethod:: from_line(line: str, **kwargs) -> py2dm.Node

   .. automethod:: to_line(**kwargs) -> list[str]

Elements
========

Base classes
------------

.. autoclass:: py2dm.Element()
   
   .. automethod:: __init__(id_: int, *nodes: int, materials: Union[tuple[Union[int, float], ...], None] = None) -> None

   .. autoattribute:: id

   .. autoattribute:: nodes

   .. autoattribute:: materials

   .. autoproperty:: num_materials

   .. automethod:: __eq__(other: object) -> bool

   .. automethod:: from_line(line: str, **kwargs) -> py2dm.Element

   .. automethod:: to_line(**kwargs)

.. autoclass:: py2dm.LinearElement()

.. autoclass:: py2dm.TriangularElement()

.. autoclass:: py2dm.QuadrilateralElement()

Element types
-------------

.. autoclass:: py2dm.Element2L()
   
.. autoclass:: py2dm.Element3L()

.. autoclass:: py2dm.Element3T()

.. autoclass:: py2dm.Element4Q()

.. autoclass:: py2dm.Element6T()

.. autoclass:: py2dm.Element8Q()

.. autoclass:: py2dm.Element9Q()

Node strings
============

.. autoclass:: py2dm.NodeString()
   
   .. automethod:: __init__(self, *nodes: int, name: Union[str, None] = None) -> None

   .. autoattribute:: nodes

   .. autoattribute:: name

   .. autoproperty:: num_nodes

   .. automethod:: __eq__(other: object) -> bool

   .. automethod:: from_line(line: str, node_string: Union[py2dm.NodeString, None] = None, **kwargs) -> tuple[py2dm.NodeString, bool]

   .. automethod:: to_line(**kwargs) -> list[str]

Entity interface
================

.. autoclass:: py2dm.Entity()
   
   .. automethod:: __eq__(other: object) -> bool

   .. automethod:: from_line(line: str, **kwargs) -> py2dm.Entity

   .. automethod:: to_line(**kwargs) -> list[str]
