# Py2DM

A Python module for reading and writing [SMS 2DM](https://www.xmswiki.com/wiki/SMS:2D_Mesh_Files_*.2dm) mesh files.

![PyPI - License](https://img.shields.io/pypi/l/py2dm)
![GitHub Workflow Status](https://img.shields.io/github/workflow/status/leonhard-s/py2dm/Run%20Python%20unit%20tests?label=tests)
[![Coveralls github branch](https://img.shields.io/coveralls/github/leonhard-s/Py2DM/master)](https://coveralls.io/github/leonhard-s/Py2DM)
[![CodeFactor Grade](https://img.shields.io/codefactor/grade/github/leonhard-s/py2dm)](https://www.codefactor.io/repository/github/leonhard-s/py2dm)
[![PyPI](https://img.shields.io/pypi/v/py2dm)](https://pypi.org/project/py2dm/)
[![Read the Docs](https://img.shields.io/readthedocs/py2dm)](https://py2dm.readthedocs.io/en/latest/)

***

- Support for all standard 2DM element types
- Optional C++ parser extensions
- Designed with large meshes (>10 million cells) in mind
- Python version 3.6+\*
- Fully type annotated

*\*Python versions 3.6 and 3.7 require external packages. The the [installation](#installation) section for details.*

The documentation for this project is hosted at [Read the Docs](https://py2dm.readthedocs.io/en/latest/).

## Basic usage

The following sections cover basic use cases to illustrate the Py2DM interface.

For detailed instructions, performance considerations and advanced use cases, please refer to the [documentation](https://py2dm.readthedocs.io/en/latest/).

### Reading mesh files

The `py2dm.Reader` class provides multiple interfaces for extracting mesh data.

For iterator-based access, the `.iter_nodes()`, `.iter_elements()` and `.iter_node_strings()` methods are available. These allow specifying the range of elements to retrieve. Alternatively, the `.elements`, `.nodes`, and `node_strings` properties provide a shorthand for the corresponding iterator's default values.

```py
import py2dm

with py2dm.Reader('path/to/mesh.2dm') as mesh:
    for node in mesh.iter_nodes():
        if node.id % 10 == 0:
            print(node)

# The above will print the following:
'<Node #10: (1200.0, 200.0, 20.0)>'
'<Node #20: (1120.0, 220.0, 10.0)>'
...
```

To access a given element or node by its unique ID, use the `.element()` and `.node()` method respectively:

```py
import py2dm

with py2dm.Reader('path/to/mesh.2dm') as mesh:
    for element in mesh.elements:
        coords = [mesh.node(n).pos for n in element.nodes]
        print(f'Element #{element.id} coordinates:\n'
              f'\t{coords}')

# The above will print the following:
'Element #1 coordinates:'
'    [(1.0, 2.0, 2.0), (2.0, 2.0, 1.5), (2.0, 1.0, 1.75)]'
'Element #2 coordinates:'
'    [(2.0, 2.0, 1.5), (2.0, 1.0, 1.75), (1.0, 1.0, 1.25)]'
...
```

### Writing mesh files

The `py2dm.Writer` class provides the `node()`, `element()`, and `node_string()` factory methods to add new geometries to the mesh. The factories for nodes and elements will return the ID they were assigned.

```py
with py2dm.Writer('path/to/mesh.2dm') as mesh:

    # Nodes can be instantiated first and added later
    my_node = py2dm.Node(1, -5.0, -5.0, 0.1)
    mesh.node(my_node)

    # Alternatively, you can use the Writer.node() method as a factory
    mesh.node(2, -5.0, 5.0, 0.2)

    # Specifying a negative ID will auto-select it based on the number
    # of existing nodes in the mesh
    mesh.node(-1, 5.0, -5.0, 0.3)
    mesh.node(-1, 5.0, 5.0, 0.2)

    # Similarly, elements can also be created separately or via the
    # factory method
    my_element = py2dm.Element3T(1, 1, 2, 3)
    mesh.element(my_element)

    # Here too you can use a negative value to auto-select an ID
    mesh.element('E3T', -1, 2, 4, 3)
```

## Format support

The 2DM standard has been extended several times by different parties over the years. This led to the original [2DM format specification](https://www.xmswiki.com/wiki/SMS:2D_Mesh_Files_*.2dm) no longer matching SMS' own implementation, or those of other software packages such as [TUFLOW](https://tuflow.com/products/tuflow/) or [BASEMENT](https://basement.ethz.ch/).

Py2DM attempts to strike a balance of supporting these custom format variants without breaking compatibility with the original standard.

### Notable deviations from the 2DM standard

- The maximum ID limit of 999'999 is not enforced.

- Floating point values may be used as material ID0s by default.

  You can set the `allow_float_matid` flag to False to quietly discard floating point materials in the mesh:

  ```py
  with py2dm.Reader('mesh.2dm', allow_float_matid=False) as mesh:
    ...
  ```

- Zero-based indices are support if the `zero_index` flag is set upon reader instantiation:

  ```py
  with py2dm.Reader('mesh.2dm', zero_index=True) as mesh:
    my_node = mesh.node(0)  # This would normally cause an error
  ```

More information on the various 2DM dialects can be found on the [Subformats](https://py2dm.readthedocs.io/en/latest/subformats.html) page of the project documentation.

## Installation

Py2DM is available on [PyPI](https://pypi.org/project/py2dm) and can be installed with pip:

```sh
python -m pip install --upgrade py2dm
```

### Requirements

Py2DM is written for Python 3.8 and up and requires no additional packages on this version.

For Python versions 3.6 and 3.7 (notably the ones used by [QGIS 3](https://qgis.org/) as of writing this), two additional packages are required to provide functionality that was not yet available in the standard library at the time.

- [typing_extensions](https://pypi.org/project/typing-extensions/)
- [cached-property](https://pypi.org/project/cached-property/)

**The above packages are only required for Python versions 3.6 and 3.7, with Python 3.8+, no third-party dependencies are needed.**

## Contributing

If you have encountered any bugs or performance issues, please do get in touch via the [repository issues](https://github.com/leonhard-s/auraxium/issues).

Similarly, any information on additional subformats or software-specific caveats is highly appreciated.
