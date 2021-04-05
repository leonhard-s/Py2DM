"""Type hinting support module."""

# pylint: disable=invalid-name

from typing import Callable, Generic, Any, Optional, Type, TypeVar, overload

_T = TypeVar('_T')

try:
    from typing import Literal
except ImportError:  # pragma: no cover
    from typing_extensions import Literal  # type: ignore


class cached_property(Generic[_T]):  # pragma: no cover
    """This class is a stripped out version of its typeshed equivalent.

    It mostly exists to allow typing both the default cached property
    in Python 3.8+ and the external fallback variant for Python 3.6 and
    3.7 to share the same type hint.

    Note that the `cached-property` package and the Python 3.8 version
    are not fully compatible, be sure to test with both variants when
    using this property.
    """

    func: Callable[[Any], _T]

    def __init__(self, func: Callable[[Any], _T]) -> None:
        raise NotImplementedError(
            'This class only exists for typg hinting purposes and '
            'should never be instantiated')

    @overload
    def __get__(self, instance: None,
                owner: Optional[Type[Any]] = ...) -> 'cached_property[_T]':
        ...

    @overload
    def __get__(self, instance: object,
                owner: Optional[Type[Any]] = ...) -> _T:
        ...

    def __get__(self, *args: Any, **kwargs: Any) -> Any:
        pass


try:
    from functools import cached_property as py38_cp
except ImportError:  # pragma: no cover
    from cached_property import cached_property as ext_cp  # type: ignore
    cached_property = ext_cp  # type: ignore
else:
    cached_property = py38_cp  # type: ignore

__all__ = [
    'Literal',
    'cached_property'
]
