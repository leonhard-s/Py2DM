==============
2DM Subformats
==============

The original `2DM format specification`_ is generally not strictly followed by other software packages or even later versions of SMS.

This fragmentation makes it impossible for Py2DM to fully support all substandards by default. The following sections cover the main differences between subformats and how to create compatible meshes using Py2DM.

Zero-indexed ID ranges
======================

Py2DM only supports zero-based entity indices when the `zero_index` flag is set as part of the :class:`py2dm.Reader` class instantiation:

.. code-block:: python3

   with py2dm.Reader('path/to/mesh.2dm) as mesh:
     assert mesh.node(0)  # Invalid

   with py2dm.Reader('path/to/mesh.2dm', zero_index=True) as mesh:
     assert mesh.node(0)  # No exception raised

Invalid ID ranges
=================

The 2DM standard requires node and element IDs to be numbered consecutively. Py2DM uses this assertion to efficiently translate between node indices and their corresponding location in the file.

This in turn means that the default :class:`py2dm.Reader` class does not support opening files with unsorted IDs, or ones with gaps in their ID ranges.

.. note::

   The :mod:`py2dm.utils` submodule provides converter functions that allow the conversion of such meshes into a format compatible with Py2DM.
   
   For a list of available utility functions, see :doc:`utils`.

BASEMENT mesh format
====================

The following information is a summary of the `BASEMENT format specification`_.

- All BASEMENT versions currently only support three-noded triangular elements (``E3T``/:class:`py2dm.Element3T`)

BASEMENT 2.x
------------

- Elements must specify a single material ID
- No support for :class:`py2dm.NodeString`

BASEMENT 3.x
------------

- Elements must specify two material IDs
- The second material is a floating point value storing the elevation of that element
- :class:`py2dm.NodeString` is supported but requires specifying ``fold_after=0`` as part of the :meth:`py2dm.Writer.flush_node_strings` call. Additionally, node strings are given a single-word string name that is stored as the last field after the final, negative node ID.

Trailing newlines
-----------------

BASEMENT v3.x does not allow trailing newlines in its 2DM meshes.

This causes compatibility issues with other programs that rely on trailing newline characters as part of the `POSIX line definition`_. Py2DM also writes trailing newlines, which can cause compatibility issues with some versions of BASEMENT 3.x.

As a workaround, you can use the following snippet to update the file after it was written by :class:`py2dm.Writer`:

.. code-block:: python3

   # This reads the mesh file written by Py2DM backwards until a
   # non-whitespace character is found. The file is then truncated
   # so it ends just before the trailing whitespace, as required.

   with open('path/to/my/mesh.2dm', 'rb+') as f:
      f.seek(0, os.SEEK_END)
      while not f.read(1).strip():
         f.seek(-2, os.SEEK_CUR)
      f.truncate()

.. note::

   Some text editors will automatically add trailing newlines when saving, which might undo this workaround.

TUFLOW format
=============

The following information is a summary of `this post <TUFLOW format post>`_ in the TUFLOW forum. While not official, it appears to be accurate.

- Both ``E3T``/:class:`py2dm.Element3T` and ``E4Q``/:class:`py2dm.Element4Q` elements supported
- A single material index is used per element
- A :class:`py2dm.NodeString` must be kept to a single line, with an extra field after the final (negative) node being used as the unique ID of that node string.

.. note::

   In addition to the cards above, some TUFLOW meshes also contain georeferencing information in their header, as well as for all nodes and elements.

   See `issue #3 <issue-3>`_ for details.

.. _2DM format specification: https://www.xmswiki.com/wiki/SMS:2D_Mesh_Files_*.2dm
.. _BASEMENT format specification: https://git.ee.ethz.ch/BASEMENTpublic/basemesh-v2/-/wikis/reference/2d-mesh-format
.. _POSIX line definition: https://pubs.opengroup.org/onlinepubs/9699919799/basedefs/V1_chap03.html#tag_03_206
.. _TUFLOW format post: https://fvforum.tuflow.com/index.php?/topic/31-2dm-mesh-file-format/
.. _issue-3: https://github.com/leonhard-s/Py2DM/issues/3
