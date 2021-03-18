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
 * @return The number of nodes as a positive integer, or 0 if the
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
    return 0;
}

/* -------------------------------------------------------------------------- */
/*                              Internal helpers                              */
/* -------------------------------------------------------------------------- */

/**
 * @brief Return whether the given character represents whitespace.
 * 
 * The characters considered whitespace are the ones from the
 * `string.whitespace` constant in Python 3.8.5.
 * 
 * @param c The character to check.
 * @return True if Python considers the given character to be
 * whitespace, otherwise false.
 */
bool is_whitespace(const char c)
{
    return (c == ' ' ||    // Space
            c == '\t' ||   // Tab
            c == '\n' ||   // Linefeed
            c == '\r' ||   // Return
            c == '\x0b' || // Formfeed
            c == '\x0c');  // Vertical tab
}

/**
 * @brief Whitespace-only implementation of Python's `str.split()`.
 * 
 * This function is not intended to be called directly, please call
 * `split()` with an empty delimiter string instead.
 * 
 * @param s The input string to split.
 * @param maxsplit The maximum number of splits allowed. If set to a
 * negative value, s will be split at every delimiter occurrence.
 * @return A vector of substrings extracted between delimiter
 * occurrences.
 */
std::vector<std::string>
split_any_whitespace(const std::string s, const ssize_t maxsplit)
{
    std::vector<std::string> chunks;
    size_t start, end = 0, len = s.length();
    for (ssize_t splits = 0; maxsplit < 0 || splits < maxsplit; splits++)
    {
        start = std::string::npos;
        for (size_t i = end; i < len; i++)
        {
            if (!is_whitespace(s[i]))
            {
                start = i;
                break;
            }
        }
        if (start == std::string::npos)
        {
            break;
        }
        end = std::string::npos;
        for (size_t i = start; i < len; i++)
        {
            if (is_whitespace(s[i]))
            {
                end = i;
                break;
            }
        }
        chunks.push_back(s.substr(start, end - start));
    }
    return chunks;
}

/**
 * @brief Split a C++ string at a delimiter substring.
 * 
 * This function emulates the Python `str.split()` implementation, but
 * utilises C++ strings to avoid the Python object overhead.
 * 
 * @param s The input string to split.
 * @param d The delimiter to split at. If empty, string will not be
 * split.
 * @param maxsplit The maximum number of splits allowed. If set to a
 * negative value, s will be split at every delimiter occurrence.
 * @return A vector of substrings extracted between delimiter
 * occurrences.
 */
std::vector<std::string>
split(const std::string s, std::string d, const ssize_t maxsplit)
{
    /** NOTE: Python's `str.split()` splits on any whitespace character
     * if no delimiter is specified. Since this requires checking for
     * multiple delimiters, this functionality is implemented
     * separately. */
    if (d.empty())
    {
        return split_any_whitespace(s, maxsplit);
    }
    std::vector<std::string> chunks;
    size_t start, end = 0;
    for (ssize_t splits = 0; maxsplit < 0 || splits < maxsplit; splits++)
    {
        start = s.find_first_not_of(d, end);
        end = s.find(d, start);
        chunks.push_back(s.substr(start, end - start));
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
chunks_from_line(const std::string line)
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
 * @param err Error flag. Set to true on error.
 * @return Converted long or -1 on error.
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
 * @param err Error flag. Set to true on error.
 * @return Converted double or -1.0 on error.
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
                     chunks[0].c_str());
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
        PyErr_Format(get_error("CardError"),
                     "Invalid element card \"%s\"",
                     card.c_str());
        return nullptr;
    }
    // Length (card known)
    size_t num_nodes = nodes_per_element(card);
    assert(num_nodes < PY_SSIZE_T_MAX);
    if (chunks.size() < num_nodes + 2)
    {
        PyErr_Format(get_error("CardError"),
                     "%s element definition requires at least %d fields "
                     "(id, node_1, ..., node_%d), got %d",
                     card.c_str(), num_nodes - 1,
                     num_nodes - 1, chunks.size() - 1);
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
    assert(num_nodes < PY_SSIZE_T_MAX);
    PyObject *nodes = PyTuple_New((Py_ssize_t)num_nodes);
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
            PyErr_Format(
                get_error("FormatError"),
                "Invalid node ID: %d",
                node_id);
            Py_DecRef(nodes);
            return nullptr;
        }
        assert((i - 2) < PY_SSIZE_T_MAX);
        PyTuple_SetItem(nodes, (Py_ssize_t)(i - 2), PyLong_FromLong(node_id));
    }
    // Material IDs
    assert((chunks.size() - num_nodes - 2) < PY_SSIZE_T_MAX);
    PyObject *materials = PyTuple_New(
        (Py_ssize_t)(chunks.size() - num_nodes - 2));
    for (size_t i = num_nodes + 2; i < chunks.size(); i++)
    {
        err = false;
        long matid_int = string_to_long(chunks[i], &err);
        if (!err)
        {
            // Conversion successful
            assert((i - num_nodes - 2) < PY_SSIZE_T_MAX);
            PyTuple_SetItem(materials, (Py_ssize_t)(i - num_nodes - 2),
                            PyLong_FromLong(matid_int));
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
        assert((i - num_nodes - 2) < PY_SSIZE_T_MAX);
        PyTuple_SetItem(materials, (Py_ssize_t)(i - num_nodes - 2),
                        PyFloat_FromDouble(matid_double));
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
                     chunks[0].c_str());
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
    return Py_BuildValue("ONs", nodes, PyBool_FromLong(is_done), name.c_str());
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