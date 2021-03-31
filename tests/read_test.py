"""Unit tests for the reader class."""

import unittest
import warnings

import py2dm  # pylint: disable=import-error


@unittest.skip('disabled')
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
        with warnings.catch_warnings(record=True):
            with py2dm.Reader(path, materials=1) as mesh:
                self.assertEqual(mesh.num_elements, 20486)
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
        with warnings.catch_warnings(record=True):
            with py2dm.Reader(path, materials=1) as mesh:
                # TODO: Add compatibility flags for TUFLOW georeferencing
                self.assertEqual(mesh.num_elements, 1875)
                self.assertEqual(mesh.num_nodes, 1976)
                self.assertTupleEqual(
                    mesh.node(800).pos, (381527.785, 168720.985, 35.879))
                self.assertTupleEqual(
                    mesh.element(1111).nodes, (1202, 1201, 1125, 1126))

    def test_triangle_e6t(self) -> None:
        path = 'tests/data/external/mdal/triangleE6T.2dm'
        # NOTE: This mesh has poorly formatted IDs and is not valid for Py2DM
        with self.assertRaises(py2dm.errors.FormatError):
            with py2dm.Reader(path, materials=1):
                pass

    def test_unordered_ids(self) -> None:
        path = 'tests/data/external/mdal/unordered_ids.2dm'
        with self.assertRaises(py2dm.errors.FormatError):
            with py2dm.Reader(path, materials=1):
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


@unittest.skip('disabled')
class TestReadRealistic(unittest.TestCase):
    """Test the read behaviour for real-world test meshes."""

    def test_tm_forum_one(self) -> None:
        path = 'tests/data/external/tm_forum/HYDRO_AS-2D.2dm'
        # NOTE: This mesh has holes in its element IDs and cannot be read by
        # Py2DM. Once the converter/conformer has been added, it should be
        # enabled here.
        with self.assertRaises(py2dm.errors.FormatError):
            with py2dm.Reader(path, materials=1):
                pass

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
