"""Custom exceptions for Py2DM."""


class Py2DMError(BaseException):
    """Base exception for any errors specific to Py2DM.

    This may be used to catch any custom exceptions raised by this
    module.

    """


class ReadError(Py2DMError):
    """Base exception for errors when reading a 2DM file."""


class FormatError(ReadError):
    """Base exception related to misformatted 2DM files."""


class CardError(FormatError):
    """Error used for issues with a particular 2DM card.

    This is a subclass of :class:`FormatError`.

    This generally means that the number and type of arguments found
    did not meet what was expected based on the card tag.

    """

    def __init__(self, card: str, message: str = '') -> None:
        super().__init__(message)
        self.card = card


class MissingCardError(FormatError):
    """Raised if a required 2DM card is not present.

    This is a subclass of :class:`FormatError`.

    """


class Py2DMWarning(Warning):
    """Base class for any warnings specific to Py2DM.

    This may be used to filter any custom warnings broadcast by this
    module.

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


class UnsupportedCardError(FormatError):
    """Raised if an unsupported tag is encountered.

    This is used to warn the user that some of the information in the
    2DM file will be lost if the mesh is loaded and re-saved.

    This is a subclass of :class:`Py2DMWarning`.

    """
