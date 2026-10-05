import inspect
from collections.abc import Iterable
from contextlib import asynccontextmanager, contextmanager
from typing import TYPE_CHECKING, Dict, Any, get_type_hints, AsyncContextManager, ContextManager, get_origin, get_args

from logger import ClassLoggerMixin, LogLevel, LoggerMixin
from pbus.components.decorators import PbusReturnTypeWrapper, PbusMetaWraps
from pbus.wrappable import is_wrappable, is_primitive

if TYPE_CHECKING:
    from pbus.settings.base import PbusSettings
    from pbus.settings.wrapper import PbusWrapperConfig


def create_wrapper_meta():
    class PbusWrapperMeta(ClassLoggerMixin, type):
        def __new__(cls, name: str, bases: tuple, dct: Dict[str, Any]):
            cls.logger.debug(f"Start wrapping {name}")
            cls.logger.debug(f"args:"
                             f"\n\tname = {name}"
                             f"\n\tbases = {bases}"
                             f"\n\tdct = {dct}")
            new_class = super().__new__(cls, name, bases, dct)
            if cls.logger.isEnabledFor(LogLevel.DEBUG):
                cls.logger.debug(f"new_class:"
                                 f"\n\t__bases__ = {new_class.__bases__}"
                                 f"\n\t__mro__ = {new_class.__mro__}"
                                 f"\n\t__dict__ = {new_class.__dict__}"
                                 f"\n\tdir = {dir(new_class)}")

            if name == "PbusBaseWrapper":
                cls.logger.debug(f"Skip wrapping {name}")
                return new_class

            for attr_name in dir(new_class):
                if attr_name.startswith('_'):
                    cls.logger.debug(f"Skip private method: {attr_name}")
                    continue

                attr_value = getattr(new_class, attr_name)
                if not callable(attr_value):
                    cls.logger.debug(f"Skip no callable method: {attr_name}")
                    continue

                try:
                    type_hints = get_type_hints(attr_value)
                except Exception as e:
                    cls.logger.debug(f"Failed to get type hints for {attr_name}: {e}")
                    type_hints = {}
                return_type = type_hints.get("return", type(None))
                if is_primitive(return_type):
                    cls.logger.debug(f"Skip method that returns primitive type '{return_type.__name__}': {attr_name}")
                    continue

                if cls.has_super(attr_name, attr_value):
                    cls.logger.debug(f"Skip method with super(), already wrapped: {attr_name}")
                    continue

                cls.logger.debug(f"{name}.{attr_name}() -> {return_type}")
                if cls.should_wrap_return_type(return_type):
                    dct[attr_name] = cls.wrap_method(attr_value)

            if cls.logger.isEnabledFor(LogLevel.DEBUG):
                result_dct = {k: get_type_hints(v) for k, v in dct.items() if not k.startswith("_") and callable(v)}
                cls.logger.debug(f"Result dct: {result_dct}")
            return super().__new__(cls, name, bases, dct)

        @classmethod
        def has_super(cls, attr_name, attr_value):
            source = inspect.getsource(attr_value)
            return "super()." in source and attr_name in source

        @classmethod
        def should_wrap_return_type(cls, return_type: Any) -> bool:
            """Check if return type contains wrappable types."""
            cls.logger.debug(f"Check return_type: {return_type}")
            if is_primitive(return_type):
                cls.logger.debug("Skip primitive type")
                return False
            if is_wrappable(return_type):
                cls.logger.debug("Should wrap simple wrappable type")
                return True
            # Check generic types
            origin = get_origin(return_type)
            if origin is not None:
                if origin is PbusReturnTypeWrapper:
                    cls.logger.debug("Skip wrapped type")
                    return False
                args = get_args(return_type)
                for arg in args:
                    if cls.should_wrap_return_type(arg):
                        cls.logger.debug("Should wrap nested type")
                        return True
                cls.logger.debug("Skip unsupported nested type")
                return False
            cls.logger.debug("Skip unsupported type")
            return False

        @classmethod
        def _wrap_result(cls, master, result, wrapper_config):
            """Wrap result based on its type annotation."""
            return_type = type(result)
            cls.logger.debug(f"result: {result}, return_type: {return_type}")
            # Direct wrappable type
            if is_wrappable(return_type):
                return wrapper_config.create_wrapper(master, result)

            if issubclass(return_type, Iterable):
                return cls._wrap_iterable(master, result, wrapper_config)
            if issubclass(return_type, (AsyncContextManager, ContextManager)):
                return cls._wrap_context_manager(master, result, wrapper_config)

            return result

        @classmethod
        def _wrap_iterable(cls, master, iterable, wrapper_config):
            """Wrap items in an iterable if they are wrappable."""
            cls.logger.debug("Start wrap iterable")

            def wrap_item(item):
                if is_wrappable(item):
                    return wrapper_config.create_wrapper(master, item)
                return item

            if isinstance(iterable, list):
                return [wrap_item(item) for item in iterable]
            elif isinstance(iterable, tuple):
                return tuple(wrap_item(item) for item in iterable)
            elif isinstance(iterable, set):
                return {wrap_item(item) for item in iterable}
            else:
                return (wrap_item(item) for item in iterable)

        @classmethod
        def _wrap_context_manager(cls, master, context_manager, wrapper_config):
            cls.logger.debug("Start wrap context manager")
            if hasattr(context_manager, "__aenter__"):
                cls.logger.debug(f"async context manager: {context_manager}")

                @asynccontextmanager
                async def async_context_manager():
                    async with context_manager as result:
                        if is_wrappable(result):
                            yield wrapper_config.create_wrapper(master, result)
                        else:
                            yield result
                return async_context_manager()
            else:
                cls.logger.debug(f"sync context manager: {context_manager}")

                @contextmanager
                def sync_context_manager():
                    with context_manager as result:
                        if is_wrappable(result):
                            yield wrapper_config.create_wrapper(master, result)
                        else:
                            yield result
                return sync_context_manager()

        @classmethod
        def wrap_method(cls, method):
            def execute(self, result):
                wrapper_config = getattr(self, 'wrapper_config')
                return cls._wrap_result(self, result, wrapper_config)

            if inspect.iscoroutinefunction(method):
                cls.logger.debug(f"async method: {method}")

                @PbusMetaWraps(method)
                async def async_wrapper(*args, **kwargs):
                    result = await method(*args, **kwargs)
                    return execute(args[0], result)
                return async_wrapper
            else:
                cls.logger.debug(f"sync method: {method}")

                @PbusMetaWraps(method)
                def sync_wrapper(*args, **kwargs):
                    result = method(*args, **kwargs)
                    return execute(args[0], result)
                return sync_wrapper

    return PbusWrapperMeta


class PbusBaseWrapper(LoggerMixin, metaclass=create_wrapper_meta()):
    def __init__(self, master, *args, **kwargs):
        self.master = master
        self._root_master = None
        self._wrapper_config = None
        self._settings = None
        super().__init__(*args, **kwargs)

    @property
    def root_master(self):
        if self._root_master is None:
            current = self
            while hasattr(current, 'master') and current.master is not None:
                current = current.master
            self._root_master = current
        return self._root_master

    @property
    def wrapper_config(self) -> "PbusWrapperConfig":
        if self._wrapper_config is None:
            self._wrapper_config = getattr(self.root_master, "wrapper_config")
        return self._wrapper_config

    @property
    def settings(self) -> "PbusSettings":
        if self._settings is None:
            self._settings = getattr(self.root_master, "settings")
        return self._settings

    @property
    def impl_obj(self):
        return getattr(self, "_impl_obj")
