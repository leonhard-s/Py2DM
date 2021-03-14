/* Reimplementation of the Py2DM line parsers in C++.

This is meant to be a drop-in replacement to speed up Py2DM when used
in a cPython extension.
*/

#define PY_SSIZE_T_CLEAN

#include "Python.h"
#include "assert.h"
#include <string>
#include <vector>

/* -------------------------------------------------------------------------- */
/*                          Format-specific utilities                         */
/* -------------------------------------------------------------------------- */

/**
 * @brief Check whether a given 2DM card represents an element.
 * 
 * @param s The 2DM card to check.
 * @return true if it is an element, otherwise false.
 */
bool card_is_element(const std::string s)
{
    return s == "E2L" ||
           s == "E3L" ||
           s == "E3T" ||
           s == "E4Q" ||
           s == "E6T" ||
           s == "E8Q" ||
           s == "E9Q";
}

/**
 * @brief Return the number of nodes in an element.
 * 
 * Note that elements can have any number of materials assigned to them
 * in addition to their defining nodes.
 * 
 * @param s The 2DM card of the element to return.
 * @return The number of nodes as a positive integer, or -1 if the
 * given card is not a known element.
 */
size_t
nodes_per_element(const std::string s)
{
    if (s == "E2L")
    {
        return 2;
    }
    if (s == "E3L" || s == "E3T")
    {
        return 3;
    }
    if (s == "E4Q")
    {
        return 4;
    }
    if (s == "E6T")
    {
        return 6;
    }
    if (s == "E8Q")
    {
        return 8;
    }
    if (s == "E9Q")
    {
        return 9;
    }
    return -1;
}

/* -------------------------------------------------------------------------- */
/*                              Internal helpers                              */
/* -------------------------------------------------------------------------- */

/**
 * @brief C string version of Python's `str.split()`.
 * 
 * This method uses the Python implementation internally and shares its
 * behaviour.
 * 
 * @param s The input string to split.
 * @param d The delimiter to split at.
 * @param maxsplit The maximum number of splits performed.
 * @return A vector of substrings split at the given delimiter.
 */
std::vector<std::string>
split(const std::string s, const std::string d, const Py_ssize_t maxsplit)
{
    PyObject *py_s = PyUnicode_FromString(s.c_str());
    PyObject *py_d = PyUnicode_FromString(d.c_str());
    if (!PyUnicode_GetLength(py_d))
    {
        Py_DecRef(py_d);
        py_d = nullptr;
    }
    PyObject *py_l = PyUnicode_Split(py_s, py_d, maxsplit);
    Py_DecRef(py_s);
    if (py_d != nullptr)
    {
        Py_DecRef(py_d);
    }
    Py_ssize_t n = PyList_Size(py_l);
    std::vector<std::string> chunks(n);
    for (Py_ssize_t i = 0; i < n; i++)
    {
        PyObject *py_i = PyList_GetItem(py_l, i);
        chunks[i] = PyUnicode_AsUTF8(py_i);
        Py_DecRef(py_i);
    }
    return chunks;
}

/**
 * @brief Return the chunks in the given line.
 * 
 * This removes any trailing comments before splitting the line into
 * whitespace-separated chunks for further processing.
 * These chunks will not contain whitespace or comments; only data.
 * 
 * @param line The line to parse.
 * @return A vector of data chunks in the given line.
 */
std::vector<std::string>
chunks_from_line(const char *line)
{
    const std::string trimmed = split(line, "#", 1)[0];
    return split(trimmed, "", -1);
}

/**
 * @brief Convert a string to a long.
 * 
 * This uses Python's string parsing strategy to ensure equal fault
 * tolerance.
 * 
 * Raises a Python ValueError if conversion is not possible.
 * 
 * @param s The string to convert.
 * @param err Error flag. Set to true on error
 * @return Converted long or NULL on error.
 */
long string_to_long(const std::string s, bool *err)
{
    PyObject *py_l = PyLong_FromString(s.c_str(), nullptr, 10);
    if (PyErr_Occurred())
    {
        *err = true;
        return -1;
    }
    long l = PyLong_AsLong(py_l);
    Py_DecRef(py_l);
    if (PyErr_Occurred())
    {
        *err = true;
        return -1;
    }
    return l;
}

/**
 * @brief Convert a string to a double.
 * 
 * This uses Python's string parsing strategy to ensure equal fault
 * tolderance.
 * 
 * Raises a Python ValueError if conversion is not possible.
 * 
 * @param s The string to convert.
 * @param err Error flag. Set to true on rrror.
 * @return Converted double or NULL on error.
 */
double
string_to_double(const std::string s, bool *err)
{
    PyObject *py_s = PyUnicode_FromString(s.c_str());
    PyObject *py_d = PyFloat_FromString(py_s);
    Py_DecRef(py_s);
    if (PyErr_Occurred())
    {
        *err = true;
        return -1.0;
    }
    double d = PyFloat_AsDouble(py_d);
    Py_DecRef(py_d);
    if (PyErr_Occurred())
    {
        *err = true;
        return -1.0;
    }
    return d;
}

/* -------------------------------------------------------------------------- */
/*                              Custom exceptions                             */
/* -------------------------------------------------------------------------- */

/**
 * @brief Get a custom exception object from the py2dm.errors submodule.
 * 
 * @param name The name of the object to retrieve.
 * @return The custom Exception matching the given name.
 */
PyObject *
get_error(const std::string name)
{
    PyObject *mod = PyImport_ImportModule("py2dm.errors");
    if (!mod)
    {
        return nullptr;
    }
    PyObject *mod_dict = PyModule_GetDict(mod);
    Py_DecRef(mod);
    PyObject *key = PyUnicode_FromString(name.c_str());
    PyObject *exc = PyDict_GetItemWithError(mod_dict, key);
    Py_DecRef(key);
    if (!exc)
    {
        return PyExc_Exception;
    }
    return exc;
}

/* -------------------------------------------------------------------------- */
/*                              2DM card parsers                              */
/* -------------------------------------------------------------------------- */

/**
 * @brief Parse a string into a node.
 * 
 * This converts a valid node definition string into a Python tuple
 * that can be used to instantiate the corresponding Node object.
 * 
 * @param self Reference to the function object iself.
 * @param args Positional arguments.
 * @param kwargs Keyword arguments.
 * @return A tuple of an integer (id) and three floats (x, y, and z
 * position), or nullptr on error.
 */
static PyObject *
py2dm_parse_node(PyObject *, PyObject *args, PyObject *kwargs)
{
    char *line;
    bool allow_zero_index = false;
    static char *keywords[] = {
        (char *)"line",
        (char *)"allow_zero_index",
        nullptr};
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "s|p", keywords,
                                     &line, &allow_zero_index))
    {
        return nullptr;
    }
    // Parse line
    const std::vector<std::string> chunks = chunks_from_line(line);
    // Length
    if (chunks.size() < 5)
    {
        PyErr_Format(get_error("CardError"),
                     "Node definitions require at least 4 fields "
                     "(id, x, y, z), got %d",
                     chunks.size() - 1);
        return nullptr;
    }
    // 2DM card
    if (chunks[0] != "ND")
    {
        PyErr_Format(get_error("CardError"),
                     "Invalid node card \"%s\"",
                     chunks[0]);
        return nullptr;
    }
    // Node ID
    bool err = false;
    long id = string_to_long(chunks[1], &err);
    if (err)
    {
        return nullptr;
    }
    if (id <= 0 && !(id == 0 && allow_zero_index))
    {
        PyErr_Format(get_error("FormatError"), "Invalid node ID: %d", id);
        return nullptr;
    }
    // Coordinates
    err = false;
    double x = string_to_double(chunks[2], &err);
    if (err)
    {
        return nullptr;
    }
    err = false;
    double y = string_to_double(chunks[3], &err);
    if (err)
    {
        return nullptr;
    }
    err = false;
    double z = string_to_double(chunks[4], &err);
    if (err)
    {
        return nullptr;
    }
    /** TODO: Warn about unused fields */
    return Py_BuildValue("lddd", id, x, y, z);
}

/**
 * @brief Parse a string into an element.
 * 
 * This converts a valid element definition string into a Python tuple
 * that can be used to instantiate the corresponding Element subclass.
 * 
 * @param self Reference to the function object iself.
 * @param args Positional arguments.
 * @param kwargs Keyword arguments.
 * @return A tuple of an integer (id) and two tuples. The first
 * contains the node IDs of the element, the second contains any
 * material IDs.
 */
static PyObject *
py2dm_parse_element(PyObject *, PyObject *args, PyObject *kwargs)
{
    char *line;
    bool allow_float_matid = true;
    bool allow_zero_index = false;
    static char *keywords[] = {
        (char *)"line",
        (char *)"allow_zero_index",
        (char *)"allow_float_matid",
        nullptr};
    if (!PyArg_ParseTupleAndKeywords(
            args, kwargs, "s|pp", keywords,
            &line, &allow_zero_index, &allow_float_matid))
    {
        return nullptr;
    }
    // Parse line
    const std::vector<std::string> chunks = chunks_from_line(line);
    // Length (generic)
    if (chunks.size() < 4)
    {
        PyErr_Format(get_error("CardError"),
                     "Element definitions require at least 3 fields "
                     "(id, node_1, node_2), got %d",
                     chunks.size() - 1);
        return nullptr;
    }
    // 2DM card
    const std::string card = chunks[0];
    if (!card_is_element(card))
    {
        PyErr_Format(get_error("CardError"), "Invalid element card \"%s\"", card);
        return nullptr;
    }
    // Length (card known)
    size_t num_nodes = nodes_per_element(card);
    assert(num_nodes > 0);
    if (chunks.size() < num_nodes + 2)
    {
        PyErr_Format(get_error("CardError"),
                     "%s element definition requires at least %d fields "
                     "(id, node_1, ..., node_%d), got %d",
                     card, num_nodes - 1, num_nodes - 1, chunks.size() - 1);
        return nullptr;
    }
    // Element ID
    bool err = false;
    long id = string_to_long(chunks[1], &err);
    if (err)
    {
        return nullptr;
    }
    if (id <= 0 && !(id == 0 && allow_zero_index))
    {
        PyErr_Format(get_error("FormatError"), "Invalid element ID: %d", id);
        return nullptr;
    }
    // Node IDs
    PyObject *nodes = PyTuple_New(num_nodes);
    for (size_t i = 2; i < num_nodes + 2; i++)
    {
        err = false;
        long node_id = string_to_long(chunks[i], &err);
        if (err)
        {
            Py_DecRef(nodes);
            return nullptr;
        }
        if (node_id <= 0 && !(node_id == 0 && allow_zero_index))
        {
            PyErr_Format(get_error("FormatError"), "Invalid node ID: %d", node_id);
            Py_DecRef(nodes);
            return nullptr;
        }
        PyTuple_SetItem(nodes, i - 2, PyLong_FromLong(node_id));
    }
    // Material IDs
    PyObject *materials = PyTuple_New(chunks.size() - num_nodes - 2);
    for (size_t i = num_nodes + 2; i < chunks.size(); i++)
    {
        err = false;
        long matid_int = string_to_long(chunks[i], &err);
        if (!err)
        {
            // Conversion successful
            PyTuple_SetItem(
                materials, i - num_nodes - 2, PyLong_FromLong(matid_int));
            continue;
        }
        // Conversion failed
        if (!allow_float_matid)
        {
            Py_DecRef(nodes);
            Py_DecRef(materials);
            return nullptr;
        }
        // Try converting to double instead
        PyErr_Clear();
        err = false;
        double matid_double = string_to_double(chunks[i], &err);
        if (err)
        {
            Py_DecRef(nodes);
            Py_DecRef(materials);
            return nullptr;
        }
        PyTuple_SetItem(
            materials, i - num_nodes - 2, PyFloat_FromDouble(matid_double));
    }
    // Build return tuple
    PyObject *r = Py_BuildValue("iOO", id, nodes, materials);
    Py_DecRef(nodes);
    Py_DecRef(materials);
    return r;
}

/**
 * @brief Parse a string into a node string.
 * 
 * This converts a valid node string definition string into a Python
 * tuple that can be used to instantiate the corresponding NodeString
 * object.
 * 
 * @param self Reference to the function object iself.
 * @param args Positional arguments.
 * @param kwargs Keyword arguments.
 * @return A Python tuple consisting of the list of nodes, a Boolean
 * flag representing whether the end of teh node string has been
 * reached, and an optional name or identifier string.
 */
static PyObject *
py2dm_parse_node_string(PyObject *, PyObject *args, PyObject *kwargs)
{
    char *line;
    PyObject *nodes = nullptr;
    bool allow_zero_index = false;
    static char *keywords[] = {
        (char *)"line",
        (char *)"allow_zero_index",
        (char *)"nodes",
        nullptr};
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "s|pO", keywords,
                                     &line, &allow_zero_index, &nodes))
    {
        return nullptr;
    }
    // Set default value
    if (!PyList_Check(nodes))
    {
        if (nodes == Py_None)
        {
            Py_DecRef(Py_None);
        }
        nodes = PyList_New(0);
    }
    Py_IncRef(nodes);
    // Parse line
    const std::vector<std::string> chunks = chunks_from_line(line);
    // Length
    if (chunks.size() < 2)
    {
        Py_DecRef(nodes);
        PyErr_Format(get_error("CardError"),
                     "Node string definitions require at least 1 field "
                     "(node_id), got %d",
                     chunks.size() - 1);
        return nullptr;
    }
    // 2DM card
    if (chunks[0] != "NS")
    {
        Py_DecRef(nodes);
        PyErr_Format(get_error("CardError"),
                     "Invalid node string card \"%s\"",
                     chunks[0]);
        return nullptr;
    }
    // Node IDs
    if (!PyList_Check(nodes))
    {
        Py_DecRef(nodes);
        PyErr_SetString(PyExc_TypeError, "Argument \"nodes\" must be a list");
        return nullptr;
    }
    bool is_done = false;
    std::string name = "";
    for (size_t i = 1; i < chunks.size(); i++)
    {
        bool err = false;
        long id = string_to_long(chunks[i], &err);
        if (err)
        {
            Py_DecRef(nodes);
            return nullptr;
        }
        if (id == 0 && !allow_zero_index)
        {
            Py_DecRef(nodes);
            PyErr_Format(get_error("FormatError"), "Invalid node ID: %d", id);
            return nullptr;
        }
        if (id < 0)
        {
            // End of node string
            is_done = true;
            PyList_Append(nodes, PyLong_FromLong(abs(id)));
            // Check final identifier
            if (i + 1 < chunks.size())
            {
                name = chunks[i + 1];
            }
            break;
        }
        PyList_Append(nodes, PyLong_FromLong(id));
    }
    // Build return tuple
    return Py_BuildValue("ONs", nodes, PyBool_FromLong(is_done), name);
}

/* -------------------------------------------------------------------------- */
/*                          Python module definition                          */
/* -------------------------------------------------------------------------- */

/** Method table */
static PyMethodDef Py2dmCParserMethods[] = {
    {"parse_element", (PyCFunction)py2dm_parse_element,
     METH_VARARGS | METH_KEYWORDS, "Parse a 2DM element definition."},
    {"parse_node", (PyCFunction)py2dm_parse_node,
     METH_VARARGS | METH_KEYWORDS, "Parse a 2DM node definition."},
    {"parse_node_string", (PyCFunction)py2dm_parse_node_string,
     METH_VARARGS | METH_KEYWORDS, "Parse a 2DM node string definition."},
    {nullptr, nullptr, 0, nullptr}};

/** Module definition */
static struct PyModuleDef Py2dmCParserModule = {
    PyModuleDef_HEAD_INIT,
    "_cparser",
    "C reimplementation of the 2DM entity parser. "
    "Refer to its docstring for details.",
    -1,
    Py2dmCParserMethods};

/** Module initialiser */
PyMODINIT_FUNC
PyInit__cparser(void)
{
    return PyModule_Create(&Py2dmCParserModule);
}