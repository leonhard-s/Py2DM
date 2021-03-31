"""Test cases for the py2dm.Reader class."""

import math
import os
from typing import Iterator
import unittest

import py2dm  # pylint: disable=import-error


class TestReader(unittest.TestCase):
    """Tests for the py2dm.Reader class."""

    _PATH = os.path.join('tests', 'data', 'basic-node-strings.2dm')

    def test___init__(self) -> None:
        path = os.path.join('path', 'to', 'mesh')
        reader = py2dm.Reader(path)
        self.assertEqual(
            reader.name, 'Unnamed mesh',
            'unpexected default mesh name')
        self.assertTrue(
            reader.closed,
            'reader not closed')
        with self.assertRaises(py2dm.errors.FileIsClosedError):
            _ = reader.element(1)

    def test_context_manager(self) -> None:
        reader = py2dm.Reader(self._PATH)
        self.assertTrue(
            reader.closed,
            'reader not closed upon instantiation')
        with reader as mesh:
            self.assertFalse(
                reader.closed,
                'reader not opening with context manager')
            self.assertIs(
                reader, mesh,
                'reader __enter__ does not return self')
        self.assertTrue(
            reader.closed,
            'reader not closed after leaving context manager')

    def test___str__(self) -> None:
        reader = py2dm.Reader(self._PATH)
        self.assertEqual(
            str(reader), 'Py2DM Reader (closed)',
            'unexpected string representation')
        reader.open()
        self.assertEqual(
            str(reader),
            ('Py2DM Reader\n'
             '\t5 nodes\n'
             '\t4 elements\n'
             '\t2 node strings'),
            'unexpected string representation')
        reader.close()
        self.assertEqual(
            str(reader), 'Py2DM Reader (closed)',
            'unexpected string representation')

    def test_extent(self) -> None:
        with py2dm.Reader(self._PATH) as mesh:
            self.assertTupleEqual(
                mesh.extent, (-5.0, 5.0, -5.0, 5.0),
                'incorrect mesh extent')
        with self.subTest('closed'):
            reader = py2dm.Reader(self._PATH)
            with self.assertRaises(py2dm.errors.FileIsClosedError):
                _ = reader.extent
        with self.subTest('empty'):
            path = os.path.join('tests', 'data', 'empty-mesh.2dm')
            with py2dm.Reader(path) as mesh:
                self.assertTrue(
                    all((math.isnan(f) for f in mesh.extent)),
                    'mesh extent not empty')

    def test_elements(self) -> None:
        with py2dm.Reader(self._PATH) as mesh:
            self.assertIsInstance(
                mesh.elements, Iterator,
                'not subclass of iterator')
            self.assertListEqual(
                list(mesh.elements),
                list(mesh.iter_elements()),
                'differing elements list')
        with self.subTest('closed'):
            reader = py2dm.Reader(self._PATH)
            with self.assertRaises(py2dm.errors.FileIsClosedError):
                _ = reader.elements

    def test_nodes(self) -> None:
        with py2dm.Reader(self._PATH) as mesh:
            self.assertIsInstance(
                mesh.nodes, Iterator,
                'not subclass of iterator')
            self.assertListEqual(
                list(mesh.nodes),
                list(mesh.iter_nodes()),
                'differing nodes list')
        with self.subTest('closed'):
            reader = py2dm.Reader(self._PATH)
            with self.assertRaises(py2dm.errors.FileIsClosedError):
                _ = reader.nodes

    def test_node_strings(self) -> None:
        with py2dm.Reader(self._PATH) as mesh:
            self.assertIsInstance(
                mesh.node_strings, Iterator,
                'not subclass of iterator')
            self.assertListEqual(
                list(mesh.node_strings),
                list(mesh.iter_node_strings()),
                'differing node strings list')
        with self.subTest('closed'):
            reader = py2dm.Reader(self._PATH)
            with self.assertRaises(py2dm.errors.FileIsClosedError):
                _ = reader.node_strings

    def test_materials_per_element(self) -> None:
        with py2dm.Reader(self._PATH) as mesh:
            self.assertEqual(
                mesh.materials_per_element, 0,
                'bad material count')
        with self.subTest('closed'):
            reader = py2dm.Reader(self._PATH)
            with self.assertRaises(py2dm.errors.FileIsClosedError):
                _ = reader.materials_per_element

    def test_num_elements(self) -> None:
        with py2dm.Reader(self._PATH) as mesh:
            self.assertEqual(
                mesh.num_elements, 4,
                'bad element count')
        with self.subTest('closed'):
            reader = py2dm.Reader(self._PATH)
            with self.assertRaises(py2dm.errors.FileIsClosedError):
                _ = reader.num_elements

    def test_num_nodes(self) -> None:
        with py2dm.Reader(self._PATH) as mesh:
            self.assertEqual(
                mesh.num_nodes, 5,
                'bad node count')
        with self.subTest('closed'):
            reader = py2dm.Reader(self._PATH)
            with self.assertRaises(py2dm.errors.FileIsClosedError):
                _ = reader.num_nodes

    def test_num_node_strings(self) -> None:
        with py2dm.Reader(self._PATH) as mesh:
            self.assertEqual(
                mesh.num_node_strings, 2,
                'bad node string count')
        with self.subTest('closed'):
            reader = py2dm.Reader(self._PATH)
            with self.assertRaises(py2dm.errors.FileIsClosedError):
                _ = reader.num_node_strings

    def test_open_close(self) -> None:
        reader = py2dm.Reader(self._PATH)
        with self.assertRaises(py2dm.errors.FileIsClosedError):
            _ = reader.element(1)
        with self.assertRaises(py2dm.errors.FileIsClosedError):
            _ = reader.num_nodes
        reader.open()
        self.assertFalse(
            reader.closed,
            'reader closed after open() call')
        _ = reader.element(1)  # Test for erroneous exception
        reader.close()
        self.assertTrue(
            reader.closed,
            'reader not closed after close() call')
        with self.assertRaises(py2dm.errors.FileIsClosedError):
            _ = reader.element(1)

    def test_element(self) -> None:
        with py2dm.Reader(self._PATH) as mesh:
            with self.subTest('valid'):
                self.assertEqual(
                    mesh.element(1),
                    py2dm.Element3T(1, 1, 2, 3),
                    'unexpected element')
            with self.subTest('too low'):
                with self.assertRaises(KeyError):
                    _ = mesh.element(0)
            with self.subTest('too high'):
                with self.assertRaises(KeyError):
                    _ = mesh.element(5)
        with self.subTest('closed'):
            reader = py2dm.Reader(self._PATH)
            with self.assertRaises(py2dm.errors.FileIsClosedError):
                _ = reader.extent

    def test_node(self) -> None:
        with py2dm.Reader(self._PATH) as mesh:
            with self.subTest('valid'):
                self.assertEqual(
                    mesh.node(2),
                    py2dm.Node(2, -5.0, 5.0, 2.0),
                    'unexpected node')
            with self.subTest('too low'):
                with self.assertRaises(KeyError):
                    _ = mesh.node(0)
            with self.subTest('too high'):
                with self.assertRaises(KeyError):
                    _ = mesh.node(6)
        with self.subTest('closed'):
            reader = py2dm.Reader(self._PATH)
            with self.assertRaises(py2dm.errors.FileIsClosedError):
                _ = reader.extent

    def test_node_string(self) -> None:
        with py2dm.Reader(self._PATH) as mesh:
            with self.subTest('valid'):
                self.assertEqual(
                    mesh.node_string('first'),
                    py2dm.NodeString(1, 2, 4, 3, name='first'),
                    'unexpected node string')
            with self.subTest('bad name'):
                with self.assertRaises(KeyError):
                    _ = mesh.node_string('third')
        with self.subTest('closed'):
            reader = py2dm.Reader(self._PATH)
            with self.assertRaises(py2dm.errors.FileIsClosedError):
                _ = reader.extent

    def test_iter_elements(self) -> None:
        with py2dm.Reader(self._PATH) as mesh:
            with self.subTest('full'):
                self.assertListEqual(
                    list(mesh.iter_elements()),
                    # pylint: disable=private-access
                    mesh._cache_elements,  # type: ignore
                    'unexpected element list')
            with self.subTest('subset'):
                self.assertListEqual(
                    list(mesh.iter_elements(2, 3)),
                    [py2dm.Element3T(2, 2, 3, 4),
                     py2dm.Element2L(3, 1, 3)],
                    'unexpected element list')
            with self.subTest('subset (lower unbounded)'):
                self.assertListEqual(
                    list(mesh.iter_elements(-1, 2)),
                    [py2dm.Element3T(1, 1, 2, 3),
                     py2dm.Element3T(2, 2, 3, 4)],
                    'unexpected element list')
            with self.subTest('subset (upper unbounded)'):
                self.assertListEqual(
                    list(mesh.iter_elements(3, -1)),
                    [py2dm.Element2L(3, 1, 3),
                     py2dm.Element2L(4, 2, 4)],
                    'unexpected element list')
            with self.subTest('start < min'):
                with self.assertRaises(IndexError):
                    _ = mesh.iter_elements(0)
            with self.subTest('start > max'):
                with self.assertRaises(IndexError):
                    _ = mesh.iter_elements(mesh.num_elements+1)
            with self.subTest('end < start'):
                with self.assertRaises(IndexError):
                    _ = mesh.iter_elements(4, 3)
            with self.subTest('end == start'):
                with self.assertRaises(IndexError):
                    _ = mesh.iter_elements(3, 3)
            with self.subTest('end > max'):
                with self.assertRaises(IndexError):
                    _ = mesh.iter_elements(1, mesh.num_elements+1)
        with self.subTest('closed'):
            reader = py2dm.Reader(self._PATH)
            with self.assertRaises(py2dm.errors.FileIsClosedError):
                _ = reader.extent

    def test_iter_nodes(self) -> None:
        with py2dm.Reader(self._PATH) as mesh:
            with self.subTest('full'):
                self.assertListEqual(
                    list(mesh.iter_nodes()),
                    # pylint: disable=private-access
                    mesh._cache_nodes,  # type: ignore
                    'unexpected node list')
            with self.subTest('subset'):
                self.assertListEqual(
                    list(mesh.iter_nodes(2, 4)),
                    [py2dm.Node(2, -5.0, 5.0, 2.0),
                     py2dm.Node(3, 5.0, -5.0, -3.0),
                     py2dm.Node(4, 5.0, 5.0, 4.0)],
                    'unexpected node list')
            with self.subTest('subset (lower unbounded)'):
                self.assertListEqual(
                    list(mesh.iter_nodes(-1, 2)),
                    [py2dm.Node(1, -5.0, -5.0, -1.0),
                     py2dm.Node(2, -5.0, 5.0, 2.0)],
                    'unexpected node list')
            with self.subTest('subset (upper unbounded)'):
                self.assertListEqual(
                    list(mesh.iter_nodes(3, -1)),
                    [py2dm.Node(3, 5.0, -5.0, -3.0),
                     py2dm.Node(4, 5.0, 5.0, 4.0),
                     py2dm.Node(5, 0.0, 0.0, 5.0)],
                    'unexpected node list')
            with self.subTest('start < min'):
                with self.assertRaises(IndexError):
                    _ = mesh.iter_nodes(0)
            with self.subTest('start > max'):
                with self.assertRaises(IndexError):
                    _ = mesh.iter_nodes(mesh.num_nodes+1)
            with self.subTest('end < start'):
                with self.assertRaises(IndexError):
                    _ = mesh.iter_nodes(4, 3)
            with self.subTest('end == start'):
                with self.assertRaises(IndexError):
                    _ = mesh.iter_nodes(3, 3)
            with self.subTest('end > max'):
                with self.assertRaises(IndexError):
                    _ = mesh.iter_nodes(1, mesh.num_nodes+1)
        with self.subTest('closed'):
            reader = py2dm.Reader(self._PATH)
            with self.assertRaises(py2dm.errors.FileIsClosedError):
                _ = reader.extent

    def test_iter_node_strings(self) -> None:
        with py2dm.Reader(self._PATH) as mesh:
            with self.subTest('full'):
                self.assertListEqual(
                    list(mesh.iter_node_strings()),
                    # pylint: disable=private-access
                    mesh._cache_node_strings,  # type: ignore
                    'unexpected node string list')
            with self.subTest('subset'):
                self.assertListEqual(
                    list(mesh.iter_node_strings(0, 2)),
                    [py2dm.NodeString(1, 2, 4, 3, name='first'),
                     py2dm.NodeString(4, 5, 1, name='second')],
                    'unexpected node string list')
            with self.subTest('subset (lower unbounded)'):
                self.assertListEqual(
                    list(mesh.iter_node_strings(-1, 1)),
                    [py2dm.NodeString(1, 2, 4, 3, name='first')],
                    'unexpected node string list')
            with self.subTest('subset (upper unbounded)'):
                self.assertListEqual(
                    list(mesh.iter_node_strings(1, -1)),
                    [py2dm.NodeString(4, 5, 1, name='second')],
                    'unexpected node string list')
            with self.subTest('start > max'):
                with self.assertRaises(IndexError):
                    _ = mesh.iter_node_strings(mesh.num_node_strings)
            with self.subTest('end < start'):
                with self.assertRaises(IndexError):
                    _ = mesh.iter_node_strings(1, 0)
            with self.subTest('end == start'):
                with self.assertRaises(IndexError):
                    _ = mesh.iter_node_strings(1, 1)
            with self.subTest('end > max'):
                with self.assertRaises(IndexError):
                    _ = mesh.iter_node_strings(0, mesh.num_node_strings+1)
        with self.subTest('closed'):
            reader = py2dm.Reader(self._PATH)
            with self.assertRaises(py2dm.errors.FileIsClosedError):
                _ = reader.extent

    def test_element_factory(self) -> None:
        from py2dm._read import _element_factory as get_element
        elements = {'E2L': py2dm.Element2L,
                    'E3L': py2dm.Element3L,
                    'E3T': py2dm.Element3T,
                    'E4Q': py2dm.Element4Q,
                    'E6T': py2dm.Element6T,
                    'E8Q': py2dm.Element8Q,
                    'E9Q': py2dm.Element9Q}
        for card, instance in elements.items():
            with self.subTest(f'{card} element'):
                line = f'{card} 1 2 3 4 5 6 7 8.0 -9 # 10'
                self.assertEqual(
                    get_element(line), instance,
                    'wrong class returned')
        with self.subTest('fallback error'):
            with self.assertRaises(NotImplementedError):
                get_element('NOT-AN-ELEMENT lorem ipsum dolor sit amet')


class TestReadSynthetic(unittest.TestCase):
    """Short, synthetic files to check specific parsing behaviours."""

    _DATA_DIR = 'tests/data/'

    @classmethod
    def data(cls, filename: str) -> str:
        """Return an absolute path to a synthetic test file."""
        return os.path.abspath(
            os.path.join(cls._DATA_DIR, filename))

    def test_empty_mesh(self) -> None:
        path = self.data('empty-mesh.2dm')
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
        path = self.data('empty-file.2dm')
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
            self.assertEqual(
                mesh.materials_per_element, 0,
                'incorrect number of materials')
            self.assertListEqual(
                list(mesh.iter_elements()), list(mesh.elements),
                'bad element iterator')
            self.assertListEqual(
                list(mesh.iter_nodes()), list(mesh.nodes),
                'bad node iterator')
            self.assertListEqual(
                list(mesh.iter_node_strings()), list(mesh.node_strings),
                'bad node string iterator')
            self.assertEqual(
                mesh.element(2),
                py2dm.Element3T(2, 2, 3, 4),
                'bad element')
            self.assertEqual(
                mesh.node(3),
                py2dm.Node(3, 5.0, -5.0, -3.0),
                'bad node')
            self.assertEqual(
                mesh.node_string('second'),
                py2dm.NodeString(4, 5, 1, name='second'),
                'bad node string')


class TestReadMdal(unittest.TestCase):
    """Extra test cases from the MDAL repository.

    These mostly exist to ensure compatibility/known incompatibilities
    between the two libraries, and between Py2DM and QGIS 3 (which uses
    MDAL for its mesh data support).
    """

    _DATA_DIR = 'tests/data/external/mdal'

    @classmethod
    def data(cls, filename: str) -> str:
        """Return an absolute path to a synthetic test file."""
        return os.path.abspath(
            os.path.join(cls._DATA_DIR, filename))

    def test_lines(self) -> None:
        path = self.data('lines.2dm')
        with py2dm.Reader(path, materials=1) as mesh:
            self.assertEqual(
                mesh.num_elements, 3,
                'incorrect element count')
            self.assertEqual(
                mesh.num_nodes, 4,
                'incorrect node count')
            self.assertEqual(
                mesh.num_node_strings, 0,
                'incorrect node string count')
            self.assertEqual(
                mesh.materials_per_element, 1,
                'incorrect material count')
            self.assertEqual(
                mesh.node(1),
                py2dm.Node(1, 1000.0, 2000.0, 20.0),
                'bad node')
            self.assertEqual(
                mesh.element(2),
                py2dm.Element2L(2, 2, 3, materials=(1,)),
                'bad element')

    def test_quad_georefed(self) -> None:
        path = self.data('M01_5m_002.2dm')
        with self.assertWarns(py2dm.errors.CustomFormatIgnored):
            with py2dm.Reader(path, materials=1) as mesh:
                self.assertEqual(
                    mesh.num_elements, 20486,
                    'incorrect element count')
                self.assertEqual(
                    mesh.num_nodes, 20893,
                    'incorrect node count')
                self.assertEqual(
                    mesh.num_node_strings, 0,
                    'incorrect node string count')
                self.assertEqual(
                    mesh.materials_per_element, 1,
                    'incorrect material count')
                self.assertEqual(
                    mesh.node(11111),
                    py2dm.Node(11111, 293161.35, 6178031.562, 42.631),
                    'bad node')
                self.assertEqual(
                    mesh.element(17710),
                    py2dm.Element4Q(
                        17710, 18051, 18050, 17947, 17948, materials=(1,)),
                    'bad element')

    def test_numbering_gaps(self) -> None:
        path = self.data('mesh_with_numbering_gaps.2dm')
        with self.assertRaises(py2dm.errors.FormatError):
            with py2dm.Reader(path, materials=1):
                pass

    def test_multi_material(self) -> None:
        path = self.data('multi_material.2dm')
        with py2dm.Reader(path) as mesh:
            self.assertEqual(
                mesh.num_elements, 12,
                'incorrect element count')
            self.assertEqual(
                mesh.num_nodes, 11,
                'incorrect node count')
            self.assertEqual(
                mesh.num_node_strings, 0,
                'incorrect node string count')
            self.assertEqual(
                mesh.materials_per_element, 3,
                'incorrect material count')
            self.assertEqual(
                mesh.node(5),
                py2dm.Node(5, -10.0, 0.0, 10.0),
                'bad node')
            self.assertEqual(
                mesh.element(10),
                py2dm.Element3T(10, 5, 9, 10, materials=(0, 8.333, 1)),
                'bad element')

    def test_not_mesh(self) -> None:
        path = self.data('not_a_mesh_file.2dm')
        with self.assertRaises(py2dm.errors.ReadError):
            with py2dm.Reader(path):
                pass

    def test_quad_and_line(self) -> None:
        path = self.data('quad_and_line.2dm')
        with py2dm.Reader(path, materials=1) as mesh:
            self.assertEqual(
                mesh.num_elements, 2,
                'incorrect element count')
            self.assertEqual(
                mesh.num_nodes, 5,
                'incorrect node count')
            self.assertEqual(
                mesh.num_node_strings, 0,
                'incorrect node string count')
            self.assertEqual(
                mesh.materials_per_element, 1,
                'incorrect material count')
            self.assertEqual(
                mesh.node(3),
                py2dm.Node(3, 3000.0, 2000.0, 40.0),
                'bad node')
            self.assertEqual(
                mesh.element(1),
                py2dm.Element4Q(1, 1, 2, 4, 5, materials=(1,)),
                'bad element')

    def test_quad_and_triangle(self) -> None:
        path = self.data('quad_and_triangle.2dm')
        with py2dm.Reader(path, materials=1) as mesh:
            self.assertEqual(
                mesh.num_elements, 2,
                'incorrect element count')
            self.assertEqual(
                mesh.num_nodes, 5,
                'incorrect node count')
            self.assertEqual(
                mesh.num_node_strings, 0,
                'incorrect node string count')
            self.assertEqual(
                mesh.materials_per_element, 1,
                'incorrect material count')
            self.assertEqual(
                mesh.node(4),
                py2dm.Node(4, 2000.0, 3000.0, 50.0),
                'bad node')
            self.assertEqual(
                mesh.element(2),
                py2dm.Element3T(2, 2, 3, 4, materials=(1,)),
                'bad element')

    def test_regular_grid(self) -> None:
        path = self.data('regular_grid.2dm')
        with self.assertWarns(py2dm.errors.CustomFormatIgnored):
            with py2dm.Reader(path, materials=1) as mesh:
                self.assertEqual(
                    mesh.num_elements, 1875,
                    'incorrect element count')
                self.assertEqual(
                    mesh.num_nodes, 1976,
                    'incorrect node count')
                self.assertEqual(
                    mesh.num_node_strings, 0,
                    'incorrect node string count')
                self.assertEqual(
                    mesh.materials_per_element, 1,
                    'incorrect material count')
                self.assertEqual(
                    mesh.node(1280),
                    py2dm.Node(1280, 381575.785, 168732.985, 36.122),
                    'bad node')
                self.assertEqual(
                    mesh.element(1620),
                    py2dm.Element4Q(
                        1620, 1718, 1717, 1641, 1642, materials=(1,)),
                    'bad element')

    def test_triangle_e6t(self) -> None:
        path = self.data('triangleE6T.2dm')
        with self.assertRaises(py2dm.errors.FormatError):
            with py2dm.Reader(path):
                pass

    def test_unordered_ids(self) -> None:
        path = self.data('unordered_ids.2dm')
        with self.assertRaises(py2dm.errors.FormatError):
            with py2dm.Reader(path):
                pass

    def test_unsupported_elements(self) -> None:
        path = self.data('unsupported_elements.2dm')
        with py2dm.Reader(path, materials=1) as mesh:
            self.assertEqual(
                mesh.num_elements, 1,
                'incorrect element count')
            self.assertEqual(
                mesh.num_nodes, 8,
                'incorrect node count')
            self.assertEqual(
                mesh.num_node_strings, 0,
                'incorrect node string count')
            self.assertEqual(
                mesh.materials_per_element, 1,
                'incorrect material count')
            self.assertEqual(
                mesh.node(5),
                py2dm.Node(5, 2000.0, 1000.0, 20.0),
                'bad node')
            self.assertEqual(
                mesh.element(1),
                py2dm.Element8Q(
                    1, 1, 2, 3, 4, 5, 6, 7, 8, materials=(1,)),
                'bad element')


class TestReadExternal(unittest.TestCase):
    """Additional real-world files for testing."""

    _DATA_DIR = 'tests/data/external'

    @classmethod
    def data(cls, filename: str, *args: str) -> str:
        """Return an absolute path to a synthetic test file."""
        return os.path.abspath(
            os.path.join(cls._DATA_DIR, filename, *args))

    def test_tm_forum_1(self) -> None:
        path = self.data('tm_forum', 'HYDRO_AS-2D.2dm')
        # NOTE: This mesh has holes in its element IDs and cannot be read by
        # Py2DM. Once the converter/conformer has been added, it should be
        # enabled here.
        with self.assertRaises(py2dm.errors.FormatError):
            with py2dm.Reader(path):
                pass

    def test_tm_forum_2(self) -> None:
        path = self.data('tm_forum', 'original_mesh.2dm')
        with py2dm.Reader(path, materials=1) as mesh:
            self.assertEqual(
                mesh.name, 'Mesh',
                'incorrect mesh name')
            self.assertTupleEqual(
                mesh.extent,
                (502382.6, 593280.0, 8522685.58, 8609367.2),
                'incorrect mesh extent')
            self.assertEqual(
                mesh.num_elements, 31580,
                'incorrect element count')
            self.assertEqual(
                mesh.num_nodes, 17151,
                'incorrect node count')
            self.assertEqual(
                mesh.num_node_strings, 0,
                'incorrect node string count')
            self.assertEqual(
                mesh.materials_per_element, 1,
                'incorrect material count')
            self.assertEqual(
                mesh.node(1337),
                py2dm.Node(1337, 552522.763, 8561666.81, -1.0),
                'bad node')
            self.assertEqual(
                mesh.element(10000),
                py2dm.Element3T(10000, 5539, 5359, 5360, materials=(4,)),
                'bad element')
