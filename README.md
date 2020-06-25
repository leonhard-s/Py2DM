# Py2DM

A Python module for reading and writing SMS 2DM mesh files.

## Documentation

This project's documentation is hosted at [Read the Docs](https://py2dm.readthedocs.io/en/latest/).

### Supported 2DM Cards

This module currently only supports a small subset of the cards defined in the 2DM format specification. If your use-case requires support of additional cards, feel free to get in touch via the [repository issues](https://github.com/leonhard-s/Py2DM/issues).

| Card                   | Description                            | Python representation                                                                     |
| :--------------------- | :------------------------------------- | :---------------------------------------------------------------------------------------- |
| MESH2D                 | File format identifier                 | -                                                                                         |
| NUM_MATERIALS_PER_ELEM | The number of material IDs per element | -                                                                                         |
| ND                     | A 3D mesh node                         | [`Node`](https://py2dm.readthedocs.io/en/latest/api.html#py2dm.entities.Node)             |
| NS                     | A line string connecting nodes         | [`NodeString`](https://py2dm.readthedocs.io/en/latest/api.html#py2dm.entities.NodeString) |
| E2L                    | Two-noded line element                 | [`Element2L`](https://py2dm.readthedocs.io/en/latest/api.html#py2dm.entities.Element2L)   |
| E3L                    | Three-noded linear element             | [`Element3L`](https://py2dm.readthedocs.io/en/latest/api.html#py2dm.entities.Element3L)   |
| E3T                    | Three-noded triangular element         | [`Element3T`](https://py2dm.readthedocs.io/en/latest/api.html#py2dm.entities.Element3T)   |
| E6T                    | Six-noded triangular element           | [`Element6T`](https://py2dm.readthedocs.io/en/latest/api.html#py2dm.entities.Element6T)   |
| E4Q                    | Four-noded quadrilateral element       | [`Element4Q`](https://py2dm.readthedocs.io/en/latest/api.html#py2dm.entities.Element4Q)   |
| E8Q                    | Eight-noded quadrilateral element      | [`Element8Q`](https://py2dm.readthedocs.io/en/latest/api.html#py2dm.entities.Element8Q)   |
| E9Q                    | Nine-noded quadrilateral element       | [`Element9Q`](https://py2dm.readthedocs.io/en/latest/api.html#py2dm.entities.Element9Q)   |

## Getting Started

> **Note:** Please note that this module is in very early stages of development and is subject to heavy changes. Be sure to specify the exact version to use with your projects until this disclaimer is removed as there is not stable API yet.

### Reading 2DM Files

Reading is performed via the `py2dm.Reader` class and its attributes `nodes`, `elements`, and `node_strings`. Alternatively, you can use their iterator equivalents `iter_nodes()`, `iter_elements()`, and `iter_node_strings()`, which are preferable for large meshes due to the reduced memory footprint.

```py
with py2dm.Reader('path/to/mesh.2dm') as mesh:
    for node in mesh.iter_nodes():
        if node.id % 10 == 0:
            print(node)
            
# The above will print the following:
Node #10: (1200.0, 200.0, 20.0)
Node #20: (1120.0, 220.0, 10.0)
...
```

### Writing 2DM Files

The `py2dm.Writer` class provides the `node()`, `element()`, and `node_string()` factory methods to add new geometries to the mesh. The factories for nodes and elements will return the ID they were assigned.

After adding your geometries, use the `py2dm.Writer.write()` method to commit the geometries to file.

```py
with py2dm.Writer('path/to/mesh.2dm') as mesh:
    # Create nodes
    for i in range(10):
        mesh.node(float(i), 1.0, i % 2)
    # Create elements
    mesh.element(py2dm.Element2L, (1, 2))
    mesh.element(py2dm.Element3T, (1, 2, 3))
    # Save mesh
    mesh.write()
```
