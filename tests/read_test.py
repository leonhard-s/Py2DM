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
        with self.assertRaises(py2dm.errors.FormatError):
            with py2dm.Reader(path) as mesh:
                _ = mesh.node(1)


class TestReadPedantic(unittest.TestCase):
    """Internal test cases for individual lines cards and lines."""

    def test_mesh2d(self) -> None:
        """Ensure only files starting with "MESH2D" are valid."""
        path = 'tests/data/nodes-only.2dm'
        with py2dm.Reader(path) as mesh:
            self.assertIsInstance(mesh, py2dm.Reader)
        path = 'tests/data/not-a-mesh.2dm'
        with self.assertRaises(py2dm.errors.ReadError):
            with py2dm.Reader(path) as mesh:
                pass

    def test_num_materials_per_elem(self) -> None:
        """Test the NUM_MATERIALS_PER_ELEM card."""
        path = 'tests/data/empty.2dm'
        with py2dm.Reader(path) as mesh:
            self.assertEqual(mesh.materials_per_element, 0)
        # TODO: Test other material numbers

    def test_nd(self) -> None:
        """Test the ND card, used for nodes."""
        # Known good
        line = 'ND 1 12 34 56'
        node = py2dm.Node.parse_line(line.split())
        self.assertEqual(node.id, 1)
        self.assertTupleEqual(node.pos, (12.0, 34.0, 56.0))
        # Bad card
        line = 'NE 1 1.0 2.0 3.0'
        with self.assertRaises(py2dm.errors.CardError):
            _ = py2dm.Node.parse_line(line.split())
        # Invalid node (too few coordinates: error)
        line = 'ND 2 21 43'
        with self.assertRaises(py2dm.errors.FormatError):
            _ = py2dm.Node.parse_line(line.split())
        # Invalid node (negative node ID: error)
        line = 'ND -3 21 43'
        with self.assertRaises(py2dm.errors.FormatError):
            _ = py2dm.Node.parse_line(line.split())
        # "Strange" node (too many coordinates: generic warning)
        line = 'ND 4 11 22 33 44'
        with self.assertWarns(py2dm.errors.FormatWarning):
            node = py2dm.Node.parse_line(line.split())
        self.assertEqual(node.id, 4)
        self.assertTupleEqual(node.pos, (12.0, 34.0, 56.0))
        # "Strange" TUFLOW-specific node (extra data ignored: specific warning)
        line = 'ND 5 1.0 2.0 3.0 2 0. 0. 0.'
        with self.assertWarns(py2dm.errors.CustomFormatIgnored):
            node = py2dm.Node.parse_line(line.split())
        self.assertEqual(node.id, 5)
        self.assertTupleEqual(node.pos, (1.0, 2.0, 3.0))

    def test_e2l(self) -> None:
        """Test the E2L card, used for simple linear elements."""
        # Known good
        line = 'E2L 1 2 3'
        element = py2dm.Element2L.parse_line(line.split())
        self.assertIsInstance(element, py2dm.Element2L)
        self.assertIsInstance(element, py2dm.LinearElement)
        # Known good (plus two materials)
        line = 'E2L 2 3 4 5 6'
        element = py2dm.Element2L.parse_line(line.split())
        self.assertIsInstance(element, py2dm.Element2L)
        self.assertIsInstance(element, py2dm.LinearElement)
        self.assertEqual(len(element.materials), 2)
        self.assertTupleEqual(element.materials, (5, 6))
        # Bad card
        line = 'E3L 3 4 5'
        with self.assertRaises(py2dm.errors.CardError):
            _ = py2dm.Element2L.parse_line(line.split())
        # Invalid element (negative element ID: error)
        line = 'E2L -4 5 6'
        with self.assertRaises(py2dm.errors.FormatError):
            _ = py2dm.Element2L.parse_line(line.split())
        # Invalid element (negative node ID: error)
        line = 'E2L 5 -6 7'
        with self.assertRaises(py2dm.errors.FormatError):
            _ = py2dm.Element2L.parse_line(line.split())
        # Invalid elements (too few node IDs: error)
        line = 'E2L 4 5'
        with self.assertRaises(py2dm.errors.FormatError):
            _ = py2dm.Element2L.parse_line(line.split())

    def test_e3l(self) -> None:
        """Test the E3L card, used for quadratic linear elements."""
        # Known good
        line = 'E3L 1 2 3 4'
        element = py2dm.Element3L.parse_line(line.split())
        self.assertIsInstance(element, py2dm.Element3L)
        self.assertIsInstance(element, py2dm.LinearElement)
        # Known good (plus two materials)
        line = 'E3L 2 3 4 5 6 7'
        element = py2dm.Element3L.parse_line(line.split())
        self.assertIsInstance(element, py2dm.Element3L)
        self.assertIsInstance(element, py2dm.LinearElement)
        self.assertEqual(len(element.materials), 2)
        self.assertTupleEqual(element.materials, (6, 7))
        # Bad card
        line = 'E2L 3 4 5'
        with self.assertRaises(py2dm.errors.CardError):
            _ = py2dm.Element3L.parse_line(line.split())
        # Invalid element (negative element ID: error)
        line = 'E3L -4 5 6 7'
        with self.assertRaises(py2dm.errors.FormatError):
            _ = py2dm.Element3L.parse_line(line.split())
        # Invalid element (negative node ID: error)
        line = 'E3L 5 -6 7 8'
        with self.assertRaises(py2dm.errors.FormatError):
            _ = py2dm.Element3L.parse_line(line.split())
        # Invalid elements (too few node IDs: error)
        line = 'E3L 6 7 8'
        with self.assertRaises(py2dm.errors.FormatError):
            _ = py2dm.Element3L.parse_line(line.split())

    def test_e3t(self) -> None:
        """Test the E3T card, used for simple triangular elements."""
        # Known good
        line = 'E3T 1 2 3 4'
        element = py2dm.Element3T.parse_line(line.split())
        self.assertIsInstance(element, py2dm.Element3T)
        self.assertIsInstance(element, py2dm.TriangularElement)
        # Known good (plus two materials)
        line = 'E3T 1 2 3 4 5 6'
        element = py2dm.Element3T.parse_line(line.split())
        self.assertIsInstance(element, py2dm.Element3T)
        self.assertIsInstance(element, py2dm.TriangularElement)
        self.assertEqual(len(element.materials), 2)
        self.assertTupleEqual(element.materials, (5, 6))
        # Bad card
        line = 'E3L 1 2 3 4'
        with self.assertRaises(py2dm.errors.CardError):
            _ = py2dm.Element3T.parse_line(line.split())
        # Invalid element (negative element ID: error)
        line = 'E3T -2 3 4 5'
        with self.assertRaises(py2dm.errors.FormatError):
            _ = py2dm.Element3T.parse_line(line.split())
        # Invalid element (negative node ID: error)
        line = 'E3T 3 -4 5 6'
        with self.assertRaises(py2dm.errors.FormatError):
            _ = py2dm.Element3T.parse_line(line.split())
        # Invalid elements (too few node IDs: error)
        line = 'E3T 4 5 6 7 8 9'
        with self.assertRaises(py2dm.errors.FormatError):
            _ = py2dm.Element3T.parse_line(line.split())

        # NOTE: The BASEMENT-specific element format is supported for all
        # elements, but only tested for E3T as that is the only type of element
        # supported by BASEMENT at the time of the writing.

        # BASEMENT-specific element format (float material: warning or ignored)
        line = 'E3T 5 6 7 8 9.5'
        with self.assertWarns(py2dm.errors.CustomFormatIgnored):
            _ = py2dm.Element3T.parse_line(line.split())
        with warnings.catch_warnings(record=True) as warnings_:
            _ = py2dm.Element3T.parse_line(
                line.split(), allow_float_materials=True)
            if warnings_:
                self.fail('Custom format warning not suppressed')

    def test_e6t(self) -> None:
        """Test the E6T card, used for quadratic triangular elements."""
        # Known good
        line = 'E6T 1 2 3 4 5 6 7'
        element = py2dm.Element6T.parse_line(line.split())
        self.assertIsInstance(element, py2dm.Element6T)
        self.assertIsInstance(element, py2dm.TriangularElement)
        # Known good (plus two materials)
        line = 'E6T 1 2 3 4 5 6 7 8 9'
        element = py2dm.Element6T.parse_line(line.split())
        self.assertIsInstance(element, py2dm.Element6T)
        self.assertIsInstance(element, py2dm.TriangularElement)
        self.assertEqual(len(element.materials), 2)
        self.assertTupleEqual(element.materials, (8, 9))
        # Bad card
        line = 'E3T 1 2 3 4 5 6 7'
        with self.assertRaises(py2dm.errors.CardError):
            _ = py2dm.Element6T.parse_line(line.split())
        # Invalid element (negative element ID: error)
        line = 'E6T -2 3 4 5 6 7 8'
        with self.assertRaises(py2dm.errors.FormatError):
            _ = py2dm.Element6T.parse_line(line.split())
        # Invalid element (negative node ID: error)
        line = 'E6T 3 -4 5 6 7 8 9'
        with self.assertRaises(py2dm.errors.FormatError):
            _ = py2dm.Element6T.parse_line(line.split())
        # Invalid elements (too few node IDs: error)
        line = 'E6T 4 5 6 7 8 9'
        with self.assertRaises(py2dm.errors.FormatError):
            _ = py2dm.Element6T.parse_line(line.split())

    def test_e4q(self) -> None:
        """Test the E4Q card, used for simple quadrilateral elements."""
        # Known good
        line = 'E4Q 1 2 3 4 5'
        element = py2dm.Element4Q.parse_line(line.split())
        self.assertIsInstance(element, py2dm.Element4Q)
        self.assertIsInstance(element, py2dm.QuadrilateralElement)
        # Known good (plus two materials)
        line = 'E4Q 1 2 3 4 5 6 7'
        element = py2dm.Element4Q.parse_line(line.split())
        self.assertIsInstance(element, py2dm.Element4Q)
        self.assertIsInstance(element, py2dm.QuadrilateralElement)
        self.assertEqual(len(element.materials), 2)
        self.assertTupleEqual(element.materials, (6, 7))
        # Bad card
        line = 'E3Q 1 2 3 4 5'
        with self.assertRaises(py2dm.errors.CardError):
            _ = py2dm.Element4Q.parse_line(line.split())
        # Invalid element (negative element ID: error)
        line = 'E4Q -2 3 4 5 6'
        with self.assertRaises(py2dm.errors.FormatError):
            _ = py2dm.Element4Q.parse_line(line.split())
        # Invalid element (negative node ID: error)
        line = 'E4Q 3 -4 5 6 7'
        with self.assertRaises(py2dm.errors.FormatError):
            _ = py2dm.Element4Q.parse_line(line.split())
        # Invalid elements (too few node IDs: error)
        line = 'E4Q 4 5 6 7'
        with self.assertRaises(py2dm.errors.FormatError):
            _ = py2dm.Element4Q.parse_line(line.split())

    def test_e8q(self) -> None:
        """Test the E8Q card, used for quadratic quadrilateral elements."""
        # Known good
        line = 'E8Q 1 2 3 4 5 6 7 8 9'
        element = py2dm.Element8Q.parse_line(line.split())
        self.assertIsInstance(element, py2dm.Element8Q)
        self.assertIsInstance(element, py2dm.QuadrilateralElement)
        # Known good (plus two materials)
        line = 'E8Q 1 2 3 4 5 6 7 8 9 10 11'
        element = py2dm.Element8Q.parse_line(line.split())
        self.assertIsInstance(element, py2dm.Element8Q)
        self.assertIsInstance(element, py2dm.QuadrilateralElement)
        self.assertEqual(len(element.materials), 2)
        self.assertTupleEqual(element.materials, (10, 11))
        # Bad card
        line = 'E6Q 1 2 3 4 5 6 7 8 9'
        with self.assertRaises(py2dm.errors.CardError):
            _ = py2dm.Element8Q.parse_line(line.split())
        # Invalid element (negative element ID: error)
        line = 'E8Q -2 3 4 5 6 7 8 9 10'
        with self.assertRaises(py2dm.errors.FormatError):
            _ = py2dm.Element8Q.parse_line(line.split())
        # Invalid element (negative node ID: error)
        line = 'E8Q 3 -4 5 6 7 8 9 10 11'
        with self.assertRaises(py2dm.errors.FormatError):
            _ = py2dm.Element8Q.parse_line(line.split())
        # Invalid elements (too few node IDs: error)
        line = 'E8Q 4 5 6 7 8 9 10 11'
        with self.assertRaises(py2dm.errors.FormatError):
            _ = py2dm.Element8Q.parse_line(line.split())

    def test_e9q(self) -> None:
        """Test the E9Q card, used for quadratic quadrilateral elements.

        This variant has an extra vertex in the centre.
        """
        # Known good
        line = 'E9Q 1 2 3 4 5 6 7 8 9 10'
        element = py2dm.Element9Q.parse_line(line.split())
        self.assertIsInstance(element, py2dm.Element9Q)
        self.assertIsInstance(element, py2dm.QuadrilateralElement)
        # Known good (plus two materials)
        line = 'E9Q 1 2 3 4 5 6 7 8 9 10 11 12'
        element = py2dm.Element9Q.parse_line(line.split())
        self.assertIsInstance(element, py2dm.Element9Q)
        self.assertIsInstance(element, py2dm.QuadrilateralElement)
        self.assertEqual(len(element.materials), 2)
        self.assertTupleEqual(element.materials, (11, 12))
        # Bad card
        line = 'E6Q 1 2 3 4 5 6 7 8 9 10'
        with self.assertRaises(py2dm.errors.CardError):
            _ = py2dm.Element9Q.parse_line(line.split())
        # Invalid element (negative element ID: error)
        line = 'E9Q -2 3 4 5 6 7 8 9 10 11'
        with self.assertRaises(py2dm.errors.FormatError):
            _ = py2dm.Element9Q.parse_line(line.split())
        # Invalid element (negative node ID: error)
        line = 'E9Q 3 -4 5 6 7 8 9 10 11 12'
        with self.assertRaises(py2dm.errors.FormatError):
            _ = py2dm.Element9Q.parse_line(line.split())
        # Invalid elements (too few node IDs: error)
        line = 'E9Q 4 5 6 7 8 9 10 11 12'
        with self.assertRaises(py2dm.errors.FormatError):
            _ = py2dm.Element9Q.parse_line(line.split())

    def test_ns(self) -> None:
        """Test the node string parser."""
        # Single line test
        line = 'NS 1 2 3 4 5 -6'
        string, flag = py2dm.NodeString.parse_line(line.split())
        self.assertTrue(flag)
        self.assertEqual(string.num_nodes, 6)
        self.assertIsNone(string.name)
        # Multiline test
        line_1 = 'NS 1 2 3 4 5 6 7 8 9 10'
        line_2 = 'NS 11 12 13 14 15 16 17 18 19 20'
        line_3 = 'NS 21 22 23 24 25 26 27 28 29 -30'
        string, flag = py2dm.NodeString.parse_line(line_1.split())
        self.assertFalse(flag)
        string, flag = py2dm.NodeString.parse_line(line_2.split(), string)
        self.assertFalse(flag)
        string, flag = py2dm.NodeString.parse_line(line_3.split(), string)
        self.assertTrue(flag)
        self.assertEqual(string.num_nodes, 30)
        self.assertIsNone(string.name)
        # Long line test
        line = 'NS 1 2 3 4 5 6 7 8 9 10 11 12 13 14 -15'
        string, flag = py2dm.NodeString.parse_line(line.split())
        self.assertTrue(flag)
        self.assertEqual(string.num_nodes, 15)
        self.assertIsNone(string.name)
        # Test numerical ID (as used by TUFLOW)
        line = 'NS 1 2 3 4 5 6 7 8 9 -10 11'
        string, flag = py2dm.NodeString.parse_line(line.split())
        self.assertTrue(flag)
        self.assertEqual(string.num_nodes, 10)
        self.assertEqual(string.name, '11')
        # Test raw string ID (as used by BASEMENT)
        line = 'NS 1 2 3 4 5 6 7 8 9 -10 string1'
        string, flag = py2dm.NodeString.parse_line(line.split())
        self.assertTrue(flag)
        self.assertEqual(string.num_nodes, 10)
        self.assertEqual(string.name, 'string1')
        # Test raw multi-word string (expected warning to use quotes)
        line = 'NS 1 2 3 4 5 6 7 8 9 -10 string2 string3'
        with self.assertWarns(py2dm.errors.FormatWarning):
            string, flag = py2dm.NodeString.parse_line(line.split())
        self.assertTrue(flag)
        self.assertEqual(string.num_nodes, 10)
        self.assertEqual(string.name, 'string2 string3')
        # Test quoted string ID (no known users but most sensible)
        line = 'NS 1 2 3 4 5 6 7 8 9 -10 "string4"'
        string, flag = py2dm.NodeString.parse_line(line.split())
        self.assertTrue(flag)
        self.assertEqual(string.num_nodes, 10)
        self.assertEqual(string.name, 'string4')
