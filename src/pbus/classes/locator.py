from typing import override
from playwright.async_api import Locator

from pbus.classes.base_wrapper import PbusBaseWrapper


class PbusLocator(PbusBaseWrapper, Locator):
    def __init__(self, master, locator: Locator):
        super().__init__(master, locator._impl_obj)

    @override
    @property
    def first(self) -> "Locator":
        # TODO: It's a temporary solution; ideally, the property should be wrapped in `base_wrapper`.
        return self.wrapper_config.create_wrapper(self, self._impl_obj.first, False)

    @override
    @property
    def last(self) -> "Locator":
        # TODO: It's a temporary solution; ideally, the property should be wrapped in `base_wrapper`.
        return self.wrapper_config.create_wrapper(self, self._impl_obj.last, False)
