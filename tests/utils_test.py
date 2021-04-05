"""Test cases for the py2dm.utils sub module."""

import os
import unittest
import tempfile
from typing import Tuple

import py2dm  # pylint: disable=import-error


class TestTriangleConverter(unittest.TestCase):
    """Tests for the py2dm.utils.triangle_to_2dm method."""

    _PATH = os.path.join('tests', 'data', 'triangle')

    def get_triangle_output(self, filename: str) -> Tuple[str, str]:
        """Return the pregenerated output for a given test file."""
        filename, _ = os.path.splitext(filename)
        output = os.path.join(self._PATH, 'output', f'{filename}.1')
        return f'{output}.node', f'{output}.ele'

    def test_spiral(self) -> None:
        node, ele = self.get_triangle_output('spiral.node')
        with tempfile.TemporaryDirectory() as temp_dir:
            output = os.path.join(temp_dir, 'spiral.2dm')
            py2dm.utils.triangle_to_2dm(node, ele, output)
            with py2dm.Reader(output) as mesh:
                self.assertEqual(
                    mesh.materials_per_element, 0,
                    'bad material count')
                self.assertEqual(
                    mesh.num_elements, 33,
                    'bad element count')
                self.assertEqual(
                    mesh.num_nodes, 26,
                    'bad node count')
                self.assertEqual(
                    mesh.num_node_strings, 0,
                    'bad node string count')
                self.assertEqual(
                    mesh.node(2),
                    py2dm.Node(2, -0.416, 0.909, 0.0),
                    'bad node returned')
                self.assertEqual(
                    mesh.element(3),
                    py2dm.Element3T(3, 16, 21, 23),
                    'bad element returned')

    def test_spiral_e6t(self) -> None:
        node, ele = self.get_triangle_output('spiral_e6t.node')
        with tempfile.TemporaryDirectory() as temp_dir:
            output = os.path.join(temp_dir, 'spiral_e6t.2dm')
            py2dm.utils.triangle_to_2dm(node, ele, output)
            with py2dm.Reader(output) as mesh:
                self.assertEqual(
                    mesh.materials_per_element, 0,
                    'bad material count')
                self.assertEqual(
                    mesh.num_elements, 33,
                    'bad element count')
                self.assertEqual(
                    mesh.num_nodes, 84,
                    'bad node count')
                self.assertEqual(
                    mesh.num_node_strings, 0,
                    'bad node string count')
                self.assertEqual(
                    mesh.node(73),
                    py2dm.Node(73, 1.76, 3.19, 0.0),
                    'bad node returned')
                self.assertEqual(
                    mesh.element(20),
                    # NOTE: Element6T node order adjusted to account for the
                    # node ordering differences between 2DM and Triangle,
                    # namely 1-6-2-4-3-5
                    py2dm.Element6T(20, 15, 70, 16, 35, 23, 71),
                    'bad element returned')
