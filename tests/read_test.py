"""Unit tests for the reader class."""

import unittest

import py2dm  # pylint: disable=import-error


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
