from playwright.async_api import Page

from pbus.classes.base_wrapper import PbusBaseWrapper
from pbus.components.decorators.logging_method import LoggingMethod
from pbus.components.decorators.settings_args_injector import PbusSettingsArgsInjector


class PbusPage(PbusBaseWrapper, Page):
    def __init__(self, master, page: Page):
        super().__init__(master, page._impl_obj)

    @LoggingMethod()
    async def wait(self, seconds: int, msg="Wait seconds"):
        while seconds > 0:
            self.logger.info(f"{msg}: {seconds}")
            seconds -= 1
            await super().wait_for_timeout(1000)

    @PbusSettingsArgsInjector(
        args_dict={"seconds": "seconds_to_close"},
    )
    async def wait_to_close(self, *, seconds: int):
        await self.wait(seconds=seconds, msg="Wait seconds to close")
