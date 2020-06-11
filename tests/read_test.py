"""Unit tests for the reader submodule."""

import unittest

import py2dm


class ReaderTests(unittest.TestCase):
    """Test cases for the Reader class."""

    def test_empty(self) -> None:
        """Tests using an empty mesh file."""
        with py2dm.Reader('tests/data/empty.2dm') as mesh:
            self.assertEqual(mesh.num_elements, 0)
            self.assertEqual(mesh.num_node_strings, 0)
            self.assertEqual(mesh.num_nodes, 0)
            self.assertListEqual(mesh.elements, [])
            self.assertListEqual(mesh.node_strings, [])
            self.assertListEqual(mesh.nodes, [])

    def test_comments(self) -> None:
        """Test using a heavily commented file."""
        with py2dm.Reader('tests/data/all-the-comments.2dm') as mesh:
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
        with py2dm.Reader('tests/data/nodes-only.2dm') as mesh:
            self.assertEqual(mesh.num_elements, 0)
            self.assertEqual(mesh.num_node_strings, 0)
            self.assertEqual(mesh.num_nodes, 4)
            node_2 = mesh.node(2)
            self.assertIsInstance(node_2, py2dm.Node)
            self.assertTupleEqual(node_2.pos, (-10.0, -10.0, 0.0))

    def test_zero_index(self) -> None:
        """Test using a mesh whos IDs start at 0 rather than 1."""
        with py2dm.Reader('tests/data/zero-indexed.2dm') as mesh:
            with self.assertWarns(UserWarning):
                element = mesh.element(0)
                self.assertIsInstance(element, py2dm.Element)
                self.assertTupleEqual(element.nodes, (0, 1, 2))
            with self.assertWarns(UserWarning):
                node = mesh.node(0)
                self.assertIsInstance(node, py2dm.Node)
                self.assertTupleEqual(node.pos, (-10.0, 10.0, 0.0))
