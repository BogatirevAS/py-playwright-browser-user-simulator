from typing import Any

from pbus.settings.wrapper import PbusWrapperConfig
from pbus.custom.page import CustomPbusPage
from pbus.custom.locator import CustomPbusLocator


class CustomPbusWrapperConfig(PbusWrapperConfig):
    page_class: Any = CustomPbusPage
    locator_class: Any = CustomPbusLocator
