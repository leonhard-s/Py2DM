"""Tools and helper methods for working with Py2DM.

This module includes independent utilities that may be useful when
working with Py2DM as part of a larger workflow. This includes
compatibility modes, format converters and the likes.
"""

import os
import warnings
from typing import List, Union

from ._entities import Element3T, Element6T
from ._write import Writer

__all__ = [
    'triangle_to_2dm'
]


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
