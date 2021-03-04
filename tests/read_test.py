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
        self.assertSequenceEqual(str(node), f'Node #1: (12.0, 34.0, 56.0)')
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
        self.assertSequenceEqual(
            str(element), 'Element #1 [E2L]: Node IDs (2, 3)')
        self.assertEqual(element.num_materials, 0)
        # Known good (plus two materials)
        line = 'E2L 2 3 4 5 6'
        element = py2dm.Element2L.parse_line(line.split())
        self.assertIsInstance(element, py2dm.Element2L)
        self.assertIsInstance(element, py2dm.LinearElement)
        self.assertEqual(len(element.materials), 2)
        self.assertTupleEqual(element.materials, (5, 6))
        self.assertEqual(element.num_materials, 2)
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
        self.assertSequenceEqual(
            str(element), 'Element #1 [E3L]: Node IDs (2, 3, 4)')
        self.assertEqual(element.num_materials, 0)
        # Known good (plus two materials)
        line = 'E3L 2 3 4 5 6 7'
        element = py2dm.Element3L.parse_line(line.split())
        self.assertIsInstance(element, py2dm.Element3L)
        self.assertIsInstance(element, py2dm.LinearElement)
        self.assertEqual(len(element.materials), 2)
        self.assertTupleEqual(element.materials, (6, 7))
        self.assertEqual(element.num_materials, 2)
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
        self.assertSequenceEqual(
            str(element), 'Element #1 [E3T]: Node IDs (2, 3, 4)')
        self.assertEqual(element.num_materials, 0)
        # Known good (plus two materials)
        line = 'E3T 1 2 3 4 5 6'
        element = py2dm.Element3T.parse_line(line.split())
        self.assertIsInstance(element, py2dm.Element3T)
        self.assertIsInstance(element, py2dm.TriangularElement)
        self.assertEqual(len(element.materials), 2)
        self.assertTupleEqual(element.materials, (5, 6))
        self.assertEqual(element.num_materials, 2)
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
        self.assertSequenceEqual(
            str(element), 'Element #1 [E6T]: Node IDs (2, 3, 4, 5, 6, 7)')
        self.assertEqual(element.num_materials, 0)
        # Known good (plus two materials)
        line = 'E6T 1 2 3 4 5 6 7 8 9'
        element = py2dm.Element6T.parse_line(line.split())
        self.assertIsInstance(element, py2dm.Element6T)
        self.assertIsInstance(element, py2dm.TriangularElement)
        self.assertEqual(len(element.materials), 2)
        self.assertTupleEqual(element.materials, (8, 9))
        self.assertEqual(element.num_materials, 2)
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
        self.assertSequenceEqual(
            str(element), 'Element #1 [E4Q]: Node IDs (2, 3, 4, 5)')
        self.assertEqual(element.num_materials, 0)
        # Known good (plus two materials)
        line = 'E4Q 1 2 3 4 5 6 7'
        element = py2dm.Element4Q.parse_line(line.split())
        self.assertIsInstance(element, py2dm.Element4Q)
        self.assertIsInstance(element, py2dm.QuadrilateralElement)
        self.assertEqual(len(element.materials), 2)
        self.assertTupleEqual(element.materials, (6, 7))
        self.assertEqual(element.num_materials, 2)
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
        self.assertSequenceEqual(str(element), 'Element #1 [E8Q]: Node IDs '
                                 '(2, 3, 4, 5, 6, 7, 8, 9)')
        self.assertEqual(element.num_materials, 0)
        # Known good (plus two materials)
        line = 'E8Q 1 2 3 4 5 6 7 8 9 10 11'
        element = py2dm.Element8Q.parse_line(line.split())
        self.assertIsInstance(element, py2dm.Element8Q)
        self.assertIsInstance(element, py2dm.QuadrilateralElement)
        self.assertEqual(len(element.materials), 2)
        self.assertTupleEqual(element.materials, (10, 11))
        self.assertEqual(element.num_materials, 2)
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
        self.assertSequenceEqual(str(element), 'Element #1 [E9Q]: Node IDs '
                                 '(2, 3, 4, 5, 6, 7, 8, 9, 10)')
        self.assertEqual(element.num_materials, 0)
        # Known good (plus two materials)
        line = 'E9Q 1 2 3 4 5 6 7 8 9 10 11 12'
        element = py2dm.Element9Q.parse_line(line.split())
        self.assertIsInstance(element, py2dm.Element9Q)
        self.assertIsInstance(element, py2dm.QuadrilateralElement)
        self.assertEqual(len(element.materials), 2)
        self.assertTupleEqual(element.materials, (11, 12))
        self.assertEqual(element.num_materials, 2)
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
        self.assertSequenceEqual(
            str(string), 'Unnamed NodeString: (1, 2, 3, 4, 5, 6)')
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
        self.assertSequenceEqual(
            str(string), 'NodeString "11": (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)')
        # Test raw string ID (as used by BASEMENT)
        line = 'NS 1 2 3 4 5 6 7 8 9 -10 string1'
        string, flag = py2dm.NodeString.parse_line(line.split())
        self.assertTrue(flag)
        self.assertEqual(string.num_nodes, 10)
        self.assertEqual(string.name, 'string1')
        self.assertSequenceEqual(str(string), 'NodeString "string1": '
                                 '(1, 2, 3, 4, 5, 6, 7, 8, 9, 10)')
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


class TestReadMDAL(unittest.TestCase):
    """Additional test cases using example meshes from MDAL."""

    def test_lines(self) -> None:
        path = 'tests/data/external/mdal/lines.2dm'
        with py2dm.Reader(path, materials=1) as mesh:
            self.assertEqual(mesh.num_elements, 3)
            self.assertEqual(mesh.num_node_strings, 0)
            self.assertEqual(mesh.num_nodes, 4)
            self.assertEqual(mesh.materials_per_element, 1)
            self.assertTupleEqual(mesh.node(1).pos, (1000.0, 2000.0, 20.0))
            self.assertTupleEqual(mesh.node(4).pos, (2000.0, 3000.0, 50.0))

    def test_tuflow_m01_5m(self) -> None:
        path = 'tests/data/external/mdal/M01_5m_002.2dm'
        with py2dm.Reader(path, materials=1) as mesh:
            self.assertEqual(mesh.num_elements, 20893)
            self.assertEqual(mesh.num_node_strings, 0)
            self.assertEqual(mesh.num_nodes, 20893)
            self.assertEqual(mesh.materials_per_element, 1)
            self.assertTupleEqual(
                mesh.node(20890).pos, (293604.333, 6178410.628, 44.671))

    def test_numbering_gaps(self) -> None:
        path = 'tests/data/external/mdal/mesh_with_numbering_gaps.2dm'
        with self.assertRaises(py2dm.errors.FormatError):
            with py2dm.Reader(path, materials=1) as mesh:
                _ = mesh.element(1)

    def test_multi_material(self) -> None:
        path = 'tests/data/external/mdal/multi_material.2dm'
        with py2dm.Reader(path) as mesh:
            self.assertEqual(mesh.num_elements, 12)
            self.assertEqual(mesh.num_node_strings, 0)
            self.assertEqual(mesh.num_nodes, 11)
            self.assertEqual(mesh.materials_per_element, 3)
            self.assertTupleEqual(mesh.node(10).pos, (0.0, 10.0, 15.0))
            self.assertTupleEqual(mesh.element(2).materials, (1, 10.0, 1))
            self.assertTupleEqual(mesh.element(2).nodes, (2, 5, 6))

    def test_not_a_mesh_file(self) -> None:
        path = 'tests/data/external/mdal/not_a_mesh_file.2dm'
        with self.assertRaises(py2dm.errors.ReadError):
            with py2dm.Reader(path):
                pass

    def test_quad_and_line(self) -> None:
        path = 'tests/data/external/mdal/quad_and_line.2dm'
        with py2dm.Reader(path, materials=1) as mesh:
            self.assertEqual(mesh.num_elements, 2)
            self.assertEqual(mesh.num_nodes, 5)
            self.assertTupleEqual(mesh.node(4).pos, (2000.0, 3000.0, 50.0))
            self.assertTupleEqual(mesh.element(1).nodes, (1, 2, 4, 5))
            self.assertTupleEqual(mesh.element(2).nodes, (2, 3))

    def test_quad_and_triangle(self) -> None:
        path = 'tests/data/external/mdal/quad_and_triangle.2dm'
        with py2dm.Reader(path, materials=1) as mesh:
            self.assertEqual(mesh.num_elements, 2)
            self.assertEqual(mesh.num_nodes, 5)
            self.assertTupleEqual(mesh.node(4).pos, (2000.0, 3000.0, 50.0))
            self.assertTupleEqual(mesh.element(1).nodes, (1, 2, 4, 5))
            self.assertTupleEqual(mesh.element(2).nodes, (2, 3, 4))

    def test_regular_grid(self) -> None:
        path = 'tests/data/external/mdal/regular_grid.2dm'
        with py2dm.Reader(path, materials=1) as mesh:
            # TODO: Add compatibility flags for TUFLOW georeferencing
            self.assertEqual(mesh.num_elements, 2)
            self.assertEqual(mesh.num_nodes, 2)
            self.assertTupleEqual(
                mesh.node(800).pos, (381527.785, 168720.985, 35.879))
            self.assertTupleEqual(
                mesh.element(1111).nodes, (1202, 1201, 1125, 1126))

    def test_triangle_e6t(self) -> None:
        path = 'tests/data/external/mdal/triangleE6T.2dm'
        with py2dm.Reader(path, materials=1) as mesh:
            self.assertEqual(mesh.num_elements, 6)
            self.assertEqual(mesh.num_nodes, 26)
            self.assertEqual(mesh.num_node_strings, 0)
            self.assertEqual(mesh.materials_per_element, 1)
            self.assertTupleEqual(mesh.node(14).pos, (8.281, 7.819, 0.0))
            self.assertIsInstance(mesh.element(1), py2dm.Element6T)
            self.assertTupleEqual(
                mesh.element(4).nodes, (6, 21, 13, 22, 14, 19))

    def test_unordered_ids(self) -> None:
        path = 'tests/data/external/mdal/unordered_ids.2dm'
        with self.assertRaises(py2dm.errors.FormatError):
            with py2dm.Reader(path, materials=1) as mesh:
                # TODO: Add info text about how to renumber a mesh
                pass

    def test_e8q(self) -> None:
        # NOTE: This file is taken from the MDAL repository without change, but
        # Py2DM does support this element - the file name is a lie.
        path = 'tests/data/external/mdal/unsupported_elements.2dm'
        with py2dm.Reader(path, materials=1) as mesh:
            self.assertEqual(mesh.num_elements, 1)
            self.assertEqual(mesh.num_nodes, 8)
            self.assertEqual(mesh.num_node_strings, 0)
            self.assertEqual(mesh.materials_per_element, 1)
            self.assertTupleEqual(mesh.node(5).pos, (2000.0, 1000.0, 20.0))
            self.assertIsInstance(mesh.element(1), py2dm.Element8Q)
            self.assertTupleEqual(
                mesh.element(1).nodes, (1, 2, 3, 4, 5, 6, 7, 8))


class TestReadRealistic(unittest.TestCase):
    """Test the read behaviour for real-world test meshes."""

    def test_tm_forum_one(self) -> None:
        path = 'tests/data/external/tm_forum/HYDRO_AS-2D.2dm'
        with py2dm.Reader(path, materials=1) as mesh:
            self.assertEqual(mesh.name, 'HYDRO_AS-2D V2.1')
            self.assertEqual(mesh.num_elements, 111761)
            self.assertEqual(mesh.num_node_strings, 3)
            self.assertEqual(mesh.num_nodes, 57094)
            self.assertEqual(mesh.materials_per_element, 1)
            self.assertTupleEqual(
                mesh.node(420).pos, (7.10408867e+5, 9.61317448e+6, 9.0e+1))
            self.assertTupleEqual(mesh.element(10).nodes, (15, 5, 16))
            self.assertListEqual(
                list(mesh.node_strings)[1].nodes[:10], list(range(10)))

    def test_tm_forum_two(self) -> None:
        path = 'tests/data/external/tm_forum/original_mesh.2dm'
        with py2dm.Reader(path, materials=1) as mesh:
            self.assertEqual(mesh.name, 'Mesh')
            self.assertEqual(mesh.num_elements, 31580)
            self.assertEqual(mesh.num_node_strings, 0)
            self.assertEqual(mesh.num_nodes, 17151)
            self.assertEqual(mesh.materials_per_element, 1)
            self.assertTupleEqual(
                mesh.node(1337).pos, (5.52522763e+5, 8.56166681e+6, -1.0e0))
            self.assertTupleEqual(
                mesh.element(10000).nodes, (5539, 5359, 5360))
