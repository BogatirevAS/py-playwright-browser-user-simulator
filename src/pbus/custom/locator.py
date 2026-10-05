import typing
from typing import Literal
from typing_extensions import override

from pbus.classes.locator import PbusLocator
from pbus.components.decorators.logging_method import LoggingMethod
from pbus.components.decorators.settings_args_injector import PbusSettingsArgsInjector


class CustomPbusLocator(PbusLocator):
    @override
    @PbusSettingsArgsInjector(
        args_list=["timeout"],
    )
    @LoggingMethod()
    async def wait_for(
        self,
        *,
        timeout: typing.Optional[float] = None,
        state: typing.Optional[
            Literal["attached", "detached", "hidden", "visible"]
        ] = None
    ) -> None:
        await super().wait_for(timeout=timeout, state=state)
