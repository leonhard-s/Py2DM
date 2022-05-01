"""Test cases for the py2dm.utils sub module."""

import csv
import os
import unittest
import shutil
import tempfile
from typing import List, Tuple

import py2dm  # pylint: disable=import-error
# pylint: disable=import-error
from py2dm.utils import (convert_random_nodes, convert_unsorted_nodes,
                         merge_meshes)


# pylint: disable=missing-function-docstring


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


class UnsortedIdConverter(unittest.TestCase):
    """Test cases for the `convert_unsorted_nodes` parser."""

    _DATA_DIR = os.path.join('tests', 'data', 'external', 'mdal')

    _temp_dir: tempfile.TemporaryDirectory  # type: ignore

    def setUp(self) -> None:
        super().setUp()
        self._temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        super().tearDown()
        self._temp_dir.cleanup()  # type: ignore

    @classmethod
    def data(cls, filename: str) -> str:
        """Return an absolute path to a synthetic test file."""
        return os.path.abspath(
            os.path.join(cls._DATA_DIR, filename))

    def convert(self, filename: str) -> str:
        """Convert an input file and open the converted copy."""
        # Copy input to temporary directory
        in_path = os.path.join(self._temp_dir.name, filename)  # type: ignore
        shutil.copy(self.data(filename), in_path)
        # Convert
        convert_unsorted_nodes(in_path)
        # Return converted file's path
        basename, ext = os.path.splitext(filename)
        return os.path.join(self._temp_dir.name,  # type: ignore
                            f'{basename}_converted{ext}')

    def test_triangle_e6t(self) -> None:
        path = self.convert('triangleE6T.2dm')
        with self.assertRaises(py2dm.errors.FormatError):
            py2dm.Reader(path).open()

    def test_unordered_ids(self) -> None:
        path = self.convert('unordered_ids.2dm')
        py2dm.Reader(path).open()


class RandomIdConverter(unittest.TestCase):
    """Test cases for the `convert_random_nodes` parser."""

    _DATA_DIR = os.path.join('tests', 'data', 'external', 'mdal')

    _temp_dir: tempfile.TemporaryDirectory  # type: ignore

    def setUp(self) -> None:
        super().setUp()
        self._temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        super().tearDown()
        self._temp_dir.cleanup()  # type: ignore

    @classmethod
    def data(cls, filename: str) -> str:
        """Return an absolute path to a synthetic test file."""
        return os.path.abspath(
            os.path.join(cls._DATA_DIR, filename))

    def convert(self, filename: str, export_conversion_tables: bool) -> str:
        """Convert an input file and open the converted copy."""
        # Copy input to temporary directory
        in_path = os.path.join(self._temp_dir.name, filename)  # type: ignore
        shutil.copy(self.data(filename), in_path)
        # Convert
        convert_random_nodes(in_path, export_conversion_tables)
        # Return converted file's path
        basename, ext = os.path.splitext(filename)
        return os.path.join(self._temp_dir.name,  # type: ignore
                            f'{basename}_converted{ext}')

    def test_triangle_e6t(self) -> None:
        path = self.convert('triangleE6T.2dm', False)
        with py2dm.Reader(path) as mesh:
            self.assertEqual(mesh.num_elements, 6)
            self.assertEqual(mesh.num_nodes, 22)
            self.assertEqual(mesh.num_node_strings, 0)
            self.assertEqual(mesh.element(1).card, 'E6T')

    def test_unordered_ids(self) -> None:
        path = self.convert('unordered_ids.2dm', False)
        with py2dm.Reader(path) as mesh:
            self.assertEqual(mesh.num_elements, 2)
            self.assertEqual(mesh.num_nodes, 5)
            self.assertEqual(mesh.num_node_strings, 0)
            self.assertEqual(mesh.element(1).card, 'E4Q')
            self.assertEqual(mesh.element(2).card, 'E3T')

    def test_triangle_e6t_table(self) -> None:
        path = self.convert('triangleE6T.2dm', True)
        basename, _ = os.path.splitext(path)
        nodes_path = f'{basename}_nodes.csv'
        with open(nodes_path, 'r', encoding='utf-8', newline='') as f_nodes:
            header, *nodes = list(csv.reader(f_nodes))
            self.assertEqual(header, ['Old Node ID', 'New Node ID'])
            self.assertListEqual(nodes[:4], [
                ['4', '1'],
                ['5', '2'],
                ['6', '3'],
                ['7', '4'],
            ])
        elements_path = f'{basename}_elements.csv'
        with open(elements_path, 'r', encoding='utf-8', newline='') as f_elements:
            header, *elements = list(csv.reader(f_elements))
            self.assertEqual(header, ['Old Element ID', 'New Element ID'])
            self.assertListEqual(elements[:4], [
                ['1', '1'],
                ['2', '2'],
                ['3', '3'],
                ['4', '4'],
            ])


class MeshMerger(unittest.TestCase):
    """Tests for the py2dm.utils.merge_meshes method."""

    _PATH = os.path.join('tests', 'data')

    _temp_dir: tempfile.TemporaryDirectory  # type: ignore

    def setUp(self) -> None:
        super().setUp()
        self._temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        super().tearDown()
        self._temp_dir.cleanup()  # type: ignore

    @classmethod
    def data(cls, filename: str) -> str:
        """Return an absolute path to a synthetic test file."""
        return os.path.abspath(
            os.path.join(cls._PATH, filename))

    def merge(self, base: str, added: str) -> str:
        path = os.path.join(self._temp_dir.name, 'merged.2dm')  # type: ignore
        merge_meshes(self.data(base), self.data(added), path)
        return path

    def test_merge_successful(self) -> None:
        path_base = self.data('merge-mesh-base.2dm')
        path_added = self.data('merge-mesh-wrap.2dm')
        path_merged = self.merge(path_base, path_added)
        with py2dm.Reader(path_merged) as merged:
            self.assertEqual(merged.num_elements, 18)
            self.assertEqual(merged.num_nodes, 16)
            self.assertEqual(merged.num_node_strings, 0)
            # Ensure the first mesh's entities are unchanged
            with py2dm.Reader(path_base) as base:
                for node in base.nodes:
                    self.assertEqual(merged.node(node.id), node)
                for element in base.elements:
                    self.assertEqual(merged.element(element.id), element)
            # Ensure all of the added mesh's entities are present
            nodes: List[Tuple[float, float, float]] = []
            elements: List[Tuple[int, ...]] = []
            with py2dm.Reader(path_added) as added:
                for node in added.nodes:
                    nodes.append(node.pos)
            for node in merged.nodes:
                if node.pos in nodes:
                    nodes.remove(node.pos)
            self.assertEqual(len(nodes), 0)
            self.assertEqual(len(elements), 0)
