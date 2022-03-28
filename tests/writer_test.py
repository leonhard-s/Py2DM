"""Unit tests for the writer class."""

import io
import os
import shutil
import tempfile
import unittest
from typing import Any, Tuple

import py2dm  # pylint: disable=import-error


# pylint: disable=missing-function-docstring

class TestWriter(unittest.TestCase):
    """Unit tests for the entire writer class API."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.temp: str = '.'

    def setUp(self) -> None:
        self.temp = tempfile.mkdtemp()

    def tearDown(self) -> None:
        shutil.rmtree(self.temp)

    def get_file(self, filename: str = 'mesh.2dm') -> str:
        """A utility to quickly return the absolute path to a file."""
        return os.path.abspath(os.path.join(self.temp, filename))

    def get_memory_writer(self) -> Tuple[py2dm.Writer, io.StringIO]:
        """Return a writer class as well as its internal IO buffer.

        :return: A monkey-patched writer class using in-memory files.
        :rtype: :obj:`typing.Tuple` [
            :class:`py2dm.Writer`, :obj:`typing.IO` [:class:`str`]]
        """
        writer = py2dm.Writer(self.get_file())
        buffer = io.StringIO()
        # pylint: disable=protected-access
        writer._file = buffer  # type: ignore
        # pylint: disable=protected-access
        writer._closed = False  # type: ignore
        return writer, buffer

    def test___init__(self) -> None:
        writer = py2dm.Writer(self.get_file())
        self.assertEqual(
            writer.name, 'Unnamed mesh',
            'unexpected default mesh name')
        self.assertTrue(
            writer.closed,
            'writer not closed')
        with self.assertRaises(py2dm.errors.FileIsClosedError):
            _ = writer.node(py2dm.Node(1, 1.0, 2.0, 3.0))

    def test_context_manager(self) -> None:
        writer = py2dm.Writer(self.get_file())
        self.assertTrue(
            writer.closed,
            'writer not closed upon instantiation')
        with writer as mesh:
            self.assertFalse(
                writer.closed,
                'writer not opened with context manager')
            self.assertIs(
                writer, mesh,
                'writer __enter__ does not return self')
        self.assertTrue(
            writer.closed,
            'writer not closed after leaving context manager')

    def test___str__(self) -> None:
        writer = py2dm.Writer(self.get_file('example.2dm'))
        self.assertEqual(
            str(writer), 'Py2DM Writer (closed)',
            'unexpected string representation')
        writer.open()
        self.assertEqual(
            str(writer),
            ('Py2DM Writer\n'
             '\t(example.2dm)\n'
             '\t0 nodes\n'
             '\t0 elements\n'
             '\t0 node strings'),
            'unexpected string representation')
        writer.node(py2dm.Node(1, 2.0, 3.0, 4.0))
        writer.node(py2dm.Node(2, 3.0, 4.0, 5.0))
        writer.node(py2dm.Node(3, 4.0, 5.0, 6.0))
        writer.element(py2dm.Element3T(1, 1, 2, 3))
        writer.element(py2dm.Element2L(2, 3, 2))
        writer.node_string(py2dm.NodeString(1, 3))
        self.assertEqual(
            str(writer),
            ('Py2DM Writer\n'
             '\t(example.2dm)\n'
             '\t3 nodes\n'
             '\t2 elements\n'
             '\t1 node strings'),
            'unexpected string representation')
        writer.close()
        self.assertEqual(
            str(writer), 'Py2DM Writer (closed)',
            'unexpected string representation')

    def test_materials_per_element(self) -> None:
        with self.subTest('fixed material count'):
            with py2dm.Writer(self.get_file(), materials=2) as mesh:
                self.assertEqual(
                    mesh.materials_per_element, 2,
                    'predefined material count not set')
                with self.assertRaises(ValueError):
                    _ = mesh.element('E3T', -1, 2, 3, 4, materials=(2,))
                element = py2dm.Element3T(-1, 2, 3, 4, materials=(2, 3, 4))
                with self.assertWarns(py2dm.errors.Py2DMWarning):
                    mesh.element(element)
                # pylint: disable=protected-access
                cache = mesh._cache[py2dm.Element]  # type: ignore
                self.assertEqual(
                    cache[-1],
                    py2dm.Element3T(1, 2, 3, 4, materials=(2, 3)),
                    'bad cached element')
        with self.subTest('autodetect material count'):
            with py2dm.Writer(self.get_file()) as mesh:
                self.assertEqual(
                    mesh.materials_per_element, -1,
                    'bad default material count')
                mesh.element('E2L', 1, 2, 3, materials=(1, 2))
                self.assertEqual(
                    mesh.materials_per_element, 2,
                    'material count not updated')
                with self.assertRaises(ValueError):
                    _ = mesh.element('E2L', -1, 2, 3, materials=(2, ))
        with self.subTest('closed'):
            writer = py2dm.Writer(self.get_file())
            with self.assertRaises(py2dm.errors.FileIsClosedError):
                _ = writer.materials_per_element

    def test_num_elements(self) -> None:
        with py2dm.Writer(self.get_file()) as mesh:
            self.assertEqual(
                mesh.num_elements, 0,
                'bad element count')
            mesh.element(py2dm.Element2L(1, 2, 3))
            mesh.element(py2dm.Element2L(2, 3, 4))
            self.assertEqual(
                mesh.num_elements, 2,
                'bad element count')
        with self.subTest('closed'):
            writer = py2dm.Writer(self.get_file())
            with self.assertRaises(py2dm.errors.FileIsClosedError):
                _ = writer.num_elements
        with self.subTest('post flush'):
            with py2dm.Writer(self.get_file()) as mesh:
                mesh.element(py2dm.Element2L(1, 2, 3))
                self.assertEqual(
                    mesh.num_elements, 1,
                    'bad element count')
                mesh.flush_elements()
                self.assertEqual(
                    mesh.num_elements, 1,
                    'element count reset upon flush')

    def test_num_nodes(self) -> None:
        with py2dm.Writer(self.get_file()) as mesh:
            self.assertEqual(
                mesh.num_nodes, 0,
                'bad node count')
            mesh.node(py2dm.Node(1, 2.0, 3.0, 4.0))
            mesh.node(py2dm.Node(2, 3.0, 4.0, 5.0))
            self.assertEqual(
                mesh.num_nodes, 2,
                'bad node count')
        with self.subTest('closed'):
            writer = py2dm.Writer(self.get_file())
            with self.assertRaises(py2dm.errors.FileIsClosedError):
                _ = writer.num_nodes
        with self.subTest('post flush'):
            with py2dm.Writer(self.get_file()) as mesh:
                mesh.node(py2dm.Node(1, 2.0, 3.0, 4.0))
                self.assertEqual(
                    mesh.num_nodes, 1,
                    'bad node count')
                mesh.flush_nodes()
                self.assertEqual(
                    mesh.num_nodes, 1,
                    'node count reset upon flush')

    def test_num_node_strings(self) -> None:
        with py2dm.Writer(self.get_file()) as mesh:
            self.assertEqual(
                mesh.num_node_strings, 0,
                'bad node string count')
            mesh.node_string(py2dm.NodeString(1, 2, 3))
            mesh.node_string(py2dm.NodeString(2, 3, 4))
            self.assertEqual(
                mesh.num_node_strings, 2,
                'bad node string count')
        with self.subTest('closed'):
            writer = py2dm.Writer(self.get_file())
            with self.assertRaises(py2dm.errors.FileIsClosedError):
                _ = writer.num_node_strings
        with self.subTest('post flush'):
            with py2dm.Writer(self.get_file()) as mesh:
                mesh.node_string(py2dm.NodeString(1, 2, 3))
                self.assertEqual(
                    mesh.num_node_strings, 1,
                    'bad node string count')
                mesh.flush_node_strings()
                self.assertEqual(
                    mesh.num_node_strings, 1,
                    'node string count reset upon flush')

    def test_open_close(self) -> None:
        writer = py2dm.Writer(self.get_file())
        with self.assertRaises(py2dm.errors.FileIsClosedError):
            _ = writer.element(py2dm.Element2L(1, 2, 3))
        with self.assertRaises(py2dm.errors.FileIsClosedError):
            _ = writer.num_nodes
        writer.open()
        self.assertFalse(
            writer.closed,
            'reader closed after open() call')
        _ = writer.element(  # Test for erroneous exception
            py2dm.Element2L(1, 2, 3))
        writer.close()
        self.assertTrue(
            writer.closed,
            'reader not closed after close() call')
        with self.assertRaises(py2dm.errors.FileIsClosedError):
            _ = writer.element(py2dm.Element2L(1, 2, 3))

    def test_element(self) -> None:
        with self.subTest('pass element'):
            with py2dm.Writer(self.get_file()) as mesh:
                element = py2dm.Element3T(2, 3, 5, 1)
                self.assertEqual(
                    mesh.element(element), 2,
                    'bad element ID')
                with self.assertRaises(TypeError):
                    _ = mesh.element(element, 3)  # type: ignore
                with self.assertRaises(TypeError):
                    _ = mesh.element(element, materials=())  # type: ignore
        with self.subTest('pass class'):
            with py2dm.Writer(self.get_file()) as mesh:
                self.assertEqual(
                    mesh.element(py2dm.Element3T, 2, 3, 4, 5), 2,
                    'bad element ID')
                with self.assertRaises(TypeError):
                    _ = mesh.element(element, 3)  # type: ignore
                with self.assertRaises(TypeError):
                    _ = mesh.element(element, materials=())  # type: ignore
        with self.subTest('pass string'):
            with py2dm.Writer(self.get_file()) as mesh:
                self.assertEqual(
                    mesh.element('E3T', 2, 3, 4, 5), 2,
                    'bad element ID')
                with self.assertRaises(TypeError):
                    _ = mesh.element(element, 3)  # type: ignore
                with self.assertRaises(TypeError):
                    _ = mesh.element(element, materials=())  # type: ignore
        with self.subTest('auto ID'):
            with py2dm.Writer(self.get_file()) as mesh:
                self.assertEqual(
                    mesh.element('E2L', -1, 2, 3), 1,
                    'bad initial ID')
                self.assertEqual(
                    mesh.element('E2L', -1, 3, 4), 2,
                    'bad incremented ID')
            with py2dm.Writer(self.get_file(), zero_index=True) as mesh:
                self.assertEqual(
                    mesh.element('E2L', -1, 2, 3), 0,
                    'bad initial ID')
                self.assertEqual(
                    mesh.element('E2L', -1, 3, 4), 1,
                    'bad incremented ID')
        with self.subTest('too few materials'):
            with py2dm.Writer(self.get_file(), materials=2) as mesh:
                with self.assertRaises(ValueError):
                    _ = mesh.element('E2L', -1, 2, 3)
                with self.assertRaises(ValueError):
                    _ = mesh.element('E2L', -1, 2, 3, materials=(1,))
                _ = mesh.element('E2L', -1, 2, 3, materials=(1, 2))
        with self.subTest('too many materials'):
            with py2dm.Writer(self.get_file(), materials=2) as mesh:
                element = py2dm.Element3T(2, 3, 5, 1, materials=(1, 2, 3))
                with self.assertWarns(py2dm.errors.Py2DMWarning):
                    mesh.element(element)
                # pylint: disable=protected-access
                cache = mesh._cache[py2dm.Element]  # type: ignore
                self.assertEqual(
                    cache[-1],
                    py2dm.Element3T(2, 3, 5, 1, materials=(1, 2)),
                    'bad cached element')
        with self.subTest('disallowed float matids'):
            with py2dm.Writer(self.get_file(), materials=1) as mesh:
                _ = mesh.element('E2L', -1, 2, 3, materials=(1.0,))
            with py2dm.Writer(self.get_file(), materials=1,
                              allow_float_matid=False) as mesh:
                with self.assertRaises(ValueError):
                    _ = mesh.element('E3L', -1, 2, 3, 4, materials=(1.0,))
        with self.subTest('closed'):
            writer = py2dm.Writer(self.get_file())
            with self.assertRaises(py2dm.errors.FileIsClosedError):
                _ = writer.element(py2dm.Element2L, 1, 2, 3)
        with self.subTest('bad flush order'):
            with py2dm.Writer(self.get_file()) as mesh:
                mesh.element(py2dm.Element2L(1, 2, 3))
                mesh.flush_elements()
                mesh.node(py2dm.Node(1, 2.0, 3.0, 4.0))
                mesh.flush_nodes()
                with self.assertRaises(py2dm.errors.WriteError):
                    mesh.element(py2dm.Element2L(12, 3, 4))

    def test_node(self) -> None:
        with self.subTest('pass node'):
            with py2dm.Writer(self.get_file()) as mesh:
                node = py2dm.Node(2, 3.0, 4.0, 5.0)
                self.assertEqual(
                    mesh.node(node), 2,
                    'bad node ID')
                with self.assertRaises(TypeError):
                    _ = mesh.node(node, 1.0)  # type: ignore
                with self.assertRaises(TypeError):
                    _ = mesh.node(node, var=True)  # type: ignore
        with self.subTest('pass args'):
            with py2dm.Writer(self.get_file()) as mesh:
                self.assertEqual(
                    mesh.node(2, 3, 4, 5), 2,
                    'bad node ID')
                with self.assertRaises(TypeError):
                    _ = mesh.node(node, 1.0)  # type: ignore
                with self.assertRaises(TypeError):
                    _ = mesh.node(node, var=True)  # type: ignore
        with self.subTest('auto ID'):
            with py2dm.Writer(self.get_file()) as mesh:
                self.assertEqual(
                    mesh.node(-1, 2.0, 3.0, 4.0), 1,
                    'bad initial ID')
                self.assertEqual(
                    mesh.node(-1, 3.0, 4.0, 5.0), 2,
                    'bad incremented ID')
            with py2dm.Writer(self.get_file(), zero_index=True) as mesh:
                self.assertEqual(
                    mesh.node(-1, 2.0, 3.0, 4.0), 0,
                    'bad initial ID')
                self.assertEqual(
                    mesh.node(-1, 3.0, 4.0, 5.0), 1,
                    'bad incremented ID')
        with self.subTest('closed'):
            writer = py2dm.Writer(self.get_file())
            with self.assertRaises(py2dm.errors.FileIsClosedError):
                _ = writer.node(1, 2.0, 3.0, 4.0)
        with self.subTest('bad flush order'):
            with py2dm.Writer(self.get_file()) as mesh:
                mesh.node(py2dm.Node(1, 2.0, 3.0, 4.0))
                mesh.flush_nodes()
                mesh.element(py2dm.Element2L(1, 2, 3))
                mesh.flush_elements()
                with self.assertRaises(py2dm.errors.WriteError):
                    mesh.node(py2dm.Node(2, 3.0, 4.0, 5.0))

    def test_node_string(self) -> None:
        with self.subTest('pass node string'):
            with py2dm.Writer(self.get_file()) as mesh:
                node_string = py2dm.NodeString(1, 2, 3)
                self.assertEqual(
                    mesh.node_string(node_string), 1,
                    'bad node string count')
                with self.assertRaises(TypeError):
                    _ = mesh.node_string(node_string, 1)  # type: ignore
                with self.assertRaises(TypeError):
                    _ = mesh.node_string(
                        node_string, name='bogus')  # type: ignore
        with self.subTest('pass args'):
            with py2dm.Writer(self.get_file()) as mesh:
                self.assertEqual(
                    mesh.node_string(1, 2, 3), 1,
                    'bad node string count')
                with self.assertRaises(TypeError):
                    _ = mesh.node_string(node_string, 1)  # type: ignore
                with self.assertRaises(TypeError):
                    _ = mesh.node_string(
                        node_string, name='bogus')  # type: ignore
        with self.subTest('closed'):
            writer = py2dm.Writer(self.get_file())
            with self.assertRaises(py2dm.errors.FileIsClosedError):
                _ = writer.node_string(1, 2)
        with self.subTest('bad flush order'):
            with py2dm.Writer(self.get_file()) as mesh:
                mesh.node_string(1, 2, 3)
                mesh.flush_node_strings()
                mesh.node(2, 3.0, 4.0, 5.0)
                mesh.flush_nodes()
                with self.assertRaises(py2dm.errors.WriteError):
                    mesh.node_string(2, 5, 6)

    def test_flush_elements(self) -> None:
        writer, buffer = self.get_memory_writer()
        writer.flush_elements()
        self.assertEqual(
            buffer.getvalue(),
            ('MESH2D\n'
             'NUM_MATERIALS_PER_ELEM 0\n'),
            'unexpected file buffer')
        writer.element('E2L', 1, 2, 3)
        self.assertEqual(
            buffer.getvalue(),
            ('MESH2D\n'
             'NUM_MATERIALS_PER_ELEM 0\n'),
            'buffer updated without flush call')
        writer.flush_elements()
        self.assertEqual(
            buffer.getvalue(),
            ('MESH2D\n'
             'NUM_MATERIALS_PER_ELEM 0\n'
             'E2L        1        2        3\n'),
            'unexpected file buffer')

    def test_flush_nodes(self) -> None:
        writer, buffer = self.get_memory_writer()
        writer.flush_nodes()
        self.assertEqual(
            buffer.getvalue(),
            ('MESH2D\n'
             'NUM_MATERIALS_PER_ELEM 0\n'),
            'unexpected file buffer')
        writer.node(1, 2.0, 3.0, 4.0)
        self.assertEqual(
            buffer.getvalue(),
            ('MESH2D\n'
             'NUM_MATERIALS_PER_ELEM 0\n'),
            'buffer updated without flush call')
        writer.flush_nodes()
        self.assertEqual(
            buffer.getvalue(),
            ('MESH2D\n'
             'NUM_MATERIALS_PER_ELEM 0\n'
             'ND        1  2.000000e+00  3.000000e+00  4.000000e+00\n'),
            'unexpected file buffer')

    def test_flush_node_strings(self) -> None:
        writer, buffer = self.get_memory_writer()
        writer.flush_node_strings()
        self.assertEqual(
            buffer.getvalue(),
            ('MESH2D\n'
             'NUM_MATERIALS_PER_ELEM 0\n'),
            'unexpected file buffer')
        writer.node_string(1, 2, 3, 4)
        self.assertEqual(
            buffer.getvalue(),
            ('MESH2D\n'
             'NUM_MATERIALS_PER_ELEM 0\n'),
            'buffer updated without flush call')
        writer.flush_node_strings()
        self.assertEqual(
            buffer.getvalue(),
            ('MESH2D\n'
             'NUM_MATERIALS_PER_ELEM 0\n'
             'NS 1 2 3 -4\n'),
            'unexpected file buffer')

    def test_write_header(self) -> None:
        with self.subTest('default'):
            writer, buffer = self.get_memory_writer()
            self.assertEqual(
                buffer.getvalue(), '',
                'buffer not initially empty')
            writer.write_header()
            self.assertEqual(
                buffer.getvalue(),
                ('MESH2D\n'
                 'NUM_MATERIALS_PER_ELEM 0\n'),
                'unexpected file buffer')
        with self.subTest('signature'):
            writer, buffer = self.get_memory_writer()
            writer.write_header('This is only a test')
            self.assertEqual(
                buffer.getvalue(),
                ('MESH2D # This is only a test\n'
                 'NUM_MATERIALS_PER_ELEM 0\n'),
                'unexpected file buffer')
        with self.subTest('multiline signature'):
            writer, buffer = self.get_memory_writer()
            writer.write_header('This signature\nspans multiple\nlines')
            self.assertEqual(
                buffer.getvalue(),
                ('MESH2D # This signature\n'
                 '# spans multiple\n'
                 '# lines\n'
                 'NUM_MATERIALS_PER_ELEM 0\n'),
                'unexpected file buffer')


class TestFileCopy(unittest.TestCase):
    """Test the writer class by comparing copied files.

    This takes an external file, reads it, and writes it back to disk.
    The original and the copy are then compared via the reader to
    ensure the process did not lose or falsify any data.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.temp: str = '.'

    def setUp(self) -> None:
        self.temp = tempfile.mkdtemp()

    def tearDown(self) -> None:
        shutil.rmtree(self.temp)

    def copy_file(self, filepath: str) -> str:
        """Create a copy of the given file and return its path.

        :param filepath: The file to copy.
        :type filepath: :class:`str`
        :return: A re-written version of the input file to test.
        :rtype: :class:`str`
        """
        out_path = os.path.join(os.path.dirname(self.temp), 'copy.2dm')
        with py2dm.Reader(filepath) as in_mesh:
            num_materials = in_mesh.materials_per_element
            with py2dm.Writer(out_path, materials=num_materials) as out_mesh:
                for node in in_mesh.nodes:
                    out_mesh.node(node)
                for element in in_mesh.elements:
                    out_mesh.element(element)
                for node_string in in_mesh.node_strings:
                    out_mesh.node_string(node_string)
        return out_path

    def compare_meshes(self, mesh_a: py2dm.Reader,
                       mesh_b: py2dm.Reader) -> None:
        """Compare two meshes entity by entity.

        :param mesh_a: The mesh to compare against.
        :type mesh_a: :class:`py2dm.Reader`
        :param mesh_b: The mesh to compare.
        :type mesh_b: :class:`py2dm.Reader`
        """
        self.assertEqual(
            mesh_a.materials_per_element,
            mesh_b.materials_per_element,
            'differing material count')
        for node_a, node_b in zip(mesh_a.nodes, mesh_b.nodes):
            self.assertEqual(
                node_a, node_b,
                'differing node in copy')
        for element_a, element_b in zip(
                mesh_a.elements, mesh_b.elements):
            self.assertEqual(
                element_a, element_b,
                'differing element in copy')
        for node_string_a, node_string_b in zip(
                mesh_a.node_strings, mesh_b.node_strings):
            self.assertEqual(
                node_string_a, node_string_b,
                'differing node strings in copy')

    def test_basic_node_string(self) -> None:
        source = os.path.join('tests', 'data', 'basic-node-strings.2dm')
        copy = self.copy_file(source)
        with py2dm.Reader(source) as mesh_a:
            with py2dm.Reader(copy) as mesh_b:
                self.compare_meshes(mesh_a, mesh_b)
