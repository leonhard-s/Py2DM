"""Tools and helper methods for working with Py2DM.

This module includes independent utilities that may be useful when
working with Py2DM as part of a larger workflow. This includes
compatibility modes, format converters and the likes.
"""

import csv
import os
import pathlib
import warnings
from typing import Dict, List, Optional, Set, Tuple, Union

from ._entities import (Element, Element3T, Element6T, NodeString, Node,
                        element_factory)
from ._write import Writer

__all__ = [
    'convert_random_nodes',
    'convert_unsorted_nodes',
    'merge_meshes',
    'triangle_to_2dm',
]


def convert_random_nodes(
        filepath: Union[str, pathlib.Path],
        export_conversion_tables: bool = False,
        encoding: str = 'utf-8') -> None:
    """Compatibility parser for 2DM files with invalid IDs.

    This parser will honour the semantics of any existing IDs (i.e.
    which nodes are connected to what element), but the ID value is
    generated internally. This allows reading node files whose IDs are
    no longer consecutive, which can occur when modifying 2DM meshes in
    external programs.

    The generated output file will be placed next to the input and
    named ``<input-filename>_converted.2dm``.

    Note that this will affect the ID of every node and element in the
    mesh. Auxiliary files that refer to these IDs will no longer work.
    You can set the `export_conversion_tables` flag to export CSV files
    containing the old and new ID of every entity in the mesh. These
    tables can be used to update external files to match the new IDs.

    .. note::

       These conversion tables are only useful if there were no
       duplicate IDs in the input, which is not validated as part of
       this utility.

    :param filepath: Input 2DM file to parse.
    :type filepath: :class:`str`
    :param export_conversion_tables: Whether to export CSV files
       representing the generated ID conversion tables, defaults to
       :obj:`False`.
    :type export_conversion_tables: :class:`bool`
    :param encoding: The encoding to use for input file.
    :type encoding: :class:`str`
    """
    # Read mesh entities
    old_nodes, old_elements, old_node_strings = _process_entities(
        filepath, encoding=encoding)
    # Update nodes
    nodes: List[Node] = []
    translate_nodes: Dict[int, int] = {}
    for index, node in enumerate(old_nodes):
        translate_nodes[node.id] = index + 1
        node.id = index + 1
        nodes.append(node)
    # Update elements
    elements: List[Element] = []
    translate_elements: Dict[int, int] = {}
    for index, element in enumerate(old_elements):
        translate_elements[element.id] = index + 1
        element.id = index + 1
        element.nodes = tuple(
            (translate_nodes[n] for n in element.nodes))
        elements.append(element)
    # Update node strings
    node_strings: List[NodeString] = []
    translate_node_strings: List[
        Tuple[Optional[str], Tuple[Tuple[int, int], ...]]] = []
    for node_string in old_node_strings:
        old_nodes = node_string.nodes
        node_string.nodes = tuple(
            (translate_nodes[n] for n in old_nodes))
        node_strings.append(node_string)
        translate_node_strings.append(
            (node_string.name, tuple(zip(old_nodes, node_string.nodes))))
    # Write converted mesh
    path, filename = os.path.split(filepath)
    base_name, ext = os.path.splitext(filename)
    filename = f'{base_name}_converted{ext}'
    outpath = os.path.join(path, filename)
    _write_converted(outpath, nodes, elements, node_strings, encoding=encoding)
    # Export conversion table
    if export_conversion_tables:
        _write_conversion_tables(os.path.join(path, f'{base_name}_converted'),
                                 translate_nodes, translate_elements,
                                 translate_node_strings, encoding=encoding)


def convert_unsorted_nodes(filepath: Union[str, pathlib.Path],
                           encoding: str = 'utf-8') -> None:
    """Compatibility parser for 2DM files with unsorted IDs.

    The nodes and elements must still produce a consecutive block of
    IDs, without gaps or duplicates. This parser will fix non-standard
    ID ordering, but will not change any IDs.

    The generated output file will be placed next to the input and
    named ``<input-filename>_converted.2dm``.

    If your node or elements IDs do have gaps or duplicates, please use
    the :meth:`py2dm.utils.compat.convert_random_nodes` converter
    instead.

    :param filepath: Input 2DM file to parse.
    :type filepath: :class:`str`
    :param encoding: The encoding to use for input file.
    :type encoding: :class:`str`
    """
    # Read mesh entities
    nodes, elements, node_strings = _process_entities(
        filepath, encoding=encoding)
    # Sort entities
    # NOTE: An insertion sort would be faster for very large meshes
    nodes = sorted(nodes, key=lambda n: n.id)
    elements = sorted(elements, key=lambda e: e.id)
    # Write converted mesh
    path, filename = os.path.split(filepath)
    base_name, ext = os.path.splitext(filename)
    filename = f'{base_name}_converted{ext}'
    outpath = os.path.join(path, filename)
    _write_converted(outpath, nodes, elements, node_strings, encoding=encoding)


def merge_meshes(mesh1: Union[str, pathlib.Path],
                 mesh2: Union[str, pathlib.Path],
                 output: Union[str, pathlib.Path] = '',
                 encoding: str = 'utf-8') -> None:
    """Merge two meshes using their shared vertices.

    This utility will merge two meshes by first merging them at their
    shared vertices, then reconnecting all elements.

    Note that this function does not check for mesh topology and may
    create self-intersections if the input meshes are not properly
    aligned.
    Likewise, this may create duplicate elements if the input meshes
    overlap exactly.

    :param mesh1: Base mesh to extend (all IDs are preserved).
    :type mesh1: :obj:`typing.Union` [
        :class:`str`, :class:`pathlib.Path`]
    :param mesh2: Mesh to add (IDs may change).
    :type mesh2: :obj:`typing.Union` [
        :class:`str`, :class:`pathlib.Path`]
    :param output: The output file to write. Defaults to
        ``<mesh1>_<mesh2>.2dm``.
    :type output: :obj:`typing.Union` [
        :class:`str`, :class:`pathlib.Path`]
    :param encoding: Text encoding to use for all file operations.
    :type encoding: :class:`str`
    """
    if not output:
        output, _ = os.path.splitext(mesh1)
        output += f'_{os.path.basename(mesh2)}'
        if not output.endswith('.2dm'):
            output += '.2dm'
    # Read all entities from the first mesh
    nodes, elements, node_strings = _process_entities(mesh1, encoding=encoding)
    mesh1_node_map: Dict[Tuple[float, float], int] = {}
    mesh1_element_set: List[Set[int]] = []
    mesh1_node_strings: List[str] = []
    for node in nodes:
        mesh1_node_map[(node.x, node.y)] = node.id
    for element in elements:
        mesh1_element_set.append(set(element.nodes))
    for node_string in node_strings:
        if node_string.name is not None:
            mesh1_node_strings.append(node_string.name)
    # Read all entities from the second mesh
    new_nodes, new_elements, new_node_strings = _process_entities(
        mesh2, encoding=encoding)
    # Deduplicate nodes
    mesh2_node_map: Dict[int, int] = {}
    for node in new_nodes:
        marker: Tuple[float, float] = (node.x, node.y)
        if marker in mesh1_node_map:
            # Node already exists, reuse its ID
            mesh2_node_map[node.id] = mesh1_node_map[marker]
    # Create output mesh
    with Writer(output, encoding=encoding) as writer:
        # Add nodes
        for node in nodes:
            writer.node(node.id, node.x, node.y, node.z)
        for node in new_nodes:
            if node.id not in mesh2_node_map:
                mesh2_node_map[node.id] = writer.node(
                    -1, node.x, node.y, node.z)
            node.id = mesh2_node_map[node.id]
        writer.flush_nodes()
        # Add elements
        for element in elements:
            writer.element(element.card, element.id, *element.nodes)
        for element in new_elements:
            # Update element node IDs according to the node ID map
            element.nodes = tuple(mesh2_node_map[n] for n in element.nodes)
            # Only add unique elements
            if set(element.nodes) not in mesh1_element_set:
                writer.element(element.card, -1, *element.nodes)
        writer.flush_elements()
        # Add node strings
        for node_string in node_strings:
            writer.node_string(*node_string.nodes, name=node_string.name)
        for node_string in new_node_strings:
            if (node_string.name is None
                    or node_string.name not in mesh1_node_strings):
                nodes = tuple(mesh2_node_map[n] for n in node_string.nodes)
                writer.node_string(*nodes, name=node_string.name)
        writer.flush_node_strings()


def triangle_to_2dm(node_file: Union[str, pathlib.Path],
                    ele_file: Union[str, pathlib.Path],
                    output: Union[str, pathlib.Path] = '',
                    encoding: str = 'utf-8') -> None:
    """Create a 2DM mesh from "Triangle" output files.

    This converter allows the creation of a Py2DM-compatible mesh from
    the output files of the Triangle 2D mesh generator:
    `<https://www.cs.cmu.edu/~quake/triangle.html>`_.

    :param node_file: The Triangle NODE file to read.
    :type node_file: :obj:`typing.Union` [
        :class:`str`, :class:`pathlib.Path`]
    :param ele_file: The Triangle ELE file to read.
    :type ele_file: :obj:`typing.Union` [
        :class:`str`, :class:`pathlib.Path`]
    :param output: The output file to write. Defaults to the name of
        the Triangle output, minus the iteration number.
    :type output: :obj:`typing.Union` [
        :class:`str`, :class:`pathlib.Path`]
    :param encoding: The encoding to use for input and output files.
    :type encoding: :class:`str`
    """
    if not output:
        output, _ = os.path.splitext(node_file)
        # Strip iteration number, if any
        if '.' in output:
            output, tail = output.rsplit('.', maxsplit=1)
            try:
                _ = int(tail)
            except ValueError:
                # Not an iteration number, re-append tail
                output = f'{output}.{tail}'
        output += '.2dm'
    # Check the header of the element file to get the number of element
    # attributes
    with open(ele_file, encoding=encoding) as f_elements:
        line = f_elements.readline()
        if not line:
            raise RuntimeError('ELE file is empty')
        _, nodes_per_element, num_materials = (int(i) for i in line.split())
    if nodes_per_element not in (3, 6):
        raise RuntimeError('Only three- and six-noded elements are supported')
    # Write mesh
    with Writer(output, materials=num_materials) as mesh:
        mesh.write_header()
        # Add nodes
        with open(node_file, encoding=encoding) as f_nodes:
            for index, line in enumerate(f_nodes):
                if index == 0:
                    num_attributes = int(line.split()[2])
                    if num_attributes > 0:
                        warnings.warn(
                            'The 2DM format does not support node-specific '
                            f'attributes, {num_attributes} attributes per '
                            'node will be ignored')
                    continue
                if line.strip().startswith('#'):
                    continue
                chunks = line.split()
                pos_2d = tuple((float(i) for i in chunks[1:3]))
                mesh.node(int(chunks[0]), pos_2d[0], pos_2d[1], 0.0)
                # Flush node cache every 10k nodes
                if index % 10_000 == 0:
                    mesh.flush_nodes()
        # Add elements
        cls = Element3T if nodes_per_element == 3 else Element6T
        with open(ele_file, encoding=encoding) as f_elements:
            for index, line in enumerate(f_elements):
                if index == 0:
                    continue
                if line.strip().startswith('#'):
                    continue
                chunks = line.split()
                id_, *nodes = (int(i) for i in chunks[:nodes_per_element+1])
                materials: List[Union[int, float]] = []
                for material in chunks[nodes_per_element+1:]:
                    try:
                        value = int(material)
                    except ValueError:
                        value = float(material)
                    materials.append(value)
                # NOTE: Triangle numbers its quadratics elements' nodes
                # corner-corner-corner-edge-edge-edge, while 2DM uses
                # counter-clockwise node ordering.
                # Ref: <https://www.cs.cmu.edu/~quake/triangle.highorder.html>
                if nodes_per_element == 6:
                    nodes = [nodes[0], nodes[5], nodes[1],
                             nodes[3], nodes[2], nodes[4]]
                mesh.element(cls, id_, *nodes, materials=tuple(materials))
                # Flush element cache every 10k elements
                if index % 10_000 == 0:
                    mesh.flush_elements()


def _process_entities(filepath: Union[str, pathlib.Path],
                      encoding: str = 'utf-8'
                      ) -> Tuple[List[Node], List[Element], List[NodeString]]:
    """Helper function for loading all mesh entities.

    :param filepath: Input 2DM file to parse.
    :type filepath: :obj:`typing.Union` [
        :class:`str`, :class:`pathlib.Path`]
    :param encoding: The encoding to use for input file.
    :type encoding: :class:`str`
    :return: A tuple of nodes, elements, and node strings.
    :rtype: :obj:`typing.Tuple` [
       :obj:`typing.List` [:class:`py2dm.Node`],
       :obj:`typing.List` [:class:`py2dm.Element`],
       :obj:`typing.List` [:class:`py2dm.NodeString`]]
    """
    nodes: List[Node] = []
    elements: List[Element] = []
    node_strings: List[NodeString] = []
    ns_done: bool = True
    # Process input file
    with open(filepath, 'r', encoding=encoding) as file_:
        ns_previous: Optional[NodeString] = None
        for line in file_:
            if line.startswith('ND '):
                nodes.append(Node.from_line(line))
                continue
            if line.startswith('NS '):
                node_string, ns_done = NodeString.from_line(line, ns_previous)
                if ns_done:
                    node_strings.append(node_string)
                    ns_previous = None
                else:
                    ns_previous = node_string
                continue
            if line.startswith('E'):
                try:
                    cls = element_factory(line)
                except NotImplementedError:
                    continue
                elements.append(cls.from_line(line))
    return nodes, elements, node_strings


def _write_converted(filepath: Union[str, pathlib.Path],
                     nodes: List[Node], elements: List[Element],
                     node_strings: List[NodeString],
                     encoding: str = 'utf-8',
                     decimals: int = 10) -> None:
    """Helper function for writing meshes from memory.

    :param filepath: Output path to write to.
    :type filepath: :obj:`typing.Union` [
        :class:`str`, :class:`pathlib.Path`]
    :param nodes: Mesh nodes
    :type nodes: :obj:`typing.List` [:class:`py2dm.Node`]
    :param elements: Mesh elements
    :type nodes: :obj:`typing.List` [:class:`py2dm.Element`]
    :param node_strings: Mesh node strings
    :type nodes: :obj:`typing.List` [:class:`py2dm.NodeString`]
    :param encoding: Text encoding to use.
    :type encoding: :class:`str`
    :param decimals: Number of decimal places to use for node coords
    :type decimals: :class:`int`
    """
    num_materials = elements[0].num_materials if elements else 0
    with Writer(filepath, materials=num_materials,
                encoding=encoding) as writer:
        for index, node in enumerate(nodes):
            writer.node(node)
            if index % 100_000 == 0:
                writer.flush_nodes(decimals=decimals)
        writer.flush_nodes(decimals=decimals)
        for index, element in enumerate(elements):
            writer.element(element)
            if index % 100_000 == 0:
                writer.flush_elements()
        writer.flush_elements()
        for index, node_string in enumerate(node_strings):
            writer.node_string(node_string)
            if index % 1000 == 0:
                writer.flush_node_strings()
        writer.flush_node_strings()


def _write_conversion_tables(filepath: str, nodes: Dict[int, int],
                             elements: Dict[int, int],
                             node_strings: List[Tuple[Optional[str], Tuple[Tuple[int, int], ...]]],
                             encoding: str = 'utf-8') -> None:
    """Helper function for exporting conversion tables as CSV files.

    :param filepath: Output directory to write to. The "_nodes.csv" and
        "_elements.csv" suffix is added automatically.
    :type filepath: :class:`str`
    :param nodes: Node conversion table
    :type nodes: :obj:`typing.Dict` [:class:`int`, :class:`int`]
    :param elements: Element conversion table
    :type elements: :obj:`typing.Dict` [:class:`int`, :class:`int`]
    :param node_strings: Node string conversion table
    :type node_strings: :obj:`typing.List` [ :obj:`typing.Tuple` [
        :obj:`typing.Optional` [:class:`str`], :obj:`typing.Tuple` [
        :obj:`typing.Tuple` [:class:`int`, :class:`int`], ...]]]
    :param encoding: The encoding to use for the output files.
    :type encoding: :class:`str`
    """
    if nodes:
        with open(f'{filepath}_nodes.csv', 'w',
                  encoding=encoding, newline='') as f_nodes:
            writer = csv.writer(f_nodes)
            writer.writerow(['Old Node ID', 'New Node ID'])
            writer.writerows(nodes.items())
    if elements:
        with open(f'{filepath}_elements.csv', 'w',
                  encoding=encoding, newline='') as f_elements:
            writer = csv.writer(f_elements)
            writer.writerow(['Old Element ID', 'New Element ID'])
            writer.writerows(elements.items())
    if node_strings:
        with open(f'{filepath}_node_strings.csv', 'w',
                  encoding=encoding, newline='') as f_node_strings:
            writer = csv.writer(f_node_strings)
            writer.writerow(['Node String', 'Old Node IDs', 'New Node IDs'])
            for index, (node_string, pairs) in enumerate(node_strings):
                if node_string is None:
                    node_string = f'NS_{index+1}'
                old, new = (' '.join(str(s) for s in p) for p in zip(*pairs))
                writer.writerow([node_string, old, new])
