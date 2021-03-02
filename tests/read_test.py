"""Unit tests for the reader class."""

import unittest
import warnings

import py2dm  # pylint: disable=import-error


class TestReadBasic(unittest.TestCase):
    """Basic tests using synthetic files to check parsing behaviour."""

    def test_empty(self) -> None:
        """Tests using an empty mesh file."""
        path = 'tests/data/empty.2dm'
        with py2dm.Reader(path) as mesh:
            self.assertEqual(mesh.num_elements, 0)
            self.assertEqual(mesh.num_node_strings, 0)
            self.assertEqual(mesh.num_nodes, 0)
            self.assertListEqual(list(mesh.elements), [])
            self.assertListEqual(list(mesh.node_strings), [])
            self.assertListEqual(list(mesh.nodes), [])

    def test_comments(self) -> None:
        """Test using a heavily commented file."""
        path = 'tests/data/all-the-comments.2dm'
        with py2dm.Reader(path) as mesh:
            self.assertEqual(mesh.num_elements, 2)
            self.assertEqual(mesh.num_node_strings, 0)
            self.assertEqual(mesh.num_nodes, 4)
            node_3 = mesh.node(3)
            self.assertIsInstance(node_3, py2dm.Node)
            self.assertTupleEqual(node_3.pos, (10.0, 10.0, 0.0))
            element_2 = mesh.element(2)
            self.assertIsInstance(element_2, py2dm.Element3T)
            self.assertTupleEqual(element_2.nodes, (2, 3, 4))

    def test_nodes_only(self) -> None:
        """Test using a mesh only containing nodes."""
        path = 'tests/data/nodes-only.2dm'
        with py2dm.Reader(path) as mesh:
            self.assertEqual(mesh.num_elements, 0)
            self.assertEqual(mesh.num_node_strings, 0)
            self.assertEqual(mesh.num_nodes, 4)
            node_2 = mesh.node(2)
            self.assertIsInstance(node_2, py2dm.Node)
            self.assertTupleEqual(node_2.pos, (-10.0, -10.0, 0.0))

    def test_zero_index(self) -> None:
        """Test using a mesh whose IDs start at 0 rather than 1."""
        path = 'tests/data/zero-indexed.2dm'
        with py2dm.Reader(path, zero_index=True) as mesh:
            self.assertEqual(mesh.num_nodes, 4)
            self.assertEqual(mesh.num_elements, 2)
            node_2 = mesh.node(2)
            self.assertIsInstance(node_2, py2dm.Node)
            self.assertTupleEqual(node_2.pos, (10.0, 10.0, 0.0))
