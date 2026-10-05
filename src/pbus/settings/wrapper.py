from typing import Optional, TYPE_CHECKING, Type, Any
from pydantic import BaseModel, ConfigDict, Field

from logger import LoggerMixin, LogLevel
from pbus.wrappable import WRAPPABLE_CLASS_MAP

if TYPE_CHECKING:
    # These are only for type checking, not at runtime
    from pbus.classes import *

    # Type aliases for type checking
    PbusBrowserContextT = Type["PbusBrowserContext"]
    PbusPageT = Type["PbusPage"]
    PbusLocatorT = Type["PbusLocator"]
    PbusDownloadT = Type["PbusDownload"]
    PbusAsyncEventInfoT = Type["PbusAsyncEventInfo"]
else:
    # At runtime, use Any
    PbusBrowserContextT = Any
    PbusPageT = Any
    PbusLocatorT = Any
    PbusDownloadT = Any
    PbusAsyncEventInfoT = Any


def _get_default_browser_context_class():
    from pbus.classes import PbusBrowserContext
    return PbusBrowserContext


def _get_default_page_class():
    from pbus.classes import PbusPage
    return PbusPage


def _get_default_locator_class():
    from pbus.classes import PbusLocator
    return PbusLocator


def _get_default_download_class():
    from pbus.classes import PbusDownload
    return PbusDownload


def _get_default_async_event_info_class():
    from pbus.classes import PbusAsyncEventInfo
    return PbusAsyncEventInfo


class PbusWrapperConfig(BaseModel, LoggerMixin):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    browser_context_class: Optional[PbusBrowserContextT] = Field(default_factory=_get_default_browser_context_class)
    page_class: Optional[PbusPageT] = Field(default_factory=_get_default_page_class)
    locator_class: Optional[PbusLocatorT] = Field(default_factory=_get_default_locator_class)
    download_class: Optional[PbusDownloadT] = Field(default_factory=_get_default_download_class)
    async_event_info_class: Optional[PbusAsyncEventInfoT] = Field(default_factory=_get_default_async_event_info_class)

    def __init__(self, **kwargs):
        self.logger.debug(f"Init kwargs: {kwargs}")
        super().__init__(**kwargs)
        if self.logger.isEnabledFor(LogLevel.DEBUG):
            classes = {k: getattr(self, k) for k in WRAPPABLE_CLASS_MAP}
            self.logger.debug(f"initialized classes: {classes}")
        self._wrapper_map = {v: getattr(self, k) for k, v in WRAPPABLE_CLASS_MAP.items()}

    @property
    def wrapper_map(self):
        return self._wrapper_map

    def create_wrapper(self, master, impl_obj, validate=True):
        """Factory method to create wrappers with type safety"""
        impl_type = type(impl_obj)
        self.logger.debug(f"impl_type: {impl_type}")

        if impl_type not in self.wrapper_map:
            if validate:
                raise ValueError(f"Unknown wrapper type: {impl_type}")
            else:
                self.logger.debug(f"Unknown wrapper type, return origin: {impl_type}")
                return impl_obj

        wrapper = self.wrapper_map[impl_type]
        self.logger.debug(f"wrapper: {wrapper}")
        return wrapper(master, impl_obj)


class PbusWrapperRegistry:
    _config: Optional[PbusWrapperConfig] = None

    @classmethod
    def _lazy_init_config(cls):
        if cls._config is None:
            cls._config = PbusWrapperConfig()

    @classmethod
    def configure(
            cls, *,
            browser_context_class: PbusBrowserContextT,
            page_class: PbusPageT,
            locator_class: PbusLocatorT,
            download_class: PbusDownloadT,
            async_event_info_class: PbusAsyncEventInfoT,
    ):
        kwargs = {
            "browser_context_class": browser_context_class,
            "page_class": page_class,
            "locator_class": locator_class,
            "download_class": download_class,
            "async_event_info_class": async_event_info_class,
        }
        cls._config = PbusWrapperConfig(**kwargs)

    @classmethod
    def get_config(cls) -> PbusWrapperConfig:
        cls._lazy_init_config()
        return cls._config

    @classmethod
    def reset(cls):
        cls._config = PbusWrapperConfig()
