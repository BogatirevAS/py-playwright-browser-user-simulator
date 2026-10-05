import pathlib
import shutil
import typing
from playwright.async_api import Download
from typing_extensions import override

from pbus.classes.base_wrapper import PbusBaseWrapper
from pbus.components.decorators.logging_method import LoggingMethod
from pbus.components.decorators.settings_args_injector import PbusSettingsArgsInjector


class PbusDownload(PbusBaseWrapper, Download):
    def __init__(self, master, download: Download):
        super().__init__(master, download._impl_obj)

    @override
    @PbusSettingsArgsInjector(
        args_list=["move"],
    )
    @LoggingMethod()
    async def save_as(self, path: typing.Union[str, pathlib.Path], *, move: bool) -> None:
        if move:
            return await self.move(path)
        return await super().save_as(path)

    @LoggingMethod()
    async def move(self, path: typing.Union[str, pathlib.Path]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(await self.path(), path)
