"""Defines custom exception and warning types used by Py2DM."""


class Py2DMError(Exception):
    """Base exception for any errors specific to Py2DM.

    Any exceptions that arise from within Py2DM will be a subclass of
    this exception type. This includes file format issues, parsing
    errors, or any other issues that are not the immediate result of
    user error.

    Errors caused by the user, such as attempting to access an element
    that does not exist in a given mesh, may still return standard
    exception types (e.g. :class:`KeyError`).

    You can catch this base class to catch any custom exceptions raised
    by this module.

    .. code-block:: python3

        path = 'my-mesh.2dm'
        try:
            with py2dm.Reader(path) as mesh:
                ...  # do stuff

        except py2dm.errors.Py2DMError as err:
            raise RuntimeError(f'Unable to read file: {path}') from err

    """


class ReadError(Py2DMError):
    """Base exception for errors when reading a 2DM file.

    This subclass of :class:`Py2DMError` can be used to provide more
    helpful errors to the user when the same operation reads and writes
    mesh files.

    :param filename: Name of the file being read
    """

    def __init__(self, message: str, filename: str) -> None:
        super().__init__(message)
        self.filename: str = filename


class MissingCardError(ReadError):
    """Raised if a required 2DM card is not present.

    This is a subclass of :class:`ReadError`.

    :param filename: Name of the file being read
    """


class FormatError(Py2DMError):
    """Base exception type for errors encountered while parsing a mesh.

    This includes unknown or invalid tags, missing file headers or
    unsupported ID orderings.

    This is a subclass of :class:`Py2DMError`.
    """


class CardError(FormatError):
    """Exception for card-specific format violations.

    This is a subclass of :class:`FormatError`.

    This exception is used for any unresolvable format violations for a
    given 2DM card. This includes the number of fields, their type, or
    the card identifier itself not being recognized.
    """


class WriteError(Py2DMError):
    """Base exception for errors when writing a 2DM file.

    This subclass of :class:`Py2DMError` can be used to provide more
    helpful errors to the user when the same operation reads and writes
    mesh files.
    """


class Py2DMWarning(Warning):
    """Base class for any warnings specific to Py2DM.

    This may be used to filter any custom warnings broadcast by this
    module.
    """


class FileIsClosedError(Py2DMError):
    """Raised if the underlying file has been closed.

    This is raised when attempting to interact with a reader or writer
    after its :meth:`py2dm.Reader.close` method has been called.
    """


class FormatWarning(Py2DMWarning):
    """Warn about a format issue with a file that could be handled."""


class CustomFormatIgnored(FormatWarning):
    """A custom, application-specific format extension was ignored.

    Some programs utilise custom formats or extra columns. When PY2DM
    recognises such a format but isn't able to keep its data, it sends
    this warning to notify the user of the potential loss of
    information.

    """
