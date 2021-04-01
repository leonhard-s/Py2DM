"""Unit tests for all classes representing 2DM entities."""

import unittest

import py2dm  # pylint: disable=import-error


class TestNode(unittest.TestCase):
    """Tests for the py2dm.Node class."""

    def test_card(self) -> None:
        self.assertEqual(
            py2dm.Node.card, 'ND',
            'bad 2DM card')

    def test___init__(self) -> None:
        node = py2dm.Node(1, -1.0, 2.0, -3.0)
        self.assertEqual(
            node.id, 1,
            'bad ID')
        self.assertEqual(
            node.x, -1.0,
            'bad X coordinate')
        self.assertEqual(
            node.y, 2.0,
            'bad Y coordinate')
        self.assertEqual(
            node.z, -3.0,
            'bad Z coordinate')

    def test___eq__(self) -> None:
        node_1 = py2dm.Node(1, -1.0, 1.0, 0.5)
        node_2 = py2dm.Node(2, -1.0, 1.0, 0.5)
        node_3 = py2dm.Node(1,  1.0, 0.0, 0.0)
        node_4 = py2dm.Node(1, -1.0, 1.0, 0.5)
        self.assertNotEqual(
            node_1, node_2,
            'different ID')
        self.assertNotEqual(
            node_1, node_3,
            'different position')
        self.assertEqual(
            node_1, node_4,
            'separate instance but same value')
        self.assertNotEqual(
            node_1, None)

    def test___repr__(self) -> None:
        self.assertEqual(
            repr(py2dm.Node(12, 3.0, 2.0, -2.0)),
            '<Node #12: (3.0, 2.0, -2.0)>',
            'unexpected string representation')

    def test_pos(self) -> None:
        node = py2dm.Node(1, 2.0, 3.0, 4.0)
        self.assertTupleEqual(
            node.pos,
            (node.x, node.y, node.z),
            'non-matching coordinates')

    def test_from_line(self) -> None:
        with self.subTest('known good'):
            line = 'ND 1 12 34 56'
            node = py2dm.Node.from_line(line)
            self.assertEqual(
                node.id, 1,
                'incorrect node ID')
            self.assertTupleEqual(
                node.pos, (12.0, 34.0, 56.0),
                'incorrect coordinates')
        with self.subTest('bad card'):
            line = 'NE 1 1.0 2.0 3.0'
            with self.assertRaises(py2dm.errors.CardError):
                _ = py2dm.Node.from_line(line)
        with self.subTest('too few coordinates'):
            line = 'ND 2 21 43'
            with self.assertRaises(py2dm.errors.FormatError):
                _ = py2dm.Node.from_line(line)
        with self.subTest('negative node ID'):
            line = 'ND -3 21 43'
            with self.assertRaises(py2dm.errors.FormatError):
                _ = py2dm.Node.from_line(line)
        with self.subTest('excess fields'):
            line = 'ND 5 1.0 2.0 3.0 2 0. 0. 0.'
            with self.assertWarns(py2dm.errors.CustomFormatIgnored):
                node = py2dm.Node.from_line(line)
                self.assertEqual(
                    node.id, 5,
                    'incorrect node ID')
                self.assertTupleEqual(
                    node.pos, (1.0, 2.0, 3.0),
                    'incorrect coordinates')

    def test_to_line(self) -> None:
        with self.subTest('default'):
            node = py2dm.Node(1, 12.0, 34.0, 56.0)
            self.assertListEqual(
                node.to_line(),
                ['ND', '1', ' 1.200000e+01', ' 3.400000e+01', ' 5.600000e+01'],
                'unexpected line chunks')
        with self.subTest('fixed_decimals'):
            node = py2dm.Node(10, -12, 20.0, 2.5)
            self.assertListEqual(
                node.to_line(decimals=2),
                ['ND', '10', '-1.20e+01', ' 2.00e+01', ' 2.50e+00'],
                'unexpected line chunks')
        with self.subTest('compact'):
            node = py2dm.Node(5, 1.23, 2.0, 4.5)
            self.assertListEqual(
                node.to_line(compact=True),
                ['ND', '5', '1.23', '2.0', '4.5'],
                'unexpected line chunks')


class TestElement2L(unittest.TestCase):
    """Tests for the py2dm.Element2L class."""

    def test_card(self) -> None:
        self.assertEqual(
            py2dm.Element2L.card, 'E2L',
            'bad 2DM card')

    def test_num_nodes(self) -> None:
        self.assertEqual(
            py2dm.Element2L.num_nodes, 2,
            'bad number of nodes')

    def test___init__(self) -> None:
        with self.subTest('known good'):
            element = py2dm.Element2L(1, 2, 3, materials=(4.0, 5))
            self.assertEqual(
                element.id, 1,
                'bad ID')
            self.assertTupleEqual(
                element.nodes, (2, 3),
                'bad nodes')
            self.assertTupleEqual(
                element.materials, (4.0, 5),
                'bad materials')
        with self.assertRaises(py2dm.errors.CardError):
            _ = py2dm.Element3T(1, 2, 3, materials=(3.0, 4))

    def test___eq__(self) -> None:
        element_1 = py2dm.Element2L(1, 2, 3)
        element_2 = py2dm.Element2L(2, 2, 3)
        element_3 = py2dm.Element2L(1, 4, 5)
        element_4 = py2dm.Element2L(1, 2, 3)
        self.assertNotEqual(
            element_1, element_2,
            'different ID')
        self.assertNotEqual(
            element_1, element_3,
            'different nodes')
        self.assertEqual(
            element_1, element_4,
            'separate instance but same value')
        self.assertNotEqual(
            element_1, None)

    def test___repr__(self) -> None:
        with self.subTest('no materials'):
            self.assertEqual(
                repr(py2dm.Element2L(12, 3, 4)),
                '<Element #12 [E2L]: Node IDs (3, 4)>',
                'unexpected string representation')
        with self.subTest('w/ materials'):
            self.assertEqual(
                repr(py2dm.Element2L(12, 3, 4, materials=(1.0, 2))),
                '<Element #12 [E2L]: Node IDs (3, 4) Materials (1.0, 2)>',
                'unexpected string representation')

    def test_num_materials(self) -> None:
        element = py2dm.Element2L(12, 3, 4, materials=(1.0, 2))
        self.assertEqual(
            element.num_materials, 2,
            'bad number of materials')

    def test_from_line(self) -> None:
        with self.subTest('known good'):
            line = 'E2L 1 2 3'
            element = py2dm.Element2L.from_line(line)
            self.assertEqual(
                element.id, 1,
                'incorrect element ID')
            self.assertTupleEqual(
                element.nodes, (2, 3),
                'incorrect nodes')
            self.assertEqual(
                element.num_materials, 0,
                'incorrect material count')
            self.assertTupleEqual(
                element.materials, (),
                'incorrect materials')
        with self.subTest('known good w/ materials'):
            line = 'E2L 2 3 4 5.0 -6'
            element = py2dm.Element2L.from_line(line)
            self.assertEqual(
                element.id, 2,
                'incorrect element ID')
            self.assertTupleEqual(
                element.nodes, (3, 4),
                'incorrect nodes')
            self.assertEqual(
                element.num_materials, 2,
                'incorrect material count')
            self.assertTupleEqual(
                element.materials, (5.0, -6),
                'incorrect materials')
        with self.subTest('bad card'):
            line = 'E3L 3 4 5'
            with self.assertRaises(py2dm.errors.CardError):
                _ = py2dm.Element2L.from_line(line)
        with self.subTest('negative element ID'):
            line = 'E2L -4 5 6'
            with self.assertRaises(py2dm.errors.FormatError):
                _ = py2dm.Element2L.from_line(line)
        with self.subTest('negative node ID'):
            line = 'E2L 5 -6 7'
            with self.assertRaises(py2dm.errors.FormatError):
                _ = py2dm.Element2L.from_line(line)
        with self.subTest('missing nodes'):
            line = 'E2L 4 5'
            with self.assertRaises(py2dm.errors.CardError):
                _ = py2dm.Element2L.from_line(line)
        with self.assertWarns(py2dm.errors.CustomFormatIgnored):
            line = 'E2L 1 2 3 4.0'
            _ = py2dm.Element2L.from_line(line, allow_float_matid=False)

    def test_to_line(self) -> None:
        with self.subTest('default'):
            element = py2dm.Element2L(1, 233, 3, materials=(1.0, -2, 5))
            self.assertListEqual(
                element.to_line(),
                ['E2L', '1', '233', '3', ' 1.000e+00', '-2', ' 5'],
                'unexpected line chunks')
        with self.subTest('fixed_decimals'):
            element = py2dm.Element2L(1, 2, 3, materials=(1.0, -2, 5))
            self.assertListEqual(
                element.to_line(decimals=2),
                ['E2L', '1', '2', '3', ' 1.00e+00', '-2', ' 5'],
                'unexpected line chunks')
        with self.subTest('compact'):
            element = py2dm.Element2L(1, 2, 3, materials=(1.0, -2, 5))
            self.assertListEqual(
                element.to_line(compact=True),
                ['E2L', '1', '2', '3', '1.0', '-2', '5'],
                'unexpected line chunks')
        with self.subTest('integer materials only'):
            element = py2dm.Element2L(1, 2, 3, materials=(1.0, -2))
            self.assertListEqual(
                element.to_line(allow_float_matid=False),
                ['E2L', '1', '2', '3', '-2'],
                'unexpected line chunks')


class TestElement3L(unittest.TestCase):
    """Tests for the py2dm.Element3L class."""

    def test_card(self) -> None:
        self.assertEqual(
            py2dm.Element3L.card, 'E3L',
            'bad 2DM card')

    def test_num_nodes(self) -> None:
        self.assertEqual(
            py2dm.Element3L.num_nodes, 3,
            'bad number of nodes')

    def test___init__(self) -> None:
        with self.subTest('known good'):
            element = py2dm.Element3L(1, 2, 3, 4, materials=(5.0, 6))
            self.assertEqual(
                element.id, 1,
                'bad ID')
            self.assertTupleEqual(
                element.nodes, (2, 3, 4),
                'bad nodes')
            self.assertTupleEqual(
                element.materials, (5.0, 6),
                'bad materials')
        with self.assertRaises(py2dm.errors.CardError):
            _ = py2dm.Element3L(1, 2, 3, materials=(4.0, 5))

    def test___eq__(self) -> None:
        element_1 = py2dm.Element3L(1, 2, 3, 4)
        element_2 = py2dm.Element3L(2, 2, 3, 4)
        element_3 = py2dm.Element3L(1, 4, 5, 6)
        element_4 = py2dm.Element3L(1, 2, 3, 4)
        self.assertNotEqual(
            element_1, element_2,
            'different ID')
        self.assertNotEqual(
            element_1, element_3,
            'different nodes')
        self.assertEqual(
            element_1, element_4,
            'separate instance but same value')
        self.assertNotEqual(
            element_1, None)

    def test___repr__(self) -> None:
        with self.subTest('no materials'):
            self.assertEqual(
                repr(py2dm.Element3L(12, 3, 4, 5)),
                '<Element #12 [E3L]: Node IDs (3, 4, 5)>',
                'unexpected string representation')
        with self.subTest('w/ materials'):
            self.assertEqual(
                repr(py2dm.Element3L(12, 3, 4, 5, materials=(1.0, 2))),
                '<Element #12 [E3L]: Node IDs (3, 4, 5) Materials (1.0, 2)>',
                'unexpected string representation')

    def test_num_materials(self) -> None:
        element = py2dm.Element3L(12, 3, 4, 5, materials=(1.0, 2))
        self.assertEqual(
            element.num_materials, 2,
            'bad number of materials')

    def test_from_line(self) -> None:
        with self.subTest('known good'):
            line = 'E3L 1 2 3 4'
            element = py2dm.Element3L.from_line(line)
            self.assertEqual(
                element.id, 1,
                'incorrect element ID')
            self.assertTupleEqual(
                element.nodes, (2, 3, 4),
                'incorrect nodes')
            self.assertEqual(
                element.num_materials, 0,
                'incorrect material count')
            self.assertTupleEqual(
                element.materials, (),
                'incorrect materials')
        with self.subTest('known good w/ materials'):
            line = 'E3L 2 3 4 5 6.0 -7'
            element = py2dm.Element3L.from_line(line)
            self.assertEqual(
                element.id, 2,
                'incorrect element ID')
            self.assertTupleEqual(
                element.nodes, (3, 4, 5),
                'incorrect nodes')
            self.assertEqual(
                element.num_materials, 2,
                'incorrect material count')
            self.assertTupleEqual(
                element.materials, (6.0, -7),
                'incorrect materials')
        with self.subTest('bad card'):
            line = 'E3T 3 4 5 6'
            with self.assertRaises(py2dm.errors.CardError):
                _ = py2dm.Element3L.from_line(line)
        with self.subTest('negative element ID'):
            line = 'E3L -4 5 6 7'
            with self.assertRaises(py2dm.errors.FormatError):
                _ = py2dm.Element3L.from_line(line)
        with self.subTest('negative node ID'):
            line = 'E3L 5 -6 7 8'
            with self.assertRaises(py2dm.errors.FormatError):
                _ = py2dm.Element3L.from_line(line)
        with self.subTest('missing nodes'):
            line = 'E3L 4 5 6'
            with self.assertRaises(py2dm.errors.CardError):
                _ = py2dm.Element3L.from_line(line)
        with self.assertWarns(py2dm.errors.CustomFormatIgnored):
            line = 'E3L 1 2 3 4 5.0'
            _ = py2dm.Element3L.from_line(line, allow_float_matid=False)

    def test_to_line(self) -> None:
        with self.subTest('default'):
            element = py2dm.Element3L(1, 233, 3, 4, materials=(1.0, -2, 5))
            self.assertListEqual(
                element.to_line(),
                ['E3L', '1', '233', '3', '4', ' 1.000e+00', '-2', ' 5'],
                'unexpected line chunks')
        with self.subTest('fixed_decimals'):
            element = py2dm.Element3L(1, 2, 3, 4, materials=(1.0, -2, 5))
            self.assertListEqual(
                element.to_line(decimals=2),
                ['E3L', '1', '2', '3', '4', ' 1.00e+00', '-2', ' 5'],
                'unexpected line chunks')
        with self.subTest('compact'):
            element = py2dm.Element3L(1, 2, 3, 4, materials=(1.0, -2, 5))
            self.assertListEqual(
                element.to_line(compact=True),
                ['E3L', '1', '2', '3', '4', '1.0', '-2', '5'],
                'unexpected line chunks')
        with self.subTest('integer materials only'):
            element = py2dm.Element3L(1, 2, 3, 4, materials=(1.0, -2))
            self.assertListEqual(
                element.to_line(allow_float_matid=False),
                ['E3L', '1', '2', '3', '4', '-2'],
                'unexpected line chunks')


class TestElement3T(unittest.TestCase):
    """Tests for the py2dm.Element3T class."""

    def test_card(self) -> None:
        self.assertEqual(
            py2dm.Element3T.card, 'E3T',
            'bad 2DM card')

    def test_num_nodes(self) -> None:
        self.assertEqual(
            py2dm.Element3T.num_nodes, 3,
            'bad number of nodes')

    def test___init__(self) -> None:
        with self.subTest('known good'):
            element = py2dm.Element3T(1, 2, 3, 4, materials=(5.0, 6))
            self.assertEqual(
                element.id, 1,
                'bad ID')
            self.assertTupleEqual(
                element.nodes, (2, 3, 4),
                'bad nodes')
            self.assertTupleEqual(
                element.materials, (5.0, 6),
                'bad materials')
        with self.assertRaises(py2dm.errors.CardError):
            _ = py2dm.Element3T(1, 2, 3, materials=(4.0, 5))

    def test___eq__(self) -> None:
        element_1 = py2dm.Element3T(1, 2, 3, 4)
        element_2 = py2dm.Element3T(2, 2, 3, 4)
        element_3 = py2dm.Element3T(1, 4, 5, 6)
        element_4 = py2dm.Element3T(1, 2, 3, 4)
        self.assertNotEqual(
            element_1, element_2,
            'different ID')
        self.assertNotEqual(
            element_1, element_3,
            'different nodes')
        self.assertEqual(
            element_1, element_4,
            'separate instance but same value')
        self.assertNotEqual(
            element_1, None)

    def test___repr__(self) -> None:
        with self.subTest('no materials'):
            self.assertEqual(
                repr(py2dm.Element3T(12, 3, 4, 5)),
                '<Element #12 [E3T]: Node IDs (3, 4, 5)>',
                'unexpected string representation')
        with self.subTest('w/ materials'):
            self.assertEqual(
                repr(py2dm.Element3T(12, 3, 4, 5, materials=(1.0, 2))),
                '<Element #12 [E3T]: Node IDs (3, 4, 5) Materials (1.0, 2)>',
                'unexpected string representation')

    def test_num_materials(self) -> None:
        element = py2dm.Element3T(12, 3, 4, 5, materials=(1.0, 2))
        self.assertEqual(
            element.num_materials, 2,
            'bad number of materials')

    def test_from_line(self) -> None:
        with self.subTest('known good'):
            line = 'E3T 1 2 3 4'
            element = py2dm.Element3T.from_line(line)
            self.assertEqual(
                element.id, 1,
                'incorrect element ID')
            self.assertTupleEqual(
                element.nodes, (2, 3, 4),
                'incorrect nodes')
            self.assertEqual(
                element.num_materials, 0,
                'incorrect material count')
            self.assertTupleEqual(
                element.materials, (),
                'incorrect materials')
        with self.subTest('known good w/ materials'):
            line = 'E3T 2 3 4 5 6.0 -7'
            element = py2dm.Element3T.from_line(line)
            self.assertEqual(
                element.id, 2,
                'incorrect element ID')
            self.assertTupleEqual(
                element.nodes, (3, 4, 5),
                'incorrect nodes')
            self.assertEqual(
                element.num_materials, 2,
                'incorrect material count')
            self.assertTupleEqual(
                element.materials, (6.0, -7),
                'incorrect materials')
        with self.subTest('bad card'):
            line = 'E3L 3 4 5 6'
            with self.assertRaises(py2dm.errors.CardError):
                _ = py2dm.Element3T.from_line(line)
        with self.subTest('negative element ID'):
            line = 'E3T -4 5 6 7'
            with self.assertRaises(py2dm.errors.FormatError):
                _ = py2dm.Element3T.from_line(line)
        with self.subTest('negative node ID'):
            line = 'E3T 5 -6 7 8'
            with self.assertRaises(py2dm.errors.FormatError):
                _ = py2dm.Element3T.from_line(line)
        with self.subTest('missing nodes'):
            line = 'E3T 4 5 6'
            with self.assertRaises(py2dm.errors.CardError):
                _ = py2dm.Element3T.from_line(line)
        with self.assertWarns(py2dm.errors.CustomFormatIgnored):
            line = 'E3T 1 2 3 4 5.0'
            _ = py2dm.Element3T.from_line(line, allow_float_matid=False)

    def test_to_line(self) -> None:
        with self.subTest('default'):
            element = py2dm.Element3T(1, 233, 3, 4, materials=(1.0, -2, 5))
            self.assertListEqual(
                element.to_line(),
                ['E3T', '1', '233', '3', '4', ' 1.000e+00', '-2', ' 5'],
                'unexpected line chunks')
        with self.subTest('fixed_decimals'):
            element = py2dm.Element3T(1, 2, 3, 4, materials=(1.0, -2, 5))
            self.assertListEqual(
                element.to_line(decimals=2),
                ['E3T', '1', '2', '3', '4', ' 1.00e+00', '-2', ' 5'],
                'unexpected line chunks')
        with self.subTest('compact'):
            element = py2dm.Element3T(1, 2, 3, 4, materials=(1.0, -2, 5))
            self.assertListEqual(
                element.to_line(compact=True),
                ['E3T', '1', '2', '3', '4', '1.0', '-2', '5'],
                'unexpected line chunks')
        with self.subTest('integer materials only'):
            element = py2dm.Element3T(1, 2, 3, 4, materials=(1.0, -2))
            self.assertListEqual(
                element.to_line(allow_float_matid=False),
                ['E3T', '1', '2', '3', '4', '-2'],
                'unexpected line chunks')


class TestElement4Q(unittest.TestCase):
    """Tests for the py2dm.Element4Q class."""

    def test_card(self) -> None:
        self.assertEqual(
            py2dm.Element4Q.card, 'E4Q',
            'bad 2DM card')

    def test_num_nodes(self) -> None:
        self.assertEqual(
            py2dm.Element4Q.num_nodes, 4,
            'bad number of nodes')

    def test___init__(self) -> None:
        with self.subTest('known good'):
            element = py2dm.Element4Q(1, 2, 3, 4, 5, materials=(6.0, 7))
            self.assertEqual(
                element.id, 1,
                'bad ID')
            self.assertTupleEqual(
                element.nodes, (2, 3, 4, 5),
                'bad nodes')
            self.assertTupleEqual(
                element.materials, (6.0, 7),
                'bad materials')
        with self.assertRaises(py2dm.errors.CardError):
            _ = py2dm.Element4Q(1, 2, 3, 4, materials=(5.0, 6))

    def test___eq__(self) -> None:
        element_1 = py2dm.Element4Q(1, 2, 3, 4, 5)
        element_2 = py2dm.Element4Q(2, 2, 3, 4, 5)
        element_3 = py2dm.Element4Q(1, 4, 5, 6, 7)
        element_4 = py2dm.Element4Q(1, 2, 3, 4, 5)
        self.assertNotEqual(
            element_1, element_2,
            'different ID')
        self.assertNotEqual(
            element_1, element_3,
            'different nodes')
        self.assertEqual(
            element_1, element_4,
            'separate instance but same value')

    def test___repr__(self) -> None:
        with self.subTest('no materials'):
            self.assertEqual(
                repr(py2dm.Element4Q(12, 3, 4, 5, 6)),
                '<Element #12 [E4Q]: Node IDs (3, 4, 5, 6)>',
                'unexpected string representation')
        with self.subTest('w/ materials'):
            self.assertEqual(
                repr(py2dm.Element4Q(12, 3, 4, 5, 6, materials=(1.0, 2))),
                ('<Element #12 [E4Q]: Node IDs (3, 4, 5, 6) '
                 'Materials (1.0, 2)>'),
                'unexpected string representation')

    def test_num_materials(self) -> None:
        element = py2dm.Element4Q(12, 3, 4, 5, 6, materials=(1.0, 2))
        self.assertEqual(
            element.num_materials, 2,
            'bad number of materials')

    def test_from_line(self) -> None:
        with self.subTest('known good'):
            line = 'E4Q 1 2 3 4 5'
            element = py2dm.Element4Q.from_line(line)
            self.assertEqual(
                element.id, 1,
                'incorrect element ID')
            self.assertTupleEqual(
                element.nodes, (2, 3, 4, 5),
                'incorrect nodes')
            self.assertEqual(
                element.num_materials, 0,
                'incorrect material count')
            self.assertTupleEqual(
                element.materials, (),
                'incorrect materials')
        with self.subTest('known good w/ materials'):
            line = 'E4Q 2 3 4 5 6 7.0 -8'
            element = py2dm.Element4Q.from_line(line)
            self.assertEqual(
                element.id, 2,
                'incorrect element ID')
            self.assertTupleEqual(
                element.nodes, (3, 4, 5, 6),
                'incorrect nodes')
            self.assertEqual(
                element.num_materials, 2,
                'incorrect material count')
            self.assertTupleEqual(
                element.materials, (7.0, -8),
                'incorrect materials')
        with self.subTest('bad card'):
            line = 'E2L 3 4 5 6 7'
            with self.assertRaises(py2dm.errors.CardError):
                _ = py2dm.Element4Q.from_line(line)
        with self.subTest('negative element ID'):
            line = 'E4Q -4 5 6 7 8'
            with self.assertRaises(py2dm.errors.FormatError):
                _ = py2dm.Element4Q.from_line(line)
        with self.subTest('negative node ID'):
            line = 'E4Q 5 -6 7 8 9'
            with self.assertRaises(py2dm.errors.FormatError):
                _ = py2dm.Element4Q.from_line(line)
        with self.subTest('missing nodes'):
            line = 'E4Q 4 5 6 7'
            with self.assertRaises(py2dm.errors.CardError):
                _ = py2dm.Element4Q.from_line(line)
        with self.assertWarns(py2dm.errors.CustomFormatIgnored):
            line = 'E4Q 1 2 3 4 5 6.0'
            _ = py2dm.Element4Q.from_line(line, allow_float_matid=False)

    def test_to_line(self) -> None:
        with self.subTest('default'):
            element = py2dm.Element4Q(1, 233, 3, 4, 5, materials=(1.0, -2, 5))
            self.assertListEqual(
                element.to_line(),
                ['E4Q', '1', '233', '3', '4', '5', ' 1.000e+00', '-2', ' 5'],
                'unexpected line chunks')
        with self.subTest('fixed_decimals'):
            element = py2dm.Element4Q(1, 2, 3, 4, 5, materials=(1.0, -2, 5))
            self.assertListEqual(
                element.to_line(decimals=2),
                ['E4Q', '1', '2', '3', '4', '5', ' 1.00e+00', '-2', ' 5'],
                'unexpected line chunks')
        with self.subTest('compact'):
            element = py2dm.Element4Q(1, 2, 3, 4, 5, materials=(1.0, -2, 5))
            self.assertListEqual(
                element.to_line(compact=True),
                ['E4Q', '1', '2', '3', '4', '5', '1.0', '-2', '5'],
                'unexpected line chunks')
        with self.subTest('integer materials only'):
            element = py2dm.Element4Q(1, 2, 3, 4, 5, materials=(1.0, -2))
            self.assertListEqual(
                element.to_line(allow_float_matid=False),
                ['E4Q', '1', '2', '3', '4', '5', '-2'],
                'unexpected line chunks')


class TestElement6T(unittest.TestCase):
    """Tests for the py2dm.Element6T class."""

    def test_card(self) -> None:
        self.assertEqual(
            py2dm.Element6T.card, 'E6T',
            'bad 2DM card')

    def test_num_nodes(self) -> None:
        self.assertEqual(
            py2dm.Element6T.num_nodes, 6,
            'bad number of nodes')

    def test___init__(self) -> None:
        with self.subTest('known good'):
            element = py2dm.Element(1, 2, 3, 4, 5, 6, 7, materials=(8.0, 9))
            self.assertEqual(
                element.id, 1,
                'bad ID')
            self.assertTupleEqual(
                element.nodes, (2, 3, 4, 5, 6, 7),
                'bad nodes')
            self.assertTupleEqual(
                element.materials, (8.0, 9),
                'bad materials')
        with self.assertRaises(py2dm.errors.CardError):
            _ = py2dm.Element6T(1, 2, 3, 4, 5, 6, materials=(7.0, 8))

    def test___eq__(self) -> None:
        element_1 = py2dm.Element6T(1, 2, 3, 4, 5, 6, 7)
        element_2 = py2dm.Element6T(2, 2, 3, 4, 5, 6, 7)
        element_3 = py2dm.Element6T(1, 4, 5, 6, 7, 8, 9)
        element_4 = py2dm.Element6T(1, 2, 3, 4, 5, 6, 7)
        self.assertNotEqual(
            element_1, element_2,
            'different ID')
        self.assertNotEqual(
            element_1, element_3,
            'different nodes')
        self.assertEqual(
            element_1, element_4,
            'separate instance but same value')
        self.assertNotEqual(
            element_1, None)

    def test___repr__(self) -> None:
        with self.subTest('no materials'):
            self.assertEqual(
                repr(py2dm.Element6T(12, 3, 4, 5, 6, 7, 8)),
                '<Element #12 [E6T]: Node IDs (3, 4, 5, 6, 7, 8)>',
                'unexpected string representation')
        with self.subTest('w/ materials'):
            self.assertEqual(
                repr(py2dm.Element6T(
                    12, 3, 4, 5, 6, 7, 8, materials=(1.0, 2))),
                ('<Element #12 [E6T]: Node IDs (3, 4, 5, 6, 7, 8) '
                 'Materials (1.0, 2)>'),
                'unexpected string representation')

    def test_num_materials(self) -> None:
        element = py2dm.Element6T(12, 3, 4, 5, 6, 7, 8, materials=(1.0, 2))
        self.assertEqual(
            element.num_materials, 2,
            'bad number of materials')

    def test_from_line(self) -> None:
        with self.subTest('known good'):
            line = 'E6T 1 2 3 4 5 6 7'
            element = py2dm.Element6T.from_line(line)
            self.assertEqual(
                element.id, 1,
                'incorrect element ID')
            self.assertTupleEqual(
                element.nodes, (2, 3, 4, 5, 6, 7),
                'incorrect nodes')
            self.assertEqual(
                element.num_materials, 0,
                'incorrect material count')
            self.assertTupleEqual(
                element.materials, (),
                'incorrect materials')
        with self.subTest('known good w/ materials'):
            line = 'E6T 2 3 4 5 6 7 8 9.0 -10'
            element = py2dm.Element6T.from_line(line)
            self.assertEqual(
                element.id, 2,
                'incorrect element ID')
            self.assertTupleEqual(
                element.nodes, (3, 4, 5, 6, 7, 8),
                'incorrect nodes')
            self.assertEqual(
                element.num_materials, 2,
                'incorrect material count')
            self.assertTupleEqual(
                element.materials, (9.0, -10),
                'incorrect materials')
        with self.subTest('bad card'):
            line = 'E3T 3 4 5 6 7 8 9'
            with self.assertRaises(py2dm.errors.CardError):
                _ = py2dm.Element6T.from_line(line)
        with self.subTest('negative element ID'):
            line = 'E6T -4 5 6 7 8 9 10'
            with self.assertRaises(py2dm.errors.FormatError):
                _ = py2dm.Element6T.from_line(line)
        with self.subTest('negative node ID'):
            line = 'E6T 5 -6 7 8 9 10 11'
            with self.assertRaises(py2dm.errors.FormatError):
                _ = py2dm.Element6T.from_line(line)
        with self.subTest('missing nodes'):
            line = 'E6T 6 7 8 9 10 11'
            with self.assertRaises(py2dm.errors.CardError):
                _ = py2dm.Element6T.from_line(line)
        with self.assertWarns(py2dm.errors.CustomFormatIgnored):
            line = 'E6T 1 2 3 4 5 6 7 8.0'
            _ = py2dm.Element6T.from_line(line, allow_float_matid=False)

    def test_to_line(self) -> None:
        with self.subTest('default'):
            element = py2dm.Element6T(
                1, 233, 3, 4, 5, 6, 7, materials=(1.0, -2, 5))
            self.assertListEqual(
                element.to_line(),
                ['E6T', '1', '233', '3', '4', '5', '6',
                    '7', ' 1.000e+00', '-2', ' 5'],
                'unexpected line chunks')
        with self.subTest('fixed_decimals'):
            element = py2dm.Element6T(
                1, 2, 3, 4, 5, 6, 7, materials=(1.0, -2, 5))
            self.assertListEqual(
                element.to_line(decimals=2),
                ['E6T', '1', '2', '3', '4', '5', '6',
                    '7', ' 1.00e+00', '-2', ' 5'],
                'unexpected line chunks')
        with self.subTest('compact'):
            element = py2dm.Element6T(
                1, 2, 3, 4, 5, 6, 7, materials=(1.0, -2, 5))
            self.assertListEqual(
                element.to_line(compact=True),
                ['E6T', '1', '2', '3', '4', '5', '6', '7', '1.0', '-2', '5'],
                'unexpected line chunks')
        with self.subTest('integer materials only'):
            element = py2dm.Element6T(
                1, 2, 3, 4, 5, 6, 7, materials=(1.0, -2))
            self.assertListEqual(
                element.to_line(allow_float_matid=False),
                ['E6T', '1', '2', '3', '4', '5', '6', '7', '-2'],
                'unexpected line chunks')


class TestElement8Q(unittest.TestCase):
    """Tests for the py2dm.Element8Q class."""

    def test_card(self) -> None:
        self.assertEqual(
            py2dm.Element8Q.card, 'E8Q',
            'bad 2DM card')

    def test_num_nodes(self) -> None:
        self.assertEqual(
            py2dm.Element8Q.num_nodes, 8,
            'bad number of nodes')

    def test___init__(self) -> None:
        with self.subTest('known good'):
            element = py2dm.Element(
                1, 2, 3, 4, 5, 6, 7, 8, 9, materials=(10.0, 11))
            self.assertEqual(
                element.id, 1,
                'bad ID')
            self.assertTupleEqual(
                element.nodes, (2, 3, 4, 5, 6, 7, 8, 9),
                'bad nodes')
            self.assertTupleEqual(
                element.materials, (10.0, 11),
                'bad materials')
        with self.assertRaises(py2dm.errors.CardError):
            _ = py2dm.Element8Q(1, 2, 3, 4, 5, 6, 7, 8, materials=(9.0, 10))

    def test___eq__(self) -> None:
        element_1 = py2dm.Element8Q(1, 2, 3, 4, 5, 6, 7, 8, 9)
        element_2 = py2dm.Element8Q(2, 2, 3, 4, 5, 6, 7, 8, 9)
        element_3 = py2dm.Element8Q(1, 4, 5, 6, 7, 8, 9, 10, 11)
        element_4 = py2dm.Element8Q(1, 2, 3, 4, 5, 6, 7, 8, 9)
        self.assertNotEqual(
            element_1, element_2,
            'different ID')
        self.assertNotEqual(
            element_1, element_3,
            'different nodes')
        self.assertEqual(
            element_1, element_4,
            'separate instance but same value')
        self.assertNotEqual(
            element_1, None)

    def test___repr__(self) -> None:
        with self.subTest('no materials'):
            self.assertEqual(
                repr(py2dm.Element8Q(12, 3, 4, 5, 6, 7, 8, 9, 10)),
                '<Element #12 [E8Q]: Node IDs (3, 4, 5, 6, 7, 8, 9, 10)>',
                'unexpected string representation')
        with self.subTest('w/ materials'):
            self.assertEqual(
                repr(py2dm.Element8Q(
                    12, 3, 4, 5, 6, 7, 8, 9, 10, materials=(1.0, 2))),
                ('<Element #12 [E8Q]: Node IDs (3, 4, 5, 6, 7, 8, 9, 10) '
                 'Materials (1.0, 2)>'),
                'unexpected string representation')

    def test_num_materials(self) -> None:
        element = py2dm.Element8Q(
            12, 3, 4, 5, 6, 7, 8, 9, 10, materials=(11.0, 12))
        self.assertEqual(
            element.num_materials, 2,
            'bad number of materials')

    def test_from_line(self) -> None:
        with self.subTest('known good'):
            line = 'E8Q 1 2 3 4 5 6 7 8 9'
            element = py2dm.Element8Q.from_line(line)
            self.assertEqual(
                element.id, 1,
                'incorrect element ID')
            self.assertTupleEqual(
                element.nodes, (2, 3, 4, 5, 6, 7, 8, 9),
                'incorrect nodes')
            self.assertEqual(
                element.num_materials, 0,
                'incorrect material count')
            self.assertTupleEqual(
                element.materials, (),
                'incorrect materials')
        with self.subTest('known good w/ materials'):
            line = 'E8Q 2 3 4 5 6 7 8 9 10 11.0 -12'
            element = py2dm.Element8Q.from_line(line)
            self.assertEqual(
                element.id, 2,
                'incorrect element ID')
            self.assertTupleEqual(
                element.nodes, (3, 4, 5, 6, 7, 8, 9, 10),
                'incorrect nodes')
            self.assertEqual(
                element.num_materials, 2,
                'incorrect material count')
            self.assertTupleEqual(
                element.materials, (11.0, -12),
                'incorrect materials')
        with self.subTest('bad card'):
            line = 'E4Q 3 4 5 6 7 8 9 10 11'
            with self.assertRaises(py2dm.errors.CardError):
                _ = py2dm.Element8Q.from_line(line)
        with self.subTest('negative element ID'):
            line = 'E8Q -4 5 6 7 8 9 10 11 12'
            with self.assertRaises(py2dm.errors.FormatError):
                _ = py2dm.Element8Q.from_line(line)
        with self.subTest('negative node ID'):
            line = 'E8Q 5 -6 7 8 9 10 11 12 13'
            with self.assertRaises(py2dm.errors.FormatError):
                _ = py2dm.Element8Q.from_line(line)
        with self.subTest('missing nodes'):
            line = 'E8Q 6 7 8 9 10 11 12 13'
            with self.assertRaises(py2dm.errors.CardError):
                _ = py2dm.Element8Q.from_line(line)
        with self.assertWarns(py2dm.errors.CustomFormatIgnored):
            line = 'E8Q 1 2 3 4 5 6 7 8 9 10.0'
            _ = py2dm.Element8Q.from_line(line, allow_float_matid=False)

    def test_to_line(self) -> None:
        with self.subTest('default'):
            element = py2dm.Element8Q(
                1, 233, 3, 4, 5, 6, 7, 8, 9, materials=(1.0, -2, 5))
            self.assertListEqual(
                element.to_line(),
                ['E8Q', '1', '233', '3', '4', '5', '6', '7',
                    '8', '9', ' 1.000e+00', '-2', ' 5'],
                'unexpected line chunks')
        with self.subTest('fixed_decimals'):
            element = py2dm.Element8Q(
                1, 2, 3, 4, 5, 6, 7, 8, 9, materials=(1.0, -2, 5))
            self.assertListEqual(
                element.to_line(decimals=2),
                ['E8Q', '1', '2', '3', '4', '5', '6', '7',
                    '8', '9', ' 1.00e+00', '-2', ' 5'],
                'unexpected line chunks')
        with self.subTest('compact'):
            element = py2dm.Element8Q(
                1, 2, 3, 4, 5, 6, 7, 8, 9, materials=(1.0, -2, 5))
            self.assertListEqual(
                element.to_line(compact=True),
                ['E8Q', '1', '2', '3', '4', '5', '6',
                    '7', '8', '9', '1.0', '-2', '5'],
                'unexpected line chunks')
        with self.subTest('integer materials only'):
            element = py2dm.Element8Q(
                1, 2, 3, 4, 5, 6, 7, 8, 9, materials=(1.0, -2))
            self.assertListEqual(
                element.to_line(allow_float_matid=False),
                ['E8Q', '1', '2', '3', '4', '5', '6', '7', '8', '9', '-2'],
                'unexpected line chunks')


class TestElement9Q(unittest.TestCase):
    """Tests for the py2dm.Element9Q class."""

    def test_card(self) -> None:
        self.assertEqual(
            py2dm.Element9Q.card, 'E9Q',
            'bad 2DM card')

    def test_num_nodes(self) -> None:
        self.assertEqual(
            py2dm.Element9Q.num_nodes, 9,
            'bad number of nodes')

    def test___init__(self) -> None:
        with self.subTest('known good'):
            element = py2dm.Element(
                1, 2, 3, 4, 5, 6, 7, 8, 9, 10, materials=(11.0, 12))
            self.assertEqual(
                element.id, 1,
                'bad ID')
            self.assertTupleEqual(
                element.nodes, (2, 3, 4, 5, 6, 7, 8, 9, 10),
                'bad nodes')
            self.assertTupleEqual(
                element.materials, (11.0, 12),
                'bad materials')
        with self.assertRaises(py2dm.errors.CardError):
            _ = py2dm.Element9Q(
                1, 2, 3, 4, 5, 6, 7, 8, 9, materials=(10.0, 11))

    def test___eq__(self) -> None:
        element_1 = py2dm.Element9Q(1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
        element_2 = py2dm.Element9Q(2, 2, 3, 4, 5, 6, 7, 8, 9, 10)
        element_3 = py2dm.Element9Q(1, 4, 5, 6, 7, 8, 9, 10, 11, 12)
        element_4 = py2dm.Element9Q(1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
        self.assertNotEqual(
            element_1, element_2,
            'different ID')
        self.assertNotEqual(
            element_1, element_3,
            'different nodes')
        self.assertEqual(
            element_1, element_4,
            'separate instance but same value')
        self.assertNotEqual(
            element_1, None)

    def test___repr__(self) -> None:
        with self.subTest('no materials'):
            self.assertEqual(
                repr(py2dm.Element9Q(12, 3, 4, 5, 6, 7, 8, 9, 10, 11)),
                '<Element #12 [E9Q]: Node IDs (3, 4, 5, 6, 7, 8, 9, 10, 11)>',
                'unexpected string representation')
        with self.subTest('w/ materials'):
            self.assertEqual(
                repr(py2dm.Element9Q(
                    12, 3, 4, 5, 6, 7, 8, 9, 10, 11, materials=(1.0, 2))),
                ('<Element #12 [E9Q]: Node IDs (3, 4, 5, 6, 7, 8, 9, 10, 11) '
                 'Materials (1.0, 2)>'),
                'unexpected string representation')

    def test_num_materials(self) -> None:
        element = py2dm.Element9Q(
            12, 3, 4, 5, 6, 7, 8, 9, 10, 11, materials=(12.0, 13))
        self.assertEqual(
            element.num_materials, 2,
            'bad number of materials')

    def test_from_line(self) -> None:
        with self.subTest('known good'):
            line = 'E9Q 1 2 3 4 5 6 7 8 9 10'
            element = py2dm.Element9Q.from_line(line)
            self.assertEqual(
                element.id, 1,
                'incorrect element ID')
            self.assertTupleEqual(
                element.nodes, (2, 3, 4, 5, 6, 7, 8, 9, 10),
                'incorrect nodes')
            self.assertEqual(
                element.num_materials, 0,
                'incorrect material count')
            self.assertTupleEqual(
                element.materials, (),
                'incorrect materials')
        with self.subTest('known good w/ materials'):
            line = 'E9Q 2 3 4 5 6 7 8 9 10 11 12.0 -13'
            element = py2dm.Element9Q.from_line(line)
            self.assertEqual(
                element.id, 2,
                'incorrect element ID')
            self.assertTupleEqual(
                element.nodes, (3, 4, 5, 6, 7, 8, 9, 10, 11),
                'incorrect nodes')
            self.assertEqual(
                element.num_materials, 2,
                'incorrect material count')
            self.assertTupleEqual(
                element.materials, (12.0, -13),
                'incorrect materials')
        with self.subTest('bad card'):
            line = 'E8Q 3 4 5 6 7 8 9 10 11 12'
            with self.assertRaises(py2dm.errors.CardError):
                _ = py2dm.Element9Q.from_line(line)
        with self.subTest('negative element ID'):
            line = 'E9Q -4 5 6 7 8 9 10 11 12 13'
            with self.assertRaises(py2dm.errors.FormatError):
                _ = py2dm.Element9Q.from_line(line)
        with self.subTest('negative node ID'):
            line = 'E9Q 5 -6 7 8 9 10 11 12 13 14'
            with self.assertRaises(py2dm.errors.FormatError):
                _ = py2dm.Element9Q.from_line(line)
        with self.subTest('missing nodes'):
            line = 'E9Q 6 7 8 9 10 11 12 13 14'
            with self.assertRaises(py2dm.errors.CardError):
                _ = py2dm.Element9Q.from_line(line)
        with self.assertWarns(py2dm.errors.CustomFormatIgnored):
            line = 'E9Q 1 2 3 4 5 6 7 8 9 10 11.0'
            _ = py2dm.Element9Q.from_line(line, allow_float_matid=False)

    def test_to_line(self) -> None:
        with self.subTest('default'):
            element = py2dm.Element9Q(
                1, 233, 3, 4, 5, 6, 7, 8, 9, 10, materials=(1.0, -2, 5))
            self.assertListEqual(
                element.to_line(),
                ['E9Q', '1', '233', '3', '4', '5', '6', '7',
                    '8', '9', '10', ' 1.000e+00', '-2', ' 5'],
                'unexpected line chunks')
        with self.subTest('fixed_decimals'):
            element = py2dm.Element9Q(
                1, 2, 3, 4, 5, 6, 7, 8, 9, 10, materials=(1.0, -2, 5))
            self.assertListEqual(
                element.to_line(decimals=2),
                ['E9Q', '1', '2', '3', '4', '5', '6', '7',
                    '8', '9', '10', ' 1.00e+00', '-2', ' 5'],
                'unexpected line chunks')
        with self.subTest('compact'):
            element = py2dm.Element9Q(
                1, 2, 3, 4, 5, 6, 7, 8, 9, 10, materials=(1.0, -2, 5))
            self.assertListEqual(
                element.to_line(compact=True),
                ['E9Q', '1', '2', '3', '4', '5', '6', '7',
                    '8', '9', '10', '1.0', '-2', '5'],
                'unexpected line chunks')
        with self.subTest('integer materials only'):
            element = py2dm.Element9Q(
                1, 2, 3, 4, 5, 6, 7, 8, 9, 10, materials=(1.0, -2))
            self.assertListEqual(
                element.to_line(allow_float_matid=False),
                ['E9Q', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '-2'],
                'unexpected line chunks')


class TestNodeString(unittest.TestCase):
    """Tests for the py2dm.NodeString class."""

    def test_card(self) -> None:
        self.assertEqual(
            py2dm.NodeString.card, 'NS',
            'bad 2DM card')

    def test___init__(self) -> None:
        node_string = py2dm.NodeString(1, 2, 3, 4, name='one')
        self.assertEqual(
            node_string.num_nodes, 4,
            'bad node count')
        self.assertTupleEqual(
            node_string.nodes,
            (1, 2, 3, 4),
            'bad nodes tuple')
        self.assertEqual(
            node_string.name, 'one',
            'bad node string name')

    def test___eq__(self) -> None:
        node_string_1 = py2dm.NodeString(1, 2, 3, 4)
        node_string_2 = py2dm.NodeString(5, 6, 7, 8)
        node_string_3 = py2dm.NodeString(1, 2, 3, 4)
        self.assertNotEqual(
            node_string_1, node_string_2,
            'different nodes')
        self.assertEqual(
            node_string_1, node_string_3,
            'separate instance but same value')
        self.assertNotEqual(
            node_string_1, None)

    def test___repr__(self) -> None:
        with self.subTest('unnamed'):
            self.assertEqual(
                repr(py2dm.NodeString(1, 2, 3, 4, 5)),
                '<Unnamed NodeString: (1, 2, 3, 4, 5)>',
                'unexpected string representation')
        with self.subTest('named'):
            self.assertEqual(
                repr(py2dm.NodeString(1, 2, 3, 4, 5, name='my node string')),
                '<NodeString "my node string": (1, 2, 3, 4, 5)>',
                'unexpected string representation')

    def test_from_line(self) -> None:
        with self.subTest('known good (short)'):
            line = 'NS 1 2 3 4 5 -6'
            node_string, is_done = py2dm.NodeString.from_line(line)
            self.assertTrue(
                is_done,
                'node string not flagged as done')
            self.assertEqual(
                node_string.num_nodes, 6,
                'unexpected number of nodes')
            self.assertIsNone(
                node_string.name,
                'node string name is not None')
            self.assertTupleEqual(
                node_string.nodes, (1, 2, 3, 4, 5, 6),
                'bad nodes tuple')
        with self.subTest('known good (multiline)'):
            line_1 = 'NS 1 2 3 4 5 6 7 8 9 10'
            line_2 = 'NS 11 12 13 14 15 16 17 18 19 20'
            line_3 = 'NS 21 22 23 24 25 26 27 28 29 -30'
            node_string, is_done = py2dm.NodeString.from_line(line_1)
            self.assertFalse(
                is_done,
                'node string incorrectly flagged as done')
            node_string, is_done = py2dm.NodeString.from_line(
                line_2, node_string)
            self.assertFalse(
                is_done,
                'node string incorrectly flagged as done')
            node_string, is_done = py2dm.NodeString.from_line(
                line_3, node_string)
            self.assertTrue(
                is_done,
                'node string not flagged as done')
            self.assertEqual(
                node_string.num_nodes, 30,
                'unexpected number of nodes')
            self.assertIsNone(
                node_string.name,
                'node string name is not None')
            self.assertTupleEqual(
                node_string.nodes, tuple(range(1, 31)),
                'bad nodes tuple')
        with self.subTest('known good (more than 10 fields)'):
            line = 'NS 1 2 3 4 5 6 7 8 9 10 11 12 13 14 -15'
            node_string, is_done = py2dm.NodeString.from_line(line)
            self.assertTrue(
                is_done,
                'node string not flagged as done')
            self.assertEqual(
                node_string.num_nodes, 15,
                'unexpected number of nodes')
            self.assertIsNone(
                node_string.name,
                'node string name is not None')
            self.assertTupleEqual(
                node_string.nodes, tuple(range(1, 16)),
                'bad nodes tuple')
        with self.subTest('numerical identifier'):
            line = 'NS 1 2 3 4 5 6 7 8 9 -10 11'
            node_string, is_done = py2dm.NodeString.from_line(line)
            self.assertTrue(
                is_done,
                'node string not flagged as done')
            self.assertEqual(
                node_string.num_nodes, 10,
                'unexpected number of nodes')
            self.assertEqual(
                node_string.name, '11',
                'bad node string name')
            self.assertTupleEqual(
                node_string.nodes, tuple(range(1, 11)),
                'bad nodes tuple')
        with self.subTest('string identifier (unquoted)'):
            line = 'NS 1 2 3 4 5 6 7 -8 lorem'
            node_string, is_done = py2dm.NodeString.from_line(line)
            self.assertTrue(
                is_done,
                'node string not flagged as done')
            self.assertEqual(
                node_string.num_nodes, 8,
                'unexpected number of nodes')
            self.assertEqual(
                node_string.name, 'lorem',
                'bad node string name')
            self.assertTupleEqual(
                node_string.nodes, tuple(range(1, 9)),
                'bad nodes tuple')
        with self.subTest('string identifier (double quoted)'):
            line = 'NS 1 2 3 4 5 6 7 8 9 10 11 -12 "ipsum"'
            node_string, is_done = py2dm.NodeString.from_line(line)
            self.assertTrue(
                is_done,
                'node string not flagged as done')
            self.assertEqual(
                node_string.num_nodes, 12,
                'unexpected number of nodes')
            self.assertEqual(
                node_string.name, 'ipsum',
                'bad node string name')
            self.assertTupleEqual(
                node_string.nodes, tuple(range(1, 13)),
                'bad nodes tuple')
        with self.subTest('bad card'):
            line = 'ND 1 2 3 4 -5'
            with self.assertRaises(py2dm.errors.CardError):
                _ = py2dm.NodeString.from_line(line)
        with self.subTest('too few nodes'):
            line = 'NS -1'
            with self.assertRaises(py2dm.errors.FormatError):
                _ = py2dm.NodeString.from_line(line)

    def test_to_line(self) -> None:
        with self.subTest('default'):
            node_string = py2dm.NodeString(*range(1, 15))
            self.assertListEqual(
                node_string.to_line(),
                ['NS', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '\n',
                 'NS', '11', '12', '13', '-14'],
                'unexpected line chunks')
        with self.subTest('single line'):
            node_string = py2dm.NodeString(*range(1, 15))
            self.assertListEqual(
                node_string.to_line(fold_after=0),
                ['NS', '1', '2', '3', '4', '5', '6', '7',
                 '8', '9', '10', '11', '12', '13', '-14'],
                'unexpected line chunks')
        with self.subTest('custom fold'):
            node_string = py2dm.NodeString(*range(1, 15))
            self.assertListEqual(
                node_string.to_line(fold_after=5),
                ['NS', '1', '2', '3', '4', '5', '\n',
                 'NS', '6', '7', '8', '9', '10', '\n',
                 'NS', '11', '12', '13', '-14'],
                'unexpected line chunks')
        with self.subTest('default w/ name'):
            node_string = py2dm.NodeString(*range(1, 15), name='test')
            self.assertListEqual(
                node_string.to_line(),
                ['NS', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '\n',
                 'NS', '11', '12', '13', '-14', 'test'],
                'unexpected line chunks')
        with self.subTest('single line w/ name'):
            node_string = py2dm.NodeString(*range(1, 15), name='test')
            self.assertListEqual(
                node_string.to_line(fold_after=0),
                ['NS', '1', '2', '3', '4', '5', '6', '7',
                 '8', '9', '10', '11', '12', '13', '-14', 'test'],
                'unexpected line chunks')
        with self.subTest('name excluded'):
            node_string = py2dm.NodeString(*range(1, 15), name='test')
            self.assertListEqual(
                node_string.to_line(include_name=False),
                ['NS', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '\n',
                 'NS', '11', '12', '13', '-14'],
                'unexpected line chunks')


class TestElementFactory(unittest.TestCase):
    """Test for the element_factory() utility method."""

    def test_element_factory(self) -> None:
        from py2dm._entities import element_factory
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
                    element_factory(line), instance,
                    'wrong class returned')
        with self.subTest('fallback error'):
            with self.assertRaises(NotImplementedError):
                element_factory('NOT-AN-ELEMENT lorem ipsum dolor sit amet')
