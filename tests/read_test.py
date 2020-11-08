"""Unit tests for the reader submodule."""

import unittest

import py2dm  # pylint: disable=import-error


class ReaderTests(unittest.TestCase):
    """Test cases for the Reader class."""

    reader = py2dm.Reader

    def test_empty(self) -> None:
        """Tests using an empty mesh file."""
        with self.reader('tests/data/empty.2dm') as mesh:
            self.assertEqual(mesh.num_elements, 0)
            self.assertEqual(mesh.num_node_strings, 0)
            self.assertEqual(mesh.num_nodes, 0)
            self.assertListEqual(list(mesh.elements), [])
            self.assertListEqual(list(mesh.node_strings), [])
            self.assertListEqual(list(mesh.nodes), [])

    def test_comments(self) -> None:
        """Test using a heavily commented file."""
        with self.reader('tests/data/all-the-comments.2dm') as mesh:
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
        with self.reader('tests/data/nodes-only.2dm') as mesh:
            self.assertEqual(mesh.num_elements, 0)
            self.assertEqual(mesh.num_node_strings, 0)
            self.assertEqual(mesh.num_nodes, 4)
            node_2 = mesh.node(2)
            self.assertIsInstance(node_2, py2dm.Node)
            self.assertTupleEqual(node_2.pos, (-10.0, -10.0, 0.0))

    def test_zero_index(self) -> None:
        """Test using a mesh whos IDs start at 0 rather than 1."""
        with self.assertRaises(RuntimeError):
            with self.reader('tests/data/zero-indexed.2dm') as mesh:
                pass


class MemoryReaderTests(ReaderTests):
    """Run the shared test cases for the MemoryReader class."""

    reader = py2dm.MemoryReader
