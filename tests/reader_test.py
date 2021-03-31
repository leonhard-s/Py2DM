"""Test cases for the py2dm.Reader class."""

import math
import os
import unittest

import py2dm  # pylint: disable=import-error


class TestReadSynthetic(unittest.TestCase):
    """Short, synthetic files to check specific parsing behaviours."""

    _DATA_DIR = 'tests/data/'

    @classmethod
    def data(cls, filename: str) -> str:
        """Return an absolute path to a synthetic test file."""
        return os.path.abspath(
            os.path.join(cls._DATA_DIR, filename))

    def test_empty_mesh(self) -> None:
        path = self.data('empty_mesh.2dm')
        with py2dm.Reader(path) as mesh:
            self.assertTrue(
                all((math.isnan(f) for f in mesh.extent)),
                'mesh extents are not empty')
            self.assertListEqual(
                list(mesh.elements), [],
                'elements list is not empty')
            self.assertListEqual(
                list(mesh.nodes), [],
                'nodes list ist not empty')
            self.assertListEqual(
                list(mesh.node_strings), [],
                'node strings list is not empty')
            self.assertEqual(
                mesh.num_elements, 0,
                'element count is not zero')
            self.assertEqual(
                mesh.num_nodes, 0,
                'node count is not zero')
            self.assertEqual(
                mesh.num_node_strings, 0,
                'node string count is not zero')
            with self.assertRaises(KeyError):
                _ = mesh.element(1)
            with self.assertRaises(KeyError):
                _ = mesh.node(1)
            with self.assertRaises(KeyError):
                _ = mesh.node_string('name')
            with self.assertRaises(StopIteration):
                _ = next(iter(mesh.iter_elements()))
            with self.assertRaises(StopIteration):
                _ = next(iter(mesh.iter_nodes()))
            with self.assertRaises(StopIteration):
                _ = next(iter(mesh.iter_node_strings()))

    def test_empty_file(self) -> None:
        path = self.data('empty_file.2dm')
        with self.assertRaises(py2dm.errors.ReadError):
            with py2dm.Reader(path) as mesh:
                _ = mesh

    def test_non_mesh(self) -> None:
        path = self.data('not-a-mesh.2dm')
        with self.assertRaises(py2dm.errors.ReadError):
            with py2dm.Reader(path) as mesh:
                _ = mesh

    def test_comments(self) -> None:
        path = self.data('all-the-comments.2dm')
        with py2dm.Reader(path) as mesh:
            self.assertTupleEqual(
                mesh.extent, (-10.0, 10.0, -10.0, 10.0),
                'incorrect mesh extents')
            self.assertListEqual(
                list(mesh.elements),
                [py2dm.Element3T(1, 1, 2, 3),
                 py2dm.Element3T(2, 2, 3, 4)],
                'bad mesh elements list')
            self.assertListEqual(
                list(mesh.nodes),
                [py2dm.Node(1, -10.0, 10.0, 0.0),
                 py2dm.Node(2, -10.0, -10.0, 0.0),
                 py2dm.Node(3, 10.0, 10.0, 0.0),
                 py2dm.Node(4, 10.0, -10.0, 0.0)],
                'bad mesh nodes list')
            self.assertListEqual(
                list(mesh.node_strings), [],
                'node strings list not empty')
            self.assertEqual(
                mesh.num_elements, 2,
                'incorrect element count')
            self.assertEqual(
                mesh.num_nodes, 4,
                'incorrect node count')
            self.assertEqual(
                mesh.num_node_strings, 0,
                'node string count not zero')
            self.assertListEqual(
                list(mesh.iter_elements()), list(mesh.elements),
                'bad element iterator')
            self.assertListEqual(
                list(mesh.iter_nodes()), list(mesh.nodes),
                'bad node iterator')
            with self.assertRaises(StopIteration):
                _ = next(iter(mesh.iter_node_strings()))

    def test_nodes_only(self) -> None:
        path = self.data('nodes-only.2dm')
        with py2dm.Reader(path) as mesh:
            self.assertTupleEqual(
                mesh.extent, (-10.0, 10.0, -10.0, 10.0),
                'incorrect mesh extents')
            self.assertListEqual(
                list(mesh.elements), [],
                'elements list not empty')
            self.assertListEqual(
                list(mesh.nodes),
                [py2dm.Node(1, -10.0, 10.0, 0.0),
                 py2dm.Node(2, -10.0, -10.0, 0.0),
                 py2dm.Node(3, 10.0, 10.0, 0.0),
                 py2dm.Node(4, 10.0, -10.0, 0.0)],
                'bad mesh nodes list')
            self.assertListEqual(
                list(mesh.node_strings), [],
                'node strings list not empty')
            self.assertEqual(
                mesh.num_elements, 0,
                'element count not zero')
            self.assertEqual(
                mesh.num_nodes, 4,
                'incorrect node count')
            self.assertEqual(
                mesh.num_node_strings, 0,
                'node string count not zero')
            with self.assertRaises(StopIteration):
                _ = next(iter(mesh.iter_elements()))
            self.assertListEqual(
                list(mesh.iter_nodes()), list(mesh.nodes),
                'bad node iterator')
            with self.assertRaises(StopIteration):
                _ = next(iter(mesh.iter_node_strings()))

    def test_zero_indexed(self) -> None:
        path = self.data('zero-indexed.2dm')
        with py2dm.Reader(path, zero_index=True) as mesh:
            self.assertTupleEqual(
                mesh.extent, (-10.0, 10.0, -10.0, 10.0),
                'incorrect mesh extents')
            self.assertListEqual(
                list(mesh.elements),
                [py2dm.Element3T(0, 0, 1, 2),
                 py2dm.Element3T(1, 1, 2, 3)],
                'bad mesh elements list')
            self.assertListEqual(
                list(mesh.nodes),
                [py2dm.Node(0, -10.0, 10.0, 0.0),
                 py2dm.Node(1, -10.0, -10.0, 0.0),
                 py2dm.Node(2, 10.0, 10.0, 0.0),
                 py2dm.Node(3, 10.0, -10.0, 0.0)],
                'bad mesh nodes list')
            self.assertListEqual(
                list(mesh.node_strings), [],
                'node strings list not empty')
            self.assertEqual(
                mesh.num_elements, 2,
                'incorrect element count')
            self.assertEqual(
                mesh.num_nodes, 4,
                'incorrect node count')
            self.assertEqual(
                mesh.num_node_strings, 0,
                'node string count not zero')
            self.assertListEqual(
                list(mesh.iter_elements()), list(mesh.elements),
                'bad element iterator')
            self.assertListEqual(
                list(mesh.iter_nodes()), list(mesh.nodes),
                'bad node iterator')
            with self.assertRaises(StopIteration):
                _ = next(iter(mesh.iter_node_strings()))

    def test_basic_node_strings(self) -> None:
        path = self.data('basic-node-strings.2dm')
        with py2dm.Reader(path) as mesh:
            self.assertTupleEqual(
                mesh.extent, (-5.0, 5.0, -5.0, 5.0),
                'incorrect mesh extents')
            self.assertListEqual(
                list(mesh.elements),
                [py2dm.Element3T(1, 1, 2, 3),
                 py2dm.Element3T(2, 2, 3, 4),
                 py2dm.Element2L(3, 1, 3),
                 py2dm.Element2L(4, 2, 4)],
                'bad mesh elements list')
            self.assertListEqual(
                list(mesh.nodes),
                [py2dm.Node(1, -5.0, -5.0, -1.0),
                 py2dm.Node(2, -5.0, 5.0, 2.0),
                 py2dm.Node(3, 5.0, -5.0, -3.0),
                 py2dm.Node(4, 5.0, 5.0, 4.0),
                 py2dm.Node(5, 0.0, 0.0, 5.0)],
                'bad mesh nodes list')
            self.assertListEqual(
                list(mesh.node_strings),
                [py2dm.NodeString(1, 2, 4, 3, name='first'),
                 py2dm.NodeString(4, 5, 1, name='second')],
                'bad node strings list')
            self.assertEqual(
                mesh.num_elements, 4,
                'incorrect element count')
            self.assertEqual(
                mesh.num_nodes, 5,
                'incorrect node count')
            self.assertEqual(
                mesh.num_node_strings, 2,
                'incorrect node string count')
            self.assertListEqual(
                list(mesh.iter_elements()), list(mesh.elements),
                'bad element iterator')
            self.assertListEqual(
                list(mesh.iter_nodes()), list(mesh.nodes),
                'bad node iterator')
            self.assertListEqual(
                list(mesh.iter_node_strings()), list(mesh.node_strings),
                'bad node string iterator')
