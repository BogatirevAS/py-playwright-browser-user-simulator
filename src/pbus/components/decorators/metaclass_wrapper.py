from functools import wraps
from typing import Generic, TypeVar, get_origin

from logger import LoggerMixin, Decoratable


GenericT = TypeVar('GenericT')


class PbusReturnTypeWrapper(Generic[GenericT]):
    """Marker type indicating the method returns an already-wrapped object."""
    pass


class PbusMetaWraps(LoggerMixin):
    def __init__(self, func: Decoratable):
        self.func = func

    def __call__(self, wrapper: Decoratable) -> Decoratable:
        wrapper = wraps(self.func)(wrapper)
        if "return" in wrapper.__annotations__:
            self.logger.debug(f"Annotations return: {wrapper.__annotations__['return']}")
            wrapper.__annotations__["return"] = PbusReturnTypeWrapper[wrapper.__annotations__['return']]
        else:
            self.logger.debug("No annotations return")
        return wrapper

    @classmethod
    def is_wrapped(cls, return_type):
        origin = get_origin(return_type)
        return origin is PbusReturnTypeWrapper
