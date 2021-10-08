"""Tools and helper methods for working with Py2DM.

This module includes independent utilities that may be useful when
working with Py2DM as part of a larger workflow. This includes
compatibility modes, format converters and the likes.
"""

import os
import warnings
from typing import Dict, List, Optional, Tuple, Union

from ._entities import (Element, Element3T, Element6T, NodeString, Node,
                        element_factory)
from ._write import Writer

__all__ = [
    'convert_random_nodes',
    'convert_unsorted_nodes',
    'triangle_to_2dm'
]


def convert_random_nodes(
        filepath: str, export_conversion_tables: bool = False) -> None:
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
    """
    # Read mesh entities
    old_nodes, old_elements, old_node_strings = _process_entities(filepath)
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
    for node_string in old_node_strings:
        node_string.nodes = tuple(
            (translate_nodes[n] for n in node_string.nodes))
        node_strings.append(node_string)
    # Write converted mesh
    path, filename = os.path.split(filepath)
    base_name, ext = os.path.splitext(filename)
    filename = f'{base_name}_converted{ext}'
    outpath = os.path.join(path, filename)
    _write_converted(outpath, nodes, elements, node_strings)


def convert_unsorted_nodes(filepath: str) -> None:
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
    """
    # Read mesh entities
    nodes, elements, node_strings = _process_entities(filepath)
    # Sort entities
    # NOTE: An insertion sort would be faster for very large meshes
    nodes = sorted(nodes, key=lambda n: n.id)
    elements = sorted(elements, key=lambda e: e.id)
    # Write converted mesh
    path, filename = os.path.split(filepath)
    base_name, ext = os.path.splitext(filename)
    filename = f'{base_name}_converted{ext}'
    outpath = os.path.join(path, filename)
    _write_converted(outpath, nodes, elements, node_strings)


def triangle_to_2dm(node_file: str, ele_file: str, output: str = '') -> None:
    """Create a 2DM mesh from "Triangle" output files.

    This converter allows the creation of a Py2DM-compatible mesh from
    the output files of the Triangle 2D mesh generator:
    `<https://www.cs.cmu.edu/~quake/triangle.html>`_.

    :param node_file: The Triangle NODE file to read.
    :type node_file: :class:`str`
    :param ele_file: The Triangle ELE file to read.
    :type ele_file: :class:`str`
    :param output: The output file to write. Defaults to the name of
        the Triangle output, minus the iteration number.
    :type output: :class:`str`
    """
    if not output:
        output, _ = os.path.splitext(node_file)
        print(f'Output (pre-tail): {output}')
        # Strip iteration number, if any
        if '.' in output:
            output, tail = output.rsplit('.', maxsplit=1)
            try:
                _ = int(tail)
            except ValueError:
                # Not an iteration number, re-append tail
                output = f'{output}.{tail}'
        print(f'Output (post-tail): {output}')
        output += '.2dm'
    # Check the header of the element file to get the number of element
    # attributes
    with open(ele_file) as f_elements:
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
        with open(node_file) as f_nodes:
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
        with open(ele_file) as f_elements:
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


def _process_entities(
        filepath: str) -> Tuple[List[Node], List[Element], List[NodeString]]:
    """Helper function for loading all mesh entities.

    :param filepath: Input 2DM file to parse.
    :type filepath: :class:`str`
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
    with open(filepath) as file_:
        for line in file_:
            if line.startswith('ND '):
                nodes.append(Node.from_line(line))
                continue
            if line.startswith('NS '):
                ns_previous: Optional[NodeString] = None
                if ns_done:
                    ns_previous = node_strings.pop()
                node_string, ns_done = NodeString.from_line(line, ns_previous)
                node_strings.append(node_string)
                continue
            if line.startswith('E'):
                try:
                    cls = element_factory(line)
                except NotImplementedError:
                    continue
                elements.append(cls.from_line(line))
    return nodes, elements, node_strings


def _write_converted(filepath: str, nodes: List[Node], elements: List[Element],
                     node_strings: List[NodeString]) -> None:
    """Helper function for writing meshes from memory.

    :param filepath: Output path to write to.
    :type filepath: :class:`str`
    :param nodes: Mesh nodes
    :type nodes: :obj:`typing.List` [:class:`py2dm.Node`]
    :param elements: Mesh elements
    :type nodes: :obj:`typing.List` [:class:`py2dm.Element`]
    :param node_strings: Mesh node strings
    :type nodes: :obj:`typing.List` [:class:`py2dm.NodeString`]
    """
    num_materials = elements[0].num_materials if elements else 0
    with Writer(filepath, materials=num_materials) as writer:
        for index, node in enumerate(nodes):
            writer.node(node)
            if index % 100_000 == 0:
                writer.flush_nodes()
        writer.flush_nodes()
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
