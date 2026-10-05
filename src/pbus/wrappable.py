from playwright._impl._async_base import AsyncEventInfo
from playwright.async_api import BrowserContext, Page, Locator, Download


WRAPPABLE_CLASS_MAP = {
    "browser_context_class": BrowserContext,
    "page_class": Page,
    "locator_class": Locator,
    "download_class": Download,
    "async_event_info_class": AsyncEventInfo,
}
WRAPPABLE_TYPES = tuple(WRAPPABLE_CLASS_MAP.values())
PRIMITIVE_TYPES = (int, float, complex, bool, str, bytes, bytearray, type(None))


def _as_type(obj_or_type):
    return obj_or_type if isinstance(obj_or_type, type) else type(obj_or_type)


def is_wrappable(obj_or_type):
    return _as_type(obj_or_type) in WRAPPABLE_TYPES


def is_primitive(obj_or_type):
    return _as_type(obj_or_type) in PRIMITIVE_TYPES
